#!/usr/bin/env python3
"""Deploy objects as one Flashbots bundle: the deployer's funding and its CREATE2 deploys land together or not at all.

    uv run scripts/fp127/deploy.py bundle <rpc> <key>...       # send (FUNDER_KEY, DEPLOYER_KEY)
    uv run scripts/fp127/deploy.py bundle --dry-run <rpc> <key>...   # the same transactions on an anvil fork

The deployer key is public (the project's designated key), so any ETH that sits in its account is taken by sweeper
bots within a block. A bundle closes that window: the first transaction moves exactly the gas the deploys need from
FUNDER_KEY's account to the deployer, the rest are the deploys through the CREATE2 proxy, and the relay includes all
of them in one block or none. Each block the bundle is rebuilt for the next one: its base fee is computed from the
parent (EIP-1559), every transaction pays that base fee plus BUNDLE_TIP_GWEI (default 2), and the funding is the sum of
the deploys' gas limits at that price, so at most the gas-limit margin (BUNDLE_GAS_MARGIN, default 1%: a CREATE2 deploy's gas estimate is exact) is left behind.
It gives up after BUNDLE_BLOCKS (default 50) blocks. BUNDLE_BUILDERS, a comma-separated list of builder names the
relay shares with, widens the blocks it can land in (the Flashbots builder alone builds a minority of them).

The deploys of one bundle must fit in a block: objects are grouped so that each group uses at most half the block's
gas limit, and each group is its own bundle with its own funding.

--dry-run forks the chain with anvil, gives the funder a balance if it has none (or uses a throwaway key when
FUNDER_KEY is unset), sends the identical signed transactions in order (each mined as it is sent: anvil checks a sender's
balance on submission), and checks that every predicted address holds
exactly the artifact's runtime. It prints each deploy's gas and the bundle's total cost at the fork's base fee.

Relay: BUNDLE_RELAY, default https://relay.flashbots.net (chain 1) or https://relay-sepolia.flashbots.net (11155111).
"""
from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request

from eth_account import Account
from eth_account.messages import encode_defunct
from Crypto.Hash import keccak

import deploy as d

RELAYS = {1: "https://relay.flashbots.net", 11155111: "https://relay-sepolia.flashbots.net"}
GWEI = 10**9


def q(url, method, params):
    out = d.rpc(url, method, params)
    if "error" in out:
        raise RuntimeError(f"{method}: {out['error']}")
    return out["result"]


def next_base_fee(block: dict) -> int:
    """EIP-1559: the base fee of the block after `block`."""
    base, used, limit = int(block["baseFeePerGas"], 16), int(block["gasUsed"], 16), int(block["gasLimit"], 16)
    target = limit // 2
    if used == target:
        return base
    if used > target:
        return base + max(base * (used - target) // target // 8, 1)
    return base - base * (target - used) // target // 8


def plan(url: str, keys: list[str], deployer: str) -> tuple[int, list[dict]]:
    """The objects still to deploy, each with its calldata and gas limit, grouped to fit in a block."""
    chain = int(q(url, "eth_chainId", []), 16)
    ok, msg = d.has_clz(url)
    if not ok:
        sys.exit(f"refusing: this chain has no CLZ ({msg})")
    margin = float(os.environ.get("BUNDLE_GAS_MARGIN", "0.01"))
    items = []
    for key in keys:
        o = d.obj(key)
        init, rt = d.artifact(o)
        addr = d.predicted(o, init)
        if d.code_at(url, addr):
            print(f"{o['name']:8} {addr} already deployed, skipped")
            continue
        data = "0x" + o["salt"].hex() + init.hex()
        est = int(q(url, "eth_estimateGas", [{"from": deployer, "to": d.CREATE2_PROXY, "data": data}]), 16)
        items.append({"o": o, "addr": addr, "rt": rt, "data": data, "gas": int(est * (1 + margin)) + 1})
    limit = int(q(url, "eth_getBlockByNumber", ["latest", False])["gasLimit"], 16)
    groups, cur = [], []
    for it in items:
        if cur and sum(x["gas"] for x in cur) + it["gas"] > limit // 2:
            groups.append(cur)
            cur = []
        cur.append(it)
    if cur:
        groups.append(cur)
    return chain, groups


def sign_group(chain: int, group: list[dict], funder, deployer, nonces: dict, fee: int, tip: int) -> tuple[list[str], int]:
    """The funding transfer, then the deploys, signed for one block at max fee `fee`."""
    value = sum(it["gas"] for it in group) * fee
    base = {"chainId": chain, "maxFeePerGas": fee, "maxPriorityFeePerGas": tip, "type": 2}
    txs = [funder.sign_transaction({**base, "nonce": nonces["funder"], "to": deployer.address, "value": value, "gas": 21000})]
    for i, it in enumerate(group):
        txs.append(deployer.sign_transaction({**base, "nonce": nonces["deployer"] + i, "to": d.CREATE2_PROXY,
                                              "value": 0, "gas": it["gas"], "data": it["data"]}))
    return ["0x" + t.raw_transaction.hex().removeprefix("0x") for t in txs], value


def relay_call(relay: str, auth, method: str, params: list) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    h = "0x" + keccak.new(digest_bits=256, data=body.encode()).hexdigest()
    sig = auth.sign_message(encode_defunct(text=h)).signature.hex()
    req = urllib.request.Request(relay, data=body.encode(), headers={
        "content-type": "application/json", "X-Flashbots-Signature": f"{auth.address}:0x{sig.removeprefix('0x')}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def send(url: str, keys: list[str]) -> int:
    for k in ("FUNDER_KEY", "DEPLOYER_KEY"):
        if not os.environ.get(k):
            sys.exit(f"{k} is not set")
    funder, deployer = Account.from_key(os.environ["FUNDER_KEY"]), Account.from_key(os.environ["DEPLOYER_KEY"])
    chain, groups = plan(url, keys, deployer.address)
    relay = os.environ.get("BUNDLE_RELAY") or RELAYS.get(chain) or sys.exit(f"no Flashbots relay known for chain {chain}")
    tip = int(float(os.environ.get("BUNDLE_TIP_GWEI", "2")) * GWEI)
    blocks = int(os.environ.get("BUNDLE_BLOCKS", "50"))
    builders = [b for b in os.environ.get("BUNDLE_BUILDERS", "").split(",") if b]
    auth = Account.from_key("0x" + secrets.token_hex(32))  # the relay's reputation key; any key will do
    for g, group in enumerate(groups, 1):
        names = " ".join(it["o"]["name"] for it in group)
        print(f"bundle {g}/{len(groups)}: {names} ({sum(it['gas'] for it in group):,} gas)")
        for _ in range(blocks):
            head = q(url, "eth_getBlockByNumber", ["latest", False])
            n, fee = int(head["number"], 16), next_base_fee(head) + tip
            nonces = {"funder": int(q(url, "eth_getTransactionCount", [funder.address, "latest"]), 16),
                      "deployer": int(q(url, "eth_getTransactionCount", [deployer.address, "latest"]), 16)}
            txs, value = sign_group(chain, group, funder, deployer, nonces, fee, tip)
            sim = relay_call(relay, auth, "eth_callBundle", [{"txs": txs, "blockNumber": hex(n + 1), "stateBlockNumber": "latest"}])
            if "error" in sim or any(r.get("error") or r.get("revert") for r in sim.get("result", {}).get("results", [])):
                sys.exit(f"simulation failed for block {n + 1}: {json.dumps(sim)[:600]}")
            bundle = {"txs": txs, "blockNumber": hex(n + 1)}
            if builders:
                bundle["builders"] = builders
            relay_call(relay, auth, "eth_sendBundle", [bundle])
            print(f"  block {n + 1}: sent, funding {value / 10**18:.6f} ETH at {fee / GWEI:.3f} gwei")
            while int(q(url, "eth_blockNumber", []), 16) <= n + 1:
                time.sleep(2)
            if all(d.code_at(url, it["addr"]) for it in group):
                break
        else:
            sys.exit(f"bundle {g} was not included in {blocks} blocks; nothing of it was sent unbundled")
        for i, it in enumerate(group):
            code = d.code_at(url, it["addr"])
            print(f"  {it['o']['name']:8} {it['addr']} {len(code)} bytes{'' if code == it['rt'] else ' (DIFFERS FROM THE ARTIFACT)'}")
            if code != it["rt"]:
                return 1
        # one receipt per deploy, as deploy.py writes for a single send
        for i, it in enumerate(group):
            h = "0x" + keccak.new(digest_bits=256, data=bytes.fromhex(txs[i + 1][2:])).hexdigest()
            rcpt = q(url, "eth_getTransactionReceipt", [h])
            net = {1: "mainnet", 11155111: "sepolia"}.get(chain, str(chain))
            path = it["o"]["record"].with_name(f"{it['o']['name']}.{net}.receipt.json")
            path.write_text(json.dumps(rcpt, indent=2) + "\n")
            print(f"  receipt {path.relative_to(d.ROOT)} (block {int(rcpt['blockNumber'], 16)}, gas {int(rcpt['gasUsed'], 16):,})")
    return 0


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def dry_run(url: str, keys: list[str]) -> int:
    port = free_port()
    fork = f"http://127.0.0.1:{port}"
    anvil = subprocess.Popen(["anvil", "--fork-url", url, "--port", str(port), "--silent"])
    try:
        for _ in range(60):
            try:
                q(fork, "eth_chainId", [])
                break
            except Exception:  # noqa: BLE001 - not up yet
                time.sleep(0.5)
        funder = Account.from_key(os.environ.get("FUNDER_KEY") or "0x" + secrets.token_hex(32))
        deployer = Account.from_key(os.environ.get("DEPLOYER_KEY") or "0x" + secrets.token_hex(32))
        chain, groups = plan(fork, keys, deployer.address)
        tip = int(float(os.environ.get("BUNDLE_TIP_GWEI", "2")) * GWEI)
        total_gas = total_cost = 0
        for g, group in enumerate(groups, 1):
            head = q(fork, "eth_getBlockByNumber", ["latest", False])
            fee = next_base_fee(head) + tip
            nonces = {"funder": int(q(fork, "eth_getTransactionCount", [funder.address, "latest"]), 16),
                      "deployer": int(q(fork, "eth_getTransactionCount", [deployer.address, "latest"]), 16)}
            txs, value = sign_group(chain, group, funder, deployer, nonces, fee, tip)
            bal = int(q(fork, "eth_getBalance", [funder.address, "latest"]), 16)
            if bal < value + 21000 * fee:
                q(fork, "anvil_setBalance", [funder.address, hex(value + 21000 * fee + 10**18)])
            # anvil checks the sender's balance on submission, so the funding goes first; the transactions are the
            # ones a real bundle carries, each mined as it is sent
            hashes = [q(fork, "eth_sendRawTransaction", [t]) for t in txs]
            print(f"bundle {g}/{len(groups)} at {fee / GWEI:.3f} gwei, funding {value / 10**18:.6f} ETH")
            for h, it in zip(hashes[1:], group):
                rcpt = q(fork, "eth_getTransactionReceipt", [h])
                gas = int(rcpt["gasUsed"], 16)
                code = d.code_at(fork, it["addr"])
                ok = rcpt["status"] == "0x1" and code == it["rt"]
                total_gas += gas
                total_cost += gas * int(rcpt["effectiveGasPrice"], 16)
                print(f"  {it['o']['name']:8} {it['addr']} gas {gas:,} limit {it['gas']:,} {'ok' if ok else 'FAILED'}")
                if not ok:
                    return 1
            left = int(q(fork, "eth_getBalance", [deployer.address, "latest"]), 16)
            print(f"  left in the deployer after the bundle: {left / 10**18:.6f} ETH")
        print(f"dry run ok: {total_gas:,} gas, {total_cost / 10**18:.6f} ETH at the fork's base fee + {tip / GWEI:g} gwei")
        return 0
    finally:
        anvil.terminate()


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    if len(argv) < 2:
        print(__doc__)
        return 2
    url, keys = argv[0], argv[1:]
    return dry_run(url, keys) if dry else send(url, keys)

#!/usr/bin/env python3
"""Deploy (or predict) the ladder contracts through the CREATE2 proxy.

    uv run scripts/ladder/deploy.py predict [rpc]
    DEPLOYER_KEY=0x... uv run scripts/ladder/deploy.py deploy [rpc]
    uv run scripts/ladder/deploy.py record [rpc]        # write contracts/deployments/Ladder.json

Nineteen contracts, salt "FP127 ladder v12": SnekmateMath (the Vyper build of
snekmate's math module, out/vyper/SnekmateMath.json from scripts/ladder/vyper.py),
the sixteen adapters (no constructor arguments, except LadderSnekmate, which
takes SnekmateMath's address), LadderRunner and EdgeRunner (constructor = the
sixteen adapter addresses as one array, in form-id order, so their init code
depends on them). Each transaction is sent with the node's
own gas estimate plus 25%, because Sepolia's code-deposit pricing is not
what forge's local EVM models (see contracts/deployments/FP127.md).

The key is read from the environment and passed to `cast send` only; it
is never printed or written.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from Crypto.Hash import keccak

ROOT = Path(__file__).resolve().parents[2]
PROXY = "0x4e59b44847b379578588920cA78FbF26c0B4956C"
SALT_ASCII = "FP127 ladder v12"
SALT = "0x" + SALT_ASCII.encode().ljust(32, b"\0").hex()
DEFAULT_RPC = "https://ethereum-sepolia-rpc.publicnode.com"
ADAPTERS = ["LadderFP127", "LadderFP127Lib", "LadderABDK", "LadderSolady", "LadderPRB",
            "LadderQuad", "LadderBalancer", "LadderAave", "LadderMorpho", "LadderMaker", "LadderFP19",
            "LadderSolmate", "LadderOZ", "LadderUniswap", "LadderPRBUD", "LadderSnekmate"]
# Vyper contracts the adapters call, deployed first: name -> the adapter that takes its address
VYPER = {"SnekmateMath": "LadderSnekmate"}
RECORD = ROOT / "contracts" / "deployments" / "Ladder.json"


def cast(*args: str) -> str:
    r = subprocess.run(["cast", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"cast {' '.join(a for a in args if not a.startswith('0x') or len(a) < 70)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def k256(data: bytes) -> bytes:
    return keccak.new(digest_bits=256, data=data).digest()


def init_code(name: str, ctor_args: bytes = b"") -> bytes:
    path = ROOT / "out" / "vyper" / f"{name}.json" if name in VYPER else ROOT / "out" / f"{name}.sol" / f"{name}.json"
    art = json.loads(path.read_text())
    return bytes.fromhex(art["bytecode"]["object"][2:]) + ctor_args


def create2(init: bytes) -> str:
    h = k256(b"\xff" + bytes.fromhex(PROXY[2:]) + bytes.fromhex(SALT[2:]) + k256(init))
    return cast("to-check-sum-address", "0x" + h[12:].hex())


def plan() -> list[dict]:
    out, takes = [], {}
    for name, adapter in VYPER.items():
        init = init_code(name)
        out.append({"name": name, "init": init, "address": create2(init), "args": []})
        takes[adapter] = out[-1]["address"]
    adapters = []
    for name in ADAPTERS:
        arg = takes.get(name)
        init = init_code(name, bytes.fromhex(cast("abi-encode", "f(address)", arg)[2:]) if arg else b"")
        adapters.append({"name": name, "init": init, "address": create2(init), "args": [arg] if arg else []})
    out += adapters
    addrs = [c["address"] for c in adapters]
    args = bytes.fromhex(cast("abi-encode", f"f(address[{len(addrs)}])", "[" + ",".join(addrs) + "]")[2:])
    for runner in ("LadderRunner", "EdgeRunner"):
        init = init_code(runner, args)
        out.append({"name": runner, "init": init, "address": create2(init), "args": addrs})
    return out


def deployed(rpc: str, addr: str) -> bool:
    return cast("code", addr, "--rpc-url", rpc) != "0x"


def cmd_predict(rpc: str) -> int:
    for c in plan():
        print(f"{c['name']:16} {c['address']}  init hash 0x{k256(c['init']).hex()}  {'deployed' if deployed(rpc, c['address']) else 'not deployed'}")
    return 0


def cmd_deploy(rpc: str) -> int:
    key = os.environ.get("DEPLOYER_KEY")
    if not key:
        print("DEPLOYER_KEY is not set")
        return 1
    for c in plan():
        if deployed(rpc, c["address"]):
            print(f"{c['name']:16} {c['address']}  already deployed")
            continue
        data = SALT + c["init"].hex()
        # Public RPCs cap eth_estimateGas (50M on some; publicnode answers "reverted" past its cap),
        # and LadderFP19's 43 KB deposit needs about 67M. When the estimate fails, send with
        # LADDER_GAS (default 90M, under Sepolia's 200M block limit); a short limit only reverts.
        try:
            est = int(cast("estimate", PROXY, data, "--rpc-url", rpc))
            gas = est * 5 // 4
            print(f"{c['name']:16} {c['address']}  estimate {est:,}  sending with {gas:,}")
        except SystemExit:
            gas = int(os.environ.get("LADDER_GAS", "90000000"))
            print(f"{c['name']:16} {c['address']}  no estimate from the RPC  sending with {gas:,}")
        receipt = json.loads(cast("send", PROXY, data, "--rpc-url", rpc, "--private-key", key, "--gas-limit", str(gas), "--json"))
        status = int(receipt["status"], 16) if isinstance(receipt["status"], str) else receipt["status"]
        print(f"{'':16} tx {receipt['transactionHash']} block {int(receipt['blockNumber'], 16)} gasUsed {int(receipt['gasUsed'], 16):,} status {status}")
        if status != 1:
            return 1
        # a public RPC can answer from a node a block behind the receipt's
        for _ in range(10):
            if deployed(rpc, c["address"]):
                break
            time.sleep(3)
        else:
            print("no code at the predicted address")
            return 1
    return 0


def cmd_record(rpc: str) -> int:
    rec = {"chainId": 11155111, "network": "sepolia", "proxy": PROXY, "salt": SALT, "saltAscii": SALT_ASCII,
           "fp127": json.loads((RECORD.parent / "FP127.json").read_text())["address"], "contracts": {}}
    for c in plan():
        code = cast("code", c["address"], "--rpc-url", rpc)
        rec["contracts"][c["name"]] = {
            "address": c["address"],
            "initCodeHash": "0x" + k256(c["init"]).hex(),
            "constructorArgs": c["args"],
            "runtimeKeccak": "0x" + k256(bytes.fromhex(code[2:])).hex() if code != "0x" else None,
            "deployed": code != "0x",
        }
    RECORD.write_text(json.dumps(rec, indent=1) + "\n")
    print(f"wrote {RECORD.relative_to(ROOT)}")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    rpc = argv[1] if len(argv) > 1 else DEFAULT_RPC
    return {"predict": cmd_predict, "deploy": cmd_deploy, "record": cmd_record}[argv[0]](rpc)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

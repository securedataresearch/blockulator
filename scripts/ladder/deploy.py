#!/usr/bin/env python3
"""Deploy (or predict) the ladder contracts through the CREATE2 proxy.

    uv run scripts/ladder/deploy.py predict [rpc]
    DEPLOYER_KEY=0x... uv run scripts/ladder/deploy.py deploy [rpc]
    uv run scripts/ladder/deploy.py record [rpc]        # write contracts/deployments/Ladder.json

Thirteen contracts, salt "FP127 ladder v9": the eleven adapters (no constructor
arguments), LadderRunner and EdgeRunner (constructor = the ten adapter
addresses as one array, so their init code depends on them). Each transaction is sent with the node's
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
from pathlib import Path

from Crypto.Hash import keccak

ROOT = Path(__file__).resolve().parents[2]
PROXY = "0x4e59b44847b379578588920cA78FbF26c0B4956C"
SALT_ASCII = "FP127 ladder v9"
SALT = "0x" + SALT_ASCII.encode().ljust(32, b"\0").hex()
DEFAULT_RPC = "https://ethereum-sepolia-rpc.publicnode.com"
ADAPTERS = ["LadderFP127", "LadderFP127Lib", "LadderABDK", "LadderSolady", "LadderPRB",
            "LadderQuad", "LadderBalancer", "LadderAave", "LadderMorpho", "LadderMaker", "LadderFP256"]
RECORD = ROOT / "contracts" / "deployments" / "Ladder.json"


def cast(*args: str) -> str:
    r = subprocess.run(["cast", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"cast {' '.join(a for a in args if not a.startswith('0x') or len(a) < 70)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def k256(data: bytes) -> bytes:
    return keccak.new(digest_bits=256, data=data).digest()


def init_code(name: str, ctor_args: bytes = b"") -> bytes:
    art = json.loads((ROOT / "out" / f"{name}.sol" / f"{name}.json").read_text())
    return bytes.fromhex(art["bytecode"]["object"][2:]) + ctor_args


def create2(init: bytes) -> str:
    h = k256(b"\xff" + bytes.fromhex(PROXY[2:]) + bytes.fromhex(SALT[2:]) + k256(init))
    return cast("to-check-sum-address", "0x" + h[12:].hex())


def plan() -> list[dict]:
    out = []
    for name in ADAPTERS:
        init = init_code(name)
        out.append({"name": name, "init": init, "address": create2(init), "args": []})
    addrs = [c["address"] for c in out]
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
        est = int(cast("estimate", PROXY, data, "--rpc-url", rpc))
        gas = est * 5 // 4
        print(f"{c['name']:16} {c['address']}  estimate {est:,}  sending with {gas:,}")
        receipt = json.loads(cast("send", PROXY, data, "--rpc-url", rpc, "--private-key", key, "--gas-limit", str(gas), "--json"))
        status = int(receipt["status"], 16) if isinstance(receipt["status"], str) else receipt["status"]
        print(f"{'':16} tx {receipt['transactionHash']} block {int(receipt['blockNumber'], 16)} gasUsed {int(receipt['gasUsed'], 16):,} status {status}")
        if status != 1:
            return 1
        if not deployed(rpc, c["address"]):
            print("no code at the predicted address")
            return 1
    return 0


def cmd_record(rpc: str) -> int:
    rec = {"chainId": 11155111, "network": "sepolia", "proxy": PROXY, "salt": SALT, "saltAscii": SALT_ASCII,
           "fp127": "0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1", "contracts": {}}
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

#!/usr/bin/env python3
"""Verify the on-chain ladder contracts (contracts/deployments/Ladder.json) on Sourcify.

    uv run scripts/ladder/verify.py [chainId]

Each contract's standard JSON input is rebuilt from its own compiler metadata (out/<C>.sol/<C>.json rawMetadata):
the exact sources it was compiled from, read from disk and checked against the metadata's keccak, and its exact
settings. forge verify-contract gathers the whole project instead, Vyper included, which Sourcify cannot take.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from Crypto.Hash import keccak

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fp127"))
from verify import SOURCIFY, http  # noqa: E402

RECORD = ROOT / "contracts" / "deployments" / "Ladder.json"


def std_input(name: str) -> tuple[dict, str, str]:
    meta = json.loads(json.loads((ROOT / "out" / f"{name}.sol" / f"{name}.json").read_text())["rawMetadata"])
    sources = {}
    for path, s in meta["sources"].items():
        text = (ROOT / path).read_text()
        if "0x" + keccak.new(digest_bits=256, data=text.encode()).hexdigest() != s["keccak256"]:
            sys.exit(f"{path} differs from the source {name} was compiled from: run make build")
        sources[path] = {"content": text}
    settings = dict(meta["settings"])
    (unit, contract), = settings.pop("compilationTarget").items()
    settings["outputSelection"] = {"*": {"*": ["abi", "evm.bytecode", "evm.deployedBytecode", "metadata"]}}
    return ({"language": meta["language"], "sources": sources, "settings": settings},
            meta["compiler"]["version"], f"{unit}:{contract}")


def verify(chain: int, name: str, address: str) -> bool:
    inp, version, ident = std_input(name)
    body = json.dumps({"stdJsonInput": inp, "compilerVersion": version, "contractIdentifier": ident}).encode()
    status, text = http("POST", f"{SOURCIFY}/v2/verify/{chain}/{address}", body, {"Content-Type": "application/json"})
    if status == 409:
        print(f"{name:18} {address} already verified")
        return True
    if status not in (200, 202):
        print(f"{name:18} {address} submit failed: {status} {text[:300]}")
        return False
    vid = json.loads(text)["verificationId"]
    for _ in range(60):
        time.sleep(5)
        s, t = http("GET", f"{SOURCIFY}/v2/verify/{vid}")
        job = json.loads(t) if s == 200 else {}
        if job.get("isJobCompleted"):
            match = job.get("contract", {}).get("match")
            print(f"{name:18} {address} {match or json.dumps(job.get('error'))[:200]}")
            return match in ("exact_match", "match")
    print(f"{name:18} {address} timed out")
    return False


def main(argv: list[str]) -> int:
    chain = int(argv[0]) if argv else 11155111
    rec = json.loads(RECORD.read_text())["contracts"]
    ok = all([verify(chain, name, c["address"]) for name, c in rec.items() if c.get("deployed")])
    print(f"{SOURCIFY}/v2/contract/{chain}/<address>")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Check every cell of the edges dataset against the live EdgeRunner.

    uv run scripts/ladder/liveedges.py [rpc] [workers=8]

Calls EdgeRunner.run(op, form, args) on Sepolia for every probe and form
with the probe's encoded arguments (scripts/ladder/edge-inputs.json),
compares the raw result (or the revert selector) with
docs/benchmarks/edges.json, and records the runner and selector in it so
the edges page's verify buttons know where to call.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDGES = ROOT / "docs" / "benchmarks" / "edges.json"
RECORD = ROOT / "contracts" / "deployments" / "Ladder.json"
INPUTS = ROOT / "scripts" / "ladder" / "edge-inputs.json"
DEFAULT_RPC = "https://ethereum-sepolia-rpc.publicnode.com"
FORMS = ["fp127", "fp127lib", "abdk", "solady", "prb", "quad", "balancer", "aave", "morpho", "maker"]
SCALE_OF_FORM = {"fp127": "fp127", "fp127lib": "fp127", "abdk": "abdk", "solady": "wad", "prb": "wad",
                 "quad": "quad", "balancer": "wad", "aave": "ray", "morpho": "wad", "maker": "ray"}
SIG = "run(uint8,uint8,int256[])(bool,int256,bytes4,uint256)"
SELECTOR = "0xf833b7d5"


def call(rpc: str, runner: str, op: int, f: int, args: list[str], tries: int = 4):
    for attempt in range(tries):
        r = subprocess.run(["cast", "call", runner, SIG, str(op), str(f), "[" + ",".join(args) + "]", "--rpc-url", rpc],
                           capture_output=True, text=True)
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            return lines[0] == "true", int(lines[1].split()[0]), lines[2][:10]
        if "revert" in r.stderr.lower():
            return None
        time.sleep(2 * (attempt + 1))
    raise SystemExit(f"rpc failed: {r.stderr.strip()[:200]}")


def main(argv: list[str]) -> int:
    rpc = argv[0] if argv else DEFAULT_RPC
    workers = int(argv[1]) if len(argv) > 1 else 8
    runner = json.loads(RECORD.read_text())["contracts"]["EdgeRunner"]["address"]
    doc = json.loads(EDGES.read_text())
    inputs = {c["id"]: c for c in json.loads(INPUTS.read_text())["cells"]}
    jobs = []
    for op in doc["ops"]:
        for p in op["probes"]:
            for fi, form in enumerate(FORMS):
                c = p["cells"].get(form)
                if c is None or c.get("range"):
                    continue
                jobs.append((op, p, fi, form, c))

    def one(j):
        op, p, fi, form, c = j
        enc = inputs[p["id"]][SCALE_OF_FORM[form]]
        res = call(rpc, runner, op["index"], fi, enc)
        if res is None:
            return f"{p['id']:34} {form:9} rpc refused the call", 1
        ok, raw, reason = res
        if c.get("reverted"):
            match = (not ok) and reason == c["reason"]
        else:
            match = ok and str(raw) == c["raw"]
        return f"{p['id']:34} {form:9} {'match' if match else 'MISMATCH'}", 0 if match else 1

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one, jobs))
    mismatches = 0
    for line, bad in results:
        if bad:
            print(line)
        mismatches += bad
    print(f"{len(jobs)} cells, {mismatches} mismatches")
    doc["liveRunner"] = runner
    doc["liveSelector"] = SELECTOR
    doc["liveNote"] = "Every cell was re-run through the live EdgeRunner on Sepolia by scripts/ladder/liveedges.py; the verify button repeats that call."
    EDGES.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"wrote {EDGES.relative_to(ROOT)}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

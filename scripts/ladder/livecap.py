#!/usr/bin/env python3
"""Measure how far up the ladder the public RPC's eth_call will go, and that
the live runner agrees with the committed dataset.

    uv run scripts/ladder/livecap.py [rpc] [workers=8]

For every scenario, input and form, calls LadderRunner.run(scenario, form,
n, p) on Sepolia for each N on the ladder with the input's floored
parameters (scripts/ladder/inputs.json), compares the raw result with
docs/benchmarks/ladder.json, and records the largest N every input of the
form completed as `liveMaxN`, and stamps the run (cells checked, mismatches,
block, date) into the dataset for the results page.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LADDER = ROOT / "docs" / "benchmarks" / "ladder.json"
RECORD = ROOT / "contracts" / "deployments" / "Ladder.json"
INPUTS = ROOT / "scripts" / "ladder" / "inputs.json"
DEFAULT_RPC = "https://ethereum-sepolia-rpc.publicnode.com"
FORMS = ["fp127", "fp127lib", "abdk", "solady", "prb", "quad", "balancer", "aave", "morpho", "maker", "fp19", "solmate", "oz", "uniswap", "prbud", "snekmate"]
SCALE_OF_FORM = {"fp127": "fp127", "fp127lib": "fp127", "abdk": "abdk", "solady": "wad", "prb": "wad",
                 "quad": "quad", "balancer": "wad", "aave": "ray", "morpho": "wad", "maker": "ray", "fp19": "fp19",
                 "solmate": "wad", "oz": "wad", "uniswap": "wad", "prbud": "wad", "snekmate": "wad"}
SIG = "run(uint8,uint8,uint32,int256[])(bool,int256,bytes4,uint256,uint256)"
SELECTOR = "0x281dbbfe"


def call(rpc: str, runner: str, s: int, f: int, n: int, p: list[str], tries: int = 4):
    """One eth_call. Transient RPC failures (timeouts, gateway errors) are retried;
    only a clean answer or a persistent refusal comes back."""
    arr = "[" + ",".join(p) + "]"
    err = "call failed"
    for attempt in range(tries):
        r = subprocess.run(["cast", "call", runner, SIG, str(s), str(f), str(n), arr,
                            "--gas-limit", "1000000000", "--rpc-url", rpc], capture_output=True, text=True)
        if r.returncode == 0:
            ok, raw, reason, gps, gt = [x.strip() for x in r.stdout.strip().splitlines()[:5]]
            return {"ok": ok == "true", "raw": int(raw.split()[0]), "reason": reason, "gas": int(gt.split()[0])}, None
        err = r.stderr.strip().splitlines()[-1][:120] if r.stderr.strip() else "call failed"
        time.sleep(2 * (attempt + 1))
    return None, err


def live_block(rpc: str) -> int:
    r = subprocess.run(["cast", "block-number", "--rpc-url", rpc], capture_output=True, text=True, check=True)
    return int(r.stdout.strip())


def walk(rpc: str, runner: str, scn: dict, inp: dict, fi: int, form: str, p: list[str], ladder: list[int]):
    """Climb one (scenario, input, form) column until the RPC refuses, the cell
    disagrees, or the ladder ends. Returns (largest N reached, mismatch flag, cells checked, log lines)."""
    sid, name = scn["id"], inp["name"]
    reached, mismatch, checked, log = 0, False, 0, []
    for n in ladder:
        cell = inp["cells"].get(form, {}).get(str(n))
        if cell is None:
            continue
        res, err = call(rpc, runner, scn["index"], fi, n, p)
        if res is None:
            log.append(f"{sid:20} {name:18} {form:9} N={n:<6} RPC refused: {err}")
            break
        if cell.get("reverted"):
            agree = not res["ok"] and res["reason"] == cell["reason"]
        else:
            agree = res["ok"] and str(res["raw"]) == cell["raw"]
            if not res["ok"] and res["reason"] == "0x00000000":
                log.append(f"{sid:20} {name:18} {form:9} N={n:<6} out of gas at the RPC cap (needs about {cell['gas']:,})")
                break
        checked += 1
        if not agree:
            mismatch = True
            log.append(f"{sid:20} {name:18} {form:9} N={n:<6} MISMATCH live={res} committed={cell.get('raw', 'reverted')}")
            break
        reached = n
    return reached, mismatch, checked, log


def main(argv: list[str]) -> int:
    rpc = argv[0] if argv else DEFAULT_RPC
    workers = int(argv[1]) if len(argv) > 1 else 8
    runner = json.loads(RECORD.read_text())["contracts"]["LadderRunner"]["address"]
    doc = json.loads(LADDER.read_text())
    inputs = {(c["id"], c["input"]): c for c in json.loads(INPUTS.read_text())["cells"]}
    jobs = []
    for scn in doc["scenarios"]:
        for fi, form in enumerate(FORMS):
            for inp in scn["inputs"]:
                p = inputs[(scn["id"], inp["name"])][SCALE_OF_FORM[form]]
                jobs.append((scn, inp, fi, form, p))
    mismatches, checked = 0, 0
    block = live_block(rpc)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda j: walk(rpc, runner, j[0], j[1], j[2], j[3], j[4], doc["ladder"]), jobs))
    for scn in doc["scenarios"]:
        scn["liveMaxN"] = {}
    for (scn, inp, fi, form, _), (reached, mismatch, n_checked, log) in zip(jobs, results):
        for line in log:
            print(line)
        mismatches += mismatch
        checked += n_checked
        cur = scn["liveMaxN"].get(form)
        scn["liveMaxN"][form] = reached if cur is None else min(cur, reached)
    for scn in doc["scenarios"]:
        print(f"{scn['id']:20} liveMaxN " + " ".join(f"{f}={scn['liveMaxN'][f]}" for f in FORMS))
    doc["liveRunner"] = runner
    doc["liveSelector"] = SELECTOR
    doc["liveNote"] = "liveMaxN is the largest N on the ladder that the public Sepolia RPC's eth_call completed for every input of that form. Above it the runner reports a bare revert because the adapter ran out of gas under the RPC's eth_call limits (calls needing more than about 40M gas, or a few seconds of execution, fail); cells above it are checked from your own node. Anyone with their own node can run every cell."
    doc["liveChecked"] = checked
    doc["liveMismatches"] = mismatches
    doc["liveBlock"] = block
    doc["liveDate"] = time.strftime("%Y-%m-%d", time.gmtime())
    if not mismatches:  # the live runner returns this dataset: it is no longer ahead of it
        doc.pop("runnersAhead", None)

    LADDER.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"updated {LADDER.relative_to(ROOT)}; mismatches: {mismatches}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

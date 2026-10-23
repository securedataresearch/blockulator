#!/usr/bin/env python3
"""Inline size: the runtime bytecode each op adds to a contract that calls it
through FP127Lib or FP256Lib.

    uv run scripts/size/inline.py            # -> docs/benchmarks/size.json + size.md
    uv run scripts/size/inline.py --keep DIR # also keep the generated contracts in DIR

For every op in contracts/src/{fp127,fp256}/ops.json it writes a throwaway
contract with one external function, f(int256 a, int256 b, int256 c), whose
body is `r = Lib.<op>(a[, b[, c]])`, and a baseline whose body is `r = a`. The
signature is the same in every contract, so the ABI decoder and dispatch cancel
and the delta is the op alone: its assembly block and every helper inside it.

Settings are the repo's default foundry profile (solc 0.8.38, evm osaka,
optimizer on, 200 runs), compiled twice: the legacy pipeline (via_ir = false,
the profile's own) and via_ir. The CBOR metadata tail is switched off so the
numbers are code only. The contracts live in a temp dir that is removed.

Each FP*Lib function is a self-contained assembly block carrying its own copy
of every helper it uses, so the single-op number is what the first op costs.
A bundle (several ops chained in one contract) records what the shared
helpers save: both pipelines merge identical code across blocks (the legacy
block deduplicator, the IR's function combiner), so a second op that shares a
kernel with the first adds less than its own row.

    uv run scripts/size/inline.py --check    # fail if size.json / size.md are stale (the date aside)
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fp127"))
from stdjson import SOLC_VERSION, find_solc  # noqa: E402

OUT_JSON = ROOT / "docs" / "benchmarks" / "size.json"
OUT_MD = ROOT / "docs" / "benchmarks" / "size.md"
GAS = {"fp127": ROOT / "docs" / "benchmarks" / "gas.json", "fp256": ROOT / "docs" / "benchmarks" / "gas256.json"}
LIMIT = 24576
EVM = "osaka"
RUNS = 200
PIPELINES = {"legacy": False, "viaIr": True}
LIBS = {
    "fp127": ("FP127Lib", "contracts/src/fp127/FP127Lib.sol"),
    "fp256": ("FP256Lib", "contracts/src/fp256/FP256Lib.sol"),
}
# Common combinations: what a contract that uses them together pays.
BUNDLES = [
    ("fp127", ["mul", "div"]),
    ("fp127", ["mulDown", "mulUp", "divDown", "divUp"]),
    ("fp127", ["exp", "ln"]),
    ("fp127", ["exp", "ln", "pow"]),
    ("fp127", ["exp", "log2", "sqrt"]),
    ("fp127", ["erf", "erfc", "normCdf"]),
    ("fp127", ["fromFixed18", "toFixed18Down", "toFixed18Up", "mulDown", "mulUp", "compound"]),
    ("fp256", ["add", "sub", "mul", "div"]),
    ("fp256", ["exp", "ln"]),
    ("fp256", ["exp", "ln", "pow"]),
    ("fp256", ["erf", "erfc", "normCdf"]),
    ("fp256", ["fromFixed18", "toFixed18Down", "toFixed18Up", "mulDown", "mulUp", "compound"]),
]
ARGS = ["a", "b", "c"]


def returns(lib: str) -> dict[str, str]:
    """Each Lib function's return type, read from its source (two FP256 ops return uint256)."""
    src = (ROOT / LIBS[lib][1]).read_text()
    return dict(re.findall(r"^    function (\w+)\([^)]*\) internal pure returns \((\w+) ", src, re.M))


RET: dict[str, dict[str, str]] = {}


def call(lib: str, op: dict, inner: str | None = None) -> str:
    """Lib.<op>(a, b, c) for the op's arity, as an int256; a uint256 parameter takes uint256(a)."""
    params = op["signature"][len(op["name"]) + 1:-1].split(",")
    args = []
    for i, t in enumerate(params):
        v = inner if (i == 0 and inner) else ARGS[i]
        args.append(f"uint256({v})" if t == "uint256" else v)
    e = f"{LIBS[lib][0]}.{op['name']}({', '.join(args)})"
    return f"int256({e})" if RET[lib][op["name"]] == "uint256" else e


def source(name: str, imports: list[str], body: str) -> str:
    imp = "".join(f'import {{{LIBS[k][0]}}} from "{LIBS[k][1]}";\n' for k in imports)
    return (f"// SPDX-License-Identifier: MIT\npragma solidity ^0.8.31;\n{imp}\n"
            f"contract {name} {{\n"
            f"    function f(int256 a, int256 b, int256 c) external pure returns (int256 r) {{\n"
            f"        a; b; c;\n        {body}\n    }}\n}}\n")


def compile_one(path: Path, name: str, via_ir: bool) -> int:
    """Runtime bytecode length in bytes of contract `name` in `path`."""
    rel = path.name
    sources = {rel: {"content": path.read_text()}}
    for _, (_, p) in LIBS.items():
        if p in sources[rel]["content"]:
            sources[p] = {"content": (ROOT / p).read_text()}
    inp = {
        "language": "Solidity",
        "sources": sources,
        "settings": {
            "optimizer": {"enabled": True, "runs": RUNS},
            "evmVersion": EVM,
            "viaIR": via_ir,
            "metadata": {"appendCBOR": False},
            "outputSelection": {rel: {name: ["evm.deployedBytecode.object"]}},
        },
    }
    p = subprocess.run([find_solc(), "--standard-json"], input=json.dumps(inp), capture_output=True, text=True)
    out = json.loads(p.stdout)
    errs = [e for e in out.get("errors", []) if e.get("severity") == "error"]
    if errs:
        raise RuntimeError(f"{name}: " + "\n".join(e.get("formattedMessage", "") for e in errs))
    return len(out["contracts"][rel][name]["evm"]["deployedBytecode"]["object"]) // 2


def staticcall_overhead(lib: str) -> int | None:
    """Gas the staticcall to the deployed object adds to add, from gas.json / gas256.json (yul median - lib median)."""
    try:
        s = json.loads(GAS[lib].read_text())["ops"]["add"]["summary"]
        return s["yul"]["median"] - s["lib"]["median"]
    except (OSError, KeyError, TypeError):
        return None


def summary(rows: dict[str, dict], key: str) -> dict:
    vals = sorted(((r[key], n) for n, r in rows.items()), key=lambda t: (t[0], t[1]))
    return {"min": {"op": vals[0][1], "bytes": vals[0][0]},
            "median": int(statistics.median(v for v, _ in vals)),
            "max": {"op": vals[-1][1], "bytes": vals[-1][0]}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", help="copy the generated contracts to this directory")
    ap.add_argument("-j", type=int, default=os.cpu_count() or 4, help="parallel solc processes")
    ap.add_argument("--check", action="store_true", help="fail if the committed size.json / size.md are stale")
    a = ap.parse_args()

    ops = {k: json.loads((ROOT / "contracts" / "src" / k / "ops.json").read_text())["ops"] for k in LIBS}
    by = {k: {o["name"]: o for o in v} for k, v in ops.items()}
    RET.update({k: returns(k) for k in LIBS})
    tmp = Path(tempfile.mkdtemp(prefix="size-inline-"))
    try:
        jobs: list[tuple[str, str, str | None, list[str] | None]] = []  # (contract, lib, op, bundle)
        (tmp / "Baseline.sol").write_text(source("Baseline", [], "r = a;"))
        jobs.append(("Baseline", "", None, None))
        for k, lst in ops.items():
            for o in lst:
                n = f"S_{k}_{o['name']}"
                (tmp / f"{n}.sol").write_text(source(n, [k], f"r = {call(k, o)};"))
                jobs.append((n, k, o["name"], None))
        for i, (k, names) in enumerate(BUNDLES):
            n = f"B_{k}_{i}"
            # chained, so no op's result is dead: r = op3(op2(op1(a, b), b), b)
            expr = "a"
            for nm in names:
                expr = call(k, by[k][nm], inner=expr)
            (tmp / f"{n}.sol").write_text(source(n, [k], f"r = {expr};"))
            jobs.append((n, k, None, names))

        work = [(j, pl) for j in jobs for pl in PIPELINES]
        sizes: dict[tuple[str, str], int] = {}

        def run(item):
            (n, *_), pl = item
            return n, pl, compile_one(tmp / f"{n}.sol", n, PIPELINES[pl])

        tty = sys.stderr.isatty()
        with ThreadPoolExecutor(max_workers=a.j) as ex:
            for i, (n, pl, b) in enumerate(ex.map(run, work), 1):
                sizes[(n, pl)] = b
                if tty:
                    print(f"\r{i}/{len(work)} compiled", end="", file=sys.stderr, flush=True)
        if tty:
            print(file=sys.stderr)
        if a.keep:
            shutil.copytree(tmp, a.keep, dirs_exist_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    base = {pl: sizes[("Baseline", pl)] for pl in PIPELINES}
    libs: dict[str, dict] = {}
    for k, lst in ops.items():
        rows = {o["name"]: {pl: sizes[(f"S_{k}_{o['name']}", pl)] - base[pl] for pl in PIPELINES} for o in lst}
        libs[k] = {"staticcallGas": staticcall_overhead(k),
                   "summary": {pl: summary(rows, pl) for pl in PIPELINES},
                   "sum": {pl: sum(r[pl] for r in rows.values()) for pl in PIPELINES},
                   "ops": rows}
    bundles = []
    for i, (k, names) in enumerate(BUNDLES):
        b = {pl: sizes[(f"B_{k}_{i}", pl)] - base[pl] for pl in PIPELINES}
        singles = {pl: sum(libs[k]["ops"][nm][pl] for nm in names) for pl in PIPELINES}
        bundles.append({"lib": k, "ops": names, **b, "sumOfSingles": singles})

    doc = {
        "generated": datetime.date.today().isoformat(),
        "description": ("Runtime bytecode, in bytes, that one op adds to a contract when it is inlined through "
                        "FP127Lib or FP256Lib, helpers included: the deployed size of a contract with one external "
                        "function f(int256,int256,int256) returning Lib.op(a[,b[,c]]), minus the same contract "
                        "returning a. legacy is the default foundry profile (via_ir = false), viaIr the same settings "
                        "through the IR. CBOR metadata is off. Each Lib function carries its own copy of its helpers "
                        "and the optimizer merges identical code across them, so a second op that shares a kernel "
                        "with the first adds less than its row: bundles chains several ops in one contract, against "
                        "the sum of their singles. staticcallGas is the gas the external call to the deployed object "
                        "adds to add (gas.json or gas256.json, yul median minus lib median)."),
        "generator": "scripts/size/inline.py (make size-inline)",
        "compiler": {"solc": SOLC_VERSION, "evmVersion": EVM, "optimizerRuns": RUNS, "cbor": False},
        "limit": LIMIT,
        "baseline": base,
        "libs": libs,
        "bundles": bundles,
    }
    if a.check:
        # bytes only: the date and the gas figures (from a gas.json a bench may just have rewritten) are kept
        try:
            old = json.loads(OUT_JSON.read_text())
            doc["generated"] = old["generated"]
            for k in libs:
                libs[k]["staticcallGas"] = old["libs"][k]["staticcallGas"]
        except (OSError, KeyError, ValueError):
            pass
        stale = [p.relative_to(ROOT) for p, t in ((OUT_JSON, json.dumps(doc, indent=1) + "\n"), (OUT_MD, markdown(doc)))
                 if not p.exists() or p.read_text() != t]
        if stale:
            print(f"stale: {', '.join(map(str, stale))}; run make size-inline", file=sys.stderr)
            return 1
        print(f"size-inline ok: {sum(len(v['ops']) for v in libs.values())} ops, {len(bundles)} bundles current")
        return 0
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")
    OUT_MD.write_text(markdown(doc))
    for k in LIBS:
        s = libs[k]["summary"]
        print(f"{k}: legacy min {s['legacy']['min']['op']} {s['legacy']['min']['bytes']}, median "
              f"{s['legacy']['median']}, max {s['legacy']['max']['op']} {s['legacy']['max']['bytes']}; "
              f"viaIr min {s['viaIr']['min']['bytes']}, median {s['viaIr']['median']}, max {s['viaIr']['max']['bytes']}")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    return 0


def fmt(n: int) -> str:
    return f"{n:,}"


def markdown(d: dict) -> str:
    c = d["compiler"]
    L = [
        "# Inline size",
        "",
        f"Generated {d['generated']} by `make size-inline` ([`scripts/size/inline.py`](../../scripts/size/inline.py)); "
        "the data is [`size.json`](size.json).",
        "",
        "The runtime bytecode one op adds to a contract that calls it through `FP127Lib` or `FP256Lib`, helpers "
        "included. Each op is compiled alone in a contract with one external function `f(int256,int256,int256)` "
        "returning `Lib.op(a[, b[, c]])`; the delta is against the same contract returning `a`, so the ABI decoder "
        f"and dispatch cancel. solc {c['solc']}, evm {c['evmVersion']}, optimizer {c['optimizerRuns']} runs, CBOR "
        "metadata off. **legacy** is the repo's default profile (`via_ir = false`); **via_ir** is the same settings "
        f"through the IR. Baseline contract: {fmt(d['baseline']['legacy'])} bytes legacy, "
        f"{fmt(d['baseline']['viaIr'])} via_ir.",
        "",
        "## Headline",
        "",
        "| library | ops | smallest | median | largest | all ops, sum of singles |",
        "|---|---:|---|---:|---|---:|",
    ]
    for k, v in d["libs"].items():
        for pl, lab in (("legacy", "legacy"), ("viaIr", "via_ir")):
            s = v["summary"][pl]
            L.append(f"| {k.upper()} {lab} | {len(v['ops'])} | `{s['min']['op']}` {fmt(s['min']['bytes'])} | "
                     f"{fmt(s['median'])} | `{s['max']['op']}` {fmt(s['max']['bytes'])} | {fmt(v['sum'][pl])} |")
    L += [
        "",
        "## Shared helpers",
        "",
        "Every `FP*Lib` function is one self-contained `assembly` block that carries its own copy of each helper it "
        "uses (`expk`, `divw`, `log2m` and the rest), so the single-op number is what the first op costs. Both "
        "pipelines merge identical code across blocks (the legacy block deduplicator, the IR's function combiner), "
        "so a second op that shares a kernel with the first adds less than its own row. Each bundle below is one "
        "contract that chains the ops, against the sum of their single-op rows.",
        "",
        "| library | ops | legacy | sum of singles | via_ir | sum of singles |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for b in d["bundles"]:
        L.append(f"| {b['lib'].upper()} | {', '.join('`' + o + '`' for o in b['ops'])} | {fmt(b['legacy'])} | "
                 f"{fmt(b['sumOfSingles']['legacy'])} | {fmt(b['viaIr'])} | {fmt(b['sumOfSingles']['viaIr'])} |")
    g1, g2 = d["libs"]["fp127"]["staticcallGas"], d["libs"]["fp256"]["staticcallGas"]
    L += [
        "",
        "## Inline or call the deployed object",
        "",
        f"Inlining saves the external call: about {g1} gas per call to the deployed FP127 and {g2} to FP256 "
        "([`gas.json`](gas.json), [`gas256.json`](gas256.json): `add`, object median minus inline median). "
        "`staticcall` the deployed object instead (for FP256, whichever of FP256, FP256E, FP256H and FP256S holds "
        f"the op) when inlining would take the contract near the {fmt(d['limit'])}-byte limit (EIP-170), or when "
        "the op is large and called rarely. Deploying code costs at least 200 gas a byte, so inlining an op of N "
        f"bytes pays for itself only after about 200N / {g1} calls: a small op at once, `pow` after thousands. "
        "The deployed objects already hold every op, so calling one adds only the call site.",
        "",
    ]
    for k, v in d["libs"].items():
        L += [f"## {k.upper()}", "", "| op | legacy | via_ir |", "|---|---:|---:|"]
        for n, r in v["ops"].items():
            L.append(f"| `{n}` | {fmt(r['legacy'])} | {fmt(r['viaIr'])} |")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())

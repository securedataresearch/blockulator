#!/usr/bin/env python3
"""Turn GAS| lines from test/fp127/GasLadder.t.sol into docs/benchmarks/gas.json
and docs/benchmarks/gas.md.

    forge test --match-contract GasLadder -vv | uv run scripts/fp127/gas_to_json.py

Line format:  GAS|<op>|<inputIndex>|<input hex>|<form>|<gas or NA>[|typical]
Forms:        huff yul caller lib abdk solady prb quad balancer

A line with the seventh field `typical` belongs to the op's typical-input set
(random non-integer inputs that take no shortcut), kept apart from the ladder:
ops[op].typical holds its inputs, gas and summary, and gas.md shows it as a
second table. ops[op].summary stays the ladder's.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = "fp256" if "--lib" in sys.argv and sys.argv[sys.argv.index("--lib") + 1] == "fp256" else "fp127"
OUT_JSON = ROOT / "docs" / "benchmarks" / ("gas256.json" if LIB == "fp256" else "gas.json")
OUT_MD = ROOT / "docs" / "benchmarks" / ("gas256.md" if LIB == "fp256" else "gas.md")
FORMS = ["yul", "lib", "fp127lib", "quad"] if LIB == "fp256" else ["huff", "yul", "caller", "lib", "abdk", "solady", "prb", "quad", "balancer"]
FORM_LABEL = {
    "huff": "Huff (Sepolia, staticcall)",
    "yul": "Yul object (staticcall)",
    "caller": "FP127Caller",
    "lib": "FP256Lib (inline)" if LIB == "fp256" else "FP127Lib (inline)",
    "abdk": "ABDKMath64x64",
    "solady": "Solady",
    "prb": "PRBMath SD59x18",
    "quad": "ABDKMathQuad",
    "balancer": "Balancer LogExpMath",
    "fp127lib": "FP127Lib (inline), the same op",
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def versions() -> dict[str, str]:
    def tag(path: str) -> str:
        return subprocess.run(["git", "-C", str(ROOT / path), "describe", "--tags", "--always"],
                              capture_output=True, text=True).stdout.strip()
    return {
        "fp127": git("rev-parse", "--short", "HEAD"),
        "huff": "sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616",
        "solady": tag("lib/solady"),
        "prb-math": tag("lib/prb-math"),
        "abdk": tag("lib/abdk-libraries-solidity"),
        "balancer": "balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored)",
        "aave": "aave-v3-origin@8305565ae342 (MathUtils, transcribed)",
        "morpho": "morpho-blue@8e26ca6a8dbc (MathLib, transcribed)",
        "maker": "dss pot.sol rpow via solady " + tag("lib/solady"),
        "forge": subprocess.run(["forge", "--version"], capture_output=True, text=True).stdout.split("\n")[0].strip(),
    }


def collect(e: dict) -> dict:
    n = max(e["inputs"]) + 1 if e["inputs"] else 0
    gas = {f: [e["gas"][f].get(i) for i in range(n)] for f in FORMS}
    summary = {}
    for f in FORMS:
        vals = [g for g in gas[f] if g is not None]
        summary[f] = (
            {"min": min(vals), "median": int(statistics.median(vals)), "max": max(vals)}
            if vals else None
        )
    return {"inputs": [e["inputs"].get(i) for i in range(n)], "gas": gas, "summary": summary}


def table(rows: dict[str, dict]) -> list[str]:
    lines = ["| op | " + " | ".join(FORM_LABEL[f] for f in FORMS) + " |",
             "|---|" + "---:|" * len(FORMS)]
    for op, e in rows.items():
        cells = []
        for f in FORMS:
            s = e["summary"][f]
            cells.append("—" if s is None else f"{s['min']:,} / {s['median']:,} / {s['max']:,}")
        lines.append(f"| {op} | " + " | ".join(cells) + " |")
    return lines


def main() -> int:
    ops: dict[str, dict] = {}
    typ: dict[str, dict] = {}
    for line in sys.stdin:
        line = line.strip()
        if "GAS|" not in line:
            continue
        line = line[line.index("GAS|"):]
        parts = line.split("|")
        if len(parts) == 7 and parts[6].strip() == "typical":
            sets = typ
        elif len(parts) == 6:
            sets = ops
        else:
            continue
        _, op, idx, inp, form, gas = parts[:6]
        e = sets.setdefault(op, {"inputs": {}, "gas": {f: {} for f in FORMS}})
        e["inputs"][int(idx)] = inp.strip()
        e["gas"][form][int(idx)] = None if gas.strip() == "NA" else int(gas)

    out_ops = {}
    for op, e in sorted(ops.items()):
        out_ops[op] = collect(e)
        if op in typ:
            out_ops[op]["typical"] = collect(typ[op])

    doc = {
        "generated": date.today().isoformat(),
        "description": ("Gas per FP256 op across an input ladder: the object (staticcall), the inline library, the same op in FP127Lib on the same value where it fits, and ABDKMathQuad. null = reverted or unsupported. summary holds min/median/max per form. The internal forms are the library call alone, timed inside the harness's entry point net of its dispatch. typical (where present) is the same over random inputs that take no shortcut." if LIB == "fp256" else
                        "Gas per op across an input ladder. First four forms are FP127; the first two and the third include the external call. FP127Lib and the competitors are the internal library call alone, timed inside the harness's entry point net of its dispatch. null = reverted or unsupported. summary holds min/median/max per form, null where there is no measurement. typical (where present) is the same over random inputs that take no shortcut."),
        "versions": versions(),
        "forms": FORMS,
        "formLabels": FORM_LABEL,
        "ops": out_ops,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")

    lines = [
        f"# {'FP256' if LIB == 'fp256' else 'FP127'} gas ladder",
        "",
        f"Generated {doc['generated']} by `make bench`. Versions: " + ", ".join(f"{k} {v}" for k, v in doc["versions"].items()) + ".",
        "",
        "Each cell is min / median / max gas over the op's input ladder. " + (
            "The object column includes the `staticcall` (and the object's own selector dispatch); "
            if LIB == "fp256" else
            "The first two FP127 columns and the Caller column include the `staticcall` (and the object's own selector dispatch); ")
        + "the inline columns are the internal library call alone, timed inside the harness's entry point with the dispatch "
          "outside the window (the same cost for every op, whatever its place in the harness's list). A dash means the "
          "library does not offer the op or reverted on every ladder input.",
        "",
        *table(out_ops),
    ]
    typical = {op: e["typical"] for op, e in out_ops.items() if "typical" in e}
    if typical:
        lines += [
            "",
            "## Typical inputs",
            "",
            "The ladder sits mostly on integers, powers of two and one, where several ops take a shortcut. These rows are "
            "the same forms on random inputs drawn per op from `keccak256(\"typical\", op, i)`: non-integer, not a power "
            "of two, across the op's usual range (`test_ladder_typical`). Min / median / max over the inputs.",
            "",
            *table(typical),
        ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}: {len(out_ops)} ops")
    return 0


if __name__ == "__main__":
    sys.exit(main())

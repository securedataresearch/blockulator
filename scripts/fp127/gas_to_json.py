#!/usr/bin/env python3
"""Turn GAS| lines from test/fp127/GasLadder.t.sol into docs/benchmarks/gas.json
and docs/benchmarks/gas.md.

    forge test --match-contract GasLadder -vv | uv run scripts/fp127/gas_to_json.py

Line format:  GAS|<op>|<inputIndex>|<input hex>|<form>|<gas or NA>
Forms:        huff yul caller lib abdk solady prb quad balancer
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
    "lib": "FP127Lib (inline)",
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


def main() -> int:
    ops: dict[str, dict] = {}
    for line in sys.stdin:
        line = line.strip()
        if "GAS|" not in line:
            continue
        line = line[line.index("GAS|"):]
        parts = line.split("|")
        if len(parts) != 6:
            continue
        _, op, idx, inp, form, gas = parts
        e = ops.setdefault(op, {"inputs": {}, "gas": {f: {} for f in FORMS}})
        e["inputs"][int(idx)] = inp.strip()
        e["gas"][form][int(idx)] = None if gas.strip() == "NA" else int(gas)

    out_ops = {}
    for op, e in sorted(ops.items()):
        n = max(e["inputs"]) + 1 if e["inputs"] else 0
        gas = {f: [e["gas"][f].get(i) for i in range(n)] for f in FORMS}
        summary = {}
        for f in FORMS:
            vals = [g for g in gas[f] if g is not None]
            summary[f] = (
                {"min": min(vals), "median": int(statistics.median(vals)), "max": max(vals)}
                if vals else None
            )
        out_ops[op] = {
            "inputs": [e["inputs"].get(i) for i in range(n)],
            "gas": gas,
            "summary": summary,
        }

    doc = {
        "generated": date.today().isoformat(),
        "description": ("Gas per FP256 op across an input ladder: the object (staticcall), the inline library, the same op in FP127Lib on the same value where it fits, and ABDKMathQuad. null = reverted or unsupported. summary holds min/median/max per form." if LIB == "fp256" else
                        "Gas per op across an input ladder. First four forms are FP127; the first two and the third include the external call. Competitors are measured as internal library calls like FP127Lib. null = reverted or unsupported. summary holds min/median/max per form, null where there is no measurement."),
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
        "Each cell is min / median / max gas over the op's input ladder. The first two FP127 columns and the Caller column include the `staticcall`; FP127Lib and the competitor libraries are internal calls. A dash means the library does not offer the op or reverted on every ladder input.",
        "",
        "| op | " + " | ".join(FORM_LABEL[f] for f in FORMS) + " |",
        "|---|" + "---:|" * len(FORMS),
    ]
    for op, e in out_ops.items():
        cells = []
        for f in FORMS:
            s = e["summary"][f]
            if s is None:
                cells.append("—")
            else:
                cells.append(f"{s['min']:,} / {s['median']:,} / {s['max']:,}")
        lines.append(f"| {op} | " + " | ".join(cells) + " |")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}: {len(out_ops)} ops")
    return 0


if __name__ == "__main__":
    sys.exit(main())

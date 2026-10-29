#!/usr/bin/env python3
"""Turn GAS| lines from test/bl127/GasLadder.t.sol into docs/benchmarks/gas.json
and docs/benchmarks/gas.md.

    forge test --match-contract GasLadder -vv | uv run scripts/bl127/gas_to_json.py

Line format:  GAS|<op>|<inputIndex>|<input hex>|<form>|<gas, NA or REV>[|typical]
Forms:        huff yul caller lib abdk solady prb quad balancer solmate oz uniswap prbud snekmate

NA: the form does not offer the op. REV: it does, but reverted on that input,
or the input is outside the function's domain or its format's range.
ops[op].reverts counts the REV inputs per form; a form with no gas and a
revert count reverted on every input ("rev" in gas.md and on the site).

CALLS says what each competitor cell calls; the run fails if a cell is
measured (or reverts) without an entry here, or an entry has no cell, so the
list and the harness cannot drift. docs/benchmarks/coverage.md maps every
function of every comparison library to an op or says why it is not compared.

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
LIB = "bl19" if "--lib" in sys.argv and sys.argv[sys.argv.index("--lib") + 1] == "bl19" else "bl127"
OUT_JSON = ROOT / "docs" / "benchmarks" / ("gas19.json" if LIB == "bl19" else "gas.json")
OUT_MD = ROOT / "docs" / "benchmarks" / ("gas19.md" if LIB == "bl19" else "gas.md")
FORMS = ["yul", "lib", "bl127lib", "quad"] if LIB == "bl19" else ["huff", "yul", "caller", "lib", "abdk", "solady", "prb", "quad", "balancer", "solmate", "oz", "uniswap", "prbud", "snekmate"]
FORM_LABEL = {
    "huff": "Huff (Sepolia, staticcall)",
    "yul": "Yul object (staticcall)",
    "caller": "BL127Caller",
    "lib": "BL19Lib (inline)" if LIB == "bl19" else "BL127Lib (inline)",
    "abdk": "ABDKMath64x64",
    "solady": "Solady",
    "prb": "PRBMath SD59x18",
    "quad": "ABDKMathQuad",
    "balancer": "Balancer LogExpMath",
    "solmate": "Solmate",
    "oz": "OpenZeppelin Math",
    "uniswap": "Uniswap FullMath",
    "prbud": "PRBMath UD60x18",
    "snekmate": "snekmate (Vyper)",
    "bl127lib": "BL127Lib (inline), the same op",
}

# What each competitor cell calls. "composed" marks a cell built from the
# library's own functions where it has no function of that name; a note in
# parentheses is a domain the harness keeps to, or a rounding difference.
CALLS_BL127 = {
    "abdk": {
        "exp": "exp(x)", "exp2": "exp_2(x)", "ln": "ln(x)", "log2": "log_2(x)", "sqrt": "sqrt(x)",
        "inv": "inv(x)", "abs": "abs(x)", "neg": "neg(x)",
        "add": "add(a, b)", "sub": "sub(a, b)", "mul": "mul(a, b)", "div": "div(a, b)",
        "avg": "avg(a, b)", "gavg": "gavg(a, b)",
        "powu": "pow(x, n), n a uint256 (n >= 0)",
    },
    "solady": {
        "exp": "expWad(x)", "ln": "lnWad(x)", "lambertW0": "lambertW0Wad(x)",
        "sqrt": "sqrtWad(x) (x >= 0)", "cbrt": "cbrtWad(x) (x >= 0)",
        "inv": "sDivWad(1e18, x) (composed)", "abs": "abs(int256)",
        "log2Up": "log2Up(uint256) on the integer x (integral x >= 1)",
        "factorial": "factorial(uint256) on the integer x (integral x)",
        "add": "rawAdd(int256, int256) (unchecked)", "sub": "rawSub(int256, int256) (unchecked)",
        "mul": "sMulWad(a, b) (toward zero)", "div": "sDivWad(a, b)", "pow": "powWad(x, y)",
        "mulDown": "mulWad(a, b) (a, b >= 0)", "mulUp": "mulWadUp(a, b) (a, b >= 0)",
        "divDown": "divWad(a, b) (a >= 0, b > 0)", "divUp": "divWadUp(a, b) (a >= 0, b > 0)",
        "avg": "avg(int256, int256)", "dist": "dist(int256, int256)",
        "min": "min(int256, int256)", "max": "max(int256, int256)",
        "zeroFloorSub": "zeroFloorSub(uint256, uint256) (a, b >= 0)",
        "gavg": "mulSqrt(a, b) (a, b >= 0)",
        "powu": "rpow(x, n, 1e18) (x >= 0, n >= 0)",
        "clamp": "clamp(int256, int256, int256)",
        "lerp": "lerp(a, b, t, 0, 1e18) (t in [0, 1]: Solady clamps t)",
    },
    "prb": {
        "exp": "exp(x)", "exp2": "exp2(x)", "ln": "ln(x)", "log2": "log2(x)", "log10": "log10(x)",
        "sqrt": "sqrt(x)", "inv": "inv(x)", "abs": "abs(x)", "neg": "unary(x)", "sign": "sign(x)",
        "floor": "floor(x)", "ceil": "ceil(x)", "frac": "frac(x)",
        "add": "add(a, b)", "sub": "sub(a, b)", "mul": "mul(a, b)", "div": "div(a, b)",
        "pow": "pow(x, y)", "powu": "powu(x, n), n a uint256 (n >= 0)",
        "avg": "avg(a, b)", "gavg": "gm(a, b)",
    },
    "quad": {
        "exp": "exp(x)", "exp2": "pow_2(x)", "ln": "ln(x)", "log2": "log_2(x)", "sqrt": "sqrt(x)",
        "inv": "div(fromUInt(1), x) (composed)", "abs": "abs(x)", "neg": "neg(x)", "sign": "sign(x)",
        "add": "add(a, b)", "sub": "sub(a, b)", "mul": "mul(a, b)", "div": "div(a, b)",
        "pow": "exp(mul(y, ln(x))) (composed)",
    },
    "balancer": {
        "exp": "exp(x)", "ln": "ln(x)", "log2": "log(x, 2e18)", "log10": "log(x, 10e18)",
        "sqrt": "pow(x, 0.5e18) (composed; x >= 0)", "cbrt": "pow(x, 333333333333333333) (composed; x >= 0)",
        "pow": "pow(x, y) (x, y >= 0)",
    },
    "solmate": {
        "exp": "wadExp(x)", "ln": "wadLn(x)", "sqrt": "sqrt(x * 1e18) (composed: the integer root; x >= 0)",
        "mul": "wadMul(a, b) (toward zero)", "div": "wadDiv(a, b) (toward zero)", "pow": "wadPow(x, y)",
        "mulDown": "mulWadDown(a, b) (a, b >= 0)", "mulUp": "mulWadUp(a, b) (a, b >= 0)",
        "divDown": "divWadDown(a, b) (a, b >= 0)", "divUp": "divWadUp(a, b) (a, b >= 0)",
        "powu": "rpow(x, n, 1e18) (x >= 0, n >= 0)",
    },
    "oz": {
        "abs": "SignedMath.abs(int256)", "sqrt": "Math.sqrt(x * 1e18) (composed: the integer root; x >= 0)",
        "log2Up": "Math.log2(uint256, Rounding.Ceil) on the integer x (integral x >= 1)",
        "mulDown": "Math.mulDiv(a, b, 1e18) (a, b >= 0)", "mulUp": "Math.mulDiv(a, b, 1e18, Rounding.Ceil) (a, b >= 0)",
        "divDown": "Math.mulDiv(a, 1e18, b) (a, b >= 0)", "divUp": "Math.mulDiv(a, 1e18, b, Rounding.Ceil) (a, b >= 0)",
        "avg": "SignedMath.average(a, b) (toward zero; BL127's avg floors)", "min": "SignedMath.min(a, b)", "max": "SignedMath.max(a, b)",
        "zeroFloorSub": "Math.saturatingSub(uint256, uint256) (a, b >= 0)",
    },
    "uniswap": {
        "mulDown": "FullMath.mulDiv(a, b, 1e18) (a, b >= 0)", "mulUp": "FullMath.mulDivRoundingUp(a, b, 1e18) (a, b >= 0)",
        "divDown": "FullMath.mulDiv(a, 1e18, b) (a, b >= 0)", "divUp": "FullMath.mulDivRoundingUp(a, 1e18, b) (a, b >= 0)",
    },
    "prbud": {
        "exp": "exp(x) (x >= 0)", "exp2": "exp2(x) (x >= 0)", "ln": "ln(x) (x >= 0)", "log2": "log2(x) (x >= 0)",
        "log10": "log10(x) (x >= 0)", "sqrt": "sqrt(x) (x >= 0)", "inv": "inv(x) (x >= 0)",
        "floor": "floor(x) (x >= 0)", "ceil": "ceil(x) (x >= 0)", "frac": "frac(x) (x >= 0)",
        "add": "add(a, b) (a, b >= 0)", "sub": "sub(a, b) (a, b >= 0)", "mul": "mul(a, b) (a, b >= 0)",
        "div": "div(a, b) (a, b >= 0)", "pow": "pow(x, y) (x, y >= 0)",
        "powu": "powu(x, n), n a uint256 (x >= 0, n >= 0)", "avg": "avg(a, b) (a, b >= 0)", "gavg": "gm(a, b) (a, b >= 0)",
    },
    "snekmate": {
        "exp": "_wad_exp(x)", "ln": "_wad_ln(x)", "cbrt": "_wad_cbrt(x) (x >= 0)", "sign": "_signum(x)",
        "log2Up": "_log2(uint256, True) on the integer x (integral x >= 1)",
        "mulDown": "_mul_div(a, b, 1e18, False) (a, b >= 0)", "mulUp": "_mul_div(a, b, 1e18, True) (a, b >= 0)",
        "divDown": "_mul_div(a, 1e18, b, False) (a, b >= 0)", "divUp": "_mul_div(a, 1e18, b, True) (a, b >= 0)",
        "avg": "_int256_average(a, b)",
    },
}
CALLS_BL19 = {
    "quad": {
        "exp": "exp(x)", "exp2": "pow_2(x)", "ln": "ln(x)", "log2": "log_2(x)", "sqrt": "sqrt(x)",
        "inv": "div(fromUInt(1), x) (composed)", "abs": "abs(x)", "neg": "neg(x)", "sign": "sign(x)",
        "add": "add(a, b)", "sub": "sub(a, b)", "mul": "mul(a, b)", "div": "div(a, b)",
        "pow": "exp(mul(y, ln(x))) (composed)",
        "cmp": "cmp(a, b)", "eq": "eq(a, b)", "lt": "cmp(a, b) < 0 (composed)",
        "toUintDown": "toUInt(x) (truncates: floor for x >= 0)",
        "toIntDown": "toInt(x) (truncates: floor for x >= 0, the rows kept)",
        "toBL127": "to128x128(x) (truncates; toBL127 rounds to nearest)",
        "fromBL127": "from128x128(x) (truncates; fromBL127 rounds to nearest)",
        "fromUintDown": "fromUInt(x) (truncates the significand)",
    },
}
CALLS = CALLS_BL19 if LIB == "bl19" else CALLS_BL127


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def versions() -> dict[str, str]:
    def tag(path: str) -> str:
        return subprocess.run(["git", "-C", str(ROOT / path), "describe", "--tags", "--always"],
                              capture_output=True, text=True).stdout.strip()
    return {
        "bl127": git("rev-parse", "--short", "HEAD"),
        "huff": "sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616",
        "solady": tag("lib/solady"),
        "prb-math": tag("lib/prb-math"),
        "abdk": tag("lib/abdk-libraries-solidity"),
        "balancer": "balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored)",
        "aave": "aave-v3-origin@8305565ae342 (MathUtils, transcribed)",
        "morpho": "morpho-blue@8e26ca6a8dbc (MathLib, transcribed)",
        "fraxlend": "fraxlend@2bed49d4dcc6 (VariableInterestRate V2, transcribed)",
        "euler": "evk-periphery@af436991e135 (IRMAdaptiveCurve, ExpLib, transcribed)",
        "maker": "dss pot.sol rpow via solady " + tag("lib/solady"),
        "solmate": "solmate@" + git("-C", str(ROOT / "lib/solmate"), "rev-parse", "--short", "HEAD") + " (no tag: v6 predates SignedWadMath)",
        "openzeppelin": "openzeppelin-contracts v5.7.0 (Math, SignedMath, vendored)",
        "uniswap": "v4-core v4.0.0 (FullMath, vendored)",
        "snekmate": tag("lib/snekmate") + " (math module, vyper 0.4.3)",
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
    out = {"inputs": [e["inputs"].get(i) for i in range(n)], "gas": gas, "summary": summary}
    reverts = {f: len(e["rev"][f]) for f in FORMS if e["rev"][f]}
    if reverts:
        out["reverts"] = reverts
    return out


def check_calls(sets: list[dict]) -> list[str]:
    """Every measured or reverting competitor cell has a CALLS entry and every entry a cell."""
    seen: dict[str, set[str]] = {f: set() for f in CALLS}
    for ops in sets:
        for op, e in ops.items():
            for f in CALLS:
                if e["gas"][f] or e["rev"][f]:
                    seen[f].add(op)
    errs = []
    for f, ops in CALLS.items():
        for op in sorted(seen[f] - set(ops)):
            errs.append(f"{f}.{op} is measured but has no CALLS entry")
        for op in sorted(set(ops) - seen[f]):
            errs.append(f"{f}.{op} is in CALLS but the harness has no cell for it")
    return errs


def table(rows: dict[str, dict]) -> list[str]:
    lines = ["| op | " + " | ".join(FORM_LABEL[f] for f in FORMS) + " |",
             "|---|" + "---:|" * len(FORMS)]
    for op, e in rows.items():
        cells = []
        for f in FORMS:
            s = e["summary"][f]
            cells.append(f"{s['min']:,} / {s['median']:,} / {s['max']:,}" if s
                         else "rev" if e.get("reverts", {}).get(f) else "")
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
        e = sets.setdefault(op, {"inputs": {}, "gas": {f: {} for f in FORMS}, "rev": {f: set() for f in FORMS}})
        e["inputs"][int(idx)] = inp.strip()
        g = gas.strip()
        if g == "REV":
            e["rev"][form].add(int(idx))
        elif g != "NA":
            e["gas"][form][int(idx)] = int(g)

    errs = check_calls([ops, typ])
    if errs:
        print("gas_to_json: CALLS and the harness disagree:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1

    out_ops = {}
    for op, e in sorted(ops.items()):
        out_ops[op] = collect(e)
        if op in typ:
            out_ops[op]["typical"] = collect(typ[op])

    doc = {
        "generated": date.today().isoformat(),
        "description": ("Gas per BL19 op across an input ladder: the object (staticcall), the inline library, the same op in BL127Lib on the same value where it fits, and ABDKMathQuad. null = no measurement on that input; reverts counts, per form, the inputs where the form offers the op but reverted or the input is outside its domain or format; a form with neither gas nor reverts does not offer the op. calls says what each Quad cell calls. summary holds min/median/max per form. The internal forms are the library call alone, timed inside the harness's entry point net of its dispatch. typical (where present) is the same over random inputs that take no shortcut." if LIB == "bl19" else
                        "Gas per op across an input ladder. First four forms are BL127; the first two and the third include the external call. BL127Lib and the competitors are the internal library call alone, timed inside the harness's entry point net of its dispatch. null = no measurement on that input; reverts counts, per form, the inputs where the form offers the op but reverted or the input is outside its domain or format; a form with neither gas nor reverts does not offer the op (the Huff and BL127Caller columns record any failure as not offered). calls says what each competitor cell calls. summary holds min/median/max per form, null where there is no measurement. typical (where present) is the same over random inputs that take no shortcut."),
        "versions": versions(),
        "forms": FORMS,
        "formLabels": FORM_LABEL,
        "calls": CALLS,
        "ops": out_ops,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")

    lines = [
        f"# {'BL19' if LIB == 'bl19' else 'BL127'} gas ladder",
        "",
        f"Generated {doc['generated']} by `make bench`. Versions: " + ", ".join(f"{k} {v}" for k, v in doc["versions"].items()) + ".",
        "",
        "Each cell is min / median / max gas over the op's input ladder. " + (
            "The object column includes the `staticcall` (and the object's own selector dispatch); "
            if LIB == "bl19" else
            "The first two BL127 columns and the Caller column include the `staticcall` (and the object's own selector dispatch); ")
        + "the inline columns are the internal library call alone, timed inside the harness's entry point with the dispatch "
          "outside the window (the same cost for every op, whatever its place in the harness's list). An empty cell means "
          "the library does not offer the op; `rev` means it does, but reverted (or the input was outside its domain or "
          "format) on every ladder input. What each library cell calls is listed at the end; "
          "[coverage.md](coverage.md) maps every function of every comparison library.",
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
    lines += ["", "## What each cell calls", "",
              "The competitor function behind each cell, on the inputs converted once to its representation. "
              "\"composed\" is built from the library's own functions where it has none of that name; a note in "
              "parentheses is the domain the harness keeps to (other inputs count as `rev`) or a rounding difference.", "",
              "| op | " + " | ".join(FORM_LABEL[f] for f in CALLS) + " |", "|---|" + "---|" * len(CALLS)]
    for op in sorted({o for c in CALLS.values() for o in c}):
        lines.append(f"| {op} | " + " | ".join(f"`{CALLS[f][op]}`" if op in CALLS[f] else "" for f in CALLS) + " |")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}: {len(out_ops)} ops")
    return 0


if __name__ == "__main__":
    sys.exit(main())

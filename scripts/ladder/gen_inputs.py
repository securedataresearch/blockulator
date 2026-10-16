#!/usr/bin/env python3
"""Generate scripts/ladder/inputs.json from scripts/ladder/scenarios.json.

Every input's parameters are resolved exactly (mpmath at 200 digits; derived
values such as the amortisation payment computed here, so the contracts hold
no arithmetic that is not a step) and floored once into each representation:
127.128 (2^128), 64.64 (2^64) and WAD (1e18). The harness (test/ladder) and
the live checks (livecap.py, liveedges.py) pass these integers to the adapters as calldata.

    uv run scripts/ladder/gen_inputs.py          # write
    uv run scripts/ladder/gen_inputs.py --check  # fail if stale
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from mpmath import mp, mpf

mp.dps = 200
ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts" / "ladder" / "scenarios.json"
OUT = ROOT / "scripts" / "ladder" / "inputs.json"

# scale name -> (exponent form, integer scale, int range the adapter accepts)
SCALES = {
    "fp127": ("2**128", 2 ** 128, (-(2 ** 255), 2 ** 255 - 1)),
    "abdk": ("2**64", 2 ** 64, (-(2 ** 127), 2 ** 127 - 1)),
    "wad": ("10**18", 10 ** 18, (-(2 ** 255), 2 ** 255 - 1)),
    "ray": ("10**27", 10 ** 27, (-(2 ** 255), 2 ** 255 - 1)),
    # binary128 is not a grid: the value is encoded to nearest as the bit
    # pattern of a bytes16 (scale None marks it; see quad_encode)
    "quad": ("binary128", None, (0, 2 ** 128 - 1)),
    # FP256, the 256-bit float: the word from scripts/fp256/oracle.py
    "fp256": ("fp256", "fp256", (-(2 ** 255), 2 ** 255 - 1)),
}

import sys as _sys
_sys.path.insert(0, str(ROOT / "scripts" / "fp256"))
import oracle as _fp256  # noqa: E402
from fractions import Fraction as _Fraction  # noqa: E402


def fp256_encode(v) -> int:
    """The FP256 word nearest to an mpf value (exact rational of its binary form)."""
    if v == 0:
        return 0
    m, e = mp.frexp(abs(v))
    T = int(mp.floor(m * mpf(2) ** 238))
    w = _fp256.encode_tm(1 if v < 0 else 0, int(e) - 1, T)
    # as a signed int256 (the harness parses the column with vm.parseInt)
    return w - 2 ** 256 if w >= 2 ** 255 else w


def fp256_decode(w: int):
    q = _fp256.decode(w)
    return mpf(q.numerator) / q.denominator


def quad_encode(v) -> int:
    """IEEE 754 binary128 bit pattern of v, rounded to nearest, as an int."""
    if v == 0:
        return 0
    sign = 1 if v < 0 else 0
    v = abs(v)
    ex = int(mp.floor(mp.log(v, 2)))
    m = v / mpf(2) ** ex
    while m >= 2:
        ex += 1
        m /= 2
    while m < 1:
        ex -= 1
        m *= 2
    frac = int(mp.floor((m - 1) * 2 ** 112 + mpf("0.5")))
    if frac >= 2 ** 112:
        frac = 0
        ex += 1
    return (sign << 127) | ((ex + 16383) << 112) | frac


def quad_decode(u: int):
    """The exact value of a binary128 bit pattern, or None for NaN / infinity."""
    sign = u >> 127
    ex = (u >> 112) & 0x7FFF
    frac = u & ((1 << 112) - 1)
    if ex == 0x7FFF:
        return None
    if ex == 0:
        v = mpf(frac) * mpf(2) ** (-16382 - 112)
    else:
        v = (1 + mpf(frac) / 2 ** 112) * mpf(2) ** (ex - 16383)
    return -v if sign else v


def to_scaled(x, scale) -> int:
    """x into a representation: floor(x * scale) on a grid, nearest for the floats."""
    if scale is None:
        return quad_encode(x)
    if scale == "fp256":
        return fp256_encode(x)
    return int(mp.floor(x * scale))


def from_scaled(raw: int, scale):
    """The exact value a representation holds."""
    if scale is None:
        return quad_decode(raw)
    if scale == "fp256":
        return fp256_decode(raw)
    return mpf(raw) / scale


def value(expr: str):
    """Decimal literal or a/b of decimal literals."""
    if "/" in expr:
        a, b = expr.split("/")
        return mpf(a.strip()) / mpf(b.strip())
    return mpf(expr.strip())


def derived(params: dict, name: str):
    if name == "payment":
        P, r, n = params["principal"], params["rate"], params["term"]
        return P * r / (1 - (1 + r) ** (-n))
    if name == "rateSec":
        return params["rateAnnual"] / 31536000
    raise KeyError(name)


def resolve(params: dict, derived_names=()) -> dict:
    """Exact mpf values for a parameter set, derived values included."""
    p = {k: value(v) for k, v in params.items()}
    for k in derived_names:
        p[k] = derived(p, k)
    return p


def floor_scaled(x, scale: int) -> int:
    return int(mp.floor(x * scale))


def build(spec: dict) -> dict:
    cells = []
    for scn in spec["scenarios"]:
        for inp in scn["inputs"]:
            p = resolve(inp["params"], scn.get("derived", {}))
            cell = {"scenario": scn["index"], "id": scn["id"], "input": inp["name"], "order": scn["order"]}
            unrep = {}
            for name, (_, scale, (lo, hi)) in SCALES.items():
                ints = [to_scaled(p[k], scale) for k in scn["order"]]
                cell[name] = [str(i) for i in ints]
                unrep[name] = any(i < lo or i > hi for i in ints) if scale != "fp256" else False
            cell["unrepresentable"] = unrep
            cells.append(cell)
    return {
        "_doc": "Generated by scripts/ladder/gen_inputs.py from scenarios.json: every input's parameters floored into each representation (encoded to nearest for binary128), as decimal strings, in the scenario's `order`. unrepresentable marks a value outside the adapter's integer type; the adapter reverts ParamOutOfRange for it.",
        "ladder": spec["ladder"],
        "scales": {k: v[0] for k, v in SCALES.items()},
        "count": len(cells),
        "cells": cells,
    }


def main(argv: list[str]) -> int:
    text = json.dumps(build(json.loads(SPEC.read_text())), indent=1) + "\n"
    if "--check" in argv:
        if OUT.exists() and OUT.read_text() == text:
            print("gen-inputs ok")
            return 0
        print("inputs.json is stale; run `make gen-inputs`")
        return 1
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

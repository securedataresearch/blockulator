#!/usr/bin/env python3
"""Build docs/benchmarks/ladder.json and ladder.md from the harness output.

    forge test --match-path "test/ladder/*" -vv | uv run scripts/ladder/ladder.py
    forge test --match-path "test/ladder/*" -vv | uv run scripts/ladder/ladder.py --check
    uv run scripts/ladder/ladder.py --selftest

Input lines (test/ladder/Ladder.t.sol):
    LADDER|<scenario>|<input>|<form>|<N>|<ok 0/1>|<raw int>|<reason bytes4>|<gasTotal>

Two truths per scenario, input and N, both the scenario's loop in exact real
arithmetic with mpmath at 300 digits:
    truth         from the exact rational parameters in scenarios.json
    truthFormat   per scale (2**128, 2**64, 10**18, 10**27, binary128, FP19):
                  the same loop started from the parameters as that scale
                  holds them (floored on the grids, nearest on the floats),
                  which is what the library actually received
Per cell, with v the decoded value, t the truth, tf the format truth:
    digits        floor(-log10(|v - t| / |t|)), an integer; v == t is
                  DIGITS_CAP (100) with exact = true. Kept for older readers.
    digitsFormat  the same against tf
    digits1, digitsFormat1
                  -log10 of the relative error, floored to one decimal (a
                  decimal string), absent when exact
    prec          what the format holds at the truth's magnitude, one decimal:
                  237 log10 2 for FP19, 113 log10 2 for binary128, and
                  -log10(ulp / |t|) on the grids (2^-128, 2^-64, 1e-18, 1e-27)
    digitsCapped, digitsFormatCapped
                  min(digits1, prec), and prec when exact: the only values
                  the charts plot and the summaries aggregate, so no median
                  or band exceeds what the format holds
    interestDigits1, interestCapped (compounding and accrual scenarios)
                  the same measured on the interest, b - principal
    absErrWei     (deep-tail-option) |v - t| in wei of the strike at 18
                  decimals
    agree         leading significant digits of the value string that are
                  literally equal to the truth string (both 42 significant
                  digits); for highlighting only, never a precision claim
    errUlps       (v - t) in units of the form's last place, signed
    relErr        (v - t) / t, signed
Summaries (per scenario, form and N) aggregate the capped values over the
inputs every shown library completed (see `common_inputs`), and report each
library's completed count.
No JSON floats: every measurement is a decimal string or an integer.
`--check` compares every measurement exactly and gas within max(2 %, 3 gas),
and both modes assert the dataset's invariants (`invariants`).
"""
from __future__ import annotations

import datetime
import json
import sys
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

from mpmath import mp, mpf, log, exp, sqrt, ncdf, nstr, floor as mfloor_

mp.dps = 300
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fp127"))
sys.path.insert(0, str(ROOT / "scripts" / "ladder"))
from gas_to_json import versions  # noqa: E402
from gen_inputs import resolve, to_scaled, from_scaled, SCALES as INPUT_SCALES  # noqa: E402

SPEC = ROOT / "scripts" / "ladder" / "scenarios.json"
OUT_JSON = ROOT / "docs" / "benchmarks" / "ladder.json"
OUT_MD = ROOT / "docs" / "benchmarks" / "ladder.md"
RECORD = ROOT / "contracts" / "deployments" / "Ladder.json"
DIGITS_CAP = 100  # the integer digits of an exact cell (v == t); the only cap on `digits`
AXIS_MAX = 80     # the charts' y axis; no plotted value is capped here (they are capped at prec)
SIG = 42          # significant digits kept for value/truth strings
FLOAT_BITS = {"quad": 113, "fp19": 237}
GRID_ULP = {"fp127": mpf(2) ** -128, "abdk": mpf(2) ** -64, "wad": mpf(10) ** -18, "ray": mpf(10) ** -27}
# scenarios whose result is a balance grown from `principal`: digits are also measured on the interest
INTEREST = {"compound", "compound-pow", "compound-annual", "accrual-per-second", "accrual-continuous"}
# deep-tail-option: absolute error in the strike's smallest unit, 18 decimals
WEI = {"deep-tail-option": mpf(10) ** 18}
SCALE_OF_FORM = {"fp127": "fp127", "fp127lib": "fp127", "abdk": "abdk", "solady": "wad", "prb": "wad",
                 "quad": "quad", "balancer": "wad", "aave": "ray", "morpho": "wad", "maker": "ray", "fp19": "fp19",
                 "solmate": "wad", "oz": "wad", "uniswap": "wad", "prbud": "wad", "snekmate": "wad",
                 "fraxlend": "wad", "euler": "wad"}
SCALE_INT = {k: v[1] for k, v in INPUT_SCALES.items()}
SCALE_NAME = {k: v[0] for k, v in INPUT_SCALES.items()}
REASONS = {
    "0x35278d12": "Overflow()", "0x23d359a3": "DivisionByZero()", "0x7db3aba7": "OutOfRange()",
    "0x00000000": "bare revert (require without a reason, or out of gas)",
    "0xedcd4dd4": "Solady SMulWadFailed()", "0xa37bfec9": "Solady ExpOverflow()",
    "0x120b5b43": "PRBMath_SD59x18_Mul_Overflow",
    "0x4e487b71": "Panic (checked arithmetic overflow or division by zero)",
    "0x49f7642b": "Solady RPowOverflow() (Maker's rpow)",
    "0x7964b44f": "ParamOutOfRange(uint256): the value does not fit the representation",
    "0x7bb9ae15": "Unsupported(uint8): the library has no model for this scenario",
    "0xa28f5c6b": "Quad NaN or infinity",
    "0x34d81929": "Negative(): a negative value where the library is unsigned (Balancer pow, PRBMath UD60x18, the WAD roots)",
    "0x059b101b": "PRBMath_SD59x18_Log_InputTooSmall", "0x063103bf": "PRBMath_SD59x18_Sqrt_Overflow",
    "0xca7ec0c5": "PRBMath_SD59x18_Exp_InputTooBig", "0x36d32ef0": "PRBMath_UD60x18_Log_InputTooSmall",
    "0x1af63aca": "PRBMath_UD60x18_Exp_InputTooBig", "0xedc236ad": "PRBMath_UD60x18_Sqrt_Overflow",
    "0x1615e638": "Solady LnWadUndefined()", "0x5c43740d": "Solady SDivWadFailed()",
    "0x08c379a0": "Error(string): a require with a message (Solmate's wadLn and snekmate's wad_ln below zero)",
    "0x022701e0": "Balancer BaseOutOfBounds()", "0xd8317311": "Balancer ExponentOutOfBounds()",
    "0xa2f9f7e3": "Balancer ProductOutOfBounds()", "0xd4794efd": "Balancer InvalidExponent()", "0xb4120f14": "Balancer OutOfBounds()",
}
PARAM_OUT_OF_RANGE = "0x7964b44f"
# the Solidity signature behind each named selector, checked by --selftest (keccak, first four bytes)
REASON_SIGS = {
    "0x35278d12": "Overflow()", "0x23d359a3": "DivisionByZero()", "0x7db3aba7": "OutOfRange()",
    "0xedcd4dd4": "SMulWadFailed()", "0xa37bfec9": "ExpOverflow()", "0x49f7642b": "RPowOverflow()",
    "0x4e487b71": "Panic(uint256)", "0x7964b44f": "ParamOutOfRange(uint256)", "0x7bb9ae15": "Unsupported(uint8)",
    "0x34d81929": "Negative()",
}

METHODOLOGY = {
    "truth": "For every scenario, input and N the same loop is run in exact real arithmetic with mpmath at 300 decimal digits (scripts/ladder/ladder.py), from the exact rational parameters in scenarios.json. Closed forms are used where the loop has one (compounding, the cumulative product, the geometric mean, the round trip, per-second and continuous accrual, the option walk, the decay and the adaptive rate); the bonding curve, the amortising loan and the Black-Scholes chain are stepped.",
    "rounding": "Inputs are floored on the grids and rounded to nearest on the floats: each library receives the parameters floored into its own representation (2^-128, 2^-64, 10^-18 or 10^-27 units) or, for ABDKMathQuad and FP19, the nearest float (scripts/ladder/inputs.json). truthFormat is the exact loop started from those parameters, so digitsFormat measures the library's arithmetic alone, while digits measures what a protocol sees: the format's rounding of the inputs plus the arithmetic. One exception: Morpho accrues from the per-second rate, rateAnnual / 31536000 floored to WAD, while truthFormat is built from the annual rate the other libraries receive, so Morpho's digitsFormat still includes its own input's rounding. Likewise in the adaptive rate, FraxLend and Euler compute from their own inputs (utilisation, step, half-life or speed) while truthFormat is built from rate0 and x, so their digitsFormat includes the rounding of those inputs (Euler's speed floored to WAD per second, FraxLend's half-life to whole seconds).",
    "inputs": "The parameters are short decimals (0.1/365, 10000, 0.05) as a protocol's governance would set them. A short decimal can sit exactly on the 10^-18 and 10^-27 grids, so WAD and RAY libraries often receive their inputs exactly while the binary formats round them; this favours WAD and RAY in digits (against exact inputs) and is visible as the gap between digits and digitsFormat. The decay scenario's eps are reciprocals of time constants in seconds (1/1036800 for twelve days), which no grid holds exactly.",
    "powers": "Integer powers are each library's own idiom, not one algorithm: FP127 and FP19 use compound (a correctly rounded (1 + r)^n that never forms a rounded 1 + r), Maker uses rpow (binary exponentiation in RAY), the WAD and 64.64 libraries and binary128 use exp(n ln(1 + r)) or their pow. Per-second accrual and compound-pow measure those choices as much as the formats.",
    "digits": "digits = floor(-log10 |v - t| / |t|), the number of correct leading significant digits by relative error, an integer; a result equal to the truth is exact (exact = true, digits = 100, the one cap on this field) and is drawn as a marker, never as a number. digits1 is the same quantity floored to one decimal instead of to an integer. It is not a string comparison: a value can be correct to 36 digits while its 37th printed digit happens to agree with the truth, or while a carry makes the printed prefix differ earlier.",
    "precision": "No format can be right to more digits than it holds at the result's magnitude: prec is 237 log10 2 = 71.3 for FP19 and 113 log10 2 = 34.0 for binary128 at any magnitude, and -log10(ulp / |t|) on the fixed grids, with ulp 2^-128 (FP127), 2^-64 (64.64), 10^-18 (WAD) or 10^-27 (RAY): 38.5 for FP127 at 1, 42.5 at 10^4. A cell may land closer to the truth than that by luck; digitsCapped = min(digits1, prec), and prec for an exact cell, is what the charts plot and the summaries aggregate, so no median or band exceeds the format's precision.",
    "summary": "Each scenario's median, minimum and maximum at each N are taken over the inputs that every library with any completed input at that N completed, so every library's median is over the same inputs. Each library's completed count is reported, and a library that completed fewer than all inputs is shown as k/n. Where no input is common to all of them, a revert counts as 0 digits over all inputs instead (basis revertsAsZero); the dataset records the basis and the inputs per N.",
    "interest": "For the compounding and accrual scenarios the digits are also measured on the interest, b - principal against t - principal (interestDigits1, interestCapped, with the format's precision taken against the interest's magnitude). Relative digits of a balance flatter a format when the interest is a small part of it: after one day the interest is about 10^-4 of the balance.",
    "wei": "For the deep-tail option, absErrWei is |v - t| in wei of the strike at 18 decimals ($100 = 10^20 wei). Past d1 = -8 the true price falls below one wei and every library's error with it, so relative digits there describe the format, not money.",
    "headline": "The Results page shows a single N = 10,000 per scenario; the ladder page shows every N.",
    "agree": "agree is the count of leading significant digits of the printed value (42 significant digits) that are literally equal to the printed truth. The demo page colours the rest of the value with it. It is a reading aid, not a measurement: a carry across 0.999… / 1.000… gives 0.",
    "gas": "gasTotal is measured inside the adapter around the scenario function (the parameter reads and the loop), after the runner has warmed the adapter and the FP127 object, so the call into the adapter and the ABI decoding are excluded. The FP127 (deployed) form includes one staticcall per op, and so does snekmate, a Vyper library that a Solidity adapter can only call; FP127Lib and the other libraries are internal calls. Aave, Morpho and Maker answer only the accrual scenarios their models describe, FraxLend and Euler only the adaptive rate, and OpenZeppelin and Uniswap FullMath, which have no exp, ln or real power (and FullMath no root), only the scenarios built from mul, div and their roots; each reports Unsupported elsewhere, which the tables and charts leave empty (a library with no model is not a revert). gasPerStep = gasTotal / N. Reverted cells carry no gas.",
    "live": "LadderRunner.run(scenario, form, n, p) on Sepolia executes any cell with one eth_call and returns (ok, raw, reason, gasPerStep, gasTotal). scripts/ladder/livecap.py sends every cell's floored parameters p and compares the returned raw word with the committed one bit for bit (or the revert selector for a reverted cell). liveMaxN is the largest N per form the public RPC completed within its gas limit, measured by scripts/ladder/livecap.py.",
    "reproduce": "make ladder regenerates ladder.json and ladder.md from the Foundry harness (test/ladder/Ladder.t.sol) and this script; make ladder-check fails CI when the committed dataset differs. Versions of every library and of forge are recorded in the dataset.",
}


# ---------------------------------------------------------------------------
# Truth: the scenario loops in exact real arithmetic, recorded at every ladder N
# ---------------------------------------------------------------------------

def truths(sid: str, p: dict, ns: list[int]) -> dict[int, mpf]:
    """{N: value} for every N in ns (sorted), stepping each loop once."""
    out = {}
    if sid in ("compound", "compound-annual", "compound-pow"):
        for n in ns:
            out[n] = p["principal"] * (1 + p["rate"]) ** n
    elif sid == "accrual-per-second":
        for n in ns:
            out[n] = p["principal"] * (1 + p["rateSec"]) ** (n * 86400)
    elif sid == "accrual-continuous":
        for n in ns:
            out[n] = p["principal"] * exp(p["rateAnnual"] * mpf(n) / 365)
    elif sid == "deep-tail-option":
        S0, K, sg, T, r, tick = p["spot"], p["strike"], p["sigma"], p["T"], p["r"], p["tick"]
        vs = sg * sqrt(T)
        for n in ns:
            S = S0 * (1 - tick) ** n
            d1 = (log(S / K) + (r + sg * sg / 2) * T) / vs
            d2 = d1 - vs
            out[n] = S * ncdf(d1) - K * exp(-r * T) * ncdf(d2)
    elif sid == "decay":
        for n in ns:
            out[n] = 1 - exp(-p["eps"] * n)
    elif sid == "adaptive-rate":
        for n in ns:
            out[n] = p["rate0"] * exp(p["x"] * n)
    elif sid == "roundtrip":
        for n in ns:
            out[n] = p["x0"]
    elif sid == "geo-mean":
        for n in ns:
            out[n] = (mpf(n + 2) / 2) ** (mpf(1) / n)
    elif sid == "cumulative-product":
        e = p["eps"]
        for n in ns:
            out[n] = (1 + e) ** ((n + 1) // 2) * (1 - e) ** (n // 2)
    elif sid == "bonding-sqrt":
        s, cost, k = p["supply"], mpf(0), 0
        for n in ns:
            while k < n:
                cost += sqrt(s)
                s += p["unit"]
                k += 1
            out[n] = cost
    elif sid == "amortise":
        b, g, pay, k = p["principal"], 1 + p["rate"], p["payment"], 0
        for n in ns:
            while k < n:
                b = b * g - pay
                k += 1
            out[n] = b
    elif sid == "black-scholes-chain":
        S, K, sig, T, r, tick = (p[k] for k in ("spot", "strike", "sigma", "T", "r", "tick"))
        drift = (r + sig * sig / 2) * T
        denom = sig * sqrt(T)
        acc, k = mpf(0), 0
        for n in ns:
            while k < n:
                acc += (log(S / K) + drift) / denom
                S += tick
                k += 1
            out[n] = acc
    else:
        raise KeyError(sid)
    return out


def floored_params(p: dict, scale) -> dict:
    """The parameters as the library received them: floor(x * scale) / scale, exact
    (the nearest binary128 value for the quad scale)."""
    return {k: from_scaled(to_scaled(v, scale), scale) for k, v in p.items()}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def sig_digits(s: str) -> str:
    """The significant digits of a decimal string: sign, leading zeros and the point removed."""
    s = s.lstrip("-").lstrip("0").lstrip(".").lstrip("0") if not s.lstrip("-").startswith("0.") else s.lstrip("-")[2:].lstrip("0")
    return s.replace(".", "")


def agree_count(value: str, truth: str) -> int:
    a, b = sig_digits(value), sig_digits(truth)
    # the mantissas must also start at the same decade: compare integer-part lengths
    def intlen(x: str) -> int:
        x = x.lstrip("-")
        return len(x.split(".")[0].lstrip("0")) if not x.startswith("0.") else -(len(x[2:]) - len(x[2:].lstrip("0")))
    if intlen(value) != intlen(truth) or (value.startswith("-") != truth.startswith("-")):
        return 0
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return min(n, SIG)


def digits_of(v, t) -> int:
    if v == t:
        return DIGITS_CAP
    if t == 0:
        return 0
    rel = abs(v - t) / abs(t)
    if rel == 0:
        return DIGITS_CAP
    return min(DIGITS_CAP, max(0, int(mfloor_(-log(rel, 10)))))


def signed(x) -> str:
    return nstr(x, 6) if x != 0 else "0"


def metrics(raw: int, scale, t, tf) -> dict:
    v = from_scaled(raw, scale)
    value = nstr(v, SIG)
    truth_s = nstr(t, SIG)
    d = digits_of(v, t)
    return {
        "value": value,
        "digits": d,
        "digitsFormat": digits_of(v, tf),
        "exact": d >= DIGITS_CAP,
        "agree": agree_count(value, truth_s),
        "errUlps": signed((v - t) * scale) if scale and scale != "fp19" else None,
        "relErr": signed((v - t) / t) if t != 0 else None,
    }


def parse_lines(stream) -> dict:
    """cells[scenario][input][form][N] = {ok, raw, reason, gas}"""
    cells: dict = {}
    for line in stream:
        if "LADDER|" not in line:
            continue
        parts = line[line.index("LADDER|"):].strip().split("|")
        if len(parts) != 9:
            continue
        _, scn, inp, form, n, ok, raw, reason, gas = parts
        cells.setdefault(scn, {}).setdefault(inp, {}).setdefault(form, {})[int(n)] = {
            "ok": ok == "1", "raw": int(raw), "reason": reason[:10], "gas": int(gas),
        }
    return cells


TENTH = Decimal("0.1")


def tenths(x) -> str:
    """x floored to one decimal, as a decimal string ("32.6"); never below 0."""
    q = max(int(mfloor_(x * 10)), 0)
    return f"{q // 10}.{q % 10}"


def precision(sc: str, mag):
    """The digits format sc holds at magnitude mag: p log10 2 on the floats, -log10(ulp / mag) on the grids."""
    if sc in FLOAT_BITS:
        return FLOAT_BITS[sc] * log(mpf(2), 10)
    if mag == 0:
        return mpf(0)
    return max(mpf(0), -log(GRID_ULP[sc] / abs(mag), 10))


def rel_digits(v, t):
    """-log10 |v - t| / |t|, not floored; None when exact (v == t, or within 10^-100 relative, which is
    the truth's own 300-digit rounding: digits_of reports those as DIGITS_CAP)."""
    if v == t:
        return None
    if t == 0:
        return mpf(0)
    d = -log(abs(v - t) / abs(t), 10)
    return None if d >= DIGITS_CAP else d


def capped(d, prec) -> str:
    return tenths(prec if d is None else min(d, prec))


def ladder_fields(raw: int, sc: str, t, tf, principal=None, wei=None) -> dict:
    """The ladder's one-decimal, precision-capped fields of one completed cell (see the module docstring)."""
    v = from_scaled(raw, SCALE_INT[sc])
    out = {}
    pr = precision(sc, t)
    d, df = rel_digits(v, t), rel_digits(v, tf)
    out["prec"] = tenths(pr)
    if d is not None:
        out["digits1"] = tenths(min(d, DIGITS_CAP))
    if df is not None:
        out["digitsFormat1"] = tenths(min(df, DIGITS_CAP))
    out["digitsCapped"] = capped(d, pr)
    out["digitsFormatCapped"] = capped(df, precision(sc, tf))
    if principal is not None:
        it = t - principal
        if it != 0:
            # a float holds |t| 2^-p absolutely; a grid holds its ulp
            ip = (precision(sc, t) - log(abs(t) / abs(it), 10)) if sc in FLOAT_BITS else precision(sc, it)
            di = rel_digits(v - principal, it)
            if di is not None:
                out["interestDigits1"] = tenths(min(di, DIGITS_CAP))
            out["interestCapped"] = capped(di, max(mpf(0), ip))
    if wei is not None:
        out["absErrWei"] = sci3(abs(v - t) * wei)
    if sc in GRID_ULP:
        out["ulps"] = sci3((v - t) / GRID_ULP[sc])
    return out


def sci3(x) -> str:
    """One number format for the page: three significant digits, plain from 0.001 to below 1000, else
    m.mm×10^k written m.mme±k; "0" for zero. The sign is kept."""
    if x == 0:
        return "0"
    a = abs(x)
    if mpf("0.001") <= a < 1000:
        s = nstr(x, 3, strip_zeros=True)
        return s[:-2] if s.endswith(".0") else s
    e = int(mfloor_(log(a, 10)))
    m = x / mpf(10) ** e
    if abs(m) >= mpf("9.995"):
        m, e = m / 10, e + 1
    return f"{nstr(m, 3, strip_zeros=False, min_fixed=-1, max_fixed=2)}e{e:+d}"


def dmedian(xs: list[str]) -> str:
    """The median of one-decimal strings, to one decimal (half-even)."""
    ds = sorted(Decimal(x) for x in xs)
    m = len(ds) // 2
    v = ds[m] if len(ds) % 2 else (ds[m - 1] + ds[m]) / 2
    return str(v.quantize(TENTH, rounding=ROUND_HALF_EVEN))


def stats(xs: list[str]) -> dict:
    return {"min": min(xs, key=Decimal), "median": dmedian(xs), "max": max(xs, key=Decimal)}


def common_inputs(done: dict, names: list[str]):
    """done[form] = the set of input names the form completed at one N. The shown forms are those
    with any completed input. Returns (basis, inputs): ("common", the inputs every shown form
    completed), or, when none is common to all, ("revertsAsZero", every input)."""
    shown = [f for f, s in done.items() if s]
    if not shown:
        return "none", []
    common = [i for i in names if all(i in done[f] for f in shown)]
    if common:
        return "common", common
    return "revertsAsZero", list(names)


def summarise(names: list[str], by_name: dict, forms: list[str], ns: list[int]):
    """summary[form][N] and basis[N] for one scenario (methodology.summary)."""
    summary = {f: {} for f in forms}
    basis = {}
    for n in ns:
        k = str(n)
        done = {}
        for f in forms:
            done[f] = set()
            for i in names:
                c = by_name[i]["cells"].get(f, {}).get(k)
                if c is not None and not c.get("reverted"):
                    done[f].add(i)
        b, members = common_inputs(done, names)
        basis[k] = {"basis": b, "inputs": members}
        for form in forms:
            cs = [c for c in (by_name[i]["cells"].get(form, {}).get(k) for i in names) if c is not None]
            row = {"inputs": len(names), "completed": len(done[form]),
                   "reverts": sum(1 for c in cs if c.get("reverted") and c["reason"] != PARAM_OUT_OF_RANGE),
                   "unrepresentable": sum(1 for c in cs if c.get("reverted") and c["reason"] == PARAM_OUT_OF_RANGE),
                   "count": 0}
            if done[form]:
                agg = []
                for i in members:
                    c = by_name[i]["cells"].get(form, {}).get(k)
                    agg.append(None if c is None or c.get("reverted") else c)
                row["count"] = len(agg)
                row["exact"] = sum(1 for c in agg if c is not None and c["exact"])
                for key, field in (("digits", "digitsCapped"), ("digitsFormat", "digitsFormatCapped"), ("interest", "interestCapped")):
                    vals = ["0.0" if c is None else c.get(field) for c in agg]
                    if all(v is not None for v in vals):
                        row[key] = stats(vals)
            summary[form][k] = row
    return summary, basis


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(cells: dict) -> dict:
    spec = json.loads(SPEC.read_text())
    forms = [f["id"] for f in spec["forms"]]
    ns = spec["ladder"]
    out_scn = []
    for scn in spec["scenarios"]:
        sid = scn["id"]
        if sid not in cells:
            continue
        inputs_out = []
        for inp in scn["inputs"]:
            if inp["name"] not in cells[sid]:
                continue
            p = resolve(inp["params"], scn.get("derived", {}))
            t_exact = truths(sid, p, ns)
            t_format = {sc: truths(sid, floored_params(p, SCALE_INT[sc]), ns) for sc in SCALE_INT}
            principal = p["principal"] if sid in INTEREST else None
            wei = WEI.get(sid)
            cells_out = {}
            for form in forms:
                sc = SCALE_OF_FORM[form]
                col = {}
                for n in ns:
                    c = cells[sid][inp["name"]].get(form, {}).get(n)
                    if c is None:
                        continue
                    if not c["ok"]:
                        col[str(n)] = {"reverted": True, "reason": c["reason"], "reasonName": REASONS.get(c["reason"], "unknown selector"), "gas": None}
                        continue
                    m = metrics(c["raw"], SCALE_INT[sc], t_exact[n], t_format[sc][n])
                    m.update(ladder_fields(c["raw"], sc, t_exact[n], t_format[sc][n], principal, wei))
                    m["raw"] = str(c["raw"])
                    m["gas"] = c["gas"]
                    m["gasPerStep"] = c["gas"] // n
                    col[str(n)] = m
                cells_out[form] = col
            row = {
                "name": inp["name"], "reference": bool(inp.get("reference")), "why": inp.get("why", ""),
                "params": inp["params"],
                "resolved": {k: nstr(v, SIG) for k, v in p.items()},
                "truth": {str(n): nstr(t_exact[n], SIG) for n in ns},
                "truthFormat": {SCALE_NAME[sc]: {str(n): nstr(t_format[sc][n], SIG) for n in ns} for sc in SCALE_INT},
                "cells": cells_out,
            }
            if wei is not None:
                row["truthWei"] = {str(n): nstr(t_exact[n] * wei, 6) for n in ns}
            inputs_out.append(row)
        summary, basis = summarise([i["name"] for i in inputs_out], {i["name"]: i for i in inputs_out}, forms, ns)
        out_scn.append({
            "id": sid, "index": scn["index"], "demo": scn["demo"], "title": scn["title"], "step": scn["step"],
            "result": scn["result"], "why": scn["why"], "order": scn["order"], "derived": scn.get("derived", {}),
            "ops": scn["ops"], "inputs": inputs_out, "summary": summary, "summaryBasis": basis,
        })
    return {
        "generated": datetime.date.today().isoformat(),
        "description": "Terminal precision: each scenario is N identical steps run through each library in its native representation for several inputs, against the same loop in exact arithmetic (mpmath, 300 digits), twice: from the exact parameters (digits) and from the parameters as the library received them (digitsFormat). See methodology.",
        "versions": versions(),
        "ladder": ns,
        "ladderLog10": {str(n): nstr(log(mpf(n), 10), 6) for n in ns},
        "forms": spec["forms"],
        "digitsCap": DIGITS_CAP,
        "axisMax": AXIS_MAX,
        "methodology": METHODOLOGY,
        "scenarios": out_scn,
    }


def runners_ahead():
    """The adapters whose compiled init code (out/) differs from the deployed record's, or None when
    all match (or the build or the record is missing): the dataset is then ahead of the live runner."""
    try:
        from Crypto.Hash import keccak
        rec = json.loads(RECORD.read_text())
        changed = []
        for name, c in rec["contracts"].items():
            if name in ("LadderRunner", "EdgeRunner"):
                continue
            art = json.loads((ROOT / "out" / f"{name}.sol" / f"{name}.json").read_text())
            h = "0x" + keccak.new(digest_bits=256, data=bytes.fromhex(art["bytecode"]["object"][2:])).hexdigest()
            if h != c["initCodeHash"]:
                changed.append(name)
    except (OSError, KeyError, ImportError, ValueError):
        return None
    if not changed:
        return None
    salt = rec["saltAscii"]
    head, _, num = salt.rpartition(" v")
    nxt = f"{head} v{int(num) + 1}" if num.isdigit() else "a new salt"
    return {"deployed": salt, "next": nxt, "changed": changed}


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def short(s: str) -> str:
    return nstr(mpf(s), 16)


def fmt_summary(row: dict, key: str) -> str:
    if key not in row:
        return "—" + (f" ({row['reverts']} revert)" if row["reverts"] else "")
    d = row[key]
    s = "exact" if row.get("exact") == row["count"] and key != "interest" else f"{d['median']} ({d['min']}–{d['max']})"
    if row["completed"] < row["inputs"]:
        s += f", {row['completed']}/{row['inputs']}"
    return s


def fmt_cell(c: dict, key: str, exact: bool) -> str:
    return "exact" if exact else c[key]


def render_md(doc: dict) -> str:
    # FP19 and FP127 first, then the rest in form-id order
    forms = sorted((f["id"] for f in doc["forms"]), key=lambda f: (f != "fp19", f not in ("fp127", "fp127lib")))
    L = ["# Terminal precision ladder", "",
         f"Generated {doc['generated']} by `make ladder`. Versions: " + ", ".join(f"{k} {v}" for k, v in doc["versions"].items()) + ".", "",
         "Each scenario is run for several inputs; the first table is the reference input in full (`digits / digitsFormat / gas per step`, where digits is against the exact truth and digitsFormat against the truth from the parameters as the library received them, both to one decimal and capped at what the format holds at that magnitude), the next two summarise all inputs (`median (min–max)` of the capped digits over the inputs every library completed at that N; `k/n` where a library completed k of n inputs). Full values, both truths, signed errors and raw words are in ladder.json; the method is in the Methodology section at the end.", ""]
    if doc.get("runnersAhead"):
        ra = doc["runnersAhead"]
        L += [f"**This dataset is ahead of the deployed runners.** {', '.join(ra['changed'])} changed after \"{ra['deployed']}\" was deployed, so the live LadderRunner does not yet return these cells; it will after the \"{ra['next']}\" redeploy.", ""]
    for s in doc["scenarios"]:
        L += [f"## {s['id']}: {s['title']}", "", f"Step: `{s['step']}`. Result: {s['result']}.", "", s["why"], ""]
        L += ["Inputs: " + "; ".join(f"**{i['name']}** " + ", ".join(f"{k} = {v}" for k, v in i["params"].items()) + (f" ({i['why']})" if i["why"] else "") for i in s["inputs"]), ""]
        ref = next((i for i in s["inputs"] if i["reference"]), s["inputs"][0])
        L += [f"### Reference input: {ref['name']}", "",
              "| N | truth | " + " | ".join(forms) + " |", "|---:|---|" + "---:|" * len(forms)]
        for n, t in ref["truth"].items():
            cells = []
            for f in forms:
                c = ref["cells"].get(f, {}).get(n)
                if c is None:
                    cells.append("—")
                elif c.get("reverted"):
                    cells.append(f"reverts `{c['reason']}`")
                else:
                    cells.append(fmt_cell(c, "digitsCapped", c["exact"]) + " / " + fmt_cell(c, "digitsFormatCapped", "digitsFormat1" not in c) + f" / {c['gasPerStep']:,}")
            L.append(f"| {n} | `{short(t)}` | " + " | ".join(cells) + " |")
        groups = [("digits", "digits"), ("digitsFormat", "digitsFormat (arithmetic alone)")]
        if any("interest" in s["summary"][f][str(n)] for f in forms for n in doc["ladder"]):
            groups.append(("interest", "digits of the interest, b − principal"))
        for key, title in groups:
            L += ["", f"### All inputs ({len(s['inputs'])}): {title}, median (min–max)", "",
                  "| N | inputs | " + " | ".join(forms) + " |", "|---:|---:|" + "---:|" * len(forms)]
            for n in doc["ladder"]:
                b = s["summaryBasis"][str(n)]
                tag = f"{len(b['inputs'])}" + (" (reverts as 0)" if b["basis"] == "revertsAsZero" else "")
                L.append(f"| {n} | {tag} | " + " | ".join(fmt_summary(s["summary"][f][str(n)], key) for f in forms) + " |")
        L.append("")
    L += ["## Methodology", ""]
    for k, v in doc["methodology"].items():
        L += [f"**{k}.** {v}", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Check
# ---------------------------------------------------------------------------

def strip_volatile(doc: dict) -> dict:
    d = json.loads(json.dumps(doc))
    for s in d.get("scenarios", []):
        s.pop("liveMaxN", None)
    return {k: d.get(k) for k in ("ladder", "forms", "digitsCap", "axisMax", "scenarios")}


def first_difference(a, b, path="") -> str:
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                return f"{path}/{k}: only in {'committed' if k in a else 'regenerated'}"
            r = first_difference(a[k], b[k], f"{path}/{k}")
            if r:
                return r
        return ""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            r = first_difference(x, y, f"{path}[{i}]")
            if r:
                return r
        return ""
    if path.endswith("/gas") or path.endswith("/gasPerStep"):
        if a is None or b is None:
            return "" if a == b else f"{path}: committed {a!r} != regenerated {b!r}"
        if abs(a - b) <= max(3, 0.02 * max(a, b)):
            return ""
    if a != b:
        return f"{path}: committed {a!r} != regenerated {b!r}"
    return ""


def invariants(doc: dict) -> list[str]:
    """Properties the dataset must have; each guards a bug the ladder once had. Run by `make ladder`
    and `make ladder-check`."""
    bad = []
    scn = {s["id"]: s for s in doc["scenarios"]}
    D = Decimal
    for s in doc["scenarios"]:
        for i in s["inputs"]:
            for f, col in i["cells"].items():
                for n, c in col.items():
                    if c.get("reverted"):
                        continue
                    # precision cap: no plotted or aggregated value above what the format holds
                    for k in ("digitsCapped", "digitsFormatCapped"):
                        if k == "digitsCapped" and D(c[k]) > D(c["prec"]):
                            bad.append(f"{s['id']}/{i['name']}/{f}/{n}: {k} {c[k]} above prec {c['prec']}")
                    # the one-decimal digits floor to the integer ones
                    if "digits1" in c and int(D(c["digits1"])) != min(c["digits"], DIGITS_CAP):
                        bad.append(f"{s['id']}/{i['name']}/{f}/{n}: digits1 {c['digits1']} vs digits {c['digits']}")
                    if c["exact"] != ("digits1" not in c):
                        bad.append(f"{s['id']}/{i['name']}/{f}/{n}: exact flag")
        for f, rows in s["summary"].items():
            for n, row in rows.items():
                for key in ("digits", "digitsFormat", "interest"):
                    if key in row and D(row[key]["max"]) > D("71.4"):
                        bad.append(f"{s['id']}/{f}/{n}: summary {key} max {row[key]['max']} above every format's precision")
                # fair medians: every form aggregates the same inputs
                b = s["summaryBasis"][n]
                if row["completed"] and row["count"] != len(b["inputs"]):
                    bad.append(f"{s['id']}/{f}/{n}: aggregated {row['count']} inputs, basis has {len(b['inputs'])}")
                if b["basis"] == "common":
                    for name in b["inputs"]:
                        c = next(x for x in s["inputs"] if x["name"] == name)["cells"].get(f, {}).get(n)
                        if row["completed"] and (c is None or c.get("reverted")):
                            bad.append(f"{s['id']}/{f}/{n}: common input {name} did not complete")
    # FP19 per-second accrual runs on compound: correctly rounded, so ~71 digits at every N
    for i in scn["accrual-per-second"]["inputs"]:
        for n, c in i["cells"]["fp19"].items():
            if c.get("reverted") or D(c["digitsCapped"]) < 69:
                bad.append(f"accrual-per-second/{i['name']}/fp19/{n}: {c.get('digitsCapped', 'reverted')} digits, compound gives about 71")
    # amortise never runs past payoff: every balance positive
    for i in scn["amortise"]["inputs"]:
        for n, t in i["truth"].items():
            if mpf(t) <= 0:
                bad.append(f"amortise/{i['name']}: truth at N = {n} is {t}, past payoff")
    # decay's eps are not on the WAD grid (a power of ten is, and flatters WAD)
    for i in scn["decay"]["inputs"]:
        e = mpf(i["resolved"]["eps"]) * 10 ** 18
        if e == mfloor_(e):
            bad.append(f"decay/{i['name']}: eps {i['resolved']['eps']} is on the WAD grid")
    return bad


# ---------------------------------------------------------------------------
# Self-test of the metric definitions
# ---------------------------------------------------------------------------

def selftest() -> int:
    from Crypto.Hash import keccak
    cases = [
        ("10002.7397260273972602739726027397260273831", "10002.7397260273972602739726027397260273973", 39),
        ("-0.00123456", "-0.00123999", 3),
        ("0.99999999", "1.00000001", 0),
        ("1.5", "1.5", 2),
        ("154769.3406914411", "154769.3406914411", 16),
        ("123", "1230", 0),
        ("0.5", "-0.5", 0),
    ]
    bad = 0
    for v, t, want in cases:
        got = agree_count(v, t)
        if got != want:
            bad += 1
            print(f"agree({v}, {t}) = {got}, want {want}")
    d = digits_of(mpf("10002.7397260273972602739726027397260273831"), mpf("10002.7397260273972602739726027397260273973"))
    if d != 38:
        bad += 1
        print(f"digits = {d}, want 38")
    if digits_of(mpf("1.5"), mpf("1.5")) != DIGITS_CAP or digits_of(mpf(0), mpf(0)) != DIGITS_CAP or digits_of(mpf(1), mpf(0)) != 0:
        bad += 1
        print("digits edge cases")
    m = metrics(3 * 2 ** 127 - 8, 2 ** 128, mpf("1.5"), mpf("1.5"))
    # 1.5 - 8 ULP prints as 1.4999…: the string prefix agrees on one digit while the value is good to 37
    if m["errUlps"] != "-8.0" or m["agree"] != 1 or m["digits"] != 37:
        bad += 1
        print("metrics on the round-trip cell:", m)
    # every named selector is the keccak of its signature (0xedcd4dd4 is SMulWadFailed, not ExpOverflow)
    for sel, sig in REASON_SIGS.items():
        h = "0x" + keccak.new(digest_bits=256, data=sig.encode()).hexdigest()[:8]
        if h != sel or sig.split("(")[0] not in REASONS[sel]:
            bad += 1
            print(f"selector {sel}: {sig} hashes to {h}; REASONS says {REASONS[sel]!r}")
    # the format's precision: 71.3 (FP19), 34.0 (binary128), 38.5 (FP127 at 1), 42.5 (FP127 at 10^4), 22.0 (WAD at 10^4)
    want = {("fp19", 1): "71.3", ("quad", 10 ** 30): "34.0", ("fp127", 1): "38.5", ("fp127", 10 ** 4): "42.5", ("wad", 10 ** 4): "22.0", ("ray", 1): "27.0"}
    for (sc, mag), w in want.items():
        if tenths(precision(sc, mpf(mag))) != w:
            bad += 1
            print(f"precision({sc}, {mag}) = {tenths(precision(sc, mpf(mag)))}, want {w}")
    # exact is prec, a lucky cell is capped at prec, a decimal is floored to one place
    f = ladder_fields(3 * 2 ** 127, "fp127", mpf("1.5"), mpf("1.5"))
    if f["digitsCapped"] != "38.7" or "digits1" in f:
        bad += 1
        print("exact cell:", f)
    f = ladder_fields(10 ** 22, "wad", mpf(10 ** 4) + mpf(10) ** -30, mpf(10 ** 4))
    if f["digits1"] != "34.0" or f["digitsCapped"] != "22.0":
        bad += 1
        print("lucky WAD cell:", f)
    # interest digits: 1e4 + 1 against 1e4 + 1 + 1e-10 has 14 balance digits but 10 interest digits
    f = ladder_fields(int((mpf(10 ** 4) + 1) * 2 ** 128), "fp127", mpf(10 ** 4) + 1 + mpf(10) ** -10, mpf(10 ** 4) + 1, principal=mpf(10 ** 4))
    if f["digits1"][:2] != "14" or f["interestDigits1"] != "10.0":
        bad += 1
        print("interest digits:", f)
    if dmedian(["1.0", "2.0", "3.0"]) != "2.0" or dmedian(["1.0", "2.0", "3.0", "4.0"]) != "2.5" or dmedian(["32.6", "32.9"]) != "32.8":
        bad += 1
        print("median")
    # fair medians: deep-tail at N = 10,000, Balancer completing 1 of 6 inputs and FP127 all 6, is
    # compared on that one input; with nothing in common, reverts count as 0
    names = ["a", "b", "c", "d", "e", "f"]
    if common_inputs({"fp127": set(names), "balancer": {"b"}, "aave": set()}, names) != ("common", ["b"]):
        bad += 1
        print("common inputs")
    if common_inputs({"fp127": {"a"}, "balancer": {"b"}}, names) != ("revertsAsZero", names):
        bad += 1
        print("reverts as zero")
    print("selftest ok" if not bad else f"selftest: {bad} failure(s)")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    doc = build(parse_lines(sys.stdin))
    bad = invariants(doc)
    if bad:
        print(f"ladder invariants: {len(bad)} failure(s)")
        for b in bad[:20]:
            print("  " + b)
        return 1
    if "--check" in argv:
        if not OUT_JSON.exists():
            print("ladder.json missing")
            return 1
        committed = json.loads(OUT_JSON.read_text())
        diff = first_difference(strip_volatile(committed), strip_volatile(doc))
        if not diff:
            print(f"ladder ok: {len(doc['scenarios'])} scenarios, {sum(len(s['inputs']) for s in doc['scenarios'])} inputs")
            return 0
        print("ladder.json is stale; run `make ladder`")
        print("first difference: " + diff)
        return 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    if OUT_JSON.exists():  # keep the live-cap measurements until livecap.py rewrites them
        old = json.loads(OUT_JSON.read_text())
        for k in ("liveRunner", "liveSelector", "liveNote"):
            if k in old:
                doc[k] = old[k]
        old_scn = {s["id"]: s for s in old.get("scenarios", [])} if isinstance(old.get("scenarios"), list) else {}
        for s in doc["scenarios"]:
            if "liveMaxN" in old_scn.get(s["id"], {}):
                s["liveMaxN"] = old_scn[s["id"]]["liveMaxN"]
    ahead = runners_ahead()
    if ahead:  # the stamp says so until livecap.py checks a runner that matches (it drops the key)
        doc["runnersAhead"] = ahead
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")
    OUT_MD.write_text(render_md(doc))
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}: {len(doc['scenarios'])} scenarios, {sum(len(s['inputs']) for s in doc['scenarios'])} inputs"
          + (f"; ahead of the deployed runners ({', '.join(ahead['changed'])} changed)" if ahead else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

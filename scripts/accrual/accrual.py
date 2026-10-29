#!/usr/bin/env python3
"""Deployed-accrual study: how many digits the interest maths deployed on
Ethereum mainnet by Aave v3 and Morpho Blue gets right, against a 200-digit
truth of the formula each protocol says it approximates.

    uv run scripts/accrual/accrual.py            # cases -> forge harness -> score -> docs/benchmarks/accrual-deployed.{json,md}
    uv run scripts/accrual/accrual.py --score    # re-score the last harness log only

Inputs: scripts/accrual/survey.json (a pinned-block snapshot of every Aave v3
Core reserve and every Morpho Blue market with >= $10k borrowed, written by
survey.py) and the stylised scenarios below, each anchored to a parameter set
that is live in that snapshot. Every case is run by test/accrual/DeployedAccrual.t.sol
through the deployed code (the pinned submodules whose runtime bytecode
verify_deployed.py proves equal to mainnet) and through BL127 and BL19
computing the stated ideal; this script computes the truth with mpmath at 200
digits and splits each deployed error into the series truncation (the
approximation) and the integer grids (the rounding).
"""
from __future__ import annotations

import json
import re
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from mpmath import mp, mpf, exp, expm1, log, ln, nstr

mp.dps = 200

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "accrual"
SURVEY = HERE / "survey.json"
CASES = HERE / "cases.json"
LOG = ROOT / "out" / "accrual" / "harness.log"
OUT_JSON = ROOT / "docs" / "benchmarks" / "accrual-deployed.json"
OUT_MD = ROOT / "docs" / "benchmarks" / "accrual-deployed.md"
VERIFY = HERE / "verify-report.json"

SPY = 365 * 86400
RAY = 10 ** 27
WAD = 10 ** 18
HOUR, DAY = 3600, 86400
# Morpho AdaptiveCurveIrm constants as stated (ConstantsLib comments), and as deployed (floored WAD per second)
SPEED = mpf(50) / SPY
MAX_RAT = mpf(2) / SPY
MIN_RAT = mpf("0.001") / SPY
MAX_RAT_WEI = 2 * WAD // SPY
MIN_RAT_WEI = WAD // 1000 // SPY
INITIAL_RAT_WEI = 4 * WAD // 100 // SPY
DIGITS_CAP = 77

PINS = {
    "aave": {"repo": "aave-dao/aave-v3-origin", "tag": "v3.7.0", "commit": "cff15de6d1271b0c800fc001f4aea4c263e8a597",
             "pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
             "poolImplementation": "0x728a138a4823392c2efa55e028d434f526fe03cf", "poolRevision": 11},
    "morpho": {"repo": "morpho-org/morpho-blue", "tag": "v1.0.0", "commit": "55d2d99304fb3fb930c688462ae2ccabb1d533ad",
               "address": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"},
    "irm": {"repo": "morpho-org/morpho-blue-irm", "tag": "v1.0.0", "commit": "a7d9cce3451b4a106bfd40933ac57a785b5228f3",
            "address": "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC"},
}

CLAIMS = [
    {"who": "Aave v3.7.0", "where": "MathUtils.calculateCompoundedInterest, doc comment",
     "text": "To avoid expensive exponentiation, the calculation is performed using a binomial approximation: "
             "(1+x)^n = 1+n*x+[n/2*(n-1)]*x^2+[n/6*(n-1)*(n-2)*x^3... The approximation slightly underpays liquidity "
             "providers and undercharges borrowers, with the advantage of great gas cost reductions."},
    {"who": "Aave v3.7.0", "where": "MathUtils.calculateCompoundedInterest, body",
     "text": "calculations compound interest using the ideal formula - e^(rate per year * number of years) ... "
             "the contract uses a polynomial approximation of the ideal formula. "
             "Code: x = rate*exp/SECONDS_PER_YEAR; return RAY + x + x.rayMul(x/2 + x.rayMul(x/6)) "
             "(the first three terms of e^x - 1, not the binomial with (n-1), (n-2) the doc comment describes)."},
    {"who": "Aave v3.7.0", "where": "MathUtils.calculateLinearInterest / ReserveLogic._updateIndexes",
     "text": "Supply side: the liquidity index grows by simple interest 1 + rate*dt/SECONDS_PER_YEAR between updates "
             "(no approximation is claimed). Aave's own interface library computes the displayed supply APY as "
             "per-second compounding of that rate: aave/aave-utilities@2d0db501 math-utils "
             "formatters/reserve/index.ts, supplyAPY = calculateCompoundedRate({rate: liquidityRate, duration: "
             "SECONDS_PER_YEAR}) = rayPow(1 + rate/SECONDS_PER_YEAR, SECONDS_PER_YEAR) - 1."},
    {"who": "Morpho Blue v1.0.0", "where": "MathLib.wTaylorCompounded",
     "text": "Returns the sum of the first three non-zero terms of a Taylor expansion of e^(nx) - 1, to approximate a "
             "continuous compound interest rate."},
    {"who": "AdaptiveCurveIrm v1.0.0", "where": "_borrowRate",
     "text": "avg = 1/T * integral_0^T curve(startRateAtTarget*exp(speed*x), err) dx. The integral is approximated with "
             "the trapezoidal rule ... With N = 2. Also: 'The speed is assumed constant between two updates, but it is in "
             "fact not constant because of interest. So the rate is always underestimated.'"},
    {"who": "AdaptiveCurveIrm v1.0.0", "where": "ExpLib.wExp",
     "text": "Returns an approximation of exp: x = q ln2 + r, |r| <= ln2/2, e^r by a 2nd-order Taylor polynomial."},
]


# ---------------------------------------------------------------------------- cases

def scaled_for(principal_units: int, index: int) -> int:
    """Scaled balance that a deposit of `principal_units` mints at `index` (rayDiv half up)."""
    return (principal_units * RAY + index // 2) // index


def build_cases(survey: dict) -> dict:
    ts = survey["timestamp"]
    aave_by = {r["symbol"]: r for r in survey["aave"]}
    A = {k: [] for k in ["id", "kind", "rate", "t", "index0", "scaled", "last", "expect"]}
    M = {k: [] for k in ["id", "supply", "borrow", "r0", "t", "last", "expect"]}
    F = {k: [] for k in ["id", "rate", "t", "borrow"]}
    meta = {}

    def aave(cid, kind, rate, t, index0, scaled, last, expect, m):
        for k, v in zip(A, [cid, kind, rate, t, index0, scaled, last, expect]):
            A[k].append(str(v))
        meta[cid] = m

    def morpho(cid, supply, borrow, r0, t, last, expect, m):
        for k, v in zip(M, [cid, supply, borrow, r0, t, last, expect]):
            M[k].append(str(v))
        meta[cid] = m

    # Stylised Aave: a reserve's live parameter set at 100% utilisation (base + slope1 + slope2), from the
    # reserve's live index, 1,000,000 tokens borrowed (or supplied), left untouched for t.
    last = 1_790_000_000
    for sym, ts_list in [("USDC", [DAY, 7 * DAY]), ("WETH", [7 * DAY]), ("LINK", [HOUR, DAY, 7 * DAY, 30 * DAY])]:
        r = aave_by[sym]
        bps = r["baseVariableBorrowRateBps"] + r["variableRateSlope1Bps"] + r["variableRateSlope2Bps"]
        rate = bps * 10 ** 23
        dec = r["decimals"]
        for t in ts_list:
            idx = int(r["variableBorrowIndex"])
            aave(f"aave-{sym.lower()}-u100-borrow-{label(t)}", 0, rate, t, idx, scaled_for(10 ** 6 * 10 ** dec, idx), last, 0,
                 {"protocol": "aave", "kind": "borrow", "group": "stylised", "symbol": sym, "decimals": dec,
                  "principal": 10 ** 6, "rateAnnual": bps / 10000, "t": t,
                  "why": f"{sym}'s live strategy at 100% utilisation: base {r['baseVariableBorrowRateBps']} + slope1 "
                         f"{r['variableRateSlope1Bps']} + slope2 {r['variableRateSlope2Bps']} bps; untouched {label(t)}"})
            if sym in ("USDC", "LINK"):
                # supply side at 100% utilisation: liquidity rate = borrow rate * U * (1 - reserve factor)
                lrate = rate * (10000 - r["reserveFactorBps"]) // 10000
                li = int(r["liquidityIndex"])
                aave(f"aave-{sym.lower()}-u100-supply-{label(t)}", 1, lrate, t, li, scaled_for(10 ** 6 * 10 ** dec, li), last, 0,
                     {"protocol": "aave", "kind": "supply", "group": "stylised", "symbol": sym, "decimals": dec,
                      "principal": 10 ** 6, "rateAnnual": lrate / RAY, "t": t,
                      "why": f"{sym} suppliers at 100% utilisation (reserve factor {r['reserveFactorBps']} bps); untouched {label(t)}"})
    # the ladder's reference: 5% for a year
    idx = int(aave_by["USDC"]["variableBorrowIndex"])
    aave("aave-ref-5pct-borrow-365d", 0, 5 * 10 ** 25, 365 * DAY, idx, scaled_for(10 ** 6 * 10 ** 6, idx), last, 0,
         {"protocol": "aave", "kind": "borrow", "group": "stylised", "symbol": "USDC", "decimals": 6, "principal": 10 ** 6,
          "rateAnnual": 0.05, "t": 365 * DAY, "why": "the ladder's reference rate (5%) over a year with no interaction"})

    # Live Aave: every reserve with variable debt and a pending accrual at the survey block.
    for r in survey["aave"]:
        t = ts - r["lastUpdateTimestamp"]
        if t <= 0:
            continue
        rate, dscaled = int(r["currentVariableBorrowRate"]), int(r["variableDebtScaled"])
        if rate > 0 and dscaled > 0:
            aave(f"live-aave-{r['symbol']}-borrow", 0, rate, t, int(r["variableBorrowIndex"]), dscaled,
                 r["lastUpdateTimestamp"], int(r["normalizedVariableDebt"]),
                 {"protocol": "aave", "kind": "borrow", "group": "live", "symbol": r["symbol"], "decimals": r["decimals"],
                  "rateAnnual": rate / RAY, "t": t, "utilization": r["utilization"], "frozen": r["frozen"],
                  "why": "pending accrual of the whole reserve's variable debt at the survey block"})
        lrate, sscaled = int(r["currentLiquidityRate"]), int(r["aTokenScaledSupply"])
        if lrate > 0 and sscaled > 0:
            aave(f"live-aave-{r['symbol']}-supply", 1, lrate, t, int(r["liquidityIndex"]), sscaled,
                 r["lastUpdateTimestamp"], int(r["normalizedIncome"]),
                 {"protocol": "aave", "kind": "supply", "group": "live", "symbol": r["symbol"], "decimals": r["decimals"],
                  "rateAnnual": lrate / RAY, "t": t, "utilization": r["utilization"], "frozen": r["frozen"],
                  "why": "pending accrual of the whole reserve's supply at the survey block"})

    # Stylised Morpho: 10,000,000 USDC borrowed, utilisation u, rate at target r0, untouched for t.
    B = 10 ** 7 * 10 ** 6
    rat = lambda apr: int(mpf(apr) * WAD / SPY)  # noqa: E731
    sty = [
        ("at-target-4pct", "0.9", INITIAL_RAT_WEI, [DAY, 7 * DAY], "at the 90% target the rate is constant (err = 0): only the series and the grid"),
        ("u95-10pct", "0.95", rat("0.10"), [DAY, 7 * DAY], "utilisation 95%: the rate at target adapts upward at 25/year"),
        ("u100-10pct", "1", rat("0.10"), [DAY, 7 * DAY], "fully utilised: the borrow rate is 4x the rate at target, which adapts at 50/year"),
        ("u100-4pct", "1", INITIAL_RAT_WEI, [7 * DAY, 30 * DAY], "fully utilised from the initial 4%: the rate at target reaches its 200% cap after 28.6 days"),
        ("u100-max", "1", MAX_RAT_WEI, [DAY, 7 * DAY, 30 * DAY], "fully utilised at the cap: 800%/year, constant"),
        ("u80-10pct", "0.8", rat("0.10"), [7 * DAY], "utilisation 80%: the rate at target decays"),
    ]
    for name, u, r0, tl, why in sty:
        # at the target the supply is chosen so that 10B = 9S exactly (err = 0, the rate is constant)
        supply = B * 10 // 9 // 10 * 10 if u == "0.9" else (int(mpf(B) / mpf(u)) if u != "1" else B)
        borrow = 9 * supply // 10 if u == "0.9" else B
        for t in tl:
            morpho(f"morpho-{name}-{label(t)}", supply, borrow, r0, t, last, 0,
                   {"protocol": "morpho", "kind": "adaptive", "group": "stylised", "symbol": "USDC", "decimals": 6,
                    "principal": borrow // 10 ** 6, "utilization": float(mpf(borrow) / supply), "rateAtTargetAnnual": float(mpf(r0) * SPY / WAD),
                    "t": t, "why": why})
    # Live Morpho: every AdaptiveCurveIrm market with borrows and a pending accrual at the survey block.
    for r in survey["morpho"]:
        t = ts - r["lastUpdate"]
        if r["rateAtTarget"] in (None, "0") or int(r["totalBorrowAssets"]) == 0 or t <= 0:
            continue
        morpho(f"live-morpho-{r['id'][:10]}-{r['symbol']}", int(r["totalSupplyAssets"]), int(r["totalBorrowAssets"]),
               int(r["rateAtTarget"]), t, r["lastUpdate"], int(r["borrowRateView"]),
               {"protocol": "morpho", "kind": "adaptive", "group": "live", "symbol": r["symbol"], "decimals": r["decimals"],
                "market": r["id"], "utilization": r["utilization"], "rateAtTargetAnnual": int(r["rateAtTarget"]) * SPY / WAD,
                "t": t, "why": "pending accrual of the whole market's borrows at the survey block"})

    # Morpho at a fixed per-second rate (the ladder's model): 5% for a year, as the ladder's reference.
    for cid, apr, t in [("morphofixed-ref-5pct-365d", "0.05", 365 * DAY), ("morphofixed-800pct-7d", "8", 7 * DAY)]:
        rate = int(mpf(apr) * WAD / SPY)
        for k, v in zip(F, [cid, rate, t, 10 ** 4 * WAD]):
            F[k].append(str(v))
        meta[cid] = {"protocol": "morpho", "kind": "fixed", "group": "stylised", "symbol": "18-dec token", "decimals": 18,
                     "principal": 10 ** 4, "rateAnnual": float(apr), "t": t,
                     "why": "constant per-second WAD rate, no IRM (the ladder's LadderMorpho model)"}
    return {"_doc": "generated by scripts/accrual/accrual.py from survey.json; parallel arrays for the forge harness",
            "surveyBlock": survey["block"], "aave": A, "morpho": M, "morphoFixed": F, "meta": meta}


def label(t: int) -> str:
    if t % DAY == 0:
        return f"{t // DAY}d"
    if t % HOUR == 0:
        return f"{t // HOUR}h"
    return f"{t}s"


# ---------------------------------------------------------------------------- harness

def run_harness() -> str:
    art = ROOT / "out" / "accrual" / "AdaptiveCurveIrm.json"
    if not art.exists():
        subprocess.run(["uv", "run", str(HERE / "verify_deployed.py"), "build"], check=True, cwd=ROOT)
    r = subprocess.run(["forge", "test", "--match-path", "test/accrual/DeployedAccrual.t.sol", "-vv"], env={**os.environ, "FOUNDRY_PROFILE": "accrual"},
                       capture_output=True, text=True, cwd=ROOT)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        sys.exit("forge test failed; see " + str(LOG.relative_to(ROOT)) + "\n" + r.stdout[-3000:])
    return r.stdout


def parse(log_text: str) -> dict:
    res: dict = {}
    for line in log_text.splitlines():
        line = line.strip()
        if not line.startswith("ACC|"):
            continue
        _, cid, form, kv = line.split("|", 3)
        res.setdefault(cid, {})[form] = {k: int(v) for k, v in (p.split("=") for p in kv.strip(";").split(";") if p)}
    return res


# ---------------------------------------------------------------------------- scoring

def bl127(raw: int):
    return mpf(raw) / mpf(2) ** 128


def bl19(raw: int):
    w = raw & ((1 << 256) - 1)
    if w == 0:
        return mpf(0)
    s, e, f = w >> 255, (w >> 236) & ((1 << 19) - 1), w & ((1 << 236) - 1)
    v = mpf((1 << 236) + f) * mpf(2) ** (e - 262143 - 236)
    return -v if s else v


def digits(err, ref) -> float:
    if err == 0:
        return float(DIGITS_CAP)
    if ref == 0:
        return 0.0
    d = -log(abs(err) / abs(ref), 10)
    return float(min(DIGITS_CAP, max(mpf(0), d)))


def sci(x) -> str:
    return nstr(x, 4, min_fixed=-3, max_fixed=4) if x != 0 else "0"


def amt(x) -> str:
    return nstr(x, 6, min_fixed=-6, max_fixed=12) if abs(x) > mpf(10) ** -150 else "0"


def taylor3(y):
    return y + y * y / 2 + y ** 3 / 6


def score_aave(cid: str, m: dict, c: dict, r: dict) -> dict:
    s, I0, rate, t = c["scaled"], c["index0"], c["rate"], c["t"]
    unit = mpf(10) ** m["decimals"]
    B0 = mpf(s) * I0 / RAY
    x = mpf(rate) * t / (mpf(RAY) * SPY)
    Gc, Gp = exp(x), (1 + mpf(rate) / (mpf(RAY) * SPY)) ** t
    approx_poly = 1 + (taylor3(x) if m["kind"] == "borrow" else x)
    d = r["deployed"]
    F, idx1, bal1 = mpf(d["factor"]) / RAY, d["index1"], d["bal1"]
    out = {"id": cid, **m, "inputs": {k: str(c[k]) for k in ("rate", "t", "index0", "scaled")},
           "principalTokens": amt(B0 / unit),
           "deployed": {"factor": str(d["factor"]), "index1": str(idx1), "bal0": str(d["bal0"]), "bal1": str(bal1)}}
    truths = {}
    for tname, G in (("continuous", Gc), ("perSecond", Gp)):
        bal_t, int_t = B0 * G, B0 * (G - 1)
        E = bal1 - bal_t
        row = {"truthBalanceTokens": amt(bal_t / unit), "truthInterestTokens": amt(int_t / unit),
               "deployed": {"errTokens": amt(E / unit), "relBalance": sci(E / bal_t), "relInterest": sci(E / int_t),
                            "digitsBalance": round(digits(E, bal_t), 2), "digitsInterest": round(digits(E, int_t), 2),
                            "approximationTokens": amt(B0 * (approx_poly - G) / unit),
                            "roundingTokens": amt((bal1 - B0 * approx_poly) / unit)},
               "gridDigitsInterest": round(digits(mpf("0.5"), int_t / unit * unit), 2) if int_t else None}
        # the grids, for the record: factor on the ray grid, index rayMul, balance to token units
        row["deployed"]["rounding"] = {"factorGridTokens": amt(B0 * (F - approx_poly) / unit),
                                       "indexGridTokens": amt(mpf(s) * (idx1 - F * I0) / RAY / unit),
                                       "tokenGridTokens": amt((bal1 - mpf(s) * idx1 / RAY) / unit)}
        key = "cont" if tname == "continuous" else "ps"
        for form, dec in (("bl127", bl127), ("bl19", bl19)):
            fb, fi = dec(r[form][f"{key}_bal"]), dec(r[form][f"{key}_int"])
            row[form] = {"errTokens": amt((fb - bal_t) / unit), "relBalance": sci((fb - bal_t) / bal_t),
                         "digitsBalance": round(digits(fb - bal_t, bal_t), 2),
                         "digitsInterest": round(digits(fi - int_t, int_t), 2)}
        truths[tname] = row
    out["truth"] = truths
    out["primaryTruth"] = "continuous" if m["kind"] == "borrow" else "perSecond"
    return out


def rat_path(r0, k, tau):
    """Rate at target at time tau, held in [MIN, MAX] as stated."""
    v = r0 * exp(k * tau)
    return min(max(v, MIN_RAT), MAX_RAT)


def score_morpho(cid: str, m: dict, c: dict, r: dict) -> dict:
    S, B, R0w, t = c["supply"], c["borrow"], c["r0"], c["t"]
    unit = mpf(10) ** m["decimals"]
    u = mpf(B) / S
    tgt = mpf("0.9")
    err = (u - tgt) / (1 - tgt) if u > tgt else (u - tgt) / tgt
    coeff = 3 if err >= 0 else mpf("0.75")
    mult = 1 + coeff * err
    R0 = mpf(R0w) / WAD
    k = SPEED * err
    if k == 0:
        integral = R0 * t
    else:
        bound = MAX_RAT if k > 0 else MIN_RAT
        tstar = log(bound / R0) / k
        integral = (bound - R0) / k + bound * (t - tstar) if t > tstar else R0 * expm1(k * t) / k
    G = exp(mult * integral)
    int_t = B * (G - 1)
    bal_t = B + int_t
    d = r["deployed"]
    rate = mpf(d["rate"]) / WAD
    y = rate * t
    E = d["interest"] - int_t
    irm_tok = B * (expm1(y) - (G - 1))
    # trapezoid (N = 2) with exact exponentials and the stated bounds: the quadrature alone
    avg_trap = mult * (R0 + rat_path(R0, k, t) + 2 * rat_path(R0, k, mpf(t) / 2)) / 4
    trap_tok = B * (expm1(avg_trap * t) - (G - 1))
    taylor_tok = B * (taylor3(y) - expm1(y))
    round_tok = d["interest"] - B * taylor3(y)
    end_true = rat_path(R0, k, t)
    out = {"id": cid, **m, "inputs": {k2: str(c[k2]) for k2 in ("supply", "borrow", "r0", "t")},
           "principalTokens": amt(B / unit),
           "avgRateTrueAnnual": sci(mult * integral / t * SPY), "avgRateDeployedAnnual": sci(rate * SPY),
           "avgRateRelErr": sci((rate - mult * integral / t) / (mult * integral / t)) if integral else "0",
           "endRateAtTargetRelErr": sci((mpf(d["endRateAtTarget"]) / WAD - end_true) / end_true),
           "deployed": {"rate": str(d["rate"]), "endRateAtTarget": str(d["endRateAtTarget"]), "taylor": str(d["taylor"]),
                        "interest": str(d["interest"])}}
    row = {"truthBalanceTokens": amt(bal_t / unit), "truthInterestTokens": amt(int_t / unit),
           "deployed": {"errTokens": amt(E / unit), "relBalance": sci(E / bal_t), "relInterest": sci(E / int_t),
                        "digitsBalance": round(digits(E, bal_t), 2), "digitsInterest": round(digits(E, int_t), 2),
                        "irmTokens": amt(irm_tok / unit), "irmTrapezoidTokens": amt(trap_tok / unit),
                        "irmWExpAndRoundingTokens": amt((irm_tok - trap_tok) / unit),
                        "approximationTokens": amt(taylor_tok / unit), "roundingTokens": amt(round_tok / unit)},
           "gridDigitsInterest": round(digits(mpf("0.5"), int_t), 2) if int_t else None}
    for form, dec in (("bl127", bl127), ("bl19", bl19)):
        fb, fi = dec(r[form]["bal"]), dec(r[form]["int"])
        row[form] = {"errTokens": amt((fi - int_t) / unit), "relBalance": sci((fb - bal_t) / bal_t),
                     "digitsBalance": round(digits(fb - bal_t, bal_t), 2), "digitsInterest": round(digits(fi - int_t, int_t), 2)}
    out["truth"] = {"continuous": row}
    out["primaryTruth"] = "continuous"
    return out


def score_fixed(cid: str, m: dict, c: dict, r: dict) -> dict:
    rate, t, B = c["rate"], c["t"], c["borrow"]
    unit = mpf(10) ** m["decimals"]
    y = mpf(rate) * t / WAD
    int_t = B * expm1(y)
    bal_t = B + int_t
    d = r["deployed"]
    E = d["interest"] - int_t
    row = {"truthBalanceTokens": amt(bal_t / unit), "truthInterestTokens": amt(int_t / unit),
           "deployed": {"errTokens": amt(E / unit), "relBalance": sci(E / bal_t), "relInterest": sci(E / int_t),
                        "digitsBalance": round(digits(E, bal_t), 2), "digitsInterest": round(digits(E, int_t), 2),
                        "approximationTokens": amt(B * (taylor3(y) - expm1(y)) / unit),
                        "roundingTokens": amt((d["interest"] - B * taylor3(y)) / unit)}}
    # the rate itself: the annual rate held as floored WAD per second, against the annual truth
    ya = mpf(str(m["rateAnnual"])) * t / SPY
    Ea = d["interest"] - B * expm1(ya)
    row["deployedVsAnnualRate"] = {"rateQuantizationTokens": amt(B * (expm1(y) - expm1(ya)) / unit),
                                   "errTokens": amt(Ea / unit), "digitsInterest": round(digits(Ea, B * expm1(ya)), 2)}
    for form, dec in (("bl127", bl127), ("bl19", bl19)):
        fb, fi = dec(r[form]["bal"]), dec(r[form]["int"])
        row[form] = {"errTokens": amt((fi - int_t) / unit), "relBalance": sci((fb - bal_t) / bal_t),
                     "digitsBalance": round(digits(fb - bal_t, bal_t), 2), "digitsInterest": round(digits(fi - int_t, int_t), 2)}
    return {"id": cid, **m, "inputs": {"rate": str(rate), "t": str(t), "borrow": str(B)}, "principalTokens": amt(B / unit),
            "deployed": {k: str(v) for k, v in d.items()}, "truth": {"continuous": row}, "primaryTruth": "continuous"}


def case_inputs(cases: dict, group: str, i: int) -> dict:
    g = cases[group]
    return {k: (int(v[i]) if k != "id" else v[i]) for k, v in g.items()}


def score(cases: dict, res: dict) -> list[dict]:
    rows = []
    for group, fn in (("aave", score_aave), ("morpho", score_morpho), ("morphoFixed", score_fixed)):
        for i, cid in enumerate(cases[group]["id"]):
            c = case_inputs(cases, group, i)
            rows.append(fn(cid, cases["meta"][cid], c, res[cid]))
    return rows


# ---------------------------------------------------------------------------- report

def human_t(t: int) -> str:
    if t >= DAY:
        return f"{t / DAY:.3g} d"
    if t >= HOUR:
        return f"{t / HOUR:.3g} h"
    return f"{t} s"


def row_line(x: dict) -> str:
    tr = x["truth"][x["primaryTruth"]]
    dep = tr["deployed"]
    rate = x.get("rateAnnual")
    rate_s = f"{rate * 100:.4g}%" if rate is not None else f"r@t {x['rateAtTargetAnnual'] * 100:.4g}%, u {x['utilization'] * 100:.4g}%"
    return (f"| `{x['id']}` | {rate_s} | {human_t(x['t'])} | {x['principalTokens']} {x['symbol']} | "
            f"{tr['truthInterestTokens']} | {dep['errTokens']} | {dep['digitsInterest']} | {dep['digitsBalance']} | "
            f"{tr.get('gridDigitsInterest', '—')} | {tr['bl127']['digitsInterest']} | {tr['bl19']['digitsInterest']} |")


def write_md(data: dict) -> None:
    rows = data["cases"]
    L = []
    L.append("# Deployed accrual: Aave v3 and Morpho Blue against their stated ideals\n")
    L.append(f"Generated {data['generated']} by `make accrual-deployed` (`uv run scripts/accrual/accrual.py`). "
             f"Survey block {data['survey']['block']} ({data['survey']['date']}). Data: `accrual-deployed.json`.\n")
    L.append("## What is measured\n")
    L.append("Each case is one accrual: a balance, a rate, and the seconds since the last update. The deployed integer "
             "maths (the pinned submodules, proven byte-identical to mainnet below) produces the new balance; mpmath at "
             "200 digits produces the formula the protocol says it approximates. **Digits** = −log10(|error| / |true value|), "
             "reported for the accrued interest (the number a lender or borrower is owed) and for the whole balance. "
             "**err** is deployed − truth in token units (negative: the protocol accrues less than its stated formula). "
             "The error is split into the **approximation** (the truncated series, computed in exact arithmetic) and the "
             "**rounding** (ray/wad grids, the rate held as an integer per second, balances in token units). BL127 and BL19 "
             "compute the same stated formula from the same integers with their own exp/ln/pow and are not rounded to "
             "token units; *grid* is the most digits any answer rounded to token units could show.\n")
    L.append("Truths: Aave borrow — e^(rate·years) (the body comment's \"ideal formula\"); the per-second binomial "
             "(1 + rate/SPY)^seconds named in the doc comment is reported alongside in the JSON and differs by less than "
             "rate²·t/(2·SPY²). Aave supply — per-second compounding of the liquidity rate (the APY Aave displays); the "
             "index itself is simple interest by design. Morpho — e^(∫ rate dt) with the AdaptiveCurveIrm's stated ideal "
             "rate path (rate at target r0·e^(50/yr·err·t), held in [0.1%, 200%]/yr, curve ×4 above target), at the "
             "utilisation of the last update (the IRM's own stated assumption).\n")
    L.append("## Summary\n")
    by = {x["id"]: x for x in rows}

    def line(cid, gist):
        x = by[cid]
        tr = x["truth"][x["primaryTruth"]]
        dep = tr["deployed"]
        L.append(f"- **{gist}** (`{cid}`): {x['principalTokens']} {x['symbol']}, idle {human_t(x['t'])}. True interest "
                 f"{tr['truthInterestTokens']}; deployed off by {dep['errTokens']} {x['symbol']} "
                 f"({sci(abs(mpf(dep['relInterest'])))} of the interest, {dep['digitsInterest']} digits; balance "
                 f"{dep['digitsBalance']}). Series {dep['approximationTokens']}, grids {dep['roundingTokens']}"
                 + (f", IRM rate path {dep['irmTokens']} (trapezoid {dep['irmTrapezoidTokens']})" if 'irmTokens' in dep else "")
                 + f". BL127 {tr['bl127']['digitsInterest']} digits, BL19 {tr['bl19']['digitsInterest']}.")

    L.append("Normal operation is accurate. Under realistic rates and idle times the Aave borrow index is within the "
             "token's own decimals or a few millionths of a token per million, and Morpho at its 90% target is the "
             "same. The digits go where the stated ideal and the shipped shortcut diverge:\n")
    line("morpho-u100-10pct-1d", "Morpho, fully utilised market untouched for a day")
    line("morpho-u100-10pct-7d", "Morpho, fully utilised market untouched for a week")
    line("morpho-u100-max-7d", "Morpho at the 800% cap for a week")
    line("aave-link-u100-borrow-7d", "Aave, slope2 300% asset at 100% utilisation for a week")
    line("aave-usdc-u100-supply-1d", "Aave supply index (simple interest) vs the displayed APY, USDC at 100% for a day")
    line("aave-usdc-u100-borrow-1d", "Control: Aave USDC borrow at 100% utilisation for a day")
    L.append("")
    L.append("Signs: Aave and Morpho's series both undercharge (as Aave's comment says); the AdaptiveCurveIrm's two-panel "
             "trapezoid overcharges whenever the rate at target is moving, because e^(kt) is convex, and the stored "
             "rate at target drifts by the wExp error (" + by["morpho-u100-10pct-1d"]["endRateAtTargetRelErr"] +
             " relative after the one-day case).\n")
    L.append("## Provenance\n")
    L.append("| contract | address | source pin | runtime bytecode |")
    L.append("|---|---|---|---|")
    vr = {t["name"]: t for t in data["verify"]["targets"]} if data.get("verify") else {}
    for name, addr, pin in [
        ("Aave v3 Pool implementation (Core, POOL_REVISION 11)", PINS["aave"]["poolImplementation"], "aave-v3-origin v3.7.0 `cff15de6`"),
        ("Aave SupplyLogic", "0x584C7d8c4cb05304FE5Ac7fbc97f20A10Fb07564", "aave-v3-origin v3.7.0"),
        ("Aave BorrowLogic", "0x52Da0ce88202D1542543598D1e1e27F0d344726A", "aave-v3-origin v3.7.0"),
        ("Aave LiquidationLogic", "0x96D5686812e33Ab509ECCDb38C89d15607B2a413", "aave-v3-origin v3.7.0"),
        ("Aave FlashLoanLogic", "0x6D414cd0d5eAf8C43200ac0c325A7E2Ad83B8be6", "aave-v3-origin v3.7.0"),
        ("Aave PoolLogic", "0xD70593841C57cbaA04957cc3EAcE95708e48853b", "aave-v3-origin v3.7.0"),
        ("Morpho Blue", PINS["morpho"]["address"], "morpho-blue v1.0.0 `55d2d993`"),
        ("AdaptiveCurveIrm", PINS["irm"]["address"], "morpho-blue-irm v1.0.0 `a7d9cce3`"),
    ]:
        key = {"Morpho Blue": "MorphoBlue", "AdaptiveCurveIrm": "AdaptiveCurveIrm"}.get(name)
        if key is None:
            key = "AavePoolImpl" if "implementation" in name else "Aave" + name.split()[-1]
        v = vr.get(key)
        st = (f"equal ({v['runtimeBytes']} B; {v['immutableSlotsMasked']} immutable slots"
              f"{', library address' if v['libraryAddressMasked'] else ''} masked; block {data['verify']['block']})") if v and v["runtimeMatches"] else "NOT CHECKED"
        L.append(f"| {name} | `{addr}` | {pin} | {st} |")
    L.append("\nThe Pool proxy is `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`. Aave deployed v3.7 from a private mirror "
             "(`lib/aave-v3-origin-private`); every verified file is byte-identical to the public tag except "
             "LiquidationLogic.sol, which differs in whitespace only, and the recompiled runtime is equal. "
             "`scripts/accrual/verify_deployed.py check` recompiles every target from `lib/` with the verified compiler "
             "and settings and compares to `eth_getCode`.\n")
    lv = data["liveChecks"]
    L.append(f"Live equivalence at the survey block: the harness reproduced `getReserveNormalizedVariableDebt` / "
             f"`getReserveNormalizedIncome` for {lv['aave']} Aave reserve sides and the deployed IRM's `borrowRateView` for "
             f"{lv['morpho']} Morpho markets exactly (assertEq in the harness).\n")
    L.append("## What the protocols claim\n")
    for c in CLAIMS:
        L.append(f"- **{c['who']}**, {c['where']}: {c['text']}")
    L.append("")
    head = ("| case | rate | idle | principal | true interest | err (tokens) | digits (interest) | digits (balance) | "
            "grid | BL127 digits (interest) | BL19 digits (interest) |\n|---|---|---|---|---|---|---|---|---|---|---|")
    L.append("## Stylised cases (live parameter sets, chosen idle times)\n")
    L.append(head)
    for x in rows:
        if x["group"] == "stylised":
            L.append(row_line(x))
    L.append("")
    L.append("### Where the error comes from (stylised, token units)\n")
    L.append("| case | approximation (series) | rounding (grids) | IRM rate path: trapezoid | IRM rate path: wExp + rounding |")
    L.append("|---|---|---|---|---|")
    for x in rows:
        if x["group"] != "stylised":
            continue
        dep = x["truth"][x["primaryTruth"]]["deployed"]
        L.append(f"| `{x['id']}` | {dep['approximationTokens']} | {dep['roundingTokens']} | {dep.get('irmTrapezoidTokens', '—')} | "
                 f"{dep.get('irmWExpAndRoundingTokens', '—')} |")
    L.append("")
    def err_units(x):
        """|err| in units of the token's last decimal."""
        return abs(mpf(x["truth"][x["primaryTruth"]]["deployed"]["errTokens"])) * mpf(10) ** x["decimals"]

    def section(title, sel, note, n=10):
        live = [x for x in rows if x["group"] == "live" and sel(x)]
        if not live:
            return
        L.append(f"### {title} ({len(live)})\n")
        L.append(note + "\n")
        L.append(head)
        for x in sorted(live, key=err_units, reverse=True)[:n]:
            L.append(row_line(x))
        ds = sorted(x["truth"][x["primaryTruth"]]["deployed"]["digitsInterest"] for x in live)
        worse = sum(1 for d in ds if d < 4)
        L.append(f"\nInterest digits across all {len(ds)}: min {ds[0]}, median {ds[len(ds) // 2]}, max {ds[-1]}; "
                 f"{worse} of {len(ds)} have fewer than 4 (a relative error in the interest above 1e-4).\n")

    L.append(f"## Live pending accruals at block {data['survey']['block']}\n")
    L.append("Every reserve or market's accrual as it would execute if touched at the survey block, from its on-chain "
             "state (rates, indexes, rate at target, totals, last update). Sorted by |err| in units of the token's last "
             "decimal; when *digits* is close to *grid* the error is just the token's decimals.\n")
    section("Aave v3 Core, variable debt", lambda x: x["protocol"] == "aave" and x["kind"] == "borrow",
            "Truth: e^(rate·years).")
    section("Aave v3 Core, supply (liquidity index)", lambda x: x["protocol"] == "aave" and x["kind"] == "supply",
            "Truth: per-second compounding of the liquidity rate (the APY Aave displays). The index is simple "
            "interest between updates by design; this is the size of that gap, not a bug.")
    section("Morpho Blue, markets idle under 7 days", lambda x: x["protocol"] == "morpho" and x["t"] < 7 * DAY,
            "Truth: e^(integral of the rate) on the IRM's stated rate path.")
    section("Morpho Blue, markets idle 7 days or more", lambda x: x["protocol"] == "morpho" and x["t"] >= 7 * DAY,
            "Dormant markets: most sit at 100% utilisation (often the borrow side is bad debt that nobody repays and "
            "the supply side cannot withdraw), so the figures are what the contract would book at the next touch, "
            "not money anyone is likely to pay.")
    L.append("## The ladder's models against the deployed code\n")
    L.append(data["ladderCheck"] + "\n")
    L.append("## Reproduce\n")
    L.append("```\nmake accrual-deployed        # offline: cases from the committed survey, forge harness, mpmath scoring\n"
             "make accrual-verify          # network: recompile the pinned sources, compare runtime bytecode to mainnet\n"
             "make accrual-survey          # network: refresh survey.json at the current block (changes the live cases)\n```\n")
    OUT_MD.write_text("\n".join(L) + "\n")


def main() -> None:
    survey = json.loads(SURVEY.read_text())
    cases = build_cases(survey)
    CASES.write_text(json.dumps(cases, indent=1) + "\n")
    text = LOG.read_text() if "--score" in sys.argv else run_harness()
    res = parse(text)
    missing = [c for g in ("aave", "morpho", "morphoFixed") for c in cases[g]["id"] if c not in res]
    if missing:
        sys.exit(f"harness produced no result for {missing[:5]}")
    rows = score(cases, res)
    ladder = [cid for cid in res if cid.startswith("ladder-")]
    data = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "description": "Aave v3 and Morpho Blue accrual as deployed on Ethereum mainnet, against a 200-digit truth of the "
                       "formula each says it approximates, with BL127 and BL19 computing the same formula for contrast.",
        "pins": PINS, "claims": CLAIMS,
        "survey": {"block": survey["block"], "timestamp": survey["timestamp"],
                   "date": datetime.fromtimestamp(survey["timestamp"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")},
        "verify": json.loads(VERIFY.read_text()) if VERIFY.exists() else None,
        "liveChecks": {"aave": sum(1 for x in cases["aave"]["expect"] if x != "0"),
                       "morpho": sum(1 for x in cases["morpho"]["expect"] if x != "0")},
        "ladderCheck": (f"`test_ladder_models_match_deployed` runs LadderAave and LadderMorpho (the published ladder's "
                        f"transcriptions) and the pinned deployed libraries on the same integers for {len(ladder)} "
                        f"(rate, N) cells of the continuous-accrual scenario (5%, 50%, 307%; N = 1..10000 days): every "
                        f"output is identical. The models differ from a deployed position in two ways the ladder already "
                        f"states or implies: the principal is a RAY (Aave) or WAD (Morpho) number rather than token units "
                        f"(deployed Aave balances round with rayMulCeil for debt and rayMulFloor for aTokens, to the token's "
                        f"decimals), and the Morpho rate is a constant per-second WAD rate rather than the AdaptiveCurveIrm's "
                        f"trapezoid average."),
        "cases": rows,
    }
    OUT_JSON.write_text(json.dumps(data, indent=1) + "\n")
    write_md(data)
    print(f"{len(rows)} cases -> {OUT_JSON.relative_to(ROOT)}, {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Worst-case correct digits of the six lending-protocol rows of the report card.

    uv run --with mpmath python scripts/tiers/measure_protocols.py

Writes talk/scenes/data/tiers-worst-protocols.json and prints the table.

The measure (the user's rule, 2026-10-30): one number per row, its correct digits
on its WORST input, digits = -log10(|v - t| / |t|) with v the protocol's own
integer result and t the exact value of the model the protocol documents,
computed with mpmath at 120 significant digits. A result equal to the truth is
exact. A relative error of 1 or more (the result is off by more than the whole
interest, or by a factor) is 0 digits; the error itself is reported beside it.

Quantity measured per row (the protocol's own integers, transcribed below line
for line, with the pinned source named):
  Aave v3        the debt factor MathUtils.calculateCompoundedInterest - RAY (the
                 interest per unit of debt, in RAY), truth e^(r t) - 1 (the code's
                 comment: "the ideal formula - e^(rate per year * number of years)")
                 aave-dao/aave-v3-origin v3.7.0 @ cff15de6d1271b0c800fc001f4aea4c263e8a597
                 src/contracts/protocol/libraries/math/{MathUtils,WadRayMath}.sol
                 rate cap: DefaultReserveInterestRateStrategyV2.MAX_BORROW_RATE = 1000_00 bps
  SparkLend      the same factor in Aave v3.0.2's binomial form, truth (1 + r/Y)^t - 1
                 (the doc comment: "(1+x)^n = 1+n*x+[n/2*(n-1)]*x^2+...", x the
                 per-second rate, n the seconds)
                 sparkdotfi/sparklend-v1-core @ 8120e495061dc3315f0a86f682f4ca645a418bf7
                 contracts/protocol/libraries/math/{MathUtils,WadRayMath}.sol
                 rate cap: the largest getMaxVariableBorrowRate() over the 20 Spark
                 reserves at block 26307942 (320% APR)
  Morpho Blue    MathLib.wTaylorCompounded(borrowRate, elapsed) (WAD), truth
                 e^(rate t) - 1 ("to approximate a continuous compound interest rate")
                 morpho-org/morpho-blue v1.0.0 @ 55d2d99304fb3fb930c688462ae2ccabb1d533ad
                 src/libraries/MathLib.sol, src/Morpho.sol _accrueInterest
                 rate range: AdaptiveCurveIrm (morpho-blue-irm v1.0.0 @ a7d9cce3451b4a106bfd40933ac57a785b5228f3,
                 src/libraries/adaptive-curve/ConstantsLib.sol): 0.25 x MIN_RATE_AT_TARGET
                 to 4 x MAX_RATE_AT_TARGET per second, the curve's ends
  Compound v3    the index increment mulFactor(index, rate * timeElapsed) of
                 accruedInterestIndices (1e15 index), truth index * rate * t / 1e18
                 exactly (simple interest between accruals, as documented)
                 compound-finance/comet @ f766f51583c23acc33b2a7824654ef2029a96804
                 contracts/CometCore.sol L51, contracts/CometWithExtendedAssetList.sol L254-L321
                 curves: cUSDCv3 0xc3d688B66703497DAA19211EEdff47f25384cdc3 at block 26307942
  FraxLend       the new full-utilisation rate of VariableInterestRate V2
                 getFullUtilizationInterest, truth clamp(F 2^(+-d^2 t / H)) (the
                 documented half-life: at 100% utilisation the rate doubles per
                 half-life, at 0% it halves; d the code's normalised distance from
                 the band, so d = 1 at both ends)
                 FraxFinance/fraxlend @ 2bed49d4dcc6702d92dede825c3424893517d841
                 src/contracts/VariableInterestRate.sol L108-L140
                 config: rate contract 0x18500cB1f2fE7a40eBdA393383A0B8548a31F261 at block 26307942
  Euler v2       the stored rate at target of IRMAdaptiveCurve after one update,
                 truth clamp(r0 e^(speed err t)) ("rateAtTarget = startRateAtTarget *
                 e^linearAdaptation bounded to min and max")
                 euler-xyz/evk-periphery @ dd93a5f518ec0775f1cb87d358fe24b9fb5fbb66
                 src/IRM/IRMAdaptiveCurve.sol L144-L220, src/IRM/lib/ExpLib.sol L23-L43
                 config: IRMAdaptiveCurve 0xC9A0109D925251E0E5380d6fB4b105408d16C23D at block 26307942

The transcriptions are this file's own; FraxLend and Euler are checked against
the ladder's adapters (contracts/src/ladder/LadderFraxlend.sol, LadderEuler.sol)
through their committed cells in docs/benchmarks/ladder.json, and Aave and
Morpho against the deployed factors recorded for the 74 + 252 live positions in
docs/benchmarks/accrual-deployed.json (every one must match bit for bit).

Search per row: the domain's corners and edges, a grid, and 12,000 random inputs
(seeded), rates and times log-uniform, utilisation uniform and log-uniform.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

from mpmath import mp, mpf, exp, log10, power

mp.dps = 120
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "talk" / "scenes" / "data" / "tiers-worst-protocols.json"
ACCRUAL = ROOT / "docs" / "benchmarks" / "accrual-deployed.json"
LADDER = ROOT / "docs" / "benchmarks" / "ladder.json"

SEED = 20261030
N_RANDOM = 12000
BLOCK = 26307942  # mainnet block of the deployed parameters read below (2026-10-30)

RAY = 10**27
WAD = 10**18
HALF_RAY = RAY // 2
Y = 31_536_000  # SECONDS_PER_YEAR in Aave, Spark, Comet; 365 days in Morpho and Euler
T_MIN, T_MAX = 1, Y
HELD = (25, 14, 10)  # the 'both must pass' floors: digits held where the format holds at least H
APR_MIN = mpf("1e-6")  # lowest annual rate sampled where the rate is the input (0.0001% APR)


# ---------------------------------------------------------------------------
# Measure
# ---------------------------------------------------------------------------

def measure(v, t):
    """(digits, relErr) of v against t; digits None when exact."""
    v, t = mpf(v), mpf(t)
    if v == t:
        return None, mpf(0)
    if t == 0:
        return 0.0, mpf("inf")
    rel = (v - t) / abs(t)
    d = -log10(abs(rel))
    return max(0.0, float(d)), rel


def nearest_digits(t, unit=1):
    """Digits of the closest value on the protocol's own grid (multiples of `unit`)."""
    t = mpf(t)
    q = mp.nint(t / unit) * unit
    d, _ = measure(q, t)
    return 100.0 if d is None else d


def tdiv(a: int, b: int) -> int:
    """Solidity signed division: truncates toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def floor2(x: float) -> float:
    return math.floor(x * 100) / 100


# ---------------------------------------------------------------------------
# Aave v3.7.0 (debt), transcribed
# ---------------------------------------------------------------------------

def ray_mul(a: int, b: int) -> int:
    # WadRayMath.rayMul: (a*b + HALF_RAY) / RAY; reverts only if a*b + HALF_RAY overflows uint256
    assert b == 0 or a <= (2**256 - 1 - HALF_RAY) // b, "rayMul overflow (revert)"
    return (a * b + HALF_RAY) // RAY


def aave_compounded(rate: int, exp_: int) -> int:
    # MathUtils.calculateCompoundedInterest (v3.7.0, L59-L83)
    if exp_ == 0:
        return RAY
    x = (rate * exp_) // Y
    return RAY + x + ray_mul(x, x // 2 + ray_mul(x, x // 6))


AAVE_MAX = 1000_00 * 10**23  # MAX_BORROW_RATE 1000_00 bps in RAY = 1000% APR


def aave_eval(rate: int, t: int):
    v = aave_compounded(rate, t) - RAY
    truth = (exp(mpf(rate) * t / (mpf(RAY) * Y)) - 1) * RAY
    return v, truth, 1


# ---------------------------------------------------------------------------
# SparkLend (Aave v3.0.2 MathUtils), transcribed
# ---------------------------------------------------------------------------

def spark_compounded(rate: int, exp_: int) -> int:
    # MathUtils.calculateCompoundedInterest (sparklend-v1-core 8120e495, L50-L80)
    if exp_ == 0:
        return RAY
    exp_m1 = exp_ - 1
    exp_m2 = exp_ - 2 if exp_ > 2 else 0
    base2 = ray_mul(rate, rate) // (Y * Y)
    base3 = ray_mul(base2, rate) // Y
    second = exp_ * exp_m1 * base2 // 2
    third = exp_ * exp_m1 * exp_m2 * base3 // 6
    return RAY + (rate * exp_) // Y + second + third


SPARK_MAX = 3_200_000_000_000_000_000_000_000_000  # 320% APR, Spark's largest getMaxVariableBorrowRate (block above)


def spark_eval(rate: int, t: int):
    v = spark_compounded(rate, t) - RAY
    truth = (power(1 + mpf(rate) / (mpf(RAY) * Y), t) - 1) * RAY
    return v, truth, 1


# ---------------------------------------------------------------------------
# Morpho Blue v1.0.0, transcribed
# ---------------------------------------------------------------------------

def w_taylor_compounded(x: int, n: int) -> int:
    # MathLib.wTaylorCompounded (L38-L44): mulDivDown = (x*y)/d
    first = x * n
    second = (first * first) // (2 * WAD)
    third = (second * first) // (3 * WAD)
    return first + second + third


MORPHO_MIN_RAT = (WAD // 1000) // 31_536_000  # MIN_RATE_AT_TARGET = 0.001 ether / 365 days
MORPHO_MAX_RAT = (2 * WAD) // 31_536_000                                   # MAX_RATE_AT_TARGET = 2.0 ether / 365 days
MORPHO_MIN = MORPHO_MIN_RAT // 4  # curve at err = -1: rateAtTarget / CURVE_STEEPNESS (4)
MORPHO_MAX = MORPHO_MAX_RAT * 4   # curve at err = +1: 4 x rateAtTarget


def morpho_eval(rate: int, t: int):
    v = w_taylor_compounded(rate, t)
    truth = (exp(mpf(rate) * t / WAD) - 1) * WAD
    return v, truth, 1


# ---------------------------------------------------------------------------
# Compound v3 (Comet), transcribed; cUSDCv3 parameters read at BLOCK
# ---------------------------------------------------------------------------

COMET = {
    "supplyKink": 900000000000000000, "supplySlopeLow": 1141552511, "supplySlopeHigh": 101344495180, "supplyBase": 0,
    "borrowKink": 900000000000000000, "borrowSlopeLow": 880834601, "borrowSlopeHigh": 114155251141, "borrowBase": 475646879,
    "baseSupplyIndex": 1208710455421805, "baseBorrowIndex": 1274978631784042,
}
BASE_INDEX_SCALE = 10**15
FACTOR_SCALE = 10**18


def mul_factor(n: int, factor: int) -> int:
    return n * factor // FACTOR_SCALE


def comet_rate(side: str, u: int) -> int:
    # getSupplyRate / getBorrowRate (L297-L321)
    c = COMET
    kink, low, high, base = c[side + "Kink"], c[side + "SlopeLow"], c[side + "SlopeHigh"], c[side + "Base"]
    if u <= kink:
        return base + mul_factor(low, u)
    return base + mul_factor(low, kink) + mul_factor(high, u - kink)


def comet_eval(side: str, u: int, t: int, index: int):
    rate = comet_rate(side, u)
    v = mul_factor(index, rate * t)  # accruedInterestIndices: index += mulFactor(index, rate * timeElapsed)
    assert index + v < 2**64, "safe64 (revert)"
    truth = mpf(index) * rate * t / FACTOR_SCALE
    return v, truth, 1


# ---------------------------------------------------------------------------
# FraxLend VariableInterestRate V2, transcribed; 0x18500cB1... read at BLOCK
# ---------------------------------------------------------------------------

UTIL_PREC = 10**5
FRAX = {"MIN_TARGET_UTIL": 75000, "MAX_TARGET_UTIL": 85000, "VERTEX_UTILIZATION": 87500,
        "MIN_FULL_UTIL_RATE": 1582470460, "MAX_FULL_UTIL_RATE": 3164940920000, "ZERO_UTIL_RATE": 158247046,
        "RATE_HALF_LIFE": 172800, "VERTEX_RATE_PERCENT": 200000000000000000}


def frax_full_util(c: dict, dt: int, u: int, f: int) -> int:
    # getFullUtilizationInterest (L108-L140)
    H = c["RATE_HALF_LIFE"]
    if u < c["MIN_TARGET_UTIL"]:
        d = ((c["MIN_TARGET_UTIL"] - u) * 10**18) // c["MIN_TARGET_UTIL"]
        g = H * 10**36 + d * d * dt
        new = (f * (H * 10**36)) // g
    elif u > c["MAX_TARGET_UTIL"]:
        d = ((u - c["MAX_TARGET_UTIL"]) * 10**18) // (UTIL_PREC - c["MAX_TARGET_UTIL"])
        g = H * 10**36 + d * d * dt
        new = (f * g) // (H * 10**36)
    else:
        new = f
    new %= 2**64  # uint64(...) cast
    if new > c["MAX_FULL_UTIL_RATE"]:
        new = c["MAX_FULL_UTIL_RATE"]
    elif new < c["MIN_FULL_UTIL_RATE"]:
        new = c["MIN_FULL_UTIL_RATE"]
    return new


def frax_truth(c: dict, dt: int, u: int, f: int):
    H = c["RATE_HALF_LIFE"]
    if u < c["MIN_TARGET_UTIL"]:
        d = mpf(c["MIN_TARGET_UTIL"] - u) / c["MIN_TARGET_UTIL"]
        x = f * power(2, -d * d * dt / H)
    elif u > c["MAX_TARGET_UTIL"]:
        d = mpf(u - c["MAX_TARGET_UTIL"]) / (UTIL_PREC - c["MAX_TARGET_UTIL"])
        x = f * power(2, d * d * dt / H)
    else:
        x = mpf(f)
    return min(max(x, c["MIN_FULL_UTIL_RATE"]), c["MAX_FULL_UTIL_RATE"])


def frax_eval(f: int, u: int, t: int):
    return frax_full_util(FRAX, t, u, f), frax_truth(FRAX, t, u, f), 1


# ---------------------------------------------------------------------------
# Euler v2 IRMAdaptiveCurve, transcribed; 0xC9A0109D... read at BLOCK
# ---------------------------------------------------------------------------

EULER = {"TARGET_UTILIZATION": 900000000000000000, "INITIAL_RATE_AT_TARGET": 317097919,
         "MIN_RATE_AT_TARGET": 31709791, "MAX_RATE_AT_TARGET": 63419583967,
         "CURVE_STEEPNESS": 4000000000000000000, "ADJUSTMENT_SPEED": 3170979198376}
LN_2_INT = 693147180559945309
LN_WEI_INT = -41446531673892822312
WEXP_UPPER_BOUND = 93859467695000404319
WEXP_UPPER_VALUE = 57716089161558943949701069502944508345128422502756744429568


def w_exp(x: int) -> int:
    # ExpLib.wExp (L23-L43)
    if x < LN_WEI_INT:
        return 0
    if x >= WEXP_UPPER_BOUND:
        return WEXP_UPPER_VALUE
    adj = -(LN_2_INT // 2) if x < 0 else LN_2_INT // 2
    q = tdiv(x + adj, LN_2_INT)
    r = x - q * LN_2_INT
    exp_r = WAD + r + tdiv(tdiv(r * r, WAD), 2)
    return exp_r << q if q >= 0 else exp_r >> -q


def euler_err(c: dict, u: int) -> int:
    # _calcErr
    norm = WAD - c["TARGET_UTILIZATION"] if u > c["TARGET_UTILIZATION"] else c["TARGET_UTILIZATION"]
    return tdiv((u - c["TARGET_UTILIZATION"]) * WAD, norm)


def euler_end_rate(c: dict, r0: int, u_last: int, elapsed: int) -> int:
    # computeInterestRateInternal, the branch with state, and _newRateAtTarget
    speed = tdiv(c["ADJUSTMENT_SPEED"] * euler_err(c, u_last), WAD)
    lin = speed * elapsed
    if lin == 0:
        return r0
    r = tdiv(r0 * w_exp(lin), WAD)
    if r < c["MIN_RATE_AT_TARGET"]:
        return c["MIN_RATE_AT_TARGET"]
    if r > c["MAX_RATE_AT_TARGET"]:
        return c["MAX_RATE_AT_TARGET"]
    return r


def euler_truth(c: dict, r0: int, u_last: int, elapsed: int):
    tu = c["TARGET_UTILIZATION"]
    err = mpf(u_last - tu) / ((WAD - tu) if u_last > tu else tu)
    x = r0 * exp(mpf(c["ADJUSTMENT_SPEED"]) / WAD * err * elapsed)
    return min(max(x, c["MIN_RATE_AT_TARGET"]), c["MAX_RATE_AT_TARGET"])


def euler_eval(r0: int, u: int, t: int):
    return euler_end_rate(EULER, r0, u, t), euler_truth(EULER, r0, u, t), 1


# ---------------------------------------------------------------------------
# Checks of the transcriptions against the repo's recorded integers
# ---------------------------------------------------------------------------

def checks() -> list[str]:
    out = []
    acc = json.loads(ACCRUAL.read_text())
    live = [c for c in acc["cases"] if c["group"] == "live"]
    n_a = n_m = 0
    for c in live:
        if c["protocol"] == "aave" and c["kind"] == "borrow":
            assert aave_compounded(int(c["inputs"]["rate"]), int(c["inputs"]["t"])) == int(c["deployed"]["factor"]), c["id"]
            n_a += 1
        if c["protocol"] == "morpho":
            assert w_taylor_compounded(int(c["deployed"]["rate"]), int(c["inputs"]["t"])) == int(c["deployed"]["taylor"]), c["id"]
            n_m += 1
    out.append(f"Aave factor equals deployed.factor on all {n_a} live borrow positions; "
               f"Morpho wTaylorCompounded equals deployed.taylor on all {n_m} live markets (accrual-deployed.json)")
    lad = json.loads(LADDER.read_text())
    sc = next(s for s in lad["scenarios"] if s["id"] == "adaptive-rate")
    inputs = {i["name"]: i for i in sc["inputs"]}
    wide_f = dict(FRAX, MIN_FULL_UTIL_RATE=0, MAX_FULL_UTIL_RATE=2**64 - 1, MIN_TARGET_UTIL=75000, MAX_TARGET_UTIL=85000)
    rate0 = (4 * WAD // 100) // 31_536_000
    k = 0
    for name, util in (("reference", 100000), ("halving", 0), ("realistic", 92500), ("weekly", 100000)):
        step = int(inputs[name]["params"]["step"])
        for n, cell in inputs[name]["cells"]["fraxlend"].items():
            if not isinstance(cell, dict) or "raw" not in cell:
                continue
            assert frax_full_util(wide_f, int(n) * step, util, rate0) == int(cell["raw"]), (name, n)
            k += 1
    wide_e = dict(EULER, MIN_RATE_AT_TARGET=0, MAX_RATE_AT_TARGET=2**255 - 1)
    j = 0
    for name, util in (("euler-speed", WAD), ("euler-halving", 0)):
        step = int(inputs[name]["params"]["step"])
        for n, cell in inputs[name]["cells"]["euler"].items():
            if not isinstance(cell, dict) or "raw" not in cell:
                continue
            assert euler_end_rate(wide_e, rate0, util, int(n) * step) == int(cell["raw"]), (name, n)
            j += 1
    out.append(f"FraxLend equals the ladder's LadderFraxlend raw on {k} cells and Euler equals LadderEuler on {j} cells "
               "(ladder.json adaptive-rate, the adapters' wide clamps)")
    return out


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def logu(rng, lo, hi) -> int:
    return int(round(math.exp(rng.uniform(math.log(lo), math.log(hi)))))


TMIN, TMAX = T_MIN, T_MAX  # the current envelope's idle times (set by run)


def times_grid():
    g = {1, 2, 3, 12, 24, 60, 3600, 86400, 7 * 86400, 30 * 86400, 182 * 86400, TMAX - 1, Y - 1, Y, TMIN, TMAX}
    return sorted(t for t in g if TMIN <= t <= TMAX)


class Search:
    def __init__(self, fn, fmt, aux=None):
        self.fn, self.fmt = fn, fmt
        self.aux = aux or {}          # {label: predicate(args)}: the worst over a sub-domain, for the notes
        self.aux_worst = {}
        self.n = 0
        self.exact = 0
        self.worst = None  # (digits, |rel|, rel, args, v, truth, unit)
        self.reverts = []
        self.worst_u = None  # (|v - t| in units of the result's last place, args, v, truth)
        self.short = None  # worst (short18, args, capacity, digits held, rel)
        self.held = {H: None for H in HELD}  # worst (digits, |rel|, rel, args, capacity) where the format holds >= H digits

    def add(self, *args):
        self.n += 1
        try:
            v, truth, unit = self.fn(*args)
        except AssertionError as e:
            self.reverts.append((args, str(e)))
            return
        err_u = abs(mpf(v) - mpf(truth)) / unit
        if self.worst_u is None or err_u > self.worst_u[0]:
            self.worst_u = (err_u, args, v, truth)
        d, rel = measure(v, truth)
        if d is None:
            self.exact += 1
            return
        key = (d, -abs(rel))
        if self.worst is None or key < (self.worst[0], -self.worst[1]):
            self.worst = (d, abs(rel), rel, args, v, truth, unit)
        if truth != 0:
            capacity = float(log10(abs(mpf(truth)) / unit))  # significant digits the format holds at this value
            sh = max(0.0, min(capacity, 18.0) - d)  # short18: digits short of min(format, 18); d is clamped at 0
            if self.short is None or sh > self.short[0]:
                self.short = (sh, args, capacity, d, rel)
            for H in HELD:
                w = self.held[H]
                if capacity >= H and (w is None or key < (w[0], -w[1])):
                    self.held[H] = (d, abs(rel), rel, args, capacity)
        for label, pred in self.aux.items():
            w = self.aux_worst.get(label)
            if pred(*args) and (w is None or key < (w[0], -abs(w[1]))):
                self.aux_worst[label] = (d, rel, args)

    def result(self) -> dict:
        d, arel, rel, args, v, truth, unit = self.worst
        return {"digits": floor2(d), "relErr": float(rel), "args": args, "value": int(v),
                "truth": mp.nstr(truth, 25), "nearest": floor2(nearest_digits(truth, unit)),
                "n": self.n, "exact": self.exact, "reverts": len(self.reverts), "input": self.fmt(*args),
                "units": float(self.worst_u[0]), "unitsInput": self.fmt(*self.worst_u[1]),
                "unitsValue": int(self.worst_u[2]), "unitsTruth": mp.nstr(self.worst_u[3], 25),
                "short18": None if self.short is None else {
                    "short18": floor2(self.short[0]) if self.short[0] > 0 else 0.0, "input": self.fmt(*self.short[1]),
                    "format_digits": floor2(self.short[2]), "digits_held": floor2(self.short[3]),
                    "relErr": float(f"{float(self.short[4]):.4g}")},
                "held": {str(H): (None if w is None else {"digits": floor2(w[0]), "relErr": float(f"{float(w[2]):.4g}"),
                                                          "capacity": floor2(w[4]), "input": self.fmt(*w[3])})
                         for H, w in self.held.items()},
                "aux": "; ".join(f"{label}: {floor2(d):.2f} digits (relative error {float(rel):+.2e}) at {self.fmt(*a)}"
                                 for label, (d, rel, a) in self.aux_worst.items())}


def apr(rate: int, scale: int) -> str:
    x = mpf(rate) * (Y if scale == WAD else 1) / scale
    return mp.nstr(x * 100, 6) + "% APR"


def dur(t: int) -> str:
    if t == 86400:
        return "1 day"
    if t >= 86400:
        return f"{t // 86400} days" if t % 86400 == 0 else f"{t} s ({t / 86400:.1f} days)"
    for u, s in ((3600, "h"), (60, "min")):
        if t >= u and t % u == 0:
            return f"{t // u} {s}"
    return f"{t} s"


DAY = {"idle 1 day or less": lambda *a: a[-1] <= 86400}


def rate_rows(fn, lo: int, hi: int, scale_fmt, rng) -> Search:
    s = Search(fn, scale_fmt, DAY)
    rates = sorted({lo, hi, (lo + hi) // 2} | {int(lo * (hi / lo) ** (i / 15)) for i in range(16)})
    for r in rates:
        for t in times_grid():
            s.add(r, t)
    for _ in range(N_RANDOM):
        s.add(logu(rng, lo, hi), logu(rng, TMIN, TMAX))
    return s


def cap_ray(apr_max):
    return None if apr_max is None else int(mpf(apr_max) * RAY)


def cap_wad_s(apr_max):
    return None if apr_max is None else int(mpf(apr_max) * WAD / Y)


def run(env: dict | None = None) -> dict:
    """The six searches over the full documented domain (env None) or over an envelope
    {"apr_max": annual rate cap, "tmin": s, "tmax": s, "label": text}: rates (and the rate
    models' starting rates) capped at apr_max, idle times in [tmin, tmax]."""
    global TMIN, TMAX
    rng = random.Random(SEED)
    rows = {}
    a_max = None if env is None else env["apr_max"]
    TMIN, TMAX = (T_MIN, T_MAX) if env is None else (env["tmin"], env["tmax"])
    lim = lambda hi, cap: hi if cap is None else min(hi, cap)  # noqa: E731
    tdom = "1 s to 1 year" if env is None else env["label"]

    # Aave v3: rates 1e-6 APR .. 1000% APR (RAY), t 1 s .. 1 year
    s = rate_rows(aave_eval, int(APR_MIN * RAY), lim(AAVE_MAX, cap_ray(a_max)),
                  lambda r, t: f"{apr(r, RAY)} borrow rate, idle {dur(t)}", rng)
    rows["aave-v3"] = (s, "rates 0.0001% to 1000% APR (MAX_BORROW_RATE), 1 s to 1 year" if env is None else
                       f"rates 0.0001% to {mp.nstr(mpf(a_max) * 100, 6)}% APR, {tdom}")

    s = rate_rows(spark_eval, int(APR_MIN * RAY), lim(SPARK_MAX, cap_ray(a_max)),
                  lambda r, t: f"{apr(r, RAY)} borrow rate, idle {dur(t)}", rng)
    rows["sparklend"] = (s, "rates 0.0001% to 320% APR (the largest getMaxVariableBorrowRate of Spark's 20 reserves), 1 s to 1 year"
                         if env is None else f"rates 0.0001% to {mp.nstr(mpf(a_max) * 100, 6)}% APR, {tdom}")

    s = rate_rows(morpho_eval, MORPHO_MIN, lim(MORPHO_MAX, cap_wad_s(a_max)),
                  lambda r, t: f"{apr(r, WAD)} borrow rate, idle {dur(t)}", rng)
    rows["morpho-blue"] = (s, "AdaptiveCurveIrm's whole range, 0.025% to 800% APR per second in WAD, 1 s to 1 year"
                           if env is None else f"rates 0.025% (the IRM's floor) to {mp.nstr(mpf(a_max) * 100, 6)}% APR, {tdom}")

    # Compound v3: side, utilisation 0..100%, t, index from 1e15 (genesis) to today's
    s = Search(comet_eval, lambda side, u, t, idx: (
        f"{side} side at {mp.nstr(mpf(u) / 10**16, 4)}% utilisation ({apr(comet_rate(side, u), WAD)}), "
        f"{dur(t)}, index {mp.nstr(mpf(idx) / BASE_INDEX_SCALE, 10)}"), {
        "rates of 0.01% APR or more": lambda side, u, t, idx: comet_rate(side, u) * Y >= WAD // 10000,
        "rates of 1% APR or more": lambda side, u, t, idx: comet_rate(side, u) * Y >= WAD // 100,
        "idle 1 day or more": lambda side, u, t, idx: t >= 86400})
    idxs = {"supply": [BASE_INDEX_SCALE, COMET["baseSupplyIndex"]], "borrow": [BASE_INDEX_SCALE, COMET["baseBorrowIndex"]]}
    us = sorted({0, 1, 10**9, 10**12, 10**15, 10**16, 10**17, 5 * 10**17, 9 * 10**17, 9 * 10**17 + 1, 95 * 10**16, 10**18})
    for side in ("supply", "borrow"):
        for u in us:
            for t in times_grid():
                for idx in idxs[side]:
                    s.add(side, u, t, idx)
    for i in range(N_RANDOM):
        side = ("supply", "borrow")[i % 2]
        u = logu(rng, 1, 10**18) if i % 4 < 2 else rng.randrange(0, 10**18 + 1)
        idx = rng.randrange(BASE_INDEX_SCALE, idxs[side][1] + 1)
        s.add(side, u, logu(rng, TMIN, TMAX), idx)
    rows["compound-v3"] = (s, "both sides of cUSDCv3's deployed curves (at most 35.2% supply, 40.0% borrow APR), utilisation 0 to "
                           f"100% (1e18 grid), {tdom}, index 1e15 to today's")

    # FraxLend: starting full-utilisation rate in [MIN, MAX], utilisation 0..1e5, t
    c = FRAX
    s = Search(frax_eval, lambda f, u, t: (
        f"full-utilisation rate {apr(f, WAD)}, {mp.nstr(mpf(u) / 1000, 5)}% utilisation, one update after {dur(t)}"), {
        "utilisation 0% or 100% (the half-life as quoted)": lambda f, u, t: u in (0, UTIL_PREC),
        "idle 1 day or less": lambda f, u, t: t <= 86400})
    f_hi = lim(c["MAX_FULL_UTIL_RATE"], cap_wad_s(a_max))
    fs = sorted({c["MIN_FULL_UTIL_RATE"], f_hi, c["MIN_FULL_UTIL_RATE"] * 2,
                 int(math.sqrt(c["MIN_FULL_UTIL_RATE"] * f_hi)), f_hi // 2})
    for f in fs:
        for u in (0, 1, 37500, 74999, 75000, 85000, 85001, 92500, 99999, 100000):
            for t in times_grid() + [86400 * k for k in range(1, 40) if TMIN <= 86400 * k <= TMAX]:
                s.add(f, u, t)
    for i in range(N_RANDOM):
        u = rng.randrange(0, UTIL_PREC + 1) if i % 2 else rng.choice((0, 100000))
        s.add(logu(rng, c["MIN_FULL_UTIL_RATE"], f_hi), u, logu(rng, TMIN, TMAX))
    rows["fraxlend"] = (s, "deployed V2 rate contract: starting full-utilisation rate MIN to "
                        + ("MAX (0.5% to 10000% APR)" if env is None else f"{mp.nstr(mpf(a_max) * 100, 6)}% APR (clamps MIN/MAX as deployed)")
                        + f", utilisation 0 to 100% (1e5 grid), one update after {tdom}")

    # Euler: start rate at target [MIN, MAX], last utilisation 0..1e18, t
    c = EULER
    s = Search(euler_eval, lambda r0, u, t: (
        f"rate at target {apr(r0, WAD)}, {mp.nstr(mpf(u) / 10**16, 5)}% utilisation, one update after {dur(t)}"), DAY)
    r_hi = lim(c["MAX_RATE_AT_TARGET"], cap_wad_s(a_max))
    for r0 in sorted({c["MIN_RATE_AT_TARGET"], c["INITIAL_RATE_AT_TARGET"], r_hi,
                      int(math.sqrt(c["MIN_RATE_AT_TARGET"] * r_hi))}):
        for u in (0, 1, 45 * 10**16, 9 * 10**17 - 1, 9 * 10**17 + 1, 95 * 10**16, 10**18):
            for t in times_grid():
                s.add(r0, u, t)
    for i in range(N_RANDOM):
        u = rng.randrange(0, WAD + 1) if i % 2 else rng.choice((0, WAD))
        s.add(logu(rng, c["MIN_RATE_AT_TARGET"], r_hi), u, logu(rng, TMIN, TMAX))
    rows["euler-adaptive-curve"] = (s, "deployed IRMAdaptiveCurve: rate at target MIN to "
                                    + ("MAX (0.1% to 200% APR)" if env is None else f"{mp.nstr(mpf(a_max) * 100, 6)}% APR (clamps as deployed)")
                                    + f", utilisation 0 to 100% (WAD), one update after {tdom}")
    return rows


# ---------------------------------------------------------------------------
# Live positions (accrual-deployed.json)
# ---------------------------------------------------------------------------

def live() -> dict:
    acc = json.loads(ACCRUAL.read_text())
    cs = [c for c in acc["cases"] if c["group"] == "live"]
    out = {}
    for p in ("aave", "morpho"):
        mine = [c for c in cs if c["protocol"] == p]
        dig = [c["truth"][c["primaryTruth"]]["deployed"]["digitsInterest"] for c in mine]
        w = min(mine, key=lambda c: c["truth"][c["primaryTruth"]]["deployed"]["digitsInterest"])
        model = []
        units = []
        for c in mine:
            if p == "aave" and c["kind"] == "borrow":
                v, t, _ = aave_eval(int(c["inputs"]["rate"]), int(c["inputs"]["t"]))
            elif p == "morpho":
                v, t, _ = morpho_eval(int(c["deployed"]["rate"]), int(c["inputs"]["t"]))
            else:
                continue
            d, _ = measure(v, t)
            model.append((100.0 if d is None else d, c["id"]))
            rate_apr = (mpf(c["inputs"]["rate"]) / RAY if p == "aave" else mpf(c["deployed"]["rate"]) * Y / WAD)
            units.append((abs(mpf(v) - t), c["id"], rate_apr, int(c["inputs"]["t"])))
        out[p] = {"n": len(mine), "min": min(dig), "minId": w["id"], "median": sorted(dig)[len(dig) // 2] if len(dig) % 2 else
                  (sorted(dig)[len(dig) // 2 - 1] + sorted(dig)[len(dig) // 2]) / 2,
                  "modelMin": floor2(min(model)[0]), "modelMinId": min(model)[1], "modelN": len(model),
                  "units": max(units, key=lambda x: x[0])}
    return out


def envelope() -> dict:
    """The 'normal inputs' envelope (the user, 2026-10-30): from the 326 live positions of
    accrual-deployed.json, annual rates up to the largest Aave rateAnnual (the coordinator's
    0.6773) and idle times from the smallest to the largest observed. Also reports the
    largest rate a live Morpho market actually charged, which is above that cap."""
    acc = json.loads(ACCRUAL.read_text())
    cs = [c for c in acc["cases"] if c["group"] == "live"]
    ts = [int(c["inputs"]["t"]) for c in cs]
    aave_max = max(c["rateAnnual"] for c in cs if c["protocol"] == "aave")
    charged = [mpf(c["deployed"]["rate"]) * Y / WAD for c in cs if c["protocol"] == "morpho"]
    cap = mpf(str(round(aave_max, 4)))
    return {"positions": len(cs), "apr_max": cap, "tmin": min(ts), "tmax": max(ts),
            "aaveMax": aave_max, "morphoChargedMax": float(max(charged)),
            "morphoAboveCap": sum(1 for x in charged if x > cap),
            "label": f"{min(ts)} s to {max(ts)} s ({max(ts) / 86400:.1f} days)"}


def digits_lost(units: float) -> float:
    """log10(max(worst error in units of the last place, 1)): 0 when every answer is within one unit."""
    return floor2(math.log10(max(units, 1.0)))


UNIT = {"aave-v3": "ray unit (1e-27) of the debt factor", "sparklend": "ray unit (1e-27) of the debt factor",
        "morpho-blue": "WAD unit (1e-18) of the compounded factor", "compound-v3": "index unit (1e-15 of the 1e15 base index)",
        "fraxlend": "1e-18 per second of the full-utilisation rate", "euler-adaptive-curve": "1e-18 per second (WAD) of the rate at target"}


TRUTH = {
    "aave-v3": "e^(r t) - 1, the debt factor's 'ideal formula' in MathUtils (v3.7.0)",
    "sparklend": "(1 + r/31536000)^t - 1, the per-second compounding Aave v3.0.2's MathUtils doc comment expands",
    "morpho-blue": "e^(r t) - 1, the continuous compounding wTaylorCompounded approximates",
    "compound-v3": "index x rate x t / 1e18 exactly: Comet's documented simple interest between accruals",
    "fraxlend": "clamp(F x 2^(+-d^2 t/H)): the documented half-life (x2 per H at 100%, x1/2 at 0%), d the code's distance from the band",
    "euler-adaptive-curve": "clamp(r0 x e^(speed x err x t)), the formula IRMAdaptiveCurve's comment states",
}


def summary(r: dict) -> dict:
    return {"worst_digits": r["digits"], "worst_input": r["input"],
            "worst_units": float(f"{r['units']:.6g}"), "digits_lost": digits_lost(r["units"]),
            "worst_input_units": r["unitsInput"], "units_detail": f"value {r['unitsValue']} against truth {r['unitsTruth']}"}


def search_text(r: dict, dom: str) -> str:
    rel = r["relErr"]
    relS = f"{rel:+.3e}" if abs(rel) < 1 else f"{rel:+.3e} (result x{1 + rel:.4g} of the truth)"
    return (f"{r['n']} inputs ({dom}): corners, a grid and {N_RANDOM} seeded random (seed {SEED}); "
            f"{r['exact']} exact, {r['reverts']} reverts. Fewest digits held: value {r['value']} against truth {r['truth']}, "
            f"relative error {relS}; the nearest value on the protocol's grid would hold {r['nearest']} digits there. "
            f"Largest error in units: {r['units']:.4g} at {r['unitsInput']}. Sub-domains: {r['aux']}.")


def main() -> int:
    notes = checks()
    env = envelope()
    domain = run()
    capped = run(env)
    env_c = dict(env, apr_max=mpf(8))
    normal = run(env_c)
    lv = live()
    doc = {"_doc": ("Worst cases of the six protocol rows of talk/scenes/data/tiers.json, generated by "
                    "scripts/tiers/measure_protocols.py (deployed parameters read at mainnet block %d). The top-level "
                    "fields of each row are over NORMAL inputs, the envelope in 'normal_envelope' (the user, 2026-10-30: "
                    "'1000%% apr doesnt make sense. let's use normal inputs', then: up to the rates live markets actually "
                    "charged); 'domain_worst' keeps the full documented domain and 'capped_67pct' the same envelope capped "
                    "at Aave's largest live rate (67.73%% APR), both for the notes. 'held_floor' (the 'both must pass' rule): "
                    "for H in 25, 14, 10, the fewest digits held over the envelope's inputs where the result's format holds at "
                    "least H significant digits at the true value (log10(|truth| / unit) >= H; 'capacity' is that count at "
                    "the worst input), null when no input qualifies. 'short18' (the user's blended number, replacing 'both must pass'): "
                    "the worst over the envelope of max(0, min(format digits at the value, 18) - digits held), format digits = "
                    "log10(|exact| / unit), digits held = -log10(relative error) clamped at 0, with its input "
                    "('short18_input', 'short18_format_digits', 'short18_digits_held'); 'correctly_rounded' is true iff "
                    "worst_units < 1 everywhere (every answer within one unit in its stated direction). 'worst_units' is the largest |v - t| over the searched inputs in units "
                    "of the result's own last place ('unit'), at 'worst_input_units'; 'digits_lost' = log10(max(worst_units, 1)), "
                    "so an answer within one unit (correctly rounded, or a floor short of one unit) loses 0. 'worst_digits' "
                    "is the fewest correct digits held, -log10(relative error) floored to two decimals (0 for an error of 100%% "
                    "or more), at 'worst_input'. 'live_*' (Aave, Morpho) are over the live positions themselves: live_min is "
                    "the file's digitsInterest (token units, against each truth it states); live_worst_units is the factor's "
                    "error in units (Aave: the 39 borrows; Morpho: wTaylorCompounded at each of the 252 markets' charged rate). "
                    "Truth: the model each protocol documents, mpmath at 120 digits. No tier: the coordinator grades." % BLOCK),
           "normal_envelope": {
               "source": "docs/benchmarks/accrual-deployed.json, group 'live' (%d positions: 74 Aave, 252 Morpho)" % env["positions"],
               "annual_rate_max": float(env_c["apr_max"]),
               "annual_rate_max_source": ("the largest rate a live market charged: Morpho, %.10f per year (800%% APR, the "
                                          "AdaptiveCurveIrm's ceiling, %d of 252 Morpho markets above Aave's largest live "
                                          "rate %.4f)" % (env["morphoChargedMax"], env["morphoAboveCap"], env["aaveMax"])),
               "idle_seconds": [env["tmin"], env["tmax"]],
               "utilisation": "0 to 100% for Compound's curves and the FraxLend and Euler rate models",
               "lower_rates": "Aave, SparkLend from 0.0001% APR; Morpho from the IRM's floor 0.025%; FraxLend and Euler from their deployed minimum",
               "upper_rates_per_row": ("each row's rate is capped at the smaller of 800% APR and its own documented maximum: "
                                       "Aave 800%, SparkLend 320%, Morpho 800%, Compound its curves (35.2% supply, 40.0% borrow), "
                                       "FraxLend starting full-utilisation rate 800% (clamp 10000%), Euler rate at target 200% (its MAX)"),
           },
           "checks": notes, "rows": {}}
    print(f"normal envelope: rates <= {float(env_c['apr_max'])}, idle {env['label']}")
    print(f"{'row':22} {'lost':>6} {'units':>10}  {'held':>5}  {'dom lost':>8}  {'67.7%':>6}  {'H25':>5} {'H14':>5} {'H10':>5}  worst input (units)")
    for rid in domain:
        rn, rd, rc = normal[rid][0].result(), domain[rid][0].result(), capped[rid][0].result()
        row = {**summary(rn), "unit": UNIT[rid], "truth": TRUTH[rid], "search": search_text(rn, normal[rid][1])}
        lost = row["digits_lost"]
        row["chip"] = "0 lost" if lost == 0 else f"{lost:.1f} lost"
        L = lv.get({"aave-v3": "aave", "morpho-blue": "morpho"}.get(rid, ""))
        row["live_min"] = None if L is None else L["min"]
        if L is not None:
            u, cid, r_apr, t = L["units"]
            row["live_worst_units"] = float(f"{float(u):.6g}")
            row["live_digits_lost"] = digits_lost(float(u))
            row["live_worst_input"] = f"{cid}: {mp.nstr(r_apr * 100, 6)}% APR, idle {dur(t)}"
            row["live_note"] = (f"digits held over the {L['n']} live positions (the file's digitsInterest): min {L['min']} "
                                f"({L['minId']}), median {L['median']:.2f}; the factor alone over {L['modelN']}: min {L['modelMin']} "
                                f"({L['modelMinId']})")
        row["domain_worst"] = {**summary(rd), "search": search_text(rd, domain[rid][1])}
        row["held_floor"] = rn["held"]
        sh = rn["short18"]
        row["short18"] = sh["short18"]
        row["short18_input"] = sh["input"]
        row["short18_format_digits"] = sh["format_digits"]
        row["short18_digits_held"] = sh["digits_held"]
        row["correctly_rounded"] = rn["units"] < 1
        if row["short18"] == 0:
            row["short18_input"] = "none: 0 at every searched input (each answer within one unit)"
            row["short18_format_digits"] = row["short18_digits_held"] = None
        row["capped_67pct"] = {k: v for k, v in summary(rc).items()}
        doc["rows"][rid] = row
        print(f"{rid:22} {lost:6.2f} {rn['units']:10.3g}  {rn['digits']:5.2f}  {rd and digits_lost(rd['units']):8.2f}  "
              f"{digits_lost(rc['units']):6.2f}  "
              + " ".join(f"{'-' if rn['held'][str(H)] is None else rn['held'][str(H)]['digits']:>5}" for H in HELD)
              + f"  short18 {rn['short18']['short18']} at {rn['short18']['input']} (format {rn['short18']['format_digits']})"
              + ("" if L is None else f"   [live: {row['live_digits_lost']} lost at {row['live_worst_input']}]"))
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    for n in notes:
        print("check:", n)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

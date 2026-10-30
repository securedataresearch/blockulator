#!/usr/bin/env python3
"""Digits lost: every library's worst error over its function's documented
domain, in units of the result's own last place, on seeded inputs.

    uv run scripts/sweep/lost.py            # inputs -> forge (test/lost/LostBench.t.sol) -> lost.json
    uv run scripts/sweep/lost.py score      # re-score the last forge outputs only
    LOST_N=4000 uv run scripts/sweep/lost.py   # the per-function count (default 40,000: wad.py's 4,000 x 10)

The 18-decimal libraries (BlockulatorWad, Solady, PRBMath SD59x18 and
UD60x18, Solmate, OpenZeppelin, Uniswap, snekmate) run on scripts/sweep/wad.py's
own seeded inputs (seed 20261023, its generators at LOST_N per function: the
first 4,000 are wad.py's own) through wad.py's own calls. The libraries wad.py
misses run beside them: Balancer LogExpMath (v3, vendored; exp, ln, log(x, 2),
log(x, 10), pow) and FixedPoint's mulDown and divDown (a * b / ONE,
a * ONE / b) on the same WAD inputs; ABDKMath64x64 (exp, exp_2, ln, log_2,
sqrt, mul, div, pow(x, uint)) and ABDKMathQuad (exp, pow_2, ln, log_2, sqrt,
mul, div) on inputs of their own built the same way (log-uniform magnitudes
over the format, values whose exact result sits near a unit boundary, exact
cases, the everyday range, the ends); Maker's rpow in RAY (Solady's
FixedPointMathLib.rpow, which mirrors DSS _rpow step for step, as
contracts/src/ladder/LadderMaker.sol takes it) on per-second and per-period
rates, as pot.sol and jug.sol compound them, and on any base.

Truth is the exact real value: mpmath at 300 digits (1,000 bits for
binary128). The error of a result is |result - exact| in units of the
result's last place: one wei for WAD, 10^-27 for RAY, 2^-64 for 64.64, and
for binary128 2^(e - 112) where 2^e <= |exact| < 2^(e+1) (e clamped at the
subnormal floor, -16382). worst_ulps is the largest over the inputs that
returned a value; digits_lost = log10(max(worst_ulps, 1)) rounded to 0.1, and
0 when every result is correctly rounded: within half a unit where no
direction is stated or the format is IEEE (nearest), below one unit on the
stated side where one is (floor, ceiling, toward zero), and below one unit
either side (faithful) where a library states no rounding at all. A result of
0 for an exact value below the format's last place is within a unit and
loses nothing.

Reverts: a revert (or, for binary128, NaN or infinity) where the exact value
fits the format is reverts_in_range, recorded apart (it grades F); a value
where the exact one does not exist or fit is value_out_of_range. A function
documented on part of the input range is scored on that part (Balancer exp:
-41 <= x <= 130; pow: x < 2^255, y < 2^254 / 10^20, -41 <= y ln x <= 130;
the logs x > 0; PRBMath UD60x18's exp, logs and pow as wad.py states them);
its reverts outside it where the value fits are counted apart
(reverts_outside_domain_value_fits).

BL127 and BL19 are not run here: their rows are docs/benchmarks/sweep.json's
(make sweep: every op correctly rounded, 0 misrounded), copied as such.
Writes docs/benchmarks/lost.json.
"""
from __future__ import annotations

import json
import math
import multiprocessing as mpc
import os
import random
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wad  # noqa: E402

ROOT = wad.ROOT
D = wad.D
OUT = wad.OUT
T256, I255, W, SEED = wad.T256, wad.I255, wad.W, wad.SEED
N = int(os.environ.get("LOST_N", 10 * wad.N))
CHUNK = int(os.environ.get("LOST_CHUNK", 4000))
WORKERS = int(os.environ.get("LOST_WORKERS", os.cpu_count() or 1))
Q64 = 1 << 64
I127 = 1 << 127
RAY = 10**27
DIRNAME = {0: "floor", 1: "ceiling", 2: "toward zero", 3: "nearest", None: "none stated (faithful: under one unit either side)"}
QDIR = "nearest (IEEE 754 binary128 default; ABDKMathQuad states no rounding)"


# ---- binary128 -------------------------------------------------------------

QBIAS, QM = 16383, 112
QEMIN = 1 - QBIAS          # -16382
QMAXEXP = 16383


def q_pack(neg: bool, man: int, exp: int) -> int:
    """The binary128 bits of (-1)^neg man 2^exp, exactly representable (or a
    subnormal truncated: only exact ones are built)."""
    if man == 0:
        return int(neg) << 127
    k = 113 - man.bit_length()
    man, exp = man << k if k >= 0 else man >> -k, exp - k
    e = exp + QM            # the unbiased exponent of the leading bit
    if e > QMAXEXP:
        return (int(neg) << 127) | (0x7FFF << 112)
    if e < QEMIN:           # subnormal
        sh = QEMIN - e
        return (int(neg) << 127) | (man >> sh)
    return (int(neg) << 127) | ((e + QBIAS) << 112) | (man - (1 << 112))


def q_from(v) -> int:
    """v (an mpf, int or float) to nearest binary128 (normal range)."""
    from mpmath import mp, mpf
    with mp.workprec(113):
        x = +mpf(v)
    if x == 0:
        return 0
    man, exp = x.man_exp
    return q_pack(bool(x < 0), abs(int(man)), int(exp))


def q_val(bits: int):
    """(kind, value): ('num', exact mpf) or ('inf', sign) or ('nan', None)."""
    from mpmath import mpf, ldexp
    bits &= (1 << 128) - 1
    neg = bits >> 127
    e = (bits >> 112) & 0x7FFF
    f = bits & ((1 << 112) - 1)
    if e == 0x7FFF:
        return ("nan", None) if f else ("inf", -1 if neg else 1)
    man, ex = (f, QEMIN - QM) if e == 0 else (f | (1 << 112), e - QBIAS - QM)
    v = ldexp(mpf(man), ex)
    return ("num", -v if neg else v)


def q_ulp(v):
    """The last place of binary128 at the exact value v's binade."""
    from mpmath import mpf, ldexp
    if v == 0:
        return ldexp(mpf(1), QEMIN - QM)
    man, exp = v.man_exp
    e = abs(int(man)).bit_length() + int(exp) - 1
    return ldexp(mpf(1), max(e, QEMIN) - QM)


def q_rand(rng, lo, hi):
    """A random binary128 with a random 113-bit significand and unbiased
    exponent uniform in lo..hi."""
    return q_pack(False, (1 << 112) | rng.getrandbits(112), rng.randint(lo, hi) - QM)


def q_neg(bits, rng, p=0.5):
    return bits | (1 << 127) if rng.random() < p else bits


# ---- inputs the wad.py generators do not make ------------------------------

def lu(rng, lo, hi):
    return wad.lu(rng, lo, hi)


def sg(rng, x, neg=0.5):
    return wad.sg(rng, x, neg)


def c128(x):
    """Clamp to int128."""
    return max(-I127, min(I127 - 1, x))


def gen_abdk_exp(rng, base):
    from mpmath import mp, mpf, log
    mp.dps = 120
    lg = (lambda v: log(v)) if base == "e" else (lambda v: log(v, 2))
    hi = 66 if base == "e" else 66
    a = []
    for i in range(N):
        kind = i % 4
        if kind == 0:      # uniform over the domain and past each end
            x = rng.randint(-70 * Q64, hi * Q64)
        elif kind == 1:    # |x| log-uniform from one unit
            x = sg(rng, lu(rng, 0, 71))
        elif kind == 2:    # the result near a whole number of units
            k = lu(rng, 1, 127)
            x = int(mp.nint(lg(mpf(k) / Q64) * Q64)) + rng.choice((-1, 0, 1))
        else:              # the everyday range
            x = rng.randint(-20 * Q64, 20 * Q64)
        a.append(c128(x))
    a[:9] = [0, 64 * Q64 - 1, 64 * Q64, -64 * Q64, -64 * Q64 - 1, 1, -1, -I127, I127 - 1]
    return a, None


def gen_abdk_log(rng, base):
    from mpmath import mp, mpf, exp
    mp.dps = 120
    a = []
    for i in range(N):
        kind = i % 4
        if kind == 0:
            x = lu(rng, 1, 127)
        elif kind == 1:    # near one
            x = Q64 + sg(rng, lu(rng, 0, 63))
        elif kind == 2:    # the log near a whole number of units
            k = sg(rng, lu(rng, 1, 69))
            x = int(mp.nint((exp(mpf(k) / Q64) if base == "e" else mpf(2) ** (mpf(k) / Q64)) * Q64))
            x += rng.choice((-1, 0, 1))
        else:
            if rng.random() < 0.25:
                k = rng.randint(-64, 62)
                x = Q64 << k if k >= 0 else Q64 >> -k
            else:
                x = rng.randint(Q64 // 1000, 1000 * Q64)
        a.append(min(max(x, 1), I127 - 1))
    a[:5] = [Q64, 1, I127 - 1, 0, -1]
    return a, None


def gen_abdk_sqrt(rng):
    a = []
    for i in range(N):
        kind = i % 3
        if kind == 0:
            x = lu(rng, 0, 127)
        else:              # x 2^64 near a perfect square m^2
            m = lu(rng, 1, 95)
            x = (m * m) // Q64 + rng.choice((-1, 0, 0, 1))
        a.append(min(max(x, 0), I127 - 1))
    a[:4] = [0, 1, I127 - 1, Q64]
    return a, None


def gen_abdk_mul(rng):
    a, b = [], []
    for i in range(N):
        kind = i % 4
        if kind == 0:
            x, y = lu(rng, 1, 100), lu(rng, 1, 100)
        elif kind == 1:    # the product near a multiple of 2^64
            y = lu(rng, 1, 100)
            x = wad.near_mult(rng, y, Q64)
        elif kind == 2:    # big by small
            x, y = lu(rng, 100, 127), lu(rng, 1, 40)
        else:
            x, y = lu(rng, 0, 127), lu(rng, 0, 127)
        a.append(c128(sg(rng, min(x, I127 - 1))))
        b.append(c128(sg(rng, min(y, I127 - 1))))
    return a, b


def gen_abdk_div(rng):
    a, b = [], []
    for i in range(N):
        kind = i % 4
        if kind == 0:
            x, y = lu(rng, 1, 100), lu(rng, 1, 100)
        elif kind == 1:    # x 2^64 one unit off a multiple of y
            y = lu(rng, 1, 127)
            m = rng.getrandbits(rng.randint(1, 120)) + 1
            x = max((m * y + rng.choice((-1, 0, 1))) // Q64, 0)
        elif kind == 2:
            x, y = lu(rng, 100, 127), lu(rng, 1, 127)
        else:
            x, y = lu(rng, 0, 127), lu(rng, 0, 127)
        a.append(c128(sg(rng, min(x, I127 - 1))))
        b.append(c128(sg(rng, min(y, I127 - 1))))
    return a, b


def gen_abdk_pow(rng):
    a, b = [], []
    for i in range(N):
        kind = i % 4
        if kind == 0:      # x log-uniform, n keeping |n ln x| under about 50
            x = lu(rng, 1, 127)
            lx = abs(math.log(x / Q64)) or 1e-19
            n = rng.randint(0, int(min(50 / lx, 2.0 ** 40)))
            x = sg(rng, x, 0.2)
        elif kind == 1:    # everyday: x in 0.5..2, n to 1,000
            x, n = rng.randint(Q64 // 2, 2 * Q64), rng.randint(0, 1000)
        elif kind == 2:    # x near one, n large
            x, n = Q64 + sg(rng, lu(rng, 0, 50)), lu(rng, 1, 64)
        else:              # whole numbers to whole powers (exact), negative bases
            v = rng.randint(2, 1 << 10)
            x = sg(rng, v * Q64, 0.3)
            n = rng.randint(0, int(62 / math.log2(v)))
        a.append(c128(x)), b.append(n)
    a[:4], b[:4] = [0, 0, Q64, -Q64], [0, 5, (1 << 255), 3]
    return a, b


def gen_q_exp(rng, base):
    from mpmath import mp, mpf, log
    mp.dps = 60
    top = 11360.0 if base == "e" else 16390.0
    bot = -11450.0 if base == "e" else -16500.0
    a = []
    for i in range(N):
        kind = i % 4
        if kind == 0:      # uniform over the range and past each end
            x = q_from(rng.uniform(bot, top))
        elif kind == 1:    # |x| from 2^-16000 up: the result near one
            x = q_neg(q_rand(rng, -16000, 13), rng)
        elif kind == 2:    # the everyday range
            x = q_from(mpf(rng.uniform(-20, 20)) + mpf(rng.random()) * mpf(2) ** -60)
        else:              # x = ln y for a random binary128 y: the result near a representable value
            y = q_val(q_rand(rng, -16381, 16382))[1]
            x = q_from(log(y) if base == "e" else log(y, 2))
        a.append(x)
    a[:3] = [0, q_from(1), q_from(-1)]
    return a, None


def gen_q_log(rng, base):
    a = []
    for i in range(N):
        kind = i % 4
        if kind == 0:      # any normal
            x = q_rand(rng, QEMIN, QMAXEXP)
        elif kind == 1:    # near one
            k = rng.randint(1, 112)
            d = q_val(q_rand(rng, -k, -k))[1]
            x = q_from(1 + d if rng.random() < 0.5 else 1 - d)
        elif kind == 2:    # powers of two (log_2 exact) and subnormals
            if rng.random() < 0.7:
                x = q_pack(False, 1, rng.randint(QEMIN - QM, QMAXEXP))
            else:
                x = rng.getrandbits(112) or 1
        else:              # the everyday range
            x = q_from(rng.uniform(0.001, 1000))
        a.append(x)
    a[:4] = [q_from(1), 1, (0x7FFE << 112) | ((1 << 112) - 1), 0]
    return a, None


def gen_q_sqrt(rng):
    a = []
    for i in range(N):
        kind = i % 4
        if kind == 0:
            x = q_rand(rng, QEMIN, QMAXEXP)
        elif kind == 1:    # subnormals
            x = rng.getrandbits(rng.randint(1, 112)) or 1
        elif kind == 2:    # perfect squares m^2 4^k (exact roots) and one place either side
            m = lu(rng, 1, 56)
            x = q_pack(False, m * m, 2 * rng.randint(-8000, 8000))
            if rng.random() < 0.5:
                x += rng.choice((-1, 1))
        else:
            x = q_from(rng.uniform(0.001, 1e6))
        a.append(x)
    a[:3] = [0, 1, q_from(1)]
    return a, None


def gen_q_mul(rng, div):
    a, b = [], []
    for i in range(N):
        kind = i % 4
        if kind == 0:
            x, y = q_rand(rng, -8000, 8000), q_rand(rng, -8000, 8000)
        elif kind == 1:    # the everyday range
            x, y = q_rand(rng, -30, 30), q_rand(rng, -30, 30)
        elif kind == 2:    # anywhere: overflow and underflow included
            x, y = q_rand(rng, QEMIN, QMAXEXP), q_rand(rng, QEMIN, QMAXEXP)
        else:              # exact products and quotients of short significands
            m1, m2 = lu(rng, 1, 56), lu(rng, 1, 56)
            e1, e2 = rng.randint(-100, 100), rng.randint(-100, 100)
            if div:
                x, y = q_pack(False, m1 * m2, e1), q_pack(False, m2, e2)
            else:
                x, y = q_pack(False, m1, e1), q_pack(False, m2, e2)
        a.append(q_neg(x, rng)), b.append(q_neg(y, rng))
    if div:
        a[:2], b[:2] = [q_from(1), 0], [0, 0]
    return a, b


def gen_maker(rng):
    from mpmath import mp, mpf
    mp.dps = 80
    a, b = [], []
    year = 365 * 86400
    for i in range(N):
        kind = i % 4
        if kind == 0:      # per-second rates (the DSR, the stability fee): 1e-6 to 1,000% a year, up to 2^32 s
            apy = mpf(10) ** rng.uniform(-6, 1)
            x = int(mp.nint((1 + apy) ** (mpf(1) / year) * RAY))
            n = lu(rng, 1, 32)
        elif kind == 1:    # per-period rates: up to 100% a period, to 10,000 periods
            x = RAY + lu(rng, 1, 90) % RAY
            n = rng.randint(0, 10000)
        elif kind == 2:    # any base (10^-27 to about 3 10^11), small powers
            x = lu(rng, 1, 128)
            n = rng.randint(0, 40)
        else:              # near one, long powers (to zero and to overflow)
            x = RAY + sg(rng, lu(rng, 0, 70))
            n = lu(rng, 1, 64)
        a.append(x), b.append(n)
    a[:5], b[:5] = [0, 0, RAY, RAY + 1, RAY], [0, 5, (1 << 255), 1, 7]
    return a, b


# input set -> (generator, scale label)
SETS_NEW = {
    "abdk_exp": lambda r: gen_abdk_exp(r, "e"), "abdk_exp2": lambda r: gen_abdk_exp(r, "2"),
    "abdk_ln": lambda r: gen_abdk_log(r, "e"), "abdk_log2": lambda r: gen_abdk_log(r, "2"),
    "abdk_sqrt": gen_abdk_sqrt, "abdk_mul": gen_abdk_mul, "abdk_div": gen_abdk_div, "abdk_pow": gen_abdk_pow,
    "q_exp": lambda r: gen_q_exp(r, "e"), "q_exp2": lambda r: gen_q_exp(r, "2"),
    "q_ln": lambda r: gen_q_log(r, "e"), "q_log2": lambda r: gen_q_log(r, "2"),
    "q_sqrt": gen_q_sqrt, "q_mul": lambda r: gen_q_mul(r, False), "q_div": lambda r: gen_q_mul(r, True),
    "maker_rpow": gen_maker,
}
WAD_SETS = list(wad.GENS)   # mul div smul sdiv sqrt cbrt exp ln log2 log10 pow w0


# ---- the typical sets: normal inputs, the grade ----------------------------
# wad.py's typical ranges (exp of -10..10, ln and the logs of 0.001..1000, pow
# of 0.5..2 to -3..3, products and quotients of amounts up to 10^9 tokens by
# 0.01..100, roots of 0.001..10^9, Lambert W of -0.25..10), TN inputs per
# function: uniform and log-uniform over the range, and a quarter near a unit
# boundary inside it (results near a whole number of units, exact cases).

TN = int(os.environ.get("LOST_TN", 100000))


def ur(rng, lo, hi):
    return rng.randint(lo, hi)


def lur(rng, lo, hi):
    """Log-uniform integer in [lo, hi] (lo >= 1)."""
    v = int(math.exp(rng.uniform(math.log(lo), math.log(hi))))
    return min(max(v + rng.getrandbits(max(v.bit_length() - 53, 0)), lo), hi)


def typ_fixed(rng, maths, S):
    """Typical inputs for a fixed-point format with scale S (10^18 or 2^64)."""
    from mpmath import mp, mpf, log, exp, lambertw
    mp.dps = 120
    a, b = [], []
    for i in range(TN):
        kind = i % 4
        x = y = 0
        if maths in ("mul", "smul", "div", "sdiv"):
            amax, blo, bhi = 10**9 * S, S // 100, 100 * S
            if kind == 0:
                x, y = ur(rng, 1, amax), ur(rng, blo, bhi)
            elif kind == 1:
                x, y = lur(rng, 1, amax), lur(rng, blo, bhi)
            elif kind == 2:
                x, y = lur(rng, 1, amax), ur(rng, blo, bhi)
            elif maths in ("mul", "smul"):   # the product near a multiple of S
                y = ur(rng, blo, bhi)
                m = lur(rng, 1, amax) * y // S
                x = min(max((m * S + rng.choice((-1, 0, 1))) // y + rng.choice((0, 1)), 1), amax)
            else:                            # x S / y near a whole number of units
                x = lur(rng, 1, amax)
                q = lur(rng, max(x // 100, 1), 100 * x)
                y = min(max(x * S // q + rng.choice((0, 1)), blo), bhi)
            if maths in ("smul", "sdiv"):
                x, y = sg(rng, x), sg(rng, y)
        elif maths in ("sqrt", "cbrt"):
            lo, hi = S // 1000, 10**9 * S
            if kind == 0:
                x = ur(rng, lo, hi)
            elif kind == 1:
                x = lur(rng, lo, hi)
            else:                            # exact roots (x = t^2 or t^3 in units: S is a square / cube) and one either side
                if S == W:
                    t = lur(rng, math.isqrt(lo) + 1, math.isqrt(hi)) if maths == "sqrt" else lur(rng, 10**5, 10**9)
                    x = (t * t if maths == "sqrt" else t ** 3) + rng.choice((-1, 0, 0, 1))
                else:
                    t = lur(rng, math.isqrt(lo) + 1, math.isqrt(hi))
                    x = t * t + rng.choice((-1, 0, 0, 1))
        elif maths in ("exp", "exp2"):
            lg = (lambda v: log(v)) if maths == "exp" else (lambda v: log(v, 2))
            bound = 10 * S
            if kind in (0, 1):
                x = ur(rng, -bound, bound)
            elif kind == 2:                  # |x| log-uniform from one unit
                x = sg(rng, lur(rng, 1, bound))
            else:                            # the result near a whole number of units
                lo_r = (exp(mpf(-10)) if maths == "exp" else mpf(2) ** -10) * S
                hi_r = (exp(mpf(10)) if maths == "exp" else mpf(2) ** 10) * S
                k = lur(rng, int(lo_r) + 1, int(hi_r))
                x = max(min(int(mp.nint(lg(mpf(k) / S) * S)) + rng.choice((-1, 0, 1)), bound), -bound)
        elif maths in ("ln", "log2", "log10"):
            lo, hi = S // 1000, 1000 * S
            if kind == 0:
                x = ur(rng, lo, hi)
            elif kind == 1:
                x = lur(rng, lo, hi) if rng.random() < 0.7 else S + sg(rng, lu(rng, 0, 59))
            elif kind == 2:                  # the log near a whole number of units
                base = {"ln": mp.e, "log2": mpf(2), "log10": mpf(10)}[maths]
                span = int(log(mpf(1000), base) * S)
                k = rng.randint(-span, span)
                x = int(mp.nint(base ** (mpf(k) / S) * S)) + rng.choice((-1, 0, 1))
            else:                            # exact cases in range
                if maths == "log10" and S == W:
                    x = 10 ** (18 + rng.randint(-3, 3))
                else:
                    kk = rng.randint(-9, 9)
                    x = S << kk if kk >= 0 else S >> -kk
            x = min(max(x, lo), hi)
        elif maths == "pow":
            if kind in (0, 1):
                x, y = ur(rng, S // 2, 2 * S), ur(rng, -3 * S, 3 * S)
            elif kind == 2:                  # the result near a whole number of units
                x = ur(rng, S // 2, 2 * S)
                y0 = mpf(rng.uniform(-3, 3))
                k = int(mp.nint((mpf(x) / S) ** y0 * S))
                lx = log(mpf(x) / S)
                y = int(mp.nint(log(mpf(k) / S) / lx * S)) + rng.choice((-1, 0, 1)) if lx != 0 else 0
                y = max(min(y, 3 * S), -3 * S)
            else:                            # exact: halves, quarters, squares to halves, whole powers
                j = rng.randint(0, 2)
                if j == 0:
                    x, y = rng.choice((S // 2, 3 * S // 4, S, 5 * S // 4, 3 * S // 2, 2 * S)), rng.randint(-3, 3) * S
                elif j == 1:
                    t = ur(rng, math.isqrt(S // 2) + 1, math.isqrt(2 * S))
                    x, y = t * t if S == W else t * t, S // 2
                else:
                    x, y = ur(rng, S // 2, 2 * S), rng.choice((S, 2 * S, -S))
        elif maths == "w0":
            if kind in (0, 1):
                x = ur(rng, -S // 4, 10 * S)
            elif kind == 2:
                x = sg(rng, lur(rng, 1, S // 4), 0.3)
            else:                            # W(x) near a whole number of units: x = w e^w
                lo_w, hi_w = lambertw(mpf(-0.25)).real, lambertw(mpf(10)).real
                k = rng.randint(int(lo_w * S) + 1, int(hi_w * S))
                w = mpf(k) / S
                x = max(min(int(mp.nint(w * exp(w) * S)) + rng.choice((-1, 0, 1)), 10 * S), -S // 4)
        a.append(x), b.append(y)
    return a, (b if maths in ("mul", "smul", "div", "sdiv", "pow") else None)


def typ_abdk_pow(rng):
    """ABDK's pow takes a whole exponent: x in 0.5..2 to 0..3 (the typical
    -3..3 where it is defined)."""
    a, b = [], []
    for i in range(TN):
        if i % 4 == 3:
            x = rng.choice((Q64 // 2, 3 * Q64 // 4, Q64, 5 * Q64 // 4, 3 * Q64 // 2, 2 * Q64))
        else:
            x = ur(rng, Q64 // 2, 2 * Q64)
        a.append(x), b.append(rng.randint(0, 3))
    return a, b


def q_unif(rng, lo, hi):
    """A binary128 with a full random significand, uniform in [lo, hi]."""
    from mpmath import mp, mpf
    with mp.workprec(300):
        return q_from(mpf(lo) + (mpf(hi) - mpf(lo)) * mpf(rng.getrandbits(200)) / mpf(2) ** 200)


def q_logu(rng, lo, hi):
    from mpmath import mp, mpf, exp, log
    with mp.workprec(300):
        u = mpf(rng.getrandbits(200)) / mpf(2) ** 200
        return q_from(exp(log(mpf(lo)) + (log(mpf(hi)) - log(mpf(lo))) * u))


def typ_quad(rng, maths):
    from mpmath import mp, mpf, log, exp
    mp.prec = 300
    a, b = [], []
    for i in range(TN):
        kind = i % 4
        y = 0
        if maths in ("exp", "exp2"):
            if kind in (0, 1):
                x = q_unif(rng, -10, 10)
            elif kind == 2:                  # |x| log-uniform 2^-100..10
                x = q_neg(q_logu(rng, mpf(2) ** -100, 10), rng)
            else:                            # x = ln y for a binary128 y in range: the result near a representable value
                lo, hi = (exp(mpf(-10)), exp(mpf(10))) if maths == "exp" else (mpf(2) ** -10, mpf(2) ** 10)
                yv = q_val(q_logu(rng, lo, hi))[1]
                x = q_from(log(yv) if maths == "exp" else log(yv, 2))
        elif maths in ("ln", "log2"):
            if kind == 0:
                x = q_unif(rng, mpf(1) / 1000, 1000)
            elif kind == 1:
                x = q_logu(rng, mpf(1) / 1000, 1000)
            elif kind == 2:                  # near one
                k = rng.randint(1, 112)
                d = q_val(q_rand(rng, -k, -k))[1]
                x = q_from(1 + d if rng.random() < 0.5 else 1 - d)
            else:                            # powers of two in range
                x = q_pack(False, 1, rng.randint(-9, 9))
        elif maths == "sqrt":
            if kind == 0:
                x = q_unif(rng, mpf(1) / 1000, 10**9)
            elif kind == 1:
                x = q_logu(rng, mpf(1) / 1000, 10**9)
            else:                            # perfect squares in range and one place either side
                m = lu(rng, 1, 56)
                e = 2 * rng.randint(-4 - m.bit_length(), 14 - m.bit_length())
                x = q_pack(False, m * m, e)
                if kind == 3:
                    x += rng.choice((-1, 1))
        else:                                # mul, div: amounts up to 10^9 by 0.01..100
            if kind == 0:
                x, y = q_unif(rng, 0, 10**9), q_unif(rng, mpf(1) / 100, 100)
            elif kind == 1:
                x, y = q_logu(rng, mpf(10) ** -18, 10**9), q_logu(rng, mpf(1) / 100, 100)
            elif kind == 2:
                x, y = q_logu(rng, 1, 10**9), q_unif(rng, mpf(1) / 100, 100)
            else:                            # exact products and quotients of short significands in range
                m2 = lu(rng, 1, 30)
                m1 = lu(rng, 1, 26)
                e2 = rng.randint(-5 - m2.bit_length(), 6 - m2.bit_length())
                mx = m1 * m2 if maths == "div" else m1
                e1 = rng.randint(-10 - mx.bit_length(), 29 - mx.bit_length())
                x = q_pack(False, mx, e1)
                y = q_pack(False, m2, e2)
            x, y = q_neg(x, rng), q_neg(y, rng)
        a.append(x), b.append(y)
    return a, (b if maths in ("mul", "div") else None)


def typ_maker(rng):
    """Per-second rates up to 67.7% APR (the largest seen live), over up to
    one year of seconds."""
    from mpmath import mp, mpf
    mp.dps = 60
    year = 365 * 86400
    a, b = [], []
    for i in range(TN):
        apr = rng.uniform(0, 0.677) if i % 2 == 0 else 10 ** rng.uniform(-6, math.log10(0.677))
        x = RAY + int(mp.nint(mpf(apr) / year * RAY))
        n = rng.randint(1, year) if i % 4 < 2 else lur(rng, 1, year)
        a.append(x), b.append(n)
    return a, b


def typ_sets():
    t = {}
    for m in WAD_SETS:
        t[m] = typ_fixed(random.Random(f"{SEED}-lost-typ-{m}"), m, W)
    for s in ("exp", "exp2", "ln", "log2", "sqrt", "mul", "div"):
        t[f"abdk_{s}"] = typ_fixed(random.Random(f"{SEED}-lost-typ-abdk-{s}"), s, Q64)
    t["abdk_pow"] = typ_abdk_pow(random.Random(f"{SEED}-lost-typ-abdk-pow"))
    for s in ("exp", "exp2", "ln", "log2", "sqrt", "mul", "div"):
        t[f"q_{s}"] = typ_quad(random.Random(f"{SEED}-lost-typ-q-{s}"), s)
    t["maker_rpow"] = typ_maker(random.Random(f"{SEED}-lost-typ-maker"))
    return t


# ---- cells -----------------------------------------------------------------
# key -> dict(lib, fn, maths, set, expr, dir, out ("u", "s", "q"), fmt ("wad", "abdk", "q", "ray"), dom)

def bal_pow_dom(a, b):
    from mpmath import mp, mpf, log
    a, b = wad.s256(a), wad.s256(b)
    if a < 0 or b < 0 or b >= 2**254 // 10**20:
        return False
    if a == 0 or b == 0:
        return True
    with mp.workdps(60):
        lv = mpf(b) / W * log(mpf(a) / W)
    return -41 <= lv <= 130


NEW = {
    "bal_exp": dict(lib="balancer", fn="exp", maths="exp", call="LogExpMath.exp(x)", expr="BAL.exp(a)", dir=None, out="s",
                    dom=lambda a, b: -41 * W <= wad.s256(a) <= 130 * W, domtext="-41 <= x <= 130"),
    "bal_ln": dict(lib="balancer", fn="ln", maths="ln", call="LogExpMath.ln(x)", expr="BAL.ln(a)", dir=None, out="s",
                   dom=lambda a, b: wad.s256(a) > 0, domtext="x > 0"),
    "bal_log2": dict(lib="balancer", fn="log2", maths="log2", call="LogExpMath.log(x, 2e18)", expr="BAL.log(a, 2e18)", dir=None,
                     out="s", dom=lambda a, b: wad.s256(a) > 0, domtext="x > 0"),
    "bal_log10": dict(lib="balancer", fn="log10", maths="log10", call="LogExpMath.log(x, 10e18)", expr="BAL.log(a, 10e18)",
                      dir=None, out="s", dom=lambda a, b: wad.s256(a) > 0, domtext="x > 0"),
    "bal_pow": dict(lib="balancer", fn="pow", maths="pow", call="LogExpMath.pow(x, y)", expr="int256(BAL.pow(uint256(a), uint256(b)))",
                    dir=None, out="u", dom=bal_pow_dom, domtext="0 <= x < 2^255, 0 <= y < 2^254 / 1e20, -41 <= y ln x <= 130"),
    "bal_mulDown": dict(lib="balancer", fn="mulDown", maths="mul", call="FixedPoint.mulDown(a, b) = a * b / 1e18",
                        expr="int256(uint256(a) * uint256(b) / 1e18)", dir=0, out="u"),
    "bal_divDown": dict(lib="balancer", fn="divDown", maths="div", call="FixedPoint.divDown(a, b) = a * 1e18 / b",
                        expr="int256(uint256(a) * 1e18 / uint256(b))", dir=0, out="u"),
}
for f, s, e, d in (("exp", "abdk_exp", "A.exp(int128(a))", None), ("exp_2", "abdk_exp2", "A.exp_2(int128(a))", None),
                   ("ln", "abdk_ln", "A.ln(int128(a))", None), ("log_2", "abdk_log2", "A.log_2(int128(a))", None),
                   ("sqrt", "abdk_sqrt", "A.sqrt(int128(a))", 0), ("mul", "abdk_mul", "A.mul(int128(a), int128(b))", 0),
                   ("div", "abdk_div", "A.div(int128(a), int128(b))", 2), ("pow", "abdk_pow", "A.pow(int128(a), uint256(b))", None)):
    NEW[f"abdk_{f}"] = dict(lib="abdk", fn=f, maths=s[5:], set=s, call=f"ABDKMath64x64.{f}", expr=f"int256({e})", dir=d, out="s")
for f, s in (("exp", "q_exp"), ("pow_2", "q_exp2"), ("ln", "q_ln"), ("log_2", "q_log2"), ("sqrt", "q_sqrt"), ("mul", "q_mul"),
             ("div", "q_div")):
    args = "QB(a), QB(b)" if s in ("q_mul", "q_div") else "QB(a)"
    NEW[f"q_{f}"] = dict(lib="quad", fn=f, maths=s[2:], set=s, call=f"ABDKMathQuad.{f}",
                         expr=f"int256(uint256(uint128(Q.{f}({args}))))", dir=3, out="q")
NEW["mk_rpow"] = dict(lib="maker", fn="rpow", maths="rpow", set="maker_rpow", call="rpow(x, n, 1e27) (Solady = DSS _rpow)",
                      expr="int256(S.rpow(uint256(a), uint256(b), 1e27))", dir=3, out="u",
                      dom=lambda a, b: RAY <= a <= 2 * RAY,
                      domtext="the documented use: x = 1 + rate, 0 <= rate <= 1 (per second or per period), any n")
NEW["mk_rpow_any"] = dict(NEW["mk_rpow"], fn="rpow (any base)", dom=None, domtext="any x, n")
for k, c in NEW.items():
    c.setdefault("set", c["maths"])
    c.setdefault("dom", None)
    c["fmt"] = "abdk" if c["lib"] == "abdk" else "q" if c["lib"] == "quad" else "ray" if c["lib"] == "maker" else "wad"


def cells():
    """Every bench cell: wad.py's (its own calls and directions) and the new ones."""
    out = {}
    for k, lib, f, e, dom in wad.bench_cells():
        maths, _, kind, dflt = wad.FUNCS[f]
        d = dflt if lib == "blockulator" else wad.COMP[lib][f][1]
        call = wad.COMP[lib][f][0] if lib in wad.COMP else f"BlockulatorWad.{f}"
        out[k] = dict(lib=lib, fn=f, maths=maths, set=maths, expr=e, wdom=dom, dir=d, out=kind, fmt="wad", call=call,
                      dom=None, wad=True)
    for k, c in NEW.items():
        out[k] = dict(c, wad=False)
    return out


# ---- the bench -------------------------------------------------------------

IMPORTS = """import {LogExpMath as BAL} from "../../contracts/src/ladder/vendor/balancer/LogExpMath.sol";
import {ABDKMath64x64 as A} from "../../lib/abdk-libraries-solidity/ABDKMath64x64.sol";
import {ABDKMathQuad as Q} from "../../lib/abdk-libraries-solidity/ABDKMathQuad.sol";

function QB(int256 x) pure returns (bytes16) { return bytes16(uint128(uint256(x))); }
"""


def write_inputs():
    """cache/sweep/lost_<set>_<chunk>.json: every input set in chunks of CHUNK."""
    D.mkdir(parents=True, exist_ok=True)
    wad.N = N
    sets = {}
    for m in WAD_SETS:
        sets[m] = wad.GENS[m](random.Random(f"{SEED}-{m}"))
    for s, g in SETS_NEW.items():
        sets[s] = g(random.Random(f"{SEED}-lost-{s}"))
    for s, ab in typ_sets().items():
        sets[f"typ_{s}"] = ab
    for p in D.glob("lost_*.json"):
        p.unlink()
    for s, (a, b) in sets.items():
        for c in range(0, len(a), CHUNK):
            wad.write(f"lost_{s}_{c // CHUNK}", a[c:c + CHUNK], None if b is None else b[c:c + CHUNK])
    (D / "lost_meta.json").write_text(json.dumps({"N": N, "CHUNK": CHUNK, "sets": {s: len(a) for s, (a, _) in sets.items()}}))
    return sets


def run_bench(sets):
    cs = cells()
    disp = []
    for k, c in cs.items():
        if c["wad"]:
            disp.append(wad.dispatch(k, c["expr"], c["wdom"], c["out"]))
        else:
            disp.append(f'        if (op == "{k}") {{ g0 = gasleft(); r = {c["expr"]}; g = gasleft(); }}')
    runs = []
    for k, c in cs.items():
        for sn in (c["set"], "typ_" + c["set"]):
            n = len(sets[sn][0])
            for j in range((n + CHUNK - 1) // CHUNK):
                runs.append(f'    function test_{k}_{"t" if sn.startswith("typ_") else "d"}{j}() public {{ this.runOne("lost_{sn}_{j}", "{k}"); }}')
    src = wad.BENCH.replace("// GENERATED by scripts/sweep/wad.py (make wad); removed after the run.",
                            "// GENERATED by scripts/sweep/lost.py; removed after the run.")
    src = src.replace('import {FullMath} from "../../contracts/src/ladder/vendor/uniswap/FullMath.sol";',
                      'import {FullMath} from "../../contracts/src/ladder/vendor/uniswap/FullMath.sol";\n' + IMPORTS)
    src = src.replace("contract WadBench is Test", "contract LostBench is Test")
    path = ROOT / "test" / "lost" / "LostBench.t.sol"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(src % {"disp": "\n".join(disp), "runs": "\n".join(runs)})
    for p in D.glob("wadbench_*_lost_*.out"):
        p.unlink()
    try:
        subprocess.run(["forge", "test", "--match-path", "test/lost/LostBench.t.sol", "-q"], cwd=ROOT, check=True)
    finally:
        if not os.environ.get("LOST_KEEP"):
            path.unlink()


# ---- truth -----------------------------------------------------------------

class Rev(Exception):
    pass


def exact(s, a, b):
    """The exact real value for input set s at (a, b), in the result's raw
    units (wei, 2^-64, RAY units; binary128 as the real value); Rev where it
    does not exist."""
    s = s[4:] if s.startswith("typ_") else s
    from mpmath import mp, mpf, exp, log, sqrt, cbrt, lambertw, power, ldexp
    mp.dps = 300
    if s in ("mul", "div", "sqrt", "cbrt"):
        pass
    elif s in WAD_SETS:
        a, b = wad.s256(a), wad.s256(b)
    if s == "mul" or s == "smul":
        return mpf(a * b) / W
    if s in ("div", "sdiv"):
        if b == 0:
            raise Rev
        return mpf(a * W) / b
    if s == "sqrt":
        return sqrt(mpf(a * W))
    if s == "cbrt":
        return cbrt(mpf(a * W * W))
    if s in ("exp", "ln", "log2", "log10", "pow", "w0"):
        t = mpf(a) / W
        if s == "exp":
            return exp(t) * W
        if s in ("ln", "log2", "log10"):
            if a <= 0:
                raise Rev
            return (log(t) if s == "ln" else log(t, 2) if s == "log2" else log(t, 10)) * W
        if s == "pow":
            if a < 0 or (a == 0 and b < 0):
                raise Rev
            if a == 0:
                return mpf(W) if b == 0 else mpf(0)
            lv = mpf(b) / W * log(t)
            if lv > 200:
                raise Rev
            return exp(lv) * W
        if a < -367879441171442321:
            raise Rev
        return lambertw(t, 0).real * W
    if s.startswith("abdk_"):
        a = wad.s256(a)
        m = s[5:]
        t = mpf(a) / Q64
        if m == "exp":
            return exp(t) * Q64
        if m == "exp2":
            return power(2, t) * Q64
        if m in ("ln", "log2"):
            if a <= 0:
                raise Rev
            return (log(t) if m == "ln" else log(t, 2)) * Q64
        if m == "sqrt":
            if a < 0:
                raise Rev
            return sqrt(mpf(a) * Q64)
        if m == "mul":
            return mpf(a * wad.s256(b)) / Q64
        if m == "div":
            b = wad.s256(b)
            if b == 0:
                raise Rev
            return mpf(a * Q64) / b
        if m == "pow":
            if a == 0:
                return mpf(Q64) if b == 0 else mpf(0)
            if abs(t) != 1 and b * abs(float(log(abs(t)))) > 200:
                if abs(t) > 1:
                    raise Rev
                return mpf(0)
            return power(t, b) * Q64
    if s.startswith("q_"):
        mp.prec = 1000
        m = s[2:]
        ka, x = q_val(a)
        if ka != "num":
            raise Rev
        if m == "exp":
            return exp(x)
        if m == "exp2":
            return power(2, x)
        if m in ("ln", "log2"):
            if x <= 0:
                raise Rev
            return log(x) if m == "ln" else log(x, 2)
        if m == "sqrt":
            if x < 0:
                raise Rev
            return sqrt(x)
        kb, y = q_val(b)
        if kb != "num":
            raise Rev
        if m == "mul":
            return x * y
        if y == 0:
            raise Rev
        return x / y
    if s == "maker_rpow":
        if a == 0:
            return mpf(RAY) if b == 0 else mpf(0)
        t = mpf(a) / RAY
        if b > 1 << 20:
            lv = b * log(t)
            if lv > 200:
                raise Rev
            return exp(lv) * RAY
        return power(t, b) * RAY
    raise ValueError(s)


def tjob(args):
    s, i, a, b = args
    try:
        return i, exact(s, a, b)
    except Rev:
        return i, None


# ---- scoring ---------------------------------------------------------------

G = {}   # fork-inherited: inputs, truths


def rnd(v, d):
    from mpmath import floor, ceil, nint
    if d == 0 or (d == 2 and v >= 0):
        return int(floor(v))
    if d == 1 or d == 2:
        return int(ceil(v))
    return int(nint(v))


def fits(c, v):
    if v is None:
        return False
    if c["fmt"] == "q":
        from mpmath import mpf, ldexp
        return abs(v) < ldexp(mpf(1), 16384) - ldexp(mpf(1), 16383 - 114)
    if abs(v) > 2**258:
        return False
    r = rnd(v, 3 if c["dir"] is None else c["dir"])
    if c["fmt"] == "abdk":
        return -I127 <= r < I127
    if c["out"] == "u":
        return 0 <= r < T256
    return -I255 <= r < I255


def rounded_ok(d, got, v, u=1):
    """Is the result got correctly rounded from the exact v, the unit being u
    (3 nearest, None faithful, 0 floor, 1 ceiling, 2 toward zero)? Compared
    on the values themselves, not on got - v (1 - 10^-30000 is 1 at 300
    digits). The slack is relative to the exact value (10^-250 of it, far
    above the oracle's 300 digits, far below a unit), so an exact case the
    oracle computes a hair off is not misrounded, and 10^-30000 rounded up
    to one unit is correct."""
    from mpmath import mpf
    got = mpf(got)
    eps = abs(v) * mpf(10) ** -250
    if d == 2:
        d = 0 if v >= 0 else 1
    if d == 3:
        return abs(got - v) <= u / 2 + eps
    if d is None:
        return got - u + eps < v < got + u - eps
    if d == 0:
        return got <= v + eps and v < got + u - eps
    return got - u + eps < v <= got + eps


def human(c, a, b):
    from mpmath import mpf, nstr
    fmt = c["fmt"]
    if fmt == "q":
        va = q_val(a)
        out = {"a_bits": "0x%032x" % a, "a": nstr(va[1], 40) if va[0] == "num" else va[0]}
        if c["set"] in ("q_mul", "q_div"):
            vb = q_val(b)
            out.update(b_bits="0x%032x" % b, b=nstr(vb[1], 40) if vb[0] == "num" else vb[0])
        return out
    if fmt == "ray":
        return {"x_raw": str(a), "x": nstr(mpf(a) / RAY, 40), "n": str(b)}
    signed = c["out"] == "s" and c["set"] not in ("mul", "div", "sqrt", "cbrt") or fmt == "abdk"
    if c["lib"] == "balancer" and c["set"] == "pow":
        signed = True
    sa = wad.s256(a) if signed or (c["set"] in WAD_SETS and c["set"] not in ("mul", "div", "sqrt", "cbrt")) else a
    scale = Q64 if fmt == "abdk" else W
    out = {"a_raw": str(sa), "a": nstr(mpf(sa) / scale, 40)}
    if c["set"] in ("mul", "div", "smul", "sdiv", "pow", "abdk_mul", "abdk_div", "abdk_pow"):
        sb = b if c["set"] in ("mul", "div") or c["set"] == "abdk_pow" else wad.s256(b)
        out.update(b_raw=str(sb), b=str(sb) if c["set"] == "abdk_pow" else nstr(mpf(sb) / scale, 40))
    return out


def sjob(job):
    """Score one cell over all the chunks of one of its input sets."""
    from mpmath import mp, mpf, log10, nstr
    mp.dps = 300
    k, sn = job
    c = G["cells"][k]
    a_all, b_all = G["inputs"][sn]
    tr = G["truth"][sn]
    outs = []
    j = 0
    while (D / f"wadbench_{k}_lost_{sn}_{j}.out").exists():
        outs += [ln.split()[0] for ln in (D / f"wadbench_{k}_lost_{sn}_{j}.out").read_text().splitlines()]
        j += 1
    n_in = len(a_all)
    if len(outs) != n_in:
        return job, {"error": f"{len(outs)} outputs for {n_in} inputs"}
    st = dict(n=0, valued=0, misrounded=0, revert_in_range=0, value_out_of_range=0, both_revert=0, outside_domain=0,
              reverts_outside_domain_value_fits=0)
    worst, wi, wgot, wv = mpf(-1), None, None, None
    rev_ex = None
    held = {H: None for H in HELD}     # H -> (worst digits held, input index, capacity)
    short = [0.0, None, None, None]    # short18: worst max(0, min(cap, 18) - held), input index, cap, held

    def hold(i, v, got):
        """Digits held (-log10 of the relative error; the format's full
        precision when exact; 0 for a revert where the value fits) at an input
        whose exact value the format holds to cap significant digits."""
        if v == 0 or abs(v) > 2**258:
            return
        cap = float(log10(abs(v) / (q_ulp(v) if c["fmt"] == "q" else 1)))
        if got is None:
            h = 0.0
        else:
            e = abs(mpf(got) - v)
            h = cap + math.log10(2) if e == 0 else float(-log10(e / abs(v)))
        sh = max(0.0, min(cap, 18.0) - h)
        if short[1] is None or sh > short[0]:
            short[:] = [sh, i, cap, h]
        for H in HELD:
            if cap >= H and (held[H] is None or h < held[H][0]):
                held[H] = (h, i, cap)
    for i in range(n_in):
        a, b, o = a_all[i], (b_all[i] if b_all else 0), outs[i]
        v = tr[i]
        if o == wad.DOM or (c["dom"] is not None and not c["dom"](a, b)):
            st["outside_domain"] += 1
            if o.startswith("R") and fits(c, v):
                st["reverts_outside_domain_value_fits"] += 1
            elif c["fmt"] == "q" and not o.startswith("R") and q_val(int(o, 16))[0] != "num" and fits(c, v):
                st["reverts_outside_domain_value_fits"] += 1
            continue
        st["n"] += 1
        ok = fits(c, v)
        if c["fmt"] == "q":
            kind, got = ("rev", None) if o.startswith("R") else q_val(int(o, 16))
            rev = kind != "num"
        else:
            rev = o.startswith("R")
            if not rev:
                raw = int(o, 16)
                got = raw if c["out"] == "u" else wad.s256(raw)
                if c["fmt"] == "abdk":
                    got = wad.s256(raw)
        if rev:
            if ok:
                hold(i, v, None)
                st["revert_in_range"] += 1
                rev_ex = rev_ex or human(c, a, b)
            else:
                st["both_revert"] += 1
            continue
        if not ok:
            st["value_out_of_range"] += 1
            continue
        st["valued"] += 1
        if c["fmt"] == "q":
            u = q_ulp(v)
            err = (got - v) / u
        else:
            err = mpf(got) - v
        good = rounded_ok(c["dir"], got, v, u if c["fmt"] == "q" else 1)
        ae = abs(err)
        if not good:
            st["misrounded"] += 1
        elif ae >= 1:      # correct, a hair under a unit (1 - 10^-30000 is 1 at 300 digits)
            ae = 1 - mpf(10) ** -200
        if ae > worst:
            worst, wi, wgot, wv = ae, i, got, v
        hold(i, v, got)
    row = {"lib": c["lib"], "function": c["fn"], "maths": c["maths"], "call": c["call"], "direction": DIRNAME[c["dir"]] if c["fmt"] != "q" else QDIR,
           "inputs_fed": n_in}
    row.update(st)
    if wi is not None:
        a, b = a_all[wi], (b_all[wi] if b_all else 0)
        row["worst_ulps"] = nstr(worst, 6) if worst >= 1 else "0.%09d" % int(mp.floor(worst * 10**9))
        cr = st["misrounded"] == 0
        row["correctly_rounded"] = cr
        row["digits_lost"] = 0.0 if cr or worst < 1 else round(float(log10(worst)), 1)
        row["worst_input"] = human(c, a, b)
        row["worst_got"] = nstr(wgot, 40) if c["fmt"] == "q" else str(wgot)
        row["worst_exact"] = nstr(wv, 45)
    else:
        row.update(worst_ulps=None, correctly_rounded=None, digits_lost=None, worst_input=None)
    if rev_ex:
        row["revert_in_range_example"] = rev_ex
    row["short18"] = None if short[1] is None else round(short[0], 1)
    row["short18_input"] = None if short[1] is None else dict(
        human(c, a_all[short[1]], b_all[short[1]] if b_all else 0),
        format_digits_at_value=round(short[2], 1), digits_held=round(short[3], 1))
    row["held_floor"] = {str(H): None if held[H] is None else round(held[H][0], 1) for H in HELD}
    row["held_floor_input"] = {str(H): None if held[H] is None else
                               dict(human(c, a_all[held[H][1]], b_all[held[H][1]] if b_all else 0),
                                    format_digits_at_value=round(held[H][2], 1)) for H in HELD}
    if c.get("domtext"):
        row["domain"] = c["domtext"]
    elif c.get("wdom"):
        row["domain"] = c["wdom"]
    return job, row


LIBLABEL = dict(wad.LABEL, balancer="Balancer LogExpMath + FixedPoint (v3)", abdk="ABDKMath64x64 (64.64)",
                quad="ABDKMathQuad (IEEE binary128)", maker="Maker rpow (RAY; Solady rpow = DSS _rpow)",
                bl127="BL127", bl19="BL19")
UNIT = {"blockulator": "1 wei (10^-18)", "solady": "1 wei", "prb": "1 wei", "prbud": "1 wei", "solmate": "1 wei", "oz": "1 wei",
        "uniswap": "1 wei", "snekmate": "1 wei", "balancer": "1 wei", "abdk": "2^-64",
        "quad": "2^(e-112) at the exact value's binade", "maker": "10^-27 (1 RAY unit)"}


def sweep_rows():
    j = json.loads((OUT / "sweep.json").read_text())
    rows = {}
    for r in j["rows"]:
        if r["lib"] not in ("bl127", "bl19") or "stage" in r:
            continue
        st = r.get("status", {})
        rows.setdefault(r["lib"], {})[r["op"]] = {
            "n": r.get("inputs", r["n"] + st.get("bothrev", 0) + st.get("gotrev", 0)),
            "worst_ulps": str(r["maxUlp"]), "digits_lost": 0.0, "correctly_rounded": r.get("misrounded", 1) == 0,
            "misrounded": r.get("misrounded"), "worst_input": None, "reverts_in_range": 0,
            "direction": "as each op states (nearest under BL127's tie rule, or the op's stated direction)",
            "source": "docs/benchmarks/sweep.json (make sweep, seed 20261020): 0 misrounded; every revert where the oracle reverts"}
    return rows


def score():
    meta = json.loads((D / "lost_meta.json").read_text())
    cs = cells()
    inputs = {}
    for s in meta["sets"]:
        a, b = [], []
        j = 0
        while (D / f"lost_{s}_{j}.json").exists():
            d = json.loads((D / f"lost_{s}_{j}.json").read_text())
            a += [int(x, 16) for x in d["a"]]
            b += [int(x, 16) for x in d.get("b", [])]
            j += 1
        inputs[s] = (a, b or None)
    t0 = time.time()
    ctx = mpc.get_context("fork")
    truth = {s: [None] * len(a) for s, (a, _) in inputs.items()}
    tasks = [(s, i, a[i], b[i] if b else 0) for s, (a, b) in inputs.items() for i in range(len(a))]
    with ctx.Pool(WORKERS) as pool:
        from mpmath import mp
        for n, (s, i, v) in enumerate(pool.imap_unordered(tjob2, tasks, chunksize=256)):
            truth[s][i] = None if v is None else mp.make_mpf(v)
            if n % 500000 == 0:
                print(f"truth {n:,}/{len(tasks):,} at {time.time() - t0:.0f}s", flush=True)
    print(f"truth done: {len(tasks):,} values in {time.time() - t0:.0f}s on {WORKERS} workers", flush=True)
    G.update(cells=cs, inputs=inputs, truth=truth)
    jobs = [(k, sn) for k, c in cs.items() for sn in ("typ_" + c["set"], c["set"])]
    with ctx.Pool(WORKERS) as pool:
        rows = dict(pool.map(sjob, jobs, chunksize=1))
    print(f"scored in {time.time() - t0:.0f}s", flush=True)

    def entry(r):
        out = {"n": r["n"], "worst_ulps": r["worst_ulps"], "digits_lost": r["digits_lost"],
               "worst_input": r["worst_input"], "reverts_in_range": r["revert_in_range"], "direction": r["direction"]}
        out.update({kk: r[kk] for kk in ("domain", "correctly_rounded", "misrounded", "valued",
                                         "value_out_of_range", "both_revert", "outside_domain",
                                         "reverts_outside_domain_value_fits", "worst_got", "worst_exact",
                                         "revert_in_range_example", "inputs_fed", "short18", "short18_input", "held_floor", "held_floor_input") if kk in r})
        return out

    libs = {}
    for (k, sn), r in rows.items():
        if "error" in r:
            raise SystemExit(f"{k} {sn}: {r['error']}")
    for k, c in cs.items():
        t, d = rows[(k, "typ_" + c["set"])], rows[(k, c["set"])]
        e = entry(t)
        e = {"call": t["call"], "maths": t["maths"], **e, "domain_worst": entry(d)}
        libs.setdefault(c["lib"], {})[c["fn"]] = e
    for lib, fns in sweep_rows().items():
        libs[lib] = fns
    doc = {"_doc": __doc__.strip(), "seed": SEED,
           "typical_inputs_per_function": TN, "domain_inputs_per_function": N,
           "note": (f"grade = worst digits lost over the typical set ({TN:,} seeded inputs per function in wad.py's typical "
                    f"ranges, a quarter or more of them near a unit boundary or an exact case inside the range; Maker's rates "
                    f"uniform and log-uniform only); domain_worst = the same over each "
                    f"function's whole documented domain ({N:,} per function = 10x wad.py's {wad.N:,}), for the notes"),
           "typical_ranges": TYPICAL, "versions": VERSIONS, "unit": UNIT, "libraries": {}}
    order = ["bl127", "bl19", "blockulator", "solady", "prb", "prbud", "solmate", "oz", "uniswap", "snekmate", "balancer",
             "abdk", "quad", "maker"]

    def worst(fns, pick):
        sc = {f: pick(r) for f, r in fns.items() if pick(r) and pick(r)["digits_lost"] is not None}
        wf = max(sc, key=lambda f: (sc[f]["digits_lost"], float(sc[f]["worst_ulps"] or 0)), default=None)
        return {"function": wf, "digits_lost": sc[wf]["digits_lost"], "worst_ulps": sc[wf]["worst_ulps"],
                "worst_input": sc[wf]["worst_input"]} if wf else None

    for lib in order:
        fns = libs.get(lib)
        if not fns:
            continue
        typ_rv = sorted(f for f, r in fns.items() if r["reverts_in_range"])
        dom_rv = sorted(f for f, r in fns.items() if r.get("domain_worst", {}).get("reverts_in_range"))
        doc["libraries"][lib] = {
            "label": LIBLABEL.get(lib, lib), "unit": UNIT.get(lib, "the op's last place (sweep.json)"),
            "grade": worst(fns, lambda r: r) if lib not in ("bl127", "bl19") else
            {"function": None, "digits_lost": 0.0, "note": "every op correctly rounded on every swept input (sweep.json); no typical-only run"},
            "reverts_in_range": sum(r["reverts_in_range"] for r in fns.values()),
            "reverts_in_range_functions": typ_rv,
            "domain_worst": worst(fns, lambda r: r.get("domain_worst")) if lib not in ("bl127", "bl19") else
            {"function": None, "digits_lost": 0.0, "note": "sweep.json covers each op's whole domain: 0 misrounded"},
            "domain_reverts_in_range": sum(r.get("domain_worst", {}).get("reverts_in_range", 0) for r in fns.values()),
            "domain_reverts_in_range_functions": dom_rv,
            **held_lib(lib, fns),
            "functions": fns}
    (OUT / "lost.json").write_text(json.dumps(doc, indent=1) + "\n")
    print("wrote docs/benchmarks/lost.json")
    for lib, L in doc["libraries"].items():
        g, w = L["grade"], L["domain_worst"]
        print(f"{lib:12s} grade {g['digits_lost']} ({g['function']}, {g.get('worst_ulps')})  revInRange {L['reverts_in_range']} {L['reverts_in_range_functions']}"
              f" | domain {w and w['digits_lost']} ({w and w['function']}, {w and w.get('worst_ulps')}) revInRange {L['domain_reverts_in_range']} {L['domain_reverts_in_range_functions']}")


HELD = (25, 14, 10)


def held_lib(lib, fns):
    """A library's held floor on the typical inputs: for each H, the worst
    digits held over its functions (where its format holds H digits)."""
    if lib in ("bl127", "bl19"):
        return {"short18": 0.0, "correctly_rounded": True,
                "short18_note": "from sweep.json: every op correctly rounded on every swept input",
                "held_floor": None,
                "held_floor_note": "not run on the typical set; every op correctly rounded on every swept input (sweep.json), "
                                   "so wherever the format holds H digits it holds them"}
    out, where = {}, {}
    for H in map(str, HELD):
        cand = [(r["held_floor"][H], f) for f, r in fns.items() if r.get("held_floor", {}).get(H) is not None]
        if not cand:
            out[H], where[H] = None, None
            continue
        h, f = min(cand)
        out[H], where[H] = h, {"function": f, "input": fns[f]["held_floor_input"][H]}
    sc = [(r["short18"], f) for f, r in fns.items() if r.get("short18") is not None]
    s18, sf = max(sc) if sc else (None, None)
    return {"short18": s18,
            "short18_where": {"function": sf, "input": fns[sf]["short18_input"]} if sf else None,
            "correctly_rounded": all(r["digits_lost"] in (0, 0.0) for r in fns.values() if r["digits_lost"] is not None),
            "held_floor": out, "held_floor_where": where}


def tjob2(args):
    s, i, a, b = args
    try:
        return s, i, exact(s, a, b)._mpf_    # the raw tuple: an unpickled mpf rounds to the receiver's precision
    except Rev:
        return s, i, None


TYPICAL = {"exp": "x in -10..10 (exp_2, pow_2 the same)", "ln, log2, log10": "x in 0.001..1000",
           "pow": "x in 0.5..2, y in -3..3 (ABDK's whole-exponent pow: 0..3; Balancer's unsigned pow: its y >= 0 half)",
           "mul": "a up to 10^9 by b in 0.01..100 (signed: either sign)", "div": "a up to 10^9 over b in 0.01..100",
           "sqrt, cbrt": "x in 0.001..10^9", "lambertW0": "x in -0.25..10",
           "rpow (Maker)": "1 + per-second rate, APR 0..67.7% (the largest seen live), n = 1 s..1 year"}


VERSIONS = {
    "solady": "acd959a", "prb-math": "29a3c06", "solmate": "89365b8", "snekmate": "908aa9c (vyper 0.4.3)",
    "abdk-libraries-solidity": "5e1e7c1", "openzeppelin": "v5.7.0 (vendored)", "uniswap": "v4-core v4.0.0 (vendored)",
    "balancer": "LogExpMath v3 (vendored, contracts/src/ladder/vendor/balancer)", "maker": "Solady acd959a rpow (= DSS _rpow)",
}


def main():
    t0 = time.time()
    if sys.argv[1:] != ["score"]:
        sets = write_inputs()
        print(f"inputs in {time.time() - t0:.0f}s", flush=True)
        run_bench(sets)
        print(f"forge done at {time.time() - t0:.0f}s", flush=True)
    score()
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

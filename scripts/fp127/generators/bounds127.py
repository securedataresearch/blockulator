#!/usr/bin/env python3
"""The error bounds behind FP127's rounding tests, measured (3.0).

    uv run scripts/fp127/generators/bounds127.py [n]     # n inputs per region (default 2000)

FP127's correctly rounded ops decide a word from a fast value V and a stated
bound err on its distance from the exact value: when V's bits below the
2^-128 grid lie more than err from the rounding boundary (nearmid, pow2t's
eb, pow2rt's eb, powu's eb, and from 3.0 rbad127), V and the exact value
round alike and the slower stage is skipped. Correct rounding of the fast
path rests on one claim per op and region: |V - exact| < err, in units of
V's last bit. This script recomputes V exactly as the Yul does (the integer
models of scripts/fp127/generators/precise_model.py and kernel192.py, which
mirror the Yul's arithmetic, and powum and cbrt's Newton step below) and the
exact value at 120 digits, and prints the largest error it sees next to the
err the Yul uses. A region whose largest ratio reaches 1 prints EXCEEDS and
the script exits 1; scripts/gates.py and CI run it beside FP19's bounds.py.

  op, region                 V (scale)                  err in the Yul (units of V's last bit)
  log2, ln, log10, one word  log2g, times ln 2 or        2^47 (nearmid's window, 2^-145): log2m
                             log10 2 by mulg (2^-192)    within 2^-160.5 (kernel192.py), the
                                                         mantissa's floor and mulg's
  log2, l2p                  l2p (2^-384)                2^85 (2^-299: one Newton step through
                                                         expk, precise_model.py)
  pow, pow2t                 2^t in one word (2^-192)    eb = ay 2^(e - 80) + 2^(e + 48) + 6:
                                                         covers this value's error and the double
                                                         word's together (both are measured)
  compound, pow2t            compt's 2^t (2^-192)        eb with ay = |k| 2^113 + 1
  compound, pow2rt           V = 2^e (1 + sh 2^-256)     eb = |k| 2^-42 + 3 units of sh's last bit
                                                         ((1 + |k|) 2^-299 relative)
  powu, 256-bit mantissa     am (2^(ae - 255))           4k + 16 (each product within 2^-255,
                                                         squarings double it: (k + 5) 2^-255)
  cbrt, word steps           cbrtw's Y                   exactly floor(cbrt z) (err 1: no error)
  cbrt, Newton step          y, one added (2^-128)       in [floor R, floor R + 3], R the root
                                                         (|y - (R + 1)| < 2)
  lambertW0, lambertWm1,     lwfin's w + v 2^-300        2^(2 msb|y| + msb|w| - 421) + |y| 2^-124
  lwfin                      (2^-300)                    + 16: Newton's y^2 |w| / (2 |1 + w|^3)
                                                         twice over, B's top word, the floors
  lambertW, near -1/e        lwbr's W = -1 +- q          6 (lwqs: y's floor, the kernel's 2^-256,
                             (2^-192)                    the floored products, about 5)
  erf, erfc, erfs            erfs (2^-192)               ERR_S = 3 2^44 (2^45.58): derived in
                                                         erf_model.py, 2^45.29 (exp2frac's 2^-146.7
                                                         times erf, the floors)
  erf, erfc, erfct           erfct (2^-192)              ERR_T = 2^20: derived 2^19.41 (e^(-x^2)'s
                                                         error times erfc(4), the certified fit)
  normCdf, erfs and erfct    erfc(y)/2 or 1 - it         ERR_S, ERR_T (y = x/sqrt 2 at 2^-192
                             (2^-192)                    and the halving: err/2 + 3.2 and + 1)
  sinh, cosh, one exp        V = (vh, vl) (2^-192)       2^20, the most over |x| <= 88 of 4 + vh / 2^43
                                                         (measured against the latter): two floors
                                                         and einvhalf's dropped bits (3), the
                                                         kernel's 2^-299 relative of e^|x| / 2
  tanh, kernel / expm1s      u / (u + 2) by divg         2: u within 1.1 below, slope <= 1/2, the
                                                         quotient's floor
  tanh, w                    (1 - w) / (1 + w) (2^-192)  3: w's floor through a slope <= 2, the
                                                         quotient's floor
  atanh, one word            log2g, times ln 2 / 2       2^47 (one log within 2^-145 scaled, or two)
  atanh, l2p                 atanhmid (2^-384)           2^137: ln 2 / 2 floored at 2^-256 under a
                                                         log2 of at most 129, two l2p (2^-299)

3.0, FP127E (rbadw, the fast paths' test, and rbadm127, the middle stages'):
  exp, exp2, exp10           2^n (1 + s) (2^-384)        2^(n + 73) + 1 (expk 2^-311.2, the
                                                         reduction 2^-376, v's floor; the Yul
                                                         takes 2^200, n <= 126)
  expm1, series              expm1s (2^-192)             2 (Horner's floors and truncations
                                                         under 1 + 1/k, damped by |x|/k)
  ln, log10, l2p             x384mul's product (2^-384)  2^135 (l2p's 2^-299 times c, c's
                                                         rounding at 2^-256 times |log2 x|)
  pow, middle near one       2^n (1 + s) (2^-384)        2^(n + 121) + 3 (|x - 1| < 2^-8, |y| >
                                                         2^14: mratio 2^-272.1 relative, t
                                                         within |t| 2^-271.9)
  pow, middle l2p            2^n (1 + s) (2^-384)        2^(n + 102) + 3 (l2p 2^-299, |y| <=
                                                         2^14.52 while |t| <= 131)
  powu, 512-bit mantissa     powus's ah (relative)       (3k + 2) 2^-510 relative (each product
                                                         3 2^-510, squarings double it; the last
                                                         stage below k = 2^16: no test)

Later phases add the regions of the tests they introduce (rbad127's err per
op). The models' agreement with the Yul is checked by the sweep (make sweep)
and the kernels' generators (kernel192.py --check, expk.py --check).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from mpmath import mp, mpf, log, power, cbrt as mcbrt, sinh as msinh, cosh as mcosh, tanh as mtanh, atanh as matanh, lambertw, erf as merf, erfc as merfc, ncdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import precise_model as P  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "fp19" / "generators"))
import mid254  # noqa: E402  FP19's mratio and wmul, which pow's middle stage imports
import erf_model as EM  # noqa: E402

mp.dps = 120
ONE = P.ONE
G = P.G
M256 = P.M256
H255 = P.H255

LN2_192 = 0xb17217f7d1cf79abc9e3b39803f2f6af40f343267298b62e      # fp127_ln's mulg constant
LOG10_2_192 = 0x4d104d427de7fbcc47c4acd605be48bc13569862a1e8f9a5  # fp127_log10's


class Meter:
    """Per region: inputs, the largest |V - exact|, the smallest err, and the
    largest |V - exact| / err (err varies with the input for pow and
    compound)."""

    def __init__(self):
        self.rows = {}

    def add(self, name, err, V, exact):
        e = abs(mpf(V) - exact)
        r = self.rows.setdefault(name, [0, mpf(0), mpf(err), 0.0])
        r[0] += 1
        r[1] = max(r[1], e)
        r[2] = min(r[2], mpf(err))
        r[3] = max(r[3], float(e / err))

    def report(self) -> bool:
        print(f"{'op, region':32} {'n':>6} {'max |V - exact|':>16} {'err (min)':>12}  {'max ratio':>9}")
        bad = False
        for name, (n, worst, err_min, ratio) in self.rows.items():
            flag = "" if ratio < 1 else "  EXCEEDS"
            bad |= ratio >= 1
            print(f"{name:32} {n:6d} {mp.nstr(worst, 6):>16} {mp.nstr(err_min, 6):>12}  {ratio:9.4f}{flag}")
        return bad


def rand_pos(rng, lo, hi):
    b = rng.randint(lo, hi)
    return rng.getrandbits(b) | (1 << b)


# ---------------------------------------------------------------------------
# the logs: the one-word value nearmid tests, and l2p
# ---------------------------------------------------------------------------

def logs(M: Meter, rng, n):
    W = mpf(2) ** 47
    for i in range(n):
        if i % 4 == 3:          # near one, both sides, at every scale
            X = ONE + rng.getrandbits(rng.randint(1, 120)) * rng.choice((1, -1))
        else:
            X = rand_pos(rng, 1, 254)
        if X <= 0 or X & (X - 1) == 0:
            continue
        x = mpf(X) / ONE
        v = P.log2g(X)
        M.add("log2, one word", W, v, log(x, 2) * G)
        M.add("ln, one word", W, P.mulg(v, LN2_192), log(x) * G)
        M.add("log10, one word", W, P.mulg(v, LOG10_2_192), log(x, 10) * G)
        if i % 4 == 0:
            M.add("log2, l2p", mpf(2) ** 85, P.l2p(X), log(x, 2) * mpf(2) ** 384)


# ---------------------------------------------------------------------------
# pow and compound: pow2t's eb, pow2rt's eb (precise_model.fastpow and
# fastcompound's inputs)
# ---------------------------------------------------------------------------

def pow_(M: Meter, rng, n):
    for i in range(n):
        X = rng.getrandbits(rng.randint(120, 136)) | 1
        Y = rng.getrandbits(rng.randint(60, 140))
        if i % 3 == 0:                         # near one with a large exponent
            X = ONE + rng.getrandbits(rng.randint(1, 100)) * rng.choice([1, -1])
            Y = rng.getrandbits(rng.randint(128, 200))
        Y = -Y if rng.random() < 0.5 else Y
        if X <= 0 or X == ONE:
            continue
        t = (Y * P.log2g(X)) >> 128
        if abs(t) >= 1 << 198:
            continue
        r, ok, v, eb = P.pow2t(t, abs(Y))
        if v is None:                          # out of pow2t's reach: the double word decides
            continue
        truth = power(mpf(X) / ONE, mpf(Y) / ONE) * G
        pre = P.pow_pre(X, Y)
        # both values' true errors, together under eb
        M.add("pow, pow2t (both values)", eb, abs(mpf(v) - truth) + (abs(mpf(pre) - truth) if pre is not None else 1), 0)


def compound(M: Meter, rng, n):
    for i in range(n):
        rate = rng.getrandbits(rng.randint(40, 127)) * rng.choice([1, 1, -1])
        if i % 5 == 0:
            rate = rng.getrandbits(rng.randint(100, 135))
        k = rng.randint(16, 1 << rng.randint(5, 31)) * rng.choice([1, 1, -1])
        X = ONE + rate
        if X <= 0 or X >= 1 << 255:
            continue
        t = k * P.log2g(X)
        if abs(t) >= 1 << 199:                 # decided by t's sign and size alone
            continue
        truth = power(mpf(X) / ONE, k) * G
        r, ok, v, eb = P.pow2t(t, (abs(k) << 113) + 1)
        if v is not None:
            M.add("compound, pow2t", eb, v, truth)
        r2, ok2, V, eb2, unit = P.pow2rt(k << 128, P.l2p(X), (abs(k) >> 42) + 3)
        if V is not None:
            M.add("compound, pow2rt", eb2, V / unit, truth / G * mpf(2) ** 129 / unit)


# ---------------------------------------------------------------------------
# powu: the 256-bit mantissa's bound (powum, as the Yul runs it)
# ---------------------------------------------------------------------------

def mant(a, b):
    """The Yul's mant: the top 256 bits of a b, renormalised, and the carry."""
    p = a * b
    c = p >> 511
    return (p >> 256 if c else p >> 255) & M256, c


def divu(a, b):
    assert a >> 128 < b
    return (a << 128) // b


def powum(ux, k, recip):
    """The Yul's powum: |x|^k (or ^-k) as am 2^(ae - 255), am in [2^255, 2^256)."""
    s = ux.bit_length() - 1
    m = ux << (255 - s)
    e = s - 128
    am, ae = H255, 0
    while True:
        if k & 1:
            am, c = mant(am, m)
            ae += e + c
        k >>= 1
        if not k:
            break
        m, c = mant(m, m)
        e = 2 * e + c
    if recip:
        if am == H255:
            ae = -ae
        else:
            qh = divu(H255, am)
            ql = divu((-(qh * am)) & M256, am)
            am, ae = (qh << 128) | ql, -ae - 1
    return am, ae


def powu(M: Meter, rng, n):
    for i in range(n):
        ux = rand_pos(rng, 64, 200) if i % 2 else rand_pos(rng, 120, 136)
        k = rng.randint(2, 1 << rng.randint(1, 24))
        recip = rng.random() < 0.4
        am, ae = powum(ux, k, recip)
        x = mpf(ux) / ONE
        exact = power(x, -k if recip else k) * power(2, 255 - ae)
        M.add("powu, 256-bit mantissa", 4 * k + 16, am, exact)


# ---------------------------------------------------------------------------
# cbrt: the word steps and the Newton step, as the Yul runs them
# ---------------------------------------------------------------------------

def icbrt(N):
    """floor(N^(1/3)) exactly."""
    y = 1 << ((N.bit_length() + 2) // 3)
    while True:
        z = (2 * y + N // (y * y)) // 3
        if z >= y:
            break
        y = z
    while y ** 3 > N:
        y -= 1
    while (y + 1) ** 3 <= N:
        y += 1
    return y


def cbrt_steps(ax):
    """(Y, z, y, j): cbrtw's Y = floor(cbrt z) from the seed, and the Newton
    step's y (one added, before the exact step-down), as fp127_cbrt."""
    ms = ax.bit_length() - 1
    sh = 255 - ms
    sh -= (sh - 1) % 3
    z = ax << sh
    j = (256 - sh) // 3
    e = ms + sh - 253
    l = 0xbf5da1f0001eb537 + ((0x428a2f98d728ae22 * (z >> (189 + e))) >> 64)
    y = (l * ((0x80000000000000006597fa94f5b8f20b50a28be635ca2b89 >> (e << 6)) & 0xffffffffffffffff)) >> 42
    for _ in range(4):
        y = (2 * y + z // (y * y)) // 3
    y -= int(y * y > z // y)
    Y = y
    y2 = Y * Y
    y = (Y << j) + ((((z - y2 * Y) >> 2) << j) // ((3 * y2) >> 2)) + 1
    return Y, z, y, ax << 256


def cbrt_(M: Meter, rng, n):
    for i in range(n):
        ax = rand_pos(rng, 0, 254)
        if i % 8 == 0:                          # perfect cubes (N = (c 2^86)^3) and their neighbours
            c = rand_pos(rng, 0, 83)
            ax = min(max(4 * c ** 3 + rng.randint(-1, 1), 1), (1 << 255) - 1)
        Y, z, y, N = cbrt_steps(ax)
        M.add("cbrt, word steps", 1, Y, icbrt(z))
        M.add("cbrt, Newton step", 2, y, mcbrt(mpf(N)) + 1)


# ---------------------------------------------------------------------------
# the hyperbolics (FP127H): rbad127's err on each fast value, rbadm127's on
# atanh's l2p stage
# ---------------------------------------------------------------------------

def hyperbolics(M: Meter, rng, n):
    for i in range(n):
        # sinh and cosh: |x| log-uniform on [2^-65, 88], an eighth next to
        # m ln 2 (where expr's n is corrected)
        b = rng.randint(63, 134)
        ax = (rng.getrandbits(b) | (1 << b)) % (88 * ONE) + (1 << 63)
        if i % 8 == 0:
            ax = max(((rng.randint(1, 126) * P.LN2_512) >> 384) + rng.randint(-3, 3), 1 << 64)
        x = mpf(ax) / ONE
        for name, sign, fn in (("cosh", 1, mcosh), ("sinh", -1, msinh)):
            if name == "cosh" and ax < 1 << 64:
                continue
            V = P.hyp_pre(ax, sign)
            # against the derived 4 + vh / 2^43; the Yul's err is its maximum, 2^20
            assert P.hyp_err(V) <= P.HYP_ERR
            M.add(f"{name}, one exp (2^-192)", P.hyp_err(V), V, fn(x) * G)
        # tanh: |x| log-uniform in each region, [2^-65, 2^-5], (2^-5, 1/4)
        # and [1/4, 46)
        lo, hi = ((63, 123), (123, 126), (126, 134))[i % 3]
        ax = rng.getrandbits(rng.randint(lo, hi - 1)) | (1 << lo)
        ax = min(ax, 46 * ONE - 1)
        V, err, reg = P.tanh_pre(ax)
        M.add(f"tanh, {reg} (2^-192)", err, V, mtanh(mpf(ax) / ONE) * G)
        # atanh: |x| from 2^-68 to 1, a quarter within 2^-1..2^-127 of 1
        if i % 4 == 3:
            ax = ONE - (rng.getrandbits(rng.randint(1, 127)) | 1)
        else:
            b = rng.randint(60, 127)
            ax = rng.getrandbits(b) | (1 << b)
        t = matanh(mpf(ax) / ONE)
        M.add("atanh, one word (2^-192)", mpf(2) ** 47, P.atanh_pre(ax), t * G)
        if i % 4 == 0 or i % 4 == 3:
            M.add("atanh, l2p (2^-384)", mpf(2) ** 137, P.atanh_mid(ax), t * mpf(2) ** 384)


# ---------------------------------------------------------------------------
# Lambert W: lwfin's value against its err, lwbr's W near -1/e against 6
# units (precise_model.py's lw_w0, lw_wm1, lw_br and lw_fin, as the Yul)
# ---------------------------------------------------------------------------

LW_BP = -0x5267adbd9d4543376382ee923e4a59ec      # 1 + e x = 1/8: lwbr below, lwfin above
LW_MIN = -0x5e2d58d8b3bcdf1abadec7829054f90d     # -floor(2^128 / e), the smallest input


def lambert(M: Meter, rng, n):
    for i in range(n):
        c = i % 5
        br = -1 if c == 2 else rng.choice((0, -1)) if c > 2 else 0
        if c == 0:                              # W0, x > 0, |x| from 2^-65 to 2^127
            x = rand_pos(rng, 63, 254)
        elif c == 1:                            # W0, -0.32 < x < 0
            x = -rand_pos(rng, 63, 126)
        elif c == 2:                            # W-1, -0.32 < x < 0, down to -2^-128
            x = -rand_pos(rng, 0, 126)
        elif c == 3:                            # either branch, just above 1 + e x = 1/8
            x = LW_BP + rand_pos(rng, 0, 124)
        else:                                   # near -1/e, both branches, to the smallest input
            x = LW_MIN + rand_pos(rng, 0, 122)
        if x < LW_MIN or (br and x >= 0) or abs(x) < 1 << 63:
            continue
        W = lambertw(mpf(x) / ONE, br).real
        if x < LW_BP:
            q, _ = P.lw_br(P.lw_q(x), 1 if br else 0)
            M.add("lambertW, near -1/e, W at 2^-192", 6, q, abs(1 + W) * G)
            continue
        w, _ = (P.lw_wm1(x) if br else P.lw_w0(x))
        _, v, err = P.lw_fin(x, w)
        M.add(f"lambertW{'m1' if br else '0'}, lwfin (2^-300)", err, w * mpf(2) ** 172 + v, W * mpf(2) ** 300)


# ---------------------------------------------------------------------------
# 3.0, FP127E: the exponentials' fast value, expm1's series, the logs' and
# pow's middle values, powu's last stage
# ---------------------------------------------------------------------------

def v384(n, s):
    """floor(2^(n + 384) (1 + s 2^-512)): the value whose low word the
    exponentials' and pow's tests read (s as expk gives it, n >= -130)."""
    return (1 << (n + 384)) + (s >> (128 - n))


def exps(M: Meter, rng, n):
    with mp.workdps(220):
        for i in range(n):
            X = rand_pos(rng, 60, 134) * rng.choice((1, -1))
            if X > 88 * ONE or X < -89 * ONE:
                continue
            k, rh, rx = P.expr(X)
            if k >= -129:
                M.add("exp, double word", mpf(2) ** (k + 73) + 1, v384(k, P.expkx(rh, rx)), mp.exp(mpf(X) / ONE) * mpf(2) ** 384)
            if -129 * ONE <= X < 127 * ONE:
                k = X >> 128
                s = P.expkx(*P.lnmul(((X << 128) & M256) << 256))
                M.add("exp2, double word", mpf(2) ** (k + 73) + 1, v384(k, s), mpf(2) ** (mpf(X) / ONE + 384))
            X = X % (38 * ONE) if X > 0 else -((-X) % (38 * ONE))
            k, f = P.y2nf(X, P.LOG2_10_384)
            if -129 <= k <= 126:
                s = P.expkx(*P.lnmul(f))
                M.add("exp10, double word", mpf(2) ** (k + 73) + 1, v384(k, s), mpf(10) ** (mpf(X) / ONE) * mpf(2) ** 384)


def sdiv(a, b):
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def expm1s(X):
    """The Yul's expm1s: e^x - 1 at 2^-192 for |x| <= 1/16 at 2^-128."""
    ax = abs(X)
    k = 27
    if ax < 1 << 122:
        k = 22
        for lim, kk in ((120, 18), (116, 14), (112, 11), (104, 8), (96, 6), (80, 5)):
            if ax < 1 << lim:
                k = kk
    xs = X << 64
    v = G
    for j in range(k, 1, -1):
        v = G + sdiv((xs * v) >> 192, j)
    return (xs * v) >> 192


def expm1(M: Meter, rng, n):
    for i in range(n):
        X = rand_pos(rng, 63, 123) * rng.choice((1, -1))
        M.add("expm1, series", 2, expm1s(X), mp.expm1(mpf(X) / ONE) * G)


def x384(L, c):
    """The Yul's x384mul before its rounding: (L's high word) c + floor(L's low word c / 2^256)."""
    return (L >> 256) * c + (((L & M256) * c) >> 256)


LN2_256R = 0xb17217f7d1cf79abc9e3b39803f2f6af40f343267298b62d8a0d175b8baafa2c
LOG10_2_256R = 0x4d104d427de7fbcc47c4acd605be48bc13569862a1e8f9a4c52f37935be631e6


def logs_mid(M: Meter, rng, n):
    for i in range(n):
        X = rand_pos(rng, 1, 254) if i % 3 else ONE + rng.getrandbits(rng.randint(1, 120)) * rng.choice((1, -1))
        if X <= 0 or X & (X - 1) == 0:
            continue
        L = P.l2p(X)
        x = mpf(X) / ONE
        M.add("ln, l2p", mpf(2) ** 135, x384(L, LN2_256R), log(x) * mpf(2) ** 384)
        M.add("log10, l2p", mpf(2) ** 135, x384(L, LOG10_2_256R), log(x, 10) * mpf(2) ** 384)


L2E = (mid254.L2E_H << 256) | mid254.L2E_L


def tnear(Mid, X, Y):
    """The Yul's tnear: (n, F) for t = y log2 x, x within 2^-8 of one."""
    sg = int(X < ONE)
    ad = abs(X - ONE)
    q = mid254.wmul(Mid.mratio(sg, ad << 128, 0), L2E)
    j = ad.bit_length()
    Z = ((q * ad) >> j) * abs(Y)
    k, f = Z >> (256 - j + 510), (Z >> (256 - j)) & ((1 << 510) - 1)
    F = f << 2
    if sg ^ (Y < 0):
        k = -k
        if F:
            k, F = k - 1, (1 << 512) - F
    return k, F


def pow_mid(M: Meter, rng, n):
    Mid = mid254.build()
    with mp.workdps(220):
        for i in range(n):
            if i % 2:
                X = ONE + (rng.getrandbits(rng.randint(1, 119)) | 1) * rng.choice((1, -1))
            else:
                X = rand_pos(rng, 100, 140)
                if abs(X - ONE) < 1 << 120:
                    continue
            x = mpf(X) / ONE
            t = mpf(rng.uniform(-130, 127)) if i % 4 else mpf(2) ** rng.uniform(-30, 3)
            Y = int(t / log(x, 2) * ONE)
            if not 0 < abs(Y) < 1 << 254:
                continue
            if abs(X - ONE) < 1 << 120 and abs(Y) > 1 << 142:
                k, F = tnear(Mid, X, Y)
                name, eb = "pow, middle near one", 121
            else:
                k, F = P.y2nf(Y, P.l2p(X))
                name, eb = "pow, middle l2p", 102
            if not -130 <= k <= 126:
                continue
            V = v384(k, P.expkx(*P.lnmul(F)))
            M.add(name, mpf(2) ** (k + eb) + 3, V, power(x, mpf(Y) / ONE) * mpf(2) ** 384)


def mant2(a, b):
    """The Yul's mant2: the top 512 bits of a b for 512-bit mantissas (the
    low-by-low product dropped), renormalised, and the carry."""
    ah, al, bh, bl = a >> 256, a & M256, b >> 256, b & M256
    p = ah * bh + ((ah * bl) >> 256) + ((al * bh) >> 256)
    c = p >> 511
    return (p if c else p << 1), c


def powus_m(ux, k, recip):
    """The Yul's powus before its rounding: (A, ae), x^k = A 2^(ae - 511)."""
    s = ux.bit_length() - 1
    m = ux << (255 - s) << 256
    e = s - 128
    if recip:
        if m == 1 << 511:
            e = -e
        else:
            m, e = (1 << 1023) // m, -e - 1
    a, ae = 1 << 511, 0
    while True:
        if k & 1:
            a, c = mant2(a, m)
            ae += e + c
        k >>= 1
        if not k:
            break
        m, c = mant2(m, m)
        e = 2 * e + c
    return a, ae


def powus(M: Meter, rng, n):
    with mp.workdps(260):
        for i in range(n // 4):
            ux = rand_pos(rng, 64, 200) if i % 2 else ONE + rng.getrandbits(rng.randint(1, 100))
            k = rng.randint(2, (1 << 16) - 1)
            recip = rng.random() < 0.4
            A, ae = powus_m(ux, k, recip)
            exact = power(mpf(ux) / ONE, -k if recip else k) * power(2, 511 - ae)
            M.add("powu, 512-bit mantissa", (3 * k + 2) * mpf(2) ** 512 / mpf(2) ** 510, A, exact)


# ---------------------------------------------------------------------------
# erf, erfc, normCdf: the value round64 rounds, against ERR_S and ERR_T
# ---------------------------------------------------------------------------

INV_SQRT2_192 = 0xb504f333f9de6484597d89b3754abe9f1d6f60ba893ba84d   # fp127_normCdf's mulg constant
G192 = 1 << 192


def erf_(M: Meter, rng, n):
    C = EM.source_tail()
    for i in range(n):
        # erfs: |x| <= 4 at every scale, half of them uniform on (0, 4]
        X = rand_pos(rng, 1, 129) if i % 2 else rng.randint(1, 4 * ONE)
        X = min(X, 4 * ONE)
        x = mpf(X) / ONE
        v, _ = EM.erf_series(X << 64)
        M.add("erf, erfc, erfs", EM.ERR_S, v, merf(x) * G192)
        # erfct: 4 < x < 9.375
        X = rng.randint(4 * ONE + 1, 0x960000000000000000000000000000000 - 1)
        x = mpf(X) / ONE
        M.add("erf, erfc, erfct", EM.ERR_T, EM.erfc_tail(X << 64, C), merfc(x) * G192)
        # normCdf: y <= 4 (|x| <= 5.66) by erfs, y > 4 (to |x| = 13.3125) by erfct
        X = rand_pos(rng, 1, 130) if i % 2 else rng.randint(1, 0x5a827999fcef32422cbec4d9baa55f4f9)
        yg = P.mulg(X << 64, INV_SQRT2_192)
        if yg <= 4 * G192:
            v = (G192 - EM.erf_series(yg)[0]) >> 1
            M.add("normCdf, erfs", EM.ERR_S, v, ncdf(-mpf(X) / ONE) * G192)
        X = rng.randint(0x5a827999fcef32422cbec4d9baa55f4fa, 0xd50000000000000000000000000000000 - 1)
        yg = P.mulg(X << 64, INV_SQRT2_192)
        if yg > 4 * G192:
            M.add("normCdf, erfct", EM.ERR_T, EM.erfc_tail(yg, C) >> 1, ncdf(-mpf(X) / ONE) * G192)


def run(n: int) -> bool:
    rng = random.Random(127)
    M = Meter()
    logs(M, rng, n)
    pow_(M, rng, n)
    compound(M, rng, n)
    powu(M, rng, n)
    cbrt_(M, rng, n)
    hyperbolics(M, rng, n)
    lambert(M, rng, n)
    exps(M, rng, n)
    expm1(M, rng, n)
    logs_mid(M, rng, n)
    pow_mid(M, rng, n)
    powus(M, rng, n)
    erf_(M, rng, n)
    bad = M.report()
    print(f"{sum(1 for r in M.rows.values() if r[3] >= 1)} regions over their bound")
    return bad


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    sys.exit(1 if run(n) else 0)

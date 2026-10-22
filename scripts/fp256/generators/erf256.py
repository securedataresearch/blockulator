#!/usr/bin/env python3
"""erf, erfc and normCdf for FP256 release three, modelled in exact integers as
the Yul runs them, with the anchor table and the Yul text it needs.

    uv run scripts/fp256/generators/erf256.py            # measure the three ops against mpmath
    uv run scripts/fp256/generators/erf256.py --yul      # print the anchor-table Yul

Everything is built on g(y) = e^(y^2) erfc(y), so erfc(y) = e^(-y^2) g(y) is a
product and never a difference:

  y < 1/2      erf(y) = (2/sqrt pi) y e^(-y^2) S, S = sum d^k / (2k+1)!!, d = 2y^2,
               summed until the term rounds to zero (about 40 terms); erfc = 1 - erf
               loses at most 1.6 bits there.
  1/2..6       the Taylor series of g around the nearest anchor y0 = j/8 (j = 4..48,
               |h| <= 1/16), its coefficients from g' = 2yg - 2/sqrt(pi):
               g_(n+1) = (2 y0 g_n + 2 g_(n-1)) / (n + 1), one stored constant g(y0)
               per anchor; products and the division rounded to nearest (truncation
               cost three bits through a bias), about 46 terms.
  6..16        the continued fraction erfc(y) = e^(-y^2) / (sqrt(pi) K),
               K = y + (1/2)/(y + 1/(y + (3/2)/(y + ...))), its convergents scaled by
               y^k so a step is X_k = X_(k-1) + (k / 2y^2) X_(k-2), the A and B pairs
               renormalised together below 2^252 by rounded shifts (B'/A'' = y/K < 1),
               to depth 4400 / floor(y^2) + 48 (measured: 262 bits of truncation).
  y >= 18      the asymptotic series erfc(y) = e^(-y^2)/(y sqrt pi) sum (-1)^m (1/2)_m / y^(2m)
               (DLMF 7.12.1), its terms at 2^-262 until one floors to zero, the
               remainder below the first omitted term: 76 terms at 18, 18 at 430.

e^(-y^2) comes from the exact 474-bit square of the significand times log2 e in
two words, so the deep tail keeps its bits: erfc(y) for y up to about 427 and
normCdf(x) for x down to about -603, where they underflow 2^-262142.
"""
from __future__ import annotations

import random
import sys

from mpmath import mp, mpf, erf as merf, erfc as merfc, ncdf, exp, sqrt, pi, log, floor, nint

sys.path.insert(0, __import__("os").path.dirname(__file__))
import kernel254 as K  # noqa: E402

W = 254
WS = 1 << W
MASK = (1 << 256) - 1
BIAS = K.BIAS
ONE = BIAS << 236
GS = 255
ANCHORS = range(4, 49)
CF_SCALE = 251


def qs(v, s):
    return int(floor(v * mpf(2) ** s))


mp.dps = 120
C2_254 = qs(2 / sqrt(pi), 254)                # 2/sqrt(pi) at 2^-254, the erf constant
C2_255 = qs(2 / sqrt(pi), 255)                # at 2^-255 for g1 (above 2^255: unsigned)
SQRTPI = qs(sqrt(pi), 254)
RSQRT2 = qs(1 / sqrt(mpf(2)), 255)            # 1/sqrt 2 at 2^-255
GTAB = {j: qs(exp(mpf(j) ** 2 / 64) * merfc(mpf(j) / 8), GS) for j in ANCHORS}


def mulwu(a, b):
    return (a * b) >> W


def signed(w):
    return w - (1 << 256) if w >> 255 else w


def mulwr(a, b):
    """round(a b / 2^254) on signed values (Python ints)."""
    return (a * b + (1 << (W - 1))) >> W


def rdiv(a, n):
    """a / n rounded to nearest, ties away from zero, for a signed a and n > 0."""
    return (a + n // 2) // n if a >= 0 else -((-a + n // 2) // n)


def rshr(a, s):
    return (a + ((1 << s) >> 1)) >> s if s > 0 else a


def expnegsq(ker, u, m, h):
    """e^(-x^2 / 2^h) for x = m 2^(u-236): (kk, v), value v 2^(kk - 254); None below 2^-2^19."""
    P = m * m
    # the two words the Yul keeps: floor(P LH / 2^256) + floor(P LL / 2^510)
    qt = ((P * ker.LOG2E_HI) >> 256) + ((P * ker.LOG2E_LO) >> 510)
    s2 = 216 + h - 2 * u
    f = (qt >> s2) & (WS - 1) if s2 < 512 else 0
    k = qt >> (s2 + 254) if s2 + 254 < 512 else 0
    if k >= 1 << 19:
        return None
    return ker.exp2kv(1, k, f)


def erfser(d):
    """S = sum d^k / (2k+1)!! at 2^-254, d = 2y^2 at 2^-254, rounded steps."""
    term = WS
    s = WS
    k = 1
    while term:
        term = rdiv(mulwr(term, d), 2 * k + 1)
        s += term
        k += 1
    return s


def erfcxa(yfix):
    """g(y) at 2^-255 for y in [1/2, 4] given at 2^-254."""
    j = (yfix + (1 << (W - 4))) >> (W - 3)
    j = min(max(j, 4), 48)
    y0 = j << (W - 3)
    h = yfix - y0
    g0 = GTAB[j]
    g1 = 2 * mulwu(y0, g0) - C2_255
    pm, p = g0, mulwr(g1, h)
    s = g0 + p
    yh2 = 2 * mulwr(y0, h)
    h22 = 2 * mulwr(h, h)
    n = 1
    while p or pm:
        p, pm = rdiv(mulwr(yh2, p) + mulwr(h22, pm), n + 1), p
        s += p
        n += 1
    return s


def div254(a, b):
    return (a << 254) // b


def erfcxcf(Y, uy):
    """g(y) for y = Y 2^(uy - 254) > 4 as (R, e): g = R 2^(e - 254), R in [2^253, 2^255)."""
    Y2 = (Y * Y) >> 254                               # y^2 = Y2 2^(2uy - 254)
    ey = 2 * uy
    if Y2 >> 255:
        Y2 >>= 1
        ey += 1
    # floor(y^2) for the depth
    yint = Y2 >> (254 - ey) if ey <= 254 else Y2 << (ey - 254)
    n = 4400 // yint + 48
    w = (1 << (504 - ey)) // Y2                      # 1/(2 y^2) at 2^-251
    am = an = 1 << CF_SCALE
    bm, bn = 0, 1 << CF_SCALE
    ea = eb = 0
    for k in range(1, n + 1):
        c = k * w
        a2 = an + rshr(c * am, CF_SCALE)
        b2 = bn + rshr(c * bm, CF_SCALE)
        # one shift for both pairs: B'/A'' = y/K is just under one, so they stay level
        sa = max(0, a2.bit_length() - 1 - CF_SCALE)
        am, an, ea = rshr(an, sa), rshr(a2, sa), ea + sa
        bm, bn, eb = rshr(bn, sa), rshr(b2, sa), eb + sa
    YS = (Y * SQRTPI) >> 254                          # y sqrt(pi) = YS 2^(uy - 254)
    DN = (an * YS) >> 254                             # an YS / 2^254
    sb_ = 253 - (bn.bit_length() - 1)
    sd_ = 253 - (DN.bit_length() - 1)
    bn2 = bn << sb_ if sb_ >= 0 else bn >> -sb_
    DN2 = DN << sd_ if sd_ >= 0 else DN >> -sd_
    R = div254(bn2, DN2)
    # g = bn / (an y sqrt pi) 2^(eb - ea); y sqrt pi = YS 2^(uy-254) -> an YS = DN 2^254
    # g = (bn / DN) 2^(eb - ea - uy) = (R / 2^254) 2^(sd_ - sb_ + eb - ea - uy)
    return R, sd_ - sb_ + eb - ea - uy


def asym(Y, uy, v):
    """erfc(y) for y >= 18 by the asymptotic series, given e^(-y^2)'s v: (D, eg) with
    D in [2^255, 2^256), erfc = D 2^(eg + kk - 254), as the Yul's erfasym."""
    y2 = (Y * Y) >> 254
    ey = 2 * uy
    if y2 >> 255:
        y2 >>= 1
        ey += 1
    W1 = (1 << 508) // y2
    w254 = W1 >> (ey + 1)
    term = W1 >> (ey - 7)                      # w at 2^-262
    T = -term
    sign, mm = 1, 2
    while term:
        term = (term * ((2 * mm - 1) * w254)) >> 254
        T += sign * term
        sign, mm = -sign, mm + 1
    assert T <= 0
    Q = (1 << 510) // ((Y * SQRTPI) >> 254)
    SQ = Q - (((-T) * Q) >> 262)
    D = (SQ * v) >> 255
    t = 255 - (D.bit_length() - 1)
    return D << t, -uy - 1 - t





def asym_regime(Y, uy):
    """y >= 18: the asymptotic series is cheaper than the fraction there (measured)."""
    return uy > 4 or (uy == 4 and Y >= 9 << 251)


def ystuff(u, m, h):
    """y = |x| (h = 0) or |x|/sqrt 2 (h = 1) as y = Y 2^(uy - 254), Y in [2^254, 2^255)."""
    Y, uy = m << 18, u
    if h == 1:
        P = Y * RSQRT2
        Y1 = P >> 255
        if Y1 < WS:
            Y1, uy = P >> 254, u - 1
        Y = Y1
    return Y, uy


def yfix(Y, uy):
    """y at 2^-254 for y < 6 (a Python int; the Yul forms j and h without it)."""
    return Y >> -uy if uy <= 0 else Y << uy


def ge13(Y, uy):
    return uy >= 4 or (uy == 3 and Y >= 13 << 251)


def erfc_big(ker, Y, uy, u, m, h):
    """erfc(y) for y >= 1/2 as (D, ee), value D 2^(ee - 254); None when it underflows."""
    r = expnegsq(ker, u, m, h)
    if r is None:
        return None
    kk, v = r
    if uy <= 1 or (uy == 2 and Y < 3 << 253):         # 1/2 <= y < 6: the anchors
        g = erfcxa(yfix(Y, uy))
        return (g * v) >> 254, kk - 1
    if asym_regime(Y, uy):                            # y >= 18: the asymptotic series
        D, eg = asym(Y, uy, v)
        return D, kk + eg
    R, eg = erfcxcf(Y, uy)                            # y >= 6: the continued fraction
    return (R * v) >> 254, kk + eg


def tofix(val):
    if val is None:
        return 0
    D, ee = val
    return D >> -ee if ee <= 0 else D << ee


def erf_small(ker, u, m, h):
    """F with erf(y) = x F for y = |x| / sqrt(2^h) < 1/2, at 2^-254."""
    P = m * m
    sh = 217 + h - 2 * u                              # d = 2 y^2 at 2^-254
    d = P >> sh if sh < 600 else 0
    S = erfser(d)
    kk, v = expnegsq(ker, u, m, h)
    E = v >> -kk
    F = mulwr(mulwr(C2_254, E), S)
    if h == 1:
        F = (F * RSQRT2) >> 255
    return F


def erfc_mag(ker, u, m, h):
    """erfc(y), y = |x| / sqrt(2^h), as (D, ee) or None (underflow)."""
    Y, uy = ystuff(u, m, h)
    if uy <= -2:                                      # y < 1/2
        F = erf_small(ker, u, m, h)
        ef = (m * F) >> (236 - u)
        return WS - ef, 0
    return erfc_big(ker, Y, uy, u, m, h)


def model_erfc(ker, x):
    s, e, m = K.unpack(x)
    if e == 0:
        return ONE
    u = e - BIAS
    if u >= 10:
        return (BIAS + 1) << 236 if s else 0
    val = erfc_mag(ker, u, m, 0)
    if s:
        return K.normround(0, BIAS, 2 * WS - tofix(val))
    if val is None or val[0] == 0:
        return 0
    return K.normround(0, BIAS + val[1], val[0])


def model_erf(ker, x):
    s, e, m = K.unpack(x)
    if e == 0:
        return 0
    u = e - BIAS
    Y, uy = ystuff(u, m, 0)
    if ge13(Y, uy):
        return ONE | (s << 255)
    if uy <= -2:
        F = erf_small(ker, u, m, 0)
        return K.normround(s, BIAS + u, (m * F) >> 236)
    return K.normround(s, BIAS, WS - tofix(erfc_big(ker, Y, uy, u, m, 0)))


def model_normCdf(ker, x):
    s, e, m = K.unpack(x)
    HALF = (BIAS - 1) << 236
    if e == 0:
        return HALF
    u = e - BIAS
    if u >= 10:
        return 0 if s else ONE
    if not s:
        Y, uy = ystuff(u, m, 1)
        if ge13(Y, uy):
            return ONE
    val = erfc_mag(ker, u, m, 1)
    if s:
        if val is None or val[0] == 0:
            return 0
        return K.normround(0, BIAS + val[1] - 1, val[0])     # erfc(y) / 2
    return K.normround(0, BIAS - 1, 2 * WS - tofix(val))     # (2 - erfc(y)) / 2


K.Kernels.model_erf = model_erf
K.Kernels.model_erfc = model_erfc
K.Kernels.model_normCdf = model_normCdf


def bits(got, truth):
    g = K.decode(got)
    if g == truth:
        return 256.0
    if truth == 0:
        return 0.0
    return float(-log(abs(g - truth) / abs(truth), 2))


def measure(ker):
    mp.dps = 160
    rng = random.Random(256)
    pts = []
    for _ in range(300):
        pts.append(K.rand_float(rng, -12, 1))
    for _ in range(300):
        pts.append(K.encode(mpf(rng.random()) * 8 * (1 if rng.getrandbits(1) else -1)))
    for _ in range(150):
        pts.append(K.encode(mpf(4) + mpf(rng.random()) * 30))
    for _ in range(80):
        pts.append(K.encode(mpf(30) + mpf(rng.random()) * 400))
    for name, fn, truth in [("erf", model_erf, merf), ("erfc", model_erfc, merfc), ("normCdf", model_normCdf, ncdf)]:
        bs = []
        for x in pts:
            xv = K.decode(x)
            t = truth(xv)
            if t == 0:
                continue
            got = fn(ker, x)
            if got == 0 and K.encode(t) == 0:
                continue
            bs.append(bits(got, t))
        print(f"{name:8} n={len(bs):4} bits min {min(bs):7.2f} mean {sum(bs) / len(bs):7.2f}")


def emit_yul():
    out = ["/// g(j/8) = e^((j/8)^2) erfc(j/8) at 2^-255 for the anchors j = 4..32 (erf256.py).",
           "function erfcxg0(j) -> g {",
           "    switch j"]
    for j in ANCHORS:
        out.append(f"    case {j} {{ g := 0x{GTAB[j]:x} }}")
    out.append("    default { g := 0 }")
    out.append("}")
    out.append(f"// C2_254 0x{C2_254:x}\n// C2_255 0x{C2_255:x}\n// SQRTPI 0x{SQRTPI:x}\n// RSQRT2 0x{RSQRT2:x}")
    return "\n".join(out)


def main(argv):
    ker, _, _ = K.build()
    if "--yul" in argv:
        print(emit_yul())
        return 0
    measure(ker)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

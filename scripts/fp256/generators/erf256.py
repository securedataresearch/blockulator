#!/usr/bin/env python3
"""erf, erfc and normCdf for FP256 by the modified trapezoidal rule, modelled
in exact integers as the Yul runs them, with the node table and the Yul text
it needs.

    uv run scripts/fp256/generators/erf256.py            # measure the three ops against mpmath
    uv run scripts/fp256/generators/erf256.py --yul      # print the table Yul and the constants
    uv run scripts/fp256/generators/erf256.py --bound    # the theorem's bound for N and the crossovers

The method (Al Azah & Chandler-Wilde, arXiv:2010.05659, Theorem 1.1). For
z = iy the Faddeeva function is w(iy) = e^(y^2) erfc(y), and the modified
trapezoidal rule with N + 1 midpoint nodes t_k = (k + 1/2) h, h = sqrt(pi/(N+1)),

    e^(y^2) erfc(y) = (2hy/pi) sum_k e^(-t_k^2) / (y^2 + t_k^2)
                      + [y < pi/h] 2 e^(y^2) / (1 + e^(2 pi y/h)) + error,

with |error| / w(iy) <= 3.97 sqrt(N+1) e^(-pi N) for every y >= 0. Multiplied
by e^(-y^2):

    erfc(y) = e^(-y^2) y U(y) + P(y),   U = sum_k c_k / (y^2 + t_k^2),
    c_k = (2h/pi) e^(-t_k^2),            P = 2 / (1 + e^(2 pi y/h)),

all terms positive. N = 58 (59 terms) puts the truncation under 2^-258 of the
value; the pole term P is below 2^-259 of erfc from y = 12 and is dropped
there. erf = 1 - erfc above y = 1/2; below, erf = tanh(pi y/h) - e^(-y^2) y U
(the pole term is 1 - tanh), two quantities each about 14y whose difference,
1.13y, keeps relative precision: tanh from e^(2 pi y/h) - 1, which comes from
the exp2 kernel for y >= 2^-5 and from the core's expm1 series (|d| < 2^-8)
with doublings below. From y = 16 the asymptotic series (DLMF 7.12.1)
erfc(y) = e^(-y^2)/(y sqrt pi) sum_m (-1)^m (1/2)_m / y^(2m), stopped at the
first term that floors to zero at 2^-262 (the remainder is bounded by that
term), is cheaper. e^(-y^2) comes from the exact 474-bit square of the
significand times log2 e in two words (expnegsq), so the tail keeps its bits
until it underflows 2^-262142 near y = 427.

Per term the quotient c_k / (y^2 + t_k^2) is floor(c_k 2^255 / B), one
modular-inverse division (divh) of the table word c_k (normalised, its binary
exponent g_k = floor(t_k^2 log2 e) recomputed from (2k+1)^2 by one integer
product) by the denominator's top 256 bits B; the 59 quotients are summed in
two words at the first term's scale.
"""
from __future__ import annotations

import math
import random
import sys

from mpmath import mp, mpf, erf as merf, erfc as merfc, ncdf, exp, sqrt, pi, log, floor, tanh

sys.path.insert(0, __import__("os").path.dirname(__file__))
import kernel254 as K  # noqa: E402

W = 254
WS = 1 << W
M254 = WS - 1
MASK = (1 << 256) - 1
BIAS = K.BIAS
ONE = BIAS << 236

N = 58                      # the rule's N: 59 nodes
NT = N + 1
POLE_Y = 12                 # the pole term is dropped from y = 12 (below 2^-259 of erfc)
ASYM_UY = 4                 # the asymptotic series from y = 16
CSCALE = 258                # c_k 2^(258 + g_k): in [2^254.2, 2^255.2)
DSCALE = 502                # y^2 + t_k^2 at 2^-502, two words, below 2^511 for y < 16


def qs(v, s):
    return int(floor(v * mpf(2) ** s))


mp.dps = 160
H = sqrt(pi / NT)
CQ = pi / (4 * NT)                              # t_k^2 = (2k+1)^2 CQ
LOG2E = 1 / log(2)
LAMBDA = 2 * pi / H                             # 2 pi y / h = y LAMBDA
KAPPA = LAMBDA * LOG2E
CH, CL = divmod(qs(CQ, DSCALE), 1 << 256)       # CQ 2^502 as two words
G64 = qs(CQ * LOG2E, 64)
LH = qs(LAMBDA, 250)
LL = qs(LAMBDA, 504) & M254
KH = qs(KAPPA, 250)
KL = qs(KAPPA, 504) & M254
SQRTPI = qs(sqrt(pi), 254)
RSQRT2 = qs(1 / sqrt(mpf(2)), 255)


def gk(k):
    return ((2 * k + 1) ** 2 * G64) >> 64


def ck(k):
    t2 = (2 * k + 1) ** 2 * CQ
    return 2 * H / pi * exp(-t2)


CTAB = [qs(ck(k), CSCALE + gk(k)) for k in range(NT)]


def mul512(a, b):
    p = a * b
    return p >> 256, p & MASK


def shr512(p1, p0, n):
    return ((p1 << 256) | p0) >> n if n < 512 else 0


def wshr(p1, p0, n):
    v = ((p1 << 256) | p0) >> n if n < 512 else 0
    return v >> 256, v & MASK


def wadd(a1, a0, b1, b0):
    v = ((a1 << 256) | a0) + ((b1 << 256) | b0)
    return (v >> 256) & MASK, v & MASK


def mulwu(a, b):
    return (a * b) >> W


def msb(x):
    return x.bit_length() - 1


def tdiv(a, b):
    """floor(a 2^256 / b) for a < b: two divu stages, a 256-bit quotient."""
    assert 0 <= a < b
    return (a << 256) // b


def expnegsq(ker, u, m, h):
    """e^(-x^2 / 2^h) for x = m 2^(u-236): (kk, v), value v 2^(kk - 254); None below 2^-2^19."""
    P = m * m
    qt = ((P * ker.LOG2E_HI) >> 256) + ((P * ker.LOG2E_LO) >> 510)
    s2 = 216 + h - 2 * u
    f = (qt >> s2) & (WS - 1) if s2 < 512 else 0
    k = qt >> (s2 + 254) if s2 + 254 < 512 else 0
    if k >= 1 << 19:
        return None
    return ker.exp2kv(1, k, f)


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


def quad(Y, uy):
    """U = sum c_k / (y^2 + t_k^2) as (MU, eU), U = MU 2^eU, MU in [2^255, 2^256)."""
    p1, p0 = mul512(Y, Y)
    hh2, ll2 = wshr(p1, p0, 6 - 2 * uy)
    A1 = A0 = 0
    sh = sh0 = 0
    for k in range(NT):
        a = (2 * k + 1) ** 2
        carry, lo = mul512(a, CL)
        hi = a * CH + carry
        ll = (ll2 + lo) & MASK
        hh = hh2 + hi + (1 if ll < lo else 0)
        assert hh < 1 << 255
        if k == 0:
            sh = sh0 = msb(hh) + 1
        while hh >= 1 << sh:
            sh += 1
        B = ((hh << (256 - sh)) | (ll >> sh)) & MASK
        q1, q0 = wshr((CTAB[k] << 255) // B, 0, gk(k) + sh - sh0 + 2)
        A1, A0 = wadd(A1, A0, q1, q0)
    t = 255 - msb(A1)
    MU = ((A1 << t) | (A0 >> (256 - t))) & MASK
    return MU, -9 - sh0 - t


def yue(ker, Y, uy, u, m, h):
    """e^(-y^2) y U as (D0, e0), value D0 2^e0 with D0 in [2^253, 2^256); None on underflow."""
    r = expnegsq(ker, u, m, h)
    if r is None:
        return None
    kk, v = r
    MU, eU = quad(Y, uy)
    p1, p0 = mul512(Y, MU)
    YU = shr512(p1, p0, 255)
    p1, p0 = mul512(YU, v)
    D0 = shr512(p1, p0, 255)
    return D0, uy + 2 + eU + kk


def twotau(Y, uy, H2, L2):
    """The two-word product y (H2 + L2 2^-254) 2^-250 as (p1, p0): y c = p 2^(uy - 504)."""
    p1, p0 = mul512(Y, H2)
    lo = mulwu(Y, L2)
    p0 = (p0 + lo) & MASK
    p1 += 1 if p0 < lo else 0
    return p1, p0


def pole_kernel(ker, Y, uy):
    """E = e^(2 pi y/h) from the 2^f kernel: (Pm, ep) with P = 2/(1+E) = Pm 2^ep,
    Pm in (2^253, 2^255]; and (Nm, W) with tanh(pi y/h) = Nm / W."""
    p1, p0 = twotau(Y, uy, KH, KL)
    k = shr512(p1, p0, 504 - uy)
    f = shr512(p1, p0, 250 - uy) & M254
    assert k < 1 << 19
    kk, v = ker.exp2kv(0, k, f)
    one = (1 << (254 - k)) if k <= 254 else 0
    Wd = v + one
    Pm = tdiv(1 << 253, Wd)
    return Pm, -254 - k, v - one, Wd


def pole_series(ker, Y, uy):
    """s = e^(2 pi y/h) - 1 from the expm1 series at 2 pi y/(h 2^j), j = uy + 14,
    and j doublings s <- 2s + s^2; returns (Pm, Tm, es): P = 1/(1 + s/2) =
    Pm 2^-255, tanh = (s/2)/(1 + s/2) = Tm 2^(-2 - es)."""
    p1, p0 = twotau(Y, uy, LH, LL)
    j = max(0, uy + 14)
    dd = shr512(p1, p0, 255)
    es = 249 - uy
    s0 = es + j
    d = dd >> (s0 - 254)
    S = mulwu(dd, ker.expm1series(d))
    for i in range(j):
        q1, q0 = mul512(S, S)
        S += shr512(q1, q0, s0 - i + 1)
        assert S < 1 << 256
    Wd = WS + (S >> (es - 253))
    Pm = tdiv(1 << 253, Wd)
    Tm = (S << 255) // Wd
    return Pm, Tm, es


def asym(ker, Y, uy, u, m, h):
    """erfc(y) for y >= 16 by the asymptotic series: (D, e), value D 2^e."""
    r = expnegsq(ker, u, m, h)
    if r is None:
        return None
    kk, v = r
    y2 = mulwu(Y, Y)
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
        term = mulwu(term, (2 * mm - 1) * w254)
        T += sign * term
        sign, mm = -sign, mm + 1
    YS = mulwu(Y, SQRTPI)
    Q = tdiv(1 << 254, YS)
    SQ = Q - (((-T) * Q) >> 262) if T <= 0 else Q + ((T * Q) >> 262)
    p1, p0 = mul512(SQ, v)
    return shr512(p1, p0, 255), kk - uy - 255, mm


def ge12(Y, uy):
    return uy >= 4 or (uy == 3 and Y >= 3 << 253)


def ge13(Y, uy):
    return uy >= 4 or (uy == 3 and Y >= 13 << 251)


ERR_QUAD = 96
ERR_ASYM = 64
ERR_T_KERNEL = 64
ERR_T_SERIES = 256
ERR_YUE = 56


def erfc_mag(ker, u, m, h):
    """erfc(y), y = |x| / sqrt(2^h), as (D, ee, er, region): value D 2^(ee - 254),
    D in [2^255, 2^256), er the error bound in units of D's last bit; None
    when it underflows."""
    Y, uy = ystuff(u, m, h)
    if uy >= ASYM_UY:
        r = asym(ker, Y, uy, u, m, h)
        if r is None:
            return None
        D, e, _ = r
        er, region = ERR_ASYM, "asymptotic"
    else:
        r = yue(ker, Y, uy, u, m, h)
        if r is None:
            return None
        D0, e0 = r
        if ge12(Y, uy):
            D, e = D0, e0
        else:
            if uy >= -5:
                Pm, ep, _, _ = pole_kernel(ker, Y, uy)
            else:
                Pm, _, _ = pole_series(ker, Y, uy)
                ep = -255
            e = max(e0, ep) + 1
            D = (D0 >> (e - e0)) + (Pm >> (e - ep))
        er, region = ERR_QUAD, "quadrature"
    if D == 0:
        return None
    t = 255 - msb(D)
    return D << t, e - t + 254, er, region


def erf_small(ker, u, m):
    """erf(y) for y < 1/2 as (D2, e2, err): tanh(pi y/h) - e^(-y^2) y U, value D2 2^e2."""
    Y, uy = ystuff(u, m, 0)
    D0, e0 = yue(ker, Y, uy, u, m, 0)
    if uy >= -5:
        _, _, Nm, Wd = pole_kernel(ker, Y, uy)
        Tm, et, ET = tdiv(Nm, Wd), -256, ERR_T_KERNEL
    else:
        _, Tm, es = pole_series(ker, Y, uy)
        et, ET = -2 - es, ERR_T_SERIES
    e = max(e0, et)
    Dt = Tm >> (e - et)
    Dr = D0 >> (e - e0)
    D2 = Dt - Dr
    err = 2 + ((Dt * ET) >> 256) + ((Dr * ERR_YUE) >> 256)
    return D2, e, err


def tofix(val):
    if val is None:
        return 0
    D, ee = val[0], val[1]
    return D >> -ee if ee <= 0 else D << ee


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
    if val is None:
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
        D2, e2, _ = erf_small(ker, u, m)
        return K.normround(s, BIAS + e2 + 254, D2)
    return K.normround(s, BIAS, WS - tofix(erfc_mag(ker, u, m, 0)))


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
        if val is None:
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
        pts.append(K.rand_float(rng, -40, 1))
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


def check_quad(ker):
    """U, the pole terms and the asymptotic series against mpmath: relative error in bits."""
    mp.dps = 160
    worst = {"U": 0, "P": 0, "T": 0, "A": 0}
    for ymant, uy in [(1, -300), (1.3, -60), (1.7, -20), (1.1, -14), (1.9, -13), (1.5, -9), (1.0, -8), (1.9, -6),
                      (1.2, -5), (1.6, -3), (1.3, -2), (1.0, -1), (1.7, 0), (1.1, 1), (1.9, 2), (1.3, 3), (1.99, 3),
                      (1.0, 4), (1.5, 4), (1.2, 6), (1.7, 8)]:
        Y = int(mpf(ymant) * WS)
        y = mpf(Y) * mpf(2) ** (uy - 254)
        if uy < ASYM_UY:
            MU, eU = quad(Y, uy)
            Ut = sum(ck(k) / (y * y + (2 * k + 1) ** 2 * CQ) for k in range(NT))
            worst["U"] = max(worst["U"], abs(mpf(MU) * mpf(2) ** eU / Ut - 1))
            Pt = 2 / (1 + exp(y * LAMBDA))
            Tt = tanh(y * LAMBDA / 2)
            if uy >= -5:
                Pm, ep, Nm, Wd = pole_kernel(ker, Y, uy)
                worst["P"] = max(worst["P"], abs(mpf(Pm) * mpf(2) ** ep / Pt - 1))
                if uy <= -2:
                    worst["T"] = max(worst["T"], abs(mpf(tdiv(Nm, Wd)) / mpf(2) ** 256 / Tt - 1))
            else:
                Pm, Tm, es = pole_series(ker, Y, uy)
                worst["P"] = max(worst["P"], abs(mpf(Pm) / mpf(2) ** 255 / Pt - 1))
                worst["T"] = max(worst["T"], abs(mpf(Tm) * mpf(2) ** (-2 - es) / Tt - 1))
        else:
            u, m = uy, Y >> 18
            D, e, mm = asym(ker, Y, uy, u, m, 0)
            worst["A"] = max(worst["A"], abs(mpf(D) * mpf(2) ** e / merfc(mpf(m) * mpf(2) ** (u - 236)) - 1))
    for k, v in worst.items():
        print(f"  {k}: worst relative error 2^{float(log(v, 2)):.1f}" if v else f"  {k}: exact")


def bound():
    for n in (44, 46, 56, 58, 64):
        b = float(log(mpf(3.97) * sqrt(n + 1) * exp(-pi * n), 2))
        print(f"N = {n}: relative error <= 2^{b:.1f}, h = {float(sqrt(pi / (n + 1))):.4f}, pi/h = {float(sqrt(pi * (n + 1))):.2f}")
    print("asymptotic series: terms to the first below 2^-262 (none when the terms grow first)")
    for y in (13.5, 14, 14.5, 15, 16, 20, 30, 100, 430):
        y = mpf(y)
        t, m = mpf(1), 0
        while t >= mpf(2) ** -262:
            m += 1
            nt = t * (2 * m - 1) / (2 * y * y)
            if nt > t:
                m = None
                break
            t = nt
        print(f"  y = {float(y):6.1f}: {m}")


def emit_yul():
    out = [f"/// The {NT} node weights c_k = (2h/pi) e^(-t_k^2), t_k = (k + 1/2) h, h = sqrt(pi/{NT}),",
           f"/// each at 2^-({CSCALE} + g_k) with g_k = floor((2k+1)^2 G64 / 2^64) (erf256.py),",
           "/// stored past the free memory pointer (read, never moved) at p.",
           "function erfctab(p) {"]
    for k in range(NT):
        out.append(f"    mstore(add(p, {32 * k:#x}), 0x{CTAB[k]:x})")
    out.append("}")
    out.append(f"// CH 0x{CH:x}\n// CL 0x{CL:x}\n// G64 0x{G64:x}\n// LH 0x{LH:x}\n// LL 0x{LL:x}\n// KH 0x{KH:x}\n// KL 0x{KL:x}\n// SQRTPI 0x{SQRTPI:x}\n// RSQRT2 0x{RSQRT2:x}")
    return "\n".join(out)


def main(argv):
    ker, _, _ = K.build()
    if "--yul" in argv:
        print(emit_yul())
        return 0
    if "--bound" in argv:
        bound()
        return 0
    if "--wide" in argv:
        emit_wide()
        check_wide()
        return 0
    check_quad(ker)
    measure(ker)
    return 0


# ---------------------------------------------------------------------------
# The wide second stage: the rule at N = 112 in two words (constants and model)
# ---------------------------------------------------------------------------

NW = 112
NWT = NW + 1
HW = sqrt(pi / NWT)
CQW = pi / (4 * NWT)                           # t_k^2 = (2k+1)^2 CQW
RW = exp(-2 * HW * HW)                         # rho_(k+1) = rho_k RW
C0W = 2 * HW / pi * exp(-CQW)                  # c_0
LAMW = 2 * pi / HW                             # 2 pi y / h = y LAMW
WSCALE = 490


def wide(v, s=510):
    """A positive value below 2^2 (or 2^(s-508)) as the wide pair (h, l): h 2^-254 + l 2^-510."""
    n = qs(v, s)
    return n >> 256, n & MASK


C0WH, C0WL = wide(C0W)
RWH, RWL = wide(RW)
CWH, CWL = wide(CQW, WSCALE)
LAMWH, LAMWL = wide(LAMW / 32)
RSQRT2H, RSQRT2L = wide(1 / sqrt(mpf(2)))
C2H, C2L = wide(2 / sqrt(pi))
LOG2E254 = qs(LOG2E, 254)
POLE_W_EY = 4                                  # the wide pole term is dropped from y = 17


def wmul(ah, al, bh, bl):
    """The Yul's wmul: the four word products, the lowest through its high word only."""
    p = ah * bh
    rh, rl = (p >> 254) & MASK, (p << 2) & MASK
    q = ah * bl + al * bh
    q1, t0 = q >> 256, q & MASK
    p0 = (((q1 << 2) & MASK) | (t0 >> 254)) & MASK
    rl = (rl + p0) & MASK
    rh = (rh + (q1 >> 254) + (1 if rl < p0 else 0)) & MASK
    p0 = ((al * bl) >> 256) >> 254
    rl2 = (rl + p0) & MASK
    rh = (rh + (1 if rl2 < p0 else 0)) & MASK
    return rh, rl2


def wval(h, l):
    return (mpf(h) * mpf(2) ** 256 + l) * mpf(2) ** -510


def wnorm(h, l):
    """(h, l) shifted so h is in [2^254, 2^255), and the shift (left positive)."""
    v = (h << 256) | l
    t = 510 - msb(v)
    v = v << t if t >= 0 else v >> -t
    return v >> 256, v & MASK, t


def wrecip(ah, al):
    q = (1 << 508) // ah
    eh, el = wmul(ah, al, q, 0)
    v = ((1 << 511) - ((eh << 256) | el)) & ((1 << 512) - 1)
    return wmul(q, 0, v >> 256, v & MASK)


def wexp_truth(x):
    """e^x as (k2, Eh, El) with e^x = 2^k2 (1 + E), E wide, from mpmath (the Yul's
    wexpr/wexpnsq are within 2^-503 of this)."""
    k2 = int(floor(log(x, 2) / 1)) if False else int(floor(x / log(2)))
    E = x and exp(x - k2 * log(2)) - 1
    while E >= 1:
        k2 += 1
        E = exp(x - k2 * log(2)) - 1
    while E < 0:
        k2 -= 1
        E = exp(x - k2 * log(2)) - 1
    n = qs(E, 510)
    return k2, n >> 256, n & MASK


def wide_erfc(u, m, h, op, exact_exp=True):
    """The wide stage for op (0 erf, 1 erfc, 2 normCdf): the value as an mpf,
    with the exponentials taken from mpmath (exact_exp) as the Yul's wide
    kernels give them within 2^-503."""
    mp.dps = 200
    Yh, Yl, ey = m << 18, 0, u
    if h:
        Yh, Yl = wmul(Yh, 0, RSQRT2H, RSQRT2L)
        if Yh < WS:
            v = ((Yh << 256) | Yl) << 1
            Yh, Yl, ey = v >> 256, v & MASK, u - 1
    y = wval(Yh, Yl) * mpf(2) ** ey
    if ey < -130:
        th, tl = wmul(Yh, Yl, C2H, C2L)
        v = wval(th, tl) * mpf(2) ** ey
        return {0: v, 1: 1 - v, 2: (1 - v) / 2}[op]
    dh, dl = wmul(Yh, Yl, Yh, Yl)
    dh, dl = wshr(dh, dl, 20 - 2 * ey)
    y2h, y2l = dh, dl
    ch, cl = C0WH, C0WL
    rh, rl = RWH, RWL
    Sh = Sl = 0
    t0 = 0
    for k in range(NWT):
        a = (2 * k + 1) ** 2
        carry, lo = mul512(a, CWL)
        hi = a * CWH + carry
        dl = (y2l + lo) & MASK
        dh = y2h + hi + (1 if dl < lo else 0)
        dh, dl, t = wnorm(dh, dl)
        if k == 0:
            t0 = t
        dh, dl = wrecip(dh, dl)
        dh, dl = wmul(ch, cl, dh, dl)
        dh, dl = wshr(dh, dl, t0 - t)
        Sh, Sl = wadd(Sh, Sl, dh, dl)
        ch, cl = wmul(ch, cl, rh, rl)
        rh, rl = wmul(rh, rl, RWH, RWL)
    Sh, Sl = wmul(Yh, Yl, Sh, Sl)
    k2, eh, el = wexp_truth(-y * y)
    Sh, Sl = wmul(Sh, Sl, eh + WS, el)
    es = ey + t0 - 20 + k2
    if ey < 4 or (ey == 4 and Yh < 0x44 << 248):
        xh, xl = wmul(Yh, Yl, LAMWH, LAMWL)
        kp, fh, fl = wexp_truth(wval(xh, xl) * mpf(2) ** (ey + 5))
        fh += WS
        gh, gl = wshr(WS, 0, kp)
        gh, gl = wadd(fh, fl, gh, gl)
        gh, gl, tg = wnorm(gh, gl)
        gh, gl = wrecip(gh, gl)
        ep = 1 - kp + tg
        if op == 0 and ey < -5:
            v = (((fh << 256) | fl) << kp) - (1 << 510)
            Th, Tl = wmul(v >> 256, v & MASK, gh, gl)
            return wval(Th, Tl) * mpf(2) ** (ep - 1) - wval(Sh, Sl) * mpf(2) ** es
        e = max(es, ep) + 1
        Sh, Sl = wshr(Sh, Sl, e - es)
        gh, gl = wshr(gh, gl, e - ep)
        Sh, Sl = wadd(Sh, Sl, gh, gl)
        es = e
    erfc = wval(Sh, Sl) * mpf(2) ** es
    return {0: 1 - erfc, 1: erfc, 2: erfc / 2}[op]


def check_wide():
    mp.dps = 200
    worst = mpf(0)
    for x in [mpf(2) ** -129, mpf(2) ** -100, mpf("0.001"), mpf("0.02"), mpf("0.03"), mpf("0.3"), mpf(1), mpf("2.5"),
              mpf(6), mpf("9.9"), mpf("12.5"), mpf("16.9"), mpf(17), mpf(25), mpf(100), mpf(400)]:
        w = K.encode(x)
        s, e, m = K.unpack(w)
        u = e - BIAS
        xv = K.decode(w)
        for op, truth in ((0, merf), (1, merfc), (2, lambda v: ncdf(-v))):
            if op == 0 and xv >= 13:
                continue
            got = wide_erfc(u, m, op == 2, op)
            t = truth(xv)
            if t == 0:
                continue
            rel = abs(got / t - 1)
            worst = max(worst, rel)
            print(f"  x = {float(xv):9.4g} op {op}: relative error 2^{float(log(rel, 2)) if rel else -999:.1f}")
    print(f"wide stage: worst relative error 2^{float(log(worst, 2)):.1f}")


def emit_wide():
    print(f"// C0WH 0x{C0WH:x}\n// C0WL 0x{C0WL:x}\n// RWH 0x{RWH:x}\n// RWL 0x{RWL:x}\n// CWH 0x{CWH:x}\n// CWL 0x{CWL:x}")
    print(f"// LAMWH 0x{LAMWH:x}\n// LAMWL 0x{LAMWL:x}\n// RSQRT2H 0x{RSQRT2H:x}\n// RSQRT2L 0x{RSQRT2L:x}\n// C2H 0x{C2H:x}\n// C2L 0x{C2L:x}\n// LOG2E254 0x{LOG2E254:x}")
    print(f"// wide bound: N = {NW}: 2^{float(log(mpf(3.97) * sqrt(NWT) * exp(-pi * NW), 2)):.1f}, pi/h = {float(pi / HW):.2f}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

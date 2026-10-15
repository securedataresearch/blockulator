#!/usr/bin/env python3
"""The wide kernels for FP256 release two (#78): 2^f and log2(1 + f) at 2^-254,
modelled in exact integer arithmetic as the Yul runs them, with the constants
and the Yul text they need.

    uv run scripts/fp256/generators/kernel254.py            # fit, measure the kernels and the ops
    uv run scripts/fp256/generators/kernel254.py --yul      # print the Yul kernel functions

Scale: 2^-254 (values below 4 fit a word). Every product is
mulw(a, b) = floor(a b / 2^254), the top of the 512-bit product.

exp2: f in [0, 1) is split as j/16 + r with j the top four bits and
r in [0, 1/16); 2^f = T[j] 2^r with T a 16-entry table of 2^(j/16) and 2^r a
Chebyshev-fitted polynomial on [0, 1/16) with error below 2^-262.

log2: the mantissa in [1, 2) is reduced by K stages (K = 12): if
mm >= 2^(1/2^k) then mm *= 2^(-1/2^k), acc += 2^-k; the residual
f = mm - 1 < 2^(1/4096) - 1 goes to a Chebyshev fit of log2(1 + f)/f.

ln near one: ln(1 + d)/d = sum (-d)^k/(k + 1), 32 terms for |d| < 2^-8.

The op models below (model_exp, model_ln, model_pow) are the Yul in Python:
unpack, the same shifts and products, normround. They are measured against
mpmath over random floats; the Precision floors in test/fp256 are set from
what they report.
"""
from __future__ import annotations

import random
import sys

from mpmath import mp, mpf, log, power, exp as mexp, nint, cos, pi, matrix, lu_solve, frexp

mp.dps = 160
MASK = (1 << 256) - 1
W = 254
WS = 1 << W
M254 = WS - 1
TABLE_BITS = 4
STAGES = 12
SERIES_TERMS = 32
BIAS = 0x3FFFF
HIDDEN = 1 << 236
FMASK = HIDDEN - 1


# ---- fitting -----------------------------------------------------------------

def fit(func, degree, a, b):
    n = degree + 1
    nodes = [(b - a) / 2 * cos(pi * (2 * k + 1) / (2 * n)) + (b + a) / 2 for k in range(n)]
    V = matrix(n, n); y = matrix(n, 1)
    for i, x in enumerate(nodes):
        for j in range(n):
            V[i, j] = x ** j
        y[i, 0] = func(x)
    c = lu_solve(V, y)
    return [c[i, 0] for i in range(n)]


def max_err(coeffs, func, a, b, pts=3000):
    worst = mpf(0)
    for i in range(pts + 1):
        x = a + (b - a) * i / pts
        r = coeffs[-1]
        for c in reversed(coeffs[:-1]):
            r = r * x + c
        worst = max(worst, abs(r - func(x)))
    return worst


def choose(func, a, b, lo, hi, target_bits):
    for d in range(lo, hi):
        c = fit(func, d, a, b)
        e = max_err(c, func, a, b)
        if e < mpf(2) ** (-target_bits):
            return d, c, e
    raise RuntimeError("no degree reached the target")


# ---- the word-level primitives, as the Yul does them -------------------------

def q(v) -> int:
    return int(nint(v * WS)) & MASK


def signed(w: int) -> int:
    return w - (1 << 256) if w >> 255 else w


def mulw(a: int, b: int) -> int:
    """floor(a b / 2^254) on signed words, masked."""
    return (signed(a) * signed(b)) >> W & MASK


def mulwu(a: int, b: int) -> int:
    return (a * b) >> W


def shr512(p: int, n: int) -> int:
    return (p >> n) & MASK if n < 512 else 0


def msb(x: int) -> int:
    return x.bit_length() - 1


def normround(s: int, e: int, D: int) -> int:
    n = msb(D)
    e += n - 254
    D = (D << (255 - n)) & MASK
    m = (D >> 19) + ((D >> 18) & 1)
    if m == 1 << 237:
        m = HIDDEN; e += 1
    if e > 0x7FFFF:
        raise OverflowError
    if e < 1:
        return 0
    return (s << 255) | (e << 236) | (m & FMASK)


def unpack(x: int):
    s = x >> 255; e = (x >> 236) & 0x7FFFF; m = x & FMASK
    if e == 0:
        assert s == 0 and m == 0
        return 0, 0, 0
    return s, e, m | HIDDEN


def encode(v) -> int:
    """A float word from an mpf, correctly rounded (half up on the magnitude)."""
    if v == 0:
        return 0
    s = 1 if v < 0 else 0
    m, ex = frexp(abs(v))
    T = int(mp.floor(m * (mpf(2) ** 238)))
    return normround(s, BIAS + ex - 238 + 254, T)


def decode(w: int):
    s, e, m = unpack(w)
    if e == 0:
        return mpf(0)
    v = mpf(m) * power(2, e - BIAS - 236)
    return -v if s else v


# ---- kernels -------------------------------------------------------------------

class Kernels:
    def __init__(self, exp_c, table, log_c, thr, inv, series, ln2, log2e_hi, log2e_lo):
        self.exp_c = exp_c          # ascending, for 2^r on [0, 1/16)
        self.table = table          # 2^(j/16), j = 0..15
        self.log_c = log_c          # ascending, for log2(1+f)/f
        self.thr = thr              # 2^(1/2^k), k = 1..STAGES
        self.inv = inv              # 2^(-1/2^k)
        self.series = series        # 1/(k+1) with alternating signs, k = 0..SERIES_TERMS-1, at 2^-254
        self.LN2 = ln2
        self.LOG2E_HI = log2e_hi    # log2 e at 2^-254
        self.LOG2E_LO = log2e_lo    # the next 254 bits

    def exp2frac(self, f: int) -> int:
        """2^f for f in [0, 2^254) at 2^-254, result in [2^254, 2^255)."""
        j = f >> (W - TABLE_BITS)
        r = f & ((1 << (W - TABLE_BITS)) - 1)
        p = self.exp_c[-1]
        for c in reversed(self.exp_c[:-1]):
            p = mulwu(p, r) + c
        return mulwu(self.table[j], p)

    def log2m(self, mm: int) -> int:
        """log2(mm) for mm in [2^254, 2^255) at 2^-254, result in [0, 2^254)."""
        acc = 0
        for k in range(STAGES):
            if mm >= self.thr[k]:
                mm = mulwu(mm, self.inv[k])
                acc += 1 << (W - 1 - k)
        f = mm - WS
        p = self.log_c[-1]
        for c in reversed(self.log_c[:-1]):
            p = (mulw(p, f) + c) & MASK
        return (acc + signed(mulw(p, f))) & MASK

    def ln1pseries(self, df: int) -> int:
        """ln(1 + d)/d at 2^-254 for a signed d at 2^-254, |d| < 2^-8."""
        p = self.series[-1]
        for c in reversed(self.series[:-1]):
            p = (mulw(df, p) + c) & MASK
        return p

    # ---- the ops ------------------------------------------------------------------

    def exp2kf(self, s: int, k: int, f: int) -> int:
        """2^(+-(k + f/2^254)) rounded once; k < 2^19 checked by the caller."""
        if s:
            if f:
                k = -k - 1; f = WS - f
            else:
                k = -k
        v = self.exp2frac(f) if f else WS
        return normround(0, k + BIAS, v)

    def model_exp(self, x: int) -> int:
        s, e, m = unpack(x)
        ONE = BIAS << 236
        if e == 0:
            return ONE
        u = e - BIAS
        if u >= 18:
            if s:
                return 0
            raise OverflowError
        if u < -237:
            return ONE
        if u < -118:
            # 1 + x (1 + x/2), exact enough; modelled with mpmath here
            return encode(1 + decode(x) * (1 + decode(x) / 2))
        # t = x log2 e = m 2^(u-236) (LOG2E_HI + LOG2E_LO 2^-254) 2^-254
        P = m * self.LOG2E_HI + mulwu(m, self.LOG2E_LO)
        # t at 2^-254 = P 2^(u - 490 + 254) = P >> (236 - u)
        qsh = 236 - u
        f = shr512(P, qsh) & M254
        k = shr512(P, qsh + 254)
        if k >= 1 << 19:
            if s:
                return 0
            raise OverflowError
        return self.exp2kf(s, k, f)

    def log2pair(self, e: int, m: int):
        """log2 of a positive number as (Lm, Ls): L = Lm 2^Ls, Lm a signed word, via the
        general path. The caller handles the near-one band."""
        u = e - BIAS
        lg = self.log2m(m << 18)
        if u == 0:
            return lg, -254
        au = abs(u)
        sh = msb(au) + 1
        Lm = ((u << (254 - sh)) + (lg >> sh)) & MASK
        return Lm, sh - 254

    def nearone(self, x: int):
        """d = x - 1 exactly when e in {bias-1, bias} and |d| < 2^-8: (sd, ud, md) or None."""
        s, e, m = unpack(x)
        if s or e not in (BIAS - 1, BIAS):
            return None
        d = decode(x) - 1
        if d == 0 or abs(d) >= mpf(2) ** -8:
            return None
        w = encode(d)
        sd, ed, md = unpack(w)
        return sd, ed - BIAS, md

    def tofixed254(self, s: int, u: int, m: int) -> int:
        t = m >> (-u - 18) if u < -18 else m << (u + 18)
        return (-t) & MASK if s else t

    def model_ln(self, x: int) -> int:
        s, e, m = unpack(x)
        assert not s and e
        ONE = BIAS << 236
        if x == ONE:
            return 0
        band = self.nearone(x)
        if band is not None:
            sd, ud, md = band
            p = self.ln1pseries(self.tofixed254(sd, ud, md))
            P = md * p                       # 491 bits, value d p 2^(ud - 490)... as D 2^(e - bias - 254)
            return normround(sd, BIAS + ud, P >> 236)
        Lm, Ls = self.log2pair(e, m)
        r = mulw(Lm, self.LN2)
        rs = signed(r)
        return normround(1 if rs < 0 else 0, BIAS + Ls + 254, abs(rs))

    def model_pow(self, x: int, y: int) -> int:
        ONE = BIAS << 236
        sx, ex, mx = unpack(x)
        sy, ey, my = unpack(y)
        assert ex and not sx and ey
        band = self.nearone(x)
        if band is not None:
            sd, ud, md = band
            p = self.ln1pseries(self.tofixed254(sd, ud, md))
            # log2(x) = d p / ln2 = md p LOG2E 2^(ud - 236 - 508)
            Lm = mulwu(mulwu(md << 17, p), self.LOG2E_HI)      # at 2^-254, times 2^(ud+1); below 2^255
            Ls = ud - 253
            Lneg = sd
        else:
            Lm, Ls = self.log2pair(ex, mx)
            Lneg = 1 if signed(Lm) < 0 else 0
            Lm = abs(signed(Lm))
        P = Lm * my                                     # |t| = P 2^(Ls + uy - 236)
        es = Ls + (ey - BIAS) - 236
        qsh = -es
        if qsh < 254:
            # |t| >= 2^(489 - 253): overflow or zero
            k = 1 << 19; f = 0
        else:
            f = shr512(P, qsh - 254) & M254
            k = shr512(P, qsh)
        s = Lneg ^ sy
        if k >= 1 << 19:
            if s:
                return 0
            raise OverflowError
        return self.exp2kf(s, k, f)


def bits(got: int, truth) -> float:
    g = decode(got)
    if g == truth:
        return 256.0
    if truth == 0:
        return 0.0
    return float(-log(abs(g - truth) / abs(truth), 2))


def build():
    sixteenth = mpf(1) / 16
    d1, ec, e1 = choose(lambda r: power(2, r), mpf(0), sixteenth, 16, 40, 262)
    print(f"exp2: degree {d1} on [0, 1/16), max poly error 2^{float(log(e1, 2)):.1f}")
    b = power(2, mpf(1) / 2 ** STAGES) - 1
    P = lambda f: (log(1 + f, 2) / f) if f != 0 else 1 / log(2)
    d2, lc, e2 = choose(P, mpf(0), b, 8, 40, 262)
    print(f"log2: degree {d2} on [0, 2^(1/{2 ** STAGES}) - 1), max poly error 2^{float(log(e2, 2)):.1f}")
    log2e = 1 / log(2)
    hi = int(mp.floor(log2e * WS))
    lo = int(nint((log2e * WS - hi) * WS))
    return Kernels([q(c) for c in ec],
                   [q(power(2, mpf(j) / 16)) for j in range(16)],
                   [q(c) for c in lc],
                   [q(power(2, mpf(1) / 2 ** (k + 1))) for k in range(STAGES)],
                   [q(power(2, -mpf(1) / 2 ** (k + 1))) for k in range(STAGES)],
                   [q(mpf((-1) ** k) / (k + 1)) for k in range(SERIES_TERMS)],
                   q(log(2)), hi, lo), d1, d2


def hx(v: int) -> str:
    return f"0x{v:x}"


def emit_yul(K: Kernels, d1: int, d2: int) -> str:
    out = []
    out.append(f"/// 2^f for f in [0, 1) at 2^-254, result at 2^-254 in [1, 2): f = j/16 + r,\n"
               f"/// 2^(j/16) from a 16-entry table and 2^r from a degree-{d1} Chebyshev fit on\n"
               f"/// [0, 1/16) (max error 2^-262, kernel254.py), Horner with a floor at 2^-254\n"
               f"/// at every step. Unsigned throughout.\n"
               f"function exp2frac(f) -> r {{\n"
               f"    let x := and(f, {hx((1 << 250) - 1)})\n"
               f"    r := {hx(K.exp_c[-1])}")
    for c in reversed(K.exp_c[:-1]):
        out.append(f"    r := add(mulwu(r, x), {hx(c)})")
    out.append("    switch shr(250, f)")
    for j, t in enumerate(K.table):
        if j == 0:
            continue
        out.append(f"    case {j} {{ r := mulwu(r, {hx(t)}) }}")
    out.append("}\n")
    out.append(f"/// f * P(f) = log2(1 + f) for f in [0, 2^(1/4096) - 1) at 2^-254. P is a\n"
               f"/// degree-{d2} Chebyshev fit of log2(1 + f) / f (max error 2^-262), Horner with\n"
               f"/// a floor at 2^-254 at every step; the coefficients alternate in sign.\n"
               f"function log2poly(f) -> r {{\n"
               f"    r := {hx(K.log_c[-1])}")
    for c in reversed(K.log_c[:-1]):
        out.append(f"    r := add(mulw(r, f), {hx(c)})")
    out.append("    r := mulw(r, f)\n}\n")
    out.append(f"/// log2(mm) for a mantissa mm in [1, 2) at 2^-254, result at 2^-254 in [0, 1),\n"
               f"/// unrounded: {STAGES} range-reduction stages by 2^(1/2^k) and the polynomial on\n"
               f"/// the residual. Absolute error below 2^-250 (kernel254.py).\n"
               f"function log2m(mm) -> r {{\n"
               f"    let acc := 0")
    for k in range(STAGES):
        out.append(f"    if iszero(gt({hx(K.thr[k])}, mm)) {{\n"
                   f"        mm := mulwu(mm, {hx(K.inv[k])})\n"
                   f"        acc := add(acc, {hx(1 << (W - 1 - k))})\n"
                   f"    }}")
    out.append(f"    r := add(acc, log2poly(sub(mm, {hx(WS)})))\n}}\n")
    half = SERIES_TERMS // 2
    out.append(f"/// ln(1 + d) / d: the series sum_{{k>=0}} (-d)^k / (k + 1) at 2^-254 for\n"
               f"/// |d| < 2^-8, Horner in {SERIES_TERMS} terms (truncation below 2^-261), in\n"
               f"/// two halves so the Yul pipeline's stack stays shallow.\n"
               f"function ln1pseries(df) -> p {{\n"
               f"    p := ln1ptail(df)")
    for c in reversed(K.series[:half]):
        out.append(f"    p := add({hx(c)}, mulw(df, p))")
    out.append("}\n")
    out.append(f"/// The upper {SERIES_TERMS - half} terms of ln1pseries.\n"
               f"function ln1ptail(df) -> p {{\n"
               f"    p := {hx(K.series[-1])}")
    for c in reversed(K.series[half:-1]):
        out.append(f"    p := add({hx(c)}, mulw(df, p))")
    out.append("}\n")
    out.append(f"// LN2      {hx(K.LN2)}\n// LOG2E_HI {hx(K.LOG2E_HI)}\n// LOG2E_LO {hx(K.LOG2E_LO)}")
    return "\n".join(out)


def rand_float(rng, lo, hi, s=None):
    u = rng.randint(lo, hi)
    sg = rng.getrandbits(1) if s is None else s
    return (sg << 255) | ((u + BIAS) << 236) | rng.getrandbits(236)


def measure_ops(K: Kernels, rng):
    mp.dps = 160
    rows = []
    xs = [rand_float(rng, -118, 17) for _ in range(300)] + [rand_float(rng, -237, -119) for _ in range(60)]
    b = []
    for x in xs:
        try:
            b.append(bits(K.model_exp(x), mexp(decode(x))))
        except OverflowError:
            pass
    rows.append(("exp", min(b), sum(b) / len(b)))
    xs = [rand_float(rng, -1000, 1000, 0) for _ in range(300)] + [rand_float(rng, -1, 0, 0) for _ in range(200)]
    for k in range(1, 30):   # near one on both sides, d ~ 2^-k
        d = mpf(2) ** -(k * 8) * (1 + rng.random())
        xs.append(encode(1 + d)); xs.append(encode(1 - d))
    b = [bits(K.model_ln(x), log(decode(x))) for x in xs if x != BIAS << 236]
    rows.append(("ln", min(b), sum(b) / len(b)))
    b = []; bsmall = []
    for _ in range(400):
        x = rand_float(rng, -40, 40, 0)
        y = rand_float(rng, -20, 10)
        if rng.random() < 0.3:
            x = encode(1 + mpf(2) ** -rng.randint(10, 230) * (rng.random() + 0.5) * (1 if rng.getrandbits(1) else -1))
            y = rand_float(rng, -5, 40)
        t = decode(y) * log(decode(x), 2)
        if abs(t) >= 262000:
            continue
        got = K.model_pow(x, y)
        bb = bits(got, power(decode(x), decode(y)))
        b.append(bb)
        if abs(t) < 64:
            bsmall.append(bb)
    rows.append(("pow", min(b), sum(b) / len(b)))
    rows.append(("pow |t|<64", min(bsmall), sum(bsmall) / len(bsmall)))
    for name, mn, mean in rows:
        print(f"{name:12} bits min {mn:7.2f} mean {mean:7.2f}")


def main(argv):
    random.seed(254)
    rng = random.Random(254)
    K, d1, d2 = build()
    if "--yul" in argv:
        print(emit_yul(K, d1, d2))
        return 0
    exp_in = [random.getrandbits(W) for _ in range(400)] + [0, 1, WS - 1, WS >> 1, (WS >> 4) - 1, WS >> 4, (WS * 15) >> 4]
    log_in = [WS + random.getrandbits(W) for _ in range(400)] + [WS + 1, 2 * WS - 1, WS + (WS >> 1), WS + (WS >> 100)]
    print("\nkernels at 2^-254, exact-integer model:")
    eb = [float(-log(abs(mpf(K.exp2frac(x)) / WS - power(2, mpf(x) / WS)) / power(2, mpf(x) / WS), 2)) for x in exp_in]
    print(f"exp2frac   n={len(eb):4} relative bits min {min(eb):7.2f}")
    worst = max(abs(mpf(signed(K.log2m(x))) / WS - log(mpf(x) / WS, 2)) for x in log_in)
    print(f"log2m      n={len(log_in):4} absolute error max 2^{float(log(worst, 2)):.1f}")
    print("\nthe ops, modelled as the Yul runs them, against mpmath:")
    measure_ops(K, rng)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

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

expm1 near zero (release three): (e^d - 1)/d = sum d^k/(k + 1)!, 24 terms for
|d| < 2^-8 (truncation below 2^-263). log1p below 2^-4 is d times the same
ln series (32 terms below 2^-8, 64 from there, truncation below 2^-261), so the log2 kernel's
2^-250 never meets a result below 2^-4; above, 1 + x is formed exactly on a
2^-254 grid under its leading bit and goes through log2m. expm1 above 2^-8 takes exp's unrounded 2^f and
subtracts the one on the same grid, so neither op cancels.

The op models below (model_exp, model_ln, model_pow, model_log1p, model_expm1) are the Yul in Python:
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
WIDE_TERMS = 64        # log1p's band, |d| < 2^-4
EXPM1_TERMS = 24
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
    def __init__(self, exp_c, table, log_c, thr, inv, series, ln2, log2e_hi, log2e_lo, eseries):
        self.exp_c = exp_c          # ascending, for 2^r on [0, 1/16)
        self.table = table          # 2^(j/16), j = 0..15
        self.log_c = log_c          # ascending, for log2(1+f)/f
        self.thr = thr              # 2^(1/2^k), k = 1..STAGES
        self.inv = inv              # 2^(-1/2^k)
        self.series = series        # 1/(k+1) with alternating signs, k = 0..WIDE_TERMS-1, at 2^-254
        self.LN2 = ln2
        self.LOG2E_HI = log2e_hi    # log2 e at 2^-254
        self.LOG2E_LO = log2e_lo    # the next 254 bits
        self.eseries = eseries      # 1/(k+1)!, k = 0..EXPM1_TERMS-1, at 2^-254

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

    def ln1pseries(self, df: int, terms: int = SERIES_TERMS) -> int:
        """ln(1 + d)/d at 2^-254 for a signed d at 2^-254: 32 terms for |d| < 2^-8,
        64 (ln1pwide) for |d| < 2^-4. Horner from zero, as the Yul quarters run it."""
        p = 0
        for c in reversed(self.series[:terms]):
            p = (mulw(df, p) + c) & MASK
        return p

    def expm1series(self, df: int) -> int:
        """(e^d - 1)/d at 2^-254 for a signed d at 2^-254, |d| < 2^-8."""
        p = self.eseries[-1]
        for c in reversed(self.eseries[:-1]):
            p = (mulw(df, p) + c) & MASK
        return p

    # ---- the ops ------------------------------------------------------------------

    def exp2kv(self, s: int, k: int, f: int):
        """2^(+-(k + f/2^254)) as (k', v): v at 2^-254 in [1, 2), unrounded."""
        if s:
            if f:
                k = -k - 1; f = WS - f
            else:
                k = -k
        return k, (self.exp2frac(f) if f else WS)

    def exp2kf(self, s: int, k: int, f: int) -> int:
        """2^(+-(k + f/2^254)) rounded once; k < 2^19 checked by the caller."""
        k, v = self.exp2kv(s, k, f)
        return normround(0, k + BIAS, v)

    def explog2(self, u: int, m: int):
        """x log2 e for x = m 2^(u - 236) as (k, f): the integer part and the
        fraction at 2^-254, from the two-word product."""
        P = m * self.LOG2E_HI + mulwu(m, self.LOG2E_LO)
        qsh = 236 - u
        return shr512(P, qsh + 254), shr512(P, qsh) & M254

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
        if u < -238:
            return ONE
        if u < -118:
            return self.expsmall(s, u, m)
        tz = 118 - u
        if not s and u < -84 and (m >> tz) & 1 and m & ((1 << tz) - 1) == 0:
            a = m >> tz                       # x = a 2^-118: 1 + x + x^2/2 is a tie
            return normround(0, BIAS, WS + (m >> -(u + 18)) + ((a * a) << 17))
        # t = x log2 e = m 2^(u-236) (LOG2E_HI + LOG2E_LO 2^-254) 2^-254
        k, f = self.explog2(u, m)
        if k >= 1 << 19:
            if s:
                return 0
            raise OverflowError
        return self.exp2kf(s, k, f)

    def expsmall(self, s: int, u: int, m: int) -> int:
        """e^x for u in [-238, -119]: floor((1 + x + x^2/2 +- x^3/6) 2^254) exactly, as the Yul."""
        k = -(u + 18)
        tq = m >> k
        tf = ((m & ((1 << k) - 1)) << (256 - k)) & MASK
        P = m * m
        j = 219 - 2 * u
        qq = P >> j
        n = j - 256
        qf = (P >> n) & MASK
        st = P & ((1 << n) - 1)
        if not s:
            d = WS + tq + qq + (1 if tf and qf >= (1 << 256) - tf else 0)
        else:
            d = WS - tq + qq - (1 if qf < tf or (qf == tf and st == 0) else 0)
        return normround(0, BIAS, d)

    def log2pair(self, e: int, m: int):
        """log2 of a positive number as (Lm, Ls): L = Lm 2^Ls, Lm a signed word, via the
        general path. The caller handles the near-one band."""
        return self.log2pairm(e - BIAS, m << 18)

    def log2pairm(self, u: int, mm: int):
        """log2(mm 2^(u - 254)) for a mantissa mm in [2^254, 2^255), as log2pair."""
        lg = self.log2m(mm)
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


def _model_log1p(self, x: int) -> int:
    s, e, m = unpack(x)
    if e == 0:
        return 0
    u = e - BIAS
    if u < -4:
        P = m * self.ln1pseries(self.tofixed254(s, u, m), SERIES_TERMS if u < -8 else WIDE_TERMS)
        return normround(s, e, P >> 236)
    assert not (s and u >= 0)
    b = max(u, 0)
    xs = m << (18 + u - b)
    one = (1 << (254 - b)) if b <= 254 else 0
    a = one - xs if s else one + xs
    n = msb(a)
    k = b + n - 254
    a = a << (254 - n) if n < 254 else a >> (n - 254)
    Lm, Ls = self.log2pairm(k, a)
    r = signed(mulw(Lm, self.LN2))
    return normround(1 if r < 0 else 0, BIAS + Ls + 254, abs(r))


def _model_expm1(self, x: int) -> int:
    s, e, m = unpack(x)
    NEGONE = (1 << 255) | (BIAS << 236)
    if e == 0:
        return 0
    u = e - BIAS
    if u < -8:
        P = m * self.expm1series(self.tofixed254(s, u, m))
        return normround(s, e, P >> 236)
    if u >= 18:
        if s:
            return NEGONE
        raise OverflowError
    k, f = self.explog2(u, m)
    if k >= 1 << 19:
        if s:
            return NEGONE
        raise OverflowError
    k, v = self.exp2kv(s, k, f)
    if not s:
        return normround(0, BIAS + k, v - ((1 << (254 - k)) if k <= 254 else 0))
    c = -(-v >> -k)                      # ceil(v 2^k)
    return normround(1, BIAS, WS - c)


Kernels.model_log1p = _model_log1p
Kernels.model_expm1 = _model_expm1


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
                   [q(mpf((-1) ** k) / (k + 1)) for k in range(WIDE_TERMS)],
                   q(log(2)), hi, lo,
                   [q(1 / mp.factorial(k + 1)) for k in range(EXPM1_TERMS)]), d1, d2


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
    out.append(f"/// ln(1 + d) / d: the series sum_{{k>=0}} (-d)^k / (k + 1) at 2^-254, Horner\n"
               f"/// in {SERIES_TERMS} terms for |d| < 2^-8 (truncation below 2^-261), from zero\n"
               f"/// through two 16-term quarters so the Yul pipeline's stack stays shallow.\n"
               f"function ln1pseries(df) -> p {{\n"
               f"    p := ln1pq1(df, ln1pq2(df, 0))\n}}\n")
    out.append(f"/// The same series in {WIDE_TERMS} terms for |d| < 2^-4 (truncation below\n"
               f"/// 2^-262): log1p's band, four quarters.\n"
               f"function ln1pwide(df) -> p {{\n"
               f"    p := ln1pq1(df, ln1pq2(df, ln1pq3(df, ln1pq4(df, 0))))\n}}\n")
    for qn in range(1, WIDE_TERMS // 16 + 1):
        lo, hi = 16 * (qn - 1), 16 * qn
        out.append(f"/// Horner steps for terms {hi - 1} down to {lo} of the ln series.\n"
                   f"function ln1pq{qn}(df, q) -> p {{\n"
                   f"    p := q")
        for c in reversed(K.series[lo:hi]):
            out.append(f"    p := add({hx(c)}, mulw(df, p))")
        out.append("}\n")
    eh = EXPM1_TERMS // 2
    out.append(f"/// (e^d - 1) / d: the series sum_{{k>=0}} d^k / (k + 1)! at 2^-254 for\n"
               f"/// |d| < 2^-8, Horner in {EXPM1_TERMS} terms (truncation below 2^-263), in\n"
               f"/// two halves as ln1pseries.\n"
               f"function expm1series(df) -> p {{\n"
               f"    p := expm1tail(df)")
    for c in reversed(K.eseries[:eh]):
        out.append(f"    p := add({hx(c)}, mulw(df, p))")
    out.append("}\n")
    out.append(f"/// The upper {EXPM1_TERMS - eh} terms of expm1series.\n"
               f"function expm1tail(df) -> p {{\n"
               f"    p := {hx(K.eseries[-1])}")
    for c in reversed(K.eseries[eh:-1]):
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
    from mpmath import log1p as mlog1p, expm1 as mexpm1
    xs = [rand_float(rng, -300, 30, 0) for _ in range(300)] + [rand_float(rng, -300, -1, 1) for _ in range(300)]
    xs += [rand_float(rng, -12, -6) for _ in range(200)]
    b = [bits(K.model_log1p(x), mlog1p(decode(x))) for x in xs]
    rows.append(("log1p", min(b), sum(b) / len(b)))
    xs = [rand_float(rng, -300, 17) for _ in range(500)] + [rand_float(rng, -12, -6) for _ in range(200)]
    b = []
    for x in xs:
        try:
            b.append(bits(K.model_expm1(x), mexpm1(decode(x))))
        except OverflowError:
            pass
    rows.append(("expm1", min(b), sum(b) / len(b)))
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

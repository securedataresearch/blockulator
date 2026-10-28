#!/usr/bin/env python3
"""FP19's exp/log kernels at 2^-254, modelled in exact integer arithmetic as
the Yul runs them, with the fits, the bounds and the Yul text they need.

    uv run scripts/fp19/generators/kernel254.py            # fit, certify, measure the kernels and the ops
    uv run scripts/fp19/generators/kernel254.py --yul      # print the Yul kernel functions
    uv run scripts/fp19/generators/kernel254.py --check    # does FP19.yul.src hold that Yul verbatim?

Scale: 2^-254 (values below 4 fit a word) at the kernels' edges. Inside
them every product is hi(a, b) = floor(a b / 2^256), the 512-bit product's
high word (mul, mulmod, sub, sub, lt), written out in line: a call to a
product helper costs about 130 gas more than its body here, and the
kernels make 15 to 30 products.

Blockulator 2.2 (Phase K) replaces release two's kernels (2^f from a
16-entry table and a degree-26 polynomial, log2 from twelve reduction
stages and a degree-17 polynomial, ln near one by the 32- and 64-term Taylor
series of ln(1 + d)/d):

exp2 (exp2frac): f in [0, 1) is split as j1/16 + j2/256 + r, r in
[0, 2^-8); 2^f = T1[j1] T2[j2] 2^r. 2^r is the degree-19 minimax polynomial
on [0, 2^-8) (Remez, minimax.py; certified sup norm 2^-270.7 relative),
Horner at 2^-255 with r at 2^-256, the top steps in one word (below). Each
table level is v + hi(v, (T - 1) 2^256), T - 1 rounded at 2^-256; the
result floored to 2^-254.

log2 (log2m): the mantissa 1 + w in [1, 2) is reduced by two additive levels
of 16 by word-only operations: i = floor(16 w), 1 + w1 = (1 + w)/(1 + i/16)
as w1 = 16 (w - i/16)/(16 + i), one shift and one div by a small integer
(no product), log2(1 + i/16) from a table and added; then the same by
1 + i/256. That leaves w2 in [0, 2^-8) and log2(1 + w2) = 2 log2(e)
atanh(y), y = w2/(2 + w2) by one divh, = y P(y^2) with P(s) = 2 log2(e)
atanh(sqrt s)/sqrt s the degree-12 minimax polynomial on [0, (2^-8/(2 -
2^-8))^2] (certified 2^-263.7 relative).

ln near one (ln1pseries, |d| < 2^-8; ln1pwide, |d| < 2^-4): ln(1 + d)/d =
(ln 2/2)(1 - y) P(y^2), y = d/(2 + d) by one divh (2/(2 + d) is 1 - y), with
the same P below 2^-8 and a degree-21 fit of it on [0, (2^-4/(2 - 2^-4))^2]
(certified 2^-266.5) for log1p's band to 2^-4. The relative precision holds
however small d is: y carries d's sign and a fixed absolute grid, and only
1 - y and y^2 enter.

One-word steps: in p_j = c_j + p_{j+1} u the error of p_j reaches the result
times u^j, so where u^j is small the product needs far fewer than 256 bits:
p_j = c_j + ((p_{j+1} >> a) (T >> b)) >> (256 - a - b), one mul. Its error is
below 1 + (2^a T + 2^b p)/2^256 units; the generator takes a step in one
word when that, times u^j, is under 2^-9 units and the whole is under 2^-6.

Every fit is minimax (Remez exchange, minimax.py), never a Taylor
truncation; each sup norm is certified on 20,002 points at 110 digits.

expm1 near zero (expm1series, |d| < 2^-8): (e^d - 1)/d, which was the
24-term Taylor series, is the degree-21 minimax polynomial on [-2^-8, 2^-8]
(certified 2^-270.7 relative), signed Horner on d at 2^-256: the one-word
steps by mul and sar, the full ones the high word less p when d < 0, all
partial sums positive. expm1 above 2^-8 takes
exp's unrounded 2^f and subtracts the one on the same grid; log1p from 2^-4
forms 1 + x exactly on a 2^-254 grid under its leading bit for log2m.

The op models below (model_exp, model_ln, model_pow, model_log1p,
model_expm1) are the Yul in Python: unpack, the same shifts and products,
normround. They are measured against mpmath over random floats; bounds.py
checks every fast value's error against the err the Yul's rounding test
uses.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from mpmath import mp, mpf, log, power, exp as mexp, nint, frexp, atanh, sqrt, ceil

sys.path.insert(0, str(Path(__file__).resolve().parent))
from minimax import remez, certify  # noqa: E402
from horner import Horner, hiline, hiset, tree  # noqa: E402

mp.dps = 110
MASK = (1 << 256) - 1
W = 254
WS = 1 << W
M254 = WS - 1
BIAS = 0x3FFFF
HIDDEN = 1 << 236
FMASK = HIDDEN - 1

EXP_LEVELS = 2             # 16-entry table levels for 2^f
EXP_DEG = 19               # 2^r on [0, 2^(-4 EXP_LEVELS))
LN_DEG = 12                # P(s) for |y| below 2^-8/(2 - 2^-8)
LNW_DEG = 21               # P(s) for |y| below 2^-4/(2 - 2^-4)
EM1_DEG = 21               # (e^d - 1)/d for |d| below 2^-8
SY = 259                   # y = d/(2 + d) at 2^-259 in log2m and the near-one ln
SS = 2 * SY - 256          # y^2 at 2^-262


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


def hi(a: int, b: int) -> int:
    return (a * b) >> 256


def divh(a: int, b: int) -> int:
    """floor(a 2^255 / b), a < 2 b."""
    assert 0 < b and a < 2 * b
    return (a << 255) // b


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


def hx(v: int) -> str:
    return f"0x{v:x}"


# ---- the fits --------------------------------------------------------------------

def em1fun(d):
    """(e^d - 1)/d."""
    from mpmath import expm1
    return expm1(d) / d if d else mpf(1)


def pfun(s):
    """P(s) = 2 log2(e) atanh(sqrt s)/sqrt s."""
    if s == 0:
        return 2 / log(2)
    y = sqrt(s)
    return 2 / log(2) * atanh(y) / y


class Fit:
    def __init__(self, name, f, deg, a, b):
        self.name, self.deg, self.a, self.b = name, deg, mpf(a), mpf(b)
        self.coeffs, self.E = remez(f, deg, a, b)
        self.sup = certify(self.coeffs, f, a, b)
        # the bounds take the grid's maximum with 2^-10 of it to spare for the
        # gaps between the points
        self.bound = self.sup * (1 + mpf(2) ** -10)

    def line(self):
        return (f"{self.name}: degree {self.deg} minimax, levelled error 2^{float(log(self.E, 2)):.1f}, "
                f"certified sup norm 2^{float(log(self.sup, 2)):.1f} relative on 20,002 points")


# ---- kernels -------------------------------------------------------------------

def at110(fn):
    """Run fn at 110 digits whatever the caller's mp.dps (bounds.py runs at
    120): the fits' last bits depend on the working precision, and the
    constants must be the ones in the source."""
    def wrapped(*args, **kw):
        with mp.workdps(110):
            return fn(*args, **kw)
    return wrapped


class Kernels:
    @at110
    def __init__(self):
        rb = mpf(2) ** (-4 * EXP_LEVELS)
        self.fit_exp = Fit("2^r", lambda r: power(2, r), EXP_DEG, 0, rb)
        ymax_n = mpf(2) ** -8 / (2 - mpf(2) ** -8)
        ymax_w = mpf(2) ** -4 / (2 - mpf(2) ** -4)
        self.fit_ln = Fit("P(s)", pfun, LN_DEG, 0, ymax_n ** 2)
        self.fit_lnw = Fit("P(s), wide", pfun, LNW_DEG, 0, ymax_w ** 2)
        h8 = mpf(2) ** -8
        self.fit_em1 = Fit("(e^d - 1)/d", em1fun, EM1_DEG, -h8, h8)
        self.hexp = Horner(self.fit_exp.coeffs, 256, 255, rb, self.fit_exp.bound, power(2, rb), "exp2frac", "x")
        self.hln = Horner(self.fit_ln.coeffs, SS, 254, ymax_n ** 2, self.fit_ln.bound, pfun(ymax_n ** 2), "lnp", "t")
        self.hlnw = Horner(self.fit_lnw.coeffs, SS, 254, ymax_w ** 2, self.fit_lnw.bound, pfun(ymax_w ** 2), "lnpw", "t")
        self.hem1 = Horner(self.fit_em1.coeffs, 256, 254, h8, self.fit_em1.bound, em1fun(h8), "expm1series", "x", signed=True)
        # exp tables: (2^(j/16^(l+1)) - 1) 2^256, rounded
        self.etab = [[int(nint((power(2, mpf(j) / 16 ** (lv + 1)) - 1) * power(2, 256))) for j in range(16)]
                     for lv in range(EXP_LEVELS)]
        # log tables at 2^-256: log2(1 + i/16), log2(1 + i/256)
        self.ltab = [[int(nint(log(1 + mpf(i) / 16 ** (lv + 1), 2) * power(2, 256))) for i in range(16)]
                     for lv in range(2)]
        self.LN2H = int(nint(log(2) / 2 * power(2, 256)))
        self.LN2 = q(log(2))
        log2e = 1 / log(2)
        self.LOG2E_HI = int(mp.floor(log2e * WS))
        self.LOG2E_LO = int(nint((log2e * WS - self.LOG2E_HI) * WS))

    # 2^f -----------------------------------------------------------------------
    def exp2frac(self, f: int) -> int:
        """2^f for f in [0, 2^254) at 2^-254, result in [2^254, 2^255)."""
        rb = 254 - 4 * EXP_LEVELS
        x = (f & ((1 << rb) - 1)) << 2
        v = self.hexp.eval(x)
        for lv in reversed(range(EXP_LEVELS)):
            j = (f >> (250 - 4 * lv)) & 15
            if j:
                v = hi(v, self.etab[lv][j]) + v
        return v >> 1

    def exp2frac_bound(self):
        """|v - 2^f 2^254| in units of 2^-254: the Horner's bound at 2^-255,
        each level Delta T + 1/2 (the table's rounding times v < 2^256) + 1
        (the floor), the final halving and its floor."""
        e = self.hexp.err
        for lv in reversed(range(EXP_LEVELS)):
            e = e * power(2, mpf(15) / 16 ** (lv + 1)) + mpf(3) / 2
        return e / 2 + 1

    # log2 ----------------------------------------------------------------------
    def log2m(self, mm: int) -> int:
        """log2(mm) for mm in [2^254, 2^255) at 2^-254, result in [0, 2^254]."""
        w = mm - WS
        i = w >> 250
        w = ((w - (i << 250)) << 6) // (16 + i)          # w1 at 2^-256, below 2^252
        acc = self.ltab[0][i]
        i = w >> 248
        w = ((w - (i << 248)) << 8) // (256 + i)         # w2 at 2^-256, below 2^248
        acc += self.ltab[1][i]
        y = divh(w << 2, (1 << 255) + (w >> 2))          # y at 2^-259
        p = self.hln.eval(hi(y, y))
        return (acc + (hi(y, p) >> 1)) >> 2

    def log2m_bound(self):
        """|log2m - log2(mm) 2^254| in units of 2^-254 (the derivation in
        log2m's Yul comment)."""
        L2E = 1 / log(2)
        tables = mpf(1) / 4                              # two roundings at 2^-256
        floors = 2 * L2E / 4                             # w1 and w2's floors, under 2^-256 each, through 1/(1 + w) ln 2
        ymax = mpf(2) ** -8 / (2 + 0)
        pm = pfun(ymax ** 2)
        ydiv = pm * (power(2, -SY) + ymax * power(2, -255)) * power(2, 254)
        poly = (self.hln.err + 1) * ymax                 # P's bound and s's floor, times y
        prod = mpf(1) / 4                                # hi(y, p) >> 1 at 2^-256
        return tables + floors + ydiv + poly + prod + 1   # the final floor

    # ln(1 + d)/d near one ---------------------------------------------------------
    def ln1pk(self, df: int, wide: int) -> int:
        """ln(1 + d)/d at 2^-254 for a signed d at 2^-254, |d| < 2^-8 (wide:
        2^-4)."""
        sd = signed(df)
        a = abs(sd)
        y = divh(a << 4, (1 << 255) + sd)               # |y| at 2^-259
        t = hi(y, y)
        p = (self.hlnw if wide else self.hln).eval(t)
        yp = hi(y, p) >> 3
        p = p - yp if sd >= 0 else p + yp
        return hi(p, self.LN2H)

    def ln1pseries(self, df: int) -> int:
        return self.ln1pk(df, 0)

    def ln1pwide(self, df: int) -> int:
        return self.ln1pk(df, 1)

    def ln1pk_bound(self, wide: int):
        """|ln1pk - ln(1 + d)/d 2^254| in units of 2^-254."""
        h = self.hlnw if wide else self.hln
        ymax = (mpf(2) ** -4 if wide else mpf(2) ** -8) / (2 - (mpf(2) ** -4 if wide else mpf(2) ** -8))
        pm = pfun(ymax ** 2)
        c = log(2) / 2 * (1 + ymax)                       # (ln 2/2)(1 - y) at most
        ydiv = pm * power(2, -SY) * power(2, 254) * log(2) / 2    # y's floor, through (ln 2/2) P
        poly = (h.err + 1) * c                            # P's bound and s's floor
        yp = 1 * log(2) / 2                               # floor of y P at 2^-254
        ln2h = pm * (1 + ymax) / 2 * power(2, -256) * power(2, 254)   # LN2H's rounding times p
        return ydiv + poly + yp + ln2h + 1                # the final floor

    def expm1series(self, df: int) -> int:
        """(e^d - 1)/d at 2^-254 for a signed d at 2^-254, |d| < 2^-8: the
        minimax polynomial on d at 2^-256, signed Horner."""
        return self.hem1.eval(signed(df) << 2)

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
            P = md * p
            return normround(sd, BIAS + ud, P >> 236)
        Lm, Ls = self.log2pair(e, m)
        r = mulw(Lm, self.LN2)
        rs = signed(r)
        return normround(1 if rs < 0 else 0, BIAS + Ls + 254, abs(rs))

    def model_pow(self, x: int, y: int) -> int:
        sx, ex, mx = unpack(x)
        sy, ey, my = unpack(y)
        assert ex and not sx and ey
        band = self.nearone(x)
        if band is not None:
            sd, ud, md = band
            p = self.ln1pseries(self.tofixed254(sd, ud, md))
            Lm = mulwu(mulwu(md << 17, p), self.LOG2E_HI)
            Ls = ud - 253
            Lneg = sd
        else:
            Lm, Ls = self.log2pair(ex, mx)
            Lneg = 1 if signed(Lm) < 0 else 0
            Lm = abs(signed(Lm))
        P = Lm * my
        es = Ls + (ey - BIAS) - 236
        qsh = -es
        if qsh < 254:
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
        df = self.tofixed254(s, u, m)
        P = m * (self.ln1pseries(df) if u < -8 else self.ln1pwide(df))
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


_BUILT = None


def build():
    """The kernels (fitted once per process), and the two kernel degrees."""
    global _BUILT
    if _BUILT is None:
        _BUILT = Kernels()
    return _BUILT, EXP_DEG, LN_DEG


# ---- the Yul -----------------------------------------------------------------------

def emit_yul(K: Kernels) -> str:
    out = []
    he, hl, hw = K.hexp, K.hln, K.hlnw
    rb = 254 - 4 * EXP_LEVELS
    eb = K.exp2frac_bound()
    out.append(
        f"/// 2^f for f in [0, 1) at 2^-254, result at 2^-254 in [1, 2), unrounded:\n"
        f"/// f = j1/16 + j2/256 + r, 2^f = T1[j1] T2[j2] 2^r. 2^r on [0, 2^-8) is\n"
        f"/// the degree-{EXP_DEG} minimax polynomial (kernel254.py; certified sup norm\n"
        f"/// 2^{float(log(K.fit_exp.sup, 2)):.1f} relative), Horner at 2^-255 on r at 2^-256 with each\n"
        f"/// product's high word in line, the top {he.ncheap} steps in one word (their\n"
        f"/// truncation, times r^j, is under 2^{float(log(he.extra, 2)):.1f} in all); each table level\n"
        f"/// adds hi(v, (T - 1) 2^256), T - 1 rounded at 2^-256, the inner level\n"
        f"/// first; the result floored to 2^-254. Within {float(eb):.2f} units of 2^-254: the\n"
        f"/// Horner {float(he.err):.2f} units of 2^-255, each level Delta T + 1/2 + 1, then\n"
        f"/// halved, plus the floor. Unsigned throughout; two table tests of four\n"
        f"/// branches each in place of release two's 15-way switch.\n"
        f"function exp2frac(f) -> r {{\n"
        f"    let x := shl(2, and(f, {hx((1 << rb) - 1)}))")
    out += ["    " + l for l in he.yul("r")]
    for lv in reversed(range(EXP_LEVELS)):
        sh = 250 - 4 * lv
        expr = f"and(shr({sh}, f), 15)" if lv else f"shr({sh}, f)"
        out.append(f"    let j{lv + 1} := {expr}")
        out += tree(f"j{lv + 1}", lambda j, lv=lv: hiline("r", "r", hx(K.etab[lv][j]), "r") if j else "")
    out.append("    r := shr(1, r)\n}\n")

    lb = K.log2m_bound()
    out.append(
        f"/// log2(mm) for a mantissa mm in [1, 2) at 2^-254, result at 2^-254 in [0, 1],\n"
        f"/// unrounded. Two additive levels by word-only operations: i = floor(16 w)\n"
        f"/// for mm = 1 + w, then 1 + w1 = (1 + w)/(1 + i/16) exactly as w1 = 16 (w -\n"
        f"/// i/16)/(16 + i), one shift and one div by a small integer, floored at\n"
        f"/// 2^-256, and log2(1 + i/16) (at 2^-256, rounded) added from a table; then\n"
        f"/// the same by 1 + i/256, leaving w2 in [0, 2^-8). log2(1 + w2) = y P(y^2),\n"
        f"/// y = w2/(2 + w2) at 2^-259 by one divh, P = 2 log2(e) atanh(sqrt s)/sqrt s\n"
        f"/// by lnp. Within {float(lb):.2f} units of 2^-254: the tables 1/4, w1 and w2's floors\n"
        f"/// (under 2^-256 each) 2 log2(e)/4, y's floor and its divisor's, P's\n"
        f"/// bound times y, y P's floor 1/4 and the final floor 1\n"
        f"/// (kernel254.py; release two's twelve stages were bounded at 37).\n"
        f"function log2m(mm) -> r {{\n"
        f"    let acc, w := log2lv(sub(mm, {hx(WS)}))\n"
        f"    let y := divh(shl(2, w), add({hx(1 << 255)}, shr(2, w)))\n"
        f"    let p := lnp(y)\n"
        f"    {hiset('w', 'y', 'p')}\n"
        f"    r := shr(2, add(acc, shr(1, w)))\n}}\n")
    out.append(
        f"/// log2m's two table levels for w = mm - 1 at 2^-254: acc the sum of the two\n"
        f"/// table words at 2^-256, v = w2 floored at 2^-256 (the middle stage's\n"
        f"/// mlog2m reads the same words and redoes the reductions exactly).\n"
        f"function log2lv(w) -> acc, v {{\n"
        f"    let i := shr(250, w)\n"
        f"    v := div(shl(6, sub(w, shl(250, i))), add(16, i))")
    out += tree("i", lambda j: f"acc := {hx(K.ltab[0][j])}" if j else "")
    out.append("    i := shr(248, v)\n"
               "    v := div(shl(8, sub(v, shl(248, i))), add(256, i))")
    out += tree("i", lambda j: f"acc := add(acc, {hx(K.ltab[1][j])})" if j else "")
    out.append("}\n")

    for h, nm, fit, dom in ((hl, "lnp", K.fit_ln, "2^-8/(2 - 2^-8)"), (hw, "lnpw", K.fit_lnw, "2^-4/(2 - 2^-4)")):
        out.append(
            f"/// P(y^2) = 2 log2(e) atanh(y)/y at 2^-254 for y at 2^-259, |y| below\n"
            f"/// {dom}: the degree-{fit.deg} minimax polynomial in s = y^2 (kernel254.py;\n"
            f"/// certified sup norm 2^{float(log(fit.sup, 2)):.1f} relative), Horner on s at 2^-262 with\n"
            f"/// the products' high words in line, the top {h.ncheap} steps in one word; within\n"
            f"/// {float(h.err):.2f} units. No Taylor coefficients: the fit is a Remez exchange.\n"
            f"function {nm}(y) -> p {{")
        out.append("    let t := 0")
        out.append("    " + hiset("t", "y", "y"))
        out += ["    " + l for l in h.yul("p")]
        out.append("}\n")

    nb, wb = K.ln1pk_bound(0), K.ln1pk_bound(1)
    out.append(
        f"/// ln(1 + d)/d at 2^-254 for a signed d at 2^-254, |d| < 2^-8 (wide = 0)\n"
        f"/// or 2^-4 (wide = 1): 2 atanh(y)/d with y = d/(2 + d) at 2^-259 by one\n"
        f"/// divh, and 2/(2 + d) = 1 - y, so (ln 2/2)(1 - y) P(y^2), P by lnp or lnpw.\n"
        f"/// y holds d's sign on a fixed grid and only 1 - y and y^2 enter, so the\n"
        f"/// value keeps its relative precision however small d is: within {float(nb):.2f}\n"
        f"/// units (wide {float(wb):.2f}): y's floor, P's bound, y P's floor, ln 2/2's rounding\n"
        f"/// and the final floor (kernel254.py).\n"
        f"function ln1pk(df, wide) -> p {{\n"
        f"    let a := df\n"
        f"    if slt(df, 0) {{ a := sub(0, df) }}\n"
        f"    let y := divh(shl(4, a), add({hx(1 << 255)}, df))\n"
        f"    switch wide\n"
        f"    case 0 {{ p := lnp(y) }}\n"
        f"    default {{ p := lnpw(y) }}\n"
        f"    let yp := 0\n"
        f"    {hiset('yp', 'y', 'p')}\n"
        f"    yp := shr(3, yp)\n"
        f"    switch slt(df, 0)\n"
        f"    case 0 {{ p := sub(p, yp) }}\n"
        f"    default {{ p := add(p, yp) }}\n"
        f"    {hiset('p', 'p', hx(K.LN2H))}\n}}\n")
    out.append("/// ln(1 + d)/d for |d| < 2^-8: ln1pk on lnp.\n"
               "function ln1pseries(df) -> p {\n    p := ln1pk(df, 0)\n}\n")
    out.append("/// ln(1 + d)/d for |d| < 2^-4: ln1pk on lnpw.\n"
               "function ln1pwide(df) -> p {\n    p := ln1pk(df, 1)\n}\n")
    he1, fe1 = K.hem1, K.fit_em1
    out.append(
        f"/// (e^d - 1)/d at 2^-254 for a signed d at 2^-254, |d| < 2^-8: the\n"
        f"/// degree-{fe1.deg} minimax polynomial on [-2^-8, 2^-8] (kernel254.py; certified\n"
        f"/// sup norm 2^{float(log(fe1.sup, 2)):.1f} relative), release three's 24-term Taylor series\n"
        f"/// before it. Signed Horner on d at 2^-256: every partial sum is positive,\n"
        f"/// the top {he1.ncheap} steps in one word by mul and sar, the others the high word\n"
        f"/// less p when d < 0 (ng); within {float(he1.err):.2f} units of 2^-254.\n"
        f"function expm1series(df) -> p {{\n"
        f"    let x := shl(2, df)\n"
        f"    let ng := slt(df, 0)")
    out += ["    " + l for l in he1.yul("p")]
    out.append("}\n")
    return "\n".join(out)


def check_source(K: Kernels) -> bool:
    """True when FP19.yul.src holds the emitted kernels verbatim, so the
    models here are the Yul that runs."""
    src = (Path(__file__).resolve().parents[3] / "contracts/src/fp19/FP19.yul.src").read_text()
    ok = all(b.strip("\n") in src for b in emit_yul(K).split("\n\n") if b.strip())
    print(f"FP19.yul.src holds kernel254.py's Yul verbatim: {'yes' if ok else 'NO'}")
    return ok


# ---- measurement -----------------------------------------------------------------

def rand_float(rng, lo, hi_, s=None):
    u = rng.randint(lo, hi_)
    sg = rng.getrandbits(1) if s is None else s
    return (sg << 255) | ((u + BIAS) << 236) | rng.getrandbits(236)


def measure_kernels(K: Kernels, rng, n=4000):
    """Each kernel against mpmath at 110 digits on random and edge inputs:
    the largest error seen, the bound, and their ratio."""
    rows = []
    rb = 254 - 4 * EXP_LEVELS
    fs = [rng.getrandbits(W) for _ in range(n)]
    fs += [1, WS - 1, (1 << rb) - 1, 1 << rb, WS >> 1, (WS >> 4) - 1, WS >> 4, (WS * 15) >> 4, ((WS * 15) >> 4) + (1 << rb) - 1]
    fs += [(j1 << 250) | (j2 << 246) | rng.choice([0, 1, (1 << rb) - 1, rng.getrandbits(rb)]) for j1 in range(16) for j2 in range(16)]
    worst = max(abs(mpf(K.exp2frac(f)) - power(2, mpf(f) / WS) * WS) for f in fs if f)
    rows.append(("exp2frac", len(fs), worst, K.exp2frac_bound()))
    ms = [WS + rng.getrandbits(W) for _ in range(n)]
    ms += [WS, WS + 1, 2 * WS - 1, WS + (WS >> 1), WS + (WS >> 100)]
    ms += [WS + (i1 << 250) + (i2 << 246) + rng.choice([0, 1, (1 << 246) - 1, rng.getrandbits(246)]) for i1 in range(16) for i2 in range(16)]
    worst = max(abs(mpf(K.log2m(m)) - log(mpf(m) / WS, 2) * WS) for m in ms)
    rows.append(("log2m", len(ms), worst, K.log2m_bound()))
    for wide, lim in ((0, 8), (1, 4)):
        ds = []
        for _ in range(n):
            e = rng.randint(lim, 250)
            v = rng.getrandbits(W - e)
            ds.append(v if rng.getrandbits(1) else (-v) & MASK)
        ds += [(1 << (W - lim)) - 1, (-((1 << (W - lim)) - 1)) & MASK, 1, MASK, 0]
        worst = mpf(0)
        for df in ds:
            d = mpf(signed(df)) / WS
            exact = (log(1 + d) / d if d else mpf(1)) * WS
            worst = max(worst, abs(mpf(K.ln1pk(df, wide)) - exact))
        rows.append(("ln1pwide" if wide else "ln1pseries", len(ds), worst, K.ln1pk_bound(wide)))
    ds = []
    for _ in range(n):
        e = rng.randint(8, 250)
        v = rng.getrandbits(W - e)
        ds.append(v if rng.getrandbits(1) else (-v) & MASK)
    ds += [(1 << (W - 8)) - 1, (-((1 << (W - 8)) - 1)) & MASK, 1, MASK, 0]
    worst = mpf(0)
    from mpmath import expm1 as mexpm1
    for df in ds:
        d = mpf(signed(df)) / WS
        exact = (mexpm1(d) / d if d else mpf(1)) * WS
        worst = max(worst, abs(mpf(K.expm1series(df)) - exact))
    rows.append(("expm1series", len(ds), worst, K.hem1.err))
    print(f"{'kernel':12} {'n':>6} {'max error':>10} {'bound':>7} {'ratio':>7}   (units of 2^-254)")
    bad = False
    for nm, cnt, worst, bound in rows:
        r = float(worst / bound)
        bad |= r >= 1
        print(f"{nm:12} {cnt:6d} {float(worst):10.3f} {float(bound):7.3f} {r:7.4f}{'  EXCEEDS' if r >= 1 else ''}")
    return bad


def measure_ops(K: Kernels, rng):
    mp.dps = 110
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
    K, _, _ = build()
    if "--yul" in argv:
        print(emit_yul(K))
        return 0
    if "--check" in argv:
        return 0 if check_source(K) else 1
    for ft in (K.fit_exp, K.fit_ln, K.fit_lnw, K.fit_em1):
        print(ft.line())
    for h in (K.hexp, K.hln, K.hlnw, K.hem1):
        print(f"{h.name}: {len(h.C) - 1} steps, {h.ncheap} in one word (b = {h.b}, their truncation "
              f"2^{float(log(h.extra, 2)) if h.extra else float('-inf'):.1f}), bound {float(h.err):.3f} units of 2^-{h.rho}")
    print("\nkernels at 2^-254, exact-integer model against mpmath:")
    bad = measure_kernels(K, random.Random(254))
    print("\nthe ops, modelled as the Yul runs them, against mpmath:")
    measure_ops(K, random.Random(254))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

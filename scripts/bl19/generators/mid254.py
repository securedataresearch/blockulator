#!/usr/bin/env python3
"""BL19's middle stage: log2 to about 2^-272, between the kernels' 2^-254
and the second stage's 2^-510, modelled in exact integers as the Yul runs
it, with its fit, its bounds and the Yul text it needs.

    uv run scripts/bl19/generators/mid254.py            # fit, certify, measure the kernels
    uv run scripts/bl19/generators/mid254.py --yul      # print the Yul
    uv run scripts/bl19/generators/mid254.py --check    # does BL19.yul.src hold that Yul verbatim?

pow, powu and compound round 2^(y log2 x) from the 2^f kernel with a bound
that grows with |y log2 x|: the kernels give log2 x within a few units of
2^-254, and t = y log2 x carries that error times |y|. When the bound
reaches the rounding boundary the middle stage recomputes log2 x within
2^-272 relative (near one) or 2^-279 absolute (off it), forms t exactly from
it, and runs the same 2^f kernel: t's error is then under 2 units for every
|t| below 2^19 (the format's range, which the fast stage has checked), so
the rounding test takes 10 units and fires about once in 13,000 calls. Only
then the second stage runs.

mratio, ln(1 + d)/d for |d| < 2^-8 given as two words at 2^-512 (exact for
near one's d = x - 1 and for the reduced mantissa below): y = d/(2 + d) by
one divh on d's top word (within 2^-257), then the exact residual e = |d| -
y0 (2 + sigma |d|) in two words and y = y0 + e (1 - sigma y0)/2, since
1/(2 + d) = (1 - y)/2; y is then within a few units of 2^-510. ln(1 + d) =
2 atanh(y) = 2 y (1 + Q), Q(s) = atanh(sqrt s)/sqrt s - 1, s = y^2, and
ln(1 + d)/d = (1 - y)(1 + Q) = 1 - y + q with q = Q - y Q in one word at
2^-275 (q < 2^-19.5): s/3 from y0's exact square, s^2 R2(s) with R2 the
degree-11 minimax polynomial of (Q - s/3)/s^2 on [0, (2^-8/(2 - 2^-8))^2]
(Remez, minimax.py), Horner on s at 2^-256. No Taylor coefficients: the fit
is a Remez exchange.

mlog2m, log2 of a mantissa mm in [1, 2) as two words at 2^-510: log2m's two
table levels (log2lv, the same hi words at 2^-256) with each reduction kept
exact in two words (a long division by 16 + i and by 256 + i), each table
value completed by a signed 64-bit low part at 2^-320, and log2(1 + w2) =
w2 mratio(w2) log2 e.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from mpmath import mp, mpf, log, power, nint, log1p

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernel254 as K  # noqa: E402
from minimax import remez, certify  # noqa: E402
from horner import Horner, hiset  # noqa: E402

MASK = K.MASK
WS = K.WS
R2_DEG = 11
SIG = 256                    # s at 2^-256 for R2's Horner
RHO = 241                    # R2 at 2^-241, so s^2 R2 lands at 2^-275
YMAX = mpf(2) ** -8 / (2 - mpf(2) ** -8)
SMAX = YMAX ** 2
L2E_H = 0x5c551d94ae0bf85ddf43ff68348e9f4475abbd546eb4ad2c45928b3668d09923
L2E_L = 0xef0e21fbaa8bb66b126c97bae0b5f059f5485cf30625484fe25fd781a9ef9cd9
ERR_MID = 10                 # rbadm's bound on v, units of 2^-254 (mid_bound)


def r2fun(s):
    """(atanh(sqrt s)/sqrt s - 1 - s/3)/s^2 = sum s^k/(2k + 5), evaluated as
    that convergent sum (the function, not a fit's coefficients)."""
    s = mpf(s)
    tot, k, t = mpf(0), 0, mpf(1)
    while True:
        term = t / (2 * k + 5)
        tot += term
        if abs(term) < mpf(2) ** -420:
            return tot
        k += 1
        t *= s


# ---- the wide primitives, as the Yul does them -------------------------------------

def wmul(a: int, b: int) -> int:
    """BL19's wmul on 512-bit A, B at 2^-510: the four word products, the
    lowest through its high word."""
    ah, al, bh, bl = a >> 256, a & MASK, b >> 256, b & MASK
    p = ah * bh
    rh = (p >> 254) & MASK
    rl = (p << 2) & MASK
    q = ((ah * bl) >> 256) + ((al * bh) >> 256)
    t0 = (ah * bl & MASK) + (al * bh & MASK)
    q = (q + (t0 >> 256)) & MASK
    t0 &= MASK
    p0 = ((q << 2) | (t0 >> 254)) & MASK
    s = rl + p0
    rl = s & MASK
    rh = (rh + (q >> 254) + (s >> 256)) & MASK
    p0 = ((al * bl) >> 256) >> 254
    s = rl + p0
    rl = s & MASK
    rh = (rh + (s >> 256)) & MASK
    return (rh << 256) | rl


def hi(a: int, b: int) -> int:
    """floor(a b / 2^256); a may be signed (the Yul's mulhi less b when a < 0)."""
    return (a * b) >> 256


def sdiv(a: int, b: int) -> int:
    q = abs(a) // b
    return -q if a < 0 else q


class Mid:
    @K.at110
    def __init__(self):
        self.K, _, _ = K.build()
        self.coeffs, self.E = remez(r2fun, R2_DEG, 0, SMAX, rel=True)
        self.sup = certify(self.coeffs, r2fun, 0, SMAX)
        self.fit_bound = self.sup * (1 + mpf(2) ** -10)
        self.h = Horner(self.coeffs, SIG, RHO, SMAX, self.fit_bound, r2fun(SMAX), "mratio", "v")
        # the table values' low parts: log2(1 + i/16^(l+1)) - hi 2^-256 at 2^-320, signed
        self.lo = []
        for lv in range(2):
            row = []
            for i in range(16):
                v = log(1 + mpf(i) / 16 ** (lv + 1), 2) * power(2, 256) - self.K.ltab[lv][i]
                c = int(nint(v * power(2, 64)))
                assert -(1 << 63) <= c < 1 << 63
                row.append(c)
            self.lo.append(row)

    def line(self):
        return (f"R2: degree {R2_DEG} minimax, levelled error 2^{float(log(self.E, 2)):.1f}, certified sup norm "
                f"2^{float(log(self.sup, 2)):.1f} relative; Horner {self.h.ncheap} of {R2_DEG} steps in one word, "
                f"within {float(self.h.err):.2f} units of 2^-{RHO}")

    # ---- the kernels ---------------------------------------------------------------
    def mratio(self, sg: int, dh: int, dl: int) -> int:
        """ln(1 + d)/d at 2^-510 for d = (-1)^sg (dh 2^256 + dl) 2^-512."""
        A = (dh << 256) | dl
        den = (1 << 255) - (dh >> 2) if sg else (1 << 255) + (dh >> 2)
        y0 = K.divh(dh << 6, den)                         # y at 2^-263
        ya = (y0 * A) >> 263                              # y0 |d| at 2^-512
        E = A - (y0 << 250) + (ya if sg else -ya)         # |d| - y0 (2 + sigma |d|)
        e = E >> 4                                        # at 2^-508, signed
        assert -(1 << 255) <= e < 1 << 255
        c = hi(e, y0) >> 6                                # e y0 2^-262
        corr = 2 * e + (c if sg else -c)                  # e (1 - sigma y0)/2 at 2^-510
        assert -(1 << 255) <= corr < 1 << 255
        Y = (y0 << 247) + corr
        assert 0 <= Y < 1 << 512
        sq = y0 * y0                                      # y0^2 at 2^-526
        t = hi(corr, y0)                                  # y0 corr at 2^-517
        s = (sq >> 253) + (t >> 242)                      # s at 2^-273
        assert 0 <= s < 1 << 256
        q3 = ((sq // 3) >> 251) + sdiv(t >> 241, 3)       # s/3 at 2^-275
        p = self.h.eval(s >> 17)                          # R2 at 2^-241, on s at 2^-256
        s2 = hi(s, s)                                     # s^2 at 2^-290
        Q = q3 + hi(s2, p)                                # at 2^-275
        assert 0 <= Q < 1 << 256
        yq = hi(y0, Q) >> 7                               # y Q at 2^-275
        q = Q + yq if sg else Q - yq
        R = (1 << 510) + (q << 235)
        return R + Y if sg else R - Y

    def mlog2s(self, s: int, u: int, m: int):
        """|log2(1 + d)| for d = (-1)^s m 2^(u - 236), |d| < 2^-8 (m need not
        be normalised), as (lh, ll) and the scale le."""
        k = u + 276
        A = m << k if k >= 0 else m >> -k
        P = self.mratio(s, A >> 256, A & MASK)
        P = wmul(P, (L2E_H << 256) | L2E_L)
        return norm3(P * m, u - 746)

    def mlog2m(self, mm: int) -> int:
        """log2(mm) for mm in [2^254, 2^255) at 2^-254, as 512 bits at 2^-510."""
        w = mm - WS
        i1 = w >> 250
        d = 16 + i1
        n = (w - (i1 << 250)) << 6
        qh = n // d
        r = n % d
        x = r << 248
        ql = ((x // d) << 8) | (((x % d) << 8) // d)
        acc = self.K.ltab[0][i1]
        i2 = qh >> 248
        acc += self.K.ltab[1][i2]
        d = 256 + i2
        ah = (((qh - (i2 << 248)) << 8) | (ql >> 248)) & MASK
        al = (ql << 8) & MASK
        qh = ah // d
        x = ((ah % d) << 247) | (al >> 9)
        q1 = x // d
        x = ((x % d) << 9) | (al & 511)
        ql = (q1 << 9) | (x // d)
        lo = self.lo[0][i1] + self.lo[1][i2]
        R = self.mratio(0, qh, ql)
        R = wmul(R, (L2E_H << 256) | L2E_L)
        W2 = ((qh << 256) | ql) >> 2
        F = wmul(W2, R)
        L = (acc << 254) + F + (lo << 190)
        assert 0 <= L < 1 << 512
        return L


def norm3(N: int, eadj: int):
    """BL19's norm3 on a 768-bit N: a 512-bit mantissa with its top bit at
    511 and the scale, adjusted as the caller does."""
    assert N > 0
    n2, n1, n0 = N >> 512, (N >> 256) & MASK, N & MASK
    if n2:
        e = K.msb(n2) + 1
        return N >> e, e + eadj
    if n1 == 0:
        e = K.msb(n0) - 511
        return (n0 << (255 - K.msb(n0))) << 256, e + eadj
    e = K.msb(n1) - 255
    return (N << -e) & ((1 << 512) - 1), e + eadj


# ---- the bounds ------------------------------------------------------------------

def ratio_bound(M: Mid):
    """|mratio - ln(1 + d)/d| relative, analytic. In units of 2^-275 on q:
    s/3's two floors and the cross term's floor and truncated division (4),
    the dropped corr^2 (under 2^-20), s^2 R2's floor 1, s^2's floor and s's
    two floors at 2^-273 through s^2 times R2, R2 at s floored to 2^-256, the
    Horner's units of 2^-241
    and the fit's times s^2 at 2^-36, y Q's floor 1 and the dropped corr Q
    (|corr| < 2^254 at 2^-510, so under 2^-19.5 units); Y within 3 units of
    2^-510 (the floors of ya, e and c, and the residual's second order); all
    over ln(1 + d)/d > 1 - 2^-9."""
    r2 = r2fun(SMAX)
    s2 = SMAX ** 2
    units = (4 + mpf(2) ** -20 + 1 + r2 * (power(2, -15) + 4 * SMAX * power(2, 2))
             + s2 * power(2, 34) * M.h.err + s2 * r2 * M.fit_bound * power(2, 275)
             + power(2, -18) + 1 + 1)
    tot = units * power(2, -275) + 3 * power(2, -510)
    return tot / (1 - YMAX)


def mlog2m_bound(M: Mid, rb):
    """|mlog2m - log2 mm| absolute: the two table values' residuals (2^-321
    each), w1 and w2's floors at 2^-512 through log2, w2 < 2^-8 times
    mratio's relative bound times log2 e, two wmuls and the low part's
    placement."""
    u = power(2, -510)
    L2E = 1 / log(2)
    return 2 * power(2, -321) + 4 * power(2, -512) * L2E + power(2, -8) * L2E * rb + 6 * u


def mid_bound(M: Mid, rb, lb):
    """v's bound in units of 2^-254 for the middle stage: the 2^f kernel,
    f's floor at 2^-254 (2 ln 2 at most), and t's error through 2^f ln 2:
    |t| < 2^19 near one (mratio's relative bound plus log2 e's wmul and the
    normalisation, 2^-500), |y| < 2^26.5 off it (|log2 x| >= log2(1 + 2^-8),
    or the same for 1 + rate) times mlog2m's absolute bound."""
    t_near = power(2, 19) * (rb + power(2, -500))
    t_off = power(2, 26.5) * lb
    dt = max(t_near, t_off) * power(2, 254)
    return M.K.exp2frac_bound() + 2 * log(2) * (1 + dt)


# ---- measurement -----------------------------------------------------------------

def measure(M: Mid, rng, n=3000):
    """Largest relative error of mratio and absolute error of mlog2m."""
    mp.dps = 130
    worst_r = mpf(0)
    for _ in range(n):
        sg = rng.getrandbits(1)
        kind = rng.random()
        if kind < 0.3:
            A = rng.randrange(1, 1 << 504)                 # up to 2^-8
        elif kind < 0.5:
            A = (1 << 504) - rng.randrange(1, 1 << 300)    # the edge
        else:
            A = rng.randrange(1, 1 << rng.randint(1, 504))
        d = mpf(A) / power(2, 512) * (-1 if sg else 1)
        got = M.mratio(sg, A >> 256, A & MASK)
        exact = log1p(d) / d
        worst_r = max(worst_r, abs(mpf(got) / power(2, 510) - exact) / exact)
    worst_l = mpf(0)
    for _ in range(n):
        mm = (1 << 254) + rng.randrange(0, 1 << 254)
        if rng.random() < 0.3:
            mm = (1 << 254) + (rng.randrange(0, 1 << 237) << 17)
        got = M.mlog2m(mm)
        exact = log(mpf(mm) / power(2, 254), 2)
        worst_l = max(worst_l, abs(mpf(got) / power(2, 510) - exact))
    return worst_r, worst_l


# ---- the Yul -----------------------------------------------------------------------

def emit_yul(M: Mid) -> str:
    h = M.h
    rb = ratio_bound(M)
    lb = mlog2m_bound(M, rb)
    out = []
    lo_words = []
    for lv in range(2):
        words = []
        for wv in range(4):
            v = 0
            for j in range(4):
                v |= (M.lo[lv][4 * wv + j] & ((1 << 64) - 1)) << (64 * j)
            words.append(v)
        lo_words.append(words)
    out.append(
        f"/// ln(1 + d)/d as two words at 2^-510 for d = (-1)^sg (dh 2^256 + dl) 2^-512,\n"
        f"/// |d| < 2^-8 (mid254.py): y = d/(2 + d) by one divh on dh (within 2^-257),\n"
        f"/// then the exact residual e = |d| - y0 (2 + sigma |d|) and y = y0 + e (1 -\n"
        f"/// sigma y0)/2, as 1/(2 + d) = (1 - y)/2; ln(1 + d)/d = 1 - y + q, q = Q - y Q\n"
        f"/// at 2^-275, Q = atanh(y)/y - 1 = s/3 + s^2 R2(s), s = y^2: s/3 from y0's\n"
        f"/// exact square, R2 the degree-{R2_DEG} minimax polynomial (certified sup norm\n"
        f"/// 2^{float(log(M.sup, 2)):.1f} relative), Horner on s at 2^-256, the top {h.ncheap} steps in one\n"
        f"/// word. Within 2^{float(log(rb, 2)):.1f} relative, however small d is. No Taylor\n"
        f"/// coefficients.\n"
        f"function mratio(sg, dh, dl) -> rh, rl {{\n"
        f"    let den := add({K.hx(1 << 255)}, shr(2, dh))\n"
        f"    if sg {{ den := sub({K.hx(1 << 255)}, shr(2, dh)) }}\n"
        f"    let y0 := divh(shl(6, dh), den)\n"
        f"    let ah, al := wmulf(dh, dl, y0, 263)\n"
        f"    let eh, el := wsub(dh, dl, shr(6, y0), shl(250, y0))\n"
        f"    switch sg\n"
        f"    case 0 {{ eh, el := wsub(eh, el, ah, al) }}\n"
        f"    default {{ eh, el := wadd(eh, el, ah, al) }}\n"
        f"    let c := or(shl(252, eh), shr(4, el))\n"
        f"    let t := sar(6, sub(mulhi(c, y0), mul(slt(c, 0), y0)))\n"
        f"    switch sg\n"
        f"    case 0 {{ c := sub(shl(1, c), t) }}\n"
        f"    default {{ c := add(shl(1, c), t) }}\n"
        f"    t := sub(mulhi(c, y0), mul(slt(c, 0), y0))\n"
        f"    let p1, p0 := mul512(y0, y0)\n"
        f"    let s := add(or(shl(3, p1), shr(253, p0)), sar(242, t))\n"
        f"    p1, p0 := wdivs(p1, p0, 3)\n"
        f"    let q := add(or(shl(5, p1), shr(251, p0)), sdiv(sar(241, t), 3))\n"
        f"    let v := shr(17, s)\n"
        f"    let p := 0")
    out += ["    " + l for l in h.yul("p")]
    out.append(
        f"    {hiset('t', 's', 's')}\n"
        f"    {hiset('t', 't', 'p')}\n"
        f"    q := add(q, t)\n"
        f"    {hiset('t', 'y0', 'q')}\n"
        f"    switch sg\n"
        f"    case 0 {{ q := sub(q, shr(7, t)) }}\n"
        f"    default {{ q := add(q, shr(7, t)) }}\n"
        f"    rh := add({K.hx(1 << 254)}, shr(21, q))\n"
        f"    rl := shl(235, q)\n"
        f"    let yh := shr(9, y0)\n"
        f"    let yl := shl(247, y0)\n"
        f"    switch slt(c, 0)\n"
        f"    case 0 {{ yh, yl := wadd(yh, yl, 0, c) }}\n"
        f"    default {{ yh, yl := wsub(yh, yl, 0, sub(0, c)) }}\n"
        f"    switch sg\n"
        f"    case 0 {{ rh, rl := wsub(rh, rl, yh, yl) }}\n"
        f"    default {{ rh, rl := wadd(rh, rl, yh, yl) }}\n}}\n")
    for lv, nm in ((0, "l2lo1"), (1, "l2lo2")):
        out.append(
            f"/// log2(1 + i/{16 ** (lv + 1)}) less its table word at 2^-256, at 2^-320 (signed, 64 bits,\n"
            f"/// four to a word; mid254.py).\n"
            f"function {nm}(i) -> c {{\n"
            f"    let v := {K.hx(lo_words[lv][0])}\n"
            f"    switch shr(2, i)\n"
            f"    case 1 {{ v := {K.hx(lo_words[lv][1])} }}\n"
            f"    case 2 {{ v := {K.hx(lo_words[lv][2])} }}\n"
            f"    case 3 {{ v := {K.hx(lo_words[lv][3])} }}\n"
            f"    c := signextend(7, shr(shl(6, and(i, 3)), v))\n}}\n")
    out.append(
        f"/// log2(mm) for a mantissa mm in [1, 2) at 2^-254 as two words at 2^-510, within\n"
        f"/// 2^{float(log(lb, 2)):.1f} (mid254.py): log2m's two table levels (log2lv) with each\n"
        f"/// reduction kept exact in two words, a long division by 16 + i and by 256 + i\n"
        f"/// in word-size digits; each table value completed by its low part at 2^-320;\n"
        f"/// log2(1 + w2) = w2 mratio(w2) log2 e.\n"
        f"function mlog2m(mm) -> lh, ll {{\n"
        f"    let w := sub(mm, {K.hx(WS)})\n"
        f"    let acc, wf := log2lv(w)\n"
        f"    let i := shr(250, w)\n"
        f"    let d := add(16, i)\n"
        f"    let x := shl(6, sub(w, shl(250, i)))\n"
        f"    let qh := div(x, d)\n"
        f"    x := shl(248, mod(x, d))\n"
        f"    let ql := or(shl(8, div(x, d)), div(shl(8, mod(x, d)), d))\n"
        f"    let lo := l2lo1(i)\n"
        f"    i := shr(248, qh)\n"
        f"    d := add(256, i)\n"
        f"    let ah := or(shl(8, sub(qh, shl(248, i))), shr(248, ql))\n"
        f"    let al := shl(8, ql)\n"
        f"    qh := div(ah, d)\n"
        f"    x := or(shl(247, mod(ah, d)), shr(9, al))\n"
        f"    ql := div(x, d)\n"
        f"    x := or(shl(9, mod(x, d)), and(al, 511))\n"
        f"    ql := or(shl(9, ql), div(x, d))\n"
        f"    lo := add(lo, l2lo2(i))\n"
        f"    // sg = 0, as w < 2^254: a literal would have the optimizer specialise a\n"
        f"    // second copy of mratio for it\n"
        f"    let rh, rl := mratio(shr(254, w), qh, ql)\n"
        f"    rh, rl := wmul(rh, rl, {K.hx(L2E_H)}, {K.hx(L2E_L)})\n"
        f"    rh, rl := wmul(shr(2, qh), or(shl(254, qh), shr(2, ql)), rh, rl)\n"
        f"    lh, ll := wadd(shr(2, acc), shl(254, acc), rh, rl)\n"
        f"    switch slt(lo, 0)\n"
        f"    case 0 {{ lh, ll := wadd(lh, ll, 0, shl(190, lo)) }}\n"
        f"    default {{ lh, ll := wsub(lh, ll, 0, shl(190, sub(0, lo))) }}\n}}\n")
    return "\n".join(out)


def check_source(M: Mid) -> bool:
    src = (Path(__file__).resolve().parents[3] / "contracts/src/bl19/BL19.yul.src").read_text()
    ok = all(b.strip("\n") in src for b in emit_yul(M).split("\n\n") if b.strip())
    print(f"BL19.yul.src holds mid254.py's Yul verbatim: {'yes' if ok else 'NO'}")
    return ok


_BUILT = None


def build() -> Mid:
    global _BUILT
    if _BUILT is None:
        _BUILT = Mid()
    return _BUILT


def main(argv):
    M = build()
    if "--yul" in argv:
        print(emit_yul(M))
        return 0
    if "--check" in argv:
        return 0 if check_source(M) else 1
    print(M.line())
    rb = ratio_bound(M)
    lb = mlog2m_bound(M, rb)
    mb = mid_bound(M, rb, lb)
    print(f"mratio bound 2^{float(log(rb, 2)):.2f} relative; mlog2m bound 2^{float(log(lb, 2)):.2f} absolute; "
          f"the middle stage's v within {float(mb):.3f} units (rbadm takes {ERR_MID})")
    wr, wl = measure(M, random.Random(285))
    print(f"measured: mratio 2^{float(log(wr, 2)):.2f} relative, mlog2m 2^{float(log(wl, 2)):.2f} absolute")
    bad = wr > rb or wl > lb or mb > ERR_MID
    print("bounds hold" if not bad else "BOUND FAILS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

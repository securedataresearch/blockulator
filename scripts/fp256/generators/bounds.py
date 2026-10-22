#!/usr/bin/env python3
"""Release four: the error bounds behind FP256's rounding test, measured.

    uv run scripts/fp256/generators/bounds.py [n]     # n inputs per region (default 2000)

Also checks the depth of the second stage's continued fraction for erfc
(truncation below 2^-390 from y = 7).

Every op that is not exact by construction hands normround a fast value D
and, since release four, first asks rbad(D, err) whether D +- err could round
differently from D (the bits under the 237-bit significand within err of half
an ULP). When it could, a second stage recomputes the value in two words at
2^-510 and rounds that. Correct rounding of the fast path rests on one claim
per op and region: |D - exact| < err, in units of D's last bit. This script
recomputes D exactly as the Yul does (the kernel254.py and erf256.py models,
which mirror the Yul's integer arithmetic) and the exact value at 120 digits,
and prints the largest error it sees next to the err the Yul uses. The
analytic bound each err comes from is in the table below and in
contracts/src/fp256/README.md; the measured maxima are the check that the
analysis is not off by a missed term.

  op, region            err in the Yul       analytic bound (units of D's last bit)
  exp                   8                    2^f kernel 4.1 (fit 2^-262, Horner floors 1.07,
                                             table product 1 + 1.07) + f's floor 1.4
  expm1, |x| < 2^-8     8                    2 x series 1.6 + 1
  expm1, kernel         8                    as exp; the one is subtracted exactly
  ln, near one          8                    2 x series 2.1 + 1
  ln, kernel            40                   (log2m 37 + Lm's shift 1) ln 2 + 2
  log1p, series         8                    2 x series 3 + 1
  log1p, kernel         44                   as ln + 1 + x's normalisation + the dropped one
  pow, compound         16 + 12 (k + 1)      near one (series, relative 8 units of log2 x)
                        8 + yq (39 + 2|u|) 355 / 2^16
                                             off it (log2m 37 + Lm's shift 2^sh <= 2|u|, and
                                             compound's dropped one 1.45), yq >= 2^8 |y|
                                             (2^8 (|n| + 1)); 6 + 1.3863 x t's error
  compsure              sure to miss         the bound reaches 2^17 for every input it
                                             passes, and |t| < 2^19 (checked by sure() below)
  powu                  2 n + 8              each 256-bit product within 2^-255, squarings
                                             double it: (n + 1) 2^-255 of am, plus 2 for 1/am
  erf, erfc, normCdf    128 (y < 1/2)        2 x F's 52 (erfser's rounded terms, e^-y^2, products) + 1
                        192 (anchors)        2 x g's 81 (1.6 per Taylor term, 50 terms, anchor 0.5) + 8
                        32 n + 64 (CF)       A and B each gain 2^-251 relative per step: 2^5 n
                        er >> -ee + 2        for the differences 1 - erfc, 2 - erfc
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from mpmath import mp, mpf, exp, expm1, log, log1p, power, erf, erfc, ncdf, sqrt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernel254 as K  # noqa: E402
import erf256 as E  # noqa: E402

BIAS = K.BIAS
WS = K.WS
mp.dps = 120


def dec(w):
    return K.decode(w)


class Meter:
    """Per region: the largest error seen, and the largest error / err ratio
    (err varies with the input for pow, compound, powu and the continued
    fraction)."""

    def __init__(self):
        self.rows = {}

    def add(self, name, err, D, exact):
        e = abs(mpf(D) - exact)
        r = self.rows.setdefault(name, [0, mpf(0), 0.0, err, err])
        r[0] += 1
        if e > r[1]:
            r[1] = e
        q = float(e / err)
        if q > r[2]:
            r[2], r[3] = q, err
        r[4] = min(r[4], err)

    def report(self):
        print(f"{'op, region':32} {'n':>6} {'max |D - exact|':>16} {'err (min)':>10}  {'max ratio':>9}")
        bad = False
        for name, (n, worst, ratio, err_at, err_min) in self.rows.items():
            flag = "" if ratio < 1 else "  EXCEEDS"
            bad |= ratio >= 1
            print(f"{name:32} {n:6d} {float(worst):16.3f} {err_min:>10}  {ratio:9.4f}{flag}")
        return bad


def rf(rng, lo, hi, s=None):
    return K.rand_float(rng, lo, hi, s)


def powyb(y):
    """The Yul's powyb: yq >= 2^8 |y|."""
    _, ey, my = K.unpack(y)
    uy = ey - BIAS
    return 1 << 68 if uy > 60 else (my >> (228 - uy) if 228 - uy < 256 else 0) + 1


def powerr0(u, yq):
    """The Yul's powerr off the near-one band."""
    return 8 + ((yq * (39 + 2 * abs(u)) * 355) >> 16)


def compsure(u, n):
    """The Yul's compsure: |n| in [2^(13 - u), 2^(17 - u)) on the series band."""
    return u < -4 and 1 << (13 - u) <= abs(n) < 1 << (17 - u)


def sure(n):
    """compsure sends an input straight to compound's second stage: it claims
    the fast bound would reach 2^17 (half an ULP of v, so rbad fires for any
    v) and |t| < 2^19 (compslow's range, where the fast stage's overflow and
    zero tests cannot fire). Checked on inputs that pass it, with t exact and
    the bound 16 + 12 (k + 1) at k = floor|t| less one for the fast t's error."""
    rng = random.Random(11)
    bad = 0
    seen = 0
    for _ in range(n):
        r = rf(rng, -60, -5)
        s, e, m = K.unpack(r)
        u = e - BIAS
        nn = rng.randint(1, 1 << rng.randint(1, 70)) * rng.choice([1, -1])
        if not compsure(u, nn):
            continue
        seen += 1
        t = abs(nn * log(1 + dec(r), 2))
        k = int(t) - 1
        bad += t >= 2 ** 19 or 16 + 12 * (k + 1) < 1 << 17
    print(f"compsure {seen} inputs: {'all hold' if not bad else f'{bad} FAIL'}")
    return bad > 0


def run(n):
    ker, _, _ = K.build()
    rng = random.Random(4)
    M = Meter()

    # exp and expm1's kernel band: v = 2^f at 2^-254, exact 2^(x log2 e - kk) 2^254
    for _ in range(n):
        x = rf(rng, -118, 17)
        s, e, m = K.unpack(x)
        u = e - BIAS
        k, f = ker.explog2(u, m)
        if k >= 1 << 19:
            continue
        kk, v = ker.exp2kv(s, k, f)
        xv = dec(x)
        M.add("exp", 8, v, exp(xv) * power(2, 254 - kk))
        if u >= -8:
            if s == 0:
                M.add("expm1, kernel", 8, v - (1 << (254 - kk) if kk <= 254 else 0), expm1(xv) * power(2, 254 - kk))
            else:
                c = -(-v >> -kk)
                M.add("expm1, kernel", 8, WS - c, -expm1(xv) * power(2, 254))
    # expm1's series band
    for _ in range(n):
        x = rf(rng, -120, -9)
        s, e, m = K.unpack(x)
        u = e - BIAS
        D = (m * ker.expm1series(ker.tofixed254(s, u, m))) >> 236
        M.add("expm1, |x| < 2^-8", 8, D, abs(expm1(dec(x))) * power(2, 254 - u))
    # ln: near one and the kernel
    for _ in range(n):
        if rng.random() < 0.5:
            d = mpf(2) ** -rng.uniform(9, 230) * (1 if rng.getrandbits(1) else -1)
            x = K.encode(1 + d)
        else:
            x = rf(rng, -1000, 1000, 0)
        if x == BIAS << 236:
            continue
        s, e, m = K.unpack(x)
        band = ker.nearone(x)
        lx = log(dec(x))
        if band is not None:
            sd, ud, md = band
            D = (md * ker.ln1pseries(ker.tofixed254(sd, ud, md))) >> 236
            M.add("ln, near one", 8, D, abs(lx) * power(2, 254 - ud))
        else:
            Lm, Ls = ker.log2pair(e, m)
            l = K.signed(K.mulw(Lm, ker.LN2))
            M.add("ln, kernel", 40, abs(l), abs(lx) * power(2, -Ls))
    # log1p: the series and the kernel
    for _ in range(n):
        r = rng.random()
        x = rf(rng, -120, -5) if r < 0.4 else (rf(rng, -4, 300, 0) if r < 0.8 else rf(rng, -4, -1, 1))
        s, e, m = K.unpack(x)
        u = e - BIAS
        lv = log1p(dec(x))
        if u < -4:
            p = ker.ln1pseries(ker.tofixed254(s, u, m), K.SERIES_TERMS if u < -8 else K.WIDE_TERMS)
            M.add("log1p, series", 8, (m * p) >> 236, abs(lv) * power(2, 254 - u))
        else:
            b = max(u, 0)
            xs = m << (18 + u - b)
            one = (1 << (254 - b)) if b <= 254 else 0
            a = one - xs if s else one + xs
            nb = K.msb(a)
            kk = b + nb - 254
            a = a << (254 - nb) if nb < 254 else a >> (nb - 254)
            Lm, Ls = ker.log2pairm(kk, a)
            l = K.signed(K.mulw(Lm, ker.LN2))
            M.add("log1p, kernel", 44, abs(l), abs(lv) * power(2, -Ls))
    # pow (and compound's tail): v against 2^(t - kk) 2^254
    for _ in range(n):
        if rng.random() < 0.4:
            x = K.encode(1 + mpf(2) ** -rng.uniform(9, 200) * (1 if rng.getrandbits(1) else -1))
            y = rf(rng, -20, 40)
        else:
            x = rf(rng, -60, 60, 0)
            y = rf(rng, -20, 12)
        sx, ex, mx = K.unpack(x)
        sy, ey, my = K.unpack(y)
        if x == BIAS << 236:
            continue
        band = ker.nearone(x)
        if band is not None:
            sd, ud, md = band
            p = ker.ln1pseries(ker.tofixed254(sd, ud, md))
            Lm = K.mulwu(K.mulwu(md << 17, p), ker.LOG2E_HI)
            Ls, Lneg = ud - 253, sd
        else:
            Lm, Ls = ker.log2pair(ex, mx)
            Lneg = 1 if K.signed(Lm) < 0 else 0
            Lm = abs(K.signed(Lm))
        P = Lm * my
        qsh = -(Ls + (ey - BIAS) - 236)
        if qsh < 254:
            continue
        f = K.shr512(P, qsh - 254) & K.M254
        k = K.shr512(P, qsh)
        if k >= 1 << 19:
            continue
        s = Lneg ^ sy
        kk, v = ker.exp2kv(s, k, f)
        t = dec(y) * log(dec(x), 2)
        uy = ey - BIAS
        err = 16 + 12 * (k + 1) if band is not None else powerr0(ex - BIAS, powyb(y))
        M.add("pow, near one" if band is not None else "pow, kernel", err, v, power(2, t - kk + 254))
    # powu: am against |x|^n 2^(255 - ae)
    for _ in range(n // 4):
        x = rf(rng, -3, 3, 0)
        nn = rng.randint(2, 1 << rng.randint(2, 15))
        s, e, m = K.unpack(x)
        am, ae, bm, be, k, inx = 1 << 255, 0, m << 19, e - BIAS, nn, False
        while True:
            if k & 1:
                p = am * bm
                if p >> 511:
                    am, c, inx = p >> 256, 1, inx or bool(p & ((1 << 256) - 1))
                else:
                    am, c, inx = p >> 255, 0, inx or bool(p & ((1 << 255) - 1))
                ae += be + c
            k >>= 1
            if not k:
                break
            p = bm * bm
            if p >> 511:
                bm, c, inx = p >> 256, 1, inx or bool(p & ((1 << 256) - 1))
            else:
                bm, c, inx = p >> 255, 0, inx or bool(p & ((1 << 255) - 1))
            be = 2 * be + c
            if abs(be) > 1 << 20:
                break
        if abs(be) > 1 << 20 or not inx:
            continue
        M.add("powu", 2 * nn + 8, am, power(dec(x), nn) * power(2, 255 - ae))
    # the error function family
    for h, nm in ((0, "erfc"), (1, "normCdf")):
        for _ in range(n):
            r = rng.random()
            x = rf(rng, -12, -2, 0) if r < 0.25 else (rf(rng, -1, 2, 0) if r < 0.75 else rf(rng, 2, 6, 0))
            s, e, m = K.unpack(x)
            u = e - BIAS
            Y, uy = E.ystuff(u, m, h)
            y = dec(x) / sqrt(2 ** h)
            if uy <= -2:
                F = E.erf_small(ker, u, m, h)
                D = WS - ((m * F) >> (236 - u))
                M.add(f"{nm}, y < 1/2", 128, D, erfc(y) * power(2, 254))
                if h == 0:
                    M.add("erf, y < 1/2", 128, (m * F) >> 236, erf(y) * power(2, 254 - u))
                continue
            val = E.erfc_big(ker, Y, uy, u, m, h)
            if val is None:
                continue
            D, ee = val
            if D == 0:
                continue
            anchors = uy <= 1 or (uy == 2 and Y < 3 << 253)
            if anchors:
                err = 192
            else:
                y2 = K.mulwu(Y, Y)
                ey = 2 * uy
                if y2 >> 255:
                    y2 >>= 1
                    ey += 1
                err = 64 + 32 * (4400 // (y2 >> (254 - ey)) + 48)
            region = "anchors" if anchors else "continued fraction"
            M.add(f"{nm}, {region}", err, D, erfc(y) * power(2, 254 - ee))
            D2 = WS - (D >> -ee)
            M.add(f"1 - {nm}, {region}", (err >> -ee) + 2, D2, (1 - erfc(y)) * power(2, 254))
    run79(ker, rng, M, n)
    bad = lambert(ker, M, max(n // 8, 50))
    return M.report() or bad or lwlnfit()


# ---- #79: FP256X2's fast values, as the Yul forms them ---------------------------

L10_HI = 0xd49a784bcd1b8afe492bf6ff4dafdb4cd96c55fe37b3ad4e91b6ac8082e7859d
L10_LO = 0x19943f7a77547ce8f892faad8eb42f5850d7b920159729533fc58b353d80ce0
LOG10_2 = 0x134413509f79fef311f12b35816f922f04d5a618a87a3e69314bcde4d6f98c79
LOG10E = 0x1bcb7b1526e50e32a6ab7555f5a67b8647dc68c048b934404747e5a89ef1d4a8
LN2_FLOOR = 0x2c5c85fdf473de6af278ece600fcbdabd03cd0c99ca62d8b628345d6e2eabe8a


def div254(a, b):
    return (a << 254) // b


def em1k(ker, u, m):
    """e^|x| - 1 at 2^-254 from the kernel, as the Yul's em1k."""
    k, f = ker.explog2(u, m)
    kk, v = ker.exp2kv(0, k, f)
    return (v << kk) - WS


def onep(s, u, m):
    """1 + x as (uu, a), a in [2^254, 2^255), for -4 <= u < 0 (the Yul's onep)."""
    a = WS - (m << (18 + u)) if s else WS + (m << (18 + u))
    n = K.msb(a)
    a = a << (254 - n) if n < 254 else a >> (n - 254)
    return n - 254, a


def run79(ker, rng, M, n):
    """exp2, exp10, log2, log10, sinh, cosh, tanh, atanh: each fast value D
    against the exact value on D's grid. The analytic bounds:

      exp2, exp10           8    as exp: the 2^f kernel 4.1 and f's floor 1.4 (log2 10's
                                 tail under 2^-490 of a unit)
      log2, near one        8    d P within 3 (the series 2, the floor 1), times log2 e:
                                 3 log2 e + 2
      log2, kernel          38   log2m 37, the shift into Lm 1
      log10, near one       8    ln's D within 5, times log10 e: 5 log10 e + 2
      log10, kernel         16   (37 + 1) log10 2 + 2
      sinh, |x| < 2^-8      18   expm1's series T within 2.5 (|x|'s floor), |x| T within 2.1,
                                 the quotient T/(1 + |x| T) within 5.6, the sum 8.1: 2 x 8.1 + 1
      sinh, to 1/2          14   U = e^|x| - 1 from the kernel within 6, U/(1 + U) within 7
      sinh, cosh, kernel    16   v within 6; 2^508/v within 7, one more for the shift
      tanh, |x| < 2^-9      14   T within 3 (2|x|'s floor), |x| T within 2.1, the quotient
                                 within 6.1: 2 x 6.1 + 1
      tanh, to 1/2          8    U = e^2|x| - 1 within 12, U/(U + 2) has slope under 1/2: 6 + 1
      tanh, kernel          8    2/(V + 1) within 6 x 0.54 + 2
      atanh, |x| < 2^-6     18   R = 1/(1 - |x|) within 2.1, y = 2|x|R within 4.2, log1p's
                                 series P within 3 + 2.1, R P within 8.3: 2 x 8.3 + 1
      atanh, kernel         32   two log2m within 37 each, the shift halves: 38 ln 2 + 2
      cbrt seed             2    the seed within two of floor(cbrt N); exact cubes then fix it
    """
    for _ in range(n):
        x = rf(rng, -30, 18)
        s, e, m = K.unpack(x)
        u = e - BIAS
        if u >= 19 or u < -238:
            continue
        P = m << 254
        q = 490 - u
        k, f = K.shr512(P, q), K.shr512(P, q - 254) & K.M254
        if k >= 1 << 19:
            continue
        kk, v = ker.exp2kv(s, k, f)
        M.add("exp2", 8, v, power(2, dec(x) - kk) * power(2, 254))
        if u <= 16:
            P = m * L10_HI + K.mulwu(m, L10_LO)
            k, f = K.shr512(P, 236 - u + 254), K.shr512(P, 236 - u) & K.M254
            kk, v = ker.exp2kv(s, k, f)
            M.add("exp10", 8, v, power(10, dec(x)) * power(2, 254 - kk))
    for _ in range(n):
        if rng.random() < 0.5:
            x = K.encode(1 + mpf(2) ** -rng.uniform(9, 230) * (1 if rng.getrandbits(1) else -1))
        else:
            x = rf(rng, -1000, 1000, 0)
        if x == BIAS << 236:
            continue
        s, e, m = K.unpack(x)
        band = ker.nearone(x)
        xv = dec(x)
        if band is not None:
            sd, ud, md = band
            p = ker.ln1pseries(ker.tofixed254(sd, ud, md))
            D = K.mulwu(K.mulwu(md << 17, p), ker.LOG2E_HI)
            M.add("log2, near one", 8, D, abs(log(xv, 2)) * power(2, 253 - ud))
            D = K.mulwu((md * p) >> 236, LOG10E)
            M.add("log10, near one", 8, D, abs(log(xv, 10)) * power(2, 254 - ud))
        else:
            Lm, Ls = ker.log2pair(e, m)
            M.add("log2, kernel", 38, abs(K.signed(Lm)), abs(log(xv, 2)) * power(2, -Ls))
            l = K.signed(K.mulw(Lm, LOG10_2))
            M.add("log10, kernel", 16, abs(l), abs(log(xv, 10)) * power(2, -Ls))
    for _ in range(n):
        x = rf(rng, -120, -2) if rng.random() < 0.5 else rf(rng, -1, 8)
        s, e, m = K.unpack(x)
        u = e - BIAS
        xv = abs(dec(x))
        if u < -1:
            df = ker.tofixed254(0, u, m)
            if u < -8:
                T = ker.expm1series(df)
                q = div254(T, WS + K.mulwu(df, T))
                M.add("sinh, |x| < 2^-8", 18, (m * (T + q)) >> 236, 2 * mp.sinh(xv) * power(2, 254 - u))
            else:
                U = em1k(ker, u, m)
                M.add("sinh, to 1/2", 14, U + div254(U, U + WS), 2 * mp.sinh(xv) * power(2, 254))
            if u < -9:
                T = ker.expm1series(2 * df)
                M.add("tanh, |x| < 2^-9", 14, (m * div254(T, WS + K.mulwu(df, T))) >> 236, mp.tanh(xv) * power(2, 254 - u))
            else:
                U = em1k(ker, u + 1, m)
                M.add("tanh, to 1/2", 8, div254(U, U + 2 * WS), mp.tanh(xv) * power(2, 254))
            continue
        k, f = ker.explog2(u, m)
        kk, v = ker.exp2kv(0, k, f)
        qv = div254(WS, v) >> (2 * kk)
        M.add("sinh, kernel", 16, v - qv, mp.sinh(xv) * power(2, 255 - kk))
        M.add("cosh, kernel", 16, v + qv, mp.cosh(xv) * power(2, 255 - kk))
        k, f = ker.explog2(u + 1, m)
        if k > 239:
            continue
        kk, v = ker.exp2kv(0, k, f)
        D = WS - div254(1 << (255 - kk), v + (1 << (254 - kk)))
        M.add("tanh, kernel", 8, D, mp.tanh(xv) * power(2, 254))
    for _ in range(n):
        x = rf(rng, -120, -5) if rng.random() < 0.4 else rf(rng, -4, -1)
        s, e, m = K.unpack(x)
        u = e - BIAS
        xv = abs(dec(x))
        if u < -6:
            xf = ker.tofixed254(0, u, m)
            Rr = div254(WS, WS - xf)
            y = 2 * K.mulwu(xf, Rr)
            P = ker.ln1pseries(y, K.SERIES_TERMS if u < -10 else K.WIDE_TERMS)
            M.add("atanh, |x| < 2^-6", 18, (m * K.mulwu(Rr, P)) >> 236, mp.atanh(xv) * power(2, 254 - u))
            continue
        uu1, a1 = onep(0, u, m)
        uu2, a2 = onep(1, u, m)
        i = uu1 - uu2
        sh = K.msb(i) + 1
        T = (i << (254 - sh)) + ((ker.log2m(a1) - ker.log2m(a2)) >> sh)
        M.add("atanh, kernel", 32, K.mulwu(T, LN2_FLOOR), mp.atanh(xv) * power(2, 255 - sh))
    for _ in range(n):
        x = rf(rng, -2000, 2000)
        s, e, m = K.unpack(x)
        v = e - 0x400EB
        q, rr = v // 3, v % 3
        g = (((2 + rr) << 253) + (ker.log2m(m << 18) >> 1)) // 3
        ip = 1 if g >= 1 << 253 else 0
        g -= ip << 253
        y = ker.exp2frac(g << 1) >> (17 - ip)
        N = m << (rr + 477)
        r = int(mp.floor(mp.cbrt(mpf(N))))
        while r ** 3 > N:
            r -= 1
        while (r + 1) ** 3 <= N:
            r += 1
        M.add("cbrt seed", 3, y, mpf(r))


# ---- Lambert W's fourth-order step, as the Yul's lwlog forms it -----------------

LN2_CEIL = 0x2c5c85fdf473de6af278ece600fcbdabd03cd0c99ca62d8b628345d6e2eabe8b
LW2Q = [266377486799641577, -1395521547598861468, 3481873446185410082, -5939118987770338793,
        8708466524488688751, -13287486091412030003, 26612150119985157926, 6798757998674]


def lw2q(f):
    """The Yul's lw2q: log2(1 + f 2^-64) at 2^-64 by a degree-7 fit."""
    p = LW2Q[0]
    for c in LW2Q[1:]:
        p = c + ((p * f) >> 64)
    return p


def lwlnfit():
    """lw2q's coefficients are the degree-7 Chebyshev interpolant of log2(1 + f)
    on [0, 1) at 2^-64, within 2^-21.4 there (lwln's claim)."""
    from mpmath import chebyfit, nint
    poly = chebyfit(lambda f: log(1 + f, 2), [0, 1], 8)
    assert [int(nint(c * mpf(2) ** 64)) for c in poly] == LW2Q, "lw2q's coefficients"
    worst = max(abs(lw2q(int(mpf(i) / 4000 * (2 ** 64 - 1))) - log(1 + mpf(i) / 4000, 2) * mpf(2) ** 64) for i in range(4001))
    print(f"lw2q: log2(1 + f) within 2^{float(log(worst / mpf(2) ** 64, 2)):.1f}")
    return worst > mpf(2) ** 42.7


def log2pairg(u, lg):
    if u == 0:
        return lg, -254
    sh = K.msb(abs(u)) + 1
    return (u << (254 - sh)) + (lg >> sh), sh - 254


def sdiv254(a, b):
    q = (abs(a) << 254) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def lwlog(ker, x, w, q2=0):
    """The Yul's lwlog: (D, err, cv)."""
    _, ex, mx = K.unpack(x)
    sw, ew, mw = K.unpack(w)
    k = ew - ex
    if mw < mx:
        q, k = ((mw << 1) << 254) // mx, k - 1
    else:
        q = (mw << 254) // mx
    lg = lw2q((q - WS) >> 190) << 190 if q2 else ker.log2m(q)
    Lm, Ls = log2pairg(k, lg)
    n = ew - 0x400EB - Ls
    wf = mw << n if n >= 0 else mw >> -n
    if sw:
        wf = -wf
    hf = wf + (1 << -Ls)
    u = sdiv254(wf + ((Lm * LN2_CEIL) >> 254), hf)
    v = sdiv254(u, hf) >> (Ls + 254)
    uv = (u * v) >> 254
    t3 = (((u * u) >> 254) * v) >> 254
    fac = WS - u + (uv >> 1) - ((uv * v) >> 254 >> 1) + (-((-t3) // 3) if t3 < 0 else t3 // 3)
    D = ((mw << 18) * fac) >> 254
    du = 17 + 16 * ((1 << 255) // abs(hf))
    return D, 2 * du + (du >> 4) + 12, max(abs(u), abs(v)) < 1 << 188


LWSER = [0x27fdc8c94fb38a69e89d4e4ab38ccc029656fdeb59fa04815ade5a7cb38240,
         -0x3e71be1a92260ba70af38553d309a99b8cd446298c481991d887214da438ee,
         0x628ad2a498c39cf0fa1d2fe7ec71fed1d3b094716efb67abcdd2d8d2cf67d1,
         -0x9d902b2ef224dcc5e5a70b6d8dc2bc90ebd2b086afec93544511bfba01f24b,
         0x1002c98983bc435a045285a1b7069470dcdc800879e4896c9e5fb4ad8b52121,
         -0x1a9bbcb24fe29f595de1b82e796c546675cfa8d4a04088c62d92416ff11207a,
         0x2d9203cae759203cae759203cae759203cae759203cae759203cae759203cae,
         -0x518a6dfc3518a6dfc3518a6dfc3518a6dfc3518a6dfc3518a6dfc3518a6dfc3,
         0x9c71c71c71c71c71c71c71c71c71c71c71c71c71c71c71c71c71c71c71c71c7,
         -0x1555555555555555555555555555555555555555555555555555555555555555,
         WS]


def lwmu():
    """mu_1..mu_11 of the branch-point series (Corless et al. 1996, (4.23)),
    exact, high degree first."""
    from fractions import Fraction as Fr
    mu = {0: Fr(-1), 1: Fr(1)}
    al = {0: Fr(2), 1: Fr(-1)}
    for k in range(2, 12):
        al[k] = sum((mu[j] * mu[k + 1 - j] for j in range(2, k)), Fr(0))
        mu[k] = Fr(k - 1, k + 1) * (mu[k - 2] / 2 + al[k - 2] / 4) - al[k] / 2 - mu[k - 1] / (k + 1)
    return [mu[k] for k in range(11, 0, -1)]


def lwser_d(p):
    """The Yul's lwser: D = |W| 2^254 from the float p, |p| < 2^-21."""
    sp, ep, mp_ = K.unpack(p)
    P = mp_ >> (0x3FFED - ep)
    if sp:
        P = -P
    S = LWSER[0]
    for c in LWSER[1:]:
        S = c + ((P * S) >> 254)
    return WS - ((P * S) >> 254)


def lambert(ker, M, n):
    """lwlog's bound on the step that starts within 2^-66 (cv), from seeds as
    lambertW0 and lambertWm1 form them (here in real arithmetic, rounded to a
    word): the measured |D - W| against err. Also that every input converges
    within lwiter's six steps."""
    from mpmath import lambertw, e as Ee
    rng = random.Random(9)
    slow = 0

    def seed(xv, br):
        if xv < -0.25:
            p = sqrt(2 * (1 + Ee * xv))
            return -1 + p * (1 if br == 0 else -1) - p * p / 3 + p ** 3 * mpf(11) / 72 * (1 if br == 0 else -1)
        if br == 0 and xv < 0.125:
            return xv - xv * xv + 1.5 * xv ** 3
        if br == 0:
            l = log(1 + xv)
            return l * (1 - log(1 + l) / (2 + l))
        lx = log(-xv)
        return lx - log(-lx) + log(-lx) / lx

    def one(xv, br, name):
        nonlocal slow
        x = K.encode(xv)
        xv = dec(x)
        if xv < -1 / Ee:
            return
        Wv = lambertw(xv, br).real
        w = K.encode(seed(xv, br))
        q2 = 1 if br == 0 and 0.125 <= xv < 2 ** 64 else 0
        for _ in range(6):
            D, err, cv = lwlog(ker, x, w, q2)
            uw = ((w >> 236) & 0x7FFFF) - BIAS
            w = K.normround(w >> 255, uw + BIAS, D)
            if cv and not q2:
                M.add(name, err, D, abs(Wv) * power(2, 254 - uw))
                return
            q2 = 0
        slow += 1

    for _ in range(n):
        one(mpf(2) ** rng.uniform(-12, 10), 0, "lambertW0, step")
        one(mpf(2) ** rng.uniform(10, 2000) if rng.random() < 0.7 else mpf(2) ** rng.randint(2000, 260000), 0, "lambertW0, step")
        one(-mpf(2) ** rng.uniform(-80, -2), 0, "lambertW0 < 0, step")
        one(-1 / Ee + mpf(2) ** -rng.uniform(3, 44), 0, "lambertW0 near -1/e, step")
        one(-mpf(2) ** rng.uniform(-300, -2) if rng.random() < 0.8 else -mpf(2) ** -rng.uniform(300, 262000), -1, "lambertWm1, step")
        one(-1 / Ee + mpf(2) ** -rng.uniform(3, 44), -1, "lambertWm1 near -1/e, step")
    print(f"lambert W: {slow} inputs did not converge in six steps")
    # the branch-point series below p = 2^-21: its constants are the rounded
    # mu_k, and D against W at the float p, as both branches form p
    for c, mu in zip(LWSER, lwmu()):
        v = mu * (1 << 254)
        assert c == (v.numerator * 2 + v.denominator) // (2 * v.denominator), "lwser's mu_k"
    for _ in range(n * 4):
        d = mpf(2) ** -rng.uniform(44, 500)
        for br in (0, -1):
            x = K.encode(-1 / Ee + d)
            xv = dec(x)
            if xv < -1 / Ee:
                continue
            q = K.encode(1 + Ee * xv)   # lwq: 1 + e x rounded once; then sqrt(2q) rounded
            p = K.encode(sqrt(2 * dec(q)) * (1 if br == 0 else -1))
            if abs(dec(p)) >= mpf(2) ** -21:
                continue
            M.add("lambert W, branch series", 4, lwser_d(p), abs(lambertw(xv, br).real) * power(2, 254))
    return slow > 0


def cf_depth(n):
    """The second stage's continued fraction for erfc at y >= 7: depth
    1700/floor|x| + 28 (erfc, x = y) or 2404/floor|x| + 28 (normCdf, x = y
    sqrt 2), truncation error relative to erfc at 150 digits."""
    mp.dps = 150
    rng = random.Random(7)
    worst = mpf(0)
    for _ in range(n):
        h = rng.getrandbits(1)
        x = mpf(rng.uniform(7 * (1.4143 if h else 1), 430 * (1.4143 if h else 1)))
        if rng.random() < 0.5:
            x = mpf(7 * (1.4143 if h else 1)) + mpf(rng.random())
        xi = int(x)
        depth = (1700 + 704 * h) // xi + 28
        y = x / sqrt(2 ** h)
        b, a = (2 * y, 2) if h == 0 else (x, 1)
        t = mpf(0)
        for k in range(depth, 0, -1):
            t = (a * k) / (b + t)
        c = (2 / sqrt(mp.pi)) if h == 0 else sqrt(2 / mp.pi)
        v = c * exp(-y * y) / (b + t)
        worst = max(worst, abs(v / erfc(y) - 1))
    print(f"continued fraction at y >= 7, depth 1700/floor|x| + 28: truncation below 2^{float(log(worst, 2)):.1f} "
          f"over {n} points (the second stage is held to 2^-392)")
    return worst > mpf(2) ** -390


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    bad = run(n)
    bad |= sure(n * 4)
    bad |= cf_depth(max(n // 20, 50))
    sys.exit(1 if bad else 0)

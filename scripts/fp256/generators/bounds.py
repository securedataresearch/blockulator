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
  exp                   8                    2^f kernel 4.7 (kernel254.py's exp2frac_bound: the
                                             fit 2^-270.7, Horner 1.51 at 2^-255, two table
                                             levels Delta T + 1.5, halved, + 1) + f's floor 1.4
  expm1, |x| < 2^-8     8                    2 x series 1.6 + 1
  expm1, kernel         8                    as exp; the one is subtracted exactly
  ln, near one          8                    2 x ln1pk 2.7 + 1 (kernel254.py's ln1pk_bound)
  ln, kernel            5                    (log2m 2.4 + Lm's shift 1) ln 2 + 2 = 4.4
                                             (kernel254.py's log2m_bound)
  log1p, series         8                    2 x ln1pk 2.7 (the wide P from 2^-8) + 1
  log1p, kernel         7                    as ln + 1 + x's normalisation 1 + the dropped one 1
  pow, compound         16 + 12 (k + 1)      near one (series, relative 8 units of log2 x)
                        8 + yq (8 + 2|u|) 355 / 2^16
                                             off it (log2m 2.4 + Lm's shift 2^sh <= 2|u|, and
                                             compound's dropped one 1.45), yq >= 2^8 |y|
                                             (2^8 (|n| + 1)); 6.1 + 1.3863 x t's error
  compsure              sure to miss         the bound reaches 2^17 for every input it
                                             passes, and |t| < 2^19 (checked by sure() below)
  powu                  2 n + 8              each 256-bit product within 2^-255, squarings
                                             double it: (n + 1) 2^-255 of am, plus 2 for 1/am
  erf, erfc, normCdf    128 (y < 1/2)        2 x F's 52 (erfser's rounded terms, e^-y^2, products) + 1
                        192 (anchors)        2 x g's 81 (1.6 per Taylor term, 50 terms, anchor 0.5) + 8
                        32 n + 64 (CF)       A and B each gain 2^-251 relative per step: 2^5 n
                        64 (y >= 18)         the asymptotic series' terms' floors at 2^-262, w's
                                             2^-254, Q's 2 units, v's 6.1, two floors (under 49)
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
    return 8 + ((yq * (8 + 2 * abs(u)) * 355) >> 16)


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
            M.add("ln, kernel", 5, abs(l), abs(lx) * power(2, -Ls))
    # log1p: the series and the kernel
    for _ in range(n):
        r = rng.random()
        x = rf(rng, -120, -5) if r < 0.4 else (rf(rng, -4, 300, 0) if r < 0.8 else rf(rng, -4, -1, 1))
        s, e, m = K.unpack(x)
        u = e - BIAS
        lv = log1p(dec(x))
        if u < -4:
            df = ker.tofixed254(s, u, m)
            p = ker.ln1pseries(df) if u < -8 else ker.ln1pwide(df)
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
            M.add("log1p, kernel", 7, abs(l), abs(lv) * power(2, -Ls))
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
            x = rf(rng, -12, -2, 0) if r < 0.2 else (rf(rng, -1, 2, 0) if r < 0.6 else (rf(rng, 2, 3, 0) if r < 0.8 else rf(rng, 4, 8, 0)))
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
            elif E.asym_regime(Y, uy):
                err = 64
            else:
                y2 = K.mulwu(Y, Y)
                ey = 2 * uy
                if y2 >> 255:
                    y2 >>= 1
                    ey += 1
                err = 64 + 32 * (4400 // (y2 >> (254 - ey)) + 48)
            region = "anchors" if anchors else ("asymptotic series" if E.asym_regime(Y, uy) else "continued fraction")
            M.add(f"{nm}, {region}", err, D, erfc(y) * power(2, 254 - ee))
            D2 = WS - (D >> -ee)
            M.add(f"1 - {nm}, {region}", (err >> -ee) + 2, D2, (1 - erfc(y)) * power(2, 254))
    run79(ker, rng, M, n)
    bad = lambert(ker, M, max(n // 8, 50))
    return M.report() or bad


# ---- #79: the fast values of the exp2..atanh family, as the Yul forms them -------

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

      exp2, exp10           8    as exp: the 2^f kernel 4.7 and f's floor 1.4 (log2 10's
                                 tail under 2^-490 of a unit)
      log2, near one        8    d P within 3.7 (ln1pk 2.7, the floor 1), times log2 e:
                                 3.7 log2 e + 2
      log2, kernel          4    log2m 2.4, the shift into Lm 1
      log10, near one       8    ln's D within 6.4, times log10 e: 6.4 log10 e + 2
      log10, kernel         4    (2.4 + 1) log10 2 + 2
      sinh, |x| < 2^-8      18   expm1's series T within 2.5 (|x|'s floor), |x| T within 2.1,
                                 the quotient T/(1 + |x| T) within 5.6, the sum 8.1: 2 x 8.1 + 1
      sinh, to 1/2          14   U = e^|x| - 1 from the kernel within 6.1, U/(1 + U) within 7.1
      sinh, cosh, kernel    16   v within 6.1; 2^508/v within 7.1, one more for the shift
      tanh, |x| < 2^-9      14   T within 3 (2|x|'s floor), |x| T within 2.1, the quotient
                                 within 6.1: 2 x 6.1 + 1
      tanh, to 1/2          8    U = e^2|x| - 1 within 12.2, U/(U + 2) has slope under 1/2: 6.1 + 1
      tanh, kernel          8    2/(V + 1) within 6.1 x 0.54 + 2
      atanh, |x| < 2^-6     18   R = 1/(1 - |x|) within 2.1, y = 2|x|R within 4.2, log1p's
                                 ln1pk P within 3 + 2.1, R P within 8.3: 2 x 8.3 + 1
      atanh, kernel         5    two log2m within 2.4 each, the shift halves: 3.4 ln 2 + 2
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
            M.add("log2, kernel", 4, abs(K.signed(Lm)), abs(log(xv, 2)) * power(2, -Ls))
            l = K.signed(K.mulw(Lm, LOG10_2))
            M.add("log10, kernel", 4, abs(l), abs(log(xv, 10)) * power(2, -Ls))
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
            P = ker.ln1pseries(y) if u < -10 else ker.ln1pwide(y)
            M.add("atanh, |x| < 2^-6", 18, (m * K.mulwu(Rr, P)) >> 236, mp.atanh(xv) * power(2, 254 - u))
            continue
        uu1, a1 = onep(0, u, m)
        uu2, a2 = onep(1, u, m)
        i = uu1 - uu2
        sh = K.msb(i) + 1
        T = (i << (254 - sh)) + ((ker.log2m(a1) - ker.log2m(a2)) >> sh)
        M.add("atanh, kernel", 5, K.mulwu(T, LN2_FLOOR), mp.atanh(xv) * power(2, 255 - sh))
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


# ---- Lambert W: seed -> fast -> safe, as the Yul forms it ---------------------
#
# Near -1/e (1 + e x = y below 1/8) the unknown is q = 1 + W on Phi(q) =
# (q - 1) e^q + 1 = y, seeded by a degree-16 fit in p = sqrt(2y) (2^-44.8)
# and finished by one sixth-order step whose e^q - 1 comes from the core's
# wide exp kernel (2^-503 absolute, which is the relative precision the
# residual needs: 2^-503/(q^2 e^q) in tau, 2^-503/(q e^q) in q): |q| within
# 5 units of 2^-254 whatever q, and W = -1 +- q exact. This replaces the
# adaptive-precision rule (262 + log2(1/|1 + w|) bits) of the literature
# review: the kernel's two words are that precision for every q down to
# 2^-246. Elsewhere the fourth-order log-form step lwlog (unchanged bound)
# after a cheap stage at 2^-126 whose seeds and step counts this section
# measures.

LN2_CEIL = 0x2c5c85fdf473de6af278ece600fcbdabd03cd0c99ca62d8b628345d6e2eabe8b
LN2_128 = 0xb17217f7d1cf79abc9e3b39803f2f6af
SQRT2_126 = 0x5a827999fcef32422cbec4d9baa55f50
EH = 0xadf85458a2bb4a9aafdc5620273d3cf1d8b9c583ce2d3695a9e13641146433fb
EL = 0x3324e7738926cfbe5f4bf8d8d8c31d763da06c80abb1185eb4f7c7b5757f5958
M256 = (1 << 256) - 1


def sdiv(a, b):
    """Yul's sdiv: truncation toward zero."""
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def isqrt_yul(n):
    """The Yul's isqrt: seven Newton steps from 2^127 and a fix-up."""
    y = 1 << 127
    for _ in range(7):
        y = (y + n // y) >> 1
    if y > n // y:
        y -= 1
    return y


def log2pairg(u, lg):
    if u == 0:
        return lg, -254
    sh = K.msb(abs(u)) + 1
    return (u << (254 - sh)) + (lg >> sh), sh - 254


def sdiv254(a, b):
    q = (abs(a) << 254) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def lwlog(ker, x, w):
    """The Yul's lwlog: (D, err, cv)."""
    _, ex, mx = K.unpack(x)
    sw, ew, mw = K.unpack(w)
    k = ew - ex
    if mw < mx:
        q, k = ((mw << 1) << 254) // mx, k - 1
    else:
        q = (mw << 254) // mx
    Lm, Ls = log2pairg(k, ker.log2m(q))
    n = ew - 0x400EB - Ls
    wf = mw << n if n >= 0 else mw >> -n
    if sw:
        wf = -wf
    hf = wf + (1 << -Ls)
    u = sdiv254(wf + ((Lm * LN2_CEIL) >> 254), hf)
    if abs(hf) > 1 << 253:
        v = ((u * (sdiv(1 << 252, hf >> 128) << 128)) >> 254) >> (Ls + 254)
    else:
        v = sdiv254(u, hf) >> (Ls + 254)
    uv = (u * v) >> 254
    t3 = (((u * u) >> 254) * v) >> 254
    fac = WS - u + (uv >> 1) - ((uv * v) >> 254 >> 1) + sdiv(t3, 3)
    D = ((mw << 18) * fac) >> 254
    ah = abs(hf) >> 4
    du = 1 + ((1 << 255) + ah - 1) // ah
    return D, 2 * du + (du >> 4) + 12, max(abs(u), abs(v)) < 1 << 188


def lwy(m):
    """The Yul's lwy: (Y, ey, yh, yl) with y = 1 + e x = Y 2^ey, Y in [2^254, 2^255), and
    y exact at 2^-510 as (yh, yl); (0, 0, 0, 0) at y = 0, None below -1/e."""
    P = m * EH + ((m * EL) >> 254 & M256)
    D = (1 << 492) - P
    if D < 0:
        return None
    if D == 0:
        return 0, 0, 0, 0
    nb = K.msb(D)
    Y = D << (254 - nb) if nb <= 254 else D >> (nb - 254)
    return Y, nb - 746, (D << 18) >> 256, (D << 18) & M256


T_STAGES = [(0x5a827999fcef32422cbec4d9baa55f50, 0x2d413cccfe779921165f626cdd52afa8, 32),
            (0x4c1bf828c6dc54b7a356918c17217b7b, 0x35d13f32b5a75abd0e69a2ee640b4ff8, 16),
            (0x45cae0f1f545eb737df23143ac529e48, 0x3ab031b9f7490e4bb40b5d6cdc1b953f, 8),
            (0x42d561b3e6243d8a62e4adc610aa60d9, 0x3d495f454921b30b1ee7431ebb6603f1, 4),
            (0x4166c34c5615d0eb9f1523ada3290600, 0x3ea0ecb6dc8a80ce9f096ec50c575ff3, 2),
            (0x40b268f9de0183b9bdf2b293de8a6f7a, 0x3f4f83033d21b05d214fce964c783b81, 1)]
ATANH_C = [0x4446135483304695b31cd2087781804, 0x4ec4ec491eccde6dc9ec3dc71cf3623, 0x5d1745d1746646dc577e7d058db642b,
           0x71c71c71c71c71bed60c1d9b8a55f08, 0x92492492492492492496556bf318f39, 0xcccccccccccccccccccccccbd3dcdb3,
           0x155555555555555555555555555556c2, 0x40000000000000000000000000000000]
LN2_122 = 0x2c5c85fdf473de6af278ece600fcbdb
LNC0 = [0x6c624f4ace937ad74c72c1900aebb69, -0x193a803a4689b1e7d4fe8cc4f525bca5, 0x3ecce60a25db5c9757959e657fdbf429, 0x95fd7e22848b1d16f2f2bb6adf6c7]
LWSP = [0x53b90081353ec0d6941c921fcfafe595a00cc42497241ae655363581fda94, -0x7da26a79225bb5fb50ea8efcc8ae9d4254e4dc4f946a07e0bfe6de0579346,
        0x644585809454cf76ef165d39ed6b3221e9ba088251003ceff2f71f7c0c755, -0x98b8b6e30746fa914f48ce0a496b7a037105c06bb06c9d7f684c61cf6fd46,
        0x110d843b49b21ba51a501bbb77ed0f257949b9cc213a87345be9ca07b63737, -0x1a313459af0764ab9552879fb1e10f9bf22264fb538a1aa117eae1bb53021a,
        0x27f5807beecdf9efb8c709fad4296181f19ead87c6548eb20db7222ab50a4c, -0x3e656398e74c5d03b4b5df785dc1c426dcc98ec31e23a08ebd7c71dc546983,
        0x628b743708e2d24266d1587a51d9c728881f97fd4201e6904b1872252776b5, -0x9d911c278f1cb7b3ed76e932800a7853179177003af08ad833049761583efd,
        0x1002c921ab74cdbe4d174f50d821165e87a6ad194e0c48cc71d0e1d0a3a51bb, -0x1a9bbc1771a4a40ca538aa8217e0e6417f0eebd3b401221c91c8d7a77ccffbb,
        0x2d9203ccc4cd1b7ae3baee267b661786f46d8800613ee614953eb058ced39ae, -0x518a6dfefd1f0da4f26b457422d5955b99bbeb25c7a90c9258e8aaf51a88dc3,
        0x9c71c71c6f490046c1d5e4523fc72a7e7eebcd533f42e92e99d9f2e603d55fc, -0x155555555519dbb6d739a70acc0e3d8ec423a092398259b8ab5412b03b634978,
        1 << 254]



def lnc(r, k):
    """The Yul's lnc: k ln 2 + ln r at 2^-128, r in [2^126, 2^127): six table reductions,
    then 2 s atanh(s)/s with the degree-7 fit in s^2 (lncfit certifies it)."""
    j = 64 * k
    for T, I, dj in T_STAGES:
        if r >= T:
            r = (r * I) >> 126
            j += dj
    s = sdiv((r - (1 << 126)) << 126, r + (1 << 126))
    s2 = (s * s) >> 126
    A = ATANH_C[0]
    for c in ATANH_C[1:]:
        A = c + ((s2 * A) >> 126)
    return j * LN2_122 + (((s * A) >> 125) << 2)


def lnc0(r, k):
    """The Yul's lnc0: the crude logarithm for the seeds (a degree-3 fit, 2^-10.8)."""
    t = r - (1 << 126)
    P = LNC0[0]
    for c in LNC0[1:]:
        P = c + ((P * t) >> 126)
    return k * LN2_128 + (P << 2)


def lnm(v):
    n = K.msb(v)
    r = v >> (n - 126) if n >= 126 else v << (126 - n)
    return r, n - 128


def lwsp(p, S):
    """The Yul's lwsp: S(p) = (1 + W)/p by the degree-16 fit, Horner at 2^-S on p at 2^-S."""
    v = LWSP[0] >> (254 - S)
    for c in LWSP[1:]:
        v = (c >> (254 - S) if c >= 0 else -((-c) >> (254 - S))) + ((p * v) >> S)
    return v


def lncfit():
    """lnc's and lwsp's fits certified: the Yul's constants are the rounded chebyfit
    coefficients, and the fits' sup norms on dense grids are what the Yul claims."""
    from mpmath import chebyfit, atanh, lambertw, e as Ee, sqrt as msqrt, power, nint, mpf, log
    mp.dps = 90
    smax = (power(2, mpf(1) / 64) - 1) / (power(2, mpf(1) / 64) + 1)
    g = lambda u: atanh(msqrt(u)) / msqrt(u) if u > 0 else mpf(1)
    ap = chebyfit(g, [mpf(0), smax ** 2], 8)
    assert [int(nint(c * mpf(2) ** 126)) for c in ap] == ATANH_C, "lnc's fit"
    worst = max(abs(sum(c * (smax ** 2 * i / 4000) ** (7 - j) for j, c in enumerate(ap)) - g(smax ** 2 * i / 4000)) for i in range(4001))
    print(f"lnc: atanh(s)/s by the degree-7 fit within 2^{float(log(worst, 2)):.1f} on [0, {float(smax):.5f}]^2")
    S = lambda p: (1 + lambertw((p * p / 2 - 1) / Ee, 0 if p > 0 else -1).real) / p if p != 0 else mpf(1)
    sp = chebyfit(S, [-mpf(1) / 2, mpf(1) / 2], 17)
    assert [int(nint(c * mpf(2) ** 254)) for c in sp] == LWSP, "lwsp's fit"
    worst2 = max(abs(sum(c * (mpf(i) / 4000) ** (16 - j) for j, c in enumerate(sp)) / S(mpf(i) / 4000) - 1) for i in range(-2000, 2001))
    print(f"lwsp: S(p) by the degree-16 fit within 2^{float(log(worst2, 2)):.1f} relative on [-1/2, 1/2]")
    mp.dps = 120
    return worst > mpf(2) ** -138 or worst2 > mpf(2) ** -44.5


def lwsw(x):
    """Winitzki's seed at 2^-128, as a float."""
    _, e, m = K.unpack(x)
    u = e - BIAS
    L = lnc0(*lnm((1 << 128) + (m >> (108 - u)))) if u < 18 else lnc0(m >> 110, u)
    l1 = lnc0(*lnm((1 << 128) + L))
    t = sdiv(l1 << 100, ((1 << 129) + L) >> 28)
    return K.normround(0, BIAS + 126, L - (((L >> 18) * t) >> 110))


def lwso(x):
    """The origin seed x (1 - x (1 - 3x/2)) as a float."""
    s, e, m = K.unpack(x)
    xa = m >> (0x4006B - e) if e <= 0x4006B else 0
    if s:
        xa = -xa
    inner = (1 << 128) - xa + ((3 * ((xa * xa) >> 128)) >> 1)
    return K.normround(s, e, ((m << 18) * inner) >> 128)


def lwsm(x):
    """The asymptotic seed for W-1 as a float."""
    _, e, m = K.unpack(x)
    lx = lnc0(m >> 110, e - BIAS)
    ll = lnc0(*lnm(-lx))
    return K.normround(1, BIAS + 126, -(lx - ll + sdiv(ll << 100, lx >> 28)))


def lwf128(x, w):
    """The Yul's lwf128: the fourth-order log-form step at 2^-126, (w', |u| 2^128)."""
    _, ex, mx = K.unpack(x)
    sw, ew, mw = K.unpack(w)
    k = ew - ex
    r = (mw << 19) // (mx >> 107)
    if r < (1 << 126):
        r <<= 1
        k -= 1
    L = lnc(r, k)
    wf = mw >> (0x4006B - ew) if ew <= 0x4006B else 0
    if sw:
        wf = -wf
    hs = (wf + (1 << 128)) >> 28
    u = sdiv((wf + L) << 100, hs)
    v = sdiv(u << 100, hs)
    uv = (u * v) >> 128
    fac = (1 << 128) - u + (uv >> 1) - (((uv * v) >> 128) >> 1) + sdiv((((u * u) >> 128) * v) >> 128, 3)
    return K.normround(sw, ew, ((mw << 18) * fac) >> 128), abs(u)


def lwfast(x, w):
    n = 0
    for _ in range(4):
        w, au = lwf128(x, w)
        n += 1
        if au < 1 << 110:
            break
    return w, n


def lwb3(qa, tau):
    """The Yul's lwb3: b3 + tau (b4 + tau b5) at 2^-112, q and tau at 2^-126."""
    C = lambda n: n << 112
    m = lambda a, b: (a * b) >> 126
    h = lambda co: __import__("functools").reduce(lambda acc, cc: C(cc) + m(qa, acc), co[1:], C(co[0]))
    v = sdiv(h([240, 1200, 3052, 4760, 4410, 1890]), 1440)
    v = sdiv(h([24, 96, 190, 210, 105]), 120) + m(tau, v)
    return sdiv(h([6, 18, 25, 15]), 24) + m(tau, v)


def lwbs(qa, tau):
    """The Yul's lwbs: 1 + tau (b1 + ...) at 2^-254 for q and tau at 2^-254."""
    m = lambda a, b: (a * b) >> 254
    C = lambda n: n << 240
    R = lwb3(qa >> 128, tau >> 128) << 128
    v = sdiv(C(3) + m(qa, C(4) + m(qa, C(2))), 6) + m(tau, R)
    v = ((C(1) + (qa >> 14)) >> 1) + m(tau, v)
    return (C(1) + m(tau, v)) << 14


def wexpm1_exact(qh, ql):
    """The core's wexpm1 / wexpr stand-in: e^r - 1 exact, floored at 2^-510 (the kernel is
    within 2^-503; its share of the bound is derived, not measured here)."""
    r = mpf((qh << 256) | ql) / power(2, 510)
    v = int(mp.floor((exp(r) - 1) * power(2, 510)))
    return v >> 256, v & M256


def lwphi(sg, q254, qh, ql):
    """The Yul's lwphi: Phi wide at 2^-510 and 1 + E1 at 2^-252."""
    one = 1 << 254
    if not sg:
        eh, el = wexpm1_exact(qh, ql)
        E252 = (eh >> 2) + (1 << 252)
    else:
        # wexpr(1, -1, |q|): e^q = (1 + X)/2, X = wexpm1(ln 2 - |q|)
        LN2 = int(mp.floor(log(2) * power(2, 510)))
        r = LN2 - ((qh << 256) | ql)
        xh, xl = wexpm1_exact(r >> 256, r & M256)
        v = (((xh + one) << 256) | xl) >> 1
        xh, xl = v >> 256, v & M256
        E252 = xh >> 2
        v = (one << 256) - v
        eh, el = v >> 256, v & M256
    m = one - q254 if not sg else one + q254
    P = (((eh << 256) | el) * m) >> 254
    Q = (qh << 256) | ql
    F = Q - P if not sg else P - Q
    return F >> 256, F & M256, E252


def lwtau(fh, fl, yh, yl, Qa, eqs, E252):
    """The Yul's lwtau."""
    D = ((fh << 256) | fl) - ((yh << 256) | yl)
    ng = D < 0
    D = abs(D)
    if D == 0:
        return 0
    n = K.msb(D)
    h = D >> (n - 255) if n >= 255 else D << (255 - n)
    e = n - 255 - 256
    B = (((Qa * Qa) >> 254) * E252) >> 254
    d = K.msb(B) - 254
    B <<= -d
    sh = e - 2 * eqs - 509 - d
    t = ((h >> 1) << 254) // B
    tau = t >> -sh if sh <= -8 else 1 << 254
    return -tau if ng else tau


def lwq510(Qa, eqs, sg, yh, yl):
    """The Yul's lwq510: (|q| 2^254, |tau| 2^254)."""
    q254 = Qa >> (-eqs - 254)
    s = eqs + 510
    Q = Qa << s
    qh, ql = Q >> 256, Q & M256
    fh, fl, E252 = lwphi(sg, q254, qh, ql)
    tau = lwtau(fh, fl, yh, yl, Qa, eqs, E252)
    qa = -q254 if sg else q254
    return (Qa - ((Qa * ((tau * lwbs(qa, tau)) >> 254)) >> 254)) >> (-eqs - 254), abs(tau)


def lwbr(Y, ey, yh, yl, sg):
    """The Yul's lwbr up to D: (D, err, steps, |tau| at the start of the last)."""
    k = 2 - (ey & 1)
    eqs = (ey - 254 + k) >> 1
    ep = eqs + 128
    P = isqrt_yul(Y >> (1 + k))
    p = P << (ep + 254) if ep + 254 >= 0 else P >> (-ep - 254)
    if sg:
        p = -p
    Qa = ((P << 128) * lwsp(p, 254)) >> 254
    n = 0
    for _ in range(2):
        qn, at = lwq510(Qa, eqs, sg, yh, yl)
        n += 1
        if at < 1 << 210 or qn < 1 << 194:
            break
        Qa = qn << (-eqs - 254)
    return (WS + qn if sg else WS - qn), 5, n, at


def lambert(ker, M, n):
    """Lambert W's bounds, measured: the safe q-form step near -1/e against
    its 5 units (the wide exp kernel stands in as the exact e^q - 1 floored
    at 2^-510; the kernel's own 2^-503 adds under a unit for |q| >= 2^-246,
    derived in lwq510's comment), lwlog's bound after the new seeds and the
    cheap stage, the step counts, and the share of inputs whose rounding
    test would fire (the fallback rate, rbad on the model's D)."""
    from mpmath import lambertw, e as Ee
    rng = random.Random(9)
    slow = 0
    steps = {}
    fall = [0, 0]

    def rb(D, err):
        w = K.msb(D) - 236
        if w < 2:
            return True
        half = 1 << (w - 1)
        low = D & ((1 << w) - 1)
        return abs(low - half) <= err

    def gen(xv, br):
        """The generic region: seed, cheap stage, lwlog; measured against err."""
        nonlocal slow
        x = K.encode(xv)
        xv = dec(x)
        s, e, m = K.unpack(x)
        u = e - BIAS
        if s and u == -2 and lwy(m)[1] <= -258:
            return
        if br == 0 and not s and u >= -3:
            w, run = lwsw(x), True
        elif br == 0:
            w, run = lwso(x), u >= -23
        else:
            w, run = lwsm(x), True
        nc = 0
        if run:
            w, nc = lwfast(x, w)
        Wv = lambertw(xv, br).real
        D, err, cv = lwlog(ker, x, w)
        if not cv:
            slow += 1
            return
        uw = ((w >> 236) & 0x7FFFF) - BIAS
        name = f"lambertW{'0' if br == 0 else 'm1'}, log form"
        M.add(name, err, D, abs(Wv) * power(2, 254 - uw))
        st = steps.setdefault(name, {})
        st[nc] = st.get(nc, 0) + 1
        fall[0] += 1
        fall[1] += rb(D, err)

    def near(xv, br):
        x = K.encode(xv)
        xv = dec(x)
        s, e, m = K.unpack(x)
        if xv < -1 / Ee or e != BIAS - 2:
            return
        Y, ey, yh, yl = lwy(m)
        if Y == 0 or ey > -258:
            return
        D, err, nst, at = lwbr(Y, ey, yh, yl, br == -1)
        name = f"lambertW{'0' if br == 0 else 'm1'}, q form"
        exact = abs(lambertw(xv, br).real) * power(2, 254)
        M.add(name, err, D, exact)
        st = steps.setdefault(name, {})
        st[nst] = st.get(nst, 0) + 1
        fall[0] += 1
        fall[1] += rb(D, err)

    for _ in range(n):
        gen(mpf(2) ** rng.uniform(-3, 10), 0)
        gen(mpf(2) ** rng.uniform(10, 2000) if rng.random() < 0.7 else mpf(2) ** rng.randint(2000, 260000), 0)
        gen(mpf(2) ** rng.uniform(-262000, -3), 0)
        gen(-mpf(2) ** rng.uniform(-80, -1.64), 0)
        gen(-mpf(2) ** rng.uniform(-300, -1.86) if rng.random() < 0.8 else -mpf(2) ** -rng.uniform(300, 262000), -1)
        for br in (0, -1):
            near(-1 / Ee + mpf(2) ** -rng.uniform(1.5, 235), br)
    print(f"lambert W: {slow} inputs left the fast stage outside 2^-66; rounding test would fire on "
          f"{fall[1]} of {fall[0]} ({100 * fall[1] / fall[0]:.3f}%)")
    for name, st in steps.items():
        print(f"  {name}: steps {dict(sorted(st.items()))}")
    return slow > 0 or lncfit()


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


def kernels(n):
    """The exp/log kernels themselves (kernel254.py): each fit's certified sup
    norm, then each kernel's largest error on n random and edge inputs against
    its stated bound."""
    ker, _, _ = K.build()
    for ft in (ker.fit_exp, ker.fit_ln, ker.fit_lnw, ker.fit_em1):
        print(ft.line())
    return K.measure_kernels(ker, random.Random(254), n)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    bad = kernels(n)
    bad |= run(n)
    bad |= sure(n * 4)
    bad |= cf_depth(max(n // 20, 50))
    sys.exit(1 if bad else 0)

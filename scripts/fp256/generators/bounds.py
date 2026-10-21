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
                        16 + 2 yb (40 + 2|u|) off it (log2m 37 + Lm's shift 2^sh <= 2|u|),
                                             yb >= |y| (|n| + 1); 6 + 1.39 x t's error
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
        yb = (my >> (236 - uy)) + 1 if uy <= 60 else 1 << 60
        err = 16 + 12 * (k + 1) if band is not None else 16 + 2 * yb * (40 + 2 * abs(ex - BIAS))
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
    return M.report()


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
    bad |= cf_depth(max(n // 20, 50))
    sys.exit(1 if bad else 0)

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
  erf, erfc, erfs            erfs (2^-192)               ERR_S = 3 2^44 (2^45.58): derived in
                                                         erf_model.py, 2^45.29 (exp2frac's 2^-146.7
                                                         times erf, the floors)
  erf, erfc, erfct           erfct (2^-192)              ERR_T = 2^20: derived 2^19.41 (e^(-x^2)'s
                                                         error times erfc(4), the certified fit)
  normCdf, erfs and erfct    erfc(y)/2 or 1 - it         ERR_S, ERR_T (y = x/sqrt 2 at 2^-192
                             (2^-192)                    and the halving: err/2 + 3.2 and + 1)

Later phases add the regions of the tests they introduce (rbad127's err per
op). The models' agreement with the Yul is checked by the sweep (make sweep)
and the kernels' generators (kernel192.py --check, expk.py --check).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from mpmath import mp, mpf, log, power, cbrt as mcbrt, erf as merf, erfc as merfc, ncdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import precise_model as P  # noqa: E402
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
    erf_(M, rng, n)
    bad = M.report()
    print(f"{sum(1 for r in M.rows.values() if r[3] >= 1)} regions over their bound")
    return bad


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    sys.exit(1 if run(n) else 0)

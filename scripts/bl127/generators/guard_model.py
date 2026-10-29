#!/usr/bin/env python3
"""Model of the guard-bit transcendental kernels (#50) in exact integer
arithmetic, as the Yul will run them, plus the constants they need.

    uv run scripts/bl127/generators/guard_model.py            # fit, measure, print constants
    uv run scripts/bl127/generators/guard_model.py --old      # also measure the current floor kernels

Kernels run at an internal scale of 2^-192 (64 guard bits below the
format's 2^-128), every product floors at 2^-192, and the result is rounded
to nearest once at the end. Coefficients come from a Chebyshev fit at 120
digits with the degree chosen so the polynomial's own error is below
2^-140, and are quantised to 2^-192.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from mpmath import mp, mpf, log, exp, power, nint, cos, pi, matrix, lu_solve

mp.dps = 120
ROOT = Path(__file__).resolve().parents[3]
MASK = (1 << 256) - 1
G = 192                      # internal fractional bits
GS = 1 << G
ONE = 1 << 128
M128 = ONE - 1
M192 = GS - 1


# ---------------------------------------------------------------------------
# fits
# ---------------------------------------------------------------------------

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


def max_err(coeffs, func, a, b, pts=4000):
    worst = mpf(0)
    for i in range(pts + 1):
        x = a + (b - a) * i / pts
        r = coeffs[-1]
        for c in reversed(coeffs[:-1]):
            r = r * x + c
        worst = max(worst, abs(r - func(x)))
    return worst


def choose(func, a, b, lo, hi, target_bits=140):
    for d in range(lo, hi):
        c = fit(func, d, a, b)
        e = max_err(c, func, a, b)
        if e < mpf(2) ** (-target_bits):
            return d, c, e
    raise RuntimeError("no degree reached the target")


def q(v) -> int:
    """quantise a real to the 2^-192 grid, two's complement in 256 bits"""
    return int(nint(v * GS)) & MASK


def signed(w: int) -> int:
    return w - (1 << 256) if w >> 255 else w


# ---------------------------------------------------------------------------
# the integer kernels, as the Yul will compute them
# ---------------------------------------------------------------------------

def mulg(a: int, b: int) -> int:
    """floor(a * b / 2^192) on signed 256-bit words, the 512-bit product kept."""
    return (signed(a) * signed(b)) >> G & MASK


def mulraw(a: int, b: int) -> int:
    return (signed(a) * signed(b)) >> 128 & MASK


def round64(r: int) -> int:
    """2^-192 -> 2^-128, round half up (sar after adding 2^63)"""
    return (signed(r) + (1 << 63)) >> 64 & MASK


class Kernels:
    def __init__(self, exp_c, log_c, rt, inv):
        self.exp_c = exp_c      # ascending c0..cn at 2^-192
        self.log_c = log_c
        self.rt = rt            # thresholds 2^(1/2^k), k=1..7, at 2^-192
        self.inv = inv          # multipliers 2^(-1/2^k) at 2^-192

    def exp2frac(self, f: int) -> int:
        """2^f for f in [0, 2^192) at 2^-192, result at 2^-192"""
        r = self.exp_c[-1]
        for c in reversed(self.exp_c[:-1]):
            r = (mulg(r, f) + c) & MASK
        return r

    def exp2core(self, t: int) -> int:
        """2^t for t at 2^-192 scale (signed), result rounded to 2^-128"""
        t = signed(t)
        if t == 0:
            return ONE
        if t < 0:
            at = -t
            k = at >> G
            f = at & M192
            if f == 0:
                return ONE >> k
            v = self.exp2frac(GS - f)                      # 2^(1-f) at 2^-192, in [1,2)
            sh = 64 + k + 1
            return (v + (1 << (sh - 1))) >> sh              # round to nearest
        k = t >> G
        f = t & M192
        v = self.exp2frac(f)                               # [1, 2) at 2^-192
        if k >= 64:
            return v << (k - 64)                            # exact: the guard bits become result bits
        sh = 64 - k
        return (v + (1 << (sh - 1))) >> sh

    def exp2(self, x: int) -> int:        # x at 2^-128
        return self.exp2core((signed(x) << 64) & MASK)

    def log2g(self, x: int) -> int:
        """log2(x) for x > 0 at 2^-128, result at 2^-192 (signed word)"""
        m = x.bit_length() - 1
        if x & (x - 1) == 0:
            return ((m - 128) << G) & MASK
        s = m - 128
        mm = (x >> s) if s >= 0 else (x << -s)            # mantissa in [1,2) at 2^-128
        mm <<= 64                                          # now at 2^-192
        acc = 0
        for k in range(7):
            if mm >= self.rt[k]:
                mm = mulg(mm, self.inv[k])
                acc += 1 << (G - 1 - k)
        f = mm - GS
        r = self.log_c[-1]
        for c in reversed(self.log_c[:-1]):
            r = (mulg(r, f) + c) & MASK
        r = mulg(r, f)
        return (((m - 128) << G) + acc + signed(r)) & MASK

    def log2(self, x: int) -> int:
        return round64(self.log2g(x))

    def ln(self, x: int) -> int:
        return round64(mulg(self.log2g(x), self.LN2))

    def log10(self, x: int) -> int:
        return round64(mulg(self.log2g(x), self.INVLOG2_10))

    def exp(self, x: int) -> int:
        return self.exp2core(mulg(signed(x) << 64 & MASK, self.LOG2E))


# the current kernels, for the before/after
EXP_OLD = [0x100000000000000000000000000000000, 0xb17217f7d1cf79abc9e3b39803f2f637, 0x3d7f7bff058b1d50de2d60dd92e71277, 0xe35846b82505fc599d3b15d9947eebb, 0x276556df749cee539977c16ab26986b, 0x5761ff9e299cc441c5fda6496fc0bb, 0xa184897c363c3b7a585493a61d0c1, 0xffe5fe2c458634358a5e0cbc3190, 0x162c0223a5c823fd9180c0672a87, 0x1b5253d395e7c3d9b7d23fb041c, 0x1e4cf5158b8eca22258a9523c8, 0x1e8cac7351bb1ac06cff974a0, 0x1c3bd650fc2b5e1a3c2798ba, 0x18161931668b3732335b8ec, 0x1314964d60c074d3410b05, 0xe1b74210e03ffef9130e, 0x9c744e6a6d037e9b359, 0x661103e6e8ef83bd5e, 0x3ee3a1d249cac3699, 0x24ae7d9788480f70, 0x1486d87bca24a71, 0x9f29a09462d53, 0x7ac5115747d8]


def old_exp2(x: int) -> int:
    x = signed(x)
    def frac(f):
        r = EXP_OLD[-1]
        for c in reversed(EXP_OLD[:-1]):
            r = (mulraw(r, f) + c) & MASK
        return r
    if x == 0:
        return ONE
    if x < 0:
        ax = -x; k = ax >> 128; f = ax & M128
        if f == 0:
            return ONE >> k
        return frac(ONE - f) >> (k + 1)
    return frac(x & M128) << (x >> 128)


def old_exp(x: int) -> int:
    return old_exp2(mulraw(x & MASK, 0x171547652b82fe1777d0ffda0d23a7d11))


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------

def to_mpf(raw: int):
    return mpf(signed(raw)) / mpf(ONE)


def ulps(got: int, truth) -> float:
    return float((mpf(signed(got)) - truth * ONE))


def bits(got: int, truth) -> float:
    err = abs(mpf(signed(got)) / ONE - truth)
    if err == 0:
        return 256.0
    return float(-log(err / abs(truth), 2))


def measure(name, fn, truthfn, inputs):
    us, bs = [], []
    for x in inputs:
        t = truthfn(to_mpf(x))
        g = fn(x)
        us.append(ulps(g, t)); bs.append(bits(g, t))
    mean = sum(us) / len(us)
    print(f"{name:14} n={len(us):4} bits min {min(bs):7.2f} mean {sum(bs)/len(bs):7.2f} | ULP err mean {mean:+8.3f} max |{max(abs(u) for u in us):8.3f}|")


def main(argv):
    random.seed(1)
    print("fitting exp2 on [0,1)")
    d1, ec, e1 = choose(lambda f: power(2, f), mpf(0), mpf(1), 22, 32)
    print(f"  degree {d1}, max poly error 2^{float(log(e1, 2)):.1f}")
    b = power(2, mpf(1) / 128) - 1
    print("fitting P(f) = log2(1+f)/f on [0, 2^(1/128)-1) (the kernel evaluates f * P(f))")
    P = lambda f: (log(1 + f, 2) / f) if f != 0 else 1 / log(2)
    d2, lc, e2 = choose(P, mpf(0), b, 10, 24)
    print(f"  degree {d2}, max poly error 2^{float(log(e2, 2)):.1f}")
    K = Kernels([q(c) for c in ec], [q(c) for c in lc],
                [q(power(2, mpf(1) / 2 ** (k + 1))) for k in range(7)],
                [q(power(2, -mpf(1) / 2 ** (k + 1))) for k in range(7)])
    K.LN2 = q(log(2)); K.INVLOG2_10 = q(1 / log(10, 2)); K.LOG2E = q(1 / log(2))

    # inputs: the committed vectors (finite, in-domain) plus random ones
    def vec(op, lo, hi):
        xs = [int(s, 16) for s in json.load(open(ROOT / "test/bl127/vectors" / f"{op}.json"))["in0"]]
        xs = [signed(x) for x in xs]
        return [x & MASK for x in xs if lo <= x <= hi]
    # relative bits are meaningless within a few ULPs of underflow, so stay above 2^-100
    exp2_in = vec("exp2", -100 * ONE, 126 * ONE) + [random.randint(-100 * ONE, 100 * ONE) & MASK for _ in range(300)]
    exp_in = vec("exp", -69 * ONE, 87 * ONE) + [random.randint(-69 * ONE, 80 * ONE) & MASK for _ in range(300)]
    log_in = vec("log2", 1, (1 << 255) - 1) + [random.randint(1, 1 << 200) for _ in range(300)] + [random.randint(ONE - (1 << 120), ONE + (1 << 120)) for _ in range(100)]
    log_in = [x for x in log_in if x > 0]

    print("\nnew kernels (guard bits, round to nearest at the end):")
    measure("exp2", K.exp2, lambda x: power(2, x), exp2_in)
    measure("exp", K.exp, exp, exp_in)
    measure("log2", K.log2, lambda x: log(x, 2), log_in)
    measure("ln", K.ln, log, log_in)
    measure("log10", K.log10, lambda x: log(x, 10), log_in)
    if "--old" in argv:
        print("\ncurrent kernels (floor everywhere):")
        measure("exp2 (old)", old_exp2, lambda x: power(2, x), exp2_in)
        measure("exp (old)", old_exp, exp, exp_in)
    x15 = 3 * ONE // 2
    print(f"\nround trip at 1.5: new exp(ln(1.5)) - 1.5 = {signed(K.exp(K.ln(x15))) - x15} ULP")

    if "--emit" in argv:
        print("\n// exp2frac192 coefficients, c0..c%d at 2^-192" % d1)
        for i, c in enumerate(K.exp_c):
            print(f"// c{i}: 0x{c:x}")
        print("// log2poly192 coefficients, c0..c%d at 2^-192" % d2)
        for i, c in enumerate(K.log_c):
            print(f"// c{i}: 0x{c:x}")
        print("// range thresholds / multipliers at 2^-192")
        for k in range(7):
            print(f"// k={k+1}: thr 0x{K.rt[k]:x} inv 0x{K.inv[k]:x}")
        print(f"// LN2 0x{K.LN2:x}\n// 1/log2(10) 0x{K.INVLOG2_10:x}\n// LOG2E 0x{K.LOG2E:x}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

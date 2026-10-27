"""Lemmas R1 and R2: FP127's sqrt is floor(sqrt(x 2^128)) on every input.

    python test/proofs/isqrt.py      # one line per step, exits 1 on any failure

The code (FP127.yul.src, the same in FP127.yul and FP127Lib.sol):

    isqrtw(z): e = (msb(z) - 16) >> 1
               y0 = ((((z >> 2e) + 2^17) 0x57d1c0) >> 32) << e
               five steps y = (y + DIV(z, y)) >> 1, then y = y - [DIV(z, y) < y]
    sqrt(x), 0 < x < 2^128:  isqrtw(x 2^128)
    sqrt(x), x >= 2^128:     sh = (255 - msb(x)) & ~1, z = x 2^sh, y = isqrtw(z), k = 64 - sh/2,
                             r = y 2^k + DIV((z - y^2) 2^(k-1), y), then r = r - 1 if r^2 > x 2^128

Every operation is read on unbounded integers; the steps below show that none leaves a word, so each EVM opcode is
its integer meaning. Write s = sqrt(z) (real) and q = floor(s).

  R1  isqrtw(z) = floor(sqrt(z)) for 2^128 <= z < 2^256.
      a. The seed. m = z >> 2e is in [2^16, 2^18), so y0 = S(m) 2^e with S(m) = ((m + 2^17) 0x57d1c0) >> 32, and
         s / 2^e lies in [sqrt(m), sqrt(m + 1)). Checked for every one of the 196,608 values of m, exactly in
         integers: S(m)^2 <= (1 + E)^2 m and S(m)^2 >= (1 - E)^2 (m + 1), so |y0 / s - 1| <= E.
      b. Each step y' = floor((y + floor(z / y)) / 2) is at least q (y + floor(z/y) = floor(y + z/y) >= floor(2s)
         >= 2q) and at most N(y) = (y + z/y) / 2 = s + (y - s)^2 / (2y). So with u = y / s - 1:
         u1 <= E^2 / (2 (1 - E)), and from then on u > -1/s and u' <= max(u, 1/s)^2 / (2 (1 - max(u, 1/s))).
         Iterated in exact rationals with s >= 2^64 (z >= 2^128), s < 2^128: after five steps y5 - s < 1, so
         y5 is q or q + 1 (it is an integer at least q and below s + 1).
      c. The correction: if y5 = q + 1 then (q + 1)^2 > z, so DIV(z, y5) < y5 and one is taken off; if y5 = q
         then q^2 <= z, DIV(z, q) >= q and nothing is. So the result is q.
      d. No step leaves a word: y < 2s and z / y < 2s, so y + DIV(z, y) < 4s < 2^130; the seed's product is below
         2^18 2^23 = 2^41.
  R2  sqrt(x) = floor(sqrt(x 2^128)) for 0 < x < 2^255.
      Below 2^128, z = x 2^128 is in [2^128, 2^256): R1. Above, msb(x) is in [128, 254], so sh is even in [0, 126],
      z = x 2^sh is in [2^254, 2^256), y = isqrtw(z) = floor(sqrt z) >= 2^127 (R1), and k = 64 - sh/2 is in
      [1, 64] with x 2^128 = z 2^(2k). With X = x 2^128, S = sqrt(X), Y = y 2^k:
      a. r0 = y 2^k + floor((z - y^2) 2^(k-1) / y) = floor((Y + X / Y) / 2), one Newton step from Y.
      b. r0 >= floor(S) (as in R1 b) and r0 <= N(Y) = S + (S - Y)^2 / (2Y) < S + 2^(2k) / (2 y 2^k)
         = S + 2^(k-1) / y <= S + 2^63 / 2^127 < S + 1: r0 is floor(S) or floor(S) + 1.
      c. r0 < 2^193, so r0^2 < 2^386 is exact in mul512 (L1), and the comparison with the pair
         (x >> 128, x 2^128 mod 2^256) is r0^2 > X: one is taken off exactly when r0 = floor(S) + 1.
      d. (z - y^2) <= 2y < 2^129, times 2^(k-1) <= 2^63, is below 2^192: no word is left.

The script checks R1 a and the iteration in R1 b exactly, the numeric bounds R2 relies on, and, as a cross-check that
this reading is the code, compares a line-by-line transcription with math.isqrt on edge and random inputs.
"""

import math
import random
import sys
import time
from fractions import Fraction

W = 2**256
MAGIC = 0x57D1C0


def msb(x):
    return x.bit_length() - 1


def seed(m):
    return ((m + 0x20000) * MAGIC) >> 32


def isqrtw(z):
    # the Yul, operation by operation; every assert is a word the EVM would hold
    e = (msb(z) - 16) >> 1
    m = z >> (2 * e)
    y = seed(m) << e
    assert 0 < y < W
    for _ in range(5):
        t = y + z // y
        assert t < W
        y = t >> 1
    return y - (1 if z // y < y else 0)


def sqrt127(x):
    if x == 0:
        return 0
    if x >> 128 == 0:
        return isqrtw(x << 128)
    sh = (255 - msb(x)) & ~1
    z = x << sh
    assert z < W
    y = isqrtw(z)
    k = 64 - (sh >> 1)
    num = (z - y * y) << (k - 1)
    assert num < W
    r = (y << k) + num // y
    assert r < W
    if r * r > x << 128:
        r -= 1
    return r


def step(name, ok, detail=""):
    print(f"{'PROVED' if ok else 'FAILED'}  {name}  {detail}".rstrip(), flush=True)
    return ok


def r1a():
    # the smallest E = 2^-n for which every m passes, found by trying n down from 24
    ms = range(2**16, 2**18)
    for n in range(24, 0, -1):
        E = Fraction(1, 2**n)
        lo, hi = (1 - E) ** 2, (1 + E) ** 2
        if all(seed(m) ** 2 <= hi * m and seed(m) ** 2 >= lo * (m + 1) for m in ms):
            return n, E
    return None, None


def r1b(E):
    # u1 from the seed; then four more steps, each from max(u, 1/s) with the smallest s (2^64) the worst
    floor_u = Fraction(1, 2**64)
    u = E**2 / (2 * (1 - E))
    us = [u]
    for _ in range(4):
        v = max(u, floor_u)
        u = v**2 / (2 * (1 - v))
        us.append(u)
    # y5 - s <= s u5 < 2^128 u5 must be below 1
    return us, 2**128 * us[-1] < 1


def main():
    ok = True
    t0 = time.time()
    n, E = r1a()
    ok &= step("R1a", n is not None, f"the seed is within 2^-{n} of sqrt(z) for all 196,608 leading values")
    us, fine = r1b(E)
    ok &= step("R1b", fine, "five steps from it end below s + 1: relative errors " + ", ".join(f"2^{math.log2(float(u)):.0f}" if u > 0 else "0" for u in us))
    # R1 d: y < 2s and z / y < 2s hold while u stays in (-1/2, 1)
    ok &= step("R1d", E < Fraction(1, 2) and all(u < 1 for u in us), "no intermediate leaves a word")
    # R2 b: 2^(k-1) / y < 1 with k <= 64 and y >= 2^127
    ok &= step("R2b", Fraction(2**63, 2**127) < 1, "the last Newton step lands on floor or floor + 1")
    ok &= step("R2d", ((2 * (2**128 - 1)) << 63) < 2**192 and (2**193) ** 2 < 2**512, "no intermediate leaves a word")
    # cross-check: the transcription is the code's reading; edges, perfect squares and their neighbours, random words
    rnd = random.Random(127)
    xs = [1, 2, 3, 2**126, 2**126 + 1, 2**128 - 1, 2**128, 2**128 + 1, 2**255 - 1]
    xs += [2**126 * k * k + k for k in range(1, 200)]
    for b in range(0, 255):
        xs += [2**b, 2**b + 1, max(1, 2**b - 1)]
    for _ in range(20000):
        b = rnd.randrange(1, 256)
        x = rnd.randrange(1, min(2**b, 2**255))
        xs.append(x)
        r = math.isqrt(x << 128)
        xs += [((r * r) >> 128) or 1, (((r + 1) ** 2 - 1) >> 128) or 1]
    bad = [x for x in xs if 0 < x < 2**255 and sqrt127(x) != math.isqrt(x << 128)]
    ok &= step("R-cross", not bad, f"the transcription equals math.isqrt on {len(xs):,} inputs" + (f"; first miss {bad[0]}" if bad else ""))
    print(f"{'PROVED' if ok else 'FAILED'}  R1  isqrtw(z) = floor(sqrt z) for 2^128 <= z < 2^256  ({time.time() - t0:.1f}s)")
    print(f"{'PROVED' if ok else 'FAILED'}  R2  FP127 sqrt(x) = floor(sqrt(x 2^128)) for 0 < x < 2^255  ({time.time() - t0:.1f}s)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The seed of FP127's isqrtw: why five Newton steps give floor(sqrt(z)).

    uv run scripts/fp127/generators/isqrt_seed.py

isqrtw(z), z >= 2^16: t = msb(z) (CLZ), e = (t - 16) >> 1, m = z >> 2e in
[2^16, 2^18), the seed y0 = ((m + 2^17) C >> 32) << e (a linear fit of sqrt
on the normalised mantissa), five steps y <- floor((y + floor(z / y)) / 2),
then y -= (floor(z / y) < y).

The bound. For z in [m 4^e, (m + 1) 4^e) and s = sqrt(z), the seed ratio
r = y0 / s lies in [Y / sqrt(m + 1), Y / sqrt(m)], Y = (m + 2^17) C >> 32,
taken over every m. A floored step is at most the real Newton step, which
increases with y above s and decreases with y below it, and it never falls
under floor(s). So y_k - s <= s E_k, E_1 = (1 - r)^2 / (2r) and
E_{k+1} = E_k^2 / (2 (1 + E_k)), at the worst r. With s < 2^128,
s E_5 < 1 means y_5 is floor(s) or floor(s) + 1, which the last line fixes.
The script prints the ratio range, E_5 and its margin, and checks the
model against math.isqrt on powers of two, squares and their neighbours,
and random z of every bit length.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction

C = 0x57D1C0      # the fit's multiplier: ratio range balanced around 1
STEPS = 5


def model(z: int) -> int:
    t = z.bit_length() - 1
    e = (t - 16) >> 1
    y = (((z >> (2 * e)) + (1 << 17)) * C >> 32) << e
    for _ in range(STEPS):
        y = (y + z // y) >> 1
    return y - (z // y < y)


def main() -> int:
    lo, hi = math.inf, 0.0
    for m in range(1 << 16, 1 << 18):
        y = ((m + (1 << 17)) * C) >> 32
        lo = min(lo, y / math.sqrt(m + 1))
        hi = max(hi, y / math.sqrt(m))
    worst = Fraction(0)
    for r in (Fraction(lo) * Fraction(999999, 1000000), Fraction(hi) * Fraction(1000001, 1000000)):
        e = (1 - r) ** 2 / (2 * r)
        for _ in range(STEPS - 1):
            e = Fraction(float(e * e / (2 * (1 + e))) * (1 + 1e-9))   # rounded up, kept small
        worst = max(worst, e)
    margin = math.log2(float(worst)) + 128
    print(f"seed ratio y0 / sqrt(z) in [{lo:.6f}, {hi:.6f}]")
    print(f"after {STEPS} steps: y - sqrt(z) < sqrt(z) {float(worst):.3e} < 2^{margin:.1f} for z < 2^256")
    rnd = random.Random(127)
    n = bad = 0
    for t in range(16, 256):
        zs = [1 << t, (1 << (t + 1)) - 1] + [rnd.randrange(1 << t, 1 << (t + 1)) for _ in range(300)]
        for z in zs:
            q = math.isqrt(z)
            for w in (z, q * q, q * q - 1, (q + 1) ** 2 - 1):
                if (1 << 16) <= w < (1 << 256):
                    n += 1
                    bad += model(w) != math.isqrt(w)
    print(f"model vs math.isqrt: {n} inputs, {bad} wrong")
    return 0 if margin < 0 and bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Model of the erf / erfc / normCdf kernels in exact integer arithmetic, as
the Yul runs them, plus the constants they need.

    uv run scripts/fp127/generators/erf_model.py            # measure, print constants
    uv run scripts/fp127/generators/erf_model.py --emit     # constants only

Two regimes, both at 2^-192 (64 guard bits), rounded once at the end:
  |x| <= T   erf by the all-positive series
             erf(x) = (2/sqrt(pi)) e^(-x^2) x sum_k (2x^2)^k / (2k+1)!!
             summed forward until the term floors to zero at 2^-192.
  |x| >  T   erfc by the continued fraction
             erfc(x) = e^(-x^2) / (sqrt(pi) K),  K = x + (1/2)/(x + 1/(x + (3/2)/(x + ...)))
             as the convergents A_k / B_k of the forward recurrence
             A_k = x A_(k-1) + (k/2) A_(k-2), to depth N(x) = C / floor(x^2) + D.
e^(-x^2) is taken from the exp2 kernel at 2^-192 without rounding (exp2g),
so a result far below one keeps its relative precision. This script reads
the exp2 polynomial from FP127.yul.src so it models the deployed constants.
"""
from __future__ import annotations

import sys
from pathlib import Path

from mpmath import mp, mpf, erf, erfc, ncdf, exp, log, sqrt, pi, nint

mp.dps = 120
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "contracts/src/fp127/FP127.yul.src"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernel192  # noqa: E402
MASK = (1 << 256) - 1
G = 192
GS = 1 << G
ONE = 1 << 128
M192 = GS - 1


def signed(w: int) -> int:
    return w - (1 << 256) if w >> 255 else w


def mulg(a: int, b: int) -> int:
    return (signed(a) * signed(b)) >> G & MASK


def round64(r: int) -> int:
    return (signed(r) + (1 << 63)) >> 64 & MASK


def q(v) -> int:
    return int(nint(v * GS)) & MASK


def divg(a: int, b: int) -> int:
    """floor(a * 2^192 / b), the guard-scale quotient (divu(shl(64, a), b))."""
    return (a << G) // b


# ---------------------------------------------------------------------------
# the exp2 kernel: kernel192.py's model of the Yul (kernel192.py --check
# holds the source to it)
# ---------------------------------------------------------------------------

def exp2frac(f: int) -> int:
    return kernel192.exp2frac(f)


def exp2g(t: int) -> int:
    """2^t at 2^-192, unrounded, for t at 2^-192 with t < 63."""
    t = signed(t)
    if t < 0:
        at = -t
        k = at >> G
        f = at & M192
        if f == 0:
            return GS >> k
        return exp2frac(GS - f) >> (k + 1)
    k = t >> G
    return exp2frac(t & M192) << k


LOG2E = q(1 / log(2))
TWO_OVER_SQRTPI = q(2 / sqrt(pi))
INV_SQRTPI = q(1 / sqrt(pi))
INV_SQRT2 = q(1 / sqrt(2))


def expg(xg: int) -> int:
    return exp2g(mulg(xg, LOG2E))


# ---------------------------------------------------------------------------
# the kernels
# ---------------------------------------------------------------------------

def erf_series(xg: int) -> tuple[int, int]:
    """erf(x) at 2^-192 for 0 <= x <= T; returns (value, iterations)."""
    x2 = mulg(xg, xg) << 1                      # 2 x^2
    term = GS
    s = GS
    k = 0
    while term:
        k += 1
        term = mulg(term, x2) // (2 * k + 1)
        s += term
    e = expg((-mulg(xg, xg)) & MASK)
    v = mulg(mulg(mulg(xg, e), s), TWO_OVER_SQRTPI)
    return v, k


def divg2(a: int, b: int) -> int:
    """floor(a * 2^192 / b) by two 2^128 stages, as the Yul's divg does."""
    qh = (a << 128) // b
    r = (a << 128) - qh * b
    ql = (r << 128) // b
    return (qh << 64) + (ql >> 64)


def erfc_cf(xg: int, n: int) -> int:
    """erfc(x) at 2^-192 for x > T: the continued fraction's convergents
    A_k / B_k by the forward recurrence A_k = x A_(k-1) + (k/2) A_(k-2),
    renormalised by 2^-64 whenever A_k exceeds 2^240, depth n."""
    am, an = GS, xg           # A_-1 = 1, A_0 = x  (at a common scale)
    bm, bn = 0, GS            # B_-1 = 0, B_0 = 1
    for k in range(1, n + 1):
        a2 = mulg(xg, an) + (k * am >> 1)
        b2 = mulg(xg, bn) + (k * bm >> 1)
        am, an, bm, bn = an, a2, bn, b2
        if an >= 1 << 240:
            am >>= 64; an >>= 64; bm >>= 64; bn >>= 64
    e = expg((-mulg(xg, xg)) & MASK)
    return divg2(mulg(e, bn), mulg(an, q(sqrt(pi))))


def depth(x: float, C: int, D: int) -> int:
    return C // max(int(x * x), 1) + D


def bits(got: int, truth) -> float:
    err = abs(mpf(signed(got)) / GS - truth)
    if err == 0:
        return 256.0
    return float(-log(err / abs(truth), 2))


def main(argv):
    if "--emit" in argv:
        print(f"// LOG2E_192          0x{LOG2E:x}")
        print(f"// TWO_OVER_SQRTPI_192 0x{TWO_OVER_SQRTPI:x}")
        print(f"// SQRTPI_192         0x{q(sqrt(pi)):x}")
        print(f"// INV_SQRT2_192      0x{INV_SQRT2:x}")
        return 0

    T = mpf(4)
    print("series regime, 0 < x <= 4: bits against erf, iterations")
    worst = 999
    for i in range(1, 61):
        x = T * i / 60
        xg = int(x * GS)
        v, k = erf_series(xg)
        b = bits(v, erf(mpf(xg) / GS))
        worst = min(worst, b)
        if i % 10 == 0 or i == 1:
            print(f"  x={float(x):5.2f} bits {b:7.2f} iterations {k}")
    print(f"  worst {worst:.2f} bits")
    for e in range(-120, -4, 8):
        xg = GS >> -e
        v, k = erf_series(xg)
        print(f"  x=2^{e:4d} bits {bits(v, erf(mpf(xg) / GS)):7.2f} iterations {k}")

    print("\ncontinued fraction, x > 4: minimal depth for the attainable bits")
    need = {}
    for x in [4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 9.3, 9.9]:
        xg = int(mpf(x) * GS)
        t = erfc(mpf(xg) / GS)
        # the attainable precision is the exp polynomial's (2^-145) or the
        # guard floor on e^(-x^2); ask for within half a bit of depth 400
        target = bits(erfc_cf(xg, 400), t) - 0.5
        n = 4
        while bits(erfc_cf(xg, n), t) < target and n < 400:
            n += 1
        need[x] = n
        print(f"  x={x:4.1f} depth {n:3d} bits {bits(erfc_cf(xg, n), t):7.2f}  erfc={float(t):.3e}")
    # choose C, D so depth(x) >= need for every probe
    for C in range(600, 3000, 50):
        for D in range(2, 12):
            if all(depth(x, C, D) >= n for x, n in need.items()):
                print(f"  depth(x) = {C} // floor(x^2) + {D} covers every probe")
                break
        else:
            continue
        break
    print("\nwith that depth, bits across the regime and normCdf tails:")
    for x in [4.0, 4.2, 4.4, 5.5, 6.6, 7.7, 8.8, 9.2, 9.3]:
        xg = int(mpf(x) * GS)
        got = erfc_cf(xg, depth(x, C, D))
        t = erfc(mpf(xg) / GS)
        rounded = signed(round64(got))
        print(f"  x={x:4.1f} bits {bits(got, t):7.2f} result ULPs {rounded} truth ULPs {float(t * ONE):.3f}")
    print(f"\n// TWO_OVER_SQRTPI_192 0x{TWO_OVER_SQRTPI:x}")
    print(f"// SQRTPI_192         0x{q(sqrt(pi)):x}")
    print(f"// INV_SQRT2_192      0x{INV_SQRT2:x}")
    print(f"// LOG2E_192          0x{LOG2E:x}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

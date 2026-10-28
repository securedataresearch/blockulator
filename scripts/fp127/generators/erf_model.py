#!/usr/bin/env python3
"""Model of the erf / erfc / normCdf kernels in exact integer arithmetic, as
the Yul runs them, plus the constants and the tail polynomial they need.

    uv run scripts/fp127/generators/erf_model.py            # measure, print constants
    uv run scripts/fp127/generators/erf_model.py --emit     # constants only
    uv run scripts/fp127/generators/erf_model.py --yul      # the tail polynomial's Yul
    uv run scripts/fp127/generators/erf_model.py --check    # does FP127.yul.src hold it verbatim?

Two regimes, both at 2^-192 (64 guard bits), rounded once at the end:
  |x| <= T   erf by the all-positive series
             erf(x) = (2/sqrt(pi)) e^(-x^2) x sum_k (2x^2)^k / (2k+1)!!
             summed forward until the term floors to zero at 2^-192.
  |x| >  T   erfc(x) = e^(-x^2) g(x), g(x) = e^(x^2) erfc(x) by one minimax
             polynomial in t = (2x - A - B)/(B - A) on [A, B] = [4, 9.5]
             (normCdf reaches y = 13.3125/sqrt 2 = 9.41), fitted with the
             tolerance 2^-175 e^(x^2): what is rounded is erfc on the 2^-128
             grid, so the fit is held to an absolute 2^-175 on erfc, which
             e^(-x^2) relaxes from 2^-149 relative at x = 4 to 2^-45 at 9.5.
             Signed Horner at 2^-192. Release 2.2's continued fraction (the
             forward recurrence to depth 1700 / floor(x^2) + 10, about 20,000
             gas at x = 4) is kept below as erfc_cf for the comparison.
e^(-x^2) is taken from the exp2 kernel at 2^-192 without rounding (exp2g),
so a result far below one keeps its relative precision. This script reads
the exp2 polynomial from FP127.yul.src so it models the deployed constants.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from mpmath import mp, mpf, erf, erfc, ncdf, exp, log, sqrt, pi, nint

mp.dps = 120
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "contracts/src/fp127/FP127.yul.src"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernel192  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts/fp19/generators"))
import minimax  # noqa: E402
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


# ---------------------------------------------------------------------------
# the tail, x in (4, 9.5]: g(x) = e^(x^2) erfc(x) by a minimax polynomial
# ---------------------------------------------------------------------------

TAIL_A, TAIL_B = mpf(4), mpf("9.5")
TAIL_DEG = 43
TAIL_TOL = 175                 # |P - g| <= 2^-175 e^(x^2): erfc within 2^-175


def _x_of(t):
    return (TAIL_B - TAIL_A) / 2 * t + (TAIL_A + TAIL_B) / 2


@lru_cache(maxsize=1)
def tail_fit():
    """(C, E, sup): the coefficients in t at 2^-192 (signed integers,
    ascending), the Remez level and the certified sup of |P - g| / tol
    after the coefficients' rounding."""
    mp.dps = 90
    g = lambda t: exp(_x_of(t) ** 2) * erfc(_x_of(t))
    w = lambda t: exp(_x_of(t) ** 2) * mpf(2) ** -TAIL_TOL
    ct, E = minimax.remez(g, TAIL_DEG, -1, 1, rel=False, w=w, grid=1500)
    C = [int(nint(c * GS)) for c in ct]
    sup = minimax.certify([mpf(c) / GS for c in C], g, -1, 1, n=3000, rel=False, w=w)
    mp.dps = 120
    return C, E, sup


TAIL_K1 = q(2 / (TAIL_B - TAIL_A))                      # t = x K1 - K0
TAIL_K0 = q((TAIL_A + TAIL_B) / (TAIL_B - TAIL_A))


def erfc_tail(xg: int) -> int:
    """erfc(x) at 2^-192 for 4 < x <= 9.5, as the Yul's erfct runs it."""
    C, _, _ = tail_fit()
    t = signed((mulg(xg, TAIL_K1) - TAIL_K0) & MASK)
    p = C[-1]
    for c in reversed(C[:-1]):
        p = ((p * t) >> G) + c
    e = expg((-mulg(xg, xg)) & MASK)
    return mulg(e, p & MASK)


def emit_yul() -> str:
    C, E, sup = tail_fit()
    lines = [
        "/// erfc(x) at 2^-192 for 4 < x <= 9.5 given at 2^-192: e^(-x^2) g(x),",
        f"/// g(x) = e^(x^2) erfc(x) by the degree-{TAIL_DEG} minimax polynomial in",
        "/// t = (2x - 13.5) / 5.5 on [4, 9.5], fitted to the tolerance 2^-175 e^(x^2)",
        f"/// (erf_model.py: certified {float(sup):.3f} of it after the coefficients'",
        "/// rounding), so erfc is within 2^-175 before e^(-x^2)'s own error; signed",
        "/// Horner at 2^-192, each step's floor under a unit of g, the product",
        "/// written in line (mulg's words, t's sign once). e^(-x^2) is taken",
        "/// unrounded, so a result far below one keeps its bits: erfc(9.3) is the",
        "/// last value above half an ULP and comes out as one ULP. Release 2.2's",
        "/// continued fraction cost about 20,000 gas at x = 4.",
        "function erfct(xg) -> v {",
        f"    let t := sub(mulg(xg, 0x{TAIL_K1:x}), 0x{TAIL_K0:x})",
        "    let tn := slt(t, 0)",
        f"    let p := {_lit(C[-1])}",
        "    let l := 0",
        "    let h := 0",
    ]
    for c in reversed(C[:-1]):
        lines += ["    l := mul(p, t)",
                  "    h := mulmod(p, t, not(0))",
                  "    p := add(or(shl(64, sub(sub(sub(sub(h, l), lt(h, l)), mul(slt(p, 0), t)), mul(tn, p))), "
                  f"shr(192, l)), {_lit(c)})"]
    lines.append("    v := mulg(expg(sub(0, mulg(xg, xg))), p)")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _lit(c: int) -> str:
    return f"0x{c:x}" if c >= 0 else f"sub(0, 0x{-c:x})"


def check_source() -> bool:
    ok = emit_yul().strip("\n") in SRC.read_text()
    print(f"FP127.yul.src holds erf_model.py's tail polynomial verbatim: {'yes' if ok else 'NO'}")
    return ok


def depth(x: float, C: int, D: int) -> int:
    return C // max(int(x * x), 1) + D


def bits(got: int, truth) -> float:
    err = abs(mpf(signed(got)) / GS - truth)
    if err == 0:
        return 256.0
    return float(-log(err / abs(truth), 2))


def main(argv):
    if "--yul" in argv:
        print(emit_yul())
        return 0
    if "--check" in argv:
        return 0 if check_source() else 1
    if "--tail" in argv:
        C, E, sup = tail_fit()
        print(f"tail fit: degree {TAIL_DEG}, Remez level {float(E):.4f}, certified sup {float(sup):.4f} of the tolerance")
        worst = mpf(0)
        for i in range(0, 2201):
            x = TAIL_A + (TAIL_B - TAIL_A) * mpf(i) / 2200
            xg = int(x * GS) + (1 if i == 0 else 0)
            got = erfc_tail(xg)
            err = abs(mpf(signed(got)) - erfc(mpf(xg) / GS) * GS)
            worst = max(worst, err)
        print(f"model against erfc at 2,201 points: largest error {float(worst):.3f} units of 2^-192 "
              f"(2^{float(log(worst, 2)) if worst else float('-inf'):.2f})")
        return 0
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

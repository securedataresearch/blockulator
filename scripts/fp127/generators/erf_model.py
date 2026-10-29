#!/usr/bin/env python3
"""Model of the erf / erfc / normCdf kernels in exact integer arithmetic, as
the Yul runs them, plus the constants and the tail polynomial they need.

    uv run scripts/fp127/generators/erf_model.py            # measure, print constants
    uv run scripts/fp127/generators/erf_model.py --emit     # constants only
    uv run scripts/fp127/generators/erf_model.py --yul      # the tail polynomial's Yul
    uv run scripts/fp127/generators/erf_model.py --check    # does FP127.yul.src hold it verbatim? and --bounds
    uv run scripts/fp127/generators/erf_model.py --bounds   # certify the fit, derive ERR_S and ERR_T

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

import re
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


def erfc_tail(xg: int, C: list[int] | None = None) -> int:
    """erfc(x) at 2^-192 for 4 < x <= 9.5, as the Yul's erfct runs it, on
    the coefficients C (default: the fit's)."""
    if C is None:
        C, _, _ = tail_fit()
    t = signed((mulg(xg, TAIL_K1) - TAIL_K0) & MASK)
    p = C[-1]
    for c in reversed(C[:-1]):
        p = ((p * t) >> G) + c
    e = expg((-mulg(xg, xg)) & MASK)
    return mulg(e, p & MASK)


def emit_yul() -> str:
    C, E, _ = tail_fit()
    sup, _ = certify_tail(tuple(C))
    lines = [
        "/// erfc(x) at 2^-192 for 4 < x <= 9.5 given at 2^-192: e^(-x^2) g(x),",
        f"/// g(x) = e^(x^2) erfc(x) by the degree-{TAIL_DEG} minimax polynomial in",
        "/// t = (2x - 13.5) / 5.5 on [4, 9.5], fitted to the tolerance 2^-175 e^(x^2)",
        f"/// (erf_model.py: within {float(sup):.3f} of it on all of [-1, 1] after the",
        "/// coefficients' rounding, certified by a dense grid and a bound on the",
        "/// error's second derivative), so erfc is within 2^-175 before e^(-x^2)'s",
        "/// own error; signed Horner at 2^-192, the 43 floors under 43 units of g,",
        "/// the product written in line (mulg's words, t's sign once). e^(-x^2) is",
        "/// taken unrounded, so a result far below one keeps its bits: erfc(9.3)",
        "/// is the last value above half an ULP and comes out as one ULP. In all",
        "/// within 2^19.4 units of 2^-192, e^(-x^2)'s error at x = 4 the most of it",
        "/// (erf_model.py --bounds): the rounding tests' 2^20. Release 2.2's",
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


# ---------------------------------------------------------------------------
# 3.0: the rounding tests' bounds, derived (bounds127.py measures them)
# ---------------------------------------------------------------------------
#
# erf, erfc and normCdf round a value v at 2^-192 once (round64); from 3.0
# rbad127(v, 64, err) first asks whether a value within err of v could round
# to another word, and if so FP19's wide second stage decides (erfw127). err
# is ERR_S for a value built on erfs and ERR_T for one built on erfct, in
# units of 2^-192. Both are derived below, every step bounded in integers:
#
#   e^(-x^2) (expg): x2 = mulg(xg, xg) is x^2 floored (under one unit), the
#     exponent mulg(-x2, LOG2E) is within dtau = 1.4427 + x^2/2 + 1 units of
#     -x^2 log2 e (x2's floor times log2 e, LOG2E's rounding times x^2, its
#     own floor), exp2frac is within eb (kernel192.py's bound, 2^45.3 units
#     on [1, 2)) and exp2g's shift floors once more: E = E* (1 + rho) + one
#     unit, |rho| <= (eb + ln2 dtau) 2^-192.
#   erfs: the series' terms floor (term_k = floor(term_(k-1) d / (2k + 1)),
#     d = 2 x2 within two units of 2x^2): eps_k = T_k - term_k obeys
#     eps_k <= eps_(k-1) r_k + 2 T_(k-1) / (2k + 1) + 1, r_k = 2x^2/(2k + 1),
#     the loop stops at some K with T_K <= eps_K (term_K = 0) and no later
#     than the first T_k < 1, so S is short by at most the eps up to there
#     and the true tail from the earliest possible K; then three floored
#     products and 2/sqrt(pi) rounded at 2^-192. erf(x) rho dominates.
#   erfct: P is the tail fit, certified rigorously below (certify_tail:
#     |P - g| <= sup 2^-175 e^(x^2) on all of [-1, 1], not only on a grid);
#     t is within 0.5 x + 1.5 units of (2x - 13.5)/5.5 (K1's and K0's
#     rounding, the floor), which moves g by at most |g'| 2.75 of that,
#     |g'(x)| <= 1/(sqrt(pi) x^2); the Horner's 43 floors add under
#     sum |t|^j <= 43 units of g; times E, floored: erfc(x) rho + g + the fit's
#     2^17 sup + e^(-x^2)(43 + ...) + 1.
#   normCdf: y = x/sqrt 2 at 2^-192 is within 0.5 x + 1 units, which moves
#     erfc(y) by under 2/sqrt(pi) of that, and the halving floors once: under
#     err/2 + 3.2 for the series, err/2 + 1 for the tail, so ERR_S and ERR_T
#     cover it too.
#   erfc for x < 0 and normCdf for x > 0 test the value before 2 - v (1 - v):
#     the low bits mirror, so that is 2 - v's test with err one less, still
#     above the bounds; each branch's err is then a constant, which solc
#     folds into the inlined rbad127 (about 40 to 80 gas a call in all).

ERR_S = 0x300000000000      # 3 2^44 = 2^45.58 units of 2^-192
ERR_T = 0x100000            # 2^20


def source_tail() -> list[int]:
    """erfct's coefficients as FP127.yul.src holds them, ascending in t."""
    body = SRC.read_text().split("function erfct(xg) -> v {", 1)[1].split("\n}\n", 1)[0]
    lits = [l.strip().removeprefix("let p := ") for l in body.splitlines() if l.strip().startswith("let p := ")]
    lits += [l.rsplit("shr(192, l)), ", 1)[1][:-1] for l in body.splitlines() if l.strip().startswith("p := add(")]

    def val(s):
        return -int(s[len("sub(0, "):-1], 16) if s.startswith("sub(0, ") else int(s, 16)
    return [val(s) for s in reversed(lits)]


def g_tail(x):
    return exp(x * x) * erfc(x)


def gder_bound(n: int, x):
    """|g^(n)(x)| for g = e^(x^2) erfc(x), x > 0: g = (2/sqrt pi) int_0^inf
    e^(-s^2 - 2xs) ds, so |g^(n)| <= (2/sqrt pi) 2^n int s^n e^(-2xs) ds =
    n!/(sqrt(pi) x^(n+1))."""
    return mp.factorial(n) / (sqrt(pi) * x ** (n + 1))


@lru_cache(maxsize=4)
def certify_tail(C: tuple[int, ...], N: int = 20000, NB: int = 1000):
    """A rigorous sup over t in [-1, 1] of |P(t) - g(x(t))| / (2^-175 e^(x^2))
    for P with the integer coefficients C at 2^-192 (exact in mpmath). On N
    equal steps, |e(t)| on a step is at most the larger end value plus
    h^2/8 max |e''| (linear interpolation's remainder); max |e''| on each of
    NB blocks is bounded by e'''s Taylor series at the block's centre to
    order 41 (e^(j) = P^(j) - g^(j) 2.75^j exactly, g's derivatives by the
    recurrence g^(n+1) = 2x g^(n) + 2n g^(n-1), g' = 2xg - 2/sqrt pi), each
    term in absolute value, plus the Lagrange remainder by e^(44) = -g^(44)
    2.75^44 (P has degree 43), bounded by gder_bound. Each step's bound is
    divided by the tolerance at its left end, the smaller (it grows with x).
    Returns (sup, the largest sampled value)."""
    assert N % NB == 0 and len(C) == TAIL_DEG + 1
    with mp.workdps(110):
        Cr = [mpf(c) / GS for c in C]
        half = (TAIL_B - TAIL_A) / 2
        mid = (TAIL_A + TAIL_B) / 2
        tol = lambda x: exp(x * x) * mpf(2) ** -TAIL_TOL

        def P(cs, t):
            r = mpf(0)
            for v in reversed(cs):
                r = r * t + v
            return r

        def ders(c):
            x = half * c + mid
            gs = [g_tail(x), None]
            gs[1] = 2 * x * gs[0] - 2 / sqrt(pi)
            for n in range(1, TAIL_DEG + 1):
                gs.append(2 * x * gs[n] + 2 * n * gs[n - 1])
            out, cs = [], list(Cr)
            for j in range(TAIL_DEG + 1):
                out.append(P(cs, c) - gs[j] * half ** j)
                cs = [k * cs[k] for k in range(1, len(cs))]
            return out

        r = mpf(1) / NB
        m2 = []
        for b in range(NB):
            c = -1 + (2 * b + 1) * r
            d = ders(c)
            s = sum(abs(d[j + 2]) * r ** j / mp.factorial(j) for j in range(TAIL_DEG - 1))
            xlo = half * (c - r) + mid
            s += gder_bound(TAIL_DEG + 1, xlo) * half ** (TAIL_DEG + 1) * r ** (TAIL_DEG - 1) / mp.factorial(TAIL_DEG - 1)
            m2.append(s)
        h = mpf(2) / N
        ts = [-1 + h * i for i in range(N + 1)]
        es = [abs(P(Cr, t) - g_tail(half * t + mid)) for t in ts]
        sup = mpf(0)
        sampled = mpf(0)
        for i in range(N):
            lo = tol(half * ts[i] + mid)
            sampled = max(sampled, es[i] / lo)
            bound = (max(es[i], es[i + 1]) + h * h / 8 * m2[i * NB // N]) / lo
            sup = max(sup, bound)
        return sup, sampled


def exp_eb():
    """exp2frac's bound in units of 2^-192 (kernel192.py)."""
    return kernel192.kernels().exp2frac_bound()


def erfs_bound(a, b):
    """The largest |erfs(xg) - erf(x) 2^192| for x in [a, b], 0 <= a < b <= 4,
    in units of 2^-192 (see the comment above ERR_S)."""
    a, b = mpf(a), mpf(b)
    c2 = 2 / sqrt(pi)
    eb = exp_eb()
    dtau = mpf("1.4427") + b * b / 2 + 1
    rho = (eb + log(2) * dtau * (1 + mpf(2) ** -64)) * (1 + mpf(2) ** -64)
    # S(z), z = 2x^2 in [za, zb]: the terms T_k (units of 2^-192) at zb and
    # za, eps_k's bound at zb; the loop stops at some K with T_K(z) <= eps_K
    # (so T_K(za) <= eps_K(zb)) and K <= khi, the first k with T_k(zb) < 1
    zb, za = 2 * b * b, 2 * a * a
    T, Ta, eps = [GS * mpf(1)], [GS * mpf(1)], [mpf(0)]
    k = 0
    while T[-1] >= 1:
        k += 1
        rk = zb / (2 * k + 1)
        T.append(T[-1] * rk)
        Ta.append(Ta[-1] * za / (2 * k + 1))
        eps.append(eps[-1] * rk + 2 * T[-2] / (2 * k + 1) / GS + 1)
    khi = len(T) - 1

    def after(K):
        """sum_(k >= K) T_k(z) / T_K(z) <= 1 + p_(K+1) + p_(K+1) p_(K+2) + ...,
        p_j = zb/(2j + 1) (below one past khi)."""
        q, p, j = mpf(1), mpf(1), K
        while p > mpf(2) ** -80:
            j += 1
            p *= zb / (2 * j + 1)
            q += p
        return q

    # S short by sum_(k < K) eps_k plus the true tail from K, T_K <= eps_K
    dS = max(sum(eps[:K]) + eps[K] * after(K) for K in range(1, khi + 1) if Ta[K] <= eps[K])
    S = (sum(T) + T[-1] * after(khi)) / GS  # S(zb), real, its terms past khi included
    return (erf(b) * rho
            + c2 * (b + 1) * S * (1 + mpf(2) ** -64)
            + c2 * b * exp(-a * a) * dS * (1 + mpf(2) ** -64)
            + 3)


def erfct_bound(a, b, sup):
    """The largest |erfct(xg) - erfc(x) 2^192| for x in [a, b], 4 < a < b <=
    9.5, in units of 2^-192, given the fit's certified sup."""
    a, b = mpf(a), mpf(b)
    eb = exp_eb()
    dtau = mpf("1.4427") + b * b / 2 + 1
    rho = (eb + log(2) * dtau * (1 + mpf(2) ** -64)) * (1 + mpf(2) ** -64)
    dt = b / 2 + mpf("1.5")
    gp = (TAIL_B - TAIL_A) / 2 * dt / (sqrt(pi) * a * a)
    g = 1 / (sqrt(pi) * a)                  # g(x) < 1/(sqrt(pi) x)
    return (erfc(a) * rho * (1 + mpf(2) ** -60)
            + g * (1 + mpf(2) ** -60)
            + sup * mpf(2) ** (G - TAIL_TOL) * (1 + mpf(2) ** -60)
            + exp(-a * a) * (TAIL_DEG + gp)
            + 1)


def derived_bounds(sup, pieces=400):
    """(max erfs bound on (0, 4], max erfct bound on (4, 9.5]), over pieces."""
    s = max(erfs_bound(mpf(4) * i / pieces, mpf(4) * (i + 1) / pieces) for i in range(pieces))
    w = (TAIL_B - TAIL_A) / pieces
    t = max(erfct_bound(TAIL_A + w * i, TAIL_A + w * (i + 1), sup) for i in range(pieces))
    return s, t


def check_bounds() -> bool:
    """The certified tail fit and the derived bounds against the Yul's ERR_S
    and ERR_T (the source must use them)."""
    C = tuple(source_tail())
    sup, sampled = certify_tail(C)
    s, t = derived_bounds(sup)
    src = SRC.read_text()
    uses = all(f"0x{e:x}" in src for e in (ERR_S, ERR_T))
    print(f"erfct's fit: certified sup {float(sup):.4f} of 2^-175 e^(x^2) on all of [-1, 1] "
          f"(largest sampled {float(sampled):.4f})")
    ok = uses
    for nm, v, e in (("erfs", s, ERR_S), ("erfct", t, ERR_T)):
        r = float(v / e)
        ok &= r < 1
        print(f"{nm:6} derived bound 2^{float(log(v, 2)):.2f} units of 2^-192, err 2^{float(log(e, 2)):.2f}: "
              f"ratio {r:.4f}{'' if r < 1 else '  EXCEEDS'}")
    print(f"FP127.yul.src uses ERR_S and ERR_T: {'yes' if uses else 'NO'}")
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
        ok = check_source()
        return 0 if check_bounds() and ok else 1
    if "--bounds" in argv:
        return 0 if check_bounds() else 1
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

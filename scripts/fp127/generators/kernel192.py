#!/usr/bin/env python3
"""FP127's one-word kernels at 2^-192 (Blockulator 2.2): 2^f (exp2frac) and
log2 of a mantissa (log2m), modelled in exact integer arithmetic as the Yul
runs them, with their fits, bounds and Yul text. precise_model.py and
erf_model.py take their exp2frac and log2m from here.

    uv run scripts/fp127/generators/kernel192.py           # fit, certify, measure against the bounds
    uv run scripts/fp127/generators/kernel192.py --yul     # print the Yul
    uv run scripts/fp127/generators/kernel192.py --check   # does FP127.yul.src hold that Yul verbatim?

exp2frac: f in [0, 1) at 2^-192 is split as j/16 + r, r in [0, 1/16);
2^f = T[j] 2^r, 2^r by the degree-15 minimax polynomial on [0, 1/16)
(minimax.py; certified sup norm 2^-147.7 relative), Horner at 2^-192 on r at
2^-256 with each product's high word in line (horner.py), the top steps in
one word, and the table level as v + hi(v, (T - 1) 2^256). Release v5's
kernel was a degree-24 Chebyshev fit on [0, 1) (2^-145.9): 24 products at
92 gas against 15 here, most of them cheaper.

log2m: the mantissa 1 + w in [1, 2) at 2^-192 is reduced by two additive
16-entry levels by word-only operations, as FP19's (kernel254.py): i =
floor(16 w), w1 = 16 (w - i/16)/(16 + i) by one shift and one div, floored at
2^-256, log2(1 + i/16) (at 2^-256, rounded) added; then the same by 1 +
i/256, leaving w2 in [0, 2^-8), and log2(1 + w2) = w2 P(w2) with P the
degree-14 minimax polynomial of log2(1 + w)/w on [0, 2^-8] (2^-153.0
relative): no division, since at FP127's precision the direct polynomial is
cheaper than y = w/(2 + w) and one in y^2 (measured 1,333 against 1,447 gas).
Release v5's was seven multiplicative stages and a degree-14 fit (about
2^-150; 2,594 gas).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from mpmath import mp, mpf, log, power, nint

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/fp19/generators"))
from minimax import remez, certify  # noqa: E402
from horner import Horner, hiline, hiset, tree, hx, hi  # noqa: E402

mp.dps = 110
G = 192
GS = 1 << G
EXP_DEG = 15
LOG_DEG = 14
SRC = ROOT / "contracts/src/fp127/FP127.yul.src"


def l2w(w):
    """log2(1 + w)/w."""
    return log(1 + w, 2) / w if w else 1 / log(2)


class Fit:
    def __init__(self, name, f, deg, a, b):
        self.name, self.deg = name, deg
        self.coeffs, self.E = remez(f, deg, a, b)
        self.sup = certify(self.coeffs, f, a, b)
        # the bounds take the grid's maximum with 2^-10 of it to spare for the
        # gaps between the points (far more than a degree-15 error moves there)
        self.bound = self.sup * (1 + mpf(2) ** -10)

    def line(self):
        return (f"{self.name}: degree {self.deg} minimax, levelled error 2^{float(log(self.E, 2)):.1f}, "
                f"certified sup norm 2^{float(log(self.sup, 2)):.1f} relative on 20,002 points")


def at110(fn):
    """Run fn at 110 digits whatever the caller's mp.dps (bounds.py runs at
    120): the fits' last bits depend on the working precision, and the
    constants must be the ones in the source."""
    def wrapped(*args, **kw):
        with mp.workdps(110):
            return fn(*args, **kw)
    return wrapped


class Kernels192:
    @at110
    def __init__(self):
        h4, h8 = mpf(2) ** -4, mpf(2) ** -8
        self.fit_exp = Fit("2^r", lambda r: power(2, r), EXP_DEG, 0, h4)
        self.fit_log = Fit("log2(1 + w)/w", l2w, LOG_DEG, 0, h8)
        # 2^r: p at 2^-192, r at 2^-256; a one-word step's truncation within
        # 2^36 units of 2^-192 (2^-156 relative), all of them within 2^40
        self.hexp = Horner(self.fit_exp.coeffs, 256, 192, h4, self.fit_exp.bound, power(2, h4), "exp2frac", "x",
                           cheap_step=mpf(2) ** 36, cheap_all=mpf(2) ** 40)
        # P(w): p at 2^-255, w at 2^-256; P's units reach the result times w
        # < 2^-8 at 2^-255, so 2^-71 of a unit of 2^-192 each: the one-word
        # steps within 2^80 of P's units (2^9 of the result's), 2^84 in all
        self.hlog = Horner(self.fit_log.coeffs, 256, 255, h8, self.fit_log.bound, l2w(0), "log2m", "x",
                           cheap_step=mpf(2) ** 80, cheap_all=mpf(2) ** 84)
        self.etab = [int(nint((power(2, mpf(j) / 16) - 1) * power(2, 256))) for j in range(16)]
        # log2(1 + i/16), log2(1 + i/256) at 2^-255, beside w P's 2^-255
        self.ltab = [[int(nint(log(1 + mpf(i) / 16 ** (lv + 1), 2) * power(2, 255))) for i in range(16)]
                     for lv in range(2)]

    # 2^f ------------------------------------------------------------------------
    def exp2frac(self, f: int) -> int:
        """2^f at 2^-192 for f in [0, 2^192), result in [2^192, 2^193)."""
        assert 0 <= f < GS
        x = (f & ((1 << 188) - 1)) << 64
        v = self.hexp.eval(x)
        j = f >> 188
        if j:
            v = hi(v, self.etab[j]) + v
        return v

    def exp2frac_bound(self):
        """In units of 2^-192: the Horner's bound (the fit's within it), times
        the table's 2^(15/16), plus its rounding (half a unit of 2^-256
        times v < 2^194, under 1/2) and the floor."""
        return self.hexp.err * power(2, mpf(15) / 16) + mpf(3) / 2

    # log2 -----------------------------------------------------------------------
    def log2m(self, mm: int) -> int:
        """log2(mm 2^-192) at 2^-192 for mm in [2^192, 2^193)."""
        assert GS <= mm < 2 * GS
        w = mm - GS
        i = w >> 188
        w = ((w - (i << 188)) << 68) // (16 + i)         # w1 at 2^-256, below 2^252
        acc = self.ltab[0][i]
        i = w >> 248
        w = ((w - (i << 248)) << 8) // (256 + i)         # w2 at 2^-256, below 2^248
        acc += self.ltab[1][i]
        p = self.hlog.eval(w)
        return (acc + hi(w, p)) >> 63

    def log2m_bound(self):
        """In units of 2^-192: P's bound (the fit within it) in units of
        2^-255 times w < 2^-8, so 2^-71 each; the tables' roundings (half a
        unit of 2^-255 each), w P's floor (one), w1 and w2's floors (under
        2^-256 each, so 2 log2(e) units of 2^-256 of the logarithm), all
        2^-63 per unit of 2^-255; and the final floor."""
        return self.hlog.err * power(2, -71) + (mpf(1) / 2 * 2 + 1 + 2 * mpf("1.4427") / 2) * power(2, -63) + 1


def emit_yul(K: Kernels192) -> str:
    he, hl = K.hexp, K.hlog
    eb, lb = K.exp2frac_bound(), K.log2m_bound()
    out = [
        f"/// 2^f for f in [0, 1) given at 2^-192, result at 2^-192 in [1, 2): f = j/16 +\n"
        f"/// r, 2^f = T[j] 2^r. 2^r on [0, 1/16) is the degree-{EXP_DEG} minimax polynomial\n"
        f"/// (kernel192.py; certified sup norm 2^{float(log(K.fit_exp.sup, 2)):.1f} relative), Horner at 2^-192 on\n"
        f"/// r at 2^-256 with each product's high word in line, the top {he.ncheap} steps in\n"
        f"/// one word; the table level adds hi(v, (T - 1) 2^256), T - 1 rounded at\n"
        f"/// 2^-256. Within 2^{float(log(eb, 2)):.1f} units of 2^-192 (2^{float(log(eb, 2)) - 192:.1f} relative). The\n"
        f"/// one-word kernel: the erf family, the Lambert W iterations and pow's\n"
        f"/// first try (pow2t) run on it; v5's was a degree-24 fit on [0, 1).\n"
        f"function exp2frac(f) -> r {{\n"
        f"    let x := shl(64, and(f, {hx((1 << 188) - 1)}))"]
    out += ["    " + l for l in he.yul("r")]
    out.append("    let j := shr(188, f)")
    out += tree("j", lambda j: hiline("r", "r", hx(K.etab[j]), "r") if j else "")
    out.append("}\n")
    out.append(
        f"/// log2(m) at 2^-192 for m = mm 2^-192 in [1, 2), unrounded. Two additive\n"
        f"/// levels by word-only operations (kernel192.py, as FP19's log2m): i =\n"
        f"/// floor(16 w) for mm = 1 + w, 1 + w1 = (1 + w)/(1 + i/16) as w1 = 16 (w -\n"
        f"/// i/16)/(16 + i) by one shift and one div, floored at 2^-256, and\n"
        f"/// log2(1 + i/16) (at 2^-255, rounded) added from a table; then the same\n"
        f"/// by 1 + i/256, leaving w2 in [0, 2^-8). log2(1 + w2) = w2 P(w2), P the\n"
        f"/// degree-{LOG_DEG} minimax polynomial of log2(1 + w)/w (certified 2^{float(log(K.fit_log.sup, 2)):.1f}\n"
        f"/// relative) at 2^-255, the top {hl.ncheap} steps in one word. Within {float(lb):.2f} units of\n"
        f"/// 2^-192; v5's seven stages and degree-14 fit were about 2^-150.\n"
        f"function log2m(mm) -> r {{\n"
        f"    let x := sub(mm, {hx(GS)})\n"
        f"    let i := shr(188, x)\n"
        f"    x := div(shl(68, sub(x, shl(188, i))), add(16, i))\n"
        f"    let acc := 0")
    out += tree("i", lambda j: f"acc := {hx(K.ltab[0][j])}" if j else "")
    out.append("    i := shr(248, x)\n"
               "    x := div(shl(8, sub(x, shl(248, i))), add(256, i))")
    out += tree("i", lambda j: f"acc := add(acc, {hx(K.ltab[1][j])})" if j else "")
    out += ["    " + l for l in hl.yul("r")]
    out.append(f"    {hiset('x', 'x', 'r')}\n"
               f"    r := shr(63, add(acc, x))\n}}\n")
    return "\n".join(out)


def check_source(K: Kernels192) -> bool:
    """True when FP127.yul.src holds each emitted function, doc comment
    included, verbatim, so the models here are the Yul that runs."""
    src = SRC.read_text()
    ok = all(b.strip("\n") in src for b in emit_yul(K).split("\n\n") if b.strip())
    print(f"FP127.yul.src holds kernel192.py's Yul verbatim: {'yes' if ok else 'NO'}")
    return ok


def measure(K: Kernels192, n=4000) -> bool:
    rng = random.Random(192)
    fs = [rng.getrandbits(G) for _ in range(n)]
    fs += [0, 1, GS - 1, (1 << 188) - 1, 1 << 188] + [(j << 188) | rng.choice([0, 1, (1 << 188) - 1, rng.getrandbits(188)]) for j in range(16) for _ in range(4)]
    ew = max(abs(mpf(K.exp2frac(f)) - power(2, mpf(f) / GS) * GS) for f in fs)
    ms = [GS + rng.getrandbits(G) for _ in range(n)]
    ms += [GS, GS + 1, 2 * GS - 1] + [GS + (i1 << 188) + (i2 << 184) + rng.choice([0, 1, (1 << 184) - 1, rng.getrandbits(184)]) for i1 in range(16) for i2 in range(16)]
    lw = max(abs(mpf(K.log2m(m)) - log(mpf(m) / GS, 2) * GS) for m in ms)
    print(f"{'kernel':10} {'n':>6} {'max error':>12} {'bound':>12} {'ratio':>7}   (units of 2^-192)")
    bad = False
    for nm, cnt, w, b in (("exp2frac", len(fs), ew, K.exp2frac_bound()), ("log2m", len(ms), lw, K.log2m_bound())):
        r = float(w / b)
        bad |= r >= 1
        print(f"{nm:10} {cnt:6d} {float(w):12.4g} {float(b):12.4g} {r:7.4f}{'  EXCEEDS' if r >= 1 else ''}"
              f"   (2^{float(log(w, 2)) - 192 if w else float('-inf'):.1f}; bound 2^{float(log(b, 2)) - 192:.1f})")
    return bad


_K = None


def kernels() -> Kernels192:
    global _K
    if _K is None:
        _K = Kernels192()
    return _K


def exp2frac(f: int) -> int:
    return kernels().exp2frac(f)


def log2m(mm: int) -> int:
    return kernels().log2m(mm)


def main(argv):
    K = kernels()
    if "--yul" in argv:
        print(emit_yul(K))
        return 0
    if "--check" in argv:
        return 0 if check_source(K) else 1
    for ft in (K.fit_exp, K.fit_log):
        print(ft.line())
    for h in (K.hexp, K.hlog):
        print(f"{h.name}: {len(h.C) - 1} steps, {h.ncheap} in one word (b = {h.b}), bound {float(h.err):.4g} units of 2^-{h.rho}")
    bad = measure(K)
    bad |= not check_source(K)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

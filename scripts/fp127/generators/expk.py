#!/usr/bin/env python3
"""FP127's double-word exp kernel expk: e^r - 1 for r in
[0, ln 2) given at 2^-512, modelled in exact integer arithmetic as the Yul
runs it, with its fit, bound and Yul text. precise_model.py takes expk from
here.

    uv run scripts/fp127/generators/expk.py           # fit, certify, measure against the bound
    uv run scripts/fp127/generators/expk.py --yul     # print the Yul
    uv run scripts/fp127/generators/expk.py --check   # does FP127.yul.src hold that Yul verbatim?

The callers (exp, exp2, exp10, pow, the logarithms' Newton step l2p, cbrt,
expm1, the hyperbolics and Lambert W) round 2^n (1 + s) once at 2^-128 with
n up to 126, so s must hold about 300 bits: a double word. It does not need
512: v5's kernel kept s to 2^-512 and paid for it in products. This one
works in X form, a value H 2^-256 + L 2^-384 with L a small word (under
2^134), so a product's cross terms are one-word multiplies and no carry is
propagated until the end.

r = j1/16 + j2/256 + j3/4096 + u: three 16-entry table levels on the top 12
bits, each e^(j 16^-i) - 1 in X form applied in the expm1 form
s + c + s c; u < 2^-12 goes to e^u - 1 = u + u^2 g(u), g the degree-16
minimax polynomial of (e^u - 1 - u)/u^2 on [0, 2^-12] (minimax.py: a Remez
fit, certified on 20,002 points; no Taylor coefficient). g's top steps run
in one word (horner.py), its last three, where 1/2, 1/6 and 1/24 need more
than one word, in X form. The bits of u below 2^-256 enter as rx (1 + s).

Every constant is floored and every product floors, and g's constant term
is lowered by its fit's bound, so the computed s never exceeds e^r - 1: s
stays below 1 for every r < ln 2 and the final carry cannot overflow.
"""
from __future__ import annotations

import random
import sys
import textwrap
from pathlib import Path

from mpmath import mp, mpf, log, power, expm1, floor as mfloor

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/fp256/generators"))
from minimax import remez, certify  # noqa: E402
from horner import Horner, tree, hx  # noqa: E402

mp.dps = 110
K = 12                      # bits taken by the table levels
DEG = 16                    # g's degree
LEVELS = 3
SRC = ROOT / "contracts/src/fp127/FP127.yul.src"
T256 = 1 << 256
M128 = (1 << 128) - 1
LN2_512 = None              # set in Kernel


def g_fn(u):
    """(e^u - 1 - u)/u^2."""
    return (expm1(u) - u) / u ** 2 if u else mpf(1) / 2


def fl(v, bits) -> int:
    return int(mfloor(v * power(2, bits)))


def at110(fn):
    def wrapped(*args, **kw):
        with mp.workdps(110):
            return fn(*args, **kw)
    return wrapped


class Kernel:
    @at110
    def __init__(self):
        global LN2_512
        with mp.workdps(180):
            LN2_512 = fl(log(2), 512)
        a = power(2, -K)
        self.coeffs, self.E = remez(g_fn, DEG, 0, a)
        self.sup = certify(self.coeffs, g_fn, 0, a)
        self.fit_bound = self.sup * (1 + mpf(2) ** -10)          # relative, on g
        self.gmax = g_fn(a)
        # the one-word tail q = c3 + c4 u + ... at 2^-256, u = t 2^-256
        self.q = Horner(self.coeffs[3:], 256, 256, a, 0, 1, "expk", "t",
                        cheap_step=mpf(2) ** 1, cheap_all=mpf(2) ** 2)
        self.q.C = [fl(c, 256) for c in self.coeffs[3:]]          # floored
        # q's error in units of 2^-256: every constant and step floors (under
        # one unit each) plus the one-word truncations; a full step's high
        # word is taken without its borrow (one unit over at most), so its
        # constant is one unit lower: two units
        um = self.q.umax
        d = len(self.q.C) - 1
        theta = [(1 + st[2]) if st else 2 for st in self.q.steps]
        self.q_err = um ** d + sum(theta[i] * um ** j for i, j in enumerate(range(d - 1, -1, -1)))
        # c0, c1, c2 in X form, floored; c0 lowered so g is never over
        self.shift = self.fit_bound * self.gmax * (1 + mpf(2) ** -8)
        self.cx = [fl(self.coeffs[0] - self.shift, 384), fl(self.coeffs[1], 384), fl(self.coeffs[2], 384)]
        # levels: e^(j 16^-(i+1)) - 1 at 2^-384, floored; level 0 is the top
        # (at 150 digits: 110 is only 365 bits)
        with mp.workdps(150):
            self.tab = [[fl(expm1(mpf(j) / mpf(16) ** (i + 1)), 384) for j in range(16)] for i in range(LEVELS)]
        self.nj = [12, 16, 16]          # r < ln 2 < 12/16: the top level never passes 11
        self.plan_shifts()

    # bounds on L through the kernel, to choose the cross terms' shifts ---------
    def plan_shifts(self):
        # after the polynomial: L of u^2 g is under 2 2^128, plus rx (1 + s), rx < 3 2^128
        Lb = 5 << 128
        self.cshift = []
        for i in (2, 1, 0):
            chmax = max(c >> 128 for c in self.tab[i])
            b = max(128, Lb.bit_length() + chmax.bit_length() - 256)
            self.cshift.append(b)
            Lb = Lb + (1 << 128) + (1 << 128) + (1 << 128) + (Lb * (chmax >> b) >> (256 - b)) + 1
        self.Lmax = Lb
        assert Lb < 1 << 140

    # the model -----------------------------------------------------------------
    def qeval(self, t: int) -> int:
        """g's one-word tail as the Yul runs it: the one-word steps as
        horner.py's, the full steps hi'(p, t) + C - 1 with hi' the high word
        less its borrow, mulmod(p, t, 2^256 - 1) - p t mod 2^256."""
        h = self.q
        p = h.C[-1]
        ts = t >> h.b
        for st, c in zip(h.steps, reversed(h.C[:-1])):
            if st:
                a, sft, _ = st
                pr = (p >> a) * ts
                assert pr < T256
                p = (pr >> sft) + c
            else:
                P = p * t
                p = ((P % (T256 - 1) - P % T256) % T256) + c - 1
            assert 0 <= p < T256
        return p

    def poly(self, t: int, ul: int):
        """e^u - 1 in X form for u = t 2^-256 + ul 2^-384, t < 2^244."""
        q = self.qeval(t)
        h, l = self.cx[2] >> 128, self.cx[2] & M128
        p = t * q
        h, l = h + (p >> 256), l + ((p & (T256 - 1)) >> 128)
        th = t >> 128
        for c in (self.cx[1], self.cx[0]):
            p = t * h
            assert th * l < T256
            l = (c & M128) + (((p & (T256 - 1)) >> 128) + ((th * l) >> 128))
            h = (c >> 128) + (p >> 256)
        Q = t * t
        qh, ql = Q >> 256, Q & (T256 - 1)
        p = qh * h
        assert (qh >> 128) * l < T256
        l = ((p & (T256 - 1)) >> 128) + (((qh >> 128) * l) >> 128) + (((ql >> 128) * (h >> 128)) >> 128)
        sh = (p >> 256) + t
        assert ul * (sh >> 128) < T256
        sl = l + ul + ((ul * (sh >> 128)) >> 128)
        return sh, sl

    def expk(self, r: int) -> int:
        """e^r - 1 at 2^-512 for r in [0, ln 2) at 2^-512 (512-bit ints)."""
        assert 0 <= r < LN2_512
        return self.expkx(r >> 256, (r & (T256 - 1)) >> 128)

    def expkx(self, rh: int, rx: int) -> int:
        """e^r - 1 at 2^-512 for r = rh 2^-256 + rx 2^-384 in [0, ln 2), rx
        under 3 2^128 (X form, as lnmul gives it), as the Yul runs it."""
        assert 0 <= rh < T256 and 0 <= rx < 3 << 128
        t = rh & ((1 << 244) - 1)
        sh, sl = self.poly(t, rx)
        for lv, i in enumerate((2, 1, 0)):
            j = (rh >> (244 + 4 * lv)) & 15
            c = self.tab[i][j]
            ch, cl = c >> 128, c & M128
            b = self.cshift[lv]
            p = sh * ch
            assert (sh >> 128) * cl < T256 and sl * (ch >> b) < T256
            sl = sl + cl + ((p & (T256 - 1)) >> 128) + (((sh >> 128) * cl) >> 128) + ((sl * (ch >> b)) >> (256 - b))
            sh = sh + ch + (p >> 256)
            assert sh < T256
        sh = sh + (sl >> 128)
        assert sh < T256, "s reached 1"
        return (sh << 256) | ((sl & M128) << 128)

    def bound(self):
        """Absolute (= relative to e^r, which is at least 1) error of s, below
        the truth only. g: the fit's bound twice (the lowering), q's error
        times u^3, the X steps' floors; times u^2 <= 2^-24. Then each level's
        floors (the constant, the low word of s c, the two cross terms with
        their truncations: under 8 units of 2^-384) on an error that grows by
        (1 + c) <= 2, and rx's terms (two units)."""
        um = power(2, -K)
        g_err = 2 * self.shift + self.q_err * power(2, -256) * um ** 3 + 6 * power(2, -384)
        e = g_err * um ** 2 + 4 * power(2, -384)
        for _ in range(LEVELS):
            e = 2 * e + 8 * power(2, -384)
        return e + power(2, -384)


def emit_yul(Kn: Kernel) -> str:
    q = Kn.q
    eb = Kn.bound()
    doc = (
        "e^r - 1 for r in [0, ln 2) given in X form, rh 2^-256 + rx 2^-384 with rx under "
        "3 2^128 (as lnmul and expr give it), as a DW (sh, sl). X form throughout: a value "
        "H 2^-256 + L 2^-384 with L a small word, so a product's cross terms are one-word "
        "multiplies and the carry waits for the end (expk.py). r = j1/16 + j2/256 + j3/4096 "
        "+ u: three 16-entry levels pick e^(j 16^-i) - 1 (at 2^-384, floored), multiplied "
        f"in the expm1 form s + c + s c; e^u - 1 = u + u^2 g(u), g the degree-{DEG} minimax "
        f"polynomial of (e^u - 1 - u)/u^2 on [0, 2^-12] (certified sup norm "
        f"2^{float(log(Kn.sup, 2)):.1f} relative), its top {q.ncheap} steps in one word, "
        f"the next {len(q.C) - 1 - q.ncheap} at 2^-256 (the high word less its borrow, one "
        "unit over at most, against a constant one unit lower), the last three in X form; "
        "the bits of u below 2^-256 add rx (1 + s). Every constant and product floors and "
        "g's constant is lowered by the fit's bound, so s is never above e^r - 1 and never "
        f"reaches 1. Within 2^{float(log(eb, 2)):.1f} relative, below. Blockulator 2.2's "
        "eight 2-bit groups and degree-16 tail held s to 2^-512 at 4,046 gas.")
    # formulas are not broken across lines
    for f in ("s + c + s c", "e^u - 1 = u + u^2 g(u)", "rx (1 + s)", "2^-256 + rx 2^-384"):
        doc = doc.replace(f, f.replace(" ", "\x00"))
    out = ["/// " + l.replace("\x00", " ") for l in textwrap.wrap(doc, 74)] + [
        "function expk(rh, rx) -> sh, sl {",
        f"    let t := and(rh, {hx((1 << 244) - 1)})",
        "    {",
    ]
    out += [f"        let ts := shr({q.b}, t)", f"        sh := {hx(q.C[-1])}"]
    for st, c in zip(q.steps, reversed(q.C[:-1])):
        if st:
            a, sft, _ = st
            out.append(f"        sh := add(shr({sft}, mul(shr({a}, sh), ts)), {hx(c)})")
        else:
            out.append(f"        sh := add(sub(mulmod(sh, t, not(0)), mul(sh, t)), {hx(c - 1)})")
    c2, c1, c0 = Kn.cx[2], Kn.cx[1], Kn.cx[0]
    out += [
        "        // g's last three steps in X form: (sh, sl) := c + t (sh, sl)",
        "        let pl := mul(t, sh)",
        "        let ph := mulmod(t, sh, not(0))",
        f"        sh := add(sub(sub(ph, pl), lt(ph, pl)), {hx(c2 >> 128)})",
        f"        sl := add(shr(128, pl), {hx(c2 & M128)})",
        "        let th := shr(128, t)",
    ]
    for c in (c1, c0):
        out += [
            "        pl := mul(t, sh)",
            "        ph := mulmod(t, sh, not(0))",
            f"        sl := add(add(shr(128, pl), shr(128, mul(th, sl))), {hx(c & M128)})",
            f"        sh := add(sub(sub(ph, pl), lt(ph, pl)), {hx(c >> 128)})",
        ]
    out += [
        "        // u + u^2 g, u^2 = (qh, ql) to 2^-512",
        "        let ql := mul(t, t)",
        "        let qh := mulmod(t, t, not(0))",
        "        qh := sub(sub(qh, ql), lt(qh, ql))",
        "        pl := mul(qh, sh)",
        "        ph := mulmod(qh, sh, not(0))",
        "        sl := add(add(shr(128, pl), shr(128, mul(shr(128, qh), sl))), shr(128, mul(shr(128, ql), shr(128, sh))))",
        "        sh := add(sub(sub(ph, pl), lt(ph, pl)), t)",
        "        sl := add(add(sl, rx), shr(128, mul(rx, shr(128, sh))))",
        "    }",
    ]
    for lv, i in enumerate((2, 1, 0)):
        b = Kn.cshift[lv]
        out += [
            f"    // level {3 - lv}: e^(j {16 ** (i + 1)}^-1) - 1",
            "    {",
            f"        let j := and(shr({244 + 4 * lv}, rh), 15)" if lv < 2 else f"        let j := shr({244 + 4 * lv}, rh)",
            "        let ch := 0",
            "        let cl := 0",
        ]
        out += ["    " + l for l in tree("j", lambda j, i=i: f"ch := {hx(Kn.tab[i][j] >> 128)} cl := {hx(Kn.tab[i][j] & M128)}"
                                       if j and j < Kn.nj[i] else "")]
        out += [
            "        let pl := mul(sh, ch)",
            "        let ph := mulmod(sh, ch, not(0))",
            f"        sl := add(add(add(sl, cl), shr(128, pl)), add(shr(128, mul(shr(128, sh), cl)), shr({256 - b}, mul(sl, shr({b}, ch)))))",
            "        sh := add(add(sh, ch), sub(sub(ph, pl), lt(ph, pl)))",
            "    }",
        ]
    out += [
        "    sh := add(sh, shr(128, sl))",
        "    sl := shl(128, sl)",
        "}",
    ]
    return "\n".join(out) + "\n"


def check_source(Kn: Kernel) -> bool:
    src = SRC.read_text()
    ok = emit_yul(Kn).strip("\n") in src
    print(f"FP127.yul.src holds expk.py's Yul verbatim: {'yes' if ok else 'NO'}")
    return ok


def measure(Kn: Kernel, n=4000) -> bool:
    rng = random.Random(512)
    rs = [rng.getrandbits(512) % LN2_512 for _ in range(n)]
    rs += [0, 1, LN2_512 - 1, (1 << 500) - 1, 1 << 500, LN2_512 >> 1]
    for j1 in range(12):
        for j2 in range(16):
            base = (j1 << 508) | (j2 << 504)
            for tail in (0, 1, (1 << 504) - 1, rng.getrandbits(504), (1 << 500) | rng.getrandbits(256)):
                v = base | tail
                if v < LN2_512:
                    rs.append(v)
    # X-form inputs with rx past 2^128, as lnmul leaves it
    xs = [(r >> 256, (r & (T256 - 1)) >> 128) for r in rs]
    for _ in range(n // 4):
        rh = rng.getrandbits(256) % ((LN2_512 >> 256) - 1)
        xs.append((rh, rng.getrandbits(128) + rng.choice([0, 1 << 128, 2 << 128])))
    worst, wr, over = mpf(0), None, 0
    with mp.workdps(140):
        for rh, rx in xs:
            s = Kn.expkx(rh, rx)
            tr = expm1(mpf(rh) / power(2, 256) + mpf(rx) / power(2, 384)) * power(2, 512)
            r = (rh, rx)
            e = tr - s
            if e < 0:
                over += 1
            if e > worst:
                worst, wr = e, r
    b = Kn.bound() * power(2, 512)
    ratio = float(worst / b)
    print(f"expk: {len(xs)} inputs, largest error 2^{float(log(worst, 2)) - 512:.2f} relative (below the truth "
          f"on every input: {'yes' if over == 0 else 'NO, ' + str(over) + ' above'}), bound 2^{float(log(b, 2)) - 512:.2f}, "
          f"ratio {ratio:.3f}")
    return over > 0 or ratio >= 1


_K = None


def kernel() -> Kernel:
    global _K
    if _K is None:
        _K = Kernel()
    return _K


def expk(r: int) -> int:
    return kernel().expk(r)


def expkx(rh: int, rx: int) -> int:
    return kernel().expkx(rh, rx)


def main(argv):
    Kn = kernel()
    if "--yul" in argv:
        print(emit_yul(Kn))
        return 0
    if "--check" in argv:
        return 0 if check_source(Kn) else 1
    print(f"g: degree {DEG} minimax on [0, 2^-{K}], levelled error 2^{float(log(Kn.E, 2)):.1f}, "
          f"certified sup norm 2^{float(log(Kn.sup, 2)):.1f} relative on 20,002 points")
    print(f"q: {len(Kn.q.C) - 1} steps, {Kn.q.ncheap} in one word (b = {Kn.q.b}), error {float(Kn.q_err):.3g} units of 2^-256")
    print(f"cross-term shifts {Kn.cshift}, L under 2^{Kn.Lmax.bit_length()}")
    bad = measure(Kn)
    bad |= not check_source(Kn)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

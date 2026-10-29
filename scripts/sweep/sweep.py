#!/usr/bin/env python3
"""Random-input accuracy sweep of the inline BL127 and BL19 libraries against
correctly rounded truth.

    uv run scripts/sweep/sweep.py          # gen -> forge (test/sweep/Sweep.t.sol) -> score
    uv run scripts/sweep/sweep.py score    # re-score the last forge outputs only
    uv run scripts/sweep/sweep.py --ops cosh,sinh   # only those ops (both libraries, both passes);
                                           # their rows replace the ones in sweep.json, the rest stay
                                           # (the second-stage gas can differ by a unit: the generated
                                           # runner is a smaller contract; the re-baseline runs everything)
    uv run scripts/sweep/sweep.py --lib bl127 --ops exp,ln   # one library's rows only (bl19, bl127, wad)

Release four adds the directed ops, powu and lambertWm1, and a second pass: the
same inputs (the first 4,000 of each) through a test-only copy of BL19Lib whose
rounding test always fails (scripts/bl127/gen.py --wide-lib), so every correctly
rounded op returns its wide second stage. That pass is generated into
test/sweep/wide/ (not committed) and removed after the run.

A third pass runs every op on all its inputs through test-only copies of BL19Lib
and BL127Lib that count each rounding-test fallback (scripts/bl127/gen.py --count-lib:
BL19's rbad firing, BL127's double-word l2p and powu's 512-bit powus), generated into
test/sweep/count/ and removed after the run: the *fallback* column is the share of
inputs that left the fast path. Its results must equal the plain pass's word for word.

Gas is the inline library call alone: Sweep.t.sol reads gasleft() on either side of
the one call, after its dispatch, and subtracts the same window around an assignment.

BL127 has the same two passes for the ops whose rounding tests exist today
(WIDE127, MID127): BL127LibWide with every test forced to fail (gen.py's bl127
"forced" map: rbad127, rbadw, rbadm127, nearmid, pow2t, pow2rt), so every result
comes from the op's last stage (the exponentials' and logs' two-word stages, pow's
exact tie or two-word stage, powu's 512-bit mantissa or pow, compound through powu),
and BL127LibMid with only the fast paths' tests forced (the logs, pow, compound and
atanh return their double-word middle stage, its own test kept). Their outputs are
wide127_* and mid127_*.

Inputs are seeded (20261020; Lambert W 7) and written to cache/sweep/, which is not
committed. BL19 results are compared with the word the oracle (scripts/bl19/oracle.py:
exact rationals and mpmath at 300 digits, half away from zero) returns, as a signed
distance in ULPs. BL127 results are compared with the real truth at 200 digits, as
|got - truth| in units of 2^-128, and with the correctly rounded word: the word
scripts/bl127/oracle.py returns, the rounding the op promises (to nearest under
BL127's tie rule, ties up, the magnitude for powu, compound, cbrt, sinh, tanh and
erf; the directed ops in their direction). The oracle works at 200 digits; where
the truth there lies within 10^-100 of a rounding boundary (an integer or a half
of the grid, beyond which 200 digits could not decide), the word is recomputed at
300 digits and the row counts it (crClose, and crChanged when 300 digits gave
another word). Writes docs/benchmarks/sweep.{json,md}.
"""
import importlib.util
import json
import multiprocessing as mpc
import os
import random
import re
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "bl19"))
import oracle as O  # noqa: E402
from mpmath import mp, mpf, e as E, lambertw, log  # noqa: E402

_spec = importlib.util.spec_from_file_location("fpgen", ROOT / "scripts" / "bl127" / "gen.py")
G = importlib.util.module_from_spec(_spec)
sys.modules["fpgen"] = G
_spec.loader.exec_module(G)
sys.path.insert(0, str(ROOT / "scripts" / "sweep"))
import wad as WD  # noqa: E402  BlockulatorWad's inputs, truth and rows
# BL127's oracle (by path: BL19's is `oracle` above), the correctly rounded word
_spec127 = importlib.util.spec_from_file_location("oracle127", ROOT / "scripts" / "bl127" / "oracle.py")
O127 = importlib.util.module_from_spec(_spec127)
_spec127.loader.exec_module(O127)

D = ROOT / "cache" / "sweep"
OUT = ROOT / "docs" / "benchmarks"
T256 = 1 << 256
ONE = 1 << 128
BIAS = 0x3FFFF
SEED, SEED_LW = 20261020, 7
OPS19 = ["add", "mul", "div", "sqrt", "exp", "ln", "log1p", "expm1", "pow", "erf", "erfc", "normCdf",
          "compound", "lambertW0", "lambertWm1", "powu",
          "mulDown", "mulUp", "divDown", "divUp", "toUintDown", "toUintUp", "toIntDown", "toIntUp",
          "floor", "ceil", "fromUintDown", "fromUintUp", "toFixed18Down", "toFixed18Up",
          # #79
          "exp2", "exp10", "log2", "log10", "log2Up", "cbrt", "sinh", "cosh", "tanh", "atanh",
          "min", "max", "clamp", "avg", "dist", "zeroFloorSub", "inv", "lerp", "frac", "round",
          "factorial", "gavg", "hypot"]
# the ops with a wide second stage, swept again through BL19LibWide
WIDE19 = ["exp", "ln", "log1p", "expm1", "pow", "erf", "erfc", "normCdf", "compound", "lambertW0",
           "lambertWm1", "powu", "exp2", "exp10", "log2", "log10", "sinh", "cosh", "tanh", "atanh"]
WIDE_N = 4000
# the ops with a middle stage (BL19's pow family), swept again through
# BL19LibMid: the fast path's test forced, the middle stage's kept
MID19 = ["pow", "powu", "compound"]
PLAIN = {"toUintDown", "toUintUp", "toIntDown", "toIntUp", "toFixed18Down", "toFixed18Up"}
SEL: set[str] | None = None   # --ops: the ops to run and re-score; None is all of them
LIBSEL: set[str] | None = None   # --lib: the libraries to run and re-score; None is all three
LIBS = ("bl19", "bl127", "wad")


def selected(op: str, lib: str | None = None) -> bool:
    return (SEL is None or op in SEL) and (LIBSEL is None or lib is None or lib in LIBSEL)


def match_tests() -> list[str]:
    """forge's --match-test for the selected ops (every test when all are selected)."""
    if SEL is None and LIBSEL is None:
        return []
    ops = "|".join(sorted(SEL)) if SEL is not None else "\\w+"
    libs = "|".join(l for l in LIBS if LIBSEL is None or l in LIBSEL)
    # forge 1.7 matches the signature, test_x(), so the end allows the parentheses
    return ["--match-test", "^test_(noop|(" + libs + ")_(" + ops + ")x?)(\\(\\))?$"]


OPS127 = ["mul", "div", "sqrt", "exp", "ln", "log2", "pow", "cbrt", "expm1", "erf", "erfc", "normCdf", "compound",
          "exp2", "exp10", "log10", "sinh", "cosh", "tanh", "atanh", "powu", "mulUp", "divUp", "divDown", "toFixed18Up",
          # 3.0: the rest of the ops a correctly rounded BL127 must show
          "log1p", "gavg", "hypot", "inv", "mulDown"]
# BL127's ops with a rounding test today, swept again through BL127LibWide
# (every test forced: their last stage) and, those with a middle stage,
# BL127LibMid (the fast path's test forced). The phases that give the other
# ops a test and a second stage add them here.
WIDE127 = ["ln", "log2", "log10", "log1p", "pow", "compound", "sinh", "cosh", "tanh", "atanh",
           "lambertW0", "lambertWm1", "exp", "exp2", "exp10", "expm1", "powu",
           "erf", "erfc", "normCdf"]
MID127 = ["pow", "compound", "atanh", "ln", "log2", "log10", "log1p"]
WIDE = {"bl19": WIDE19, "bl127": WIDE127}
MID = {"bl19": MID19, "bl127": MID127}
TWO = {"add", "mul", "div", "pow", "compound", "powu", "mulDown", "mulUp", "divDown", "divUp",
       "min", "max", "avg", "dist", "zeroFloorSub", "gavg", "hypot"}
THREE = {"clamp", "lerp"}


# ---- inputs ----------------------------------------------------------------

def f19(rng, emin, emax, neg=0.5):
    e = rng.randint(emin, emax)
    f = rng.getrandbits(236)
    s = 1 if rng.random() < neg else 0
    return (s << 255) | ((BIAS + e) << 236) | f


def f127(rng, lo_bits, hi_bits, neg=0.5):
    """A raw word whose magnitude has its msb in [lo_bits, hi_bits] (value = raw / 2^128)."""
    b = rng.randint(lo_bits, hi_bits)
    m = rng.getrandbits(b) | (1 << b)
    return (-m if rng.random() < neg else m) % T256


def write(name, a, b=None, c=None):
    d = {"a": ["0x%064x" % (x % T256) for x in a]}
    if b is not None:
        d["b"] = ["0x%064x" % (x % T256) for x in b]
    if c is not None:
        d["c"] = ["0x%064x" % (x % T256) for x in c]
    (D / f"{name}.json").write_text(json.dumps(d))


def gen():
    D.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    N, S = 20000, 4000
    write("bl19_add", [f19(rng, -40, 40) for _ in range(S)], [f19(rng, -40, 40) for _ in range(S)])
    write("bl19_mul", [f19(rng, -400, 400) for _ in range(S)], [f19(rng, -400, 400) for _ in range(S)])
    write("bl19_div", [f19(rng, -400, 400) for _ in range(S)], [f19(rng, -400, 400) for _ in range(S)])
    write("bl19_sqrt", [f19(rng, -400, 400, 0) for _ in range(S)])
    write("bl19_exp", [f19(rng, -30, 9) for _ in range(N)])
    write("bl19_ln", [f19(rng, -300, 300, 0) for _ in range(N // 2)] + [f19(rng, -1, 0, 0) for _ in range(N // 2)])
    write("bl19_log1p", [f19(rng, -60, 4, 0.3) for _ in range(N)])
    write("bl19_expm1", [f19(rng, -60, 6) for _ in range(N)])
    write("bl19_pow", [f19(rng, -2, 2, 0) for _ in range(N)], [f19(rng, -8, 6) for _ in range(N)])
    write("bl19_erf", [f19(rng, -8, 2) for _ in range(S)])
    write("bl19_erfc", [f19(rng, -8, 4) for _ in range(S)])
    write("bl19_normCdf", [f19(rng, -8, 4) for _ in range(S)])
    write("bl19_compound", [f19(rng, -40, -5) for _ in range(S)], [rng.randint(1, 40_000_000) for _ in range(S)])
    write("bl19_lambertW0", [f19(rng, -10, 8, 0) for _ in range(S // 2)])
    write("bl127_mul", [f127(rng, 100, 200) for _ in range(S)], [f127(rng, 60, 160) for _ in range(S)])
    write("bl127_div", [f127(rng, 100, 200) for _ in range(S)], [f127(rng, 100, 200) for _ in range(S)])
    write("bl127_sqrt", [f127(rng, 1, 254, 0) for _ in range(S)])
    write("bl127_exp", [f127(rng, 100, 134) for _ in range(S)])
    write("bl127_ln", [f127(rng, 1, 254, 0) for _ in range(S)])
    write("bl127_log2", [f127(rng, 1, 254, 0) for _ in range(S)])
    write("bl127_pow", [f127(rng, 126, 130, 0) for _ in range(S)], [f127(rng, 100, 134) for _ in range(S)])
    write("bl127_cbrt", [f127(rng, 1, 254) for _ in range(S)])
    write("bl127_expm1", [f127(rng, 60, 134) for _ in range(S)])
    write("bl127_erf", [f127(rng, 100, 130) for _ in range(S // 2)])
    write("bl127_normCdf", [f127(rng, 100, 131) for _ in range(S // 2)])
    # erfc joined the BL127 sweep for the second gas pass; its own stream keeps every other op's inputs
    re = random.Random(SEED + 6)
    write("bl127_erfc", [f127(re, 100, 131) for _ in range(S // 2)])
    write("bl127_compound", [f127(rng, 80, 123) for _ in range(S)], [rng.randint(1, 40_000_000) << 128 for _ in range(S)])
    # atanh joined the BL127 sweep for the second gas pass, on its own stream: |x| from 2^-68 up
    # to 1, the last quarter within 2^-1..2^-120 of +-1
    ra = random.Random(SEED + 7)
    write("bl127_atanh", [f127(ra, 60, 127) for _ in range(3 * S // 4)]
          + [(ONE - (ra.getrandbits(ra.randint(8, 127)) | 1)) * ra.choice((1, -1)) for _ in range(S // 4)])
    # BL127 v5: the rest of the exponential family, the hyperbolics, powu and the directed edge ops
    rv = random.Random(SEED + 5)
    write("bl127_exp2", [f127(rv, 100, 134) for _ in range(S)])
    write("bl127_exp10", [f127(rv, 100, 133) for _ in range(S)])
    write("bl127_log10", [f127(rv, 1, 254, 0) for _ in range(S)])
    write("bl127_sinh", [f127(rv, 100, 134) for _ in range(S)])
    write("bl127_cosh", [f127(rv, 100, 134) for _ in range(S)])
    write("bl127_tanh", [f127(rv, 100, 134) for _ in range(S)])
    write("bl127_powu", [f127(rv, 120, 136) for _ in range(S)], [rv.randint(-300, 300) << 128 for _ in range(S)])
    write("bl127_mulUp", [f127(rv, 100, 200) for _ in range(S)], [f127(rv, 60, 160) for _ in range(S)])
    write("bl127_divUp", [f127(rv, 100, 200) for _ in range(S)], [f127(rv, 100, 200) for _ in range(S)])
    write("bl127_divDown", [f127(rv, 100, 200) for _ in range(S)], [f127(rv, 100, 200) for _ in range(S)])
    write("bl127_toFixed18Up", [f127(rv, 1, 250) for _ in range(S)])
    # BL127 Lambert W: W0 log-uniform on (0, 2^100] and within [2^-20, 1/e] of -1/e; W-1 on [-1/e, 0)
    mp.dps = 80
    rl = random.Random(SEED_LW)
    nie = int(-ONE / E)
    w0, wm1 = [], []
    for _ in range(1500):
        if rl.random() < 0.6:
            b = rl.randint(28, 228)
            w0.append(rl.getrandbits(b) | (1 << b))
        else:
            db = rl.randint(108, 126)
            w0.append(nie + (rl.getrandbits(db) | (1 << db)))
        db = rl.randint(1, 126)
        d = rl.getrandbits(db) | (1 << db)
        wm1.append(-d if -d >= nie else nie + (1 << 108) + rl.getrandbits(100))
    # 3.0: both branches within 2^-20 of -1/e down to the smallest input
    # (lwbr's q at 2^-64), and W0 on small negative x (lwfin from the cubic)
    for _ in range(500):
        db = rl.randint(0, 107)
        w0.append(nie + (rl.getrandbits(db) | (1 << db)))
        db = rl.randint(0, 107)
        wm1.append(nie + (rl.getrandbits(db) | (1 << db)))
        db = rl.randint(63, 120)
        w0.append(-(rl.getrandbits(db) | (1 << db)))
    write("bl127_lambertW0", w0)
    write("bl127_lambertWm1", [x for x in wm1 if x < 0])
    gen127()
    gen4()
    WD.gen()


def gen127():
    """3.0's BL127 ops, from their own seed so every earlier op keeps its inputs."""
    rng = random.Random(SEED + 127)
    S = 4000
    # log1p: |x| < 1 at every scale down to 2^-127, both signs, then x from 1 to 2^126
    write("bl127_log1p", [f127(rng, 1, 127) for _ in range(S // 2)] + [f127(rng, 128, 254, 0) for _ in range(S // 2)])
    # gavg: a b fits the word; hypot: both squares fit (where v4's composition did not overflow)
    ga, gb = [f127(rng, 1, 190, 0) for _ in range(S)], [f127(rng, 1, 190, 0) for _ in range(S)]
    ha, hb = [f127(rng, 1, 190) for _ in range(S)], [f127(rng, 1, 190) for _ in range(S)]
    # 3.0 rounds both once from the exact value, whose product cannot overflow: the second half of
    # each over the whole range, from its own seed (gavg's pairs share a sign)
    wr = random.Random(SEED + 1276)
    for i in range(S // 2, S):
        a, b = f127(wr, 1, 254), f127(wr, 1, 254, 0)
        ga[i], gb[i] = a, ((-b) % T256 if a >> 255 else b)
        ha[i], hb[i] = f127(wr, 1, 254), f127(wr, 1, 254)
    write("bl127_gavg", ga, gb)
    write("bl127_hypot", ha, hb)
    write("bl127_inv", [f127(rng, 1, 254) for _ in range(S)])
    write("bl127_mulDown", [f127(rng, 100, 200) for _ in range(S)], [f127(rng, 60, 160) for _ in range(S)])
    # pow and powu's last quarter (3.0): bases within 2^-8 of one at every
    # scale with exponents spreading y log2 x over the whole range (where
    # v5's absolute log missed), and the exact ties (x^y an odd multiple of
    # 2^-129); for powu |n| from 2^16 (pow's road) and its ties
    mp.dps = 60
    ties = [(3 << 127, 129 << 128), (1 << 127, 129 << 128), (8 << 128, -43 << 128)]
    for k in range(1, 8):
        ties.append((3 ** (2 ** k) << (128 - 2 ** k), (129 << 128) >> k))
    for _ in range(12):
        c = rng.getrandbits(rng.randint(2, 84)) | 1
        ties += [(c << 85, 3 << 128), ((c * c) << 42, 3 << 127)]
    for k in range(1, 6):
        b = rng.randrange(3, 62, 2)
        ties.append(((b ** (2 ** k)) << (128 - 3 * 2 ** k), (43 << 128) >> k))
    near, yn = [], []
    for _ in range(S // 4 - len(ties)):
        d = rng.getrandbits(rng.randint(1, 120)) | 1
        x = ONE + d * rng.choice((1, -1))
        t = mpf(rng.uniform(-130, 127)) if rng.random() < 0.7 else mpf(2) ** rng.uniform(-20, 7) * rng.choice((1, -1))
        near.append(x)
        yn.append(max(min(int(t / mp.log(mpf(x) / ONE, 2) * ONE), 1 << 254), -(1 << 254)))
    pw = json.loads((D / "bl127_pow.json").read_text())
    keep = 3 * S // 4
    write("bl127_pow", [int(v, 16) for v in pw["a"][:keep]] + near + [a for a, _ in ties],
          [int(v, 16) for v in pw["b"][:keep]] + yn + [b for _, b in ties])
    big, kn = [], []
    for _ in range(S // 8):
        d = rng.getrandbits(rng.randint(1, 100)) | 1
        x = ONE + d * rng.choice((1, -1))
        top = min(126 / abs(float(mp.log(mpf(x) / ONE, 2))), 2.0 ** 120)
        k = rng.randint(1 << 16, max(1 << 16, int(top)))
        big.append(x * rng.choice((1, -1)))
        kn.append(rng.choice((1, -1)) * k << 128)
    for _ in range(S // 8):
        c = rng.getrandbits(rng.randint(2, 84)) | 1
        big.append((c << 85) * rng.choice((1, -1)))
        kn.append(3 << 128)
    pu = json.loads((D / "bl127_powu.json").read_text())
    keep = 3 * S // 4
    write("bl127_powu", [int(v, 16) for v in pu["a"][:keep]] + big, [int(v, 16) for v in pu["b"][:keep]] + kn)


def near_branch(rng, n):
    """Words just above -1/e: -1/e + d for d from 2^-230 to 2^-3."""
    mp.dps = 120
    out = []
    for _ in range(n):
        d = mpf(2) ** -rng.uniform(3, 230)
        out.append(O.encode_mpf(-1 / E + d))
    return out


def gen4():
    """Release four's inputs, drawn from their own seed so the earlier ops'
    inputs are unchanged."""
    rng = random.Random(SEED + 4)
    S, N = 4000, 20000
    # W0 on the negative side and near -1/e; W-1 on [-1/e, 0)
    w0neg = [f19(rng, -64, -3, 1) for _ in range(S // 4)] + near_branch(rng, S // 4)
    write("bl19_lambertWm1", [f19(rng, -300, -3, 1) for _ in range(S // 2)] + near_branch(rng, S // 2))
    write("bl19_powu", [f19(rng, -2, 2) for _ in range(S)],
          [rng.choice([1, -1]) * rng.randint(2, 1 << rng.randint(2, 20)) for _ in range(S)])
    for op in ("mulDown", "mulUp"):
        write(f"bl19_{op}", [f19(rng, -400, 400) for _ in range(S)], [f19(rng, -400, 400) for _ in range(S)])
    for op in ("divDown", "divUp"):
        write(f"bl19_{op}", [f19(rng, -400, 400) for _ in range(S)], [f19(rng, -400, 400) for _ in range(S)])
    # amounts: integers and near-integers to 2^256, a few negatives and tiny values
    for op in ("toUintDown", "toUintUp"):
        write(f"bl19_{op}", [f19(rng, -4, 255, 0.05) for _ in range(S)])
    for op in ("toIntDown", "toIntUp", "floor", "ceil"):
        write(f"bl19_{op}", [f19(rng, -4, 254) for _ in range(S)])
    for op in ("fromUintDown", "fromUintUp"):
        write(f"bl19_{op}", [rng.getrandbits(rng.randint(200, 256)) for _ in range(S)])
    for op in ("toFixed18Down", "toFixed18Up"):
        write(f"bl19_{op}", [f19(rng, -80, 190) for _ in range(S)])
    # wider ranges for the ops whose second stage has more than one branch,
    # appended to the op's own rows ("x" files, merged by load)
    E = S // 2
    write("bl19_expx", [f19(rng, 9, 17) for _ in range(E)])
    write("bl19_expm1x", [f19(rng, 6, 17) for _ in range(E)])
    write("bl19_log1px", [f19(rng, 4, 300, 0) for _ in range(E // 2)] + [f19(rng, -4, -1, 1) for _ in range(E // 2)])
    write("bl19_powx", [f19(rng, -300, 300, 0) for _ in range(E)], [f19(rng, -20, 10) for _ in range(E)])
    write("bl19_compoundx", [f19(rng, -4, 8, 0.3) for _ in range(E // 2)] + [f19(rng, -1, -1, 1) for _ in range(E // 2)],
          [rng.choice([1, -1]) * rng.randint(1, 1 << rng.randint(1, 12)) for _ in range(E)])
    write("bl19_erfcx", [f19(rng, 4, 8) for _ in range(E)])
    write("bl19_normCdfx", [f19(rng, 4, 9, 0.8) for _ in range(E)])
    write("bl19_powux", [f19(rng, -40, 40) for _ in range(E)], [rng.choice([1, -1]) * rng.randint(2, 200) for _ in range(E)])
    write("bl19_lambertW0x", w0neg + [f19(rng, 8, 18, 0) for _ in range(E // 2)] + [f19(rng, 1000, 200000, 0) for _ in range(E // 2)])
    gen79()


def near_one(rng, n):
    """Words within 2^-4 of one, on both sides, at every scale down to 2^-230."""
    mp.dps = 120
    return [O.encode_mpf(1 + mpf(2) ** -rng.uniform(4, 230) * rng.choice([1, -1])) for _ in range(n)]


def gen79():
    """#79's inputs, from their own seed."""
    rng = random.Random(SEED + 79)
    S, N = 4000, 8000
    write("bl19_exp2", [f19(rng, -40, 18) for _ in range(N)])
    write("bl19_exp10", [f19(rng, -40, 16) for _ in range(N)])
    for op in ("log2", "log10"):
        write(f"bl19_{op}", [f19(rng, -300, 300, 0) for _ in range(N // 2)] + [f19(rng, -1, 0, 0) for _ in range(N // 4)]
              + near_one(rng, N // 4))
    write("bl19_log2Up", [f19(rng, -300, 300, 0.05) for _ in range(S)])
    write("bl19_cbrt", [f19(rng, -1000, 1000) for _ in range(S)])
    for op in ("sinh", "cosh", "tanh"):
        write(f"bl19_{op}", [f19(rng, -130, 8) for _ in range(N // 2)] + [f19(rng, -3, 3) for _ in range(N // 2)])
    write("bl19_atanh", [f19(rng, -130, -1) for _ in range(N // 2)] + [f19(rng, -5, -1) for _ in range(N // 2)])
    pair = lambda lo, hi: ([f19(rng, lo, hi) for _ in range(S)], [f19(rng, lo, hi) for _ in range(S)])
    for op in ("min", "max", "avg", "dist", "zeroFloorSub"):
        write(f"bl19_{op}", *pair(-300, 300))
    write("bl19_inv", [f19(rng, -400, 400) for _ in range(S)])
    for op in ("frac", "round"):
        write(f"bl19_{op}", [f19(rng, -4, 240) for _ in range(S)])
    # the draws of the removed gcd's inputs, so every later op keeps its inputs
    [f19(rng, -2, 300) for _ in range(2 * S)]
    # hypot near its own exponents (where the sum of squares is exact) and far apart
    ha = [f19(rng, -400, 400) for _ in range(S)]
    hb = [(((x >> 236) & 0x7FFFF) + rng.randint(-130, 130)) << 236 | rng.getrandbits(236) | (rng.getrandbits(1) << 255) for x in ha]
    write("bl19_hypot", ha, hb)
    write("bl19_gavg", [f19(rng, -400, 400, 0) for _ in range(S)], [f19(rng, -400, 400, 0) for _ in range(S)])
    write("bl19_clamp", [f19(rng, -5, 5) for _ in range(S)], [f19(rng, -5, 5) for _ in range(S)], [f19(rng, -5, 5) for _ in range(S)])
    # lerp, eight shapes: b near a (b - a cancels), t near -a/(b - a) (the sum
    # cancels), t near one (a (1 - t) cancels), exponents spread by 600, by
    # 200,000, a far under t b, and plain
    la, lb, lt = [], [], []
    for i in range(N):
        a, b, t = f19(rng, -40, 40), f19(rng, -40, 40), f19(rng, -3, 3)
        kind = i % 8
        if kind == 0:
            b = a ^ rng.getrandbits(rng.randint(1, 236))
        elif kind == 1 and a != b:
            qa, qb = O.decode(a), O.decode(b)
            t = O.encode(-qa / (qb - qa)) ^ rng.getrandbits(rng.randint(0, 40))
        elif kind == 2:
            t = (BIAS << 236) ^ rng.getrandbits(rng.randint(1, 236)) ^ (rng.getrandbits(1) << 255) ^ (rng.getrandbits(1) << 236)
        elif kind == 3:
            a, b, t = f19(rng, -600, 600), f19(rng, -600, 600), f19(rng, -800, 800)
        elif kind == 4:
            a, b, t = f19(rng, -200000, 200000), f19(rng, -200000, 200000), f19(rng, -60000, 60000)
        elif kind == 5:
            a = f19(rng, -3000, -300)
        la.append(a), lb.append(b), lt.append(t)
    write("bl19_lerp", la, lb, lt)
    # factorial over its whole domain, and past it
    write("bl19_factorial", [O.encode(Fraction(n)) for n in range(0, 175)])



# ---- scoring ---------------------------------------------------------------

def s256(v):
    v %= T256
    return v - T256 if v >> 255 else v


def key19(w):
    w %= T256
    return -(w & (T256 // 2 - 1)) if w >> 255 else w


EXTRA = ["exp", "expm1", "log1p", "pow", "compound", "erfc", "normCdf", "powu", "lambertW0"]


def load(name):
    lib, op = name.split("_", 1)
    if lib in ("bl19", "wide", "mid") and op in EXTRA and (D / f"bl19_{op}x.json").exists():
        return load1(name) + load1(name + "x")
    return load1(name)


# the forced passes' output prefix -> their inputs' (wide127_exp.out ran bl127_exp.json)
STAGED = {"wide_": "bl19_", "mid_": "bl19_", "wide127_": "bl127_", "mid127_": "bl127_"}


def load1(name):
    pre = next((p for p in STAGED if name.startswith(p)), None)
    src = STAGED[pre] + name[len(pre):] if pre else name
    j = json.loads((D / f"{src}.json").read_text())
    a = [int(x, 16) for x in j["a"]]
    b = [int(x, 16) for x in j.get("b", [])] or [0] * len(a)
    c = [int(x, 16) for x in j.get("c", [])] or [0] * len(a)
    lines = (D / f"{name}.out").read_text().splitlines()
    outs = [ln.split()[0] for ln in lines]
    gas = [int(ln.split()[1]) if len(ln.split()) > 1 else 0 for ln in lines]
    if pre:
        a, b, c = a[:len(outs)], b[:len(outs)], c[:len(outs)]
    assert len(outs) == len(a), name
    return list(zip(a, b, c, outs, gas))


def job19(args):
    op, a, b, c, out = args
    mp.dps = 300        # the oracle's precision; gen() lowers it for the BL127 Lambert inputs
    try:
        ref = O.OPS[op](*([a, b, c] if op in THREE else [a, b] if op in TWO else [a]))
        ref = int(ref, 16) if isinstance(ref, str) else ref
    except O.Revert:
        return ("bothrev" if out.startswith("R") else "refrev", None)
    if out.startswith("R"):
        return ("gotrev", None)
    if op in PLAIN:
        return ("ok", int(out, 16) - ref % T256 if op.startswith("toUint") else s256(int(out, 16)) - s256(ref))
    return ("ok", key19(int(out, 16)) - key19(ref))


def truth127(op, a, b):
    A, B = s256(a), s256(b)
    x, y = mpf(A) / ONE, mpf(B) / ONE
    return {
        "mul": lambda: mpf(A) * B / ONE,
        "div": lambda: mpf(A) * ONE / B,
        "sqrt": lambda: mp.sqrt(mpf(A) * ONE),
        "exp": lambda: mp.exp(x) * ONE,
        "ln": lambda: mp.log(x) * ONE,
        "log2": lambda: mp.log(x, 2) * ONE,
        "pow": lambda: mp.power(x, y) * ONE,
        "cbrt": lambda: (mp.cbrt(x) if A >= 0 else -mp.cbrt(-x)) * ONE,
        "expm1": lambda: mp.expm1(x) * ONE,
        "erf": lambda: mp.erf(x) * ONE,
        "erfc": lambda: mp.erfc(x) * ONE,
        "normCdf": lambda: mp.ncdf(x) * ONE,
        "compound": lambda: mp.power(1 + x, int(mp.floor(y))) * ONE,
        "exp2": lambda: mp.power(2, x) * ONE,
        "exp10": lambda: mp.power(10, x) * ONE,
        "log10": lambda: mp.log(x, 10) * ONE,
        "sinh": lambda: mp.sinh(x) * ONE,
        "cosh": lambda: mp.cosh(x) * ONE,
        "tanh": lambda: mp.tanh(x) * ONE,
        "atanh": lambda: mp.atanh(x) * ONE,
        "powu": lambda: mp.power(x, int(mp.floor(y))) * ONE,
        "mulUp": lambda: mpf(A) * B / ONE,
        "divUp": lambda: mpf(A) * ONE / B,
        "divDown": lambda: mpf(A) * ONE / B,
        "toFixed18Up": lambda: mpf(A) * 10**18 / ONE,
        "lambertW0": lambda: lambertw(x, 0).real * ONE,
        "lambertWm1": lambda: lambertw(x, -1).real * ONE,
        "log1p": lambda: mp.log1p(x) * ONE,
        "gavg": lambda: mp.sqrt(mpf(A) * B),
        "hypot": lambda: mp.sqrt(mpf(A) * A + mpf(B) * B),
        "inv": lambda: mpf(ONE) * ONE / A,
        "mulDown": lambda: mpf(A) * B / ONE,
    }[op]()


# a truth within this of an integer or a half (in the result's units) is
# within reach of a rounding boundary for 200 digits: at most 2^255 (77
# digits) leaves them good to 10^-123, so 10^-100 is a wide margin
CR_REACH = mpf(10) ** -100


def crword(op, a, b):
    """(the correctly rounded word or "R" for a revert, close, changed):
    scripts/bl127/oracle.py's word at its 200 digits; close when its truth
    lies within CR_REACH of a rounding boundary, and then recomputed at 300
    digits, changed when that gives another word."""
    A, B = s256(a), s256(b)
    args = [A, B] if op in TWO else [A]

    def one():
        try:
            v = O127.OPS[op](*args)
        except O127.Revert:
            return "R", None
        return (v[0], v[1]) if isinstance(v, tuple) else (v, None)

    mp.dps = 200
    w, t = one()
    if t is None:
        return w, False, False
    t2 = 2 * mpf(t)
    if abs(t2 - mp.nint(t2)) >= CR_REACH:
        return w, False, False
    with mp.workdps(300):
        w3, _ = one()
    return w3, True, w3 != w


def job127(args):
    op, a, b, out = args
    mp.dps = 200
    cr, close, changed = crword(op, a, b)
    mp.dps = 200
    if out.startswith("R"):
        return ("gotrev", None, None, None, None, cr == "R", close, changed)
    got = s256(int(out, 16))
    t = truth127(op, a, b)
    if not -2**255 <= t < 2**255:
        return ("refover", None, None, None, None, False, close, changed)
    err = got - t
    bits = float(log(abs(t), 2) - log(abs(err), 2)) if err != 0 and t != 0 else 999.0
    near = op.startswith("lambert") and s256(a) < 0 and mpf(s256(a)) / ONE + 1 / E < mpf(2) ** -20
    return ("ok", float(err), bits, near, abs(t) >= ONE, cr != "R" and got == cr, close, changed)


def summarize19(op, res):
    st = Counter(r[0] for r in res)
    errs = [r[1] for r in res if r[0] == "ok"]
    c = Counter(errs)
    return {"lib": "bl19", "op": op, "n": len(errs), "status": dict(st), "correctlyRounded": c.get(0, 0),
            "misrounded": len(errs) - c.get(0, 0), "maxUlp": max((abs(x) for x in errs), default=0),
            "hist": {str(k): v for k, v in sorted(c.items())}}


def gasstats(gs):
    """Median, 99th percentile and largest gas of the calls that returned (the
    inline library's own cost, the self-call subtracted)."""
    g = sorted(x for x in gs if x)
    if not g:
        return {}
    return {"gasMedian": g[len(g) // 2], "gasP99": g[int(0.99 * (len(g) - 1))], "gasMax": g[-1]}


def summarize127(op, res):
    st = Counter(r[0] for r in res)
    ok = [r for r in res if r[0] == "ok"]
    ae = sorted(abs(r[1]) for r in ok)
    n = len(ae)
    far = [r[2] for r in ok if not r[3] and r[4]]
    near = [r[2] for r in ok if r[3]]
    # the correctly rounded word, with reverts where the oracle reverts
    cr = sum(1 for r in res if r[5])
    s = {"lib": "bl127", "op": op, "n": n, "status": dict(st),
         "inputs": len(res), "correctlyRounded": cr, "misrounded": len(res) - cr,
         "crClose": sum(1 for r in res if r[6]), "crChanged": sum(1 for r in res if r[7]),
         "nearest": sum(1 for x in ae if x <= 0.5000001), "faithful": sum(1 for x in ae if x < 1.0000001),
         "maxUlp": ae[-1] if n else 0, "p99Ulp": ae[int(0.99 * (n - 1))] if n else 0,
         "medianUlp": ae[n // 2] if n else 0, "minBits": round(min(far), 1) if far else None,
         "below": sum(1 for r in ok if r[1] < -1e-9), "above": sum(1 for r in ok if r[1] > 1e-9)}
    if near:
        s["minBitsWithin2^-20OfMinus1/e"] = round(min(near), 1)
    return s


def score():
    rows = []
    with mpc.Pool() as pool:
        for op in OPS19:
            if not selected(op, "bl19"):
                continue
            data = load(f"bl19_{op}")
            res = pool.map(job19, [(op, a, b, c, o) for a, b, c, o, g in data], chunksize=64)
            rows.append(dict(summarize19(op, res), **gasstats([g for *_, g in data]), **fallback("bl19", op, data)))
            print(json.dumps(rows[-1]), flush=True)
        for op in WIDE19:
            if not selected(op, "bl19") or not (D / f"wide_{op}.out").exists():
                continue
            data = load(f"wide_{op}")
            res = pool.map(job19, [(op, a, b, c, o) for a, b, c, o, g in data], chunksize=16)
            rows.append(dict(summarize19(op, res), stage="second", **gasstats([g for *_, g in data])))
            print(json.dumps(rows[-1]), flush=True)
        for op in MID19:
            if not selected(op, "bl19") or not (D / f"mid_{op}.out").exists():
                continue
            data = load(f"mid_{op}")
            res = pool.map(job19, [(op, a, b, c, o) for a, b, c, o, g in data], chunksize=16)
            rows.append(dict(summarize19(op, res), stage="middle", **gasstats([g for *_, g in data])))
            print(json.dumps(rows[-1]), flush=True)
        for op in OPS127 + ["lambertW0", "lambertWm1"]:
            if not selected(op, "bl127"):
                continue
            data = load(f"bl127_{op}")
            res = pool.map(job127, [(op, a, b, o) for a, b, c, o, g in data], chunksize=64)
            rows.append(dict(summarize127(op, res), **gasstats([g for *_, g in data]), **fallback("bl127", op, data)))
            print(json.dumps(rows[-1]), flush=True)
        for tag, stage, ops in (("wide127", "second", WIDE127), ("mid127", "middle", MID127)):
            for op in ops:
                if not selected(op, "bl127") or not (D / f"{tag}_{op}.out").exists():
                    continue
                data = load(f"{tag}_{op}")
                res = pool.map(job127, [(op, a, b, o) for a, b, c, o, g in data], chunksize=16)
                rows.append(dict(summarize127(op, res), stage=stage, **gasstats([g for *_, g in data])))
                print(json.dumps(rows[-1]), flush=True)
        rows += WD.sweep_rows(pool, lambda op: selected(op, "wad"), fallback)
    if SEL is not None or LIBSEL is not None:
        # a partial run: the selected ops' rows replace their old ones, every other row stays
        key = lambda r: (r["lib"], r["op"], r.get("stage"))  # noqa: E731
        new = {key(r): r for r in rows}
        old = json.loads((OUT / "sweep.json").read_text())["rows"]
        rows = [new.pop(key(r), r) for r in old] + list(new.values())
    doc = {"_doc": __doc__.strip(), "seed": SEED, "seedLambert": SEED_LW, "rows": rows}
    (OUT / "sweep.json").write_text(json.dumps(doc, indent=1) + "\n")
    md = ["# Random-input accuracy sweep",
          "",
          "Generated by `make sweep` (`scripts/sweep/sweep.py`, `test/sweep/Sweep.t.sol`) from seeded random "
          "inputs. BL19 is compared with the correctly rounded word (scripts/bl19/oracle.py, 300 digits, "
          "ties away from zero); BL127 with the real truth at 200 digits, in units of 2^-128, and with "
          "its correctly rounded word (scripts/bl127/oracle.py). Data: `sweep.json`.",
          "",
          "## BL19",
          "",
          "Release four: every op below is correctly rounded or exact by construction; the "
          "directed ops (Down: toward minus infinity, Up: toward plus infinity) are compared "
          "with the exact value rounded in their direction, the plain-integer ones (toUint, "
          "toInt) as integers.",
          "",
          "Gas is the inline library's (BL19Lib) own cost on these inputs, median / 99th "
          "percentile / largest, the second stage's runs included where the fast value's "
          "error bound reached the rounding boundary. *Fallback* is the share of inputs whose "
          "rounding test fired (a dash: the op has none); for pow, powu and compound, which "
          "have a middle stage, the share that went on to the second stage follows the arrow.",
          "",
          "| op | inputs | correctly rounded | misrounded | max ULP | gas median / p99 / max | fallback |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        if r["lib"] == "bl19" and "stage" not in r:
            md.append(f"| {r['op']} | {r['n']:,} | {r['correctlyRounded']:,} | {r['misrounded']:,} | {r['maxUlp']} | "
                      f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} | {pct(r)} |")
    if any(r.get("stage") == "middle" and r["lib"] == "bl19" for r in rows):
        md += ["",
               "### The middle stage alone",
               "",
               "The first 4,000 inputs of pow, powu and compound again, through a test-only copy of "
               "BL19Lib whose fast path's rounding test always fails and whose middle stage's test "
               "is kept: log2 x within 2^-285 (scripts/bl19/generators/mid254.py), t = y log2 x "
               "exact from it, the 2^f kernel, and the second stage only where that cannot decide.",
               "",
               "| op | inputs | correctly rounded | misrounded | max ULP | gas median / p99 / max |",
               "|---|---:|---:|---:|---:|---:|"]
        for r in rows:
            if r.get("stage") == "middle" and r["lib"] == "bl19":
                md.append(f"| {r['op']} | {r['n']:,} | {r['correctlyRounded']:,} | {r['misrounded']:,} | {r['maxUlp']} | "
                          f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} |")
    if any(r.get("stage") == "second" and r["lib"] == "bl19" for r in rows):
        md += ["",
               "### The second stage alone",
               "",
               "The first 4,000 inputs of each op again, through a test-only copy of BL19Lib whose "
               "rounding tests (the middle stage's too) always fail, so every result comes from the wide second stage "
               "(two words at 2^-510) that normally runs only when the fast value is too close to "
               "a tie.",
               "",
               "| op | inputs | correctly rounded | misrounded | max ULP | gas median / p99 / max |",
               "|---|---:|---:|---:|---:|---:|"]
        for r in rows:
            if r.get("stage") == "second" and r["lib"] == "bl19":
                md.append(f"| {r['op']} | {r['n']:,} | {r['correctlyRounded']:,} | {r['misrounded']:,} | {r['maxUlp']} | "
                          f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} |")
    md += ["",
           "## BL127",
           "",
           "*correctly rounded*: the word scripts/bl127/oracle.py gives, the rounding the op promises: to nearest "
           "with BL127's tie rule (ties up; powu, compound, cbrt, sinh, tanh and erf round the magnitude, so their "
           "ties go away from zero), the directed ops in their direction; a "
           "revert where the oracle reverts counts as correct, so *inputs* includes the reverts; the ULP columns "
           "are over the results that returned. "
           "*nearest*: within half a ULP; *faithful*: within one; *min bits*: fewest correct bits relative to the "
           "result, over results of magnitude 1 or more (below 1 a fixed point's absolute grid sets the bits; "
           "for Lambert W the 2^-20 neighbourhood of -1/e is shown separately). The directed ops (mulUp, divUp, "
           "divDown, toFixed18Up) are under one ULP in their direction by design: *below / above truth* shows "
           "the direction; toFixed18Up is measured in its own unit, 10^-18. Gas is BL127Lib's own cost, "
           "median / p99 / largest; *fallback* is the share of inputs whose fast value's rounding test fired "
           "(the next stage ran: every transcendental has one since 3.0, and for the logs, pow and compound, "
           "which have a middle stage, the share whose middle stage's test fired too follows the arrow; "
           "a dash: the op has none).",
           "",
           "| op | inputs | correctly rounded | misrounded | nearest | faithful | max ULP | median ULP | min bits (≥ 1) | below / above truth | gas median / p99 / max | fallback |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|"]

    def row127(r, fallback=True):
        near = r.get("minBitsWithin2^-20OfMinus1/e")
        mb = "—" if r["minBits"] is None else f"{r['minBits']}" + (f" ({near} near −1/e)" if near is not None else "")
        return (f"| {r['op']} | {r.get('inputs', r['n']):,} | {r.get('correctlyRounded', 0):,} | {r.get('misrounded', 0):,} | "
                f"{r['nearest']:,} | {r['faithful']:,} | {r['maxUlp']:.3g} | "
                f"{r['medianUlp']:.3g} | {mb} | {r['below']:,} / {r['above']:,} | "
                f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,}"
                + (f" | {pct(r)} |" if fallback else " |"))

    for r in rows:
        if r["lib"] == "bl127" and "stage" not in r:
            md.append(row127(r))
    for stage, title, text in (
            ("middle", "The middle stage alone",
             "The first 4,000 inputs of the ops with a middle stage again, through a test-only copy of BL127Lib "
             "whose fast paths' rounding tests always fail (nearmid, pow2t, rbad127, rbadw): log2 x to 2^-299 "
             "(l2p; pow near one relative, through BL19's mratio), the logs rounded from it and pow's and "
             "compound's double-word 2^t, each with its own test kept and the last stage behind it."),
            ("second", "The last stage alone",
             "The first 4,000 inputs of each op with a rounding test again, through a test-only copy of BL127Lib "
             "whose tests (nearmid, pow2t, pow2rt, rbad127, rbadw, rbadm127) always fail, so every result comes "
             "from the stage that runs when every earlier value is too close to a tie: the two-word exponential "
             "(BL19's wexpm1) for exp, exp2, exp10 and expm1, one Newton step through it for the logs, pow's "
             "exact tie or its two-word log and exponential, powu's 512-bit mantissa (pow from |n| = 2^16), "
             "compound through powu, and the hyperbolics' two-word stages.")):
        if any(r.get("stage") == stage and r["lib"] == "bl127" for r in rows):
            md += ["", f"### {title}", "", text, "",
                   "| op | inputs | correctly rounded | misrounded | nearest | faithful | max ULP | median ULP | min bits (≥ 1) | below / above truth | gas median / p99 / max |",
                   "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
            md += [row127(r, False) for r in rows if r.get("stage") == stage and r["lib"] == "bl127"]
    md += WD.sweep_md(rows, pct)
    (OUT / "sweep.md").write_text("\n".join(md) + "\n")
    print("wrote docs/benchmarks/sweep.{json,md}")


WIDE_TEST = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// GENERATED by scripts/sweep/sweep.py for a forced pass; removed after the run.

import {Test} from "forge-std/Test.sol";
import {LIBNAME} from "./LIBNAME.sol";

contract SweepPFX is Test {
    string constant DIR = "cache/sweep/";

    function f(bytes32 op, int256 a, int256 b) external view returns (int256 r, uint256 g) {
        uint256 g0;
        if (op == "noop") { g0 = gasleft(); r = a; g = gasleft(); }
%s
        require(g0 != 0, "op");
        g = g0 - g;
    }

    function _base() internal view returns (uint256 g) {
        (, g) = this.f("noop", 0, 0);
    }

    function runOne(string memory op, bool two) external {
        _run(op, two);
    }

    function _run(string memory op, bool two) internal {
        string memory path = string.concat(DIR, "SRCLIB_", op, ".json");
        if (!vm.exists(path)) return;
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = two ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, "PREFIX_", op, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        uint256 n = a.length < %d ? a.length : %d;
        uint256 base = _base();
        for (uint256 i; i < n; i++) {
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i]))) returns (int256 r, uint256 g) {
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
    }

%s
}
"""


def run_wide(tag="wide", lib="bl19"):
    """Generate <Lib>LibWide (every rounding test forced; tag "mid":
    <Lib>LibMid, the fast path's test forced and the middle stage's kept, for
    the ops with a middle stage) and its runner, run them on the first WIDE_N
    inputs, remove them. The outputs are wide_* and mid_* for BL19, wide127_*
    and mid127_* for BL127."""
    if LIBSEL is not None and lib not in LIBSEL:
        return
    Tag = tag.capitalize()
    pfx = tag if lib == "bl19" else f"{tag}127"
    Lib = f"{lib.upper()}Lib{Tag}"
    wd = ROOT / "test" / "sweep" / pfx
    ops = (WIDE if tag == "wide" else MID)[lib]
    names = [op for op in ops if selected(op)]
    if lib == "bl19":
        names += [f"{op}x" for op in EXTRA if selected(op) and op in ops]
    if not names:
        return
    subprocess.run(["uv", "run", "scripts/bl127/gen.py", "--lib", lib, f"--{tag}-lib",
                    str(wd / f"{Lib}.sol")], cwd=ROOT, check=True)
    fn = {f"{op}x": op for op in EXTRA}
    disp = "\n".join(f'        if (op == "{n}") {{ g0 = gasleft(); r = {Lib}.{fn.get(n, n)}(a{", b" if fn.get(n, n) in TWO else ""}); g = gasleft(); }}'
                      for n in names)
    runs = "\n".join(f'    function test_{n}() public {{ this.runOne("{n}", {"true" if fn.get(n, n) in TWO else "false"}); }}' for n in names)
    test = (WIDE_TEST.replace("LIBNAME", Lib).replace("PFX", pfx.capitalize())
            .replace("SRCLIB", lib).replace("PREFIX", pfx))
    (wd / f"Sweep{pfx.capitalize()}.t.sol").write_text(test % (disp, WIDE_N, WIDE_N, runs))
    try:
        subprocess.run(["forge", "test", "--match-path", f"test/sweep/{pfx}/Sweep{pfx.capitalize()}.t.sol", "-q"], cwd=ROOT, check=True)
    finally:
        for f in wd.glob("*"):
            f.unlink()
        wd.rmdir()


# ---- the instrumented passes (count here, probe for make profile) ----------

INSTR_TEST = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// GENERATED by scripts/sweep/sweep.py for the %(tag)s pass; removed after the run.

import {Test} from "forge-std/Test.sol";
%(imports)s

/// Test/sweep/Sweep.t.sol's dispatch on the instrumented libraries. The
/// libraries record into memory from 0x8000 (scripts/bl127/gen.py: count_wrap,
/// probe_wrap); f pre-expands it outside the timed window and returns the
/// %(rec)d record words beside the result and the window's gas.
contract Sweep%(Tag)s is Test {
    string constant DIR = "cache/sweep/";
    uint256 constant REC = %(rec)d;
    uint256 constant LIMIT = %(limit)d;

    function f(bytes32 op, int256 a, int256 b, int256 c) external view returns (int256 r, uint256 g, uint256[] memory rec) {
        assembly { mstore(%(top)s, 0) }
        uint256 g0;
%(disp)s
        require(g0 != 0, "op");
        g = g0 - g;
        rec = new uint256[](REC);
        for (uint256 i; i < REC; i++) {
            uint256 w;
            assembly { w := mload(add(0x8000, mul(0x20, i))) }
            rec[i] = w;
        }
    }

    function runOne(string memory op, uint256 args) external {
        string memory path = string.concat(DIR, op, ".json");
        if (!vm.exists(path)) return;
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = args > 1 ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        bytes32[] memory c = args > 2 ? vm.parseJsonBytes32Array(j, ".c") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, "%(tag)s_", op, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        (, uint256 base,) = this.f("noop", 0, 0, 0);
        uint256 n = a.length < LIMIT ? a.length : LIMIT;
        for (uint256 i; i < n; i++) this.line(outp, k, [int256(uint256(a[i])), int256(uint256(b[i])), int256(uint256(c[i]))], base);
    }

    /// One input's line, in its own call so its memory is released.
    function line(string memory outp, bytes32 k, int256[3] memory x, uint256 base) external {
        try this.f(k, x[0], x[1], x[2]) returns (int256 r, uint256 g, uint256[] memory rec) {
            string memory s = string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0));
            for (uint256 w; w < rec.length; w++) s = string.concat(s, " ", vm.toString(rec[w]));
            vm.writeLine(outp, s);
        } catch (bytes memory e) {
            vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
        }
    }

%(runs)s
}
"""


def sweep_dispatch() -> list[tuple[str, str]]:
    """(name, expression) of every op in Sweep.t.sol's f, in order, then
    SweepWad.t.sol's (BlockulatorWad's, in its own contract)."""
    src = (ROOT / "test" / "sweep" / "Sweep.t.sol").read_text() + (ROOT / "test" / "sweep" / "SweepWad.t.sol").read_text()
    found = re.findall(r'if \(op == "(\w+)"\) \{ g0 = gasleft\(\); r = (.*?); g = gasleft\(\); \}', src)
    seen: set[str] = set()
    return [(n, e) for n, e in found if not (n in seen or seen.add(n))]   # noop once


def rec_words(kind: str) -> int:
    """Record words from 0x8000: the counter, or the probes' shared words and three per probe."""
    if kind == "count":
        return 2
    return (G.PROBE_BASE - G.COUNT_SLOT + G.PROBE_STRIDE * max(len(v) for v in G.PROBES.values())) // 32


def base_op(name: str) -> str:
    """bl19_erfcx -> erfc, bl127_erf -> erf: the op behind an input file's name."""
    op = name.split("_", 1)[1] if "_" in name else name
    return op[:-1] if name.startswith("bl19_") and op.endswith("x") and op[:-1] in EXTRA else op


def nargs(name: str) -> int:
    op = base_op(name)
    if name.startswith("wad_"):
        return WD.FUNCS[op][1]
    return 3 if op in THREE else 2 if op in TWO else 1


def wide_names() -> list[str]:
    """The input files of the second-stage pass, as run_wide runs them."""
    return [f"bl19_{op}" for op in WIDE19] + [f"bl19_{op}x" for op in EXTRA]


def run_instrumented(kind: str, forced: bool = False):
    """Generate the count or probe libraries and their runner, run them on the
    swept inputs, remove them. forced: BL19 only, with the rounding test
    forced to fail as in run_wide (gen.py --forced), on the same first WIDE_N
    inputs of the ops with a second stage; the outputs are <kind>wide_*.out."""
    tag = kind + ("wide" if forced else "")
    Tag = tag.capitalize()
    wd = ROOT / "test" / "sweep" / tag
    libs = ("bl19",) if forced else ("bl19", "bl127")
    if kind == "count" and not forced:
        libs += ("wad",)   # BlockulatorWad's fallback share; make profile's probes stay BL19's and BL127's
    libs = tuple(l for l in libs if LIBSEL is None or l in LIBSEL)
    if not libs:
        return
    for lib in libs:
        subprocess.run(["uv", "run", "scripts/bl127/gen.py", "--lib", lib, f"--{kind}-lib",
                        str(wd / f"{lib.upper()}Lib{Tag}.sol")] + (["--forced"] if forced else []), cwd=ROOT, check=True)
    want = set(wide_names()) if forced else None
    disp, runs = [], []
    for name, expr in sweep_dispatch():
        if forced and name != "noop" and name not in want:
            continue
        if name != "noop" and not selected(base_op(name), name.split("_", 1)[0]):
            continue
        if name.startswith("wad_") and "wad" not in libs:
            continue
        expr = (expr.replace("BL19Lib.", f"BL19Lib{Tag}.").replace("BL127Lib.", f"BL127Lib{Tag}.")
                .replace("BlockulatorWad.", f"WADLib{Tag}."))
        disp.append(f'        if (op == "{name}") {{ g0 = gasleft(); r = {expr}; g = gasleft(); }}')
        if name != "noop":
            runs.append(f'    function test_{name}() public {{ this.runOne("{name}", {nargs(name)}); }}')
    rec = rec_words(kind)
    imports = "\n".join(f'import {{{lib.upper()}Lib{Tag}}} from "./{lib.upper()}Lib{Tag}.sol";' for lib in libs)
    (wd / f"Sweep{Tag}.t.sol").write_text(INSTR_TEST % {
        "tag": tag, "Tag": Tag, "rec": rec, "top": hex(G.COUNT_SLOT + 32 * rec), "imports": imports,
        "limit": WIDE_N if forced else 1 << 32, "disp": "\n".join(disp), "runs": "\n".join(runs)})
    keep = bool(os.environ.get("SWEEP_KEEP"))   # leave the generated files, show forge's output
    try:
        subprocess.run(["forge", "test", "--match-path", f"test/sweep/{tag}/Sweep{Tag}.t.sol"] + ([] if keep else ["-q"]),
                       cwd=ROOT, check=True)
    finally:
        if not keep:
            for f in wd.glob("*"):
                f.unlink()
            wd.rmdir()


def load_rec(kind: str, name: str):
    """The instrumented pass's lines for an input file (with the x rows, as
    load): (out, gas, [record words]) per input."""
    lib, op = name.split("_", 1)
    names = [name] + ([name + "x"] if lib == "bl19" and op in EXTRA and (D / f"{name}x.json").exists() else [])
    rows = []
    for n in names:
        path = D / f"{kind}_{n}.out"
        if not path.exists():
            return None
        for ln in path.read_text().splitlines():
            parts = ln.split()
            rows.append((parts[0], int(parts[1]) if len(parts) > 1 else 0, [int(x) for x in parts[2:]]))
    return rows


def closures(lib: str) -> dict[str, set[str]]:
    """Each export's Solidity name -> the Yul functions it runs."""
    src = G.parse(G.LIBS[lib]["src"].read_text())
    return {e.sol_name: {f.name for f in G.closure(src, e.yul_name)} for e in src.exports}


def fallback(lib: str, op: str, data) -> dict:
    """The count pass for one op: inputs whose rounding test fired, or {} when
    the op has no counted fallback (or the pass did not run)."""
    if not set(G.COUNTS[lib]) & closures(lib).get(op, set()):
        return {}
    rec = load_rec("count", f"{lib}_{op}")
    if rec is None:
        return {}
    plain = [d[-2] for d in data]
    got = [o for o, _, _ in rec]
    assert got == plain, f"{lib} {op}: the count pass changed a result"
    fired = [w[0] for o, _, w in rec if w]
    out = {"fallback": sum(1 for c in fired if c), "fallbackRuns": sum(fired), "fallbackPct": round(100 * sum(1 for c in fired if c) / len(rec), 3)}
    if {"bl19": "rbadm", "bl127": "rbadm127"}.get(lib) in closures(lib).get(op, set()):
        second = sum(1 for o, _, w in rec if len(w) > 1 and w[1])
        out.update(second=second, secondPct=round(100 * second / len(rec), 3))
    return out


def pct(r) -> str:
    if "fallbackPct" not in r:
        return "—"
    f = lambda p: "0" if p == 0 else f"{p:.2f}%" if p >= 0.01 else f"{p:.3f}%"  # noqa: E731
    return f(r["fallbackPct"]) + (f" → {f(r['secondPct'])}" if "secondPct" in r else "")


def main():
    global SEL, LIBSEL
    args = sys.argv[1:]
    while args[:1] in (["--ops"], ["--lib"]):
        if args[0] == "--ops":
            SEL = set(args[1].split(","))
        else:
            LIBSEL = set(args[1].split(","))
            if LIBSEL - set(LIBS):
                sys.exit(f"--lib: one or more of {', '.join(LIBS)}")
        args = args[2:]
    if SEL is not None:
        unknown = SEL - set(OPS19) - set(OPS127) - {"lambertW0", "lambertWm1"} - set(WD.FUNCS)
        if unknown:
            sys.exit(f"--ops: not swept: {', '.join(sorted(unknown))}")
    if args != ["score"]:
        gen()
        subprocess.run(["forge", "test", "--match-path", "test/sweep/Sweep*.t.sol", "-q"] + match_tests(), cwd=ROOT, check=True)
        run_wide()
        run_wide("mid")
        run_wide("wide", "bl127")
        run_wide("mid", "bl127")
        if LIBSEL is None or "wad" in LIBSEL:
            WD.run_wide(SEL)
        run_instrumented("count")
    score()


if __name__ == "__main__":
    main()

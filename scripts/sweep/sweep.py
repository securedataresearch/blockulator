#!/usr/bin/env python3
"""Random-input accuracy sweep of the inline FP127 and FP256 libraries against
correctly rounded truth.

    uv run scripts/sweep/sweep.py          # gen -> forge (test/sweep/Sweep.t.sol) -> score
    uv run scripts/sweep/sweep.py score    # re-score the last forge outputs only

Release four adds the directed ops, powu and lambertWm1, and a second pass: the
same inputs (the first 4,000 of each) through a test-only copy of FP256Lib whose
rounding test always fails (scripts/fp127/gen.py --wide-lib), so every correctly
rounded op returns its wide second stage. That pass is generated into
test/sweep/wide/ (not committed) and removed after the run.

A third pass runs every op on all its inputs through test-only copies of FP256Lib
and FP127Lib that count each rounding-test fallback (scripts/fp127/gen.py --count-lib:
FP256's rbad firing, FP127's nearmid firing and powu's 512-bit powus), generated into
test/sweep/count/ and removed after the run: the *fallback* column is the share of
inputs that left the fast path. Its results must equal the plain pass's word for word.

Gas is the inline library call alone: Sweep.t.sol reads gasleft() on either side of
the one call, after its dispatch, and subtracts the same window around an assignment.

Inputs are seeded (20261020; Lambert W 7) and written to cache/sweep/, which is not
committed. FP256 results are compared with the word the oracle (scripts/fp256/oracle.py:
exact rationals and mpmath at 300 digits, half away from zero) returns, as a signed
distance in ULPs. FP127 results are compared with the real truth at 200 digits, as
|got - truth| in units of 2^-128. Writes docs/benchmarks/sweep.{json,md}.
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
sys.path.insert(0, str(ROOT / "scripts" / "fp256"))
import oracle as O  # noqa: E402
from mpmath import mp, mpf, e as E, lambertw, log  # noqa: E402

_spec = importlib.util.spec_from_file_location("fpgen", ROOT / "scripts" / "fp127" / "gen.py")
G = importlib.util.module_from_spec(_spec)
sys.modules["fpgen"] = G
_spec.loader.exec_module(G)

D = ROOT / "cache" / "sweep"
OUT = ROOT / "docs" / "benchmarks"
T256 = 1 << 256
ONE = 1 << 128
BIAS = 0x3FFFF
SEED, SEED_LW = 20261020, 7
OPS256 = ["add", "mul", "div", "sqrt", "exp", "ln", "log1p", "expm1", "pow", "erf", "erfc", "normCdf",
          "compound", "lambertW0", "lambertWm1", "powu",
          "mulDown", "mulUp", "divDown", "divUp", "toUintDown", "toUintUp", "toIntDown", "toIntUp",
          "floor", "ceil", "fromUintDown", "fromUintUp", "toFixed18Down", "toFixed18Up",
          # #79: FP256X2 and FP256X3
          "exp2", "exp10", "log2", "log10", "log2Up", "cbrt", "sinh", "cosh", "tanh", "atanh",
          "min", "max", "clamp", "avg", "dist", "zeroFloorSub", "inv", "lerp", "frac", "round",
          "gcd", "factorial", "pi", "gavg", "hypot"]
# the ops with a wide second stage, swept again through FP256LibWide
WIDE256 = ["exp", "ln", "log1p", "expm1", "pow", "erf", "erfc", "normCdf", "compound", "lambertW0",
           "lambertWm1", "powu", "exp2", "exp10", "log2", "log10", "sinh", "cosh", "tanh", "atanh"]
WIDE_N = 4000
PLAIN = {"toUintDown", "toUintUp", "toIntDown", "toIntUp", "toFixed18Down", "toFixed18Up"}
OPS127 = ["mul", "div", "sqrt", "exp", "ln", "log2", "pow", "cbrt", "expm1", "erf", "normCdf", "compound",
          "exp2", "exp10", "log10", "sinh", "cosh", "tanh", "powu", "mulUp", "divUp", "divDown", "toFixed18Up"]
TWO = {"add", "mul", "div", "pow", "compound", "powu", "mulDown", "mulUp", "divDown", "divUp",
       "min", "max", "avg", "dist", "zeroFloorSub", "gcd", "gavg", "hypot"}
THREE = {"clamp", "lerp"}


# ---- inputs ----------------------------------------------------------------

def f256(rng, emin, emax, neg=0.5):
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
    write("fp256_add", [f256(rng, -40, 40) for _ in range(S)], [f256(rng, -40, 40) for _ in range(S)])
    write("fp256_mul", [f256(rng, -400, 400) for _ in range(S)], [f256(rng, -400, 400) for _ in range(S)])
    write("fp256_div", [f256(rng, -400, 400) for _ in range(S)], [f256(rng, -400, 400) for _ in range(S)])
    write("fp256_sqrt", [f256(rng, -400, 400, 0) for _ in range(S)])
    write("fp256_exp", [f256(rng, -30, 9) for _ in range(N)])
    write("fp256_ln", [f256(rng, -300, 300, 0) for _ in range(N // 2)] + [f256(rng, -1, 0, 0) for _ in range(N // 2)])
    write("fp256_log1p", [f256(rng, -60, 4, 0.3) for _ in range(N)])
    write("fp256_expm1", [f256(rng, -60, 6) for _ in range(N)])
    write("fp256_pow", [f256(rng, -2, 2, 0) for _ in range(N)], [f256(rng, -8, 6) for _ in range(N)])
    write("fp256_erf", [f256(rng, -8, 2) for _ in range(S)])
    write("fp256_erfc", [f256(rng, -8, 4) for _ in range(S)])
    write("fp256_normCdf", [f256(rng, -8, 4) for _ in range(S)])
    write("fp256_compound", [f256(rng, -40, -5) for _ in range(S)], [rng.randint(1, 40_000_000) for _ in range(S)])
    write("fp256_lambertW0", [f256(rng, -10, 8, 0) for _ in range(S // 2)])
    write("fp127_mul", [f127(rng, 100, 200) for _ in range(S)], [f127(rng, 60, 160) for _ in range(S)])
    write("fp127_div", [f127(rng, 100, 200) for _ in range(S)], [f127(rng, 100, 200) for _ in range(S)])
    write("fp127_sqrt", [f127(rng, 1, 254, 0) for _ in range(S)])
    write("fp127_exp", [f127(rng, 100, 134) for _ in range(S)])
    write("fp127_ln", [f127(rng, 1, 254, 0) for _ in range(S)])
    write("fp127_log2", [f127(rng, 1, 254, 0) for _ in range(S)])
    write("fp127_pow", [f127(rng, 126, 130, 0) for _ in range(S)], [f127(rng, 100, 134) for _ in range(S)])
    write("fp127_cbrt", [f127(rng, 1, 254) for _ in range(S)])
    write("fp127_expm1", [f127(rng, 60, 134) for _ in range(S)])
    write("fp127_erf", [f127(rng, 100, 130) for _ in range(S // 2)])
    write("fp127_normCdf", [f127(rng, 100, 131) for _ in range(S // 2)])
    write("fp127_compound", [f127(rng, 80, 123) for _ in range(S)], [rng.randint(1, 40_000_000) << 128 for _ in range(S)])
    # FP127 v5: the rest of the exponential family, the hyperbolics, powu and the directed edge ops
    rv = random.Random(SEED + 5)
    write("fp127_exp2", [f127(rv, 100, 134) for _ in range(S)])
    write("fp127_exp10", [f127(rv, 100, 133) for _ in range(S)])
    write("fp127_log10", [f127(rv, 1, 254, 0) for _ in range(S)])
    write("fp127_sinh", [f127(rv, 100, 134) for _ in range(S)])
    write("fp127_cosh", [f127(rv, 100, 134) for _ in range(S)])
    write("fp127_tanh", [f127(rv, 100, 134) for _ in range(S)])
    write("fp127_powu", [f127(rv, 120, 136) for _ in range(S)], [rv.randint(-300, 300) << 128 for _ in range(S)])
    write("fp127_mulUp", [f127(rv, 100, 200) for _ in range(S)], [f127(rv, 60, 160) for _ in range(S)])
    write("fp127_divUp", [f127(rv, 100, 200) for _ in range(S)], [f127(rv, 100, 200) for _ in range(S)])
    write("fp127_divDown", [f127(rv, 100, 200) for _ in range(S)], [f127(rv, 100, 200) for _ in range(S)])
    write("fp127_toFixed18Up", [f127(rv, 1, 250) for _ in range(S)])
    # FP127 Lambert W: W0 log-uniform on (0, 2^100] and within [2^-20, 1/e] of -1/e; W-1 on [-1/e, 0)
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
    write("fp127_lambertW0", w0)
    write("fp127_lambertWm1", [x for x in wm1 if x < 0])
    gen4()


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
    w0neg = [f256(rng, -64, -3, 1) for _ in range(S // 4)] + near_branch(rng, S // 4)
    write("fp256_lambertWm1", [f256(rng, -300, -3, 1) for _ in range(S // 2)] + near_branch(rng, S // 2))
    write("fp256_powu", [f256(rng, -2, 2) for _ in range(S)],
          [rng.choice([1, -1]) * rng.randint(2, 1 << rng.randint(2, 20)) for _ in range(S)])
    for op in ("mulDown", "mulUp"):
        write(f"fp256_{op}", [f256(rng, -400, 400) for _ in range(S)], [f256(rng, -400, 400) for _ in range(S)])
    for op in ("divDown", "divUp"):
        write(f"fp256_{op}", [f256(rng, -400, 400) for _ in range(S)], [f256(rng, -400, 400) for _ in range(S)])
    # amounts: integers and near-integers to 2^256, a few negatives and tiny values
    for op in ("toUintDown", "toUintUp"):
        write(f"fp256_{op}", [f256(rng, -4, 255, 0.05) for _ in range(S)])
    for op in ("toIntDown", "toIntUp", "floor", "ceil"):
        write(f"fp256_{op}", [f256(rng, -4, 254) for _ in range(S)])
    for op in ("fromUintDown", "fromUintUp"):
        write(f"fp256_{op}", [rng.getrandbits(rng.randint(200, 256)) for _ in range(S)])
    for op in ("toFixed18Down", "toFixed18Up"):
        write(f"fp256_{op}", [f256(rng, -80, 190) for _ in range(S)])
    # wider ranges for the ops whose second stage has more than one branch,
    # appended to the op's own rows ("x" files, merged by load)
    E = S // 2
    write("fp256_expx", [f256(rng, 9, 17) for _ in range(E)])
    write("fp256_expm1x", [f256(rng, 6, 17) for _ in range(E)])
    write("fp256_log1px", [f256(rng, 4, 300, 0) for _ in range(E // 2)] + [f256(rng, -4, -1, 1) for _ in range(E // 2)])
    write("fp256_powx", [f256(rng, -300, 300, 0) for _ in range(E)], [f256(rng, -20, 10) for _ in range(E)])
    write("fp256_compoundx", [f256(rng, -4, 8, 0.3) for _ in range(E // 2)] + [f256(rng, -1, -1, 1) for _ in range(E // 2)],
          [rng.choice([1, -1]) * rng.randint(1, 1 << rng.randint(1, 12)) for _ in range(E)])
    write("fp256_erfcx", [f256(rng, 4, 8) for _ in range(E)])
    write("fp256_normCdfx", [f256(rng, 4, 9, 0.8) for _ in range(E)])
    write("fp256_powux", [f256(rng, -40, 40) for _ in range(E)], [rng.choice([1, -1]) * rng.randint(2, 200) for _ in range(E)])
    write("fp256_lambertW0x", w0neg + [f256(rng, 8, 18, 0) for _ in range(E // 2)] + [f256(rng, 1000, 200000, 0) for _ in range(E // 2)])
    gen79()


def near_one(rng, n):
    """Words within 2^-4 of one, on both sides, at every scale down to 2^-230."""
    mp.dps = 120
    return [O.encode_mpf(1 + mpf(2) ** -rng.uniform(4, 230) * rng.choice([1, -1])) for _ in range(n)]


def gen79():
    """#79's inputs (FP256X2 and FP256X3), from their own seed."""
    rng = random.Random(SEED + 79)
    S, N = 4000, 8000
    write("fp256_exp2", [f256(rng, -40, 18) for _ in range(N)])
    write("fp256_exp10", [f256(rng, -40, 16) for _ in range(N)])
    for op in ("log2", "log10"):
        write(f"fp256_{op}", [f256(rng, -300, 300, 0) for _ in range(N // 2)] + [f256(rng, -1, 0, 0) for _ in range(N // 4)]
              + near_one(rng, N // 4))
    write("fp256_log2Up", [f256(rng, -300, 300, 0.05) for _ in range(S)])
    write("fp256_cbrt", [f256(rng, -1000, 1000) for _ in range(S)])
    for op in ("sinh", "cosh", "tanh"):
        write(f"fp256_{op}", [f256(rng, -130, 8) for _ in range(N // 2)] + [f256(rng, -3, 3) for _ in range(N // 2)])
    write("fp256_atanh", [f256(rng, -130, -1) for _ in range(N // 2)] + [f256(rng, -5, -1) for _ in range(N // 2)])
    pair = lambda lo, hi: ([f256(rng, lo, hi) for _ in range(S)], [f256(rng, lo, hi) for _ in range(S)])
    for op in ("min", "max", "avg", "dist", "zeroFloorSub"):
        write(f"fp256_{op}", *pair(-300, 300))
    write("fp256_inv", [f256(rng, -400, 400) for _ in range(S)])
    for op in ("frac", "round"):
        write(f"fp256_{op}", [f256(rng, -4, 240) for _ in range(S)])
    write("fp256_gcd", [f256(rng, -2, 300) for _ in range(S)], [f256(rng, -2, 300) for _ in range(S)])
    # hypot near its own exponents (where the sum of squares is exact) and far apart
    ha = [f256(rng, -400, 400) for _ in range(S)]
    hb = [(((x >> 236) & 0x7FFFF) + rng.randint(-130, 130)) << 236 | rng.getrandbits(236) | (rng.getrandbits(1) << 255) for x in ha]
    write("fp256_hypot", ha, hb)
    write("fp256_gavg", [f256(rng, -400, 400, 0) for _ in range(S)], [f256(rng, -400, 400, 0) for _ in range(S)])
    write("fp256_clamp", [f256(rng, -5, 5) for _ in range(S)], [f256(rng, -5, 5) for _ in range(S)], [f256(rng, -5, 5) for _ in range(S)])
    # lerp, eight shapes: b near a (b - a cancels), t near -a/(b - a) (the sum
    # cancels), t near one (a (1 - t) cancels), exponents spread by 600, by
    # 200,000, a far under t b, and plain
    la, lb, lt = [], [], []
    for i in range(N):
        a, b, t = f256(rng, -40, 40), f256(rng, -40, 40), f256(rng, -3, 3)
        kind = i % 8
        if kind == 0:
            b = a ^ rng.getrandbits(rng.randint(1, 236))
        elif kind == 1 and a != b:
            qa, qb = O.decode(a), O.decode(b)
            t = O.encode(-qa / (qb - qa)) ^ rng.getrandbits(rng.randint(0, 40))
        elif kind == 2:
            t = (BIAS << 236) ^ rng.getrandbits(rng.randint(1, 236)) ^ (rng.getrandbits(1) << 255) ^ (rng.getrandbits(1) << 236)
        elif kind == 3:
            a, b, t = f256(rng, -600, 600), f256(rng, -600, 600), f256(rng, -800, 800)
        elif kind == 4:
            a, b, t = f256(rng, -200000, 200000), f256(rng, -200000, 200000), f256(rng, -60000, 60000)
        elif kind == 5:
            a = f256(rng, -3000, -300)
        la.append(a), lb.append(b), lt.append(t)
    write("fp256_lerp", la, lb, lt)
    # factorial over its whole domain, and past it; pi for every number of terms to 40
    write("fp256_factorial", [O.encode(Fraction(n)) for n in range(0, 20370)])
    write("fp256_pi", [O.encode(Fraction(n)) for n in range(1, 41)] + [O.encode(Fraction(n, 2)) for n in range(2, 30)])



# ---- scoring ---------------------------------------------------------------

def s256(v):
    v %= T256
    return v - T256 if v >> 255 else v


def key256(w):
    w %= T256
    return -(w & (T256 // 2 - 1)) if w >> 255 else w


EXTRA = ["exp", "expm1", "log1p", "pow", "compound", "erfc", "normCdf", "powu", "lambertW0"]


def load(name):
    lib, op = name.split("_", 1)
    if lib in ("fp256", "wide") and op in EXTRA and (D / f"fp256_{op}x.json").exists():
        return load1(name) + load1(name + "x")
    return load1(name)


def load1(name):
    src = name.replace("wide_", "fp256_")
    j = json.loads((D / f"{src}.json").read_text())
    a = [int(x, 16) for x in j["a"]]
    b = [int(x, 16) for x in j.get("b", [])] or [0] * len(a)
    c = [int(x, 16) for x in j.get("c", [])] or [0] * len(a)
    lines = (D / f"{name}.out").read_text().splitlines()
    outs = [ln.split()[0] for ln in lines]
    gas = [int(ln.split()[1]) if len(ln.split()) > 1 else 0 for ln in lines]
    if name.startswith("wide_"):
        a, b, c = a[:len(outs)], b[:len(outs)], c[:len(outs)]
    assert len(outs) == len(a), name
    return list(zip(a, b, c, outs, gas))


def job256(args):
    op, a, b, c, out = args
    mp.dps = 300        # the oracle's precision; gen() lowers it for the FP127 Lambert inputs
    try:
        ref = O.OPS[op](*([a, b, c] if op in THREE else [a, b] if op in TWO else [a]))
        ref = int(ref, 16) if isinstance(ref, str) else ref
    except O.Revert:
        return ("bothrev" if out.startswith("R") else "refrev", None)
    if out.startswith("R"):
        return ("gotrev", None)
    if op in PLAIN:
        return ("ok", int(out, 16) - ref % T256 if op.startswith("toUint") else s256(int(out, 16)) - s256(ref))
    return ("ok", key256(int(out, 16)) - key256(ref))


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
        "normCdf": lambda: mp.ncdf(x) * ONE,
        "compound": lambda: mp.power(1 + x, int(mp.floor(y))) * ONE,
        "exp2": lambda: mp.power(2, x) * ONE,
        "exp10": lambda: mp.power(10, x) * ONE,
        "log10": lambda: mp.log(x, 10) * ONE,
        "sinh": lambda: mp.sinh(x) * ONE,
        "cosh": lambda: mp.cosh(x) * ONE,
        "tanh": lambda: mp.tanh(x) * ONE,
        "powu": lambda: mp.power(x, int(mp.floor(y))) * ONE,
        "mulUp": lambda: mpf(A) * B / ONE,
        "divUp": lambda: mpf(A) * ONE / B,
        "divDown": lambda: mpf(A) * ONE / B,
        "toFixed18Up": lambda: mpf(A) * 10**18 / ONE,
        "lambertW0": lambda: lambertw(x, 0).real * ONE,
        "lambertWm1": lambda: lambertw(x, -1).real * ONE,
    }[op]()


def job127(args):
    op, a, b, out = args
    mp.dps = 200
    if out.startswith("R"):
        return ("gotrev", None, None, None, None)
    got = s256(int(out, 16))
    t = truth127(op, a, b)
    if abs(t) >= 2**255:
        return ("refover", None, None, None, None)
    err = got - t
    bits = float(log(abs(t), 2) - log(abs(err), 2)) if err != 0 and t != 0 else 999.0
    near = op.startswith("lambert") and s256(a) < 0 and mpf(s256(a)) / ONE + 1 / E < mpf(2) ** -20
    return ("ok", float(err), bits, near, abs(t) >= ONE)


def summarize256(op, res):
    st = Counter(r[0] for r in res)
    errs = [r[1] for r in res if r[0] == "ok"]
    c = Counter(errs)
    return {"lib": "fp256", "op": op, "n": len(errs), "status": dict(st), "correctlyRounded": c.get(0, 0),
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
    s = {"lib": "fp127", "op": op, "n": n, "status": dict(st),
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
        for op in OPS256:
            data = load(f"fp256_{op}")
            res = pool.map(job256, [(op, a, b, c, o) for a, b, c, o, g in data], chunksize=64)
            rows.append(dict(summarize256(op, res), **gasstats([g for *_, g in data]), **fallback("fp256", op, data)))
            print(json.dumps(rows[-1]), flush=True)
        for op in WIDE256:
            if not (D / f"wide_{op}.out").exists():
                continue
            data = load(f"wide_{op}")
            res = pool.map(job256, [(op, a, b, c, o) for a, b, c, o, g in data], chunksize=16)
            rows.append(dict(summarize256(op, res), stage="second", **gasstats([g for *_, g in data])))
            print(json.dumps(rows[-1]), flush=True)
        for op in OPS127 + ["lambertW0", "lambertWm1"]:
            data = load(f"fp127_{op}")
            res = pool.map(job127, [(op, a, b, o) for a, b, c, o, g in data], chunksize=64)
            rows.append(dict(summarize127(op, res), **gasstats([g for *_, g in data]), **fallback("fp127", op, data)))
            print(json.dumps(rows[-1]), flush=True)
    doc = {"_doc": __doc__.strip(), "seed": SEED, "seedLambert": SEED_LW, "rows": rows}
    (OUT / "sweep.json").write_text(json.dumps(doc, indent=1) + "\n")
    md = ["# Random-input accuracy sweep",
          "",
          "Generated by `make sweep` (`scripts/sweep/sweep.py`, `test/sweep/Sweep.t.sol`) from seeded random "
          "inputs. FP256 is compared with the correctly rounded word (scripts/fp256/oracle.py, 300 digits, "
          "ties away from zero); FP127 with the real truth at 200 digits, in units of 2^-128. "
          "Data: `sweep.json`.",
          "",
          "## FP256",
          "",
          "Release four: every op below is correctly rounded or exact by construction; the "
          "directed ops (Down: toward minus infinity, Up: toward plus infinity) are compared "
          "with the exact value rounded in their direction, the plain-integer ones (toUint, "
          "toInt) as integers.",
          "",
          "Gas is the inline library's (FP256Lib) own cost on these inputs, median / 99th "
          "percentile / largest, the second stage's runs included where the fast value's "
          "error bound reached the rounding boundary. *Fallback* is the share of inputs whose "
          "rounding test fired (a dash: the op has none; Lambert W runs its wide step always).",
          "",
          "| op | inputs | correctly rounded | misrounded | max ULP | gas median / p99 / max | fallback |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        if r["lib"] == "fp256" and "stage" not in r:
            md.append(f"| {r['op']} | {r['n']:,} | {r['correctlyRounded']:,} | {r['misrounded']:,} | {r['maxUlp']} | "
                      f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} | {pct(r)} |")
    if any(r.get("stage") for r in rows):
        md += ["",
               "### The second stage alone",
               "",
               "The first 4,000 inputs of each op again, through a test-only copy of FP256Lib whose "
               "rounding test always fails, so every result comes from the wide second stage "
               "(two words at 2^-510) that normally runs only when the fast value is too close to "
               "a tie.",
               "",
               "| op | inputs | correctly rounded | misrounded | max ULP | gas median / p99 / max |",
               "|---|---:|---:|---:|---:|---:|"]
        for r in rows:
            if r.get("stage"):
                md.append(f"| {r['op']} | {r['n']:,} | {r['correctlyRounded']:,} | {r['misrounded']:,} | {r['maxUlp']} | "
                          f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} |")
    md += ["",
           "## FP127",
           "",
           "*nearest*: within half a ULP; *faithful*: within one; *min bits*: fewest correct bits relative to the "
           "result, over results of magnitude 1 or more (below 1 a fixed point's absolute grid sets the bits; "
           "for Lambert W the 2^-20 neighbourhood of -1/e is shown separately). The directed ops (mulUp, divUp, "
           "divDown, toFixed18Up) are under one ULP in their direction by design: *below / above truth* shows "
           "the direction; toFixed18Up is measured in its own unit, 10^-18. Gas is FP127Lib's own cost, "
           "median / p99 / largest; *fallback* is the share of inputs that took the double-word decider "
           "(ln, log2, log10 near a midpoint; powu and compound on a 512-bit mantissa; a dash: the op has none).",
           "",
           "| op | inputs | nearest | faithful | max ULP | median ULP | min bits (≥ 1) | below / above truth | gas median / p99 / max | fallback |",
           "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|"]
    for r in rows:
        if r["lib"] == "fp127":
            near = r.get("minBitsWithin2^-20OfMinus1/e")
            mb = "—" if r["minBits"] is None else f"{r['minBits']}" + (f" ({near} near −1/e)" if near is not None else "")
            md.append(f"| {r['op']} | {r['n']:,} | {r['nearest']:,} | {r['faithful']:,} | {r['maxUlp']:.3g} | "
                      f"{r['medianUlp']:.3g} | {mb} | {r['below']:,} / {r['above']:,} | "
                      f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} | {pct(r)} |")
    (OUT / "sweep.md").write_text("\n".join(md) + "\n")
    print("wrote docs/benchmarks/sweep.{json,md}")


WIDE_TEST = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// GENERATED by scripts/sweep/sweep.py for the second-stage pass; removed after the run.

import {Test} from "forge-std/Test.sol";
import {FP256LibWide} from "./FP256LibWide.sol";

contract SweepWide is Test {
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
        string memory path = string.concat(DIR, "fp256_", op, ".json");
        if (!vm.exists(path)) return;
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = two ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, "wide_", op, ".out");
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


def run_wide():
    """Generate FP256LibWide and its runner, run them, remove them."""
    wd = ROOT / "test" / "sweep" / "wide"
    subprocess.run(["uv", "run", "scripts/fp127/gen.py", "--lib", "fp256", "--wide-lib",
                    str(wd / "FP256LibWide.sol")], cwd=ROOT, check=True)
    names = WIDE256 + [f"{op}x" for op in EXTRA]
    fn = {f"{op}x": op for op in EXTRA}
    disp = "\n".join(f'        if (op == "{n}") {{ g0 = gasleft(); r = FP256LibWide.{fn.get(n, n)}(a{", b" if fn.get(n, n) in TWO else ""}); g = gasleft(); }}'
                      for n in names)
    runs = "\n".join(f'    function test_{n}() public {{ this.runOne("{n}", {"true" if fn.get(n, n) in TWO else "false"}); }}' for n in names)
    (wd / "SweepWide.t.sol").write_text(WIDE_TEST % (disp, WIDE_N, WIDE_N, runs))
    try:
        subprocess.run(["forge", "test", "--match-path", "test/sweep/wide/SweepWide.t.sol", "-q"], cwd=ROOT, check=True)
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
/// libraries record into memory from 0x8000 (scripts/fp127/gen.py: count_wrap,
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
    """(name, expression) of every op in Sweep.t.sol's f, in order."""
    src = (ROOT / "test" / "sweep" / "Sweep.t.sol").read_text()
    return re.findall(r'if \(op == "(\w+)"\) \{ g0 = gasleft\(\); r = (.*?); g = gasleft\(\); \}', src)


def rec_words(kind: str) -> int:
    """Record words from 0x8000: the counter, or the probes' shared words and three per probe."""
    if kind == "count":
        return 1
    return (G.PROBE_BASE - G.COUNT_SLOT + G.PROBE_STRIDE * max(len(v) for v in G.PROBES.values())) // 32


def nargs(name: str) -> int:
    op = name.split("_", 1)[1] if "_" in name else name
    op = op[:-1] if name.startswith("fp256_") and op.endswith("x") and op[:-1] in EXTRA else op
    return 3 if op in THREE else 2 if op in TWO else 1


def wide_names() -> list[str]:
    """The input files of the second-stage pass, as run_wide runs them."""
    return [f"fp256_{op}" for op in WIDE256] + [f"fp256_{op}x" for op in EXTRA]


def run_instrumented(kind: str, forced: bool = False):
    """Generate the count or probe libraries and their runner, run them on the
    swept inputs, remove them. forced: FP256 only, with the rounding test
    forced to fail as in run_wide (gen.py --forced), on the same first WIDE_N
    inputs of the ops with a second stage; the outputs are <kind>wide_*.out."""
    tag = kind + ("wide" if forced else "")
    Tag = tag.capitalize()
    wd = ROOT / "test" / "sweep" / tag
    libs = ("fp256",) if forced else ("fp256", "fp127")
    for lib in libs:
        subprocess.run(["uv", "run", "scripts/fp127/gen.py", "--lib", lib, f"--{kind}-lib",
                        str(wd / f"{lib.upper()}Lib{Tag}.sol")] + (["--forced"] if forced else []), cwd=ROOT, check=True)
    want = set(wide_names()) if forced else None
    disp, runs = [], []
    for name, expr in sweep_dispatch():
        if forced and name != "noop" and name not in want:
            continue
        expr = expr.replace("FP256Lib.", f"FP256Lib{Tag}.").replace("FP127Lib.", f"FP127Lib{Tag}.")
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
    names = [name] + ([name + "x"] if lib == "fp256" and op in EXTRA and (D / f"{name}x.json").exists() else [])
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
    return {"fallback": sum(1 for c in fired if c), "fallbackRuns": sum(fired), "fallbackPct": round(100 * sum(1 for c in fired if c) / len(rec), 3)}


def pct(r) -> str:
    if "fallbackPct" not in r:
        return "—"
    p = r["fallbackPct"]
    return "0" if p == 0 else f"{p:.2f}%" if p >= 0.01 else f"{p:.3f}%"


def main():
    if sys.argv[1:] != ["score"]:
        gen()
        subprocess.run(["forge", "test", "--match-path", "test/sweep/Sweep.t.sol", "-q"], cwd=ROOT, check=True)
        run_wide()
        run_instrumented("count")
    score()


if __name__ == "__main__":
    main()

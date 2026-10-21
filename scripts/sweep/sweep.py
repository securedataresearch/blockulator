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

Inputs are seeded (20261020; Lambert W 7) and written to cache/sweep/, which is not
committed. FP256 results are compared with the word the oracle (scripts/fp256/oracle.py:
exact rationals and mpmath at 300 digits, half away from zero) returns, as a signed
distance in ULPs. FP127 results are compared with the real truth at 200 digits, as
|got - truth| in units of 2^-128. Writes docs/benchmarks/sweep.{json,md}.
"""
import json
import multiprocessing as mpc
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fp256"))
import oracle as O  # noqa: E402
from mpmath import mp, mpf, e as E, lambertw, log  # noqa: E402

D = ROOT / "cache" / "sweep"
OUT = ROOT / "docs" / "benchmarks"
T256 = 1 << 256
ONE = 1 << 128
BIAS = 0x3FFFF
SEED, SEED_LW = 20261020, 7
OPS256 = ["add", "mul", "div", "sqrt", "exp", "ln", "log1p", "expm1", "pow", "erf", "erfc", "normCdf",
          "compound", "lambertW0", "lambertWm1", "powu",
          "mulDown", "mulUp", "divDown", "divUp", "toUintDown", "toUintUp", "toIntDown", "toIntUp",
          "floor", "ceil", "fromUintDown", "fromUintUp", "toFixed18Down", "toFixed18Up"]
# the ops with a wide second stage, swept again through FP256LibWide
WIDE256 = ["exp", "ln", "log1p", "expm1", "pow", "erf", "erfc", "normCdf", "compound", "lambertW0",
           "lambertWm1", "powu"]
WIDE_N = 4000
PLAIN = {"toUintDown", "toUintUp", "toIntDown", "toIntUp", "toFixed18Down", "toFixed18Up"}
OPS127 = ["mul", "div", "sqrt", "exp", "ln", "log2", "pow", "cbrt", "expm1", "erf", "normCdf", "compound",
          "exp2", "exp10", "log10", "sinh", "cosh", "tanh", "powu", "mulUp", "divUp", "divDown", "toFixed18Up"]
TWO = {"add", "mul", "div", "pow", "compound", "powu", "mulDown", "mulUp", "divDown", "divUp"}


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


def write(name, a, b=None):
    d = {"a": ["0x%064x" % (x % T256) for x in a]}
    if b is not None:
        d["b"] = ["0x%064x" % (x % T256) for x in b]
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
    lines = (D / f"{name}.out").read_text().splitlines()
    outs = [ln.split()[0] for ln in lines]
    gas = [int(ln.split()[1]) if len(ln.split()) > 1 else 0 for ln in lines]
    if name.startswith("wide_"):
        a, b = a[:len(outs)], b[:len(outs)]
    assert len(outs) == len(a), name
    return list(zip(a, b, outs, gas))


def job256(args):
    op, a, b, out = args
    mp.dps = 300        # the oracle's precision; gen() lowers it for the FP127 Lambert inputs
    try:
        ref = O.OPS[op](*([a, b] if op in TWO else [a]))
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
            res = pool.map(job256, [(op, a, b, o) for a, b, o, g in data], chunksize=64)
            rows.append(dict(summarize256(op, res), **gasstats([g for *_, g in data])))
            print(json.dumps(rows[-1]), flush=True)
        for op in WIDE256:
            if not (D / f"wide_{op}.out").exists():
                continue
            data = load(f"wide_{op}")
            res = pool.map(job256, [(op, a, b, o) for a, b, o, g in data], chunksize=16)
            rows.append(dict(summarize256(op, res), stage="second", **gasstats([g for *_, g in data])))
            print(json.dumps(rows[-1]), flush=True)
        for op in OPS127 + ["lambertW0", "lambertWm1"]:
            res = pool.map(job127, [(op, a, b, o) for a, b, o, g in load(f"fp127_{op}")], chunksize=64)
            rows.append(summarize127(op, res))
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
          "error bound reached the rounding boundary.",
          "",
          "| op | inputs | correctly rounded | misrounded | max ULP | gas median / p99 / max |",
          "|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        if r["lib"] == "fp256" and "stage" not in r:
            md.append(f"| {r['op']} | {r['n']:,} | {r['correctlyRounded']:,} | {r['misrounded']:,} | {r['maxUlp']} | "
                      f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} |")
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
           "the direction; toFixed18Up is measured in its own unit, 10^-18.",
           "",
           "| op | inputs | nearest | faithful | max ULP | median ULP | min bits (≥ 1) | below / above truth |",
           "|---|---:|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        if r["lib"] == "fp127":
            near = r.get("minBitsWithin2^-20OfMinus1/e")
            mb = "—" if r["minBits"] is None else f"{r['minBits']}" + (f" ({near} near −1/e)" if near is not None else "")
            md.append(f"| {r['op']} | {r['n']:,} | {r['nearest']:,} | {r['faithful']:,} | {r['maxUlp']:.3g} | "
                      f"{r['medianUlp']:.3g} | {mb} | {r['below']:,} / {r['above']:,} |")
    (OUT / "sweep.md").write_text("\n".join(md) + "\n")
    print("wrote docs/benchmarks/sweep.{json,md}")


WIDE_TEST = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// GENERATED by scripts/sweep/sweep.py for the second-stage pass; removed after the run.

import {Test} from "forge-std/Test.sol";
import {FP256LibWide} from "./FP256LibWide.sol";

contract SweepWide is Test {
    string constant DIR = "cache/sweep/";

    function f(bytes32 op, int256 a, int256 b) external pure returns (int256) {
        if (op == "noop") return 0;
%s
        revert("op");
    }

    function _base() internal view returns (uint256) {
        uint256 g0 = gasleft();
        try this.f("noop", 0, 0) returns (int256) {} catch {}
        return g0 - gasleft();
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
            uint256 g0 = gasleft();
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i]))) returns (int256 r) {
                uint256 g = g0 - gasleft();
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
    }

    function test_sweep_wide() public {
%s
    }
}
"""


def run_wide():
    """Generate FP256LibWide and its runner, run them, remove them."""
    wd = ROOT / "test" / "sweep" / "wide"
    subprocess.run(["uv", "run", "scripts/fp127/gen.py", "--lib", "fp256", "--wide-lib",
                    str(wd / "FP256LibWide.sol")], cwd=ROOT, check=True)
    names = WIDE256 + [f"{op}x" for op in EXTRA]
    fn = {f"{op}x": op for op in EXTRA}
    disp = "\n".join(f'        if (op == "{n}") return FP256LibWide.{fn.get(n, n)}(a{", b" if fn.get(n, n) in TWO else ""});'
                      for n in names)
    runs = "\n".join(f'        this.runOne("{n}", {"true" if fn.get(n, n) in TWO else "false"});' for n in names)
    (wd / "SweepWide.t.sol").write_text(WIDE_TEST % (disp, WIDE_N, WIDE_N, runs))
    try:
        subprocess.run(["forge", "test", "--match-path", "test/sweep/wide/SweepWide.t.sol", "-q"], cwd=ROOT, check=True)
    finally:
        for f in wd.glob("*"):
            f.unlink()
        wd.rmdir()


def main():
    if sys.argv[1:] != ["score"]:
        gen()
        subprocess.run(["forge", "test", "--match-path", "test/sweep/Sweep.t.sol", "-q"], cwd=ROOT, check=True)
        run_wide()
    score()


if __name__ == "__main__":
    main()

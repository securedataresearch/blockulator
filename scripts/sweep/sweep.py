#!/usr/bin/env python3
"""Random-input accuracy sweep of the inline FP127 and FP256 libraries against
correctly rounded truth.

    uv run scripts/sweep/sweep.py          # gen -> forge (test/sweep/Sweep.t.sol) -> score
    uv run scripts/sweep/sweep.py score    # re-score the last forge outputs only

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
          "compound", "lambertW0"]
OPS127 = ["mul", "div", "sqrt", "exp", "ln", "log2", "pow", "cbrt", "expm1", "erf", "normCdf", "compound"]
TWO = {"add", "mul", "div", "pow", "compound"}


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


# ---- scoring ---------------------------------------------------------------

def s256(v):
    v %= T256
    return v - T256 if v >> 255 else v


def key256(w):
    w %= T256
    return -(w & (T256 // 2 - 1)) if w >> 255 else w


def load(name):
    j = json.loads((D / f"{name}.json").read_text())
    a = [int(x, 16) for x in j["a"]]
    b = [int(x, 16) for x in j.get("b", [])] or [0] * len(a)
    outs = (D / f"{name}.out").read_text().split()
    assert len(outs) == len(a), name
    return list(zip(a, b, outs))


def job256(args):
    op, a, b, out = args
    try:
        ref = O.OPS[op](*([a, b] if op in TWO else [a]))
        ref = int(ref, 16) if isinstance(ref, str) else ref
    except O.Revert:
        return ("bothrev" if out.startswith("R") else "refrev", None)
    if out.startswith("R"):
        return ("gotrev", None)
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
            res = pool.map(job256, [(op, a, b, o) for a, b, o in load(f"fp256_{op}")], chunksize=64)
            rows.append(summarize256(op, res))
            print(json.dumps(rows[-1]), flush=True)
        for op in OPS127 + ["lambertW0", "lambertWm1"]:
            res = pool.map(job127, [(op, a, b, o) for a, b, o in load(f"fp127_{op}")], chunksize=64)
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
          "| op | inputs | correctly rounded | misrounded | max ULP |",
          "|---|---:|---:|---:|---:|"]
    for r in rows:
        if r["lib"] == "fp256":
            md.append(f"| {r['op']} | {r['n']:,} | {r['correctlyRounded']:,} | {r['misrounded']:,} | {r['maxUlp']} |")
    md += ["",
           "## FP127",
           "",
           "*nearest*: within half a ULP; *faithful*: within one; *min bits*: fewest correct bits relative to the "
           "result, over results of magnitude 1 or more (below 1 a fixed point's absolute grid sets the bits; "
           "for Lambert W the 2^-20 neighbourhood of -1/e is shown separately).",
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


def main():
    if sys.argv[1:] != ["score"]:
        gen()
        subprocess.run(["forge", "test", "--match-path", "test/sweep/Sweep.t.sol", "-q"], cwd=ROOT, check=True)
    score()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""FP127 reference oracle, version 2.

Exact reference values for every FP127 op in native 127.128 (one int256,
value = raw / 2^128), with the same rounding the Yul uses and the same
domain: where the Yul reverts, the oracle says `REVERT:<ErrorName>`.

    uv run scripts/fp127/oracle.py one <op> <arg>...      one word (hex) or REVERT:<Error>
    uv run scripts/fp127/oracle.py vectors                write test/fp127/vectors/<op>.json
    uv run scripts/fp127/oracle.py check                  regenerate to a temp dir and diff

Arguments are decimal or 0x-hex, two's complement for negatives (a value
at or above 2^255 is negative).

Rounding, matching contracts/src/fp127/README.md:
    mul, polynomials, toFixed18   floor toward -inf
    div, fromFixed18, inv          truncate toward 0
    transcendentals                mpmath at 200 digits, then floor
The Yul floors every Horner step, so floor is the right reference and
the tests allow a few ULP on top.
"""
from __future__ import annotations

import difflib
import json
import random
import sys
import tempfile
from pathlib import Path

from mpmath import mp, mpf, mpc, lambertw

mp.dps = 200

ROOT = Path(__file__).resolve().parents[2]
VEC_DIR = ROOT / "test" / "fp127" / "vectors"
SPEC = ROOT / "scripts" / "fp127" / "vector_spec.json"

ONE = 1 << 128
HALF = 1 << 127
MASK = ONE - 1
TWO255 = 1 << 255
TWO256 = 1 << 256
MIN = -TWO255
MAX = TWO255 - 1
E18 = 10**18

INV_E_RAW = 0x5E2D58D8B3BCDF1ABADEC7829054F90D  # floor(2^128 / e), the Huff constant


class Revert(Exception):
    def __init__(self, name: str):
        super().__init__(name)
        self.name = name


# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------

def parse(s: str) -> int:
    v = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
    if v >= TWO255:
        v -= TWO256
    return v


def word(v: int) -> str:
    return f"0x{v % TWO256:064x}"


def fit(v: int) -> int:
    if v < MIN or v > MAX:
        raise Revert("Overflow")
    return v


def to_mpf(raw: int):
    return mpf(raw) / mpf(ONE)


def floor_raw(x) -> int:
    """mpf value -> floor(value * 2^128) as int."""
    return int(mp.floor(x * mpf(ONE)))


def mfloor(x) -> int:
    return fit(floor_raw(x))


# ---------------------------------------------------------------------------
# Integer-exact ops
# ---------------------------------------------------------------------------

def op_add(a, b): return fit(a + b)
def op_sub(a, b): return fit(a - b)
def op_mul(a, b): return fit((a * b) >> 128)          # Python >> floors


def _trunc_div(n: int, d: int) -> int:
    q = abs(n) // abs(d)
    return -q if (n < 0) != (d < 0) else q


def op_div(a, b):
    if b == 0:
        raise Revert("DivisionByZero")
    return fit(_trunc_div(a << 128, b))


def op_fromFixed18(x):
    if x < -(1 << 127) or x >= (1 << 127):
        raise Revert("OutOfRange")
    return _trunc_div(x << 128, E18)


def op_toFixed18(x):
    return (x * E18) >> 128


def op_abs(x):
    if x == MIN:
        raise Revert("Overflow")
    return abs(x)


def op_neg(x):
    if x == MIN:
        raise Revert("Overflow")
    return -x


def op_inv(x): return op_div(ONE, x)
def op_sign(x): return (1 if x > 0 else -1 if x < 0 else 0) * ONE
def op_min(a, b): return min(a, b)
def op_max(a, b): return max(a, b)
def op_clamp(x, lo, hi): return min(hi, max(lo, x))
def op_avg(a, b): return (a + b) >> 1


def op_zeroFloorSub(a, b):
    r = op_sub(a, b)
    return r if r > 0 else 0


def op_dist(a, b): return op_abs(op_sub(a, b))
def op_lerp(a, b, t): return op_add(a, op_mul(t, op_sub(b, a)))


def op_floor(x):
    return (x >> 128) << 128


def op_ceil(x):
    return fit(-op_floor(-x)) if x != MIN else MIN


def op_frac(x): return x & MASK
def op_round(x): return op_floor(op_add(x, HALF))


def op_gcd(a, b):
    import math
    return math.gcd(abs(a >> 128), abs(b >> 128)) << 128


def op_factorial(n):
    if n < 0:
        raise Revert("OutOfRange")
    k = n >> 128
    if k > 33:
        raise Revert("OutOfRange")
    import math
    return math.factorial(k) << 128


# ---------------------------------------------------------------------------
# Transcendentals (mpmath, then floor)
# ---------------------------------------------------------------------------

def op_exp(x):
    if x == 0:
        return ONE
    if x > 88 * ONE:
        raise Revert("Overflow")
    if x < -88 * ONE:
        return 0
    return mfloor(mp.exp(to_mpf(x)))


def op_exp2(x):
    if x >= 127 * ONE:
        raise Revert("Overflow")
    if x < -128 * ONE:
        return 0
    return mfloor(mp.power(2, to_mpf(x)))


def op_exp10(x):
    # the Yul computes exp2(mul(x, log2(10))) with checked mul
    y = op_mul(x, 0x35269E12F346E2BF924AFDBFD36BF6D33)
    if y >= 127 * ONE:
        raise Revert("Overflow")
    if y < -128 * ONE:
        return 0
    return mfloor(mp.power(10, to_mpf(x)))


def op_pi(terms):
    """Ramanujan's 1914 series in exact reals, floor(terms) terms, floored
    to the grid; 1 <= floor(terms) <= 7 (zero terms is an empty sum)."""
    if terms < 0:
        raise Revert("OutOfRange")
    n = terms >> 128
    if n > 7 or n == 0:
        raise Revert("OutOfRange")
    s = mpf(0)
    for k in range(n):
        s += mp.factorial(4 * k) * (1103 + 26390 * k) / (mp.factorial(k) ** 4 * mpf(396) ** (4 * k))
    return mfloor(1 / (2 * mp.sqrt(2) / 9801 * s))


def _pos(x):
    if x <= 0:
        raise Revert("OutOfRange")


def op_ln(x):
    _pos(x)
    return mfloor(mp.log(to_mpf(x)))


def op_log2(x):
    _pos(x)
    return mfloor(mp.log(to_mpf(x), 2))


def op_log10(x):
    _pos(x)
    return mfloor(mp.log(to_mpf(x), 10))


def op_log2Up(x):
    _pos(x)
    if x & (x - 1) == 0:
        return (x.bit_length() - 1 - 128) * ONE
    return op_ceil(op_log2(x))


def op_sqrt(x):
    if x < 0:
        raise Revert("OutOfRange")
    import math
    return math.isqrt(x << 128)


def op_cbrt(x):
    if x == 0:
        return 0
    neg = x < 0
    if neg:
        x = op_abs(x)
    v = mp.cbrt(to_mpf(x))
    r = mfloor(v)
    return -r if neg else r


def op_pow(x, y):
    if y == 0:
        return ONE
    if x == 0:
        return 0
    if x == ONE:
        return ONE
    if x < 0:
        raise Revert("OutOfRange")
    # exact shortcuts mirror the Yul so that the reference is what the
    # library can actually hit
    if y == ONE:
        return x
    if y == 2 * ONE:
        return op_mul(x, x)
    if y == 3 * ONE:
        return op_mul(op_mul(x, x), x)
    if y == 4 * ONE:
        x2 = op_mul(x, x)
        return op_mul(x2, x2)
    if y == HALF:
        return op_sqrt(x)
    if y == ONE // 4:
        return op_sqrt(op_sqrt(x))
    if y == -ONE:
        return op_inv(x)
    v = mp.power(to_mpf(x), to_mpf(y))
    r = floor_raw(v)
    if r >= TWO255:
        raise Revert("Overflow")
    return r


def op_gavg(a, b): return op_sqrt(op_mul(a, b))
def op_hypot(a, b): return op_sqrt(op_add(op_mul(a, a), op_mul(b, b)))


def op_lambertW0(x):
    if x < -INV_E_RAW:
        raise Revert("OutOfRange")
    if x == 0:
        return 0
    w = lambertw(to_mpf(x), k=0)
    if isinstance(w, mpc):
        w = w.real
    return mfloor(w)


def op_lambertWm1(x):
    if x < -INV_E_RAW or x >= 0:
        raise Revert("OutOfRange")
    w = lambertw(to_mpf(x), k=-1)
    if isinstance(w, mpc):
        w = w.real
    return mfloor(w)


# ---------------------------------------------------------------------------
# v4: integer powers, near one, hyperbolic, the error function
# ---------------------------------------------------------------------------

def op_powu(x, n):
    """x^floor(n): exact rational when the exponent is small, mpmath beyond.
    The Yul rounds to nearest; the oracle floors, as for every other op."""
    k = n >> 128
    if k == 0:
        return ONE
    if x == 0:
        if k < 0:
            raise Revert("DivisionByZero")
        return 0
    neg = x < 0 and (k & 1) == 1
    ax = abs(x)
    # decide the magnitude first so an absurd exponent never materialises
    mag = k * mp.log(to_mpf(ax), 2)
    if mag > 256:
        raise Revert("Overflow")
    if mag < -130:
        return 0
    v = mp.power(to_mpf(ax), k)
    r = floor_raw(v)
    if r >= TWO255:
        raise Revert("Overflow")
    return -r if neg else r


def op_compound(rate, n):
    return op_powu(op_add(ONE, rate), n)


def op_log1p(x):
    if x <= -ONE:
        raise Revert("OutOfRange")
    return op_ln(op_add(ONE, x))


def op_expm1(x):
    if x == 0:
        return 0
    if x > 88 * ONE:
        raise Revert("Overflow")
    if x < -88 * ONE:
        return -ONE
    return mfloor(mp.expm1(to_mpf(x)))


def op_sinh(x):
    if abs(x) > 88 * ONE:
        raise Revert("Overflow")
    return mfloor(mp.sinh(to_mpf(x)))


def op_cosh(x):
    if abs(x) > 88 * ONE:
        raise Revert("Overflow")
    return mfloor(mp.cosh(to_mpf(x)))


def op_tanh(x):
    return mfloor(mp.tanh(to_mpf(x)))


def op_atanh(x):
    if abs(x) >= ONE:
        raise Revert("OutOfRange")
    return mfloor(mp.atanh(to_mpf(x)))


def op_erf(x):
    return mfloor(mp.erf(to_mpf(x)))


def op_erfc(x):
    return mfloor(mp.erfc(to_mpf(x)))


def op_normCdf(x):
    return mfloor(mp.ncdf(to_mpf(x)))


OPS = {name[3:]: fn for name, fn in globals().items() if name.startswith("op_")}
OPS_LOWER = {k.lower(): k for k in OPS}


def compute(op: str, args: list[int]) -> str:
    fn = OPS[OPS_LOWER[op.lower()]]
    try:
        return word(fn(*args))
    except Revert as r:
        return f"REVERT:{r.name}"


# ---------------------------------------------------------------------------
# Vectors
# ---------------------------------------------------------------------------

def _logspace(lo_exp: int, hi_exp: int, per: int) -> list[int]:
    """Raw values 2^(lo_exp .. hi_exp) sampled `per` points per power of two,
    as values (not raw): exponent e means value 2^e, raw 2^(e+128)."""
    out = []
    steps = (hi_exp - lo_exp) * per
    for i in range(steps + 1):
        e = lo_exp + i / per
        out.append(int(mp.floor(mp.power(2, mpf(e) + 128))))
    return out


def _rand(rng: random.Random, lo: int, hi: int, n: int) -> list[int]:
    return [rng.randint(lo, hi) for _ in range(n)]


def _expand_set(items: list, rng: random.Random) -> list[int]:
    vals: list[int] = []
    for item in items:
        if isinstance(item, str):
            vals.append(parse(item))
        elif isinstance(item, (int,)):
            vals.append(item)
        elif isinstance(item, dict):
            if "val" in item:                       # decimal value -> raw floor(v * 2^128)
                vals.append(int(mp.floor(mpf(item["val"]) * mpf(ONE))))
            if "mult" in item:                      # k * ONE exactly
                vals.append(int(item["mult"]) * ONE)
            if "raw" in item:                       # raw integer (also accepts expressions like "1<<200")
                vals.append(int(eval(str(item["raw"]), {"__builtins__": {}}, {"ONE": ONE, "MIN": MIN, "MAX": MAX, "INV_E": INV_E_RAW})))
            if "logspace" in item:                  # values 2^lo .. 2^hi, `per` points per octave
                lo, hi, per = item["logspace"]
                pts = _logspace(lo, hi, per)
                vals += pts
                if item.get("negate"):
                    vals += [-v for v in pts]
            if "random" in item:                    # raw ints uniform in [lo, hi]
                lo, hi, n = item["random"]
                lo = int(eval(str(lo), {"__builtins__": {}}, {"ONE": ONE, "MIN": MIN, "MAX": MAX, "INV_E": INV_E_RAW}))
                hi = int(eval(str(hi), {"__builtins__": {}}, {"ONE": ONE, "MIN": MIN, "MAX": MAX, "INV_E": INV_E_RAW}))
                vals += _rand(rng, lo, hi, n)
    # dedupe, keep order
    seen = set()
    out = []
    for v in vals:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def build_inputs(spec: dict, sets: dict[str, list[int]], rng: random.Random) -> list[list[int]]:
    cols = [sets[name] for name in spec["args"]]
    if len(cols) == 1:
        return [[v] for v in cols[0]]
    if spec.get("pairing", "cartesian") == "zip":
        n = max(len(c) for c in cols)
        return [[cols[j][i % len(cols[j])] for j in range(len(cols))] for i in range(n)]
    import itertools
    combos = list(itertools.product(*cols))
    cap = spec.get("cap", 400)
    if len(combos) > cap:
        combos = rng.sample(combos, cap)
    return [list(c) for c in combos]


def gen_vectors(out_dir: Path) -> dict[str, int]:
    spec = json.loads(SPEC.read_text())
    rng = random.Random(spec.get("seed", 127))
    sets = {name: _expand_set(items, random.Random(f"{spec.get('seed', 127)}:{name}")) for name, items in spec["sets"].items()}
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for op, entry in spec["ops"].items():
        inputs = build_inputs(entry, sets, rng)
        arity = len(entry["args"])
        cols = {f"in{j}": [word(a[j]) for a in inputs] for j in range(arity)}
        cols["out"] = [compute(op, a) for a in inputs]
        # flat parallel arrays: Foundry's vm.parseJsonStringArray reads each
        # column without an ABI struct decoder (which hits stack-too-deep on
        # nested string arrays)
        lines = [f'"{k}": [\n' + ",\n".join(json.dumps(v) for v in vals) + "\n]" for k, vals in cols.items()]
        (out_dir / f"{op}.json").write_text('{"arity": ' + str(arity) + ',\n' + ",\n".join(lines) + "\n}\n")
        counts[op] = len(inputs)
    return counts


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == "one":
        sys.stdout.write(compute(argv[2], [parse(a) for a in argv[3:]]))
        return 0
    if cmd == "vectors":
        counts = gen_vectors(VEC_DIR)
        print(f"wrote {len(counts)} vector files, {sum(counts.values())} vectors")
        for op, n in sorted(counts.items()):
            print(f"  {op:14s} {n}")
        return 0
    if cmd == "check":
        with tempfile.TemporaryDirectory() as tmp:
            gen_vectors(Path(tmp))
            dirty = False
            for f in sorted(Path(tmp).glob("*.json")):
                cur = VEC_DIR / f.name
                a = cur.read_text() if cur.exists() else ""
                b = f.read_text()
                if a != b:
                    dirty = True
                    sys.stderr.write(f"--- {cur} is stale\n")
                    for line in list(difflib.unified_diff(a.splitlines(), b.splitlines(), str(cur), "generated", lineterm="", n=1))[:12]:
                        sys.stderr.write(line + "\n")
            if dirty:
                sys.stderr.write("run: uv run scripts/fp127/oracle.py vectors\n")
                return 1
        print("vectors-check ok")
        return 0
    print(f"unknown command {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

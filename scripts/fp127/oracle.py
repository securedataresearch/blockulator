#!/usr/bin/env python3
"""FP127 reference oracle, version 3 (FP127 v5).

Reference values for every FP127 op in native 127.128 (one int256,
value = raw / 2^128), with the rounding each op promises and the same
domain: where the Yul reverts, the oracle says `REVERT:<ErrorName>`.
Every vector also carries the real truth, so the precision test measures
the true distance in ULPs, not the distance to a rounded reference.

    uv run scripts/fp127/oracle.py one <op> <arg>...      one word (hex) or REVERT:<Error>
    uv run scripts/fp127/oracle.py vectors                write test/fp127/vectors/<op>.json
    uv run scripts/fp127/oracle.py check                  regenerate to a temp dir and diff

Arguments are decimal or 0x-hex, two's complement for negatives (a value
at or above 2^255 is negative).

Rounding, matching contracts/src/fp127/README.md:
    mul, mulDown, sqrt, toFixed18(Down), avg   floor toward -inf
    mulUp, divUp, toFixed18Up                  ceil toward +inf
    div, inv, fromFixed18                      truncate toward 0
    divDown                                    floor toward -inf
    transcendentals                            nearest, ties up (powu, cbrt and the odd
                                               functions round the magnitude)
mpmath at 200 digits. Each vector file holds in0.. (inputs), out (the
reference word) and t: round((truth - out) 2^64), the truth's offset from
out in units of 2^-64 ULP ("0" where out is exact or a revert).
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


HALF_MPF = mpf(1) / 2


def T(out: int, truth):
    """A result with its real truth (raw units, or WAD units for toFixed18*)."""
    return (out, truth)


def near(v, signed_magnitude: bool = False):
    """Nearest word to v (raw units), ties up; with signed_magnitude, the
    magnitude is rounded and the sign applied (ties away from zero)."""
    if signed_magnitude and v < 0:
        out = -int(mp.floor(-v + HALF_MPF))
    else:
        out = int(mp.floor(v + HALF_MPF))
    return T(fit(out), v)


def nearv(x, signed_magnitude: bool = False):
    """near() of a value (not raw)."""
    return near(x * mpf(ONE), signed_magnitude)


# ---------------------------------------------------------------------------
# Integer-exact ops
# ---------------------------------------------------------------------------

def op_add(a, b): return fit(a + b)
def op_sub(a, b): return fit(a - b)
def op_mul(a, b): return T(fit((a * b) >> 128), mpf(a * b) / ONE)   # Python >> floors
def op_mulDown(a, b): return op_mul(a, b)
def op_mulUp(a, b):
    op_mul(a, b)                                   # the floor must fit first, as in the Yul
    return T(fit(-((-a * b) >> 128)), mpf(a * b) / ONE)


def _trunc_div(n: int, d: int) -> int:
    q = abs(n) // abs(d)
    return -q if (n < 0) != (d < 0) else q


def _divtruth(a, b):
    return mpf(a) * ONE / b


def op_div(a, b):
    if b == 0:
        raise Revert("DivisionByZero")
    return T(fit(_trunc_div(a << 128, b)), _divtruth(a, b))


def op_divDown(a, b):
    if b == 0:
        raise Revert("DivisionByZero")
    op_div(a, b)                                   # the same Overflow decision as div
    return T(fit((a << 128) // b), _divtruth(a, b))


def op_divUp(a, b):
    if b == 0:
        raise Revert("DivisionByZero")
    op_div(a, b)
    return T(fit(-((-a << 128) // b)), _divtruth(a, b))


def op_fromFixed18(x):
    if x < -(1 << 127) or x >= (1 << 127):
        raise Revert("OutOfRange")
    return T(_trunc_div(x << 128, E18), mpf(x) * ONE / E18)


def op_toFixed18(x):
    return T((x * E18) >> 128, mpf(x) * E18 / ONE)


def op_toFixed18Down(x): return op_toFixed18(x)


def op_toFixed18Up(x):
    return T(-((-x * E18) >> 128), mpf(x) * E18 / ONE)


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
def op_avg(a, b): return T((a + b) >> 1, mpf(a + b) / 2)


def op_zeroFloorSub(a, b):
    r = op_sub(a, b)
    return r if r > 0 else 0


def op_dist(a, b): return op_abs(op_sub(a, b))


def op_lerp(a, b, t):
    d = op_sub(b, a)
    out = op_add(a, op_mul(t, d)[0])
    return T(out, a + mpf(t) * d / ONE)


def op_floor(x):
    return (x >> 128) << 128


def op_ceil(x):
    return fit(-op_floor(-x)) if x != MIN else MIN


def op_frac(x): return x & MASK
def op_round(x): return op_floor(op_add(x, HALF))


def op_factorial(n):
    if n < 0:
        raise Revert("OutOfRange")
    k = n >> 128
    if k > 33:
        raise Revert("OutOfRange")
    import math
    return math.factorial(k) << 128


# ---------------------------------------------------------------------------
# Transcendentals: nearest to the 200-digit truth, ties up
# ---------------------------------------------------------------------------

def op_exp(x):
    if x == 0:
        return ONE
    if x > 88 * ONE:
        raise Revert("Overflow")
    if x < -90 * ONE:
        return T(0, mp.exp(to_mpf(x)) * ONE)
    return nearv(mp.exp(to_mpf(x)))


def _pow2_domain(v):
    """the exp2/exp10/pow rule: Overflow from 2^127, nearest otherwise"""
    if v >= mpf(2) ** 127:
        raise Revert("Overflow")
    return nearv(v)


def op_exp2(x):
    if x >= 127 * ONE:
        raise Revert("Overflow")
    v = mp.power(2, to_mpf(x))
    if x < -130 * ONE:
        return T(0, v * ONE)
    return _pow2_domain(v)


def op_exp10(x):
    return _pow2_domain(mp.power(10, to_mpf(x)))


def _pos(x):
    if x <= 0:
        raise Revert("OutOfRange")


def op_ln(x):
    _pos(x)
    return nearv(mp.log(to_mpf(x)))


def op_log2(x):
    _pos(x)
    return nearv(mp.log(to_mpf(x), 2))


def op_log10(x):
    _pos(x)
    return nearv(mp.log(to_mpf(x), 10))


def op_log2Up(x):
    _pos(x)
    k = x.bit_length() - 1 - 128
    return (k + (0 if x & (x - 1) == 0 else 1)) * ONE


def op_sqrt(x):
    if x < 0:
        raise Revert("OutOfRange")
    import math
    return T(math.isqrt(x << 128), mp.sqrt(mpf(x) * ONE))


def op_cbrt(x):
    if x == 0:
        return 0
    if x == MIN:
        raise Revert("Overflow")
    v = mp.cbrt(to_mpf(abs(x)))
    return nearv(v if x > 0 else -v, True)


def op_pow(x, y):
    if y == 0:
        return ONE
    if x == 0:
        return 0
    if x == ONE:
        return ONE
    if x < 0:
        raise Revert("OutOfRange")
    if y == ONE:
        return x
    if y == 2 * ONE:
        return near(mpf(x) * x / ONE)
    if x == 2 * ONE:
        return op_exp2(y)
    if x == 10 * ONE:
        return op_exp10(y)
    v = mp.power(to_mpf(x), to_mpf(y))
    tie = _pow_tie(x, y, v)
    return _pow2_domain(v) if tie is None else tie


def _pow_tie(x, y, v):
    """x^y's word when x^y is exactly a midpoint of the grid (odd 2^-129),
    which mpmath's x^y, rounded at the working precision, could put on
    either side; None otherwise. The candidate w 2^-129 nearest the value is
    checked exactly: (w 2^-129)^(2^j) = x^p for y = p/2^j in lowest terms."""
    if y <= 0 and x & (x - 1):
        return None
    w = int(mp.nint(v * mpf(2) ** 129))
    if w % 2 == 0 or abs(v * mpf(2) ** 129 - w) > mpf(2) ** -64:
        return None
    from fractions import Fraction
    q = Fraction(y, ONE)
    if q.denominator > 1 << 7 or abs(q.numerator) > 1 << 16:
        return None
    if Fraction(w, 1 << 129) ** q.denominator != Fraction(x, ONE) ** q.numerator:
        return None
    if w + 1 >= 2 * TWO255:
        raise Revert("Overflow")
    return T((w + 1) // 2, mpf(w) / 2)


def op_gavg(a, b):
    p = op_mul(a, b)[0]
    return T(op_sqrt(p)[0], mp.sqrt(mpf(a) * b))


def op_hypot(a, b):
    s = op_add(op_mul(a, a)[0], op_mul(b, b)[0])
    return T(op_sqrt(s)[0], mp.sqrt(mpf(a) * a + mpf(b) * b))


def op_lambertW0(x):
    if x < -INV_E_RAW:
        raise Revert("OutOfRange")
    if x == 0:
        return 0
    w = lambertw(to_mpf(x), k=0)
    if isinstance(w, mpc):
        w = w.real
    return nearv(w)


def op_lambertWm1(x):
    if x < -INV_E_RAW or x >= 0:
        raise Revert("OutOfRange")
    w = lambertw(to_mpf(x), k=-1)
    if isinstance(w, mpc):
        w = w.real
    return nearv(w)


# ---------------------------------------------------------------------------
# v4: integer powers, near one, hyperbolic, the error function
# ---------------------------------------------------------------------------

def op_powu(x, n):
    """x^floor(n), rounded to nearest on the magnitude (ties away from zero)."""
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
    if mag < -140:
        return T(0, mp.power(to_mpf(ax), k) * ONE * (-1 if neg else 1))
    if abs(k) <= 4096:
        from fractions import Fraction
        v = Fraction(ax, ONE) ** k * ONE
        out = (v.numerator * 2 + v.denominator) // (2 * v.denominator)
        tv = mpf(v.numerator) / v.denominator
    else:
        with mp.workdps(260):
            tv = mp.exp(k * mp.log(mpf(ax) / ONE)) * ONE
        out = int(mp.floor(tv + HALF_MPF))
    if out >= TWO255:
        raise Revert("Overflow")
    return T(-out, -tv) if neg else T(out, tv)


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
    v = mp.expm1(to_mpf(x))
    if x < -90 * ONE:
        return T(-ONE, v * ONE)
    return nearv(v)


def op_sinh(x):
    if abs(x) > 88 * ONE:
        raise Revert("Overflow")
    return nearv(mp.sinh(to_mpf(x)), True)


def op_cosh(x):
    if abs(x) > 88 * ONE:
        raise Revert("Overflow")
    return nearv(mp.cosh(to_mpf(x)))


def op_tanh(x):
    return nearv(mp.tanh(to_mpf(x)), True)


def op_atanh(x):
    if abs(x) >= ONE:
        raise Revert("OutOfRange")
    return nearv(mp.atanh(to_mpf(x)), True)


def op_erf(x):
    return nearv(mp.erf(to_mpf(x)), True)


def op_erfc(x):
    return nearv(mp.erfc(to_mpf(x)))


def op_normCdf(x):
    return nearv(mp.ncdf(to_mpf(x)))


OPS = {name[3:]: fn for name, fn in globals().items() if name.startswith("op_")}
OPS_LOWER = {k.lower(): k for k in OPS}


def evaluate(op: str, args: list[int]) -> tuple[str, str]:
    """(reference word or REVERT:<Error>, truth offset in 2^-64 ULP as a decimal string)"""
    fn = OPS[OPS_LOWER[op.lower()]]
    try:
        res = fn(*args)
    except Revert as r:
        return f"REVERT:{r.name}", "0"
    if isinstance(res, tuple):
        out, truth = res
        t = int(mp.floor((truth - out) * mpf(2) ** 64 + HALF_MPF))
        return word(out), str(t)
    return word(res), "0"


def compute(op: str, args: list[int]) -> str:
    return evaluate(op, args)[0]


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
        res = [evaluate(op, a) for a in inputs]
        cols["out"] = [r[0] for r in res]
        cols["t"] = [r[1] for r in res]
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

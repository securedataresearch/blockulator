#!/usr/bin/env python3
"""FP256 reference oracle.

Exact reference values for every FP256 op, with the same rounding the Yul
uses (half up on the magnitude, once) and the same domain: where the Yul
reverts, the oracle says `REVERT:<ErrorName>`.

    uv run scripts/fp256/oracle.py one <op> <word>...     one word (hex) or REVERT:<Error>
    uv run scripts/fp256/oracle.py vectors                write test/fp256/vectors/<op>.json
    uv run scripts/fp256/oracle.py check                  regenerate to a temp dir and diff

Words are the int256 bit patterns (0x-hex or decimal, two's complement).
add, sub, mul, div, sqrt and the conversions are computed with exact
rationals (fractions.Fraction, math.isqrt), so they are bit-exact
references; the transcendental ops go through mpmath at 300 digits and are
rounded the same way. Release four's directed ops (mulDown, mulUp, divDown,
divUp, toUintDown, toUintUp, toIntDown, toIntUp, toFixed18Down, toFixed18Up,
floor, ceil, fromUintDown, fromUintUp) are exact rationals rounded toward minus
or plus infinity.
"""
from __future__ import annotations

import difflib
import json
import math
import random
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

from mpmath import mp, mpf, log, exp as mexp, power, frexp, log1p, expm1, erf as merf, erfc as merfc, ncdf, lambertw

mp.dps = 300

ROOT = Path(__file__).resolve().parents[2]
VEC_DIR = ROOT / "test" / "fp256" / "vectors"
SPEC = ROOT / "scripts" / "fp256" / "vector_spec.json"

BIAS = 0x3FFFF
EMAX = 0x7FFFF
SIGN = 1 << 255
MAG = SIGN - 1
FMASK = (1 << 236) - 1
HIDDEN = 1 << 236
ONE = BIAS << 236
TWO = (BIAS + 1) << 236
HALF = (BIAS - 1) << 236
NEGONE = ONE | SIGN
TWO256 = 1 << 256
TWO255 = 1 << 255
E18 = 10**18
LN2_WORD = 0x3FFFE62E42FEFA39EF35793C7673007E5ED5E81E6864CE5316C5B141A2EB7175
E18_WORD = 0x4003ABC16D674EC8000000000000000000000000000000000000000000000000


class Revert(Exception):
    def __init__(self, name: str):
        super().__init__(name)
        self.name = name


# ---------------------------------------------------------------------------
# The word
# ---------------------------------------------------------------------------

def parse(s: str) -> int:
    v = int(s, 16) if s.lower().startswith("0x") else int(s, 10)
    return v % TWO256


def word(u: int) -> str:
    return f"0x{u % TWO256:064x}"


def unpack(w: int) -> tuple[int, int, int]:
    """(sign, biased exponent, 237-bit significand); zero -> (0, 0, 0)."""
    w %= TWO256
    s = w >> 255
    e = (w >> 236) & EMAX
    f = w & FMASK
    if e == 0:
        if s or f:
            raise Revert("OutOfRange")
        return 0, 0, 0
    return s, e, f | HIDDEN


def decode(w: int) -> Fraction:
    s, e, m = unpack(w)
    if e == 0:
        return Fraction(0)
    v = Fraction(m) * (Fraction(2) ** (e - BIAS - 236))
    return -v if s else v


def encode_tm(s: int, e: int, T: int) -> int:
    """Pack from T = floor(|value| * 2^(237 - e)) (one bit below the grid, so
    T in [2^237, 2^238)): half up on the magnitude, then range checks."""
    M = (T >> 1) + (T & 1)
    if M == 1 << 237:
        M = HIDDEN
        e += 1
    E = e + BIAS
    if E > EMAX:
        raise Revert("Overflow")
    if E < 1:
        return 0
    return (s << 255) | (E << 236) | (M - HIDDEN)


def encode(q: Fraction) -> int:
    """The word nearest to the exact rational q."""
    if q == 0:
        return 0
    s = 1 if q < 0 else 0
    q = abs(q)
    n, d = q.numerator, q.denominator
    e = n.bit_length() - d.bit_length()
    if Fraction(2) ** e > q:
        e -= 1
    elif Fraction(2) ** (e + 1) <= q:
        e += 1
    T = (n << (237 - e)) // d if e <= 237 else n // (d << (e - 237))
    return encode_tm(s, e, T)


def encode_mpf(v) -> int:
    if v == 0:
        return 0
    s = 1 if v < 0 else 0
    m, ex = frexp(abs(v))              # abs(v) = m 2^ex, m in [1/2, 1)
    T = int(mp.floor(m * (mpf(2) ** 238)))
    return encode_tm(s, ex - 1, T)


def to_mpf(w: int):
    q = decode(w)
    return mpf(q.numerator) / q.denominator


def check(w: int) -> None:
    unpack(w)


# ---------------------------------------------------------------------------
# Ops
# ---------------------------------------------------------------------------

def op_add(a, b): return encode(decode(a) + decode(b))
def op_sub(a, b): return encode(decode(a) - decode(b))
def op_mul(a, b): return encode(decode(a) * decode(b))


def op_div(a, b):
    qa, qb = decode(a), decode(b)
    if qb == 0:
        raise Revert("DivisionByZero")
    return encode(qa / qb)


def op_sqrt(x):
    q = decode(x)
    if q < 0:
        raise Revert("OutOfRange")
    if q == 0:
        return 0
    n, d = q.numerator, q.denominator
    # e = floor(log2 sqrt(q)): find via the integer square root at a coarse scale
    e2 = n.bit_length() - d.bit_length()
    e = e2 // 2 - 1
    while Fraction(4) ** (e + 1) <= q:
        e += 1
    while Fraction(4) ** e > q:
        e -= 1
    s = 237 - e
    T = math.isqrt((n << (2 * s)) // d) if s >= 0 else math.isqrt(n // (d << (-2 * s)))
    return encode_tm(0, e, T)


def op_exp(x):
    s, e, m = unpack(x)
    if e == 0:
        return ONE
    u = e - BIAS
    if u >= 18:
        if s:
            return 0
        raise Revert("Overflow")
    return encode_mpf(mexp(to_mpf(x)))


def op_ln(x):
    s, e, m = unpack(x)
    if s or e == 0:
        raise Revert("OutOfRange")
    if x == ONE:
        return 0
    return encode_mpf(log(to_mpf(x)))


def op_log1p(x):
    s, e, m = unpack(x)
    if e == 0:
        return 0
    if s and e - BIAS >= 0:
        raise Revert("OutOfRange")
    return encode_mpf(log1p(to_mpf(x)))


def op_expm1(x):
    s, e, m = unpack(x)
    if e == 0:
        return 0
    if e - BIAS >= 18:
        if s:
            return NEGONE
        raise Revert("Overflow")
    return encode_mpf(expm1(to_mpf(x)))


def op_erf(x):
    s, e, m = unpack(x)
    if e == 0:
        return 0
    return encode_mpf(merf(to_mpf(x)))


def op_erfc(x):
    s, e, m = unpack(x)
    if e == 0:
        return ONE
    return encode_mpf(merfc(to_mpf(x)))


def op_normCdf(x):
    s, e, m = unpack(x)
    if e == 0:
        return HALF
    return encode_mpf(ncdf(to_mpf(x)))


def _below_branch(x):
    """x < -1/e, decided at 300 digits (e x is irrational, never exactly -1)."""
    return x >> 255 and to_mpf(x) * mexp(1) < -1


def op_lambertW0(x):
    s, e, m = unpack(x)
    if e == 0:
        return 0
    if _below_branch(x):
        raise Revert("OutOfRange")
    return encode_mpf(lambertw(to_mpf(x), 0).real)


def op_lambertWm1(x):
    s, e, m = unpack(x)
    if e == 0 or not s or _below_branch(x):
        raise Revert("OutOfRange")
    return encode_mpf(lambertw(to_mpf(x), -1).real)


def _int(n):
    return n - TWO256 if n >= TWO255 else n


def _iroot(a: int, q: int) -> int | None:
    """The integer q-th root of a >= 0 when a is a perfect q-th power."""
    if a < 2:
        return a
    r = int(round(a ** (1.0 / q))) if a.bit_length() < 1000 else 1 << (a.bit_length() // q)
    # Newton from above, then check
    r = max(r, 1)
    while True:
        nr = ((q - 1) * r + a // r ** (q - 1)) // q
        if nr >= r:
            break
        r = nr
    for c in (r - 1, r, r + 1):
        if c >= 0 and c ** q == a:
            return c
    return None


def _exact_pow(x: Fraction, y: Fraction) -> Fraction | None:
    """x^y exactly when it is rational, for x > 0 and y = p / 2^k with k <= 8
    and |p| <= 300 (every exact tie of a 237-bit result is among these); None
    otherwise. Release four: the 300-digit path can land a hair on the wrong
    side of an exact tie."""
    p, q = y.numerator, y.denominator
    if q > 256 or abs(p) > 300:
        return None
    num, den = x.numerator, x.denominator          # den is a power of two
    c = (num & -num).bit_length() - 1
    odd, e2 = num >> c, c - (den.bit_length() - 1)
    if e2 % q:
        return None
    r = _iroot(odd, q)
    if r is None:
        return None
    return (Fraction(r) * Fraction(2) ** (e2 // q)) ** p


def op_powu(x, n):
    """x^n for a plain integer n: exact rationals for small n, 300 digits above."""
    k = _int(n)
    if k == 0:
        return ONE
    s, e, m = unpack(x)
    if e == 0:
        if k < 0:
            raise Revert("DivisionByZero")
        return 0
    if abs(k) <= 300:
        return encode(decode(x) ** k)
    return encode_mpf(power(to_mpf(x), k))


def op_compound(rate, n):
    """(1 + rate)^n for a plain integer n, as exp(n log1p(rate)) at 300 digits."""
    k = _int(n)
    s, e, m = unpack(rate)
    if k == 0 or e == 0:
        return ONE
    q = decode(rate)
    if q < -1:
        raise Revert("OutOfRange")
    if q == -1:
        if k < 0:
            raise Revert("DivisionByZero")
        return 0
    if abs(k) <= 160:
        return encode((1 + q) ** k)
    return encode_mpf(mexp(k * log1p(to_mpf(rate))))


def op_pow(x, y):
    if y == 0:
        return ONE
    sx, ex, mx = unpack(x)
    check(y)
    if ex == 0:
        if y >> 255:
            raise Revert("DivisionByZero")
        return 0
    if x == ONE:
        return ONE
    if sx:
        raise Revert("OutOfRange")
    if y == ONE:
        return x
    if y == TWO:
        return op_mul(x, x)
    if y == HALF:
        return op_sqrt(x)
    if y == NEGONE:
        return op_div(ONE, x)
    t = to_mpf(y) * log(to_mpf(x), 2)
    if abs(t) >= 2 ** 19:
        if t < 0:
            return 0
        raise Revert("Overflow")
    ex = _exact_pow(decode(x), decode(y))
    if ex is not None:
        return encode(ex)
    return encode_mpf(power(2, t))


def op_neg(x):
    check(x)
    return x ^ SIGN if x else 0


def op_abs(x):
    check(x)
    return x & MAG


def op_sign(x):
    check(x)
    return (ONE | (x & SIGN)) if x else 0


def _key(x):
    check(x)
    return -(x & MAG) if x >> 255 else x


def op_cmp(a, b):
    ka, kb = _key(a), _key(b)
    return (ka > kb) - (ka < kb)


def op_lt(a, b): return int(_key(a) < _key(b))


def op_eq(a, b):
    check(a); check(b)
    return int(a == b)


def op_fromUint(x): return encode(Fraction(x % TWO256))


def op_fromFP127(x):
    v = x - TWO256 if x >= TWO255 else x
    return encode(Fraction(v, 1 << 128))


def op_toFP127(x):
    q = decode(x)
    s = q < 0
    T = (abs(q).numerator << 129) // abs(q).denominator      # |q| 2^129, floored
    r = (T >> 1) + (T & 1)
    if r > MAG + int(s):
        raise Revert("Overflow")
    return (-r) % TWO256 if s else r


def op_fromFixed18(x):
    v = x - TWO256 if x >= TWO255 else x
    # the Yul takes the integer as a number first (exact below 2^237) and divides once
    n = encode(Fraction(abs(v)))
    return op_div(n | (SIGN if v < 0 else 0), E18_WORD)


def op_toFixed18(x):
    q = decode(x)
    s = q < 0
    T = (abs(q).numerator * E18 * 2) // abs(q).denominator
    r = (T >> 1) + (T & 1)
    if r > MAG + int(s):
        raise Revert("Overflow")
    return (-r) % TWO256 if s else r


# ---- release four: the edge (directed rounding) -------------------------------

def encode_dir(q: Fraction, up: bool) -> int:
    """The word nearest q in the direction of +infinity (up) or -infinity:
    floor of the magnitude, plus one ULP when the direction is away from
    zero and bits were dropped; past the bottom of the format the smallest
    number away from zero, else zero."""
    if q == 0:
        return 0
    s = 1 if q < 0 else 0
    a = abs(q)
    away = up != bool(s)
    n, d = a.numerator, a.denominator
    e = n.bit_length() - d.bit_length()
    if Fraction(2) ** e > a:
        e -= 1
    elif Fraction(2) ** (e + 1) <= a:
        e += 1
    num, den = (n << (236 - e), d) if e <= 236 else (n, d << (e - 236))
    M, rem = divmod(num, den)
    if away and rem:
        M += 1
        if M == 1 << 237:
            M = HIDDEN
            e += 1
    E = e + BIAS
    if E > EMAX:
        raise Revert("Overflow")
    if E < 1:
        return ((s << 255) | (1 << 236)) if away else 0
    return (s << 255) | (E << 236) | (M - HIDDEN)


def op_mulDown(a, b): return encode_dir(decode(a) * decode(b), False)
def op_mulUp(a, b): return encode_dir(decode(a) * decode(b), True)


def _divdir(a, b, up):
    qa, qb = decode(a), decode(b)
    if qb == 0:
        raise Revert("DivisionByZero")
    return encode_dir(qa / qb, up)


def op_divDown(a, b): return _divdir(a, b, False)
def op_divUp(a, b): return _divdir(a, b, True)


def _floorq(q: Fraction) -> int:
    return q.numerator // q.denominator


def _ceilq(q: Fraction) -> int:
    return -((-q.numerator) // q.denominator)


def _touint(x, up):
    q = decode(x)
    if q < 0:
        raise Revert("OutOfRange")
    v = _ceilq(q) if up else _floorq(q)
    if v >= TWO256:
        raise Revert("Overflow")
    return v


def op_toUintDown(x): return _touint(x, False)
def op_toUintUp(x): return _touint(x, True)


def _toint(x, up):
    q = decode(x)
    v = _ceilq(q) if up else _floorq(q)
    if v >= TWO255 or v < -TWO255:
        raise Revert("Overflow")
    return v % TWO256


def op_toIntDown(x): return _toint(x, False)
def op_toIntUp(x): return _toint(x, True)
def op_floor(x): return encode(Fraction(_floorq(decode(x))))
def op_ceil(x): return encode(Fraction(_ceilq(decode(x))))
def _tofixed18dir(x, up):
    q = decode(x) * E18
    v = _ceilq(q) if up else _floorq(q)
    if v >= TWO255 or v < -TWO255:
        raise Revert("Overflow")
    return v % TWO256


def op_toFixed18Down(x): return _tofixed18dir(x, False)
def op_toFixed18Up(x): return _tofixed18dir(x, True)
def op_fromUintDown(x): return encode_dir(Fraction(x % TWO256), False)
def op_fromUintUp(x): return encode_dir(Fraction(x % TWO256), True)


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

def fval(s: str) -> int:
    return encode(Fraction(s))


def _expand_set(items: list, rng: random.Random) -> list[int]:
    vals: list[int] = []
    for item in items:
        if isinstance(item, str):
            vals.append(parse(item))
        elif isinstance(item, dict):
            if "fval" in item:                      # decimal value -> nearest word
                vals.append(fval(item["fval"]))
            if "fraw" in item:                      # raw word, hex or decimal
                vals.append(parse(str(item["fraw"])))
            if "flog" in item:                      # 2^lo .. 2^hi, `per` points per octave
                lo, hi, per = item["flog"]
                pts = [encode_mpf(mpf(2) ** (lo + i / per)) for i in range((hi - lo) * per + 1)]
                vals += pts
                if item.get("negate"):
                    vals += [p ^ SIGN for p in pts]
            if "frand" in item:                     # random sign, exponent in [lo, hi], significand
                lo, hi, n = item["frand"]
                for _ in range(n):
                    e = rng.randint(lo, hi) + BIAS
                    vals.append((rng.randint(0, 1) << 255) | (e << 236) | rng.getrandbits(236))
    seen = set()
    out = []
    for v in vals:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def build_inputs(spec: dict, sets: dict[str, list[int]], rng: random.Random) -> list[list[int]]:
    rows = _build_rows(spec, sets, rng)
    # explicit tuples (release four: exact ties of pow, compound and powu)
    for pair in spec.get("pairs", []):
        rows.append([_expand_set([item], rng)[0] for item in pair])
    return rows


def _build_rows(spec: dict, sets: dict[str, list[int]], rng: random.Random) -> list[list[int]]:
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
    seed = spec.get("seed", 256)
    rng = random.Random(seed)
    sets = {name: _expand_set(items, random.Random(f"{seed}:{name}")) for name, items in spec["sets"].items()}
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for op, entry in spec["ops"].items():
        inputs = build_inputs(entry, sets, rng)
        arity = len(entry["args"])
        cols = {f"in{j}": [word(a[j]) for a in inputs] for j in range(arity)}
        cols["out"] = [compute(op, a) for a in inputs]
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
                sys.stderr.write("run: uv run scripts/fp256/oracle.py vectors\n")
                return 1
        print("vectors-fp256-check ok")
        return 0
    print(f"unknown command {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

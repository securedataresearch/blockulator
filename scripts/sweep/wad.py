#!/usr/bin/env python3
"""BlockulatorWad against the exact value, and Solady's and PRBMath's WAD
functions beside it, on the same seeded inputs.

    uv run scripts/sweep/wad.py            # make wad: inputs -> forge (test/wad/WadBench.t.sol) -> wad.{json,md}
    uv run scripts/sweep/wad.py score      # re-score the last forge outputs only

The inputs (seed 20261023) cover each function's domain: log-uniform
magnitudes from one wei to the top of the range, both signs where the
function takes them, the inputs whose exact value sits near a wei boundary
(an output near an integer number of wei: x = ln(k) for exp, perfect squares
and cubes for the roots, products one wei either side of a multiple of
10^18), the exact cases (exp(0), ln(1), powers of two and ten for the logs,
perfect powers for pow) and the ends of each domain. make sweep runs the same
inputs through BlockulatorWad as its WAD rows (scripts/sweep/sweep.py), with
a forced second-stage pass.

Truth is the exact real value: integer arithmetic for mul, div, sqrt and
cbrt; mpmath at 300 digits for the rest, rounded in the stated direction. A
value within 10^-250 of an integer is an exact case, and is accepted only
where it is one (exp(0), ln(1), log2 at 10^18 2^k, log10 at 10^(18 + k), a
pow whose rational power is exactly that integer, W(0)); any other would stop
the run.

Each library is scored in its own rounding direction (DIRS): BlockulatorWad
in the direction each function states; Solady floor for the unsigned and
exp/ln/pow results, toward zero for sMulWad, sDivWad and lambertW0Wad (its
sdiv); PRBMath floor for UD60x18 and exp/pow, toward zero for SD59x18's mul,
div and logs (log2 of x < 1 is minus log2(1/x) truncated). *Wrong* counts a
result that is not that integer, or a revert where the value fits, or a value
where the exact one does not.

Gas is each library's internal call alone (WadBench.t.sol reads gasleft() on
either side of the call, net of the same window around an assignment), on
the swept inputs and on a typical set: 200 random inputs per function in its
everyday range (exp of -10..10, ln of 0.001..1000, pow of 0.5..2 to -3..3,
products and quotients of amounts up to 10^9 tokens), which take no shortcut.
Writes docs/benchmarks/wad.{json,md}.
"""
from __future__ import annotations

import json
import math
import multiprocessing as mpc
import os
import random
import re
import statistics
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "cache" / "sweep"
OUT = ROOT / "docs" / "benchmarks"
T256 = 1 << 256
I255 = 1 << 255
W = 10**18
SEED = 20261023
N = 4000          # inputs per function
NT = 200          # typical inputs per function

# Each swept function: name -> (inputs file, arguments, kind, direction)
#   kind: u (uint256 in, uint256 out), s (int256), and the maths it computes
#   direction: 0 floor, 1 ceiling, 2 toward zero
FUNCS = {
    "mulWad": ("mul", 2, "u", 0), "mulWadUp": ("mul", 2, "u", 1),
    "divWad": ("div", 2, "u", 0), "divWadUp": ("div", 2, "u", 1),
    "sMulWad": ("smul", 2, "s", 2), "sMulWadDown": ("smul", 2, "s", 0), "sMulWadUp": ("smul", 2, "s", 1),
    "sDivWad": ("sdiv", 2, "s", 2), "sDivWadDown": ("sdiv", 2, "s", 0), "sDivWadUp": ("sdiv", 2, "s", 1),
    "sqrtWad": ("sqrt", 1, "u", 0), "sqrtWadUp": ("sqrt", 1, "u", 1),
    "cbrtWad": ("cbrt", 1, "u", 0), "cbrtWadUp": ("cbrt", 1, "u", 1),
    "expWad": ("exp", 1, "s", 0), "expWadUp": ("exp", 1, "s", 1),
    "lnWad": ("ln", 1, "s", 0), "lnWadUp": ("ln", 1, "s", 1),
    "log2Wad": ("log2", 1, "s", 0), "log2WadUp": ("log2", 1, "s", 1),
    "log10Wad": ("log10", 1, "s", 0), "log10WadUp": ("log10", 1, "s", 1),
    "powWad": ("pow", 2, "s", 0), "powWadUp": ("pow", 2, "s", 1),
    "lambertW0Wad": ("w0", 1, "s", 2), "lambertW0WadDown": ("w0", 1, "s", 0), "lambertW0WadUp": ("w0", 1, "s", 1),
}
# the functions with a second stage, swept again with the fast path's test forced to fail
WIDE = [f for f, (m, *_) in FUNCS.items() if m in ("exp", "ln", "log2", "log10", "pow", "w0")]
WIDE_N = 4000

# The competitors: library -> our function -> (their call, their direction).
# The calls are Solidity expressions in WadBench.t.sol; a and b are the inputs.
COMP = {
    "solady": {
        "mulWad": ("S.mulWad(uint256(a), uint256(b))", 0), "mulWadUp": ("S.mulWadUp(uint256(a), uint256(b))", 1),
        "divWad": ("S.divWad(uint256(a), uint256(b))", 0), "divWadUp": ("S.divWadUp(uint256(a), uint256(b))", 1),
        "sMulWad": ("S.sMulWad(a, b)", 2), "sDivWad": ("S.sDivWad(a, b)", 2),
        "sqrtWad": ("S.sqrtWad(uint256(a))", 0), "cbrtWad": ("S.cbrtWad(uint256(a))", 0),
        "expWad": ("S.expWad(a)", 0), "lnWad": ("S.lnWad(a)", 0), "powWad": ("S.powWad(a, b)", 0),
        "lambertW0Wad": ("S.lambertW0Wad(a)", 2),
    },
    "prb": {
        "mulWad": ("UD60x18.unwrap(PU.mul(UD60x18.wrap(uint256(a)), UD60x18.wrap(uint256(b))))", 0),
        "divWad": ("UD60x18.unwrap(PU.div(UD60x18.wrap(uint256(a)), UD60x18.wrap(uint256(b))))", 0),
        "sMulWad": ("SD59x18.unwrap(PS.mul(SD59x18.wrap(a), SD59x18.wrap(b)))", 2),
        "sDivWad": ("SD59x18.unwrap(PS.div(SD59x18.wrap(a), SD59x18.wrap(b)))", 2),
        "sqrtWad": ("UD60x18.unwrap(PU.sqrt(UD60x18.wrap(uint256(a))))", 0),
        "expWad": ("SD59x18.unwrap(PS.exp(SD59x18.wrap(a)))", 0),
        "lnWad": ("SD59x18.unwrap(PS.ln(SD59x18.wrap(a)))", 2),
        "log2Wad": ("SD59x18.unwrap(PS.log2(SD59x18.wrap(a)))", 2),
        "log10Wad": ("SD59x18.unwrap(PS.log10(SD59x18.wrap(a)))", 2),
        "powWad": ("SD59x18.unwrap(PS.pow(SD59x18.wrap(a), SD59x18.wrap(b)))", 0),
    },
}
LIBS = ["blockulator", "solady", "prb"]
LABEL = {"blockulator": "BlockulatorWad", "solady": "Solady FixedPointMathLib", "prb": "PRBMath (UD60x18 / SD59x18)"}
DIRNAME = {0: "floor", 1: "ceiling", 2: "toward zero"}


# ---- inputs ----------------------------------------------------------------

def lu(rng, lo, hi):
    """A log-uniform integer with between lo and hi bits."""
    b = rng.randint(lo, hi)
    return rng.getrandbits(b) | (1 << (b - 1)) if b else 0


def sg(rng, x, neg=0.5):
    return -x if rng.random() < neg else x


def near_mult(rng, y, k):
    """x with x y one wei off a multiple of k (or exactly on it)."""
    m = rng.getrandbits(rng.randint(1, 200)) + 1
    t = m * k + rng.choice((-1, 0, 1))
    return max(t // y, 1) + rng.choice((0, 1))


def gen_mul(rng):
    a, b = [], []
    for i in range(N):
        kind = i % 4
        if kind == 0:      # amounts: up to 10^30 each
            x, y = lu(rng, 1, 100), lu(rng, 1, 100)
        elif kind == 1:    # the product near a multiple of 10^18
            y = lu(rng, 1, 128)
            x = near_mult(rng, y, W)
        elif kind == 2:    # the product past 2^256, the result within a word
            x, y = lu(rng, 128, 256), lu(rng, 1, 70)
        else:              # anywhere, results that overflow included
            x, y = lu(rng, 0, 256), lu(rng, 0, 256)
        a.append(x % T256), b.append(y % T256)
    return a, b


def gen_div(rng):
    a, b = [], []
    for i in range(N):
        kind = i % 4
        if kind == 0:
            x, y = lu(rng, 1, 100), lu(rng, 1, 100)
        elif kind == 1:    # x 10^18 one wei off a multiple of y
            y = lu(rng, 1, 160)
            m = rng.getrandbits(rng.randint(1, 180)) + 1
            x = max((m * y + rng.choice((-1, 0, 1))) // W, 0)
        elif kind == 2:    # x 10^18 past 2^256
            x, y = lu(rng, 196, 256), lu(rng, 100, 256)
        else:
            x, y = lu(rng, 0, 256), lu(rng, 0, 256)
        a.append(x % T256), b.append(y % T256)
    return a, b


def gen_smul(rng):
    a, b = gen_mul(rng)
    return [sg(rng, x >> 1) % T256 for x in a], [sg(rng, y >> 1) % T256 for y in b]


def gen_sdiv(rng):
    a, b = gen_div(rng)
    return [sg(rng, x >> 1) % T256 for x in a], [sg(rng, y >> 1) % T256 for y in b]


def gen_sqrt(rng):
    a = []
    for i in range(N):
        kind = i % 3
        if kind == 0:
            x = lu(rng, 0, 256)
        else:              # x = m^2 (an exact root m 10^9) and one either side
            m = lu(rng, 1, 128)
            x = m * m + rng.choice((-1, 0, 0, 1))
        a.append(min(max(x, 0), T256 - 1))
    return a, None


def gen_cbrt(rng):
    a = []
    for i in range(N):
        kind = i % 3
        if kind == 0:
            x = lu(rng, 0, 256)
        else:              # x = m^3 (an exact root m 10^12) and one either side
            m = lu(rng, 1, 85)
            x = m ** 3 + rng.choice((-1, 0, 0, 1))
        a.append(min(max(x, 0), T256 - 1))
    return a, None


def gen_exp(rng):
    from mpmath import mp, mpf, log
    mp.dps = 120
    a = []
    for i in range(N):
        kind = i % 4
        if kind == 0:      # uniform over the domain and a little past each end
            x = rng.randint(-43 * W, 136 * W)
        elif kind == 1:    # |x| log-uniform from one wei
            x = sg(rng, lu(rng, 0, 67))
        elif kind == 2:    # e^x near a whole number of wei: x = ln(k 10^-18) rounded
            k = lu(rng, 1, 254)
            x = int(mp.nint(log(mpf(k) / W) * W)) + rng.choice((-1, 0, 1))
        else:              # the everyday range
            x = rng.randint(-20 * W, 20 * W)
        a.append(x % T256)
    a[:8] = [v % T256 for v in (0, 135305999368893231589, 135305999368893231590, -41446531673892822312,
                                 -41446531673892822313, 1, -1, -(1 << 255))]
    return a, None


def gen_log(rng, base):
    from mpmath import mp, mpf, exp
    mp.dps = 120
    a = []
    for i in range(N):
        kind = i % 4
        if kind == 0:
            x = lu(rng, 1, 255)
        elif kind == 1:    # near one
            x = W + sg(rng, lu(rng, 0, 59))
        elif kind == 2:    # the log near a whole number of wei
            k = sg(rng, lu(rng, 1, 67))
            if base == "ln":
                x = int(mp.nint(exp(mpf(k) / W) * W))
            elif base == "log2":
                x = int(mp.nint(mpf(2) ** (mpf(k) / W) * W))
            else:
                x = int(mp.nint(mpf(10) ** (mpf(k) / W) * W))
            x += rng.choice((-1, 0, 1))
        else:              # the exact cases and the everyday range
            j = rng.randint(0, 3)
            if j == 0 and base == "log2":
                k = rng.randint(-18, 194)
                x = W << k if k >= 0 else W >> -k
            elif j == 0 and base == "log10":
                k = rng.randint(-18, 58)
                x = 10 ** (18 + k)
            else:
                x = rng.randint(W // 1000, 1000 * W)
        a.append(min(max(x, 1), I255 - 1) % T256)
    a[:5] = [v % T256 for v in (W, 1, I255 - 1, 0, -1)]
    return a, None


def gen_pow(rng):
    from mpmath import mp, mpf, log
    mp.dps = 120
    a, b = [], []
    for i in range(N):
        kind = i % 6
        if kind == 0:      # x log-uniform, y keeping |y ln x| under about 140
            x = lu(rng, 1, 255)
            lx = abs(float(log(mpf(x) / W))) or 1e-18
            y = int(sg(rng, rng.uniform(0, min(150 / lx, 2.0 ** 190))) * W)
        elif kind == 1:    # everyday: x in 0.5..2, y in -3..3
            x, y = rng.randint(W // 2, 2 * W), rng.randint(-3 * W, 3 * W)
        elif kind == 2:    # x near one, y huge
            x = W + sg(rng, lu(rng, 0, 50))
            y = sg(rng, lu(rng, 60, 160))
        elif kind == 3:    # exact powers: whole numbers to whole powers, squares to halves
            j = rng.randint(0, 3)
            if j == 0:
                n = rng.randint(1, 8)
                x, y = rng.randint(2, int(2 ** (190 / n)) + 1) * W, n * W
            elif j == 1:
                m = lu(rng, 1, 126)
                x, y = m * m, W // 2
            elif j == 2:
                x, y = rng.choice((W // 2, W // 4, 3 * W // 2, 5 * W // 4, 25 * W // 10)), rng.randint(-6, 6) * W
            else:          # whole cubes to minus one and two
                m = lu(rng, 1, 60)
                x, y = m ** 3 * W, rng.choice((-W, 2 * W))
        elif kind == 4:    # the result near a whole number of wei and near the ends
            x = rng.randint(2 * W, 10**30)
            y = int(mpf(rng.uniform(100, 135.3)) / log(mpf(x) / W) * W)
        else:              # anywhere, with x = 0 and negatives for the reverts
            x = rng.choice((0, rng.randint(1, W), -rng.randint(1, W), lu(rng, 1, 255)))
            y = sg(rng, lu(rng, 0, 70))
        a.append(x % T256), b.append(y % T256)
    return a, b


def gen_w0(rng):
    a = []
    lo = -367879441171442321
    for i in range(N):
        kind = i % 4
        if kind == 0:
            x = lu(rng, 0, 255)
        elif kind == 1:    # just above -1/e
            x = lo + lu(rng, 0, 58)
        elif kind == 2:
            x = -lu(rng, 0, 58)
        else:
            x = rng.randint(lo, 10**21)
        a.append(min(max(x, lo - 2), I255 - 1) % T256)
    a[:6] = [v % T256 for v in (0, lo, lo - 1, 1, -1, I255 - 1)]
    return a, None


GENS = {"mul": gen_mul, "div": gen_div, "smul": gen_smul, "sdiv": gen_sdiv, "sqrt": gen_sqrt, "cbrt": gen_cbrt,
        "exp": gen_exp, "ln": lambda r: gen_log(r, "ln"), "log2": lambda r: gen_log(r, "log2"),
        "log10": lambda r: gen_log(r, "log10"), "pow": gen_pow, "w0": gen_w0}


def typical(rng, maths):
    """The everyday range, no shortcuts (no whole numbers, no 10^18)."""
    nz = lambda v: v + 1 if v % W == 0 else v  # noqa: E731
    if maths in ("mul", "smul"):
        a = [nz(rng.randint(1, 10**27)) for _ in range(NT)]
        b = [nz(rng.randint(W // 100, 100 * W)) for _ in range(NT)]
    elif maths in ("div", "sdiv"):
        a = [nz(rng.randint(1, 10**27)) for _ in range(NT)]
        b = [nz(rng.randint(W // 100, 100 * W)) for _ in range(NT)]
    elif maths in ("sqrt", "cbrt"):
        a, b = [nz(rng.randint(W // 1000, 10**27)) for _ in range(NT)], None
    elif maths == "exp":
        a, b = [nz(rng.randint(-10 * W, 10 * W)) for _ in range(NT)], None
    elif maths in ("ln", "log2", "log10"):
        a, b = [nz(rng.randint(W // 1000, 1000 * W)) for _ in range(NT)], None
    elif maths == "pow":
        a = [nz(rng.randint(W // 2, 2 * W)) for _ in range(NT)]
        b = [nz(rng.randint(-3 * W, 3 * W)) for _ in range(NT)]
    else:
        a, b = [nz(rng.randint(-W // 4, 10 * W)) for _ in range(NT)], None
    if maths in ("smul", "sdiv"):
        a = [sg(rng, x) for x in a]
    return [x % T256 for x in a], (None if b is None else [y % T256 for y in b])


def write(name, a, b=None):
    d = {"a": ["0x%064x" % (x % T256) for x in a]}
    if b is not None:
        d["b"] = ["0x%064x" % (y % T256) for y in b]
    (D / f"{name}.json").write_text(json.dumps(d))


def gen():
    """cache/sweep/wad_<function>.json (the swept inputs, one file per
    function, the same inputs for the directions of one maths) and
    wadtyp_<function>.json (the typical set)."""
    D.mkdir(parents=True, exist_ok=True)
    made = {}
    for maths in GENS:
        made[maths] = GENS[maths](random.Random(f"{SEED}-{maths}"))
        made[maths, "typ"] = typical(random.Random(f"{SEED}-{maths}-typical"), maths)
    for f, (maths, *_) in FUNCS.items():
        write(f"wad_{f}", *made[maths])
        write(f"wadtyp_{f}", *made[maths, "typ"])


# ---- truth -----------------------------------------------------------------

def s256(v):
    v %= T256
    return v - T256 if v >> 255 else v


def rdiv(n, d, direction):
    """n / d rounded in direction (d > 0)."""
    q, r = divmod(n, d)            # floor
    if r and (direction == 1 or (direction == 2 and n < 0)):
        q += 1
    return q


class Rev(Exception):
    pass


class OracleError(Exception):
    """A value the oracle cannot round: within its precision of an integer
    without being a known exact case."""


def exact_int(maths, a, b, v):
    """The integer v rounds to when v (mpf, 300 digits) is within 10^-270 of
    it relative (10^-250 absolute below one) and the value is exactly that
    integer, else None. Raises OracleError on a near-integer that is not an
    exact case: the oracle could not decide it."""
    from mpmath import mpf, nint
    n = int(nint(v))
    if abs(v - n) > mpf(10) ** -250 * max(abs(v) * mpf(10) ** -20, 1):
        return None
    if n == 0 and maths in ("exp", "pow"):
        return None        # a positive value under 10^-250 wei: not an integer
    ok = False
    if maths == "exp":
        ok = a == 0
    elif maths == "ln":
        ok = a == W
    elif maths == "log2":
        ok = n % W == 0 and Fraction(a, W) == Fraction(2) ** (n // W)
    elif maths == "log10":
        ok = n % W == 0 and Fraction(a, W) == Fraction(10) ** (n // W)
    elif maths == "w0":
        ok = a == 0
    elif maths == "pow":
        y = Fraction(b, W)
        p, q = y.numerator, y.denominator
        if a == W or b == 0:
            ok = n == W
        elif q <= 1000 and abs(p) <= 20000:
            ok = Fraction(n, W) ** q == Fraction(a, W) ** p
    if not ok:
        raise OracleError(f"{maths}({a}, {b}) is within the oracle's precision of {n} and not a known exact case")
    return n


def truth(maths, a, b, direction):
    """The exact value rounded in direction, as an integer; Rev when the
    function's domain or its word excludes it."""
    from mpmath import mp, mpf, exp, log, lambertw, floor, ceil
    mp.dps = 300
    if maths == "mul":
        if a >= T256 or b >= T256:
            raise Rev
        return rdiv(a * b, W, direction)
    if maths == "div":
        if b == 0:
            raise Rev
        return rdiv(a * W, b, direction)
    if maths == "smul":
        return rdiv(a * b, W, direction)
    if maths == "sdiv":
        if b == 0:
            raise Rev
        n, d = a * W, b
        if d < 0:
            n, d = -n, -d
        return rdiv(n, d, direction)
    if maths == "sqrt":
        r = math.isqrt(a * W)
        return r + (direction == 1 and r * r != a * W)
    if maths == "cbrt":
        n = a * W * W
        lo, hi = 0, 1 << 130
        while lo < hi:     # the floor of the cube root, exactly
            mid = (lo + hi + 1) // 2
            if mid ** 3 <= n:
                lo = mid
            else:
                hi = mid - 1
        r = lo
        return r + (direction == 1 and r ** 3 != n)
    t = mpf(a) / W
    if maths == "exp":
        v = exp(t) * W
    elif maths in ("ln", "log2", "log10"):
        if a <= 0:
            raise Rev
        v = log(t) * W if maths == "ln" else log(t, 2) * W if maths == "log2" else log(t, 10) * W
    elif maths == "pow":
        if a < 0 or (a == 0 and b < 0):
            raise Rev
        if a == 0:
            return W if b == 0 else 0
        lv = mpf(b) / W * log(t)
        if lv > 200:
            raise Rev
        if lv < -200:
            return 1 if direction == 1 else 0
        v = exp(lv) * W
    elif maths == "w0":
        if a < -367879441171442321:
            raise Rev
        v = lambertw(t, 0).real * W
    n = exact_int(maths, a, b, v)
    if n is not None:
        return n
    if direction == 0 or (direction == 2 and v > 0):
        return int(floor(v))
    return int(ceil(v))


def fits(kind, v):
    return 0 <= v < T256 if kind == "u" else -I255 <= v < I255


def job(args):
    """(status, wei off) for one output: ok/wrong with the signed distance in
    wei, or bothrev / gotrev / refrev."""
    maths, kind, direction, a, b, out = args
    a, b = (a, b) if kind == "u" or maths in ("mul", "div", "sqrt", "cbrt") else (s256(a), s256(b))
    try:
        ref = truth(maths, a, b, direction)
        if not fits(kind, ref):
            raise Rev
    except Rev:
        return ("bothrev" if out.startswith("R") else "refrev", None)
    if out.startswith("R"):
        return ("gotrev", None)
    got = int(out, 16) if kind == "u" else s256(int(out, 16))
    return ("ok", got - ref)


def load(name, inputs=None):
    """(a, b, out, gas) for an input file and its outputs; inputs names the
    input file when it is not the output's own."""
    j = json.loads((D / f"{inputs or name}.json").read_text())
    a = [int(x, 16) for x in j["a"]]
    b = [int(x, 16) for x in j.get("b", [])] or [0] * len(a)
    lines = (D / f"{name}.out").read_text().splitlines()
    outs = [ln.split()[0] for ln in lines]
    gas = [int(ln.split()[1]) if len(ln.split()) > 1 else 0 for ln in lines]
    a, b = a[:len(outs)], b[:len(outs)]
    return list(zip(a, b, outs, gas))


def score_rows(pool, name, f, direction=None, inputs=None):
    """The scored statuses of one output file for function f."""
    maths, _, kind, dflt = FUNCS[f]
    d = dflt if direction is None else direction
    data = load(name, inputs)
    res = pool.map(job, [(maths, kind, d, a, b, o) for a, b, o, g in data], chunksize=32)
    return res, [g for *_, g in data]


def summary(res, gas):
    """n inputs; wrongWei: values off by any wei (of `valued`, the inputs where
    the library and the truth both return one); revertInRange: reverts where
    the exact value fits; valueOutOfRange: a value where the exact one does
    not exist or fit; wrong: all three. maxWei / medianWei over the valued
    inputs, the share of them off by a wei, and a histogram (capped at 10^6)."""
    st = Counter(r[0] for r in res)
    off = [abs(r[1]) for r in res if r[0] == "ok"]
    ww = sum(1 for x in off if x)
    wrong = ww + st.get("gotrev", 0) + st.get("refrev", 0)
    n = len(res)
    g = sorted(x for x in gas if x)
    out = {"n": n, "status": dict(st), "wrong": wrong, "wrongPct": round(100 * wrong / n, 3) if n else 0,
           "valued": len(off), "wrongWei": ww, "wrongWeiPct": round(100 * ww / len(off), 3) if off else 0,
           "revertInRange": st.get("gotrev", 0), "valueOutOfRange": st.get("refrev", 0),
           "maxWei": max(off, default=0), "medianWei": statistics.median(off) if off else 0,
           "hist": {str(k): v for k, v in sorted(Counter(min(x, 10**6) for x in off).items())[:12]}}
    if g:
        out.update(gasMedian=g[len(g) // 2], gasP99=g[int(0.99 * (len(g) - 1))], gasMax=g[-1])
    return out


# ---- make sweep's second-stage pass ----------------------------------------

WIDE_TEST = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;
// GENERATED by scripts/sweep/wad.py for make sweep's second-stage pass; removed after the run.

import {Test} from "forge-std/Test.sol";
import {BlockulatorWadWide as B} from "./BlockulatorWadWide.sol";

contract SweepWadWide is Test {
    string constant DIR = "cache/sweep/";

    function f(bytes32 op, int256 a, int256 b) external view returns (int256 r, uint256 g) {
        uint256 g0;
        if (op == "noop") { g0 = gasleft(); r = a; g = gasleft(); }
%(disp)s
        require(g0 != 0, "op");
        g = g0 - g;
    }

    function runOne(string memory op) external {
        string memory j = vm.readFile(string.concat(DIR, "wad_", op, ".json"));
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = vm.keyExistsJson(j, ".b") ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, "wadwide_", op, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        (, uint256 base) = this.f("noop", 0, 0);
        uint256 n = a.length < %(n)d ? a.length : %(n)d;
        for (uint256 i; i < n; i++) {
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i]))) returns (int256 r, uint256 g) {
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
    }

%(runs)s
}
"""


def run_wide(want=None):
    """The first WIDE_N inputs of each function with a second stage, through
    a test-only BlockulatorWad whose fast-path test always fails (gen.py
    --lib wad --wide-lib), so every result is the second stage's; written to
    cache/sweep/wadwide_<function>.out. The generated files are removed."""
    names = [f for f in WIDE if want is None or f in want]
    if not names:
        return
    wd = ROOT / "test" / "sweep" / "wadwide"
    subprocess.run(["uv", "run", "scripts/fp127/gen.py", "--lib", "wad", "--wide-lib",
                    str(wd / "BlockulatorWadWide.sol")], cwd=ROOT, check=True)
    disp = "\n".join(f'        if (op == "{f}") {{ g0 = gasleft(); r = B.{f}(a{", b" if FUNCS[f][1] == 2 else ""}); g = gasleft(); }}'
                     for f in names)
    runs = "\n".join(f'    function test_{f}() public {{ this.runOne("{f}"); }}' for f in names)
    (wd / "SweepWadWide.t.sol").write_text(WIDE_TEST % {"disp": disp, "runs": runs, "n": WIDE_N})
    keep = bool(os.environ.get("SWEEP_KEEP"))   # leave the generated files, show forge's output
    try:
        subprocess.run(["forge", "test", "--match-path", "test/sweep/wadwide/SweepWadWide.t.sol"] + ([] if keep else ["-q"]),
                       cwd=ROOT, check=True)
    finally:
        if not keep:
            for p in wd.glob("*"):
                p.unlink()
            wd.rmdir()


def sweep_rows(pool, selected, fallback) -> list[dict]:
    """make sweep's WAD rows: every function on its inputs (with the count
    pass's fallback share), then the second-stage pass."""
    rows = []
    for f, (maths, nargs, kind, d) in FUNCS.items():
        if not selected(f) or not (D / f"wad_{f}.out").exists():
            continue
        res, gas = score_rows(pool, f"wad_{f}", f)
        rows.append({"lib": "wad", "op": f, "direction": DIRNAME[d], **summary(res, gas),
                     **fallback("wad", f, load(f"wad_{f}"))})
        print(json.dumps(rows[-1]), flush=True)
    for f in WIDE:
        if not selected(f) or not (D / f"wadwide_{f}.out").exists():
            continue
        res, gas = score_rows(pool, f"wadwide_{f}", f, inputs=f"wad_{f}")
        rows.append({"lib": "wad", "op": f, "stage": "second", "direction": DIRNAME[FUNCS[f][3]], **summary(res, gas)})
        print(json.dumps(rows[-1]), flush=True)
    return rows


def sweep_md(rows, pct) -> list[str]:
    """make sweep's WAD section of sweep.md."""
    md = ["",
          "## BlockulatorWad",
          "",
          "Every function and direction on `scripts/sweep/wad.py`'s inputs, against the exact value "
          "rounded in the stated direction (integers for mul, div, sqrt and cbrt; mpmath at 300 digits "
          "for the rest). *Wrong* is any result off by a wei, a revert where the value fits or a value "
          "where it does not. *Fallback* is the share of inputs whose fast path could not decide the "
          "last wei and ran the second stage. Competitors on the same inputs: `wad.md`.",
          "",
          "| function | direction | inputs | wrong | reverts (both) | gas median / p99 / max | fallback |",
          "|---|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        if r["lib"] == "wad" and "stage" not in r:
            md.append(f"| {r['op']} | {r['direction']} | {r['n']:,} | {r['wrong']:,} | {r['status'].get('bothrev', 0):,} | "
                      f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} | {pct(r)} |")
    md += ["",
           "### The second stage alone",
           "",
           f"The first {WIDE_N:,} inputs of each function with a second stage again, through a test-only "
           "copy of BlockulatorWad whose fast-path test always fails, so every result comes from the "
           "second stage at 2^-510 on the exact input.",
           "",
           "| function | direction | inputs | wrong | gas median / p99 / max |",
           "|---|---|---:|---:|---:|"]
    for r in rows:
        if r["lib"] == "wad" and r.get("stage"):
            md.append(f"| {r['op']} | {r['direction']} | {r['n']:,} | {r['wrong']:,} | "
                      f"{r.get('gasMedian', 0):,} / {r.get('gasP99', 0):,} / {r.get('gasMax', 0):,} |")
    return md


# ---- the bench -------------------------------------------------------------

BENCH = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;
// GENERATED by scripts/sweep/wad.py (make wad); removed after the run.

import {Test} from "forge-std/Test.sol";
import {BlockulatorWad as B} from "../../contracts/src/wad/BlockulatorWad.sol";
import {FixedPointMathLib as S} from "../../lib/solady/src/utils/FixedPointMathLib.sol";
import {SD59x18} from "../../lib/prb-math/src/SD59x18.sol";
import {UD60x18} from "../../lib/prb-math/src/UD60x18.sol";
import * as PS from "../../lib/prb-math/src/sd59x18/Math.sol";
import * as PU from "../../lib/prb-math/src/ud60x18/Math.sol";

/// Every library's WAD function on the same inputs, one result and its gas
/// per line, as Sweep.t.sol records BlockulatorWad.
contract WadBench is Test {
    string constant DIR = "cache/sweep/";

    function f(bytes32 op, int256 a, int256 b) external view returns (int256 r, uint256 g) {
        uint256 g0;
        if (op == "noop") { g0 = gasleft(); r = a; g = gasleft(); }
%(disp)s
        require(g0 != 0, "op");
        g = g0 - g;
    }

    function runOne(string memory inp, string memory op) external {
        string memory path = string.concat(DIR, inp, ".json");
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = vm.keyExistsJson(j, ".b") ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, "wadbench_", op, "_", inp, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        (, uint256 base) = this.f("noop", 0, 0);
        for (uint256 i; i < a.length; i++) {
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i]))) returns (int256 r, uint256 g) {
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
    }

%(runs)s
}
"""


def bench_cells():
    """(op key, library, our function, expression) for every bench cell."""
    cells = []
    for f, (maths, nargs, kind, _) in FUNCS.items():
        args = "uint256(a), uint256(b)" if kind == "u" and nargs == 2 else "a, b" if nargs == 2 else "uint256(a)" if kind == "u" else "a"
        call = f"B.{f}({args})"
        cells.append((f"b_{f}", "blockulator", f, f"int256({call})" if kind == "u" else call))
        for lib, calls in COMP.items():
            if f in calls:
                expr = calls[f][0]
                cells.append((f"{lib[0]}_{f}", lib, f, f"int256({expr})" if kind == "u" else expr))
    return cells


def run_bench():
    cells = bench_cells()
    disp = "\n".join(f'        if (op == "{k}") {{ g0 = gasleft(); r = {e}; g = gasleft(); }}' for k, _, _, e in cells)
    runs = []
    for k, _, f, _ in cells:
        for inp in (f"wad_{f}", f"wadtyp_{f}"):
            runs.append(f'    function test_{k}_{"t" if inp.startswith("wadtyp") else "s"}() public {{ this.runOne("{inp}", "{k}"); }}')
    path = ROOT / "test" / "wad" / "WadBench.t.sol"
    path.write_text(BENCH % {"disp": disp, "runs": "\n".join(runs)})
    try:
        subprocess.run(["forge", "test", "--match-path", "test/wad/WadBench.t.sol", "-q"], cwd=ROOT, check=True)
    finally:
        path.unlink()


def versions() -> dict:
    def sub(p):
        try:
            return subprocess.check_output(["git", "-C", str(ROOT / p), "describe", "--tags", "--always"], text=True).strip()
        except subprocess.CalledProcessError:
            return "?"
    head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    return {"blockulator": head, "solady": sub("lib/solady"), "prb-math": sub("lib/prb-math")}


SIZE_SRC = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;
// GENERATED by scripts/sweep/wad.py (make wad) to measure inline sizes; removed after the build.

import {BlockulatorWad as B} from "../../contracts/src/wad/BlockulatorWad.sol";
import {FixedPointMathLib as S} from "../../lib/solady/src/utils/FixedPointMathLib.sol";
import {SD59x18} from "../../lib/prb-math/src/SD59x18.sol";
import {UD60x18} from "../../lib/prb-math/src/UD60x18.sol";
import * as PS from "../../lib/prb-math/src/sd59x18/Math.sol";
import * as PU from "../../lib/prb-math/src/ud60x18/Math.sol";

contract WadSizeBase {
    function f(int256 a, int256 b) external pure returns (int256 r) { r = a ^ b; }
}
%s
"""


def sizes() -> dict[str, int]:
    """Bytes each function adds to a contract that calls it once: the deployed
    size of a one-function contract less that of the same contract returning
    a ^ b (default profile: solc 0.8.38, optimizer 200 runs, evm osaka)."""
    cells = bench_cells()
    body = "\n".join(f"contract WadSize_{k} {{\n    function f(int256 a, int256 b) external pure returns (int256 r) {{ r = {e}; }}\n}}"
                     for k, _, _, e in cells)
    path = ROOT / "test" / "wad" / "WadSize.sol"
    path.write_text(SIZE_SRC % body)
    try:
        subprocess.run(["forge", "build", str(path.relative_to(ROOT))], cwd=ROOT, check=True, capture_output=True)
        def size(name):
            art = json.loads((ROOT / "out" / "WadSize.sol" / f"{name}.json").read_text())
            return (len(art["deployedBytecode"]["object"]) - 2) // 2
        base = size("WadSizeBase")
        return {k: size(f"WadSize_{k}") - base for k, *_ in cells}
    finally:
        path.unlink()


def score(with_sizes=True):
    rows = []
    sz = sizes() if with_sizes else {}
    with mpc.Pool() as pool:
        for k, lib, f, _ in bench_cells():
            direction = FUNCS[f][3] if lib == "blockulator" else COMP[lib][f][1]
            res, gas = score_rows(pool, f"wadbench_{k}_wad_{f}", f, direction, inputs=f"wad_{f}")
            _, tgas = score_rows(pool, f"wadbench_{k}_wadtyp_{f}", f, direction, inputs=f"wadtyp_{f}")
            tg = sorted(x for x in tgas if x)
            row = {"lib": lib, "function": f, "call": COMP[lib][f][0] if lib in COMP else f"BlockulatorWad.{f}",
                   "direction": DIRNAME[direction], **summary(res, gas),
                   "gasTypical": tg[len(tg) // 2] if tg else None, "bytes": sz.get(k)}
            rows.append(row)
            print(json.dumps(row), flush=True)
    doc = {"_doc": __doc__.strip(), "seed": SEED, "versions": versions(), "libraries": LABEL, "rows": rows}
    (OUT / "wad.json").write_text(json.dumps(doc, indent=1) + "\n")
    (OUT / "wad.md").write_text(render(doc))
    print("wrote docs/benchmarks/wad.{json,md}")


def render(doc) -> str:
    rows = doc["rows"]
    by = {(r["lib"], r["function"]): r for r in rows}
    ours = [r for r in rows if r["lib"] == "blockulator"]
    n_ours = sum(r["n"] for r in ours)
    w_ours = sum(r["wrong"] for r in ours)
    md = ["# WAD maths to the last wei",
          "",
          "Generated by `make wad` (`scripts/sweep/wad.py`) from seeded inputs: each function's domain "
          "(log-uniform magnitudes from one wei up), the inputs whose exact value lies near a wei boundary, "
          "the exact cases and the ends. Truth is the exact real value (integers for mul, div, sqrt and "
          "cbrt; mpmath at 300 digits for the rest), rounded in each library's own direction. Data: "
          "`wad.json`; BlockulatorWad's own rows, with the forced second-stage pass, are in `sweep.md`.",
          "",
          f"Versions: BlockulatorWad at {doc['versions']['blockulator']}, Solady {doc['versions']['solady']}, "
          f"PRBMath {doc['versions']['prb-math']}.",
          "",
          f"BlockulatorWad: **{w_ours:,} wrong of {n_ours:,}** results across {len(ours)} functions and directions.",
          "",
          "## Wei error",
          "",
          "*Wrong wei*: results off by at least one wei, of the inputs where the library and the exact "
          "value both give one; *max / median*: wei off over those inputs. *Reverts in range*: reverts where "
          "the exact result fits the word (a narrower domain, as Solady's mulWad reverting once x y passes "
          "2^256); *value out of range*: a value where there is none.",
          "",
          "| function | direction | BlockulatorWad | Solady wrong wei | max / median | reverts in range | PRBMath wrong wei | max / median | reverts in range |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|"]

    def cells(r):
        if not r:
            return ["—", "—", "—"]
        rev = r["revertInRange"] + r["valueOutOfRange"]
        return [f"{r['wrongWei']:,} of {r['valued']:,} ({r['wrongWeiPct']:.1f}%)",
                f"{fmt(r['maxWei'])} / {fmt(r['medianWei'])}",
                f"{rev:,}" if rev else "0"]
    for f in FUNCS:
        b = by[("blockulator", f)]
        md.append(f"| {f} | {b['direction']} | {b['wrong']:,} wrong of {b['n']:,} | "
                  + " | ".join(cells(by.get(("solady", f))) + cells(by.get(("prb", f)))) + " |")
    md += ["",
           "Each library in its own direction: Solady floor, and toward zero for sMulWad, sDivWad and "
           "lambertW0Wad (its sdiv); PRBMath floor for UD60x18, exp and pow, toward zero for SD59x18's mul, "
           "div and logs (log2 of x < 1 is minus log2(1/x) truncated). A dash: the library has no such "
           "function (Solady has no WAD log2 or log10 and no Up for exp, ln, pow or Lambert W; PRBMath no "
           "Up, no cbrt and no Lambert W).",
           "",
           "## Gas and size",
           "",
           "Each library's internal call alone. *Typical*: the median over 200 everyday inputs that take no "
           "shortcut (exp of -10..10, ln and the logs of 0.001..1,000, pow of 0.5..2 to -3..3, products and "
           "quotients of amounts up to 10^9 tokens); *swept*: median / 99th percentile over the swept inputs, "
           "BlockulatorWad's second stage included where it ran. *Bytes*: what one call adds to a contract.",
           "",
           "| function | BlockulatorWad typical | swept median / p99 | bytes | Solady typical | bytes | PRBMath typical | bytes |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for f in FUNCS:
        b = by[("blockulator", f)]
        s, p = by.get(("solady", f)), by.get(("prb", f))
        md.append(f"| {f} | {fmt(b.get('gasTypical'))} | {fmt(b.get('gasMedian'))} / {fmt(b.get('gasP99'))} | {fmt(b.get('bytes'))} | "
                  f"{fmt(s.get('gasTypical')) if s else '—'} | {fmt(s.get('bytes')) if s else '—'} | "
                  f"{fmt(p.get('gasTypical')) if p else '—'} | {fmt(p.get('bytes')) if p else '—'} |")
    return "\n".join(md) + "\n"


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float) and not v.is_integer():
        return f"{v:,.1f}"
    v = int(v)
    return f"{v:.3g}" if v >= 10**9 else f"{v:,}"


def main():
    if sys.argv[1:] != ["score"]:
        gen()
        run_bench()
    score(with_sizes=sys.argv[1:] != ["score"])


if __name__ == "__main__":
    main()

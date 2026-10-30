#!/usr/bin/env python3
"""Worst-case correct digits for the exchange rows of talk/scenes/data/tiers.json.

    uv run --with mpmath python scripts/tiers/measure_exchanges.py            # every row, prints the table,
                                                                              #   writes talk/scenes/data/tiers-worst-exchanges.json
    uv run --with mpmath python scripts/tiers/measure_exchanges.py ROW [ROW]  # some rows only (no JSON written)

The rule (the user's, 2026-10-30): every row is graded by ONE number, its
correct digits on its WORST input. For each row the function's integer
arithmetic is transcribed as the pinned source does it (Python ints, the
constants parsed from the fetched file, the same shifts, floors and ceilings)
and its result is compared with the exact value of the formula the protocol
itself documents, computed with mpmath at 120 digits. Two numbers per row:

    worst_digits = min over the domain of -log10(|returned - exact| / |exact|)
    worst_units  = max over the domain of |returned - exact|, in units of the
                   result's last place (its integer unit)

A returned value equal to the exact one has every digit of the integer correct;
it counts as len(str(value)) digits. Swap rows count digits only on trades of
at least 10^6 units in and out (a 3-wei trade trivially has few digits); their
worst_units covers the same trades.

Sources are fetched at their pinned commits (raw.githubusercontent.com) into
~/.cache/blockulator/tiers-src and checked against the sha256 below. Curve's
files are "all rights reserved": nothing of them is copied here. Their
functions are fetched and translated mechanically (vyper_module below) at run
time and executed; the repo holds only the translator.

The grade input (the coordinator, 2026-10-30) is DIGITS LOST:
digits_lost = log10(max(worst_units, 1)), so a correctly rounded result
(<= 0.5 unit, or < 1 unit in the stated direction) loses 0. No tier is
assigned here; the thresholds are set from these numbers.

Heavy runs: TIERS_WORKERS (default min(64, cores)) and TIERS_SCALE (default 1;
below 1 shrinks every random search for a quick look).
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import random
import re
import sys
import types
import urllib.request
from multiprocessing import Pool
from pathlib import Path

import mpmath as mp

mp.mp.dps = 120
ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "talk" / "scenes" / "data" / "tiers-worst-exchanges.json"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "blockulator" / "tiers-src"
WORKERS = int(os.environ.get("TIERS_WORKERS", min(64, os.cpu_count() or 1)))
SCALE = float(os.environ.get("TIERS_SCALE", "1"))  # < 1 for a quick look; the recorded run uses 1
SEED = 20261030

# NORMAL inputs (the user, 2026-10-30: "let's use normal inputs"): each row's number is its worst case here;
# the function's whole documented domain is kept under domain_worst.
N_LO, N_HI = 10 ** 6, 10 ** 27        # swap amounts and reserves, in token units
P_LO, P_HI = 1e-6, 1e6                # prices, raw units of one token per raw unit of the other
NORMAL_TICK = 138_163                 # |tick| of 1.0001^tick in [1e-6, 1e6] (the coordinator's figure)
TWAP_LO, TWAP_HI = 60, 86_400         # TWAP windows, seconds
# 2026-10-30, the user via the coordinator: swap amounts and every reserve at least ONE WHOLE TOKEN and at most
# 1e9 tokens; token prices 1e-6..1e6; a swap's error is counted in the smallest unit of the more valuable token.
DECS = (6, 8, 18)                     # token decimals sampled (USDC-, WBTC-, ETH-like)
T_LO, T_HI = 1.0, 1e9                 # whole tokens
HELD = (25, 14, 10)                   # held_floor thresholds (digits the format holds at the value)

# ---------------------------------------------------------------- pinned sources
GH = "https://raw.githubusercontent.com/"
SRC = {
    # Uniswap v2-core @ 6a9e7c97 (the K check) and v2-periphery @ 0335e8f7 (getAmountOut, the router's quote)
    "v2pair": ("Uniswap/v2-core/6a9e7c97860676e0992f22a49665760444c1cdf5/contracts/UniswapV2Pair.sol",
               "43a5421b31415868367b62bfa161ca10bcee03778873faad905f5a3e2cce9cbd"),
    "v2lib": ("Uniswap/v2-periphery/0335e8f7e1bd1e8d8329fd300aea2ef2f36dd19f/contracts/libraries/UniswapV2Library.sol",
              "4f83e9334f833568fa47b36e9ceca435f6c2962760a0596b043c4e538d0fd9f2"),
    # Uniswap v3-core @ 5ea68a77 (v4-core @ bea7f6d1 carries the same constants and roundings)
    "v3sqrt": ("Uniswap/v3-core/5ea68a77cb541c6b3812df783be71ba8c081e25f/contracts/libraries/SqrtPriceMath.sol",
               "ddd62e3a94346248677f30f1ab009ef015e71e4b8696dcca890eeabc9dc6c149"),
    "v3swap": ("Uniswap/v3-core/5ea68a77cb541c6b3812df783be71ba8c081e25f/contracts/libraries/SwapMath.sol",
               "d6cb9a153be4ea9fb2377ef88641ef7979b5cee6933162f1b732d0289e26e1b6"),
    "v3tick": ("Uniswap/v3-core/5ea68a77cb541c6b3812df783be71ba8c081e25f/contracts/libraries/TickMath.sol",
               "e68d3c6c8c847d16c287c1f17f684d11cf0f6267a8d8dc29e81656bccf68f062"),
    "v4tick": ("Uniswap/v4-core/bea7f6d1c11cd5dc4f0d5151ffa37a1c239feee6/src/libraries/TickMath.sol",
               "272d4f6d3ff9ae33596ebcdb84a71a3c2d4542ae8fb5c88ddf1aca8043f5d06b"),
    # Uniswap v3-periphery @ 24ccf014
    "oracle": ("Uniswap/v3-periphery/24ccf014fe7f81d74a14c1689d6fdf123f280e45/contracts/libraries/OracleLibrary.sol",
               "3e4967a8d77a63127219d22852199551b614f12a16d66c0c415329b8c2cbe5a0"),
    # Curve 3pool @ 574f4402, stableswap-ng @ 3332cd44, twocrypto-ng @ 5cbe5589 (all rights reserved: fetched, never copied)
    "3pool": ("curvefi/curve-contract/574f44027d089de0eac765f5a74ea5ae96aba968/contracts/pools/3pool/StableSwap3Pool.vy",
              "03e0bf29ae2fe945a3629b8085062da8f9d9d25957e86001dfc3df68c895f9dc"),
    "ng": ("curvefi/stableswap-ng/3332cd44656ec64b3c048885e1dd71955254b262/contracts/main/CurveStableSwapNG.vy",
           "dfe8f8a4dda288c41c630ea4be9bb0e5d61244c50dfdeaf1981a098b55ee12ab"),
    "twomath": ("curvefi/twocrypto-ng/5cbe558902402e8fcb331463089db65fc56c11f9/contracts/main/TwocryptoMath.vy",
                "35443ba825f9dafcd7ce86e1d424c210d5963494c69eca6938c3dd5904f37d7d"),
    "twoconst": ("curvefi/twocrypto-ng/5cbe558902402e8fcb331463089db65fc56c11f9/contracts/main/constants.vy",
                 "80080f672c1b80d9e56ae59611548771f966c84a008e462bbe9dd75fbe6bcf8d"),
    # Aerodrome @ 1ba30815
    "aero": ("aerodrome-finance/contracts/1ba30815bba620f7e9faa34769ffd00c214c9b82/contracts/Pool.sol",
             "348d3c313dbbb9a2d0598480075bf91e77ceb2d774aeddbe229c9f551186c8bf"),
    # Trader Joe Liquidity Book (lfj-gg/joe-v2) @ 067c6ccf
    "lbprice": ("lfj-gg/joe-v2/067c6ccf5b8ff1526d03fa3e4c65ec45d01c1f73/src/libraries/PriceHelper.sol",
                "15cd510359cf8d9a6db4ad6b9a3682a66d8b65a7d319c38734794cc073d00965"),
    "lbpow": ("lfj-gg/joe-v2/067c6ccf5b8ff1526d03fa3e4c65ec45d01c1f73/src/libraries/math/Uint128x128Math.sol",
              "c092f230ef4b13b95ac115701015ecc8eb9be08ab72091eebaedb23768fc2161"),
    "lbbin": ("lfj-gg/joe-v2/067c6ccf5b8ff1526d03fa3e4c65ec45d01c1f73/src/libraries/BinHelper.sol",
              "5ab002bc1745636706d0f0da4b6036598470fac5b0fc524646ba27c7ff6f1998"),
    "lbfee": ("lfj-gg/joe-v2/067c6ccf5b8ff1526d03fa3e4c65ec45d01c1f73/src/libraries/FeeHelper.sol",
              "c16b77a6f5821ffe4f67c37dce57a02910d1a5d0c5c11d3024e4e9899c7ac54d"),
    # Pendle core v2 @ 87685c89
    "pendle_mmc": ("pendle-finance/pendle-core-v2-public/87685c89d05087535e9b9647eeda0e3d297d1f06/contracts/core/Market/MarketMathCore.sol",
                   "34dc6ecf3aadedfb700d7d88302b17a9eecd11631bbb9b4c6303246a84e9b3a7"),
    "pendle_lem": ("pendle-finance/pendle-core-v2-public/87685c89d05087535e9b9647eeda0e3d297d1f06/contracts/core/libraries/math/LogExpMath.sol",
                   "094a3114366a11375096715e3edf2885321b99082d08e7de6dfb82bdcbde5649"),
    # GMX synthetics @ a85ea349 and the prb-math it pins (package.json "prb-math": "2.4.3", tag v2.4.3 = commit 8cb5b772)
    "gmx_prec": ("gmx-io/gmx-synthetics/a85ea3491c19c93bb4b5a002d9b358fb769b7849/contracts/utils/Precision.sol",
                 "8713db02a257238101fc62cc682a8f8061fba25951216863576afbbd00f34808"),
    "prb": ("PaulRBerg/prb-math/8cb5b772eadc31ab48fa0d07f4dc16b99cfbcc1f/contracts/PRBMath.sol",
            "3ef522031838f10557feebf5cfd49cb2d0c15f42038b648bc33a7f3ebb3d6500"),
    "prbud": ("PaulRBerg/prb-math/8cb5b772eadc31ab48fa0d07f4dc16b99cfbcc1f/contracts/PRBMathUD60x18.sol",
              "f433763fb95aea1fec7bea4829262c4d95c73acb21ef5d926c9e3aba89e544ca"),
    # Algebra V1 (tag v1.0.0) @ 60d71de0
    "algebra_fee": ("cryptoalgebra/Algebra/60d71de06b75518b6bc9e1d6909fcb7c0c9e5cd7/src/core/contracts/libraries/AdaptiveFee.sol",
                    "4a03ad5d8c557283bca29181bdf30f2d9edafd0ca9413d309f25e1c6b416c160"),
    "algebra_factory": ("cryptoalgebra/Algebra/60d71de06b75518b6bc9e1d6909fcb7c0c9e5cd7/src/core/contracts/AlgebraFactory.sol",
                        "579b4fbf7e3aad220460a8f99ad6dda9769e89ad8756543a58aa587c0d182a2d"),
    # Maverick v2-common @ d91e8714
    "mav_tick": ("maverickprotocol/v2-common/d91e8714a20b65913166d6b6608590ff822c3f06/contracts/libraries/TickMath.sol",
                 "e461f441c8718e55a0ff5a89a9c2efe383c68ab53801de9a9f123453a1492c2d"),
    "mav_const": ("maverickprotocol/v2-common/d91e8714a20b65913166d6b6608590ff822c3f06/contracts/libraries/Constants.sol",
                  "ab53f5d359a9c93afa12de1dde0d23a2475cd7470d34816ad25f175e552357b5"),
}


def src(key: str) -> str:
    path, digest = SRC[key]
    f = CACHE / digest
    if not f.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(GH + path, timeout=60) as r:
            data = r.read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit(f"{key}: sha256 mismatch for {path}")
        f.write_bytes(data)
    return f.read_text()


def hexes_in(text: str, pattern: str) -> list[int]:
    return [int(h, 16) for h in re.findall(pattern, text)]


# ---------------------------------------------------------------- EVM integer helpers
U256 = 1 << 256
LOG10_2 = math.log10(2)
MAXU = U256 - 1


class Revert(Exception):
    pass


def mul_div(a, b, d):  # FullMath.mulDiv / Uint256x256Math: exact floor(a*b/d) with a 512-bit product
    if d == 0:
        raise Revert("div0")
    r = a * b // d
    if r >= U256:
        raise Revert("mulDiv overflow")
    return r


def mul_div_up(a, b, d):
    r = mul_div(a, b, d)
    if (a * b) % d:
        r += 1
        if r >= U256:
            raise Revert("mulDiv overflow")
    return r


def div_up(a, b):  # UnsafeMath.divRoundingUp
    return a // b + (1 if a % b else 0)


# ---------------------------------------------------------------- the measure
FULL = "exact (every digit of the integer)"


class Worst:
    """Tracks min digits and max units, with the inputs that give them."""

    def __init__(self):
        self.d = math.inf
        self.d_in = None
        self.u = 0.0
        self.u_in = None
        self.n = 0
        self.n_digits = 0
        self.signs = set()
        self.reverts = 0
        self.revert_in = None
        self.note = {}
        self.uc = 0.0  # swap rows: error in units of the coarser of the two tokens' last places
        self.uc_in = None
        self.held = {H: (math.inf, None) for H in HELD}  # min digits where log10|exact| >= H
        self.s18 = (-1.0, None, None)  # (short18, input, format digits there)

    def held_update(self, cap, d, inp, exact_hit=False, cap_counted=None):
        """cap = log10 |exact| in the result's own unit (held_floor); cap_counted = the same in the unit errors are
        counted in (short18; a swap's more valuable token), default cap; d = digits held."""
        for H in HELD:
            if cap >= H and d < self.held[H][0]:
                self.held[H] = (d, inp)
        f = cap if cap_counted is None else cap_counted
        short = 0.0 if exact_hit else max(0.0, min(f, 18.0) - d)
        if short > self.s18[0]:
            self.s18 = (short, inp, f)

    def add(self, ret: int, exact, inp, count_digits=True, other=None):
        self.n += 1
        err = mp.mpf(ret) - exact
        a = abs(err)
        u = float(a)
        if a < 1 and u >= 1.0:  # keep "below one unit" visible after the float conversion
            u = math.nextafter(1.0, 0.0)
        if err > 0:
            self.signs.add("+")
        elif err < 0:
            self.signs.add("-")
        if u > self.u:
            self.u, self.u_in = u, inp
        if other is not None:
            uc = float(a / max(mp.mpf(1), abs(exact) / other))
            if a < 1 and uc >= 1.0:
                uc = math.nextafter(1.0, 0.0)
            if uc > self.uc:
                self.uc, self.uc_in = uc, inp
        if count_digits:
            self.n_digits += 1
            d = float(len(str(abs(ret)))) if a == 0 else float(-mp.log10(a / abs(exact)))
            if d < self.d:
                self.d, self.d_in = d, inp
            if exact != 0:
                # format digits in the counted unit: for a swap, the more valuable token's smallest unit,
                # i.e. |exact| / max(1, |exact|/other) = min(|exact|, other)
                mag = abs(exact) if other is None else min(abs(exact), mp.mpf(other))
                self.held_update(float(mp.log10(abs(exact))), d, inp, exact_hit=(a == 0), cap_counted=float(mp.log10(mag)))
        return err

    def revert(self, inp, why):
        self.reverts += 1
        self.why = getattr(self, "why", {})
        self.why[why] = self.why.get(why, 0) + 1
        self.why_in = getattr(self, "why_in", {})
        self.why_in.setdefault(why, inp)
        if self.revert_in is None:
            self.revert_in = f"{inp}: {why}"

    def merge(self, o: "Worst"):
        self.n += o.n
        self.n_digits += o.n_digits
        self.signs |= o.signs
        self.reverts += o.reverts
        self.why = getattr(self, "why", {})
        for k, v in getattr(o, "why", {}).items():
            self.why[k] = self.why.get(k, 0) + v
        self.why_in = getattr(self, "why_in", {})
        for k, v in getattr(o, "why_in", {}).items():
            self.why_in.setdefault(k, v)
        if self.revert_in is None:
            self.revert_in = o.revert_in
        if o.d < self.d:
            self.d, self.d_in = o.d, o.d_in
        if o.u > self.u:
            self.u, self.u_in = o.u, o.u_in
        if o.uc > self.uc:
            self.uc, self.uc_in = o.uc, o.uc_in
        for H in HELD:
            if o.held[H][0] < self.held[H][0]:
                self.held[H] = o.held[H]
        if o.s18[0] > self.s18[0]:
            self.s18 = o.s18
        for k, v in o.note.items():
            if k not in self.note:
                self.note[k] = v
            else:
                a, b = self.note[k], v
                self.note[k] = (min(a[0], b[0]), a[1] if a[0] <= b[0] else b[1])
        return self

    def bucket_u(self, key, u, inp):
        """Max units per named sub-domain (stored negated so merge's min keeps the max)."""
        self.bucket("units: " + key, -float(u), inp)

    def bucket(self, key, d, inp):
        """Min digits per named sub-domain (for the notes)."""
        cur = self.note.get(key)
        if cur is None or d < cur[0]:
            self.note[key] = (d, inp)


def parallel(fn, n_total: int, *extra) -> Worst:
    """Run fn(seed, n, *extra) on WORKERS processes; each returns a Worst."""
    n_total = max(1, int(n_total * SCALE))
    chunks = WORKERS * 2
    per = -(-n_total // chunks)
    args = [(SEED + 7919 * k + (1 if extra and extra[0] else 0), per, *extra) for k in range(chunks)]
    with Pool(WORKERS) as p:
        parts = p.starmap(fn, args)
    w = Worst()
    for part in parts:
        w.merge(part)
    return w


def loguni(rng: random.Random, lo: int, hi: int) -> int:
    """Integer log-uniform in [lo, hi]."""
    if hi <= lo:
        return lo
    x = math.exp(rng.uniform(math.log(lo), math.log(hi)))
    v = int(x)
    # sprinkle low bits so values are not float-shaped
    if v > 1 << 52:
        v ^= rng.getrandbits(v.bit_length() - 52)
    return min(max(v, lo), hi)


def logtok(rng, lo=T_LO, hi=T_HI):
    """A token amount log-uniform in [lo, hi] whole tokens (float)."""
    return math.exp(rng.uniform(math.log(lo), math.log(hi)))


def units(tokens, dec, rng=None):
    """Whole-token amount to raw units, with random low digits."""
    v = int(mp.mpf(tokens) * 10 ** dec)
    if rng is not None and dec > 0:
        v = (v // 10 ** min(dec, 6)) * 10 ** min(dec, 6) + rng.randrange(10 ** min(dec, 6))
    return max(v, 10 ** dec)


def logprice(rng, lo=P_LO, hi=P_HI):
    """A price log-uniform in [lo, hi]."""
    return math.exp(rng.uniform(math.log(lo), math.log(hi)))


def mpf_exact_digits(ret, exact):
    err = abs(mp.mpf(ret) - exact)
    return float(len(str(abs(ret)))) if err == 0 else float(-mp.log10(err / abs(exact)))


# ================================================================ 1. Uniswap v2 swap
def v2_get_amount_out(amount_in, r_in, r_out):
    # UniswapV2Library.getAmountOut (v2-periphery @ 0335e8f7, L43-50), SafeMath = checked uint256
    if amount_in <= 0 or r_in <= 0 or r_out <= 0:
        raise Revert("INSUFFICIENT")
    a = amount_in * 997
    num = a * r_out
    den = r_in * 1000 + a
    if num >= U256 or den >= U256:
        raise Revert("overflow")
    return num // den


def v2_k_ok(r0, r1, amount_in, out):
    # UniswapV2Pair.swap (v2-core @ 6a9e7c97, L180-182) for token0 in, token1 out
    b0, b1 = r0 + amount_in, r1 - out
    b0a = b0 * 1000 - amount_in * 3
    b1a = b1 * 1000 - 0
    return b0a * b1a >= r0 * r1 * 1000 ** 2


def _v2_chunk(seed, n, normal):
    rng = random.Random(seed)
    w = Worst()
    R = (1 << 112) - 1
    kept = 0
    while kept < n:
        if normal:
            din, dout = rng.choice(DECS), rng.choice(DECS)
            tin, p = logtok(rng), logprice(rng)
            if not T_LO <= tin * p <= T_HI:
                continue
            r_in, r_out = units(tin, din, rng), units(tin * p, dout, rng)
            a = units(logtok(rng), din, rng)
        else:
            r_in, r_out = loguni(rng, 10 ** 6, R), loguni(rng, 10 ** 6, R)
            a = loguni(rng, 10 ** 6, R - r_in)
        out = v2_get_amount_out(a, r_in, r_out)
        num, den = a * 997 * r_out, r_in * 1000 + a * 997
        exact = mp.mpf(num) / den
        if exact < (1 if normal else 10 ** 6):
            continue
        kept += 1
        if kept < 2000:  # the pair's own check: out passes, out + 1 does not
            assert v2_k_ok(r_in, r_out, a, out) and (out + 1 > r_out or not v2_k_ok(r_in, r_out, a, out + 1))
        w.add(out, exact, f"reserveIn={r_in}, reserveOut={r_out}, amountIn={a}", other=a)
    return w


def row_uniswap_v2():
    src("v2lib"), src("v2pair")
    wn = parallel(_v2_chunk, 200_000, True)
    wd = parallel(_v2_chunk, 100_000, False)
    R = (1 << 112) - 1
    vals = sorted({10 ** 6, R} | {1 << k for k in range(20, 112)})
    for r_in in vals:
        for r_out in vals[::7]:
            for a in (10 ** 6, r_in, R - r_in):
                if a < 10 ** 6 or r_in + a > R:
                    continue
                out = v2_get_amount_out(a, r_in, r_out)
                exact = mp.mpf(a * 997 * r_out) / (r_in * 1000 + a * 997)
                if exact >= 10 ** 6:
                    wd.add(out, exact, f"reserveIn={r_in}, reserveOut={r_out}, amountIn={a}", other=a)
    # boundary search: exact output just above one whole token of an 18-decimal out token
    rng = random.Random(SEED)
    for _ in range(20000):
        r_in = units(logtok(rng), 18, rng)
        r_out = units(logtok(rng, 2.0), 18, rng)
        t = 10 ** 18 + rng.random()
        a = int(1000 * r_in * t / (997 * (r_out - t))) + 1
        if not 10 ** 18 <= a <= 10 ** 27:
            continue
        out = v2_get_amount_out(a, r_in, r_out)
        exact = mp.mpf(a * 997 * r_out) / (r_in * 1000 + a * 997)
        if exact >= 10 ** 6:
            for w in (wn, wd):
                w.add(out, exact, f"reserveIn={r_in}, reserveOut={r_out}, amountIn={a}", other=a)
    for w in (wn, wd):
        assert w.signs <= {"-"} and w.u < 1, (w.signs, w.u, w.u_in)
    return dict(
        w=wn, wd=wd,
        normal_range="reserves and amountIn 1..1e9 whole tokens (decimals 6, 8 or 18 each), price (reserveOut/reserveIn in tokens) 1e-6..1e6; error in the smallest unit of the more valuable token",
        truth="amountIn·(997/1000)·reserveOut / (reserveIn + amountIn·997/1000): the x·y = k output with the 0.3% fee on the input, exact rational",
        search="normal: 200,000 random trades plus 20,000 solved for an exact output just above 1e6; domain: 100,000 random (reserves to 2^112−1) and every power of two 2^20..2^111 as reserves and amounts; the first 2,000 of each run checked against the pair's K inequality (out passes, out+1 fails)",
        extra="getAmountIn (the exact-output quote) returns floor(exact)+1: 1 unit above the exact input when the division is exact, always up.",
    )


# ================================================================ 2. Uniswap v3/v4 swap step
Q96 = 1 << 96
MIN_SQRT_RATIO = 4295128739
MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342


def _u160(x):
    if x >= 1 << 160:
        raise Revert("toUint160")
    return x


def next_sqrt_from_amount0_up(sqrtP, L, amount, add):
    # SqrtPriceMath.getNextSqrtPriceFromAmount0RoundingUp (solidity 0.7: amount * sqrtP wraps mod 2^256)
    if amount == 0:
        return sqrtP
    num1 = L << 96
    if add:
        product = (amount * sqrtP) % U256
        if product // amount == sqrtP:
            den = num1 + product
            if den < U256 and den >= num1:
                return mul_div_up(num1, sqrtP, den)
        return div_up(num1, num1 // sqrtP + amount)
    product = (amount * sqrtP) % U256
    if not (product // amount == sqrtP and num1 > product):
        raise Revert("amount0 sub")
    return _u160(mul_div_up(num1, sqrtP, num1 - product))


def next_sqrt_from_amount1_down(sqrtP, L, amount, add):
    if add:
        q = (amount << 96) // L if amount <= (1 << 160) - 1 else mul_div(amount, Q96, L)
        return _u160(sqrtP + q)
    q = div_up(amount << 96, L) if amount <= (1 << 160) - 1 else mul_div_up(amount, Q96, L)
    if not sqrtP > q:
        raise Revert("amount1 sub")
    return sqrtP - q


def amount0_delta(a, b, L, up):
    if a > b:
        a, b = b, a
    num1, num2 = L << 96, b - a
    if a == 0:
        raise Revert("a=0")
    return div_up(mul_div_up(num1, num2, b), a) if up else mul_div(num1, num2, b) // a


def amount1_delta(a, b, L, up):
    if a > b:
        a, b = b, a
    return mul_div_up(L, b - a, Q96) if up else mul_div(L, b - a, Q96)


def compute_swap_step(cur, target, L, remaining, fee):
    # SwapMath.computeSwapStep (v3-core @ 5ea68a77, L21-97); v4-core @ bea7f6d1 has the same roundings
    zfo = cur >= target
    exact_in = remaining >= 0
    amount_in = amount_out = 0
    if exact_in:
        less_fee = mul_div(remaining, 10 ** 6 - fee, 10 ** 6)
        amount_in = amount0_delta(target, cur, L, True) if zfo else amount1_delta(cur, target, L, True)
        if less_fee >= amount_in:
            nxt = target
        else:
            nxt = next_sqrt_from_amount0_up(cur, L, less_fee, True) if zfo else next_sqrt_from_amount1_down(cur, L, less_fee, True)
    else:
        amount_out = amount1_delta(target, cur, L, False) if zfo else amount0_delta(cur, target, L, False)
        if -remaining >= amount_out:
            nxt = target
        else:
            nxt = next_sqrt_from_amount1_down(cur, L, -remaining, False) if zfo else next_sqrt_from_amount0_up(cur, L, -remaining, False)
    mx = target == nxt
    if zfo:
        amount_in = amount_in if (mx and exact_in) else amount0_delta(nxt, cur, L, True)
        amount_out = amount_out if (mx and not exact_in) else amount1_delta(nxt, cur, L, False)
    else:
        amount_in = amount_in if (mx and exact_in) else amount1_delta(cur, nxt, L, True)
        amount_out = amount_out if (mx and not exact_in) else amount0_delta(cur, nxt, L, False)
    if not exact_in and amount_out > -remaining:
        amount_out = -remaining
    if exact_in and nxt != target:
        fee_amt = remaining - amount_in
    else:
        fee_amt = mul_div_up(amount_in, fee, 10 ** 6 - fee)
    return nxt, amount_in, amount_out, fee_amt


MAX_LIQ_PER_TICK_1 = ((1 << 128) - 1) // ((887272 * 2) // 1 + 1)  # Tick.tickSpacingToMaxLiquidityPerTick(1)


def v3_case(cur, L, amount, fee, zfo, exact_in):
    """Returns (code result, exact, label) or None if the step reaches its target or reverts."""
    target = MIN_SQRT_RATIO if zfo else MAX_SQRT_RATIO - 1
    rem = amount if exact_in else -amount
    nxt, ain, aout, famt = compute_swap_step(cur, target, L, rem, fee)
    if nxt == target:
        return None
    P = mp.mpf(cur) / Q96
    Lm = mp.mpf(L)
    f = mp.mpf(fee) / 10 ** 6
    if exact_in:
        a = mp.mpf(amount) * (1 - f)
        if zfo:
            Q = Lm * P / (Lm + a * P)
            exact = Lm * (P - Q)
        else:
            Q = P + a / Lm
            exact = Lm * (1 / P - 1 / Q)
        return aout, exact, "exactIn"
    b = mp.mpf(amount)
    if zfo:
        Q = P - b / Lm
        if Q <= 0:
            return None
        exact = Lm * (1 / Q - 1 / P) / (1 - f)
    else:
        iq = 1 / P - b / Lm
        if iq <= 0:
            return None
        exact = Lm * (1 / iq - P) / (1 - f)
    return ain + famt, exact, "exactOut"


def _v3_chunk(seed, n, normal):
    rng = random.Random(seed)
    w = Worst()
    kept = 0
    while kept < n:
        if normal:
            d0, d1 = rng.choice(DECS), rng.choice(DECS)
            P = mp.mpf(logprice(rng)) * mp.mpf(10) ** (d1 - d0)  # raw token1 per raw token0
            cur = int(Q96 * mp.sqrt(P))
            if not MIN_SQRT_RATIO < cur < MAX_SQRT_RATIO - 1:
                continue
            x_tok = logtok(rng)  # virtual reserves x = L/sqrtP, y = L*sqrtP both 1..1e9 tokens
            L = int(x_tok * 10 ** d0 * mp.sqrt(P))
            y_tok = L * mp.sqrt(P) / 10 ** d1
            if not (L > 0 and T_LO <= y_tok <= T_HI):
                continue
            fee = rng.choice((100, 500, 3000, 10000, rng.randrange(0, 100_001)))
        else:
            cur = loguni(rng, MIN_SQRT_RATIO + 1, MAX_SQRT_RATIO - 2)
            L = loguni(rng, 1, MAX_LIQ_PER_TICK_1)
            amount = loguni(rng, 10 ** 6, 1 << 128)
            fee = rng.choice((100, 500, 3000, 10000, rng.randrange(0, 10 ** 6)))
        zfo, exact_in = rng.random() < 0.5, rng.random() < 0.5
        if normal:  # the amount given: the input token (exact in) or the output token (exact out), 1..1e9 tokens
            given_dec = (d0 if zfo else d1) if exact_in else (d1 if zfo else d0)
            amount = units(logtok(rng), given_dec, rng)
        try:
            r = v3_case(cur, L, amount, fee, zfo, exact_in)
        except Revert:
            continue
        if r is None:
            continue
        ret, exact, kind = r
        if exact < (1 if normal else 10 ** 6):
            continue
        kept += 1
        inp = f"{kind} {'zeroForOne' if zfo else 'oneForZero'}: sqrtPriceX96={cur} (price {mp.nstr((mp.mpf(cur) / Q96) ** 2, 6)}), liquidity={L}, amount={amount}, feePips={fee}"
        w.add(ret, exact, inp, other=amount)
    return w


def row_uniswap_v3_swap():
    src("v3sqrt"), src("v3swap")
    wn = parallel(_v3_chunk, 150_000, True)
    wd = parallel(_v3_chunk, 100_000, False)
    for cur in (Q96, MIN_SQRT_RATIO + 1, MAX_SQRT_RATIO - 2, 1 << 64, 1 << 128, 1 << 159, Q96 // 1000, Q96 * 1000):
        for L in (10 ** 6, 10 ** 12, 10 ** 18, 10 ** 24, 10 ** 27, MAX_LIQ_PER_TICK_1):
            for amount in (10 ** 6, 10 ** 6 + 1, 10 ** 12, 10 ** 18, 10 ** 24, 10 ** 27):
                for fee in (0, 100, 500, 3000, 10000):
                    for zfo in (True, False):
                        for exact_in in (True, False):
                            try:
                                r = v3_case(cur, L, amount, fee, zfo, exact_in)
                            except Revert:
                                continue
                            if r is None or r[1] < 10 ** 6:
                                continue
                            inp = f"{r[2]} {'zeroForOne' if zfo else 'oneForZero'}: sqrtPriceX96={cur} (price {mp.nstr((mp.mpf(cur) / Q96) ** 2, 6)}), liquidity={L}, amount={amount}, feePips={fee}"
                            wd.add(r[0], r[1], inp, other=amount)
                            pass
    return dict(
        w=wn, wd=wd,
        normal_range="token price 1e-6..1e6 (decimals 6, 8 or 18 each), liquidity whose virtual reserves L/√P and L·√P are both 1..1e9 whole tokens, amount 1..1e9 whole tokens, fee 100/500/3000/10000 pips or up to 10%; error in the smallest unit of the more valuable token",
        truth="the documented constant-liquidity step: input less the fee a = amount·(1 − fee/10^6); zeroForOne √Q = L√P/(L + a√P), out = L(√P − √Q); oneForZero √Q = √P + a/L, out = L(1/√P − 1/√Q); exact output: in = L·Δ(·)/(1 − fee); √P = sqrtPriceX96/2^96, real",
        search="normal: 150,000 random in-range steps (both directions, exact in and exact out; exact amounts below 1e6 skipped); domain: 100,000 random over MIN..MAX_SQRT_RATIO, liquidity to maxLiquidityPerTick(1) = 1.9e32, amounts to 2^128, any fee; plus a grid of 8 prices × 6 liquidities × 6 amounts × 5 fees × 4 kinds",
    )


# ================================================================ 6. Uniswap v3/v4 TickMath (exhaustive)
def v3_tick_consts():
    t = src("v3tick")
    body = t[t.index("function getSqrtRatioAtTick"):t.index("function getTickAtSqrtRatio")]
    c = hexes_in(body, r"0x([0-9a-f]{20,})")
    # first: odd-bit constant then 0x1000..; then 19 multipliers
    first, one = c[0], c[1]
    assert one == 1 << 128 and len(c) == 21
    t4 = src("v4tick")
    b4 = t4[t4.index("function getSqrtPriceAtTick"):t4.index("function getTickAtSqrtPrice")]
    c4 = hexes_in(b4, r"\*\s*0x([0-9a-f]{20,})\)")
    assert c4 == c[2:], "v4 TickMath constants differ from v3"
    return first, c[2:]


def get_sqrt_ratio_at_tick(tick, first, mults):
    a = -tick if tick < 0 else tick
    if a > 887272:
        raise Revert("T")
    ratio = first if a & 1 else 1 << 128
    for i, m in enumerate(mults):
        if a & (2 << i):
            ratio = (ratio * m) >> 128
    if tick > 0:
        ratio = MAXU // ratio
    return (ratio >> 32) + (0 if ratio % (1 << 32) == 0 else 1)


def _tick_sweep(sign, lo, hi, first, mults, fracbits=520):
    """Exact sqrt(1.0001)^tick * 2^96 stepped in fixed point with 2^-fracbits resolution (error < tick·2^-fracbits).
    Returns (domain Worst, normal Worst for |tick| <= NORMAL_TICK, ceil-correct flag)."""
    wd, wn = Worst(), Worst()
    mp.mp.dps = 200
    r = mp.sqrt(mp.mpf("1.0001")) if sign > 0 else 1 / mp.sqrt(mp.mpf("1.0001"))
    R = int(mp.floor(r * mp.mpf(2) ** fracbits))
    S = int(mp.floor(mp.mpf(2) ** 96 * r ** lo * mp.mpf(2) ** fracbits))
    mp.mp.dps = 120
    ceil_ok = [True, True]
    for k in range(lo, hi + 1):
        t = sign * k
        ret = get_sqrt_ratio_at_tick(t, first, mults)
        diff = (ret << fracbits) - S
        if diff < 0 or diff >= (1 << fracbits):
            ceil_ok[0] = False
            if k <= NORMAL_TICK:
                ceil_ok[1] = False
        u = abs(diff) / 2.0 ** fracbits
        d = (math.log10(S) - math.log10(abs(diff))) if diff else float(len(str(ret)))
        cap = math.log10(S) - fracbits * LOG10_2
        for w in ((wd, wn) if k <= NORMAL_TICK else (wd,)):
            w.n += 1
            w.n_digits += 1
            if u > w.u:
                w.u, w.u_in = u, f"tick {t}"
            if d < w.d:
                w.d, w.d_in = d, f"tick {t}"
            w.held_update(cap, d, f"tick {t}", exact_hit=(diff == 0))
            w.signs.add("+" if diff > 0 else "-" if diff < 0 else "0")
        if k == hi:
            ex = mp.sqrt(mp.mpf("1.0001") ** t) * 2 ** 96
            assert abs(mp.mpf(S) / mp.mpf(2) ** fracbits / ex - 1) < mp.mpf(10) ** -100
        S = (S * R) >> fracbits
    return wd, wn, ceil_ok


def _tick_job(args):
    sign, lo, hi = args
    first, mults = v3_tick_consts()
    return _tick_sweep(sign, lo, hi, first, mults)


def row_uniswap_v3_tickmath():
    first, mults = v3_tick_consts()
    jobs = []
    step = 887272 // (WORKERS * 2) + 1
    for sign in (1, -1):
        for lo in range(0 if sign > 0 else 1, 887273, step):
            jobs.append((sign, lo, min(lo + step - 1, 887272)))
    with Pool(WORKERS) as p:
        parts = p.map(_tick_job, jobs)
    wd, wn = Worst(), Worst()
    ceil_ok, ceil_n = True, True
    for d_, n_, c_ in parts:
        wd.merge(d_)
        wn.merge(n_)
        ceil_ok &= c_[0]
        ceil_n &= c_[1]
    wn.signs.discard("0")
    wd.signs.discard("0")
    d_at = {}
    for t in (-887272, -500000, -138163, -100000, -10000, -1, 1, 10000, 100000, 138163, 500000, 887272):
        ex = mp.sqrt(mp.mpf("1.0001") ** t) * 2 ** 96
        d_at[t] = round(mpf_exact_digits(get_sqrt_ratio_at_tick(t, first, mults), ex), 2)
    wd.note["digits_at"] = (0, d_at)
    wd.note["ceil_correct_everywhere"] = (1.0 if ceil_ok else 0.0, None)
    return dict(
        w=wn, wd=wd,
        normal_range=f"|tick| <= {NORMAL_TICK:,} (prices 1e-6..1e6)",
        truth="sqrt(1.0001^tick)·2^96 (the @notice: 'Calculates sqrt(1.0001^tick) * 2^96')",
        search="every tick in [−887272, 887272] (1,774,545 ticks; the normal range is a subset of the same sweep), truth stepped in 2^-520 fixed point from mpmath seeds and checked against mpmath at the end of every run",
        extra=(("returned = ceil(exact) at every normal tick (correctly rounded up, the stated direction)" if ceil_n else
                f"not ceil(exact) at every normal tick: the worst is {wn.u:.6f} units at {wn.u_in}") + "; " +
               ("ceil(exact) at every tick of the domain" if ceil_ok else "not ceil(exact) over the whole domain")),
    )


# ================================================================ 13. Maverick v2 TickMath (exhaustive)
def mav_consts():
    t = src("mav_tick")
    body = t[t.index("function tickSqrtPrice"):]
    body = body[:body.index("_result = ")]
    c = hexes_in(body, r"0x([0-9a-f]{20,})")
    assert c[1] == 1 << 128 and len(c) == 20
    k = src("mav_const")
    max_tick = int(re.search(r"uint256 constant MAX_TICK = ([\d_]+);", k).group(1).replace("_", ""))
    one = int(re.search(r"uint128 constant ONE = (\d+e\d+|\d+);", k).group(1).replace("1e18", str(10 ** 18)))
    return c[0], c[2:], max_tick, one


def mav_tick_sqrt_price(tick, first, mults, max_tick, one):
    a = abs(tick)
    if a > max_tick:
        raise Revert("TickMaxExceeded")
    ratio = first if a & 1 else 1 << 128
    for i, m in enumerate(mults):
        if a & (2 << i):
            ratio = (ratio * m) >> 128
    if tick > 0:
        ratio = MAXU // ratio
    return (ratio * one) >> 128


def _mav_job(args):
    sign, lo, hi = args
    first, mults, max_tick, one = mav_consts()
    fracbits = 400
    mp.mp.dps = 200
    r = mp.sqrt(mp.mpf("1.0001")) if sign > 0 else 1 / mp.sqrt(mp.mpf("1.0001"))
    R = int(mp.floor(r * mp.mpf(2) ** fracbits))
    S = int(mp.floor(one * r ** lo * mp.mpf(2) ** fracbits))
    mp.mp.dps = 120
    wd, wn = Worst(), Worst()
    for k in range(lo, hi + 1):
        t = sign * k
        ret = mav_tick_sqrt_price(t, first, mults, max_tick, one)
        diff = (ret << fracbits) - S
        u = abs(diff) / 2.0 ** fracbits
        d = (math.log10(S) - math.log10(abs(diff))) if diff else float(len(str(ret)))
        cap = math.log10(S) - fracbits * LOG10_2
        for w in ((wd, wn) if k <= NORMAL_TICK else (wd,)):
            w.n += 1
            w.n_digits += 1
            if u > w.u:
                w.u, w.u_in = u, f"tick {t} (tickSpacing 1)"
            if d < w.d:
                w.d, w.d_in = d, f"tick {t} (tickSpacing 1)"
            w.held_update(cap, d, f"tick {t} (tickSpacing 1)", exact_hit=(diff == 0))
            if diff:
                w.signs.add("+" if diff > 0 else "-")
        if k == hi:
            ex = mp.sqrt(mp.mpf("1.0001") ** t) * one
            assert abs(mp.mpf(S) / mp.mpf(2) ** fracbits / ex - 1) < mp.mpf(10) ** -100
        S = (S * R) >> fracbits
    return wd, wn


def row_maverick_tickmath():
    first, mults, max_tick, one = mav_consts()
    step = max_tick // (WORKERS * 2) + 1
    jobs = [(s, lo, min(lo + step - 1, max_tick)) for s in (1, -1) for lo in range(0 if s > 0 else 1, max_tick + 1, step)]
    with Pool(WORKERS) as p:
        parts = p.map(_mav_job, jobs)
    wd, wn = Worst(), Worst()
    for d_, n_ in parts:
        wd.merge(d_)
        wn.merge(n_)
    d_at = {}
    for t in (-max_tick, -138163, -100000, -10000, -1000, -1, 1, 1000, 10000, 100000, 138163, max_tick):
        ex = mp.sqrt(mp.mpf("1.0001") ** t) * one
        d_at[t] = round(mpf_exact_digits(mav_tick_sqrt_price(t, first, mults, max_tick, one), ex), 2)
    wd.note["digits_at"] = (0, d_at)
    return dict(
        w=wn, wd=wd,
        normal_range=f"|tick·tickSpacing| <= {NORMAL_TICK:,} (prices 1e-6..1e6)",
        truth="sqrt(1.0001^tick)·1e18 (tickSqrtPrice, D18; Constants.sol 'max price 1e14 in D18 scale')",
        search=f"every subtick in [−{max_tick}, {max_tick}] ({2 * max_tick + 1:,} values; tickSpacing·tick is the only input the constants see), truth stepped in 2^-400 fixed point from mpmath seeds and checked against mpmath at the end of every run",
    )


# ================================================================ 7. Trader Joe LB bin price (exhaustive per bin step)
LB_BIN_STEPS = (1, 2, 5, 8, 10, 15, 20, 25, 50, 80, 100, 150, 200, 250)


def lb_consts():
    t = src("lbprice")
    assert "Constants.SCALE + (uint256(binStep) << Constants.SCALE_OFFSET) / Constants.BASIS_POINT_MAX" in t
    assert "REAL_ID_SHIFT = 1 << 23" in t
    p = src("lbpow")
    assert "if (absY < 0x100000)" in p and "squared := div(not(0), squared)" in p
    return 1 << 128, 10_000, 1 << 23


def lb_base(bin_step):
    scale, bpm, _ = 1 << 128, 10_000, None
    return scale + (bin_step << 128) // bpm


def lb_pow(x, y):
    # Uint128x128Math.pow (L95-175)
    if y == 0:
        return 1 << 128
    invert = y < 0
    absy = -y if y < 0 else y
    result = 0
    if absy < 0x100000:
        result = 1 << 128
        sq = x
        if x > (1 << 128) - 1:
            sq = MAXU // sq
            invert = not invert
        for i in range(20):
            if absy & (1 << i):
                result = ((result * sq) % U256) >> 128
            sq = ((sq * sq) % U256) >> 128
    if result == 0:
        raise Revert("PowUnderflow")
    return MAXU // result if invert else result


def lb_price(id_, bin_step):
    return lb_pow(lb_base(bin_step), id_ - (1 << 23))


def _lb_job(args):
    bin_step, sign = args
    fracbits = 560
    mp.mp.dps = 220
    b = 1 + mp.mpf(bin_step) / 10_000
    r = b if sign > 0 else 1 / b
    R = int(mp.floor(r * mp.mpf(2) ** fracbits))
    S = int(mp.floor(mp.mpf(2) ** 128 * mp.mpf(2) ** fracbits)) if sign > 0 else int(mp.floor(mp.mpf(2) ** 128 / b * mp.mpf(2) ** fracbits))
    lg_step = float(mp.log10(b))
    mp.mp.dps = 120
    wd, wn = Worst(), Worst()
    e = 0 if sign > 0 else -1
    base = lb_base(bin_step)
    last_ok = None
    while True:
        try:
            ret = lb_pow(base, e)
        except Revert:
            break
        diff = (ret << fracbits) - S
        u = abs(diff) / 2.0 ** fracbits
        inp = f"binStep {bin_step}, id 2^23{e:+d}"
        d = (math.log10(S) - math.log10(abs(diff))) if diff else float(len(str(ret)))
        cap = math.log10(S) - fracbits * LOG10_2
        for w in ((wd, wn) if abs(e * lg_step) <= 6 else (wd,)):
            w.n += 1
            w.n_digits += 1
            if u > w.u:
                w.u, w.u_in = u, inp
            if d < w.d:
                w.d, w.d_in = d, inp
            w.held_update(cap, d, inp, exact_hit=(diff == 0))
            if diff:
                w.signs.add("+" if diff > 0 else "-")
        last_ok = e
        e += sign
        if abs(e) >= 0x100000:
            break
        S = (S * R) >> fracbits
    wd.note[f"range binStep {bin_step} {'+' if sign > 0 else '-'}"] = (float(last_ok), None)
    return wd, wn


def row_trader_joe_lb_price():
    lb_consts()
    jobs = [(s, sg) for s in LB_BIN_STEPS for sg in (1, -1)]
    with Pool(WORKERS) as p:
        parts = p.map(_lb_job, jobs)
    wd, wn = Worst(), Worst()
    ranges = {}
    for d_, n_ in parts:
        for k in list(d_.note):
            if k.startswith("range"):
                ranges[k] = int(d_.note.pop(k)[0])
        wd.merge(d_)
        wn.merge(n_)
    wd.note["ranges"] = (0, ranges)
    for s_, e_ in ((100, 1388), (1, 138163), (25, 1), (100, -1388)):
        ex = (1 + mp.mpf(s_) / 10000) ** e_ * mp.mpf(2) ** 128
        got = mpf_exact_digits(lb_price((1 << 23) + e_, s_), ex)
        assert got > 0
    return dict(
        w=wn, wd=wd,
        normal_range="ids whose price (1 + binStep/10000)^(id − 2^23) is within 1e-6..1e6, at each bin step",
        truth="(1 + binStep/10000)^(id − 2^23)·2^128 (PriceHelper: the base is '1 + binStep / BASIS_POINT_MAX', price = base^exponent in 128.128)",
        search=f"every id at bin steps {', '.join(map(str, LB_BIN_STEPS))} from 2^23 outward in both directions until getPriceFromId reverts (PowUnderflow) or |exponent| reaches 2^20; truth stepped in 2^-560 fixed point",
    )


# ================================================================ 5. Trader Joe LB swap in a bin
def lb_get_amounts(reserve_out, price, total_fee, amount_in, swap_for_y):
    # BinHelper.getAmounts (L230-271) with FeeHelper.getFeeAmount/getFeeAmountFrom
    P18 = 10 ** 18
    if swap_for_y:
        max_in = div_up(reserve_out << 128, price)  # shiftDivRoundUp
    else:
        max_in = (reserve_out * price) >> 128
        if (reserve_out * price) % (1 << 128):
            max_in += 1  # mulShiftRoundUp
    if max_in >= 1 << 128:
        raise Revert("safe128")
    den = P18 - total_fee
    max_fee = (max_in * total_fee + den - 1) // den
    max_in += max_fee
    if amount_in >= max_in:
        return max_in, reserve_out, max_fee, True
    fee = (amount_in * total_fee + P18 - 1) // P18
    net = amount_in - fee
    out = (net * price) >> 128 if swap_for_y else (net << 128) // price
    if out >= 1 << 128:
        raise Revert("safe128")
    out = min(out, reserve_out)
    return amount_in, out, fee, False


def _lbswap_chunk(seed, n, normal):
    rng = random.Random(seed)
    w = Worst()
    kept = 0
    hi = N_HI if normal else (1 << 128) - 1
    while kept < n:
        s = rng.choice(LB_BIN_STEPS)
        if normal:
            dx_, dy_ = rng.choice(DECS), rng.choice(DECS)
            raw = mp.mpf(logprice(rng)) * mp.mpf(10) ** (dy_ - dx_)  # raw Y per raw X
            e = int(mp.nint(mp.log(raw) / mp.log(1 + mp.mpf(s) / 10000)))
        else:
            span = int(38 * math.log(10) / math.log(1 + s / 10000))
            e = rng.choice((rng.randint(-span, span), rng.randint(-span // 20, span // 20), rng.randint(-min(span, 2000), min(span, 2000))))
        try:
            price = lb_price((1 << 23) + e, s)
        except Revert:
            continue
        P = (1 + mp.mpf(s) / 10000) ** e
        total_fee = rng.choice((0, rng.randrange(0, 10 ** 17 + 1), 10 ** 15, 3 * 10 ** 15))
        f = mp.mpf(total_fee) / 10 ** 18
        sfy = rng.random() < 0.5
        if normal:
            reserve_out = units(logtok(rng), dy_ if sfy else dx_, rng)
            amount_in = units(logtok(rng), dx_ if sfy else dy_, rng)
        else:
            reserve_out = loguni(rng, 10 ** 6, hi)
            amount_in = loguni(rng, 10 ** 6, hi)
        try:
            ain, aout, fee, full = lb_get_amounts(reserve_out, price, total_fee, amount_in, sfy)
        except Revert:
            continue
        if full:
            exact = (mp.mpf(reserve_out) / P if sfy else mp.mpf(reserve_out) * P) / (1 - f)
            ret, kind, other = ain, "bin emptied (amountIn charged)", reserve_out
        else:
            exact = mp.mpf(amount_in) * (1 - f) * (P if sfy else 1 / P)
            ret, kind, other = aout, "partial (amountOut)", amount_in
        if exact < (1 if normal else 10 ** 6) or exact >= 1 << 128:
            continue
        kept += 1
        inp = f"{kind}, swapForY={sfy}: binStep {s}, id 2^23{e:+d} (price {mp.nstr(P, 6)}), reserveOut={reserve_out}, amountIn={amount_in}, totalFee={total_fee}"
        w.add(ret, exact, inp, other=other)
    return w


def row_trader_joe_lb_swap():
    src("lbbin"), src("lbfee")
    wn = parallel(_lbswap_chunk, 150_000, True)
    wd = parallel(_lbswap_chunk, 100_000, False)
    return dict(
        w=wn, wd=wd,
        normal_range="token price 1e-6..1e6 (decimals 6, 8 or 18 each; the bin nearest that price at each bin step), reserveOut and amountIn 1..1e9 whole tokens, totalFee 0..10%; error in the smallest unit of the more valuable token",
        truth="amountIn·(1 − totalFee/1e18)·P out of the bin (swapForY; ÷P for X), with P = (1 + binStep/10000)^(id − 2^23) the documented price; a bin emptied charges reserveOut/P/(1 − fee)",
        search="normal: 150,000 random swaps in one bin (bin steps as in the price row, ids over the normal price band, fee 0..0.1e18 = the pair's cap); domain: 100,000 with prices to 1e±38 and reserves/amounts to 2^128; exact amounts below 1e6 skipped",
    )


# ================================================================ 8. Uniswap v3 TWAP (OracleLibrary)
def consult_mean_tick(delta, seconds_ago):
    # OracleLibrary.consult L34-36: int56 / uint32 truncates toward zero, then 'Always round to negative infinity'
    q = abs(delta) // seconds_ago
    t = q if delta >= 0 else -q
    if delta < 0 and (delta % seconds_ago != 0):
        t -= 1
    return t


def quote_at_tick(tick, base_amount, base_lt_quote, first, mults):
    s = get_sqrt_ratio_at_tick(tick, first, mults)
    if s <= (1 << 128) - 1:
        r192 = s * s
        return mul_div(r192, base_amount, 1 << 192) if base_lt_quote else mul_div(1 << 192, base_amount, r192)
    r128 = mul_div(s, s, 1 << 64)
    return mul_div(r128, base_amount, 1 << 128) if base_lt_quote else mul_div(1 << 128, base_amount, r128)


def _twap_chunk(seed, n, normal):
    rng = random.Random(seed)
    first, mults = v3_tick_consts()
    w = Worst()
    kept = 0
    while kept < n:
        if normal:
            secs = rng.choice((rng.randint(TWAP_LO, 3600), rng.randint(TWAP_LO, TWAP_HI), TWAP_LO, TWAP_HI))
            mean = rng.randint(-NORMAL_TICK + 1, NORMAL_TICK - 1)
            base = units(logtok(rng), rng.choice(DECS), rng)
        else:
            secs = rng.choice((rng.randint(1, 3600), rng.randint(1, 86400 * 30), rng.randint(1, (1 << 32) - 1)))
            mean = rng.choice((rng.randint(-887271, 887271), rng.randint(-50000, 50000)))
            base = loguni(rng, 10 ** 6, (1 << 128) - 1)
        frac = rng.choice((rng.randrange(secs), secs - 1, 1 if secs > 1 else 0))
        delta = mean * secs + frac
        if not -(1 << 55) <= delta < 1 << 55:
            continue
        tick = consult_mean_tick(delta, secs)
        if not -887272 <= tick <= 887272:
            continue
        blq = rng.random() < 0.5
        true_tick = mp.mpf(delta) / secs
        exact = base * mp.mpf("1.0001") ** (true_tick if blq else -true_tick)
        if exact < 10 ** 6 or exact > MAXU:
            continue
        try:
            q = quote_at_tick(tick, base, blq, first, mults)
        except Revert:
            continue
        kept += 1
        w.add(q, exact, f"tickCumulativesDelta={delta}, secondsAgo={secs} (mean tick {mp.nstr(true_tick, 12)} → {tick}), baseAmount={base}, base<quote={blq}")
    return w


def row_uniswap_v3_twap():
    src("oracle")
    first, mults = v3_tick_consts()
    wn = parallel(_twap_chunk, 150_000, True)
    wd = parallel(_twap_chunk, 100_000, False)
    for secs, w, ticks, base in ((TWAP_HI, wn, (-NORMAL_TICK + 1, -1, 0, 1, NORMAL_TICK - 2), 10 ** 27),
                                 ((1 << 32) - 1, wd, (-887271, -1, 0, 1, 200000, 887270), 10 ** 18)):
        for mean in ticks:
            for frac in (secs - 1, 1):
                delta = mean * secs + frac
                tick = consult_mean_tick(delta, secs)
                for blq in (True, False):
                    true_tick = mp.mpf(delta) / secs
                    exact = base * mp.mpf("1.0001") ** (true_tick if blq else -true_tick)
                    if exact < 10 ** 6:
                        continue
                    q = quote_at_tick(tick, base, blq, first, mults)
                    w.add(q, exact, f"tickCumulativesDelta={delta}, secondsAgo={secs} (mean tick {mp.nstr(true_tick, 15)} → {tick}), baseAmount={base}, base<quote={blq}")
    return dict(
        w=wn, wd=wd,
        normal_range=f"windows {TWAP_LO} s..1 day, mean |tick| < {NORMAL_TICK:,} (prices 1e-6..1e6), baseAmount 1..1e9 whole tokens (decimals 6, 8 or 18); error in the quote's own unit",
        truth="baseAmount·1.0001^(tickCumulativesDelta/secondsAgo): the price at the true arithmetic-mean tick over the window",
        search="normal: 150,000 random windows (remainder random, secondsAgo−1 or 1; both token orders) plus 1-day windows with remainder 86,399 s at five ticks; domain: 100,000 with windows to 2^32−1 s, the whole tick range and baseAmount to 2^128",
    )


# ================================================================ 9. Pendle exchange rate
def pendle_consts():
    t = src("pendle_lem")
    c = {}
    for name, val in re.findall(r"int256 constant (x\d+|a\d+) = ([\d_]+);", t):
        c[name] = int(val.replace("_", ""))
    assert len(c) == 24
    m = src("pendle_mmc")
    assert "uint256 rt = (lnImpliedRate * timeToExpiry) / IMPLIED_RATE_TIME;" in m
    assert "IMPLIED_RATE_TIME = 365 * DAY" in m
    return c


def pendle_exp(x, c):
    # LogExpMath.exp (L94-200); x >= 0 here (rt is unsigned)
    ONE_18, ONE_20 = 10 ** 18, 10 ** 20
    if not (-41 * ONE_18 <= x <= 130 * ONE_18):
        raise Revert("Invalid exponent")
    assert x >= 0
    if x >= c["x0"]:
        x -= c["x0"]
        first = c["a0"]
    elif x >= c["x1"]:
        x -= c["x1"]
        first = c["a1"]
    else:
        first = 1
    x *= 100
    product = ONE_20
    for k in range(2, 10):
        if x >= c[f"x{k}"]:
            x -= c[f"x{k}"]
            product = product * c[f"a{k}"] // ONE_20
    s = ONE_20
    term = x
    s += term
    for k in range(2, 13):
        term = term * x // ONE_20 // k
        s += term
    return product * s // ONE_20 * first // 100


YEAR = 365 * 86400


def _pendle_chunk(seed, n, normal):
    rng = random.Random(seed)
    c = pendle_consts()
    w = Worst()
    for _ in range(n):
        if normal:
            tte = rng.choice((rng.randint(86400, 2 * YEAR), loguni(rng, 86400, 2 * YEAR)))
            ln_r = rng.choice((loguni(rng, 10 ** 12, int(math.log(2) * 1e18)), rng.randint(1, int(math.log(2) * 1e18))))
        else:
            tte = rng.choice((rng.randint(1, 2 * YEAR), loguni(rng, 1, 5 * YEAR)))
            cap = 130 * 10 ** 18 * YEAR // tte
            ln_r = min(loguni(rng, 1, cap), cap)
        rt = ln_r * tte // YEAR
        ret = pendle_exp(rt, c)
        exact = mp.exp(mp.mpf(ln_r) * tte / YEAR / 10 ** 18) * 10 ** 18
        w.add(ret, exact, f"lnImpliedRate={ln_r} (APY {mp.nstr(mp.exp(mp.mpf(ln_r) / 10 ** 18) - 1, 6)}), timeToExpiry={tte} s (rt = {mp.nstr(mp.mpf(rt) / 10 ** 18, 10)})")
    return w


def row_pendle():
    c = pendle_consts()
    wn = parallel(_pendle_chunk, 150_000, True)
    wd = parallel(_pendle_chunk, 100_000, False)
    edges = {0, 1, 130 * 10 ** 18, 130 * 10 ** 18 - 1}
    for k in range(0, 10):
        xk = c[f"x{k}"] // (100 if k >= 2 else 1)
        for d in (-1, 0, 1):
            for base in (0, c["x1"], c["x0"]):
                v = base + xk + d
                if 0 <= v <= 130 * 10 ** 18:
                    edges.add(v)
    edges |= {1 << k for k in range(0, 67) if 1 << k <= 130 * 10 ** 18}
    rt_max = int(math.log(2) * 1e18) * 2  # APY 100% for two years
    for rt in sorted(edges):
        ret = pendle_exp(rt, c)
        exact = mp.exp(mp.mpf(rt) / 10 ** 18) * 10 ** 18
        inp = f"rt = {rt} (lnImpliedRate·timeToExpiry/365 days, exact)"
        wd.add(ret, exact, inp)
        if rt <= rt_max:
            wn.add(ret, exact, inp)
    return dict(
        w=wn, wd=wd,
        normal_range="implied APY 0..100% (lnImpliedRate ≤ ln 2), time to expiry 1 day..2 years",
        truth="E = e^(lnImpliedRate/1e18 · timeToExpiry/365 days)·1e18 ('The formula is E = e^rt')",
        search="normal: 150,000 random (expiry uniform or log-uniform in 1 day..2 years; lnImpliedRate uniform or log-uniform up to ln 2) plus every reduction threshold and power of two with rt ≤ 2·ln 2; domain: 100,000 up to LogExpMath's 130e18 bound on rt (expiry to 5 years) and every threshold x0..x9 ±1 and power of two to 130e18",
    )


# ================================================================ 10. GMX v2 applyExponentFactor
def prb_consts():
    t = src("prb")
    body = t[t.index("function exp2(uint256 x)"):t.index("function mostSignificantBit")]
    pairs = re.findall(r"if \(x & 0x([0-9A-Fa-f]+) > 0\) \{\s*result = \(result \* 0x([0-9A-Fa-f]+)\) >> 64;", body)
    assert len(pairs) == 64
    u = src("prbud")
    assert "result = exp2(mul(log2(x), y));" in u and "for (uint256 delta = HALF_SCALE; delta > 0; delta >>= 1)" in u
    g = src("gmx_prec")
    assert "return value / FLOAT_TO_WEI_DIVISOR;" in g and "if (floatValue < FLOAT_PRECISION)" in g
    return [(int(a, 16), int(b, 16)) for a, b in pairs]


SC = 10 ** 18


def prb_exp2_192x64(x, pairs):
    result = 0x800000000000000000000000000000000000000000000000
    for bit, m in pairs:
        if x & bit:
            result = (result * m) >> 64
    result *= SC
    return result >> (191 - (x >> 64))


def prb_log2(x):
    if x < SC:
        raise Revert("LogInputTooSmall")
    n = (x // SC).bit_length() - 1
    result = n * SC
    y = x >> n
    if y == SC:
        return result
    delta = SC // 2
    while delta > 0:
        y = y * y // SC
        if y >= 2 * SC:
            result += delta
            y >>= 1
        delta >>= 1
    return result


def prb_mul(x, y):  # mulDivFixedPoint: round half up
    p = x * y
    if p >> 256 >= SC:
        raise Revert("MulDivFixedPointOverflow")
    return p // SC + (1 if p % SC > 499999999999999999 else 0)


def gmx_apply_exponent(float_value, exponent, pairs):
    FP = 10 ** 30
    if float_value < FP:
        return 0
    if exponent == FP:
        return float_value
    x, y = float_value // 10 ** 12, exponent // 10 ** 12
    e = prb_mul(prb_log2(x), y)
    if e >= 192 * SC:
        raise Revert("Exp2InputTooBig")
    return prb_exp2_192x64((e << 64) // SC, pairs) * 10 ** 12


def _gmx_chunk(seed, n, normal):
    rng = random.Random(seed)
    pairs = prb_consts()
    w = Worst()
    FP = 10 ** 30
    top = 10 ** 9 if normal else 10 ** 12
    kept = 0
    while kept < n:
        ex = rng.choice((2 * FP, rng.randint(FP + 1, 3 * FP), rng.randint(FP + 1, 2 * FP), int(1.5 * FP) + rng.randint(-10 ** 12, 10 ** 12)))
        v = rng.choice((loguni(rng, FP, top * FP), rng.randint(FP, 2 * FP), loguni(rng, FP, 10 ** 6 * FP)))
        try:
            ret = gmx_apply_exponent(v, ex, pairs)
        except Revert:
            continue
        kept += 1
        exact = (mp.mpf(v) / FP) ** (mp.mpf(ex) / FP) * FP
        w.add(ret, exact, f"floatValue={v} ({mp.nstr(mp.mpf(v) / FP, 8)} USD), exponentFactor={ex} ({mp.nstr(mp.mpf(ex) / FP, 8)})")
    return w


def row_gmx():
    pairs = prb_consts()
    wn = parallel(_gmx_chunk, 150_000, True)
    wd = parallel(_gmx_chunk, 100_000, False)
    FP = 10 ** 30
    for v in [FP, FP + 1, FP + 10 ** 12, FP + 10 ** 12 - 1, 2 * FP - 1, 2 * FP] + [FP << k for k in range(1, 40)] + [10 ** k * FP for k in range(1, 13)]:
        for ex in (FP + 10 ** 12, int(1.5 * FP), 2 * FP, 3 * FP, 2 * FP - 1):
            try:
                ret = gmx_apply_exponent(v, ex, pairs)
            except Revert:
                continue
            exact = (mp.mpf(v) / FP) ** (mp.mpf(ex) / FP) * FP
            inp = f"floatValue={v} ({mp.nstr(mp.mpf(v) / FP, 8)} USD), exponentFactor={ex} ({mp.nstr(mp.mpf(ex) / FP, 8)})"
            wd.add(ret, exact, inp)
            if v <= 10 ** 9 * FP:
                wn.add(ret, exact, inp)
    return dict(
        w=wn, wd=wd,
        normal_range="floatValue (the USD imbalance) 1 USD..1e9 USD, exponent factor in (1, 3]",
        truth="(floatValue/1e30)^(exponentFactor/1e30)·1e30 (applyExponentFactor; the impact is diffUsd^exponent·factor)",
        search="normal: 150,000 random (floatValue log-uniform to 1e9 or 1e6 USD or uniform in [1, 2) USD; exponentFactor 2.0, uniform in (1, 3], (1, 2] or 1.5 ± 1e-18) plus powers of two and ten and the 1-USD edge (below it the function returns 0 by design) at five exponents; domain: the same to 1e12 USD",
    )


# ================================================================ 12. Algebra V1 dynamic fee
def algebra_config():
    t = src("algebra_fee")
    assert "if (x >= 6 * uint256(g)) return alpha;" in t and "res += (xLowestDegree * g) / 5040 + (xLowestDegree * x) / (40320);" in t
    f = src("algebra_factory")
    m = re.search(r"AdaptiveFee\.Configuration\((.*?)\);", f, re.S)
    vals = [ln.split("//")[0].strip().rstrip(",") for ln in m.group(1).strip().splitlines()]
    base_fee = 100  # Constants.BASE_FEE
    env = {"Constants.BASE_FEE": str(base_fee)}
    out = []
    for v in vals:
        for k, r in env.items():
            v = v.replace(k, r)
        out.append(int(eval(v, {"__builtins__": {}})))
    keys = ("alpha1", "alpha2", "beta1", "beta2", "gamma1", "gamma2", "volumeBeta", "volumeGamma", "baseFee")
    return dict(zip(keys, out))


def alg_exp(x, g, g8):
    res = g8
    gh = g8 // g
    res += x * gh
    xl = x
    for d in (2, 6, 24, 120, 720):
        gh //= g
        xl *= x
        res += xl * gh // d
    xl *= x
    res += xl * g // 5040 + xl * x // 40320
    return res


def alg_sigmoid(x, g, alpha, beta):
    if x > beta:
        x -= beta
        if x >= 6 * g:
            return alpha
        g8 = g ** 8
        ex = alg_exp(x, g, g8)
        return alpha * ex // (g8 + ex)
    x = beta - x
    if x >= 6 * g:
        return 0
    g8 = g ** 8
    ex = g8 + alg_exp(x, g, g8)
    return alpha * g8 // ex


def alg_fee(vol, vpl, c):
    s = alg_sigmoid(vol, c["gamma1"], c["alpha1"], c["beta1"]) + alg_sigmoid(vol, c["gamma2"], c["alpha2"], c["beta2"])
    s = min(s, 65535)
    return c["baseFee"] + alg_sigmoid(vpl, c["volumeGamma"], s, c["volumeBeta"])


def sig_true(x, g, alpha, beta):
    return mp.mpf(alpha) / (1 + mp.exp((mp.mpf(beta) - x) / g))


def _algebra_job(args):
    vpl_list, vol_hi = args
    c = algebra_config()
    mp.mp.dps = 110
    inner = [sig_true(v, c["gamma1"], c["alpha1"], c["beta1"]) + sig_true(v, c["gamma2"], c["alpha2"], c["beta2"]) for v in range(vol_hi + 1)]
    w = Worst()
    for vpl in vpl_list:
        dv = 1 / (1 + mp.exp((mp.mpf(c["volumeBeta"]) - vpl) / c["volumeGamma"]))
        for vol in range(vol_hi + 1):
            ret = alg_fee(vol, vpl, c)
            exact = c["baseFee"] + inner[vol] * dv
            w.add(ret, exact, f"volatility={vol}, volumePerLiquidity={vpl}")
    return w


def row_algebra():
    c = algebra_config()
    vol_hi = c["beta2"] + 6 * c["gamma2"] + 1000  # beyond it both sigmoids return alpha
    vpls = list(range(0, 6 * c["volumeGamma"] + 41))
    jobs = [(vpls[k::WORKERS * 2], vol_hi) for k in range(WORKERS * 2) if vpls[k::WORKERS * 2]]
    with Pool(WORKERS) as p:
        parts = p.map(_algebra_job, jobs)
    w = Worst()
    for part in parts:
        w.merge(part)
    w.note["config"] = (0, c)
    return dict(
        w=w, wd=w,
        normal_range=f"every volatility 0..{vol_hi} and volumePerLiquidity 0..{vpls[-1]} (beyond them each sigmoid returns its cap by design), at the factory's default configuration",
        truth="baseFee + sigmoidV(sigmoid1(vol) + sigmoid2(vol)), each sigmoid α/(1 + e^((β − x)/γ)) as AdaptiveFee's @notice states, real-valued, at the factory's default configuration",
        search=f"exhaustive: every volatility 0..{vol_hi} × every volumePerLiquidity 0..{vpls[-1]} ({(vol_hi + 1) * len(vpls):,} inputs) at AlgebraFactory's baseFeeConfiguration {c}",
    )


# ================================================================ 4. Aerodrome stable pool
def aero_check():
    t = src("aero")
    for s in ("amountIn -= (amountIn * IPoolFactory(factory).getFee(address(this), stable)) / 10000;",
              "uint256 y = reserveB - _get_y(amountIn + reserveA, xy, reserveB);",
              "return (y * (tokenIn == token0 ? decimals1 : decimals0)) / 1e18;",
              "if (_k(x0, y + 1) > xy) {"):
        assert s in t, s


class Aero:
    def __init__(self, dec0, dec1):
        self.d0, self.d1 = dec0, dec1

    def _k(self, x, y):
        _x = x * 10 ** 18 // self.d0
        _y = y * 10 ** 18 // self.d1
        _a = _x * _y // 10 ** 18
        _b = _x * _x // 10 ** 18 + _y * _y // 10 ** 18
        return _a * _b // 10 ** 18

    @staticmethod
    def _f(x0, y):
        _a = x0 * y // 10 ** 18
        _b = x0 * x0 // 10 ** 18 + y * y // 10 ** 18
        return _a * _b // 10 ** 18

    @staticmethod
    def _d(x0, y):
        return 3 * x0 * (y * y // 10 ** 18) // 10 ** 18 + (x0 * x0 // 10 ** 18) * x0 // 10 ** 18

    def _get_y(self, x0, xy, y):
        for _ in range(255):
            k = self._f(x0, y)
            if k < xy:
                d = self._d(x0, y)
                if d == 0:
                    raise Revert("div0")
                dy = (xy - k) * 10 ** 18 // d
                if dy == 0:
                    if k == xy:
                        return y
                    if self._k(x0, y + 1) > xy:
                        return y + 1
                    dy = 1
                y = y + dy
            else:
                d = self._d(x0, y)
                if d == 0:
                    raise Revert("div0")
                dy = (k - xy) * 10 ** 18 // d
                if dy == 0:
                    if k == xy or self._f(x0, y - 1) < xy:
                        return y
                    dy = 1
                if dy > y:
                    raise Revert("underflow")
                y = y - dy
        raise Revert("!y")

    def get_amount_out(self, amount_in, token0_in, r0, r1, fee):
        amount_in -= amount_in * fee // 10000
        xy = self._k(r0, r1)
        r0n, r1n = r0 * 10 ** 18 // self.d0, r1 * 10 ** 18 // self.d1
        ra, rb = (r0n, r1n) if token0_in else (r1n, r0n)
        amount_in = amount_in * 10 ** 18 // (self.d0 if token0_in else self.d1)
        yv = self._get_y(amount_in + ra, xy, rb)
        if yv > rb:
            raise Revert("underflow")
        return (rb - yv) * (self.d1 if token0_in else self.d0) // 10 ** 18


def aero_exact(amount_in, token0_in, r0, r1, fee, d0, d1):
    x, y = mp.mpf(r0) / d0, mp.mpf(r1) / d1
    k = x ** 3 * y + x * y ** 3
    a = mp.mpf(amount_in) * (1 - mp.mpf(fee) / 10000)
    if token0_in:
        xa, yb, db = x + a / d0, y, d1
    else:
        xa, yb, db = y + a / d1, x, d0
    # solve xa^3 Y + xa Y^3 = k for Y (monotone increasing in Y): Newton from the pre-trade balance
    Y = yb
    for _ in range(200):
        fy = xa ** 3 * Y + xa * Y ** 3 - k
        step = fy / (xa ** 3 + 3 * xa * Y ** 2)
        Y -= step
        if abs(step) < mp.mpf(10) ** (-100) * Y:
            break
    return (yb - Y) * db


def _aero_chunk(seed, n, normal):
    rng = random.Random(seed)
    w = Worst()
    kept = 0
    while kept < n:
        d0, d1 = rng.choice((10 ** 18, 10 ** 6)), rng.choice((10 ** 18, 10 ** 6))
        pool = Aero(d0, d1)
        tok = rng.random() < 0.5
        fee = rng.choice((5, 0, 1, 30, 300, rng.randint(0, 300)))
        if normal:
            d0, d1 = 10 ** rng.choice(DECS), 10 ** rng.choice(DECS)
            pool = Aero(d0, d1)
            # a stable pool: the other reserve within ×1000 of the same token amount, or equal
            t0 = logtok(rng)
            t1 = t0 if rng.random() < 0.3 else t0 * logprice(rng, 1e-3, 1e3)
            if not T_LO <= t1 <= T_HI:
                continue
            r0, r1 = units(t0, len(str(d0)) - 1, rng), units(t1, len(str(d1)) - 1, rng)
            tin = t0 if tok else t1
            amount = units(logtok(rng, T_LO, min(T_HI, 2 * tin)), len(str(d0 if tok else d1)) - 1, rng)
        else:
            t0 = loguni(rng, 1, 10 ** 12)
            t1 = t0 if rng.random() < 0.3 else loguni(rng, max(1, t0 // 1000), t0 * 1000)
            r0 = t0 * d0 + rng.randrange(d0)
            r1 = t1 * d1 + rng.randrange(d1)
            amount = loguni(rng, 10 ** 6, max(10 ** 6, (r0 if tok else r1) * 10))
        big = r0 >= d0 and r1 >= d1
        try:
            ret = pool.get_amount_out(amount, tok, r0, r1, fee)
        except Revert as e:
            w.revert(f"dec {d0},{d1} r0={r0} r1={r1} in={amount} token0In={tok} fee={fee}", str(e) + (" (reserves >= 1 token)" if big else ""))
            continue
        exact = aero_exact(amount, tok, r0, r1, fee, d0, d1)
        if exact < (1 if normal else 10 ** 6):
            continue
        kept += 1
        inp = f"decimals ({len(str(d0)) - 1}, {len(str(d1)) - 1}), reserve0={r0}, reserve1={r1}, amountIn={amount} of token{'0' if tok else '1'}, fee={fee}/10000"
        err = w.add(ret, exact, inp, other=amount)
        w.bucket_u(f"decimals {len(str(d0)) - 1}/{len(str(d1)) - 1}", abs(err), inp)
        if big:
            w.bucket_u("reserves >= 1 token each", abs(err), inp)
            w.bucket("reserves >= 1 token each", mpf_exact_digits(ret, exact), inp)
            if d0 == d1:
                w.bucket_u("reserves >= 1 token each, same decimals", abs(err), inp)
    return w


def row_aerodrome():
    aero_check()
    wn = parallel(_aero_chunk, 150_000, True)
    wd = parallel(_aero_chunk, 100_000, False)
    return dict(
        w=wn, wd=wd,
        normal_range="reserves 1..1e9 whole tokens within ×1000 of each other, amountIn 1 token..min(1e9 tokens, 2× the reserve in), decimals 6, 8 or 18 each, fee 0..3%; error in the smallest unit of the more valuable token",
        truth="the stable invariant x³y + xy³ = k on decimal-normalised reserves, solved exactly for the output after the input less fee/10000",
        search="normal: 150,000 random getAmountOut calls; domain: 100,000 with reserves to 1e12 tokens (1e30 units) and amountIn to 10× the reserve; fee 0..300 (the factory's MAX_FEE) with 5 the stable default; exact outputs below 1e6 skipped",
    )


# ================================================================ Curve: fetch-and-translate (no Curve text is stored here)
class VyRevert(Exception):
    pass


def _vdiv(a, b):
    if b == 0:
        raise VyRevert("div0")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _vmod(a, b):
    return a - b * _vdiv(a, b)


def _u(x):
    if x < 0 or x >= U256:
        raise VyRevert("uint256 range")
    return x


def _s(x):
    if not -(1 << 255) <= x < 1 << 255:
        raise VyRevert("int256 range")
    return x


def _copy(v):
    return list(v) if isinstance(v, (list, tuple)) else v


class _VyT(ast.NodeTransformer):
    def __init__(self, checked: str | None):
        self.checked = checked  # "_u", "_s" or None

    def _wrap(self, node):
        if self.checked is None:
            return node
        return ast.Call(func=ast.Name(self.checked, ast.Load()), args=[node], keywords=[])

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, (ast.Div, ast.FloorDiv)):
            return ast.Call(func=ast.Name("_vdiv", ast.Load()), args=[node.left, node.right], keywords=[])
        if isinstance(node.op, ast.Mod):
            return ast.Call(func=ast.Name("_vmod", ast.Load()), args=[node.left, node.right], keywords=[])
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Pow)):
            return self._wrap(node)
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        tgt_load = ast.parse(ast.unparse(node.target), mode="eval").body
        val = self.visit_BinOp(ast.BinOp(left=tgt_load, op=node.op, right=node.value))
        return ast.Assign(targets=[node.target], value=val)

    def visit_Assign(self, node):
        self.generic_visit(node)
        if isinstance(node.value, ast.Name):
            node.value = ast.Call(func=ast.Name("_copy", ast.Load()), args=[node.value], keywords=[])
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        f = node.func
        if isinstance(f, ast.Name):
            if f.id == "convert":
                return node.args[0]
            if f.id == "empty":  # empty(uint256) is 0, empty(DynArray[...]) is []
                a0 = node.args[0]
                if isinstance(a0, ast.Name) and re.fullmatch(r"u?int\d+", a0.id):
                    return ast.Constant(0)
                if isinstance(a0, ast.Name) and a0.id == "bool":
                    return ast.Constant(False)
                return ast.List(elts=[], ctx=ast.Load())
            if f.id == "unsafe_div":
                f.id = "_vdiv"
            elif f.id in ("unsafe_mul", "unsafe_add", "unsafe_sub"):
                op = {"unsafe_mul": ast.Mult(), "unsafe_add": ast.Add(), "unsafe_sub": ast.Sub()}[f.id]
                return ast.BinOp(left=node.args[0], op=op, right=node.args[1])
            elif f.id == "pow_mod256":
                return ast.Call(func=ast.Name("pow", ast.Load()), args=[node.args[0], node.args[1], ast.Constant(U256)], keywords=[])
            elif f.id == "isqrt":
                f.id = "_isqrt"
        return node

    def visit_Raise(self, node):
        self.generic_visit(node)
        msg = node.exc if node.exc is not None else ast.Constant("raise")
        return ast.Raise(exc=ast.Call(func=ast.Name("VyRevert", ast.Load()), args=[msg], keywords=[]), cause=None)

    def visit_Assert(self, node):
        self.generic_visit(node)
        msg = node.msg or ast.Constant("assert")
        return ast.If(test=ast.UnaryOp(op=ast.Not(), operand=node.test),
                      body=[ast.Raise(exc=ast.Call(func=ast.Name("VyRevert", ast.Load()), args=[msg], keywords=[]), cause=None)],
                      orelse=[])


def _split_top(s: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def vyper_module(text: str, funcs: dict[str, str | None], consts: dict, state: dict):
    """Translate the named Vyper functions (name -> '_u' | '_s' | None for overflow checks) into Python
    methods of a namespace object whose attributes are `state`; module constants are parsed from the file."""
    text = re.sub(r'"""[\s\S]*?"""', "", text)
    lines = [re.sub(r"#.*$", "", ln).rstrip() for ln in text.splitlines()]
    ns = {"VyRevert": VyRevert, "_vdiv": _vdiv, "_vmod": _vmod, "_u": _u, "_s": _s, "_copy": _copy,
          "_isqrt": math.isqrt, "max": max, "min": min, "abs": abs, "range": range, "len": len}
    ns.update(consts)
    for ln in lines:
        m = re.match(r"^(\w+)\s*:\s*(?:public\()?constant\(.+?\)\)?\s*=\s*(.+)$", ln)
        if m:
            try:
                ns[m.group(1)] = eval(m.group(2), {"__builtins__": {}}, ns)
            except Exception:
                pass
    ns.update(consts)
    obj = types.SimpleNamespace(**state)
    for name, checked in funcs.items():
        i = next(k for k, ln in enumerate(lines) if re.match(rf"^def {name}\(", ln))
        hdr = ""
        j = i
        while True:
            hdr += lines[j].strip() + " "
            if lines[j].rstrip().endswith(":") and hdr.count("(") == hdr.count(")"):
                break
            j += 1
        params = hdr[hdr.index("(") + 1:hdr.rindex(")", 0, hdr.rindex("->") if "->" in hdr else len(hdr))]
        names = []
        for p in _split_top(params):
            p = p.strip()
            if not p:
                continue
            nm = p.split(":")[0].strip()
            dflt = p.split("=", 1)[1].strip() if "=" in p else None
            names.append(f"{nm}={dflt}" if dflt else nm)
        body = []
        k = j + 1
        while k < len(lines) and (lines[k] == "" or lines[k].startswith((" ", "\t"))):
            ln = lines[k]
            ln = re.sub(r"^(\s*)for (\w+)\s*:\s*[\w\[\], ]+? in ", r"\1for \2 in ", ln)
            ln = re.sub(r"^(\s*)(\w+)\s*:\s*[A-Za-z_][\w\[\], ]*?\s*=\s*", r"\1\2 = ", ln)
            ln = re.sub(r",\s*bound\s*=\s*\w+\)", ")", ln)
            body.append(ln)
            k += 1
        code = f"def {name}(self, {', '.join(names)}):\n" + "\n".join(body) + "\n"
        tree = ast.parse(code)
        tree = ast.fix_missing_locations(_VyT(checked).visit(tree))
        ns["__py_" + name] = ast.unparse(tree)
        exec(compile(tree, f"<{name}>", "exec"), ns)
        fn = ns[name]
        setattr(obj, name, (lambda f: (lambda *a: f(obj, *a)))(fn))
    return obj, ns


# ================================================================ 3. Curve StableSwap (3pool get_dy, ng __exchange)
def _ng_obj(n_coins, amp, fee, offpeg):
    t = src("ng")
    state = dict(fee=fee, offpeg_fee_multiplier=offpeg, admin_balances=[0] * n_coins)
    consts = dict(N_COINS=n_coins, N_COINS_128=n_coins)
    obj, ns = vyper_module(t, {"get_D": "_u", "get_y": "_u", "_dynamic_fee": "_u", "__exchange": "_u"}, consts, state)
    obj._A = lambda: amp
    obj.upkeep_oracles = lambda *a: None
    return obj, ns


def _3pool_obj(amp, fee, balances):
    t = src("3pool")
    state = dict(fee=fee, balances=list(balances))
    obj, ns = vyper_module(t, {"_xp": "_u", "get_D": "_u", "get_y": "_u", "get_dy": "_u"}, {}, state)
    obj._A = lambda: amp
    return obj, ns


def stableswap_D(xp, Ann):
    """Real D of Ann·S + D = Ann·D + D^(n+1)/(n^n·Πx)."""
    n = len(xp)
    S = mp.fsum(xp)
    P = mp.fprod(xp)
    D = S
    for _ in range(300):
        f = Ann * S + D - Ann * D - D ** (n + 1) / (n ** n * P)
        fp = 1 - Ann - (n + 1) * D ** n / (n ** n * P)
        step = f / fp
        D -= step
        if abs(step) < mp.mpf(10) ** -105 * D:
            break
    return D


def stableswap_y(xp_others, D, Ann, n):
    """Real y with Ann·(S' + y) + D = Ann·D + D^(n+1)/(n^n·P'·y)."""
    S_ = mp.fsum(xp_others)
    P_ = mp.fprod(xp_others)
    b = S_ + D / Ann - D
    c = D ** (n + 1) / (n ** n * P_ * Ann)
    return (-b + mp.sqrt(b * b + 4 * c)) / 2


def _curve_bal(rng, dec, normal):
    if normal:  # 1 .. 1e9 whole tokens
        return loguni(rng, dec, 10 ** 9 * dec)
    return loguni(rng, 10 ** 3, 10 ** 10) * dec + rng.randrange(dec)


def _curve_normal(bal, decs):
    toks = [mp.mpf(b) / d for b, d in zip(bal, decs)]
    return all(d <= b <= 10 ** 9 * d for b, d in zip(bal, decs)) and max(toks) / min(toks) <= 10 ** 6


def _curve_chunk(seed, n, normal):
    rng = random.Random(seed)
    w = Worst()
    kept = 0
    while kept < n:
        which = rng.random()
        try:
            if which < 0.35:  # 3pool: DAI (18), USDC (6), USDT (6); RATES from the file
                amp = rng.choice((2000, rng.randint(1, 10 ** 6 - 1), rng.randint(1, 5000)))
                fee = rng.choice((1_000_000, 4_000_000, rng.randint(0, 5 * 10 ** 9)))
                dec = (10 ** 18, 10 ** 6, 10 ** 6)
                bal = [_curve_bal(rng, dec[k], normal) for k in range(3)]
                if rng.random() < 0.5:  # balanced in tokens
                    t = mp.mpf(bal[0]) / dec[0]
                    bal = [bal[0]] + [int(t * dec[k]) + rng.randrange(1000) for k in (1, 2)]
                if normal and not _curve_normal(bal, dec):
                    continue
                i, j = rng.sample(range(3), 2)
                dx = loguni(rng, dec[i], min(10 ** 9 * dec[i], bal[i] * 2)) if normal else loguni(rng, 10 ** 6, bal[i] * 2)
                obj, ns = _3pool_obj(amp, fee, bal)
                ret = obj.get_dy(i, j, dx)
                RATES = ns["RATES"]
                xp = [mp.mpf(RATES[k]) * bal[k] / 10 ** 18 for k in range(3)]
                Ann = mp.mpf(amp) * 3
                D = stableswap_D(xp, Ann)
                x = xp[i] + mp.mpf(dx) * RATES[i] / 10 ** 18
                others = [x if k == i else xp[k] for k in range(3) if k != j]
                y = stableswap_y(others, D, Ann, 3)
                exact = (xp[j] - y) * (1 - mp.mpf(fee) / 10 ** 10) * 10 ** 18 / RATES[j]
                label = f"3pool get_dy({i},{j},{dx}): balances={bal}, A={amp}, fee={fee}"
                dec_list = dec
                pool = "3pool"
                offpeg = 0
            else:  # stableswap-ng __exchange, 2..4 coins, 18 or 6 decimals, dynamic fee
                nc = rng.choice((2, 2, 3, 4))
                amp = rng.choice((200, 1000, rng.randint(1, 10 ** 6 - 1), rng.randint(1, 5000))) * 100  # A·A_PRECISION
                fee = rng.choice((1_000_000, 4_000_000, rng.randint(0, 5 * 10 ** 9)))
                offpeg = rng.choice((10 ** 10, 2 * 10 ** 10, 5 * 10 ** 10, rng.randint(10 ** 10, 10 ** 11)))
                if offpeg * fee > 5 * 10 ** 9 * 10 ** 10:
                    offpeg = 10 ** 10
                decs = [rng.choice(DECS) for _ in range(nc)]
                rates = [10 ** (36 - d) for d in decs]
                bal = [_curve_bal(rng, 10 ** decs[k], normal) for k in range(nc)]
                if rng.random() < 0.5:
                    t = mp.mpf(bal[0]) / 10 ** decs[0]
                    bal = [bal[0]] + [int(t * 10 ** decs[k]) + rng.randrange(1000) for k in range(1, nc)]
                if normal and not _curve_normal(bal, [10 ** d for d in decs]):
                    continue
                i, j = rng.sample(range(nc), 2)
                dx = loguni(rng, 10 ** decs[i], min(10 ** (9 + decs[i]), bal[i] * 2)) if normal else loguni(rng, 10 ** 6, bal[i] * 2)
                obj, ns = _ng_obj(nc, amp, fee, offpeg)
                P18 = ns["PRECISION"]
                xp_i = [rates[k] * bal[k] // P18 for k in range(nc)]
                x_int = xp_i[i] + dx * rates[i] // P18
                ret = obj.__exchange(x_int, list(xp_i), rates, i, j)
                xp = [mp.mpf(rates[k]) * bal[k] / P18 for k in range(nc)]
                Ann = mp.mpf(amp) * nc / ns["A_PRECISION"]
                D = stableswap_D(xp, Ann)
                x = xp[i] + mp.mpf(dx) * rates[i] / P18
                others = [x if k == i else xp[k] for k in range(nc) if k != j]
                y = stableswap_y(others, D, Ann, nc)
                FD = ns["FEE_DENOMINATOR"]
                if offpeg <= FD:
                    fee_e = mp.mpf(fee)
                else:
                    xpi, xpj = (xp[i] + x) / 2, (xp[j] + y) / 2
                    fee_e = mp.mpf(offpeg) * fee / ((mp.mpf(offpeg) - FD) * 4 * xpi * xpj / (xpi + xpj) ** 2 + FD)
                exact = (xp[j] - y) * (1 - fee_e / FD) * P18 / rates[j]
                label = f"ng ({nc} coins, decimals {decs}) exchange {i}->{j} dx={dx}: balances={bal}, A·100={amp}, fee={fee}, offpeg={offpeg}"
                dec_list = [10 ** d for d in decs]
                pool = "ng"
        except VyRevert as e:
            dl = (10 ** 18, 10 ** 6, 10 ** 6) if which < 0.35 else [10 ** d for d in decs]
            big = all(b >= d for b, d in zip(bal, dl))
            w.revert(f"balances={bal}, {i}->{j}, dx={dx}, A={amp}", f"{'3pool' if which < 0.35 else 'ng'}: {e}" + (" (balances >= 1 token)" if big else ""))
            continue
        if exact < (1 if normal else 10 ** 6):
            continue
        kept += 1
        err = w.add(ret, exact, label, other=dx)
        if all(b >= d for b, d in zip(bal, dec_list)):
            w.bucket_u("balances >= 1 token each", abs(err), label)
            w.bucket("balances >= 1 token each", mpf_exact_digits(ret, exact), label)
        w.bucket(pool, mpf_exact_digits(ret, exact), label)
        w.bucket_u(pool, abs(err), label)
        if pool == "ng" and offpeg <= 10 ** 10:
            w.bucket_u("ng, static fee (offpeg multiplier <= 1e10)", abs(err), label)
    return w


def row_curve_stableswap():
    src("3pool"), src("ng")
    wn = parallel(_curve_chunk, 150_000, True)
    wd = parallel(_curve_chunk, 100_000, False)
    return dict(
        w=wn, wd=wd,
        normal_range="balances 1..1e9 whole tokens within ×1e6 of each other, dx 1 token..min(1e9 tokens, 2× the balance in), error in the smallest unit of the more valuable coin; reverts excluded, graded on precision (balanced in tokens or not), coins of 6, 8 or 18 decimals (3pool: 18, 6, 6), A to 1e6, fee and offpeg multiplier within the pool's caps",
        truth="the StableSwap invariant Ann·Σx + D = Ann·D + D^(n+1)/(n^n·Πx) (the contracts' A is the paper's A·n^(n−1), so Ann = A·n), D and y solved exactly; output (x_j − y)·(1 − fee)·1e18/rate_j, with ng's documented dynamic fee at the mid-trade balances",
        search="normal: 150,000 random swaps through the fetched source translated to Python: 3pool get_dy (35%; DAI/USDC/USDT rates from the file) and stableswap-ng __exchange (2, 3 or 4 coins of 18 or 6 decimals); domain: 100,000 with balances 1e3..1e10 tokens and dx to 2× the balance; exact outputs below 1e6 skipped",
    )


# ================================================================ 11. Curve twocrypto-ng get_y
def _two_obj():
    c_ns = types.SimpleNamespace()
    ct = src("twoconst")
    env = {}
    for ln in ct.splitlines():
        m = re.match(r"^(\w+)\s*:\s*(?:public\()?constant\(.+?\)\)?\s*=\s*([^#]+)", ln)
        if m:
            env[m.group(1)] = eval(m.group(2), {"__builtins__": {}}, env)
    for k, v in env.items():
        setattr(c_ns, k, v)
    t = src("twomath")
    obj, ns = vyper_module(t, {"_snekmate_log_2": "_u", "_cbrt": None, "_newton_y": "_u", "newton_y": "_u", "get_y": "_s"},
                           {"c": c_ns, "N_COINS": env["N_COINS"]}, {})
    return obj, env


def cryptoswap_y(ANN, gamma, xj, D, A_MULT, y0):
    """Real y of K·D·(x+y) + x·y = K·D² + (D/2)², K = A·K0·γ²/(γ+1−K0)², K0 = 4xy/D², ANN = A·N^N·A_MULTIPLIER."""
    A = mp.mpf(ANN) / A_MULT / 4  # ANN = A·N^N·A_MULTIPLIER, N = 2
    g = mp.mpf(gamma) / 10 ** 18
    x = mp.mpf(xj)
    D = mp.mpf(D)

    def F(y):
        K0 = 4 * x * y / D ** 2
        K = A * K0 * g ** 2 / (g + 1 - K0) ** 2
        return K * D * (x + y) + x * y - K * D ** 2 - D ** 2 / 4

    return mp.findroot(F, mp.mpf(y0), tol=mp.mpf(10) ** -100, maxsteps=200)


def _two_chunk(seed, n, normal):
    rng = random.Random(seed)
    obj, c = _two_obj()
    w = Worst()
    kept = 0
    while kept < n:
        ANN = rng.choice((loguni(rng, c["MIN_A"], c["MAX_A"]), 400000, 4 * 10000 * rng.randint(1, 1000)))
        gamma = rng.choice((loguni(rng, c["MIN_GAMMA"], c["MAX_GAMMA"]), 145000000000000, 11809167828997, rng.randint(c["MIN_GAMMA"], c["MAX_GAMMA"])))
        D = loguni(rng, 10 ** 17, 2 * N_HI if normal else 10 ** 33)
        lim = 100 * 10 ** 18 if gamma <= c["MAX_GAMMA_SMALL"] else 100 * 10 ** 18 * c["MAX_GAMMA_SMALL"] // gamma
        # x_j such that K0_i = 2e18·x_j/D sits in [1e36/lim, lim]
        k0 = math.exp(rng.uniform(math.log(1e36 / lim), math.log(lim)))
        if rng.random() < 0.3:
            k0 = 1e18 * math.exp(rng.uniform(-0.3, 0.3))
        xj = max(1, int(k0 * D / 2e18))
        if normal and not 10 ** 18 <= xj <= 10 ** 27:
            continue
        i = rng.randint(0, 1)
        x = [0, 0]
        x[1 - i] = xj
        fn = rng.random() < 0.5
        try:
            ret = obj.get_y(ANN, gamma, x, D, i)[0] if fn else obj.newton_y(ANN, gamma, x, D, i)
        except VyRevert:
            continue
        try:
            exact = cryptoswap_y(ANN, gamma, xj, D, c["A_MULTIPLIER"], ret)
        except (ValueError, ZeroDivisionError):
            continue
        kept += 1
        inp = f"{'get_y' if fn else 'newton_y'}(ANN={ANN}, gamma={gamma}, x_j={xj}, D={D}, i={i})"
        w.add(ret, exact, inp)
        w.bucket("get_y" if fn else "newton_y", mpf_exact_digits(ret, exact), inp)
    return w


def row_curve_twocrypto():
    src("twomath"), src("twoconst")
    wn = parallel(_two_chunk, 150_000, True)
    wd = parallel(_two_chunk, 100_000, False)
    return dict(
        w=wn, wd=wd,
        normal_range="D up to 2e27 and x_j 1..1e9 whole tokens (1e18..1e27 in price-scaled units), x_j/D inside the contract's asserted band, A and gamma over their whole allowed ranges",
        truth="the Cryptoswap invariant (N = 2): K·D·(x + y) + x·y = K·D² + (D/2)², K = A·K0·γ²/(γ + 1 − K0)², K0 = 4xy/D², A = ANN/(A_MULTIPLIER·N^N); y solved exactly",
        search="normal: 150,000 random calls, half get_y (the cubic, with its Newton fallback) and half newton_y, through the fetched source translated to Python (ANN log-uniform over [MIN_A, MAX_A], gamma log-uniform or uniform over [MIN_GAMMA, MAX_GAMMA], x_j across the asserted K0 band or near balance); domain: 100,000 with D to 1e33 (the asserted range); calls the contract's own safety asserts reject are outside the domain",
    )


# ================================================================ table, JSON
ROWS = {
    "uniswap-v2-swap": row_uniswap_v2,
    "uniswap-v3-swap": row_uniswap_v3_swap,
    "curve-stableswap": row_curve_stableswap,
    "aerodrome-stable": row_aerodrome,
    "trader-joe-lb-swap": row_trader_joe_lb_swap,
    "uniswap-v3-tickmath": row_uniswap_v3_tickmath,
    "trader-joe-lb-price": row_trader_joe_lb_price,
    "uniswap-v3-twap": row_uniswap_v3_twap,
    "pendle-market": row_pendle,
    "gmx-v2-price-impact": row_gmx,
    "curve-twocrypto-get-y": row_curve_twocrypto,
    "algebra-v1-fee": row_algebra,
    "maverick-v2-tickmath": row_maverick_tickmath,
}


SWAP_ROWS = {"uniswap-v2-swap", "uniswap-v3-swap", "curve-stableswap", "aerodrome-stable", "trader-joe-lb-swap"}


def digits_lost(w) -> float:
    """The coordinator's measure (2026-10-30): log10(max(worst_units, 1)); correctly rounded = 0."""
    return math.log10(max(w.u, 1.0))


def chip(w) -> str:
    dl = digits_lost(w)
    if dl == 0:
        return "≤ ½ unit" if w.u <= 0.5 else "< 1 unit"
    return f"{dl:.1f} lost" if dl < 10 else f"{dl:.0f} lost"


def summary(w, swap=False):
    u, u_in = (w.uc, w.uc_in) if swap else (w.u, w.u_in)
    out = dict(
        worst_digits=round(w.d, 2) if math.isfinite(w.d) else None,
        worst_units=float(f"{u:.4g}"),
        digits_lost=round(math.log10(max(u, 1.0)), 2),
        worst_input=str(u_in),
        held_floor={str(H): (round(w.held[H][0], 2) if math.isfinite(w.held[H][0]) else None) for H in HELD},
        held_floor_input={str(H): w.held[H][1] for H in HELD},
        short18=round(max(w.s18[0], 0.0), 2),
        short18_input=w.s18[1],
        short18_format_digits=round(w.s18[2], 2) if w.s18[2] is not None else None,
        correctly_rounded=bool(u <= 0.5 or (u < 1 and len(w.signs - {"0"}) == 1)),
        worst_digits_input=str(w.d_in),
    )
    if swap:
        out.update(worst_units_output_token=float(f"{w.u:.4g}"), worst_units_output_token_input=str(w.u_in))
    out.update(direction="".join(sorted(w.signs)) or "exact", inputs=w.n)
    return out


def main(argv):
    rows = argv or list(ROWS)
    out = {}
    print(f"{'row':26} {'lost':>6} {'units':>11} {'digits':>7} | {'domain lost':>11} {'digits':>7}")
    for rid in rows:
        r = ROWS[rid]()
        w, wd = r["w"], r["wd"]
        swap = rid in SWAP_ROWS
        row = summary(w, swap)
        row.update(chip=f"{row['digits_lost']:.1f} lost" if row["digits_lost"] else "0 lost",
                   normal_range=r["normal_range"], truth=r["truth"], search=r["search"])
        row["domain_worst"] = summary(wd, swap)
        if r.get("extra"):
            row["extra"] = r["extra"]
        notes = {}
        for src_w in (w, wd):
            for k, v in sorted(src_w.note.items()):
                if k in notes:
                    continue
                if k in ("digits_at", "config", "ranges"):
                    notes[k] = v[1]
                elif k.startswith("units: "):
                    notes[k] = {"worst_units": float(f"{-v[0]:.4g}"), "digits_lost": round(math.log10(max(-v[0], 1.0)), 2), "input": v[1]}
                elif v[1] is not None:
                    notes[k] = {"digits": round(v[0], 2), "input": v[1]}
                else:
                    notes[k] = round(v[0], 2)
        if notes:
            row["notes"] = notes
        if (wd.reverts or w.reverts) and rid != "curve-stableswap":  # the user: Curve graded on precision only
            row["reverts"] = {"normal": w.reverts, "normal_why": getattr(w, "why", {}), "domain": wd.reverts,
                              "domain_why": getattr(wd, "why", {}),
                              "example": {**getattr(wd, "why_in", {}), **getattr(w, "why_in", {})}}
        out[rid] = row
        hf = row["held_floor"]
        print(f"{rid:26} {row['digits_lost']:6.2f} {row['worst_units']:11.4g} {w.d:7.2f} | {row['domain_worst']['digits_lost']:11.2f}"
              f"  held {hf['25']}/{hf['14']}/{hf['10']}  short18 {row['short18']} (fmt {row['short18_format_digits']}) "
              f"CR={row['correctly_rounded']}   {str(row['short18_input'])[:120]}")
        sys.stdout.flush()
    if not argv:
        doc = ("Worst-case measurement of the exchange rows of tiers.json (2026-10-30). Each function's integer arithmetic is "
               "transcribed from its pinned source and compared with the exact value of the formula the protocol documents "
               "(mpmath, 120 digits). The row's number is digits_lost = log10(max(worst_units, 1)) over NORMAL inputs "
               "(normal_range; token prices 1e-6..1e6, swap amounts and every reserve 1..1e9 whole tokens, TWAP windows 60 s..1 day): "
               "worst_units is the largest |returned − exact| in units of the result's last place (for a swap: the smallest unit of "
               "the more valuable token of the pair, i.e. the error divided by max(1, average price); worst_units_output_token "
               "keeps the output token's own count), so a correctly rounded result loses 0. held_floor[H] is the fewest correct "
               "digits over the normal inputs whose exact value has at least H digits in the result's unit (null if none). "
               "short18 (the user's one blended number) is the worst over the same inputs of max(0, min(format digits, 18) − digits "
               "held), format digits = log10(|exact|/unit) in the unit errors are counted in; correctly_rounded is true iff every "
               "normal result is within 0.5 unit, or under 1 unit in one direction. "
               "worst_digits = min −log10(|returned − exact|/|exact|) on the same inputs. domain_worst holds the same figures over "
               "the function's whole documented domain. No tier is assigned here. "
               "Generated by scripts/tiers/measure_exchanges.py; method per row in talk/briefs/tiers-provenance.md, "
               "'Worst-case measurement (2026-10-30)'.")
        OUT_JSON.write_text(json.dumps({"_doc": doc, "rows": out}, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    else:
        print(json.dumps(out, indent=1, ensure_ascii=False))



if __name__ == "__main__":
    main(sys.argv[1:])

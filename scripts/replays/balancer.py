#!/usr/bin/env python3
"""Replay of the Balancer V2 Composable Stable Pool exploit (Ethereum, 3 Nov 2025)
from the attack transaction's own integers.

    uv run scripts/replays/balancer.py fetch     # (network) trace + archive state + verified source -> balancer.json
    uv run scripts/replays/balancer.py           # offline: score -> forge harness -> balancer.json + docs/benchmarks/replay-balancer.md
    uv run scripts/replays/balancer.py --score   # re-score the last harness log only

`fetch` is read-only: debug_traceTransaction (callTracer) and eth_call at
block - 1 on keyless public endpoints, and the verified source from
Routescan's Etherscan-compatible API. It never signs or sends anything.

The attack transaction deploys a contract whose constructor runs one Vault
batchSwap against each of two pools (osETH/WETH, then wstETH/WETH). Every
pool call in it is an `onSwap` from the Vault with the pool's raw balances
and the requested amount; its return value is the amount the pool charged.
Those calls are the integers this replay is built on.

The micro-swap phase of each batchSwap (every swap that involves neither
BPT) is replayed through:
  deployed  StableMath as verified on Etherscan, _upscale = mulDown (bit-exact
            against every on-chain return; Python here and the Foundry test)
  mulUp     the same, with the given-out amount upscaled by mulUp (V3's fix)
  fp127     FP127 (127.128 fixed point) for the upscaled amounts and the pool
            maths, Newton run to FP127's own grid, ceil to token wei at the end
  fp19     FP19 (256-bit float), the same algorithm on FP19's grid
  exact     exact rationals for the upscaling, the invariant and balance roots
            at 200 digits (mpmath), ceil to token wei at the end
  nearest   exact, rounded to nearest at the wei boundary (sensitivity only)
Each model prices every call of the phase on that call's own on-chain balances
and amount; the change in the true invariant (exact root, exact rates) says
what each call would have cost the pool. The attacker's adaptive plan (drain
the rate token to `leave` wei, take `leave - 1` out, swap the recorded WETH
amount back) is also replayed on each model's own balances, which reproduces
the on-chain sequence under deployed pricing and records where it breaks under
the others. The forge harness (test/replays/Balancer.t.sol) runs deployed,
mulUp, fp127 and fp19 and asserts them; this script scores its log.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from mpmath import mp, mpf, sqrt as msqrt, log10, nstr

mp.dps = 200

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "replays"
OUT = HERE / "balancer.json"
MD = ROOT / "docs" / "benchmarks" / "replay-balancer.md"
LOG = ROOT / "out" / "replays" / "balancer.log"
TEST = "test/replays/Balancer.t.sol"

TX = "0x6ed07db1a9fe5c0794d44cd36081d6a6df103fab868cdd75d581e3bd23bc9742"
VAULT = "0xba12222222228d8ba445958a75a0704d566bf2c8"
POOLS = {"osETH": "0xdacf5fa19b1f720111609043ac67a9818262850c",
         "wstETH": "0x93d199263632a4ef4bb438f1feb99e57b4b5f0bd"}
SYMBOLS = {"0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
           "0xf1c9acdc66974dfb6decb12aa385b9cd01190e38": "osETH",
           "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0": "wstETH",
           POOLS["osETH"]: "osETH/WETH-BPT", POOLS["wstETH"]: "wstETH-WETH-BPT"}
# Keyless public endpoints. Tenderly's gateway serves archive eth_call but rate-limits
# debug_traceTransaction; dRPC's free tier serves both.
TRACE_RPCS = ["https://eth.drpc.org", "https://mainnet.gateway.tenderly.co"]
STATE_RPCS = ["https://mainnet.gateway.tenderly.co", "https://eth.drpc.org"]
SOURCE_API = "https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api"

ONE = 10 ** 18
AMP_PRECISION = 1000
SEL = {"onSwap": "0x01ec954a", "batchSwap": "0x945bcec9", "getScalingFactors": "0x1dd746ea",
       "getAmplificationParameter": "0x6daccffa", "getSwapFeePercentage": "0x55c67628", "getRate": "0x679aefce",
       "getActualSupply": "0x876f303b", "getPoolId": "0x38fff2d0", "getBptIndex": "0x82687a56",
       "getRateProviders": "0x238a2d59", "updateTokenRateCache": "0x2df2c7c0", "getPoolTokens": "0xf94d4668",
       "version": "0x54fd4d50", "getTokenRateCache": "0x7f1260d1"}

# The verified files and functions the replay transcribes (file:line from the Etherscan-verified
# standard-JSON input of both pools; the two pools' files are byte-identical).
CITE = [
    ("@balancer-labs/v2-pool-utils/contracts/BaseGeneralPool.sol", "function onSwap("),
    ("@balancer-labs/v2-pool-utils/contracts/BaseGeneralPool.sol", "function _swapGivenOut("),
    ("contracts/ComposableStablePool.sol", "function _swapGivenOut("),
    ("contracts/ComposableStablePool.sol", "function _onRegularSwap("),
    ("@balancer-labs/v2-pool-utils/contracts/BasePool.sol", "function _addSwapFeeAmount("),
    ("@balancer-labs/v2-pool-utils/contracts/BasePool.sol", "function _upscale("),
    ("@balancer-labs/v2-pool-utils/contracts/BasePool.sol", "function _upscaleArray("),
    ("@balancer-labs/v2-pool-utils/contracts/BasePool.sol", "function _downscaleUp("),
    ("contracts/StableMath.sol", "function _calculateInvariant("),
    ("contracts/StableMath.sol", "function _calcInGivenOut("),
    ("contracts/StableMath.sol", "function _getTokenBalanceGivenInvariantAndAllOtherBalances("),
    ("@balancer-labs/v2-solidity-utils/contracts/math/FixedPoint.sol", "function mulDown("),
    ("@balancer-labs/v2-solidity-utils/contracts/math/FixedPoint.sol", "function mulUp("),
    ("@balancer-labs/v2-solidity-utils/contracts/math/FixedPoint.sol", "function divUp("),
    ("@balancer-labs/v2-solidity-utils/contracts/math/FixedPoint.sol", "function complement("),
    ("@balancer-labs/v2-solidity-utils/contracts/math/Math.sol", "function divUp("),
]


# ---------------------------------------------------------------- network (fetch only)

def _rpc_any(urls, method, params):
    sys.path.insert(0, str(ROOT / "scripts" / "accrual"))
    from rpc import rpc  # the repo's keyless JSON-RPC helper
    err = None
    for u in urls:
        try:
            return rpc(u, method, params), u
        except Exception as e:  # rate limits differ by endpoint; try the next one
            err = e
    raise RuntimeError(f"{method}: {err}")


def words(h: str) -> list[int]:
    h = h[2:] if h.startswith("0x") else h
    return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]


def signed(x: int) -> int:
    return x - 2 ** 256 if x >= 2 ** 255 else x


def decode_onswap(inp: str, out: str) -> dict:
    w = words(inp[10:])
    ro, bo = w[0] // 32, w[1] // 32
    n = w[bo]
    return {"kind": w[ro], "tokenIn": "0x%040x" % w[ro + 1], "tokenOut": "0x%040x" % w[ro + 2], "amount": w[ro + 3],
            "balances": w[bo + 1:bo + 1 + n], "i": w[2], "j": w[3], "result": int(out, 16)}


def calls(node):
    yield node
    for k in node.get("calls", []):
        yield from calls(k)


def fetch() -> None:
    tx, _ = _rpc_any(STATE_RPCS, "eth_getTransactionByHash", [TX])
    rc, _ = _rpc_any(STATE_RPCS, "eth_getTransactionReceipt", [TX])
    block = int(rc["blockNumber"], 16)
    blk, _ = _rpc_any(STATE_RPCS, "eth_getBlockByNumber", [hex(block), False])
    trace, trace_url = _rpc_any(TRACE_RPCS, "debug_traceTransaction", [TX, {"tracer": "callTracer"}])
    trace_sha = hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    prev = hex(block - 1)

    def call(to, data):
        r, u = _rpc_any(STATE_RPCS, "eth_call", [{"to": to, "data": data}, prev])
        return r

    out = {"about": "Balancer V2 Composable Stable Pool exploit, Ethereum mainnet, replayed from the attack transaction's "
                    "own integers. Written by scripts/replays/balancer.py; read by test/replays/Balancer.t.sol.",
           "provenance": {"tx": TX, "block": block, "blockHash": rc["blockHash"],
                          "timestamp": datetime.fromtimestamp(int(blk["timestamp"], 16), timezone.utc).isoformat(),
                          "from": tx["from"], "created": rc["contractAddress"], "status": int(rc["status"], 16),
                          "gasUsed": int(rc["gasUsed"], 16), "vault": VAULT,
                          "traceEndpoint": trace_url, "traceTracer": "callTracer", "traceSha256": trace_sha,
                          "stateEndpoint": STATE_RPCS[0], "stateBlock": block - 1, "sourceApi": SOURCE_API,
                          "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
           "pools": {}}

    for name, addr in POOLS.items():
        p: dict = {"address": addr}
        # -- in-transaction calls to the pool (and its batchSwap), in order
        swaps, reads, bs = [], [], None
        for c in calls(trace):
            to, sel = c.get("to", "").lower(), c.get("input", "")[:10]
            if to == addr and sel == SEL["onSwap"]:
                swaps.append(decode_onswap(c["input"], c["output"]))
            elif to == addr and sel in (SEL["getScalingFactors"], SEL["getRate"], SEL["getAmplificationParameter"],
                                        SEL["getSwapFeePercentage"], SEL["getActualSupply"]):
                reads.append((len(swaps), sel, c.get("output")))
            elif to == addr and sel == SEL["updateTokenRateCache"]:
                prov = [k for k in c.get("calls", []) if k.get("input", "")[:10] == SEL["getRate"]]
                p["rateCacheUpdatedInTx"] = {"token": "0x" + c["input"][-40:], "provider": prov[0]["to"],
                                             "providerRate": int(prov[0]["output"], 16)}
            elif to == VAULT and sel == SEL["batchSwap"] and bs is None:
                kids = [k for k in c.get("calls", []) if k.get("to", "").lower() == addr]
                if kids:
                    w = words(c["output"])
                    bs = [signed(x) for x in w[2:2 + w[1]]]
                    f = words(c["input"][10:10 + 64 * 7])
                    p["batchSwapFunds"] = {"kind": f[0], "sender": "0x%040x" % f[3], "fromInternalBalance": bool(f[4]),
                                           "recipient": "0x%040x" % f[5], "toInternalBalance": bool(f[6])}
        # the swaps' rates: the attacker's own getScalingFactors() read, after updateTokenRateCache, before any swap
        sf_tx = [r for r in reads if r[1] == SEL["getScalingFactors"]][-1]
        assert sf_tx[0] == 0
        p["scalingFactorsInTx"] = words(sf_tx[2])[2:]
        amp = words([r for r in reads if r[1] == SEL["getAmplificationParameter"]][0][2])
        p["amp"] = {"value": amp[0], "isUpdating": bool(amp[1]), "precision": amp[2]}
        p["swapFeePercentage"] = words([r for r in reads if r[1] == SEL["getSwapFeePercentage"]][0][2])[0]
        rates = [(r[0], int(r[2], 16)) for r in reads if r[1] == SEL["getRate"]]
        p["bptRateBefore"] = [v for k, v in rates if k == 0][0]
        p["bptRateAfter"] = [v for k, v in rates if k == len(swaps)][-1]
        p["actualSupplyBefore"] = int([r for r in reads if r[1] == SEL["getActualSupply"]][0][2], 16)
        p["batchSwapAssetDeltas"] = bs
        # -- archive state at block - 1
        pid = call(addr, SEL["getPoolId"])
        p["poolId"] = pid
        w = words(call(VAULT, SEL["getPoolTokens"] + pid[2:]))
        n = w[3]
        p["tokens"] = ["0x%040x" % x for x in w[4:4 + n]]
        p["symbols"] = [SYMBOLS.get(t, t) for t in p["tokens"]]
        p["balancesBlockMinus1"] = w[5 + n:5 + 2 * n]
        p["lastChangeBlock"] = w[2]
        p["bptIndex"] = words(call(addr, SEL["getBptIndex"]))[0]
        p["scalingFactorsBlockMinus1"] = words(call(addr, SEL["getScalingFactors"]))[2:]
        p["rateProviders"] = ["0x%040x" % x for x in words(call(addr, SEL["getRateProviders"]))[2:]]
        prov = [x for x in p["rateProviders"] if int(x, 16)][0]
        p["providerRateBlockMinus1"] = words(call(prov, SEL["getRate"]))[0]
        a = words(call(addr, SEL["getAmplificationParameter"]))
        p["ampBlockMinus1"] = {"value": a[0], "isUpdating": bool(a[1]), "precision": a[2]}
        p["swapFeeBlockMinus1"] = words(call(addr, SEL["getSwapFeePercentage"]))[0]
        p["bptRateBlockMinus1"] = words(call(addr, SEL["getRate"]))[0]
        v = call(addr, SEL["version"])
        vw = bytes.fromhex(v[2:])
        ln = int.from_bytes(vw[32:64], "big")
        p["version"] = vw[64:64 + ln].decode()
        p["swaps"] = [{"kind": s["kind"], "i": s["i"], "j": s["j"], "amount": str(s["amount"]),
                       "balances": [str(b) for b in s["balances"]], "amountIn": str(s["result"])} for s in swaps]
        assert all(s["kind"] == 1 for s in swaps), "every swap in the attack is GIVEN_OUT"
        assert [int(b) for b in p["swaps"][0]["balances"]] == p["balancesBlockMinus1"]
        # -- verified source
        src = _http(f"{SOURCE_API}?module=contract&action=getsourcecode&address={addr}")["result"][0]
        std = json.loads(src["SourceCode"][1:-1])
        files = {k: v["content"] for k, v in std["sources"].items()}
        p["source"] = {"contractName": src["ContractName"], "compiler": src["CompilerVersion"],
                       "optimizer": {"enabled": src["OptimizationUsed"] == "1", "runs": int(src["Runs"])},
                       "files": {f: hashlib.sha256(files[f].encode()).hexdigest() for f in sorted({c[0] for c in CITE})},
                       "cites": {f"{f.split('/')[-1]}:{fn[9:-1]}": f"{f}:{_lines(files[f], fn)}" for f, fn in CITE}}
        out["pools"][name] = p
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: block {block}, trace sha256 {trace_sha[:16]}..")


def _http(url):
    sys.path.insert(0, str(ROOT / "scripts" / "accrual"))
    from rpc import http_json
    return http_json(url)


def _lines(text: str, fn: str) -> str:
    lines = text.split("\n")
    s = next(i for i, l in enumerate(lines) if fn in l)
    depth, seen = 0, False
    for e in range(s, len(lines)):
        depth += lines[e].count("{") - lines[e].count("}")
        seen = seen or "{" in lines[e]
        if seen and depth == 0:
            return f"{s + 1}-{e + 1}"
    raise ValueError(fn)


# ---------------------------------------------------------------- the deployed arithmetic (Python port)

def mul_down(a, b): return a * b // ONE
def mul_up(a, b): return 0 if a * b == 0 else (a * b - 1) // ONE + 1
def fdiv_up(a, b): return 0 if a == 0 else (a * ONE - 1) // b + 1
def div_up(a, b): return 0 if a == 0 else 1 + (a - 1) // b


def invariant_int(amp, bal):
    """StableMath._calculateInvariant; returns (D, iterations)."""
    s, n = sum(bal), len(bal)
    d, ann = s, amp * n
    for it in range(255):
        dp = d
        for b in bal:
            dp = dp * d // (b * n)
        prev = d
        d = ((ann * s // AMP_PRECISION + dp * n) * d) // ((ann - AMP_PRECISION) * d // AMP_PRECISION + (n + 1) * dp)
        if abs(d - prev) <= 1:
            return d, it + 1
    raise RuntimeError("STABLE_INVARIANT_DIDNT_CONVERGE")


def balance_int(amp, bal, d, k):
    """StableMath._getTokenBalanceGivenInvariantAndAllOtherBalances; returns (y, iterations, c, b)."""
    n = len(bal)
    ann = amp * n
    s, pd = bal[0], bal[0] * n
    for j in range(1, n):
        pd = pd * bal[j] * n // d
        s += bal[j]
    s -= bal[k]
    inv2 = d * d
    c = div_up(inv2, ann * pd) * AMP_PRECISION * bal[k]
    b = s + d // ann * AMP_PRECISION
    y = div_up(inv2 + c, d + b)
    for it in range(255):
        p = y
        y = div_up(y * y + c, y * 2 + b - d)
        if abs(y - p) <= 1:
            return y, it + 1, c, b
    raise RuntimeError("STABLE_GET_BALANCE_DIDNT_CONVERGE")


def swap_int(pool, raw, i, j, amount, up=mul_down):
    """BaseGeneralPool._swapGivenOut -> ComposableStablePool._onRegularSwap -> StableMath._calcInGivenOut."""
    sf, bpt = pool["sf"], pool["bpt"]
    scaled = [mul_down(raw[k], sf[k]) for k in range(3)]
    a = up(amount, sf[j])
    bal = [scaled[k] for k in range(3) if k != bpt]
    ii, jj = i - (i > bpt), j - (j > bpt)
    d, itd = invariant_int(pool["amp"], bal)
    bal[jj] -= a
    y, ity, c, b = balance_int(pool["amp"], bal, d, ii)
    bal[jj] += a
    ain = y - bal[ii] + 1
    ain = fdiv_up(ain, sf[i])
    ain = fdiv_up(ain, ONE - pool["fee"])
    return ain, {"D": d, "itD": itd, "y": y, "itY": ity, "a": a, "bal": bal, "c": c, "b": b, "ii": ii, "jj": jj}


# ---------------------------------------------------------------- exact (rationals, roots at 200 digits)

def annp(pool):
    return Fraction(pool["amp"] * 2, AMP_PRECISION)


def invariant_exact(A, b0, b1):
    """Root of D^3/(4 b0 b1) + (A - 1) D - A (b0 + b1) = 0 (n = 2), A = Ann / AMP_PRECISION."""
    b0, b1, A = mpf(b0.numerator) / b0.denominator, mpf(b1.numerator) / b1.denominator, mpf(A.numerator) / A.denominator
    d = b0 + b1
    for _ in range(400):
        f = d ** 3 / (4 * b0 * b1) + (A - 1) * d - A * (b0 + b1)
        fp = 3 * d ** 2 / (4 * b0 * b1) + (A - 1)
        nd = d - f / fp
        if abs(nd - d) <= abs(nd) * mpf(10) ** (-190):
            return nd
        d = nd
    raise RuntimeError("exact invariant")


def balance_exact(A, d, other):
    """Positive root x of x^2 + (o + D/A - D) x - D^3/(4 o A) = 0."""
    A = mpf(A.numerator) / A.denominator
    o = other if isinstance(other, mpf) else mpf(other.numerator) / other.denominator
    bb = o + d / A - d
    c = d ** 3 / (4 * o * A)
    return (-bb + msqrt(bb * bb + 4 * c)) / 2


def frac_mpf(x):
    return mpf(x.numerator) / x.denominator if isinstance(x, Fraction) else mpf(x)


def swap_exact(pool, raw, i, j, amount):
    sf, bpt = pool["sf"], pool["bpt"]
    q = [Fraction(sf[k], ONE) for k in range(3)]
    scaled = [raw[k] * q[k] for k in range(3)]
    bal = [scaled[k] for k in range(3) if k != bpt]
    ii, jj = i - (i > bpt), j - (j > bpt)
    A = annp(pool)
    d = invariant_exact(A, bal[0], bal[1])
    other = bal[jj] - amount * q[j]
    y = balance_exact(A, d, other)
    need = (y - frac_mpf(bal[ii])) / frac_mpf(q[i]) / (1 - mpf(pool["fee"]) / ONE)
    return int(mp.ceil(need)), {"D": d, "y": y, "need": need}


def true_invariant(pool, raw):
    q = [Fraction(pool["sf"][k], ONE) for k in range(3)]
    bal = [raw[k] * q[k] for k in range(3) if k != pool["bpt"]]
    return invariant_exact(annp(pool), bal[0], bal[1])


# ---------------------------------------------------------------- the micro-swap phase

KINDS = ("drain", "micro", "restore")


def pool_params(p):
    return {"sf": p["scalingFactorsInTx"], "amp": p["amp"]["value"], "fee": p["swapFeePercentage"], "bpt": p["bptIndex"]}


def micro(p):
    """The phase: every swap of the batchSwap that involves neither BPT. Each is tagged drain (take the rate
    token down to `leave` wei), micro (take leave - 1 out) or restore (swap it back for a recorded WETH amount)."""
    sw = p["swaps"]
    reg = [k for k, s in enumerate(sw) if p["bptIndex"] not in (s["i"], s["j"])]
    assert reg == list(range(reg[0], reg[-1] + 1)), "the regular swaps are one contiguous run"
    steps = [dict(sw[k], k=k) for k in reg]
    left = {}
    for s in steps:
        r = int(s["balances"][s["j"]]) - int(s["amount"])
        left[r] = left.get(r, 0) + 1
    leave = max(left, key=left.get)
    for s in steps:
        if int(s["balances"][s["j"]]) - int(s["amount"]) == leave:
            s["plan"], s["what"] = 0, "drain"
        else:
            s["plan"], s["what"] = 1, "micro" if int(s["amount"]) < leave else "restore"
    return steps, leave


def evaluate(pool, s, model):
    raw = [int(b) for b in s["balances"]]
    i, j, amt = s["i"], s["j"], int(s["amount"])
    if model == "deployed":
        return swap_int(pool, raw, i, j, amt)
    if model == "mulUp":
        return swap_int(pool, raw, i, j, amt, up=mul_up)
    if model == "exact":
        return swap_exact(pool, raw, i, j, amt)
    raise ValueError(model)


def plan_replay(pool, steps, leave, model):
    """The attacker's plan (drain the rate token to `leave` wei, take leave - 1 out, swap the recorded WETH amount
    back) from the phase's first balances, priced by `model` on its own balances. Returns the swap at which the
    plan can no longer be executed (an amount out of at least the balance), or None and the invariant ratio."""
    raw = [int(b) for b in steps[0]["balances"]]
    d0 = true_invariant(pool, raw)
    for s in steps:
        i, j = s["i"], s["j"]
        amt = raw[j] - leave if s["plan"] == 0 else int(s["amount"])
        if not 0 < amt < raw[j]:
            return {"breaksAtSwap": s["k"], "balanceOut": raw[j], "wanted": amt}
        ain, _ = evaluate(pool, dict(s, balances=[str(b) for b in raw], amount=str(amt)), model)
        raw[i] += ain
        raw[j] -= amt
    return {"breaksAtSwap": None, "invariantRatio": sci(true_invariant(pool, raw) / d0, 10)}


def sci(x, n=4):
    return nstr(mpf(x), n, min_fixed=-4, max_fixed=9) if x != 0 else "0"


# ---------------------------------------------------------------- forge harness log

FP_RE = re.compile(r"BAL\|(\w+)\|(\w+)\|(\d+)\|(.*)")


def run_forge():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["forge", "test", "--match-path", TEST, "-vv"], cwd=ROOT, capture_output=True, text=True)
    LOG.write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        print(r.stdout[-6000:], r.stderr[-2000:])
        raise SystemExit("forge harness failed")


def parse_log():
    rows: dict = {}
    for line in LOG.read_text().splitlines():
        m = FP_RE.search(line)
        if not m:
            continue
        pool, model, k, kv = m.groups()
        d = dict(x.split("=", 1) for x in kv.strip().split(";") if x)
        rows.setdefault(pool, {}).setdefault(model, {})[int(k)] = d
    return rows


def fp127_val(s):
    return Fraction(int(s), 2 ** 128)


def fp19_val(s):
    w = int(s) % 2 ** 256
    if w == 0:
        return Fraction(0)
    neg, e, f = w >> 255, (w >> 236) & 0x7FFFF, w & ((1 << 236) - 1)
    v = Fraction((1 << 236) + f) * Fraction(2) ** (e - 262143 - 236)
    return -v if neg else v


# ---------------------------------------------------------------- score

MODELS = ("deployed", "mulUp", "fp127", "fp19", "exact", "nearest")


def score(run_harness: bool):
    data = json.loads(OUT.read_text())
    tests, prep = {}, {}
    for name, p in data["pools"].items():
        pool = pool_params(p)
        steps, leave = micro(p)
        # the Vault's balances chain: each call's balances are the previous call's plus amountIn, minus amount
        for a, b in zip(steps, steps[1:]):
            nb = [int(x) for x in a["balances"]]
            nb[a["i"]] += int(a["amountIn"])
            nb[a["j"]] -= int(a["amount"])
            assert nb == [int(x) for x in b["balances"]], (name, a["k"])
        ev = {m: [evaluate(pool, s, m) for s in steps] for m in ("deployed", "mulUp", "exact")}
        # the deployed arithmetic reproduces every on-chain return of the phase, each call on its own inputs
        for s, (got, _) in zip(steps, ev["deployed"]):
            assert got == int(s["amountIn"]), (name, s["k"], got, s["amountIn"])
        tests[name] = {
            "sf": [str(x) for x in pool["sf"]], "amp": str(pool["amp"]), "fee": str(pool["fee"]), "bpt": str(pool["bpt"]),
            "leave": str(leave), "first": str(steps[0]["k"]),
            "i": [str(s["i"]) for s in steps], "j": [str(s["j"]) for s in steps], "amount": [s["amount"] for s in steps],
            "plan": [str(s["plan"]) for s in steps], "amountIn": [s["amountIn"] for s in steps],
            "bal0": [s["balances"][0] for s in steps], "bal1": [s["balances"][1] for s in steps],
            "bal2": [s["balances"][2] for s in steps],
            "expectMulUp": [str(a) for a, _ in ev["mulUp"]], "expectExact": [str(a) for a, _ in ev["exact"]],
        }
        prep[name] = {"pool": pool, "steps": steps, "leave": leave, "ev": ev}
    data["test"] = tests
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    if run_harness:
        run_forge()
    log = parse_log()
    data["score"] = {}
    for name, P in prep.items():
        for m in ("deployed", "mulUp"):  # the Solidity transcription agrees with the Python port, call by call
            for s, (a, x) in zip(P["steps"], P["ev"][m]):
                d = log[name][m][s["k"]]
                assert (int(d["in"]), int(d["D"]), int(d["y"]), int(d["itD"]), int(d["itY"])) == \
                       (a, x["D"], x["y"], x["itD"], x["itY"]), (name, m, s["k"])
        data["score"][name] = summarise(name, data["pools"][name], P, log[name])
    data["score"]["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    write_md(data)
    print(f"wrote {OUT.relative_to(ROOT)} and {MD.relative_to(ROOT)}")


def summarise(name, p, P, log):
    pool, steps = P["pool"], P["steps"]
    sym = p["symbols"]
    rk = [k for k in range(3) if k != pool["bpt"] and pool["sf"][k] != ONE][0]
    wk = [k for k in range(3) if k != pool["bpt"] and k != rk][0]
    q = {k: Fraction(pool["sf"][k], ONE) for k in range(3)}
    tvl = sum(Fraction(int(p["balancesBlockMinus1"][k]), ONE) * q[k] for k in (wk, rk))
    amounts = {m: [a for a, _ in P["ev"][m]] for m in P["ev"]}
    for m in ("fp127", "fp19"):
        amounts[m] = [int(log[m][s["k"]]["in"]) for s in steps]
    # sensitivity, not a proposal: the exact charge rounded to nearest instead of up at the wei boundary
    amounts["nearest"] = [int(mp.floor(x["need"] + mpf(1) / 2)) for _, x in P["ev"]["exact"]]
    rows, agg = [], {m: {"in": {sym[wk]: 0, sym[rk]: 0}, "under": 0, "over": 0, "equal": 0, "dD": mpf(0), "logRatio": mpf(1),
                         "fall": 0, "byKind": {k: {"dD": mpf(0), "n": 0} for k in KINDS}} for m in MODELS}
    attr_tot = {k: {} for k in KINDS}
    for t, s in enumerate(steps):
        before = [int(b) for b in s["balances"]]
        d0 = true_invariant(pool, before)
        a = int(s["amount"])
        row = {"k": s["k"], "what": s["what"], "tokenIn": sym[s["i"]], "tokenOut": sym[s["j"]], "out": a,
               "balancesBefore": [before[wk], before[rk]], "trueInvariantBefore": sci(d0, 12),
               "upscaledOutDeployed": P["ev"]["deployed"][t][1]["a"], "upscaledOutMulUp": P["ev"]["mulUp"][t][1]["a"],
               "upscaledOutTrue": sci(mpf(a) * frac_mpf(q[s["j"]]), 12),
               "exactNeed": sci(P["ev"]["exact"][t][1]["need"], 12), "models": {}}
        for m in MODELS:
            ain = amounts[m][t]
            after = list(before)
            after[s["i"]] += ain
            after[s["j"]] -= a
            d1 = true_invariant(pool, after)
            dd = d1 - d0
            row["models"][m] = {"in": ain, "dD": sci(dd, 8), "rel": sci(dd / d0, 6)}
            g = agg[m]
            g["in"][sym[s["i"]]] += ain
            ex = amounts["exact"][t]
            g["under" if ain < ex else "over" if ain > ex else "equal"] += 1
            g["dD"] += dd
            g["logRatio"] *= d1 / d0
            g["fall"] += dd < 0
            g["byKind"][s["what"]]["dD"] += dd
            g["byKind"][s["what"]]["n"] += 1
        at = attribution(pool, s)
        row["attribution"] = {k: sci(v, 8) for k, v in at.items()}
        for k, v in at.items():
            attr_tot[s["what"]][k] = attr_tot[s["what"]].get(k, mpf(0)) + v
        rows.append(row)
    start = [int(b) for b in steps[0]["balances"]]
    end = [int(b) for b in steps[-1]["balances"]]
    end[steps[-1]["i"]] += int(steps[-1]["amountIn"])
    end[steps[-1]["j"]] -= int(steps[-1]["amount"])
    dstart, dend = true_invariant(pool, start), true_invariant(pool, end)
    models = {}
    for m in MODELS:
        g = agg[m]
        models[m] = {"amountIn": g["in"], "stepsUnderExact": g["under"], "stepsOverExact": g["over"],
                     "stepsEqualExact": g["equal"], "stepsInvariantFalls": g["fall"], "sumDeltaInvariant": sci(g["dD"], 10),
                     "invariantRatio": sci(g["logRatio"], 10),
                     "projectedExtractionEth": sci((1 - g["logRatio"]) * frac_mpf(tvl), 6),
                     "byKind": {k: {"n": v["n"], "sumDeltaInvariant": sci(v["dD"], 8)} for k, v in g["byKind"].items()}}
    assert abs(agg["deployed"]["logRatio"] - dend / dstart) < mpf(10) ** -150, sci(agg["deployed"]["logRatio"] - dend / dstart)  # telescopes
    return {"pool": name, "address": p["address"], "symbols": sym, "rateToken": sym[rk], "rate": str(pool["sf"][rk]),
            "amp": pool["amp"], "fee": pool["fee"], "leave": P["leave"], "firstSwap": steps[0]["k"],
            "lastSwap": steps[-1]["k"], "swaps": len(steps),
            "kinds": {k: sum(1 for s in steps if s["what"] == k) for k in KINDS},
            "tvlBlockMinus1Eth": sci(tvl, 10), "trueInvariantStart": sci(dstart, 12), "trueInvariantEnd": sci(dend, 12),
            "onchainInvariantRatio": sci(dend / dstart, 10),
            "bptRate": {"before": p["bptRateBefore"], "after": p["bptRateAfter"],
                        "ratio": sci(Fraction(p["bptRateAfter"], p["bptRateBefore"]), 8)},
            "batchSwapAssetDeltas": dict(zip(sym, p["batchSwapAssetDeltas"])),
            # the whole batchSwap's net to the attacker, valued at the in-transaction rates (BPT at its rate after)
            "batchSwapNetEth": sci(sum(-Fraction(p["batchSwapAssetDeltas"][k], ONE) * q[k] for k in (wk, rk))
                                   - Fraction(p["batchSwapAssetDeltas"][pool["bpt"]], ONE) * Fraction(p["bptRateAfter"], ONE), 8),
            "attributionByKind": {w: {k: sci(v, 8) for k, v in t.items()} for w, t in attr_tot.items()},
            "planReplay": {m: plan_replay(pool, steps, P["leave"], m) for m in ("deployed", "mulUp", "exact")},
            "models": models, "convergence": convergence(pool, steps, P["ev"], log), "steps": rows}


def need_exact(pool, bal, a, ii, jj, qi):
    """The exact charge (token units, fee included, before any rounding) from upscaled balances `bal` (the two
    non-BPT tokens) and upscaled amount out `a`, all rationals."""
    A = annp(pool)
    d = invariant_exact(A, Fraction(bal[0]), Fraction(bal[1]))
    y = balance_exact(A, d, Fraction(bal[jj]) - Fraction(a))
    return (y - frac_mpf(Fraction(bal[ii]))) / frac_mpf(qi) / (1 - mpf(pool["fee"]) / ONE)


def attribution(pool, s):
    """deployed - exact charge for one call, split by where the rounding happens (token-in units):
    amountOut  only the given-out amount upscaled by mulDown (everything else exact)
    balances   only the balances upscaled by mulDown
    upscales   both together, exact solver
    solver     the rest: StableMath's integer Newton (P_D floored, c rounded up, stop at <= 1, + 1),
               _downscaleUp and the fee's divUp."""
    sf, bpt = pool["sf"], pool["bpt"]
    raw = [int(b) for b in s["balances"]]
    i, j, amt = s["i"], s["j"], int(s["amount"])
    ii, jj = i - (i > bpt), j - (j > bpt)
    q = [Fraction(sf[k], ONE) for k in range(3)]
    upd = [mul_down(raw[k], sf[k]) for k in range(3) if k != bpt]
    upx = [raw[k] * q[k] for k in range(3) if k != bpt]
    dep, _ = swap_int(pool, raw, i, j, amt)
    n_ex = need_exact(pool, upx, amt * q[j], ii, jj, q[i])
    n_amt = need_exact(pool, upx, mul_down(amt, sf[j]), ii, jj, q[i])
    n_bal = need_exact(pool, upd, amt * q[j], ii, jj, q[i])
    n_both = need_exact(pool, upd, mul_down(amt, sf[j]), ii, jj, q[i])
    return {"amountOut": n_amt - n_ex, "balances": n_bal - n_ex, "upscales": n_both - n_ex, "solver": dep - n_both,
            "total": dep - n_ex}


def convergence(pool, steps, ev, log):
    """Iterations of each Newton solve and the residual against the exact root of the same inputs."""
    A = annp(pool)
    conv = {}
    st = {"itD": [], "itY": [], "relD": [], "absD": [], "relY": [], "absY": [], "absYstop": [], "relYstop": []}
    for (_, x) in ev["deployed"]:
        bal = x["bal"]
        dstar = invariant_exact(A, Fraction(bal[0]), Fraction(bal[1]))
        o = bal[x["jj"]] - x["a"]
        ystar = balance_exact(A, mpf(x["D"]), Fraction(o))
        # the root of the solver's own quadratic (its rounded c and b): what the stopping rule alone leaves
        bb, c = mpf(x["b"]) - x["D"], mpf(x["c"])
        yq = (-bb + msqrt(bb * bb + 4 * c)) / 2
        st["itD"].append(x["itD"]); st["itY"].append(x["itY"])
        st["absD"].append(x["D"] - dstar); st["relD"].append((x["D"] - dstar) / dstar)
        st["absY"].append(x["y"] - ystar); st["relY"].append((x["y"] - ystar) / ystar)
        st["absYstop"].append(x["y"] - yq); st["relYstop"].append((x["y"] - yq) / yq)
    conv["deployed"] = agg_conv(st)
    for m, val in (("fp127", fp127_val), ("fp19", fp19_val)):
        st = {"itD": [], "itY": [], "relD": [], "absD": [], "relY": [], "absY": []}
        for s in steps:
            d = log[m][s["k"]]
            b0, b1, dd, yy, oo = (val(d[k]) for k in ("b0", "b1", "Dw", "yw", "ow"))
            dstar = invariant_exact(A, b0, b1)
            ystar = balance_exact(A, frac_mpf(dd), oo)
            st["itD"].append(int(d["itD"])); st["itY"].append(int(d["itY"]))
            st["absD"].append(frac_mpf(dd) - dstar); st["relD"].append((frac_mpf(dd) - dstar) / dstar)
            st["absY"].append(frac_mpf(yy) - ystar); st["relY"].append((frac_mpf(yy) - ystar) / ystar)
        conv[m] = agg_conv(st)
        ls = [s["k"] for s in steps]
        conv[m]["stoppedOnGrid"] = {"D": sum(log[m][k]["howD"] == "0" for k in ls),
                                    "y": sum(log[m][k]["howY"] == "0" for k in ls)}
        conv[m]["stoppedOnStall"] = {"D": sum(log[m][k]["howD"] == "1" for k in ls),
                                     "y": sum(log[m][k]["howY"] == "1" for k in ls)}
        conv[m]["literalRuleNeverStopped"] = {"D": sum(log[m][k]["litD"] == "0" for k in ls),
                                              "y": sum(log[m][k]["litY"] == "0" for k in ls)}
        lit = [int(log[m][k]["litD"]) for k in ls if log[m][k]["litD"] != "0"]
        conv[m]["literalRuleItersWhenItStopped"] = {"D": [min(lit), max(lit)] if lit else None}
    conv["calls"] = len(steps)
    return conv


def agg_conv(st):
    o = {}
    for k, v in st.items():
        if k.startswith("it"):
            w = sorted(v)
            o[k] = {"min": w[0], "median": w[len(w) // 2], "max": w[-1], "total": sum(w)}
        else:
            a = [abs(x) for x in v]
            mx = max(a)
            o[k] = {"maxAbs": sci(mx, 4), "medianAbs": sci(sorted(a)[len(a) // 2], 4),
                    "below": sum(1 for x in v if x < 0), "above": sum(1 for x in v if x > 0)}
            if k.startswith("rel"):
                o[k]["minDigits"] = round(float(-log10(mx)), 2) if mx else None
    return o


# ---------------------------------------------------------------- report

def write_md(data):
    MD.write_text(render(data))


LABEL = {"deployed": "deployed (V2, `_upscale` = mulDown)", "mulUp": "mulUp on the given-out amount (V3's direction)",
         "fp127": "FP127 inside, ceil to wei once", "fp19": "FP19 inside, ceil to wei once",
         "exact": "exact rationals, ceil to wei once", "nearest": "exact, but round-to-nearest at the wei boundary (sensitivity)"}


def ci(x):
    return f"{int(x):,}"


def fnum(s, n=6):
    """A number string from the JSON as a short human figure."""
    v = mpf(s)
    if v == 0:
        return "0"
    if abs(v) >= 1e6 or abs(v) < 1e-3:
        return nstr(v, n)
    return nstr(v, n, min_fixed=-9, max_fixed=12)


def render(data):
    pv, pools, sc = data["provenance"], data["pools"], data["score"]
    o, w = [], None
    w = o.append
    os_, ws = sc["osETH"], sc["wstETH"]
    po, pw = pools["osETH"], pools["wstETH"]
    s23 = os_["steps"][1]
    w("# Replay: the Balancer V2 Composable Stable Pool exploit, five rulers")
    w("")
    w(f"Generated {sc['generated']} by `uv run scripts/replays/balancer.py` from `scripts/replays/balancer.json` "
      f"(fetched {pv['fetched']} by `balancer.py fetch`); every integer below is asserted by "
      f"`forge test --match-path {TEST}` with no network.")
    w("")
    w("## What happened, in the transaction's own integers")
    w("")
    w(f"Ethereum tx [`{pv['tx'][:10]}…`](https://etherscan.io/tx/{pv['tx']}) (block {ci(pv['block'])}, {pv['timestamp'][:19]} UTC) "
      f"deploys a contract whose constructor runs one Vault `batchSwap` against each of two ComposableStablePool v5 pools. "
      f"Every swap in both is GIVEN_OUT. Each `onSwap` call from the Vault carries the pool's raw balances and the requested "
      f"amount out, and returns the amount the pool charged. Those {len(po['swaps'])} + {len(pw['swaps'])} calls are the data for this replay.")
    w("")
    w("| pool | swaps | phase replayed | rate token, in-tx rate | amp (A·n^(n−1)·1000) | swap fee |")
    w("|---|---|---|---|---|---|")
    for n, s, p in (("osETH", os_, po), ("wstETH", ws, pw)):
        r = int(s["rate"])
        w(f"| {p['symbols'][p['bptIndex']]} `{p['address'][:10]}…` | {len(p['swaps'])} | "
          f"{s['firstSwap']}–{s['lastSwap']}: {s['swaps']} swaps, {s['kinds']['micro']} cycles of drain / micro / restore | "
          f"{s['rateToken']} {r // ONE}.{r % ONE:018d} | {ci(s['amp'])} | {s['fee'] / 1e16:g}% |")
    w("")
    w(f"Swaps 0–21 of each batch swap BPT in for tokens out (exits via swap) until both balances are tiny "
      f"(osETH pool: {ci(os_['steps'][0]['balancesBefore'][0])} WETH-wei and "
      f"{ci(os_['steps'][0]['balancesBefore'][1])} osETH-wei). The replayed phase then repeats three swaps: **drain** the rate "
      f"token to {os_['leave']} wei ({ws['leave']} in the wstETH pool), **micro**: take {os_['leave'] - 1} wei ({ws['leave'] - 1}) of it out, "
      f"**restore**: swap the rate token back in for a chosen WETH amount. The last swaps buy BPT back with tokens.")
    w("")
    w("The micro swap, first cycle, osETH pool (swap 23):")
    w("")
    w(f"- balances before: {ci(s23['balancesBefore'][0])} WETH-wei, {ci(s23['balancesBefore'][1])} osETH-wei; amount out {s23['out']} osETH-wei.")
    w(f"- `_upscale(17, 1058132408689971699)` = mulDown(17 × 1.058132408689971699 = {s23['upscaledOutTrue']}) = "
      f"**{s23['upscaledOutDeployed']}**. mulUp gives {s23['upscaledOutMulUp']}. The pool's own balance of 18 wei upscales to 19, "
      f"against a true 19.046. So the pool believes 2 units are left after the swap; the true figure is 1.058.")
    m = s23["models"]
    w(f"- Charged on chain: **{ci(m['deployed']['in'])} WETH-wei**. The exact charge for the same request on the same balances "
      f"(fee included, rounded up) is **{ci(m['exact']['in'])}**, so the pool undercharged by "
      f"{(1 - m['deployed']['in'] / m['exact']['in']) * 100:.1f}%. The true invariant fell by "
      f"{fnum(-mpf(m['deployed']['dD']))} wei-eq ({-mpf(m['deployed']['rel']) * 100:.2f}%) on this one call.")
    s23w = ws["steps"][1]
    mw = s23w["models"]
    w(f"- wstETH pool, swap 23: 4 wei out of 5. 4 × 1.21811641527976076 = {s23w['upscaledOutTrue']} → **{s23w['upscaledOutDeployed']}**. "
      f"Charged {ci(mw['deployed']['in'])} WETH-wei; exact {ci(mw['exact']['in'])} "
      f"({(1 - mw['deployed']['in'] / mw['exact']['in']) * 100:.1f}% under); the invariant fell by {-mpf(mw['deployed']['rel']) * 100:.2f}%.")
    w("")
    w("Across the phase (true invariant D*: the pool's own StableSwap invariant, solved exactly on the raw balances × the exact in-tx rates, in 18-decimal wei):")
    w("")
    w("| pool | D* before swap 22 | D* after the phase | ratio | BPT `getRate()` before → after the whole batchSwap (on chain) | batchSwap net to the attacker |")
    w("|---|---|---|---|---|---|")
    for n, s in (("osETH/WETH", os_), ("wstETH/WETH", ws)):
        w(f"| {n} | {fnum(s['trueInvariantStart'], 9)} | {fnum(s['trueInvariantEnd'], 9)} | {fnum(s['onchainInvariantRatio'], 5)} | "
          f"{s['bptRate']['before'] / 1e18:.6f} → {s['bptRate']['after'] / 1e18:.6f} (×{fnum(s['bptRate']['ratio'], 5)}) | "
          f"{fnum(s['batchSwapNetEth'], 7)} ETH |")
    w("")
    w("The batchSwap net is the Vault's `assetDeltas`, valued at the in-transaction rates, with the BPT left over valued at its "
      "rate after the swaps. Both batchSwaps settle to and from the attack contract's Vault internal balance (`fromInternalBalance` and `toInternalBalance` both true), so nothing leaves the Vault in this transaction. The swaps around the phase exit at the fair BPT "
      "price and buy back after the invariant has collapsed, so the take is about (1 − ratio) × the pool's value: "
      f"{fnum(os_['models']['deployed']['projectedExtractionEth'], 6)} ETH projected against {fnum(os_['batchSwapNetEth'], 7)} realised (osETH), "
      f"and {fnum(ws['models']['deployed']['projectedExtractionEth'], 6)} against {fnum(ws['batchSwapNetEth'], 7)} (wstETH).")
    w("")
    w("## The same calls on five rulers")
    w("")
    w("Each model prices every call of the phase on that call's own on-chain balances and amount. *Below exact* counts the calls "
      "charged less than the exact charge. *ΔD* is the change in the true invariant D* if that call had been charged this "
      "model's amount. *Ratio* is the product of the per-call ratios D*after / D*before, which for the deployed row is "
      "the on-chain ratio. *Projected* is (1 − ratio) × the pool's value at block − 1, the first-order take of the "
      "exit / deflate / re-enter plan; a negative value means the pool gains.")
    w("")
    for n, s in (("osETH/WETH", os_), ("wstETH/WETH", ws)):
        w(f"**{n}** ({s['swaps']} calls, swaps {s['firstSwap']}–{s['lastSwap']}; pool value {fnum(s['tvlBlockMinus1Eth'], 7)} ETH)")
        w("")
        w("| model | charged in (WETH-wei / rate-token-wei) | calls below exact | calls that lower D* | ΣΔD* (wei-eq) | ratio | projected take (ETH) |")
        w("|---|---|---|---|---|---|---|")
        for mm in MODELS:
            g = s["models"][mm]
            a = g["amountIn"]
            w(f"| {LABEL[mm]} | {ci(a['WETH'])} / {ci(a[s['rateToken']])} | {g['stepsUnderExact']} | {g['stepsInvariantFalls']} | "
              f"{fnum(g['sumDeltaInvariant'], 7)} | {fnum(g['invariantRatio'], 7)} | {fnum(g['projectedExtractionEth'], 6)} |")
        w("")
        w("ΣΔD* by kind of call:")
        w("")
        w("| model | drain | micro | restore |")
        w("|---|---|---|---|")
        for mm in MODELS:
            b = s["models"][mm]["byKind"]
            w(f"| {mm} | {fnum(b['drain']['sumDeltaInvariant'], 6)} | {fnum(b['micro']['sumDeltaInvariant'], 6)} | {fnum(b['restore']['sumDeltaInvariant'], 6)} |")
        w("")
    w("First cycle, per call (osETH/WETH): amount charged and ΔD* (wei-eq).")
    w("")
    w("| swap | kind | out | " + " | ".join(MODELS) + " |")
    w("|---|---|---|" + "---|" * len(MODELS))
    for r in os_["steps"][:3] + ws["steps"][:3]:
        cells = [f"{ci(r['models'][mm]['in'])} ({fnum(r['models'][mm]['dD'], 4)})" for mm in MODELS]
        w(f"| {'osETH' if r in os_['steps'] else 'wstETH'} {r['k']} | {r['what']}: {r['tokenIn']} in, {r['tokenOut']} out | {ci(r['out'])} | " + " | ".join(cells) + " |")
    w("")
    w("### Which alternative alone suffices")
    w("")
    om, wm = os_["models"], ws["models"]
    w(f"- **FP127 and FP19** charge exactly the exact-rational amount on all {os_['swaps']} + {ws['swaps']} calls. That is asserted "
      f"call by call in the test, and no call lowers D*. Inside the format the upscaled 17 osETH-wei stays 17.988250947729518883 "
      f"to within 2^-128. The only rounding to the wei grid is the final ceil, which favours the pool.")
    w(f"- **mulUp alone** defeats the attack as executed: every micro call now over-charges, and the per-call ratio is "
      f"{fnum(om['mulUp']['invariantRatio'], 4)} (osETH) and {fnum(wm['mulUp']['invariantRatio'], 4)} (wstETH) instead of "
      f"{fnum(om['deployed']['invariantRatio'], 4)} and {fnum(wm['deployed']['invariantRatio'], 4)}. It does not make every call safe. "
      f"All {os_['kinds']['restore']} + {ws['kinds']['restore']} restore calls still lower D*, by exactly the deployed amount "
      f"({fnum(om['mulUp']['byKind']['restore']['sumDeltaInvariant'], 6)} and {fnum(wm['mulUp']['byKind']['restore']['sumDeltaInvariant'], 6)} wei-eq). "
      f"Their given-out token is WETH, whose scaling factor is exactly 1, so mulUp changes nothing there. Their loss comes from the "
      f"token-in balance: 1 wei of the rate token upscales by mulDown to 1, against a true 1.058 or 1.218. "
      f"mulUp also over-charges a trader heavily at these balances: {ci(s23['models']['mulUp']['in'])} against the exact {ci(s23['models']['exact']['in'])} on swap 23.")
    w(f"- **Round-to-nearest at the boundary** instead of ceil, with exact maths inside: {om['nearest']['stepsInvariantFalls']} + "
      f"{wm['nearest']['stepsInvariantFalls']} calls lower D* by under half a wei of the token in each. The 0.01% fee keeps the phase net "
      f"positive, with ratios {fnum(om['nearest']['invariantRatio'], 6)} and {fnum(wm['nearest']['invariantRatio'], 6)}. FP127's claim therefore "
      f"depends on keeping the boundary's direction.")
    pr = os_["planReplay"]
    w(f"- The attacker's plan itself cannot be executed under the alternatives. Replayed adaptively (drain to {os_['leave']}, take "
      f"{os_['leave'] - 1}, restore with the recorded WETH amount) on each model's own balances, it reaches swap "
      f"{pr['mulUp']['breaksAtSwap']} under mulUp and swap {pr['exact']['breaksAtSwap']} under exact pricing with less of the rate token left "
      f"than it means to leave behind ({pr['exact']['balanceOut']} wei against {os_['leave']}). In the wstETH pool it fails at swaps "
      f"{ws['planReplay']['mulUp']['breaksAtSwap']} and {ws['planReplay']['exact']['breaksAtSwap']}. Under deployed pricing it reproduces the "
      f"on-chain sequence exactly.")
    w("")
    w("### Where the deployed undercharge comes from")
    w("")
    w("The difference deployed − exact, summed by kind of call and split by where the rounding happens, is in units of the token in. "
      "*amountOut*: only the given-out amount upscaled by mulDown. *balances*: only the balances upscaled by mulDown. "
      "*upscales*: both together. *solver*: what remains, which is StableMath's integer Newton (P_D floored, c rounded up, stop at ≤ 1, +1), "
      "`_downscaleUp` and the fee's divUp.")
    w("")
    w("| pool | kind | amountOut | balances | upscales | solver | total |")
    w("|---|---|---|---|---|---|---|")
    for n, s in (("osETH", os_), ("wstETH", ws)):
        for k in KINDS:
            a = s["attributionByKind"][k]
            w(f"| {n} | {k} | {fnum(a['amountOut'], 6)} | {fnum(a['balances'], 6)} | {fnum(a['upscales'], 6)} | {fnum(a['solver'], 6)} | {fnum(a['total'], 6)} |")
    w("")
    w("The micro calls' undercharge is the given-out amount's truncation. The balance truncation partly offsets it there and is the "
      "whole loss on the restore calls. The integer solvers err on the pool's side in every kind of call.")
    w("")
    w("## Newton convergence: where each ruler stops")
    w("")
    w("StableMath's `_calculateInvariant` and `_getTokenBalanceGivenInvariantAndAllOtherBalances` are Newton iterations that "
      "stop when two iterates differ by ≤ 1 on the wei grid. The same two maps run in FP127 and in FP19 with the same algebra, "
      "reordered only so that FP127 does not overflow. Their stop is ≤ 1 unit of the format's own grid, or a stall: the step has "
      "stopped shrinking and is already below 2^-64 (FP127) or 2^-128 (FP19) of the iterate. Residuals are measured against the "
      "exact root (200 digits) of the same inputs each solver received.")
    w("")
    w("| pool | ruler | invariant: iterations (median / max) | invariant: worst residual | balance: iterations (median / max) | balance: worst residual |")
    w("|---|---|---|---|---|---|")
    for n, s in (("osETH", os_), ("wstETH", ws)):
        c = s["convergence"]
        d = c["deployed"]
        w(f"| {n} | wei grid (deployed) | {d['itD']['median']} / {d['itD']['max']} | {fnum(d['absD']['maxAbs'], 4)} wei "
          f"(rel {fnum(d['relD']['maxAbs'], 3)}, {d['relD']['minDigits']} digits) | {d['itY']['median']} / {d['itY']['max']} | "
          f"rel {fnum(d['relY']['maxAbs'], 3)} ({d['relY']['minDigits']} digits), always above the root; the stop alone leaves ≤ {fnum(d['absYstop']['maxAbs'], 4)} wei |")
        for mm in ("fp127", "fp19"):
            f = c[mm]
            w(f"| {n} | {mm.upper()} | {f['itD']['median']} / {f['itD']['max']} | rel {fnum(f['relD']['maxAbs'], 3)} ({f['relD']['minDigits']} digits) | "
              f"{f['itY']['median']} / {f['itY']['max']} | rel {fnum(f['relY']['maxAbs'], 3)} ({f['relY']['minDigits']} digits) |")
    w("")
    c1, c2 = os_["convergence"], ws["convergence"]
    w(f"- The same iteration reaches whatever ruler it runs on. On the wei grid the invariant stops within "
      f"{fnum(c1['deployed']['absD']['maxAbs'], 3)} wei of its own root (worst relative {fnum(c1['deployed']['relD']['maxAbs'], 2)}, "
      f"{c1['deployed']['relD']['minDigits']} digits, osETH; {c2['deployed']['relD']['minDigits']} in the larger wstETH pool). "
      f"On FP127 it reaches {min(c1['fp127']['relD']['minDigits'], c2['fp127']['relD']['minDigits'])}–"
      f"{max(c1['fp127']['relD']['minDigits'], c2['fp127']['relD']['minDigits'])} digits, and on FP19 "
      f"{min(c1['fp19']['relD']['minDigits'], c2['fp19']['relD']['minDigits'])}–{max(c1['fp19']['relD']['minDigits'], c2['fp19']['relD']['minDigits'])}. "
      f"It costs a few more iterations: median {c1['deployed']['itD']['median']} → {c1['fp127']['itD']['median']} → {c1['fp19']['itD']['median']} (osETH) and "
      f"{c2['deployed']['itD']['median']} → {c2['fp127']['itD']['median']} → {c2['fp19']['itD']['median']} (wstETH, where one balance is 1 wei against 10^14).")
    w(f"- The literal \"≤ 1 unit\" stop does not carry over to a fine grid. The map evaluated in FP127 is noisier than one unit "
      f"near the root (D times a ratio carries D·2^-128), so the literal rule never stopped within 255 iterations on "
      f"{c1['fp127']['literalRuleNeverStopped']['D']} of {c1['calls']} (osETH) and {c2['fp127']['literalRuleNeverStopped']['D']} of {c2['calls']} "
      f"(wstETH) invariant solves. In FP19 the counts are {c1['fp19']['literalRuleNeverStopped']['D']} and {c2['fp19']['literalRuleNeverStopped']['D']}. "
      f"StableMath's cap would revert there (`STABLE_INVARIANT_DIDNT_CONVERGE`). The stall test ends them, and their residuals are in the "
      f"table. The balance solver's literal rule always stopped.")
    w(f"- The deployed solvers are not what the attacker exploited. Their result is the root of their own rounded quadratic to within "
      f"≤ 1 wei, and is always above the exact root ({c1['deployed']['absY']['above']}/{c1['calls']} and {c2['deployed']['absY']['above']}/{c2['calls']}). "
      f"So it charges more, by up to {fnum(c1['deployed']['relY']['maxAbs'], 3)} and {fnum(c2['deployed']['relY']['maxAbs'], 3)} of the solved balance, "
      f"because its coefficients are rounded to whole units before it starts. b = sum + ⌊D / (amp·n)⌋·1000 loses D / (amp·n) entirely "
      f"in the osETH pool, where D < amp·n = 400,000 throughout the phase. P_D = ⌊2·b0·2·b1 / D⌋ is floored and c is rounded up; "
      f"each of these raises the solved balance. The invariant's ≤ 1 stop lands on either side of the root "
      f"({c1['deployed']['absD']['below']} below / {c1['deployed']['absD']['above']} above in osETH; "
      f"{c2['deployed']['absD']['below']} / {c2['deployed']['absD']['above']} in wstETH). The wei ruler decided these answers too, but "
      f"in the pool's favour. The 1-wei quantum that hurt was the one applied to the *inputs* of the solve: the given-out amount "
      f"and the token-in balance.")
    w("")
    w("## Against the published write-ups")
    w("")
    w("- OpenZeppelin's 17 × 1.058132408689971699 = 17.98 → 17 against a balance of 18 is exactly every micro swap of the "
      "osETH pool (the first is swap 23).")
    w(f"- No call in this transaction has a 9-wei balance, an 8-wei amount out or the 8.918 product. The Ethereum pools are steered to "
      f"{os_['leave']} wei of osETH (out {os_['leave'] - 1}) and {ws['leave']} wei of wstETH (out {ws['leave'] - 1}, "
      f"4 × 1.218 = 4.87 → 4, truncated by {(1 - 4 / mpf(s23w['upscaledOutTrue'])) * 100:.0f}%). That example may come from another chain's pool; it is not this one.")
    w(f"- Counts in this transaction: {len(po['swaps'])} + {len(pw['swaps'])} swaps in the two batchSwaps, of which "
      f"{os_['swaps']} + {ws['swaps']} are token-for-token and {os_['kinds']['micro']} + {ws['kinds']['micro']} are the micro swaps. "
      f"\"65 operations\" does not match any of these counts.")
    trunc = [(1 - mpf(x['upscaledOutDeployed']) / mpf(x['upscaledOutTrue'])) * 100 for x in (s23, s23w)]
    under = [(1 - mpf(x['models']['deployed']['in']) / x['models']['exact']['in']) * 100 for x in (s23, s23w)]
    fall = [-mpf(x['models']['deployed']['rel']) * 100 for x in (s23, s23w)]
    w(f"- The truncation per micro swap is {trunc[0]:.1f}% of the amount (osETH) and {trunc[1]:.1f}% (wstETH). The damage is larger: "
      f"{under[0]:.1f}% and {under[1]:.1f}% of the charge on the first micro swaps, and {fall[0]:.1f}% and {fall[1]:.1f}% of the whole "
      "invariant on that one call. This is because the pool also misjudges what is left, 2 against 1.058, at the steep end of the curve.")
    w("")
    w("## Provenance")
    w("")
    w(f"- Transaction {pv['tx']}, block {pv['block']} (`{pv['blockHash']}`), from `{pv['from']}`, contract created `{pv['created']}`, "
      f"status {pv['status']}, gas {ci(pv['gasUsed'])}.")
    w(f"- Call trace: `debug_traceTransaction` with `callTracer` from {pv['traceEndpoint']} (keyless), sha256 of the canonical JSON "
      f"`{pv['traceSha256']}`. Every `onSwap` (selector `0x01ec954a`) to each pool is decoded into `pools.*.swaps` "
      f"(kind, indices, amount, the balances the Vault passed, the return).")
    w(f"- Pool state at block {pv['stateBlock']} by `eth_call` on {pv['stateEndpoint']}: pool tokens and balances (equal to the first "
      f"call's), scaling factors, rate providers, amp, swap fee, BPT rate, `version()` "
      f"(`{json.loads(po['version'])['deployment']}`). The rate used by every swap is the one in the transaction: the attacker "
      f"called `updateTokenRateCache` first. osETH's provider returned {po['rateCacheUpdatedInTx']['providerRate']} in the transaction, "
      f"against a cached {po['scalingFactorsBlockMinus1'][2]} and {po['providerRateBlockMinus1']} from the provider at block − 1. "
      f"For wstETH the cache already equalled the provider ({pw['rateCacheUpdatedInTx']['providerRate']}). `scalingFactorsInTx` is "
      f"the attacker's own `getScalingFactors()` read after the update.")
    w(f"- Source: verified standard-JSON input of both pools from {pv['sourceApi']} (`getsourcecode`), "
      f"{po['source']['contractName']} {po['source']['compiler']}, optimizer {po['source']['optimizer']['runs']} runs; the "
      f"two pools' files are byte-identical. Transcribed into `{TEST}` (library `BalancerV2`):")
    w("")
    w("| function | verified file:lines | sha256 of the file |")
    w("|---|---|---|")
    for k, v in po["source"]["cites"].items():
        f = v.rsplit(":", 1)[0]
        w(f"| `{k.split(':', 1)[1]}` | `{v}` | `{po['source']['files'][f][:16]}…` |")
    w("")
    w("Not done: recompiling the verified source and comparing bytecode with `eth_getCode`, as the accrual study does. The "
      f"transcription is instead checked against all {os_['swaps'] + ws['swaps']} on-chain returns of the phase. Each call is "
      "reproduced bit for bit from its own inputs, and the whole phase is reproduced from its first balances alone.")
    w("")
    w("## What the test asserts")
    w("")
    w(f"`{TEST}` reads `scripts/replays/balancer.json` and needs no network:")
    w("")
    w("- `test_deployed_*`: every call's return, bit for bit.")
    w("- `test_deployed_plan_*`: the plan replayed from the first balances reproduces every amount and every Vault balance.")
    w("- `test_mulUp_*`: the mulUp variant equals this script's port.")
    w("- `test_fp127_*` and `test_fp19_*`: the formats equal the exact-rational charge on every call.")
    w("- `test_upscale_headline`: the products by hand.")
    w("")
    w("`balancer.py` also asserts three things: that its Python port equals the Solidity transcription in amount, D, y and "
      "iteration counts on every call; that the Vault's balances chain from call to call; and that the per-call invariant ratios "
      "telescope to the on-chain one.")
    w("")
    w("## Caveat")
    w("")
    w("The alternatives are priced call by call on the balances that actually occurred, not along a path an attacker would "
      "re-optimise for each ruler. They show that these calls stop paying under FP127, FP19 or exact pricing; they do not show that no "
      "other sequence could find what remains, such as the token-in balance truncation that mulUp leaves.")
    w("")
    return "\n".join(o) + "\n"


def main():
    args = sys.argv[1:]
    if args[:1] == ["fetch"]:
        fetch()
    else:
        score(run_harness="--score" not in args)


if __name__ == "__main__":
    main()

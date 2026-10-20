#!/usr/bin/env python3
"""Replay of the 31 Aug 2026 Balancer V1 drain against a 200-digit truth.

    uv run scripts/replays/balancer_v1.py fetch [rpc]   # (network) receipts, pool state at block-1, verified source,
                                                        #   recompile + bytecode compare -> scripts/replays/balancer_v1.json
    uv run scripts/replays/balancer_v1.py score         # (offline) Python model of the deployed BNum/BMath replays every
                                                        #   logged pool call bit-exactly, mpmath at 200 digits, forge test
                                                        #   (FP127, FP256) -> docs/benchmarks/replay-balancer-v1.md
    uv run scripts/replays/balancer_v1.py score --no-forge   # reuse out/replays/balancer_v1.log

The five attack transactions are the ones SlowMist listed
(x.com/SlowMist_Team/status/2094272540193722744). Each drained one Balancer V1
BPool deployed by Balancer's own BFactory 0x9424B141...76Bd. Every pool call
is recovered from the pool's own anonymous LOG_CALL event (the full calldata),
and its result from LOG_SWAP / LOG_JOIN / LOG_EXIT; the pool's state is read
by eth_call at the block before the attack (and checked to be untouched
earlier in the attack block). Nothing here signs or sends a transaction.

`score` re-runs every call through a transcription of the verified
BNum/BMath/BPool arithmetic and asserts each logged amount; the same is done
in Solidity by test/replays/BalancerV1.t.sol, which also computes
calcSingleInGivenPoolOut / calcSingleOutGivenPoolIn with FP127 and FP256.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "accrual"))
from rpc import addr_word, rpc, sel, words, decode_string  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "replays"
DATA = HERE / "balancer_v1.json"
LOG = ROOT / "out" / "replays" / "balancer_v1.log"
OUT_MD = ROOT / "docs" / "benchmarks" / "replay-balancer-v1.md"

ARCHIVE_RPC = "https://mainnet.gateway.tenderly.co"  # keyless public gateway with archive state
ROUTESCAN = "https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api"
POOL1 = "0x2257aaac34bcb27900291f7b84ee2565a6cbac57"  # the "vulnerable contract" SlowMist named; verified on Etherscan
BFACTORY = "0x9424B1412450D0f8Fc2255FAf6046b98213B76Bd"
SLOWMIST = "https://x.com/SlowMist_Team/status/2094272540193722744"
TXS = [
    "0x72510b257cc09bde8435b83ac1636f9498ffc353583330600b5b8da43d0d1aff",
    "0xeef311556b2a2a5be915d1d21785f47311faab26051d5cc832f701fd4ced2c2c",
    "0x37e47f0f5f4ec77e96d220410f6aece30a7589d478c6b17badeb55aa70d66628",
    "0xbaedc537df2075c3edbd43bbd918363be4b9c090971ce4f9592c1ddb3061e111",
    "0xb2d84f926ba84a707d91aa1e1b5fda9565d8db414eece9bd93ced733f8417332",
]
SOLC = {"version": "0.5.12", "long": "v0.5.12+commit.7709ece9",
        "sha256": "70b6f0a355385c5aea26c761b2e58b3216aa564f41e4e156813be3c47a66ae9c"}  # binaries.soliditylang.org list.json

# op kinds, shared with test/replays/BalancerV1.t.sol
SWAP_IN, SWAP_OUT, JOIN_POOL_OUT, EXIT_POOL_IN, EXIT_POOL = 0, 1, 2, 3, 4
CALLS = {
    "swapExactAmountIn(address,uint256,address,uint256,uint256)": SWAP_IN,
    "swapExactAmountOut(address,uint256,address,uint256,uint256)": SWAP_OUT,
    "joinswapPoolAmountOut(address,uint256,uint256)": JOIN_POOL_OUT,
    "exitswapPoolAmountIn(address,uint256,uint256)": EXIT_POOL_IN,
    "exitPool(uint256,uint256[])": EXIT_POOL,
}
SEL = {sel(k)[2:]: (k, v) for k, v in CALLS.items()}
T_SWAP = sel("LOG_SWAP(address,address,address,uint256,uint256)")[2:]
T_JOIN = sel("LOG_JOIN(address,address,uint256)")[2:]
T_EXIT = sel("LOG_EXIT(address,address,uint256)")[2:]
FLASH = {sel("FlashLoan(address,address,address,uint256,uint8,uint256,uint16)")[2:]: "Aave-v3-style FlashLoan",
         sel("FlashLoan(address,address,uint256)")[2:]: "Morpho FlashLoan",
         sel("Flash(address,address,uint256,uint256,uint256,uint256)")[2:]: "Uniswap V3 Flash"}
OTHER_POOL_SELECTORS = {sel(s)[2:]: s for s in [
    "joinPool(uint256,uint256[])", "joinswapExternAmountIn(address,uint256,uint256)",
    "exitswapExternAmountOut(address,uint256,uint256)", "gulp(address)", "setSwapFee(uint256)",
    "setPublicSwap(bool)", "finalize()", "bind(address,uint256,uint256)", "rebind(address,uint256,uint256)",
    "unbind(address)", "setController(address)"]}

# The functions transcribed into test/replays/BalancerV1.t.sol and modelled below, located in the verified source
CITE = [("BConst.sol", r"uint public constant BONE "), ("BConst.sol", r"MIN_BPOW_BASE"), ("BConst.sol", r"MAX_BPOW_BASE"),
        ("BConst.sol", r"BPOW_PRECISION"), ("BConst.sol", r"MAX_IN_RATIO"), ("BConst.sol", r"MAX_OUT_RATIO"),
        ("BConst.sol", r"EXIT_FEE"), ("BConst.sol", r"MIN_BALANCE"),
        ("BNum.sol", "function btoi"), ("BNum.sol", "function bfloor"), ("BNum.sol", "function badd"),
        ("BNum.sol", "function bsub("), ("BNum.sol", "function bsubSign"), ("BNum.sol", "function bmul"),
        ("BNum.sol", "function bdiv"), ("BNum.sol", "function bpowi"), ("BNum.sol", "function bpow("),
        ("BNum.sol", "function bpowApprox"),
        ("BMath.sol", "function calcSpotPrice"), ("BMath.sol", "function calcOutGivenIn"),
        ("BMath.sol", "function calcInGivenOut"), ("BMath.sol", "function calcSingleInGivenPoolOut"),
        ("BMath.sol", "function calcSingleOutGivenPoolIn"),
        ("BPool.sol", "function exitPool"), ("BPool.sol", "function swapExactAmountIn"),
        ("BPool.sol", "function swapExactAmountOut"), ("BPool.sol", "function joinswapPoolAmountOut"),
        ("BPool.sol", "function exitswapPoolAmountIn")]


# ---------------------------------------------------------------------------------------------
# network: fetch
# ---------------------------------------------------------------------------------------------

def _call(url: str, to: str, data: str, block: str) -> str:
    return rpc(url, "eth_call", [{"to": to, "data": data}, block])


def _addr(w: int) -> str:
    return "0x" + hex(w)[2:].rjust(40, "0")


def _symbol(url: str, t: str, block: str) -> str:
    try:
        return decode_string(_call(url, t, sel("symbol()"), block))
    except RuntimeError:
        return "?"


def _decimals(url: str, t: str, block: str) -> int | None:
    try:
        return words(_call(url, t, sel("decimals()"), block))[0]
    except RuntimeError:
        return None


def _locate(text: str, needle: str) -> list[int]:
    """1-based [first, last] line of the declaration containing `needle` (a function body ends at its
    closing brace at the same indent; a constant is one line)."""
    lines = text.split("\n")
    for i, l in enumerate(lines):
        if needle in l:
            if "function" not in needle:
                return [i + 1, i + 1]
            indent = len(l) - len(l.lstrip())
            for j in range(i + 1, len(lines)):
                if lines[j].rstrip() == " " * indent + "}":
                    return [i + 1, j + 1]
    raise KeyError(needle)


def verified_source(address: str) -> dict:
    req = urllib.request.Request(f"{ROUTESCAN}?module=contract&action=getsourcecode&address={address}",
                                 headers={"User-Agent": "blockulator-replay/1.0"})
    r = json.load(urllib.request.urlopen(req, timeout=120))["result"][0]
    s = r["SourceCode"]
    if s.startswith("{{"):
        s = s[1:-1]
    j = json.loads(s)
    return {"contract": r["ContractName"], "compiler": r["CompilerVersion"], "optimizer": r["OptimizationUsed"] == "1",
            "runs": int(r["Runs"]), "evmVersion": r["EVMVersion"] or "default",
            "sources": {k: v["content"] for k, v in j["sources"].items()}}


def find_solc() -> str:
    p = Path.home() / ".local" / "share" / "svm" / SOLC["version"] / f"solc-{SOLC['version']}"
    if not p.exists():
        url = "https://binaries.soliditylang.org/linux-amd64/solc-linux-amd64-" + SOLC["long"]
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8"}), timeout=300).read()
        if hashlib.sha256(data).hexdigest() != SOLC["sha256"]:
            sys.exit("solc 0.5.12: checksum mismatch")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        p.chmod(0o755)
    return str(p)


def compile_bpool(src: dict) -> str:
    """Runtime bytecode of BPool from the verified sources with the verified settings. The files are
    compiled under contracts/ (balancer-labs/balancer-core's layout): the metadata hash records source
    paths, and with that prefix the whole runtime, metadata included, equals the chain's."""
    inp = {"language": "Solidity", "sources": {"contracts/" + k: {"content": v} for k, v in src["sources"].items()},
           "settings": {"optimizer": {"enabled": src["optimizer"], "runs": src["runs"]},
                        "outputSelection": {"contracts/BPool.sol": {"BPool": ["evm.deployedBytecode.object"]}}}}
    out = json.loads(subprocess.run([find_solc(), "--standard-json"], input=json.dumps(inp), capture_output=True,
                                    text=True, check=True).stdout)
    errs = [e for e in out.get("errors", []) if e["severity"] == "error"]
    if errs:
        sys.exit(json.dumps(errs, indent=1))
    return "0x" + out["contracts"]["contracts/BPool.sol"]["BPool"]["evm"]["deployedBytecode"]["object"]


def decode_ops(receipt: dict, pool: str, tokens: list[str]) -> list[dict]:
    """Every pool call in the transaction, in order, from the pool's LOG_CALL (anonymous: topic0 is the
    selector left-aligned, data is abi.encode(msg.data)), and its logged result."""
    idx = {t.lower(): i for i, t in enumerate(tokens)}
    ops: list[dict] = []
    for lg in receipt["logs"]:
        if lg["address"].lower() != pool.lower() or not lg["topics"]:
            continue
        t0 = lg["topics"][0][2:]
        d = lg["data"][2:]
        if t0[8:].strip("0") == "" and (t0[:8] in SEL or t0[:8] in OTHER_POOL_SELECTORS):
            if t0[:8] in OTHER_POOL_SELECTORS:
                raise SystemExit(f"{receipt['transactionHash']}: unmodelled pool call {OTHER_POOL_SELECTORS[t0[:8]]}")
            n = int(d[64:128], 16)
            cd = d[128:128 + 2 * n]
            a = [int(cd[8 + 64 * k:8 + 64 * (k + 1)], 16) for k in range((len(cd) - 8) // 64)]
            sig, kind = SEL[t0[:8]]
            op = {"log": int(lg["logIndex"], 16), "kind": kind, "call": sig.split("(")[0]}
            if kind in (SWAP_IN, SWAP_OUT):
                op.update(tokenIn=idx[_addr(a[0])], arg=str(a[1]), tokenOut=idx[_addr(a[2])], arg2=str(a[3]), maxPrice=str(a[4]))
            elif kind in (JOIN_POOL_OUT, EXIT_POOL_IN):
                op.update(token=idx[_addr(a[0])], arg=str(a[1]), limit=str(a[2]))
            else:  # exitPool(poolAmountIn, uint[] minAmountsOut): a[1] is the offset, a[2] the length
                op.update(arg=str(a[0]), minAmountsOut=[str(x) for x in a[3:3 + a[2]]])
            op["result"] = []
            ops.append(op)
        elif t0.startswith(T_SWAP):
            ops[-1]["result"] = [str(int(d[:64], 16)), str(int(d[64:128], 16))]  # tokenAmountIn, tokenAmountOut
        elif t0.startswith(T_JOIN) or t0.startswith(T_EXIT):
            ops[-1]["result"].append(str(int(d[:64], 16)))
    return ops


def flash_loans(receipt: dict) -> list[dict]:
    out = []
    for lg in receipt["logs"]:
        if lg["topics"] and lg["topics"][0][2:10] in FLASH:
            ev = FLASH[lg["topics"][0][2:10]]
            d = lg["data"][2:]
            if ev.startswith("Aave"):
                f = {"asset": "0x" + lg["topics"][2][26:], "amount": str(int(d[64:128], 16))}
            elif ev.startswith("Morpho"):
                f = {"asset": "0x" + lg["topics"][2][26:], "amount": str(int(d[:64], 16))}
            else:
                f = {"amount0": str(int(d[:64], 16)), "amount1": str(int(d[64:128], 16))}
            out.append({"lender": lg["address"], "event": ev, **f})
    return out


def tape(pool: dict) -> dict:
    """The calls as parallel string arrays for vm.parseJsonStringArray in test/replays/BalancerV1.t.sol:
    kind; i (tokenIn / token); j (tokenOut, else 0); x (amountIn / maxAmountIn / poolAmount); y (minAmountOut /
    amountOut / limit); r (the logged result: amountOut for SWAP_IN, amountIn for SWAP_OUT, the token amount
    for joins and single exits, 0 for exitPool, whose per-token results are in exitPoolOut)."""
    t = {k: [] for k in ("kind", "i", "j", "x", "y", "r")}
    ex = {}
    for op in pool["ops"]:
        k = op["kind"]
        t["kind"].append(str(k))
        if k in (SWAP_IN, SWAP_OUT):
            t["i"].append(str(op["tokenIn"])); t["j"].append(str(op["tokenOut"]))
            t["x"].append(op["arg"]); t["y"].append(op["arg2"])
            t["r"].append(op["result"][1] if k == SWAP_IN else op["result"][0])
        elif k in (JOIN_POOL_OUT, EXIT_POOL_IN):
            t["i"].append(str(op["token"])); t["j"].append("0")
            t["x"].append(op["arg"]); t["y"].append(op["limit"]); t["r"].append(op["result"][0])
        else:
            t["i"].append("0"); t["j"].append("0"); t["x"].append(op["arg"]); t["y"].append("0"); t["r"].append("0")
            ex = {"exitPoolOut": op["result"], "exitPoolMin": op["minAmountsOut"]}
    st = pool["state"]
    t.update(balance=[x["balance"] for x in st["tokens"]], denorm=[x["denorm"] for x in st["tokens"]],
             exitPoolOut=ex.get("exitPoolOut", []), exitPoolMin=ex.get("exitPoolMin", []))
    return t


def fetch(url: str) -> None:
    from Crypto.Hash import keccak
    src = verified_source(POOL1)
    fac = verified_source(BFACTORY)
    shared = sorted(k for k in src["sources"] if k in fac["sources"])
    same_as_factory = all(src["sources"][k] == fac["sources"][k] for k in shared)
    runtime = compile_bpool(src)
    cites = {}
    for f, needle in CITE:
        cites.setdefault(f, {})[needle.replace("function ", "").strip("( ").replace("uint public constant ", "")] = \
            _locate(src["sources"][f], needle)
    pools = []
    for h in TXS:
        rc = rpc(url, "eth_getTransactionReceipt", [h])
        tx = rpc(url, "eth_getTransactionByHash", [h])
        bn = int(rc["blockNumber"], 16)
        blk = rpc(url, "eth_getBlockByNumber", [hex(bn), False])
        joins = {}
        for lg in rc["logs"]:
            if lg["topics"] and lg["topics"][0][2:].startswith(T_JOIN):
                joins[lg["address"].lower()] = joins.get(lg["address"].lower(), 0) + 1
        pool = max(joins, key=joins.get)
        prev = hex(bn - 1)
        # the pool's state at the end of the previous block is the attack's starting state only if no
        # earlier transaction in the attack block touched it
        same_block = rpc(url, "eth_getLogs", [{"address": pool, "fromBlock": hex(bn), "toBlock": hex(bn)}])
        earlier = sorted({lg["transactionHash"] for lg in same_block if int(lg["transactionIndex"], 16) < int(rc["transactionIndex"], 16)})
        later = sorted({lg["transactionHash"] for lg in same_block if int(lg["transactionIndex"], 16) > int(rc["transactionIndex"], 16)})
        code = rpc(url, "eth_getCode", [pool, prev])
        toks = [_addr(x) for x in words(_call(url, pool, sel("getCurrentTokens()"), prev))[2:]]
        g = lambda f, *a: words(_call(url, pool, sel(f) + "".join(addr_word(x) for x in a), prev))[0]  # noqa: E731
        state = {
            "finalized": bool(g("isFinalized()")), "publicSwap": bool(g("isPublicSwap()")),
            "swapFee": str(g("getSwapFee()")), "totalWeight": str(g("getTotalDenormalizedWeight()")),
            "totalSupply": str(g("totalSupply()")), "controller": _addr(g("getController()")),
            "isBPool": bool(words(_call(url, BFACTORY, sel("isBPool(address)") + addr_word(pool), prev))[0]),
            "tokens": [{"address": t, "symbol": _symbol(url, t, prev),
                        "decimals": _decimals(url, t, prev),
                        "denorm": str(g("getDenormalizedWeight(address)", t)), "balance": str(g("getBalance(address)", t)),
                        "erc20BalanceOf": str(words(_call(url, t, sel("balanceOf(address)") + addr_word(pool), prev))[0])}
                       for t in toks],
        }
        ops = decode_ops(rc, pool, toks)
        pools.append({
            "tx": h, "block": bn, "txIndex": int(rc["transactionIndex"], 16),
            "time": datetime.fromtimestamp(int(blk["timestamp"], 16), timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "from": tx["from"], "to": tx["to"], "pool": pool, "stateBlock": bn - 1,
            "poolLogsEarlierInBlock": earlier, "poolLogsLaterInBlock": later,
            "codeKeccak": "0x" + keccak.new(digest_bits=256, data=bytes.fromhex(code[2:])).hexdigest(),
            "codeEqualsRecompiledBPool": code.lower() == runtime.lower(),
            "flashLoans": flash_loans(rc), "state": state, "ops": ops,
        })
        pools[-1]["tape"] = tape(pools[-1])
        print(f"{h[:10]} block {bn} pool {pool} ops {len(ops)} code==BPool {code.lower() == runtime.lower()} "
              f"isBPool {state['isBPool']} earlier {len(earlier)}", file=sys.stderr)
    out = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "rpc": url, "report": SLOWMIST,
        "source": {"address": POOL1, "via": ROUTESCAN,
                   "contract": src["contract"], "compiler": src["compiler"], "optimizer": src["optimizer"],
                   "runs": src["runs"], "evmVersion": src["evmVersion"],
                   "sha256": {k: hashlib.sha256(v.encode()).hexdigest() for k, v in sorted(src["sources"].items())},
                   "identicalToBFactoryVerifiedSources": same_as_factory, "bfactory": BFACTORY,
                   "runtimeKeccak": "0x" + keccak.new(digest_bits=256, data=bytes.fromhex(runtime[2:])).hexdigest(),
                   "lines": cites},
        "pools": pools,
    }
    DATA.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {DATA.relative_to(ROOT)}", file=sys.stderr)


# ---------------------------------------------------------------------------------------------
# offline: the deployed arithmetic, transcribed (verified source lines in balancer_v1.json "lines")
# ---------------------------------------------------------------------------------------------

U256 = 1 << 256
BONE = 10 ** 18
MIN_BPOW_BASE, MAX_BPOW_BASE = 1, 2 * BONE - 1
BPOW_PRECISION = BONE // 10 ** 10
MAX_IN_RATIO, MAX_OUT_RATIO = BONE // 2, BONE // 3 + 1
EXIT_FEE = 0


class Revert(Exception):
    pass


def _req(c: bool, msg: str) -> None:
    if not c:
        raise Revert(msg)


def badd(a, b):
    c = a + b
    _req(c < U256, "ERR_ADD_OVERFLOW")
    return c


def bsub(a, b):
    _req(a >= b, "ERR_SUB_UNDERFLOW")
    return a - b


def bsubSign(a, b):
    return (a - b, False) if a >= b else (b - a, True)


def bmul(a, b):  # half up on the 1e-18 grid
    c0 = a * b
    _req(c0 < U256, "ERR_MUL_OVERFLOW")
    c1 = c0 + BONE // 2
    _req(c1 < U256, "ERR_MUL_OVERFLOW")
    return c1 // BONE


def bdiv(a, b):  # half up on the 1e-18 grid
    _req(b != 0, "ERR_DIV_ZERO")
    c0 = a * BONE
    _req(c0 < U256, "ERR_DIV_INTERNAL")
    c1 = c0 + b // 2
    _req(c1 < U256, "ERR_DIV_INTERNAL")
    return c1 // b


def bpowi(a, n):
    z = a if n % 2 else BONE
    n //= 2
    while n:
        a = bmul(a, a)
        if n % 2:
            z = bmul(z, a)
        n //= 2
    return z


class Series:
    """What bpowApprox did on one call: iterations, the term that stopped it, its inputs."""
    def __init__(self):
        self.calls: list[dict] = []
        self.scale = 0  # the token balance the power multiplies, to size a residual in token units
        self.where = ""
        self.token = -1


def bpowApprox(base, exp, precision, rec: Series | None = None):
    a = exp
    x, xneg = bsubSign(base, BONE)
    term = BONE
    s = term
    negative = False
    i = 1
    while term >= precision:
        bigK = i * BONE
        c, cneg = bsubSign(a, bsub(bigK, BONE))
        term = bmul(term, bmul(c, x))
        term = bdiv(term, bigK)
        if term == 0:
            break
        if xneg:
            negative = not negative
        if cneg:
            negative = not negative
        s = bsub(s, term) if negative else badd(s, term)
        i += 1
    if rec is not None:
        # the loop body ran i - 1 times when the stopping rule ended it, i times when a zero term broke it
        rec.calls.append({"base": base, "exp": exp, "iterations": i - 1 if term != 0 else i, "lastTerm": term,
                          "zeroBreak": term == 0, "sum": s, "scale": rec.scale, "where": rec.where,
                          "token": rec.token})
    return s


def bpow(base, exp, rec: Series | None = None):
    _req(base >= MIN_BPOW_BASE, "ERR_BPOW_BASE_TOO_LOW")
    _req(base <= MAX_BPOW_BASE, "ERR_BPOW_BASE_TOO_HIGH")
    whole = (exp // BONE) * BONE
    remain = bsub(exp, whole)
    wholePow = bpowi(base, whole // BONE)
    if remain == 0:
        return wholePow
    return bmul(wholePow, bpowApprox(base, remain, BPOW_PRECISION, rec))


def calcSpotPrice(bI, wI, bO, wO, fee):
    return bmul(bdiv(bdiv(bI, wI), bdiv(bO, wO)), bdiv(BONE, bsub(BONE, fee)))


def calcOutGivenIn(bI, wI, bO, wO, aI, fee, rec=None):
    if rec is not None:
        rec.scale, rec.where = bO, "calcOutGivenIn"
    y = bdiv(bI, badd(bI, bmul(aI, bsub(BONE, fee))))
    return bmul(bO, bsub(BONE, bpow(y, bdiv(wI, wO), rec)))


def calcInGivenOut(bI, wI, bO, wO, aO, fee, rec=None):
    if rec is not None:
        rec.scale, rec.where = bI, "calcInGivenOut"
    y = bdiv(bO, bsub(bO, aO))
    foo = bsub(bpow(y, bdiv(wO, wI), rec), BONE)
    return bdiv(bmul(bI, foo), bsub(BONE, fee))


def calcSingleInGivenPoolOut(bI, wI, S, tW, P, fee, rec=None, steps=None):
    nw = bdiv(wI, tW)
    poolRatio = bdiv(badd(S, P), S)
    boo = bdiv(BONE, nw)
    tokenInRatio = bpow(poolRatio, boo, rec)
    newBal = bmul(tokenInRatio, bI)
    afterFee = bsub(newBal, bI)
    zar = bmul(bsub(BONE, nw), fee)
    out = bdiv(afterFee, bsub(BONE, zar))
    if steps is not None:
        steps.update(normalizedWeight=nw, poolRatio=poolRatio, boo=boo, tokenInRatio=tokenInRatio,
                     newTokenBalanceIn=newBal, tokenAmountInAfterFee=afterFee, zar=zar, tokenAmountIn=out)
    return out


def calcSingleOutGivenPoolIn(bO, wO, S, tW, P, fee, rec=None, steps=None):
    nw = bdiv(wO, tW)
    pAfter = bmul(P, bsub(BONE, EXIT_FEE))
    poolRatio = bdiv(bsub(S, pAfter), S)
    boo = bdiv(BONE, nw)
    tokenOutRatio = bpow(poolRatio, boo, rec)
    newBal = bmul(tokenOutRatio, bO)
    before = bsub(bO, newBal)
    zaz = bmul(bsub(BONE, nw), fee)
    out = bmul(before, bsub(BONE, zaz))
    if steps is not None:
        steps.update(normalizedWeight=nw, poolRatio=poolRatio, boo=boo, tokenOutRatio=tokenOutRatio,
                     newTokenBalanceOut=newBal, tokenAmountOutBeforeSwapFee=before, zaz=zaz, tokenAmountOut=out)
    return out


def replay(pool: dict, rec: Series | None = None) -> list[dict]:
    """Run every logged call through the transcription from the pinned state; assert each logged amount.
    Returns, per join / single-token exit, the state it ran on and the intermediate integers."""
    st = pool["state"]
    bal = [int(t["balance"]) for t in st["tokens"]]
    w = [int(t["denorm"]) for t in st["tokens"]]
    tW, fee, S = int(st["totalWeight"]), int(st["swapFee"]), int(st["totalSupply"])
    rows = []
    for k, op in enumerate(pool["ops"]):
        res = [int(x) for x in op["result"]]
        kind = op["kind"]
        if kind in (SWAP_IN, SWAP_OUT):
            i, o, mp_ = op["tokenIn"], op["tokenOut"], int(op["maxPrice"])
            if rec is not None:
                rec.token = o if kind == SWAP_IN else i
            before = calcSpotPrice(bal[i], w[i], bal[o], w[o], fee)
            _req(before <= mp_, "ERR_BAD_LIMIT_PRICE")
            if kind == SWAP_IN:
                aI, minOut = int(op["arg"]), int(op["arg2"])
                _req(aI <= bmul(bal[i], MAX_IN_RATIO), "ERR_MAX_IN_RATIO")
                aO = calcOutGivenIn(bal[i], w[i], bal[o], w[o], aI, fee, rec)
                _req(aO >= minOut, "ERR_LIMIT_OUT")
            else:
                maxIn, aO = int(op["arg"]), int(op["arg2"])
                _req(aO <= bmul(bal[o], MAX_OUT_RATIO), "ERR_MAX_OUT_RATIO")
                aI = calcInGivenOut(bal[i], w[i], bal[o], w[o], aO, fee, rec)
                _req(aI <= maxIn, "ERR_LIMIT_IN")
            bal[i] = badd(bal[i], aI)
            bal[o] = bsub(bal[o], aO)
            after = calcSpotPrice(bal[i], w[i], bal[o], w[o], fee)
            _req(after >= before, "ERR_MATH_APPROX")
            _req(after <= mp_, "ERR_LIMIT_PRICE")
            _req(before <= bdiv(aI, aO), "ERR_MATH_APPROX")
            assert [aI, aO] == res, (pool["tx"], k, op, aI, aO)
        elif kind == JOIN_POOL_OUT:
            t, P, lim = op["token"], int(op["arg"]), int(op["limit"])
            steps: dict = {}
            aI = calcSingleInGivenPoolOut(bal[t], w[t], S, tW, P, fee, rec, steps)
            _req(aI != 0, "ERR_MATH_APPROX")
            _req(aI <= lim, "ERR_LIMIT_IN")
            _req(aI <= bmul(bal[t], MAX_IN_RATIO), "ERR_MAX_IN_RATIO")
            rows.append({"op": k, "kind": kind, "token": t, "balance": bal[t], "weight": w[t], "totalWeight": tW,
                         "supply": S, "poolAmount": P, "limit": lim, "fee": fee, "deployed": aI, "steps": steps})
            bal[t] = badd(bal[t], aI)
            S = S + P
            assert [aI] == res, (pool["tx"], k, op, aI)
        elif kind == EXIT_POOL_IN:
            t, P, lim = op["token"], int(op["arg"]), int(op["limit"])
            steps = {}
            aO = calcSingleOutGivenPoolIn(bal[t], w[t], S, tW, P, fee, rec, steps)
            _req(aO >= lim, "ERR_LIMIT_OUT")
            _req(aO <= bmul(bal[t], MAX_OUT_RATIO), "ERR_MAX_OUT_RATIO")
            rows.append({"op": k, "kind": kind, "token": t, "balance": bal[t], "weight": w[t], "totalWeight": tW,
                         "supply": S, "poolAmount": P, "limit": lim, "fee": fee, "deployed": aO, "steps": steps})
            bal[t] = bsub(bal[t], aO)
            S = bsub(S, P - bmul(P, EXIT_FEE))
            assert [aO] == res, (pool["tx"], k, op, aO)
        elif kind == EXIT_POOL:
            P = int(op["arg"])
            ratio = bdiv(bsub(P, bmul(P, EXIT_FEE)), S)
            _req(ratio != 0, "ERR_MATH_APPROX")
            S = bsub(S, P)
            outs = []
            for j in range(len(bal)):
                aO = bmul(ratio, bal[j])
                _req(aO != 0, "ERR_MATH_APPROX")
                _req(aO >= int(op["minAmountsOut"][j]), "ERR_LIMIT_OUT")
                bal[j] = bsub(bal[j], aO)
                outs.append(aO)
            assert outs == res, (pool["tx"], k, outs, res)
    pool["_final"] = {"balances": bal, "supply": S}
    return rows


# ---------------------------------------------------------------------------------------------
# offline: score
# ---------------------------------------------------------------------------------------------

SYMBOL_FALLBACK = {"0x0ba45a8b5d5575935b8158a88c631e9f9c95a2e5": "TRB"}  # TellorMaster: symbol() reverted at the attack block
LENDERS = {"0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb": "Morpho Blue",
           "0xc13e21b648a5ee794902342038ff3adab66be987": "SparkLend Pool (Aave v3 fork; marketId \"Spark Protocol\")",
           "0x9359c87b38dd25192c5f2b07b351ac91c90e6ca7": "Uniswap V3 pool"}
DIGITS_CAP = 77


def _mp():
    from mpmath import mp
    mp.dps = 200
    return mp


def fp256_value(word: int):
    from mpmath import mpf
    w = word % (1 << 256)
    s, e, f = w >> 255, (w >> 236) & ((1 << 19) - 1), w & ((1 << 236) - 1)
    if e == 0:
        return mpf(0)
    v = mpf((1 << 236) + f) * mpf(2) ** (e - 262143 - 236)
    return -v if s else v


def digits(v, truth) -> float:
    from mpmath import log10, fabs
    if v == truth:
        return float(DIGITS_CAP)
    return min(DIGITS_CAP, float(-log10(fabs(v - truth) / fabs(truth))))


def run_forge(run: bool) -> tuple[dict, dict]:
    if run:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["forge", "test", "--match-path", "test/replays/BalancerV1.t.sol", "-vv"], cwd=ROOT,
                           capture_output=True, text=True)
        LOG.write_text(r.stdout + r.stderr)
        if r.returncode != 0:
            sys.exit(f"forge test failed; see {LOG.relative_to(ROOT)}")
    rows, sums = {}, {}
    for line in LOG.read_text().splitlines():
        line = line.strip()
        if line.startswith("BAL|"):
            _, p, k, kind, kv = line.split("|", 4)
            rows[(int(p), int(k))] = {a: int(b) for a, b in (x.split("=") for x in kv.strip(";").split(";"))}
        elif line.startswith("BALSUM|"):
            _, p, kv = line.split("|", 2)
            sums[int(p)] = {a: int(b) for a, b in (x.split("=") for x in kv.strip(";").split(";"))}
    if not rows:
        sys.exit(f"no BAL| lines in {LOG.relative_to(ROOT)}")
    return rows, sums


def exact_amount(r: dict):
    """The stated formula (BMath.sol comments above calcSingleInGivenPoolOut / calcSingleOutGivenPoolIn) at 200 digits."""
    from mpmath import mpf
    b, P, S, w, tW, fee = (mpf(r[k]) for k in ("balance", "poolAmount", "supply", "weight", "totalWeight", "fee"))
    f = (1 - w / tW) * fee / BONE
    if r["kind"] == JOIN_POOL_OUT:
        return b * ((1 + P / S) ** (tW / w) - 1) / (1 - f)
    return b * (1 - (1 - P / S) ** (tW / w)) * (1 - f)


def decompose(r: dict) -> dict:
    """deployed - exact, split along the deployed steps (a telescoping chain, so the parts sum to the total):
    power = the 18-decimal ratio (bdiv of the supplies, then bpowi's bmul squarings) vs the exact power;
    grid  = bmul(ratio, balance) rounded half up to a whole token unit (BMath.sol:174 / :215);
    fee   = the fee factor on BNum's grid (zar / zaz) and the last bdiv / bmul onto whole units (:180 / :222)."""
    from mpmath import mpf
    st = r["steps"]
    b, P, S, w, tW, fee = (mpf(r[k]) for k in ("balance", "poolAmount", "supply", "weight", "totalWeight", "fee"))
    f = (1 - w / tW) * fee / BONE
    q0 = exact_amount(r)
    if r["kind"] == JOIN_POOL_OUT:
        q1 = (b * mpf(st["tokenInRatio"]) / BONE - b) / (1 - f)
        q2 = mpf(st["tokenAmountInAfterFee"]) / (1 - f)
    else:
        q1 = (b - b * mpf(st["tokenOutRatio"]) / BONE) * (1 - f)
        q2 = mpf(st["tokenAmountOutBeforeSwapFee"]) * (1 - f)
    q3 = mpf(r["deployed"])
    return {"exact": q0, "power": q1 - q0, "grid": q2 - q1, "fee": q3 - q2, "total": q3 - q0}


def series_exact_terms(base: int, exp: int, tol) -> int:
    """Terms the same binomial series of (1 + x)^a needs, in exact arithmetic, before a term falls below tol."""
    from mpmath import mpf, fabs
    x = mpf(base) / BONE - 1
    a = mpf(exp) / BONE
    term, k = mpf(1), 0
    while fabs(term) >= tol:
        k += 1
        term = term * (a - (k - 1)) * x / k
        if k > 10000:
            break
    return k


def fmt(x, n=6) -> str:
    from mpmath import nstr
    return nstr(x, n)


def sym(t: dict) -> str:
    return t["symbol"] if t["symbol"] != "?" else SYMBOL_FALLBACK.get(t["address"].lower(), t["address"])


def cycle_rules(pool: dict, rows: list[dict]) -> dict:
    """The attacker's first join/exit pair at a balance of 3 units, re-tuned to each rounding rule from the same
    starting state: the BPT one unit buys on the join (P_j) and the BPT one unit costs on the following exit
    (P_x, from the supply after the join, at a balance of 4), and what one cycle nets as a share of the supply.
      deployed  the amounts the attacker actually used (BNum, half up at the token grid mid-computation)
      nearest   the exact formula, rounded to the nearest unit once: the join must cost < 1.5, the exit be worth >= 0.5
      toward    the exact formula, ceil in / floor out: the join must cost <= 1, the exit be worth >= 1"""
    from mpmath import mpf, ceil, floor
    j = next(r for r in rows if r["kind"] == JOIN_POOL_OUT and r["balance"] == 3)
    x = next(r for r in rows if r["op"] == j["op"] + 1)
    assert x["kind"] == EXIT_POOL_IN and x["balance"] == 4 and x["supply"] == j["supply"] + j["poolAmount"]
    S, b, w, tW = mpf(j["supply"]), mpf(3), mpf(j["weight"]), mpf(j["totalWeight"])
    f = (1 - w / tW) * mpf(j["fee"]) / BONE

    def cost(P):
        return b * ((1 + mpf(P) / S) ** (tW / w) - 1) / (1 - f)

    def worth(P, S2):
        return 4 * (1 - (1 - mpf(P) / S2) ** (tW / w)) * (1 - f)

    def pj(target):
        return S * ((1 + target * (1 - f) / b) ** (w / tW) - 1)

    def px(target, S2):
        return S2 * (1 - (1 - target / (4 * (1 - f))) ** (w / tW))

    out = {"op": j["op"], "supply": j["supply"], "deployed": (j["poolAmount"], x["poolAmount"])}
    jn = int(ceil(pj(mpf("1.5")))) - 1
    assert cost(jn) < mpf("1.5") <= cost(jn + 1)
    xn = int(ceil(px(mpf("0.5"), S + jn)))
    assert worth(xn, S + jn) >= mpf("0.5") > worth(xn - 1, S + jn)
    out["nearest"] = (jn, xn)
    jt = int(floor(pj(mpf(1))))
    assert cost(jt) <= 1 < cost(jt + 1)
    xt = int(ceil(px(mpf(1), S + jt)))
    assert worth(xt, S + jt) >= 1 > worth(xt - 1, S + jt)
    out["toward"] = (jt, xt)
    for k in ("deployed", "nearest", "toward"):
        a_, b_ = out[k]
        out[k] = {"join": a_, "exit": b_, "net": a_ - b_, "netShare": mpf(a_ - b_) / S,
                  "joinShare": mpf(a_) / S, "exitShare": mpf(b_) / (S + a_)}
    return out


def check_test_constants(cyc0: dict) -> None:
    """The Foundry test pins pool 1's re-tuned amounts as literals; they must be the ones solved here."""
    src = (ROOT / "test" / "replays" / "BalancerV1.t.sol").read_text()
    lit = {k: int(v) for k, v in re.findall(r"uint256 constant (\w+) = (\d+);", src)}
    assert lit["DECISIVE_SUPPLY"] == cyc0["supply"] and lit["DECISIVE_OP"] == cyc0["op"]
    assert lit["DECISIVE_POOL_OUT"] == cyc0["deployed"]["join"]
    assert (lit["NEAREST_JOIN_P"], lit["NEAREST_EXIT_P"]) == (cyc0["nearest"]["join"], cyc0["nearest"]["exit"])
    assert (lit["TOWARD_JOIN_P"], lit["TOWARD_EXIT_P"]) == (cyc0["toward"]["join"], cyc0["toward"]["exit"])


def score(run_forge_test: bool = True) -> None:
    _mp()
    from mpmath import mpf, ceil, floor
    data = json.loads(DATA.read_text())
    forge, sums = run_forge(run_forge_test)
    pools_out = []
    all_series = []
    for pi, pool in enumerate(data["pools"]):
        rec = Series()
        rows = replay(pool, rec)  # asserts every logged amount
        toks = pool["state"]["tokens"]
        for c in rec.calls:
            c["sym"], c["dec"] = sym(toks[c["token"]]), toks[c["token"]]["decimals"]
        all_series += [dict(c, pool=pi) for c in rec.calls]
        n_checked = sum(len(op["result"]) for op in pool["ops"])
        out_rows = []
        for r in rows:
            f = forge[(pi, r["op"])]
            # the Solidity transcription and the Python one agree on every intermediate integer
            for a, b in (("dep", "deployed"), ("bal", "balance"), ("S", "supply"), ("P", "poolAmount")):
                assert f[a] == r[b], (pi, r["op"], a)
            assert f["ratio"] == r["steps"]["tokenInRatio" if r["kind"] == JOIN_POOL_OUT else "tokenOutRatio"]
            ex = exact_amount(r)
            v127 = mpf(f["fp127"]) / mpf(2) ** 128
            v256 = fp256_value(f["fp256"])
            toward = int(ceil(ex)) if r["kind"] == JOIN_POOL_OUT else int(floor(ex))
            assert f["fp127u"] == toward and f["fp256u"] == toward, (pi, r["op"], "token units")
            d = decompose(r)
            out_rows.append({"op": r["op"], "log": pool["ops"][r["op"]]["log"], "kind": r["kind"],
                             "token": sym(toks[r["token"]]), "balance": r["balance"], "limit": r["limit"],
                             "poolAmount": r["poolAmount"], "supply": r["supply"], "share": mpf(r["poolAmount"]) / r["supply"],
                             "deployed": r["deployed"], "exact": ex, "toward": toward, "bnum1": f["bnum1"],
                             "fp127u": f["fp127u"], "fp256u": f["fp256u"], "nearest": int(floor(ex + mpf(1) / 2)),
                             "d127": digits(v127, ex), "d256": digits(v256, ex), "decomp": d, "steps": r["steps"]})
        fin = pool["_final"]
        joins = [o for o in out_rows if o["kind"] == JOIN_POOL_OUT]
        exits = [o for o in out_rows if o["kind"] == EXIT_POOL_IN]
        dust_exits = [o for o in exits if o["limit"] > 0]
        exit_pool = [op for op in pool["ops"] if op["kind"] == EXIT_POOL]
        cyc = cycle_rules(pool, rows)
        if pi == 0:
            check_test_constants(cyc)
        pools_out.append({"i": pi, "pool": pool, "rows": out_rows, "cycle": cyc, "joins": joins, "exits": exits, "dust": dust_exits,
                          "checked": n_checked, "series": rec.calls, "final": fin, "exitPool": exit_pool,
                          "minted": sum(o["poolAmount"] for o in joins),
                          "burned": sum(o["poolAmount"] for o in exits),
                          "sum": sums.get(pi, {})})
    write_md(data, pools_out, all_series)


def write_md(data: dict, P: list[dict], series: list[dict]) -> None:
    from mpmath import mpf, fabs
    from statistics import median
    L: list[str] = []
    a = L.append
    src = data["source"]
    lines = src["lines"]

    def cite(f, k):
        x = lines[f][k]
        return f"{f}:{x[0]}" if x[0] == x[1] else f"{f}:{x[0]}-{x[1]}"

    def short(h, n=10):
        return h[:n] + "…" + h[-4:]

    def units(v, dec):
        return f"{v / 10 ** dec:,.{min(dec, 8)}f}" if dec is not None else str(v)

    total_checked = sum(p["checked"] for p in P)
    total_ops = sum(len(p["pool"]["ops"]) for p in P)
    total_joins = sum(len(p["joins"]) for p in P)
    total_dust = sum(len(p["dust"]) for p in P)
    p0 = P[0]
    dec = next(o for o in p0["joins"] if o["op"] == 53)
    a("# Replay: the Balancer V1 drain of 31 August 2026")
    a("")
    a(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} by `uv run scripts/replays/balancer_v1.py score` "
      f"(offline) from `scripts/replays/balancer_v1.json` (fetched {data['generated']} by `balancer_v1.py fetch`). "
      "The Foundry replay is `test/replays/BalancerV1.t.sol`; it needs no network.")
    a("")
    a("## The answer first")
    a("")
    a(f"- **Five pools, not one.** SlowMist's five transactions hit five different Balancer V1 BPools, all deployed by "
      f"Balancer's own BFactory `{src['bfactory']}`, between {P[0]['pool']['time'][11:16]} and {P[-1]['pool']['time'][11:16]} UTC. "
      "SlowMist named only the first pool as the vulnerable contract.")
    a(f"- **Every attack join paid one token unit for about one and a half.** Across the {total_joins} joins "
      f"(`joinswapPoolAmountOut`, `maxAmountIn = 1`), the exact price was "
      f"{fmt(min(o['exact'] for p in P for o in p['joins']), 8)} to {fmt(max(o['exact'] for p in P for o in p['joins']), 8)} units. "
      f"The deployed maths charged 1 every time. In the opposite direction, each of the {total_dust} dust exits "
      f"(`exitswapPoolAmountIn`, `minAmountOut = 1`) was worth {fmt(min(o['exact'] for p in P for o in p['dust']), 6)} to "
      f"{fmt(max(o['exact'] for p in P for o in p['dust']), 6)} units, and the pool paid 1.")
    a("- **The loss is one rounding step.** `bmul(tokenInRatio, tokenBalanceIn)` "
      f"({cite('BMath.sol', 'calcSingleInGivenPoolOut')}, line 174) multiplies an 18-decimal ratio by a balance held in raw "
      "token units: satoshi for WBTC and renBTC, 10^-6 for USDC. `bmul` rounds half up "
      f"({cite('BNum.sol', 'bmul')}). At a balance of 3 units, 3 × 1.499999999999999997 = 4.499999999999999991 rounds "
      "to 4 rather than 5, so the attacker pays 1. On an exit, 3.4999… rounds down, so the pool pays out 1.")
    a("- **The binomial series is not involved.** In every attacked pool the attacked token's normalized weight is "
      "1/4, 1/8 or 1/10. So `boo = 1/w` is a whole number, and `bpow` returns from `bpowi` "
      f"({cite('BNum.sol', 'bpow')}). `bpowApprox` is never called in any join or exit. Where it did run (in "
      f"{len(series)} swap calculations), it stopped at a term below 1e-10, and its residual against the exact "
      f"power was at most {fmt(max(_series_rel(c) for c in series), 2)} relative.")
    c0 = P[0]["cycle"]
    a("- **Direction closes the loop; precision does not.** FP127, FP256 and 200-digit mpmath, each rounded toward "
      "the pool (ceil in, floor out), give 2 for every join and 0 for every dust exit, so every one of them reverts "
      "on the attacker's own limits. BNum's own 18-decimal ratio, kept on a 10^-18 grid and rounded up once at the "
      "end, gives the same answers. But the same exact formula rounded once *to nearest* only blocks these calls "
      "because the attacker tuned them to the deployed rounding. Re-tuned to nearest-once from the same state, "
      f"one join/exit cycle in pool 1 still nets {fmt(c0['nearest']['netShare'] * 100, 4)}% of the BPT supply "
      f"(deployed: {fmt(c0['deployed']['netShare'] * 100, 4)}%). Toward the pool it nets "
      f"{fmt(c0['toward']['netShare'] * 100, 3)}%, a loss. The deployed ratio had 18 correct digits. What it lacked "
      "was a rounding direction at the token grid.")
    a("")

    # ---- what happened
    a("## What happened")
    a("")
    a("All five attacks followed the same loop. The attacker flash-borrowed from "
      + ", ".join(sorted({LENDERS.get(f['lender'].lower(), f['lender']) for p in P for f in p['pool']['flashLoans']}))
      + ". The loans were nested. With them, the attacker used public swaps to push one token's pool balance down to "
      "a few raw units (`swapExactAmountOut` for 1 unit at a time near the end, which `MAX_OUT_RATIO` allows down to "
      "a balance of 2). It then alternated a join of 1 unit for a chosen BPT amount with an exit of a smaller BPT "
      "amount for 1 unit. Each join/exit pair returns the balance to where it started and leaves the attacker with "
      "more BPT. Finally the attacker swapped the token back in and redeemed the accumulated BPT. In four pools that "
      "was one proportional `exitPool`; in the eight-token pool it was single-token exits with `minAmountOut = 0`. "
      "`MIN_BALANCE` is checked only in `bind`/`rebind`, so nothing stops a swap from taking a balance to dust.")
    a("")
    a("| # | tx | block, time (UTC) | pool | tokens (weight) | swap fee | attacked token | its balance before → in the loop | joins / exits | BPT minted / burned in the loop | BPT redeemed at the end |")
    a("|---|---|---|---|---|---|---|---|---|---|---|")
    for p in P:
        pool = p["pool"]
        st = pool["state"]
        tw = int(st["totalWeight"])
        toks = ", ".join(f"{sym(t)} ({int(t['denorm']) * 100 / tw:g}%)" for t in st["tokens"])
        att = Counter_most(o["token"] for o in p["joins"])
        ai = next(i for i, t in enumerate(st["tokens"]) if sym(t) == att)
        loop_bal = Counter_most(o["balance"] for o in p["joins"])
        if p["exitPool"]:
            red = f"{int(p['exitPool'][0]['arg']) / 1e18:,.6f} (`exitPool`)"
        else:
            red = f"{sum(o['poolAmount'] for o in p['exits'] if o['limit'] == 0) / 1e18:,.6f} ({sum(1 for o in p['exits'] if o['limit'] == 0)} × `exitswapPoolAmountIn`, min 0)"
        a(f"| {p['i'] + 1} | [`{short(pool['tx'])}`](https://etherscan.io/tx/{pool['tx']}) | {pool['block']}, {pool['time'][11:19]} | "
          f"`{pool['pool']}` | {toks} | {int(st['swapFee']) / 1e16:g}% | {att} | {st['tokens'][ai]['balance']} → {loop_bal} units | "
          f"{len(p['joins'])} / {len(p['exits'])} | {p['minted'] / 1e18:,.6f} / {sum(o['poolAmount'] for o in p['dust']) / 1e18:,.6f} | {red} |")
    a("")
    net0 = p0["minted"] - sum(o["poolAmount"] for o in p0["dust"])
    a(f"The \"4,408.8 BPT\" in the reports is the first pool's final `exitPool` of {int(p0['exitPool'][0]['arg'])} wei. "
      f"It is the net of the loop: {len(p0['joins'])} one-satoshi joins minted {p0['minted'] / 1e18:,.6f} BPT, "
      f"{len(p0['dust'])} one-satoshi exits burned {sum(o['poolAmount'] for o in p0['dust']) / 1e18:,.6f}, and the difference is "
      f"{net0} wei, exactly the amount redeemed. No single satoshi minted 4,408.8 BPT. Each one bought between "
      f"{fmt(min(o['share'] for o in p0['joins']) * 100, 4)}% and {fmt(max(o['share'] for o in p0['joins']) * 100, 4)}% of "
      f"the supply at the time. The pool's supply before the attack was {int(p0['pool']['state']['totalSupply']) / 1e18:.6f} BPT.")
    a("")
    a("What left each pool (balance before the attack → after, in token units; from the replay):")
    a("")
    a("| # | token | before | after | taken |")
    a("|---|---|---|---|---|")
    for p in P:
        st = p["pool"]["state"]
        for j, t in enumerate(st["tokens"]):
            b0, b1 = int(t["balance"]), p["final"]["balances"][j]
            if b1 != b0:
                dd = t["decimals"]
                a(f"| {p['i'] + 1} | {sym(t)} | {units(b0, dd)} | {units(b1, dd)} | {(b0 - b1) / b0 * 100:.2f}% |")
    a("")

    # ---- decisive join
    s = dec["steps"]
    a("## The decisive join, in integers")
    a("")
    a(f"Pool 1 (`{p0['pool']['pool']}`), call {dec['op']} of {len(p0['pool']['ops'])} in tx `{short(p0['pool']['tx'])}` "
      f"(LOG_CALL at log index {hex(dec['log'])}) is the first join against a WBTC balance of 3 satoshi: "
      f"`joinswapPoolAmountOut(WBTC, {dec['poolAmount']}, 1)` with pool supply {dec['supply']}. "
      "`test_decisive_join` asserts every integer below; `test_decisive_join_matches_the_replay` checks that this is "
      "the replay's state at that call.")
    a("")
    a("| step (BMath.sol) | deployed integer | value | exact |")
    a("|---|---|---|---|")
    S_, Pa = mpf(dec["supply"]), mpf(dec["poolAmount"])
    a(f"| normalizedWeight = bdiv(wI, tW) (:167) | {s['normalizedWeight']} | 0.25 | 0.25 |")
    a(f"| poolRatio = bdiv(pS + pAo, pS) (:169) | {s['poolRatio']} | {fmt(mpf(s['poolRatio']) / BONE, 19)} | {fmt(1 + Pa / S_, 25)} |")
    a(f"| boo = bdiv(BONE, normalizedWeight) (:172) | {s['boo']} | 4 | 4 |")
    a(f"| tokenInRatio = bpow(poolRatio, boo) (:173) → bpowi, no series | {s['tokenInRatio']} | {fmt(mpf(s['tokenInRatio']) / BONE, 19)} | {fmt((1 + Pa / S_) ** 4, 25)} |")
    a(f"| newTokenBalanceIn = bmul(tokenInRatio, 3) (:174) | {s['newTokenBalanceIn']} | 4.499999999999999991 → **4** | {fmt(3 * (1 + Pa / S_) ** 4, 25)} |")
    a(f"| tokenAmountInAfterFee (:175) | {s['tokenAmountInAfterFee']} | 1 | {fmt(3 * (1 + Pa / S_) ** 4 - 3, 25)} |")
    a(f"| zar = bmul(1 − 0.25, 0.5%) (:179) | {s['zar']} | 0.00375 | 0.00375 |")
    a(f"| tokenAmountIn = bdiv(afterFee, 1 − zar) (:180) | {s['tokenAmountIn']} | 1.0038 → **1** | **{fmt(dec['exact'], 25)}** |")
    a("")
    a(f"The attacker sized `poolAmountOut` so that BNum's ratio landed 3 × 10^-18 below 1.5. That puts the new balance "
      f"9 × 10^-18 satoshi below the half-way point between 4 and 5 satoshi, so it rounds down. The integer survives "
      f"in every pool: in the replay the deployed `tokenInRatio` at a balance of 3 is always just under 1.5 "
      f"({', '.join(sorted({str(o['steps']['tokenInRatio']) for p in P for o in p['joins'] if o['balance'] == 3}))}). "
      f"At a balance of 7 it is just under 8.5/7, and at the eight-token pool's USDC balance of 38 it is just under 39.5/38.")
    a("")

    # ---- table
    a("## Every join and exit: deployed, toward the pool, and exact")
    a("")
    a("Each column computes the same `calcSingleInGivenPoolOut` / `calcSingleOutGivenPoolIn` from the same on-chain "
      "state (the replay's state at that call). Every column except *deployed* converts to token units once, toward "
      "the pool: ceil for an amount in, floor for an amount out. *BNum, one rounding* keeps BNum's own 18-decimal "
      "`tokenInRatio`, holds the amount on a 10^-18 grid, and rounds once at the end. FP127 and FP256 evaluate "
      "`b·expm1((tW/w)·log1p(±pA/pS))` with the fee factor. *Digits* is −log10 of the relative error against "
      "200-digit mpmath before rounding. *Pays?* asks whether the attacker's own limit (maxAmountIn = 1, "
      "minAmountOut = 1) would still be met. The last column rounds the exact value to the nearest unit once, "
      "for the section after this one.")
    a("")
    a("| # | call | n | balance (units) | deployed | exact (range) | BNum, one rounding | FP127 | FP256 | exact, rounded | FP127 digits (min) | FP256 digits (min) | pays? | exact, nearest once |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for p in P:
        for label, grp in (("join, max in 1", p["joins"]), ("exit, min out 1", p["dust"])):
            if not grp:
                continue
            bals = sorted({o["balance"] for o in grp})
            one = lambda key: ", ".join(str(x) for x in sorted({o[key] for o in grp}))  # noqa: E731
            pays = sum(1 for o in grp if (o["toward"] <= o["limit"] if o["kind"] == JOIN_POOL_OUT else o["toward"] >= o["limit"]))
            a(f"| {p['i'] + 1} | {label} | {len(grp)} | {', '.join(map(str, bals))} | {one('deployed')} | "
              f"{fmt(min(o['exact'] for o in grp), 8)} – {fmt(max(o['exact'] for o in grp), 8)} | {one('bnum1')} | "
              f"{one('fp127u')} | {one('fp256u')} | {one('toward')} | {min(o['d127'] for o in grp):.2f} | "
              f"{min(o['d256'] for o in grp):.2f} | {'no' if pays == 0 else f'{pays} of {len(grp)}'} | {one('nearest')} |")
    big = [o for p in P for o in p["exits"] if o["limit"] == 0]
    if big:
        a("")
        a(f"Pool 2 was redeemed with {len(big)} single-token exits at real size (`minAmountOut = 0`). Those are not "
          f"part of the rounding loop. Their deployed amounts differ from the exact ones by at most "
          f"{fmt(max(fabs(o['decomp']['total'] / o['exact']) for o in big), 3)} relative, which is BNum's 18 digits "
          "doing what it promises.")
    a("")

    # ---- precision or direction
    a("## Precision or direction?")
    a("")
    a("The last column of the table above also blocks these calls: 1.5056 rounds to 2, and 0.498 rounds to 0. "
      "That is only because the attacker tuned each call to the deployed arithmetic. The question for a pool is "
      "what an attacker can get once it tunes to the pool's rule. Each row below starts from the state of each "
      "pool's first join at a balance of 3 units. It solves, at 200 digits, for the most BPT one unit buys on the "
      "join and the least BPT one unit costs on the exit that follows (at a balance of 4, from the supply after the "
      "join). Then it reports what one join/exit cycle nets the attacker. The balance is back at 3 after each "
      "cycle, so the cycle repeats.")
    a("")
    a("| # | rule | BPT for 1 unit in (% of supply) | BPT for 1 unit out (% of supply) | net per cycle (% of supply) |")
    a("|---|---|---|---|---|")
    names = {"deployed": "deployed (the attacker's own amounts)", "nearest": "exact formula, nearest once (FP127 / FP256 / mpmath)",
             "toward": "exact formula, toward the pool (ceil in, floor out)"}
    for p in P:
        for k in ("deployed", "nearest", "toward"):
            c = p["cycle"][k]
            a(f"| {p['i'] + 1} | {names[k]} | {c['join'] / 1e18:.6f} ({fmt(c['joinShare'] * 100, 4)}%) | "
              f"{c['exit'] / 1e18:.6f} ({fmt(c['exitShare'] * 100, 4)}%) | **{fmt(c['netShare'] * 100, 4)}%** |")
    a("")
    a("With full precision and round-to-nearest, the loop is almost exactly as profitable as it was on chain. "
      "38 or 71 digits do not help when the last step can round half a unit in the caller's favour. Rounded toward "
      "the pool, the loop runs backwards: each cycle leaves the swap fee in the pool. "
      "`test_precision_without_direction_still_pays` and `test_direction_closes_the_loop` assert pool 1's row in "
      "FP127 and FP256 (`score` checks the test's literals against these solutions).")
    a("")

    # ---- decomposition
    a("## Where the half unit goes")
    a("")
    a("deployed − exact, split along the deployed steps (the parts sum to the total). *power* is the 18-decimal ratio "
      "(`bdiv` of the supplies, then `bpowi`'s `bmul` squarings) against the exact power, times the balance. *grid* "
      "is `bmul(ratio, balance)` rounded half up to a whole token unit. *fee* is the fee factor on BNum's grid plus "
      "the last `bdiv` / `bmul` onto whole units. Token units; the range is over the calls.")
    a("")
    a("| # | call | total | power (18-dec ratio, bpowi) | grid (new balance to whole units) | fee step |")
    a("|---|---|---|---|---|---|")
    for p in P:
        for label, grp in (("join", p["joins"]), ("dust exit", p["dust"])):
            if not grp:
                continue
            rng = lambda k: f"{fmt(min(o['decomp'][k] for o in grp), 4)} … {fmt(max(o['decomp'][k] for o in grp), 4)}"  # noqa: E731
            a(f"| {p['i'] + 1} | {label} | {rng('total')} | {rng('power')} | {rng('grid')} | {rng('fee')} |")
    a("")
    a("The 18-decimal maths in front of the grid (the ratio and `bpowi`) is off by at most "
      f"{fmt(max(fabs(o['decomp']['power']) for p in P for o in p['joins'] + p['dust']), 2)} token units. On a join, "
      "the grid step alone moves the result by −0.5 units; on an exit, by +0.5. The fee step rounds the remaining "
      "≈ 1.004 (join) or ≈ 0.996 (exit) to 1.")
    a("")

    # ---- series
    it = [c["iterations"] for c in series]
    res = []
    for c in series:
        ex = (mpf(c["base"]) / BONE) ** (mpf(c["exp"]) / BONE)
        res.append(fabs(mpf(c["sum"]) / BONE - ex) / ex)
    t127 = [series_exact_terms(c["base"], c["exp"], mpf(2) ** -128) for c in series]
    t256 = [series_exact_terms(c["base"], c["exp"], mpf(2) ** -237) for c in series]
    t1e10 = [series_exact_terms(c["base"], c["exp"], mpf(10) ** -10) for c in series]
    xs = [fabs(mpf(c["base"]) / BONE - 1) for c in series]
    a("## bpowApprox: measured, and not the step that loses")
    a("")
    a(f"`bpow(base, exp)` ({cite('BNum.sol', 'bpow')}) splits the exponent. The whole part goes to `bpowi`, square "
      f"and multiply with `bmul` at every step ({cite('BNum.sol', 'bpowi')}). Only a fractional part goes to "
      f"`bpowApprox` ({cite('BNum.sol', 'bpowApprox')}), the binomial series of (1 + x)^a, which stops after the first "
      f"term below `BPOW_PRECISION` = BONE / 10^10 = 10^8 wei = 10^-10 ({cite('BConst.sol', 'BPOW_PRECISION')}). "
      "That stopping term is still added.")
    a("")
    a(f"- **In the {total_joins} joins and {sum(len(p['exits']) for p in P)} single-token exits: zero calls.** "
      "The exponent is tW/wI = 4, 8 or 10 (`boo % BONE == 0`, asserted on every call in the Foundry replay). The "
      "decisive ratio comes from two or three `bmul` squarings, each rounding half up at 10^-18.")
    a(f"- **In the swaps that built the dust balance: {len(series)} calls** (pools "
      f"{', '.join(str(i + 1) for i in sorted({c['pool'] for c in series}))}, where weight ratios such as 12.5/17.5 "
      f"are not whole). |x| = |base − 1| ranged {fmt(min(xs), 3)} – {fmt(max(xs), 3)}. The loop ran "
      f"{min(it)} – {max(it)} iterations (median {median(it):g}); "
      f"{sum(1 for c in series if c['zeroBreak'])} of them ended on a term that rounded to zero rather than on the "
      f"tolerance. The relative residual against the exact power (base^frac at 200 digits) is "
      f"{fmt(min(res), 2)} – {fmt(max(res), 2)}. Times the balance it multiplies, that is at most "
      f"{_series_worst(series)}. For an 18-decimal token with a large balance, this is more than one raw unit: "
      "the stopping rule does show in swap amounts. It is not what moved this attack.")
    a(f"- **The same series, run in exact arithmetic to each ruler's tolerance**, needs {min(t1e10)} – {max(t1e10)} terms "
      f"to reach 10^-10 (BNum's own rule without BNum's rounding), {min(t127)} – {max(t127)} terms to reach 2^-128 "
      f"(FP127's ulp at 1), and {min(t256)} – {max(t256)} to reach 2^-237 (FP256's relative ulp). The series does "
      "converge, and a finer ruler only means more terms. Had the series run at the decisive join, the largest "
      f"residual measured here ({fmt(max(res), 2)}) times a 3-unit balance would be "
      f"{fmt(max(res) * 3, 2)} units, about nine orders of magnitude below the half-unit grid step that decided "
      "the outcome.")
    a("")
    a("For the talk: in this incident the stopping ruler did not decide the answer, because the series never ran "
      "where it mattered. What decided it was a coarser ruler: whole token units, applied in the middle of the "
      "computation, rounding to nearest, against a balance that the attacker had made three units long.")
    a("")

    # ---- provenance
    a("## Provenance")
    a("")
    a(f"- **Transactions**: the five listed in SlowMist's alert ({data['report']}). Receipts and state come from "
      f"`{data['rpc']}`, keyless and read-only (eth_getTransactionReceipt, eth_call and eth_getCode at block − 1, "
      "eth_getLogs). Nothing was signed or sent.")
    a("- **Calls**: decoded from each pool's anonymous `LOG_CALL(bytes4 indexed sig, address indexed caller, bytes data)`, "
      "which BPool's `_logs_` modifier emits with the full calldata. Results come from `LOG_SWAP` / `LOG_JOIN` / "
      f"`LOG_EXIT`. {total_ops} calls in total; {total_checked} logged amounts reproduced exactly by the Python "
      "transcription and again by the Solidity one, swaps and `exitPool` included.")
    a("- **State**: `getCurrentTokens`, `getDenormalizedWeight`, `getBalance` (the pool's internal record, which is what "
      "the maths reads), `getTotalDenormalizedWeight`, `getSwapFee` and `totalSupply` at block − 1. For every pool, "
      "`eth_getLogs` over the attack block shows no earlier transaction touching it, so block − 1 is the attack's "
      "starting state. All five pools were finalized with public swap on, and `BFactory.isBPool(pool)` is true for each.")
    a(f"- **Code**: the BPool source verified on Etherscan for `{src['address']}` ({src['compiler']}, optimizer "
      f"{src['runs']} runs, default EVM) was fetched through Routescan's Etherscan-compatible API. Its files are "
      f"byte-identical to the sources verified for BFactory `{src['bfactory']}` "
      f"({'yes' if src['identicalToBFactoryVerifiedSources'] else 'NO'}). `fetch` recompiles them with solc 0.5.12 "
      "(sha256-checked from binaries.soliditylang.org) under `contracts/`, which is balancer-labs/balancer-core's "
      f"layout and is what the metadata hash records. The runtime bytecode, metadata included, equals "
      f"`eth_getCode` for all five pools "
      f"({', '.join('yes' if p['pool']['codeEqualsRecompiledBPool'] else 'NO' for p in P)}; runtime keccak "
      f"`{src['runtimeKeccak']}`).")
    a("- **Transcribed lines** (file sha256 in the JSON): "
      + "; ".join(f"`{cite(f, k)}` {k}" for f, ks in lines.items() for k in ks) + ".")
    a("- **Flash loans** (from the receipts): "
      + "; ".join(f"tx {p['i'] + 1}: " + ", ".join(sorted({LENDERS.get(f['lender'].lower(), f['lender']) for f in p['pool']['flashLoans']}))
                  for p in P) + ".")
    a("")

    # ---- contradictions
    a("## Where this differs from the reports")
    a("")
    a("- \"A pool drained of ~$234K\": the attacker drained five BPools in five transactions over 68 minutes. Whether "
      "$234K covers one pool or all five is not stated. This replay counts tokens, not dollars (table above).")
    a("- \"1 satoshi minted 4,408.8 BPT\": each 1-satoshi join minted "
      f"{fmt(min(o['share'] for o in p0['joins']) * 100, 4)}–{fmt(max(o['share'] for o in p0['joins']) * 100, 4)}% "
      f"of the supply at that moment ({min(o['poolAmount'] for o in p0['joins']) / 1e18:.4f} to "
      f"{max(o['poolAmount'] for o in p0['joins']) / 1e18:.4f} BPT, growing as the attacker's own BPT grew the "
      f"supply). The figure 4,408.8 is the net of {len(p0['joins'])} joins and {len(p0['dust'])} exits, redeemed in "
      "one `exitPool`.")
    a("- \"Rounded down to 1 satoshi\" by \"18-decimal fixed-point maths\": the 18-decimal part was accurate to 18 "
      "digits. The rounding that mattered is `bmul` of that ratio by a balance in raw units, which rounds to the "
      "nearest satoshi (or 10^-6 USDC). The required input is 1.5 units and rounds half up to 1, because the "
      "attacker placed it just below the half. The exits get the mirror image: 0.5 units paid out as 1.")
    a("- \"Flash loans from Aave, Spark, Morpho and Uniswap V3\": the receipts show SparkLend (an Aave v3 fork) and "
      "Morpho Blue in every transaction, and a Uniswap V3 flash in the first. No Aave v3 Pool `FlashLoan` event appears.")
    a("- Two of the five pools were not WBTC pools: pool 3's attacked token is USDC and pool 4's is renBTC. The "
      "eight-token pool 2 was attacked on USDC (with WETH and DAI joins and exits too).")
    a("")

    # ---- fix
    a("## What fixed it")
    a("")
    a("Nothing in V1 has changed. BPools have no admin pause and no upgrade path, and a finalized pool's maths is "
      "fixed. On 31 August Balancer warned LPs to withdraw from the deprecated V1 pools, proportionally, through "
      "legacy.balancer.fi; the pools are non-pausable, and Balancer said other products were unaffected. That is as "
      "reported by The Defiant, ChainCatcher and CryptoTicker; the original post was not retrievable here. I found "
      "no Balancer advice addressed to forks. The forks' exposure follows from this replay: any fork that keeps "
      "`calcSingleInGivenPoolOut` / `calcSingleOutGivenPoolIn` on raw balances with half-up `bmul`, and lets swaps "
      "take a balance to dust, is open to the same loop. The repair the numbers point to is rounding toward the "
      "pool at the token grid: up for amounts in, down for amounts out. Any of the four *toward the pool* columns "
      "above blocks every step of the loop. Balancer V2 does this in its FixedPoint (`mulUp`/`divUp` versus "
      "`mulDown`/`divDown`, chosen per step in its WeightedMath), and it scales balances to 18 decimals before any "
      "of that maths. A minimum balance enforced on swaps, not only in `bind`, would also have stopped the setup.")
    a("")
    a("## Caveat")
    a("")
    a("The counterfactuals are each evaluated at the on-chain state of that call. In a world where the pool rounded "
      "toward itself, the first join would have reverted and the later states would never have existed. The test "
      "shows that every step of this attack would fail; it does not show that no other sequence could profit.")
    a("")
    a("## Reproduce")
    a("")
    a("```")
    a("forge test --match-path test/replays/BalancerV1.t.sol        # offline: replay, asserts, decisive join")
    a("uv run scripts/replays/balancer_v1.py score                  # offline: runs the test, scores at 200 digits, writes this page")
    a("uv run scripts/replays/balancer_v1.py fetch                  # network (read-only): refetch receipts, state, source; recompile")
    a("```")
    OUT_MD.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT_MD.relative_to(ROOT)}", file=sys.stderr)


def _series_rel(c: dict):
    from mpmath import mpf, fabs
    ex = (mpf(c["base"]) / BONE) ** (mpf(c["exp"]) / BONE)
    return fabs(mpf(c["sum"]) / BONE - ex) / ex


def _series_worst(series: list[dict]) -> str:
    c = max(series, key=_series_token_err)
    e = _series_token_err(c)
    return f"{fmt(e, 3)} raw units of {c['sym']} ({fmt(e / mpf_(10) ** c['dec'], 3)} {c['sym']}, in {c['where']})"


def mpf_(x):
    from mpmath import mpf
    return mpf(x)


def _series_token_err(c: dict):
    from mpmath import mpf, fabs
    ex = (mpf(c["base"]) / BONE) ** (mpf(c["exp"]) / BONE)
    return fabs(mpf(c["sum"]) / BONE - ex) * c["scale"]


def Counter_most(it):
    from collections import Counter
    return Counter(it).most_common(1)[0][0]


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "score"
    if mode == "fetch":
        fetch(sys.argv[2] if len(sys.argv) > 2 else ARCHIVE_RPC)
    elif mode == "score":
        score("--no-forge" not in sys.argv)
    else:
        sys.exit(__doc__)

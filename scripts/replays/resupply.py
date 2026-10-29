#!/usr/bin/env python3
"""Resupply replay: the 26 June 2025 ResupplyPair exploit, one division at a time.

    uv run scripts/replays/resupply.py fetch    # network: trace, logs, state and verified source -> scripts/replays/resupply.json
    uv run scripts/replays/resupply.py          # offline: forge test -> exact scoring -> docs/benchmarks/replay-resupply.md
    uv run scripts/replays/resupply.py --score  # offline: re-score the last forge log only

The attack transaction (0xffbbd492...72d3, block 22785461, index 0) donated
crvUSD into the empty cvcrvUSD ERC-4626 vault, minted one share wei, posted it
as collateral and borrowed 10,000,000 reUSD. `fetch` pins every integer the
pair's solvency check used, each from the call trace (debug_traceTransaction,
callTracer), the transaction's own event logs, or an eth_call at the block
before (pre-state) and the block itself (post-state), and checks every cited
source line against the verified source on Sourcify. The forge test
(test/replays/Resupply.t.sol) replays the decisive arithmetic from those
integers with no network, asserts it equals what happened on chain, and runs
the same step through divUp, divide-at-the-end, BL127 and BL19. This script
scores each against exact rational arithmetic (Python Fraction, with mpmath at
200 digits for the digit counts).

Read-only: no transactions, no keys. RPC endpoints are public and keyless.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from fractions import Fraction
from math import ceil, floor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "replays"
PINS = HERE / "resupply.json"
LOG = ROOT / "out" / "replays" / "resupply.log"
OUT_MD = ROOT / "docs" / "benchmarks" / "replay-resupply.md"
TEST = "test/replays/Resupply.t.sol"

sys.path.insert(0, str(ROOT / "scripts" / "accrual"))

TX = "0xffbbd492e0605a8bb6d490c3cd879e87ff60862b0684160d08fd5711e7a872d3"
# Public keyless endpoints. eth.drpc.org serves debug_traceTransaction and archive eth_call.
TRACE_RPC = os.environ.get("REPLAY_TRACE_RPC", "https://eth.drpc.org")
STATE_RPC = os.environ.get("REPLAY_STATE_RPC", "https://eth.drpc.org")
SOURCIFY = "https://sourcify.dev/server/v2/contract/1/{}?fields=sources,compilation,deployment,runtimeBytecode"

A = {
    "pair": "0x6e90c85a495d54c6d7e1f3400fef1f6e59f86bd6",        # ResupplyPair (cvcrvUSD collateral)
    "oracle": "0xcb7e25fbbd8afe4ce73d7dac647dbc3d847f3c82",      # BasicVaultOracle
    "vault": "0x01144442fba7adccb5c9dc9cf33dd009d50a9e1d",       # cvcrvUSD, EIP-1167 proxy
    "vaultImpl": "0xc014f34d5ba10b6799d76b0f5acdeee577805085",   # LlamaLend Vault.vy
    "controller": "0x89707721927d7aaeeee513797a8d6cbbd0e08f41",  # LlamaLend crvUSD controller of that vault
    "crvUSD": "0xf939e0a03fb07f59a73314e73794be0e57ac1b4e",
    "reUSD": "0x57ab1e0003f623289cd798b1824be09a793e4bec",
}

# Every expression the forge test vendors, with the verified file and line it comes from.
# fetch checks each line against Sourcify; score copies them into the report.
CITES = [
    ("vaultImpl", "Vault.vy", 85, "DEAD_SHARES: constant(uint256) = 1000"),
    ("vaultImpl", "Vault.vy", 197, "borrowed_precision: uint256 = 10**(18 - borrowed_token.decimals())"),
    ("vaultImpl", "Vault.vy", 217, "self.precision = borrowed_precision"),
    ("vaultImpl", "Vault.vy", 267, "return self.borrowed_token.balanceOf(self.controller.address) + self.controller.total_debt()"),
    ("vaultImpl", "Vault.vy", 304, "numerator: uint256 = shares * (total_assets * precision + 1)"),
    ("vaultImpl", "Vault.vy", 305, "denominator: uint256 = (self.totalSupply + DEAD_SHARES) * precision"),
    ("vaultImpl", "Vault.vy", 307, "return numerator / denominator"),
    ("vaultImpl", "Vault.vy", 309, "return (numerator + denominator - 1) / denominator"),
    ("vaultImpl", "Vault.vy", 422, "assets: uint256 = self._convert_to_assets(shares, False, total_assets)"),
    ("oracle", "src/protocol/BasicVaultOracle.sol", 23, "_price = IERC4626(_vault).convertToAssets(1e18);"),
    ("pair", "src/protocol/pair/ResupplyPairConstants.sol", 12, "uint256 public constant LTV_PRECISION = 1e5;"),
    ("pair", "src/protocol/pair/ResupplyPairConstants.sol", 14, "uint256 public constant EXCHANGE_PRECISION = 1e18;"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 573, "_exchangeRate = 1e36 / IOracle(_exchangeRateInfo.oracle).getPrices(address(collateral));"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 272, "if (_maxLTV == 0) return true;"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 275, "uint256 _borrowerAmount = totalBorrow.toAmount(_userBorrowShares[_borrower], true);"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 280, "if (_collateralAmount == 0) return false;"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 282, "uint256 _ltv = ((_borrowerAmount * _exchangeRate * LTV_PRECISION) / EXCHANGE_PRECISION) / _collateralAmount;"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 283, "return _ltv <= _maxLTV;"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 304, "if (!_isSolvent(_borrower, _exchangeRateInfo.exchangeRate)) {"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 640, "uint256 debtForMint = (_borrowAmount * (LIQ_PRECISION + mintFee) / LIQ_PRECISION);"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 649, "_sharesAdded = _totalBorrow.toShares(debtForMint, true);"),
    ("pair", "src/protocol/pair/ResupplyPairCore.sol", 688, "_updateExchangeRate();"),
    ("pair", "src/libraries/VaultAccount.sol", 18, "shares = amount;"),
    ("pair", "src/libraries/VaultAccount.sol", 33, "amount = (shares * total.amount) / total.shares;"),
    ("pair", "src/libraries/VaultAccount.sol", 34, "if (roundUp && total.amount > 0 && (amount * total.shares) / total.amount < shares) {"),
]


def sel(sig: str) -> str:
    from rpc import sel as _sel
    return _sel(sig)


# ---------------------------------------------------------------------------- fetch (network)

def http_get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "blockulator-replay/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def flat_calls(node, depth=0, out=None):
    out = [] if out is None else out
    out.append({"depth": depth, "type": node["type"], "from": node.get("from", "").lower(), "to": node.get("to", "").lower(),
                "input": node.get("input", "0x"), "output": node.get("output", "0x") or "0x", "error": node.get("error")})
    for c in node.get("calls", []) or []:
        flat_calls(c, depth + 1, out)
    return out


def w(hexdata: str, i: int = 0) -> int:
    h = hexdata[2:] if hexdata.startswith("0x") else hexdata
    return int(h[64 * i:64 * (i + 1)], 16)


def args(c) -> str:
    return c["input"][10:]


def one(calls, pred, what):
    hits = [c for c in calls if pred(c)]
    if len(hits) != 1:
        sys.exit(f"trace: expected exactly one {what}, found {len(hits)}")
    return hits[0]


def fetch():
    from rpc import rpc

    tx = rpc(TRACE_RPC, "eth_getTransactionByHash", [TX])
    block = int(tx["blockNumber"], 16)
    index = int(tx["transactionIndex"], 16)
    assert index == 0, "the pre-state is the end of block-1 only for the first transaction in its block"
    blk = rpc(STATE_RPC, "eth_getBlockByNumber", [hex(block), False])
    rc = rpc(TRACE_RPC, "eth_getTransactionReceipt", [TX])
    assert rc["status"] == "0x1"
    trace = rpc(TRACE_RPC, "debug_traceTransaction", [TX, {"tracer": "callTracer"}])
    calls = flat_calls(trace)
    attacker = tx["from"].lower()
    p, o, v, ctl, crv = A["pair"], A["oracle"], A["vault"], A["controller"], A["crvUSD"]

    # --- the call trace
    S = {k: sel(k) for k in ["getPrices(address)", "convertToAssets(uint256)", "transfer(address,uint256)", "mint(uint256)",
                              "balanceOf(address)", "total_debt()", "borrow(uint256,uint256,address)",
                              "addCollateralVault(uint256,address)", "mintFee()", "totalDebtAvailable()", "controller()"]}
    borrow = one(calls, lambda c: c["to"] == p and c["input"].startswith(S["borrow(uint256,uint256,address)"]), "borrow")
    borrower = borrow["from"]
    gp_i = [i for i, c in enumerate(calls) if c["to"] == o and c["input"].startswith(S["getPrices(address)"])]
    assert len(gp_i) == 1, "one getPrices"
    gp = calls[gp_i[0]]
    assert w(args(gp)) == int(v, 16), "getPrices(vault)"
    price = w(gp["output"])
    # its subtree: the vault's convertToAssets(1e18), and inside it the two halves of totalAssets
    sub = []
    for c in calls[gp_i[0] + 1:]:
        if c["depth"] <= gp["depth"]:
            break
        sub.append(c)
    cta = one(sub, lambda c: c["to"] == v and c["input"].startswith(S["convertToAssets(uint256)"]), "convertToAssets under getPrices")
    assert w(args(cta)) == 10 ** 18 and w(cta["output"]) == price
    bal = one(sub, lambda c: c["to"] == crv and c["input"].startswith(S["balanceOf(address)"]), "crvUSD.balanceOf(controller)")
    assert w(args(bal)) == int(ctl, 16)
    debt = one(sub, lambda c: c["to"] == ctl and c["input"].startswith(S["total_debt()"]), "controller.total_debt()")
    donation = one(calls, lambda c: c["to"] == crv and c["from"] == borrower and c["input"].startswith(S["transfer(address,uint256)"])
                   and w(args(c)) == int(ctl, 16), "donation transfer to the controller")
    mint = one(calls, lambda c: c["to"] == v and c["input"].startswith(S["mint(uint256)"]), "vault.mint(shares)")
    addc = one(calls, lambda c: c["to"] == p and c["input"].startswith(S["addCollateralVault(uint256,address)"]), "addCollateralVault")
    assert w(args(addc), 1) == int(borrower, 16)
    fee = one(calls, lambda c: c["to"] == p and c["input"].startswith(S["mintFee()"]), "mintFee()")
    avail = one(calls, lambda c: c["to"] == p and c["input"].startswith(S["totalDebtAvailable()"]), "totalDebtAvailable()")

    # --- the transaction's own logs from the pair
    logs =[l for l in rc["logs"] if l["address"].lower() == p]
    def logw(sig):
        hits = [l for l in logs if l["topics"][0] == _topic(sig)]
        assert len(hits) == 1, sig
        l = hits[0]
        return [int(t, 16) for t in l["topics"][1:]], [w(l["data"], i) for i in range((len(l["data"]) - 2) // 64)], int(l["logIndex"], 16)
    (er_t, er_d, er_i) = logw("UpdateExchangeRate(uint256)")
    (bo_t, bo_d, bo_i) = logw("Borrow(address,address,uint256,uint256,uint256)")
    (ac_t, ac_d, ac_i) = logw("AddCollateral(address,uint256)")
    assert bo_t[0] == int(borrower, 16) and ac_t[0] == int(borrower, 16)
    vlogs = [l for l in rc["logs"] if l["address"].lower() == v and l["topics"][0] == _topic("Transfer(address,address,uint256)")
             and int(l["topics"][1], 16) == 0]
    assert len(vlogs) == 1, "one cvcrvUSD mint in the tx"
    minted = w(vlogs[0]["data"])

    # --- state before (end of block-1 = just before this tx, index 0) and after (end of block)
    def call(to, sig, *a, blockno):
        data = sel(sig) + "".join(hex(x)[2:].rjust(64, "0") if isinstance(x, int) else x.lower().replace("0x", "").rjust(64, "0") for x in a)
        r = rpc(STATE_RPC, "eth_call", [{"to": to, "data": data}, hex(blockno)])
        return [w(r, i) for i in range((len(r) - 2) // 64)]

    def state(b):
        return {
            "block": b,
            "pair.maxLTV": call(p, "maxLTV()", blockno=b)[0],
            "pair.mintFee": call(p, "mintFee()", blockno=b)[0],
            "pair.borrowLimit": call(p, "borrowLimit()", blockno=b)[0],
            "pair.minimumBorrowAmount": call(p, "minimumBorrowAmount()", blockno=b)[0],
            "pair.totalBorrow.amount": call(p, "totalBorrow()", blockno=b)[0],
            "pair.totalBorrow.shares": call(p, "totalBorrow()", blockno=b)[1],
            "pair.exchangeRateInfo.exchangeRate": call(p, "exchangeRateInfo()", blockno=b)[2],
            "pair.exchangeRateInfo.oracle": hex(call(p, "exchangeRateInfo()", blockno=b)[0]),
            "pair.collateral": hex(call(p, "collateral()", blockno=b)[0]),
            "pair.LTV_PRECISION": call(p, "LTV_PRECISION()", blockno=b)[0],
            "pair.EXCHANGE_PRECISION": call(p, "EXCHANGE_PRECISION()", blockno=b)[0],
            "vault.totalSupply": call(v, "totalSupply()", blockno=b)[0],
            "vault.totalAssets": call(v, "totalAssets()", blockno=b)[0],
            "vault.controller": hex(call(v, "controller()", blockno=b)[0]),
            "crvUSD.decimals": call(crv, "decimals()", blockno=b)[0],
            "oracle.getPrices(vault)": call(o, "getPrices(address)", v, blockno=b)[0],
        }
    pre, post = state(block - 1), state(block)
    post["pair.userCollateralBalance(borrower)"] = call(p, "userCollateralBalance(address)", borrower, blockno=block)[0]
    post["pair.userBorrowShares(borrower)"] = call(p, "userBorrowShares(address)", borrower, blockno=block)[0]
    impl_code = rpc(STATE_RPC, "eth_getCode", [v, hex(block - 1)])
    assert A["vaultImpl"][2:] in impl_code.lower(), "cvcrvUSD is an EIP-1167 proxy to the LlamaLend Vault implementation"
    assert pre["pair.exchangeRateInfo.oracle"] == hex(int(o, 16)) and pre["pair.collateral"] == hex(int(v, 16))
    assert pre["vault.controller"] == hex(int(ctl, 16))

    # --- verified source: Sourcify full/partial match, every cited line checked
    sources = {}
    for key in ("pair", "oracle", "vaultImpl"):
        addr = A[key]
        r = http_get(SOURCIFY.format(addr))
        onchain = rpc(STATE_RPC, "eth_getCode", [addr, hex(block)]).lower()
        rb = (r.get("runtimeBytecode") or {}).get("onchainBytecode", "").lower()
        files = {path: s["content"] for path, s in r["sources"].items()}
        sources[key] = {"address": addr, "name": r["compilation"]["name"], "compiler": r["compilation"]["compilerVersion"],
                        "match": r.get("match"), "runtimeMatch": r.get("runtimeMatch"), "creationMatch": r.get("creationMatch"),
                        "deployBlock": int(r["deployment"]["blockNumber"]), "deployTx": r["deployment"]["transactionHash"],
                        "sourcifyOnchainBytecodeEqualsGetCode": bool(rb) and rb == onchain,
                        "files": {}}
        for (k, f, line, text) in CITES:
            if k != key:
                continue
            body = files[f].split("\n")
            got = body[line - 1].strip()
            if text not in got:
                sys.exit(f"citation drift: {key} {f}:{line} is {got!r}, expected {text!r}")
            sources[key]["files"][f] = {"sha256": hashlib.sha256(files[f].encode()).hexdigest(), "lines": len(body)}

    # --- the integers the solvency check used, each with where it came from
    TA = w(bal["output"]) + w(debt["output"])
    TS = pre["vault.totalSupply"] + minted
    prec = 10 ** (18 - pre["crvUSD.decimals"])
    DEAD = 1000
    # the vault formula must reproduce the traced price exactly with these inputs
    assert 10 ** 18 * (TA * prec + 1) // ((TS + DEAD) * prec) == price, "vault formula does not reproduce the traced price"
    # and mint(1)'s ceil reproduces what the attacker paid, from the pre-mint totals
    assert (w(args(mint)) * ((w(args(donation), 1) + pre["vault.totalAssets"]) * prec + 1) + (pre["vault.totalSupply"] + DEAD) * prec - 1) \
        // ((pre["vault.totalSupply"] + DEAD) * prec) == w(mint["output"])
    borrow_amount = w(args(borrow))
    borrow_shares = w(borrow["output"])
    tb_amount = pre["pair.totalBorrow.amount"] + borrow_amount * (10 ** 5 + w(fee["output"])) // 10 ** 5
    tb_shares = pre["pair.totalBorrow.shares"] + borrow_shares
    assert (tb_amount, tb_shares) == (post["pair.totalBorrow.amount"], post["pair.totalBorrow.shares"])

    pins = {
        "block": block, "txIndex": index, "price": price, "vaultTotalAssets": TA, "vaultTotalSupply": TS, "vaultPrecision": prec,
        "deadShares": DEAD, "exchangeRateOnChain": er_d[0], "collateral": ac_d[0], "borrowAmount": borrow_amount,
        "borrowShares": borrow_shares, "mintFee": w(fee["output"]), "totalBorrowAmountBefore": pre["pair.totalBorrow.amount"],
        "totalBorrowSharesBefore": pre["pair.totalBorrow.shares"], "maxLTV": pre["pair.maxLTV"],
        "ltvPrecision": pre["pair.LTV_PRECISION"], "exchangePrecision": pre["pair.EXCHANGE_PRECISION"],
        "donation": w(args(donation), 1), "mintShares": w(args(mint)), "mintAssets": w(mint["output"]),
        "debtAvailable": w(avail["output"]), "pricePreAttack": pre["oracle.getPrices(vault)"],
        "exchangeRateBefore": pre["pair.exchangeRateInfo.exchangeRate"],
    }
    prov = {
        "block": "eth_getTransactionByHash: blockNumber; transactionIndex 0, so block-1's end state is this tx's pre-state",
        "txIndex": "eth_getTransactionByHash",
        "price": f"trace: STATICCALL oracle.getPrices(vault) return value (BasicVaultOracle.sol:23), inside pair.borrow; equal to the nested vault.convertToAssets(1e18) return",
        "vaultTotalAssets": "trace: crvUSD.balanceOf(controller) + controller.total_debt() inside that convertToAssets (Vault.vy:267)",
        "vaultTotalSupply": "eth_call vault.totalSupply() at block-1 plus the one cvcrvUSD mint Transfer log in this tx",
        "vaultPrecision": "10**(18 - crvUSD.decimals()) (Vault.vy:197, 217); decimals by eth_call; reproduces the traced price, a different precision does not",
        "deadShares": "Vault.vy:85 constant",
        "exchangeRateOnChain": f"log #{er_i}: pair UpdateExchangeRate(uint256) in this tx",
        "collateral": f"log #{ac_i}: pair AddCollateral(borrower, amount); eth_call userCollateralBalance(borrower) at the block agrees",
        "borrowAmount": f"trace: pair.borrow(_borrowAmount, 0, receiver) input; log #{bo_i} Borrow agrees",
        "borrowShares": f"trace: pair.borrow return; log #{bo_i} Borrow agrees; eth_call userBorrowShares(borrower) at the block agrees",
        "mintFee": "trace: pair.mintFee() return during the attack (also eth_call at block-1)",
        "totalBorrowAmountBefore": "eth_call pair.totalBorrow() at block-1",
        "totalBorrowSharesBefore": "eth_call pair.totalBorrow() at block-1",
        "maxLTV": "eth_call pair.maxLTV() at block-1 and at the block",
        "ltvPrecision": "eth_call pair.LTV_PRECISION(); ResupplyPairConstants.sol:12",
        "exchangePrecision": "eth_call pair.EXCHANGE_PRECISION(); ResupplyPairConstants.sol:14",
        "donation": "trace: crvUSD.transfer(controller, amount) from the attack contract",
        "mintShares": "trace: vault.mint(shares) input",
        "mintAssets": "trace: vault.mint return (assets pulled); the Vault.vy:422 ceil reproduces it from the pre-mint totals",
        "debtAvailable": "trace: pair.totalDebtAvailable() return just before borrow",
        "pricePreAttack": "eth_call oracle.getPrices(vault) at block-1",
        "exchangeRateBefore": "eth_call pair.exchangeRateInfo() at block-1",
    }
    checks = {
        "exchangeRateStoredAfter": post["pair.exchangeRateInfo.exchangeRate"],
        "userCollateralBalanceAfter": post["pair.userCollateralBalance(borrower)"],
        "userBorrowSharesAfter": post["pair.userBorrowShares(borrower)"],
        "totalBorrowAfter": [post["pair.totalBorrow.amount"], post["pair.totalBorrow.shares"]],
        "getPricesAtBlock": post["oracle.getPrices(vault)"],
        "borrowLogData": bo_d, "maxLTVAtBlock": post["pair.maxLTV"],
    }
    assert checks["exchangeRateStoredAfter"] == pins["exchangeRateOnChain"]
    assert checks["userCollateralBalanceAfter"] == pins["collateral"]
    assert checks["userBorrowSharesAfter"] == pins["borrowShares"]
    assert bo_d[0] == borrow_amount and bo_d[1] == borrow_shares
    assert post["pair.maxLTV"] == pre["pair.maxLTV"]

    # --- ages: when the pair and the vault were created (Routescan's Etherscan-compatible API, keyless)
    cr = http_get("https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api?module=contract&action=getcontractcreation"
                  f"&contractaddresses={p},{v}")["result"]
    ages = {}
    for row in cr:
        ctx = rpc(STATE_RPC, "eth_getTransactionByHash", [row["txHash"]])
        cb = int(ctx["blockNumber"], 16)
        ts = int(rpc(STATE_RPC, "eth_getBlockByNumber", [hex(cb), False])["timestamp"], 16)
        name = "pair" if row["contractAddress"].lower() == p else "vault"
        ages[name] = {"creationTx": row["txHash"], "block": cb, "timestamp": ts,
                      "secondsBeforeAttack": int(blk["timestamp"], 16) - ts}

    out = {
        "_doc": "Pinned by `uv run scripts/replays/resupply.py fetch` (read-only, public RPC). `pins` are the integers "
                "test/replays/Resupply.t.sol replays; `provenance` says where each came from; `state` is eth_call at "
                "block-1 (pre-state: the tx is index 0) and at the block; `sources` are the Sourcify-verified contracts "
                "with every cited line checked. Integers are decimal strings.",
        "tx": TX, "attacker": attacker, "borrower": borrower,
        "blockTimestamp": int(blk["timestamp"], 16),
        "rpc": {"trace": TRACE_RPC, "state": STATE_RPC},
        "addresses": A,
        "pins": {k: str(x) for k, x in pins.items()},
        "provenance": prov,
        "checks": json.loads(json.dumps(checks, default=str), parse_int=str),
        "state": {"pre": {k: str(x) for k, x in pre.items()}, "post": {k: str(x) for k, x in post.items()}},
        "sources": sources,
        "ages": ages,
        "citations":[{"contract": k, "address": A[k], "file": f, "line": line, "text": t} for (k, f, line, t) in CITES],
    }
    PINS.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {PINS.relative_to(ROOT)}: block {block}, price {price}, exchange rate on chain {er_d[0]}")


def _topic(sig: str) -> str:
    from Crypto.Hash import keccak
    return "0x" + keccak.new(digest_bits=256, data=sig.encode()).hexdigest()


# ---------------------------------------------------------------------------- score (offline)

def run_forge() -> str:
    r = subprocess.run(["forge", "test", "--match-path", TEST, "-vv"], capture_output=True, text=True, cwd=ROOT)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        sys.exit("forge test failed; see " + str(LOG.relative_to(ROOT)) + "\n" + r.stdout[-3000:])
    return r.stdout


def parse(text: str) -> dict:
    res = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("RSP|"):
            _, form, kv = line.split("|", 2)
            res[form] = {k: int(x) for k, x in (q.split("=") for q in kv.strip(";").split(";") if q)}
    return res


def bl127(raw: int) -> Fraction:
    return Fraction(raw, 1 << 128)


def bl19(raw: int) -> Fraction:
    wd = raw & ((1 << 256) - 1)
    if wd == 0:
        return Fraction(0)
    s, e, f = wd >> 255, (wd >> 236) & ((1 << 19) - 1), wd & ((1 << 236) - 1)
    k = e - 262143 - 236
    v = Fraction((1 << 236) + f) * (Fraction(2) ** k)
    return -v if s else v


def digits(x: Fraction, ref: Fraction) -> str:
    from mpmath import mp, mpf, log10
    mp.dps = 200
    if x == ref:
        return "exact"
    if ref == 0:
        return "—"
    err = abs(Fraction(x) - ref) / abs(ref)
    if err >= 1:
        return "0"  # no correct digit
    return f"{float(-log10(mpf(err.numerator) / mpf(err.denominator))):.2f}"


def fmt(x: Fraction | int, sig: int = 28) -> str:
    from mpmath import mp, mpf, nstr
    mp.dps = 200
    x = Fraction(x)
    if x.denominator == 1:
        return f"{x.numerator:,}" if abs(x.numerator) < 10 ** 30 else nstr(mpf(x.numerator), sig)
    return nstr(mpf(x.numerator) / mpf(x.denominator), sig)


def score(text: str):
    J = json.loads(PINS.read_text())
    P = {k: int(x) for k, x in J["pins"].items()}
    R = parse(text)
    price, B0, C, maxLTV = P["price"], P["borrowAmount"], P["collateral"], P["maxLTV"]
    LTVP, EXP = P["ltvPrecision"], P["exchangePrecision"]
    # borrower amount as the pair computes it (VaultAccount.toAmount with roundUp, after the borrow's bookkeeping)
    B = R["deployed"]["borrowerAmount"]
    assert B == B0 * (LTVP + P["mintFee"]) // LTVP

    exact_rate = Fraction(10 ** 36, price)
    exact_ltv = B * exact_rate * LTVP / EXP / C
    exact_max = Fraction(C * maxLTV * EXP) / (exact_rate * LTVP)  # reUSD wei the 1-wei position may owe at maxLTV

    rows = []
    d = R["deployed"]
    assert d["rate"] == 10 ** 36 // price == P["exchangeRateOnChain"]
    assert d["ltv"] == ((B * d["rate"] * LTVP) // EXP) // C
    rows.append(("WAD as deployed: `1e36 / price` (floor)", Fraction(d["rate"]), Fraction(d["ltv"]), d["solvent"], None,
                 "matches chain: UpdateExchangeRate(0), borrow succeeded"))
    u = R["divup"]
    assert u["rate"] == -(-10 ** 36 // price) and u["ltv"] == ((B * u["rate"] * LTVP) // EXP) // C
    rows.append(("divUp on the rate (ceil)", Fraction(u["rate"]), Fraction(u["ltv"]), u["solvent"], Fraction(u["maxBorrow"]), ""))
    e = R["divlast"]
    assert e["ltv"] == -(-(B * 10 ** 36 * LTVP) // (price * EXP * C))
    rows.append(("divide by the price at the end (LTV ceil)", None, Fraction(e["ltv"]), e["solvent"], Fraction(e["maxBorrow"]),
                 f"floor would give {e['ltvFloor']:,}, same verdict"))
    f1 = R["bl127"]
    rows.append(("BL127 (inline lib), same formula", bl127(f1["rate"]), bl127(f1["ltv"]), f1["solvent"], Fraction(f1["maxBorrow"]),
                 f"LTV ceil to the 1e5 grid: {f1['ltvCeil']:,}"))
    f2 = R["bl19"]
    rows.append(("BL19, same formula", bl19(f2["rate"]), bl19(f2["ltv"]), f2["solvent"], Fraction(f2["maxBorrow"]),
                 f"LTV ceil to the 1e5 grid: {f2['ltvCeil']:,}"))
    rows.append(("exact (rational)", exact_rate, exact_ltv, int(exact_ltv <= maxLTV), Fraction(floor(exact_max)), ""))

    # the cliff before the cliff: same vault (1 share outstanding), other donation sizes. Derived, not on chain.
    cliff = []
    for ta_tokens in (400, 500, 600, 667, 999, 1000, 1001, 1500, 2002):
        TA = ta_tokens * 10 ** 18 + (1 if ta_tokens == 2002 else 0)
        pr = 10 ** 18 * (TA * P["vaultPrecision"] + 1) // ((P["vaultTotalSupply"] + P["deadShares"]) * P["vaultPrecision"])
        ex = Fraction(10 ** 36, pr)
        fl = 10 ** 36 // pr
        cliff.append((TA, pr, ex, fl, 1 - Fraction(fl) / ex))

    md = render(J, P, B, rows, exact_rate, exact_ltv, exact_max, cliff)
    OUT_MD.write_text(md)
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    for r in rows:
        print(f"  {r[0]:<45} rate {fmt(r[1]) if r[1] is not None else '—':>30}  ltv {fmt(r[2]):>30}  solvent {r[3]}")


def render(J, P, B, rows, exact_rate, exact_ltv, exact_max, cliff) -> str:
    when = datetime.fromtimestamp(J["blockTimestamp"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    maxLTV = P["maxLTV"]
    pct = lambda x: f"{float(Fraction(x) / P['ltvPrecision'] * 100):,.6g}%"
    L = []
    L.append("# Replay: Resupply, 26 June 2025\n")
    L.append(f"Generated by `uv run scripts/replays/resupply.py` from `scripts/replays/resupply.json` (pinned by "
             f"`resupply.py fetch`) and `{TEST}`. Transaction [`{J['tx'][:10]}…{J['tx'][-4:]}`](https://etherscan.io/tx/{J['tx']}), "
             f"block {P['block']} (index {P['txIndex']}), {when}.\n")
    L.append("## What happened, in integers\n")
    L.append(f"1. The attack contract sent {fmt(Fraction(P['donation'], 10**18))} crvUSD straight to the cvcrvUSD vault's controller "
             f"(a donation: no shares minted). Before the transaction the vault had {J['state']['pre']['vault.totalSupply']} shares "
             f"and {J['state']['pre']['vault.totalAssets']} assets; the oracle read {int(P['pricePreAttack']):,} "
             f"(= 1e18 / DEAD_SHARES) and the pair's stored exchange rate was {int(P['exchangeRateBefore']):,}. The pair had been "
             f"deployed {J['ages']['pair']['secondsBeforeAttack'] / 60:.0f} minutes earlier (block {J['ages']['pair']['block']}); "
             f"the vault {J['ages']['vault']['secondsBeforeAttack'] / 86400:.1f} days earlier (block {J['ages']['vault']['block']}), "
             f"and it held no shares and no assets.")
    L.append(f"2. It minted {P['mintShares']} share wei for {P['mintAssets']:,} crvUSD wei (Vault.vy:422 rounds the cost up), "
             f"so the vault held totalSupply = {P['vaultTotalSupply']}, totalAssets = {P['vaultTotalAssets']:,} wei.")
    L.append(f"3. It posted that {P['collateral']} share wei as collateral and called `borrow({P['borrowAmount']:,}, 0, …)` "
             f"(10,000,000 reUSD, all of the pair's {fmt(Fraction(P['debtAvailable'], 10**18))} available).")
    L.append(f"4. Inside `borrow`, `BasicVaultOracle.getPrices` returned **{P['price']:,}** "
             f"(convertToAssets(1e18) = 1e18 × (totalAssets + 1) / (totalSupply + 1000), floored).")
    L.append(f"5. `_exchangeRate = 1e36 / price` = **{P['exchangeRateOnChain']}** (the transaction emitted `UpdateExchangeRate(0)`). "
             f"The exact quotient is {fmt(exact_rate, 30)}.")
    L.append(f"6. The solvency check: borrower amount {B:,} × rate 0 × 1e5 / 1e18 / {P['collateral']} = LTV **0** ≤ maxLTV "
             f"{maxLTV:,} ({pct(maxLTV)}): solvent. {fmt(Fraction(P['borrowAmount'], 10**18))} reUSD were minted against "
             f"{P['collateral']} wei of cvcrvUSD.\n")
    L.append(f"With the exact rate the same check computes LTV = {fmt(exact_ltv, 30)} in units of 1e-5: "
             f"{float(exact_ltv / maxLTV):,.0f} times the {pct(maxLTV)} cap. The most the 1-wei position "
             f"could owe at the cap is {fmt(Fraction(floor(exact_max), 10**18), 22)} reUSD (one share wei is worth "
             f"{fmt(Fraction(P['price'], 10**36), 22)} crvUSD).\n")
    L.append("## The decisive step on each ruler\n")
    L.append("Same integers, same formula (`ResupplyPairCore.sol:573` then `:282`), different arithmetic. *rate* is collateral "
             "wei per 1e18 reUSD wei; *LTV* is in units of 1e-5 (maxLTV " + f"{maxLTV:,}" + "); *max borrow* is the reUSD the "
             "1-wei position may owe at maxLTV, rounded down (the protocol's favour); *digits* is −log10 of the relative "
             "error against the exact value.\n")
    L.append("| method | rate | rate digits | LTV (1e-5) | verdict | max borrow on 1 wei (reUSD) | note |")
    L.append("|---|---|---|---|---|---|---|")
    for name, rate, ltv, solvent, mb, note in rows:
        verdict = "solvent: borrow passes" if solvent else "**insolvent: reverts**"
        mbs = "unbounded (rate 0)" if mb is None else fmt(mb / 10 ** 18, 22)
        rs = "—" if rate is None else fmt(rate, 30)
        rd = "—" if rate is None else digits(rate, exact_rate)
        L.append(f"| {name} | {rs} | {rd} | {fmt(ltv, 30)} | {verdict} | {mbs} | {note} |")
    L.append("")
    L.append("Reading the table: the deployed rate has 0 correct digits (it is 0 where the truth is one half). `divUp` blocks the "
             "attack but is a one-mark ruler too: it reads one half as 1, doubling the LTV and halving what an honest "
             "borrower could take (0.95 reUSD instead of 1.9). Dividing by the price at the end needs no new library and "
             "gets the verdict and the LTV right to the integer. BL127 and BL19 carry the half and give the exact verdict "
             "and the exact cap.\n")
    wall = (2 ** 127 * (P["vaultTotalSupply"] + P["deadShares"]) * P["vaultPrecision"] + 10 ** 18 - 1) // 10 ** 18 - 1
    L.append(f"Range: BL127 holds integers below 2^127 ≈ 1.7e38, so its port of this line takes the price as an exact integer "
             f"only while totalAssets stays under {fmt(Fraction(wall, 10**18), 9)} crvUSD with one share outstanding "
             f"({float(Fraction(wall, P['vaultTotalAssets'])):.0f} times the attack's); above that the port reverts (`_q` in the "
             f"test) rather than floors. BL19 has no such wall.\n")
    L.append("## The cliff before the cliff (derived, not on chain)\n")
    L.append("The same vault with one share wei outstanding and other totalAssets. The floored rate is an integer, so the debt "
             "the check sees is understated by up to half long before it reaches zero:\n")
    L.append("| totalAssets (crvUSD) | price | exact rate | floored rate | debt understated by |")
    L.append("|---|---|---|---|---|")
    for TA, pr, ex, fl, under in cliff:
        L.append(f"| {fmt(Fraction(TA, 10**18), 22)} | {pr:,} | {fmt(ex, 12)} | {fl} | {float(under * 100):.4g}% |")
    L.append("")
    L.append("## Provenance\n")
    L.append("| integer | value | source |")
    L.append("|---|---|---|")
    for k, x in J["pins"].items():
        L.append(f"| `{k}` | {int(x):,} | {J['provenance'][k]} |")
    L.append("")
    L.append(f"Post-state cross-checks at block {P['block']} (eth_call): stored exchange rate "
             f"{J['checks']['exchangeRateStoredAfter']}, userCollateralBalance {J['checks']['userCollateralBalanceAfter']}, "
             f"userBorrowShares {int(J['checks']['userBorrowSharesAfter']):,}, totalBorrow "
             f"({int(J['checks']['totalBorrowAfter'][0]):,}, {int(J['checks']['totalBorrowAfter'][1]):,}), getPrices "
             f"{int(J['checks']['getPricesAtBlock']):,}. RPC: `{J['rpc']['trace']}` (debug_traceTransaction callTracer, receipt) "
             f"and `{J['rpc']['state']}` (archive eth_call).\n")
    L.append("| contract | address | verified source | compiler | Sourcify | deployed at block |")
    L.append("|---|---|---|---|---|---|")
    for k, s in J["sources"].items():
        L.append(f"| {s['name']} | `{s['address']}` | {', '.join(s['files'])} | {s['compiler']} | {s['runtimeMatch']} "
                 f"(runtime), {s['creationMatch']} (creation); Sourcify's on-chain bytecode = eth_getCode: "
                 f"{'yes' if s['sourcifyOnchainBytecodeEqualsGetCode'] else 'not returned'} | {s['deployBlock']} |")
    L.append(f"\ncvcrvUSD (`{J['addresses']['vault']}`) is an EIP-1167 proxy to the Vault.vy implementation above "
             f"(checked from eth_getCode). Every vendored expression, checked line by line against the verified source "
             f"by `fetch`:\n")
    for c in J["citations"]:
        L.append(f"- `{c['file']}:{c['line']}` ({c['contract']}): `{c['text']}`")
    L.append("")
    L.append("## Caveat\n")
    L.append("This replays one division: divUp, dividing last, BL127 and BL19 each reject this borrow, but none of them "
             "stops a market from going live against an empty vault whose share price a donation sets, so the floor was the "
             "last check that failed, not the only one.\n")
    L.append("## Reproduce\n")
    L.append("```\nuv run scripts/replays/resupply.py fetch   # network, read-only: re-pin scripts/replays/resupply.json\n"
             f"forge test --match-path {TEST} -vv   # offline replay and assertions\n"
             "uv run scripts/replays/resupply.py         # offline: forge + exact scoring -> this file\n```\n")
    return "\n".join(L)


def main():
    a = sys.argv[1:]
    if a and a[0] == "fetch":
        fetch()
        return
    if a and a[0] == "--score":
        score(LOG.read_text())
        return
    score(run_forge())


if __name__ == "__main__":
    main()

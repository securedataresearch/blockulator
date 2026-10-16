#!/usr/bin/env python3
"""Snapshot of real mainnet conditions for the deployed-accrual study.

    uv run scripts/accrual/survey.py [rpc]

Reads, at one pinned block, every Aave v3 Core reserve (rates, indexes, last
update, interest-rate parameters, utilisation) and every Morpho Blue market
with at least $10k borrowed (state, rate at target, last update), and writes
scripts/accrual/survey.json. The Morpho market ids come from Morpho's public
API (only to enumerate them); every number recorded is read on chain at the
pinned block. The scenarios in scripts/accrual/scenarios.json cite it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rpc import DEFAULT_RPC, addr_word, batch_call, decode_string, http_json, rpc, sel, words  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "scripts" / "accrual" / "survey.json"

AAVE_POOL = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
ADAPTIVE_IRM = "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC"
SPY = 365 * 86400
MORPHO_API = "https://blue-api.morpho.org/graphql"


def aave(url: str, block: str) -> list[dict]:
    lst = batch_call(url, [(AAVE_POOL, sel("getReservesList()"))], block)[0]
    w = words(lst)
    n = w[1]
    assets = ["0x" + hex(x)[2:].rjust(40, "0") for x in w[2:2 + n]]
    strat = "0x" + hex(words(batch_call(url, [(AAVE_POOL, sel("RESERVE_INTEREST_RATE_STRATEGY()"))], block)[0])[0])[2:].rjust(40, "0")
    rd = batch_call(url, [(AAVE_POOL, sel("getReserveData(address)") + addr_word(a)) for a in assets], block)
    ir = batch_call(url, [(strat, sel("getInterestRateDataBps(address)") + addr_word(a)) for a in assets], block)
    sy = batch_call(url, [(a, sel("symbol()")) for a in assets], block)
    de = batch_call(url, [(a, sel("decimals()")) for a in assets], block)
    rows = []
    toks = []
    for a, r in zip(assets, rd):
        x = words(r)
        toks.append(("0x" + hex(x[8])[2:].rjust(40, "0"), "0x" + hex(x[10])[2:].rjust(40, "0")))
    sup = batch_call(url, [(t[0], sel("totalSupply()")) for t in toks], block)
    debt = batch_call(url, [(t[1], sel("totalSupply()")) for t in toks], block)
    ssup = batch_call(url, [(t[0], sel("scaledTotalSupply()")) for t in toks], block)
    sdebt = batch_call(url, [(t[1], sel("scaledTotalSupply()")) for t in toks], block)
    nd = batch_call(url, [(AAVE_POOL, sel("getReserveNormalizedVariableDebt(address)") + addr_word(a)) for a in assets], block)
    ni = batch_call(url, [(AAVE_POOL, sel("getReserveNormalizedIncome(address)") + addr_word(a)) for a in assets], block)
    for i, a in enumerate(assets):
        x = words(rd[i])
        cfg = x[0]
        bps = words(ir[i]) if ir[i] else [0, 0, 0, 0]
        s, d = int(sup[i], 16), int(debt[i], 16)
        rows.append({
            "asset": a, "symbol": decode_string(sy[i]), "decimals": int(de[i], 16),
            "liquidityIndex": str(x[1]), "currentLiquidityRate": str(x[2]),
            "variableBorrowIndex": str(x[3]), "currentVariableBorrowRate": str(x[4]),
            "lastUpdateTimestamp": x[6],
            "active": bool(cfg >> 56 & 1), "frozen": bool(cfg >> 57 & 1), "borrowingEnabled": bool(cfg >> 58 & 1),
            "paused": bool(cfg >> 60 & 1), "reserveFactorBps": cfg >> 64 & 0xFFFF,
            "optimalUsageRatioBps": bps[0], "baseVariableBorrowRateBps": bps[1],
            "variableRateSlope1Bps": bps[2], "variableRateSlope2Bps": bps[3],
            "aTokenSupply": str(s), "variableDebt": str(d),
            "aTokenScaledSupply": str(int(ssup[i], 16)), "variableDebtScaled": str(int(sdebt[i], 16)),
            "normalizedVariableDebt": str(int(nd[i], 16)), "normalizedIncome": str(int(ni[i], 16)),
            "utilization": (d / s) if s else 0.0,
        })
    return rows


def morpho_ids() -> list[str]:
    q = ('{ markets(first: 1000, where: {chainId_in: [1], borrowAssetsUsd_gte: 10000}) '
         '{ items { marketId } } }')
    r = http_json(MORPHO_API, {"query": q})
    return sorted({m["marketId"] for m in r["data"]["markets"]["items"]})


def morpho(url: str, block: str, ids: list[str]) -> list[dict]:
    mk = batch_call(url, [(MORPHO, sel("market(bytes32)") + i[2:]) for i in ids], block)
    mp = batch_call(url, [(MORPHO, sel("idToMarketParams(bytes32)") + i[2:]) for i in ids], block)
    rows = []
    loan = []
    for i in range(len(ids)):
        p = words(mp[i])
        loan.append("0x" + hex(p[0])[2:].rjust(40, "0"))
    rat = batch_call(url, [(ADAPTIVE_IRM, sel("rateAtTarget(bytes32)") + i[2:]) for i in ids], block)
    sig = "borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))"
    br = batch_call(url, [(ADAPTIVE_IRM, sel(sig) + mp[i][2:] + mk[i][2:]) for i in range(len(ids))], block)
    sy = batch_call(url, [(a, sel("symbol()")) for a in loan], block)
    de = batch_call(url, [(a, sel("decimals()")) for a in loan], block)
    for i, mid in enumerate(ids):
        m, p = words(mk[i]), words(mp[i])
        irm = "0x" + hex(p[3])[2:].rjust(40, "0")
        rows.append({
            "id": mid, "loanToken": loan[i], "symbol": decode_string(sy[i]), "decimals": int(de[i], 16) if de[i] else None,
            "irm": irm, "lltv": str(p[4]),
            "totalSupplyAssets": str(m[0]), "totalBorrowAssets": str(m[2]), "lastUpdate": m[4], "fee": str(m[5]),
            "utilization": (m[2] / m[0]) if m[0] else 0.0,
            "rateAtTarget": str(int(rat[i], 16)) if irm.lower() == ADAPTIVE_IRM.lower() and rat[i] else None,
            "borrowRateView": str(int(br[i], 16)) if irm.lower() == ADAPTIVE_IRM.lower() and br[i] else None,
        })
    return rows


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RPC
    bn = int(rpc(url, "eth_blockNumber", []), 16)
    block = hex(bn)
    ts = int(rpc(url, "eth_getBlockByNumber", [block, False])["timestamp"], 16)
    out = {"block": bn, "timestamp": ts, "rpc": url,
           "aavePool": AAVE_POOL, "morpho": MORPHO, "adaptiveCurveIrm": ADAPTIVE_IRM,
           "note": "Every number is an eth_call at `block`. Morpho market ids (>= $10k borrowed) were enumerated with "
                   "Morpho's public API; their states are read on chain.",
           "aave": aave(url, block)}
    out["morpho"] = morpho(url, block, morpho_ids())
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    a, m = out["aave"], out["morpho"]
    print(f"block {bn} ts {ts}: {len(a)} Aave reserves, {len(m)} Morpho markets -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

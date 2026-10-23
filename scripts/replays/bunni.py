#!/usr/bin/env python3
"""Bunni v2 exploit replay (Ethereum, 2 Sep 2025): the 44 withdrawals that took
the pool's active USDC balance from 28 wei to 4, replayed from integers pinned
out of the attack transaction, and the same withdrawals with the idle balance
held in mulDivUp (the protocol's fix), FP127, FP19 and exact rationals.

    uv run scripts/replays/bunni.py fetch     # network: trace + receipt + Sourcify -> scripts/replays/bunni.json
    uv run scripts/replays/bunni.py           # offline: replay + forge test -> docs/benchmarks/replay-bunni.md
    uv run scripts/replays/bunni.py --no-forge  # offline, Python replay only (no forge)

fetch is read-only. It uses keyless public endpoints: eth_getTransactionByHash,
eth_getTransactionReceipt and eth_getBlockByNumber from publicnode, a
callTracer debug_traceTransaction (with logs) from drpc's public endpoint
(Tenderly's public gateway as a fallback), and Sourcify v2 for verified
source. It never signs or sends anything. Every integer it writes is read from
a call input, a call output or an event in that trace; every event it uses is
checked against the canonical receipt; every vendored expression is checked
line by line against the Sourcify source of the contract that ran it. It then
replays the 44 withdrawals in Python and refuses to write the JSON unless the
replay reproduces every observation (each Withdraw event, each vault
VaultStatus, each pool-state read the attacker made between withdrawals, and
the hook's own reads after the last one).

The offline mode needs no network: it replays from bunni.json, runs
test/replays/Bunni.t.sol (which asserts the same observations in Solidity
and prints REPLAY| lines), checks the forge numbers equal the Python ones, and
scores FP127 and FP19 against exact rational arithmetic.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "replays"
OUT_JSON = HERE / "bunni.json"
OUT_MD = ROOT / "docs" / "benchmarks" / "replay-bunni.md"
LOG = ROOT / "out" / "replays" / "bunni-forge.log"
TEST = "test/replays/Bunni.t.sol"

TX = "0x1c27c4d625429acfc0f97e466eda725fd09ebdc77550e529ba4cbdbc33beb97b"
# keyless public endpoints only. The receipt is taken from a different provider than the
# trace where possible, so the log cross-check is not one node agreeing with itself.
TX_RPCS = ["https://mainnet.gateway.tenderly.co", "https://ethereum-rpc.publicnode.com", "https://eth.drpc.org"]
TRACE_RPCS = ["https://eth.drpc.org", "https://mainnet.gateway.tenderly.co"]
SOURCIFY = "https://sourcify.dev/server/v2/contract/1/{}?fields=all"
POSTMORTEM = "https://blog.bunni.xyz/posts/exploit-post-mortem/"

HUB = "0x000000000049c7bcbca294e63567b4d21eb765f1"
HUB_LOGIC = "0x000000000dbb048f2e744e4b15b5aeef65e09528"
HOOK = "0x000052423c1db6b7ff8641b85a7eefc7b2791888"
HOOK_LOGIC = "0x000000007a00d1e94c60f9e1cfb1ea752035f52c"
SWAP_MATH = "0x000000000f4c25e8636a637948003a36f589696b"
PM = "0x000000000004444c5dc75cb358380d2e3de08a90"
BUNNI_TOKEN = "0xc92c2ba90213fc3048a527052b0b4febfa716763"
VAULT0 = "0xe0a80d35bb6618cba260120b279d357978c42bce"  # Euler EVK vault over USDC
VAULT1 = "0x7c280dbdef569e96c7919251bd2b0edf0734c5a8"  # Euler EVK vault over USDT
EVK_VAULT_MODULE = "0xb4ad4d9c02c01b01cf586c16f01c58c73c7f0188"
EVAULT_IMPL = "0x8ff1c814719096b61abf00bb46ead0c9a529dd7d"  # the beacon's implementation; delegates to the module
ROLE = {"0x000000000049c7bcbca294e63567b4d21eb765f1": "BunniHub (withdraw entry point)",
        "0x000000000dbb048f2e744e4b15b5aeef65e09528": "BunniHubLogic (external library: withdraw)",
        "0x000052423c1db6b7ff8641b85a7eefc7b2791888": "BunniHook (Uniswap v4 hook)",
        "0x000000007a00d1e94c60f9e1cfb1ea752035f52c": "BunniHookLogic (external library: beforeSwap, queryLDF)",
        "0x000000000f4c25e8636a637948003a36f589696b": "BunniSwapMath (external library: computeSwap)",
        "0xb4ad4d9c02c01b01cf586c16f01c58c73c7f0188": "Euler EVK Vault module (previewRedeem, withdraw)",
        "0x8ff1c814719096b61abf00bb46ead0c9a529dd7d": "Euler EVault implementation (dispatches to the module)",
        "0xe0a80d35bb6618cba260120b279d357978c42bce": "Euler vault over USDC (BeaconProxy)",
        "0x7c280dbdef569e96c7919251bd2b0edf0734c5a8": "Euler vault over USDT (BeaconProxy)",
        "0x000000000b757686c9596cada54fa28f8c429e0d": "the pool's LDF (outputs taken from the trace)"}
LDF = "0x000000000b757686c9596cada54fa28f8c429e0d"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
FLASH_POOL = "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"  # Uniswap v3 WETH/USDT 0.3%
AAVE_POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"

SEL = {"withdraw": "0x5d4a505e", "poolState": "0xe0b01bac", "swap": "0xf3cd914c", "totalSupply": "0x18160ddd",
       "previewRedeem": "0x4cdad506", "vaultWithdraw": "0xb460af94", "take": "0x0b0d9c09", "ldfQuery": "0x685056ff",
       "computeSwap": "0xeded9364", "flash": "0x490e6cbc", "aaveSupply": "0x617ba037"}
T_WITHDRAW = "0xbc70c2ef"  # IBunniHub.Withdraw topic prefix (full topic checked against the receipt)
T_VAULT_STATUS = "0x80b61abbfc5f73cfe5cf93cec97a69ed20643dc6c6f1833b05a1560aa164e24c"
VD = 10 ** 6  # EVK ConversionHelpers.VIRTUAL_DEPOSIT_AMOUNT
Q96 = 1 << 96
MASK255 = (1 << 255) - 1

# Every expression the replay vendors, with the line it must match in the Sourcify
# source of the contract that executed it (verified on fetch).
CITES = [
    ("idle", HUB_LOGIC, "src/lib/BunniHubLogic.sol", 478,
     "uint256 newBalance = balance - balance.mulDiv(shares, currentTotalSupply);"),
    ("supply", HUB_LOGIC, "src/lib/BunniHubLogic.sol", 432, "uint256 currentTotalSupply = state.bunniToken.totalSupply();"),
    ("reserveAmount0", HUB_LOGIC, "src/lib/BunniHubLogic.sol", 463,
     "getReservesInUnderlying(state.reserve0.mulDiv(shares, currentTotalSupply), state.vault0);"),
    ("rawAmount0", HUB_LOGIC, "src/lib/BunniHubLogic.sol", 466,
     "uint256 rawAmount0 = state.rawBalance0.mulDiv(shares, currentTotalSupply);"),
    ("reserveChange0", HUB_LOGIC, "src/lib/BunniHubLogic.sol", 495, "s.reserve0[poolId] = state.reserve0 - reserveChange;"),
    ("vaultWithdraw", HUB_LOGIC, "src/lib/BunniHubLogic.sol", 843,
     "reserveChange = vault.withdraw(amount, user, address(this));"),
    ("previewRedeem", HUB_LOGIC, "src/lib/VaultMath.sol", 7,
     "return address(vault) == address(0) ? reserveAmount : vault.previewRedeem(reserveAmount);"),
    ("mulDiv", HUB_LOGIC, "lib/solady/src/utils/FixedPointMathLib.sol", 604, "z := div(z, d)"),
    ("mulDivUp", HUB_LOGIC, "lib/solady/src/utils/FixedPointMathLib.sol", 619, "z := add(iszero(iszero(mod(z, d))), div(z, d))"),
    ("idleUnpack", HUB_LOGIC, "src/types/IdleBalance.sol", 36, "rawBalance := and(mask, idleBalance)"),
    ("balance0", HOOK_LOGIC, "src/lib/BunniHookLogic.sol", 197,
     "(bunniState.rawBalance0 + reserveBalance0, bunniState.rawBalance1 + reserveBalance1);"),
    ("roundTick", HOOK_LOGIC, "src/lib/QueryLDF.sol", 64, "(int24 roundedTick, int24 nextRoundedTick) = roundTick(tick, key.tickSpacing);"),
    ("densities", HOOK_LOGIC, "src/lib/QueryLDF.sol", 77,
     "(uint256 density0OfRoundedTickX96, uint256 density1OfRoundedTickX96) = LiquidityAmounts.getAmountsForLiquidity("),
    ("totalDensity0", HOOK_LOGIC, "src/lib/QueryLDF.sol", 80, "totalDensity0X96 = density0RightOfRoundedTickX96 + density0OfRoundedTickX96;"),
    ("subIdle", HOOK_LOGIC, "src/lib/QueryLDF.sol", 88, "balance0 = subReLU(balance0, balance);"),
    ("estimate0", HOOK_LOGIC, "src/lib/QueryLDF.sol", 97,
     "uint256 totalLiquidityEstimate0 = noToken0 ? 0 : balance0.fullMulDiv(Q96, totalDensity0X96);"),
    ("estimate1", HOOK_LOGIC, "src/lib/QueryLDF.sol", 98,
     "uint256 totalLiquidityEstimate1 = noToken1 ? 0 : balance1.fullMulDiv(Q96, totalDensity1X96);"),
    ("useEstimate0", HOOK_LOGIC, "src/lib/QueryLDF.sol", 100,
     "(totalLiquidityEstimate0 < totalLiquidityEstimate1 || totalDensity1X96 == 0) && totalDensity0X96 != 0;"),
    ("liquidity0", HOOK_LOGIC, "src/lib/QueryLDF.sol", 103,
     "noToken0 ? 0 : roundUpFullMulDivResult(balance0, Q96, totalDensity0X96, totalLiquidityEstimate0);"),
    ("liquidity1", HOOK_LOGIC, "src/lib/QueryLDF.sol", 110,
     "noToken1 ? 0 : roundUpFullMulDivResult(balance1, Q96, totalDensity1X96, totalLiquidityEstimate1);"),
    ("active0", HOOK_LOGIC, "src/lib/QueryLDF.sol", 105,
     "noToken0 ? 0 : FixedPointMathLib.min(balance0, totalLiquidityEstimate0.fullMulX96(totalDensity0X96)),"),
    ("roundTickBody", HOOK_LOGIC, "src/lib/Math.sol", 33, "if (currentTick < 0 && currentTick % tickSpacing != 0) compressed--;"),
    ("subReLU", HOOK_LOGIC, "src/lib/Math.sol", 72, "return x > y ? x - y : 0;"),
    ("roundUpResult", HOOK_LOGIC, "src/lib/Math.sol", 87, "if mulmod(x, y, d) {"),
    ("amounts", HOOK_LOGIC, "src/lib/LiquidityAmounts.sol", 26, "if (sqrtRatioX96 <= sqrtRatioAX96) {"),
    ("amount0Up", HOOK_LOGIC, "src/lib/SqrtPriceMath.sol", 206,
     "FixedPointMathLib.fullMulDivUp(numerator1, numerator2, sqrtPriceBX96), sqrtPriceAX96"),
    ("amount1Up", HOOK_LOGIC, "src/lib/SqrtPriceMath.sol", 251,
     "amount1 := add(amount1, and(gt(mulmod(_liquidity, numerator, denominator), 0), roundUp))"),
    ("fullMulX96", HOOK_LOGIC, "src/lib/FullMathX96.sol", 32, "z := shr(96, z)"),
    ("divRoundingUp", HOOK_LOGIC, "lib/v4-core/src/libraries/UnsafeMath.sol", 14, "z := add(div(x, y), gt(mod(x, y), 0))"),
    ("sqrtAtTick", HOOK_LOGIC, "lib/v4-core/src/libraries/TickMath.sol", 57,
     "function getSqrtPriceAtTick(int24 tick) internal pure returns (uint160 sqrtPriceX96) {"),
    ("sqrtAtTickRound", HOOK_LOGIC, "lib/v4-core/src/libraries/TickMath.sol", 111,
     "sqrtPriceX96 := shr(32, add(price, sub(shl(32, 1), 1)))"),
    ("evkTotals", EVK_VAULT_MODULE, "lib/euler-vault-kit/src/EVault/shared/lib/ConversionHelpers.sol", 22,
     "vaultCache.cash.toUint() + vaultCache.totalBorrows.toAssetsUp().toUint() + VIRTUAL_DEPOSIT_AMOUNT;"),
    ("evkVirtual", EVK_VAULT_MODULE, "lib/euler-vault-kit/src/EVault/shared/lib/ConversionHelpers.sol", 13,
     "uint256 internal constant VIRTUAL_DEPOSIT_AMOUNT = 1e6;"),
    ("evkToAssetsDown", EVK_VAULT_MODULE, "lib/euler-vault-kit/src/EVault/shared/types/Shares.sol", 25,
     "return TypesLib.toAssets(amount.toUint() * totalAssets / totalShares);"),
    ("evkToSharesUp", EVK_VAULT_MODULE, "lib/euler-vault-kit/src/EVault/shared/types/Assets.sol", 38,
     "return TypesLib.toShares((amount.toUint() * totalShares + (totalAssets - 1)) / totalAssets);"),
    ("evkConvertToAssets", EVK_VAULT_MODULE, "lib/euler-vault-kit/src/EVault/modules/Vault.sol", 37,
     "return shares.toShares().toAssetsDown(vaultCache).toUint();"),
    ("evkWithdraw", EVK_VAULT_MODULE, "lib/euler-vault-kit/src/EVault/modules/Vault.sol", 159,
     "Shares shares = assets.toSharesUp(vaultCache);"),
    ("evkVaultStatus", EVK_VAULT_MODULE, "lib/euler-vault-kit/src/EVault/shared/Base.sol", 144,
     "a.totalBorrows.toAssetsUp().toUint(),"),
]


# ---------------------------------------------------------------------------- arithmetic (shared by fetch and offline)

def cdiv(x: int, y: int) -> int:
    return -(-x // y)


class Vault:
    """An Euler EVK vault's share/asset conversion inside one block (no interest accrues
    between operations at one timestamp): ConversionHelpers.conversionTotals with the
    1e6 virtual deposit, toAssetsDown for previewRedeem, toSharesUp for withdraw."""

    def __init__(self, cash: int, borrows: int, shares: int):
        self.cash, self.borrows, self.shares = cash, borrows, shares

    def totals(self) -> tuple[int, int]:
        return self.cash + self.borrows + VD, self.shares + VD

    def preview_redeem(self, s: int) -> int:
        a, t = self.totals()
        return s * a // t

    def withdraw(self, assets: int) -> int:
        if assets == 0:
            return 0
        a, t = self.totals()
        burned = (assets * t + a - 1) // a
        self.cash -= assets
        self.shares -= burned
        return burned


_TICK_M = [0xfff97272373d413259a46990580e213a, 0xfff2e50f5f656932ef12357cf3c7fdcc, 0xffe5caca7e10e4e61c3624eaa0941cd0,
           0xffcb9843d60f6159c9db58835c926644, 0xff973b41fa98c081472e6896dfb254c0, 0xff2ea16466c96a3843ec78b326b52861,
           0xfe5dee046a99a2a811c461f1969c3053, 0xfcbe86c7900a88aedcffc83b479aa3a4, 0xf987a7253ac413176f2b074cf7815e54,
           0xf3392b0822b70005940c7a398e4b70f3, 0xe7159475a2c29b7443b29c7fa6e889d9, 0xd097f3bdfd2022b8845ad8f792aa5825,
           0xa9f746462d870fdf8a65dc1f90e061e5, 0x70d869a156d2a1b890bb3df62baf32f7, 0x31be135f97d08fd981231505542fcfa6,
           0x9aa508b5b7a84e1c677de54f3e99bc9, 0x5d6af8dedb81196699c329225ee604, 0x2216e584f5fa1ea926041bedfe98,
           0x48a170391f7dc42444e8fa2]


def sqrt_at_tick(tick: int) -> int:
    """v4-core TickMath.getSqrtPriceAtTick."""
    a = abs(tick)
    p = 0xfffcb933bd6fad37aa2d162d1a594001 if a & 1 else 1 << 128
    for i, m in enumerate(_TICK_M):
        if a & (2 << i):
            p = (p * m) >> 128
    if tick > 0:
        p = ((1 << 256) - 1) // p
    return (p + (1 << 32) - 1) >> 32


def amounts_for_liquidity(p: int, a: int, b: int, liq: int) -> tuple[int, int]:
    """Bunni LiquidityAmounts.getAmountsForLiquidity(..., roundingUp = true)."""
    a, b = min(a, b), max(a, b)

    def a0(x, y):
        return cdiv(cdiv((liq << 96) * (y - x), y), x)

    def a1(x, y):
        return cdiv(liq * (y - x), Q96)

    if p <= a:
        return a0(a, b), 0
    if p < b:
        return a0(p, b), a1(a, p)
    return 0, a1(a, b)


def round_tick(tick: int, spacing: int) -> tuple[int, int]:
    c = int(tick / spacing)
    if tick < 0 and tick % spacing:
        c -= 1
    return c * spacing, c * spacing + spacing


def query_ldf(tick: int, spacing: int, sqrtp: int, ldf_out: list[int], bal0: int, bal1: int, idle: int, idle0: bool) -> dict:
    """Bunni queryLDF (QueryLDF.sol:64-117) from the LDF's own query outputs; no surge."""
    liq, d0r, d1l = ldf_out[:3]
    rt, nrt = round_tick(tick, spacing)
    x0, x1 = amounts_for_liquidity(sqrtp, sqrt_at_tick(rt), sqrt_at_tick(nrt), liq)
    td0, td1 = d0r + x0, d1l + x1
    if idle0:
        bal0 = max(bal0 - idle, 0)
    else:
        bal1 = max(bal1 - idle, 0)
    out = dict(balance0=bal0, balance1=bal1, totalDensity0X96=td0, totalDensity1X96=td1, L=0, est0=0, est1=0,
               active0=0, active1=0, bound=None)
    if bal0 == 0 and bal1 == 0:
        return out
    n0, n1 = bal0 == 0 or td0 == 0, bal1 == 0 or td1 == 0
    e0 = 0 if n0 else bal0 * Q96 // td0
    e1 = 0 if n1 else bal1 * Q96 // td1
    use0 = (e0 < e1 or td1 == 0) and td0 != 0
    e, bal, td, n = (e0, bal0, td0, n0) if use0 else (e1, bal1, td1, n1)
    out.update(est0=e0, est1=e1, bound="token0" if use0 else "token1",
               L=0 if n else e + (1 if (bal * Q96) % td else 0),
               active0=0 if n0 else min(bal0, e * td0 >> 96), active1=0 if n1 else min(bal1, e * td1 >> 96))
    return out


def replay(d: dict) -> dict:
    """The 44 withdrawals from the pinned start state. Token flows (raw and reserve
    withdrawals, the vault's share burn) are the deployed integer code in every form;
    only the idle-balance update differs. Returns per-step sequences and checks every
    on-chain observation in d."""
    st, steps = d["start"], d["steps"]
    raw0, raw1, res0, res1 = (int(st[k]) for k in ("raw0", "raw1", "reserve0", "reserve1"))
    idle0 = int(st["idle"])
    v0 = Vault(*(int(st["vault0"][k]) for k in ("cash", "totalBorrows", "totalShares")))
    v1 = Vault(*(int(st["vault1"][k]) for k in ("cash", "totalBorrows", "totalShares")))
    n = len(steps["shares"])
    T0 = int(st["totalSupply"])
    idle = {"deployed": idle0, "mulDivUp": idle0, "fp127": idle0 << 128}
    exact = Fraction(idle0)
    snaps = {int(k): i for i, k in enumerate(d["snapshots"]["after"])}
    seq = {f: [] for f in ("deployed", "mulDivUp", "fp127", "exact")}
    bal0s, bal1s = [], []
    T = T0

    def record():
        b0, b1 = raw0 + v0.preview_redeem(res0), raw1 + v1.preview_redeem(res1)
        bal0s.append(b0), bal1s.append(b1)
        seq["deployed"].append(b0 - idle["deployed"])
        seq["mulDivUp"].append(b0 - idle["mulDivUp"])
        seq["fp127"].append(Fraction((b0 << 128) - idle["fp127"], 1 << 128))
        seq["exact"].append(b0 - exact)

    record()
    for k in range(n):
        s = int(steps["shares"][k])
        assert int(steps["totalSupply"][k]) == T, f"step {k}: totalSupply {steps['totalSupply'][k]} != replayed {T}"
        ra0, ra1 = v0.preview_redeem(res0 * s // T), v1.preview_redeem(res1 * s // T)
        rw0, rw1 = raw0 * s // T, raw1 * s // T
        assert (ra0 + rw0, ra1 + rw1) == (int(steps["amount0"][k]), int(steps["amount1"][k])), f"step {k}: Withdraw amounts"
        assert (rw0, rw1) == (int(steps["rawOut0"][k]), int(steps["rawOut1"][k])), f"step {k}: PoolManager take"
        assert (ra0, ra1) == (int(steps["vault0Assets"][k]), int(steps["vault1Assets"][k])), f"step {k}: vault withdraw assets"
        c0, c1 = v0.withdraw(ra0), v1.withdraw(ra1)
        assert (c0, c1) == (int(steps["vault0Burned"][k]), int(steps["vault1Burned"][k])), f"step {k}: shares burned"
        assert (v0.shares, v0.cash, v1.shares, v1.cash) == tuple(int(steps[x][k]) for x in (
            "vault0SharesAfter", "vault0CashAfter", "vault1SharesAfter", "vault1CashAfter")), f"step {k}: VaultStatus"
        res0, res1, raw0, raw1 = res0 - c0, res1 - c1, raw0 - rw0, raw1 - rw1
        i = idle["deployed"]
        idle["deployed"] = i - i * s // T                    # BunniHubLogic.sol:478
        i = idle["mulDivUp"]
        idle["mulDivUp"] = i - cdiv(i * s, T)                # the fix
        i = idle["fp127"]
        idle["fp127"] = i - (i * s) // T                     # FP127: sub(i, div(mul(i, s), T)), floor/trunc at 2^-128
        exact = exact - exact * s / T
        T -= s
        if k + 1 in snaps:
            j = snaps[k + 1]
            got = [raw0, raw1, res0, res1, idle["deployed"]]
            want = [int(d["snapshots"][x][j]) for x in ("raw0", "raw1", "reserve0", "reserve1", "idle")]
            assert got == want, f"after withdrawal {k + 1}: state {got} != on-chain {want}"
        record()
    assert exact == Fraction(idle0 * T, T0), "exact idle must telescope to idle0 * T_n / T_0"
    hk = d["hookAfter"]
    assert v0.preview_redeem(res0) == int(hk["previewRedeem0"]) and v1.preview_redeem(res1) == int(hk["previewRedeem1"])
    return dict(seq=seq, bal0=bal0s, bal1=bal1s, idle=idle, exactIdle=exact, T=T,
                final=dict(raw0=raw0, raw1=raw1, reserve0=res0, reserve1=res1))


def liquidity_table(d: dict, r: dict) -> dict:
    """queryLDF at the start state and at the end for each form. The integer pipeline
    takes integer balances, so a fractional active balance is floored (idle ceilinged)."""
    lq = d["ldf"]["tick5000"]
    args = (int(lq["tick"]), int(d["pool"]["tickSpacing"]), int(lq["sqrtPriceX96"]), [int(x) for x in lq["out"]])
    b0s, b1s = r["bal0"], r["bal1"]
    idle0 = int(d["start"]["idle"])
    out = {"start": query_ldf(*args, b0s[0], b1s[0], idle0, True)}
    for f in ("deployed", "mulDivUp", "fp127", "exact"):
        a = r["seq"][f][-1]
        a_int = a if isinstance(a, int) else (a.numerator // a.denominator)
        out[f] = query_ldf(*args, b0s[-1], b1s[-1], b0s[-1] - a_int, True)
    return out


def validate_ldf(d: dict) -> None:
    """The port reproduces the hook's own totalLiquidity / active balances where the chain shows them."""
    sp = int(d["pool"]["tickSpacing"])
    for key in ("swap3", "afterWithdrawals"):
        o = d["observed"][key]
        q = d["ldf"][o["ldf"]]
        got = query_ldf(int(q["tick"]), sp, int(q["sqrtPriceX96"]), [int(x) for x in q["out"]],
                        int(o["balance0"]), int(o["balance1"]), int(o["idle"]), True)
        want = (int(o["totalLiquidity"]), int(o["active0"]), int(o["active1"]))
        assert (got["L"], got["active0"], got["active1"]) == want, f"queryLDF port vs chain at {key}: {got} != {want}"


# ---------------------------------------------------------------------------- fetch (network)

def _w(h: str) -> list[int]:
    h = h[2:] if h.startswith("0x") else h
    return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]


def _signed(x: int) -> int:
    return x - (1 << 256) if x >> 255 else x


def fetch() -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "accrual"))
    from rpc import http_json, rpc  # noqa: E402  (repo helper; no web3 dependency)

    served = {}

    def rpc_any(urls, method, params):
        for u in urls:  # pruned nodes answer null for old receipts; keep the first real answer
            try:
                res = rpc(u, method, params)
            except Exception as e:
                print(f"{u} {method}: {e}", file=sys.stderr)
                continue
            if res is not None:
                served[method] = u
                return res
        sys.exit(f"no public endpoint served {method}")

    tx = rpc_any(TX_RPCS, "eth_getTransactionByHash", [TX])
    rc = rpc_any(TX_RPCS, "eth_getTransactionReceipt", [TX])
    blk = rpc_any(TX_RPCS, "eth_getBlockByNumber", [tx["blockNumber"], False])
    assert rc["status"] == "0x1" and rc["blockNumber"] == tx["blockNumber"]
    trace, trace_rpc = None, None
    for u in TRACE_RPCS:
        try:
            trace = rpc(u, "debug_traceTransaction", [TX, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
            trace_rpc = u
            break
        except Exception as e:  # rate limits on public gateways
            print(f"{u}: {e}", file=sys.stderr)
    if trace is None:
        sys.exit("no public endpoint served debug_traceTransaction")
    trace_sha = hashlib.sha256(json.dumps(trace, sort_keys=True).encode()).hexdigest()

    # flatten in execution order; logs ordered as the EVM emitted them (callTracer puts a frame's
    # logs with an index into its calls; we keep (path, position) so ordering against calls is exact)
    nodes, logs = [], []

    def walk(n, path):
        nodes.append((path, n))
        calls = n.get("calls") or []
        for lg in n.get("logs") or []:
            pos = lg.get("position", len(calls))
            logs.append((path, int(pos, 16) if isinstance(pos, str) else int(pos), lg))
        for i, c in enumerate(calls):
            walk(c, f"{path}.{i}")
    walk(trace, "0")
    order = {p: i for i, (p, _) in enumerate(nodes)}
    kids: dict[str, list[str]] = {}
    last: dict[str, int] = {}  # the last node, in execution order, of each frame's subtree
    for p, _ in nodes:
        if "." in p:
            kids.setdefault(p.rsplit(".", 1)[0], []).append(p)
        q = p
        while True:
            last[q] = max(last.get(q, -1), order[p])
            if "." not in q:
                break
            q = q.rsplit(".", 1)[0]

    def log_key(item):
        # a log at `position` k came after the frame's first k child calls: just before child k,
        # or after the whole subtree (deeper frames' trailing logs first)
        path, pos, _ = item
        ch = kids.get(path, [])
        return (order[ch[pos]], 0, 0) if pos < len(ch) else (last[path], 1, -path.count("."))
    logs.sort(key=log_key)

    # receipt cross-check: the trace's logs, in order, equal the canonical receipt's
    rlogs = [(l["address"].lower(), [t.lower() for t in l["topics"]], l["data"].lower()) for l in rc["logs"]]
    tlogs = [(lg["address"].lower(), [t.lower() for t in lg["topics"]], lg["data"].lower()) for _, _, lg in logs]
    assert rlogs == tlogs, "trace logs differ from the receipt"

    def to(n):
        return n.get("to", "").lower()

    def sel(n):
        return n.get("input", "")[:10]

    def frm(n):
        return n.get("from", "").lower()

    withdraws = [(p, n) for p, n in nodes if to(n) == HUB and sel(n) == SEL["withdraw"]]
    assert len(withdraws) == 44, len(withdraws)
    first_w = order[withdraws[0][0]]

    def pool_state(n):
        o = _w(n["output"])[1:1 + 24]
        return dict(raw0=o[19], raw1=o[20], reserve0=o[21], reserve1=o[22], idleWord=o[23],
                    vault0=hex(o[6]), vault1=hex(o[7]), bunniToken=hex(o[1]), ldf=hex(o[0]))

    states = [(p, n) for p, n in nodes if to(n) == HUB and sel(n) == SEL["poolState"]]
    pre = [(p, n) for p, n in states if order[p] < first_w][-1]
    s0 = pool_state(pre[1])
    assert s0["idleWord"] >> 255 == 1, "idle balance is in token0 (USDC)"
    assert int(s0["vault0"], 16) == int(VAULT0, 16) and int(s0["vault1"], 16) == int(VAULT1, 16)

    def vault_status(addr, upto):
        best = None
        for path, _, lg in logs:
            if lg["address"].lower() == addr and lg["topics"][0].lower() == T_VAULT_STATUS and order[path] < upto:
                best = (path, _w(lg["data"]))
        return best

    def vs(addr, upto):
        path, w = vault_status(addr, upto)
        return dict(totalShares=str(w[0]), totalBorrows=str(w[1]), cash=str(w[3]), interestAccumulator=str(w[4]),
                    timestamp=str(w[6]), trace=path)

    key_words = _w(withdraws[0][1]["input"][10:])[:5]
    pool = dict(currency0=USDC, currency1=USDT, fee=key_words[2], tickSpacing=_signed(key_words[3]), hooks=HOOK,
                bunniToken=BUNNI_TOKEN, vault0=VAULT0, vault1=VAULT1, ldf=LDF,
                poolId=hex(_w(pre[1]["input"][10:])[0]), idleIsToken0=True)
    assert hex(key_words[0]) == USDC and hex(key_words[1]) == USDT and int(hex(key_words[4]), 16) == int(HOOK, 16)

    steps = {k: [] for k in ("shares", "totalSupply", "amount0", "amount1", "rawOut0", "rawOut1", "vault0Assets",
                             "vault0Burned", "vault1Assets", "vault1Burned", "vault0SharesAfter", "vault0CashAfter",
                             "vault1SharesAfter", "vault1CashAfter", "trace")}
    for p, n in withdraws:
        sub = [(q, m) for q, m in nodes if q.startswith(p + ".")]
        a = _w(n["input"][10:])
        assert a[10] == 0, "not a queued withdrawal"
        sup = [m for q, m in sub if to(m) == BUNNI_TOKEN and sel(m) == SEL["totalSupply"] and m["type"] == "STATICCALL"]
        steps["shares"].append(str(a[6]))
        steps["totalSupply"].append(str(_w(sup[0]["output"])[0]))
        ev = [lg for q, _, lg in logs if (q == p or q.startswith(p + ".")) and lg["address"].lower() == HUB
              and lg["topics"][0].startswith(T_WITHDRAW)]
        assert len(ev) == 1
        amt = _w(ev[0]["data"])
        assert amt[2] == a[6] and _w(n["output"])[:2] == amt[:2]
        steps["amount0"].append(str(amt[0]))
        steps["amount1"].append(str(amt[1]))
        takes = [_w(m["input"][10:]) for q, m in sub if to(m) == PM and sel(m) == SEL["take"]]
        t0 = [t[2] for t in takes if t[0] == int(USDC, 16)]
        t1 = [t[2] for t in takes if t[0] == int(USDT, 16)]
        steps["rawOut0"].append(str(t0[0] if t0 else 0))
        steps["rawOut1"].append(str(t1[0] if t1 else 0))
        for i, va in ((0, VAULT0), (1, VAULT1)):
            # the hub's own call into the vault (from the hub, not the EVC's re-entry)
            wd = [m for q, m in sub if to(m) == va and sel(m) == SEL["vaultWithdraw"] and frm(m) == HUB]
            assert len(wd) <= 1
            steps[f"vault{i}Assets"].append(str(_w(wd[0]["input"][10:])[0] if wd else 0))
            steps[f"vault{i}Burned"].append(str(_w(wd[0]["output"])[0] if wd else 0))
            st = vault_status(va, max(order[q] for q, _ in sub) + 1)
            steps[f"vault{i}SharesAfter"].append(str(st[1][0]))
            steps[f"vault{i}CashAfter"].append(str(st[1][3]))
        steps["trace"].append(p)

    # the attacker contract's own poolState reads between withdrawals: state after k withdrawals
    # (none of them sits inside a withdraw call; the window ends at the first swap after the last one)
    last_w = order[withdraws[-1][0]]
    wpos = [order[p] for p, _ in withdraws]
    end = min(order[p] for p, n in nodes if to(n) == PM and sel(n) == SEL["swap"] and order[p] > last_w)
    snaps = {k: [] for k in ("after", "raw0", "raw1", "reserve0", "reserve1", "idle", "trace")}
    seen = set()
    for p, n in states:
        if frm(n) == HOOK or not first_w < order[p] < end:
            continue
        assert not any(p.startswith(w + ".") for w, _ in withdraws)
        k = sum(1 for x in wpos if x < order[p])
        if k in seen:
            continue
        seen.add(k)
        s = pool_state(n)
        for x in ("raw0", "raw1", "reserve0", "reserve1"):
            snaps[x].append(str(s[x]))
        snaps["idle"].append(str(s["idleWord"] & MASK255))
        snaps["after"].append(k)
        snaps["trace"].append(p)

    # swaps: swap3 is the 1-USDT exact-in swap that left 28; the next swap is the first after the withdrawals
    swaps = [(p, n) for p, n in nodes if to(n) == PM and sel(n) == SEL["swap"] and frm(n) != HOOK]
    pre_sw = [(p, n) for p, n in swaps if order[p] < first_w]
    post_sw = [(p, n) for p, n in swaps if order[p] > last_w]

    def swap_info(p, n):
        a = _w(n["input"][10:])
        sub = [(q, m) for q, m in nodes if q.startswith(p + ".")]
        cs = [(q, m) for q, m in sub if sel(m) == SEL["computeSwap"] and to(m) == SWAP_MATH][0]
        ci = [_signed(x) for x in _w(cs[1]["input"][10:])]
        qs = [(q, m) for q, m in sub if to(m) == LDF and sel(m) == SEL["ldfQuery"] and order[q] < order[cs[0]]][-1]
        qi, qo = [_signed(x) for x in _w(qs[1]["input"][10:])], _w(qs[1]["output"])
        pr = [(q, m) for q, m in sub if sel(m) == SEL["previewRedeem"] and frm(m) == HOOK and order[q] < order[qs[0]]]
        ps = [m for q, m in sub if to(m) == HUB and sel(m) == SEL["poolState"] and frm(m) == HOOK][0]
        s = pool_state(ps)
        u0 = [_w(m["output"])[0] for q, m in pr if to(m) == VAULT0][0]
        u1 = [_w(m["output"])[0] for q, m in pr if to(m) == VAULT1][0]
        return dict(trace=p, zeroForOne=a[5], amountSpecified=_signed(a[6]),
                    state=s, previewRedeem0=u0, previewRedeem1=u1,
                    ldf=dict(trace=qs[0], roundedTick=qi[5], twapTick=qi[6], tick=qi[7], ldfParams=hex(qi[8] % (1 << 256)),
                             ldfState=hex(qi[9] % (1 << 256)), out=[str(x) for x in qo[:3]], shouldSurge=qo[4]),
                    computeSwap=dict(trace=cs[0], totalLiquidity=ci[5], liquidityDensityOfRoundedTickX96=ci[6],
                                     active0=ci[7], active1=ci[8], sqrtPriceX96=ci[9], tick=ci[10]))

    s3 = swap_info(*pre_sw[-1])
    sa = swap_info(*post_sw[0])
    assert s3["amountSpecified"] == -1000000 and s3["computeSwap"]["tick"] == 3
    assert sa["computeSwap"]["tick"] == 5000 and sa["ldf"]["shouldSurge"] == 0 and s3["ldf"]["shouldSurge"] == 0
    # the 28-wei state: tick 5000 at the price swap3 left; the LDF query there has the same inputs
    # (rounded tick, TWAP tick, spot tick, params, state) as the post-withdrawal swap, so the same outputs
    s3cs = [m for q, m in nodes if q.startswith(pre_sw[-1][0] + ".") and to(m) == LDF and sel(m) == SEL["ldfQuery"]]
    sa_q = [m for q, m in nodes if q == sa["ldf"]["trace"]][0]
    assert _w(s3cs[-1]["input"][10:]) == _w(sa_q["input"][10:]), "LDF inputs at the 28-wei state differ"
    assert _w(s3cs[-1]["output"]) == _w(sa_q["output"])
    assert sa["computeSwap"]["sqrtPriceX96"] == sqrt_at_tick(5000)

    def obs(s, ldfkey):
        st = s["state"]
        return dict(ldf=ldfkey, trace=s["computeSwap"]["trace"],
                    balance0=str(st["raw0"] + s["previewRedeem0"]), balance1=str(st["raw1"] + s["previewRedeem1"]),
                    idle=str(st["idleWord"] & MASK255), totalLiquidity=str(s["computeSwap"]["totalLiquidity"]),
                    active0=str(s["computeSwap"]["active0"]), active1=str(s["computeSwap"]["active1"]))

    # flash loan and where the proceeds went (context for the write-up)
    flash = [n for p, n in nodes if to(n) == FLASH_POOL and sel(n) == SEL["flash"]][0]
    fl = _w(flash["input"][10:])
    aave = [_w(n["input"][10:]) for p, n in nodes if to(n) == AAVE_POOL and sel(n) == SEL["aaveSupply"]]
    swaps_ctx = [dict(trace=p, zeroForOne=_w(n["input"][10:])[5], amountSpecified=_signed(_w(n["input"][10:])[6]))
                 for p, n in swaps]

    # Sourcify: every contract whose code the replay transliterates, and every cited line
    contracts, files = {}, {}
    for addr in (HUB, HUB_LOGIC, HOOK, HOOK_LOGIC, SWAP_MATH, EVK_VAULT_MODULE, EVAULT_IMPL, VAULT0, VAULT1, LDF):
        sd = http_json(SOURCIFY.format(addr))
        comp = sd.get("compilation") or {}
        contracts[addr] = dict(name=comp.get("name"), fullyQualifiedName=comp.get("fullyQualifiedName"),
                               compiler=comp.get("compilerVersion"), match=sd.get("match"),
                               runtimeMatch=sd.get("runtimeMatch"), creationMatch=sd.get("creationMatch"),
                               deployment=sd.get("deployment"))
        assert sd.get("runtimeMatch") in ("exact_match", "match"), (addr, sd.get("runtimeMatch"))
        files[addr] = sd.get("sources") or {}
    cites, bad = [], []
    for cid, addr, path, line, text in CITES:
        src = files[addr][path]["content"]
        got = src.splitlines()[line - 1].strip()
        if text not in got:
            at = [i + 1 for i, s in enumerate(src.splitlines()) if text in s]
            bad.append(f"{cid}: {path}:{line} is {got!r}; the expected text is at line(s) {at}")
            continue
        cites.append(dict(id=cid, contract=contracts[addr]["name"], address=addr, file=path, line=line, text=got,
                          fileSha256=hashlib.sha256(src.encode()).hexdigest()))
    if bad:
        sys.exit("cited lines do not match the verified source:\n  " + "\n  ".join(bad))

    d = dict(
        _doc="generated by scripts/replays/bunni.py fetch from the attack transaction's callTracer trace (with logs), "
             "checked against the receipt; parallel string arrays for the forge test",
        generated=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        tx=dict(hash=TX, chainId=1, block=int(tx["blockNumber"], 16), index=int(tx["transactionIndex"], 16),
                timestamp=int(blk["timestamp"], 16), sender=tx["from"], to=tx["to"], gasUsed=int(rc["gasUsed"], 16),
                postmortem=POSTMORTEM),
        endpoints=dict(tx=served["eth_getTransactionByHash"], receipt=served["eth_getTransactionReceipt"],
                       block=served["eth_getBlockByNumber"], trace=trace_rpc, sourcify=SOURCIFY.format("<address>"),
                       traceSha256=trace_sha,
                       note="read-only: eth_getTransactionByHash, eth_getTransactionReceipt, eth_getBlockByNumber, "
                            "debug_traceTransaction(callTracer, withLog); Sourcify v2 GET"),
        contracts=contracts, cites=cites, pool=pool,
        context=dict(flashLoan=dict(pool=FLASH_POOL, amount1=str(fl[2]), token=USDT),
                     swaps=swaps_ctx, aaveSupplies=[dict(asset=hex(a[0]), amount=str(a[1])) for a in aave]),
        start=dict(trace=pre[0], raw0=str(s0["raw0"]), raw1=str(s0["raw1"]), reserve0=str(s0["reserve0"]),
                   reserve1=str(s0["reserve1"]), idle=str(s0["idleWord"] & MASK255), idleWord=hex(s0["idleWord"]),
                   totalSupply=steps["totalSupply"][0], vault0=vs(VAULT0, first_w), vault1=vs(VAULT1, first_w)),
        steps=steps, snapshots=snaps,
        hookAfter=dict(trace=sa["trace"], previewRedeem0=str(sa["previewRedeem0"]), previewRedeem1=str(sa["previewRedeem1"]),
                       reserve0=str(sa["state"]["reserve0"]), reserve1=str(sa["state"]["reserve1"])),
        ldf={"tick3": dict(tick=3, sqrtPriceX96=str(s3["computeSwap"]["sqrtPriceX96"]), out=s3["ldf"]["out"], trace=s3["ldf"]["trace"]),
             "tick5000": dict(tick=5000, sqrtPriceX96=str(sa["computeSwap"]["sqrtPriceX96"]), out=sa["ldf"]["out"],
                              trace=sa["ldf"]["trace"], twapTick=sa["ldf"]["twapTick"])},
        observed={"swap3": obs(s3, "tick3"), "afterWithdrawals": obs(sa, "tick5000")},
    )
    # the start state as the hook would see it: swap3 left raw0 lower by its output; the vault untouched since
    assert int(d["start"]["reserve0"]) == s3["state"]["reserve0"]
    r = replay(d)
    validate_ldf(d)
    assert r["seq"]["deployed"][0] == 28 and r["seq"]["deployed"][-1] == 4, (r["seq"]["deployed"][0], r["seq"]["deployed"][-1])
    OUT_JSON.write_text(json.dumps(d, indent=1) + "\n")
    print(f"{len(steps['shares'])} withdrawals, {len(snaps['after'])} attacker snapshots, {len(cites)} cited lines -> "
          f"{OUT_JSON.relative_to(ROOT)} (trace from {trace_rpc})")


# ---------------------------------------------------------------------------- offline: forge + score + write-up

def run_forge() -> str:
    r = subprocess.run(["forge", "test", "--match-path", TEST, "-vv"], capture_output=True, text=True, cwd=ROOT)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        sys.exit("forge test failed; see " + str(LOG.relative_to(ROOT)) + "\n" + r.stdout[-3000:])
    return r.stdout


def parse_forge(text: str) -> dict:
    res: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("REPLAY|"):
            _, form, kv = line.split("|", 2)
            res[form] = {k: int(v) for k, v in (p.split("=") for p in kv.strip(";").split(";") if p)}
    return res


def fp19_value(raw: int) -> Fraction:
    w = raw & ((1 << 256) - 1)
    if w == 0:
        return Fraction(0)
    s, e, f = w >> 255, (w >> 236) & ((1 << 19) - 1), w & ((1 << 236) - 1)
    sh = e - 262143 - 236
    v = Fraction((1 << 236) + f) * (Fraction(2) ** sh)
    return -v if s else v


def fp127_value(raw: int) -> Fraction:
    return Fraction(raw - (1 << 256) if raw >> 255 else raw, 1 << 128)


def fmt(q: Fraction, places: int = 6) -> str:
    """q to `places` decimals, rounded half up on the magnitude."""
    if q.denominator == 1:
        return str(q.numerator)
    neg = q < 0
    r = int(abs(q) * 10 ** places + Fraction(1, 2))
    ip, digits = divmod(r, 10 ** places)
    return ("-" if neg else "") + f"{ip}.{digits:0{places}d}"


def sci(q: Fraction) -> str:
    if q == 0:
        return "0"
    return f"{float(q):+.2f}" if abs(q) >= Fraction(1, 100) else f"{float(q):+.2e}"


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch()
        return
    d = json.loads(OUT_JSON.read_text())
    r = replay(d)
    validate_ldf(d)
    liq = liquidity_table(d, r)
    forge = None
    if "--no-forge" not in sys.argv:
        forge = parse_forge(run_forge())
        f = forge
        # the forge replay must agree with this one, integer for integer
        assert f["deployed"]["active0"] == r["seq"]["deployed"][-1] and f["deployed"]["L"] == liq["deployed"]["L"]
        assert f["mulDivUp"]["active0"] == r["seq"]["mulDivUp"][-1] and f["mulDivUp"]["L"] == liq["mulDivUp"]["L"]
        assert fp127_value(f["fp127"]["active0"]) == r["seq"]["fp127"][-1], "forge FP127 differs from the Python FP127 model"
        assert f["start"]["L"] == liq["start"]["L"] and f["exact"]["L"] == liq["exact"]["L"]
        assert Fraction(f["exact"]["num"], f["exact"]["den"]) == r["seq"]["exact"][-1]
    ex = r["seq"]["exact"]
    rows = []
    for form, label in (("deployed", "deployed (`mulDiv`, floor on the subtrahend)"), ("mulDivUp", "the fix (`mulDivUp`)"),
                        ("fp127", "FP127 idle balance"), ("fp19", "FP19 idle balance"), ("exact", "exact rational")):
        if form == "fp19":
            if not forge:
                continue
            a = fp19_value(forge["fp19"]["active0"])
            lq = forge["fp19"]["L"]
        else:
            a = Fraction(r["seq"][form][-1])
            lq = liq[form]["L"]
        rows.append(dict(form=form, label=label, active=a, err=a - ex[-1], L=lq,
                         dL=Fraction(lq, liq["start"]["L"]) - 1))
    write_md(d, r, liq, rows, forge)
    for x in rows:
        print(f"{x['form']:9s} active0 {fmt(x['active'], 40) if x['form'] in ('fp127', 'fp19') else fmt(x['active'])}"
              f"  err {sci(x['err'])}  L {x['L']}  dL {float(x['dL']):+.6%}")


def write_md(d: dict, r: dict, liq: dict, rows: list, forge: dict | None) -> None:
    st, steps = d["start"], d["steps"]
    seqd = r["seq"]["deployed"]
    n = len(steps["shares"])
    T0, Tn = int(st["totalSupply"]), r["T"]
    burned = T0 - Tn
    cite = {c["id"]: c for c in d["cites"]}

    def c(cid):
        x = cite[cid]
        return f"{x['file'].split('/')[-1]}:{x['line']}"
    L0, Ld = liq["start"]["L"], liq["deployed"]["L"]
    td0 = liq["start"]["totalDensity0X96"]
    thresh = Fraction(liq["start"]["est1"] * td0, Q96)
    ex = r["seq"]["exact"]
    shares_set = sorted(set(steps["shares"]), key=int)
    L = []
    L.append("# Replay: Bunni v2, 2 Sep 2025 (Ethereum)\n")
    L.append(f"Generated by `uv run scripts/replays/bunni.py` from `scripts/replays/bunni.json` (pinned by "
             f"`bunni.py fetch` from tx [`{TX[:10]}…`](https://etherscan.io/tx/{TX}), block {d['tx']['block']}, "
             f"index {d['tx']['index']}, on {d['generated']}). Test: `{TEST}` (offline).\n")
    L.append("## Numbers\n")
    L.append(f"- Idle-adjusted USDC balance (balance0 − idle, what `queryLDF` prices with): **{seqd[0]} → {seqd[-1]} wei** "
             f"over {n} withdrawals ({fmt(Fraction(seqd[-1] - seqd[0], seqd[0]) * 100, 1)}%).")
    L.append(f"- Shares burned: {burned} of {T0} ({fmt(Fraction(burned, T0) * 100, 9)}%); pro rata the balance should "
             f"have moved by {fmt(Fraction(seqd[0] * burned, T0), 12)} wei.")
    L.append(f"- Total liquidity: **{L0} → {Ld}** ({float(Fraction(Ld, L0) - 1):+.2%}). At {seqd[0]} wei the pool was "
             f"bound by the USDT estimate; the USDC estimate takes over below {fmt(thresh, 2)} wei and falls in "
             f"proportion to the balance from there.")
    L.append(f"- The chain shows the end of it directly: the first swap after the withdrawals passed "
             f"`totalLiquidity = {d['observed']['afterWithdrawals']['totalLiquidity']}` and active balances "
             f"({d['observed']['afterWithdrawals']['active0']}, {d['observed']['afterWithdrawals']['active1']}) into "
             f"`BunniSwapMath.computeSwap` (trace `{d['observed']['afterWithdrawals']['trace']}`); the replay reproduces "
             f"all three. (`queryLDF`'s active balance is min(balance, liquidity × density), which floors "
             f"{seqd[-1]} to {d['observed']['afterWithdrawals']['active0']}.)\n")
    L.append("### Same 44 withdrawals, idle balance held differently\n")
    L.append("Token transfers out are unchanged in every row (raw and vault withdrawals floor in the pool's favour, "
             "the vault burns shares rounded up); only the stored idle balance and its update differ.\n")
    L.append("| idle balance | active USDC after 44 (wei) | error vs exact (wei) | total liquidity after | change |")
    L.append("|---|---|---|---|---|")
    for x in rows:
        a = fmt(x["active"], 40 if x["form"] in ("fp127", "fp19") else 6)
        if x["form"] == "exact":
            a = f"{fmt(x['active'], 12)}… (= {x['active'].numerator}/{x['active'].denominator})"
        L.append(f"| {x['label']} | {a} | {sci(x['err'])} | {x['L']} | {float(x['dL']):+.7%} |")
    L.append(f"\nStart: active {seqd[0]} wei, liquidity {L0}. Liquidity takes integer balances, so for FP127, FP19 and "
             f"exact the active balance is floored before `queryLDF` (the idle balance rounded up: the same direction "
             f"as the deployed code, applied once instead of {n} times).\n")
    L.append("Per step (active USDC, wei; deployed / mulDivUp / exact):\n")
    L.append("```")
    L.append("step " + " ".join(f"{k:>3d}" for k in range(n + 1)))
    L.append("dep  " + " ".join(f"{v:>3d}" for v in seqd))
    L.append("up   " + " ".join(f"{v:>3d}" for v in r["seq"]["mulDivUp"]))
    L.append("exact" + " ".join(f"{round(v):>3d}" for v in ex) + "   (rounded to the nearest wei)")
    L.append("```\n")
    L.append("## What happened\n")
    ctx = d["context"]
    L.append(f"1. Flash loan of {int(ctx['flashLoan']['amount1']) / 1e6:,.6f} USDT from the Uniswap v3 WETH/USDT pool "
             f"`{ctx['flashLoan']['pool']}`.")
    sw = ctx["swaps"]
    out3 = int(d["observed"]["swap3"]["balance0"]) - r["bal0"][0]
    L.append(f"2. Three swaps on the Bunni USDC/USDT pool (Uniswap v4, hook `{HOOK}`): {sw[0]['amountSpecified'] * -1 / 1e6:,.6f} "
             f"USDT in; {sw[1]['amountSpecified'] / 1e6:,.6f} USDC out (exact output); {sw[2]['amountSpecified'] * -1 / 1e6:,.6f} "
             f"USDT in for {out3} wei USDC, leaving balance0 − idle at {seqd[0]} wei (raw {st['raw0']} + vault "
             f"{r['bal0'][0] - int(st['raw0'])} − idle {st['idle']}).")
    L.append(f"3. {n} withdrawals from `BunniHub` (1 × {steps['shares'][0]} shares, {n - 1} × {steps['shares'][1]}). Each "
             f"removes ⌊idle·s/T⌋ from the idle balance ({c('idle')}) — the floor sits on the subtrahend, so the stored idle "
             f"balance rounds up — while the pool's USDC leaves as ⌊raw·s/T⌋ plus the vault's ⌊reserve·s/T⌋ shares "
             f"redeemed at the vault's rate ({c('rawAmount0')}, {c('reserveAmount0')}). Active USDC fell {seqd[0]} → {seqd[-1]}.")
    sup = ", ".join("{:,.6f} {}".format(int(a["amount"]) / 1e6, "USDC" if int(a["asset"], 16) == int(USDC, 16) else "USDT")
                    for a in ctx["aaveSupplies"])
    L.append(f"4. A swap pair against the now mispriced pool (traces `{sw[3]['trace']}`, `{sw[4]['trace']}`), repay "
             f"the loan, and supply {sup} to Aave v3. Bunni's [post-mortem]({POSTMORTEM}) puts the loss across Ethereum and Unichain at about $8.4M; "
             f"this replay covers the rounding, not the sandwich.\n")
    L.append("## Provenance\n")
    L.append(f"Trace: `debug_traceTransaction` (callTracer with logs) from `{d['endpoints']['trace']}`, "
             f"sha256 {d['endpoints']['traceSha256'][:16]}… of its canonical JSON; every event used was checked, in "
             f"order, against the receipt from `{d['endpoints']['receipt']}`. Paths like `0.6.3.1.6` index the call tree "
             f"(root `0`, then child positions).\n")
    L.append("| integer | value | where in the trace |")
    L.append("|---|---|---|")
    L.append(f"| raw USDC / USDT held by the hub (start) | {st['raw0']} / {st['raw1']} | `poolState` read at `{st['trace']}` |")
    L.append(f"| vault shares held (start) | {st['reserve0']} / {st['reserve1']} | same read |")
    L.append(f"| idle balance (USDC, start) | {st['idle']} (word `{st['idleWord'][:6]}…`, top bit = token0) | same read |")
    L.append(f"| BunniToken total supply before withdrawal 1 | {st['totalSupply']} | `totalSupply()` inside `{steps['trace'][0]}` |")
    for i, nm in ((0, "USDC"), (1, "USDT")):
        v = st[f"vault{i}"]
        L.append(f"| EVK {nm} vault: totalShares, totalBorrows, cash | {v['totalShares']}, {v['totalBorrows']}, {v['cash']} "
                 f"| last `VaultStatus` before the withdrawals, `{v['trace']}` |")
    L.append(f"| shares per withdrawal | {', '.join(shares_set)} | `withdraw` calldata, `{steps['trace'][0]}` … `{steps['trace'][-1]}` |")
    L.append(f"| LDF outputs at tick 5000 | {', '.join(d['ldf']['tick5000']['out'])} | `query` at `{d['ldf']['tick5000']['trace']}` |")
    L.append(f"| sqrtPriceX96 at tick 5000 | {d['ldf']['tick5000']['sqrtPriceX96']} | `computeSwap` input; equals `getSqrtPriceAtTick(5000)` |")
    L.append(f"| hook's vault reads after withdrawal 44 | {d['hookAfter']['previewRedeem0']} / {d['hookAfter']['previewRedeem1']} | `previewRedeem` at `{d['hookAfter']['trace']}` |")
    L.append("")
    L.append(f"Checked by the replay (Python and `{TEST}` alike): all {n} `Withdraw` events (amount0, amount1), the "
             f"PoolManager `take` amounts, each vault's `withdraw` assets and shares burned, {2 * n} `VaultStatus` events "
             f"(totalShares, cash), {len(d['snapshots']['after'])} `poolState` reads the attack contract made between "
             f"withdrawals (raw balances, vault shares, idle balance), the hook's own `previewRedeem` after the last "
             f"one, and `queryLDF`'s outputs at two states the chain shows (swap 3: {d['observed']['swap3']['totalLiquidity']}; "
             f"after the withdrawals: {d['observed']['afterWithdrawals']['totalLiquidity']}). The liquidity at the 28-wei "
             f"state ({L0}) is computed, not observed: no swap ran there. Its LDF inputs (rounded tick, TWAP tick, spot "
             f"tick, params, state) equal those of the post-withdrawal swap, which `fetch` asserts.\n")
    L.append("Verified source (Sourcify, runtime exact match):\n")
    L.append("| contract | role | address | compiler |")
    L.append("|---|---|---|---|")
    for a, ci in d["contracts"].items():
        L.append(f"| {ci['name']} | {ROLE.get(a, '')} | `{a}` | {ci['compiler']} ({ci['runtimeMatch']}) |")
    L.append("\nVendored expressions (each line checked against that source on fetch):\n")
    for x in d["cites"]:
        L.append(f"- `{x['contract']}` {x['file']}:{x['line']} — `{x['text']}`")
    L.append("")
    L.append("## Notes\n")
    up = r["seq"]["mulDivUp"][-1]
    L.append(f"- **The fix.** `mulDivUp` rounds the idle balance down, so each withdrawal can only raise the active "
             f"balance. Here it ends at {up} wei against an exact {fmt(ex[-1], 2)}: wrong by {fmt(up - ex[-1], 2)} wei "
             f"({float((up - ex[-1]) / ex[-1]):+.0%}), in the other direction. That is harmless in this state because "
             f"liquidity is bound by the USDT side; when the USDC side binds, liquidity follows the overstated balance. "
             f"The post-mortem says of the change that \"it's unclear if this change will introduce new attack vectors\".")
    L.append(f"- **FP127.** The transliteration is `sub(idle, div(mul(idle, s), T))` with the idle balance stored as a "
             f"127.128 word. FP127's `div` truncates, so it rounds the idle balance up exactly as the deployed code does; "
             f"the grid is 2^-128 wei instead of 1 wei, so {n} steps move it by under {n}·2^-128 ≈ "
             f"{n / 2 ** 128:.1e} wei. A non-negative 127.128 word is below 2^255, so it fits the 255 bits `IdleBalance` "
             f"already gives the balance ({c('idleUnpack')}). It only helps if the stored state is FP127: rounding to a wei "
             f"before storing it brings back the deployed bug, one wei per step.")
    L.append(f"- **Why exact rises to {fmt(ex[-1], 2)}, not 28.** The token transfers still floor in the pool's favour, "
             f"so each withdrawal leaves a fraction of a wei of raw USDC and vault shares behind; that is real USDC in "
             f"the pool and not idle, so it counts as active. Exact idle arithmetic telescopes to idle₀·T₄₄/T₀ "
             f"(asserted).")
    L.append("- **Not modelled.** The sandwich itself, the LDF (`CarpetedDoubleGeometricDistribution`; its outputs are "
             "taken from the trace), and the Unichain transaction.\n")
    dep_err = ex[-1] - seqd[-1]
    L.append(f"**Caveat:** FP127 fixes this only if the idle balance is *stored* as an FP127 word and updated in FP127 "
             f"(token transfers still round to whole wei), and `mulDivUp` alone also stops this {n}-step sequence, ending "
             f"{fmt(up - ex[-1], 2)} wei high where the deployed code ended {fmt(dep_err, 2)} wei low.\n")
    L.append("## Reproduce\n")
    L.append("```\nuv run scripts/replays/bunni.py              # offline: replay + forge test + this file\n"
             "forge test --match-path test/replays/Bunni.t.sol -vv   # offline, the Solidity replay alone\n"
             "uv run scripts/replays/bunni.py fetch        # network (read-only): re-pin bunni.json from the trace\n```\n")
    OUT_MD.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()

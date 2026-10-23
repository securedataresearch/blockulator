// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP19Lib} from "../../contracts/src/fp19/FP19Lib.sol";

// Bunni v2 exploit replay, Ethereum tx 0x1c27c4d6...beb97b (block 23273098, index 84).
//
// Integers: scripts/replays/bunni.json, pinned by `uv run scripts/replays/bunni.py fetch`
// from the transaction's callTracer trace and checked against its receipt. No network here.
//
// The deployed arithmetic below is vendored from the Sourcify-verified source of the
// contracts that executed it (runtime exact matches; every cited line is re-checked against
// that source by `bunni.py fetch`):
//   BunniHubLogic  0x000000000dbb048f2e744e4b15b5aeef65e09528  (withdraw; solady FixedPointMathLib)
//   BunniHookLogic 0x000000007a00d1e94c60f9e1cfb1ea752035f52c  (beforeSwap -> queryLDF; v4-core TickMath)
//   EVK Vault      0xb4ad4d9c02c01b01cf586c16f01c58c73c7f0188  (previewRedeem / withdraw behind both reserve vaults)
// Assembly helpers are copied verbatim; the rest are line-for-line transliterations.

/// solady FixedPointMathLib as compiled into both Bunni libraries
/// (lib/solady/src/utils/FixedPointMathLib.sol, verbatim).
library SoladyMath {
    /// FixedPointMathLib.sol:455-512
    function fullMulDiv(uint256 x, uint256 y, uint256 d) internal pure returns (uint256 z) {
        /// @solidity memory-safe-assembly
        assembly {
            z := mul(x, y)
            for {} 1 {} {
                if iszero(mul(or(iszero(x), eq(div(z, x), y)), d)) {
                    let mm := mulmod(x, y, not(0))
                    let p1 := sub(mm, add(z, lt(mm, z)))
                    let r := mulmod(x, y, d)
                    let t := and(d, sub(0, d))
                    if iszero(gt(d, p1)) {
                        mstore(0x00, 0xae47f702) // `FullMulDivFailed()`.
                        revert(0x1c, 0x04)
                    }
                    d := div(d, t)
                    let inv := xor(2, mul(3, d))
                    inv := mul(inv, sub(2, mul(d, inv)))
                    inv := mul(inv, sub(2, mul(d, inv)))
                    inv := mul(inv, sub(2, mul(d, inv)))
                    inv := mul(inv, sub(2, mul(d, inv)))
                    inv := mul(inv, sub(2, mul(d, inv)))
                    z :=
                        mul(
                            or(mul(sub(p1, gt(r, z)), add(div(sub(0, t), t), 1)), div(sub(z, r), t)),
                            mul(sub(2, mul(d, inv)), inv)
                        )
                    break
                }
                z := div(z, d)
                break
            }
        }
    }

    /// FixedPointMathLib.sol:548-560
    function fullMulDivUp(uint256 x, uint256 y, uint256 d) internal pure returns (uint256 z) {
        z = fullMulDiv(x, y, d);
        /// @solidity memory-safe-assembly
        assembly {
            if mulmod(x, y, d) {
                z := add(z, 1)
                if iszero(z) {
                    mstore(0x00, 0xae47f702) // `FullMulDivFailed()`.
                    revert(0x1c, 0x04)
                }
            }
        }
    }

    /// FixedPointMathLib.sol:595-606 (BunniHubLogic.sol:478 uses this: `balance.mulDiv(shares, currentTotalSupply)`)
    function mulDiv(uint256 x, uint256 y, uint256 d) internal pure returns (uint256 z) {
        /// @solidity memory-safe-assembly
        assembly {
            z := mul(x, y)
            if iszero(mul(or(iszero(x), eq(div(z, x), y)), d)) {
                mstore(0x00, 0xad251c27) // `MulDivFailed()`.
                revert(0x1c, 0x04)
            }
            z := div(z, d)
        }
    }

    /// FixedPointMathLib.sol:610-621 (the fix: `balance.mulDivUp(shares, currentTotalSupply)`)
    function mulDivUp(uint256 x, uint256 y, uint256 d) internal pure returns (uint256 z) {
        /// @solidity memory-safe-assembly
        assembly {
            z := mul(x, y)
            if iszero(mul(or(iszero(x), eq(div(z, x), y)), d)) {
                mstore(0x00, 0xad251c27) // `MulDivFailed()`.
                revert(0x1c, 0x04)
            }
            z := add(iszero(iszero(mod(z, d))), div(z, d))
        }
    }
}

/// Bunni's own math helpers (BunniHookLogic bundle, src/lib/*.sol) and the v4-core pieces it calls.
library BunniMath {
    uint256 internal constant Q96 = 0x1000000000000000000000000;

    /// Math.sol:31-36
    function roundTick(int24 currentTick, int24 tickSpacing) internal pure returns (int24 roundedTick, int24 nextRoundedTick) {
        int24 compressed = currentTick / tickSpacing;
        if (currentTick < 0 && currentTick % tickSpacing != 0) compressed--; // round towards negative infinity
        roundedTick = compressed * tickSpacing;
        nextRoundedTick = roundedTick + tickSpacing;
    }

    /// Math.sol:70-74
    function subReLU(uint256 x, uint256 y) internal pure returns (uint256) {
        unchecked {
            return x > y ? x - y : 0;
        }
    }

    /// Math.sol:80-95
    function roundUpFullMulDivResult(uint256 x, uint256 y, uint256 d, uint256 resultRoundedDown)
        internal
        pure
        returns (uint256 result)
    {
        result = resultRoundedDown;
        /// @solidity memory-safe-assembly
        assembly {
            if mulmod(x, y, d) {
                result := add(resultRoundedDown, 1)
                if iszero(result) {
                    mstore(0x00, 0xae47f702) // `FullMulDivFailed()`.
                    revert(0x1c, 0x04)
                }
            }
        }
    }

    /// FullMathX96.sol:12-36
    function fullMulX96(uint256 x, uint256 y) internal pure returns (uint256 z) {
        /// @solidity memory-safe-assembly
        assembly {
            z := mul(x, y)
            for {} 1 {} {
                if iszero(or(iszero(x), eq(div(z, x), y))) {
                    let mm := mulmod(x, y, not(0))
                    let p1 := sub(mm, add(z, lt(mm, z)))
                    if iszero(shr(96, p1)) {
                        z := add(shl(160, p1), shr(96, z))
                        break
                    }
                    mstore(0x00, 0xae47f702) // `FullMulDivFailed()`.
                    revert(0x1c, 0x04)
                }
                z := shr(96, z)
                break
            }
        }
    }

    /// v4-core UnsafeMath.sol:12-16
    function divRoundingUp(uint256 x, uint256 y) internal pure returns (uint256 z) {
        assembly ("memory-safe") {
            z := add(div(x, y), gt(mod(x, y), 0))
        }
    }

    /// v4-core TickMath.sol:57-113. One change: the InvalidTick custom revert is a require.
    function getSqrtPriceAtTick(int24 tick) internal pure returns (uint160 sqrtPriceX96) {
        unchecked {
            uint256 absTick;
            assembly ("memory-safe") {
                tick := signextend(2, tick)
                let mask := sar(255, tick)
                absTick := xor(mask, add(mask, tick))
            }
            require(absTick <= 887272, "InvalidTick");
            uint256 price;
            assembly ("memory-safe") {
                price := xor(shl(128, 1), mul(xor(shl(128, 1), 0xfffcb933bd6fad37aa2d162d1a594001), and(absTick, 0x1)))
            }
            if (absTick & 0x2 != 0) price = (price * 0xfff97272373d413259a46990580e213a) >> 128;
            if (absTick & 0x4 != 0) price = (price * 0xfff2e50f5f656932ef12357cf3c7fdcc) >> 128;
            if (absTick & 0x8 != 0) price = (price * 0xffe5caca7e10e4e61c3624eaa0941cd0) >> 128;
            if (absTick & 0x10 != 0) price = (price * 0xffcb9843d60f6159c9db58835c926644) >> 128;
            if (absTick & 0x20 != 0) price = (price * 0xff973b41fa98c081472e6896dfb254c0) >> 128;
            if (absTick & 0x40 != 0) price = (price * 0xff2ea16466c96a3843ec78b326b52861) >> 128;
            if (absTick & 0x80 != 0) price = (price * 0xfe5dee046a99a2a811c461f1969c3053) >> 128;
            if (absTick & 0x100 != 0) price = (price * 0xfcbe86c7900a88aedcffc83b479aa3a4) >> 128;
            if (absTick & 0x200 != 0) price = (price * 0xf987a7253ac413176f2b074cf7815e54) >> 128;
            if (absTick & 0x400 != 0) price = (price * 0xf3392b0822b70005940c7a398e4b70f3) >> 128;
            if (absTick & 0x800 != 0) price = (price * 0xe7159475a2c29b7443b29c7fa6e889d9) >> 128;
            if (absTick & 0x1000 != 0) price = (price * 0xd097f3bdfd2022b8845ad8f792aa5825) >> 128;
            if (absTick & 0x2000 != 0) price = (price * 0xa9f746462d870fdf8a65dc1f90e061e5) >> 128;
            if (absTick & 0x4000 != 0) price = (price * 0x70d869a156d2a1b890bb3df62baf32f7) >> 128;
            if (absTick & 0x8000 != 0) price = (price * 0x31be135f97d08fd981231505542fcfa6) >> 128;
            if (absTick & 0x10000 != 0) price = (price * 0x9aa508b5b7a84e1c677de54f3e99bc9) >> 128;
            if (absTick & 0x20000 != 0) price = (price * 0x5d6af8dedb81196699c329225ee604) >> 128;
            if (absTick & 0x40000 != 0) price = (price * 0x2216e584f5fa1ea926041bedfe98) >> 128;
            if (absTick & 0x80000 != 0) price = (price * 0x48a170391f7dc42444e8fa2) >> 128;
            assembly ("memory-safe") {
                if sgt(tick, 0) { price := div(not(0), price) }
                sqrtPriceX96 := shr(32, add(price, sub(shl(32, 1), 1)))
            }
        }
    }

    /// SqrtPriceMath.sol:185-210
    function getAmount0Delta(uint160 sqrtPriceAX96, uint160 sqrtPriceBX96, uint256 liquidity, bool roundUp)
        internal
        pure
        returns (uint256)
    {
        unchecked {
            if (sqrtPriceAX96 > sqrtPriceBX96) (sqrtPriceAX96, sqrtPriceBX96) = (sqrtPriceBX96, sqrtPriceAX96);
            require(sqrtPriceAX96 != 0, "InvalidPrice");
            uint256 numerator1 = uint256(liquidity) << 96;
            uint256 numerator2 = sqrtPriceBX96 - sqrtPriceAX96;
            return roundUp
                ? divRoundingUp(SoladyMath.fullMulDivUp(numerator1, numerator2, sqrtPriceBX96), sqrtPriceAX96)
                : SoladyMath.fullMulDiv(numerator1, numerator2, sqrtPriceBX96) / sqrtPriceAX96;
        }
    }

    /// SqrtPriceMath.sol:213-224, 233-253
    function getAmount1Delta(uint160 sqrtPriceAX96, uint160 sqrtPriceBX96, uint256 liquidity, bool roundUp)
        internal
        pure
        returns (uint256 amount1)
    {
        uint256 numerator = sqrtPriceAX96 >= sqrtPriceBX96 ? sqrtPriceAX96 - sqrtPriceBX96 : sqrtPriceBX96 - sqrtPriceAX96;
        uint256 denominator = Q96;
        uint256 _liquidity = uint256(liquidity);
        amount1 = SoladyMath.fullMulDiv(_liquidity, numerator, denominator);
        assembly ("memory-safe") {
            amount1 := add(amount1, and(gt(mulmod(_liquidity, numerator, denominator), 0), roundUp))
        }
    }

    /// LiquidityAmounts.sol:17-34
    function getAmountsForLiquidity(
        uint160 sqrtRatioX96,
        uint160 sqrtRatioAX96,
        uint160 sqrtRatioBX96,
        uint256 liquidity,
        bool roundingUp
    ) internal pure returns (uint256 amount0, uint256 amount1) {
        if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
        if (sqrtRatioX96 <= sqrtRatioAX96) {
            amount0 = getAmount0Delta(sqrtRatioAX96, sqrtRatioBX96, liquidity, roundingUp);
        } else if (sqrtRatioX96 < sqrtRatioBX96) {
            amount0 = getAmount0Delta(sqrtRatioX96, sqrtRatioBX96, liquidity, roundingUp);
            amount1 = getAmount1Delta(sqrtRatioAX96, sqrtRatioX96, liquidity, roundingUp);
        } else {
            amount1 = getAmount1Delta(sqrtRatioAX96, sqrtRatioBX96, liquidity, roundingUp);
        }
    }

    struct LdfQuery {
        int24 tick;
        int24 tickSpacing;
        uint160 sqrtPriceX96;
        uint256 liquidityDensityOfRoundedTickX96; // ldf.query outputs, taken from the trace
        uint256 density0RightOfRoundedTickX96;
        uint256 density1LeftOfRoundedTickX96;
    }

    struct LdfResult {
        uint256 totalLiquidity;
        uint256 activeBalance0;
        uint256 activeBalance1;
        uint256 estimate0;
        uint256 estimate1;
        uint256 totalDensity0X96;
    }

    /// QueryLDF.sol:64-81: the token densities, from the ldf.query outputs (inputs here).
    function totalDensities(LdfQuery memory q) internal pure returns (uint256 totalDensity0X96, uint256 totalDensity1X96) {
        (int24 roundedTick, int24 nextRoundedTick) = roundTick(q.tick, q.tickSpacing);
        (uint160 roundedTickSqrtRatio, uint160 nextRoundedTickSqrtRatio) =
            (getSqrtPriceAtTick(roundedTick), getSqrtPriceAtTick(nextRoundedTick));
        (uint256 density0OfRoundedTickX96, uint256 density1OfRoundedTickX96) = getAmountsForLiquidity(
            q.sqrtPriceX96, roundedTickSqrtRatio, nextRoundedTickSqrtRatio, q.liquidityDensityOfRoundedTickX96, true
        );
        totalDensity0X96 = q.density0RightOfRoundedTickX96 + density0OfRoundedTickX96;
        totalDensity1X96 = q.density1LeftOfRoundedTickX96 + density1OfRoundedTickX96;
    }

    /// QueryLDF.sol:83-117, no surge, idle balance in token0 (the pool's IdleBalance word has
    /// its top bit set).
    function queryLDF(LdfQuery memory q, uint256 balance0, uint256 balance1, uint256 idleBalance0)
        internal
        pure
        returns (LdfResult memory r)
    {
        (uint256 totalDensity0X96, uint256 totalDensity1X96) = totalDensities(q);
        r.totalDensity0X96 = totalDensity0X96;
        balance0 = subReLU(balance0, idleBalance0); // QueryLDF.sol:88
        if (balance0 != 0 || balance1 != 0) {
            bool noToken0 = balance0 == 0 || totalDensity0X96 == 0;
            bool noToken1 = balance1 == 0 || totalDensity1X96 == 0;
            uint256 totalLiquidityEstimate0 = noToken0 ? 0 : SoladyMath.fullMulDiv(balance0, Q96, totalDensity0X96);
            uint256 totalLiquidityEstimate1 = noToken1 ? 0 : SoladyMath.fullMulDiv(balance1, Q96, totalDensity1X96);
            (r.estimate0, r.estimate1) = (totalLiquidityEstimate0, totalLiquidityEstimate1);
            bool useLiquidityEstimate0 =
                (totalLiquidityEstimate0 < totalLiquidityEstimate1 || totalDensity1X96 == 0) && totalDensity0X96 != 0;
            if (useLiquidityEstimate0) {
                r.totalLiquidity =
                    noToken0 ? 0 : roundUpFullMulDivResult(balance0, Q96, totalDensity0X96, totalLiquidityEstimate0);
                (r.activeBalance0, r.activeBalance1) = (
                    noToken0 ? 0 : _min(balance0, fullMulX96(totalLiquidityEstimate0, totalDensity0X96)),
                    noToken1 ? 0 : _min(balance1, fullMulX96(totalLiquidityEstimate0, totalDensity1X96))
                );
            } else {
                r.totalLiquidity =
                    noToken1 ? 0 : roundUpFullMulDivResult(balance1, Q96, totalDensity1X96, totalLiquidityEstimate1);
                (r.activeBalance0, r.activeBalance1) = (
                    noToken0 ? 0 : _min(balance0, fullMulX96(totalLiquidityEstimate1, totalDensity0X96)),
                    noToken1 ? 0 : _min(balance1, fullMulX96(totalLiquidityEstimate1, totalDensity1X96))
                );
            }
        }
    }

    function _min(uint256 x, uint256 y) private pure returns (uint256) {
        return x < y ? x : y;
    }
}

/// Euler EVK vault conversions at one block timestamp (no accrual between operations):
/// ConversionHelpers.sol:13-25, Shares.sol:22-27 (toAssetsDown), Assets.sol:34-40 (toSharesUp),
/// Vault.sol:35-38 (convertToAssets = previewRedeem), Vault.sol:153-163 (withdraw burns toSharesUp).
library Evk {
    uint256 internal constant VIRTUAL_DEPOSIT_AMOUNT = 1e6;

    struct V {
        uint256 cash;
        uint256 totalBorrows; // as VaultStatus emits it: totalBorrows.toAssetsUp() (Base.sol:144)
        uint256 totalShares;
    }

    function totals(V memory v) internal pure returns (uint256 totalAssets, uint256 totalShares) {
        totalAssets = v.cash + v.totalBorrows + VIRTUAL_DEPOSIT_AMOUNT;
        totalShares = v.totalShares + VIRTUAL_DEPOSIT_AMOUNT;
    }

    function previewRedeem(V memory v, uint256 shares) internal pure returns (uint256) {
        (uint256 a, uint256 s) = totals(v);
        return shares * a / s;
    }

    function withdraw(V memory v, uint256 assets) internal pure returns (uint256 shares) {
        if (assets == 0) return 0;
        (uint256 a, uint256 s) = totals(v);
        shares = (assets * s + (a - 1)) / a;
        v.cash -= assets;
        v.totalShares -= shares;
    }
}

contract BunniReplay is Test {
    string constant DATA = "scripts/replays/bunni.json";
    uint256 constant N = 44;

    string json;

    struct Pool {
        uint256 raw0;
        uint256 raw1;
        uint256 reserve0;
        uint256 reserve1;
        uint256 totalSupply;
        Evk.V v0;
        Evk.V v1;
    }

    /// One idle balance per form; the token flows (Pool) are shared, because every form
    /// pays out exactly what the deployed code pays out.
    struct Idle {
        uint256 deployed; // balance - balance.mulDiv(shares, totalSupply)   BunniHubLogic.sol:478
        uint256 up; //       balance - balance.mulDivUp(shares, totalSupply) (the fix)
        int256 fp127; //     sub(i, div(mul(i, s), T)) in 127.128
        int256 fp19; //     the same in FP19
        uint256 exactNum; // idle0 * T_k: the exact idle balance is exactNum / T_0
    }

    struct Run {
        uint256[] active; // balance0 - idle, deployed, per step (0..N)
        uint256[] activeUp;
        uint256 balance0;
        uint256 balance1;
        uint256 idle0;
        uint256 T0;
        Idle idle;
    }

    function setUp() public {
        json = vm.readFile(DATA);
    }

    function _u(string memory key) internal view returns (uint256) {
        return vm.parseUint(vm.parseJsonString(json, key));
    }

    function _ua(string memory key) internal view returns (uint256[] memory out) {
        string[] memory s = vm.parseJsonStringArray(json, key);
        out = new uint256[](s.length);
        for (uint256 i; i < s.length; i++) out[i] = vm.parseUint(s[i]);
    }

    function _start() internal view returns (Pool memory p) {
        p.raw0 = _u(".start.raw0");
        p.raw1 = _u(".start.raw1");
        p.reserve0 = _u(".start.reserve0");
        p.reserve1 = _u(".start.reserve1");
        p.totalSupply = _u(".start.totalSupply");
        p.v0 = Evk.V(_u(".start.vault0.cash"), _u(".start.vault0.totalBorrows"), _u(".start.vault0.totalShares"));
        p.v1 = Evk.V(_u(".start.vault1.cash"), _u(".start.vault1.totalBorrows"), _u(".start.vault1.totalShares"));
    }

    function _balances(Pool memory p) internal pure returns (uint256 b0, uint256 b1) {
        // BunniHookLogic.sol:193-197: raw + getReservesInUnderlying(reserve, vault) (VaultMath.sol:7)
        b0 = p.raw0 + Evk.previewRedeem(p.v0, p.reserve0);
        b1 = p.raw1 + Evk.previewRedeem(p.v1, p.reserve1);
    }

    /// One withdrawal, BunniHubLogic.sol:462-503, checked against what the chain did.
    function _withdraw(Pool memory p, uint256 k, uint256 shares) internal view {
        uint256 T = p.totalSupply;
        assertEq(T, _ua(".steps.totalSupply")[k], "totalSupply() read inside withdraw");
        uint256 reserveAmount0 = Evk.previewRedeem(p.v0, SoladyMath.mulDiv(p.reserve0, shares, T));
        uint256 reserveAmount1 = Evk.previewRedeem(p.v1, SoladyMath.mulDiv(p.reserve1, shares, T));
        uint256 rawAmount0 = SoladyMath.mulDiv(p.raw0, shares, T);
        uint256 rawAmount1 = SoladyMath.mulDiv(p.raw1, shares, T);
        assertEq(reserveAmount0 + rawAmount0, _ua(".steps.amount0")[k], "Withdraw event amount0");
        assertEq(reserveAmount1 + rawAmount1, _ua(".steps.amount1")[k], "Withdraw event amount1");
        assertEq(rawAmount0, _ua(".steps.rawOut0")[k], "PoolManager take, USDC");
        assertEq(rawAmount1, _ua(".steps.rawOut1")[k], "PoolManager take, USDT");
        assertEq(reserveAmount0, _ua(".steps.vault0Assets")[k], "vault0.withdraw assets");
        assertEq(reserveAmount1, _ua(".steps.vault1Assets")[k], "vault1.withdraw assets");
        uint256 c0 = Evk.withdraw(p.v0, reserveAmount0);
        uint256 c1 = Evk.withdraw(p.v1, reserveAmount1);
        assertEq(c0, _ua(".steps.vault0Burned")[k], "vault0 shares burned");
        assertEq(c1, _ua(".steps.vault1Burned")[k], "vault1 shares burned");
        assertEq(p.v0.totalShares, _ua(".steps.vault0SharesAfter")[k], "vault0 VaultStatus totalShares");
        assertEq(p.v0.cash, _ua(".steps.vault0CashAfter")[k], "vault0 VaultStatus cash");
        assertEq(p.v1.totalShares, _ua(".steps.vault1SharesAfter")[k], "vault1 VaultStatus totalShares");
        assertEq(p.v1.cash, _ua(".steps.vault1CashAfter")[k], "vault1 VaultStatus cash");
        p.reserve0 -= c0;
        p.reserve1 -= c1;
        p.raw0 -= rawAmount0;
        p.raw1 -= rawAmount1;
        p.totalSupply = T - shares;
    }

    function _updateIdle(Idle memory i, uint256 shares, uint256 T) internal pure {
        i.deployed = i.deployed - SoladyMath.mulDiv(i.deployed, shares, T);
        i.up = i.up - SoladyMath.mulDivUp(i.up, shares, T);
        i.fp127 = FP127Lib.sub(i.fp127, FP127Lib.div(FP127Lib.mul(i.fp127, int256(shares) << 128), int256(T) << 128));
        i.fp19 = FP19Lib.sub(i.fp19, FP19Lib.div(FP19Lib.mul(i.fp19, FP19Lib.fromUint(shares)), FP19Lib.fromUint(T)));
        // exact: idle * (T - s) / T; with idle = exactNum / T_0 and exactNum = idle0 * T this is exact
        require(i.exactNum % T == 0, "exactNum = idle0 * T");
        i.exactNum = i.exactNum / T * (T - shares);
    }

    function _checkSnapshot(Pool memory p, Idle memory i, uint256 after_) internal view {
        uint256[] memory ks = vm.parseJsonUintArray(json, ".snapshots.after");
        for (uint256 j; j < ks.length; j++) {
            if (ks[j] != after_) continue;
            assertEq(p.raw0, _ua(".snapshots.raw0")[j], "poolState rawBalance0");
            assertEq(p.raw1, _ua(".snapshots.raw1")[j], "poolState rawBalance1");
            assertEq(p.reserve0, _ua(".snapshots.reserve0")[j], "poolState reserve0");
            assertEq(p.reserve1, _ua(".snapshots.reserve1")[j], "poolState reserve1");
            assertEq(i.deployed, _ua(".snapshots.idle")[j], "poolState idleBalance");
        }
    }

    function _run() internal view returns (Run memory r) {
        Pool memory p = _start();
        r.idle0 = _u(".start.idle");
        r.T0 = p.totalSupply;
        r.idle = Idle(r.idle0, r.idle0, int256(r.idle0) << 128, FP19Lib.fromUint(r.idle0), r.idle0 * r.T0);
        uint256[] memory shares = _ua(".steps.shares");
        assertEq(shares.length, N);
        r.active = new uint256[](N + 1);
        r.activeUp = new uint256[](N + 1);
        (uint256 b0,) = _balances(p);
        r.active[0] = b0 - r.idle.deployed;
        r.activeUp[0] = b0 - r.idle.up;
        for (uint256 k; k < N; k++) {
            uint256 T = p.totalSupply;
            _withdraw(p, k, shares[k]);
            _updateIdle(r.idle, shares[k], T);
            _checkSnapshot(p, r.idle, k + 1);
            (b0,) = _balances(p);
            r.active[k + 1] = b0 - r.idle.deployed;
            r.activeUp[k + 1] = b0 - r.idle.up;
        }
        (r.balance0, r.balance1) = _balances(p);
        // the hook's own vault reads in the first swap after the withdrawals
        assertEq(Evk.previewRedeem(p.v0, p.reserve0), _u(".hookAfter.previewRedeem0"), "hook previewRedeem(reserve0)");
        assertEq(Evk.previewRedeem(p.v1, p.reserve1), _u(".hookAfter.previewRedeem1"), "hook previewRedeem(reserve1)");
        assertEq(r.idle.exactNum, r.idle0 * p.totalSupply, "exact idle telescopes to idle0 * T_n / T_0");
    }

    function _ldf(string memory which) internal view returns (BunniMath.LdfQuery memory q) {
        uint256[] memory out = _ua(string.concat(".ldf.", which, ".out"));
        q = BunniMath.LdfQuery({
            tick: int24(vm.parseJsonInt(json, string.concat(".ldf.", which, ".tick"))),
            tickSpacing: int24(vm.parseJsonInt(json, ".pool.tickSpacing")),
            sqrtPriceX96: uint160(_u(string.concat(".ldf.", which, ".sqrtPriceX96"))),
            liquidityDensityOfRoundedTickX96: out[0],
            density0RightOfRoundedTickX96: out[1],
            density1LeftOfRoundedTickX96: out[2]
        });
    }

    function _emit(string memory form, string memory kv) internal pure {
        console.log(string.concat("REPLAY|", form, "|", kv));
    }

    function _kv(string memory k, uint256 v) internal pure returns (string memory) {
        return string.concat(k, "=", vm.toString(v), ";");
    }

    // ------------------------------------------------------------------------- tests

    /// The deployed withdraw arithmetic, 44 times, against every observation in the trace:
    /// the idle-adjusted USDC balance goes 28 -> 4.
    function test_deployed_withdrawals_match_chain() public view {
        Run memory r = _run();
        assertEq(r.active[0], 28, "balance0 - idle before the withdrawals");
        assertEq(r.active[N], 4, "balance0 - idle after 44 withdrawals");
        for (uint256 k; k <= N; k++) {
            console.log(string.concat("STEP|", vm.toString(k), "|deployed=", vm.toString(r.active[k]), ";mulDivUp=",
                vm.toString(r.activeUp[k])));
        }
    }

    /// queryLDF, ported, reproduces the totalLiquidity and active balances the hook passed to
    /// BunniSwapMath.computeSwap at both states where the chain shows them.
    function test_queryLDF_matches_chain() public view {
        string[2] memory keys = ["swap3", "afterWithdrawals"];
        for (uint256 j; j < 2; j++) {
            string memory o = string.concat(".observed.", keys[j]);
            BunniMath.LdfResult memory r = BunniMath.queryLDF(
                _ldf(vm.parseJsonString(json, string.concat(o, ".ldf"))),
                _u(string.concat(o, ".balance0")),
                _u(string.concat(o, ".balance1")),
                _u(string.concat(o, ".idle"))
            );
            assertEq(r.totalLiquidity, _u(string.concat(o, ".totalLiquidity")), "computeSwap totalLiquidity");
            assertEq(r.activeBalance0, _u(string.concat(o, ".active0")), "computeSwap currentActiveBalance0");
            assertEq(r.activeBalance1, _u(string.concat(o, ".active1")), "computeSwap currentActiveBalance1");
        }
        assertEq(BunniMath.getSqrtPriceAtTick(5000), uint160(_u(".ldf.tick5000.sqrtPriceX96")), "price sits on tick 5000");
    }

    /// The same 44 withdrawals with the idle balance held four other ways; token flows unchanged.
    /// Liquidity takes integer balances, so a fractional active balance is floored first.
    function test_idle_balance_forms() public view {
        Run memory r = _run();
        BunniMath.LdfQuery memory q = _ldf("tick5000");
        uint256 lStart = _formStart(r, q);
        uint256 lDep = _formDeployed(r, q);
        assertLt(lDep * 100, lStart * 16, "deployed: liquidity fell below 16% of its start");
        uint256 lUp = _formUp(r, q);
        uint256 l127 = _formFp127(r, q);
        uint256 l19 = _formFp19(r, q);
        uint256 lEx = _formExact(r, q);
        // every non-deployed form leaves the pool bound by the USDT estimate, at one liquidity
        assertEq(lUp, lEx, "mulDivUp liquidity");
        assertEq(l127, lEx, "FP127 liquidity");
        assertEq(l19, lEx, "FP19 liquidity");
    }

    function _formStart(Run memory r, BunniMath.LdfQuery memory q) internal view returns (uint256) {
        (uint256 s0, uint256 s1) = _balances(_start());
        BunniMath.LdfResult memory x = BunniMath.queryLDF(q, s0, s1, r.idle0);
        _emit("start", string.concat(_kv("active0", s0 - r.idle0), _kv("L", x.totalLiquidity), _kv("est0", x.estimate0),
            _kv("est1", x.estimate1)));
        assertEq(x.totalLiquidity, x.estimate1 + 1, "at 28 wei the USDT estimate binds");
        return x.totalLiquidity;
    }

    function _formDeployed(Run memory r, BunniMath.LdfQuery memory q) internal view returns (uint256) {
        BunniMath.LdfResult memory x = BunniMath.queryLDF(q, r.balance0, r.balance1, r.idle.deployed);
        assertEq(x.totalLiquidity, _u(".observed.afterWithdrawals.totalLiquidity"), "deployed liquidity = chain");
        assertEq(x.totalLiquidity, x.estimate0 + 1, "at 4 wei the USDC estimate binds");
        _emit("deployed", string.concat(_kv("active0", r.balance0 - r.idle.deployed), _kv("L", x.totalLiquidity)));
        return x.totalLiquidity;
    }

    function _formUp(Run memory r, BunniMath.LdfQuery memory q) internal view returns (uint256) {
        assertEq(r.balance0 - r.idle.up, 48, "mulDivUp: 48 wei, above exact");
        BunniMath.LdfResult memory x = BunniMath.queryLDF(q, r.balance0, r.balance1, r.idle.up);
        _emit("mulDivUp", string.concat(_kv("active0", r.balance0 - r.idle.up), _kv("L", x.totalLiquidity)));
        return x.totalLiquidity;
    }

    /// FP127: active = (balance0 << 128) - idle, within 44 units of 2^-128 of exact.
    function _formFp127(Run memory r, BunniMath.LdfQuery memory q) internal view returns (uint256) {
        int256 a = FP127Lib.sub(int256(r.balance0) << 128, r.idle.fp127);
        assertEq(uint256(a >> 128), 35, "FP127: floor 35");
        uint256 lhs = uint256(a) * r.T0;
        uint256 rhs = (r.balance0 * r.T0 - r.idle.exactNum) << 128;
        assertLt(lhs > rhs ? lhs - rhs : rhs - lhs, N * r.T0, "FP127 within 44 ulp of exact");
        BunniMath.LdfResult memory x = BunniMath.queryLDF(q, r.balance0, r.balance1, r.balance0 - uint256(a >> 128));
        _emit("fp127", string.concat(_kv("active0", uint256(a)), _kv("L", x.totalLiquidity)));
        return x.totalLiquidity;
    }

    function _formFp19(Run memory r, BunniMath.LdfQuery memory q) internal view returns (uint256) {
        int256 a = FP19Lib.sub(FP19Lib.fromUint(r.balance0), r.idle.fp19);
        assertEq(_fp19Floor(a), 35, "FP19: floor 35");
        BunniMath.LdfResult memory x = BunniMath.queryLDF(q, r.balance0, r.balance1, r.balance0 - _fp19Floor(a));
        _emit("fp19", string.concat(_kv("active0", uint256(a)), _kv("L", x.totalLiquidity)));
        return x.totalLiquidity;
    }

    /// exact: active = balance0 - idle0 * T_n / T_0 = (balance0 * T_0 - exactNum) / T_0
    function _formExact(Run memory r, BunniMath.LdfQuery memory q) internal view returns (uint256) {
        uint256 num = r.balance0 * r.T0 - r.idle.exactNum;
        assertEq(num / r.T0, 35, "exact: 35.63 wei");
        BunniMath.LdfResult memory x = BunniMath.queryLDF(q, r.balance0, r.balance1, r.balance0 - num / r.T0);
        assertEq(x.totalLiquidity, x.estimate1 + 1, "exact: the USDT estimate still binds");
        _emit("exact", string.concat(_kv("num", num), _kv("den", r.T0), _kv("L", x.totalLiquidity)));
        return x.totalLiquidity;
    }

    /// floor of a non-negative FP19 word (README: value = (2^236 + F) * 2^(E - 262143 - 236))
    function _fp19Floor(int256 x) internal pure returns (uint256) {
        uint256 w = uint256(x);
        require(w >> 255 == 0, "negative");
        if (w == 0) return 0;
        uint256 e = (w >> 236) & ((1 << 19) - 1);
        uint256 m = (1 << 236) | (w & ((1 << 236) - 1));
        int256 sh = int256(e) - 262143 - 236;
        if (sh >= 0) return m << uint256(sh);
        uint256 rsh = uint256(-sh);
        return rsh >= 256 ? 0 : m >> rsh;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP127Lib} from "fp127/FP127Lib.sol";
import {FP256Lib} from "fp256/FP256Lib.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

// The snippets of the "Integrating" sections (README, /library/, /library/fp256/),
// compiled and run against the replays in test/examples/Integrating.t.sol.
//
// Two rules. Store the state in the format. Round toward the protocol at the token
// edge: floor what is paid out, ceil what is taken in.
//
// Two moves that take roundings out: divide last (one 512-bit mulDiv, one rounding), and
// keep an index as its logarithm (each accrual an exact add, one exp when it is read).
//
// The directed ops (FP127 mulUp, mulDown, divUp, divDown, toFixed18Up, toFixed18Down;
// FP256 mulUp, mulDown, divUp, divDown, toUintUp, toUintDown, toIntUp, toIntDown,
// toFixed18Up, toFixed18Down, floor, ceil) are in FP127 v5 and FP256 release four, deployed
// (Blockulator 2.1) and inline; the older FP127 v4 and FP256 release three objects do not
// have them, except FP127's floor and ceil.

/// FP127 has no fromUint: an integer below 2^127 is `int256(x) << 128`.
function q(uint256 x) pure returns (int256) {
    require(x < 1 << 127, "FP127 range");
    return int256(x) << 128;
}

/// Rule 1 (Bunni v2): the idle balance stays a 127.128 word of token wei.
/// BunniHubLogic.sol:478 is `balance - balance.mulDiv(shares, totalSupply)` on whole wei.
contract IdleBalance127 {
    int256 public idle; // wei x 2^128, never rounded before it is stored

    constructor(uint256 idleWei) {
        idle = q(idleWei);
    }

    function withdraw(uint256 shares, uint256 totalSupply) external {
        idle = FP127Lib.sub(idle, FP127Lib.div(FP127Lib.mul(idle, q(shares)), q(totalSupply)));
    }

    /// The edge: what the pool may price with, in whole wei, rounded down.
    function active(uint256 balanceWei) external view returns (uint256) {
        return uint256(FP127Lib.floor(FP127Lib.sub(q(balanceWei), idle)) >> 128);
    }
}

/// Rule 1 in FP256: the same state as an FP256 word.
contract IdleBalance256 {
    int256 public idle;

    constructor(uint256 idleWei) {
        idle = FP256Lib.fromUint(idleWei); // exact below 2^237
    }

    function withdraw(uint256 shares, uint256 totalSupply) external {
        idle = FP256Lib.sub(idle, FP256Lib.div(FP256Lib.mul(idle, FP256Lib.fromUint(shares)), FP256Lib.fromUint(totalSupply)));
    }

    function active(uint256 balanceWei) external view returns (uint256) {
        return FP256Lib.toUintDown(FP256Lib.sub(FP256Lib.fromUint(balanceWei), idle));
    }
}

/// Rule 2 (Resupply): ResupplyPairCore.sol:573 and :282 in FP127.
/// The LTV is held against the borrower, so every step rounds up.
/// The most a position may borrow is paid out, so every step rounds down.
library Solvency127 {
    /// collateral wei per 1e18 debt wei, never below the true rate
    function rateUp(uint256 price) internal pure returns (int256) {
        return FP127Lib.divUp(q(1e36), q(price));
    }

    /// LTV in units of 1e-5, never below the true LTV
    function ltv(uint256 debt, uint256 price, uint256 collateral) internal pure returns (int256) {
        int256 x = FP127Lib.mulUp(FP127Lib.mulUp(q(debt), rateUp(price)), q(1e5));
        return FP127Lib.divUp(FP127Lib.divUp(x, q(1e18)), q(collateral));
    }

    function isSolvent(uint256 debt, uint256 price, uint256 collateral, uint256 maxLTV) internal pure returns (bool) {
        return ltv(debt, price, collateral) <= q(maxLTV);
    }

    /// The edge, charged: the LTV on the protocol's integer grid, rounded up.
    function ltvOnGrid(uint256 debt, uint256 price, uint256 collateral) internal pure returns (uint256) {
        return uint256(FP127Lib.ceil(ltv(debt, price, collateral)) >> 128);
    }

    /// The edge, paid out: the most the position may borrow, in debt-token wei, rounded down.
    function maxBorrow(uint256 collateral, uint256 maxLTV, uint256 price) internal pure returns (uint256) {
        int256 tokens = FP127Lib.divDown(FP127Lib.mulDown(q(collateral), q(maxLTV)), FP127Lib.mulUp(rateUp(price), q(1e5)));
        return uint256(FP127Lib.toFixed18Down(tokens)); // whole tokens -> 18-decimal wei, down
    }
}

/// Rule 2 (Resupply) in FP256.
library Solvency256 {
    function rateUp(uint256 price) internal pure returns (int256) {
        return FP256Lib.divUp(FP256Lib.fromUint(1e36), FP256Lib.fromUint(price));
    }

    function ltv(uint256 debt, uint256 price, uint256 collateral) internal pure returns (int256) {
        int256 x = FP256Lib.mulUp(FP256Lib.mulUp(FP256Lib.fromUint(debt), rateUp(price)), FP256Lib.fromUint(1e5));
        return FP256Lib.divUp(FP256Lib.divUp(x, FP256Lib.fromUint(1e18)), FP256Lib.fromUint(collateral));
    }

    function isSolvent(uint256 debt, uint256 price, uint256 collateral, uint256 maxLTV) internal pure returns (bool) {
        return FP256Lib.cmp(ltv(debt, price, collateral), FP256Lib.fromUint(maxLTV)) <= 0;
    }

    function ltvOnGrid(uint256 debt, uint256 price, uint256 collateral) internal pure returns (uint256) {
        return FP256Lib.toUintUp(ltv(debt, price, collateral));
    }

    function maxBorrow(uint256 collateral, uint256 maxLTV, uint256 price) internal pure returns (uint256) {
        int256 tokens = FP256Lib.divDown(
            FP256Lib.mulDown(FP256Lib.fromUint(collateral), FP256Lib.fromUint(maxLTV)),
            FP256Lib.mulUp(rateUp(price), FP256Lib.fromUint(1e5))
        );
        return uint256(FP256Lib.toFixed18Down(tokens));
    }
}

/// Rule 2 (Balancer V1): calcSingleInGivenPoolOut and calcSingleOutGivenPoolIn
/// (BMath.sol:146-155, :184-194) in FP256. The formula is evaluated once, in the
/// format; the direction is chosen only where it lands on whole token units.
library JoinExit256 {
    function _fee(uint256 weight, uint256 totalWeight, uint256 feeWad) private pure returns (int256) {
        int256 share = FP256Lib.div(FP256Lib.fromUint(weight), FP256Lib.fromUint(totalWeight));
        return FP256Lib.mul(FP256Lib.sub(FP256Lib.ONE, share), FP256Lib.fromFixed18(int256(feeWad)));
    }

    /// Tokens the pool takes in for `poolOut` BPT: rounded up.
    function joinCost(uint256 balance, uint256 weight, uint256 supply, uint256 totalWeight, uint256 poolOut, uint256 feeWad)
        internal
        pure
        returns (uint256)
    {
        int256 x = FP256Lib.div(FP256Lib.fromUint(poolOut), FP256Lib.fromUint(supply));
        int256 y = FP256Lib.div(FP256Lib.fromUint(totalWeight), FP256Lib.fromUint(weight));
        int256 g = FP256Lib.expm1(FP256Lib.mul(y, FP256Lib.log1p(x))); // (1 + x)^y - 1
        int256 cost = FP256Lib.div(FP256Lib.mul(FP256Lib.fromUint(balance), g), FP256Lib.sub(FP256Lib.ONE, _fee(weight, totalWeight, feeWad)));
        return FP256Lib.toUintUp(cost);
    }

    /// Tokens the pool pays out for `poolIn` BPT: rounded down.
    function exitPays(uint256 balance, uint256 weight, uint256 supply, uint256 totalWeight, uint256 poolIn, uint256 feeWad)
        internal
        pure
        returns (uint256)
    {
        int256 x = FP256Lib.div(FP256Lib.fromUint(poolIn), FP256Lib.fromUint(supply));
        int256 y = FP256Lib.div(FP256Lib.fromUint(totalWeight), FP256Lib.fromUint(weight));
        int256 g = FP256Lib.neg(FP256Lib.expm1(FP256Lib.mul(y, FP256Lib.log1p(FP256Lib.neg(x))))); // 1 - (1 - x)^y
        int256 pays = FP256Lib.mul(FP256Lib.mul(FP256Lib.fromUint(balance), g), FP256Lib.sub(FP256Lib.ONE, _fee(weight, totalWeight, feeWad)));
        return FP256Lib.toUintDown(pays);
    }
}

/// Rule 2 (Balancer V2): a GIVEN_OUT swap charges amountIn / (1 - fee)
/// (BasePool.sol:618-621), then converts to token wei (_downscaleUp). Here the
/// amount in comes from the solver as an FP256 word, the given-out amount and the
/// balances were never truncated, and the only step onto the wei grid is the last.
library SwapCharge256 {
    function chargeIn(int256 amountIn, uint256 feeWad) internal pure returns (uint256) {
        int256 gross = FP256Lib.divUp(FP256Lib.mulUp(amountIn, FP256Lib.fromUint(1e18)), FP256Lib.fromUint(1e18 - feeWad));
        return FP256Lib.toUintUp(gross);
    }

    /// amount x rate / 1e18 kept in the format (BasePool.sol:680-686 truncates it to wei)
    function upscale(uint256 amount, uint256 rateWad) internal pure returns (int256) {
        return FP256Lib.div(FP256Lib.mul(FP256Lib.fromUint(amount), FP256Lib.fromUint(rateWad)), FP256Lib.fromUint(1e18));
    }
}

// ---- Moving the maths: fewer roundings, not more digits ------------------------------------

/// Divide last (Resupply). ResupplyPairCore.sol:573 divides first, `1e36 / price`, and the
/// floor made the rate 0. Moved to the end, debt * 1e36 * 1e5 / (price * 1e18 * collateral)
/// is one 512-bit product and one division: one rounding, in the protocol's direction.
library DivideLast {
    /// LTV in units of 1e-5, rounded up: it is held against the borrower.
    /// 1e23 is 1e36 * 1e5 / 1e18. The checked `*` reverts rather than wraps.
    function ltvUp(uint256 debt, uint256 price, uint256 collateral) internal pure returns (uint256) {
        return FixedPointMathLib.fullMulDivUp(debt, 1e23, price * collateral);
    }

    /// The most the position may owe, in debt-token wei, rounded down: it is paid out.
    function maxBorrow(uint256 collateral, uint256 maxLTV, uint256 price) internal pure returns (uint256) {
        return FixedPointMathLib.fullMulDiv(collateral * maxLTV, price, 1e23);
    }

    /// The same move on FP127 words a, b >= 0, c > 0: the 2^128 scales cancel, so the word
    /// a * b / c is fullMulDiv on the raw integers, rounded once, down.
    /// FP127Lib.div(FP127Lib.mul(a, b), c) rounds twice.
    function mulDiv127(int256 a, int256 b, int256 c) internal pure returns (int256) {
        require(a >= 0 && b >= 0 && c > 0, "a, b >= 0, c > 0");
        uint256 r = FixedPointMathLib.fullMulDiv(uint256(a), uint256(b), uint256(c));
        require(r < 1 << 255, "FP127 range");
        return int256(r);
    }
}

/// The index stored as a product: every accrual is an exp and a mul, two roundings.
contract Index127 {
    int256 public index = 1 << 128; // 1.0

    function accrue(int256 ratePerSecond, uint256 dt) external {
        index = FP127Lib.mul(index, FP127Lib.exp(ratePerSecond * int256(dt)));
    }
}

/// The index stored as its logarithm: every accrual is an add, which never rounds.
/// ratePerSecond is a continuous rate (ln of the growth per second) as an FP127 word.
contract LogIndex127 {
    int256 public logIndex; // ln(index); 0 is an index of 1

    function accrue(int256 ratePerSecond, uint256 dt) external {
        // a word times a whole number is an integer product; add only checks overflow
        logIndex = FP127Lib.add(logIndex, ratePerSecond * int256(dt));
    }

    /// The one rounding, at the read: e^L to the nearest word (v5). Reverts above L = 88.
    function index() external view returns (int256) {
        return FP127Lib.exp(logIndex);
    }

    /// The same read in FP256: fromFP127 is exact below 2^109 and exp is correctly rounded,
    /// so this is e^L rounded once, and it is not capped at 88.
    function index256() external view returns (int256) {
        return FP256Lib.exp(FP256Lib.fromFP127(logIndex));
    }
}

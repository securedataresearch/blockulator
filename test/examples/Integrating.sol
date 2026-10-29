// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {BL127Lib} from "bl127/BL127Lib.sol";
import {BL19Lib} from "bl19/BL19Lib.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";

// The snippets of the "Integrating" sections (README, /library/, /library/bl19/),
// compiled and run against the replays in test/examples/Integrating.t.sol.
//
// Two rules. Store the state in the format. Round toward the protocol at the token
// edge: floor what is paid out, ceil what is taken in.
//
// Two moves that take roundings out: divide last (one 512-bit mulDiv, one rounding), and
// keep an index as its logarithm (each accrual an exact add, one exp when it is read).
//
// The directed ops (BL127 mulUp, mulDown, divUp, divDown, toFixed18Up, toFixed18Down;
// BL19 mulUp, mulDown, divUp, divDown, toUintUp, toUintDown, toIntUp, toIntDown,
// toFixed18Up, toFixed18Down, floor, ceil) are in BL127 v9 and BL19 v6, deployed
// (Blockulator 3.0; also BL127 v5 to v8, BL19 release four and v5, Blockulator 2.1 and 2.2) and inline; the older BL127 v4 and BL19 release three objects do not
// have them, except BL127's floor and ceil.

/// BL127 has no fromUint: an integer below 2^127 is `int256(x) << 128`.
function q(uint256 x) pure returns (int256) {
    require(x < 1 << 127, "BL127 range");
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
        idle = BL127Lib.sub(idle, BL127Lib.div(BL127Lib.mul(idle, q(shares)), q(totalSupply)));
    }

    /// The edge: what the pool may price with, in whole wei, rounded down.
    function active(uint256 balanceWei) external view returns (uint256) {
        return uint256(BL127Lib.floor(BL127Lib.sub(q(balanceWei), idle)) >> 128);
    }
}

/// Rule 1 in BL19: the same state as an BL19 word.
contract IdleBalance19 {
    int256 public idle;

    constructor(uint256 idleWei) {
        idle = BL19Lib.fromUint(idleWei); // exact below 2^237
    }

    function withdraw(uint256 shares, uint256 totalSupply) external {
        idle = BL19Lib.sub(idle, BL19Lib.div(BL19Lib.mul(idle, BL19Lib.fromUint(shares)), BL19Lib.fromUint(totalSupply)));
    }

    function active(uint256 balanceWei) external view returns (uint256) {
        return BL19Lib.toUintDown(BL19Lib.sub(BL19Lib.fromUint(balanceWei), idle));
    }
}

/// Rule 2 (Resupply): ResupplyPairCore.sol:573 and :282 in BL127.
/// The LTV is held against the borrower, so every step rounds up.
/// The most a position may borrow is paid out, so every step rounds down.
library Solvency127 {
    /// collateral wei per 1e18 debt wei, never below the true rate
    function rateUp(uint256 price) internal pure returns (int256) {
        return BL127Lib.divUp(q(1e36), q(price));
    }

    /// LTV in units of 1e-5, never below the true LTV
    function ltv(uint256 debt, uint256 price, uint256 collateral) internal pure returns (int256) {
        int256 x = BL127Lib.mulUp(BL127Lib.mulUp(q(debt), rateUp(price)), q(1e5));
        return BL127Lib.divUp(BL127Lib.divUp(x, q(1e18)), q(collateral));
    }

    function isSolvent(uint256 debt, uint256 price, uint256 collateral, uint256 maxLTV) internal pure returns (bool) {
        return ltv(debt, price, collateral) <= q(maxLTV);
    }

    /// The edge, charged: the LTV on the protocol's integer grid, rounded up.
    function ltvOnGrid(uint256 debt, uint256 price, uint256 collateral) internal pure returns (uint256) {
        return uint256(BL127Lib.ceil(ltv(debt, price, collateral)) >> 128);
    }

    /// The edge, paid out: the most the position may borrow, in debt-token wei, rounded down.
    function maxBorrow(uint256 collateral, uint256 maxLTV, uint256 price) internal pure returns (uint256) {
        int256 tokens = BL127Lib.divDown(BL127Lib.mulDown(q(collateral), q(maxLTV)), BL127Lib.mulUp(rateUp(price), q(1e5)));
        return uint256(BL127Lib.toFixed18Down(tokens)); // whole tokens -> 18-decimal wei, down
    }
}

/// Rule 2 (Resupply) in BL19.
library Solvency19 {
    function rateUp(uint256 price) internal pure returns (int256) {
        return BL19Lib.divUp(BL19Lib.fromUint(1e36), BL19Lib.fromUint(price));
    }

    function ltv(uint256 debt, uint256 price, uint256 collateral) internal pure returns (int256) {
        int256 x = BL19Lib.mulUp(BL19Lib.mulUp(BL19Lib.fromUint(debt), rateUp(price)), BL19Lib.fromUint(1e5));
        return BL19Lib.divUp(BL19Lib.divUp(x, BL19Lib.fromUint(1e18)), BL19Lib.fromUint(collateral));
    }

    function isSolvent(uint256 debt, uint256 price, uint256 collateral, uint256 maxLTV) internal pure returns (bool) {
        return BL19Lib.cmp(ltv(debt, price, collateral), BL19Lib.fromUint(maxLTV)) <= 0;
    }

    function ltvOnGrid(uint256 debt, uint256 price, uint256 collateral) internal pure returns (uint256) {
        return BL19Lib.toUintUp(ltv(debt, price, collateral));
    }

    function maxBorrow(uint256 collateral, uint256 maxLTV, uint256 price) internal pure returns (uint256) {
        int256 tokens = BL19Lib.divDown(
            BL19Lib.mulDown(BL19Lib.fromUint(collateral), BL19Lib.fromUint(maxLTV)),
            BL19Lib.mulUp(rateUp(price), BL19Lib.fromUint(1e5))
        );
        return uint256(BL19Lib.toFixed18Down(tokens));
    }
}

/// Rule 2 (Balancer V1): calcSingleInGivenPoolOut and calcSingleOutGivenPoolIn
/// (BMath.sol:146-155, :184-194) in BL19. The formula is evaluated once, in the
/// format; the direction is chosen only where it lands on whole token units.
library JoinExit19 {
    function _fee(uint256 weight, uint256 totalWeight, uint256 feeWad) private pure returns (int256) {
        int256 share = BL19Lib.div(BL19Lib.fromUint(weight), BL19Lib.fromUint(totalWeight));
        return BL19Lib.mul(BL19Lib.sub(BL19Lib.ONE, share), BL19Lib.fromFixed18(int256(feeWad)));
    }

    /// Tokens the pool takes in for `poolOut` BPT: rounded up.
    function joinCost(uint256 balance, uint256 weight, uint256 supply, uint256 totalWeight, uint256 poolOut, uint256 feeWad)
        internal
        pure
        returns (uint256)
    {
        int256 x = BL19Lib.div(BL19Lib.fromUint(poolOut), BL19Lib.fromUint(supply));
        int256 y = BL19Lib.div(BL19Lib.fromUint(totalWeight), BL19Lib.fromUint(weight));
        int256 g = BL19Lib.expm1(BL19Lib.mul(y, BL19Lib.log1p(x))); // (1 + x)^y - 1
        int256 cost = BL19Lib.div(BL19Lib.mul(BL19Lib.fromUint(balance), g), BL19Lib.sub(BL19Lib.ONE, _fee(weight, totalWeight, feeWad)));
        return BL19Lib.toUintUp(cost);
    }

    /// Tokens the pool pays out for `poolIn` BPT: rounded down.
    function exitPays(uint256 balance, uint256 weight, uint256 supply, uint256 totalWeight, uint256 poolIn, uint256 feeWad)
        internal
        pure
        returns (uint256)
    {
        int256 x = BL19Lib.div(BL19Lib.fromUint(poolIn), BL19Lib.fromUint(supply));
        int256 y = BL19Lib.div(BL19Lib.fromUint(totalWeight), BL19Lib.fromUint(weight));
        int256 g = BL19Lib.neg(BL19Lib.expm1(BL19Lib.mul(y, BL19Lib.log1p(BL19Lib.neg(x))))); // 1 - (1 - x)^y
        int256 pays = BL19Lib.mul(BL19Lib.mul(BL19Lib.fromUint(balance), g), BL19Lib.sub(BL19Lib.ONE, _fee(weight, totalWeight, feeWad)));
        return BL19Lib.toUintDown(pays);
    }
}

/// Rule 2 (Balancer V2): a GIVEN_OUT swap charges amountIn / (1 - fee)
/// (BasePool.sol:618-621), then converts to token wei (_downscaleUp). Here the
/// amount in comes from the solver as an BL19 word, the given-out amount and the
/// balances were never truncated, and the only step onto the wei grid is the last.
library SwapCharge19 {
    function chargeIn(int256 amountIn, uint256 feeWad) internal pure returns (uint256) {
        int256 gross = BL19Lib.divUp(BL19Lib.mulUp(amountIn, BL19Lib.fromUint(1e18)), BL19Lib.fromUint(1e18 - feeWad));
        return BL19Lib.toUintUp(gross);
    }

    /// amount x rate / 1e18 kept in the format (BasePool.sol:680-686 truncates it to wei)
    function upscale(uint256 amount, uint256 rateWad) internal pure returns (int256) {
        return BL19Lib.div(BL19Lib.mul(BL19Lib.fromUint(amount), BL19Lib.fromUint(rateWad)), BL19Lib.fromUint(1e18));
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

    /// The same move on BL127 words a, b >= 0, c > 0: the 2^128 scales cancel, so the word
    /// a * b / c is fullMulDiv on the raw integers, rounded once, down.
    /// BL127Lib.div(BL127Lib.mul(a, b), c) rounds twice.
    function mulDiv127(int256 a, int256 b, int256 c) internal pure returns (int256) {
        require(a >= 0 && b >= 0 && c > 0, "a, b >= 0, c > 0");
        uint256 r = FixedPointMathLib.fullMulDiv(uint256(a), uint256(b), uint256(c));
        require(r < 1 << 255, "BL127 range");
        return int256(r);
    }
}

/// The index stored as a product: every accrual is an exp and a mul, two roundings.
contract Index127 {
    int256 public index = 1 << 128; // 1.0

    function accrue(int256 ratePerSecond, uint256 dt) external {
        index = BL127Lib.mul(index, BL127Lib.exp(ratePerSecond * int256(dt)));
    }
}

/// The index stored as its logarithm: every accrual is an add, which never rounds.
/// ratePerSecond is a continuous rate (ln of the growth per second) as an BL127 word.
contract LogIndex127 {
    int256 public logIndex; // ln(index); 0 is an index of 1

    function accrue(int256 ratePerSecond, uint256 dt) external {
        // a word times a whole number is an integer product; add only checks overflow
        logIndex = BL127Lib.add(logIndex, ratePerSecond * int256(dt));
    }

    /// The one rounding, at the read: e^L to the nearest word (since v5). Reverts above L = 88.
    function index() external view returns (int256) {
        return BL127Lib.exp(logIndex);
    }

    /// The same read in BL19: fromBL127 is exact below 2^109 and exp is correctly rounded,
    /// so this is e^L rounded once, and it is not capped at 88.
    function index19() external view returns (int256) {
        return BL19Lib.exp(BL19Lib.fromBL127(logIndex));
    }
}

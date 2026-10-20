// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title BalancerV1Math
/// @notice A transcription of the arithmetic of Balancer V1's BPool as deployed by
///         BFactory 0x9424B1412450D0f8Fc2255FAf6046b98213B76Bd. The source is the
///         Etherscan-verified BPool at 0x2257aaac34bcb27900291f7b84ee2565a6cbac57
///         (solc 0.5.12+commit.7709ece9, optimizer 2000 runs; GPL-3.0-or-later,
///         balancer-labs/balancer-core). scripts/replays/balancer_v1.py fetch recompiles
///         those files and finds the runtime bytecode of all five attacked pools equal to
///         it, metadata included; the line numbers below are into those verified files
///         and are recorded in scripts/replays/balancer_v1.json (.source.lines), with the
///         sha256 of each file.
///
///         Solidity 0.5 does not check overflow; BNum's own requires do, and they are kept
///         as written. Every operation is inside `unchecked` so the 0.8 compiler adds
///         nothing the 0.5 code did not have. The revert strings are the originals.
library BalancerV1Math {
    // BConst.sol:19, 26, 35-37, 39-40
    uint256 internal constant BONE = 10 ** 18;
    uint256 internal constant EXIT_FEE = 0;
    uint256 internal constant MIN_BPOW_BASE = 1 wei;
    uint256 internal constant MAX_BPOW_BASE = (2 * BONE) - 1 wei;
    uint256 internal constant BPOW_PRECISION = BONE / 10 ** 10;
    uint256 internal constant MAX_IN_RATIO = BONE / 2;
    uint256 internal constant MAX_OUT_RATIO = (BONE / 3) + 1 wei;

    // BNum.sol:20-25
    function btoi(uint256 a) internal pure returns (uint256) {
        return a / BONE;
    }

    // BNum.sol:27-32
    function bfloor(uint256 a) internal pure returns (uint256) {
        unchecked { return btoi(a) * BONE; }
    }

    // BNum.sol:34-41
    function badd(uint256 a, uint256 b) internal pure returns (uint256) {
        unchecked {
            uint256 c = a + b;
            require(c >= a, "ERR_ADD_OVERFLOW");
            return c;
        }
    }

    // BNum.sol:43-50
    function bsub(uint256 a, uint256 b) internal pure returns (uint256) {
        (uint256 c, bool flag) = bsubSign(a, b);
        require(!flag, "ERR_SUB_UNDERFLOW");
        return c;
    }

    // BNum.sol:52-61
    function bsubSign(uint256 a, uint256 b) internal pure returns (uint256, bool) {
        unchecked {
            if (a >= b) return (a - b, false);
            else return (b - a, true);
        }
    }

    // BNum.sol:63-73: (a*b + BONE/2) / BONE, half up on the 1e-18 grid
    function bmul(uint256 a, uint256 b) internal pure returns (uint256) {
        unchecked {
            uint256 c0 = a * b;
            require(a == 0 || c0 / a == b, "ERR_MUL_OVERFLOW");
            uint256 c1 = c0 + (BONE / 2);
            require(c1 >= c0, "ERR_MUL_OVERFLOW");
            return c1 / BONE;
        }
    }

    // BNum.sol:75-86: (a*BONE + b/2) / b, half up on the 1e-18 grid
    function bdiv(uint256 a, uint256 b) internal pure returns (uint256) {
        unchecked {
            require(b != 0, "ERR_DIV_ZERO");
            uint256 c0 = a * BONE;
            require(a == 0 || c0 / a == BONE, "ERR_DIV_INTERNAL");
            uint256 c1 = c0 + (b / 2);
            require(c1 >= c0, "ERR_DIV_INTERNAL");
            return c1 / b;
        }
    }

    // BNum.sol:89-103 (DSMath.wpow): square and multiply, bmul at every step
    function bpowi(uint256 a, uint256 n) internal pure returns (uint256) {
        unchecked {
            uint256 z = n % 2 != 0 ? a : BONE;
            for (n /= 2; n != 0; n /= 2) {
                a = bmul(a, a);
                if (n % 2 != 0) z = bmul(z, a);
            }
            return z;
        }
    }

    // BNum.sol:108-126: base^exp = base^floor(exp) * base^frac(exp); the series only for a fractional part
    function bpow(uint256 base, uint256 exp) internal pure returns (uint256) {
        require(base >= MIN_BPOW_BASE, "ERR_BPOW_BASE_TOO_LOW");
        require(base <= MAX_BPOW_BASE, "ERR_BPOW_BASE_TOO_HIGH");
        uint256 whole = bfloor(exp);
        uint256 remain = bsub(exp, whole);
        uint256 wholePow = bpowi(base, btoi(whole));
        if (remain == 0) return wholePow;
        (uint256 partialResult,,) = bpowApprox(base, remain, BPOW_PRECISION);
        return bmul(wholePow, partialResult);
    }

    // BNum.sol:128-161: the binomial series of (1 + x)^a, stopped when a term falls below
    // `precision` (BPOW_PRECISION = 1e8 wei = 1e-10). Returns the sum as deployed, and, for
    // measurement only, the iterations the loop ran and the last term it computed.
    function bpowApprox(uint256 base, uint256 exp, uint256 precision)
        internal
        pure
        returns (uint256 sum, uint256 iterations, uint256 lastTerm)
    {
        unchecked {
            uint256 a = exp;
            (uint256 x, bool xneg) = bsubSign(base, BONE);
            uint256 term = BONE;
            sum = term;
            bool negative = false;
            for (uint256 i = 1; term >= precision; i++) {
                iterations = i;
                uint256 bigK = i * BONE;
                (uint256 c, bool cneg) = bsubSign(a, bsub(bigK, BONE));
                term = bmul(term, bmul(c, x));
                term = bdiv(term, bigK);
                if (term == 0) break;
                if (xneg) negative = !negative;
                if (cneg) negative = !negative;
                if (negative) sum = bsub(sum, term);
                else sum = badd(sum, term);
            }
            lastTerm = term;
        }
    }

    // BMath.sol:28-43
    function calcSpotPrice(uint256 bI, uint256 wI, uint256 bO, uint256 wO, uint256 swapFee)
        internal
        pure
        returns (uint256)
    {
        uint256 numer = bdiv(bI, wI);
        uint256 denom = bdiv(bO, wO);
        uint256 ratio = bdiv(numer, denom);
        uint256 scale = bdiv(BONE, bsub(BONE, swapFee));
        return bmul(ratio, scale);
    }

    // BMath.sol:55-74
    function calcOutGivenIn(uint256 bI, uint256 wI, uint256 bO, uint256 wO, uint256 aI, uint256 swapFee)
        internal
        pure
        returns (uint256)
    {
        uint256 weightRatio = bdiv(wI, wO);
        uint256 adjustedIn = bmul(aI, bsub(BONE, swapFee));
        uint256 y = bdiv(bI, badd(bI, adjustedIn));
        uint256 foo = bpow(y, weightRatio);
        return bmul(bO, bsub(BONE, foo));
    }

    // BMath.sol:86-105
    function calcInGivenOut(uint256 bI, uint256 wI, uint256 bO, uint256 wO, uint256 aO, uint256 swapFee)
        internal
        pure
        returns (uint256)
    {
        uint256 weightRatio = bdiv(wO, wI);
        uint256 y = bdiv(bO, bsub(bO, aO));
        uint256 foo = bsub(bpow(y, weightRatio), BONE);
        return bdiv(bmul(bI, foo), bsub(BONE, swapFee));
    }

    /// The intermediate integers of calcSingleInGivenPoolOut, named as in BMath.sol.
    struct JoinSteps {
        uint256 normalizedWeight;
        uint256 poolRatio;
        uint256 boo;
        uint256 tokenInRatio; // 18-decimal: (1 + pAo/pS)^(tW/wI)
        uint256 newTokenBalanceIn; // token units: bmul(tokenInRatio, bI), half up to the nearest unit
        uint256 tokenAmountInAfterFee;
        uint256 zar;
        uint256 tokenAmountIn;
    }

    // BMath.sol:156-182
    function calcSingleInGivenPoolOut(uint256 bI, uint256 wI, uint256 pS, uint256 tW, uint256 pAo, uint256 swapFee)
        internal
        pure
        returns (JoinSteps memory s)
    {
        s.normalizedWeight = bdiv(wI, tW); // :167
        uint256 newPoolSupply = badd(pS, pAo); // :168
        s.poolRatio = bdiv(newPoolSupply, pS); // :169
        s.boo = bdiv(BONE, s.normalizedWeight); // :172
        s.tokenInRatio = bpow(s.poolRatio, s.boo); // :173
        s.newTokenBalanceIn = bmul(s.tokenInRatio, bI); // :174
        s.tokenAmountInAfterFee = bsub(s.newTokenBalanceIn, bI); // :175
        s.zar = bmul(bsub(BONE, s.normalizedWeight), swapFee); // :179
        s.tokenAmountIn = bdiv(s.tokenAmountInAfterFee, bsub(BONE, s.zar)); // :180
    }

    struct ExitSteps {
        uint256 normalizedWeight;
        uint256 poolRatio;
        uint256 boo;
        uint256 tokenOutRatio; // 18-decimal: (1 - pAi/pS)^(tW/wO)
        uint256 newTokenBalanceOut; // token units: bmul(tokenOutRatio, bO), half up to the nearest unit
        uint256 tokenAmountOutBeforeSwapFee;
        uint256 zaz;
        uint256 tokenAmountOut;
    }

    // BMath.sol:195-224
    function calcSingleOutGivenPoolIn(uint256 bO, uint256 wO, uint256 pS, uint256 tW, uint256 pAi, uint256 swapFee)
        internal
        pure
        returns (ExitSteps memory s)
    {
        s.normalizedWeight = bdiv(wO, tW); // :206
        uint256 poolAmountInAfterExitFee = bmul(pAi, bsub(BONE, EXIT_FEE)); // :209
        uint256 newPoolSupply = bsub(pS, poolAmountInAfterExitFee); // :210
        s.poolRatio = bdiv(newPoolSupply, pS); // :211
        s.boo = bdiv(BONE, s.normalizedWeight); // :214
        s.tokenOutRatio = bpow(s.poolRatio, s.boo); // :214
        s.newTokenBalanceOut = bmul(s.tokenOutRatio, bO); // :215
        s.tokenAmountOutBeforeSwapFee = bsub(bO, s.newTokenBalanceOut); // :217
        s.zaz = bmul(bsub(BONE, s.normalizedWeight), swapFee); // :221
        s.tokenAmountOut = bmul(s.tokenAmountOutBeforeSwapFee, bsub(BONE, s.zaz)); // :222
    }
}

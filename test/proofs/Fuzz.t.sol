// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import "forge-std/Test.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP256Lib} from "../../contracts/src/fp256/FP256Lib.sol";
import {Kernels} from "./Kernels.sol";
import {Ref127} from "./Ref127.sol";
import {Ref256} from "./Ref256.sol";
import {Wide} from "./Wide.sol";

/// @title LongDiv
/// @notice Schoolbook references for what the solver cannot close: the floor
///         quotient of a 512-bit numerator by a word, and the integer square
///         root of a 512-bit number, both bit by bit with exact comparisons.
library LongDiv {
    /// floor((nh 2^256 + nl) / d) for d > 0 and nh < d (so the quotient is a word).
    function div(uint256 nh, uint256 nl, uint256 d) internal pure returns (uint256 q) {
        require(d != 0 && nh < d);
        uint256 r = nh; // the running remainder, always < d
        for (uint256 i = 256; i > 0; i--) {
            // r 2 + next bit, which may be 2^256 + something: compare without overflow
            bool carry = r >> 255 == 1;
            r = (r << 1) | ((nl >> (i - 1)) & 1);
            q <<= 1;
            if (carry || r >= d) {
                unchecked {
                    r -= d;
                }
                q |= 1;
            }
        }
    }

    /// floor(sqrt(nh 2^256 + nl)), bit by bit: y + 2^i is kept when its exact square fits.
    function isqrt(uint256 nh, uint256 nl) internal pure returns (uint256 y) {
        for (uint256 i = 256; i > 0; i--) {
            uint256 c = y | (uint256(1) << (i - 1));
            (uint256 sh, uint256 sl) = Wide.umul(c, c);
            if (!Wide.ult(nh, nl, sh, sl)) y = c;
        }
    }
}

contract Lib127 {
    function sqrt(int256 x) external pure returns (int256) { return FP127Lib.sqrt(x); }
}

contract Lib256 {
    function sqrt(int256 x) external pure returns (int256) { return FP256Lib.sqrt(x); }
}

/// @title FuzzProofs
/// @notice The fuzzed half of docs/proofs.md: the division kernels the proofs
///         take as lemmas (K127, K256) against a long division, and both
///         square roots against exact integer roots. Inputs are spread over
///         bit lengths, so short and long operands are as likely as random words.
contract FuzzProofs is Test {
    Lib127 internal l127;
    Lib256 internal l256;

    function setUp() public {
        l127 = new Lib127();
        l256 = new Lib256();
    }

    /// A word with a random bit length: x's top (seed % 257) bits cleared.
    function spread(uint256 x, uint256 seed) internal pure returns (uint256) {
        uint256 k = seed % 257;
        return k == 256 ? 0 : x >> k;
    }

    /// K127: Kernels.divq(a, b) = floor(a 2^128 / b) for b > 0, a >> 128 < b, a >> 128 > 0.
    function testFuzz_K127(uint256 a, uint256 b, uint256 sa, uint256 sb) public pure {
        b = spread(b, sb);
        if (b < 2) b = 2;
        // a's high half in [1, min(b, 2^128) - 1], its low half spread
        uint256 cap = b - 1 < type(uint128).max ? b - 1 : type(uint128).max;
        uint256 hi = 1 + spread(a >> 128, sa) % cap;
        a = (hi << 128) | (spread(a, sa >> 9) & type(uint128).max);
        assertEq(Kernels.divq(a, b), LongDiv.div(a >> 128, a << 128, b));
    }

    /// K256: Kernels.divh(a, b) = floor(a 2^255 / b) for b > 0, a < 2 b.
    function testFuzz_K256(uint256 a, uint256 b, uint256 sa, uint256 sb) public pure {
        a = spread(a, sa);
        b = spread(b, sb);
        vm.assume(b != 0 && a / 2 < b); // a < 2 b
        assertEq(Kernels.divh(a, b), LongDiv.div(a >> 1, a << 255, b));
    }

    /// K256 where FP256 uses it: two significands in [2^236, 2^237).
    function testFuzz_K256_significands(uint256 a, uint256 b) public pure {
        a = (a >> 20) | (uint256(1) << 236);
        b = (b >> 20) | (uint256(1) << 236);
        a &= (uint256(1) << 237) - 1;
        b &= (uint256(1) << 237) - 1;
        assertEq(Kernels.divh(a, b), LongDiv.div(a >> 1, a << 255, b));
    }

    /// FP127 sqrt: r = floor(sqrt(x 2^128)), by the exact squares (Ref127.isSqrt).
    function testFuzz_fp127_sqrt(uint256 x, uint256 sx) public view {
        int256 v = int256(spread(x, sx) >> 1);
        int256 r = l127.sqrt(v);
        assertTrue(Ref127.isSqrt(v, r), "sqrt is not the floor of the root");
    }

    /// Regression for #159: where x 2^128 + 1 is a perfect square (s + 1)^2 the
    /// Huff's sqrt (kept bit for bit until #159) returned s + 1; it now returns
    /// the floor s: x = 2^126 k^2 + k, k = 1..4.
    function test_fp127_sqrt_regression_159() public view {
        for (uint256 k = 1; k <= 4; k++) {
            int256 x = int256((uint256(1) << 126) * k * k + k);
            int256 r = l127.sqrt(x);
            assertEq(r, int256((uint256(1) << 127) * k));
            assertTrue(Ref127.isSqrt(x, r));
        }
    }

    /// Regression for #159: a b / 2^128 = -2^255 - (2^127 + 1) / 2^128 has the
    /// ceiling -2^255, which fits; mulUp returns it (it reverted Overflow).
    function test_fp127_mulUp_regression_159() public view {
        int256 a = -int256(0x7fffffffffffffffffffffffffffffff80000000000000000000000000000001);
        int256 b = int256(uint256(1 << 128) + 1);
        (bytes4 se, int256 sr) = Ref127.mulUp(a, b);
        assertEq(se, bytes4(0));
        assertEq(sr, type(int256).min);
        assertEq(this.mulUp127(a, b), type(int256).min);
    }

    function mulUp127(int256 a, int256 b) external pure returns (int256) {
        return FP127Lib.mulUp(a, b);
    }

    /// FP127 sqrt below zero: OutOfRange.
    function testFuzz_fp127_sqrt_negative(int256 x) public {
        vm.assume(x < 0);
        vm.expectRevert(FP127Lib.OutOfRange.selector);
        l127.sqrt(x);
    }

    /// The reference square root of an FP256 word: the exact integer root of
    /// the significand scaled to an even exponent and 479+ bits, rounded once
    /// to nearest with the root's remainder as the sticky part.
    function refSqrt256(int256 x) internal pure returns (bytes4, int256) {
        Ref256.Num memory n = Ref256.unpack(x);
        if (!n.valid || n.s == 1) return (Ref256.OUTOFRANGE, 0);
        if (n.m == 0) return (0, 0);
        int256 u = Ref256.ulp(n.e);
        uint256 m = n.m;
        if (u % 2 != 0) {
            m <<= 1;
            u -= 1;
        }
        // N = m 2^242 < 2^480, sqrt(x) = sqrt(N) 2^((u - 242) / 2)
        uint256 nh = m >> 14;
        uint256 nl = m << 242;
        uint256 y = LongDiv.isqrt(nh, nl);
        (uint256 sh, uint256 sl) = Wide.umul(y, y);
        bool sticky = sh != nh || sl != nl;
        return Ref256.toFloat(0, 0, y, sticky, (u - 242) / 2, Ref256.NEAREST);
    }

    function checkSqrt256(int256 x) internal view {
        (bytes4 se, int256 sr) = refSqrt256(x);
        try l256.sqrt(x) returns (int256 r) {
            assertEq(se, bytes4(0), "sqrt returned where the spec reverts");
            assertEq(r, sr, "sqrt is not the correctly rounded root");
        } catch (bytes memory err) {
            assertEq(bytes4(err), se, "sqrt reverted differently");
        }
    }

    /// FP256 sqrt on random words: every exponent, both signs, non-numbers.
    function testFuzz_fp256_sqrt(int256 x) public view {
        checkSqrt256(x);
    }

    /// FP256 sqrt next to exact squares, where a root lies near a rounding
    /// boundary: (y^2 + d) as a number, y up to 118 bits, d in [-2, 2].
    function testFuzz_fp256_sqrt_near_squares(uint256 y, uint256 sy, int8 d) public view {
        y = spread(y >> 138, sy) | 1;
        (, uint256 sq) = Wide.umul(y, y);
        int256 dd = int256(d) % 3;
        uint256 v = dd < 0 && sq < uint256(-dd) ? sq : uint256(int256(sq) + dd);
        checkSqrt256(FP256Lib.fromUint(v));
    }
}

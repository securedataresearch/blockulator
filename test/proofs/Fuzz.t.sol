// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import "forge-std/Test.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import {BL19Lib} from "../../contracts/src/bl19/BL19Lib.sol";
import {Kernels} from "./Kernels.sol";
import {Ref127} from "./Ref127.sol";
import {Ref19} from "./Ref19.sol";
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
    function sqrt(int256 x) external pure returns (int256) { return BL127Lib.sqrt(x); }
    function gavg(int256 a, int256 b) external pure returns (int256) { return BL127Lib.gavg(a, b); }
    function hypot(int256 a, int256 b) external pure returns (int256) { return BL127Lib.hypot(a, b); }
}

contract Lib19 {
    function sqrt(int256 x) external pure returns (int256) { return BL19Lib.sqrt(x); }
    function add(int256 a, int256 b) external pure returns (int256) { return BL19Lib.add(a, b); }
    function sub(int256 a, int256 b) external pure returns (int256) { return BL19Lib.sub(a, b); }
    function toFixed18(int256 x, uint256 mode) external pure returns (int256) {
        if (mode == 0) return BL19Lib.toFixed18(x);
        if (mode == 1) return BL19Lib.toFixed18Down(x);
        return BL19Lib.toFixed18Up(x);
    }
}

/// @title FuzzProofs
/// @notice The fuzzed half of docs/proofs.md: the division kernels the proofs
///         take as lemmas (K127, K19) against a long division, and both
///         square roots, and BL127's gavg and hypot, against exact integer
///         roots. Inputs are spread over
///         bit lengths, so short and long operands are as likely as random words.
contract FuzzProofs is Test {
    Lib127 internal l127;
    Lib19 internal l19;

    function setUp() public {
        l127 = new Lib127();
        l19 = new Lib19();
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

    /// K19: Kernels.divh(a, b) = floor(a 2^255 / b) for b > 0, a < 2 b.
    function testFuzz_K19(uint256 a, uint256 b, uint256 sa, uint256 sb) public pure {
        b = spread(b, sb);
        if (b == 0) b = 1;
        // a < 2 b by construction (an assume rejected most inputs and stopped a 50,000-run fuzz)
        a = spread(a, sa);
        if (b <= type(uint256).max / 2) a %= 2 * b;
        assertEq(Kernels.divh(a, b), LongDiv.div(a >> 1, a << 255, b));
    }

    /// K19 where BL19 uses it: two significands in [2^236, 2^237).
    function testFuzz_K19_significands(uint256 a, uint256 b) public pure {
        a = (a >> 20) | (uint256(1) << 236);
        b = (b >> 20) | (uint256(1) << 236);
        a &= (uint256(1) << 237) - 1;
        b &= (uint256(1) << 237) - 1;
        assertEq(Kernels.divh(a, b), LongDiv.div(a >> 1, a << 255, b));
    }

    /// BL127 sqrt: r = floor(sqrt(x 2^128)), by the exact squares (Ref127.isSqrt).
    function testFuzz_bl127_sqrt(uint256 x, uint256 sx) public view {
        int256 v = int256(spread(x, sx) >> 1);
        int256 r = l127.sqrt(v);
        assertTrue(Ref127.isSqrt(v, r), "sqrt is not the floor of the root");
    }

    /// Regression for #159: where x 2^128 + 1 is a perfect square (s + 1)^2 the
    /// Huff's sqrt (kept bit for bit until #159) returned s + 1; it now returns
    /// the floor s: x = 2^126 k^2 + k, k = 1..4.
    function test_bl127_sqrt_regression_159() public view {
        for (uint256 k = 1; k <= 4; k++) {
            int256 x = int256((uint256(1) << 126) * k * k + k);
            int256 r = l127.sqrt(x);
            assertEq(r, int256((uint256(1) << 127) * k));
            assertTrue(Ref127.isSqrt(x, r));
        }
    }

    /// Regression for #159: a b / 2^128 = -2^255 - (2^127 + 1) / 2^128 has the
    /// ceiling -2^255, which fits; mulUp returns it (it reverted Overflow).
    function test_bl127_mulUp_regression_159() public view {
        int256 a = -int256(0x7fffffffffffffffffffffffffffffff80000000000000000000000000000001);
        int256 b = int256(uint256(1 << 128) + 1);
        (bytes4 se, int256 sr) = Ref127.mulUp(a, b);
        assertEq(se, bytes4(0));
        assertEq(sr, type(int256).min);
        assertEq(this.mulUp127(a, b), type(int256).min);
    }

    function mulUp127(int256 a, int256 b) external pure returns (int256) {
        return BL127Lib.mulUp(a, b);
    }

    /// BL127 sqrt below zero: OutOfRange.
    function testFuzz_bl127_sqrt_negative(int256 x) public {
        vm.assume(x < 0);
        vm.expectRevert(BL127Lib.OutOfRange.selector);
        l127.sqrt(x);
    }

    /// The nearest integer to sqrt(nh 2^256 + nl), from the bit-by-bit root
    /// y: one up iff N - y^2 > y (no ties: N = y^2 + y + 1/4 is no integer);
    /// Overflow past 2^255 - 1. gavg's and hypot's spec on the raw words.
    function refRoot(uint256 nh, uint256 nl) internal pure returns (bytes4, int256) {
        uint256 y = LongDiv.isqrt(nh, nl);
        (uint256 ph, uint256 pl) = Wide.umul(y, y + 1);
        if (Wide.ult(ph, pl, nh, nl)) y += 1;
        if (y >= uint256(1) << 255) return (Ref127.OVERFLOW, 0);
        return (0, int256(y));
    }

    function abs127(int256 x) internal pure returns (uint256) {
        unchecked { return x < 0 ? uint256(-x) : uint256(x); }
    }

    function check127(bool returned, int256 r, bytes memory err, bytes4 se, int256 sr, string memory op) internal pure {
        if (returned) {
            assertEq(se, bytes4(0), string.concat(op, " returned where the spec reverts"));
            assertEq(r, sr, string.concat(op, " is not the nearest root"));
        } else {
            assertEq(bytes4(err), se, string.concat(op, " reverted differently"));
        }
    }

    /// BL127 gavg (3.0): the nearest root of the exact product |a| |b| of the
    /// raw words; 0 when either is zero; OutOfRange for opposite signs.
    function checkGavg127(int256 a, int256 b) internal view {
        bytes4 se;
        int256 sr;
        if (a != 0 && b != 0) {
            if ((a < 0) != (b < 0)) se = Ref127.OUTOFRANGE;
            else {
                (uint256 nh, uint256 nl) = Wide.umul(abs127(a), abs127(b));
                (se, sr) = refRoot(nh, nl);
            }
        }
        try l127.gavg(a, b) returns (int256 r) { check127(true, r, "", se, sr, "gavg"); }
        catch (bytes memory err) { check127(false, 0, err, se, sr, "gavg"); }
    }

    /// BL127 hypot (3.0): the nearest root of the exact A^2 + B^2.
    function checkHypot127(int256 a, int256 b) internal view {
        (uint256 ah, uint256 al) = Wide.umul(abs127(a), abs127(a));
        (uint256 bh, uint256 bl) = Wide.umul(abs127(b), abs127(b));
        unchecked {
            al += bl;
            ah += bh + (al < bl ? 1 : 0);
        }
        (bytes4 se, int256 sr) = refRoot(ah, al);
        try l127.hypot(a, b) returns (int256 r) { check127(true, r, "", se, sr, "hypot"); }
        catch (bytes memory err) { check127(false, 0, err, se, sr, "hypot"); }
    }

    /// A word with a random bit length and sign.
    function spreadSigned(uint256 x, uint256 seed) internal pure returns (int256 v) {
        v = int256(spread(x, seed) >> 1);
        if ((seed >> 9) & 1 == 1) v = -v;
        if ((seed >> 10) & 63 == 0) v = type(int256).min;
    }

    function testFuzz_bl127_gavg(uint256 a, uint256 b, uint256 sa, uint256 sb) public view {
        checkGavg127(spreadSigned(a, sa), spreadSigned(b, sb));
    }

    function testFuzz_bl127_hypot(uint256 a, uint256 b, uint256 sa, uint256 sb) public view {
        checkHypot127(spreadSigned(a, sa), spreadSigned(b, sb));
    }

    /// Next to the midpoints: gavg(x, x + d) has N = x^2 + d x, whose root
    /// is just under x + 1/2 for d = 1 (N = x (x + 1), rounds down) and just
    /// over it for d = 2; hypot(x, small) sits just above x.
    function testFuzz_bl127_roots_near_mid(uint256 x, uint256 sx, uint8 d) public view {
        int256 v = int256(spread(x, sx) >> 2);
        int256 dd = int256(uint256(d % 5)) - 2;
        checkGavg127(v, v + dd);
        checkGavg127(-v, -v - dd);
        checkHypot127(v, dd);
        checkHypot127(v, int256(spread(x >> 7, sx >> 3) >> 130));
    }

    /// The edges: zero, one ULP, the extreme words, and the old floors' worst case.
    function test_bl127_roots_edges() public view {
        int256[8] memory w = [int256(0), 1, -1, type(int256).max, type(int256).min, type(int256).min + 1,
            int256(1) << 50, int256(1) << 68];
        for (uint256 i; i < w.length; i++) {
            for (uint256 j; j < w.length; j++) {
                checkGavg127(w[i], w[j]);
                checkHypot127(w[i], w[j]);
            }
        }
        assertEq(l127.gavg(int256(1) << 50, int256(1) << 68), int256(1) << 59);
    }

    /// The reference square root of an BL19 word: the exact integer root of
    /// the significand scaled to an even exponent and 479+ bits, rounded once
    /// to nearest with the root's remainder as the sticky part.
    function refSqrt19(int256 x) internal pure returns (bytes4, int256) {
        Ref19.Num memory n = Ref19.unpack(x);
        if (!n.valid || n.s == 1) return (Ref19.OUTOFRANGE, 0);
        if (n.m == 0) return (0, 0);
        int256 u = Ref19.ulp(n.e);
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
        return Ref19.toFloat(0, 0, y, sticky, (u - 242) / 2, Ref19.NEAREST);
    }

    function checkSqrt19(int256 x) internal view {
        (bytes4 se, int256 sr) = refSqrt19(x);
        try l19.sqrt(x) returns (int256 r) {
            assertEq(se, bytes4(0), "sqrt returned where the spec reverts");
            assertEq(r, sr, "sqrt is not the correctly rounded root");
        } catch (bytes memory err) {
            assertEq(bytes4(err), se, "sqrt reverted differently");
        }
    }

    /// BL19 sqrt on random words: every exponent, both signs, non-numbers.
    function testFuzz_bl19_sqrt(int256 x) public view {
        checkSqrt19(x);
    }

    /// BL19 sqrt next to exact squares, where a root lies near a rounding
    /// boundary: (y^2 + d) as a number, y up to 118 bits, d in [-2, 2].
    function testFuzz_bl19_sqrt_near_squares(uint256 y, uint256 sy, int8 d) public view {
        y = spread(y >> 138, sy) | 1;
        (, uint256 sq) = Wide.umul(y, y);
        int256 dd = int256(d) % 3;
        uint256 v = dd < 0 && sq < uint256(-dd) ? sq : uint256(int256(sq) + dd);
        checkSqrt19(BL19Lib.fromUint(v));
    }

    /// The BL19 ops whose Halmos checks run out of time (add, sub, the three
    /// toFixed18 roundings), against the same exact specs (Ref19): the word,
    /// or the same revert. Operands share nearby exponents so that every
    /// alignment, cancellation and rounding path is reached, not only the
    /// far-apart case random words give.
    function nearExp(int256 a, uint256 b, uint256 d) internal pure returns (int256) {
        uint256 ea = (uint256(a) >> 236) & 0x7ffff;
        if (ea == 0) ea = 1;
        uint256 eb = ea + (d % 600);
        eb = eb > 300 ? eb - 300 : ea;
        if (eb == 0 || eb > 0x7ffff) eb = ea;
        return int256((b & ~(uint256(0x7ffff) << 236)) | (eb << 236));
    }

    function checkWord19(bool returned, int256 r, bytes memory err, bytes4 se, int256 sr, string memory op) internal pure {
        if (returned) {
            assertEq(se, bytes4(0), string.concat(op, " returned where the spec reverts"));
            assertEq(r, sr, string.concat(op, " is not the spec's word"));
        } else {
            assertEq(bytes4(err), se, string.concat(op, " reverted differently"));
        }
    }

    function testFuzz_bl19_add(int256 a, uint256 bb, uint256 d, bool flip) public view {
        int256 b = nearExp(a, bb, d);
        if (flip) b = int256(uint256(b) ^ (uint256(1) << 255));
        (bytes4 se, int256 sr) = Ref19.add(a, b);
        try l19.add(a, b) returns (int256 r) { checkWord19(true, r, "", se, sr, "add"); }
        catch (bytes memory err) { checkWord19(false, 0, err, se, sr, "add"); }
    }

    function testFuzz_bl19_sub(int256 a, uint256 bb, uint256 d, bool flip) public view {
        int256 b = nearExp(a, bb, d);
        if (flip) b = int256(uint256(b) ^ (uint256(1) << 255));
        (bytes4 se, int256 sr) = Ref19.sub(a, b);
        try l19.sub(a, b) returns (int256 r) { checkWord19(true, r, "", se, sr, "sub"); }
        catch (bytes memory err) { checkWord19(false, 0, err, se, sr, "sub"); }
    }

    /// toFixed18, Down and Up, with exponents across the whole range where the
    /// result is a nonzero integer up to int256 and a little beyond.
    function testFuzz_bl19_toFixed18(int256 x, uint256 e, uint256 mode) public view {
        mode = mode % 3;
        x = int256((uint256(x) & ~(uint256(0x7ffff) << 236)) | ((0x400eb - 300 + e % 310) << 236));
        (bytes4 se, int256 sr) = Ref19.toFixed18(x, mode);
        try l19.toFixed18(x, mode) returns (int256 r) { checkWord19(true, r, "", se, sr, "toFixed18"); }
        catch (bytes memory err) { checkWord19(false, 0, err, se, sr, "toFixed18"); }
    }
}

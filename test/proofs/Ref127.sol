// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Wide} from "./Wide.sol";
import {Kernels} from "./Kernels.sol";

/// @title Ref127
/// @notice Reference specifications of BL127's core ops, written from the
///         documented semantics (contracts/src/bl127/README.md and each op's
///         notice), not from the library's code. A value is raw / 2^128.
///
///         Each spec returns (err, r): err is 0 and r the result, or err is the
///         4-byte error the op must revert with. Every result is the exact
///         value rounded in the op's direction, computed on exact integers
///         (Wide) and range-checked once at the end:
///           mul, mulDown   floor(a b / 2^128)
///           mulUp          ceil(a b / 2^128)
///           div, inv       trunc(a 2^128 / b), trunc(2^256 / x)
///           divDown, divUp floor, ceil of a 2^128 / b
///           sqrt           floor(sqrt(x 2^128))
///           floor, ceil    the multiple of 2^128 at or below / above x
///           round          floor(x + 2^127): halves up
///           toFixed18(Down), toFixed18Up  floor, ceil of x 10^18 / 2^128
///           fromFixed18    trunc(x 2^128 / 10^18)
library Ref127 {
    bytes4 internal constant OVERFLOW = 0x35278d12;
    bytes4 internal constant DIVZERO = 0x23d359a3;
    bytes4 internal constant OUTOFRANGE = 0x7db3aba7;

    int256 internal constant MAX = type(int256).max;
    int256 internal constant MIN = type(int256).min;
    uint256 internal constant LOW128 = (uint256(1) << 128) - 1;

    /// The exact a + b, Overflow outside int256.
    function add(int256 a, int256 b) internal pure returns (bytes4, int256) {
        if ((b > 0 && a > MAX - b) || (b < 0 && a < MIN - b)) return (OVERFLOW, 0);
        unchecked {
            return (0, a + b);
        }
    }

    /// The exact a - b, Overflow outside int256.
    function sub(int256 a, int256 b) internal pure returns (bytes4, int256) {
        if ((b < 0 && a > MAX + b) || (b > 0 && a < MIN + b)) return (OVERFLOW, 0);
        unchecked {
            return (0, a - b);
        }
    }

    /// A signed pair as the result word, Overflow when it does not fit.
    function word(int256 hi, uint256 lo) internal pure returns (bytes4, int256) {
        (bool fits, int256 r) = Wide.toInt(hi, lo);
        if (!fits) return (OVERFLOW, 0);
        return (0, r);
    }

    /// floor(a b / 2^128).
    function mulDown(int256 a, int256 b) internal pure returns (bytes4, int256) {
        (int256 ph, uint256 pl) = Wide.smul(a, b);
        (int256 fh, uint256 fl) = Wide.sshr(ph, pl, 128);
        return word(fh, fl);
    }

    /// ceil(a b / 2^128): the floor, plus one when a b is not a multiple of 2^128.
    function mulUp(int256 a, int256 b) internal pure returns (bytes4, int256) {
        (int256 ph, uint256 pl) = Wide.smul(a, b);
        (int256 fh, uint256 fl) = Wide.sshr(ph, pl, 128);
        if (pl & LOW128 != 0) (fh, fl) = Wide.sadd(fh, fl, 1);
        return word(fh, fl);
    }

    /// The quotient of a 2^128 by b on magnitudes: Q = floor(|a| 2^128 / |b|)
    /// as a pair (Q >= 2^256 is flagged, it fits no result), the remainder's
    /// nonzero-ness, and the sign of the exact quotient.
    function quot(int256 a, int256 b) internal pure returns (bool big, uint256 q, bool inexact, bool neg) {
        uint256 ua = Wide.uabs(a);
        uint256 ub = Wide.uabs(b);
        neg = (a < 0) != (b < 0);
        // N = ua 2^128 = (ua >> 128) 2^256 + (ua << 128). Q < 2^256 iff ua >> 128 < ub.
        uint256 nh = ua >> 128;
        if (nh >= ub) return (true, 0, false, neg);
        // the EVM's DIV is the floor quotient of words; above a word, the kernel
        // (Kernels.divq, lemma K127)
        assert(nh < ub); // the kernel's precondition, K127
        q = nh == 0 ? (ua << 128) / ub : Kernels.divq(ua, ub);
        // the EVM's MULMOD is the exact remainder of ua 2^128 by ub
        inexact = mulmod(ua, 1 << 128, ub) != 0;
    }

    /// The signed result -q or q for a magnitude q < 2^256, plus a step of
    /// one toward minus (dn) or plus (up) infinity.
    function signed(uint256 q, bool neg, bool dn, bool up) internal pure returns (bytes4, int256) {
        // the signed pair (0, q) or its negation
        int256 h = 0;
        uint256 l = q;
        if (neg && q != 0) {
            h = -1;
            unchecked {
                l = 0 - q;
            }
        }
        if (up) (h, l) = Wide.sadd(h, l, 1);
        if (dn) {
            unchecked {
                if (l == 0) h -= 1;
                l -= 1;
            }
        }
        return word(h, l);
    }

    /// trunc(a 2^128 / b).
    function div(int256 a, int256 b) internal pure returns (bytes4, int256) {
        if (b == 0) return (DIVZERO, 0);
        (bool big, uint256 q,, bool neg) = quot(a, b);
        if (big) return (OVERFLOW, 0);
        return signed(q, neg, false, false);
    }

    /// floor(a 2^128 / b): trunc, one lower when negative and inexact.
    function divDown(int256 a, int256 b) internal pure returns (bytes4, int256) {
        if (b == 0) return (DIVZERO, 0);
        (bool big, uint256 q, bool inexact, bool neg) = quot(a, b);
        if (big) return (OVERFLOW, 0);
        return signed(q, neg, neg && inexact, false);
    }

    /// ceil(a 2^128 / b): trunc, one higher when positive and inexact.
    function divUp(int256 a, int256 b) internal pure returns (bytes4, int256) {
        if (b == 0) return (DIVZERO, 0);
        (bool big, uint256 q, bool inexact, bool neg) = quot(a, b);
        if (big) return (OVERFLOW, 0);
        return signed(q, neg, false, !neg && inexact);
    }

    /// trunc(2^256 / x) = 1/x in the format.
    function inv(int256 x) internal pure returns (bytes4, int256) {
        if (x == 0) return (DIVZERO, 0);
        uint256 u = Wide.uabs(x);
        if (u == 1) return (OVERFLOW, 0); // 2^256
        // floor(2^256 / u) = floor((2^256 - u) / u) + 1 (L4), the EVM's DIV
        uint256 q;
        unchecked {
            q = (0 - u) / u + 1;
        }
        return signed(q, x < 0, false, false);
    }

    /// The multiple of 2^128 at or below x: 2^128 floor(x / 2^128).
    function floor(int256 x) internal pure returns (bytes4, int256) {
        return (0, (x >> 128) << 128); // >> on int256 is floor division by 2^128
    }

    /// The multiple of 2^128 at or above x.
    function ceil(int256 x) internal pure returns (bytes4, int256) {
        int256 q = x >> 128;
        if (uint256(x) & LOW128 != 0) q += 1;
        if (q >= int256(1) << 127) return (OVERFLOW, 0);
        return (0, q << 128);
    }

    /// floor(x + 1/2): the nearest multiple of 2^128, halves up.
    function round(int256 x) internal pure returns (bytes4, int256) {
        // x + 2^127 as a signed pair, then floor by 2^128
        (int256 h, uint256 l) = Wide.sadd(x < 0 ? int256(-1) : int256(0), uint256(x), 1 << 127);
        (h, l) = Wide.sshr(h, l, 128);
        (bool fits, int256 q) = Wide.toInt(h, l);
        if (!fits || q >= int256(1) << 127 || q < -(int256(1) << 127)) return (OVERFLOW, 0);
        return (0, q << 128);
    }

    /// x 10^18 as an exact signed pair: x = xh 2^128 + xl with xl in [0, 2^128),
    /// so x 10^18 = (xh 10^18) 2^128 + xl 10^18, both terms exact in a word.
    function times1e18(int256 x) internal pure returns (int256 h, uint256 l) {
        int256 xh = x >> 128;
        uint256 xl = uint256(x) & LOW128;
        unchecked {
            int256 t = xh * 1e18; // |xh| <= 2^127: under 2^188, exact
            uint256 u = xl * 1e18; // under 2^188, exact
            // (t 2^128) + u
            h = t >> 128;
            l = uint256(t) << 128;
            uint256 s = l + u;
            if (s < l) h += 1;
            l = s;
        }
    }

    /// floor(x 10^18 / 2^128).
    function toFixed18Down(int256 x) internal pure returns (bytes4, int256) {
        (int256 h, uint256 l) = times1e18(x);
        (h, l) = Wide.sshr(h, l, 128);
        return word(h, l);
    }

    /// ceil(x 10^18 / 2^128).
    function toFixed18Up(int256 x) internal pure returns (bytes4, int256) {
        (int256 h, uint256 l) = times1e18(x);
        bool inexact = l & LOW128 != 0;
        (h, l) = Wide.sshr(h, l, 128);
        if (inexact) (h, l) = Wide.sadd(h, l, 1);
        return word(h, l);
    }

    /// trunc(x 2^128 / 10^18), OutOfRange where x 2^128 leaves int256.
    function fromFixed18(int256 x) internal pure returns (bytes4, int256) {
        if (x < -(int256(1) << 127) || x >= int256(1) << 127) return (OUTOFRANGE, 0);
        return (0, (x << 128) / 1e18); // Solidity's int division truncates (SDIV)
    }

    /// The square root's specification as a test of a candidate r:
    /// r = floor(sqrt(x 2^128)) iff r^2 <= x 2^128 < (r + 1)^2. Exact squares.
    function isSqrt(int256 x, int256 r) internal pure returns (bool) {
        if (x < 0 || r < 0) return false;
        uint256 nh = uint256(x) >> 128;
        uint256 nl = uint256(x) << 128;
        (uint256 sh, uint256 sl) = Wide.umul(uint256(r), uint256(r));
        (uint256 th, uint256 tl) = Wide.umul(uint256(r) + 1, uint256(r) + 1);
        return !Wide.ult(nh, nl, sh, sl) && Wide.ult(nh, nl, th, tl);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Wide} from "./Wide.sol";
import {Kernels} from "./Kernels.sol";

/// @title Ref256
/// @notice Reference specifications of FP256's core ops, written from the
///         format and the documented semantics (contracts/src/fp256/README.md
///         and each op's notice), not from the library's code.
///
///         The format. A word is sign s (bit 255), biased exponent e (bits
///         254..236) and fraction f (235..0). Zero is the all-zero word; any
///         other word with e = 0 is not a number. Otherwise the significand is
///         m = 2^236 + f and the value is (-1)^s m 2^(e - BIAS - 236).
///
///         The rounding. `toFloat` takes an exact value (-1)^s (N + d) 2^k,
///         N an integer of up to 512 bits and d in [0, 1) with sticky = (d > 0),
///         and returns the word for it:
///           * L = bit length of N, by comparisons (Wide-free binary search);
///           * at L <= 237 the value is exact: R = N 2^(237 - L);
///           * above, R = floor(N / 2^t), t = L - 237, and the rest
///             rem = N mod 2^t decides: to nearest, R + 1 when
///             rem + d >= 2^(t - 1) (ties away from zero on the magnitude);
///             directed, R + 1 when rem + d > 0 and the direction points away
///             from zero. With 2^(t - 1) an integer, rem + d >= 2^(t - 1) iff
///             rem >= 2^(t - 1), so d matters only to the directed modes;
///           * R = 2^237 after the increment is 2^236 one binade up;
///           * the biased exponent E = k + t + BIAS + 236. Above EMAX:
///             Overflow. Below 1 (underflow): zero, or toward plus or minus
///             infinity away from zero, the smallest number with the sign.
///         `toInt` rounds (-1)^s N / 2^t to an integer the same three ways.
library Ref256 {
    bytes4 internal constant OVERFLOW = 0x35278d12;
    bytes4 internal constant DIVZERO = 0x23d359a3;
    bytes4 internal constant OUTOFRANGE = 0x7db3aba7;

    int256 internal constant BIAS = 262143;
    int256 internal constant EMAX = 524287;
    uint256 internal constant HID = 1 << 236;
    uint256 internal constant TOP = 1 << 237;

    uint256 internal constant NEAREST = 0;
    uint256 internal constant DOWN = 1; // toward minus infinity
    uint256 internal constant UP = 2; // toward plus infinity

    /// A word's fields: valid is false for a word that is not a number; zero
    /// is (true, 0, 0, 0). value = (-1)^s m 2^(e - BIAS - 236).
    struct Num {
        bool valid;
        uint256 s;
        int256 e;
        uint256 m;
    }

    function unpack(int256 x) internal pure returns (Num memory n) {
        uint256 w = uint256(x);
        n.e = int256((w >> 236) & 0x7ffff);
        if (n.e == 0) {
            n.valid = w == 0;
            return n;
        }
        n.valid = true;
        n.s = w >> 255;
        n.m = (w & (HID - 1)) | HID;
    }

    /// The word for sign s, biased exponent e in [1, EMAX], significand m in [2^236, 2^237).
    function pack(uint256 s, int256 e, uint256 m) internal pure returns (int256) {
        return int256((s << 255) | (uint256(e) << 236) | (m - HID));
    }

    /// The exponent of a significand's last bit: value = (-1)^s m 2^ulp(e).
    function ulp(int256 e) internal pure returns (int256) {
        return e - BIAS - 236;
    }

    /// Whether rounding in `mode` moves a magnitude with sign s up.
    function away(uint256 s, uint256 mode) internal pure returns (bool) {
        return (mode == UP && s == 0) || (mode == DOWN && s == 1);
    }

    // ---- exact 512-bit helpers on (h, l) = h 2^256 + l ------------------------
    // Branch-free (each forked branch is a path for the solver).

    /// The bit length of (h, l): 0 for zero, else 1 + the index of the top bit,
    /// by a binary search of comparisons against powers of two.
    function bitlen(uint256 h, uint256 l) internal pure returns (uint256 n) {
        assembly {
            let big := iszero(iszero(h))
            n := shl(8, big)
            let x := xor(l, and(xor(h, l), sub(0, big))) // h if big, else l
            let c := shl(7, gt(x, 0xffffffffffffffffffffffffffffffff))
            x := shr(c, x)
            n := add(n, c)
            c := shl(6, gt(x, 0xffffffffffffffff))
            x := shr(c, x)
            n := add(n, c)
            c := shl(5, gt(x, 0xffffffff))
            x := shr(c, x)
            n := add(n, c)
            c := shl(4, gt(x, 0xffff))
            x := shr(c, x)
            n := add(n, c)
            c := shl(3, gt(x, 0xff))
            x := shr(c, x)
            n := add(n, c)
            c := shl(2, gt(x, 0xf))
            x := shr(c, x)
            n := add(n, c)
            c := shl(1, gt(x, 0x3))
            x := shr(c, x)
            n := add(n, c)
            c := gt(x, 0x1)
            x := shr(c, x)
            n := add(n, c)
            n := add(n, x) // x is now 1, or 0 for zero
        }
    }

    /// floor((h, l) / 2^t) for 0 <= t <= 511, as a word (the caller knows it fits).
    function shr512(uint256 h, uint256 l, uint256 t) internal pure returns (uint256 r) {
        assembly {
            // t < 256: h's low bits above l's high bits; t >= 256: h alone. A
            // shift by 256 or more is zero in the EVM, so the three terms cover both.
            r := or(or(shl(sub(256, t), h), shr(t, l)), shr(sub(t, 256), h))
            if iszero(t) { r := l }
        }
    }

    /// (h, l) mod 2^t for 0 <= t <= 511.
    function low512(uint256 h, uint256 l, uint256 t) internal pure returns (uint256 rh, uint256 rl) {
        assembly {
            rl := and(l, sub(shl(t, 1), 1)) // the mask is all ones from t = 256
            rh := and(and(h, sub(shl(sub(t, 256), 1), 1)), sub(0, iszero(lt(t, 256))))
        }
    }

    /// 2^j as a pair, 0 <= j <= 511.
    function pow2(uint256 j) internal pure returns (uint256 ph, uint256 pl) {
        assembly {
            pl := shl(j, 1)
            ph := and(shl(sub(j, 256), 1), sub(0, iszero(lt(j, 256))))
        }
    }

    // ---- the two roundings ----------------------------------------------------

    /// The word for (-1)^s (N + d) 2^k, N = (nh, nl), d in [0, 1), sticky = d > 0.
    /// With sticky, N must have at least 238 bits, so that every rounding
    /// boundary is an integer.
    function toFloat(uint256 s, uint256 nh, uint256 nl, bool sticky, int256 k, uint256 mode)
        internal
        pure
        returns (bytes4, int256)
    {
        (bool zero, uint256 R, int256 t) = round237(s, nh, nl, sticky, mode);
        if (zero) return (0, 0);
        int256 E = k + t + BIAS + 236;
        if (E > EMAX) return (OVERFLOW, 0);
        if (E < 1) {
            if (mode != NEAREST && away(s, mode)) return (0, pack(s, 1, HID));
            return (0, 0);
        }
        return (0, pack(s, E, R));
    }

    /// N + d rounded to 237 bits: R in [2^236, 2^237) with N + d ~ R 2^t.
    function round237(uint256 s, uint256 nh, uint256 nl, bool sticky, uint256 mode)
        internal
        pure
        returns (bool zero, uint256 R, int256 t)
    {
        uint256 L = bitlen(nh, nl);
        if (L == 0) {
            assert(!sticky);
            return (true, 0, 0);
        }
        bool up;
        if (L <= 237) {
            assert(!sticky);
            R = nl << (237 - L); // exact
            t = int256(L) - 237;
        } else {
            assert(!sticky || L >= 238);
            uint256 tu = L - 237;
            R = shr512(nh, nl, tu);
            up = roundsUp(s, nh, nl, tu, sticky, mode);
            t = int256(tu);
        }
        if (up) {
            R += 1;
            if (R == TOP) {
                R = HID;
                t += 1;
            }
        }
    }

    /// Whether N + d, cut at 2^t (t >= 1), rounds its magnitude up: to nearest
    /// when the rest rem = N mod 2^t is at least half of 2^t; directed when
    /// anything was cut and the direction points away from zero.
    function roundsUp(uint256 s, uint256 nh, uint256 nl, uint256 t, bool sticky, uint256 mode)
        internal
        pure
        returns (bool)
    {
        (uint256 rh, uint256 rl) = low512(nh, nl, t);
        if (mode == NEAREST) {
            (uint256 hh, uint256 hl) = pow2(t - 1);
            return !Wide.ult(rh, rl, hh, hl); // rem >= half
        }
        return (rh != 0 || rl != 0 || sticky) && away(s, mode);
    }

    /// The magnitude J of (-1)^s N / 2^t rounded to an integer in `mode`
    /// (nearest: halves away from zero), N = (nh, nl) with nh < 2^255; big
    /// when J >= 2^256.
    function toInt(uint256 s, uint256 nh, uint256 nl, uint256 t, uint256 mode)
        internal
        pure
        returns (bool big, uint256 J)
    {
        bool up;
        if (t >= 512) {
            // N < 2^511 <= 2^(t - 1): no integer part, under a half
            up = mode != NEAREST && (nh != 0 || nl != 0) && away(s, mode);
        } else {
            if (t < 256 && (nh >> t) != 0) return (true, 0);
            J = shr512(nh, nl, t);
            if (t > 0) up = roundsUp(s, nh, nl, t, false, mode);
        }
        if (up) {
            if (J == type(uint256).max) return (true, 0);
            J += 1;
        }
    }

    /// The signed result (-1)^s J, Overflow outside int256.
    function signedInt(uint256 s, bool big, uint256 J) internal pure returns (bytes4, int256) {
        if (big) return (OVERFLOW, 0);
        if (s == 0) {
            if (J > uint256(type(int256).max)) return (OVERFLOW, 0);
            return (0, int256(J));
        }
        if (J > uint256(type(int256).max) + 1) return (OVERFLOW, 0);
        return (0, int256(0 - J)); // two's complement of J
    }

    // ---- the ops ----------------------------------------------------------------

    uint256 internal constant G = 270; // the sum's grid: 270 bits under the larger term's last bit

    /// a + b (flip = 0) or a - b (flip = 1), rounded to nearest.
    function addsub(int256 a, int256 b, uint256 flip) internal pure returns (bytes4, int256) {
        Num memory x = unpack(a);
        Num memory y = unpack(b);
        if (!x.valid || !y.valid) return (OUTOFRANGE, 0);
        y.s ^= flip;
        if (y.m == 0) return (0, a); // a + 0 = a, exact
        if (x.m == 0) return (0, pack(y.s, y.e, y.m)); // 0 + b, 0 - b
        // x the term of larger magnitude
        if (y.e > x.e || (y.e == x.e && y.m > x.m)) (x, y) = (y, x);
        uint256 d = uint256(x.e - y.e);
        // In units of 2^(ulp(x.e) - G): x = x.m 2^G exactly, y = y.m 2^(G - d),
        // exact for d <= G and otherwise floor(y.m / 2^(d - G)) plus a sticky part.
        (uint256 yh, uint256 yl, bool sticky) = alignY(y.m, d);
        uint256 nh;
        uint256 nl;
        unchecked {
            uint256 xh = x.m << (G - 256); // x.m 2^G < 2^507, all in the high word
            if (x.s == y.s) {
                // N + d = x + y
                nl = yl;
                nh = xh + yh;
            } else {
                // x - (y + d) = (x - y - 1) + (1 - d) when d > 0
                nl = 0 - yl;
                nh = xh - yh - (yl != 0 ? 1 : 0);
                if (sticky) {
                    if (nl == 0) nh -= 1;
                    nl -= 1;
                }
            }
        }
        return toFloat(x.s, nh, nl, sticky, ulp(x.e) - int256(G), NEAREST);
    }

    /// my 2^(G - d) as a pair when d <= G; floor(my / 2^(d - G)) and whether
    /// bits were cut when d > G.
    function alignY(uint256 my, uint256 d) internal pure returns (uint256 yh, uint256 yl, bool sticky) {
        if (d <= G) {
            uint256 sh = G - d; // my 2^sh < 2^507
            if (sh >= 256) return (my << (sh - 256), 0, false);
            if (sh == 0) return (0, my, false);
            return (my >> (256 - sh), my << sh, false);
        }
        uint256 cut = d - G;
        if (cut >= 256) return (0, 0, true); // 0 < y < 1 unit
        return (0, my >> cut, my & ((1 << cut) - 1) != 0);
    }

    function add(int256 a, int256 b) internal pure returns (bytes4, int256) {
        return addsub(a, b, 0);
    }

    function sub(int256 a, int256 b) internal pure returns (bytes4, int256) {
        return addsub(a, b, 1);
    }

    /// a b: the exact product of the significands (L1), one rounding in `mode`.
    function mul(int256 a, int256 b, uint256 mode) internal pure returns (bytes4, int256) {
        Num memory x = unpack(a);
        Num memory y = unpack(b);
        if (!x.valid || !y.valid) return (OUTOFRANGE, 0);
        if (x.m == 0 || y.m == 0) return (0, 0);
        (uint256 ph, uint256 pl) = Wide.umul(x.m, y.m);
        return toFloat(x.s ^ y.s, ph, pl, false, ulp(x.e) + ulp(y.e), mode);
    }

    /// a / b: Q = floor(ma 2^255 / mb) (K256) and the exact remainder's
    /// nonzero-ness, one rounding in `mode`.
    function div(int256 a, int256 b, uint256 mode) internal pure returns (bytes4, int256) {
        Num memory x = unpack(a);
        Num memory y = unpack(b);
        if (!x.valid || !y.valid) return (OUTOFRANGE, 0);
        if (y.m == 0) return (DIVZERO, 0);
        if (x.m == 0) return (0, 0);
        assert(x.m < 2 * y.m); // K256's precondition
        uint256 q = Kernels.divh(x.m, y.m); // ma / mb in (1/2, 2): q in (2^254, 2^256)
        bool sticky = mulmod(x.m, 1 << 255, y.m) != 0;
        // a / b = (ma 2^255 / mb) 2^(ulp(ea) - ulp(eb) - 255)
        return toFloat(x.s ^ y.s, 0, q, sticky, x.e - y.e - 255, mode);
    }

    /// 1 / x: Q = floor(2^491 / m) (K256), one rounding to nearest.
    function inv(int256 a) internal pure returns (bytes4, int256) {
        Num memory x = unpack(a);
        if (!x.valid) return (OUTOFRANGE, 0);
        if (x.m == 0) return (DIVZERO, 0);
        assert(HID < 2 * x.m); // K256's precondition
        uint256 q = Kernels.divh(HID, x.m);
        bool sticky = mulmod(HID, 1 << 255, x.m) != 0;
        // 1 / (m 2^ulp(e)) = (2^491 / m) 2^(-491 - ulp(e))
        return toFloat(x.s, 0, q, sticky, -491 - ulp(x.e), NEAREST);
    }

    /// The integral number at or below (DOWN) or above (UP) x, or nearest
    /// with halves away from zero (NEAREST): exact.
    function integral(int256 a, uint256 mode) internal pure returns (bytes4, int256) {
        Num memory x = unpack(a);
        if (!x.valid) return (OUTOFRANGE, 0);
        if (x.m == 0) return (0, 0);
        int256 u = ulp(x.e);
        if (u >= 0) return (0, a); // already an integer
        (, uint256 J) = toInt(x.s, 0, x.m, uint256(-u), mode); // J <= 2^237
        return toFloat(x.s, 0, J, false, 0, NEAREST); // exact: J has at most 238 bits, the last zero if 238
    }

    /// floor(x) (DOWN) or ceil(x) (UP) as a plain integer; unsigned (uint256,
    /// OutOfRange below zero) or signed (int256).
    function integer(int256 a, uint256 mode, bool unsigned_) internal pure returns (bytes4, int256) {
        Num memory x = unpack(a);
        if (!x.valid) return (OUTOFRANGE, 0);
        if (x.m == 0) return (0, 0);
        if (unsigned_ && x.s == 1) return (OUTOFRANGE, 0);
        int256 u = ulp(x.e);
        bool big;
        uint256 J;
        if (u >= 0) {
            // m 2^u, an integer of 237 + u bits
            if (u > 19) big = true;
            else J = x.m << uint256(u);
        } else {
            (big, J) = toInt(x.s, 0, x.m, uint256(-u), mode);
        }
        if (unsigned_) {
            if (big) return (OVERFLOW, 0);
            return (0, int256(J)); // the uint256's bits
        }
        return signedInt(x.s, big, J);
    }

    /// x 10^18 rounded to an integer in `mode`, from the exact product M 10^18 (L1).
    function toFixed18(int256 a, uint256 mode) internal pure returns (bytes4, int256) {
        Num memory x = unpack(a);
        if (!x.valid) return (OUTOFRANGE, 0);
        if (x.m == 0) return (0, 0);
        int256 u = ulp(x.e);
        if (u >= 0) return (OVERFLOW, 0); // |x| 10^18 >= 2^236 10^18 > 2^295
        (uint256 ph, uint256 pl) = Wide.umul(x.m, 1e18); // under 2^297
        (bool big, uint256 J) = toInt(x.s, ph, pl, uint256(-u), mode);
        return signedInt(x.s, big, J);
    }

    /// The uint256 x as a number, rounded in `mode`.
    function fromUint(uint256 x, uint256 mode) internal pure returns (bytes4, int256) {
        return toFloat(0, 0, x, false, 0, mode);
    }

    /// The 18-decimal integer x as a number, then divided by 10^18, each rounded
    /// to nearest (the documented two roundings; one when |x| < 2^237).
    function fromFixed18(int256 a) internal pure returns (bytes4, int256) {
        if (a == 0) return (0, 0);
        uint256 u = Wide.uabs(a);
        (, int256 w) = toFloat(0, 0, u, false, 0, NEAREST); // never overflows
        Num memory x = unpack(w);
        // m 2^ulp(e) / 10^18 = (m 2^60 / 5^18) 2^(ulp(e) - 78)
        uint256 q = Kernels.q18(x.m); // floor(m 2^60 / 5^18), lemma K18
        bool sticky = mulmod(x.m, 1 << 60, 3814697265625) != 0;
        return toFloat(a < 0 ? 1 : 0, 0, q, sticky, ulp(x.e) - 78, NEAREST);
    }
}

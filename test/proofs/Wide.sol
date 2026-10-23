// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

/// @title Wide
/// @notice Exact integers wider than a word, for the reference specs. A pair
///         (hi, lo) is hi 2^256 + lo: unsigned with hi a uint256, or two's
///         complement with hi an int256. Nothing here rounds.
///
///         Two primitives are the EVM's own and carry lemmas proved in
///         test/proofs/lemmas.py over unbounded integers:
///           L1  umul: for all words a, b, with l = MUL(a, b) and
///               m = MULMOD(a, b, 2^256 - 1), h = m - l - (m < l) is
///               floor(a b / 2^256): (h, l) is the exact product.
///           L2  smul: for words a, b read as two's complement, the exact
///               signed product is (h - [a < 0] b - [b < 0] a, l), the high
///               word taken mod 2^256.
///           L5  uabs: (x XOR m) - m, m = SAR(255, x), is |x|.
///         Everything else is word arithmetic with explicit carries.
library Wide {
    /// |x| as a uint256, |-2^255| = 2^255: (x XOR m) - m for the sign mask m,
    /// lemma L5. Spelled as the libraries spell it, so that the products the
    /// specs form from it are the libraries' terms.
    function uabs(int256 x) internal pure returns (uint256 r) {
        assembly {
            let m := sar(255, x)
            r := sub(xor(x, m), m)
        }
    }

    /// The exact unsigned product a b as (hi, lo). L1.
    function umul(uint256 a, uint256 b) internal pure returns (uint256 hi, uint256 lo) {
        uint256 mm;
        assembly {
            lo := mul(a, b)
            mm := mulmod(a, b, not(0))
        }
        unchecked {
            hi = mm - lo - (mm < lo ? 1 : 0);
        }
    }

    /// The exact signed product a b as (hi, lo), two's complement. L2.
    function smul(int256 a, int256 b) internal pure returns (int256 hi, uint256 lo) {
        uint256 h;
        (h, lo) = umul(uint256(a), uint256(b));
        assembly {
            // [a < 0] b and [b < 0] a, the corrections of L2
            h := sub(sub(h, mul(slt(a, 0), b)), mul(slt(b, 0), a))
        }
        hi = int256(h);
    }

    /// (hi, lo) + c for a small unsigned c, signed pair.
    function sadd(int256 hi, uint256 lo, uint256 c) internal pure returns (int256, uint256) {
        unchecked {
            uint256 l = lo + c;
            return (hi + (l < lo ? int256(1) : int256(0)), l);
        }
    }

    /// The signed pair as an int256, and whether it fits one.
    function toInt(int256 hi, uint256 lo) internal pure returns (bool fits, int256 r) {
        r = int256(lo);
        fits = (hi == 0 && r >= 0) || (hi == -1 && r < 0);
    }

    /// floor((hi, lo) / 2^k) for 0 < k < 256, signed pair.
    function sshr(int256 hi, uint256 lo, uint256 k) internal pure returns (int256, uint256) {
        return (hi >> k, (uint256(hi) << (256 - k)) | (lo >> k));
    }

    /// a < b on unsigned pairs.
    function ult(uint256 ah, uint256 al, uint256 bh, uint256 bl) internal pure returns (bool) {
        return ah < bh || (ah == bh && al < bl);
    }
}

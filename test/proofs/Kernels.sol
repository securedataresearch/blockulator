// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

/// @title Kernels
/// @notice The integer division kernels the reference specs take as given.
///
///         Each is a 512-by-256 floor division by Remco Bloemen's mulDiv
///         (exact remainder subtracted, the divisor's powers of two divided
///         out, its odd part inverted modulo 2^256 by six Newton steps),
///         copied verbatim from the library source. The specs use them as the
///         exact floor quotient, which is lemma
///           K127  divq(a, b)   = floor(a 2^128 / b)  for b > 0, a >> 128 < b
///           K256  divh(a, b)   = floor(a 2^255 / b)  for b > 0, a < 2 b
///         The Halmos proofs show every op equals its spec given these
///         quotients; test/proofs/kernel.py proves the lemmas, step by step
///         over the integers (the remainder's borrow, the division by the
///         divisor's powers of two, the Newton inverse modulo 2^256), and
///         test/proofs/Fuzz.t.sol checks them against a long division. The
///         solver could not close them inside the op proofs: the inverse is a
///         chain of eleven 256-bit products.
library Kernels {
    /// FP127's div kernel, as fp127_div writes it (contracts/src/fp127/FP127.yul.src).
    function divq(uint256 ua, uint256 ub) internal pure returns (uint256 q) {
        assembly {
            q := shr(128, ua)
            let prod0 := shl(128, ua)
            let rem := mulmod(ua, 0x100000000000000000000000000000000, ub)
            q := sub(q, gt(rem, prod0))
            prod0 := sub(prod0, rem)
            let twos := and(sub(0, ub), ub)
            let d := div(ub, twos)
            prod0 := or(div(prod0, twos), mul(q, add(div(sub(0, twos), twos), 1)))
            let iv := xor(mul(3, d), 2)
            iv := mul(iv, sub(2, mul(d, iv)))
            iv := mul(iv, sub(2, mul(d, iv)))
            iv := mul(iv, sub(2, mul(d, iv)))
            iv := mul(iv, sub(2, mul(d, iv)))
            iv := mul(iv, sub(2, mul(d, iv)))
            iv := mul(iv, sub(2, mul(d, iv)))
            q := mul(prod0, iv)
        }
    }

    /// FP256's divh (contracts/src/fp256/FP256.yul.src).
    function divh(uint256 a, uint256 b) internal pure returns (uint256 q) {
        assembly {
            let prod0 := shl(255, a)
            let prod1 := shr(1, a)
            let remainder := mulmod(a, 0x8000000000000000000000000000000000000000000000000000000000000000, b)
            prod1 := sub(prod1, gt(remainder, prod0))
            prod0 := sub(prod0, remainder)
            let twos := and(sub(0, b), b)
            b := div(b, twos)
            prod0 := div(prod0, twos)
            prod0 := or(prod0, mul(prod1, add(div(sub(0, twos), twos), 1)))
            let iv := xor(mul(3, b), 2)
            iv := mul(iv, sub(2, mul(b, iv)))
            iv := mul(iv, sub(2, mul(b, iv)))
            iv := mul(iv, sub(2, mul(b, iv)))
            iv := mul(iv, sub(2, mul(b, iv)))
            iv := mul(iv, sub(2, mul(b, iv)))
            iv := mul(iv, sub(2, mul(b, iv)))
            q := mul(prod0, iv)
        }
    }

    /// floor(m 2^60 / 5^18) for m < 2^237, as fp256_fromFixed18 writes it: two
    /// word divisions by 5^18 < 2^42, m split at bit 100. Lemma K18, proved
    /// in test/proofs/lemmas.py (linear integer arithmetic).
    function q18(uint256 m) internal pure returns (uint256 q) {
        assembly {
            let A := shl(60, shr(100, m))
            q := add(shl(100, div(A, 3814697265625)), div(add(shl(100, mod(A, 3814697265625)), shl(60, and(m, 0xfffffffffffffffffffffffff))), 3814697265625))
        }
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {FP19Lib} from "../../contracts/src/fp19/FP19Lib.sol";
import {Harness} from "./Harness.sol";
import {Ref19} from "./Ref19.sol";
import {Kernels} from "./Kernels.sol";
import {Wide} from "./Wide.sol";

/// @title ProofsFP19
/// @notice Halmos proofs: for every int256 (or uint256) input, each FP19 op
///         returns exactly what Ref19 returns, or reverts with the error
///         Ref19 names.
contract ProofsFP19 is Harness {
    uint256 internal constant N = 0; // Ref19.NEAREST
    uint256 internal constant D = 1; // Ref19.DOWN
    uint256 internal constant U = 2; // Ref19.UP

    function fp19_add(int256 a, int256 b) external pure returns (int256) { return FP19Lib.add(a, b); }
    function fp19_sub(int256 a, int256 b) external pure returns (int256) { return FP19Lib.sub(a, b); }
    function fp19_mul(int256 a, int256 b) external pure returns (int256) { return FP19Lib.mul(a, b); }
    function fp19_mulDown(int256 a, int256 b) external pure returns (int256) { return FP19Lib.mulDown(a, b); }
    function fp19_mulUp(int256 a, int256 b) external pure returns (int256) { return FP19Lib.mulUp(a, b); }
    function fp19_div(int256 a, int256 b) external pure returns (int256) { return FP19Lib.div(a, b); }
    function fp19_divDown(int256 a, int256 b) external pure returns (int256) { return FP19Lib.divDown(a, b); }
    function fp19_divUp(int256 a, int256 b) external pure returns (int256) { return FP19Lib.divUp(a, b); }
    function fp19_inv(int256 x) external pure returns (int256) { return FP19Lib.inv(x); }
    function fp19_floor(int256 x) external pure returns (int256) { return FP19Lib.floor(x); }
    function fp19_ceil(int256 x) external pure returns (int256) { return FP19Lib.ceil(x); }
    function fp19_round(int256 x) external pure returns (int256) { return FP19Lib.round(x); }
    function fp19_toUintDown(int256 x) external pure returns (int256) { return int256(FP19Lib.toUintDown(x)); }
    function fp19_toUintUp(int256 x) external pure returns (int256) { return int256(FP19Lib.toUintUp(x)); }
    function fp19_toIntDown(int256 x) external pure returns (int256) { return FP19Lib.toIntDown(x); }
    function fp19_toIntUp(int256 x) external pure returns (int256) { return FP19Lib.toIntUp(x); }
    function fp19_toFixed18(int256 x) external pure returns (int256) { return FP19Lib.toFixed18(x); }
    function fp19_toFixed18Down(int256 x) external pure returns (int256) { return FP19Lib.toFixed18Down(x); }
    function fp19_toFixed18Up(int256 x) external pure returns (int256) { return FP19Lib.toFixed18Up(x); }
    function fp19_fromUint(int256 x) external pure returns (int256) { return FP19Lib.fromUint(uint256(x)); }
    function fp19_fromUintDown(int256 x) external pure returns (int256) { return FP19Lib.fromUintDown(uint256(x)); }
    function fp19_fromUintUp(int256 x) external pure returns (int256) { return FP19Lib.fromUintUp(uint256(x)); }
    function fp19_fromFixed18(int256 x) external pure returns (int256) { return FP19Lib.fromFixed18(x); }

    // the specs, behind an external call: a spec that reverts fails the proof
    function ref_add(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref19.add(a, b); }
    function ref_sub(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref19.sub(a, b); }
    function ref_mul(int256 a, int256 b, uint256 mode) external pure returns (bytes4, int256) { return Ref19.mul(a, b, mode); }
    function ref_div(int256 a, int256 b, uint256 mode) external pure returns (bytes4, int256) { return Ref19.div(a, b, mode); }
    function ref_inv(int256 a) external pure returns (bytes4, int256) { return Ref19.inv(a); }
    function ref_integral(int256 a, uint256 mode) external pure returns (bytes4, int256) { return Ref19.integral(a, mode); }
    function ref_integer(int256 a, uint256 mode, bool unsigned_) external pure returns (bytes4, int256) { return Ref19.integer(a, mode, unsigned_); }
    function ref_toFixed18(int256 a, uint256 mode) external pure returns (bytes4, int256) { return Ref19.toFixed18(a, mode); }
    function ref_fromUint(uint256 x, uint256 mode) external pure returns (bytes4, int256) { return Ref19.fromUint(x, mode); }
    function ref_fromFixed18(int256 a) external pure returns (bytes4, int256) { return Ref19.fromFixed18(a); }

    // ---- facts about the uninterpreted terms, each a lemma (lemmas.py) ----
    // Called before the spec runs, whose own asserts state the same ranges;
    // each computes the term the library and the spec share, and none can
    // revert.

    /// L6: two significands' product lies in [2^472, 2^474).
    function assumeL6(int256 a, int256 b) internal view {
        Ref19.Num memory x = Ref19.unpack(a);
        Ref19.Num memory y = Ref19.unpack(b);
        if (x.m == 0 || y.m == 0) return;
        (uint256 ph,) = Wide.umul(x.m, y.m);
        vm.assume(ph >> 216 != 0 && ph >> 218 == 0);
    }

    /// L7: the quotient of two significands, floor(ma 2^255 / mb), is at least 2^254.
    function assumeL7(int256 a, int256 b) internal view {
        Ref19.Num memory x = Ref19.unpack(a);
        Ref19.Num memory y = Ref19.unpack(b);
        if (x.m == 0 || y.m == 0) return;
        vm.assume(Kernels.divh(x.m, y.m) >> 254 != 0);
    }

    /// L7: floor(2^491 / m) is at least 2^254.
    function assumeL7inv(int256 a) internal view {
        Ref19.Num memory x = Ref19.unpack(a);
        if (x.m == 0) return;
        vm.assume(Kernels.divh(1 << 236, x.m) >> 254 != 0);
    }

    /// L7: floor(m 2^60 / 5^18) is at least 2^254, for fromFixed18's rounded |x|.
    function assumeL7q18(int256 a) internal view {
        if (a == 0) return;
        (, int256 w) = Ref19.toFloat(0, 0, Wide.uabs(a), false, 0, Ref19.NEAREST);
        vm.assume(Kernels.q18(Ref19.unpack(w).m) >> 254 != 0);
    }

    // ---- input classes ----
    // Where one symbolic run does not close in time, a check splits its
    // inputs by a field: `pin` forks one path per value of the field in a
    // window, and on each path the field is the constant the search reached,
    // so the op and the spec run with concrete shift amounts. Every input is
    // still covered: inside the window by its own path, outside it by the
    // symbolic run.

    /// d for 0 <= d < 2^10, as the literal a ten-step binary search reaches:
    /// on each path the result is a constant (and equal to d).
    function pin(uint256 d) internal pure returns (uint256 k) {
        assembly {
            if iszero(lt(d, add(k, 512))) { k := add(k, 512) }
            if iszero(lt(d, add(k, 256))) { k := add(k, 256) }
            if iszero(lt(d, add(k, 128))) { k := add(k, 128) }
            if iszero(lt(d, add(k, 64))) { k := add(k, 64) }
            if iszero(lt(d, add(k, 32))) { k := add(k, 32) }
            if iszero(lt(d, add(k, 16))) { k := add(k, 16) }
            if iszero(lt(d, add(k, 8))) { k := add(k, 8) }
            if iszero(lt(d, add(k, 4))) { k := add(k, 4) }
            if iszero(lt(d, add(k, 2))) { k := add(k, 2) }
            if iszero(lt(d, add(k, 1))) { k := add(k, 1) }
        }
    }

    /// x with its exponent field rewritten as a literal when it lies in
    /// [lo, lo + n), n <= 2^10; x itself otherwise. The word is unchanged.
    function pinExp(int256 x, uint256 lo, uint256 n) internal pure returns (int256) {
        uint256 e = (uint256(x) >> 236) & 0x7ffff;
        if (e < lo || e >= lo + n) return x;
        uint256 k = lo + pin(e - lo);
        return int256((uint256(x) & ~(uint256(0x7ffff) << 236)) | (k << 236));
    }

    /// toFixed18's window: |x| 10^18 = m 10^18 2^-k with k = 0x400eb - e in
    /// [1, 297], the exponents whose result needs a shift (below, Overflow;
    /// above, zero).
    function pinToFixed18(int256 x) internal pure returns (int256) {
        return pinExp(x, 0x400eb - 297, 297);
    }

    function check_fp19_add(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp19_add.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_add, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp19_sub(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp19_sub.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_sub, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp19_mul(int256 a, int256 b) public view {
        assumeL3(a, b);
        (bytes4 e, int256 r) = run2(this.fp19_mul.selector, a, b);
        assumeL6(a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_mul, (a, b, N)));
        same(e, r, se, sr);
    }

    function check_fp19_mulDown(int256 a, int256 b) public view {
        assumeL3(a, b);
        (bytes4 e, int256 r) = run2(this.fp19_mulDown.selector, a, b);
        assumeL6(a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_mul, (a, b, D)));
        same(e, r, se, sr);
    }

    function check_fp19_mulUp(int256 a, int256 b) public view {
        assumeL3(a, b);
        (bytes4 e, int256 r) = run2(this.fp19_mulUp.selector, a, b);
        assumeL6(a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_mul, (a, b, U)));
        same(e, r, se, sr);
    }

    function check_fp19_div(int256 a, int256 b) public view {
        assumeL3(a, b);
        (bytes4 e, int256 r) = run2(this.fp19_div.selector, a, b);
        assumeL7(a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_div, (a, b, N)));
        same(e, r, se, sr);
    }

    function check_fp19_divDown(int256 a, int256 b) public view {
        assumeL3(a, b);
        (bytes4 e, int256 r) = run2(this.fp19_divDown.selector, a, b);
        assumeL7(a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_div, (a, b, D)));
        same(e, r, se, sr);
    }

    function check_fp19_divUp(int256 a, int256 b) public view {
        assumeL3(a, b);
        (bytes4 e, int256 r) = run2(this.fp19_divUp.selector, a, b);
        assumeL7(a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_div, (a, b, U)));
        same(e, r, se, sr);
    }

    function check_fp19_inv(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_inv.selector, x);
        assumeL7inv(x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_inv, (x)));
        same(e, r, se, sr);
    }

    function check_fp19_floor(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_floor.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_integral, (x, D)));
        same(e, r, se, sr);
    }

    function check_fp19_ceil(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_ceil.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_integral, (x, U)));
        same(e, r, se, sr);
    }

    function check_fp19_round(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_round.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_integral, (x, N)));
        same(e, r, se, sr);
    }

    function check_fp19_toUintDown(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_toUintDown.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_integer, (x, D, true)));
        same(e, r, se, sr);
    }

    function check_fp19_toUintUp(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_toUintUp.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_integer, (x, U, true)));
        same(e, r, se, sr);
    }

    function check_fp19_toIntDown(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_toIntDown.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_integer, (x, D, false)));
        same(e, r, se, sr);
    }

    function check_fp19_toIntUp(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_toIntUp.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_integer, (x, U, false)));
        same(e, r, se, sr);
    }

    function check_fp19_toFixed18(int256 x) public view {
        x = pinToFixed18(x);
        (bytes4 e, int256 r) = run1(this.fp19_toFixed18.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_toFixed18, (x, N)));
        same(e, r, se, sr);
    }

    function check_fp19_toFixed18Down(int256 x) public view {
        x = pinToFixed18(x);
        (bytes4 e, int256 r) = run1(this.fp19_toFixed18Down.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_toFixed18, (x, D)));
        same(e, r, se, sr);
    }

    function check_fp19_toFixed18Up(int256 x) public view {
        x = pinToFixed18(x);
        (bytes4 e, int256 r) = run1(this.fp19_toFixed18Up.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_toFixed18, (x, U)));
        same(e, r, se, sr);
    }

    function check_fp19_fromUint(uint256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_fromUint.selector, int256(x));
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_fromUint, (x, N)));
        same(e, r, se, sr);
    }

    function check_fp19_fromUintDown(uint256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_fromUintDown.selector, int256(x));
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_fromUint, (x, D)));
        same(e, r, se, sr);
    }

    function check_fp19_fromUintUp(uint256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_fromUintUp.selector, int256(x));
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_fromUint, (x, U)));
        same(e, r, se, sr);
    }

    function check_fp19_fromFixed18(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp19_fromFixed18.selector, x);
        assumeL7q18(x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_fromFixed18, (x)));
        same(e, r, se, sr);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {Harness} from "./Harness.sol";
import {Ref127} from "./Ref127.sol";
import {Wide} from "./Wide.sol";

/// @title ProofsFP127
/// @notice Halmos proofs: for every int256 input, each FP127 op returns
///         exactly what Ref127 returns, or reverts with the error Ref127 names.
///         The parameters of a check_ function are symbolic: one passing run
///         covers all 2^256 (or 2^512) inputs.
contract ProofsFP127 is Harness {
    function fp127_add(int256 a, int256 b) external pure returns (int256) { return FP127Lib.add(a, b); }
    function fp127_sub(int256 a, int256 b) external pure returns (int256) { return FP127Lib.sub(a, b); }
    function fp127_mul(int256 a, int256 b) external pure returns (int256) { return FP127Lib.mul(a, b); }
    function fp127_mulDown(int256 a, int256 b) external pure returns (int256) { return FP127Lib.mulDown(a, b); }
    function fp127_mulUp(int256 a, int256 b) external pure returns (int256) { return FP127Lib.mulUp(a, b); }
    function fp127_div(int256 a, int256 b) external pure returns (int256) { return FP127Lib.div(a, b); }
    function fp127_divDown(int256 a, int256 b) external pure returns (int256) { return FP127Lib.divDown(a, b); }
    function fp127_divUp(int256 a, int256 b) external pure returns (int256) { return FP127Lib.divUp(a, b); }
    function fp127_inv(int256 x) external pure returns (int256) { return FP127Lib.inv(x); }
    function fp127_floor(int256 x) external pure returns (int256) { return FP127Lib.floor(x); }
    function fp127_ceil(int256 x) external pure returns (int256) { return FP127Lib.ceil(x); }
    function fp127_round(int256 x) external pure returns (int256) { return FP127Lib.round(x); }
    function fp127_toFixed18(int256 x) external pure returns (int256) { return FP127Lib.toFixed18(x); }
    function fp127_toFixed18Down(int256 x) external pure returns (int256) { return FP127Lib.toFixed18Down(x); }
    function fp127_toFixed18Up(int256 x) external pure returns (int256) { return FP127Lib.toFixed18Up(x); }
    function fp127_fromFixed18(int256 x) external pure returns (int256) { return FP127Lib.fromFixed18(x); }

    // the specs, behind an external call: a spec that reverts fails the proof
    function ref_add(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref127.add(a, b); }
    function ref_sub(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref127.sub(a, b); }
    function ref_mulDown(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref127.mulDown(a, b); }
    function ref_mulUp(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref127.mulUp(a, b); }
    function ref_div(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref127.div(a, b); }
    function ref_divDown(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref127.divDown(a, b); }
    function ref_divUp(int256 a, int256 b) external pure returns (bytes4, int256) { return Ref127.divUp(a, b); }
    function ref_inv(int256 x) external pure returns (bytes4, int256) { return Ref127.inv(x); }
    function ref_floor(int256 x) external pure returns (bytes4, int256) { return Ref127.floor(x); }
    function ref_ceil(int256 x) external pure returns (bytes4, int256) { return Ref127.ceil(x); }
    function ref_round(int256 x) external pure returns (bytes4, int256) { return Ref127.round(x); }
    function ref_toFixed18Down(int256 x) external pure returns (bytes4, int256) { return Ref127.toFixed18Down(x); }
    function ref_toFixed18Up(int256 x) external pure returns (bytes4, int256) { return Ref127.toFixed18Up(x); }
    function ref_fromFixed18(int256 x) external pure returns (bytes4, int256) { return Ref127.fromFixed18(x); }

    function check_fp127_add(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp127_add.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_add, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp127_sub(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp127_sub.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_sub, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp127_mul(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp127_mul.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_mulDown, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp127_mulDown(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp127_mulDown.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_mulDown, (a, b)));
        same(e, r, se, sr);
    }

    /// Fails: mulUp reverts where its floor is -2^255 - 1 and the ceiling
    /// -2^255 fits (docs/proofs.md, FuzzProofs.test_fp127_mulUp_counterexample).
    /// The solver finds the failing path at once, but a concrete model needs
    /// a factorisation of a 383-bit window, so the run ends in a timeout.
    function check_fp127_mulUp(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp127_mulUp.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_mulUp, (a, b)));
        same(e, r, se, sr);
    }

    /// mulUp on every input outside that window: products whose floor is
    /// not -2^255 - 1 with a nonzero remainder.
    function check_fp127_mulUp_outside(int256 a, int256 b) public view {
        (int256 ph, uint256 pl) = Wide.smul(a, b);
        (int256 fh, uint256 fl) = Wide.sshr(ph, pl, 128);
        // floor(a b / 2^128) = -2^255 - 1 is the pair (-1, 2^255 - 1)
        vm.assume(!(fh == -1 && fl == uint256(type(int256).max) && pl & Ref127.LOW128 != 0));
        (bytes4 e, int256 r) = run2(this.fp127_mulUp.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_mulUp, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp127_div(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp127_div.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_div, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp127_divDown(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp127_divDown.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_divDown, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp127_divUp(int256 a, int256 b) public view {
        (bytes4 e, int256 r) = run2(this.fp127_divUp.selector, a, b);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_divUp, (a, b)));
        same(e, r, se, sr);
    }

    function check_fp127_inv(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp127_inv.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_inv, (x)));
        same(e, r, se, sr);
    }

    function check_fp127_floor(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp127_floor.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_floor, (x)));
        same(e, r, se, sr);
    }

    function check_fp127_ceil(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp127_ceil.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_ceil, (x)));
        same(e, r, se, sr);
    }

    function check_fp127_round(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp127_round.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_round, (x)));
        same(e, r, se, sr);
    }

    function check_fp127_toFixed18(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp127_toFixed18.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_toFixed18Down, (x)));
        same(e, r, se, sr);
    }

    function check_fp127_toFixed18Down(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp127_toFixed18Down.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_toFixed18Down, (x)));
        same(e, r, se, sr);
    }

    function check_fp127_toFixed18Up(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp127_toFixed18Up.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_toFixed18Up, (x)));
        same(e, r, se, sr);
    }

    function check_fp127_fromFixed18(int256 x) public view {
        (bytes4 e, int256 r) = run1(this.fp127_fromFixed18.selector, x);
        (bytes4 se, int256 sr) = spec(abi.encodeCall(this.ref_fromFixed18, (x)));
        same(e, r, se, sr);
    }
}

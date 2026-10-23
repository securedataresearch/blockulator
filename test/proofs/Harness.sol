// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Vm} from "forge-std/Vm.sol";

/// @title Harness
/// @notice Calls an op of the inline library through an external call to the
///         test contract itself, so a revert comes back as data: (0, r) on
///         success, (selector, 0) on a revert. A revert that is not a 4-byte
///         error fails the proof.
abstract contract Harness {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    /// Lemma L3 (test/proofs/lemmas.py), handed to the solver as an
    /// assumption because multiplication is uninterpreted in the proofs: the
    /// product of two FP256 exponent fields, each below 2^19, is zero iff one
    /// of them is (it cannot wrap). FP256's binary ops test their two
    /// exponents with one MUL; the term here is the same product.
    function assumeL3(int256 a, int256 b) internal view {
        uint256 p;
        bool z;
        assembly {
            let ea := and(shr(236, a), 0x7ffff)
            let eb := and(shr(236, b), 0x7ffff)
            p := mul(ea, eb)
            z := or(iszero(ea), iszero(eb))
        }
        vm.assume((p == 0) == z);
    }

    function _ret(bool ok, bytes memory ret) private pure returns (bytes4 err, int256 r) {
        if (ok) {
            assert(ret.length == 32);
            r = abi.decode(ret, (int256));
        } else {
            assert(ret.length == 4);
            err = bytes4(ret);
            assert(err != 0);
        }
    }

    function run1(bytes4 sel, int256 x) internal view returns (bytes4, int256) {
        (bool ok, bytes memory ret) = address(this).staticcall(abi.encodeWithSelector(sel, x));
        return _ret(ok, ret);
    }

    function run2(bytes4 sel, int256 a, int256 b) internal view returns (bytes4, int256) {
        (bool ok, bytes memory ret) = address(this).staticcall(abi.encodeWithSelector(sel, a, b));
        return _ret(ok, ret);
    }

    /// The spec's answer, through an external call too: Halmos counts only
    /// failed assertions, so a spec that reverted in place (a checked
    /// overflow, say) would drop its path silently. Here it fails the proof.
    function spec(bytes memory call) internal view returns (bytes4 se, int256 sr) {
        (bool ok, bytes memory ret) = address(this).staticcall(call);
        assert(ok);
        (se, sr) = abi.decode(ret, (bytes4, int256));
    }

    /// The op returned exactly what the spec returns, or reverted exactly as it says.
    function same(bytes4 e, int256 r, bytes4 se, int256 sr) internal pure {
        assert(e == se);
        if (e == 0) assert(r == sr);
    }
}

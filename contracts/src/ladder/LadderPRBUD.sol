// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {ParamOutOfRange} from "./ILadder.sol";
import {UD60x18, ud} from "../../../lib/prb-math/src/UD60x18.sol";
import * as M from "../../../lib/prb-math/src/ud60x18/Math.sol";

/// @title LadderPRBUD
/// @notice PRBMath UD60x18, the unsigned WAD half of PRBMath: mul, div, exp,
///         ln, sqrt, pow and powu from the library, checked native add/sub.
///         A negative parameter does not fit the type (ParamOutOfRange), and
///         a negative intermediate (a difference below zero) reverts with
///         Negative() where it would enter the library.
contract LadderPRBUD is LadderBase {
    error Negative();
    error Overflow();

    /// int256 of a library result; Overflow() past int256, where a bare cast would wrap.
    function _i(uint256 v) internal pure returns (int256) {
        if (v > uint256(type(int256).max)) revert Overflow();
        return int256(v);
    }

    function _p(int256[] calldata p, uint256 i) internal pure override returns (int256) {
        if (p[i] < 0) revert ParamOutOfRange(i);
        return p[i];
    }
    function _u(int256 x) internal pure returns (UD60x18) {
        if (x < 0) revert Negative();
        return ud(uint256(x));
    }
    function _one() internal pure override returns (int256) { return 1e18; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) * 1e18; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return a + b; }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return a - b; }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return _i(M.mul(_u(a), _u(b)).unwrap()); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return _i(M.div(_u(a), _u(b)).unwrap()); }
    function _exp(int256 x) internal view override returns (int256) { return _i(M.exp(_u(x)).unwrap()); }
    function _ln(int256 x) internal view override returns (int256) { return _i(M.ln(_u(x)).unwrap()); }
    function _sqrt(int256 x) internal view override returns (int256) { return _i(M.sqrt(_u(x)).unwrap()); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return _i(M.pow(_u(x), _u(y)).unwrap()); }
    /// powu: PRBMath's exponentiation by squaring.
    function _powu(int256 x, int256 n) internal view override returns (int256) {
        if (n < 0) return _i(M.div(ud(1e18), M.powu(_u(x), uint256(-n))).unwrap());
        return _i(M.powu(_u(x), uint256(n)).unwrap());
    }
}

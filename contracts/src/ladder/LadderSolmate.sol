// SPDX-License-Identifier: AGPL-3.0-only
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {wadMul, wadDiv, wadExp, wadLn, wadPow} from "../../../lib/solmate/src/utils/SignedWadMath.sol";
import {FixedPointMathLib as F} from "../../../lib/solmate/src/utils/FixedPointMathLib.sol";

/// @title LadderSolmate
/// @notice Solmate in signed WAD (1e18): SignedWadMath's wadMul, wadDiv
///         (sdiv, toward zero), wadExp, wadLn and wadPow, and
///         FixedPointMathLib's rpow for integer powers. Solmate's sqrt is the
///         integer root, so a WAD root is sqrt(x 10^18), as a Solmate user
///         takes it. Checked native add/sub.
///
///         This file is AGPL-3.0-only because it links Solmate's
///         FixedPointMathLib (lib/solmate, AGPL-3.0-only); SignedWadMath is MIT.
contract LadderSolmate is LadderBase {
    error Negative();
    error Overflow();

    /// int256 of a library result; Overflow() past int256, where a bare cast would wrap.
    function _i(uint256 v) internal pure returns (int256) {
        if (v > uint256(type(int256).max)) revert Overflow();
        return int256(v);
    }

    function _one() internal pure override returns (int256) { return 1e18; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) * 1e18; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return a + b; }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return a - b; }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return wadMul(a, b); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return wadDiv(a, b); }
    function _exp(int256 x) internal view override returns (int256) { return wadExp(x); }
    function _ln(int256 x) internal view override returns (int256) { return wadLn(x); }
    function _sqrt(int256 x) internal view override returns (int256) {
        if (x < 0) revert Negative();
        return int256(F.sqrt(uint256(x) * 1e18));
    }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return wadPow(x, y); }
    /// rpow(x, n, 1e18): exponentiation by squaring, half up each step.
    function _powu(int256 x, int256 n) internal view override returns (int256) {
        if (x < 0) revert Negative();
        if (n < 0) return wadDiv(1e18, _i(F.rpow(uint256(x), uint256(-n), 1e18)));
        return _i(F.rpow(uint256(x), uint256(n), 1e18));
    }
}

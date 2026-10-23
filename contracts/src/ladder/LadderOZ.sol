// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {Unsupported, Op} from "./ILadder.sol";
import {Math} from "./vendor/openzeppelin/utils/math/Math.sol";

/// @title LadderOZ
/// @notice OpenZeppelin Contracts' Math (v5.7.0, vendored) in WAD. Its maths
///         is integer maths, so the WAD ops are its integer functions with
///         10^18 put in, as an OpenZeppelin user writes them: mul =
///         mulDiv(a, b, 1e18), div = mulDiv(a, 1e18, b), sqrt =
///         sqrt(x 10^18), each rounding down. mulDiv is unsigned: it is
///         applied to magnitudes with the sign restored (truncation toward
///         zero). OpenZeppelin has no exp, ln or real power, so every
///         scenario that needs one is Unsupported, which the ladder leaves
///         empty.
contract LadderOZ is LadderBase {
    error Negative();
    error Overflow();

    function _abs(int256 x) internal pure returns (uint256) { return x < 0 ? uint256(-x) : uint256(x); }
    /// The magnitude with the sign restored; Overflow() past int256, where a bare cast would wrap.
    function _sign(int256 a, int256 b, uint256 m) internal pure returns (int256) {
        if (m > uint256(type(int256).max)) revert Overflow();
        return (a < 0) != (b < 0) ? -int256(m) : int256(m);
    }
    function _one() internal pure override returns (int256) { return 1e18; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) * 1e18; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return a + b; }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return a - b; }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return _sign(a, b, Math.mulDiv(_abs(a), _abs(b), 1e18)); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return _sign(a, b, Math.mulDiv(_abs(a), 1e18, _abs(b))); }
    function _sqrt(int256 x) internal view override returns (int256) {
        if (x < 0) revert Negative();
        return int256(Math.sqrt(uint256(x) * 1e18));
    }
    function _exp(int256) internal view override returns (int256) { revert Unsupported(Op.EXP); }
    function _ln(int256) internal view override returns (int256) { revert Unsupported(Op.LN); }
    function _pow(int256, int256) internal view override returns (int256) { revert Unsupported(Op.POW); }
}

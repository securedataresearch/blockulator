// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {LogExpMath} from "./vendor/balancer/LogExpMath.sol";

/// @title LadderBalancer
/// @notice Balancer's LogExpMath (v3, vendored under vendor/balancer) in WAD:
///         exp, ln and pow with 20-decimal internals, the pow behind every
///         weighted pool. Balancer's FixedPoint is unsigned, so mulDown and
///         divDown are applied here to magnitudes with the sign restored
///         (truncation toward zero, as FixedPoint truncates). There is no
///         sqrt in the library; sqrt(x) is pow(x, 1/2), which is how a
///         Balancer pool would take a root. pow is defined for x, y >= 0.
contract LadderBalancer is LadderBase {
    error Negative();

    function _one() internal pure override returns (int256) { return 1e18; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) * 1e18; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return a + b; }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return a - b; }
    function _abs(int256 x) internal pure returns (uint256) { return x < 0 ? uint256(-x) : uint256(x); }
    function _sign(int256 a, int256 b, uint256 m) internal pure returns (int256) { return (a < 0) != (b < 0) ? -int256(m) : int256(m); }
    /// FixedPoint.mulDown: a * b / ONE.
    function _mul(int256 a, int256 b) internal view override returns (int256) { return _sign(a, b, _abs(a) * _abs(b) / 1e18); }
    /// FixedPoint.divDown: a * ONE / b.
    function _div(int256 a, int256 b) internal view override returns (int256) { return _sign(a, b, _abs(a) * 1e18 / _abs(b)); }
    function _exp(int256 x) internal view override returns (int256) { return LogExpMath.exp(x); }
    function _ln(int256 x) internal view override returns (int256) { return LogExpMath.ln(x); }
    function _sqrt(int256 x) internal view override returns (int256) {
        if (x < 0) revert Negative();
        return int256(LogExpMath.pow(uint256(x), 5e17));
    }
    function _pow(int256 x, int256 y) internal view override returns (int256) {
        if (x < 0 || y < 0) revert Negative();
        return int256(LogExpMath.pow(uint256(x), uint256(y)));
    }
}

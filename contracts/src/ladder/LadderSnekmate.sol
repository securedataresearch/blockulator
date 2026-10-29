// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";

/// @notice contracts/src/ladder/vyper/SnekmateMath.vy: snekmate's math module
///         (v0.1.2, Vyper 0.4.3), each function returning (result, gas).
interface ISnekmateMath {
    function wad_exp(int256 x) external view returns (int256, uint256);
    function wad_ln(int256 x) external view returns (int256, uint256);
    function wad_cbrt(uint256 x) external view returns (uint256, uint256);
    function wad_sqrt(uint256 x) external view returns (uint256, uint256);
    function mul_div(uint256 x, uint256 y, uint256 d, bool roundup) external view returns (uint256, uint256);
    function log2(uint256 x, bool roundup) external view returns (uint256, uint256);
    function int256_average(int256 x, int256 y) external view returns (int256, uint256);
    function signum(int256 x) external view returns (int256, uint256);
    function noop(int256 x) external view returns (int256, uint256);
}

/// @title LadderSnekmate
/// @notice snekmate's Vyper math module in signed WAD, through the deployed
///         SnekmateMath contract (one staticcall per op, as BL127's deployed
///         form makes): wad_exp and wad_ln; mul and div are mul_div(|a|, |b|,
///         1e18) and mul_div(|a|, 1e18, |b|), rounding down, with the sign
///         restored (truncation toward zero). snekmate has no square root or
///         real power: sqrt is Vyper's built-in isqrt(x 10^18), as a Vyper
///         contract takes it, and pow(x, y) is wad_exp(wad_ln(x) y / 10^18),
///         as Solmate's wadPow composes it. Checked native add/sub.
contract LadderSnekmate is LadderBase {
    error Negative();
    error Overflow();

    ISnekmateMath public immutable math;

    constructor(address m) { math = ISnekmateMath(m); }

    function _warm() internal view override { require(address(math).code.length != 0, "no SnekmateMath"); }

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
    function _mul(int256 a, int256 b) internal view override returns (int256) {
        (uint256 m,) = math.mul_div(_abs(a), _abs(b), 1e18, false);
        return _sign(a, b, m);
    }
    function _div(int256 a, int256 b) internal view override returns (int256) {
        (uint256 m,) = math.mul_div(_abs(a), 1e18, _abs(b), false);
        return _sign(a, b, m);
    }
    function _exp(int256 x) internal view override returns (int256 r) { (r,) = math.wad_exp(x); }
    function _ln(int256 x) internal view override returns (int256 r) { (r,) = math.wad_ln(x); }
    function _sqrt(int256 x) internal view override returns (int256) {
        if (x < 0) revert Negative();
        (uint256 r,) = math.wad_sqrt(uint256(x));
        return int256(r);
    }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return _exp(_ln(x) * y / 1e18); }
}

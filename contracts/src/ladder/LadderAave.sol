// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ILadderAdapter, Scenario, BadParamCount, ParamOutOfRange, Unsupported} from "./ILadder.sol";

/// @title LadderAave
/// @notice Aave v3's interest accrual, in RAY (1e27): the three-term
///         expansion of e^(rate * t) that MathUtils.calculateCompoundedInterest
///         uses, with WadRayMath.rayMul's half-up rounding, transcribed from
///         aave-v3-origin (src/contracts/protocol/libraries/math, BUSL-1.1,
///         not vendored; see vendor/README.md). Aave states the ideal as
///         e^(rate per year * years) and notes that the expansion
///         "slightly underpays liquidity providers and undercharges
///         borrowers", so this adapter answers only the continuous accrual
///         scenario, where that is the model being judged, and reports
///         Unsupported for every other one.
contract LadderAave is ILadderAdapter {
    uint256 constant RAY = 1e27;
    uint256 constant HALF_RAY = 0.5e27;
    uint256 constant SECONDS_PER_YEAR = 365 days;

    /// WadRayMath.rayMul: (a * b + HALF_RAY) / RAY.
    function rayMul(uint256 a, uint256 b) internal pure returns (uint256) { return (a * b + HALF_RAY) / RAY; }

    /// MathUtils.calculateCompoundedInterest(rate, lastUpdate, now) with now - lastUpdate = seconds_.
    function compoundedInterest(uint256 rate, uint256 seconds_) internal pure returns (uint256) {
        if (seconds_ == 0) return RAY;
        uint256 x = (rate * seconds_) / SECONDS_PER_YEAR;
        return RAY + x + rayMul(x, x / 2 + rayMul(x, x / 6));
    }

    /// p = [principal, rateAnnual, rateSec] in RAY; N days of accrual.
    function run(uint8 scenario, uint32 n, int256[] calldata p) external view returns (int256 raw, uint256 gasUsed) {
        if (scenario != Scenario.ACCRUAL_CONTINUOUS) revert Unsupported(scenario);
        if (p.length != 3) revert BadParamCount(scenario, p.length);
        if (p[0] < 0) revert ParamOutOfRange(0);
        if (p[1] < 0) revert ParamOutOfRange(1);
        uint256 g0 = gasleft();
        uint256 factor = compoundedInterest(uint256(p[1]), uint256(n) * 86400);
        raw = int256(rayMul(uint256(p[0]), factor));
        gasUsed = g0 - gasleft();
    }
    /// Aave's maths has no general op: every edge is Unsupported.
    function op(uint8 op_, int256[] calldata) external pure returns (int256, uint256) { revert Unsupported(op_); }
}

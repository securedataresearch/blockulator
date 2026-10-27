// SPDX-License-Identifier: MIT
// Copyright (c) 2023 Morpho Association
pragma solidity ^0.8.24;

import {ILadderAdapter, Scenario, BadParamCount, ParamOutOfRange, Unsupported} from "./ILadder.sol";

/// @title EulerAdaptiveCurve
/// @notice Euler v2's IRMAdaptiveCurve rate-at-target update and its ExpLib,
///         transcribed with their integer types and rounding from
///         euler-xyz/evk-periphery @ af436991 (src/IRM/IRMAdaptiveCurve.sol,
///         src/IRM/lib/ExpLib.sol; MIT, Copyright (c) 2023 Morpho
///         Association; Euler Labs, adapted from morpho-blue-irm; see
///         vendor/README.md). The contract's immutables are the fields of
///         Config. Every line below is the deployed line with the immutable
///         read from `c`.
library EulerAdaptiveCurve {
    int256 internal constant WAD = 1e18;
    /// @dev ln(2).
    int256 internal constant LN_2_INT = 0.693147180559945309e18;
    /// @dev ln(1e-18).
    int256 internal constant LN_WEI_INT = -41.446531673892822312e18;
    /// @dev Above this bound, `wExp` is clipped to avoid overflowing when multiplied with 1e18.
    int256 internal constant WEXP_UPPER_BOUND = 93.859467695000404319e18;
    /// @dev The value of wExp(`WEXP_UPPER_BOUND`).
    int256 internal constant WEXP_UPPER_VALUE = 57716089161558943949701069502944508345128.422502756744429568e18;

    struct Config {
        int256 TARGET_UTILIZATION;
        int256 MIN_RATE_AT_TARGET;
        int256 MAX_RATE_AT_TARGET;
        int256 CURVE_STEEPNESS;
        int256 ADJUSTMENT_SPEED;
    }

    /// ExpLib.wExp: x = q ln2 + r, |r| <= ln2 / 2, e^r by the second-order
    /// Taylor polynomial 1 + r + r^2/2, times 2^q.
    function wExp(int256 x) internal pure returns (int256) {
        unchecked {
            if (x < LN_WEI_INT) return 0;
            if (x >= WEXP_UPPER_BOUND) return WEXP_UPPER_VALUE;
            int256 roundingAdjustment = (x < 0) ? -(LN_2_INT / 2) : (LN_2_INT / 2);
            int256 q = (x + roundingAdjustment) / LN_2_INT;
            int256 r = x - q * LN_2_INT;
            int256 expR = WAD + r + (r * r) / WAD / 2;
            if (q >= 0) return expR << uint256(q);
            else return expR >> uint256(-q);
        }
    }

    /// IRMAdaptiveCurve._newRateAtTarget, whose comment states the formula
    /// "rateAtTarget = startRateAtTarget * e^linearAdaptation bounded to min and max".
    function newRateAtTarget(Config memory c, int256 startRateAtTarget, int256 linearAdaptation) internal pure returns (int256) {
        int256 rateAtTarget = startRateAtTarget * wExp(linearAdaptation) / WAD;
        if (rateAtTarget < c.MIN_RATE_AT_TARGET) return c.MIN_RATE_AT_TARGET;
        if (rateAtTarget > c.MAX_RATE_AT_TARGET) return c.MAX_RATE_AT_TARGET;
        return rateAtTarget;
    }

    /// IRMAdaptiveCurve._calcErr.
    function calcErr(Config memory c, int256 utilization) internal pure returns (int256) {
        int256 errNormFactor = utilization > c.TARGET_UTILIZATION ? WAD - c.TARGET_UTILIZATION : c.TARGET_UTILIZATION;
        return (utilization - c.TARGET_UTILIZATION) * WAD / errNormFactor;
    }

    /// IRMAdaptiveCurve._curve.
    function curve(Config memory c, int256 rateAtTarget, int256 err) internal pure returns (int256) {
        int256 coeff = err < 0 ? WAD - WAD * WAD / c.CURVE_STEEPNESS : c.CURVE_STEEPNESS - WAD;
        return ((coeff * err / WAD) + WAD) * rateAtTarget / WAD;
    }

    /// The rate-at-target branch of IRMAdaptiveCurve.computeInterestRateInternal
    /// for a vault that has state (startRateAtTarget != 0): the adaptation uses
    /// the utilisation stored at the last update, over the time since it.
    function endRateAtTarget(Config memory c, int256 startRateAtTarget, int256 lastUtilization, int256 elapsed)
        internal
        pure
        returns (int256)
    {
        int256 errOld = calcErr(c, lastUtilization);
        int256 speed = c.ADJUSTMENT_SPEED * errOld / WAD;
        int256 linearAdaptation = speed * elapsed;
        if (linearAdaptation == 0) return startRateAtTarget;
        return newRateAtTarget(c, startRateAtTarget, linearAdaptation);
    }
}

/// @title LadderEuler
/// @notice Euler v2's adaptive rate at target (EulerAdaptiveCurve above), for
///         the adaptive-rate scenario only. The comment on _newRateAtTarget
///         states rateAtTarget = startRateAtTarget * e^linearAdaptation, the
///         code forms linearAdaptation = ADJUSTMENT_SPEED * err * elapsed and
///         computes e^x with ExpLib.wExp, a second-order Taylor
///         polynomial after reducing x by ln 2 (Morpho's ExpLib). The adapter
///         runs the target utilisation of the deployed IRMs (90%) and the
///         scenario's speed per second in WAD, floored, as the deployed
///         ADJUSTMENT_SPEED is (3170979198376 = 100 per 365-day year at
///         0xC9A0109D925251E0E5380d6fB4b105408d16C23D), with the bounds set
///         wide (0 to 2^255 - 1) so they do not bind, since the scenario
///         measures the adaptation; the deployed contracts clamp to
///         [MIN_RATE_AT_TARGET, MAX_RATE_AT_TARGET]. The vault is idle for N
///         steps and updated once; the result is the stored rate at target.
contract LadderEuler is ILadderAdapter {
    int256 constant TARGET_UTILIZATION = 0.9e18;

    /// p = [rate0, x, util, step, halfLife, speed] in WAD (scenarios.json
    /// `order`): rate0 is the rate at target per second, util the
    /// utilisation, step in seconds, speed the adjustment speed per second.
    /// x and halfLife are the other models' inputs.
    function run(uint8 scenario, uint32 n, int256[] calldata p) external view returns (int256 raw, uint256 gasUsed) {
        if (scenario != Scenario.ADAPTIVE_RATE) revert Unsupported(scenario);
        if (p.length != 6) revert BadParamCount(scenario, p.length);
        if (p[0] <= 0 || p[0] > int256(uint256(type(uint144).max))) revert ParamOutOfRange(0);
        if (p[2] < 0 || p[2] > 1e18) revert ParamOutOfRange(2);
        if (p[3] < 0) revert ParamOutOfRange(3);
        if (p[5] < 0) revert ParamOutOfRange(5);
        uint256 g0 = gasleft();
        EulerAdaptiveCurve.Config memory c = EulerAdaptiveCurve.Config({
            TARGET_UTILIZATION: TARGET_UTILIZATION, MIN_RATE_AT_TARGET: 0, MAX_RATE_AT_TARGET: type(int256).max,
            CURVE_STEEPNESS: 4e18, ADJUSTMENT_SPEED: p[5]
        });
        int256 elapsed = int256(uint256(n)) * (p[3] / 1e18);
        raw = EulerAdaptiveCurve.endRateAtTarget(c, p[0], p[2], elapsed);
        gasUsed = g0 - gasleft();
    }

    /// Euler's IRM has no general op: every edge is Unsupported.
    function op(uint8 op_, int256[] calldata) external pure returns (int256, uint256) { revert Unsupported(op_); }
}

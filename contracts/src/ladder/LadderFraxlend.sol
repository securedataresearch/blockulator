// SPDX-License-Identifier: ISC
pragma solidity ^0.8.24;

import {ILadderAdapter, Scenario, BadParamCount, ParamOutOfRange, Unsupported} from "./ILadder.sol";

/// @title FraxlendRate
/// @notice FraxLend's VariableInterestRate V2 and the interest charge of
///         FraxlendPairCore._calculateInterest, transcribed with their
///         integer types and rounding from FraxFinance/fraxlend @ 2bed49d4
///         (src/contracts/VariableInterestRate.sol, FraxlendPairCore.sol;
///         ISC, Drake Evans, Frax Finance; see vendor/README.md). The
///         contract's immutables are the fields of Config. Every line below
///         is the deployed line with the immutable read from `c`.
library FraxlendRate {
    uint256 internal constant UTIL_PREC = 1e5;
    uint256 internal constant RATE_PREC = 1e18;

    struct Config {
        uint256 MIN_TARGET_UTIL;
        uint256 MAX_TARGET_UTIL;
        uint256 VERTEX_UTILIZATION;
        uint256 MIN_FULL_UTIL_RATE;
        uint256 MAX_FULL_UTIL_RATE;
        uint256 ZERO_UTIL_RATE;
        uint256 RATE_HALF_LIFE;
        uint256 VERTEX_RATE_PERCENT;
    }

    /// VariableInterestRate.getFullUtilizationInterest: below the target band
    /// F H / (H + d^2 dt), above it F (H + d^2 dt) / H, d the distance from
    /// the band normalised to 1 (18 decimals, floored), then clamped.
    function getFullUtilizationInterest(Config memory c, uint256 _deltaTime, uint256 _utilization, uint64 _fullUtilizationInterest)
        internal
        pure
        returns (uint64 _newFullUtilizationInterest)
    {
        if (_utilization < c.MIN_TARGET_UTIL) {
            // 18 decimals
            uint256 _deltaUtilization = ((c.MIN_TARGET_UTIL - _utilization) * 1e18) / c.MIN_TARGET_UTIL;
            // 36 decimals
            uint256 _decayGrowth = (c.RATE_HALF_LIFE * 1e36) + (_deltaUtilization * _deltaUtilization * _deltaTime);
            // 18 decimals
            _newFullUtilizationInterest = uint64((_fullUtilizationInterest * (c.RATE_HALF_LIFE * 1e36)) / _decayGrowth);
        } else if (_utilization > c.MAX_TARGET_UTIL) {
            // 18 decimals
            uint256 _deltaUtilization = ((_utilization - c.MAX_TARGET_UTIL) * 1e18) / (UTIL_PREC - c.MAX_TARGET_UTIL);
            // 36 decimals
            uint256 _decayGrowth = (c.RATE_HALF_LIFE * 1e36) + (_deltaUtilization * _deltaUtilization * _deltaTime);
            // 18 decimals
            _newFullUtilizationInterest = uint64((_fullUtilizationInterest * _decayGrowth) / (c.RATE_HALF_LIFE * 1e36));
        } else {
            _newFullUtilizationInterest = _fullUtilizationInterest;
        }
        if (_newFullUtilizationInterest > c.MAX_FULL_UTIL_RATE) {
            _newFullUtilizationInterest = uint64(c.MAX_FULL_UTIL_RATE);
        } else if (_newFullUtilizationInterest < c.MIN_FULL_UTIL_RATE) {
            _newFullUtilizationInterest = uint64(c.MIN_FULL_UTIL_RATE);
        }
    }

    /// VariableInterestRate.getNewRate: the two-slope curve through the vertex.
    function getNewRate(Config memory c, uint256 _deltaTime, uint256 _utilization, uint64 _oldFullUtilizationInterest)
        internal
        pure
        returns (uint64 _newRatePerSec, uint64 _newFullUtilizationInterest)
    {
        _newFullUtilizationInterest = getFullUtilizationInterest(c, _deltaTime, _utilization, _oldFullUtilizationInterest);
        uint256 _vertexInterest =
            (((_newFullUtilizationInterest - c.ZERO_UTIL_RATE) * c.VERTEX_RATE_PERCENT) / RATE_PREC) + c.ZERO_UTIL_RATE;
        if (_utilization < c.VERTEX_UTILIZATION) {
            _newRatePerSec = uint64(c.ZERO_UTIL_RATE + (_utilization * (_vertexInterest - c.ZERO_UTIL_RATE)) / c.VERTEX_UTILIZATION);
        } else {
            _newRatePerSec = uint64(
                _vertexInterest
                    + ((_utilization - c.VERTEX_UTILIZATION) * (_newFullUtilizationInterest - _vertexInterest))
                        / (UTIL_PREC - c.VERTEX_UTILIZATION)
            );
        }
    }

    /// FraxlendPairCore._calculateInterest's charge for the elapsed interval:
    /// the new rate (the one getNewRate returns at the end of the interval)
    /// times the interval, simple interest, floored.
    function interestEarned(uint256 _deltaTime, uint256 _totalBorrowAmount, uint64 _newRate) internal pure returns (uint256) {
        return (_deltaTime * _totalBorrowAmount * _newRate) / RATE_PREC;
    }
}

/// @title LadderFraxlend
/// @notice FraxLend's adaptive full-utilisation rate (FraxlendRate above), for
///         the adaptive-rate scenario only. FraxLend's documentation states the
///         adaptation as a half-life: at 0% utilisation the rates "decrease by
///         50% each half-life", at 100% "the increase will be 100% per
///         half-life", the documented model 2^(+-t/H). The code computes one
///         update after dt as F (1 + d^2 dt / H), or F / (1 + d^2 dt / H) below
///         the band, with d the normalised distance from the band. The
///         adapter runs the band of the deployed rate contract
///         0x18500cB1f2fE7a40eBdA393383A0B8548a31F261 (75% to 85%) and the
///         scenario's half-life floored to whole seconds, with the rate
///         clamps set wide (0 to 2^64 - 1) so they do not bind, since the
///         scenario measures the adaptation, not the bounds; the deployed
///         contract clamps to [MIN_FULL_UTIL_RATE, MAX_FULL_UTIL_RATE]. The
///         market is idle for N steps and updated once.
contract LadderFraxlend is ILadderAdapter {
    uint256 constant MIN_TARGET_UTIL = 75000;
    uint256 constant MAX_TARGET_UTIL = 85000;

    /// p = [rate0, x, util, step, halfLife, speed] in WAD (scenarios.json
    /// `order`): rate0 is the full-utilisation rate per second (uint64), util
    /// the utilisation as a fraction (to 1e5, as the pair computes it), step
    /// and halfLife in seconds. x and speed are the other models' inputs.
    function run(uint8 scenario, uint32 n, int256[] calldata p) external view returns (int256 raw, uint256 gasUsed) {
        if (scenario != Scenario.ADAPTIVE_RATE) revert Unsupported(scenario);
        if (p.length != 6) revert BadParamCount(scenario, p.length);
        if (p[0] < 0 || p[0] > int256(uint256(type(uint64).max))) revert ParamOutOfRange(0);
        if (p[2] < 0 || p[2] > 1e18) revert ParamOutOfRange(2);
        if (p[3] < 0) revert ParamOutOfRange(3);
        if (p[4] < 1e18) revert ParamOutOfRange(4);
        uint256 g0 = gasleft();
        FraxlendRate.Config memory c = FraxlendRate.Config({
            MIN_TARGET_UTIL: MIN_TARGET_UTIL, MAX_TARGET_UTIL: MAX_TARGET_UTIL, VERTEX_UTILIZATION: 0,
            MIN_FULL_UTIL_RATE: 0, MAX_FULL_UTIL_RATE: type(uint64).max, ZERO_UTIL_RATE: 0,
            RATE_HALF_LIFE: uint256(p[4]) / 1e18, VERTEX_RATE_PERCENT: 0
        });
        uint256 dt = uint256(n) * (uint256(p[3]) / 1e18);
        raw = int256(uint256(FraxlendRate.getFullUtilizationInterest(c, dt, uint256(p[2]) / 1e13, uint64(uint256(p[0])))));
        gasUsed = g0 - gasleft();
    }

    /// FraxLend's maths has no general op: every edge is Unsupported.
    function op(uint8 op_, int256[] calldata) external pure returns (int256, uint256) { revert Unsupported(op_); }
}

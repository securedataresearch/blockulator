// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ILadderAdapter, Scenario, BadParamCount, ParamOutOfRange, Unsupported} from "./ILadder.sol";
import {FixedPointMathLib} from "../../../lib/solady/src/utils/FixedPointMathLib.sol";

/// @title LadderMaker
/// @notice MakerDAO's rate accumulator in RAY (1e27): rpow(1 + rate, n, RAY),
///         exponentiation by squaring with half-up rounding at every step,
///         as pot.sol and jug.sol compound the Dai Savings Rate and the
///         stability fee per second. pot.sol is AGPL-3.0, so the algorithm
///         is taken from Solady's MIT `rpow`, which mirrors it step for
///         step; the balance is then rmul(balance, factor), floored, as
///         Maker does. Maker's model is discrete compounding, so this
///         adapter answers the daily, annual and per-second compounding
///         scenarios and reports Unsupported for the rest.
contract LadderMaker is ILadderAdapter {
    uint256 constant RAY = 1e27;

    function rmul(uint256 x, uint256 y) internal pure returns (uint256) { return x * y / RAY; }

    function _accrue(uint256 b0, uint256 rate, uint256 steps) internal pure returns (int256) {
        return int256(rmul(b0, FixedPointMathLib.rpow(RAY + rate, steps, RAY)));
    }

    /// p = [principal, rate] in RAY: rate per day (compound), per year (compound-annual) or per second (accrual-per-second).
    function run(uint8 scenario, uint32 n, int256[] calldata p) external view returns (int256 raw, uint256 gasUsed) {
        bool perSecond = scenario == Scenario.ACCRUAL_PER_SECOND;
        if (!(scenario == Scenario.COMPOUND || scenario == Scenario.COMPOUND_ANNUAL || perSecond)) revert Unsupported(scenario);
        if (p.length != 2) revert BadParamCount(scenario, p.length);
        if (p[0] < 0) revert ParamOutOfRange(0);
        if (p[1] < 0) revert ParamOutOfRange(1);
        uint256 g0 = gasleft();
        raw = _accrue(uint256(p[0]), uint256(p[1]), perSecond ? uint256(n) * 86400 : uint256(n));
        gasUsed = g0 - gasleft();
    }
}

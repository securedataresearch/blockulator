// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ILadderAdapter, Scenario, BadParamCount, ParamOutOfRange, Unsupported} from "./ILadder.sol";

/// @title LadderMorpho
/// @notice Morpho Blue's interest accrual in WAD: MathLib.wTaylorCompounded,
///         "the sum of the first three non-zero terms of a Taylor expansion
///         of e^(nx) - 1, to approximate a continuous compound interest
///         rate", applied as Morpho's _accrueInterest does, interest =
///         wMulDown(assets, wTaylorCompounded(borrowRate, elapsed)).
///         Transcribed from morpho-blue src/libraries/MathLib.sol
///         (GPL-2.0-or-later, not vendored; see vendor/README.md). The
///         borrow rate Morpho holds is per second in WAD, so the scenario
///         hands this adapter rateSec floored to 18 decimals: a 5% APR is
///         1,585,489,599 wei per second, ten significant digits before
///         any arithmetic. Only the continuous accrual scenario is answered.
contract LadderMorpho is ILadderAdapter {
    uint256 constant WAD = 1e18;

    function mulDivDown(uint256 x, uint256 y, uint256 d) internal pure returns (uint256) { return (x * y) / d; }
    function wMulDown(uint256 x, uint256 y) internal pure returns (uint256) { return mulDivDown(x, y, WAD); }

    /// MathLib.wTaylorCompounded.
    function wTaylorCompounded(uint256 x, uint256 n) internal pure returns (uint256) {
        uint256 firstTerm = x * n;
        uint256 secondTerm = mulDivDown(firstTerm, firstTerm, 2 * WAD);
        uint256 thirdTerm = mulDivDown(secondTerm, firstTerm, 3 * WAD);
        return firstTerm + secondTerm + thirdTerm;
    }

    /// p = [principal, rateAnnual, rateSec] in WAD; N days of accrual.
    function run(uint8 scenario, uint32 n, int256[] calldata p) external view returns (int256 raw, uint256 gasUsed) {
        if (scenario != Scenario.ACCRUAL_CONTINUOUS) revert Unsupported(scenario);
        if (p.length != 3) revert BadParamCount(scenario, p.length);
        if (p[0] < 0) revert ParamOutOfRange(0);
        if (p[2] < 0) revert ParamOutOfRange(2);
        uint256 g0 = gasleft();
        uint256 assets = uint256(p[0]);
        uint256 interest = wMulDown(assets, wTaylorCompounded(uint256(p[2]), uint256(n) * 86400));
        raw = int256(assets + interest);
        gasUsed = g0 - gasleft();
    }
}

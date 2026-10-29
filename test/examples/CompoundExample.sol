// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {BL127Lib} from "bl127/BL127Lib.sol";

/// @notice The ten-line example on blockulator.com/library: take a WAD
///         principal and a WAD per-step rate, accrue N steps in 127.128,
///         hand back a WAD. The only conversions are at the edges.
contract CompoundExample {
    function accrue(int256 principalWad, int256 rateWad, uint256 steps) external pure returns (int256 balanceWad) {
        int256 b = BL127Lib.fromFixed18(principalWad);
        int256 growth = BL127Lib.add(BL127Lib.ONE, BL127Lib.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = BL127Lib.mul(b, growth);
        }
        return BL127Lib.toFixed18(b);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IBL127} from "bl127/IBL127.sol";

/// @notice The deployed-form example on blockulator.com/library: the same
///         accrual through the shared BL127 object, so every contract on the
///         chain runs identical bytecode for the math.
contract StaticcallExample {
    IBL127 public constant BL127 = IBL127(0x0DF738d125677550a80A46BaF254386C66f96E0d);
    int256 internal constant ONE = int256(1) << 128;

    function accrue(int256 principalWad, int256 rateWad, uint256 steps) external view returns (int256 balanceWad) {
        int256 b = BL127.fromFixed18(principalWad);
        int256 growth = BL127.add(ONE, BL127.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = BL127.mul(b, growth);
        }
        return BL127.toFixed18(b);
    }
}

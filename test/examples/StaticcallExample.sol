// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IFP127} from "fp127/IFP127.sol";

/// @notice The deployed-form example on blockulator.com/library: the same
///         accrual through the shared FP127 object, so every contract on the
///         chain runs identical bytecode for the math.
contract StaticcallExample {
    IFP127 public constant FP127 = IFP127(0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1);
    int256 internal constant ONE = int256(1) << 128;

    function accrue(int256 principalWad, int256 rateWad, uint256 steps) external view returns (int256 balanceWad) {
        int256 b = FP127.fromFixed18(principalWad);
        int256 growth = FP127.add(ONE, FP127.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = FP127.mul(b, growth);
        }
        return FP127.toFixed18(b);
    }
}

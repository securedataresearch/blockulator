// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import "forge-std/Test.sol";
import {CheckExample} from "./CheckExample.sol";

/// @notice The figures on blockulator.com/library/checking, each asserted.
contract CheckTest is Test {
    function test_threeInputs() public pure {
        (int256 yours, int256 correct, int256 gap) = CheckExample.expWadGap(1e18);
        assertEq(yours, 2718281828459045235);
        assertEq(correct, 2718281828459045235);   // e = 2.718281828459045235360...
        assertEq(gap, 0);
        (yours, correct, gap) = CheckExample.expWadGap(3e18);
        assertEq(correct, 20085536923187667740);  // e^3 = 20.085536923187667740928...
        assertEq(gap, 1);
        (yours, correct, gap) = CheckExample.expWadGap(10e18);
        assertEq(correct, 22026465794806716516957); // e^10 = 22026.465794806716516957900...
        assertEq(gap, 23);
    }

    /// x = 0.05, 0.10, ..., 10.00: the page says 108 of these 200 differ and the largest gap is 222 wei.
    function test_scan() public pure {
        uint256 off;
        int256 worst;
        for (int256 i = 1; i <= 200; i++) {
            (,, int256 g) = CheckExample.expWadGap(i * 0.05e18);
            if (g != 0) off++;
            if (g < 0) g = -g;
            if (g > worst) worst = g;
        }
        assertEq(off, 108);
        assertEq(worst, 222);
    }
}

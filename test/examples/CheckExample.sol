// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {BL19Lib} from "bl19/BL19Lib.sol";
import {FixedPointMathLib} from "../../lib/solady/src/utils/FixedPointMathLib.sol";

/// @notice The example on blockulator.com/library/checking: keep your own
///         library and measure how far its answer is from the correctly
///         rounded one. Here the library is Solady and the function is expWad.
library CheckExample {
    /// @return yours   what your library returns, in WAD
    /// @return correct e^x from BL19 (71 digits), rounded down to 18 decimals
    /// @return gap     yours - correct, in wei
    function expWadGap(int256 xWad) internal pure returns (int256 yours, int256 correct, int256 gap) {
        yours = FixedPointMathLib.expWad(xWad);
        correct = BL19Lib.toFixed18Down(BL19Lib.exp(BL19Lib.fromFixed18(xWad)));
        gap = yours - correct;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {SD59x18, sd} from "../../../lib/prb-math/src/SD59x18.sol";
import * as M from "../../../lib/prb-math/src/sd59x18/Math.sol";

/// @title LadderPRB
/// @notice PRBMath SD59x18 (signed WAD). Checked native add/sub; mul, div,
///         exp, ln, sqrt, pow from the library.
contract LadderPRB is LadderBase {
    function _one() internal pure override returns (int256) { return 1e18; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) * 1e18; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return a + b; }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return a - b; }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return M.mul(sd(a), sd(b)).unwrap(); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return M.div(sd(a), sd(b)).unwrap(); }
    function _exp(int256 x) internal view override returns (int256) { return M.exp(sd(x)).unwrap(); }
    function _ln(int256 x) internal view override returns (int256) { return M.ln(sd(x)).unwrap(); }
    function _sqrt(int256 x) internal view override returns (int256) { return M.sqrt(sd(x)).unwrap(); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return M.pow(sd(x), sd(y)).unwrap(); }
    /// powu: PRBMath's exponentiation by squaring.
    function _powu(int256 x, int256 n) internal view override returns (int256) {
        if (n < 0) return M.div(sd(1e18), M.powu(sd(x), uint256(-n))).unwrap();
        return M.powu(sd(x), uint256(n)).unwrap();
    }
}

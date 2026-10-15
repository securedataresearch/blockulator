// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {FixedPointMathLib as S} from "../../../lib/solady/src/utils/FixedPointMathLib.sol";

/// @title LadderSolady
/// @notice Solady FixedPointMathLib in signed WAD (1e18). Checked native
///         add/sub, sMulWad/sDivWad, expWad/lnWad/powWad, sqrtWad.
contract LadderSolady is LadderBase {
    function _one() internal pure override returns (int256) { return 1e18; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) * 1e18; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return a + b; }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return a - b; }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return S.sMulWad(a, b); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return S.sDivWad(a, b); }
    function _exp(int256 x) internal view override returns (int256) { return S.expWad(x); }
    function _ln(int256 x) internal view override returns (int256) { return S.lnWad(x); }
    function _sqrt(int256 x) internal view override returns (int256) { require(x >= 0, "sqrt<0"); return int256(S.sqrtWad(uint256(x))); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return S.powWad(x, y); }
    function _lambertW0(int256 x) internal view override returns (int256) { return S.lambertW0Wad(x); }
    /// rpow: Solady's port of Maker's exponentiation by squaring, half up each step.
    function _powu(int256 x, int256 n) internal view override returns (int256) {
        require(x >= 0, "powu<0");
        if (n < 0) return S.sDivWad(1e18, int256(S.rpow(uint256(x), uint256(-n), 1e18)));
        return int256(S.rpow(uint256(x), uint256(n), 1e18));
    }
}

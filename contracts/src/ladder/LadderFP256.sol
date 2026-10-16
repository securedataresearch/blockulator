// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {FP256Lib} from "../fp256/FP256Lib.sol";

/// @title LadderFP256
/// @notice FP256, the 256-bit float, inline (FP256Lib). Each int256 is the
///         float's bit pattern (scripts/ladder/inputs.json encodes the
///         parameters to nearest); the sign is bit 255, so the sign test is
///         overridden. Every op the edges ask for is the library's own
///         (pow, log1p, expm1, erf, erfc, normCdf, both Lambert branches, powu
///         and compound); the scenarios' composite recipes run through them.
contract LadderFP256 is LadderBase {
    function _isNeg(int256 x) internal pure override returns (bool) { return x < 0; }
    function _one() internal pure override returns (int256) { return FP256Lib.ONE; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return FP256Lib.fromUint(u); }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return FP256Lib.add(a, b); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return FP256Lib.sub(a, b); }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return FP256Lib.mul(a, b); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return FP256Lib.div(a, b); }
    function _exp(int256 x) internal view override returns (int256) { return FP256Lib.exp(x); }
    function _ln(int256 x) internal view override returns (int256) { return FP256Lib.ln(x); }
    function _sqrt(int256 x) internal view override returns (int256) { return FP256Lib.sqrt(x); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return FP256Lib.pow(x, y); }
    function _log1p(int256 x) internal view override returns (int256) { return FP256Lib.log1p(x); }
    function _expm1(int256 x) internal view override returns (int256) { return FP256Lib.expm1(x); }
    function _erf(int256 x) internal view override returns (int256) { return FP256Lib.erf(x); }
    function _erfc(int256 x) internal view override returns (int256) { return FP256Lib.erfc(x); }
    function _normCdf(int256 x) internal view override returns (int256) { return FP256Lib.normCdf(x); }
    function _lambertW0(int256 x) internal view override returns (int256) { return FP256Lib.lambertW0(x); }
    function _lambertWm1(int256 x) internal view override returns (int256) { return FP256Lib.lambertWm1(x); }
    function _powu(int256 x, int256 n) internal view override returns (int256) { return FP256Lib.powu(x, n); }
    function _compoundOp(int256 rate, int256 n) internal view override returns (int256) { return FP256Lib.compound(rate, n); }
}

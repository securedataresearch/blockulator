// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {FP19Lib} from "../fp19/FP19Lib.sol";

/// @title LadderFP19
/// @notice FP19, the 256-bit float, inline (FP19Lib). Each int256 is the
///         float's bit pattern (scripts/ladder/inputs.json encodes the
///         parameters to nearest); the sign is bit 255, so the sign test is
///         overridden. Every op the edges ask for is the library's own
///         (pow, log1p, expm1, erf, erfc, normCdf, both Lambert branches, powu
///         and compound); per-second accrual is compound, as FP127's is; the
///         scenarios' other composite recipes run through them.
contract LadderFP19 is LadderBase {
    function _isNeg(int256 x) internal pure override returns (bool) { return x < 0; }
    function _one() internal pure override returns (int256) { return FP19Lib.ONE; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return FP19Lib.fromUint(u); }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return FP19Lib.add(a, b); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return FP19Lib.sub(a, b); }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return FP19Lib.mul(a, b); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return FP19Lib.div(a, b); }
    function _exp(int256 x) internal view override returns (int256) { return FP19Lib.exp(x); }
    function _ln(int256 x) internal view override returns (int256) { return FP19Lib.ln(x); }
    function _sqrt(int256 x) internal view override returns (int256) { return FP19Lib.sqrt(x); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return FP19Lib.pow(x, y); }
    function _log1p(int256 x) internal view override returns (int256) { return FP19Lib.log1p(x); }
    function _expm1(int256 x) internal view override returns (int256) { return FP19Lib.expm1(x); }
    function _erf(int256 x) internal view override returns (int256) { return FP19Lib.erf(x); }
    function _erfc(int256 x) internal view override returns (int256) { return FP19Lib.erfc(x); }
    function _normCdf(int256 x) internal view override returns (int256) { return FP19Lib.normCdf(x); }
    function _lambertW0(int256 x) internal view override returns (int256) { return FP19Lib.lambertW0(x); }
    function _lambertWm1(int256 x) internal view override returns (int256) { return FP19Lib.lambertWm1(x); }
    function _powu(int256 x, int256 n) internal view override returns (int256) { return FP19Lib.powu(x, n); }
    function _compoundOp(int256 rate, int256 n) internal view override returns (int256) { return FP19Lib.compound(rate, n); }
    /// compound: (1 + rs)^steps correctly rounded, without forming a rounded
    /// 1 + rs (a per-second rate needs 266 bits for it), as FP127 does with
    /// its compound; the default would round 1 + rs to 237 bits and raise it.
    function _accrue(int256 b, int256 rs, uint256 steps) internal view override returns (int256) { return _mul(b, FP19Lib.compound(rs, int256(steps))); }
}

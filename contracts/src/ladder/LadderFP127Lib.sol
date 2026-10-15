// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {FP127Lib} from "../fp127/FP127Lib.sol";

/// @title LadderFP127Lib
/// @notice The inline library form of FP127. Bit-identical to LadderFP127
///         (proven by test/fp127/EquivalenceOps.t.sol), without the call.
contract LadderFP127Lib is LadderBase {
    function _one() internal pure override returns (int256) { return int256(1) << 128; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) << 128; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return FP127Lib.add(a, b); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return FP127Lib.sub(a, b); }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return FP127Lib.mul(a, b); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return FP127Lib.div(a, b); }
    function _exp(int256 x) internal view override returns (int256) { return FP127Lib.exp(x); }
    function _ln(int256 x) internal view override returns (int256) { return FP127Lib.ln(x); }
    function _sqrt(int256 x) internal view override returns (int256) { return FP127Lib.sqrt(x); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return FP127Lib.pow(x, y); }
    /// compound: (1 + rs)^steps as one exact integer power, not exp(steps ln(1 + rs)).
    function _accrue(int256 b, int256 rs, uint256 steps) internal view override returns (int256) { return _mul(b, FP127Lib.compound(rs, int256(steps) << 128)); }
    function _pi() internal view override returns (int256) { return FP127Lib.pi(int256(5) << 128); }
    function _normCdf(int256 x) internal view override returns (int256) { return FP127Lib.normCdf(x); }
    function _lambertW0(int256 x) internal view override returns (int256) { return FP127Lib.lambertW0(x); }
    function _lambertWm1(int256 x) internal view override returns (int256) { return FP127Lib.lambertWm1(x); }
    function _log1p(int256 x) internal view override returns (int256) { return FP127Lib.log1p(x); }
    function _expm1(int256 x) internal view override returns (int256) { return FP127Lib.expm1(x); }
    function _powu(int256 x, int256 n) internal view override returns (int256) { return FP127Lib.powu(x, n << 128); }
    function _compoundOp(int256 rate, int256 n) internal view override returns (int256) { return FP127Lib.compound(rate, n << 128); }
    function _erf(int256 x) internal view override returns (int256) { return FP127Lib.erf(x); }
    function _erfc(int256 x) internal view override returns (int256) { return FP127Lib.erfc(x); }
}

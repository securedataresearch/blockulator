// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {FP127_ADDRESS} from "./ILadder.sol";
import {IFP127} from "../fp127/IFP127.sol";
import {FP127Lib} from "../fp127/FP127Lib.sol";

/// @title LadderFP127
/// @notice Every op is a staticcall to the deployed FP127 object, so this
///         adapter returns exactly what Sepolia returns. Reverts bubble.
contract LadderFP127 is LadderBase {
    IFP127 constant F = IFP127(FP127_ADDRESS);

    function _one() internal pure override returns (int256) { return int256(1) << 128; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) << 128; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return a + b; }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return a - b; }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return F.mul(a, b); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return F.div(a, b); }
    function _exp(int256 x) internal view override returns (int256) { return F.exp(x); }
    function _ln(int256 x) internal view override returns (int256) { return F.ln(x); }
    function _sqrt(int256 x) internal view override returns (int256) { return F.sqrt(x); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return F.pow(x, y); }
    /// compound: (1 + rs)^steps as one exact integer power, not exp(steps ln(1 + rs)).
    function _accrue(int256 b, int256 rs, uint256 steps) internal view override returns (int256) { return _mul(b, F.compound(rs, int256(steps) << 128)); }
    function _pi() internal pure override returns (int256) { return FP127Lib.PI; }
    function _normCdf(int256 x) internal view override returns (int256) { return F.normCdf(x); }
    function _lambertW0(int256 x) internal view override returns (int256) { return F.lambertW0(x); }
    function _lambertWm1(int256 x) internal view override returns (int256) { return F.lambertWm1(x); }
    function _log1p(int256 x) internal view override returns (int256) { return F.log1p(x); }
    function _expm1(int256 x) internal view override returns (int256) { return F.expm1(x); }
    function _powu(int256 x, int256 n) internal view override returns (int256) { return F.powu(x, n << 128); }
    function _compoundOp(int256 rate, int256 n) internal view override returns (int256) { return F.compound(rate, n << 128); }
    function _erf(int256 x) internal view override returns (int256) { return F.erf(x); }
    function _erfc(int256 x) internal view override returns (int256) { return F.erfc(x); }
}

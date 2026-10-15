// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {ParamOutOfRange} from "./ILadder.sol";
import {ABDKMathQuad as Q} from "../../../lib/abdk-libraries-solidity/ABDKMathQuad.sol";

/// @title LadderQuad
/// @notice ABDKMathQuad, IEEE 754 binary128: a 113-bit significand and a
///         15-bit exponent, so about 34 decimal digits anywhere between
///         1e-4932 and 1e4932. The only floating-point library in the
///         ladder, and the one with no floor. Each int256 holds the 128-bit
///         pattern of a bytes16 (scripts/ladder/inputs.json encodes the
///         parameters to nearest). The library returns NaN or infinity
///         where the others revert; the adapter turns those into a revert
///         so a cell is either a number or a reason. pow(x, y) is
///         exp(y ln x), as the library has no pow.
contract LadderQuad is LadderBase {
    error QuadNotFinite();

    function _p(int256[] calldata p, uint256 i) internal pure override returns (int256) {
        int256 x = p[i];
        if (x < 0 || x > int256(uint256(type(uint128).max))) revert ParamOutOfRange(i);
        return x;
    }
    function _q(int256 x) internal pure returns (bytes16) { return bytes16(uint128(uint256(x))); }
    function _r(bytes16 b) internal pure returns (int256) {
        if (Q.isNaN(b) || Q.isInfinity(b)) revert QuadNotFinite();
        return int256(uint256(uint128(b)));
    }
    function _isNeg(int256 x) internal pure override returns (bool) { return (uint256(x) >> 127) & 1 == 1; }
    function _one() internal pure override returns (int256) { return int256(uint256(uint128(Q.fromUInt(1)))); }
    function _fromUint(uint256 u) internal pure override returns (int256) { return _r(Q.fromUInt(u)); }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return _r(Q.add(_q(a), _q(b))); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return _r(Q.sub(_q(a), _q(b))); }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return _r(Q.mul(_q(a), _q(b))); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return _r(Q.div(_q(a), _q(b))); }
    function _exp(int256 x) internal view override returns (int256) { return _r(Q.exp(_q(x))); }
    function _ln(int256 x) internal view override returns (int256) { return _r(Q.ln(_q(x))); }
    function _sqrt(int256 x) internal view override returns (int256) { return _r(Q.sqrt(_q(x))); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return _r(Q.exp(Q.mul(_q(y), Q.ln(_q(x))))); }
}

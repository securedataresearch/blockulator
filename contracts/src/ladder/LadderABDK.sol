// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {ParamOutOfRange} from "./ILadder.sol";
import {ABDKMath64x64 as A} from "../../../lib/abdk-libraries-solidity/ABDKMath64x64.sol";

/// @title LadderABDK
/// @notice ABDKMath64x64, int128 with 64 fractional bits. ABDK has no
///         real-exponent pow, so pow(x, y) is exp(y ln x) as the library's
///         own README suggests.
contract LadderABDK is LadderBase {
    /// int128(x) truncates silently in Solidity, so the range is checked here.
    function _p(int256[] calldata p, uint256 i) internal pure override returns (int256) {
        int256 x = p[i];
        if (x != int256(int128(x))) revert ParamOutOfRange(i);
        return x;
    }
    function _one() internal pure override returns (int256) { return int256(1) << 64; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return A.fromUInt(u); }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return A.add(int128(a), int128(b)); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return A.sub(int128(a), int128(b)); }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return A.mul(int128(a), int128(b)); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return A.div(int128(a), int128(b)); }
    function _exp(int256 x) internal view override returns (int256) { return A.exp(int128(x)); }
    function _ln(int256 x) internal view override returns (int256) { return A.ln(int128(x)); }
    function _sqrt(int256 x) internal view override returns (int256) { return A.sqrt(int128(x)); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return A.exp(A.mul(int128(y), A.ln(int128(x)))); }
    /// pow(x, uint): ABDK's exponentiation by squaring.
    function _powu(int256 x, int256 n) internal view override returns (int256) {
        if (n < 0) return A.div(int128(int256(1) << 64), A.pow(int128(x), uint256(-n)));
        return A.pow(int128(x), uint256(n));
    }
}

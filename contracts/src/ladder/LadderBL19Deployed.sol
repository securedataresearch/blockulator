// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {BL19_ADDRESS, BL19E_ADDRESS, BL19N_ADDRESS, BL19S_ADDRESS} from "./ILadder.sol";
import {IBL19} from "../bl19/IBL19.sol";
import {IBL19E} from "../bl19/IBL19E.sol";
import {IBL19N} from "../bl19/IBL19N.sol";
import {IBL19S} from "../bl19/IBL19S.sol";
import {BL19Lib} from "../bl19/BL19Lib.sol";

/// @title LadderBL19Deployed
/// @notice LadderBL19's ops as staticcalls to BL19's deployed objects (the number, the elementary functions, the normal
///         distribution and Lambert W; add, sub and fromUint inline, see below), so the on-chain runners check the bytecode at BL19's addresses, as LadderBL127 checks BL127's.
///         The objects return the same words as BL19Lib (fuzzed equal), so every cell equals LadderBL19's; the
///         Bl19Deployed test checks that on every scenario. Reverts bubble.
contract LadderBL19Deployed is LadderBase {
    IBL19 constant N = IBL19(BL19_ADDRESS);
    IBL19E constant E = IBL19E(BL19E_ADDRESS);
    IBL19N constant D = IBL19N(BL19N_ADDRESS);
    IBL19S constant S = IBL19S(BL19S_ADDRESS);

    function _isNeg(int256 x) internal pure override returns (bool) { return x < 0; }
    function _one() internal pure override returns (int256) { return BL19Lib.ONE; }
    // LadderBase keeps these three pure, so they run inline (BL19Lib, the object's own source); every other op is a
    // staticcall to a deployed object.
    function _fromUint(uint256 u) internal pure override returns (int256) { return BL19Lib.fromUint(u); }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return BL19Lib.add(a, b); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return BL19Lib.sub(a, b); }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return N.mul(a, b); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return N.div(a, b); }
    function _sqrt(int256 x) internal view override returns (int256) { return N.sqrt(x); }
    function _exp(int256 x) internal view override returns (int256) { return E.exp(x); }
    function _ln(int256 x) internal view override returns (int256) { return E.ln(x); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return E.pow(x, y); }
    function _log1p(int256 x) internal view override returns (int256) { return E.log1p(x); }
    function _expm1(int256 x) internal view override returns (int256) { return E.expm1(x); }
    function _powu(int256 x, int256 n) internal view override returns (int256) { return E.powu(x, n); }
    function _compoundOp(int256 rate, int256 n) internal view override returns (int256) { return E.compound(rate, n); }
    /// compound: (1 + rs)^steps correctly rounded, as LadderBL19 does it.
    function _accrue(int256 b, int256 rs, uint256 steps) internal view override returns (int256) { return _mul(b, E.compound(rs, int256(steps))); }
    function _erf(int256 x) internal view override returns (int256) { return D.erf(x); }
    function _erfc(int256 x) internal view override returns (int256) { return D.erfc(x); }
    function _normCdf(int256 x) internal view override returns (int256) { return D.normCdf(x); }
    function _lambertW0(int256 x) internal view override returns (int256) { return S.lambertW0(x); }
    function _lambertWm1(int256 x) internal view override returns (int256) { return S.lambertWm1(x); }
}

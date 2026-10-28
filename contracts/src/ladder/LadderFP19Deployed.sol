// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {FP19_ADDRESS, FP19E_ADDRESS, FP19S_ADDRESS} from "./ILadder.sol";
import {IFP19} from "../fp19/IFP19.sol";
import {IFP19E} from "../fp19/IFP19E.sol";
import {IFP19S} from "../fp19/IFP19S.sol";
import {FP19Lib} from "../fp19/FP19Lib.sol";

/// @title LadderFP19Deployed
/// @notice LadderFP19's ops as staticcalls to FP19's deployed objects (the number, the elementary and the special
///         functions; add, sub and fromUint inline, see below), so the on-chain runners check the bytecode at FP19's addresses, as LadderFP127 checks FP127's.
///         The objects return the same words as FP19Lib (fuzzed equal), so every cell equals LadderFP19's; the
///         Fp19Deployed test checks that on every scenario. Reverts bubble.
contract LadderFP19Deployed is LadderBase {
    IFP19 constant N = IFP19(FP19_ADDRESS);
    IFP19E constant E = IFP19E(FP19E_ADDRESS);
    IFP19S constant S = IFP19S(FP19S_ADDRESS);

    function _isNeg(int256 x) internal pure override returns (bool) { return x < 0; }
    function _one() internal pure override returns (int256) { return FP19Lib.ONE; }
    // LadderBase keeps these three pure, so they run inline (FP19Lib, the object's own source); every other op is a
    // staticcall to a deployed object.
    function _fromUint(uint256 u) internal pure override returns (int256) { return FP19Lib.fromUint(u); }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return FP19Lib.add(a, b); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return FP19Lib.sub(a, b); }
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
    /// compound: (1 + rs)^steps correctly rounded, as LadderFP19 does it.
    function _accrue(int256 b, int256 rs, uint256 steps) internal view override returns (int256) { return _mul(b, E.compound(rs, int256(steps))); }
    function _erf(int256 x) internal view override returns (int256) { return S.erf(x); }
    function _erfc(int256 x) internal view override returns (int256) { return S.erfc(x); }
    function _normCdf(int256 x) internal view override returns (int256) { return S.normCdf(x); }
    function _lambertW0(int256 x) internal view override returns (int256) { return S.lambertW0(x); }
    function _lambertWm1(int256 x) internal view override returns (int256) { return S.lambertWm1(x); }
}

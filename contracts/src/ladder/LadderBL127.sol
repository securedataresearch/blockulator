// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {LadderBase} from "./LadderBase.sol";
import {BL127_ADDRESS, BL127E_ADDRESS, BL127N_ADDRESS, BL127S_ADDRESS} from "./ILadder.sol";
import {IBL127} from "../bl127/IBL127.sol";
import {IBL127E} from "../bl127/IBL127E.sol";
import {IBL127N} from "../bl127/IBL127N.sol";
import {IBL127S} from "../bl127/IBL127S.sol";
import {BL127Lib} from "../bl127/BL127Lib.sol";

/// @title LadderBL127
/// @notice Every op is a staticcall to the deployed BL127 objects (the number, the elementary functions, the normal
///         distribution and Lambert W), so this adapter returns exactly what the chain returns. Reverts bubble.
contract LadderBL127 is LadderBase {
    IBL127 constant F = IBL127(BL127_ADDRESS);
    IBL127E constant E = IBL127E(BL127E_ADDRESS);
    IBL127N constant D = IBL127N(BL127N_ADDRESS);
    IBL127S constant S = IBL127S(BL127S_ADDRESS);

    /// The runners warm BL127 itself; the objects the transcendentals call are touched here, outside the timed
    /// window, so no row pays a cold-account surcharge.
    function _warm() internal view override {
        require(BL127E_ADDRESS.code.length != 0 && BL127N_ADDRESS.code.length != 0 && BL127S_ADDRESS.code.length != 0,
            "no BL127 objects");
    }

    function _one() internal pure override returns (int256) { return int256(1) << 128; }
    function _fromUint(uint256 u) internal pure override returns (int256) { return int256(u) << 128; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return a + b; }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return a - b; }
    function _mul(int256 a, int256 b) internal view override returns (int256) { return F.mul(a, b); }
    function _div(int256 a, int256 b) internal view override returns (int256) { return F.div(a, b); }
    function _exp(int256 x) internal view override returns (int256) { return E.exp(x); }
    function _ln(int256 x) internal view override returns (int256) { return E.ln(x); }
    function _sqrt(int256 x) internal view override returns (int256) { return F.sqrt(x); }
    function _pow(int256 x, int256 y) internal view override returns (int256) { return E.pow(x, y); }
    /// compound: (1 + rs)^steps as one exact integer power, not exp(steps ln(1 + rs)).
    function _accrue(int256 b, int256 rs, uint256 steps) internal view override returns (int256) { return _mul(b, E.compound(rs, int256(steps) << 128)); }
    function _pi() internal pure override returns (int256) { return BL127Lib.PI; }
    function _normCdf(int256 x) internal view override returns (int256) { return D.normCdf(x); }
    function _lambertW0(int256 x) internal view override returns (int256) { return S.lambertW0(x); }
    function _lambertWm1(int256 x) internal view override returns (int256) { return S.lambertWm1(x); }
    function _log1p(int256 x) internal view override returns (int256) { return E.log1p(x); }
    function _expm1(int256 x) internal view override returns (int256) { return E.expm1(x); }
    function _powu(int256 x, int256 n) internal view override returns (int256) { return E.powu(x, n << 128); }
    function _compoundOp(int256 rate, int256 n) internal view override returns (int256) { return E.compound(rate, n << 128); }
    function _erf(int256 x) internal view override returns (int256) { return D.erf(x); }
    function _erfc(int256 x) internal view override returns (int256) { return D.erfc(x); }
}

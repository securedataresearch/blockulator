// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP19Lib} from "../../contracts/src/fp19/FP19Lib.sol";

/// @title IdealAccrual
/// @notice The formulas Aave v3 and Morpho Blue say they approximate,
///         computed directly with a full-precision library, for contrast
///         with the deployed approximations. Inputs are the same integers
///         the protocols hold (RAY rates and indexes, WAD rates, token
///         units); every result is the library's own number (no rounding to
///         token units), returned as its raw word.
abstract contract IdealAccrual {
    uint256 constant SPY = 365 days;

    function _u(uint256 x) internal pure virtual returns (int256);
    function _add(int256 a, int256 b) internal pure virtual returns (int256);
    function _sub(int256 a, int256 b) internal pure virtual returns (int256);
    function _mul(int256 a, int256 b) internal pure virtual returns (int256);
    function _div(int256 a, int256 b) internal pure virtual returns (int256);
    function _exp(int256 x) internal pure virtual returns (int256);
    function _expm1(int256 x) internal pure virtual returns (int256);
    function _ln(int256 x) internal pure virtual returns (int256);
    function _gt(int256 a, int256 b) internal pure virtual returns (bool);
    /// (1 + r)^n for an integer n.
    function _compound(int256 r, uint256 n) internal pure virtual returns (int256);

    /// scaled * index / 1e27, the balance a scaled amount stands for.
    function _balance(uint256 scaled, uint256 index) internal pure returns (int256) {
        return _mul(_u(scaled), _div(_u(index), _u(1e27)));
    }

    /// Aave's stated ideal for the variable borrow index, e^(rate per year * years).
    /// Returns (balance, interest) for `scaled` at `index0`.
    function aaveContinuous(uint256 rateRay, uint256 t, uint256 index0, uint256 scaled) external pure returns (int256, int256) {
        int256 b0 = _balance(scaled, index0);
        int256 x = _div(_mul(_u(rateRay), _u(t)), _mul(_u(1e27), _u(SPY)));
        int256 interest = _mul(b0, _expm1(x));
        return (_add(b0, interest), interest);
    }

    /// Per-second compounding of the per-second rate, (1 + rate/SPY)^t: the
    /// binomial Aave's doc comment names, and the APY its interface displays.
    function aavePerSecond(uint256 rateRay, uint256 t, uint256 index0, uint256 scaled) external pure returns (int256, int256) {
        int256 b0 = _balance(scaled, index0);
        int256 rs = _div(_u(rateRay), _mul(_u(1e27), _u(SPY)));
        int256 interest = _mul(b0, _sub(_compound(rs, t), _u(1)));
        return (_add(b0, interest), interest);
    }

    /// Morpho Blue with the AdaptiveCurveIrm, as the IRM's comments state the
    /// ideal: avg = 1/T * integral_0^T curve(r0 * e^(speed * t), err) dt with
    /// the rate at target held in [MIN, MAX], and interest = B * (e^(avg*T) - 1).
    /// Constants are the stated ones (50/year, 90%, steepness 4, 0.1%..200%/year).
    function morphoAdaptive(uint256 supply, uint256 borrow, uint256 r0Wad, uint256 t) external pure returns (int256, int256) {
        (int256 err, bool above) = _err(supply, borrow);
        int256 one = _u(1);
        // curve multiplier 1 + coeff * err: coeff = 3 above target, 3/4 below
        int256 mult = above ? _add(one, _mul(_u(3), err)) : _sub(one, _mul(_div(_u(3), _u(4)), _sub(_u(0), err)));
        int256 integral = _integral(err, above, _div(_u(r0Wad), _u(1e18)), _u(t));
        int256 interest = _mul(_u(borrow), _expm1(_mul(mult, integral)));
        return (_add(_u(borrow), interest), interest);
    }

    /// err = (u - 0.9)/0.1 above the target, (u - 0.9)/0.9 below it, from the
    /// exact integer numerator 10B - 9S so nothing cancels near the target.
    function _err(uint256 supply, uint256 borrow) internal pure returns (int256 err, bool above) {
        above = 10 * borrow > 9 * supply;
        if (above) err = _div(_u(10 * borrow - 9 * supply), _u(supply));
        else err = _sub(_u(0), _div(_u(9 * supply - 10 * borrow), _u(9 * supply)));
    }

    /// integral_0^T clamp(r0 e^(k t)) dt with k = 50/year * err, written with
    /// z = k T and the time to the bound in seconds, so no per-second k (about
    /// 1e-6 * err) is ever held on its own.
    function _integral(int256 err, bool above, int256 r0, int256 tt) internal pure returns (int256) {
        if (err == 0) return _mul(r0, tt);
        int256 k50 = _mul(_u(50), err); // per year, signed
        int256 bound = above ? _div(_u(2), _u(SPY)) : _div(_u(1), _mul(_u(1000), _u(SPY)));
        // seconds until the rate at target reaches its bound: ln(bound / r0) * SPY / (50 err)
        int256 ts = _div(_mul(_ln(_div(bound, r0)), _u(SPY)), k50);
        // past ts: (bound - r0)/k up to ts, then the bound until T
        if (_gt(tt, ts)) return _add(_div(_mul(_sub(bound, r0), _u(SPY)), k50), _mul(bound, _sub(tt, ts)));
        int256 z = _div(_mul(k50, tt), _u(SPY));
        return _mul(_mul(r0, tt), _div(_expm1(z), z));
    }

    /// Morpho Blue at a fixed per-second WAD rate: B * (e^(rate * t) - 1).
    function morphoFixed(uint256 rateWad, uint256 t, uint256 borrow) external pure returns (int256, int256) {
        int256 interest = _mul(_u(borrow), _expm1(_div(_mul(_u(rateWad), _u(t)), _u(1e18))));
        return (_add(_u(borrow), interest), interest);
    }
}

contract IdealFP127 is IdealAccrual {
    function _u(uint256 x) internal pure override returns (int256) { return int256(x) << 128; }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return FP127Lib.add(a, b); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return FP127Lib.sub(a, b); }
    function _mul(int256 a, int256 b) internal pure override returns (int256) { return FP127Lib.mul(a, b); }
    function _div(int256 a, int256 b) internal pure override returns (int256) { return FP127Lib.div(a, b); }
    function _exp(int256 x) internal pure override returns (int256) { return FP127Lib.exp(x); }
    function _expm1(int256 x) internal pure override returns (int256) { return FP127Lib.expm1(x); }
    function _ln(int256 x) internal pure override returns (int256) { return FP127Lib.ln(x); }
    function _gt(int256 a, int256 b) internal pure override returns (bool) { return a > b; }
    function _compound(int256 r, uint256 n) internal pure override returns (int256) { return FP127Lib.compound(r, int256(n) << 128); }
}

contract IdealFP19 is IdealAccrual {
    function _u(uint256 x) internal pure override returns (int256) { return FP19Lib.fromUint(x); }
    function _add(int256 a, int256 b) internal pure override returns (int256) { return FP19Lib.add(a, b); }
    function _sub(int256 a, int256 b) internal pure override returns (int256) { return FP19Lib.sub(a, b); }
    function _mul(int256 a, int256 b) internal pure override returns (int256) { return FP19Lib.mul(a, b); }
    function _div(int256 a, int256 b) internal pure override returns (int256) { return FP19Lib.div(a, b); }
    function _exp(int256 x) internal pure override returns (int256) { return FP19Lib.exp(x); }
    /// FP19 release two has no expm1; e^x - 1 by subtraction keeps about
    /// 71 + log10(x) digits, which is still beyond anything measured here.
    function _expm1(int256 x) internal pure override returns (int256) { return FP19Lib.sub(FP19Lib.exp(x), FP19Lib.ONE); }
    function _ln(int256 x) internal pure override returns (int256) { return FP19Lib.ln(x); }
    function _gt(int256 a, int256 b) internal pure override returns (bool) { return FP19Lib.cmp(a, b) > 0; }
    function _compound(int256 r, uint256 n) internal pure override returns (int256) { return FP19Lib.pow(FP19Lib.add(FP19Lib.ONE, r), FP19Lib.fromUint(n)); }
}

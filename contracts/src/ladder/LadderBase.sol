// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ILadderAdapter, Scenario, BadParamCount} from "./ILadder.sol";

/// @title LadderBase
/// @notice The scenario loops, written once against seven virtual ops and a
///         parameter accessor. Each adapter supplies the ops in its library's
///         representation; the loops never convert between steps.
///
/// Every scenario is N identical steps. Parameters arrive in `p`, already
/// floored into the adapter's representation (scripts/ladder/inputs.json);
/// results leave raw. Gas is measured around the scenario function, so it
/// covers the parameter reads and the loop but not the call into the adapter.
abstract contract LadderBase is ILadderAdapter {
    error UnknownScenario(uint8 scenario);

    // ---- the representation, supplied by each adapter ---------------------

    function _one() internal pure virtual returns (int256);
    function _fromUint(uint256 u) internal pure virtual returns (int256);
    /// p[i], range-checked by adapters whose type is narrower than int256.
    function _p(int256[] calldata p, uint256 i) internal pure virtual returns (int256) { return p[i]; }
    function _add(int256 a, int256 b) internal pure virtual returns (int256);
    function _sub(int256 a, int256 b) internal pure virtual returns (int256);
    function _mul(int256 a, int256 b) internal view virtual returns (int256);
    function _div(int256 a, int256 b) internal view virtual returns (int256);
    function _exp(int256 x) internal view virtual returns (int256);
    function _ln(int256 x) internal view virtual returns (int256);
    function _sqrt(int256 x) internal view virtual returns (int256);
    function _pow(int256 x, int256 y) internal view virtual returns (int256);

    // ---- composite ops a library may have natively -------------------------

    /// b (1 + rs)^steps, discrete compounding over `steps` periods. Default:
    /// the real-exponent pow. FP127 overrides with compound (an exact
    /// integer power); Maker answers with rpow.
    function _accrue(int256 b, int256 rs, uint256 steps) internal view virtual returns (int256) {
        return _mul(b, _pow(_add(_one(), rs), _fromUint(steps)));
    }

    /// b e^(r t) with t = days / 365, continuous accrual. Default: exp.
    /// Aave and Morpho answer with their three-term expansions, from the
    /// annual and the per-second rate respectively.
    function _accrueCont(int256 b, int256 rateAnnual, int256 /*rateSec*/, uint32 days_) internal view virtual returns (int256) {
        return _mul(b, _exp(_mul(rateAnnual, _div(_fromUint(days_), _fromUint(365)))));
    }

    // ---- dispatch ----------------------------------------------------------

    function run(uint8 scenario, uint32 n, int256[] calldata p) external view returns (int256 raw, uint256 gasUsed) {
        _need(scenario, p, _arity(scenario));
        uint256 g0 = gasleft();
        if (scenario == Scenario.COMPOUND) raw = _compound(p, n);
        else if (scenario == Scenario.COMPOUND_POW) raw = _compoundPow(p, n);
        else if (scenario == Scenario.BONDING_SQRT) raw = _bondingSqrt(p, n);
        else if (scenario == Scenario.ROUNDTRIP) raw = _roundtrip(p, n);
        else if (scenario == Scenario.AMORTISE) raw = _amortise(p, n);
        else if (scenario == Scenario.GEO_MEAN) raw = _geoMean(n);
        else if (scenario == Scenario.BLACK_SCHOLES_CHAIN) raw = _blackScholesChain(p, n);
        else if (scenario == Scenario.CUMULATIVE_PRODUCT) raw = _cumulativeProduct(p, n);
        else if (scenario == Scenario.COMPOUND_ANNUAL) raw = _compound(p, n);
        else if (scenario == Scenario.ACCRUAL_PER_SECOND) raw = _accrualPerSecond(p, n);
        else if (scenario == Scenario.ACCRUAL_CONTINUOUS) raw = _accrualContinuous(p, n);
        else revert UnknownScenario(scenario);
        gasUsed = g0 - gasleft();
    }

    /// Parameter count per scenario, the `order` in scenarios.json.
    function _arity(uint8 scenario) internal pure returns (uint256) {
        if (scenario == Scenario.COMPOUND || scenario == Scenario.COMPOUND_POW || scenario == Scenario.COMPOUND_ANNUAL) return 2;
        if (scenario == Scenario.BONDING_SQRT) return 2;
        if (scenario == Scenario.ROUNDTRIP) return 1;
        if (scenario == Scenario.AMORTISE) return 3;
        if (scenario == Scenario.GEO_MEAN) return 0;
        if (scenario == Scenario.BLACK_SCHOLES_CHAIN) return 6;
        if (scenario == Scenario.CUMULATIVE_PRODUCT) return 1;
        if (scenario == Scenario.ACCRUAL_PER_SECOND) return 2;
        if (scenario == Scenario.ACCRUAL_CONTINUOUS) return 3;
        revert UnknownScenario(scenario);
    }

    function _need(uint8 scenario, int256[] calldata p, uint256 k) internal pure {
        if (p.length != k) revert BadParamCount(scenario, p.length);
    }

    // ---- scenarios ---------------------------------------------------------

    /// p = [principal, rate]. b = b * (1 + r), N times.
    function _compound(int256[] calldata p, uint32 n) internal view returns (int256 b) {
        b = _p(p, 0);
        int256 g = _add(_one(), _p(p, 1));
        for (uint32 i; i < n; i++) b = _mul(b, g);
    }

    /// p = [principal, rate]. b0 * (1 + r)^N with a real-exponent pow.
    function _compoundPow(int256[] calldata p, uint32 n) internal view returns (int256) {
        int256 g = _add(_one(), _p(p, 1));
        return _mul(_p(p, 0), _pow(g, _fromUint(n)));
    }

    /// p = [supply, unit]. cost += sqrt(s); s += unit, N times.
    function _bondingSqrt(int256[] calldata p, uint32 n) internal view returns (int256 cost) {
        int256 s = _p(p, 0);
        int256 unit = _p(p, 1);
        for (uint32 i; i < n; i++) {
            cost = _add(cost, _sqrt(s));
            s = _add(s, unit);
        }
    }

    /// p = [x0]. x = exp(ln(x)), N times.
    function _roundtrip(int256[] calldata p, uint32 n) internal view returns (int256 x) {
        x = _p(p, 0);
        for (uint32 i; i < n; i++) x = _exp(_ln(x));
    }

    /// p = [principal, rate, payment]. b = b * (1 + r) - payment, N times.
    function _amortise(int256[] calldata p, uint32 n) internal view returns (int256 b) {
        b = _p(p, 0);
        int256 g = _add(_one(), _p(p, 1));
        int256 pay = _p(p, 2);
        for (uint32 i; i < n; i++) b = _sub(_mul(b, g), pay);
    }

    /// L += ln((i + 2) / (i + 1)) for i = 1..N; g = exp(L / N).
    function _geoMean(uint32 n) internal view returns (int256) {
        int256 L;
        for (uint32 i = 1; i <= n; i++) {
            L = _add(L, _ln(_div(_fromUint(uint256(i) + 2), _fromUint(uint256(i) + 1))));
        }
        return _exp(_div(L, _fromUint(n)));
    }

    /// p = [spot, strike, sigma, T, r, tick]. acc += d1(S); S += tick, N times, with
    /// d1 = (ln(S / K) + (r + sigma^2 / 2) T) / (sigma sqrt(T)).
    function _blackScholesChain(int256[] calldata p, uint32 n) internal view returns (int256 acc) {
        int256 S = _p(p, 0);
        int256 K = _p(p, 1);
        int256 sigma = _p(p, 2);
        int256 T = _p(p, 3);
        int256 tick = _p(p, 5);
        int256 drift = _mul(_add(_p(p, 4), _div(_mul(sigma, sigma), _fromUint(2))), T);
        for (uint32 i; i < n; i++) {
            int256 d1 = _div(_add(_ln(_div(S, K)), drift), _mul(sigma, _sqrt(T)));
            acc = _add(acc, d1);
            S = _add(S, tick);
        }
    }

    /// p = [eps]. prod = prod * (1 + eps_i), eps_i = +eps for odd i and -eps for even i, i = 1..N.
    function _cumulativeProduct(int256[] calldata p, uint32 n) internal view returns (int256 prod) {
        prod = _one();
        int256 up = _add(_one(), _p(p, 0));
        int256 dn = _sub(_one(), _p(p, 0));
        for (uint32 i = 1; i <= n; i++) prod = _mul(prod, i & 1 == 1 ? up : dn);
    }

    /// p = [principal, rateSec]. b0 (1 + rs)^(N * 86400): N days of per-second compounding.
    function _accrualPerSecond(int256[] calldata p, uint32 n) internal view returns (int256) {
        return _accrue(_p(p, 0), _p(p, 1), uint256(n) * 86400);
    }

    /// p = [principal, rateAnnual, rateSec]. b0 e^(r N / 365): N days of continuous accrual.
    function _accrualContinuous(int256[] calldata p, uint32 n) internal view returns (int256) {
        return _accrueCont(_p(p, 0), _p(p, 1), _p(p, 2), n);
    }
}

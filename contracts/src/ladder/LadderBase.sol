// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ILadderAdapter, Scenario, Op, BadParamCount, Unsupported} from "./ILadder.sol";

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

    /// Touch, outside the timed window, any contract the ops call, so the
    /// measurement does not include a cold-account surcharge. The Vyper
    /// adapter (LadderSnekmate) touches its library and LadderFP127 FP127's
    /// other objects; the inline adapters call nothing, and the runner warms
    /// the FP127 object itself.
    function _warm() internal view virtual {}

    // ---- composite ops a library may have natively -------------------------

    /// Sign test in the representation. Every grid is a signed integer;
    /// binary128 keeps its sign in bit 127 and overrides this.
    function _isNeg(int256 x) internal pure virtual returns (bool) { return x < 0; }

    /// pi, by Ramanujan's series through the library's own mul, div and
    /// sqrt (nine terms, eight digits each, so a 71-digit form is not bounded
    /// by it; the recipe of docs/benchmarks/pi.md). FP127 overrides it with
    /// its constant, FP127Lib.PI.
    function _pi() internal view virtual returns (int256) {
        int256 one = _one();
        int256 c = one;
        int256 s = _fromUint(0);
        for (uint256 k; k < 9; k++) {
            s = _add(s, _mul(c, _fromUint(1103 + 26390 * k)));
            uint256 k4 = 4 * k;
            c = _div(_mul(c, _fromUint((k4 + 1) * (k4 + 2) * (k4 + 3) * (k4 + 4))), _fromUint((k + 1) ** 4 * 24591257856));
        }
        int256 invpi = _div(_mul(_mul(_fromUint(2), _sqrt(_fromUint(2))), s), _fromUint(9801));
        return _div(one, invpi);
    }

    /// The standard normal distribution function Phi(x) = erfc(-x / sqrt2) / 2,
    /// by the same recipe FP127's normCdf uses, through the library's own
    /// ops: the all-positive series (2/sqrt(pi)) e^(-y^2) y sum (2y^2)^k/(2k+1)!!
    /// for y <= 4, summed until a term no longer changes the sum, and the
    /// continued fraction e^(-y^2) / (sqrt(pi) K), K = y + (1/2)/(y + 1/(y + ...)),
    /// evaluated backward from depth 120, beyond. pi comes from _pi. Where
    /// the library's exp underflows (e^(-y^2) below its floor, y above
    /// about 6.4 on an 18-decimal grid) the tail is zero or a revert.
    function _normCdf(int256 x) internal view virtual returns (int256) {
        int256 two = _fromUint(2);
        bool neg = _isNeg(x);
        int256 y = _div(neg ? _sub(_fromUint(0), x) : x, _sqrt(two));
        int256 v = y <= _fromUint(4) ? _erfcSeries(y) : _erfcFraction(y);
        int256 half = _div(v, two);
        return neg ? half : _sub(_one(), half);
    }

    /// erfc(y) for 0 <= y <= 4 as 1 - erf(y), erf by the all-positive series.
    function _erfcSeries(int256 y) internal view returns (int256) { return _sub(_one(), _erfSeries(y)); }

    /// erf(y) for 0 <= y <= 4 by the all-positive series.
    function _erfSeries(int256 y) internal view returns (int256) {
        int256 one = _one();
        int256 d = _mul(_fromUint(2), _mul(y, y));
        int256 term = one;
        int256 s = one;
        for (uint256 k = 1; k < 200; k++) {
            term = _div(_mul(term, d), _fromUint(2 * k + 1));
            int256 s2 = _add(s, term);
            if (s2 == s) break;
            s = s2;
        }
        int256 e = _exp(_sub(_fromUint(0), _mul(y, y)));
        return _mul(_mul(_mul(_div(_fromUint(2), _sqrt(_pi())), e), y), s);
    }

    // ---- the one-shot ops of the edges dataset -----------------------------
    // Defaults are what a user of the library would write; adapters override
    // where the library has the op natively.

    function _lambertW0(int256) internal view virtual returns (int256) { revert Unsupported(Op.W0); }
    function _lambertWm1(int256) internal view virtual returns (int256) { revert Unsupported(Op.WM1); }
    function _log1p(int256 x) internal view virtual returns (int256) { return _ln(_add(_one(), x)); }
    function _expm1(int256 x) internal view virtual returns (int256) { return _sub(_exp(x), _one()); }
    /// x^n for an integer n, through the real-exponent pow.
    function _powu(int256 x, int256 n) internal view virtual returns (int256) {
        bool neg = n < 0;
        int256 r = _pow(x, _fromUint(uint256(neg ? -n : n)));
        return neg ? _div(_one(), r) : r;
    }
    function _compoundOp(int256 rate, int256 n) internal view virtual returns (int256) { return _powu(_add(_one(), rate), n); }
    function _erf(int256 x) internal view virtual returns (int256) {
        bool neg = _isNeg(x);
        int256 y = neg ? _sub(_fromUint(0), x) : x;
        int256 v = y <= _fromUint(4) ? _erfSeries(y) : _sub(_one(), _erfcFraction(y));
        return neg ? _sub(_fromUint(0), v) : v;
    }
    function _erfc(int256 x) internal view virtual returns (int256) {
        bool neg = _isNeg(x);
        int256 y = neg ? _sub(_fromUint(0), x) : x;
        int256 v = y <= _fromUint(4) ? _erfcSeries(y) : _erfcFraction(y);
        return neg ? _sub(_fromUint(2), v) : v;
    }

    function op(uint8 o, int256[] calldata a) external view returns (int256 raw, uint256 gasUsed) {
        uint256 want = (o == Op.POW || o == Op.MUL || o == Op.DIV || o == Op.COMPOUND || o == Op.POWU) ? 2 : 1;
        if (a.length != want) revert BadParamCount(o, a.length);
        _warm();
        uint256 g0 = gasleft();
        if (o == Op.LN) raw = _ln(_p(a, 0));
        else if (o == Op.EXP) raw = _exp(_p(a, 0));
        else if (o == Op.SQRT) raw = _sqrt(_p(a, 0));
        else if (o == Op.POW) raw = _pow(_p(a, 0), _p(a, 1));
        else if (o == Op.MUL) raw = _mul(_p(a, 0), _p(a, 1));
        else if (o == Op.DIV) raw = _div(_p(a, 0), _p(a, 1));
        else if (o == Op.W0) raw = _lambertW0(_p(a, 0));
        else if (o == Op.WM1) raw = _lambertWm1(_p(a, 0));
        else if (o == Op.LOG1P) raw = _log1p(_p(a, 0));
        else if (o == Op.EXPM1) raw = _expm1(_p(a, 0));
        else if (o == Op.COMPOUND) raw = _compoundOp(_p(a, 0), a[1]);
        else if (o == Op.POWU) raw = _powu(_p(a, 0), a[1]);
        else if (o == Op.ERF) raw = _erf(_p(a, 0));
        else if (o == Op.ERFC) raw = _erfc(_p(a, 0));
        else if (o == Op.NORMCDF) raw = _normCdf(_p(a, 0));
        else revert Unsupported(o);
        gasUsed = g0 - gasleft();
    }

    /// erfc(y) for y > 4 by the continued fraction, backward from depth 120.
    function _erfcFraction(int256 y) internal view returns (int256) {
        int256 two = _fromUint(2);
        int256 f = y;
        for (uint256 i = 120; i > 0; i--) f = _add(y, _div(_div(_fromUint(i), two), f));
        int256 e = _exp(_sub(_fromUint(0), _mul(y, y)));
        return _div(e, _mul(_sqrt(_pi()), f));
    }

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
        _warm();
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
        else if (scenario == Scenario.DEEP_TAIL_OPTION) raw = _deepTailOption(p, n);
        else if (scenario == Scenario.DECAY) raw = _decay(p, n);
        else if (scenario == Scenario.ADAPTIVE_RATE) raw = _adaptiveRate(p, n);
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
        if (scenario == Scenario.DEEP_TAIL_OPTION) return 6;
        if (scenario == Scenario.DECAY) return 1;
        if (scenario == Scenario.ADAPTIVE_RATE) return 6;
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

    /// p = [spot, strike, sigma, T, r, tick]. S = S (1 - tick) N times, then
    /// the Black-Scholes call price S N(d1) - K e^(-rT) N(d2) at that spot.
    function _deepTailOption(int256[] calldata p, uint32 n) internal view returns (int256) {
        int256 S = _p(p, 0);
        int256 g = _sub(_one(), _p(p, 5));
        for (uint32 i; i < n; i++) S = _mul(S, g);
        return _callPrice(S, _p(p, 1), _p(p, 2), _p(p, 3), _p(p, 4));
    }

    /// Black-Scholes: S N(d1) - K e^(-rT) N(d2), d1 = (ln(S/K) + (r + sigma^2/2) T) / (sigma sqrt T).
    function _callPrice(int256 S, int256 K, int256 sigma, int256 T, int256 r) internal view returns (int256) {
        int256 vs = _mul(sigma, _sqrt(T));
        int256 d1 = _div(_add(_ln(_div(S, K)), _mul(_add(r, _div(_mul(sigma, sigma), _fromUint(2))), T)), vs);
        int256 disc = _mul(K, _exp(_sub(_fromUint(0), _mul(r, T))));
        return _sub(_mul(S, _normCdf(d1)), _mul(disc, _normCdf(_sub(d1, vs))));
    }

    /// p = [eps]. D = D e^(-eps) N times; the result is the share released,
    /// 1 - D, which is where an 18-decimal e^(-eps) that rounds to one
    /// shows.
    function _decay(int256[] calldata p, uint32 n) internal view returns (int256) {
        int256 one = _one();
        int256 eps = _p(p, 0);
        int256 D = one;
        for (uint32 i; i < n; i++) D = _mul(D, _exp(_sub(_fromUint(0), eps)));
        return _sub(one, D);
    }

    /// p = [rate0, x, util, step, halfLife, speed]: the rate an adaptive
    /// model holds after N idle steps, as the protocols document it,
    /// rate0 e^(x N) with x = speed * err * step the exponent per step. The
    /// last four parameters are the protocols' own inputs (LadderFraxlend,
    /// LadderEuler); a library computes the documented model from the first two.
    function _adaptiveRate(int256[] calldata p, uint32 n) internal view returns (int256) {
        return _mul(_p(p, 0), _exp(_mul(_p(p, 1), _fromUint(n))));
    }
}

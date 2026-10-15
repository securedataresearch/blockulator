// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP127Harness} from "../base/FP127Harness.sol";
import {IFP127} from "../../contracts/src/fp127/IFP127.sol";

/// @title Behaviour
/// @notice Known values, identities and shortcut dispatch for the Yul build.
///         Carried over from the Huff-era suites (FP127Test, core/*) and the
///         property tests that used to live in EquivalenceOps. Independent of
///         the Huff baseline and of the oracle; these are the facts a reader
///         can check by hand.
contract Behaviour is FP127Harness {
    int256 constant E_RAW = 924983374546220337150911035843336795079;   // floor(e * 2^128)
    int256 constant PI_RAW = 1068362306129446170624574138052468108800; // floor(pi * 2^128)... approx, checked loosely

    function _absd(int256 a, int256 b) internal pure returns (int256) { return a > b ? a - b : b - a; }

    // ------------------------------------------------------------------
    // Known values
    // ------------------------------------------------------------------

    function test_conversions() public view {
        assertEq(obj.fromFixed18(1e18), ONE);
        assertEq(obj.toFixed18(ONE), 1e18);
        assertEq(obj.fromFixed18(-5e17), -ONE / 2);
        assertEq(obj.toFixed18(-ONE / 2), -5e17);
        assertEq(obj.fromFixed18(0), 0);
        assertEq(obj.toFixed18(1), 0);           // one ULP is below 1e-18
        assertEq(obj.toFixed18(-1), -1);         // floor, not trunc
    }

    function test_arithmetic_known() public view {
        assertEq(obj.add(2 * ONE, 3 * ONE), 5 * ONE);
        assertEq(obj.sub(2 * ONE, 3 * ONE), -ONE);
        assertEq(obj.mul(2 * ONE, 3 * ONE), 6 * ONE);
        assertEq(obj.mul(-2 * ONE, 3 * ONE), -6 * ONE);
        assertEq(obj.div(3 * ONE, 2 * ONE), ONE + ONE / 2);
        assertEq(obj.div(-3 * ONE, 2 * ONE), -(ONE + ONE / 2));
        assertEq(obj.div(ONE, 3 * ONE), ONE / 3);
        assertEq(obj.inv(4 * ONE), ONE / 4);
        // rounding direction: mul floors, div truncates
        assertEq(obj.mul(-ONE, ONE + 1), -(ONE + 1));
        assertEq(obj.mul(-(ONE + 1), ONE / 2), -(ONE / 2) - 1);
        assertEq(obj.div(-(ONE + 1), 2 * ONE), -(ONE / 2));
    }

    function test_transcendental_known() public view {
        int256 e = obj.exp(ONE);
        assertLe(_absd(e, E_RAW), 4, "e");
        assertEq(obj.exp(0), ONE);
        assertEq(obj.exp2(10 * ONE), 1024 * ONE);
        assertEq(obj.exp2(-ONE), ONE / 2);
        assertEq(obj.exp2(0), ONE);
        assertLe(_absd(obj.exp10(2 * ONE), 100 * ONE), 256, "exp10(2) via log2(10) is not exact");
        assertEq(obj.log2(1024 * ONE), 10 * ONE);
        assertEq(obj.log2(ONE / 4), -2 * ONE);
        assertEq(obj.log2(ONE), 0);
        assertEq(obj.ln(ONE), 0);
        assertLe(_absd(obj.ln(e), ONE), 8, "ln e");
        assertLe(_absd(obj.log10(1000 * ONE), 3 * ONE), 8, "log10 1000");
        assertEq(obj.sqrt(4 * ONE), 2 * ONE);
        assertEq(obj.sqrt(ONE / 4), ONE / 2);
        assertEq(obj.sqrt(0), 0);
    }

    function test_integer_ops_known() public view {
        assertEq(obj.floor(-ONE / 2), -ONE);
        assertEq(obj.floor(ONE + ONE / 2), ONE);
        assertEq(obj.ceil(-ONE / 2), 0);
        assertEq(obj.ceil(ONE + 1), 2 * ONE);
        assertEq(obj.round(ONE / 2), ONE);
        assertEq(obj.round(-ONE / 2), 0);
        assertEq(obj.round(ONE / 2 - 1), 0);
        assertEq(obj.frac(-ONE / 2), ONE / 2);
        assertEq(obj.sign(-5), -ONE);
        assertEq(obj.sign(0), 0);
        assertEq(obj.sign(1), ONE);
        assertEq(obj.factorial(5 * ONE + 1), 120 * ONE);
        assertEq(obj.factorial(0), ONE);
        // pi by Ramanujan's series: about eight digits a term, the format's floor at five
        int256 PI = 1069028584064966747859680373161870783300; // floor(pi * 2^128)
        assertLe(_absd(obj.pi(ONE), PI), PI / 10000000, "one term: 7 digits");
        assertLe(_absd(obj.pi(2 * ONE), PI), PI / 1000000000000000, "two terms: 15 digits");
        assertLe(_absd(obj.pi(5 * ONE), PI), 400, "five terms: within 400 ULP (36 digits)");
        assertEq(obj.pi(6 * ONE), obj.pi(5 * ONE), "a sixth term changes nothing");
        _expectRevert(abi.encodeCall(IFP127.pi, (0)), IFP127.OutOfRange.selector, "pi(0): no terms");
        _expectRevert(abi.encodeCall(IFP127.pi, (8 * ONE)), IFP127.OutOfRange.selector, "pi(8)");
        _expectRevert(abi.encodeCall(IFP127.pi, (-1)), IFP127.OutOfRange.selector, "pi(-1)");
        assertEq(obj.factorial(33 * ONE), int256(8683317618811886495518194401280000000) * ONE);
        assertEq(obj.gcd(12 * ONE, 18 * ONE), 6 * ONE);
        assertEq(obj.gcd(-12 * ONE, 18 * ONE), 6 * ONE);
        assertEq(obj.gcd(-4 * ONE, -4 * ONE), 4 * ONE);
        assertEq(obj.gcd(7 * ONE, 0), 7 * ONE);
        assertEq(obj.log2Up(5 * ONE), 3 * ONE);
        assertEq(obj.log2Up(8 * ONE), 3 * ONE);
        assertEq(obj.log2Up(ONE / 3), -1 * ONE);
    }

    function test_selection_known() public view {
        assertEq(obj.min(-ONE, ONE), -ONE);
        assertEq(obj.max(-ONE, ONE), ONE);
        assertEq(obj.clamp(5 * ONE, 0, ONE), ONE);
        assertEq(obj.clamp(-5 * ONE, 0, ONE), 0);
        assertEq(obj.clamp(ONE / 2, 0, ONE), ONE / 2);
        assertEq(obj.avg(ONE, 3 * ONE), 2 * ONE);
        assertEq(obj.avg(MAX, MAX), MAX);
        assertEq(obj.avg(MIN, MIN), MIN);
        assertEq(obj.avg(-ONE, 0), -ONE / 2);
        assertEq(obj.dist(-ONE, ONE), 2 * ONE);
        assertEq(obj.zeroFloorSub(ONE, 2 * ONE), 0);
        assertEq(obj.zeroFloorSub(2 * ONE, ONE), ONE);
        assertEq(obj.lerp(0, 10 * ONE, ONE / 2), 5 * ONE);
        assertEq(obj.lerp(10 * ONE, 0, ONE / 4), 7 * ONE + ONE / 2);
        assertEq(obj.hypot(3 * ONE, 4 * ONE), 5 * ONE);
        assertEq(obj.gavg(2 * ONE, 8 * ONE), 4 * ONE);
    }

    function test_lambert_known() public view {
        assertEq(obj.lambertW0(0), 0);
        assertEq(obj.lambertW0(ONE), 0x91304d7c74b2ba5eafddaa6286dc28e1);
        assertEq(obj.lambertW0(2 * ONE), 0xda445aab89e28ccbe8ac8e1abd5cd1db);
        // W(-1/4) = -0.35740295618138890306881110405590475...
        assertLe(_absd(obj.lambertW0(-ONE / 4), -121617923873943470405355803408166885968), 16);
        // W(e) = 1 exactly
        assertLe(_absd(obj.lambertW0(E_RAW), ONE), 16);
    }

    int256 constant NEG_INV_E = -int256(0x5e2d58d8b3bcdf1abadec7829054f90d);

    function test_lambertm1_known() public view {
        // -INV_E_RAW is floor(2^128 / e) negated, a fraction of an ULP inside
        // the domain, where W = -1 - sqrt(2 e d) is about -1 - 2^-63. Both
        // branches carry ~63 bits there (infinite slope), so compare loosely.
        assertLe(_absd(obj.lambertWm1(NEG_INV_E), -ONE), ONE >> 60);
        // W_{-1}(-2 e^-2) = -2, W_{-1}(-3 e^-3) = -3
        int256 x2 = obj.mul(-2 * ONE, obj.exp(-2 * ONE));
        assertLe(_absd(obj.lambertWm1(x2), -2 * ONE), 16);
        int256 x3 = obj.mul(-3 * ONE, obj.exp(-3 * ONE));
        assertLe(_absd(obj.lambertWm1(x3), -3 * ONE), 16);
        // the smallest negative input is still in the domain
        int256 wmin = obj.lambertWm1(-1);
        assertLt(wmin, -93 * ONE);
        assertGt(wmin, -94 * ONE);
    }

    function test_lambertm1_domain() public view {
        _expectRevert(abi.encodeCall(IFP127.lambertWm1, (0)), IFP127.OutOfRange.selector, "lambertWm1(0)");
        _expectRevert(abi.encodeCall(IFP127.lambertWm1, (ONE)), IFP127.OutOfRange.selector, "lambertWm1(1)");
        _expectRevert(abi.encodeCall(IFP127.lambertWm1, (MAX)), IFP127.OutOfRange.selector, "lambertWm1(MAX)");
        _expectRevert(abi.encodeCall(IFP127.lambertWm1, (NEG_INV_E - 1)), IFP127.OutOfRange.selector, "lambertWm1(-1/e - 1)");
        _expectRevert(abi.encodeCall(IFP127.lambertWm1, (MIN)), IFP127.OutOfRange.selector, "lambertWm1(MIN)");
    }

    // ------------------------------------------------------------------
    // Shortcut dispatch: the shortcut must equal the direct op
    // ------------------------------------------------------------------

    function testFuzz_pow_shortcuts(int256 x, uint8 which) public view {
        x = bound(x, ONE / 1000, 1000 * ONE);
        uint8 k = which % 7;
        int256 y; int256 direct;
        if (k == 0) { y = ONE; direct = x; }
        else if (k == 1) { y = 2 * ONE; direct = obj.mul(x, x); }
        else if (k == 2) { y = 3 * ONE; direct = obj.mul(obj.mul(x, x), x); }
        else if (k == 3) { y = 4 * ONE; int256 x2 = obj.mul(x, x); direct = obj.mul(x2, x2); }
        else if (k == 4) { y = ONE / 2; direct = obj.sqrt(x); }
        else if (k == 5) { y = ONE / 4; direct = obj.sqrt(obj.sqrt(x)); }
        else { y = -ONE; direct = obj.inv(x); }
        assertEq(obj.pow(x, y), direct, "y shortcut");
        int256 ysm = bound(int256(uint256(which)), -30 * ONE, 30 * ONE);
        assertEq(obj.pow(2 * ONE, ysm), obj.exp2(ysm), "x=2 shortcut");
        assertEq(obj.pow(10 * ONE, ysm), obj.exp10(ysm), "x=10 shortcut");
    }

    function test_pow_edge_cases() public view {
        assertEq(obj.pow(0, 0), ONE);
        assertEq(obj.pow(0, 5 * ONE), 0);
        assertEq(obj.pow(ONE, 123 * ONE), ONE);
        assertEq(obj.pow(3 * ONE, 2 * ONE), 9 * ONE);
        assertEq(obj.pow(2 * ONE, 10 * ONE), 1024 * ONE);
        assertEq(obj.pow(10 * ONE, 2 * ONE), 100 * ONE);
        assertEq(obj.pow(27 * ONE, ONE / 2), obj.sqrt(27 * ONE));
    }

    function test_cbrt_shortcuts() public view {
        assertEq(obj.cbrt(8 * ONE), 2 * ONE);
        assertEq(obj.cbrt(27 * ONE), 3 * ONE);
        assertEq(obj.cbrt(64 * ONE), 4 * ONE);
        assertEq(obj.cbrt(0), 0);
        assertEq(obj.cbrt(-27 * ONE), -obj.pow(27 * ONE, obj.div(ONE, 3 * ONE)));
    }

    function test_log2_powers_of_two() public view {
        for (int256 k = -120; k <= 126; k += 3) {
            int256 x = k >= 0 ? ONE << uint256(k) : ONE >> uint256(-k);
            assertEq(obj.log2(x), k * ONE);
            assertEq(obj.log2Up(x), k * ONE);
        }
    }

    // ------------------------------------------------------------------
    // Properties
    // ------------------------------------------------------------------

    function testFuzz_prop_fixed18_roundtrip(int256 w) public view {
        w = bound(w, -(int256(1) << 127), (int256(1) << 127) - 1);
        int256 back = obj.toFixed18(obj.fromFixed18(w));
        assertLe(back, w);
        assertLe(w - back, 1);
    }

    function testFuzz_prop_mul_one(int256 a) public view {
        assertEq(obj.mul(a, ONE), a);
        assertEq(obj.mul(ONE, a), a);
        assertEq(obj.div(a, ONE), a);
    }

    function testFuzz_prop_mul_commutes(int256 a, int256 b) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.mul, (a, b))),
                    _try(address(obj), abi.encodeCall(IFP127.mul, (b, a))), "mul commutes");
    }

    function testFuzz_prop_mul_then_div(int256 a, int256 b) public view {
        a = bound(a, -(int256(1) << 180), int256(1) << 180);
        b = bound(b, ONE, int256(1) << 200);
        if (a & 1 == 1) b = -b;
        int256 back = obj.div(obj.mul(a, b), b);
        assertLe(_absd(back, a), 2);
    }

    function testFuzz_prop_exp_ln(int256 x) public view {
        x = bound(x, ONE / 1000, 1000 * ONE);
        int256 back = obj.exp(obj.ln(x));
        assertLe(_absd(back, x), (x >> 110) + 8);
    }

    function testFuzz_prop_sqrt_square(int256 x) public view {
        x = bound(x, 0, int256(1) << 250);
        int256 s = obj.sqrt(x);
        assertLe(obj.mul(s, s), x);
        assertGe(obj.mul(s + 1, s + 1), x);
    }

    function testFuzz_prop_lambertW0_inverse(int256 x) public view {
        x = bound(x, -int256(0x5e2d58d8b3bcdf1abadec7829054f90d) / 2, int256(1) << 160);
        int256 w = obj.lambertW0(x);
        int256 back = obj.mul(w, obj.exp(w));
        int256 tol = (x < 0 ? -x : x) >> 112;
        assertLe(_absd(back, x), tol + 8);
    }

    /// On the secondary branch w + ln(-w) = ln(-x), w <= -1, and W_{-1} <= W_0.
    function testFuzz_prop_lambertWm1_inverse(int256 x) public view {
        x = bound(x, NEG_INV_E, -1);
        int256 w = obj.lambertWm1(x);
        assertLe(w, -ONE + (ONE >> 60));
        assertLe(w, obj.lambertW0(x) + (ONE >> 60));
        int256 lhs = w + obj.ln(-w);
        int256 rhs = obj.ln(-x);
        int256 tol = (w < 0 ? -w : w) >> 100;
        assertLe(_absd(lhs, rhs), tol + 8);
    }

    function testFuzz_prop_floor_ceil(int256 x) public view {
        x = bound(x, MIN + ONE, MAX - ONE);
        int256 f = obj.floor(x);
        int256 c = obj.ceil(x);
        assertLe(f, x);
        assertGe(c, x);
        assertEq(f & (ONE - 1), 0);
        assertEq(c & (ONE - 1), 0);
        assertEq(obj.frac(x), x - f);
    }

    // ------------------------------------------------------------------
    // v4: integer powers, near one, hyperbolic, the error function
    // ------------------------------------------------------------------

    function test_powu_known() public view {
        assertEq(obj.powu(2 * ONE, 10 * ONE), 1024 * ONE, "2^10 exact");
        assertEq(obj.powu(2 * ONE, -3 * ONE), ONE / 8, "2^-3 exact");
        assertEq(obj.powu(-3 * ONE, 3 * ONE), -27 * ONE, "(-3)^3 exact");
        assertEq(obj.powu(-3 * ONE, 2 * ONE), 9 * ONE, "(-3)^2 exact");
        assertEq(obj.powu(ONE + ONE / 2, 2 * ONE), 2 * ONE + ONE / 4, "1.5^2 exact");
        assertEq(obj.powu(ONE / 2, 200 * ONE), 0, "2^-200 is below the grid");
        assertEq(obj.powu(2 * ONE, 126 * ONE), ONE << 126, "2^126 is the largest power of two");
        assertEq(obj.powu(7 * ONE, 0), ONE, "n = 0");
        assertEq(obj.powu(0, 0), ONE, "0^0 = 1");
        assertEq(obj.powu(0, 5 * ONE), 0, "0^5");
        assertEq(obj.powu(ONE, 1000000 * ONE), ONE, "1^n");
        assertEq(obj.powu(-ONE, 1000001 * ONE), -ONE, "(-1)^odd");
        assertEq(obj.powu(3 * ONE, 2 * ONE + ONE / 2), 9 * ONE, "the exponent is floored");
        // 1.1^10 = 2.5937424601, a decimal that is not on the grid: within one ULP
        int256 b = ONE + ONE / 10;
        int256 ten = obj.mul(obj.mul(obj.mul(b, b), obj.mul(b, b)), obj.mul(obj.mul(b, b), obj.mul(obj.mul(b, b), obj.mul(b, b))));
        assertLe(_absd(obj.powu(b, 10 * ONE), ten), 12, "1.1^10 against the mul chain");
        _expectRevert(abi.encodeCall(IFP127.powu, (2 * ONE, 127 * ONE)), IFP127.Overflow.selector, "2^127");
        _expectRevert(abi.encodeCall(IFP127.powu, (10 * ONE, 39 * ONE)), IFP127.Overflow.selector, "10^39");
        _expectRevert(abi.encodeCall(IFP127.powu, (0, -ONE)), IFP127.DivisionByZero.selector, "0^-1");
    }

    /// (1 + r)^n through the mantissa path against the daily compounding
    /// loop of the ladder's headline cell: $10,000 at 10% APR for a year.
    function test_compound_known() public view {
        int256 r = 93228045731763962592705371899114578; // floor(0.1 / 365 * 2^128)
        int256 g = ONE + r;
        int256 b = ONE;
        for (uint256 i; i < 365; i++) b = obj.mul(b, g);
        // the loop floors 365 times; compound rounds once
        assertLe(_absd(obj.compound(r, 365 * ONE), b), 400, "a year of daily compounding");
        assertGe(obj.compound(r, 365 * ONE), b, "the floored loop sits below");
        assertEq(obj.compound(0, 1000 * ONE), ONE, "zero rate");
        assertEq(obj.compound(-ONE, 3 * ONE), 0, "rate -1 empties the balance");
        _expectRevert(abi.encodeCall(IFP127.compound, (-ONE, -ONE)), IFP127.DivisionByZero.selector, "compound(-1, -1)");
        _expectRevert(abi.encodeCall(IFP127.compound, (MAX, ONE)), IFP127.Overflow.selector, "1 + MAX");
    }

    function test_near_one_known() public view {
        assertEq(obj.log1p(0), 0);
        assertEq(obj.expm1(0), 0);
        // below 2^-64 the curvature is below the grid: log1p(x) = expm1(x) = x
        assertEq(obj.expm1(1 << 60), 1 << 60, "expm1 of 2^-68");
        assertLe(_absd(obj.log1p(1 << 60), 1 << 60), 1, "log1p of 2^-68");
        assertEq(obj.log1p(ONE), obj.ln(2 * ONE), "log1p(1) = ln 2");
        assertEq(obj.expm1(ONE), obj.exp(ONE) - ONE, "expm1(1) = e - 1");
        assertEq(obj.expm1(-100 * ONE), -ONE, "expm1 far below");
        _expectRevert(abi.encodeCall(IFP127.log1p, (-ONE)), IFP127.OutOfRange.selector, "log1p(-1)");
        _expectRevert(abi.encodeCall(IFP127.log1p, (MIN)), IFP127.OutOfRange.selector, "log1p(MIN)");
        _expectRevert(abi.encodeCall(IFP127.log1p, (MAX)), IFP127.Overflow.selector, "log1p(MAX)");
        _expectRevert(abi.encodeCall(IFP127.expm1, (89 * ONE)), IFP127.Overflow.selector, "expm1(89)");
    }

    function test_hyperbolic_known() public view {
        assertEq(obj.sinh(0), 0);
        assertEq(obj.cosh(0), ONE);
        assertEq(obj.tanh(0), 0);
        assertEq(obj.atanh(0), 0);
        assertEq(obj.tanh(50 * ONE), ONE, "tanh saturates");
        assertEq(obj.tanh(-50 * ONE), -ONE);
        assertEq(obj.tanh(-ONE / 10), -obj.tanh(ONE / 10), "tanh is odd");
        assertEq(obj.sinh(-3 * ONE), -obj.sinh(3 * ONE), "sinh is odd");
        assertEq(obj.cosh(-3 * ONE), obj.cosh(3 * ONE), "cosh is even");
        // atanh(1/2) = ln(3) / 2
        assertLe(_absd(obj.atanh(ONE / 2), obj.ln(3 * ONE) / 2), 2);
        // cosh(88) is the largest the format holds
        assertGt(obj.cosh(88 * ONE), 0);
        _expectRevert(abi.encodeCall(IFP127.sinh, (89 * ONE)), IFP127.Overflow.selector, "sinh(89)");
        _expectRevert(abi.encodeCall(IFP127.cosh, (-89 * ONE)), IFP127.Overflow.selector, "cosh(-89)");
        _expectRevert(abi.encodeCall(IFP127.atanh, (ONE)), IFP127.OutOfRange.selector, "atanh(1)");
        _expectRevert(abi.encodeCall(IFP127.atanh, (-ONE)), IFP127.OutOfRange.selector, "atanh(-1)");
        _expectRevert(abi.encodeCall(IFP127.atanh, (MAX)), IFP127.OutOfRange.selector, "atanh(MAX)");
    }

    function test_erf_known() public view {
        assertEq(obj.erf(0), 0);
        assertEq(obj.erfc(0), ONE);
        assertEq(obj.normCdf(0), ONE / 2);
        // erf(1) = 0.84270079294971486934122063508260925...
        assertLe(_absd(obj.erf(ONE), 286756220431080668183289216208796350931), 2);
        assertEq(obj.erf(-ONE), -obj.erf(ONE), "erf is odd");
        assertEq(obj.erf(10 * ONE), ONE, "erf saturates at 10");
        assertEq(obj.erf(-10 * ONE), -ONE);
        assertEq(obj.erfc(10 * ONE), 0, "erfc(10) is below the grid");
        assertEq(obj.erfc(-10 * ONE), 2 * ONE);
        assertEq(obj.erfc(93 * ONE / 10), 1, "erfc(9.3) = 1.65e-39 is one ULP");
        assertEq(obj.erfc(94 * ONE / 10), 0, "erfc(9.4) rounds to zero");
        // the tails of the normal distribution, where an 18-decimal N(d) is zero
        assertEq(obj.normCdf(-13 * ONE), 2, "Phi(-13) = 6.1e-39 is two ULPs");
        assertEq(obj.normCdf(-14 * ONE), 0, "Phi(-14) rounds to zero");
        assertEq(obj.normCdf(14 * ONE), ONE);
        // Phi(-9) = 1.1285884059538405e-19
        assertLe(_absd(obj.normCdf(-9 * ONE), 38403873405750185486), 2);
        // the series/fraction seam at 4 and the scaled seam of normCdf
        assertLe(_absd(obj.erf(4 * ONE + 1), obj.erf(4 * ONE)), 2, "continuous across x = 4");
        assertLe(_absd(obj.erfc(4 * ONE + 1), obj.erfc(4 * ONE)), 2);
    }

    function testFuzz_prop_erf_complement(int256 x) public view {
        x = bound(x, -12 * ONE, 12 * ONE);
        assertLe(_absd(obj.erf(x) + obj.erfc(x), ONE), 2, "erf + erfc = 1");
        assertLe(_absd(obj.normCdf(x) + obj.normCdf(-x), ONE), 2, "Phi(x) + Phi(-x) = 1");
        assertGe(obj.erfc(x), 0);
        assertLe(obj.normCdf(x), ONE);
    }

    function testFuzz_prop_near_one(int256 x) public view {
        x = bound(x, -ONE, ONE);
        assertLe(_absd(obj.expm1(x), obj.exp(x) - ONE), 2, "expm1 against exp");
        if (x > -ONE) assertEq(obj.log1p(x), obj.ln(ONE + x), "log1p is ln(1 + x)");
        // the round trip holds to the grid
        assertLe(_absd(obj.log1p(obj.expm1(x)), x), 2, "log1p(expm1(x)) = x");
    }

    function testFuzz_prop_hyperbolic(int256 x) public view {
        x = bound(x, -40 * ONE, 40 * ONE);
        int256 s = obj.sinh(x);
        int256 c = obj.cosh(x);
        // cosh^2 - sinh^2 = 1, with the products' own rounding allowed for
        int256 tol = (c >> 120) + 8;
        assertLe(_absd(obj.mul(c, c) - obj.mul(s, s), ONE), tol, "cosh^2 - sinh^2");
        assertLe(_absd(obj.tanh(x), obj.div(s, c)), 4, "tanh = sinh / cosh");
        int256 t = obj.tanh(x);
        if (t > -ONE && t < ONE) {
            int256 back = obj.atanh(t);
            // atanh amplifies one ULP of tanh by 1 / (1 - tanh^2) = cosh^2
            int256 tol2 = obj.mul(c, c) >> 120;
            assertLe(_absd(back, x), tol2 + 4, "atanh(tanh(x)) = x");
        }
    }

    function testFuzz_prop_powu_squaring(int256 x, uint8 n) public view {
        x = bound(x, -4 * ONE, 4 * ONE);
        uint256 k = uint256(n) % 12;
        int256 p = obj.powu(x, int256(k) * ONE);
        int256 q = ONE;
        for (uint256 i; i < k; i++) q = obj.mul(q, x);
        // k - 1 floors in the chain against one rounding;
        // each floor in the chain is scaled by the later factors, up to 4^k
        assertLe(_absd(p, q), (int256(k) + 2) << (2 * k), "powu against the mul chain");
    }
}

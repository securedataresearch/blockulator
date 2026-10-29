// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP127Harness} from "../base/FP127Harness.sol";
import {IFP127} from "../../contracts/src/fp127/IFP127.sol";
import {IFP127E} from "../../contracts/src/fp127/IFP127E.sol";
import {IFP127H} from "../../contracts/src/fp127/IFP127H.sol";
import {IFP127S} from "../../contracts/src/fp127/IFP127S.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";

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
        int256 e = objE.exp(ONE);
        assertLe(_absd(e, E_RAW), 4, "e");
        assertEq(objE.exp(0), ONE);
        assertEq(objE.exp2(10 * ONE), 1024 * ONE);
        assertEq(objE.exp2(-ONE), ONE / 2);
        assertEq(objE.exp2(0), ONE);
        assertLe(_absd(objE.exp10(2 * ONE), 100 * ONE), 256, "exp10(2) via log2(10) is not exact");
        assertEq(objE.log2(1024 * ONE), 10 * ONE);
        assertEq(objE.log2(ONE / 4), -2 * ONE);
        assertEq(objE.log2(ONE), 0);
        assertEq(objE.ln(ONE), 0);
        assertLe(_absd(objE.ln(e), ONE), 8, "ln e");
        assertLe(_absd(objE.log10(1000 * ONE), 3 * ONE), 8, "log10 1000");
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
        assertEq(FP127Lib.PI, 1069028584064966747859680373161870783301, "PI is pi * 2^128 to the nearest integer");
        assertEq(obj.factorial(33 * ONE), int256(8683317618811886495518194401280000000) * ONE);
        assertEq(objE.log2Up(5 * ONE), 3 * ONE);
        assertEq(objE.log2Up(8 * ONE), 3 * ONE);
        assertEq(objE.log2Up(ONE / 3), -1 * ONE);
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
        assertEq(objS.lambertW0(0), 0);
        assertEq(objS.lambertW0(ONE), 0x91304d7c74b2ba5eafddaa6286dc28e1);
        assertEq(objS.lambertW0(2 * ONE), 0xda445aab89e28ccbe8ac8e1abd5cd1db);
        // W(-1/4) = -0.35740295618138890306881110405590475...
        assertLe(_absd(objS.lambertW0(-ONE / 4), -121617923873943470405355803408166885968), 16);
        // W(e) = 1 exactly
        assertLe(_absd(objS.lambertW0(E_RAW), ONE), 16);
    }

    int256 constant NEG_INV_E = -int256(0x5e2d58d8b3bcdf1abadec7829054f90d);

    function test_lambertm1_known() public view {
        // -INV_E_RAW is floor(2^128 / e) negated, a fraction of an ULP inside
        // the domain, where W = -1 - sqrt(2 e d) is about -1 - 2^-63. Both
        // branches carry ~63 bits there (infinite slope), so compare loosely.
        assertLe(_absd(objS.lambertWm1(NEG_INV_E), -ONE), ONE >> 60);
        // W_{-1}(-2 e^-2) = -2, W_{-1}(-3 e^-3) = -3
        int256 x2 = obj.mul(-2 * ONE, objE.exp(-2 * ONE));
        assertLe(_absd(objS.lambertWm1(x2), -2 * ONE), 16);
        int256 x3 = obj.mul(-3 * ONE, objE.exp(-3 * ONE));
        assertLe(_absd(objS.lambertWm1(x3), -3 * ONE), 16);
        // the smallest negative input is still in the domain
        int256 wmin = objS.lambertWm1(-1);
        assertLt(wmin, -93 * ONE);
        assertGt(wmin, -94 * ONE);
    }

    function test_lambertm1_domain() public view {
        _expectRevert(abi.encodeCall(IFP127S.lambertWm1, (0)), IFP127.OutOfRange.selector, "lambertWm1(0)");
        _expectRevert(abi.encodeCall(IFP127S.lambertWm1, (ONE)), IFP127.OutOfRange.selector, "lambertWm1(1)");
        _expectRevert(abi.encodeCall(IFP127S.lambertWm1, (MAX)), IFP127.OutOfRange.selector, "lambertWm1(MAX)");
        _expectRevert(abi.encodeCall(IFP127S.lambertWm1, (NEG_INV_E - 1)), IFP127.OutOfRange.selector, "lambertWm1(-1/e - 1)");
        _expectRevert(abi.encodeCall(IFP127S.lambertWm1, (MIN)), IFP127.OutOfRange.selector, "lambertWm1(MIN)");
    }

    // ------------------------------------------------------------------
    // Shortcut dispatch
    // ------------------------------------------------------------------

    /// v5 keeps four pow shortcuts, all correctly rounded: y = 1 (x itself),
    /// y = 2 (the 512-bit square, rounded once), x = 2 (exp2) and x = 10
    /// (exp10). v4's y in {3, 4, 1/2, 1/4, -1} floored through mul, sqrt or
    /// div; they now take the general path, which is the nearest word, so
    /// they sit within the old composites' own error of them.
    function testFuzz_pow_shortcuts(int256 x, uint8 which) public view {
        x = bound(x, ONE / 1000, 1000 * ONE);
        uint8 k = which % 7;
        int256 got;
        if (k == 0) { assertEq(objE.pow(x, ONE), x, "y = 1"); }
        else if (k == 1) {
            got = objE.pow(x, 2 * ONE);
            uint256 lo;
            unchecked { lo = uint256(x) * uint256(x); }
            assertEq(got, obj.mul(x, x) + int256((lo >> 127) & 1), "y = 2 is the rounded square");
        } else {
            int256 y; int256 direct;
            if (k == 2) { y = 3 * ONE; direct = obj.mul(obj.mul(x, x), x); }
            else if (k == 3) { y = 4 * ONE; int256 x2 = obj.mul(x, x); direct = obj.mul(x2, x2); }
            else if (k == 4) { y = ONE / 2; direct = obj.sqrt(x); }
            else if (k == 5) { y = ONE / 4; direct = obj.sqrt(obj.sqrt(x)); }
            else { y = -ONE; direct = obj.inv(x); }
            got = objE.pow(x, y);
            assertLe(_absd(got, direct), (_absd(direct, 0) >> 100) + 4, "general path within the composite's error");
        }
        int256 ysm = bound(int256(uint256(which)), -30 * ONE, 30 * ONE);
        assertEq(objE.pow(2 * ONE, ysm), objE.exp2(ysm), "x=2 shortcut");
        assertEq(objE.pow(10 * ONE, ysm), objE.exp10(ysm), "x=10 shortcut");
    }

    function test_pow_edge_cases() public view {
        assertEq(objE.pow(0, 0), ONE);
        assertEq(objE.pow(0, 5 * ONE), 0);
        assertEq(objE.pow(ONE, 123 * ONE), ONE);
        assertEq(objE.pow(3 * ONE, 2 * ONE), 9 * ONE);
        assertEq(objE.pow(2 * ONE, 10 * ONE), 1024 * ONE);
        assertEq(objE.pow(10 * ONE, 2 * ONE), 100 * ONE);
        assertLe(_absd(objE.pow(27 * ONE, ONE / 2), obj.sqrt(27 * ONE)), 1);
        assertEq(objE.pow(4 * ONE, ONE / 2), 2 * ONE, "exact square root");
        assertEq(objE.pow(9 * ONE, ONE / 2), 3 * ONE, "exact square root through the general path");
    }

    function test_cbrt_shortcuts() public view {
        assertEq(obj.cbrt(8 * ONE), 2 * ONE);
        assertEq(obj.cbrt(27 * ONE), 3 * ONE);
        assertEq(obj.cbrt(64 * ONE), 4 * ONE);
        assertEq(obj.cbrt(0), 0);
        assertEq(obj.cbrt(-27 * ONE), -3 * ONE);
        assertEq(obj.cbrt(1000 * ONE), 10 * ONE, "no shortcut: exact through the double word");
        assertEq(obj.cbrt(-ONE / 8), -ONE / 2);
        assertEq(obj.cbrt(int256(1) << 254), int256(1) << 170, "2^126 cubed root");
    }

    function test_log2_powers_of_two() public view {
        for (int256 k = -120; k <= 126; k += 3) {
            int256 x = k >= 0 ? ONE << uint256(k) : ONE >> uint256(-k);
            assertEq(objE.log2(x), k * ONE);
            assertEq(objE.log2Up(x), k * ONE);
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
        int256 back = objE.exp(objE.ln(x));
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
        int256 w = objS.lambertW0(x);
        int256 back = obj.mul(w, objE.exp(w));
        int256 tol = (x < 0 ? -x : x) >> 112;
        assertLe(_absd(back, x), tol + 8);
    }

    /// On the secondary branch w + ln(-w) = ln(-x), w <= -1, and W_{-1} <= W_0.
    function testFuzz_prop_lambertWm1_inverse(int256 x) public view {
        x = bound(x, NEG_INV_E, -1);
        int256 w = objS.lambertWm1(x);
        assertLe(w, -ONE + (ONE >> 60));
        assertLe(w, objS.lambertW0(x) + (ONE >> 60));
        int256 lhs = w + objE.ln(-w);
        int256 rhs = objE.ln(-x);
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
    // v5: directed rounding at the token edge
    // ------------------------------------------------------------------

    /// The replays (docs/benchmarks/replay-*.md) show the loss lives where a
    /// protocol leaves the fixed point for integer token units: it must round
    /// toward itself there. These are the ops it rounds with.
    function test_directed_known() public view {
        int256 third = ONE / 3;                          // floor(2^128 / 3)
        assertEq(obj.mulDown(third, 3 * ONE), ONE - 1);
        assertEq(obj.mulUp(third, 3 * ONE), ONE - 1, "exact product: up = down");
        assertEq(obj.mulDown(ONE + 1, ONE / 2), ONE / 2);
        assertEq(obj.mulUp(ONE + 1, ONE / 2), ONE / 2 + 1);
        assertEq(obj.mulDown(-(ONE + 1), ONE / 2), -(ONE / 2) - 1);
        assertEq(obj.mulUp(-(ONE + 1), ONE / 2), -(ONE / 2));
        assertEq(obj.divDown(ONE, 3 * ONE), third);
        assertEq(obj.divUp(ONE, 3 * ONE), third + 1);
        assertEq(obj.divDown(-ONE, 3 * ONE), -third - 1, "toward -inf, where div truncates");
        assertEq(obj.div(-ONE, 3 * ONE), -third);
        assertEq(obj.divUp(-ONE, 3 * ONE), -third);
        assertEq(obj.divUp(6 * ONE, 3 * ONE), 2 * ONE, "exact quotient: up = down");
        assertEq(obj.toFixed18Down(ONE / 3), 333333333333333333);
        assertEq(obj.toFixed18Up(ONE / 3), 333333333333333334);
        assertEq(obj.toFixed18Up(ONE), 1e18, "exact: no rounding");
        assertEq(obj.toFixed18Up(1), 1, "one ULP is a whole wei charged");
        assertEq(obj.toFixed18Down(1), 0, "and nothing paid");
        assertEq(obj.toFixed18Up(-1), 0);
        assertEq(obj.toFixed18Down(-1), -1);
        _expectRevert(abi.encodeCall(IFP127.mulUp, (MAX, ONE + 1)), IFP127.Overflow.selector, "mulUp overflow");
        _expectRevert(abi.encodeCall(IFP127.divUp, (ONE, 0)), IFP127.DivisionByZero.selector, "divUp by zero");
        _expectRevert(abi.encodeCall(IFP127.divDown, (MIN, ONE / 2)), IFP127.Overflow.selector, "divDown overflow");
    }

    function testFuzz_prop_directed(int256 a, int256 b) public view {
        a = bound(a, -(int256(1) << 190), int256(1) << 190);
        b = bound(b, -(int256(1) << 190), int256(1) << 190);
        int256 lo = obj.mulDown(a, b);
        int256 hi = obj.mulUp(a, b);
        assertEq(lo, obj.mul(a, b), "mulDown is mul");
        assertTrue(hi == lo || hi == lo + 1, "mulUp is mulDown or one above");
        // exactly when the product has bits below the grid
        unchecked { assertEq(hi - lo, (uint256(a) * uint256(b)) % uint256(ONE) == 0 ? int256(0) : int256(1)); }
        if (b > int256(1) << 64 || b < -(int256(1) << 64)) {
            int256 dd = obj.divDown(a, b);
            int256 du = obj.divUp(a, b);
            assertTrue(du == dd || du == dd + 1, "divUp is divDown or one above");
            int256 t = obj.div(a, b);
            assertEq(t, (a < 0) != (b < 0) ? du : dd, "div truncates toward zero");
        }
        int256 wd = obj.toFixed18Down(a);
        int256 wu = obj.toFixed18Up(a);
        assertEq(wd, obj.toFixed18(a));
        assertTrue(wu == wd || wu == wd + 1);
    }

    // ------------------------------------------------------------------
    // v4: integer powers, near one, hyperbolic, the error function
    // ------------------------------------------------------------------

    function test_powu_known() public view {
        assertEq(objE.powu(2 * ONE, 10 * ONE), 1024 * ONE, "2^10 exact");
        assertEq(objE.powu(2 * ONE, -3 * ONE), ONE / 8, "2^-3 exact");
        assertEq(objE.powu(-3 * ONE, 3 * ONE), -27 * ONE, "(-3)^3 exact");
        assertEq(objE.powu(-3 * ONE, 2 * ONE), 9 * ONE, "(-3)^2 exact");
        assertEq(objE.powu(ONE + ONE / 2, 2 * ONE), 2 * ONE + ONE / 4, "1.5^2 exact");
        assertEq(objE.powu(ONE / 2, 200 * ONE), 0, "2^-200 is below the grid");
        assertEq(objE.powu(2 * ONE, 126 * ONE), ONE << 126, "2^126 is the largest power of two");
        assertEq(objE.powu(7 * ONE, 0), ONE, "n = 0");
        assertEq(objE.powu(0, 0), ONE, "0^0 = 1");
        assertEq(objE.powu(0, 5 * ONE), 0, "0^5");
        assertEq(objE.powu(ONE, 1000000 * ONE), ONE, "1^n");
        assertEq(objE.powu(-ONE, 1000001 * ONE), -ONE, "(-1)^odd");
        assertEq(objE.powu(3 * ONE, 2 * ONE + ONE / 2), 9 * ONE, "the exponent is floored");
        // 1.1^10 = 2.5937424601, a decimal that is not on the grid: within one ULP
        int256 b = ONE + ONE / 10;
        int256 ten = obj.mul(obj.mul(obj.mul(b, b), obj.mul(b, b)), obj.mul(obj.mul(b, b), obj.mul(obj.mul(b, b), obj.mul(b, b))));
        assertLe(_absd(objE.powu(b, 10 * ONE), ten), 12, "1.1^10 against the mul chain");
        _expectRevert(abi.encodeCall(IFP127E.powu, (2 * ONE, 127 * ONE)), IFP127.Overflow.selector, "2^127");
        _expectRevert(abi.encodeCall(IFP127E.powu, (10 * ONE, 39 * ONE)), IFP127.Overflow.selector, "10^39");
        _expectRevert(abi.encodeCall(IFP127E.powu, (0, -ONE)), IFP127.DivisionByZero.selector, "0^-1");
    }

    /// (1 + r)^n through the mantissa path against the daily compounding
    /// loop of the ladder's headline cell: $10,000 at 10% APR for a year.
    function test_compound_known() public view {
        int256 r = 93228045731763962592705371899114578; // floor(0.1 / 365 * 2^128)
        int256 g = ONE + r;
        int256 b = ONE;
        for (uint256 i; i < 365; i++) b = obj.mul(b, g);
        // the loop floors 365 times; compound rounds once
        assertLe(_absd(objE.compound(r, 365 * ONE), b), 400, "a year of daily compounding");
        assertGe(objE.compound(r, 365 * ONE), b, "the floored loop sits below");
        assertEq(objE.compound(0, 1000 * ONE), ONE, "zero rate");
        assertEq(objE.compound(-ONE, 3 * ONE), 0, "rate -1 empties the balance");
        _expectRevert(abi.encodeCall(IFP127E.compound, (-ONE, -ONE)), IFP127.DivisionByZero.selector, "compound(-1, -1)");
        _expectRevert(abi.encodeCall(IFP127E.compound, (MAX, ONE)), IFP127.Overflow.selector, "1 + MAX");
    }

    function test_near_one_known() public view {
        assertEq(objE.log1p(0), 0);
        assertEq(objE.expm1(0), 0);
        // below 2^-64 the curvature is below the grid: log1p(x) = expm1(x) = x
        assertEq(objE.expm1(1 << 60), 1 << 60, "expm1 of 2^-68");
        assertLe(_absd(objE.log1p(1 << 60), 1 << 60), 1, "log1p of 2^-68");
        assertEq(objE.log1p(ONE), objE.ln(2 * ONE), "log1p(1) = ln 2");
        assertEq(objE.expm1(ONE), objE.exp(ONE) - ONE, "expm1(1) = e - 1");
        assertEq(objE.expm1(-100 * ONE), -ONE, "expm1 far below");
        _expectRevert(abi.encodeCall(IFP127E.log1p, (-ONE)), IFP127.OutOfRange.selector, "log1p(-1)");
        _expectRevert(abi.encodeCall(IFP127E.log1p, (MIN)), IFP127.OutOfRange.selector, "log1p(MIN)");
        _expectRevert(abi.encodeCall(IFP127E.log1p, (MAX)), IFP127.Overflow.selector, "log1p(MAX)");
        _expectRevert(abi.encodeCall(IFP127E.expm1, (89 * ONE)), IFP127.Overflow.selector, "expm1(89)");
    }

    function test_hyperbolic_known() public view {
        assertEq(objH.sinh(0), 0);
        assertEq(objH.cosh(0), ONE);
        assertEq(objH.tanh(0), 0);
        assertEq(objH.atanh(0), 0);
        assertEq(objH.tanh(50 * ONE), ONE, "tanh saturates");
        assertEq(objH.tanh(-50 * ONE), -ONE);
        assertEq(objH.tanh(-ONE / 10), -objH.tanh(ONE / 10), "tanh is odd");
        assertEq(objH.sinh(-3 * ONE), -objH.sinh(3 * ONE), "sinh is odd");
        assertEq(objH.cosh(-3 * ONE), objH.cosh(3 * ONE), "cosh is even");
        // atanh(1/2) = ln(3) / 2
        assertLe(_absd(objH.atanh(ONE / 2), objE.ln(3 * ONE) / 2), 2);
        // cosh(88) is the largest the format holds
        assertGt(objH.cosh(88 * ONE), 0);
        _expectRevert(abi.encodeCall(IFP127H.sinh, (89 * ONE)), IFP127.Overflow.selector, "sinh(89)");
        _expectRevert(abi.encodeCall(IFP127H.cosh, (-89 * ONE)), IFP127.Overflow.selector, "cosh(-89)");
        _expectRevert(abi.encodeCall(IFP127H.atanh, (ONE)), IFP127.OutOfRange.selector, "atanh(1)");
        _expectRevert(abi.encodeCall(IFP127H.atanh, (-ONE)), IFP127.OutOfRange.selector, "atanh(-1)");
        _expectRevert(abi.encodeCall(IFP127H.atanh, (MAX)), IFP127.OutOfRange.selector, "atanh(MAX)");
    }

    function test_erf_known() public view {
        assertEq(objN.erf(0), 0);
        assertEq(objN.erfc(0), ONE);
        assertEq(objN.normCdf(0), ONE / 2);
        // erf(1) = 0.84270079294971486934122063508260925...
        assertLe(_absd(objN.erf(ONE), 286756220431080668183289216208796350931), 2);
        assertEq(objN.erf(-ONE), -objN.erf(ONE), "erf is odd");
        assertEq(objN.erf(10 * ONE), ONE, "erf saturates at 10");
        assertEq(objN.erf(-10 * ONE), -ONE);
        assertEq(objN.erfc(10 * ONE), 0, "erfc(10) is below the grid");
        assertEq(objN.erfc(-10 * ONE), 2 * ONE);
        assertEq(objN.erfc(93 * ONE / 10), 1, "erfc(9.3) = 1.65e-39 is one ULP");
        assertEq(objN.erfc(94 * ONE / 10), 0, "erfc(9.4) rounds to zero");
        // the tails of the normal distribution, where an 18-decimal N(d) is zero
        assertEq(objN.normCdf(-13 * ONE), 2, "Phi(-13) = 6.1e-39 is two ULPs");
        assertEq(objN.normCdf(-14 * ONE), 0, "Phi(-14) rounds to zero");
        assertEq(objN.normCdf(14 * ONE), ONE);
        // Phi(-9) = 1.1285884059538405e-19
        assertLe(_absd(objN.normCdf(-9 * ONE), 38403873405750185486), 2);
        // the series/fraction seam at 4 and the scaled seam of normCdf
        assertLe(_absd(objN.erf(4 * ONE + 1), objN.erf(4 * ONE)), 2, "continuous across x = 4");
        assertLe(_absd(objN.erfc(4 * ONE + 1), objN.erfc(4 * ONE)), 2);
    }

    function testFuzz_prop_erf_complement(int256 x) public view {
        x = bound(x, -12 * ONE, 12 * ONE);
        assertLe(_absd(objN.erf(x) + objN.erfc(x), ONE), 2, "erf + erfc = 1");
        assertLe(_absd(objN.normCdf(x) + objN.normCdf(-x), ONE), 2, "Phi(x) + Phi(-x) = 1");
        assertGe(objN.erfc(x), 0);
        assertLe(objN.normCdf(x), ONE);
    }

    function testFuzz_prop_near_one(int256 x) public view {
        x = bound(x, -ONE, ONE);
        assertLe(_absd(objE.expm1(x), objE.exp(x) - ONE), 2, "expm1 against exp");
        if (x > -ONE) assertEq(objE.log1p(x), objE.ln(ONE + x), "log1p is ln(1 + x)");
        // the round trip holds to the grid
        assertLe(_absd(objE.log1p(objE.expm1(x)), x), 2, "log1p(expm1(x)) = x");
    }

    function testFuzz_prop_hyperbolic(int256 x) public view {
        x = bound(x, -40 * ONE, 40 * ONE);
        int256 s = objH.sinh(x);
        int256 c = objH.cosh(x);
        // cosh^2 - sinh^2 = 1, with the products' own rounding allowed for
        int256 tol = (c >> 120) + 8;
        assertLe(_absd(obj.mul(c, c) - obj.mul(s, s), ONE), tol, "cosh^2 - sinh^2");
        assertLe(_absd(objH.tanh(x), obj.div(s, c)), 4, "tanh = sinh / cosh");
        int256 t = objH.tanh(x);
        if (t > -ONE && t < ONE) {
            int256 back = objH.atanh(t);
            // atanh amplifies one ULP of tanh by 1 / (1 - tanh^2) = cosh^2
            int256 tol2 = obj.mul(c, c) >> 120;
            assertLe(_absd(back, x), tol2 + 4, "atanh(tanh(x)) = x");
        }
    }

    function testFuzz_prop_powu_squaring(int256 x, uint8 n) public view {
        x = bound(x, -4 * ONE, 4 * ONE);
        uint256 k = uint256(n) % 12;
        int256 p = objE.powu(x, int256(k) * ONE);
        int256 q = ONE;
        for (uint256 i; i < k; i++) q = obj.mul(q, x);
        // k - 1 floors in the chain against one rounding;
        // each floor in the chain is scaled by the later factors, up to 4^k
        assertLe(_absd(p, q), (int256(k) + 2) << (2 * k), "powu against the mul chain");
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP256Harness} from "../base/FP256Harness.sol";
import {IFP256} from "../../contracts/src/fp256/IFP256.sol";
import {IFP256X} from "../../contracts/src/fp256/IFP256X.sol";

/// @title Behaviour256
/// @notice Known values and edges a reader can check by hand.
contract Behaviour256 is FP256Harness {
    int256 constant LN2 = int256(0x3fffe62e42fefa39ef35793c7673007e5ed5e81e6864ce5316c5b141a2eb7175);
    int256 constant E18 = int256(0x4003abc16d674ec8000000000000000000000000000000000000000000000000);

    function test_constants() public view {
        assertEq(obj.fromUint(1), ONE);
        assertEq(obj.fromUint(2), TWO);
        assertEq(obj.fromUint(1e18), E18);
        assertEq(obj.div(ONE, TWO), HALF);
        assertEq(obj.add(ONE, ONE), TWO);
        assertEq(obj.mul(TWO, TWO), obj.fromUint(4));
        assertEq(obj.sub(TWO, ONE), ONE);
        assertEq(obj.sub(ONE, ONE), 0, "x - x is +0");
        assertGe(_bits(obj.ln(TWO), LN2), 236, "ln 2 to the grid");
        assertEq(obj.ln(ONE), 0);
        assertEq(obj.exp(0), ONE);
        assertEq(obj.sqrt(obj.fromUint(4)), TWO);
        assertEq(obj.sqrt(obj.fromUint(9)), obj.fromUint(3));
        assertEq(obj.sqrt(0), 0);
        assertEq(obj.pow(TWO, obj.fromUint(10)), obj.fromUint(1024), "2^10 by the general path");
        assertEq(obj.pow(obj.fromUint(3), TWO), obj.fromUint(9));
        assertEq(obj.pow(0, 0), ONE);
        assertEq(obj.pow(0, ONE), 0);
    }

    function test_conversions() public view {
        assertEq(obj.toFixed18(ONE), 1e18);
        assertEq(obj.fromFixed18(1e18), ONE);
        assertEq(obj.fromFixed18(5e17), HALF);
        assertEq(obj.toFixed18(obj.fromFixed18(3141592653589793238)), 3141592653589793238);
        assertEq(obj.toFixed18(obj.neg(ONE)), -1e18);
        assertEq(obj.toFP127(ONE), int256(1) << 128);
        assertEq(obj.fromFP127(int256(1) << 128), ONE);
        assertEq(obj.fromFP127(-(int256(1) << 128)), obj.neg(ONE));
        assertEq(obj.toFP127(obj.fromFP127(1)), 1, "one 127.128 unit round trips");
        assertEq(obj.toFP127(_mk(false, -129, uint256(1) << 236)), 1, "2^-129 rounds to one unit, away from zero");
        assertEq(obj.toFP127(_mk(false, -130, uint256(1) << 236)), 0, "2^-130 rounds to zero");
        assertEq(obj.toFP127(obj.fromFP127(type(int256).min)), type(int256).min, "-2^127 is allowed");
        _expectRevert(abi.encodeCall(IFP256.toFP127, (_mk(false, 127, uint256(1) << 236))), IFP256.Overflow.selector, "2^127 does not fit");
        _expectRevert(abi.encodeCall(IFP256.toFixed18, (_mk(false, 250, uint256(1) << 236))), IFP256.Overflow.selector, "2^250 * 1e18 does not fit");
        assertEq(obj.toFixed18(_mk(false, -70, uint256(1) << 236)), 0, "2^-70 * 1e18 rounds to zero");
    }

    function test_sign_and_order() public view {
        assertEq(obj.neg(0), 0);
        assertEq(obj.abs(obj.neg(ONE)), ONE);
        assertEq(obj.sign(obj.neg(TWO)), obj.neg(ONE));
        assertEq(obj.sign(0), 0);
        assertEq(obj.cmp(ONE, TWO), -1);
        assertEq(obj.cmp(obj.neg(ONE), obj.neg(TWO)), 1);
        assertEq(obj.cmp(obj.neg(ONE), ONE), -1);
        assertEq(obj.lt(0, ONE), 1);
        assertEq(obj.lt(obj.neg(ONE), 0), 1);
        assertEq(obj.eq(ONE, ONE), 1);
        assertEq(obj.eq(ONE, TWO), 0);
    }

    function test_range_edges() public view {
        int256 maxv = MAX_WORD;
        _expectRevert(abi.encodeCall(IFP256.add, (maxv, maxv)), IFP256.Overflow.selector, "max + max");
        _expectRevert(abi.encodeCall(IFP256.mul, (maxv, TWO)), IFP256.Overflow.selector, "max * 2");
        assertEq(obj.div(maxv, maxv), ONE);
        assertEq(obj.mul(MIN_NORMAL, HALF), 0, "below the smallest normal rounds to zero");
        assertEq(obj.sub(MIN_NORMAL, MIN_NORMAL), 0);
        _expectRevert(abi.encodeCall(IFP256.div, (ONE, 0)), IFP256.DivisionByZero.selector, "x / 0");
        _expectRevert(abi.encodeCall(IFP256.sqrt, (obj.neg(ONE))), IFP256.OutOfRange.selector, "sqrt(-1)");
        _expectRevert(abi.encodeCall(IFP256.ln, (0)), IFP256.OutOfRange.selector, "ln 0");
        _expectRevert(abi.encodeCall(IFP256.ln, (obj.neg(ONE))), IFP256.OutOfRange.selector, "ln -1");
        _expectRevert(abi.encodeCall(IFP256.pow, (obj.neg(TWO), HALF)), IFP256.OutOfRange.selector, "(-2)^0.5");
        _expectRevert(abi.encodeCall(IFP256.pow, (0, obj.neg(ONE))), IFP256.DivisionByZero.selector, "0^-1");
        _expectRevert(abi.encodeCall(IFP256.exp, (obj.fromUint(262144))), IFP256.Overflow.selector, "exp(2^18)");
        _expectRevert(abi.encodeCall(IFP256.exp, (obj.fromUint(181706))), IFP256.Overflow.selector, "exp above the word");
        assertEq(obj.exp(obj.neg(obj.fromUint(262144))), 0, "exp(-2^18) is zero");
        assertEq(obj.exp(obj.neg(obj.fromUint(181706))), 0, "exp far below the floor is zero");
        assertGt(obj.exp(obj.fromUint(181704)), 0, "exp(181704) fits");
        assertGt(obj.exp(obj.neg(obj.fromUint(181600))), 0, "exp(-181600) is still a number");
        // the invalid words
        _expectRevert(abi.encodeCall(IFP256.abs, (SIGN)), IFP256.OutOfRange.selector, "-0 is not a number");
        _expectRevert(abi.encodeCall(IFP256.add, (1, ONE)), IFP256.OutOfRange.selector, "a bare fraction is not a number");
    }

    /// The series bands: exp near zero and ln near one keep relative precision.
    function test_near_one() public view {
        int256 tiny = _mk(false, -200, uint256(1) << 236);       // 2^-200
        assertEq(obj.exp(tiny), obj.add(ONE, tiny), "exp(2^-200) = 1 + 2^-200 on the grid");
        int256 x = obj.add(ONE, tiny);
        // ln(1 + d) = d - d^2/2 + d^3/3 - ...: at d = 2^-200 the third term is below the grid
        assertEq(obj.ln(x), obj.sub(tiny, _mk(false, -401, uint256(1) << 236)), "ln(1 + 2^-200) = 2^-200 - 2^-401");
        int256 below = _mk(false, -240, uint256(1) << 236);
        assertEq(obj.exp(below), ONE, "exp below 2^-237 is exactly one");
        int256 d = _mk(false, -30, uint256(1) << 236);           // 2^-30, inside the band
        int256 l = obj.ln(obj.add(ONE, d));
        // ln(1 + d) = d - d^2/2 + ...: the second term is 2^-61, so the result is below d by about that
        assertEq(obj.lt(l, d), 1);
        assertGe(_bits(obj.exp(l), obj.add(ONE, d)), 235, "round trip inside the band");
    }

    /// log1p and expm1 take the argument itself, so nothing near zero is lost to a rounded 1 + x.
    function test_log1p_expm1() public view {
        assertEq(obj.log1p(0), 0);
        assertEq(obj.expm1(0), 0);
        int256 t = _mk(false, -300, uint256(1) << 236);           // 2^-300: the second term is below the grid
        assertEq(obj.log1p(t), t, "log1p(2^-300) = 2^-300");
        assertEq(obj.expm1(t), t, "expm1(2^-300) = 2^-300");
        int256 d = _mk(false, -200, uint256(1) << 236);
        int256 sq = _mk(false, -401, uint256(1) << 236);
        assertEq(obj.log1p(d), obj.sub(d, sq), "log1p(2^-200) = 2^-200 - 2^-401");
        assertEq(obj.expm1(d), obj.add(d, sq), "expm1(2^-200) = 2^-200 + 2^-401");
        assertEq(obj.log1p(ONE), obj.ln(TWO), "log1p(1) = ln 2");
        assertEq(obj.expm1(obj.neg(obj.fromUint(1000))), obj.neg(ONE), "expm1(-1000) = -1");
        _expectRevert(abi.encodeCall(IFP256.log1p, (obj.neg(ONE))), IFP256.OutOfRange.selector, "log1p(-1)");
        _expectRevert(abi.encodeCall(IFP256.log1p, (obj.neg(TWO))), IFP256.OutOfRange.selector, "log1p(-2)");
        _expectRevert(abi.encodeCall(IFP256.expm1, (obj.fromUint(181706))), IFP256.Overflow.selector, "expm1 above the word");
        int256 x = _mk(false, -30, uint256(1) << 236);
        assertGe(_bits(obj.expm1(obj.log1p(x)), x), 235, "expm1(log1p(2^-30))");
        assertGe(_bits(obj.log1p(obj.expm1(obj.fromUint(3))), obj.fromUint(3)), 235, "log1p(expm1(3))");
    }

    /// The error function family: odd and complementary symmetry, the ends, the deep tail.
    function test_erf_family() public view {
        assertEq(objX.erf(0), 0);
        assertEq(objX.erfc(0), ONE);
        assertEq(objX.normCdf(0), HALF);
        int256 x = _mk(false, 0, uint256(0x3) << 233);           // 1.375
        assertEq(objX.erf(obj.neg(x)), obj.neg(objX.erf(x)), "erf is odd");
        assertGe(_bits(obj.add(objX.erf(x), objX.erfc(x)), ONE), 236, "erf + erfc = 1");
        assertGe(_bits(obj.add(objX.normCdf(x), objX.normCdf(obj.neg(x))), ONE), 236, "Phi(x) + Phi(-x) = 1");
        assertEq(objX.erf(obj.fromUint(13)), ONE, "erf is one from 13");
        assertEq(objX.erfc(obj.fromUint(1000)), 0, "erfc underflows");
        assertEq(objX.erfc(obj.neg(obj.fromUint(1000))), TWO, "erfc(-1000) = 2");
        assertEq(objX.normCdf(obj.fromUint(1000)), ONE);
        assertEq(objX.normCdf(obj.neg(obj.fromUint(1000))), 0, "Phi underflows");
        assertGt(objX.erfc(obj.fromUint(426)), 0, "erfc(426) is still a number, about 10^-78,800");
        assertGt(objX.normCdf(obj.neg(obj.fromUint(602))), 0, "Phi(-602) is still a number");
        // erfc(y) = 2 Phi(-y sqrt 2) in the tail; the rounded argument y sqrt 2 costs
        // about 2 y^2 2^-236 relative, eleven bits at y = 30
        int256 y = obj.fromUint(30);
        int256 z = obj.neg(obj.mul(y, obj.sqrt(TWO)));
        assertGe(_bits(objX.erfc(y), obj.mul(TWO, objX.normCdf(z))), 220, "erfc(30) = 2 Phi(-30 sqrt 2)");
    }

    /// Lambert W: the defining identity on both branches, the domain ends.
    function test_lambert() public view {
        assertEq(objX.lambertW0(0), 0);
        int256 em1 = obj.exp(obj.neg(ONE));                          // 1/e
        int256 w = objX.lambertW0(obj.fromUint(10));
        assertGe(_bits(obj.mul(w, obj.exp(w)), obj.fromUint(10)), 234, "W0(10) e^W0(10) = 10");
        assertGe(_bits(objX.lambertW0(obj.mul(ONE, obj.exp(ONE))), ONE), 235, "W0(e) = 1");
        int256 x = obj.neg(obj.fromFixed18(100000000000000000));    // -0.1
        int256 v = objX.lambertWm1(x);
        assertGe(_bits(obj.mul(v, obj.exp(v)), x), 234, "Wm1(-0.1) e^Wm1 = -0.1");
        assertEq(obj.lt(v, obj.neg(ONE)), 1, "Wm1 is below -1");
        _expectRevertX(abi.encodeCall(IFP256X.lambertW0, (obj.neg(HALF))), IFP256X.OutOfRange.selector, "W0(-1/2)");
        _expectRevertX(abi.encodeCall(IFP256X.lambertWm1, (em1)), IFP256X.OutOfRange.selector, "Wm1(1/e)");
        _expectRevertX(abi.encodeCall(IFP256X.lambertWm1, (0)), IFP256X.OutOfRange.selector, "Wm1(0)");
        // the far ends: W0 near the top of the format, Wm1 near the bottom
        assertEq(obj.lt(obj.fromUint(181000), objX.lambertW0(MAX_WORD)), 1);
        assertEq(obj.lt(objX.lambertWm1(obj.neg(MIN_NORMAL)), obj.neg(obj.fromUint(181000))), 1);
    }

    /// powu and compound: exact small powers, signs, the reciprocal, the domain.
    function test_powu_compound() public view {
        assertEq(obj.powu(obj.fromUint(3), 5), obj.fromUint(243), "3^5 = 243 exactly");
        assertEq(obj.powu(TWO, -3), _mk(false, -3, uint256(1) << 236), "2^-3 = 1/8");
        assertEq(obj.powu(obj.neg(TWO), 3), obj.neg(obj.fromUint(8)), "(-2)^3 = -8");
        assertEq(obj.powu(obj.neg(TWO), 4), obj.fromUint(16), "(-2)^4 = 16");
        assertEq(obj.powu(0, 0), ONE, "0^0 = 1");
        assertEq(obj.powu(0, 7), 0);
        _expectRevert(abi.encodeCall(IFP256.powu, (0, -1)), IFP256.DivisionByZero.selector, "0^-1");
        _expectRevert(abi.encodeCall(IFP256.powu, (TWO, 1 << 20)), IFP256.Overflow.selector, "2^(2^20)");
        assertEq(obj.powu(HALF, 1 << 20), 0, "(1/2)^(2^20) underflows");
        assertEq(obj.compound(0, 1000), ONE);
        assertEq(obj.compound(obj.fromFixed18(50000000000000000), 0), ONE);
        assertEq(obj.compound(obj.neg(ONE), 2), 0, "(1 - 1)^2 = 0");
        _expectRevert(abi.encodeCall(IFP256.compound, (obj.neg(ONE), -1)), IFP256.DivisionByZero.selector, "0^-1");
        _expectRevert(abi.encodeCall(IFP256.compound, (obj.neg(TWO), 1)), IFP256.OutOfRange.selector, "rate below -1");
        // (1 + r)^n against powu of the base, for an r the base holds exactly
        assertEq(obj.compound(HALF, 12), obj.powu(obj.add(ONE, HALF), 12), "compound(1/2, 12) = 1.5^12, both correctly rounded");
    }

    /// Release four: directed rounding at the token edge, values a reader can check.
    function test_directed() public view {
        int256 third = obj.div(ONE, obj.fromUint(3));
        // 1/3 rounded down and up: one ULP apart, the nearest one of them
        int256 d = obj.divDown(ONE, obj.fromUint(3));
        int256 u = obj.divUp(ONE, obj.fromUint(3));
        assertEq(u, d + 1, "1/3: Up is Down plus one ULP");
        assertTrue(third == d || third == u);
        assertEq(obj.divDown(obj.neg(ONE), obj.fromUint(3)), obj.neg(u), "-1/3 down is -(1/3 up)");
        assertEq(obj.divUp(obj.fromUint(6), obj.fromUint(3)), TWO, "exact quotients are exact both ways");
        assertEq(obj.mulDown(third, obj.fromUint(3)), obj.mulUp(third, obj.fromUint(3)) - 1, "3 x (1/3) is inexact");
        // token units: 2.5 tokens of 18 decimals pay out 2 and charge 3 at the integer edge
        int256 two5 = obj.add(TWO, HALF);
        assertEq(obj.toUintDown(two5), 2);
        assertEq(obj.toUintUp(two5), 3);
        assertEq(obj.toUintDown(obj.fromUint(7)), 7, "integers are exact");
        assertEq(obj.toUintUp(obj.fromUint(7)), 7);
        assertEq(obj.toUintUp(_mk(false, -300, uint256(1) << 236)), 1, "any positive amount charges at least one unit");
        assertEq(obj.toUintDown(_mk(false, -300, uint256(1) << 236)), 0);
        _expectRevert(abi.encodeCall(IFP256.toUintDown, (obj.neg(HALF))), IFP256.OutOfRange.selector, "negative amounts revert");
        _expectRevert(abi.encodeCall(IFP256.toUintUp, (_mk(false, 256, uint256(1) << 236))), IFP256.Overflow.selector, "2^256 does not fit");
        assertEq(obj.toUintDown(_mk(false, 255, (uint256(1) << 237) - 1)), type(uint256).max - ((uint256(1) << 19) - 1), "the largest number below 2^256");
        // 18-decimal units: 1/3 token pays 333333333333333333 wei and charges ...334
        assertEq(obj.toFixed18Down(third), 333333333333333333);
        assertEq(obj.toFixed18Up(third), 333333333333333334);
        assertEq(obj.toFixed18Down(obj.neg(third)), -333333333333333334);
        assertEq(obj.toFixed18Up(_mk(false, -100, uint256(1) << 236)), 1, "dust charges one wei");
        assertEq(obj.toFixed18Down(_mk(false, -100, uint256(1) << 236)), 0);
        assertEq(obj.toFixed18Up(obj.fromFixed18(1e18)), 1e18, "exact amounts are exact");
        // signed integers and integral numbers
        assertEq(obj.toIntDown(obj.neg(two5)), -3);
        assertEq(obj.toIntUp(obj.neg(two5)), -2);
        assertEq(obj.toIntDown(obj.neg(_mk(false, 255, uint256(1) << 236))), type(int256).min, "-2^255 fits");
        _expectRevert(abi.encodeCall(IFP256.toIntUp, (_mk(false, 255, uint256(1) << 236))), IFP256.Overflow.selector, "2^255 does not");
        assertEq(obj.floor(two5), TWO);
        assertEq(obj.ceil(two5), obj.fromUint(3));
        assertEq(obj.floor(obj.neg(two5)), obj.neg(obj.fromUint(3)));
        assertEq(obj.ceil(obj.neg(HALF)), 0, "ceil(-1/2) is zero, not minus zero");
        assertEq(obj.floor(obj.neg(HALF)), obj.neg(ONE));
        // above 2^237 fromUint rounds; Down and Up bracket the integer
        uint256 v = (uint256(1) << 240) + 3;
        assertEq(obj.toUintDown(obj.fromUintDown(v)), uint256(1) << 240);
        assertEq(obj.toUintDown(obj.fromUintUp(v)), (uint256(1) << 240) + 16, "one ULP at 2^240 is 16");
        assertEq(obj.fromUintUp(type(uint256).max), _mk(false, 256, uint256(1) << 236), "rounds up to 2^256");
        // underflow: Up never rounds a positive product to zero
        int256 tiny = _mk(false, -200000, uint256(1) << 236);
        assertEq(obj.mulDown(tiny, tiny), 0);
        assertEq(obj.mulUp(tiny, tiny), MIN_NORMAL, "the smallest number");
        assertEq(obj.mulDown(obj.neg(tiny), tiny), MIN_NORMAL | SIGN, "minus the smallest number");
        assertEq(obj.mulUp(obj.neg(tiny), tiny), 0);
        _expectRevert(abi.encodeCall(IFP256.divUp, (ONE, 0)), IFP256.DivisionByZero.selector, "divUp by zero");
    }

    /// Release four: exact ties round away from zero, as a reader can check.
    function test_ties() public view {
        uint256 c = (uint256(1) << 79) + 1;       // c^3 = 2^237 + 3 2^158 + 3 2^79 + 1: 238 bits, odd
        int256 want = obj.fromUint(c * c * c);   // fromUint's one rounding: half away from zero
        assertEq(obj.pow(obj.fromUint(c), obj.fromUint(3)), want, "pow(c, 3)");
        assertEq(obj.pow(obj.fromUint(c * c), obj.div(obj.fromUint(3), TWO)), want, "pow(c^2, 3/2)");
        assertEq(obj.powu(obj.fromUint(c), 3), want, "powu(c, 3)");
        assertEq(obj.powu(obj.neg(obj.fromUint(c)), 3), obj.neg(want), "powu(-c, 3)");
        assertEq(obj.compound(obj.fromUint(c - 1), 3), want, "compound(c - 1, 3)");
        assertEq(obj.compound(TWO, 150), obj.powu(obj.fromUint(3), 150), "3^150: 238 bits, a tie both ways");
        assertEq(obj.pow(obj.fromUint(9), obj.div(obj.fromUint(3), TWO)), obj.fromUint(27), "9^1.5 = 27 exactly");
    }
}

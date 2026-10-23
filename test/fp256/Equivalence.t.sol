// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP256Harness} from "../base/FP256Harness.sol";
import {IFP256} from "../../contracts/src/fp256/IFP256.sol";
import {IFP256E} from "../../contracts/src/fp256/IFP256E.sol";
import {IFP256H} from "../../contracts/src/fp256/IFP256H.sol";
import {IFP256S} from "../../contracts/src/fp256/IFP256S.sol";

/// @title Equivalence256
/// @notice The deployed object and the inline library return identical
///         results, including which inputs revert and with what data, on the
///         full int256 domain; plus the algebraic identities the format
///         promises (section 15 of the design).
contract Equivalence256 is FP256Harness {
    function _objLib(bytes memory call, string memory what) internal view {
        _assertSame(_try(_objFor(what), call), _try(address(lib), call), what);
    }

    function testFuzz_objEqLib_add(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.add, (a, b)), "add"); }
    function testFuzz_objEqLib_sub(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.sub, (a, b)), "sub"); }
    function testFuzz_objEqLib_mul(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.mul, (a, b)), "mul"); }
    function testFuzz_objEqLib_div(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.div, (a, b)), "div"); }
    function testFuzz_objEqLib_sqrt(int256 x) public view { _objLib(abi.encodeCall(IFP256.sqrt, (x)), "sqrt"); }
    function testFuzz_objEqLib_exp(int256 x) public view { _objLib(abi.encodeCall(IFP256E.exp, (x)), "exp"); }
    function testFuzz_objEqLib_ln(int256 x) public view { _objLib(abi.encodeCall(IFP256E.ln, (x)), "ln"); }
    function testFuzz_objEqLib_pow(int256 x, int256 y) public view { _objLib(abi.encodeCall(IFP256E.pow, (x, y)), "pow"); }
    function testFuzz_objEqLib_powu(int256 x, int256 n) public view { _objLib(abi.encodeCall(IFP256E.powu, (x, n)), "powu"); }
    function testFuzz_objEqLib_compound(int256 r, int256 n) public view { _objLib(abi.encodeCall(IFP256E.compound, (r, n)), "compound"); }
    function testFuzz_objEqLib_log1p(int256 x) public view { _objLib(abi.encodeCall(IFP256E.log1p, (x)), "log1p"); }
    function testFuzz_objEqLib_expm1(int256 x) public view { _objLib(abi.encodeCall(IFP256E.expm1, (x)), "expm1"); }
    function testFuzz_objEqLib_erf(int256 x) public view { _objLib(abi.encodeCall(IFP256S.erf, (x)), "erf"); }
    function testFuzz_objEqLib_erfc(int256 x) public view { _objLib(abi.encodeCall(IFP256S.erfc, (x)), "erfc"); }
    function testFuzz_objEqLib_normCdf(int256 x) public view { _objLib(abi.encodeCall(IFP256S.normCdf, (x)), "normCdf"); }
    function testFuzz_objEqLib_lambertW0(int256 x) public view { _objLib(abi.encodeCall(IFP256S.lambertW0, (x)), "lambertW0"); }
    function testFuzz_objEqLib_lambertWm1(int256 x) public view { _objLib(abi.encodeCall(IFP256S.lambertWm1, (x)), "lambertWm1"); }
    function testFuzz_objEqLib_neg(int256 x) public view { _objLib(abi.encodeCall(IFP256.neg, (x)), "neg"); }
    function testFuzz_objEqLib_abs(int256 x) public view { _objLib(abi.encodeCall(IFP256.abs, (x)), "abs"); }
    function testFuzz_objEqLib_sign(int256 x) public view { _objLib(abi.encodeCall(IFP256.sign, (x)), "sign"); }
    function testFuzz_objEqLib_cmp(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.cmp, (a, b)), "cmp"); }
    function testFuzz_objEqLib_lt(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.lt, (a, b)), "lt"); }
    function testFuzz_objEqLib_eq(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.eq, (a, b)), "eq"); }
    function testFuzz_objEqLib_fromUint(uint256 x) public view { _objLib(abi.encodeCall(IFP256.fromUint, (x)), "fromUint"); }
    function testFuzz_objEqLib_fromFP127(int256 x) public view { _objLib(abi.encodeCall(IFP256.fromFP127, (x)), "fromFP127"); }
    function testFuzz_objEqLib_toFP127(int256 x) public view { _objLib(abi.encodeCall(IFP256.toFP127, (x)), "toFP127"); }
    function testFuzz_objEqLib_fromFixed18(int256 x) public view { _objLib(abi.encodeCall(IFP256.fromFixed18, (x)), "fromFixed18"); }
    function testFuzz_objEqLib_toFixed18(int256 x) public view { _objLib(abi.encodeCall(IFP256.toFixed18, (x)), "toFixed18"); }
    function testFuzz_objEqLib_mulDown(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.mulDown, (a, b)), "mulDown"); }
    function testFuzz_objEqLib_mulUp(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.mulUp, (a, b)), "mulUp"); }
    function testFuzz_objEqLib_divDown(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.divDown, (a, b)), "divDown"); }
    function testFuzz_objEqLib_divUp(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.divUp, (a, b)), "divUp"); }
    function testFuzz_objEqLib_toUintDown(int256 x) public view { _objLib(abi.encodeCall(IFP256.toUintDown, (x)), "toUintDown"); }
    function testFuzz_objEqLib_toUintUp(int256 x) public view { _objLib(abi.encodeCall(IFP256.toUintUp, (x)), "toUintUp"); }
    function testFuzz_objEqLib_toIntDown(int256 x) public view { _objLib(abi.encodeCall(IFP256.toIntDown, (x)), "toIntDown"); }
    function testFuzz_objEqLib_toIntUp(int256 x) public view { _objLib(abi.encodeCall(IFP256.toIntUp, (x)), "toIntUp"); }
    function testFuzz_objEqLib_floor(int256 x) public view { _objLib(abi.encodeCall(IFP256.floor, (x)), "floor"); }
    function testFuzz_objEqLib_ceil(int256 x) public view { _objLib(abi.encodeCall(IFP256.ceil, (x)), "ceil"); }
    function testFuzz_objEqLib_fromUintDown(uint256 x) public view { _objLib(abi.encodeCall(IFP256.fromUintDown, (x)), "fromUintDown"); }
    function testFuzz_objEqLib_fromUintUp(uint256 x) public view { _objLib(abi.encodeCall(IFP256.fromUintUp, (x)), "fromUintUp"); }
    function testFuzz_objEqLib_toFixed18Down(int256 x) public view { _objLib(abi.encodeCall(IFP256.toFixed18Down, (x)), "toFixed18Down"); }
    function testFuzz_objEqLib_toFixed18Up(int256 x) public view { _objLib(abi.encodeCall(IFP256.toFixed18Up, (x)), "toFixed18Up"); }
    // #79: FP256X2 and FP256X3, on raw words and on numbers in a working range
    function testFuzz_objEqLib_exp2(int256 x) public view { _objLib(abi.encodeCall(IFP256E.exp2, (x)), "exp2"); }
    function testFuzz_objEqLib_exp10(int256 x) public view { _objLib(abi.encodeCall(IFP256E.exp10, (x)), "exp10"); }
    function testFuzz_objEqLib_log2(int256 x) public view { _objLib(abi.encodeCall(IFP256E.log2, (x)), "log2"); }
    function testFuzz_objEqLib_log10(int256 x) public view { _objLib(abi.encodeCall(IFP256E.log10, (x)), "log10"); }
    function testFuzz_objEqLib_log2Up(int256 x) public view { _objLib(abi.encodeCall(IFP256E.log2Up, (x)), "log2Up"); }
    function testFuzz_objEqLib_cbrt(int256 x) public view { _objLib(abi.encodeCall(IFP256.cbrt, (x)), "cbrt"); }
    function testFuzz_objEqLib_sinh(int256 x) public view { _objLib(abi.encodeCall(IFP256H.sinh, (x)), "sinh"); }
    function testFuzz_objEqLib_cosh(int256 x) public view { _objLib(abi.encodeCall(IFP256H.cosh, (x)), "cosh"); }
    function testFuzz_objEqLib_tanh(int256 x) public view { _objLib(abi.encodeCall(IFP256H.tanh, (x)), "tanh"); }
    function testFuzz_objEqLib_atanh(int256 x) public view { _objLib(abi.encodeCall(IFP256H.atanh, (x)), "atanh"); }
    function testFuzz_objEqLib_min(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.min, (a, b)), "min"); }
    function testFuzz_objEqLib_max(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.max, (a, b)), "max"); }
    function testFuzz_objEqLib_avg(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.avg, (a, b)), "avg"); }
    function testFuzz_objEqLib_dist(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.dist, (a, b)), "dist"); }
    function testFuzz_objEqLib_zeroFloorSub(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.zeroFloorSub, (a, b)), "zeroFloorSub"); }
    function testFuzz_objEqLib_gavg(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.gavg, (a, b)), "gavg"); }
    function testFuzz_objEqLib_hypot(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.hypot, (a, b)), "hypot"); }
    function testFuzz_objEqLib_inv(int256 x) public view { _objLib(abi.encodeCall(IFP256.inv, (x)), "inv"); }
    function testFuzz_objEqLib_frac(int256 x) public view { _objLib(abi.encodeCall(IFP256.frac, (x)), "frac"); }
    function testFuzz_objEqLib_round(int256 x) public view { _objLib(abi.encodeCall(IFP256.round, (x)), "round"); }
    function testFuzz_objEqLib_factorial(int256 x) public view { _objLib(abi.encodeCall(IFP256S.factorial, (x)), "factorial"); }
    function testFuzz_objEqLib_clamp(int256 x, int256 lo, int256 hi) public view { _objLib(abi.encodeCall(IFP256.clamp, (x, lo, hi)), "clamp"); }
    function testFuzz_objEqLib_lerp(int256 a, int256 b, int256 t) public view { _objLib(abi.encodeCall(IFP256.lerp, (a, b, t)), "lerp"); }
    function testFuzz_objEqLib_num1_79(int256 w, uint8 which) public view {
        int256 x = _num(w, -300, 300);
        string[14] memory ops = ["exp2", "exp10", "log2", "log10", "log2Up", "cbrt", "sinh", "cosh", "tanh", "atanh", "inv", "frac", "round", "factorial"];
        string memory op = ops[which % 14];
        _objLib(abi.encodeWithSignature(string.concat(op, "(int256)"), x), op);
        int256 y = _num(w, -12, 12);
        _objLib(abi.encodeWithSignature(string.concat(op, "(int256)"), y), op);
    }

    function testFuzz_objEqLib_num2_79(int256 wa, int256 wb, uint8 which) public view {
        int256 a = _num(wa, -300, 300);
        int256 b = _num(wb, -300, 300);
        string[7] memory ops = ["min", "max", "avg", "dist", "zeroFloorSub", "gavg", "hypot"];
        string memory op = ops[which % 7];
        _objLib(abi.encodeWithSignature(string.concat(op, "(int256,int256)"), a, b), op);
    }

    function testFuzz_objEqLib_lerp_num(int256 wa, int256 wb, int256 wt, uint8 spread) public view {
        int256 lim = spread % 2 == 0 ? int256(40) : int256(200000);
        _objLib(abi.encodeCall(IFP256.lerp, (_num(wa, -lim, lim), _num(wb, -lim, lim), _num(wt, -lim, lim))), "lerp");
    }

    // ---- a valid number from fuzz input -------------------------------------

    function _num(int256 w, int256 lo, int256 hi) internal pure returns (int256) {
        bool s = (uint256(w) >> 255) == 1;
        int256 u = int256(bound(uint256(w) & 0xfffff, 0, uint256(hi - lo))) + lo;
        return _mk(s, u, uint256(w) & ((uint256(1) << 236) - 1));
    }

    // ---- identities -----------------------------------------------------------

    function testFuzz_prop_fromFP127_roundtrip(int256 x) public view {
        // every 127.128 word with at most 237 significant bits survives the round trip
        x = bound(x, -(int256(1) << 236), int256(1) << 236);
        assertEq(obj.toFP127(obj.fromFP127(x)), x, "toFP127(fromFP127(x))");
    }

    function testFuzz_prop_toFP127_roundtrip(int256 w) public view {
        int256 f = _num(w, -100, 100);
        // a float within 2^-128 resolution of the grid: the rounded word decodes back exactly when the
        // float itself sits on the grid; here check the weaker, exact statement on powers of two
        int256 g = obj.fromFP127(obj.toFP127(f));
        // |g - f| <= half a 127.128 unit
        int256 d = obj.sub(g, f);
        int256 halfUnit = _mk(false, -129, uint256(1) << 236);
        assertEq(obj.lt(obj.abs(d), obj.add(halfUnit, _mk(false, -200, uint256(1) << 236))), 1, "within half a unit");
    }

    function testFuzz_prop_powers_of_two_exact(int256 w, int16 k) public view {
        int256 x = _num(w, -1000, 1000);
        int256 p = _mk(false, int256(k), uint256(1) << 236);
        (bool s, uint256 e, uint256 m) = _unpack(x);
        int256 want = _mk(s, int256(e) - int256(BIAS) + int256(k), m);
        assertEq(obj.mul(x, p), want, "mul by 2^k");
        assertEq(obj.div(x, p), _mk(s, int256(e) - int256(BIAS) - int256(k), m), "div by 2^k");
        assertEq(obj.mul(x, ONE), x, "x * 1");
        assertEq(obj.div(x, ONE), x, "x / 1");
        assertEq(obj.div(x, x), ONE, "x / x");
    }

    function testFuzz_prop_add_algebra(int256 wa, int256 wb) public view {
        int256 a = _num(wa, -1000, 1000);
        int256 b = _num(wb, -1000, 1000);
        assertEq(obj.add(a, b), obj.add(b, a), "commutative");
        assertEq(obj.mul(a, b), obj.mul(b, a), "mul commutative");
        assertEq(obj.add(a, 0), a, "x + 0");
        assertEq(obj.sub(a, a), 0, "x - x");
        assertEq(obj.sub(a, b), obj.add(a, obj.neg(b)), "a - b = a + (-b)");
        assertEq(obj.neg(obj.neg(a)), a, "neg neg");
        assertEq(obj.neg(obj.add(a, b)), obj.add(obj.neg(a), obj.neg(b)), "ties away: -(a+b) = -a + -b");
        assertEq(obj.mul(obj.neg(a), b), obj.neg(obj.mul(a, b)), "-(a b)");
    }

    function testFuzz_prop_sqrt(int256 w) public view {
        int256 x = _mk(false, int256(bound(uint256(w) & 0xffff, 0, 2000)) - 1000, uint256(w) & ((uint256(1) << 236) - 1));
        int256 r = obj.sqrt(x);
        // r^2 within 2 ULP of x, and sqrt(x^2) within 1 ULP of x
        assertLe(_ulps(obj.mul(r, r), x), 2, "sqrt^2");
        assertLe(_ulps(obj.sqrt(obj.mul(x, x)), x), 1, "sqrt(x^2)");
    }

    function testFuzz_prop_div_mul(int256 wa, int256 wb) public view {
        int256 a = _num(wa, -1000, 1000);
        int256 b = _num(wb, -1000, 1000);
        assertLe(_ulps(obj.div(obj.mul(a, b), b), a), 2, "(a b) / b");
    }

    function testFuzz_prop_exp_ln(int256 w) public view {
        int256 x = _mk(false, int256(bound(uint256(w) & 0xffff, 0, 400)) - 200, uint256(w) & ((uint256(1) << 236) - 1));
        // ln then exp: two roundings, the second scaled by |ln x| (up to 139 here)
        assertGe(_bits(objE.exp(objE.ln(x)), x), 228, "exp(ln x)");
    }

    function testFuzz_prop_compare(int256 wa, int256 wb) public view {
        int256 a = _num(wa, -300, 300);
        int256 b = _num(wb, -300, 300);
        int256 d = obj.sub(a, b);
        int256 c = obj.cmp(a, b);
        if (d == 0) { assertEq(c, 0); assertEq(obj.eq(a, b), 1); }
        else if (d < 0) { assertEq(c, -1); assertEq(obj.lt(a, b), 1); }
        else { assertEq(c, 1); assertEq(obj.lt(a, b), 0); }
    }

    function testFuzz_prop_fixed18_roundtrip(int256 x) public view {
        x = bound(x, -(int256(1) << 236), int256(1) << 236);
        // one rounding each way at 2^-236 relative cannot move an 18-decimal word
        assertEq(obj.toFixed18(obj.fromFixed18(x)), x, "toFixed18(fromFixed18(w))");
    }

    // ---- release four: directed rounding brackets the nearest word ------------

    /// The next word above a positive x (one ULP up; the carry moves the exponent).
    function _up1(int256 x) internal pure returns (int256) { return x + 1; }

    function testFuzz_prop_mul_directed(int256 wa, int256 wb) public view {
        int256 a = _num(wa, -1000, 1000);
        int256 b = _num(wb, -1000, 1000);
        int256 n = obj.mul(a, b);
        int256 d = obj.mulDown(a, b);
        int256 u = obj.mulUp(a, b);
        // Down <= nearest <= Up, at most one ULP apart, equal exactly when the product is exact
        assertEq(obj.lt(n, d), 0, "mulDown <= mul");
        assertEq(obj.lt(u, n), 0, "mul <= mulUp");
        assertTrue(d == u || n == d || n == u, "nearest is one of the two");
        if (d != u) {
            if (d >= 0) assertEq(u, _up1(d), "Up is Down plus one ULP");
            else assertEq(d, _up1(u), "magnitudes one ULP apart");
        }
        // the sign rule: Up on -x is -(Down on x)
        assertEq(obj.mulUp(obj.neg(a), b), obj.neg(d), "mulUp(-a, b) = -mulDown(a, b)");
    }

    function testFuzz_prop_div_directed(int256 wa, int256 wb) public view {
        int256 a = _num(wa, -1000, 1000);
        int256 b = _num(wb, -1000, 1000);
        int256 n = obj.div(a, b);
        int256 d = obj.divDown(a, b);
        int256 u = obj.divUp(a, b);
        assertEq(obj.lt(n, d), 0, "divDown <= div");
        assertEq(obj.lt(u, n), 0, "div <= divUp");
        assertTrue(d == u || n == d || n == u, "nearest is one of the two");
        if (d != u) {
            if (d >= 0) assertEq(u, _up1(d), "Up is Down plus one ULP");
            else assertEq(d, _up1(u), "magnitudes one ULP apart");
        }
        // exact quotients: (a b) / b when a b is exact
        if (obj.mulDown(a, b) == obj.mulUp(a, b)) {
            int256 p = obj.mul(a, b);
            assertEq(obj.divDown(p, b), a, "divDown of an exact product");
            assertEq(obj.divUp(p, b), a, "divUp of an exact product");
        }
    }

    function testFuzz_prop_toUint_directed(int256 w) public view {
        int256 x = _num(w, -8, 254);
        x = obj.abs(x);
        uint256 d = obj.toUintDown(x);
        uint256 u = obj.toUintUp(x);
        assertTrue(u == d || u == d + 1, "ceil is floor or floor + 1");
        // floor(x) as a number is at or below x, ceil(x) at or above (both exact below 2^237)
        if (d < (uint256(1) << 237)) {
            assertEq(obj.lt(x, obj.fromUint(d)), 0, "floor <= x");
            assertEq(obj.lt(obj.fromUint(u), x), 0, "x <= ceil");
            assertEq(u == d, obj.eq(obj.fromUint(d), x) == 1, "equal exactly for integers");
        }
        assertEq(obj.floor(x), d < (uint256(1) << 237) ? obj.fromUint(d) : x, "floor as a number");
    }

    function testFuzz_prop_toInt_directed(int256 w) public view {
        int256 x = _num(w, -8, 250);
        int256 d = obj.toIntDown(x);
        int256 u = obj.toIntUp(x);
        assertTrue(u == d || u == d + 1, "ceil is floor or floor + 1");
        assertEq(obj.toIntUp(obj.neg(x)), -d, "ceil(-x) = -floor(x)");
        assertEq(obj.ceil(obj.neg(x)), obj.neg(obj.floor(x)), "ceil(-x) = -floor(x) as numbers");
    }

    function testFuzz_prop_toFixed18_directed(int256 w) public view {
        int256 x = _num(w, -80, 180);
        int256 n = obj.toFixed18(x);
        int256 d = obj.toFixed18Down(x);
        int256 u = obj.toFixed18Up(x);
        assertTrue(u == d || u == d + 1, "Up is Down or Down + 1");
        assertTrue(n == d || n == u, "nearest is one of the two");
        assertEq(obj.toFixed18Up(obj.neg(x)), -d, "Up(-x) = -Down(x)");
        // exact 18-decimal words go through unchanged
        int256 f = obj.fromFixed18(d);
        if (obj.toFixed18Down(f) == obj.toFixed18Up(f)) assertEq(obj.toFixed18Down(f), d);
    }

    function testFuzz_prop_fromUint_directed(uint256 v) public view {
        int256 d = obj.fromUintDown(v);
        int256 u = obj.fromUintUp(v);
        int256 n = obj.fromUint(v);
        assertTrue(n == d || n == u, "nearest is one of the two");
        if (v < (uint256(1) << 237)) assertTrue(d == u && d == n, "exact below 2^237");
        else assertTrue(u == d || u == _up1(d), "one ULP apart");
        assertLe(obj.toUintDown(d), v, "Down at or below");
        if (v <= type(uint256).max - (uint256(1) << 19)) assertGe(obj.toUintUp(u), v, "Up at or above");
    }

    // ---- release four: exact ties round away from zero ------------------------

    /// c^n for an odd c with c^n of exactly 238 bits: a tie, so the word is
    /// fromUint(c^n), whose single rounding takes it away from zero.
    function _tie(uint256 seed, uint256 n) internal pure returns (uint256 c, uint256 p) {
        uint256 bits = (238 + n - 1) / n;
        for (uint256 i; i < 64; i++) {
            c = (uint256(keccak256(abi.encode(seed, i))) >> (256 - bits)) | (uint256(1) << (bits - 1)) | 1;
            p = c;
            for (uint256 j = 1; j < n; j++) p *= c;
            if (p >> 237 == 1) return (c, p);
        }
        return (0, 0);
    }

    function testFuzz_ties_pow_powu(uint256 seed, uint8 nn, int16 sk) public view {
        uint256 n = bound(uint256(nn), 2, 9);
        (uint256 c, uint256 p) = _tie(seed, n);
        vm.assume(c != 0);
        int256 k = int256(bound(int256(sk), -200, 200));
        int256 scale = _mk(false, k, uint256(1) << 236);
        int256 x = obj.mul(obj.fromUint(c), scale);
        int256 want = obj.mul(obj.fromUint(p), _mk(false, k * int256(n), uint256(1) << 236));
        assertEq(objE.pow(x, obj.fromUint(n)), want, "pow(c 2^k, n) is the tie rounded away");
        assertEq(objE.powu(x, int256(n)), want, "powu(c 2^k, n)");
        if (n % 2 == 1) assertEq(objE.powu(obj.neg(x), int256(n)), obj.neg(want), "powu(-c, odd n)");
        // c^2 to the n/2: the tie through a square root
        if (n % 2 == 1 && n <= 5) {
            int256 y = obj.div(obj.fromUint(n), TWO);
            assertEq(objE.pow(obj.mul(x, x), y), want, "pow(c^2 2^2k, n/2)");
        }
    }

    function testFuzz_ties_compound(uint256 seed, uint8 nn) public view {
        uint256 n = bound(uint256(nn), 2, 9);
        (uint256 c, uint256 p) = _tie(seed, n);
        vm.assume(c != 0);
        // 1 + rate = c, and 1 + rate = c 2^-b in [1/2, 1) (a negative rate)
        assertEq(objE.compound(obj.fromUint(c - 1), int256(n)), obj.fromUint(p), "compound(c - 1, n)");
        uint256 b = 256 - _lz(c);
        int256 r = obj.sub(_mk(false, -1, c << (237 - b)), ONE);
        int256 want = obj.mul(obj.fromUint(p), _mk(false, -int256(b * n), uint256(1) << 236));
        assertEq(objE.compound(r, int256(n)), want, "compound(c 2^-b - 1, n)");
        // (1 + 2^-79)^3 and 3^150
        assertEq(objE.compound(_mk(false, -79, uint256(1) << 236), 3),
                 obj.mul(obj.fromUint(((uint256(1) << 79) + 1) ** 3), _mk(false, -237, uint256(1) << 236)), "(1 + 2^-79)^3");
    }

    function _lz(uint256 x) internal pure returns (uint256 n) {
        n = 256;
        while (x != 0) { x >>= 1; n--; }
    }

    // ---- #79: identities ---------------------------------------------------------

    function testFuzz_prop_selection(int256 wa, int256 wb, int256 wc) public view {
        int256 a = _num(wa, -300, 300);
        int256 b = _num(wb, -300, 300);
        int256 c = _num(wc, -300, 300);
        int256 lo = obj.min(a, b);
        int256 hi = obj.max(a, b);
        assertTrue((lo == a && hi == b) || (lo == b && hi == a), "min and max are the two words");
        assertEq(obj.lt(hi, lo), 0, "min <= max");
        int256 k = obj.clamp(c, lo, hi);
        assertEq(obj.lt(k, lo) + obj.lt(hi, k), 0, "clamp lands in [lo, hi]");
        int256 m = obj.avg(a, b);
        assertEq(obj.lt(m, lo) + obj.lt(hi, m), 0, "avg lies between");
        assertEq(obj.avg(a, a), a, "avg(a, a) = a");
        assertEq(obj.dist(a, b), obj.dist(b, a), "dist is symmetric");
        assertEq(obj.dist(a, b), obj.abs(obj.sub(a, b)), "dist = |a - b|");
        assertEq(obj.lerp(a, b, 0), a, "lerp at 0");
        assertEq(obj.lerp(a, b, ONE), b, "lerp at 1");
        assertEq(obj.lerp(a, a, c), a, "lerp of equal ends");
        assertEq(obj.lerp(a, b, HALF), obj.avg(a, b), "lerp at 1/2 is avg: one rounding of the same value");
    }

    function testFuzz_prop_integral(int256 w) public view {
        int256 x = _num(w, -8, 250);
        int256 r = obj.round(x);
        assertEq(obj.round(obj.neg(x)), obj.neg(r), "round is odd");
        assertEq(obj.floor(r), r, "round is integral");
        assertEq(obj.lt(HALF, obj.abs(obj.sub(r, x))), 0, "within a half");
        int256 f = obj.frac(x);
        assertEq(f, obj.sub(x, obj.floor(x)), "frac = x - floor(x)");
        if (x >= 0) assertEq(obj.add(obj.floor(x), f), x, "floor + frac = x, exactly, for x >= 0");
    }

    function testFuzz_prop_roots(int256 wa, int256 wb) public view {
        int256 a = _num(wa, -100000, 100000);
        int256 b = _num(wb, -100000, 100000);
        assertEq(obj.cbrt(obj.neg(a)), obj.neg(obj.cbrt(a)), "cbrt is odd");
        assertEq(obj.hypot(a, b), obj.hypot(obj.neg(b), a), "hypot is symmetric and even");
        assertEq(obj.hypot(a, 0), obj.abs(a));
        assertEq(obj.gavg(a, a), obj.abs(a), "gavg(a, a) = |a|");
        // a 79-bit significand cubed is exact, and its cube root is that number
        int256 c = _mk(false, int256(uint256(wb) % 2000) - 1000, (uint256(wa) >> 100) << 158);
        assertEq(obj.cbrt(obj.mul(obj.mul(c, c), c)), c, "cbrt of an exact cube");
    }

    function testFuzz_prop_bases(int16 k, int256 w) public view {
        int256 n = int256(k) % 262000;
        int256 p = _mk(false, n, uint256(1) << 236);
        assertEq(objE.exp2(obj.fromFP127(n << 128)), p, "2^n exact");
        assertEq(objE.log2(p), obj.fromFP127(n << 128), "log2 2^n = n");
        assertEq(objE.log2Up(p), obj.fromFP127(n << 128), "log2Up 2^n = n");
        int256 x = _num(w, -100, 100);
        x = obj.abs(x);
        if (x != 0 && x != ONE) {
            assertGe(_bits(objE.exp2(objE.log2(x)), x), 228, "exp2(log2 x)");
            assertGe(_bits(objE.exp10(objE.log10(x)), x), 228, "exp10(log10 x)");
        }
        int256 y = _num(w, -60, 7);
        assertEq(objH.sinh(obj.neg(y)), obj.neg(objH.sinh(y)), "sinh is odd");
        assertEq(objH.cosh(obj.neg(y)), objH.cosh(y), "cosh is even");
        assertEq(objH.tanh(obj.neg(y)), obj.neg(objH.tanh(y)), "tanh is odd");
    }

    function testFuzz_invalid_words_revert(int256 w) public view {
        // exponent 0 with any other bit set is not a number, in every op
        int256 bad = int256((uint256(w) & ~(uint256(0x7ffff) << 236)));
        vm.assume(bad != 0);
        _expectRevert(abi.encodeCall(IFP256.add, (bad, ONE)), IFP256.OutOfRange.selector, "add");
        _expectRevert(abi.encodeCall(IFP256.mul, (ONE, bad)), IFP256.OutOfRange.selector, "mul");
        _expectRevert(abi.encodeCall(IFP256.neg, (bad)), IFP256.OutOfRange.selector, "neg");
        _expectRevert(abi.encodeCall(IFP256.cmp, (bad, ONE)), IFP256.OutOfRange.selector, "cmp");
        _expectRevert(abi.encodeCall(IFP256.eq, (ONE, bad)), IFP256.OutOfRange.selector, "eq");
        _expectRevertAt(address(objE), abi.encodeCall(IFP256E.exp, (bad)), IFP256.OutOfRange.selector, "exp");
        _expectRevert(abi.encodeCall(IFP256.toFixed18, (bad)), IFP256.OutOfRange.selector, "toFixed18");
        _expectRevertAt(address(objE), abi.encodeCall(IFP256E.exp2, (bad)), IFP256.OutOfRange.selector, "exp2");
        _expectRevertAt(address(objH), abi.encodeCall(IFP256H.tanh, (bad)), IFP256.OutOfRange.selector, "tanh");
        _expectRevertAt(address(obj), abi.encodeCall(IFP256.min, (bad, ONE)), IFP256.OutOfRange.selector, "min");
        _expectRevertAt(address(obj), abi.encodeCall(IFP256.lerp, (ONE, ONE, bad)), IFP256.OutOfRange.selector, "lerp");
        _expectRevertAt(address(obj), abi.encodeCall(IFP256.round, (bad)), IFP256.OutOfRange.selector, "round");
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP256Harness} from "../base/FP256Harness.sol";
import {IFP256} from "../../contracts/src/fp256/IFP256.sol";

/// @title Equivalence256
/// @notice The deployed object and the inline library return identical
///         results, including which inputs revert and with what data, on the
///         full int256 domain; plus the algebraic identities the format
///         promises (section 15 of the design).
contract Equivalence256 is FP256Harness {
    function _objLib(bytes memory call, string memory what) internal view {
        _assertSame(_try(address(obj), call), _try(address(lib), call), what);
    }

    function testFuzz_objEqLib_add(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.add, (a, b)), "add"); }
    function testFuzz_objEqLib_sub(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.sub, (a, b)), "sub"); }
    function testFuzz_objEqLib_mul(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.mul, (a, b)), "mul"); }
    function testFuzz_objEqLib_div(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP256.div, (a, b)), "div"); }
    function testFuzz_objEqLib_sqrt(int256 x) public view { _objLib(abi.encodeCall(IFP256.sqrt, (x)), "sqrt"); }
    function testFuzz_objEqLib_exp(int256 x) public view { _objLib(abi.encodeCall(IFP256.exp, (x)), "exp"); }
    function testFuzz_objEqLib_ln(int256 x) public view { _objLib(abi.encodeCall(IFP256.ln, (x)), "ln"); }
    function testFuzz_objEqLib_pow(int256 x, int256 y) public view { _objLib(abi.encodeCall(IFP256.pow, (x, y)), "pow"); }
    function testFuzz_objEqLib_log1p(int256 x) public view { _objLib(abi.encodeCall(IFP256.log1p, (x)), "log1p"); }
    function testFuzz_objEqLib_expm1(int256 x) public view { _objLib(abi.encodeCall(IFP256.expm1, (x)), "expm1"); }
    function testFuzz_objEqLib_erf(int256 x) public view { _objLib(abi.encodeCall(IFP256.erf, (x)), "erf"); }
    function testFuzz_objEqLib_erfc(int256 x) public view { _objLib(abi.encodeCall(IFP256.erfc, (x)), "erfc"); }
    function testFuzz_objEqLib_normCdf(int256 x) public view { _objLib(abi.encodeCall(IFP256.normCdf, (x)), "normCdf"); }
    function testFuzz_objEqLib_lambertW0(int256 x) public view { _objLib(abi.encodeCall(IFP256.lambertW0, (x)), "lambertW0"); }
    function testFuzz_objEqLib_lambertWm1(int256 x) public view { _objLib(abi.encodeCall(IFP256.lambertWm1, (x)), "lambertWm1"); }
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
        assertGe(_bits(obj.exp(obj.ln(x)), x), 228, "exp(ln x)");
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

    function testFuzz_invalid_words_revert(int256 w) public view {
        // exponent 0 with any other bit set is not a number, in every op
        int256 bad = int256((uint256(w) & ~(uint256(0x7ffff) << 236)));
        vm.assume(bad != 0);
        _expectRevert(abi.encodeCall(IFP256.add, (bad, ONE)), IFP256.OutOfRange.selector, "add");
        _expectRevert(abi.encodeCall(IFP256.mul, (ONE, bad)), IFP256.OutOfRange.selector, "mul");
        _expectRevert(abi.encodeCall(IFP256.neg, (bad)), IFP256.OutOfRange.selector, "neg");
        _expectRevert(abi.encodeCall(IFP256.cmp, (bad, ONE)), IFP256.OutOfRange.selector, "cmp");
        _expectRevert(abi.encodeCall(IFP256.eq, (ONE, bad)), IFP256.OutOfRange.selector, "eq");
        _expectRevert(abi.encodeCall(IFP256.exp, (bad)), IFP256.OutOfRange.selector, "exp");
        _expectRevert(abi.encodeCall(IFP256.toFixed18, (bad)), IFP256.OutOfRange.selector, "toFixed18");
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP256Harness} from "../base/FP256Harness.sol";
import {FP256Lib} from "../../contracts/src/fp256/FP256Lib.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {ABDKMathQuad as Q} from "../../lib/abdk-libraries-solidity/ABDKMathQuad.sol";
import {console} from "forge-std/console.sol";

/// @title GasLadder256
/// @notice Gas for every FP256 op across an input ladder, for the object
///         (staticcall), the inline library, the same op in FP127Lib on the
///         same value (where it is in range) and ABDKMathQuad, the other
///         float. Prints GAS|op|idx|input|form|gas; scripts/fp127/gas_to_json.py
///         --lib fp256 writes docs/benchmarks/gas256.{json,md}.
contract GasLadder256 is FP256Harness {
    int256 constant NA = type(int256).min;

    function setUp() public override {
        super.setUp();
        obj.mul(ONE, ONE);
    }

    // ---- conversions --------------------------------------------------

    function _fp127(int256 x) internal view returns (int256, bool) {
        (bool ok, bytes memory out) = address(obj).staticcall(abi.encodeWithSignature("toFP127(int256)", x));
        return ok ? (abi.decode(out, (int256)), true) : (int256(0), false);
    }

    function _quad(int256 x) internal view returns (bytes16, bool) {
        (int256 f, bool ok) = _fp127(x);
        if (!ok) return (bytes16(0), false);
        return (Q.from128x128(f), true);
    }

    // ---- measurement --------------------------------------------------

    function _ext(address t, bytes memory data) internal view returns (int256) {
        uint256 g0 = gasleft();
        (bool ok,) = t.staticcall(data);
        uint256 g = g0 - gasleft();
        return ok ? int256(g) : NA;
    }

    function _emit(string memory op, uint256 idx, string memory input, string memory form, int256 g) internal pure {
        console.log(string.concat("GAS|", op, "|", vm.toString(idx), "|", input, "|", form, "|", g == NA ? "NA" : vm.toString(uint256(g))));
    }

    function _selfTry(bytes memory data) internal view returns (int256) {
        uint256 g0 = gasleft();
        (bool ok,) = address(this).staticcall(data);
        uint256 g = g0 - gasleft();
        return ok ? int256(g) : NA;
    }

    function cNoop(string calldata) external pure returns (int256) { return 0; }

    function _baseline() internal view returns (uint256) {
        uint256 g0 = gasleft();
        (bool ok,) = address(this).staticcall(abi.encodeWithSelector(this.cNoop.selector, "x"));
        uint256 g = g0 - gasleft();
        require(ok);
        return g;
    }

    function _net(int256 g, uint256 base) internal pure returns (int256) { return g == NA ? NA : g - int256(base); }

    // ---- entry points (external so reverts are catchable) ---------------

    function cLib1(string calldata op, int256 x) external pure returns (int256) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("sqrt")) return FP256Lib.sqrt(x);
        if (h == keccak256("exp")) return FP256Lib.exp(x);
        if (h == keccak256("ln")) return FP256Lib.ln(x);
        if (h == keccak256("neg")) return FP256Lib.neg(x);
        if (h == keccak256("abs")) return FP256Lib.abs(x);
        if (h == keccak256("sign")) return FP256Lib.sign(x);
        if (h == keccak256("toFP127")) return FP256Lib.toFP127(x);
        if (h == keccak256("fromFP127")) return FP256Lib.fromFP127(x);
        if (h == keccak256("toFixed18")) return FP256Lib.toFixed18(x);
        if (h == keccak256("fromFixed18")) return FP256Lib.fromFixed18(x);
        if (h == keccak256("fromUint")) return FP256Lib.fromUint(uint256(x));
        revert("na");
    }

    function cLib2(string calldata op, int256 a, int256 b) external pure returns (int256) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("add")) return FP256Lib.add(a, b);
        if (h == keccak256("sub")) return FP256Lib.sub(a, b);
        if (h == keccak256("mul")) return FP256Lib.mul(a, b);
        if (h == keccak256("div")) return FP256Lib.div(a, b);
        if (h == keccak256("pow")) return FP256Lib.pow(a, b);
        if (h == keccak256("cmp")) return FP256Lib.cmp(a, b);
        if (h == keccak256("lt")) return FP256Lib.lt(a, b);
        if (h == keccak256("eq")) return FP256Lib.eq(a, b);
        revert("na");
    }

    function cFp127_1(string calldata op, int256 x) external pure returns (int256) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("sqrt")) return FP127Lib.sqrt(x);
        if (h == keccak256("exp")) return FP127Lib.exp(x);
        if (h == keccak256("ln")) return FP127Lib.ln(x);
        if (h == keccak256("neg")) return FP127Lib.neg(x);
        if (h == keccak256("abs")) return FP127Lib.abs(x);
        if (h == keccak256("sign")) return FP127Lib.sign(x);
        if (h == keccak256("toFixed18")) return FP127Lib.toFixed18(x);
        if (h == keccak256("fromFixed18")) return FP127Lib.fromFixed18(x);
        revert("na");
    }

    function cFp127_2(string calldata op, int256 a, int256 b) external pure returns (int256) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("add")) return FP127Lib.add(a, b);
        if (h == keccak256("sub")) return FP127Lib.sub(a, b);
        if (h == keccak256("mul")) return FP127Lib.mul(a, b);
        if (h == keccak256("div")) return FP127Lib.div(a, b);
        if (h == keccak256("pow")) return FP127Lib.pow(a, b);
        revert("na");
    }

    function cQuad1(string calldata op, bytes16 x) external pure returns (bytes16) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("sqrt")) return Q.sqrt(x);
        if (h == keccak256("exp")) return Q.exp(x);
        if (h == keccak256("ln")) return Q.ln(x);
        if (h == keccak256("neg")) return Q.neg(x);
        if (h == keccak256("abs")) return Q.abs(x);
        revert("na");
    }

    function cQuad2(string calldata op, bytes16 a, bytes16 b) external pure returns (bytes16) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("add")) return Q.add(a, b);
        if (h == keccak256("sub")) return Q.sub(a, b);
        if (h == keccak256("mul")) return Q.mul(a, b);
        if (h == keccak256("div")) return Q.div(a, b);
        if (h == keccak256("pow")) return Q.exp(Q.mul(b, Q.ln(a)));
        revert("na");
    }

    // ---- drivers --------------------------------------------------------

    function _run1(string memory op, int256[6] memory xs, bool uintArg) internal view {
        for (uint256 i; i < xs.length; i++) {
            string memory label = vm.toString(xs[i]);
            bytes memory call = abi.encodeWithSignature(string.concat(op, uintArg ? "(uint256)" : "(int256)"), xs[i]);
            uint256 base = _baseline();
            _emit(op, i, label, "yul", _ext(address(obj), call));
            _emit(op, i, label, "lib", _net(_selfTry(abi.encodeWithSelector(this.cLib1.selector, op, xs[i])), base));
            _emit(op, i, label, "fp127lib", _fp127Gas1(op, xs[i], base));
            _emit(op, i, label, "quad", _quadGas1(op, xs[i], base));
        }
    }

    function _fp127Gas1(string memory op, int256 x, uint256 base) internal view returns (int256) {
        (int256 f, bool ok) = _fp127(x);
        if (!ok) return NA;
        return _net(_selfTry(abi.encodeWithSelector(this.cFp127_1.selector, op, f)), base);
    }

    function _quadGas1(string memory op, int256 x, uint256 base) internal view returns (int256) {
        (bytes16 q, bool ok) = _quad(x);
        if (!ok) return NA;
        return _net(_selfTry(abi.encodeWithSelector(this.cQuad1.selector, op, q)), base);
    }

    function _run2(string memory op, int256[6] memory a, int256[6] memory b) internal view {
        for (uint256 i; i < a.length; i++) {
            string memory label = string.concat(vm.toString(a[i]), ",", vm.toString(b[i]));
            uint256 base = _baseline();
            _emit(op, i, label, "yul", _ext(address(obj), abi.encodeWithSignature(string.concat(op, "(int256,int256)"), a[i], b[i])));
            _emit(op, i, label, "lib", _net(_selfTry(abi.encodeWithSelector(this.cLib2.selector, op, a[i], b[i])), base));
            _emit(op, i, label, "fp127lib", _fp127Gas2(op, a[i], b[i], base));
            _emit(op, i, label, "quad", _quadGas2(op, a[i], b[i], base));
        }
    }

    function _fp127Gas2(string memory op, int256 a, int256 b, uint256 base) internal view returns (int256) {
        (int256 fa, bool okA) = _fp127(a);
        (int256 fb, bool okB) = _fp127(b);
        if (!(okA && okB)) return NA;
        return _net(_selfTry(abi.encodeWithSelector(this.cFp127_2.selector, op, fa, fb)), base);
    }

    function _quadGas2(string memory op, int256 a, int256 b, uint256 base) internal view returns (int256) {
        (bytes16 qa, bool okA) = _quad(a);
        (bytes16 qb, bool okB) = _quad(b);
        if (!(okA && okB)) return NA;
        return _net(_selfTry(abi.encodeWithSelector(this.cQuad2.selector, op, qa, qb)), base);
    }

    // ---- the ladders ------------------------------------------------------

    function _v(int256 u, uint256 frac) internal pure returns (int256) { return _mk(false, u, frac); }
    function _nv(int256 u, uint256 frac) internal pure returns (int256) { return _mk(true, u, frac); }

    uint256 constant PI_F = 0x921fb54442d18469898cc51701b839a252049c1114cf98e804177d4c76273644; // fraction of pi (1.5707... * 2)
    uint256 constant E_F = 0x5bf0a8b1457695355fb8ac404e7a79e3b1738b079c5a6d2b53c26c8228c867f7;

    function _unary() internal pure returns (int256[6] memory xs) {
        xs = [_v(-60, 0), _v(-1, 0), ONE, _v(1, PI_F >> 20), _v(9, 0xf4240 << 216), _v(60, 0)];
    }

    function _posBinary() internal pure returns (int256[6] memory a, int256[6] memory b) {
        a = [ONE, _v(1, PI_F >> 20), _v(9, 0xf4240 << 216), _v(60, 0), _v(-60, 0), _v(300, 0)];
        b = [ONE, _v(1, E_F >> 20), _v(-2, 0x5555 << 220), _v(40, 0), _v(-40, 0), _v(-300, 0)];
    }

    function test_ladder_arith() public view {
        (int256[6] memory a, int256[6] memory b) = _posBinary();
        _run2("add", a, b);
        _run2("sub", a, b);
        _run2("mul", a, b);
        _run2("div", a, b);
        _run2("cmp", a, b);
        _run2("lt", a, b);
        _run2("eq", a, b);
    }

    function test_ladder_unary() public view {
        int256[6] memory xs = _unary();
        _run1("sqrt", xs, false);
        _run1("ln", xs, false);
        _run1("neg", xs, false);
        _run1("abs", xs, false);
        _run1("sign", xs, false);
        _run1("exp", [_nv(6, 0x4 << 232), _nv(0, 0), _v(-1, 0), ONE, _v(4, 0x4 << 232), _v(17, 0x6 << 232)], false);
    }

    function test_ladder_pow() public view {
        _run2("pow", [_v(0, 0x28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c >> 20), _v(1, PI_F >> 20), TWO, _v(3, 0x4 << 232), HALF, _v(1, 0x8 << 232)],
                     [_v(8, 0x6d << 229), _v(1, E_F >> 20), _v(3, 0x4 << 232), _v(1, 0x4 << 232), _nv(1, 0x8 << 232), TWO]);
    }

    function test_ladder_conversions() public view {
        int256[6] memory xs = _unary();
        _run1("toFP127", xs, false);
        _run1("toFixed18", xs, false);
        _run1("fromFP127", [int256(1), int256(1) << 127, int256(1) << 128, int256(3) << 127, int256(1000) << 128, -(int256(1) << 128)], false);
        _run1("fromFixed18", [int256(1), 5e17, 1e18, 3141592653589793238, 1000e18, -3141592653589793238], false);
        _run1("fromUint", [int256(1), int256(2), int256(1e18), int256(1) << 100, int256(1) << 236, int256(1) << 250], true);
    }
}

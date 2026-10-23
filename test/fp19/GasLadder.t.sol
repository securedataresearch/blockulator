// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP19Harness} from "../base/FP19Harness.sol";
import {FP19Lib} from "../../contracts/src/fp19/FP19Lib.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {ABDKMathQuad as Q} from "../../lib/abdk-libraries-solidity/ABDKMathQuad.sol";
import {console} from "forge-std/console.sol";

/// @title GasLadder19
/// @notice Gas for every FP19 op across an input ladder, for the object
///         (staticcall), the inline library, the same op in FP127Lib on the
///         same value (where it is in range) and ABDKMathQuad, the other
///         float. Prints GAS|op|idx|input|form|gas (and |typical on the
///         typical-input rows); gas is NA where the form does not offer the
///         op and REV where it does but reverted or the input is outside its
///         domain or its format's range. scripts/fp127/gas_to_json.py --lib
///         fp19 writes docs/benchmarks/gas19.{json,md}. The internal forms
///         are timed as test/fp127/GasLadder.t.sol times them (_timed).
contract GasLadder19 is FP19Harness {
    int256 constant NA = type(int256).min;
    int256 constant REV = type(int256).min + 1;
    bytes32 constant NA_REASON = keccak256(abi.encodeWithSignature("Error(string)", "na"));

    /// Each test runs as its own transaction, so the accounts setUp touched
    /// are cold again: touch every object first, so no row pays the
    /// 2,500-gas cold-account surcharge.
    function _warm() internal view {
        obj.mul(ONE, ONE);
        objE.exp(ONE);
        objH.sinh(ONE);
        objS.erf(ONE);
    }

    // ---- conversions --------------------------------------------------

    function _fp127(int256 x) internal view returns (int256, bool) {
        (bool ok, bytes memory out) = address(obj).staticcall(abi.encodeWithSignature("toFP127(int256)", x));
        return ok ? (abi.decode(out, (int256)), true) : (int256(0), false);
    }

    /// FP19 word -> binary128 directly (sign, exponent rebiased, the 236-bit
    /// fraction truncated to 112), so Quad gets every value it can hold, not
    /// only those that fit 127.128. Not ok outside binary128's normal range.
    function _quad(int256 x) internal pure returns (bytes16, bool) {
        if (x == 0) return (bytes16(0), true);
        (bool s, uint256 e, uint256 m) = _unpack(x);
        int256 qe = int256(e) - int256(BIAS) + 16383;
        if (qe < 1 || qe > 32766) return (bytes16(0), false);
        uint256 q = (s ? uint256(1) << 127 : 0) | (uint256(qe) << 112) | (m >> 124);
        return (bytes16(uint128(q)), true);
    }

    // ---- measurement --------------------------------------------------

    function _ext(address t, bytes memory data) internal view returns (int256) {
        uint256 g0 = gasleft();
        (bool ok,) = t.staticcall(data);
        uint256 g = g0 - gasleft();
        return ok ? int256(g) : REV;
    }

    function _emit(string memory op, uint256 idx, string memory input, string memory form, int256 g, string memory set) internal pure {
        string memory line = string.concat("GAS|", op, "|", vm.toString(idx), "|", input, "|", form, "|", g == NA ? "NA" : g == REV ? "REV" : vm.toString(uint256(g)));
        console.log(bytes(set).length == 0 ? line : string.concat(line, "|", set));
    }

    /// The entry point's own gasleft() window around the one library call,
    /// minus the same window around a plain assignment (op "id"): dispatch
    /// and ABI decoding stay outside, whatever the op's place in the list.
    /// A revert is NA when the entry point has no such op ("na"), else REV.
    function _timed(bytes memory call, bytes memory idCall) internal view returns (int256) {
        (bool ok, bytes memory out) = address(this).staticcall(call);
        if (!ok) return keccak256(out) == NA_REASON ? NA : REV;
        (bool okId, bytes memory outId) = address(this).staticcall(idCall);
        require(okId, "id");
        return int256(abi.decode(out, (uint256))) - int256(abi.decode(outId, (uint256)));
    }

    // ---- entry points (external so reverts are catchable) ---------------

    function cLib1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = FP19Lib.sqrt(x); g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = FP19Lib.exp(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = FP19Lib.ln(x); g = gasleft(); }
        if (h == keccak256("log1p")) { g0 = gasleft(); r = FP19Lib.log1p(x); g = gasleft(); }
        if (h == keccak256("expm1")) { g0 = gasleft(); r = FP19Lib.expm1(x); g = gasleft(); }
        if (h == keccak256("erf")) { g0 = gasleft(); r = FP19Lib.erf(x); g = gasleft(); }
        if (h == keccak256("erfc")) { g0 = gasleft(); r = FP19Lib.erfc(x); g = gasleft(); }
        if (h == keccak256("normCdf")) { g0 = gasleft(); r = FP19Lib.normCdf(x); g = gasleft(); }
        if (h == keccak256("lambertW0")) { g0 = gasleft(); r = FP19Lib.lambertW0(x); g = gasleft(); }
        if (h == keccak256("lambertWm1")) { g0 = gasleft(); r = FP19Lib.lambertWm1(x); g = gasleft(); }
        if (h == keccak256("neg")) { g0 = gasleft(); r = FP19Lib.neg(x); g = gasleft(); }
        if (h == keccak256("abs")) { g0 = gasleft(); r = FP19Lib.abs(x); g = gasleft(); }
        if (h == keccak256("sign")) { g0 = gasleft(); r = FP19Lib.sign(x); g = gasleft(); }
        if (h == keccak256("toFP127")) { g0 = gasleft(); r = FP19Lib.toFP127(x); g = gasleft(); }
        if (h == keccak256("fromFP127")) { g0 = gasleft(); r = FP19Lib.fromFP127(x); g = gasleft(); }
        if (h == keccak256("toFixed18")) { g0 = gasleft(); r = FP19Lib.toFixed18(x); g = gasleft(); }
        if (h == keccak256("fromFixed18")) { g0 = gasleft(); r = FP19Lib.fromFixed18(x); g = gasleft(); }
        if (h == keccak256("fromUint")) { g0 = gasleft(); r = FP19Lib.fromUint(uint256(x)); g = gasleft(); }
        if (h == keccak256("fromUintDown")) { g0 = gasleft(); r = FP19Lib.fromUintDown(uint256(x)); g = gasleft(); }
        if (h == keccak256("fromUintUp")) { g0 = gasleft(); r = FP19Lib.fromUintUp(uint256(x)); g = gasleft(); }
        if (h == keccak256("toUintDown")) { g0 = gasleft(); r = int256(FP19Lib.toUintDown(x)); g = gasleft(); }
        if (h == keccak256("toUintUp")) { g0 = gasleft(); r = int256(FP19Lib.toUintUp(x)); g = gasleft(); }
        if (h == keccak256("toIntDown")) { g0 = gasleft(); r = FP19Lib.toIntDown(x); g = gasleft(); }
        if (h == keccak256("toIntUp")) { g0 = gasleft(); r = FP19Lib.toIntUp(x); g = gasleft(); }
        if (h == keccak256("floor")) { g0 = gasleft(); r = FP19Lib.floor(x); g = gasleft(); }
        if (h == keccak256("ceil")) { g0 = gasleft(); r = FP19Lib.ceil(x); g = gasleft(); }
        if (h == keccak256("toFixed18Down")) { g0 = gasleft(); r = FP19Lib.toFixed18Down(x); g = gasleft(); }
        if (h == keccak256("toFixed18Up")) { g0 = gasleft(); r = FP19Lib.toFixed18Up(x); g = gasleft(); }
        if (h == keccak256("exp2")) { g0 = gasleft(); r = FP19Lib.exp2(x); g = gasleft(); }
        if (h == keccak256("exp10")) { g0 = gasleft(); r = FP19Lib.exp10(x); g = gasleft(); }
        if (h == keccak256("log2")) { g0 = gasleft(); r = FP19Lib.log2(x); g = gasleft(); }
        if (h == keccak256("log10")) { g0 = gasleft(); r = FP19Lib.log10(x); g = gasleft(); }
        if (h == keccak256("log2Up")) { g0 = gasleft(); r = FP19Lib.log2Up(x); g = gasleft(); }
        if (h == keccak256("cbrt")) { g0 = gasleft(); r = FP19Lib.cbrt(x); g = gasleft(); }
        if (h == keccak256("sinh")) { g0 = gasleft(); r = FP19Lib.sinh(x); g = gasleft(); }
        if (h == keccak256("cosh")) { g0 = gasleft(); r = FP19Lib.cosh(x); g = gasleft(); }
        if (h == keccak256("tanh")) { g0 = gasleft(); r = FP19Lib.tanh(x); g = gasleft(); }
        if (h == keccak256("atanh")) { g0 = gasleft(); r = FP19Lib.atanh(x); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = FP19Lib.inv(x); g = gasleft(); }
        if (h == keccak256("frac")) { g0 = gasleft(); r = FP19Lib.frac(x); g = gasleft(); }
        if (h == keccak256("round")) { g0 = gasleft(); r = FP19Lib.round(x); g = gasleft(); }
        if (h == keccak256("factorial")) { g0 = gasleft(); r = FP19Lib.factorial(x); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cLib2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("add")) { g0 = gasleft(); r = FP19Lib.add(a, b); g = gasleft(); }
        if (h == keccak256("sub")) { g0 = gasleft(); r = FP19Lib.sub(a, b); g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = FP19Lib.mul(a, b); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = FP19Lib.div(a, b); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = FP19Lib.pow(a, b); g = gasleft(); }
        if (h == keccak256("powu")) { g0 = gasleft(); r = FP19Lib.powu(a, b); g = gasleft(); }
        if (h == keccak256("compound")) { g0 = gasleft(); r = FP19Lib.compound(a, b); g = gasleft(); }
        if (h == keccak256("cmp")) { g0 = gasleft(); r = FP19Lib.cmp(a, b); g = gasleft(); }
        if (h == keccak256("lt")) { g0 = gasleft(); r = FP19Lib.lt(a, b); g = gasleft(); }
        if (h == keccak256("eq")) { g0 = gasleft(); r = FP19Lib.eq(a, b); g = gasleft(); }
        if (h == keccak256("mulDown")) { g0 = gasleft(); r = FP19Lib.mulDown(a, b); g = gasleft(); }
        if (h == keccak256("mulUp")) { g0 = gasleft(); r = FP19Lib.mulUp(a, b); g = gasleft(); }
        if (h == keccak256("divDown")) { g0 = gasleft(); r = FP19Lib.divDown(a, b); g = gasleft(); }
        if (h == keccak256("divUp")) { g0 = gasleft(); r = FP19Lib.divUp(a, b); g = gasleft(); }
        if (h == keccak256("min")) { g0 = gasleft(); r = FP19Lib.min(a, b); g = gasleft(); }
        if (h == keccak256("max")) { g0 = gasleft(); r = FP19Lib.max(a, b); g = gasleft(); }
        if (h == keccak256("avg")) { g0 = gasleft(); r = FP19Lib.avg(a, b); g = gasleft(); }
        if (h == keccak256("dist")) { g0 = gasleft(); r = FP19Lib.dist(a, b); g = gasleft(); }
        if (h == keccak256("zeroFloorSub")) { g0 = gasleft(); r = FP19Lib.zeroFloorSub(a, b); g = gasleft(); }
        if (h == keccak256("gavg")) { g0 = gasleft(); r = FP19Lib.gavg(a, b); g = gasleft(); }
        if (h == keccak256("hypot")) { g0 = gasleft(); r = FP19Lib.hypot(a, b); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cFp127_1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = FP127Lib.sqrt(x); g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = FP127Lib.exp(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = FP127Lib.ln(x); g = gasleft(); }
        if (h == keccak256("log1p")) { g0 = gasleft(); r = FP127Lib.log1p(x); g = gasleft(); }
        if (h == keccak256("expm1")) { g0 = gasleft(); r = FP127Lib.expm1(x); g = gasleft(); }
        if (h == keccak256("erf")) { g0 = gasleft(); r = FP127Lib.erf(x); g = gasleft(); }
        if (h == keccak256("erfc")) { g0 = gasleft(); r = FP127Lib.erfc(x); g = gasleft(); }
        if (h == keccak256("normCdf")) { g0 = gasleft(); r = FP127Lib.normCdf(x); g = gasleft(); }
        if (h == keccak256("lambertW0")) { g0 = gasleft(); r = FP127Lib.lambertW0(x); g = gasleft(); }
        if (h == keccak256("lambertWm1")) { g0 = gasleft(); r = FP127Lib.lambertWm1(x); g = gasleft(); }
        if (h == keccak256("neg")) { g0 = gasleft(); r = FP127Lib.neg(x); g = gasleft(); }
        if (h == keccak256("abs")) { g0 = gasleft(); r = FP127Lib.abs(x); g = gasleft(); }
        if (h == keccak256("sign")) { g0 = gasleft(); r = FP127Lib.sign(x); g = gasleft(); }
        if (h == keccak256("toFixed18")) { g0 = gasleft(); r = FP127Lib.toFixed18(x); g = gasleft(); }
        if (h == keccak256("fromFixed18")) { g0 = gasleft(); r = FP127Lib.fromFixed18(x); g = gasleft(); }
        if (h == keccak256("exp2")) { g0 = gasleft(); r = FP127Lib.exp2(x); g = gasleft(); }
        if (h == keccak256("exp10")) { g0 = gasleft(); r = FP127Lib.exp10(x); g = gasleft(); }
        if (h == keccak256("log2")) { g0 = gasleft(); r = FP127Lib.log2(x); g = gasleft(); }
        if (h == keccak256("log10")) { g0 = gasleft(); r = FP127Lib.log10(x); g = gasleft(); }
        if (h == keccak256("log2Up")) { g0 = gasleft(); r = FP127Lib.log2Up(x); g = gasleft(); }
        if (h == keccak256("cbrt")) { g0 = gasleft(); r = FP127Lib.cbrt(x); g = gasleft(); }
        if (h == keccak256("sinh")) { g0 = gasleft(); r = FP127Lib.sinh(x); g = gasleft(); }
        if (h == keccak256("cosh")) { g0 = gasleft(); r = FP127Lib.cosh(x); g = gasleft(); }
        if (h == keccak256("tanh")) { g0 = gasleft(); r = FP127Lib.tanh(x); g = gasleft(); }
        if (h == keccak256("atanh")) { g0 = gasleft(); r = FP127Lib.atanh(x); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = FP127Lib.inv(x); g = gasleft(); }
        if (h == keccak256("frac")) { g0 = gasleft(); r = FP127Lib.frac(x); g = gasleft(); }
        if (h == keccak256("round")) { g0 = gasleft(); r = FP127Lib.round(x); g = gasleft(); }
        if (h == keccak256("factorial")) { g0 = gasleft(); r = FP127Lib.factorial(x); g = gasleft(); }
        if (h == keccak256("floor")) { g0 = gasleft(); r = FP127Lib.floor(x); g = gasleft(); }
        if (h == keccak256("ceil")) { g0 = gasleft(); r = FP127Lib.ceil(x); g = gasleft(); }
        if (h == keccak256("toFixed18Down")) { g0 = gasleft(); r = FP127Lib.toFixed18Down(x); g = gasleft(); }
        if (h == keccak256("toFixed18Up")) { g0 = gasleft(); r = FP127Lib.toFixed18Up(x); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cFp127_2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("add")) { g0 = gasleft(); r = FP127Lib.add(a, b); g = gasleft(); }
        if (h == keccak256("sub")) { g0 = gasleft(); r = FP127Lib.sub(a, b); g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = FP127Lib.mul(a, b); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = FP127Lib.div(a, b); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = FP127Lib.pow(a, b); g = gasleft(); }
        if (h == keccak256("min")) { g0 = gasleft(); r = FP127Lib.min(a, b); g = gasleft(); }
        if (h == keccak256("max")) { g0 = gasleft(); r = FP127Lib.max(a, b); g = gasleft(); }
        if (h == keccak256("avg")) { g0 = gasleft(); r = FP127Lib.avg(a, b); g = gasleft(); }
        if (h == keccak256("dist")) { g0 = gasleft(); r = FP127Lib.dist(a, b); g = gasleft(); }
        if (h == keccak256("zeroFloorSub")) { g0 = gasleft(); r = FP127Lib.zeroFloorSub(a, b); g = gasleft(); }
        if (h == keccak256("gavg")) { g0 = gasleft(); r = FP127Lib.gavg(a, b); g = gasleft(); }
        if (h == keccak256("hypot")) { g0 = gasleft(); r = FP127Lib.hypot(a, b); g = gasleft(); }
        if (h == keccak256("mulDown")) { g0 = gasleft(); r = FP127Lib.mulDown(a, b); g = gasleft(); }
        if (h == keccak256("mulUp")) { g0 = gasleft(); r = FP127Lib.mulUp(a, b); g = gasleft(); }
        if (h == keccak256("divDown")) { g0 = gasleft(); r = FP127Lib.divDown(a, b); g = gasleft(); }
        if (h == keccak256("divUp")) { g0 = gasleft(); r = FP127Lib.divUp(a, b); g = gasleft(); }
        // b arrives as n << 128 (see _fp127Gas2)
        if (h == keccak256("powu")) { g0 = gasleft(); r = FP127Lib.powu(a, b); g = gasleft(); }
        if (h == keccak256("compound")) { g0 = gasleft(); r = FP127Lib.compound(a, b); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cQuad1(string calldata op, bytes16 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        bytes16 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = Q.sqrt(x); g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = Q.exp(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = Q.ln(x); g = gasleft(); }
        if (h == keccak256("neg")) { g0 = gasleft(); r = Q.neg(x); g = gasleft(); }
        if (h == keccak256("abs")) { g0 = gasleft(); r = Q.abs(x); g = gasleft(); }
        if (h == keccak256("exp2")) { g0 = gasleft(); r = Q.pow_2(x); g = gasleft(); }
        if (h == keccak256("log2")) { g0 = gasleft(); r = Q.log_2(x); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = Q.div(Q.fromUInt(1), x); g = gasleft(); }
        int256 n;
        int8 s8;
        if (h == keccak256("sign")) { g0 = gasleft(); s8 = Q.sign(x); g = gasleft(); }
        // toUInt and toInt truncate toward zero: floor on x >= 0
        if (h == keccak256("toUintDown")) { g0 = gasleft(); n = int256(Q.toUInt(x)); g = gasleft(); }
        if (h == keccak256("toIntDown")) { require(Q.sign(x) >= 0, "domain"); g0 = gasleft(); n = Q.toInt(x); g = gasleft(); }
        // to128x128 truncates toward zero; FP19's toFP127 rounds to nearest
        if (h == keccak256("toFP127")) { g0 = gasleft(); n = Q.to128x128(x); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    /// The conversions into Quad, from a plain integer or a 127.128 word.
    function cQuadFrom(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        bytes16 r;
        int256 y;
        if (h == keccak256("id")) { g0 = gasleft(); y = x; g = gasleft(); }
        // fromUInt truncates the significand: FP19's fromUintDown
        if (h == keccak256("fromUintDown")) { g0 = gasleft(); r = Q.fromUInt(uint256(x)); g = gasleft(); }
        // from128x128 truncates toward zero; FP19's fromFP127 rounds to nearest
        if (h == keccak256("fromFP127")) { g0 = gasleft(); r = Q.from128x128(x); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cQuad2(string calldata op, bytes16 a, bytes16 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        bytes16 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("add")) { g0 = gasleft(); r = Q.add(a, b); g = gasleft(); }
        if (h == keccak256("sub")) { g0 = gasleft(); r = Q.sub(a, b); g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = Q.mul(a, b); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = Q.div(a, b); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = Q.exp(Q.mul(b, Q.ln(a))); g = gasleft(); }
        int8 c8;
        bool e;
        if (h == keccak256("cmp")) { g0 = gasleft(); c8 = Q.cmp(a, b); g = gasleft(); }
        if (h == keccak256("eq")) { g0 = gasleft(); e = Q.eq(a, b); g = gasleft(); }
        if (h == keccak256("lt")) { g0 = gasleft(); e = Q.cmp(a, b) < 0; g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    /// The three-argument ops (#79): clamp and lerp.
    function cLib3(string calldata op, int256 a, int256 b, int256 c) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("clamp")) { g0 = gasleft(); r = FP19Lib.clamp(a, b, c); g = gasleft(); }
        if (h == keccak256("lerp")) { g0 = gasleft(); r = FP19Lib.lerp(a, b, c); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cFp127_3(string calldata op, int256 a, int256 b, int256 c) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("clamp")) { g0 = gasleft(); r = FP127Lib.clamp(a, b, c); g = gasleft(); }
        if (h == keccak256("lerp")) { g0 = gasleft(); r = FP127Lib.lerp(a, b, c); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    // ---- drivers --------------------------------------------------------

    function _row1(string memory op, uint256 i, int256 x, bool uintArg, string memory set) internal view {
        string memory label = vm.toString(x);
        bytes memory call = abi.encodeWithSignature(string.concat(op, uintArg ? "(uint256)" : "(int256)"), x);
        _emit(op, i, label, "yul", _ext(_objFor(op), call), set);
        _emit(op, i, label, "lib", _timed(abi.encodeCall(this.cLib1, (op, x)), abi.encodeCall(this.cLib1, ("id", x))), set);
        _emit(op, i, label, "fp127lib", _fp127Gas1(op, x), set);
        _emit(op, i, label, "quad", _quadGas1(op, x), set);
    }

    function _run1(string memory op, int256[6] memory xs, bool uintArg) internal view {
        for (uint256 i; i < xs.length; i++) _row1(op, i, xs[i], uintArg, "");
    }

    /// An input the form's format cannot hold is REV where the form offers
    /// the op and NA where it does not; the call on zeros only asks which.
    function _outOfRange(int256 probe) internal pure returns (int256) {
        return probe == NA ? NA : REV;
    }

    function _fp127Gas1(string memory op, int256 x) internal view returns (int256) {
        // fromFixed18 takes the plain 18-decimal integer in both libraries
        if (keccak256(bytes(op)) == keccak256("fromFixed18")) {
            return _timed(abi.encodeCall(this.cFp127_1, (op, x)), abi.encodeCall(this.cFp127_1, ("id", x)));
        }
        (int256 f, bool ok) = _fp127(x);
        if (!ok) return _outOfRange(_timed(abi.encodeCall(this.cFp127_1, (op, int256(0))), abi.encodeCall(this.cFp127_1, ("id", int256(0)))));
        return _timed(abi.encodeCall(this.cFp127_1, (op, f)), abi.encodeCall(this.cFp127_1, ("id", f)));
    }

    function _quadGas1(string memory op, int256 x) internal view returns (int256) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("fromUintDown") || h == keccak256("fromFP127")) {
            return _timed(abi.encodeCall(this.cQuadFrom, (op, x)), abi.encodeCall(this.cQuadFrom, ("id", x)));
        }
        (bytes16 q, bool ok) = _quad(x);
        if (!ok) return _outOfRange(_timed(abi.encodeCall(this.cQuad1, (op, bytes16(0))), abi.encodeCall(this.cQuad1, ("id", bytes16(0)))));
        return _timed(abi.encodeCall(this.cQuad1, (op, q)), abi.encodeCall(this.cQuad1, ("id", q)));
    }

    function _row2(string memory op, uint256 i, int256 a, int256 b, string memory set) internal view {
        string memory label = string.concat(vm.toString(a), ",", vm.toString(b));
        _emit(op, i, label, "yul", _ext(_objFor(op), abi.encodeWithSignature(string.concat(op, "(int256,int256)"), a, b)), set);
        _emit(op, i, label, "lib", _timed(abi.encodeCall(this.cLib2, (op, a, b)), abi.encodeCall(this.cLib2, ("id", a, b))), set);
        _emit(op, i, label, "fp127lib", _fp127Gas2(op, a, b), set);
        _emit(op, i, label, "quad", _quadGas2(op, a, b), set);
    }

    function _run2(string memory op, int256[6] memory a, int256[6] memory b) internal view {
        for (uint256 i; i < a.length; i++) _row2(op, i, a[i], b[i], "");
    }

    /// powu and compound take a plain integer n here; FP127's take n << 128.
    function _fp127Gas2(string memory op, int256 a, int256 b) internal view returns (int256) {
        (int256 fa, bool okA) = _fp127(a);
        bool plainN = keccak256(bytes(op)) == keccak256("powu") || keccak256(bytes(op)) == keccak256("compound");
        int256 fb;
        bool okB;
        if (plainN) {
            okB = b >= -(int256(1) << 127) && b < int256(1) << 127;
            fb = okB ? b << 128 : int256(0);
        } else {
            (fb, okB) = _fp127(b);
        }
        if (!(okA && okB)) return _outOfRange(_timed(abi.encodeCall(this.cFp127_2, (op, int256(0), int256(0))), abi.encodeCall(this.cFp127_2, ("id", int256(0), int256(0)))));
        return _timed(abi.encodeCall(this.cFp127_2, (op, fa, fb)), abi.encodeCall(this.cFp127_2, ("id", fa, fb)));
    }

    function _quadGas2(string memory op, int256 a, int256 b) internal view returns (int256) {
        (bytes16 qa, bool okA) = _quad(a);
        (bytes16 qb, bool okB) = _quad(b);
        if (!(okA && okB)) return _outOfRange(_timed(abi.encodeCall(this.cQuad2, (op, bytes16(0), bytes16(0))), abi.encodeCall(this.cQuad2, ("id", bytes16(0), bytes16(0)))));
        return _timed(abi.encodeCall(this.cQuad2, (op, qa, qb)), abi.encodeCall(this.cQuad2, ("id", qa, qb)));
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
        _warm();
        (int256[6] memory a, int256[6] memory b) = _posBinary();
        _run2("add", a, b);
        _run2("sub", a, b);
        _run2("mul", a, b);
        _run2("div", a, b);
        _run2("cmp", a, b);
        _run2("lt", a, b);
        _run2("eq", a, b);
        // release four: directed rounding of the product and the quotient
        _run2("mulDown", a, b);
        _run2("mulUp", a, b);
        _run2("divDown", a, b);
        _run2("divUp", a, b);
    }

    function test_ladder_unary() public view {
        _warm();
        int256[6] memory xs = _unary();
        _run1("sqrt", xs, false);
        _run1("ln", xs, false);
        _run1("neg", xs, false);
        _run1("abs", xs, false);
        _run1("sign", xs, false);
        _run1("exp", [_nv(6, 0x4 << 232), _nv(0, 0), _v(-1, 0), ONE, _v(4, 0x4 << 232), _v(17, 0x6 << 232)], false);
        _run1("log1p", [_v(-60, 0), _v(-30, 0), _nv(-9, 0), _v(-8, 0), _v(-1, 0), _v(9, 0xf4240 << 216)], false);
        _run1("expm1", [_v(-60, 0), _v(-30, 0), _nv(-9, 0), _v(-8, 0), _nv(-1, 0), _v(4, 0x4 << 232)], false);
        // the erf family: the series (below 1/2), the anchors (to 4), the continued fraction, the deep tail
        _run1("erf", [_v(-30, 0), _v(-2, 0), ONE, _v(1, 0x8 << 232), _v(2, 0x4 << 232), _v(3, 0x2 << 232)], false);
        _run1("erfc", [_v(-2, 0), ONE, _v(1, 0x8 << 232), _v(2, 0x4 << 232), _v(3, 0x2 << 232), _v(8, 0x9 << 232)], false);
        _run1("normCdf", [_nv(-2, 0), _nv(0, 0), _nv(2, 0x8 << 232), _nv(3, 0x2 << 232), _nv(5, 0), _nv(9, 0x1 << 232)], false);
        // Lambert W: the branch-point series, Newton near the branch, the origin, the log form, the far end
        _run1("lambertW0", [_nv(-2, 0x78b56362cb << 200), _nv(-2, 0x78b56 << 216), _nv(-4, 0), ONE, _v(4, 0), _v(100, 0)], false);
        _run1("lambertWm1", [_nv(-2, 0x78b56362cb << 200), _nv(-2, 0x78b56 << 216), _nv(-3, 0), _nv(-10, 0), _nv(-60, 0), _nv(-1000, 0)], false);
    }

    function test_ladder_pow() public view {
        _warm();
        _run2("pow", [_v(0, 0x28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c >> 20), _v(1, PI_F >> 20), TWO, _v(3, 0x4 << 232), HALF, _v(1, 0x8 << 232)],
                     [_v(8, 0x6d << 229), _v(1, E_F >> 20), _v(3, 0x4 << 232), _v(1, 0x4 << 232), _nv(1, 0x8 << 232), TWO]);
    }

    /// powu and compound take a plain integer n (FP127's column gets n << 128);
    /// Quad has neither.
    function test_ladder_powu() public view {
        _warm();
        _run2("powu", [_v(0, 0x28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c28f5c >> 20), _v(1, PI_F >> 20), TWO, _v(0, 1 << 200), HALF, _v(-1, 0x8 << 232)],
                      [int256(2), int256(12), int256(365), int256(31536000), int256(-10000), int256(1) << 100]);
        _run2("compound", [_v(-30, 0), _v(-12, 0), _v(-4, 0x9999 << 220), _nv(-5, 0), _v(-8, 0x8 << 232), _v(-29, 0x5 << 232)],
                      [int256(365), int256(10000), int256(10), int256(100), int256(-365), int256(315360000)]);
    }

    function _row3(string memory op, uint256 i, int256 a, int256 b, int256 c, string memory set) internal view {
        string memory label = string.concat(vm.toString(a), ",", vm.toString(b), ",", vm.toString(c));
        _emit(op, i, label, "yul", _ext(_objFor(op), abi.encodeWithSignature(string.concat(op, "(int256,int256,int256)"), a, b, c)), set);
        _emit(op, i, label, "lib", _timed(abi.encodeCall(this.cLib3, (op, a, b, c)), abi.encodeCall(this.cLib3, ("id", a, b, c))), set);
        _emit(op, i, label, "fp127lib", _fp127Gas3(op, a, b, c), set);
        _emit(op, i, label, "quad", NA, set);
    }

    function _run3(string memory op, int256[6] memory a, int256[6] memory b, int256[6] memory c) internal view {
        for (uint256 i; i < a.length; i++) _row3(op, i, a[i], b[i], c[i], "");
    }

    function _fp127Gas3(string memory op, int256 a, int256 b, int256 c) internal view returns (int256) {
        (int256 fa, bool okA) = _fp127(a);
        (int256 fb, bool okB) = _fp127(b);
        (int256 fc, bool okC) = _fp127(c);
        if (!(okA && okB && okC)) return _outOfRange(_timed(abi.encodeCall(this.cFp127_3, (op, int256(0), int256(0), int256(0))), abi.encodeCall(this.cFp127_3, ("id", int256(0), int256(0), int256(0)))));
        return _timed(abi.encodeCall(this.cFp127_3, (op, fa, fb, fc)), abi.encodeCall(this.cFp127_3, ("id", fa, fb, fc)));
    }

    // ---- typical inputs -------------------------------------------------
    // The ladder words are mostly integers and powers of two. The typical
    // rows draw TYPICAL words per op from keccak256("typical", op, i): an
    // exponent uniform in [elo, ehi] and 236 random fraction bits, the sign
    // by sgn (1 positive, -1 negative, 0 either).

    uint256 constant TYPICAL = 8;

    function _rnd(string memory op, uint256 i) internal pure returns (uint256) {
        return uint256(keccak256(abi.encode("typical", op, i)));
    }

    function _typ(string memory op, uint256 i, int256 elo, int256 ehi, int256 sgn) internal pure returns (int256 x) {
        uint256 h = _rnd(op, i);
        int256 e = elo + int256(h % uint256(ehi - elo + 1));
        uint256 f = uint256(keccak256(abi.encode(h))) >> 20;
        bool neg = sgn < 0 || (sgn == 0 && (h >> 64) & 1 == 1);
        x = _mk(neg, e, f);
    }

    function _typ1(string memory op, int256 elo, int256 ehi, int256 sgn) internal view {
        for (uint256 i; i < TYPICAL; i++) _row1(op, i, _typ(op, i, elo, ehi, sgn), false, "typical");
    }

    /// A small rate r below 2^-k and a plain integer n of up to k bits, so
    /// (1 + r)^n stays near one.
    function _typRate(string memory op, uint256 i) internal pure returns (int256 r, int256 n) {
        uint256 h = _rnd(op, i + 1000);
        uint256 k = 1 + h % 20;
        n = int256(2 + (h >> 64) % ((uint256(1) << k) - 1));
        r = _typ(op, i, -40, -int256(k) - 1, 1);
    }

    function test_ladder_typical() public view {
        _warm();
        _typ1("sqrt", -300, 300, 1);
        _typ1("exp", -6, 5, 0);
        _typ1("ln", -60, 60, 1);
        _typ1("log1p", -30, 4, 1);
        _typ1("expm1", -30, 5, 0);
        _typ1("erf", -6, 2, 0);
        _typ1("erfc", -4, 3, 0);
        _typ1("normCdf", -4, 3, 0);
        _typ1("lambertW0", -10, 40, 1);
        _typ1("lambertWm1", -60, -3, -1);
        // #79
        _typ1("exp2", -6, 6, 0);
        _typ1("exp10", -6, 5, 0);
        _typ1("log2", -60, 60, 1);
        _typ1("log10", -60, 60, 1);
        _typ1("cbrt", -300, 300, 0);
        _typ1("sinh", -6, 5, 0);
        _typ1("cosh", -6, 5, 0);
        _typ1("tanh", -6, 4, 0);
        _typ1("atanh", -12, -1, 0);
        for (uint256 i; i < TYPICAL; i++) {
            _row2("pow", i, _typ("pow", i, -4, 4, 1), _typ("pow", i + 100, -4, 3, 0), "typical");
            (int256 r, int256 n) = _typRate("powu", i);
            _row2("powu", i, FP19Lib.add(ONE, r), n, "typical");
            (r, n) = _typRate("compound", i);
            _row2("compound", i, r, n, "typical");
            _row2("hypot", i, _typ("hypot", i, -60, 60, 0), _typ("hypot", i + 100, -60, 60, 0), "typical");
            _row2("gavg", i, _typ("gavg", i, -60, 60, 1), _typ("gavg", i + 100, -60, 60, 1), "typical");
            _row3("lerp", i, _typ("lerp", i, -8, 8, 0), _typ("lerp", i + 100, -8, 8, 0), _typ("lerp", i + 200, -4, -1, 1), "typical");
        }
    }

    function test_ladder_conversions() public view {
        _warm();
        int256[6] memory xs = _unary();
        _run1("toFP127", xs, false);
        _run1("toFixed18", xs, false);
        _run1("fromFP127", [int256(1), int256(1) << 127, int256(1) << 128, int256(3) << 127, int256(1000) << 128, -(int256(1) << 128)], false);
        _run1("fromFixed18", [int256(1), 5e17, 1e18, 3141592653589793238, 1000e18, -3141592653589793238], false);
        _run1("fromUint", [int256(1), int256(2), int256(1e18), int256(1) << 100, int256(1) << 236, int256(1) << 250], true);
        // release four: the edge
        _run1("fromUintDown", [int256(1), int256(2), int256(1e18), int256(1) << 100, int256(1) << 236, (int256(1) << 250) + 12345], true);
        _run1("fromUintUp", [int256(1), int256(2), int256(1e18), int256(1) << 100, int256(1) << 236, (int256(1) << 250) + 12345], true);
        int256[6] memory amts = [_v(-60, 0), _v(-1, 0), ONE, _v(1, PI_F >> 20), _v(59, 0xf4240 << 216), _v(200, 1)];
        _run1("toUintDown", amts, false);
        _run1("toUintUp", amts, false);
        _run1("toIntDown", amts, false);
        _run1("toIntUp", amts, false);
        _run1("floor", amts, false);
        _run1("ceil", amts, false);
        _run1("toFixed18Down", xs, false);
        _run1("toFixed18Up", xs, false);
    }

    // ---- #79 ------------------------------------------------------------------

    function test_ladder_x2() public view {
        _warm();
        int256[6] memory xs = _unary();
        // integral x skip the kernel; the rest take it
        _run1("exp2", [_nv(-30, 0x1234 << 220), _nv(2, PI_F >> 20), _v(-1, 0), ONE, _v(4, E_F >> 20), _v(14, PI_F >> 20)], false);
        _run1("exp10", [_nv(-30, 0x1234 << 220), _nv(2, PI_F >> 20), _v(-1, 0), ONE, _v(4, E_F >> 20), _v(14, PI_F >> 20)], false);
        _run1("log2", xs, false);
        _run1("log10", xs, false);
        _run1("log2Up", xs, false);
        _run1("cbrt", xs, false);
        // the hyperbolics: the series below 1/2, the kernel above, the far end
        _run1("sinh", [_v(-60, 0), _v(-2, 0), _nv(-1, 0x8 << 232), ONE, _v(4, 0x4 << 232), _v(17, 0x6 << 232)], false);
        _run1("cosh", [_v(-60, 0), _v(-2, 0), _nv(-1, 0x8 << 232), ONE, _v(4, 0x4 << 232), _v(17, 0x6 << 232)], false);
        _run1("tanh", [_v(-60, 0), _v(-2, 0), _nv(-1, 0x8 << 232), ONE, _v(4, 0x4 << 232), _v(7, 0)], false);
        _run1("atanh", [_v(-60, 0), _v(-6, 0), _nv(-4, 0), _v(-2, 0), _v(-1, 0x8 << 232), _nv(-1, (uint256(1) << 236) - 1)], false);
    }

    function test_ladder_x3() public view {
        _warm();
        int256[6] memory xs = _unary();
        (int256[6] memory a, int256[6] memory b) = _posBinary();
        _run2("min", a, b);
        _run2("max", a, b);
        _run2("avg", a, b);
        _run2("dist", a, b);
        _run2("zeroFloorSub", a, b);
        _run2("gavg", a, b);
        _run2("hypot", a, b);
        _run1("inv", xs, false);
        _run1("frac", [_v(-60, 0), _v(-1, 0), _nv(1, PI_F >> 20), _v(1, PI_F >> 20), _v(59, 0xf4240 << 216), _v(200, 1)], false);
        _run1("round", [_v(-60, 0), _v(-1, 0), _nv(1, PI_F >> 20), _v(1, PI_F >> 20), _v(59, 0xf4240 << 216), _v(200, 1)], false);
        _run1("factorial", [ONE, _v(2, 0x4 << 232), _v(4, 0), _v(6, 0x9 << 230), _v(9, 0xf4 << 228), _v(14, 0x3e << 230)], false);
        _run3("clamp", xs, [_v(-2, 0), _v(-2, 0), _v(-2, 0), _v(-2, 0), _v(-2, 0), _v(-2, 0)], [TWO, TWO, TWO, TWO, TWO, TWO]);
        _run3("lerp", a, b, [HALF, _v(-2, 0), _nv(0, 0), _v(3, 0), _v(-100, 0), _v(100, 0)]);
    }
}

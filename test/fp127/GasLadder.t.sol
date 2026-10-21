// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP127Harness} from "../base/FP127Harness.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {console} from "forge-std/console.sol";
import {ABDKMath64x64} from "../../lib/abdk-libraries-solidity/ABDKMath64x64.sol";
import {FixedPointMathLib} from "../../lib/solady/src/utils/FixedPointMathLib.sol";
import {SD59x18, sd} from "../../lib/prb-math/src/SD59x18.sol";
import * as PRB from "../../lib/prb-math/src/sd59x18/Math.sol";
import {ABDKMathQuad as Q} from "../../lib/abdk-libraries-solidity/ABDKMathQuad.sol";
import {LogExpMath} from "../../contracts/src/ladder/vendor/balancer/LogExpMath.sol";

/// @title GasLadder
/// @notice Gas for every op across an input ladder, for every form:
///         huff (Sepolia bytecode, staticcall), yul (object, staticcall),
///         caller (FP127Caller, two hops), lib (FP127Lib, internal), and the
///         competitor libraries abdk / solady / prb / quad / balancer as
///         internal calls on the same inputs converted once to their
///         representation.
///
/// Prints GAS|op|idx|input|form|gas (NA when the form reverted or lacks the
/// op). scripts/fp127/gas_to_json.py turns the lines into gas.json.
contract GasLadder is FP127Harness {
    int256 constant PI = 1068362306129446170624574138052468108800;
    int256 constant E_ = 924983374546220337150911035843336795079;
    int256 constant NA = type(int256).min;

    function setUp() public override {
        super.setUp();
        huff.mulRaw(uint256(ONE), uint256(ONE));
        obj.mul(ONE, ONE);
        caller.mul(ONE, ONE);
    }

    // ---- conversions --------------------------------------------------

    function _wad(int256 x) internal pure returns (int256) { return FP127Lib.toFixed18(x); }

    /// 127.128 -> binary128 (ABDKMathQuad's own conversion, to nearest).
    function _quad(int256 x) internal pure returns (bytes16) { return Q.from128x128(x); }

    /// 127.128 -> 64.64; NA when it does not fit int128.
    function _abdk(int256 x) internal pure returns (int128, bool) {
        int256 v = x >> 64;
        if (v > type(int128).max || v < type(int128).min) return (0, false);
        return (int128(v), true);
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

    function _fp127Rows(string memory op, uint256 idx, string memory label, bytes memory newCall, bytes memory huffCall, int256 libGas) internal view {
        _emit(op, idx, label, "huff", _ext(address(huff), huffCall));
        _emit(op, idx, label, "yul", _ext(address(obj), newCall));
        _emit(op, idx, label, "caller", _ext(address(caller), newCall));
        _emit(op, idx, label, "lib", libGas);
    }

    // The competitor calls are wrapped in external self-calls so a revert
    // inside the library is caught and recorded as NA.
    function _selfTry(bytes memory data) internal view returns (int256) {
        uint256 g0 = gasleft();
        (bool ok,) = address(this).staticcall(data);
        uint256 g = g0 - gasleft();
        return ok ? int256(g) : NA;
    }

    // ---- ladders ------------------------------------------------------

    function _unary() internal pure returns (int256[7] memory xs) {
        xs = [ONE >> 60, ONE / 2, ONE, PI, 1000 * ONE, ONE << 60, -PI];
    }

    function _posUnary() internal pure returns (int256[7] memory xs) {
        xs = [ONE >> 60, ONE / 2, ONE, PI, 1000 * ONE, ONE << 60, ONE << 120];
    }

    function _binary() internal pure returns (int256[6] memory a, int256[6] memory b) {
        a = [ONE, PI, -PI, 1000 * ONE, ONE << 60, ONE >> 60];
        b = [ONE, E_, E_, ONE / 3, ONE << 40, ONE >> 40];
    }

    // ---- competitor entry points (external so reverts are catchable) ----

    function cAbdk1(string calldata op, int128 x) external pure returns (int128 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("exp")) return ABDKMath64x64.exp(x);
        if (h == keccak256("exp2")) return ABDKMath64x64.exp_2(x);
        if (h == keccak256("ln")) return ABDKMath64x64.ln(x);
        if (h == keccak256("log2")) return ABDKMath64x64.log_2(x);
        if (h == keccak256("sqrt")) return ABDKMath64x64.sqrt(x);
        if (h == keccak256("inv")) return ABDKMath64x64.inv(x);
        if (h == keccak256("abs")) return ABDKMath64x64.abs(x);
        if (h == keccak256("neg")) return ABDKMath64x64.neg(x);
        revert("na");
    }

    function cAbdk2(string calldata op, int128 a, int128 b) external pure returns (int128 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("mul")) return ABDKMath64x64.mul(a, b);
        if (h == keccak256("div")) return ABDKMath64x64.div(a, b);
        if (h == keccak256("add")) return ABDKMath64x64.add(a, b);
        if (h == keccak256("sub")) return ABDKMath64x64.sub(a, b);
        if (h == keccak256("avg")) return ABDKMath64x64.avg(a, b);
        if (h == keccak256("gavg")) return ABDKMath64x64.gavg(a, b);
        if (h == keccak256("pow")) return ABDKMath64x64.pow(a, uint256(int256(b >> 64)));
        revert("na");
    }

    function cSolady1(string calldata op, int256 x) external pure returns (int256 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("exp")) return FixedPointMathLib.expWad(x);
        if (h == keccak256("ln")) return FixedPointMathLib.lnWad(x);
        if (h == keccak256("sqrt")) return int256(FixedPointMathLib.sqrtWad(uint256(x)));
        if (h == keccak256("cbrt")) return int256(FixedPointMathLib.cbrtWad(uint256(x)));
        if (h == keccak256("lambertW0")) return FixedPointMathLib.lambertW0Wad(x);
        if (h == keccak256("inv")) return FixedPointMathLib.sDivWad(1e18, x);
        revert("na");
    }

    function cSolady2(string calldata op, int256 a, int256 b) external pure returns (int256 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("mul")) return FixedPointMathLib.sMulWad(a, b);
        if (h == keccak256("div")) return FixedPointMathLib.sDivWad(a, b);
        if (h == keccak256("pow")) return FixedPointMathLib.powWad(a, b);
        // Solady's directed WAD ops are unsigned
        if (h == keccak256("mulDown") && a >= 0 && b >= 0) return int256(FixedPointMathLib.mulWad(uint256(a), uint256(b)));
        if (h == keccak256("mulUp") && a >= 0 && b >= 0) return int256(FixedPointMathLib.mulWadUp(uint256(a), uint256(b)));
        if (h == keccak256("divDown") && a >= 0 && b > 0) return int256(FixedPointMathLib.divWad(uint256(a), uint256(b)));
        if (h == keccak256("divUp") && a >= 0 && b > 0) return int256(FixedPointMathLib.divWadUp(uint256(a), uint256(b)));
        if (h == keccak256("add")) return a + b;
        if (h == keccak256("sub")) return a - b;
        revert("na");
    }

    function cPrb1(string calldata op, int256 x) external pure returns (int256 r) {
        bytes32 h = keccak256(bytes(op));
        SD59x18 v = sd(x);
        if (h == keccak256("exp")) return PRB.exp(v).unwrap();
        if (h == keccak256("exp2")) return PRB.exp2(v).unwrap();
        if (h == keccak256("ln")) return PRB.ln(v).unwrap();
        if (h == keccak256("log2")) return PRB.log2(v).unwrap();
        if (h == keccak256("log10")) return PRB.log10(v).unwrap();
        if (h == keccak256("sqrt")) return PRB.sqrt(v).unwrap();
        if (h == keccak256("inv")) return PRB.inv(v).unwrap();
        if (h == keccak256("abs")) return PRB.abs(v).unwrap();
        if (h == keccak256("floor")) return PRB.floor(v).unwrap();
        if (h == keccak256("ceil")) return PRB.ceil(v).unwrap();
        if (h == keccak256("frac")) return PRB.frac(v).unwrap();
        if (h == keccak256("sign")) return PRB.sign(v).unwrap();
        revert("na");
    }

    function cPrb2(string calldata op, int256 a, int256 b) external pure returns (int256 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("mul")) return PRB.mul(sd(a), sd(b)).unwrap();
        if (h == keccak256("div")) return PRB.div(sd(a), sd(b)).unwrap();
        if (h == keccak256("pow")) return PRB.pow(sd(a), sd(b)).unwrap();
        if (h == keccak256("avg")) return PRB.avg(sd(a), sd(b)).unwrap();
        if (h == keccak256("gavg")) return PRB.gm(sd(a), sd(b)).unwrap();
        if (h == keccak256("add")) return a + b;
        if (h == keccak256("sub")) return a - b;
        revert("na");
    }

    function cQuad1(string calldata op, bytes16 x) external pure returns (bytes16 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("exp")) return Q.exp(x);
        if (h == keccak256("exp2")) return Q.pow_2(x);
        if (h == keccak256("ln")) return Q.ln(x);
        if (h == keccak256("log2")) return Q.log_2(x);
        if (h == keccak256("sqrt")) return Q.sqrt(x);
        if (h == keccak256("inv")) return Q.div(Q.fromUInt(1), x);
        if (h == keccak256("abs")) return Q.abs(x);
        if (h == keccak256("neg")) return Q.neg(x);
        revert("na");
    }

    function cQuad2(string calldata op, bytes16 a, bytes16 b) external pure returns (bytes16 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("mul")) return Q.mul(a, b);
        if (h == keccak256("div")) return Q.div(a, b);
        if (h == keccak256("add")) return Q.add(a, b);
        if (h == keccak256("sub")) return Q.sub(a, b);
        if (h == keccak256("pow")) return Q.exp(Q.mul(b, Q.ln(a)));
        revert("na");
    }

    function cBal1(string calldata op, int256 x) external pure returns (int256 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("exp")) return LogExpMath.exp(x);
        if (h == keccak256("ln")) return LogExpMath.ln(x);
        if (h == keccak256("sqrt")) return int256(LogExpMath.pow(uint256(x), 5e17));
        if (h == keccak256("cbrt")) return int256(LogExpMath.pow(uint256(x), 333333333333333333));
        revert("na");
    }

    function cBal2(string calldata op, int256 a, int256 b) external pure returns (int256 r) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("pow")) return int256(LogExpMath.pow(uint256(a), uint256(b)));
        if (h == keccak256("mul")) return a * b / 1e18;
        if (h == keccak256("div")) return a * 1e18 / b;
        revert("na");
    }

    /// Gas of the external self-call minus the gas of an empty self-call,
    /// so competitor numbers approximate an internal call like FP127Lib.
    function cNoop(string calldata) external pure returns (int256) { return 0; }

    function _baseline() internal view returns (uint256) {
        uint256 g0 = gasleft();
        (bool ok,) = address(this).staticcall(abi.encodeWithSelector(this.cNoop.selector, "x"));
        uint256 g = g0 - gasleft();
        require(ok);
        return g;
    }

    function _comp1(string memory op, uint256 idx, string memory label, int256 x) internal view {
        uint256 base = _baseline();
        (int128 xa, bool okA) = _abdk(x);
        int256 g = okA ? _selfTry(abi.encodeWithSelector(this.cAbdk1.selector, op, xa)) : NA;
        _emit(op, idx, label, "abdk", g == NA ? NA : g - int256(base));
        g = _selfTry(abi.encodeWithSelector(this.cSolady1.selector, op, _wad(x)));
        _emit(op, idx, label, "solady", g == NA ? NA : g - int256(base));
        g = _selfTry(abi.encodeWithSelector(this.cPrb1.selector, op, _wad(x)));
        _emit(op, idx, label, "prb", g == NA ? NA : g - int256(base));
        g = _selfTry(abi.encodeWithSelector(this.cQuad1.selector, op, _quad(x)));
        _emit(op, idx, label, "quad", g == NA ? NA : g - int256(base));
        g = _selfTry(abi.encodeWithSelector(this.cBal1.selector, op, _wad(x)));
        _emit(op, idx, label, "balancer", g == NA ? NA : g - int256(base));
    }

    function _comp2(string memory op, uint256 idx, string memory label, int256 a, int256 b) internal view {
        uint256 base = _baseline();
        (int128 aa, bool okA) = _abdk(a);
        (int128 ba, bool okB) = _abdk(b);
        int256 g = (okA && okB) ? _selfTry(abi.encodeWithSelector(this.cAbdk2.selector, op, aa, ba)) : NA;
        _emit(op, idx, label, "abdk", g == NA ? NA : g - int256(base));
        g = _selfTry(abi.encodeWithSelector(this.cSolady2.selector, op, _wad(a), _wad(b)));
        _emit(op, idx, label, "solady", g == NA ? NA : g - int256(base));
        g = _selfTry(abi.encodeWithSelector(this.cPrb2.selector, op, _wad(a), _wad(b)));
        _emit(op, idx, label, "prb", g == NA ? NA : g - int256(base));
        g = _selfTry(abi.encodeWithSelector(this.cQuad2.selector, op, _quad(a), _quad(b)));
        _emit(op, idx, label, "quad", g == NA ? NA : g - int256(base));
        g = _selfTry(abi.encodeWithSelector(this.cBal2.selector, op, _wad(a), _wad(b)));
        _emit(op, idx, label, "balancer", g == NA ? NA : g - int256(base));
    }

    // ---- FP127Lib internal timing per op ------------------------------
    // Each op is timed as a direct internal call. Reverts are caught by
    // routing through LibUser (external), minus the external baseline.

    function _libGas1(string memory op, int256 x) internal view returns (int256) {
        uint256 base = _baseline();
        int256 g = _selfTry(abi.encodeWithSelector(this.cLib1.selector, op, x));
        return g == NA ? NA : g - int256(base);
    }

    function _libGas2(string memory op, int256 a, int256 b) internal view returns (int256) {
        uint256 base = _baseline();
        int256 g = _selfTry(abi.encodeWithSelector(this.cLib2.selector, op, a, b));
        return g == NA ? NA : g - int256(base);
    }

    function cLib1(string calldata op, int256 x) external pure returns (int256) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("exp")) return FP127Lib.exp(x);
        if (h == keccak256("exp2")) return FP127Lib.exp2(x);
        if (h == keccak256("exp10")) return FP127Lib.exp10(x);
        if (h == keccak256("ln")) return FP127Lib.ln(x);
        if (h == keccak256("log2")) return FP127Lib.log2(x);
        if (h == keccak256("log10")) return FP127Lib.log10(x);
        if (h == keccak256("log2Up")) return FP127Lib.log2Up(x);
        if (h == keccak256("sqrt")) return FP127Lib.sqrt(x);
        if (h == keccak256("cbrt")) return FP127Lib.cbrt(x);
        if (h == keccak256("inv")) return FP127Lib.inv(x);
        if (h == keccak256("abs")) return FP127Lib.abs(x);
        if (h == keccak256("neg")) return FP127Lib.neg(x);
        if (h == keccak256("sign")) return FP127Lib.sign(x);
        if (h == keccak256("floor")) return FP127Lib.floor(x);
        if (h == keccak256("ceil")) return FP127Lib.ceil(x);
        if (h == keccak256("frac")) return FP127Lib.frac(x);
        if (h == keccak256("round")) return FP127Lib.round(x);
        if (h == keccak256("factorial")) return FP127Lib.factorial(x);
        if (h == keccak256("lambertW0")) return FP127Lib.lambertW0(x);
        if (h == keccak256("lambertWm1")) return FP127Lib.lambertWm1(x);
        if (h == keccak256("pi")) return FP127Lib.pi(x);
        if (h == keccak256("log1p")) return FP127Lib.log1p(x);
        if (h == keccak256("expm1")) return FP127Lib.expm1(x);
        if (h == keccak256("sinh")) return FP127Lib.sinh(x);
        if (h == keccak256("cosh")) return FP127Lib.cosh(x);
        if (h == keccak256("tanh")) return FP127Lib.tanh(x);
        if (h == keccak256("atanh")) return FP127Lib.atanh(x);
        if (h == keccak256("erf")) return FP127Lib.erf(x);
        if (h == keccak256("erfc")) return FP127Lib.erfc(x);
        if (h == keccak256("normCdf")) return FP127Lib.normCdf(x);
        if (h == keccak256("fromFixed18")) return FP127Lib.fromFixed18(x);
        if (h == keccak256("toFixed18")) return FP127Lib.toFixed18(x);
        if (h == keccak256("toFixed18Down")) return FP127Lib.toFixed18Down(x);
        if (h == keccak256("toFixed18Up")) return FP127Lib.toFixed18Up(x);
        revert("na");
    }

    function cLib2(string calldata op, int256 a, int256 b) external pure returns (int256) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("add")) return FP127Lib.add(a, b);
        if (h == keccak256("sub")) return FP127Lib.sub(a, b);
        if (h == keccak256("mul")) return FP127Lib.mul(a, b);
        if (h == keccak256("div")) return FP127Lib.div(a, b);
        if (h == keccak256("pow")) return FP127Lib.pow(a, b);
        if (h == keccak256("powu")) return FP127Lib.powu(a, b);
        if (h == keccak256("compound")) return FP127Lib.compound(a, b);
        if (h == keccak256("min")) return FP127Lib.min(a, b);
        if (h == keccak256("max")) return FP127Lib.max(a, b);
        if (h == keccak256("avg")) return FP127Lib.avg(a, b);
        if (h == keccak256("gavg")) return FP127Lib.gavg(a, b);
        if (h == keccak256("hypot")) return FP127Lib.hypot(a, b);
        if (h == keccak256("dist")) return FP127Lib.dist(a, b);
        if (h == keccak256("zeroFloorSub")) return FP127Lib.zeroFloorSub(a, b);
        if (h == keccak256("gcd")) return FP127Lib.gcd(a, b);
        if (h == keccak256("mulDown")) return FP127Lib.mulDown(a, b);
        if (h == keccak256("mulUp")) return FP127Lib.mulUp(a, b);
        if (h == keccak256("divDown")) return FP127Lib.divDown(a, b);
        if (h == keccak256("divUp")) return FP127Lib.divUp(a, b);
        revert("na");
    }

    // ---- drivers --------------------------------------------------------

    function _run1(string memory op, int256[7] memory xs, bool competitors) internal view {
        for (uint256 i; i < xs.length; i++) {
            string memory label = vm.toString(xs[i]);
            bytes memory newCall = abi.encodeWithSignature(string.concat(op, "(int256)"), xs[i]);
            // the legacy conversions have no Raw suffix
            bool conv = keccak256(bytes(op)) == keccak256("fromFixed18") || keccak256(bytes(op)) == keccak256("toFixed18");
            bytes memory huffCall = abi.encodeWithSignature(string.concat(op, conv ? "(uint256)" : "Raw(uint256)"), uint256(xs[i]));
            _fp127Rows(op, i, label, newCall, huffCall, _libGas1(op, xs[i]));
            if (competitors) _comp1(op, i, label, xs[i]);
        }
    }

    function _run2(string memory op, int256[6] memory a, int256[6] memory b, bool competitors) internal view {
        for (uint256 i; i < a.length; i++) {
            string memory label = string.concat(vm.toString(a[i]), ",", vm.toString(b[i]));
            bytes memory newCall = abi.encodeWithSignature(string.concat(op, "(int256,int256)"), a[i], b[i]);
            bytes memory huffCall = abi.encodeWithSignature(string.concat(op, "Raw(uint256,uint256)"), uint256(a[i]), uint256(b[i]));
            _fp127Rows(op, i, label, newCall, huffCall, _libGas2(op, a[i], b[i]));
            if (competitors) _comp2(op, i, label, a[i], b[i]);
        }
    }

    function test_ladder_arith() public view {
        (int256[6] memory a, int256[6] memory b) = _binary();
        _run2("add", a, b, true);
        _run2("sub", a, b, true);
        _run2("mul", a, b, true);
        _run2("div", a, b, true);
        _run2("avg", a, b, true);
        _run2("dist", a, b, false);
        _run2("zeroFloorSub", a, b, false);
        _run2("min", a, b, false);
        _run2("max", a, b, false);
        _run2("gcd", [12 * ONE, 1000003 * ONE, 18 * ONE, ONE << 100, 7 * ONE, 0], [18 * ONE, 999983 * ONE, 6 * ONE, ONE << 90, 0, 5 * ONE], false);
    }

    function test_ladder_unary() public view {
        int256[7] memory xs = _unary();
        _run1("abs", xs, true);
        _run1("neg", xs, true);
        _run1("sign", xs, true);
        _run1("floor", xs, true);
        _run1("ceil", xs, true);
        _run1("frac", xs, true);
        _run1("round", xs, false);
        _run1("inv", xs, true);
        _run1("toFixed18", xs, false);
        _run1("fromFixed18", [int256(1), 5e17, 1e18, 3141592653589793238, 1000e18, int256(1) << 100, -3141592653589793238], false);
    }

    function test_ladder_exp() public view {
        _run1("exp", [-80 * ONE, -ONE, ONE / 2, ONE, PI, 20 * ONE, 80 * ONE], true);
        _run1("exp2", [-100 * ONE, -ONE, ONE / 2, ONE, PI, 60 * ONE, 126 * ONE], true);
        _run1("exp10", [-30 * ONE, -ONE, ONE / 2, ONE, PI, 20 * ONE, 37 * ONE], false);
    }

    function test_ladder_log() public view {
        int256[7] memory xs = _posUnary();
        _run1("ln", xs, true);
        _run1("log2", xs, true);
        _run1("log10", xs, true);
        _run1("log2Up", xs, false);
    }

    function test_ladder_roots() public view {
        int256[7] memory xs = _posUnary();
        _run1("sqrt", xs, true);
        _run1("cbrt", [ONE >> 60, ONE / 2, ONE, PI, 1000 * ONE, ONE << 60, -PI], true);
        (int256[6] memory a, int256[6] memory b) = _binary();
        _run2("hypot", a, b, false);
        _run2("gavg", [ONE, PI, 2 * ONE, 1000 * ONE, ONE << 60, ONE >> 60], [ONE, E_, 8 * ONE, ONE / 3, ONE << 40, ONE >> 40], true);
    }

    function test_ladder_pow() public view {
        _run2("pow", [ONE + ONE / 100, PI, 2 * ONE, 10 * ONE, ONE / 2, 3 * ONE],
                     [365 * ONE, E_, 10 * ONE, 2 * ONE + ONE / 2, -3 * ONE, 2 * ONE], true);
    }

    function test_ladder_special() public view {
        _run1("lambertW0", [-ONE / 4, ONE / 100, ONE / 2, ONE + ONE / 2, 10 * ONE, 1000 * ONE, ONE << 100], true);
        _run1("lambertWm1", [-int256(0x5e2d58d8b3bcdf1abadec7829054f90d) + 1, -ONE / 3, -ONE / 4, -ONE / 10, -ONE / 1000, -(ONE >> 40), -1], true);
        _run1("factorial", [int256(0), ONE, 5 * ONE, 10 * ONE, 20 * ONE, 30 * ONE, 33 * ONE], false);
        _run1("pi", [ONE, 2 * ONE, 3 * ONE, 4 * ONE, 5 * ONE, 6 * ONE, 7 * ONE], false);
    }

    // v4 ops. The per-second rate is 5% APR / 31,536,000; the Black-Scholes
    // tails are where an 18-decimal N(d) is zero.
    int256 constant R_SEC = 539514153540300709448526457749; // floor(0.05 / 31536000 * 2^128)

    function test_ladder_v4_powers() public view {
        _run2("powu", [2 * ONE, ONE + ONE / 100, ONE + R_SEC, ONE / 2, PI, 3 * ONE],
                      [10 * ONE, 365 * ONE, 31536000 * ONE, 100 * ONE, 7 * ONE, -5 * ONE], false);
        _run2("compound", [ONE / 10, ONE / 3650, R_SEC, ONE / 2, -ONE / 100, ONE / 100],
                          [10 * ONE, 365 * ONE, 31536000 * ONE, 100 * ONE, 365 * ONE, 315360000 * ONE], false);
    }

    function test_ladder_v4_near_one() public view {
        int256[7] memory xs = [R_SEC, ONE >> 60, -(ONE >> 40), ONE / 1000, -ONE / 100, ONE / 2, 5 * ONE];
        _run1("log1p", xs, false);
        _run1("expm1", xs, false);
        _run1("sinh", xs, false);
        _run1("cosh", xs, false);
        _run1("tanh", xs, false);
        _run1("atanh", [R_SEC, ONE >> 60, -(ONE >> 40), ONE / 1000, -ONE / 100, ONE / 2, ONE - 1], false);
    }

    // v5: the directed edge ops, on the arithmetic ladder
    function test_ladder_v5_directed() public view {
        (int256[6] memory a, int256[6] memory b) = _binary();
        _run2("mulDown", a, b, true);
        _run2("mulUp", a, b, true);
        _run2("divDown", a, b, true);
        _run2("divUp", a, b, true);
        int256[7] memory xs = _unary();
        _run1("toFixed18Down", xs, false);
        _run1("toFixed18Up", xs, false);
    }

    function test_ladder_v4_erf() public view {
        int256[7] memory xs = [ONE / 100, ONE / 2, ONE, 2 * ONE, 4 * ONE, 6 * ONE, 9 * ONE];
        _run1("erf", xs, false);
        _run1("erfc", xs, false);
        _run1("normCdf", [-13 * ONE, -9 * ONE, -5 * ONE, -ONE, 0, ONE, 5 * ONE], false);
    }
}

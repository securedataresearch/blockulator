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
/// op), with a seventh field |typical on the typical-input rows.
/// scripts/fp127/gas_to_json.py turns the lines into gas.json. The internal
/// forms are timed inside their entry point, net of dispatch (see _timed).
contract GasLadder is FP127Harness {
    int256 constant PI = 1069028584064966747859680373161870783300; // floor(pi * 2^128)
    int256 constant E_ = 924983374546220337150911035843336795079;
    int256 constant NA = type(int256).min;

    /// Each test runs as its own transaction, so the accounts setUp touched
    /// are cold again: touch every called object first, so no row pays the
    /// 2,500-gas cold-account surcharge.
    function _warm() internal view {
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

    /// One GAS| line; set is "" for the ladder rows and "typical" for the
    /// typical-input rows, which carry it as a seventh field.
    function _emit(string memory op, uint256 idx, string memory input, string memory form, int256 g, string memory set) internal pure {
        string memory line = string.concat("GAS|", op, "|", vm.toString(idx), "|", input, "|", form, "|", g == NA ? "NA" : vm.toString(uint256(g)));
        console.log(bytes(set).length == 0 ? line : string.concat(line, "|", set));
    }

    function _fp127Rows(string memory op, uint256 idx, string memory label, bytes memory newCall, bytes memory huffCall, int256 libGas, string memory set) internal view {
        _emit(op, idx, label, "huff", _ext(address(huff), huffCall), set);
        _emit(op, idx, label, "yul", _ext(address(obj), newCall), set);
        _emit(op, idx, label, "caller", _ext(address(caller), newCall), set);
        _emit(op, idx, label, "lib", libGas, set);
    }

    /// The internal forms (FP127Lib and the competitors) are timed inside an
    /// external entry point of this contract, so a revert is caught and
    /// recorded as NA. The entry point finds the op by name, then reads
    /// gasleft() on either side of the one library call, so neither the
    /// dispatch nor the ABI decoding is in the window; the same window around
    /// a plain assignment (op "id") is subtracted. What is left is the
    /// internal call as a caller's code pays it, the same for every op
    /// whatever its place in the entry point's list.
    function _timed(bytes memory call, bytes memory idCall) internal view returns (int256) {
        (bool ok, bytes memory out) = address(this).staticcall(call);
        if (!ok) return NA;
        (bool okId, bytes memory outId) = address(this).staticcall(idCall);
        require(okId, "id");
        return int256(abi.decode(out, (uint256))) - int256(abi.decode(outId, (uint256)));
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

    function cAbdk1(string calldata op, int128 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int128 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = ABDKMath64x64.exp(x); g = gasleft(); }
        if (h == keccak256("exp2")) { g0 = gasleft(); r = ABDKMath64x64.exp_2(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = ABDKMath64x64.ln(x); g = gasleft(); }
        if (h == keccak256("log2")) { g0 = gasleft(); r = ABDKMath64x64.log_2(x); g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = ABDKMath64x64.sqrt(x); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = ABDKMath64x64.inv(x); g = gasleft(); }
        if (h == keccak256("abs")) { g0 = gasleft(); r = ABDKMath64x64.abs(x); g = gasleft(); }
        if (h == keccak256("neg")) { g0 = gasleft(); r = ABDKMath64x64.neg(x); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cAbdk2(string calldata op, int128 a, int128 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int128 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = ABDKMath64x64.mul(a, b); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = ABDKMath64x64.div(a, b); g = gasleft(); }
        if (h == keccak256("add")) { g0 = gasleft(); r = ABDKMath64x64.add(a, b); g = gasleft(); }
        if (h == keccak256("sub")) { g0 = gasleft(); r = ABDKMath64x64.sub(a, b); g = gasleft(); }
        if (h == keccak256("avg")) { g0 = gasleft(); r = ABDKMath64x64.avg(a, b); g = gasleft(); }
        if (h == keccak256("gavg")) { g0 = gasleft(); r = ABDKMath64x64.gavg(a, b); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = ABDKMath64x64.pow(a, uint256(int256(b >> 64))); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cSolady1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = FixedPointMathLib.expWad(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = FixedPointMathLib.lnWad(x); g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = int256(FixedPointMathLib.sqrtWad(uint256(x))); g = gasleft(); }
        if (h == keccak256("cbrt")) { g0 = gasleft(); r = int256(FixedPointMathLib.cbrtWad(uint256(x))); g = gasleft(); }
        if (h == keccak256("lambertW0")) { g0 = gasleft(); r = FixedPointMathLib.lambertW0Wad(x); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = FixedPointMathLib.sDivWad(1e18, x); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cSolady2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = FixedPointMathLib.sMulWad(a, b); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = FixedPointMathLib.sDivWad(a, b); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = FixedPointMathLib.powWad(a, b); g = gasleft(); }
        // Solady's directed WAD ops are unsigned
        if (h == keccak256("mulDown") && a >= 0 && b >= 0) { g0 = gasleft(); r = int256(FixedPointMathLib.mulWad(uint256(a), uint256(b))); g = gasleft(); }
        if (h == keccak256("mulUp") && a >= 0 && b >= 0) { g0 = gasleft(); r = int256(FixedPointMathLib.mulWadUp(uint256(a), uint256(b))); g = gasleft(); }
        if (h == keccak256("divDown") && a >= 0 && b > 0) { g0 = gasleft(); r = int256(FixedPointMathLib.divWad(uint256(a), uint256(b))); g = gasleft(); }
        if (h == keccak256("divUp") && a >= 0 && b > 0) { g0 = gasleft(); r = int256(FixedPointMathLib.divWadUp(uint256(a), uint256(b))); g = gasleft(); }
        if (h == keccak256("add")) { g0 = gasleft(); r = a + b; g = gasleft(); }
        if (h == keccak256("sub")) { g0 = gasleft(); r = a - b; g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cPrb1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        SD59x18 v = sd(x);
        if (h == keccak256("exp")) { g0 = gasleft(); r = PRB.exp(v).unwrap(); g = gasleft(); }
        if (h == keccak256("exp2")) { g0 = gasleft(); r = PRB.exp2(v).unwrap(); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = PRB.ln(v).unwrap(); g = gasleft(); }
        if (h == keccak256("log2")) { g0 = gasleft(); r = PRB.log2(v).unwrap(); g = gasleft(); }
        if (h == keccak256("log10")) { g0 = gasleft(); r = PRB.log10(v).unwrap(); g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = PRB.sqrt(v).unwrap(); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = PRB.inv(v).unwrap(); g = gasleft(); }
        if (h == keccak256("abs")) { g0 = gasleft(); r = PRB.abs(v).unwrap(); g = gasleft(); }
        if (h == keccak256("floor")) { g0 = gasleft(); r = PRB.floor(v).unwrap(); g = gasleft(); }
        if (h == keccak256("ceil")) { g0 = gasleft(); r = PRB.ceil(v).unwrap(); g = gasleft(); }
        if (h == keccak256("frac")) { g0 = gasleft(); r = PRB.frac(v).unwrap(); g = gasleft(); }
        if (h == keccak256("sign")) { g0 = gasleft(); r = PRB.sign(v).unwrap(); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cPrb2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = PRB.mul(sd(a), sd(b)).unwrap(); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = PRB.div(sd(a), sd(b)).unwrap(); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = PRB.pow(sd(a), sd(b)).unwrap(); g = gasleft(); }
        if (h == keccak256("avg")) { g0 = gasleft(); r = PRB.avg(sd(a), sd(b)).unwrap(); g = gasleft(); }
        if (h == keccak256("gavg")) { g0 = gasleft(); r = PRB.gm(sd(a), sd(b)).unwrap(); g = gasleft(); }
        if (h == keccak256("add")) { g0 = gasleft(); r = a + b; g = gasleft(); }
        if (h == keccak256("sub")) { g0 = gasleft(); r = a - b; g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cQuad1(string calldata op, bytes16 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        bytes16 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = Q.exp(x); g = gasleft(); }
        if (h == keccak256("exp2")) { g0 = gasleft(); r = Q.pow_2(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = Q.ln(x); g = gasleft(); }
        if (h == keccak256("log2")) { g0 = gasleft(); r = Q.log_2(x); g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = Q.sqrt(x); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = Q.div(Q.fromUInt(1), x); g = gasleft(); }
        if (h == keccak256("abs")) { g0 = gasleft(); r = Q.abs(x); g = gasleft(); }
        if (h == keccak256("neg")) { g0 = gasleft(); r = Q.neg(x); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cQuad2(string calldata op, bytes16 a, bytes16 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        bytes16 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = Q.mul(a, b); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = Q.div(a, b); g = gasleft(); }
        if (h == keccak256("add")) { g0 = gasleft(); r = Q.add(a, b); g = gasleft(); }
        if (h == keccak256("sub")) { g0 = gasleft(); r = Q.sub(a, b); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = Q.exp(Q.mul(b, Q.ln(a))); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cBal1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = LogExpMath.exp(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = LogExpMath.ln(x); g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = int256(LogExpMath.pow(uint256(x), 5e17)); g = gasleft(); }
        if (h == keccak256("cbrt")) { g0 = gasleft(); r = int256(LogExpMath.pow(uint256(x), 333333333333333333)); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cBal2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = int256(LogExpMath.pow(uint256(a), uint256(b))); g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = a * b / 1e18; g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = a * 1e18 / b; g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function _comp1(string memory op, uint256 idx, string memory label, int256 x, string memory set) internal view {
        (int128 xa, bool okA) = _abdk(x);
        _emit(op, idx, label, "abdk", okA ? _timed(abi.encodeCall(this.cAbdk1, (op, xa)), abi.encodeCall(this.cAbdk1, ("id", xa))) : NA, set);
        _emit(op, idx, label, "solady", _timed(abi.encodeCall(this.cSolady1, (op, _wad(x))), abi.encodeCall(this.cSolady1, ("id", _wad(x)))), set);
        _emit(op, idx, label, "prb", _timed(abi.encodeCall(this.cPrb1, (op, _wad(x))), abi.encodeCall(this.cPrb1, ("id", _wad(x)))), set);
        _emit(op, idx, label, "quad", _timed(abi.encodeCall(this.cQuad1, (op, _quad(x))), abi.encodeCall(this.cQuad1, ("id", _quad(x)))), set);
        _emit(op, idx, label, "balancer", _timed(abi.encodeCall(this.cBal1, (op, _wad(x))), abi.encodeCall(this.cBal1, ("id", _wad(x)))), set);
    }

    function _abdkGas2(string memory op, int256 a, int256 b) internal view returns (int256) {
        (int128 aa, bool okA) = _abdk(a);
        (int128 ba, bool okB) = _abdk(b);
        if (!(okA && okB)) return NA;
        return _timed(abi.encodeCall(this.cAbdk2, (op, aa, ba)), abi.encodeCall(this.cAbdk2, ("id", aa, ba)));
    }

    function _comp2(string memory op, uint256 idx, string memory label, int256 a, int256 b, string memory set) internal view {
        _emit(op, idx, label, "abdk", _abdkGas2(op, a, b), set);
        _emit(op, idx, label, "solady", _timed(abi.encodeCall(this.cSolady2, (op, _wad(a), _wad(b))), abi.encodeCall(this.cSolady2, ("id", _wad(a), _wad(b)))), set);
        _emit(op, idx, label, "prb", _timed(abi.encodeCall(this.cPrb2, (op, _wad(a), _wad(b))), abi.encodeCall(this.cPrb2, ("id", _wad(a), _wad(b)))), set);
        _emit(op, idx, label, "quad", _timed(abi.encodeCall(this.cQuad2, (op, _quad(a), _quad(b))), abi.encodeCall(this.cQuad2, ("id", _quad(a), _quad(b)))), set);
        _emit(op, idx, label, "balancer", _timed(abi.encodeCall(this.cBal2, (op, _wad(a), _wad(b))), abi.encodeCall(this.cBal2, ("id", _wad(a), _wad(b)))), set);
    }

    // ---- FP127Lib internal timing per op ------------------------------

    function _libGas1(string memory op, int256 x) internal view returns (int256) {
        return _timed(abi.encodeCall(this.cLib1, (op, x)), abi.encodeCall(this.cLib1, ("id", x)));
    }

    function _libGas2(string memory op, int256 a, int256 b) internal view returns (int256) {
        return _timed(abi.encodeCall(this.cLib2, (op, a, b)), abi.encodeCall(this.cLib2, ("id", a, b)));
    }

    function cLib1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = FP127Lib.exp(x); g = gasleft(); }
        if (h == keccak256("exp2")) { g0 = gasleft(); r = FP127Lib.exp2(x); g = gasleft(); }
        if (h == keccak256("exp10")) { g0 = gasleft(); r = FP127Lib.exp10(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = FP127Lib.ln(x); g = gasleft(); }
        if (h == keccak256("log2")) { g0 = gasleft(); r = FP127Lib.log2(x); g = gasleft(); }
        if (h == keccak256("log10")) { g0 = gasleft(); r = FP127Lib.log10(x); g = gasleft(); }
        if (h == keccak256("log2Up")) { g0 = gasleft(); r = FP127Lib.log2Up(x); g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = FP127Lib.sqrt(x); g = gasleft(); }
        if (h == keccak256("cbrt")) { g0 = gasleft(); r = FP127Lib.cbrt(x); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = FP127Lib.inv(x); g = gasleft(); }
        if (h == keccak256("abs")) { g0 = gasleft(); r = FP127Lib.abs(x); g = gasleft(); }
        if (h == keccak256("neg")) { g0 = gasleft(); r = FP127Lib.neg(x); g = gasleft(); }
        if (h == keccak256("sign")) { g0 = gasleft(); r = FP127Lib.sign(x); g = gasleft(); }
        if (h == keccak256("floor")) { g0 = gasleft(); r = FP127Lib.floor(x); g = gasleft(); }
        if (h == keccak256("ceil")) { g0 = gasleft(); r = FP127Lib.ceil(x); g = gasleft(); }
        if (h == keccak256("frac")) { g0 = gasleft(); r = FP127Lib.frac(x); g = gasleft(); }
        if (h == keccak256("round")) { g0 = gasleft(); r = FP127Lib.round(x); g = gasleft(); }
        if (h == keccak256("factorial")) { g0 = gasleft(); r = FP127Lib.factorial(x); g = gasleft(); }
        if (h == keccak256("lambertW0")) { g0 = gasleft(); r = FP127Lib.lambertW0(x); g = gasleft(); }
        if (h == keccak256("lambertWm1")) { g0 = gasleft(); r = FP127Lib.lambertWm1(x); g = gasleft(); }
        if (h == keccak256("pi")) { g0 = gasleft(); r = FP127Lib.pi(x); g = gasleft(); }
        if (h == keccak256("log1p")) { g0 = gasleft(); r = FP127Lib.log1p(x); g = gasleft(); }
        if (h == keccak256("expm1")) { g0 = gasleft(); r = FP127Lib.expm1(x); g = gasleft(); }
        if (h == keccak256("sinh")) { g0 = gasleft(); r = FP127Lib.sinh(x); g = gasleft(); }
        if (h == keccak256("cosh")) { g0 = gasleft(); r = FP127Lib.cosh(x); g = gasleft(); }
        if (h == keccak256("tanh")) { g0 = gasleft(); r = FP127Lib.tanh(x); g = gasleft(); }
        if (h == keccak256("atanh")) { g0 = gasleft(); r = FP127Lib.atanh(x); g = gasleft(); }
        if (h == keccak256("erf")) { g0 = gasleft(); r = FP127Lib.erf(x); g = gasleft(); }
        if (h == keccak256("erfc")) { g0 = gasleft(); r = FP127Lib.erfc(x); g = gasleft(); }
        if (h == keccak256("normCdf")) { g0 = gasleft(); r = FP127Lib.normCdf(x); g = gasleft(); }
        if (h == keccak256("fromFixed18")) { g0 = gasleft(); r = FP127Lib.fromFixed18(x); g = gasleft(); }
        if (h == keccak256("toFixed18")) { g0 = gasleft(); r = FP127Lib.toFixed18(x); g = gasleft(); }
        if (h == keccak256("toFixed18Down")) { g0 = gasleft(); r = FP127Lib.toFixed18Down(x); g = gasleft(); }
        if (h == keccak256("toFixed18Up")) { g0 = gasleft(); r = FP127Lib.toFixed18Up(x); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cLib2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("add")) { g0 = gasleft(); r = FP127Lib.add(a, b); g = gasleft(); }
        if (h == keccak256("sub")) { g0 = gasleft(); r = FP127Lib.sub(a, b); g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = FP127Lib.mul(a, b); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = FP127Lib.div(a, b); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = FP127Lib.pow(a, b); g = gasleft(); }
        if (h == keccak256("powu")) { g0 = gasleft(); r = FP127Lib.powu(a, b); g = gasleft(); }
        if (h == keccak256("compound")) { g0 = gasleft(); r = FP127Lib.compound(a, b); g = gasleft(); }
        if (h == keccak256("min")) { g0 = gasleft(); r = FP127Lib.min(a, b); g = gasleft(); }
        if (h == keccak256("max")) { g0 = gasleft(); r = FP127Lib.max(a, b); g = gasleft(); }
        if (h == keccak256("avg")) { g0 = gasleft(); r = FP127Lib.avg(a, b); g = gasleft(); }
        if (h == keccak256("gavg")) { g0 = gasleft(); r = FP127Lib.gavg(a, b); g = gasleft(); }
        if (h == keccak256("hypot")) { g0 = gasleft(); r = FP127Lib.hypot(a, b); g = gasleft(); }
        if (h == keccak256("dist")) { g0 = gasleft(); r = FP127Lib.dist(a, b); g = gasleft(); }
        if (h == keccak256("zeroFloorSub")) { g0 = gasleft(); r = FP127Lib.zeroFloorSub(a, b); g = gasleft(); }
        if (h == keccak256("gcd")) { g0 = gasleft(); r = FP127Lib.gcd(a, b); g = gasleft(); }
        if (h == keccak256("mulDown")) { g0 = gasleft(); r = FP127Lib.mulDown(a, b); g = gasleft(); }
        if (h == keccak256("mulUp")) { g0 = gasleft(); r = FP127Lib.mulUp(a, b); g = gasleft(); }
        if (h == keccak256("divDown")) { g0 = gasleft(); r = FP127Lib.divDown(a, b); g = gasleft(); }
        if (h == keccak256("divUp")) { g0 = gasleft(); r = FP127Lib.divUp(a, b); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    // ---- drivers --------------------------------------------------------

    function _row1(string memory op, uint256 i, int256 x, bool competitors, string memory set) internal view {
        string memory label = vm.toString(x);
        bytes memory newCall = abi.encodeWithSignature(string.concat(op, "(int256)"), x);
        // the legacy conversions have no Raw suffix
        bool conv = keccak256(bytes(op)) == keccak256("fromFixed18") || keccak256(bytes(op)) == keccak256("toFixed18");
        bytes memory huffCall = abi.encodeWithSignature(string.concat(op, conv ? "(uint256)" : "Raw(uint256)"), uint256(x));
        _fp127Rows(op, i, label, newCall, huffCall, _libGas1(op, x), set);
        if (competitors) _comp1(op, i, label, x, set);
    }

    function _row2(string memory op, uint256 i, int256 a, int256 b, bool competitors, string memory set) internal view {
        string memory label = string.concat(vm.toString(a), ",", vm.toString(b));
        bytes memory newCall = abi.encodeWithSignature(string.concat(op, "(int256,int256)"), a, b);
        bytes memory huffCall = abi.encodeWithSignature(string.concat(op, "Raw(uint256,uint256)"), uint256(a), uint256(b));
        _fp127Rows(op, i, label, newCall, huffCall, _libGas2(op, a, b), set);
        if (competitors) _comp2(op, i, label, a, b, set);
    }

    function _run1(string memory op, int256[7] memory xs, bool competitors) internal view {
        for (uint256 i; i < xs.length; i++) _row1(op, i, xs[i], competitors, "");
    }

    function _run2(string memory op, int256[6] memory a, int256[6] memory b, bool competitors) internal view {
        for (uint256 i; i < a.length; i++) _row2(op, i, a[i], b[i], competitors, "");
    }

    // ---- typical inputs -------------------------------------------------
    // The ladders above sit mostly on integers, powers of two and one, where
    // several ops take a shortcut. The typical rows draw TYPICAL inputs per
    // op from keccak256("typical", op, i): a magnitude in [2^e, 2^(e+1)) for
    // e uniform in [elo, ehi], 128 random mantissa bits (never an integer
    // or a power of two at these sizes), the sign by sgn (1 positive, -1
    // negative, 0 either).

    uint256 constant TYPICAL = 8;

    function _rnd(string memory op, uint256 i) internal pure returns (uint256) {
        return uint256(keccak256(abi.encode("typical", op, i)));
    }

    function _typ(string memory op, uint256 i, int256 elo, int256 ehi, int256 sgn) internal pure returns (int256 x) {
        uint256 h = _rnd(op, i);
        int256 e = elo + int256(h % uint256(ehi - elo + 1));
        uint256 m = (h >> 128) | (uint256(1) << 128);
        x = int256(e >= 0 ? m << uint256(e) : m >> uint256(-e));
        if (sgn < 0 || (sgn == 0 && (h >> 64) & 1 == 1)) x = -x;
    }

    function _typ1(string memory op, int256 elo, int256 ehi, int256 sgn, bool competitors) internal view {
        for (uint256 i; i < TYPICAL; i++) _row1(op, i, _typ(op, i, elo, ehi, sgn), competitors, "typical");
    }

    /// A small rate r and an integer n with r n < 1, so (1 + r)^n stays near
    /// one: n has up to k bits, r is below 2^-k.
    function _typRate(string memory op, uint256 i) internal pure returns (int256 r, int256 n) {
        uint256 h = _rnd(op, i + 1000);
        uint256 k = 1 + h % 20;
        n = int256(2 + (h >> 64) % ((uint256(1) << k) - 1));
        r = _typ(op, i, -40, -int256(k) - 1, 1);
    }

    function test_ladder_typical() public view {
        _warm();
        _typ1("exp", -4, 5, 0, true);
        _typ1("exp2", -4, 5, 0, true);
        _typ1("exp10", -4, 4, 0, false);
        _typ1("expm1", -8, 5, 0, false);
        _typ1("ln", -60, 60, 1, true);
        _typ1("log2", -60, 60, 1, true);
        _typ1("log10", -60, 60, 1, true);
        _typ1("log1p", -20, 4, 1, false);
        _typ1("sqrt", -60, 100, 1, true);
        _typ1("cbrt", -60, 100, 0, true);
        _typ1("sinh", -8, 5, 0, false);
        _typ1("cosh", -8, 5, 0, false);
        _typ1("tanh", -8, 5, 0, false);
        _typ1("atanh", -12, -2, 0, false);
        _typ1("erf", -4, 2, 0, false);
        _typ1("erfc", -4, 2, 0, false);
        _typ1("normCdf", -4, 3, 0, false);
        _typ1("lambertW0", -10, 40, 1, true);
        _typ1("lambertWm1", -30, -3, -1, true);
        for (uint256 i; i < TYPICAL; i++) {
            _row2("pow", i, _typ("pow", i, -4, 4, 1), _typ("pow", i + 100, -4, 3, 0), true, "typical");
            (int256 r, int256 n) = _typRate("powu", i);
            _row2("powu", i, ONE + r, n << 128, false, "typical");
            (r, n) = _typRate("compound", i);
            _row2("compound", i, r, n << 128, false, "typical");
        }
    }

    function test_ladder_arith() public view {
        _warm();
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
        _warm();
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
        _warm();
        _run1("exp", [-80 * ONE, -ONE, ONE / 2, ONE, PI, 20 * ONE, 80 * ONE], true);
        _run1("exp2", [-100 * ONE, -ONE, ONE / 2, ONE, PI, 60 * ONE, 126 * ONE], true);
        _run1("exp10", [-30 * ONE, -ONE, ONE / 2, ONE, PI, 20 * ONE, 37 * ONE], false);
    }

    function test_ladder_log() public view {
        _warm();
        int256[7] memory xs = _posUnary();
        _run1("ln", xs, true);
        _run1("log2", xs, true);
        _run1("log10", xs, true);
        _run1("log2Up", xs, false);
    }

    function test_ladder_roots() public view {
        _warm();
        int256[7] memory xs = _posUnary();
        _run1("sqrt", xs, true);
        _run1("cbrt", [ONE >> 60, ONE / 2, ONE, PI, 1000 * ONE, ONE << 60, -PI], true);
        (int256[6] memory a, int256[6] memory b) = _binary();
        _run2("hypot", a, b, false);
        _run2("gavg", [ONE, PI, 2 * ONE, 1000 * ONE, ONE << 60, ONE >> 60], [ONE, E_, 8 * ONE, ONE / 3, ONE << 40, ONE >> 40], true);
    }

    function test_ladder_pow() public view {
        _warm();
        _run2("pow", [ONE + ONE / 100, PI, 2 * ONE, 10 * ONE, ONE / 2, 3 * ONE],
                     [365 * ONE, E_, 10 * ONE, 2 * ONE + ONE / 2, -3 * ONE, 2 * ONE], true);
    }

    function test_ladder_special() public view {
        _warm();
        _run1("lambertW0", [-ONE / 4, ONE / 100, ONE / 2, ONE + ONE / 2, 10 * ONE, 1000 * ONE, ONE << 100], true);
        _run1("lambertWm1", [-int256(0x5e2d58d8b3bcdf1abadec7829054f90d) + 1, -ONE / 3, -ONE / 4, -ONE / 10, -ONE / 1000, -(ONE >> 40), -1], true);
        _run1("factorial", [int256(0), ONE, 5 * ONE, 10 * ONE, 20 * ONE, 30 * ONE, 33 * ONE], false);
        _run1("pi", [ONE, 2 * ONE, 3 * ONE, 4 * ONE, 5 * ONE, 6 * ONE, 7 * ONE], false);
    }

    // v4 ops. The per-second rate is 5% APR / 31,536,000; the Black-Scholes
    // tails are where an 18-decimal N(d) is zero.
    int256 constant R_SEC = 539514153540300709448526457749; // floor(0.05 / 31536000 * 2^128)

    function test_ladder_v4_powers() public view {
        _warm();
        _run2("powu", [2 * ONE, ONE + ONE / 100, ONE + R_SEC, ONE / 2, PI, 3 * ONE],
                      [10 * ONE, 365 * ONE, 31536000 * ONE, 100 * ONE, 7 * ONE, -5 * ONE], false);
        _run2("compound", [ONE / 10, ONE / 3650, R_SEC, ONE / 2, -ONE / 100, ONE / 100],
                          [10 * ONE, 365 * ONE, 31536000 * ONE, 100 * ONE, 365 * ONE, 315360000 * ONE], false);
    }

    function test_ladder_v4_near_one() public view {
        _warm();
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
        _warm();
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
        _warm();
        int256[7] memory xs = [ONE / 100, ONE / 2, ONE, 2 * ONE, 4 * ONE, 6 * ONE, 9 * ONE];
        _run1("erf", xs, false);
        _run1("erfc", xs, false);
        _run1("normCdf", [-13 * ONE, -9 * ONE, -5 * ONE, -ONE, 0, ONE, 5 * ONE], false);
    }
}

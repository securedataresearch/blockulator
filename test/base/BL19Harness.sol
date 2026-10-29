// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {IBL19} from "../../contracts/src/bl19/IBL19.sol";
import {IBL19E} from "../../contracts/src/bl19/IBL19E.sol";
import {IBL19H} from "../../contracts/src/bl19/IBL19H.sol";
import {IBL19N} from "../../contracts/src/bl19/IBL19N.sol";
import {IBL19S} from "../../contracts/src/bl19/IBL19S.sol";
import {BL19Lib} from "../../contracts/src/bl19/BL19Lib.sol";

/// @notice External wrapper around the inline library so every call can be
///         made with try/catch and compared with the object on the same calldata.
contract LibUser19 {
    function add(int256 a, int256 b) external pure returns (int256) { return BL19Lib.add(a, b); }
    function sub(int256 a, int256 b) external pure returns (int256) { return BL19Lib.sub(a, b); }
    function mul(int256 a, int256 b) external pure returns (int256) { return BL19Lib.mul(a, b); }
    function div(int256 a, int256 b) external pure returns (int256) { return BL19Lib.div(a, b); }
    function sqrt(int256 x) external pure returns (int256) { return BL19Lib.sqrt(x); }
    function exp(int256 x) external pure returns (int256) { return BL19Lib.exp(x); }
    function ln(int256 x) external pure returns (int256) { return BL19Lib.ln(x); }
    function pow(int256 x, int256 y) external pure returns (int256) { return BL19Lib.pow(x, y); }
    function log1p(int256 x) external pure returns (int256) { return BL19Lib.log1p(x); }
    function expm1(int256 x) external pure returns (int256) { return BL19Lib.expm1(x); }
    function erf(int256 x) external pure returns (int256) { return BL19Lib.erf(x); }
    function erfc(int256 x) external pure returns (int256) { return BL19Lib.erfc(x); }
    function normCdf(int256 x) external pure returns (int256) { return BL19Lib.normCdf(x); }
    function lambertW0(int256 x) external pure returns (int256) { return BL19Lib.lambertW0(x); }
    function lambertWm1(int256 x) external pure returns (int256) { return BL19Lib.lambertWm1(x); }
    function powu(int256 x, int256 n) external pure returns (int256) { return BL19Lib.powu(x, n); }
    function compound(int256 r, int256 n) external pure returns (int256) { return BL19Lib.compound(r, n); }
    function neg(int256 x) external pure returns (int256) { return BL19Lib.neg(x); }
    function abs(int256 x) external pure returns (int256) { return BL19Lib.abs(x); }
    function sign(int256 x) external pure returns (int256) { return BL19Lib.sign(x); }
    function cmp(int256 a, int256 b) external pure returns (int256) { return BL19Lib.cmp(a, b); }
    function lt(int256 a, int256 b) external pure returns (int256) { return BL19Lib.lt(a, b); }
    function eq(int256 a, int256 b) external pure returns (int256) { return BL19Lib.eq(a, b); }
    function fromUint(uint256 x) external pure returns (int256) { return BL19Lib.fromUint(x); }
    function fromBL127(int256 x) external pure returns (int256) { return BL19Lib.fromBL127(x); }
    function toBL127(int256 x) external pure returns (int256) { return BL19Lib.toBL127(x); }
    function fromFixed18(int256 x) external pure returns (int256) { return BL19Lib.fromFixed18(x); }
    function toFixed18(int256 x) external pure returns (int256) { return BL19Lib.toFixed18(x); }
    function mulDown(int256 a, int256 b) external pure returns (int256) { return BL19Lib.mulDown(a, b); }
    function mulUp(int256 a, int256 b) external pure returns (int256) { return BL19Lib.mulUp(a, b); }
    function divDown(int256 a, int256 b) external pure returns (int256) { return BL19Lib.divDown(a, b); }
    function divUp(int256 a, int256 b) external pure returns (int256) { return BL19Lib.divUp(a, b); }
    function toUintDown(int256 x) external pure returns (uint256) { return BL19Lib.toUintDown(x); }
    function toUintUp(int256 x) external pure returns (uint256) { return BL19Lib.toUintUp(x); }
    function toIntDown(int256 x) external pure returns (int256) { return BL19Lib.toIntDown(x); }
    function toIntUp(int256 x) external pure returns (int256) { return BL19Lib.toIntUp(x); }
    function floor(int256 x) external pure returns (int256) { return BL19Lib.floor(x); }
    function ceil(int256 x) external pure returns (int256) { return BL19Lib.ceil(x); }
    function fromUintDown(uint256 x) external pure returns (int256) { return BL19Lib.fromUintDown(x); }
    function fromUintUp(uint256 x) external pure returns (int256) { return BL19Lib.fromUintUp(x); }
    function toFixed18Down(int256 x) external pure returns (int256) { return BL19Lib.toFixed18Down(x); }
    function toFixed18Up(int256 x) external pure returns (int256) { return BL19Lib.toFixed18Up(x); }
    // #79
    function exp2(int256 x) external pure returns (int256) { return BL19Lib.exp2(x); }
    function exp10(int256 x) external pure returns (int256) { return BL19Lib.exp10(x); }
    function log2(int256 x) external pure returns (int256) { return BL19Lib.log2(x); }
    function log10(int256 x) external pure returns (int256) { return BL19Lib.log10(x); }
    function log2Up(int256 x) external pure returns (int256) { return BL19Lib.log2Up(x); }
    function cbrt(int256 x) external pure returns (int256) { return BL19Lib.cbrt(x); }
    function sinh(int256 x) external pure returns (int256) { return BL19Lib.sinh(x); }
    function cosh(int256 x) external pure returns (int256) { return BL19Lib.cosh(x); }
    function tanh(int256 x) external pure returns (int256) { return BL19Lib.tanh(x); }
    function atanh(int256 x) external pure returns (int256) { return BL19Lib.atanh(x); }
    function min(int256 a, int256 b) external pure returns (int256) { return BL19Lib.min(a, b); }
    function max(int256 a, int256 b) external pure returns (int256) { return BL19Lib.max(a, b); }
    function clamp(int256 x, int256 lo, int256 hi) external pure returns (int256) { return BL19Lib.clamp(x, lo, hi); }
    function avg(int256 a, int256 b) external pure returns (int256) { return BL19Lib.avg(a, b); }
    function dist(int256 a, int256 b) external pure returns (int256) { return BL19Lib.dist(a, b); }
    function zeroFloorSub(int256 a, int256 b) external pure returns (int256) { return BL19Lib.zeroFloorSub(a, b); }
    function inv(int256 x) external pure returns (int256) { return BL19Lib.inv(x); }
    function lerp(int256 a, int256 b, int256 t) external pure returns (int256) { return BL19Lib.lerp(a, b, t); }
    function frac(int256 x) external pure returns (int256) { return BL19Lib.frac(x); }
    function round(int256 x) external pure returns (int256) { return BL19Lib.round(x); }
    function factorial(int256 n) external pure returns (int256) { return BL19Lib.factorial(n); }
    function gavg(int256 a, int256 b) external pure returns (int256) { return BL19Lib.gavg(a, b); }
    function hypot(int256 a, int256 b) external pure returns (int256) { return BL19Lib.hypot(a, b); }
}

abstract contract BL19Harness is Test {
    /// the number: arithmetic, roots, comparison, rounding, conversions
    IBL19 internal obj;
    /// the elementary functions on the exp/log kernel
    IBL19E internal objE;
    /// the hyperbolic functions
    IBL19H internal objH;
    /// the normal distribution: erf, erfc, normCdf
    IBL19N internal objN;
    /// the special functions: Lambert W
    IBL19S internal objS;
    LibUser19 internal lib;

    uint256 internal constant BIAS = 0x3ffff;
    int256 internal constant ONE = int256(0x3ffff) << 236;
    int256 internal constant TWO = int256(0x40000) << 236;
    int256 internal constant HALF = int256(0x3fffe) << 236;
    int256 internal constant SIGN = type(int256).min;
    int256 internal constant MAG = type(int256).max;
    int256 internal constant HIDDEN = int256(1) << 236;
    int256 internal constant MIN_NORMAL = int256(1) << 236;         // exponent 1, fraction 0
    int256 internal constant MAX_WORD = type(int256).max;           // exponent 0x7ffff, fraction all ones

    function setUp() public virtual {
        obj = IBL19(_deployYulObject("out/BL19.yul/BL19.json"));
        objE = IBL19E(_deployYulObject("out/BL19E.yul/BL19E.json"));
        objH = IBL19H(_deployYulObject("out/BL19H.yul/BL19H.json"));
        objN = IBL19N(_deployYulObject("out/BL19N.yul/BL19N.json"));
        objS = IBL19S(_deployYulObject("out/BL19S.yul/BL19S.json"));
        lib = new LibUser19();
    }

    function _deployYulObject(string memory artifact) internal returns (address deployed) {
        bytes memory initCode = vm.parseJsonBytes(vm.readFile(artifact), ".bytecode.object");
        assembly ("memory-safe") {
            deployed := create(0, add(initCode, 0x20), mload(initCode))
        }
        require(deployed != address(0), "yul deploy failed");
    }

    // ---- the word ---------------------------------------------------------

    function _unpack(int256 w) internal pure returns (bool s, uint256 e, uint256 m) {
        s = w < 0;
        e = (uint256(w) >> 236) & 0x7ffff;
        m = uint256(w) & ((uint256(1) << 236) - 1);
        if (e != 0) m |= uint256(1) << 236;
    }

    /// A number from (sign, unbiased exponent u, 237-bit significand m).
    function _mk(bool s, int256 u, uint256 m) internal pure returns (int256) {
        uint256 e = uint256(u + int256(BIAS));
        return int256((s ? uint256(1) << 255 : 0) | (e << 236) | (m & ((uint256(1) << 236) - 1)));
    }

    /// Relative correct bits of `got` against `truth`, on decoded values:
    /// align the significands at the larger exponent and compare. 256 when
    /// equal; 0 when the signs differ or the exponents are far apart.
    function _bits(int256 got, int256 truth) internal pure returns (uint256) {
        if (got == truth) return 256;
        if (truth == 0 || got == 0) return 0;
        (bool sg, uint256 eg, uint256 mg) = _unpack(got);
        (bool st, uint256 et, uint256 mt) = _unpack(truth);
        if (sg != st) return 0;
        uint256 T; uint256 M;
        if (et >= eg) {
            if (et - eg > 18) return 0;
            T = mt << (et - eg); M = mg;
        } else {
            if (eg - et > 18) return 0;
            T = mt; M = mg << (eg - et);
        }
        uint256 d = T > M ? T - M : M - T;
        if (d == 0) return 256;
        uint256 bt = _msb(T); uint256 bd = _msb(d);
        return bt > bd ? bt - bd : 0;
    }

    /// Distance in ULPs of the truth's exponent (capped), for the 2-ULP rule.
    function _ulps(int256 got, int256 truth) internal pure returns (uint256) {
        if (got == truth) return 0;
        (bool sg, uint256 eg, uint256 mg) = _unpack(got);
        (bool st, uint256 et, uint256 mt) = _unpack(truth);
        if (sg != st && got != 0 && truth != 0) return type(uint256).max;
        if (truth == 0 || got == 0) return type(uint256).max;
        if (et > eg + 1 || eg > et + 1) return type(uint256).max;
        uint256 T = et >= eg ? mt << (et - eg) : mt;
        uint256 M = eg >= et ? mg << (eg - et) : mg;
        return T > M ? T - M : M - T;
    }

    function _msb(uint256 x) internal pure returns (uint256 r) { while (x > 1) { x >>= 1; r++; } }

    function _sel(bytes memory err) internal pure returns (bytes4 s) {
        if (err.length < 4) return 0;
        assembly { s := mload(add(err, 0x20)) }
    }

    struct Res { bool ok; int256 value; bytes err; }

    function _try(address target, bytes memory data) internal view returns (Res memory r) {
        (bool ok, bytes memory out) = target.staticcall(data);
        r.ok = ok;
        if (ok) r.value = abi.decode(out, (int256));
        else r.err = out;
    }

    function _assertSame(Res memory x, Res memory y, string memory what) internal pure {
        assertEq(x.ok, y.ok, string.concat(what, ": ok flag"));
        if (x.ok) assertEq(x.value, y.value, string.concat(what, ": value"));
        else assertEq(keccak256(x.err), keccak256(y.err), string.concat(what, ": revert data"));
    }

    /// The object that serves op (contracts/src/bl19/ops.json): BL19E for
    /// the elementary functions, BL19H for the hyperbolic ones, BL19N for
    /// erf, erfc and normCdf, BL19S for Lambert W, BL19 for the rest.
    function _isE(string memory op) internal pure returns (bool) {
        bytes32 h = keccak256(bytes(op));
        return h == keccak256("exp") || h == keccak256("exp2") || h == keccak256("exp10") || h == keccak256("expm1")
            || h == keccak256("ln") || h == keccak256("log2") || h == keccak256("log10") || h == keccak256("log2Up")
            || h == keccak256("log1p") || h == keccak256("pow") || h == keccak256("powu") || h == keccak256("compound");
    }

    function _isH(string memory op) internal pure returns (bool) {
        bytes32 h = keccak256(bytes(op));
        return h == keccak256("sinh") || h == keccak256("cosh") || h == keccak256("tanh") || h == keccak256("atanh");
    }

    function _isN(string memory op) internal pure returns (bool) {
        bytes32 h = keccak256(bytes(op));
        return h == keccak256("erf") || h == keccak256("erfc") || h == keccak256("normCdf");
    }

    function _isS(string memory op) internal pure returns (bool) {
        bytes32 h = keccak256(bytes(op));
        return h == keccak256("lambertW0") || h == keccak256("lambertWm1");
    }

    function _objFor(string memory op) internal view returns (address) {
        if (_isE(op)) return address(objE);
        if (_isH(op)) return address(objH);
        if (_isN(op)) return address(objN);
        if (_isS(op)) return address(objS);
        return address(obj);
    }

    function _expectRevertAt(address o, bytes memory call, bytes4 err, string memory what) internal view {
        Res memory r = _try(o, call);
        assertFalse(r.ok, string.concat(what, ": expected revert"));
        assertEq(_sel(r.err), err, string.concat(what, ": wrong error"));
    }

    function _expectRevert(bytes memory call, bytes4 err, string memory what) internal view {
        Res memory o = _try(address(obj), call);
        assertFalse(o.ok, string.concat(what, ": expected revert"));
        assertEq(_sel(o.err), err, string.concat(what, ": wrong error"));
    }
}

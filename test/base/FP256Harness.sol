// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {IFP256} from "../../contracts/src/fp256/IFP256.sol";
import {IFP256X} from "../../contracts/src/fp256/IFP256X.sol";
import {IFP256X2} from "../../contracts/src/fp256/IFP256X2.sol";
import {IFP256X3} from "../../contracts/src/fp256/IFP256X3.sol";
import {FP256Lib} from "../../contracts/src/fp256/FP256Lib.sol";

/// @notice External wrapper around the inline library so every call can be
///         made with try/catch and compared with the object on the same calldata.
contract LibUser256 {
    function add(int256 a, int256 b) external pure returns (int256) { return FP256Lib.add(a, b); }
    function sub(int256 a, int256 b) external pure returns (int256) { return FP256Lib.sub(a, b); }
    function mul(int256 a, int256 b) external pure returns (int256) { return FP256Lib.mul(a, b); }
    function div(int256 a, int256 b) external pure returns (int256) { return FP256Lib.div(a, b); }
    function sqrt(int256 x) external pure returns (int256) { return FP256Lib.sqrt(x); }
    function exp(int256 x) external pure returns (int256) { return FP256Lib.exp(x); }
    function ln(int256 x) external pure returns (int256) { return FP256Lib.ln(x); }
    function pow(int256 x, int256 y) external pure returns (int256) { return FP256Lib.pow(x, y); }
    function log1p(int256 x) external pure returns (int256) { return FP256Lib.log1p(x); }
    function expm1(int256 x) external pure returns (int256) { return FP256Lib.expm1(x); }
    function erf(int256 x) external pure returns (int256) { return FP256Lib.erf(x); }
    function erfc(int256 x) external pure returns (int256) { return FP256Lib.erfc(x); }
    function normCdf(int256 x) external pure returns (int256) { return FP256Lib.normCdf(x); }
    function lambertW0(int256 x) external pure returns (int256) { return FP256Lib.lambertW0(x); }
    function lambertWm1(int256 x) external pure returns (int256) { return FP256Lib.lambertWm1(x); }
    function powu(int256 x, int256 n) external pure returns (int256) { return FP256Lib.powu(x, n); }
    function compound(int256 r, int256 n) external pure returns (int256) { return FP256Lib.compound(r, n); }
    function neg(int256 x) external pure returns (int256) { return FP256Lib.neg(x); }
    function abs(int256 x) external pure returns (int256) { return FP256Lib.abs(x); }
    function sign(int256 x) external pure returns (int256) { return FP256Lib.sign(x); }
    function cmp(int256 a, int256 b) external pure returns (int256) { return FP256Lib.cmp(a, b); }
    function lt(int256 a, int256 b) external pure returns (int256) { return FP256Lib.lt(a, b); }
    function eq(int256 a, int256 b) external pure returns (int256) { return FP256Lib.eq(a, b); }
    function fromUint(uint256 x) external pure returns (int256) { return FP256Lib.fromUint(x); }
    function fromFP127(int256 x) external pure returns (int256) { return FP256Lib.fromFP127(x); }
    function toFP127(int256 x) external pure returns (int256) { return FP256Lib.toFP127(x); }
    function fromFixed18(int256 x) external pure returns (int256) { return FP256Lib.fromFixed18(x); }
    function toFixed18(int256 x) external pure returns (int256) { return FP256Lib.toFixed18(x); }
    function mulDown(int256 a, int256 b) external pure returns (int256) { return FP256Lib.mulDown(a, b); }
    function mulUp(int256 a, int256 b) external pure returns (int256) { return FP256Lib.mulUp(a, b); }
    function divDown(int256 a, int256 b) external pure returns (int256) { return FP256Lib.divDown(a, b); }
    function divUp(int256 a, int256 b) external pure returns (int256) { return FP256Lib.divUp(a, b); }
    function toUintDown(int256 x) external pure returns (uint256) { return FP256Lib.toUintDown(x); }
    function toUintUp(int256 x) external pure returns (uint256) { return FP256Lib.toUintUp(x); }
    function toIntDown(int256 x) external pure returns (int256) { return FP256Lib.toIntDown(x); }
    function toIntUp(int256 x) external pure returns (int256) { return FP256Lib.toIntUp(x); }
    function floor(int256 x) external pure returns (int256) { return FP256Lib.floor(x); }
    function ceil(int256 x) external pure returns (int256) { return FP256Lib.ceil(x); }
    function fromUintDown(uint256 x) external pure returns (int256) { return FP256Lib.fromUintDown(x); }
    function fromUintUp(uint256 x) external pure returns (int256) { return FP256Lib.fromUintUp(x); }
    function toFixed18Down(int256 x) external pure returns (int256) { return FP256Lib.toFixed18Down(x); }
    function toFixed18Up(int256 x) external pure returns (int256) { return FP256Lib.toFixed18Up(x); }
    // #79: FP256X2
    function exp2(int256 x) external pure returns (int256) { return FP256Lib.exp2(x); }
    function exp10(int256 x) external pure returns (int256) { return FP256Lib.exp10(x); }
    function log2(int256 x) external pure returns (int256) { return FP256Lib.log2(x); }
    function log10(int256 x) external pure returns (int256) { return FP256Lib.log10(x); }
    function log2Up(int256 x) external pure returns (int256) { return FP256Lib.log2Up(x); }
    function cbrt(int256 x) external pure returns (int256) { return FP256Lib.cbrt(x); }
    function sinh(int256 x) external pure returns (int256) { return FP256Lib.sinh(x); }
    function cosh(int256 x) external pure returns (int256) { return FP256Lib.cosh(x); }
    function tanh(int256 x) external pure returns (int256) { return FP256Lib.tanh(x); }
    function atanh(int256 x) external pure returns (int256) { return FP256Lib.atanh(x); }
    // #79: FP256X3
    function min(int256 a, int256 b) external pure returns (int256) { return FP256Lib.min(a, b); }
    function max(int256 a, int256 b) external pure returns (int256) { return FP256Lib.max(a, b); }
    function clamp(int256 x, int256 lo, int256 hi) external pure returns (int256) { return FP256Lib.clamp(x, lo, hi); }
    function avg(int256 a, int256 b) external pure returns (int256) { return FP256Lib.avg(a, b); }
    function dist(int256 a, int256 b) external pure returns (int256) { return FP256Lib.dist(a, b); }
    function zeroFloorSub(int256 a, int256 b) external pure returns (int256) { return FP256Lib.zeroFloorSub(a, b); }
    function inv(int256 x) external pure returns (int256) { return FP256Lib.inv(x); }
    function lerp(int256 a, int256 b, int256 t) external pure returns (int256) { return FP256Lib.lerp(a, b, t); }
    function frac(int256 x) external pure returns (int256) { return FP256Lib.frac(x); }
    function round(int256 x) external pure returns (int256) { return FP256Lib.round(x); }
    function gcd(int256 a, int256 b) external pure returns (int256) { return FP256Lib.gcd(a, b); }
    function factorial(int256 n) external pure returns (int256) { return FP256Lib.factorial(n); }
    function pi(int256 terms) external pure returns (int256) { return FP256Lib.pi(terms); }
    function gavg(int256 a, int256 b) external pure returns (int256) { return FP256Lib.gavg(a, b); }
    function hypot(int256 a, int256 b) external pure returns (int256) { return FP256Lib.hypot(a, b); }
}

abstract contract FP256Harness is Test {
    IFP256 internal obj;
    /// release four's second object: the error function family and Lambert W
    IFP256X internal objX;
    /// #79's objects: the exponential family and roots on the kernels (FP256X2),
    /// the algebraic ops (FP256X3)
    IFP256X2 internal objX2;
    IFP256X3 internal objX3;
    LibUser256 internal lib;

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
        obj = IFP256(_deployYulObject("out/FP256.yul/FP256.json"));
        objX = IFP256X(_deployYulObject("out/FP256X.yul/FP256X.json"));
        objX2 = IFP256X2(_deployYulObject("out/FP256X2.yul/FP256X2.json"));
        objX3 = IFP256X3(_deployYulObject("out/FP256X3.yul/FP256X3.json"));
        lib = new LibUser256();
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

    /// The object that serves op: FP256X for the error function family and
    /// Lambert W, FP256 for everything else.
    function _isX(string memory op) internal pure returns (bool) {
        bytes32 h = keccak256(bytes(op));
        return h == keccak256("erf") || h == keccak256("erfc") || h == keccak256("normCdf")
            || h == keccak256("lambertW0") || h == keccak256("lambertWm1");
    }

    /// #79's ops: FP256X2 for the exponential family, cbrt and the hyperbolics,
    /// FP256X3 for the algebraic ones.
    function _isX2(string memory op) internal pure returns (bool) {
        bytes32 h = keccak256(bytes(op));
        return h == keccak256("exp2") || h == keccak256("exp10") || h == keccak256("log2") || h == keccak256("log10")
            || h == keccak256("log2Up") || h == keccak256("cbrt") || h == keccak256("sinh") || h == keccak256("cosh")
            || h == keccak256("tanh") || h == keccak256("atanh");
    }

    function _isX3(string memory op) internal pure returns (bool) {
        bytes32 h = keccak256(bytes(op));
        return h == keccak256("min") || h == keccak256("max") || h == keccak256("clamp") || h == keccak256("avg")
            || h == keccak256("dist") || h == keccak256("zeroFloorSub") || h == keccak256("inv") || h == keccak256("lerp")
            || h == keccak256("frac") || h == keccak256("round") || h == keccak256("gcd") || h == keccak256("factorial")
            || h == keccak256("pi") || h == keccak256("gavg") || h == keccak256("hypot");
    }

    function _objFor(string memory op) internal view returns (address) {
        if (_isX(op)) return address(objX);
        if (_isX2(op)) return address(objX2);
        if (_isX3(op)) return address(objX3);
        return address(obj);
    }

    function _expectRevertX(bytes memory call, bytes4 err, string memory what) internal view {
        Res memory o = _try(address(objX), call);
        assertFalse(o.ok, string.concat(what, ": expected revert"));
        assertEq(_sel(o.err), err, string.concat(what, ": wrong error"));
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

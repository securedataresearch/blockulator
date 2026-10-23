// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {IFP127} from "../../contracts/src/fp127/IFP127.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP127Caller} from "../../contracts/src/fp127/FP127Caller.sol";
import {FixedPointMathLib} from "../../lib/solady/src/utils/FixedPointMathLib.sol";

/// @notice The legacy Huff ABI. Every parameter is uint256 and the *Raw ops
///         speak native 127.128. Selectors match the bytecode deployed on
///         Sepolia at 0xfae694D0c2c44181791F838c54Ed64C3151FfE30.
interface IHuffFP127 {
    function addRaw(uint256 a, uint256 b) external pure returns (uint256);
    function subRaw(uint256 a, uint256 b) external pure returns (uint256);
    function mulRaw(uint256 a, uint256 b) external pure returns (uint256);
    function divRaw(uint256 a, uint256 b) external pure returns (uint256);
    function fromFixed18(uint256 x) external pure returns (uint256);
    function toFixed18(uint256 x) external pure returns (uint256);
}

/// @notice External wrapper around the inline library so every call can be
///         made with try/catch and measured like an external call.
contract LibUser {
    function add(int256 a, int256 b) external pure returns (int256) { return FP127Lib.add(a, b); }
    function sub(int256 a, int256 b) external pure returns (int256) { return FP127Lib.sub(a, b); }
    function mul(int256 a, int256 b) external pure returns (int256) { return FP127Lib.mul(a, b); }
    function div(int256 a, int256 b) external pure returns (int256) { return FP127Lib.div(a, b); }
    function fromFixed18(int256 x) external pure returns (int256) { return FP127Lib.fromFixed18(x); }
    function toFixed18(int256 x) external pure returns (int256) { return FP127Lib.toFixed18(x); }
    function toFixed18Down(int256 x) external pure returns (int256) { return FP127Lib.toFixed18Down(x); }
    function toFixed18Up(int256 x) external pure returns (int256) { return FP127Lib.toFixed18Up(x); }
    function mulDown(int256 a, int256 b) external pure returns (int256) { return FP127Lib.mulDown(a, b); }
    function mulUp(int256 a, int256 b) external pure returns (int256) { return FP127Lib.mulUp(a, b); }
    function divDown(int256 a, int256 b) external pure returns (int256) { return FP127Lib.divDown(a, b); }
    function divUp(int256 a, int256 b) external pure returns (int256) { return FP127Lib.divUp(a, b); }
    function exp(int256 x) external pure returns (int256) { return FP127Lib.exp(x); }
    function exp2(int256 x) external pure returns (int256) { return FP127Lib.exp2(x); }
    function exp10(int256 x) external pure returns (int256) { return FP127Lib.exp10(x); }
    function ln(int256 x) external pure returns (int256) { return FP127Lib.ln(x); }
    function log2(int256 x) external pure returns (int256) { return FP127Lib.log2(x); }
    function log10(int256 x) external pure returns (int256) { return FP127Lib.log10(x); }
    function log2Up(int256 x) external pure returns (int256) { return FP127Lib.log2Up(x); }
    function sqrt(int256 x) external pure returns (int256) { return FP127Lib.sqrt(x); }
    function cbrt(int256 x) external pure returns (int256) { return FP127Lib.cbrt(x); }
    function abs(int256 x) external pure returns (int256) { return FP127Lib.abs(x); }
    function neg(int256 x) external pure returns (int256) { return FP127Lib.neg(x); }
    function inv(int256 x) external pure returns (int256) { return FP127Lib.inv(x); }
    function sign(int256 x) external pure returns (int256) { return FP127Lib.sign(x); }
    function floor(int256 x) external pure returns (int256) { return FP127Lib.floor(x); }
    function ceil(int256 x) external pure returns (int256) { return FP127Lib.ceil(x); }
    function frac(int256 x) external pure returns (int256) { return FP127Lib.frac(x); }
    function round(int256 x) external pure returns (int256) { return FP127Lib.round(x); }
    function factorial(int256 x) external pure returns (int256) { return FP127Lib.factorial(x); }
    function lambertW0(int256 x) external pure returns (int256) { return FP127Lib.lambertW0(x); }
    function lambertWm1(int256 x) external pure returns (int256) { return FP127Lib.lambertWm1(x); }
    function pow(int256 a, int256 b) external pure returns (int256) { return FP127Lib.pow(a, b); }
    function min(int256 a, int256 b) external pure returns (int256) { return FP127Lib.min(a, b); }
    function max(int256 a, int256 b) external pure returns (int256) { return FP127Lib.max(a, b); }
    function avg(int256 a, int256 b) external pure returns (int256) { return FP127Lib.avg(a, b); }
    function zeroFloorSub(int256 a, int256 b) external pure returns (int256) { return FP127Lib.zeroFloorSub(a, b); }
    function dist(int256 a, int256 b) external pure returns (int256) { return FP127Lib.dist(a, b); }
    function gavg(int256 a, int256 b) external pure returns (int256) { return FP127Lib.gavg(a, b); }
    function hypot(int256 a, int256 b) external pure returns (int256) { return FP127Lib.hypot(a, b); }
    function clamp(int256 a, int256 b, int256 c) external pure returns (int256) { return FP127Lib.clamp(a, b, c); }
    function lerp(int256 a, int256 b, int256 c) external pure returns (int256) { return FP127Lib.lerp(a, b, c); }
    function powu(int256 a, int256 b) external pure returns (int256) { return FP127Lib.powu(a, b); }
    function compound(int256 a, int256 b) external pure returns (int256) { return FP127Lib.compound(a, b); }
    function log1p(int256 x) external pure returns (int256) { return FP127Lib.log1p(x); }
    function expm1(int256 x) external pure returns (int256) { return FP127Lib.expm1(x); }
    function sinh(int256 x) external pure returns (int256) { return FP127Lib.sinh(x); }
    function cosh(int256 x) external pure returns (int256) { return FP127Lib.cosh(x); }
    function tanh(int256 x) external pure returns (int256) { return FP127Lib.tanh(x); }
    function atanh(int256 x) external pure returns (int256) { return FP127Lib.atanh(x); }
    function erf(int256 x) external pure returns (int256) { return FP127Lib.erf(x); }
    function erfc(int256 x) external pure returns (int256) { return FP127Lib.erfc(x); }
    function normCdf(int256 x) external pure returns (int256) { return FP127Lib.normCdf(x); }
}

/// @notice Independent reference arithmetic built on Solady's fullMulDiv so
///         the overflow checks in the Yul are tested against something that
///         is not the Yul.
contract Ref {
    uint256 constant TWO128 = 1 << 128;
    uint256 constant MAX_POS = uint256(type(int256).max);

    function add(int256 a, int256 b) external pure returns (int256) { return a + b; }
    function sub(int256 a, int256 b) external pure returns (int256) { return a - b; }

    /// floor(a * b / 2^128) with exact 512-bit intermediate, reverting if the
    /// mathematically exact result does not fit in int256.
    function mul(int256 a, int256 b) external pure returns (int256) {
        bool neg = (a < 0) != (b < 0);
        uint256 ua = _abs(a);
        uint256 ub = _abs(b);
        uint256 q = FixedPointMathLib.fullMulDiv(ua, ub, TWO128);
        uint256 rem = mulmod(ua, ub, TWO128);
        if (!neg) {
            require(q <= MAX_POS, "ref overflow");
            return int256(q);
        }
        // floor of a negative quotient
        uint256 mag = q + (rem != 0 ? 1 : 0);
        require(mag <= MAX_POS + 1, "ref overflow");
        if (mag == 0) return 0;
        return -int256(mag - 1) - 1;
    }

    /// trunc(a * 2^128 / b), reverting on b == 0 or when the result does not
    /// fit in int256.
    function div(int256 a, int256 b) external pure returns (int256) {
        require(b != 0, "ref div0");
        bool neg = (a < 0) != (b < 0);
        uint256 q = FixedPointMathLib.fullMulDiv(_abs(a), TWO128, _abs(b));
        if (!neg) {
            require(q <= MAX_POS, "ref overflow");
            return int256(q);
        }
        require(q <= MAX_POS + 1, "ref overflow");
        if (q == 0) return 0;
        return -int256(q - 1) - 1;
    }

    function fromFixed18(int256 x) external pure returns (int256) {
        require(x >= -(int256(1) << 127) && x < (int256(1) << 127), "ref range");
        return (x << 128) / 1e18;
    }

    function toFixed18(int256 x) external pure returns (int256) {
        int256 hi = x >> 128;
        uint256 lo = uint256(x) & (TWO128 - 1);
        return hi * 1e18 + int256((lo * 1e18) >> 128);
    }

    function _abs(int256 x) internal pure returns (uint256) {
        return x < 0 ? uint256(-(x + 1)) + 1 : uint256(x);
    }
}

abstract contract FP127Harness is Test {
    IHuffFP127 internal huff;
    IFP127 internal obj;
    LibUser internal lib;
    FP127Caller internal caller;
    Ref internal ref;

    int256 internal constant ONE = int256(1) << 128;
    int256 internal constant MIN = type(int256).min;
    int256 internal constant MAX = type(int256).max;

    string internal constant HUFF_BASELINE = "contracts/archive/huff/fp127.sepolia.runtime.hex";

    function setUp() public virtual {
        bytes memory code = vm.parseBytes(vm.readFile(HUFF_BASELINE));
        address h = makeAddr("huff-sepolia-baseline");
        vm.etch(h, code);
        huff = IHuffFP127(h);

        obj = IFP127(_deployYulObject("out/FP127.yul/FP127.json"));
        lib = new LibUser();
        caller = new FP127Caller(address(obj));
        ref = new Ref();
    }

    /// Yul artifacts carry a null ABI, which vm.getCode refuses to parse, so
    /// the init code is read from the artifact JSON and created directly.
    function _deployYulObject(string memory artifact) internal returns (address deployed) {
        bytes memory initCode = vm.parseJsonBytes(vm.readFile(artifact), ".bytecode.object");
        assembly ("memory-safe") {
            deployed := create(0, add(initCode, 0x20), mload(initCode))
        }
        require(deployed != address(0), "yul deploy failed");
    }

    // ---- result capture -------------------------------------------------

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

    /// Asserts that the Yul object reverts on `call` with the custom error `err`.
    function _expectRevert(bytes memory call, bytes4 err, string memory what) internal view {
        Res memory o = _try(address(obj), call);
        assertFalse(o.ok, string.concat(what, ": expected revert"));
        assertEq(_sel(o.err), err, string.concat(what, ": wrong error"));
    }

    function _sel(bytes memory err) internal pure returns (bytes4 s) {
        if (err.length < 4) return 0;
        assembly { s := mload(add(err, 0x20)) }
    }
}

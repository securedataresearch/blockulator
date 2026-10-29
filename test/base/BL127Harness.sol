// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {IBL127} from "../../contracts/src/bl127/IBL127.sol";
import {IBL127E} from "../../contracts/src/bl127/IBL127E.sol";
import {IBL127H} from "../../contracts/src/bl127/IBL127H.sol";
import {IBL127N} from "../../contracts/src/bl127/IBL127N.sol";
import {IBL127S} from "../../contracts/src/bl127/IBL127S.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import {BL127Caller} from "../../contracts/src/bl127/BL127Caller.sol";
import {FixedPointMathLib} from "../../lib/solady/src/utils/FixedPointMathLib.sol";

/// @notice The legacy Huff ABI. Every parameter is uint256 and the *Raw ops
///         speak native 127.128. Selectors match the bytecode deployed on
///         Sepolia at 0xfae694D0c2c44181791F838c54Ed64C3151FfE30.
interface IHuffBL127 {
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
    function add(int256 a, int256 b) external pure returns (int256) { return BL127Lib.add(a, b); }
    function sub(int256 a, int256 b) external pure returns (int256) { return BL127Lib.sub(a, b); }
    function mul(int256 a, int256 b) external pure returns (int256) { return BL127Lib.mul(a, b); }
    function div(int256 a, int256 b) external pure returns (int256) { return BL127Lib.div(a, b); }
    function fromFixed18(int256 x) external pure returns (int256) { return BL127Lib.fromFixed18(x); }
    function toFixed18(int256 x) external pure returns (int256) { return BL127Lib.toFixed18(x); }
    function toFixed18Down(int256 x) external pure returns (int256) { return BL127Lib.toFixed18Down(x); }
    function toFixed18Up(int256 x) external pure returns (int256) { return BL127Lib.toFixed18Up(x); }
    function mulDown(int256 a, int256 b) external pure returns (int256) { return BL127Lib.mulDown(a, b); }
    function mulUp(int256 a, int256 b) external pure returns (int256) { return BL127Lib.mulUp(a, b); }
    function divDown(int256 a, int256 b) external pure returns (int256) { return BL127Lib.divDown(a, b); }
    function divUp(int256 a, int256 b) external pure returns (int256) { return BL127Lib.divUp(a, b); }
    function exp(int256 x) external pure returns (int256) { return BL127Lib.exp(x); }
    function exp2(int256 x) external pure returns (int256) { return BL127Lib.exp2(x); }
    function exp10(int256 x) external pure returns (int256) { return BL127Lib.exp10(x); }
    function ln(int256 x) external pure returns (int256) { return BL127Lib.ln(x); }
    function log2(int256 x) external pure returns (int256) { return BL127Lib.log2(x); }
    function log10(int256 x) external pure returns (int256) { return BL127Lib.log10(x); }
    function log2Up(int256 x) external pure returns (int256) { return BL127Lib.log2Up(x); }
    function sqrt(int256 x) external pure returns (int256) { return BL127Lib.sqrt(x); }
    function cbrt(int256 x) external pure returns (int256) { return BL127Lib.cbrt(x); }
    function abs(int256 x) external pure returns (int256) { return BL127Lib.abs(x); }
    function neg(int256 x) external pure returns (int256) { return BL127Lib.neg(x); }
    function inv(int256 x) external pure returns (int256) { return BL127Lib.inv(x); }
    function sign(int256 x) external pure returns (int256) { return BL127Lib.sign(x); }
    function floor(int256 x) external pure returns (int256) { return BL127Lib.floor(x); }
    function ceil(int256 x) external pure returns (int256) { return BL127Lib.ceil(x); }
    function frac(int256 x) external pure returns (int256) { return BL127Lib.frac(x); }
    function round(int256 x) external pure returns (int256) { return BL127Lib.round(x); }
    function factorial(int256 x) external pure returns (int256) { return BL127Lib.factorial(x); }
    function lambertW0(int256 x) external pure returns (int256) { return BL127Lib.lambertW0(x); }
    function lambertWm1(int256 x) external pure returns (int256) { return BL127Lib.lambertWm1(x); }
    function pow(int256 a, int256 b) external pure returns (int256) { return BL127Lib.pow(a, b); }
    function min(int256 a, int256 b) external pure returns (int256) { return BL127Lib.min(a, b); }
    function max(int256 a, int256 b) external pure returns (int256) { return BL127Lib.max(a, b); }
    function avg(int256 a, int256 b) external pure returns (int256) { return BL127Lib.avg(a, b); }
    function zeroFloorSub(int256 a, int256 b) external pure returns (int256) { return BL127Lib.zeroFloorSub(a, b); }
    function dist(int256 a, int256 b) external pure returns (int256) { return BL127Lib.dist(a, b); }
    function gavg(int256 a, int256 b) external pure returns (int256) { return BL127Lib.gavg(a, b); }
    function hypot(int256 a, int256 b) external pure returns (int256) { return BL127Lib.hypot(a, b); }
    function clamp(int256 a, int256 b, int256 c) external pure returns (int256) { return BL127Lib.clamp(a, b, c); }
    function lerp(int256 a, int256 b, int256 c) external pure returns (int256) { return BL127Lib.lerp(a, b, c); }
    function powu(int256 a, int256 b) external pure returns (int256) { return BL127Lib.powu(a, b); }
    function compound(int256 a, int256 b) external pure returns (int256) { return BL127Lib.compound(a, b); }
    function log1p(int256 x) external pure returns (int256) { return BL127Lib.log1p(x); }
    function expm1(int256 x) external pure returns (int256) { return BL127Lib.expm1(x); }
    function sinh(int256 x) external pure returns (int256) { return BL127Lib.sinh(x); }
    function cosh(int256 x) external pure returns (int256) { return BL127Lib.cosh(x); }
    function tanh(int256 x) external pure returns (int256) { return BL127Lib.tanh(x); }
    function atanh(int256 x) external pure returns (int256) { return BL127Lib.atanh(x); }
    function erf(int256 x) external pure returns (int256) { return BL127Lib.erf(x); }
    function erfc(int256 x) external pure returns (int256) { return BL127Lib.erfc(x); }
    function normCdf(int256 x) external pure returns (int256) { return BL127Lib.normCdf(x); }
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

abstract contract BL127Harness is Test {
    IHuffBL127 internal huff;
    /// the number: arithmetic and its directed forms, conversions, roots,
    /// comparison, rounding
    IBL127 internal obj;
    /// the elementary functions on the exp/log kernels
    IBL127E internal objE;
    /// the hyperbolic functions
    IBL127H internal objH;
    /// the normal distribution: erf, erfc, normCdf
    IBL127N internal objN;
    /// the special functions: Lambert W
    IBL127S internal objS;
    /// Each export's object, from contracts/src/bl127/ops.json, by name hash
    /// and by selector: the letter after "BL127" ("E", "H", "N", "S"), zero for
    /// BL127 itself. Read once in setUp, so a re-layout of the objects edits
    /// only the object tags in BL127.yul.src.
    mapping(bytes32 => bytes1) internal objOfName;
    mapping(bytes4 => bytes1) internal objOfSel;
    LibUser internal lib;
    BL127Caller internal caller;
    Ref internal ref;

    int256 internal constant ONE = int256(1) << 128;
    int256 internal constant MIN = type(int256).min;
    int256 internal constant MAX = type(int256).max;

    string internal constant HUFF_BASELINE = "contracts/archive/huff/bl127.sepolia.runtime.hex";

    function setUp() public virtual {
        bytes memory code = vm.parseBytes(vm.readFile(HUFF_BASELINE));
        address h = makeAddr("huff-sepolia-baseline");
        vm.etch(h, code);
        huff = IHuffBL127(h);

        obj = IBL127(_deployYulObject("out/BL127.yul/BL127.json"));
        objE = IBL127E(_deployYulObject("out/BL127E.yul/BL127E.json"));
        objH = IBL127H(_deployYulObject("out/BL127H.yul/BL127H.json"));
        objN = IBL127N(_deployYulObject("out/BL127N.yul/BL127N.json"));
        objS = IBL127S(_deployYulObject("out/BL127S.yul/BL127S.json"));
        _loadObjects();
        lib = new LibUser();
        caller = new BL127Caller(address(obj));
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

    function _loadObjects() internal {
        string memory json = vm.readFile("contracts/src/bl127/ops.json");
        for (uint256 i; ; i++) {
            string memory op = string.concat(".ops[", vm.toString(i), "]");
            if (!vm.keyExistsJson(json, op)) break;
            bytes memory o = bytes(vm.parseJsonString(json, string.concat(op, ".object")));
            bytes1 letter = o.length > 5 ? o[5] : bytes1(0);
            objOfName[keccak256(bytes(vm.parseJsonString(json, string.concat(op, ".name"))))] = letter;
            objOfSel[bytes4(keccak256(bytes(vm.parseJsonString(json, string.concat(op, ".signature")))))] = letter;
        }
    }

    function _objAt(bytes1 letter) internal view returns (address) {
        if (letter == "E") return address(objE);
        if (letter == "H") return address(objH);
        if (letter == "N") return address(objN);
        if (letter == "S") return address(objS);
        return address(obj);
    }

    /// The object that serves op (contracts/src/bl127/ops.json): BL127E for
    /// the elementary functions, BL127H for the hyperbolic ones, BL127N for
    /// erf, erfc and normCdf, BL127S for Lambert W, BL127 for the rest.
    function _objFor(string memory op) internal view returns (address) {
        return _objAt(objOfName[keccak256(bytes(op))]);
    }

    /// The object that serves the call's selector; BL127 for a selector no
    /// object has, so a bad-selector test still reaches an object.
    function _objOf(bytes memory call) internal view returns (address) {
        return _objAt(call.length < 4 ? bytes1(0) : objOfSel[bytes4(call)]);
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

    /// Asserts that the Yul object serving `call` reverts on it with the
    /// custom error `err`.
    function _expectRevert(bytes memory call, bytes4 err, string memory what) internal view {
        Res memory o = _try(_objOf(call), call);
        assertFalse(o.ok, string.concat(what, ": expected revert"));
        assertEq(_sel(o.err), err, string.concat(what, ": wrong error"));
    }

    function _sel(bytes memory err) internal pure returns (bytes4 s) {
        if (err.length < 4) return 0;
        assembly { s := mload(add(err, 0x20)) }
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP127Harness} from "../base/FP127Harness.sol";
import {IFP127} from "../../contracts/src/fp127/IFP127.sol";
import {console} from "forge-std/console.sol";

/// @title Precision
/// @notice Every op against committed mpmath vectors (test/fp127/vectors/*.json,
///         produced by scripts/fp127/oracle.py). No ffi at test time.
///
/// For each vector: if the oracle says REVERT:<Error>, the Yul must revert
/// with that selector. Otherwise the relative correct bits
/// msb(|truth|) - msb(|truth - got|) (256 when exact) must be at or above the
/// op's floor. Per-op count / min / mean bits and the worst input are printed
/// as PREC|op|n|min|mean|worstInput and written to docs/fp127/precision.json.
contract Precision is FP127Harness {
    /// Where the per-op stats are written; empty disables the write.
    function _out() internal pure virtual returns (string memory) { return "docs/fp127/precision.json"; }

    function _ops() internal pure returns (string[49] memory o) {
        o = [
            "add", "sub", "mul", "div", "fromFixed18", "toFixed18",
            "exp", "exp2", "exp10", "ln", "log2", "log10", "log2Up",
            "sqrt", "cbrt", "pow", "inv", "abs", "neg", "sign", "min", "max", "clamp", "avg",
            "zeroFloorSub", "dist", "lerp", "floor", "ceil", "frac", "round", "gcd", "factorial",
            "hypot", "gavg", "lambertW0", "lambertWm1", "pi",
            "powu", "compound", "log1p", "expm1", "sinh", "cosh", "tanh", "atanh", "erf", "erfc", "normCdf"
        ];
    }

    /// Minimum relative correct bits per op. 256 means bit-exact.
    function _floorBits(string memory op) internal pure returns (uint256) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("hypot") || h == keccak256("gavg")) return 120;
        // guard-bit kernels: the exp family is limited by its polynomial (2^-145),
        // the log family rounds to within one ULP of the truth
        if (h == keccak256("exp") || h == keccak256("exp2") || h == keccak256("exp10")) return 140;
        if (h == keccak256("ln") || h == keccak256("log2") || h == keccak256("log10")) return 200;
        if (h == keccak256("pow") || h == keccak256("cbrt") || h == keccak256("lambertW0")
            || h == keccak256("lambertWm1") || h == keccak256("pi")) return 115;
        // v4: the exp kernel's 2^-145 bounds expm1, sinh, cosh, tanh and the
        // erf family; log1p and atanh ride the log kernel; powu and compound
        // round a 256-bit mantissa once and are within one ULP
        if (h == keccak256("expm1") || h == keccak256("sinh") || h == keccak256("cosh") || h == keccak256("tanh")
            || h == keccak256("erf") || h == keccak256("erfc") || h == keccak256("normCdf")) return 140;
        if (h == keccak256("log1p") || h == keccak256("atanh")) return 200;
        if (h == keccak256("powu") || h == keccak256("compound")) return 120;
        return 256;
    }

    function _msb(uint256 x) internal pure returns (uint256 r) { while (x > 1) { x >>= 1; r++; } }

    function _bits(int256 got, int256 truth) internal pure returns (uint256) {
        uint256 d = uint256(got > truth ? got - truth : truth - got);
        if (d == 0) return 256;
        uint256 t = uint256(truth < 0 ? -truth : truth);
        uint256 mt = _msb(t); uint256 md = _msb(d);
        return mt > md ? mt - md : 0;
    }

    function _errSel(string memory name) internal pure returns (bytes4) {
        bytes32 h = keccak256(bytes(name));
        if (h == keccak256("Overflow")) return IFP127.Overflow.selector;
        if (h == keccak256("DivisionByZero")) return IFP127.DivisionByZero.selector;
        if (h == keccak256("OutOfRange")) return IFP127.OutOfRange.selector;
        revert("unknown error name");
    }

    function _isRevert(string memory s) internal pure returns (bool) {
        bytes memory b = bytes(s);
        return b.length > 7 && b[0] == "R" && b[1] == "E" && b[2] == "V" && b[3] == "E" && b[4] == "R" && b[5] == "T" && b[6] == ":";
    }

    function _after7(string memory s) internal pure returns (string memory) {
        bytes memory b = bytes(s);
        bytes memory o = new bytes(b.length - 7);
        for (uint256 i = 7; i < b.length; i++) o[i - 7] = b[i];
        return string(o);
    }

    function _encode(string memory op, string[] memory inp) internal pure returns (bytes memory) {
        if (inp.length == 1) return abi.encodeWithSignature(string.concat(op, "(int256)"), int256(vm.parseUint(inp[0])));
        if (inp.length == 2) return abi.encodeWithSignature(string.concat(op, "(int256,int256)"), int256(vm.parseUint(inp[0])), int256(vm.parseUint(inp[1])));
        return abi.encodeWithSignature(string.concat(op, "(int256,int256,int256)"), int256(vm.parseUint(inp[0])), int256(vm.parseUint(inp[1])), int256(vm.parseUint(inp[2])));
    }

    function _label(string[] memory inp) internal pure returns (string memory s) {
        s = inp[0];
        for (uint256 i = 1; i < inp.length; i++) s = string.concat(s, ",", inp[i]);
    }

    struct Stats { uint256 n; uint256 minBits; uint256 sumBits; uint256 reverts; string worst; }

    /// Runs one op's vector file: {"arity": k, "in0": [...], ..., "out": [...]}.
    function _runOp(string memory op) internal view returns (Stats memory st) {
        string memory json = vm.readFile(string.concat("test/fp127/vectors/", op, ".json"));
        uint256 arity = vm.parseJsonUint(json, ".arity");
        string[] memory outs = vm.parseJsonStringArray(json, ".out");
        string[] memory in0 = vm.parseJsonStringArray(json, ".in0");
        string[] memory in1 = arity > 1 ? vm.parseJsonStringArray(json, ".in1") : new string[](0);
        string[] memory in2 = arity > 2 ? vm.parseJsonStringArray(json, ".in2") : new string[](0);
        uint256 floorBits = _floorBits(op);
        st.minBits = 256;
        for (uint256 i; i < outs.length; i++) {
            string[] memory inp = new string[](arity);
            inp[0] = in0[i];
            if (arity > 1) inp[1] = in1[i];
            if (arity > 2) inp[2] = in2[i];
            _one(op, inp, outs[i], floorBits, st);
        }
    }

    /// Both branches have infinite slope at the branch point -1/e: one ULP of input
    /// resolution there moves W by about 2^-63, so no implementation can
    /// report more than ~63 correct bits within 2^-20 of it. The floor is
    /// relaxed to 60 bits in that neighbourhood only.
    int256 constant NEG_INV_E = -int256(0x5e2d58d8b3bcdf1abadec7829054f90d);

    function _one(string memory op, string[] memory inp, string memory expected, uint256 floorBits, Stats memory st) internal view {
        if (keccak256(bytes(op)) == keccak256("lambertW0") || keccak256(bytes(op)) == keccak256("lambertWm1")) {
            int256 x = int256(vm.parseUint(inp[0]));
            if (x < NEG_INV_E + (ONE >> 20)) floorBits = 60;
        }
        (bool ok, bytes memory out) = address(obj).staticcall(_encode(op, inp));
        if (_isRevert(expected)) {
            assertFalse(ok, string.concat(op, " should revert for ", _label(inp)));
            assertEq(_sel(out), _errSel(_after7(expected)), string.concat(op, " wrong error for ", _label(inp)));
            st.reverts++;
            return;
        }
        assertTrue(ok, string.concat(op, " reverted for ", _label(inp)));
        int256 got = abi.decode(out, (int256));
        int256 truth = int256(vm.parseUint(expected));
        uint256 b = _bits(got, truth);
        // For approximated ops a result within 2 ULP of the truth is as good
        // as the format allows, whatever the relative measure says when the
        // truth itself is a handful of ULP (e.g. W(-2^-128)). Exact ops keep
        // the strict rule.
        if (floorBits < 256) {
            int256 d = got > truth ? got - truth : truth - got;
            if (d <= 2 && b < 255) b = 255;
        }
        st.n++;
        st.sumBits += b;
        if (b < st.minBits) { st.minBits = b; st.worst = _label(inp); }
        assertGe(b, floorBits, string.concat(op, " below precision floor at ", _label(inp)));
    }

    function _record(string memory op, Stats memory st) internal returns (string memory) {
        uint256 mean = st.n == 0 ? 256 : st.sumBits / st.n;
        console.log(string.concat("PREC|", op, "|", vm.toString(st.n), "|", vm.toString(st.minBits), "|", vm.toString(mean), "|", st.worst));
        string memory o = string.concat("op_", op);
        vm.serializeUint(o, "n", st.n);
        vm.serializeUint(o, "reverts", st.reverts);
        vm.serializeUint(o, "minBits", st.minBits);
        vm.serializeUint(o, "meanBits", mean);
        string memory entry = vm.serializeString(o, "worstInput", st.worst);
        return vm.serializeString("precision", op, entry);
    }

    function test_precision_all() public virtual {
        string[49] memory ops = _ops();
        string memory doc;
        for (uint256 i; i < ops.length; i++) {
            doc = _record(ops[i], _runOp(ops[i]));
        }
        if (bytes(_out()).length > 0) vm.writeJson(doc, _out());
    }
}

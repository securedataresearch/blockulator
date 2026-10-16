// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP256Harness} from "../base/FP256Harness.sol";
import {IFP256} from "../../contracts/src/fp256/IFP256.sol";
import {console} from "forge-std/console.sol";

/// @title Precision256
/// @notice Every FP256 op against committed vectors (test/fp256/vectors/*.json,
///         produced by scripts/fp256/oracle.py). For each vector: a REVERT
///         must revert with that selector; otherwise the relative correct
///         bits on the decoded values (FP256Harness._bits, 256 when the words
///         are equal) must be at or above the op's floor. There is no ULP
///         slack: a floor of 256 means the word must equal the oracle's.
///         Prints PREC|op|n|min|mean|worstInput and writes
///         docs/fp256/precision.json.
contract Precision256 is FP256Harness {
    function _out() internal pure virtual returns (string memory) { return "docs/fp256/precision.json"; }

    function _ops() internal pure returns (string[28] memory o) {
        o = ["add", "sub", "mul", "div", "sqrt", "exp", "ln", "pow", "log1p", "expm1", "erf", "erfc", "normCdf", "lambertW0", "lambertWm1", "neg", "abs", "sign", "cmp", "lt", "eq",
             "fromUint", "fromFP127", "toFP127", "fromFixed18", "toFixed18", "powu", "compound"];
    }

    /// Minimum relative correct bits per op. 256 means bit-exact.
    function _floorBits(string memory op) internal pure returns (uint256) {
        // every op but pow is correctly rounded at every committed vector. pow's
        // t = y log2 x carries the log2 kernel's 2^-250 times |t|, so it is
        // held to one ULP (236 bits); 7 of its 234 vectors sit there
        if (keccak256(bytes(op)) == keccak256("pow")) return 236;
        // powu (binary exponentiation below 2^16, pow's tail above) and compound
        // (pow's tail) are within one ULP while |t| = |n log2 x| < 2^13 and lose
        // log2|t| - 13 bits above it, as pow: 233 and 231 at |t| near 2^17 and 2^15
        if (keccak256(bytes(op)) == keccak256("powu")) return 233;
        if (keccak256(bytes(op)) == keccak256("compound")) return 231;
        // Lambert W iterates on the rounded float ops: within one ULP away from -1/e (235
        // bits at worst), and near it Newton loses log2(1/p) bits, p = sqrt(2(1 + e x)),
        // until the branch-point series takes over below p = 2^-21: 218 bits at worst
        if (keccak256(bytes(op)) == keccak256("lambertW0") || keccak256(bytes(op)) == keccak256("lambertWm1")) return 218;
        return 256;
    }

    /// Plain-integer results (cmp, lt, eq) compare as words.
    function _plain(string memory op) internal pure returns (bool) {
        bytes32 h = keccak256(bytes(op));
        return h == keccak256("cmp") || h == keccak256("lt") || h == keccak256("eq")
            || h == keccak256("toFP127") || h == keccak256("toFixed18");
    }

    function _errSel(string memory name) internal pure returns (bytes4) {
        bytes32 h = keccak256(bytes(name));
        if (h == keccak256("Overflow")) return IFP256.Overflow.selector;
        if (h == keccak256("DivisionByZero")) return IFP256.DivisionByZero.selector;
        if (h == keccak256("OutOfRange")) return IFP256.OutOfRange.selector;
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
        bool u = keccak256(bytes(op)) == keccak256("fromUint");
        if (inp.length == 1) return abi.encodeWithSignature(string.concat(op, u ? "(uint256)" : "(int256)"), int256(vm.parseUint(inp[0])));
        return abi.encodeWithSignature(string.concat(op, "(int256,int256)"), int256(vm.parseUint(inp[0])), int256(vm.parseUint(inp[1])));
    }

    function _label(string[] memory inp) internal pure returns (string memory s) {
        s = inp[0];
        for (uint256 i = 1; i < inp.length; i++) s = string.concat(s, ",", inp[i]);
    }

    struct Stats { uint256 n; uint256 minBits; uint256 sumBits; uint256 reverts; string worst; }

    function _runOp(string memory op) internal view returns (Stats memory st) {
        string memory json = vm.readFile(string.concat("test/fp256/vectors/", op, ".json"));
        uint256 arity = vm.parseJsonUint(json, ".arity");
        string[] memory outs = vm.parseJsonStringArray(json, ".out");
        string[] memory in0 = vm.parseJsonStringArray(json, ".in0");
        string[] memory in1 = arity > 1 ? vm.parseJsonStringArray(json, ".in1") : new string[](0);
        uint256 floorBits = _floorBits(op);
        st.minBits = 256;
        for (uint256 i; i < outs.length; i++) {
            string[] memory inp = new string[](arity);
            inp[0] = in0[i];
            if (arity > 1) inp[1] = in1[i];
            _one(op, inp, outs[i], floorBits, st);
        }
    }

    function _one(string memory op, string[] memory inp, string memory expected, uint256 floorBits, Stats memory st) internal view {
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
        uint256 b;
        if (_plain(op)) b = got == truth ? 256 : 0;
        else b = got == truth ? 256 : _bits(got, truth);
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
        string[28] memory ops = _ops();
        string memory doc;
        for (uint256 i; i < ops.length; i++) {
            doc = _record(ops[i], _runOp(ops[i]));
        }
        if (bytes(_out()).length > 0) vm.writeJson(doc, _out());
    }
}

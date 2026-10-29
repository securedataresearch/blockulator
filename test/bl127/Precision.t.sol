// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {BL127Harness} from "../base/BL127Harness.sol";
import {IBL127} from "../../contracts/src/bl127/IBL127.sol";
import {console} from "forge-std/console.sol";

/// @title Precision
/// @notice Every op against committed mpmath vectors (test/bl127/vectors/*.json,
///         produced by scripts/bl127/oracle.py). No ffi at test time.
///
/// Each vector holds the inputs, a reference word `out` and `t`, the real
/// truth's offset from `out` in units of 2^-64 ULP. If the oracle says
/// REVERT:<Error>, the Yul must revert with that selector. Otherwise the error
/// is the true distance |got - truth|, measured to 2^-64 ULP, and it must be
/// within the op's rounding contract (_contract): 0 for an exact op, one ULP
/// for a directed one (floor, ceil, trunc), half an ULP for a nearest one,
/// all at the 2^-64 ULP resolution of t. Per op the test records the vectors, the reverts, the largest
/// error, how many results are the nearest word, and the fewest relative
/// correct bits over results of magnitude 1 or more; PREC| lines and
/// docs/bl127/precision.json carry them.
contract Precision is BL127Harness {
    /// Where the per-op stats are written; empty disables the write.
    function _out() internal pure virtual returns (string memory) { return "docs/bl127/precision.json"; }

    uint256 constant ULP = 1 << 64;          // one ULP in the error's units
    uint256 constant HALF = 1 << 63;

    function _ops() internal pure returns (string[53] memory o) {
        o = [
            "add", "sub", "mul", "mulDown", "mulUp", "div", "divDown", "divUp",
            "fromFixed18", "toFixed18", "toFixed18Down", "toFixed18Up",
            "exp", "exp2", "exp10", "ln", "log2", "log10", "log2Up",
            "sqrt", "cbrt", "pow", "inv", "abs", "neg", "sign", "min", "max", "clamp", "avg",
            "zeroFloorSub", "dist", "lerp", "floor", "ceil", "frac", "round", "factorial",
            "hypot", "gavg", "lambertW0", "lambertWm1",
            "powu", "compound", "log1p", "expm1", "sinh", "cosh", "tanh", "atanh", "erf", "erfc", "normCdf"
        ];
    }

    function _is(bytes32 h, string memory a) internal pure returns (bool) { return h == keccak256(bytes(a)); }

    /// The rounding each op promises and the largest error, in 2^-64 ULP, that
    /// promise allows against the real truth.
    function _contract(string memory op) internal pure returns (string memory label, uint256 bound) {
        bytes32 h = keccak256(bytes(op));
        if (_is(h, "mul") || _is(h, "mulDown") || _is(h, "divDown") || _is(h, "toFixed18") || _is(h, "toFixed18Down")
            || _is(h, "sqrt") || _is(h, "avg") || _is(h, "lerp")) return ("floor", ULP);
        if (_is(h, "mulUp") || _is(h, "divUp") || _is(h, "toFixed18Up")) return ("ceil", ULP);
        if (_is(h, "div") || _is(h, "inv") || _is(h, "fromFixed18")) return ("trunc", ULP);
        // gavg and hypot (3.0): the root of the exact product or sum of
        // squares, rounded once; up to v8 the floored root of a floored value
        if (_is(h, "hypot") || _is(h, "gavg")) return ("nearest", HALF);
        if (_is(h, "exp") || _is(h, "exp2") || _is(h, "exp10") || _is(h, "ln") || _is(h, "log2") || _is(h, "log10")
            || _is(h, "cbrt") || _is(h, "pow") || _is(h, "lambertW0") || _is(h, "lambertWm1") || _is(h, "powu")
            || _is(h, "compound") || _is(h, "log1p") || _is(h, "expm1") || _is(h, "sinh") || _is(h, "cosh")
            || _is(h, "tanh") || _is(h, "atanh") || _is(h, "erf") || _is(h, "erfc") || _is(h, "normCdf")) {
            return ("nearest", HALF);
        }
        return ("exact", 0);
    }

    function _msb(uint256 x) internal pure returns (uint256 r) { while (x > 1) { x >>= 1; r++; } }

    function _errSel(string memory name) internal pure returns (bytes4) {
        bytes32 h = keccak256(bytes(name));
        if (h == keccak256("Overflow")) return IBL127.Overflow.selector;
        if (h == keccak256("DivisionByZero")) return IBL127.DivisionByZero.selector;
        if (h == keccak256("OutOfRange")) return IBL127.OutOfRange.selector;
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

    /// |got - truth| in 2^-64 ULP, where truth = out + t 2^-64; saturates at
    /// 2^255 when got is absurdly far from out.
    function _err(int256 got, int256 out, int256 t) internal pure returns (uint256) {
        uint256 ud;
        unchecked { ud = got >= out ? uint256(got) - uint256(out) : uint256(out) - uint256(got); }
        if (ud >= 1 << 180) return 1 << 255;
        int256 d = int256(ud << 64);
        if (got < out) d = -d;
        d -= t;
        return uint256(d < 0 ? -d : d);
    }

    struct Stats {
        uint256 n; uint256 reverts; uint256 maxErr; uint256 nearest;
        uint256 minBits; uint256 sumBits; uint256 nBits; string worst; uint256 bound;
    }

    struct Vec { string[] outs; string[] ts; string[] in0; string[] in1; string[] in2; uint256 arity; }

    function _load(string memory op) internal view returns (Vec memory v) {
        string memory json = vm.readFile(string.concat("test/bl127/vectors/", op, ".json"));
        v.arity = vm.parseJsonUint(json, ".arity");
        v.outs = vm.parseJsonStringArray(json, ".out");
        v.ts = vm.parseJsonStringArray(json, ".t");
        v.in0 = vm.parseJsonStringArray(json, ".in0");
        v.in1 = v.arity > 1 ? vm.parseJsonStringArray(json, ".in1") : new string[](0);
        v.in2 = v.arity > 2 ? vm.parseJsonStringArray(json, ".in2") : new string[](0);
    }

    /// Runs one op's vector file: {"arity": k, "in0": [...], ..., "out": [...], "t": [...]}.
    function _runOp(string memory op) internal view returns (Stats memory st) {
        Vec memory v = _load(op);
        (, st.bound) = _contract(op);
        st.minBits = 256;
        for (uint256 i; i < v.outs.length; i++) {
            string[] memory inp = new string[](v.arity);
            inp[0] = v.in0[i];
            if (v.arity > 1) inp[1] = v.in1[i];
            if (v.arity > 2) inp[2] = v.in2[i];
            _one(op, inp, v.outs[i], vm.parseInt(v.ts[i]), st);
        }
    }

    function _one(string memory op, string[] memory inp, string memory expected, int256 t, Stats memory st) internal view {
        (bool ok, bytes memory out) = _objFor(op).staticcall(_encode(op, inp));
        if (_isRevert(expected)) {
            assertFalse(ok, string.concat(op, " should revert for ", _label(inp)));
            assertEq(_sel(out), _errSel(_after7(expected)), string.concat(op, " wrong error for ", _label(inp)));
            st.reverts++;
            return;
        }
        assertTrue(ok, string.concat(op, " reverted for ", _label(inp)));
        int256 got = abi.decode(out, (int256));
        int256 ref = int256(vm.parseUint(expected));
        uint256 e = _err(got, ref, t);
        st.n++;
        if (e <= HALF) st.nearest++;
        if (e > st.maxErr) {
            st.maxErr = e;
            st.worst = _label(inp);
        }
        // relative correct bits over results of magnitude 1 or more
        uint256 a;
        unchecked { a = ref < 0 ? uint256(-ref) : uint256(ref); }
        if (a >= uint256(ONE)) {
            uint256 b = 256;
            if (e > 0) {
                uint256 mt = _msb(a) + 64;
                uint256 md = _msb(e);
                b = mt > md ? mt - md : 0;
            }
            st.nBits++;
            st.sumBits += b;
            if (b < st.minBits) st.minBits = b;
        }
        assertLe(e, st.bound, string.concat(op, " outside its rounding contract at ", _label(inp)));
    }

    function _record(string memory op, Stats memory st) internal returns (string memory) {
        (string memory label,) = _contract(op);
        uint256 mean = st.nBits == 0 ? 256 : st.sumBits / st.nBits;
        console.log(string.concat("PREC|", op, "|", vm.toString(st.n), "|", _ulpString(st.maxErr), "|",
            vm.toString(st.nearest), "|", vm.toString(st.minBits), "|", st.worst));
        string memory o = string.concat("op_", op);
        vm.serializeString(o, "rounding", label);
        vm.serializeUint(o, "n", st.n);
        vm.serializeUint(o, "reverts", st.reverts);
        vm.serializeString(o, "maxErrUlp", _ulpString(st.maxErr));
        vm.serializeUint(o, "nearest", st.nearest);
        vm.serializeUint(o, "minBits", st.minBits);
        vm.serializeUint(o, "meanBits", mean);
        string memory entry = vm.serializeString(o, "worstInput", st.worst);
        return vm.serializeString("precision", op, entry);
    }

    /// An error in 2^-64 ULP as a decimal ULP count with four places.
    function _ulpString(uint256 e) internal pure returns (string memory) {
        if (e >= 1 << 200) return "huge";
        uint256 q = (e * 10000 + (ULP >> 1)) >> 64;
        string memory f = vm.toString(q % 10000);
        while (bytes(f).length < 4) f = string.concat("0", f);
        return string.concat(vm.toString(q / 10000), ".", f);
    }

    function test_precision_all() public virtual {
        string[53] memory ops = _ops();
        string memory doc;
        for (uint256 i; i < ops.length; i++) {
            doc = _record(ops[i], _runOp(ops[i]));
        }
        if (bytes(_out()).length > 0) vm.writeJson(doc, _out());
    }
}

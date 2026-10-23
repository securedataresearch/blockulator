// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import "forge-std/Test.sol";
import {LibUser} from "../base/FP127Harness.sol";
import {LibUser256} from "../base/FP256Harness.sol";

/// @title ObjectsEqLib
/// @notice Every deployed object returns exactly what its inline library
///         returns, for every export of both libraries, on inputs aimed at
///         the leading-bit count (msb, on CLZ). The exports come from each
///         library's ops.json (name, selector, arity, object), so nothing here
///         names an op or an object: a re-layout of the objects needs no edit.
///
///         For each export the object (out/<Object>.yul) and the library
///         (behind LibUser / LibUser256) must give the same success flag and
///         the same return or revert bytes. Each fuzz run calls every export
///         once, so N runs are N inputs per op. The inputs: raw words, tiny
///         values, 2^k and its neighbours, all-ones masks, values across the
///         scales near one, the ends of FP256's exponent range, small integers,
///         exact powers of two in FP256, and a second argument a few units from
///         the first (or from its negation), so add and sub cancel. The sweeps
///         walk 2^k - 1, 2^k and 2^k + 1 for every k through every argument.
///
///         FP_REF_DIR=<dir under out/> adds a third implementation: the objects
///         from <dir><Object>.yul/<Object>.json, e.g. a previous release's
///         artifacts, which must then return the same bytes too.
contract ObjectsEqLib is Test {
    struct Op {
        string name;
        bytes4 sel;
        uint256 arity;
        address obj;
        address ref;   // zero unless FP_REF_DIR is set
    }

    /// The two libraries: 0 is FP127, 1 is FP256.
    Op[][2] internal ops;
    address[2] internal lib;
    mapping(bytes32 => address) internal deployed;

    uint256 internal constant BIAS = 0x3ffff;
    uint256 internal constant FRAC = (uint256(1) << 236) - 1;
    uint256 internal constant SIGN = uint256(1) << 255;
    uint256 internal constant ONE127 = uint256(1) << 128;
    uint256 internal constant ONE256 = BIAS << 236;

    function setUp() public {
        lib[0] = address(new LibUser());
        lib[1] = address(new LibUser256());
        string memory ref = vm.envOr("FP_REF_DIR", string(""));
        _load(0, "contracts/src/fp127/ops.json", "FP127", ref);
        _load(1, "contracts/src/fp256/ops.json", "FP256", ref);
    }

    function _load(uint256 l, string memory path, string memory single, string memory ref) internal {
        string memory json = vm.readFile(path);
        for (uint256 i; vm.keyExistsJson(json, _at(i, "")); i++) {
            string memory o =
                vm.keyExistsJson(json, _at(i, ".object")) ? vm.parseJsonString(json, _at(i, ".object")) : single;
            ops[l].push(Op(vm.parseJsonString(json, _at(i, ".name")),
                bytes4(vm.parseBytes32(string.concat(vm.parseJsonString(json, _at(i, ".selector")), "00000000000000000000000000000000000000000000000000000000"))),
                vm.parseJsonStringArray(json, _at(i, ".inputs")).length,
                _object(string.concat("out/", o, ".yul/", o, ".json")),
                bytes(ref).length == 0 ? address(0) : _object(string.concat(ref, o, ".yul/", o, ".json"))));
        }
    }

    function _at(uint256 i, string memory key) internal pure returns (string memory) {
        return string.concat(".ops[", vm.toString(i), "]", key);
    }

    function _object(string memory artifact) internal returns (address d) {
        bytes32 k = keccak256(bytes(artifact));
        d = deployed[k];
        if (d != address(0)) return d;
        bytes memory initCode = vm.parseJsonBytes(vm.readFile(artifact), ".bytecode.object");
        assembly ("memory-safe") {
            d := create(0, add(initCode, 0x20), mload(initCode))
        }
        require(d != address(0), string.concat("deploy failed: ", artifact));
        deployed[k] = d;
    }

    function _data(Op memory op, uint256 a, uint256 b, uint256 c) internal pure returns (bytes memory) {
        if (op.arity == 1) return abi.encodePacked(op.sel, a);
        if (op.arity == 2) return abi.encodePacked(op.sel, a, b);
        return abi.encodePacked(op.sel, a, b, c);
    }

    function _args(uint256 a, uint256 b, uint256 c) internal pure returns (string memory) {
        return string.concat("(", vm.toString(bytes32(a)), ", ", vm.toString(bytes32(b)), ", ", vm.toString(bytes32(c)), ")");
    }

    function _check(uint256 l, Op memory op, uint256 a, uint256 b, uint256 c) internal view {
        bytes memory d = _data(op, a, b, c);
        (bool ok1, bytes memory r1) = op.obj.staticcall(d);
        (bool ok2, bytes memory r2) = lib[l].staticcall(d);
        if (ok1 != ok2 || keccak256(r1) != keccak256(r2)) {
            revert(string.concat(op.name, ": object differs from the library at ", _args(a, b, c),
                " obj ", vm.toString(r1), " lib ", vm.toString(r2)));
        }
        if (op.ref != address(0)) {
            (bool ok3, bytes memory r3) = op.ref.staticcall(d);
            if (ok1 != ok3 || keccak256(r1) != keccak256(r3)) {
                revert(string.concat(op.name, ": object differs from FP_REF_DIR's at ", _args(a, b, c),
                    " obj ", vm.toString(r1), " ref ", vm.toString(r3)));
            }
        }
    }

    function _msb(uint256 x) internal pure returns (uint256 r) {
        while (x > 1) { x >>= 1; r++; }
    }

    /// One argument from the seed r in the given mode (0..7), for library l.
    function _shape(uint256 l, uint256 r, uint256 mode) internal pure returns (uint256 w) {
        unchecked {
            uint256 k = r >> 248;
            uint256 r2 = uint256(keccak256(abi.encode(r)));
            bool neg = r2 & 1 == 1;
            mode %= 8;
            if (mode == 0) return r;
            if (mode == 1) w = r >> k;                                         // tiny
            else if (mode == 2) w = (uint256(1) << k) + ((r2 >> 8) % 9) - 4;   // 2^k + [-4, 4]
            else if (mode == 3) w = (uint256(1) << k) - 1;                     // all ones
            else if (l == 0) {
                if (mode == 4) w = uint256(int256(r) >> (64 + k % 190));               // every scale
                else if (mode == 5) w = ONE127 + uint256(int256(r) >> (100 + k % 150)); // near one
                else if (mode == 6) w = uint256((int256(k % 64) - 32) << 128);         // small integers
                else w = r & ((uint256(1) << k) - 1);                                  // k random bits
            } else {
                uint256 e;
                uint256 f = r & FRAC;
                if (mode == 4) e = BIAS + k - 128;                                     // near one
                else if (mode == 5) e = k % 2 == 0 ? k >> 3 : 0x7ffff - (k >> 3);     // the exponent's ends
                else if (mode == 6) {                                                  // small integers
                    uint256 n = k % 64 + 1;
                    uint256 m = _msb(n);
                    e = BIAS + m;
                    f = (n << (236 - m)) & FRAC;
                } else {                                                               // 2^j, a few low bits
                    e = BIAS + k - 128;
                    f = r2 >> 253;
                }
                w = (e << 236) | f;
                return neg ? w ^ SIGN : w;
            }
            if (neg) w = 0 - w;
        }
    }

    function _run(uint256 l, uint256 s0, uint256 s1, uint256 s2, uint256 m, uint256 parity) internal view {
        uint256 a = _shape(l, s0, m);
        uint256 b = _shape(l, s1, m >> 3);
        uint256 c = _shape(l, s2, m >> 6);
        if ((m >> 9) % 4 == 0) {
            // b a few units from a (or from -a): add and sub cancel
            uint256 delta = s1 % (uint256(1) << ((s1 >> 248) % 72));
            unchecked {
                b = (m >> 11) & 1 == 1 ? a - delta : a + delta;
                if ((m >> 12) & 1 == 1) b = l == 0 ? 0 - b : b ^ SIGN;
            }
        }
        Op[] storage list = ops[l];
        for (uint256 i; i < list.length; i++) {
            if (parity < 2 && i % 2 != parity) continue;
            _check(l, list[i], a, b, c);
        }
    }

    /// forge-config: default.fuzz.runs = 10000
    function testFuzz_fp127(uint256 s0, uint256 s1, uint256 s2, uint256 m) public view {
        _run(0, s0, s1, s2, m, 2);
    }

    // FP256's exports in two halves, so the two run in parallel
    /// forge-config: default.fuzz.runs = 10000
    function testFuzz_fp256_even(uint256 s0, uint256 s1, uint256 s2, uint256 m) public view {
        _run(1, s0, s1, s2, m, 0);
    }

    /// forge-config: default.fuzz.runs = 10000
    function testFuzz_fp256_odd(uint256 s0, uint256 s1, uint256 s2, uint256 m) public view {
        _run(1, s0, s1, s2, m, 1);
    }

    /// 2^k - 1, 2^k and 2^k + 1 for every k in every argument position, the
    /// others one.
    function _sweep(uint256 l) internal view {
        uint256 one = l == 0 ? ONE127 : ONE256;
        Op[] storage list = ops[l];
        for (uint256 i; i < list.length; i++) {
            Op memory op = list[i];
            for (uint256 k; k < 256; k++) {
                for (uint256 d; d < 3; d++) {
                    uint256 x;
                    unchecked { x = (uint256(1) << k) + d - 1; }
                    _check(l, op, x, one, one);
                    if (op.arity > 1) _check(l, op, one, x, one);
                    if (op.arity > 2) _check(l, op, one, one, x);
                    _check(l, op, x, x >> 1, x);
                }
            }
        }
    }

    function test_powersOfTwo_fp127() public view {
        _sweep(0);
    }

    function test_powersOfTwo_fp256() public view {
        _sweep(1);
    }

    /// Both libraries' exports loaded, each with a deployed object.
    function test_everyExport() public view {
        for (uint256 l; l < 2; l++) {
            assertGt(ops[l].length, 0, "exports");
            for (uint256 i; i < ops[l].length; i++) {
                assertGt(ops[l][i].obj.code.length, 0, "object deployed");
            }
        }
    }
}

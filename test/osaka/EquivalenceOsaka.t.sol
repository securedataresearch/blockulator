// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {OsakaBase} from "./OsakaBase.sol";

/// @title EquivalenceOsaka
/// @notice The osaka build returns exactly what the shanghai build returns.
///         For every export of both libraries (from ops.json), on the same
///         inputs, three implementations must give the same success flag and
///         the same return or revert bytes:
///           sh   the shanghai object (out/<Object>.yul, solc 0.8.24)
///           os   the osaka object (out/osaka/<Object>.yul, solc 0.8.38, msb on CLZ)
///           lib  the osaka inline library (osaka/<Lib>Osaka.sol) behind LibUserOsaka*
///         Each fuzz run calls every export of the library once, so N runs
///         are N inputs per op. The inputs are shaped where a leading-bit
///         count matters: raw words, tiny values, powers of two and their
///         neighbours, all-ones masks, values across the scales near one, the
///         ends of FP256's exponent range, small integers, exact powers of two
///         in FP256, and a second argument a few units from the first (or its
///         negation), so add and sub cancel. The sweeps then walk 2^k - 1, 2^k
///         and 2^k + 1 for every k through every argument position.
contract EquivalenceOsaka is OsakaBase {
    function _check(uint256 lib, Op memory op, uint256 a, uint256 b, uint256 c) internal view {
        bytes memory d = _data(op, a, b, c);
        (bool ok1, bytes memory r1) = op.sh.staticcall(d);
        (bool ok2, bytes memory r2) = op.os.staticcall(d);
        (bool ok3, bytes memory r3) = libOsaka[lib].staticcall(d);
        if (ok1 != ok2 || keccak256(r1) != keccak256(r2)) {
            revert(string.concat(op.name, ": osaka object differs from shanghai at ", _args(a, b, c),
                " sh ", vm.toString(r1), " os ", vm.toString(r2)));
        }
        if (ok1 != ok3 || keccak256(r1) != keccak256(r3)) {
            revert(string.concat(op.name, ": osaka inline library differs from the objects at ", _args(a, b, c),
                " sh ", vm.toString(r1), " lib ", vm.toString(r3)));
        }
    }

    function _args(uint256 a, uint256 b, uint256 c) internal pure returns (string memory) {
        return string.concat("(", vm.toString(bytes32(a)), ", ", vm.toString(bytes32(b)), ", ", vm.toString(bytes32(c)), ")");
    }

    function _run(uint256 lib, uint256 s0, uint256 s1, uint256 s2, uint256 m, uint256 parity) internal view {
        uint256 a = _shape(lib, s0, m);
        uint256 b = _shape(lib, s1, m >> 3);
        uint256 c = _shape(lib, s2, m >> 6);
        if ((m >> 9) % 4 == 0) {
            // b a few units from a (or from -a): add and sub cancel
            uint256 delta = s1 % (uint256(1) << ((s1 >> 248) % 72));
            unchecked {
                b = (m >> 11) & 1 == 1 ? a - delta : a + delta;
                if ((m >> 12) & 1 == 1) b = lib == 0 ? 0 - b : b ^ SIGN;
            }
        }
        Op[] storage list = ops[lib];
        for (uint256 i; i < list.length; i++) {
            if (parity < 2 && i % 2 != parity) continue;
            _check(lib, list[i], a, b, c);
        }
    }

    function testFuzz_fp127(uint256 s0, uint256 s1, uint256 s2, uint256 m) public view {
        _run(0, s0, s1, s2, m, 2);
    }

    // FP256's 67 exports in two halves, so the two run in parallel
    function testFuzz_fp256_even(uint256 s0, uint256 s1, uint256 s2, uint256 m) public view {
        _run(1, s0, s1, s2, m, 0);
    }

    function testFuzz_fp256_odd(uint256 s0, uint256 s1, uint256 s2, uint256 m) public view {
        _run(1, s0, s1, s2, m, 1);
    }

    /// 2^k - 1, 2^k and 2^k + 1 for every k in every argument position, the
    /// others one.
    function _sweep(uint256 lib) internal view {
        uint256 one = lib == 0 ? ONE127 : ONE256;
        Op[] storage list = ops[lib];
        for (uint256 i; i < list.length; i++) {
            Op memory op = list[i];
            for (uint256 k; k < 256; k++) {
                for (uint256 d; d < 3; d++) {
                    uint256 x;
                    unchecked { x = (uint256(1) << k) + d - 1; }
                    _check(lib, op, x, one, one);
                    if (op.arity > 1) _check(lib, op, one, x, one);
                    if (op.arity > 2) _check(lib, op, one, one, x);
                    _check(lib, op, x, x >> 1, x);
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

    /// Both libraries' exports loaded, each with a shanghai and an osaka object.
    function test_everyExport() public view {
        assertGt(ops[0].length, 0, "FP127 exports");
        assertGt(ops[1].length, 0, "FP256 exports");
        for (uint256 lib; lib < 2; lib++) {
            for (uint256 i; i < ops[lib].length; i++) {
                assertTrue(ops[lib][i].sh != ops[lib][i].os, "two builds");
                assertGt(ops[lib][i].os.code.length, 0, "osaka object deployed");
            }
        }
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Test} from "forge-std/Test.sol";
import {ImportDemoLib} from "./imports/ImportDemoLib.sol";
import {LibUser19} from "../base/FP19Harness.sol";

contract ImportDemoUser {
    function expm1(int256 x) external pure returns (int256) { return ImportDemoLib.expm1(x); }
    function wexpm1(uint256 rh, uint256 rl) external pure returns (uint256, uint256) { return ImportDemoLib.wexpm1(rh, rl); }
    function rbad127(uint256 v, uint256 g, uint256 err) external pure returns (uint256) { return ImportDemoLib.rbad127(v, g, err); }
}

/// @title Imports
/// @notice scripts/fp127/gen.py's import line, demonstrated: ImportDemoLib
///         (test/fp127/imports/, generated from ImportDemo.yul.src) calls
///         FP19.yul.src's wexpm1 and its whole expm1 export through the line
///         "import fp19 as w19: wexpm1, fp19_expm1", every function of their
///         closures renamed w19_<name>. The renamed expm1 must return
///         FP19Lib.expm1's word, and revert with its data, on every input;
///         the renamed wexpm1 must be within its stated 2^-503 of e^r - 1
///         (mpmath at 320 digits, floored at 2^-510); and FP127.yul.src's
///         rbad127, imported as f127_rbad127, must say exactly when a value
///         within err of v rounds to another word than v (to nearest, ties
///         up, with g guard bits).
contract Imports is Test {
    ImportDemoUser demo;
    LibUser19 fp19;

    uint256 constant BIAS = 0x3ffff;

    function setUp() public {
        demo = new ImportDemoUser();
        fp19 = new LibUser19();
    }

    function _same(int256 x) internal view {
        (bool ok1, bytes memory r1) = address(demo).staticcall(abi.encodeCall(ImportDemoUser.expm1, (x)));
        (bool ok2, bytes memory r2) = address(fp19).staticcall(abi.encodeCall(LibUser19.expm1, (x)));
        assertEq(ok1, ok2, "ok flag");
        assertEq(keccak256(r1), keccak256(r2), "result or revert data");
    }

    function testFuzz_expm1_word(int256 x) public view {
        _same(x);
    }

    /// FP19 words of every exponent expm1 computes on, both signs: the fast
    /// path, its two-word second stage and the ends of the domain.
    function testFuzz_expm1_shaped(uint256 r, uint16 e, bool neg) public view {
        uint256 w = ((BIAS + (uint256(e) % 320) - 300) << 236) | (r & ((uint256(1) << 236) - 1));
        _same(int256(neg ? w | (uint256(1) << 255) : w));
    }

    /// |wexpm1(r) - floor((e^r - 1) 2^510)| < 2^7 units of 2^-510, the kernel's
    /// 2^-503; the truths from mpmath at 320 digits.
    function _vec(uint256 rh, uint256 rl, uint256 th, uint256 tl) internal view {
        (uint256 eh, uint256 el) = demo.wexpm1(rh, rl);
        uint256 dl;
        uint256 dh;
        unchecked {
            dl = el - tl;
            dh = eh - th - (el < tl ? 1 : 0);
        }
        bool close = (dh == 0 && dl < 128) || (dh == type(uint256).max && dl > type(uint256).max - 128);
        assertTrue(close, string.concat("wexpm1 off at r = ", vm.toString(bytes32(rh)), vm.toString(bytes32(rl))));
    }

    function test_wexpm1_vectors() public view {
        _vec(0x0000000000000000000000000000000000000000000000000000000000000000, 0x0000000000000000000000000000000000000000000000000000000000000001, 0x0000000000000000000000000000000000000000000000000000000000000000, 0x0000000000000000000000000000000000000000000000000000000000000001);
        _vec(0x0000000000000000000000000000000000000000000000000000000000000000, 0x0000000000000100000000000000000000000000000000000000000000000000, 0x0000000000000000000000000000000000000000000000000000000000000000, 0x0000000000000100000000000000000000000000000000000000000000000000);
        _vec(0x0666666666666666666666666666666666666666666666666666666666666666, 0x6666666666666666666666666666666666666666666666666666666666666666, 0x06bb1ecd68034e6be08e302615aac607185f81721d994791bb2eefc9f3c6505b, 0xfcba85d048fc376de9337a547ecf42b361e02982f0de84d213ab69cde3e0839f);
        _vec(0x2000000000000000000000000000000000000000000000000000000000000000, 0x0000000000000000000000000000000000000000000000000000000000000000, 0x2984a638781a6f25cb7fbeadb7ccfe6c7d947c5b04c2d1d67112ff2418d9fcb3, 0x0bbd5c9e6a448b884f9bb6fde5c56645d27b56633d987c8ed70cdd400ad897a4);
        _vec(0x2c5c85fdf473de6af278ece600fcbdabd03cd0c99ca62d8b628345d6e2eabe8a, 0xf9ee1d881b7aeb26156554bed2be86c43b4bab8d704e085109d5ceca445a6e09, 0x3fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        _vec(0x3999999999999999999999999999999999999999999999999999999999999999, 0x9999999999999999999999999999999999999999999999999999999999999999, 0x5d6a232ae3c5dca26d1460113d369d1bd54373183063c9994430c2f261bb41a2, 0x9a9f90d49196e14380218d8b083aaae6dc09f8b683977b7bb601c48e4f59d1de);
        _vec(0x3fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, 0x6df85458a2bb4a9aafdc5620273d3cf1d8b9c583ce2d3695a9e13641146433fb, 0xcc939dce249b3ef97d2fe363630c75d8f681b202aec4617ad3df1ed5d5fd655e);
        _vec(0x2b2f3aef4c97f28b3a0a5295687adef733f9aaa7f0ac05f844a968e807a3577d, 0x060877be191b316dd28fe89f9065a872949b70309fb81994e990bf360b6951b3, 0x3daaeba16e8e08767f879f1638d3040ac470c6485ed768912bccbbc991cfc1ac, 0x281040255c6e1736b98f6b0888a5fa051306c3d76917b51a9a48e0ada39f0f78);
        _vec(0x3c01ff0c1fd271ded3fbfafab4bf861088ae7b2df5fc90b74b3b2e6f500e6e46, 0x0feb15c1f38d41a761a2168c4f603713ec461ee5ef277cb0de8b05afaaff97ff, 0x63731b901ecb9d6d94791ec6b8bc341eb74930407e6cb30e9fd9502ae5ae835d, 0xda0e378842c57a389e668170cb4d1e907f588b0010849acff8a0d174be7d5417);
        _vec(0x26d8e4e8bb8d1c6b2d4d5f9df3717393791f744a058a99ed597ee2b0f9e32ba9, 0x5ececb139795a6babc36daff170356f4ce6908e21b85710060cdd584ec285ffe, 0x356ef2728f57fb2810219af94b88b9fd9996f5aa6a2dea115be8858ecdb55d54, 0x1ddcbcf47e23c1d37d4dd0b5565ec4344b8336ea980a5bb003407719c569cddb);
        _vec(0x00000000000086365ecb7e9d405468d818c40d5b9e2396d7416870e11f2eeb5d, 0x8177e7ec1d8c9896486c8e23b091886f6079d293d88a389a5f610571faaa6f42, 0x00000000000086365ecb7e9dcd0e566a6bc4a894a1a15207d2d368fdff4a8aa9, 0xc825f639782160d9f65c2f6f9178815d63809a8c4582cfc9ad548591a3602c85);
        _vec(0x0000000000000000000000000000000000000000000000000000000000000000, 0x00000000000000000000000000000001344f8c02b9d273b6b7d4777642c268e4, 0x0000000000000000000000000000000000000000000000000000000000000000, 0x00000000000000000000000000000001344f8c02b9d273b6b7d4777642c268e4);
        _vec(0x0000000000000000000000000000000000000000000000000000000000000000, 0x000d381408806234d5e6fc06a92943a8b87c21ba328758016e041c98bfe807ac, 0x0000000000000000000000000000000000000000000000000000000000000000, 0x000d381408806234d5e6fc06a92943a8b87c21ba328758016e041c98bfe807ac);
        _vec(0x0000000000000000000000000000000000000000000000000000000000000000, 0x0000001ed97359db9253bb0acfc8c28eecf2e8efe606d030d13f655c28b12ab3, 0x0000000000000000000000000000000000000000000000000000000000000000, 0x0000001ed97359db9253bb0acfc8c28eecf2e8efe606d030d13f655c28b12ab3);
    }

    /// The word a value V carried with g guard bits rounds to under FP127's
    /// rule: floor(V 2^-g + 1/2), ties up.
    function _word(uint256 V, uint256 g) internal pure returns (uint256) {
        return g == 256 ? (V >= (uint256(1) << 255) ? 1 : 0) : (V + (uint256(1) << (g - 1))) >> g;
    }

    /// rbad127 against its definition: bad exactly when some V in
    /// [v - err, v + err] rounds to another word than v, which (words rise
    /// with V) is when one end of the interval does.
    function testFuzz_rbad127(uint256 v, uint256 g, uint256 err, uint8 shape) public view {
        g = bound(g, 1, 256);
        v = bound(v, 0, (uint256(1) << 254) - 1);
        // err: tiny, about the guard bits' scale, or across half a step
        if (shape % 3 == 0) err = bound(err, 0, 4);
        else if (shape % 3 == 1) err = bound(err, 0, g > 2 ? uint256(1) << (g - 2) : 2);
        else err = bound(err, 0, uint256(1) << (g < 200 ? g : 200));
        // v near a midpoint of its step, the case the test exists for
        if (shape >= 128 && g < 254) v = ((v >> g) << g) + (uint256(1) << (g - 1)) + (err % 7) - 3;
        if (v < err) v = err;
        uint256 w = _word(v, g);
        bool bad = _word(v - err, g) != w || _word(v + err, g) != w;
        assertEq(demo.rbad127(v, g, err), bad ? 1 : 0, "rbad127");
    }

    function test_rbad127_ties() public view {
        // exactly on the midpoint, exact: the tie, which rounds up, is not bad
        assertEq(demo.rbad127(0x8000000000000000, 64, 0), 0);
        // on the midpoint with any error: bad
        assertEq(demo.rbad127(0x8000000000000000, 64, 1), 1);
        // one below it, exact or one unit off (V may reach it): good, bad
        assertEq(demo.rbad127(0x7fffffffffffffff, 64, 0), 0);
        assertEq(demo.rbad127(0x7fffffffffffffff, 64, 1), 1);
        // one above it: one unit off may land on it, which still rounds up
        assertEq(demo.rbad127(0x8000000000000001, 64, 1), 0);
        assertEq(demo.rbad127(0x8000000000000001, 64, 2), 1);
        // a signed value: the low bits of its two's complement
        assertEq(demo.rbad127(uint256(-int256(0x18000000000000000)), 64, 0), 0);
        assertEq(demo.rbad127(uint256(-int256(0x18000000000000000)), 64, 1), 1);
        // g = 256 (a two-word value's low word) and err reaching half a step
        assertEq(demo.rbad127(uint256(1) << 255, 256, 0), 0);
        assertEq(demo.rbad127(0, 256, uint256(1) << 255), 1);
        assertEq(demo.rbad127(0, 1, 0), 0);
        assertEq(demo.rbad127(1, 1, 0), 0);
        assertEq(demo.rbad127(0, 1, 1), 1);
    }
}

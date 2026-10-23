// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP127Harness} from "../base/FP127Harness.sol";
import {IFP127} from "../../contracts/src/fp127/IFP127.sol";

/// @notice Legacy Huff selectors for the ops ported in the op-port phase.
interface IHuffOps {
    function expRaw(uint256) external pure returns (uint256);
    function exp2Raw(uint256) external pure returns (uint256);
    function lnRaw(uint256) external pure returns (uint256);
    function log2Raw(uint256) external pure returns (uint256);
    function log10Raw(uint256) external pure returns (uint256);
    function exp10Raw(uint256) external pure returns (uint256);
    function sqrtRaw(uint256) external pure returns (uint256);
    function cbrtRaw(uint256) external pure returns (uint256);
    function powRaw(uint256, uint256) external pure returns (uint256);
    function absRaw(uint256) external pure returns (uint256);
    function negRaw(uint256) external pure returns (uint256);
    function invRaw(uint256) external pure returns (uint256);
    function minRaw(uint256, uint256) external pure returns (uint256);
    function maxRaw(uint256, uint256) external pure returns (uint256);
    function clampRaw(uint256, uint256, uint256) external pure returns (uint256);
    function avgRaw(uint256, uint256) external pure returns (uint256);
    function zeroFloorSubRaw(uint256, uint256) external pure returns (uint256);
    function distRaw(uint256, uint256) external pure returns (uint256);
    function gavgRaw(uint256, uint256) external pure returns (uint256);
    function hypotRaw(uint256, uint256) external pure returns (uint256);
    function lerpRaw(uint256, uint256, uint256) external pure returns (uint256);
    function signRaw(uint256) external pure returns (uint256);
    function floorRaw(uint256) external pure returns (uint256);
    function ceilRaw(uint256) external pure returns (uint256);
    function fracRaw(uint256) external pure returns (uint256);
    function roundRaw(uint256) external pure returns (uint256);
    function log2UpRaw(uint256) external pure returns (uint256);
    function factorialRaw(uint256) external pure returns (uint256);
    function lambertW0Raw(uint256) external pure returns (uint256);
}

/// @title EquivalenceOps
/// @notice For every op ported after the arithmetic core: the Yul object and
///         the inline library agree on the full domain, and both agree with
///         the Sepolia Huff bytecode on every input where the Huff computed a
///         defined answer. Named divergence tests record where the Yul now
///         reverts and what the Huff used to return.
contract EquivalenceOps is FP127Harness {
    int256 constant B190 = int256(1) << 190;

    function _objLib(bytes memory call, string memory what) internal view {
        _assertSame(_try(address(obj), call), _try(address(lib), call), what);
    }

    /// Yul object must succeed and equal the Huff on a defined input.
    function _objHuff(bytes memory newCall, bytes memory huffCall, string memory what) internal view {
        Res memory o = _try(address(obj), newCall);
        Res memory h = _try(address(huff), huffCall);
        assertTrue(h.ok, string.concat(what, ": huff reverted"));
        assertTrue(o.ok, string.concat(what, ": obj reverted"));
        assertEq(o.value, h.value, string.concat(what, ": obj != huff"));
    }

    function _u(int256 x) internal pure returns (uint256) { return uint256(x); }

    /// The transcendentals now run with 64 guard bits and round to nearest,
    /// where the Huff floored every step: the two agree to the Huff's own
    /// precision, not bit for bit. Both must succeed and the Yul must be
    /// within 2^-100 relative (plus 16 ULP) of the Huff: near a result of
    /// zero the Huff's own floors reach 11 ULPs (ln and log2 at 1 - 2^-128).
    function _objHuffClose(bytes memory newCall, bytes memory huffCall, string memory what) internal view {
        Res memory o = _try(address(obj), newCall);
        Res memory h = _try(address(huff), huffCall);
        assertTrue(h.ok, string.concat(what, ": huff reverted"));
        assertTrue(o.ok, string.concat(what, ": obj reverted"));
        assertLe(_absd(o.value, h.value), (_absd(h.value, 0) >> 100) + 16, string.concat(what, ": obj not within 2^-100 of huff"));
    }

    // ------------------------------------------------------------------
    // Object == library, full domain
    // ------------------------------------------------------------------

    function testFuzz_objEqLib_exp(int256 x) public view { _objLib(abi.encodeCall(IFP127.exp, (x)), "exp"); }
    function testFuzz_objEqLib_exp2(int256 x) public view { _objLib(abi.encodeCall(IFP127.exp2, (x)), "exp2"); }
    function testFuzz_objEqLib_exp10(int256 x) public view { _objLib(abi.encodeCall(IFP127.exp10, (x)), "exp10"); }
    function testFuzz_objEqLib_ln(int256 x) public view { _objLib(abi.encodeCall(IFP127.ln, (x)), "ln"); }
    function testFuzz_objEqLib_log2(int256 x) public view { _objLib(abi.encodeCall(IFP127.log2, (x)), "log2"); }
    function testFuzz_objEqLib_log10(int256 x) public view { _objLib(abi.encodeCall(IFP127.log10, (x)), "log10"); }
    function testFuzz_objEqLib_log2Up(int256 x) public view { _objLib(abi.encodeCall(IFP127.log2Up, (x)), "log2Up"); }
    function testFuzz_objEqLib_sqrt(int256 x) public view { _objLib(abi.encodeCall(IFP127.sqrt, (x)), "sqrt"); }
    function testFuzz_objEqLib_cbrt(int256 x) public view { _objLib(abi.encodeCall(IFP127.cbrt, (x)), "cbrt"); }
    function testFuzz_objEqLib_pow(int256 x, int256 y) public view { _objLib(abi.encodeCall(IFP127.pow, (x, y)), "pow"); }
    function testFuzz_objEqLib_abs(int256 x) public view { _objLib(abi.encodeCall(IFP127.abs, (x)), "abs"); }
    function testFuzz_objEqLib_neg(int256 x) public view { _objLib(abi.encodeCall(IFP127.neg, (x)), "neg"); }
    function testFuzz_objEqLib_inv(int256 x) public view { _objLib(abi.encodeCall(IFP127.inv, (x)), "inv"); }
    function testFuzz_objEqLib_min(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.min, (a, b)), "min"); }
    function testFuzz_objEqLib_max(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.max, (a, b)), "max"); }
    function testFuzz_objEqLib_clamp(int256 x, int256 lo, int256 hi) public view { _objLib(abi.encodeCall(IFP127.clamp, (x, lo, hi)), "clamp"); }
    function testFuzz_objEqLib_avg(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.avg, (a, b)), "avg"); }
    function testFuzz_objEqLib_zeroFloorSub(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.zeroFloorSub, (a, b)), "zeroFloorSub"); }
    function testFuzz_objEqLib_dist(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.dist, (a, b)), "dist"); }
    function testFuzz_objEqLib_gavg(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.gavg, (a, b)), "gavg"); }
    function testFuzz_objEqLib_hypot(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.hypot, (a, b)), "hypot"); }
    function testFuzz_objEqLib_lerp(int256 a, int256 b, int256 t) public view { _objLib(abi.encodeCall(IFP127.lerp, (a, b, t)), "lerp"); }
    function testFuzz_objEqLib_sign(int256 x) public view { _objLib(abi.encodeCall(IFP127.sign, (x)), "sign"); }
    function testFuzz_objEqLib_floor(int256 x) public view { _objLib(abi.encodeCall(IFP127.floor, (x)), "floor"); }
    function testFuzz_objEqLib_ceil(int256 x) public view { _objLib(abi.encodeCall(IFP127.ceil, (x)), "ceil"); }
    function testFuzz_objEqLib_frac(int256 x) public view { _objLib(abi.encodeCall(IFP127.frac, (x)), "frac"); }
    function testFuzz_objEqLib_round(int256 x) public view { _objLib(abi.encodeCall(IFP127.round, (x)), "round"); }
    function testFuzz_objEqLib_factorial(int256 n) public view { _objLib(abi.encodeCall(IFP127.factorial, (n)), "factorial"); }
    function testFuzz_objEqLib_powu(int256 x, int256 n) public view { _objLib(abi.encodeCall(IFP127.powu, (x, n)), "powu"); }
    function testFuzz_objEqLib_compound(int256 r, int256 n) public view { _objLib(abi.encodeCall(IFP127.compound, (r, n)), "compound"); }
    function testFuzz_objEqLib_log1p(int256 x) public view { _objLib(abi.encodeCall(IFP127.log1p, (x)), "log1p"); }
    function testFuzz_objEqLib_expm1(int256 x) public view { _objLib(abi.encodeCall(IFP127.expm1, (x)), "expm1"); }
    function testFuzz_objEqLib_sinh(int256 x) public view { _objLib(abi.encodeCall(IFP127.sinh, (x)), "sinh"); }
    function testFuzz_objEqLib_cosh(int256 x) public view { _objLib(abi.encodeCall(IFP127.cosh, (x)), "cosh"); }
    function testFuzz_objEqLib_tanh(int256 x) public view { _objLib(abi.encodeCall(IFP127.tanh, (x)), "tanh"); }
    function testFuzz_objEqLib_atanh(int256 x) public view { _objLib(abi.encodeCall(IFP127.atanh, (x)), "atanh"); }
    function testFuzz_objEqLib_erf(int256 x) public view { _objLib(abi.encodeCall(IFP127.erf, (x)), "erf"); }
    function testFuzz_objEqLib_erfc(int256 x) public view { _objLib(abi.encodeCall(IFP127.erfc, (x)), "erfc"); }
    // v5: the directed edge ops
    function testFuzz_objEqLib_mulDown(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.mulDown, (a, b)), "mulDown"); }
    function testFuzz_objEqLib_mulUp(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.mulUp, (a, b)), "mulUp"); }
    function testFuzz_objEqLib_divDown(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.divDown, (a, b)), "divDown"); }
    function testFuzz_objEqLib_divUp(int256 a, int256 b) public view { _objLib(abi.encodeCall(IFP127.divUp, (a, b)), "divUp"); }
    function testFuzz_objEqLib_toFixed18Down(int256 x) public view { _objLib(abi.encodeCall(IFP127.toFixed18Down, (x)), "toFixed18Down"); }
    function testFuzz_objEqLib_toFixed18Up(int256 x) public view { _objLib(abi.encodeCall(IFP127.toFixed18Up, (x)), "toFixed18Up"); }
    /// In range, so the fuzzer exercises the result and not only the reverts.
    function testFuzz_objEqLib_directed_inRange(int256 a, int256 b) public view {
        a = bound(a, -B190, B190);
        b = bound(b, -B190, B190);
        _objLib(abi.encodeCall(IFP127.mulUp, (a, b)), "mulUp in range");
        _objLib(abi.encodeCall(IFP127.mulDown, (a, b)), "mulDown in range");
        if (b != 0 && (b > int256(1) << 64 || b < -(int256(1) << 64))) {
            _objLib(abi.encodeCall(IFP127.divUp, (a, b)), "divUp in range");
            _objLib(abi.encodeCall(IFP127.divDown, (a, b)), "divDown in range");
        }
    }
    function testFuzz_objEqLib_normCdf(int256 x) public view { _objLib(abi.encodeCall(IFP127.normCdf, (x)), "normCdf"); }
    function testFuzz_objEqLib_lambertW0(int256 x) public view {
        x = bound(x, -int256(0x5e2d58d8b3bcdf1abadec7829054f90d), int256(1) << 200);
        _objLib(abi.encodeCall(IFP127.lambertW0, (x)), "lambertW0");
    }
    function testFuzz_objEqLib_lambertWm1(int256 x) public view {
        x = bound(x, -int256(0x5e2d58d8b3bcdf1abadec7829054f90d) - 1, 1);
        _objLib(abi.encodeCall(IFP127.lambertWm1, (x)), "lambertWm1");
    }

    // ------------------------------------------------------------------
    // Object == Huff on the Huff's defined domain
    // ------------------------------------------------------------------

    function testFuzz_huff_exp(int256 x) public view {
        x = bound(x, -88 * ONE, 88 * ONE);
        _objHuffClose(abi.encodeCall(IFP127.exp, (x)), abi.encodeCall(IHuffOps.expRaw, (_u(x))), "exp");
    }

    function testFuzz_huff_exp2(int256 x) public view {
        x = bound(x, -128 * ONE, 127 * ONE - 1);
        _objHuffClose(abi.encodeCall(IFP127.exp2, (x)), abi.encodeCall(IHuffOps.exp2Raw, (_u(x))), "exp2");
    }

    function testFuzz_huff_exp10(int256 x) public view {
        x = bound(x, -38 * ONE, 38 * ONE);
        _objHuffClose(abi.encodeCall(IFP127.exp10, (x)), abi.encodeCall(IHuffOps.exp10Raw, (_u(x))), "exp10");
    }

    function testFuzz_huff_ln(int256 x) public view {
        x = bound(x, 1, MAX);
        _objHuffClose(abi.encodeCall(IFP127.ln, (x)), abi.encodeCall(IHuffOps.lnRaw, (_u(x))), "ln");
    }

    function testFuzz_huff_log2(int256 x) public view {
        x = bound(x, 1, MAX);
        _objHuffClose(abi.encodeCall(IFP127.log2, (x)), abi.encodeCall(IHuffOps.log2Raw, (_u(x))), "log2");
    }

    function testFuzz_huff_log10(int256 x) public view {
        x = bound(x, 1, MAX);
        _objHuffClose(abi.encodeCall(IFP127.log10, (x)), abi.encodeCall(IHuffOps.log10Raw, (_u(x))), "log10");
    }

    /// v5 computes ceil(log2 x) exactly from the msb. The Huff (and v4) took
    /// ceil of a rounded log2, which is one low when x sits just above a
    /// power of two and the log2 rounds down onto the integer; there the Yul
    /// is one higher, and right.
    function testFuzz_huff_log2Up(int256 x) public view {
        x = bound(x, 1, MAX);
        Res memory o = _try(address(obj), abi.encodeCall(IFP127.log2Up, (x)));
        Res memory h = _try(address(huff), abi.encodeCall(IHuffOps.log2UpRaw, (_u(x))));
        assertTrue(o.ok && h.ok, "log2Up: both succeed");
        uint256 m;
        for (uint256 t = uint256(x); t > 1; t >>= 1) m++;
        if (o.value == h.value + ONE) {
            // x = 2^m (1 + e) with e below 2^-120: the rounded log2 is m - 128 exactly
            assertLt(uint256(x) - (uint256(1) << m), (uint256(1) << m) >> 120, "log2Up: Huff low only just above a power of two");
        } else {
            assertEq(o.value, h.value, "log2Up: obj != huff");
        }
    }

    function test_divergence_log2Up_above_power_of_two() public view {
        int256 x = (ONE << 64) + 0x5fc97a4a9078;     // 2^64 (1 + 2^-152): log2 rounds to 64
        assertEq(obj.log2Up(x), 65 * ONE);
        assertEq(int256(IHuffOps(address(huff)).log2UpRaw(_u(x))), 64 * ONE);
    }

    function testFuzz_huff_sqrt(int256 x) public view {
        x = bound(x, 0, MAX);
        _objHuff(abi.encodeCall(IFP127.sqrt, (x)), abi.encodeCall(IHuffOps.sqrtRaw, (_u(x))), "sqrt");
    }

    function testFuzz_huff_cbrt(int256 x) public view {
        vm.assume(x != MIN);
        _objHuffClose(abi.encodeCall(IFP127.cbrt, (x)), abi.encodeCall(IHuffOps.cbrtRaw, (_u(x))), "cbrt");
    }

    /// General pow path: 0.001 <= x <= 1000, -8 <= y <= 8, result fits.
    function testFuzz_huff_pow(int256 x, int256 y) public view {
        x = bound(x, ONE / 1000, 1000 * ONE);
        y = bound(y, -8 * ONE, 8 * ONE);
        // the Sepolia bytecode has no shortcuts; keep the fuzzer off them
        vm.assume(x != 2 * ONE && x != 10 * ONE);
        vm.assume(y != ONE && y != 2 * ONE && y != 3 * ONE && y != 4 * ONE && y != ONE / 2 && y != ONE / 4 && y != -ONE);
        _objHuffClose(abi.encodeCall(IFP127.pow, (x, y)), abi.encodeCall(IHuffOps.powRaw, (_u(x), _u(y))), "pow");
    }

    /// Shortcut paths: y in {1, 2, 3, 4, 1/2, 1/4, -1}, x in {2, 10}.
    /// The Sepolia bytecode predates shortcut_constants.huff and runs the
    /// general 2^(y log2 x) path for these, so it is not bit-identical; the
    /// Yul follows the repo source and takes the exact route. Assert the
    /// shortcut equals the direct op and that the Huff is within 2^-100.
    function testFuzz_huff_pow_shortcuts(int256 x, uint8 which) public view {
        x = bound(x, ONE / 1000, 1000 * ONE);
        int256 y;
        int256 direct;
        uint8 k = which % 7;
        if (k == 0) { y = ONE; direct = x; }
        else if (k == 1) { y = 2 * ONE; direct = obj.mul(x, x); }
        else if (k == 2) { y = 3 * ONE; direct = obj.mul(obj.mul(x, x), x); }
        else if (k == 3) { y = 4 * ONE; int256 x2 = obj.mul(x, x); direct = obj.mul(x2, x2); }
        else if (k == 4) { y = ONE / 2; direct = obj.sqrt(x); }
        else if (k == 5) { y = ONE / 4; direct = obj.sqrt(obj.sqrt(x)); }
        else { y = -ONE; direct = obj.inv(x); }
        int256 got = obj.pow(x, y);
        // v5: y = 1 is exact and y = 2 the rounded square; the rest take the
        // general path, the nearest word, within the floored composite's error
        if (k == 0) assertEq(got, direct, "y = 1");
        else assertLe(_absd(got, direct), (_absd(direct, 0) >> 100) + 4, "pow within the composite's error");
        int256 h = int256(IHuffOps(address(huff)).powRaw(_u(x), _u(y)));
        assertLe(_absd(got, h), (_absd(got, 0) >> 100) + 4, "huff general path within 2^-100");

        int256 ysm = bound(int256(uint256(which)), -30 * ONE, 30 * ONE);
        assertEq(obj.pow(2 * ONE, ysm), obj.exp2(ysm), "x=2 shortcut");
        assertEq(obj.pow(10 * ONE, ysm), obj.exp10(ysm), "x=10 shortcut");
    }

    function testFuzz_huff_abs_neg(int256 x) public view {
        vm.assume(x != MIN);
        _objHuff(abi.encodeCall(IFP127.abs, (x)), abi.encodeCall(IHuffOps.absRaw, (_u(x))), "abs");
        _objHuff(abi.encodeCall(IFP127.neg, (x)), abi.encodeCall(IHuffOps.negRaw, (_u(x))), "neg");
    }

    function testFuzz_huff_inv(int256 x) public view {
        // |x| >= 3 so 2^256/|x| fits in int256; |x| in {1, 2} overflows and the Huff wrapped
        vm.assume(x > 2 || x < -2);
        _objHuff(abi.encodeCall(IFP127.inv, (x)), abi.encodeCall(IHuffOps.invRaw, (_u(x))), "inv");
    }

    function testFuzz_huff_minmax(int256 a, int256 b, int256 c) public view {
        _objHuff(abi.encodeCall(IFP127.min, (a, b)), abi.encodeCall(IHuffOps.minRaw, (_u(a), _u(b))), "min");
        _objHuff(abi.encodeCall(IFP127.max, (a, b)), abi.encodeCall(IHuffOps.maxRaw, (_u(a), _u(b))), "max");
        _objHuff(abi.encodeCall(IFP127.clamp, (a, b, c)), abi.encodeCall(IHuffOps.clampRaw, (_u(a), _u(b), _u(c))), "clamp");
        _objHuff(abi.encodeCall(IFP127.avg, (a, b)), abi.encodeCall(IHuffOps.avgRaw, (_u(a), _u(b))), "avg");
    }

    function testFuzz_huff_bitops(int256 x) public view {
        _objHuff(abi.encodeCall(IFP127.sign, (x)), abi.encodeCall(IHuffOps.signRaw, (_u(x))), "sign");
        _objHuff(abi.encodeCall(IFP127.floor, (x)), abi.encodeCall(IHuffOps.floorRaw, (_u(x))), "floor");
        _objHuff(abi.encodeCall(IFP127.frac, (x)), abi.encodeCall(IHuffOps.fracRaw, (_u(x))), "frac");
    }

    function testFuzz_huff_ceil_round(int256 x) public view {
        x = bound(x, MIN, MAX - ONE);
        _objHuff(abi.encodeCall(IFP127.ceil, (x)), abi.encodeCall(IHuffOps.ceilRaw, (_u(x))), "ceil");
        _objHuff(abi.encodeCall(IFP127.round, (x)), abi.encodeCall(IHuffOps.roundRaw, (_u(x))), "round");
    }

    function testFuzz_huff_sub_family(int256 a, int256 b, int256 t) public view {
        a = bound(a, -B190, B190);
        b = bound(b, -B190, B190);
        t = bound(t, -4 * ONE, 4 * ONE);
        _objHuff(abi.encodeCall(IFP127.zeroFloorSub, (a, b)), abi.encodeCall(IHuffOps.zeroFloorSubRaw, (_u(a), _u(b))), "zeroFloorSub");
        _objHuff(abi.encodeCall(IFP127.dist, (a, b)), abi.encodeCall(IHuffOps.distRaw, (_u(a), _u(b))), "dist");
        _objHuff(abi.encodeCall(IFP127.lerp, (a, b, t)), abi.encodeCall(IHuffOps.lerpRaw, (_u(a), _u(b), _u(t))), "lerp");
        _objHuff(abi.encodeCall(IFP127.hypot, (a, b)), abi.encodeCall(IHuffOps.hypotRaw, (_u(a), _u(b))), "hypot");
    }

    function testFuzz_huff_gavg(int256 a, int256 b) public view {
        a = bound(a, 0, B190);
        b = bound(b, 0, B190);
        _objHuff(abi.encodeCall(IFP127.gavg, (a, b)), abi.encodeCall(IHuffOps.gavgRaw, (_u(a), _u(b))), "gavg");
    }

    function testFuzz_huff_factorial(int256 n) public view {
        n = bound(n, 0, 34 * ONE - 1);
        _objHuff(abi.encodeCall(IFP127.factorial, (n)), abi.encodeCall(IHuffOps.factorialRaw, (_u(n))), "factorial");
    }

    /// The Huff Lambert W (table seed, two steps) delivered 50 to 100 bits
    /// on [1, 64) and under 40 bits near 0; the Yul delivers 126+. Agreement
    /// is asserted on [1, 64) to 2^-40 relative; Precision.t.sol holds the
    /// real bar.
    function testFuzz_huff_lambertW0(int256 x) public view {
        x = bound(x, ONE, 64 * ONE - 1);
        int256 o = obj.lambertW0(x);
        int256 h = int256(IHuffOps(address(huff)).lambertW0Raw(_u(x)));
        assertLe(_absd(o, h), (o >> 40) + 4, "lambertW0 vs sepolia huff");
    }

    // ------------------------------------------------------------------
    // Divergences: Yul reverts, Huff returned a sentinel or garbage
    // ------------------------------------------------------------------

    function test_divergence_exp_overflow() public view {
        // Huff: exp(89) returns MAX_UINT256 (-1 as int256).
        assertEq(IHuffOps(address(huff)).expRaw(_u(89 * ONE)), type(uint256).max);
        _expectRevert(abi.encodeCall(IFP127.exp, (89 * ONE)), IFP127.Overflow.selector, "exp");
    }

    function test_divergence_exp2_at_127() public view {
        // Huff: exp2(127) wraps to MIN. Yul: Overflow.
        assertEq(int256(IHuffOps(address(huff)).exp2Raw(_u(127 * ONE))), MIN);
        _expectRevert(abi.encodeCall(IFP127.exp2, (127 * ONE)), IFP127.Overflow.selector, "exp2");
    }

    function test_divergence_log_nonpositive() public view {
        // Huff: log2(0) and log2(-1) return 0. Yul: OutOfRange.
        assertEq(IHuffOps(address(huff)).log2Raw(0), 0);
        assertEq(IHuffOps(address(huff)).log2Raw(_u(-ONE)), 0);
        _expectRevert(abi.encodeCall(IFP127.log2, (0)), IFP127.OutOfRange.selector, "log2(0)");
        _expectRevert(abi.encodeCall(IFP127.ln, (-ONE)), IFP127.OutOfRange.selector, "ln(-1)");
        _expectRevert(abi.encodeCall(IFP127.log10, (0)), IFP127.OutOfRange.selector, "log10(0)");
    }

    function test_divergence_sqrt_negative() public view {
        _expectRevert(abi.encodeCall(IFP127.sqrt, (-ONE)), IFP127.OutOfRange.selector, "sqrt");
    }

    function test_divergence_pow_negative_base() public view {
        // Both revert; the Huff with empty data, the Yul with OutOfRange.
        Res memory h = _try(address(huff), abi.encodeCall(IHuffOps.powRaw, (_u(-ONE), _u(ONE / 2))));
        assertFalse(h.ok);
        assertEq(h.err.length, 0);
        _expectRevert(abi.encodeCall(IFP127.pow, (-ONE, ONE / 2)), IFP127.OutOfRange.selector, "pow");
    }

    function test_divergence_factorial_range() public view {
        assertEq(IHuffOps(address(huff)).factorialRaw(_u(34 * ONE)), type(uint256).max);
        _expectRevert(abi.encodeCall(IFP127.factorial, (34 * ONE)), IFP127.OutOfRange.selector, "factorial(34)");
        _expectRevert(abi.encodeCall(IFP127.factorial, (-ONE)), IFP127.OutOfRange.selector, "factorial(-1)");
    }

    function test_divergence_lambertW0_domain() public view {
        // Huff: below -1/e returns 0. Yul: OutOfRange.
        assertEq(IHuffOps(address(huff)).lambertW0Raw(_u(-ONE)), 0);
        _expectRevert(abi.encodeCall(IFP127.lambertW0, (-ONE)), IFP127.OutOfRange.selector, "lambertW0");
    }

    function test_divergence_lambertW0_negative_oog() public view {
        // Huff: any x in [-1/e, 0) indexes memory near 2^133 and runs out of
        // gas. Yul: a real answer. W(-0.25) = -0.3574029561813889...
        Res memory h = _try(address(huff), abi.encodeCall(IHuffOps.lambertW0Raw, (_u(-ONE / 4))));
        assertFalse(h.ok, "huff should fail");
        int256 w = obj.lambertW0(-ONE / 4);
        // -0.3574029561813889 * 2^128
        int256 expected = -121617923873943470405355803408166885968;
        int256 d = w > expected ? w - expected : expected - w;
        assertLe(d, int256(1) << 4, "W(-1/4) within 16 ULP");
    }

    function test_divergence_lambertW0_table_shortcuts() public view {
        // Sepolia bytecode predates the W(1..5) shortcuts and iterates; the
        // repo source and the Yul return the table entry. Observed live:
        // Huff W(2) = ...613656, table = ...613659, 3 ULP apart.
        int256 h = int256(IHuffOps(address(huff)).lambertW0Raw(_u(2 * ONE)));
        int256 y = obj.lambertW0(2 * ONE);
        assertEq(y, 0xda445aab89e28ccbe8ac8e1abd5cd1db);
        assertLe(_absd(h, y), 8);
    }

    function test_divergence_abs_neg_min() public view {
        assertEq(int256(IHuffOps(address(huff)).absRaw(_u(MIN))), MIN);
        _expectRevert(abi.encodeCall(IFP127.abs, (MIN)), IFP127.Overflow.selector, "abs");
        _expectRevert(abi.encodeCall(IFP127.neg, (MIN)), IFP127.Overflow.selector, "neg");
    }

    // ------------------------------------------------------------------
    // Known values and identities
    // ------------------------------------------------------------------

    function test_known_transcendentals() public view {
        // e = 2.718281828459045235360287471352662497757...
        int256 e = obj.exp(ONE);
        int256 eRef = 924983374546220337150911035843336795079; // floor(e * 2^128)
        assertLe(_absd(e, eRef), 4);
        assertEq(obj.exp2(10 * ONE), 1024 * ONE);
        assertEq(obj.exp2(-ONE), ONE / 2);
        assertEq(obj.log2(1024 * ONE), 10 * ONE);
        assertEq(obj.log2(ONE / 4), -2 * ONE);
        assertLe(_absd(obj.ln(e), ONE), 8);
        assertEq(obj.sqrt(4 * ONE), 2 * ONE);
        assertEq(obj.sqrt(ONE / 4), ONE / 2);
        assertEq(obj.cbrt(27 * ONE), 3 * ONE);
        assertEq(obj.cbrt(-27 * ONE), -3 * ONE);
        assertEq(obj.pow(3 * ONE, 2 * ONE), 9 * ONE);
        assertEq(obj.pow(2 * ONE, 10 * ONE), 1024 * ONE);
        assertEq(obj.pow(10 * ONE, 2 * ONE), 100 * ONE);
        assertEq(obj.factorial(5 * ONE + 1), 120 * ONE);
        assertEq(obj.factorial(0), ONE);
        assertEq(obj.lambertW0(ONE), 0x91304d7c74b2ba5eafddaa6286dc28e1);
        assertEq(obj.lambertW0(0), 0);
        assertEq(obj.floor(-ONE / 2), -ONE);
        assertEq(obj.ceil(-ONE / 2), 0);
        assertEq(obj.round(ONE / 2), ONE);
        assertEq(obj.round(-ONE / 2), 0);
        assertEq(obj.sign(-5), -ONE);
        assertEq(obj.log2Up(5 * ONE), 3 * ONE);
        assertEq(obj.log2Up(8 * ONE), 3 * ONE);
    }

    /// W(x) e^W(x) == x to within a few ULP across the whole domain,
    /// including the regions the Huff could not handle.
    function testFuzz_prop_lambertW0_inverse(int256 x) public view {
        x = bound(x, -int256(0x5e2d58d8b3bcdf1abadec7829054f90d) / 2, int256(1) << 160);
        int256 w = obj.lambertW0(x);
        int256 back = obj.mul(w, obj.exp(w));
        int256 d = _absd(back, x);
        // the residual w e^w - x is amplified by e^w (1 + w) relative to the
        // error in w; 2^-112 relative plus 8 ULP leaves room for exp's own
        // error on top of 126-bit w
        int256 tol = (x < 0 ? -x : x) >> 112;
        assertLe(d, tol + 8);
    }

    function testFuzz_prop_exp_ln(int256 x) public view {
        x = bound(x, ONE / 1000, 1000 * ONE);
        int256 back = obj.exp(obj.ln(x));
        assertLe(_absd(back, x), (x >> 110) + 8);
    }

    function testFuzz_prop_sqrt_square(int256 x) public view {
        x = bound(x, 0, int256(1) << 250);
        int256 s = obj.sqrt(x);
        int256 sq = obj.mul(s, s);
        assertLe(sq, x);
        int256 s1 = s + 1;
        // (s+1)^2 may floor back to exactly x, so >= not >
        assertGe(obj.mul(s1, s1), x);
    }

    function _absd(int256 a, int256 b) internal pure returns (int256) {
        return a > b ? a - b : b - a;
    }
}

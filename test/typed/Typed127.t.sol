// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Test} from "forge-std/Test.sol";
import {console} from "forge-std/console.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import "../../contracts/src/bl127/BL127Type.sol";

// One contract per op and form, f(x, y, z) the op alone, as a caller's own
// contract would hold it: R127_<op> calls BL127Lib, T127_<op> the typed API.
// test_gas compares their call gas. Every op of contracts/src/bl127/ops.json
// has a pair, a row in _ops() and a line in raw() and typed()
// (test_coversEveryOp checks the table).

contract R127_exp2 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.exp2(x);
    }
}

contract T127_exp2 {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.exp2());
    }
}

contract R127_exp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.exp(x);
    }
}

contract T127_exp {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.exp());
    }
}

contract R127_exp10 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.exp10(x);
    }
}

contract T127_exp10 {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.exp10());
    }
}

contract R127_log2 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.log2(x);
    }
}

contract T127_log2 {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.log2());
    }
}

contract R127_ln {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.ln(x);
    }
}

contract T127_ln {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.ln());
    }
}

contract R127_log10 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.log10(x);
    }
}

contract T127_log10 {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.log10());
    }
}

contract R127_log2Up {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.log2Up(x);
    }
}

contract T127_log2Up {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.log2Up());
    }
}

contract R127_sqrt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.sqrt(x);
    }
}

contract T127_sqrt {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.sqrt());
    }
}

contract R127_cbrt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.cbrt(x);
    }
}

contract T127_cbrt {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.cbrt());
    }
}

contract R127_inv {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.inv(x);
    }
}

contract T127_inv {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.inv());
    }
}

contract R127_abs {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.abs(x);
    }
}

contract T127_abs {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.abs());
    }
}

contract R127_sign {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.sign(x);
    }
}

contract T127_sign {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.sign());
    }
}

contract R127_floor {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.floor(x);
    }
}

contract T127_floor {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.floor());
    }
}

contract R127_ceil {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.ceil(x);
    }
}

contract T127_ceil {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.ceil());
    }
}

contract R127_frac {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.frac(x);
    }
}

contract T127_frac {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.frac());
    }
}

contract R127_round {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.round(x);
    }
}

contract T127_round {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.round());
    }
}

contract R127_factorial {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.factorial(x);
    }
}

contract T127_factorial {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.factorial());
    }
}

contract R127_lambertW0 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.lambertW0(x);
    }
}

contract T127_lambertW0 {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.lambertW0());
    }
}

contract R127_lambertWm1 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.lambertWm1(x);
    }
}

contract T127_lambertWm1 {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.lambertWm1());
    }
}

contract R127_log1p {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.log1p(x);
    }
}

contract T127_log1p {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.log1p());
    }
}

contract R127_expm1 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.expm1(x);
    }
}

contract T127_expm1 {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.expm1());
    }
}

contract R127_sinh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.sinh(x);
    }
}

contract T127_sinh {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.sinh());
    }
}

contract R127_cosh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.cosh(x);
    }
}

contract T127_cosh {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.cosh());
    }
}

contract R127_tanh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.tanh(x);
    }
}

contract T127_tanh {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.tanh());
    }
}

contract R127_atanh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.atanh(x);
    }
}

contract T127_atanh {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.atanh());
    }
}

contract R127_erf {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.erf(x);
    }
}

contract T127_erf {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.erf());
    }
}

contract R127_erfc {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.erfc(x);
    }
}

contract T127_erfc {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.erfc());
    }
}

contract R127_normCdf {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.normCdf(x);
    }
}

contract T127_normCdf {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.normCdf());
    }
}

contract R127_neg {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.neg(x);
    }
}

contract T127_neg {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(-a);
    }
}

contract R127_add {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.add(x, y);
    }
}

contract T127_add {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a + b);
    }
}

contract R127_sub {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.sub(x, y);
    }
}

contract T127_sub {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a - b);
    }
}

contract R127_mul {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.mul(x, y);
    }
}

contract T127_mul {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a * b);
    }
}

contract R127_div {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.div(x, y);
    }
}

contract T127_div {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a / b);
    }
}

contract R127_mulDown {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.mulDown(x, y);
    }
}

contract T127_mulDown {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.mulDown(b));
    }
}

contract R127_mulUp {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.mulUp(x, y);
    }
}

contract T127_mulUp {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.mulUp(b));
    }
}

contract R127_divDown {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.divDown(x, y);
    }
}

contract T127_divDown {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.divDown(b));
    }
}

contract R127_divUp {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.divUp(x, y);
    }
}

contract T127_divUp {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.divUp(b));
    }
}

contract R127_pow {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.pow(x, y);
    }
}

contract T127_pow {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.pow(b));
    }
}

contract R127_powu {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.powu(x, y);
    }
}

contract T127_powu {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.powu(b));
    }
}

contract R127_compound {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.compound(x, y);
    }
}

contract T127_compound {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.compound(b));
    }
}

contract R127_gavg {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.gavg(x, y);
    }
}

contract T127_gavg {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.gavg(b));
    }
}

contract R127_hypot {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.hypot(x, y);
    }
}

contract T127_hypot {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.hypot(b));
    }
}

contract R127_min {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.min(x, y);
    }
}

contract T127_min {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.min(b));
    }
}

contract R127_max {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.max(x, y);
    }
}

contract T127_max {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.max(b));
    }
}

contract R127_avg {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.avg(x, y);
    }
}

contract T127_avg {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.avg(b));
    }
}

contract R127_zeroFloorSub {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.zeroFloorSub(x, y);
    }
}

contract T127_zeroFloorSub {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.zeroFloorSub(b));
    }
}

contract R127_dist {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL127Lib.dist(x, y);
    }
}

contract T127_dist {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.dist(b));
    }
}

contract R127_clamp {
    function f(int256 x, int256 y, int256 z) external pure returns (int256 r) {
        r = BL127Lib.clamp(x, y, z);
    }
}

contract T127_clamp {
    function f(BL127 a, BL127 b, BL127 c) external pure returns (int256 r) {
        r = BL127.unwrap(a.clamp(b, c));
    }
}

contract R127_lerp {
    function f(int256 x, int256 y, int256 z) external pure returns (int256 r) {
        r = BL127Lib.lerp(x, y, z);
    }
}

contract T127_lerp {
    function f(BL127 a, BL127 b, BL127 c) external pure returns (int256 r) {
        r = BL127.unwrap(a.lerp(b, c));
    }
}

contract R127_lt {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = x < y ? int256(1) : int256(0);
    }
}

contract T127_lt {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = a < b ? int256(1) : int256(0);
    }
}

contract R127_gt {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = x > y ? int256(1) : int256(0);
    }
}

contract T127_gt {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = a > b ? int256(1) : int256(0);
    }
}

contract R127_le {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = x <= y ? int256(1) : int256(0);
    }
}

contract T127_le {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = a <= b ? int256(1) : int256(0);
    }
}

contract R127_ge {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = x >= y ? int256(1) : int256(0);
    }
}

contract T127_ge {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = a >= b ? int256(1) : int256(0);
    }
}

contract R127_eq {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = x == y ? int256(1) : int256(0);
    }
}

contract T127_eq {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = a == b ? int256(1) : int256(0);
    }
}

contract R127_ne {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = x != y ? int256(1) : int256(0);
    }
}

contract T127_ne {
    function f(BL127 a, BL127 b, int256) external pure returns (int256 r) {
        r = a != b ? int256(1) : int256(0);
    }
}

contract R127_fromFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.fromFixed18(x);
    }
}

contract T127_fromFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(bl127FromFixed18(x));
    }
}

contract R127_toFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.toFixed18(x);
    }
}

contract T127_toFixed18 {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18();
    }
}

contract R127_toFixed18Down {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.toFixed18Down(x);
    }
}

contract T127_toFixed18Down {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18Down();
    }
}

contract R127_toFixed18Up {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.toFixed18Up(x);
    }
}

contract T127_toFixed18Up {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18Up();
    }
}

contract R127_fromWad {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        if (uint256(x) > uint256(type(int256).max)) revert BL127Lib.Overflow();
        r = BL127Lib.fromFixed18(x);
    }
}

contract T127_fromWad {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(bl127FromWad(uint256(x)));
    }
}

contract R127_toWadDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.toFixed18Down(x);
        if (r < 0) revert BL127Lib.OutOfRange();
    }
}

contract T127_toWadDown {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toWadDown());
    }
}

contract R127_toWadUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.toFixed18Up(x);
        if (r < 0) revert BL127Lib.OutOfRange();
    }
}

contract T127_toWadUp {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toWadUp());
    }
}

contract R127_fromInt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        if (x > type(int128).max || x < type(int128).min) revert BL127Lib.Overflow();
        r = x * BL127Lib.ONE;
    }
}

contract T127_fromInt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(bl127FromInt(x));
    }
}

contract R127_toIntDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL127Lib.floor(x) / BL127Lib.ONE;
    }
}

contract T127_toIntDown {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = a.toIntDown();
    }
}

contract R127_toIntUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = x / BL127Lib.ONE;
        if (x > 0 && x % BL127Lib.ONE != 0) r += 1;
    }
}

contract T127_toIntUp {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = a.toIntUp();
    }
}

contract R127_unwrap {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = x;
    }
}

contract T127_unwrap {
    function f(BL127 a, int256, int256) external pure returns (int256 r) {
        r = a.unwrap();
    }
}

/// @title Typed127
/// @notice contracts/src/bl127/BL127Type.sol adds nothing to BL127Lib:
///         - testFuzz_same: raw() and typed() run every op by name, raw() on
///           BL127Lib and typed() through the type (the operator where one is
///           bound, the attached function otherwise), on the same fuzzed
///           inputs: the same word or the same revert data, byte for byte;
///         - test_gas: on a typical input, the typed contract's call costs the
///           raw one's within TYPED_GAS_TOL gas. make typed runs it twice:
///           under the default profile (legacy codegen) with the default
///           tolerance, 120 (the wrapper is one more internal call frame,
///           36 to 56 gas, and up to 114 on floor, frac and sign, which the
///           legacy optimizer inlines whole into a raw caller but not through
///           the wrapper), and through the IR with 0, where every op costs
///           the same. Prints TYPED|bl127|op|raw|typed;
///         - test_coversEveryOp: every op in ops.json is in the table.
///         The typed-only helpers (bl127FromWad, toWadDown, toWadUp,
///         bl127FromInt, toIntDown, toIntUp) are checked against the raw call
///         with the guard they document, or an independent formula (the last
///         three, whose gas is printed but not compared).
contract Typed127 is Test {
    struct Op {
        bytes32 name;
        bytes kinds; // v BL127, i int256, u uint256 (one char per argument)
        int256[3] typ; // a typical input, in domain
        bool same; // raw is the same call, so the gas must match
        string rawC; // the two contracts
        string typedC;
    }

    int256 constant O = BL127Lib.ONE;
    bytes32 constant NA = keccak256(abi.encodeWithSignature("Error(string)", "na"));

    // ---- the two forms of every op ---------------------------------------

    function raw(bytes32 op, int256 x, int256 y, int256 z) external pure returns (int256 r) {
        (z);
        if (op == "exp2") {
            r = BL127Lib.exp2(x);
        } else if (op == "exp") {
            r = BL127Lib.exp(x);
        } else if (op == "exp10") {
            r = BL127Lib.exp10(x);
        } else if (op == "log2") {
            r = BL127Lib.log2(x);
        } else if (op == "ln") {
            r = BL127Lib.ln(x);
        } else if (op == "log10") {
            r = BL127Lib.log10(x);
        } else if (op == "log2Up") {
            r = BL127Lib.log2Up(x);
        } else if (op == "sqrt") {
            r = BL127Lib.sqrt(x);
        } else if (op == "cbrt") {
            r = BL127Lib.cbrt(x);
        } else if (op == "inv") {
            r = BL127Lib.inv(x);
        } else if (op == "abs") {
            r = BL127Lib.abs(x);
        } else if (op == "sign") {
            r = BL127Lib.sign(x);
        } else if (op == "floor") {
            r = BL127Lib.floor(x);
        } else if (op == "ceil") {
            r = BL127Lib.ceil(x);
        } else if (op == "frac") {
            r = BL127Lib.frac(x);
        } else if (op == "round") {
            r = BL127Lib.round(x);
        } else if (op == "factorial") {
            r = BL127Lib.factorial(x);
        } else if (op == "lambertW0") {
            r = BL127Lib.lambertW0(x);
        } else if (op == "lambertWm1") {
            r = BL127Lib.lambertWm1(x);
        } else if (op == "log1p") {
            r = BL127Lib.log1p(x);
        } else if (op == "expm1") {
            r = BL127Lib.expm1(x);
        } else if (op == "sinh") {
            r = BL127Lib.sinh(x);
        } else if (op == "cosh") {
            r = BL127Lib.cosh(x);
        } else if (op == "tanh") {
            r = BL127Lib.tanh(x);
        } else if (op == "atanh") {
            r = BL127Lib.atanh(x);
        } else if (op == "erf") {
            r = BL127Lib.erf(x);
        } else if (op == "erfc") {
            r = BL127Lib.erfc(x);
        } else if (op == "normCdf") {
            r = BL127Lib.normCdf(x);
        } else if (op == "neg") {
            r = BL127Lib.neg(x);
        } else if (op == "add") {
            r = BL127Lib.add(x, y);
        } else if (op == "sub") {
            r = BL127Lib.sub(x, y);
        } else if (op == "mul") {
            r = BL127Lib.mul(x, y);
        } else if (op == "div") {
            r = BL127Lib.div(x, y);
        } else if (op == "mulDown") {
            r = BL127Lib.mulDown(x, y);
        } else if (op == "mulUp") {
            r = BL127Lib.mulUp(x, y);
        } else if (op == "divDown") {
            r = BL127Lib.divDown(x, y);
        } else if (op == "divUp") {
            r = BL127Lib.divUp(x, y);
        } else if (op == "pow") {
            r = BL127Lib.pow(x, y);
        } else if (op == "powu") {
            r = BL127Lib.powu(x, y);
        } else if (op == "compound") {
            r = BL127Lib.compound(x, y);
        } else if (op == "gavg") {
            r = BL127Lib.gavg(x, y);
        } else if (op == "hypot") {
            r = BL127Lib.hypot(x, y);
        } else if (op == "min") {
            r = BL127Lib.min(x, y);
        } else if (op == "max") {
            r = BL127Lib.max(x, y);
        } else if (op == "avg") {
            r = BL127Lib.avg(x, y);
        } else if (op == "zeroFloorSub") {
            r = BL127Lib.zeroFloorSub(x, y);
        } else if (op == "dist") {
            r = BL127Lib.dist(x, y);
        } else if (op == "clamp") {
            r = BL127Lib.clamp(x, y, z);
        } else if (op == "lerp") {
            r = BL127Lib.lerp(x, y, z);
        } else if (op == "lt") {
            r = x < y ? int256(1) : int256(0);
        } else if (op == "gt") {
            r = x > y ? int256(1) : int256(0);
        } else if (op == "le") {
            r = x <= y ? int256(1) : int256(0);
        } else if (op == "ge") {
            r = x >= y ? int256(1) : int256(0);
        } else if (op == "eq") {
            r = x == y ? int256(1) : int256(0);
        } else if (op == "ne") {
            r = x != y ? int256(1) : int256(0);
        } else if (op == "fromFixed18") {
            r = BL127Lib.fromFixed18(x);
        } else if (op == "toFixed18") {
            r = BL127Lib.toFixed18(x);
        } else if (op == "toFixed18Down") {
            r = BL127Lib.toFixed18Down(x);
        } else if (op == "toFixed18Up") {
            r = BL127Lib.toFixed18Up(x);
        } else if (op == "fromWad") {
            if (uint256(x) > uint256(type(int256).max)) revert BL127Lib.Overflow();
            r = BL127Lib.fromFixed18(x);
        } else if (op == "toWadDown") {
            r = BL127Lib.toFixed18Down(x);
            if (r < 0) revert BL127Lib.OutOfRange();
        } else if (op == "toWadUp") {
            r = BL127Lib.toFixed18Up(x);
            if (r < 0) revert BL127Lib.OutOfRange();
        } else if (op == "fromInt") {
            if (x > type(int128).max || x < type(int128).min) revert BL127Lib.Overflow();
            r = x * BL127Lib.ONE;
        } else if (op == "toIntDown") {
            r = BL127Lib.floor(x) / BL127Lib.ONE;
        } else if (op == "toIntUp") {
            r = x / BL127Lib.ONE;
            if (x > 0 && x % BL127Lib.ONE != 0) r += 1;
        } else if (op == "unwrap") {
            r = x;
        } else {
            revert("na");
        }
    }

    function typed(bytes32 op, int256 x, int256 y, int256 z) external pure returns (int256 r) {
        (BL127 a, BL127 b, BL127 c) = (BL127.wrap(x), BL127.wrap(y), BL127.wrap(z));
        (a, b, c);
        if (op == "exp2") r = BL127.unwrap(a.exp2());
        else if (op == "exp") r = BL127.unwrap(a.exp());
        else if (op == "exp10") r = BL127.unwrap(a.exp10());
        else if (op == "log2") r = BL127.unwrap(a.log2());
        else if (op == "ln") r = BL127.unwrap(a.ln());
        else if (op == "log10") r = BL127.unwrap(a.log10());
        else if (op == "log2Up") r = BL127.unwrap(a.log2Up());
        else if (op == "sqrt") r = BL127.unwrap(a.sqrt());
        else if (op == "cbrt") r = BL127.unwrap(a.cbrt());
        else if (op == "inv") r = BL127.unwrap(a.inv());
        else if (op == "abs") r = BL127.unwrap(a.abs());
        else if (op == "sign") r = BL127.unwrap(a.sign());
        else if (op == "floor") r = BL127.unwrap(a.floor());
        else if (op == "ceil") r = BL127.unwrap(a.ceil());
        else if (op == "frac") r = BL127.unwrap(a.frac());
        else if (op == "round") r = BL127.unwrap(a.round());
        else if (op == "factorial") r = BL127.unwrap(a.factorial());
        else if (op == "lambertW0") r = BL127.unwrap(a.lambertW0());
        else if (op == "lambertWm1") r = BL127.unwrap(a.lambertWm1());
        else if (op == "log1p") r = BL127.unwrap(a.log1p());
        else if (op == "expm1") r = BL127.unwrap(a.expm1());
        else if (op == "sinh") r = BL127.unwrap(a.sinh());
        else if (op == "cosh") r = BL127.unwrap(a.cosh());
        else if (op == "tanh") r = BL127.unwrap(a.tanh());
        else if (op == "atanh") r = BL127.unwrap(a.atanh());
        else if (op == "erf") r = BL127.unwrap(a.erf());
        else if (op == "erfc") r = BL127.unwrap(a.erfc());
        else if (op == "normCdf") r = BL127.unwrap(a.normCdf());
        else if (op == "neg") r = BL127.unwrap(-a);
        else if (op == "add") r = BL127.unwrap(a + b);
        else if (op == "sub") r = BL127.unwrap(a - b);
        else if (op == "mul") r = BL127.unwrap(a * b);
        else if (op == "div") r = BL127.unwrap(a / b);
        else if (op == "mulDown") r = BL127.unwrap(a.mulDown(b));
        else if (op == "mulUp") r = BL127.unwrap(a.mulUp(b));
        else if (op == "divDown") r = BL127.unwrap(a.divDown(b));
        else if (op == "divUp") r = BL127.unwrap(a.divUp(b));
        else if (op == "pow") r = BL127.unwrap(a.pow(b));
        else if (op == "powu") r = BL127.unwrap(a.powu(b));
        else if (op == "compound") r = BL127.unwrap(a.compound(b));
        else if (op == "gavg") r = BL127.unwrap(a.gavg(b));
        else if (op == "hypot") r = BL127.unwrap(a.hypot(b));
        else if (op == "min") r = BL127.unwrap(a.min(b));
        else if (op == "max") r = BL127.unwrap(a.max(b));
        else if (op == "avg") r = BL127.unwrap(a.avg(b));
        else if (op == "zeroFloorSub") r = BL127.unwrap(a.zeroFloorSub(b));
        else if (op == "dist") r = BL127.unwrap(a.dist(b));
        else if (op == "clamp") r = BL127.unwrap(a.clamp(b, c));
        else if (op == "lerp") r = BL127.unwrap(a.lerp(b, c));
        else if (op == "lt") r = a < b ? int256(1) : int256(0);
        else if (op == "gt") r = a > b ? int256(1) : int256(0);
        else if (op == "le") r = a <= b ? int256(1) : int256(0);
        else if (op == "ge") r = a >= b ? int256(1) : int256(0);
        else if (op == "eq") r = a == b ? int256(1) : int256(0);
        else if (op == "ne") r = a != b ? int256(1) : int256(0);
        else if (op == "fromFixed18") r = BL127.unwrap(bl127FromFixed18(x));
        else if (op == "toFixed18") r = a.toFixed18();
        else if (op == "toFixed18Down") r = a.toFixed18Down();
        else if (op == "toFixed18Up") r = a.toFixed18Up();
        else if (op == "fromWad") r = BL127.unwrap(bl127FromWad(uint256(x)));
        else if (op == "toWadDown") r = int256(a.toWadDown());
        else if (op == "toWadUp") r = int256(a.toWadUp());
        else if (op == "fromInt") r = BL127.unwrap(bl127FromInt(x));
        else if (op == "toIntDown") r = a.toIntDown();
        else if (op == "toIntUp") r = a.toIntUp();
        else if (op == "unwrap") r = a.unwrap();
        else revert("na");
    }

    // ---- the table ---------------------------------------------------------

    function _q(int256 num, int256 den) internal pure returns (int256) {
        return num * O / den;
    }

    function _ops() internal pure returns (Op[] memory t) {
        t = new Op[](66);
        t[0] = Op("exp2", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_exp2", "T127_exp2");
        t[1] = Op("exp", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_exp", "T127_exp");
        t[2] = Op("exp10", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_exp10", "T127_exp10");
        t[3] = Op("log2", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_log2", "T127_log2");
        t[4] = Op("ln", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_ln", "T127_ln");
        t[5] = Op("log10", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_log10", "T127_log10");
        t[6] = Op("log2Up", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_log2Up", "T127_log2Up");
        t[7] = Op("sqrt", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_sqrt", "T127_sqrt");
        t[8] = Op("cbrt", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_cbrt", "T127_cbrt");
        t[9] = Op("inv", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_inv", "T127_inv");
        t[10] = Op("abs", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_abs", "T127_abs");
        t[11] = Op("sign", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_sign", "T127_sign");
        t[12] = Op("floor", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_floor", "T127_floor");
        t[13] = Op("ceil", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_ceil", "T127_ceil");
        t[14] = Op("frac", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_frac", "T127_frac");
        t[15] = Op("round", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_round", "T127_round");
        t[16] = Op("factorial", "v", [_q(5, 1), int256(0), int256(0)], true, "R127_factorial", "T127_factorial");
        t[17] = Op("lambertW0", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_lambertW0", "T127_lambertW0");
        t[18] = Op("lambertWm1", "v", [_q(-1, 4), int256(0), int256(0)], true, "R127_lambertWm1", "T127_lambertWm1");
        t[19] = Op("log1p", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_log1p", "T127_log1p");
        t[20] = Op("expm1", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_expm1", "T127_expm1");
        t[21] = Op("sinh", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_sinh", "T127_sinh");
        t[22] = Op("cosh", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_cosh", "T127_cosh");
        t[23] = Op("tanh", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_tanh", "T127_tanh");
        t[24] = Op("atanh", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_atanh", "T127_atanh");
        t[25] = Op("erf", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_erf", "T127_erf");
        t[26] = Op("erfc", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_erfc", "T127_erfc");
        t[27] = Op("normCdf", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_normCdf", "T127_normCdf");
        t[28] = Op("neg", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_neg", "T127_neg");
        t[29] = Op("add", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_add", "T127_add");
        t[30] = Op("sub", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_sub", "T127_sub");
        t[31] = Op("mul", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_mul", "T127_mul");
        t[32] = Op("div", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_div", "T127_div");
        t[33] = Op("mulDown", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_mulDown", "T127_mulDown");
        t[34] = Op("mulUp", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_mulUp", "T127_mulUp");
        t[35] = Op("divDown", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_divDown", "T127_divDown");
        t[36] = Op("divUp", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_divUp", "T127_divUp");
        t[37] = Op("pow", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_pow", "T127_pow");
        t[38] = Op("powu", "vv", [_q(5, 4), _q(5, 1), int256(0)], true, "R127_powu", "T127_powu");
        t[39] = Op("compound", "vv", [_q(1, 100), _q(12, 1), int256(0)], true, "R127_compound", "T127_compound");
        t[40] = Op("gavg", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_gavg", "T127_gavg");
        t[41] = Op("hypot", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_hypot", "T127_hypot");
        t[42] = Op("min", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_min", "T127_min");
        t[43] = Op("max", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_max", "T127_max");
        t[44] = Op("avg", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_avg", "T127_avg");
        t[45] =
            Op("zeroFloorSub", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_zeroFloorSub", "T127_zeroFloorSub");
        t[46] = Op("dist", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_dist", "T127_dist");
        t[47] = Op("clamp", "vvv", [_q(3, 4), _q(1, 4), _q(5, 4)], true, "R127_clamp", "T127_clamp");
        t[48] = Op("lerp", "vvv", [_q(1, 4), _q(5, 4), _q(3, 4)], true, "R127_lerp", "T127_lerp");
        t[49] = Op("lt", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_lt", "T127_lt");
        t[50] = Op("gt", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_gt", "T127_gt");
        t[51] = Op("le", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_le", "T127_le");
        t[52] = Op("ge", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_ge", "T127_ge");
        t[53] = Op("eq", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_eq", "T127_eq");
        t[54] = Op("ne", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R127_ne", "T127_ne");
        t[55] = Op(
            "fromFixed18", "i", [int256(1.5e18), int256(0), int256(0)], true, "R127_fromFixed18", "T127_fromFixed18"
        );
        t[56] = Op("toFixed18", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_toFixed18", "T127_toFixed18");
        t[57] = Op(
            "toFixed18Down", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_toFixed18Down", "T127_toFixed18Down"
        );
        t[58] = Op("toFixed18Up", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_toFixed18Up", "T127_toFixed18Up");
        t[59] = Op("fromWad", "u", [int256(1.5e18), int256(0), int256(0)], true, "R127_fromWad", "T127_fromWad");
        t[60] = Op("toWadDown", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_toWadDown", "T127_toWadDown");
        t[61] = Op("toWadUp", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_toWadUp", "T127_toWadUp");
        t[62] = Op("fromInt", "i", [int256(7), int256(0), int256(0)], false, "R127_fromInt", "T127_fromInt");
        t[63] = Op("toIntDown", "v", [_q(7, 4), int256(0), int256(0)], false, "R127_toIntDown", "T127_toIntDown");
        t[64] = Op("toIntUp", "v", [_q(7, 4), int256(0), int256(0)], false, "R127_toIntUp", "T127_toIntUp");
        t[65] = Op("unwrap", "v", [_q(3, 4), int256(0), int256(0)], true, "R127_unwrap", "T127_unwrap");
    }

    // ---- inputs ------------------------------------------------------------

    /// s < 16 picks a special word, else x shifted right by s - 16: every
    /// magnitude from the full word down to a few raw units, either sign.
    function _v(int256 x, uint8 s) internal pure returns (int256) {
        if (s >= 16) return x >> (s - 16);
        int256[16] memory sp = [
            int256(0),
            O,
            -O,
            BL127Lib.PI,
            -BL127Lib.PI,
            type(int256).max,
            type(int256).min,
            type(int256).min + 1,
            O / 2,
            -O / 2,
            33 * O,
            int256(1),
            int256(-1),
            2 * O,
            34 * O,
            -(O * 367879441171442321 / 1e18)
        ];
        return sp[s];
    }

    function _arg(bytes memory kinds, uint256 k, int256 x, uint8 s) internal pure returns (int256) {
        if (k >= kinds.length) return 0;
        bytes1 c = kinds[k];
        if (c == "v") return _v(x, s);
        if (c == "i") return x >> s;
        return int256(uint256(x) >> s);
    }

    function _name(bytes32 b) internal pure returns (string memory) {
        uint256 n;
        while (n < 32 && b[n] != 0) n++;
        bytes memory s = new bytes(n);
        for (uint256 i; i < n; i++) {
            s[i] = b[i];
        }
        return string(s);
    }

    // ---- the checks --------------------------------------------------------

    function _same(bytes32 op, int256 x, int256 y, int256 z) internal view {
        (bool okR, bytes memory outR) = address(this).staticcall(abi.encodeCall(this.raw, (op, x, y, z)));
        (bool okT, bytes memory outT) = address(this).staticcall(abi.encodeCall(this.typed, (op, x, y, z)));
        string memory name = _name(op);
        assertTrue(okR || keccak256(outR) != NA, name);
        assertEq(okT, okR, name);
        if (okR) assertEq(abi.decode(outT, (int256)), abi.decode(outR, (int256)), name);
        else assertEq(outT, outR, name);
    }

    function testFuzz_same(int256 x, uint8 sx, int256 y, uint8 sy, int256 z, uint8 sz) public view {
        Op[] memory t = _ops();
        for (uint256 i; i < t.length; i++) {
            bytes memory k = t[i].kinds;
            _same(t[i].name, _arg(k, 0, x, sx), _arg(k, 1, y, sy), _arg(k, 2, z, sz));
        }
    }

    /// The whole call's gas, the encoding outside the window and no memory
    /// touched inside it (an expansion would cost more as memory grows): the two
    /// contracts have the one function, so dispatch and decoding are equal.
    function _gas(string memory c, int256[3] memory a) internal returns (uint256 g) {
        address t = vm.deployCode(c);
        bytes memory data = abi.encodeWithSignature("f(int256,int256,int256)", a[0], a[1], a[2]);
        bool ok;
        assembly {
            g := gas()
            ok := staticcall(gas(), t, add(data, 0x20), mload(data), 0, 0)
            g := sub(g, gas())
        }
        require(ok, c);
    }

    function test_gas() public {
        uint256 tol = vm.envOr("TYPED_GAS_TOL", uint256(120));
        Op[] memory t = _ops();
        uint256 worst;
        for (uint256 i; i < t.length; i++) {
            uint256 gR = _gas(t[i].rawC, t[i].typ);
            uint256 gT = _gas(t[i].typedC, t[i].typ);
            console.log(string.concat("TYPED|bl127|", _name(t[i].name), "|", vm.toString(gR), "|", vm.toString(gT)));
            if (!t[i].same) continue;
            uint256 d = gT > gR ? gT - gR : gR - gT;
            if (d > worst) worst = d;
            assertApproxEqAbs(gT, gR, tol, _name(t[i].name));
        }
        console.log(string.concat("TYPED|bl127|worst|", vm.toString(worst)));
    }

    function test_coversEveryOp() public view {
        string[] memory names =
            abi.decode(vm.parseJson(vm.readFile("contracts/src/bl127/ops.json"), ".ops[*].name"), (string[]));
        Op[] memory t = _ops();
        for (uint256 j; j < names.length; j++) {
            bool found;
            for (uint256 i; i < t.length; i++) {
                if (t[i].name == bytes32(bytes(names[j]))) found = true;
            }
            assertTrue(found, names[j]);
        }
    }

    // ---- the API as a caller writes it -------------------------------------

    function test_constants() public pure {
        assertEq(BL127.unwrap(ONE), BL127Lib.ONE);
        assertEq(BL127.unwrap(PI), BL127Lib.PI);
        assertEq(BL127.unwrap(bl127(42)), 42);
        assertEq(bl127(42).unwrap(), 42);
    }

    function test_example() public pure {
        BL127 b = bl127FromWad(1.5e18) * ONE.exp(); // 1.5 e
        assertEq(BL127.unwrap(b), BL127Lib.mul(BL127Lib.fromFixed18(1.5e18), BL127Lib.exp(BL127Lib.ONE)));
        assertTrue(b > bl127FromInt(4) && b < bl127FromInt(5));
        assertEq(b.toWadDown(), 4077422742688567853);
        assertEq(b.toWadUp(), 4077422742688567854);
        assertEq(b.toIntDown(), 4);
        assertEq(b.toIntUp(), 5);
        BL127 r = (b - ONE).ln() / PI + -ONE;
        assertEq(
            BL127.unwrap(r),
            BL127Lib.add(
                BL127Lib.div(BL127Lib.ln(BL127Lib.sub(BL127.unwrap(b), BL127Lib.ONE)), BL127Lib.PI),
                BL127Lib.neg(BL127Lib.ONE)
            )
        );
        assertTrue(r != ONE && r <= ONE && r >= -ONE && !(r == ONE));
    }
}

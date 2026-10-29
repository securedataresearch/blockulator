// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Test} from "forge-std/Test.sol";
import {console} from "forge-std/console.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import {BL19Lib} from "../../contracts/src/bl19/BL19Lib.sol";
import {BL127, bl127, bl127FromInt, ONE as ONE127} from "../../contracts/src/bl127/BL127Type.sol";
import "../../contracts/src/bl19/BL19Type.sol";

// One contract per op and form, f(x, y, z) the op alone, as a caller's own
// contract would hold it: R19_<op> calls BL19Lib, T19_<op> the typed API.
// test_gas compares their call gas. Every op of contracts/src/bl19/ops.json
// has a pair, a row in _ops() and a line in raw() and typed()
// (test_coversEveryOp checks the table).

contract R19_sqrt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.sqrt(x);
    }
}

contract T19_sqrt {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.sqrt());
    }
}

contract R19_exp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.exp(x);
    }
}

contract T19_exp {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.exp());
    }
}

contract R19_ln {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.ln(x);
    }
}

contract T19_ln {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.ln());
    }
}

contract R19_log1p {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.log1p(x);
    }
}

contract T19_log1p {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.log1p());
    }
}

contract R19_expm1 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.expm1(x);
    }
}

contract T19_expm1 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.expm1());
    }
}

contract R19_erf {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.erf(x);
    }
}

contract T19_erf {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.erf());
    }
}

contract R19_erfc {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.erfc(x);
    }
}

contract T19_erfc {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.erfc());
    }
}

contract R19_normCdf {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.normCdf(x);
    }
}

contract T19_normCdf {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.normCdf());
    }
}

contract R19_lambertW0 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.lambertW0(x);
    }
}

contract T19_lambertW0 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.lambertW0());
    }
}

contract R19_lambertWm1 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.lambertWm1(x);
    }
}

contract T19_lambertWm1 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.lambertWm1());
    }
}

contract R19_abs {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.abs(x);
    }
}

contract T19_abs {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.abs());
    }
}

contract R19_sign {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.sign(x);
    }
}

contract T19_sign {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.sign());
    }
}

contract R19_floor {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.floor(x);
    }
}

contract T19_floor {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.floor());
    }
}

contract R19_ceil {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.ceil(x);
    }
}

contract T19_ceil {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.ceil());
    }
}

contract R19_inv {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.inv(x);
    }
}

contract T19_inv {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.inv());
    }
}

contract R19_frac {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.frac(x);
    }
}

contract T19_frac {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.frac());
    }
}

contract R19_round {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.round(x);
    }
}

contract T19_round {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.round());
    }
}

contract R19_log2Up {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.log2Up(x);
    }
}

contract T19_log2Up {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.log2Up());
    }
}

contract R19_factorial {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.factorial(x);
    }
}

contract T19_factorial {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.factorial());
    }
}

contract R19_cbrt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.cbrt(x);
    }
}

contract T19_cbrt {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.cbrt());
    }
}

contract R19_exp2 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.exp2(x);
    }
}

contract T19_exp2 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.exp2());
    }
}

contract R19_exp10 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.exp10(x);
    }
}

contract T19_exp10 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.exp10());
    }
}

contract R19_log2 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.log2(x);
    }
}

contract T19_log2 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.log2());
    }
}

contract R19_log10 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.log10(x);
    }
}

contract T19_log10 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.log10());
    }
}

contract R19_sinh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.sinh(x);
    }
}

contract T19_sinh {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.sinh());
    }
}

contract R19_cosh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.cosh(x);
    }
}

contract T19_cosh {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.cosh());
    }
}

contract R19_tanh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.tanh(x);
    }
}

contract T19_tanh {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.tanh());
    }
}

contract R19_atanh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.atanh(x);
    }
}

contract T19_atanh {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.atanh());
    }
}

contract R19_neg {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.neg(x);
    }
}

contract T19_neg {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(-a);
    }
}

contract R19_add {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.add(x, y);
    }
}

contract T19_add {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a + b);
    }
}

contract R19_sub {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.sub(x, y);
    }
}

contract T19_sub {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a - b);
    }
}

contract R19_mul {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.mul(x, y);
    }
}

contract T19_mul {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a * b);
    }
}

contract R19_div {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.div(x, y);
    }
}

contract T19_div {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a / b);
    }
}

contract R19_pow {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.pow(x, y);
    }
}

contract T19_pow {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.pow(b));
    }
}

contract R19_mulDown {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.mulDown(x, y);
    }
}

contract T19_mulDown {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.mulDown(b));
    }
}

contract R19_mulUp {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.mulUp(x, y);
    }
}

contract T19_mulUp {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.mulUp(b));
    }
}

contract R19_divDown {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.divDown(x, y);
    }
}

contract T19_divDown {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.divDown(b));
    }
}

contract R19_divUp {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.divUp(x, y);
    }
}

contract T19_divUp {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.divUp(b));
    }
}

contract R19_min {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.min(x, y);
    }
}

contract T19_min {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.min(b));
    }
}

contract R19_max {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.max(x, y);
    }
}

contract T19_max {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.max(b));
    }
}

contract R19_avg {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.avg(x, y);
    }
}

contract T19_avg {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.avg(b));
    }
}

contract R19_dist {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.dist(x, y);
    }
}

contract T19_dist {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.dist(b));
    }
}

contract R19_zeroFloorSub {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.zeroFloorSub(x, y);
    }
}

contract T19_zeroFloorSub {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.zeroFloorSub(b));
    }
}

contract R19_gavg {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.gavg(x, y);
    }
}

contract T19_gavg {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.gavg(b));
    }
}

contract R19_hypot {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.hypot(x, y);
    }
}

contract T19_hypot {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.hypot(b));
    }
}

contract R19_powu {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.powu(x, y);
    }
}

contract T19_powu {
    function f(BL19 a, int256 y, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.powu(y));
    }
}

contract R19_compound {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.compound(x, y);
    }
}

contract T19_compound {
    function f(BL19 a, int256 y, int256) external pure returns (int256 r) {
        r = BL19.unwrap(a.compound(y));
    }
}

contract R19_clamp {
    function f(int256 x, int256 y, int256 z) external pure returns (int256 r) {
        r = BL19Lib.clamp(x, y, z);
    }
}

contract T19_clamp {
    function f(BL19 a, BL19 b, BL19 c) external pure returns (int256 r) {
        r = BL19.unwrap(a.clamp(b, c));
    }
}

contract R19_lerp {
    function f(int256 x, int256 y, int256 z) external pure returns (int256 r) {
        r = BL19Lib.lerp(x, y, z);
    }
}

contract T19_lerp {
    function f(BL19 a, BL19 b, BL19 c) external pure returns (int256 r) {
        r = BL19.unwrap(a.lerp(b, c));
    }
}

contract R19_cmp {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.cmp(x, y);
    }
}

contract T19_cmp {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = a.cmp(b);
    }
}

contract R19_lt {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.lt(x, y) != 0 ? int256(1) : int256(0);
    }
}

contract T19_lt {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = a < b ? int256(1) : int256(0);
    }
}

contract R19_gt {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.lt(y, x) != 0 ? int256(1) : int256(0);
    }
}

contract T19_gt {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = a > b ? int256(1) : int256(0);
    }
}

contract R19_le {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.lt(y, x) == 0 ? int256(1) : int256(0);
    }
}

contract T19_le {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = a <= b ? int256(1) : int256(0);
    }
}

contract R19_ge {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.lt(x, y) == 0 ? int256(1) : int256(0);
    }
}

contract T19_ge {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = a >= b ? int256(1) : int256(0);
    }
}

contract R19_eq {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.eq(x, y) != 0 ? int256(1) : int256(0);
    }
}

contract T19_eq {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = a == b ? int256(1) : int256(0);
    }
}

contract R19_ne {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = BL19Lib.eq(x, y) == 0 ? int256(1) : int256(0);
    }
}

contract T19_ne {
    function f(BL19 a, BL19 b, int256) external pure returns (int256 r) {
        r = a != b ? int256(1) : int256(0);
    }
}

contract R19_fromUint {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.fromUint(uint256(x));
    }
}

contract T19_fromUint {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(bl19FromUint(uint256(x)));
    }
}

contract R19_fromUintDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.fromUintDown(uint256(x));
    }
}

contract T19_fromUintDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(bl19FromUintDown(uint256(x)));
    }
}

contract R19_fromUintUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.fromUintUp(uint256(x));
    }
}

contract T19_fromUintUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(bl19FromUintUp(uint256(x)));
    }
}

contract R19_fromFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.fromFixed18(x);
    }
}

contract T19_fromFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(bl19FromFixed18(x));
    }
}

contract R19_fromBL127 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.fromBL127(x);
    }
}

contract T19_fromBL127 {
    function f(BL127 x, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(toBL19(x));
    }
}

contract R19_toBL127 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.toBL127(x);
    }
}

contract T19_toBL127 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = BL127.unwrap(a.toBL127());
    }
}

contract R19_toFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.toFixed18(x);
    }
}

contract T19_toFixed18 {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18();
    }
}

contract R19_toFixed18Down {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.toFixed18Down(x);
    }
}

contract T19_toFixed18Down {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18Down();
    }
}

contract R19_toFixed18Up {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.toFixed18Up(x);
    }
}

contract T19_toFixed18Up {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18Up();
    }
}

contract R19_toIntDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.toIntDown(x);
    }
}

contract T19_toIntDown {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = a.toIntDown();
    }
}

contract R19_toIntUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.toIntUp(x);
    }
}

contract T19_toIntUp {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = a.toIntUp();
    }
}

contract R19_toUintDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = int256(BL19Lib.toUintDown(x));
    }
}

contract T19_toUintDown {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toUintDown());
    }
}

contract R19_toUintUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = int256(BL19Lib.toUintUp(x));
    }
}

contract T19_toUintUp {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toUintUp());
    }
}

contract R19_fromWad {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        if (uint256(x) > uint256(type(int256).max)) revert BL19Lib.Overflow();
        r = BL19Lib.fromFixed18(x);
    }
}

contract T19_fromWad {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(bl19FromWad(uint256(x)));
    }
}

contract R19_toWadDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.toFixed18Down(x);
        if (r < 0) revert BL19Lib.OutOfRange();
    }
}

contract T19_toWadDown {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toWadDown());
    }
}

contract R19_toWadUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19Lib.toFixed18Up(x);
        if (r < 0) revert BL19Lib.OutOfRange();
    }
}

contract T19_toWadUp {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toWadUp());
    }
}

contract R19_fromInt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = x >= 0
            ? BL19Lib.fromUint(uint256(x))
            : BL19Lib.sub(0, BL19Lib.fromUint(x == type(int256).min ? uint256(1) << 255 : uint256(-x)));
    }
}

contract T19_fromInt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = BL19.unwrap(bl19FromInt(x));
    }
}

contract R19_unwrap {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = x;
    }
}

contract T19_unwrap {
    function f(BL19 a, int256, int256) external pure returns (int256 r) {
        r = a.unwrap();
    }
}

/// @title Typed19
/// @notice contracts/src/bl19/BL19Type.sol adds nothing to BL19Lib: the
///         same three checks as test/typed/Typed127.t.sol (testFuzz_same,
///         test_gas with TYPED|bl19|op|raw|typed lines, test_coversEveryOp),
///         plus testFuzz_order: the six comparison operators agree with
///         BL19Lib.cmp. The comparisons' raw form is BL19Lib.lt / eq read
///         as a bool, as a raw caller writes it. bl19FromInt is checked
///         against an independent formula (0 - |n|), so its gas is printed but
///         not compared. The file also imports BL127Type into the same scope,
///         ONE aliased, as a caller holding both types does.
contract Typed19 is Test {
    struct Op {
        bytes32 name;
        bytes kinds; // v BL19, f BL127 word, i int256, u uint256 (one char per argument)
        int256[3] typ; // a typical input, in domain
        bool same; // raw is the same call, so the gas must match
        string rawC; // the two contracts
        string typedC;
    }

    int256 constant O = BL19Lib.ONE;
    bytes32 constant NA = keccak256(abi.encodeWithSignature("Error(string)", "na"));

    // ---- the two forms of every op ---------------------------------------

    function raw(bytes32 op, int256 x, int256 y, int256 z) external pure returns (int256 r) {
        (z);
        if (op == "sqrt") {
            r = BL19Lib.sqrt(x);
        } else if (op == "exp") {
            r = BL19Lib.exp(x);
        } else if (op == "ln") {
            r = BL19Lib.ln(x);
        } else if (op == "log1p") {
            r = BL19Lib.log1p(x);
        } else if (op == "expm1") {
            r = BL19Lib.expm1(x);
        } else if (op == "erf") {
            r = BL19Lib.erf(x);
        } else if (op == "erfc") {
            r = BL19Lib.erfc(x);
        } else if (op == "normCdf") {
            r = BL19Lib.normCdf(x);
        } else if (op == "lambertW0") {
            r = BL19Lib.lambertW0(x);
        } else if (op == "lambertWm1") {
            r = BL19Lib.lambertWm1(x);
        } else if (op == "abs") {
            r = BL19Lib.abs(x);
        } else if (op == "sign") {
            r = BL19Lib.sign(x);
        } else if (op == "floor") {
            r = BL19Lib.floor(x);
        } else if (op == "ceil") {
            r = BL19Lib.ceil(x);
        } else if (op == "inv") {
            r = BL19Lib.inv(x);
        } else if (op == "frac") {
            r = BL19Lib.frac(x);
        } else if (op == "round") {
            r = BL19Lib.round(x);
        } else if (op == "log2Up") {
            r = BL19Lib.log2Up(x);
        } else if (op == "factorial") {
            r = BL19Lib.factorial(x);
        } else if (op == "cbrt") {
            r = BL19Lib.cbrt(x);
        } else if (op == "exp2") {
            r = BL19Lib.exp2(x);
        } else if (op == "exp10") {
            r = BL19Lib.exp10(x);
        } else if (op == "log2") {
            r = BL19Lib.log2(x);
        } else if (op == "log10") {
            r = BL19Lib.log10(x);
        } else if (op == "sinh") {
            r = BL19Lib.sinh(x);
        } else if (op == "cosh") {
            r = BL19Lib.cosh(x);
        } else if (op == "tanh") {
            r = BL19Lib.tanh(x);
        } else if (op == "atanh") {
            r = BL19Lib.atanh(x);
        } else if (op == "neg") {
            r = BL19Lib.neg(x);
        } else if (op == "add") {
            r = BL19Lib.add(x, y);
        } else if (op == "sub") {
            r = BL19Lib.sub(x, y);
        } else if (op == "mul") {
            r = BL19Lib.mul(x, y);
        } else if (op == "div") {
            r = BL19Lib.div(x, y);
        } else if (op == "pow") {
            r = BL19Lib.pow(x, y);
        } else if (op == "mulDown") {
            r = BL19Lib.mulDown(x, y);
        } else if (op == "mulUp") {
            r = BL19Lib.mulUp(x, y);
        } else if (op == "divDown") {
            r = BL19Lib.divDown(x, y);
        } else if (op == "divUp") {
            r = BL19Lib.divUp(x, y);
        } else if (op == "min") {
            r = BL19Lib.min(x, y);
        } else if (op == "max") {
            r = BL19Lib.max(x, y);
        } else if (op == "avg") {
            r = BL19Lib.avg(x, y);
        } else if (op == "dist") {
            r = BL19Lib.dist(x, y);
        } else if (op == "zeroFloorSub") {
            r = BL19Lib.zeroFloorSub(x, y);
        } else if (op == "gavg") {
            r = BL19Lib.gavg(x, y);
        } else if (op == "hypot") {
            r = BL19Lib.hypot(x, y);
        } else if (op == "powu") {
            r = BL19Lib.powu(x, y);
        } else if (op == "compound") {
            r = BL19Lib.compound(x, y);
        } else if (op == "clamp") {
            r = BL19Lib.clamp(x, y, z);
        } else if (op == "lerp") {
            r = BL19Lib.lerp(x, y, z);
        } else if (op == "cmp") {
            r = BL19Lib.cmp(x, y);
        } else if (op == "lt") {
            r = BL19Lib.lt(x, y) != 0 ? int256(1) : int256(0);
        } else if (op == "gt") {
            r = BL19Lib.lt(y, x) != 0 ? int256(1) : int256(0);
        } else if (op == "le") {
            r = BL19Lib.lt(y, x) == 0 ? int256(1) : int256(0);
        } else if (op == "ge") {
            r = BL19Lib.lt(x, y) == 0 ? int256(1) : int256(0);
        } else if (op == "eq") {
            r = BL19Lib.eq(x, y) != 0 ? int256(1) : int256(0);
        } else if (op == "ne") {
            r = BL19Lib.eq(x, y) == 0 ? int256(1) : int256(0);
        } else if (op == "fromUint") {
            r = BL19Lib.fromUint(uint256(x));
        } else if (op == "fromUintDown") {
            r = BL19Lib.fromUintDown(uint256(x));
        } else if (op == "fromUintUp") {
            r = BL19Lib.fromUintUp(uint256(x));
        } else if (op == "fromFixed18") {
            r = BL19Lib.fromFixed18(x);
        } else if (op == "fromBL127") {
            r = BL19Lib.fromBL127(x);
        } else if (op == "toBL127") {
            r = BL19Lib.toBL127(x);
        } else if (op == "toFixed18") {
            r = BL19Lib.toFixed18(x);
        } else if (op == "toFixed18Down") {
            r = BL19Lib.toFixed18Down(x);
        } else if (op == "toFixed18Up") {
            r = BL19Lib.toFixed18Up(x);
        } else if (op == "toIntDown") {
            r = BL19Lib.toIntDown(x);
        } else if (op == "toIntUp") {
            r = BL19Lib.toIntUp(x);
        } else if (op == "toUintDown") {
            r = int256(BL19Lib.toUintDown(x));
        } else if (op == "toUintUp") {
            r = int256(BL19Lib.toUintUp(x));
        } else if (op == "fromWad") {
            if (uint256(x) > uint256(type(int256).max)) revert BL19Lib.Overflow();
            r = BL19Lib.fromFixed18(x);
        } else if (op == "toWadDown") {
            r = BL19Lib.toFixed18Down(x);
            if (r < 0) revert BL19Lib.OutOfRange();
        } else if (op == "toWadUp") {
            r = BL19Lib.toFixed18Up(x);
            if (r < 0) revert BL19Lib.OutOfRange();
        } else if (op == "fromInt") {
            r = x >= 0
                ? BL19Lib.fromUint(uint256(x))
                : BL19Lib.sub(0, BL19Lib.fromUint(x == type(int256).min ? uint256(1) << 255 : uint256(-x)));
        } else if (op == "unwrap") {
            r = x;
        } else {
            revert("na");
        }
    }

    function typed(bytes32 op, int256 x, int256 y, int256 z) external pure returns (int256 r) {
        (BL19 a, BL19 b, BL19 c) = (BL19.wrap(x), BL19.wrap(y), BL19.wrap(z));
        (a, b, c);
        if (op == "sqrt") r = BL19.unwrap(a.sqrt());
        else if (op == "exp") r = BL19.unwrap(a.exp());
        else if (op == "ln") r = BL19.unwrap(a.ln());
        else if (op == "log1p") r = BL19.unwrap(a.log1p());
        else if (op == "expm1") r = BL19.unwrap(a.expm1());
        else if (op == "erf") r = BL19.unwrap(a.erf());
        else if (op == "erfc") r = BL19.unwrap(a.erfc());
        else if (op == "normCdf") r = BL19.unwrap(a.normCdf());
        else if (op == "lambertW0") r = BL19.unwrap(a.lambertW0());
        else if (op == "lambertWm1") r = BL19.unwrap(a.lambertWm1());
        else if (op == "abs") r = BL19.unwrap(a.abs());
        else if (op == "sign") r = BL19.unwrap(a.sign());
        else if (op == "floor") r = BL19.unwrap(a.floor());
        else if (op == "ceil") r = BL19.unwrap(a.ceil());
        else if (op == "inv") r = BL19.unwrap(a.inv());
        else if (op == "frac") r = BL19.unwrap(a.frac());
        else if (op == "round") r = BL19.unwrap(a.round());
        else if (op == "log2Up") r = BL19.unwrap(a.log2Up());
        else if (op == "factorial") r = BL19.unwrap(a.factorial());
        else if (op == "cbrt") r = BL19.unwrap(a.cbrt());
        else if (op == "exp2") r = BL19.unwrap(a.exp2());
        else if (op == "exp10") r = BL19.unwrap(a.exp10());
        else if (op == "log2") r = BL19.unwrap(a.log2());
        else if (op == "log10") r = BL19.unwrap(a.log10());
        else if (op == "sinh") r = BL19.unwrap(a.sinh());
        else if (op == "cosh") r = BL19.unwrap(a.cosh());
        else if (op == "tanh") r = BL19.unwrap(a.tanh());
        else if (op == "atanh") r = BL19.unwrap(a.atanh());
        else if (op == "neg") r = BL19.unwrap(-a);
        else if (op == "add") r = BL19.unwrap(a + b);
        else if (op == "sub") r = BL19.unwrap(a - b);
        else if (op == "mul") r = BL19.unwrap(a * b);
        else if (op == "div") r = BL19.unwrap(a / b);
        else if (op == "pow") r = BL19.unwrap(a.pow(b));
        else if (op == "mulDown") r = BL19.unwrap(a.mulDown(b));
        else if (op == "mulUp") r = BL19.unwrap(a.mulUp(b));
        else if (op == "divDown") r = BL19.unwrap(a.divDown(b));
        else if (op == "divUp") r = BL19.unwrap(a.divUp(b));
        else if (op == "min") r = BL19.unwrap(a.min(b));
        else if (op == "max") r = BL19.unwrap(a.max(b));
        else if (op == "avg") r = BL19.unwrap(a.avg(b));
        else if (op == "dist") r = BL19.unwrap(a.dist(b));
        else if (op == "zeroFloorSub") r = BL19.unwrap(a.zeroFloorSub(b));
        else if (op == "gavg") r = BL19.unwrap(a.gavg(b));
        else if (op == "hypot") r = BL19.unwrap(a.hypot(b));
        else if (op == "powu") r = BL19.unwrap(a.powu(y));
        else if (op == "compound") r = BL19.unwrap(a.compound(y));
        else if (op == "clamp") r = BL19.unwrap(a.clamp(b, c));
        else if (op == "lerp") r = BL19.unwrap(a.lerp(b, c));
        else if (op == "cmp") r = a.cmp(b);
        else if (op == "lt") r = a < b ? int256(1) : int256(0);
        else if (op == "gt") r = a > b ? int256(1) : int256(0);
        else if (op == "le") r = a <= b ? int256(1) : int256(0);
        else if (op == "ge") r = a >= b ? int256(1) : int256(0);
        else if (op == "eq") r = a == b ? int256(1) : int256(0);
        else if (op == "ne") r = a != b ? int256(1) : int256(0);
        else if (op == "fromUint") r = BL19.unwrap(bl19FromUint(uint256(x)));
        else if (op == "fromUintDown") r = BL19.unwrap(bl19FromUintDown(uint256(x)));
        else if (op == "fromUintUp") r = BL19.unwrap(bl19FromUintUp(uint256(x)));
        else if (op == "fromFixed18") r = BL19.unwrap(bl19FromFixed18(x));
        else if (op == "fromBL127") r = BL19.unwrap(toBL19(BL127.wrap(x)));
        else if (op == "toBL127") r = BL127.unwrap(a.toBL127());
        else if (op == "toFixed18") r = a.toFixed18();
        else if (op == "toFixed18Down") r = a.toFixed18Down();
        else if (op == "toFixed18Up") r = a.toFixed18Up();
        else if (op == "toIntDown") r = a.toIntDown();
        else if (op == "toIntUp") r = a.toIntUp();
        else if (op == "toUintDown") r = int256(a.toUintDown());
        else if (op == "toUintUp") r = int256(a.toUintUp());
        else if (op == "fromWad") r = BL19.unwrap(bl19FromWad(uint256(x)));
        else if (op == "toWadDown") r = int256(a.toWadDown());
        else if (op == "toWadUp") r = int256(a.toWadUp());
        else if (op == "fromInt") r = BL19.unwrap(bl19FromInt(x));
        else if (op == "unwrap") r = a.unwrap();
        else revert("na");
    }

    // ---- the table ---------------------------------------------------------

    function _i(int256 n) internal pure returns (int256) {
        return n >= 0 ? BL19Lib.fromUint(uint256(n)) : BL19Lib.neg(BL19Lib.fromUint(uint256(-n)));
    }

    function _q(int256 num, int256 den) internal pure returns (int256) {
        return BL19Lib.div(_i(num), _i(den));
    }

    function _q127(int256 num, int256 den) internal pure returns (int256) {
        return num * BL127Lib.ONE / den;
    }

    function _ops() internal pure returns (Op[] memory t) {
        t = new Op[](74);
        t[0] = Op("sqrt", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_sqrt", "T19_sqrt");
        t[1] = Op("exp", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_exp", "T19_exp");
        t[2] = Op("ln", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_ln", "T19_ln");
        t[3] = Op("log1p", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_log1p", "T19_log1p");
        t[4] = Op("expm1", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_expm1", "T19_expm1");
        t[5] = Op("erf", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_erf", "T19_erf");
        t[6] = Op("erfc", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_erfc", "T19_erfc");
        t[7] = Op("normCdf", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_normCdf", "T19_normCdf");
        t[8] = Op("lambertW0", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_lambertW0", "T19_lambertW0");
        t[9] = Op("lambertWm1", "v", [_q(-1, 4), int256(0), int256(0)], true, "R19_lambertWm1", "T19_lambertWm1");
        t[10] = Op("abs", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_abs", "T19_abs");
        t[11] = Op("sign", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_sign", "T19_sign");
        t[12] = Op("floor", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_floor", "T19_floor");
        t[13] = Op("ceil", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_ceil", "T19_ceil");
        t[14] = Op("inv", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_inv", "T19_inv");
        t[15] = Op("frac", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_frac", "T19_frac");
        t[16] = Op("round", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_round", "T19_round");
        t[17] = Op("log2Up", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_log2Up", "T19_log2Up");
        t[18] = Op("factorial", "v", [_q(5, 1), int256(0), int256(0)], true, "R19_factorial", "T19_factorial");
        t[19] = Op("cbrt", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_cbrt", "T19_cbrt");
        t[20] = Op("exp2", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_exp2", "T19_exp2");
        t[21] = Op("exp10", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_exp10", "T19_exp10");
        t[22] = Op("log2", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_log2", "T19_log2");
        t[23] = Op("log10", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_log10", "T19_log10");
        t[24] = Op("sinh", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_sinh", "T19_sinh");
        t[25] = Op("cosh", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_cosh", "T19_cosh");
        t[26] = Op("tanh", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_tanh", "T19_tanh");
        t[27] = Op("atanh", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_atanh", "T19_atanh");
        t[28] = Op("neg", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_neg", "T19_neg");
        t[29] = Op("add", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_add", "T19_add");
        t[30] = Op("sub", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_sub", "T19_sub");
        t[31] = Op("mul", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_mul", "T19_mul");
        t[32] = Op("div", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_div", "T19_div");
        t[33] = Op("pow", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_pow", "T19_pow");
        t[34] = Op("mulDown", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_mulDown", "T19_mulDown");
        t[35] = Op("mulUp", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_mulUp", "T19_mulUp");
        t[36] = Op("divDown", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_divDown", "T19_divDown");
        t[37] = Op("divUp", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_divUp", "T19_divUp");
        t[38] = Op("min", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_min", "T19_min");
        t[39] = Op("max", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_max", "T19_max");
        t[40] = Op("avg", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_avg", "T19_avg");
        t[41] = Op("dist", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_dist", "T19_dist");
        t[42] =
            Op("zeroFloorSub", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_zeroFloorSub", "T19_zeroFloorSub");
        t[43] = Op("gavg", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_gavg", "T19_gavg");
        t[44] = Op("hypot", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_hypot", "T19_hypot");
        t[45] = Op("powu", "vi", [_q(5, 4), int256(5), int256(0)], true, "R19_powu", "T19_powu");
        t[46] = Op("compound", "vi", [_q(1, 100), int256(12), int256(0)], true, "R19_compound", "T19_compound");
        t[47] = Op("clamp", "vvv", [_q(3, 4), _q(1, 4), _q(5, 4)], true, "R19_clamp", "T19_clamp");
        t[48] = Op("lerp", "vvv", [_q(1, 4), _q(5, 4), _q(3, 4)], true, "R19_lerp", "T19_lerp");
        t[49] = Op("cmp", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_cmp", "T19_cmp");
        t[50] = Op("lt", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_lt", "T19_lt");
        t[51] = Op("gt", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_gt", "T19_gt");
        t[52] = Op("le", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_le", "T19_le");
        t[53] = Op("ge", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_ge", "T19_ge");
        t[54] = Op("eq", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_eq", "T19_eq");
        t[55] = Op("ne", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R19_ne", "T19_ne");
        t[56] = Op("fromUint", "u", [int256(7), int256(0), int256(0)], true, "R19_fromUint", "T19_fromUint");
        t[57] =
            Op("fromUintDown", "u", [int256(7), int256(0), int256(0)], true, "R19_fromUintDown", "T19_fromUintDown");
        t[58] = Op("fromUintUp", "u", [int256(7), int256(0), int256(0)], true, "R19_fromUintUp", "T19_fromUintUp");
        t[59] = Op(
            "fromFixed18", "i", [int256(1.5e18), int256(0), int256(0)], true, "R19_fromFixed18", "T19_fromFixed18"
        );
        t[60] = Op("fromBL127", "f", [_q127(3, 4), int256(0), int256(0)], true, "R19_fromBL127", "T19_fromBL127");
        t[61] = Op("toBL127", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_toBL127", "T19_toBL127");
        t[62] = Op("toFixed18", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_toFixed18", "T19_toFixed18");
        t[63] = Op(
            "toFixed18Down", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_toFixed18Down", "T19_toFixed18Down"
        );
        t[64] = Op("toFixed18Up", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_toFixed18Up", "T19_toFixed18Up");
        t[65] = Op("toIntDown", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_toIntDown", "T19_toIntDown");
        t[66] = Op("toIntUp", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_toIntUp", "T19_toIntUp");
        t[67] = Op("toUintDown", "v", [_q(7, 4), int256(0), int256(0)], true, "R19_toUintDown", "T19_toUintDown");
        t[68] = Op("toUintUp", "v", [_q(7, 4), int256(0), int256(0)], true, "R19_toUintUp", "T19_toUintUp");
        t[69] = Op("fromWad", "u", [int256(1.5e18), int256(0), int256(0)], true, "R19_fromWad", "T19_fromWad");
        t[70] = Op("toWadDown", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_toWadDown", "T19_toWadDown");
        t[71] = Op("toWadUp", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_toWadUp", "T19_toWadUp");
        t[72] = Op("fromInt", "i", [int256(-7), int256(0), int256(0)], false, "R19_fromInt", "T19_fromInt");
        t[73] = Op("unwrap", "v", [_q(3, 4), int256(0), int256(0)], true, "R19_unwrap", "T19_unwrap");
    }

    // ---- inputs ------------------------------------------------------------

    /// A 127.128 word: as Typed127 shapes it.
    function _f(int256 x, uint8 s) internal pure returns (int256) {
        if (s >= 8) return x >> (s - 8);
        int256[8] memory sp = [
            int256(0),
            BL127Lib.ONE,
            -BL127Lib.ONE,
            BL127Lib.PI,
            type(int256).max,
            type(int256).min,
            int256(1),
            int256(-1)
        ];
        return sp[s];
    }

    /// An BL19 word. s < 16: a special (zero, one, pi, the extremes of the
    /// format, a word that is not a number, the raw fuzzed word, ...);
    /// s < 136: an BL127 value, every magnitude from 2^127 down to 2^-128;
    /// else the fuzzed word with its exponent moved to within 2^±512 of one.
    function _v(int256 x, uint8 s) internal pure returns (int256) {
        if (s >= 136) {
            uint256 w = uint256(x);
            uint256 e = 0x3ffff + ((w >> 236) & 0x3ff) - 512;
            return int256((w & ~(uint256(0x7ffff) << 236)) | (e << 236));
        }
        if (s >= 16) return BL19Lib.fromBL127(x >> ((s - 16) * 2));
        int256[16] memory sp = [
            int256(0),
            O,
            BL19Lib.neg(O),
            BL19Lib.PI,
            BL19Lib.neg(BL19Lib.PI),
            int256(1) << 236,
            type(int256).max,
            type(int256).min | type(int256).max,
            int256(1),
            x,
            BL19Lib.div(O, _i(2)),
            _i(20367),
            _q(-367879441171442321, 1e18),
            _i(2),
            _i(34),
            BL19Lib.fromBL127(1)
        ];
        return sp[s];
    }

    function _arg(bytes memory kinds, uint256 k, int256 x, uint8 s) internal pure returns (int256) {
        if (k >= kinds.length) return 0;
        bytes1 c = kinds[k];
        if (c == "v") return _v(x, s);
        if (c == "f") return _f(x, s);
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

    /// The six operators and BL19Lib.cmp on the same pair (reverts if
    /// either word is not a number).
    function order(int256 x, int256 y) external pure returns (int256 c, bool[6] memory r) {
        (BL19 a, BL19 b) = (BL19.wrap(x), BL19.wrap(y));
        c = BL19Lib.cmp(x, y);
        r = [a < b, a > b, a <= b, a >= b, a == b, a != b];
    }

    function testFuzz_order(int256 x, uint8 sx, int256 y, uint8 sy, bool same) public view {
        (int256 a, int256 b) = (_v(x, sx), _v(y, sy));
        if (same) b = a;
        try this.order(a, b) returns (int256 c, bool[6] memory r) {
            assertEq(r[0], c < 0);
            assertEq(r[1], c > 0);
            assertEq(r[2], c <= 0);
            assertEq(r[3], c >= 0);
            assertEq(r[4], c == 0);
            assertEq(r[5], c != 0);
        } catch (bytes memory err) {
            assertEq(err, abi.encodeWithSelector(BL19Lib.OutOfRange.selector));
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
            console.log(string.concat("TYPED|bl19|", _name(t[i].name), "|", vm.toString(gR), "|", vm.toString(gT)));
            if (!t[i].same) continue;
            uint256 d = gT > gR ? gT - gR : gR - gT;
            if (d > worst) worst = d;
            assertApproxEqAbs(gT, gR, tol, _name(t[i].name));
        }
        console.log(string.concat("TYPED|bl19|worst|", vm.toString(worst)));
    }

    function test_coversEveryOp() public view {
        string[] memory names =
            abi.decode(vm.parseJson(vm.readFile("contracts/src/bl19/ops.json"), ".ops[*].name"), (string[]));
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
        assertEq(BL19.unwrap(ONE), BL19Lib.ONE);
        assertEq(BL19.unwrap(PI), BL19Lib.PI);
        assertEq(BL19.unwrap(bl19(42)), 42);
        assertEq(bl19(42).unwrap(), 42);
        assertEq(BL19.unwrap(toBL19(ONE127)), BL19Lib.ONE);
        assertEq(BL127.unwrap(ONE.toBL127()), BL127Lib.ONE);
    }

    function test_example() public pure {
        BL19 b = bl19FromWad(1.5e18) * ONE.exp(); // 1.5 e
        assertEq(BL19.unwrap(b), BL19Lib.mul(BL19Lib.fromFixed18(1.5e18), BL19Lib.exp(BL19Lib.ONE)));
        assertTrue(b > bl19FromInt(4) && b < bl19FromInt(5));
        assertEq(b.toIntDown(), 4);
        assertEq(b.toUintUp(), 5);
        BL127 n = b.toBL127();
        assertTrue(BL127.unwrap(n) > BL127.unwrap(bl127FromInt(4)));
        assertTrue(toBL19(n) <= b + bl19FromFixed18(1) && -toBL19(n) < ONE);
        assertEq(bl19FromInt(-7).toIntDown(), -7);
        assertEq(bl19FromInt(type(int256).min).toIntDown(), type(int256).min);
        assertEq(BL127.unwrap(bl127(5)), 5);
    }
}

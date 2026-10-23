// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Test} from "forge-std/Test.sol";
import {console} from "forge-std/console.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP256Lib} from "../../contracts/src/fp256/FP256Lib.sol";
import {FP127, fp127, fp127FromInt, ONE as ONE127} from "../../contracts/src/fp127/FP127Type.sol";
import "../../contracts/src/fp256/FP256Type.sol";

// One contract per op and form, f(x, y, z) the op alone, as a caller's own
// contract would hold it: R256_<op> calls FP256Lib, T256_<op> the typed API.
// test_gas compares their call gas. Every op of contracts/src/fp256/ops.json
// has a pair, a row in _ops() and a line in raw() and typed()
// (test_coversEveryOp checks the table).

contract R256_sqrt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.sqrt(x);
    }
}

contract T256_sqrt {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.sqrt());
    }
}

contract R256_exp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.exp(x);
    }
}

contract T256_exp {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.exp());
    }
}

contract R256_ln {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.ln(x);
    }
}

contract T256_ln {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.ln());
    }
}

contract R256_log1p {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.log1p(x);
    }
}

contract T256_log1p {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.log1p());
    }
}

contract R256_expm1 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.expm1(x);
    }
}

contract T256_expm1 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.expm1());
    }
}

contract R256_erf {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.erf(x);
    }
}

contract T256_erf {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.erf());
    }
}

contract R256_erfc {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.erfc(x);
    }
}

contract T256_erfc {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.erfc());
    }
}

contract R256_normCdf {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.normCdf(x);
    }
}

contract T256_normCdf {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.normCdf());
    }
}

contract R256_lambertW0 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.lambertW0(x);
    }
}

contract T256_lambertW0 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.lambertW0());
    }
}

contract R256_lambertWm1 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.lambertWm1(x);
    }
}

contract T256_lambertWm1 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.lambertWm1());
    }
}

contract R256_abs {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.abs(x);
    }
}

contract T256_abs {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.abs());
    }
}

contract R256_sign {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.sign(x);
    }
}

contract T256_sign {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.sign());
    }
}

contract R256_floor {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.floor(x);
    }
}

contract T256_floor {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.floor());
    }
}

contract R256_ceil {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.ceil(x);
    }
}

contract T256_ceil {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.ceil());
    }
}

contract R256_inv {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.inv(x);
    }
}

contract T256_inv {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.inv());
    }
}

contract R256_frac {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.frac(x);
    }
}

contract T256_frac {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.frac());
    }
}

contract R256_round {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.round(x);
    }
}

contract T256_round {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.round());
    }
}

contract R256_log2Up {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.log2Up(x);
    }
}

contract T256_log2Up {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.log2Up());
    }
}

contract R256_factorial {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.factorial(x);
    }
}

contract T256_factorial {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.factorial());
    }
}

contract R256_cbrt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.cbrt(x);
    }
}

contract T256_cbrt {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.cbrt());
    }
}

contract R256_exp2 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.exp2(x);
    }
}

contract T256_exp2 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.exp2());
    }
}

contract R256_exp10 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.exp10(x);
    }
}

contract T256_exp10 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.exp10());
    }
}

contract R256_log2 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.log2(x);
    }
}

contract T256_log2 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.log2());
    }
}

contract R256_log10 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.log10(x);
    }
}

contract T256_log10 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.log10());
    }
}

contract R256_sinh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.sinh(x);
    }
}

contract T256_sinh {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.sinh());
    }
}

contract R256_cosh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.cosh(x);
    }
}

contract T256_cosh {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.cosh());
    }
}

contract R256_tanh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.tanh(x);
    }
}

contract T256_tanh {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.tanh());
    }
}

contract R256_atanh {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.atanh(x);
    }
}

contract T256_atanh {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.atanh());
    }
}

contract R256_neg {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.neg(x);
    }
}

contract T256_neg {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(-a);
    }
}

contract R256_add {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.add(x, y);
    }
}

contract T256_add {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a + b);
    }
}

contract R256_sub {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.sub(x, y);
    }
}

contract T256_sub {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a - b);
    }
}

contract R256_mul {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.mul(x, y);
    }
}

contract T256_mul {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a * b);
    }
}

contract R256_div {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.div(x, y);
    }
}

contract T256_div {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a / b);
    }
}

contract R256_pow {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.pow(x, y);
    }
}

contract T256_pow {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.pow(b));
    }
}

contract R256_mulDown {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.mulDown(x, y);
    }
}

contract T256_mulDown {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.mulDown(b));
    }
}

contract R256_mulUp {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.mulUp(x, y);
    }
}

contract T256_mulUp {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.mulUp(b));
    }
}

contract R256_divDown {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.divDown(x, y);
    }
}

contract T256_divDown {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.divDown(b));
    }
}

contract R256_divUp {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.divUp(x, y);
    }
}

contract T256_divUp {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.divUp(b));
    }
}

contract R256_min {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.min(x, y);
    }
}

contract T256_min {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.min(b));
    }
}

contract R256_max {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.max(x, y);
    }
}

contract T256_max {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.max(b));
    }
}

contract R256_avg {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.avg(x, y);
    }
}

contract T256_avg {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.avg(b));
    }
}

contract R256_dist {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.dist(x, y);
    }
}

contract T256_dist {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.dist(b));
    }
}

contract R256_zeroFloorSub {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.zeroFloorSub(x, y);
    }
}

contract T256_zeroFloorSub {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.zeroFloorSub(b));
    }
}

contract R256_gavg {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.gavg(x, y);
    }
}

contract T256_gavg {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.gavg(b));
    }
}

contract R256_hypot {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.hypot(x, y);
    }
}

contract T256_hypot {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.hypot(b));
    }
}

contract R256_powu {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.powu(x, y);
    }
}

contract T256_powu {
    function f(FP256 a, int256 y, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.powu(y));
    }
}

contract R256_compound {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.compound(x, y);
    }
}

contract T256_compound {
    function f(FP256 a, int256 y, int256) external pure returns (int256 r) {
        r = FP256.unwrap(a.compound(y));
    }
}

contract R256_clamp {
    function f(int256 x, int256 y, int256 z) external pure returns (int256 r) {
        r = FP256Lib.clamp(x, y, z);
    }
}

contract T256_clamp {
    function f(FP256 a, FP256 b, FP256 c) external pure returns (int256 r) {
        r = FP256.unwrap(a.clamp(b, c));
    }
}

contract R256_lerp {
    function f(int256 x, int256 y, int256 z) external pure returns (int256 r) {
        r = FP256Lib.lerp(x, y, z);
    }
}

contract T256_lerp {
    function f(FP256 a, FP256 b, FP256 c) external pure returns (int256 r) {
        r = FP256.unwrap(a.lerp(b, c));
    }
}

contract R256_cmp {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.cmp(x, y);
    }
}

contract T256_cmp {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = a.cmp(b);
    }
}

contract R256_lt {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.lt(x, y) != 0 ? int256(1) : int256(0);
    }
}

contract T256_lt {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = a < b ? int256(1) : int256(0);
    }
}

contract R256_gt {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.lt(y, x) != 0 ? int256(1) : int256(0);
    }
}

contract T256_gt {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = a > b ? int256(1) : int256(0);
    }
}

contract R256_le {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.lt(y, x) == 0 ? int256(1) : int256(0);
    }
}

contract T256_le {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = a <= b ? int256(1) : int256(0);
    }
}

contract R256_ge {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.lt(x, y) == 0 ? int256(1) : int256(0);
    }
}

contract T256_ge {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = a >= b ? int256(1) : int256(0);
    }
}

contract R256_eq {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.eq(x, y) != 0 ? int256(1) : int256(0);
    }
}

contract T256_eq {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = a == b ? int256(1) : int256(0);
    }
}

contract R256_ne {
    function f(int256 x, int256 y, int256) external pure returns (int256 r) {
        r = FP256Lib.eq(x, y) == 0 ? int256(1) : int256(0);
    }
}

contract T256_ne {
    function f(FP256 a, FP256 b, int256) external pure returns (int256 r) {
        r = a != b ? int256(1) : int256(0);
    }
}

contract R256_fromUint {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.fromUint(uint256(x));
    }
}

contract T256_fromUint {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(fp256FromUint(uint256(x)));
    }
}

contract R256_fromUintDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.fromUintDown(uint256(x));
    }
}

contract T256_fromUintDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(fp256FromUintDown(uint256(x)));
    }
}

contract R256_fromUintUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.fromUintUp(uint256(x));
    }
}

contract T256_fromUintUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(fp256FromUintUp(uint256(x)));
    }
}

contract R256_fromFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.fromFixed18(x);
    }
}

contract T256_fromFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(fp256FromFixed18(x));
    }
}

contract R256_fromFP127 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.fromFP127(x);
    }
}

contract T256_fromFP127 {
    function f(FP127 x, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(toFP256(x));
    }
}

contract R256_toFP127 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.toFP127(x);
    }
}

contract T256_toFP127 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = FP127.unwrap(a.toFP127());
    }
}

contract R256_toFixed18 {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.toFixed18(x);
    }
}

contract T256_toFixed18 {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18();
    }
}

contract R256_toFixed18Down {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.toFixed18Down(x);
    }
}

contract T256_toFixed18Down {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18Down();
    }
}

contract R256_toFixed18Up {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.toFixed18Up(x);
    }
}

contract T256_toFixed18Up {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = a.toFixed18Up();
    }
}

contract R256_toIntDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.toIntDown(x);
    }
}

contract T256_toIntDown {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = a.toIntDown();
    }
}

contract R256_toIntUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.toIntUp(x);
    }
}

contract T256_toIntUp {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = a.toIntUp();
    }
}

contract R256_toUintDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = int256(FP256Lib.toUintDown(x));
    }
}

contract T256_toUintDown {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toUintDown());
    }
}

contract R256_toUintUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = int256(FP256Lib.toUintUp(x));
    }
}

contract T256_toUintUp {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toUintUp());
    }
}

contract R256_fromWad {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        if (uint256(x) > uint256(type(int256).max)) revert FP256Lib.Overflow();
        r = FP256Lib.fromFixed18(x);
    }
}

contract T256_fromWad {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(fp256FromWad(uint256(x)));
    }
}

contract R256_toWadDown {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.toFixed18Down(x);
        if (r < 0) revert FP256Lib.OutOfRange();
    }
}

contract T256_toWadDown {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toWadDown());
    }
}

contract R256_toWadUp {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256Lib.toFixed18Up(x);
        if (r < 0) revert FP256Lib.OutOfRange();
    }
}

contract T256_toWadUp {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = int256(a.toWadUp());
    }
}

contract R256_fromInt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = x >= 0
            ? FP256Lib.fromUint(uint256(x))
            : FP256Lib.sub(0, FP256Lib.fromUint(x == type(int256).min ? uint256(1) << 255 : uint256(-x)));
    }
}

contract T256_fromInt {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = FP256.unwrap(fp256FromInt(x));
    }
}

contract R256_unwrap {
    function f(int256 x, int256, int256) external pure returns (int256 r) {
        r = x;
    }
}

contract T256_unwrap {
    function f(FP256 a, int256, int256) external pure returns (int256 r) {
        r = a.unwrap();
    }
}

/// @title Typed256
/// @notice contracts/src/fp256/FP256Type.sol adds nothing to FP256Lib: the
///         same three checks as test/typed/Typed127.t.sol (testFuzz_same,
///         test_gas with TYPED|fp256|op|raw|typed lines, test_coversEveryOp),
///         plus testFuzz_order: the six comparison operators agree with
///         FP256Lib.cmp. The comparisons' raw form is FP256Lib.lt / eq read
///         as a bool, as a raw caller writes it. fp256FromInt is checked
///         against an independent formula (0 - |n|), so its gas is printed but
///         not compared. The file also imports FP127Type into the same scope,
///         ONE aliased, as a caller holding both types does.
contract Typed256 is Test {
    struct Op {
        bytes32 name;
        bytes kinds; // v FP256, f FP127 word, i int256, u uint256 (one char per argument)
        int256[3] typ; // a typical input, in domain
        bool same; // raw is the same call, so the gas must match
        string rawC; // the two contracts
        string typedC;
    }

    int256 constant O = FP256Lib.ONE;
    bytes32 constant NA = keccak256(abi.encodeWithSignature("Error(string)", "na"));

    // ---- the two forms of every op ---------------------------------------

    function raw(bytes32 op, int256 x, int256 y, int256 z) external pure returns (int256 r) {
        (z);
        if (op == "sqrt") {
            r = FP256Lib.sqrt(x);
        } else if (op == "exp") {
            r = FP256Lib.exp(x);
        } else if (op == "ln") {
            r = FP256Lib.ln(x);
        } else if (op == "log1p") {
            r = FP256Lib.log1p(x);
        } else if (op == "expm1") {
            r = FP256Lib.expm1(x);
        } else if (op == "erf") {
            r = FP256Lib.erf(x);
        } else if (op == "erfc") {
            r = FP256Lib.erfc(x);
        } else if (op == "normCdf") {
            r = FP256Lib.normCdf(x);
        } else if (op == "lambertW0") {
            r = FP256Lib.lambertW0(x);
        } else if (op == "lambertWm1") {
            r = FP256Lib.lambertWm1(x);
        } else if (op == "abs") {
            r = FP256Lib.abs(x);
        } else if (op == "sign") {
            r = FP256Lib.sign(x);
        } else if (op == "floor") {
            r = FP256Lib.floor(x);
        } else if (op == "ceil") {
            r = FP256Lib.ceil(x);
        } else if (op == "inv") {
            r = FP256Lib.inv(x);
        } else if (op == "frac") {
            r = FP256Lib.frac(x);
        } else if (op == "round") {
            r = FP256Lib.round(x);
        } else if (op == "log2Up") {
            r = FP256Lib.log2Up(x);
        } else if (op == "factorial") {
            r = FP256Lib.factorial(x);
        } else if (op == "cbrt") {
            r = FP256Lib.cbrt(x);
        } else if (op == "exp2") {
            r = FP256Lib.exp2(x);
        } else if (op == "exp10") {
            r = FP256Lib.exp10(x);
        } else if (op == "log2") {
            r = FP256Lib.log2(x);
        } else if (op == "log10") {
            r = FP256Lib.log10(x);
        } else if (op == "sinh") {
            r = FP256Lib.sinh(x);
        } else if (op == "cosh") {
            r = FP256Lib.cosh(x);
        } else if (op == "tanh") {
            r = FP256Lib.tanh(x);
        } else if (op == "atanh") {
            r = FP256Lib.atanh(x);
        } else if (op == "neg") {
            r = FP256Lib.neg(x);
        } else if (op == "add") {
            r = FP256Lib.add(x, y);
        } else if (op == "sub") {
            r = FP256Lib.sub(x, y);
        } else if (op == "mul") {
            r = FP256Lib.mul(x, y);
        } else if (op == "div") {
            r = FP256Lib.div(x, y);
        } else if (op == "pow") {
            r = FP256Lib.pow(x, y);
        } else if (op == "mulDown") {
            r = FP256Lib.mulDown(x, y);
        } else if (op == "mulUp") {
            r = FP256Lib.mulUp(x, y);
        } else if (op == "divDown") {
            r = FP256Lib.divDown(x, y);
        } else if (op == "divUp") {
            r = FP256Lib.divUp(x, y);
        } else if (op == "min") {
            r = FP256Lib.min(x, y);
        } else if (op == "max") {
            r = FP256Lib.max(x, y);
        } else if (op == "avg") {
            r = FP256Lib.avg(x, y);
        } else if (op == "dist") {
            r = FP256Lib.dist(x, y);
        } else if (op == "zeroFloorSub") {
            r = FP256Lib.zeroFloorSub(x, y);
        } else if (op == "gavg") {
            r = FP256Lib.gavg(x, y);
        } else if (op == "hypot") {
            r = FP256Lib.hypot(x, y);
        } else if (op == "powu") {
            r = FP256Lib.powu(x, y);
        } else if (op == "compound") {
            r = FP256Lib.compound(x, y);
        } else if (op == "clamp") {
            r = FP256Lib.clamp(x, y, z);
        } else if (op == "lerp") {
            r = FP256Lib.lerp(x, y, z);
        } else if (op == "cmp") {
            r = FP256Lib.cmp(x, y);
        } else if (op == "lt") {
            r = FP256Lib.lt(x, y) != 0 ? int256(1) : int256(0);
        } else if (op == "gt") {
            r = FP256Lib.lt(y, x) != 0 ? int256(1) : int256(0);
        } else if (op == "le") {
            r = FP256Lib.lt(y, x) == 0 ? int256(1) : int256(0);
        } else if (op == "ge") {
            r = FP256Lib.lt(x, y) == 0 ? int256(1) : int256(0);
        } else if (op == "eq") {
            r = FP256Lib.eq(x, y) != 0 ? int256(1) : int256(0);
        } else if (op == "ne") {
            r = FP256Lib.eq(x, y) == 0 ? int256(1) : int256(0);
        } else if (op == "fromUint") {
            r = FP256Lib.fromUint(uint256(x));
        } else if (op == "fromUintDown") {
            r = FP256Lib.fromUintDown(uint256(x));
        } else if (op == "fromUintUp") {
            r = FP256Lib.fromUintUp(uint256(x));
        } else if (op == "fromFixed18") {
            r = FP256Lib.fromFixed18(x);
        } else if (op == "fromFP127") {
            r = FP256Lib.fromFP127(x);
        } else if (op == "toFP127") {
            r = FP256Lib.toFP127(x);
        } else if (op == "toFixed18") {
            r = FP256Lib.toFixed18(x);
        } else if (op == "toFixed18Down") {
            r = FP256Lib.toFixed18Down(x);
        } else if (op == "toFixed18Up") {
            r = FP256Lib.toFixed18Up(x);
        } else if (op == "toIntDown") {
            r = FP256Lib.toIntDown(x);
        } else if (op == "toIntUp") {
            r = FP256Lib.toIntUp(x);
        } else if (op == "toUintDown") {
            r = int256(FP256Lib.toUintDown(x));
        } else if (op == "toUintUp") {
            r = int256(FP256Lib.toUintUp(x));
        } else if (op == "fromWad") {
            if (uint256(x) > uint256(type(int256).max)) revert FP256Lib.Overflow();
            r = FP256Lib.fromFixed18(x);
        } else if (op == "toWadDown") {
            r = FP256Lib.toFixed18Down(x);
            if (r < 0) revert FP256Lib.OutOfRange();
        } else if (op == "toWadUp") {
            r = FP256Lib.toFixed18Up(x);
            if (r < 0) revert FP256Lib.OutOfRange();
        } else if (op == "fromInt") {
            r = x >= 0
                ? FP256Lib.fromUint(uint256(x))
                : FP256Lib.sub(0, FP256Lib.fromUint(x == type(int256).min ? uint256(1) << 255 : uint256(-x)));
        } else if (op == "unwrap") {
            r = x;
        } else {
            revert("na");
        }
    }

    function typed(bytes32 op, int256 x, int256 y, int256 z) external pure returns (int256 r) {
        (FP256 a, FP256 b, FP256 c) = (FP256.wrap(x), FP256.wrap(y), FP256.wrap(z));
        (a, b, c);
        if (op == "sqrt") r = FP256.unwrap(a.sqrt());
        else if (op == "exp") r = FP256.unwrap(a.exp());
        else if (op == "ln") r = FP256.unwrap(a.ln());
        else if (op == "log1p") r = FP256.unwrap(a.log1p());
        else if (op == "expm1") r = FP256.unwrap(a.expm1());
        else if (op == "erf") r = FP256.unwrap(a.erf());
        else if (op == "erfc") r = FP256.unwrap(a.erfc());
        else if (op == "normCdf") r = FP256.unwrap(a.normCdf());
        else if (op == "lambertW0") r = FP256.unwrap(a.lambertW0());
        else if (op == "lambertWm1") r = FP256.unwrap(a.lambertWm1());
        else if (op == "abs") r = FP256.unwrap(a.abs());
        else if (op == "sign") r = FP256.unwrap(a.sign());
        else if (op == "floor") r = FP256.unwrap(a.floor());
        else if (op == "ceil") r = FP256.unwrap(a.ceil());
        else if (op == "inv") r = FP256.unwrap(a.inv());
        else if (op == "frac") r = FP256.unwrap(a.frac());
        else if (op == "round") r = FP256.unwrap(a.round());
        else if (op == "log2Up") r = FP256.unwrap(a.log2Up());
        else if (op == "factorial") r = FP256.unwrap(a.factorial());
        else if (op == "cbrt") r = FP256.unwrap(a.cbrt());
        else if (op == "exp2") r = FP256.unwrap(a.exp2());
        else if (op == "exp10") r = FP256.unwrap(a.exp10());
        else if (op == "log2") r = FP256.unwrap(a.log2());
        else if (op == "log10") r = FP256.unwrap(a.log10());
        else if (op == "sinh") r = FP256.unwrap(a.sinh());
        else if (op == "cosh") r = FP256.unwrap(a.cosh());
        else if (op == "tanh") r = FP256.unwrap(a.tanh());
        else if (op == "atanh") r = FP256.unwrap(a.atanh());
        else if (op == "neg") r = FP256.unwrap(-a);
        else if (op == "add") r = FP256.unwrap(a + b);
        else if (op == "sub") r = FP256.unwrap(a - b);
        else if (op == "mul") r = FP256.unwrap(a * b);
        else if (op == "div") r = FP256.unwrap(a / b);
        else if (op == "pow") r = FP256.unwrap(a.pow(b));
        else if (op == "mulDown") r = FP256.unwrap(a.mulDown(b));
        else if (op == "mulUp") r = FP256.unwrap(a.mulUp(b));
        else if (op == "divDown") r = FP256.unwrap(a.divDown(b));
        else if (op == "divUp") r = FP256.unwrap(a.divUp(b));
        else if (op == "min") r = FP256.unwrap(a.min(b));
        else if (op == "max") r = FP256.unwrap(a.max(b));
        else if (op == "avg") r = FP256.unwrap(a.avg(b));
        else if (op == "dist") r = FP256.unwrap(a.dist(b));
        else if (op == "zeroFloorSub") r = FP256.unwrap(a.zeroFloorSub(b));
        else if (op == "gavg") r = FP256.unwrap(a.gavg(b));
        else if (op == "hypot") r = FP256.unwrap(a.hypot(b));
        else if (op == "powu") r = FP256.unwrap(a.powu(y));
        else if (op == "compound") r = FP256.unwrap(a.compound(y));
        else if (op == "clamp") r = FP256.unwrap(a.clamp(b, c));
        else if (op == "lerp") r = FP256.unwrap(a.lerp(b, c));
        else if (op == "cmp") r = a.cmp(b);
        else if (op == "lt") r = a < b ? int256(1) : int256(0);
        else if (op == "gt") r = a > b ? int256(1) : int256(0);
        else if (op == "le") r = a <= b ? int256(1) : int256(0);
        else if (op == "ge") r = a >= b ? int256(1) : int256(0);
        else if (op == "eq") r = a == b ? int256(1) : int256(0);
        else if (op == "ne") r = a != b ? int256(1) : int256(0);
        else if (op == "fromUint") r = FP256.unwrap(fp256FromUint(uint256(x)));
        else if (op == "fromUintDown") r = FP256.unwrap(fp256FromUintDown(uint256(x)));
        else if (op == "fromUintUp") r = FP256.unwrap(fp256FromUintUp(uint256(x)));
        else if (op == "fromFixed18") r = FP256.unwrap(fp256FromFixed18(x));
        else if (op == "fromFP127") r = FP256.unwrap(toFP256(FP127.wrap(x)));
        else if (op == "toFP127") r = FP127.unwrap(a.toFP127());
        else if (op == "toFixed18") r = a.toFixed18();
        else if (op == "toFixed18Down") r = a.toFixed18Down();
        else if (op == "toFixed18Up") r = a.toFixed18Up();
        else if (op == "toIntDown") r = a.toIntDown();
        else if (op == "toIntUp") r = a.toIntUp();
        else if (op == "toUintDown") r = int256(a.toUintDown());
        else if (op == "toUintUp") r = int256(a.toUintUp());
        else if (op == "fromWad") r = FP256.unwrap(fp256FromWad(uint256(x)));
        else if (op == "toWadDown") r = int256(a.toWadDown());
        else if (op == "toWadUp") r = int256(a.toWadUp());
        else if (op == "fromInt") r = FP256.unwrap(fp256FromInt(x));
        else if (op == "unwrap") r = a.unwrap();
        else revert("na");
    }

    // ---- the table ---------------------------------------------------------

    function _i(int256 n) internal pure returns (int256) {
        return n >= 0 ? FP256Lib.fromUint(uint256(n)) : FP256Lib.neg(FP256Lib.fromUint(uint256(-n)));
    }

    function _q(int256 num, int256 den) internal pure returns (int256) {
        return FP256Lib.div(_i(num), _i(den));
    }

    function _q127(int256 num, int256 den) internal pure returns (int256) {
        return num * FP127Lib.ONE / den;
    }

    function _ops() internal pure returns (Op[] memory t) {
        t = new Op[](74);
        t[0] = Op("sqrt", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_sqrt", "T256_sqrt");
        t[1] = Op("exp", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_exp", "T256_exp");
        t[2] = Op("ln", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_ln", "T256_ln");
        t[3] = Op("log1p", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_log1p", "T256_log1p");
        t[4] = Op("expm1", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_expm1", "T256_expm1");
        t[5] = Op("erf", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_erf", "T256_erf");
        t[6] = Op("erfc", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_erfc", "T256_erfc");
        t[7] = Op("normCdf", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_normCdf", "T256_normCdf");
        t[8] = Op("lambertW0", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_lambertW0", "T256_lambertW0");
        t[9] = Op("lambertWm1", "v", [_q(-1, 4), int256(0), int256(0)], true, "R256_lambertWm1", "T256_lambertWm1");
        t[10] = Op("abs", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_abs", "T256_abs");
        t[11] = Op("sign", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_sign", "T256_sign");
        t[12] = Op("floor", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_floor", "T256_floor");
        t[13] = Op("ceil", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_ceil", "T256_ceil");
        t[14] = Op("inv", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_inv", "T256_inv");
        t[15] = Op("frac", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_frac", "T256_frac");
        t[16] = Op("round", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_round", "T256_round");
        t[17] = Op("log2Up", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_log2Up", "T256_log2Up");
        t[18] = Op("factorial", "v", [_q(5, 1), int256(0), int256(0)], true, "R256_factorial", "T256_factorial");
        t[19] = Op("cbrt", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_cbrt", "T256_cbrt");
        t[20] = Op("exp2", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_exp2", "T256_exp2");
        t[21] = Op("exp10", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_exp10", "T256_exp10");
        t[22] = Op("log2", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_log2", "T256_log2");
        t[23] = Op("log10", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_log10", "T256_log10");
        t[24] = Op("sinh", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_sinh", "T256_sinh");
        t[25] = Op("cosh", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_cosh", "T256_cosh");
        t[26] = Op("tanh", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_tanh", "T256_tanh");
        t[27] = Op("atanh", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_atanh", "T256_atanh");
        t[28] = Op("neg", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_neg", "T256_neg");
        t[29] = Op("add", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_add", "T256_add");
        t[30] = Op("sub", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_sub", "T256_sub");
        t[31] = Op("mul", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_mul", "T256_mul");
        t[32] = Op("div", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_div", "T256_div");
        t[33] = Op("pow", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_pow", "T256_pow");
        t[34] = Op("mulDown", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_mulDown", "T256_mulDown");
        t[35] = Op("mulUp", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_mulUp", "T256_mulUp");
        t[36] = Op("divDown", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_divDown", "T256_divDown");
        t[37] = Op("divUp", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_divUp", "T256_divUp");
        t[38] = Op("min", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_min", "T256_min");
        t[39] = Op("max", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_max", "T256_max");
        t[40] = Op("avg", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_avg", "T256_avg");
        t[41] = Op("dist", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_dist", "T256_dist");
        t[42] =
            Op("zeroFloorSub", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_zeroFloorSub", "T256_zeroFloorSub");
        t[43] = Op("gavg", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_gavg", "T256_gavg");
        t[44] = Op("hypot", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_hypot", "T256_hypot");
        t[45] = Op("powu", "vi", [_q(5, 4), int256(5), int256(0)], true, "R256_powu", "T256_powu");
        t[46] = Op("compound", "vi", [_q(1, 100), int256(12), int256(0)], true, "R256_compound", "T256_compound");
        t[47] = Op("clamp", "vvv", [_q(3, 4), _q(1, 4), _q(5, 4)], true, "R256_clamp", "T256_clamp");
        t[48] = Op("lerp", "vvv", [_q(1, 4), _q(5, 4), _q(3, 4)], true, "R256_lerp", "T256_lerp");
        t[49] = Op("cmp", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_cmp", "T256_cmp");
        t[50] = Op("lt", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_lt", "T256_lt");
        t[51] = Op("gt", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_gt", "T256_gt");
        t[52] = Op("le", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_le", "T256_le");
        t[53] = Op("ge", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_ge", "T256_ge");
        t[54] = Op("eq", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_eq", "T256_eq");
        t[55] = Op("ne", "vv", [_q(5, 4), _q(3, 4), int256(0)], true, "R256_ne", "T256_ne");
        t[56] = Op("fromUint", "u", [int256(7), int256(0), int256(0)], true, "R256_fromUint", "T256_fromUint");
        t[57] =
            Op("fromUintDown", "u", [int256(7), int256(0), int256(0)], true, "R256_fromUintDown", "T256_fromUintDown");
        t[58] = Op("fromUintUp", "u", [int256(7), int256(0), int256(0)], true, "R256_fromUintUp", "T256_fromUintUp");
        t[59] = Op(
            "fromFixed18", "i", [int256(1.5e18), int256(0), int256(0)], true, "R256_fromFixed18", "T256_fromFixed18"
        );
        t[60] = Op("fromFP127", "f", [_q127(3, 4), int256(0), int256(0)], true, "R256_fromFP127", "T256_fromFP127");
        t[61] = Op("toFP127", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_toFP127", "T256_toFP127");
        t[62] = Op("toFixed18", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_toFixed18", "T256_toFixed18");
        t[63] = Op(
            "toFixed18Down", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_toFixed18Down", "T256_toFixed18Down"
        );
        t[64] = Op("toFixed18Up", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_toFixed18Up", "T256_toFixed18Up");
        t[65] = Op("toIntDown", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_toIntDown", "T256_toIntDown");
        t[66] = Op("toIntUp", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_toIntUp", "T256_toIntUp");
        t[67] = Op("toUintDown", "v", [_q(7, 4), int256(0), int256(0)], true, "R256_toUintDown", "T256_toUintDown");
        t[68] = Op("toUintUp", "v", [_q(7, 4), int256(0), int256(0)], true, "R256_toUintUp", "T256_toUintUp");
        t[69] = Op("fromWad", "u", [int256(1.5e18), int256(0), int256(0)], true, "R256_fromWad", "T256_fromWad");
        t[70] = Op("toWadDown", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_toWadDown", "T256_toWadDown");
        t[71] = Op("toWadUp", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_toWadUp", "T256_toWadUp");
        t[72] = Op("fromInt", "i", [int256(-7), int256(0), int256(0)], false, "R256_fromInt", "T256_fromInt");
        t[73] = Op("unwrap", "v", [_q(3, 4), int256(0), int256(0)], true, "R256_unwrap", "T256_unwrap");
    }

    // ---- inputs ------------------------------------------------------------

    /// A 127.128 word: as Typed127 shapes it.
    function _f(int256 x, uint8 s) internal pure returns (int256) {
        if (s >= 8) return x >> (s - 8);
        int256[8] memory sp = [
            int256(0),
            FP127Lib.ONE,
            -FP127Lib.ONE,
            FP127Lib.PI,
            type(int256).max,
            type(int256).min,
            int256(1),
            int256(-1)
        ];
        return sp[s];
    }

    /// An FP256 word. s < 16: a special (zero, one, pi, the extremes of the
    /// format, a word that is not a number, the raw fuzzed word, ...);
    /// s < 136: an FP127 value, every magnitude from 2^127 down to 2^-128;
    /// else the fuzzed word with its exponent moved to within 2^±512 of one.
    function _v(int256 x, uint8 s) internal pure returns (int256) {
        if (s >= 136) {
            uint256 w = uint256(x);
            uint256 e = 0x3ffff + ((w >> 236) & 0x3ff) - 512;
            return int256((w & ~(uint256(0x7ffff) << 236)) | (e << 236));
        }
        if (s >= 16) return FP256Lib.fromFP127(x >> ((s - 16) * 2));
        int256[16] memory sp = [
            int256(0),
            O,
            FP256Lib.neg(O),
            FP256Lib.PI,
            FP256Lib.neg(FP256Lib.PI),
            int256(1) << 236,
            type(int256).max,
            type(int256).min | type(int256).max,
            int256(1),
            x,
            FP256Lib.div(O, _i(2)),
            _i(20367),
            _q(-367879441171442321, 1e18),
            _i(2),
            _i(34),
            FP256Lib.fromFP127(1)
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

    /// The six operators and FP256Lib.cmp on the same pair (reverts if
    /// either word is not a number).
    function order(int256 x, int256 y) external pure returns (int256 c, bool[6] memory r) {
        (FP256 a, FP256 b) = (FP256.wrap(x), FP256.wrap(y));
        c = FP256Lib.cmp(x, y);
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
            assertEq(err, abi.encodeWithSelector(FP256Lib.OutOfRange.selector));
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
            console.log(string.concat("TYPED|fp256|", _name(t[i].name), "|", vm.toString(gR), "|", vm.toString(gT)));
            if (!t[i].same) continue;
            uint256 d = gT > gR ? gT - gR : gR - gT;
            if (d > worst) worst = d;
            assertApproxEqAbs(gT, gR, tol, _name(t[i].name));
        }
        console.log(string.concat("TYPED|fp256|worst|", vm.toString(worst)));
    }

    function test_coversEveryOp() public view {
        string[] memory names =
            abi.decode(vm.parseJson(vm.readFile("contracts/src/fp256/ops.json"), ".ops[*].name"), (string[]));
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
        assertEq(FP256.unwrap(ONE), FP256Lib.ONE);
        assertEq(FP256.unwrap(PI), FP256Lib.PI);
        assertEq(FP256.unwrap(fp256(42)), 42);
        assertEq(fp256(42).unwrap(), 42);
        assertEq(FP256.unwrap(toFP256(ONE127)), FP256Lib.ONE);
        assertEq(FP127.unwrap(ONE.toFP127()), FP127Lib.ONE);
    }

    function test_example() public pure {
        FP256 b = fp256FromWad(1.5e18) * ONE.exp(); // 1.5 e
        assertEq(FP256.unwrap(b), FP256Lib.mul(FP256Lib.fromFixed18(1.5e18), FP256Lib.exp(FP256Lib.ONE)));
        assertTrue(b > fp256FromInt(4) && b < fp256FromInt(5));
        assertEq(b.toIntDown(), 4);
        assertEq(b.toUintUp(), 5);
        FP127 n = b.toFP127();
        assertTrue(FP127.unwrap(n) > FP127.unwrap(fp127FromInt(4)));
        assertTrue(toFP256(n) <= b + fp256FromFixed18(1) && -toFP256(n) < ONE);
        assertEq(fp256FromInt(-7).toIntDown(), -7);
        assertEq(fp256FromInt(type(int256).min).toIntDown(), type(int256).min);
        assertEq(FP127.unwrap(fp127(5)), 5);
    }
}

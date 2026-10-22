// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP256Lib} from "../../contracts/src/fp256/FP256Lib.sol";

/// Random-input accuracy sweep: runs each op of the inline libraries on the seeded
/// inputs scripts/sweep/sweep.py writes to cache/sweep/<lib>_<op>.json and writes one
/// result word (or "R" + revert data) per line to <lib>_<op>.out for scoring against
/// correctly rounded truth. Skips when the inputs are absent, so plain `forge test`
/// does not run it; `make sweep` generates, runs and scores.
contract Sweep is Test {
    string constant DIR = "cache/sweep/";

    /// The op's result and the gas of its one library call: gasleft() is read
    /// on either side of the call, so the dispatch below (a chain of
    /// comparisons, longer for the later ops) stays outside the window. The
    /// same window around a plain assignment ("noop") is the baseline.
    function f(bytes32 op, int256 a, int256 b, int256 c) external view returns (int256 r, uint256 g) {
        uint256 g0;
        if (op == "noop") { g0 = gasleft(); r = a; g = gasleft(); }
        if (op == "fp256_add") { g0 = gasleft(); r = FP256Lib.add(a, b); g = gasleft(); }
        if (op == "fp256_mul") { g0 = gasleft(); r = FP256Lib.mul(a, b); g = gasleft(); }
        if (op == "fp256_div") { g0 = gasleft(); r = FP256Lib.div(a, b); g = gasleft(); }
        if (op == "fp256_sqrt") { g0 = gasleft(); r = FP256Lib.sqrt(a); g = gasleft(); }
        if (op == "fp256_exp") { g0 = gasleft(); r = FP256Lib.exp(a); g = gasleft(); }
        if (op == "fp256_ln") { g0 = gasleft(); r = FP256Lib.ln(a); g = gasleft(); }
        if (op == "fp256_log1p") { g0 = gasleft(); r = FP256Lib.log1p(a); g = gasleft(); }
        if (op == "fp256_expm1") { g0 = gasleft(); r = FP256Lib.expm1(a); g = gasleft(); }
        if (op == "fp256_pow") { g0 = gasleft(); r = FP256Lib.pow(a, b); g = gasleft(); }
        if (op == "fp256_erf") { g0 = gasleft(); r = FP256Lib.erf(a); g = gasleft(); }
        if (op == "fp256_erfc") { g0 = gasleft(); r = FP256Lib.erfc(a); g = gasleft(); }
        if (op == "fp256_normCdf") { g0 = gasleft(); r = FP256Lib.normCdf(a); g = gasleft(); }
        if (op == "fp256_compound") { g0 = gasleft(); r = FP256Lib.compound(a, b); g = gasleft(); }
        if (op == "fp256_lambertW0") { g0 = gasleft(); r = FP256Lib.lambertW0(a); g = gasleft(); }
        if (op == "fp256_lambertWm1") { g0 = gasleft(); r = FP256Lib.lambertWm1(a); g = gasleft(); }
        if (op == "fp256_lambertW0x") { g0 = gasleft(); r = FP256Lib.lambertW0(a); g = gasleft(); }
        if (op == "fp256_expx") { g0 = gasleft(); r = FP256Lib.exp(a); g = gasleft(); }
        if (op == "fp256_expm1x") { g0 = gasleft(); r = FP256Lib.expm1(a); g = gasleft(); }
        if (op == "fp256_log1px") { g0 = gasleft(); r = FP256Lib.log1p(a); g = gasleft(); }
        if (op == "fp256_powx") { g0 = gasleft(); r = FP256Lib.pow(a, b); g = gasleft(); }
        if (op == "fp256_compoundx") { g0 = gasleft(); r = FP256Lib.compound(a, b); g = gasleft(); }
        if (op == "fp256_erfcx") { g0 = gasleft(); r = FP256Lib.erfc(a); g = gasleft(); }
        if (op == "fp256_normCdfx") { g0 = gasleft(); r = FP256Lib.normCdf(a); g = gasleft(); }
        if (op == "fp256_powux") { g0 = gasleft(); r = FP256Lib.powu(a, b); g = gasleft(); }
        if (op == "fp256_powu") { g0 = gasleft(); r = FP256Lib.powu(a, b); g = gasleft(); }
        if (op == "fp256_mulDown") { g0 = gasleft(); r = FP256Lib.mulDown(a, b); g = gasleft(); }
        if (op == "fp256_mulUp") { g0 = gasleft(); r = FP256Lib.mulUp(a, b); g = gasleft(); }
        if (op == "fp256_divDown") { g0 = gasleft(); r = FP256Lib.divDown(a, b); g = gasleft(); }
        if (op == "fp256_divUp") { g0 = gasleft(); r = FP256Lib.divUp(a, b); g = gasleft(); }
        if (op == "fp256_toUintDown") { g0 = gasleft(); r = int256(FP256Lib.toUintDown(a)); g = gasleft(); }
        if (op == "fp256_toUintUp") { g0 = gasleft(); r = int256(FP256Lib.toUintUp(a)); g = gasleft(); }
        if (op == "fp256_toIntDown") { g0 = gasleft(); r = FP256Lib.toIntDown(a); g = gasleft(); }
        if (op == "fp256_toIntUp") { g0 = gasleft(); r = FP256Lib.toIntUp(a); g = gasleft(); }
        if (op == "fp256_floor") { g0 = gasleft(); r = FP256Lib.floor(a); g = gasleft(); }
        if (op == "fp256_ceil") { g0 = gasleft(); r = FP256Lib.ceil(a); g = gasleft(); }
        if (op == "fp256_fromUintDown") { g0 = gasleft(); r = FP256Lib.fromUintDown(uint256(a)); g = gasleft(); }
        if (op == "fp256_fromUintUp") { g0 = gasleft(); r = FP256Lib.fromUintUp(uint256(a)); g = gasleft(); }
        if (op == "fp256_toFixed18Down") { g0 = gasleft(); r = FP256Lib.toFixed18Down(a); g = gasleft(); }
        if (op == "fp256_toFixed18Up") { g0 = gasleft(); r = FP256Lib.toFixed18Up(a); g = gasleft(); }
        if (op == "fp256_exp2") { g0 = gasleft(); r = FP256Lib.exp2(a); g = gasleft(); }
        if (op == "fp256_exp10") { g0 = gasleft(); r = FP256Lib.exp10(a); g = gasleft(); }
        if (op == "fp256_log2") { g0 = gasleft(); r = FP256Lib.log2(a); g = gasleft(); }
        if (op == "fp256_log10") { g0 = gasleft(); r = FP256Lib.log10(a); g = gasleft(); }
        if (op == "fp256_log2Up") { g0 = gasleft(); r = FP256Lib.log2Up(a); g = gasleft(); }
        if (op == "fp256_cbrt") { g0 = gasleft(); r = FP256Lib.cbrt(a); g = gasleft(); }
        if (op == "fp256_sinh") { g0 = gasleft(); r = FP256Lib.sinh(a); g = gasleft(); }
        if (op == "fp256_cosh") { g0 = gasleft(); r = FP256Lib.cosh(a); g = gasleft(); }
        if (op == "fp256_tanh") { g0 = gasleft(); r = FP256Lib.tanh(a); g = gasleft(); }
        if (op == "fp256_atanh") { g0 = gasleft(); r = FP256Lib.atanh(a); g = gasleft(); }
        if (op == "fp256_min") { g0 = gasleft(); r = FP256Lib.min(a, b); g = gasleft(); }
        if (op == "fp256_max") { g0 = gasleft(); r = FP256Lib.max(a, b); g = gasleft(); }
        if (op == "fp256_avg") { g0 = gasleft(); r = FP256Lib.avg(a, b); g = gasleft(); }
        if (op == "fp256_dist") { g0 = gasleft(); r = FP256Lib.dist(a, b); g = gasleft(); }
        if (op == "fp256_zeroFloorSub") { g0 = gasleft(); r = FP256Lib.zeroFloorSub(a, b); g = gasleft(); }
        if (op == "fp256_inv") { g0 = gasleft(); r = FP256Lib.inv(a); g = gasleft(); }
        if (op == "fp256_frac") { g0 = gasleft(); r = FP256Lib.frac(a); g = gasleft(); }
        if (op == "fp256_round") { g0 = gasleft(); r = FP256Lib.round(a); g = gasleft(); }
        if (op == "fp256_gcd") { g0 = gasleft(); r = FP256Lib.gcd(a, b); g = gasleft(); }
        if (op == "fp256_factorial") { g0 = gasleft(); r = FP256Lib.factorial(a); g = gasleft(); }
        if (op == "fp256_pi") { g0 = gasleft(); r = FP256Lib.pi(a); g = gasleft(); }
        if (op == "fp256_gavg") { g0 = gasleft(); r = FP256Lib.gavg(a, b); g = gasleft(); }
        if (op == "fp256_hypot") { g0 = gasleft(); r = FP256Lib.hypot(a, b); g = gasleft(); }
        if (op == "fp127_mul") { g0 = gasleft(); r = FP127Lib.mul(a, b); g = gasleft(); }
        if (op == "fp127_div") { g0 = gasleft(); r = FP127Lib.div(a, b); g = gasleft(); }
        if (op == "fp127_sqrt") { g0 = gasleft(); r = FP127Lib.sqrt(a); g = gasleft(); }
        if (op == "fp127_exp") { g0 = gasleft(); r = FP127Lib.exp(a); g = gasleft(); }
        if (op == "fp127_ln") { g0 = gasleft(); r = FP127Lib.ln(a); g = gasleft(); }
        if (op == "fp127_log2") { g0 = gasleft(); r = FP127Lib.log2(a); g = gasleft(); }
        if (op == "fp127_pow") { g0 = gasleft(); r = FP127Lib.pow(a, b); g = gasleft(); }
        if (op == "fp127_cbrt") { g0 = gasleft(); r = FP127Lib.cbrt(a); g = gasleft(); }
        if (op == "fp127_expm1") { g0 = gasleft(); r = FP127Lib.expm1(a); g = gasleft(); }
        if (op == "fp127_erf") { g0 = gasleft(); r = FP127Lib.erf(a); g = gasleft(); }
        if (op == "fp127_normCdf") { g0 = gasleft(); r = FP127Lib.normCdf(a); g = gasleft(); }
        if (op == "fp127_compound") { g0 = gasleft(); r = FP127Lib.compound(a, b); g = gasleft(); }
        if (op == "fp127_lambertW0") { g0 = gasleft(); r = FP127Lib.lambertW0(a); g = gasleft(); }
        if (op == "fp127_lambertWm1") { g0 = gasleft(); r = FP127Lib.lambertWm1(a); g = gasleft(); }
        if (op == "fp127_exp2") { g0 = gasleft(); r = FP127Lib.exp2(a); g = gasleft(); }
        if (op == "fp127_exp10") { g0 = gasleft(); r = FP127Lib.exp10(a); g = gasleft(); }
        if (op == "fp127_log10") { g0 = gasleft(); r = FP127Lib.log10(a); g = gasleft(); }
        if (op == "fp127_sinh") { g0 = gasleft(); r = FP127Lib.sinh(a); g = gasleft(); }
        if (op == "fp127_cosh") { g0 = gasleft(); r = FP127Lib.cosh(a); g = gasleft(); }
        if (op == "fp127_tanh") { g0 = gasleft(); r = FP127Lib.tanh(a); g = gasleft(); }
        if (op == "fp127_powu") { g0 = gasleft(); r = FP127Lib.powu(a, b); g = gasleft(); }
        if (op == "fp127_mulUp") { g0 = gasleft(); r = FP127Lib.mulUp(a, b); g = gasleft(); }
        if (op == "fp127_divUp") { g0 = gasleft(); r = FP127Lib.divUp(a, b); g = gasleft(); }
        if (op == "fp127_divDown") { g0 = gasleft(); r = FP127Lib.divDown(a, b); g = gasleft(); }
        if (op == "fp127_toFixed18Up") { g0 = gasleft(); r = FP127Lib.toFixed18Up(a); g = gasleft(); }
        if (op == "fp256_clamp") { g0 = gasleft(); r = FP256Lib.clamp(a, b, c); g = gasleft(); }
        if (op == "fp256_lerp") { g0 = gasleft(); r = FP256Lib.lerp(a, b, c); g = gasleft(); }
        require(g0 != 0, "op");
        g = g0 - g;
    }

    /// One op per external call, so its memory is released before the next.
    function runOne(string memory op, bool two) external {
        _run(op, two ? 2 : 1);
    }

    function runOne3(string memory op) external {
        _run(op, 3);
    }

    function _run(string memory op, uint256 args) internal {
        string memory path = string.concat(DIR, op, ".json");
        if (!vm.exists(path)) return;
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = args > 1 ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        bytes32[] memory c = args > 2 ? vm.parseJsonBytes32Array(j, ".c") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, op, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        uint256 base = _base();
        for (uint256 i; i < a.length; i++) {
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i])), int256(uint256(c[i]))) returns (int256 r, uint256 g) {
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
    }

    /// The window around a plain assignment, subtracted from every row: what
    /// is left is the inline library call's own cost.
    function _base() internal view returns (uint256 g) {
        (, g) = this.f("noop", 0, 0, 0);
    }

    // One test per op: forge runs test functions in parallel, and each op
    // writes its own output file.
    function test_fp256_add() public { this.runOne("fp256_add", true); }
    function test_fp256_mul() public { this.runOne("fp256_mul", true); }
    function test_fp256_div() public { this.runOne("fp256_div", true); }
    function test_fp256_sqrt() public { this.runOne("fp256_sqrt", false); }
    function test_fp256_exp() public { this.runOne("fp256_exp", false); }
    function test_fp256_ln() public { this.runOne("fp256_ln", false); }
    function test_fp256_log1p() public { this.runOne("fp256_log1p", false); }
    function test_fp256_expm1() public { this.runOne("fp256_expm1", false); }
    function test_fp256_pow() public { this.runOne("fp256_pow", true); }
    function test_fp256_erf() public { this.runOne("fp256_erf", false); }
    function test_fp256_erfc() public { this.runOne("fp256_erfc", false); }
    function test_fp256_normCdf() public { this.runOne("fp256_normCdf", false); }
    function test_fp256_compound() public { this.runOne("fp256_compound", true); }
    function test_fp256_lambertW0() public { this.runOne("fp256_lambertW0", false); }
    function test_fp256_lambertW0x() public { this.runOne("fp256_lambertW0x", false); }
    function test_fp256_lambertWm1() public { this.runOne("fp256_lambertWm1", false); }
    function test_fp256_powu() public { this.runOne("fp256_powu", true); }
    function test_fp256_expx() public { this.runOne("fp256_expx", false); }
    function test_fp256_expm1x() public { this.runOne("fp256_expm1x", false); }
    function test_fp256_log1px() public { this.runOne("fp256_log1px", false); }
    function test_fp256_powx() public { this.runOne("fp256_powx", true); }
    function test_fp256_compoundx() public { this.runOne("fp256_compoundx", true); }
    function test_fp256_erfcx() public { this.runOne("fp256_erfcx", false); }
    function test_fp256_normCdfx() public { this.runOne("fp256_normCdfx", false); }
    function test_fp256_powux() public { this.runOne("fp256_powux", true); }
    function test_fp256_mulDown() public { this.runOne("fp256_mulDown", true); }
    function test_fp256_mulUp() public { this.runOne("fp256_mulUp", true); }
    function test_fp256_divDown() public { this.runOne("fp256_divDown", true); }
    function test_fp256_divUp() public { this.runOne("fp256_divUp", true); }
    function test_fp256_toUintDown() public { this.runOne("fp256_toUintDown", false); }
    function test_fp256_toUintUp() public { this.runOne("fp256_toUintUp", false); }
    function test_fp256_toIntDown() public { this.runOne("fp256_toIntDown", false); }
    function test_fp256_toIntUp() public { this.runOne("fp256_toIntUp", false); }
    function test_fp256_floor() public { this.runOne("fp256_floor", false); }
    function test_fp256_ceil() public { this.runOne("fp256_ceil", false); }
    function test_fp256_fromUintDown() public { this.runOne("fp256_fromUintDown", false); }
    function test_fp256_fromUintUp() public { this.runOne("fp256_fromUintUp", false); }
    function test_fp256_toFixed18Down() public { this.runOne("fp256_toFixed18Down", false); }
    function test_fp256_toFixed18Up() public { this.runOne("fp256_toFixed18Up", false); }
    function test_fp256_exp2() public { this.runOne("fp256_exp2", false); }
    function test_fp256_exp10() public { this.runOne("fp256_exp10", false); }
    function test_fp256_log2() public { this.runOne("fp256_log2", false); }
    function test_fp256_log10() public { this.runOne("fp256_log10", false); }
    function test_fp256_log2Up() public { this.runOne("fp256_log2Up", false); }
    function test_fp256_cbrt() public { this.runOne("fp256_cbrt", false); }
    function test_fp256_sinh() public { this.runOne("fp256_sinh", false); }
    function test_fp256_cosh() public { this.runOne("fp256_cosh", false); }
    function test_fp256_tanh() public { this.runOne("fp256_tanh", false); }
    function test_fp256_atanh() public { this.runOne("fp256_atanh", false); }
    function test_fp256_min() public { this.runOne("fp256_min", true); }
    function test_fp256_max() public { this.runOne("fp256_max", true); }
    function test_fp256_avg() public { this.runOne("fp256_avg", true); }
    function test_fp256_dist() public { this.runOne("fp256_dist", true); }
    function test_fp256_zeroFloorSub() public { this.runOne("fp256_zeroFloorSub", true); }
    function test_fp256_inv() public { this.runOne("fp256_inv", false); }
    function test_fp256_frac() public { this.runOne("fp256_frac", false); }
    function test_fp256_round() public { this.runOne("fp256_round", false); }
    function test_fp256_gcd() public { this.runOne("fp256_gcd", true); }
    function test_fp256_factorial() public { this.runOne("fp256_factorial", false); }
    function test_fp256_pi() public { this.runOne("fp256_pi", false); }
    function test_fp256_gavg() public { this.runOne("fp256_gavg", true); }
    function test_fp256_hypot() public { this.runOne("fp256_hypot", true); }
    function test_fp256_clamp() public { this.runOne3("fp256_clamp"); }
    function test_fp256_lerp() public { this.runOne3("fp256_lerp"); }
    function test_fp127_mul() public { this.runOne("fp127_mul", true); }
    function test_fp127_div() public { this.runOne("fp127_div", true); }
    function test_fp127_sqrt() public { this.runOne("fp127_sqrt", false); }
    function test_fp127_exp() public { this.runOne("fp127_exp", false); }
    function test_fp127_ln() public { this.runOne("fp127_ln", false); }
    function test_fp127_log2() public { this.runOne("fp127_log2", false); }
    function test_fp127_pow() public { this.runOne("fp127_pow", true); }
    function test_fp127_cbrt() public { this.runOne("fp127_cbrt", false); }
    function test_fp127_expm1() public { this.runOne("fp127_expm1", false); }
    function test_fp127_erf() public { this.runOne("fp127_erf", false); }
    function test_fp127_normCdf() public { this.runOne("fp127_normCdf", false); }
    function test_fp127_compound() public { this.runOne("fp127_compound", true); }
    function test_fp127_lambertW0() public { this.runOne("fp127_lambertW0", false); }
    function test_fp127_lambertWm1() public { this.runOne("fp127_lambertWm1", false); }
    function test_fp127_exp2() public { this.runOne("fp127_exp2", false); }
    function test_fp127_exp10() public { this.runOne("fp127_exp10", false); }
    function test_fp127_log10() public { this.runOne("fp127_log10", false); }
    function test_fp127_sinh() public { this.runOne("fp127_sinh", false); }
    function test_fp127_cosh() public { this.runOne("fp127_cosh", false); }
    function test_fp127_tanh() public { this.runOne("fp127_tanh", false); }
    function test_fp127_powu() public { this.runOne("fp127_powu", true); }
    function test_fp127_mulUp() public { this.runOne("fp127_mulUp", true); }
    function test_fp127_divUp() public { this.runOne("fp127_divUp", true); }
    function test_fp127_divDown() public { this.runOne("fp127_divDown", true); }
    function test_fp127_toFixed18Up() public { this.runOne("fp127_toFixed18Up", false); }
}

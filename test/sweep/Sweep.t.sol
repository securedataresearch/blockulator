// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP19Lib} from "../../contracts/src/fp19/FP19Lib.sol";

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
        if (op == "fp19_add") { g0 = gasleft(); r = FP19Lib.add(a, b); g = gasleft(); }
        if (op == "fp19_mul") { g0 = gasleft(); r = FP19Lib.mul(a, b); g = gasleft(); }
        if (op == "fp19_div") { g0 = gasleft(); r = FP19Lib.div(a, b); g = gasleft(); }
        if (op == "fp19_sqrt") { g0 = gasleft(); r = FP19Lib.sqrt(a); g = gasleft(); }
        if (op == "fp19_exp") { g0 = gasleft(); r = FP19Lib.exp(a); g = gasleft(); }
        if (op == "fp19_ln") { g0 = gasleft(); r = FP19Lib.ln(a); g = gasleft(); }
        if (op == "fp19_log1p") { g0 = gasleft(); r = FP19Lib.log1p(a); g = gasleft(); }
        if (op == "fp19_expm1") { g0 = gasleft(); r = FP19Lib.expm1(a); g = gasleft(); }
        if (op == "fp19_pow") { g0 = gasleft(); r = FP19Lib.pow(a, b); g = gasleft(); }
        if (op == "fp19_erf") { g0 = gasleft(); r = FP19Lib.erf(a); g = gasleft(); }
        if (op == "fp19_erfc") { g0 = gasleft(); r = FP19Lib.erfc(a); g = gasleft(); }
        if (op == "fp19_normCdf") { g0 = gasleft(); r = FP19Lib.normCdf(a); g = gasleft(); }
        if (op == "fp19_compound") { g0 = gasleft(); r = FP19Lib.compound(a, b); g = gasleft(); }
        if (op == "fp19_lambertW0") { g0 = gasleft(); r = FP19Lib.lambertW0(a); g = gasleft(); }
        if (op == "fp19_lambertWm1") { g0 = gasleft(); r = FP19Lib.lambertWm1(a); g = gasleft(); }
        if (op == "fp19_lambertW0x") { g0 = gasleft(); r = FP19Lib.lambertW0(a); g = gasleft(); }
        if (op == "fp19_expx") { g0 = gasleft(); r = FP19Lib.exp(a); g = gasleft(); }
        if (op == "fp19_expm1x") { g0 = gasleft(); r = FP19Lib.expm1(a); g = gasleft(); }
        if (op == "fp19_log1px") { g0 = gasleft(); r = FP19Lib.log1p(a); g = gasleft(); }
        if (op == "fp19_powx") { g0 = gasleft(); r = FP19Lib.pow(a, b); g = gasleft(); }
        if (op == "fp19_compoundx") { g0 = gasleft(); r = FP19Lib.compound(a, b); g = gasleft(); }
        if (op == "fp19_erfcx") { g0 = gasleft(); r = FP19Lib.erfc(a); g = gasleft(); }
        if (op == "fp19_normCdfx") { g0 = gasleft(); r = FP19Lib.normCdf(a); g = gasleft(); }
        if (op == "fp19_powux") { g0 = gasleft(); r = FP19Lib.powu(a, b); g = gasleft(); }
        if (op == "fp19_powu") { g0 = gasleft(); r = FP19Lib.powu(a, b); g = gasleft(); }
        if (op == "fp19_mulDown") { g0 = gasleft(); r = FP19Lib.mulDown(a, b); g = gasleft(); }
        if (op == "fp19_mulUp") { g0 = gasleft(); r = FP19Lib.mulUp(a, b); g = gasleft(); }
        if (op == "fp19_divDown") { g0 = gasleft(); r = FP19Lib.divDown(a, b); g = gasleft(); }
        if (op == "fp19_divUp") { g0 = gasleft(); r = FP19Lib.divUp(a, b); g = gasleft(); }
        if (op == "fp19_toUintDown") { g0 = gasleft(); r = int256(FP19Lib.toUintDown(a)); g = gasleft(); }
        if (op == "fp19_toUintUp") { g0 = gasleft(); r = int256(FP19Lib.toUintUp(a)); g = gasleft(); }
        if (op == "fp19_toIntDown") { g0 = gasleft(); r = FP19Lib.toIntDown(a); g = gasleft(); }
        if (op == "fp19_toIntUp") { g0 = gasleft(); r = FP19Lib.toIntUp(a); g = gasleft(); }
        if (op == "fp19_floor") { g0 = gasleft(); r = FP19Lib.floor(a); g = gasleft(); }
        if (op == "fp19_ceil") { g0 = gasleft(); r = FP19Lib.ceil(a); g = gasleft(); }
        if (op == "fp19_fromUintDown") { g0 = gasleft(); r = FP19Lib.fromUintDown(uint256(a)); g = gasleft(); }
        if (op == "fp19_fromUintUp") { g0 = gasleft(); r = FP19Lib.fromUintUp(uint256(a)); g = gasleft(); }
        if (op == "fp19_toFixed18Down") { g0 = gasleft(); r = FP19Lib.toFixed18Down(a); g = gasleft(); }
        if (op == "fp19_toFixed18Up") { g0 = gasleft(); r = FP19Lib.toFixed18Up(a); g = gasleft(); }
        if (op == "fp19_exp2") { g0 = gasleft(); r = FP19Lib.exp2(a); g = gasleft(); }
        if (op == "fp19_exp10") { g0 = gasleft(); r = FP19Lib.exp10(a); g = gasleft(); }
        if (op == "fp19_log2") { g0 = gasleft(); r = FP19Lib.log2(a); g = gasleft(); }
        if (op == "fp19_log10") { g0 = gasleft(); r = FP19Lib.log10(a); g = gasleft(); }
        if (op == "fp19_log2Up") { g0 = gasleft(); r = FP19Lib.log2Up(a); g = gasleft(); }
        if (op == "fp19_cbrt") { g0 = gasleft(); r = FP19Lib.cbrt(a); g = gasleft(); }
        if (op == "fp19_sinh") { g0 = gasleft(); r = FP19Lib.sinh(a); g = gasleft(); }
        if (op == "fp19_cosh") { g0 = gasleft(); r = FP19Lib.cosh(a); g = gasleft(); }
        if (op == "fp19_tanh") { g0 = gasleft(); r = FP19Lib.tanh(a); g = gasleft(); }
        if (op == "fp19_atanh") { g0 = gasleft(); r = FP19Lib.atanh(a); g = gasleft(); }
        if (op == "fp19_min") { g0 = gasleft(); r = FP19Lib.min(a, b); g = gasleft(); }
        if (op == "fp19_max") { g0 = gasleft(); r = FP19Lib.max(a, b); g = gasleft(); }
        if (op == "fp19_avg") { g0 = gasleft(); r = FP19Lib.avg(a, b); g = gasleft(); }
        if (op == "fp19_dist") { g0 = gasleft(); r = FP19Lib.dist(a, b); g = gasleft(); }
        if (op == "fp19_zeroFloorSub") { g0 = gasleft(); r = FP19Lib.zeroFloorSub(a, b); g = gasleft(); }
        if (op == "fp19_inv") { g0 = gasleft(); r = FP19Lib.inv(a); g = gasleft(); }
        if (op == "fp19_frac") { g0 = gasleft(); r = FP19Lib.frac(a); g = gasleft(); }
        if (op == "fp19_round") { g0 = gasleft(); r = FP19Lib.round(a); g = gasleft(); }
        if (op == "fp19_factorial") { g0 = gasleft(); r = FP19Lib.factorial(a); g = gasleft(); }
        if (op == "fp19_gavg") { g0 = gasleft(); r = FP19Lib.gavg(a, b); g = gasleft(); }
        if (op == "fp19_hypot") { g0 = gasleft(); r = FP19Lib.hypot(a, b); g = gasleft(); }
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
        if (op == "fp127_erfc") { g0 = gasleft(); r = FP127Lib.erfc(a); g = gasleft(); }
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
        if (op == "fp127_atanh") { g0 = gasleft(); r = FP127Lib.atanh(a); g = gasleft(); }
        if (op == "fp127_powu") { g0 = gasleft(); r = FP127Lib.powu(a, b); g = gasleft(); }
        if (op == "fp127_mulUp") { g0 = gasleft(); r = FP127Lib.mulUp(a, b); g = gasleft(); }
        if (op == "fp127_divUp") { g0 = gasleft(); r = FP127Lib.divUp(a, b); g = gasleft(); }
        if (op == "fp127_divDown") { g0 = gasleft(); r = FP127Lib.divDown(a, b); g = gasleft(); }
        if (op == "fp127_toFixed18Up") { g0 = gasleft(); r = FP127Lib.toFixed18Up(a); g = gasleft(); }
        if (op == "fp127_log1p") { g0 = gasleft(); r = FP127Lib.log1p(a); g = gasleft(); }
        if (op == "fp127_gavg") { g0 = gasleft(); r = FP127Lib.gavg(a, b); g = gasleft(); }
        if (op == "fp127_hypot") { g0 = gasleft(); r = FP127Lib.hypot(a, b); g = gasleft(); }
        if (op == "fp127_inv") { g0 = gasleft(); r = FP127Lib.inv(a); g = gasleft(); }
        if (op == "fp127_mulDown") { g0 = gasleft(); r = FP127Lib.mulDown(a, b); g = gasleft(); }
        if (op == "fp19_clamp") { g0 = gasleft(); r = FP19Lib.clamp(a, b, c); g = gasleft(); }
        if (op == "fp19_lerp") { g0 = gasleft(); r = FP19Lib.lerp(a, b, c); g = gasleft(); }
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
    function test_fp19_add() public { this.runOne("fp19_add", true); }
    function test_fp19_mul() public { this.runOne("fp19_mul", true); }
    function test_fp19_div() public { this.runOne("fp19_div", true); }
    function test_fp19_sqrt() public { this.runOne("fp19_sqrt", false); }
    function test_fp19_exp() public { this.runOne("fp19_exp", false); }
    function test_fp19_ln() public { this.runOne("fp19_ln", false); }
    function test_fp19_log1p() public { this.runOne("fp19_log1p", false); }
    function test_fp19_expm1() public { this.runOne("fp19_expm1", false); }
    function test_fp19_pow() public { this.runOne("fp19_pow", true); }
    function test_fp19_erf() public { this.runOne("fp19_erf", false); }
    function test_fp19_erfc() public { this.runOne("fp19_erfc", false); }
    function test_fp19_normCdf() public { this.runOne("fp19_normCdf", false); }
    function test_fp19_compound() public { this.runOne("fp19_compound", true); }
    function test_fp19_lambertW0() public { this.runOne("fp19_lambertW0", false); }
    function test_fp19_lambertW0x() public { this.runOne("fp19_lambertW0x", false); }
    function test_fp19_lambertWm1() public { this.runOne("fp19_lambertWm1", false); }
    function test_fp19_powu() public { this.runOne("fp19_powu", true); }
    function test_fp19_expx() public { this.runOne("fp19_expx", false); }
    function test_fp19_expm1x() public { this.runOne("fp19_expm1x", false); }
    function test_fp19_log1px() public { this.runOne("fp19_log1px", false); }
    function test_fp19_powx() public { this.runOne("fp19_powx", true); }
    function test_fp19_compoundx() public { this.runOne("fp19_compoundx", true); }
    function test_fp19_erfcx() public { this.runOne("fp19_erfcx", false); }
    function test_fp19_normCdfx() public { this.runOne("fp19_normCdfx", false); }
    function test_fp19_powux() public { this.runOne("fp19_powux", true); }
    function test_fp19_mulDown() public { this.runOne("fp19_mulDown", true); }
    function test_fp19_mulUp() public { this.runOne("fp19_mulUp", true); }
    function test_fp19_divDown() public { this.runOne("fp19_divDown", true); }
    function test_fp19_divUp() public { this.runOne("fp19_divUp", true); }
    function test_fp19_toUintDown() public { this.runOne("fp19_toUintDown", false); }
    function test_fp19_toUintUp() public { this.runOne("fp19_toUintUp", false); }
    function test_fp19_toIntDown() public { this.runOne("fp19_toIntDown", false); }
    function test_fp19_toIntUp() public { this.runOne("fp19_toIntUp", false); }
    function test_fp19_floor() public { this.runOne("fp19_floor", false); }
    function test_fp19_ceil() public { this.runOne("fp19_ceil", false); }
    function test_fp19_fromUintDown() public { this.runOne("fp19_fromUintDown", false); }
    function test_fp19_fromUintUp() public { this.runOne("fp19_fromUintUp", false); }
    function test_fp19_toFixed18Down() public { this.runOne("fp19_toFixed18Down", false); }
    function test_fp19_toFixed18Up() public { this.runOne("fp19_toFixed18Up", false); }
    function test_fp19_exp2() public { this.runOne("fp19_exp2", false); }
    function test_fp19_exp10() public { this.runOne("fp19_exp10", false); }
    function test_fp19_log2() public { this.runOne("fp19_log2", false); }
    function test_fp19_log10() public { this.runOne("fp19_log10", false); }
    function test_fp19_log2Up() public { this.runOne("fp19_log2Up", false); }
    function test_fp19_cbrt() public { this.runOne("fp19_cbrt", false); }
    function test_fp19_sinh() public { this.runOne("fp19_sinh", false); }
    function test_fp19_cosh() public { this.runOne("fp19_cosh", false); }
    function test_fp19_tanh() public { this.runOne("fp19_tanh", false); }
    function test_fp19_atanh() public { this.runOne("fp19_atanh", false); }
    function test_fp19_min() public { this.runOne("fp19_min", true); }
    function test_fp19_max() public { this.runOne("fp19_max", true); }
    function test_fp19_avg() public { this.runOne("fp19_avg", true); }
    function test_fp19_dist() public { this.runOne("fp19_dist", true); }
    function test_fp19_zeroFloorSub() public { this.runOne("fp19_zeroFloorSub", true); }
    function test_fp19_inv() public { this.runOne("fp19_inv", false); }
    function test_fp19_frac() public { this.runOne("fp19_frac", false); }
    function test_fp19_round() public { this.runOne("fp19_round", false); }
    function test_fp19_factorial() public { this.runOne("fp19_factorial", false); }
    function test_fp19_gavg() public { this.runOne("fp19_gavg", true); }
    function test_fp19_hypot() public { this.runOne("fp19_hypot", true); }
    function test_fp19_clamp() public { this.runOne3("fp19_clamp"); }
    function test_fp19_lerp() public { this.runOne3("fp19_lerp"); }
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
    function test_fp127_erfc() public { this.runOne("fp127_erfc", false); }
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
    function test_fp127_atanh() public { this.runOne("fp127_atanh", false); }
    function test_fp127_powu() public { this.runOne("fp127_powu", true); }
    function test_fp127_mulUp() public { this.runOne("fp127_mulUp", true); }
    function test_fp127_divUp() public { this.runOne("fp127_divUp", true); }
    function test_fp127_divDown() public { this.runOne("fp127_divDown", true); }
    function test_fp127_toFixed18Up() public { this.runOne("fp127_toFixed18Up", false); }
    function test_fp127_log1p() public { this.runOne("fp127_log1p", false); }
    function test_fp127_gavg() public { this.runOne("fp127_gavg", true); }
    function test_fp127_hypot() public { this.runOne("fp127_hypot", true); }
    function test_fp127_inv() public { this.runOne("fp127_inv", false); }
    function test_fp127_mulDown() public { this.runOne("fp127_mulDown", true); }
}

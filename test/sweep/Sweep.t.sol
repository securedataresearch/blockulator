// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import {BL19Lib} from "../../contracts/src/bl19/BL19Lib.sol";

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
        if (op == "bl19_add") { g0 = gasleft(); r = BL19Lib.add(a, b); g = gasleft(); }
        if (op == "bl19_mul") { g0 = gasleft(); r = BL19Lib.mul(a, b); g = gasleft(); }
        if (op == "bl19_div") { g0 = gasleft(); r = BL19Lib.div(a, b); g = gasleft(); }
        if (op == "bl19_sqrt") { g0 = gasleft(); r = BL19Lib.sqrt(a); g = gasleft(); }
        if (op == "bl19_exp") { g0 = gasleft(); r = BL19Lib.exp(a); g = gasleft(); }
        if (op == "bl19_ln") { g0 = gasleft(); r = BL19Lib.ln(a); g = gasleft(); }
        if (op == "bl19_log1p") { g0 = gasleft(); r = BL19Lib.log1p(a); g = gasleft(); }
        if (op == "bl19_expm1") { g0 = gasleft(); r = BL19Lib.expm1(a); g = gasleft(); }
        if (op == "bl19_pow") { g0 = gasleft(); r = BL19Lib.pow(a, b); g = gasleft(); }
        if (op == "bl19_erf") { g0 = gasleft(); r = BL19Lib.erf(a); g = gasleft(); }
        if (op == "bl19_erfc") { g0 = gasleft(); r = BL19Lib.erfc(a); g = gasleft(); }
        if (op == "bl19_normCdf") { g0 = gasleft(); r = BL19Lib.normCdf(a); g = gasleft(); }
        if (op == "bl19_compound") { g0 = gasleft(); r = BL19Lib.compound(a, b); g = gasleft(); }
        if (op == "bl19_lambertW0") { g0 = gasleft(); r = BL19Lib.lambertW0(a); g = gasleft(); }
        if (op == "bl19_lambertWm1") { g0 = gasleft(); r = BL19Lib.lambertWm1(a); g = gasleft(); }
        if (op == "bl19_lambertW0x") { g0 = gasleft(); r = BL19Lib.lambertW0(a); g = gasleft(); }
        if (op == "bl19_expx") { g0 = gasleft(); r = BL19Lib.exp(a); g = gasleft(); }
        if (op == "bl19_expm1x") { g0 = gasleft(); r = BL19Lib.expm1(a); g = gasleft(); }
        if (op == "bl19_log1px") { g0 = gasleft(); r = BL19Lib.log1p(a); g = gasleft(); }
        if (op == "bl19_powx") { g0 = gasleft(); r = BL19Lib.pow(a, b); g = gasleft(); }
        if (op == "bl19_compoundx") { g0 = gasleft(); r = BL19Lib.compound(a, b); g = gasleft(); }
        if (op == "bl19_erfcx") { g0 = gasleft(); r = BL19Lib.erfc(a); g = gasleft(); }
        if (op == "bl19_normCdfx") { g0 = gasleft(); r = BL19Lib.normCdf(a); g = gasleft(); }
        if (op == "bl19_powux") { g0 = gasleft(); r = BL19Lib.powu(a, b); g = gasleft(); }
        if (op == "bl19_powu") { g0 = gasleft(); r = BL19Lib.powu(a, b); g = gasleft(); }
        if (op == "bl19_mulDown") { g0 = gasleft(); r = BL19Lib.mulDown(a, b); g = gasleft(); }
        if (op == "bl19_mulUp") { g0 = gasleft(); r = BL19Lib.mulUp(a, b); g = gasleft(); }
        if (op == "bl19_divDown") { g0 = gasleft(); r = BL19Lib.divDown(a, b); g = gasleft(); }
        if (op == "bl19_divUp") { g0 = gasleft(); r = BL19Lib.divUp(a, b); g = gasleft(); }
        if (op == "bl19_toUintDown") { g0 = gasleft(); r = int256(BL19Lib.toUintDown(a)); g = gasleft(); }
        if (op == "bl19_toUintUp") { g0 = gasleft(); r = int256(BL19Lib.toUintUp(a)); g = gasleft(); }
        if (op == "bl19_toIntDown") { g0 = gasleft(); r = BL19Lib.toIntDown(a); g = gasleft(); }
        if (op == "bl19_toIntUp") { g0 = gasleft(); r = BL19Lib.toIntUp(a); g = gasleft(); }
        if (op == "bl19_floor") { g0 = gasleft(); r = BL19Lib.floor(a); g = gasleft(); }
        if (op == "bl19_ceil") { g0 = gasleft(); r = BL19Lib.ceil(a); g = gasleft(); }
        if (op == "bl19_fromUintDown") { g0 = gasleft(); r = BL19Lib.fromUintDown(uint256(a)); g = gasleft(); }
        if (op == "bl19_fromUintUp") { g0 = gasleft(); r = BL19Lib.fromUintUp(uint256(a)); g = gasleft(); }
        if (op == "bl19_toFixed18Down") { g0 = gasleft(); r = BL19Lib.toFixed18Down(a); g = gasleft(); }
        if (op == "bl19_toFixed18Up") { g0 = gasleft(); r = BL19Lib.toFixed18Up(a); g = gasleft(); }
        if (op == "bl19_exp2") { g0 = gasleft(); r = BL19Lib.exp2(a); g = gasleft(); }
        if (op == "bl19_exp10") { g0 = gasleft(); r = BL19Lib.exp10(a); g = gasleft(); }
        if (op == "bl19_log2") { g0 = gasleft(); r = BL19Lib.log2(a); g = gasleft(); }
        if (op == "bl19_log10") { g0 = gasleft(); r = BL19Lib.log10(a); g = gasleft(); }
        if (op == "bl19_log2Up") { g0 = gasleft(); r = BL19Lib.log2Up(a); g = gasleft(); }
        if (op == "bl19_cbrt") { g0 = gasleft(); r = BL19Lib.cbrt(a); g = gasleft(); }
        if (op == "bl19_sinh") { g0 = gasleft(); r = BL19Lib.sinh(a); g = gasleft(); }
        if (op == "bl19_cosh") { g0 = gasleft(); r = BL19Lib.cosh(a); g = gasleft(); }
        if (op == "bl19_tanh") { g0 = gasleft(); r = BL19Lib.tanh(a); g = gasleft(); }
        if (op == "bl19_atanh") { g0 = gasleft(); r = BL19Lib.atanh(a); g = gasleft(); }
        if (op == "bl19_min") { g0 = gasleft(); r = BL19Lib.min(a, b); g = gasleft(); }
        if (op == "bl19_max") { g0 = gasleft(); r = BL19Lib.max(a, b); g = gasleft(); }
        if (op == "bl19_avg") { g0 = gasleft(); r = BL19Lib.avg(a, b); g = gasleft(); }
        if (op == "bl19_dist") { g0 = gasleft(); r = BL19Lib.dist(a, b); g = gasleft(); }
        if (op == "bl19_zeroFloorSub") { g0 = gasleft(); r = BL19Lib.zeroFloorSub(a, b); g = gasleft(); }
        if (op == "bl19_inv") { g0 = gasleft(); r = BL19Lib.inv(a); g = gasleft(); }
        if (op == "bl19_frac") { g0 = gasleft(); r = BL19Lib.frac(a); g = gasleft(); }
        if (op == "bl19_round") { g0 = gasleft(); r = BL19Lib.round(a); g = gasleft(); }
        if (op == "bl19_factorial") { g0 = gasleft(); r = BL19Lib.factorial(a); g = gasleft(); }
        if (op == "bl19_gavg") { g0 = gasleft(); r = BL19Lib.gavg(a, b); g = gasleft(); }
        if (op == "bl19_hypot") { g0 = gasleft(); r = BL19Lib.hypot(a, b); g = gasleft(); }
        if (op == "bl127_mul") { g0 = gasleft(); r = BL127Lib.mul(a, b); g = gasleft(); }
        if (op == "bl127_div") { g0 = gasleft(); r = BL127Lib.div(a, b); g = gasleft(); }
        if (op == "bl127_sqrt") { g0 = gasleft(); r = BL127Lib.sqrt(a); g = gasleft(); }
        if (op == "bl127_exp") { g0 = gasleft(); r = BL127Lib.exp(a); g = gasleft(); }
        if (op == "bl127_ln") { g0 = gasleft(); r = BL127Lib.ln(a); g = gasleft(); }
        if (op == "bl127_log2") { g0 = gasleft(); r = BL127Lib.log2(a); g = gasleft(); }
        if (op == "bl127_pow") { g0 = gasleft(); r = BL127Lib.pow(a, b); g = gasleft(); }
        if (op == "bl127_cbrt") { g0 = gasleft(); r = BL127Lib.cbrt(a); g = gasleft(); }
        if (op == "bl127_expm1") { g0 = gasleft(); r = BL127Lib.expm1(a); g = gasleft(); }
        if (op == "bl127_erf") { g0 = gasleft(); r = BL127Lib.erf(a); g = gasleft(); }
        if (op == "bl127_erfc") { g0 = gasleft(); r = BL127Lib.erfc(a); g = gasleft(); }
        if (op == "bl127_normCdf") { g0 = gasleft(); r = BL127Lib.normCdf(a); g = gasleft(); }
        if (op == "bl127_compound") { g0 = gasleft(); r = BL127Lib.compound(a, b); g = gasleft(); }
        if (op == "bl127_lambertW0") { g0 = gasleft(); r = BL127Lib.lambertW0(a); g = gasleft(); }
        if (op == "bl127_lambertWm1") { g0 = gasleft(); r = BL127Lib.lambertWm1(a); g = gasleft(); }
        if (op == "bl127_exp2") { g0 = gasleft(); r = BL127Lib.exp2(a); g = gasleft(); }
        if (op == "bl127_exp10") { g0 = gasleft(); r = BL127Lib.exp10(a); g = gasleft(); }
        if (op == "bl127_log10") { g0 = gasleft(); r = BL127Lib.log10(a); g = gasleft(); }
        if (op == "bl127_sinh") { g0 = gasleft(); r = BL127Lib.sinh(a); g = gasleft(); }
        if (op == "bl127_cosh") { g0 = gasleft(); r = BL127Lib.cosh(a); g = gasleft(); }
        if (op == "bl127_tanh") { g0 = gasleft(); r = BL127Lib.tanh(a); g = gasleft(); }
        if (op == "bl127_atanh") { g0 = gasleft(); r = BL127Lib.atanh(a); g = gasleft(); }
        if (op == "bl127_powu") { g0 = gasleft(); r = BL127Lib.powu(a, b); g = gasleft(); }
        if (op == "bl127_mulUp") { g0 = gasleft(); r = BL127Lib.mulUp(a, b); g = gasleft(); }
        if (op == "bl127_divUp") { g0 = gasleft(); r = BL127Lib.divUp(a, b); g = gasleft(); }
        if (op == "bl127_divDown") { g0 = gasleft(); r = BL127Lib.divDown(a, b); g = gasleft(); }
        if (op == "bl127_toFixed18Up") { g0 = gasleft(); r = BL127Lib.toFixed18Up(a); g = gasleft(); }
        if (op == "bl127_log1p") { g0 = gasleft(); r = BL127Lib.log1p(a); g = gasleft(); }
        if (op == "bl127_gavg") { g0 = gasleft(); r = BL127Lib.gavg(a, b); g = gasleft(); }
        if (op == "bl127_hypot") { g0 = gasleft(); r = BL127Lib.hypot(a, b); g = gasleft(); }
        if (op == "bl127_inv") { g0 = gasleft(); r = BL127Lib.inv(a); g = gasleft(); }
        if (op == "bl127_mulDown") { g0 = gasleft(); r = BL127Lib.mulDown(a, b); g = gasleft(); }
        if (op == "bl19_clamp") { g0 = gasleft(); r = BL19Lib.clamp(a, b, c); g = gasleft(); }
        if (op == "bl19_lerp") { g0 = gasleft(); r = BL19Lib.lerp(a, b, c); g = gasleft(); }
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
    function test_bl19_add() public { this.runOne("bl19_add", true); }
    function test_bl19_mul() public { this.runOne("bl19_mul", true); }
    function test_bl19_div() public { this.runOne("bl19_div", true); }
    function test_bl19_sqrt() public { this.runOne("bl19_sqrt", false); }
    function test_bl19_exp() public { this.runOne("bl19_exp", false); }
    function test_bl19_ln() public { this.runOne("bl19_ln", false); }
    function test_bl19_log1p() public { this.runOne("bl19_log1p", false); }
    function test_bl19_expm1() public { this.runOne("bl19_expm1", false); }
    function test_bl19_pow() public { this.runOne("bl19_pow", true); }
    function test_bl19_erf() public { this.runOne("bl19_erf", false); }
    function test_bl19_erfc() public { this.runOne("bl19_erfc", false); }
    function test_bl19_normCdf() public { this.runOne("bl19_normCdf", false); }
    function test_bl19_compound() public { this.runOne("bl19_compound", true); }
    function test_bl19_lambertW0() public { this.runOne("bl19_lambertW0", false); }
    function test_bl19_lambertW0x() public { this.runOne("bl19_lambertW0x", false); }
    function test_bl19_lambertWm1() public { this.runOne("bl19_lambertWm1", false); }
    function test_bl19_powu() public { this.runOne("bl19_powu", true); }
    function test_bl19_expx() public { this.runOne("bl19_expx", false); }
    function test_bl19_expm1x() public { this.runOne("bl19_expm1x", false); }
    function test_bl19_log1px() public { this.runOne("bl19_log1px", false); }
    function test_bl19_powx() public { this.runOne("bl19_powx", true); }
    function test_bl19_compoundx() public { this.runOne("bl19_compoundx", true); }
    function test_bl19_erfcx() public { this.runOne("bl19_erfcx", false); }
    function test_bl19_normCdfx() public { this.runOne("bl19_normCdfx", false); }
    function test_bl19_powux() public { this.runOne("bl19_powux", true); }
    function test_bl19_mulDown() public { this.runOne("bl19_mulDown", true); }
    function test_bl19_mulUp() public { this.runOne("bl19_mulUp", true); }
    function test_bl19_divDown() public { this.runOne("bl19_divDown", true); }
    function test_bl19_divUp() public { this.runOne("bl19_divUp", true); }
    function test_bl19_toUintDown() public { this.runOne("bl19_toUintDown", false); }
    function test_bl19_toUintUp() public { this.runOne("bl19_toUintUp", false); }
    function test_bl19_toIntDown() public { this.runOne("bl19_toIntDown", false); }
    function test_bl19_toIntUp() public { this.runOne("bl19_toIntUp", false); }
    function test_bl19_floor() public { this.runOne("bl19_floor", false); }
    function test_bl19_ceil() public { this.runOne("bl19_ceil", false); }
    function test_bl19_fromUintDown() public { this.runOne("bl19_fromUintDown", false); }
    function test_bl19_fromUintUp() public { this.runOne("bl19_fromUintUp", false); }
    function test_bl19_toFixed18Down() public { this.runOne("bl19_toFixed18Down", false); }
    function test_bl19_toFixed18Up() public { this.runOne("bl19_toFixed18Up", false); }
    function test_bl19_exp2() public { this.runOne("bl19_exp2", false); }
    function test_bl19_exp10() public { this.runOne("bl19_exp10", false); }
    function test_bl19_log2() public { this.runOne("bl19_log2", false); }
    function test_bl19_log10() public { this.runOne("bl19_log10", false); }
    function test_bl19_log2Up() public { this.runOne("bl19_log2Up", false); }
    function test_bl19_cbrt() public { this.runOne("bl19_cbrt", false); }
    function test_bl19_sinh() public { this.runOne("bl19_sinh", false); }
    function test_bl19_cosh() public { this.runOne("bl19_cosh", false); }
    function test_bl19_tanh() public { this.runOne("bl19_tanh", false); }
    function test_bl19_atanh() public { this.runOne("bl19_atanh", false); }
    function test_bl19_min() public { this.runOne("bl19_min", true); }
    function test_bl19_max() public { this.runOne("bl19_max", true); }
    function test_bl19_avg() public { this.runOne("bl19_avg", true); }
    function test_bl19_dist() public { this.runOne("bl19_dist", true); }
    function test_bl19_zeroFloorSub() public { this.runOne("bl19_zeroFloorSub", true); }
    function test_bl19_inv() public { this.runOne("bl19_inv", false); }
    function test_bl19_frac() public { this.runOne("bl19_frac", false); }
    function test_bl19_round() public { this.runOne("bl19_round", false); }
    function test_bl19_factorial() public { this.runOne("bl19_factorial", false); }
    function test_bl19_gavg() public { this.runOne("bl19_gavg", true); }
    function test_bl19_hypot() public { this.runOne("bl19_hypot", true); }
    function test_bl19_clamp() public { this.runOne3("bl19_clamp"); }
    function test_bl19_lerp() public { this.runOne3("bl19_lerp"); }
    function test_bl127_mul() public { this.runOne("bl127_mul", true); }
    function test_bl127_div() public { this.runOne("bl127_div", true); }
    function test_bl127_sqrt() public { this.runOne("bl127_sqrt", false); }
    function test_bl127_exp() public { this.runOne("bl127_exp", false); }
    function test_bl127_ln() public { this.runOne("bl127_ln", false); }
    function test_bl127_log2() public { this.runOne("bl127_log2", false); }
    function test_bl127_pow() public { this.runOne("bl127_pow", true); }
    function test_bl127_cbrt() public { this.runOne("bl127_cbrt", false); }
    function test_bl127_expm1() public { this.runOne("bl127_expm1", false); }
    function test_bl127_erf() public { this.runOne("bl127_erf", false); }
    function test_bl127_erfc() public { this.runOne("bl127_erfc", false); }
    function test_bl127_normCdf() public { this.runOne("bl127_normCdf", false); }
    function test_bl127_compound() public { this.runOne("bl127_compound", true); }
    function test_bl127_lambertW0() public { this.runOne("bl127_lambertW0", false); }
    function test_bl127_lambertWm1() public { this.runOne("bl127_lambertWm1", false); }
    function test_bl127_exp2() public { this.runOne("bl127_exp2", false); }
    function test_bl127_exp10() public { this.runOne("bl127_exp10", false); }
    function test_bl127_log10() public { this.runOne("bl127_log10", false); }
    function test_bl127_sinh() public { this.runOne("bl127_sinh", false); }
    function test_bl127_cosh() public { this.runOne("bl127_cosh", false); }
    function test_bl127_tanh() public { this.runOne("bl127_tanh", false); }
    function test_bl127_atanh() public { this.runOne("bl127_atanh", false); }
    function test_bl127_powu() public { this.runOne("bl127_powu", true); }
    function test_bl127_mulUp() public { this.runOne("bl127_mulUp", true); }
    function test_bl127_divUp() public { this.runOne("bl127_divUp", true); }
    function test_bl127_divDown() public { this.runOne("bl127_divDown", true); }
    function test_bl127_toFixed18Up() public { this.runOne("bl127_toFixed18Up", false); }
    function test_bl127_log1p() public { this.runOne("bl127_log1p", false); }
    function test_bl127_gavg() public { this.runOne("bl127_gavg", true); }
    function test_bl127_hypot() public { this.runOne("bl127_hypot", true); }
    function test_bl127_inv() public { this.runOne("bl127_inv", false); }
    function test_bl127_mulDown() public { this.runOne("bl127_mulDown", true); }
}

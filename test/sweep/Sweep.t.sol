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
    function f(bytes32 op, int256 a, int256 b) external view returns (int256 r, uint256 g) {
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
        require(g0 != 0, "op");
        g = g0 - g;
    }

    /// One op per external call, so its memory is released before the next.
    function runOne(string memory op, bool two) external {
        _run(op, two);
    }

    function _run(string memory op, bool two) internal {
        string memory path = string.concat(DIR, op, ".json");
        if (!vm.exists(path)) return;
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = two ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, op, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        uint256 base = _base();
        for (uint256 i; i < a.length; i++) {
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i]))) returns (int256 r, uint256 g) {
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
    }

    /// The window around a plain assignment, subtracted from every row: what
    /// is left is the inline library call's own cost.
    function _base() internal view returns (uint256 g) {
        (, g) = this.f("noop", 0, 0);
    }

    function test_sweep_fp256() public {
        this.runOne("fp256_add", true); this.runOne("fp256_mul", true); this.runOne("fp256_div", true); this.runOne("fp256_sqrt", false);
        this.runOne("fp256_exp", false); this.runOne("fp256_ln", false); this.runOne("fp256_log1p", false); this.runOne("fp256_expm1", false);
        this.runOne("fp256_pow", true); this.runOne("fp256_erf", false); this.runOne("fp256_erfc", false); this.runOne("fp256_normCdf", false);
        this.runOne("fp256_compound", true); this.runOne("fp256_lambertW0", false);
        // release four
        this.runOne("fp256_lambertW0x", false); this.runOne("fp256_lambertWm1", false); this.runOne("fp256_powu", true);
        this.runOne("fp256_expx", false); this.runOne("fp256_expm1x", false); this.runOne("fp256_log1px", false); this.runOne("fp256_powx", true);
        this.runOne("fp256_compoundx", true); this.runOne("fp256_erfcx", false); this.runOne("fp256_normCdfx", false); this.runOne("fp256_powux", true);
        this.runOne("fp256_mulDown", true); this.runOne("fp256_mulUp", true); this.runOne("fp256_divDown", true); this.runOne("fp256_divUp", true);
        this.runOne("fp256_toUintDown", false); this.runOne("fp256_toUintUp", false); this.runOne("fp256_toIntDown", false); this.runOne("fp256_toIntUp", false);
        this.runOne("fp256_floor", false); this.runOne("fp256_ceil", false); this.runOne("fp256_fromUintDown", false); this.runOne("fp256_fromUintUp", false);
        this.runOne("fp256_toFixed18Down", false); this.runOne("fp256_toFixed18Up", false);
    }

    function test_sweep_fp127() public {
        this.runOne("fp127_mul", true); this.runOne("fp127_div", true); this.runOne("fp127_sqrt", false); this.runOne("fp127_exp", false);
        this.runOne("fp127_ln", false); this.runOne("fp127_log2", false); this.runOne("fp127_pow", true); this.runOne("fp127_cbrt", false);
        this.runOne("fp127_expm1", false); this.runOne("fp127_erf", false); this.runOne("fp127_normCdf", false); this.runOne("fp127_compound", true);
        this.runOne("fp127_lambertW0", false); this.runOne("fp127_lambertWm1", false);
        this.runOne("fp127_exp2", false); this.runOne("fp127_exp10", false); this.runOne("fp127_log10", false); this.runOne("fp127_sinh", false);
        this.runOne("fp127_cosh", false); this.runOne("fp127_tanh", false); this.runOne("fp127_powu", true); this.runOne("fp127_mulUp", true);
        this.runOne("fp127_divUp", true); this.runOne("fp127_divDown", true); this.runOne("fp127_toFixed18Up", false);
    }
}

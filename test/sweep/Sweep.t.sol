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

    function f(bytes32 op, int256 a, int256 b) external pure returns (int256) {
        if (op == "noop") return 0;
        if (op == "fp256_add") return FP256Lib.add(a, b);
        if (op == "fp256_mul") return FP256Lib.mul(a, b);
        if (op == "fp256_div") return FP256Lib.div(a, b);
        if (op == "fp256_sqrt") return FP256Lib.sqrt(a);
        if (op == "fp256_exp") return FP256Lib.exp(a);
        if (op == "fp256_ln") return FP256Lib.ln(a);
        if (op == "fp256_log1p") return FP256Lib.log1p(a);
        if (op == "fp256_expm1") return FP256Lib.expm1(a);
        if (op == "fp256_pow") return FP256Lib.pow(a, b);
        if (op == "fp256_erf") return FP256Lib.erf(a);
        if (op == "fp256_erfc") return FP256Lib.erfc(a);
        if (op == "fp256_normCdf") return FP256Lib.normCdf(a);
        if (op == "fp256_compound") return FP256Lib.compound(a, b);
        if (op == "fp256_lambertW0") return FP256Lib.lambertW0(a);
        if (op == "fp256_lambertWm1") return FP256Lib.lambertWm1(a);
        if (op == "fp256_lambertW0x") return FP256Lib.lambertW0(a);
        if (op == "fp256_expx") return FP256Lib.exp(a);
        if (op == "fp256_expm1x") return FP256Lib.expm1(a);
        if (op == "fp256_log1px") return FP256Lib.log1p(a);
        if (op == "fp256_powx") return FP256Lib.pow(a, b);
        if (op == "fp256_compoundx") return FP256Lib.compound(a, b);
        if (op == "fp256_erfcx") return FP256Lib.erfc(a);
        if (op == "fp256_normCdfx") return FP256Lib.normCdf(a);
        if (op == "fp256_powux") return FP256Lib.powu(a, b);
        if (op == "fp256_powu") return FP256Lib.powu(a, b);
        if (op == "fp256_mulDown") return FP256Lib.mulDown(a, b);
        if (op == "fp256_mulUp") return FP256Lib.mulUp(a, b);
        if (op == "fp256_divDown") return FP256Lib.divDown(a, b);
        if (op == "fp256_divUp") return FP256Lib.divUp(a, b);
        if (op == "fp256_toUintDown") return int256(FP256Lib.toUintDown(a));
        if (op == "fp256_toUintUp") return int256(FP256Lib.toUintUp(a));
        if (op == "fp256_toIntDown") return FP256Lib.toIntDown(a);
        if (op == "fp256_toIntUp") return FP256Lib.toIntUp(a);
        if (op == "fp256_floor") return FP256Lib.floor(a);
        if (op == "fp256_ceil") return FP256Lib.ceil(a);
        if (op == "fp256_fromUintDown") return FP256Lib.fromUintDown(uint256(a));
        if (op == "fp256_fromUintUp") return FP256Lib.fromUintUp(uint256(a));
        if (op == "fp256_toFixed18Down") return FP256Lib.toFixed18Down(a);
        if (op == "fp256_toFixed18Up") return FP256Lib.toFixed18Up(a);
        if (op == "fp256_exp2") return FP256Lib.exp2(a);
        if (op == "fp256_exp10") return FP256Lib.exp10(a);
        if (op == "fp256_log2") return FP256Lib.log2(a);
        if (op == "fp256_log10") return FP256Lib.log10(a);
        if (op == "fp256_log2Up") return FP256Lib.log2Up(a);
        if (op == "fp256_cbrt") return FP256Lib.cbrt(a);
        if (op == "fp256_sinh") return FP256Lib.sinh(a);
        if (op == "fp256_cosh") return FP256Lib.cosh(a);
        if (op == "fp256_tanh") return FP256Lib.tanh(a);
        if (op == "fp256_atanh") return FP256Lib.atanh(a);
        if (op == "fp256_min") return FP256Lib.min(a, b);
        if (op == "fp256_max") return FP256Lib.max(a, b);
        if (op == "fp256_avg") return FP256Lib.avg(a, b);
        if (op == "fp256_dist") return FP256Lib.dist(a, b);
        if (op == "fp256_zeroFloorSub") return FP256Lib.zeroFloorSub(a, b);
        if (op == "fp256_inv") return FP256Lib.inv(a);
        if (op == "fp256_frac") return FP256Lib.frac(a);
        if (op == "fp256_round") return FP256Lib.round(a);
        if (op == "fp256_gcd") return FP256Lib.gcd(a, b);
        if (op == "fp256_factorial") return FP256Lib.factorial(a);
        if (op == "fp256_pi") return FP256Lib.pi(a);
        if (op == "fp256_gavg") return FP256Lib.gavg(a, b);
        if (op == "fp256_hypot") return FP256Lib.hypot(a, b);
        if (op == "fp127_mul") return FP127Lib.mul(a, b);
        if (op == "fp127_div") return FP127Lib.div(a, b);
        if (op == "fp127_sqrt") return FP127Lib.sqrt(a);
        if (op == "fp127_exp") return FP127Lib.exp(a);
        if (op == "fp127_ln") return FP127Lib.ln(a);
        if (op == "fp127_log2") return FP127Lib.log2(a);
        if (op == "fp127_pow") return FP127Lib.pow(a, b);
        if (op == "fp127_cbrt") return FP127Lib.cbrt(a);
        if (op == "fp127_expm1") return FP127Lib.expm1(a);
        if (op == "fp127_erf") return FP127Lib.erf(a);
        if (op == "fp127_normCdf") return FP127Lib.normCdf(a);
        if (op == "fp127_compound") return FP127Lib.compound(a, b);
        if (op == "fp127_lambertW0") return FP127Lib.lambertW0(a);
        if (op == "fp127_lambertWm1") return FP127Lib.lambertWm1(a);
        if (op == "fp127_exp2") return FP127Lib.exp2(a);
        if (op == "fp127_exp10") return FP127Lib.exp10(a);
        if (op == "fp127_log10") return FP127Lib.log10(a);
        if (op == "fp127_sinh") return FP127Lib.sinh(a);
        if (op == "fp127_cosh") return FP127Lib.cosh(a);
        if (op == "fp127_tanh") return FP127Lib.tanh(a);
        if (op == "fp127_powu") return FP127Lib.powu(a, b);
        if (op == "fp127_mulUp") return FP127Lib.mulUp(a, b);
        if (op == "fp127_divUp") return FP127Lib.divUp(a, b);
        if (op == "fp127_divDown") return FP127Lib.divDown(a, b);
        if (op == "fp127_toFixed18Up") return FP127Lib.toFixed18Up(a);
        revert("op");
    }

    /// The three-argument ops (#79).
    function f3(bytes32 op, int256 a, int256 b, int256 c) external pure returns (int256) {
        if (op == "noop") return 0;
        if (op == "fp256_clamp") return FP256Lib.clamp(a, b, c);
        if (op == "fp256_lerp") return FP256Lib.lerp(a, b, c);
        revert("op");
    }

    /// One op per external call, so its memory is released before the next.
    function runOne(string memory op, bool two) external {
        _run(op, two);
    }

    function runOne3(string memory op) external {
        string memory path = string.concat(DIR, op, ".json");
        if (!vm.exists(path)) return;
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = vm.parseJsonBytes32Array(j, ".b");
        bytes32[] memory c = vm.parseJsonBytes32Array(j, ".c");
        string memory outp = string.concat(DIR, op, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        uint256 g0 = gasleft();
        try this.f3("noop", 0, 0, 0) returns (int256) {} catch {}
        uint256 base = g0 - gasleft();
        for (uint256 i; i < a.length; i++) {
            g0 = gasleft();
            try this.f3(k, int256(uint256(a[i])), int256(uint256(b[i])), int256(uint256(c[i]))) returns (int256 r) {
                uint256 g = g0 - gasleft();
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
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
            uint256 g0 = gasleft();
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i]))) returns (int256 r) {
                uint256 g = g0 - gasleft();
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
    }

    /// Gas of the self-call with a no-op, subtracted from every row: what is
    /// left is the inline library's own cost.
    function _base() internal view returns (uint256) {
        uint256 g0 = gasleft();
        try this.f("noop", 0, 0) returns (int256) {} catch {}
        return g0 - gasleft();
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
        // #79
        this.runOne("fp256_exp2", false); this.runOne("fp256_exp10", false); this.runOne("fp256_log2", false); this.runOne("fp256_log10", false);
        this.runOne("fp256_log2Up", false); this.runOne("fp256_cbrt", false); this.runOne("fp256_sinh", false); this.runOne("fp256_cosh", false);
        this.runOne("fp256_tanh", false); this.runOne("fp256_atanh", false); this.runOne("fp256_min", true); this.runOne("fp256_max", true);
        this.runOne("fp256_avg", true); this.runOne("fp256_dist", true); this.runOne("fp256_zeroFloorSub", true); this.runOne("fp256_inv", false);
        this.runOne("fp256_frac", false); this.runOne("fp256_round", false); this.runOne("fp256_gcd", true); this.runOne("fp256_factorial", false);
        this.runOne("fp256_pi", false); this.runOne("fp256_gavg", true); this.runOne("fp256_hypot", true);
        this.runOne3("fp256_clamp"); this.runOne3("fp256_lerp");
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

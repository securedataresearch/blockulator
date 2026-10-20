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

    function _run(string memory op, bool two) internal {
        string memory path = string.concat(DIR, op, ".json");
        if (!vm.exists(path)) return;
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = two ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, op, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        for (uint256 i; i < a.length; i++) {
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i]))) returns (int256 r) {
                vm.writeLine(outp, vm.toString(bytes32(uint256(r))));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e)));
            }
        }
    }

    function test_sweep_fp256() public {
        _run("fp256_add", true); _run("fp256_mul", true); _run("fp256_div", true); _run("fp256_sqrt", false);
        _run("fp256_exp", false); _run("fp256_ln", false); _run("fp256_log1p", false); _run("fp256_expm1", false);
        _run("fp256_pow", true); _run("fp256_erf", false); _run("fp256_erfc", false); _run("fp256_normCdf", false);
        _run("fp256_compound", true); _run("fp256_lambertW0", false);
    }

    function test_sweep_fp127() public {
        _run("fp127_mul", true); _run("fp127_div", true); _run("fp127_sqrt", false); _run("fp127_exp", false);
        _run("fp127_ln", false); _run("fp127_log2", false); _run("fp127_pow", true); _run("fp127_cbrt", false);
        _run("fp127_expm1", false); _run("fp127_erf", false); _run("fp127_normCdf", false); _run("fp127_compound", true);
        _run("fp127_lambertW0", false); _run("fp127_lambertWm1", false);
        _run("fp127_exp2", false); _run("fp127_exp10", false); _run("fp127_log10", false); _run("fp127_sinh", false);
        _run("fp127_cosh", false); _run("fp127_tanh", false); _run("fp127_powu", true); _run("fp127_mulUp", true);
        _run("fp127_divUp", true); _run("fp127_divDown", true); _run("fp127_toFixed18Up", false);
    }
}

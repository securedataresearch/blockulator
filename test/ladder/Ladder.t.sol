// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {FP127_ADDRESS, Scenario, Form} from "../../contracts/src/ladder/ILadder.sol";
import {LadderRunner} from "../../contracts/src/ladder/LadderRunner.sol";
import {LadderFP127} from "../../contracts/src/ladder/LadderFP127.sol";
import {LadderFP127Lib} from "../../contracts/src/ladder/LadderFP127Lib.sol";
import {LadderABDK} from "../../contracts/src/ladder/LadderABDK.sol";
import {LadderSolady} from "../../contracts/src/ladder/LadderSolady.sol";
import {LadderPRB} from "../../contracts/src/ladder/LadderPRB.sol";
import {LadderQuad} from "../../contracts/src/ladder/LadderQuad.sol";
import {LadderBalancer} from "../../contracts/src/ladder/LadderBalancer.sol";
import {LadderAave} from "../../contracts/src/ladder/LadderAave.sol";
import {LadderMorpho} from "../../contracts/src/ladder/LadderMorpho.sol";
import {LadderMaker} from "../../contracts/src/ladder/LadderMaker.sol";

/// @title Ladder
/// @notice Produces the terminal-precision dataset: every scenario, for every
///         input in scripts/ladder/inputs.json, through every form for every
///         N on the ladder, by calling the same LadderRunner that is deployed
///         on Sepolia. Prints
///         LADDER|scenario|input|form|N|ok|raw|reason|gasTotal
///         and scripts/ladder/ladder.py computes the mpmath truth and writes
///         docs/benchmarks/ladder.json. One test per scenario so forge runs
///         them in parallel.
///
/// The FP127 runtime from the build artifact is etched at its CREATE2 address,
/// so the "fp127" form exercises the deployed bytecode exactly as Sepolia does.
contract Ladder is Test {
    string constant INPUTS = "scripts/ladder/inputs.json";
    string[10] FORMS = ["fp127", "fp127lib", "abdk", "solady", "prb", "quad", "balancer", "aave", "morpho", "maker"];

    LadderRunner runner;
    string json;
    uint256[] ladder;

    function setUp() public {
        bytes memory runtime = vm.parseJsonBytes(vm.readFile("out/FP127.yul/FP127.json"), ".deployedBytecode.object");
        vm.etch(FP127_ADDRESS, runtime);
        runner = new LadderRunner([
            address(new LadderFP127()),
            address(new LadderFP127Lib()),
            address(new LadderABDK()),
            address(new LadderSolady()),
            address(new LadderPRB()),
            address(new LadderQuad()),
            address(new LadderBalancer()),
            address(new LadderAave()),
            address(new LadderMorpho()),
            address(new LadderMaker())
        ]);
        json = vm.readFile(INPUTS);
        ladder = vm.parseJsonUintArray(json, ".ladder");
    }

    /// The inputs.json key holding a form's floored parameters (the scale).
    function _scaleKey(uint8 f) internal pure returns (string memory) {
        if (f == Form.FP127 || f == Form.FP127LIB) return "fp127";
        if (f == Form.ABDK) return "abdk";
        if (f == Form.QUAD) return "quad";
        if (f == Form.AAVE || f == Form.MAKER) return "ray";
        return "wad";
    }

    function _params(uint256 cell, string memory key) internal view returns (int256[] memory p) {
        string[] memory s = vm.parseJsonStringArray(json, string.concat(".cells[", vm.toString(cell), "].", key));
        p = new int256[](s.length);
        for (uint256 i; i < s.length; i++) p[i] = vm.parseInt(s[i]);
    }

    struct Inp { string id; string input; int256[] fp; int256[] abdk; int256[] wad; int256[] quad; int256[] ray; }

    function _of(Inp memory x, uint8 f) internal pure returns (int256[] memory) {
        if (f == Form.FP127 || f == Form.FP127LIB) return x.fp;
        if (f == Form.ABDK) return x.abdk;
        if (f == Form.QUAD) return x.quad;
        if (f == Form.AAVE || f == Form.MAKER) return x.ray;
        return x.wad;
    }

    function _cell(Inp memory x, uint8 s, uint8 f, uint32 n) internal view returns (bool ok, int256 raw) {
        bytes4 reason;
        uint256 gas;
        (ok, raw, reason,, gas) = runner.run(s, f, n, _of(x, f));
        console.log(string.concat(
            "LADDER|", x.id, "|", x.input, "|", FORMS[f], "|", vm.toString(n), "|", ok ? "1" : "0", "|",
            vm.toString(raw), "|", vm.toString(reason), "|", vm.toString(gas)
        ));
    }

    /// One input through every form and N, with the invariant that the
    /// deployed object and the inline library agree.
    function _input(Inp memory x, uint8 s) internal view {
        for (uint256 i; i < ladder.length; i++) {
            uint32 n = uint32(ladder[i]);
            (bool ok0, int256 r0) = _cell(x, s, Form.FP127, n);
            (bool ok1, int256 r1) = _cell(x, s, Form.FP127LIB, n);
            assertEq(ok0, ok1, string.concat(x.id, "/", x.input, ": fp127/fp127lib ok differ"));
            assertEq(r0, r1, string.concat(x.id, "/", x.input, ": fp127/fp127lib raw differ"));
            for (uint8 f = Form.ABDK; f < Form.COUNT; f++) _cell(x, s, f, n);
        }
    }

    /// Every input of one scenario.
    function _scenario(uint8 s) internal view {
        uint256 count = vm.parseJsonUint(json, ".count");
        for (uint256 c; c < count; c++) {
            string memory base = string.concat(".cells[", vm.toString(c), "]");
            if (vm.parseJsonUint(json, string.concat(base, ".scenario")) != s) continue;
            Inp memory x = Inp({
                id: vm.parseJsonString(json, string.concat(base, ".id")),
                input: vm.parseJsonString(json, string.concat(base, ".input")),
                fp: _params(c, "fp127"),
                abdk: _params(c, "abdk"),
                wad: _params(c, "wad"),
                quad: _params(c, "quad"),
                ray: _params(c, "ray")
            });
            _input(x, s);
        }
    }

    function test_ladder_compound() public view { _scenario(Scenario.COMPOUND); }
    function test_ladder_compoundPow() public view { _scenario(Scenario.COMPOUND_POW); }
    function test_ladder_bondingSqrt() public view { _scenario(Scenario.BONDING_SQRT); }
    function test_ladder_roundtrip() public view { _scenario(Scenario.ROUNDTRIP); }
    function test_ladder_amortise() public view { _scenario(Scenario.AMORTISE); }
    function test_ladder_geoMean() public view { _scenario(Scenario.GEO_MEAN); }
    function test_ladder_blackScholesChain() public view { _scenario(Scenario.BLACK_SCHOLES_CHAIN); }
    function test_ladder_cumulativeProduct() public view { _scenario(Scenario.CUMULATIVE_PRODUCT); }
    function test_ladder_compoundAnnual() public view { _scenario(Scenario.COMPOUND_ANNUAL); }
    function test_ladder_accrualPerSecond() public view { _scenario(Scenario.ACCRUAL_PER_SECOND); }
    function test_ladder_accrualContinuous() public view { _scenario(Scenario.ACCRUAL_CONTINUOUS); }
    function test_ladder_deepTailOption() public view { _scenario(Scenario.DEEP_TAIL_OPTION); }
    function test_ladder_decay() public view { _scenario(Scenario.DECAY); }

    /// The generic normCdf through Solady's primitives agrees with FP127's op
    /// near the money (the price at N = 0 of the reference input).
    function test_generic_normCdf_near_money() public view {
        int256[] memory w = new int256[](6);
        w[0] = 100e18; w[1] = 100e18; w[2] = 0.2e18; w[3] = 0.5e18; w[4] = 0.05e18; w[5] = 0.000173e18;
        (bool okS, int256 rawS,,,) = runner.run(Scenario.DEEP_TAIL_OPTION, Form.SOLADY, 0, w);
        int256[] memory f = new int256[](6);
        for (uint256 i; i < 6; i++) f[i] = (w[i] << 128) / 1e18;
        (bool okF, int256 rawF,,,) = runner.run(Scenario.DEEP_TAIL_OPTION, Form.FP127LIB, 0, f);
        assertTrue(okS && okF);
        int256 fp18 = rawF * 1e18 / (int256(1) << 128);
        // Black-Scholes at the money, 20% vol, six months, 5%: 6.8887...; WAD agrees to ~1e-16
        assertGt(fp18, 6.8e18); assertLt(fp18, 6.95e18);
        int256 diff = fp18 > rawS ? fp18 - rawS : rawS - fp18;
        assertLt(diff, 1e4, "generic normCdf through WAD within 1e-14 of FP127's");
    }

    function test_runner_catches_reverts() public view {
        int256[] memory p = new int256[](1);
        (bool ok, int256 raw, bytes4 reason,, uint256 gas) = runner.run(99, Form.SOLADY, 1, p);
        assertFalse(ok);
        assertEq(raw, 0);
        assertEq(gas, 0);
        assertEq(reason, bytes4(keccak256("UnknownScenario(uint8)")));
    }

    function test_runner_bad_param_count() public view {
        int256[] memory p = new int256[](1);
        (bool ok,, bytes4 reason,,) = runner.run(Scenario.COMPOUND, Form.SOLADY, 1, p);
        assertFalse(ok);
        assertEq(reason, bytes4(keccak256("BadParamCount(uint8,uint256)")));
    }

    function test_abdk_param_out_of_range() public view {
        int256[] memory p = new int256[](2);
        p[0] = int256(1) << 130; // does not fit int128
        p[1] = 0;
        (bool ok,, bytes4 reason,,) = runner.run(Scenario.COMPOUND, Form.ABDK, 1, p);
        assertFalse(ok);
        assertEq(reason, bytes4(keccak256("ParamOutOfRange(uint256)")));
    }

    /// The accrual libraries report Unsupported for the scenarios outside
    /// their model, and the runner records it like any revert.
    function test_accrual_forms_unsupported() public view {
        int256[] memory p = new int256[](2);
        p[0] = 1e27;
        p[1] = 1e25;
        for (uint8 f = Form.AAVE; f <= Form.MAKER; f++) {
            (bool ok,, bytes4 reason,,) = runner.run(Scenario.ROUNDTRIP, f, 1, p);
            assertFalse(ok);
            assertEq(reason, bytes4(keccak256("Unsupported(uint8)")));
        }
        (bool okM, int256 rawM,,,) = runner.run(Scenario.COMPOUND, Form.MAKER, 1, p);
        assertTrue(okM);
        assertEq(rawM, 1.01e27);
    }

    /// Quad: a NaN result is a revert, not a number.
    function test_quad_nan_is_revert() public view {
        int256[] memory p = new int256[](1);
        p[0] = int256(uint256(0xbfff0000000000000000000000000000)); // -1 in binary128
        (bool ok,, bytes4 reason,,) = runner.run(Scenario.ROUNDTRIP, Form.QUAD, 1, p);
        assertFalse(ok);
        assertEq(reason, bytes4(keccak256("QuadNotFinite()")));
    }

    function test_runner_unknown_form() public {
        int256[] memory p = new int256[](0);
        vm.expectRevert(abi.encodeWithSignature("UnknownForm(uint8)", uint8(255)));
        runner.run(0, 255, 1, p);
    }
}

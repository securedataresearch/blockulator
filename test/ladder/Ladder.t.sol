// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {BL127_ADDRESS, BL127E_ADDRESS, BL127H_ADDRESS, BL127N_ADDRESS, BL127S_ADDRESS, Scenario, Form} from "../../contracts/src/ladder/ILadder.sol";
import {LadderRunner} from "../../contracts/src/ladder/LadderRunner.sol";
import {LadderBL127} from "../../contracts/src/ladder/LadderBL127.sol";
import {LadderBL127Lib} from "../../contracts/src/ladder/LadderBL127Lib.sol";
import {LadderABDK} from "../../contracts/src/ladder/LadderABDK.sol";
import {LadderSolady} from "../../contracts/src/ladder/LadderSolady.sol";
import {LadderPRB} from "../../contracts/src/ladder/LadderPRB.sol";
import {LadderQuad} from "../../contracts/src/ladder/LadderQuad.sol";
import {LadderBalancer} from "../../contracts/src/ladder/LadderBalancer.sol";
import {LadderAave} from "../../contracts/src/ladder/LadderAave.sol";
import {LadderMorpho} from "../../contracts/src/ladder/LadderMorpho.sol";
import {LadderMaker} from "../../contracts/src/ladder/LadderMaker.sol";
import {LadderBL19} from "../../contracts/src/ladder/LadderBL19.sol";
import {LadderSolmate} from "../../contracts/src/ladder/LadderSolmate.sol";
import {LadderOZ} from "../../contracts/src/ladder/LadderOZ.sol";
import {LadderUniswap} from "../../contracts/src/ladder/LadderUniswap.sol";
import {LadderPRBUD} from "../../contracts/src/ladder/LadderPRBUD.sol";
import {LadderSnekmate} from "../../contracts/src/ladder/LadderSnekmate.sol";
import {LadderFraxlend} from "../../contracts/src/ladder/LadderFraxlend.sol";
import {LadderEuler} from "../../contracts/src/ladder/LadderEuler.sol";

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
/// The five BL127 objects' runtimes from the build artifacts are etched at their
/// CREATE2 addresses, so the "bl127" form exercises the deployed bytecode exactly
/// as the chain does.
contract Ladder is Test {
    string constant INPUTS = "scripts/ladder/inputs.json";
    string[18] FORMS = ["bl127", "bl127lib", "abdk", "solady", "prb", "quad", "balancer", "aave", "morpho", "maker", "bl19", "solmate", "oz", "uniswap", "prbud", "snekmate", "fraxlend", "euler"];

    LadderRunner runner;
    string json;
    uint256[] ladder;

    /// The Vyper SnekmateMath contract, deployed from its artifact
    /// (scripts/ladder/vyper.py: snekmate v0.1.2, Vyper 0.4.3).
    function _snekmate() internal returns (address m) {
        bytes memory init = vm.parseJsonBytes(vm.readFile("out/vyper/SnekmateMath.json"), ".bytecode.object");
        assembly { m := create(0, add(init, 32), mload(init)) }
        require(m != address(0), "SnekmateMath deploy");
    }

    function _etch(address a, string memory name) internal {
        vm.etch(a, vm.parseJsonBytes(vm.readFile(string.concat("out/", name, ".yul/", name, ".json")), ".deployedBytecode.object"));
    }

    function setUp() public {
        _etch(BL127_ADDRESS, "BL127");
        _etch(BL127E_ADDRESS, "BL127E");
        _etch(BL127H_ADDRESS, "BL127H");
        _etch(BL127N_ADDRESS, "BL127N");
        _etch(BL127S_ADDRESS, "BL127S");
        runner = new LadderRunner([
            address(new LadderBL127()),
            address(new LadderBL127Lib()),
            address(new LadderABDK()),
            address(new LadderSolady()),
            address(new LadderPRB()),
            address(new LadderQuad()),
            address(new LadderBalancer()),
            address(new LadderAave()),
            address(new LadderMorpho()),
            address(new LadderMaker()),
            address(new LadderBL19()),
            address(new LadderSolmate()),
            address(new LadderOZ()),
            address(new LadderUniswap()),
            address(new LadderPRBUD()),
            address(new LadderSnekmate(_snekmate())),
            address(new LadderFraxlend()),
            address(new LadderEuler())
        ]);
        json = vm.readFile(INPUTS);
        ladder = vm.parseJsonUintArray(json, ".ladder");
    }

    /// The inputs.json key holding a form's floored parameters (the scale).
    function _scaleKey(uint8 f) internal pure returns (string memory) {
        if (f == Form.BL127 || f == Form.BL127LIB) return "bl127";
        if (f == Form.ABDK) return "abdk";
        if (f == Form.QUAD) return "quad";
        if (f == Form.BL19) return "bl19";
        if (f == Form.AAVE || f == Form.MAKER) return "ray";
        return "wad";
    }

    function _params(uint256 cell, string memory key) internal view returns (int256[] memory p) {
        string[] memory s = vm.parseJsonStringArray(json, string.concat(".cells[", vm.toString(cell), "].", key));
        p = new int256[](s.length);
        for (uint256 i; i < s.length; i++) p[i] = vm.parseInt(s[i]);
    }

    struct Inp { string id; string input; int256[] fp; int256[] abdk; int256[] wad; int256[] quad; int256[] ray; int256[] bl19; }

    function _of(Inp memory x, uint8 f) internal pure returns (int256[] memory) {
        if (f == Form.BL127 || f == Form.BL127LIB) return x.fp;
        if (f == Form.ABDK) return x.abdk;
        if (f == Form.QUAD) return x.quad;
        if (f == Form.BL19) return x.bl19;
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
            (bool ok0, int256 r0) = _cell(x, s, Form.BL127, n);
            (bool ok1, int256 r1) = _cell(x, s, Form.BL127LIB, n);
            assertEq(ok0, ok1, string.concat(x.id, "/", x.input, ": bl127/bl127lib ok differ"));
            assertEq(r0, r1, string.concat(x.id, "/", x.input, ": bl127/bl127lib raw differ"));
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
                fp: _params(c, "bl127"),
                abdk: _params(c, "abdk"),
                wad: _params(c, "wad"),
                quad: _params(c, "quad"),
                ray: _params(c, "ray"),
                bl19: _params(c, "bl19")
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
    function test_ladder_adaptiveRate() public view { _scenario(Scenario.ADAPTIVE_RATE); }

    /// The generic normCdf through Solady's primitives agrees with BL127's op
    /// near the money (the price at N = 0 of the reference input).
    function test_generic_normCdf_near_money() public view {
        int256[] memory w = new int256[](6);
        w[0] = 100e18; w[1] = 100e18; w[2] = 0.2e18; w[3] = 0.5e18; w[4] = 0.05e18; w[5] = 0.000173e18;
        (bool okS, int256 rawS,,,) = runner.run(Scenario.DEEP_TAIL_OPTION, Form.SOLADY, 0, w);
        int256[] memory f = new int256[](6);
        for (uint256 i; i < 6; i++) f[i] = (w[i] << 128) / 1e18;
        (bool okF, int256 rawF,,,) = runner.run(Scenario.DEEP_TAIL_OPTION, Form.BL127LIB, 0, f);
        assertTrue(okS && okF);
        int256 fp18 = rawF * 1e18 / (int256(1) << 128);
        // Black-Scholes at the money, 20% vol, six months, 5%: 6.8887...; WAD agrees to ~1e-16
        assertGt(fp18, 6.8e18); assertLt(fp18, 6.95e18);
        int256 diff = fp18 > rawS ? fp18 - rawS : rawS - fp18;
        assertLt(diff, 1e4, "generic normCdf through WAD within 1e-14 of BL127's");
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

    /// The adaptive-rate models (FraxLend, Euler) answer only their scenario.
    /// At one update after exactly one half-life FraxLend's F (1 + dt / H)
    /// is the documented 2x, and Euler's wExp at x = ln 2 is 2 to the wei.
    function test_rate_models_unsupported_elsewhere() public view {
        int256[] memory p = new int256[](6);
        p[0] = 1e9;
        p[2] = 1e18;
        p[3] = 86400e18;
        p[4] = 86400e18;
        p[5] = 0.693147180559945309e18 / int256(86400);
        for (uint8 f = Form.FRAXLEND; f <= Form.EULER; f++) {
            (bool ok,, bytes4 reason,,) = runner.run(Scenario.DECAY, f, 1, p);
            assertFalse(ok);
            assertEq(reason, bytes4(keccak256("Unsupported(uint8)")));
        }
        (bool okF, int256 rawF,,,) = runner.run(Scenario.ADAPTIVE_RATE, Form.FRAXLEND, 1, p);
        assertTrue(okF);
        assertEq(rawF, 2e9);
        (bool okE, int256 rawE,,,) = runner.run(Scenario.ADAPTIVE_RATE, Form.EULER, 1, p);
        assertTrue(okE);
        assertApproxEqAbs(rawE, 2e9, 1);
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

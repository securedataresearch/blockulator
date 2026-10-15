// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {FP127_ADDRESS, Form, Op} from "../../contracts/src/ladder/ILadder.sol";
import {EdgeRunner} from "../../contracts/src/ladder/EdgeRunner.sol";
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
import {LadderFP256} from "../../contracts/src/ladder/LadderFP256.sol";

/// @title Edges
/// @notice Produces the edges dataset: every probe of scripts/ladder/edge-inputs.json
///         through every form, one call each, by the same EdgeRunner that is
///         deployed on Sepolia. Prints EDGE|probe|form|ok|raw|reason|gas
///         (reason RANGE when the argument does not fit the representation,
///         in which case nothing is called) and scripts/ladder/edges.py
///         computes the truth and writes docs/benchmarks/edges.json.
contract Edges is Test {
    string constant INPUTS = "scripts/ladder/edge-inputs.json";
    string[11] FORMS = ["fp127", "fp127lib", "abdk", "solady", "prb", "quad", "balancer", "aave", "morpho", "maker", "fp256"];
    string[11] SCALE = ["fp127", "fp127", "abdk", "wad", "wad", "quad", "wad", "ray", "wad", "ray", "fp256"];

    EdgeRunner runner;
    string json;

    function setUp() public {
        bytes memory runtime = vm.parseJsonBytes(vm.readFile("out/FP127.yul/FP127.json"), ".deployedBytecode.object");
        vm.etch(FP127_ADDRESS, runtime);
        runner = new EdgeRunner([
            address(new LadderFP127()),
            address(new LadderFP127Lib()),
            address(new LadderABDK()),
            address(new LadderSolady()),
            address(new LadderPRB()),
            address(new LadderQuad()),
            address(new LadderBalancer()),
            address(new LadderAave()),
            address(new LadderMorpho()),
            address(new LadderMaker()),
            address(new LadderFP256())
        ]);
        json = vm.readFile(INPUTS);
    }

    function _args(string memory base, string memory key) internal view returns (int256[] memory a) {
        string[] memory s = vm.parseJsonStringArray(json, string.concat(base, ".", key));
        a = new int256[](s.length);
        for (uint256 i; i < s.length; i++) a[i] = vm.parseInt(s[i]);
    }

    function test_edges() public view {
        uint256 count = vm.parseJsonUint(json, ".count");
        for (uint256 c; c < count; c++) {
            string memory base = string.concat(".cells[", vm.toString(c), "]");
            string memory id = vm.parseJsonString(json, string.concat(base, ".id"));
            uint8 opIndex = uint8(vm.parseJsonUint(json, string.concat(base, ".opIndex")));
            for (uint8 f; f < Form.COUNT; f++) {
                if (vm.parseJsonBool(json, string.concat(base, ".unrepresentable.", SCALE[f]))) {
                    console.log(string.concat("EDGE|", id, "|", FORMS[f], "|0|0|RANGE|0"));
                    continue;
                }
                (bool ok, int256 raw, bytes4 reason, uint256 gas) = runner.run(opIndex, f, _args(base, SCALE[f]));
                console.log(string.concat("EDGE|", id, "|", FORMS[f], "|", ok ? "1" : "0", "|", vm.toString(raw), "|", vm.toString(reason), "|", vm.toString(gas)));
                if (f == Form.FP127LIB) {
                    (bool ok0, int256 raw0,,) = runner.run(opIndex, Form.FP127, _args(base, SCALE[0]));
                    assertEq(ok0, ok, string.concat(id, ": fp127/fp127lib ok differ"));
                    assertEq(raw0, raw, string.concat(id, ": fp127/fp127lib raw differ"));
                }
            }
        }
    }

    function test_edge_runner_catches_reverts() public view {
        int256[] memory a = new int256[](1);
        a[0] = -1e18;
        (bool ok, int256 raw, bytes4 reason, uint256 gas) = runner.run(Op.LN, Form.SOLADY, a);
        assertFalse(ok);
        assertEq(raw, 0);
        assertEq(gas, 0);
        assertTrue(reason != bytes4(0));
        (ok,, reason,) = runner.run(Op.W0, Form.PRB, a);
        assertFalse(ok);
        assertEq(reason, bytes4(keccak256("Unsupported(uint8)")));
    }
}

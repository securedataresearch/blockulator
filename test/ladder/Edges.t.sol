// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {BL127_ADDRESS, BL127E_ADDRESS, BL127H_ADDRESS, BL127N_ADDRESS, BL127S_ADDRESS, Form, Op} from "../../contracts/src/ladder/ILadder.sol";
import {EdgeRunner} from "../../contracts/src/ladder/EdgeRunner.sol";
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

/// @title Edges
/// @notice Produces the edges dataset: every probe of scripts/ladder/edge-inputs.json
///         through every form, one call each, by the same EdgeRunner that is
///         deployed on Sepolia. Prints EDGE|probe|form|ok|raw|reason|gas
///         (reason RANGE when the argument does not fit the representation,
///         in which case nothing is called) and scripts/ladder/edges.py
///         computes the truth and writes docs/benchmarks/edges.json.
contract Edges is Test {
    string constant INPUTS = "scripts/ladder/edge-inputs.json";
    string[18] FORMS = ["bl127", "bl127lib", "abdk", "solady", "prb", "quad", "balancer", "aave", "morpho", "maker", "bl19", "solmate", "oz", "uniswap", "prbud", "snekmate", "fraxlend", "euler"];
    string[18] SCALE = ["bl127", "bl127", "abdk", "wad", "wad", "quad", "wad", "ray", "wad", "ray", "bl19", "wad", "wad", "wad", "wad", "wad", "wad", "wad"];

    EdgeRunner runner;
    string json;

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
        runner = new EdgeRunner([
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
                if (f == Form.BL127LIB) {
                    (bool ok0, int256 raw0,,) = runner.run(opIndex, Form.BL127, _args(base, SCALE[0]));
                    assertEq(ok0, ok, string.concat(id, ": bl127/bl127lib ok differ"));
                    assertEq(raw0, raw, string.concat(id, ": bl127/bl127lib raw differ"));
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

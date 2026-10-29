// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {BL19_ADDRESS, BL19E_ADDRESS, BL19H_ADDRESS, BL19N_ADDRESS, BL19S_ADDRESS} from "../../contracts/src/ladder/ILadder.sol";
import {LadderBL19} from "../../contracts/src/ladder/LadderBL19.sol";
import {LadderBL19Deployed} from "../../contracts/src/ladder/LadderBL19Deployed.sol";

/// LadderBL19Deployed, the form the on-chain runners use, returns what LadderBL19 (inline, the form ladder.json is
/// generated from) returns, on every input of every scenario at every N of the ladder: the same word, or a revert
/// on both. The four BL19 objects' runtimes from the build artifacts are etched at their CREATE2 addresses, so
/// this is the bytecode the chain holds.
contract Bl19Deployed is Test {
    LadderBL19 inl;
    LadderBL19Deployed deployed;

    function _etch(address a, string memory name) internal {
        vm.etch(a, vm.parseJsonBytes(vm.readFile(string.concat("out/", name, ".yul/", name, ".json")), ".deployedBytecode.object"));
    }

    function setUp() public {
        _etch(BL19_ADDRESS, "BL19");
        _etch(BL19E_ADDRESS, "BL19E");
        _etch(BL19H_ADDRESS, "BL19H");
        _etch(BL19N_ADDRESS, "BL19N");
        _etch(BL19S_ADDRESS, "BL19S");
        inl = new LadderBL19();
        deployed = new LadderBL19Deployed();
    }

    function test_same_as_inline() public view {
        string memory json = vm.readFile("scripts/ladder/inputs.json");
        uint256[] memory ladder = vm.parseJsonUintArray(json, ".ladder");
        uint256 count = vm.parseJsonUint(json, ".count");
        uint256 cells;
        for (uint256 i; i < count; i++) {
            string memory base = string.concat(".cells[", vm.toString(i), "]");
            uint8 s = uint8(vm.parseJsonUint(json, string.concat(base, ".scenario")));
            string[] memory ps = vm.parseJsonStringArray(json, string.concat(base, ".bl19"));
            int256[] memory p = new int256[](ps.length);
            for (uint256 j; j < ps.length; j++) p[j] = vm.parseInt(ps[j]);
            for (uint256 k; k < ladder.length; k++) {
                uint32 n = uint32(ladder[k]);
                (bool okA, int256 a) = _run(address(inl), s, n, p);
                (bool okB, int256 b) = _run(address(deployed), s, n, p);
                assertEq(okA, okB, string.concat(base, " N=", vm.toString(n), ": one reverts"));
                assertEq(a, b, string.concat(base, " N=", vm.toString(n), ": different words"));
                cells++;
            }
        }
        assertGt(cells, 900);
    }

    function _run(address ad, uint8 s, uint32 n, int256[] memory p) internal view returns (bool ok, int256 raw) {
        (bool success, bytes memory ret) = ad.staticcall(abi.encodeWithSignature("run(uint8,uint32,int256[])", s, n, p));
        if (!success) return (false, int256(uint256(bytes32(ret.length >= 4 ? bytes32(bytes4(ret)) : bytes32(0)))));
        (raw,) = abi.decode(ret, (int256, uint256));
        ok = true;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Precision19} from "./Precision.t.sol";
import {IFP19} from "../../contracts/src/fp19/IFP19.sol";
import {IFP19E} from "../../contracts/src/fp19/IFP19E.sol";
import {IFP19H} from "../../contracts/src/fp19/IFP19H.sol";
import {IFP19N} from "../../contracts/src/fp19/IFP19N.sol";
import {IFP19S} from "../../contracts/src/fp19/IFP19S.sol";

/// @title Deployed19
/// @notice Post-deploy smoke test: every committed vector against the live
///         objects recorded in contracts/deployments/FP19.json, FP19E.json,
///         FP19H.json and FP19S.json (the number, the elementary, hyperbolic
///         and special functions); an object without a record keeps the
///         local artifact.
///
///   make smoke-fp19-sepolia      (forge test --match-contract Deployed19 --fork-url <sepolia rpc>)
///
/// Skips itself unless the fork is Sepolia, so `make test` never touches
/// the network.
contract Deployed19 is Precision19 {
    uint256 constant SEPOLIA = 11155111;

    function _out() internal pure override returns (string memory) { return ""; }

    function setUp() public override {
        super.setUp();
        if (block.chainid == SEPOLIA) {
            string memory json = vm.readFile("contracts/deployments/FP19.json");
            address live = vm.parseJsonAddress(json, ".address");
            require(live.code.length > 0, "no code at the recorded FP19 address");
            obj = IFP19(live);
            address a = _live("FP19E");
            if (a != address(0)) objE = IFP19E(a);
            a = _live("FP19H");
            if (a != address(0)) objH = IFP19H(a);
            a = _live("FP19N");
            if (a != address(0)) objN = IFP19N(a);
            a = _live("FP19S");
            if (a != address(0)) objS = IFP19S(a);
        }
    }

    /// The recorded address of object name, or zero when it has no record.
    function _live(string memory name) internal view returns (address a) {
        string memory path = string.concat("contracts/deployments/", name, ".json");
        if (!vm.exists(path)) return address(0);
        a = vm.parseJsonAddress(vm.readFile(path), ".address");
        require(a.code.length > 0, string.concat("no code at the recorded ", name, " address"));
    }

    function test_precision_all() public override {
        vm.skip(block.chainid != SEPOLIA);
        super.test_precision_all();
    }
}

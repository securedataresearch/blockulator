// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Precision19} from "./Precision.t.sol";
import {IBL19} from "../../contracts/src/bl19/IBL19.sol";
import {IBL19E} from "../../contracts/src/bl19/IBL19E.sol";
import {IBL19H} from "../../contracts/src/bl19/IBL19H.sol";
import {IBL19N} from "../../contracts/src/bl19/IBL19N.sol";
import {IBL19S} from "../../contracts/src/bl19/IBL19S.sol";

/// @title Deployed19
/// @notice Post-deploy smoke test: every committed vector against the live
///         objects recorded in contracts/deployments/BL19.json, BL19E.json,
///         BL19H.json and BL19S.json (the number, the elementary, hyperbolic
///         and special functions); an object without a record keeps the
///         local artifact.
///
///   make smoke-bl19-sepolia      (forge test --match-contract Deployed19 --fork-url <sepolia rpc>)
///
/// Skips itself unless the fork is Sepolia, so `make test` never touches
/// the network.
contract Deployed19 is Precision19 {
    uint256 constant SEPOLIA = 11155111;

    function _out() internal pure override returns (string memory) { return ""; }

    function setUp() public override {
        super.setUp();
        if (block.chainid == SEPOLIA) {
            string memory json = vm.readFile("contracts/deployments/BL19.json");
            address live = vm.parseJsonAddress(json, ".address");
            require(live.code.length > 0, "no code at the recorded BL19 address");
            obj = IBL19(live);
            address a = _live("BL19E");
            if (a != address(0)) objE = IBL19E(a);
            a = _live("BL19H");
            if (a != address(0)) objH = IBL19H(a);
            a = _live("BL19N");
            if (a != address(0)) objN = IBL19N(a);
            a = _live("BL19S");
            if (a != address(0)) objS = IBL19S(a);
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

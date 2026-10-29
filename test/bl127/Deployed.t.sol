// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Precision} from "./Precision.t.sol";
import {IBL127} from "../../contracts/src/bl127/IBL127.sol";
import {IBL127E} from "../../contracts/src/bl127/IBL127E.sol";
import {IBL127H} from "../../contracts/src/bl127/IBL127H.sol";
import {IBL127N} from "../../contracts/src/bl127/IBL127N.sol";
import {IBL127S} from "../../contracts/src/bl127/IBL127S.sol";

/// @title Deployed
/// @notice Post-deploy smoke test: every committed vector against the live
///         objects recorded in contracts/deployments/BL127.json, BL127E.json,
///         BL127H.json, BL127N.json and BL127S.json (the number, the
///         elementary, hyperbolic, normal and special functions); an object
///         without a record keeps the local artifact.
///
///   make smoke-sepolia      (forge test --match-contract Deployed --fork-url <sepolia rpc>)
///
/// Skips itself unless the fork is Sepolia, so `make test` never touches
/// the network.
contract Deployed is Precision {
    uint256 constant SEPOLIA = 11155111;

    function _out() internal pure override returns (string memory) { return ""; }

    function setUp() public override {
        super.setUp();
        if (block.chainid == SEPOLIA) {
            string memory json = vm.readFile("contracts/deployments/BL127.json");
            address live = vm.parseJsonAddress(json, ".address");
            require(live.code.length > 0, "no code at the recorded address");
            obj = IBL127(live);
            address a = _live("BL127E");
            if (a != address(0)) objE = IBL127E(a);
            a = _live("BL127H");
            if (a != address(0)) objH = IBL127H(a);
            a = _live("BL127N");
            if (a != address(0)) objN = IBL127N(a);
            a = _live("BL127S");
            if (a != address(0)) objS = IBL127S(a);
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

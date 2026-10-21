// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Precision256} from "./Precision.t.sol";
import {IFP256} from "../../contracts/src/fp256/IFP256.sol";
import {IFP256X} from "../../contracts/src/fp256/IFP256X.sol";
import {IFP256X2} from "../../contracts/src/fp256/IFP256X2.sol";
import {IFP256X3} from "../../contracts/src/fp256/IFP256X3.sol";

/// @title Deployed256
/// @notice Post-deploy smoke test: every committed vector against the live
///         FP256 object recorded in contracts/deployments/FP256.json and, from
///         release four, the FP256X, FP256X2 and FP256X3 objects in
///         contracts/deployments/FP256X.json, FP256X2.json and FP256X3.json.
///
///   make smoke-fp256-sepolia      (forge test --match-contract Deployed256 --fork-url <sepolia rpc>)
///
/// Skips itself unless the fork is Sepolia, so `make test` never touches
/// the network.
contract Deployed256 is Precision256 {
    uint256 constant SEPOLIA = 11155111;

    function _out() internal pure override returns (string memory) { return ""; }

    function setUp() public override {
        super.setUp();
        if (block.chainid == SEPOLIA) {
            string memory json = vm.readFile("contracts/deployments/FP256.json");
            address live = vm.parseJsonAddress(json, ".address");
            require(live.code.length > 0, "no code at the recorded FP256 address");
            obj = IFP256(live);
            // release four's second object, once its record exists
            if (vm.exists("contracts/deployments/FP256X.json")) {
                address liveX = vm.parseJsonAddress(vm.readFile("contracts/deployments/FP256X.json"), ".address");
                require(liveX.code.length > 0, "no code at the recorded FP256X address");
                objX = IFP256X(liveX);
            }
            // #79's objects, once their records exist
            if (vm.exists("contracts/deployments/FP256X2.json")) {
                address liveX2 = vm.parseJsonAddress(vm.readFile("contracts/deployments/FP256X2.json"), ".address");
                require(liveX2.code.length > 0, "no code at the recorded FP256X2 address");
                objX2 = IFP256X2(liveX2);
            }
            if (vm.exists("contracts/deployments/FP256X3.json")) {
                address liveX3 = vm.parseJsonAddress(vm.readFile("contracts/deployments/FP256X3.json"), ".address");
                require(liveX3.code.length > 0, "no code at the recorded FP256X3 address");
                objX3 = IFP256X3(liveX3);
            }
        }
    }

    function test_precision_all() public override {
        vm.skip(block.chainid != SEPOLIA);
        super.test_precision_all();
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Precision256} from "./Precision.t.sol";
import {IFP256} from "../../contracts/src/fp256/IFP256.sol";

/// @title Deployed256
/// @notice Post-deploy smoke test: every committed vector against the live
///         FP256 object recorded in contracts/deployments/FP256.json.
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
        }
    }

    function test_precision_all() public override {
        vm.skip(block.chainid != SEPOLIA);
        super.test_precision_all();
    }
}

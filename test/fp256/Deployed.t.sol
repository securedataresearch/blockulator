// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Precision256} from "./Precision.t.sol";
import {IFP256} from "../../contracts/src/fp256/IFP256.sol";
import {IFP256E} from "../../contracts/src/fp256/IFP256E.sol";
import {IFP256H} from "../../contracts/src/fp256/IFP256H.sol";
import {IFP256S} from "../../contracts/src/fp256/IFP256S.sol";

/// @title Deployed256
/// @notice Post-deploy smoke test: every committed vector against the live
///         objects recorded in contracts/deployments/FP256.json, FP256E.json,
///         FP256H.json and FP256S.json (the number, the elementary, hyperbolic
///         and special functions); an object without a record keeps the
///         local artifact.
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
            address a = _live("FP256E");
            if (a != address(0)) objE = IFP256E(a);
            a = _live("FP256H");
            if (a != address(0)) objH = IFP256H(a);
            a = _live("FP256S");
            if (a != address(0)) objS = IFP256S(a);
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

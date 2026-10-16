// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";

/// @title DeployFP256
/// @notice Deploys the generated FP256 Yul object through Arachnid's
///         deterministic CREATE2 proxy, so the same bytecode lands at the
///         same address on every chain the proxy exists on.
///
///   forge script script/DeployFP256.s.sol --sig "predict()" --rpc-url <rpc>
///   forge script script/DeployFP256.s.sol --rpc-url <rpc> --private-key <key> --broadcast
///
/// The init code is read from the Foundry artifact the same way the test
/// harness does (Yul artifacts carry a null ABI, so vm.getCode refuses
/// them). There are no constructor arguments, so the address depends only on
/// FP256.yul and the compiler settings in foundry.toml.
contract DeployFP256 is Script {
    /// Arachnid's deterministic-deployment-proxy, present on every major chain.
    address constant DEPLOYER = 0x4e59b44847b379578588920cA78FbF26c0B4956C;
    /// Published salt. ASCII "FP256 v3", right-padded with zeros (release three: 28 ops, adding log1p, expm1, erf, erfc, normCdf, lambertW0, lambertWm1, powu and compound; release two was "FP256 v2", release one "FP256 v1").
    bytes32 constant SALT = bytes32("FP256 v3");
    string constant ARTIFACT = "out/FP256.yul/FP256.json";

    function _artifact() internal view returns (bytes memory initCode, bytes memory runtime) {
        string memory json = vm.readFile(ARTIFACT);
        initCode = vm.parseJsonBytes(json, ".bytecode.object");
        runtime = vm.parseJsonBytes(json, ".deployedBytecode.object");
    }

    function _predict(bytes memory initCode) internal pure returns (address) {
        return address(uint160(uint256(keccak256(abi.encodePacked(bytes1(0xff), DEPLOYER, SALT, keccak256(initCode))))));
    }

    function _log(bytes memory initCode, bytes memory runtime, address predicted) internal pure {
        console.log("deployer        ", DEPLOYER);
        console.log("salt            ", vm.toString(SALT));
        console.log("init code hash  ", vm.toString(keccak256(initCode)));
        console.log("runtime keccak  ", vm.toString(keccak256(runtime)));
        console.log("runtime bytes   ", runtime.length);
        console.log("address         ", predicted);
    }

    /// Prints the deterministic address without broadcasting anything.
    function predict() public view returns (address predicted) {
        (bytes memory initCode, bytes memory runtime) = _artifact();
        predicted = _predict(initCode);
        _log(initCode, runtime, predicted);
        console.log("deployed here   ", predicted.code.length > 0);
    }

    /// Deploys if and only if nothing is at the predicted address yet.
    function run() public {
        (bytes memory initCode, bytes memory runtime) = _artifact();
        address predicted = _predict(initCode);
        _log(initCode, runtime, predicted);
        require(DEPLOYER.code.length > 0, "CREATE2 proxy missing on this chain");

        if (predicted.code.length > 0) {
            require(keccak256(predicted.code) == keccak256(runtime), "address occupied by different code");
            console.log("already deployed, nothing to do");
            return;
        }

        vm.broadcast();
        (bool ok,) = DEPLOYER.call(abi.encodePacked(SALT, initCode));
        require(ok, "CREATE2 proxy call failed");
        require(predicted.code.length > 0, "no code at predicted address");
        require(keccak256(predicted.code) == keccak256(runtime), "deployed runtime differs from artifact");
        console.log("deployed");
    }
}

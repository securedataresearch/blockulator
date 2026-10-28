// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {CompoundExample} from "./CompoundExample.sol";
import {StaticcallExample} from "./StaticcallExample.sol";

/// @notice The two snippets on the library page compile and agree with the
///         compound scenario's reference input of the ladder
///         (docs/benchmarks/ladder.json, compound, reference, N = 365:
///         11051.5578161626437393801159668...). The WAD
///         rate is truncated to 18 decimals, so the match is to about 15
///         digits, not 36; that gap is the point of the why page.
contract ExamplesTest is Test {
    int256 constant TRUTH_WAD = 11051557816162643739380; // floor to 18 decimals
    int256 constant TOL = 1e8;                        // 1e-10 of a unit

    function test_inlineExample() public {
        CompoundExample ex = new CompoundExample();
        int256 got = ex.accrue(10_000e18, int256(0.1e18) / 365, 365);
        assertApproxEqAbs(got, TRUTH_WAD, uint256(TOL));
    }

    function test_staticcallExample() public {
        // the deployed object's runtime, installed at its Sepolia address
        bytes memory initCode = vm.parseJsonBytes(vm.readFile("out/FP127.yul/FP127.json"), ".bytecode.object");
        address deployed;
        assembly ("memory-safe") { deployed := create(0, add(initCode, 0x20), mload(initCode)) }
        vm.etch(0x466eCEde5Dc25189AD9ED999d0B4D41Cb022510B, deployed.code);
        StaticcallExample ex = new StaticcallExample();
        int256 got = ex.accrue(10_000e18, int256(0.1e18) / 365, 365);
        assertApproxEqAbs(got, TRUTH_WAD, uint256(TOL));
    }
}

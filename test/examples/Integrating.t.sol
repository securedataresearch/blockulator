// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {FP127Lib} from "fp127/FP127Lib.sol";
import {FP256Lib} from "fp256/FP256Lib.sol";
import {IdleBalance127, IdleBalance256, Solvency127, Solvency256, JoinExit256, SwapCharge256} from "./Integrating.sol";

/// @notice The "Integrating" snippets, run on the replays' own integers. Every expected
///         value here is a number in docs/benchmarks/replay-*.md, from the data in
///         scripts/replays/*.json; the replay tests in test/replays/ assert them first.
contract IntegratingTest is Test {
    // ---- Rule 1: Bunni (docs/benchmarks/replay-bunni.md, scripts/replays/bunni.json) -------------

    function _uints(string memory json, string memory key) internal pure returns (uint256[] memory a) {
        string[] memory s = vm.parseJsonStringArray(json, key);
        a = new uint256[](s.length);
        for (uint256 k; k < s.length; k++) a[k] = vm.parseUint(s[k]);
    }

    function test_bunni_stateInTheFormat() public {
        string memory json = vm.readFile("scripts/replays/bunni.json");
        uint256 idle0 = vm.parseUint(vm.parseJsonString(json, ".start.idle"));
        uint256[] memory shares = _uints(json, ".steps.shares");
        uint256[] memory supply = _uints(json, ".steps.totalSupply");
        assertEq(shares.length, 44);

        IdleBalance127 a = new IdleBalance127(idle0);
        IdleBalance256 b = new IdleBalance256(idle0);
        uint256 deployed = idle0; // BunniHubLogic.sol:478, whole wei
        uint256 fix = idle0; // the fix: mulDivUp on the subtrahend
        uint256 storedUp = idle0; // the FP127 update, rounded up to wei before each store
        uint256 storedDown = idle0; // the same, rounded down
        for (uint256 k; k < 44; k++) {
            uint256 s = shares[k];
            uint256 t = supply[k];
            a.withdraw(s, t);
            b.withdraw(s, t);
            deployed -= deployed * s / t;
            fix -= (fix * s + t - 1) / t;
            int256 u = FP127Lib.sub(int256(storedUp) << 128, FP127Lib.div(FP127Lib.mul(int256(storedUp) << 128, int256(s) << 128), int256(t) << 128));
            storedUp = uint256(FP127Lib.ceil(u) >> 128);
            int256 d = FP127Lib.sub(int256(storedDown) << 128, FP127Lib.div(FP127Lib.mul(int256(storedDown) << 128, int256(s) << 128), int256(t) << 128));
            storedDown = uint256(FP127Lib.floor(d) >> 128);
        }
        // the deployed code ends with 4 wei active (replay-bunni.md), which fixes the final balance
        uint256 balance = deployed + 4;
        // kept in the format: 35.63 wei, floored once to 35
        assertEq(a.active(balance), 35);
        assertEq(b.active(balance), 35);
        // the fix ends at 48 wei, 12.37 high
        assertEq(balance - fix, 48);
        // rounding the stored word to wei gives the integer answers back:
        // up before each store is the deployed code, down is the fix
        assertEq(storedUp, deployed);
        assertEq(storedDown, fix);
    }

    // ---- Rule 2: Resupply (docs/benchmarks/replay-resupply.md, scripts/replays/resupply.json) -----

    function _pin(string memory json, string memory key) internal pure returns (uint256) {
        return vm.parseUint(vm.parseJsonString(json, string.concat(".pins.", key)));
    }

    function test_resupply_roundTowardTheProtocol() public view {
        string memory json = vm.readFile("scripts/replays/resupply.json");
        uint256 price = _pin(json, "price");
        uint256 debt = _pin(json, "borrowAmount");
        uint256 collateral = _pin(json, "collateral");
        uint256 maxLTV = _pin(json, "maxLTV");
        // as deployed: 1e36 / price floors to 0, the LTV is 0, the borrow passes
        assertEq(1e36 / price, 0);

        assertFalse(Solvency127.isSolvent(debt, price, collateral, maxLTV));
        assertFalse(Solvency256.isSolvent(debt, price, collateral, maxLTV));
        // LTV ceil to the 1e5 grid: 500,000,000,000
        assertEq(Solvency127.ltvOnGrid(debt, price, collateral), 500_000_000_000);
        assertEq(Solvency256.ltvOnGrid(debt, price, collateral), 500_000_000_000);
        // the most the 1-wei position may owe at maxLTV: 1.9 reUSD
        assertEq(Solvency127.maxBorrow(collateral, maxLTV, price), 1.9e18);
        assertEq(Solvency256.maxBorrow(collateral, maxLTV, price), 1.9e18);
    }

    // ---- Rule 2: Balancer V1 (docs/benchmarks/replay-balancer-v1.md; constants from
    //      test/replays/BalancerV1.t.sol, solved by scripts/replays/balancer_v1.py score) ---------

    uint256 constant BAL = 3; // WBTC satoshi, pool 1's first join at a balance of 3
    uint256 constant SUPPLY = 6464513554335253717;
    uint256 constant W = 12.5e18;
    uint256 constant TW = 50e18;
    uint256 constant FEE = 0.005e18;
    uint256 constant DECISIVE_POOL_OUT = 689646715905234062;
    uint256 constant NEAREST_JOIN_P = 687409992083284011;
    uint256 constant NEAREST_EXIT_P = 235740524732716483;
    uint256 constant TOWARD_JOIN_P = 480429659539467039;
    uint256 constant TOWARD_EXIT_P = 483973556600802202;

    function test_balancerV1_directionNotPrecision() public pure {
        // the decisive join: exact 1.5056 satoshi; deployed charged 1, toward the pool 2 > maxAmountIn
        assertEq(JoinExit256.joinCost(BAL, W, SUPPLY, TW, DECISIVE_POOL_OUT, FEE), 2);
        // re-tuned to round-to-nearest: just under 1.5 in, just over 0.5 out; nearest pays both
        // (test/replays/BalancerV1.t.sol asserts nearest = 1 for both), toward the pool pays neither
        assertEq(JoinExit256.joinCost(BAL, W, SUPPLY, TW, NEAREST_JOIN_P, FEE), 2);
        assertEq(JoinExit256.exitPays(4, W, SUPPLY + NEAREST_JOIN_P, TW, NEAREST_EXIT_P, FEE), 0);
        // re-tuned to the pool's direction: the most one satoshi buys, the least that pays one out
        assertEq(JoinExit256.joinCost(BAL, W, SUPPLY, TW, TOWARD_JOIN_P, FEE), 1);
        assertEq(JoinExit256.joinCost(BAL, W, SUPPLY, TW, TOWARD_JOIN_P + 1, FEE), 2);
        assertEq(JoinExit256.exitPays(4, W, SUPPLY + TOWARD_JOIN_P, TW, TOWARD_EXIT_P, FEE), 1);
        assertEq(JoinExit256.exitPays(4, W, SUPPLY + TOWARD_JOIN_P, TW, TOWARD_EXIT_P - 1, FEE), 0);
        // so a cycle buys less BPT than it sells: the loop runs backwards
        assertLt(TOWARD_JOIN_P, TOWARD_EXIT_P);
    }

    // ---- Rule 2: Balancer V2 (docs/benchmarks/replay-balancer.md) -------------------------------

    function test_balancerV2_upscaleKeptInTheFormat() public pure {
        // 17 osETH-wei x 1.058132408689971699: _upscale (mulDown) reads 17; the true 17.988...
        int256 up = SwapCharge256.upscale(17, 1058132408689971699);
        assertEq(FP256Lib.toUintDown(up), 17);
        assertEq(FP256Lib.toUintUp(up), 18);
        assertEq(FP256Lib.toFixed18(up), 17988250947729518883);
        // 4 wstETH-wei x 1.218116415279760760 = 4.87: read as 4
        assertEq(FP256Lib.toUintDown(SwapCharge256.upscale(4, 1218116415279760760)), 4);
    }

    function test_balancerV2_chargeRoundsUp() public pure {
        // 0.01% fee: an amount in of exactly 999,900 wei grosses up to exactly 1,000,000
        assertEq(SwapCharge256.chargeIn(FP256Lib.fromUint(999_900), 1e14), 1_000_000);
        // one part in 2^200 above it is charged one more wei
        int256 above = FP256Lib.mulUp(FP256Lib.fromUint(999_900), FP256Lib.add(FP256Lib.ONE, FP256Lib.div(FP256Lib.ONE, FP256Lib.fromUint(1 << 200))));
        assertEq(SwapCharge256.chargeIn(above, 1e14), 1_000_001);
        // dust is charged one wei, never zero
        assertEq(SwapCharge256.chargeIn(FP256Lib.div(FP256Lib.ONE, FP256Lib.fromUint(1e30)), 1e14), 1);
    }
}

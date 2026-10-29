// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {BL127Lib} from "bl127/BL127Lib.sol";
import {BL19Lib} from "bl19/BL19Lib.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {IdleBalance127, IdleBalance19, Solvency127, Solvency19, JoinExit19, SwapCharge19, DivideLast, Index127, LogIndex127} from "./Integrating.sol";

/// @notice The "Integrating" snippets, run on the replays' own integers. Every expected
///         value here is a number in docs/benchmarks/replay-*.md, from the data in
///         scripts/replays/*.json; the replay tests in test/replays/ assert them first.
///         The mulDiv127 and logIndex tests have no replay. mulDiv127 uses exact powers of
///         two; the logIndex tests measure both forms of an index against e^L in BL19, and
///         the pages quote what they log (`forge test --match-test logIndex -vv`).
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
        IdleBalance19 b = new IdleBalance19(idle0);
        uint256 deployed = idle0; // BunniHubLogic.sol:478, whole wei
        uint256 fix = idle0; // the fix: mulDivUp on the subtrahend
        uint256 storedUp = idle0; // the BL127 update, rounded up to wei before each store
        uint256 storedDown = idle0; // the same, rounded down
        for (uint256 k; k < 44; k++) {
            uint256 s = shares[k];
            uint256 t = supply[k];
            a.withdraw(s, t);
            b.withdraw(s, t);
            deployed -= deployed * s / t;
            fix -= (fix * s + t - 1) / t;
            int256 u = BL127Lib.sub(int256(storedUp) << 128, BL127Lib.div(BL127Lib.mul(int256(storedUp) << 128, int256(s) << 128), int256(t) << 128));
            storedUp = uint256(BL127Lib.ceil(u) >> 128);
            int256 d = BL127Lib.sub(int256(storedDown) << 128, BL127Lib.div(BL127Lib.mul(int256(storedDown) << 128, int256(s) << 128), int256(t) << 128));
            storedDown = uint256(BL127Lib.floor(d) >> 128);
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
        assertFalse(Solvency19.isSolvent(debt, price, collateral, maxLTV));
        // LTV ceil to the 1e5 grid: 500,000,000,000
        assertEq(Solvency127.ltvOnGrid(debt, price, collateral), 500_000_000_000);
        assertEq(Solvency19.ltvOnGrid(debt, price, collateral), 500_000_000_000);
        // the most the 1-wei position may owe at maxLTV: 1.9 reUSD
        assertEq(Solvency127.maxBorrow(collateral, maxLTV, price), 1.9e18);
        assertEq(Solvency19.maxBorrow(collateral, maxLTV, price), 1.9e18);
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
        assertEq(JoinExit19.joinCost(BAL, W, SUPPLY, TW, DECISIVE_POOL_OUT, FEE), 2);
        // re-tuned to round-to-nearest: just under 1.5 in, just over 0.5 out; nearest pays both
        // (test/replays/BalancerV1.t.sol asserts nearest = 1 for both), toward the pool pays neither
        assertEq(JoinExit19.joinCost(BAL, W, SUPPLY, TW, NEAREST_JOIN_P, FEE), 2);
        assertEq(JoinExit19.exitPays(4, W, SUPPLY + NEAREST_JOIN_P, TW, NEAREST_EXIT_P, FEE), 0);
        // re-tuned to the pool's direction: the most one satoshi buys, the least that pays one out
        assertEq(JoinExit19.joinCost(BAL, W, SUPPLY, TW, TOWARD_JOIN_P, FEE), 1);
        assertEq(JoinExit19.joinCost(BAL, W, SUPPLY, TW, TOWARD_JOIN_P + 1, FEE), 2);
        assertEq(JoinExit19.exitPays(4, W, SUPPLY + TOWARD_JOIN_P, TW, TOWARD_EXIT_P, FEE), 1);
        assertEq(JoinExit19.exitPays(4, W, SUPPLY + TOWARD_JOIN_P, TW, TOWARD_EXIT_P - 1, FEE), 0);
        // so a cycle buys less BPT than it sells: the loop runs backwards
        assertLt(TOWARD_JOIN_P, TOWARD_EXIT_P);
    }

    // ---- Rule 2: Balancer V2 (docs/benchmarks/replay-balancer.md) -------------------------------

    function test_balancerV2_upscaleKeptInTheFormat() public pure {
        // 17 osETH-wei x 1.058132408689971699: _upscale (mulDown) reads 17; the true 17.988...
        int256 up = SwapCharge19.upscale(17, 1058132408689971699);
        assertEq(BL19Lib.toUintDown(up), 17);
        assertEq(BL19Lib.toUintUp(up), 18);
        assertEq(BL19Lib.toFixed18(up), 17988250947729518883);
        // 4 wstETH-wei x 1.218116415279760760 = 4.87: read as 4
        assertEq(BL19Lib.toUintDown(SwapCharge19.upscale(4, 1218116415279760760)), 4);
    }

    function test_balancerV2_chargeRoundsUp() public pure {
        // 0.01% fee: an amount in of exactly 999,900 wei grosses up to exactly 1,000,000
        assertEq(SwapCharge19.chargeIn(BL19Lib.fromUint(999_900), 1e14), 1_000_000);
        // one part in 2^200 above it is charged one more wei
        int256 above = BL19Lib.mulUp(BL19Lib.fromUint(999_900), BL19Lib.add(BL19Lib.ONE, BL19Lib.div(BL19Lib.ONE, BL19Lib.fromUint(1 << 200))));
        assertEq(SwapCharge19.chargeIn(above, 1e14), 1_000_001);
        // dust is charged one wei, never zero
        assertEq(SwapCharge19.chargeIn(BL19Lib.div(BL19Lib.ONE, BL19Lib.fromUint(1e30)), 1e14), 1);
    }

    // ---- Divide last: Resupply (docs/benchmarks/replay-resupply.md, "divide by the price at the end") --

    function test_resupply_divideLast() public view {
        string memory json = vm.readFile("scripts/replays/resupply.json");
        uint256 price = _pin(json, "price");
        uint256 debt = _pin(json, "borrowAmount");
        uint256 collateral = _pin(json, "collateral");
        uint256 maxLTV = _pin(json, "maxLTV");
        // divide first, as deployed: the rate floors to 0 and so does the LTV
        assertEq(debt * (1e36 / price) * 1e5 / 1e18 / collateral, 0);
        // divide last, rounded up: 500,000,000,000 against a cap of 95,000; the borrow reverts
        assertEq(DivideLast.ltvUp(debt, price, collateral), 500_000_000_000);
        // rounded down instead: 499,999,999,999, the same verdict
        assertEq(FixedPointMathLib.fullMulDiv(debt, 1e23, price * collateral), 499_999_999_999);
        // the most the 1-wei position may owe at maxLTV: 1.9 reUSD
        assertEq(DivideLast.maxBorrow(collateral, maxLTV, price), 1.9e18);
    }

    function test_mulDiv127_oneRounding() public pure {
        // 2^-100 x 2^-40 / 2^-60 = 2^-80, a word of 2^48 raw units. Every input is an exact word.
        int256 a = 1 << 28;
        int256 b = 1 << 88;
        int256 c = 1 << 68;
        // the product 2^-140 is below 2^-128, so mul floors it to 0 before the division
        assertEq(BL127Lib.mul(a, b), 0);
        assertEq(BL127Lib.div(BL127Lib.mul(a, b), c), 0);
        // one 512-bit product, one division: exact here
        assertEq(DivideLast.mulDiv127(a, b, c), 1 << 48);
    }

    // ---- Accrue in the log: N accruals of a continuous rate, both ways --------------------------
    //
    // Rates are uniform below 2^-28 per second (up to about 12% a year), dt uniform in 1..86,400 s.
    // The reference is e^L in BL19: L is exact, fromBL127 is exact, exp is correctly rounded to 237
    // bits, so its own error is about 2^-109 units of 2^-128. Errors are in millionths of 2^-128.

    function _rate(uint256 seed, uint256 k) internal pure returns (int256) {
        return int256(uint256(keccak256(abi.encode(seed, k, "r"))) % (1 << 100));
    }

    function _dt(uint256 seed, uint256 k) internal pure returns (uint256) {
        return 1 + uint256(keccak256(abi.encode(seed, k, "t"))) % 86_400;
    }

    /// (w - ref) in millionths of 2^-128
    function _err(int256 w, int256 ref) internal pure returns (int256) {
        return BL19Lib.toFixed18(BL19Lib.mul(BL19Lib.sub(BL19Lib.fromBL127(w), ref), BL19Lib.fromUint(1 << 128))) / 1e12;
    }

    function _abs(int256 x) internal pure returns (int256) {
        return x < 0 ? -x : x;
    }

    function _accrue(uint256 n, uint256 seed) internal returns (int256 logErr, int256 mulErr) {
        Index127 m = new Index127();
        LogIndex127 l = new LogIndex127();
        for (uint256 k; k < n; k++) {
            m.accrue(_rate(seed, k), _dt(seed, k));
            l.accrue(_rate(seed, k), _dt(seed, k));
        }
        int256 ref = BL19Lib.exp(BL19Lib.fromBL127(l.logIndex()));
        logErr = _err(l.index(), ref);
        mulErr = _err(m.index(), ref);
        // the BL19 read, rounded to BL127, is the same word
        assertEq(BL19Lib.toBL127(l.index19()), l.index());
        console.log(string.concat("accrual N=", vm.toString(n), " seed=", vm.toString(seed),
            " log read err=", vm.toString(logErr), " multiplied err=", vm.toString(mulErr), " (1e-6 x 2^-128)"));
    }

    function test_logIndex_accrual() public {
        for (uint256 seed; seed < 3; seed++) {
            // one accrual: both are the same single exp
            (int256 l1, int256 m1) = _accrue(1, seed);
            assertEq(l1, m1);
            assertLe(_abs(l1), 500_001);
            // more: the log read stays within half a unit; the product drifts about half a unit per accrual
            (int256 l10, int256 m10) = _accrue(10, seed);
            assertLe(_abs(l10), 500_001);
            assertGt(_abs(m10), 1_000_000);
            (int256 l1000, int256 m1000) = _accrue(1000, seed);
            assertLe(_abs(l1000), 500_001);
            assertGt(_abs(m1000), 500_000_000);
        }
    }

    /// The limit: a per-period rate r over n periods. log1p(r) rounds once, and that rounding is
    /// added n times; compound(r, n) rounds once for the whole run.
    function test_logIndex_perPeriodRateLoses() public pure {
        for (uint256 seed; seed < 2; seed++) {
            int256 L;
            int256 idx = 1 << 128;
            int256 ref = BL19Lib.ONE;
            for (uint256 k; k < 100; k++) {
                int256 r = _rate(seed, k);
                uint256 n = _dt(seed, k);
                L = BL127Lib.add(L, BL127Lib.log1p(r) * int256(n));
                idx = BL127Lib.mul(idx, BL127Lib.compound(r, int256(n) << 128));
                ref = BL19Lib.mul(ref, BL19Lib.compound(BL19Lib.fromBL127(r), int256(n)));
            }
            int256 logErr = _err(BL127Lib.exp(L), ref);
            int256 mulErr = _err(idx, ref);
            console.log(string.concat("per-period N=100 seed=", vm.toString(seed), " log1p x n err=", vm.toString(logErr),
                " compound err=", vm.toString(mulErr), " (1e-6 x 2^-128)"));
            assertGt(_abs(logErr), 100_000_000_000); // over 100,000 units of 2^-128
            assertLt(_abs(mulErr), 100_000_000); // under 100
        }
    }

    /// In BL19 the product drifts too, at BL19's scale: each exp and mul rounds to nearest,
    /// so the drift is a random walk of 2^-237-sized steps. Measured in parts of 2^236.
    function test_logIndex_bl19Drift() public {
        for (uint256 seed; seed < 3; seed++) {
            LogIndex127 l = new LogIndex127();
            int256 idx = BL19Lib.ONE;
            for (uint256 k; k < 1000; k++) {
                l.accrue(_rate(seed, k), _dt(seed, k));
                idx = BL19Lib.mul(idx, BL19Lib.exp(BL19Lib.fromBL127(_rate(seed, k) * int256(_dt(seed, k)))));
            }
            int256 rd = l.index19();
            int256 rel = BL19Lib.div(BL19Lib.sub(idx, rd), rd);
            int256 parts = BL19Lib.toFixed18(BL19Lib.mul(rel, BL19Lib.pow(BL19Lib.fromUint(2), BL19Lib.fromUint(236)))) / 1e12;
            console.log(string.concat("bl19 N=1000 seed=", vm.toString(seed), " multiplied vs log read=", vm.toString(parts), " (1e-6 x 2^-236)"));
            assertGt(_abs(parts), 0);
            assertLt(_abs(parts), 100_000_000); // under 100 parts in 2^236
        }
    }

    function test_logIndex_readPast88() public {
        LogIndex127 l = new LogIndex127();
        l.accrue(int256(1) << 128, 100); // L = 100
        vm.expectRevert();
        l.index(); // BL127's exp stops at 88
        // BL19 reads e^100, about 2.7e43, past BL127's 2^127
        assertGt(BL19Lib.cmp(l.index19(), BL19Lib.fromUint(1 << 127)), 0);
    }
}

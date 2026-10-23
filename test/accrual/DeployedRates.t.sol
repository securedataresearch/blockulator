// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {FraxlendRate, LadderFraxlend} from "../../contracts/src/ladder/LadderFraxlend.sol";
import {EulerAdaptiveCurve, LadderEuler} from "../../contracts/src/ladder/LadderEuler.sol";
import {Scenario} from "../../contracts/src/ladder/ILadder.sol";

interface IFraxRate {
    function MIN_TARGET_UTIL() external view returns (uint256);
    function MAX_TARGET_UTIL() external view returns (uint256);
    function VERTEX_UTILIZATION() external view returns (uint256);
    function MIN_FULL_UTIL_RATE() external view returns (uint256);
    function MAX_FULL_UTIL_RATE() external view returns (uint256);
    function ZERO_UTIL_RATE() external view returns (uint256);
    function RATE_HALF_LIFE() external view returns (uint256);
    function VERTEX_RATE_PERCENT() external view returns (uint256);
    function getNewRate(uint256 deltaTime, uint256 utilization, uint64 oldFullUtilizationInterest)
        external
        view
        returns (uint64 newRatePerSec, uint64 newFullUtilizationInterest);
}

struct CurrentRateInfo { uint32 lastBlock; uint32 feeToProtocolRate; uint64 lastTimestamp; uint64 ratePerSec; uint64 fullUtilizationRate; }
struct VaultAccount { uint128 amount; uint128 shares; }

interface IFraxPair {
    function rateContract() external view returns (address);
    function currentRateInfo() external view returns (uint32, uint32, uint64, uint64, uint64);
    function totalBorrow() external view returns (uint128 amount, uint128 shares);
    function totalAsset() external view returns (uint128 amount, uint128 shares);
    function isInterestPaused() external view returns (bool);
    function previewAddInterest()
        external
        view
        returns (uint256, uint256, uint256, CurrentRateInfo memory, VaultAccount memory, VaultAccount memory);
}

interface IEulerIrm {
    function TARGET_UTILIZATION() external view returns (int256);
    function INITIAL_RATE_AT_TARGET() external view returns (int256);
    function MIN_RATE_AT_TARGET() external view returns (int256);
    function MAX_RATE_AT_TARGET() external view returns (int256);
    function CURVE_STEEPNESS() external view returns (int256);
    function ADJUSTMENT_SPEED() external view returns (int256);
    function computeInterestRate(address vault, uint256 cash, uint256 borrows) external returns (uint256);
    function computeInterestRateView(address vault, uint256 cash, uint256 borrows) external view returns (uint256);
    function computeRateAtTargetView(address vault, uint256 cash, uint256 borrows) external view returns (uint256);
}

/// @title DeployedRates
/// @notice LadderFraxlend and LadderEuler (the transcriptions in the ladder)
///         against the deployed contracts on Ethereum mainnet, on a fork:
///         the same inputs in, the same integers out. Network: run with
///         `make rates-verify` (forge test --fork-url, MAINNET_RPC); without
///         a fork every test is skipped.
///         FraxLend: VariableInterestRate V2 0x18500cB1f2fE7a40eBdA393383A0B8548a31F261
///         (fraxlend 2bed49d4, its configuration read from its own getters)
///         and the pair 0x78bB3aEC3d855431bd9289fD98dA13F9ebB7ef15 that uses it,
///         whose previewAddInterest charges the new rate over the interval.
///         Euler v2: IRMAdaptiveCurve 0xC9A0109D925251E0E5380d6fB4b105408d16C23D
///         (evk-periphery af436991, from the factory
///         0x3EC2d5af936bBB57DD19C292BAfb89da0E377F42), driven for fresh
///         vault addresses through its own computeInterestRate, and read
///         back through computeRateAtTargetView and computeInterestRateView.
contract DeployedRates is Test {
    IFraxRate constant FRAX_RATE = IFraxRate(0x18500cB1f2fE7a40eBdA393383A0B8548a31F261);
    IFraxPair constant FRAX_PAIR = IFraxPair(0x78bB3aEC3d855431bd9289fD98dA13F9ebB7ef15);
    IEulerIrm constant EULER_IRM = IEulerIrm(0xC9A0109D925251E0E5380d6fB4b105408d16C23D);

    modifier onFork() {
        if (address(FRAX_RATE).code.length == 0) {
            vm.skip(true);
            return;
        }
        _;
    }

    function _frax() internal view returns (FraxlendRate.Config memory c) {
        c = FraxlendRate.Config({
            MIN_TARGET_UTIL: FRAX_RATE.MIN_TARGET_UTIL(), MAX_TARGET_UTIL: FRAX_RATE.MAX_TARGET_UTIL(),
            VERTEX_UTILIZATION: FRAX_RATE.VERTEX_UTILIZATION(), MIN_FULL_UTIL_RATE: FRAX_RATE.MIN_FULL_UTIL_RATE(),
            MAX_FULL_UTIL_RATE: FRAX_RATE.MAX_FULL_UTIL_RATE(), ZERO_UTIL_RATE: FRAX_RATE.ZERO_UTIL_RATE(),
            RATE_HALF_LIFE: FRAX_RATE.RATE_HALF_LIFE(), VERTEX_RATE_PERCENT: FRAX_RATE.VERTEX_RATE_PERCENT()
        });
    }

    function _euler() internal view returns (EulerAdaptiveCurve.Config memory c) {
        c = EulerAdaptiveCurve.Config({
            TARGET_UTILIZATION: EULER_IRM.TARGET_UTILIZATION(), MIN_RATE_AT_TARGET: EULER_IRM.MIN_RATE_AT_TARGET(),
            MAX_RATE_AT_TARGET: EULER_IRM.MAX_RATE_AT_TARGET(), CURVE_STEEPNESS: EULER_IRM.CURVE_STEEPNESS(),
            ADJUSTMENT_SPEED: EULER_IRM.ADJUSTMENT_SPEED()
        });
    }

    // ---- FraxLend ---------------------------------------------------------------

    /// getNewRate on a grid of elapsed times, utilisations (below, in and
    /// above the band, its edges) and full-utilisation rates (the clamps,
    /// the pair's current one, values that clamp): (newRate, newFull) equal.
    function test_fraxlend_rate_matches_deployed() public onFork {
        FraxlendRate.Config memory c = _frax();
        (,,,, uint64 pairFull) = FRAX_PAIR.currentRateInfo();
        uint256[10] memory utils = [uint256(0), 20000, 37500, 74999, 75000, 80000, 85000, 85001, 92500, 100000];
        uint256[7] memory dts = [uint256(1), 12, 3600, 86400, 172800, 604800, 31536000];
        uint64[5] memory fulls = [uint64(c.MIN_FULL_UTIL_RATE), pairFull, 1e10, uint64(c.MAX_FULL_UTIL_RATE), 1268391679];
        uint256 cases;
        for (uint256 i; i < utils.length; i++) {
            for (uint256 j; j < dts.length; j++) {
                for (uint256 k; k < fulls.length; k++) {
                    (uint64 r0, uint64 f0) = FRAX_RATE.getNewRate(dts[j], utils[i], fulls[k]);
                    (uint64 r1, uint64 f1) = FraxlendRate.getNewRate(c, dts[j], utils[i], fulls[k]);
                    assertEq(f1, f0, "FraxlendRate.getFullUtilizationInterest != deployed");
                    assertEq(r1, r0, "FraxlendRate.getNewRate != deployed");
                    cases++;
                }
            }
        }
        console.log(string.concat("FRAX|getNewRate|", vm.toString(cases), " cases equal"));
    }

    /// The ladder adapter (LadderFraxlend.run, the scenario's path) against the
    /// deployed getNewRate, at the deployed half-life, wherever the deployed
    /// clamps do not bind (the adapter runs with them wide).
    function test_fraxlend_ladder_matches_deployed() public onFork {
        FraxlendRate.Config memory c = _frax();
        LadderFraxlend a = new LadderFraxlend();
        (,,,, uint64 pairFull) = FRAX_PAIR.currentRateInfo();
        int256[3] memory utils = [int256(0), 0.925e18, 1e18];
        uint32[6] memory ns = [uint32(1), 2, 5, 10, 20, 50];
        uint256 compared;
        for (uint256 i; i < utils.length; i++) {
            for (uint256 k; k < ns.length; k++) {
                int256[] memory p = new int256[](6);
                p[0] = int256(uint256(pairFull));
                p[2] = utils[i];
                p[3] = 86400e18;
                p[4] = int256(c.RATE_HALF_LIFE) * 1e18;
                (int256 raw,) = a.run(Scenario.ADAPTIVE_RATE, ns[k], p);
                (, uint64 f0) = FRAX_RATE.getNewRate(uint256(ns[k]) * 86400, uint256(utils[i]) / 1e13, pairFull);
                if (f0 == c.MIN_FULL_UTIL_RATE || f0 == c.MAX_FULL_UTIL_RATE) continue;
                assertEq(uint256(raw), f0, "LadderFraxlend != deployed getNewRate");
                compared++;
            }
        }
        assertGt(compared, 10);
        console.log(string.concat("FRAX|ladder|", vm.toString(compared), " cells equal"));
    }

    /// The pair: previewAddInterest after an idle interval returns the rate the
    /// rate contract gives for the pair's utilisation, and charges
    /// interestEarned = deltaTime * totalBorrow * newRate / 1e18, the new rate
    /// over the whole interval.
    function test_fraxlend_pair_charge_matches_deployed() public onFork {
        assertEq(FRAX_PAIR.rateContract(), address(FRAX_RATE));
        assertFalse(FRAX_PAIR.isInterestPaused());
        FraxlendRate.Config memory c = _frax();
        (,, uint64 last,, uint64 full) = FRAX_PAIR.currentRateInfo();
        (uint128 borrow,) = FRAX_PAIR.totalBorrow();
        (uint128 asset,) = FRAX_PAIR.totalAsset();
        uint256 util = asset == 0 ? 0 : (1e5 * uint256(borrow)) / asset;
        uint256 t0 = block.timestamp;
        uint256[4] memory waits = [uint256(1), 3600, 86400, 604800];
        for (uint256 i; i < waits.length; i++) {
            vm.warp(t0 + waits[i]);
            (uint256 earned,,, CurrentRateInfo memory info,,) = FRAX_PAIR.previewAddInterest();
            uint256 dt = block.timestamp - last;
            (uint64 r, uint64 f) = FraxlendRate.getNewRate(c, dt, util, full);
            assertEq(info.ratePerSec, r, "pair rate != FraxlendRate.getNewRate");
            assertEq(info.fullUtilizationRate, f, "pair full-utilisation rate != FraxlendRate");
            assertEq(earned, FraxlendRate.interestEarned(dt, borrow, r), "pair interestEarned != dt * borrow * newRate / 1e18");
        }
    }

    // ---- Euler v2 ---------------------------------------------------------------

    function _util(uint256 cash, uint256 borrows) internal pure returns (int256) {
        int256 totalAssets = int256(cash + borrows);
        if (totalAssets == 0) return 0;
        return int256(borrows) * 1e18 / totalAssets;
    }

    /// Fresh vaults driven through the deployed IRM: after each idle interval
    /// the rate at target (computeRateAtTargetView, RAY = WAD * 1e9) and the
    /// rate (computeInterestRateView) equal EulerAdaptiveCurve's, then the
    /// vault updates and the next interval starts from the stored state.
    struct Vault { address vault; int256 start; int256 lastUtil; }

    function test_euler_matches_deployed() public onFork {
        EulerAdaptiveCurve.Config memory c = _euler();
        uint256[2][6] memory states = [[uint256(0), 1000], [uint256(1000), 1], [uint256(75), 925], [uint256(50), 950], [uint256(300), 700], [uint256(1), 999]];
        uint256[5] memory waits = [uint256(12), 3600, 86400, 3 * 86400, 7 * 86400];
        uint256 compared;
        for (uint256 v; v < 3; v++) {
            Vault memory x = Vault(address(uint160(0xE01E2000 + v)), EULER_IRM.INITIAL_RATE_AT_TARGET(), 0);
            vm.prank(x.vault);
            EULER_IRM.computeInterestRate(x.vault, states[v][0] * 1e18, states[v][1] * 1e18);
            x.lastUtil = _util(states[v][0] * 1e18, states[v][1] * 1e18);
            for (uint256 w; w < waits.length; w++) {
                _eulerInterval(c, x, waits[w], states[(v + w + 1) % states.length]);
                compared++;
            }
        }
        console.log(string.concat("EULER|IRMAdaptiveCurve|", vm.toString(compared), " intervals equal"));
    }

    /// One idle interval of `wait` seconds, then the vault updates at (cash, borrows).
    function _eulerInterval(EulerAdaptiveCurve.Config memory c, Vault memory x, uint256 wait, uint256[2] memory state) internal {
        uint256 cash = state[0] * 1e18;
        uint256 borrows = state[1] * 1e18;
        vm.warp(block.timestamp + wait);
        int256 end = EulerAdaptiveCurve.endRateAtTarget(c, x.start, x.lastUtil, int256(wait));
        assertEq(EULER_IRM.computeRateAtTargetView(x.vault, cash, borrows), uint256(end) * 1e9, "rate at target != deployed");
        int256 util = _util(cash, borrows);
        int256 rate = EulerAdaptiveCurve.curve(c, end, EulerAdaptiveCurve.calcErr(c, util));
        assertEq(EULER_IRM.computeInterestRateView(x.vault, cash, borrows), uint256(rate) * 1e9, "rate != deployed");
        vm.prank(x.vault);
        EULER_IRM.computeInterestRate(x.vault, cash, borrows);
        x.start = end;
        x.lastUtil = util;
    }

    /// The ladder adapter (LadderEuler.run, the scenario's path) against the
    /// deployed IRM: a fresh vault at utilisation u from the initial rate at
    /// target, idle for N days, read back; wherever the deployed bounds do
    /// not bind (the adapter runs with them wide).
    function test_euler_ladder_matches_deployed() public onFork {
        EulerAdaptiveCurve.Config memory c = _euler();
        LadderEuler a = new LadderEuler();
        uint256[2][3] memory states = [[uint256(1000), 1], [uint256(75), 925], [uint256(0), 1000]];
        uint32[6] memory ns = [uint32(1), 2, 5, 10, 20, 50];
        uint256 compared;
        uint256 t0 = block.timestamp;
        for (uint256 i; i < states.length; i++) {
            for (uint256 k; k < ns.length; k++) {
                address vault = address(uint160(0xE01E3000 + i * 100 + k));
                uint256 cash = states[i][0] * 1e18;
                uint256 borrows = states[i][1] * 1e18;
                vm.warp(t0);
                vm.prank(vault);
                EULER_IRM.computeInterestRate(vault, cash, borrows);
                vm.warp(t0 + uint256(ns[k]) * 86400);
                int256 deployed = int256(EULER_IRM.computeRateAtTargetView(vault, cash, borrows) / 1e9);
                int256[] memory p = new int256[](6);
                p[0] = EULER_IRM.INITIAL_RATE_AT_TARGET();
                p[2] = _util(cash, borrows);
                p[3] = 86400e18;
                p[5] = c.ADJUSTMENT_SPEED;
                (int256 raw,) = a.run(Scenario.ADAPTIVE_RATE, ns[k], p);
                if (deployed == c.MIN_RATE_AT_TARGET || deployed == c.MAX_RATE_AT_TARGET) continue;
                assertEq(raw, deployed, "LadderEuler != deployed IRMAdaptiveCurve");
                compared++;
            }
        }
        assertGt(compared, 8);
        console.log(string.concat("EULER|ladder|", vm.toString(compared), " cells equal"));
    }
}

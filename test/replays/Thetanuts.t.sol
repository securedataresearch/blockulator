// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import {BL19Lib} from "../../contracts/src/bl19/BL19Lib.sol";

/// @notice The deployed arithmetic of the Thetanuts Index Vault V1 USDC PUT
///         (0xC2C3AE0a7b405058558C9b4a63b373486CB86Ac7). Its source is not
///         verified, so this is a model of its bytecode (solc 0.8.9), not a
///         transcription: `claim` and `mint` both compute a component's share with
///         the compiler's checked multiply (overflow check DIV at pc 12165, MUL at
///         pc 12186) and checked divide (DIV at pc 12220), floored.
///         scripts/replays/thetanuts.py fetch checks this model against all 190
///         executions in the attack's opcode trace and every storage write.
library ThetanutsDeployed {
    /// stored * amount / totalSupply (pcs 12158-12222)
    function share(uint256 stored, uint256 amount, uint256 supply) internal pure returns (uint256) {
        return stored * amount / supply;
    }
}

/// @title Thetanuts replay
/// @notice tx 0xbba9f138fe39503bfd1aa62932dbd6ab35d37d23d48e4b7bf2988a9d5dc39fec,
///         block 25323329, index 0. Replays the claim and the 37 mints from the
///         integers pinned in scripts/replays/thetanuts.json (no network), asserts
///         each equals the chain, then reruns the mints with the charge rounded
///         up, in BL127 and BL19, against exact rationals and under round-to-
///         nearest re-tuned. Prints
///             TNT|<form>|k=v;k=v;...
///         for scripts/replays/thetanuts.py, which scores them against exact rationals.
contract ThetanutsReplay is Test {
    string constant PINS = "scripts/replays/thetanuts.json";
    uint256 constant N = 5; // components
    uint256 constant MINTS = 37;

    // ---- pinned integers (provenance in thetanuts.json and docs/benchmarks/replay-thetanuts.md)
    uint256 constant SUPPLY_BEFORE = 153054600572; // slot 4 at block-1
    uint256 constant CLAIM = 153054600569; // claim(uint256) input; index Transfer(attacker -> 0)
    uint256 constant FLASH = 153054600569; // the pool's FlashLoan log
    uint256 constant PREMIUM = 137749140;
    uint256 constant SUPPLY_AFTER = 153192349712; // slot 4 at the block
    uint256 constant LAST_MINT = 15753396239; // the 37th mint; mints 1-36 are 2^1 .. 2^36

    function _storedBefore() internal pure returns (uint256[N] memory s) {
        // keccak(component . 10) + 1 at block-1 (= component.balanceOf(vault))
        s = [uint256(49716431048), 23955277334, 6378688542, 17186382410, 10028704388];
    }

    function _payout() internal pure returns (uint256[N] memory p) {
        // component Transfer(vault -> attacker) logs inside the claim
        p = [uint256(49716431047), 23955277333, 6378688541, 17186382409, 10028704387];
    }

    function _mintAmount(uint256 k) internal pure returns (uint256) {
        return k < 36 ? 2 << k : LAST_MINT;
    }

    function _s(string memory j, string memory key) internal pure returns (uint256) {
        return vm.parseUint(vm.parseJsonString(j, key));
    }

    function test_pins_match_json() public view {
        string memory j = vm.readFile(PINS);
        assertEq(_s(j, ".pre.totalSupply"), SUPPLY_BEFORE);
        assertEq(_s(j, ".claim.amount"), CLAIM);
        assertEq(_s(j, ".claim.supplyBefore"), SUPPLY_BEFORE);
        assertEq(_s(j, ".flashLoan.amount"), FLASH);
        assertEq(_s(j, ".flashLoan.premium"), PREMIUM);
        assertEq(_s(j, ".post.totalSupply"), SUPPLY_AFTER);
        uint256[N] memory s0 = _storedBefore();
        uint256[N] memory p = _payout();
        for (uint256 i; i < N; i++) {
            string memory ix = string.concat("[", vm.toString(i), "]");
            assertEq(_s(j, string.concat(".pre.stored", ix)), s0[i]);
            assertEq(_s(j, string.concat(".claim.payout", ix)), p[i]);
            assertEq(_s(j, string.concat(".post.stored", ix)), 1);
        }
        for (uint256 k; k < MINTS; k++) {
            string memory m = string.concat(".mints[", vm.toString(k), "]");
            assertEq(_s(j, string.concat(m, ".amount")), _mintAmount(k));
            for (uint256 i; i < N; i++) {
                assertEq(_s(j, string.concat(m, ".charge[", vm.toString(i), "]")), 0);
            }
        }
    }

    /// Bit-exact: the claim's five payouts, the 185 mint charges (all 0) and the
    /// post-state are what the chain did.
    function test_deployed_replay() public pure {
        uint256[N] memory st = _storedBefore();
        uint256[N] memory p = _payout();
        uint256 supply = SUPPLY_BEFORE;
        // claim: the share is taken against the supply before the burn
        for (uint256 i; i < N; i++) {
            uint256 out = ThetanutsDeployed.share(st[i], CLAIM, supply);
            assertEq(out, p[i]);
            // floored, so at or below the exact pro-rata share: the claim is in the vault's favour
            assertLe(out * supply, st[i] * CLAIM);
            st[i] -= out;
            assertEq(st[i], 1);
        }
        supply -= CLAIM;
        assertEq(supply, 3);
        // 37 mints, each below the supply, so 1 * amount / supply floors to 0
        uint256 minted;
        for (uint256 k; k < MINTS; k++) {
            uint256 a = _mintAmount(k);
            assertLt(a, supply);
            for (uint256 i; i < N; i++) {
                uint256 charge = ThetanutsDeployed.share(st[i], a, supply);
                assertEq(charge, 0);
                st[i] += charge;
            }
            supply += a;
            minted += a;
        }
        assertEq(supply, SUPPLY_AFTER);
        assertEq(minted, FLASH + PREMIUM); // exactly the loan and its fee
        for (uint256 i; i < N; i++) {
            assertEq(st[i], 1);
        }
    }

    /// Exact rationals on the chain path: every charge is strictly between 0 and 1
    /// raw unit, so a whole-unit transfer has to round it one way or the other.
    function test_exact_charge_is_a_fraction_of_a_unit() public pure {
        uint256 supply = SUPPLY_BEFORE - CLAIM;
        for (uint256 k; k < MINTS; k++) {
            uint256 a = _mintAmount(k);
            assertGt(1 * a, 0);
            assertLt(1 * a, supply); // 0 < a/supply < 1
            supply += a;
        }
    }

    /// Round up: the ratio stored/supply never falls below the 1/3 the claim left,
    /// so minting M tokens costs at least ceil(M/3) of every component, more than
    /// the claim took of any of them.
    function test_round_up_costs_more_than_the_claim_took() public pure {
        (uint256 paid, uint256 minted) = _ceilPath(false);
        uint256 floorUp = (minted + 2) / 3;
        assertEq(minted, FLASH + PREMIUM);
        assertGe(paid, floorUp);
        uint256[N] memory p = _payout();
        for (uint256 i; i < N; i++) {
            assertGt(floorUp, p[i]);
            assertGt(paid, p[i]);
        }
    }

    /// Nearest, re-tuned: mint the largest amount whose charge rounds to 0 to nearest
    /// (2 * stored * a < supply) until the loan is repaid. Every mint is free.
    function test_nearest_retuned_is_still_free() public pure {
        _nearestPath(); // the attacker's own amounts do pay, to nearest
        (uint256 count, uint256 paid) = _nearestRetuned();
        assertEq(paid, 0);
        assertGt(count, MINTS);
    }

    function _ceilPath(bool log) internal pure returns (uint256 paid, uint256 minted) {
        uint256 stored = 1; // every component: 1 raw unit after the claim
        uint256 supply = SUPPLY_BEFORE - CLAIM;
        for (uint256 k; k < MINTS; k++) {
            uint256 a = _mintAmount(k);
            uint256 charge = (stored * a + supply - 1) / supply;
            if (log) {
                _line("ceil", string.concat("k=", vm.toString(k), ";amount=", vm.toString(a), ";supplyBefore=", vm.toString(supply),
                    ";storedBefore=", vm.toString(stored), ";charge=", vm.toString(charge)));
            }
            stored += charge;
            supply += a;
            minted += a;
            assertGe(3 * stored, supply); // the invariant: stored / supply >= 1/3
        }
        paid = stored - 1;
    }

    /// The same path with the charge computed in BL127, then ceiled to a raw unit.
    function _bl127CeilPath() internal pure returns (uint256 paid) {
        uint256 stored = 1;
        uint256 supply = SUPPLY_BEFORE - CLAIM;
        for (uint256 k; k < MINTS; k++) {
            uint256 a = _mintAmount(k);
            int256 c = BL127Lib.div(BL127Lib.mul(_q(stored), _q(a)), _q(supply));
            stored += uint256(BL127Lib.ceil(c) >> 128);
            supply += a;
        }
        paid = stored - 1;
    }

    /// The same path with the charge computed in BL19, then ceiled to a raw unit.
    function _bl19CeilPath() internal pure returns (uint256 paid) {
        uint256 stored = 1;
        uint256 supply = SUPPLY_BEFORE - CLAIM;
        for (uint256 k; k < MINTS; k++) {
            uint256 a = _mintAmount(k);
            int256 c = BL19Lib.div(BL19Lib.mul(BL19Lib.fromUint(stored), BL19Lib.fromUint(a)), BL19Lib.fromUint(supply));
            stored += uint256(BL127Lib.ceil(BL19Lib.toBL127(c)) >> 128);
            supply += a;
        }
        paid = stored - 1;
    }

    /// The attacker's own 37 amounts with the charge rounded to nearest (halves up).
    function _nearestPath() internal pure returns (uint256 paid) {
        uint256 stored = 1;
        uint256 supply = SUPPLY_BEFORE - CLAIM;
        for (uint256 k; k < MINTS; k++) {
            uint256 a = _mintAmount(k);
            stored += (2 * stored * a + supply) / (2 * supply);
            supply += a;
        }
        paid = stored - 1;
        uint256[N] memory p = _payout();
        for (uint256 i; i < N; i++) {
            assertGt(paid, p[i]);
        }
    }

    function _nearestRetuned() internal pure returns (uint256 count, uint256 paid) {
        uint256 stored = 1;
        uint256 supply = SUPPLY_BEFORE - CLAIM;
        uint256 held;
        uint256 target = FLASH + PREMIUM;
        while (held < target) {
            uint256 a = (supply - 1) / (2 * stored);
            if (a > target - held) a = target - held;
            uint256 charge = (2 * stored * a + supply) / (2 * supply); // nearest, halves up
            assertEq(charge, 0);
            paid += charge;
            held += a;
            supply += a;
            count++;
        }
    }

    function test_fp_ceil_paths_match_integer_round_up() public pure {
        (uint256 paid,) = _ceilPath(false);
        assertEq(_bl127CeilPath(), paid);
        assertEq(_bl19CeilPath(), paid);
    }

    function test_report() public pure {
        uint256[N] memory st = _storedBefore();
        for (uint256 i; i < N; i++) {
            _line("claim", string.concat("i=", vm.toString(i), ";payout=", vm.toString(ThetanutsDeployed.share(st[i], CLAIM, SUPPLY_BEFORE))));
        }
        uint256 supply = SUPPLY_BEFORE - CLAIM;
        for (uint256 k; k < MINTS; k++) {
            uint256 a = _mintAmount(k);
            // as deployed (stored is 1 for every component on the chain path)
            _line("deployed", string.concat("k=", vm.toString(k), ";amount=", vm.toString(a), ";supply=", vm.toString(supply),
                ";charge=", vm.toString(ThetanutsDeployed.share(1, a, supply))));
            // BL127: the charge to 2^-128, then the three ways to make it a raw unit
            int256 c = BL127Lib.div(BL127Lib.mul(_q(1), _q(a)), _q(supply));
            int256 fl = BL127Lib.floor(c) >> 128;
            int256 ce = BL127Lib.ceil(c) >> 128;
            assertEq(fl, 0);
            assertEq(ce, 1);
            _line("bl127", string.concat("k=", vm.toString(k), ";raw=", vm.toString(c), ";floor=", vm.toString(fl), ";ceil=",
                vm.toString(ce), ";round=", vm.toString(BL127Lib.round(c) >> 128)));
            // BL19: same
            int256 d = BL19Lib.div(BL19Lib.mul(BL19Lib.fromUint(1), BL19Lib.fromUint(a)), BL19Lib.fromUint(supply));
            int256 dfl = BL127Lib.floor(BL19Lib.toBL127(d)) >> 128;
            int256 dce = BL127Lib.ceil(BL19Lib.toBL127(d)) >> 128;
            assertEq(dfl, 0);
            assertEq(dce, 1);
            _line("bl19", string.concat("k=", vm.toString(k), ";raw=", vm.toString(d), ";floor=", vm.toString(dfl), ";ceil=", vm.toString(dce)));
            supply += a;
        }
        (uint256 paid, uint256 minted) = _ceilPath(true);
        _line("ceilSummary", string.concat("paidPerComponent=", vm.toString(paid), ";minPerComponent=", vm.toString((minted + 2) / 3),
            ";minted=", vm.toString(minted)));
        _line("bl127ceil", string.concat("paidPerComponent=", vm.toString(_bl127CeilPath())));
        _line("bl19ceil", string.concat("paidPerComponent=", vm.toString(_bl19CeilPath())));
        _line("nearestPath", string.concat("paidPerComponent=", vm.toString(_nearestPath())));
        (uint256 count, uint256 npaid) = _nearestRetuned();
        _line("nearestRetuned", string.concat("mints=", vm.toString(count), ";paidPerComponent=", vm.toString(npaid), ";minted=",
            vm.toString(FLASH + PREMIUM)));
    }

    /// BL127 holds integers below 2^127 exactly; everything here is below 2^72.
    function _q(uint256 x) internal pure returns (int256) {
        require(x < 1 << 127, "BL127 range");
        return int256(x) << 128;
    }

    function _line(string memory form, string memory kv) internal pure {
        console.log(string.concat("TNT|", form, "|", kv));
    }
}

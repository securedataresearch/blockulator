// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Test} from "forge-std/Test.sol";
import {BlockulatorWad} from "../../contracts/src/wad/BlockulatorWad.sol";

/// BlockulatorWad's rows of the random-input sweep, as Sweep.t.sol runs the
/// BL127 and BL19 ops: every direction of every function on the seeded
/// inputs scripts/sweep/wad.py writes to cache/sweep/wad_<function>.json,
/// one result word (or "R" + revert data) and its gas per line to
/// wad_<function>.out. Its own contract, so Sweep.t.sol's dispatch (and the
/// gas it measures) is unchanged. Skips when the inputs are absent.
contract SweepWad is Test {
    string constant DIR = "cache/sweep/";

    /// The result and the gas of the one library call, the window around a
    /// plain assignment ("noop") the baseline, as Sweep.t.sol's f.
    function f(bytes32 op, int256 a, int256 b, int256 c) external view returns (int256 r, uint256 g) {
        uint256 g0;
        if (op == "noop") { g0 = gasleft(); r = a; g = gasleft(); }
        if (op == "wad_mulWad") { g0 = gasleft(); r = int256(BlockulatorWad.mulWad(uint256(a), uint256(b))); g = gasleft(); }
        if (op == "wad_mulWadUp") { g0 = gasleft(); r = int256(BlockulatorWad.mulWadUp(uint256(a), uint256(b))); g = gasleft(); }
        if (op == "wad_divWad") { g0 = gasleft(); r = int256(BlockulatorWad.divWad(uint256(a), uint256(b))); g = gasleft(); }
        if (op == "wad_divWadUp") { g0 = gasleft(); r = int256(BlockulatorWad.divWadUp(uint256(a), uint256(b))); g = gasleft(); }
        if (op == "wad_sMulWad") { g0 = gasleft(); r = BlockulatorWad.sMulWad(a, b); g = gasleft(); }
        if (op == "wad_sMulWadDown") { g0 = gasleft(); r = BlockulatorWad.sMulWadDown(a, b); g = gasleft(); }
        if (op == "wad_sMulWadUp") { g0 = gasleft(); r = BlockulatorWad.sMulWadUp(a, b); g = gasleft(); }
        if (op == "wad_sDivWad") { g0 = gasleft(); r = BlockulatorWad.sDivWad(a, b); g = gasleft(); }
        if (op == "wad_sDivWadDown") { g0 = gasleft(); r = BlockulatorWad.sDivWadDown(a, b); g = gasleft(); }
        if (op == "wad_sDivWadUp") { g0 = gasleft(); r = BlockulatorWad.sDivWadUp(a, b); g = gasleft(); }
        if (op == "wad_sqrtWad") { g0 = gasleft(); r = int256(BlockulatorWad.sqrtWad(uint256(a))); g = gasleft(); }
        if (op == "wad_sqrtWadUp") { g0 = gasleft(); r = int256(BlockulatorWad.sqrtWadUp(uint256(a))); g = gasleft(); }
        if (op == "wad_cbrtWad") { g0 = gasleft(); r = int256(BlockulatorWad.cbrtWad(uint256(a))); g = gasleft(); }
        if (op == "wad_cbrtWadUp") { g0 = gasleft(); r = int256(BlockulatorWad.cbrtWadUp(uint256(a))); g = gasleft(); }
        if (op == "wad_expWad") { g0 = gasleft(); r = BlockulatorWad.expWad(a); g = gasleft(); }
        if (op == "wad_expWadUp") { g0 = gasleft(); r = BlockulatorWad.expWadUp(a); g = gasleft(); }
        if (op == "wad_lnWad") { g0 = gasleft(); r = BlockulatorWad.lnWad(a); g = gasleft(); }
        if (op == "wad_lnWadUp") { g0 = gasleft(); r = BlockulatorWad.lnWadUp(a); g = gasleft(); }
        if (op == "wad_log2Wad") { g0 = gasleft(); r = BlockulatorWad.log2Wad(a); g = gasleft(); }
        if (op == "wad_log2WadUp") { g0 = gasleft(); r = BlockulatorWad.log2WadUp(a); g = gasleft(); }
        if (op == "wad_log10Wad") { g0 = gasleft(); r = BlockulatorWad.log10Wad(a); g = gasleft(); }
        if (op == "wad_log10WadUp") { g0 = gasleft(); r = BlockulatorWad.log10WadUp(a); g = gasleft(); }
        if (op == "wad_powWad") { g0 = gasleft(); r = BlockulatorWad.powWad(a, b); g = gasleft(); }
        if (op == "wad_powWadUp") { g0 = gasleft(); r = BlockulatorWad.powWadUp(a, b); g = gasleft(); }
        if (op == "wad_lambertW0Wad") { g0 = gasleft(); r = BlockulatorWad.lambertW0Wad(a); g = gasleft(); }
        if (op == "wad_lambertW0WadDown") { g0 = gasleft(); r = BlockulatorWad.lambertW0WadDown(a); g = gasleft(); }
        if (op == "wad_lambertW0WadUp") { g0 = gasleft(); r = BlockulatorWad.lambertW0WadUp(a); g = gasleft(); }
        require(g0 != 0, "op");
        g = g0 - g;
    }

    /// One function per external call, so its memory is released before the next.
    function runOne(string memory op, bool two) external {
        string memory path = string.concat(DIR, op, ".json");
        if (!vm.exists(path)) return;
        string memory j = vm.readFile(path);
        bytes32[] memory a = vm.parseJsonBytes32Array(j, ".a");
        bytes32[] memory b = two ? vm.parseJsonBytes32Array(j, ".b") : new bytes32[](a.length);
        string memory outp = string.concat(DIR, op, ".out");
        if (vm.exists(outp)) vm.removeFile(outp);
        bytes32 k = bytes32(bytes(op));
        (, uint256 base) = this.f("noop", 0, 0, 0);
        for (uint256 i; i < a.length; i++) {
            try this.f(k, int256(uint256(a[i])), int256(uint256(b[i])), 0) returns (int256 r, uint256 g) {
                vm.writeLine(outp, string.concat(vm.toString(bytes32(uint256(r))), " ", vm.toString(g > base ? g - base : 0)));
            } catch (bytes memory e) {
                vm.writeLine(outp, string.concat("R", vm.toString(e), " 0"));
            }
        }
    }

    // One test per function: forge runs test functions in parallel, and each
    // writes its own output file.
    function test_wad_mulWad() public { this.runOne("wad_mulWad", true); }
    function test_wad_mulWadUp() public { this.runOne("wad_mulWadUp", true); }
    function test_wad_divWad() public { this.runOne("wad_divWad", true); }
    function test_wad_divWadUp() public { this.runOne("wad_divWadUp", true); }
    function test_wad_sMulWad() public { this.runOne("wad_sMulWad", true); }
    function test_wad_sMulWadDown() public { this.runOne("wad_sMulWadDown", true); }
    function test_wad_sMulWadUp() public { this.runOne("wad_sMulWadUp", true); }
    function test_wad_sDivWad() public { this.runOne("wad_sDivWad", true); }
    function test_wad_sDivWadDown() public { this.runOne("wad_sDivWadDown", true); }
    function test_wad_sDivWadUp() public { this.runOne("wad_sDivWadUp", true); }
    function test_wad_sqrtWad() public { this.runOne("wad_sqrtWad", false); }
    function test_wad_sqrtWadUp() public { this.runOne("wad_sqrtWadUp", false); }
    function test_wad_cbrtWad() public { this.runOne("wad_cbrtWad", false); }
    function test_wad_cbrtWadUp() public { this.runOne("wad_cbrtWadUp", false); }
    function test_wad_expWad() public { this.runOne("wad_expWad", false); }
    function test_wad_expWadUp() public { this.runOne("wad_expWadUp", false); }
    function test_wad_lnWad() public { this.runOne("wad_lnWad", false); }
    function test_wad_lnWadUp() public { this.runOne("wad_lnWadUp", false); }
    function test_wad_log2Wad() public { this.runOne("wad_log2Wad", false); }
    function test_wad_log2WadUp() public { this.runOne("wad_log2WadUp", false); }
    function test_wad_log10Wad() public { this.runOne("wad_log10Wad", false); }
    function test_wad_log10WadUp() public { this.runOne("wad_log10WadUp", false); }
    function test_wad_powWad() public { this.runOne("wad_powWad", true); }
    function test_wad_powWadUp() public { this.runOne("wad_powWadUp", true); }
    function test_wad_lambertW0Wad() public { this.runOne("wad_lambertW0Wad", false); }
    function test_wad_lambertW0WadDown() public { this.runOne("wad_lambertW0WadDown", false); }
    function test_wad_lambertW0WadUp() public { this.runOne("wad_lambertW0WadUp", false); }
}

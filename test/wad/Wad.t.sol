// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Test} from "forge-std/Test.sol";
import {BlockulatorWad as W} from "../../contracts/src/wad/BlockulatorWad.sol";
import {FixedPointMathLib as S} from "../../lib/solady/src/utils/FixedPointMathLib.sol";

/// @title Wad
/// @notice BlockulatorWad: known values to the last wei (the exact value from
///         mpmath at 300 digits, rounded in each direction), Solady's revert
///         selectors at the ends of each domain, the aliases, and fuzzing: the
///         algebraic functions against Solady's exact fullMulDiv, sqrt and
///         cbrt, the transcendental ones for Up - Down in {0, 1} and
///         monotonicity. make sweep holds every function to 0 wrong wei on
///         its seeded inputs and through its second stage alone.
contract Wad is Test {
    uint256 constant WAD = 1e18;

    function test_exp() public pure {
        assertEq(W.expWad(0), 1e18);
        assertEq(W.expWadUp(0), 1e18);
        assertEq(W.expWad(1000000000000000000), 2718281828459045235);
        assertEq(W.expWadUp(1000000000000000000), 2718281828459045236);
        assertEq(W.expWad(-1000000000000000000), 367879441171442321);
        assertEq(W.expWadUp(-1000000000000000000), 367879441171442322);
        assertEq(W.expWad(3000000000000000000), 20085536923187667740, "Solady: ...741");
        assertEq(W.expWadUp(3000000000000000000), 20085536923187667741);
        assertEq(W.expWad(10000000000000000000), 22026465794806716516957);
        assertEq(W.expWadUp(10000000000000000000), 22026465794806716516958);
        assertEq(W.expWad(50000000000000000000), 5184705528587072464087453322933485384827);
        assertEq(W.expWadUp(50000000000000000000), 5184705528587072464087453322933485384828);
        assertEq(W.expWad(100000000000000000000), 26881171418161354484126255515800135873611118773741922415191608);
        assertEq(W.expWadUp(100000000000000000000), 26881171418161354484126255515800135873611118773741922415191609);
        assertEq(W.expWad(-41446531673892822312), 1);
        assertEq(W.expWadUp(-41446531673892822312), 2);
        assertEq(W.expWad(-41446531673892822313), 0);
        assertEq(W.expWadUp(-41446531673892822313), 1);
        assertEq(W.expWadUp(type(int256).min), 1);
        assertEq(W.expWad(135305999368893231589), 57896044618658097707712807547600434460894277218426047864535176624857265142719);
        assertEq(W.expWadUp(135305999368893231589), 57896044618658097707712807547600434460894277218426047864535176624857265142720);
        assertEq(W.expWad(1), 1000000000000000001);
        assertEq(W.expWadUp(1), 1000000000000000002);
        assertEq(W.expWad(-1), 999999999999999999);
        assertEq(W.expWadUp(-1), 1000000000000000000);
    }

    function test_ln() public pure {
        assertEq(W.lnWad(1e18), 0);
        assertEq(W.lnWadUp(1e18), 0);
        assertEq(W.lnWad(2718281828459045235), 999999999999999999);
        assertEq(W.lnWadUp(2718281828459045235), 1000000000000000000);
        assertEq(W.lnWad(11723640096265400935), 2461607324344817917, "Solady: ...918");
        assertEq(W.lnWadUp(11723640096265400935), 2461607324344817918);
        assertEq(W.lnWad(1), -41446531673892822313);
        assertEq(W.lnWadUp(1), -41446531673892822312);
        assertEq(W.lnWad(42), -37708862055609454007);
        assertEq(W.lnWadUp(42), -37708862055609454006);
        assertEq(W.lnWad(1000000000), -20723265836946411157);
        assertEq(W.lnWadUp(1000000000), -20723265836946411156);
        assertEq(W.lnWad(type(int256).max), 135305999368893231589);
        assertEq(W.lnWadUp(type(int256).max), 135305999368893231590);
        assertEq(W.lnWad(340282366920938463463374607431768211456), 47276307437780177293);
        assertEq(W.lnWadUp(340282366920938463463374607431768211456), 47276307437780177294);
        assertEq(W.lnWad(500000000000000000), -693147180559945310);
        assertEq(W.lnWadUp(500000000000000000), -693147180559945309);
    }

    function test_logs() public pure {
        assertEq(W.log2Wad(3000000000000000000), 1584962500721156181);
        assertEq(W.log2WadUp(3000000000000000000), 1584962500721156182);
        assertEq(W.log2Wad(333333333333333333), -1584962500721156183);
        assertEq(W.log2WadUp(333333333333333333), -1584962500721156182);
        assertEq(W.log2Wad(type(int256).max), 195205294292027477738);
        assertEq(W.log2WadUp(type(int256).max), 195205294292027477739);
        assertEq(W.log2Wad(1), -59794705707972522262);
        assertEq(W.log2WadUp(1), -59794705707972522261);
        // exact at 10^18 2^k
        assertEq(W.log2Wad(8e18), 3e18);
        assertEq(W.log2WadUp(8e18), 3e18);
        assertEq(W.log2Wad(1e18 >> 18), -18e18);
        assertEq(W.log2Wad(1e18 << 190), 190e18);
        assertEq(W.log10Wad(3000000000000000000), 477121254719662437);
        assertEq(W.log10WadUp(3000000000000000000), 477121254719662438);
        assertEq(W.log10Wad(200000000000000000), -698970004336018805);
        assertEq(W.log10WadUp(200000000000000000), -698970004336018804);
        assertEq(W.log10Wad(type(int256).max), 58762648894315204779);
        assertEq(W.log10WadUp(type(int256).max), 58762648894315204780);
        // exact at 10^(18 + k)
        assertEq(W.log10Wad(1), -18e18);
        assertEq(W.log10WadUp(1), -18e18);
        assertEq(W.log10Wad(1e19), 1e18);
        assertEq(W.log10WadUp(1e19), 1e18);
        assertEq(W.log10Wad(1e76), 58e18);
    }

    function test_pow() public pure {
        assertEq(W.powWad(2000000000000000000, 3000000000000000000), 8000000000000000000);
        assertEq(W.powWadUp(2000000000000000000, 3000000000000000000), 8000000000000000000);
        assertEq(W.powWad(1500000000000000000, 2500000000000000000), 2755675960631075360);
        assertEq(W.powWadUp(1500000000000000000, 2500000000000000000), 2755675960631075361);
        assertEq(W.powWad(100000000000000000, 1500000000000000000), 31622776601683793);
        assertEq(W.powWadUp(100000000000000000, 1500000000000000000), 31622776601683794);
        assertEq(W.powWad(3000000000000000000, -1500000000000000000), 192450089729875254);
        assertEq(W.powWadUp(3000000000000000000, -1500000000000000000), 192450089729875255);
        assertEq(W.powWad(4000000000000000000, 500000000000000000), 2000000000000000000);
        assertEq(W.powWadUp(4000000000000000000, 500000000000000000), 2000000000000000000);
        assertEq(W.powWad(1000000000000000001, 1e38), 26881171418161353140067684607732446164801662957472777864944054);
        assertEq(W.powWadUp(1000000000000000001, 1e38), 26881171418161353140067684607732446164801662957472777864944055);
        // exact powers, the shortcuts and 0^y
        assertEq(W.powWad(1.1e18, 2e18), 1.21e18);
        assertEq(W.powWad(0.5e18, 2e18), 0.25e18);
        assertEq(W.powWad(2e18, -2e18), 0.25e18);
        assertEq(W.powWad(9e18, -0.5e18), 333333333333333333);
        assertEq(W.powWadUp(9e18, -0.5e18), 333333333333333334);
        assertEq(W.powWad(3e18, -1e18), 333333333333333333);
        assertEq(W.powWadUp(3e18, -1e18), 333333333333333334);
        assertEq(W.powWad(0, 0), 1e18);
        assertEq(W.powWad(0, 1e18), 0);
        assertEq(W.powWad(7e18, 0), 1e18);
        assertEq(W.powWad(1e18, type(int256).max), 1e18);
        assertEq(W.powWad(0.5e18, 1e30), 0);
        assertEq(W.powWadUp(0.5e18, 1e30), 1);
    }

    function test_lambertW0() public pure {
        assertEq(W.lambertW0Wad(0), 0);
        assertEq(W.lambertW0Wad(1), 0, "Solady: 1");
        assertEq(W.lambertW0WadUp(1), 1);
        assertEq(W.lambertW0Wad(2), 1, "Solady: 2");
        assertEq(W.lambertW0WadUp(2), 2);
        assertEq(W.lambertW0Wad(3), 2);
        assertEq(W.lambertW0WadUp(3), 3);
        assertEq(W.lambertW0Wad(1000000000000000000), 567143290409783872);
        assertEq(W.lambertW0WadUp(1000000000000000000), 567143290409783873);
        // toward zero below zero, as Solady's sdiv: Down is one further
        assertEq(W.lambertW0Wad(-3678794411715), -3678807945318);
        assertEq(W.lambertW0WadUp(-3678794411715), -3678807945318);
        assertEq(W.lambertW0WadDown(-3678794411715), -3678807945319);
        assertEq(W.lambertW0Wad(-367879441171442321), -999999998200665989, "Solady: -999999999741585709");
        assertEq(W.lambertW0WadDown(-367879441171442321), -999999998200665990);
        assertEq(W.lambertW0Wad(type(int256).max), 130435123404408416612);
        assertEq(W.lambertW0WadUp(type(int256).max), 130435123404408416613);
        assertEq(W.lambertW0Wad(340282366920938463463374607431768211456), 43503466806167642613);
        assertEq(W.lambertW0WadUp(340282366920938463463374607431768211456), 43503466806167642614);
    }

    function test_algebra() public pure {
        assertEq(W.mulWad(3e18, 0.7e18), 2.1e18);
        assertEq(W.mulWad(1, 1), 0);
        assertEq(W.mulWadUp(1, 1), 1);
        assertEq(W.divWad(1e18, 3e18), 333333333333333333);
        assertEq(W.divWadUp(1e18, 3e18), 333333333333333334);
        assertEq(W.sMulWad(-1, 1), 0, "toward zero");
        assertEq(W.sMulWadDown(-1, 1), -1);
        assertEq(W.sMulWadUp(-1, 1), 0);
        assertEq(W.sMulWadUp(1, 1), 1);
        assertEq(W.sDivWad(-1, 3e18), 0);
        assertEq(W.sDivWadDown(-1, 3e18), -1);
        assertEq(W.sDivWadUp(1, 3e18), 1);
        assertEq(W.sqrtWad(2e18), 1414213562373095048);
        assertEq(W.sqrtWadUp(2e18), 1414213562373095049);
        assertEq(W.sqrtWad(4e18), 2e18);
        assertEq(W.sqrtWadUp(4e18), 2e18);
        assertEq(W.sqrtWad(type(uint256).max), 340282366920938463463374607431768211455999999999);
        assertEq(W.cbrtWad(2e18), 1259921049894873164);
        assertEq(W.cbrtWadUp(2e18), 1259921049894873165);
        assertEq(W.cbrtWad(8e18), 2e18);
        assertEq(W.cbrtWadUp(8e18), 2e18);
        assertEq(W.cbrtWad(0), 0);
        // past 2^256 in the product, where Solady reverts
        assertEq(W.mulWad(type(uint256).max, 1e17), type(uint256).max / 10);
        assertEq(W.divWad(type(uint256).max / 1e9, 1e18), type(uint256).max / 1e9);
        assertEq(W.sMulWad(type(int256).min, 1e18), type(int256).min);
        assertEq(W.sDivWad(type(int256).min / 1e9, 1e18), type(int256).min / 1e9);
    }

    // ---- reverts: Solady's selectors at Solady's ends ----------------------

    function expW(int256 x) external pure returns (int256) { return W.expWad(x); }
    function expUpW(int256 x) external pure returns (int256) { return W.expWadUp(x); }
    function lnW(int256 x) external pure returns (int256) { return W.lnWad(x); }
    function log2W(int256 x) external pure returns (int256) { return W.log2Wad(x); }
    function powW(int256 x, int256 y) external pure returns (int256) { return W.powWad(x, y); }
    function w0W(int256 x) external pure returns (int256) { return W.lambertW0Wad(x); }
    function mulW(uint256 x, uint256 y) external pure returns (uint256) { return W.mulWad(x, y); }
    function mulUpW(uint256 x, uint256 y) external pure returns (uint256) { return W.mulWadUp(x, y); }
    function divW(uint256 x, uint256 y) external pure returns (uint256) { return W.divWad(x, y); }
    function smulW(int256 x, int256 y) external pure returns (int256) { return W.sMulWad(x, y); }
    function sdivW(int256 x, int256 y) external pure returns (int256) { return W.sDivWad(x, y); }

    function test_reverts() public {
        vm.expectRevert(S.ExpOverflow.selector);
        this.expW(135305999368893231590);
        vm.expectRevert(S.ExpOverflow.selector);
        this.expUpW(type(int256).max);
        vm.expectRevert(S.LnWadUndefined.selector);
        this.lnW(0);
        vm.expectRevert(S.LnWadUndefined.selector);
        this.lnW(-1);
        vm.expectRevert(S.LnWadUndefined.selector);
        this.log2W(0);
        vm.expectRevert(S.LnWadUndefined.selector);
        this.powW(-1, 1e18);
        vm.expectRevert(S.LnWadUndefined.selector);
        this.powW(0, -1);
        vm.expectRevert(S.ExpOverflow.selector);
        this.powW(2e18, 256e18);
        vm.expectRevert(S.ExpOverflow.selector);
        this.powW(type(int256).max, 2e18);
        vm.expectRevert(S.OutOfDomain.selector);
        this.w0W(-367879441171442322);
        vm.expectRevert(S.MulWadFailed.selector);
        this.mulW(type(uint256).max, 2e18);
        vm.expectRevert(S.MulWadFailed.selector);
        this.mulUpW(type(uint256).max, 1e18 + 1);
        vm.expectRevert(S.DivWadFailed.selector);
        this.divW(1, 0);
        vm.expectRevert(S.DivWadFailed.selector);
        this.divW(type(uint256).max, 1e17);
        vm.expectRevert(S.SMulWadFailed.selector);
        this.smulW(type(int256).min, 2e18);
        vm.expectRevert(S.SDivWadFailed.selector);
        this.sdivW(1, 0);
        vm.expectRevert(S.SDivWadFailed.selector);
        this.sdivW(type(int256).min, 1e17);
    }

    // ---- fuzzing -------------------------------------------------------

    /// mul and div against Solady's exact 512-bit fullMulDiv, where it returns.
    function testFuzz_mulDiv(uint256 x, uint256 y) public {
        try this.fullMulDiv(x, y, WAD) returns (uint256 z) {
            assertEq(W.mulWad(x, y), z);
            assertEq(W.mulWadDown(x, y), z);
        } catch {}
        try this.fullMulDivUp(x, y, WAD) returns (uint256 z) {
            assertEq(W.mulWadUp(x, y), z);
        } catch {}
        if (y != 0) {
            try this.fullMulDiv(x, WAD, y) returns (uint256 z) {
                assertEq(W.divWad(x, y), z);
                assertEq(W.divWadDown(x, y), z);
            } catch {}
            try this.fullMulDivUp(x, WAD, y) returns (uint256 z) {
                assertEq(W.divWadUp(x, y), z);
            } catch {}
        }
    }

    function fullMulDiv(uint256 x, uint256 y, uint256 d) external pure returns (uint256) { return S.fullMulDiv(x, y, d); }
    function fullMulDivUp(uint256 x, uint256 y, uint256 d) external pure returns (uint256) { return S.fullMulDivUp(x, y, d); }

    /// The signed ones from the magnitudes' exact quotient and the sign.
    function testFuzz_signed(int256 x, int256 y) public {
        uint256 a = x < 0 ? uint256(-(x + 1)) + 1 : uint256(x);
        uint256 b = y < 0 ? uint256(-(y + 1)) + 1 : uint256(y);
        bool ng = (x < 0) != (y < 0);
        try this.fullMulDiv(a, b, WAD) returns (uint256 q) {
            bool inexact = mulmod(a, b, WAD) != 0;
            _signed(ng, q, inexact, W.sMulWad, W.sMulWadDown, W.sMulWadUp, x, y);
        } catch {}
        if (y != 0) {
            try this.fullMulDiv(a, WAD, b) returns (uint256 q) {
                bool inexact = mulmod(a, WAD, b) != 0;
                _signed(ng, q, inexact, W.sDivWad, W.sDivWadDown, W.sDivWadUp, x, y);
            } catch {}
        }
    }

    function _signed(bool ng, uint256 q, bool inexact,
                     function(int256, int256) pure returns (int256) zero,
                     function(int256, int256) pure returns (int256) down,
                     function(int256, int256) pure returns (int256) up,
                     int256 x, int256 y) internal pure {
        int256 t;
        if (ng) {
            if (q > uint256(type(int256).max) + 1) return;
            t = q == 0 ? int256(0) : -int256(q - 1) - 1;
        } else {
            if (q > uint256(type(int256).max)) return;
            t = int256(q);
        }
        assertEq(zero(x, y), t, "toward zero");
        if (inexact && !ng && t == type(int256).max) return;
        if (inexact && ng && t == type(int256).min) return;
        assertEq(down(x, y), ng && inexact ? t - 1 : t, "down");
        assertEq(up(x, y), !ng && inexact ? t + 1 : t, "up");
    }

    /// sqrt and cbrt against Solady's exact roots (cbrt formally verified).
    function testFuzz_roots(uint256 x) public pure {
        uint256 r = S.sqrtWad(x);
        assertEq(W.sqrtWad(x), r);
        assertEq(W.sqrtWadDown(x), r);
        (uint256 h, uint256 l) = _mul512(r, r);
        (uint256 nh, uint256 nl) = _mul512(x, WAD);
        assertEq(W.sqrtWadUp(x), (h == nh && l == nl) ? r : r + 1);
        uint256 c = S.cbrtWad(x);
        assertEq(W.cbrtWad(x), c);
        assertEq(W.cbrtWadDown(x), c);
        uint256 up = W.cbrtWadUp(x);
        assertTrue(up == c || up == c + 1);
    }

    function _mul512(uint256 a, uint256 b) internal pure returns (uint256 h, uint256 l) {
        assembly {
            l := mul(a, b)
            let mm := mulmod(a, b, not(0))
            h := sub(sub(mm, l), lt(mm, l))
        }
    }

    /// Up is Down or one above, and both are monotone, across the domains.
    function testFuzz_directions(int256 x, int256 y) public pure {
        int256 e = int256(bound(x, -42e18, 135305999368893231589));
        _pair(W.expWad(e), W.expWadUp(e));
        assertLe(W.expWad(e - 1), W.expWad(e));
        int256 p = int256(bound(x, 1, type(int256).max));
        _pair(W.lnWad(p), W.lnWadUp(p));
        _pair(W.log2Wad(p), W.log2WadUp(p));
        _pair(W.log10Wad(p), W.log10WadUp(p));
        if (p > 1) assertLe(W.lnWad(p - 1), W.lnWad(p));
        int256 w = int256(bound(x, -367879441171442321, type(int256).max));
        _pair(W.lambertW0WadDown(w), W.lambertW0WadUp(w));
        int256 z = W.lambertW0Wad(w);
        assertTrue(z == (w < 0 ? W.lambertW0WadUp(w) : W.lambertW0WadDown(w)), "W0 toward zero");
        int256 b = int256(bound(x, 0.01e18, 100e18));
        int256 k = int256(bound(y, -20e18, 20e18));
        _pair(W.powWad(b, k), W.powWadUp(b, k));
        assertEq(W.exp(e), W.expWad(e));
        assertEq(W.ln(p), W.lnWad(p));
        assertEq(W.pow(b, k), W.powWad(b, k));
        assertEq(W.expWadDown(e), W.expWad(e));
        assertEq(W.lnWadDown(p), W.lnWad(p));
        assertEq(W.log2WadDown(p), W.log2Wad(p));
        assertEq(W.log10WadDown(p), W.log10Wad(p));
        assertEq(W.powWadDown(b, k), W.powWad(b, k));
    }

    function _pair(int256 down, int256 up) internal pure {
        assertTrue(up == down || up == down + 1, "up - down in {0, 1}");
    }
}

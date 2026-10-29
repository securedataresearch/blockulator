// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {FP127Harness, IHuffFP127} from "../base/FP127Harness.sol";
import {IFP127} from "../../contracts/src/fp127/IFP127.sol";

/// @title Equivalence
/// @notice Proves "generated from one source" and "matches the live Huff".
///
/// Three implementations of every op are compared:
///   obj   the deployed Yul object, via staticcall
///   lib   the inline Solidity library, via LibUser
///   huff  the runtime bytecode fetched from Sepolia, via its legacy ABI
///
/// 1. obj == lib on the full int256 domain, including which inputs revert
///    and with what data.
/// 2. obj == huff on every input where the Huff did not wrap. "Did not wrap"
///    is decided by an independent reference (Ref, built on Solady's
///    fullMulDiv), never by the Yul itself.
/// 3. Named divergence tests record the one policy change: the Yul reverts
///    where the Huff silently wrapped or returned garbage.
contract Equivalence is FP127Harness {
    // -----------------------------------------------------------------------
    // 1. Deployed object == inline library, full domain
    // -----------------------------------------------------------------------

    function testFuzz_objEqLib_add(int256 a, int256 b) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.add, (a, b))),
                    _try(address(lib), abi.encodeCall(IFP127.add, (a, b))), "add");
    }

    function testFuzz_objEqLib_sub(int256 a, int256 b) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.sub, (a, b))),
                    _try(address(lib), abi.encodeCall(IFP127.sub, (a, b))), "sub");
    }

    function testFuzz_objEqLib_mul(int256 a, int256 b) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.mul, (a, b))),
                    _try(address(lib), abi.encodeCall(IFP127.mul, (a, b))), "mul");
    }

    function testFuzz_objEqLib_div(int256 a, int256 b) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.div, (a, b))),
                    _try(address(lib), abi.encodeCall(IFP127.div, (a, b))), "div");
    }

    function testFuzz_objEqLib_fromFixed18(int256 x) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.fromFixed18, (x))),
                    _try(address(lib), abi.encodeCall(IFP127.fromFixed18, (x))), "fromFixed18");
    }

    function testFuzz_objEqLib_toFixed18(int256 x) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.toFixed18, (x))),
                    _try(address(lib), abi.encodeCall(IFP127.toFixed18, (x))), "toFixed18");
    }

    /// The caller harness bubbles the object's result and revert data unchanged.
    function testFuzz_callerEqObj_mul(int256 a, int256 b) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.mul, (a, b))),
                    _try(address(caller), abi.encodeCall(IFP127.mul, (a, b))), "caller mul");
    }

    function testFuzz_callerEqObj_div(int256 a, int256 b) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.div, (a, b))),
                    _try(address(caller), abi.encodeCall(IFP127.div, (a, b))), "caller div");
    }

    // -----------------------------------------------------------------------
    // 2. Object == reference == Huff wherever the Huff did not wrap
    // -----------------------------------------------------------------------

    /// Runs op on ref, obj and huff. If ref says the exact result fits, all
    /// three must agree. If ref says it does not fit, obj must revert with
    /// the expected selector. Huff is only consulted when ref succeeds.
    function _triple(
        bytes memory newCall,
        bytes memory huffCall,
        bytes4 expectedErr,
        string memory what
    ) internal view {
        Res memory r = _try(address(ref), newCall);
        Res memory o = _try(_objOf(newCall), newCall);
        if (r.ok) {
            assertTrue(o.ok, string.concat(what, ": obj reverted where ref fits"));
            assertEq(o.value, r.value, string.concat(what, ": obj != ref"));
            Res memory h = _try(address(huff), huffCall);
            assertTrue(h.ok, string.concat(what, ": huff reverted"));
            assertEq(o.value, h.value, string.concat(what, ": obj != huff"));
        } else {
            assertFalse(o.ok, string.concat(what, ": obj succeeded where ref overflows"));
            assertEq(_sel(o.err), expectedErr, string.concat(what, ": wrong error"));
        }
    }

    function testFuzz_add(int256 a, int256 b) public view {
        _triple(abi.encodeCall(IFP127.add, (a, b)),
                abi.encodeCall(IHuffFP127.addRaw, (uint256(a), uint256(b))),
                IFP127.Overflow.selector, "add");
    }

    function testFuzz_sub(int256 a, int256 b) public view {
        _triple(abi.encodeCall(IFP127.sub, (a, b)),
                abi.encodeCall(IHuffFP127.subRaw, (uint256(a), uint256(b))),
                IFP127.Overflow.selector, "sub");
    }

    function testFuzz_mul(int256 a, int256 b) public view {
        _triple(abi.encodeCall(IFP127.mul, (a, b)),
                abi.encodeCall(IHuffFP127.mulRaw, (uint256(a), uint256(b))),
                IFP127.Overflow.selector, "mul");
    }

    /// Unbounded fuzz almost always overflows mul. This one keeps both
    /// operands inside +/- 2^190 so the product fits and the Huff path is
    /// exercised on every run.
    function testFuzz_mul_inRange(int256 a, int256 b) public view {
        a = bound(a, -(int256(1) << 190), int256(1) << 190);
        b = bound(b, -(int256(1) << 190), int256(1) << 190);
        _triple(abi.encodeCall(IFP127.mul, (a, b)),
                abi.encodeCall(IHuffFP127.mulRaw, (uint256(a), uint256(b))),
                IFP127.Overflow.selector, "mul");
    }

    function testFuzz_div(int256 a, int256 b) public view {
        vm.assume(b != 0);
        _triple(abi.encodeCall(IFP127.div, (a, b)),
                abi.encodeCall(IHuffFP127.divRaw, (uint256(a), uint256(b))),
                IFP127.Overflow.selector, "div");
    }

    /// Keeps |a| < 2^190 and |b| >= 2^64 so the quotient fits and the Huff
    /// path is exercised on every run.
    function testFuzz_div_inRange(int256 a, int256 b) public view {
        a = bound(a, -(int256(1) << 190), int256(1) << 190);
        b = bound(b, int256(1) << 64, MAX);
        if (a & 1 == 1) b = -b;
        _triple(abi.encodeCall(IFP127.div, (a, b)),
                abi.encodeCall(IHuffFP127.divRaw, (uint256(a), uint256(b))),
                IFP127.Overflow.selector, "div");
    }

    function testFuzz_fromFixed18(int256 x) public view {
        _triple(abi.encodeCall(IFP127.fromFixed18, (x)),
                abi.encodeCall(IHuffFP127.fromFixed18, (uint256(x))),
                IFP127.OutOfRange.selector, "fromFixed18");
    }

    function testFuzz_fromFixed18_inRange(int256 x) public view {
        x = bound(x, -(int256(1) << 127), (int256(1) << 127) - 1);
        _triple(abi.encodeCall(IFP127.fromFixed18, (x)),
                abi.encodeCall(IHuffFP127.fromFixed18, (uint256(x))),
                IFP127.OutOfRange.selector, "fromFixed18");
    }

    function testFuzz_toFixed18(int256 x) public view {
        _triple(abi.encodeCall(IFP127.toFixed18, (x)),
                abi.encodeCall(IHuffFP127.toFixed18, (uint256(x))),
                bytes4(0), "toFixed18");
    }

    // -----------------------------------------------------------------------
    // 3. Named divergences: where the Yul reverts and the Huff did not
    // -----------------------------------------------------------------------

    function test_divergence_add_wraps() public view {
        // Huff: MAX + 1 wraps to MIN. Yul: Overflow.
        assertEq(int256(huff.addRaw(uint256(MAX), 1)), MIN);
        Res memory o = _try(address(obj), abi.encodeCall(IFP127.add, (MAX, 1)));
        assertFalse(o.ok);
        assertEq(_sel(o.err), IFP127.Overflow.selector);
    }

    function test_divergence_sub_wraps() public view {
        // Huff: MIN - 1 wraps to MAX. Yul: Overflow.
        assertEq(int256(huff.subRaw(uint256(MIN), 1)), MAX);
        Res memory o = _try(address(obj), abi.encodeCall(IFP127.sub, (MIN, 1)));
        assertFalse(o.ok);
        assertEq(_sel(o.err), IFP127.Overflow.selector);
    }

    function test_divergence_mul_wraps() public view {
        // 2^64 * 2^64 = 2^128, whose raw encoding 2^256 does not fit.
        int256 x = int256(1) << 192;
        // Huff: the 4-term sum wraps to 0.
        assertEq(huff.mulRaw(uint256(x), uint256(x)), 0);
        Res memory o = _try(address(obj), abi.encodeCall(IFP127.mul, (x, x)));
        assertFalse(o.ok);
        assertEq(_sel(o.err), IFP127.Overflow.selector);
    }

    function test_divergence_div_by_zero() public view {
        // Huff: returns (|a| >> 128) * 128 with the sign fixed. For a = 2.0
        // that is 256, observed live on Sepolia. Yul: DivisionByZero.
        assertEq(huff.divRaw(uint256(2 * ONE), 0), 256);
        Res memory o = _try(address(obj), abi.encodeCall(IFP127.div, (2 * ONE, 0)));
        assertFalse(o.ok);
        assertEq(_sel(o.err), IFP127.DivisionByZero.selector);
    }

    function test_divergence_div_quotient_overflow() public view {
        // (2^200) / 2^-64 = 2^264 as a value; raw 2^392 does not fit.
        int256 a = int256(1) << 200;
        int256 b = int256(1) << 64;
        Res memory h = _try(address(huff), abi.encodeCall(IHuffFP127.divRaw, (uint256(a), uint256(b))));
        assertTrue(h.ok, "huff returned something");
        Res memory o = _try(address(obj), abi.encodeCall(IFP127.div, (a, b)));
        assertFalse(o.ok);
        assertEq(_sel(o.err), IFP127.Overflow.selector);
    }

    function test_divergence_fromFixed18_wraps() public view {
        // 2^127 << 128 loses its top bit and flips sign in the Huff.
        int256 x = int256(1) << 127;
        int256 h = int256(huff.fromFixed18(uint256(x)));
        assertTrue(h < 0, "huff flipped sign");
        Res memory o = _try(address(obj), abi.encodeCall(IFP127.fromFixed18, (x)));
        assertFalse(o.ok);
        assertEq(_sel(o.err), IFP127.OutOfRange.selector);
    }

    function test_unknownSelector_reverts_empty() public view {
        (bool ok, bytes memory out) = address(obj).staticcall(hex"deadbeef");
        assertFalse(ok);
        assertEq(out.length, 0);
    }

    // -----------------------------------------------------------------------
    // Properties (independent of Huff)
    // -----------------------------------------------------------------------

    /// fromFixed18 truncates toward zero and toFixed18 floors, so the round
    /// trip is exact for negatives and at most 1 ULP low for positives.
    function testFuzz_prop_fixed18_roundtrip(int256 w) public view {
        w = bound(w, -(int256(1) << 127), (int256(1) << 127) - 1);
        int256 back = obj.toFixed18(obj.fromFixed18(w));
        assertLe(back, w);
        assertLe(w - back, 1);
    }

    function testFuzz_prop_mul_one(int256 a) public view {
        assertEq(obj.mul(a, ONE), a);
        assertEq(obj.mul(ONE, a), a);
    }

    function testFuzz_prop_div_one(int256 a) public view {
        assertEq(obj.div(a, ONE), a);
    }

    function testFuzz_prop_mul_commutes(int256 a, int256 b) public view {
        _assertSame(_try(address(obj), abi.encodeCall(IFP127.mul, (a, b))),
                    _try(address(obj), abi.encodeCall(IFP127.mul, (b, a))), "mul commutes");
    }

    /// div(mul(a, b), b) is within 2 ULP of a once |b| >= ONE.
    function testFuzz_prop_mul_then_div(int256 a, int256 b) public view {
        a = bound(a, -(int256(1) << 180), int256(1) << 180);
        b = bound(b, ONE, int256(1) << 200);
        if (a & 1 == 1) b = -b;
        int256 back = obj.div(obj.mul(a, b), b);
        int256 d = back > a ? back - a : a - back;
        assertLe(d, 2);
    }

    function test_known_values() public view {
        assertEq(obj.mul(2 * ONE, 3 * ONE), 6 * ONE);
        assertEq(obj.div(3 * ONE, 2 * ONE), ONE + ONE / 2);
        assertEq(obj.mul(-2 * ONE, 3 * ONE), -6 * ONE);
        assertEq(obj.div(-3 * ONE, 2 * ONE), -(ONE + ONE / 2));
        assertEq(obj.fromFixed18(1e18), ONE);
        assertEq(obj.toFixed18(ONE), 1e18);
        assertEq(obj.fromFixed18(-5e17), -ONE / 2);
        // exact negative product, no rounding involved
        assertEq(obj.mul(-ONE, ONE / 3), -(ONE / 3));
        // rounding direction: mul floors toward -inf, div truncates toward 0.
        // -1 * (1 + 2^-128) = -(ONE + 1): floor keeps the -1 ULP.
        assertEq(obj.mul(-ONE, ONE + 1), -(ONE + 1));
        // -(ONE+1) / 2: exact value -(2^127 + 0.5); trunc gives -2^127.
        assertEq(obj.div(-(ONE + 1), 2 * ONE), -(ONE / 2));
        // mul of the same quantity: floor gives -(2^127) - 1.
        assertEq(obj.mul(-(ONE + 1), ONE / 2), -(ONE / 2) - 1);
    }
}

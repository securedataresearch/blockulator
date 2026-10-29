// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {console} from "forge-std/console.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import {BL19Lib} from "../../contracts/src/bl19/BL19Lib.sol";

/// @title ViaIrBench
/// @notice make profile's build-setting bench: the inline libraries on
///         typical inputs beside the Yul objects. make profile runs it twice,
///         under the default profile (via_ir = false) and under
///         [profile.viair] (via_ir = true), and asks whether compiling the
///         caller through the IR closes the gap between BL127Lib / BL19Lib
///         and the objects, which solc compiles with its Yul optimizer.
///         Prints VIA|lib|op|i|form|gas: form inline is the library call
///         alone (timed inside lib127 / lib19, net of the "id" window, as the
///         gas ladders do; the result is stored to memory inside the window
///         so the IR optimizer can neither drop nor move the call), form
///         object the whole staticcall. The trivial ops (abs, neg, ...) give
///         the object's own call and dispatch cost per selector position.
contract ViaIrBench is Test {
    address internal bl127;
    address internal bl127e;
    address internal bl127h;
    address internal bl127n;
    address internal bl127s;
    address internal bl19;
    address internal bl19e;
    address internal bl19h;
    address internal bl19n;
    address internal bl19s;
    uint256 constant N = 8;

    function setUp() public {
        bl127 = _deploy("out/BL127.yul/BL127.json");
        bl127e = _deploy("out/BL127E.yul/BL127E.json");
        bl127h = _deploy("out/BL127H.yul/BL127H.json");
        bl127n = _deploy("out/BL127N.yul/BL127N.json");
        bl127s = _deploy("out/BL127S.yul/BL127S.json");
        bl19 = _deploy("out/BL19.yul/BL19.json");
        bl19e = _deploy("out/BL19E.yul/BL19E.json");
        bl19h = _deploy("out/BL19H.yul/BL19H.json");
        bl19n = _deploy("out/BL19N.yul/BL19N.json");
        bl19s = _deploy("out/BL19S.yul/BL19S.json");
    }

    function _deploy(string memory artifact) internal returns (address d) {
        bytes memory init = vm.parseJsonBytes(vm.readFile(artifact), ".bytecode.object");
        assembly {
            d := create(0, add(init, 0x20), mload(init))
        }
        require(d != address(0), artifact);
    }

    // ---- the timed entry points -----------------------------------------

    function lib127(bytes32 op, int256 x, int256 y) external view returns (uint256 g) {
        uint256 g0;
        int256 r;
        if (op == "id") { g0 = gasleft(); r = x; assembly { mstore(0, r) } g = gasleft(); }
        if (op == "abs") { g0 = gasleft(); r = BL127Lib.abs(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "neg") { g0 = gasleft(); r = BL127Lib.neg(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "sign") { g0 = gasleft(); r = BL127Lib.sign(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "floor") { g0 = gasleft(); r = BL127Lib.floor(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "ceil") { g0 = gasleft(); r = BL127Lib.ceil(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "frac") { g0 = gasleft(); r = BL127Lib.frac(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "add") { g0 = gasleft(); r = BL127Lib.add(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "sub") { g0 = gasleft(); r = BL127Lib.sub(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "min") { g0 = gasleft(); r = BL127Lib.min(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "max") { g0 = gasleft(); r = BL127Lib.max(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "mul") { g0 = gasleft(); r = BL127Lib.mul(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "div") { g0 = gasleft(); r = BL127Lib.div(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "sqrt") { g0 = gasleft(); r = BL127Lib.sqrt(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "exp") { g0 = gasleft(); r = BL127Lib.exp(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "ln") { g0 = gasleft(); r = BL127Lib.ln(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "pow") { g0 = gasleft(); r = BL127Lib.pow(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "cbrt") { g0 = gasleft(); r = BL127Lib.cbrt(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "sinh") { g0 = gasleft(); r = BL127Lib.sinh(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "cosh") { g0 = gasleft(); r = BL127Lib.cosh(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "erf") { g0 = gasleft(); r = BL127Lib.erf(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "normCdf") { g0 = gasleft(); r = BL127Lib.normCdf(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "lambertW0") { g0 = gasleft(); r = BL127Lib.lambertW0(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "lambertWm1") { g0 = gasleft(); r = BL127Lib.lambertWm1(x); assembly { mstore(0, r) } g = gasleft(); }
        require(g0 != 0, "op");
        g = g0 - g;
    }

    function lib19(bytes32 op, int256 x, int256 y) external view returns (uint256 g) {
        uint256 g0;
        int256 r;
        if (op == "id") { g0 = gasleft(); r = x; assembly { mstore(0, r) } g = gasleft(); }
        if (op == "abs") { g0 = gasleft(); r = BL19Lib.abs(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "neg") { g0 = gasleft(); r = BL19Lib.neg(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "sign") { g0 = gasleft(); r = BL19Lib.sign(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "cmp") { g0 = gasleft(); r = BL19Lib.cmp(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "lt") { g0 = gasleft(); r = BL19Lib.lt(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "eq") { g0 = gasleft(); r = BL19Lib.eq(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "add") { g0 = gasleft(); r = BL19Lib.add(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "mul") { g0 = gasleft(); r = BL19Lib.mul(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "div") { g0 = gasleft(); r = BL19Lib.div(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "sqrt") { g0 = gasleft(); r = BL19Lib.sqrt(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "exp") { g0 = gasleft(); r = BL19Lib.exp(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "ln") { g0 = gasleft(); r = BL19Lib.ln(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "pow") { g0 = gasleft(); r = BL19Lib.pow(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "erf") { g0 = gasleft(); r = BL19Lib.erf(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "normCdf") { g0 = gasleft(); r = BL19Lib.normCdf(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "lambertW0") { g0 = gasleft(); r = BL19Lib.lambertW0(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "lambertWm1") { g0 = gasleft(); r = BL19Lib.lambertWm1(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "min") { g0 = gasleft(); r = BL19Lib.min(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "max") { g0 = gasleft(); r = BL19Lib.max(x, y); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "exp2") { g0 = gasleft(); r = BL19Lib.exp2(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "log2") { g0 = gasleft(); r = BL19Lib.log2(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "cbrt") { g0 = gasleft(); r = BL19Lib.cbrt(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "cosh") { g0 = gasleft(); r = BL19Lib.cosh(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "tanh") { g0 = gasleft(); r = BL19Lib.tanh(x); assembly { mstore(0, r) } g = gasleft(); }
        if (op == "hypot") { g0 = gasleft(); r = BL19Lib.hypot(x, y); assembly { mstore(0, r) } g = gasleft(); }
        require(g0 != 0, "op");
        g = g0 - g;
    }

    // ---- measurement ----------------------------------------------------

    function _inline(bool is127, bytes32 op, int256 x, int256 y) internal view returns (int256) {
        bytes4 sel = is127 ? this.lib127.selector : this.lib19.selector;
        (bool ok, bytes memory out) = address(this).staticcall(abi.encodeWithSelector(sel, op, x, y));
        if (!ok) return -1;
        (, bytes memory outId) = address(this).staticcall(abi.encodeWithSelector(sel, bytes32("id"), x, y));
        return int256(abi.decode(out, (uint256))) - int256(abi.decode(outId, (uint256)));
    }

    function _object(address t, bytes memory data) internal view returns (int256) {
        uint256 g0 = gasleft();
        (bool ok,) = t.staticcall(data);
        uint256 g = g0 - gasleft();
        return ok ? int256(g) : -1;
    }

    function _emit(string memory lib, string memory op, uint256 i, string memory form, int256 g) internal pure {
        if (g < 0) return;
        console.log(string.concat("VIA|", lib, "|", op, "|", vm.toString(i), "|", form, "|", vm.toString(uint256(g))));
    }

    function _one(bool is127, string memory op, uint256 i, int256 x, int256 y, bool two) internal view {
        address t = is127 ? _obj127(op) : _obj19(op);
        bytes memory data = two ? abi.encodeWithSignature(string.concat(op, "(int256,int256)"), x, y)
                                : abi.encodeWithSignature(string.concat(op, "(int256)"), x);
        string memory lib = is127 ? "bl127" : "bl19";
        _emit(lib, op, i, "inline", _inline(is127, bytes32(bytes(op)), x, y));
        _emit(lib, op, i, "object", _object(t, data));
    }

    function _obj127(string memory op) internal view returns (address) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("erf") || h == keccak256("erfc") || h == keccak256("normCdf")) return bl127n;
        if (h == keccak256("lambertW0") || h == keccak256("lambertWm1")) return bl127s;
        if (h == keccak256("sinh") || h == keccak256("cosh") || h == keccak256("tanh") || h == keccak256("atanh")) return bl127h;
        if (h == keccak256("exp") || h == keccak256("exp2") || h == keccak256("exp10") || h == keccak256("expm1")
            || h == keccak256("ln") || h == keccak256("log2") || h == keccak256("log10") || h == keccak256("log2Up")
            || h == keccak256("log1p") || h == keccak256("pow") || h == keccak256("powu") || h == keccak256("compound")) return bl127e;
        return bl127;
    }

    function _obj19(string memory op) internal view returns (address) {
        bytes32 h = keccak256(bytes(op));
        if (h == keccak256("erf") || h == keccak256("erfc") || h == keccak256("normCdf")) return bl19n;
        if (h == keccak256("lambertW0") || h == keccak256("lambertWm1")) return bl19s;
        if (h == keccak256("sinh") || h == keccak256("cosh") || h == keccak256("tanh") || h == keccak256("atanh")) return bl19h;
        if (h == keccak256("exp") || h == keccak256("exp2") || h == keccak256("exp10") || h == keccak256("expm1")
            || h == keccak256("ln") || h == keccak256("log2") || h == keccak256("log10") || h == keccak256("log2Up")
            || h == keccak256("log1p") || h == keccak256("pow") || h == keccak256("powu") || h == keccak256("compound")) return bl19e;
        return bl19;
    }

    // ---- typical inputs, as the gas ladders draw them -------------------

    function _rnd(string memory op, uint256 i) internal pure returns (uint256) {
        return uint256(keccak256(abi.encode("typical", op, i)));
    }

    /// BL127: magnitude in [2^e, 2^(e+1)), e uniform in [elo, ehi], random mantissa.
    function _t127(string memory op, uint256 i, int256 elo, int256 ehi, int256 sgn) internal pure returns (int256 x) {
        uint256 h = _rnd(op, i);
        int256 e = elo + int256(h % uint256(ehi - elo + 1));
        uint256 m = (h >> 128) | (uint256(1) << 128);
        x = int256(e >= 0 ? m << uint256(e) : m >> uint256(-e));
        if (sgn < 0 || (sgn == 0 && (h >> 64) & 1 == 1)) x = -x;
    }

    /// BL19: exponent uniform in [elo, ehi], 236 random fraction bits.
    function _t19(string memory op, uint256 i, int256 elo, int256 ehi, int256 sgn) internal pure returns (int256) {
        uint256 h = _rnd(op, i);
        int256 e = elo + int256(h % uint256(ehi - elo + 1));
        uint256 f = (uint256(keccak256(abi.encode(h))) >> 20) & ((uint256(1) << 236) - 1);
        bool neg = sgn < 0 || (sgn == 0 && (h >> 64) & 1 == 1);
        return int256((neg ? uint256(1) << 255 : 0) | (uint256(e + 0x3ffff) << 236) | f);
    }

    function _u127(string memory op, int256 elo, int256 ehi, int256 sgn) internal view {
        for (uint256 i; i < N; i++) _one(true, op, i, _t127(op, i, elo, ehi, sgn), 0, false);
    }

    function _b127(string memory op) internal view {
        for (uint256 i; i < N; i++) _one(true, op, i, _t127(op, i, -8, 8, 0), _t127(op, i + 100, -8, 8, 0), true);
    }

    function _u19(string memory op, int256 elo, int256 ehi, int256 sgn) internal view {
        for (uint256 i; i < N; i++) _one(false, op, i, _t19(op, i, elo, ehi, sgn), 0, false);
    }

    function _b19(string memory op) internal view {
        for (uint256 i; i < N; i++) _one(false, op, i, _t19(op, i, -8, 8, 0), _t19(op, i + 100, -8, 8, 0), true);
    }

    function test_viair_bl127() public view {
        _object(bl127, abi.encodeWithSignature("abs(int256)", int256(1)));
        _u127("abs", -8, 8, 0);
        _u127("neg", -8, 8, 0);
        _u127("sign", -8, 8, 0);
        _u127("floor", -8, 8, 0);
        _u127("ceil", -8, 8, 0);
        _u127("frac", -8, 8, 0);
        _b127("add");
        _b127("sub");
        _b127("min");
        _b127("max");
        _b127("mul");
        _b127("div");
        _u127("sqrt", -60, 100, 1);
        _u127("exp", -4, 5, 0);
        _u127("ln", -60, 60, 1);
        for (uint256 i; i < N; i++) _one(true, "pow", i, _t127("pow", i, -4, 4, 1), _t127("pow", i + 100, -4, 3, 0), true);
        _u127("cbrt", -60, 100, 0);
        _u127("sinh", -8, 5, 0);
        _u127("cosh", -8, 5, 0);
        _u127("erf", -4, 2, 0);
        _u127("normCdf", -4, 3, 0);
        _u127("lambertW0", -10, 40, 1);
        _u127("lambertWm1", -30, -3, -1);
    }

    function test_viair_bl19() public view {
        _object(bl19, abi.encodeWithSignature("abs(int256)", int256(1)));
        _object(bl19e, abi.encodeWithSignature("exp(int256)", int256(1)));
        _object(bl19h, abi.encodeWithSignature("sinh(int256)", int256(1)));
        _object(bl19n, abi.encodeWithSignature("erf(int256)", int256(1)));
        _object(bl19s, abi.encodeWithSignature("lambertW0(int256)", int256(1)));
        _u19("abs", -8, 8, 0);
        _u19("neg", -8, 8, 0);
        _u19("sign", -8, 8, 0);
        _b19("cmp");
        _b19("lt");
        _b19("eq");
        _b19("add");
        _b19("mul");
        _b19("div");
        _u19("sqrt", -300, 300, 1);
        _u19("exp", -6, 5, 0);
        _u19("ln", -60, 60, 1);
        for (uint256 i; i < N; i++) _one(false, "pow", i, _t19("pow", i, -4, 4, 1), _t19("pow", i + 100, -4, 3, 0), true);
        _u19("erf", -6, 2, 0);
        _u19("normCdf", -4, 3, 0);
        _u19("lambertW0", -10, 40, 1);
        _u19("lambertWm1", -60, -3, -1);
        _b19("min");
        _b19("max");
        _u19("exp2", -6, 6, 0);
        _u19("log2", -60, 60, 1);
        _u19("cbrt", -300, 300, 0);
        _u19("cosh", -6, 5, 0);
        _u19("tanh", -6, 4, 0);
        _b19("hypot");
    }
}

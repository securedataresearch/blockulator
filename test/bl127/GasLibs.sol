// SPDX-License-Identifier: AGPL-3.0-only
pragma solidity ^0.8.24;

// AGPL-3.0-only because it links Solmate's FixedPointMathLib (lib/solmate).

import {wadMul, wadDiv, wadExp, wadLn, wadPow} from "../../lib/solmate/src/utils/SignedWadMath.sol";
import {FixedPointMathLib as SM} from "../../lib/solmate/src/utils/FixedPointMathLib.sol";
import {Math as OZ} from "../../contracts/src/ladder/vendor/openzeppelin/utils/math/Math.sol";
import {SignedMath as OZS} from "../../contracts/src/ladder/vendor/openzeppelin/utils/math/SignedMath.sol";
import {FullMath} from "../../contracts/src/ladder/vendor/uniswap/FullMath.sol";
import {UD60x18, ud} from "../../lib/prb-math/src/UD60x18.sol";
import * as PU from "../../lib/prb-math/src/ud60x18/Math.sol";
import {add as puAdd, sub as puSub} from "../../lib/prb-math/src/ud60x18/Helpers.sol";
import {ISnekmateMath} from "../../contracts/src/ladder/LadderSnekmate.sol";

/// @title GasLibs
/// @notice GasLadder's entry points for the libraries added with issue #166:
///         Solmate, OpenZeppelin Math, Uniswap FullMath, PRBMath UD60x18 and
///         snekmate (Vyper). The same contract as GasLadder's own entry
///         points: find the op by name, read gasleft() on either side of the
///         one library call, revert "na" where the library has no such op
///         and "domain" outside the function's domain. GasLadder subtracts
///         the same window around an assignment (op "id").
///
///         snekmate is a Vyper library, so it runs in its own contract
///         (contracts/src/ladder/vyper/SnekmateMath.vy), which reads msg.gas
///         around the module call and returns it with the result: its cells
///         are that figure net of the same window around an assignment
///         (noop), the call as a Vyper contract pays it, with no external
///         call in it. Its "id" is zero.
contract GasLibs {
    ISnekmateMath immutable snek;

    constructor(address s) { snek = ISnekmateMath(s); }

    function _u(int256 x) internal pure returns (uint256) { require(x >= 0, "domain"); return uint256(x); }
    /// a plain integer n >= 1 from an integral WAD
    function _n(int256 x, uint256 lo) internal pure returns (uint256) {
        require(x >= int256(lo) * 1e18 && x % 1e18 == 0, "domain");
        return uint256(x) / 1e18;
    }

    // ---- Solmate ----------------------------------------------------------

    function cSolmate1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("exp")) { g0 = gasleft(); r = wadExp(x); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = wadLn(x); g = gasleft(); }
        // sqrt(uint256) is the integer root: a WAD root is sqrt(x 1e18)
        if (h == keccak256("sqrt")) { uint256 u = _u(x); require(u <= type(uint256).max / 1e18, "domain"); g0 = gasleft(); r = int256(SM.sqrt(u * 1e18)); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cSolmate2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("mul")) { g0 = gasleft(); r = wadMul(a, b); g = gasleft(); }
        if (h == keccak256("div")) { g0 = gasleft(); r = wadDiv(a, b); g = gasleft(); }
        if (h == keccak256("pow")) { g0 = gasleft(); r = wadPow(a, b); g = gasleft(); }
        if (h == keccak256("mulDown")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(SM.mulWadDown(x, y)); g = gasleft(); }
        if (h == keccak256("mulUp")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(SM.mulWadUp(x, y)); g = gasleft(); }
        if (h == keccak256("divDown")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(SM.divWadDown(x, y)); g = gasleft(); }
        if (h == keccak256("divUp")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(SM.divWadUp(x, y)); g = gasleft(); }
        // rpow(x, n, 1e18): a plain unsigned integer exponent
        if (h == keccak256("powu")) { (uint256 x, uint256 n) = (_u(a), _n(b, 0)); g0 = gasleft(); r = int256(SM.rpow(x, n, 1e18)); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    // ---- OpenZeppelin Math, SignedMath --------------------------------------

    function cOz1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = x; g = gasleft(); }
        if (h == keccak256("abs")) { g0 = gasleft(); r = int256(OZS.abs(x)); g = gasleft(); }
        // sqrt(uint256) is the integer root: a WAD root is sqrt(x 1e18)
        if (h == keccak256("sqrt")) { uint256 u = _u(x); require(u <= type(uint256).max / 1e18, "domain"); g0 = gasleft(); r = int256(OZ.sqrt(u * 1e18)); g = gasleft(); }
        // log2(uint256, Ceil) is ceil(log2 n) of the plain integer, BL127's log2Up on integers
        if (h == keccak256("log2Up")) { uint256 n = _n(x, 1); g0 = gasleft(); r = int256(OZ.log2(n, OZ.Rounding.Ceil)); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cOz2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("mulDown")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(OZ.mulDiv(x, y, 1e18)); g = gasleft(); }
        if (h == keccak256("mulUp")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(OZ.mulDiv(x, y, 1e18, OZ.Rounding.Ceil)); g = gasleft(); }
        if (h == keccak256("divDown")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(OZ.mulDiv(x, 1e18, y)); g = gasleft(); }
        if (h == keccak256("divUp")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(OZ.mulDiv(x, 1e18, y, OZ.Rounding.Ceil)); g = gasleft(); }
        if (h == keccak256("avg")) { g0 = gasleft(); r = OZS.average(a, b); g = gasleft(); }
        if (h == keccak256("min")) { g0 = gasleft(); r = OZS.min(a, b); g = gasleft(); }
        if (h == keccak256("max")) { g0 = gasleft(); r = OZS.max(a, b); g = gasleft(); }
        if (h == keccak256("zeroFloorSub")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(OZ.saturatingSub(x, y)); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    // ---- Uniswap v4 FullMath ------------------------------------------------

    function cUni2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        int256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = a; g = gasleft(); }
        if (h == keccak256("mulDown")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(FullMath.mulDiv(x, y, 1e18)); g = gasleft(); }
        if (h == keccak256("mulUp")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(FullMath.mulDivRoundingUp(x, y, 1e18)); g = gasleft(); }
        if (h == keccak256("divDown")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(FullMath.mulDiv(x, 1e18, y)); g = gasleft(); }
        if (h == keccak256("divUp")) { (uint256 x, uint256 y) = (_u(a), _u(b)); g0 = gasleft(); r = int256(FullMath.mulDivRoundingUp(x, 1e18, y)); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    // ---- PRBMath UD60x18 ----------------------------------------------------

    function cPrbud1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        uint256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = uint256(x); g = gasleft(); }
        bool known = h == keccak256("exp") || h == keccak256("exp2") || h == keccak256("ln") || h == keccak256("log2")
            || h == keccak256("log10") || h == keccak256("sqrt") || h == keccak256("inv") || h == keccak256("floor")
            || h == keccak256("ceil") || h == keccak256("frac");
        require(g0 != 0 || known, "na");
        UD60x18 v = ud(h == keccak256("id") ? 0 : _u(x));
        if (h == keccak256("exp")) { g0 = gasleft(); r = PU.exp(v).unwrap(); g = gasleft(); }
        if (h == keccak256("exp2")) { g0 = gasleft(); r = PU.exp2(v).unwrap(); g = gasleft(); }
        if (h == keccak256("ln")) { g0 = gasleft(); r = PU.ln(v).unwrap(); g = gasleft(); }
        if (h == keccak256("log2")) { g0 = gasleft(); r = PU.log2(v).unwrap(); g = gasleft(); }
        if (h == keccak256("log10")) { g0 = gasleft(); r = PU.log10(v).unwrap(); g = gasleft(); }
        if (h == keccak256("sqrt")) { g0 = gasleft(); r = PU.sqrt(v).unwrap(); g = gasleft(); }
        if (h == keccak256("inv")) { g0 = gasleft(); r = PU.inv(v).unwrap(); g = gasleft(); }
        if (h == keccak256("floor")) { g0 = gasleft(); r = PU.floor(v).unwrap(); g = gasleft(); }
        if (h == keccak256("ceil")) { g0 = gasleft(); r = PU.ceil(v).unwrap(); g = gasleft(); }
        if (h == keccak256("frac")) { g0 = gasleft(); r = PU.frac(v).unwrap(); g = gasleft(); }
        require(g0 != 0, "na");
        g = g0 - g;
    }

    function cPrbud2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 g0;
        uint256 r;
        if (h == keccak256("id")) { g0 = gasleft(); r = uint256(a); g = gasleft(); }
        bool known = h == keccak256("mul") || h == keccak256("div") || h == keccak256("pow") || h == keccak256("powu")
            || h == keccak256("avg") || h == keccak256("gavg") || h == keccak256("add") || h == keccak256("sub");
        require(g0 != 0 || known, "na");
        UD60x18 x = ud(h == keccak256("id") ? 0 : _u(a));
        // powu(UD60x18, uint256): a plain unsigned integer exponent
        if (h == keccak256("powu")) { uint256 n = _n(b, 0); g0 = gasleft(); r = PU.powu(x, n).unwrap(); g = gasleft(); }
        else if (h != keccak256("id")) {
            UD60x18 y = ud(_u(b));
            if (h == keccak256("mul")) { g0 = gasleft(); r = PU.mul(x, y).unwrap(); g = gasleft(); }
            if (h == keccak256("div")) { g0 = gasleft(); r = PU.div(x, y).unwrap(); g = gasleft(); }
            if (h == keccak256("pow")) { g0 = gasleft(); r = PU.pow(x, y).unwrap(); g = gasleft(); }
            if (h == keccak256("avg")) { g0 = gasleft(); r = PU.avg(x, y).unwrap(); g = gasleft(); }
            if (h == keccak256("gavg")) { g0 = gasleft(); r = PU.gm(x, y).unwrap(); g = gasleft(); }
            if (h == keccak256("add")) { g0 = gasleft(); r = puAdd(x, y).unwrap(); g = gasleft(); }
            if (h == keccak256("sub")) { g0 = gasleft(); r = puSub(x, y).unwrap(); g = gasleft(); }
        }
        g = g0 - g;
    }

    // ---- snekmate (Vyper) ---------------------------------------------------

    function _net(uint256 gv) internal view returns (uint256) {
        (, uint256 g0) = snek.noop(0);
        return gv - g0;
    }

    function cSnek1(string calldata op, int256 x) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 gv;
        if (h == keccak256("id")) return 0;
        if (h == keccak256("exp")) (, gv) = snek.wad_exp(x);
        else if (h == keccak256("ln")) (, gv) = snek.wad_ln(x);
        else if (h == keccak256("cbrt")) (, gv) = snek.wad_cbrt(_u(x));
        else if (h == keccak256("sign")) (, gv) = snek.signum(x);
        // log2(uint256, True) is ceil(log2 n) of the plain integer, BL127's log2Up on integers
        else if (h == keccak256("log2Up")) (, gv) = snek.log2(_n(x, 1), true);
        else revert("na");
        g = _net(gv);
    }

    function cSnek2(string calldata op, int256 a, int256 b) external view returns (uint256 g) {
        bytes32 h = keccak256(bytes(op));
        uint256 gv;
        if (h == keccak256("id")) return 0;
        if (h == keccak256("mulDown")) (, gv) = snek.mul_div(_u(a), _u(b), 1e18, false);
        else if (h == keccak256("mulUp")) (, gv) = snek.mul_div(_u(a), _u(b), 1e18, true);
        else if (h == keccak256("divDown")) (, gv) = snek.mul_div(_u(a), 1e18, _u(b), false);
        else if (h == keccak256("divUp")) (, gv) = snek.mul_div(_u(a), 1e18, _u(b), true);
        else if (h == keccak256("avg")) (, gv) = snek.int256_average(a, b);
        else revert("na");
        g = _net(gv);
    }
}

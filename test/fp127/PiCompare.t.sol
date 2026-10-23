// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FixedPointMathLib as S} from "../../lib/solady/src/utils/FixedPointMathLib.sol";
import {ABDKMath64x64 as A} from "../../lib/abdk-libraries-solidity/ABDKMath64x64.sol";
import {SD59x18, sd} from "../../lib/prb-math/src/SD59x18.sol";
import * as M from "../../lib/prb-math/src/sd59x18/Math.sol";
import {ABDKMathQuad as Q} from "../../lib/abdk-libraries-solidity/ABDKMathQuad.sol";
import {LogExpMath} from "../../contracts/src/ladder/vendor/balancer/LogExpMath.sol";
import {FP256Lib} from "../../contracts/src/fp256/FP256Lib.sol";

/// @title PiCompare
/// @notice Ramanujan's 1914 series for 1/pi, the same recipe through each
///         library's own sqrt, mul and div on its own grid. The term ratios
///         are integers and are applied exactly in every format; what
///         differs is the grid the running term lives on, the sqrt(2), and
///         the final reciprocal. Prints PICMP|form|terms|raw|scale|gas for
///         scripts/fp127/pi_compare.py, which writes docs/benchmarks/pi.md.
contract PiCompare is Test {
    int256 constant ONE = int256(1) << 128;

    function _series(uint256 terms, int256 one, function(int256) pure returns (int256) sqrt_,
                     function(int256, int256) pure returns (int256) mul_,
                     function(int256, int256) pure returns (int256) div_) internal pure returns (int256) {
        int256 c = one;
        int256 s = 0;
        for (uint256 k; k < terms; k++) {
            s += c * int256(1103 + 26390 * k);
            uint256 k4 = 4 * k;
            c = c * int256((k4 + 1) * (k4 + 2) * (k4 + 3) * (k4 + 4)) / int256((k + 1) ** 4 * 24591257856);
        }
        int256 invpi = mul_(2 * sqrt_(2 * one), s) / 9801;
        return div_(one, invpi);
    }

    function fpSqrt(int256 x) internal pure returns (int256) { return FP127Lib.sqrt(x); }
    function fpMul(int256 a, int256 b) internal pure returns (int256) { return FP127Lib.mul(a, b); }
    function fpDiv(int256 a, int256 b) internal pure returns (int256) { return FP127Lib.div(a, b); }
    function solSqrt(int256 x) internal pure returns (int256) { return int256(S.sqrtWad(uint256(x))); }
    function solMul(int256 a, int256 b) internal pure returns (int256) { return S.sMulWad(a, b); }
    function solDiv(int256 a, int256 b) internal pure returns (int256) { return S.sDivWad(a, b); }
    function prbSqrt(int256 x) internal pure returns (int256) { return M.sqrt(sd(x)).unwrap(); }
    function prbMul(int256 a, int256 b) internal pure returns (int256) { return M.mul(sd(a), sd(b)).unwrap(); }
    function prbDiv(int256 a, int256 b) internal pure returns (int256) { return M.div(sd(a), sd(b)).unwrap(); }
    function abdkSqrt(int256 x) internal pure returns (int256) { return A.sqrt(int128(x)); }
    function abdkMul(int256 a, int256 b) internal pure returns (int256) { return A.mul(int128(a), int128(b)); }
    function abdkDiv(int256 a, int256 b) internal pure returns (int256) { return A.div(int128(a), int128(b)); }
    function balSqrt(int256 x) internal pure returns (int256) { return int256(LogExpMath.pow(uint256(x), 5e17)); }
    function balMul(int256 a, int256 b) internal pure returns (int256) { return a * b / 1e18; }
    function balDiv(int256 a, int256 b) internal pure returns (int256) { return a * 1e18 / b; }

    /// FP256 has no grid either: the series through its own ops.
    function _seriesFP256(uint256 terms) internal pure returns (int256) {
        int256 c = FP256Lib.ONE;
        int256 s = 0;
        for (uint256 k; k < terms; k++) {
            s = FP256Lib.add(s, FP256Lib.mul(c, FP256Lib.fromUint(1103 + 26390 * k)));
            uint256 k4 = 4 * k;
            c = FP256Lib.div(FP256Lib.mul(c, FP256Lib.fromUint((k4 + 1) * (k4 + 2) * (k4 + 3) * (k4 + 4))), FP256Lib.fromUint((k + 1) ** 4 * 24591257856));
        }
        int256 invpi = FP256Lib.div(FP256Lib.mul(FP256Lib.mul(FP256Lib.fromUint(2), FP256Lib.sqrt(FP256Lib.fromUint(2))), s), FP256Lib.fromUint(9801));
        return FP256Lib.div(FP256Lib.ONE, invpi);
    }

    /// Quad has no grid: the series is run on bytes16 directly, the integer
    /// term ratios through fromUInt, and the bit pattern is logged.
    function _seriesQuad(uint256 terms) internal pure returns (int256) {
        bytes16 c = Q.fromUInt(1);
        bytes16 s = Q.fromUInt(0);
        for (uint256 k; k < terms; k++) {
            s = Q.add(s, Q.mul(c, Q.fromUInt(1103 + 26390 * k)));
            uint256 k4 = 4 * k;
            c = Q.div(Q.mul(c, Q.fromUInt((k4 + 1) * (k4 + 2) * (k4 + 3) * (k4 + 4))), Q.fromUInt((k + 1) ** 4 * 24591257856));
        }
        bytes16 invpi = Q.div(Q.mul(Q.mul(Q.fromUInt(2), Q.sqrt(Q.fromUInt(2))), s), Q.fromUInt(9801));
        return int256(uint256(uint128(Q.div(Q.fromUInt(1), invpi))));
    }

    function _log(string memory form, uint256 terms, int256 raw, string memory scale, uint256 gas) internal pure {
        console.log(string.concat("PICMP|", form, "|", vm.toString(terms), "|", vm.toString(raw), "|", scale, "|", vm.toString(gas)));
    }

    function test_pi_compare() public view {
        for (uint256 t = 1; t <= 10; t++) {
            uint256 g0 = gasleft(); int256 r = _series(t, ONE, fpSqrt, fpMul, fpDiv); _log("fp127lib", t, r, "2**128", g0 - gasleft());
            g0 = gasleft(); r = _series(t, 1e18, solSqrt, solMul, solDiv); _log("solady", t, r, "10**18", g0 - gasleft());
            g0 = gasleft(); r = _series(t, 1e18, prbSqrt, prbMul, prbDiv); _log("prb", t, r, "10**18", g0 - gasleft());
            g0 = gasleft(); r = _series(t, int256(1) << 64, abdkSqrt, abdkMul, abdkDiv); _log("abdk", t, r, "2**64", g0 - gasleft());
            g0 = gasleft(); r = _series(t, 1e18, balSqrt, balMul, balDiv); _log("balancer", t, r, "10**18", g0 - gasleft());
            g0 = gasleft(); r = _seriesQuad(t); _log("quad", t, r, "binary128", g0 - gasleft());
            g0 = gasleft(); r = _seriesFP256(t); _log("fp256", t, r, "fp256", g0 - gasleft());
        }
        // the libraries' constants, for reference: PRBMath's 18 decimals, and
        // FP127Lib.PI and FP256Lib.PI, each its format's word nearest pi
        _log("prb-constant", 0, 3_141592653589793238, "10**18", 0);
        _log("fp127-constant", 0, FP127Lib.PI, "2**128", 0);
        _log("fp256-constant", 0, FP256Lib.PI, "fp256", 0);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {BL127Lib as F} from "bl127/BL127Lib.sol";

/// @notice Pi from nothing but square roots, on the inline library: two
///         quadratically and quartically convergent iterations that need
///         only add, mul, div and sqrt. In 127.128 the Borwein quartic
///         iteration reaches the format's floor, 36 correct digits, in two
///         steps from sqrt(2); Gauss-Legendre takes four. Both are views:
///         call them for free and watch the digits arrive.
contract PiIteration {
    int256 constant ONE = int256(1) << 128;

    /// Gauss-Legendre (Brent-Salamin, 1975): a, b -> their arithmetic and
    /// geometric means; pi ~ (a + b)^2 / (4 t). Digits double per step.
    function gaussLegendre(uint8 steps) external pure returns (int256 piApprox) {
        int256 a = ONE;
        int256 b = F.sqrt(ONE / 2);
        int256 t = ONE / 4;
        int256 p = 1;
        for (uint8 i; i < steps; i++) {
            int256 an = (a + b) / 2;
            b = F.sqrt(F.mul(a, b));
            int256 d = a - an;
            t -= p * F.mul(d, d);
            a = an;
            p *= 2;
        }
        int256 s = a + b;
        return F.div(F.mul(s, s), 4 * t);
    }

    /// Borwein brothers' quartic iteration (1985), built on Ramanujan's
    /// modular equations: y0 = sqrt(2) - 1, a0 = 6 - 4 sqrt(2), then
    ///   y' = (1 - (1 - y^4)^(1/4)) / (1 + (1 - y^4)^(1/4))
    ///   a' = a (1 + y')^4 - 2^(2k+3) y' (1 + y' + y'^2)
    /// and a -> 1 / pi. Digits quadruple per step; two steps reach 36 here.
    function borwein(uint8 steps) external pure returns (int256 piApprox) {
        int256 r2 = F.sqrt(2 * ONE);
        int256 y = r2 - ONE;
        int256 a = 6 * ONE - 4 * r2;
        for (uint8 k; k < steps; k++) {
            int256 y2 = F.mul(y, y);
            int256 f = F.sqrt(F.sqrt(ONE - F.mul(y2, y2)));   // (1 - y^4)^(1/4)
            y = F.div(ONE - f, ONE + f);
            int256 yp = ONE + y;
            int256 yp2 = F.mul(yp, yp);
            a = F.mul(a, F.mul(yp2, yp2)) - (int256(1) << (2 * k + 3)) * F.mul(y, ONE + y + F.mul(y, y));
        }
        return F.div(ONE, a);
    }
}

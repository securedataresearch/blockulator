// SPDX-License-Identifier: GPL-3.0-only
// Transcribed from primitivefinance/rmm-core @ 8d3ef9b, contracts/libraries/CumulativeNormalDistribution.sol
// (GPL-3.0-only), getCDF and getErrorFunction line for line, on ABDKMath64x64 (lib/abdk-libraries-solidity).
// Benchmark only: nothing in BL127, BL19 or BlockulatorWad imports it.
pragma solidity ^0.8.4;

import {ABDKMath64x64} from "../../lib/abdk-libraries-solidity/ABDKMath64x64.sol";

library RmmCDF {
    using ABDKMath64x64 for int128;

    int128 internal constant ONE_INT = 0x10000000000000000;
    int128 internal constant HALF_INT = 0x8000000000000000;
    int128 internal constant CDF0 = 0x53dd02a4f5ee2e46;
    int128 internal constant CDF1 = 0x413c831bb169f874;
    int128 internal constant CDF2 = -0x48d4c730f051a5fe;
    // 0x16a09e667f3bcc908 is sqrt(2) in 64.64. getCDF uses it both to scale z = x / sqrt(2), which is right, and as
    // the Abramowitz and Stegun coefficient a3 in getErrorFunction, where 1.421413741 belongs: kept as shipped.
    int128 internal constant CDF3 = 0x16a09e667f3bcc908;
    int128 internal constant CDF4 = -0x17401c57014c38f14;
    int128 internal constant CDF5 = 0x10fb844255a12d72e;

    function getCDF(int128 x) internal pure returns (int128) {
        int128 z = x.div(CDF3);
        int128 t = ONE_INT.div(ONE_INT.add(CDF0.mul(z.abs())));
        int128 erf = getErrorFunction(z, t);
        if (z < 0) {
            erf = erf.neg();
        }
        int128 result = (HALF_INT).mul(ONE_INT.add(erf));
        return result;
    }

    function getErrorFunction(int128 z, int128 t) internal pure returns (int128) {
        int128 step1 = t.mul(CDF3.add(t.mul(CDF4.add(t.mul(CDF5)))));
        int128 step2 = CDF1.add(t.mul(CDF2.add(step1)));
        int128 result = ONE_INT.sub(t.mul(step2.mul((z.mul(z).neg()).exp())));
        return result;
    }
}

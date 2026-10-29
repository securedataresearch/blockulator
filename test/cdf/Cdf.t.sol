// SPDX-License-Identifier: AGPL-3.0-only
// AGPL because it links solstat, which links solmate v7 (AGPL-3.0-only); see contracts/src/ladder/vendor/README.md.
pragma solidity ^0.8.24;

import {Test, console2} from "forge-std/Test.sol";
import {BL127Lib} from "../../contracts/src/bl127/BL127Lib.sol";
import {BL19Lib} from "../../contracts/src/bl19/BL19Lib.sol";
import {Gaussian} from "../../lib/solstat/src/Gaussian.sol";
import {BlackScholes} from "../../contracts/src/ladder/vendor/lyra/libraries/BlackScholes.sol";
import {RmmCDF} from "./CdfRmm.sol";

/// The normal CDF and erfc, every on-chain implementation measured the same way: each library's own code at
/// x = k/32, k = -192..192 (x in [-6, 6], exact in every representation here), the result's raw word and the gas of
/// the call inside its wrapper. scripts/cdf/cdf.py reads the lines, computes the truth and writes
/// docs/benchmarks/cdf.{json,md}. Each wrapper is an external call so a revert is a result, not a failed test.
///
///   CDF|<impl>|<op>|<k>|<raw or REVERT>|<gas>
contract CdfBL127 {
    function normCdf(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = BL127Lib.normCdf(x); g -= gasleft();
    }
    function erfc(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = BL127Lib.erfc(x); g -= gasleft();
    }
}

contract CdfBL19 {
    function normCdf(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = BL19Lib.normCdf(x); g -= gasleft();
    }
    function erfc(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = BL19Lib.erfc(x); g -= gasleft();
    }
}

/// solstat (primitivefinance/solstat, commit 80c603f, lib/solstat): Gaussian.cdf and Gaussian.erfc on WAD.
contract CdfSolstat {
    function normCdf(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = Gaussian.cdf(x); g -= gasleft();
    }
    function erfc(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = Gaussian.erfc(x); g -= gasleft();
    }
}

/// Lyra v1 (lyra-finance/lyra-protocol, commit ea9e36a, vendored, ISC): BlackScholes._stdNormalCDF on 1e27. A public library
/// function, so the call is a DELEGATECALL into the linked library, as deployed; its gas is in the figure. No erfc.
contract CdfLyra {
    function normCdf(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = int256(BlackScholes._stdNormalCDF(x)); g -= gasleft();
    }
    function erfc(int256) external pure returns (int256, uint256) { revert(); }
}

/// rmm-core (primitivefinance/rmm-core, commit 8d3ef9b, transcribed, GPL-3.0-only): getCDF on ABDK 64.64. No erfc.
contract CdfRmm {
    function normCdf(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = RmmCDF.getCDF(int128(x)); g -= gasleft();
    }
    function erfc(int256) external pure returns (int256, uint256) { revert(); }
}

interface ICdf {
    function normCdf(int256 x) external view returns (int256, uint256);
    function erfc(int256 x) external view returns (int256, uint256);
}

contract Cdf is Test {
    int256 internal constant K = 192; // x = k/32 for |k| <= K

    function emit_(string memory impl, string memory op, int256 k, bool ok, int256 raw, uint256 gas) internal pure {
        console2.log(string.concat("CDF|", impl, "|", op, "|", vm.toString(k), "|", ok ? vm.toString(raw) : "REVERT", "|", vm.toString(gas)));
    }

    function sweep(string memory impl, ICdf c, function(int256) internal pure returns (int256) enc) internal {
        sweep(impl, c, enc, true);
    }

    function sweep(string memory impl, ICdf c, function(int256) internal pure returns (int256) enc, bool withErfc) internal {
        for (int256 k = -K; k <= K; k++) {
            int256 x = enc(k);
            try c.normCdf(x) returns (int256 r, uint256 g) { emit_(impl, "normCdf", k, true, r, g); }
            catch { emit_(impl, "normCdf", k, false, 0, 0); }
            if (!withErfc) continue;
            try c.erfc(x) returns (int256 r, uint256 g) { emit_(impl, "erfc", k, true, r, g); }
            catch { emit_(impl, "erfc", k, false, 0, 0); }
        }
    }

    function bl127(int256 k) internal pure returns (int256) { return (k << 128) / 32; } // exact: 32 divides 2^128
    function wad(int256 k) internal pure returns (int256) { return k * 1e18 / 32; } // exact: 1e18 / 32 = 31.25e15, k * 1e18 divisible by 32
    function bl19(int256 k) internal pure returns (int256) { return BL19Lib.fromFixed18(wad(k)); } // exact: k/32 is dyadic
    function ray(int256 k) internal pure returns (int256) { return k * 1e27 / 32; } // exact: 1e27 / 32 = 3.125e25
    function abdk(int256 k) internal pure returns (int256) { return (k << 64) / 32; } // exact

    function test_cdf() public {
        sweep("bl127", ICdf(address(new CdfBL127())), bl127);
        sweep("bl19", ICdf(address(new CdfBL19())), bl19);
        sweep("solstat", ICdf(address(new CdfSolstat())), wad);
        sweep("lyra", ICdf(address(new CdfLyra())), ray, false);
        sweep("rmm", ICdf(address(new CdfRmm())), abdk, false);
    }
}

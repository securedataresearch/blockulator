// SPDX-License-Identifier: AGPL-3.0-only
// AGPL because it links solstat, which links solmate v7 (AGPL-3.0-only); see contracts/src/ladder/vendor/README.md.
pragma solidity ^0.8.24;

import {Test, console2} from "forge-std/Test.sol";
import {FP127Lib} from "../../contracts/src/fp127/FP127Lib.sol";
import {FP19Lib} from "../../contracts/src/fp19/FP19Lib.sol";
import {Gaussian} from "../../lib/solstat/src/Gaussian.sol";

/// The normal CDF and erfc, every on-chain implementation measured the same way: each library's own code at
/// x = k/32, k = -192..192 (x in [-6, 6], exact in every representation here), the result's raw word and the gas of
/// the call inside its wrapper. scripts/cdf/cdf.py reads the lines, computes the truth and writes
/// docs/benchmarks/cdf.{json,md}. Each wrapper is an external call so a revert is a result, not a failed test.
///
///   CDF|<impl>|<op>|<k>|<raw or REVERT>|<gas>
contract CdfFP127 {
    function normCdf(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = FP127Lib.normCdf(x); g -= gasleft();
    }
    function erfc(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = FP127Lib.erfc(x); g -= gasleft();
    }
}

contract CdfFP19 {
    function normCdf(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = FP19Lib.normCdf(x); g -= gasleft();
    }
    function erfc(int256 x) external view returns (int256 r, uint256 g) {
        g = gasleft(); r = FP19Lib.erfc(x); g -= gasleft();
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
        for (int256 k = -K; k <= K; k++) {
            int256 x = enc(k);
            try c.normCdf(x) returns (int256 r, uint256 g) { emit_(impl, "normCdf", k, true, r, g); }
            catch { emit_(impl, "normCdf", k, false, 0, 0); }
            try c.erfc(x) returns (int256 r, uint256 g) { emit_(impl, "erfc", k, true, r, g); }
            catch { emit_(impl, "erfc", k, false, 0, 0); }
        }
    }

    function fp127(int256 k) internal pure returns (int256) { return (k << 128) / 32; } // exact: 32 divides 2^128
    function wad(int256 k) internal pure returns (int256) { return k * 1e18 / 32; } // exact: 1e18 / 32 = 31.25e15, k * 1e18 divisible by 32
    function fp19(int256 k) internal pure returns (int256) { return FP19Lib.fromFixed18(wad(k)); } // exact: k/32 is dyadic

    function test_cdf() public {
        sweep("fp127", ICdf(address(new CdfFP127())), fp127);
        sweep("fp19", ICdf(address(new CdfFP19())), fp19);
        sweep("solstat", ICdf(address(new CdfSolstat())), wad);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {Precision} from "../fp127/Precision.t.sol";
import {Precision256} from "../fp256/Precision.t.sol";

/// @notice The committed precision vectors (test/fp127/vectors,
///         test/fp256/vectors) against the osaka objects: the same suites as
///         the shanghai build's, reading out/osaka/ and writing no report.
contract PrecisionOsaka127 is Precision {
    function _buildDir() internal pure override returns (string memory) { return "out/osaka/"; }
    function _out() internal pure override returns (string memory) { return ""; }
}

contract PrecisionOsaka256 is Precision256 {
    function _buildDir() internal pure override returns (string memory) { return "out/osaka/"; }
    function _out() internal pure override returns (string memory) { return ""; }
}

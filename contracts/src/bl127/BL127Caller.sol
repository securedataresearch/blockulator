// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IBL127} from "./IBL127.sol";

/// @title BL127Caller
/// @notice Thin harness around the deployed BL127 object. Every function is a
///         staticcall to the shared address; revert data is bubbled unchanged
///         so callers see the same custom errors the object raises.
/// @dev Use this when you want every contract on a chain to agree with one
///      deployed bytecode. Use BL127Lib when you want the math inlined.
contract BL127Caller {
    address public immutable bl127;

    error ZeroAddress();

    constructor(address bl127_) {
        if (bl127_ == address(0)) revert ZeroAddress();
        bl127 = bl127_;
    }

    function add(int256 a, int256 b) external view returns (int256) {
        return _call2(IBL127.add.selector, a, b);
    }

    function sub(int256 a, int256 b) external view returns (int256) {
        return _call2(IBL127.sub.selector, a, b);
    }

    function mul(int256 a, int256 b) external view returns (int256) {
        return _call2(IBL127.mul.selector, a, b);
    }

    function div(int256 a, int256 b) external view returns (int256) {
        return _call2(IBL127.div.selector, a, b);
    }

    function fromFixed18(int256 x) external view returns (int256) {
        return _call1(IBL127.fromFixed18.selector, x);
    }

    function toFixed18(int256 x) external view returns (int256) {
        return _call1(IBL127.toFixed18.selector, x);
    }

    function _call1(bytes4 sel, int256 x) internal view returns (int256 r) {
        (bool ok, bytes memory out) = bl127.staticcall(abi.encodeWithSelector(sel, x));
        if (!ok) _bubble(out);
        r = abi.decode(out, (int256));
    }

    function _call2(bytes4 sel, int256 a, int256 b) internal view returns (int256 r) {
        (bool ok, bytes memory out) = bl127.staticcall(abi.encodeWithSelector(sel, a, b));
        if (!ok) _bubble(out);
        r = abi.decode(out, (int256));
    }

    function _bubble(bytes memory data) internal pure {
        assembly ("memory-safe") {
            revert(add(data, 0x20), mload(data))
        }
    }
}

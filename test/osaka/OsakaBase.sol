// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import "forge-std/Test.sol";
import {LibUserOsaka127} from "./gen/LibUserOsaka127.sol";
import {LibUserOsaka256} from "./gen/LibUserOsaka256.sol";

/// @notice The two builds side by side, for the osaka suites (make test-osaka,
///         make bench-osaka; [profile.osaka], evm osaka). Every deployed object
///         is created twice, from out/<Object>.yul (shanghai, make build) and
///         out/osaka/<Object>.yul (osaka, make build-osaka), and each library's
///         osaka inline library sits behind the generated LibUserOsaka*
///         wrapper. The exports come from each library's ops.json (name,
///         selector, arity, object), so nothing here names an op or an object.
abstract contract OsakaBase is Test {
    struct Op {
        string name;
        bytes4 sel;
        uint256 arity;
        address sh;    // the shanghai object that carries it
        address os;    // the osaka object
    }

    /// The two libraries: 0 is FP127, 1 is FP256.
    Op[][2] internal ops;
    address[2] internal libOsaka;

    mapping(bytes32 => address) internal deployed;

    uint256 internal constant BIAS = 0x3ffff;
    uint256 internal constant FRAC = (uint256(1) << 236) - 1;
    uint256 internal constant SIGN = uint256(1) << 255;
    uint256 internal constant ONE127 = uint256(1) << 128;
    uint256 internal constant ONE256 = BIAS << 236;

    function setUp() public virtual {
        libOsaka[0] = address(new LibUserOsaka127());
        libOsaka[1] = address(new LibUserOsaka256());
        _load(0, "contracts/src/fp127/ops.json", "FP127");
        _load(1, "contracts/src/fp256/ops.json", "FP256");
    }

    function _load(uint256 lib, string memory path, string memory single) internal {
        string memory json = vm.readFile(path);
        for (uint256 i; vm.keyExistsJson(json, _at(i, "")); i++) {
            string memory o = vm.keyExistsJson(json, _at(i, ".object")) ? vm.parseJsonString(json, _at(i, ".object")) : single;
            ops[lib].push(Op(vm.parseJsonString(json, _at(i, ".name")),
                bytes4(vm.parseBytes32(_pad(vm.parseJsonString(json, _at(i, ".selector"))))),
                vm.parseJsonStringArray(json, _at(i, ".inputs")).length,
                _object(string.concat("out/", o, ".yul/", o, ".json")),
                _object(string.concat("out/osaka/", o, ".yul/", o, ".json"))));
        }
    }

    function _at(uint256 i, string memory key) internal pure returns (string memory) {
        return string.concat(".ops[", vm.toString(i), "]", key);
    }

    /// "0x12345678" -> a bytes32 string the parser takes
    function _pad(string memory s) internal pure returns (string memory) {
        return string.concat(s, "00000000000000000000000000000000000000000000000000000000");
    }

    function _object(string memory artifact) internal returns (address d) {
        bytes32 k = keccak256(bytes(artifact));
        d = deployed[k];
        if (d != address(0)) return d;
        bytes memory initCode = vm.parseJsonBytes(vm.readFile(artifact), ".bytecode.object");
        assembly ("memory-safe") {
            d := create(0, add(initCode, 0x20), mload(initCode))
        }
        require(d != address(0), string.concat("deploy failed: ", artifact));
        deployed[k] = d;
    }

    function _data(Op memory op, uint256 a, uint256 b, uint256 c) internal pure returns (bytes memory) {
        if (op.arity == 1) return abi.encodePacked(op.sel, a);
        if (op.arity == 2) return abi.encodePacked(op.sel, a, b);
        return abi.encodePacked(op.sel, a, b, c);
    }

    function _msb(uint256 x) internal pure returns (uint256 r) {
        while (x > 1) { x >>= 1; r++; }
    }

    /// One argument from the seed r in the given mode (0..7), for library lib.
    function _shape(uint256 lib, uint256 r, uint256 mode) internal pure returns (uint256 w) {
        unchecked {
        uint256 k = r >> 248;
        uint256 r2 = uint256(keccak256(abi.encode(r)));
        bool neg = r2 & 1 == 1;
        mode %= 8;
        if (mode == 0) return r;
        if (mode == 1) w = r >> k;                                    // tiny
        else if (mode == 2) w = (uint256(1) << k) + ((r2 >> 8) % 9) - 4;  // 2^k + [-4, 4]
        else if (mode == 3) w = (uint256(1) << k) - 1;                // all ones
        else if (lib == 0) {
            if (mode == 4) w = uint256(int256(r) >> (64 + k % 190));           // every scale
            else if (mode == 5) w = ONE127 + uint256(int256(r) >> (100 + k % 150)); // near one
            else if (mode == 6) w = uint256((int256(k % 64) - 32) << 128);     // small integers
            else w = r & ((uint256(1) << k) - 1);                              // k random bits
        } else {
            uint256 e;
            uint256 f = r & FRAC;
            if (mode == 4) e = BIAS + k - 128;                                  // near one
            else if (mode == 5) e = k % 2 == 0 ? k >> 3 : 0x7ffff - (k >> 3);  // the exponent's ends
            else if (mode == 6) {                                               // small integers
                uint256 n = k % 64 + 1;
                uint256 m = _msb(n);
                e = BIAS + m;
                f = (n << (236 - m)) & FRAC;
            } else {                                                            // 2^j, a few low bits
                e = BIAS + k - 128;
                f = r2 >> 253;
            }
            w = (e << 236) | f;
            return neg ? w ^ SIGN : w;
        }
        if (neg) w = 0 - w;
        }
    }
}

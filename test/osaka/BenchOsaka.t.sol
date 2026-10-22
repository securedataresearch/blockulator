// SPDX-License-Identifier: MIT
pragma solidity ^0.8.31;

import {OsakaBase} from "./OsakaBase.sol";
import {console} from "forge-std/console.sol";

/// @title BenchOsaka
/// @notice Gas of every export, osaka object against shanghai object, on the
///         same inputs and the same (osaka) EVM, so the difference is the code
///         alone. The inputs are the op's committed precision vectors
///         (test/<lib>/vectors/<op>.json), or, for an op without vectors, 64
///         shaped inputs near one; an input counts only where both builds
///         succeed. One line per op:
///         OSAKA|<lib>|<object>|<op>|<n>|<shanghai median>|<osaka median>|<shanghai mean>|<osaka mean>
///         make bench-osaka pipes them to scripts/fp127/bench_osaka.py.
contract BenchOsaka is OsakaBase {
    string[2] internal LIBS = ["fp127", "fp256"];

    /// The call alone: no return data copied, no memory grown, so neither
    /// build pays for the other's allocations.
    function _gas(address t, bytes memory d) internal view returns (bool ok, uint256 g) {
        assembly ("memory-safe") {
            let g0 := gas()
            ok := staticcall(gas(), t, add(d, 0x20), mload(d), 0, 0)
            g := sub(g0, gas())
        }
    }

    function _median(uint256[] memory v, uint256 n) internal pure returns (uint256) {
        for (uint256 i = 1; i < n; i++) {
            uint256 x = v[i];
            uint256 j = i;
            while (j > 0 && v[j - 1] > x) { v[j] = v[j - 1]; j--; }
            v[j] = x;
        }
        return n == 0 ? 0 : v[n / 2];
    }

    function _inputs(uint256 lib, Op memory op) internal view returns (uint256[][3] memory in_, uint256 n) {
        string memory path = string.concat("test/", LIBS[lib], "/vectors/", op.name, ".json");
        if (vm.isFile(path)) {
            string memory json = vm.readFile(path);
            for (uint256 a; a < op.arity; a++) {
                string[] memory s = vm.parseJsonStringArray(json, string.concat(".in", vm.toString(a)));
                in_[a] = new uint256[](s.length);
                for (uint256 i; i < s.length; i++) in_[a][i] = uint256(vm.parseBytes32(s[i]));
                n = s.length;
            }
        } else {
            n = 64;
            for (uint256 a; a < op.arity; a++) {
                in_[a] = new uint256[](n);
                for (uint256 i; i < n; i++) {
                    in_[a][i] = _shape(lib, uint256(keccak256(abi.encode(op.name, a, i))), 4);
                }
            }
        }
    }

    function _objectName(uint256 lib, Op memory op) internal view returns (string memory) {
        string memory json = vm.readFile(lib == 0 ? "contracts/src/fp127/ops.json" : "contracts/src/fp256/ops.json");
        for (uint256 i; vm.keyExistsJson(json, _at(i, "")); i++) {
            if (keccak256(bytes(vm.parseJsonString(json, _at(i, ".name")))) != keccak256(bytes(op.name))) continue;
            return vm.keyExistsJson(json, _at(i, ".object")) ? vm.parseJsonString(json, _at(i, ".object")) : "FP127";
        }
        return "?";
    }

    struct Row { uint256 n; uint256 shMed; uint256 osMed; uint256 shMean; uint256 osMean; }

    function _measure(uint256 lib, Op memory op) internal view returns (Row memory r) {
        (uint256[][3] memory in_, uint256 n) = _inputs(lib, op);
        uint256[] memory gs = new uint256[](n);
        uint256[] memory go = new uint256[](n);
        for (uint256 k; k < n; k++) {
            bytes memory d = _data(op, in_[0][k], op.arity > 1 ? in_[1][k] : 0, op.arity > 2 ? in_[2][k] : 0);
            (bool ok1, uint256 g1) = _gas(op.sh, d);
            (bool ok2, uint256 g2) = _gas(op.os, d);
            assertEq(ok1, ok2, op.name);
            if (!ok1) continue;
            gs[r.n] = g1;
            go[r.n] = g2;
            r.shMean += g1;
            r.osMean += g2;
            r.n++;
        }
        if (r.n > 0) {
            r.shMean /= r.n;
            r.osMean /= r.n;
        }
        r.shMed = _median(gs, r.n);
        r.osMed = _median(go, r.n);
    }

    function test_bench() public view {
        for (uint256 lib; lib < 2; lib++) {
            for (uint256 i; i < ops[lib].length; i++) {
                Op memory op = ops[lib][i];
                // warm both accounts, as every later call is
                _gas(op.sh, "");
                _gas(op.os, "");
                Row memory r = _measure(lib, op);
                console.log(string.concat("OSAKA|", LIBS[lib], "|", _objectName(lib, op), "|", op.name, "|",
                    vm.toString(r.n), "|", vm.toString(r.shMed), "|", vm.toString(r.osMed), "|",
                    vm.toString(r.shMean), "|", vm.toString(r.osMean)));
            }
        }
    }
}

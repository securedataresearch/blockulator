+++
title = "FP127"
description = "Signed 127.128 fixed point. One int256, 128 fractional bits (38 digits at 1), 53 ops, every transcendental the nearest word (pow near 2⁹⁰ excepted). One Yul source, two forms: a deployed object and an inline library."

[extra]
group = "library"
# anchors of the integration section, now on /library/integrating/: page.html forwards them
moved = ["rule-1-bunni-v2", "rule-2-resupply", "rule-2-balancer-v2", "rule-2-balancer-v1-the-counter-example", "the-edge-ops", "divide-last", "keep-an-index-as-its-logarithm"]
moved_to = "/library/integrating/"
+++

Both forms are generated from one file and fuzzed equal across the full `int256` domain, reverts included.

## Encoding

`value × 2^128` in an `int256`, two's complement. `ONE` is `2^128`. Range ±1.7 × 10<sup>38</sup>, 128 fractional bits: 38 digits at 1, 32 at 10<sup>−6</sup>, 8 at 10<sup>−30</sup>. Every op takes and returns this one type. `fromFixed18` and `toFixed18` convert to and from WAD.

{{ <wordstrip format="fp127,wad" /> }}

Errors: `Overflow()`, `DivisionByZero()`, `OutOfRange()`. Nothing wraps.

## Deployed form

{{ <deployment /> }}

No storage, no owner, no upgrade path. A new version is a new salt and a new address. The address above is v6 (53 ops, Blockulator 2.2): `pi` is now the constant `FP127Lib.PI` (π · 2<sup>128</sup> to the nearest integer) and `gcd` is gone, and every other op returns the same word as v5 for less gas. v6 is an evmVersion osaka build and needs the CLZ opcode (EIP-7939): it runs on Ethereum, Sepolia and the other chains with CLZ, not on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list]({{ config.extra.repo }}/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)). v5 (Blockulator 2.1, `0x619176d72D7a12390F8970802943D344c0fd3fE2`) added the directed `mulUp`, `mulDown`, `divUp`, `divDown`, `toFixed18Up` and `toFixed18Down` and rounded every transcendental to the nearest word. v1 to v5 stay deployed at the addresses in the record.

`sqrt(2)` from the command line:

```sh
cast call 0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4 "sqrt(int256)(int256)" \
  680564733841876926926749214863536422912 \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
# 481231938336009023090067544955250113854
python3 -c "print(481231938336009023090067544955250113854 / 2**128)"
# 1.4142135623730951
```

From Solidity:

```solidity
import {IFP127} from "fp127/IFP127.sol";

contract StaticcallExample {
    IFP127 public constant FP127 = IFP127(0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4);
    int256 internal constant ONE = int256(1) << 128;

    function accrue(int256 principalWad, int256 rateWad, uint256 steps)
        external view returns (int256 balanceWad)
    {
        int256 b = FP127.fromFixed18(principalWad);
        int256 growth = FP127.add(ONE, FP127.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = FP127.mul(b, growth);
        }
        return FP127.toFixed18(b);
    }
}
```

## Inline form

`FP127Lib.sol`: the same Yul in `memory-safe` assembly, one `internal pure` function per op. No external call: about 570 gas cheaper than the `staticcall` on `add`, 620 on `mul` and 610 on `sqrt`. On `exp`, `exp2`, `exp10`, `sinh`, `cosh` and both Lambert W branches the deployed object is cheaper, by 50 to 620 gas (medians on typical inputs in [`gas.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/gas.md)).

Compile it with `via_ir = true` (in `foundry.toml`): solc's legacy pipeline leaves the heavy ops 5–14% dearer than the same Yul in the object (net of its call), and through the IR they come within about −7% to +3% of it, `mul` 263 → 181 and `ln` 1,886 → 1,625 gas on typical inputs; the build takes about 5.5× as long ([`profile.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/profile.md)).

Install it one of three ways; the import path is the same in each:

```sh
# Foundry, from git
forge install securedataresearch/blockulator
echo "@blockulator/contracts/=lib/blockulator/contracts/src/" >> remappings.txt

# npm, yarn or pnpm (Hardhat needs no remapping; Foundry reading node_modules needs this one)
npm install @blockulator/contracts
echo "@blockulator/contracts/=node_modules/@blockulator/contracts/" >> remappings.txt

# Soldeer
forge soldeer install blockulator~<version>
echo "@blockulator/contracts/=dependencies/blockulator-<version>/" >> remappings.txt
```

```solidity
import {FP127Lib} from "@blockulator/contracts/fp127/FP127Lib.sol";

contract CompoundExample {
    function accrue(int256 principalWad, int256 rateWad, uint256 steps)
        external pure returns (int256 balanceWad)
    {
        int256 b = FP127Lib.fromFixed18(principalWad);
        int256 growth = FP127Lib.add(FP127Lib.ONE, FP127Lib.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = FP127Lib.mul(b, growth);
        }
        return FP127Lib.toFixed18(b);
    }
}
```

Both examples are compiled and tested in `test/examples/` against the [ladder's](/results/ladder/#compound) compound scenario.

## Integrating

Two rules, each from the replay of a real exploit. The [integration page](/library/integrating/) has the replays, the code in both formats and the edge-op tables.

1. **Store the state in the format.** Keep a running balance, index or accumulator as an FP127 word, and round to token units only on the way out. In Bunni v2's replay this alone turns a balance drained from 28 wei to 4 into 35.6 wei, within 10<sup>−37</sup> of exact.
2. **Round toward the protocol at the token edge.** Floor what you pay out and ceil what you take in: `toFixed18Down` and `toFixed18Up`, `mulDown` and `mulUp`, `divDown` and `divUp`. Under this rule Resupply's borrow against 1 wei of collateral reverts, and Balancer V2's charge matches the exact one on every call.

## The ops

{{ <optable /> }}

## For agents

[`/.well-known/agent.json`](/.well-known/agent.json), [`/llms.txt`](/llms.txt), ABI at [`/data/abi.json`](/data/abi.json). Reads are `eth_call`: no gas, no wallet.

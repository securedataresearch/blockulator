+++
title = "BL127"
description = "Signed fixed point with 128 bits after the point: 38 correct digits at 1, in one int256. 53 ops, every one correctly rounded. Inline it or call the deployed contracts."

[extra]
group = "library"
# anchors of the integration section, now on /library/integrating/: page.html forwards them
moved = ["rule-1-bunni-v2", "rule-2-resupply", "rule-2-balancer-v2", "rule-2-balancer-v1-the-counter-example", "the-edge-ops", "divide-last", "keep-an-index-as-its-logarithm"]
moved_to = "/library/integrating/"
+++

BL127 is a number format and a math library for Solidity. A value is stored as `value × 2^128` in an `int256`, so it keeps 38 correct digits at 1 where WAD keeps 18, and the same Yul source ships two ways: a library you inline, and a deployed contract you call. The two are fuzzed equal on every `int256`, reverts included.

## Install

The import path is the same however you install it:

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
import {BL127Lib} from "@blockulator/contracts/bl127/BL127Lib.sol";

contract CompoundExample {
    function accrue(int256 principalWad, int256 rateWad, uint256 steps)
        external pure returns (int256 balanceWad)
    {
        int256 b = BL127Lib.fromFixed18(principalWad);
        int256 growth = BL127Lib.add(BL127Lib.ONE, BL127Lib.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = BL127Lib.mul(b, growth);
        }
        return BL127Lib.toFixed18(b);
    }
}
```

This example is compiled and tested in `test/examples/` against the [ladder's](/results/ladder/#compound) compound scenario. Compile with `via_ir = true` in `foundry.toml`: through the IR the inline ops come within a few percent of the deployed contract's gas, and on the legacy pipeline the heavy ops cost 5–14% more ([`profile.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/profile.md)).

## Typed API

`BL127Type.sol` is opt-in: `type BL127 is int256`, with `+ - * /`, unary `-` and `< > <= >= == !=` bound to the library, and every other op attached (`x.exp()`, `a.mulUp(b)`). `bl127FromWad` and `toWadDown` / `toWadUp` convert unsigned WADs, `bl127FromInt` integers, and `ONE` and `PI` are typed constants. Each function only re-types its arguments, so the words and reverts are `BL127Lib`'s, checked under fuzzing in `test/typed/`. Through the IR every op costs the same gas as the raw call; under the legacy pipeline the wrapper is one more internal call, 37 to 114 gas.

```solidity
import {BL127, ONE, PI, bl127FromWad} from "bl127/BL127Type.sol";

BL127 b = bl127FromWad(1.5e18) * ONE.exp();  // 1.5e; * is BL127Lib.mul
BL127 r = (b - ONE).ln() / PI + -ONE;        // operators and attached ops
bool inside = r >= -ONE && r <= ONE;
uint256 paid = b.toWadDown();                // 4077422742688567853, floored
```

## The format

The range is ±1.7 × 10<sup>38</sup>. With 128 bits after the point, BL127 keeps 38 digits at 1, 32 at 10<sup>−6</sup> and 8 at 10<sup>−30</sup>. `ONE` is `2^128`, every op takes and returns this one type, and `fromFixed18` and `toFixed18` convert to and from WAD.

{{ <wordstrip format="bl127,wad" /> }}

Errors are `Overflow()`, `DivisionByZero()` and `OutOfRange()`. Nothing wraps.

## The deployed contracts

Calling the deployed contract costs one `staticcall`, about 600 gas more than inlining on simple ops like `add` and `mul`. On the heavy ops (`exp`, `exp2`, `exp10`, `sinh`, `cosh` and both Lambert W branches) it is cheaper than inlining, by 50 to 620 gas ([`gas.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/gas.md)). It is also the way to use BL127 from an `eth_call`, where gas is free.

{{ <deployment /> }}

BL127 v9 (Blockulator 3.0) is five contracts from one source, one idea each. The record above is the BL127 contract's; [`BL127.md`](/contracts/deployments/BL127.md) has all five.

| contract | what it holds | address | ops |
|---|---|---|---|
| BL127 | the number | `0x0DF738d125677550a80A46BaF254386C66f96E0d` | `add` `sub` `mul` `div` `inv` `sqrt` `cbrt` `hypot` `gavg`; `neg` `abs` `sign`; `min` `max` `clamp`; `floor` `ceil` `round` `frac`; `avg` `dist` `zeroFloorSub` `lerp`; `factorial`; `mulDown` `mulUp` `divDown` `divUp`; `fromFixed18` `toFixed18` `toFixed18Down` `toFixed18Up` |
| BL127E | the elementary functions, on one exp/log kernel | `0xc16F4C45B78D90A4D4C030cABF4f2A34c1Fb0808` | `exp` `exp2` `exp10` `expm1` `ln` `log2` `log10` `log2Up` `log1p` `pow` `powu` `compound` |
| BL127H | the hyperbolic functions | `0xf2F99947aD1cC370bD5388a2997A5E4963a0B27B` | `sinh` `cosh` `tanh` `atanh` |
| BL127N | the normal distribution | `0xAA7Cd9635aE8630379636F533f23DBf2C193d296` | `erf` `erfc` `normCdf` |
| BL127S | Lambert W | `0xB9C2583a7Ad2251444DC7752658B6C1107C25036` | `lambertW0` `lambertWm1` |

Each object has its own interface (`IBL127.sol`, `IBL127E.sol`, `IBL127H.sol`, `IBL127N.sol`, `IBL127S.sol`) and ABI; [`ops.json`](/data/ops.json) names each op's object. The inline library holds all 53 ops.

They have no storage, no owner and no upgrade path: a new version gets a new salt and a new address, and v1 to v8 (one contract each) stay deployed at the addresses in the record. It is built for evmVersion osaka and needs the CLZ opcode (EIP-7939), so it runs on Ethereum, Sepolia and the other chains with CLZ, but not on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list]({{ config.extra.repo }}/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)). What changed in each version is in the [changelog]({{ config.extra.repo }}/blob/master/CHANGELOG.md).

`sqrt(2)` from the command line:

```sh
cast call 0x0DF738d125677550a80A46BaF254386C66f96E0d "sqrt(int256)(int256)" \
  680564733841876926926749214863536422912 \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com
# 481231938336009023090067544955250113854
python3 -c "print(481231938336009023090067544955250113854 / 2**128)"
# 1.4142135623730951
```

From Solidity:

```solidity
import {IBL127} from "bl127/IBL127.sol";

contract StaticcallExample {
    IBL127 public constant BL127 = IBL127(0x0DF738d125677550a80A46BaF254386C66f96E0d);
    int256 internal constant ONE = int256(1) << 128;

    function accrue(int256 principalWad, int256 rateWad, uint256 steps)
        external view returns (int256 balanceWad)
    {
        int256 b = BL127.fromFixed18(principalWad);
        int256 growth = BL127.add(ONE, BL127.fromFixed18(rateWad));
        for (uint256 i = 0; i < steps; i++) {
            b = BL127.mul(b, growth);
        }
        return BL127.toFixed18(b);
    }
}
```

## Integrating

Two rules, each from the replay of a real exploit. The [integration page](/library/integrating/) has the replays, the code in both formats and the edge-op tables.

1. **Store the state in the format.** Keep a running balance, index or accumulator as an BL127 word, and round to token units only on the way out. In Bunni v2's replay this alone turns a balance drained from 28 wei to 4 into 35.6 wei, within 10<sup>−37</sup> of exact.
2. **Round toward the protocol at the token edge.** Floor what you pay out and ceil what you take in: `toFixed18Down` and `toFixed18Up`, `mulDown` and `mulUp`, `divDown` and `divUp`. Under this rule Resupply's borrow against 1 wei of collateral reverts, and Balancer V2's charge matches the exact one on every call.

## The ops

Each op's worst-case precision against its gas. Hover a dot for the op.

{{ <plot chart="libops" arg="bl127" label="Correct bits on the worst input against median gas per call for each op; the numbers are in the table below." /> }}

{{ <optable /> }}

## For agents

[`/.well-known/agent.json`](/.well-known/agent.json), [`/llms.txt`](/llms.txt), ABI at [`/data/abi.json`](/data/abi.json). Reads are `eth_call`: no gas, no wallet.

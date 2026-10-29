+++
title = "BL19"
description = "A 256-bit binary float with about 71 digits at any size, every op correctly rounded."
path = "library/bl19"
aliases = ["/float/", "/library/fp256/", "/library/fp19/"]

[extra]
group = "library"
# anchors of the integration section, now on /library/integrating/: page.html forwards them
moved = ["rule-1-bunni-v2", "rule-2-resupply", "rule-2-balancer-v2", "rule-2-balancer-v1-the-counter-example", "the-edge-ops", "divide-last", "keep-an-index-as-its-logarithm"]
moved_to = "/library/integrating/"
+++

BL19 is a float, so its digits move with the value: about 71 at any size, where BL127 keeps 38 at 1 and 8 at 10<sup>−30</sup>. Every op is correctly rounded: none of 360,590 random inputs was misrounded ([sweep]({{ config.extra.repo }}/blob/master/docs/benchmarks/sweep.md)).

## The format

A value is one `int256`: the sign in bit 255, a 19-bit exponent (bias 262,143) and a 236-bit fraction with an implicit leading one. That is 237 significant bits, about 71 digits, from 10<sup>−78,913</sup> to 10<sup>78,913</sup>.

{{ <wordstrip format="bl19" /> }}

`value = (-1)^s (1 + F / 2^236) 2^(E - 262143)`, with s the sign, E the exponent and F the fraction.

There is no NaN, infinity, subnormal or negative zero. Zero is all zero bits, any other value with exponent 0 reverts with `OutOfRange`, and two values are equal exactly when their bits are. Each op rounds once, ties away from zero. Overflow reverts with `Overflow`, underflow rounds to zero, and division by zero reverts with `DivisionByZero`. `ONE` is `0x3ffff << 236`.

| | digits | range | add | mul | div | exp | ln | pow | sqrt |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| **BL19** | **71** | 10<sup>±78,913</sup> | {{ <gas op="add" lib="bl19" form="lib" /> }} | {{ <gas op="mul" lib="bl19" form="lib" /> }} | {{ <gas op="div" lib="bl19" form="lib" /> }} | {{ <gas op="exp" lib="bl19" form="lib" /> }} | {{ <gas op="ln" lib="bl19" form="lib" /> }} | {{ <gas op="pow" lib="bl19" form="lib" /> }} | {{ <gas op="sqrt" lib="bl19" form="lib" /> }} |
| BL127 | 38 at 1 | 2<sup>−128</sup> to 2<sup>127</sup> (±1.7 × 10<sup>38</sup>) | {{ <gas op="add" lib="bl19" form="bl127lib" /> }} | {{ <gas op="mul" lib="bl19" form="bl127lib" /> }} | {{ <gas op="div" lib="bl19" form="bl127lib" /> }} | {{ <gas op="exp" lib="bl19" form="bl127lib" /> }} | {{ <gas op="ln" lib="bl19" form="bl127lib" /> }} | {{ <gas op="pow" lib="bl19" form="bl127lib" /> }} | {{ <gas op="sqrt" lib="bl19" form="bl127lib" /> }} |
| ABDKMathQuad | 34 | 10<sup>±4,932</sup> | {{ <gas op="add" lib="bl19" form="quad" /> }} | {{ <gas op="mul" lib="bl19" form="quad" /> }} | {{ <gas op="div" lib="bl19" form="quad" /> }} | {{ <gas op="exp" lib="bl19" form="quad" /> }} | {{ <gas op="ln" lib="bl19" form="quad" /> }} | {{ <gas op="pow" lib="bl19" form="quad" /> }} | {{ <gas op="sqrt" lib="bl19" form="quad" /> }} |

Inline library, median gas per call on the same inputs ([full table](#gas-against-bl127-and-quad)). BL19 carries twice binary128's digits and costs less than Quad on every op here but `sqrt`. BL127 costs less than BL19 on every op here, with fewer digits.

## The deployed contracts

{{ <deployment lib="bl19" /> }}

BL19 v6 (Blockulator 3.0) is five contracts from one source. The record above is the BL19 contract's; [`BL19.md`](/contracts/deployments/BL19.md) has all five.

| contract | what it holds | address | ops |
|---|---|---|---|
| BL19 | the number | `0x94d9d43D6202827429a8058959eeCf6d232b8729` | `add` `sub` `mul` `div` `inv` `sqrt` `cbrt` `hypot` `gavg`; `neg` `abs` `sign`; `cmp` `lt` `eq` `min` `max` `clamp`; `floor` `ceil` `round` `frac`; `avg` `dist` `zeroFloorSub` `lerp`; `factorial`; `mulDown` `mulUp` `divDown` `divUp`; every conversion |
| BL19E | the elementary functions, on one exp/log kernel | `0x8e5eE786bDD7c35a2867Fd329441d0BD0fB61092` | `exp` `exp2` `exp10` `expm1` `ln` `log2` `log10` `log2Up` `log1p` `pow` `powu` `compound` |
| BL19H | the hyperbolic functions | `0xF059611C1c42543DE6EE82353Eb082Fd8999081f` | `sinh` `cosh` `tanh` `atanh` |
| BL19N | the normal distribution | `0xCe9F09D646B37a9100F05ED1FFD14E9f43180214` | `erf` `erfc` `normCdf` |
| BL19S | Lambert W | `0xf74ba90535224870830e6e89D2b328d4cc09DE48` | `lambertW0` `lambertWm1` |

BL19H has its own copy of the exp/log kernel because BL19E with the hyperbolics was over the 24,576-byte limit, and BL19N holds the erf family's fitted polynomial. `factorial` is a table in the core, for n ≤ 170. `pi` is the constant `BL19Lib.PI`, and `gcd` was removed in v5. The inline library holds all 65 ops.

The contracts need the CLZ opcode (EIP-7939, evmVersion osaka), so they do not run on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list]({{ config.extra.repo }}/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)). BL19 v5 (Blockulator 2.2: BL19, BL19E, BL19H and BL19S), v4 (Blockulator 2.1: BL19, BL19X, BL19X2 and BL19X3) and v3 (Blockulator 2.0) stay live at the addresses in the record.

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

Compile `BL19Lib.sol` with `via_ir = true` in `foundry.toml`. Through the IR, `add` drops from 677 to 545 gas and `exp` from 3,277 to 2,848 ([`profile.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/profile.md)).

```solidity
import {BL19Lib} from "@blockulator/contracts/bl19/BL19Lib.sol";

// a per-second rate over a year, with the rate itself held to 71 digits
int256 r = BL19Lib.div(BL19Lib.fromFixed18(0.05e18), BL19Lib.fromUint(31536000));
int256 g = BL19Lib.compound(r, 31536000);   // (1 + r)^n without ever rounding 1 + r
int256 balanceWad = BL19Lib.toFixed18(BL19Lib.mul(BL19Lib.fromFixed18(principalWad), g));
```

`fromFixed18` and `toFixed18` convert to and from WAD. `fromBL127` is exact below 2<sup>109</sup> and rounds once above; `toBL127` rounds to the nearest 2<sup>−128</sup>.

## Typed API

`BL19Type.sol` is opt-in: `type BL19 is int256`, with arithmetic and comparison operators bound to the library and every other op attached (`x.exp()`, `a.mulUp(b)`). `bl19FromWad`, `bl19FromInt` and `bl19FromUint` convert in, `toWadDown`, `toUintUp` and the rest convert out, `toBL127` and `toBL19` cross to BL127's type, and `ONE` and `PI` are typed constants. The wrapper only re-types, so results and reverts are `BL19Lib`'s, and through the IR the gas is the same.

```solidity
import {BL19, ONE, bl19FromWad, bl19FromInt} from "bl19/BL19Type.sol";
import {BL127} from "bl127/BL127Type.sol";

BL19 b = bl19FromWad(1.5e18) * ONE.exp();  // 1.5e; * is BL19Lib.mul
bool between = b > bl19FromInt(4) && b < bl19FromInt(5);
uint256 charged = b.toUintUp();              // 5, ceiled
BL127 n = b.toBL127();                       // the nearest BL127 value
```

## Integrating

Two rules, each from the replay of a real exploit ([integrating](/library/integrating/) has the replays and code).

1. **Store the state in the format.** Keep a running balance, index or accumulator as an BL19 value, and round to token units only on the way out. In Bunni v2's replay this keeps a balance the attack drained from 28 wei to 4 at 35.6 wei, as exact arithmetic does.
2. **Round toward the protocol at the token edge.** Round down what you pay out and round up what you take in: `toUintDown` and `toUintUp`, `toFixed18Down` and `toFixed18Up`, `mulDown` and `mulUp`, `divDown` and `divUp`. Under this rule Resupply's borrow against 1 wei of collateral reverts.

## The ops

Each op's worst-case precision against its gas. Hover a dot for the op.

{{ <plot chart="libops" arg="bl19" label="Correct bits on the worst input against median gas per call for each op; the numbers are in the table below." /> }}

{{ <optable lib="bl19" /> }}

### Gas against BL127 and Quad

{{ <gastable repo={config.extra.repo} lib="bl19" /> }}

The source is `contracts/src/bl19/BL19.yul.src`; the deployed contracts and the inline library are fuzzed equal across all of `int256`. Full reference: [`contracts/src/bl19/README.md`]({{ config.extra.repo }}/blob/master/contracts/src/bl19/README.md).

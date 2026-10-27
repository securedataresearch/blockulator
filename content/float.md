+++
title = "FP19"
description = "A 256-bit binary float with about 71 digits at any size, every op correctly rounded."
path = "library/fp19"
aliases = ["/float/", "/library/fp256/"]

[extra]
group = "library"
# anchors of the integration section, now on /library/integrating/: page.html forwards them
moved = ["rule-1-bunni-v2", "rule-2-resupply", "rule-2-balancer-v2", "rule-2-balancer-v1-the-counter-example", "the-edge-ops", "divide-last", "keep-an-index-as-its-logarithm"]
moved_to = "/library/integrating/"
+++

FP19 is a float, so its digits move with the value: about 71 at any size, where FP127 keeps 38 at 1 and 8 at 10<sup>−30</sup>. Every op is correctly rounded: none of 360,590 random inputs was misrounded ([sweep]({{ config.extra.repo }}/blob/master/docs/benchmarks/sweep.md)).

## The format

A value is one `int256`: the sign in bit 255, a 19-bit exponent (bias 262,143) and a 236-bit fraction with an implicit leading one. That is 237 significant bits, about 71 digits, from 10<sup>−78,913</sup> to 10<sup>78,913</sup>.

{{ <wordstrip format="fp19" /> }}

`value = (-1)^s (1 + F / 2^236) 2^(E - 262143)`, with s the sign, E the exponent and F the fraction.

There is no NaN, infinity, subnormal or negative zero. Zero is all zero bits, any other value with exponent 0 reverts with `OutOfRange`, and two values are equal exactly when their bits are. Each op rounds once, ties away from zero. Overflow reverts with `Overflow`, underflow rounds to zero, and division by zero reverts with `DivisionByZero`. `ONE` is `0x3ffff << 236`.

| | digits | range | add | mul | div | exp | ln | pow | sqrt |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| **FP19** | **71** | 10<sup>±78,913</sup> | {{ <gas op="add" lib="fp19" form="lib" /> }} | {{ <gas op="mul" lib="fp19" form="lib" /> }} | {{ <gas op="div" lib="fp19" form="lib" /> }} | {{ <gas op="exp" lib="fp19" form="lib" /> }} | {{ <gas op="ln" lib="fp19" form="lib" /> }} | {{ <gas op="pow" lib="fp19" form="lib" /> }} | {{ <gas op="sqrt" lib="fp19" form="lib" /> }} |
| FP127 | 38 at 1 | 2<sup>−128</sup> to 2<sup>127</sup> (±1.7 × 10<sup>38</sup>) | {{ <gas op="add" lib="fp19" form="fp127lib" /> }} | {{ <gas op="mul" lib="fp19" form="fp127lib" /> }} | {{ <gas op="div" lib="fp19" form="fp127lib" /> }} | {{ <gas op="exp" lib="fp19" form="fp127lib" /> }} | {{ <gas op="ln" lib="fp19" form="fp127lib" /> }} | {{ <gas op="pow" lib="fp19" form="fp127lib" /> }} | {{ <gas op="sqrt" lib="fp19" form="fp127lib" /> }} |
| ABDKMathQuad | 34 | 10<sup>±4,932</sup> | {{ <gas op="add" lib="fp19" form="quad" /> }} | {{ <gas op="mul" lib="fp19" form="quad" /> }} | {{ <gas op="div" lib="fp19" form="quad" /> }} | {{ <gas op="exp" lib="fp19" form="quad" /> }} | {{ <gas op="ln" lib="fp19" form="quad" /> }} | {{ <gas op="pow" lib="fp19" form="quad" /> }} | {{ <gas op="sqrt" lib="fp19" form="quad" /> }} |

Inline library, median gas per call on the same inputs ([full table](#gas-against-fp127-and-quad)). FP19 carries twice binary128's digits and costs less than Quad on every op here but `sqrt`. FP127 costs less than FP19 on every op here, with fewer digits.

## The deployed contracts

{{ <deployment lib="fp19" /> }}

FP19 v5 (Blockulator 2.2) is four contracts from one source. The record above is the FP19 contract's; [`FP19.md`](/contracts/deployments/FP19.md) has all four.

| contract | what it holds | address | ops |
|---|---|---|---|
| FP19 | the number | `0xAa1f71B7B08d568379b28E1488c6B737a1C6eb52` | `add` `sub` `mul` `div` `inv` `sqrt` `cbrt` `hypot` `gavg`; `neg` `abs` `sign`; `cmp` `lt` `eq` `min` `max` `clamp`; `floor` `ceil` `round` `frac`; `avg` `dist` `zeroFloorSub` `lerp`; `mulDown` `mulUp` `divDown` `divUp`; every conversion |
| FP19E | the elementary functions, on one exp/log kernel | `0x017F68A57dD53a6dF2043c24B712b287F9549AE2` | `exp` `exp2` `exp10` `expm1` `ln` `log2` `log10` `log2Up` `log1p` `pow` `powu` `compound` |
| FP19H | the hyperbolic functions | `0xEfefa2B63A173d56F9db79C5dd8A607F4aA859A5` | `sinh` `cosh` `tanh` `atanh` |
| FP19S | the special functions | `0x73E8809F163d4358773cc5F25c134997B4b842F4` | `erf` `erfc` `normCdf` `lambertW0` `lambertWm1` `factorial` |

FP19H has its own copy of the exp/log kernel because FP19E with the hyperbolics was over the 24,576-byte limit. `pi` is the constant `FP19Lib.PI`, and `gcd` was removed in v5. The inline library holds all 65 ops.

The contracts need the CLZ opcode (EIP-7939, evmVersion osaka), so they do not run on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list]({{ config.extra.repo }}/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)). FP19 v4 (Blockulator 2.1: FP19, FP19X, FP19X2 and FP19X3) and v3 (Blockulator 2.0) stay live at the addresses in the record.

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

Compile `FP19Lib.sol` with `via_ir = true` in `foundry.toml`. Through the IR, `add` drops from 677 to 545 gas and `exp` from 3,277 to 2,848 ([`profile.md`]({{ config.extra.repo }}/blob/master/docs/benchmarks/profile.md)).

```solidity
import {FP19Lib} from "@blockulator/contracts/fp19/FP19Lib.sol";

// a per-second rate over a year, with the rate itself held to 71 digits
int256 r = FP19Lib.div(FP19Lib.fromFixed18(0.05e18), FP19Lib.fromUint(31536000));
int256 g = FP19Lib.compound(r, 31536000);   // (1 + r)^n without ever rounding 1 + r
int256 balanceWad = FP19Lib.toFixed18(FP19Lib.mul(FP19Lib.fromFixed18(principalWad), g));
```

`fromFixed18` and `toFixed18` convert to and from WAD. `fromFP127` is exact below 2<sup>109</sup> and rounds once above; `toFP127` rounds to the nearest 2<sup>−128</sup>.

## Typed API

`FP19Type.sol` is opt-in: `type FP19 is int256`, with arithmetic and comparison operators bound to the library and every other op attached (`x.exp()`, `a.mulUp(b)`). `fp19FromWad`, `fp19FromInt` and `fp19FromUint` convert in, `toWadDown`, `toUintUp` and the rest convert out, `toFP127` and `toFP19` cross to FP127's type, and `ONE` and `PI` are typed constants. The wrapper only re-types, so results and reverts are `FP19Lib`'s, and through the IR the gas is the same.

```solidity
import {FP19, ONE, fp19FromWad, fp19FromInt} from "fp19/FP19Type.sol";
import {FP127} from "fp127/FP127Type.sol";

FP19 b = fp19FromWad(1.5e18) * ONE.exp();  // 1.5e; * is FP19Lib.mul
bool between = b > fp19FromInt(4) && b < fp19FromInt(5);
uint256 charged = b.toUintUp();              // 5, ceiled
FP127 n = b.toFP127();                       // the nearest FP127 value
```

## Integrating

Two rules, each from the replay of a real exploit ([integrating](/library/integrating/) has the replays and code).

1. **Store the state in the format.** Keep a running balance, index or accumulator as an FP19 value, and round to token units only on the way out. In Bunni v2's replay this keeps a balance the attack drained from 28 wei to 4 at 35.6 wei, as exact arithmetic does.
2. **Round toward the protocol at the token edge.** Round down what you pay out and round up what you take in: `toUintDown` and `toUintUp`, `toFixed18Down` and `toFixed18Up`, `mulDown` and `mulUp`, `divDown` and `divUp`. Under this rule Resupply's borrow against 1 wei of collateral reverts.

## The ops

Each op's worst-case precision against its gas. Hover a dot for the op.

{{ <plot chart="libops" arg="fp19" label="Correct bits on the worst input against median gas per call for each op; the numbers are in the table below." /> }}

{{ <optable lib="fp19" /> }}

### Gas against FP127 and Quad

{{ <gastable repo={config.extra.repo} lib="fp19" /> }}

The source is `contracts/src/fp19/FP19.yul.src`; the deployed contracts and the inline library are fuzzed equal across all of `int256`. Full reference: [`contracts/src/fp19/README.md`]({{ config.extra.repo }}/blob/master/contracts/src/fp19/README.md).

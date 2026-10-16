+++
title = "FP256"
description = "256-bit binary float. One word, 71 digits at any magnitude, every op rounded once."
path = "library/fp256"
aliases = ["/float/"]

[extra]
group = "library"
+++

FP127 has 38 digits between 2^−128 and 2^127 and nothing outside; the [edges](/results/edges/) show where that ends. FP256 fills the whole word, so the digits travel with the value.

## The word

Sign in bit 255, a 19-bit exponent (bias 262,143), a 236-bit fraction with an implicit one: 237 significant bits, about 71 digits, from 10^−78,900 to 10^78,900. No NaN, no infinity, no subnormals, no negative zero. Zero is the all-zero word; any other word with exponent 0 reverts `OutOfRange`. Equality is bit equality.

```
[ s | E, 19 bits | F, 236 bits ]      value = (-1)^s (1 + F / 2^236) 2^(E - 262143)
```

Rounding: once per op, ties away from zero. Overflow reverts; underflow rounds to zero. `ONE` is `0x3ffff << 236`.

| | digits | range |
|---|---:|---|
| FP127 | 38 | 2^−128 to 2^127 (±1.7 × 10^38) |
| ABDKMathQuad | 34 | 10^±4,932 |
| FP256 | 71 | 10^±78,900 |

## Deployed form

The address below is release one. Release two (the kernels described under [Release two](#release-two)) is in the repository and not yet deployed.

{{ <deployment lib="fp256" /> }}

## Inline form

```sh
forge install securedataresearch/blockulator
echo "fp256/=lib/blockulator/contracts/src/fp256/" >> remappings.txt
```

```solidity
import {FP256Lib} from "fp256/FP256Lib.sol";

// a per-second rate over a year, with the rate itself held to 71 digits
int256 r = FP256Lib.div(FP256Lib.fromFixed18(0.05e18), FP256Lib.fromUint(31536000));
int256 g = FP256Lib.pow(FP256Lib.add(FP256Lib.ONE, r), FP256Lib.fromUint(31536000));
int256 balanceWad = FP256Lib.toFixed18(FP256Lib.mul(FP256Lib.fromFixed18(principalWad), g));
```

`fromFP127` / `toFP127` convert exactly whenever the value fits; `fromFixed18` / `toFixed18` convert to WAD.

## Release two

Every op, `exp`, `ln` and `pow` included, returns the correctly rounded word at every committed vector. Release one borrowed FP127's kernels and held 146, 149 and 123 bits on those three. Release two computes at 2^−254 with 512-bit products: 2^f from a 16-entry table and a degree-26 polynomial, log2 from twelve reduction stages and a degree-17 polynomial, each within 2^−250 before the one rounding.

## The ops

{{ <optable lib="fp256" /> }}

Source: `contracts/src/fp256/FP256.yul.src`, built by FP127's generator; object and library proven equal on all of `int256`. Full reference: [`contracts/src/fp256/README.md`]({{ config.extra.repo }}/blob/master/contracts/src/fp256/README.md).

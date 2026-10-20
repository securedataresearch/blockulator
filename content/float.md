+++
title = "FP256"
description = "256-bit binary float. One word, 71 digits at any magnitude, every op but Lambert W rounded once."
path = "library/fp256"
aliases = ["/float/"]

[extra]
group = "library"
+++

FP127 has 38 digits at 1, 8 at 10^−30 and nothing outside 2^−128 to 2^127; the [edges](/results/edges/) show where that ends. FP256 fills the whole word, so the digits travel with the value.

## The word

Sign in bit 255, a 19-bit exponent (bias 262,143), a 236-bit fraction with an implicit one: 237 significant bits, about 71 digits, from 10^−78,900 to 10^78,900. No NaN, no infinity, no subnormals, no negative zero. Zero is the all-zero word; any other word with exponent 0 reverts `OutOfRange`. Equality is bit equality.

```
[ s | E, 19 bits | F, 236 bits ]      value = (-1)^s (1 + F / 2^236) 2^(E - 262143)
```

Rounding: once per op (Lambert W iterates), ties away from zero. Overflow reverts; underflow rounds to zero. `ONE` is `0x3ffff << 236`.

| | digits | range |
|---|---:|---|
| FP127 | 38 at 1 | 2^−128 to 2^127 (±1.7 × 10^38) |
| ABDKMathQuad | 34 | 10^±4,932 |
| FP256 | 71 | 10^±78,900 |

## Deployed form

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
int256 g = FP256Lib.compound(r, 31536000);   // (1 + r)^n without ever rounding 1 + r
int256 balanceWad = FP256Lib.toFixed18(FP256Lib.mul(FP256Lib.fromFixed18(principalWad), g));
```

`fromFP127` is exact below 2^109 and rounds once above, `toFP127` rounds to the nearest 2^−128; `fromFixed18` / `toFixed18` convert to WAD.

## Release three

28 ops. `exp`, `ln`, `log1p`, `expm1`, `erf`, `erfc`, `normCdf` and every non-transcendental op return the correctly rounded word at every committed vector. `pow`, `powu` and `compound` are within one unit in the last place while |y log2 x| stays below about 2^13; the Lambert branches are within two units away from −1/e. On random inputs (4,000 to 20,000 per op) `add`, `mul`, `div`, `sqrt`, `exp`, `log1p`, `expm1`, `erf` and `erfc` were correctly rounded every time; `ln`, `normCdf` and `pow` were one unit off on 1 in 20,000, 4,000 and 2,500. The kernels run at 2^−254 with 512-bit products: 2^f from a 16-entry table and a degree-26 polynomial, log2 from twelve reduction stages and a degree-17 polynomial, `erfc` as e^(−y²) times a scaled series or continued fraction (never 1 − erf). Release one borrowed FP127's kernels (146, 149 and 123 bits on exp, ln and pow); release two refit them for the wide word; release three added nine ops.

## The ops

{{ <optable lib="fp256" /> }}

Source: `contracts/src/fp256/FP256.yul.src`, built by FP127's generator; object and library fuzzed equal across all of `int256`. Full reference: [`contracts/src/fp256/README.md`]({{ config.extra.repo }}/blob/master/contracts/src/fp256/README.md).

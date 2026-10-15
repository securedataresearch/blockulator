+++
title = "Float"
description = "FP256: 256-bit binary floating point for the EVM. One word, 71 digits at any magnitude, no walls, every op rounded once from kernels at 2^-254."
+++

FP127 is a fixed point: 38 digits between 2^−128 and 2^127, and nothing outside. The [edges](/edges/) measured where that ends. FP256 is the second ruler: a binary float that fills the whole word, so the digits travel with the value.

## The word

One `int256` holding the bit pattern of a float: the sign in bit 255, a 19-bit biased exponent in bits 254..236 (bias 262,143), and a 236-bit fraction with an implicit leading one, so 237 significant bits, about 71 decimal digits, from 2^−262142 to just under 2^262145 (about 10^±78,900). Zero is the all-zero word and the only word with exponent 0; any other word with exponent 0 is not a number and every op reverts `OutOfRange` on it. There is no NaN, no infinity, no subnormal and no negative zero: every valid word is a finite number with one representation, equality is bit equality, and positive words order as unsigned integers.

```
[ s | E, 19 bits | F, 236 bits ]      value = (-1)^s (1 + F / 2^236) 2^(E - 262143)
```

Rounding is half up on the magnitude (ties away from zero), once per op. Overflow reverts; underflow rounds to zero. `ONE` is `0x3ffff << 236`.

Against the other two rulers on this site: FP127 holds 128 bits of fraction, so where the money lives it has 38 digits to FP256's 71 and to ABDKMathQuad's 34; past 2^±128 it has none, and the floats keep theirs. Quad uses 128 bits of the word; FP256 uses all 256.

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
int256 g = FP256Lib.pow(FP256Lib.add(FP256Lib.ONE, r), FP256Lib.fromUint(31536000));
int256 balanceWad = FP256Lib.toFixed18(FP256Lib.mul(FP256Lib.fromFixed18(principalWad), g));
```

`fromFP127` and `toFP127` bridge to FP127 (exact in both directions whenever the value fits), `fromFixed18` and `toFixed18` to WAD.

## Release two

The arithmetic, the root, the comparisons and the conversions are exact to the 237-bit grid at every committed vector, and so are `exp`, `ln` and `pow`. Release one borrowed FP127's kernels, which compute at 2^−192 with polynomials fitted for a 128-bit result, and held 146, 149 and 123 bits. Release two's kernels compute at 2^−254 with 512-bit products: 2^f from a 16-entry table and a degree-26 polynomial, log2 from twelve reduction stages and a degree-17 polynomial, each within 2^−250 before the one rounding, so the rounded word is the correct one at every vector. The series bands near zero and near one stay, at the same scale, so small arguments keep their relative precision.

## The ops

{{ <optable lib="fp256" /> }}

The source is one Yul file, `contracts/src/fp256/FP256.yul.src`, read by the same generator as FP127's; the helpers it shares with FP127 are byte-identical copies, and the object and the library are proven equal on the full `int256` domain. The format and every op are documented in [`contracts/src/fp256/README.md`]({{ config.extra.repo }}/blob/master/contracts/src/fp256/README.md).

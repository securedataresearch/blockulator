+++
title = "Migrating"
description = "From Solady, PRBMath and ABDK: what each call becomes, and what changes in the result and the gas."
path = "library/migrating"

[extra]
group = "library"
+++

Every number on this page is measured. The share of results off by a wei or more, and the worst error, come from the [WAD results](/results/wad/); the gas comes from the [per-op benchmarks](/results/ops/). Hover a row for the exact call.

## From Solady

BlockulatorWad has the names, signatures, rounding directions and error selectors of Solady's `FixedPointMathLib`, so the move is one import:

```solidity
import {BlockulatorWad as FixedPointMathLib} from "@blockulator/contracts/wad/BlockulatorWad.sol";
```

{{ <table name="migrate.solady.wad" first="Solady FixedPointMathLib" /> }}

Solady's multiply and divide functions return exact values. Their share wrong is all reverts where x · y (or x · 10<sup>18</sup> for a quotient) passes 2<sup>256</sup> though the result fits, so their worst error is 0. The worst error is absolute: near 10<sup>74</sup>, one part in 10<sup>18</sup> is many wei.

BlockulatorWad returns the exact value rounded once, and its domains only widen: `mulWad` and `divWad` revert only when the result does not fit, `powWad(0, y)` is defined, and `expWad` reaches one wei further ([full list](https://github.com/securedataresearch/blockulator/blob/master/contracts/src/wad/README.md#where-it-differs-from-solady)).

It needs the CLZ opcode: compile with `evm_version = "osaka"` and solc 0.8.31 or later. Keep Solady's integer helpers (`abs`, `min`, `avg` and the rest); they have no WAD meaning.

## From PRBMath

PRBMath's values are user-defined types over the same 18-decimal integers, so a call moves by unwrapping. `exp`, `ln` and `pow` keep PRBMath's names. `mul`, `div` and `sqrt` become `mulWad` or `sMulWad`, `divWad` or `sDivWad`, and `sqrtWad`. `log2` and `log10` become `log2Wad` and `log10Wad`.

```solidity
// SD59x18 x, y;
int256 r = BlockulatorWad.pow(x.unwrap(), y.unwrap());   // was x.pow(y)
```

{{ <table name="migrate.prbmath.wad" first="PRBMath SD59x18 and UD60x18" /> }}

{{ <table name="migrate.prbmath.wadud" first="PRBMath UD60x18" /> }}

## From ABDK

Each of ABDK's two formats has a Blockulator counterpart of the same kind, and both use one `int256` per value:

- ABDKMath64x64 moves to FP127: 127.128 fixed point, with 64 more fractional bits. `x << 64` converts.
- ABDKMathQuad's binary128 moves to FP19: a 256-bit binary float, with 237 bits of significand against 113.

{{ <table name="migrate.abdk.ops" first="ABDKMath64x64" /> }}

{{ <table name="migrate.abdk.quad" first="ABDKMathQuad" /> }}

Gas is the inline library on both sides. FP127 and FP19 are also deployed as contracts you can `staticcall`; [the library pages](/library/) have the addresses.

+++
title = "Migrating"
description = "From Solady, PRBMath and ABDK: what each call becomes, and what changes in the result and the gas."
path = "library/migrating"

[extra]
group = "library"
+++

Every number on this page is measured: the share of results off by at least a wei and the worst error come from the WAD sweep ([WAD results](/results/wad/)), the gas from the per-op benchmarks ([per op](/results/ops/)). Hover a row for the exact call measured.

## From Solady

BlockulatorWad has the names, signatures, rounding directions and error selectors of Solady's `FixedPointMathLib`, so the move is one import:

```solidity
import {BlockulatorWad as FixedPointMathLib} from "blockulator/contracts/src/wad/BlockulatorWad.sol";
```

{{ <table name="migrate.solady.wad" first="Solady FixedPointMathLib" /> }}

Every value Solady's multiply and divide functions return is exact; their share wrong is all reverts where the result fits (x · y, or x · 10<sup>18</sup> for a quotient, past 2<sup>256</sup>), which is why their worst error is 0. The worst error is absolute: on a result near 10<sup>74</sup>, one part in 10<sup>18</sup> is many wei.

What changes is that every result is the exact value rounded once, and the domains only widen. `mulWad` and `divWad` revert only when the result does not fit; `powWad(0, y)` is defined; `expWad` reaches one wei further. BlockulatorWad needs the CLZ opcode (compile with `evm_version = "osaka"`, solc 0.8.31 or later), so it does not run on chains without it. The full list is in [its README](https://github.com/securedataresearch/blockulator/blob/master/contracts/src/wad/README.md#where-it-differs-from-solady). Solady's integer helpers (`abs`, `min`, `avg` and the rest) have no WAD meaning; keep them.

## From PRBMath

PRBMath's values are user-defined types over the same 18-decimal integers, so a call moves by unwrapping: `exp`, `ln` and `pow` keep PRBMath's names; `mul`, `div` and `sqrt` become `mulWad` or `sMulWad`, `divWad` or `sDivWad`, `sqrtWad`; `log2` and `log10` become `log2Wad` and `log10Wad`.

```solidity
// SD59x18 x, y;
int256 r = BlockulatorWad.pow(x.unwrap(), y.unwrap());   // was x.pow(y)
```

{{ <table name="migrate.prbmath.wad" first="PRBMath SD59x18 and UD60x18" /> }}

{{ <table name="migrate.prbmath.wadud" first="PRBMath UD60x18" /> }}

## From ABDK

ABDK's two formats have a Blockulator counterpart of the same kind. 64.64 fixed point moves to FP127 (127.128 fixed point, 64 more fractional bits: `x << 64` converts), and ABDKMathQuad's binary128 moves to FP19 (a 256-bit binary float, 237 bits of significand against 113). Both are one int256 per value; the table gives each call's counterpart.

{{ <table name="migrate.abdk.ops" first="ABDKMath64x64" /> }}

{{ <table name="migrate.abdk.quad" first="ABDKMathQuad" /> }}

Gas is the inline library on both sides. FP127 and FP19 are also deployed as objects to `staticcall`; [the library pages](/library/) have the addresses.

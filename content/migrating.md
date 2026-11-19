+++
title = "Migrating"
description = "From Solady, PRBMath and ABDK to BL19 or BL127: what each call becomes, and what changes in the result and the gas."
path = "library/migrating"

[extra]
group = "library"
+++

Every number on this page is measured. The share of results off by a wei or more is on everyday inputs, from the [WAD results](/results/wad/); the gas comes from the same run for Solady and PRBMath, and from the [per-op benchmarks](/results/ops/) for ABDK. Hover a row for the exact call.

A WAD value moves in with `fromFixed18` and out with `toFixed18Down` or `toFixed18Up`. Do that around a whole calculation, not around each call: the tables below convert around every single call, which is the worst case for the gas. [Integrating](/library/integrating/) has the two rules.

## From Solady

{{ <table name="migrate.solady.wad" first="Solady FixedPointMathLib" /> }}

Move `expWad`, `lnWad`, `powWad` and `lambertW0Wad`: on everyday inputs Solady is off by a wei on 4% to 68% of their results, and BL19 and BL127 on none. Keep `mulWad`, `divWad`, `sqrtWad` and `cbrtWad` for a single product, quotient or root of token amounts: they are exact and cost less: `mulWad` is 86 gas, against 827 through BL127 and 2,473 through BL19 with their conversions. Both libraries need the CLZ opcode: compile with `evm_version = "osaka"` and solc 0.8.31 or later.

## From PRBMath

PRBMath's values are user-defined types over the same 18-decimal integers, so a value moves by unwrapping: `BL19Lib.fromFixed18(x.unwrap())`. BL19 and BL127 have typed values with operators too ([BL19](/library/bl19/#typed-api), [BL127](/library/#typed-api)).

{{ <table name="migrate.prbmath.wad" first="PRBMath SD59x18 and UD60x18" /> }}

{{ <table name="migrate.prbmath.wadud" first="PRBMath UD60x18" /> }}

On 200 everyday inputs each, PRBMath's `exp` is off by a wei on 107 results and its `ln`, `log2`, `log10` and `pow` on all 200; BL19 and BL127 on none. Its `mul`, `div` and `sqrt` are exact; keep them for a single product, quotient or root.

## From ABDK

Each of ABDK's two formats has a Blockulator counterpart of the same kind, and both use one `int256` per value:

- ABDKMath64x64 moves to BL127: 127.128 fixed point, with 64 more fractional bits. `x << 64` converts.
- ABDKMathQuad's binary128 moves to BL19: a 256-bit binary float, with 237 bits of significand against 113.

{{ <table name="migrate.abdk.ops" first="ABDKMath64x64" /> }}

{{ <table name="migrate.abdk.quad" first="ABDKMathQuad" /> }}

Gas is the inline library on both sides. BL127 and BL19 are also deployed as contracts you can `staticcall`; [the library pages](/library/) have the addresses.

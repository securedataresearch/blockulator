+++
title = "Move to BL19 or BL127"
description = "From Solady, PRBMath and ABDK to BL19 or BL127: what each library does better, what each call becomes, and what changes in the result and the gas."
path = "library/moving"
aliases = ["/library/migrating/", "/vs/"]

[extra]
group = "library"
+++

Every number on this page is measured. The share of results off by a wei or more is on everyday inputs, from the [WAD results](/results/wad/); the gas comes from the same run for Solady and PRBMath, and from the [per-op benchmarks](/results/ops/) for ABDK. Hover a row for the exact call.

A WAD value moves in with `fromFixed18` and out with `toFixed18Down` or `toFixed18Up`. Do that around a whole calculation, not around each call: the tables below convert around every single call, which is the worst case for the gas. [Integrating](/library/integrating/) has the two rules.

Each established library does something better than Blockulator, and each section below says what before it shows the measurements. If you intend to keep your library, [Check your math](/library/checking/) shows how to measure it against BL19 instead.

## From Solady

{{ <table name="migrate.solady.wad" first="Solady FixedPointMathLib" /> }}

Move `expWad`, `lnWad`, `powWad` and `lambertW0Wad`: on everyday inputs Solady is off by a wei on 4% to 68% of their results, and BL19 and BL127 on none. Keep `mulWad`, `divWad`, `sqrtWad` and `cbrtWad` for a single product, quotient or root of token amounts: they are exact and cost less: `mulWad` is 86 gas, against 827 through BL127 and 2,473 through BL19 with their conversions. Both libraries need the CLZ opcode: compile with `evm_version = "osaka"` and solc 0.8.31 or later.

### Solady: what it does better, side by side

**What it does better:** gas. Its `expWad`, `lnWad` and `powWad` are the cheapest WAD transcendentals there are, its code is small, and it runs on every EVM chain.

**The answer:** they are cheap because they stop short of the last wei: on 200 everyday inputs each, `expWad` is off by a wei on 55 results, `lnWad` on 8 and `powWad` on 136, and BL19 and BL127 on none. BL127 keeps 38 digits at 6.6 times the gas on `exp` and 3.5 times on `ln`. For a single product or quotient of token amounts Solady's `mulWad` and `divWad` are exact and cheaper; keep them.

{{ <table name="vs.solady" first="" /> }}

## From PRBMath

PRBMath's values are user-defined types over the same 18-decimal integers, so a value moves by unwrapping: `BL19Lib.fromFixed18(x.unwrap())`. BL19 and BL127 have typed values with operators too ([BL19](/library/bl19/#typed-api), [BL127](/library/bl127/#typed-api)).

{{ <table name="migrate.prbmath.wad" first="PRBMath SD59x18 and UD60x18" /> }}

{{ <table name="migrate.prbmath.wadud" first="PRBMath UD60x18" /> }}

On 200 everyday inputs each, PRBMath's SD59x18 `exp` is off by a wei on 107 results and its `ln`, `log2`, `log10` and `pow` on all 200; BL19 and BL127 on none. Its `mul`, `div` and `sqrt` are exact; keep them for a single product, quotient or root.

### PRBMath: what it does better, side by side

**What it does better:** types. SD59x18 and UD60x18 are user-defined value types with operators, so a raw integer cannot be passed where a fixed-point value is meant.

**The answer:** BL19 and BL127 are typed the same way. PRBMath is off by a wei more often than Solady, on 107 of 200 everyday `exp` results and on all 200 `ln`, `log2`, `log10` and `pow` results, and costs 3.6 times BL127's gas on `ln` and 3.0 times on `pow`; `exp` costs about the same, 2,844 gas against BL127's 2,834.

{{ <table name="vs.prbmath" first="" /> }}

## From ABDK

Each of ABDK's two formats has a Blockulator counterpart of the same kind, and both use one `int256` per value:

- ABDKMath64x64 moves to BL127: 127.128 fixed point, with 64 more fractional bits. `x << 64` converts.
- ABDKMathQuad's binary128 moves to BL19: a 256-bit binary float, with 237 bits of significand against 113.

{{ <table name="migrate.abdk.ops" first="ABDKMath64x64" /> }}

{{ <table name="migrate.abdk.quad" first="ABDKMathQuad" /> }}

Gas is the inline library on both sides. BL127 and BL19 are also deployed as contracts you can `staticcall`; [the library pages](/library/) have the addresses.

### ABDK 64.64: what it does better, side by side

**What it does better:** maturity and reach. ABDKMath64x64 is old, small and runs everywhere, and its `mul` and `div` cost less than BL127's.

**The answer:** BL127 is the same idea with 64 more fractional bits: 38 digits at 1 against 19, at lower gas on `add`, `exp` and `ln`, and about the same on `sqrt` (815 gas against 822). On the edge calls it reverts less often and returns zero far less often. Its own limit is its range, ±1.7 × 10<sup>38</sup>.

{{ <table name="vs.abdk" first="" /> }}

### ABDKMathQuad (binary128): what it does better, side by side

**What it does better:** interoperability. Its values are IEEE 754 binary128, the same bits as quadruple precision off chain. Its `sqrt` costs less than BL19's.

**The answer:** BL19 has 237 bits of significand against 113, and costs less on `add`, `mul`, `exp`, `ln` and `pow`, and about the same on `div`. Against BL127, binary128 keeps 34.0 digits at any size, and BL127 keeps 38.5 + log<sub>10</sub>|x|, which is more from |x| ≈ 3 × 10<sup>−5</sup> up.

{{ <table name="vs.quad" first="" /> }}

## Where Blockulator cannot go

- **Chains without CLZ.** BL19 and BL127 need the CLZ opcode (EIP-7939, the osaka EVM) and solc 0.8.31 or later, so they do not run on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list](https://github.com/securedataresearch/blockulator/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)).
- **The cheapest exp.** Where a wei of error per call is acceptable, Solady is cheaper.
- **Eight core ops without a proof.** 17 of BL127's 19 core ops and 18 of BL19's 24 are proven for every input. BL127's `gavg` and `hypot`, and BL19's `add`, `sub`, `sqrt` and the three `toFixed18`, are fuzzed against their exact specs, not proven ([proofs](/proofs/)).

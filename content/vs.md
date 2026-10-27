+++
title = "Versus"
description = "Why not Solady, PRBMath or ABDK: what each does better, what Blockulator answers, and where it cannot go."
path = "vs"

[extra]
group = "results"
+++

Each established library does something better. This page says what, then puts the measurements side by side. Gas is the median per call on everyday inputs, inline on both sides.

## Solady

**What it does better:** gas. Its `expWad`, `lnWad` and `powWad` are the cheapest WAD transcendentals there are, its code is small, and it runs on every EVM chain.

**The answer:** they are cheap because they stop short of the last wei. BlockulatorWad has Solady's names and is never off by a wei, at 5.5 times the gas on `expWad` and 4.3 times on `lnWad`. Its products and quotients cost 15 to 40 gas more than Solady's, and never revert where the result fits.

{{ <table name="vs.solady" first="" /> }}

## PRBMath

**What it does better:** types. SD59x18 and UD60x18 are user-defined value types with operators, so a raw integer cannot be passed where a fixed-point value is meant.

**The answer:** FP19 and FP127 are typed the same way, and BlockulatorWad takes PRBMath's integers as they are. PRBMath is off by a wei more often than Solady, and BlockulatorWad costs less on every WAD function. PRBMath costs 2.9 times as much on `ln` and 2.1 times as much on `pow`.

{{ <table name="vs.prbmath" first="" /> }}

## ABDK 64.64

**What it does better:** maturity and reach. ABDKMath64x64 is old, small and runs everywhere, and its `mul` and `div` cost less than FP127's.

**The answer:** FP127 is the same idea with 64 more fractional bits: 38 digits at 1 against 19, at lower gas on `add`, `exp`, `ln` and `sqrt`. On the edge calls it reverts less often and returns zero far less often. Its own limit is its range, ±1.7 × 10<sup>38</sup>.

{{ <table name="vs.abdk" first="" /> }}

## ABDKMathQuad (binary128)

**What it does better:** interoperability. Its values are IEEE 754 binary128, the same bits as quadruple precision off chain. Its `sqrt` costs less than FP19's.

**The answer:** FP19 has 237 bits of significand against 113, and costs less on `add`, `mul`, `div`, `exp`, `ln` and `pow`. Against FP127, binary128 keeps 34.0 digits at any size, and FP127 keeps 38.5 + log<sub>10</sub>|x|, which is more from |x| ≈ 3 × 10<sup>−5</sup> up.

{{ <table name="vs.quad" first="" /> }}

## Where Blockulator cannot go

- **Chains without CLZ.** FP19, FP127 and BlockulatorWad need the CLZ opcode (EIP-7939, the osaka EVM) and solc 0.8.31 or later, so they do not run on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list](https://github.com/securedataresearch/blockulator/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)).
- **The cheapest exp.** Where a wei of error per call is acceptable, Solady is cheaper.
- **Six FP19 ops without a proof.** All 17 of FP127's core ops and 18 of FP19's 24 are proven for every input. FP19's `add`, `sub`, `sqrt` and the three `toFixed18` are fuzzed against their exact specs, not proven ([proofs](/proofs/)).

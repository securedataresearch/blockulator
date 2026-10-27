+++
title = "Versus"
description = "Why not Solady, PRBMath or ABDK: what each does better, what Blockulator answers, and where it cannot go."
path = "vs"

[extra]
group = "results"
+++

Each established library has something real going for it. This page says what, then puts the measurements side by side. Every number is generated from the same datasets as the rest of the site; hover a row for its name in full. Gas is the median per call on everyday inputs, inline on both sides.

## Solady

**What it does better:** gas. Solady's `expWad`, `lnWad` and `powWad` are the cheapest WAD transcendentals there are, at a few hundred gas, and its code is small. It runs on every EVM chain.

**The answer:** they are cheap because they stop short of the last wei. BlockulatorWad has Solady's names and rounding directions, and is never off by a wei. It costs about five times the gas on `expWad` and four on `lnWad`. Products, quotients and roots cost about the same in both, and there BlockulatorWad never reverts where the result fits.

{{ <table name="vs.solady" first="" /> }}

## PRBMath

**What it does better:** types. SD59x18 and UD60x18 are user-defined value types with operators, so a raw integer cannot be passed where a fixed-point value is meant, and an unsigned one cannot go negative.

**The answer:** FP127 and FP19 are typed the same way (`type FP127 is int256`, with operators), and BlockulatorWad takes PRBMath's integers as they are. On the WAD functions PRBMath is off by a wei more often than Solady, and BlockulatorWad is cheaper on every one: `ln` by about three times, `pow` by two.

{{ <table name="vs.prbmath" first="" /> }}

## ABDK 64.64

**What it does better:** maturity and reach. ABDKMath64x64 is old, small and runs everywhere; its `mul` is cheaper than FP127's.

**The answer:** FP127 is the same idea with 64 more fractional bits: 38 digits at 1 against 19, with `exp`, `ln` and `sqrt` cheaper. On the edge probes it reverts less often and goes to zero far less often; its own wall is the range, ±1.7 × 10<sup>38</sup>.

{{ <table name="vs.abdk" first="" /> }}

## ABDKMathQuad (binary128)

**What it does better:** interoperability. Its words are IEEE 754 binary128, the same bits as quadruple precision off chain, and its `sqrt` is cheaper than FP19's.

**The answer:** FP19 is a 256-bit float with 237 bits of significand against 113, so binary128 never matches its precision. It is also cheaper on `mul`, `exp`, `ln` and `pow`. Against FP127, binary128 keeps 34.0 digits at any magnitude, and FP127's 38.5 + log<sub>10</sub>|x| passes it from |x| ≈ 3 × 10<sup>−5</sup> up.

{{ <table name="vs.quad" first="" /> }}

## Where Blockulator cannot go

- **Chains without CLZ.** FP19, FP127 and BlockulatorWad use the CLZ opcode (EIP-7939, the osaka EVM). They run on Ethereum and the chains that have it, not on zkSync Era, Avalanche C-Chain or Polygon zkEVM ([the list](https://github.com/securedataresearch/blockulator/blob/master/contracts/deployments/README.md#chains-clz-osaka-required)), and they need solc 0.8.31 or later.
- **The cheapest exp.** Where a protocol can afford an error of a wei or more on every call, Solady is cheaper.
- **Proofs in progress.** 15 of FP127's core ops are proven for every input; FP19's are being written ([proofs](/proofs/)).

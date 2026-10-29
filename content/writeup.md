+++
title = "Why the digits hold"
description = "What BL127 and BL19 are, why 18-decimal maths loses digits, and how every result here is checked."

[extra]
group = "writeup"
+++

## Two formats in one 256-bit value

**BL127** is signed fixed point with 128 bits after the point: 38 digits at 1, a range of ±1.7 × 10<sup>38</sup>, and 53 ops. **BL19** is a 256-bit float: about 71 digits at any size from 10<sup>−78,913</sup> to 10<sup>78,913</sup>, and 65 ops. Every op is exact or rounds once, and each ships as a deployed contract and an inline library.

## Why WAD loses digits

An 18-decimal number has about 60 bits of fraction, and every `mulWad` rounds. Once, that costs nothing: the error is below a token's smallest unit. But interest compounds, and every step rounds again. Compound $10,000 at 10% daily for a year and the WAD libraries keep 16.9 digits, BL127 36.2 and BL19 68.9. Aave's and Morpho's three-term e<sup>x</sup> keeps 1.2 digits on a market left idle for 10,000 days ([why](/why/)).

## How we know it is right

- **Measured.** The [ladder](/results/ladder/) runs 14 real calculations, repeated up to 10,000 times, in every library against 300-digit arithmetic. On the [edges](/results/edges/), 139 calls at the ends of each domain, BL19 keeps at least 53 digits.
- **To the last wei.** BlockulatorWad keeps Solady's function names and is exact on all 108,000 results we tested. The WAD libraries it replaces are a wei or more off on 24% to 98% of their `exp`, `ln` and `pow` results.
- **Proven.** All 17 of BL127's core ops and 18 of BL19's 24 are proven for every input; BL19's other six are fuzzed against their exact specs ([proofs](/proofs/)).
- **No owner.** No contract has storage, an owner, a proxy or an upgrade path, and each is verified on Sourcify and Blockscout.

## What it costs

BL127 costs less than PRBMath's SD59x18 on `add`, `mul`, `div`, `ln`, `pow` and `sqrt`; on `exp` it is 2,835 gas against 2,816. BL19 costs less than ABDKMathQuad on all of those but `sqrt`. Solady is cheaper than both, at 18 digits ([per op](/results/ops/)).

## When to use it

Use it for calculations that compound, accrue, iterate or chain transcendentals, and for large sums. If a protocol multiplies once and settles, Solady is cheaper and loses nothing real. More digits do not stop an exploit of an empty market, like those that hit Compound and Aave forks.

## More

[The results](/results/) · [the library](/library/) · [integrating](/library/integrating/) · the [EthCC talk](https://www.youtube.com/watch?v=a_tL99NY-yc) on the first version of BL127 · [the source](https://github.com/securedataresearch/blockulator)

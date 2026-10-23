+++
title = "Why the digits hold"
description = "What FP127 and FP19 are, why fixed-decimal maths loses digits, and how every result here is checked."
+++

## Two formats, one word

**FP127** is signed 127.128 fixed point: one `int256`, 128 fractional bits, 38 digits at 1, 53 ops from `add` to `exp`, `ln`, `pow`, the error function and both branches of Lambert W. **FP19** is a 256-bit binary float in the same word: a 19-bit exponent and 237 significant bits, about 71 digits at any magnitude from 10<sup>−78,913</sup> to 10<sup>78,913</sup>, 65 ops. Every op is exact or rounds once, to the nearest word or in its stated direction. Each library is one Yul source that becomes both a deployed contract and an inline Solidity library, fuzzed equal across all of `int256`.

## Why WAD loses digits

An 18-decimal number has about 60 bits of fraction, and every `mulWad` rounds once. A protocol never calls it once: it compounds, accrues, iterates. Every library loses about a digit per decade of steps; what differs is where it starts. $10,000 at 10% APR, compounded daily for a year: the WAD libraries keep 16 digits, ABDKMathQuad 31, FP127 36 [compound, N = 365]. Interest accrued in one step after an idle market is worse: Aave's and Morpho's three-term expansion of e<sup>rt</sup> keeps 6 digits after a year and 1 after twenty-seven. The [why](/why/) page has the full argument.

## How we know it is right

- **Built for the whole word.** Roots and inverses converge by Newton's method. `exp`, `ln` and `pow` reduce the argument with tables and finish with polynomials generated for the full precision of the word, their error bounds checked in exact integers; then every result rounds once. A short series fitted for small arguments, like a three-term expansion of e<sup>x</sup>, has no such margin, and its error grows with the argument.
- **Measured against exact arithmetic.** Every op is checked against 200- to 300-digit arithmetic: 14 scenarios over N = 1 to 10,000 steps on the [ladder](/results/ladder/), 139 probes where formats break on the [edges](/results/edges/), against every other library on this site. FP19 has no zero, no revert and no out-of-range on any probe.
- **To the last wei.** BlockulatorWad keeps Solady's names and computes in FP19: 0 wrong of 108,000 results, where the WAD libraries are wrong on 24–98% of `exp`, `ln` and `pow` results by at least a wei.
- **Proven.** FP127's core arithmetic and directed rounding are proven for all inputs with Halmos; FP19's proofs are under way ([proofs](/proofs/)).
- **Checked on chain.** The deployed contracts were re-run cell by cell against the data on this site: 9,411 ladder cells and 1,511 edge cells, 0 mismatches.

## What it costs

Correct rounding is paid in gas, and the gas sits next to the digits on every [table](/#gas). FP127 is cheaper than PRBMath, ABDK and OpenZeppelin on most ops; Solady and Solmate are cheaper still, at 18 digits. FP19 is cheaper than binary128 on `add`, `mul`, `div`, `exp`, `ln` and `pow`.

## Trust

No storage, no owner, no proxy, no upgrade. Each contract is deployed with CREATE2, so its address is recomputable from the repository; a change is a new salt and a new address. Every contract is verified on Sourcify and Blockscout.

## What it is not for

FP127 tops out near 1.7 × 10<sup>38</sup>, so it is for the maths in the middle, the rate, the price, the ratio, and a token amount goes back to wei with one `toFixed18Down` at the edge. If a protocol multiplies once and settles, Solady is cheaper and good enough. If it accrues, iterates or chains transcendentals, the [ladder](/results/ladder/) shows how many digits are left.

## More

[The results](/results/) · [the library](/library/) · [integrating](/library/integrating/) · the [EthCC talk](https://www.youtube.com/watch?v=a_tL99NY-yc) on the first, Huff-era FP127 · [the source](https://github.com/securedataresearch/blockulator)

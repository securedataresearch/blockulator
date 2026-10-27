+++
title = "Why WAD loses digits"
description = "WAD keeps about 60 bits of fraction and rounds on every step: where the digits go, and what 128 bits buy."
+++

Each figure links to its scenario on the [ladder](/results/ladder/): 14 calculations protocols really run, repeated up to 10,000 times and checked against 300-digit arithmetic ([`ladder.json`](/data/ladder.json)).

## Where the bits go in WAD

A WAD library stores a value as an integer times 10<sup>18</sup>. That is about 2<sup>60</sup>, so about 60 of the 256 bits hold the fraction.

The other 196 bits are not spare precision. They let `x * y` fit before the divide by 10<sup>18</sup>, and you cannot store a value in them: a balance of 10<sup>40</sup> fits, but `mulWad` reverts once it multiplies it by more than 11.6. ABDK's 64.64 splits a 128-bit budget into 64 bits of fraction and 64 of integer, so it is the first to revert when a balance grows ([annual compounding](/results/ladder/#compound-annual)).

{{ <wordstrip format="wad,6464" /> }}

## Where the bits go in FP127

FP127 spends the 256 bits on 128 bits of fraction, 127 integer bits and a sign. `mul` forms the full 512-bit product and keeps the middle 256 bits, so nothing is held back for headroom. That gives about 38 digits of fraction against WAD's 18, with a range of ±1.7 × 10<sup>38</sup>.

{{ <wordstrip format="fp127" /> }}

## Why iteration is what breaks it

One `mulWad` costs nothing real: its error is below a token's smallest unit. But a lending protocol accrues again and again, and after N accruals it has rounded N times.

Take $10,000 at 10% a year, compounded daily ([compound](/results/ladder/#compound)). After one day the WAD libraries are right to 19.5 digits, after a year 16.9, after 10,000 days 15.5. Over the same steps FP127 goes from 38.8 to 34.8. Both lose about a digit each time the steps grow tenfold. FP127 starts 19 digits higher, and the start is what you keep.

Subtraction is worse. An amortising loan computes `b = b·(1+r) − payment` every day, and near payoff the balance is a small difference of two large numbers. A $300,000 loan at 5%, paid daily over 10,001 days, has $55 left after 10,000 days. There the WAD libraries keep 11.9 digits and FP127 31.2 ([amortise](/results/ladder/#amortise)). Twelve digits of $55 is fine. Twelve digits of a position a basis point from liquidation, across a million accounts, may not be.

## What it costs

Inline library, median gas per call: random inputs that take no shortcut for `exp`, `ln`, `pow`, `sqrt` and `normCdf`, a fixed set across magnitudes for `mul` and `div`. A blank is an op the library does not offer; the [per-op tables](/results/ops/) have every op.

| op | FP127 | FP19 | Quad | Solady | PRBMath | ABDK | Balancer |
|---|---:|---:|---:|---:|---:|---:|---:|
| mul | {{ <gas op="mul" /> }} | {{ <gas op="mul" lib="fp19" /> }} | {{ <gas op="mul" lib="fp19" form="quad" /> }} | {{ <gas op="mul" form="solady" /> }} | {{ <gas op="mul" form="prb" /> }} | {{ <gas op="mul" form="abdk" /> }} | {{ <gas op="mul" form="balancer" /> }} |
| div | {{ <gas op="div" /> }} | {{ <gas op="div" lib="fp19" /> }} | {{ <gas op="div" lib="fp19" form="quad" /> }} | {{ <gas op="div" form="solady" /> }} | {{ <gas op="div" form="prb" /> }} | {{ <gas op="div" form="abdk" /> }} | {{ <gas op="div" form="balancer" /> }} |
| exp | {{ <gas op="exp" /> }} | {{ <gas op="exp" lib="fp19" /> }} | {{ <gas op="exp" lib="fp19" form="quad" /> }} | {{ <gas op="exp" form="solady" /> }} | {{ <gas op="exp" form="prb" /> }} | {{ <gas op="exp" form="abdk" /> }} | {{ <gas op="exp" form="balancer" /> }} |
| ln | {{ <gas op="ln" /> }} | {{ <gas op="ln" lib="fp19" /> }} | {{ <gas op="ln" lib="fp19" form="quad" /> }} | {{ <gas op="ln" form="solady" /> }} | {{ <gas op="ln" form="prb" /> }} | {{ <gas op="ln" form="abdk" /> }} | {{ <gas op="ln" form="balancer" /> }} |
| sqrt | {{ <gas op="sqrt" /> }} | {{ <gas op="sqrt" lib="fp19" /> }} | {{ <gas op="sqrt" lib="fp19" form="quad" /> }} | {{ <gas op="sqrt" form="solady" /> }} | {{ <gas op="sqrt" form="prb" /> }} | {{ <gas op="sqrt" form="abdk" /> }} | {{ <gas op="sqrt" form="balancer" /> }} |
| pow | {{ <gas op="pow" /> }} | {{ <gas op="pow" lib="fp19" /> }} | {{ <gas op="pow" lib="fp19" form="quad" /> }} | {{ <gas op="pow" form="solady" /> }} | {{ <gas op="pow" form="prb" /> }} | {{ <gas op="pow" form="abdk" /> }} | {{ <gas op="pow" form="balancer" /> }} |
| normCdf | {{ <gas op="normCdf" /> }} | {{ <gas op="normCdf" lib="fp19" /> }} | | | | | |

FP127 costs less than PRBMath on every op both offer here, and more than Solady on every op Solady offers, because it computes twice the bits. The floats, FP19 and Quad, pay for their moving point on every `add` and `mul`. FP19 costs less than Quad on every op here but `sqrt`.

## What it does not fix

FP127's range has two ends. It tops out near 1.7 × 10<sup>38</sup>: `exp(89)` reverts, and Uniswap's top tick, 1.0001<sup>887272</sup>, is one bit past it. Its smallest step is 2<sup>−128</sup>, so an argument of 10<sup>−30</sup> keeps 8 digits, and so do its root and reciprocal ([edges: exp](/results/edges/#exp), [pow](/results/edges/#pow), [sqrt](/results/edges/#sqrt), [div](/results/edges/#div)).

Fixed point gets the most precision inside a band; a float gets the widest band. [FP19](/library/fp19/) keeps at least 53 digits on every edge call, where ABDKMathQuad keeps as few as 4. FP127 is for the maths in the middle: the price, the ratio, the growth factor 1 + r. Above 3 × 10<sup>−5</sup> it holds more digits than binary128's 34.

It does not replace the integer arithmetic of a transfer, it does not stop an exploit of an empty market, and it is not cheap enough for a path that does not need the digits.

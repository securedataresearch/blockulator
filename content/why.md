+++
title = "Why WAD loses digits"
description = "60 bits of fraction, rounded once per step, for every step. Where the digits go and what 128 bits buy."
+++

Each linked figure is a cell of the [ladder](/results/ladder/) ([`ladder.json`](/data/ladder.json)): the reference input of the scenario, digits against the exact truth.

## Where the bits go in WAD

A WAD library stores a value as an integer scaled by 10<sup>18</sup>. That scale is
about 2<sup>59.79</sup>, so roughly 60 of the word's 256 bits hold the fraction. The
other 196 are not spare precision. They exist so that `x * y` fits before
the divide by 10<sup>18</sup>, and they are consumed by that product. You cannot
store a value in them: a 10<sup>40</sup> balance fits in the word, and `mulWad`
reverts once it multiplies it by more than 11.6.

ABDK's 64.64 is the same budget drawn differently, 64 fractional bits and a
64-bit integer part in an `int128`, which is why it reverts first when a
balance grows ([annual compounding, N = 365](/results/ladder/#compound-annual)).

{{ <wordstrip format="wad,6464" /> }}

## Where the bits go in FP127

FP127 spends the word as 128 fractional bits, 127 integer bits and a sign.
`mul` forms the full 512-bit product with `mul` and `mulmod` and keeps
the middle 256 bits, so no bits are reserved as overflow headroom. The
result is about 38 decimal digits in the fraction against 18 for WAD, with
a range of ±1.7 × 10<sup>38</sup>.

{{ <wordstrip format="fp127" /> }}

## Why iteration is what breaks it

One `mulWad` rounds once, to the nearest 10<sup>−18</sup>, and that is fine. A
lending protocol does not call it once. It accrues interest every block,
and after N accruals the rounding has been applied N times.

Take $10,000 at 10% APR, compounded daily ([compound](/results/ladder/#compound)). After one day ABDK
and the WAD libraries are right to 19.5 digits. After a year WAD libraries are right to 16.9;
after 10,000 steps, 15.5. FP127 goes from 38.8 to 34.8 over the same ladder. The slopes are the same, about one digit per decade of N.
The intercept is twenty digits apart, and the intercept is what you keep.

The round trip makes the mechanism visible: `x = exp(ln(x))` should be the
identity ([round trip](/results/ladder/#roundtrip)). PRBMath drifts from 16.9 digits to 12.9 by N = 10,000; Solady returns exactly 1.5 at every N, but by luck of the grid:
expWad and lnWad both truncate (each ends in a right shift), and at 1.5 the
two truncations happen to land back on the starting word. Two of its ten
inputs come back exact; the others drift to 14 digits by N = 10,000.
FP127 rounds to nearest at 2<sup>−128</sup> and returns the
identical word on every step, holding 38.7 digits at N = 10,000. It did not always: the first Yul port floored every step of exp and
ln, came back 8 ULPs low on each round trip, and lost a digit per decade of
N. Rounding to nearest with guard bits fixed it, and the ladder is where
that showed.

Subtraction is worse. An amortising loan is `b = b·(1+r) − payment` every
day, and near payoff the balance is a small difference of two large
numbers. A $300,000 loan at 5% paid daily over 10,001 days has one payment
left at N = 10,000, and there WAD libraries are down to 11.9 digits
and FP127 to 31.2 ([amortise](/results/ladder/#amortise)); after a year, with the balance still large, they had 17.2 and 36.5.
Twelve digits of a $55 balance is still fine. Twelve digits of a position
that is a basis point from liquidation across a million accounts is not,
and the ladder is where you find out which case you are in.

The arithmetic for N = 10,000: the rate and the payment floored to 10<sup>−18</sup>,
carried 10,000 times into a balance five thousand times smaller than the
loan, leave 11.9 digits on their own; the 10,000 floored `mulWad`s alone
leave 15.7.

The ladder measures each cell twice, and the second measurement says where
the loss comes from. Against the exact inputs, FP127 is right to 36 digits
after a year of daily compounding; against the inputs as the format rounds
them, it is right to 40 ([compound, N = 365](/results/ladder/#compound)). The
rate's rounding to 2<sup>−128</sup>, applied once and carried N times, sets the 36;
the 365 floored multiplications cost about two of the 42 digits the grid
holds at that balance. The WAD libraries lose part of theirs the
same way, 16.9 against exact inputs and 19.7 against rounded ones at N = 365,
and the rest to the arithmetic.

## What it costs

Per op, inline library, median gas per call: over random inputs that take no shortcut for `exp`, `ln`, `pow`, `sqrt` and `normCdf`, over the input ladder for `mul` and `div` (the [per-op tables](/results/ops/) have every op). FP256 and Quad are from FP256's benchmark, the rest from FP127's. An empty cell is an op the library does not offer.

| op | FP127 | FP256 | Quad | Solady | PRBMath | ABDK | Balancer |
|---|---:|---:|---:|---:|---:|---:|---:|
| mul | {{ <gas op="mul" /> }} | {{ <gas op="mul" lib="fp256" /> }} | {{ <gas op="mul" lib="fp256" form="quad" /> }} | {{ <gas op="mul" form="solady" /> }} | {{ <gas op="mul" form="prb" /> }} | {{ <gas op="mul" form="abdk" /> }} | {{ <gas op="mul" form="balancer" /> }} |
| div | {{ <gas op="div" /> }} | {{ <gas op="div" lib="fp256" /> }} | {{ <gas op="div" lib="fp256" form="quad" /> }} | {{ <gas op="div" form="solady" /> }} | {{ <gas op="div" form="prb" /> }} | {{ <gas op="div" form="abdk" /> }} | {{ <gas op="div" form="balancer" /> }} |
| exp | {{ <gas op="exp" /> }} | {{ <gas op="exp" lib="fp256" /> }} | {{ <gas op="exp" lib="fp256" form="quad" /> }} | {{ <gas op="exp" form="solady" /> }} | {{ <gas op="exp" form="prb" /> }} | {{ <gas op="exp" form="abdk" /> }} | {{ <gas op="exp" form="balancer" /> }} |
| ln | {{ <gas op="ln" /> }} | {{ <gas op="ln" lib="fp256" /> }} | {{ <gas op="ln" lib="fp256" form="quad" /> }} | {{ <gas op="ln" form="solady" /> }} | {{ <gas op="ln" form="prb" /> }} | {{ <gas op="ln" form="abdk" /> }} | {{ <gas op="ln" form="balancer" /> }} |
| sqrt | {{ <gas op="sqrt" /> }} | {{ <gas op="sqrt" lib="fp256" /> }} | {{ <gas op="sqrt" lib="fp256" form="quad" /> }} | {{ <gas op="sqrt" form="solady" /> }} | {{ <gas op="sqrt" form="prb" /> }} | {{ <gas op="sqrt" form="abdk" /> }} | {{ <gas op="sqrt" form="balancer" /> }} |
| pow | {{ <gas op="pow" /> }} | {{ <gas op="pow" lib="fp256" /> }} | {{ <gas op="pow" lib="fp256" form="quad" /> }} | {{ <gas op="pow" form="solady" /> }} | {{ <gas op="pow" form="prb" /> }} | {{ <gas op="pow" form="abdk" /> }} | {{ <gas op="pow" form="balancer" /> }} |
| normCdf | {{ <gas op="normCdf" /> }} | {{ <gas op="normCdf" lib="fp256" /> }} | | | | | |

Multiplication costs about twice Solady's and about half PRBMath's;
division 1.3 to 7 times theirs. The
transcendentals cost more because they compute twice as many bits and
round to the nearest word, and the error function family is the honest
expensive one. The floats, FP256 and Quad, pay for their moving point on
every add and mul, and Quad several times over on `ln` and `pow`. FP256's `exp`,
on its table-and-polynomial kernel, is cheaper than FP127's; FP127's root, seeded from
its exact bit length, is cheaper than FP256's. Through the deployed
objects the `staticcall` adds 460 to 620 gas to `add` and `mul`.

## What it does not fix

Range, and the floor. FP127 tops out near 1.7 × 10<sup>38</sup> and its grid stops at
2<sup>−128</sup>: exp(89) reverts and exp(−89) is zero, Uniswap's top tick
1.0001<sup>887272</sup> is one bit past the word, and an argument of 10<sup>−30</sup> has
eight digits on the grid, and so do its root and reciprocal ([edges: exp](/results/edges/#exp),
[pow](/results/edges/#pow), [sqrt](/results/edges/#sqrt), [div](/results/edges/#div)). A
fixed point maximises precision inside a band; a float maximises the band.
ABDKMathQuad, the first float in the tables, holds 4 to 34 digits at the
edges (the low end where an argument is 1 + x) and 16 or more on the
ladders, with half the word idle; FP256, the
[second ruler](/library/fp256/), fills the word and holds 53 or more at the edges and 54
or more on the ladders. The [edges](/results/edges/) page shows all three sides. FP127 is for the maths in the
middle, the price, the ratio, the growth factor 1 + r, values above
3 × 10<sup>−5</sup>, where it holds 38 digits at 1 against binary128's 34, and the conversion back to wei is one
`toFixed18` at the edge. It is not a replacement for the integer
arithmetic of a transfer, and it is not cheap enough to put in a path that
does not need the digits.

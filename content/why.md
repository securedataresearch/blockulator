+++
title = "Why WAD loses digits"
description = "60 bits of fraction, rounded once per step, for every step. Where the digits go and what 128 bits buy."
+++

Bracketed references are cells in [`ladder.json`](/data/ladder.json) or
[`gas.json`](/data/gas.json): the reference input of each scenario, digits
against the exact truth.

## Where the bits go in WAD

A WAD library stores a value as an integer scaled by 10^18. That scale is
about 2^59.79, so roughly 60 of the word's 256 bits hold the fraction. The
other 196 are not spare precision. They exist so that `x * y` fits before
the divide by 10^18, and they are consumed by that product. You cannot
store a value in them: a 10^40 balance fits in the word, and `mulWad`
reverts once it multiplies it by more than 11.6.

ABDK's 64.64 is the same budget drawn differently, 64 fractional bits and a
64-bit integer part in an `int128`, which is why it reverts first when a
balance grows [compound-annual, N = 365, abdk].

{{ <wordstrip format="wad,6464" /> }}

## Where the bits go in FP127

FP127 spends the word as 128 fractional bits, 127 integer bits and a sign.
`mul` forms the full 512-bit product with `mul` and `mulmod` and keeps
the middle 256 bits, so no bits are reserved as overflow headroom. The
result is about 38 decimal digits in the fraction against 18 for WAD, with
a range of ±1.7·10^38.

{{ <wordstrip format="fp127" /> }}

## Why iteration is what breaks it

One `mulWad` rounds once, to the nearest 10^-18, and that is fine. A
lending protocol does not call it once. It accrues interest every block,
and after N accruals the rounding has been applied N times.

Take $10,000 at 10% APR, compounded daily [compound]. After one day ABDK
and the WAD libraries are right to 19.5 digits. After a year WAD libraries are right to 16.9
[compound, N = 365, solady]; after 10,000 steps, 15.5 [compound, N = 10000,
solady]. FP127 goes from 38.8 to 34.8 over the same ladder [compound, N = 1 and
10000, fp127]. The slopes are the same, about one digit per decade of N.
The intercept is twenty digits apart, and the intercept is what you keep.

The round trip makes the mechanism visible: `x = exp(ln(x))` should be the
identity. PRBMath drifts from 16.9 digits to 12.9 by N = 10,000 [roundtrip,
prb]; Solady returns exactly 1.5 at every N, but by luck of the grid:
expWad and lnWad both truncate (each ends in a right shift), and at 1.5 the
two truncations happen to land back on the starting word. Two of its ten
inputs come back exact; the others drift to 14 digits by N = 10,000
[roundtrip, solady]. FP127 rounds to nearest at 2^-128 and returns the
identical word on every step, holding 38.7 digits at N = 10,000 [roundtrip,
N = 10000, fp127]. It did not always: the first Yul port floored every step of exp and
ln, came back 8 ULPs low on each round trip, and lost a digit per decade of
N. Rounding to nearest with guard bits fixed it, and the ladder is where
that showed.

Subtraction is worse. An amortising loan is `b = b·(1+r) − payment` every
day, and near payoff the balance is a small difference of two large
numbers. A $300,000 loan at 5% paid daily over 10,001 days has one payment
left at N = 10,000, and there WAD libraries are down to 11.9 digits
[amortise, N = 10000, solady] and FP127 to 31.2 [amortise, N = 10000,
fp127]; after a year, with the balance still large, they had 17.2 and 36.5.
Twelve digits of a $55 balance is still fine. Twelve digits of a position
that is a basis point from liquidation across a million accounts is not,
and the ladder is where you find out which case you are in.

The arithmetic for N = 10,000: the rate and the payment floored to 10^-18,
carried 10,000 times into a balance five thousand times smaller than the
loan, leave 11.9 digits on their own; the 10,000 floored `mulWad`s alone
leave 15.7 [amortise, N = 10000, solady, digitsFormat].

The ladder measures each cell twice, and the second measurement says where
the loss comes from. Against the exact inputs, FP127 is right to 36 digits
after a year of daily compounding; against the inputs as the format rounds
them, it is right to 40 [compound, N = 365, fp127, digitsFormat]. The
rate's rounding to 2^-128, applied once and carried N times, sets the 36;
the 365 floored multiplications cost about two of the 42 digits the grid
holds at that balance. The WAD libraries lose part of theirs the
same way, 16.9 against exact inputs and 19.7 against rounded ones at N = 365
[compound, N = 365, solady], and the rest to the arithmetic.

## What it costs

Per op, inline library form, median over the gas ladder [gas.json and
gas256.json, lib]:

| op | FP127 | FP256 | Quad | Solady | PRBMath | ABDK | Balancer |
|---|---:|---:|---:|---:|---:|---:|---:|
| mul | 263 | 530 | 688 | 126 | 485 | 171 | 239 |
| div | 645 | 800 | 818 | 93 | 509 | 221 | 239 |
| exp | 6,006 | 3,295 | 5,850 | 430 | 2,788 | 3,373 | 1,054 |
| ln | 600 | 3,006 | 1,586 | 556 | 828 | 7,078 | 1,156 |
| sqrt | 1,025 | 1,205 | 760 | 393 | 993 | 788 | 2,259 |
| pow | 3,537 | 5,541 | 23,290 | 1,275 | 9,911 | 1,348 | 2,203 |
| normCdf | 11,512 | 23,108 | — | — | — | — | — |

Multiplication costs about twice Solady's and about half PRBMath's;
division 1.3 to 7 times theirs. The
transcendentals cost more because they compute twice as many bits and
round to the nearest word, and the error function family is the honest
expensive one. The floats, FP256 and Quad, pay for their moving point on
every add and mul, and Quad several times over on pow (FP256's `exp`,
on its table-and-polynomial kernel, is now cheaper than FP127's); FP127's root, seeded from
its exact bit length, is cheaper than FP256's. Through the deployed
objects the `staticcall` adds 460 to 630 gas to `add` and `mul`.

## What it does not fix

Range, and the floor. FP127 tops out near 1.7·10^38 and its grid stops at
2^-128: exp(89) reverts and exp(-89) is zero, Uniswap's top tick
1.0001^887272 is one bit past the word, and an argument of 10^-30 has
eight digits on the grid, and so do its root and reciprocal [edges: exp,
pow, sqrt, div]. A
fixed point maximises precision inside a band; a float maximises the band.
ABDKMathQuad, the first float in the tables, holds 4 to 34 digits at the
edges (the low end where an argument is 1 + x) and 16 or more on the
ladders, with half the word idle; FP256, the
[second ruler](/library/fp256/), fills the word and holds 53 or more at the edges and 54
or more on the ladders. The [edges](/results/edges/) page shows all three sides. FP127 is for the maths in the
middle, the price, the ratio, the growth factor 1 + r, values above
3 × 10^-5, where it holds 38 digits at 1 against the float's 34, and the conversion back to wei is one
`toFixed18` at the edge. It is not a replacement for the integer
arithmetic of a transfer, and it is not cheap enough to put in a path that
does not need the digits.

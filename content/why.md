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
store a value in them: a 10^40 balance fits in the word, and the next
`mulWad` reverts because the product does not.

ABDK's 64.64 is the same budget drawn differently, 64 fractional bits and a
64-bit integer part in an `int128`, which is why it reverts first when a
balance grows [compound-annual, N = 365, abdk].

## Where the bits go in FP127

FP127 spends the word as 128 fractional bits, 127 integer bits and a sign.
`mul` forms the full 512-bit product with a four-term schoolbook and keeps
the middle 256 bits, so no bits are reserved as overflow headroom. The
result is about 38 decimal digits in the fraction against 18 for WAD, with
a range of ±1.7·10^38.

## Why iteration is what breaks it

One `mulWad` rounds once, to the nearest 10^-18, and that is fine. A
lending protocol does not call it once. It accrues interest every block,
and after N accruals the rounding has been applied N times.

Take $10,000 at 10% APR, compounded daily [compound]. After one day every
library is right to 19 digits. After a year WAD libraries are right to 16
[compound, N = 365, solady]; after 10,000 steps, 15 [compound, N = 10000,
solady]. FP127 goes from 38 to 34 over the same ladder [compound, N = 1 and
10000, fp127]. The slopes are the same, about one digit per decade of N.
The intercept is twenty digits apart, and the intercept is what you keep.

The round trip makes the mechanism visible: `x = exp(ln(x))` should be the
identity. PRBMath drifts from 16 digits to 12 by N = 10,000 [roundtrip,
prb]; Solady sits on a fixed point at 1.5 and does not drift, because its
composed error is under half a unit at 10^-18 and rounding to nearest snaps
it back; FP127 does the same at 2^-128, returning the identical word on
every step and holding 38 digits at N = 10,000 [roundtrip, N = 10000,
fp127]. It did not always: the first Yul port floored every step of exp and
ln, came back 8 ULPs low on each round trip, and lost a digit per decade of
N. Rounding to nearest with guard bits fixed it, and the ladder is where
that showed.

Subtraction is worse. An amortising loan is `b = b·(1+r) − payment` every
day, and near payoff the balance is a small difference of two large
numbers. At N = 365, one payment before the loan clears, WAD libraries are
down to 15 digits [amortise, N = 365, solady] and FP127 to 34 [amortise,
N = 365, fp127]. Fifteen digits of a $840 balance is still fine. Fifteen
digits of a position that is a basis point from liquidation across a
million accounts is not, and the ladder is where you find out which case
you are in.

The arithmetic for N = 365: 60 fractional bits minus log2(365) ≈ 8.5 bits
of accumulated rounding leaves 51 bits, about 15.5 decimal digits, which is
what the table shows.

The ladder measures each cell twice, and the second measurement says where
the loss comes from. Against the exact inputs, FP127 is right to 36 digits
after a year of daily compounding; against the inputs as the format rounds
them, it is right to 40, the cap [compound, N = 365, fp127, digitsFormat].
Every digit FP127 loses on that scenario is the rate's rounding to 2^-128,
applied once and carried N times; the multiplications themselves lose
nothing the measurement can see. The WAD libraries lose part of theirs the
same way, 16 against exact inputs and 19 against rounded ones at N = 365
[compound, N = 365, solady], and the rest to the arithmetic.

## What it costs

Per op, inline library form, median over the gas ladder [gas.json, lib]:

| op | FP127 | FP256 | Quad | Solady | PRBMath | ABDK | Balancer |
|---|---:|---:|---:|---:|---:|---:|---:|
| mul | 531 | 1,366 | 1,036 | 321 | 641 | 455 | 471 |
| div | 981 | 2,115 | 1,209 | 329 | 705 | 546 | 512 |
| exp | 5,366 | 7,145 | 6,072 | 547 | 2,951 | 3,542 | 1,191 |
| ln | 1,035 | 6,882 | 1,927 | 731 | 1,099 | 7,340 | 1,358 |
| sqrt | 3,632 | 2,794 | 1,205 | 622 | 1,402 | 1,159 | 2,520 |
| pow | 6,654 | 10,916 | 23,879 | 1,605 | 10,062 | 1,932 | 2,412 |
| normCdf | 23,487 | — | — | — | — | — | — |

Multiplication and division cost about what they cost in WAD. The
transcendentals cost more because they compute twice as many bits, and the
error function family is the honest expensive one. The floats, FP256 and
Quad, pay for their moving point on every add and several times over on
pow; FP256's root is cheaper than FP127's because it starts from a native
integer root. Through the deployed objects add a `staticcall`, about 700
gas, per op.

## What it does not fix

Range, and the floor. FP127 tops out near 1.7·10^38 and its grid stops at
2^-128: exp(89) reverts and exp(-89) is zero, Uniswap's top tick
1.0001^887272 is one bit past the word, and a result of 10^-30 has eight
digits on the grid however exact the op was [edges: exp, pow, sqrt]. A
fixed point maximises precision inside a band; a float maximises the band.
ABDKMathQuad, the first float in the tables, holds 34 digits at every edge
and 29 to 33 on every ladder, with half the word idle; FP256, the
[second ruler](/library/fp256/), fills the word and holds 71 at the edges and 40 to
70 on the ladders. The [edges](/results/edges/) page shows all three sides. FP127 is for the maths in the
middle, the rate, the price, the ratio, the exponent, where it holds 38
digits against the float's 34, and the conversion back to wei is one
`toFixed18` at the edge. It is not a replacement for the integer
arithmetic of a transfer, and it is not cheap enough to put in a path that
does not need the digits.

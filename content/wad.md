+++
title = "WAD"
description = "Every established library's WAD functions on the same inputs, with BL19 and BL127 beside them, against the exact value to the last wei."
path = "results/wad"

[extra]
group = "results"
+++

Every library is scored in its own rounding direction, against the exact value. BL19 and BL127 are not WAD libraries: each is called here as a WAD user would call it, `fromFixed18` on every argument, the op, then `toFixed18Down` or `toFixed18Up`.

## Everyday inputs

200 inputs per function in its everyday range, none a round number: `exp` of −10 to 10, `ln` and the logs of 0.001 to 1,000, `pow` of 0.5 to 2 raised to −3 to 3, and products, quotients and roots of amounts up to 10<sup>9</sup> tokens.

{{ <plot chart="wad" src="home" label="Share of everyday results off by at least one wei, per function and library. The numbers are in the table below." /> }}

{{ <table name="wad.everyday" first="function · share off by a wei" heat={true} cls="loss" /> }}

BL19 and BL127 return the exact integer on every one. Every library is exact on products, quotients and roots. Hover a cell for the counts.

## The whole domain

4,000 inputs per function over everything a 256-bit word holds, weighted toward the hard cases: sizes from one wei to 10<sup>59</sup> tokens, and inputs built so the exact answer lands on or beside a whole wei (perfect squares and cubes, products that are a whole number of wei, x = ln k).

{{ <table name="wad.wei" first="function · share off by a wei" heat={true} cls="loss" /> }}

Here the integer libraries stay exact on products, quotients and roots, and BL19 and BL127 do not. BL19 holds 71 digits, so an answer past 10<sup>71</sup> wei cannot carry its last wei. A decimal that is not a binary fraction is rounded as it converts in, so an answer that should land exactly on a whole wei can land one below. For a single product, quotient or root of token amounts, integer `mulDiv` is the right tool; [Integrating](/library/integrating/) keeps the state in the format and rounds once, at the token edge.

## Reverts where the value fits

{{ <table name="wad.reverts" first="function · share reverting" heat={true} cls="loss" /> }}

Over the whole domain, a library reverts when its own range is narrower than the result: Solady's `mulWad` once x · y passes 2<sup>256</sup>, BL127 past 1.7 × 10<sup>38</sup>.

## Worst error

{{ <table name="wad.worst" first="function · worst, in wei" /> }}

The largest distance from the exact integer over the values each library returned, over the whole domain. A revert is not counted here.

## Gas

{{ <table name="wad.gas" first="function · gas per call" /> }}

Median gas of the internal call on everyday inputs; BL19's and BL127's includes their conversions (exp of −10..10, ln of 0.001..1000, pow of 0.5..2 to −3..3, products and quotients of amounts up to 10<sup>9</sup> tokens). Full counts and the method: [wad.md](https://github.com/securedataresearch/blockulator/blob/master/docs/benchmarks/wad.md); data: [wad.json](/data/wad.json).

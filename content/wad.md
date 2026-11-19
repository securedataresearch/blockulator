+++
title = "WAD"
description = "Every established library's WAD functions on the same inputs, with BL19 and BL127 beside them, against the exact value to the last wei."
path = "results/wad"

[extra]
group = "results"
+++

Every library is scored in its own rounding direction, against the exact value: is the integer it returns the right one, and does it return one wherever the value fits.

BL19 and BL127 are not WAD libraries. Each is called here as a WAD user would call it: `fromFixed18` on every argument, the op, then `toFixed18Down` or `toFixed18Up`. On `exp`, `ln`, the logs, `pow` and Lambert W they are off by a wei far less often than Solady or PRBMath. On a single product, quotient or root the WAD libraries are exact and BL19 and BL127 are not: converting an 18-decimal number in rounds it, so a result that should land exactly on a wei can land one below. That is why [Integrating](/library/integrating/) keeps the state in the format and rounds once, at the token edge.

{{ <plot chart="wad" src="home" label="Share of results off by at least one wei, per function and library. The numbers are in the tables below." /> }}

## Off by a wei

{{ <table name="wad.wei" first="function · share off by a wei" heat={true} cls="loss" /> }}

The share of the values each library returns that are not the exact integer in its own direction. Hover a cell for the counts.

## Reverts where the value fits

{{ <table name="wad.reverts" first="function · share reverting" heat={true} cls="loss" /> }}

The inputs run from one wei to the top of a 256-bit word. A library reverts here when its own range is narrower than the result: Solady's `mulWad` once x · y passes 2<sup>256</sup>, BL127 past 1.7 × 10<sup>38</sup>.

## Worst error

{{ <table name="wad.worst" first="function · worst, in wei" /> }}

The largest distance from the exact integer over the values each library returned. A revert is not counted here.

## Gas

{{ <table name="wad.gas" first="function · gas per call" /> }}

Median gas of the internal call on everyday inputs; BL19's and BL127's includes their conversions (exp of −10..10, ln of 0.001..1000, pow of 0.5..2 to −3..3, products and quotients of amounts up to 10<sup>9</sup> tokens). Full counts and the method: [wad.md](https://github.com/securedataresearch/blockulator/blob/master/docs/benchmarks/wad.md); data: [wad.json](/data/wad.json).

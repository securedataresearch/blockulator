+++
title = "WAD"
description = "Every established library's WAD functions on the same inputs, with BL19 and BL127 beside them, against the exact value to the last wei."
path = "results/wad"

[extra]
group = "results"
+++

Every library is scored in its own rounding direction: a result is wrong if it is not the integer that direction gives, if it reverts where the value fits, or if it returns a value where none fits.

BL19 and BL127 are not WAD libraries. Each is called here as a WAD user would call it: `fromFixed18` on every argument, the op, then `toFixed18Down` or `toFixed18Up`. On `exp`, `ln`, the logs, `pow` and Lambert W they are off by a wei far less often than Solady or PRBMath. On a single product, quotient or root the WAD libraries are exact and BL19 and BL127 are not: converting an 18-decimal number in rounds it, so a result that should land exactly on a wei can land one below. That is why [Integrating](/library/integrating/) keeps the state in the format and rounds once, at the token edge.

{{ <plot chart="wad" src="home" label="Share of results off by at least one wei, per function and library. The numbers are in the tables below." /> }}

## Share wrong

{{ <table name="wad.wrong" first="function · share wrong" heat={true} cls="loss" /> }}

Hover a cell for the counts: how many were wrong, how many reverted where the value fits, and the direction scored.

## Worst error

{{ <table name="wad.worst" first="function · worst, in wei" /> }}

The largest distance from the exact integer over the values each library returned. A revert counts as wrong above, not here.

## Gas

{{ <table name="wad.gas" first="function · gas per call" /> }}

Median gas of the internal call on everyday inputs; BL19's and BL127's includes their conversions (exp of −10..10, ln of 0.001..1000, pow of 0.5..2 to −3..3, products and quotients of amounts up to 10<sup>9</sup> tokens). Full counts and the method: [wad.md](https://github.com/securedataresearch/blockulator/blob/master/docs/benchmarks/wad.md); data: [wad.json](/data/wad.json).

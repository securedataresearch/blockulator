+++
title = "WAD"
description = "Every established library's WAD functions on the same everyday inputs, with BL19 and BL127 beside them, against the exact value to the last wei."
path = "results/wad"

[extra]
group = "results"
+++

Every library is scored in its own rounding direction, against the exact value. BL19 and BL127 are not WAD libraries: each is called here as a WAD user would call it, `fromFixed18` on every argument, the op, then `toFixed18Down` or `toFixed18Up`.

200 inputs per function in its everyday range, none a round number: `exp` of −10 to 10, `ln` and the logs of 0.001 to 1,000, `pow` of 0.5 to 2 raised to −3 to 3, and products, quotients and roots of amounts up to 10<sup>9</sup> tokens.

{{ <plot chart="wad" src="home" label="Share of everyday results off by at least one wei, per function and library. The numbers are in the table below." /> }}

## Off by a wei

{{ <table name="wad.everyday" first="function · share off by a wei" heat={true} cls="loss" /> }}

BL19 and BL127 return the exact integer on every one. Every library is exact on products, quotients and roots; for a single one of those on token amounts, integer `mulDiv` is the cheaper tool. Hover a cell for the counts.

## Worst error

{{ <table name="wad.worst" first="function · worst, in wei" /> }}

The largest distance from the exact integer over each library's results.

## Gas

{{ <table name="wad.gas" first="function · gas per call" /> }}

Median gas of the internal call on the same inputs; BL19's and BL127's includes their conversions. The method, and a sweep of each function's whole domain: [wad.md](https://github.com/securedataresearch/blockulator/blob/master/docs/benchmarks/wad.md); data: [wad.json](/data/wad.json).

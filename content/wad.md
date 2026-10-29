+++
title = "WAD"
description = "BlockulatorWad and every established library's WAD functions, on the same inputs, against the exact value to the last wei."
path = "results/wad"

[extra]
group = "results"
+++

Every library is scored in its own rounding direction: a result is wrong if it is not the integer that direction gives, if it reverts where the value fits, or if it returns a value where none fits. BlockulatorWad computes each function in BL19 and decides the last wei exactly.

{{ <plot chart="wad" src="home" label="Share of results off by at least one wei, per function and library; BlockulatorWad is at 0 on every function. The numbers are in the tables below." /> }}

## Share wrong

{{ <table name="wad.wrong" first="function · share wrong" heat={true} cls="loss" /> }}

Hover a cell for the counts: how many were wrong, how many reverted where the value fits, and the direction scored.

## Worst error

{{ <table name="wad.worst" first="function · worst, in wei" /> }}

The largest distance from the exact integer over the values each library returned. A revert counts as wrong above, not here.

## Gas

{{ <table name="wad.gas" first="function · gas per call" /> }}

Median gas of the internal call on everyday inputs (exp of −10..10, ln of 0.001..1000, pow of 0.5..2 to −3..3, products and quotients of amounts up to 10<sup>9</sup> tokens). Full counts and the method: [wad.md](https://github.com/securedataresearch/blockulator/blob/master/docs/benchmarks/wad.md); data: [wad.json](/data/wad.json).

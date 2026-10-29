+++
title = "Deployed"
description = "Aave v3 and Morpho Blue as deployed on mainnet, against the formula each says it computes."
path = "results/deployed"

[extra]
group = "results"
+++

Each case is one accrual: a balance, a rate and the seconds since the last update. The deployed integer maths, recompiled from pinned sources and checked byte for byte against mainnet, gives the new balance. 200-digit arithmetic gives the formula the protocol states: Aave's e<sup>rate·years</sup> for borrows and per-second compounding for supply, and Morpho's e<sup>∫rate</sup> along its adaptive curve's own stated rate path. BL127 and BL19 compute that same formula from the same integers.

Normal operation is accurate: the deployed interest is right to within the token's own decimals. The digits go where the stated formula and the shipped shortcut diverge: a fully used market left alone for a day or a week, a rate at its cap.

{{ <plot chart="deployed" label="Correct digits of the interest for each stylised case, as deployed and in BL127 and BL19; the numbers are in the table below." /> }}

{{ <table name="deployed" first="case" /> }}

Hover a case for its parameters. *Off by* is deployed minus the stated formula, in tokens: negative is less interest than the formula. Most of Morpho's error after a day or a week idle is not in a library call: its adaptive curve integrates the rate with a two-panel trapezoid, which overcharges while the rate at target moves.

## Every live market

{{ <plot chart="live" label="Correct digits of the pending interest for every live Aave reserve side and Morpho market at the survey block, as deployed and in BL127." /> }}

The pending accrual of every Aave v3 reserve side (74) and every Morpho Blue market (252) at the survey block, with the harness reproducing each deployed result exactly. Live intervals are short, so these are high. The provenance, the claims quoted from each protocol's source and the split of every error into approximation and rounding: [accrual-deployed.md](https://github.com/securedataresearch/blockulator/blob/master/docs/benchmarks/accrual-deployed.md).

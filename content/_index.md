+++
title = "Blockulator: the definitive source for precision"
# The description is config.toml's, the one the whole site falls back to.
template = "home.html"

[extra]
eyebrow = "Blockulator 2.2 · Secure Data Research"
headline = "The definitive source for precision."
# {fp127}, {fp19} and the other {placeholders} below are filled from static/data/home.json (templates/macros.html fill).
sub = "Two Solidity math libraries that keep {fp127} and {fp19} correct digits where WAD keeps 18, so interest, prices and payouts stay right to the last wei. Use them when large sums are at stake or the call is free."
cta_primary_text = "See the results"
cta_primary_href = "/results/"
cta_secondary_text = "Use the library"
cta_secondary_href = "/library/"

accrual_title = "Leave a market alone and its interest goes wrong"
accrual_note = "Put $10,000 in at 5% a year and accrue it in one step after N days. Aave and Morpho approximate e<sup>x</sup> with three terms, so the longer a market waits for an update, the fewer digits survive: after 10,000 days, one. FP127 and FP19 lose less than two digits over the whole range."
accrual_source = "Correct digits against exact arithmetic, each capped at what the library's format holds. OpenZeppelin, Uniswap and Maker have no exponential, so they are not here. The input is the <a href=\"/results/ladder/#accrual-continuous\">continuous-accrual scenario</a>'s; data: <a href=\"/data/ladder.json\">ladder.json</a>."

gas_title = "Twice the digits, and competitive on gas"
gas_note = "FP127 carries twice the digits of every 18-decimal library and costs less than PRBMath's SD59x18 on add, mul, div, exp, ln, pow and sqrt. FP19 carries twice binary128's digits and costs less than ABDKMathQuad on add, mul, div, exp, ln and pow. Solady is cheaper than both, at 18 digits."
gas_source = "Each dot is a library: the digits its format holds at 1, against its gas as a multiple of FP127's over the ops both offer; hover for the range. Median of inline calls over random inputs that take no shortcut (<sup>t</sup>). Aave, Morpho and Maker are formulas inside protocols, so they have no gas. Every op: <a href=\"/results/ops/\">per op</a>; data: <a href=\"/data/gas.json\">gas.json</a>, <a href=\"/data/fp19/gas.json\">fp19/gas.json</a>."

wad_title = "Correct to the last wei"
wad_note = "BlockulatorWad keeps Solady's function names and returns the exact answer, rounded the way each function promises, on all {n} results we tested across {fns} functions and rounding directions. The libraries it replaces are a wei off on up to {worst}% of their results for some functions."
wad_source = "Seeded inputs over each function's domain, including those whose exact value sits next to a wei boundary. Every library here is 18-decimal fixed point."

ask_title = "Use FP127 and FP19."
ask_text = "Both are a <code>forge install</code> away. Integration engineering is free."
ask_primary_text = "Email us"
ask_primary_href = "mailto:sam@securedataresearch.net?subject=Blockulator%20integration"
ask_secondary_text = "Read the write-up"
ask_secondary_href = "/writeup/"

more_title = "Everything else we measured"
[[extra.more]]
label = "scenarios"
title = "{scenarios} real calculations, up to 10,000 steps"
text = "Compounding, loans, bonding curves, option pricing and decay, run in every library and checked against 300-digit arithmetic."
href = "/results/ladder/"

[[extra.more]]
label = "edges"
title = "{probes} calls where formats break"
text = "Tiny and huge arguments and the ends of each domain, across {ops} ops: which libraries return zero, revert or lose every digit."
href = "/results/edges/"

[[extra.more]]
label = "in production"
title = "Aave and Morpho as deployed"
text = "The live markets' own accrual against the formula each says it computes."
href = "/results/deployed/"

[[extra.more]]
label = "incidents"
title = "Four exploits, replayed"
text = "Real attacks rerun from their own transactions, and what would have stopped each one."
href = "/results/incidents/"

[[extra.steps]]
label = "two formats"
title = "{fp127} digits fixed, {fp19} floating"
href = "/why/#where-the-bits-go-in-wad"
text = "FP127 is fixed point with 128 bits after the point. FP19 is a 256-bit float that reaches 10<sup>±78,913</sup>. WAD gives the fraction 60 bits."

[[extra.steps]]
label = "measured"
title = "Against 300-digit arithmetic"
href = "/results/"
text = "FP127, FP19 and {others} other libraries, run through {scenarios} scenarios of up to 10,000 steps each."

[[extra.steps]]
label = "two forms"
title = "Deploy it or inline it"
href = "/library/"
text = "Each format is one Yul source, built into a deployed contract and an inline library that are fuzzed equal on every int256."

[[extra.steps]]
label = "trust"
title = "No owner, no upgrades"
text = "No contract has storage, a proxy or an admin key. A new version gets a new address, and the old ones stay."

+++

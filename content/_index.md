+++
title = "Blockulator: the definitive source for precision"
# The description is config.toml's, the one the whole site falls back to.
template = "home.html"

[extra]
eyebrow = "Blockulator 2.2 · Secure Data Research"
headline = "The definitive source for precision."
sub = "Blockulator brings real scientific calculations to the blockchain with convergent iterations. It is the perfect companion for smart contracts, agents, and browser applications."
cta_primary_text = "See the results"
cta_primary_href = "/results/"
cta_secondary_text = "Use the library"
cta_secondary_href = "/library/"
ask_title = "Use FP127 and FP19."
ask_text = "Both are a <code>forge install</code> away. Integration engineering is free."
ask_primary_text = "Email us"
ask_primary_href = "mailto:sam@securedataresearch.net?subject=Blockulator%20integration"
ask_secondary_text = "Read the write-up"
ask_secondary_href = "/writeup/"
gas_title = "Twice the digits, at the same gas"
gas_note = "Each library at the digits its format holds at 1, against its gas as a multiple of FP127's on the same ops. FP19 carries twice binary128's digits, FP127 twice every fixed-point library's, at the gas of the WAD libraries in the middle. Hover a dot for the range over its ops; the table has every op."
gas_source = "Inline calls over random inputs that take no shortcut (<sup>t</sup>) or the op's input ladder. Aave, Morpho and Maker are formulas inside protocols, not libraries, so they have no gas row. Every op: <a href=\"/results/ops/\">per op</a>; data: <a href=\"/data/gas.json\">gas.json</a>, <a href=\"/data/fp19/gas.json\">fp19/gas.json</a>."
accrual_title = "Leave a market alone and its interest goes wrong"
accrual_note = "$10,000 at 5% APR, accrued in one step after N days without an update, against exact arithmetic. Aave and Morpho ship a three-term expansion of e<sup>x</sup> and fall to one digit; the other libraries keep what their format holds, which sets how far each can be trusted."
accrual_source = "The reference input of the <a href=\"/results/ladder/#accrual-continuous\">continuous-accrual scenario</a>; each library's digits are capped at what its format holds. OpenZeppelin, Uniswap and Maker have no exponential, so they are not in it. Data: <a href=\"/data/ladder.json\">ladder.json</a>."
wad_title = "Correct to the last wei"
wad_note = "The share of results off by at least one wei, one dot per library, against the exact value rounded in each library's own direction. BlockulatorWad keeps Solady's names and is wrong on none: 0 of {n} results across {fns} functions and rounding directions."
wad_source = "Seeded inputs over each function's domain, including those whose exact value sits next to a wei boundary. Every library here is 18-decimal fixed point."
ladder_title = "Every scenario, every library"
ladder_note = "Median correct digits after the last step of each of {scenarios} scenarios: compounding, amortising, bonding curves, option pricing, decay. Floating point on the left, fixed point on the right; a dash is a library with no model for that scenario, or one that reverts on it."
ladder_source = "N up to 10,000 steps, each against 300-digit arithmetic; the step-by-step chart for each scenario is on <a href=\"/results/ladder/\">the ladder</a>. Data: <a href=\"/data/ladder.json\">ladder.json</a>."
edges_title = "At the edges of each format"
edges_note = "{probes} probes across {ops} ops where formats break: tiny and huge arguments, values next to a format's floor, the ends of each domain. Each bar counts a library's probes: to the left of zero the ones it fails (out of range, reverted, sent to zero, or no correct digit), to the right the ones it computes, by the digits it keeps."
edges_source = "Each probe is one op evaluated once, against 200-digit arithmetic. Every probe: <a href=\"/results/edges/\">the edges</a>; data: <a href=\"/data/edges.json\">edges.json</a>."

[[extra.steps]]
label = "the word"
title = "128 fixed bits, 237 floating"
href = "/why/#where-the-bits-go-in-wad"
text = "WAD gives the fraction 60 bits. FP127 gives it 128. FP19 floats 237 significant bits out to 10<sup>±78,913</sup>."

[[extra.steps]]
label = "the ladder"
title = "Measured over N steps"
# {scenarios} and {others} are counted from static/data/home.json by templates/home.html.
text = "FP127, FP19 and {others} other libraries, {scenarios} scenarios, N = 1 to 10,000, against 300-digit arithmetic."

[[extra.steps]]
label = "two forms"
title = "One source each"
text = "Each is one Yul source, generated into a deployed contract and an inline library, fuzzed equal on all of int256."

[[extra.steps]]
label = "trust"
title = "No owner"
text = "No contract has storage, a proxy or an upgrade. A change is a new salt and a new address."

+++

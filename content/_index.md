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
chart_title = "Leave a market alone and its interest goes wrong"
chart_scenario = "accrual-continuous"
chart_note = "$10,000 at 5% APR, accrued in one step after N days without an update. Aave and Morpho ship a three-term expansion of e<sup>x</sup>: {proto365} correct digits after a year ({proto365i} of the interest alone), {proto10k} after 10,000 days, ${short} short. FP127 keeps {fp127}, FP19 {fp19}."
ask_title = "Use FP127 and FP19."
ask_text = "Both are a <code>forge install</code> away. Integration engineering is free."
ask_primary_text = "Email us"
ask_primary_href = "mailto:sam@securedataresearch.net?subject=Blockulator%20integration"
ask_secondary_text = "Read the write-up"
ask_secondary_href = "/writeup/"
pitch_title = "Twice the digits, at the same gas"
pitch_note = "One <code>int256</code> per number, every op tested against exact arithmetic. FP19 carries twice binary128's digits, FP127 twice PRBMath's, and the gas sits next to them."
wad_title = "Correct to the last wei"
wad_functions = ["expWad", "lnWad", "powWad"]
wad_note = "The WAD libraries round exp, ln and pow wrong on {lo}–{hi}% of inputs, by at least one wei. BlockulatorWad keeps Solady's names and is wrong on none: 0 of {n} results across {fns} functions and rounding directions."
wad_source = "Seeded inputs over each function's domain, including those whose exact value sits next to a wei boundary; each library scored against the exact value in its own rounding direction."

[[extra.steps]]
label = "the word"
title = "128 fixed bits, 237 floating"
href = "/why/#where-the-bits-go-in-wad"
text = "WAD gives the fraction 60 bits. FP127 gives it 128. FP19 floats 237 significant bits out to 10<sup>±78,913</sup>."

[[extra.steps]]
label = "the ladder"
title = "Measured over N steps"
# {scenarios}, {inputs} and {others} are counted from static/data/ladder.json by templates/home.html.
text = "FP127, FP19 and {others} other libraries, {scenarios} scenarios, {inputs} inputs, N = 1 to 10,000, against 300-digit arithmetic."

[[extra.steps]]
label = "two forms"
title = "One source each"
text = "Each is one Yul source, generated into a deployed contract and an inline library, fuzzed equal on all of int256."

[[extra.steps]]
label = "trust"
title = "No owner"
text = "No contract has storage, a proxy or an upgrade. A change is a new salt and a new address."

+++

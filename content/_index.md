+++
title = "blockulator"
description = "Blockulator 2.0 by Secure Data Research: FP127, 38 digits at 1 for the money range, and FP256, 71 digits at any magnitude, measured against ABDK, Solady, PRBMath, Balancer, Aave, Morpho and Maker."
template = "home.html"

[extra]
eyebrow = "Blockulator 2.0 · Secure Data Research"
headline = "Dust is Over."
sub = "Two rulers for EVM arithmetic: FP127 for the money range, FP256 for everything. Round once; never run out of ruler."
cta_primary_text = "See the results"
cta_primary_href = "/results/"
cta_secondary_text = "Use the library"
cta_secondary_href = "/library/"
chart_title = "Correct digits left after N steps"
chart_note = "$10,000 at 10% APR, one multiplication a day, out to 10,000 days. After a year: FP256 {fp256}, FP127 {fp127}, WAD {wad}."
ask_title = "Use FP127 and FP256."
ask_text = "Both are a <code>forge install</code> away. Integration engineering is free."
ask_primary_text = "Email us"
ask_primary_href = "mailto:sam@securedataresearch.net?subject=Blockulator%20integration"
ask_secondary_text = "Read the write-up"
ask_secondary_href = "/writeup/"
limits_title = "Limits"

[[extra.steps]]
label = "the word"
title = "128 fixed bits, 237 floating"
href = "/why/#where-the-bits-go-in-wad"
text = "WAD gives the fraction 60 bits. FP127 gives it 128. FP256 floats 237 significant bits out to 10^±78,913."

[[extra.steps]]
label = "the ladder"
title = "Measured over N steps"
# {scenarios}, {inputs} and {others} are counted from static/data/ladder.json by templates/home.html.
text = "FP127, FP256 and {others} other libraries, {scenarios} scenarios, {inputs} inputs, N = 1 to 10,000, against 300-digit arithmetic."

[[extra.steps]]
label = "two forms"
title = "One source each"
text = "Each is one Yul source, generated into a deployed contract and an inline library, fuzzed equal on all of int256."

[[extra.steps]]
label = "trust"
title = "No owner"
text = "No contract has storage, a proxy or an upgrade. A change is a new salt and a new address."

# Limits: terse facts, each from committed data. {gas} is filled by templates/home.html from
# static/data/gas.json: FP127Lib over Solady median gas for mul, div, exp, ln and pow.
[[extra.limits]]
label = "gas"
title = "Solady is {gas}× cheaper"
text = "Per op than FP127 inline: median gas for mul, div, exp, ln and pow."

[[extra.limits]]
label = "FP256 range"
title = "10^±78,913"
text = "Past it a result reverts, or rounds to zero below."

[[extra.limits]]
label = "FP127 range"
title = "±1.7 × 10^38"
text = "A fixed grid: 38 digits at 1, 32 at 10^−6, 8 at 10^−30."

[[extra.limits]]
label = "status"
title = "Sepolia only"
text = "No mainnet deployment. Not audited."

[[extra.limits]]
label = "two forms"
title = "Fuzzed equal, not proven"
text = "Object and inline library agree on every fuzzed input. No formal proof."
+++

+++
title = "blockulator"
description = "Blockulator 2.0 by Secure Data Research: FP127, 38 digits for the money range, and FP256, 71 digits at any magnitude, measured against ABDK, Solady, PRBMath, Balancer, Aave, Morpho and Maker."
template = "home.html"

[extra]
eyebrow = "Blockulator 2.0 · Secure Data Research"
headline = "Dust is Over."
sub = "Two rulers for EVM arithmetic: FP127 for the money range, FP256 for everything. Round once; never run out of ruler."
cta_primary_text = "See the results"
cta_primary_href = "/results/"
cta_secondary_text = "Use the library"
cta_secondary_href = "/library/"
chart_title = "A year of daily compounding"
chart_note = "$10,000 at 10% APR, one multiplication per day. Correct digits left after 365 steps."
ask_title = "Use FP127 and FP256."
ask_text = "Both are a <code>forge install</code> away. Integration engineering is free."
ask_primary_text = "Email us"
ask_primary_href = "mailto:sam@securedataresearch.net?subject=Blockulator%20integration"
ask_secondary_text = "Read the write-up"
ask_secondary_href = "/writeup/"

[[extra.steps]]
label = "the word"
title = "128 fractional bits"
text = "WAD gives the fraction 60 bits and the rest to overflow headroom. FP127 gives it 128."

[[extra.steps]]
label = "the ladder"
title = "Measured over N steps"
text = "13 scenarios, 87 inputs, 10 libraries, N = 1 to 10,000, against 200-digit arithmetic."

[[extra.steps]]
label = "two forms"
title = "One source"
text = "A deployed object and an inline library, generated from the same Yul and proven equal on all of int256."

[[extra.steps]]
label = "trust"
title = "No owner"
text = "No storage, no proxy, no upgrade. A change is a new salt and a new address."
+++

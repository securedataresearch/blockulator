+++
title = "blockulator"
description = "FP127: 38-digit fixed-point math for the EVM, and FP256, a 71-digit float, measured against ABDK, Solady, PRBMath, Balancer, Aave, Morpho and Maker."
template = "home.html"

[extra]
headline = "38 digits where WAD keeps 18."
sub = "FP127 is 127.128 fixed point in one int256: 49 ops, deployed on Sepolia, inlinable from Solidity. FP256 is its 71-digit float sibling."
cta_primary_text = "See the results"
cta_primary_href = "/results/"
cta_secondary_text = "Use the library"
cta_secondary_href = "/library/"
chart_title = "A year of daily compounding"
chart_note = "$10,000 at 10% APR, one multiplication per day. Correct digits left after 365 steps."
ask_title = "Looking for three testnet integrations and one audit partner."
ask_text = "The inline library is a <code>forge install</code> away. Integration engineering is free."
ask_primary_text = "Email us"
ask_primary_href = "mailto:sam@securedataresearch.net?subject=FP127%20integration"
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

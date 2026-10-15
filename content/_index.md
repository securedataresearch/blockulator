+++
title = "blockulator"
description = "FP127: 38 decimal digits of fixed-point math for the EVM, measured against ABDK, Solady and PRBMath."
template = "home.html"

[extra]
headline = "128-bit fixed point for the EVM."
sub = "FP127 is a signed 127.128 fixed-point library: one int256, 38 decimal digits, 49 operations, deployed on Sepolia and usable inline from Solidity. This site measures it against ABDK (64.64 and binary128), Solady, PRBMath, Balancer and the accrual maths of Aave, Morpho and Maker, one step at a time, and shows the method."
cta_primary_text = "The measurements"
cta_primary_href = "/demo/"
cta_secondary_text = "The library"
cta_secondary_href = "/library/"
steps_title = "What it is"
tiles_title = "On this site"
ask_title = "Three protocols to integrate it on testnet. One partner to fund the audit."
ask_text = "FP127 is deployed on Sepolia and the inline library is a <code>forge install</code> away. Our engineering time for a testnet integration is at no charge."
ask_primary_text = "Email us"
ask_primary_href = "mailto:sam@securedataresearch.net?subject=FP127%20integration"
ask_secondary_text = "Read the write-up"
ask_secondary_href = "/writeup/"

[[extra.steps]]
label = "the word"
title = "128 fractional bits."
text = "WAD spends 60 bits of the word on the fraction and the rest on overflow headroom. FP127 spends 128 on the fraction, 127 on the integer, one on the sign."

[[extra.steps]]
label = "the ladder"
title = "Measured over N steps."
text = "Thirteen scenarios, 87 inputs, nine libraries, N from 1 to 10,000, every cell against 200-digit arithmetic, twice: from the exact inputs and from the inputs as each format rounds them."

[[extra.steps]]
label = "two forms"
title = "One source, agree by construction."
text = "A deployed object at a CREATE2 address with a published salt, and a Solidity library with the same Yul in assembly blocks. Proven equal on the full int256 domain."

[[extra.steps]]
label = "trust"
title = "No storage, no owner."
text = "Nothing to freeze, nothing to upgrade. A change is a new salt and a new address, recorded in the repository. Verified on Sourcify as an exact match."

[[extra.pages]]
name = "Demo"
tag = "the terminal-precision ladder, every cell checkable live"
href = "/demo/"
site = "/demo/"
color = "emerald"

[[extra.pages]]
name = "Why"
tag = "where WAD loses its bits, and why iteration is what breaks it"
href = "/why/"
site = "/why/"
color = "gold"

[[extra.pages]]
name = "Library"
tag = "address, ABI, encoding, the inline snippet, the op table"
href = "/library/"
site = "/library/"
color = "sapphire"

[[extra.pages]]
name = "Float"
tag = "FP256, the second ruler: 71 digits at any magnitude, one word"
href = "/float/"
site = "/float/"
color = "sapphire"

[[extra.pages]]
name = "Compare"
tag = "gas and single-op precision against ABDK, Solady, PRBMath"
href = "/compare/"
site = "/compare/"
color = "red"

[[extra.pages]]
name = "Write-up"
tag = "the whole story, in the first person, with sources"
href = "/writeup/"
site = "/writeup/"
color = "emerald"
+++

The common EVM math libraries store a value to about 18 decimal places. That is enough for one multiplication and not for a loop: a lending protocol accrues every block, and after N steps the rounding has been applied N times. The [ladder](/demo/) runs thirteen such loops through ABDKMath64x64, ABDKMathQuad, Solady, PRBMath, Balancer, Aave, Morpho, Maker and FP127 for 87 inputs, against exact arithmetic, and counts the digits that survive at each N. It also separates what the number format costs from what the arithmetic costs, and every cell can be re-run on Sepolia.

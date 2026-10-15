+++
title = "Edges"
description = "One call at the end of each library's domain: where a result goes to zero, reverts, or runs out of digits, through ten libraries against 300-digit arithmetic, checkable on Sepolia."
template = "edges.html"
+++

The [ladder](/demo/) measures a slope: digits lost one step at a time. This page measures the cliffs. Each probe is one op evaluated once where a domain ends: a logarithm within a per-second rate of one, an exponential of −42, a probability of one in 10^18, a base a hair above one raised to a year of seconds, the tail of the normal distribution where an option's price lives. Every library runs the probe in its own representation and the result is compared with the exact value; a cell either has digits or says how the library had no answer: **zero** where the result fell below the format's floor, **revert** with the reason, **range** when the argument does not fit the word, **n/a** when the library has no way to compute the op. FP127's own ends are on the page too: exp at ±88, the word at 1.7 × 10^38, the tail of erfc at 9.3.

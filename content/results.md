+++
title = "Results"
description = "Correct digits left after 10,000 steps, per scenario and library."
template = "results.html"
path = "results"

[extra]
group = "results"
n = 10000
+++

A scenario is a calculation protocols really run (daily interest, a loan, a bonding curve) repeated N times in each library's own number format. Each result is compared with the same loop in 300-digit arithmetic, and the score is how many digits are still correct. After 10,000 days of daily compounding, FP19 keeps 67.4 digits, FP127 34.8 and Solady 14.8.

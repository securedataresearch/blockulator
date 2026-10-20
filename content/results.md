+++
title = "Results"
description = "Correct digits left after 10,000 steps, per scenario and library."
template = "results.html"
path = "results"

[extra]
group = "results"
n = 10000
+++

Each scenario repeats one step N times in every library's own representation and compares the result with the same loop in 300-digit arithmetic. Daily compounding: FP127 keeps 34 digits, Solady 14. The per-second accrual a lending market runs: 29 against 8.5.

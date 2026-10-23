+++
title = "Results"
description = "Correct digits left after 10,000 steps, per scenario and library."
template = "results.html"
path = "results"

[extra]
group = "results"
n = 10000
+++

Each scenario repeats one step N times in every library's own representation and compares the result with the same loop in 300-digit arithmetic. Daily compounding: FP127 keeps 34.8 digits, Solady 14.8. Per-second accrual, which Maker compounds with rpow: Maker keeps 18.3, FP127 29.8 and FP256 71.2. FP127's 29.8 is the rate's own rounding: a per-second rate floored to 2<sup>−128</sup> holds about 29 digits, and against the rate as the format holds it FP127 keeps 40.

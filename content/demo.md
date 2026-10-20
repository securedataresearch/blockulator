+++
title = "Ladder"
description = "13 scenarios, 87 inputs, N from 1 to 10,000, every cell against 300-digit arithmetic."
template = "demo.html"
path = "results/ladder"
aliases = ["/demo/"]

[extra]
group = "results"
+++

Each scenario is measured twice: against the exact inputs, which is what a protocol sees, and against the inputs as each format rounds them, which isolates the arithmetic. The chart covers every input; the table below it is the reference input, cell by cell.

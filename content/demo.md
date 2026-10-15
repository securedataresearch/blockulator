+++
title = "Terminal precision"
description = "Thirteen scenarios, 87 inputs, nine libraries, N from 1 to 10,000, every cell against 200-digit arithmetic and checkable on Sepolia."
template = "demo.html"
+++

Each scenario is N identical steps run through each library in its native representation, for several inputs, against the same loop in exact arithmetic. It is measured twice: against the exact inputs, which is what a protocol sees, and against the inputs as each format rounds them, which isolates the library's arithmetic. The chart is the summary over all inputs; the table is the reference input in full, and every cell of it can be re-run on Sepolia. "How this was measured" defines every number.

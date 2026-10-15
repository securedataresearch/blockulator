+++
title = "Compare"
description = "Gas and single-op precision for FP127 against ABDKMath64x64, ABDKMathQuad, Solady, PRBMath and Balancer."
+++

The [ladder](/demo/) is the argument: precision over N steps, which is how protocols use a math library. This page is the per-op view behind it, measured by the same Foundry suites that CI runs on every commit.

## Gas per op

{{ <gastable repo={config.extra.repo} /> }}

Multiplication and division cost about what they cost in WAD. The transcendentals cost more because they compute twice as many bits.

## Precision per op

{{ <precisiontable /> }}

Integer, rounding and comparison ops are bit-exact, and so are `ln`, `log2` and `log10` to within one ULP of the truth; `exp`, `exp2` and `exp10` hold 146 bits or better, the limit of their degree-24 polynomial. The transcendentals compute with 64 guard bits and round to nearest once, so their error has no sign bias and iterated calls do not drift. The two Lambert W branches lose bits only within 2^-20 of the branch point at −1/e, where the slope is infinite and one ULP of input moves the output by 2^-63; everywhere else they measure 126 to 128 bits.

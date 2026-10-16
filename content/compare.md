+++
title = "Per op"
description = "Gas and single-call precision for FP127 against ABDK, Quad, Solady, PRBMath and Balancer."
path = "results/ops"
aliases = ["/compare/"]

[extra]
group = "results"
+++

## Gas per op

{{ <gastable repo={config.extra.repo} /> }}

`mul` and `div` cost about what they cost in WAD. The transcendentals cost more because they compute twice the bits. Quad and FP256 ([its table](/library/fp256/#the-ops)) pay for the moving point on every op. Only FP127 has `erf`, `erfc`, `normCdf` and Lambert W, and they are the expensive ones.

## Precision per op

{{ <precisiontable /> }}

- Integer, rounding and comparison ops: bit-exact. `ln`, `log2`, `log10`: within one ULP.
- `exp`, `exp2`, `exp10`: 146 bits or better, the limit of the degree-24 polynomial.
- Transcendentals use 64 guard bits and round to nearest once, so the error has no sign bias and iterated calls do not drift.
- Lambert W: 126 to 128 bits, except within 2^−20 of the branch point at −1/e, where one ULP of input moves the output by 2^−63.
- `powu`, `compound`, `erf`, `erfc`, `normCdf`: within two ULP. `expm1`, `sinh`, `cosh`, `tanh`: 140 bits or better. `log1p`, `atanh`: one ULP.

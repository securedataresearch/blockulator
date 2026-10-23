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

Inline, `mul` costs 263 gas against the WAD libraries' 126 to 485, `div` 645 against 93 to 509. The transcendentals cost more because they compute twice the bits. Quad and FP256 ([its table](/library/fp256/#the-ops)) pay for the moving point on every op. Only FP127 and FP256 have `erf`, `erfc`, `normCdf` and W₋₁ (Solady has W₀), and they are the expensive ones.

## Precision per op

{{ <precisiontable /> }}

- Integer, rounding and comparison ops: bit-exact. `mul` and `sqrt` round down and `div` toward zero, within one ULP; "exact" in the table means equal to an oracle that rounds the same way. `ln`, `log2`, `log10`: within two ULP of the floored truth at every vector; on 4,000 random inputs `ln` was 1.31 ULP from the truth at worst, `log2` 1.88.
- `exp`, `exp2`, `exp10`: 146 bits or better, the limit of the degree-24 polynomial.
- Transcendentals use 64 guard bits and round to nearest once: `exp(ln x)` returns the same word for 10,000 steps. Above 2^16 the polynomial's 2^−146, not the rounding, sets `exp`'s error.
- Lambert W: within two ULP for x > 0 and 118 bits or better down to 2^−20 of the branch point at −1/e; 65 within it, where one ULP of input moves the output by 2^−63.
- `erf`, `normCdf`: correctly rounded on 2,000 random inputs each; `erfc` within two ULP. `powu`, `compound`: within two ULP for results below 2^104, 231 bits above. `expm1`, `sinh`, `cosh`, `tanh`: 140 bits or better. `log1p`, `atanh`: two ULP.

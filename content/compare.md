+++
title = "Per op"
description = "Gas and digits per op: FP127 and FP256 against Quad, Solady, PRBMath, ABDK and Balancer."
path = "results/ops"
aliases = ["/compare/"]

[extra]
group = "results"
+++

{{ <pitch layout="ops" /> }}

FP127's transcendentals compute twice the bits and round to the nearest word; Quad and FP256 ([its table](/library/fp256/#the-ops)) pay for the moving point on every op. Only FP127 and FP256 have `erf`, `erfc`, `normCdf` and W₋₁ (Solady has W₀), and they are the expensive ones.

## Gas per op

Every op, every library, inline unless the column says otherwise.

{{ <gastable repo={config.extra.repo} /> }}

## Precision per op

{{ <precisiontable /> }}

- Integer, rounding and comparison ops: bit-exact. `mul` and `sqrt` round down and `div` toward zero, within one ULP; "exact" in the table means equal to an oracle that rounds the same way. The directed ops round the way their names say, within one ULP.
- Every transcendental (`exp`, `ln`, `pow`, `powu`, `compound`, `cbrt`, the hyperbolics, `erf`, `erfc`, `normCdf`, both Lambert W branches) returns the nearest word at every committed vector: within half an ULP (`maxErrUlp` in the data), from guard bits and one rounding. `exp(ln x)` returns the same word for 10,000 steps. The one known exception is `pow` with an exponent near 2<sup>90</sup>.

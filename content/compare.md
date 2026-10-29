+++
title = "Per op"
description = "Gas and digits per op: FP127 and FP19 against Quad, Solady, PRBMath, ABDK and Balancer."
path = "results/ops"
aliases = ["/compare/"]

[extra]
group = "results"
+++

{{ <pitch layout="ops" /> }}

Only FP19 and FP127 offer `erf`, `erfc`, `normCdf` and both Lambert W branches (Solady has W₀ alone), each correctly rounded or the nearest word. FP19's per-op detail, with the deployed objects, is [on its page](/library/fp19/#the-ops).

## Gas per op

Every op of FP19 and FP127 against every library we compare, all called inline.

{{ <plot chart="gasops" label="Median gas per call for every op and library on a log scale, one row per op; the numbers are in the table below." /> }}

{{ <gasall /> }}

## Precision per op

{{ <precisiontable /> }}

- Integer, rounding and comparison ops: bit-exact. `mul` and `sqrt` round down and `div` toward zero, within one ULP; "exact" in the table means equal to an oracle that rounds the same way. The directed ops round the way their names say, within one ULP.
- Every transcendental (`exp`, `ln`, `pow`, `powu`, `compound`, `cbrt`, the hyperbolics, `erf`, `erfc`, `normCdf`, both Lambert W branches) is correctly rounded to nearest: each fast value carries a derived error bound and a rounding test, and a wider stage decides what the test cannot, so the word is within half an ULP (`maxErrUlp` in the data) at every committed vector and on every random input of the sweep, plain and with every test forced. `exp(ln x)` returns the same word for 10,000 steps. The `pow` exception of earlier releases (an exponent near 2<sup>90</sup>) is gone in 3.0.

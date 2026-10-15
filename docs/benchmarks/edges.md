# Edges: where each library's domain ends

Generated 2026-10-15 by `make edges`. Versions: fp127 2b291a7, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, forge forge Version: 1.7.1.

Each probe is one op evaluated once at the end of a domain, through every library in its own representation, against mpmath at 200 digits. Cells give correct digits against the exact truth (`digits`; `digitsFormat`, the signed error and the raw words are in edges.json), or how the library had no answer: **ZERO** when it returned 0 where the truth is not (the result fell below the format's floor), **REVERT** with the reason, **RANGE** when the argument does not fit the representation, **n/a** when the library has no way to compute the op. FP127Lib coincides with FP127 and is omitted. The method is in the Methodology section at the end.

## ln(x)

The logarithm near one is where a per-second rate lives: ln(1 + r) for r = 1e-9 has eight digits on an 18-decimal grid.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ln(1+1e-6)` | `1.0e-6` | 34 | 13 | 12 | 11 | 28 | 12 | n/a | n/a | n/a |
| `ln(1+1e-9)` a per-second rate | `1.0e-9` | 30 | 10 | 9 | 8 | 25 | 9 | n/a | n/a | n/a |
| `ln(1+1e-12)` | `1.0e-12` | 26 | 7 | 6 | 5 | 22 | 5 | n/a | n/a | n/a |
| `ln(1+1e-15)` | `1.0e-15` | 24 | 4 | 15 | 2 | 19 | 3 | n/a | n/a | n/a |
| `ln(1+1e-18)` the last digit of an 18-decimal grid | `1.0e-18` | 21 | 1 | 18 | ZERO | 16 | ZERO | n/a | n/a | n/a |
| `ln(1-1e-12)` | `-1.0e-12` | 26 | 6 | 12 | 5 | 24 | 12 | n/a | n/a | n/a |
| `ln(1e-18)` | `-41.446532` | 22 | 3 | 19 | 19 | 33 | 20 | n/a | n/a | n/a |
| `ln(1e-30)` | `-69.077553` | 10 | REVERT bare revert | REVERT unknown selector | REVERT unknown selector | 33 | REVERT Balancer OutOfBounds | n/a | n/a | n/a |
| `ln(1e30)` | `69.077553` | 41 | RANGE | 20 | 18 | 33 | 20 | n/a | n/a | n/a |
| `ln(1e38)` | `87.498234` | 40 | RANGE | 20 | 18 | 33 | 20 | n/a | n/a | n/a |

## exp(x)

exp below -42 is zero on an 18-decimal grid and has one digit at -40: every probability, discount or decay smaller than 1e-18 is gone.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `exp(-1e-12)` | `1.0` | 39 | 18 | 24 | 18 | 34 | 24 | n/a | n/a | n/a |
| `exp(-20)` | `2.061e-9` | 31 | 10 | 9 | 9 | 32 | 9 | n/a | n/a | n/a |
| `exp(-30)` | `9.358e-14` | 26 | 6 | 5 | 5 | 32 | 5 | n/a | n/a | n/a |
| `exp(-40)` a probability of 4e-18: one digit on an 18-decimal grid | `4.248e-18` | 21 | 2 | 1 | 1 | 32 | 1 | n/a | n/a | n/a |
| `exp(-41)` | `1.563e-18` | 21 | 1 | 0 | 0 | 32 | 0 | n/a | n/a | n/a |
| `exp(-42)` zero on an 18-decimal grid | `5.75e-19` | 21 | 1 | ZERO | ZERO | 32 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `exp(-43)` | `2.115e-19` | 21 | 0 | ZERO | ZERO | 32 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `exp(-60)` | `8.757e-27` | 13 | ZERO | ZERO | ZERO | 32 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `exp(-88)` the last value above FP127's floor | `6.055e-39` | 1 | ZERO | ZERO | ZERO | 31 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `exp(-89)` zero on FP127's grid | `2.227e-39` | ZERO | ZERO | ZERO | ZERO | 31 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `exp(-100)` | `3.72e-44` | ZERO | ZERO | ZERO | ZERO | 31 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `exp(40)` | `2.354e+17` | 43 | 19 | 20 | 16 | 32 | 21 | n/a | n/a | n/a |
| `exp(43)` | `4.728e+18` | 43 | 21 | 21 | 16 | 32 | 20 | n/a | n/a | n/a |
| `exp(44)` beyond ABDK 64.64's range | `1.285e+19` | 43 | REVERT bare revert | 20 | 16 | 32 | 20 | n/a | n/a | n/a |
| `exp(60)` | `1.142e+26` | 45 | REVERT bare revert | 20 | 16 | 32 | 20 | n/a | n/a | n/a |
| `exp(88)` the largest FP127 holds | `1.652e+38` | 44 | REVERT bare revert | 20 | 16 | 31 | 20 | n/a | n/a | n/a |
| `exp(89)` FP127 reverts; the WAD word still has room | `4.49e+38` | REVERT Overflow | REVERT bare revert | 20 | 16 | 31 | 20 | n/a | n/a | n/a |
| `exp(100)` | `2.688e+43` | REVERT Overflow | REVERT bare revert | 21 | 16 | 31 | 21 | n/a | n/a | n/a |
| `exp(130)` | `2.873e+56` | REVERT Overflow | REVERT bare revert | 20 | 16 | 31 | 21 | n/a | n/a | n/a |
| `exp(135)` | `4.263e+58` | REVERT Overflow | REVERT bare revert | 20 | REVERT unknown selector | 31 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `exp(136)` beyond every fixed-point word | `1.159e+59` | REVERT Overflow | REVERT bare revert | REVERT unknown selector | REVERT unknown selector | 31 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |

## sqrt(x)

The root of a tiny number: sqrt(1e-20) is 1e-10, which the grid holds, but 1e-20 itself is zero on it.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `sqrt(1e-6)` | `0.001` | 33 | 13 | exact | exact | 34 | exact | n/a | n/a | n/a |
| `sqrt(1e-12)` | `1.0e-6` | 27 | 8 | exact | exact | 34 | exact | n/a | n/a | n/a |
| `sqrt(1e-18)` | `1.0e-9` | 21 | 1 | exact | exact | 34 | exact | n/a | n/a | n/a |
| `sqrt(1e-20)` the input is zero on an 18-decimal grid | `1.0e-10` | 19 | ZERO | ZERO | ZERO | 34 | ZERO | n/a | n/a | n/a |
| `sqrt(1e-30)` | `1.0e-15` | 8 | ZERO | ZERO | ZERO | 34 | ZERO | n/a | n/a | n/a |
| `sqrt(1e30)` | `1.0e+15` | exact | RANGE | exact | exact | exact | 18 | n/a | n/a | n/a |
| `sqrt(1e36)` | `1.0e+18` | exact | RANGE | exact | exact | exact | 18 | n/a | n/a | n/a |
| `sqrt(1e38)` | `1.0e+19` | exact | RANGE | exact | exact | exact | 17 | n/a | n/a | n/a |
| `sqrt(1e40)` beyond FP127's word | `1.0e+20` | RANGE | RANGE | exact | exact | exact | 18 | n/a | n/a | n/a |
| `sqrt(1e50)` | `1.0e+25` | RANGE | RANGE | exact | REVERT unknown selector | exact | 18 | RANGE | n/a | RANGE |

## pow(x, y)

A base near one to a large power: per-second rates over years, and Uniswap's tick range 1.0001^(+-887272).

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `pow(1+0.05/31536000,31536000)` 5% APR per second, one year | `1.0512711` | 31 | 11 | 10 | 9 | 27 | 11 | n/a | n/a | n/a |
| `pow(1+0.001/31536000,31536000)` 0.1% APR per second, one year | `1.0010005` | 31 | 11 | 10 | 9 | 26 | 10 | n/a | n/a | n/a |
| `pow(1+0.05/31536000,315360000)` ten years | `1.6487213` | 30 | 10 | 9 | 8 | 26 | 10 | n/a | n/a | n/a |
| `pow(1+0.05/31536000/12,31536000*12)` twelve times a second | `1.0512711` | 30 | 10 | 10 | 8 | 25 | 9 | n/a | n/a | n/a |
| `pow(1.0001,887272)` Uniswap's top tick, 3.4e38: one bit past FP127's word | `3.403e+38` | REVERT Overflow | REVERT bare revert | 12 | 11 | 29 | 17 | n/a | n/a | n/a |
| `pow(1.0001,-887272)` Uniswap's bottom tick, 2.9e-39: one ULP of FP127 | `2.939e-39` | 4 | ZERO | ZERO | ZERO | 29 | REVERT Balancer | n/a | n/a | n/a |
| `pow(0.999999,1000000)` | `0.36787926` | 32 | 13 | 12 | 11 | 28 | 18 | n/a | n/a | n/a |
| `pow(2,0.5)` | `1.4142136` | 39 | 18 | 17 | 18 | 33 | 17 | n/a | n/a | n/a |
| `pow(10,-18)` | `1.0e-18` | 20 | 1 | exact | exact | 31 | REVERT Balancer | n/a | n/a | n/a |
| `pow(1e-9,0.5)` | `3.162e-5` | 29 | 10 | 9 | 9 | 32 | 9 | n/a | n/a | n/a |
| `pow(1e-18,0.5)` | `1.0e-9` | 21 | 1 | exact | exact | 32 | exact | n/a | n/a | n/a |

## mul(a, b)

Tiny times tiny: a fee on a fee, a unit price times a unit size, below 1e-18 is zero.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `mul(1e-9,1e-9)` the last digit of an 18-decimal grid | `1.0e-18` | 20 | 1 | ZERO | ZERO | 33 | ZERO | n/a | n/a | n/a |
| `mul(1e-10,1e-10)` zero on it | `1.0e-20` | 18 | ZERO | ZERO | ZERO | 34 | ZERO | n/a | n/a | n/a |
| `mul(1e-12,1e-8)` | `1.0e-20` | 18 | ZERO | ZERO | ZERO | 34 | ZERO | n/a | n/a | n/a |
| `mul(1e19,1e19)` | `1.0e+38` | exact | RANGE | exact | exact | exact | exact | n/a | n/a | n/a |
| `mul(1e20,1e20)` beyond FP127's word | `1.0e+40` | REVERT Overflow | RANGE | exact | exact | exact | exact | n/a | n/a | n/a |

## div(a, b)

Small over large, and one over tiny.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `div(1,3)` | `0.33333333` | 38 | 19 | 17 | 17 | 34 | 17 | n/a | n/a | n/a |
| `div(1e-12,1e9)` | `1.0e-21` | 17 | ZERO | ZERO | ZERO | 34 | ZERO | n/a | n/a | n/a |
| `div(1e-9,1e12)` | `1.0e-21` | 17 | ZERO | ZERO | ZERO | 33 | ZERO | n/a | n/a | n/a |
| `div(1e30,1e-9)` | `1.0e+39` | REVERT Overflow | RANGE | 8 | 8 | exact | 8 | n/a | n/a | n/a |
| `div(1,1e-30)` | `1.0e+30` | 8 | REVERT bare revert | REVERT unknown selector | REVERT Panic | exact | REVERT Panic | n/a | n/a | n/a |

## W0(x)

The principal Lambert branch near its branch point -1/e, where the slope is infinite; only Solady has it among the others.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `lambertW0(-1/e+1e-6)` | `-0.99767017` | 35 | n/a | 15 | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertW0(-1/e+1e-9)` | `-0.99992627` | 34 | n/a | 13 | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertW0(-1/e+1e-12)` | `-0.99999767` | 32 | n/a | 12 | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertW0(-1/e+1e-15)` | `-0.99999993` | 30 | n/a | 10 | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertW0(-1/e+1e-18)` one grid step from the branch point | `-1.0` | 29 | n/a | 8 | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertW0(-1e-18)` | `-1.0e-18` | 20 | n/a | 17 | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertW0(1e-18)` | `1.0e-18` | 20 | n/a | 18 | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertW0(1e30)` | `64.904634` | 41 | RANGE | 20 | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertW0(1e38)` | `83.078448` | 40 | RANGE | 20 | n/a | n/a | n/a | n/a | n/a | n/a |

## W-1(x)

The secondary branch, toward zero from below; FP127 only.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `lambertWm1(-1/e+1e-9)` | `-1.0000737` | 34 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertWm1(-1e-10)` | `-26.295239` | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| `lambertWm1(-1e-30)` | `-73.37311` | 11 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## log1p(x)

ln(1 + x) as an op: the libraries without it compute ln(1 + x), and 1 + x is where x loses its digits.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `log1p(1e-6)` | `1.0e-6` | 34 | 13 | 12 | 11 | 28 | 12 | n/a | n/a | n/a |
| `log1p(1e-9)` a per-second rate | `1.0e-9` | 30 | 10 | 8 | 8 | 25 | 8 | n/a | n/a | n/a |
| `log1p(1e-12)` | `1.0e-12` | 26 | 7 | 12 | 5 | 22 | 6 | n/a | n/a | n/a |
| `log1p(1e-15)` | `1.0e-15` | 24 | 4 | 15 | 2 | 18 | 3 | n/a | n/a | n/a |
| `log1p(1e-18)` | `1.0e-18` | 21 | 1 | 18 | ZERO | 15 | ZERO | n/a | n/a | n/a |
| `log1p(1e-20)` below an 18-decimal grid | `1.0e-20` | 18 | ZERO | ZERO | ZERO | 14 | ZERO | n/a | n/a | n/a |
| `log1p(1e-30)` | `1.0e-30` | 8 | ZERO | ZERO | ZERO | 4 | ZERO | n/a | n/a | n/a |
| `log1p(-1e-9)` | `-1.0e-9` | 30 | 10 | 9 | 8 | 25 | 9 | n/a | n/a | n/a |
| `log1p(1e6)` | `13.815512` | 40 | 20 | 19 | 18 | 33 | 19 | n/a | n/a | n/a |

## expm1(x)

e^x - 1 as an op: the libraries without it compute exp(x) - 1 and the one cancels the digits.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `expm1(1e-6)` | `1.0e-6` | 33 | 13 | 12 | 11 | 27 | 12 | n/a | n/a | n/a |
| `expm1(1e-9)` | `1.0e-9` | 29 | 9 | 8 | 8 | 24 | 8 | n/a | n/a | n/a |
| `expm1(1e-12)` | `1.0e-12` | 26 | 7 | 12 | 5 | 21 | 12 | n/a | n/a | n/a |
| `expm1(1e-15)` | `1.0e-15` | 23 | 4 | 15 | 2 | 18 | 15 | n/a | n/a | n/a |
| `expm1(1e-18)` | `1.0e-18` | 20 | 1 | 18 | ZERO | 15 | 18 | n/a | n/a | n/a |
| `expm1(1e-20)` | `1.0e-20` | 18 | ZERO | ZERO | ZERO | 14 | ZERO | n/a | n/a | n/a |
| `expm1(-1e-9)` | `-1.0e-9` | 30 | 10 | 9 | 9 | 25 | 9 | n/a | n/a | n/a |
| `expm1(-40)` | `-1.0` | 38 | 19 | 18 | 18 | 34 | 18 | n/a | n/a | n/a |
| `expm1(-88)` | `-1.0` | 39 | 38 | 38 | 38 | 34 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `expm1(20)` | `4.8516519e+8` | 44 | 19 | 19 | 17 | 32 | 21 | n/a | n/a | n/a |

## compound(r, n)

(1 + r)^n for an integer n: per-second rates over years. FP127 and Maker take an exact integer power; the rest exp(n ln(1 + r)).

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `compound(0.05/31536000,31536000)` 5% APR per second, one year | `1.0512711` | 31 | 11 | 12 | 10 | 26 | 11 | n/a | n/a | 19 |
| `compound(0.05/31536000,315360000)` ten years | `1.6487213` | 30 | 10 | 11 | 9 | 25 | 10 | n/a | n/a | 18 |
| `compound(0.001/31536000,31536000)` 0.1% APR per second | `1.0010005` | 31 | 12 | 10 | 10 | 26 | 10 | n/a | n/a | 19 |
| `compound(0.1/365,365)` the ladder's headline cell | `1.1051558` | 36 | 17 | 17 | 15 | 31 | 16 | n/a | n/a | 24 |
| `compound(1e-12,1000000000)` a rate of 1e-12 over a billion steps | `1.0010005` | 29 | 11 | 12 | 12 | 25 | 18 | n/a | n/a | 22 |
| `compound(-0.5,10)` | `0.0009765625` | exact | exact | exact | exact | 32 | exact | n/a | n/a | REVERT ParamOutOfRange |
| `compound(0.000000001,10000000)` | `1.0100502` | 31 | 12 | 10 | 10 | 27 | 10 | n/a | n/a | 19 |

## powu(x, n)

An integer power. Solady's rpow, PRBMath's powu, ABDK's pow and Maker's rpow square at the format's precision; FP127 on a 256-bit mantissa.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `powu(2,10)` | `1024.0` | exact | exact | exact | exact | 32 | 17 | n/a | n/a | exact |
| `powu(1.0001,887272)` Uniswap's top tick | `3.403e+38` | REVERT Overflow | REVERT bare revert | 13 | 12 | 29 | 17 | n/a | n/a | REVERT Solady RPowOverflow |
| `powu(1.0001,-887272)` Uniswap's bottom tick | `2.939e-39` | 4 | REVERT bare revert | ZERO | ZERO | 29 | ZERO | n/a | n/a | n/a |
| `powu(0.999999,1000000)` | `0.36787926` | 32 | 13 | 14 | 13 | 28 | 18 | n/a | n/a | 23 |
| `powu(1+0.05/31536000,31536000)` | `1.0512711` | 31 | 11 | 12 | 10 | 27 | 11 | n/a | n/a | 19 |
| `powu(10,38)` | `1.0e+38` | exact | REVERT bare revert | exact | exact | 31 | 16 | n/a | n/a | REVERT Solady RPowOverflow |
| `powu(3,-5)` | `0.0041152263` | 36 | 17 | 15 | 15 | 32 | 15 | n/a | n/a | n/a |
| `powu(1.1,100)` | `13780.612` | 36 | 17 | 19 | 19 | 32 | 15 | n/a | n/a | 29 |

## erf(x)

The error function; the libraries without it run the same series and continued fraction through their own ops.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `erf(1e-10)` | `1.128e-10` | 28 | 9 | 8 | 8 | 33 | 8 | n/a | n/a | n/a |
| `erf(0.5)` | `0.52049988` | 39 | 17 | 16 | 16 | 32 | 16 | n/a | n/a | n/a |
| `erf(1)` | `0.84270079` | 39 | 17 | 16 | 16 | 32 | 16 | n/a | n/a | n/a |
| `erf(3)` | `0.99997791` | 39 | 15 | 14 | 14 | 32 | 14 | n/a | n/a | n/a |
| `erf(4)` | `0.99999998` | 39 | 12 | 11 | 11 | 32 | 11 | n/a | n/a | n/a |
| `erf(5)` | `1.0` | 38 | 19 | 18 | 18 | 34 | 18 | n/a | n/a | n/a |
| `erf(6)` | `1.0` | 39 | 19 | 18 | 18 | 34 | 18 | n/a | n/a | n/a |
| `erf(8)` | `1.0` | 39 | 28 | 28 | 28 | 34 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `erf(9)` | `1.0` | 39 | 36 | 36 | 36 | 34 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |

## erfc(x)

The tail of the normal distribution: erfc(6) is 2e-17, erfc(9.3) one ULP of FP127, zero on an 18-decimal grid from about 6.4.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `erfc(1)` | `0.15729921` | 38 | 17 | 16 | 16 | 31 | 15 | n/a | n/a | n/a |
| `erfc(3)` | `2.209e-5` | 34 | 10 | 9 | 9 | 27 | 9 | n/a | n/a | n/a |
| `erfc(4)` | `1.542e-8` | 31 | 4 | 3 | 3 | 24 | 3 | n/a | n/a | n/a |
| `erfc(5)` | `1.537e-12` | 27 | 7 | 6 | 6 | 32 | 6 | n/a | n/a | n/a |
| `erfc(6)` 2e-17: the last digit of an 18-decimal grid | `2.152e-17` | 23 | 2 | 1 | 1 | 32 | 1 | n/a | n/a | n/a |
| `erfc(7)` | `4.184e-23` | 16 | ZERO | ZERO | ZERO | 32 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `erfc(8)` | `1.122e-29` | 10 | ZERO | ZERO | ZERO | 32 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `erfc(9)` | `4.137e-37` | 2 | ZERO | ZERO | ZERO | 32 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `erfc(9.3)` one ULP of FP127 | `1.653e-39` | 0 | ZERO | ZERO | ZERO | 34 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `erfc(10)` | `2.088e-45` | ZERO | ZERO | ZERO | ZERO | 31 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |

## normCdf(x)

N(d) of Black-Scholes: zero on an 18-decimal grid from d = -8.3, two ULPs of FP127 at -13.

| probe | truth | fp127 | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `normCdf(1e-12)` | `0.5` | 38 | 19 | 18 | 18 | 34 | 18 | n/a | n/a | n/a |
| `normCdf(-1)` | `0.15865525` | 38 | 17 | 16 | 16 | 32 | 16 | n/a | n/a | n/a |
| `normCdf(-3)` | `0.001349898` | 35 | 14 | 13 | 13 | 29 | 13 | n/a | n/a | n/a |
| `normCdf(-5)` | `2.867e-7` | 32 | 8 | 6 | 6 | 26 | 6 | n/a | n/a | n/a |
| `normCdf(-6)` a one-in-a-billion event | `9.866e-10` | 30 | 10 | 8 | 8 | 32 | 8 | n/a | n/a | n/a |
| `normCdf(-8)` | `6.221e-16` | 24 | 4 | 3 | 3 | 31 | 3 | n/a | n/a | n/a |
| `normCdf(-8.3)` the last value above an 18-decimal grid | `5.206e-17` | 23 | 3 | 2 | 2 | 32 | 2 | n/a | n/a | n/a |
| `normCdf(-9)` | `1.129e-19` | 21 | 1 | ZERO | ZERO | 31 | ZERO | n/a | n/a | n/a |
| `normCdf(-10)` | `7.62e-24` | 15 | ZERO | ZERO | ZERO | 32 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `normCdf(-13)` two ULPs of FP127 | `6.117e-39` | 1 | ZERO | ZERO | ZERO | 31 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `normCdf(-14)` | `7.794e-45` | ZERO | ZERO | ZERO | ZERO | 31 | REVERT Balancer InvalidExponent | n/a | n/a | n/a |
| `normCdf(5)` | `0.99999971` | 39 | 14 | 12 | 12 | 32 | 12 | n/a | n/a | n/a |

## Methodology

**truth.** Every probe is one op evaluated once. The truth is mpmath at 200 decimal digits from the exact arguments; truthFormat is the same op from the arguments as the representation holds them (floored on a grid, nearest for binary128), so digitsFormat measures the op alone and digits what a caller sees.

**digits.** digits = floor(-log10 |v - t| / |t|), capped at 60 (reported as exact); errUlps is the signed error in units of the representation's last place (none for binary128).

**zero.** A cell is marked zero when the library returned 0 and the truth is not 0: the result fell below the representation's floor. On an 18-decimal grid that is anything below 1e-18; on FP127's, below 2^-128.

**reverted.** A revert is recorded with its selector and name. Unsupported means the library has no way to compute the op (the accrual libraries have no general ops; only FP127 has the secondary Lambert branch; the libraries without erf, erfc or normCdf run the same series and continued fraction through their own ops instead, so those cells are not Unsupported).

**range.** RANGE means the argument does not fit the representation at all (above 2^127 for FP127, 2^63 for 64.64, 2^128 as a bit pattern for binary128) and nothing was called.

**gas.** gas is measured inside the adapter around the op, after the adapter and the FP127 object are warm. The FP127 (deployed) form includes the staticcall; the others are internal calls.

**live.** EdgeRunner.run(op, form, args) on Sepolia evaluates any cell with one eth_call and returns (ok, raw, reason, gas); the edges page's verify button sends the probe's encoded arguments and compares the raw word bit for bit.

**reproduce.** make edges regenerates edges.json and edges.md from test/ladder/Edges.t.sol and this script; make edges-check fails CI when the committed dataset differs.


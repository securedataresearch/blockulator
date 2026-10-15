# Terminal precision ladder

Generated 2026-10-15 by `make ladder`. Versions: fp127 ab96431, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, forge forge Version: 1.7.1.

Each scenario is run for several inputs; the first table is the reference input in full (`digits / digitsFormat / gas per step`, where digits is against the exact truth and digitsFormat against the truth from the parameters as the library received them), the second is the summary over all inputs (`median (min–max)` digits, capped at 40). Full values, both truths, signed errors and raw words are in ladder.json; the method is in the Methodology section at the end.

## compound: Daily compound interest

Step: `b = b * (1 + r)`. Result: balance after N days.

Per-block or per-day accrual in every lending protocol: one mul per step, N steps.

Inputs: **reference** principal = 10000, rate = 0.1/365 ($10,000 at 10% APR, the headline cell); **tiny-low** principal = 1, rate = 0.01/365 (one unit at 1%: the integer part is small, the fraction carries everything); **tiny-high** principal = 1, rate = 0.5/365 (one unit at 50%); **mid-1pct** principal = 10000, rate = 0.01/365 (a slow rate: the per-step factor is close to 1); **mid-5pct** principal = 10000, rate = 0.05/365 (a typical lending rate); **mid-50pct** principal = 10000, rate = 0.5/365 (a high rate: the balance grows 150x by N = 10,000); **large** principal = 1000000, rate = 0.1/365 (a million-unit position); **huge** principal = 100000000, rate = 0.1/365 (a hundred-million-unit pool); **huge-high** principal = 100000000, rate = 0.5/365 (the largest balance the ladder reaches, near 10^14); **fraction** principal = 0.001, rate = 0.1/365 (a sub-unit balance: leading zeros in WAD)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10002.7397260274` | 38 / exact / 2,148 | 38 / exact / 888 | 19 / exact / 934 | 19 / exact / 744 | 19 / exact / 1,104 | 33 / 33 / 2,933 | 19 / exact / 1,015 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 27 / exact / 610 |
| 2 | `10005.48020266467` | 38 / 42 / 1,885 | 38 / 42 / 623 | 19 / 23 / 610 | 19 / 22 / 488 | 19 / 22 / 848 | 33 / 33 / 1,974 | 19 / 22 / 759 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 27 / 420 |
| 5 | `10013.70613829244` | 38 / 42 / 1,727 | 38 / 42 / 464 | 19 / 23 / 415 | 18 / 21 / 335 | 18 / 21 / 695 | 33 / 33 / 1,398 | 18 / 21 / 606 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 197 |
| 10 | `10027.43106240757` | 37 / 41 / 1,674 | 37 / 41 / 411 | 18 / 22 / 350 | 18 / 21 / 284 | 18 / 21 / 644 | 32 / 32 / 1,206 | 18 / 21 / 555 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 121 |
| 20 | `10054.93737113361` | 37 / 41 / 1,648 | 37 / 41 / 384 | 18 / 22 / 318 | 18 / 21 / 258 | 18 / 21 / 618 | 32 / 32 / 1,110 | 18 / 21 / 529 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 68 |
| 50 | `10137.90984214166` | 37 / 41 / 1,632 | 37 / 41 / 368 | 18 / 21 / 298 | 17 / 20 / 243 | 17 / 20 / 603 | 32 / 32 / 1,053 | 17 / 20 / 514 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 25 / 26 / 31 |
| 100 | `10277.72159673926` | 36 / 40 / 1,627 | 36 / 40 / 363 | 17 / 21 / 292 | 17 / 20 / 238 | 17 / 20 / 598 | 31 / 31 / 1,034 | 17 / 20 / 509 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 25 / 25 / 17 |
| 365 | `11051.55781616264` | 36 / 40 / 1,624 | 36 / 40 / 359 | 17 / 21 / 287 | 16 / 19 / 234 | 16 / 19 / 594 | 31 / 31 / 1,020 | 16 / 19 / 505 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 24 / 25 / 6 |
| 1000 | `13151.29420081218` | 35 / 39 / 1,624 | 35 / 39 / 358 | 16 / 20 / 286 | 16 / 19 / 233 | 16 / 19 / 593 | 30 / 30 / 1,016 | 16 / 19 / 504 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 24 / 24 / 2 |
| 10000 | `154769.3406914411` | 34 / 39 / 1,641 | 34 / 39 / 358 | 15 / 20 / 286 | 15 / 18 / 233 | 15 / 18 / 593 | 29 / 29 / 1,015 | 15 / 18 / 504 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 23 / 23 / 0 |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (35–39) | 38 (35–39) | 19 (16–20) | 18 (15–19) | 18 (15–19) | 33 (33–35) | 18 (15–19) | — (10 revert) | — (10 revert) | 27 (24–28) |
| 2 | 38 (35–38) | 38 (35–38) | 19 (15–19) | 18 (14–19) | 18 (14–19) | 33 (33–34) | 18 (14–19) | — (10 revert) | — (10 revert) | 26 (25–27) |
| 5 | 38 (35–38) | 38 (35–38) | 18.5 (15–19) | 18 (14–19) | 18 (14–19) | 33 (32–33) | 18 (14–19) | — (10 revert) | — (10 revert) | 26 (24–27) |
| 10 | 37 (34–38) | 37 (34–38) | 18 (15–19) | 17 (14–18) | 17 (14–18) | 32 (32–33) | 17 (14–18) | — (10 revert) | — (10 revert) | 26 (24–26) |
| 20 | 37 (34–37) | 37 (34–37) | 18 (15–18) | 17 (13–18) | 17 (13–18) | 32 (32–32) | 17 (13–18) | — (10 revert) | — (10 revert) | 26 (24–26) |
| 50 | 37 (34–37) | 37 (34–37) | 17.5 (14–18) | 17 (13–18) | 17 (13–18) | 32 (31–32) | 17 (13–18) | — (10 revert) | — (10 revert) | 25 (24–26) |
| 100 | 36 (33–37) | 36 (33–37) | 17 (14–18) | 16 (13–17) | 16 (13–17) | 31 (31–32) | 16 (13–17) | — (10 revert) | — (10 revert) | 25 (24–25) |
| 365 | 36 (33–36) | 36 (33–36) | 16.5 (14–17) | 16 (12–17) | 16 (12–17) | 31 (31–31) | 16 (12–17) | — (10 revert) | — (10 revert) | 24 (24–25) |
| 1000 | 35 (32–36) | 35 (32–36) | 16 (13–17) | 15 (12–16) | 15 (12–16) | 30 (30–31) | 15 (12–16) | — (10 revert) | — (10 revert) | 24 (24–24) |
| 10000 | 34 (32–35) | 34 (32–35) | 15 (13–16) | 14 (11–15) | 14 (11–15) | 29 (29–30) | 14 (11–15) | — (10 revert) | — (10 revert) | 23 (23–23) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 (35–40) | 40 (35–40) | 40 (16–40) | 40 (15–40) | 40 (15–40) | 33 (33–35) | 40 (15–40) | — (10 revert) | — (10 revert) | 40 (24–40) |
| 2 | 40 (35–40) | 40 (35–40) | 23 (16–27) | 22 (14–26) | 22 (14–26) | 33 (33–34) | 22 (14–26) | — (10 revert) | — (10 revert) | 27 (25–27) |
| 5 | 40 (35–40) | 40 (35–40) | 22.5 (15–27) | 21 (14–26) | 21 (14–26) | 33 (32–33) | 21 (14–26) | — (10 revert) | — (10 revert) | 27 (24–27) |
| 10 | 40 (34–40) | 40 (34–40) | 22 (15–26) | 21 (14–25) | 21 (14–25) | 32 (32–33) | 21 (14–25) | — (10 revert) | — (10 revert) | 26 (24–26) |
| 20 | 40 (34–40) | 40 (34–40) | 22 (15–26) | 21 (13–25) | 21 (13–25) | 32 (32–32) | 21 (13–25) | — (10 revert) | — (10 revert) | 26 (24–26) |
| 50 | 40 (34–40) | 40 (34–40) | 21 (14–25) | 20 (13–24) | 20 (13–24) | 32 (31–32) | 20 (13–24) | — (10 revert) | — (10 revert) | 26 (24–26) |
| 100 | 40 (33–40) | 40 (33–40) | 21 (14–25) | 20 (13–24) | 20 (13–24) | 31 (31–32) | 20 (13–24) | — (10 revert) | — (10 revert) | 25 (24–26) |
| 365 | 40 (33–40) | 40 (33–40) | 21 (14–25) | 19 (12–23) | 19 (12–23) | 31 (31–31) | 19 (12–23) | — (10 revert) | — (10 revert) | 25 (24–25) |
| 1000 | 39 (32–40) | 39 (32–40) | 20 (13–24) | 19 (12–23) | 19 (12–23) | 30 (30–31) | 19 (12–23) | — (10 revert) | — (10 revert) | 24 (24–25) |
| 10000 | 39 (32–40) | 39 (32–40) | 19.5 (13–24) | 18 (11–23) | 18 (11–23) | 29 (29–30) | 18 (11–23) | — (10 revert) | — (10 revert) | 23 (23–24) |

## compound-pow: Compound interest in one pow

Step: `b0 * (1 + r)^N`. Result: the same balance, computed with one real-exponent pow.

The clever way to skip the loop. pow is exp(N ln(1+r)) in every library, so its precision is bounded by ln and exp, and the error grows with N without any loop.

Inputs: **reference** principal = 10000, rate = 0.1/365 ($10,000 at 10% APR, the headline cell); **tiny-low** principal = 1, rate = 0.01/365 (one unit at 1%: the integer part is small, the fraction carries everything); **tiny-high** principal = 1, rate = 0.5/365 (one unit at 50%); **mid-1pct** principal = 10000, rate = 0.01/365 (a slow rate: the per-step factor is close to 1); **mid-5pct** principal = 10000, rate = 0.05/365 (a typical lending rate); **mid-50pct** principal = 10000, rate = 0.5/365 (a high rate: the balance grows 150x by N = 10,000); **large** principal = 1000000, rate = 0.1/365 (a million-unit position); **huge** principal = 100000000, rate = 0.1/365 (a hundred-million-unit pool); **huge-high** principal = 100000000, rate = 0.5/365 (the largest balance the ladder reaches, near 10^14); **fraction** principal = 0.001, rate = 0.1/365 (a sub-unit balance: leading zeros in WAD)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10002.7397260274` | 38 / exact / 3,285 | 38 / exact / 1,130 | 19 / 19 / 11,498 | 17 / 18 / 2,153 | 19 / exact / 1,436 | 33 / 33 / 28,822 | 17 / 18 / 3,096 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `10005.48020266467` | 38 / 38 / 1,747 | 38 / 38 / 682 | 18 / 18 / 5,749 | 17 / 18 / 1,076 | 16 / 16 / 5,366 | 33 / 33 / 14,413 | 17 / 18 / 1,548 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `10013.70613829244` | 38 / 38 / 2,136 | 38 / 38 / 2,117 | 18 / 18 / 2,282 | 17 / 17 / 430 | 16 / 16 / 2,118 | 33 / 33 / 5,728 | 17 / 18 / 619 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `10027.43106240757` | 37 / 39 / 1,068 | 37 / 39 / 1,058 | 18 / 18 / 1,141 | 17 / 17 / 215 | 16 / 16 / 1,060 | 33 / 33 / 2,864 | 18 / 18 / 309 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `10054.93737113361` | 37 / 39 / 534 | 37 / 39 / 529 | 17 / 18 / 570 | 17 / 17 / 107 | 15 / 15 / 530 | 33 / 33 / 1,432 | 17 / 18 / 154 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `10137.90984214166` | 37 / 38 / 213 | 37 / 38 / 211 | 17 / 17 / 230 | 16 / 16 / 43 | 15 / 15 / 217 | 32 / 32 / 573 | 17 / 18 / 61 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `10277.72159673926` | 36 / 39 / 106 | 36 / 39 / 105 | 17 / 17 / 115 | 16 / 16 / 21 | 15 / 15 / 109 | 32 / 32 / 286 | 17 / 17 / 30 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `11051.55781616264` | 36 / 39 / 29 | 36 / 39 / 29 | 16 / 16 / 31 | 15 / 15 / 5 | 14 / 14 / 29 | 31 / 31 / 78 | 16 / 18 / 8 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `13151.29420081218` | 35 / 39 / 10 | 35 / 39 / 10 | 16 / 16 / 11 | 15 / 15 / 2 | 14 / 14 / 10 | 31 / 31 / 28 | 16 / 18 / 3 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `154769.3406914411` | 34 / 40 / 1 | 34 / 40 / 1 | 15 / 15 / 1 | 14 / 14 / 0 | 13 / 13 / 1 | 30 / 30 / 2 | 15 / 17 / 0 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (35–39) | 38 (35–39) | 19 (16–19) | 17 (15–17) | 18 (15–19) | 33 (33–33) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) |
| 2 | 38 (35–38) | 38 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) | 33 (33–34) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) |
| 5 | 38 (35–38) | 38 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) | 33 (32–33) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) |
| 10 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) | 33 (32–34) | 17 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 20 | 37 (35–37) | 37 (35–37) | 17 (16–18) | 16 (15–17) | 15 (15–15) | 33 (32–33) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) |
| 50 | 37 (35–37) | 37 (35–37) | 17 (16–17) | 16 (15–17) | 15 (15–15) | 32 (32–33) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) |
| 100 | 36 (35–37) | 36 (35–37) | 17 (16–17) | 16 (15–17) | 15 (14–15) | 32 (31–33) | 16 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) |
| 365 | 36 (35–36) | 36 (35–36) | 16 (16–16) | 15 (15–16) | 14 (14–14) | 31 (31–32) | 16 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) |
| 1000 | 35 (35–36) | 35 (35–36) | 16 (15–16) | 15 (14–16) | 14 (13–14) | 31 (30–32) | 15 (15–16) | — (10 revert) | — (10 revert) | — (10 revert) |
| 10000 | 34 (34–35) | 34 (34–35) | 15 (15–15) | 14 (13–15) | 13 (12–13) | 30 (29–31) | 14.5 (14–15) | — (10 revert) | — (10 revert) | — (10 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 (35–40) | 40 (35–40) | 19 (16–19) | 18 (15–18) | 40 (15–40) | 33 (33–33) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 2 | 38 (35–38) | 38 (35–38) | 18.5 (16–19) | 17 (15–18) | 16 (15–16) | 33 (33–34) | 17 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 5 | 38 (35–39) | 38 (35–39) | 18 (16–19) | 17 (15–17) | 16 (15–16) | 33 (32–33) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 10 | 39 (35–40) | 39 (35–40) | 18 (16–18) | 17 (15–18) | 16 (15–16) | 33 (32–34) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 20 | 39 (35–39) | 39 (35–39) | 18 (16–18) | 16 (15–17) | 15 (15–15) | 33 (32–33) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 50 | 39 (37–39) | 39 (37–39) | 17 (16–18) | 16 (15–17) | 15 (15–15) | 32 (32–33) | 17 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 100 | 39 (37–39) | 39 (37–39) | 17 (16–18) | 16 (15–17) | 15 (14–15) | 32 (31–33) | 17 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 365 | 39 (35–40) | 39 (35–40) | 16.5 (16–17) | 15 (15–16) | 14 (14–14) | 31 (31–32) | 17.5 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 1000 | 39 (36–39) | 39 (36–39) | 16 (16–17) | 15 (14–16) | 14 (13–14) | 31 (30–32) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) |
| 10000 | 40 (36–40) | 40 (36–40) | 15 (15–16) | 14 (14–15) | 13 (12–13) | 30 (29–31) | 18 (16–18) | — (10 revert) | — (10 revert) | — (10 revert) |

## bonding-sqrt: Square-root bonding curve

Step: `cost += sqrt(s); s += 1`. Result: total cost of N unit buys.

Bonding curves price each token at a root of the supply; the sum of N floors is where the digits go.

Inputs: **reference** supply = 1000, unit = 1 (a thousand tokens out, unit buys); **from-one** supply = 1, unit = 1 (the curve from its first token); **half-units** supply = 1000, unit = 0.5 (buys that are not integers); **deep** supply = 1000000, unit = 1 (a million out: sqrt is large, the sum is huge); **micro** supply = 1, unit = 0.001 (thousandth-unit buys from the start); **very-deep** supply = 1000000000, unit = 1000 (a billion out in thousand-token lots); **small-steps** supply = 10, unit = 0.01 (hundredth-unit buys from ten)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `31.62277660168379` | 41 / 41 / 4,491 | 41 / 41 / 4,198 | 20 / 20 / 1,814 | 19 / 19 / 1,262 | 19 / 19 / 1,753 | 34 / 34 / 3,234 | 18 / 18 / 3,206 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `63.26136064079654` | 40 / 40 / 4,276 | 40 / 40 / 3,986 | 21 / 21 / 1,574 | 19 / 19 / 1,050 | 19 / 19 / 1,545 | 33 / 33 / 3,118 | 18 / 18 / 2,994 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `158.2718785032213` | 40 / 40 / 4,147 | 40 / 40 / 3,859 | 21 / 21 / 1,424 | 19 / 19 / 923 | 19 / 19 / 1,419 | 33 / 33 / 3,023 | 18 / 18 / 2,867 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `316.9381559123806` | 40 / 40 / 4,104 | 40 / 40 / 3,817 | 21 / 21 / 1,376 | 19 / 19 / 881 | 19 / 19 / 1,375 | 33 / 33 / 2,985 | 18 / 18 / 2,825 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `635.4500029402082` | 40 / 40 / 4,083 | 40 / 40 / 3,796 | 21 / 21 / 1,351 | 19 / 19 / 860 | 19 / 19 / 1,354 | 33 / 33 / 2,964 | 18 / 18 / 2,804 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `1600.350881438697` | 40 / 40 / 4,008 | 40 / 40 / 3,692 | 21 / 21 / 1,339 | 19 / 19 / 847 | 19 / 19 / 1,342 | 32 / 32 / 2,952 | 18 / 18 / 2,802 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `3239.292264514382` | 40 / 40 / 3,976 | 40 / 40 / 3,646 | 21 / 21 / 1,336 | 19 / 19 / 843 | 19 / 19 / 1,338 | 32 / 32 / 2,947 | 17 / 17 / 2,805 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `12536.2620049473` | 40 / 40 / 3,952 | 40 / 40 / 3,612 | 21 / 21 / 1,334 | 19 / 19 / 840 | 19 / 19 / 1,335 | 31 / 31 / 2,943 | 18 / 18 / 2,763 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `38540.07865481035` | 40 / 40 / 3,948 | 40 / 40 / 3,604 | 21 / 21 / 1,333 | 19 / 19 / 839 | 19 / 19 / 1,345 | 31 / 31 / 2,942 | 18 / 18 / 2,779 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `748008.0076158747` | 40 / 40 / 4,035 | 40 / 40 / 3,694 | 21 / 21 / 1,345 | 20 / 20 / 839 | 20 / 20 / 1,354 | 30 / 30 / 2,941 | 18 / 18 / 2,702 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (7): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 (39–40) | 40 (39–40) | 23 (20–40) | 22 (18–40) | 22 (18–40) | 34 (33–40) | 18 (17–40) | — (7 revert) | — (7 revert) | — (7 revert) |
| 2 | 40 (38–40) | 40 (38–40) | 20 (19–24) | 19 (18–22) | 19 (18–22) | 34 (33–34) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 5 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–34) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 10 | 40 (38–40) | 40 (38–40) | 20 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–33) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 20 | 40 (38–40) | 40 (38–40) | 21 (18–24) | 19 (18–22) | 19 (18–22) | 33 (33–33) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 50 | 40 (37–40) | 40 (37–40) | 21 (18–24) | 19 (18–22) | 19 (18–22) | 32 (32–32) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 100 | 40 (37–40) | 40 (37–40) | 21 (18–24) | 19 (18–22) | 19 (18–22) | 32 (32–32) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 365 | 40 (36–40) | 40 (36–40) | 21 (17–24) | 19 (18–22) | 19 (18–22) | 31 (31–31) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 1000 | 40 (36–40) | 40 (36–40) | 21 (17–24) | 19 (18–22) | 19 (18–22) | 31 (31–31) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 10000 | 40 (36–40) | 40 (36–40) | 21 (16–24) | 20 (18–22) | 20 (18–22) | 30 (30–30) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 (39–40) | 40 (39–40) | 23 (20–40) | 22 (18–40) | 22 (18–40) | 34 (33–40) | 18 (17–40) | — (7 revert) | — (7 revert) | — (7 revert) |
| 2 | 40 (38–40) | 40 (38–40) | 20 (19–24) | 19 (18–22) | 19 (18–22) | 34 (33–34) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 5 | 40 (39–40) | 40 (39–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–34) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 10 | 40 (38–40) | 40 (38–40) | 20 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–33) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 20 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–33) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 50 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 32 (32–32) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 100 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 32 (32–32) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 365 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 31 (31–31) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 1000 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 31 (31–31) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) |
| 10000 | 40 (39–40) | 40 (39–40) | 21 (19–24) | 20 (18–22) | 20 (18–22) | 30 (30–30) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) |

## roundtrip: exp(ln(x)) round trip

Step: `x = exp(ln(x))`. Result: x after N round trips; the answer is the input.

Isolates transcendental error. Every step should be the identity; what remains is the library's ln and exp error, compounded.

Inputs: **reference** x0 = 1.5 (1.5 is representable in every format, so a perfect library returns it exactly); **hundredth** x0 = 0.01 (ln is large and negative); **tenth** x0 = 0.1 (a typical price ratio); **near-one-below** x0 = 0.7 (ln is small: cancellation territory); **just-above-one** x0 = 1.0001 (ln is tiny: the log1p regime); **two** x0 = 2 (the simplest non-trivial value); **ten** x0 = 10 (a round decade); **thousand** x0 = 1000 (three decades); **million** x0 = 1000000 (six decades, near ABDK's comfortable range); **awkward** x0 = 123456.789 (a value with no special structure)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `1.5` | 38 / 38 / 10,190 | 38 / 38 / 10,151 | 19 / 19 / 10,892 | exact / exact / 1,441 | 16 / 16 / 10,093 | 33 / 33 / 23,587 | 17 / 17 / 2,617 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `1.5` | 38 / 38 / 10,018 | 38 / 38 / 9,982 | 18 / 18 / 10,698 | exact / exact / 1,272 | 16 / 16 / 9,902 | 33 / 33 / 23,376 | 17 / 17 / 2,448 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `1.5` | 38 / 38 / 9,914 | 38 / 38 / 9,880 | 18 / 18 / 10,578 | exact / exact / 1,170 | 16 / 16 / 9,772 | 32 / 32 / 23,252 | 17 / 17 / 2,346 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `1.5` | 38 / 38 / 9,880 | 38 / 38 / 9,846 | 18 / 18 / 10,538 | exact / exact / 1,136 | 15 / 15 / 9,794 | 32 / 32 / 23,224 | 16 / 16 / 2,312 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `1.5` | 38 / 38 / 9,863 | 38 / 38 / 9,829 | 17 / 17 / 10,522 | exact / exact / 1,119 | 15 / 15 / 9,801 | 32 / 32 / 23,211 | 16 / 16 / 2,295 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `1.5` | 38 / 38 / 9,853 | 38 / 38 / 9,819 | 17 / 17 / 10,507 | exact / exact / 1,109 | 15 / 15 / 9,789 | 31 / 31 / 23,192 | 16 / 16 / 2,285 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `1.5` | 38 / 38 / 9,850 | 38 / 38 / 9,816 | 17 / 17 / 10,502 | exact / exact / 1,106 | 14 / 14 / 9,773 | 31 / 31 / 23,189 | 15 / 15 / 2,282 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `1.5` | 38 / 38 / 9,849 | 38 / 38 / 9,813 | 16 / 16 / 10,488 | exact / exact / 1,103 | 14 / 14 / 9,778 | 31 / 31 / 23,181 | 15 / 15 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `1.5` | 38 / 38 / 9,854 | 38 / 38 / 9,813 | 16 / 16 / 10,495 | exact / exact / 1,103 | 13 / 13 / 9,761 | 30 / 30 / 23,187 | 14 / 14 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `1.5` | 38 / 38 / 9,924 | 38 / 38 / 9,813 | 15 / 15 / 10,500 | exact / exact / 1,103 | 12 / 12 / 9,758 | 29 / 29 / 23,224 | 13 / 13 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (36–39) | 38 (36–39) | 19 (17–19) | 18 (16–40) | 17 (16–40) | 32.5 (32–34) | 18 (17–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 2 | 38 (36–39) | 38 (36–39) | 18 (16–18) | 17 (16–40) | 16 (16–40) | 32 (31–33) | 17 (17–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 5 | 38 (36–39) | 38 (36–39) | 18 (16–18) | 17 (16–40) | 16 (16–40) | 32 (31–33) | 17 (17–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 10 | 38 (36–39) | 38 (36–39) | 17.5 (16–18) | 17 (15–40) | 16 (15–40) | 31.5 (31–33) | 17 (16–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 20 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (15–40) | 15 (15–40) | 31 (30–33) | 16 (16–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 50 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (15–40) | 15 (15–40) | 31 (30–33) | 16 (16–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 100 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (15–40) | 15 (14–40) | 30.5 (30–33) | 16 (15–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 365 | 38 (36–39) | 38 (36–39) | 16 (14–16) | 15 (14–40) | 14 (14–40) | 30 (29–33) | 15 (15–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 1000 | 38 (36–39) | 38 (36–39) | 16 (14–16) | 15 (13–40) | 14 (13–40) | 29.5 (29–33) | 15 (14–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 10000 | 38 (36–39) | 38 (36–39) | 15 (13–15) | 14 (12–40) | 13 (12–40) | 28.5 (28–33) | 14 (13–40) | — (10 revert) | — (10 revert) | — (10 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 (38–40) | 39 (38–40) | 19 (17–19) | 18 (16–40) | 17 (16–40) | 32.5 (32–33) | 18 (17–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 2 | 39 (38–40) | 39 (38–40) | 18 (16–18) | 17 (16–40) | 16 (16–40) | 32 (31–33) | 17 (17–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 5 | 39 (38–40) | 39 (38–40) | 18 (16–18) | 17 (16–40) | 16 (16–40) | 32 (31–33) | 17 (17–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 10 | 39 (38–40) | 39 (38–40) | 17.5 (16–18) | 17 (15–40) | 16 (15–40) | 31.5 (31–33) | 17 (16–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 20 | 39 (38–40) | 39 (38–40) | 17 (15–17) | 16 (15–40) | 15 (15–40) | 31 (30–33) | 16 (16–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 50 | 39 (38–40) | 39 (38–40) | 17 (15–17) | 16 (15–40) | 15 (15–40) | 31 (30–33) | 16 (16–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 100 | 39 (38–40) | 39 (38–40) | 17 (15–17) | 16 (15–40) | 15 (14–40) | 30.5 (30–33) | 16 (15–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 365 | 39 (38–40) | 39 (38–40) | 16 (14–16) | 15 (14–40) | 14 (14–40) | 30 (29–33) | 15 (15–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 1000 | 39 (38–40) | 39 (38–40) | 16 (14–16) | 15 (13–40) | 14 (13–40) | 29.5 (29–33) | 15 (14–40) | — (10 revert) | — (10 revert) | — (10 revert) |
| 10000 | 39 (38–40) | 39 (38–40) | 15 (13–15) | 14 (12–40) | 13 (12–40) | 28.5 (28–33) | 14 (13–40) | — (10 revert) | — (10 revert) | — (10 revert) |

## amortise: Amortising loan

Step: `b = b * (1 + r) - payment`. Result: outstanding balance after N daily payments.

Subtracting nearly equal numbers. The payment retires the loan at step 366, so at N = 365 the balance is one payment and relative error is amplified several hundred times.

Inputs: **reference** principal = 300000, rate = 0.05/365, term = 366 (a mortgage-sized loan retiring at step 366); **small** principal = 10000, rate = 0.05/365, term = 366 (a small loan); **high-rate** principal = 300000, rate = 0.1/365, term = 366 (double the rate); **ten-year** principal = 300000, rate = 0.05/365, term = 3650 (a ten-year term: at N = 365 nine tenths remain); **large-low** principal = 1000000, rate = 0.03/365, term = 366 (a large loan at a low rate); **very-high** principal = 300000, rate = 0.2/365, term = 366 (20% APR); **micro** principal = 500, rate = 0.05/365, term = 366 (a tiny loan: the payment is a few units); **retires-at-10001** principal = 300000, rate = 0.05/365, term = 10001 (retires one step past the ladder's end, so N = 10,000 is the one-payment cell)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `299200.6479903559` | 39 / exact / 2,551 | 39 / exact / 1,318 | 20 / exact / 1,434 | 19 / exact / 1,147 | 19 / exact / 1,507 | 33 / 33 / 4,718 | 19 / exact / 1,418 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `298401.1864804365` | 38 / 44 / 2,163 | 38 / 44 / 928 | 19 / 25 / 967 | 19 / 23 / 766 | 19 / 23 / 1,126 | 33 / 33 / 3,604 | 19 / 23 / 1,037 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `296002.1447990159` | 38 / 43 / 1,930 | 38 / 43 / 694 | 19 / 24 / 686 | 19 / 23 / 538 | 19 / 23 / 898 | 32 / 32 / 2,936 | 19 / 23 / 809 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `292001.5505907346` | 38 / 43 / 1,852 | 38 / 43 / 616 | 19 / 24 / 593 | 18 / 22 / 462 | 18 / 22 / 822 | 32 / 32 / 2,713 | 18 / 22 / 733 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `283992.1376448092` | 37 / 42 / 1,813 | 37 / 42 / 577 | 18 / 23 / 546 | 18 / 22 / 424 | 18 / 22 / 784 | 32 / 32 / 2,602 | 18 / 22 / 695 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `259897.9672060033` | 37 / 42 / 1,790 | 37 / 42 / 553 | 18 / 23 / 518 | 18 / 22 / 401 | 18 / 22 / 761 | 31 / 31 / 2,535 | 18 / 22 / 672 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `219520.3390882176` | 37 / 42 / 1,782 | 37 / 42 / 545 | 17 / 22 / 509 | 17 / 21 / 393 | 17 / 21 / 753 | 31 / 31 / 2,513 | 17 / 21 / 664 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `840.3327859747961` | 34 / 39 / 1,777 | 34 / 39 / 540 | 15 / 19 / 502 | 15 / 18 / 388 | 15 / 18 / 748 | 28 / 28 / 2,496 | 15 / 18 / 659 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `-556627.3884008416` | 36 / 41 / 1,777 | 36 / 41 / 538 | 17 / 22 / 500 | 17 / 21 / 386 | 17 / 21 / 753 | 31 / 31 / 2,191 | 17 / 21 / 726 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `-16823263.35321035` | 35 / 41 / 1,794 | 35 / 41 / 538 | 16 / 22 / 500 | 16 / 21 / 386 | 16 / 21 / 756 | 29 / 29 / 2,032 | 16 / 21 / 761 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (8): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 (38–39) | 39 (38–39) | 20 (19–20) | 19 (18–19) | 19 (18–19) | 33 (33–33) | 19 (18–19) | — (8 revert) | — (8 revert) | — (8 revert) |
| 2 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 19 (17–19) | 19 (17–19) | 33 (33–33) | 19 (17–19) | — (8 revert) | — (8 revert) | — (8 revert) |
| 5 | 38 (37–38) | 38 (37–38) | 19 (18–19) | 19 (17–19) | 19 (17–19) | 32 (32–33) | 19 (17–19) | — (8 revert) | — (8 revert) | — (8 revert) |
| 10 | 38 (37–38) | 38 (37–38) | 19 (18–19) | 18 (17–18) | 18 (17–18) | 32 (32–32) | 18 (17–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 18 (16–18) | 18 (16–18) | 32 (32–32) | 18 (16–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 50 | 37 (36–37) | 37 (36–37) | 18 (17–18) | 18 (16–18) | 18 (16–18) | 31 (31–32) | 18 (16–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 100 | 37 (36–37) | 37 (36–37) | 17 (17–18) | 17 (16–17) | 17 (16–17) | 31 (31–31) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 365 | 34 (33–36) | 34 (33–36) | 15 (14–17) | 14.5 (13–17) | 14.5 (13–17) | 28 (28–31) | 14.5 (13–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 1000 | 36 (36–36) | 36 (36–36) | 17 (16–17) | 16.5 (15–17) | 16.5 (15–17) | 31 (30–31) | 16.5 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 10000 | 35 (31–35) | 35 (31–35) | 15.5 (12–16) | 15.5 (11–16) | 15.5 (11–16) | 29 (25–30) | 15.5 (11–16) | — (8 revert) | — (8 revert) | — (8 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 33 (33–33) | 40 (40–40) | — (8 revert) | — (8 revert) | — (8 revert) |
| 2 | 40 (40–40) | 40 (40–40) | 24 (22–25) | 23 (21–24) | 23 (21–24) | 33 (33–33) | 23 (21–24) | — (8 revert) | — (8 revert) | — (8 revert) |
| 5 | 40 (40–40) | 40 (40–40) | 24 (21–24) | 23 (20–23) | 23 (20–23) | 32 (32–33) | 23 (20–23) | — (8 revert) | — (8 revert) | — (8 revert) |
| 10 | 40 (40–40) | 40 (40–40) | 24 (21–24) | 22 (20–23) | 22 (20–23) | 32 (32–32) | 22 (20–23) | — (8 revert) | — (8 revert) | — (8 revert) |
| 20 | 40 (40–40) | 40 (40–40) | 23 (20–24) | 22 (19–23) | 22 (19–23) | 32 (32–32) | 22 (19–23) | — (8 revert) | — (8 revert) | — (8 revert) |
| 50 | 40 (39–40) | 40 (39–40) | 23 (20–23) | 22 (19–22) | 22 (19–22) | 31 (31–32) | 22 (19–22) | — (8 revert) | — (8 revert) | — (8 revert) |
| 100 | 40 (39–40) | 40 (39–40) | 22 (20–23) | 21 (18–22) | 21 (18–22) | 31 (31–31) | 21 (18–22) | — (8 revert) | — (8 revert) | — (8 revert) |
| 365 | 39 (36–40) | 39 (36–40) | 19 (17–22) | 18 (15–21) | 18 (15–21) | 28 (28–31) | 18 (15–21) | — (8 revert) | — (8 revert) | — (8 revert) |
| 1000 | 40 (38–40) | 40 (38–40) | 21.5 (19–22) | 20.5 (18–22) | 20.5 (18–22) | 31 (30–31) | 20.5 (18–22) | — (8 revert) | — (8 revert) | — (8 revert) |
| 10000 | 40 (36–40) | 40 (36–40) | 21.5 (16–22) | 21 (15–21) | 21 (15–21) | 29 (25–30) | 21 (15–21) | — (8 revert) | — (8 revert) | — (8 revert) |

## geo-mean: Running geometric mean

Step: `L += ln(x_i); g = exp(L / N), x_i = (i + 2) / (i + 1)`. Result: geometric mean of N terms; truth telescopes to ((N + 2) / 2)^(1 / N).

Index and basket maths: a sum of logs, one division, one exp. The division by N and the final exp expose every accumulated ULP.

Inputs: **reference**  (the scenario has no parameters; its inputs are the integers 1..N)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `1.5` | 38 / 38 / 12,962 | 38 / 38 / 11,962 | 19 / 19 / 12,146 | exact / exact / 2,580 | 16 / 16 / 12,066 | 33 / 33 / 28,422 | 17 / 17 / 4,358 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `1.414213562373095` | 38 / 38 / 9,601 | 38 / 38 / 8,929 | 18 / 18 / 10,322 | 17 / 17 / 2,042 | 16 / 16 / 10,383 | 33 / 33 / 25,241 | 17 / 17 / 3,360 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `1.284735157123439` | 38 / 38 / 7,459 | 38 / 38 / 6,950 | 19 / 19 / 8,889 | 17 / 17 / 1,720 | 16 / 16 / 9,067 | 33 / 33 / 22,612 | 17 / 17 / 2,767 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `1.196231198851315` | 38 / 38 / 6,709 | 38 / 38 / 6,243 | 18 / 18 / 8,503 | 17 / 17 / 1,612 | 16 / 16 / 8,686 | 33 / 33 / 21,921 | 17 / 17 / 2,535 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `1.127378204157833` | 38 / 38 / 6,341 | 38 / 38 / 5,900 | 18 / 18 / 8,308 | 17 / 17 / 1,558 | 16 / 16 / 8,538 | 33 / 33 / 21,654 | 17 / 17 / 2,322 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `1.067331844248559` | 38 / 38 / 6,071 | 38 / 38 / 5,631 | 18 / 18 / 8,184 | 17 / 17 / 1,526 | 16 / 16 / 8,376 | 33 / 33 / 21,578 | 17 / 17 / 2,194 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `1.04010144984871` | 39 / 39 / 5,936 | 39 / 39 / 5,485 | 18 / 18 / 8,147 | 17 / 17 / 1,515 | 16 / 16 / 8,318 | 33 / 33 / 21,638 | 17 / 17 / 2,151 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `1.01438248702624` | 38 / 38 / 5,740 | 38 / 38 / 5,250 | 18 / 18 / 8,117 | 17 / 17 / 1,507 | 16 / 16 / 8,258 | 33 / 33 / 21,830 | 17 / 17 / 2,120 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `1.006235969300459` | 39 / 39 / 5,666 | 39 / 39 / 5,155 | 18 / 18 / 8,110 | 17 / 17 / 1,506 | 16 / 16 / 8,241 | 33 / 33 / 22,011 | 17 / 17 / 2,113 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `1.00085210215008` | 38 / 38 / 5,695 | 38 / 38 / 5,105 | 18 / 18 / 8,107 | 17 / 17 / 1,505 | 16 / 16 / 8,188 | 33 / 33 / 22,491 | 17 / 17 / 2,109 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (1): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 40 (40–40) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 2 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 5 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 10 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 20 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 50 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 100 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 365 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 1000 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 10000 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 40 (40–40) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 2 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 5 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 10 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 20 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 50 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 100 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 365 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 1000 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |
| 10000 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) |

## black-scholes-chain: Black-Scholes d1 along a price path

Step: `acc += d1(S); S += tick, with d1 = (ln(S / K) + (r + sigma^2 / 2) T) / (sigma sqrt(T))`. Result: sum of d1 over N ticks.

The options-desk case: ln, div, sqrt and mul in one expression, re-evaluated as the spot moves and aggregated.

Inputs: **reference** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (at the money, 20% vol, six months); **low-vol** spot = 100, strike = 100, sigma = 0.05, T = 0.5, r = 0.05, tick = 0.01 (5% vol: the denominator is small); **high-vol** spot = 100, strike = 100, sigma = 0.8, T = 0.5, r = 0.05, tick = 0.01 (80% vol); **in-the-money** spot = 120, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (ln(S/K) is positive and not small); **out-of-the-money** spot = 80, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (ln(S/K) is negative); **short-dated** spot = 100, strike = 100, sigma = 0.2, T = 0.01, r = 0.05, tick = 0.01 (sqrt(T) is small); **long-dated** spot = 100, strike = 100, sigma = 0.2, T = 2, r = 0.05, tick = 0.01 (two years); **coarse-ticks** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 1 (whole-unit ticks: S doubles by N = 100 and reaches 10,100)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `0.2474873734152916` | 37 / 37 / 14,759 | 37 / 37 / 8,335 | 18 / 18 / 11,764 | 17 / 17 / 3,822 | 17 / 17 / 6,998 | 34 / 34 / 13,162 | 17 / 17 / 7,708 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `0.4956818182587876` | 37 / 37 / 13,481 | 37 / 37 / 8,968 | 17 / 17 / 10,635 | 18 / 18 / 2,921 | 16 / 16 / 8,436 | 32 / 32 / 19,642 | 17 / 17 / 6,386 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `1.244506874463792` | 37 / 37 / 12,714 | 37 / 37 / 9,347 | 17 / 17 / 9,957 | 17 / 17 / 2,381 | 15 / 15 / 9,431 | 32 / 32 / 23,377 | 16 / 16 / 5,592 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `2.506683467804941` | 36 / 37 / 12,459 | 36 / 37 / 9,474 | 17 / 17 / 9,731 | 17 / 17 / 2,201 | 15 / 15 / 9,734 | 31 / 31 / 24,511 | 16 / 16 / 5,328 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `5.084010514032979` | 36 / 37 / 12,331 | 36 / 37 / 9,537 | 17 / 17 / 9,618 | 17 / 17 / 2,111 | 15 / 15 / 9,905 | 31 / 31 / 25,006 | 16 / 16 / 5,196 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `13.23914876467473` | 36 / 37 / 12,256 | 36 / 37 / 9,575 | 17 / 17 / 9,551 | 17 / 17 / 2,057 | 15 / 15 / 10,052 | 31 / 31 / 25,202 | 16 / 16 / 5,116 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `28.23736439326609` | 36 / 37 / 12,304 | 36 / 37 / 9,677 | 17 / 17 / 9,528 | 17 / 17 / 2,039 | 15 / 15 / 10,098 | 30 / 30 / 25,187 | 16 / 16 / 5,090 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `136.7454508837998` | 36 / 37 / 12,423 | 36 / 37 / 9,845 | 17 / 17 / 9,512 | 17 / 17 / 2,025 | 15 / 15 / 10,135 | 30 / 30 / 25,027 | 16 / 16 / 5,071 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `589.4747739528645` | 36 / 37 / 12,561 | 36 / 37 / 9,989 | 17 / 18 / 9,508 | 18 / 18 / 2,022 | 15 / 15 / 10,171 | 30 / 30 / 24,823 | 17 / 17 / 5,066 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `29787.55928753143` | 36 / 39 / 13,263 | 36 / 39 / 10,331 | 18 / 19 / 9,506 | 17 / 17 / 2,021 | 16 / 16 / 10,223 | 30 / 30 / 24,408 | 17 / 17 / 5,313 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (8): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 (35–38) | 37 (35–38) | 18 (17–19) | 17 (17–40) | 17 (16–40) | 34 (33–34) | 17 (17–40) | — (8 revert) | — (8 revert) | — (8 revert) |
| 2 | 37 (35–38) | 37 (35–38) | 17.5 (16–18) | 17.5 (15–18) | 16 (14–16) | 32.5 (30–33) | 17 (15–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 5 | 37 (35–38) | 37 (35–38) | 17 (16–18) | 17 (15–18) | 15.5 (14–16) | 32 (30–33) | 17 (15–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 10 | 37 (35–38) | 37 (35–38) | 17 (16–18) | 17 (15–18) | 15.5 (14–16) | 32 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 20 | 37 (35–37) | 37 (35–37) | 17.5 (16–18) | 17 (15–17) | 16 (14–16) | 32 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 50 | 37 (35–38) | 37 (35–38) | 17.5 (16–18) | 17 (15–17) | 16 (14–16) | 31 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 100 | 37 (36–39) | 37 (36–39) | 17.5 (16–19) | 17 (16–17) | 16 (14–16) | 31 (30–32) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 365 | 37 (36–38) | 37 (36–38) | 17.5 (17–19) | 17 (16–17) | 16 (15–17) | 30.5 (30–31) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 1000 | 37 (36–38) | 37 (36–38) | 17 (17–18) | 17 (16–18) | 16 (15–17) | 30 (30–31) | 17 (16–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 10000 | 37 (36–38) | 37 (36–38) | 18 (17–20) | 17 (17–18) | 16 (16–17) | 30 (29–30) | 17 (17–17) | — (8 revert) | — (8 revert) | — (8 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 (35–38) | 37 (35–38) | 18 (17–19) | 17 (17–40) | 17 (16–40) | 34 (33–35) | 17 (17–40) | — (8 revert) | — (8 revert) | — (8 revert) |
| 2 | 37 (35–39) | 37 (35–39) | 18 (16–19) | 17.5 (15–18) | 16 (14–16) | 32.5 (30–33) | 17 (15–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 5 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–18) | 15.5 (14–16) | 32 (30–32) | 17 (15–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 10 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–18) | 15.5 (14–16) | 32 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 20 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (14–16) | 32 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 50 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (14–16) | 31 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 100 | 37.5 (36–39) | 37.5 (36–39) | 18 (16–19) | 17 (16–17) | 16 (14–16) | 31 (30–32) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 365 | 37 (36–38) | 37 (36–38) | 18 (17–19) | 17 (16–17) | 16 (15–17) | 30.5 (30–31) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) |
| 1000 | 37.5 (37–38) | 37.5 (37–38) | 18 (17–19) | 17 (16–18) | 16 (15–17) | 30 (30–31) | 17 (16–18) | — (8 revert) | — (8 revert) | — (8 revert) |
| 10000 | 38 (37–39) | 38 (37–39) | 18 (17–20) | 17 (17–18) | 16 (16–17) | 30 (29–30) | 17 (17–17) | — (8 revert) | — (8 revert) | — (8 revert) |

## cumulative-product: Cumulative product of small factors

Step: `p = p * (1 + eps_i), eps_i = +eps for odd i, -eps for even i`. Result: product after N factors.

The general form of fee accrual, index levels and LP share accounting: many factors a basis point from one. The drift from 1 is where the digits are, and it is small.

Inputs: **reference** eps = 0.0001 (a basis point); **percent** eps = 0.01 (one percent); **tenth-percent** eps = 0.001 (ten basis points); **micro** eps = 0.000001 (a hundredth of a basis point: the factors are within WAD's last digits of one); **five-percent** eps = 0.05 (large factors: the product falls to 4e-6 by N = 10,000)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `1.0001` | 39 / exact / 2,644 | 39 / exact / 1,411 | 20 / exact / 1,491 | exact / exact / 1,234 | exact / exact / 1,594 | 35 / 35 / 5,693 | exact / exact / 1,505 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `0.99999999` | 39 / 39 / 2,188 | 39 / 39 / 940 | 19 / 19 / 944 | exact / exact / 789 | exact / exact / 1,149 | 33 / 33 / 3,409 | exact / exact / 1,060 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `1.000099979998` | 38 / 38 / 1,915 | 38 / 38 / 657 | 18 / 18 / 616 | 20 / 20 / 522 | 20 / 20 / 882 | 33 / 33 / 2,023 | 20 / 20 / 793 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `0.999999950000001` | 37 / 37 / 1,824 | 37 / 37 / 563 | 18 / 18 / 506 | 17 / 17 / 433 | 17 / 17 / 793 | 32 / 32 / 1,566 | 17 / 17 / 704 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `0.9999999000000045` | 37 / 37 / 1,779 | 37 / 37 / 516 | 18 / 18 / 452 | 17 / 17 / 388 | 17 / 17 / 748 | 32 / 32 / 1,335 | 17 / 17 / 659 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `0.99999975000003` | 37 / 37 / 1,751 | 37 / 37 / 488 | 17 / 17 / 419 | 16 / 16 / 362 | 16 / 16 / 722 | 32 / 32 / 1,197 | 16 / 16 / 633 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `0.9999995000001225` | 36 / 36 / 1,742 | 36 / 36 / 478 | 17 / 17 / 408 | 16 / 16 / 353 | 16 / 16 / 713 | 31 / 31 / 1,151 | 16 / 16 / 624 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `1.000098179819647` | 36 / 36 / 1,736 | 36 / 36 / 472 | 16 / 16 / 400 | 15 / 15 / 346 | 15 / 15 / 706 | 31 / 31 / 1,118 | 15 / 15 / 617 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `0.999995000012475` | 35 / 35 / 1,736 | 35 / 35 / 470 | 16 / 16 / 398 | 15 / 15 / 345 | 15 / 15 / 705 | 30 / 30 / 1,110 | 15 / 15 / 616 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `0.9999500012497292` | 34 / 34 / 1,753 | 34 / 34 / 469 | 15 / 15 / 397 | 14 / 14 / 344 | 14 / 14 / 704 | 29 / 29 / 1,105 | 14 / 14 / 615 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (5): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 40 (40–40) | 40 (40–40) | 34 (33–35) | 40 (40–40) | — (5 revert) | — (5 revert) | — (5 revert) |
| 2 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 40 (40–40) | 40 (40–40) | 33 (33–34) | 40 (40–40) | — (5 revert) | — (5 revert) | — (5 revert) |
| 5 | 38 (37–38) | 38 (37–38) | 18 (18–19) | 40 (20–40) | 40 (20–40) | 33 (33–33) | 40 (20–40) | — (5 revert) | — (5 revert) | — (5 revert) |
| 10 | 37 (37–37) | 37 (37–37) | 18 (18–19) | 18 (17–22) | 18 (17–22) | 32 (32–33) | 18 (17–22) | — (5 revert) | — (5 revert) | — (5 revert) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 17 (17–22) | 17 (17–22) | 32 (32–32) | 17 (17–22) | — (5 revert) | — (5 revert) | — (5 revert) |
| 50 | 37 (37–37) | 37 (37–37) | 17 (17–18) | 16 (16–21) | 16 (16–21) | 32 (32–32) | 16 (16–21) | — (5 revert) | — (5 revert) | — (5 revert) |
| 100 | 36 (36–36) | 36 (36–36) | 17 (17–17) | 16 (16–20) | 16 (16–20) | 31 (31–31) | 16 (16–20) | — (5 revert) | — (5 revert) | — (5 revert) |
| 365 | 36 (36–36) | 36 (36–36) | 16 (16–17) | 15 (15–19) | 15 (15–19) | 31 (31–31) | 15 (15–19) | — (5 revert) | — (5 revert) | — (5 revert) |
| 1000 | 35 (35–35) | 35 (35–35) | 16 (16–16) | 15 (15–18) | 15 (15–18) | 30 (30–30) | 15 (15–18) | — (5 revert) | — (5 revert) | — (5 revert) |
| 10000 | 34 (30–34) | 34 (30–34) | 15 (11–15) | 14 (9–16) | 14 (9–16) | 29 (29–29) | 14 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 34 (33–35) | 40 (40–40) | — (5 revert) | — (5 revert) | — (5 revert) |
| 2 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 40 (40–40) | 40 (40–40) | 33 (33–34) | 40 (40–40) | — (5 revert) | — (5 revert) | — (5 revert) |
| 5 | 38 (38–38) | 38 (38–38) | 18 (18–19) | 40 (20–40) | 40 (20–40) | 33 (33–33) | 40 (20–40) | — (5 revert) | — (5 revert) | — (5 revert) |
| 10 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 18 (17–22) | 18 (17–22) | 32 (32–33) | 18 (17–22) | — (5 revert) | — (5 revert) | — (5 revert) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 17 (17–22) | 17 (17–22) | 32 (32–32) | 17 (17–22) | — (5 revert) | — (5 revert) | — (5 revert) |
| 50 | 37 (37–37) | 37 (37–37) | 17 (17–17) | 16 (16–21) | 16 (16–21) | 32 (32–32) | 16 (16–21) | — (5 revert) | — (5 revert) | — (5 revert) |
| 100 | 36 (36–36) | 36 (36–36) | 17 (17–17) | 16 (16–20) | 16 (16–20) | 31 (31–31) | 16 (16–20) | — (5 revert) | — (5 revert) | — (5 revert) |
| 365 | 36 (36–36) | 36 (36–36) | 16 (16–17) | 15 (15–19) | 15 (15–19) | 31 (31–31) | 15 (15–19) | — (5 revert) | — (5 revert) | — (5 revert) |
| 1000 | 35 (35–35) | 35 (35–35) | 16 (16–16) | 15 (15–18) | 15 (15–18) | 30 (30–30) | 15 (15–18) | — (5 revert) | — (5 revert) | — (5 revert) |
| 10000 | 34 (30–34) | 34 (30–34) | 15 (11–15) | 14 (9–16) | 14 (9–16) | 29 (29–29) | 14 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) |

## compound-annual: Annual compounding at 10% (README claim check)

Step: `b = b * 1.1`. Result: balance after N years.

The old README asserted $25,937.42 true against $25,932.38 for Solady at N = 10 with no source. This row regenerates that number.

Inputs: **reference** principal = 10000, rate = 0.1 (the README claim); **five-pct** principal = 10000, rate = 0.05 (5% a year); **unit** principal = 1, rate = 0.1 (one unit); **million** principal = 1000000, rate = 0.1 (a million units: ABDK overflows sooner); **fifty-pct** principal = 10000, rate = 0.5 (50% a year: every library overflows before N = 100)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `11000.0` | 38 / exact / 2,403 | 38 / exact / 1,143 | 19 / exact / 1,189 | exact / exact / 999 | exact / exact / 1,359 | 33 / 33 / 3,188 | exact / exact / 1,270 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 610 |
| 2 | `12100.0` | 38 / exact / 2,012 | 38 / exact / 750 | 19 / 39 / 737 | exact / exact / 616 | exact / exact / 976 | 33 / 33 / 2,101 | exact / exact / 887 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 420 |
| 5 | `16105.1` | 38 / 42 / 1,778 | 38 / 42 / 515 | 18 / 23 / 466 | exact / exact / 386 | exact / exact / 746 | 33 / 33 / 1,449 | exact / exact / 657 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 197 |
| 10 | `25937.424601` | 37 / 42 / 1,700 | 37 / 42 / 436 | 18 / 23 / 376 | exact / exact / 309 | exact / exact / 669 | 32 / 32 / 1,228 | exact / exact / 580 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 121 |
| 20 | `67274.999493256` | 37 / 42 / 1,661 | 37 / 42 / 397 | 18 / 22 / 331 | exact / exact / 271 | exact / exact / 631 | 32 / 32 / 1,117 | exact / exact / 542 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 68 |
| 50 | `1173908.528796953` | 37 / 41 / 1,637 | 37 / 41 / 373 | 17 / 22 / 304 | 22 / 22 / 248 | 22 / 22 / 608 | 32 / 32 / 1,052 | 22 / 22 / 519 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 29 / 29 / 31 |
| 100 | `137806123.3982227` | 36 / 41 / 1,630 | 36 / 41 / 365 | 17 / 22 / 295 | 22 / 22 / 240 | 22 / 22 / 600 | 31 / 31 / 1,030 | 22 / 22 / 511 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 29 / 29 / 17 |
| 365 | `1.283305580313353e+19` | 36 / 41 / 1,624 | 36 / 41 / 360 | reverts `0x00000000` | 22 / 22 / 235 | 22 / 22 / 595 | 31 / 31 / 1,015 | 22 / 22 / 506 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 28 / 28 / 6 |
| 1000 | `2.469932918005826e+45` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | 22 / 22 / 602 | 30 / 30 / 1,011 | reverts `0x4e487b71` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x49f7642b` |
| 10000 | `8.449900251200348e+417` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | reverts `0x120b5b43` | 29 / 29 / 1,009 | reverts `0x4e487b71` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x49f7642b` |

### All inputs (5): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–40) | 38 (38–40) | 19 (19–40) | 40 (40–40) | 40 (40–40) | 33 (33–40) | 40 (40–40) | — (5 revert) | — (5 revert) | 40 (40–40) |
| 2 | 38 (38–40) | 38 (38–40) | 19 (19–40) | 40 (40–40) | 40 (40–40) | 33 (33–40) | 40 (40–40) | — (5 revert) | — (5 revert) | 40 (40–40) |
| 5 | 38 (37–40) | 38 (37–40) | 18 (18–40) | 40 (40–40) | 40 (40–40) | 33 (32–40) | 40 (40–40) | — (5 revert) | — (5 revert) | 40 (40–40) |
| 10 | 37 (37–40) | 37 (37–40) | 18 (18–40) | 40 (40–40) | 40 (40–40) | 32 (32–40) | 40 (40–40) | — (5 revert) | — (5 revert) | 40 (40–40) |
| 20 | 37 (37–40) | 37 (37–40) | 18 (18–40) | 40 (18–40) | 40 (18–40) | 32 (32–40) | 40 (18–40) | — (5 revert) | — (5 revert) | 40 (28–40) |
| 50 | 37 (36–40) | 37 (36–40) | 17 (17–40) | 22 (18–25) | 22 (18–25) | 32 (31–40) | 22 (18–25) | — (5 revert) | — (5 revert) | 29 (28–33) |
| 100 | 36 (36–40) | 36 (36–40) | 17 (17–17), 1 revert | 22 (18–25) | 22 (18–25) | 31 (31–32) | 22 (18–25) | — (5 revert) | — (5 revert) | 29 (27–33) |
| 365 | 36 (36–36), 1 revert | 36 (36–36), 1 revert | 16 (16–16), 3 revert | 21.5 (18–24), 1 revert | 21.5 (18–24), 1 revert | 31 (31–31) | 21.5 (18–24), 1 revert | — (5 revert) | — (5 revert) | 28 (26–28), 1 revert |
| 1000 | 35 (35–35), 4 revert | 35 (35–35), 4 revert | — (5 revert) | 21 (21–21), 4 revert | 21.5 (18–24), 1 revert | 30 (30–31) | 21 (21–21), 4 revert | — (5 revert) | — (5 revert) | — (5 revert) |
| 10000 | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | 29 (29–30) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 33 (33–40) | 40 (40–40) | — (5 revert) | — (5 revert) | 40 (40–40) |
| 2 | 40 (38–40) | 40 (38–40) | 39 (20–40) | 40 (40–40) | 40 (40–40) | 33 (33–40) | 40 (40–40) | — (5 revert) | — (5 revert) | 40 (40–40) |
| 5 | 40 (38–40) | 40 (38–40) | 23 (19–40) | 40 (40–40) | 40 (40–40) | 33 (32–40) | 40 (40–40) | — (5 revert) | — (5 revert) | 40 (40–40) |
| 10 | 40 (38–40) | 40 (38–40) | 23 (18–40) | 40 (40–40) | 40 (40–40) | 32 (32–40) | 40 (40–40) | — (5 revert) | — (5 revert) | 40 (40–40) |
| 20 | 40 (37–40) | 40 (37–40) | 22 (18–40) | 40 (18–40) | 40 (18–40) | 32 (32–40) | 40 (18–40) | — (5 revert) | — (5 revert) | 40 (28–40) |
| 50 | 40 (37–40) | 40 (37–40) | 22 (18–40) | 22 (18–25) | 22 (18–25) | 32 (31–40) | 22 (18–25) | — (5 revert) | — (5 revert) | 29 (28–33) |
| 100 | 40 (37–40) | 40 (37–40) | 22 (18–24), 1 revert | 22 (18–25) | 22 (18–25) | 31 (31–32) | 22 (18–25) | — (5 revert) | — (5 revert) | 29 (27–33) |
| 365 | 40 (37–40), 1 revert | 40 (37–40), 1 revert | 20 (18–22), 3 revert | 21.5 (18–24), 1 revert | 21.5 (18–24), 1 revert | 31 (31–31) | 21.5 (18–24), 1 revert | — (5 revert) | — (5 revert) | 28 (26–28), 1 revert |
| 1000 | 40 (40–40), 4 revert | 40 (40–40), 4 revert | — (5 revert) | 21 (21–21), 4 revert | 21.5 (18–24), 1 revert | 30 (30–31) | 21 (21–21), 4 revert | — (5 revert) | — (5 revert) | — (5 revert) |
| 10000 | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | 29 (29–30) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) |

## accrual-per-second: Per-second accrual

Step: `b = b0 * (1 + r/31536000)^(N * 86400)`. Result: balance after N days of per-second compounding.

How Maker's jug and pot accrue: the rate per second, compounded every second, N days at a time. The rate is 1.6e-9 at 5% APR, which an 18-decimal grid holds to ten digits before any arithmetic; FP127 computes the power as one exact integer power (compound), the WAD and 64.64 libraries as exp(n ln(1 + r)), Maker as rpow.

Inputs: **reference** principal = 10000, rateSec = 0.05/31536000 ($10,000 at 5% APR, the lending protocol's steady state); **one-pct** principal = 10000, rateSec = 0.01/31536000 (a slow rate: 1% APR is 3.2e-10 a second); **twenty-pct** principal = 10000, rateSec = 0.2/31536000 (20% APR); **fifty-pct** principal = 10000, rateSec = 0.5/31536000 (50% APR, where the three-term expansions strain); **unit** principal = 1, rateSec = 0.05/31536000 (one unit, the fraction carries everything); **huge** principal = 100000000, rateSec = 0.05/31536000 (a hundred-million-unit pool)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10001.36995684313` | 33 / 39 / 9,390 | 33 / 39 / 7,284 | 14 / 14 / 11,908 | 13 / 13 / 2,517 | 12 / 12 / 10,845 | 28 / 28 / 31,502 | 13 / 17 / 3,464 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 22 / 22 / 3,471 |
| 2 | `10002.74010136444` | 33 / 38 / 4,825 | 33 / 38 / 3,778 | 13 / 14 / 5,961 | 12 / 12 / 1,258 | 11 / 11 / 5,429 | 28 / 28 / 15,753 | 13 / 17 / 1,732 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 22 / 22 / 1,809 |
| 5 | `10006.85166125453` | 33 / 39 / 2,100 | 33 / 39 / 1,681 | 13 / 13 / 2,370 | 12 / 12 / 503 | 11 / 11 / 2,152 | 28 / 28 / 6,278 | 13 / 18 / 692 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 803 |
| 10 | `10013.70801703526` | 32 / 39 / 1,076 | 32 / 39 / 868 | 13 / 13 / 1,185 | 12 / 12 / 251 | 11 / 11 / 1,077 | 27 / 27 / 3,139 | 12 / 18 / 346 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 416 |
| 20 | `10027.43482504363` | 32 / 38 / 551 | 32 / 38 / 447 | 12 / 13 / 593 | 11 / 11 / 125 | 10 / 10 / 549 | 27 / 27 / 1,569 | 12 / 18 / 173 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 215 |
| 50 | `10068.72825267094` | 32 / 39 / 230 | 32 / 39 / 190 | 12 / 12 / 238 | 11 / 11 / 50 | 10 / 10 / 221 | 27 / 27 / 632 | 12 / 18 / 69 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 20 / 20 / 92 |
| 100 | `10137.92886261339` | 31 / 39 / 118 | 31 / 39 / 97 | 12 / 12 / 119 | 11 / 11 / 25 | 10 / 10 / 110 | 26 / 26 / 316 | 11 / 18 / 34 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 20 / 20 / 47 |
| 365 | `10512.71096334355` | 31 / 39 / 34 | 31 / 39 / 28 | 11 / 11 / 32 | 10 / 10 / 6 | 9 / 9 / 30 | 26 / 26 / 86 | 11 / 18 / 9 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 19 / 20 / 13 |
| 1000 | `11468.12438528825` | 30 / 38 / 12 | 30 / 38 / 10 | 11 / 11 / 11 | 10 / 10 / 2 | 9 / 9 / 11 | 25 / 25 / 31 | 10 / 18 / 3 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 19 / 19 / 5 |
| 10000 | `39348.11638983319` | 29 / 40 / 1 | 29 / 40 / 1 | 10 / 10 / 1 | 9 / 9 / 0 | 8 / 8 / 1 | 24 / 24 / 3 | 9 / 18 / 0 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 18 / 18 / 0 |

### All inputs (6): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 33 (33–35) | 33 (33–35) | 14 (14–14) | 12.5 (12–13) | 12 (12–12) | 28 (28–29) | 13 (13–13) | — (6 revert) | — (6 revert) | 22 (22–23) |
| 2 | 33 (33–34) | 33 (33–34) | 13 (13–14) | 12 (12–12) | 11 (11–11) | 28 (28–29) | 12.5 (12–13) | — (6 revert) | — (6 revert) | 22 (21–23) |
| 5 | 33 (32–34) | 33 (32–34) | 13 (13–13) | 12 (12–12) | 11 (11–11) | 28 (28–28) | 12.5 (12–13) | — (6 revert) | — (6 revert) | 21 (21–22) |
| 10 | 32 (32–34) | 32 (32–34) | 13 (13–13) | 11.5 (11–12) | 11 (11–11) | 27 (27–28) | 12 (12–12) | — (6 revert) | — (6 revert) | 21 (21–22) |
| 20 | 32 (32–33) | 32 (32–33) | 12 (12–13) | 11 (11–11) | 10 (10–10) | 27 (27–28) | 11.5 (11–12) | — (6 revert) | — (6 revert) | 21 (20–22) |
| 50 | 32 (31–33) | 32 (31–33) | 12 (12–12) | 11 (11–11) | 10 (10–10) | 27 (27–27) | 11.5 (11–12) | — (6 revert) | — (6 revert) | 20 (20–21) |
| 100 | 31 (31–33) | 31 (31–33) | 12 (12–12) | 10.5 (10–11) | 10 (10–10) | 26 (26–27) | 11 (11–11) | — (6 revert) | — (6 revert) | 20 (20–21) |
| 365 | 31 (31–32) | 31 (31–32) | 11 (11–11) | 10 (10–10) | 9 (9–9) | 26 (26–26) | 10.5 (10–11) | — (6 revert) | — (6 revert) | 19 (19–21) |
| 1000 | 30 (30–32) | 30 (30–32) | 11 (11–11) | 9.5 (9–10) | 9 (9–9) | 25 (25–26) | 10 (10–10) | — (6 revert) | — (6 revert) | 19 (19–20) |
| 10000 | 29 (29–31) | 29 (29–31) | 10 (10–10) | 8.5 (8–9) | 8 (8–8) | 24 (24–25) | 9 (9–9) | — (6 revert) | — (6 revert) | 18 (18–19) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 (38–39) | 39 (38–39) | 14 (14–14) | 13 (13–13) | 12 (12–12) | 28 (28–29) | 17.5 (17–18) | — (6 revert) | — (6 revert) | 22 (22–23) |
| 2 | 38 (38–39) | 38 (38–39) | 14 (13–14) | 12 (12–13) | 11 (11–11) | 28 (28–29) | 17 (17–18) | — (6 revert) | — (6 revert) | 22 (22–22) |
| 5 | 39 (39–39) | 39 (39–39) | 13 (13–13) | 12 (12–12) | 11 (11–11) | 28 (28–28) | 17.5 (17–18) | — (6 revert) | — (6 revert) | 21.5 (21–22) |
| 10 | 39 (38–40) | 39 (38–40) | 13 (13–13) | 12 (12–12) | 11 (11–11) | 27 (27–28) | 17.5 (17–18) | — (6 revert) | — (6 revert) | 21 (21–22) |
| 20 | 38 (38–39) | 38 (38–39) | 13 (12–13) | 11 (11–12) | 10 (10–10) | 27 (27–28) | 18 (17–18) | — (6 revert) | — (6 revert) | 21 (21–21) |
| 50 | 39 (38–39) | 39 (38–39) | 12 (12–12) | 11 (11–11) | 10 (10–10) | 27 (27–27) | 18 (17–18) | — (6 revert) | — (6 revert) | 20.5 (20–21) |
| 100 | 39 (38–39) | 39 (38–39) | 12 (12–12) | 11 (11–11) | 10 (10–10) | 26 (26–27) | 18 (17–18) | — (6 revert) | — (6 revert) | 20 (20–21) |
| 365 | 39 (39–40) | 39 (39–40) | 11 (11–12) | 10 (10–11) | 9 (9–9) | 26 (26–26) | 18 (17–18) | — (6 revert) | — (6 revert) | 20 (20–20) |
| 1000 | 38.5 (38–39) | 38.5 (38–39) | 11 (11–11) | 10 (10–10) | 9 (9–9) | 25 (25–26) | 18 (17–18) | — (6 revert) | — (6 revert) | 19 (19–20) |
| 10000 | 40 (39–40) | 40 (39–40) | 10 (10–10) | 9 (9–9) | 8 (8–8) | 24 (24–25) | 18 (17–18) | — (6 revert) | — (6 revert) | 18 (18–19) |

## accrual-continuous: Continuous accrual

Step: `b = b0 * e^(r * N / 365)`. Result: balance after N days of continuous accrual.

How Aave and Morpho accrue: the ideal is e^(rate * time), and both ship a three-term expansion of it (1 + x + x^2/2 + x^3/6), which Aave notes 'slightly underpays liquidity providers and undercharges borrowers'. Every library is judged against the exponential it approximates. The step here is one accrual spanning N days, which is what a market that nobody touched for N days computes on its next interaction; the expansion's error is x^4/24 with x = rate * years, so it is invisible at daily updates and the whole story at a year or more. Morpho holds the rate per second in WAD (1,585,489,599 wei at 5% APR), ten significant digits before any arithmetic; both digit counts show that loss, since the format truth is built from the annual rate the other libraries receive.

Inputs: **reference** principal = 10000, rateAnnual = 0.05 ($10,000 at 5% APR, the lending protocol's steady state); **one-pct** principal = 10000, rateAnnual = 0.01 (a slow rate: 1% APR is 3.2e-10 a second); **twenty-pct** principal = 10000, rateAnnual = 0.2 (20% APR); **fifty-pct** principal = 10000, rateAnnual = 0.5 (50% APR, where the three-term expansions strain); **unit** principal = 1, rateAnnual = 0.05 (one unit, the fraction carries everything); **huge** principal = 100000000, rateAnnual = 0.05 (a hundred-million-unit pool)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10001.36995684422` | 38 / 38 / 10,489 | 38 / 38 / 7,338 | 19 / 19 / 5,082 | 18 / 18 / 2,062 | 18 / 18 / 5,114 | 33 / 33 / 11,226 | 18 / 18 / 3,453 | 16 / 16 / 1,608 | 13 / 13 / 1,442 | reverts `0x7bb9ae15` |
| 2 | `10002.74010136661` | 38 / 38 / 5,244 | 38 / 38 / 3,669 | 19 / 19 / 2,541 | 18 / 18 / 1,031 | 17 / 17 / 2,564 | 33 / 33 / 5,615 | 18 / 18 / 1,726 | 15 / 15 / 804 | 13 / 13 / 721 | reverts `0x7bb9ae15` |
| 5 | `10006.85166125997` | 39 / 39 / 2,097 | 39 / 39 / 1,467 | 19 / 19 / 1,010 | 18 / 18 / 412 | 17 / 17 / 1,025 | 34 / 34 / 2,234 | 18 / 18 / 690 | 14 / 14 / 321 | 13 / 13 / 288 | reverts `0x7bb9ae15` |
| 10 | `10013.70801704614` | 38 / 38 / 1,048 | 38 / 38 / 733 | 18 / 18 / 506 | 18 / 18 / 206 | 17 / 17 / 515 | 33 / 33 / 1,117 | 18 / 18 / 345 | 12 / 12 / 160 | 12 / 12 / 144 | reverts `0x7bb9ae15` |
| 20 | `10027.43482506541` | 38 / 38 / 524 | 38 / 38 / 366 | 19 / 19 / 253 | 18 / 18 / 103 | 18 / 18 / 267 | 34 / 34 / 558 | 18 / 18 / 172 | 11 / 11 / 80 | 11 / 11 / 72 | reverts `0x7bb9ae15` |
| 50 | `10068.72825272561` | 38 / 38 / 209 | 38 / 38 / 146 | 18 / 18 / 103 | 18 / 18 / 41 | 17 / 17 / 108 | 33 / 33 / 223 | 18 / 18 / 69 | 10 / 10 / 32 | 10 / 10 / 28 | reverts `0x7bb9ae15` |
| 100 | `10137.92886272349` | 38 / 38 / 104 | 38 / 38 / 73 | 19 / 19 / 50 | 18 / 18 / 20 | 17 / 17 / 54 | 34 / 34 / 111 | 18 / 18 / 34 | 8 / 8 / 16 | 8 / 8 / 14 | reverts `0x7bb9ae15` |
| 365 | `10512.71096376024` | 38 / 39 / 28 | 38 / 39 / 20 | 19 / 20 / 14 | 18 / 18 / 5 | 18 / 18 / 15 | 33 / 33 / 30 | 18 / 18 / 9 | 6 / 6 / 4 | 6 / 6 / 3 | reverts `0x7bb9ae15` |
| 1000 | `11468.12438653363` | 38 / 38 / 10 | 38 / 38 / 7 | 18 / 19 / 5 | 18 / 18 / 2 | 17 / 17 / 5 | 33 / 33 / 11 | 18 / 18 / 3 | 4 / 4 / 1 | 4 / 4 / 1 | reverts `0x7bb9ae15` |
| 10000 | `39348.11643256335` | 37 / 38 / 1 | 37 / 38 / 0 | 17 / 19 / 0 | 17 / 17 / 0 | 17 / 17 / 0 | 33 / 33 / 1 | 17 / 17 / 0 | 1 / 1 / 0 | 1 / 1 / 0 | reverts `0x7bb9ae15` |

### All inputs (6): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 18 (17–18) | 17.5 (17–18) | 33.5 (33–34) | 18 (17–18) | 16 (12–19) | 13 (12–13) | — (6 revert) |
| 2 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 18 (17–18) | 17 (17–18) | 33 (33–34) | 18 (17–18) | 15 (11–18) | 12.5 (11–13) | — (6 revert) |
| 5 | 39 (38–39) | 39 (38–39) | 19 (19–19) | 18 (18–18) | 17 (17–18) | 34 (33–34) | 18 (18–18) | 14 (10–16) | 12.5 (10–13) | — (6 revert) |
| 10 | 38 (38–39) | 38 (38–39) | 18.5 (18–19) | 18 (18–18) | 17 (17–17) | 33 (33–34) | 18 (18–18) | 12 (8–15) | 12 (8–12) | — (6 revert) |
| 20 | 38 (38–39) | 38 (38–39) | 19 (18–19) | 18 (17–18) | 17.5 (17–18) | 34 (33–34) | 18 (17–18) | 11 (7–14) | 11 (7–11) | — (6 revert) |
| 50 | 38 (38–39) | 38 (38–39) | 18 (18–19) | 18 (17–18) | 17 (17–17) | 33 (33–34) | 18 (17–18) | 10 (6–12) | 10 (6–11) | — (6 revert) |
| 100 | 38 (38–39) | 38 (38–39) | 19 (18–19) | 18 (18–18) | 17 (17–18) | 33.5 (33–34) | 18 (18–18) | 8 (4–11) | 8 (4–11) | — (6 revert) |
| 365 | 38 (38–40) | 38 (38–40) | 19 (19–19) | 18 (18–18) | 18 (17–18) | 33 (33–34) | 18 (18–18) | 6 (2–9) | 6 (2–9) | — (6 revert) |
| 1000 | 38 (38–38) | 38 (38–38) | 18 (18–19) | 17.5 (17–18) | 17 (17–17) | 33 (33–34) | 17.5 (17–18) | 4 (1–7) | 4 (1–7) | — (6 revert) |
| 10000 | 37 (37–38) | 37 (37–38) | 17.5 (17–19) | 17.5 (17–18) | 17 (17–18) | 33 (32–33) | 17 (17–18) | 1 (0–3) | 1 (0–3) | — (6 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 18 (17–18) | 17.5 (17–18) | 33.5 (33–34) | 18 (17–18) | 16 (12–19) | 13 (12–13) | — (6 revert) |
| 2 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 18 (17–18) | 17 (17–18) | 33 (33–34) | 18 (17–18) | 15 (11–18) | 12.5 (11–13) | — (6 revert) |
| 5 | 39 (38–39) | 39 (38–39) | 19 (19–19) | 18 (18–18) | 17 (17–18) | 34 (33–34) | 18 (18–18) | 14 (10–16) | 12.5 (10–13) | — (6 revert) |
| 10 | 38 (38–39) | 38 (38–39) | 18.5 (18–19) | 18 (18–18) | 17 (17–17) | 33 (33–34) | 18 (18–18) | 12 (8–15) | 12 (8–12) | — (6 revert) |
| 20 | 38 (38–39) | 38 (38–39) | 19 (18–19) | 18 (17–18) | 17.5 (17–18) | 34 (33–34) | 18 (17–18) | 11 (7–14) | 11 (7–11) | — (6 revert) |
| 50 | 38 (38–39) | 38 (38–39) | 18 (18–19) | 18 (17–18) | 17 (17–17) | 33 (33–34) | 18 (17–18) | 10 (6–12) | 10 (6–11) | — (6 revert) |
| 100 | 38 (38–39) | 38 (38–39) | 19 (18–19) | 18 (18–18) | 17 (17–18) | 33.5 (33–34) | 18 (18–18) | 8 (4–11) | 8 (4–11) | — (6 revert) |
| 365 | 39 (38–40) | 39 (38–40) | 19.5 (19–20) | 18 (18–18) | 18 (17–18) | 33 (33–34) | 18 (18–18) | 6 (2–9) | 6 (2–9) | — (6 revert) |
| 1000 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 17.5 (17–18) | 17 (17–17) | 33 (33–34) | 17.5 (17–18) | 4 (1–7) | 4 (1–7) | — (6 revert) |
| 10000 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 17.5 (17–18) | 17 (17–18) | 33 (32–33) | 17 (17–18) | 1 (0–3) | 1 (0–3) | — (6 revert) |

## deep-tail-option: An option walking out of the money

Step: `S = S (1 - tick); then C = S N(d1) - K e^(-rT) N(d2)`. Result: the Black-Scholes call price after N down-ticks of the spot.

Options protocols price with N(d), the normal distribution function, and the spot walks. Near the money every library agrees; past d = -8 an 18-decimal N(d) is zero and the price with it, and before that e^(-d^2/2) has lost most of its digits. FP127 has normCdf as an op; the other libraries run the same series and continued fraction through their own exp, sqrt, mul and div, with pi by Ramanujan through the same ops, so each is judged on its primitives.

Inputs: **reference** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.000173 (at the money, 20% vol, six months; d1 reaches -12 at N = 10,000); **slow-walk** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.0001 (a slower walk: d1 reaches -7 at N = 10,000, where an 18-decimal N(d) has a few digits left); **fast-walk** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.0005 (a faster walk: d1 passes -12 near N = 3,500; beyond it the price is below every grid); **low-vol** spot = 100, strike = 100, sigma = 0.05, T = 0.5, r = 0.05, tick = 0.00005 (5% vol: d moves four times faster per tick); **high-vol** spot = 100, strike = 100, sigma = 0.8, T = 0.5, r = 0.05, tick = 0.0007 (80% vol: a long way to the tail); **short-dated** spot = 100, strike = 100, sigma = 0.2, T = 0.01, r = 0.05, tick = 0.00003 (ten days to expiry: sigma sqrt(T) is 0.02 and the tail comes fast)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `6.878391866103811` | 37 / 37 / 53,688 | 37 / 37 / 44,487 | 18 / 18 / 82,136 | 16 / 16 / 57,287 | 16 / 16 / 112,727 | 32 / 32 / 288,970 | 16 / 16 / 99,962 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `6.868065132714932` | 37 / 38 / 27,655 | 37 / 38 / 22,422 | 18 / 17 / 41,211 | 17 / 17 / 28,760 | 16 / 16 / 56,658 | 32 / 32 / 144,950 | 17 / 17 / 50,233 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `6.837144794797698` | 37 / 39 / 11,988 | 37 / 39 / 9,132 | 18 / 18 / 16,636 | 16 / 16 / 11,643 | 16 / 16 / 23,027 | 32 / 32 / 58,561 | 16 / 16 / 20,395 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `6.785810396029252` | 36 / 38 / 6,805 | 36 / 38 / 4,745 | 18 / 18 / 8,466 | 16 / 16 / 5,938 | 16 / 16 / 11,808 | 31 / 31 / 29,375 | 16 / 16 / 10,449 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `6.683889366360745` | 36 / 38 / 4,213 | 36 / 38 / 2,551 | 17 / 17 / 4,374 | 16 / 16 / 3,041 | 16 / 16 / 6,120 | 31 / 31 / 14,955 | 16 / 16 / 5,404 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `6.384100145151291` | 36 / 38 / 2,641 | 36 / 38 / 1,216 | 17 / 18 / 1,899 | 16 / 16 / 1,338 | 16 / 16 / 2,766 | 31 / 31 / 6,501 | 16 / 16 / 2,434 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `5.904291981569546` | 35 / 37 / 2,116 | 35 / 37 / 769 | 16 / 17 / 1,071 | 16 / 16 / 769 | 16 / 16 / 1,648 | 30 / 30 / 3,567 | 16 / 16 / 1,441 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `3.76450175108814` | 35 / 37 / 1,767 | 35 / 37 / 481 | 16 / 17 / 519 | 16 / 16 / 394 | 16 / 16 / 909 | 30 / 30 / 1,784 | 16 / 16 / 785 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `0.9741872197637135` | 34 / 36 / 1,683 | 34 / 36 / 410 | 15 / 16 / 388 | 15 / 15 / 305 | 15 / 15 / 733 | 29 / 29 / 1,354 | 15 / 15 / 628 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `4.263958353856216e-34` | 3 / 3 / 1,648 | 3 / 3 / 364 | 0 / 0 / 315 | 0 / 0 / 254 | 0 / 0 / 637 | 27 / 27 / 1,082 | reverts `0xd4794efd` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (6): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 (36–38) | 37 (36–38) | 18 (17–18) | 16 (16–16) | 16 (16–17) | 32 (31–32) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 2 | 37 (36–38) | 37 (36–38) | 17.5 (17–18) | 16 (16–17) | 16 (16–16) | 32 (31–32) | 16 (16–17) | — (6 revert) | — (6 revert) | — (6 revert) |
| 5 | 37 (36–38) | 37 (36–38) | 17.5 (17–18) | 16 (16–17) | 16 (16–16) | 32 (31–32) | 16 (15–17) | — (6 revert) | — (6 revert) | — (6 revert) |
| 10 | 36 (36–38) | 36 (36–38) | 17 (17–18) | 16 (15–17) | 16 (15–16) | 31 (31–32) | 16 (15–17) | — (6 revert) | — (6 revert) | — (6 revert) |
| 20 | 36 (35–38) | 36 (35–38) | 17 (16–17) | 16 (15–16) | 16 (16–16) | 31 (30–32) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 50 | 36 (35–38) | 36 (35–38) | 16.5 (16–18) | 16 (16–16) | 16 (16–17) | 31 (30–31) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 100 | 35 (35–38) | 35 (35–38) | 16 (15–19) | 16 (16–16) | 16 (16–19) | 30 (30–31) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 365 | 34.5 (34–37) | 34.5 (34–37) | 15.5 (15–17) | 16 (15–16) | 16 (15–16) | 30 (29–30) | 15.5 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 1000 | 34 (33–36) | 34 (33–36) | 14.5 (12–17) | 15 (11–15) | 15 (10–15) | 29 (27–30) | 15 (10–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 10000 | 0.5 (0–25) | 0.5 (0–25) | 0 (0–6) | 0 (0–4) | 0 (0–4) | 27 (26–28) | 4 (4–4), 5 revert | — (6 revert) | — (6 revert) | — (6 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 (36–38) | 37 (36–38) | 18 (17–18) | 16 (16–16) | 16 (16–17) | 32 (31–32) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 2 | 38 (36–38) | 38 (36–38) | 17.5 (17–18) | 16 (16–17) | 16 (16–16) | 32 (31–32) | 16 (16–17) | — (6 revert) | — (6 revert) | — (6 revert) |
| 5 | 37.5 (37–39) | 37.5 (37–39) | 17.5 (17–18) | 16 (16–17) | 16 (16–16) | 32 (31–32) | 16 (15–17) | — (6 revert) | — (6 revert) | — (6 revert) |
| 10 | 37.5 (37–38) | 37.5 (37–38) | 18 (16–18) | 16 (15–17) | 16 (15–16) | 31 (31–32) | 16 (15–17) | — (6 revert) | — (6 revert) | — (6 revert) |
| 20 | 37.5 (37–38) | 37.5 (37–38) | 17.5 (16–18) | 16 (15–16) | 16 (16–16) | 31 (30–32) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 50 | 37 (37–39) | 37 (37–39) | 17.5 (17–18) | 16 (16–16) | 16 (16–17) | 31 (30–31) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 100 | 37 (36–38) | 37 (36–38) | 17 (17–18) | 16 (16–16) | 16 (16–19) | 30 (30–31) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 365 | 37 (36–37) | 37 (36–37) | 17 (16–17) | 16 (15–16) | 16 (15–16) | 30 (29–30) | 15.5 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 1000 | 35.5 (34–37) | 35.5 (34–37) | 16 (12–17) | 15 (11–15) | 15 (10–15) | 29 (27–30) | 15 (10–16) | — (6 revert) | — (6 revert) | — (6 revert) |
| 10000 | 0.5 (0–25) | 0.5 (0–25) | 0 (0–6) | 0 (0–4) | 0 (0–4) | 27 (26–28) | 4 (4–4), 5 revert | — (6 revert) | — (6 revert) | — (6 revert) |

## decay: Decay, the share released

Step: `D = D e^(-eps); result 1 - D`. Result: the share released after N steps of decay.

Vesting, TWAP weights and exponential moving averages multiply by e^(-dt/tau) every step. The factor is a hair below one, and on an 18-decimal grid e^(-eps) rounds to a grid point whose distance from one is wrong by up to 1e-18 relative, every step: at eps = 1e-12 that is six digits of the released share, at 1e-15 three, at 1e-18 nothing is released at all.

Inputs: **reference** eps = 0.000001 (one millionth a step: a one-second step against a twelve-day time constant); **nano** eps = 0.000000001 (1e-9 a step: a one-second step against a thirty-year time constant); **pico** eps = 0.000000000001 (1e-12 a step: the factor is within WAD's last six digits of one); **femto** eps = 0.000000000000001 (1e-15 a step: three digits of the factor's distance from one survive on WAD); **atto** eps = 0.00000000000000001 (1e-17 a step: below WAD's grid, e^(-eps) is one and nothing decays)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `9.999995000001667e-7` | 32 / 33 / 7,978 | 32 / 33 / 6,642 | 13 / 13 / 4,981 | 12 / 12 / 1,824 | 12 / 12 / 4,038 | 28 / 28 / 11,056 | 12 / 12 / 2,685 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `1.999998000001333e-6` | 32 / 33 / 7,570 | 32 / 33 / 6,225 | 13 / 13 / 4,529 | 12 / 12 / 1,424 | 12 / 12 / 3,638 | 28 / 28 / 9,651 | 12 / 12 / 2,285 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `4.999987500020833e-6` | 33 / 34 / 7,326 | 33 / 34 / 5,975 | 13 / 13 / 4,258 | 12 / 12 / 1,184 | 12 / 12 / 3,398 | 28 / 28 / 8,801 | 12 / 12 / 2,045 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `9.999950000166666e-6` | 33 / 34 / 7,244 | 33 / 34 / 5,892 | 13 / 13 / 4,168 | 12 / 12 / 1,104 | 12 / 12 / 3,318 | 28 / 28 / 8,511 | 12 / 12 / 1,965 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `1.999980000133333e-5` | 33 / 33 / 7,203 | 33 / 33 / 5,850 | 13 / 13 / 4,123 | 12 / 12 / 1,064 | 12 / 12 / 3,278 | 28 / 28 / 8,372 | 12 / 12 / 1,925 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `4.999875002083307e-5` | 33 / 33 / 7,179 | 33 / 33 / 5,825 | 13 / 13 / 4,096 | 12 / 12 / 1,040 | 12 / 12 / 3,254 | 28 / 28 / 8,289 | 12 / 12 / 1,901 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `9.99950001666625e-5` | 33 / 33 / 7,171 | 33 / 33 / 5,817 | 13 / 13 / 4,087 | 12 / 12 / 1,032 | 12 / 12 / 3,246 | 28 / 28 / 8,261 | 12 / 12 / 1,893 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `0.0003649333956037813` | 33 / 33 / 7,168 | 33 / 33 / 5,811 | 13 / 13 / 4,080 | 11 / 11 / 1,026 | 12 / 12 / 3,240 | 28 / 28 / 8,240 | 11 / 11 / 1,887 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `0.0009995001666250083` | 33 / 33 / 7,171 | 33 / 33 / 5,809 | 13 / 13 / 4,078 | 11 / 11 / 1,024 | 12 / 12 / 3,238 | 28 / 28 / 8,235 | 11 / 11 / 1,885 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `0.009950166250831946` | 33 / 33 / 7,241 | 33 / 33 / 5,809 | 13 / 13 / 4,078 | 11 / 11 / 1,024 | 12 / 12 / 3,238 | 28 / 28 / 8,233 | 11 / 11 / 1,885 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

### All inputs (5): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 26 (21–32) | 26 (21–32) | 7 (2–13) | 12 (9–17) | 6 (1–12) | 22 (17–28) | 12 (9–17) | — (5 revert) | — (5 revert) | — (5 revert) |
| 2 | 26 (21–32) | 26 (21–32) | 7 (2–13) | 14 (11–18) | 6 (1–18) | 22 (17–28) | 14 (11–18) | — (5 revert) | — (5 revert) | — (5 revert) |
| 5 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–16) | 6 (1–12) | 22 (17–28) | 12 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) |
| 10 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–16) | 6 (1–12) | 22 (16–28) | 12 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) |
| 20 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–15) | 6 (1–12) | 22 (16–28) | 12 (9–15) | — (5 revert) | — (5 revert) | — (5 revert) |
| 50 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–15) | 6 (1–12) | 22 (16–28) | 12 (9–15) | — (5 revert) | — (5 revert) | — (5 revert) |
| 100 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–15) | 6 (1–12) | 22 (16–28) | 12 (9–15) | — (5 revert) | — (5 revert) | — (5 revert) |
| 365 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 11 (9–14) | 6 (1–12) | 22 (16–28) | 11 (9–14) | — (5 revert) | — (5 revert) | — (5 revert) |
| 1000 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 11 (9–14) | 6 (1–12) | 22 (16–28) | 11 (9–14) | — (5 revert) | — (5 revert) | — (5 revert) |
| 10000 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 11 (8–13) | 6 (1–12) | 21 (16–28) | 11 (8–13) | — (5 revert) | — (5 revert) | — (5 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–17) | 6 (1–12) | 22 (17–28) | 12 (9–17) | — (5 revert) | — (5 revert) | — (5 revert) |
| 2 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–16) | 6 (1–12) | 22 (17–28) | 12 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) |
| 5 | 27 (21–34) | 27 (21–34) | 7 (2–13) | 12 (8–16) | 6 (1–12) | 22 (17–28) | 12 (8–16) | — (5 revert) | — (5 revert) | — (5 revert) |
| 10 | 27 (21–34) | 27 (21–34) | 7 (2–13) | 12 (8–16) | 6 (1–12) | 22 (16–28) | 12 (8–16) | — (5 revert) | — (5 revert) | — (5 revert) |
| 20 | 27 (21–33) | 27 (21–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) |
| 50 | 28 (21–33) | 28 (21–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) |
| 100 | 28 (21–33) | 28 (21–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) |
| 365 | 29 (21–33) | 29 (21–33) | 7 (2–13) | 11 (8–14) | 6 (1–12) | 22 (16–28) | 11 (8–14) | — (5 revert) | — (5 revert) | — (5 revert) |
| 1000 | 28 (21–33) | 28 (21–33) | 7 (2–13) | 11 (8–14) | 6 (1–12) | 22 (16–28) | 11 (8–14) | — (5 revert) | — (5 revert) | — (5 revert) |
| 10000 | 28 (21–33) | 28 (21–33) | 7 (2–13) | 11 (8–13) | 6 (1–12) | 21 (16–28) | 11 (8–13) | — (5 revert) | — (5 revert) | — (5 revert) |

## Methodology

**truth.** For every scenario, input and N the same loop is run in exact real arithmetic with mpmath at 200 decimal digits (scripts/ladder/ladder.py), from the exact rational parameters in scenarios.json. Closed forms are used where the loop has one (compounding, the cumulative product, the geometric mean, the round trip, per-second and continuous accrual, the option walk and the decay); the bonding curve, the amortising loan and the Black-Scholes chain are stepped.

**rounding.** Each library receives the parameters floored into its own representation (2^-128, 2^-64, 10^-18 or 10^-27 units, or the nearest binary128 value for ABDKMathQuad; scripts/ladder/inputs.json). truthFormat is the exact loop started from those floored parameters, so digitsFormat measures the library's arithmetic alone, while digits measures what a protocol sees: the format's rounding of the inputs plus the arithmetic.

**digits.** digits = floor(-log10 |v - t| / |t|), the number of correct leading significant digits by relative error, capped at 60, which is reported as exact. It is not a string comparison: a value can be correct to 36 digits while its 37th printed digit happens to agree with the truth, or while a carry makes the printed prefix differ earlier.

**agree.** agree is the count of leading significant digits of the printed value (42 significant digits) that are literally equal to the printed truth. The demo page colours the rest of the value with it. It is a reading aid, not a measurement: a carry across 0.999… / 1.000… gives 0.

**gas.** gasTotal is measured inside the adapter around the scenario function (the parameter reads and the loop), after the runner has warmed the adapter and the FP127 object, so the call into the adapter and the ABI decoding are excluded. The FP127 (deployed) form includes one staticcall per op; FP127Lib and the other libraries are internal calls. Aave, Morpho and Maker answer only the accrual scenarios their models describe and report Unsupported elsewhere, which the tables show as a revert. gasPerStep = gasTotal / N. Reverted cells carry no gas.

**live.** LadderRunner.run(scenario, form, n, p) on Sepolia executes any cell with one eth_call and returns (ok, raw, reason, gasPerStep, gasTotal). The demo's verify button sends the cell's floored parameters p and compares the returned raw word with the committed one bit for bit (or the revert selector for a reverted cell). liveMaxN is the largest N per form the public RPC completed within its gas limit, measured by scripts/ladder/livecap.py.

**reproduce.** make ladder regenerates ladder.json and ladder.md from the Foundry harness (test/ladder/Ladder.t.sol) and this script; make ladder-check fails CI when the committed dataset differs. Versions of every library and of forge are recorded in the dataset.

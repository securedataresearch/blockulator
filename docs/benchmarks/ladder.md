# Terminal precision ladder

Generated 2026-10-15 by `make ladder`. Versions: fp127 279ec8a, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, forge forge Version: 1.7.1.

Each scenario is run for several inputs; the first table is the reference input in full (`digits / digitsFormat / gas per step`, where digits is against the exact truth and digitsFormat against the truth from the parameters as the library received them), the second is the summary over all inputs (`median (min–max)` digits, capped at 40). Full values, both truths, signed errors and raw words are in ladder.json; the method is in the Methodology section at the end.

## compound: Daily compound interest

Step: `b = b * (1 + r)`. Result: balance after N days.

Per-block or per-day accrual in every lending protocol: one mul per step, N steps.

Inputs: **reference** principal = 10000, rate = 0.1/365 ($10,000 at 10% APR, the headline cell); **tiny-low** principal = 1, rate = 0.01/365 (one unit at 1%: the integer part is small, the fraction carries everything); **tiny-high** principal = 1, rate = 0.5/365 (one unit at 50%); **mid-1pct** principal = 10000, rate = 0.01/365 (a slow rate: the per-step factor is close to 1); **mid-5pct** principal = 10000, rate = 0.05/365 (a typical lending rate); **mid-50pct** principal = 10000, rate = 0.5/365 (a high rate: the balance grows 150x by N = 10,000); **large** principal = 1000000, rate = 0.1/365 (a million-unit position); **huge** principal = 100000000, rate = 0.1/365 (a hundred-million-unit pool); **huge-high** principal = 100000000, rate = 0.5/365 (the largest balance the ladder reaches, near 10^14); **fraction** principal = 0.001, rate = 0.1/365 (a sub-unit balance: leading zeros in WAD)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10002.7397260274` | 38 / exact / 2,113 | 38 / exact / 928 | 19 / exact / 934 | 19 / exact / 752 | 19 / exact / 1,112 | 33 / 33 / 2,941 | 19 / exact / 1,023 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 27 / exact / 610 |
| 2 | `10005.48020266467` | 38 / 42 / 1,848 | 38 / 42 / 653 | 19 / 23 / 609 | 19 / 22 / 494 | 19 / 22 / 854 | 33 / 33 / 1,980 | 19 / 22 / 765 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 27 / 420 |
| 5 | `10013.70613829244` | 38 / 42 / 1,689 | 38 / 42 / 488 | 19 / 23 / 414 | 18 / 21 / 340 | 18 / 21 / 700 | 33 / 33 / 1,403 | 18 / 21 / 611 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 197 |
| 10 | `10027.43106240757` | 37 / 41 / 1,636 | 37 / 41 / 433 | 18 / 22 / 349 | 18 / 21 / 288 | 18 / 21 / 648 | 32 / 32 / 1,211 | 18 / 21 / 559 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 121 |
| 20 | `10054.93737113361` | 37 / 41 / 1,609 | 37 / 41 / 405 | 18 / 22 / 317 | 18 / 21 / 262 | 18 / 21 / 622 | 32 / 32 / 1,115 | 18 / 21 / 533 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 68 |
| 50 | `10137.90984214166` | 37 / 41 / 1,593 | 37 / 41 / 389 | 18 / 21 / 297 | 17 / 20 / 247 | 17 / 20 / 607 | 32 / 32 / 1,057 | 17 / 20 / 518 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 25 / 26 / 31 |
| 100 | `10277.72159673926` | 36 / 40 / 1,588 | 36 / 40 / 383 | 17 / 21 / 291 | 17 / 20 / 242 | 17 / 20 / 602 | 31 / 31 / 1,038 | 17 / 20 / 513 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 25 / 25 / 17 |
| 365 | `11051.55781616264` | 36 / 40 / 1,585 | 36 / 40 / 379 | 17 / 21 / 286 | 16 / 19 / 238 | 16 / 19 / 598 | 31 / 31 / 1,024 | 16 / 19 / 509 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 24 / 25 / 6 |
| 1000 | `13151.29420081218` | 35 / 39 / 1,585 | 35 / 39 / 378 | 16 / 20 / 285 | 16 / 19 / 237 | 16 / 19 / 597 | 30 / 30 / 1,020 | 16 / 19 / 508 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 24 / 24 / 2 |
| 10000 | `154769.3406914411` | 34 / 39 / 1,602 | 34 / 39 / 378 | 15 / 20 / 285 | 15 / 18 / 237 | 15 / 18 / 597 | 29 / 29 / 1,019 | 15 / 18 / 508 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 23 / 23 / 0 |

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
| 1 | `10002.7397260274` | 38 / exact / 3,233 | 38 / exact / 1,178 | 19 / 19 / 11,497 | 17 / 18 / 2,165 | 19 / exact / 1,448 | 33 / 33 / 28,834 | 17 / 18 / 3,108 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `10005.48020266467` | 38 / 38 / 1,721 | 38 / 38 / 706 | 18 / 18 / 5,748 | 17 / 18 / 1,082 | 16 / 16 / 5,378 | 33 / 33 / 14,419 | 17 / 18 / 1,554 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `10013.70613829244` | 38 / 38 / 2,125 | 38 / 38 / 2,124 | 18 / 18 / 2,282 | 17 / 17 / 433 | 16 / 16 / 2,123 | 33 / 33 / 5,731 | 17 / 18 / 621 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `10027.43106240757` | 37 / 39 / 1,062 | 37 / 39 / 1,062 | 18 / 18 / 1,141 | 17 / 17 / 216 | 16 / 16 / 1,063 | 33 / 33 / 2,866 | 18 / 18 / 310 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `10054.93737113361` | 37 / 39 / 531 | 37 / 39 / 531 | 17 / 18 / 570 | 17 / 17 / 108 | 15 / 15 / 531 | 33 / 33 / 1,432 | 17 / 18 / 155 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `10137.90984214166` | 37 / 38 / 212 | 37 / 38 / 212 | 17 / 17 / 230 | 16 / 16 / 43 | 15 / 15 / 218 | 32 / 32 / 573 | 17 / 18 / 62 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `10277.72159673926` | 36 / 39 / 106 | 36 / 39 / 106 | 17 / 17 / 115 | 16 / 16 / 21 | 15 / 15 / 109 | 32 / 32 / 286 | 17 / 17 / 31 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `11051.55781616264` | 36 / 39 / 29 | 36 / 39 / 29 | 16 / 16 / 31 | 15 / 15 / 5 | 14 / 14 / 29 | 31 / 31 / 78 | 16 / 18 / 8 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `13151.29420081218` | 35 / 39 / 10 | 35 / 39 / 10 | 16 / 16 / 11 | 15 / 15 / 2 | 14 / 14 / 11 | 31 / 31 / 28 | 16 / 18 / 3 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
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
| 1 | `31.62277660168379` | 41 / 41 / 4,456 | 41 / 41 / 4,226 | 20 / 20 / 1,816 | 19 / 19 / 1,270 | 19 / 19 / 1,741 | 34 / 34 / 3,242 | 18 / 18 / 3,214 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `63.26136064079654` | 40 / 40 / 4,241 | 40 / 40 / 4,014 | 21 / 21 / 1,576 | 19 / 19 / 1,058 | 19 / 19 / 1,533 | 33 / 33 / 3,126 | 18 / 18 / 3,002 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `158.2718785032213` | 40 / 40 / 4,112 | 40 / 40 / 3,887 | 21 / 21 / 1,426 | 19 / 19 / 931 | 19 / 19 / 1,407 | 33 / 33 / 3,031 | 18 / 18 / 2,875 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `316.9381559123806` | 40 / 40 / 4,069 | 40 / 40 / 3,845 | 21 / 21 / 1,378 | 19 / 19 / 889 | 19 / 19 / 1,363 | 33 / 33 / 2,993 | 18 / 18 / 2,833 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `635.4500029402082` | 40 / 40 / 4,048 | 40 / 40 / 3,824 | 21 / 21 / 1,353 | 19 / 19 / 868 | 19 / 19 / 1,342 | 33 / 33 / 2,972 | 18 / 18 / 2,812 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `1600.350881438697` | 40 / 40 / 3,973 | 40 / 40 / 3,720 | 21 / 21 / 1,341 | 19 / 19 / 855 | 19 / 19 / 1,330 | 32 / 32 / 2,960 | 18 / 18 / 2,810 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `3239.292264514382` | 40 / 40 / 3,941 | 40 / 40 / 3,674 | 21 / 21 / 1,338 | 19 / 19 / 851 | 19 / 19 / 1,326 | 32 / 32 / 2,955 | 17 / 17 / 2,813 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `12536.2620049473` | 40 / 40 / 3,917 | 40 / 40 / 3,640 | 21 / 21 / 1,336 | 19 / 19 / 848 | 19 / 19 / 1,323 | 31 / 31 / 2,951 | 18 / 18 / 2,771 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `38540.07865481035` | 40 / 40 / 3,913 | 40 / 40 / 3,632 | 21 / 21 / 1,335 | 19 / 19 / 847 | 19 / 19 / 1,333 | 31 / 31 / 2,950 | 18 / 18 / 2,787 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `748008.0076158747` | 40 / 40 / 4,000 | 40 / 40 / 3,722 | 21 / 21 / 1,347 | 20 / 20 / 847 | 20 / 20 / 1,342 | 30 / 30 / 2,949 | 18 / 18 / 2,710 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

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
| 1 | `1.5` | 38 / 38 / 10,137 | 38 / 38 / 10,139 | 19 / 19 / 10,892 | exact / exact / 1,441 | 16 / 16 / 10,093 | 33 / 33 / 23,587 | 17 / 17 / 2,617 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `1.5` | 38 / 38 / 9,965 | 38 / 38 / 9,970 | 18 / 18 / 10,698 | exact / exact / 1,272 | 16 / 16 / 9,902 | 33 / 33 / 23,376 | 17 / 17 / 2,448 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `1.5` | 38 / 38 / 9,861 | 38 / 38 / 9,868 | 18 / 18 / 10,578 | exact / exact / 1,170 | 16 / 16 / 9,772 | 32 / 32 / 23,252 | 17 / 17 / 2,346 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `1.5` | 38 / 38 / 9,827 | 38 / 38 / 9,834 | 18 / 18 / 10,538 | exact / exact / 1,136 | 15 / 15 / 9,794 | 32 / 32 / 23,224 | 16 / 16 / 2,312 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `1.5` | 38 / 38 / 9,810 | 38 / 38 / 9,817 | 17 / 17 / 10,522 | exact / exact / 1,119 | 15 / 15 / 9,801 | 32 / 32 / 23,211 | 16 / 16 / 2,295 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `1.5` | 38 / 38 / 9,800 | 38 / 38 / 9,807 | 17 / 17 / 10,507 | exact / exact / 1,109 | 15 / 15 / 9,789 | 31 / 31 / 23,192 | 16 / 16 / 2,285 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `1.5` | 38 / 38 / 9,797 | 38 / 38 / 9,804 | 17 / 17 / 10,502 | exact / exact / 1,106 | 14 / 14 / 9,773 | 31 / 31 / 23,189 | 15 / 15 / 2,282 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `1.5` | 38 / 38 / 9,796 | 38 / 38 / 9,801 | 16 / 16 / 10,488 | exact / exact / 1,103 | 14 / 14 / 9,778 | 31 / 31 / 23,181 | 15 / 15 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `1.5` | 38 / 38 / 9,801 | 38 / 38 / 9,801 | 16 / 16 / 10,495 | exact / exact / 1,103 | 13 / 13 / 9,761 | 30 / 30 / 23,187 | 14 / 14 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `1.5` | 38 / 38 / 9,871 | 38 / 38 / 9,801 | 15 / 15 / 10,500 | exact / exact / 1,103 | 12 / 12 / 9,758 | 29 / 29 / 23,224 | 13 / 13 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

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
| 1 | `299200.6479903559` | 39 / exact / 2,520 | 39 / exact / 1,366 | 20 / exact / 1,434 | 19 / exact / 1,159 | 19 / exact / 1,519 | 33 / 33 / 4,734 | 19 / exact / 1,430 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `298401.1864804365` | 38 / 44 / 2,130 | 38 / 44 / 966 | 19 / 25 / 966 | 19 / 23 / 776 | 19 / 23 / 1,136 | 33 / 33 / 3,618 | 19 / 23 / 1,047 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `296002.1447990159` | 38 / 43 / 1,896 | 38 / 43 / 726 | 19 / 24 / 686 | 19 / 23 / 547 | 19 / 23 / 907 | 32 / 32 / 2,949 | 19 / 23 / 818 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `292001.5505907346` | 38 / 43 / 1,818 | 38 / 43 / 646 | 19 / 24 / 592 | 18 / 22 / 470 | 18 / 22 / 830 | 32 / 32 / 2,726 | 18 / 22 / 741 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `283992.1376448092` | 37 / 42 / 1,779 | 37 / 42 / 606 | 18 / 23 / 545 | 18 / 22 / 432 | 18 / 22 / 792 | 32 / 32 / 2,614 | 18 / 22 / 703 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `259897.9672060033` | 37 / 42 / 1,755 | 37 / 42 / 582 | 18 / 23 / 517 | 18 / 22 / 409 | 18 / 22 / 769 | 31 / 31 / 2,547 | 18 / 22 / 680 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `219520.3390882176` | 37 / 42 / 1,748 | 37 / 42 / 574 | 17 / 22 / 508 | 17 / 21 / 401 | 17 / 21 / 761 | 31 / 31 / 2,525 | 17 / 21 / 672 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `840.3327859747961` | 34 / 39 / 1,742 | 34 / 39 / 568 | 15 / 19 / 501 | 15 / 18 / 396 | 15 / 18 / 756 | 28 / 28 / 2,508 | 15 / 18 / 667 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `-556627.3884008416` | 36 / 41 / 1,742 | 36 / 41 / 566 | 17 / 22 / 499 | 17 / 21 / 394 | 17 / 21 / 761 | 31 / 31 / 2,203 | 17 / 21 / 734 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `-16823263.35321035` | 35 / 41 / 1,759 | 35 / 41 / 566 | 16 / 22 / 499 | 16 / 21 / 394 | 16 / 21 / 764 | 29 / 29 / 2,044 | 16 / 21 / 769 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

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
| 1 | `1.5` | 38 / 38 / 12,857 | 38 / 38 / 11,986 | 19 / 19 / 12,147 | exact / exact / 2,592 | 16 / 16 / 12,078 | 33 / 33 / 28,434 | 17 / 17 / 4,370 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `1.414213562373095` | 38 / 38 / 9,526 | 38 / 38 / 8,955 | 18 / 18 / 10,323 | 17 / 17 / 2,052 | 16 / 16 / 10,393 | 33 / 33 / 25,251 | 17 / 17 / 3,370 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `1.284735157123439` | 38 / 38 / 7,402 | 38 / 38 / 6,977 | 19 / 19 / 8,890 | 17 / 17 / 1,728 | 16 / 16 / 9,076 | 33 / 33 / 22,620 | 17 / 17 / 2,776 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `1.196231198851315` | 38 / 38 / 6,658 | 38 / 38 / 6,271 | 18 / 18 / 8,504 | 17 / 17 / 1,620 | 16 / 16 / 8,695 | 33 / 33 / 21,929 | 17 / 17 / 2,543 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `1.127378204157833` | 38 / 38 / 6,293 | 38 / 38 / 5,928 | 18 / 18 / 8,309 | 17 / 17 / 1,566 | 16 / 16 / 8,547 | 33 / 33 / 21,662 | 17 / 17 / 2,330 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `1.067331844248559` | 38 / 38 / 6,025 | 38 / 38 / 5,659 | 18 / 18 / 8,185 | 17 / 17 / 1,534 | 16 / 16 / 8,384 | 33 / 33 / 21,586 | 17 / 17 / 2,202 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `1.04010144984871` | 39 / 39 / 5,891 | 39 / 39 / 5,512 | 18 / 18 / 8,148 | 17 / 17 / 1,523 | 16 / 16 / 8,326 | 33 / 33 / 21,646 | 17 / 17 / 2,159 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `1.01438248702624` | 38 / 38 / 5,694 | 38 / 38 / 5,278 | 18 / 18 / 8,118 | 17 / 17 / 1,515 | 16 / 16 / 8,266 | 33 / 33 / 21,838 | 17 / 17 / 2,128 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `1.006235969300459` | 39 / 39 / 5,621 | 39 / 39 / 5,183 | 18 / 18 / 8,111 | 17 / 17 / 1,514 | 16 / 16 / 8,249 | 33 / 33 / 22,019 | 17 / 17 / 2,121 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `1.00085210215008` | 38 / 38 / 5,650 | 38 / 38 / 5,133 | 18 / 18 / 8,108 | 17 / 17 / 1,513 | 16 / 16 / 8,196 | 33 / 33 / 22,499 | 17 / 17 / 2,117 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

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
| 1 | `0.2474873734152916` | 37 / 37 / 14,510 | 37 / 37 / 8,487 | 18 / 18 / 11,765 | 17 / 17 / 3,862 | 17 / 17 / 7,005 | 34 / 34 / 13,202 | 17 / 17 / 7,754 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `0.4956818182587876` | 37 / 37 / 13,283 | 37 / 37 / 9,086 | 17 / 17 / 10,636 | 18 / 18 / 2,953 | 16 / 16 / 8,442 | 32 / 32 / 19,674 | 17 / 17 / 6,424 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `1.244506874463792` | 37 / 37 / 12,547 | 37 / 37 / 9,445 | 17 / 17 / 9,959 | 17 / 17 / 2,408 | 15 / 15 / 9,436 | 32 / 32 / 23,404 | 16 / 16 / 5,626 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `2.506683467804941` | 36 / 37 / 12,302 | 36 / 37 / 9,565 | 17 / 17 / 9,733 | 17 / 17 / 2,226 | 15 / 15 / 9,738 | 31 / 31 / 24,536 | 16 / 16 / 5,360 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `5.084010514032979` | 36 / 37 / 12,179 | 36 / 37 / 9,625 | 17 / 17 / 9,620 | 17 / 17 / 2,135 | 15 / 15 / 9,909 | 31 / 31 / 25,031 | 16 / 16 / 5,227 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `13.23914876467473` | 36 / 37 / 12,107 | 36 / 37 / 9,661 | 17 / 17 / 9,553 | 17 / 17 / 2,081 | 15 / 15 / 10,056 | 31 / 31 / 25,226 | 16 / 16 / 5,147 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `28.23736439326609` | 36 / 37 / 12,156 | 36 / 37 / 9,762 | 17 / 17 / 9,530 | 17 / 17 / 2,063 | 15 / 15 / 10,102 | 30 / 30 / 25,211 | 16 / 16 / 5,120 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `136.7454508837998` | 36 / 37 / 12,276 | 36 / 37 / 9,929 | 17 / 17 / 9,514 | 17 / 17 / 2,049 | 15 / 15 / 10,139 | 30 / 30 / 25,051 | 16 / 16 / 5,101 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `589.4747739528645` | 36 / 37 / 12,414 | 36 / 37 / 10,073 | 17 / 18 / 9,510 | 18 / 18 / 2,046 | 15 / 15 / 10,175 | 30 / 30 / 24,847 | 17 / 17 / 5,096 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `29787.55928753143` | 36 / 39 / 13,116 | 36 / 39 / 10,415 | 18 / 19 / 9,508 | 17 / 17 / 2,045 | 16 / 16 / 10,227 | 30 / 30 / 24,432 | 17 / 17 / 5,343 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

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
| 1 | `1.0001` | 39 / exact / 2,613 | 39 / exact / 1,459 | 20 / exact / 1,491 | exact / exact / 1,246 | exact / exact / 1,606 | 35 / 35 / 5,709 | exact / exact / 1,517 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 2 | `0.99999999` | 39 / 39 / 2,153 | 39 / 39 / 974 | 19 / 19 / 943 | exact / exact / 797 | exact / exact / 1,157 | 33 / 33 / 3,419 | exact / exact / 1,068 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 5 | `1.000099979998` | 38 / 38 / 1,878 | 38 / 38 / 683 | 18 / 18 / 615 | 20 / 20 / 528 | 20 / 20 / 888 | 33 / 33 / 2,029 | 20 / 20 / 799 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10 | `0.999999950000001` | 37 / 37 / 1,786 | 37 / 37 / 586 | 18 / 18 / 505 | 17 / 17 / 438 | 17 / 17 / 798 | 32 / 32 / 1,571 | 17 / 17 / 709 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 20 | `0.9999999000000045` | 37 / 37 / 1,740 | 37 / 37 / 537 | 18 / 18 / 451 | 17 / 17 / 393 | 17 / 17 / 753 | 32 / 32 / 1,340 | 17 / 17 / 664 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 50 | `0.99999975000003` | 37 / 37 / 1,712 | 37 / 37 / 508 | 17 / 17 / 418 | 16 / 16 / 366 | 16 / 16 / 726 | 32 / 32 / 1,201 | 16 / 16 / 637 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 100 | `0.9999995000001225` | 36 / 36 / 1,703 | 36 / 36 / 499 | 17 / 17 / 407 | 16 / 16 / 357 | 16 / 16 / 717 | 31 / 31 / 1,155 | 16 / 16 / 628 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 365 | `1.000098179819647` | 36 / 36 / 1,697 | 36 / 36 / 492 | 16 / 16 / 399 | 15 / 15 / 350 | 15 / 15 / 710 | 31 / 31 / 1,122 | 15 / 15 / 621 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 1000 | `0.999995000012475` | 35 / 35 / 1,697 | 35 / 35 / 490 | 16 / 16 / 397 | 15 / 15 / 349 | 15 / 15 / 709 | 30 / 30 / 1,114 | 15 / 15 / 620 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |
| 10000 | `0.9999500012497292` | 34 / 34 / 1,714 | 34 / 34 / 489 | 15 / 15 / 396 | 14 / 14 / 348 | 14 / 14 / 708 | 29 / 29 / 1,109 | 14 / 14 / 619 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` |

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
| 1 | `11000.0` | 38 / exact / 2,368 | 38 / exact / 1,183 | 19 / exact / 1,189 | exact / exact / 1,007 | exact / exact / 1,367 | 33 / 33 / 3,196 | exact / exact / 1,278 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 610 |
| 2 | `12100.0` | 38 / exact / 1,975 | 38 / exact / 780 | 19 / 39 / 737 | exact / exact / 622 | exact / exact / 982 | 33 / 33 / 2,107 | exact / exact / 893 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 420 |
| 5 | `16105.1` | 38 / 42 / 1,740 | 38 / 42 / 539 | 18 / 23 / 465 | exact / exact / 391 | exact / exact / 751 | 33 / 33 / 1,454 | exact / exact / 662 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 197 |
| 10 | `25937.424601` | 37 / 42 / 1,661 | 37 / 42 / 458 | 18 / 23 / 375 | exact / exact / 314 | exact / exact / 674 | 32 / 32 / 1,232 | exact / exact / 585 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 121 |
| 20 | `67274.999493256` | 37 / 42 / 1,622 | 37 / 42 / 418 | 18 / 22 / 330 | exact / exact / 275 | exact / exact / 635 | 32 / 32 / 1,121 | exact / exact / 546 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 68 |
| 50 | `1173908.528796953` | 37 / 41 / 1,598 | 37 / 41 / 394 | 17 / 22 / 303 | 22 / 22 / 252 | 22 / 22 / 612 | 32 / 32 / 1,056 | 22 / 22 / 523 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 29 / 29 / 31 |
| 100 | `137806123.3982227` | 36 / 41 / 1,591 | 36 / 41 / 386 | 17 / 22 / 294 | 22 / 22 / 244 | 22 / 22 / 604 | 31 / 31 / 1,034 | 22 / 22 / 515 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 29 / 29 / 17 |
| 365 | `1.283305580313353e+19` | 36 / 41 / 1,585 | 36 / 41 / 380 | reverts `0x00000000` | 22 / 22 / 239 | 22 / 22 / 599 | 31 / 31 / 1,019 | 22 / 22 / 510 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 28 / 28 / 6 |
| 1000 | `2.469932918005826e+45` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | 22 / 22 / 606 | 30 / 30 / 1,015 | reverts `0x4e487b71` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x49f7642b` |
| 10000 | `8.449900251200348e+417` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | reverts `0x120b5b43` | 29 / 29 / 1,013 | reverts `0x4e487b71` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x49f7642b` |

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
| 1 | `10001.36995684313` | 33 / 39 / 9,319 | 33 / 39 / 7,312 | 14 / 14 / 11,907 | 13 / 13 / 2,533 | 12 / 12 / 10,868 | 28 / 28 / 31,514 | 13 / 17 / 3,476 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 22 / 22 / 3,471 |
| 2 | `10002.74010136444` | 33 / 38 / 4,790 | 33 / 38 / 3,792 | 13 / 14 / 5,960 | 12 / 12 / 1,266 | 11 / 11 / 5,441 | 28 / 28 / 15,759 | 13 / 17 / 1,738 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 22 / 22 / 1,809 |
| 5 | `10006.85166125453` | 33 / 39 / 2,085 | 33 / 39 / 1,687 | 13 / 13 / 2,370 | 12 / 12 / 506 | 11 / 11 / 2,156 | 28 / 28 / 6,281 | 13 / 18 / 695 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 803 |
| 10 | `10013.70801703526` | 32 / 39 / 1,069 | 32 / 39 / 871 | 13 / 13 / 1,185 | 12 / 12 / 253 | 11 / 11 / 1,079 | 27 / 27 / 3,141 | 12 / 18 / 347 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 416 |
| 20 | `10027.43482504363` | 32 / 38 / 547 | 32 / 38 / 449 | 12 / 13 / 593 | 11 / 11 / 126 | 10 / 10 / 550 | 27 / 27 / 1,570 | 12 / 18 / 173 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 215 |
| 50 | `10068.72825267094` | 32 / 39 / 229 | 32 / 39 / 190 | 12 / 12 / 238 | 11 / 11 / 50 | 10 / 10 / 221 | 27 / 27 / 632 | 12 / 18 / 69 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 20 / 20 / 92 |
| 100 | `10137.92886261339` | 31 / 39 / 117 | 31 / 39 / 98 | 12 / 12 / 119 | 11 / 11 / 25 | 10 / 10 / 110 | 26 / 26 / 316 | 11 / 18 / 34 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 20 / 20 / 47 |
| 365 | `10512.71096334355` | 31 / 39 / 33 | 31 / 39 / 28 | 11 / 11 / 32 | 10 / 10 / 6 | 9 / 9 / 30 | 26 / 26 / 86 | 11 / 18 / 9 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 19 / 20 / 13 |
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
| 1 | `10001.36995684422` | 38 / 38 / 10,351 | 38 / 38 / 7,374 | 19 / 19 / 5,080 | 18 / 18 / 2,074 | 18 / 18 / 5,126 | 33 / 33 / 11,238 | 18 / 18 / 3,465 | 16 / 16 / 1,608 | 13 / 13 / 1,442 | reverts `0x7bb9ae15` |
| 2 | `10002.74010136661` | 38 / 38 / 5,175 | 38 / 38 / 3,687 | 19 / 19 / 2,540 | 18 / 18 / 1,037 | 17 / 17 / 2,570 | 33 / 33 / 5,621 | 18 / 18 / 1,732 | 15 / 15 / 804 | 13 / 13 / 721 | reverts `0x7bb9ae15` |
| 5 | `10006.85166125997` | 39 / 39 / 2,070 | 39 / 39 / 1,474 | 19 / 19 / 1,010 | 18 / 18 / 414 | 17 / 17 / 1,028 | 34 / 34 / 2,237 | 18 / 18 / 693 | 14 / 14 / 321 | 13 / 13 / 288 | reverts `0x7bb9ae15` |
| 10 | `10013.70801704614` | 38 / 38 / 1,035 | 38 / 38 / 737 | 18 / 18 / 506 | 18 / 18 / 207 | 17 / 17 / 516 | 33 / 33 / 1,119 | 18 / 18 / 346 | 12 / 12 / 160 | 12 / 12 / 144 | reverts `0x7bb9ae15` |
| 20 | `10027.43482506541` | 38 / 38 / 517 | 38 / 38 / 368 | 19 / 19 / 253 | 18 / 18 / 103 | 18 / 18 / 268 | 34 / 34 / 559 | 18 / 18 / 173 | 11 / 11 / 80 | 11 / 11 / 72 | reverts `0x7bb9ae15` |
| 50 | `10068.72825272561` | 38 / 38 / 207 | 38 / 38 / 147 | 18 / 18 / 103 | 18 / 18 / 41 | 17 / 17 / 108 | 33 / 33 / 223 | 18 / 18 / 69 | 10 / 10 / 32 | 10 / 10 / 28 | reverts `0x7bb9ae15` |
| 100 | `10137.92886272349` | 38 / 38 / 103 | 38 / 38 / 73 | 19 / 19 / 50 | 18 / 18 / 20 | 17 / 17 / 54 | 34 / 34 / 111 | 18 / 18 / 34 | 8 / 8 / 16 | 8 / 8 / 14 | reverts `0x7bb9ae15` |
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

## Methodology

**truth.** For every scenario, input and N the same loop is run in exact real arithmetic with mpmath at 200 decimal digits (scripts/ladder/ladder.py), from the exact rational parameters in scenarios.json. Closed forms are used where the loop has one (compounding, the cumulative product, the geometric mean, the round trip, per-second and continuous accrual); the bonding curve, the amortising loan and the Black-Scholes chain are stepped.

**rounding.** Each library receives the parameters floored into its own representation (2^-128, 2^-64, 10^-18 or 10^-27 units, or the nearest binary128 value for ABDKMathQuad; scripts/ladder/inputs.json). truthFormat is the exact loop started from those floored parameters, so digitsFormat measures the library's arithmetic alone, while digits measures what a protocol sees: the format's rounding of the inputs plus the arithmetic.

**digits.** digits = floor(-log10 |v - t| / |t|), the number of correct leading significant digits by relative error, capped at 60, which is reported as exact. It is not a string comparison: a value can be correct to 36 digits while its 37th printed digit happens to agree with the truth, or while a carry makes the printed prefix differ earlier.

**agree.** agree is the count of leading significant digits of the printed value (42 significant digits) that are literally equal to the printed truth. The demo page colours the rest of the value with it. It is a reading aid, not a measurement: a carry across 0.999… / 1.000… gives 0.

**gas.** gasTotal is measured inside the adapter around the scenario function (the parameter reads and the loop), after the runner has warmed the adapter and the FP127 object, so the call into the adapter and the ABI decoding are excluded. The FP127 (deployed) form includes one staticcall per op; FP127Lib and the other libraries are internal calls. Aave, Morpho and Maker answer only the accrual scenarios their models describe and report Unsupported elsewhere, which the tables show as a revert. gasPerStep = gasTotal / N. Reverted cells carry no gas.

**live.** LadderRunner.run(scenario, form, n, p) on Sepolia executes any cell with one eth_call and returns (ok, raw, reason, gasPerStep, gasTotal). The demo's verify button sends the cell's floored parameters p and compares the returned raw word with the committed one bit for bit (or the revert selector for a reverted cell). liveMaxN is the largest N per form the public RPC completed within its gas limit, measured by scripts/ladder/livecap.py.

**reproduce.** make ladder regenerates ladder.json and ladder.md from the Foundry harness (test/ladder/Ladder.t.sol) and this script; make ladder-check fails CI when the committed dataset differs. Versions of every library and of forge are recorded in the dataset.

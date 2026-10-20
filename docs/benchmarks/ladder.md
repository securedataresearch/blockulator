# Terminal precision ladder

Generated 2026-10-20 by `make ladder`. Versions: fp127 091c5aa, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, forge forge Version: 1.7.1.

Each scenario is run for several inputs; the first table is the reference input in full (`digits / digitsFormat / gas per step`, where digits is against the exact truth and digitsFormat against the truth from the parameters as the library received them), the second is the summary over all inputs (`median (min–max)` digits, capped at 40). Full values, both truths, signed errors and raw words are in ladder.json; the method is in the Methodology section at the end.

## compound: Daily compound interest

Step: `b = b * (1 + r)`. Result: balance after N days.

Per-block or per-day accrual in every lending protocol: one mul per step, N steps.

Inputs: **reference** principal = 10000, rate = 0.1/365 ($10,000 at 10% APR, the headline cell); **tiny-low** principal = 1, rate = 0.01/365 (one unit at 1%: the integer part is small, the fraction carries everything); **tiny-high** principal = 1, rate = 0.5/365 (one unit at 50%); **mid-1pct** principal = 10000, rate = 0.01/365 (a slow rate: the per-step factor is close to 1); **mid-5pct** principal = 10000, rate = 0.05/365 (a typical lending rate); **mid-50pct** principal = 10000, rate = 0.5/365 (a high rate: the balance grows 150x by N = 10,000); **large** principal = 1000000, rate = 0.1/365 (a million-unit position); **huge** principal = 100000000, rate = 0.1/365 (a hundred-million-unit pool); **huge-high** principal = 100000000, rate = 0.5/365 (the largest balance the ladder reaches, near 10^14); **fraction** principal = 0.001, rate = 0.1/365 (a sub-unit balance: leading zeros in WAD)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10002.7397260274` | 38 / exact / 2,236 | 38 / exact / 900 | 19 / exact / 934 | 19 / exact / 744 | 19 / exact / 1,104 | 33 / 33 / 2,933 | 19 / exact / 1,015 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 27 / exact / 610 | 71 / 71 / 2,875 |
| 2 | `10005.48020266467` | 38 / 42 / 1,973 | 38 / 42 / 635 | 19 / 23 / 610 | 19 / 22 / 488 | 19 / 22 / 848 | 33 / 33 / 1,974 | 19 / 22 / 759 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 27 / 420 | 71 / 71 / 2,054 |
| 5 | `10013.70613829244` | 38 / 42 / 1,815 | 38 / 42 / 476 | 19 / 23 / 415 | 18 / 21 / 335 | 18 / 21 / 695 | 33 / 33 / 1,398 | 18 / 21 / 606 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 197 | 70 / 70 / 1,561 |
| 10 | `10027.43106240757` | 37 / 41 / 1,762 | 37 / 41 / 423 | 18 / 22 / 350 | 18 / 21 / 284 | 18 / 21 / 644 | 32 / 32 / 1,206 | 18 / 21 / 555 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 121 | 70 / 70 / 1,397 |
| 20 | `10054.93737113361` | 37 / 41 / 1,736 | 37 / 41 / 396 | 18 / 22 / 318 | 18 / 21 / 258 | 18 / 21 / 618 | 32 / 32 / 1,110 | 18 / 21 / 529 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 68 | 70 / 70 / 1,315 |
| 50 | `10137.90984214166` | 37 / 41 / 1,720 | 37 / 41 / 380 | 18 / 21 / 298 | 17 / 20 / 243 | 17 / 20 / 603 | 32 / 32 / 1,053 | 17 / 20 / 514 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 25 / 26 / 31 | 69 / 69 / 1,265 |
| 100 | `10277.72159673926` | 36 / 40 / 1,715 | 36 / 40 / 375 | 17 / 21 / 292 | 17 / 20 / 238 | 17 / 20 / 598 | 31 / 31 / 1,034 | 17 / 20 / 509 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 25 / 25 / 17 | 69 / 69 / 1,249 |
| 365 | `11051.55781616264` | 36 / 40 / 1,712 | 36 / 40 / 371 | 17 / 21 / 287 | 16 / 19 / 234 | 16 / 19 / 594 | 31 / 31 / 1,020 | 16 / 19 / 505 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 24 / 25 / 6 | 68 / 68 / 1,237 |
| 1000 | `13151.29420081218` | 35 / 39 / 1,712 | 35 / 39 / 370 | 16 / 20 / 286 | 16 / 19 / 233 | 16 / 19 / 593 | 30 / 30 / 1,016 | 16 / 19 / 504 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 24 / 24 / 2 | 68 / 68 / 1,234 |
| 10000 | `154769.3406914411` | 34 / 39 / 1,729 | 34 / 39 / 370 | 15 / 20 / 286 | 15 / 18 / 233 | 15 / 18 / 593 | 29 / 29 / 1,015 | 15 / 18 / 504 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 23 / 23 / 0 | 67 / 67 / 1,233 |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (35–39) | 38 (35–39) | 19 (16–20) | 18 (15–19) | 18 (15–19) | 33 (33–35) | 18 (15–19) | — (10 revert) | — (10 revert) | 27 (24–28) | 71 (71–71) |
| 2 | 38 (35–38) | 38 (35–38) | 19 (15–19) | 18 (14–19) | 18 (14–19) | 33 (33–34) | 18 (14–19) | — (10 revert) | — (10 revert) | 26 (25–27) | 71 (71–71) |
| 5 | 38 (35–38) | 38 (35–38) | 18.5 (15–19) | 18 (14–19) | 18 (14–19) | 33 (32–33) | 18 (14–19) | — (10 revert) | — (10 revert) | 26 (24–27) | 70 (70–71) |
| 10 | 37 (34–38) | 37 (34–38) | 18 (15–19) | 17 (14–18) | 17 (14–18) | 32 (32–33) | 17 (14–18) | — (10 revert) | — (10 revert) | 26 (24–26) | 70 (70–71) |
| 20 | 37 (34–37) | 37 (34–37) | 18 (15–18) | 17 (13–18) | 17 (13–18) | 32 (32–32) | 17 (13–18) | — (10 revert) | — (10 revert) | 26 (24–26) | 70 (70–70) |
| 50 | 37 (34–37) | 37 (34–37) | 17.5 (14–18) | 17 (13–18) | 17 (13–18) | 32 (31–32) | 17 (13–18) | — (10 revert) | — (10 revert) | 25 (24–26) | 69 (69–70) |
| 100 | 36 (33–37) | 36 (33–37) | 17 (14–18) | 16 (13–17) | 16 (13–17) | 31 (31–32) | 16 (13–17) | — (10 revert) | — (10 revert) | 25 (24–25) | 69 (69–69) |
| 365 | 36 (33–36) | 36 (33–36) | 16.5 (14–17) | 16 (12–17) | 16 (12–17) | 31 (31–31) | 16 (12–17) | — (10 revert) | — (10 revert) | 24 (24–25) | 68 (68–69) |
| 1000 | 35 (32–36) | 35 (32–36) | 16 (13–17) | 15 (12–16) | 15 (12–16) | 30 (30–31) | 15 (12–16) | — (10 revert) | — (10 revert) | 24 (24–24) | 68 (68–68) |
| 10000 | 34 (32–35) | 34 (32–35) | 15 (13–16) | 14 (11–15) | 14 (11–15) | 29 (29–30) | 14 (11–15) | — (10 revert) | — (10 revert) | 23 (23–23) | 67 (67–67) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 80 (35–80) | 80 (35–80) | 80 (16–80) | 80 (15–80) | 80 (15–80) | 33 (33–35) | 80 (15–80) | — (10 revert) | — (10 revert) | 80 (24–80) | 71 (71–71) |
| 2 | 42 (35–47) | 42 (35–47) | 23 (16–27) | 22 (14–26) | 22 (14–26) | 33 (33–34) | 22 (14–26) | — (10 revert) | — (10 revert) | 27 (25–27) | 71 (71–71) |
| 5 | 42 (35–46) | 42 (35–46) | 22.5 (15–27) | 21 (14–26) | 21 (14–26) | 33 (32–33) | 21 (14–26) | — (10 revert) | — (10 revert) | 27 (24–27) | 70 (70–71) |
| 10 | 41 (34–45) | 41 (34–45) | 22 (15–26) | 21 (14–25) | 21 (14–25) | 32 (32–33) | 21 (14–25) | — (10 revert) | — (10 revert) | 26 (24–26) | 70 (70–71) |
| 20 | 41 (34–45) | 41 (34–45) | 22 (15–26) | 21 (13–25) | 21 (13–25) | 32 (32–32) | 21 (13–25) | — (10 revert) | — (10 revert) | 26 (24–26) | 70 (70–70) |
| 50 | 41 (34–45) | 41 (34–45) | 21 (14–25) | 20 (13–24) | 20 (13–24) | 32 (31–32) | 20 (13–24) | — (10 revert) | — (10 revert) | 26 (24–26) | 69 (69–70) |
| 100 | 40 (33–44) | 40 (33–44) | 21 (14–25) | 20 (13–24) | 20 (13–24) | 31 (31–32) | 20 (13–24) | — (10 revert) | — (10 revert) | 25 (24–26) | 69 (69–69) |
| 365 | 40 (33–44) | 40 (33–44) | 21 (14–25) | 19 (12–23) | 19 (12–23) | 31 (31–31) | 19 (12–23) | — (10 revert) | — (10 revert) | 25 (24–25) | 68 (68–69) |
| 1000 | 39 (32–44) | 39 (32–44) | 20 (13–24) | 19 (12–23) | 19 (12–23) | 30 (30–31) | 19 (12–23) | — (10 revert) | — (10 revert) | 24 (24–25) | 68 (68–68) |
| 10000 | 39 (32–43) | 39 (32–43) | 19.5 (13–24) | 18 (11–23) | 18 (11–23) | 29 (29–30) | 18 (11–23) | — (10 revert) | — (10 revert) | 23 (23–24) | 67 (67–67) |

## compound-pow: Compound interest in one pow

Step: `b0 * (1 + r)^N`. Result: the same balance, computed with one real-exponent pow.

The clever way to skip the loop. pow is exp(N ln(1+r)) in every library, so its precision is bounded by ln and exp, and the error grows with N without any loop.

Inputs: **reference** principal = 10000, rate = 0.1/365 ($10,000 at 10% APR, the headline cell); **tiny-low** principal = 1, rate = 0.01/365 (one unit at 1%: the integer part is small, the fraction carries everything); **tiny-high** principal = 1, rate = 0.5/365 (one unit at 50%); **mid-1pct** principal = 10000, rate = 0.01/365 (a slow rate: the per-step factor is close to 1); **mid-5pct** principal = 10000, rate = 0.05/365 (a typical lending rate); **mid-50pct** principal = 10000, rate = 0.5/365 (a high rate: the balance grows 150x by N = 10,000); **large** principal = 1000000, rate = 0.1/365 (a million-unit position); **huge** principal = 100000000, rate = 0.1/365 (a hundred-million-unit pool); **huge-high** principal = 100000000, rate = 0.5/365 (the largest balance the ladder reaches, near 10^14); **fraction** principal = 0.001, rate = 0.1/365 (a sub-unit balance: leading zeros in WAD)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10002.7397260274` | 38 / exact / 3,461 | 38 / exact / 1,146 | 19 / 19 / 11,498 | 17 / 18 / 2,153 | 19 / exact / 1,436 | 33 / 33 / 28,822 | 17 / 18 / 3,096 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 4,010 |
| 2 | `10005.48020266467` | 38 / 38 / 1,832 | 38 / 38 / 699 | 18 / 18 / 5,749 | 17 / 18 / 1,076 | 16 / 16 / 5,366 | 33 / 33 / 14,413 | 17 / 18 / 1,548 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,563 |
| 5 | `10013.70613829244` | 38 / 38 / 2,884 | 38 / 38 / 2,869 | 18 / 18 / 2,282 | 17 / 17 / 430 | 16 / 16 / 2,118 | 33 / 33 / 5,728 | 17 / 18 / 619 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 4,050 |
| 10 | `10027.43106240757` | 37 / 39 / 1,420 | 37 / 39 / 1,408 | 18 / 18 / 1,141 | 17 / 17 / 215 | 16 / 16 / 1,060 | 33 / 33 / 2,864 | 18 / 18 / 309 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 2,026 |
| 20 | `10054.93737113361` | 37 / 39 / 737 | 37 / 39 / 735 | 17 / 18 / 570 | 17 / 17 / 107 | 15 / 15 / 530 | 33 / 33 / 1,432 | 17 / 18 / 154 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,012 |
| 50 | `10137.90984214166` | 37 / 38 / 283 | 37 / 38 / 280 | 17 / 17 / 230 | 16 / 16 / 43 | 15 / 15 / 217 | 32 / 32 / 573 | 17 / 18 / 61 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 405 |
| 100 | `10277.72159673926` | 36 / 39 / 141 | 36 / 39 / 140 | 17 / 17 / 115 | 16 / 16 / 21 | 15 / 15 / 109 | 32 / 32 / 286 | 17 / 17 / 30 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 202 |
| 365 | `11051.55781616264` | 36 / 39 / 41 | 36 / 39 / 41 | 16 / 16 / 31 | 15 / 15 / 5 | 14 / 14 / 29 | 31 / 31 / 78 | 16 / 18 / 8 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 55 |
| 1000 | `13151.29420081218` | 35 / 39 / 14 | 35 / 39 / 14 | 16 / 16 / 11 | 15 / 15 / 2 | 14 / 14 / 10 | 31 / 31 / 28 | 16 / 18 / 3 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 20 |
| 10000 | `154769.3406914411` | 34 / 40 / 1 | 34 / 40 / 1 | 15 / 15 / 1 | 14 / 14 / 0 | 13 / 13 / 1 | 30 / 30 / 2 | 15 / 17 / 0 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 67 / 67 / 2 |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (35–39) | 38 (35–39) | 19 (16–19) | 17 (15–17) | 18 (15–19) | 33 (33–33) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) | 71 (71–71) |
| 2 | 38 (35–38) | 38 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) | 33 (33–34) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) | 71 (71–72) |
| 5 | 38 (35–38) | 38 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) | 33 (32–33) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) | 70 (70–71) |
| 10 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) | 33 (32–34) | 17 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 70 (70–70) |
| 20 | 37 (35–37) | 37 (35–37) | 17 (16–18) | 16 (15–17) | 15 (15–15) | 33 (32–33) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) | 70 (70–70) |
| 50 | 37 (35–37) | 37 (35–37) | 17 (16–17) | 16 (15–17) | 15 (15–15) | 32 (32–33) | 17 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) | 69 (69–70) |
| 100 | 36 (35–37) | 36 (35–37) | 17 (16–17) | 16 (15–17) | 15 (14–15) | 32 (31–33) | 16 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) | 69 (69–69) |
| 365 | 36 (35–36) | 36 (35–36) | 16 (16–16) | 15 (15–16) | 14 (14–14) | 31 (31–32) | 16 (15–17) | — (10 revert) | — (10 revert) | — (10 revert) | 68 (68–69) |
| 1000 | 35 (35–36) | 35 (35–36) | 16 (15–16) | 15 (14–16) | 14 (13–14) | 31 (30–32) | 15 (15–16) | — (10 revert) | — (10 revert) | — (10 revert) | 68 (68–68) |
| 10000 | 34 (34–35) | 34 (34–35) | 15 (15–15) | 14 (13–15) | 13 (12–13) | 30 (29–31) | 14.5 (14–15) | — (10 revert) | — (10 revert) | — (10 revert) | 67 (67–67) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 80 (35–80) | 80 (35–80) | 19 (16–19) | 18 (15–18) | 80 (15–80) | 33 (33–33) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 71 (71–71) |
| 2 | 39 (35–39) | 39 (35–39) | 18.5 (16–19) | 17 (15–18) | 16 (15–16) | 33 (33–34) | 17 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 71 (71–72) |
| 5 | 38 (35–39) | 38 (35–39) | 18 (16–19) | 17 (15–17) | 16 (15–16) | 33 (32–33) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 70 (70–71) |
| 10 | 39 (35–40) | 39 (35–40) | 18 (16–18) | 17 (15–18) | 16 (15–16) | 33 (32–34) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 70 (70–70) |
| 20 | 39 (35–39) | 39 (35–39) | 18 (16–18) | 16 (15–17) | 15 (15–15) | 33 (32–33) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 70 (70–70) |
| 50 | 39 (37–39) | 39 (37–39) | 17 (16–18) | 16 (15–17) | 15 (15–15) | 32 (32–33) | 17 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 69 (69–70) |
| 100 | 39 (37–39) | 39 (37–39) | 17 (16–18) | 16 (15–17) | 15 (14–15) | 32 (31–33) | 17 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 69 (69–69) |
| 365 | 39 (35–42) | 39 (35–42) | 16.5 (16–17) | 15 (15–16) | 14 (14–14) | 31 (31–32) | 17.5 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 68 (68–69) |
| 1000 | 39 (36–39) | 39 (36–39) | 16 (16–17) | 15 (14–16) | 14 (13–14) | 31 (30–32) | 18 (15–18) | — (10 revert) | — (10 revert) | — (10 revert) | 68 (68–68) |
| 10000 | 40 (36–45) | 40 (36–45) | 15 (15–16) | 14 (14–15) | 13 (12–13) | 30 (29–31) | 18 (16–18) | — (10 revert) | — (10 revert) | — (10 revert) | 67 (67–67) |

## bonding-sqrt: Square-root bonding curve

Step: `cost += sqrt(s); s += 1`. Result: total cost of N unit buys.

Bonding curves price each token at a root of the supply; the sum of N floors is where the digits go.

Inputs: **reference** supply = 1000, unit = 1 (a thousand tokens out, unit buys); **from-one** supply = 1, unit = 1 (the curve from its first token); **half-units** supply = 1000, unit = 0.5 (buys that are not integers); **deep** supply = 1000000, unit = 1 (a million out: sqrt is large, the sum is huge); **micro** supply = 1, unit = 0.001 (thousandth-unit buys from the start); **very-deep** supply = 1000000000, unit = 1000 (a billion out in thousand-token lots); **small-steps** supply = 10, unit = 0.01 (hundredth-unit buys from ten)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `31.62277660168379` | 41 / 41 / 4,554 | 41 / 41 / 4,198 | 20 / 20 / 1,814 | 19 / 19 / 1,262 | 19 / 19 / 1,753 | 34 / 34 / 3,234 | 18 / 18 / 3,206 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 5,056 |
| 2 | `63.26136064079654` | 40 / 40 / 4,339 | 40 / 40 / 3,986 | 21 / 21 / 1,574 | 19 / 19 / 1,050 | 19 / 19 / 1,545 | 33 / 33 / 3,118 | 18 / 18 / 2,994 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 5,227 |
| 5 | `158.2718785032213` | 40 / 40 / 4,210 | 40 / 40 / 3,859 | 21 / 21 / 1,424 | 19 / 19 / 923 | 19 / 19 / 1,419 | 33 / 33 / 3,023 | 18 / 18 / 2,867 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 5,312 |
| 10 | `316.9381559123806` | 40 / 40 / 4,167 | 40 / 40 / 3,817 | 21 / 21 / 1,376 | 19 / 19 / 881 | 19 / 19 / 1,375 | 33 / 33 / 2,985 | 18 / 18 / 2,825 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 72 / 72 / 5,339 |
| 20 | `635.4500029402082` | 40 / 40 / 4,146 | 40 / 40 / 3,796 | 21 / 21 / 1,351 | 19 / 19 / 860 | 19 / 19 / 1,354 | 33 / 33 / 2,964 | 18 / 18 / 2,804 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 5,352 |
| 50 | `1600.350881438697` | 40 / 40 / 4,087 | 40 / 40 / 3,692 | 21 / 21 / 1,339 | 19 / 19 / 847 | 19 / 19 / 1,342 | 32 / 32 / 2,952 | 18 / 18 / 2,802 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 5,360 |
| 100 | `3239.292264514382` | 40 / 40 / 4,061 | 40 / 40 / 3,646 | 21 / 21 / 1,336 | 19 / 19 / 843 | 19 / 19 / 1,338 | 32 / 32 / 2,947 | 17 / 17 / 2,805 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 5,362 |
| 365 | `12536.2620049473` | 40 / 40 / 4,043 | 40 / 40 / 3,612 | 21 / 21 / 1,334 | 19 / 19 / 840 | 19 / 19 / 1,335 | 31 / 31 / 2,943 | 18 / 18 / 2,763 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 5,364 |
| 1000 | `38540.07865481035` | 40 / 40 / 4,040 | 40 / 40 / 3,604 | 21 / 21 / 1,333 | 19 / 19 / 839 | 19 / 19 / 1,345 | 31 / 31 / 2,942 | 18 / 18 / 2,779 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 5,364 |
| 10000 | `748008.0076158747` | 40 / 40 / 4,113 | 40 / 40 / 3,694 | 21 / 21 / 1,345 | 20 / 20 / 839 | 20 / 20 / 1,354 | 30 / 30 / 2,941 | 18 / 18 / 2,702 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 5,364 |

### All inputs (7): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 43 (39–80) | 43 (39–80) | 23 (20–80) | 22 (18–80) | 22 (18–80) | 34 (33–80) | 18 (17–80) | — (7 revert) | — (7 revert) | — (7 revert) | 72 (71–80) |
| 2 | 40 (38–43) | 40 (38–43) | 20 (19–24) | 19 (18–22) | 19 (18–22) | 34 (33–34) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 71 (71–73) |
| 5 | 40 (38–43) | 40 (38–43) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–34) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 71 (70–72) |
| 10 | 40 (38–43) | 40 (38–43) | 20 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–33) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 71 (70–72) |
| 20 | 40 (38–43) | 40 (38–43) | 21 (18–24) | 19 (18–22) | 19 (18–22) | 33 (33–33) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) | 71 (70–71) |
| 50 | 40 (37–43) | 40 (37–43) | 21 (18–24) | 19 (18–22) | 19 (18–22) | 32 (32–32) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (70–71) |
| 100 | 40 (37–43) | 40 (37–43) | 21 (18–24) | 19 (18–22) | 19 (18–22) | 32 (32–32) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (70–71) |
| 365 | 40 (36–43) | 40 (36–43) | 21 (17–24) | 19 (18–22) | 19 (18–22) | 31 (31–31) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (69–71) |
| 1000 | 40 (36–43) | 40 (36–43) | 21 (17–24) | 19 (18–22) | 19 (18–22) | 31 (31–31) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (69–70) |
| 10000 | 40 (36–43) | 40 (36–43) | 21 (16–24) | 20 (18–22) | 20 (18–22) | 30 (30–30) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (68–70) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 43 (39–80) | 43 (39–80) | 23 (20–80) | 22 (18–80) | 22 (18–80) | 34 (33–80) | 18 (17–80) | — (7 revert) | — (7 revert) | — (7 revert) | 72 (71–80) |
| 2 | 40 (38–43) | 40 (38–43) | 20 (19–24) | 19 (18–22) | 19 (18–22) | 34 (33–34) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 71 (71–73) |
| 5 | 40 (39–43) | 40 (39–43) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–34) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 71 (70–72) |
| 10 | 40 (38–43) | 40 (38–43) | 20 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–33) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 71 (70–72) |
| 20 | 40 (38–43) | 40 (38–43) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 33 (33–33) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) | 71 (70–71) |
| 50 | 40 (38–43) | 40 (38–43) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 32 (32–32) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (70–71) |
| 100 | 40 (38–43) | 40 (38–43) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 32 (32–32) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (70–71) |
| 365 | 40 (38–43) | 40 (38–43) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 31 (31–31) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (69–71) |
| 1000 | 40 (38–43) | 40 (38–43) | 21 (19–24) | 19 (18–22) | 19 (18–22) | 31 (31–31) | 18 (17–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (69–70) |
| 10000 | 40 (39–43) | 40 (39–43) | 21 (19–24) | 20 (18–22) | 20 (18–22) | 30 (30–30) | 18 (18–18) | — (7 revert) | — (7 revert) | — (7 revert) | 70 (68–70) |

## roundtrip: exp(ln(x)) round trip

Step: `x = exp(ln(x))`. Result: x after N round trips; the answer is the input.

Isolates transcendental error. Every step should be the identity; what remains is the library's ln and exp error, compounded.

Inputs: **reference** x0 = 1.5 (1.5 is representable in every format, so a perfect library returns it exactly); **hundredth** x0 = 0.01 (ln is large and negative); **tenth** x0 = 0.1 (a typical price ratio); **near-one-below** x0 = 0.7 (ln is small: cancellation territory); **just-above-one** x0 = 1.0001 (ln is tiny: the log1p regime); **two** x0 = 2 (the simplest non-trivial value); **ten** x0 = 10 (a round decade); **thousand** x0 = 1000 (three decades); **million** x0 = 1000000 (six decades, near ABDK's comfortable range); **awkward** x0 = 123456.789 (a value with no special structure)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `1.5` | 38 / 38 / 10,883 | 38 / 38 / 9,646 | 19 / 19 / 10,892 | exact / exact / 1,441 | 16 / 16 / 10,093 | 33 / 33 / 23,587 | 17 / 17 / 2,617 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 16,139 |
| 2 | `1.5` | 38 / 38 / 10,711 | 38 / 38 / 9,477 | 18 / 18 / 10,698 | exact / exact / 1,272 | 16 / 16 / 9,902 | 33 / 33 / 23,376 | 17 / 17 / 2,448 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,970 |
| 5 | `1.5` | 38 / 38 / 10,607 | 38 / 38 / 9,375 | 18 / 18 / 10,578 | exact / exact / 1,170 | 16 / 16 / 9,772 | 32 / 32 / 23,252 | 17 / 17 / 2,346 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,868 |
| 10 | `1.5` | 38 / 38 / 10,573 | 38 / 38 / 9,341 | 18 / 18 / 10,538 | exact / exact / 1,136 | 15 / 15 / 9,794 | 32 / 32 / 23,224 | 16 / 16 / 2,312 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,834 |
| 20 | `1.5` | 38 / 38 / 10,556 | 38 / 38 / 9,324 | 17 / 17 / 10,522 | exact / exact / 1,119 | 15 / 15 / 9,801 | 32 / 32 / 23,211 | 16 / 16 / 2,295 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,817 |
| 50 | `1.5` | 38 / 38 / 10,546 | 38 / 38 / 9,314 | 17 / 17 / 10,507 | exact / exact / 1,109 | 15 / 15 / 9,789 | 31 / 31 / 23,192 | 16 / 16 / 2,285 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,807 |
| 100 | `1.5` | 38 / 38 / 10,543 | 38 / 38 / 9,311 | 17 / 17 / 10,502 | exact / exact / 1,106 | 14 / 14 / 9,773 | 31 / 31 / 23,189 | 15 / 15 / 2,282 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,804 |
| 365 | `1.5` | 38 / 38 / 10,542 | 38 / 38 / 9,308 | 16 / 16 / 10,488 | exact / exact / 1,103 | 14 / 14 / 9,778 | 31 / 31 / 23,181 | 15 / 15 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,801 |
| 1000 | `1.5` | 38 / 38 / 10,547 | 38 / 38 / 9,308 | 16 / 16 / 10,495 | exact / exact / 1,103 | 13 / 13 / 9,761 | 30 / 30 / 23,187 | 14 / 14 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,801 |
| 10000 | `1.5` | 38 / 38 / 10,617 | 38 / 38 / 9,308 | 15 / 15 / 10,500 | exact / exact / 1,103 | 12 / 12 / 9,758 | 29 / 29 / 23,224 | 13 / 13 / 2,279 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 15,801 |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (36–39) | 38 (36–39) | 19 (17–19) | 18 (17–80) | 17 (16–80) | 32.5 (32–34) | 18 (17–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 2 | 38 (36–39) | 38 (36–39) | 18 (16–18) | 17 (16–80) | 16 (16–80) | 32 (31–33) | 17 (17–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 5 | 38 (36–39) | 38 (36–39) | 18 (16–18) | 17 (16–80) | 16 (16–80) | 32 (31–33) | 17 (17–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 10 | 38 (36–39) | 38 (36–39) | 17.5 (16–18) | 17 (15–80) | 16 (15–80) | 31.5 (31–33) | 17 (16–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 20 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (15–80) | 15 (15–80) | 31 (30–33) | 16 (16–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 50 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (15–80) | 15 (15–80) | 31 (30–33) | 16 (16–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 100 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (14–80) | 15 (14–80) | 30.5 (30–33) | 16 (15–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 365 | 38 (36–39) | 38 (36–39) | 16 (14–16) | 15 (14–80) | 14 (14–80) | 30 (29–33) | 15 (15–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 1000 | 38 (36–39) | 38 (36–39) | 16 (14–16) | 15 (13–80) | 14 (13–80) | 29.5 (29–33) | 15 (14–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |
| 10000 | 38 (36–39) | 38 (36–39) | 15 (13–15) | 14 (12–80) | 13 (12–80) | 28.5 (28–33) | 14 (13–80) | — (10 revert) | — (10 revert) | — (10 revert) | 71.5 (70–80) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 (38–80) | 39 (38–80) | 19 (17–19) | 18 (17–80) | 17 (16–80) | 32.5 (32–33) | 18 (17–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 2 | 39 (38–80) | 39 (38–80) | 18 (16–18) | 17 (16–80) | 16 (16–80) | 32 (31–33) | 17 (17–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 5 | 39 (38–80) | 39 (38–80) | 18 (16–18) | 17 (16–80) | 16 (16–80) | 32 (31–33) | 17 (17–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 10 | 39 (38–80) | 39 (38–80) | 17.5 (16–18) | 17 (15–80) | 16 (15–80) | 31.5 (31–33) | 17 (16–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 20 | 39 (38–80) | 39 (38–80) | 17 (15–17) | 16 (15–80) | 15 (15–80) | 31 (30–33) | 16 (16–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 50 | 39 (38–80) | 39 (38–80) | 17 (15–17) | 16 (15–80) | 15 (15–80) | 31 (30–33) | 16 (16–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 100 | 39 (38–80) | 39 (38–80) | 17 (15–17) | 16 (14–80) | 15 (14–80) | 30.5 (30–33) | 16 (15–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 365 | 39 (38–80) | 39 (38–80) | 16 (14–16) | 15 (14–80) | 14 (14–80) | 30 (29–33) | 15 (15–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 1000 | 39 (38–80) | 39 (38–80) | 16 (14–16) | 15 (13–80) | 14 (13–80) | 29.5 (29–33) | 15 (14–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |
| 10000 | 39 (38–80) | 39 (38–80) | 15 (13–15) | 14 (12–80) | 13 (12–80) | 28.5 (28–33) | 14 (13–80) | — (10 revert) | — (10 revert) | — (10 revert) | 80 (70–80) |

## amortise: Amortising loan

Step: `b = b * (1 + r) - payment`. Result: outstanding balance after N daily payments.

Subtracting nearly equal numbers. The payment retires the loan at step 366, so at N = 365 the balance is one payment and relative error is amplified several hundred times.

Inputs: **reference** principal = 300000, rate = 0.05/365, term = 366 (a mortgage-sized loan retiring at step 366); **small** principal = 10000, rate = 0.05/365, term = 366 (a small loan); **high-rate** principal = 300000, rate = 0.1/365, term = 366 (double the rate); **ten-year** principal = 300000, rate = 0.05/365, term = 3650 (a ten-year term: at N = 365 nine tenths remain); **large-low** principal = 1000000, rate = 0.03/365, term = 366 (a large loan at a low rate); **very-high** principal = 300000, rate = 0.2/365, term = 366 (20% APR); **micro** principal = 500, rate = 0.05/365, term = 366 (a tiny loan: the payment is a few units); **retires-at-10001** principal = 300000, rate = 0.05/365, term = 10001 (retires one step past the ladder's end, so N = 10,000 is the one-payment cell)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `299200.6479903559` | 39 / exact / 2,639 | 39 / exact / 1,330 | 20 / exact / 1,434 | 19 / exact / 1,147 | 19 / exact / 1,507 | 33 / 33 / 4,718 | 19 / exact / 1,418 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 4,463 |
| 2 | `298401.1864804365` | 38 / 44 / 2,251 | 38 / 44 / 940 | 19 / 25 / 967 | 19 / 23 / 766 | 19 / 23 / 1,126 | 33 / 33 / 3,604 | 19 / 23 / 1,037 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 3,517 |
| 5 | `296002.1447990159` | 38 / 43 / 2,018 | 38 / 43 / 706 | 19 / 24 / 686 | 19 / 23 / 538 | 19 / 23 / 898 | 32 / 32 / 2,936 | 19 / 23 / 809 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 2,949 |
| 10 | `292001.5505907346` | 38 / 43 / 1,940 | 38 / 43 / 628 | 19 / 24 / 593 | 18 / 22 / 462 | 18 / 22 / 822 | 32 / 32 / 2,713 | 18 / 22 / 733 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 2,760 |
| 20 | `283992.1376448092` | 37 / 42 / 1,901 | 37 / 42 / 589 | 18 / 23 / 546 | 18 / 22 / 424 | 18 / 22 / 784 | 32 / 32 / 2,602 | 18 / 22 / 695 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 2,665 |
| 50 | `259897.9672060033` | 37 / 42 / 1,878 | 37 / 42 / 565 | 18 / 23 / 518 | 18 / 22 / 401 | 18 / 22 / 761 | 31 / 31 / 2,535 | 18 / 22 / 672 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 2,608 |
| 100 | `219520.3390882176` | 37 / 42 / 1,870 | 37 / 42 / 557 | 17 / 22 / 509 | 17 / 21 / 393 | 17 / 21 / 753 | 31 / 31 / 2,513 | 17 / 21 / 664 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 2,589 |
| 365 | `840.3327859747961` | 34 / 39 / 1,865 | 34 / 39 / 552 | 15 / 19 / 502 | 15 / 18 / 388 | 15 / 18 / 748 | 28 / 28 / 2,496 | 15 / 18 / 659 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 2,575 |
| 1000 | `-556627.3884008416` | 36 / 41 / 1,865 | 36 / 41 / 550 | 17 / 22 / 500 | 17 / 21 / 386 | 17 / 21 / 753 | 31 / 31 / 2,191 | 17 / 21 / 726 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 2,536 |
| 10000 | `-16823263.35321035` | 35 / 41 / 1,882 | 35 / 41 / 550 | 16 / 22 / 500 | 16 / 21 / 386 | 16 / 21 / 756 | 29 / 29 / 2,032 | 16 / 21 / 761 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 2,516 |

### All inputs (8): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 (38–39) | 39 (38–39) | 20 (19–20) | 19 (18–19) | 19 (18–19) | 33 (33–33) | 19 (18–19) | — (8 revert) | — (8 revert) | — (8 revert) | 71 (71–71) |
| 2 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 19 (17–19) | 19 (17–19) | 33 (33–33) | 19 (17–19) | — (8 revert) | — (8 revert) | — (8 revert) | 71 (70–72) |
| 5 | 38 (37–38) | 38 (37–38) | 19 (18–19) | 19 (17–19) | 19 (17–19) | 32 (32–33) | 19 (17–19) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (70–71) |
| 10 | 38 (37–38) | 38 (37–38) | 19 (18–19) | 18 (17–18) | 18 (17–18) | 32 (32–32) | 18 (17–18) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (70–71) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 18 (16–18) | 18 (16–18) | 32 (32–32) | 18 (16–18) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (69–71) |
| 50 | 37 (36–37) | 37 (36–37) | 18 (17–18) | 18 (16–18) | 18 (16–18) | 31 (31–32) | 18 (16–18) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (69–70) |
| 100 | 37 (36–37) | 37 (36–37) | 17 (17–18) | 17 (16–17) | 17 (16–17) | 31 (31–31) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (69–69) |
| 365 | 34 (33–36) | 34 (33–36) | 15 (14–17) | 14.5 (13–17) | 14.5 (13–17) | 28 (28–31) | 14.5 (13–17) | — (8 revert) | — (8 revert) | — (8 revert) | 66 (66–68) |
| 1000 | 36 (36–36) | 36 (36–36) | 17 (16–17) | 16.5 (15–17) | 16.5 (15–17) | 31 (30–31) | 16.5 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (68–70) |
| 10000 | 35 (31–35) | 35 (31–35) | 15.5 (12–16) | 15.5 (11–16) | 15.5 (11–16) | 29 (25–30) | 15.5 (11–16) | — (8 revert) | — (8 revert) | — (8 revert) | 67 (63–68) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 80 (80–80) | 80 (80–80) | 80 (80–80) | 80 (80–80) | 80 (80–80) | 33 (33–33) | 80 (80–80) | — (8 revert) | — (8 revert) | — (8 revert) | 71 (71–71) |
| 2 | 44 (41–46) | 44 (41–46) | 24 (22–25) | 23 (21–24) | 23 (21–24) | 33 (33–33) | 23 (21–24) | — (8 revert) | — (8 revert) | — (8 revert) | 71 (70–72) |
| 5 | 43 (40–44) | 43 (40–44) | 24 (21–24) | 23 (20–23) | 23 (20–23) | 32 (32–33) | 23 (20–23) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (70–71) |
| 10 | 43 (40–44) | 43 (40–44) | 24 (21–24) | 22 (20–23) | 22 (20–23) | 32 (32–32) | 22 (20–23) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (70–71) |
| 20 | 42.5 (40–43) | 42.5 (40–43) | 23 (20–24) | 22 (19–23) | 22 (19–23) | 32 (32–32) | 22 (19–23) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (69–71) |
| 50 | 42 (39–43) | 42 (39–43) | 23 (20–23) | 22 (19–22) | 22 (19–22) | 31 (31–32) | 22 (19–22) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (69–70) |
| 100 | 42 (39–42) | 42 (39–42) | 22 (20–23) | 21 (18–22) | 21 (18–22) | 31 (31–31) | 21 (18–22) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (69–69) |
| 365 | 39 (36–41) | 39 (36–41) | 19 (17–22) | 18 (15–21) | 18 (15–21) | 28 (28–31) | 18 (15–21) | — (8 revert) | — (8 revert) | — (8 revert) | 66 (66–68) |
| 1000 | 41 (38–42) | 41 (38–42) | 21.5 (19–22) | 20.5 (18–22) | 20.5 (18–22) | 31 (30–31) | 20.5 (18–22) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (68–70) |
| 10000 | 40.5 (36–42) | 40.5 (36–42) | 21.5 (16–22) | 21 (15–21) | 21 (15–21) | 29 (25–30) | 21 (15–21) | — (8 revert) | — (8 revert) | — (8 revert) | 67 (63–68) |

## geo-mean: Running geometric mean

Step: `L += ln(x_i); g = exp(L / N), x_i = (i + 2) / (i + 1)`. Result: geometric mean of N terms; truth telescopes to ((N + 2) / 2)^(1 / N).

Index and basket maths: a sum of logs, one division, one exp. The division by N and the final exp expose every accumulated ULP.

Inputs: **reference**  (the scenario has no parameters; its inputs are the integers 1..N)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `1.5` | 38 / 38 / 13,787 | 38 / 38 / 11,481 | 19 / 19 / 12,146 | exact / exact / 2,580 | 16 / 16 / 12,066 | 33 / 33 / 28,422 | 17 / 17 / 4,358 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 22,676 |
| 2 | `1.414213562373095` | 38 / 38 / 9,830 | 38 / 38 / 8,063 | 18 / 18 / 10,322 | 17 / 17 / 2,042 | 16 / 16 / 10,383 | 33 / 33 / 25,241 | 17 / 17 / 3,360 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 17,985 |
| 5 | `1.284735157123439` | 38 / 38 / 6,974 | 38 / 38 / 5,470 | 19 / 19 / 8,889 | 17 / 17 / 1,720 | 16 / 16 / 9,067 | 33 / 33 / 22,612 | 17 / 17 / 2,767 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 15,125 |
| 10 | `1.196231198851315` | 38 / 38 / 6,336 | 38 / 38 / 4,960 | 18 / 18 / 8,503 | 17 / 17 / 1,612 | 16 / 16 / 8,686 | 33 / 33 / 21,921 | 17 / 17 / 2,535 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 14,105 |
| 20 | `1.127378204157833` | 38 / 38 / 5,876 | 38 / 38 / 4,549 | 18 / 18 / 8,308 | 17 / 17 / 1,558 | 16 / 16 / 8,538 | 33 / 33 / 21,654 | 17 / 17 / 2,322 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 72 / 72 / 13,631 |
| 50 | `1.067331844248559` | 38 / 38 / 5,580 | 38 / 38 / 4,287 | 18 / 18 / 8,184 | 17 / 17 / 1,526 | 16 / 16 / 8,376 | 33 / 33 / 21,578 | 17 / 17 / 2,194 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 13,272 |
| 100 | `1.04010144984871` | 39 / 39 / 5,451 | 39 / 39 / 4,171 | 18 / 18 / 8,147 | 17 / 17 / 1,515 | 16 / 16 / 8,318 | 33 / 33 / 21,638 | 17 / 17 / 2,151 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 13,104 |
| 365 | `1.01438248702624` | 38 / 38 / 5,303 | 38 / 38 / 4,038 | 18 / 18 / 8,117 | 17 / 17 / 1,507 | 16 / 16 / 8,258 | 33 / 33 / 21,830 | 17 / 17 / 2,120 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 13,591 |
| 1000 | `1.006235969300459` | 39 / 39 / 5,249 | 39 / 39 / 3,986 | 18 / 18 / 8,110 | 17 / 17 / 1,506 | 16 / 16 / 8,241 | 33 / 33 / 22,011 | 17 / 17 / 2,113 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 72 / 72 / 14,536 |
| 10000 | `1.00085210215008` | 38 / 38 / 5,289 | 38 / 38 / 3,958 | 18 / 18 / 8,107 | 17 / 17 / 1,505 | 16 / 16 / 8,188 | 33 / 33 / 22,491 | 17 / 17 / 2,109 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 15,045 |

### All inputs (1): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 80 (80–80) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 80 (80–80) |
| 2 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 5 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 10 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 20 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 72 (72–72) |
| 50 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 100 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 365 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 1000 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 72 (72–72) |
| 10000 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 80 (80–80) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 80 (80–80) |
| 2 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 5 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 10 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 20 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 72 (72–72) |
| 50 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 100 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 365 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |
| 1000 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 72 (72–72) |
| 10000 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) | 33 (33–33) | 17 (17–17) | — (1 revert) | — (1 revert) | — (1 revert) | 71 (71–71) |

## black-scholes-chain: Black-Scholes d1 along a price path

Step: `acc += d1(S); S += tick, with d1 = (ln(S / K) + (r + sigma^2 / 2) T) / (sigma sqrt(T))`. Result: sum of d1 over N ticks.

The options-desk case: ln, div, sqrt and mul in one expression, re-evaluated as the spot moves and aggregated.

Inputs: **reference** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (at the money, 20% vol, six months); **low-vol** spot = 100, strike = 100, sigma = 0.05, T = 0.5, r = 0.05, tick = 0.01 (5% vol: the denominator is small); **high-vol** spot = 100, strike = 100, sigma = 0.8, T = 0.5, r = 0.05, tick = 0.01 (80% vol); **in-the-money** spot = 120, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (ln(S/K) is positive and not small); **out-of-the-money** spot = 80, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (ln(S/K) is negative); **short-dated** spot = 100, strike = 100, sigma = 0.2, T = 0.01, r = 0.05, tick = 0.01 (sqrt(T) is small); **long-dated** spot = 100, strike = 100, sigma = 0.2, T = 2, r = 0.05, tick = 0.01 (two years); **coarse-ticks** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 1 (whole-unit ticks: S doubles by N = 100 and reaches 10,100)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `0.2474873734152916` | 37 / 37 / 15,372 | 37 / 37 / 8,407 | 18 / 18 / 11,764 | 17 / 17 / 3,822 | 17 / 17 / 6,998 | 34 / 34 / 13,162 | 17 / 17 / 7,708 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 17,672 |
| 2 | `0.4956818182587876` | 37 / 37 / 13,693 | 37 / 37 / 8,444 | 17 / 17 / 10,635 | 18 / 18 / 2,921 | 16 / 16 / 8,436 | 32 / 32 / 19,642 | 17 / 17 / 6,386 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 19,787 |
| 5 | `1.244506874463792` | 37 / 37 / 12,686 | 37 / 37 / 8,466 | 17 / 17 / 9,957 | 17 / 17 / 2,381 | 15 / 15 / 9,431 | 32 / 32 / 23,377 | 16 / 16 / 5,592 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 21,048 |
| 10 | `2.506683467804941` | 36 / 37 / 12,351 | 36 / 37 / 8,473 | 17 / 17 / 9,731 | 17 / 17 / 2,201 | 15 / 15 / 9,734 | 31 / 31 / 24,511 | 16 / 16 / 5,328 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 21,474 |
| 20 | `5.084010514032979` | 36 / 37 / 12,184 | 36 / 37 / 8,477 | 17 / 17 / 9,618 | 17 / 17 / 2,111 | 15 / 15 / 9,905 | 31 / 31 / 25,006 | 16 / 16 / 5,196 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 21,683 |
| 50 | `13.23914876467473` | 36 / 37 / 12,084 | 36 / 37 / 8,479 | 17 / 17 / 9,551 | 17 / 17 / 2,057 | 15 / 15 / 10,052 | 31 / 31 / 25,202 | 16 / 16 / 5,116 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 21,355 |
| 100 | `28.23736439326609` | 36 / 37 / 12,100 | 36 / 37 / 8,523 | 17 / 17 / 9,528 | 17 / 17 / 2,039 | 15 / 15 / 10,098 | 30 / 30 / 25,187 | 16 / 16 / 5,090 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 20,507 |
| 365 | `136.7454508837998` | 36 / 37 / 12,173 | 36 / 37 / 8,599 | 17 / 17 / 9,512 | 17 / 17 / 2,025 | 15 / 15 / 10,135 | 30 / 30 / 25,027 | 16 / 16 / 5,071 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 19,969 |
| 1000 | `589.4747739528645` | 36 / 37 / 12,272 | 36 / 37 / 8,666 | 17 / 18 / 9,508 | 18 / 18 / 2,022 | 15 / 15 / 10,171 | 30 / 30 / 24,823 | 17 / 17 / 5,066 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 19,935 |
| 10000 | `29787.55928753143` | 36 / 39 / 12,890 | 36 / 39 / 8,830 | 18 / 19 / 9,506 | 17 / 17 / 2,021 | 16 / 16 / 10,223 | 30 / 30 / 24,408 | 17 / 17 / 5,313 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 67 / 67 / 20,186 |

### All inputs (8): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 (35–38) | 37 (35–38) | 18 (17–19) | 17 (17–80) | 17 (16–80) | 34 (33–34) | 17 (17–80) | — (8 revert) | — (8 revert) | — (8 revert) | 71 (70–71) |
| 2 | 37 (35–38) | 37 (35–38) | 17.5 (16–18) | 17.5 (15–18) | 16 (14–16) | 32.5 (30–33) | 17 (15–18) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (69–72) |
| 5 | 37 (35–38) | 37 (35–38) | 17 (16–18) | 17 (15–18) | 15.5 (14–16) | 32 (30–33) | 17 (15–18) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (68–71) |
| 10 | 37 (35–38) | 37 (35–38) | 17 (16–18) | 17 (15–18) | 15.5 (14–16) | 32 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (68–71) |
| 20 | 37 (35–37) | 37 (35–37) | 17.5 (16–18) | 17 (15–17) | 16 (14–16) | 32 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (68–71) |
| 50 | 37 (35–38) | 37 (35–38) | 17.5 (16–18) | 17 (15–17) | 16 (14–16) | 31 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (67–70) |
| 100 | 37 (36–39) | 37 (36–39) | 17.5 (16–19) | 17 (16–17) | 16 (14–16) | 31 (30–32) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (67–71) |
| 365 | 37 (36–38) | 37 (36–38) | 17.5 (17–19) | 17 (16–17) | 16 (15–17) | 30.5 (30–31) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) | 68 (67–70) |
| 1000 | 37 (36–38) | 37 (36–38) | 17 (17–18) | 17 (16–18) | 16 (15–17) | 30 (30–31) | 17 (16–18) | — (8 revert) | — (8 revert) | — (8 revert) | 68 (67–70) |
| 10000 | 37 (36–38) | 37 (36–38) | 18 (17–20) | 17 (17–18) | 16 (16–17) | 30 (29–30) | 17 (17–17) | — (8 revert) | — (8 revert) | — (8 revert) | 67.5 (67–70) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 (35–38) | 37 (35–38) | 18 (17–19) | 17 (17–80) | 17 (16–80) | 34 (33–35) | 17 (17–80) | — (8 revert) | — (8 revert) | — (8 revert) | 71 (71–71) |
| 2 | 37 (35–39) | 37 (35–39) | 18 (16–19) | 17.5 (15–18) | 16 (14–16) | 32.5 (30–33) | 17 (15–18) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (69–71) |
| 5 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–18) | 15.5 (14–16) | 32 (30–32) | 17 (15–18) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (68–71) |
| 10 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–18) | 15.5 (14–16) | 32 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (68–71) |
| 20 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (14–16) | 32 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) | 70 (68–71) |
| 50 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (14–16) | 31 (30–32) | 17 (15–17) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (67–70) |
| 100 | 37.5 (36–39) | 37.5 (36–39) | 18 (16–19) | 17 (16–17) | 16 (14–16) | 31 (30–32) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) | 69 (67–71) |
| 365 | 37 (36–38) | 37 (36–38) | 18 (17–19) | 17 (16–17) | 16 (15–17) | 30.5 (30–31) | 17 (16–17) | — (8 revert) | — (8 revert) | — (8 revert) | 68 (67–71) |
| 1000 | 37.5 (37–38) | 37.5 (37–38) | 18 (17–19) | 17 (16–18) | 16 (15–17) | 30 (30–31) | 17 (16–18) | — (8 revert) | — (8 revert) | — (8 revert) | 68 (67–70) |
| 10000 | 38 (37–39) | 38 (37–39) | 18 (17–20) | 17 (17–18) | 16 (16–17) | 30 (29–30) | 17 (17–17) | — (8 revert) | — (8 revert) | — (8 revert) | 67.5 (67–70) |

## cumulative-product: Cumulative product of small factors

Step: `p = p * (1 + eps_i), eps_i = +eps for odd i, -eps for even i`. Result: product after N factors.

The general form of fee accrual, index levels and LP share accounting: many factors a basis point from one. The drift from 1 is where the digits are, and it is small.

Inputs: **reference** eps = 0.0001 (a basis point); **percent** eps = 0.01 (one percent); **tenth-percent** eps = 0.001 (ten basis points); **micro** eps = 0.000001 (a hundredth of a basis point: the factors are within WAD's last digits of one); **five-percent** eps = 0.05 (large factors: the product falls to 4e-6 by N = 10,000)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `1.0001` | 39 / exact / 2,732 | 39 / exact / 1,423 | 20 / exact / 1,491 | exact / exact / 1,234 | exact / exact / 1,594 | 35 / 35 / 5,693 | exact / exact / 1,505 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 4,544 |
| 2 | `0.99999999` | 39 / 39 / 2,276 | 39 / 39 / 952 | 19 / 19 / 944 | exact / exact / 789 | exact / exact / 1,149 | 33 / 33 / 3,409 | exact / exact / 1,060 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,944 |
| 5 | `1.000099979998` | 38 / 38 / 2,003 | 38 / 38 / 669 | 18 / 18 / 616 | 20 / 20 / 522 | 20 / 20 / 882 | 33 / 33 / 2,023 | 20 / 20 / 793 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 1,986 |
| 10 | `0.999999950000001` | 37 / 37 / 1,912 | 37 / 37 / 575 | 18 / 18 / 506 | 17 / 17 / 433 | 17 / 17 / 793 | 32 / 32 / 1,566 | 17 / 17 / 704 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 72 / 72 / 1,666 |
| 20 | `0.9999999000000045` | 37 / 37 / 1,867 | 37 / 37 / 528 | 18 / 18 / 452 | 17 / 17 / 388 | 17 / 17 / 748 | 32 / 32 / 1,335 | 17 / 17 / 659 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 1,507 |
| 50 | `0.99999975000003` | 37 / 37 / 1,839 | 37 / 37 / 500 | 17 / 17 / 419 | 16 / 16 / 362 | 16 / 16 / 722 | 32 / 32 / 1,197 | 16 / 16 / 633 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,411 |
| 100 | `0.9999995000001225` | 36 / 36 / 1,830 | 36 / 36 / 490 | 17 / 17 / 408 | 16 / 16 / 353 | 16 / 16 / 713 | 31 / 31 / 1,151 | 16 / 16 / 624 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,379 |
| 365 | `1.000098179819647` | 36 / 36 / 1,824 | 36 / 36 / 484 | 16 / 16 / 400 | 15 / 15 / 346 | 15 / 15 / 706 | 31 / 31 / 1,118 | 15 / 15 / 617 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 1,356 |
| 1000 | `0.999995000012475` | 35 / 35 / 1,824 | 35 / 35 / 482 | 16 / 16 / 398 | 15 / 15 / 345 | 15 / 15 / 705 | 30 / 30 / 1,110 | 15 / 15 / 616 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,350 |
| 10000 | `0.9999500012497292` | 34 / 34 / 1,841 | 34 / 34 / 481 | 15 / 15 / 397 | 14 / 14 / 344 | 14 / 14 / 704 | 29 / 29 / 1,105 | 14 / 14 / 615 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,347 |

### All inputs (5): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 80 (80–80) | 80 (80–80) | 34 (33–35) | 80 (80–80) | — (5 revert) | — (5 revert) | — (5 revert) | 71 (71–71) |
| 2 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 80 (80–80) | 80 (80–80) | 33 (33–34) | 80 (80–80) | — (5 revert) | — (5 revert) | — (5 revert) | 71 (71–71) |
| 5 | 38 (37–38) | 38 (37–38) | 18 (18–19) | 80 (20–80) | 80 (20–80) | 33 (33–33) | 80 (20–80) | — (5 revert) | — (5 revert) | — (5 revert) | 71 (70–71) |
| 10 | 37 (37–37) | 37 (37–37) | 18 (18–19) | 18 (17–22) | 18 (17–22) | 32 (32–33) | 18 (17–22) | — (5 revert) | — (5 revert) | — (5 revert) | 71 (70–72) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 17 (17–22) | 17 (17–22) | 32 (32–32) | 17 (17–22) | — (5 revert) | — (5 revert) | — (5 revert) | 70 (70–71) |
| 50 | 37 (37–37) | 37 (37–37) | 17 (17–18) | 16 (16–21) | 16 (16–21) | 32 (32–32) | 16 (16–21) | — (5 revert) | — (5 revert) | — (5 revert) | 70 (69–71) |
| 100 | 36 (36–36) | 36 (36–36) | 17 (17–17) | 16 (16–20) | 16 (16–20) | 31 (31–31) | 16 (16–20) | — (5 revert) | — (5 revert) | — (5 revert) | 70 (69–70) |
| 365 | 36 (36–36) | 36 (36–36) | 16 (16–17) | 15 (15–19) | 15 (15–19) | 31 (31–31) | 15 (15–19) | — (5 revert) | — (5 revert) | — (5 revert) | 69 (69–71) |
| 1000 | 35 (35–35) | 35 (35–35) | 16 (16–16) | 15 (15–18) | 15 (15–18) | 30 (30–30) | 15 (15–18) | — (5 revert) | — (5 revert) | — (5 revert) | 69 (68–70) |
| 10000 | 34 (30–34) | 34 (30–34) | 15 (11–15) | 14 (9–16) | 14 (9–16) | 29 (29–29) | 14 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) | 69 (67–70) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 80 (80–80) | 80 (80–80) | 80 (80–80) | 80 (80–80) | 80 (80–80) | 34 (33–35) | 80 (80–80) | — (5 revert) | — (5 revert) | — (5 revert) | 71 (71–71) |
| 2 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 80 (80–80) | 80 (80–80) | 33 (33–34) | 80 (80–80) | — (5 revert) | — (5 revert) | — (5 revert) | 71 (71–71) |
| 5 | 38 (38–38) | 38 (38–38) | 18 (18–19) | 80 (20–80) | 80 (20–80) | 33 (33–33) | 80 (20–80) | — (5 revert) | — (5 revert) | — (5 revert) | 71 (70–71) |
| 10 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 18 (17–22) | 18 (17–22) | 32 (32–33) | 18 (17–22) | — (5 revert) | — (5 revert) | — (5 revert) | 71 (70–72) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 17 (17–22) | 17 (17–22) | 32 (32–32) | 17 (17–22) | — (5 revert) | — (5 revert) | — (5 revert) | 70 (70–71) |
| 50 | 37 (37–37) | 37 (37–37) | 17 (17–17) | 16 (16–21) | 16 (16–21) | 32 (32–32) | 16 (16–21) | — (5 revert) | — (5 revert) | — (5 revert) | 70 (69–71) |
| 100 | 36 (36–36) | 36 (36–36) | 17 (17–17) | 16 (16–20) | 16 (16–20) | 31 (31–31) | 16 (16–20) | — (5 revert) | — (5 revert) | — (5 revert) | 70 (69–70) |
| 365 | 36 (36–36) | 36 (36–36) | 16 (16–17) | 15 (15–19) | 15 (15–19) | 31 (31–31) | 15 (15–19) | — (5 revert) | — (5 revert) | — (5 revert) | 69 (69–71) |
| 1000 | 35 (35–35) | 35 (35–35) | 16 (16–16) | 15 (15–18) | 15 (15–18) | 30 (30–30) | 15 (15–18) | — (5 revert) | — (5 revert) | — (5 revert) | 70 (68–70) |
| 10000 | 34 (30–34) | 34 (30–34) | 15 (11–15) | 14 (9–16) | 14 (9–16) | 29 (29–29) | 14 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) | 69 (67–70) |

## compound-annual: Annual compounding at 10% (README claim check)

Step: `b = b * 1.1`. Result: balance after N years.

The old README asserted $25,937.42 true against $25,932.38 for Solady at N = 10 with no source. This row regenerates that number.

Inputs: **reference** principal = 10000, rate = 0.1 (the README claim); **five-pct** principal = 10000, rate = 0.05 (5% a year); **unit** principal = 1, rate = 0.1 (one unit); **million** principal = 1000000, rate = 0.1 (a million units: ABDK overflows sooner); **fifty-pct** principal = 10000, rate = 0.5 (50% a year: every library overflows before N = 100)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `11000.0` | 38 / exact / 2,491 | 38 / exact / 1,155 | 19 / exact / 1,189 | exact / exact / 999 | exact / exact / 1,359 | 33 / 33 / 3,188 | exact / exact / 1,270 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 610 | exact / 72 / 3,130 |
| 2 | `12100.0` | 38 / 77 / 2,100 | 38 / 77 / 762 | 19 / 39 / 737 | exact / exact / 616 | exact / exact / 976 | 33 / 33 / 2,101 | exact / exact / 887 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 420 | 71 / 71 / 2,181 |
| 5 | `16105.1` | 38 / 42 / 1,866 | 38 / 42 / 527 | 18 / 23 / 466 | exact / exact / 386 | exact / exact / 746 | 33 / 33 / 1,449 | exact / exact / 657 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 197 | 70 / 70 / 1,612 |
| 10 | `25937.424601` | 37 / 42 / 1,788 | 37 / 42 / 448 | 18 / 23 / 376 | exact / exact / 309 | exact / exact / 669 | 32 / 32 / 1,228 | exact / exact / 580 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 121 | 70 / 70 / 1,423 |
| 20 | `67274.999493256` | 37 / 42 / 1,749 | 37 / 42 / 409 | 18 / 22 / 331 | exact / exact / 271 | exact / exact / 631 | 32 / 32 / 1,117 | exact / exact / 542 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 68 | 70 / 70 / 1,328 |
| 50 | `1173908.528796953` | 37 / 41 / 1,725 | 37 / 41 / 385 | 17 / 22 / 304 | 22 / 22 / 248 | 22 / 22 / 608 | 32 / 32 / 1,052 | 22 / 22 / 519 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 29 / 29 / 31 | 69 / 69 / 1,271 |
| 100 | `137806123.3982227` | 36 / 41 / 1,718 | 36 / 41 / 377 | 17 / 22 / 295 | 22 / 22 / 240 | 22 / 22 / 600 | 31 / 31 / 1,030 | 22 / 22 / 511 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 29 / 29 / 17 | 69 / 69 / 1,252 |
| 365 | `1.283305580313353e+19` | 36 / 41 / 1,712 | 36 / 41 / 372 | reverts `0x00000000` | 22 / 22 / 235 | 22 / 22 / 595 | 31 / 31 / 1,015 | 22 / 22 / 506 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 28 / 28 / 6 | 68 / 68 / 1,239 |
| 1000 | `2.469932918005826e+45` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | 22 / 22 / 602 | 30 / 30 / 1,011 | reverts `0x4e487b71` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x49f7642b` | 68 / 68 / 1,235 |
| 10000 | `8.449900251200348e+417` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | reverts `0x120b5b43` | 29 / 29 / 1,009 | reverts `0x4e487b71` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x49f7642b` | 67 / 67 / 1,234 |

### All inputs (5): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–80) | 38 (38–80) | 19 (19–80) | 80 (80–80) | 80 (80–80) | 33 (33–80) | 80 (80–80) | — (5 revert) | — (5 revert) | 80 (80–80) | 80 (71–80) |
| 2 | 38 (38–80) | 38 (38–80) | 19 (19–80) | 80 (80–80) | 80 (80–80) | 33 (33–80) | 80 (80–80) | — (5 revert) | — (5 revert) | 80 (80–80) | 80 (71–80) |
| 5 | 38 (37–80) | 38 (37–80) | 18 (18–80) | 80 (80–80) | 80 (80–80) | 33 (32–80) | 80 (80–80) | — (5 revert) | — (5 revert) | 80 (80–80) | 70 (70–80) |
| 10 | 37 (37–80) | 37 (37–80) | 18 (18–80) | 80 (80–80) | 80 (80–80) | 32 (32–80) | 80 (80–80) | — (5 revert) | — (5 revert) | 80 (80–80) | 70 (70–80) |
| 20 | 37 (37–80) | 37 (37–80) | 18 (18–80) | 80 (18–80) | 80 (18–80) | 32 (32–80) | 80 (18–80) | — (5 revert) | — (5 revert) | 80 (28–80) | 70 (70–80) |
| 50 | 37 (36–80) | 37 (36–80) | 17 (17–80) | 22 (18–25) | 22 (18–25) | 32 (31–80) | 22 (18–25) | — (5 revert) | — (5 revert) | 29 (28–33) | 69 (69–80) |
| 100 | 36 (36–80) | 36 (36–80) | 17 (17–17), 1 revert | 22 (18–25) | 22 (18–25) | 31 (31–32) | 22 (18–25) | — (5 revert) | — (5 revert) | 29 (27–33) | 69 (69–80) |
| 365 | 36 (36–36), 1 revert | 36 (36–36), 1 revert | 16 (16–16), 3 revert | 21.5 (18–24), 1 revert | 21.5 (18–24), 1 revert | 31 (31–31) | 21.5 (18–24), 1 revert | — (5 revert) | — (5 revert) | 28 (26–28), 1 revert | 68 (68–69) |
| 1000 | 35 (35–35), 4 revert | 35 (35–35), 4 revert | — (5 revert) | 21 (21–21), 4 revert | 21.5 (18–24), 1 revert | 30 (30–31) | 21 (21–21), 4 revert | — (5 revert) | — (5 revert) | — (5 revert) | 68 (68–69) |
| 10000 | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | 29 (29–30) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | 67 (67–67) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 80 (80–80) | 80 (80–80) | 80 (80–80) | 80 (80–80) | 80 (80–80) | 33 (33–80) | 80 (80–80) | — (5 revert) | — (5 revert) | 80 (80–80) | 72 (71–80) |
| 2 | 77 (38–80) | 77 (38–80) | 39 (20–80) | 80 (80–80) | 80 (80–80) | 33 (33–80) | 80 (80–80) | — (5 revert) | — (5 revert) | 80 (80–80) | 72 (71–80) |
| 5 | 42 (38–80) | 42 (38–80) | 23 (19–80) | 80 (80–80) | 80 (80–80) | 33 (32–80) | 80 (80–80) | — (5 revert) | — (5 revert) | 80 (80–80) | 70 (70–80) |
| 10 | 42 (38–80) | 42 (38–80) | 23 (18–80) | 80 (80–80) | 80 (80–80) | 32 (32–80) | 80 (80–80) | — (5 revert) | — (5 revert) | 80 (80–80) | 70 (70–80) |
| 20 | 42 (37–80) | 42 (37–80) | 22 (18–80) | 80 (18–80) | 80 (18–80) | 32 (32–80) | 80 (18–80) | — (5 revert) | — (5 revert) | 80 (28–80) | 70 (70–80) |
| 50 | 41 (37–80) | 41 (37–80) | 22 (18–80) | 22 (18–25) | 22 (18–25) | 32 (31–80) | 22 (18–25) | — (5 revert) | — (5 revert) | 29 (28–33) | 69 (69–80) |
| 100 | 41 (37–80) | 41 (37–80) | 22 (18–24), 1 revert | 22 (18–25) | 22 (18–25) | 31 (31–32) | 22 (18–25) | — (5 revert) | — (5 revert) | 29 (27–33) | 69 (69–80) |
| 365 | 41 (37–44), 1 revert | 41 (37–44), 1 revert | 20 (18–22), 3 revert | 21.5 (18–24), 1 revert | 21.5 (18–24), 1 revert | 31 (31–31) | 21.5 (18–24), 1 revert | — (5 revert) | — (5 revert) | 28 (26–28), 1 revert | 68 (68–69) |
| 1000 | 41 (41–41), 4 revert | 41 (41–41), 4 revert | — (5 revert) | 21 (21–21), 4 revert | 21.5 (18–24), 1 revert | 30 (30–31) | 21 (21–21), 4 revert | — (5 revert) | — (5 revert) | — (5 revert) | 68 (68–69) |
| 10000 | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | 29 (29–30) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | 67 (67–67) |

## accrual-per-second: Per-second accrual

Step: `b = b0 * (1 + r/31536000)^(N * 86400)`. Result: balance after N days of per-second compounding.

How Maker's jug and pot accrue: the rate per second, compounded every second, N days at a time. The rate is 1.6e-9 at 5% APR, which an 18-decimal grid holds to ten digits before any arithmetic; FP127 computes the power as one exact integer power (compound), the WAD and 64.64 libraries as exp(n ln(1 + r)), Maker as rpow.

Inputs: **reference** principal = 10000, rateSec = 0.05/31536000 ($10,000 at 5% APR, the lending protocol's steady state); **one-pct** principal = 10000, rateSec = 0.01/31536000 (a slow rate: 1% APR is 3.2e-10 a second); **twenty-pct** principal = 10000, rateSec = 0.2/31536000 (20% APR); **fifty-pct** principal = 10000, rateSec = 0.5/31536000 (50% APR, where the three-term expansions strain); **unit** principal = 1, rateSec = 0.05/31536000 (one unit, the fraction carries everything); **huge** principal = 100000000, rateSec = 0.05/31536000 (a hundred-million-unit pool)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10001.36995684313` | 33 / 39 / 9,601 | 33 / 39 / 7,443 | 14 / 14 / 11,908 | 13 / 13 / 2,517 | 12 / 12 / 10,845 | 28 / 28 / 31,502 | 13 / 17 / 3,464 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 22 / 22 / 3,471 | 66 / 66 / 20,577 |
| 2 | `10002.74010136444` | 33 / 38 / 4,926 | 33 / 38 / 3,855 | 13 / 14 / 5,961 | 12 / 12 / 1,258 | 11 / 11 / 5,429 | 28 / 28 / 15,753 | 13 / 17 / 1,732 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 22 / 22 / 1,809 | 66 / 66 / 10,291 |
| 5 | `10006.85166125453` | 33 / 39 / 2,140 | 33 / 39 / 1,715 | 13 / 13 / 2,370 | 12 / 12 / 503 | 11 / 11 / 2,152 | 28 / 28 / 6,278 | 13 / 18 / 692 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 803 | 65 / 65 / 4,119 |
| 10 | `10013.70801703526` | 32 / 39 / 1,095 | 32 / 39 / 884 | 13 / 13 / 1,185 | 12 / 12 / 251 | 11 / 11 / 1,077 | 27 / 27 / 3,139 | 12 / 18 / 346 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 416 | 65 / 65 / 2,060 |
| 20 | `10027.43482504363` | 32 / 38 / 560 | 32 / 38 / 455 | 12 / 13 / 593 | 11 / 11 / 125 | 10 / 10 / 549 | 27 / 27 / 1,569 | 12 / 18 / 173 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 215 | 65 / 65 / 1,029 |
| 50 | `10068.72825267094` | 32 / 39 / 234 | 32 / 39 / 193 | 12 / 12 / 238 | 11 / 11 / 50 | 10 / 10 / 221 | 27 / 27 / 632 | 12 / 18 / 69 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 20 / 20 / 92 | 64 / 64 / 412 |
| 100 | `10137.92886261339` | 31 / 39 / 119 | 31 / 39 / 99 | 12 / 12 / 119 | 11 / 11 / 25 | 10 / 10 / 110 | 26 / 26 / 316 | 11 / 18 / 34 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 20 / 20 / 47 | 64 / 64 / 206 |
| 365 | `10512.71096334355` | 31 / 39 / 34 | 31 / 39 / 29 | 11 / 11 / 32 | 10 / 10 / 6 | 9 / 9 / 30 | 26 / 26 / 86 | 11 / 18 / 9 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 19 / 20 / 13 | 63 / 63 / 56 |
| 1000 | `11468.12438528825` | 30 / 38 / 12 | 30 / 38 / 10 | 11 / 11 / 11 | 10 / 10 / 2 | 9 / 9 / 11 | 25 / 25 / 31 | 10 / 18 / 3 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 19 / 19 / 5 | 63 / 63 / 20 |
| 10000 | `39348.11638983319` | 29 / 40 / 1 | 29 / 40 / 1 | 10 / 10 / 1 | 9 / 9 / 0 | 8 / 8 / 1 | 24 / 24 / 3 | 9 / 18 / 0 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 18 / 18 / 0 | 62 / 62 / 2 |

### All inputs (6): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 33 (33–35) | 33 (33–35) | 14 (14–14) | 12.5 (12–13) | 12 (12–12) | 28 (28–29) | 13 (13–13) | — (6 revert) | — (6 revert) | 22 (22–23) | 66 (66–67) |
| 2 | 33 (33–34) | 33 (33–34) | 13 (13–14) | 12 (12–12) | 11 (11–11) | 28 (28–29) | 12.5 (12–13) | — (6 revert) | — (6 revert) | 22 (21–23) | 66 (66–66) |
| 5 | 33 (32–34) | 33 (32–34) | 13 (13–13) | 12 (12–12) | 11 (11–11) | 28 (28–28) | 12.5 (12–13) | — (6 revert) | — (6 revert) | 21 (21–22) | 65 (65–66) |
| 10 | 32 (32–34) | 32 (32–34) | 13 (13–13) | 11.5 (11–12) | 11 (11–11) | 27 (27–28) | 12 (12–12) | — (6 revert) | — (6 revert) | 21 (21–22) | 65 (65–66) |
| 20 | 32 (32–33) | 32 (32–33) | 12 (12–13) | 11 (11–11) | 10 (10–10) | 27 (27–28) | 11.5 (11–12) | — (6 revert) | — (6 revert) | 21 (20–22) | 65 (65–65) |
| 50 | 32 (31–33) | 32 (31–33) | 12 (12–12) | 11 (11–11) | 10 (10–10) | 27 (27–27) | 11.5 (11–12) | — (6 revert) | — (6 revert) | 20 (20–21) | 64 (64–65) |
| 100 | 31 (31–33) | 31 (31–33) | 12 (12–12) | 10.5 (10–11) | 10 (10–10) | 26 (26–27) | 11 (11–11) | — (6 revert) | — (6 revert) | 20 (20–21) | 64 (64–65) |
| 365 | 31 (31–32) | 31 (31–32) | 11 (11–11) | 10 (10–10) | 9 (9–9) | 26 (26–26) | 10.5 (10–11) | — (6 revert) | — (6 revert) | 19 (19–21) | 63.5 (63–64) |
| 1000 | 30 (30–32) | 30 (30–32) | 11 (11–11) | 9.5 (9–10) | 9 (9–9) | 25 (25–26) | 10 (10–10) | — (6 revert) | — (6 revert) | 19 (19–20) | 63 (63–64) |
| 10000 | 29 (29–31) | 29 (29–31) | 10 (10–10) | 8.5 (8–9) | 8 (8–8) | 24 (24–25) | 9 (9–9) | — (6 revert) | — (6 revert) | 18 (18–19) | 62 (62–63) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 (38–39) | 39 (38–39) | 14 (14–14) | 13 (13–13) | 12 (12–12) | 28 (28–29) | 17.5 (17–18) | — (6 revert) | — (6 revert) | 22 (22–23) | 66 (66–67) |
| 2 | 38 (38–39) | 38 (38–39) | 14 (13–14) | 12 (12–13) | 11 (11–11) | 28 (28–29) | 17 (17–18) | — (6 revert) | — (6 revert) | 22 (22–22) | 66 (66–66) |
| 5 | 39 (39–39) | 39 (39–39) | 13 (13–13) | 12 (12–12) | 11 (11–11) | 28 (28–28) | 17.5 (17–18) | — (6 revert) | — (6 revert) | 21.5 (21–22) | 65 (65–66) |
| 10 | 39 (38–40) | 39 (38–40) | 13 (13–13) | 12 (12–12) | 11 (11–11) | 27 (27–28) | 17.5 (17–18) | — (6 revert) | — (6 revert) | 21 (21–22) | 65 (65–66) |
| 20 | 38 (38–39) | 38 (38–39) | 13 (12–13) | 11 (11–12) | 10 (10–10) | 27 (27–28) | 18 (17–18) | — (6 revert) | — (6 revert) | 21 (21–21) | 65 (65–65) |
| 50 | 39 (38–39) | 39 (38–39) | 12 (12–12) | 11 (11–11) | 10 (10–10) | 27 (27–27) | 18 (17–18) | — (6 revert) | — (6 revert) | 20.5 (20–21) | 64 (64–65) |
| 100 | 39 (38–39) | 39 (38–39) | 12 (12–12) | 11 (11–11) | 10 (10–10) | 26 (26–27) | 18 (17–18) | — (6 revert) | — (6 revert) | 20 (20–21) | 64 (64–65) |
| 365 | 39 (39–40) | 39 (39–40) | 11 (11–12) | 10 (10–11) | 9 (9–9) | 26 (26–26) | 18 (17–18) | — (6 revert) | — (6 revert) | 20 (20–20) | 63.5 (63–64) |
| 1000 | 38.5 (38–39) | 38.5 (38–39) | 11 (11–11) | 10 (10–10) | 9 (9–9) | 25 (25–26) | 18 (17–18) | — (6 revert) | — (6 revert) | 19 (19–20) | 63 (63–64) |
| 10000 | 40 (39–44) | 40 (39–44) | 10 (10–10) | 9 (9–9) | 8 (8–8) | 24 (24–25) | 18 (17–18) | — (6 revert) | — (6 revert) | 18 (18–19) | 62 (62–63) |

## accrual-continuous: Continuous accrual

Step: `b = b0 * e^(r * N / 365)`. Result: balance after N days of continuous accrual.

How Aave and Morpho accrue: the ideal is e^(rate * time), and both ship a three-term expansion of it (1 + x + x^2/2 + x^3/6), which Aave notes 'slightly underpays liquidity providers and undercharges borrowers'. Every library is judged against the exponential it approximates. The step here is one accrual spanning N days, which is what a market that nobody touched for N days computes on its next interaction; the expansion's error is x^4/24 with x = rate * years, so it is invisible at daily updates and the whole story at a year or more. Morpho holds the rate per second in WAD (1,585,489,599 wei at 5% APR), ten significant digits before any arithmetic; both digit counts show that loss, since the format truth is built from the annual rate the other libraries receive.

Inputs: **reference** principal = 10000, rateAnnual = 0.05 ($10,000 at 5% APR, the lending protocol's steady state); **one-pct** principal = 10000, rateAnnual = 0.01 (a slow rate: 1% APR is 3.2e-10 a second); **twenty-pct** principal = 10000, rateAnnual = 0.2 (20% APR); **fifty-pct** principal = 10000, rateAnnual = 0.5 (50% APR, where the three-term expansions strain); **unit** principal = 1, rateAnnual = 0.05 (one unit, the fraction carries everything); **huge** principal = 100000000, rateAnnual = 0.05 (a hundred-million-unit pool)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10001.36995684422` | 38 / 38 / 10,436 | 38 / 38 / 6,561 | 19 / 19 / 5,082 | 18 / 18 / 2,062 | 18 / 18 / 5,114 | 33 / 33 / 11,226 | 18 / 18 / 3,453 | 16 / 16 / 1,608 | 13 / 13 / 1,442 | reverts `0x7bb9ae15` | 71 / 71 / 13,526 |
| 2 | `10002.74010136661` | 38 / 38 / 5,346 | 38 / 38 / 3,435 | 19 / 19 / 2,541 | 18 / 18 / 1,031 | 17 / 17 / 2,564 | 33 / 33 / 5,615 | 18 / 18 / 1,726 | 15 / 15 / 804 | 13 / 13 / 721 | reverts `0x7bb9ae15` | 72 / 72 / 6,766 |
| 5 | `10006.85166125997` | 39 / 39 / 2,154 | 39 / 39 / 1,385 | 19 / 19 / 1,010 | 18 / 18 / 412 | 17 / 17 / 1,025 | 34 / 34 / 2,234 | 18 / 18 / 690 | 14 / 14 / 321 | 13 / 13 / 288 | reverts `0x7bb9ae15` | 73 / 73 / 2,708 |
| 10 | `10013.70801704614` | 38 / 38 / 1,130 | 38 / 38 / 755 | 18 / 18 / 506 | 18 / 18 / 206 | 17 / 17 / 515 | 33 / 33 / 1,117 | 18 / 18 / 345 | 12 / 12 / 160 | 12 / 12 / 144 | reverts `0x7bb9ae15` | 72 / 72 / 1,355 |
| 20 | `10027.43482506541` | 38 / 38 / 554 | 38 / 38 / 364 | 19 / 19 / 253 | 18 / 18 / 103 | 18 / 18 / 267 | 34 / 34 / 558 | 18 / 18 / 172 | 11 / 11 / 80 | 11 / 11 / 72 | reverts `0x7bb9ae15` | 71 / 71 / 677 |
| 50 | `10068.72825272561` | 38 / 38 / 214 | 38 / 38 / 138 | 18 / 18 / 103 | 18 / 18 / 41 | 17 / 17 / 108 | 33 / 33 / 223 | 18 / 18 / 69 | 10 / 10 / 32 | 10 / 10 / 28 | reverts `0x7bb9ae15` | 72 / 72 / 271 |
| 100 | `10137.92886272349` | 38 / 38 / 110 | 38 / 38 / 72 | 19 / 19 / 50 | 18 / 18 / 20 | 17 / 17 / 54 | 34 / 34 / 111 | 18 / 18 / 34 | 8 / 8 / 16 | 8 / 8 / 14 | reverts `0x7bb9ae15` | 71 / 71 / 135 |
| 365 | `10512.71096376024` | 38 / 39 / 30 | 38 / 39 / 20 | 19 / 20 / 14 | 18 / 18 / 5 | 18 / 18 / 15 | 33 / 33 / 30 | 18 / 18 / 9 | 6 / 6 / 4 | 6 / 6 / 3 | reverts `0x7bb9ae15` | 71 / 71 / 36 |
| 1000 | `11468.12438653363` | 38 / 38 / 11 | 38 / 38 / 7 | 18 / 19 / 5 | 18 / 18 / 2 | 17 / 17 / 5 | 33 / 33 / 11 | 18 / 18 / 3 | 4 / 4 / 1 | 4 / 4 / 1 | reverts `0x7bb9ae15` | 71 / 71 / 13 |
| 10000 | `39348.11643256335` | 37 / 38 / 1 | 37 / 38 / 0 | 17 / 19 / 0 | 17 / 17 / 0 | 17 / 17 / 0 | 33 / 33 / 1 | 17 / 17 / 0 | 1 / 1 / 0 | 1 / 1 / 0 | reverts `0x7bb9ae15` | 72 / 71 / 1 |

### All inputs (6): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 18 (17–18) | 17.5 (17–18) | 33.5 (33–34) | 18 (17–18) | 16 (12–19) | 13 (12–13) | — (6 revert) | 71 (71–72) |
| 2 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 18 (17–18) | 17 (17–18) | 33 (33–34) | 18 (17–18) | 15 (11–18) | 12.5 (11–13) | — (6 revert) | 71 (71–72) |
| 5 | 39 (38–39) | 39 (38–39) | 19 (19–19) | 18 (18–18) | 17 (17–18) | 34 (33–34) | 18 (18–18) | 14 (10–16) | 12.5 (10–13) | — (6 revert) | 71.5 (71–73) |
| 10 | 38 (38–39) | 38 (38–39) | 18.5 (18–19) | 18 (18–18) | 17 (17–17) | 33 (33–34) | 18 (18–18) | 12 (8–15) | 12 (8–12) | — (6 revert) | 71 (71–72) |
| 20 | 38 (38–39) | 38 (38–39) | 19 (18–19) | 18 (17–18) | 17.5 (17–18) | 34 (33–34) | 18 (17–18) | 11 (7–14) | 11 (7–11) | — (6 revert) | 71 (71–73) |
| 50 | 38 (38–39) | 38 (38–39) | 18 (18–19) | 18 (17–18) | 17 (17–17) | 33 (33–34) | 18 (17–18) | 10 (6–12) | 10 (6–11) | — (6 revert) | 71.5 (71–72) |
| 100 | 38 (38–39) | 38 (38–39) | 19 (18–19) | 18 (18–18) | 17 (17–18) | 33.5 (33–34) | 18 (18–18) | 8 (4–11) | 8 (4–11) | — (6 revert) | 71 (71–73) |
| 365 | 38 (38–40) | 38 (38–40) | 19 (19–19) | 18 (18–18) | 18 (17–18) | 33 (33–34) | 18 (18–18) | 6 (2–9) | 6 (2–9) | — (6 revert) | 71 (71–71) |
| 1000 | 38 (38–38) | 38 (38–38) | 18 (18–19) | 17.5 (17–18) | 17 (17–17) | 33 (33–34) | 17.5 (17–18) | 4 (1–7) | 4 (1–7) | — (6 revert) | 71 (71–71) |
| 10000 | 37 (37–38) | 37 (37–38) | 17.5 (17–19) | 17.5 (17–18) | 17 (17–18) | 33 (32–33) | 17 (17–18) | 1 (0–3) | 1 (0–3) | — (6 revert) | 71 (70–72) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 18 (17–18) | 17.5 (17–18) | 33.5 (33–34) | 18 (17–18) | 16 (12–19) | 13 (12–13) | — (6 revert) | 71 (71–72) |
| 2 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 18 (17–18) | 17 (17–18) | 33 (33–34) | 18 (17–18) | 15 (11–18) | 12.5 (11–13) | — (6 revert) | 71 (71–72) |
| 5 | 39 (38–39) | 39 (38–39) | 19 (19–19) | 18 (18–18) | 17 (17–18) | 34 (33–34) | 18 (18–18) | 14 (10–16) | 12.5 (10–13) | — (6 revert) | 71.5 (71–73) |
| 10 | 38 (38–39) | 38 (38–39) | 18.5 (18–19) | 18 (18–18) | 17 (17–17) | 33 (33–34) | 18 (18–18) | 12 (8–15) | 12 (8–12) | — (6 revert) | 71 (71–72) |
| 20 | 38 (38–39) | 38 (38–39) | 19 (18–19) | 18 (17–18) | 17.5 (17–18) | 34 (33–34) | 18 (17–18) | 11 (7–14) | 11 (7–11) | — (6 revert) | 71 (71–73) |
| 50 | 38 (38–39) | 38 (38–39) | 18 (18–19) | 18 (17–18) | 17 (17–17) | 33 (33–34) | 18 (17–18) | 10 (6–12) | 10 (6–11) | — (6 revert) | 71.5 (71–72) |
| 100 | 38 (38–39) | 38 (38–39) | 19 (18–19) | 18 (18–18) | 17 (17–18) | 33.5 (33–34) | 18 (18–18) | 8 (4–11) | 8 (4–11) | — (6 revert) | 71 (71–73) |
| 365 | 39 (38–40) | 39 (38–40) | 19.5 (19–20) | 18 (18–18) | 18 (17–18) | 33 (33–34) | 18 (18–18) | 6 (2–9) | 6 (2–9) | — (6 revert) | 71 (71–71) |
| 1000 | 38 (38–38) | 38 (38–38) | 19 (18–19) | 17.5 (17–18) | 17 (17–17) | 33 (33–34) | 17.5 (17–18) | 4 (1–7) | 4 (1–7) | — (6 revert) | 71 (71–71) |
| 10000 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 17.5 (17–18) | 17 (17–18) | 33 (32–33) | 17 (17–18) | 1 (0–3) | 1 (0–3) | — (6 revert) | 71 (71–72) |

## deep-tail-option: An option walking out of the money

Step: `S = S (1 - tick); then C = S N(d1) - K e^(-rT) N(d2)`. Result: the Black-Scholes call price after N down-ticks of the spot.

Options protocols price with N(d), the normal distribution function, and the spot walks. Near the money every library agrees; past d = -8 an 18-decimal N(d) is zero and the price with it, and before that e^(-d^2/2) has lost most of its digits. FP127 has normCdf as an op; the other libraries run the same series and continued fraction through their own exp, sqrt, mul and div, with pi by Ramanujan through the same ops, so each is judged on its primitives.

Inputs: **reference** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.000173 (at the money, 20% vol, six months; d1 reaches -12 at N = 10,000); **slow-walk** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.0001 (a slower walk: d1 reaches -7 at N = 10,000, where an 18-decimal N(d) has a few digits left); **fast-walk** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.0005 (a faster walk: d1 passes -12 near N = 3,500; beyond it the price is below every grid); **low-vol** spot = 100, strike = 100, sigma = 0.05, T = 0.5, r = 0.05, tick = 0.00005 (5% vol: d moves four times faster per tick); **high-vol** spot = 100, strike = 100, sigma = 0.8, T = 0.5, r = 0.05, tick = 0.0007 (80% vol: a long way to the tail); **short-dated** spot = 100, strike = 100, sigma = 0.2, T = 0.01, r = 0.05, tick = 0.00003 (ten days to expiry: sigma sqrt(T) is 0.02 and the tail comes fast)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `6.878391866103811` | 37 / 37 / 55,285 | 37 / 37 / 43,684 | 18 / 18 / 103,328 | 16 / 16 / 77,511 | 16 / 16 / 142,047 | 32 / 32 / 345,298 | 16 / 16 / 126,930 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 78,540 |
| 2 | `6.868065132714932` | 37 / 38 / 28,498 | 37 / 38 / 22,027 | 18 / 17 / 51,807 | 17 / 17 / 38,872 | 16 / 16 / 71,318 | 32 / 32 / 173,114 | 17 / 17 / 63,717 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 39,895 |
| 5 | `6.837144794797698` | 37 / 39 / 12,378 | 37 / 39 / 8,981 | 18 / 18 / 20,874 | 16 / 16 / 15,688 | 16 / 16 / 28,891 | 32 / 32 / 69,826 | 16 / 16 / 25,789 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 16,702 |
| 10 | `6.785810396029252` | 36 / 38 / 7,044 | 36 / 38 / 4,675 | 18 / 18 / 10,586 | 16 / 16 / 7,960 | 16 / 16 / 14,740 | 31 / 31 / 35,008 | 16 / 16 / 13,146 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 8,916 |
| 20 | `6.683889366360745` | 36 / 38 / 4,377 | 36 / 38 / 2,522 | 17 / 17 / 5,433 | 16 / 16 / 4,052 | 16 / 16 / 7,586 | 31 / 31 / 17,772 | 16 / 16 / 6,752 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 5,089 |
| 50 | `6.384100145151291` | 36 / 38 / 2,760 | 36 / 38 / 1,213 | 17 / 18 / 2,323 | 16 / 16 / 1,743 | 16 / 16 / 3,352 | 31 / 31 / 7,628 | 16 / 16 / 2,974 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 2,731 |
| 100 | `5.904291981569546` | 35 / 37 / 2,220 | 35 / 37 / 775 | 16 / 17 / 1,283 | 16 / 16 / 971 | 16 / 16 / 1,941 | 30 / 30 / 4,131 | 16 / 16 / 1,711 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 1,968 |
| 365 | `3.76450175108814` | 35 / 37 / 1,860 | 35 / 37 / 491 | 16 / 17 / 577 | 16 / 16 / 450 | 16 / 16 / 990 | 30 / 30 / 1,938 | 16 / 16 / 859 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 1,449 |
| 1000 | `0.9741872197637135` | 34 / 36 / 1,773 | 34 / 36 / 422 | 15 / 16 / 409 | 15 / 15 / 325 | 15 / 15 / 763 | 29 / 29 / 1,410 | 15 / 15 / 655 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 1,356 |
| 10000 | `4.263958353856216e-34` | 3 / 3 / 1,737 | 3 / 3 / 376 | 0 / 0 / 317 | 0 / 0 / 256 | 0 / 0 / 640 | 27 / 27 / 1,087 | reverts `0xd4794efd` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 1,255 |

### All inputs (6): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 (36–38) | 37 (36–38) | 18 (17–18) | 16 (16–16) | 16 (16–17) | 32 (31–32) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 70 (69–71) |
| 2 | 37 (36–38) | 37 (36–38) | 17.5 (17–18) | 16 (16–17) | 16 (16–16) | 32 (31–32) | 16 (16–17) | — (6 revert) | — (6 revert) | — (6 revert) | 70 (69–71) |
| 5 | 37 (36–38) | 37 (36–38) | 17.5 (17–18) | 16 (16–17) | 16 (16–16) | 32 (31–32) | 16 (15–17) | — (6 revert) | — (6 revert) | — (6 revert) | 70 (69–70) |
| 10 | 36 (36–38) | 36 (36–38) | 17 (17–18) | 16 (15–17) | 16 (15–16) | 31 (31–32) | 16 (15–17) | — (6 revert) | — (6 revert) | — (6 revert) | 70 (68–70) |
| 20 | 36 (35–38) | 36 (35–38) | 17 (16–17) | 16 (15–16) | 16 (16–16) | 31 (30–32) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 69 (68–71) |
| 50 | 36 (35–38) | 36 (35–38) | 16.5 (16–18) | 16 (16–16) | 16 (16–17) | 31 (30–31) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 69 (68–69) |
| 100 | 35 (35–38) | 35 (35–38) | 16 (15–19) | 16 (16–16) | 16 (16–19) | 30 (30–31) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 68 (67–69) |
| 365 | 34.5 (34–37) | 34.5 (34–37) | 15.5 (15–17) | 16 (15–16) | 16 (15–16) | 30 (29–30) | 15.5 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 68 (67–68) |
| 1000 | 34 (33–36) | 34 (33–36) | 14.5 (12–17) | 15 (11–15) | 15 (10–15) | 29 (27–30) | 15 (10–16) | — (6 revert) | — (6 revert) | — (6 revert) | 67 (66–68) |
| 10000 | 0.5 (0–25) | 0.5 (0–25) | 0 (0–6) | 0 (0–4) | 0 (0–4) | 27 (26–28) | 4 (4–4), 5 revert | — (6 revert) | — (6 revert) | — (6 revert) | 65.5 (64–66) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 (36–38) | 37 (36–38) | 18 (17–18) | 16 (16–16) | 16 (16–17) | 32 (31–32) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 70 (69–71) |
| 2 | 38 (36–38) | 38 (36–38) | 17.5 (17–18) | 16 (16–17) | 16 (16–16) | 32 (31–32) | 16 (16–17) | — (6 revert) | — (6 revert) | — (6 revert) | 70 (69–71) |
| 5 | 37.5 (37–39) | 37.5 (37–39) | 17.5 (17–18) | 16 (16–17) | 16 (16–16) | 32 (31–32) | 16 (15–17) | — (6 revert) | — (6 revert) | — (6 revert) | 70 (69–71) |
| 10 | 37.5 (37–38) | 37.5 (37–38) | 18 (16–18) | 16 (15–17) | 16 (15–16) | 31 (31–32) | 16 (15–17) | — (6 revert) | — (6 revert) | — (6 revert) | 70 (68–70) |
| 20 | 37.5 (37–38) | 37.5 (37–38) | 17.5 (16–18) | 16 (15–16) | 16 (16–16) | 31 (30–32) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 69 (68–71) |
| 50 | 37 (37–39) | 37 (37–39) | 17.5 (17–18) | 16 (16–16) | 16 (16–17) | 31 (30–31) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 69 (68–69) |
| 100 | 37 (36–38) | 37 (36–38) | 17 (17–18) | 16 (16–16) | 16 (16–19) | 30 (30–31) | 16 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 68 (67–69) |
| 365 | 37 (36–37) | 37 (36–37) | 17 (16–17) | 16 (15–16) | 16 (15–16) | 30 (29–30) | 15.5 (15–16) | — (6 revert) | — (6 revert) | — (6 revert) | 68 (67–68) |
| 1000 | 35.5 (34–37) | 35.5 (34–37) | 16 (12–17) | 15 (11–15) | 15 (10–15) | 29 (27–30) | 15 (10–16) | — (6 revert) | — (6 revert) | — (6 revert) | 67 (66–68) |
| 10000 | 0.5 (0–25) | 0.5 (0–25) | 0 (0–6) | 0 (0–4) | 0 (0–4) | 27 (26–28) | 4 (4–4), 5 revert | — (6 revert) | — (6 revert) | — (6 revert) | 65.5 (64–66) |

## decay: Decay, the share released

Step: `D = D e^(-eps); result 1 - D`. Result: the share released after N steps of decay.

Vesting, TWAP weights and exponential moving averages multiply by e^(-dt/tau) every step. The factor is a hair below one, and on an 18-decimal grid e^(-eps) rounds to a grid point whose distance from one is wrong by up to 1e-18 relative, every step: at eps = 1e-12 that is six digits of the released share, at 1e-15 three, at 1e-18 nothing is released at all.

Inputs: **reference** eps = 0.000001 (one millionth a step: a one-second step against a twelve-day time constant); **nano** eps = 0.000000001 (1e-9 a step: a one-second step against a thirty-year time constant); **pico** eps = 0.000000000001 (1e-12 a step: the factor is within WAD's last six digits of one); **femto** eps = 0.000000000000001 (1e-15 a step: three digits of the factor's distance from one survive on WAD); **atto** eps = 0.00000000000000001 (1e-17 a step: below WAD's grid, e^(-eps) is one and nothing decays)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `9.999995000001667e-7` | 32 / 33 / 9,344 | 32 / 33 / 7,578 | 13 / 13 / 4,981 | 12 / 12 / 1,824 | 12 / 12 / 4,038 | 28 / 28 / 11,056 | 12 / 12 / 2,685 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 11,260 |
| 2 | `1.999998000001333e-6` | 32 / 33 / 8,936 | 32 / 33 / 7,161 | 13 / 13 / 4,529 | 12 / 12 / 1,424 | 12 / 12 / 3,638 | 28 / 28 / 9,651 | 12 / 12 / 2,285 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 10,288 |
| 5 | `4.999987500020833e-6` | 33 / 34 / 8,692 | 33 / 34 / 6,911 | 13 / 13 / 4,258 | 12 / 12 / 1,184 | 12 / 12 / 3,398 | 28 / 28 / 8,801 | 12 / 12 / 2,045 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 9,700 |
| 10 | `9.999950000166666e-6` | 33 / 34 / 8,610 | 33 / 34 / 6,828 | 13 / 13 / 4,168 | 12 / 12 / 1,104 | 12 / 12 / 3,318 | 28 / 28 / 8,511 | 12 / 12 / 1,965 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 9,506 |
| 20 | `1.999980000133333e-5` | 33 / 33 / 8,569 | 33 / 33 / 6,786 | 13 / 13 / 4,123 | 12 / 12 / 1,064 | 12 / 12 / 3,278 | 28 / 28 / 8,372 | 12 / 12 / 1,925 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 9,409 |
| 50 | `4.999875002083307e-5` | 33 / 33 / 8,545 | 33 / 33 / 6,761 | 13 / 13 / 4,096 | 12 / 12 / 1,040 | 12 / 12 / 3,254 | 28 / 28 / 8,289 | 12 / 12 / 1,901 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 9,350 |
| 100 | `9.99950001666625e-5` | 33 / 33 / 8,537 | 33 / 33 / 6,753 | 13 / 13 / 4,087 | 12 / 12 / 1,032 | 12 / 12 / 3,246 | 28 / 28 / 8,261 | 12 / 12 / 1,893 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 9,330 |
| 365 | `0.0003649333956037813` | 33 / 33 / 8,534 | 33 / 33 / 6,747 | 13 / 13 / 4,080 | 11 / 11 / 1,026 | 12 / 12 / 3,240 | 28 / 28 / 8,240 | 11 / 11 / 1,887 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 9,316 |
| 1000 | `0.0009995001666250083` | 33 / 33 / 8,537 | 33 / 33 / 6,745 | 13 / 13 / 4,078 | 11 / 11 / 1,024 | 12 / 12 / 3,238 | 28 / 28 / 8,235 | 11 / 11 / 1,885 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 9,312 |
| 10000 | `0.009950166250831946` | 33 / 33 / 8,607 | 33 / 33 / 6,745 | 13 / 13 / 4,078 | 11 / 11 / 1,024 | 12 / 12 / 3,238 | 28 / 28 / 8,233 | 11 / 11 / 1,885 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 9,311 |

### All inputs (5): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 26 (21–32) | 26 (21–32) | 7 (2–13) | 12 (9–17) | 6 (1–12) | 22 (17–28) | 12 (9–17) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 2 | 26 (21–32) | 26 (21–32) | 7 (2–13) | 12 (9–16) | 6 (1–18) | 22 (17–28) | 12 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 5 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (8–16) | 6 (1–12) | 22 (17–28) | 12 (8–16) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 10 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (8–16) | 6 (1–12) | 22 (16–28) | 12 (8–16) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 20 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 50 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 100 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 365 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 11 (8–14) | 6 (1–12) | 22 (16–28) | 11 (8–14) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 1000 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 11 (8–14) | 6 (1–12) | 22 (16–28) | 11 (8–14) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 10000 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 11 (8–13) | 6 (1–12) | 21 (16–28) | 11 (8–13) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–17) | 6 (1–12) | 22 (17–28) | 12 (9–17) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 2 | 26 (22–33) | 26 (22–33) | 7 (2–13) | 12 (9–16) | 6 (1–18) | 22 (17–28) | 12 (9–16) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 5 | 27 (21–34) | 27 (21–34) | 7 (2–13) | 12 (8–16) | 6 (1–12) | 22 (17–28) | 12 (8–16) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 10 | 27 (21–34) | 27 (21–34) | 7 (2–13) | 12 (8–16) | 6 (1–12) | 22 (16–28) | 12 (8–16) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 20 | 27 (21–33) | 27 (21–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 50 | 28 (21–33) | 28 (21–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 100 | 28 (21–33) | 28 (21–33) | 7 (2–13) | 12 (8–15) | 6 (1–12) | 22 (16–28) | 12 (8–15) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 365 | 29 (21–33) | 29 (21–33) | 7 (2–13) | 11 (8–14) | 6 (1–12) | 22 (16–28) | 11 (8–14) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 1000 | 28 (21–33) | 28 (21–33) | 7 (2–13) | 11 (8–14) | 6 (1–12) | 22 (16–28) | 11 (8–14) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |
| 10000 | 28 (21–33) | 28 (21–33) | 7 (2–13) | 11 (8–13) | 6 (1–12) | 21 (16–28) | 11 (8–13) | — (5 revert) | — (5 revert) | — (5 revert) | 59 (54–66) |

## Methodology

**truth.** For every scenario, input and N the same loop is run in exact real arithmetic with mpmath at 300 decimal digits (scripts/ladder/ladder.py), from the exact rational parameters in scenarios.json. Closed forms are used where the loop has one (compounding, the cumulative product, the geometric mean, the round trip, per-second and continuous accrual, the option walk and the decay); the bonding curve, the amortising loan and the Black-Scholes chain are stepped.

**rounding.** Each library receives the parameters floored into its own representation (2^-128, 2^-64, 10^-18 or 10^-27 units, or the nearest float for ABDKMathQuad and FP256; scripts/ladder/inputs.json). truthFormat is the exact loop started from those floored parameters, so digitsFormat measures the library's arithmetic alone, while digits measures what a protocol sees: the format's rounding of the inputs plus the arithmetic.

**digits.** digits = floor(-log10 |v - t| / |t|), the number of correct leading significant digits by relative error, capped at 100, which is reported as exact. It is not a string comparison: a value can be correct to 36 digits while its 37th printed digit happens to agree with the truth, or while a carry makes the printed prefix differ earlier.

**agree.** agree is the count of leading significant digits of the printed value (42 significant digits) that are literally equal to the printed truth. The demo page colours the rest of the value with it. It is a reading aid, not a measurement: a carry across 0.999… / 1.000… gives 0.

**gas.** gasTotal is measured inside the adapter around the scenario function (the parameter reads and the loop), after the runner has warmed the adapter and the FP127 object, so the call into the adapter and the ABI decoding are excluded. The FP127 (deployed) form includes one staticcall per op; FP127Lib and the other libraries are internal calls. Aave, Morpho and Maker answer only the accrual scenarios their models describe and report Unsupported elsewhere, which the tables show as a revert. gasPerStep = gasTotal / N. Reverted cells carry no gas.

**live.** LadderRunner.run(scenario, form, n, p) on Sepolia executes any cell with one eth_call and returns (ok, raw, reason, gasPerStep, gasTotal). scripts/ladder/livecap.py sends every cell's floored parameters p and compares the returned raw word with the committed one bit for bit (or the revert selector for a reverted cell). liveMaxN is the largest N per form the public RPC completed within its gas limit, measured by scripts/ladder/livecap.py.

**reproduce.** make ladder regenerates ladder.json and ladder.md from the Foundry harness (test/ladder/Ladder.t.sol) and this script; make ladder-check fails CI when the committed dataset differs. Versions of every library and of forge are recorded in the dataset.

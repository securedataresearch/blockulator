# Terminal precision ladder

Generated 2026-10-22 by `make ladder`. Versions: fp127 cf03224, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, forge forge Version: 1.7.1.

Each scenario is run for several inputs; the first table is the reference input in full (`digits / digitsFormat / gas per step`, where digits is against the exact truth and digitsFormat against the truth from the parameters as the library received them), the second is the summary over all inputs (`median (min–max)` digits, capped at 40). Full values, both truths, signed errors and raw words are in ladder.json; the method is in the Methodology section at the end.

## compound: Daily compound interest

Step: `b = b * (1 + r)`. Result: balance after N days.

Per-block or per-day accrual in every lending protocol: one mul per step, N steps.

Inputs: **reference** principal = 10000, rate = 0.1/365 ($10,000 at 10% APR, the headline cell); **tiny-low** principal = 1, rate = 0.01/365 (one unit at 1%: the integer part is small, the fraction carries everything); **tiny-high** principal = 1, rate = 0.5/365 (one unit at 50%); **mid-1pct** principal = 10000, rate = 0.01/365 (a slow rate: the per-step factor is close to 1); **mid-5pct** principal = 10000, rate = 0.05/365 (a typical lending rate); **mid-50pct** principal = 10000, rate = 0.5/365 (a high rate: the balance grows 150x by N = 10,000); **large** principal = 1000000, rate = 0.1/365 (a million-unit position); **huge** principal = 100000000, rate = 0.1/365 (a hundred-million-unit pool); **huge-high** principal = 100000000, rate = 0.5/365 (the largest balance the ladder reaches, near 10^14); **fraction** principal = 0.001, rate = 0.1/365 (a sub-unit balance: leading zeros in WAD)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb | quad | balancer | aave | morpho | maker | fp256 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `10002.7397260274` | 38 / exact / 1,430 | 38 / exact / 900 | 19 / exact / 932 | 19 / exact / 744 | 19 / exact / 1,103 | 33 / 33 / 2,930 | 19 / exact / 1,013 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 27 / exact / 610 | 71 / 71 / 1,669 |
| 2 | `10005.48020266467` | 38 / 42 / 1,167 | 38 / 42 / 635 | 19 / 23 / 609 | 19 / 22 / 488 | 19 / 22 / 847 | 33 / 33 / 1,972 | 19 / 22 / 757 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 27 / 420 | 71 / 71 / 1,145 |
| 5 | `10013.70613829244` | 38 / 42 / 1,009 | 38 / 42 / 476 | 19 / 23 / 415 | 18 / 21 / 335 | 18 / 21 / 694 | 33 / 33 / 1,398 | 18 / 21 / 604 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 197 | 70 / 70 / 830 |
| 10 | `10027.43106240757` | 37 / 41 / 956 | 37 / 41 / 423 | 18 / 22 / 350 | 18 / 21 / 284 | 18 / 21 / 643 | 32 / 32 / 1,206 | 18 / 21 / 553 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 121 | 70 / 70 / 725 |
| 20 | `10054.93737113361` | 37 / 41 / 930 | 37 / 41 / 396 | 18 / 22 / 318 | 18 / 21 / 258 | 18 / 21 / 617 | 32 / 32 / 1,110 | 18 / 21 / 527 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 26 / 26 / 68 | 70 / 70 / 673 |
| 50 | `10137.90984214166` | 37 / 41 / 914 | 37 / 41 / 380 | 18 / 21 / 298 | 17 / 20 / 243 | 17 / 20 / 602 | 32 / 32 / 1,053 | 17 / 20 / 512 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 25 / 26 / 31 | 69 / 69 / 641 |
| 100 | `10277.72159673926` | 36 / 40 / 909 | 36 / 40 / 375 | 17 / 21 / 292 | 17 / 20 / 238 | 17 / 20 / 597 | 31 / 31 / 1,034 | 17 / 20 / 507 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 25 / 25 / 17 | 69 / 69 / 631 |
| 365 | `11051.55781616264` | 36 / 40 / 906 | 36 / 40 / 371 | 17 / 21 / 287 | 16 / 19 / 234 | 16 / 19 / 593 | 31 / 31 / 1,020 | 16 / 19 / 503 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 24 / 25 / 6 | 68 / 68 / 623 |
| 1000 | `13151.29420081218` | 35 / 39 / 906 | 35 / 39 / 370 | 16 / 20 / 286 | 16 / 19 / 233 | 16 / 19 / 592 | 30 / 30 / 1,016 | 16 / 19 / 502 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 24 / 24 / 2 | 68 / 68 / 622 |
| 10000 | `154769.3406914411` | 34 / 39 / 923 | 34 / 39 / 370 | 15 / 20 / 286 | 15 / 18 / 233 | 15 / 18 / 592 | 29 / 29 / 1,015 | 15 / 18 / 502 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 23 / 23 / 0 | 67 / 67 / 621 |

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
| 1 | `10002.7397260274` | 38 / exact / 2,234 | 38 / exact / 1,146 | 19 / 19 / 11,494 | 17 / 18 / 2,153 | 19 / exact / 1,435 | 33 / 33 / 28,817 | 17 / 18 / 3,093 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,584 |
| 2 | `10005.48020266467` | 38 / 38 / 1,237 | 38 / 38 / 699 | 18 / 18 / 5,747 | 17 / 18 / 1,076 | 16 / 16 / 5,365 | 33 / 33 / 14,411 | 17 / 18 / 1,546 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 1,541 |
| 5 | `10013.70613829244` | 38 / 38 / 1,004 | 38 / 38 / 800 | 18 / 18 / 2,282 | 17 / 17 / 430 | 16 / 16 / 2,118 | 33 / 33 / 5,727 | 17 / 18 / 618 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,731 |
| 10 | `10027.43106240757` | 37 / 39 / 502 | 37 / 39 / 400 | 18 / 18 / 1,141 | 17 / 17 / 215 | 16 / 16 / 1,060 | 33 / 33 / 2,864 | 18 / 18 / 309 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 872 |
| 20 | `10054.93737113361` | 37 / 39 / 251 | 37 / 39 / 200 | 17 / 18 / 570 | 17 / 17 / 107 | 15 / 15 / 530 | 33 / 33 / 1,431 | 17 / 18 / 154 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 436 |
| 50 | `10137.90984214166` | 37 / 38 / 100 | 37 / 38 / 80 | 17 / 17 / 230 | 16 / 16 / 43 | 15 / 15 / 217 | 32 / 32 / 573 | 17 / 18 / 61 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 174 |
| 100 | `10277.72159673926` | 36 / 39 / 50 | 36 / 39 / 40 | 17 / 17 / 115 | 16 / 16 / 21 | 15 / 15 / 109 | 32 / 32 / 286 | 17 / 17 / 30 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 87 |
| 365 | `11051.55781616264` | 36 / 39 / 13 | 36 / 39 / 11 | 16 / 16 / 31 | 15 / 15 / 5 | 14 / 14 / 29 | 31 / 31 / 78 | 16 / 18 / 8 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 24 |
| 1000 | `13151.29420081218` | 35 / 39 / 5 | 35 / 39 / 4 | 16 / 16 / 11 | 15 / 15 / 2 | 14 / 14 / 10 | 31 / 31 / 28 | 16 / 18 / 3 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 8 |
| 10000 | `154769.3406914411` | 34 / 40 / 1 | 34 / 40 / 1 | 15 / 15 / 1 | 14 / 14 / 0 | 13 / 13 / 1 | 30 / 30 / 2 | 15 / 17 / 0 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 67 / 67 / 0 |

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
| 1 | `31.62277660168379` | 41 / 41 / 2,252 | 41 / 41 / 1,911 | 20 / 20 / 1,810 | 19 / 19 / 1,260 | 19 / 19 / 1,752 | 34 / 34 / 3,231 | 18 / 18 / 3,204 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 3,197 |
| 2 | `63.26136064079654` | 40 / 40 / 2,038 | 40 / 40 / 1,700 | 21 / 21 / 1,572 | 19 / 19 / 1,049 | 19 / 19 / 1,545 | 33 / 33 / 3,116 | 18 / 18 / 2,993 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,949 |
| 5 | `158.2718785032213` | 40 / 40 / 1,909 | 40 / 40 / 1,573 | 21 / 21 / 1,422 | 19 / 19 / 922 | 19 / 19 / 1,419 | 33 / 33 / 3,023 | 18 / 18 / 2,866 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,790 |
| 10 | `316.9381559123806` | 40 / 40 / 1,866 | 40 / 40 / 1,531 | 21 / 21 / 1,375 | 19 / 19 / 880 | 19 / 19 / 1,375 | 33 / 33 / 2,985 | 18 / 18 / 2,824 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 72 / 72 / 2,740 |
| 20 | `635.4500029402082` | 40 / 40 / 1,845 | 40 / 40 / 1,510 | 21 / 21 / 1,350 | 19 / 19 / 859 | 19 / 19 / 1,354 | 33 / 33 / 2,964 | 18 / 18 / 2,803 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,712 |
| 50 | `1600.350881438697` | 40 / 40 / 1,832 | 40 / 40 / 1,497 | 21 / 21 / 1,338 | 19 / 19 / 846 | 19 / 19 / 1,342 | 32 / 32 / 2,952 | 18 / 18 / 2,801 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,697 |
| 100 | `3239.292264514382` | 40 / 40 / 1,828 | 40 / 40 / 1,493 | 21 / 21 / 1,335 | 19 / 19 / 842 | 19 / 19 / 1,338 | 32 / 32 / 2,947 | 17 / 17 / 2,804 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 2,691 |
| 365 | `12536.2620049473` | 40 / 40 / 1,825 | 40 / 40 / 1,490 | 21 / 21 / 1,333 | 19 / 19 / 839 | 19 / 19 / 1,335 | 31 / 31 / 2,943 | 18 / 18 / 2,762 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,688 |
| 1000 | `38540.07865481035` | 40 / 40 / 1,826 | 40 / 40 / 1,489 | 21 / 21 / 1,332 | 19 / 19 / 838 | 19 / 19 / 1,345 | 31 / 31 / 2,942 | 18 / 18 / 2,778 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 2,686 |
| 10000 | `748008.0076158747` | 40 / 40 / 1,843 | 40 / 40 / 1,489 | 21 / 21 / 1,344 | 20 / 20 / 838 | 20 / 20 / 1,354 | 30 / 30 / 2,941 | 18 / 18 / 2,701 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 2,685 |

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
| 1 | `1.5` | 38 / 38 / 8,266 | 38 / 38 / 7,990 | 19 / 19 / 10,889 | exact / exact / 1,441 | 16 / 16 / 10,093 | 33 / 33 / 23,586 | 17 / 17 / 2,616 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,629 |
| 2 | `1.5` | 38 / 38 / 8,094 | 38 / 38 / 7,853 | 18 / 18 / 10,695 | exact / exact / 1,272 | 16 / 16 / 9,902 | 33 / 33 / 23,375 | 17 / 17 / 2,447 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,460 |
| 5 | `1.5` | 38 / 38 / 7,991 | 38 / 38 / 7,771 | 18 / 18 / 10,576 | exact / exact / 1,170 | 16 / 16 / 9,772 | 32 / 32 / 23,252 | 17 / 17 / 2,345 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,358 |
| 10 | `1.5` | 38 / 38 / 7,957 | 38 / 38 / 7,744 | 18 / 18 / 10,536 | exact / exact / 1,136 | 15 / 15 / 9,794 | 32 / 32 / 23,223 | 16 / 16 / 2,311 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,324 |
| 20 | `1.5` | 38 / 38 / 7,940 | 38 / 38 / 7,730 | 17 / 17 / 10,519 | exact / exact / 1,119 | 15 / 15 / 9,801 | 32 / 32 / 23,211 | 16 / 16 / 2,294 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,307 |
| 50 | `1.5` | 38 / 38 / 7,930 | 38 / 38 / 7,722 | 17 / 17 / 10,504 | exact / exact / 1,109 | 15 / 15 / 9,789 | 31 / 31 / 23,192 | 16 / 16 / 2,284 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,297 |
| 100 | `1.5` | 38 / 38 / 7,927 | 38 / 38 / 7,719 | 17 / 17 / 10,500 | exact / exact / 1,106 | 14 / 14 / 9,773 | 31 / 31 / 23,189 | 15 / 15 / 2,281 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,294 |
| 365 | `1.5` | 38 / 38 / 7,926 | 38 / 38 / 7,717 | 16 / 16 / 10,486 | exact / exact / 1,103 | 14 / 14 / 9,778 | 31 / 31 / 23,181 | 15 / 15 / 2,278 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,291 |
| 1000 | `1.5` | 38 / 38 / 7,931 | 38 / 38 / 7,717 | 16 / 16 / 10,493 | exact / exact / 1,103 | 13 / 13 / 9,761 | 30 / 30 / 23,187 | 14 / 14 / 2,278 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,291 |
| 10000 | `1.5` | 38 / 38 / 8,001 | 38 / 38 / 7,717 | 15 / 15 / 10,498 | exact / exact / 1,103 | 12 / 12 / 9,758 | 29 / 29 / 23,224 | 13 / 13 / 2,278 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 7,291 |

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
| 1 | `299200.6479903559` | 39 / exact / 1,833 | 39 / exact / 1,330 | 20 / exact / 1,431 | 19 / exact / 1,147 | 19 / exact / 1,506 | 33 / 33 / 4,713 | 19 / exact / 1,416 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,700 |
| 2 | `298401.1864804365` | 38 / 44 / 1,445 | 38 / 44 / 940 | 19 / 25 / 965 | 19 / 23 / 766 | 19 / 23 / 1,125 | 33 / 33 / 3,601 | 19 / 23 / 1,035 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,051 |
| 5 | `296002.1447990159` | 38 / 43 / 1,212 | 38 / 43 / 706 | 19 / 24 / 686 | 19 / 23 / 538 | 19 / 23 / 897 | 32 / 32 / 2,934 | 19 / 23 / 807 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,661 |
| 10 | `292001.5505907346` | 38 / 43 / 1,134 | 38 / 43 / 628 | 19 / 24 / 593 | 18 / 22 / 462 | 18 / 22 / 821 | 32 / 32 / 2,712 | 18 / 22 / 731 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,531 |
| 20 | `283992.1376448092` | 37 / 42 / 1,095 | 37 / 42 / 589 | 18 / 23 / 546 | 18 / 22 / 424 | 18 / 22 / 783 | 32 / 32 / 2,601 | 18 / 22 / 693 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 1,466 |
| 50 | `259897.9672060033` | 37 / 42 / 1,072 | 37 / 42 / 565 | 18 / 23 / 518 | 18 / 22 / 401 | 18 / 22 / 760 | 31 / 31 / 2,534 | 18 / 22 / 670 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 1,427 |
| 100 | `219520.3390882176` | 37 / 42 / 1,064 | 37 / 42 / 557 | 17 / 22 / 509 | 17 / 21 / 393 | 17 / 21 / 752 | 31 / 31 / 2,512 | 17 / 21 / 662 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 1,414 |
| 365 | `840.3327859747961` | 34 / 39 / 1,059 | 34 / 39 / 552 | 15 / 19 / 502 | 15 / 18 / 388 | 15 / 18 / 747 | 28 / 28 / 2,495 | 15 / 18 / 657 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 1,405 |
| 1000 | `-556627.3884008416` | 36 / 41 / 1,059 | 36 / 41 / 550 | 17 / 22 / 500 | 17 / 21 / 386 | 17 / 21 / 752 | 31 / 31 / 2,191 | 17 / 21 / 724 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 1,344 |
| 10000 | `-16823263.35321035` | 35 / 41 / 1,076 | 35 / 41 / 550 | 16 / 22 / 500 | 16 / 21 / 386 | 16 / 21 / 755 | 29 / 29 / 2,032 | 16 / 21 / 759 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 1,311 |

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
| 1 | `1.5` | 38 / 38 / 10,729 | 38 / 38 / 9,476 | 19 / 19 / 12,139 | exact / exact / 2,575 | 16 / 16 / 12,059 | 33 / 33 / 28,414 | 17 / 17 / 4,348 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 11,600 |
| 2 | `1.414213562373095` | 38 / 38 / 7,482 | 38 / 38 / 6,466 | 18 / 18 / 10,315 | 17 / 17 / 2,037 | 16 / 16 / 10,376 | 33 / 33 / 25,233 | 17 / 17 / 3,351 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 9,175 |
| 5 | `1.284735157123439` | 38 / 38 / 5,115 | 38 / 38 / 4,236 | 19 / 19 / 8,882 | 17 / 17 / 1,715 | 16 / 16 / 9,061 | 33 / 33 / 22,604 | 17 / 17 / 2,758 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 7,683 |
| 10 | `1.196231198851315` | 38 / 38 / 4,653 | 38 / 38 / 3,812 | 18 / 18 / 8,496 | 17 / 17 / 1,607 | 16 / 16 / 8,680 | 33 / 33 / 21,914 | 17 / 17 / 2,526 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 7,190 |
| 20 | `1.127378204157833` | 38 / 38 / 4,262 | 38 / 38 / 3,437 | 18 / 18 / 8,301 | 17 / 17 / 1,553 | 16 / 16 / 8,532 | 33 / 33 / 21,647 | 17 / 17 / 2,313 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 72 / 72 / 6,943 |
| 50 | `1.067331844248559` | 38 / 38 / 4,043 | 38 / 38 / 3,226 | 18 / 18 / 8,177 | 17 / 17 / 1,521 | 16 / 16 / 8,370 | 33 / 33 / 21,571 | 17 / 17 / 2,186 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 6,795 |
| 100 | `1.04010144984871` | 39 / 39 / 3,969 | 39 / 39 / 3,151 | 18 / 18 / 8,140 | 17 / 17 / 1,510 | 16 / 16 / 8,312 | 33 / 33 / 21,631 | 17 / 17 / 2,143 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 6,742 |
| 365 | `1.01438248702624` | 38 / 38 / 3,928 | 38 / 38 / 3,094 | 18 / 18 / 8,110 | 17 / 17 / 1,502 | 16 / 16 / 8,252 | 33 / 33 / 21,823 | 17 / 17 / 2,112 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 6,588 |
| 1000 | `1.006235969300459` | 39 / 39 / 3,919 | 39 / 39 / 3,073 | 18 / 18 / 8,103 | 17 / 17 / 1,501 | 16 / 16 / 8,235 | 33 / 33 / 22,004 | 17 / 17 / 2,105 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 72 / 72 / 6,419 |
| 10000 | `1.00085210215008` | 38 / 38 / 3,982 | 38 / 38 / 3,062 | 18 / 18 / 8,100 | 17 / 17 / 1,500 | 16 / 16 / 8,182 | 33 / 33 / 22,484 | 17 / 17 / 2,101 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 6,342 |

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
| 1 | `0.2474873734152916` | 37 / 37 / 9,033 | 37 / 37 / 5,008 | 18 / 18 / 11,754 | 17 / 17 / 3,820 | 17 / 17 / 6,991 | 34 / 34 / 13,154 | 17 / 17 / 7,693 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 10,204 |
| 2 | `0.4956818182587876` | 37 / 37 / 7,932 | 37 / 37 / 4,773 | 17 / 17 / 10,628 | 18 / 18 / 2,920 | 16 / 16 / 8,431 | 32 / 32 / 19,638 | 17 / 17 / 6,374 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 9,747 |
| 5 | `1.244506874463792` | 37 / 37 / 7,272 | 37 / 37 / 4,632 | 17 / 17 / 9,953 | 17 / 17 / 2,380 | 15 / 15 / 9,427 | 32 / 32 / 23,375 | 16 / 16 / 5,583 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 9,460 |
| 10 | `2.506683467804941` | 36 / 37 / 7,052 | 36 / 37 / 4,585 | 17 / 17 / 9,728 | 17 / 17 / 2,200 | 15 / 15 / 9,730 | 31 / 31 / 24,510 | 16 / 16 / 5,319 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 9,364 |
| 20 | `5.084010514032979` | 36 / 37 / 6,943 | 36 / 37 / 4,561 | 17 / 17 / 9,615 | 17 / 17 / 2,110 | 15 / 15 / 9,901 | 31 / 31 / 25,006 | 16 / 16 / 5,187 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 9,315 |
| 50 | `13.23914876467473` | 36 / 37 / 6,879 | 36 / 37 / 4,550 | 17 / 17 / 9,548 | 17 / 17 / 2,056 | 15 / 15 / 10,049 | 31 / 31 / 25,202 | 16 / 16 / 5,108 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 9,355 |
| 100 | `28.23736439326609` | 36 / 37 / 6,862 | 36 / 37 / 4,553 | 17 / 17 / 9,525 | 17 / 17 / 2,038 | 15 / 15 / 10,095 | 30 / 30 / 25,187 | 16 / 16 / 5,082 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 9,489 |
| 365 | `136.7454508837998` | 36 / 37 / 6,859 | 36 / 37 / 4,566 | 17 / 17 / 9,509 | 17 / 17 / 2,024 | 15 / 15 / 10,132 | 30 / 30 / 25,027 | 16 / 16 / 5,063 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 9,597 |
| 1000 | `589.4747739528645` | 36 / 37 / 6,887 | 36 / 37 / 4,572 | 17 / 18 / 9,505 | 18 / 18 / 2,021 | 15 / 15 / 10,168 | 30 / 30 / 24,823 | 17 / 17 / 5,058 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 9,614 |
| 10000 | `29787.55928753143` | 36 / 39 / 7,329 | 36 / 39 / 4,595 | 18 / 19 / 9,503 | 17 / 17 / 2,020 | 16 / 16 / 10,220 | 30 / 30 / 24,408 | 17 / 17 / 5,305 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 67 / 67 / 9,642 |

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
| 1 | `1.0001` | 39 / exact / 1,921 | 39 / exact / 1,418 | 20 / exact / 1,484 | exact / exact / 1,229 | exact / exact / 1,588 | 35 / 35 / 5,682 | exact / exact / 1,498 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,788 |
| 2 | `0.99999999` | 39 / 39 / 1,465 | 39 / 39 / 947 | 19 / 19 / 938 | exact / exact / 784 | exact / exact / 1,143 | 33 / 33 / 3,401 | exact / exact / 1,053 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 1,757 |
| 5 | `1.000099979998` | 38 / 38 / 1,192 | 38 / 38 / 664 | 18 / 18 / 610 | 20 / 20 / 517 | 20 / 20 / 876 | 33 / 33 / 2,016 | 20 / 20 / 786 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 1,139 |
| 10 | `0.999999950000001` | 37 / 37 / 1,101 | 37 / 37 / 570 | 18 / 18 / 501 | 17 / 17 / 428 | 17 / 17 / 787 | 32 / 32 / 1,560 | 17 / 17 / 697 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 72 / 72 / 933 |
| 20 | `0.9999999000000045` | 37 / 37 / 1,056 | 37 / 37 / 523 | 18 / 18 / 447 | 17 / 17 / 383 | 17 / 17 / 742 | 32 / 32 / 1,330 | 17 / 17 / 652 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 830 |
| 50 | `0.99999975000003` | 37 / 37 / 1,028 | 37 / 37 / 495 | 17 / 17 / 414 | 16 / 16 / 357 | 16 / 16 / 716 | 32 / 32 / 1,192 | 16 / 16 / 626 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 768 |
| 100 | `0.9999995000001225` | 36 / 36 / 1,019 | 36 / 36 / 485 | 17 / 17 / 403 | 16 / 16 / 348 | 16 / 16 / 707 | 31 / 31 / 1,146 | 16 / 16 / 617 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 748 |
| 365 | `1.000098179819647` | 36 / 36 / 1,013 | 36 / 36 / 479 | 16 / 16 / 395 | 15 / 15 / 341 | 15 / 15 / 700 | 31 / 31 / 1,113 | 15 / 15 / 610 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 733 |
| 1000 | `0.999995000012475` | 35 / 35 / 1,013 | 35 / 35 / 477 | 16 / 16 / 393 | 15 / 15 / 340 | 15 / 15 / 699 | 30 / 30 / 1,105 | 15 / 15 / 609 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 729 |
| 10000 | `0.9999500012497292` | 34 / 34 / 1,030 | 34 / 34 / 476 | 15 / 15 / 392 | 14 / 14 / 339 | 14 / 14 / 698 | 29 / 29 / 1,100 | 14 / 14 / 608 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 727 |

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
| 1 | `11000.0` | 38 / exact / 1,685 | 38 / exact / 1,155 | 19 / exact / 1,187 | exact / exact / 999 | exact / exact / 1,358 | 33 / 33 / 3,185 | exact / exact / 1,268 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 610 | exact / 72 / 1,924 |
| 2 | `12100.0` | 38 / 77 / 1,294 | 38 / 77 / 762 | 19 / 39 / 736 | exact / exact / 616 | exact / exact / 975 | 33 / 33 / 2,100 | exact / exact / 885 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 420 | 71 / 71 / 1,272 |
| 5 | `16105.1` | 38 / 42 / 1,060 | 38 / 42 / 527 | 18 / 23 / 466 | exact / exact / 386 | exact / exact / 745 | 33 / 33 / 1,449 | exact / exact / 655 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 197 | 70 / 70 / 881 |
| 10 | `25937.424601` | 37 / 42 / 982 | 37 / 42 / 448 | 18 / 23 / 376 | exact / exact / 309 | exact / exact / 668 | 32 / 32 / 1,227 | exact / exact / 578 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 121 | 70 / 70 / 751 |
| 20 | `67274.999493256` | 37 / 42 / 943 | 37 / 42 / 409 | 18 / 22 / 331 | exact / exact / 271 | exact / exact / 630 | 32 / 32 / 1,117 | exact / exact / 540 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | exact / exact / 68 | 70 / 70 / 686 |
| 50 | `1173908.528796953` | 37 / 41 / 919 | 37 / 41 / 385 | 17 / 22 / 304 | 22 / 22 / 248 | 22 / 22 / 607 | 32 / 32 / 1,052 | 22 / 22 / 517 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 29 / 29 / 31 | 69 / 69 / 647 |
| 100 | `137806123.3982227` | 36 / 41 / 912 | 36 / 41 / 377 | 17 / 22 / 295 | 22 / 22 / 240 | 22 / 22 / 599 | 31 / 31 / 1,030 | 22 / 22 / 509 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 29 / 29 / 17 | 69 / 69 / 634 |
| 365 | `1.283305580313353e+19` | 36 / 41 / 906 | 36 / 41 / 372 | reverts `0x00000000` | 22 / 22 / 235 | 22 / 22 / 594 | 31 / 31 / 1,015 | 22 / 22 / 504 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 28 / 28 / 6 | 68 / 68 / 624 |
| 1000 | `2.469932918005826e+45` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | 22 / 22 / 601 | 30 / 30 / 1,011 | reverts `0x4e487b71` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x49f7642b` | 68 / 68 / 622 |
| 10000 | `8.449900251200348e+417` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | reverts `0x120b5b43` | 29 / 29 / 1,009 | reverts `0x4e487b71` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x49f7642b` | 67 / 67 / 621 |

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
| 1 | `10001.36995684313` | 33 / 39 / 8,006 | 33 / 39 / 7,271 | 14 / 14 / 11,904 | 13 / 13 / 2,517 | 12 / 12 / 10,843 | 28 / 28 / 31,498 | 13 / 17 / 3,461 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 22 / 22 / 3,471 | 66 / 66 / 9,007 |
| 2 | `10002.74010136444` | 33 / 38 / 4,128 | 33 / 38 / 3,769 | 13 / 14 / 5,959 | 12 / 12 / 1,258 | 11 / 11 / 5,428 | 28 / 28 / 15,751 | 13 / 17 / 1,730 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 22 / 22 / 1,809 | 66 / 66 / 4,509 |
| 5 | `10006.85166125453` | 33 / 39 / 1,821 | 33 / 39 / 1,681 | 13 / 13 / 2,369 | 12 / 12 / 503 | 11 / 11 / 2,151 | 28 / 28 / 6,278 | 13 / 18 / 692 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 803 | 65 / 65 / 1,801 |
| 10 | `10013.70801703526` | 32 / 39 / 935 | 32 / 39 / 867 | 13 / 13 / 1,184 | 12 / 12 / 251 | 11 / 11 / 1,077 | 27 / 27 / 3,139 | 12 / 18 / 346 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 416 | 65 / 65 / 900 |
| 20 | `10027.43482504363` | 32 / 38 / 480 | 32 / 38 / 447 | 12 / 13 / 593 | 11 / 11 / 125 | 10 / 10 / 549 | 27 / 27 / 1,569 | 12 / 18 / 173 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 21 / 21 / 215 | 65 / 65 / 454 |
| 50 | `10068.72825267094` | 32 / 39 / 202 | 32 / 39 / 189 | 12 / 12 / 238 | 11 / 11 / 50 | 10 / 10 / 221 | 27 / 27 / 632 | 12 / 18 / 69 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 20 / 20 / 92 | 64 / 64 / 181 |
| 100 | `10137.92886261339` | 31 / 39 / 103 | 31 / 39 / 97 | 12 / 12 / 119 | 11 / 11 / 25 | 10 / 10 / 110 | 26 / 26 / 316 | 11 / 18 / 34 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 20 / 20 / 47 | 64 / 64 / 91 |
| 365 | `10512.71096334355` | 31 / 39 / 30 | 31 / 39 / 28 | 11 / 11 / 32 | 10 / 10 / 6 | 9 / 9 / 30 | 26 / 26 / 86 | 11 / 18 / 9 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 19 / 20 / 13 | 63 / 63 / 25 |
| 1000 | `11468.12438528825` | 30 / 38 / 11 | 30 / 38 / 10 | 11 / 11 / 11 | 10 / 10 / 2 | 9 / 9 / 11 | 25 / 25 / 31 | 10 / 18 / 3 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 19 / 19 / 5 | 63 / 63 / 9 |
| 10000 | `39348.11638983319` | 29 / 40 / 1 | 29 / 40 / 1 | 10 / 10 / 1 | 9 / 9 / 0 | 8 / 8 / 1 | 24 / 24 / 3 | 9 / 18 / 0 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 18 / 18 / 0 | 62 / 62 / 0 |

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
| 1 | `10001.36995684422` | 38 / 38 / 7,472 | 38 / 38 / 6,114 | 19 / 19 / 5,079 | 18 / 18 / 2,062 | 18 / 18 / 5,111 | 33 / 33 / 11,221 | 18 / 18 / 3,447 | 16 / 16 / 1,608 | 13 / 13 / 1,442 | reverts `0x7bb9ae15` | 71 / 71 / 6,685 |
| 2 | `10002.74010136661` | 38 / 38 / 3,876 | 38 / 38 / 3,221 | 19 / 19 / 2,539 | 18 / 18 / 1,031 | 17 / 17 / 2,562 | 33 / 33 / 5,613 | 18 / 18 / 1,723 | 15 / 15 / 804 | 13 / 13 / 721 | reverts `0x7bb9ae15` | 72 / 72 / 3,348 |
| 5 | `10006.85166125997` | 39 / 39 / 1,566 | 39 / 39 / 1,293 | 19 / 19 / 1,010 | 18 / 18 / 412 | 17 / 17 / 1,025 | 34 / 34 / 2,233 | 18 / 18 / 689 | 14 / 14 / 321 | 13 / 13 / 288 | reverts `0x7bb9ae15` | 73 / 73 / 1,337 |
| 10 | `10013.70801704614` | 38 / 38 / 846 | 38 / 38 / 713 | 18 / 18 / 506 | 18 / 18 / 206 | 17 / 17 / 515 | 33 / 33 / 1,117 | 18 / 18 / 344 | 12 / 12 / 160 | 12 / 12 / 144 | reverts `0x7bb9ae15` | 72 / 72 / 669 |
| 20 | `10027.43482506541` | 38 / 38 / 408 | 38 / 38 / 341 | 19 / 19 / 253 | 18 / 18 / 103 | 18 / 18 / 267 | 34 / 34 / 558 | 18 / 18 / 172 | 11 / 11 / 80 | 11 / 11 / 72 | reverts `0x7bb9ae15` | 71 / 71 / 337 |
| 50 | `10068.72825272561` | 38 / 38 / 155 | 38 / 38 / 129 | 18 / 18 / 103 | 18 / 18 / 41 | 17 / 17 / 108 | 33 / 33 / 222 | 18 / 18 / 68 | 10 / 10 / 32 | 10 / 10 / 28 | reverts `0x7bb9ae15` | 72 / 72 / 135 |
| 100 | `10137.92886272349` | 38 / 38 / 81 | 38 / 38 / 68 | 19 / 19 / 50 | 18 / 18 / 20 | 17 / 17 / 54 | 34 / 34 / 111 | 18 / 18 / 34 | 8 / 8 / 16 | 8 / 8 / 14 | reverts `0x7bb9ae15` | 71 / 71 / 67 |
| 365 | `10512.71096376024` | 38 / 39 / 22 | 38 / 39 / 18 | 19 / 20 / 14 | 18 / 18 / 5 | 18 / 18 / 15 | 33 / 33 / 30 | 18 / 18 / 9 | 6 / 6 / 4 | 6 / 6 / 3 | reverts `0x7bb9ae15` | 71 / 71 / 18 |
| 1000 | `11468.12438653363` | 38 / 38 / 8 | 38 / 38 / 7 | 18 / 19 / 5 | 18 / 18 / 2 | 17 / 17 / 5 | 33 / 33 / 11 | 18 / 18 / 3 | 4 / 4 / 1 | 4 / 4 / 1 | reverts `0x7bb9ae15` | 71 / 71 / 6 |
| 10000 | `39348.11643256335` | 37 / 38 / 0 | 37 / 38 / 0 | 17 / 19 / 0 | 17 / 17 / 0 | 17 / 17 / 0 | 33 / 33 / 1 | 17 / 17 / 0 | 1 / 1 / 0 | 1 / 1 / 0 | reverts `0x7bb9ae15` | 72 / 71 / 0 |

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
| 1 | `6.878391866103811` | 37 / 37 / 32,317 | 37 / 37 / 26,083 | 18 / 18 / 103,309 | 16 / 16 / 77,500 | 16 / 16 / 141,920 | 32 / 32 / 345,171 | 16 / 16 / 126,672 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 47,730 |
| 2 | `6.868065132714932` | 37 / 38 / 16,611 | 37 / 38 / 13,226 | 18 / 17 / 51,797 | 17 / 17 / 38,866 | 16 / 16 / 71,254 | 32 / 32 / 173,051 | 17 / 17 / 63,587 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 24,186 |
| 5 | `6.837144794797698` | 37 / 39 / 7,158 | 37 / 39 / 5,483 | 18 / 18 / 20,871 | 16 / 16 / 15,686 | 16 / 16 / 28,865 | 32 / 32 / 69,801 | 16 / 16 / 25,736 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 10,049 |
| 10 | `6.785810396029252` | 36 / 38 / 4,031 | 36 / 38 / 2,928 | 18 / 18 / 10,584 | 16 / 16 / 7,959 | 16 / 16 / 14,727 | 31 / 31 / 34,995 | 16 / 16 / 13,119 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 70 / 70 / 5,281 |
| 20 | `6.683889366360745` | 36 / 38 / 2,467 | 36 / 38 / 1,649 | 17 / 17 / 5,432 | 16 / 16 / 4,052 | 16 / 16 / 7,578 | 31 / 31 / 17,766 | 16 / 16 / 6,737 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 71 / 71 / 2,963 |
| 50 | `6.384100145151291` | 36 / 38 / 1,521 | 36 / 38 / 872 | 17 / 18 / 2,322 | 16 / 16 / 1,742 | 16 / 16 / 3,349 | 31 / 31 / 7,625 | 16 / 16 / 2,967 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 1,542 |
| 100 | `5.904291981569546` | 35 / 37 / 1,204 | 35 / 37 / 612 | 16 / 17 / 1,283 | 16 / 16 / 971 | 16 / 16 / 1,939 | 30 / 30 / 4,129 | 16 / 16 / 1,706 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 69 / 69 / 1,065 |
| 365 | `3.76450175108814` | 35 / 37 / 993 | 35 / 37 / 442 | 16 / 17 / 577 | 16 / 16 / 450 | 16 / 16 / 988 | 30 / 30 / 1,938 | 16 / 16 / 856 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 754 |
| 1000 | `0.9741872197637135` | 34 / 36 / 942 | 34 / 36 / 401 | 15 / 16 / 409 | 15 / 15 / 325 | 15 / 15 / 761 | 29 / 29 / 1,410 | 15 / 15 / 653 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 68 / 68 / 711 |
| 10000 | `4.263958353856216e-34` | 3 / 3 / 928 | 3 / 3 / 373 | 0 / 0 / 317 | 0 / 0 / 256 | 0 / 0 / 639 | 27 / 27 / 1,087 | reverts `0xd4794efd` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 632 |

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
| 1 | `9.999995000001667e-7` | 32 / 33 / 7,508 | 32 / 33 / 7,099 | 13 / 13 / 4,980 | 12 / 12 / 1,824 | 12 / 12 / 4,037 | 28 / 28 / 11,052 | 12 / 12 / 2,683 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 6,409 |
| 2 | `1.999998000001333e-6` | 32 / 33 / 7,100 | 32 / 33 / 6,682 | 13 / 13 / 4,529 | 12 / 12 / 1,424 | 12 / 12 / 3,637 | 28 / 28 / 9,649 | 12 / 12 / 2,283 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 5,638 |
| 5 | `4.999987500020833e-6` | 33 / 34 / 6,856 | 33 / 34 / 6,432 | 13 / 13 / 4,258 | 12 / 12 / 1,184 | 12 / 12 / 3,397 | 28 / 28 / 8,800 | 12 / 12 / 2,043 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 5,175 |
| 10 | `9.999950000166666e-6` | 33 / 34 / 6,774 | 33 / 34 / 6,349 | 13 / 13 / 4,168 | 12 / 12 / 1,104 | 12 / 12 / 3,317 | 28 / 28 / 8,510 | 12 / 12 / 1,963 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 5,021 |
| 20 | `1.999980000133333e-5` | 33 / 33 / 6,733 | 33 / 33 / 6,307 | 13 / 13 / 4,123 | 12 / 12 / 1,064 | 12 / 12 / 3,277 | 28 / 28 / 8,372 | 12 / 12 / 1,923 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 4,944 |
| 50 | `4.999875002083307e-5` | 33 / 33 / 6,709 | 33 / 33 / 6,282 | 13 / 13 / 4,096 | 12 / 12 / 1,040 | 12 / 12 / 3,253 | 28 / 28 / 8,288 | 12 / 12 / 1,899 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 4,897 |
| 100 | `9.99950001666625e-5` | 33 / 33 / 6,701 | 33 / 33 / 6,274 | 13 / 13 / 4,087 | 12 / 12 / 1,032 | 12 / 12 / 3,245 | 28 / 28 / 8,261 | 12 / 12 / 1,891 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 4,882 |
| 365 | `0.0003649333956037813` | 33 / 33 / 6,698 | 33 / 33 / 6,268 | 13 / 13 / 4,080 | 11 / 11 / 1,026 | 12 / 12 / 3,239 | 28 / 28 / 8,240 | 11 / 11 / 1,885 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 4,871 |
| 1000 | `0.0009995001666250083` | 33 / 33 / 6,701 | 33 / 33 / 6,266 | 13 / 13 / 4,078 | 11 / 11 / 1,024 | 12 / 12 / 3,237 | 28 / 28 / 8,235 | 11 / 11 / 1,883 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 4,868 |
| 10000 | `0.009950166250831946` | 33 / 33 / 6,771 | 33 / 33 / 6,266 | 13 / 13 / 4,078 | 11 / 11 / 1,024 | 12 / 12 / 3,237 | 28 / 28 / 8,233 | 11 / 11 / 1,883 | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | reverts `0x7bb9ae15` | 66 / 66 / 4,867 |

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

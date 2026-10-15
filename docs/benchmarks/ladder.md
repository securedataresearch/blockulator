# Terminal precision ladder

Generated 2026-10-15 by `make ladder`. Versions: fp127 7906acf, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, forge forge Version: 1.7.1.

Each scenario is run for several inputs; the first table is the reference input in full (`digits / digitsFormat / gas per step`, where digits is against the exact truth and digitsFormat against the truth from the parameters as the library received them), the second is the summary over all inputs (`median (min–max)` digits, capped at 40). Full values, both truths, signed errors and raw words are in ladder.json; the method is in the Methodology section at the end.

## compound: Daily compound interest

Step: `b = b * (1 + r)`. Result: balance after N days.

Per-block or per-day accrual in every lending protocol: one mul per step, N steps.

Inputs: **reference** principal = 10000, rate = 0.1/365 ($10,000 at 10% APR, the headline cell); **tiny-low** principal = 1, rate = 0.01/365 (one unit at 1%: the integer part is small, the fraction carries everything); **tiny-high** principal = 1, rate = 0.5/365 (one unit at 50%); **mid-1pct** principal = 10000, rate = 0.01/365 (a slow rate: the per-step factor is close to 1); **mid-5pct** principal = 10000, rate = 0.05/365 (a typical lending rate); **mid-50pct** principal = 10000, rate = 0.5/365 (a high rate: the balance grows 150x by N = 10,000); **large** principal = 1000000, rate = 0.1/365 (a million-unit position); **huge** principal = 100000000, rate = 0.1/365 (a hundred-million-unit pool); **huge-high** principal = 100000000, rate = 0.5/365 (the largest balance the ladder reaches, near 10^14); **fraction** principal = 0.001, rate = 0.1/365 (a sub-unit balance: leading zeros in WAD)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `10002.7397260274` | 38 / exact / 2,113 | 38 / exact / 928 | 19 / exact / 934 | 19 / exact / 752 | 19 / exact / 1,112 |
| 2 | `10005.48020266467` | 38 / 42 / 1,848 | 38 / 42 / 653 | 19 / 23 / 609 | 19 / 22 / 494 | 19 / 22 / 854 |
| 5 | `10013.70613829244` | 38 / 42 / 1,689 | 38 / 42 / 488 | 19 / 23 / 414 | 18 / 21 / 340 | 18 / 21 / 700 |
| 10 | `10027.43106240757` | 37 / 41 / 1,636 | 37 / 41 / 433 | 18 / 22 / 349 | 18 / 21 / 288 | 18 / 21 / 648 |
| 20 | `10054.93737113361` | 37 / 41 / 1,609 | 37 / 41 / 405 | 18 / 22 / 317 | 18 / 21 / 262 | 18 / 21 / 622 |
| 50 | `10137.90984214166` | 37 / 41 / 1,593 | 37 / 41 / 389 | 18 / 21 / 297 | 17 / 20 / 247 | 17 / 20 / 607 |
| 100 | `10277.72159673926` | 36 / 40 / 1,588 | 36 / 40 / 383 | 17 / 21 / 291 | 17 / 20 / 242 | 17 / 20 / 602 |
| 365 | `11051.55781616264` | 36 / 40 / 1,585 | 36 / 40 / 379 | 17 / 21 / 286 | 16 / 19 / 238 | 16 / 19 / 598 |
| 1000 | `13151.29420081218` | 35 / 39 / 1,585 | 35 / 39 / 378 | 16 / 20 / 285 | 16 / 19 / 237 | 16 / 19 / 597 |
| 10000 | `154769.3406914411` | 34 / 39 / 1,602 | 34 / 39 / 378 | 15 / 20 / 285 | 15 / 18 / 237 | 15 / 18 / 597 |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 38 (35–39) | 38 (35–39) | 19 (16–20) | 18 (15–19) | 18 (15–19) |
| 2 | 38 (35–38) | 38 (35–38) | 19 (15–19) | 18 (14–19) | 18 (14–19) |
| 5 | 38 (35–38) | 38 (35–38) | 18.5 (15–19) | 18 (14–19) | 18 (14–19) |
| 10 | 37 (34–38) | 37 (34–38) | 18 (15–19) | 17 (14–18) | 17 (14–18) |
| 20 | 37 (34–37) | 37 (34–37) | 18 (15–18) | 17 (13–18) | 17 (13–18) |
| 50 | 37 (34–37) | 37 (34–37) | 17.5 (14–18) | 17 (13–18) | 17 (13–18) |
| 100 | 36 (33–37) | 36 (33–37) | 17 (14–18) | 16 (13–17) | 16 (13–17) |
| 365 | 36 (33–36) | 36 (33–36) | 16.5 (14–17) | 16 (12–17) | 16 (12–17) |
| 1000 | 35 (32–36) | 35 (32–36) | 16 (13–17) | 15 (12–16) | 15 (12–16) |
| 10000 | 34 (32–35) | 34 (32–35) | 15 (13–16) | 14 (11–15) | 14 (11–15) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 (35–40) | 40 (35–40) | 40 (16–40) | 40 (15–40) | 40 (15–40) |
| 2 | 40 (35–40) | 40 (35–40) | 23 (16–27) | 22 (14–26) | 22 (14–26) |
| 5 | 40 (35–40) | 40 (35–40) | 22.5 (15–27) | 21 (14–26) | 21 (14–26) |
| 10 | 40 (34–40) | 40 (34–40) | 22 (15–26) | 21 (14–25) | 21 (14–25) |
| 20 | 40 (34–40) | 40 (34–40) | 22 (15–26) | 21 (13–25) | 21 (13–25) |
| 50 | 40 (34–40) | 40 (34–40) | 21 (14–25) | 20 (13–24) | 20 (13–24) |
| 100 | 40 (33–40) | 40 (33–40) | 21 (14–25) | 20 (13–24) | 20 (13–24) |
| 365 | 40 (33–40) | 40 (33–40) | 21 (14–25) | 19 (12–23) | 19 (12–23) |
| 1000 | 39 (32–40) | 39 (32–40) | 20 (13–24) | 19 (12–23) | 19 (12–23) |
| 10000 | 39 (32–40) | 39 (32–40) | 19.5 (13–24) | 18 (11–23) | 18 (11–23) |

## compound-pow: Compound interest in one pow

Step: `b0 * (1 + r)^N`. Result: the same balance, computed with one real-exponent pow.

The clever way to skip the loop. pow is exp(N ln(1+r)) in every library, so its precision is bounded by ln and exp, and the error grows with N without any loop.

Inputs: **reference** principal = 10000, rate = 0.1/365 ($10,000 at 10% APR, the headline cell); **tiny-low** principal = 1, rate = 0.01/365 (one unit at 1%: the integer part is small, the fraction carries everything); **tiny-high** principal = 1, rate = 0.5/365 (one unit at 50%); **mid-1pct** principal = 10000, rate = 0.01/365 (a slow rate: the per-step factor is close to 1); **mid-5pct** principal = 10000, rate = 0.05/365 (a typical lending rate); **mid-50pct** principal = 10000, rate = 0.5/365 (a high rate: the balance grows 150x by N = 10,000); **large** principal = 1000000, rate = 0.1/365 (a million-unit position); **huge** principal = 100000000, rate = 0.1/365 (a hundred-million-unit pool); **huge-high** principal = 100000000, rate = 0.5/365 (the largest balance the ladder reaches, near 10^14); **fraction** principal = 0.001, rate = 0.1/365 (a sub-unit balance: leading zeros in WAD)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `10002.7397260274` | 38 / exact / 3,233 | 38 / exact / 1,178 | 19 / 19 / 11,497 | 17 / 18 / 2,165 | 19 / exact / 1,448 |
| 2 | `10005.48020266467` | 38 / 38 / 1,721 | 38 / 38 / 706 | 18 / 18 / 5,748 | 17 / 18 / 1,082 | 16 / 16 / 5,378 |
| 5 | `10013.70613829244` | 38 / 38 / 2,125 | 38 / 38 / 2,124 | 18 / 18 / 2,282 | 17 / 17 / 433 | 16 / 16 / 2,123 |
| 10 | `10027.43106240757` | 37 / 39 / 1,062 | 37 / 39 / 1,062 | 18 / 18 / 1,141 | 17 / 17 / 216 | 16 / 16 / 1,063 |
| 20 | `10054.93737113361` | 37 / 39 / 531 | 37 / 39 / 531 | 17 / 18 / 570 | 17 / 17 / 108 | 15 / 15 / 531 |
| 50 | `10137.90984214166` | 37 / 38 / 212 | 37 / 38 / 212 | 17 / 17 / 230 | 16 / 16 / 43 | 15 / 15 / 218 |
| 100 | `10277.72159673926` | 36 / 39 / 106 | 36 / 39 / 106 | 17 / 17 / 115 | 16 / 16 / 21 | 15 / 15 / 109 |
| 365 | `11051.55781616264` | 36 / 39 / 29 | 36 / 39 / 29 | 16 / 16 / 31 | 15 / 15 / 5 | 14 / 14 / 29 |
| 1000 | `13151.29420081218` | 35 / 39 / 10 | 35 / 39 / 10 | 16 / 16 / 11 | 15 / 15 / 2 | 14 / 14 / 11 |
| 10000 | `154769.3406914411` | 34 / 40 / 1 | 34 / 40 / 1 | 15 / 15 / 1 | 14 / 14 / 0 | 13 / 13 / 1 |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 38 (35–39) | 38 (35–39) | 19 (16–19) | 17 (15–17) | 18 (15–19) |
| 2 | 38 (35–38) | 38 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) |
| 5 | 38 (35–38) | 38 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) |
| 10 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (15–16) |
| 20 | 37 (35–37) | 37 (35–37) | 17 (16–18) | 16 (15–17) | 15 (15–15) |
| 50 | 37 (35–37) | 37 (35–37) | 17 (16–17) | 16 (15–17) | 15 (15–15) |
| 100 | 36 (35–37) | 36 (35–37) | 17 (16–17) | 16 (15–17) | 15 (14–15) |
| 365 | 36 (35–36) | 36 (35–36) | 16 (16–16) | 15 (15–16) | 14 (14–14) |
| 1000 | 35 (35–36) | 35 (35–36) | 16 (15–16) | 15 (14–16) | 14 (13–14) |
| 10000 | 34 (34–35) | 34 (34–35) | 15 (15–15) | 14 (13–15) | 13 (12–13) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 (35–40) | 40 (35–40) | 19 (16–19) | 18 (15–18) | 40 (15–40) |
| 2 | 38 (35–38) | 38 (35–38) | 18.5 (16–19) | 17 (15–18) | 16 (15–16) |
| 5 | 38 (35–39) | 38 (35–39) | 18 (16–19) | 17 (15–17) | 16 (15–16) |
| 10 | 39 (35–40) | 39 (35–40) | 18 (16–18) | 17 (15–18) | 16 (15–16) |
| 20 | 39 (35–39) | 39 (35–39) | 18 (16–18) | 16 (15–17) | 15 (15–15) |
| 50 | 39 (37–39) | 39 (37–39) | 17 (16–18) | 16 (15–17) | 15 (15–15) |
| 100 | 39 (37–39) | 39 (37–39) | 17 (16–18) | 16 (15–17) | 15 (14–15) |
| 365 | 39 (35–40) | 39 (35–40) | 16.5 (16–17) | 15 (15–16) | 14 (14–14) |
| 1000 | 39 (36–39) | 39 (36–39) | 16 (16–17) | 15 (14–16) | 14 (13–14) |
| 10000 | 40 (36–40) | 40 (36–40) | 15 (15–16) | 14 (14–15) | 13 (12–13) |

## bonding-sqrt: Square-root bonding curve

Step: `cost += sqrt(s); s += 1`. Result: total cost of N unit buys.

Bonding curves price each token at a root of the supply; the sum of N floors is where the digits go.

Inputs: **reference** supply = 1000, unit = 1 (a thousand tokens out, unit buys); **from-one** supply = 1, unit = 1 (the curve from its first token); **half-units** supply = 1000, unit = 0.5 (buys that are not integers); **deep** supply = 1000000, unit = 1 (a million out: sqrt is large, the sum is huge); **micro** supply = 1, unit = 0.001 (thousandth-unit buys from the start); **very-deep** supply = 1000000000, unit = 1000 (a billion out in thousand-token lots); **small-steps** supply = 10, unit = 0.01 (hundredth-unit buys from ten)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `31.62277660168379` | 41 / 41 / 4,456 | 41 / 41 / 4,226 | 20 / 20 / 1,816 | 19 / 19 / 1,270 | 19 / 19 / 1,750 |
| 2 | `63.26136064079654` | 40 / 40 / 4,241 | 40 / 40 / 4,014 | 21 / 21 / 1,576 | 19 / 19 / 1,058 | 19 / 19 / 1,542 |
| 5 | `158.2718785032213` | 40 / 40 / 4,112 | 40 / 40 / 3,887 | 21 / 21 / 1,426 | 19 / 19 / 931 | 19 / 19 / 1,416 |
| 10 | `316.9381559123806` | 40 / 40 / 4,069 | 40 / 40 / 3,845 | 21 / 21 / 1,378 | 19 / 19 / 889 | 19 / 19 / 1,372 |
| 20 | `635.4500029402082` | 40 / 40 / 4,048 | 40 / 40 / 3,824 | 21 / 21 / 1,353 | 19 / 19 / 868 | 19 / 19 / 1,351 |
| 50 | `1600.350881438697` | 40 / 40 / 3,973 | 40 / 40 / 3,720 | 21 / 21 / 1,341 | 19 / 19 / 855 | 19 / 19 / 1,339 |
| 100 | `3239.292264514382` | 40 / 40 / 3,941 | 40 / 40 / 3,674 | 21 / 21 / 1,338 | 19 / 19 / 851 | 19 / 19 / 1,335 |
| 365 | `12536.2620049473` | 40 / 40 / 3,917 | 40 / 40 / 3,640 | 21 / 21 / 1,336 | 19 / 19 / 848 | 19 / 19 / 1,332 |
| 1000 | `38540.07865481035` | 40 / 40 / 3,913 | 40 / 40 / 3,632 | 21 / 21 / 1,335 | 19 / 19 / 847 | 19 / 19 / 1,342 |
| 10000 | `748008.0076158747` | 40 / 40 / 4,000 | 40 / 40 / 3,722 | 21 / 21 / 1,347 | 20 / 20 / 847 | 20 / 20 / 1,351 |

### All inputs (7): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 (39–40) | 40 (39–40) | 23 (20–40) | 22 (18–40) | 22 (18–40) |
| 2 | 40 (38–40) | 40 (38–40) | 20 (19–24) | 19 (18–22) | 19 (18–22) |
| 5 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) |
| 10 | 40 (38–40) | 40 (38–40) | 20 (19–24) | 19 (18–22) | 19 (18–22) |
| 20 | 40 (38–40) | 40 (38–40) | 21 (18–24) | 19 (18–22) | 19 (18–22) |
| 50 | 40 (37–40) | 40 (37–40) | 21 (18–24) | 19 (18–22) | 19 (18–22) |
| 100 | 40 (37–40) | 40 (37–40) | 21 (18–24) | 19 (18–22) | 19 (18–22) |
| 365 | 40 (36–40) | 40 (36–40) | 21 (17–24) | 19 (18–22) | 19 (18–22) |
| 1000 | 40 (36–40) | 40 (36–40) | 21 (17–24) | 19 (18–22) | 19 (18–22) |
| 10000 | 40 (36–40) | 40 (36–40) | 21 (16–24) | 20 (18–22) | 20 (18–22) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 (39–40) | 40 (39–40) | 23 (20–40) | 22 (18–40) | 22 (18–40) |
| 2 | 40 (38–40) | 40 (38–40) | 20 (19–24) | 19 (18–22) | 19 (18–22) |
| 5 | 40 (39–40) | 40 (39–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) |
| 10 | 40 (38–40) | 40 (38–40) | 20 (19–24) | 19 (18–22) | 19 (18–22) |
| 20 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) |
| 50 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) |
| 100 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) |
| 365 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) |
| 1000 | 40 (38–40) | 40 (38–40) | 21 (19–24) | 19 (18–22) | 19 (18–22) |
| 10000 | 40 (39–40) | 40 (39–40) | 21 (19–24) | 20 (18–22) | 20 (18–22) |

## roundtrip: exp(ln(x)) round trip

Step: `x = exp(ln(x))`. Result: x after N round trips; the answer is the input.

Isolates transcendental error. Every step should be the identity; what remains is the library's ln and exp error, compounded.

Inputs: **reference** x0 = 1.5 (1.5 is representable in every format, so a perfect library returns it exactly); **hundredth** x0 = 0.01 (ln is large and negative); **tenth** x0 = 0.1 (a typical price ratio); **near-one-below** x0 = 0.7 (ln is small: cancellation territory); **just-above-one** x0 = 1.0001 (ln is tiny: the log1p regime); **two** x0 = 2 (the simplest non-trivial value); **ten** x0 = 10 (a round decade); **thousand** x0 = 1000 (three decades); **million** x0 = 1000000 (six decades, near ABDK's comfortable range); **awkward** x0 = 123456.789 (a value with no special structure)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `1.5` | 38 / 38 / 10,137 | 38 / 38 / 10,139 | 19 / 19 / 10,892 | exact / exact / 1,441 | 16 / 16 / 10,093 |
| 2 | `1.5` | 38 / 38 / 9,965 | 38 / 38 / 9,970 | 18 / 18 / 10,698 | exact / exact / 1,272 | 16 / 16 / 9,902 |
| 5 | `1.5` | 38 / 38 / 9,861 | 38 / 38 / 9,868 | 18 / 18 / 10,578 | exact / exact / 1,170 | 16 / 16 / 9,772 |
| 10 | `1.5` | 38 / 38 / 9,827 | 38 / 38 / 9,834 | 18 / 18 / 10,538 | exact / exact / 1,136 | 15 / 15 / 9,794 |
| 20 | `1.5` | 38 / 38 / 9,810 | 38 / 38 / 9,817 | 17 / 17 / 10,522 | exact / exact / 1,119 | 15 / 15 / 9,801 |
| 50 | `1.5` | 38 / 38 / 9,800 | 38 / 38 / 9,807 | 17 / 17 / 10,507 | exact / exact / 1,109 | 15 / 15 / 9,789 |
| 100 | `1.5` | 38 / 38 / 9,797 | 38 / 38 / 9,804 | 17 / 17 / 10,502 | exact / exact / 1,106 | 14 / 14 / 9,773 |
| 365 | `1.5` | 38 / 38 / 9,796 | 38 / 38 / 9,801 | 16 / 16 / 10,488 | exact / exact / 1,103 | 14 / 14 / 9,778 |
| 1000 | `1.5` | 38 / 38 / 9,801 | 38 / 38 / 9,801 | 16 / 16 / 10,495 | exact / exact / 1,103 | 13 / 13 / 9,761 |
| 10000 | `1.5` | 38 / 38 / 9,871 | 38 / 38 / 9,801 | 15 / 15 / 10,500 | exact / exact / 1,103 | 12 / 12 / 9,758 |

### All inputs (10): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 38 (36–39) | 38 (36–39) | 19 (17–19) | 18 (16–40) | 17 (16–40) |
| 2 | 38 (36–39) | 38 (36–39) | 18 (16–18) | 17 (16–40) | 16 (16–40) |
| 5 | 38 (36–39) | 38 (36–39) | 18 (16–18) | 17 (16–40) | 16 (16–40) |
| 10 | 38 (36–39) | 38 (36–39) | 17.5 (16–18) | 17 (15–40) | 16 (15–40) |
| 20 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (15–40) | 15 (15–40) |
| 50 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (15–40) | 15 (15–40) |
| 100 | 38 (36–39) | 38 (36–39) | 17 (15–17) | 16 (15–40) | 15 (14–40) |
| 365 | 38 (36–39) | 38 (36–39) | 16 (14–16) | 15 (14–40) | 14 (14–40) |
| 1000 | 38 (36–39) | 38 (36–39) | 16 (14–16) | 15 (13–40) | 14 (13–40) |
| 10000 | 38 (36–39) | 38 (36–39) | 15 (13–15) | 14 (12–40) | 13 (12–40) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 39 (38–40) | 39 (38–40) | 19 (17–19) | 18 (16–40) | 17 (16–40) |
| 2 | 39 (38–40) | 39 (38–40) | 18 (16–18) | 17 (16–40) | 16 (16–40) |
| 5 | 39 (38–40) | 39 (38–40) | 18 (16–18) | 17 (16–40) | 16 (16–40) |
| 10 | 39 (38–40) | 39 (38–40) | 17.5 (16–18) | 17 (15–40) | 16 (15–40) |
| 20 | 39 (38–40) | 39 (38–40) | 17 (15–17) | 16 (15–40) | 15 (15–40) |
| 50 | 39 (38–40) | 39 (38–40) | 17 (15–17) | 16 (15–40) | 15 (15–40) |
| 100 | 39 (38–40) | 39 (38–40) | 17 (15–17) | 16 (15–40) | 15 (14–40) |
| 365 | 39 (38–40) | 39 (38–40) | 16 (14–16) | 15 (14–40) | 14 (14–40) |
| 1000 | 39 (38–40) | 39 (38–40) | 16 (14–16) | 15 (13–40) | 14 (13–40) |
| 10000 | 39 (38–40) | 39 (38–40) | 15 (13–15) | 14 (12–40) | 13 (12–40) |

## amortise: Amortising loan

Step: `b = b * (1 + r) - payment`. Result: outstanding balance after N daily payments.

Subtracting nearly equal numbers. The payment retires the loan at step 366, so at N = 365 the balance is one payment and relative error is amplified several hundred times.

Inputs: **reference** principal = 300000, rate = 0.05/365, term = 366 (a mortgage-sized loan retiring at step 366); **small** principal = 10000, rate = 0.05/365, term = 366 (a small loan); **high-rate** principal = 300000, rate = 0.1/365, term = 366 (double the rate); **ten-year** principal = 300000, rate = 0.05/365, term = 3650 (a ten-year term: at N = 365 nine tenths remain); **large-low** principal = 1000000, rate = 0.03/365, term = 366 (a large loan at a low rate); **very-high** principal = 300000, rate = 0.2/365, term = 366 (20% APR); **micro** principal = 500, rate = 0.05/365, term = 366 (a tiny loan: the payment is a few units); **retires-at-10001** principal = 300000, rate = 0.05/365, term = 10001 (retires one step past the ladder's end, so N = 10,000 is the one-payment cell)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `299200.6479903559` | 39 / exact / 2,520 | 39 / exact / 1,366 | 20 / exact / 1,434 | 19 / exact / 1,159 | 19 / exact / 1,519 |
| 2 | `298401.1864804365` | 38 / 44 / 2,130 | 38 / 44 / 966 | 19 / 25 / 966 | 19 / 23 / 776 | 19 / 23 / 1,136 |
| 5 | `296002.1447990159` | 38 / 43 / 1,896 | 38 / 43 / 726 | 19 / 24 / 686 | 19 / 23 / 547 | 19 / 23 / 907 |
| 10 | `292001.5505907346` | 38 / 43 / 1,818 | 38 / 43 / 646 | 19 / 24 / 592 | 18 / 22 / 470 | 18 / 22 / 830 |
| 20 | `283992.1376448092` | 37 / 42 / 1,779 | 37 / 42 / 606 | 18 / 23 / 545 | 18 / 22 / 432 | 18 / 22 / 792 |
| 50 | `259897.9672060033` | 37 / 42 / 1,755 | 37 / 42 / 582 | 18 / 23 / 517 | 18 / 22 / 409 | 18 / 22 / 769 |
| 100 | `219520.3390882176` | 37 / 42 / 1,748 | 37 / 42 / 574 | 17 / 22 / 508 | 17 / 21 / 401 | 17 / 21 / 761 |
| 365 | `840.3327859747961` | 34 / 39 / 1,742 | 34 / 39 / 568 | 15 / 19 / 501 | 15 / 18 / 396 | 15 / 18 / 756 |
| 1000 | `-556627.3884008416` | 36 / 41 / 1,742 | 36 / 41 / 566 | 17 / 22 / 499 | 17 / 21 / 394 | 17 / 21 / 761 |
| 10000 | `-16823263.35321035` | 35 / 41 / 1,759 | 35 / 41 / 566 | 16 / 22 / 499 | 16 / 21 / 394 | 16 / 21 / 764 |

### All inputs (8): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 39 (38–39) | 39 (38–39) | 20 (19–20) | 19 (18–19) | 19 (18–19) |
| 2 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 19 (17–19) | 19 (17–19) |
| 5 | 38 (37–38) | 38 (37–38) | 19 (18–19) | 19 (17–19) | 19 (17–19) |
| 10 | 38 (37–38) | 38 (37–38) | 19 (18–19) | 18 (17–18) | 18 (17–18) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 18 (16–18) | 18 (16–18) |
| 50 | 37 (36–37) | 37 (36–37) | 18 (17–18) | 18 (16–18) | 18 (16–18) |
| 100 | 37 (36–37) | 37 (36–37) | 17 (17–18) | 17 (16–17) | 17 (16–17) |
| 365 | 34 (33–36) | 34 (33–36) | 15 (14–17) | 14.5 (13–17) | 14.5 (13–17) |
| 1000 | 36 (36–36) | 36 (36–36) | 17 (16–17) | 16.5 (15–17) | 16.5 (15–17) |
| 10000 | 35 (31–35) | 35 (31–35) | 15.5 (12–16) | 15.5 (11–16) | 15.5 (11–16) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) |
| 2 | 40 (40–40) | 40 (40–40) | 24 (22–25) | 23 (21–24) | 23 (21–24) |
| 5 | 40 (40–40) | 40 (40–40) | 24 (21–24) | 23 (20–23) | 23 (20–23) |
| 10 | 40 (40–40) | 40 (40–40) | 24 (21–24) | 22 (20–23) | 22 (20–23) |
| 20 | 40 (40–40) | 40 (40–40) | 23 (20–24) | 22 (19–23) | 22 (19–23) |
| 50 | 40 (39–40) | 40 (39–40) | 23 (20–23) | 22 (19–22) | 22 (19–22) |
| 100 | 40 (39–40) | 40 (39–40) | 22 (20–23) | 21 (18–22) | 21 (18–22) |
| 365 | 39 (36–40) | 39 (36–40) | 19 (17–22) | 18 (15–21) | 18 (15–21) |
| 1000 | 40 (38–40) | 40 (38–40) | 21.5 (19–22) | 20.5 (18–22) | 20.5 (18–22) |
| 10000 | 40 (36–40) | 40 (36–40) | 21.5 (16–22) | 21 (15–21) | 21 (15–21) |

## geo-mean: Running geometric mean

Step: `L += ln(x_i); g = exp(L / N), x_i = (i + 2) / (i + 1)`. Result: geometric mean of N terms; truth telescopes to ((N + 2) / 2)^(1 / N).

Index and basket maths: a sum of logs, one division, one exp. The division by N and the final exp expose every accumulated ULP.

Inputs: **reference**  (the scenario has no parameters; its inputs are the integers 1..N)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `1.5` | 38 / 38 / 12,857 | 38 / 38 / 11,986 | 19 / 19 / 12,147 | exact / exact / 2,592 | 16 / 16 / 12,078 |
| 2 | `1.414213562373095` | 38 / 38 / 9,526 | 38 / 38 / 8,955 | 18 / 18 / 10,323 | 17 / 17 / 2,052 | 16 / 16 / 10,393 |
| 5 | `1.284735157123439` | 38 / 38 / 7,402 | 38 / 38 / 6,977 | 19 / 19 / 8,890 | 17 / 17 / 1,728 | 16 / 16 / 9,076 |
| 10 | `1.196231198851315` | 38 / 38 / 6,658 | 38 / 38 / 6,271 | 18 / 18 / 8,504 | 17 / 17 / 1,620 | 16 / 16 / 8,695 |
| 20 | `1.127378204157833` | 38 / 38 / 6,293 | 38 / 38 / 5,928 | 18 / 18 / 8,309 | 17 / 17 / 1,566 | 16 / 16 / 8,547 |
| 50 | `1.067331844248559` | 38 / 38 / 6,025 | 38 / 38 / 5,659 | 18 / 18 / 8,185 | 17 / 17 / 1,534 | 16 / 16 / 8,384 |
| 100 | `1.04010144984871` | 39 / 39 / 5,891 | 39 / 39 / 5,512 | 18 / 18 / 8,148 | 17 / 17 / 1,523 | 16 / 16 / 8,326 |
| 365 | `1.01438248702624` | 38 / 38 / 5,694 | 38 / 38 / 5,278 | 18 / 18 / 8,118 | 17 / 17 / 1,515 | 16 / 16 / 8,266 |
| 1000 | `1.006235969300459` | 39 / 39 / 5,621 | 39 / 39 / 5,183 | 18 / 18 / 8,111 | 17 / 17 / 1,514 | 16 / 16 / 8,249 |
| 10000 | `1.00085210215008` | 38 / 38 / 5,650 | 38 / 38 / 5,133 | 18 / 18 / 8,108 | 17 / 17 / 1,513 | 16 / 16 / 8,196 |

### All inputs (1): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 40 (40–40) | 16 (16–16) |
| 2 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 5 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 17 (17–17) | 16 (16–16) |
| 10 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 20 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 50 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 100 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 365 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 1000 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 10000 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 40 (40–40) | 16 (16–16) |
| 2 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 5 | 38 (38–38) | 38 (38–38) | 19 (19–19) | 17 (17–17) | 16 (16–16) |
| 10 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 20 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 50 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 100 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 365 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 1000 | 39 (39–39) | 39 (39–39) | 18 (18–18) | 17 (17–17) | 16 (16–16) |
| 10000 | 38 (38–38) | 38 (38–38) | 18 (18–18) | 17 (17–17) | 16 (16–16) |

## black-scholes-chain: Black-Scholes d1 along a price path

Step: `acc += d1(S); S += tick, with d1 = (ln(S / K) + (r + sigma^2 / 2) T) / (sigma sqrt(T))`. Result: sum of d1 over N ticks.

The options-desk case: ln, div, sqrt and mul in one expression, re-evaluated as the spot moves and aggregated.

Inputs: **reference** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (at the money, 20% vol, six months); **low-vol** spot = 100, strike = 100, sigma = 0.05, T = 0.5, r = 0.05, tick = 0.01 (5% vol: the denominator is small); **high-vol** spot = 100, strike = 100, sigma = 0.8, T = 0.5, r = 0.05, tick = 0.01 (80% vol); **in-the-money** spot = 120, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (ln(S/K) is positive and not small); **out-of-the-money** spot = 80, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 0.01 (ln(S/K) is negative); **short-dated** spot = 100, strike = 100, sigma = 0.2, T = 0.01, r = 0.05, tick = 0.01 (sqrt(T) is small); **long-dated** spot = 100, strike = 100, sigma = 0.2, T = 2, r = 0.05, tick = 0.01 (two years); **coarse-ticks** spot = 100, strike = 100, sigma = 0.2, T = 0.5, r = 0.05, tick = 1 (whole-unit ticks: S doubles by N = 100 and reaches 10,100)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `0.2474873734152916` | 37 / 37 / 14,510 | 37 / 37 / 8,487 | 18 / 18 / 11,765 | 17 / 17 / 3,862 | 17 / 17 / 7,014 |
| 2 | `0.4956818182587876` | 37 / 37 / 13,283 | 37 / 37 / 9,086 | 17 / 17 / 10,636 | 18 / 18 / 2,953 | 16 / 16 / 8,451 |
| 5 | `1.244506874463792` | 37 / 37 / 12,547 | 37 / 37 / 9,445 | 17 / 17 / 9,959 | 17 / 17 / 2,408 | 15 / 15 / 9,445 |
| 10 | `2.506683467804941` | 36 / 37 / 12,302 | 36 / 37 / 9,565 | 17 / 17 / 9,733 | 17 / 17 / 2,226 | 15 / 15 / 9,747 |
| 20 | `5.084010514032979` | 36 / 37 / 12,179 | 36 / 37 / 9,625 | 17 / 17 / 9,620 | 17 / 17 / 2,135 | 15 / 15 / 9,918 |
| 50 | `13.23914876467473` | 36 / 37 / 12,107 | 36 / 37 / 9,661 | 17 / 17 / 9,553 | 17 / 17 / 2,081 | 15 / 15 / 10,065 |
| 100 | `28.23736439326609` | 36 / 37 / 12,156 | 36 / 37 / 9,762 | 17 / 17 / 9,530 | 17 / 17 / 2,063 | 15 / 15 / 10,111 |
| 365 | `136.7454508837998` | 36 / 37 / 12,276 | 36 / 37 / 9,929 | 17 / 17 / 9,514 | 17 / 17 / 2,049 | 15 / 15 / 10,148 |
| 1000 | `589.4747739528645` | 36 / 37 / 12,414 | 36 / 37 / 10,073 | 17 / 18 / 9,510 | 18 / 18 / 2,046 | 15 / 15 / 10,184 |
| 10000 | `29787.55928753143` | 36 / 39 / 13,116 | 36 / 39 / 10,415 | 18 / 19 / 9,508 | 17 / 17 / 2,045 | 16 / 16 / 10,236 |

### All inputs (8): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 37 (35–38) | 37 (35–38) | 18 (17–19) | 17 (17–40) | 17 (16–40) |
| 2 | 37 (35–38) | 37 (35–38) | 17.5 (16–18) | 17.5 (15–18) | 16 (14–16) |
| 5 | 37 (35–38) | 37 (35–38) | 17 (16–18) | 17 (15–18) | 15.5 (14–16) |
| 10 | 37 (35–38) | 37 (35–38) | 17 (16–18) | 17 (15–18) | 15.5 (14–16) |
| 20 | 37 (35–37) | 37 (35–37) | 17.5 (16–18) | 17 (15–17) | 16 (14–16) |
| 50 | 37 (35–38) | 37 (35–38) | 17.5 (16–18) | 17 (15–17) | 16 (14–16) |
| 100 | 37 (36–39) | 37 (36–39) | 17.5 (16–19) | 17 (16–17) | 16 (14–16) |
| 365 | 37 (36–38) | 37 (36–38) | 17.5 (17–19) | 17 (16–17) | 16 (15–17) |
| 1000 | 37 (36–38) | 37 (36–38) | 17 (17–18) | 17 (16–18) | 16 (15–17) |
| 10000 | 37 (36–38) | 37 (36–38) | 18 (17–20) | 17 (17–18) | 16 (16–17) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 37 (35–38) | 37 (35–38) | 18 (17–19) | 17 (17–40) | 17 (16–40) |
| 2 | 37 (35–39) | 37 (35–39) | 18 (16–19) | 17.5 (15–18) | 16 (14–16) |
| 5 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–18) | 15.5 (14–16) |
| 10 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–18) | 15.5 (14–16) |
| 20 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (14–16) |
| 50 | 37 (35–38) | 37 (35–38) | 18 (16–18) | 17 (15–17) | 16 (14–16) |
| 100 | 37.5 (36–39) | 37.5 (36–39) | 18 (16–19) | 17 (16–17) | 16 (14–16) |
| 365 | 37 (36–38) | 37 (36–38) | 18 (17–19) | 17 (16–17) | 16 (15–17) |
| 1000 | 37.5 (37–38) | 37.5 (37–38) | 18 (17–19) | 17 (16–18) | 16 (15–17) |
| 10000 | 38 (37–39) | 38 (37–39) | 18 (17–20) | 17 (17–18) | 16 (16–17) |

## cumulative-product: Cumulative product of small factors

Step: `p = p * (1 + eps_i), eps_i = +eps for odd i, -eps for even i`. Result: product after N factors.

The general form of fee accrual, index levels and LP share accounting: many factors a basis point from one. The drift from 1 is where the digits are, and it is small.

Inputs: **reference** eps = 0.0001 (a basis point); **percent** eps = 0.01 (one percent); **tenth-percent** eps = 0.001 (ten basis points); **micro** eps = 0.000001 (a hundredth of a basis point: the factors are within WAD's last digits of one); **five-percent** eps = 0.05 (large factors: the product falls to 4e-6 by N = 10,000)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `1.0001` | 39 / exact / 2,613 | 39 / exact / 1,459 | 20 / exact / 1,491 | exact / exact / 1,246 | exact / exact / 1,606 |
| 2 | `0.99999999` | 39 / 39 / 2,153 | 39 / 39 / 974 | 19 / 19 / 943 | exact / exact / 797 | exact / exact / 1,157 |
| 5 | `1.000099979998` | 38 / 38 / 1,878 | 38 / 38 / 683 | 18 / 18 / 615 | 20 / 20 / 528 | 20 / 20 / 888 |
| 10 | `0.999999950000001` | 37 / 37 / 1,786 | 37 / 37 / 586 | 18 / 18 / 505 | 17 / 17 / 438 | 17 / 17 / 798 |
| 20 | `0.9999999000000045` | 37 / 37 / 1,740 | 37 / 37 / 537 | 18 / 18 / 451 | 17 / 17 / 393 | 17 / 17 / 753 |
| 50 | `0.99999975000003` | 37 / 37 / 1,712 | 37 / 37 / 508 | 17 / 17 / 418 | 16 / 16 / 366 | 16 / 16 / 726 |
| 100 | `0.9999995000001225` | 36 / 36 / 1,703 | 36 / 36 / 499 | 17 / 17 / 407 | 16 / 16 / 357 | 16 / 16 / 717 |
| 365 | `1.000098179819647` | 36 / 36 / 1,697 | 36 / 36 / 492 | 16 / 16 / 399 | 15 / 15 / 350 | 15 / 15 / 710 |
| 1000 | `0.999995000012475` | 35 / 35 / 1,697 | 35 / 35 / 490 | 16 / 16 / 397 | 15 / 15 / 349 | 15 / 15 / 709 |
| 10000 | `0.9999500012497292` | 34 / 34 / 1,714 | 34 / 34 / 489 | 15 / 15 / 396 | 14 / 14 / 348 | 14 / 14 / 708 |

### All inputs (5): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 40 (40–40) | 40 (40–40) |
| 2 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 40 (40–40) | 40 (40–40) |
| 5 | 38 (37–38) | 38 (37–38) | 18 (18–19) | 40 (20–40) | 40 (20–40) |
| 10 | 37 (37–37) | 37 (37–37) | 18 (18–19) | 18 (17–22) | 18 (17–22) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 17 (17–22) | 17 (17–22) |
| 50 | 37 (37–37) | 37 (37–37) | 17 (17–18) | 16 (16–21) | 16 (16–21) |
| 100 | 36 (36–36) | 36 (36–36) | 17 (17–17) | 16 (16–20) | 16 (16–20) |
| 365 | 36 (36–36) | 36 (36–36) | 16 (16–17) | 15 (15–19) | 15 (15–19) |
| 1000 | 35 (35–35) | 35 (35–35) | 16 (16–16) | 15 (15–18) | 15 (15–18) |
| 10000 | 34 (30–34) | 34 (30–34) | 15 (11–15) | 14 (9–16) | 14 (9–16) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) |
| 2 | 38 (38–39) | 38 (38–39) | 19 (19–20) | 40 (40–40) | 40 (40–40) |
| 5 | 38 (38–38) | 38 (38–38) | 18 (18–19) | 40 (20–40) | 40 (20–40) |
| 10 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 18 (17–22) | 18 (17–22) |
| 20 | 37 (37–37) | 37 (37–37) | 18 (18–18) | 17 (17–22) | 17 (17–22) |
| 50 | 37 (37–37) | 37 (37–37) | 17 (17–17) | 16 (16–21) | 16 (16–21) |
| 100 | 36 (36–36) | 36 (36–36) | 17 (17–17) | 16 (16–20) | 16 (16–20) |
| 365 | 36 (36–36) | 36 (36–36) | 16 (16–17) | 15 (15–19) | 15 (15–19) |
| 1000 | 35 (35–35) | 35 (35–35) | 16 (16–16) | 15 (15–18) | 15 (15–18) |
| 10000 | 34 (30–34) | 34 (30–34) | 15 (11–15) | 14 (9–16) | 14 (9–16) |

## compound-annual: Annual compounding at 10% (README claim check)

Step: `b = b * 1.1`. Result: balance after N years.

The old README asserted $25,937.42 true against $25,932.38 for Solady at N = 10 with no source. This row regenerates that number.

Inputs: **reference** principal = 10000, rate = 0.1 (the README claim); **five-pct** principal = 10000, rate = 0.05 (5% a year); **unit** principal = 1, rate = 0.1 (one unit); **million** principal = 1000000, rate = 0.1 (a million units: ABDK overflows sooner); **fifty-pct** principal = 10000, rate = 0.5 (50% a year: every library overflows before N = 100)

### Reference input: reference

| N | truth | fp127 | fp127lib | abdk | solady | prb |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `11000.0` | 38 / exact / 2,368 | 38 / exact / 1,183 | 19 / exact / 1,189 | exact / exact / 1,007 | exact / exact / 1,367 |
| 2 | `12100.0` | 38 / exact / 1,975 | 38 / exact / 780 | 19 / 39 / 737 | exact / exact / 622 | exact / exact / 982 |
| 5 | `16105.1` | 38 / 42 / 1,740 | 38 / 42 / 539 | 18 / 23 / 465 | exact / exact / 391 | exact / exact / 751 |
| 10 | `25937.424601` | 37 / 42 / 1,661 | 37 / 42 / 458 | 18 / 23 / 375 | exact / exact / 314 | exact / exact / 674 |
| 20 | `67274.999493256` | 37 / 42 / 1,622 | 37 / 42 / 418 | 18 / 22 / 330 | exact / exact / 275 | exact / exact / 635 |
| 50 | `1173908.528796953` | 37 / 41 / 1,598 | 37 / 41 / 394 | 17 / 22 / 303 | 22 / 22 / 252 | 22 / 22 / 612 |
| 100 | `137806123.3982227` | 36 / 41 / 1,591 | 36 / 41 / 386 | 17 / 22 / 294 | 22 / 22 / 244 | 22 / 22 / 604 |
| 365 | `1.283305580313353e+19` | 36 / 41 / 1,585 | 36 / 41 / 380 | reverts `0x00000000` | 22 / 22 / 239 | 22 / 22 / 599 |
| 1000 | `2.469932918005826e+45` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | 22 / 22 / 606 |
| 10000 | `8.449900251200348e+417` | reverts `0x35278d12` | reverts `0x35278d12` | reverts `0x00000000` | reverts `0xedcd4dd4` | reverts `0x120b5b43` |

### All inputs (5): digits, median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 38 (38–40) | 38 (38–40) | 19 (19–40) | 40 (40–40) | 40 (40–40) |
| 2 | 38 (38–40) | 38 (38–40) | 19 (19–40) | 40 (40–40) | 40 (40–40) |
| 5 | 38 (37–40) | 38 (37–40) | 18 (18–40) | 40 (40–40) | 40 (40–40) |
| 10 | 37 (37–40) | 37 (37–40) | 18 (18–40) | 40 (40–40) | 40 (40–40) |
| 20 | 37 (37–40) | 37 (37–40) | 18 (18–40) | 40 (18–40) | 40 (18–40) |
| 50 | 37 (36–40) | 37 (36–40) | 17 (17–40) | 22 (18–25) | 22 (18–25) |
| 100 | 36 (36–40) | 36 (36–40) | 17 (17–17), 1 revert | 22 (18–25) | 22 (18–25) |
| 365 | 36 (36–36), 1 revert | 36 (36–36), 1 revert | 16 (16–16), 3 revert | 21.5 (18–24), 1 revert | 21.5 (18–24), 1 revert |
| 1000 | 35 (35–35), 4 revert | 35 (35–35), 4 revert | — (5 revert) | 21 (21–21), 4 revert | 21.5 (18–24), 1 revert |
| 10000 | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) |

### All inputs: digitsFormat (arithmetic alone), median (min–max)

| N | fp127 | fp127lib | abdk | solady | prb |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) | 40 (40–40) |
| 2 | 40 (38–40) | 40 (38–40) | 39 (20–40) | 40 (40–40) | 40 (40–40) |
| 5 | 40 (38–40) | 40 (38–40) | 23 (19–40) | 40 (40–40) | 40 (40–40) |
| 10 | 40 (38–40) | 40 (38–40) | 23 (18–40) | 40 (40–40) | 40 (40–40) |
| 20 | 40 (37–40) | 40 (37–40) | 22 (18–40) | 40 (18–40) | 40 (18–40) |
| 50 | 40 (37–40) | 40 (37–40) | 22 (18–40) | 22 (18–25) | 22 (18–25) |
| 100 | 40 (37–40) | 40 (37–40) | 22 (18–24), 1 revert | 22 (18–25) | 22 (18–25) |
| 365 | 40 (37–40), 1 revert | 40 (37–40), 1 revert | 20 (18–22), 3 revert | 21.5 (18–24), 1 revert | 21.5 (18–24), 1 revert |
| 1000 | 40 (40–40), 4 revert | 40 (40–40), 4 revert | — (5 revert) | 21 (21–21), 4 revert | 21.5 (18–24), 1 revert |
| 10000 | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) | — (5 revert) |

## Methodology

**truth.** For every scenario, input and N the same loop is run in exact real arithmetic with mpmath at 200 decimal digits (scripts/ladder/ladder.py), from the exact rational parameters in scenarios.json. Closed forms are used where the loop has one (compounding, the cumulative product, the geometric mean, the round trip); the bonding curve, the amortising loan and the Black-Scholes chain are stepped.

**rounding.** Each library receives the parameters floored into its own representation (2^-128, 2^-64 or 10^-18 units; scripts/ladder/inputs.json). truthFormat is the exact loop started from those floored parameters, so digitsFormat measures the library's arithmetic alone, while digits measures what a protocol sees: the format's rounding of the inputs plus the arithmetic.

**digits.** digits = floor(-log10 |v - t| / |t|), the number of correct leading significant digits by relative error, capped at 60, which is reported as exact. It is not a string comparison: a value can be correct to 36 digits while its 37th printed digit happens to agree with the truth, or while a carry makes the printed prefix differ earlier.

**agree.** agree is the count of leading significant digits of the printed value (42 significant digits) that are literally equal to the printed truth. The demo page colours the rest of the value with it. It is a reading aid, not a measurement: a carry across 0.999… / 1.000… gives 0.

**gas.** gasTotal is measured inside the adapter around the scenario function (the parameter reads and the loop), after the runner has warmed the adapter and the FP127 object, so the call into the adapter and the ABI decoding are excluded. The FP127 (deployed) form includes one staticcall per op; FP127Lib and the other libraries are internal calls. gasPerStep = gasTotal / N. Reverted cells carry no gas.

**live.** LadderRunner.run(scenario, form, n, p) on Sepolia executes any cell with one eth_call and returns (ok, raw, reason, gasPerStep, gasTotal). The demo's verify button sends the cell's floored parameters p and compares the returned raw word with the committed one bit for bit (or the revert selector for a reverted cell). liveMaxN is the largest N per form the public RPC completed within its gas limit, measured by scripts/ladder/livecap.py.

**reproduce.** make ladder regenerates ladder.json and ladder.md from the Foundry harness (test/ladder/Ladder.t.sol) and this script; make ladder-check fails CI when the committed dataset differs. Versions of every library and of forge are recorded in the dataset.

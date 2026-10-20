# Replay: the Balancer V1 drain of 31 August 2026

Generated 2026-10-20 by `uv run scripts/replays/balancer_v1.py score` (offline) from `scripts/replays/balancer_v1.json` (fetched 2026-10-20 by `balancer_v1.py fetch`). The Foundry replay is `test/replays/BalancerV1.t.sol`; it needs no network.

## The answer first

- **Five pools, not one.** SlowMist's five transactions hit five different Balancer V1 BPools, all deployed by Balancer's own BFactory `0x9424B1412450D0f8Fc2255FAf6046b98213B76Bd`, between 02:28 and 03:36 UTC. SlowMist named only the first pool as the vulnerable contract.
- **Every attack join paid one token unit for about one and a half.** Across the 438 joins (`joinswapPoolAmountOut`, `maxAmountIn = 1`), the exact price was 1.5007879 to 1.5274949 units. The deployed maths charged 1 every time. In the opposite direction, each of the 489 dust exits (`exitswapPoolAmountIn`, `minAmountOut = 1`) was worth 0.491 to 0.499738 units, and the pool paid 1.
- **The loss is one rounding step.** `bmul(tokenInRatio, tokenBalanceIn)` (BMath.sol:156-182, line 174) multiplies an 18-decimal ratio by a balance held in raw token units: satoshi for WBTC and renBTC, 10^-6 for USDC. `bmul` rounds half up (BNum.sol:63-73). At a balance of 3 units, 3 × 1.499999999999999997 = 4.499999999999999991 rounds to 4 rather than 5, so the attacker pays 1. On an exit, 3.4999… rounds down, so the pool pays out 1.
- **The binomial series is not involved.** In every attacked pool the attacked token's normalized weight is 1/4, 1/8 or 1/10. So `boo = 1/w` is a whole number, and `bpow` returns from `bpowi` (BNum.sol:108-126). `bpowApprox` is never called in any join or exit. Where it did run (in 109 swap calculations), it stopped at a term below 1e-10, and its residual against the exact power was at most 4.2e-11 relative.
- **Direction closes the loop; precision does not.** FP127, FP256 and 200-digit mpmath, each rounded toward the pool (ceil in, floor out), give 2 for every join and 0 for every dust exit, so every one of them reverts on the attacker's own limits. BNum's own 18-decimal ratio, kept on a 10^-18 grid and rounded up once at the end, gives the same answers. But the same exact formula rounded once *to nearest* only blocks these calls because the attacker tuned them to the deployed rounding. Re-tuned to nearest-once from the same state, one join/exit cycle in pool 1 still nets 6.987% of the BPT supply (deployed: 7.035%). Toward the pool it nets -0.0548%, a loss. The deployed ratio had 18 correct digits. What it lacked was a rounding direction at the token grid.

## What happened

All five attacks followed the same loop. The attacker flash-borrowed from Morpho Blue, SparkLend Pool (Aave v3 fork; marketId "Spark Protocol"), Uniswap V3 pool. The loans were nested. With them, the attacker used public swaps to push one token's pool balance down to a few raw units (`swapExactAmountOut` for 1 unit at a time near the end, which `MAX_OUT_RATIO` allows down to a balance of 2). It then alternated a join of 1 unit for a chosen BPT amount with an exit of a smaller BPT amount for 1 unit. Each join/exit pair returns the balance to where it started and leaves the attacker with more BPT. Finally the attacker swapped the token back in and redeemed the accumulated BPT. In four pools that was one proportional `exitPool`; in the eight-token pool it was single-token exits with `minAmountOut = 0`. `MIN_BALANCE` is checked only in `bind`/`rebind`, so nothing stops a swap from taking a balance to dust.

| # | tx | block, time (UTC) | pool | tokens (weight) | swap fee | attacked token | its balance before → in the loop | joins / exits | BPT minted / burned in the loop | BPT redeemed at the end |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | [`0x72510b25…1aff`](https://etherscan.io/tx/0x72510b257cc09bde8435b83ac1636f9498ffc353583330600b5b8da43d0d1aff) | 25872274, 02:28:23 | `0x2257aaac34bcb27900291f7b84ee2565a6cbac57` | DPI (25%), USDC (25%), WETH (25%), WBTC (25%) | 0.5% | WBTC | 35748405 → 3 units | 100 / 104 | 6,686.919700 / 2,278.111648 | 4,408.808052 (`exitPool`) |
| 2 | [`0xeef31155…2c2c`](https://etherscan.io/tx/0xeef311556b2a2a5be915d1d21785f47311faab26051d5cc832f701fd4ced2c2c) | 25872328, 02:39:11 | `0x1373e57f764a7944bdd7a4bd5ca3007d496934da` | DAI (12.5%), USDC (12.5%), WETH (12.5%), MKR (12.5%), UMA (12.5%), LINK (12.5%), SNX (12.5%), TRB (12.5%) | 1% | USDC | 8528380659 → 3 units | 56 / 124 | 235,182.015693 / 88,826.005191 | 146,356.010502 (33 × `exitswapPoolAmountIn`, min 0) |
| 3 | [`0x37e47f0f…6628`](https://etherscan.io/tx/0x37e47f0f5f4ec77e96d220410f6aece30a7589d478c6b17badeb55aa70d66628) | 25872446, 03:03:11 | `0x9b208194acc0a8ccb2a8dcafeacfbb7dcc093f81` | USDC (25%), DAI (35%), WETH (40%) | 0.07% | USDC | 9637674448 → 3 units | 80 / 84 | 2,051.946786 / 699.633629 | 1,352.313157 (`exitPool`) |
| 4 | [`0xbaedc537…e111`](https://etherscan.io/tx/0xbaedc537df2075c3edbd43bbd918363be4b9c090971ce4f9592c1ddb3061e111) | 25872477, 03:09:23 | `0x3b260cf977df1ff8d87960064daee2ce491a1b91` | UNI-V2 (40%), WETH (30%), renBTC (10%), LINK (10%), UNI (10%) | 2% | renBTC | 10707111 → 3 units | 102 / 106 | 131,684.384543 / 44,219.841991 | 87,464.542552 (`exitPool`) |
| 5 | [`0xb2d84f92…7332`](https://etherscan.io/tx/0xb2d84f926ba84a707d91aa1e1b5fda9565d8db414eece9bd93ced733f8417332) | 25872613, 03:36:47 | `0xcd461b73d5fc8ea1d69a600f44618bdfac98364d` | WETH (30%), UNI-V2 (40%), WBTC (10%), SNX (10%), LINK (10%) | 1% | WBTC | 2755120 → 3 units | 100 / 104 | 8,505.186204 / 2,857.069298 | 5,648.116906 (`exitPool`) |

The "4,408.8 BPT" in the reports is the first pool's final `exitPool` of 4408808051748945978379 wei. It is the net of the loop: 100 one-satoshi joins minted 6,686.919700 BPT, 104 one-satoshi exits burned 2,278.111648, and the difference is 4408808051748945978379 wei, exactly the amount redeemed. No single satoshi minted 4,408.8 BPT. Each one bought between 4.974% and 10.67% of the supply at the time. The pool's supply before the attack was 6.076387 BPT.

What left each pool (balance before the attack → after, in token units; from the replay):

| # | token | before | after | taken |
|---|---|---|---|---|
| 1 | DPI | 546.83609422 | 0.57099095 | 99.90% |
| 1 | USDC | 27,744.378914 | 29.654069 | 99.89% |
| 1 | WETH | 11.46045556 | 0.01207425 | 99.89% |
| 1 | WBTC | 0.35748405 | 0.00037669 | 99.89% |
| 2 | DAI | 8,507.59643397 | 1,587.51332357 | 81.34% |
| 2 | USDC | 8,528.380659 | 1,584.652082 | 81.42% |
| 2 | WETH | 3.52686481 | 0.64621423 | 81.68% |
| 2 | MKR | 5.36000902 | 0.98236533 | 81.67% |
| 2 | UMA | 23,352.82189923 | 4,275.88710237 | 81.69% |
| 2 | LINK | 765.23401912 | 139.03582275 | 81.83% |
| 2 | SNX | 40,585.20007794 | 7,429.74303458 | 81.69% |
| 3 | USDC | 9,637.674448 | 37.144283 | 99.61% |
| 3 | DAI | 13,497.90296101 | 52.01861909 | 99.61% |
| 3 | WETH | 6.41403444 | 0.02471227 | 99.61% |
| 4 | UNI-V2 | 4,541.42198848 | 285.80055527 | 93.71% |
| 4 | WETH | 3.12342992 | 0.19665246 | 93.70% |
| 4 | renBTC | 0.10707111 | 0.00673827 | 93.71% |
| 4 | LINK | 224.66155879 | 14.13783781 | 93.71% |
| 4 | UNI | 488.26719515 | 30.73833460 | 93.70% |
| 5 | WETH | 2.65216154 | 0.17180512 | 93.52% |
| 5 | UNI-V2 | 1,093.63121321 | 70.82054219 | 93.52% |
| 5 | WBTC | 0.02755120 | 0.00178487 | 93.52% |
| 5 | SNX | 10,188.19811113 | 660.02267671 | 93.52% |
| 5 | LINK | 191.94860933 | 12.43508754 | 93.52% |

## The decisive join, in integers

Pool 1 (`0x2257aaac34bcb27900291f7b84ee2565a6cbac57`), call 53 of 290 in tx `0x72510b25…1aff` (LOG_CALL at log index 0x13a) is the first join against a WBTC balance of 3 satoshi: `joinswapPoolAmountOut(WBTC, 689646715905234062, 1)` with pool supply 6464513554335253717. `test_decisive_join` asserts every integer below; `test_decisive_join_matches_the_replay` checks that this is the replay's state at that call.

| step (BMath.sol) | deployed integer | value | exact |
|---|---|---|---|
| normalizedWeight = bdiv(wI, tW) (:167) | 250000000000000000 | 0.25 | 0.25 |
| poolRatio = bdiv(pS + pAo, pS) (:169) | 1106681919700321592 | 1.106681919700321592 | 1.106681919700321592346648 |
| boo = bdiv(BONE, normalizedWeight) (:172) | 4000000000000000000 | 4 | 4 |
| tokenInRatio = bpow(poolRatio, boo) (:173) → bpowi, no series | 1499999999999999997 | 1.499999999999999997 | 1.499999999999999999663091 |
| newTokenBalanceIn = bmul(tokenInRatio, 3) (:174) | 4 | 4.499999999999999991 → **4** | 4.499999999999999998989274 |
| tokenAmountInAfterFee (:175) | 1 | 1 | 1.499999999999999998989274 |
| zar = bmul(1 − 0.25, 0.5%) (:179) | 3750000000000000 | 0.00375 | 0.00375 |
| tokenAmountIn = bdiv(afterFee, 1 − zar) (:180) | 1 | 1.0038 → **1** | **1.505646173149309911156109** |

The attacker sized `poolAmountOut` so that BNum's ratio landed 3 × 10^-18 below 1.5. That puts the new balance 9 × 10^-18 satoshi below the half-way point between 4 and 5 satoshi, so it rounds down. The integer survives in every pool: in the replay the deployed `tokenInRatio` at a balance of 3 is always just under 1.5 (1499999999999999988, 1499999999999999997). At a balance of 7 it is just under 8.5/7, and at the eight-token pool's USDC balance of 38 it is just under 39.5/38.

## Every join and exit: deployed, toward the pool, and exact

Each column computes the same `calcSingleInGivenPoolOut` / `calcSingleOutGivenPoolIn` from the same on-chain state (the replay's state at that call). Every column except *deployed* converts to token units once, toward the pool: ceil for an amount in, floor for an amount out. *BNum, one rounding* keeps BNum's own 18-decimal `tokenInRatio`, holds the amount on a 10^-18 grid, and rounds once at the end. FP127 and FP256 evaluate `b·expm1((tW/w)·log1p(±pA/pS))` with the fee factor. *Digits* is −log10 of the relative error against 200-digit mpmath before rounding. *Pays?* asks whether the attacker's own limit (maxAmountIn = 1, minAmountOut = 1) would still be met. The last column rounds the exact value to the nearest unit once, for the section after this one.

| # | call | n | balance (units) | deployed | exact (range) | BNum, one rounding | FP127 | FP256 | exact, rounded | FP127 digits (min) | FP256 digits (min) | pays? | exact, nearest once |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | join, max in 1 | 100 | 3, 4, 5, 7 | 1 | 1.5056462 – 1.5056462 | 2 | 2 | 2 | 2 | 37.24 | 70.89 | no | 2 |
| 1 | exit, min out 1 | 104 | 4, 5, 6, 7, 8 | 1 | 0.498125 – 0.498125 | 0 | 0 | 0 | 0 | 36.89 | 70.96 | no | 0 |
| 2 | join, max in 1 | 56 | 3, 4, 5, 7, 8, 10, 11, 13, 14, 16, 18, 20, 21, 23, 25, 27, 28, 30, 32, 34, 36, 38 | 1 | 1.5132409 – 1.5132409 | 2 | 2 | 2 | 2 | 36.24 | 70.99 | no | 2 |
| 2 | exit, min out 1 | 91 | 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | 1 | 0.495625 – 0.495625 | 0 | 0 | 0 | 0 | 35.71 | 71.01 | no | 0 |
| 3 | join, max in 1 | 80 | 3, 4, 5, 7 | 1 | 1.5007879 – 1.5007879 | 2 | 2 | 2 | 2 | 37.34 | 71.04 | no | 2 |
| 3 | exit, min out 1 | 84 | 4, 5, 6, 7, 8 | 1 | 0.4997375 – 0.4997375 | 0 | 0 | 0 | 0 | 36.88 | 70.97 | no | 0 |
| 4 | join, max in 1 | 102 | 3, 4, 5, 7 | 1 | 1.5274949 – 1.5274949 | 2 | 2 | 2 | 2 | 36.92 | 70.87 | no | 2 |
| 4 | exit, min out 1 | 106 | 4, 5, 6, 7, 8 | 1 | 0.491 – 0.491 | 0 | 0 | 0 | 0 | 36.47 | 70.87 | no | 0 |
| 5 | join, max in 1 | 100 | 3, 4, 5, 7 | 1 | 1.5136226 – 1.5136226 | 2 | 2 | 2 | 2 | 36.83 | 70.90 | no | 2 |
| 5 | exit, min out 1 | 104 | 4, 5, 6, 7, 8 | 1 | 0.4955 – 0.4955 | 0 | 0 | 0 | 0 | 36.39 | 70.92 | no | 0 |

Pool 2 was redeemed with 33 single-token exits at real size (`minAmountOut = 0`). Those are not part of the rounding loop. Their deployed amounts differ from the exact ones by at most 2.12e-17 relative, which is BNum's 18 digits doing what it promises.

## Precision or direction?

The last column of the table above also blocks these calls: 1.5056 rounds to 2, and 0.498 rounds to 0. That is only because the attacker tuned each call to the deployed arithmetic. The question for a pool is what an attacker can get once it tunes to the pool's rule. Each row below starts from the state of each pool's first join at a balance of 3 units. It solves, at 200 digits, for the most BPT one unit buys on the join and the least BPT one unit costs on the exit that follows (at a balance of 4, from the supply after the join). Then it reports what one join/exit cycle nets the attacker. The balance is back at 3 after each cycle, so the cycle repeats.

| # | rule | BPT for 1 unit in (% of supply) | BPT for 1 unit out (% of supply) | net per cycle (% of supply) |
|---|---|---|---|---|
| 1 | deployed (the attacker's own amounts) | 0.689647 (10.67%) | 0.234884 (3.283%) | **7.035%** |
| 1 | exact formula, nearest once (FP127 / FP256 / mpmath) | 0.687410 (10.63%) | 0.235741 (3.296%) | **6.987%** |
| 1 | exact formula, toward the pool (ceil in, floor out) | 0.480430 (7.432%) | 0.483974 (6.969%) | **-0.05482%** |
| 2 | deployed (the attacker's own amounts) | 3447.439201 (5.199%) | 1154.692308 (1.655%) | **3.458%** |
| 2 | exact formula, nearest once (FP127 / FP256 / mpmath) | 3421.974184 (5.161%) | 1165.086654 (1.671%) | **3.404%** |
| 2 | exact formula, toward the pool (ceil in, floor out) | 2409.114426 (3.633%) | 2451.677323 (3.568%) | **-0.06419%** |
| 3 | deployed (the attacker's own amounts) | 0.827210 (10.67%) | 0.281736 (3.283%) | **7.035%** |
| 3 | exact formula, nearest once (FP127 / FP256 / mpmath) | 0.826834 (10.66%) | 0.281879 (3.285%) | **7.028%** |
| 3 | exact formula, toward the pool (ceil in, floor out) | 0.577940 (7.453%) | 0.578534 (6.944%) | **-0.007659%** |
| 4 | deployed (the attacker's own amounts) | 270.261461 (4.138%) | 90.217846 (1.326%) | **2.757%** |
| 4 | exact formula, nearest once (FP127 / FP256 / mpmath) | 266.169494 (4.075%) | 91.921979 (1.352%) | **2.668%** |
| 4 | exact formula, toward the pool (ceil in, floor out) | 187.590142 (2.872%) | 194.534964 (2.895%) | **-0.1063%** |
| 5 | deployed (the attacker's own amounts) | 18.503229 (4.138%) | 6.176691 (1.326%) | **2.757%** |
| 5 | exact formula, nearest once (FP127 / FP256 / mpmath) | 18.363342 (4.107%) | 6.234465 (1.339%) | **2.712%** |
| 5 | exact formula, toward the pool (ceil in, floor out) | 12.947067 (2.895%) | 13.183299 (2.865%) | **-0.05283%** |

With full precision and round-to-nearest, the loop is almost exactly as profitable as it was on chain. 38 or 71 digits do not help when the last step can round half a unit in the caller's favour. Rounded toward the pool, the loop runs backwards: each cycle leaves the swap fee in the pool. `test_precision_without_direction_still_pays` and `test_direction_closes_the_loop` assert pool 1's row in FP127 and FP256 (`score` checks the test's literals against these solutions).

## Where the half unit goes

deployed − exact, split along the deployed steps (the parts sum to the total). *power* is the 18-decimal ratio (`bdiv` of the supplies, then `bpowi`'s `bmul` squarings) against the exact power, times the balance. *grid* is `bmul(ratio, balance)` rounded half up to a whole token unit. *fee* is the fee factor on BNum's grid plus the last `bdiv` / `bmul` onto whole units. Token units; the range is over the calls.

| # | call | total | power (18-dec ratio, bpowi) | grid (new balance to whole units) | fee step |
|---|---|---|---|---|---|
| 1 | join | -0.5056 … -0.5056 | -1.531e-17 … -5.048e-18 | -0.5019 … -0.5019 | -0.003764 … -0.003764 |
| 1 | dust exit | 0.5019 … 0.5019 | 2.958e-18 … 1.494e-17 | 0.4981 … 0.4981 | 0.00375 … 0.00375 |
| 2 | join | -0.5132 … -0.5132 | -2.01e-16 … -1.375e-17 | -0.5044 … -0.5044 | -0.008827 … -0.008827 |
| 2 | dust exit | 0.5044 … 0.5044 | 5.763e-18 … 2.101e-16 | 0.4956 … 0.4956 | 0.00875 … 0.00875 |
| 3 | join | -0.5008 … -0.5008 | -1.761e-17 … -7.707e-18 | -0.5003 … -0.5003 | -0.0005253 … -0.0005253 |
| 3 | dust exit | 0.5003 … 0.5003 | 3.107e-18 … 1.478e-17 | 0.4997 … 0.4997 | 0.000525 … 0.000525 |
| 4 | join | -0.5275 … -0.5275 | -4.256e-17 … -2.142e-17 | -0.5092 … -0.5092 | -0.01833 … -0.01833 |
| 4 | dust exit | 0.509 … 0.509 | 1.067e-17 … 4.554e-17 | 0.491 … 0.491 | 0.018 … 0.018 |
| 5 | join | -0.5136 … -0.5136 | -4.202e-17 … -2.115e-17 | -0.5045 … -0.5045 | -0.009082 … -0.009082 |
| 5 | dust exit | 0.5045 … 0.5045 | 1.071e-17 … 4.595e-17 | 0.4955 … 0.4955 | 0.009 … 0.009 |

The 18-decimal maths in front of the grid (the ratio and `bpowi`) is off by at most 2.1e-16 token units. On a join, the grid step alone moves the result by −0.5 units; on an exit, by +0.5. The fee step rounds the remaining ≈ 1.004 (join) or ≈ 0.996 (exit) to 1.

## bpowApprox: measured, and not the step that loses

`bpow(base, exp)` (BNum.sol:108-126) splits the exponent. The whole part goes to `bpowi`, square and multiply with `bmul` at every step (BNum.sol:89-103). Only a fractional part goes to `bpowApprox` (BNum.sol:128-161), the binomial series of (1 + x)^a, which stops after the first term below `BPOW_PRECISION` = BONE / 10^10 = 10^8 wei = 10^-10 (BConst.sol:37). That stopping term is still added.

- **In the 438 joins and 522 single-token exits: zero calls.** The exponent is tW/wI = 4, 8 or 10 (`boo % BONE == 0`, asserted on every call in the Foundry replay). The decisive ratio comes from two or three `bmul` squarings, each rounding half up at 10^-18.
- **In the swaps that built the dust balance: 109 calls** (pools 3, 4, 5, where weight ratios such as 12.5/17.5 are not whole). |x| = |base − 1| ranged 0.000548 – 0.355. The loop ran 3 – 17 iterations (median 15); 0 of them ended on a term that rounded to zero rather than on the tolerance. The relative residual against the exact power (base^frac at 200 digits) is 1.5e-16 – 4.2e-11. Times the balance it multiplies, that is at most 3.58e+12 raw units of DAI (3.58e-6 DAI, in calcInGivenOut). For an 18-decimal token with a large balance, this is more than one raw unit: the stopping rule does show in swap amounts. It is not what moved this attack.
- **The same series, run in exact arithmetic to each ruler's tolerance**, needs 3 – 17 terms to reach 10^-10 (BNum's own rule without BNum's rounding), 12 – 78 terms to reach 2^-128 (FP127's ulp at 1), and 22 – 150 to reach 2^-237 (FP256's relative ulp). The series does converge, and a finer ruler only means more terms. Had the series run at the decisive join, the largest residual measured here (4.2e-11) times a 3-unit balance would be 1.3e-10 units, about nine orders of magnitude below the half-unit grid step that decided the outcome.

For the talk: in this incident the stopping ruler did not decide the answer, because the series never ran where it mattered. What decided it was a coarser ruler: whole token units, applied in the middle of the computation, rounding to nearest, against a balance that the attacker had made three units long.

## Provenance

- **Transactions**: the five listed in SlowMist's alert (https://x.com/SlowMist_Team/status/2094272540193722744). Receipts and state come from `https://mainnet.gateway.tenderly.co`, keyless and read-only (eth_getTransactionReceipt, eth_call and eth_getCode at block − 1, eth_getLogs). Nothing was signed or sent.
- **Calls**: decoded from each pool's anonymous `LOG_CALL(bytes4 indexed sig, address indexed caller, bytes data)`, which BPool's `_logs_` modifier emits with the full calldata. Results come from `LOG_SWAP` / `LOG_JOIN` / `LOG_EXIT`. 1417 calls in total; 1883 logged amounts reproduced exactly by the Python transcription and again by the Solidity one, swaps and `exitPool` included.
- **State**: `getCurrentTokens`, `getDenormalizedWeight`, `getBalance` (the pool's internal record, which is what the maths reads), `getTotalDenormalizedWeight`, `getSwapFee` and `totalSupply` at block − 1. For every pool, `eth_getLogs` over the attack block shows no earlier transaction touching it, so block − 1 is the attack's starting state. All five pools were finalized with public swap on, and `BFactory.isBPool(pool)` is true for each.
- **Code**: the BPool source verified on Etherscan for `0x2257aaac34bcb27900291f7b84ee2565a6cbac57` (v0.5.12+commit.7709ece9, optimizer 2000 runs, default EVM) was fetched through Routescan's Etherscan-compatible API. Its files are byte-identical to the sources verified for BFactory `0x9424B1412450D0f8Fc2255FAf6046b98213B76Bd` (yes). `fetch` recompiles them with solc 0.5.12 (sha256-checked from binaries.soliditylang.org) under `contracts/`, which is balancer-labs/balancer-core's layout and is what the metadata hash records. The runtime bytecode, metadata included, equals `eth_getCode` for all five pools (yes, yes, yes, yes, yes; runtime keccak `0x974df1c33872ba8aab782be5117ff348802441590f84ed7701d734bb9c21683e`).
- **Transcribed lines** (file sha256 in the JSON): `BConst.sol:19` BONE; `BConst.sol:35` MIN_BPOW_BASE; `BConst.sol:36` MAX_BPOW_BASE; `BConst.sol:37` BPOW_PRECISION; `BConst.sol:39` MAX_IN_RATIO; `BConst.sol:40` MAX_OUT_RATIO; `BConst.sol:26` EXIT_FEE; `BConst.sol:31` MIN_BALANCE; `BNum.sol:20-25` btoi; `BNum.sol:27-32` bfloor; `BNum.sol:34-41` badd; `BNum.sol:43-50` bsub; `BNum.sol:52-61` bsubSign; `BNum.sol:63-73` bmul; `BNum.sol:75-86` bdiv; `BNum.sol:89-103` bpowi; `BNum.sol:108-126` bpow; `BNum.sol:128-161` bpowApprox; `BMath.sol:28-43` calcSpotPrice; `BMath.sol:55-74` calcOutGivenIn; `BMath.sol:86-105` calcInGivenOut; `BMath.sol:156-182` calcSingleInGivenPoolOut; `BMath.sol:195-224` calcSingleOutGivenPoolIn; `BPool.sol:392-420` exitPool; `BPool.sol:423-484` swapExactAmountIn; `BPool.sol:486-546` swapExactAmountOut; `BPool.sol:584-618` joinswapPoolAmountOut; `BPool.sol:620-656` exitswapPoolAmountIn.
- **Flash loans** (from the receipts): tx 1: Morpho Blue, SparkLend Pool (Aave v3 fork; marketId "Spark Protocol"), Uniswap V3 pool; tx 2: Morpho Blue, SparkLend Pool (Aave v3 fork; marketId "Spark Protocol"); tx 3: Morpho Blue, SparkLend Pool (Aave v3 fork; marketId "Spark Protocol"); tx 4: Morpho Blue, SparkLend Pool (Aave v3 fork; marketId "Spark Protocol"); tx 5: Morpho Blue, SparkLend Pool (Aave v3 fork; marketId "Spark Protocol").

## Where this differs from the reports

- "A pool drained of ~$234K": the attacker drained five BPools in five transactions over 68 minutes. Whether $234K covers one pool or all five is not stated. This replay counts tokens, not dollars (table above).
- "1 satoshi minted 4,408.8 BPT": each 1-satoshi join minted 4.974–10.67% of the supply at that moment (0.3022 to 440.0331 BPT, growing as the attacker's own BPT grew the supply). The figure 4,408.8 is the net of 100 joins and 104 exits, redeemed in one `exitPool`.
- "Rounded down to 1 satoshi" by "18-decimal fixed-point maths": the 18-decimal part was accurate to 18 digits. The rounding that mattered is `bmul` of that ratio by a balance in raw units, which rounds to the nearest satoshi (or 10^-6 USDC). The required input is 1.5 units and rounds half up to 1, because the attacker placed it just below the half. The exits get the mirror image: 0.5 units paid out as 1.
- "Flash loans from Aave, Spark, Morpho and Uniswap V3": the receipts show SparkLend (an Aave v3 fork) and Morpho Blue in every transaction, and a Uniswap V3 flash in the first. No Aave v3 Pool `FlashLoan` event appears.
- Two of the five pools were not WBTC pools: pool 3's attacked token is USDC and pool 4's is renBTC. The eight-token pool 2 was attacked on USDC (with WETH and DAI joins and exits too).

## What fixed it

Nothing in V1 has changed. BPools have no admin pause and no upgrade path, and a finalized pool's maths is fixed. On 31 August Balancer warned LPs to withdraw from the deprecated V1 pools, proportionally, through legacy.balancer.fi; the pools are non-pausable, and Balancer said other products were unaffected. That is as reported by The Defiant, ChainCatcher and CryptoTicker; the original post was not retrievable here. I found no Balancer advice addressed to forks. The forks' exposure follows from this replay: any fork that keeps `calcSingleInGivenPoolOut` / `calcSingleOutGivenPoolIn` on raw balances with half-up `bmul`, and lets swaps take a balance to dust, is open to the same loop. The repair the numbers point to is rounding toward the pool at the token grid: up for amounts in, down for amounts out. Any of the four *toward the pool* columns above blocks every step of the loop. Balancer V2 does this in its FixedPoint (`mulUp`/`divUp` versus `mulDown`/`divDown`, chosen per step in its WeightedMath), and it scales balances to 18 decimals before any of that maths. A minimum balance enforced on swaps, not only in `bind`, would also have stopped the setup.

## Caveat

The counterfactuals are each evaluated at the on-chain state of that call. In a world where the pool rounded toward itself, the first join would have reverted and the later states would never have existed. The test shows that every step of this attack would fail; it does not show that no other sequence could profit.

## Reproduce

```
forge test --match-path test/replays/BalancerV1.t.sol        # offline: replay, asserts, decisive join
uv run scripts/replays/balancer_v1.py score                  # offline: runs the test, scores at 200 digits, writes this page
uv run scripts/replays/balancer_v1.py fetch                  # network (read-only): refetch receipts, state, source; recompile
```

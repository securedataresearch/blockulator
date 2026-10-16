# Deployed accrual: Aave v3 and Morpho Blue against their stated ideals

Generated 2026-10-16 by `make accrual-deployed` (`uv run scripts/accrual/accrual.py`). Survey block 26206698 (2026-10-16 17:49 UTC). Data: `accrual-deployed.json`.

## What is measured

Each case is one accrual: a balance, a rate, and the seconds since the last update. The deployed integer maths (the pinned submodules, proven byte-identical to mainnet below) produces the new balance; mpmath at 200 digits produces the formula the protocol says it approximates. **Digits** = −log10(|error| / |true value|), reported for the accrued interest (the number a lender or borrower is owed) and for the whole balance. **err** is deployed − truth in token units (negative: the protocol accrues less than its stated formula). The error is split into the **approximation** (the truncated series, computed in exact arithmetic) and the **rounding** (ray/wad grids, the rate held as an integer per second, balances in token units). FP127 and FP256 compute the same stated formula from the same integers with their own exp/ln/pow and are not rounded to token units; *grid* is the most digits any answer rounded to token units could show.

Truths: Aave borrow — e^(rate·years) (the body comment's "ideal formula"); the per-second binomial (1 + rate/SPY)^seconds named in the doc comment is reported alongside in the JSON and differs by less than rate²·t/(2·SPY²). Aave supply — per-second compounding of the liquidity rate (the APY Aave displays); the index itself is simple interest by design. Morpho — e^(∫ rate dt) with the AdaptiveCurveIrm's stated ideal rate path (rate at target r0·e^(50/yr·err·t), held in [0.1%, 200%]/yr, curve ×4 above target), at the utilisation of the last update (the IRM's own stated assumption).

## Summary

Normal operation is accurate. Under realistic rates and idle times the Aave borrow index is within the token's own decimals or a few millionths of a token per million, and Morpho at its 90% target is the same. The digits go where the stated ideal and the shipped shortcut diverge:

- **Morpho, fully utilised market untouched for a day** (`morpho-u100-10pct-1d`): 10000000.0 USDC, idle 1 d. True interest 11751.9; deployed off by 3.08123 USDC (2.622e-4 of the interest, 3.58 digits; balance 6.51). Series -7.93884e-7, grids -9.56256e-7, IRM rate path 3.08123 (trapezoid 4.59666). FP127 30.29 digits, FP256 68.54.
- **Morpho, fully utilised market untouched for a week** (`morpho-u100-10pct-7d`): 10000000.0 USDC, idle 7 d. True interest 129539.0; deployed off by 2478.09 USDC (0.01913 of the interest, 1.72 digits; balance 3.61). Series -0.0123607, grids -6.45252e-8, IRM rate path 2478.1 (trapezoid 2488.26). FP127 30.29 digits, FP256 70.0.
- **Morpho at the 800% cap for a week** (`morpho-u100-max-7d`): 10000000.0 USDC, idle 7 d. True interest 1658200.0; deployed off by -238.14 USDC (1.436e-4 of the interest, 3.84 digits; balance 4.69). Series -238.14, grids -3.0937e-7, IRM rate path -0.0000149245 (trapezoid -3.73113e-6). FP127 31.95 digits, FP256 71.44.
- **Aave, slope2 300% asset at 100% utilisation for a week** (`aave-link-u100-borrow-7d`): 1000000.0 LINK, idle 7 d. True interest 60644.5; deployed off by -0.506637 LINK (8.354e-6 of the interest, 5.08 digits; balance 6.32). Series -0.506637, grids 4.79186e-19. FP127 37.67 digits, FP256 70.2.
- **Aave supply index (simple interest) vs the displayed APY, USDC at 100% for a day** (`aave-usdc-u100-supply-1d`): 1000000.0 USDC, idle 1 d. True interest 357.598; deployed off by -0.0639223 USDC (1.788e-4 of the interest, 3.75 digits; balance 7.19). Series -0.0639222, grids -4.92879e-9. FP127 30.83 digits, FP256 63.28.
- **Control: Aave USDC borrow at 100% utilisation for a day** (`aave-usdc-u100-borrow-1d`): 1000000.0 USDC, idle 1 d. True interest 397.339; deployed off by 1.228e-7 USDC (3.091e-10 of the interest, 9.51 digits; balance 12.91). Series -1.03782e-9, grids 1.23838e-7. FP127 35.42 digits, FP256 67.97.

Signs: Aave and Morpho's series both undercharge (as Aave's comment says); the AdaptiveCurveIrm's two-panel trapezoid overcharges whenever the rate at target is moving, because e^(kt) is convex, and the stored rate at target drifts by the wExp error (-3.867e-4 relative after the one-day case).

## Provenance

| contract | address | source pin | runtime bytecode |
|---|---|---|---|
| Aave v3 Pool implementation (Core, POOL_REVISION 11) | `0x728a138a4823392c2efa55e028d434f526fe03cf` | aave-v3-origin v3.7.0 `cff15de6` | equal (21146 B; 33 immutable slots masked; block 26206682) |
| Aave SupplyLogic | `0x584C7d8c4cb05304FE5Ac7fbc97f20A10Fb07564` | aave-v3-origin v3.7.0 | equal (10302 B; 0 immutable slots, library address masked; block 26206682) |
| Aave BorrowLogic | `0x52Da0ce88202D1542543598D1e1e27F0d344726A` | aave-v3-origin v3.7.0 | equal (9587 B; 0 immutable slots, library address masked; block 26206682) |
| Aave LiquidationLogic | `0x96D5686812e33Ab509ECCDb38C89d15607B2a413` | aave-v3-origin v3.7.0 | equal (12101 B; 0 immutable slots, library address masked; block 26206682) |
| Aave FlashLoanLogic | `0x6D414cd0d5eAf8C43200ac0c325A7E2Ad83B8be6` | aave-v3-origin v3.7.0 | equal (8227 B; 0 immutable slots, library address masked; block 26206682) |
| Aave PoolLogic | `0xD70593841C57cbaA04957cc3EAcE95708e48853b` | aave-v3-origin v3.7.0 | equal (7311 B; 0 immutable slots, library address masked; block 26206682) |
| Morpho Blue | `0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb` | morpho-blue v1.0.0 `55d2d993` | equal (15623 B; 2 immutable slots masked; block 26206682) |
| AdaptiveCurveIrm | `0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC` | morpho-blue-irm v1.0.0 `a7d9cce3` | equal (2717 B; 2 immutable slots masked; block 26206682) |

The Pool proxy is `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`. Aave deployed v3.7 from a private mirror (`lib/aave-v3-origin-private`); every verified file is byte-identical to the public tag except LiquidationLogic.sol, which differs in whitespace only, and the recompiled runtime is equal. `scripts/accrual/verify_deployed.py check` recompiles every target from `lib/` with the verified compiler and settings and compares to `eth_getCode`.

Live equivalence at the survey block: the harness reproduced `getReserveNormalizedVariableDebt` / `getReserveNormalizedIncome` for 74 Aave reserve sides and the deployed IRM's `borrowRateView` for 252 Morpho markets exactly (assertEq in the harness).

## What the protocols claim

- **Aave v3.7.0**, MathUtils.calculateCompoundedInterest, doc comment: To avoid expensive exponentiation, the calculation is performed using a binomial approximation: (1+x)^n = 1+n*x+[n/2*(n-1)]*x^2+[n/6*(n-1)*(n-2)*x^3... The approximation slightly underpays liquidity providers and undercharges borrowers, with the advantage of great gas cost reductions.
- **Aave v3.7.0**, MathUtils.calculateCompoundedInterest, body: calculations compound interest using the ideal formula - e^(rate per year * number of years) ... the contract uses a polynomial approximation of the ideal formula. Code: x = rate*exp/SECONDS_PER_YEAR; return RAY + x + x.rayMul(x/2 + x.rayMul(x/6)) (the first three terms of e^x - 1, not the binomial with (n-1), (n-2) the doc comment describes).
- **Aave v3.7.0**, MathUtils.calculateLinearInterest / ReserveLogic._updateIndexes: Supply side: the liquidity index grows by simple interest 1 + rate*dt/SECONDS_PER_YEAR between updates (no approximation is claimed). Aave's own interface library computes the displayed supply APY as per-second compounding of that rate: aave/aave-utilities@2d0db501 math-utils formatters/reserve/index.ts, supplyAPY = calculateCompoundedRate({rate: liquidityRate, duration: SECONDS_PER_YEAR}) = rayPow(1 + rate/SECONDS_PER_YEAR, SECONDS_PER_YEAR) - 1.
- **Morpho Blue v1.0.0**, MathLib.wTaylorCompounded: Returns the sum of the first three non-zero terms of a Taylor expansion of e^(nx) - 1, to approximate a continuous compound interest rate.
- **AdaptiveCurveIrm v1.0.0**, _borrowRate: avg = 1/T * integral_0^T curve(startRateAtTarget*exp(speed*x), err) dx. The integral is approximated with the trapezoidal rule ... With N = 2. Also: 'The speed is assumed constant between two updates, but it is in fact not constant because of interest. So the rate is always underestimated.'
- **AdaptiveCurveIrm v1.0.0**, ExpLib.wExp: Returns an approximation of exp: x = q ln2 + r, |r| <= ln2/2, e^r by a 2nd-order Taylor polynomial.

## Stylised cases (live parameter sets, chosen idle times)

| case | rate | idle | principal | true interest | err (tokens) | digits (interest) | digits (balance) | grid | FP127 digits (interest) | FP256 digits (interest) |
|---|---|---|---|---|---|---|---|---|---|---|
| `aave-usdc-u100-borrow-1d` | 14.5% | 1 d | 1000000.0 USDC | 397.339 | 1.228e-7 | 9.51 | 12.91 | 8.9 | 35.42 | 67.97 |
| `aave-usdc-u100-supply-1d` | 13.05% | 1 d | 1000000.0 USDC | 357.598 | -0.0639223 | 3.75 | 7.19 | 8.85 | 30.83 | 63.28 |
| `aave-usdc-u100-borrow-7d` | 14.5% | 7 d | 1000000.0 USDC | 2784.69 | -2.16379e-6 | 9.11 | 11.67 | 9.75 | 35.98 | 69.06 |
| `aave-usdc-u100-supply-7d` | 13.05% | 7 d | 1000000.0 USDC | 2505.87 | -3.13446 | 2.9 | 5.5 | 9.7 | 30.83 | 63.27 |
| `aave-weth-u100-borrow-7d` | 8.2% | 7 d | 1000000.0 WETH | 1573.84 | -2.54919e-7 | 9.79 | 12.59 | 21.5 | 35.9 | 68.66 |
| `aave-link-u100-borrow-1h` | 307% | 1 h | 1000000.0 LINK | 350.518 | -6.28574e-10 | 11.75 | 15.2 | 20.85 | 35.05 | 67.96 |
| `aave-link-u100-supply-1h` | 245.6% | 1 h | 1000000.0 LINK | 280.405 | -0.0392951 | 3.85 | 7.41 | 20.75 | 31.57 | 64.8 |
| `aave-link-u100-borrow-1d` | 307% | 1 d | 1000000.0 LINK | 8446.43 | -0.000208882 | 7.61 | 9.68 | 22.23 | 37.25 | 69.36 |
| `aave-link-u100-supply-1d` | 245.6% | 1 d | 1000000.0 LINK | 6751.46 | -22.6888 | 2.47 | 4.65 | 22.13 | 31.57 | 64.8 |
| `aave-link-u100-borrow-7d` | 307% | 7 d | 1000000.0 LINK | 60644.5 | -0.506637 | 5.08 | 6.32 | 23.08 | 37.67 | 70.2 |
| `aave-link-u100-supply-7d` | 245.6% | 7 d | 1000000.0 LINK | 48228.3 | -1126.89 | 1.63 | 2.97 | 22.98 | 31.56 | 64.79 |
| `aave-link-u100-borrow-30d` | 307% | 30 d | 1000000.0 LINK | 287019.0 | -177.806 | 3.21 | 3.86 | 23.76 | 38.17 | 70.9 |
| `aave-link-u100-supply-30d` | 245.6% | 30 d | 1000000.0 LINK | 223680.0 | -21817.3 | 1.01 | 1.75 | 23.65 | 31.52 | 64.75 |
| `aave-ref-5pct-borrow-365d` | 5% | 365 d | 1000000.0 USDC | 51271.1 | -0.263043 | 5.29 | 6.6 | 11.01 | 37.2 | 70.17 |
| `morpho-at-target-4pct-1d` | r@t 4%, u 90% | 1 d | 10000000.0 USDC | 1095.95 | -6.39122e-7 | 9.23 | 13.19 | 9.34 | 30.1 | 67.42 |
| `morpho-at-target-4pct-7d` | r@t 4%, u 90% | 7 d | 10000000.0 USDC | 7674.18 | -8.185e-7 | 9.97 | 13.09 | 10.19 | 30.1 | 69.89 |
| `morpho-u95-10pct-1d` | r@t 10%, u 95% | 1 d | 10000000.0 USDC | 7091.84 | 0.576857 | 4.09 | 7.24 | 10.15 | 30.29 | 68.3 |
| `morpho-u95-10pct-7d` | r@t 10%, u 95% | 7 d | 10000000.0 USDC | 61708.5 | 274.507 | 2.35 | 4.56 | 11.09 | 30.29 | 70.21 |
| `morpho-u100-10pct-1d` | r@t 10%, u 100% | 1 d | 10000000.0 USDC | 11751.9 | 3.08123 | 3.58 | 6.51 | 10.37 | 30.29 | 68.54 |
| `morpho-u100-10pct-7d` | r@t 10%, u 100% | 7 d | 10000000.0 USDC | 129539.0 | 2478.09 | 1.72 | 3.61 | 11.41 | 30.29 | 70.0 |
| `morpho-u100-4pct-7d` | r@t 4%, u 100% | 7 d | 10000000.0 USDC | 51615.5 | 983.543 | 1.72 | 4.01 | 11.01 | 30.09 | 69.48 |
| `morpho-u100-4pct-30d` | r@t 4%, u 100% | 30 d | 10000000.0 USDC | 2073290.0 | 373938.0 | 0.74 | 1.51 | 12.62 | 30.13 | 71.08 |
| `morpho-u100-max-1d` | r@t 200%, u 100% | 1 d | 10000000.0 USDC | 221598.0 | -0.0965814 | 6.36 | 8.02 | 11.65 | 31.97 | 71.03 |
| `morpho-u100-max-7d` | r@t 200%, u 100% | 7 d | 10000000.0 USDC | 1658200.0 | -238.14 | 3.84 | 4.69 | 12.52 | 31.95 | 71.44 |
| `morpho-u100-max-30d` | r@t 200%, u 100% | 30 d | 10000000.0 USDC | 9300270.0 | -89366.4 | 2.02 | 2.33 | 13.27 | 31.84 | 71.75 |
| `morpho-u80-10pct-7d` | r@t 10%, u 80% | 7 d | 10000000.0 USDC | 16689.7 | 5.03335 | 3.52 | 6.3 | 10.52 | 30.29 | 69.22 |
| `morphofixed-ref-5pct-365d` | 5% | 365 d | 10000.0 18-dec token | 512.711 | -0.00263043 | 5.29 | 6.6 | — | 37.81 | 70.3 |
| `morphofixed-800pct-7d` | 800% | 7 d | 10000.0 18-dec token | 1658.2 | -0.23814 | 3.84 | 4.69 | — | 37.74 | 70.94 |

### Where the error comes from (stylised, token units)

| case | approximation (series) | rounding (grids) | IRM rate path: trapezoid | IRM rate path: wExp + rounding |
|---|---|---|---|---|
| `aave-usdc-u100-borrow-1d` | -1.03782e-9 | 1.23838e-7 | — | — |
| `aave-usdc-u100-supply-1d` | -0.0639222 | -4.92879e-9 | — | — |
| `aave-usdc-u100-borrow-7d` | -2.493e-6 | 3.29211e-7 | — | — |
| `aave-usdc-u100-supply-7d` | -3.13446 | -4.57905e-7 | — | — |
| `aave-weth-u100-borrow-7d` | -2.54919e-7 | 8.36391e-19 | — | — |
| `aave-link-u100-borrow-1h` | -6.28574e-10 | 3.01567e-19 | — | — |
| `aave-link-u100-supply-1h` | -0.0392951 | -5.16767e-19 | — | — |
| `aave-link-u100-borrow-1d` | -0.000208882 | 8.73846e-19 | — | — |
| `aave-link-u100-supply-1d` | -22.6888 | -6.99333e-19 | — | — |
| `aave-link-u100-borrow-7d` | -0.506637 | 4.79186e-19 | — | — |
| `aave-link-u100-supply-7d` | -1126.89 | -9.72784e-19 | — | — |
| `aave-link-u100-borrow-30d` | -177.806 | 5.73953e-19 | — | — |
| `aave-link-u100-supply-30d` | -21817.3 | -3.54348e-19 | — | — |
| `aave-ref-5pct-borrow-365d` | -0.263043 | 9.54835e-8 | — | — |
| `morpho-at-target-4pct-1d` | -6.00989e-11 | -6.39062e-7 | 0 | 0 |
| `morpho-at-target-4pct-7d` | -1.44317e-7 | -6.74184e-7 | 0 | 0 |
| `morpho-u95-10pct-1d` | -1.05296e-7 | -1.10943e-7 | 0.693358 | -0.116501 |
| `morpho-u95-10pct-7d` | -0.000608201 | -2.93676e-8 | 296.156 | -21.6484 |
| `morpho-u100-10pct-1d` | -7.93884e-7 | -9.56256e-7 | 4.59666 | -1.51543 |
| `morpho-u100-10pct-7d` | -0.0123607 | -6.45252e-8 | 2488.26 | -10.1595 |
| `morpho-u100-4pct-7d` | -0.000315935 | -4.16563e-7 | 987.575 | -4.03198 |
| `morpho-u100-4pct-30d` | -1001.88 | -3.95702e-8 | 374939.0 | 1.62391 |
| `morpho-u100-max-1d` | -0.0965792 | -3.10268e-7 | -4.67337e-7 | -1.40201e-6 |
| `morpho-u100-max-7d` | -238.14 | -3.0937e-7 | -3.73113e-6 | -0.0000111934 |
| `morpho-u100-max-30d` | -89366.4 | -5.20822e-7 | -0.0000264726 | -0.0000794177 |
| `morpho-u80-10pct-7d` | -3.22702e-6 | -6.96324e-7 | 3.95015 | 1.0832 |
| `morphofixed-ref-5pct-365d` | -0.00263043 | -3.33352e-15 | — | — |
| `morphofixed-800pct-7d` | -0.23814 | -9.48523e-15 | — | — |

## Live pending accruals at block 26206698

Every reserve or market's accrual as it would execute if touched at the survey block, from its on-chain state (rates, indexes, rate at target, totals, last update). Sorted by |err| in units of the token's last decimal; when *digits* is close to *grid* the error is just the token's decimals.

### Aave v3 Core, variable debt (39)

Truth: e^(rate·years).

| case | rate | idle | principal | true interest | err (tokens) | digits (interest) | digits (balance) | grid | FP127 digits (interest) | FP256 digits (interest) |
|---|---|---|---|---|---|---|---|---|---|---|
| `live-aave-FRAX-borrow` | 67.73% | 4.27 d | 28624.3 FRAX | 227.665 | -4.70515e-6 | 7.68 | 9.79 | 20.66 | 37.14 | 69.47 |
| `live-aave-CRV-borrow` | 5.574% | 10.6 d | 937065.0 CRV | 1523.19 | -2.71783e-7 | 9.75 | 12.54 | 21.48 | 35.87 | 69.26 |
| `live-aave-BAL-borrow` | 26.07% | 4.27 d | 26659.9 BAL | 81.4365 | -9.61846e-8 | 8.93 | 11.44 | 20.21 | 37.07 | 69.58 |
| `live-aave-SNX-borrow` | 13.95% | 5.18 d | 57849.0 SNX | 114.684 | -3.70994e-8 | 9.49 | 12.19 | 20.36 | 36.37 | 68.81 |
| `live-aave-KNC-borrow` | 23.74% | 4.27 d | 10889.4 KNC | 30.2833 | -2.70033e-8 | 9.05 | 11.61 | 19.78 | 35.93 | 69.43 |
| `live-aave-LUSD-borrow` | 6.6% | 1.06 d | 480978.0 LUSD | 92.1174 | -2.69544e-11 | 12.53 | 16.25 | 20.27 | 35.56 | 67.93 |
| `live-aave-STG-borrow` | 20.33% | 4.27 d | 10.1406 STG | 0.0241433 | -1.35185e-11 | 9.25 | 11.88 | 16.68 | 37.2 | 68.92 |
| `live-aave-FXS-borrow` | 20.24% | 4.27 d | 5.52836 FXS | 0.0131019 | -7.2359e-12 | 9.26 | 11.88 | 16.42 | 36.16 | 68.88 |
| `live-aave-RPL-borrow` | 6.936% | 1.04 d | 64241.6 RPL | 12.7557 | -4.15913e-12 | 12.49 | 16.19 | 19.41 | 35.3 | 67.89 |
| `live-aave-DAI-borrow` | 4.963% | 2.83 h | 117947000.0 DAI | 1893.4 | -3.26348e-13 | 15.76 | 20.56 | 21.58 | 34.06 | 67.63 |

Interest digits across all 39: min 0.0, median 11.9, max 19.71; 3 of 39 have fewer than 4 (a relative error in the interest above 1e-4).

### Aave v3 Core, supply (liquidity index) (35)

Truth: per-second compounding of the liquidity rate (the APY Aave displays). The index is simple interest between updates by design; this is the size of that gap, not a bug.

| case | rate | idle | principal | true interest | err (tokens) | digits (interest) | digits (balance) | grid | FP127 digits (interest) | FP256 digits (interest) |
|---|---|---|---|---|---|---|---|---|---|---|
| `live-aave-CRV-supply` | 0.3228% | 10.6 d | 8090830.0 CRV | 761.012 | -0.0357875 | 4.33 | 8.35 | 21.18 | 28.95 | 63.27 |
| `live-aave-BAL-supply` | 3.802% | 4.27 d | 146273.0 BAL | 65.0576 | -0.0144634 | 3.65 | 7.01 | 20.11 | 29.71 | 62.72 |
| `live-aave-DAI-supply` | 3.399% | 2.83 h | 129137000.0 DAI | 1419.81 | -0.00780434 | 5.26 | 10.22 | 21.45 | 31.29 | 62.47 |
| `live-aave-KNC-supply` | 3.554% | 4.27 d | 58175.5 KNC | 24.1873 | -0.00502671 | 3.68 | 7.06 | 19.68 | 29.92 | 62.56 |
| `live-aave-USDtb-supply` | 1.532% | 6.73 h | 12676700.0 USDtb | 149.242 | -0.000878461 | 5.23 | 10.16 | 20.47 | 29.66 | 62.71 |
| `live-aave-RLUSD-supply` | 3.147% | 1.19 h | 3076330.0 RLUSD | 13.188 | -0.0000282612 | 5.67 | 11.04 | 19.42 | 29.86 | 62.91 |
| `live-aave-USDe-supply` | 0.2469% | 1.07 h | 250746000.0 USDe | 75.391 | -0.0000113308 | 6.82 | 13.34 | 20.18 | 29.75 | 62.04 |
| `live-aave-1INCH-supply` | 0.1279% | 1.44 d | 680573.0 1INCH | 3.43917 | -8.68955e-6 | 5.6 | 10.89 | 18.84 | 28.17 | 61.15 |
| `live-aave-SNX-supply` | 0.03327% | 5.18 d | 242254.0 SNX | 1.14426 | -2.70235e-6 | 5.63 | 10.95 | 18.36 | 28.71 | 60.38 |
| `live-aave-LDO-supply` | 0.05012% | 1.75 d | 717959.0 LDO | 1.72884 | -2.08149e-6 | 5.92 | 11.54 | 18.54 | 28.25 | 60.63 |

Interest digits across all 35: min 0.0, median 5.67, max 11.13; 5 of 35 have fewer than 4 (a relative error in the interest above 1e-4).

### Morpho Blue, markets idle under 7 days (210)

Truth: e^(integral of the rate) on the IRM's stated rate path.

| case | rate | idle | principal | true interest | err (tokens) | digits (interest) | digits (balance) | grid | FP127 digits (interest) | FP256 digits (interest) |
|---|---|---|---|---|---|---|---|---|---|---|
| `live-morpho-0x7bb3c455-wARS` | r@t 16.45%, u 77.29% | 15.8 h | 64968300.0 wARS | 17175.2 | 0.0602877 | 5.45 | 9.03 | 22.54 | 31.11 | 67.78 |
| `live-morpho-0x987b2c19-EURCV` | r@t 2.653%, u 80.03% | 1.16 d | 3680460.0 EURCV | 282.596 | 0.00191321 | 5.17 | 9.28 | 20.75 | 29.54 | 67.51 |
| `live-morpho-0x140fe487-USDe` | r@t 1.719%, u 99.34% | 21.6 h | 50159.4 USDe | 8.55827 | 0.0017013 | 3.7 | 7.47 | 19.23 | 29.88 | 67.77 |
| `live-morpho-0xd2630c0e-msETH` | r@t 18.02%, u 92.04% | 4.83 d | 1050.44 msETH | 4.33395 | 0.00111301 | 3.59 | 5.98 | 18.94 | 30.48 | 69.0 |
| `live-morpho-0xa128dddc-RLUSD` | r@t 2.371%, u 87.19% | 14.5 h | 21225700.0 RLUSD | 813.671 | 0.000112261 | 6.86 | 11.28 | 21.21 | 29.49 | 67.19 |
| `live-morpho-0x88a18b2f-USDtb` | r@t 5.931%, u 90.42% | 20.8 h | 900981.0 USDtb | 142.828 | 0.0000712247 | 6.3 | 10.1 | 20.46 | 30.09 | 67.66 |
| `live-morpho-0xac0ab812-msUSD` | r@t 2.697%, u 89.84% | 4.04 d | 9051170.0 msUSD | 2693.84 | 0.0000501908 | 7.73 | 11.26 | 21.73 | 29.47 | 68.12 |
| `live-morpho-0x9551f524-EURCV` | r@t 5.946%, u 86.79% | 1.99 d | 73610.4 EURCV | 23.1406 | 0.0000468198 | 5.69 | 9.2 | 19.67 | 30.43 | 67.89 |
| `live-morpho-0x8e6aeb10-DAI` | r@t 9.842%, u 87.15% | 1.72 d | 31227.8 DAI | 14.1192 | 0.0000168044 | 5.92 | 9.27 | 19.45 | 30.31 | 68.34 |
| `live-morpho-0x35c92b23-frxUSD` | r@t 5.845%, u 96.3% | 3.82 h | 21495.2 frxUSD | 1.59625 | 6.07644e-6 | 5.42 | 9.55 | 18.5 | 30.18 | 68.83 |

Interest digits across all 210: min 2.9, median 7.41, max 11.38; 7 of 210 have fewer than 4 (a relative error in the interest above 1e-4).

### Morpho Blue, markets idle 7 days or more (42)

Dormant markets: most sit at 100% utilisation (often the borrow side is bad debt that nobody repays and the supply side cannot withdraw), so the figures are what the contract would book at the next touch, not money anyone is likely to pay.

| case | rate | idle | principal | true interest | err (tokens) | digits (interest) | digits (balance) | grid | FP127 digits (interest) | FP256 digits (interest) |
|---|---|---|---|---|---|---|---|---|---|---|
| `live-morpho-0x1dca6989-USR` | r@t 200%, u 100% | 31.1 d | 34733200000.0 USR | 33980500000.0 | -361723000.0 | 1.97 | 2.28 | 28.83 | 31.84 | 71.13 |
| `live-morpho-0x8ebcaf72-lvlUSD` | r@t 188.3%, u 100% | 340 d | 5271.06 lvlUSD | 9153210.0 | -8623020.0 | 0.03 | 0.03 | 25.26 | 31.11 | 71.55 |
| `live-morpho-0x8d18658c-wUSDL` | r@t 200%, u 100% | 295 d | 3.91756e+15 wUSDL | 2.49744e+18 | -2.21447e+18 | 0.05 | 0.05 | 24.7 | 31.17 | 70.42 |
| `live-morpho-0xcc39b6c9-USD0` | r@t 0.293%, u 100% | 207 d | 25867.7 USD0 | 979267.0 | -569745.0 | 0.24 | 0.25 | 24.29 | 29.62 | 71.07 |
| `live-morpho-0x11db9f2c-WETH` | r@t 200%, u 100% | 310 d | 21.1454 WETH | 18860.8 | -17123.5 | 0.04 | 0.04 | 22.58 | 31.15 | 70.64 |
| `live-morpho-0x1f1ca195-WETH` | r@t 0.1%, u 100% | 254 d | 0.250966 WETH | 22.5851 | -16.3029 | 0.14 | 0.15 | 19.65 | 29.25 | 70.93 |
| `live-morpho-0x760b14c9-DAI` | r@t 2.49%, u 90.36% | 122 d | 44077.2 DAI | 558.226 | 3.20489 | 2.24 | 4.14 | 21.05 | 29.49 | 69.79 |
| `live-morpho-0xe475337d-DAI` | r@t 2.708%, u 90.61% | 53.1 d | 25557.6 DAI | 150.88 | 0.651714 | 2.36 | 4.6 | 20.48 | 30.2 | 69.99 |
| `live-morpho-0xbec3a938-apxUSD` | r@t 2.642%, u 87.64% | 58.8 d | 71043.7 apxUSD | 267.557 | 0.386261 | 2.84 | 5.27 | 20.73 | 29.88 | 68.99 |
| `live-morpho-0x9d1d0c9b-tGBP` | r@t 0.4364%, u 56.68% | 26.9 d | 78510.7 tGBP | 9.95413 | 0.383057 | 1.41 | 5.31 | 19.3 | 29.82 | 67.59 |

Interest digits across all 42: min 0.03, median 1.7, max 8.27; 37 of 42 have fewer than 4 (a relative error in the interest above 1e-4).

## The ladder's models against the deployed code

`test_ladder_models_match_deployed` runs LadderAave and LadderMorpho (the published ladder's transcriptions) and the pinned deployed libraries on the same integers for 18 (rate, N) cells of the continuous-accrual scenario (5%, 50%, 307%; N = 1..10000 days): every output is identical. The models differ from a deployed position in two ways the ladder already states or implies: the principal is a RAY (Aave) or WAD (Morpho) number rather than token units (deployed Aave balances round with rayMulCeil for debt and rayMulFloor for aTokens, to the token's decimals), and the Morpho rate is a constant per-second WAD rate rather than the AdaptiveCurveIrm's trapezoid average.

## Reproduce

```
make accrual-deployed        # offline: cases from the committed survey, forge harness, mpmath scoring
make accrual-verify          # network: recompile the pinned sources, compare runtime bytecode to mainnet
make accrual-survey          # network: refresh survey.json at the current block (changes the live cases)
```


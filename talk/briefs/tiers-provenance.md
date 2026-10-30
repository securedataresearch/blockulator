# Provenance for `talk/scenes/data/tiers.json` (slide 20, the report card)

Written 2026-10-30. Every row of `tiers.json` carries a `claim` T-id; this note gives, for each, the quoted line (file at a pinned commit, fetched 2026-10-30) or the computation. Grades are the printed rule applied to what was measured or documented; nothing here is a defect claim, and no loss is claimed at any exchange. Measurements marked "computed" were run with mpmath at 120 decimal digits (`uv run python`, mpmath 1.4.1); the throwaway scripts lived in the session scratchpad, so the method is written out here rather than referenced.

Digits = floor(−log10 |v − t| / |t|), the project's definition (docs/benchmarks/ladder.json → methodology.digits).

## S · integer-exact swap maths

**T1 · Uniswap v2 swap.** `contracts/UniswapV2Pair.sol` @ 6a9e7c97, L180–182:
```
uint balance0Adjusted = balance0.mul(1000).sub(amount0In.mul(3));
uint balance1Adjusted = balance1.mul(1000).sub(amount1In.mul(3));
require(balance0Adjusted.mul(balance1Adjusted) >= uint(_reserve0).mul(_reserve1).mul(1000**2), 'UniswapV2: K');
```
uint256 throughout; the output amount is whatever integer the caller requests that satisfies the check. Repo licence GPL-3.0.

**T2 · Uniswap v3/v4 swap step.** `contracts/libraries/SqrtPriceMath.sol` @ 5ea68a77, L18: "Always rounds up, because in the exact output case (increasing price) we need to move the price at least far enough to get the desired output amount"; L59: "Always rounds down, because in the exact output case (decreasing price) we need to move the price at least far enough to get the desired output amount"; L44/54 `FullMath.mulDivRoundingUp(...)`. `SwapMath.sol` L95 `feeAmount = FullMath.mulDivRoundingUp(amountIn, feePips, 1e6 - feePips)`. FullMath.mulDiv is the 512-bit exact floor(a·b/d). v4-core `src/libraries/SwapMath.sol` @ bea7f6d1 is the same library under MIT. Licence: v3-core file headers say BUSL-1.1; v3-core LICENSE L18–21: "Change Date: The earlier of 2023-04-01 ... Change License: GNU General Public License v2.0 or later" (date passed). v3-core `TickMath.sol` header is already GPL-2.0-or-later.

**T3 · Curve StableSwap.** 3pool `contracts/pools/3pool/StableSwap3Pool.vy` @ 574f4402, L205–217 (get_D):
```
for _i in range(255):
    ...
    # Equality with the precision of 1
    if D > Dprev:
        if D - Dprev <= 1:
            break
    else:
        if Dprev - D <= 1:
            break
```
and L387–395 (get_y) the same on `y_prev`. stableswap-ng `contracts/main/CurveStableSwapNG.vy` @ 3332cd44, L1098–1121 (get_D) and L1069–1072 (get_y) carry the identical stop. Licence: ng header L7 "@license Copyright (c) Curve.Fi, 2020-2023 - all rights reserved"; 3pool header "(c) Curve.Fi, 2020". Read only; nothing transcribed.

**T4 · Aerodrome stable pool.** `contracts/Pool.sol` @ 1ba30815, L381–382: "// The curve, either x3y+y3x for stable pools, or x*y for volatile pools / if (_k(_balance0, _balance1) < _k(_reserve0, _reserve1)) revert K();". L411–440 `_get_y`: "// If _k(x0, y + 1) > xy, then we are close to the correct answer. // There's no closer answer than y + 1 / return y + 1;" and the mirror case "There's no closer answer than "y"". Integer arithmetic on 1e18-normalised reserves. Licence: Pool.sol L1 `// SPDX-License-Identifier: GPL-3.0-or-later` (the draft said BUSL; the repo's licence field is unset). Velodrome was not fetched and is not named.

**T5 · Trader Joe LB swap in a bin.** `src/libraries/BinHelper.sol` @ 067c6ccf (lfj-gg/joe-v2, the moved repo), L238–240:
```
uint128 maxAmountIn = swapForY
    ? uint256(binReserveOut).shiftDivRoundUp(Constants.SCALE_OFFSET, price).safe128()
    : uint256(binReserveOut).mulShiftRoundUp(price, Constants.SCALE_OFFSET).safe128();
```
L262 `uint256(amountIn).mulShiftRoundDown(price, Constants.SCALE_OFFSET).safe128()`. Licence MIT.

## A · about 30 digits

**T6 · Uniswap v3/v4 TickMath (computed).** `getSqrtRatioAtTick` (v3-core `contracts/libraries/TickMath.sol` @ 5ea68a77, L23–53) transcribed with its 20 constants parsed from the file by regex. Constant check: constant i vs 2^128 / sqrt(1.0001^(2^i)), largest |difference| 0.49 units (each constant is the nearest integer). Output `sqrtPriceX96` vs sqrt(1.0001^tick)·2^96:

| tick | −887272 | −500000 | −200000 | −100000 | −23027 | −10000 | −1000 | −100 | −10 | −1 | 1 | 10 | 100 | 1000 | 10000 | 23027 | 100000 | 200000 | 500000 | 887272 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| digits | 9 | 18 | 24 | 27 | 28 | 29 | 29 | 29 | 28 | 28 | 29 | 29 | 28 | 29 | 29 | 29 | 31 | 33 | 27 | 19 |

Tick 0 is exact (2^96). Near par the Q64.96 grid is 2^-96 ≈ 1.3e-29 relative, hence 29; at MIN_TICK the value is about 2^32 units, so about 32 significant bits remain, hence 9. L53 `sqrtPriceX96 = uint160((ratio >> 32) + (ratio % (1 << 32) == 0 ? 0 : 1))` rounds up, so the result is not the nearest representable (not S). v4-core `src/libraries/TickMath.sol` @ bea7f6d1 (MIT) is the same algorithm.

**T7 · Trader Joe LB bin price (computed).** `PriceHelper.getPriceFromId` = `getBase(binStep).pow(id − 2^23)`, `getBase` = `Constants.SCALE + (uint256(binStep) << Constants.SCALE_OFFSET) / Constants.BASIS_POINT_MAX` (L28–58 @ 067c6ccf); `Uint128x128Math.pow` (L95–175) transcribed: invert x when x > 2^128 − 1, then square-and-multiply with `shr(128, mul(...))` per bit, `type(uint256).max / result` when the sign asks. Base floor: relative error −4.3e-40 (binStep 1) to −1.9e-39 (binStep 25). Price vs (1 + binStep/10000)^e · 2^128:

| binStep | e = −max | −max/10 | −1 | 1 | max/10 | max |
|---|---|---|---|---|---|---|
| 1 (max 10000) | 34 | 35 | 38 | 39 | 35 | 34 |
| 10 (max 10000) | 34 | 36 | 39 | 38 | 36 | 34 |
| 25 (max 5000) | 33 | 36 | 39 | 38 | 36 | 33 |
| 100 (max 3000) | 26 | 36 | 39 | 38 | 36 | 26 |

Larger |e| at binStep 100 underflows the 128.128 intermediate and the contract reverts (`Uint128x128Math__PowUnderflow`), so those ids are outside the format, not measured. Licence MIT.

## B · as documented

**T8 · Uniswap v3 TWAP.** v3-periphery `contracts/libraries/OracleLibrary.sol` @ 24ccf014, L34–36:
```
arithmeticMeanTick = int24(tickCumulativesDelta / secondsAgo);
// Always round to negative infinity
if (tickCumulativesDelta < 0 && (tickCumulativesDelta % secondsAgo != 0)) arithmeticMeanTick--;
```
A tick is a factor 1.0001 = 1 bp, so flooring the mean tick moves the price `getQuoteAtTick` reports by less than 1 bp. Licence GPL-2.0-or-later. The draft's live figure (+0.787 bp, USDC/WETH, block 26258017) needs an archive `observe` call that was not re-run; it is not in `tiers.json`.

**T9 · Pendle market exchange rate (draft S → B).** `contracts/core/Market/MarketMathCore.sol` @ 87685c89, L314–324: "/// @notice Converts an implied rate to an exchange rate given a time to expiry. The formula is E = e^rt ... exchangeRate = LogExpMath.exp(rt.Int());" and L309 `uint256 lnRate = exchangeRate.ln().Uint();`. LogExpMath is Balancer's 18-decimal ln/exp (L4 import). Exponentials in WAD are not integer-exact, so B. Licence header GPL-3.0-or-later.

**T10 · GMX v2 price impact (draft S → B).** `contracts/utils/Precision.sol` @ a85ea349, L88–109:
```
// `PRBMathUD60x18.pow` doesn't work for `x` less than one
if (floatValue < FLOAT_PRECISION) { return 0; }
...
// we need to convert float (30 decimals) to 60x18 (18 decimals) and then back to 30 decimals
uint256 weiValue = PRBMathUD60x18.pow(floatToWei(floatValue), floatToWei(exponentFactor));
```
called from `PricingUtils.applyImpactFactor` L104–110. Licence: file headers BUSL-1.1; LICENSE @ a85ea349 L10–11 "Change Date: The earlier of 31 August 2026 ... Change License: GNU General Public License v2.0 or later" (the draft said GPL; the change date has passed for this version only if it was published before then, so the row says BUSL-1.1 with the change terms).

**T11 · Curve twocrypto-ng get_y.** `contracts/main/TwocryptoMath.vy` @ 5cbe5589, L150 `convergence_limit: uint256 = max(max(x_j // 10**14, D // 10**14), 100)` and L196 `if diff < max(convergence_limit, y // 10**14): return y`. A stated stopping precision of 1e-14 relative in 18-decimal arithmetic. Licence header L5 "@license Copyright (c) Curve.Fi, 2025 - all rights reserved"; read only. The draft's 7.4e-16 figure was not re-run (its script is gone and the licence forbids transcription) and is not in `tiers.json`. Note: this is the file at `main`; the deployed twocrypto-ng math contract may be an earlier revision of the same solver.

**T12 · Algebra V1 dynamic fee.** cryptoalgebra/Algebra tag v1.0.0 @ 60d71de0, `src/core/contracts/libraries/AdaptiveFee.sol`: L41 "/// @notice calculates α / (1 + e^( (β-x) / γ))", L52 `if (x >= 6 * uint256(g)) return alpha;`, L59 `if (x >= 6 * uint256(g)) return 0;`, L67–69 "/// @notice calculates e^(x/g) * g^8 in a series, since (around zero): e^x = 1 + x + x^2/2 + ... + x^n/n! + ...", the series summed through the x^8 term (L81–100). Fee returned as uint16 (L29). Licence: file header BUSL-1.1 at the tag, no LICENSE file at the tag, repo licence field unset (the draft said GPL).

**T13 · Compound v3 (draft C → B).** `contracts/CometCore.sol` @ f766f515, L51 `uint64 internal constant BASE_INDEX_SCALE = 1e15;`; `contracts/CometWithExtendedAssetList.sol` L254–265:
```
baseSupplyIndex_ += safe64(mulFactor(baseSupplyIndex_, supplyRate * timeElapsed));
baseBorrowIndex_ += safe64(mulFactor(baseBorrowIndex_, borrowRate * timeElapsed));
```
Linear between accruals on a 15-decimal index: a documented precision choice (B), not fewer digits than the format holds. (`contracts/Comet.sol` is not present at this commit; the extended-asset-list contract carries the accrual.) Licence: BUSL-1.1, LICENSE L18–21 "Change Date: The earlier of 2025-12-31 ... Change License: GNU General Public License v2.0 or later".

## C · fewer digits than the format, or a model off its documented value

**T14 · Maverick v2 TickMath (computed; draft B → C).** `contracts/libraries/TickMath.sol` @ d91e8714, L54–80 `tickSqrtPrice`: 19 constants, `if (_tick > 0) ratio = type(uint256).max / ratio; _result = (ratio * ONE) >> 128;` with `ONE = 1e18`, `MAX_TICK = 322_378` (`Constants.sol` L17, "max price 1e14 in D18 scale"). Constants parsed from the file; relative error of constant i against 2^128 / sqrt(1.0001^(2^i)):

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rel. error | 5.5e-18 | 1.1e-17 | 2.2e-17 | 4.4e-17 | 8.8e-17 | 1.8e-16 | 3.5e-16 | 7.0e-16 | 1.4e-15 | 2.8e-15 | 5.6e-15 | 1.1e-14 | 2.3e-14 | 4.5e-14 | 9.0e-14 | 1.8e-13 | 3.6e-13 | 7.2e-13 | 1.4e-12 |

(each doubles: the table behaves as the first constant squared up, so its error compounds). `tickSqrtPrice` (D18) vs sqrt(1.0001^tick)·1e18: tick ±1 → 17 digits; ±1000 → 14; ±10000 → 13; ±100000 → 12; ±300000 and ±322378 → 11. The format (18 decimals of a value near 1e18·sqrt(1.0001^tick)) holds 18, so by the printed rule this is C; it is a constant table shared by every user of a pool, and no loss is claimed. The draft's "constants are 1.0001 as float64" was tested and does not hold: float64 1/sqrt(1.0001) scaled to Q128 is 0xfffcb933bd6fb8000..., the file has 0xfffcb933bd6fad9d3af5f0b9f25db4d6 (Uniswap's correctly rounded constant is 0xfffcb933bd6fad37aa2d162d1a594001). Licence GPL-2.0-or-later.

**T15 · Aave v3.** `docs/benchmarks/accrual-deployed.json` (generated 2026-10-16; survey block 26206698): cases with `group = "live"`, `protocol = "aave"`: 74 (39 borrow, 35 supply). Computed from the file: `digitsInterest` median 8.605, min 0.0; `digitsBalance` median 13.5, min 7.01. The .md states the halves: borrow "Interest digits across all 39: min 0.0, median 11.9, max 19.71"; supply "across all 35: min 0.0, median 5.67, max 11.13", with the supply truth being "per-second compounding of the liquidity rate (the APY Aave displays)". Claims quoted in the JSON: MathUtils doc comment "The approximation slightly underpays liquidity providers and undercharges borrowers" (aave-v3-origin v3.7.0 @ cff15de6, `MathUtils.sol` L38–44) and the body L83 `return WadRayMath.RAY + x + x.rayMul(x / 2 + x.rayMul(x / 6));`. Licence: MathUtils.sol header BUSL-1.1.

**T16 · Morpho Blue.** Same file, `protocol = "morpho"`: 252 live markets; computed `digitsInterest` median 7.06 (the .md: 210 idle under 7 days "median 7.41"; 42 idle 7 days or more "median 1.7", "most sit at 100% utilisation"); `digitsBalance` median 11.9. Truth "e^(integral of the rate) on the IRM's stated rate path". morpho-blue v1.0.0 @ 55d2d993 `src/libraries/MathLib.sol` L36–38: "/// @dev Returns the sum of the first three non-zero terms of a Taylor expansion of e^(nx) - 1, to approximate a continuous compound interest rate." Licence header GPL-2.0-or-later.

**T17 · SparkLend (computed).** sparkdotfi/sparklend-v1-core @ 8120e495 (the moved repo), `contracts/protocol/libraries/math/MathUtils.sol` L71–72, 79:
```
basePowerTwo = rate.rayMul(rate) / (SECONDS_PER_YEAR * SECONDS_PER_YEAR);
basePowerThree = basePowerTwo.rayMul(rate) / SECONDS_PER_YEAR;
...
uint256 thirdTerm = exp * expMinusOne * expMinusTwo * basePowerThree;
```
with `rayMul(a, b) = (a·b + RAY/2) / RAY`, RAY = 1e27, SECONDS_PER_YEAR = 31536000. Binary search over the integer formula: `basePowerThree == 0` for every rate up to 31535999842319999605799990 (3.1536% APR) and 1 at the next RAY unit, i.e. the cubic term of the binomial is identically zero below 3.1536% APR, however long the idle period. Size of the dropped term at 3% APR, x = 0.03·t/year: x³/6 relative to the interest x is x²/6 = 1.1e-9 (1 day), 1.0e-6 (30 days), 1.5e-4 (365 days). The repo's README is Aave V3's; the deployed Spark pool was not re-verified against its bytecode, so the row says "repo code". Licence header BUSL-1.1.

**T18 · FraxLend VariableInterestRate V2.** `docs/benchmarks/ladder.json` → scenarios[id = adaptive-rate] → inputs[name = reference] ("100% utilisation, a day per step, FraxLend's deployed half-life of two days (rate contract 0x18500cB1...F261)"; rate0 = 1.26839167935e-9 per second = 4% APR): cells.fraxlend["5"].value = 0.000000004439370876 (×3.5000 of rate0), truth["5"] = 0.00000000717510686 (×5.6569 = 2^(5/2)); digits1 "1.2". Scenario summary for fraxlend, N = 1: digits min 0.2, median 1.4, max 4.7. Source `src/contracts/VariableInterestRate.sol` @ 2bed49d4 (the ladder's pin), L129–133:
```
uint256 _deltaUtilization = ((_utilization - MAX_TARGET_UTIL) * 1e18) / (UTIL_PREC - MAX_TARGET_UTIL);
uint256 _decayGrowth = (RATE_HALF_LIFE * 1e36) + (_deltaUtilization * _deltaUtilization * _deltaTime);
_newFullUtilizationInterest = uint64((_fullUtilizationInterest * _decayGrowth) / (RATE_HALF_LIFE * 1e36));
```
i.e. F·(1 + δ²Δt/H), which equals the documented 2^(Δt/H) (L53 "The interest rate half life in seconds") only at Δt = H; the draft's "one update after two half-lives gives 3× vs 4×" follows (1 + 2 = 3 against 2² = 4) and the ladder's N = 2 cell (Δt = H exactly) shows the two agreeing to 9 digits. Licence header ISC.

**T19 · Euler v2 IRMAdaptiveCurve.** `ladder.json` → adaptive-rate → inputs[name = euler-speed] ("Euler's deployed ADJUSTMENT_SPEED, 100 per 365-day year (3170979198376 wei per second at 0xC9A0109D...C23D)", 100% utilisation): cells.euler["1"].relErr = −0.00279481 (value 1.663499614e-9 against truth 1.668161808e-9), digits1 2.5. inputs[name = euler-halving] (0% utilisation at Euler's speed): cells.euler["1"].relErr = +0.00421513 (9.68490475e-10 against 9.64425300e-10), digits1 2.3. So the stored rate at target after one idle day is −0.28% / +0.42% off r0·e^(speed·err·t). Source evk-periphery @ dd93a5f5 `src/IRM/IRMAdaptiveCurve.sol` L197–201: "/// Formula: `rateAtTarget = startRateAtTarget * e^linearAdaptation` bounded to min and max. ... int256 rateAtTarget = startRateAtTarget * ExpLib.wExp(linearAdaptation) / WAD;" and `src/IRM/lib/ExpLib.sol` L36–37 "// Compute e^r with a 2nd-order Taylor polynomial. ... int256 expR = WAD + r + (r * r) / WAD / 2;" after "x = q * ln(2) + r with ... -ln(2)/2 <= r <= ln(2)/2". Licence headers MIT.

## F · the incidents

**T20–T24.** Copied verbatim from `talk/scenes/data/incidents.json` (`incidents[0..4]`): `name` = protocol, `date`, `loss`, `lossUsd`, `measured` = that file's `rounding` sentence, `note` = its `source` string. Nothing re-derived here; that file's `_doc` carries its provenance (research_notes/talk/essay-v6.txt §2 and the replays under docs/benchmarks/replay-*.md).

## Not pinned (left out of `tiers.json`)

- **Ekubo ticks (draft S) and Ekubo TWAMM "34-bit log2(e)" (draft B).** `EkuboProtocol/evm-contracts` @ 933c813c: `src/math/ticks.sol` uses base 1.000001 ("sqrtRatio = sqrt(1.000001^tick)"), so the draft's framing does not transfer; the TWAMM constant was not found in `src/math/twamm.sol`/`exp2.sol` on a read; and every file is under the "Ekubo DAO Shared Revenue License 1.0" (ekubo-license-v1.eth), which the project treats as read-only. Not measured, so not graded.
- **DODO guide price as WAD of raw units (draft B).** The quantified example (PEPE/USDC, i = 10, 10% grid) needs the lost script; no primary quote fetched. Dropped.
- **Balancer powUp margin (draft B).** Balancer V2 and V1 are F rows from incidents.json; a B row for Balancer's LogExpMath/weighted maths would put one name in two tiers on the same slide, and the "deliberate margin" quote was not fetched. Dropped.
- **Uniswap v3 TWAP live +0.787 bp** and **Curve twocrypto 7.4e-16 / D ~18 digits**: the rows stay (T8, T11) on the source quote alone; the numbers were not re-run.
- **Velodrome** (named with Aerodrome in the draft): not fetched; the row is Aerodrome only.
- **Pendle, GMX v2 integer-exact (draft S):** re-graded B (T9, T10), not dropped.

## Grade changes from the draft

| row | draft | now | why |
|---|---|---|---|
| Uniswap v3/v4 TickMath | S | A | rounds up, not to nearest; 29 digits near par, 9 at MIN_TICK (measured) |
| Trader Joe LB bin price | S | A | 26–39 digits from repeated squaring in 128.128 (measured); the in-bin swap stays S |
| Pendle | S | B | exchange rate is LogExpMath.exp in 18 decimals, as documented |
| GMX v2 | S | B | price impact uses PRBMathUD60x18.pow after a 30→18 decimal conversion |
| Compound v3 | C | B | a 15-decimal index with simple interest between accruals is a documented choice |
| Maverick v2 TickMath | B | C | 11–17 digits in an 18-decimal result (measured); the float64 explanation does not hold |

## Licence notes carried in `source.licence`

Curve (3pool, ng, twocrypto-ng): all rights reserved, read only. Aerodrome Pool.sol: GPL-3.0-or-later header (draft said BUSL). Uniswap v2-core GPL-3.0; v3-core BUSL-1.1 with Change Date 2023-04-01 → GPL-2.0-or-later, TickMath.sol already GPL-2.0-or-later; v3-periphery GPL-2.0-or-later; v4-core MIT. Trader Joe LB MIT. Pendle GPL-3.0-or-later. GMX BUSL-1.1 (change date 31 Aug 2026 → GPL-2.0-or-later). Maverick GPL-2.0-or-later. Algebra V1 BUSL-1.1 header at v1.0.0. Compound v3 BUSL-1.1 (change date 2025-12-31 → GPL-2.0-or-later). Aave v3 BUSL-1.1. Morpho Blue GPL-2.0-or-later. SparkLend BUSL-1.1. FraxLend ISC. Euler MIT.

## 2026-10-30: the user's F rule

The user: "<10 digits is F tier, and balancer reverts? so i guess F tier". The rule now reads C · 10 correct digits or more, but fewer than the format holds; F · under 10 correct digits, a revert inside the domain, or a rounding step that lost money. Rows moved C → F: Aave v3 (8.6, T-row above), Morpho Blue (7.1), FraxLend V2 (1.2 on the ladder), Euler v2 IRMAdaptiveCurve (2.4 on the ladder), SparkLend. SparkLend had no digit count; it is computed here: Aave v3.0.2's `calculateCompoundedInterest` in exact ray integers (RAY = 1e27, SECONDS_PER_YEAR = 31536000, rate = 3% APR, exp = 86400 s; basePowerThree = 0), against continuous compounding e^(rt) − 1 at 60 digits (mpmath): 8.8 correct digits of the day's interest. Maverick v2 TickMath (11–17 digits) stays C. On the libraries slide (computed, s21): Balancer moves to F (reverts from exp(−42) inside its type's domain), with Aave, Morpho, FraxLend and Euler v2; ABDK 64.64 (10.5) and Maker (23.3) stay C.

## Worst-case measurement, protocols (2026-10-30)

By the user's rule: each protocol row is graded by one number, its correct digits on its worst input, digits = −log10 |v − t| / |t| (floored to two decimals; a relative error of 1 or more is 0), with v the protocol's own integer result and t the exact value of the model the protocol documents, mpmath at 120 digits. Script `scripts/tiers/measure_protocols.py` (`uv run --with mpmath python scripts/tiers/measure_protocols.py`), output `talk/scenes/data/tiers-worst-protocols.json`. The integer arithmetic is transcribed in the script from the pinned sources (SHAs in its header and below), not run through the ladder's Solidity; the transcriptions are checked against the repo's recorded integers before measuring: Aave's factor equals `deployed.factor` on all 39 live borrows and Morpho's `wTaylorCompounded` equals `deployed.taylor` on all 252 live markets in `accrual-deployed.json`; FraxLend and Euler equal the ladder adapters' raw words on 40 and 20 cells of `ladder.json` adaptive-rate. Deployed parameters (Comet curves, FraxLend and Euler immutables, Spark's rate caps) were read by `eth_call` at mainnet block 26307942. Search per row: the domain's corners and edges, a grid, and 12,000 seeded random inputs (seed 20261030; rates and times log-uniform, utilisation uniform and log-uniform), 12,204 to 14,550 inputs per row; no input reverted in any row. "Nearest" below is what the closest value on the protocol's own grid would score at the same input, so a worst case the format forces can be told from one the arithmetic causes.

**Aave v3 (T15) · 0.00 digits, F (unchanged).** The debt factor `MathUtils.calculateCompoundedInterest` − RAY (aave-v3-origin v3.7.0 @ cff15de6, `x = rate·exp / SECONDS_PER_YEAR; RAY + x + x.rayMul(x/2 + x.rayMul(x/6))`) against e^(rt) − 1, the "ideal formula" its comment names. Domain: borrow rates 0.0001% to 1000% APR (`DefaultReserveInterestRateStrategyV2.MAX_BORROW_RATE = 1000_00` bps), 1 s to 1 year. Worst: 1000% APR idle 365 days, factor 1 + 226.67 against e^10 = 22026.47, relative error −0.990 (the nearest RAY value would hold 31.9 digits). Idle 1 day or less, the worst is 6.07 (1000% APR, one day). Live (`accrual-deployed.json`, 74 positions): min 0.0 (live-aave-LBTC-borrow: 1.6e-11 LBTC of interest, below one satoshi, so the token grid itself gives 0), median 8.61; the factor alone over the 39 live borrows, min 7.68 (live-aave-FRAX-borrow).

**SparkLend (T17) · 0.38 digits, F (unchanged).** Aave v3.0.2's binomial (sparklend-v1-core @ 8120e495, `MathUtils.sol` L50–80, `basePowerTwo = rate.rayMul(rate) / SECONDS_PER_YEAR²`, `basePowerThree = basePowerTwo.rayMul(rate) / SECONDS_PER_YEAR`) against (1 + r/31536000)^t − 1, the per-second compounding its doc comment expands ("(1+x)^n = 1+n*x+[n/2*(n-1)]*x^2+..."). Domain: 0.0001% to 320% APR, the largest `getMaxVariableBorrowRate()` over Spark's 20 reserves at the block above, 1 s to 1 year. Worst: 320% APR idle 365 days, interest 13.78 against 23.53 per unit, relative error −0.414 (nearest RAY value: 29.6 digits). Idle 1 day or less: 7.55. No live data. Note the truth here is per-second compounding, as the v3.0.2 comment states, where the earlier F-rule note measured against e^(rt).

**Morpho Blue (T16) · 0.01 digits, F (unchanged).** `MathLib.wTaylorCompounded(borrowRate, elapsed)` (morpho-blue v1.0.0 @ 55d2d993, L38–44, as `_accrueInterest` calls it) against e^(rt) − 1. Domain: the AdaptiveCurveIrm's whole output range (morpho-blue-irm v1.0.0 @ a7d9cce3 ConstantsLib: 0.25 × MIN_RATE_AT_TARGET to 4 × MAX_RATE_AT_TARGET, 0.025% to 800% APR per second in WAD), 1 s to 1 year. Worst: 800% APR idle 365 days, 125.33 against e^8 − 1 = 2979.96, relative error −0.958 (nearest WAD value: 22.1 digits). Idle 1 day or less: 6.36. Live (252 markets): min 0.03 (live-morpho-0x8ebcaf72-lvlUSD, idle 340 days at 100% utilisation with the rate at target near its maximum; truth on the IRM's rate path), median 7.06; `wTaylorCompounded` alone at each market's deployed rate, min 0.02 on the same market.

**Compound v3 (T13) · 0.00 digits, B → F.** The index increment `mulFactor(index, rate·timeElapsed)` of `accruedInterestIndices` (comet @ f766f515, `CometWithExtendedAssetList.sol` L254–265, rates L297–321, `BASE_INDEX_SCALE = 1e15`) against index·rate·t / 1e18 exactly, the documented simple interest, with cUSDCv3's deployed curves (0xc3d688B6…cdc3: supply 0 + 1141552511/s below the 90% kink, borrow base 475646879/s). Domain: both sides, utilisation 0 to 100% on its 1e18 grid, 1 s to 1 year, index from 1e15 (genesis) to today's (1.2087e15 supply, 1.2750e15 borrow). The only error is the floor to the 1e15 index grid. Worst: supply side at 1e-9 utilisation (3.15e-9% APR), 1 s, index 1.0: the true increment is 0.001 of a unit and the code adds 0; the nearest grid value would also be 0 there, so this worst case is the format's, not the arithmetic's. Rates of 0.01% APR or more: 3.57 digits (supply side, 0.30% utilisation, 1 s); 1% APR or more: 5.61 (1 s). Idle 1 day or more: 2.11, again at a near-zero rate. The index floors rather than rounding to nearest, so it is not S; by the printed rule (< 10) it is F on any of these figures.

**FraxLend VariableInterestRate V2 (T18) · 0.00 digits, F (unchanged).** `getFullUtilizationInterest` (fraxlend @ 2bed49d4, `VariableInterestRate.sol` L108–140, with the uint64 cast and the clamps) against clamp(F·2^(±d²t/H), MIN, MAX): the documented half-life, doubling per H at 100% utilisation and halving at 0% (d = 1 at both ends; d²-weighted in between as the code weights it). Domain, from the deployed rate contract 0x18500cB1…F261 (band 75–85%, H = 172800 s, full-utilisation rate 1582470460 to 3164940920000 per second, 0.5% to 10000% APR): starting full-utilisation rate MIN to MAX, utilisation 0 to 100% on its 1e5 grid, one update after 1 s to 1 year. Worst: 9980.96% APR at 0.001% utilisation, one update after 22 days: the code divides by 1 + 11 = 12, the half-life by 2^11 and then clamps to MIN, so the result is 166.7 times the truth (relative error +165.7). At exactly 0% or 100% (the half-life as quoted) the same 0.00; idle 1 day or less, 1.21 (98.5% APR, 100% utilisation, 21.3 hours).

**Euler v2 IRMAdaptiveCurve (T19) · 2.04 digits, F (unchanged).** The stored rate at target after one update (evk-periphery @ dd93a5f5, `IRMAdaptiveCurve.sol` L144–220 `computeInterestRateInternal`, `_newRateAtTarget`, `_calcErr`; `ExpLib.wExp` L23–43, signed division truncating toward zero) against clamp(r0·e^(speed·err·t), MIN, MAX), the formula the code's comment states. Domain, from the deployed IRM 0xC9A0109D…C23D (target 90%, ADJUSTMENT_SPEED 3170979198376, rate at target 31709791 to 63419583967 per second, 0.1% to 200% APR): starting rate at target MIN to MAX, last utilisation 0 to 100% (WAD), one update after 1 s to 1 year. Worst: rate at target 75.76% APR, 38.52% utilisation, 24.3 days, relative error +0.0090: the reduced argument lands at r ≈ −ln2/2, where 1 + r + r²/2 is 0.9% above e^r (the nearest WAD-per-second value would hold 9.5 digits there). Idle 1 day or less: 2.37 (200% APR, 0% utilisation, one day).

Grade changes from this measurement: Compound v3 B → F (the only change; its worst case is format-forced, and it measures 3.57 digits at rates of 0.01% APR or more, still F). Aave v3, Morpho Blue, SparkLend, FraxLend and Euler v2 stay F, now on their domain worst rather than the live median (Aave 8.6 → 0.00 printed, Morpho 7.1 → 0.01). Not measured: Aave's supply side (the liquidity index's simple interest; the task's Aave model is the debt's e^(rt)), and the Morpho IRM's own rate-path error over the domain (the live figures include it).

**Digits lost (added 2026-10-30, the user's change of measure).** For each row the same searched inputs are also scored by the absolute error in units of the result's own last place: |v − t| with v the protocol's integer and t the exact model value on the same scale. The units are a ray unit (1e-27) of the debt factor for Aave v3 and SparkLend, a WAD unit of the compounded factor for Morpho Blue, an index unit (1e-15 of the 1e15 base) for Compound v3, and 1e-18 per second of the rate for FraxLend's full-utilisation rate and Euler's rate at target. `worst_units` is the largest such error over the search and `worst_input_units` is where it occurs, which may differ from the digits-held worst. Then `digits_lost` = log10(max(worst_units, 1)), so any answer within one unit loses 0 digits: a correctly rounded answer (≤ 0.5 unit) or a floor short of one unit. Results:

| row | worst_units | digits_lost | worst input for units |
|---|---|---|---|
| Aave v3 | 2.18e31 | 31.33 | 1000% APR, idle 365 days |
| SparkLend | 9.75e27 | 27.98 | 320% APR, idle 365 days |
| Morpho Blue | 2.85e21 | 21.45 | 800% APR, idle 365 days |
| Compound v3 | 0.99998 | 0.00 | borrow side, 1.5% APR, 227 s, index 1.0812 |
| FraxLend | 3.15e12 | 12.49 | 4.99% APR at 99.999% utilisation, one update after 22 days |
| Euler v2 | 3.70e8 | 8.56 | 138.3% APR at 100% utilisation, one update after 1.3 days |

For Compound, every input is within one index unit. Its only error is the floor of an exact rational increment computed from the protocol's own per-second rate, so it loses 0 digits. On the units measure the worst cases at the top of the domain are the clamps. FraxLend's code stays at 18987324640 (60% APR) where the half-life reaches MAX (3164940920000, 10000% APR). Euler's code clamps to MAX (63419583967) where the truth is 63049328544, after wExp's 0.6% overshoot. The `tier` field was removed from `tiers-worst-protocols.json`; grading waits for the thresholds.

**Normal inputs (added 2026-10-30; the user: "1000% apr doesnt make sense. let's use normal inputs").** The top-level fields of each row in `tiers-worst-protocols.json` are now the worst over a normal envelope taken from the data. That file's `normal_envelope` field states it. The source is the 326 live positions of `docs/benchmarks/accrual-deployed.json` (group `live`). Annual rates run up to 0.6773, the largest Aave `rateAnnual` (live-aave-FRAX-borrow, 0.6772698566), and idle times run from 24 s to 29,409,252 s (340.4 days), the smallest and largest observed. Utilisation runs 0 to 100% for Compound's curves and the two rate models. Lower rates: from 0.0001% APR for Aave and SparkLend, from the rate model's floor (0.025% APR) for Morpho, and from the deployed minimum for FraxLend and Euler; FraxLend and Euler keep their deployed clamps. The search is the same as before (corners, grid, 12,000 seeded random), restricted to the envelope. The full-domain figures stay under `domain_worst`. One caveat: 28 of the 252 live Morpho markets charged more than the cap, up to 800% APR at 100% utilisation (the rate model's ceiling). `charged_envelope` repeats the search with the cap at 800% APR, and the `live_*` fields cover those markets directly.

| row | digits lost (normal) | worst units | worst input (units) | digits held there | live: lost, at | 800% cap | full domain |
|---|---|---|---|---|---|---|---|
| Aave v3 | 24.87 | 7.57e24 ray | 67.73% APR, idle 340.4 days | 2.06 | 17.21, FRAX borrow 67.7% APR, 4.3 days | 30.21 | 31.33 |
| SparkLend | 24.87 | 7.57e24 ray | 67.73% APR, idle 340.4 days | 2.06 | n/a | 27.83 (its 320% cap) | 27.98 |
| Morpho Blue | 15.87 | 7.57e15 WAD | 67.73% APR, idle 340.4 days | 2.06 | 21.16, lvlUSD 788% APR, 340.4 days | 21.21 | 21.45 |
| Compound v3 | 0.00 | 0.99995 index units | borrow side, 1.5% APR, 21303 s | (floor, < 1 unit) | n/a | 0.00 | 0.00 |
| FraxLend | 12.49 | 3.15e12 per-second units | 4.99% APR, 99.999% utilisation, one update after 22 days | 0.00 | n/a | 12.49 | 12.49 |
| Euler v2 | 8.50 | 3.18e8 per-second units | rate at target 63.9% APR, 100% utilisation, 4.0 days | (2.04 elsewhere) | n/a | 8.71 | 8.56 |

Aave, SparkLend and Morpho share one worst case, the top rate idle the longest time. The truncated series is about 0.66% short of e^0.632 − 1 there (2.06 digits held). The three differ in digits lost only by the scale of their last place: RAY for Aave and SparkLend, WAD for Morpho, nine decimals fewer. Digits lost therefore compares a protocol with its own format, not one protocol with another. Compound loses nothing: its index floors an exact increment and stays within one unit everywhere. Its fewest digits held, 0, is still the format's case (a 3e-9% APR rate over 24 s). For FraxLend, even inside the envelope one update after 22 days at 100% utilisation takes the half-life model to the 10000% APR clamp while the code gives 60%. So the worst output is far outside normal rates even though the inputs are normal. For Euler the worst case is wExp's 2nd-order step at |r| near ln2/2, with no clamp.

## Worst-case measurement (2026-10-30)

Exchange rows, measured by `scripts/tiers/measure_exchanges.py` (`uv run --with mpmath python scripts/tiers/measure_exchanges.py`; the recorded run used 64 processes on shrek, `TIERS_WORKERS=64`) into `talk/scenes/data/tiers-worst-exchanges.json`. Each function's integer arithmetic is transcribed from the pinned file (same constants, parsed from the fetched source and checked by sha256; same floors, ceilings and shifts; Solidity 0.7 wrap-around where the source relies on it) and compared with the exact value of the formula the protocol documents, mpmath at 120 digits. Curve's files are all rights reserved: the script fetches them at run time and translates get_D/get_y/__exchange/get_dy mechanically to Python; no Curve text is stored in the repo.

The row's number is **digits lost = log10(max(worst units, 1))**, so a correctly rounded answer loses 0. It is taken over NORMAL inputs (the user: "1000% apr doesnt make sense. let's use normal inputs", then: amounts and reserves of at least one whole token). Swap amounts and every reserve are 1..1e9 whole tokens, with token decimals 6, 8 or 18 on each side. Token prices are 1e-6..1e6. Tick maths uses |tick| ≤ 138,163 and LB ids with price 1e-6..1e6. TWAP windows are 60 s..1 day. Each row's `normal_range` states its exact range, and `domain_worst` keeps the whole documented domain.

For a swap, worst units counts the error in the smallest unit of the **more valuable token of the pair**: the error divided by max(1, average price). `worst_units_output_token` keeps the output token's own count. Single-value results (TickMath, LB price, TWAP, Pendle, GMX in its documented 30 decimals, Algebra, twocrypto get_y, Maverick) count in their own last place.

`held_floor[H]` for H = 25, 14, 10 is the fewest correct digits over the normal inputs whose exact value has at least H digits in the result's unit (null when there are none). For the swaps it is bounded by the amount the caller passes. One whole token of a 6-decimal token has 7 digits, so a fee floored or ceiled by one unit of input caps the output's relative accuracy near 1e-7 however many digits the output has. `worst_digits` (fewest correct digits anywhere in the normal range, including outputs of a few units) is kept for reference. No tier is assigned here. There are 13 exchange rows (the 14th row of the brief, Compound v3, is a protocol).

**Uniswap v2 swap (T1).** getAmountOut (v2-periphery @ 0335e8f7) is transcribed. The first 2,000 results of each run are checked against the pair's K inequality (v2-core @ 6a9e7c97 L180–182): out passes, out + 1 fails. Truth: amountIn·0.997·reserveOut/(reserveIn + 0.997·amountIn), exact rational. Every result is floor(exact). **0.00 digits lost**: under one unit, always down, over 200,000 whole-token trades plus 20,000 solved for an output just above one 18-decimal token. Domain (reserves to 2^112 − 1 and every power of two): also 0.00. held_floor 25.02 / 14.00 / 10.01: nothing is rounded but the output itself. getAmountIn returns floor(exact) + 1, a whole unit above when the division is exact.

**Uniswap v3/v4 swap step (T2).** SwapMath.computeSwapStep with SqrtPriceMath and FullMath is transcribed (v3-core @ 5ea68a77; v4-core @ bea7f6d1 has the same roundings). Truth: the documented constant-liquidity step, with the fee taken off the input as a real fraction, for exact-in (amountOut) and exact-out (amountIn + fee). The normal range is 150,000 steps whose virtual reserves L/√P and L·√P are each 1..1e9 tokens. **0.32 digits lost**: 2.07 units of the more valuable token, at exact-out zeroForOne, raw price 1.0e11, fee 9.1%. In the output token's own units the worst is 6.5e17: a floored input unit is worth up to the price ratio. held_floor 7.21 / 6.06 / 6.02, set by the fee floor of one unit on an input of about 1e7 units. Domain (MIN..MAX_SQRT_RATIO, liquidity to 1.9e32, amounts from 1e6 units): 4.78 lost. There, rounding the next √P to the Q64.96 grid moves the output by L/2^96 per grid step.

**Curve StableSwap (T3).** 3pool get_dy (@ 574f4402) and stableswap-ng __exchange (@ 3332cd44) are fetched and translated. Truth: the StableSwap invariant with Ann = A·n (the contracts' A is the paper's A·n^(n−1)), D and y solved exactly. The output is (x_j − y)(1 − fee)·1e18/rate_j, with ng's dynamic fee taken from its documented formula at the mid-trade balances. Normal range: balances 1..1e9 tokens within ×1e6 of each other, dx 1 token..min(1e9 tokens, 2× the balance in). Graded on precision only: reverts are excluded from the row. 150,000 swaps: **16.74 digits lost**, 5.4e16 units, ng with 2 coins of 18 decimals, balances 9.7e8 tokens each, dx 6.9e8 tokens, offpeg multiplier 2. The dynamic fee is an integer in 1e-10 units, so the output carries up to 1e-10 relative error. With a static fee the worst is 478 output-token units (2.68 lost; 3pool 2,582 units, 3.41 lost), counted in the output token's own unit. held_floor 9.94 / 9.76 / 9.76, the same 1e-10 fee step. Domain (to 1e10 tokens, dx from 1e6 units): 17.82 lost. **ng reverts inside the normal range**: 131 of the 150,000 (110 with every balance ≥ 1 token). Example: 4 coins of 6 decimals, balances 11,326,442.06 / 3,753.25 / 174.19 / 10,110.71 tokens, A = 200: get_D's Newton step alternates between …157413 and …157415 for all 255 iterations (the exact D is …157412.7) and never meets its "within 1" stop, so it raises. 3pool's get_D breaks after 255 iterations instead of raising.

**Aerodrome stable pool (T4).** Pool.getAmountOut / _getAmountOut / _get_y / _k (@ 1ba30815) are transcribed, including _get_y's call of _k(x0, y + 1) on already-normalised values. Truth: x³y + xy³ = k on decimal-normalised reserves, solved exactly after the input less fee/10000. Normal: 150,000 calls, reserves 1..1e9 tokens within ×1000, amountIn up to 2× the reserve in, fee 0..300. **0.05 digits lost**: 1.12 units, at 18/18 decimals with 1.5-token reserves, a 1.78-token trade and a 3% fee. In the output token's own units, a 6-decimal input against an 18-decimal output is off by up to 3.1e14 units, the floored fee unit priced in the cheaper token. No normal call reverts. held_floor 11.02 / 6.02 / 6.02: the fee is floored on a 6-decimal input of 1 to 57,000 tokens. Domain: 0.04 lost.

**Trader Joe LB swap in a bin (T5).** BinHelper.getAmounts with FeeHelper (@ 067c6ccf) is transcribed. Truth: amountIn(1 − fee)·P out (÷P for X), with P the documented (1 + binStep/10000)^(id − 2^23). For an emptied bin the truth is the input reserveOut/P/(1 − fee). Normal: 150,000 swaps at the bin nearest a token price of 1e-6..1e6, with reserves and amounts of 1..1e9 tokens and fees up to 10%. **0.31 digits lost**: 2.05 units, for an emptied bin at binStep 1, raw price 1.1e-4. In the output token's own units the worst is 9.9e17, the fee ceiling of one input unit. held_floor 7.19 / 6.02 / 6.01, the same fee ceiling on a small input. Domain (prices to 1e±38): 3.20 lost.

**Uniswap v3/v4 TickMath (T6).** getSqrtRatioAtTick is transcribed (constants parsed; v4's are identical). Truth: sqrt(1.0001^tick)·2^96. Every tick of [−887272, 887272] is swept, with the truth stepped in 2^-520 fixed point and checked against mpmath. Normal (|tick| ≤ 138,163, 276,327 ticks): **0.00 digits lost**. The worst is 1.000122 units at tick 133129, a positive tick where the inversion leaves the ceiling just over one unit above exact. Every negative normal tick returns ceil(exact). held_floor 25.90 at every threshold (tick −138157). Domain: 28.89 lost at tick 887234, where `type(uint256).max / ratio` inverts a small ratio. Only 9.64 digits are held at MIN_TICK, where the Q64.96 value is 4.3e9.

**Trader Joe LB bin price (T7).** getPriceFromId = Uint128x128Math.pow(getBase(binStep), id − 2^23) is transcribed. Truth: (1 + binStep/10000)^(id − 2^23)·2^128. Every id at bin steps 1, 2, 5, 8, 10, 15, 20, 25, 50, 80, 100, 150, 200 and 250 is swept outward until pow reverts. Normal (price 1e-6..1e6, 591,452 ids): **12.14 digits lost**, 1.38e12 units, at binStep 2, id 2^23 + 69083 (price 1e6). Above 1 the base exceeds 2^128 − 1, so pow inverts it, raises 1/base and divides `type(uint256).max` by the result. A 45-digit price therefore comes back with the 32 digits of a 2^128·1e-6 intermediate. held_floor 32.39 at every threshold. Domain: 76.76 lost at binStep 1, id 2^23 + 880341.

**Uniswap v3 TWAP (T8).** OracleLibrary.consult's mean tick (@ 24ccf014, L34–36) and getQuoteAtTick with TickMath are transcribed. Truth: baseAmount·1.0001^(tickCumulativesDelta/secondsAgo). Normal: 150,000 windows of 60 s..1 day, mean |tick| < 138,163, baseAmount 1..1e9 tokens. **29.00 digits lost**, 1.0e29 units, on a 1-day window with mean tick −138161.0000116 floored to −138162 and baseAmount 1e9 18-decimal tokens. The floor costs up to one tick, 1e-4 of the price, on a quote of about 33 digits. held_floor 4.00 at every threshold. Domain: 72.63 lost.

**Pendle exchange rate (T9).** In _getExchangeRateFromImpliedRate (@ 87685c89), rt = lnImpliedRate·timeToExpiry/365 days is floored, then LogExpMath.exp runs (transcribed, with a0..a11/x0..x11 parsed). Truth: e^(lnImpliedRate/1e18·timeToExpiry/365 days)·1e18. Normal: 150,000 inputs with implied APY 0..100% and expiry 1 day..2 years. **0.99 digits lost**: 9.8 units, always low, at APY 87% over 1.99 years. held_floor null / 17.44 / 17.44 (an 18-decimal rate near 1..4 has 19 digits). Domain (rt up to 130): 56.75 lost.

**GMX v2 price impact (T10).** Precision.applyExponentFactor (@ a85ea349) is transcribed with PRBMathUD60x18.pow = exp2(mul(log2 x, y)) from prb-math v2.4.3 (commit 8cb5b772, the version gmx's package.json pins; exp2's 64 factors parsed). Truth: (floatValue/1e30)^(exponent/1e30)·1e30, counted in the documented 30 decimals. Normal: 150,000 inputs from 1 to 1e9 USD, with exponent in (1, 3]. **40.54 digits lost**: 3.5e40 units at 1e9 USD with exponent 3. The result is a 30-decimal number computed in 18 decimals and multiplied back by 1e12, and the 18-decimal pow holds about 16.3 digits of a 58-digit value. held_floor 16.28 at every threshold. Domain (to 1e12 USD): 49.48 lost. Below 1 USD the function returns 0 by design.

**Curve twocrypto-ng get_y (T11).** get_y (the cubic, falling back to _newton_y) and newton_y (@ 5cbe5589, constants.vy) are fetched and translated. Truth: K·D·(x + y) + xy = K·D² + (D/2)², with K = A·K0·γ²/(γ + 1 − K0)², K0 = 4xy/D² and A = ANN/(A_MULTIPLIER·4). The code's newton_y agrees with this root to 1e-18. Normal: x_j of 1..1e9 tokens (1e18..1e27 in price-scaled units) inside the asserted K0 band, D up to 2e27, A and gamma over their whole ranges. **12.91 digits lost**: 8.2e12 units at newton_y(ANN 113106, gamma 1.18e13, x_j 1.07e25, D 1.97e27), where y = 9.05e28 comes back 9.0e-17 high. held_floor 15.34 / 14.36 / 14.36. Domain (D to 1e33): 18.55 lost.

**Algebra V1 dynamic fee (T12).** AdaptiveFee.getFee/sigmoid/exp (v1.0.0 @ 60d71de0) is transcribed at AlgebraFactory's default configuration, parsed from the file: alpha1 2900, alpha2 12000, beta1 360, beta2 60000, gamma1 59, gamma2 8500, volumeBeta 0, volumeGamma 10, baseFee 100. Truth: baseFee + sigmoidV(sigmoid1 + sigmoid2), each sigmoid α/(1 + e^((β − x)/γ)) real. The sweep is exhaustive: every volatility 0..112000 × every volumePerLiquidity 0..100, 11.3 million inputs. **1.82 digits lost**: 66.4 units (of 1e-6), at volatility 111000 = beta2 + 6·gamma2, where the code returns alpha2 for a sigmoid worth 0.9975·alpha2. held_floor null (a uint16 fee has at most 5 digits). Only 0.83 digits are held at volatility 6: both sigmoids are past their 6γ cut and return 0 where they are worth 7.2 and 10.3 units.

**Maverick v2 TickMath (T14).** tickSqrtPrice is transcribed with its 19 constants parsed. Truth: sqrt(1.0001^tick)·1e18. Every subtick of ±322,378 is swept. Normal (|tick| ≤ 138,163): **8.88 digits lost**, 7.6e8 units, at tick 138163, where 12.12 of the value's 21 digits are held. held_floor null / 12.12 / 12.12. Domain: 13.25 lost at tick 322378.

| row | digits lost | worst units | held_floor 25 / 14 / 10 | domain lost |
|---|---|---|---|---|
| Uniswap v2 swap | 0.00 | 0.99999 | 25.02 / 14.00 / 10.01 | 0.00 |
| Uniswap v3/v4 swap step | 0.32 | 2.07 | 7.21 / 6.06 / 6.02 | 4.78 |
| Curve StableSwap | 16.74 | 5.4e16 | 9.94 / 9.76 / 9.76 | 17.82 |
| Aerodrome stable | 0.05 | 1.12 | 11.02 / 6.02 / 6.02 | 0.04 |
| Trader Joe LB swap | 0.31 | 2.05 | 7.19 / 6.02 / 6.01 | 3.20 |
| Uniswap TickMath | 0.00 | 1.000122 | 25.90 / 25.90 / 25.90 | 28.89 |
| Trader Joe LB price | 12.14 | 1.38e12 | 32.39 / 32.39 / 32.39 | 76.76 |
| Uniswap v3 TWAP | 29.00 | 1.0e29 | 4.00 / 4.00 / 4.00 | 72.63 |
| Pendle | 0.99 | 9.8 | – / 17.44 / 17.44 | 56.75 |
| GMX v2 | 40.54 | 3.5e40 | 16.28 / 16.28 / 16.28 | 49.48 |
| Curve twocrypto get_y | 12.91 | 8.2e12 | 15.34 / 14.36 / 14.36 | 18.55 |
| Algebra V1 fee | 1.82 | 66.4 | – / – / – | 1.82 |
| Maverick v2 TickMath | 8.88 | 7.6e8 | – / 12.12 / 12.12 | 13.25 |

**short18 (added 2026-10-30; the user's blended number, which replaces "both must pass").** Per row: the worst over the normal envelope (rates up to 800% APR or the row's own maximum, idle 24 s to 340.4 days) of max(0, min(format digits at the value, 18) − digits held). Format digits = log10(|exact| / unit) in the row's unit. Digits held = −log10 of the relative error of the interest factor (or the rate), clamped at 0. Results: Aave v3 17.97 (800% APR, 340.4 days; format 30.23, held 0.02); SparkLend 17.56 (320% APR, 340.4 days; format 28.27, held 0.43); Morpho Blue 17.97 (800% APR, 340.4 days; format 21.23, held 0.02); Compound v3 0 at every input (each answer within one index unit, so held ≥ format digits everywhere); FraxLend 12.49 (4.99% APR start, 99.999% utilisation, 22 days; format 12.5, held 0.00); Euler v2 8.71 (rate at target 17.2% APR, 100% utilisation, 8.9 days; format 10.79, held 2.07). `correctly_rounded` is true only for Compound v3: its worst error is 0.99995 of a unit, in the floor direction its code states.

**short18 (the user's blended number, 2026-10-30).** Per row, the worst over the same normal inputs of max(0, min(format digits, 18) − digits held). Format digits = log10(|exact|/unit) in the unit the errors are counted in (a swap's more valuable token); digits held = −log10 of the relative error. The JSON fields are `short18`, `short18_input` and `short18_format_digits`. Results: Uniswap v2 0.00; Uniswap v3/v4 swap 0.32; Curve StableSwap 8.24; Aerodrome 0.03; LB swap 0.31; TickMath 0.00; LB price 0.00; TWAP 14.00; Pendle 0.56; GMX v2 1.72; twocrypto get_y 3.64; Algebra 1.82; Maverick 5.88. `correctly_rounded` (under 0.5 unit, or under 1 unit in one direction, on every normal input) is true only for Uniswap v2. TickMath misses by 1.000122 units at tick 133129.

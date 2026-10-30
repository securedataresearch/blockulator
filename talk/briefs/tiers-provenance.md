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

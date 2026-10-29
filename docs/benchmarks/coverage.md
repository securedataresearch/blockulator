# Comparison coverage

Every function of every comparison library, from the source in `lib/` and `contracts/src/ladder/vendor/`, mapped to the BL127 or BL19 op it computes, or listed as not compared with the reason. The gas harnesses are `test/bl127/GasLadder.t.sol` (`make bench` → [gas.md](gas.md), gas.json) and `test/bl19/GasLadder.t.sol` (`make bench-bl19` → [gas19.md](gas19.md), gas19.json). The exact call behind each cell is `CALLS` in `scripts/bl127/gas_to_json.py`, written to gas.json as `calls`. The bench fails if a measured cell has no `CALLS` entry, or an entry has no cell.

Versions: Solady v0.1.26, PRBMath v4.2.0 (SD59x18 and UD60x18), ABDK v3.2, Balancer LogExpMath from balancer-v3-monorepo@2b9ce4b1b8ad (vendored), Solmate main@89365b8, OpenZeppelin Contracts v5.7.0 (vendored), Uniswap v4-core v4.0.0 FullMath (vendored), snekmate v0.1.2 (Vyper 0.4.3).

## Which libraries

The bar is an established library: published, with tagged releases, maintained, used by deployed protocols, and under a licence that lets this repository build it. Each candidate was checked against its official repository on 2026-10-23.

| library | language | verdict | version | why |
|---|---|---|---|---|
| Solady `FixedPointMathLib` | Solidity | in (already) | v0.1.26 | |
| PRBMath SD59x18 | Solidity | in (already) | v4.2.0 | |
| ABDKMath64x64, ABDKMathQuad | Solidity | in (already) | v3.2 | |
| Balancer `LogExpMath` | Solidity | in (already) | v3 monorepo @2b9ce4b1b8ad | |
| **PRBMath UD60x18** | Solidity | **added** | v4.2.0 (the submodule already pinned) | The unsigned half of PRBMath: same release, same users as SD59x18. Its exp, ln and log2 are different code from SD59x18's. |
| **Solmate** `FixedPointMathLib` + `SignedWadMath` | Solidity | **added** | main@89365b8 (2025-07); submodule `lib/solmate` | 4,300 stars, audited major releases, the maths behind Solmate's ERC4626 and the VRGDAs. The only tag, v6 (2022), predates `SignedWadMath`, so the pin is the main commit that `forge install transmissions11/solmate` fetches. `FixedPointMathLib.sol` is AGPL-3.0-only, so it is a submodule and is not vendored, and the adapter that links it, `LadderSolmate.sol`, is AGPL-3.0-only. `SignedWadMath.sol` is MIT. |
| **OpenZeppelin** `Math`, `SignedMath` | Solidity | **added** | v5.7.0 (2026-07); vendored, MIT | The most used Solidity library, audited every release. Its maths is integer maths: `mulDiv` with a rounding mode, `sqrt`, the integer logs, `average`. It enters wherever a WAD op is that integer function with 10^18 put in (mulDown = `mulDiv(a, b, 1e18)` and so on). |
| **Uniswap v4-core** `FullMath` | Solidity | **added** | v4.0.0; vendored, MIT | The `mulDiv` and `mulDivRoundingUp` inside every Uniswap v3 and v4 pool. v3-core's copy needs solc < 0.8; v4-core's is the same algorithm for 0.8. |
| Uniswap `TickMath` | Solidity | not compared | v4.0.0 | No op computes it: `getSqrtPriceAtTick(t)` is the fixed-base power sqrt(1.0001)^t in Q64.96, and `getTickAtSqrtPrice` its floor log, on the integer tick grid. |
| DappHub `ds-math` | Solidity | rejected | none | No tagged release, no commit since 2022, GPL-3.0. Its `wmul`/`rmul` are half-up `x * y / WAD`, and its `rpow` is the one Maker deployed, which the ladder already runs as `LadderMaker`. |
| Balancer `FixedPoint` | Solidity | rejected | | GPL-3.0-or-later, so it cannot be vendored here; Balancer's mulDown/divDown are reproduced in `LadderBalancer` as before. |
| **snekmate** `math` | Vyper | **added** | v0.1.2 (2025-06), compiled with Vyper 0.4.3 as it requires; submodule `lib/snekmate` | The standard Vyper library, on PyPI and npm, and in production: Curve's twocrypto-ng imports its `math` module, and the modules Curve uses were reviewed in Curve's audits. AGPL-3.0-only, so it is a submodule, and the wrapper that exports it, `contracts/src/ladder/vyper/SnekmateMath.vy`, is AGPL-3.0-only. |
| Curve tricrypto-ng / twocrypto-ng / stableswap-ng maths | Vyper | rejected | | Licence: "Copyright (c) Curve.Fi, 2020-2023 - all rights reserved", and "only contracts owned by Curve DAO or Swiss Stake GmbH are allowed to call this contract". The functions are compared anyway: `wad_exp` is snekmate's `_wad_exp` (a verbatim copy in tricrypto-ng and stableswap-ng, an import in twocrypto-ng), and snekmate's `_wad_cbrt` is Curve's `_cbrt`, the same constants and seven Newton steps. `geometric_mean` takes three coins; no op does. |
| huffmate `FixedPointMath` | Huff | rejected | v1.1 (2023-02) | Its README: "unaudited and are not recommended for use in production". No production users found, no release since 2023. Its fixed-point maths is a port of Solmate's, which is compared. |
| pure-Yul maths libraries | Yul | none exist | | No published, tagged, adopted Yul maths library exists beyond Solady's inline assembly, which is compared. |

**What a cell means.** A number is the median gas over the op's input ladder. An empty cell means the library does not offer the op, and only that. `rev` means the library offers the op but reverted on every ladder input, or every input was outside the function's domain or format. In gas.json, `ops[op].reverts[form]` counts such inputs per form; the medians leave them out. After this audit no `rev` cell remains: every function benched computes on at least part of its op's ladder.

**Which table.** BL127's table compares the WAD libraries (Solady, PRBMath SD59x18 and UD60x18, Balancer, Solmate, OpenZeppelin, Uniswap FullMath, snekmate), 64.64 and binary128. The five added with issue #166 have their entry points in `test/bl127/GasLibs.sol`. BL19's table compares binary128, the other float, and BL127Lib on the same value. The WAD and 64.64 libraries are not repeated on BL19's table: every op they share with BL19 is also an BL127 op, so it is compared there.

**Statuses.**
- compared: benched before this audit, on the same function.
- new: benched by this audit.
- fixed: was benched under the wrong op or was not the library's function.
- domain: benched on the part of the ladder inside the function's domain. The other inputs count as reverting (REV), never as not offered.
- variant: the same function as a benched one (an unchecked twin, an unsigned overload, an alias), not benched again.
- none: no FP op computes the same function; see "Not compared" below.

Conversions into each library's representation happen once, outside the timed window. They are: WAD = `BL127Lib.toFixed18`; 64.64 = `x >> 64` (REV where it does not fit int128); binary128 = `ABDKMathQuad.from128x128` on BL127's table, and on BL19's a direct repacking of the BL19 word (sign, rebiased exponent, fraction truncated to 112 bits).

## Solady FixedPointMathLib (78 functions, counting overloads)

| function | op | benched | status |
|---|---|---|---|
| `sMulWad(int256, int256)` | mul | yes | compared (rounds toward zero; BL127's `mul` floors) |
| `sDivWad(int256, int256)` | div | yes | compared; also `inv` as `sDivWad(1e18, x)`, composed |
| `mulWad(uint256, uint256)` | mulDown | yes | compared, domain a, b ≥ 0 |
| `mulWadUp(uint256, uint256)` | mulUp | yes | compared, domain a, b ≥ 0 |
| `divWad(uint256, uint256)` | divDown | yes | compared, domain a ≥ 0, b > 0 |
| `divWadUp(uint256, uint256)` | divUp | yes | compared, domain a ≥ 0, b > 0 |
| `powWad(int256, int256)` | pow | yes | compared (the exponent is a WAD) |
| `expWad(int256)` | exp | yes | compared |
| `lnWad(int256)` | ln | yes | compared |
| `lambertW0Wad(int256)` | lambertW0 | yes | compared |
| `sqrtWad(uint256)` | sqrt | yes | compared, domain x ≥ 0 (was given negative words as uint256) |
| `cbrtWad(uint256)` | cbrt | yes | compared, domain x ≥ 0 (as above; BL127's cbrt takes negatives) |
| `abs(int256)` | abs | yes | new |
| `avg(int256, int256)` | avg | yes | new (floors, as BL127's) |
| `dist(int256, int256)` | dist | yes | new |
| `min(int256, int256)` | min | yes | new |
| `max(int256, int256)` | max | yes | new |
| `clamp(int256, int256, int256)` | clamp | yes | new (clamp joined BL127's gas ladder in this audit) |
| `lerp(int256 a, b, t, begin, end)` | lerp | yes | new, domain t ∈ [0, 1]: called as `lerp(a, b, t, 0, 1e18)`; Solady clamps t to [begin, end], BL127 does not |
| `zeroFloorSub(uint256, uint256)` | zeroFloorSub | yes | new, domain a, b ≥ 0 |
| `mulSqrt(uint256, uint256)` | gavg | yes | new, domain a, b ≥ 0: sqrt(x y) of two WADs is the WAD geometric mean |
| `rpow(uint256 x, uint256 y, uint256 b)` | powu | yes | new, domain x ≥ 0, integer n ≥ 0: `rpow(x, n, 1e18)` |
| `factorial(uint256)` | factorial | yes | new, domain integral x: given the plain integer, returns the plain integer n! |
| `log2Up(uint256)` | log2Up | yes | new, domain integral x ≥ 1: ceil(log2 n) of the plain integer, which BL127's `log2Up` is on integers |
| `rawAdd(int256, int256)` | add | yes | fixed: the cell was Solidity's checked `a + b`, which is not a Solady function; it is now Solady's unchecked `rawAdd` |
| `rawSub(int256, int256)` | sub | yes | fixed, as `rawAdd` |
| `rawMulWad`, `rawSMulWad`, `rawMulWadUp`, `rawDivWad`, `rawSDivWad`, `rawDivWadUp` | mul, mulDown, … | no | variant: the unchecked twins of the six above |
| `avg`, `dist`, `min`, `max`, `clamp`, `lerp` (uint256 overloads) | | no | variant: BL127 is signed; the int256 overloads are benched |
| `saturatingSub(uint256, uint256)` | zeroFloorSub | no | variant: `zeroFloorSub` is its alias |
| `fullMulEq`, `fullMulDiv`, `fullMulDivUnchecked`, `fullMulDivUp`, `fullMulDivN`, `mulDiv`, `mulDivUp` | | no | none |
| `invMod`, `divUp`, `saturatingAdd`, `saturatingMul`, `gcd`, `isEven` | | no | none |
| `ternary` ×3, `coalesce` ×3 | | no | none |
| `sqrt(uint256)`, `cbrt(uint256)`, `log2(uint256)`, `log10(uint256)`, `log10Up(uint256)`, `log256(uint256)`, `log256Up(uint256)` | | no | none |
| `sci`, `packSci`, `unpackSci` | | no | none |
| `rawAdd`, `rawSub` (uint256), `rawMul` ×2, `rawDiv`, `rawSDiv`, `rawMod`, `rawSMod`, `rawAddMod`, `rawMulMod` | | no | none |

12 compared, 14 new (2 of them fixed), 12 variants, 40 none; 12 of the benched functions are domain-limited.

## PRBMath SD59x18 (54 functions: Math 18, Helpers 21, Conversions 2, Casting 13)

| function | op | benched | status |
|---|---|---|---|
| `abs`, `avg`, `ceil`, `div`, `exp`, `exp2`, `floor`, `frac`, `inv`, `ln`, `log10`, `log2`, `mul`, `pow`, `sign`, `sqrt` | the same names | yes | compared |
| `gm` | gavg | yes | compared |
| `powu(SD59x18, uint256)` | powu | yes | new, domain integer n ≥ 0 |
| `add` (Helpers) | add | yes | fixed: the cell was Solidity's `a + b`; it is now PRB's checked `add` |
| `sub` (Helpers) | sub | yes | fixed, as `add` |
| `unary` (Helpers) | neg | yes | new |
| `uncheckedAdd`, `uncheckedSub`, `uncheckedUnary` | add, sub, neg | no | variant: the unchecked twins |
| `and`, `and2`, `or`, `xor`, `not`, `lshift`, `rshift` | | no | none |
| `mod` | | no | none |
| `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `isZero` | | no | none (BL127 table); not compared on the BL19 table |
| `convert(int256)`, `convert(SD59x18)` | | no | none (BL127 table); not compared on the BL19 table |
| `intoInt256`, `intoSD1x18`, `intoSD21x18`, `intoUD2x18`, `intoUD21x18`, `intoUD60x18`, `intoUint256`, `intoUint128`, `intoUint40`, `sd`, `sd59x18`, `unwrap`, `wrap` | | no | none |

17 compared, 4 new (2 of them fixed), 3 variants, 30 none; `powu` is domain-limited.

## ABDKMath64x64 (25 exported, 2 private)

| function | op | benched | status |
|---|---|---|---|
| `add`, `sub`, `mul`, `div`, `neg`, `abs`, `inv`, `avg`, `gavg`, `sqrt`, `ln`, `exp` | the same names | yes | compared |
| `log_2` | log2 | yes | compared |
| `exp_2` | exp2 | yes | compared |
| `pow(int128, uint256)` | powu | yes | fixed, domain integer n ≥ 0: it takes a plain unsigned integer exponent, so it is `powu`. It had been benched as real `pow`, with the 64.64 exponent truncated to an integer (e → 2, 2.5 → 2, −3 → a huge uint256) |
| `fromInt`, `toInt`, `fromUInt`, `toUInt`, `from128x128`, `to128x128` | | no | none |
| `muli`, `mulu`, `divi`, `divu` | | no | none |
| `divuu`, `sqrtu` | | | private |

14 compared, 1 fixed (now powu), 10 none; `pow` is domain-limited.

## ABDKMathQuad (28 exported, 1 private)

| function | op | benched | status |
|---|---|---|---|
| `add`, `sub`, `mul`, `div`, `neg`, `abs`, `sqrt`, `ln`, `exp` | the same names | yes, both tables | compared |
| `log_2` | log2 | yes, both tables | compared |
| `pow_2` | exp2 | yes, both tables | compared |
| (`div(fromUInt(1), x)`) | inv | yes, both tables | composed; new on BL19's table |
| (`exp(mul(y, ln(x)))`) | pow | yes, both tables | composed |
| `sign` | sign | yes, both tables | new |
| `cmp` | cmp (BL19); also `lt` as `cmp(a, b) < 0`, composed | yes, BL19 | new |
| `eq` | eq (BL19) | yes, BL19 | new |
| `toUInt` | toUintDown (BL19) | yes, BL19 | new: truncates, which is floor on the ladder's non-negative inputs |
| `toInt` | toIntDown (BL19) | yes, BL19 | new, domain x ≥ 0: truncation is floor only there |
| `fromUInt` | fromUintDown (BL19) | yes, BL19 | new: truncates the significand, which is BL19's `fromUintDown`, not its rounding `fromUint` |
| `from128x128` | fromBL127 (BL19) | yes, BL19 | new: truncates where BL19 rounds to nearest; on BL127's table it is the input conversion |
| `to128x128` | toBL127 (BL19) | yes, BL19 | new: truncates where BL19 rounds to nearest |
| `fromInt`, `from64x64`, `to64x64`, `fromOctuple`, `toOctuple`, `fromDouble`, `toDouble`, `isNaN`, `isInfinity` | | no | none |
| `mostSignificantBit` | | | private |

11 compared, 8 new, 9 none; `toInt` is domain-limited.

## Balancer LogExpMath (4 internal, 2 private)

| function | op | benched | status |
|---|---|---|---|
| `exp(int256)` | exp | yes | compared |
| `ln(int256)` | ln | yes | compared |
| `pow(uint256, uint256)` | pow | yes | compared, domain x, y ≥ 0 (was given negative exponents as uint256); also `sqrt` = `pow(x, 0.5e18)` and `cbrt` = `pow(x, 333333333333333333)`, composed, x ≥ 0 |
| `log(int256 arg, int256 base)` | log2, log10 | yes | new: `log(x, 2e18)` and `log(x, 10e18)` |
| `_ln`, `_ln_36` | | | private |

The `mul` and `div` cells are removed. They measured Solidity's `a * b / 1e18` and `a * 1e18 / b`, not LogExpMath functions; Balancer's own `mulDown`/`divDown` live in `FixedPoint`, which is not vendored.

3 compared, 1 new, 2 cells removed; `pow` is domain-limited.

## PRBMath UD60x18 (49 functions: Math 16, Helpers 19, Conversions 2, Casting 12)

| function | op | benched | status |
|---|---|---|---|
| `avg`, `ceil`, `div`, `exp`, `exp2`, `floor`, `frac`, `inv`, `ln`, `log10`, `log2`, `mul`, `pow`, `sqrt` | the same names | yes | new, domain x ≥ 0 (and y ≥ 0 for pow) |
| `gm` | gavg | yes | new, domain a, b ≥ 0 |
| `powu(UD60x18, uint256)` | powu | yes | new, domain x ≥ 0, integer n ≥ 0 |
| `add`, `sub` (Helpers) | add, sub | yes | new, domain a, b ≥ 0 (sub reverts below zero) |
| `uncheckedAdd`, `uncheckedSub` | add, sub | no | variant |
| `and`, `and2`, `or`, `xor`, `not`, `lshift`, `rshift`, `mod`, `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `isZero` | | no | none (as SD59x18's) |
| `convert` ×2, `intoSD1x18`, `intoSD21x18`, `intoUD2x18`, `intoUD21x18`, `intoSD59x18`, `intoUint256`, `intoUint128`, `intoUint40`, `ud`, `ud60x18`, `unwrap`, `wrap` | | no | none |

18 new, 2 variants, 29 none; all 18 domain-limited. UD60x18 is also in the WAD table (`make wad`): its mul, div and sqrt were already PRBMath's rows there, and its exp, ln, log2, log10 and pow, separate code from SD59x18's, are new rows, scored on their domain (x ≥ 0; the logs x ≥ 1).

## Solmate (FixedPointMathLib 11 functions, SignedWadMath 11)

| function | op | benched | status |
|---|---|---|---|
| `wadMul(int256, int256)` | mul | yes | new (sdiv: toward zero) |
| `wadDiv(int256, int256)` | div | yes | new (toward zero) |
| `wadExp`, `wadLn` | exp, ln | yes | new |
| `wadPow(int256, int256)` | pow | yes | new: `wadExp(wadLn(x) * y / 1e18)`, x > 0 |
| `mulWadDown`, `mulWadUp` | mulDown, mulUp | yes | new, domain a, b ≥ 0 |
| `divWadDown`, `divWadUp` | divDown, divUp | yes | new, domain a, b ≥ 0 |
| `rpow(uint256 x, uint256 n, uint256 scalar)` | powu | yes | new, domain x ≥ 0, integer n ≥ 0: `rpow(x, n, 1e18)` |
| `sqrt(uint256)` | sqrt | yes | new, composed, domain x ≥ 0: the integer root of x · 10^18 is the WAD root, the only root Solmate has |
| `unsafeWadMul`, `unsafeWadDiv` | mul, div | no | variant: the unchecked twins |
| `mulDivDown`, `mulDivUp` | | no | none: a free denominator (as Solady's `fullMulDiv`) |
| `toWadUnsafe`, `toDaysWadUnsafe`, `fromDaysWadUnsafe`, `unsafeMod`, `unsafeDiv` ×2, `unsafeDivUp` | | no | none: conversions and raw integer division |

11 new (1 composed), 2 variants, 9 none. Solmate's exp, ln and pow are Remco Bloemen's, as Solady's are: on the WAD table their wrong-wei counts are Solady's to the input.

## OpenZeppelin Math (39 functions, counting overloads) and SignedMath (5)

| function | op | benched | status |
|---|---|---|---|
| `mulDiv(x, y, d)`, `mulDiv(x, y, d, Rounding)` | mulDown, mulUp, divDown, divUp | yes | new, domain a, b ≥ 0: `mulDiv(a, b, 1e18[, Ceil])` and `mulDiv(a, 1e18, b[, Ceil])` |
| `sqrt(uint256)`, `sqrt(uint256, Rounding)` | sqrt | yes | new, composed, domain x ≥ 0: `sqrt(x * 1e18)`; the Ceil overload is on the WAD table (sqrtWadUp) |
| `log2(uint256, Rounding)` | log2Up | yes | new, domain integral x ≥ 1, `Rounding.Ceil` |
| `saturatingSub(uint256, uint256)` | zeroFloorSub | yes | new, domain a, b ≥ 0 |
| SignedMath `abs`, `min`, `max` | abs, min, max | yes | new |
| SignedMath `average` | avg | yes | new (rounds toward zero; BL127's avg floors) |
| `max`, `min`, `average` (uint256), SignedMath `ternary`, Math `ternary` | | no | variant / none |
| `ceilDiv`, `tryAdd`, `trySub`, `tryMul`, `tryDiv`, `tryMod`, `saturatingAdd`, `saturatingMul`, `add512`, `mul512`, `mulShr` ×2, `invMod`, `invModPrime`, `modExp` ×2, `tryModExp` ×2, `log2(uint256)`, `log10` ×2, `log256` ×2, `unsignedRoundsUp`, `clz` | | no | none: integer arithmetic, number theory and floor logs (as Solady's) |

11 new (1 composed), 2 variants, the rest none. OpenZeppelin has no exp, ln or real power, so on the ladder it answers the scenarios built from mul, div and the root, and is Unsupported on the rest.

## Uniswap v4-core FullMath (2 functions)

| function | op | benched | status |
|---|---|---|---|
| `mulDiv(a, b, d)` | mulDown, divDown | yes | new, domain a, b ≥ 0: `mulDiv(a, b, 1e18)`, `mulDiv(a, 1e18, b)` |
| `mulDivRoundingUp(a, b, d)` | mulUp, divUp | yes | new, as above |

4 new. On the ladder FullMath answers the scenarios built from mul and div alone. `TickMath` is not compared ("Which libraries").

## snekmate math (12 functions)

| function | op | benched | status |
|---|---|---|---|
| `_wad_exp`, `_wad_ln` | exp, ln | yes | new (`_wad_ln(0)` returns 0) |
| `_wad_cbrt(uint256)` | cbrt | yes | new, domain x ≥ 0 |
| `_mul_div(x, y, d, roundup)` | mulDown, mulUp, divDown, divUp | yes | new, domain a, b ≥ 0 |
| `_int256_average` | avg | yes | new (floors, as BL127's) |
| `_signum` | sign | yes | new |
| `_log2(uint256, roundup)` | log2Up | yes | new, domain integral x ≥ 1, `roundup = True` |
| `_uint256_average` | avg | no | variant |
| `_ceil_div`, `_log10`, `_log256`, `_cbrt` (the integer root) | | no | none (as Solady's) |

10 new, 1 variant, 4 none. snekmate is Vyper: `contracts/src/ladder/vyper/SnekmateMath.vy` exports the module, built by `scripts/ladder/vyper.py` with the compiler snekmate pins (0.4.3). Its gas cells are the module call as that contract times it with `msg.gas`, net of the same window around an assignment, so no external call is in them; on the ladder the adapter makes one staticcall per op, as BL127's deployed form does. snekmate has no square root and no real power: the ladder takes the root with Vyper's built-in `isqrt(x * 10**18)` and pow as `wad_exp(wad_ln(x) * y / 1e18)`, as Solmate composes it; neither is on the gas or WAD tables.

## Protocols: Aave, Morpho, Maker, FraxLend, Euler v2

Their maths is transcribed for the ladder only: the accrual of Aave (`MathUtils`), Morpho (`MathLib`) and Maker (`rpow`), and the adaptive rate models of FraxLend (`VariableInterestRate` V2) and Euler v2 (`IRMAdaptiveCurve` with `ExpLib`). No op table claims to cover them, and they are not on the gas tables. Pins and licences are in `contracts/src/ladder/vendor/README.md`; `test/accrual/DeployedAccrual.t.sol` and `test/accrual/DeployedRates.t.sol` (`make rates-verify`, a mainnet fork) check the transcriptions against the deployed code.

Which protocols' deployed maths the ladder measures was decided by a pass over about twenty deployed lending, perps and DAO-run protocols (issue #178), each function read at a pinned commit, the deployed source compared where an explorer serves it, and the error computed against the model the protocol documents:

- **A: in the ladder.** The deployed code departs from the model its own documentation or comments state, on realistic inputs, by more than an exact exp or a finer grid would leave.
- **B: out, the departure is small or needs unrealistic inputs.**
- **C: out, exact enough, or the shortcut is the documented model.**

| grade | protocol | function | what the code computes, against what it states | why |
|---|---|---|---|---|
| A | FraxLend `VariableInterestRate` V2 (fraxlend @2bed49d4, ISC; rate contract `0x18500cB1…F261`) | `getFullUtilizationInterest`, charged by `FraxlendPairCore._calculateInterest` | One update after dt: F (1 + d² dt / H) above the band, F H / (H + d² dt) below it. The documentation states a half-life: "the increase will be 100% per half-life" at 100% utilisation, "decrease by 50% each half-life" at 0%, 2^(±t/H). The two agree at dt = H only: after 2H one update gives 3× (documented 4×), after H/2 1.5× (documented 1.414×); hourly updates over a half-life give 2.69× and 0.372× (documented 2× and 0.5×). The pair then charges the new rate over the whole interval as simple interest. | Ladder scenario `adaptive-rate`, `LadderFraxlend` |
| A | Euler v2 `IRMAdaptiveCurve` (evk-periphery @af436991, MIT; factory `0x3EC2d5af…7F42`, 14 deployments) | `_newRateAtTarget` through `ExpLib.wExp` | The comment states rateAtTarget = startRateAtTarget · e^linearAdaptation; `wExp` reduces x by ln 2 and takes 1 + r + r²/2 (Morpho's ExpLib). At the deployed speed (100 per year), 100% utilisation, the stored rate at target is −0.28% off after an idle day and +0.08% after a week; at 0% utilisation, +0.42% after a day. Every later rate multiplies the stored one, so the error stays. | Ladder scenario `adaptive-rate`, `LadderEuler` |
| B | SparkLend (Aave v3.0.2 fork, BUSL-1.1) | `MathUtils.calculateCompoundedInterest` | The older three-term binomial with floored powers: 6 to 9 digits of the interest against its stated (1 + r/SPY)^n, and the cubic term is 0 for every APR below 3.15%. | A different formula from `LadderAave`'s, but the loss is about $1e-5 on $100M idle a day at 3%; the supply side is the same linear index as Aave's. |
| B | Compound v3 (Comet, BUSL-1.1) | `accruedInterestIndices` | Simple interest per touch, which the docs state (an APR, "accrues every second"); the index is 15 digits (1e15 in a uint64) and floored at each accrual, about 1.4e-6 of the interest at 1% APR when touched every second. | The accrual is the documented model; the index grid loss is about $10 a year on a $500M market. |
| C | Compound v2 | `CToken.accrueInterest` | Simple interest per touch; the docs say interest "compounds only during blocks in which" the market is touched. | Documented. |
| C | Fluid | `LiquidityCalcs.calcExchangePrices` | Linear accrual, the rate in 0.01% steps, storage written past a threshold or after a day; the comments say the rounding favours the protocol. | Deliberate packing. |
| C | Liquity v1 / v2 | `LiquityMath._decPow` / simple interest | v1's decay constants sit within 4e-16 of their half-lives, about 4e-12 relative over a week; v2's README states simple, non-compounding interest. | Exact enough; documented. |
| C | crvUSD / LLAMMA | `AMM._rate_mul`, `_p_oracle_up` | 1 + integral(rate, dt) per update, as its docstring states; band prices about 1e-16. | Exact enough, and the licence ("all rights reserved") rules out transcription. |
| C | GMX v2 | `Precision.applyExponentFactor`, funding, borrowing | PRBMath v2.4.3 pow (about 1e-17), linear borrowing per second. | Exact enough; the funding's end-of-interval rate is a model choice. |
| C | Synthetix v3 perps | `PerpsMarket.unrecordedFunding` | The trapezoid of a linearly moving rate, exact for a constant velocity. | Exact. |
| C | Pendle v2 | `MarketMathCore` implied rate | Balancer's LogExpMath, already in the ladder; about 1e-13 relative an hour before expiry. | Exact enough. |
| C | Euler v2 EVK accrual | `RPow.rpow` in `Cache.initVaultCache` | Ray squaring, half up; about 1e-26. | Exact enough. |
| C | Ajna, Silo v2 | PRBMath v2 `exp` | About 1e-17. | Exact enough. |
| C | Ethena sUSDe, Yearn v3, Gearbox v3, Aave v4 (v0.5.x) | vesting, unlocking, linear growth, the Hub's linear index | Linear by design. | The shortcut is the model. |
| C | Spark SSR oracle | `getConversionRate*` | rpow, the Aave binomial or linear; about 1e-11 over a week. | Exact enough. |
| – | gTrade | borrowing fee per block | Not verified: no public source could be read. | |

## BL127Lib on BL19's table

BL19's table shows the same op in BL127Lib on the same value. These ops were missing from that column, though BL127 has them, and are now benched: `floor`, `ceil`, `toFixed18Down`, `toFixed18Up`, `mulDown`, `mulUp`, `divDown`, `divUp`, `powu` and `compound` (BL127 takes n << 128 where BL19 takes the plain integer), and `fromFixed18` (the raw WAD had been routed through `toBL127`).

The 12 cells still empty there are ops BL127 does not have: `cmp`, `lt`, `eq` (a 127.128 word compares as an int256), `fromUint`, `fromUintDown`, `fromUintUp`, `toUintDown`, `toUintUp`, `toIntDown`, `toIntUp`, `fromBL127`, `toBL127`.

## Not compared

One line per function or group, on why no FP op computes the same function.

- **Solady `fullMulDiv`, `fullMulDivUp`, `fullMulDivUnchecked`, `fullMulDivN`, `mulDiv`, `mulDivUp`, `fullMulEq`:** integer x·y/d (and x·y = a·b) with a free denominator. No op takes a denominator; the WAD case d = 1e18 is `mulWad`, which is compared.
- **Solady `rpow` with a base other than 1e18:** the 1e18 case is compared as `powu`. Other bases are other fixed-point formats.
- **Solady `invMod`, `gcd`, `isEven`, `divUp`:** integer number theory and integer ceil division; no fixed-point op.
- **Solady `saturatingAdd`, `saturatingMul`:** unsigned saturation; BL127's arithmetic reverts on overflow instead.
- **Solady `ternary`, `coalesce`:** selection helpers, no arithmetic.
- **Solady `sqrt`, `cbrt` (uint256):** floor roots of an integer. BL127's `sqrt` and `cbrt` are roots of a real; the fixed-point roots `sqrtWad` and `cbrtWad` are compared.
- **Solady `log2`, `log10`, `log10Up`, `log256`, `log256Up` (uint256):** integer floor and ceil logarithms. BL127's `log2` and `log10` are real-valued, and it has no floor log. Only `log2Up` has an BL127 equivalent, and it is compared.
- **Solady `sci`, `packSci`, `unpackSci`:** decimal mantissa and exponent packing; no op.
- **Solady unsigned `rawAdd`, `rawSub`, `rawMul`, `rawDiv`, `rawSDiv`, `rawMod`, `rawSMod`, `rawAddMod`, `rawMulMod`:** raw EVM opcodes on integers. The signed `rawAdd` and `rawSub` stand in for add and sub; a raw product is not a fixed-point product.
- **PRBMath `and`, `and2`, `or`, `xor`, `not`, `lshift`, `rshift`, `mod`:** bitwise and remainder operations on the raw word; no op.
- **PRBMath `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `isZero`:**
  - BL127 table: BL127 has no comparison ops, because a 127.128 word compares as an int256, exactly as an SD59x18 does.
  - BL19 table: BL19's `cmp`, `lt` and `eq` are not compared against PRBMath. That table compares only binary128, the other float, and BL127Lib. BL19's comparisons are measured against Quad's `cmp` and `eq` there.
- **PRBMath `convert(int256)`, `convert(SD59x18)`:** integer ↔ SD59x18, ×1e18 and ÷1e18 toward zero.
  - BL127 table: BL127 has no integer conversions (a shift does it).
  - BL19 table: not compared, for the same reason as the comparisons. BL19's `fromUint` and `toInt*` are compared against Quad there.
- **PRBMath casts (`intoInt256` … `wrap`):** type conversions with range checks, no arithmetic.
- **ABDK 64.64 `fromInt`, `toInt`, `fromUInt`, `toUInt`, `from128x128`, `to128x128`:** conversions into and out of 64.64 itself. BL127 has none of these (its integer conversions are shifts), and 64.64 is not on BL19's table.
- **ABDK 64.64 `muli`, `mulu`, `divi`, `divu`:** 64.64 × integer → integer, and integer ÷ integer → 64.64; no op mixes the two representations.
- **ABDKMathQuad `fromInt`:** signed integer → binary128. BL19 has only `fromUint` (and its Down/Up), and Quad's `fromUInt` is compared against `fromUintDown`.
- **ABDKMathQuad `from64x64`, `to64x64`, `fromOctuple`, `toOctuple`, `fromDouble`, `toDouble`:** conversions to formats no FP library has.
- **ABDKMathQuad `isNaN`, `isInfinity`:** BL127 and BL19 have no NaN or infinity; they revert instead.

## Ops no library offers

These are empty on every competitor column, and correctly so:

- Both tables: `exp10`, `hypot`, `round`, `compound`, `lambertWm1` (Solady has W₀ only), `log1p`, `expm1`, `sinh`, `cosh`, `tanh`, `atanh`, `erf`, `erfc`, `normCdf`.
- BL127 table: the conversions `fromFixed18`, `toFixed18`, `toFixed18Down`, `toFixed18Up`. A WAD library is natively 18-decimal.
- BL19 table, Quad column: all of the above (the fixed-18 conversions included), plus `lambertW0`, `cbrt`, `log10`, `log2Up`, `gavg`, `avg`, `min`, `max`, `clamp`, `dist`, `zeroFloorSub`, `lerp`, `floor`, `ceil`, `frac`, `factorial`, the directed `mulDown`, `mulUp`, `divDown`, `divUp`, `powu`, `fromUint`, `fromUintUp`, `toUintUp`, `toIntUp`.

## Precision comparisons

- The precision table on the site (`precisiontable`, from `docs/bl127/precision.json`) is BL127's alone; no other library appears in it.
- Competitor precision per op is in the edges dataset ([edges.md](edges.md), `make edges`): 15 ops, probed for every library. Its "n/a" cells were checked and are correct:
  - Aave, Morpho, Maker, FraxLend and Euler have no general functions.
  - OpenZeppelin and Uniswap FullMath have mul and div (and OpenZeppelin a root) only; PRBMath UD60x18 takes no negative argument, so its negative probes are `ParamOutOfRange`.
  - Only Solady has `lambertW0`, and no library has `lambertWm1`.
  - Libraries without `powu`, `log1p` or the like get them composed from their own primitives in `contracts/src/ladder/Ladder*.sol`. ABDK's `pow` and Solady's `rpow` are already used there as powu.

## Empty cells, before and after

| table | cells | empty before | empty after | rev |
|---|---:|---:|---:|---:|
| BL127 (site columns: Yul, BL127Lib and the five libraries) | 357 → 371 (`clamp`, `lerp` added) | 186 | 181 | 0 |
| BL19 (object, BL19Lib, BL127Lib, Quad) | 260 | 76 | 55 | 0 |

Issue #166 added five columns to BL127's table (53 ops each): Solmate 11 cells, OpenZeppelin 11, Uniswap FullMath 4, PRBMath UD60x18 18, snekmate 10. None is `rev`.

Before, an empty cell meant either not offered or reverted on every input. Now every empty cell is an op the library does not offer, and the bench enforces it.

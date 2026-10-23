# Comparison coverage

Every function of every comparison library, from the source in `lib/` and `contracts/src/ladder/vendor/`, mapped to the FP127 or FP256 op it computes, or listed as not compared with the reason. The gas harnesses are `test/fp127/GasLadder.t.sol` (`make bench` → [gas.md](gas.md), gas.json) and `test/fp256/GasLadder.t.sol` (`make bench-fp256` → [gas256.md](gas256.md), gas256.json). The exact call behind each cell is `CALLS` in `scripts/fp127/gas_to_json.py`, written to gas.json as `calls`. The bench fails if a measured cell has no `CALLS` entry, or an entry has no cell.

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

**Which table.** FP127's table compares the WAD libraries (Solady, PRBMath, Balancer), 64.64 and binary128. FP256's table compares binary128, the other float, and FP127Lib on the same value. The WAD and 64.64 libraries are not repeated on FP256's table: every op they share with FP256 is also an FP127 op, so it is compared there.

**Statuses.**
- compared: benched before this audit, on the same function.
- new: benched by this audit.
- fixed: was benched under the wrong op or was not the library's function.
- domain: benched on the part of the ladder inside the function's domain. The other inputs count as reverting (REV), never as not offered.
- variant: the same function as a benched one (an unchecked twin, an unsigned overload, an alias), not benched again.
- none: no FP op computes the same function; see "Not compared" below.

Conversions into each library's representation happen once, outside the timed window. They are: WAD = `FP127Lib.toFixed18`; 64.64 = `x >> 64` (REV where it does not fit int128); binary128 = `ABDKMathQuad.from128x128` on FP127's table, and on FP256's a direct repacking of the FP256 word (sign, rebiased exponent, fraction truncated to 112 bits).

## Solady FixedPointMathLib (78 functions, counting overloads)

| function | op | benched | status |
|---|---|---|---|
| `sMulWad(int256, int256)` | mul | yes | compared (rounds toward zero; FP127's `mul` floors) |
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
| `cbrtWad(uint256)` | cbrt | yes | compared, domain x ≥ 0 (as above; FP127's cbrt takes negatives) |
| `abs(int256)` | abs | yes | new |
| `avg(int256, int256)` | avg | yes | new (floors, as FP127's) |
| `dist(int256, int256)` | dist | yes | new |
| `min(int256, int256)` | min | yes | new |
| `max(int256, int256)` | max | yes | new |
| `clamp(int256, int256, int256)` | clamp | yes | new (clamp joined FP127's gas ladder in this audit) |
| `lerp(int256 a, b, t, begin, end)` | lerp | yes | new, domain t ∈ [0, 1]: called as `lerp(a, b, t, 0, 1e18)`; Solady clamps t to [begin, end], FP127 does not |
| `zeroFloorSub(uint256, uint256)` | zeroFloorSub | yes | new, domain a, b ≥ 0 |
| `mulSqrt(uint256, uint256)` | gavg | yes | new, domain a, b ≥ 0: sqrt(x y) of two WADs is the WAD geometric mean |
| `rpow(uint256 x, uint256 y, uint256 b)` | powu | yes | new, domain x ≥ 0, integer n ≥ 0: `rpow(x, n, 1e18)` |
| `factorial(uint256)` | factorial | yes | new, domain integral x: given the plain integer, returns the plain integer n! |
| `log2Up(uint256)` | log2Up | yes | new, domain integral x ≥ 1: ceil(log2 n) of the plain integer, which FP127's `log2Up` is on integers |
| `rawAdd(int256, int256)` | add | yes | fixed: the cell was Solidity's checked `a + b`, which is not a Solady function; it is now Solady's unchecked `rawAdd` |
| `rawSub(int256, int256)` | sub | yes | fixed, as `rawAdd` |
| `rawMulWad`, `rawSMulWad`, `rawMulWadUp`, `rawDivWad`, `rawSDivWad`, `rawDivWadUp` | mul, mulDown, … | no | variant: the unchecked twins of the six above |
| `avg`, `dist`, `min`, `max`, `clamp`, `lerp` (uint256 overloads) | | no | variant: FP127 is signed; the int256 overloads are benched |
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
| `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `isZero` | | no | none (FP127 table); not compared on the FP256 table |
| `convert(int256)`, `convert(SD59x18)` | | no | none (FP127 table); not compared on the FP256 table |
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
| (`div(fromUInt(1), x)`) | inv | yes, both tables | composed; new on FP256's table |
| (`exp(mul(y, ln(x)))`) | pow | yes, both tables | composed |
| `sign` | sign | yes, both tables | new |
| `cmp` | cmp (FP256); also `lt` as `cmp(a, b) < 0`, composed | yes, FP256 | new |
| `eq` | eq (FP256) | yes, FP256 | new |
| `toUInt` | toUintDown (FP256) | yes, FP256 | new: truncates, which is floor on the ladder's non-negative inputs |
| `toInt` | toIntDown (FP256) | yes, FP256 | new, domain x ≥ 0: truncation is floor only there |
| `fromUInt` | fromUintDown (FP256) | yes, FP256 | new: truncates the significand, which is FP256's `fromUintDown`, not its rounding `fromUint` |
| `from128x128` | fromFP127 (FP256) | yes, FP256 | new: truncates where FP256 rounds to nearest; on FP127's table it is the input conversion |
| `to128x128` | toFP127 (FP256) | yes, FP256 | new: truncates where FP256 rounds to nearest |
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

## Aave, Morpho, Maker

Their accrual maths (Aave `MathUtils`, Morpho `MathLib`, Maker `rpow`) is transcribed for the ladder only. No op table claims to cover them, and they are not on the gas tables.

## FP127Lib on FP256's table

FP256's table shows the same op in FP127Lib on the same value. These ops were missing from that column, though FP127 has them, and are now benched: `floor`, `ceil`, `toFixed18Down`, `toFixed18Up`, `mulDown`, `mulUp`, `divDown`, `divUp`, `powu` and `compound` (FP127 takes n << 128 where FP256 takes the plain integer), and `fromFixed18` (the raw WAD had been routed through `toFP127`).

The 12 cells still empty there are ops FP127 does not have: `cmp`, `lt`, `eq` (a 127.128 word compares as an int256), `fromUint`, `fromUintDown`, `fromUintUp`, `toUintDown`, `toUintUp`, `toIntDown`, `toIntUp`, `fromFP127`, `toFP127`.

## Not compared

One line per function or group, on why no FP op computes the same function.

- **Solady `fullMulDiv`, `fullMulDivUp`, `fullMulDivUnchecked`, `fullMulDivN`, `mulDiv`, `mulDivUp`, `fullMulEq`:** integer x·y/d (and x·y = a·b) with a free denominator. No op takes a denominator; the WAD case d = 1e18 is `mulWad`, which is compared.
- **Solady `rpow` with a base other than 1e18:** the 1e18 case is compared as `powu`. Other bases are other fixed-point formats.
- **Solady `invMod`, `gcd`, `isEven`, `divUp`:** integer number theory and integer ceil division; no fixed-point op.
- **Solady `saturatingAdd`, `saturatingMul`:** unsigned saturation; FP127's arithmetic reverts on overflow instead.
- **Solady `ternary`, `coalesce`:** selection helpers, no arithmetic.
- **Solady `sqrt`, `cbrt` (uint256):** floor roots of an integer. FP127's `sqrt` and `cbrt` are roots of a real; the fixed-point roots `sqrtWad` and `cbrtWad` are compared.
- **Solady `log2`, `log10`, `log10Up`, `log256`, `log256Up` (uint256):** integer floor and ceil logarithms. FP127's `log2` and `log10` are real-valued, and it has no floor log. Only `log2Up` has an FP127 equivalent, and it is compared.
- **Solady `sci`, `packSci`, `unpackSci`:** decimal mantissa and exponent packing; no op.
- **Solady unsigned `rawAdd`, `rawSub`, `rawMul`, `rawDiv`, `rawSDiv`, `rawMod`, `rawSMod`, `rawAddMod`, `rawMulMod`:** raw EVM opcodes on integers. The signed `rawAdd` and `rawSub` stand in for add and sub; a raw product is not a fixed-point product.
- **PRBMath `and`, `and2`, `or`, `xor`, `not`, `lshift`, `rshift`, `mod`:** bitwise and remainder operations on the raw word; no op.
- **PRBMath `eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `isZero`:**
  - FP127 table: FP127 has no comparison ops, because a 127.128 word compares as an int256, exactly as an SD59x18 does.
  - FP256 table: FP256's `cmp`, `lt` and `eq` are not compared against PRBMath. That table compares only binary128, the other float, and FP127Lib. FP256's comparisons are measured against Quad's `cmp` and `eq` there.
- **PRBMath `convert(int256)`, `convert(SD59x18)`:** integer ↔ SD59x18, ×1e18 and ÷1e18 toward zero.
  - FP127 table: FP127 has no integer conversions (a shift does it).
  - FP256 table: not compared, for the same reason as the comparisons. FP256's `fromUint` and `toInt*` are compared against Quad there.
- **PRBMath casts (`intoInt256` … `wrap`):** type conversions with range checks, no arithmetic.
- **ABDK 64.64 `fromInt`, `toInt`, `fromUInt`, `toUInt`, `from128x128`, `to128x128`:** conversions into and out of 64.64 itself. FP127 has none of these (its integer conversions are shifts), and 64.64 is not on FP256's table.
- **ABDK 64.64 `muli`, `mulu`, `divi`, `divu`:** 64.64 × integer → integer, and integer ÷ integer → 64.64; no op mixes the two representations.
- **ABDKMathQuad `fromInt`:** signed integer → binary128. FP256 has only `fromUint` (and its Down/Up), and Quad's `fromUInt` is compared against `fromUintDown`.
- **ABDKMathQuad `from64x64`, `to64x64`, `fromOctuple`, `toOctuple`, `fromDouble`, `toDouble`:** conversions to formats no FP library has.
- **ABDKMathQuad `isNaN`, `isInfinity`:** FP127 and FP256 have no NaN or infinity; they revert instead.

## Ops no library offers

These are empty on every competitor column, and correctly so:

- Both tables: `exp10`, `hypot`, `round`, `compound`, `lambertWm1` (Solady has W₀ only), `log1p`, `expm1`, `sinh`, `cosh`, `tanh`, `atanh`, `erf`, `erfc`, `normCdf`.
- FP127 table: the conversions `fromFixed18`, `toFixed18`, `toFixed18Down`, `toFixed18Up`. A WAD library is natively 18-decimal.
- FP256 table, Quad column: all of the above (the fixed-18 conversions included), plus `lambertW0`, `cbrt`, `log10`, `log2Up`, `gavg`, `avg`, `min`, `max`, `clamp`, `dist`, `zeroFloorSub`, `lerp`, `floor`, `ceil`, `frac`, `factorial`, the directed `mulDown`, `mulUp`, `divDown`, `divUp`, `powu`, `fromUint`, `fromUintUp`, `toUintUp`, `toIntUp`.

## Precision comparisons

- The precision table on the site (`precisiontable`, from `docs/fp127/precision.json`) is FP127's alone; no other library appears in it.
- Competitor precision per op is in the edges dataset ([edges.md](edges.md), `make edges`): 15 ops, probed for every library. Its "n/a" cells were checked and are correct:
  - Aave, Morpho and Maker have no general functions.
  - Only Solady has `lambertW0`, and no library has `lambertWm1`.
  - Libraries without `powu`, `log1p` or the like get them composed from their own primitives in `contracts/src/ladder/Ladder*.sol`. ABDK's `pow` and Solady's `rpow` are already used there as powu.

## Empty cells, before and after

| table | cells | empty before | empty after | rev |
|---|---:|---:|---:|---:|
| FP127 (site columns: Yul, FP127Lib and the five libraries) | 357 → 371 (`clamp`, `lerp` added) | 186 | 181 | 0 |
| FP256 (object, FP256Lib, FP127Lib, Quad) | 260 | 76 | 55 | 0 |

Before, an empty cell meant either not offered or reverted on every input. Now every empty cell is an op the library does not offer, and the bench enforces it.

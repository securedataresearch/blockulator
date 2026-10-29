# FP127 history: the Huff era

FP127 is signed 127.128 fixed point: one `int256` per value, `value = raw / 2^128`,
so `ONE = 2^128`, range about ±1.7e38, 128 fractional bits, about 38 decimal
digits. It began as a pure-Huff contract, deployed to Sepolia at
`0xfae694D0c2c44181791F838c54Ed64C3151FfE30`. The runtime bytecode fetched from
that address at block 11,857,616 is the baseline the current test suites compare
against. In October 2026 the contract was ported to a single Yul source
(PRs #36, #37, #38 and #40 in SamReeves/blockulator). The Huff sources now live
under `contracts/archive/huff/`.

This file folds seven Huff-era documents into one record: the old README, the
deployment summary, the "final analysis", two gas-optimization write-ups, an
"improvements" log and an "optimization complete" summary. All seven entered
the repository on 2026-03-05 and were last touched on 2026-03-17. Every number
below that is attributed to them is a measurement or an estimate from March 2026
against code that has since changed. Current figures live in
`docs/fp127/precision.md` and `docs/benchmarks/gas.md`. Where the seven
documents disagree with each other or with the archived source, this file says
so rather than picking one.

## The Huff design

**Representation.** Two's complement `int256`, 128 integer bits, 128 fractional
bits. The old docs called it "127.128" in most places and "128.128" in the Huff
source README; both mean the same word layout, with the sign bit taken out of
the integer field in the first spelling. No tagged special values: the
deployment summary lists "+Inf, -Inf, NaN, -0 (IEEE 754-like)" as a feature,
but the improvements log lists "no special values" as a known issue and
proposes them as future work, and the archived source has none. The
deployment summary is wrong on this point.

**Op set.** The contract grew from four ops (add, sub, mul, div, the state the
deployment summary describes) to the 34 the site registry lists: add, sub,
mul, div, exp, exp2, exp10, ln, log2, log10, sqrt, pow, abs, neg, inv, min,
max, clamp, avg, gavg, dist, zeroFloorSub, hypot, cbrt, lerp, sign, floor,
ceil, frac, round, log2Up, gcd, factorial, lambertW0. Every op was exposed
twice: a fixed18 form that converted its `uint256` arguments through
`fromFixed18`, computed, and converted back through `toFixed18`, and a `Raw`
form that took and returned 127.128 words directly. With `fromFixed18`,
`toFixed18` and `divUnsignedRaw` that made 71 selectors. The ABI typed
everything as `uint256`; the Solidity interface is kept at
`contracts/archive/huff/src/fp127/Ifp127.sol`.

**Dispatcher and macros.** `fp127.huff` is the entry point. Its `MAIN()` macro
loads the selector, runs a linear chain of `dup1 __FUNC_SIG(name) eq label
jumpi` checks over all 71 selectors, and reverts with no data on a miss. Each
landing pad reads calldata, calls the op, `mstore`s the result at `0x00` and
returns 32 bytes. The ops themselves are Huff `fn`s and `macro`s split across
`constants.huff`, `primitives.huff` (sign test, negate, MSB binary search,
Newton sqrt step), `arithmetic.huff` (mul, div, conversions), `log2.huff`,
`exp.huff`, `ln.huff`, `sqrt.huff`, `pow.huff`, `utils.huff`,
`transcendental_utils.huff` and `lambertw0.huff`. Several helpers carry a
comment of the form "converted to function to save N bytes (M call sites)",
which records the pressure that eventually ran `huffc` out of room: the
source README later recorded that the combined expanded source hit the
compiler's internal limit (`byte index 115922 is out of bounds`) once
`lambertwm1.huff` was included. `test_fp127.huff` was a separate deployable
harness with the same selectors.

**mul.** Four-term schoolbook decomposition on the signed halves:
`a_hi * b_hi << 128 + a_hi * b_lo + a_lo * b_hi + (a_lo * b_lo) >> 128`, with
`sar` for the high halves and a 128-bit mask for the low halves. The result is
the middle 256 bits of the exact product, so it floors. The two gas write-ups
describe two different layouts of this macro (see the next section); the
archived source matches neither exactly. It pushes `MASK128` once and cleans
up with `swap3 pop pop pop`.

**div.** The old README, the final analysis and the improvements log all
describe division as a two-step 64-bit "shift and divide" with about 62 bits
of fractional precision, and the improvements log records a four-step 32-bit
variant that reached only about 93 bits and was reverted. The archived source
does something else: `FP127_DIV_UNSIGNED` is a full Remco Bloemen `mulDiv`
with the multiplier fixed at `2^128` (512-bit product, remainder subtraction
via `mulmod`, factor out powers of two, Newton-Raphson modular inverse), and
`FP127_DIV` wraps it with sign stripping and re-signing, so it truncates. The
source header says "Precision: Full 128 fractional bits (exact for all
inputs)". The docs were written against the earlier chunked version and never
updated. The equivalence suites confirm the Sepolia bytecode is the full
`mulDiv`.

**exp, ln, log2, sqrt.** The Huff source README describes a "binary
digit-by-digit table method" using `tables.huff` with 135 precomputed
`e^(2^(k-128))` entries per function, and `sqrt` as `exp(ln(x) / 2)`. No
`tables.huff` exists in the archive and the sources do not match that
description. What shipped: `exp2` splits x into integer and fraction, runs a
degree-22 minimax polynomial by Horner on the fraction, and shifts by the
integer part; `exp` is `exp2(x * 1/ln 2)`. `log2` finds the MSB, normalises
into [1, 2), range-reduces through seven stages with precomputed `2^(1/2^k)`
thresholds, and evaluates a degree-17 polynomial for `ln(1+f)/f`; `ln` and
`log10` are `log2` scaled. `sqrt` is an MSB-derived initial guess followed by
seven Newton steps, each one calling `FP127_DIV_UNSIGNED`. The source README
is stale on all of this; its gas figures ("exp ~21k, ln ~41k, sqrt ~63k") are
from the table version and are an order of magnitude above what the shipped
code costs.

**Lambert W0.** `lambertw0.huff` seeds from a 64-entry table of W(1)..W(64)
with linear interpolation. The table is written into memory at `0x200`
onwards on every call, 64 `mstore`s, before the lookup. The source says this
gives 16 to 20 bits for 1 ≤ x < 64, interpolates between W(0) and W(1) below
1, and reuses W(64) as the seed above 64. The seed is then refined by two
Fritsch-Shafer-Crowley steps, documented as quartic ("bits quadruple each
step"), and one Iacono-Boyd finisher, documented as cancellation-free. The
file also defines a Newton-Raphson step that the shipped path does not use.
Header estimate: 12,000 to 14,000 gas and 128 fractional bits for x ≤ 64.
Neither claim held up; see "What the port found".

**factorial.** A jump table of 34 constants for 0! through 33!, selected by a
chain of 34 `eq jumpi` checks on the floored integer part.

**Shortcut constants.** `shortcut_constants.huff` is generated by
`scripts/fp127/generators/generate_shortcuts.py` and holds 98 constants: a
set of input values (small integers, 1/4, 1/8, e, -1, and so on) and the
precomputed function results for them (ln, log10, pow, cbrt, W). `pow`,
`cbrt` (in `transcendental_utils.huff`) and `lambertW0` check their inputs
against these first and return the stored value without iterating. The
Sepolia bytecode predates this file; see below.

**Sentinels instead of reverts.** The only revert in the contract is the
dispatcher's unknown-selector path. Every domain or range problem inside an
op returned a value: `exp` and `exp2` above their thresholds and `factorial`
above 33 returned `MAX_UINT256`; `exp` and `exp2` below their thresholds,
`log2` (and so `ln`, `log10`) at or below zero, `pow(0, y)` and `lambertW0`
below -1/e returned 0; `add`, `sub` and `mul` wrapped; `fromFixed18` lost its
top bit above 2^127. The improvements log records the wrapping as "EVM
default behavior" and lists checked arithmetic as optional future work. The
docs give no reason for the sentinel design beyond gas.

## Gas work on the Huff

Three rounds are documented. All numbers here are from March 2026 and
describe versions of `FP127_MUL` that are not the one in the archive.

**Round 1: fix and tidy (optimization-complete log).** A refactor that
replaced `[FRAC_BITS]` with the literal `0x80` shifted the stack by one and
broke every `dup` index in `mul`, so `1 * 1 = 0`. The fix restored the
indices, replaced six `swap1 pop` pairs with `swap6` and six `pop`s, deleted a
duplicate `fp127_optimized.huff`, and switched `fromFixed18` from
`[ONE] mul` to `0x80 shl`. A mulmod-based unsigned multiply was prototyped
and dropped because sign handling cost more than the ~25% it saved.

| op (March 2026, core macro estimate) | before | after |
|---|---:|---:|
| mul, signed | broken | ~200 |
| mul, unsigned prototype | n/a | ~150 |
| div | ~500 | ~450 |
| fixed18 conversions | ~120 | ~100 |

**Round 2: inline extraction (gas-optimizations and optimization-summary
docs).** Instead of extracting `a_hi`, `a_lo`, `b_hi`, `b_lo` up front and
carrying six stack items, each of the four terms extracts its own operands,
so the stack never exceeds five items and cleanup drops from `swap6` plus six
`pop`s to `swap2` plus two. The cost was pushing `MASK128` four times instead
of two.

| metric (March 2026) | before | after | note |
|---|---:|---:|---|
| core opcodes | ~132 gas | ~67 gas | doc's own count |
| core with overhead | ~200 gas | ~140 gas | estimate |
| Foundry, through a call | 1,027 gas | ~750 gas | after figure is a projection, marked with an asterisk in the source doc |
| stack cleanup | 15 gas | 7 gas | |
| extra PUSH16 | 0 | +6 gas | |

The ~750 figure was never measured. `docs/benchmarks/gas.md` (generated
2026-10-06) reports the Sepolia bytecode at 997 / 999 / 1,001 gas for `mul`
through a `staticcall`, in line with the 1,027 the earlier docs measured, not
the projection.

**Round 3: Foundry benchmarks against ABDK and Solady (README and final
analysis).** These are the headline numbers the old README carried.

| library (March 2026, Foundry) | mul gas | div gas | claimed precision |
|---|---:|---:|---|
| FP127 | 1,027 | 518 | 128 bits mul, "~62 bits" div |
| ABDKMath64x64 | 341 | 342 | 64 bits |
| Solady WAD | 611 | 611 | 60 bits |

The 518-gas division figure belongs to the chunked version. The `mulDiv` that
actually shipped measures 1,363 / 1,365 / 1,367 through a `staticcall` in the
October 2026 ladder, so the "division is 15% cheaper than Solady" claim in the
old README did not survive the switch to full precision.

**Precision claims in the gas docs.** The write-ups quote three different
multiplication test runs and the numbers do not agree, because the test sets
differ (65 cases in one, 551 in another) and because one run predates the
`dup` index fix.

| source doc (March 2026) | tests | bit-exact | min precision | avg precision |
|---|---:|---:|---:|---:|
| README, final analysis, optimization summary | 65 | 40% | 102.7 bits | 123.4 bits |
| gas optimizations (same 65, "identical precision") | 65 | 25% | 78.9 bits | 123.4 bits |
| improvements, optimization complete | 551 | 87% | 118.0 bits | 127.8 bits |

For division the improvements log reports 62.0 bits average over 449 tests in
one section and "88.4 bits avg" from a separate benchmark script in another,
without reconciling them. Both describe the chunked version.

What was learned, in the docs' own terms: the schoolbook `mul` was good
enough and the mulmod trick was not worth the sign handling; stack discipline
matters more than opcode count in Huff; `pyrevm` does not report gas, so the
Python harness could validate precision but not cost, and gas had to come
from Foundry; and a chunked division is a false economy once precision is the
point of the library. The final analysis also proposed an EIP-5000 `MULDIV`
opcode, a hybrid wrapper that would pick Solady or FP127 by precision need,
and IEEE-style rounding modes. None of those were pursued.

## Deployment of the Huff

**Build.** `contracts/deployments/compile-huff.sh` (now
`contracts/archive/huff/compile-huff.sh`) ran `huffc file -b` for creation
bytecode and `huffc file -r` for runtime bytecode into `contracts/build/huff/`,
wrote `contracts/build/bytecode/fp127.json`, and emitted a hand-maintained ABI
to `contracts/build/abis/fixedpoint127.json` with every function typed
`uint256` and `pure`. The Huff source README gives the manual invocation as
`huffc --evm-version paris ... -r`. The compiler was `huffc` 0.3.x from
`huff-rs`.

**Deploy.** `contracts/deployments/deploy-and-update.sh` compiled, checked the
runtime size against the 24,576-byte limit, ran
`contracts/deployments/deploy-fixedpoint127.js`, and `sed`-patched the
resulting address into the site's contract registry. The deploy script used
ethers v5: `JsonRpcProvider` against `https://ethereum-sepolia-rpc.publicnode.com`
by default, a wallet from `PRIVATE_KEY`, and `ContractFactory.deploy()` with
no constructor arguments, which is a plain `CREATE` from the deployer's nonce.
It then called `mulRaw(2 << 128, 3 << 128)` and checked for `6 << 128`, and
wrote `contracts/deployments/active/fixedpoint127-deployment.json`. All three
files were removed in the deploy-and-retire PR; the CREATE2 record that
replaces them is `contracts/deployments/FP127.md`.

**Addresses.** The deployment summary records the first deployment on
2026-03-05 at `0x1A4073C46bC9bC01994c2Fa7dd9DaD76092DBAA2`, transaction
`0x79765e7c...a04c2d`, with four operations. That contract is not the
baseline. The registry moved to `0xfae694D0c2c44181791F838c54Ed64C3151FfE30`
in the "polish" commit of 2026-03-18 (the deleted `deploy-config.json` carried
a timestamp of `2026-03-18T02:34:00Z`), and no document in the set was updated
to say so. The 34-op bytecode at the second address, fetched at block
11,857,616, is what `fp127.sepolia.runtime.hex` holds.

**What the site called it.** The registry key was `fixedpoint127`, display
name `FP127`, category `huff`, description "Signed 127.128 fixed-point
arithmetic with 34 operations", route `/#/fp127`. The deployment summary
describes the calculator page as titled "FixedPoint127" with the subtitle
"Huff Assembly, 127.128 Fixed-Point", and that same document records the
rename of the docs from `FP127_*` to `FIXEDPOINT127_*`. The code, the ABI
file and the registry kept both names side by side from then on.

## What the port found

The authoritative list is the "What changed from the Huff" section of
`contracts/src/fp127/README.md`; this is the short version.

- `div` was already a full-precision Bloemen `mulDiv` with a `2^128`
  multiplier. The README's "~62-bit two-step chunking" and the 518-gas figure
  described an earlier version. The Yul ports it verbatim and adds the two
  missing guards.
- The Lambert W0 FSC step does not quadruple correct bits in this arithmetic;
  measured, it roughly doubles them (7, 14, 29, 58, 117). Two steps from a 16
  to 20 bit seed therefore gave 50 to 100 bits on (0, 64), under 40 bits near
  zero, read past the table above 64, and ran out of gas below zero. The Yul
  reseeds analytically, runs four FSC steps and one IB step, and drops the
  64-entry table, which is where most of the bytecode saving came from.
- The Huff returned sentinels where the Yul reverts: 0 and `MAX_UINT256` as
  listed above, plus division by zero, which returned `(|a| >> 128) * 128`
  (observed live: `divRaw(2.0, 0) == 256`). Every old answer is recorded in a
  `test_divergence_*` case.
- `gcd` extracted integer parts with a logical shift and then tested the sign
  bit of the shifted word, so negative inputs were wrong.
- `lambertwm1.huff` never shipped and never worked. The old README says it was
  archived "due to huffc size limit"; that was the trigger, but the routine
  also referenced an undefined constant, had its domain checks inverted,
  seeded with the wrong sign and called the step macro with the wrong stack
  convention. The Yul `lambertWm1` is a fresh implementation.
- The Sepolia bytecode predates `shortcut_constants.huff`. Its W(2) is the
  iterated value, 3 ULP off the table, so the equivalence suite compares the
  shortcut paths of `pow`, `cbrt` and `lambertW0` within a tolerance rather
  than to the bit, and a `huffc` rebuild of the archived sources does not
  reproduce the live bytecode.

## Where things are now

- `contracts/src/fp127/FP127.yul.src`: the hand-written source. `FP127.yul`,
  `FP127Lib.sol`, `IFP127.sol` and `abi.json` are generated from it by
  `make gen`; `make gen-check` fails CI if they are stale.
- `contracts/src/fp127/README.md`: representation, ABI, revert rules, and the
  full "What changed from the Huff" and "Legacy baseline" sections.
- `docs/fp127/precision.md` and `precision.json`: current per-op precision
  against the mpmath oracle, regenerated by `make test` and
  `make precision-report`.
- `docs/benchmarks/gas.md` and `gas.json`: the current gas ladder, with the
  Sepolia Huff bytecode as a column beside the Yul object, `FP127Caller`,
  `FP127Lib`, ABDK, Solady and PRBMath.
- `contracts/archive/huff/README.md`: the archived Huff sources, the baseline
  hex and its keccak, and how to rebuild with `huffc` if you must.
- `contracts/deployments/FP127.md`: the CREATE2 deployment record for the Yul
  object, written in the same PR that retired the files this history replaces.

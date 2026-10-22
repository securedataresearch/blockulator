# FP127 in Yul

Signed 127.128 fixed-point arithmetic for the EVM. One `int256` per value,
`value = raw / 2^128`, so `ONE = 2^128`. Range about ±1.7e38, 128 fractional
bits on an absolute grid of 2^-128: 38 digits at 1, 32 at 10^-6, 8 at
10^-30.

This directory holds **one hand-written file** and five generated ones.

| file | role |
|---|---|
| `FP127.yul.src` | the source of truth: Yul function bodies only |
| `FP127.yul` | generated: deployable object with a selector dispatcher |
| `FP127Lib.sol` | generated: Solidity library, one `assembly` block per op |
| `IFP127.sol` | generated: interface and custom errors of the deployed object |
| `abi.json` | generated: ABI of the deployed object |
| `ops.json` | generated: op table (signature, selector, domain, reverts) for the site |
| `FP127Caller.sol` | hand-written: thin `staticcall` harness around a deployed object |

```
make gen              # regenerate the five outputs
make gen-check        # fail if they are stale (CI runs this)
make vectors          # regenerate the mpmath vectors in test/fp127/vectors/
make vectors-check    # fail if they are stale (CI runs this)
make test             # gen-check + vectors-check + equivalence, behaviour, precision
make precision-report # docs/fp127/precision.md from the last test run
make bench            # gas ladder for every op and form -> docs/benchmarks/
make size             # deployed runtime size against the 24,576-byte limit
```

## Two forms, one source

The same Yul function bodies are emitted twice.

**Deployed object.** `FP127.yul` wraps the bodies in a dispatcher that
finds the 4-byte selector by binary search. It is deployed with CREATE2
through the deterministic proxy at
`0x4e59b44847b379578588920cA78FbF26c0B4956C`; the salt names the version.
This source is v5 (salt `"FP127 v5"`, 55 ops, 19,863 bytes of runtime),
live on Sepolia at `0x619176d72D7a12390F8970802943D344c0fd3fE2` since
2026-10-21 (Blockulator 2.1); `make predict` recomputes that address from
the artifact. v1 to v4 stay deployed. Record and verification recipe in
[`contracts/deployments/FP127.md`](../../deployments/FP127.md).
Every contract that `staticcall`s it runs identical bytecode.
`FP127Caller.sol` is the minimal Solidity wrapper for that path; it bubbles
revert data unchanged.

**Inline library.** `FP127Lib.sol` puts each body, plus the transitive
closure of helpers it calls, inside a `("memory-safe")` assembly block. No
external call, no shared address, cheapest per op. This is the form Austin
Griffith and Hadrien Croubois suggested.

`test/fp127/Equivalence.t.sol` and `EquivalenceOps.t.sol` fuzz the two
across the full `int256` domain for identical results, including which
inputs revert and with what data, and check both against the Huff bytecode
live on Sepolia wherever the Huff computed a defined answer: bit for bit on
the arithmetic, within 2^-100 relative on the transcendentals, which now
round where the Huff floored. `Behaviour.t.sol`
holds the known values, identities and shortcut-dispatch checks a reader
can verify by hand; `Precision.t.sol` holds the oracle comparison.

## Rules the source must obey

The generator (`scripts/fp127/gen.py`) rejects a source that breaks any of
these, because the inline-assembly dialect is a strict subset of Yul and
because a library must not trample its caller's memory or shadow its own
members.

1. Top level holds only comments and `function` definitions.
2. No `object`, `code`, `datacopy`, `dataoffset`, `datasize`, `codecopy`,
   `calldataload`, `calldatasize`, `return(`, `pc()`, `jump`, storage ops,
   external calls, or logs. The dispatcher and the library wrapper own
   calldata and returndata.
3. The only literal memory addresses are `0x00` and `0x20` (Solidity scratch
   space). Anything else must be `mload(0x40)`-relative.
4. Yul identifiers never start with `_`. The library wrapper names its
   Solidity parameters `_a`, `_b`, `_r` so nothing can shadow.
5. No Yul identifier may equal an export's Solidity name, since every
   assembly block shares scope with the library's members.
6. No recursion.
7. Exported functions carry `/// @export name(type a, ...) returns (type r)`.
   Parameter names in the annotation must match the Yul parameters. Helpers
   have no annotation and are not dispatched.
8. Reverts go through `rev(sel)` with a selector declared by
   `/// @error Name() 0xselector`. The generator checks every selector
   against keccak and every `rev(...)` literal against the declared list.

## ABI

Native 127.128 only. There is no `Raw` suffix and no 18-decimal flavour of
each op; `fromFixed18` and `toFixed18` are the bridge. All parameters are
`int256`. Errors are `Overflow()`, `DivisionByZero()`, `OutOfRange()`.

| op | semantics | reverts |
|---|---|---|
| `add`, `sub` | exact | `Overflow` |
| `mul(a, b)`, `mulDown(a, b)` | floor(a·b / 2^128) | `Overflow` |
| `mulUp(a, b)` | ceil(a·b / 2^128) | `Overflow` |
| `div(a, b)` | trunc(a·2^128 / b) | `DivisionByZero`, `Overflow` |
| `divDown(a, b)`, `divUp(a, b)` | floor, ceil of a·2^128 / b | `DivisionByZero`, `Overflow` |
| `fromFixed18(x)` | trunc(x·2^128 / 10^18) | `OutOfRange` if \|x\| ≥ 2^127 |
| `toFixed18(x)`, `toFixed18Down(x)` | floor(x·10^18 / 2^128) | never |
| `toFixed18Up(x)` | ceil(x·10^18 / 2^128) | never |
| `exp(x)` | e^x; 0 below −90 (under half an ULP from −89.42) | `Overflow` above 88 |
| `exp2(x)` | 2^x; 0 below −129 | `Overflow` at or above 127 |
| `exp10(x)` | 10^x; 0 below 2^-129 | `Overflow` from 2^127 (x ≈ 38.23) |
| `ln`, `log2`, `log10` | x > 0 | `OutOfRange` |
| `log2Up(x)` | ceil(log2 x): msb − 128, plus one unless a power of two | `OutOfRange` |
| `sqrt(x)` | floor, x ≥ 0 | `OutOfRange` |
| `cbrt(x)` | all x, odd; exact for perfect cubes | `Overflow` only at −2^255 |
| `pow(x, y)` | x^y for x ≥ 0; 0^0 = 1; shortcuts y = 1, y = 2 (the rounded square), x = 2, x = 10 | `OutOfRange` for x < 0, `Overflow` |
| `powu(x, n)` | x^floor(n) for any integer n, binary exponentiation on a 256-bit mantissa, a 512-bit one where that is ambiguous, one rounding; exact when representable | `Overflow`, `DivisionByZero` for 0^negative |
| `compound(r, n)` | (1 + r)^floor(n) through `powu` | `Overflow`, `DivisionByZero` |
| `inv(x)` | 1/x | `DivisionByZero`, `Overflow` |
| `abs`, `neg` | | `Overflow` at −2^255 |
| `sign`, `min`, `max`, `clamp`, `avg`, `floor`, `frac` | exact, never revert | |
| `ceil`, `round` | exact | `Overflow` at the top of the range |
| `zeroFloorSub`, `dist`, `lerp`, `hypot`, `gavg` | checked compositions | `Overflow`, `OutOfRange` |
| `gcd(a, b)` | gcd of \|floor a\|, \|floor b\| | never |
| `factorial(n)` | floor(n)! for 0 ≤ n < 34 | `OutOfRange` |
| `lambertW0(x)` | W(x) for x ≥ −1/e | `OutOfRange` |
| `lambertWm1(x)` | W₋₁(x) for −1/e ≤ x < 0 | `OutOfRange` |
| `pi(terms)` | Ramanujan's 1914 series, floor(terms) terms, 1 ≤ terms ≤ 7; five terms give 36 digits, 230 ULP from π, and more add nothing | `OutOfRange` |
| `log1p(x)` | ln(1 + x), the sum exact in the format | `OutOfRange` at or below −1, `Overflow` |
| `expm1(x)` | e^x − 1, the one subtracted before rounding; −1 below −90 | `Overflow` above 88 |
| `sinh`, `cosh` | \|x\| ≤ 88; below 1 the odd series (sinh) and the even series (cosh, within 3 units of 2^-192) at 2^-192; cosh is exactly 1 below 2^-64 | `Overflow` |
| `tanh(x)` | all x; ±1 exactly from \|x\| = 46 | never |
| `atanh(x)` | \|x\| < 1, both logs unrounded at 2^-192 | `OutOfRange` |
| `erf(x)`, `erfc(x)` | all x; series to 4, continued fraction beyond, at 2^-192; erfc(9.3) is one ULP, zero beyond | never |
| `normCdf(x)` | Φ(x) = erfc(−x/√2)/2, the N(d) of Black-Scholes; Φ(−13) is two ULPs, Φ(−14) is zero, Φ(14) is one | never |

**Rounding (v5).** Every transcendental returns the nearest word, ties up:
`exp`, `exp2`, `exp10`, `expm1`, `sinh`, `cosh`, `tanh`, `pow`, `cbrt`,
`ln`, `log2`, `log10`, `log1p`, `powu`, `compound`, `lambertW0`,
`lambertWm1`, and, through the one-word kernel, `atanh`, `erf`, `erfc` and
`normCdf` (no misrounding at any vector or random input). `add`, `sub`,
`log2Up` and the integer ops are exact. `mul`, `mulDown`, `divDown`,
`sqrt`, `toFixed18`, `toFixed18Down` floor; `mulUp`, `divUp`, `toFixed18Up`
ceil; `div`, `inv`, `fromFixed18` truncate. The exception is `pow` with an
extreme exponent: its error is below 2^-299 (1 + |y|) relative before the
rounding, so it is the nearest word while |y| x^y < 2^140 or so and
faithful to |y| x^y < 2^170; a base within 2^-88 of one raised past 2^90
(results near 2^120) misses by up to 1e11 ULPs. `gavg` and `hypot` are the
v4 compositions (floored root of a floored product or sum), kept
bit-identical to the Huff: within one ULP when the product is 1 or more,
but a small product's 2^-128 is amplified by the root.

**At the token edge.** The replays
([`docs/benchmarks/replay-*.md`](../../../docs/benchmarks/)) put every loss
where a protocol leaves the fixed point for integer token units. Round
toward the protocol there: `mulUp`/`divUp`/`toFixed18Up` for what it
charges or takes in, `mulDown`/`divDown`/`toFixed18Down` for what it pays
out, `floor` and `ceil` for whole units. `div` truncates toward zero, so a
negative quotient rounds up; `divDown` does not.

**The v5 kernels.** An exponential is split exactly into 2^n 2^f with f a
512-bit fraction (`y2nf`: the exponent y·log2(b), log2(b) to 2^-384, formed
as one 768-bit product), and e^(f ln 2) − 1 is evaluated by `expk` to about
2^-300 relative: the top 16 bits of the argument pick up to eight
double-word factors e^(v·4^-k) from a 24-entry table, the rest goes to
u + u²/2 in the double word and a one-word tail. The result is formed at
2^-192 in two words and rounded once. `l2p` refines the one-word log2 by one
Newton step through `expk` (2^-299 absolute); `pow` and `cbrt` use it.
`ln`, `log2` and `log10` round the one-word kernel when its 2^-145 error
bound cannot change the answer and fall back to `l2p` within 2^-145 of a
midpoint (about one input in 2^17). Lambert W ends with one Newton step
whose residual comes from the double-word exponential, and near −1/e it
seeds from 1 + e·x to 2^-254. `scripts/fp127/generators/precise_model.py`
models the kernels in integers and measures them.

Rounding directions of the arithmetic are inherited from the Huff and
preserved exactly: `mul` floors because it is the middle 256 bits of the
exact 512-bit two's complement product; `div` truncates because it strips
signs, divides, and re-signs. The transcendentals do not floor any more
(v2, 2026-10-07): `exp2`, `exp`, `exp10`, `log2`, `ln` and `log10` run
their kernels at 2^-192, 64 guard bits below the format, floor every
product there (`mulg`), and round to nearest once at the end (`round64`).
`ln` and `log10` scale the unrounded 192-bit `log2`, `exp` and `exp10` form
their argument at 2^-192, and a large `exp2` result keeps the guard bits as
result bits, so in v2 to v4 `ln`, `log2` and `log10` were within two ULP
(1.31 and 1.88 at worst for `ln` and `log2` on 4,000 random inputs each) and
the exponentials within one ULP below 2^16 and 2^-146 relative above; v5
replaced the exponentials' kernel and added the logs' fallback (above). The ladder's `exp(ln(x))` round trip,
which drifted 8 ULPs per step under floor, now returns the same word on
every step. The polynomials (degree 24 for 2^f, degree 14 for
log2(1+f)/f) are Chebyshev fits with error below 2^-145, from
`scripts/fp127/generators/guard_model.py`, which also models the kernels
in exact integer arithmetic and measures them.

Version 4 (2026-10-15) adds eleven ops and moves `pow`'s exponent product
to 2^-192 as well: `log2(x)` is taken unrounded and multiplied by `y` at
the guard scale, so `(1 + r)^n` with a per-second `r` keeps the bits that
a 128-bit product lost. `powu` and `compound` do not use the exponential
at all: |x| is written as a 256-bit mantissa with a binary exponent,
squared and multiplied keeping the top 256 bits of every 512-bit product,
and the word is formed once at the end, so an integer power was within one
ULP for results below 2^104 (231 bits above; v5 adds the 512-bit decider and
is the nearest word throughout) and exact whenever the value is representable, where
Maker's `rpow` and PRBMath's `powu` floor on every squaring. `expm1`,
`sinh`, `tanh` and `atanh` subtract before they round (series at 2^-192
near zero, the kernels above), so a result near zero keeps its relative
precision; `log1p` is `ln` of an exact sum. `erf` uses the all-positive
series (2/√π) e^(−x²) x Σ (2x²)^k/(2k+1)!! to x = 4 and the continued
fraction e^(−x²)/(√π K) beyond, both at 2^-192 with e^(−x²) unrounded, so
the tail keeps its digits down to the format's floor; `normCdf` is
erfc(−x/√2)/2. The term counts, the regime split and the fraction depth
1700/⌊x²⌋ + 10 come from `scripts/fp127/generators/erf_model.py`.

## Precision

`make test` runs every op over the committed mpmath vectors in
`test/fp127/vectors/` (generated by `scripts/fp127/oracle.py`, which uses
exact integer arithmetic for the integer ops and mpmath at 200 digits for
the rest, with the same rounding and domain as the Yul). Each vector carries
the real truth, and `Precision.t.sol` holds every op to its rounding
contract against it, measured to 2^-64 ULP: exact ops 0, directed ops under
one ULP, nearest ops at most half; v4's test allowed 2 ULP from a floored
reference. It writes [`docs/fp127/precision.json`](../../../docs/fp127/precision.json);
`make precision-report` renders [`docs/fp127/precision.md`](../../../docs/fp127/precision.md).
On 15,124 vectors every nearest op is the nearest word; `pi` is within 230
ULP of its own partial sum (the floored terms are scaled by 1103 + 26390 k).
`make sweep` measures 4,000 seeded random inputs per op
([`docs/benchmarks/sweep.md`](../../../docs/benchmarks/sweep.md)): every
v5 transcendental within half an ULP, where v4 had `exp` at 4e32, `pow` at
4.8e34, `cbrt` at 1.6e14, `compound` at 1.3e6, Lambert W at 1,153 and `ln`,
`log2` at 1.31 and 1.88 ULPs.

## Gas

`make bench` runs `test/fp127/GasLadder.t.sol` over an input ladder per op
and writes [`docs/benchmarks/gas.json`](../../../docs/benchmarks/gas.json)
and [`docs/benchmarks/gas.md`](../../../docs/benchmarks/gas.md), with the
Huff baseline, the Yul object, `FP127Caller`, `FP127Lib`, and ABDK, Solady
and PRBMath side by side. Through a `staticcall` the Yul object costs 700
to 800 gas more than the Huff on `add` and `mul` and less on `ln`, `log2`,
`pow` and `cbrt`; the inline library removes the call overhead.
Lambert W is the one op that got dearer, buying the nearest word where the
Huff had 50 to 100 bits: a median of 41k gas for `lambertW0` and 32k for
`lambertWm1` through the object in v5. Of the version 4 ops, `powu` and
`compound` cost 2,200 to 10,500 gas (one squaring step per bit of the
exponent), the near-one and hyperbolic ops 4,000 to 11,500, and the error
function family is the honest expensive one: 1,100 to 39,000 gas depending
on where x falls, the continued fraction near x = 4 being the dearest.

v5 against v4, medians through the object: `exp` 7,076 (+1,544), `exp10`
5,794 (+908), `exp2` 4,664 (−696), `pow` 5,742 (−352), `cbrt` 7,270 (+551),
`cosh` 9,372 (+155), `atanh` 7,646 (−1,055), `log1p` 4,397 (−317),
`lambertW0` 41,481 (+5,242), `lambertWm1` 31,764 (+2,402). Six more selectors
put about 90 gas on most other ops' dispatch. The directed ops cost 900 to
2,600 through the object, 950 to 1,530 inline.

## What changed from the Huff

**Guards.** The Huff had none: `add`/`sub`/`mul` wrapped, `fromFixed18` lost
its top bit above 2^127, `div` by zero returned `(|a| >> 128) * 128`
(observed live: `divRaw(2.0, 0) == 256`), `exp` above 88 and `factorial`
above 33 returned `MAX_UINT256`, `exp2(127)` wrapped to the minimum,
`log2(x ≤ 0)` returned 0, `sqrt(x < 0)` and `log2Up(x ≤ 0)` read garbage,
`lambertW0` below −1/e returned 0. The Yul reverts in every one of those
cases, and `test_divergence_*` records each old answer.

**`mul`.** Same function, different construction: the exact 512-bit product
from `mul` and `mulmod(a, b, not(0))`, corrected for signs, middle 256 bits
taken. Cheaper, and the overflow check falls out of it.

**`div`.** Was already a full-precision Bloemen `mulDiv` with a 2^128
multiplier. The old README's "~62-bit two-step chunking" described an
earlier version. Ported verbatim plus the two missing guards.

**`gcd`.** The Huff extracted integer parts with a logical shift and then
tested the sign bit of the shifted word, so negatives were mishandled. The
Yul uses an arithmetic shift and absolute values.

**`factorial`.** Computed by exact integer multiplication instead of a
34-entry jump table. Identical values.

**`lambertW0`.** Redesigned. The Huff seeded from a 64-entry interpolation
table and ran two FSC steps and an IB finisher, documented as quartic.
Measured, each FSC step in this arithmetic roughly doubles the correct bits
(7, 14, 29, 58, 117), so that recipe delivered 50 to 100 bits on (0, 64),
under 40 bits near 0, read past the table above 64 and ran out of gas below
0. The Yul seeds to five to eight bits (Winitzki's approximation for x > 0,
the origin series for −¼ < x < 0, the branch-point series down to −1/e),
runs four FSC steps and one IB step, and measures 118 to 130 bits across the
domain. W(1..5) are still exact table values. The 64-entry table is gone,
which is where most of the bytecode saving came from.

**`lambertWm1`.** New. The Huff had a `lambertwm1.huff` that never shipped
(`huffc` ran out of code size) and could not have worked: it referenced an
undefined constant, had its domain checks inverted, seeded with the wrong
sign and called the step macro with the wrong stack convention. The Yul
routine is a fresh implementation on the secondary real branch, −1/e ≤ x < 0,
W ≤ −1. Neither W₀ step transfers: the FSC residual needs e^−w and the IB
step needs x / w = e^w, and on this branch w reaches about −93 at x = −2^−128,
where one overflows and the other underflows the format. Instead it iterates
the log form w + ln(−w) = ln(−x) by Newton, w′ = w − w (w + ln(−w) − L) / (w + 1),
which is the IB step with the logarithm split and needs only `ln` and `div`.
Seeds are the branch-point series below −¼ and the three-term asymptotic
L − ln(−L) + ln(−L)/L above it; five steps take 8 to 40 seed bits to 120 to
128 outside 2^-20 of −1/e, and v5's double-word step takes that to the
nearest word. v4 returned exactly −1 at the format's branch point
−floor(2^128/e); W₋₁ there is −1 − 2^-63.3, which v5 returns.

**Shortcuts.** v4 kept the exact shortcuts from `shortcut_constants.huff`
for `pow`, `cbrt` and `lambertW0`. v5 keeps W(1..5) (nearest, W(4) one ULP
up from v4) and, for `pow`, y = 1, y = 2 (the rounded square), x = 2 and
x = 10; `cbrt` and the other `pow` shortcuts take the double-word path,
which is the nearest word and exact on perfect powers. The bytecode on
Sepolia predates that file (its W(2) is the iterated value, 3 ULP from the
table), so the equivalence suite compares those paths to the Huff within a
tolerance rather than to the bit.

## Legacy baseline

`contracts/archive/huff/fp127.sepolia.runtime.hex` is the runtime bytecode
of the Huff contract at `0xfae694D0c2c44181791F838c54Ed64C3151FfE30`,
fetched at Sepolia block 11,857,616 with `make fetch-baseline`. keccak256
of the hex text: `0x74946c4dd85b8bbbab56d77d34defdf4e66ea15c0647993ea445f0b95591d10b`.
The equivalence suites etch it, so no Huff toolchain is needed. The Huff
sources are archived under `contracts/archive/huff/` (see its README); the
Huff-era test suites were replaced by the files above and the Huff-era
documents by [`docs/fp127/HISTORY.md`](../../../docs/fp127/HISTORY.md).

# FP127 in Yul

Signed 127.128 fixed-point arithmetic for the EVM. One `int256` per value,
`value = raw / 2^128`, so `ONE = 2^128`. Range about ±1.7e38, 128 fractional
bits on an absolute grid of 2^-128: 38 digits at 1, 32 at 10^-6, 8 at
10^-30.

This directory holds **one hand-written source** and the files generated
from it.

| file | role |
|---|---|
| `FP127.yul.src` | the source of truth: Yul function bodies only |
| `FP127.yul`, `FP127E.yul`, `FP127H.yul`, `FP127N.yul`, `FP127S.yul` | generated: the five deployable objects (from 3.0), each with a selector dispatcher |
| `FP127Lib.sol` | generated: Solidity library, one `assembly` block per op |
| `IFP127.sol`, `IFP127E.sol`, `IFP127H.sol`, `IFP127N.sol`, `IFP127S.sol` | generated: interface and custom errors of each deployed object |
| `abi.json`, `abiE.json`, `abiH.json`, `abiN.json`, `abiS.json` | generated: ABI of each deployed object |
| `ops.json` | generated: op table (signature, selector, object, domain, reverts) for the site |
| `FP127Caller.sol` | hand-written: thin `staticcall` harness around a deployed object |
| `FP127Type.sol` | hand-written: the typed API, `type FP127 is int256` with operators over `FP127Lib` |

```
make gen              # regenerate the outputs
make gen-check        # fail if they are stale (CI runs this)
make vectors          # regenerate the mpmath vectors in test/fp127/vectors/
make vectors-check    # fail if they are stale (CI runs this)
make test             # gen-check + vectors-check + equivalence, behaviour, precision
make precision-report # docs/fp127/precision.md from the last test run
make bench            # gas ladder for every op and form -> docs/benchmarks/
make size             # the five objects' runtime sizes against the 24,576-byte limit
```

## Chains: CLZ (Osaka) required

Every leading-bit count goes through one helper, `msb(x) = 255 - clz(x)`,
on the CLZ opcode (EIP-7939, Fusaka/Osaka, 5 gas), guarded so msb(0) = 0.
Both forms (the object and `FP127Lib.sol`) need it: compile the library
with solc >= 0.8.31 and `evm_version = "osaka"` (this repo pins 0.8.38),
and use either only on a chain that has CLZ. `isqrtw`'s seed comes from the
same exact bit length (a linear fit on the normalised mantissa, five Newton
steps where Solady's seed needed seven; `scripts/fp127/generators/isqrt_seed.py`
proves the bound). Results are the same words and reverts as v5, which
ran a binary search for msb: about 140 to 1,900 gas less per op through the
object, and 200 to 1,400 less inline where an op counts leading bits
([`docs/benchmarks/gas.md`](../../../docs/benchmarks/gas.md)).

Supported chains are those with CLZ, as of 2026-10-22 (each probed live;
dates and names are the networks' announced activations):

| chain | CLZ since | upgrade |
|---|---|---|
| Ethereum mainnet | 2025-12-03 | Fusaka |
| Sepolia | 2025-10-14 | Fusaka |
| Hoodi | (probe) | Fusaka |
| Arbitrum One | 2026-01-08 | ArbOS 51 |
| OP Mainnet | 2026-07-08 | Upgrade 19 "Karst" |
| Unichain | 2026-07-08 | Upgrade 19 "Karst" |
| Base | 2026-05-28 | "Azul" |
| Polygon PoS | 2026-03-04 | Lisovo |
| BNB Chain | 2026-04-28 | Osaka / Mendel |
| Gnosis | 2026-04-14 | Fusaka |
| Scroll | (probe) | Galileo |
| Linea | (probe) | |

**Unsupported** (no CLZ, probed 2026-10-22): zkSync Era, Avalanche C-Chain,
Polygon zkEVM.

The objects deploy fine on a chain without CLZ (the init code only copies
the runtime), but there the opcode is invalid and every call that counts
leading bits fails and burns all the gas it was given. Probe a chain before
deploying to it or calling it: an `eth_call` with no `to` and the creation
code `0x60011e60005260206000f3` (PUSH1 1, CLZ, PUSH1 0, MSTORE, PUSH1 32,
PUSH1 0, RETURN) returns the word `0xff` where CLZ exists. `make probe-clz
RPC=<url>` runs it, and every `deploy-*` target runs it first and refuses
to send unless the answer is 255.

## Two forms, one source

The same Yul function bodies are emitted twice.

**Deployed objects.** From 3.0 (v9) FP127 deploys as five objects by idea,
as FP19 does: `FP127` the number (arithmetic and its directed forms,
conversions, `sqrt`, `cbrt`, `gavg`, `hypot`, `inv`, `factorial` and the
small ops, 32 exports), `FP127E` the elementary functions on the exp/log
kernels (`exp`, `exp2`, `exp10`, `expm1`, `ln`, `log2`, `log10`, `log2Up`,
`log1p`, `pow`, `powu`, `compound`), `FP127H` the hyperbolic functions
(`sinh`, `cosh`, `tanh`, `atanh`), `FP127N` the normal distribution (`erf`,
`erfc`, `normCdf`) and `FP127S` Lambert W (`lambertW0`, `lambertWm1`). An
export's `/// @object` tag in the source places it; an untagged one is in
`FP127`. Each object carries only its exports and their callees (a kernel
two objects share is copied into each: bytes, not gas) and has its own
interface and ABI; `FP127Lib.sol` holds every export. Runtime sizes at the
split: 3,367, 12,716, 7,560, 5,005 and 7,994 bytes, where v8's one object
had 779 bytes free, so each had room for the second stage behind its
rounding tests. The split kept v8's words, op for op (`test/objects/ObjectsEqLib.t.sol`
with `FP_REF_DIR` set to v8's artifact under every name); since then every
object gained its second stages (see Rounding), and the sizes are `FP127`
3,728, `FP127E` 18,808, `FP127H` 13,093, `FP127N` 9,088 and `FP127S` 11,817
bytes. Salts `"FP127 v9"`, `"FP127E v9"`, `"FP127H v9"`, `"FP127N v9"`,
`"FP127S v9"`; not deployed yet (the predicted CREATE2 addresses are in
`CHANGELOG.md` and `contracts/src/ladder/ILadder.sol`).

Each object wraps its bodies in a dispatcher that finds the 4-byte selector
by binary search (a flat switch under ten exports: `FP127H`, `FP127N`,
`FP127S`). It is deployed with CREATE2
through the deterministic proxy at
`0x4e59b44847b379578588920cA78FbF26c0B4956C`; the salt names the version.
v8 (salt `"FP127 v8"`, 53 ops, 23,797 bytes of runtime, an evm osaka
build that needs CLZ) is live on Sepolia at
`0x466eCEde5Dc25189AD9ED999d0B4D41Cb022510B` since 2026-10-28 (Blockulator
3.0): the same words as v6, with `exp`, `div`, `factorial`, `compound` and
the erfc tail cheaper. v7 (salt `"FP127 v7"`, `0xb97E0b824d86470BfAA52fe44f09363755d52591`,
2026-10-27: `exp` and `div` only) was superseded by v8 before mainnet and stays live. v6 (salt `"FP127 v6"`, Blockulator 2.2) stays live at
`0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4`; there `pi` became the constant `FP127Lib.PI` and `gcd` was removed. v5
(salt `"FP127 v5"`, 55 ops, Blockulator 2.1) stays live at
`0x619176d72D7a12390F8970802943D344c0fd3fE2`, and v1 to v4 stay deployed. Record and verification recipe in
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
9. Functions of another library's source come in through an import line,
   `/// @import fp19 as w19: wexp, wexpm1, wlnw, ...`. The generator takes
   each named function of `contracts/src/fp19/FP19.yul.src` and every
   function it calls, transitively, and renames each `w19_<name>` where the
   imported text defines or calls it: the source calls `w19_wexpm1`, which
   calls `w19_wmul`, `w19_msb` and so on, so the helpers both sources define
   (`msb`, `rev`, `mul512`, `log2m`, ...) never meet. Lines naming the same
   library and alias join. The imported code is validated with the source;
   an imported parameter or local named like one of this source's functions
   is rejected (Yul forbids the shadowing), and every error it reverts with
   must be declared here. An import costs nothing until an export calls it:
   objects and the library's blocks carry closures only, so the line in
   `FP127.yul.src` (FP19's wide kernels for the second stages, at 2^-497 to
   2^-510) changes no object's bytes by itself. BlockulatorWad's base source
   is the same mechanism without the prefix. `test/fp127/imports/` holds the
   demonstration: a test-only library importing FP19's `wexpm1` and its whole
   `expm1`, and FP127's `rbad127`, checked against `FP19Lib`, mpmath and the
   rounding `rbad127` describes (`test/fp127/Imports.t.sol`).

## Typed API

`FP127Type.sol` is opt-in: `type FP127 is int256`, with `+ - * /`, unary
`-` and `< > <= >= == !=` bound globally, and every other op attached, so
`x.exp()` and `a.mulUp(b)` work. `*` is `mul` (floor) and `/` is `div`
(truncated toward zero); the directed forms keep their names. Each function
is a pure free function that only re-types its arguments, so the words and
reverts are `FP127Lib`'s. Conversions: `FP127.wrap` / `unwrap` (or `fp127(raw)`,
as PRBMath's `sd()`), `fp127FromWad(uint256)` and `toWadDown` / `toWadUp` for
unsigned WADs, `fp127FromFixed18` and `toFixed18*` for signed ones,
`fp127FromInt` / `toIntDown` / `toIntUp`, and the constants `ONE` and `PI`.
`FP19Type.sol` holds the typed FP127 ↔ FP19 conversions.

```solidity
import {FP127, ONE, PI, fp127FromWad} from "fp127/FP127Type.sol";

FP127 b = fp127FromWad(1.5e18) * ONE.exp();  // 1.5e; * is FP127Lib.mul
FP127 r = (b - ONE).ln() / PI + -ONE;        // operators and attached ops
bool inside = r >= -ONE && r <= ONE;
uint256 paid = b.toWadDown();                // 4077422742688567853, floored
```

`make typed` (part of `make test`) fuzzes every typed function against the
raw call, result and revert data byte for byte, and compares the gas of one
small contract per op in each form. Through the IR (`via_ir = true`) every
op costs exactly the same. Under the legacy pipeline the wrapper is one more
internal call: 37 to 78 gas, nothing on the comparisons, and 112 to 114 on
`floor`, `frac` and `sign`, which the legacy optimizer inlines whole into a
raw caller but not through the wrapper.

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
| `exp(x)` | e^x, correctly rounded; 0 below −90 (under half an ULP from −89.42) | `Overflow` above 88 |
| `exp2(x)` | 2^x, correctly rounded; 0 below −129 | `Overflow` at or above 127 |
| `exp10(x)` | 10^x, correctly rounded; 0 below 2^-129 | `Overflow` from 2^127 (x ≈ 38.23) |
| `ln`, `log2`, `log10` | x > 0, correctly rounded | `OutOfRange` |
| `log2Up(x)` | ceil(log2 x): msb − 128, plus one unless a power of two; exact | `OutOfRange` |
| `sqrt(x)` | floor, x ≥ 0 | `OutOfRange` |
| `cbrt(x)` | all x, odd; nearest decided exactly; exact for perfect cubes | `Overflow` only at −2^255 |
| `pow(x, y)` | x^y for x ≥ 0, correctly rounded, exact ties decided exactly; 0^0 = 1; shortcuts y = 1, y = 2 (the rounded square), x = 2, x = 10 | `OutOfRange` for x < 0, `Overflow` |
| `powu(x, n)` | x^floor(n) for any integer n, correctly rounded: binary exponentiation on a 256-bit mantissa, a 512-bit one where that is ambiguous, one rounding; `pow` from \|n\| = 2^16; exact when representable | `Overflow`, `DivisionByZero` for 0^negative |
| `compound(r, n)` | (1 + r)^floor(n), correctly rounded: for \|n\| ≥ 16 n log2(1 + r) and 2^t in one word, then at 2^-299 with a test, `powu` last | `Overflow`, `DivisionByZero` |
| `inv(x)` | 1/x, truncated toward zero (floor(2^256 / \|x\|), re-signed) | `DivisionByZero`, `Overflow` |
| `abs`, `neg` | | `Overflow` at −2^255 |
| `sign`, `min`, `max`, `clamp`, `avg`, `floor`, `frac` | exact, never revert | |
| `ceil`, `round` | exact | `Overflow` at the top of the range |
| `zeroFloorSub`, `dist`, `lerp` | checked compositions | `Overflow` |
| `gavg(a, b)` | √(a·b) to nearest, rounded once from the exact 512-bit product (never a tie); two negatives give the positive root | `OutOfRange` for opposite signs, `Overflow` only at a = b = −2^255 |
| `hypot(a, b)` | √(a² + b²) to nearest, rounded once from the exact sum of squares (never a tie); no intermediate overflow | `Overflow` where the root passes the largest word |
| `factorial(n)` | floor(n)! for 0 ≤ n < 34 | `OutOfRange` |
| `lambertW0(x)` | W(x) for x ≥ −1/e, correctly rounded: the double-word Newton step's value tested by `rbad127`, a log-form step at 2^-510 on a miss; W(0) = 0 the one exact point | `OutOfRange` |
| `lambertWm1(x)` | W₋₁(x) for −1/e ≤ x < 0, correctly rounded as `lambertW0` | `OutOfRange` |
| `log1p(x)` | ln(1 + x), the sum exact in the format, correctly rounded with `ln` | `OutOfRange` at or below −1, `Overflow` |
| `expm1(x)` | e^x − 1, correctly rounded: on the grid the one is exact, so `exp(x)` − 1 word for word (a tested series below 1/16); −1 below −90 | `Overflow` above 88 |
| `sinh`, `cosh` | \|x\| ≤ 88, correctly rounded; (u ± u/(1+u))/2-shaped from one double-word exp and one division at 2^-192 (within 3 units plus 2^-299 relative, `rbad127` err 2^20), e^\|x\| and e^−\|x\| in two words past it; sinh is x below 2^-65, cosh is 1 below 2^-64 | `Overflow` |
| `tanh(x)` | all x, correctly rounded; u/(u + 2) or (1 − w)/(1 + w) at 2^-192 (err 2 or 3 units), (1 − w)/(1 + w) in two words past it; ±1 exactly from \|x\| = 46 | never |
| `atanh(x)` | \|x\| < 1, correctly rounded; log1p(2\|x\|/(1 − \|x\|))/2, one division and one unrounded log at 2^-192 (err 2^47 units), then `l2p` of 1 ± \|x\| (2^-248), then ln(1 ± \|x\|) in two words | `OutOfRange` |
| `erf(x)`, `erfc(x)` | all x, correctly rounded; series to 4, e^(x²) erfc(x) by a minimax polynomial beyond, at 2^-192 (`rbad127` err 3·2^44 and 2^20 units, derived), FP19's series or continued fraction in two words past it; erfc(9.3) is one ULP, zero beyond | never |
| `normCdf(x)` | Φ(x) = erfc(−x/√2)/2, the N(d) of Black-Scholes, correctly rounded as `erf` (y = \|x\|/√2 exact in the second stage); Φ(−13) is two ULPs, Φ(−14) is zero, Φ(14) is one | never |

**Constants.** `FP127Lib.ONE` is 2^128 and `FP127Lib.PI` is π · 2^128 to
the nearest integer, `0x3243f6a8885a308d313198a2e03707345` (38 digits). Pi
was an op, Ramanujan's series in the format, through Blockulator 2.1; as a
constant it is exact to the grid and costs nothing, and an object caller can
copy the literal. e, ln 2 and ln 10 are not constants: `exp(ONE)`, `ln(2 ONE)`
and `ln(10 ONE)` return the same nearest words, and `exp2`, `log2` and
`log10` absorb most uses of them.

**The tie rule.** To nearest is floor(v + 1/2) on the 2^-128 grid: ties
toward +∞ (`round64`, `rnd192`, `rndw` and the logs' `x384mul` all add half
and floor). `powu` and `compound`, `cbrt`, and the odd `sinh`, `tanh`, `atanh` and
`erf` round the magnitude and apply the sign, so their ties go away from
zero; `scripts/fp127/oracle.py` rounds each op the same way, and make sweep's
*correctly rounded* column compares with its word. `rbad127(v, g, err)` is
the rounding test under this rule (3.0, called by the ops' second stages as
they land): 1 when a value within `err` of `v`, carried with `g` guard bits
below the grid (`v`'s low `g` bits; `g = 256` for a two-word value's low
word), may round to another word than `v` does: when the low bits are within
`err` below half a step, at most `err` above it, or `err` reaches half a
step. A `v` exactly on the midpoint with `err = 0` is the tie itself and
rounds up. Its body is one interval test, the low bits within [half − err,
half + err), with no branch, so solc inlines a call with constant `g` and
`err` (about 40 gas; the branching form cost 190). `rbadw(v, err)` is
`rbad127(v, 256, err)` in four operations, for the exponentials, whose
bodies are too large for solc to inline into: there a call with the general
`g` cost 2 to 3% of the op. `scripts/fp127/generators/bounds127.py` measures each fast value's
stated bound against 120-digit truth (CI runs it).

**Rounding (3.0).** Every op is correctly rounded: its result is the exact
real value rounded once, in the direction the op states, on every input of
its domain. The transcendentals round to nearest under the tie rule above:
`exp`, `exp2`, `exp10`, `expm1`, `sinh`, `cosh`, `tanh`, `atanh`, `pow`,
`cbrt`, `ln`, `log2`, `log10`, `log1p`, `powu`, `compound`, `lambertW0`,
`lambertWm1`, `erf`, `erfc` and `normCdf`. Each one's fast value carries a
bound derived in the source and tested by `rbad127` (`rbadw`, `rbadm127`)
before the one rounding; where the bound could reach a midpoint a wider
stage decides, in two words on FP19's kernels (2^-497 to 2^-510, far below
what the 2^-128 grid can see) or, for `pow`, `powu` and `cbrt`, by an exact
computation where a tie is possible. `gavg` and `hypot` return the nearest
word decided exactly: for raw words A and B the raw result is the root of
the integer A·B or A² + B², taken in two words and rounded once, and an
integer's root is never a tie. `add`, `sub`, `log2Up` and the integer ops
are exact. `mul`, `mulDown`, `divDown`, `sqrt`, `toFixed18`,
`toFixed18Down` floor; `mulUp`, `divUp`, `toFixed18Up` ceil; `div`, `inv`,
`fromFixed18` truncate.

What is proven and what is tested: the arithmetic, the directed forms, the
conversions, `inv`, `sqrt` and the rounding ops are proven for every input
against a separate specification (Halmos, and an exact integer argument for
the root: [`docs/proofs.md`](../../../docs/proofs.md)); `gavg` and `hypot`
are fuzzed against a bit-by-bit root of the same integer. The
transcendentals' guarantee rests on three checks, each a merge gate: every
fast value's stated bound is measured against 120-digit truth
(`scripts/fp127/generators/bounds127.py`; the largest ratio of measured
error to stated bound is 0.92, the exponentials'); `make sweep` runs every
op on seeded random inputs plain, with every rounding test forced (the last
stage alone, `gen.py --wide-lib`) and with the fast tests forced (the middle
stage alone, `--mid-lib`), each against the correctly rounded word: 0
misrounded in all three passes; and `make test` holds every op to its
contract on the committed vectors, which carry the inputs found within a
bound of a midpoint. The last stage rounds without a test, so the one case
no check covers is a transcendental whose true value lies within that
stage's error of a midpoint (2^-290 for Lambert W, 2^-444 for the error
function, 2^-487 or better elsewhere, relative where the op's bound is); no
such input is known, and where a midpoint can be hit exactly (`pow`, `powu`,
`cbrt`, `exp2(−129)`) it is decided exactly.

Up to v8 `pow` was the one exception: with log2 x absolute to 2^-299 a
base within 2^-88 of one raised past 2^90 (results near 2^120) missed by
up to 1e11 ULPs, and it rounded exact ties down; 3.0 repairs both (below).
Up to v8 `gavg` and `hypot` were the Huff's compositions, kept bit-identical
to it: the floored root of a floored product or sum of squares. A product
under one ULP floored to zero, so they were low by up to 2^64 ULPs
(gavg(2^-78, 2^-60) returned 0 for 2^-69), and they reverted with
`Overflow` wherever a·b or a² + b² passed 2^127 though the root fits. 3.0
drops that definition for FP19's: one rounding of the exact value.

**At the token edge.** The replays
([`docs/benchmarks/replay-*.md`](../../../docs/benchmarks/)) put every loss
where a protocol leaves the fixed point for integer token units. Round
toward the protocol there: `mulUp`/`divUp`/`toFixed18Up` for what it
charges or takes in, `mulDown`/`divDown`/`toFixed18Down` for what it pays
out, `floor` and `ceil` for whole units. `div` truncates toward zero, so a
negative quotient rounds up; `divDown` does not.

**The v5 kernels.** An exponential is split exactly into 2^n 2^f with f a
512-bit fraction (`y2nf`: the exponent y·log2(b), log2(b) to 2^-384, formed
as one 768-bit product; `exp` and the hyperbolics reduce x = n·ln 2 + r
directly, `expr`), and e^r − 1 is evaluated by `expk` to 2^-311 relative,
never above the truth (below). The result is rounded once from the kernel's
high word. `l2p` refines the one-word log2 by one Newton step through
`expk` (2^-313 absolute); `pow` uses it. `cbrt` is
Newton on y³ = |x|·2^256 with precision doubling (a seed from the bits, four
word steps, one residual step, exact cubes) and an exact midpoint test.
`ln`, `log2` and `log10` round the one-word kernel when its 2^-145 error
bound cannot change the answer and fall back to `l2p` within 2^-145 of a
midpoint (about one input in 2^17); from 3.0 `l2p`'s value is tested too
(`rbadm127`) and a two-word Newton step (`l2w`, `logw`) decides what it
cannot. Lambert W near −1/e (1 + e·x < 1/8)
seeds q = 1 + W by a degree-16 fit in √(2(1 + e·x)) and takes one
sixth-order step on the double-word exp kernel (W within 6 units of 2^-192
whatever q); elsewhere it seeds from a crude logarithm, runs one-word
fourth-order log-form steps at 2^-126 on a table-driven logarithm until one
starts within 2^-22, and ends with one Newton step whose residual comes
from the double-word exponential, its value V at 2^-300 within
err = 2^(2·msb|y| + msb|w| − 421) + |y|·2^-124 + 16 units (y the step's
residual: Newton's own y²|w|/(2|1 + w|³) twice over, B's top word, the
floors). From 3.0 `rbad127` tests either value and, when its bound may
cross a midpoint, `lwwide` decides: FP19's `lwfix` in 127.128, one
log-form Newton step at 2^-510 (`w19_wrecip`, `w19_wmul`, `w19_wlnw`,
`w19_kln2`) from that value, within 2^-290 absolute, rounded once. W(x) is
transcendental for every word x but 0 (Lindemann–Weierstrass), so it is
never a midpoint and the tie rule never applies; W(0) = 0, and |x| < 2^-65
returns x (W(x) − x is under 2^-130). `bounds127.py` checks both bounds
(largest ratio 0.20 and 0.58 of the stated one) and
`precise_model.py lambertw` the stages before them. `scripts/fp127/generators/precise_model.py` models the
kernels in integers and measures them.

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
every step.

**The one-word kernels (Blockulator 2.2).** 2^f and log2 of a mantissa at
2^-192, behind the erf family, Lambert W's iterations, pow's first try
(`pow2t`) and the logs' rounding test, were rewritten after measuring what
the EVM charges (FP19's kernel pass did the same): `exp2frac` is one
16-entry table level and the degree-15 minimax polynomial of 2^r on
[0, 1/16) (2^-147.7 relative; v5's was a degree-24 fit on [0, 1),
2^-145.9), Horner on the products' high words with the top 10 steps in one
word, within 2^-146.7 relative: 2,216 → 1,380 gas a call. `log2m` is two
additive 16-entry levels by word-only reductions (a shift and a div by
16 + i or 256 + i; the table's logarithm added, never multiplied) and the
degree-14 minimax polynomial of log2(1 + w)/w on [0, 2^-8] (2^-153.0),
within 2^-160.5 absolute where v5's seven stages were about 2^-150: 2,594 →
1,333. `scripts/fp127/generators/kernel192.py` fits them (Remez,
`scripts/fp19/generators/minimax.py`), models them in exact integers,
checks that the source holds its Yul verbatim and measures them against
their bounds; `precise_model.py` and `erf_model.py` take them from there.
Blockulator 2.2's `expk` kept v5's eight 2-bit groups (each factor
multiplied in line, 4,046 gas in the inline library).

**Division (after 2.2).** `div`, `divDown` and `divUp` share `divw`, the exact
floor(|a|·2^128 / |b|): when |a| and |b| are both under 2^64 it is long
division in two 64-bit digits (|a|·2^64 fits a word and every remainder is
below |b| < 2^192, so shifted by 64 it fits too: three `div`s and a `mod`);
a third digit when only |b| is under 2^64; Bloemen's mulDiv (`divu`)
beyond. 2.2 ran the mulDiv for every |a| ≥ 1. The directed forms add one
`mulmod` for exactness. Same words and the same reverts: `div` 649 → 412
gas on the ladder (PRBMath 509), `divDown` and `divUp` 818 → 475.

**The double-word exp kernel (after 2.2).** `expk` works in X form, a value
H·2^-256 + L·2^-384 with L a small word: about 300 bits are what the
callers round (2^n(1 + s) at 2^-128 with n up to 126), not 512, so every
product's cross terms are one-word multiplies and no carry is propagated
until the end. Three 16-entry levels take the top 12 bits of r, each
e^(j·16^-i) − 1 (at 2^-384) applied in the expm1 form s + c + s·c; the rest,
u < 2^-12, goes to u + u²·g(u), g the degree-16 minimax polynomial of
(e^u − 1 − u)/u² on [0, 2^-12] (2^-292.8 relative), its top steps in one
word, the middle ones on the products' high words and the last three in X
form. Every constant and product floors and g's constant is lowered by its
fit's bound, so s never exceeds e^r − 1 and cannot reach 1: within
2^-311.2 relative, 2^-313.0 measured. `lnmul` gives f·ln 2 in X form with
its cross terms in one word; `exp` and `expx` (expm1, sinh, cosh, tanh,
Lambert W's last step) skip the 768-bit exponent product: n comes from
log2 e at 2^-119 in one word, r = x − n·ln 2 from ln 2 at 2^-384, and one
test corrects n by one (on the 2^-128 grid x − m·ln 2 stays 2^-137 from 0
for every 0 < |m| ≤ 300, so the test cannot be fooled). The rounding reads
only the kernel's high word: with e = n + 129 the word is half of
2^e + ⌊sh·2^(e−256)⌋ + 1, and the low word is under one unit of that sum.
`exp` 5,360 → 2,716 gas (the typical median of `gas.json`, inline;
PRBMath 2,816), `expk` alone 4,046 → about 2,200. `scripts/fp127/generators/expk.py` fits and certifies
g, models the kernel in exact integers, checks that the source holds its
Yul verbatim and measures it against its bound; `precise_model.py` takes
it from there. The pinned optimizer had made three copies of the kernel
(FunctionSpecializer on Lambert W's literal branch flag); one call with
chosen arguments keeps one, and FP127 is 1.1 KB smaller than 2.2's.

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
1700/⌊x²⌋ + 10 came from `scripts/fp127/generators/erf_model.py`; 3.0
replaces the fraction (below).

**`compound` and the erfc tail (3.0).** `compound` went through `powu`'s
binary exponentiation, about 9,200 gas for a per-second rate over a year
(25 squarings and their multiplies). For |n| ≥ 16 it now takes the
logarithm first: t = n log2(1 + r) is formed exactly from the one-word
`log2m` (within 2^-160.5, so t within |n| 2^-160), and `pow2t` rounds 2^t
when its bound, given |n| 2^113 + 1 as the scale of t's error, cannot
change the word. Where it cannot (a result from about 2^3 with a large n,
or within reach of a midpoint), `l2p` (log2 to 2^-299) and `pow2rt`, the
double-word 2^t with a rounding test (V within (1 + |n|) 2^-299 relative plus
one unit of `sh`, eb = |n| 2^-42 + 3 units), try again; |t| from 128 is
Overflow or 0 by itself; `powu`, whose 512-bit decider is the nearest word,
takes |n| < 16, ties and what is left. `precise_model.py fastcompound`
checks both bounds on 10,008 random inputs (8,818 decided in one word,
1,186 of the other 1,190 at 2^-299, every one the nearest word; largest
error over bound 0.16 and 0.33). Sweep median 9,245 → 3,360 gas. The
inline `FP127Lib.compound` now carries the log and exp kernels: 11.0 KB
where it was 1.3 KB ([`size.md`](../../../docs/benchmarks/size.md)).

The erfc tail, 4 < x ≤ 9.5, ran the continued fraction, about 20,000 gas
near x = 4. It is now e^(−x²) g(x) with g(x) = e^(x²) erfc(x) the degree-43
minimax polynomial in t = (2x − 13.5)/5.5 (`erfct`): what is rounded is
erfc on the 2^-128 grid, so the fit is held to an absolute 2^-175 on erfc,
the tolerance 2^-175 e^(x²) on g, which is 2^-149 relative at x = 4 and
2^-45 at 9.5; within 0.244 of it after the coefficients' rounding on all
of the interval (3.0: certified, below).
`erf_model.py --tail` models the Horner in integers (largest error against
erfc 2^18.25 units of 2^-192, the fraction's 2^18.17, both e^(−x²)'s);
`--check` holds the source to its Yul (CI). 7,650 gas at every x of the
tail; the products are written in line (calls to `mulg` cost 10,770).

**The hyperbolics, correctly rounded (3.0).** `sinh`, `cosh`, `tanh` and
`atanh` (`FP127H`) round their fast value only when its stated bound cannot
change the word (`rbad127`); otherwise a second stage decides on FP19's wide
kernels, imported as `w19_*`, whose absolute error (2^-497 to 2^-505) is far
below anything the 2^-128 grid can see. `sinh` and `cosh`: V within 3 units
of 2^-192 plus 2^-299 of e^|x|/2, under 2^19 units at |x| = 88, so err is
2^20 (a constant: solc inlines the test); past it e^|x| = 2^k (1 + E) by
`w19_wexpr`, e^−|x| by `w19_wrecip`, subtracted or added at 2^-510 (FP19's
`hypw`). `tanh`: u/(u + 2) below 1/4 (u within 1.1 units below, slope at
most 1/2, plus the quotient's floor: err 2), (1 − w)/(1 + w) from 1/4
(slope at most 2: err 3); past it (1 − w)/(1 + w) with w = e^−2|x| in two
words (FP19's `tanhw2`). `atanh`: the one-word log (2^-145) with err 2^47
units; past it `l2p` of the exact words 1 + |x| and 1 − |x|, times ln 2/2
at 2^-256 (err 2^-248, the constant's floor under a log of at most 129,
`rbadm127`); past that ln(1 + |x|) and ln(1 − |x|) by `w19_wlnw`, the
difference at 2^-384 plus j ln 2. `bounds127.py` measures every err
(largest ratio 0.75, tanh below 2^-5). Sweep medians, inline: `sinh` 3,868
→ 3,924, `cosh` 3,824 → 3,877, `tanh` 3,821 → 3,873, `atanh` 2,750 →
2,814; the second stages cost about 27,700 (`sinh`, `cosh`), 28,200
(`tanh`), 12,400 (`atanh`'s `l2p`) and 60,900 (its wide logs), and no
sweep input reached one. `FP127H` is 13,093 bytes (7,560 before; 13,234 before the merge with the other phases); inline, `sinh` and `cosh`
take about 6.4 KB, `tanh` 6.7 KB and `atanh`, with three stages, 11.2 KB
([`size.md`](../../../docs/benchmarks/size.md)).

**The elementary functions, correctly rounded (3.0).** Every op of `FP127E`
now rounds a value only when its stated bound cannot change the word, and a
last stage decides the rest: FP19's wide kernels (`w19_*`, 2^-497 to 2^-503
absolute, far below anything the 2^-128 grid can see), or an exact
computation where a tie is possible. Each bound is derived in the source and
measured by `bounds127.py`; `make sweep` runs every op plain, with every
test forced (the last stage alone) and with the fast tests forced (the
middle stage alone): 0 misrounded in all three.

- `exp`, `exp2`, `exp10`: V = 2^n (1 + s) from `expk` (2^-311.2) and the
  reduction (2^-376) is within 2^(n − 311.1), under 2^(n + 73) + 1 units of
  2^-384 (largest ratio 0.92); the test (`rbadw`) takes 2^200 for every n ≤
  126. Past it `expw`: |x| c at 2^-510 modulo 4 from the three-word
  c 2^638 (c = 1, ln 2, ln 10), FP19's `wexpr` and `wexpm1`, rounded once
  by `rndw`: within 2^(n − 502.9), under 2^-248 ULP. No tie exists except
  2^-129 = `exp2(−129)`, which is exact and rounds up. `exp2` forms f ln 2
  in line (`lnmul` with nothing below 2^-256).
- `ln`, `log2`, `log10`, `log1p`: the one-word value and `nearmid` as
  before; `l2p` (2^-299, 2^85 units of 2^-384) is now tested (`rbadm127`;
  ln and log10 2^135, the constant's 2^-257 times |log2 x| ≤ 2^7); past it
  one Newton step in two words (`l2w`: f0 = l2p − (ms − 128), 2^-f0 = (1 +
  E)/2 by `wexpm1`, d = m 2^-f0 − 1 from the exact three-word product,
  log2(1 + d) = d log2 e within d² < 2^-597) and c (a + F) summed at 2^-500
  (`logw`): within 2^-497.8. `log1p` is `ln` of the exact 1 + x, so it is
  correctly rounded with `ln` (the grid is absolute: no relative loss near
  zero).
- `expm1`: on the 2^-128 grid the one is exact, so `expm1(x)` is `exp(x)`
  − 1 word for word; beyond 1/16 it is exactly that. Below, the series stays
  (cheaper) with a test: within 2 units of 2^-192 (each Horner step's floor
  and truncation under 1 + 1/k, damped by |x|/k ≤ 1/32; measured 1.02),
  and `expw` − 1 behind it.
- `pow`: `pow2t` first, as before. The middle stage (`powmid`) takes `l2p`
  while |y| ≤ 2^14 or off the near-one band (|log2 x| ≥ 2^-7.48 bounds |y|
  by 2^14.52 for any result in range: t within 2^-284.4), and log2 x
  relative within 2^-8 of one with a larger y (`tnear`: d = x − 1 exact,
  FP19's `mratio` for ln(1 + d)/d within 2^-272.1 relative, so t within |t|
  2^-271.9); t split exactly, 2^f by `expk`, and the test
  2^(n + 121) + 3 or 2^(n + 102) + 3 units of 2^-384 (largest ratios 0.29,
  0.33). Past it `powslow`: an exact tie first (`powtie`: x = c 2^a with c
  odd gives an odd multiple of 2^-129 only for a y = −129 exactly, so y is
  3, 3/2, 43/2^j (j ≤ 5) or 129/2^j (j ≤ 7), c a perfect 2^j-th power b^(2^j)
  and the word (b^p + 1)/2; for c = 1 it is 2^-129 itself), else log2 x in
  two words (FP19's `wlog2s` near one, `l2w` and `wlog2u` elsewhere), t =
  y log2 x split at 2^-510 and 2^t by `wexpm1`: within 2^-487.5 relative,
  under 2^-232 ULP. v8 rounded the ties down (`pow2r` is one-sided low).
- `powu`: the 256-bit mantissa's test is `rbad127` (forceable); the 512-bit
  `powus` behind it is the last stage, within (3k + 2) 2^-510 relative
  (each product 3 2^-510 after renormalising, squarings doubling it;
  `bounds127.py` largest ratio 0.62), under 2^-237 ULP while k < 2^16 and
  exact at a tie (a tie needs k ≤ 129 and c^k < 2^256, so every partial
  product fits). From k = 2^16 the doubling would reach 2^-384, so `powu`
  calls `pow` (no tie is possible there): the sweep's |n| from 2^16 cost
  11,780 / 146,949 gas (median, p99) on `powus`, now 3,572 / 10,762.
- `compound`: unchanged; `powu` is its backstop, so it inherits the above.

Gas on the sweep's inputs, inline, median (master → 3.0): `exp` 2,697 →
2,828 (+4.9%), `exp2` 2,640 → 2,684 (+1.7%), `exp10` 2,970 → 3,069
(+3.3%), `expm1` 2,061 → 2,076, the logs unchanged (their fast path is
untouched), `pow` 3,314 → 3,376 (+1.9%; p99 8,399 → 8,833, the middle
stage's test) on the inputs both versions share, `powu` 3,493 → 3,520,
`compound` 3,301 → 3,360. The last stages cost about 25,000 (the
exponentials), 29,000 (the logs) and 55,000 to 90,000 (`pow`); the middle
stage of the logs about 5,500. `pow`'s sweep now holds 961 bases within 2^-8
of one (t spread over the whole range) and 39 exact ties, where v8
misrounded 48. `FP127E` is 18,808 bytes (12,716 before).

**The error function, correctly rounded (3.0).** `erf`, `erfc` and
`normCdf` (`FP127N`) test their value at 2^-192 with `rbad127` before the
one rounding, each branch's err a constant. Both bounds are derived, not
only measured (`erf_model.py --bounds`, run by `--check` in CI). `erfs`
(|x| ≤ 4): e^(−x²) carries `exp2frac`'s 2^-146.7 relative (plus 2^-187 at most
from its exponent's floors), which times erf is at most 2^45.29 units of
2^-192; the series' floors (each term's error bounded by the recurrence
ε_k ≤ ε_(k−1)·2x²/(2k + 1) + 1, the stop no later than the first term
under a unit, the true tail from the earliest stop) and the three floored
products add under 2^23.5: err 3·2^44 (2^45.58). `erfct` (4 < x < 9.375):
the fit is certified on all of [−1, 1], not only at points: on 20,000 steps
the error is at most the larger end value plus h²/8 max |e″|, and |e″| on
each of 1,000 blocks is bounded by its Taylor series at the block's centre
(g's derivatives by g^(n+1) = 2x g^(n) + 2n g^(n−1)) with the Lagrange
remainder from |g^(n)(x)| ≤ n!/(√π x^(n+1)), which follows from g(x) =
(2/√π) ∫ e^(−s² − 2xs) ds: 0.2438 of the tolerance 2^-175 e^(x²) (0.2404
the largest sampled). With e^(−x²)'s 2^-146.7 times erfc(4), t's rounding
(|g′| ≤ 1/(√π x²)) and the Horner's 43 floors (under 43 units of g, times
e^(−x²)): 2^19.41 units, err 2^20. `normCdf`'s y = |x|/√2 at 2^-192 and
the halving add under 4 units, inside the same errs. Past the test,
`erfw127` hands x to FP19's wide second stage as its exact (u, m) (y =
|x|/√2 stays exact, as in `fp19_normCdf`): below y = 7 the series in two
words (`w19_erfser2`), from 7 one minus the continued fraction
(`w19_erfccf2`), 2^-444 or better, rounded once to the grid 2^-128
(2^-127 for `normCdf`, which is ½ ± that). erf(y) is never a midpoint for
x ≠ 0, so `erfc` = 1 ∓ that word and Φ = ½ ± it exactly. `bounds127.py`
measures both errs (ratios 0.41 and 0.30). The fast path skips the second
stage unless within 2^-18.4 ULP of a midpoint (series) or 2^-44 (tail);
the vectors carry 13 random inputs found that close, decided by it (v8 had
each right). Inline A/B on the sweep's inputs: `erf` median 3,630 → 3,689,
`erfc` 3,510 → 3,592, `normCdf` 3,715 → 3,750 (the same old and new calls side by side; the sweep table, its runner recompiled around the new library, reads 3,623 → 3,775, 3,497 → 3,654 and 3,694 → 3,823); `make cdf` on [−6, 6]:
`normCdf` 12,435 → 12,466, `erfc` 9,140 → 9,211; the second stage costs
about 48,000 at the median and 355,000 at most (the two-word series just
below y = 7). `FP127N` is 9,088 bytes (5,005 before; 9,013 before the merge with the other phases); inline, each op
about 8.9 KB (5.5 before).

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
Every nearest op is the nearest word on every vector.
`make sweep` measures 1,500 to 5,000 seeded random inputs per op
([`docs/benchmarks/sweep.md`](../../../docs/benchmarks/sweep.md)) against
the correctly rounded word, three times (plain, every rounding test forced,
the fast tests forced): 0 misrounded in each pass. v4 had `exp` at 4e32
ULPs, `pow` at 4.8e34, `cbrt` at 1.6e14, `compound` at 1.3e6, Lambert W at
1,153 and `ln`, `log2` at 1.31 and 1.88; v5 brought every transcendental
within half an ULP on the sweep, and 3.0 adds the tests and stages that
make that the contract on every input.

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
on where x falls, the continued fraction near x = 4 being the dearest. In
3.0 `compound` is about 3,400 at the median and the erfc tail 7,650 at
every x; the series just below 4 (about 20,500) is now the family's dearest.

v5 against v4, medians through the object: `exp` 7,076 (+1,544), `exp10`
5,794 (+908), `exp2` 4,664 (−696), `pow` 5,742 (−352), `cbrt` 7,270 (+551),
`cosh` 9,372 (+155), `atanh` 7,646 (−1,055), `log1p` 4,397 (−317),
`lambertW0` 41,481 (+5,242), `lambertWm1` 31,764 (+2,402). Six more selectors
put about 90 gas on most other ops' dispatch. The directed ops cost 900 to
2,600 through the object, 950 to 1,530 inline.

3.0 (v9) against v8, medians on the ladder's inputs: inline, the rounding
tests cost the transcendentals a few percent (`exp` 2,726 → 2,845, `exp2`
2,549 → 2,593, `exp10` 2,987 → 3,086, `sinh` 3,880 → 4,029, `cosh` 3,835 →
3,981, `tanh` 3,828 → 3,967, `atanh` 2,746 → 2,910, `erf` 7,588 → 7,739,
`erfc` 7,573 → 7,721, `normCdf` 8,286 → 8,421, `lambertW0` 8,170 → 8,367,
`lambertWm1` 8,052 → 8,247, `pow` 3,028 → 3,050, `powu` 2,809 → 2,872),
`expm1` is cheaper (3,106 → 2,968), the logs and the arithmetic are
unchanged, and `gavg` and `hypot` fall (1,079 → 1,003, 1,366 → 1,164).
Through the objects the smaller dispatchers take 20 to 70 gas off most ops
(`add` 708 → 682, `mul` 928 → 862, `log2` 965 → 900); `exp` is 3,000 →
3,058 and `hypot` 1,840 → 1,690.

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

**`factorial`.** A table of the 34 values, two to a word, found by a binary
search on n/2, as the Huff's jump table was (v6 multiplied them out: 190 to
1,918 gas; the table is about 400 at every n). Identical values.

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

# Formal proofs: core arithmetic and directed rounding

For every input, each op below returns exactly the word its reference
specification returns, or reverts with exactly the error the specification
names. "Every input" means every int256 (or uint256) argument: Halmos executes
the compiled inline library symbolically, so one passing run covers all 2^256
or 2^512 inputs, not a sample of them.

The libraries are the inline forms, [`BL127Lib.sol`](../contracts/src/bl127/BL127Lib.sol)
and [`BL19Lib.sol`](../contracts/src/bl19/BL19Lib.sol). They are generated
from the same Yul as the deployed objects, and
[`test/objects/ObjectsEqLib.t.sol`](../test/objects/ObjectsEqLib.t.sol) fuzzes
every object against its library for equal words and equal reverts. The
proofs are about the libraries' bytecode as solc 0.8.38 compiles it (optimizer
on, 200 runs, evm osaka); the objects are covered through that equality, not
proved directly.

## Status

`proven` is for all inputs, against a spec whose integer primitives are
themselves proved (the lemmas in brackets, [below](#lemmas)). `proven-except`
is for all inputs outside a stated window, where a pinned counterexample shows
the op leaving its documented semantics. `fuzzed` has no symbolic proof: the
op is fuzzed against the exact spec. `counterexample` is fuzzed and has a
pinned input where it leaves its spec. Solver time is Halmos's own, with
bitwuzla, from the last recorded run, on one machine with two solver threads per
check and each check allowed 2,000 s (the timed-out checks below ran out of that
allowance); it varies by a factor of two or so between runs. The fuzz results in
`proofs.json` are from 50,000 runs per test.

<!-- proofs:table -->
| library | op | status | spec | solver time | checks |
|---|---|---|---|---:|---|
| BL127 | `add` | proven | a + b exact; Overflow outside int256 | 1 s | `check_bl127_add` |
| BL127 | `sub` | proven | a - b exact; Overflow outside int256 | 1 s | `check_bl127_sub` |
| BL127 | `mul` | proven (L1, L2) | floor(a b / 2^128); Overflow when it leaves int256 | 45 s | `check_bl127_mul` |
| BL127 | `mulDown` | proven (L1, L2) | floor(a b / 2^128) | 48 s | `check_bl127_mulDown` |
| BL127 | `mulUp` | proven (L1, L2) | ceil(a b / 2^128); Overflow when it leaves int256 | 419 s | `check_bl127_mulUp_outside`, `check_bl127_mulUp_window` |
| BL127 | `div` | proven (K127, L5) | trunc(a 2^128 / b); DivisionByZero; Overflow | 1 s | `check_bl127_div` |
| BL127 | `divDown` | proven (K127, L5) | floor(a 2^128 / b) | 3 s | `check_bl127_divDown` |
| BL127 | `divUp` | proven (K127, L5) | ceil(a 2^128 / b) | 2 s | `check_bl127_divUp` |
| BL127 | `inv` | proven (L4, L5) | trunc(2^256 / x); DivisionByZero; Overflow | 0 s | `check_bl127_inv` |
| BL127 | `sqrt` | proven (R1, R2, L1) | floor(sqrt(x 2^128)); OutOfRange below zero | – | `isqrt.py` |
| BL127 | `gavg` | fuzzed | sqrt(a b) to nearest from the exact product (never a tie); OutOfRange for opposite signs; Overflow only at a = b = -2^255 | – | FuzzProofs |
| BL127 | `hypot` | fuzzed | sqrt(a^2 + b^2) to nearest from the exact sum of squares (never a tie); Overflow past 2^255 - 1 | – | FuzzProofs |
| BL127 | `floor` | proven | 2^128 floor(x / 2^128) | 0 s | `check_bl127_floor` |
| BL127 | `ceil` | proven | 2^128 ceil(x / 2^128); Overflow at 2^255 | 0 s | `check_bl127_ceil` |
| BL127 | `round` | proven | 2^128 floor(x / 2^128 + 1/2); Overflow at 2^255 | 0 s | `check_bl127_round` |
| BL127 | `toFixed18` | proven | floor(x 10^18 / 2^128) | 20 s | `check_bl127_toFixed18` |
| BL127 | `toFixed18Down` | proven | floor(x 10^18 / 2^128) | 19 s | `check_bl127_toFixed18Down` |
| BL127 | `toFixed18Up` | proven | ceil(x 10^18 / 2^128) | 48 s | `check_bl127_toFixed18Up` |
| BL127 | `fromFixed18` | proven | trunc(x 2^128 / 10^18); OutOfRange outside [-2^127, 2^127) | 0 s | `check_bl127_fromFixed18` |
| BL19 | `add` | fuzzed | a + b rounded to nearest (237 bits, ties away) | – | `check_bl19_add` |
| BL19 | `sub` | fuzzed | a - b rounded to nearest | – | `check_bl19_sub` |
| BL19 | `mul` | proven (L1, L3) | a b rounded to nearest | 430 s | `check_bl19_mul` |
| BL19 | `mulDown` | proven (L1, L3) | a b rounded toward -inf | 1023 s | `check_bl19_mulDown` |
| BL19 | `mulUp` | proven (L1, L3) | a b rounded toward +inf | 731 s | `check_bl19_mulUp` |
| BL19 | `div` | proven (K19, L3) | a / b rounded to nearest | 114 s | `check_bl19_div` |
| BL19 | `divDown` | proven (K19, L3) | a / b rounded toward -inf | 303 s | `check_bl19_divDown` |
| BL19 | `divUp` | proven (K19, L3) | a / b rounded toward +inf | 264 s | `check_bl19_divUp` |
| BL19 | `inv` | proven (K19) | 1 / x rounded to nearest | 60 s | `check_bl19_inv` |
| BL19 | `sqrt` | fuzzed | sqrt(x) rounded to nearest | – | FuzzProofs |
| BL19 | `floor` | proven | the integral number at or below x | 199 s | `check_bl19_floor` |
| BL19 | `ceil` | proven | the integral number at or above x | 202 s | `check_bl19_ceil` |
| BL19 | `round` | proven | the nearest integral number, halves away from zero | 206 s | `check_bl19_round` |
| BL19 | `toUintDown` | proven | floor(x) as uint256 | 1 s | `check_bl19_toUintDown` |
| BL19 | `toUintUp` | proven | ceil(x) as uint256 | 1 s | `check_bl19_toUintUp` |
| BL19 | `toIntDown` | proven | floor(x) as int256 | 1 s | `check_bl19_toIntDown` |
| BL19 | `toIntUp` | proven | ceil(x) as int256 | 1 s | `check_bl19_toIntUp` |
| BL19 | `toFixed18` | fuzzed (L1) | x 10^18 to the nearest integer, halves away | – | `check_bl19_toFixed18` |
| BL19 | `toFixed18Down` | fuzzed (L1) | floor(x 10^18) | – | `check_bl19_toFixed18Down` |
| BL19 | `toFixed18Up` | fuzzed (L1) | ceil(x 10^18) | – | `check_bl19_toFixed18Up` |
| BL19 | `fromUint` | proven | x rounded to nearest | 36 s | `check_bl19_fromUint` |
| BL19 | `fromUintDown` | proven | x truncated to 237 bits | 27 s | `check_bl19_fromUintDown` |
| BL19 | `fromUintUp` | proven | x rounded up to 237 bits | 64 s | `check_bl19_fromUintUp` |
| BL19 | `fromFixed18` | proven (K18, L5) | round(round(x) / 10^18), each to nearest (one rounding below 2^237) | 1661 s | `check_bl19_fromFixed18` |
<!-- /proofs:table -->

The same data, with paths and the lemma list, is
[`docs/benchmarks/proofs.json`](benchmarks/proofs.json).

## Counterexamples found, and fixed

The proofs found two BL127 ops leaving their documented semantics; both are fixed in #159 and pinned as regression tests in [`test/proofs/Fuzz.t.sol`](../test/proofs/Fuzz.t.sol).

- **`sqrt` returned floor + 1** where x·2^128 + 1 is a perfect square (s + 1)^2 (e.g. raw x = 2^126 + 1): the Huff's seven Newton steps, kept bit for bit until #159, could stop one above the floor. BL127 now returns the floor on every input, and that is now proven (R1, R2 below). `gavg` and `hypot`, then built on it, no longer are: since 3.0 they round once from the exact product or sum of squares (below).
- **`mulUp` reverted where its result fits**: where floor(a·b/2^128) = −2^255 − 1 the ceiling −2^255 fits; mulUp now returns it, proven in that window (`check_bl127_mulUp_window`) as on every other input.

## How the proofs work

**Halmos.** Each `check_` function in
[`test/proofs/ProofsBL127.t.sol`](../test/proofs/ProofsBL127.t.sol) and
[`ProofsBL19.t.sol`](../test/proofs/ProofsBL19.t.sol) calls the op through
an external call to the test contract (so a revert comes back as data), calls
the reference spec, and asserts that both returned the same word or reverted
with the same 4-byte error. Halmos runs it with symbolic arguments and asks the
solver, for every path, whether the assertion can fail. Two changes to
Halmos 0.3.3 are made at run time by
[`test/proofs/halmos_clz.py`](../test/proofs/halmos_clz.py), which then runs
Halmos's own main:

- **CLZ.** Halmos has no CLZ opcode (a16z/halmos#586), and both libraries
  count leading bits with it. The wrapper adds it as a binary search on the
  top bits, and `--selftest` proves that term equal to the definition for all
  2^256 words.
- **Commuted products.** Halmos leaves a product of two symbolic words
  uninterpreted, so the solver knows only that equal operands give equal
  products, and MUL(a, b) and MUL(b, a) would be unrelated. The wrapper orders
  the operands canonically; multiplication commutes, so this is sound.

**Uninterpreted arithmetic.** Because products, quotients and remainders of
two symbolic words stay uninterpreted, a passing check holds for any
interpretation of MUL, DIV, MOD and MULMOD that maps equal arguments to equal
results. The solver never bit-blasts a 256-bit multiplier; 256-bit nonlinear
arithmetic, which no solver closes, never reaches it. The specs reach exact
integers through a few primitives built from those opcodes, and each primitive
is a lemma proved separately over unbounded integers.

**The specs.** [`Ref127.sol`](../test/proofs/Ref127.sol) and
[`Ref19.sol`](../test/proofs/Ref19.sol) are written from the documented
semantics, not from the library code, and are meant to be read:

- BL127: the exact signed 512-bit product (L1, L2), floored or ceiled by a
  shift and a remainder test, range-checked once; quotients from the exact
  floor quotient of |a| 2^128 by |b| (the EVM's DIV below 2^256, the kernel
  K127 above) and the exact remainder (MULMOD), re-signed and stepped one
  unit toward the named direction.
- BL19: `unpack` into sign, biased exponent and 237-bit significand; each op
  forms its exact value as (-1)^s (N + d) 2^k, N an integer of up to 512 bits
  and d in [0, 1) known only by whether it is zero (the sticky part); then one
  reference rounding, `toFloat`: the bit length of N by a binary search of
  comparisons, R = floor(N / 2^t) for t = L - 237, and the rest compared with
  half of 2^t as an exact 512-bit integer (to nearest, ties away from zero on
  the magnitude) or tested for zero (directed: up when anything was cut and the
  direction points away from zero); a carry to 2^237 moves one binade up; then
  Overflow above the largest exponent and, below the smallest, zero or (away
  from zero) the smallest number. Sums are exact on a grid 270 bits under the
  larger term's last bit, the smaller term entering by its floor and a sticky
  bit when it lies further down. Integer results (`floor`, `ceil`, `round`,
  `toUint*`, `toInt*`, `toFixed18*`) use `toInt`, the same rounding to an
  integer.

None of the specs uses the libraries' normalisation, leading-bit count, guard
bits or rounding helpers. Where a spec shares a computation with the library
it is a primitive below, used as the definition of the integer it stands for.

## Lemmas

[`test/proofs/lemmas.py`](../test/proofs/lemmas.py) and
[`test/proofs/kernel.py`](../test/proofs/kernel.py) prove them with Z3 over
unbounded integers, reading each opcode by its definition (MUL is a b mod
2^256, DIV the floor quotient, MULMOD a b mod n) and settling the bit
operations with bit-vector lemmas. [`test/proofs/isqrt.py`](../test/proofs/isqrt.py)
proves R1 and R2 in exact integers: an exhaustive check of the seed, then the
Newton error bound iterated in exact rationals.

| lemma | statement | used by |
|---|---|---|
| L1 | `(MULMOD(a, b, 2^256 - 1) - MUL(a, b) - borrow, MUL(a, b))` is the exact 512-bit a b | every product |
| L2 | for two's complement a, b, subtracting [a < 0] b and [b < 0] a from that high word gives the exact signed product | BL127 mul, mulDown, mulUp |
| L3 | the product of two BL19 exponent fields (each below 2^19) is zero iff one of them is | BL19 mul, div and their directed forms, handed to the solver as an assumption |
| L4 | for 2 <= u < 2^256, `DIV(2^256 - u, u) + 1` = floor(2^256 / u) | BL127 inv |
| L5 | `(x XOR SAR(255, x)) - SAR(255, x)` is \|x\| (the specs' magnitudes, spelled as the libraries spell them so their products meet) | BL127 div, divDown, divUp, inv; BL19 fromFixed18 |
| K18 | `Kernels.q18(m)` (two word divisions by 5^18, m split at bit 100) = floor(m 2^60 / 5^18), every intermediate a word | BL19 fromFixed18 |
| K127 | `Kernels.divq(a, b)` = floor(a 2^128 / b) for 0 < a >> 128 < b | BL127 div, divDown, divUp |
| K19 | `Kernels.divh(a, b)` = floor(a 2^255 / b) for 0 < b, a < 2 b | BL19 div, divDown, divUp, inv |
| R1 | `isqrtw(z)` = floor(sqrt z) for 2^128 <= z < 2^256: the seed within 2^-4 for every leading value, five Newton steps to below 2^-128, the correction exact | BL127 sqrt |
| R2 | BL127 `sqrt(x)` = floor(sqrt(x 2^128)) for 0 < x < 2^255: above 2^128 one more Newton step lands on the floor or one above, and the 512-bit square check takes off the one | BL127 sqrt |

K127 and K19 are Remco Bloemen's mulDiv, copied verbatim into
[`Kernels.sol`](../test/proofs/Kernels.sol) from the library source: the
remainder's borrow, the division of the divisor's powers of two out of both
words (a bit-vector lemma for `AND(SUB(0, b), b)`, then the 256 values of the
power one by one), the OR that is an addition because the bits are disjoint,
the seed `XOR(MUL(3, d), 2)` correct to 4 bits, and six Newton steps, each a
polynomial identity that doubles the bits of the inverse, 4 to 256. A Halmos
check uses the kernel as the floor quotient: the op is proved equal to the
spec computed with the kernel, and the kernel equal to the floor by its
lemma. They are also fuzzed against a long division
([`Fuzz.t.sol`](../test/proofs/Fuzz.t.sol)), as both square roots and BL127's
gavg and hypot are against exact integer roots, and the BL19 ops whose Halmos
checks time out (add, sub and the three toFixed18 roundings) against the same
specs the checks use (`Ref19`).

## What is and is not covered

- **Covered:** the 19 BL127 and 24 BL19 ops in the table, for all inputs,
  including which error each revert carries, except the ops marked fuzzed:
  BL127's `gavg` and `hypot` and BL19's `sqrt` (no symbolic check), and
  BL19's `add`, `sub`, `toFixed18`, `toFixed18Down` and `toFixed18Up`, where
  Halmos runs out of time (2,000 s each). Those are fuzzed against the same
  exact specs.
- **BL127's square root: proven outside the solver.** A Newton iteration's
  result is the floor only by an argument about its convergence, which Halmos
  cannot close: it would have to relate the iterate's square to the input
  through uninterpreted products. [`test/proofs/isqrt.py`](../test/proofs/isqrt.py)
  makes that argument in exact integers: the seed is within 2^-4 of the root
  for each of its 196,608 leading values (checked one by one), five steps take
  the relative error to below 2^-128, so the last iterate is the floor or one
  above it, and the two corrections are exact (R1, R2). It also checks that a
  line-by-line transcription of the code is `math.isqrt` on 60,973 edge and
  random inputs. BL19's root is fuzzed against an exact integer root
  (`testFuzz_bl19_sqrt`, and next to exact squares
  `testFuzz_bl19_sqrt_near_squares`).
- **BL127's `gavg` and `hypot`: fuzzed.** Since 3.0 each is the nearest
  integer to the root of an exact two-word integer (the raw words' product,
  or their sum of squares), taken by `rootw`: `isqrtw` as above, one Newton
  step and an exact 512-bit test that steps the candidate up at most twice
  (the error argument is in its comment). They are fuzzed against the
  bit-by-bit root of the same integer, rounded once, with the same reverts
  (`testFuzz_bl127_gavg`, `testFuzz_bl127_hypot`, next to the midpoints
  `testFuzz_bl127_roots_near_mid`, and the extreme words
  `test_bl127_roots_edges`).
- **Not covered:** the deployed objects directly (see the top), every other op
  (the transcendentals, `avg`, `lerp`, the comparisons and so on),
  gas, and the compiler. The proofs trust Halmos's model of the EVM, the
  wrapper's two changes, bitwuzla and Z3, and the reading of each lemma's code
  as the integers its model names.

## Reproduce

```
uv tool install halmos==0.3.3      # or: pip install halmos==0.3.3
make proofs                        # CI's subset: lemmas, the CLZ self-test, the fuzz tests, the checks under two minutes
make proofs PROOFS_FULL=1          # every check, 50,000 fuzz runs; rewrites proofs.json and the table above
uv run python test/proofs/run.py --only bl19_add   # one op (any regex on the check names)
```

Halmos downloads bitwuzla on first use (`HALMOS_ALLOW_DOWNLOAD=1`, which
`make proofs` sets). The full run takes about an hour on 16 cores; JOBS and
SOLVER_THREADS set the parallelism.

# Formal proofs: core arithmetic and directed rounding

For every input, each op below returns exactly the word its reference
specification returns, or reverts with exactly the error the specification
names. "Every input" means every int256 (or uint256) argument: Halmos executes
the compiled inline library symbolically, so one passing run covers all 2^256
or 2^512 inputs, not a sample of them.

The libraries are the inline forms, [`FP127Lib.sol`](../contracts/src/fp127/FP127Lib.sol)
and [`FP19Lib.sol`](../contracts/src/fp19/FP19Lib.sol). They are generated
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
bitwuzla, from the last full run (`make proofs PROOFS_FULL=1`), on one machine
with two solver threads per check; it varies by a factor of two or so between
runs.

<!-- proofs:table -->
| library | op | status | spec | solver time | checks |
|---|---|---|---|---:|---|
| FP127 | `add` | proven | a + b exact; Overflow outside int256 | 1 s | `check_fp127_add` |
| FP127 | `sub` | proven | a - b exact; Overflow outside int256 | 1 s | `check_fp127_sub` |
| FP127 | `mul` | proven (L1, L2) | floor(a b / 2^128); Overflow when it leaves int256 | 45 s | `check_fp127_mul` |
| FP127 | `mulDown` | proven (L1, L2) | floor(a b / 2^128) | 48 s | `check_fp127_mulDown` |
| FP127 | `mulUp` | proven-except (L1, L2) | ceil(a b / 2^128); Overflow when it leaves int256 | 183 s | `check_fp127_mulUp_outside` |
| FP127 | `div` | proven (K127, L5) | trunc(a 2^128 / b); DivisionByZero; Overflow | 1 s | `check_fp127_div` |
| FP127 | `divDown` | proven (K127, L5) | floor(a 2^128 / b) | 3 s | `check_fp127_divDown` |
| FP127 | `divUp` | proven (K127, L5) | ceil(a 2^128 / b) | 2 s | `check_fp127_divUp` |
| FP127 | `inv` | proven (L4, L5) | trunc(2^256 / x); DivisionByZero; Overflow | 0 s | `check_fp127_inv` |
| FP127 | `sqrt` | fuzzed | floor(sqrt(x 2^128)); OutOfRange below zero | – | FuzzProofs |
| FP127 | `floor` | proven | 2^128 floor(x / 2^128) | 0 s | `check_fp127_floor` |
| FP127 | `ceil` | proven | 2^128 ceil(x / 2^128); Overflow at 2^255 | 0 s | `check_fp127_ceil` |
| FP127 | `round` | proven | 2^128 floor(x / 2^128 + 1/2); Overflow at 2^255 | 0 s | `check_fp127_round` |
| FP127 | `toFixed18` | proven | floor(x 10^18 / 2^128) | 20 s | `check_fp127_toFixed18` |
| FP127 | `toFixed18Down` | proven | floor(x 10^18 / 2^128) | 19 s | `check_fp127_toFixed18Down` |
| FP127 | `toFixed18Up` | proven | ceil(x 10^18 / 2^128) | 48 s | `check_fp127_toFixed18Up` |
| FP127 | `fromFixed18` | proven | trunc(x 2^128 / 10^18); OutOfRange outside [-2^127, 2^127) | 0 s | `check_fp127_fromFixed18` |
| FP19 | `add` | in-progress | a + b rounded to nearest (237 bits, ties away) | – | `check_fp19_add` |
| FP19 | `sub` | in-progress | a - b rounded to nearest | – | `check_fp19_sub` |
| FP19 | `mul` | in-progress (L1, L3) | a b rounded to nearest | – | `check_fp19_mul` |
| FP19 | `mulDown` | in-progress (L1, L3) | a b rounded toward -inf | – | `check_fp19_mulDown` |
| FP19 | `mulUp` | in-progress (L1, L3) | a b rounded toward +inf | – | `check_fp19_mulUp` |
| FP19 | `div` | in-progress (K19, L3) | a / b rounded to nearest | – | `check_fp19_div` |
| FP19 | `divDown` | in-progress (K19, L3) | a / b rounded toward -inf | – | `check_fp19_divDown` |
| FP19 | `divUp` | in-progress (K19, L3) | a / b rounded toward +inf | – | `check_fp19_divUp` |
| FP19 | `inv` | in-progress (K19) | 1 / x rounded to nearest | – | `check_fp19_inv` |
| FP19 | `sqrt` | fuzzed | sqrt(x) rounded to nearest | – | FuzzProofs |
| FP19 | `floor` | in-progress | the integral number at or below x | – | `check_fp19_floor` |
| FP19 | `ceil` | in-progress | the integral number at or above x | – | `check_fp19_ceil` |
| FP19 | `round` | in-progress | the nearest integral number, halves away from zero | – | `check_fp19_round` |
| FP19 | `toUintDown` | in-progress | floor(x) as uint256 | – | `check_fp19_toUintDown` |
| FP19 | `toUintUp` | in-progress | ceil(x) as uint256 | – | `check_fp19_toUintUp` |
| FP19 | `toIntDown` | in-progress | floor(x) as int256 | – | `check_fp19_toIntDown` |
| FP19 | `toIntUp` | in-progress | ceil(x) as int256 | – | `check_fp19_toIntUp` |
| FP19 | `toFixed18` | in-progress (L1) | x 10^18 to the nearest integer, halves away | – | `check_fp19_toFixed18` |
| FP19 | `toFixed18Down` | in-progress (L1) | floor(x 10^18) | – | `check_fp19_toFixed18Down` |
| FP19 | `toFixed18Up` | in-progress (L1) | ceil(x 10^18) | – | `check_fp19_toFixed18Up` |
| FP19 | `fromUint` | in-progress | x rounded to nearest | – | `check_fp19_fromUint` |
| FP19 | `fromUintDown` | in-progress | x truncated to 237 bits | – | `check_fp19_fromUintDown` |
| FP19 | `fromUintUp` | in-progress | x rounded up to 237 bits | – | `check_fp19_fromUintUp` |
| FP19 | `fromFixed18` | in-progress (K18, L5) | round(round(x) / 10^18), each to nearest (one rounding below 2^237) | – | `check_fp19_fromFixed18` |
<!-- /proofs:table -->

The same data, with paths and the lemma list, is
[`docs/benchmarks/proofs.json`](benchmarks/proofs.json).

## Counterexamples found, and fixed

The proofs found two FP127 ops leaving their documented semantics; both are fixed in #159 and pinned as regression tests in [`test/proofs/Fuzz.t.sol`](../test/proofs/Fuzz.t.sol).

- **`sqrt` returned floor + 1** where x·2^128 + 1 is a perfect square (s + 1)^2 (e.g. raw x = 2^126 + 1): the Huff's seven Newton steps, kept bit for bit until #159, could stop one above the floor. FP127 now returns the floor on every input; `sqrt` is fuzzed against the exact root (no symbolic proof yet). `gavg` and `hypot`, built on it, may now be one below the Huff on those inputs.
- **`mulUp` reverted where its result fits**: where floor(a·b/2^128) = −2^255 − 1 the ceiling −2^255 fits; mulUp now returns it. Proven on every other input.

## How the proofs work

**Halmos.** Each `check_` function in
[`test/proofs/ProofsFP127.t.sol`](../test/proofs/ProofsFP127.t.sol) and
[`ProofsFP19.t.sol`](../test/proofs/ProofsFP19.t.sol) calls the op through
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

- FP127: the exact signed 512-bit product (L1, L2), floored or ceiled by a
  shift and a remainder test, range-checked once; quotients from the exact
  floor quotient of |a| 2^128 by |b| (the EVM's DIV below 2^256, the kernel
  K127 above) and the exact remainder (MULMOD), re-signed and stepped one
  unit toward the named direction.
- FP19: `unpack` into sign, biased exponent and 237-bit significand; each op
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
operations with bit-vector lemmas.

| lemma | statement | used by |
|---|---|---|
| L1 | `(MULMOD(a, b, 2^256 - 1) - MUL(a, b) - borrow, MUL(a, b))` is the exact 512-bit a b | every product |
| L2 | for two's complement a, b, subtracting [a < 0] b and [b < 0] a from that high word gives the exact signed product | FP127 mul, mulDown, mulUp |
| L3 | the product of two FP19 exponent fields (each below 2^19) is zero iff one of them is | FP19 mul, div and their directed forms, handed to the solver as an assumption |
| L4 | for 2 <= u < 2^256, `DIV(2^256 - u, u) + 1` = floor(2^256 / u) | FP127 inv |
| L5 | `(x XOR SAR(255, x)) - SAR(255, x)` is \|x\| (the specs' magnitudes, spelled as the libraries spell them so their products meet) | FP127 div, divDown, divUp, inv; FP19 fromFixed18 |
| K18 | `Kernels.q18(m)` (two word divisions by 5^18, m split at bit 100) = floor(m 2^60 / 5^18), every intermediate a word | FP19 fromFixed18 |
| K127 | `Kernels.divq(a, b)` = floor(a 2^128 / b) for 0 < a >> 128 < b | FP127 div, divDown, divUp |
| K19 | `Kernels.divh(a, b)` = floor(a 2^255 / b) for 0 < b, a < 2 b | FP19 div, divDown, divUp, inv |

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
([`Fuzz.t.sol`](../test/proofs/Fuzz.t.sol)), as both square roots are against
exact integer roots.

## What is and is not covered

- **Covered:** the 17 FP127 and 24 FP19 ops in the table, for all inputs,
  including which error each revert carries, except FP127 `mulUp`'s window and
  the two square roots.
- **Square roots: fuzzed.** The result of a Newton iteration is the floor only
  by an argument about the iteration's convergence, which no check here
  closes: the solver would have to relate the iterate's square to the input
  through uninterpreted products. Both are fuzzed against an exact integer
  root (`testFuzz_fp127_sqrt`, `testFuzz_fp19_sqrt`, and next to exact
  squares `testFuzz_fp19_sqrt_near_squares`); FP127's has the pinned
  counterexample above.
- **Not covered:** the deployed objects directly (see the top), every other op
  (the transcendentals, `avg`, `lerp`, `hypot`, the comparisons and so on),
  gas, and the compiler. The proofs trust Halmos's model of the EVM, the
  wrapper's two changes, bitwuzla and Z3, and the reading of each lemma's code
  as the integers its model names.

## Reproduce

```
uv tool install halmos==0.3.3      # or: pip install halmos==0.3.3
make proofs                        # CI's subset: lemmas, the CLZ self-test, the fuzz tests, the checks under two minutes
make proofs PROOFS_FULL=1          # every check, 50,000 fuzz runs; rewrites proofs.json and the table above
uv run python test/proofs/run.py --only fp19_add   # one op (any regex on the check names)
```

Halmos downloads bitwuzla on first use (`HALMOS_ALLOW_DOWNLOAD=1`, which
`make proofs` sets). The full run takes about an hour on 16 cores; JOBS and
SOLVER_THREADS set the parallelism.

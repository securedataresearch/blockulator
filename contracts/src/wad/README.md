# BlockulatorWad

WAD maths with Solady's names, every result correct to the last wei.
`BlockulatorWad` is an inline library on plain 18-decimal integers (x means
x · 10⁻¹⁸) whose functions carry the names and signatures of Solady's
`FixedPointMathLib`, so moving to it is an import swap:

```solidity
import {BlockulatorWad as FixedPointMathLib} from "blockulator/contracts/src/wad/BlockulatorWad.sol";
```

Each function returns the exact real value of its maths on its exact
input, rounded once in the stated direction. Solady and PRBMath are exact
for products and quotients; on the swept inputs (`make wad`,
[`docs/benchmarks/wad.md`](../../../docs/benchmarks/wad.md)) Solady's
`expWad` is off by at least a wei on 48% of inputs, `lnWad` on 24%, `powWad`
on 66% and `lambertW0Wad` on 28% (by up to 1.5 · 10⁹ wei near −1/e), and
PRBMath's `exp`, `ln`, `log2`, `log10` and `pow` on 72 to 98%. BlockulatorWad:
0 wrong of 108,000, every function, every direction.

It uses the CLZ opcode, as FP19 does: compile with `evm_version = "osaka"`
(solc ≥ 0.8.31) and run only on a chain that has CLZ (EIP-7939; see
[FP19's chain list](../fp19/README.md#chains-clz-osaka-required)). There is
no deployed object; the library is inlined into its caller.

## Functions

| function | direction | domain | reverts |
|---|---|---|---|
| `mulWad(uint256, uint256)`, `mulWadDown` | floor | the result fits uint256 | `MulWadFailed()` |
| `mulWadUp` | ceiling | as mulWad | `MulWadFailed()` |
| `divWad(uint256, uint256)`, `divWadDown` | floor | y ≠ 0, the result fits | `DivWadFailed()` |
| `divWadUp` | ceiling | as divWad | `DivWadFailed()` |
| `sMulWad(int256, int256)` | toward zero | the result fits int256 | `SMulWadFailed()` |
| `sMulWadDown`, `sMulWadUp` | floor, ceiling | as sMulWad | `SMulWadFailed()` |
| `sDivWad(int256, int256)` | toward zero | y ≠ 0, the result fits | `SDivWadFailed()` |
| `sDivWadDown`, `sDivWadUp` | floor, ceiling | as sDivWad | `SDivWadFailed()` |
| `sqrtWad(uint256)`, `sqrtWadDown` | floor | any | never |
| `sqrtWadUp` | ceiling | any | never |
| `cbrtWad(uint256)`, `cbrtWadDown` | floor | any | never |
| `cbrtWadUp` | ceiling | any | never |
| `expWad(int256)`, `expWadDown`, `exp` | floor | x ≤ 135305999368893231589 | `ExpOverflow()` |
| `expWadUp` | ceiling | as expWad (one wei, never zero, below −41.4465) | `ExpOverflow()` |
| `lnWad(int256)`, `lnWadDown`, `ln` | floor | x > 0 | `LnWadUndefined()` |
| `lnWadUp` | ceiling | x > 0 | `LnWadUndefined()` |
| `log2Wad(int256)`, `log2WadDown` | floor | x > 0 | `LnWadUndefined()` |
| `log2WadUp` | ceiling | x > 0 | `LnWadUndefined()` |
| `log10Wad(int256)`, `log10WadDown` | floor | x > 0 | `LnWadUndefined()` |
| `log10WadUp` | ceiling | x > 0 | `LnWadUndefined()` |
| `powWad(int256, int256)`, `powWadDown`, `pow` | floor | x ≥ 0 (0^y for y ≥ 0), a result below 2^255 | `LnWadUndefined()`, `ExpOverflow()` |
| `powWadUp` | ceiling | as powWad | as powWad |
| `lambertW0Wad(int256)` | toward zero | x ≥ −367879441171442321 | `OutOfDomain()` |
| `lambertW0WadDown`, `lambertW0WadUp` | floor, ceiling | as lambertW0Wad | `OutOfDomain()` |

The defaults round as Solady's code rounds: floor for the unsigned results
and for exp, ln and pow (its `sar` and right shifts), toward zero for
`sMulWad`, `sDivWad` and `lambertW0Wad` (its `sdiv`; Solady's comment on
sMulWad says "rounded down", its code truncates). The errors are Solady's,
with Solady's selectors, so `vm.expectRevert(FixedPointMathLib.ExpOverflow.selector)`
still passes. `exp`, `ln` and `pow` are PRBMath's names (SD59x18) for the
same functions; PRBMath's `log2`, `log10`, `sqrt`, `mul` and `div` are left
out, since Solady's `log2`, `log10` and `sqrt` are integer functions and
the same names would mean two things. Solady has no WAD log2 or log10; the
names follow its pattern.

## Where it differs from Solady

- **Wider domains, never narrower.** `mulWad`, `mulWadUp`, `sMulWad` revert
  only when the result does not fit, not when x · y passes 2^256; `divWad`,
  `divWadUp`, `sDivWad` only for y = 0 or a result that does not fit, not
  when x · 10¹⁸ passes 2^256 (the 512-bit product, then mulDiv).
- `expWad(135305999368893231589)` returns its value
  (5.7896… · 10⁷⁶, below 2^255); Solady reverts from that input, one wei
  early.
- `powWad(0, y)` is 0 for y > 0 and 10¹⁸ for y = 0, as PRBMath's pow;
  Solady reverts on x = 0 (`lnWad(0)`). 0^y for y < 0 reverts
  `LnWadUndefined()`.
- `powWad` is the exact power (x · 10⁻¹⁸)^(y · 10⁻¹⁸), not
  `expWad(lnWad(x) · y / 10¹⁸)`; where Solady's composed form reverts with a
  checked-arithmetic panic or `ExpOverflow`, this reverts `ExpOverflow()`
  exactly when the result reaches 2^255.
- Every result is exact (Solady's are within its approximation: see above).

## How the last wei is decided

Products, quotients and roots are exact integer arithmetic: the 512-bit
product with 10¹⁸ (or 10³⁶) and one division (by 2^18 and the inverse of
5^18 modulo 2^256, or Remco Bloemen's mulDiv), the integer square root of
x · 10¹⁸ (FP19's word and two-word roots), the integer cube root of
x · 10³⁶ (FP19's seed and Newton steps, one wide step and an exact cube).
The one-word cases take the one-word path Solady takes.

The transcendental functions run in two stages
([`BlockulatorWad.yul.src`](BlockulatorWad.yul.src) states every bound):

1. **A fast value with a bound.** exp, ln, log2, log10 and pow run FP19's
   kernels (`exp2frac`, 2^f within 4.7 units of 2^-254; `log2m`, within
   2.32) on the exact input: x · log2(e) / 10¹⁸ is the exact three-word
   product of the integer x with a two-word constant, and x = m · 2^u is
   split exactly, so the input is never rounded. lambertW0 runs FP19's
   correctly rounded lambertW0 on `fromFixed18(x)`, with the input's
   rounding in its bound (|W(X) − W(t)| ≤ 2^-237 |W| / (1 + W)). The value
   times 10¹⁸ is cut, exactly, into its integer I and the next 256 bits F.
   When F lies farther than the bound from 0 and from 1 (at 2^-256 wei),
   the exact value is strictly between I and I + 1 and the direction picks
   one. On the sweep's inputs, which crowd the wei boundaries, the exact
   cases and the top of the range, 0 (lambertW0) to 0.9% (exp) go on, 6%
   for log2 and log10 and 9% for pow. Half of pow's are exact values: an
   integer power of a decimal rational that is a whole number of wei
   (x 10^-18 = p / (2^b2 5^b5) in lowest terms, so (x 10^-18)^n 10^18 is
   p^n 2^(18 - b2 n) 5^(18 - b5 n), or for n < 0 a power of 2 and 5 over
   p^-n). `wadpowx` decides those exactly before the second stage, in 6,900
   to 7,700 gas against its 54,000. The other half are results above about
   2^175 wei, where the cut needs the power itself to about 2^-275 and the
   second stage is the stage that has it.
2. **The second stage**, when the bound reaches a wei boundary (or the
   value is above about 2^240 wei, where 2^-254 is too coarse): the value
   from the exact input in two words at 2^-510, with FP19's own
   second-stage arithmetic (`wexpm1`, `wexpr`, `wlnw` and the wide
   products), within 2^-500 relative for exp, 2^-495 absolute for the logs,
   2^-428 relative for pow and 2^-380 absolute for lambertW0 (one log-form
   Newton step on exact mantissas). The same cut; a fraction within the
   bound of 0 or 1 is taken as that integer, which is exactly right for the
   exact values (exp(0), ln(1), log2 of 10¹⁸ · 2^k, a perfect power's pow).
   log2 and log10 test their exact cases (x = 10¹⁸ · 2^k, 10^(18+k))
   exactly first.

**What is guaranteed.** The fast stage's bounds are proven (and recomputed
by `make sweep`'s inputs, 0 wrong); the second stage's are stated in the
source. A result can be wrong only if its exact value is not an integer
number of wei and yet lies within the second stage's bound of one: under
2^-170 wei for pow, 2^-236 for the rest. For exp, ln, log2, log10 and
Lambert W no such value is known and none is expected (Lindemann–Weierstrass
rules out exact values other than the listed ones; a non-exact value that
close would be a one-in-2^170 event per input). The same argument stands
behind FP19's correct rounding. It is not a proof for every input, which
for transcendental functions would need an exhaustive worst-case search
over about 2^67 inputs per function.

## Evidence

- `make sweep`: 4,000 seeded inputs per function and direction, 27 rows
  (108,000 results), against the exact value rounded in the stated direction
  (integers for the algebraic functions, mpmath at 300 digits for the rest):
  **0 wrong wei**. The same inputs again through a test-only copy whose fast
  test always fails (`gen.py --lib wad --wide-lib`), so every result is the
  second stage's: **0 wrong**, 13 rows, 52,000 results. The *fallback*
  column is the share that ran the second stage. `make gates` fails on any
  wrong WAD row.
- `make wad`: Solady and PRBMath on the same inputs, in their own rounding
  directions, gas on typical and swept inputs, bytes per call
  ([`docs/benchmarks/wad.md`](../../../docs/benchmarks/wad.md)).
- `test/wad/Wad.t.sol` (in `make test` and CI): known values to the wei,
  Solady's selectors at each end, the algebraic functions fuzzed against
  Solady's exact `fullMulDiv`, `sqrtWad` and `cbrtWad`, Up − Down ∈ {0, 1}
  and monotonicity for the rest.

## Gas

The typical-input medians (`wad.md` has every function, the swept
medians and the 99th percentiles):

| | BlockulatorWad | Solady | PRBMath |
|---|---:|---:|---:|
| mulWad | 107 | 86 | 218 |
| divWad | 103 | 87 | 242 |
| sqrtWad | 388 | 393 | 794 |
| cbrtWad | 748 | 607 | — |
| expWad | 2,357 | 430 | 2,719 |
| lnWad | 2,415 | 544 | 6,980 |
| log2Wad | 2,160 | — | 6,636 |
| powWad | 4,762 | 1,263 | 9,877 |
| lambertW0Wad | 12,097 | 2,808 | — |

The second stage costs 26,000 to 66,000 gas when it runs.

## Built from FP19's source

[`BlockulatorWad.yul.src`](BlockulatorWad.yul.src) is Yul function bodies,
as FP19's source is; `scripts/fp127/gen.py --lib wad` (`make gen-wad`)
reads it with `FP19.yul.src`, whose functions it calls, and writes
`BlockulatorWad.sol` and `ops.json`. `make gen-check` fails when they are
stale. An export without a `leave` is written into its assembly block
rather than called: a call inside a block costs about 50 gas and a block
that defines any function about 25, as much as a one-word mulWad, so the
mul and div exports define none.

Measured before choosing (median gas, the same harness): composing the
inline FP19Lib in Solidity, `toFixed18Down(exp(fromFixed18(x)))`, costs
4,476 for exp, 4,309 for ln and 8,513 for pow, without the last-wei
guarantee (it rounds the input, and FP19Lib does not expose the wide
stage); the generated library's kernels on the exact input cost 2,231,
2,424 and 4,680 with it.

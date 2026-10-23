# Changelog

A release is the public name for a set of deployed contracts. Each contract
keeps its own version in its CREATE2 salt, because the salt names the address;
`contracts/deployments/RELEASE.json` maps the release to every address.

## Unreleased (Blockulator 2.2)

FP256 deploys as four objects by idea, replacing FP256, FP256X, FP256X2 and
FP256X3: **FP256**, the number (arithmetic, roots, comparison, rounding,
conversions: 43 ops, salt `FP256 v5`); **FP256E**, the elementary functions
on one exp/log kernel (exp, exp2, exp10, expm1, ln, log2, log10, log2Up,
log1p, pow, powu, compound; `FP256E v5`); **FP256H**, the hyperbolic
functions (sinh, cosh, tanh, atanh; `FP256H v5`), their own object because
FP256E with them measured 27,308 bytes, over the 24,576 limit, so FP256H
carries its own copy of the kernel; **FP256S**, the special functions (erf,
erfc, normCdf, lambertW0, lambertWm1, factorial; `FP256S v5`). In both
libraries `pi` is now a constant and `gcd` is removed. Without the kernels
the FP256 core is 10,333 bytes, and the room goes to the basic ops' fast
path, bit-identical: through the object `mulDown`/`mulUp` 201 to 267 gas
less, `divDown`/`divUp` 250 to 256, the in-place conversions up to 67, and
add, sub, mul, div 10 to 70 (`docs/benchmarks/gas256.md`).

FP256's exp/log kernels are rewritten, measured first and bit-identical in
every result (correct rounding fixes the word; only the gas and the
fallback rates move): 2^f by two 16-entry table levels and a degree-19
minimax polynomial, log2 by two additive 16-entry levels, one division and a
degree-12 minimax polynomial in y², ln(1 + d)/d and (e^d − 1)/d near zero by
minimax polynomials in place of the Taylor series, every product's high word
in line and the top polynomial steps in one word. Sweep medians, inline:
exp 7,077 → 3,241, ln 7,640 → 3,623, log1p 8,727 → 2,558, expm1 6,523 →
2,390, pow 14,011 → 5,844, compound 16,113 → 6,246, sinh 7,331 → 3,565,
atanh 12,606 → 5,073, erf 16,962 → 12,932, lambertW0 14,524 → 10,623.
FP256E is 21,598 bytes and FP256H 13,021.

FP127's one-word kernels get the same treatment (salt `FP127 v6` at the
deploy): 2^f by one 16-entry table and a degree-15 minimax polynomial
(2^-146.7 relative, from 2^-145.9), log2 by two additive 16-entry levels and
a degree-14 minimax polynomial (2^-160.5 absolute, from about 2^-150). Its
double-word exp kernel multiplies each table factor in line instead of
through a helper called from 23 cases. Every result is the same word; sweep
medians: ln 3,215 → 1,934, log2 2,999 → 1,718, pow 5,861 → 3,375, exp 6,085
→ 5,651, erf 4,879 → 3,623, atanh 3,715 → 2,750, lambertW0 11,765 → 11,308.
FP127 is 21,858 bytes (from 22,272).

Migration: `pi(terms)` → `FP127Lib.PI` / `FP256Lib.PI` (the format's word
nearest π; an object caller copies the literal); `gcd` has no replacement;
an FP256 caller of FP256X, FP256X2 or FP256X3 calls the object that now
holds the op (`contracts/src/fp256/ops.json` names it), through `IFP256`,
`IFP256E`, `IFP256H` or `IFP256S`. The inline libraries keep every other
signature.

## Blockulator 2.1 (2026-10-21)

Both rulers round once: every FP127 transcendental to the nearest word,
every FP256 op correctly rounded or exact, and the directed ops for the
token edge. Deployed 2026-10-21, Sepolia blocks 11,966,114 to 11,966,639.

| component | version | Sepolia |
|---|---|---|
| FP127 | FP127 v5, 55 ops, 19,863 bytes | `0x619176d72D7a12390F8970802943D344c0fd3fE2` |
| FP256 | FP256 v4, 37 ops, 24,512 bytes | `0xA3C8C8700465F9e20Ff9dfA64066c2EF693Aa6c9` |
| FP256X | FP256X v4, 5 ops, 22,266 bytes | `0x175246B258Cc0dC3efEFe74b5fac8cC52C0c40d0` |
| FP256X2 | FP256X2 v4, 10 ops, 19,889 bytes | `0xE655bB8b1Cf848cAf3FD69F381289d144f5Bc697` |
| FP256X3 | FP256X3 v4, 15 ops, 6,844 bytes | `0x59D51481cb2EA924EC17FE263cd05b90CEF22383` |
| LadderRunner | FP127 ladder v9 | `0xCd4581E0a9Cf014d1aF660F62a7D96039efE7DC5` |
| EdgeRunner | FP127 ladder v9 | `0xcA89eeA1831c38B62d2d3332ECbb8A57BaF246fF` |

Records: `contracts/deployments/{RELEASE,FP127,FP256,Ladder}.md`. FP127
and the four FP256 objects are verified on Sourcify and Blockscout and pass
their smoke tests against the live contracts; the thirteen ladder contracts
are verified on Sourcify. FP127 v5's first send ran out of gas under the
old 20M deploy limit and created nothing; `DEPLOY_GAS` is now 40M and every
deploy target rejects a reverted receipt. The earlier objects (FP127 v1 to
v4, FP256 releases one to three, ladder v1 to v8) stay deployed.

### FP127 v5

Salt `FP127 v5`, 55 ops, 19,863 bytes of runtime, deployed 2026-10-21 at
`0x619176d72D7a12390F8970802943D344c0fd3fE2`.

- Every transcendental returns the nearest word. `exp`, `exp2`, `exp10`,
  `expm1`, `sinh`, `cosh` and `tanh` round once from a double-word kernel
  good to about 2^−300; `ln`, `log2`, `log10`, `log1p`, `pow` and `cbrt`
  round the one-word value when its error bound allows and fall back to the
  double word near a midpoint; `powu` and
  `compound` settle ambiguous roundings on a 512-bit mantissa; Lambert W
  ends with a double-word Newton step. Random-input sweep, max error in
  ULPs, v4 → v5: `exp` 4.0e32 → 0.5, `pow` 4.8e34 → 0.5, `cbrt` 1.6e14 →
  0.5, `expm1` 8.2e31 → 0.5, `compound` 1.3e6 → 0.5, `lambertW0` 1,153 →
  0.5, `lambertWm1` 253 → 0.5, `ln` 1.31 → 0.5, `log2` 1.88 → 0.5. `pow`
  is the exception at extreme exponents: error under 2^−299 (1 + |y|)
  relative, nearest while |y| x^y < 2^140 or so.
- Directed rounding for the token edge: `mulUp`, `mulDown`, `divUp`,
  `divDown`, `toFixed18Up`, `toFixed18Down`. `mul`, `div`, `sqrt` and
  `toFixed18` are unchanged.
- Domain ends now round to nearest: `exp` returns 0 below −90 (v4: −88, two
  ULPs early), `expm1` −1 below −90, `exp2` 0 below −129, `tanh` ±1 from 46
  (v4: 44, four ULPs early); `exp10` decides Overflow on the exact
  exponent; `log2Up` is exact (v4 was one low just above a power of two);
  `lambertWm1` at −floor(2^128/e) is −1 − 2^−63.3 (v4: −1).
- `pow` keeps the shortcuts y = 1, y = 2 (now the rounded square), x = 2,
  x = 10; y ∈ {3, 4, ½, ¼, −1}, which floored, take the general path.
- The precision test measures the true distance to the real truth and holds
  each op to its rounding contract (v4: within 2 ULP of a floored reference).
- Gas through the object, ladder medians against v4: `exp` 6,058 (+145),
  `exp2` 3,714 (−2,048), `pow` 4,956 (−4,425), `cbrt` 4,545 (−5,404),
  `lambertW0` 24,690 (+3,752), `sqrt` 2,175 (−2,104), `mul` 1,103 (+99).
  The object dispatches by binary search on the selector, not a linear
  chain.
- A gas-only pass (`fp127-faster`), every result the same word, checked on
  the sweep, the vectors and dense extra sets. Sweep medians:
  - Lambert W uses Halley steps, as many as the seed needs: `lambertW0`
    46,170 → 18,607 and `lambertWm1` 35,250 → 23,977.
  - `pow` and `cbrt` try one word first: 14,807 → 6,121 and 14,935 → 6,019.
  - The erf loops run inline; erf's worst case falls from 66,655 to 36,440.
  - At tiny x, `expm1` 7,089 → 2,066, `sinh` 6,060 → 2,284 and `tanh`
    7,988 → 4,680.
  - `sqrt` 3,209 → 710 uses Solady's isqrt seed, keeping v4's word where it
    was not the floor.
  - `inv` 698 → 242, `div` 315 when |a| < 1, and the logs' fallback
    ~12,600 → ~9,760.
  - `exp2frac` runs inline throughout.

### FP256 release four

Correctly rounded, and the edge. Four objects, deployed 2026-10-21 at the
addresses in the table above.

- Every FP256 op is correctly rounded or exact: 0 misrounded of 364,658
  random inputs (281,821 before #79's ops), and 0 when every input is
  forced through the second stage (`docs/benchmarks/sweep.md`); release
  three had pow 8 in 20,000 off by one ULP, ln 1, normCdf 1 in 4,000,
  compound up to 4 ULP (291 of 3,853), lambertW0 up to 2 (668 of 2,000). Each fast value carries a stated error
  bound; when it reaches the rounding boundary a second stage recomputes the
  value in two words at 2^−510. pow, compound and powu compute exact ties
  exactly. The bounds are measured against the models in
  `scripts/fp256/generators/bounds.py`: none reaches 0.67 of its value.
- The edge, rounding toward minus or plus infinity once from the exact
  value: `mulDown`, `mulUp`, `divDown`, `divUp`, `toUintDown`, `toUintUp`,
  `toIntDown`, `toIntUp`, `toFixed18Down`, `toFixed18Up`, `floor`, `ceil`,
  `fromUintDown`, `fromUintUp`; a positive Up result never underflows to
  zero.
- Two objects from one source: FP256 (arithmetic, the edge, exp, ln, log1p,
  expm1, pow, powu, compound, conversions) and FP256X (erf, erfc, normCdf,
  lambertW0, lambertWm1), salts `FP256 v4` and `FP256X v4`; the inline
  library holds all of them. `make predict-fp256x`, `deploy-fp256x-sepolia`,
  `verify-fp256x-sepolia`.
- Gas: the fast paths cost a few hundred gas more; the second stage, when it
  runs, 29k (exp) to 430k (erfc's continued fraction). The optimisation
  pass (fp256-faster, results unchanged word for word): Lambert W by
  fourth-order steps at word precision with a stated bound and the rounding
  test, the wide step only on a miss, 34k / 30k at the median (W0 / W−1;
  151k / 156k before, 109k in release three); `wexpm1` 27k → 21k, so every
  second stage is about 6k cheaper; pow, powu and compound fallbacks
  shorter (p99 80k → 68k, 92k → 73k, 167k → 116k), the pow bound tighter,
  `wln1ps`'s length set by |d|.
- The ops FP127 has and FP256 lacked (#79), each correctly rounded or exact:
  `exp2`, `exp10`, `log2`, `log10`, `log2Up`, `cbrt`, `sinh`, `cosh`,
  `tanh`, `atanh` in FP256X2 (on the same kernels, each with a stated bound
  and a two-word second stage) and `min`, `max`, `clamp`, `avg`, `dist`,
  `zeroFloorSub`, `inv`, `lerp`, `frac`, `round`, `gcd`, `factorial`, `pi`,
  `gavg`, `hypot` in FP256X3 (exact values, or one rounding of an exact
  sum, product or root). `lerp` rounds a + t (b - a) once from the exact
  value, summed in a 1,024-bit window just past the free memory pointer;
  `hypot` rounds Pythagorean ties away from zero; `factorial` runs to 20,366
  and is checked against the exact factorial at every n; `pi(terms)` is the
  correctly rounded Ramanujan partial sum; `round` takes halves away from
  zero. Salts `FP256X2 v4` and `FP256X3 v4`; `make predict-fp256x2`,
  `-fp256x3` and their deploy and verify targets. 67 ops in all.

### Ladder v9

Salt `FP127 ladder v9`, deployed 2026-10-21: the eleven adapters, with
`LadderFP127` calling FP127 v5, `LadderFP127Lib` inlining it and
`LadderFP256` inlining release four, and both runners. The datasets and the
live runners now compute the same code again.

## Blockulator 2.0 (2026-10-16)

Two rulers in one word: FP127 for the money range, FP256 for everything.

| component | version | Sepolia |
|---|---|---|
| FP127 | FP127 v4, 49 ops | `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1` |
| FP256 | FP256 v3, 28 ops | `0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be` |
| LadderRunner | FP127 ladder v8 | `0xEf689d3782490066fE911a6dD33357f59caE40fE` |
| EdgeRunner | FP127 ladder v8 | `0x09b8fC41E872279A749a0221AE23D124079AcB44` |

- FP256, a 256-bit binary float: sign, 19-bit exponent, 236-bit fraction,
  about 71 digits from 10^−78,913 to 10^78,913, no NaN or infinity.
  Release three adds log1p, expm1, erf, erfc, normCdf, both Lambert branches,
  powu and compound; exp, ln, log1p, expm1 and the erf family return the
  correctly rounded word at every committed vector.
- FP127 v4: 49 ops, adding powu, compound, log1p, expm1, the hyperbolics,
  erf, erfc and normCdf.
- The ladder (13 scenarios × 10 libraries, N to 10,000) and the edges (139
  one-shot probes) re-run through the live runners with 0 mismatches: the
  9,373 ladder cells a public RPC can execute and all 1,511 edge cells that
  make a call.
- The site: four-item navigation, one results overview, one live-check
  stamp per page.

Records: `contracts/deployments/{FP127,FP256,Ladder}.md`.

## Blockulator 1.0

FP127 as a Huff contract (`0xfae694D0c2c44181791F838c54Ed64C3151FfE30`): 127.128 fixed point on Sepolia, the original
library this release replaces. Its address and the later FP127 versions
stay live and are listed in `contracts/deployments/FP127.md`.

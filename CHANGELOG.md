# Changelog

A release is the public name for a set of deployed contracts. Each contract
keeps its own version in its CREATE2 salt, because the salt names the address;
`contracts/deployments/RELEASE.json` maps the release to every address.

## Unreleased

FP127 v5: in source, not yet deployed (salt `FP127 v5`, 55 ops, 17,157
bytes of runtime). v4 stays live at `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1`.

- Every transcendental returns the nearest word. `exp`, `exp2`, `exp10`,
  `expm1`, `sinh`, `cosh`, `tanh`, `pow` and `cbrt` round once from a
  double-word kernel good to about 2^−300; `ln`, `log2`, `log10` and `log1p`
  fall back to a double-word log within 2^−145 of a midpoint; `powu` and
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
- Gas through the object, medians: `exp` 7,076 (+1,544), `exp2` 4,664
  (−696), `pow` 5,742 (−352), `cbrt` 7,270 (+551), `lambertW0` 41,481
  (+5,242), `lambertWm1` 31,764 (+2,402), `atanh` 7,646 (−1,055); six more
  selectors add about 90 to the other ops' dispatch.

FP256 release four, not yet deployed: correctly rounded, and the edge.

| component | version | Sepolia |
|---|---|---|
| FP256 | FP256 v4, 37 ops, 24,512 bytes | not yet deployed |
| FP256X | FP256X v4, 5 ops, 22,266 bytes | not yet deployed |
| FP256X2 | FP256X2 v4, 10 ops, 19,889 bytes | not yet deployed |
| FP256X3 | FP256X3 v4, 15 ops, 6,844 bytes | not yet deployed |

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

## Blockulator 2.0 (2026-10-16)

Two rulers in one word: FP127 for the money range, FP256 for everything.

| component | version | Sepolia |
|---|---|---|
| FP127 | FP127 v4, 49 ops | `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1` |
| FP256 | FP256 v3, 28 ops | `0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be` |
| LadderRunner | FP127 ladder v8 | `0xEf689d3782490066fE911a6dD33357f59caE40fE` |
| EdgeRunner | FP127 ladder v8 | `0x09b8fC41E872279A749a0221AE23D124079AcB44` |

- FP256, a 256-bit binary float: sign, 19-bit exponent, 236-bit fraction,
  about 71 digits from 10^−78,900 to 10^78,900, no NaN or infinity.
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

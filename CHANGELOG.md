# Changelog

A release is the public name for a set of deployed contracts. Each contract
keeps its own version in its CREATE2 salt, because the salt names the address;
`contracts/deployments/RELEASE.json` maps the release to every address.

## Unreleased

FP256 release four, not yet deployed: correctly rounded, and the edge.

| component | version | Sepolia |
|---|---|---|
| FP256 | FP256 v4, 37 ops, 24,250 bytes | not yet deployed |
| FP256X | FP256X v4, 5 ops, 23,891 bytes | not yet deployed |

- Every FP256 op is correctly rounded or exact: 0 misrounded of 281,821
  random inputs, and 0 when every input is forced through the second stage
  (`docs/benchmarks/sweep.md`); release three had pow 8 in 20,000 off by
  one ULP, ln 1, normCdf 1 in 4,000, compound up to 4 ULP (291 of 3,853),
  lambertW0 up to 2 (668 of 2,000). Each fast value carries a stated error
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
  library holds all 42. `make predict-fp256x`, `deploy-fp256x-sepolia`,
  `verify-fp256x-sepolia`.
- Gas: the fast paths cost a few hundred gas more; the second stage, when it
  runs, 36k (exp) to 436k (erfc's continued fraction); Lambert W always
  takes one wide step, 152k at the median (109k before).

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

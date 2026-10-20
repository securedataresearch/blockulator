# Changelog

A release is the public name for a set of deployed contracts. Each contract
keeps its own version in its CREATE2 salt, because the salt names the address;
`contracts/deployments/RELEASE.json` maps the release to every address.

## Unreleased

FP127 v5: in source, not yet deployed (salt `FP127 v5`, 55 ops, 17,066
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
  (−696), `pow` 5,742 (−352), `cbrt` 7,270 (+551), `lambertW0` 40,777
  (+4,538), `lambertWm1` 29,952 (+590), `atanh` 7,042 (−1,659); six more
  selectors add about 90 to the other ops' dispatch.

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

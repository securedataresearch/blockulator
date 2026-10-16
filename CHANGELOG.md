# Changelog

A release is the public name for a set of deployed contracts. Each contract
keeps its own version in its CREATE2 salt, because the salt names the address;
`contracts/deployments/RELEASE.json` maps the release to every address.

## Blockulator 2.0 (2026-10-16)

Two rulers in one word: FP127 for the money range, FP256 for everything.

| component | version | Sepolia |
|---|---|---|
| FP127 | FP127 v4, 49 ops | `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1` |
| FP256 | FP256 v3, 28 ops | `0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be` |
| LadderRunner | FP127 ladder v8 | `0xEf689d3782490066fE911a6dD33357f59caE40fE` |
| EdgeRunner | FP127 ladder v8 | `0x09b8fC41E872279A749a0221AE23D124079AcB44` |

- FP256, a 256-bit binary float: sign, 19-bit exponent, 236-bit fraction,
  about 71 digits from 10^−78,900 to 10^78,900, no NaN, infinity or walls.
  Release three adds log1p, expm1, erf, erfc, normCdf, both Lambert branches,
  powu and compound; exp, ln, log1p, expm1 and the erf family return the
  correctly rounded word at every committed vector.
- FP127 v4: 49 ops, adding powu, compound, log1p, expm1, the hyperbolics,
  erf, erfc and normCdf.
- The ladder (13 scenarios × 11 libraries, N to 10,000) and the edges (139
  one-shot probes) re-run every cell through the live runners.
- The site: four-item navigation, one results overview, one live-check
  stamp per page.

Records: `contracts/deployments/{FP127,FP256,Ladder}.md`.

## Blockulator 1.0

FP127 as a Huff contract (`0xfae694D0c2c44181791F838c54Ed64C3151FfE30`): 127.128 fixed point on Sepolia, the original
library this release replaces. Its address and the later FP127 versions
stay live and are listed in `contracts/deployments/FP127.md`.

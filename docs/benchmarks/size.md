# Inline size

Generated 2026-10-28 by `make size-inline` ([`scripts/size/inline.py`](../../scripts/size/inline.py)); the data is [`size.json`](size.json).

The runtime bytecode one op adds to a contract that calls it through `FP127Lib` or `FP19Lib`, helpers included. Each op is compiled alone in a contract with one external function `f(int256,int256,int256)` returning `Lib.op(a[, b[, c]])`; the delta is against the same contract returning `a`, so the ABI decoder and dispatch cancel. solc 0.8.38, evm osaka, optimizer 200 runs, CBOR metadata off. **legacy** is the repo's default profile (`via_ir = false`); **via_ir** is the same settings through the IR. Baseline contract: 118 bytes legacy, 63 via_ir.

## Headline

| library | ops | smallest | median | largest | all ops, sum of singles |
|---|---:|---|---:|---|---:|
| FP127 legacy | 53 | `sign` 8 | 480 | `compound` 16,930 | 184,361 |
| FP127 via_ir | 53 | `sign` 10 | 321 | `compound` 16,473 | 175,563 |
| FP19 legacy | 65 | `abs` 108 | 544 | `normCdf` 17,159 | 225,807 |
| FP19 via_ir | 65 | `abs` 55 | 443 | `normCdf` 17,344 | 209,090 |

## Shared helpers

Every `FP*Lib` function is one self-contained `assembly` block that carries its own copy of each helper it uses (`expk`, `divw`, `log2m` and the rest), so the single-op number is what the first op costs. Both pipelines merge identical code across blocks (the legacy block deduplicator, the IR's function combiner), so a second op that shares a kernel with the first adds less than its own row. Each bundle below is one contract that chains the ops, against the sum of their single-op rows.

| library | ops | legacy | sum of singles | via_ir | sum of singles |
|---|---|---:|---:|---:|---:|
| FP127 | `mul`, `div` | 582 | 599 | 372 | 389 |
| FP127 | `mulDown`, `mulUp`, `divDown`, `divUp` | 914 | 1,368 | 592 | 900 |
| FP127 | `exp`, `ln` | 9,765 | 14,399 | 9,116 | 13,178 |
| FP127 | `exp`, `ln`, `pow` | 16,995 | 29,626 | 16,458 | 27,963 |
| FP127 | `exp`, `log2`, `sqrt` | 9,816 | 14,489 | 9,095 | 13,178 |
| FP127 | `erf`, `erfc`, `normCdf` | 5,815 | 16,377 | 11,394 | 16,217 |
| FP127 | `fromFixed18`, `toFixed18Down`, `toFixed18Up`, `mulDown`, `mulUp`, `compound` | 17,447 | 17,556 | 16,804 | 16,845 |
| FP19 | `add`, `sub`, `mul`, `div` | 1,113 | 2,046 | 1,031 | 1,661 |
| FP19 | `exp`, `ln` | 11,852 | 12,764 | 10,340 | 10,833 |
| FP19 | `exp`, `ln`, `pow` | 17,208 | 27,561 | 15,726 | 23,842 |
| FP19 | `erf`, `erfc`, `normCdf` | 20,175 | 51,296 | 19,495 | 51,393 |
| FP19 | `fromFixed18`, `toFixed18Down`, `toFixed18Up`, `mulDown`, `mulUp`, `compound` | 14,893 | 15,992 | 14,512 | 15,044 |

## Inline or call the deployed object

Inlining saves the external call: about 579 gas per call to the deployed FP127 and 464 to FP19 ([`gas.json`](gas.json), [`gas19.json`](gas19.json): `add`, object median minus inline median). `staticcall` the deployed object instead (for FP19, whichever of FP19, FP19E, FP19H, FP19N and FP19S holds the op) when inlining would take the contract near the 24,576-byte limit (EIP-170), or when the op is large and called rarely. Deploying code costs at least 200 gas a byte, so inlining an op of N bytes pays for itself only after about 200N / 579 calls: a small op at once, `pow` after thousands. The deployed objects already hold every op, so calling one adds only the call site.

## FP127

| op | legacy | via_ir |
|---|---:|---:|
| `fromFixed18` | 86 | 41 |
| `toFixed18` | 54 | 39 |
| `toFixed18Down` | 77 | 39 |
| `toFixed18Up` | 92 | 62 |
| `add` | 75 | 33 |
| `sub` | 75 | 33 |
| `mul` | 119 | 68 |
| `div` | 480 | 321 |
| `mulDown` | 128 | 68 |
| `mulUp` | 243 | 162 |
| `divDown` | 498 | 333 |
| `divUp` | 499 | 337 |
| `exp2` | 5,637 | 5,137 |
| `exp` | 5,794 | 5,173 |
| `exp10` | 5,825 | 5,360 |
| `log2` | 8,337 | 7,733 |
| `ln` | 8,605 | 8,005 |
| `log10` | 8,605 | 8,267 |
| `log2Up` | 106 | 56 |
| `sqrt` | 358 | 272 |
| `pow` | 15,227 | 14,785 |
| `powu` | 16,406 | 15,992 |
| `compound` | 16,930 | 16,473 |
| `cbrt` | 600 | 472 |
| `gavg` | 566 | 483 |
| `hypot` | 549 | 457 |
| `inv` | 135 | 84 |
| `abs` | 74 | 34 |
| `neg` | 70 | 28 |
| `sign` | 8 | 10 |
| `min` | 51 | 15 |
| `max` | 51 | 15 |
| `clamp` | 76 | 33 |
| `avg` | 46 | 20 |
| `zeroFloorSub` | 101 | 45 |
| `dist` | 122 | 51 |
| `lerp` | 219 | 100 |
| `floor` | 17 | 19 |
| `ceil` | 90 | 46 |
| `frac` | 16 | 18 |
| `round` | 103 | 48 |
| `factorial` | 864 | 690 |
| `lambertW0` | 12,374 | 11,698 |
| `lambertWm1` | 12,050 | 11,399 |
| `log1p` | 8,692 | 8,065 |
| `expm1` | 6,207 | 6,143 |
| `sinh` | 6,392 | 5,709 |
| `cosh` | 6,382 | 5,694 |
| `tanh` | 6,715 | 6,962 |
| `atanh` | 11,158 | 12,219 |
| `erf` | 5,456 | 5,364 |
| `erfc` | 5,431 | 5,371 |
| `normCdf` | 5,490 | 5,482 |

## FP19

| op | legacy | via_ir |
|---|---:|---:|
| `add` | 632 | 508 |
| `sub` | 633 | 511 |
| `mul` | 337 | 276 |
| `div` | 444 | 366 |
| `sqrt` | 531 | 443 |
| `exp` | 6,232 | 5,823 |
| `ln` | 6,532 | 5,010 |
| `pow` | 14,797 | 13,009 |
| `log1p` | 6,329 | 6,349 |
| `expm1` | 7,802 | 8,000 |
| `erf` | 17,031 | 16,910 |
| `erfc` | 17,106 | 17,139 |
| `normCdf` | 17,159 | 17,344 |
| `lambertW0` | 10,740 | 10,026 |
| `lambertWm1` | 10,474 | 10,183 |
| `powu` | 15,557 | 13,796 |
| `compound` | 13,873 | 13,347 |
| `neg` | 108 | 56 |
| `abs` | 108 | 55 |
| `sign` | 116 | 64 |
| `cmp` | 178 | 106 |
| `lt` | 173 | 100 |
| `eq` | 129 | 82 |
| `fromUint` | 234 | 141 |
| `fromFP127` | 244 | 158 |
| `toFP127` | 313 | 249 |
| `fromFixed18` | 325 | 272 |
| `toFixed18` | 351 | 260 |
| `mulDown` | 449 | 364 |
| `mulUp` | 450 | 366 |
| `divDown` | 544 | 443 |
| `divUp` | 545 | 446 |
| `toUintDown` | 284 | 159 |
| `toUintUp` | 285 | 186 |
| `toIntDown` | 304 | 238 |
| `toIntUp` | 305 | 247 |
| `floor` | 376 | 303 |
| `ceil` | 377 | 310 |
| `toFixed18Down` | 447 | 344 |
| `toFixed18Up` | 448 | 351 |
| `fromUintDown` | 302 | 132 |
| `fromUintUp` | 303 | 225 |
| `min` | 184 | 113 |
| `max` | 184 | 113 |
| `clamp` | 242 | 163 |
| `avg` | 633 | 515 |
| `dist` | 660 | 520 |
| `zeroFloorSub` | 663 | 527 |
| `inv` | 401 | 294 |
| `lerp` | 2,741 | 2,684 |
| `frac` | 980 | 877 |
| `round` | 343 | 285 |
| `log2Up` | 381 | 293 |
| `factorial` | 8,211 | 6,912 |
| `cbrt` | 960 | 849 |
| `gavg` | 713 | 575 |
| `hypot` | 978 | 751 |
| `exp2` | 5,825 | 5,420 |
| `exp10` | 5,846 | 5,568 |
| `log2` | 6,741 | 5,129 |
| `log10` | 6,742 | 5,398 |
| `sinh` | 8,007 | 7,606 |
| `cosh` | 6,322 | 5,830 |
| `tanh` | 8,082 | 7,814 |
| `atanh` | 6,061 | 6,157 |

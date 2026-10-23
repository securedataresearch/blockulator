# Inline size

Generated 2026-10-23 by `make size-inline` ([`scripts/size/inline.py`](../../scripts/size/inline.py)); the data is [`size.json`](size.json).

The runtime bytecode one op adds to a contract that calls it through `FP127Lib` or `FP256Lib`, helpers included. Each op is compiled alone in a contract with one external function `f(int256,int256,int256)` returning `Lib.op(a[, b[, c]])`; the delta is against the same contract returning `a`, so the ABI decoder and dispatch cancel. solc 0.8.38, evm osaka, optimizer 200 runs, CBOR metadata off. **legacy** is the repo's default profile (`via_ir = false`); **via_ir** is the same settings through the IR. Baseline contract: 118 bytes legacy, 63 via_ir.

## Headline

| library | ops | smallest | median | largest | all ops, sum of singles |
|---|---:|---|---:|---|---:|
| FP127 legacy | 53 | `sign` 8 | 480 | `pow` 10,153 | 111,514 |
| FP127 via_ir | 53 | `sign` 10 | 321 | `pow` 9,604 | 102,062 |
| FP256 legacy | 65 | `abs` 108 | 544 | `powu` 13,272 | 197,199 |
| FP256 via_ir | 65 | `abs` 55 | 443 | `normCdf` 12,843 | 183,316 |

## Shared helpers

Every `FP*Lib` function is one self-contained `assembly` block that carries its own copy of each helper it uses (`expk`, `divw`, `log2m` and the rest), so the single-op number is what the first op costs. Both pipelines merge identical code across blocks (the legacy block deduplicator, the IR's function combiner), so a second op that shares a kernel with the first adds less than its own row. Each bundle below is one contract that chains the ops, against the sum of their single-op rows.

| library | ops | legacy | sum of singles | via_ir | sum of singles |
|---|---|---:|---:|---:|---:|
| FP127 | `mul`, `div` | 582 | 599 | 372 | 389 |
| FP127 | `mulDown`, `mulUp`, `divDown`, `divUp` | 805 | 1,336 | 526 | 856 |
| FP127 | `exp`, `ln` | 7,768 | 11,868 | 7,222 | 10,975 |
| FP127 | `exp`, `ln`, `pow` | 10,925 | 22,021 | 10,404 | 20,579 |
| FP127 | `exp`, `log2`, `sqrt` | 8,250 | 12,427 | 7,610 | 11,383 |
| FP127 | `erf`, `erfc`, `normCdf` | 4,188 | 9,828 | 4,568 | 9,759 |
| FP127 | `fromFixed18`, `toFixed18Down`, `toFixed18Up`, `mulDown`, `mulUp`, `compound` | 1,684 | 1,862 | 1,434 | 1,501 |
| FP256 | `add`, `sub`, `mul`, `div` | 1,113 | 2,046 | 1,031 | 1,661 |
| FP256 | `exp`, `ln` | 11,838 | 12,750 | 10,340 | 10,833 |
| FP256 | `exp`, `ln`, `pow` | 14,918 | 25,262 | 13,690 | 21,810 |
| FP256 | `erf`, `erfc`, `normCdf` | 16,431 | 36,986 | 15,176 | 37,890 |
| FP256 | `fromFixed18`, `toFixed18Down`, `toFixed18Up`, `mulDown`, `mulUp`, `compound` | 12,755 | 13,854 | 12,894 | 13,203 |

## Inline or call the deployed object

Inlining saves the external call: about 570 gas per call to the deployed FP127 and 464 to FP256 ([`gas.json`](gas.json), [`gas256.json`](gas256.json): `add`, object median minus inline median). `staticcall` the deployed object instead (for FP256, whichever of FP256, FP256E, FP256H and FP256S holds the op) when inlining would take the contract near the 24,576-byte limit (EIP-170), or when the op is large and called rarely. Deploying code costs at least 200 gas a byte, so inlining an op of N bytes pays for itself only after about 200N / 570 calls: a small op at once, `pow` after thousands. The deployed objects already hold every op, so calling one adds only the call site.

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
| `mulUp` | 211 | 118 |
| `divDown` | 498 | 333 |
| `divUp` | 499 | 337 |
| `exp2` | 4,333 | 3,943 |
| `exp` | 4,533 | 4,157 |
| `exp10` | 4,484 | 4,141 |
| `log2` | 7,141 | 6,571 |
| `ln` | 7,335 | 6,818 |
| `log10` | 7,335 | 6,818 |
| `log2Up` | 106 | 56 |
| `sqrt` | 753 | 655 |
| `pow` | 10,153 | 9,604 |
| `powu` | 1,212 | 1,151 |
| `compound` | 1,268 | 1,173 |
| `cbrt` | 600 | 472 |
| `gavg` | 852 | 726 |
| `hypot` | 903 | 761 |
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
| `factorial` | 118 | 62 |
| `lambertW0` | 8,427 | 7,807 |
| `lambertWm1` | 8,112 | 7,527 |
| `log1p` | 7,422 | 6,878 |
| `expm1` | 5,090 | 4,651 |
| `sinh` | 4,898 | 4,400 |
| `cosh` | 4,888 | 4,394 |
| `tanh` | 5,183 | 4,769 |
| `atanh` | 2,967 | 2,711 |
| `erf` | 3,270 | 3,210 |
| `erfc` | 3,245 | 3,219 |
| `normCdf` | 3,313 | 3,330 |

## FP256

| op | legacy | via_ir |
|---|---:|---:|
| `add` | 632 | 508 |
| `sub` | 633 | 511 |
| `mul` | 337 | 276 |
| `div` | 444 | 366 |
| `sqrt` | 531 | 443 |
| `exp` | 6,232 | 5,823 |
| `ln` | 6,518 | 5,010 |
| `pow` | 12,512 | 10,977 |
| `log1p` | 6,315 | 6,349 |
| `expm1` | 7,802 | 8,000 |
| `erf` | 12,261 | 12,409 |
| `erfc` | 12,336 | 12,638 |
| `normCdf` | 12,389 | 12,843 |
| `lambertW0` | 10,726 | 10,026 |
| `lambertWm1` | 10,460 | 10,183 |
| `powu` | 13,272 | 11,752 |
| `compound` | 11,735 | 11,506 |
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
| `factorial` | 777 | 558 |
| `cbrt` | 960 | 849 |
| `gavg` | 713 | 575 |
| `hypot` | 978 | 751 |
| `exp2` | 5,825 | 5,420 |
| `exp10` | 5,846 | 5,568 |
| `log2` | 6,669 | 5,129 |
| `log10` | 6,728 | 5,398 |
| `sinh` | 8,007 | 7,606 |
| `cosh` | 6,322 | 5,830 |
| `tanh` | 8,082 | 7,814 |
| `atanh` | 6,047 | 6,157 |

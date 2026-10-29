# FP19 gas ladder

Generated 2026-10-28 by `make bench`. Versions: fp127 6c2eeaf, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), fraxlend fraxlend@2bed49d4dcc6 (VariableInterestRate V2, transcribed), euler evk-periphery@af436991e135 (IRMAdaptiveCurve, ExpLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, solmate solmate@89365b8 (no tag: v6 predates SignedWadMath), openzeppelin openzeppelin-contracts v5.7.0 (Math, SignedMath, vendored), uniswap v4-core v4.0.0 (FullMath, vendored), snekmate v0.1.2 (math module, vyper 0.4.3), forge forge Version: 1.7.1.

Each cell is min / median / max gas over the op's input ladder. The object column includes the `staticcall` (and the object's own selector dispatch); the inline columns are the internal library call alone, timed inside the harness's entry point with the dispatch outside the window (the same cost for every op, whatever its place in the harness's list). An empty cell means the library does not offer the op; `rev` means it does, but reverted (or the input was outside its domain or format) on every ladder input. What each library cell calls is listed at the end; [coverage.md](coverage.md) maps every function of every comparison library.

| op | Yul object (staticcall) | FP19Lib (inline) | FP127Lib (inline), the same op | ABDKMathQuad |
|---|---:|---:|---:|---:|
| abs | 724 / 727 / 743 | 133 / 133 / 133 | 152 / 152 / 152 | 21 / 21 / 21 |
| add | 1,119 / 1,126 / 1,167 | 662 / 662 / 681 | 128 / 128 / 128 | 460 / 734 / 765 |
| atanh | 3,430 / 5,037 / 5,058 | 3,406 / 5,150 / 5,206 | 2,904 / 2,941 / 2,968 |  |
| avg | 1,115 / 1,116 / 1,156 | 663 / 663 / 682 | 114 / 114 / 114 |  |
| cbrt | 3,039 / 3,086 / 3,111 | 2,734 / 2,760 / 2,773 | 1,944 / 1,944 / 1,944 |  |
| ceil | 960 / 1,131 / 1,246 | 336 / 523 / 571 | 147 / 147 / 147 |  |
| clamp | 1,128 / 1,134 / 1,178 | 491 / 491 / 492 | 241 / 241 / 242 |  |
| cmp | 801 / 803 / 805 | 248 / 248 / 248 |  | 346 / 476 / 489 |
| compound | 5,483 / 5,695 / 6,051 | 5,867 / 6,197 / 6,661 | 2,263 / 3,271 / 8,455 |  |
| cosh | 3,424 / 3,511 / 3,539 | 3,465 / 3,671 / 3,692 | 3,953 / 4,054 / 4,104 |  |
| dist | 1,042 / 1,230 / 1,324 | 607 / 819 / 928 | 289 / 289 / 289 |  |
| div | 1,354 / 1,370 / 1,374 | 800 / 800 / 800 | 412 / 412 / 412 | 818 / 818 / 818 |
| divDown | 1,440 / 1,464 / 1,493 | 987 / 987 / 987 | 475 / 475 / 475 |  |
| divUp | 1,479 / 1,531 / 1,577 | 988 / 988 / 1,034 | 478 / 478 / 478 |  |
| eq | 798 / 830 / 836 | 176 / 176 / 176 |  | 108 / 108 / 147 |
| erf | 5,622 / 9,690 / 12,649 | 6,159 / 10,607 / 13,599 | 3,187 / 7,803 / 16,399 |  |
| erfc | 9,723 / 9,755 / 12,791 | 10,498 / 10,653 / 13,687 | 250 / 7,785 / 16,405 |  |
| exp | 3,340 / 3,368 / 3,421 | 3,268 / 3,295 / 3,328 | 2,835 / 2,845 / 2,895 | 979 / 5,766 / 5,959 |
| exp10 | 3,193 / 3,216 / 3,255 | 3,153 / 3,180 / 3,274 | 3,065 / 3,081 / 3,086 |  |
| exp2 | 1,859 / 3,187 / 3,274 | 1,541 / 3,107 / 3,186 | 2,593 / 2,699 / 2,734 | 404 / 4,536 / 5,920 |
| expm1 | 2,734 / 3,038 / 3,455 | 2,375 / 2,749 / 3,382 | 1,560 / 2,960 / 4,488 |  |
| factorial | 1,013 / 1,217 / 1,223 | 392 / 719 / 762 | 399 / 400 / 422 |  |
| floor | 928 / 1,130 / 1,134 | 309 / 522 / 522 | 72 / 72 / 72 |  |
| frac | 834 / 1,050 / 1,960 | 187 / 428 / 1,419 | 69 / 69 / 69 |  |
| fromFP127 | 946 / 949 / 962 | 440 / 440 / 440 |  | 495 / 539 / 623 |
| fromFixed18 | 1,145 / 1,148 / 1,151 | 554 / 554 / 554 | 140 / 140 / 140 |  |
| fromUint | 934 / 937 / 940 | 413 / 413 / 413 |  |  |
| fromUintDown | 910 / 912 / 939 | 487 / 487 / 487 |  | 435 / 500 / 558 |
| fromUintUp | 995 / 999 / 1,048 | 488 / 488 / 534 |  |  |
| gavg | 2,267 / 2,297 / 2,323 | 1,864 / 1,864 / 1,878 | 706 / 1,003 / 1,003 |  |
| hypot | 1,162 / 3,286 / 3,524 | 595 / 3,329 / 3,668 | 867 / 1,164 / 1,164 |  |
| inv | 1,247 / 1,249 / 1,253 | 747 / 747 / 747 | 242 / 242 / 242 | 1,253 / 1,253 / 1,295 |
| lambertW0 | 9,149 / 9,554 / 27,305 | 10,005 / 10,597 / 32,217 | 328 / 8,183 / 11,264 |  |
| lambertWm1 | 8,005 / 9,521 / 28,009 | 8,754 / 10,571 / 33,141 | 8,025 / 8,844 / 11,326 |  |
| lerp | 1,220 / 6,403 / 6,824 | 546 / 5,884 / 6,782 | 477 / 477 / 477 |  |
| ln | 803 / 3,259 / 4,155 | 274 / 3,069 / 4,123 | 139 / 590 / 1,944 | 555 / 1,564 / 16,850 |
| log10 | 809 / 3,271 / 4,177 | 270 / 3,058 / 4,112 | 139 / 590 / 1,944 |  |
| log1p | 2,825 / 3,036 / 3,563 | 2,571 / 2,829 / 3,508 | 2,033 / 2,049 / 2,127 |  |
| log2 | 818 / 3,140 / 4,043 | 270 / 2,843 / 3,897 | 374 / 374 / 1,728 | 128 / 852 / 16,096 |
| log2Up | 912 / 1,169 / 1,190 | 340 / 679 / 693 | 209 / 209 / 209 |  |
| lt | 794 / 818 / 826 | 233 / 233 / 233 |  | 358 / 488 / 501 |
| max | 821 / 827 / 829 | 250 / 250 / 251 | 113 / 113 / 114 |  |
| min | 831 / 837 / 844 | 250 / 251 / 251 | 113 / 114 / 114 |  |
| mul | 1,058 / 1,063 / 1,071 | 530 / 530 / 530 | 255 / 255 / 255 | 667 / 709 / 709 |
| mulDown | 1,208 / 1,244 / 1,251 | 727 / 727 / 727 | 315 / 315 / 315 |  |
| mulUp | 1,220 / 1,243 / 1,268 | 728 / 728 / 774 | 337 / 337 / 386 |  |
| neg | 711 / 715 / 725 | 127 / 127 / 127 | 116 / 116 / 116 | 9 / 9 / 9 |
| normCdf | 9,938 / 10,036 / 19,471 | 10,772 / 11,174 / 21,847 | 236 / 7,056 / 8,474 |  |
| pow | 1,416 / 5,469 / 6,448 | 990 / 5,604 / 6,823 | 502 / 2,856 / 3,344 | 1,581 / 23,087 / 23,325 |
| powu | 2,213 / 5,329 / 7,189 | 1,701 / 5,305 / 7,435 | 1,314 / 4,030 / 10,504 |  |
| round | 864 / 1,100 / 1,160 | 226 / 474 / 522 | 212 / 212 / 212 |  |
| sign | 761 / 764 / 768 | 139 / 139 / 139 | 75 / 75 / 75 | 181 / 181 / 181 |
| sinh | 3,173 / 3,507 / 3,510 | 3,053 / 3,660 / 3,697 | 4,001 / 4,102 / 4,152 |  |
| sqrt | 1,665 / 1,684 / 1,705 | 1,201 / 1,205 / 1,209 | 469 / 816 / 816 | 760 / 760 / 760 |
| sub | 1,017 / 1,190 / 1,298 | 533 / 745 / 854 | 128 / 128 / 128 | 726 / 1,230 / 1,325 |
| tanh | 1,297 / 3,571 / 3,598 | 1,027 / 3,709 / 3,723 | 247 / 3,945 / 3,976 |  |
| toFP127 | 911 / 914 / 918 | 343 / 343 / 343 |  | 278 / 292 / 292 |
| toFixed18 | 974 / 1,030 / 1,033 | 440 / 480 / 480 | 121 / 121 / 121 |  |
| toFixed18Down | 1,278 / 1,309 / 1,313 | 718 / 723 / 723 | 160 / 160 / 160 |  |
| toFixed18Up | 1,321 / 1,335 / 1,388 | 724 / 724 / 738 | 185 / 185 / 190 |  |
| toIntDown | 918 / 1,077 / 1,080 | 330 / 466 / 466 |  | 109 / 278 / 293 |
| toIntUp | 956 / 1,124 / 1,186 | 331 / 467 / 481 |  |  |
| toUintDown | 814 / 871 / 875 | 286 / 405 / 405 |  | 83 / 240 / 254 |
| toUintUp | 824 / 937 / 984 | 287 / 406 / 420 |  |  |
| zeroFloorSub | 1,127 / 1,294 / 1,432 | 617 / 829 / 938 | 212 / 212 / 215 |  |

## Typical inputs

The ladder sits mostly on integers, powers of two and one, where several ops take a shortcut. These rows are the same forms on random inputs drawn per op from `keccak256("typical", op, i)`: non-integer, not a power of two, across the op's usual range (`test_ladder_typical`). Min / median / max over the inputs.

| op | Yul object (staticcall) | FP19Lib (inline) | FP127Lib (inline), the same op | ABDKMathQuad |
|---|---:|---:|---:|---:|
| atanh | 3,588 / 4,016 / 5,203 | 3,411 / 3,882 / 5,227 | 2,904 / 2,941 / 2,969 |  |
| cbrt | 3,165 / 3,196 / 3,319 | 2,734 / 2,734 / 2,773 | 101 / 1,022 / 1,948 |  |
| compound | 5,578 / 5,611 / 5,826 | 5,856 / 5,858 / 5,943 | 2,221 / 3,078 / 3,078 |  |
| cosh | 3,641 / 3,674 / 3,775 | 3,682 / 3,692 / 3,703 | 4,017 / 4,059 / 4,118 |  |
| erf | 9,101 / 9,676 / 10,119 | 9,890 / 10,624 / 10,948 | 4,804 / 8,427 / 18,468 |  |
| erfc | 9,713 / 9,759 / 15,041 | 10,509 / 10,654 / 16,090 | 250 / 7,586 / 8,799 |  |
| exp | 3,266 / 3,317 / 3,408 | 3,127 / 3,278 / 3,338 | 2,788 / 2,824 / 2,851 | 5,570 / 5,668 / 5,973 |
| exp10 | 3,310 / 3,349 / 3,422 | 3,139 / 3,177 / 3,257 | 3,055 / 3,077 / 3,106 |  |
| exp2 | 3,282 / 3,299 / 3,444 | 2,939 / 3,096 / 3,158 | 2,673 / 2,697 / 2,714 | 4,788 / 5,031 / 5,219 |
| expm1 | 2,760 / 2,785 / 3,486 | 2,384 / 2,395 / 3,419 | 2,072 / 2,960 / 3,797 |  |
| gavg | 2,384 / 2,569 / 2,735 | 1,870 / 2,099 / 2,334 | 706 / 1,003 / 1,003 |  |
| hypot | 3,299 / 3,559 / 3,783 | 3,275 / 3,556 / 3,615 | 867 / 1,164 / 1,164 |  |
| lambertW0 | 7,974 / 9,591 / 9,968 | 8,685 / 10,672 / 11,048 | 6,582 / 8,264 / 8,420 |  |
| lambertWm1 | 9,373 / 9,788 / 10,004 | 10,298 / 10,759 / 10,993 | 8,064 / 8,159 / 8,313 |  |
| lerp | 6,615 / 6,890 / 7,011 | 5,893 / 6,515 / 6,520 | 477 / 477 / 477 |  |
| ln | 3,258 / 3,283 / 3,292 | 3,056 / 3,106 / 3,132 | 1,878 / 1,934 / 1,954 | 16,265 / 16,356 / 16,570 |
| log10 | 3,397 / 3,426 / 4,310 | 3,076 / 3,101 / 4,186 | 1,909 / 1,923 / 1,954 |  |
| log1p | 2,809 / 2,846 / 3,515 | 2,576 / 2,587 / 3,482 | 2,033 / 2,033 / 2,097 |  |
| log2 | 3,245 / 3,262 / 3,328 | 2,865 / 2,885 / 2,906 | 1,697 / 1,728 / 1,738 | 15,536 / 15,553 / 16,113 |
| normCdf | 10,063 / 11,442 / 13,834 | 11,043 / 12,354 / 14,726 | 5,420 / 6,316 / 15,867 |  |
| pow | 5,807 / 5,994 / 6,815 | 5,821 / 5,964 / 7,057 | 3,277 / 3,410 / 3,431 | 23,384 / 23,479 / 23,563 |
| powu | 2,505 / 6,694 / 8,754 | 1,738 / 6,647 / 8,761 | 1,340 / 5,252 / 10,488 |  |
| sinh | 3,588 / 3,640 / 3,727 | 3,565 / 3,670 / 3,708 | 4,055 / 4,096 / 4,166 |  |
| sqrt | 1,667 / 1,685 / 1,702 | 1,201 / 1,205 / 1,209 | 126 / 297 / 816 | 760 / 760 / 760 |
| tanh | 3,689 / 3,740 / 3,781 | 3,591 / 3,717 / 3,733 | 3,956 / 3,967 / 6,183 |  |

## What each cell calls

The competitor function behind each cell, on the inputs converted once to its representation. "composed" is built from the library's own functions where it has none of that name; a note in parentheses is the domain the harness keeps to (other inputs count as `rev`) or a rounding difference.

| op | ABDKMathQuad |
|---|---|
| abs | `abs(x)` |
| add | `add(a, b)` |
| cmp | `cmp(a, b)` |
| div | `div(a, b)` |
| eq | `eq(a, b)` |
| exp | `exp(x)` |
| exp2 | `pow_2(x)` |
| fromFP127 | `from128x128(x) (truncates; fromFP127 rounds to nearest)` |
| fromUintDown | `fromUInt(x) (truncates the significand)` |
| inv | `div(fromUInt(1), x) (composed)` |
| ln | `ln(x)` |
| log2 | `log_2(x)` |
| lt | `cmp(a, b) < 0 (composed)` |
| mul | `mul(a, b)` |
| neg | `neg(x)` |
| pow | `exp(mul(y, ln(x))) (composed)` |
| sign | `sign(x)` |
| sqrt | `sqrt(x)` |
| sub | `sub(a, b)` |
| toFP127 | `to128x128(x) (truncates; toFP127 rounds to nearest)` |
| toIntDown | `toInt(x) (truncates: floor for x >= 0, the rows kept)` |
| toUintDown | `toUInt(x) (truncates: floor for x >= 0)` |

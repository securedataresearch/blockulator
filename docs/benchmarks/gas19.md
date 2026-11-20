# BL19 gas ladder

Generated 2026-11-19 by `make bench`. Versions: bl127 5d0ff94, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), fraxlend fraxlend@2bed49d4dcc6 (VariableInterestRate V2, transcribed), euler evk-periphery@af436991e135 (IRMAdaptiveCurve, ExpLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, solmate solmate@89365b8 (no tag: v6 predates SignedWadMath), openzeppelin openzeppelin-contracts v5.7.0 (Math, SignedMath, vendored), uniswap v4-core v4.0.0 (FullMath, vendored), snekmate v0.1.2 (math module, vyper 0.4.3), forge forge Version: 1.7.1.

Each cell is min / median / max gas over the op's input ladder. The object column includes the `staticcall` (and the object's own selector dispatch); the inline columns are the internal library call alone, timed inside the harness's entry point with the dispatch outside the window (the same cost for every op, whatever its place in the harness's list). An empty cell means the library does not offer the op; `rev` means it does, but reverted (or the input was outside its domain or format) on every ladder input. What each library cell calls is listed at the end; [coverage.md](coverage.md) maps every function of every comparison library.

| op | Yul object (staticcall) | BL19Lib (inline) | BL127Lib (inline), the same op | ABDKMathQuad |
|---|---:|---:|---:|---:|
| abs | 724 / 727 / 743 | 133 / 133 / 133 | 152 / 152 / 152 | 21 / 21 / 21 |
| add | 1,119 / 1,126 / 1,167 | 650 / 650 / 669 | 128 / 128 / 128 | 460 / 734 / 765 |
| atanh | 3,430 / 5,037 / 5,058 | 3,404 / 5,148 / 5,204 | 2,913 / 2,950 / 2,977 |  |
| avg | 1,115 / 1,116 / 1,156 | 663 / 663 / 682 | 114 / 114 / 114 |  |
| cbrt | 3,039 / 3,086 / 3,111 | 2,736 / 2,762 / 2,775 | 1,953 / 1,953 / 1,953 |  |
| ceil | 960 / 1,131 / 1,197 | 336 / 522 / 570 | 147 / 147 / 147 |  |
| clamp | 1,128 / 1,134 / 1,178 | 491 / 491 / 492 | 241 / 241 / 242 |  |
| cmp | 801 / 803 / 805 | 248 / 248 / 248 |  | 346 / 476 / 489 |
| compound | 5,483 / 5,695 / 6,051 | 5,863 / 6,193 / 6,657 | 2,272 / 3,282 / 8,465 |  |
| cosh | 3,424 / 3,511 / 3,539 | 3,466 / 3,672 / 3,693 | 3,954 / 4,055 / 4,105 |  |
| dist | 1,042 / 1,230 / 1,324 | 607 / 819 / 927 | 289 / 289 / 289 |  |
| div | 1,354 / 1,370 / 1,374 | 804 / 804 / 804 | 413 / 413 / 413 | 818 / 818 / 818 |
| divDown | 1,440 / 1,464 / 1,493 | 987 / 987 / 987 | 476 / 476 / 476 |  |
| divUp | 1,479 / 1,531 / 1,577 | 988 / 988 / 1,034 | 479 / 479 / 479 |  |
| eq | 798 / 830 / 836 | 176 / 176 / 176 |  | 108 / 108 / 147 |
| erf | 5,622 / 9,690 / 12,649 | 6,156 / 10,604 / 13,596 | 3,191 / 7,804 / 16,404 |  |
| erfc | 9,723 / 9,755 / 12,791 | 10,495 / 10,650 / 13,684 | 250 / 7,786 / 16,410 |  |
| exp | 3,340 / 3,368 / 3,421 | 3,265 / 3,292 / 3,325 | 2,835 / 2,845 / 2,895 | 979 / 5,766 / 5,959 |
| exp10 | 3,193 / 3,216 / 3,255 | 3,150 / 3,177 / 3,271 | 3,065 / 3,081 / 3,086 |  |
| exp2 | 1,859 / 3,187 / 3,274 | 1,539 / 3,104 / 3,183 | 2,593 / 2,699 / 2,734 | 404 / 4,536 / 5,920 |
| expm1 | 2,734 / 3,038 / 3,455 | 2,373 / 2,747 / 3,379 | 1,560 / 2,960 / 4,488 |  |
| factorial | 1,013 / 1,217 / 1,223 | 391 / 717 / 761 | 399 / 400 / 422 |  |
| floor | 928 / 1,130 / 1,178 | 309 / 521 / 521 | 72 / 72 / 72 |  |
| frac | 834 / 1,050 / 1,960 | 187 / 427 / 1,417 | 69 / 69 / 69 |  |
| fromBL127 | 945 / 948 / 961 | 439 / 439 / 439 |  | 495 / 539 / 623 |
| fromFixed18 | 1,123 / 1,126 / 1,129 | 554 / 554 / 554 | 140 / 140 / 140 |  |
| fromUint | 934 / 937 / 940 | 412 / 412 / 412 |  |  |
| fromUintDown | 910 / 912 / 939 | 486 / 486 / 486 |  | 435 / 500 / 558 |
| fromUintUp | 995 / 999 / 1,048 | 487 / 487 / 533 |  |  |
| gavg | 2,267 / 2,297 / 2,323 | 1,865 / 1,865 / 1,879 | 719 / 1,025 / 1,025 |  |
| hypot | 1,162 / 3,286 / 3,524 | 592 / 3,326 / 3,665 | 880 / 1,186 / 1,186 |  |
| inv | 1,247 / 1,249 / 1,253 | 747 / 747 / 747 | 242 / 242 / 242 | 1,253 / 1,253 / 1,295 |
| lambertW0 | 9,149 / 9,554 / 27,305 | 10,022 / 10,614 / 32,215 | 328 / 8,217 / 11,271 |  |
| lambertWm1 | 8,005 / 9,521 / 28,009 | 8,761 / 10,588 / 33,139 | 8,059 / 8,881 / 11,333 |  |
| lerp | 1,238 / 6,421 / 6,842 | 543 / 5,877 / 6,775 | 477 / 477 / 477 |  |
| ln | 803 / 3,259 / 4,155 | 273 / 3,067 / 4,119 | 139 / 588 / 1,942 | 555 / 1,564 / 16,850 |
| log10 | 809 / 3,271 / 4,177 | 269 / 3,056 / 4,108 | 139 / 588 / 1,942 |  |
| log1p | 2,825 / 3,036 / 3,563 | 2,569 / 2,827 / 3,506 | 2,031 / 2,047 / 2,125 |  |
| log2 | 818 / 3,140 / 4,043 | 269 / 2,841 / 3,893 | 372 / 372 / 1,726 | 128 / 852 / 16,096 |
| log2Up | 912 / 1,169 / 1,190 | 339 / 677 / 691 | 218 / 218 / 218 |  |
| lt | 794 / 818 / 826 | 233 / 233 / 233 |  | 358 / 488 / 501 |
| max | 802 / 808 / 810 | 250 / 250 / 251 | 125 / 125 / 126 |  |
| min | 831 / 837 / 844 | 250 / 251 / 251 | 125 / 126 / 126 |  |
| mul | 1,058 / 1,063 / 1,071 | 530 / 530 / 530 | 267 / 267 / 267 | 667 / 709 / 709 |
| mulDown | 1,208 / 1,244 / 1,251 | 727 / 727 / 727 | 315 / 315 / 315 |  |
| mulUp | 1,220 / 1,243 / 1,268 | 728 / 728 / 774 | 337 / 337 / 386 |  |
| neg | 711 / 715 / 725 | 127 / 127 / 127 | 116 / 116 / 116 | 9 / 9 / 9 |
| normCdf | 9,938 / 10,036 / 19,471 | 10,769 / 11,170 / 21,843 | 236 / 7,059 / 8,480 |  |
| pow | 1,416 / 5,469 / 6,448 | 988 / 5,600 / 6,817 | 502 / 2,856 / 3,344 | 1,581 / 23,087 / 23,325 |
| powu | 2,213 / 5,329 / 7,189 | 1,699 / 5,301 / 7,427 | 1,323 / 4,039 / 10,520 |  |
| round | 864 / 1,100 / 1,160 | 226 / 473 / 521 | 212 / 212 / 212 |  |
| sign | 761 / 764 / 768 | 139 / 139 / 139 | 75 / 75 / 75 | 181 / 181 / 181 |
| sinh | 3,173 / 3,507 / 3,510 | 3,051 / 3,657 / 3,695 | 4,002 / 4,103 / 4,153 |  |
| sqrt | 1,625 / 1,644 / 1,665 | 1,203 / 1,207 / 1,211 | 478 / 833 / 833 | 760 / 760 / 760 |
| sub | 1,017 / 1,190 / 1,298 | 533 / 745 / 853 | 140 / 140 / 140 | 726 / 1,230 / 1,325 |
| tanh | 1,297 / 3,571 / 3,598 | 1,026 / 3,706 / 3,720 | 247 / 3,946 / 3,977 |  |
| toBL127 | 934 / 937 / 941 | 343 / 343 / 343 |  | 278 / 292 / 292 |
| toFixed18 | 974 / 1,030 / 1,033 | 440 / 480 / 480 | 121 / 121 / 121 |  |
| toFixed18Down | 1,278 / 1,309 / 1,313 | 718 / 723 / 723 | 160 / 160 / 160 |  |
| toFixed18Up | 1,321 / 1,335 / 1,388 | 724 / 724 / 738 | 185 / 185 / 190 |  |
| toIntDown | 937 / 1,096 / 1,099 | 330 / 466 / 466 |  | 109 / 278 / 293 |
| toIntUp | 956 / 1,124 / 1,144 | 331 / 467 / 481 |  |  |
| toUintDown | 814 / 871 / 875 | 286 / 405 / 405 |  | 83 / 240 / 254 |
| toUintUp | 846 / 959 / 1,006 | 287 / 406 / 419 |  |  |
| zeroFloorSub | 1,127 / 1,294 / 1,432 | 617 / 829 / 937 | 212 / 212 / 215 |  |

## Typical inputs

The ladder sits mostly on integers, powers of two and one, where several ops take a shortcut. These rows are the same forms on random inputs drawn per op from `keccak256("typical", op, i)`: non-integer, not a power of two, across the op's usual range. The inline columns are measured on 100 inputs, and the columns that include the external call on the first eight (`test_ladder_typical`, `test_ladder_typical_inline_*`): a call's figure moves with what the test has already run, an inline one does not. An inline figure does depend on how the calling contract compiles, so read these to about 1 or 2 percent, not to the gas. Min / median / max over the inputs.

| op | Yul object (staticcall) | BL19Lib (inline) | BL127Lib (inline), the same op | ABDKMathQuad |
|---|---:|---:|---:|---:|
| atanh | 3,588 / 4,016 / 5,203 | 3,398 / 5,198 / 5,244 | 2,913 / 2,952 / 2,997 |  |
| cbrt | 3,165 / 3,196 / 3,319 | 2,736 / 2,762 / 2,775 | 101 / 1,953 / 2,314 |  |
| compound | 5,578 / 5,611 / 5,826 | 5,852 / 5,863 / 6,547 | 1,556 / 3,088 / 3,231 |  |
| cosh | 3,641 / 3,674 / 3,775 | 3,531 / 3,683 / 3,724 | 3,981 / 4,054 / 4,128 |  |
| erf | 9,101 / 9,676 / 10,119 | 9,887 / 10,633 / 15,999 | 4,665 / 7,794 / 20,243 |  |
| erfc | 9,713 / 9,759 / 15,041 | 10,502 / 10,671 / 16,087 | 250 / 7,787 / 20,667 |  |
| exp | 3,266 / 3,317 / 3,408 | 3,124 / 3,300 / 3,355 | 2,783 / 2,834 / 2,875 | 5,472 / 5,806 / 6,155 |
| exp10 | 3,310 / 3,349 / 3,422 | 3,025 / 3,188 / 3,264 | 442 / 3,076 / 3,116 |  |
| exp2 | 3,282 / 3,299 / 3,444 | 2,926 / 3,088 / 3,175 | 2,636 / 2,694 / 2,744 | 4,788 / 5,052 / 5,317 |
| expm1 | 2,760 / 2,785 / 3,486 | 2,373 / 2,393 / 3,420 | 2,072 / 2,958 / 5,162 |  |
| gavg | 2,384 / 2,569 / 2,735 | 1,865 / 2,106 / 2,351 | 719 / 1,025 / 1,025 |  |
| hypot | 3,299 / 3,559 / 3,783 | 3,207 / 3,515 / 3,855 | 880 / 1,186 / 1,186 |  |
| lambertW0 | 7,974 / 9,591 / 9,968 | 8,682 / 10,757 / 41,623 | 6,591 / 8,319 / 8,546 |  |
| lambertWm1 | 9,373 / 9,788 / 10,004 | 10,152 / 10,589 / 41,638 | 7,923 / 8,175 / 8,364 |  |
| lerp | 6,633 / 6,908 / 7,029 | 5,886 / 6,486 / 6,513 | 477 / 477 / 477 |  |
| ln | 3,258 / 3,283 / 3,292 | 3,054 / 3,100 / 3,130 | 1,876 / 1,932 / 1,962 | 16,248 / 16,388 / 16,850 |
| log10 | 3,397 / 3,426 / 4,310 | 3,054 / 3,099 / 4,182 | 1,876 / 1,922 / 1,952 |  |
| log1p | 2,809 / 2,846 / 3,515 | 2,569 / 2,585 / 3,506 | 2,031 / 2,031 / 2,115 |  |
| log2 | 3,245 / 3,262 / 3,328 | 2,828 / 2,873 / 3,967 | 1,660 / 1,706 / 1,746 | 15,536 / 15,676 / 16,656 |
| normCdf | 10,063 / 11,442 / 13,834 | 10,706 / 11,472 / 17,304 | 236 / 7,707 / 19,094 |  |
| pow | 5,807 / 5,994 / 6,815 | 5,721 / 5,940 / 7,051 | 3,151 / 3,383 / 9,996 | 22,919 / 23,406 / 24,067 |
| powu | 2,505 / 6,694 / 8,754 | 1,725 / 6,649 / 17,006 | 1,349 / 4,890 / 10,625 |  |
| sinh | 3,588 / 3,640 / 3,727 | 3,520 / 3,664 / 3,716 | 4,029 / 4,102 / 4,176 |  |
| sqrt | 1,627 / 1,645 / 1,662 | 1,203 / 1,203 / 1,219 | 126 / 478 / 833 | 760 / 760 / 760 |
| tanh | 3,689 / 3,740 / 3,781 | 3,477 / 3,710 / 3,750 | 3,903 / 3,967 / 6,183 |  |

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
| fromBL127 | `from128x128(x) (truncates; fromBL127 rounds to nearest)` |
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
| toBL127 | `to128x128(x) (truncates; toBL127 rounds to nearest)` |
| toIntDown | `toInt(x) (truncates: floor for x >= 0, the rows kept)` |
| toUintDown | `toUInt(x) (truncates: floor for x >= 0)` |

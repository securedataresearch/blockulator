# FP127 gas ladder

Generated 2026-10-28 by `make bench`. Versions: fp127 7356be2, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), fraxlend fraxlend@2bed49d4dcc6 (VariableInterestRate V2, transcribed), euler evk-periphery@af436991e135 (IRMAdaptiveCurve, ExpLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, solmate solmate@89365b8 (no tag: v6 predates SignedWadMath), openzeppelin openzeppelin-contracts v5.7.0 (Math, SignedMath, vendored), uniswap v4-core v4.0.0 (FullMath, vendored), snekmate v0.1.2 (math module, vyper 0.4.3), forge forge Version: 1.7.1.

Each cell is min / median / max gas over the op's input ladder. The first two FP127 columns and the Caller column include the `staticcall` (and the object's own selector dispatch); the inline columns are the internal library call alone, timed inside the harness's entry point with the dispatch outside the window (the same cost for every op, whatever its place in the harness's list). An empty cell means the library does not offer the op; `rev` means it does, but reverted (or the input was outside its domain or format) on every ladder input. What each library cell calls is listed at the end; [coverage.md](coverage.md) maps every function of every comparison library.

| op | Huff (Sepolia, staticcall) | Yul object (staticcall) | FP127Caller | FP127Lib (inline) | ABDKMath64x64 | Solady | PRBMath SD59x18 | ABDKMathQuad | Balancer LogExpMath | Solmate | OpenZeppelin Math | Uniswap FullMath | PRBMath UD60x18 | snekmate (Vyper) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abs | 1,281 / 1,286 / 1,292 | 715 / 726 / 739 |  | 140 / 140 / 140 | 106 / 120 / 120 | 18 / 18 / 18 | 121 / 121 / 190 | 21 / 21 / 21 |  |  | 18 / 18 / 18 |  |  |  |
| add | 585 / 590 / 596 | 688 / 707 / 720 | 1,787 / 1,804 / 1,820 | 128 / 128 / 128 | 162 / 162 / 162 | 3 / 3 / 3 | 189 / 189 / 189 | 704 / 765 / 1,268 |  |  |  |  | 150 / 150 / 150 |  |
| atanh |  | 2,370 / 3,020 / 3,050 |  | 2,116 / 2,746 / 2,785 |  |  |  |  |  |  |  |  |  |  |
| avg | 1,484 / 1,489 / 1,494 | 867 / 882 / 964 |  | 114 / 114 / 114 | 31 / 31 / 31 | 60 / 60 / 60 | 154 / 154 / 156 |  |  |  | 318 / 318 / 318 |  | 105 / 105 / 105 | 113 / 113 / 113 |
| cbrt | 1,915 / 9,817 / 10,756 | 2,271 / 2,281 / 2,304 |  | 1,932 / 1,932 / 1,936 |  | 619 / 619 / 619 |  |  | 98 / 2,189 / 2,419 |  |  |  |  | 110 / 1,452 / 1,533 |
| ceil | 1,811 / 1,816 / 1,821 | 826 / 836 / 873 |  | 147 / 147 / 147 |  |  | 201 / 201 / 244 |  |  |  |  |  | 117 / 117 / 117 |  |
| clamp |  | 734 / 741 / 751 |  | 241 / 241 / 242 |  | 49 / 49 / 49 |  |  |  |  |  |  |  |  |
| compound |  | 2,724 / 3,620 / 8,055 |  | 2,200 / 3,154 / 8,406 |  |  |  |  |  |  |  |  |  |  |
| cosh |  | 3,952 / 3,958 / 3,985 |  | 3,808 / 3,835 / 3,969 |  |  |  |  |  |  |  |  |  |  |
| dist | 1,569 / 1,574 / 1,580 | 955 / 974 / 1,048 |  | 289 / 289 / 289 |  | 32 / 32 / 32 |  |  |  |  |  |  |  |  |
| div | 1,183 / 1,189 / 1,194 | 1,058 / 1,073 / 1,094 | 2,152 / 2,168 / 2,184 | 412 / 412 / 412 | 221 / 221 / 221 | 93 / 93 / 93 | 509 / 509 / 520 | 818 / 818 / 818 |  | 97 / 97 / 97 |  |  | 261 / 261 / 261 |  |
| divDown |  | 1,073 / 1,089 / 1,106 |  | 475 / 475 / 475 |  | 87 / 87 / 87 |  |  |  | 150 / 150 / 150 | 239 / 239 / 239 | 179 / 179 / 179 |  | 323 / 323 / 323 |
| divUp |  | 1,090 / 1,106 / 1,122 |  | 478 / 478 / 478 |  | 113 / 113 / 113 |  |  |  | 176 / 176 / 176 | 621 / 621 / 621 | 282 / 282 / 304 |  | 386 / 386 / 391 |
| erf |  | 4,382 / 7,544 / 20,006 |  | 4,300 / 7,588 / 20,460 |  |  |  |  |  |  |  |  |  |  |
| erfc |  | 4,414 / 7,535 / 20,031 |  | 4,309 / 7,573 / 20,469 |  |  |  |  |  |  |  |  |  |  |
| exp | 5,774 / 5,779 / 5,810 | 2,970 / 3,000 / 3,024 |  | 2,716 / 2,726 / 2,776 | 111 / 3,373 / 3,457 | 59 / 430 / 430 | 86 / 2,788 / 2,928 | 5,640 / 5,850 / 6,043 | 1,020 / 1,054 / 1,062 | 63 / 430 / 430 |  |  | 2,636 / 2,692 / 2,720 | 110 / 604 / 604 |
| exp10 | 6,437 / 6,438 / 6,473 | 3,168 / 3,171 / 3,194 |  | 2,966 / 2,987 / 2,997 |  |  |  |  |  |  |  |  |  |  |
| exp2 | 1,097 / 5,630 / 5,635 | 2,846 / 2,866 / 2,889 |  | 2,549 / 2,549 / 2,660 | 111 / 2,798 / 3,176 |  | 111 / 424 / 2,552 | 4,254 / 4,268 / 4,884 |  |  |  |  | 453 / 453 / 2,473 |  |
| expm1 |  | 2,066 / 3,262 / 4,747 |  | 1,545 / 3,106 / 4,473 |  |  |  |  |  |  |  |  |  |  |
| factorial | 2,093 / 2,318 / 2,829 | 903 / 927 / 1,003 |  | 389 / 400 / 422 |  | 79 / 579 / 1,729 |  |  |  |  |  |  |  |  |
| floor | 1,767 / 1,772 / 1,777 | 756 / 770 / 801 |  | 72 / 72 / 72 |  |  | 201 / 201 / 237 |  |  |  |  |  | 28 / 28 / 28 |  |
| frac | 1,804 / 1,810 / 1,815 | 761 / 771 / 781 |  | 69 / 69 / 69 |  |  | 125 / 125 / 125 |  |  |  |  |  | 8 / 8 / 8 |  |
| fromFixed18 | 798 / 799 / 800 | 880 / 882 / 979 | 1,943 / 1,946 / 2,035 | 140 / 140 / 140 |  |  |  |  |  |  |  |  |  |  |
| gavg | 4,896 / 4,931 / 5,094 | 1,329 / 1,599 / 1,615 |  | 733 / 1,079 / 1,079 | 805 / 833 / 891 | 78 / 449 / 5,856 | 122 / 960 / 984 |  |  |  |  |  | 122 / 949 / 973 |  |
| hypot | 5,469 / 5,498 / 5,666 | 1,551 / 1,839 / 1,871 |  | 1,020 / 1,366 / 1,366 |  |  |  |  |  |  |  |  |  |  |
| inv | 1,877 / 1,882 / 1,887 | 947 / 956 / 967 |  | 242 / 242 / 242 | 202 / 202 / 202 | 93 / 93 / 93 | 177 / 177 / 177 | 1,259 / 1,259 / 1,301 |  |  |  |  | 94 / 94 / 94 |  |
| lambertW0 | 12,826 / 20,801 / 20,996 | 7,431 / 7,651 / 8,339 |  | 7,938 / 8,170 / 9,089 |  | 1,569 / 2,658 / 3,894 |  |  |  |  |  |  |  |  |
| lambertWm1 |  | 7,450 / 7,669 / 10,119 |  | 7,812 / 8,052 / 11,102 |  |  |  |  |  |  |  |  |  |  |
| lerp |  | 1,003 / 1,017 / 1,025 |  | 477 / 477 / 477 |  | 118 / 282 / 295 |  |  |  |  |  |  |  |  |
| ln | 1,048 / 4,018 / 5,017 | 736 / 1,093 / 2,286 |  | 139 / 600 / 1,954 | 7,055 / 7,078 / 7,141 | 556 / 556 / 556 | 813 / 828 / 7,127 | 555 / 1,586 / 16,948 | 834 / 1,156 / 1,207 | 632 / 632 / 632 |  |  | 524 / 524 / 6,549 | 144 / 1,298 / 1,343 |
| log10 | 1,775 / 4,575 / 5,574 | 739 / 1,096 / 2,289 |  | 139 / 600 / 1,954 |  |  | 558 / 2,409 / 8,663 |  | 1,487 / 1,859 / 1,882 |  |  |  | 548 / 2,328 / 8,293 |  |
| log1p |  | 2,391 / 2,394 / 2,403 |  | 2,043 / 2,062 / 2,127 |  |  |  |  |  |  |  |  |  |  |
| log2 | 1,030 / 3,830 / 4,829 | 948 / 965 / 2,156 |  | 384 / 384 / 1,738 | 6,958 / 6,981 / 7,044 |  | 499 / 514 / 6,813 | 128 / 855 / 16,236 | 1,517 / 1,889 / 1,912 |  |  |  | 422 / 422 / 6,447 |  |
| log2Up | 2,319 / 2,398 / 5,988 | 814 / 824 / 878 |  | 209 / 209 / 209 |  | 247 / 247 / 247 |  |  |  |  | 513 / 513 / 513 |  |  | 397 / 505 / 541 |
| max | 1,488 / 1,494 / 1,499 | 1,019 / 1,040 / 1,155 |  | 125 / 125 / 126 |  | 23 / 23 / 23 |  |  |  |  | 86 / 86 / 86 |  |  |  |
| min | 1,452 / 1,457 / 1,467 | 980 / 1,001 / 1,099 |  | 125 / 126 / 126 |  | 23 / 23 / 23 |  |  |  |  | 86 / 86 / 86 |  |  |  |
| mul | 810 / 815 / 821 | 909 / 928 / 981 | 2,041 / 2,057 / 2,073 | 267 / 267 / 267 | 171 / 171 / 171 | 126 / 126 / 126 | 485 / 485 / 496 | 667 / 688 / 709 |  | 131 / 131 / 131 |  |  | 237 / 237 / 237 |  |
| mulDown |  | 813 / 829 / 846 |  | 315 / 315 / 315 |  | 86 / 86 / 86 |  |  |  | 150 / 150 / 150 | 239 / 239 / 239 | 179 / 179 / 179 |  | 323 / 323 / 323 |
| mulUp |  | 921 / 960 / 981 |  | 337 / 337 / 377 |  | 110 / 110 / 110 |  |  |  | 176 / 176 / 176 | 621 / 621 / 621 | 282 / 282 / 304 |  | 386 / 386 / 391 |
| neg | 1,294 / 1,299 / 1,304 | 747 / 757 / 767 |  | 116 / 116 / 116 | 76 / 76 / 76 |  | 134 / 134 / 134 | 9 / 9 / 9 |  |  |  |  |  |  |
| normCdf |  | 696 / 8,241 / 18,333 |  | 112 / 8,286 / 18,777 |  |  |  |  |  |  |  |  |  |  |
| pow | 8,844 / 9,182 / 9,535 | 1,117 / 3,281 / 8,073 |  | 502 / 3,028 / 8,371 |  | 1,279 / 1,279 / 1,279 | 1,511 / 9,911 / 10,047 | 8,748 / 23,290 / 24,459 | 2,000 / 2,203 / 2,319 | 1,355 / 1,355 / 1,355 |  |  | 1,267 / 9,292 / 9,406 |  |
| powu |  | 2,423 / 3,233 / 9,383 |  | 1,899 / 2,809 / 9,305 | 885 / 1,492 / 5,436 | 617 / 1,308 / 4,523 | 1,180 / 2,277 / 7,586 |  |  | 688 / 1,436 / 4,980 |  |  | 956 / 2,097 / 7,604 |  |
| round | 2,051 / 2,052 / 2,054 | 842 / 845 / 923 |  | 212 / 212 / 212 |  |  |  |  |  |  |  |  |  |  |
| sign | 1,722 / 1,727 / 1,732 | 734 / 744 / 755 |  | 75 / 75 / 75 |  |  | 84 / 84 / 189 | 181 / 181 / 182 |  |  |  |  |  | 78 / 78 / 78 |
| sinh |  | 3,948 / 3,966 / 3,985 |  | 3,853 / 3,880 / 4,014 |  |  |  |  |  |  |  |  |  |  |
| sqrt | 4,066 / 4,145 / 4,334 | 984 / 1,288 / 1,297 |  | 469 / 815 / 815 | 754 / 788 / 876 | 393 / 393 / 393 | 316 / 993 / 1,034 | 759 / 760 / 760 | 98 / 2,259 / 2,377 | 408 / 456 / 480 | 141 / 787 / 817 |  | 167 / 847 / 888 |  |
| sub | 623 / 628 / 634 | 734 / 745 / 760 | 1,849 / 1,865 / 1,881 | 140 / 140 / 140 | 162 / 162 / 162 | 3 / 3 / 3 | 187 / 187 / 187 | 726 / 1,236 / 1,331 |  |  |  |  | 150 / 150 / 150 |  |
| tanh |  | 2,890 / 3,970 / 6,205 |  | 2,438 / 3,828 / 6,044 |  |  |  |  |  |  |  |  |  |  |
| toFixed18 | 843 / 844 / 845 | 860 / 863 / 865 | 1,877 / 1,881 / 1,973 | 121 / 121 / 121 |  |  |  |  |  |  |  |  |  |  |
| toFixed18Down |  | 765 / 768 / 770 |  | 160 / 160 / 160 |  |  |  |  |  |  |  |  |  |  |
| toFixed18Up |  | 855 / 859 / 872 |  | 185 / 185 / 190 |  |  |  |  |  |  |  |  |  |  |
| zeroFloorSub | 1,568 / 1,573 / 1,579 | 1,038 / 1,058 / 1,078 |  | 212 / 212 / 215 |  | 17 / 17 / 17 |  |  |  |  | 92 / 92 / 92 |  |  |  |

## Typical inputs

The ladder sits mostly on integers, powers of two and one, where several ops take a shortcut. These rows are the same forms on random inputs drawn per op from `keccak256("typical", op, i)`: non-integer, not a power of two, across the op's usual range (`test_ladder_typical`). Min / median / max over the inputs.

| op | Huff (Sepolia, staticcall) | Yul object (staticcall) | FP127Caller | FP127Lib (inline) | ABDKMath64x64 | Solady | PRBMath SD59x18 | ABDKMathQuad | Balancer LogExpMath | Solmate | OpenZeppelin Math | Uniswap FullMath | PRBMath UD60x18 | snekmate (Vyper) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| atanh |  | 3,243 / 3,253 / 3,284 |  | 2,746 / 2,780 / 2,830 |  |  |  |  |  |  |  |  |  |  |
| cbrt | 10,013 / 10,403 / 10,878 | 2,454 / 2,478 / 2,614 |  | 1,932 / 1,936 / 1,936 |  | 619 / 619 / 1,186 |  |  | 2,301 / 2,311 / 2,313 |  |  |  |  | 1,407 / 1,424 / 1,462 |
| compound |  | 3,267 / 4,098 / 4,173 |  | 2,158 / 3,080 / 3,080 |  |  |  |  |  |  |  |  |  |  |
| cosh |  | 4,199 / 4,234 / 4,348 |  | 3,882 / 3,927 / 3,982 |  |  |  |  |  |  |  |  |  |  |
| erf |  | 5,808 / 7,733 / 11,901 |  | 5,480 / 7,406 / 11,765 |  |  |  |  |  |  |  |  |  |  |
| erfc |  | 5,824 / 7,337 / 8,543 |  | 5,485 / 7,025 / 8,259 |  |  |  |  |  |  |  |  |  |  |
| exp | 5,771 / 5,782 / 5,814 | 2,991 / 3,002 / 3,035 |  | 2,684 / 2,716 / 2,746 | 3,317 / 3,380 / 3,499 | 430 / 430 / 430 | 2,732 / 2,816 / 2,984 | 5,696 / 5,808 / 6,057 | 978 / 1,040 / 1,146 | 430 / 430 / 430 |  |  | 2,636 / 2,720 / 2,804 | 604 / 604 / 604 |
| exp10 | 6,443 / 6,445 / 6,484 | 3,171 / 3,185 / 3,237 |  | 2,946 / 2,982 / 3,017 |  |  |  |  |  |  |  |  |  |  |
| exp2 | 5,628 / 5,640 / 5,677 | 2,881 / 2,891 / 2,951 |  | 2,618 / 2,668 / 2,670 | 3,148 / 3,225 / 3,316 |  | 2,524 / 2,671 / 2,860 | 4,926 / 5,073 / 5,315 |  |  |  |  | 2,445 / 2,557 / 2,599 |  |
| expm1 |  | 3,203 / 3,295 / 5,453 |  | 2,959 / 3,059 / 5,147 |  |  |  |  |  |  |  |  |  |  |
| lambertW0 | 20,773 / 21,226 / 2,047,586,767 | 6,739 / 7,950 / 8,096 |  | 6,395 / 8,107 / 8,234 |  | 1,569 / 3,045 / 3,271 |  |  |  |  |  |  |  |  |
| lambertWm1 |  | 7,822 / 7,908 / 8,119 |  | 7,894 / 7,959 / 8,078 |  |  |  |  |  |  |  |  |  |  |
| ln | 4,204 / 4,520 / 5,044 | 2,353 / 2,363 / 2,428 |  | 1,905 / 1,944 / 1,964 | 7,055 / 7,080 / 7,105 | 556 / 556 / 556 | 6,857 / 7,083 / 7,247 | 16,265 / 16,335 / 16,668 | 1,031 / 1,091 / 1,237 | 632 / 632 / 632 |  |  | 6,279 / 6,474 / 6,669 | 1,145 / 1,226 / 1,289 |
| log10 | 4,960 / 5,152 / 5,482 | 2,366 / 2,375 / 2,393 |  | 1,924 / 1,934 / 1,964 |  |  | 8,543 / 8,618 / 8,843 |  | 1,792 / 1,891 / 1,940 |  |  |  | 8,173 / 8,233 / 8,473 |  |
| log1p |  | 2,560 / 2,565 / 2,575 |  | 2,043 / 2,064 / 2,127 |  |  |  |  |  |  |  |  |  |  |
| log2 | 4,198 / 4,445 / 4,877 | 2,229 / 2,249 / 2,319 |  | 1,672 / 1,723 / 1,738 | 6,972 / 6,990 / 7,026 |  | 6,604 / 6,724 / 6,844 | 15,536 / 15,553 / 15,973 | 1,880 / 1,908 / 1,937 |  |  |  | 6,327 / 6,402 / 6,477 |  |
| normCdf |  | 1,063 / 6,179 / 14,917 |  | 245 / 5,903 / 14,923 |  |  |  |  |  |  |  |  |  |  |
| pow | 9,631 / 9,783 / 9,922 | 4,256 / 4,300 / 4,377 |  | 3,220 / 3,316 / 3,351 |  | 1,279 / 1,279 / 1,279 | 9,844 / 10,065 / 10,363 | 23,384 / 23,609 / 24,137 | 2,185 / 2,223 / 2,313 | 1,355 / 1,355 / 1,355 |  |  | 9,238 / 9,544 / 9,654 |  |
| powu |  | 2,386 / 6,123 / 7,378 |  | 1,277 / 5,189 / 6,539 | 1,151 / 3,133 / 3,953 | 386 / 2,318 / 3,011 | 793 / 4,006 / 5,068 |  |  | 422 / 2,559 / 3,322 |  |  | 558 / 3,881 / 4,998 |  |
| sinh |  | 4,199 / 4,209 / 4,223 |  | 3,920 / 3,960 / 3,988 |  |  |  |  |  |  |  |  |  |  |
| sqrt | 4,182 / 4,298 / 4,406 | 1,165 / 1,224 / 1,480 |  | 469 / 469 / 815 | 760 / 828 / 850 | 393 / 393 / 393 | 945 / 978 / 1,011 | 759 / 759 / 760 | 2,287 / 2,349 / 2,545 | 432 / 456 / 480 | 739 / 766 / 793 |  | 799 / 824 / 856 |  |
| tanh |  | 4,201 / 4,290 / 6,440 |  | 3,787 / 3,836 / 6,044 |  |  |  |  |  |  |  |  |  |  |

## What each cell calls

The competitor function behind each cell, on the inputs converted once to its representation. "composed" is built from the library's own functions where it has none of that name; a note in parentheses is the domain the harness keeps to (other inputs count as `rev`) or a rounding difference.

| op | ABDKMath64x64 | Solady | PRBMath SD59x18 | ABDKMathQuad | Balancer LogExpMath | Solmate | OpenZeppelin Math | Uniswap FullMath | PRBMath UD60x18 | snekmate (Vyper) |
|---|---|---|---|---|---|---|---|---|---|---|
| abs | `abs(x)` | `abs(int256)` | `abs(x)` | `abs(x)` |  |  | `SignedMath.abs(int256)` |  |  |  |
| add | `add(a, b)` | `rawAdd(int256, int256) (unchecked)` | `add(a, b)` | `add(a, b)` |  |  |  |  | `add(a, b) (a, b >= 0)` |  |
| avg | `avg(a, b)` | `avg(int256, int256)` | `avg(a, b)` |  |  |  | `SignedMath.average(a, b) (toward zero; FP127's avg floors)` |  | `avg(a, b) (a, b >= 0)` | `_int256_average(a, b)` |
| cbrt |  | `cbrtWad(x) (x >= 0)` |  |  | `pow(x, 333333333333333333) (composed; x >= 0)` |  |  |  |  | `_wad_cbrt(x) (x >= 0)` |
| ceil |  |  | `ceil(x)` |  |  |  |  |  | `ceil(x) (x >= 0)` |  |
| clamp |  | `clamp(int256, int256, int256)` |  |  |  |  |  |  |  |  |
| dist |  | `dist(int256, int256)` |  |  |  |  |  |  |  |  |
| div | `div(a, b)` | `sDivWad(a, b)` | `div(a, b)` | `div(a, b)` |  | `wadDiv(a, b) (toward zero)` |  |  | `div(a, b) (a, b >= 0)` |  |
| divDown |  | `divWad(a, b) (a >= 0, b > 0)` |  |  |  | `divWadDown(a, b) (a, b >= 0)` | `Math.mulDiv(a, 1e18, b) (a, b >= 0)` | `FullMath.mulDiv(a, 1e18, b) (a, b >= 0)` |  | `_mul_div(a, 1e18, b, False) (a, b >= 0)` |
| divUp |  | `divWadUp(a, b) (a >= 0, b > 0)` |  |  |  | `divWadUp(a, b) (a, b >= 0)` | `Math.mulDiv(a, 1e18, b, Rounding.Ceil) (a, b >= 0)` | `FullMath.mulDivRoundingUp(a, 1e18, b) (a, b >= 0)` |  | `_mul_div(a, 1e18, b, True) (a, b >= 0)` |
| exp | `exp(x)` | `expWad(x)` | `exp(x)` | `exp(x)` | `exp(x)` | `wadExp(x)` |  |  | `exp(x) (x >= 0)` | `_wad_exp(x)` |
| exp2 | `exp_2(x)` |  | `exp2(x)` | `pow_2(x)` |  |  |  |  | `exp2(x) (x >= 0)` |  |
| factorial |  | `factorial(uint256) on the integer x (integral x)` |  |  |  |  |  |  |  |  |
| floor |  |  | `floor(x)` |  |  |  |  |  | `floor(x) (x >= 0)` |  |
| frac |  |  | `frac(x)` |  |  |  |  |  | `frac(x) (x >= 0)` |  |
| gavg | `gavg(a, b)` | `mulSqrt(a, b) (a, b >= 0)` | `gm(a, b)` |  |  |  |  |  | `gm(a, b) (a, b >= 0)` |  |
| inv | `inv(x)` | `sDivWad(1e18, x) (composed)` | `inv(x)` | `div(fromUInt(1), x) (composed)` |  |  |  |  | `inv(x) (x >= 0)` |  |
| lambertW0 |  | `lambertW0Wad(x)` |  |  |  |  |  |  |  |  |
| lerp |  | `lerp(a, b, t, 0, 1e18) (t in [0, 1]: Solady clamps t)` |  |  |  |  |  |  |  |  |
| ln | `ln(x)` | `lnWad(x)` | `ln(x)` | `ln(x)` | `ln(x)` | `wadLn(x)` |  |  | `ln(x) (x >= 0)` | `_wad_ln(x)` |
| log10 |  |  | `log10(x)` |  | `log(x, 10e18)` |  |  |  | `log10(x) (x >= 0)` |  |
| log2 | `log_2(x)` |  | `log2(x)` | `log_2(x)` | `log(x, 2e18)` |  |  |  | `log2(x) (x >= 0)` |  |
| log2Up |  | `log2Up(uint256) on the integer x (integral x >= 1)` |  |  |  |  | `Math.log2(uint256, Rounding.Ceil) on the integer x (integral x >= 1)` |  |  | `_log2(uint256, True) on the integer x (integral x >= 1)` |
| max |  | `max(int256, int256)` |  |  |  |  | `SignedMath.max(a, b)` |  |  |  |
| min |  | `min(int256, int256)` |  |  |  |  | `SignedMath.min(a, b)` |  |  |  |
| mul | `mul(a, b)` | `sMulWad(a, b) (toward zero)` | `mul(a, b)` | `mul(a, b)` |  | `wadMul(a, b) (toward zero)` |  |  | `mul(a, b) (a, b >= 0)` |  |
| mulDown |  | `mulWad(a, b) (a, b >= 0)` |  |  |  | `mulWadDown(a, b) (a, b >= 0)` | `Math.mulDiv(a, b, 1e18) (a, b >= 0)` | `FullMath.mulDiv(a, b, 1e18) (a, b >= 0)` |  | `_mul_div(a, b, 1e18, False) (a, b >= 0)` |
| mulUp |  | `mulWadUp(a, b) (a, b >= 0)` |  |  |  | `mulWadUp(a, b) (a, b >= 0)` | `Math.mulDiv(a, b, 1e18, Rounding.Ceil) (a, b >= 0)` | `FullMath.mulDivRoundingUp(a, b, 1e18) (a, b >= 0)` |  | `_mul_div(a, b, 1e18, True) (a, b >= 0)` |
| neg | `neg(x)` |  | `unary(x)` | `neg(x)` |  |  |  |  |  |  |
| pow |  | `powWad(x, y)` | `pow(x, y)` | `exp(mul(y, ln(x))) (composed)` | `pow(x, y) (x, y >= 0)` | `wadPow(x, y)` |  |  | `pow(x, y) (x, y >= 0)` |  |
| powu | `pow(x, n), n a uint256 (n >= 0)` | `rpow(x, n, 1e18) (x >= 0, n >= 0)` | `powu(x, n), n a uint256 (n >= 0)` |  |  | `rpow(x, n, 1e18) (x >= 0, n >= 0)` |  |  | `powu(x, n), n a uint256 (x >= 0, n >= 0)` |  |
| sign |  |  | `sign(x)` | `sign(x)` |  |  |  |  |  | `_signum(x)` |
| sqrt | `sqrt(x)` | `sqrtWad(x) (x >= 0)` | `sqrt(x)` | `sqrt(x)` | `pow(x, 0.5e18) (composed; x >= 0)` | `sqrt(x * 1e18) (composed: the integer root; x >= 0)` | `Math.sqrt(x * 1e18) (composed: the integer root; x >= 0)` |  | `sqrt(x) (x >= 0)` |  |
| sub | `sub(a, b)` | `rawSub(int256, int256) (unchecked)` | `sub(a, b)` | `sub(a, b)` |  |  |  |  | `sub(a, b) (a, b >= 0)` |  |
| zeroFloorSub |  | `zeroFloorSub(uint256, uint256) (a, b >= 0)` |  |  |  |  | `Math.saturatingSub(uint256, uint256) (a, b >= 0)` |  |  |  |

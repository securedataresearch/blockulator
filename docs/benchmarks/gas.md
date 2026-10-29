# BL127 gas ladder

Generated 2026-10-28 by `make bench`. Versions: bl127 6c2eeaf, huff sepolia:0xfae694D0c2c44181791F838c54Ed64C3151FfE30@11857616, solady v0.1.26, prb-math v4.2.0, abdk v3.2, balancer balancer-v3-monorepo@2b9ce4b1b8ad (LogExpMath.sol, vendored), aave aave-v3-origin@8305565ae342 (MathUtils, transcribed), morpho morpho-blue@8e26ca6a8dbc (MathLib, transcribed), fraxlend fraxlend@2bed49d4dcc6 (VariableInterestRate V2, transcribed), euler evk-periphery@af436991e135 (IRMAdaptiveCurve, ExpLib, transcribed), maker dss pot.sol rpow via solady v0.1.26, solmate solmate@89365b8 (no tag: v6 predates SignedWadMath), openzeppelin openzeppelin-contracts v5.7.0 (Math, SignedMath, vendored), uniswap v4-core v4.0.0 (FullMath, vendored), snekmate v0.1.2 (math module, vyper 0.4.3), forge forge Version: 1.7.1.

Each cell is min / median / max gas over the op's input ladder. The first two BL127 columns and the Caller column include the `staticcall` (and the object's own selector dispatch); the inline columns are the internal library call alone, timed inside the harness's entry point with the dispatch outside the window (the same cost for every op, whatever its place in the harness's list). An empty cell means the library does not offer the op; `rev` means it does, but reverted (or the input was outside its domain or format) on every ladder input. What each library cell calls is listed at the end; [coverage.md](coverage.md) maps every function of every comparison library.

| op | Huff (Sepolia, staticcall) | Yul object (staticcall) | BL127Caller | BL127Lib (inline) | ABDKMath64x64 | Solady | PRBMath SD59x18 | ABDKMathQuad | Balancer LogExpMath | Solmate | OpenZeppelin Math | Uniswap FullMath | PRBMath UD60x18 | snekmate (Vyper) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| abs | 1,281 / 1,286 / 1,291 | 672 / 681 / 695 |  | 140 / 140 / 140 | 106 / 120 / 120 | 18 / 18 / 18 | 121 / 121 / 190 | 21 / 21 / 21 |  |  | 18 / 18 / 18 |  |  |  |
| add | 585 / 590 / 596 | 663 / 682 / 696 | 1,762 / 1,778 / 1,795 | 128 / 128 / 128 | 162 / 162 / 162 | 3 / 3 / 3 | 189 / 189 / 189 | 704 / 765 / 1,268 |  |  |  |  | 150 / 150 / 150 |  |
| atanh |  | 2,390 / 3,031 / 3,063 |  | 2,280 / 2,910 / 2,949 |  |  |  |  |  |  |  |  |  |  |
| avg | 1,484 / 1,489 / 1,494 | 840 / 857 / 938 |  | 114 / 114 / 114 | 31 / 31 / 31 | 60 / 60 / 60 | 154 / 154 / 156 |  |  |  | 318 / 318 / 318 |  | 105 / 105 / 105 | 113 / 113 / 113 |
| cbrt | 1,914 / 9,817 / 10,756 | 2,245 / 2,255 / 2,277 |  | 1,932 / 1,932 / 1,936 |  | 619 / 619 / 619 |  |  | 98 / 2,191 / 2,423 |  |  |  |  | 110 / 1,452 / 1,533 |
| ceil | 1,811 / 1,815 / 1,821 | 824 / 834 / 871 |  | 147 / 147 / 147 |  |  | 201 / 201 / 244 |  |  |  |  |  | 117 / 117 / 117 |  |
| clamp |  | 753 / 760 / 770 |  | 241 / 241 / 242 |  | 49 / 49 / 49 |  |  |  |  |  |  |  |  |
| compound |  | 2,667 / 3,527 / 7,963 |  | 2,263 / 3,153 / 8,405 |  |  |  |  |  |  |  |  |  |  |
| cosh |  | 3,936 / 3,942 / 3,970 |  | 3,954 / 3,981 / 4,115 |  |  |  |  |  |  |  |  |  |  |
| dist | 1,569 / 1,575 / 1,580 | 973 / 992 / 1,066 |  | 289 / 289 / 289 |  | 32 / 32 / 32 |  |  |  |  |  |  |  |  |
| div | 1,183 / 1,189 / 1,194 | 1,032 / 1,047 / 1,067 | 2,126 / 2,141 / 2,158 | 413 / 413 / 413 | 221 / 221 / 221 | 93 / 93 / 93 | 509 / 509 / 520 | 818 / 818 / 818 |  | 97 / 97 / 97 |  |  | 261 / 261 / 261 |  |
| divDown |  | 1,015 / 1,030 / 1,047 |  | 476 / 476 / 476 |  | 87 / 87 / 87 |  |  |  | 150 / 150 / 150 | 239 / 239 / 239 | 179 / 179 / 179 |  | 323 / 323 / 323 |
| divUp |  | 1,098 / 1,115 / 1,131 |  | 479 / 479 / 479 |  | 113 / 113 / 113 |  |  |  | 176 / 176 / 176 | 621 / 621 / 621 | 282 / 282 / 304 |  | 386 / 386 / 391 |
| erf |  | 4,330 / 7,481 / 19,954 |  | 4,456 / 7,739 / 20,616 |  |  |  |  |  |  |  |  |  |  |
| erfc |  | 4,406 / 7,514 / 20,024 |  | 4,462 / 7,721 / 20,622 |  |  |  |  |  |  |  |  |  |  |
| exp | 5,774 / 5,779 / 5,810 | 3,026 / 3,058 / 3,080 |  | 2,835 / 2,845 / 2,895 | 111 / 3,373 / 3,457 | 59 / 430 / 430 | 86 / 2,788 / 2,928 | 5,640 / 5,850 / 6,043 | 1,020 / 1,054 / 1,062 | 63 / 430 / 430 |  |  | 2,636 / 2,692 / 2,720 | 110 / 604 / 604 |
| exp10 | 6,437 / 6,438 / 6,473 | 3,154 / 3,157 / 3,181 |  | 3,065 / 3,086 / 3,096 |  |  |  |  |  |  |  |  |  |  |
| exp2 | 1,097 / 5,629 / 5,635 | 2,860 / 2,881 / 2,903 |  | 2,593 / 2,593 / 2,704 | 111 / 2,798 / 3,176 |  | 111 / 424 / 2,552 | 4,254 / 4,268 / 4,884 |  |  |  |  | 453 / 453 / 2,473 |  |
| expm1 |  | 1,985 / 3,145 / 4,666 |  | 1,560 / 2,968 / 4,488 |  |  |  |  |  |  |  |  |  |  |
| factorial | 2,093 / 2,317 / 2,829 | 857 / 880 / 957 |  | 389 / 400 / 422 |  | 79 / 579 / 1,729 |  |  |  |  |  |  |  |  |
| floor | 1,767 / 1,772 / 1,778 | 731 / 744 / 775 |  | 72 / 72 / 72 |  |  | 201 / 201 / 237 |  |  |  |  |  | 28 / 28 / 28 |  |
| frac | 1,804 / 1,810 / 1,815 | 757 / 767 / 777 |  | 69 / 69 / 69 |  |  | 125 / 125 / 125 |  |  |  |  |  | 8 / 8 / 8 |  |
| fromFixed18 | 798 / 799 / 801 | 855 / 858 / 954 | 1,918 / 1,920 / 2,010 | 140 / 140 / 140 |  |  |  |  |  |  |  |  |  |  |
| gavg | 4,895 / 4,931 / 5,094 | 1,335 / 1,625 / 1,641 |  | 706 / 1,003 / 1,003 | 805 / 833 / 891 | 78 / 449 / 5,856 | 122 / 960 / 984 |  |  |  |  |  | 122 / 949 / 973 |  |
| hypot | 5,469 / 5,498 / 5,666 | 1,381 / 1,689 / 1,722 |  | 867 / 1,164 / 1,164 |  |  |  |  |  |  |  |  |  |  |
| inv | 1,877 / 1,882 / 1,887 | 944 / 954 / 964 |  | 242 / 242 / 242 | 202 / 202 / 202 | 93 / 93 / 93 | 177 / 177 / 177 | 1,259 / 1,259 / 1,301 |  |  |  |  | 94 / 94 / 94 |  |
| lambertW0 | 12,826 / 20,802 / 20,996 | 7,428 / 7,648 / 8,336 |  | 8,135 / 8,367 / 9,286 |  | 1,569 / 2,658 / 3,894 |  |  |  |  |  |  |  |  |
| lambertWm1 |  | 7,425 / 7,643 / 10,095 |  | 8,009 / 8,247 / 11,259 |  |  |  |  |  |  |  |  |  |  |
| lerp |  | 977 / 986 / 995 |  | 477 / 477 / 477 |  | 118 / 282 / 295 |  |  |  |  |  |  |  |  |
| ln | 1,048 / 4,018 / 5,016 | 684 / 1,051 / 2,244 |  | 139 / 600 / 1,954 | 7,055 / 7,078 / 7,141 | 556 / 556 / 556 | 813 / 828 / 7,127 | 555 / 1,586 / 16,948 | 834 / 1,160 / 1,211 | 632 / 632 / 632 |  |  | 524 / 524 / 6,549 | 144 / 1,298 / 1,343 |
| log10 | 1,775 / 4,575 / 5,573 | 713 / 1,081 / 2,274 |  | 139 / 600 / 1,954 |  |  | 558 / 2,409 / 8,663 |  | 1,491 / 1,865 / 1,890 |  |  |  | 548 / 2,328 / 8,293 |  |
| log1p |  | 2,352 / 2,355 / 2,364 |  | 2,043 / 2,062 / 2,127 |  |  |  |  |  |  |  |  |  |  |
| log2 | 1,030 / 3,831 / 4,828 | 883 / 900 / 2,085 |  | 384 / 384 / 1,738 | 6,958 / 6,981 / 7,044 |  | 499 / 514 / 6,813 | 128 / 855 / 16,236 | 1,521 / 1,895 / 1,920 |  |  |  | 422 / 422 / 6,447 |  |
| log2Up | 2,320 / 2,399 / 5,987 | 804 / 815 / 869 |  | 209 / 209 / 209 |  | 247 / 247 / 247 |  |  |  |  | 513 / 513 / 513 |  |  | 397 / 505 / 541 |
| max | 1,488 / 1,494 / 1,499 | 1,016 / 1,037 / 1,152 |  | 125 / 125 / 126 |  | 23 / 23 / 23 |  |  |  |  | 86 / 86 / 86 |  |  |  |
| min | 1,452 / 1,457 / 1,467 | 914 / 935 / 1,032 |  | 125 / 126 / 126 |  | 23 / 23 / 23 |  |  |  |  | 86 / 86 / 86 |  |  |  |
| mul | 810 / 815 / 821 | 843 / 862 / 915 | 1,976 / 1,991 / 2,008 | 267 / 267 / 267 | 171 / 171 / 171 | 126 / 126 / 126 | 485 / 485 / 496 | 667 / 688 / 709 |  | 131 / 131 / 131 |  |  | 237 / 237 / 237 |  |
| mulDown |  | 787 / 803 / 819 |  | 315 / 315 / 315 |  | 86 / 86 / 86 |  |  |  | 150 / 150 / 150 | 239 / 239 / 239 | 179 / 179 / 179 |  | 323 / 323 / 323 |
| mulUp |  | 875 / 913 / 934 |  | 337 / 337 / 377 |  | 110 / 110 / 110 |  |  |  | 176 / 176 / 176 | 621 / 621 / 621 | 282 / 282 / 304 |  | 386 / 386 / 391 |
| neg | 1,294 / 1,299 / 1,304 | 703 / 712 / 722 |  | 116 / 116 / 116 | 76 / 76 / 76 |  | 134 / 134 / 134 | 9 / 9 / 9 |  |  |  |  |  |  |
| normCdf |  | 584 / 8,211 / 18,316 |  | 112 / 8,421 / 18,910 |  |  |  |  |  |  |  |  |  |  |
| pow | 8,844 / 9,182 / 9,534 | 996 / 3,246 / 8,305 |  | 502 / 3,050 / 8,786 |  | 1,279 / 1,279 / 1,279 | 1,511 / 9,911 / 10,047 | 8,748 / 23,290 / 24,459 | 2,000 / 2,207 / 2,323 | 1,355 / 1,355 / 1,355 |  |  | 1,267 / 9,292 / 9,406 |  |
| powu |  | 2,425 / 3,230 / 9,554 |  | 1,962 / 2,872 / 10,520 | 885 / 1,492 / 5,436 | 617 / 1,308 / 4,523 | 1,180 / 2,277 / 7,586 |  |  | 688 / 1,436 / 4,980 |  |  | 956 / 2,097 / 7,604 |  |
| round | 2,051 / 2,052 / 2,053 | 881 / 884 / 961 |  | 212 / 212 / 212 |  |  |  |  |  |  |  |  |  |  |
| sign | 1,722 / 1,727 / 1,732 | 727 / 737 / 748 |  | 75 / 75 / 75 |  |  | 84 / 84 / 189 | 181 / 181 / 182 |  |  |  |  |  | 78 / 78 / 78 |
| sinh |  | 3,934 / 3,952 / 3,971 |  | 4,002 / 4,029 / 4,163 |  |  |  |  |  |  |  |  |  |  |
| sqrt | 4,066 / 4,145 / 4,334 | 982 / 1,285 / 1,295 |  | 469 / 815 / 815 | 754 / 788 / 876 | 393 / 393 / 393 | 316 / 993 / 1,034 | 759 / 760 / 760 | 98 / 2,259 / 2,381 | 408 / 456 / 480 | 141 / 787 / 817 |  | 167 / 847 / 888 |  |
| sub | 623 / 628 / 634 | 730 / 741 / 756 | 1,845 / 1,860 / 1,878 | 140 / 140 / 140 | 162 / 162 / 162 | 3 / 3 / 3 | 187 / 187 / 187 | 726 / 1,236 / 1,331 |  |  |  |  | 150 / 150 / 150 |  |
| tanh |  | 2,810 / 3,886 / 6,125 |  | 2,577 / 3,967 / 6,183 |  |  |  |  |  |  |  |  |  |  |
| toFixed18 | 842 / 844 / 846 | 875 / 877 / 880 | 1,892 / 1,895 / 1,988 | 121 / 121 / 121 |  |  |  |  |  |  |  |  |  |  |
| toFixed18Down |  | 763 / 765 / 768 |  | 160 / 160 / 160 |  |  |  |  |  |  |  |  |  |  |
| toFixed18Up |  | 871 / 874 / 888 |  | 185 / 185 / 190 |  |  |  |  |  |  |  |  |  |  |
| zeroFloorSub | 1,569 / 1,573 / 1,579 | 1,012 / 1,032 / 1,052 |  | 212 / 212 / 215 |  | 17 / 17 / 17 |  |  |  |  | 92 / 92 / 92 |  |  |  |

## Typical inputs

The ladder sits mostly on integers, powers of two and one, where several ops take a shortcut. These rows are the same forms on random inputs drawn per op from `keccak256("typical", op, i)`: non-integer, not a power of two, across the op's usual range (`test_ladder_typical`). Min / median / max over the inputs.

| op | Huff (Sepolia, staticcall) | Yul object (staticcall) | BL127Caller | BL127Lib (inline) | ABDKMath64x64 | Solady | PRBMath SD59x18 | ABDKMathQuad | Balancer LogExpMath | Solmate | OpenZeppelin Math | Uniswap FullMath | PRBMath UD60x18 | snekmate (Vyper) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| atanh |  | 3,255 / 3,268 / 3,296 |  | 2,910 / 2,944 / 2,994 |  |  |  |  |  |  |  |  |  |  |
| cbrt | 10,013 / 10,402 / 10,879 | 2,428 / 2,452 / 2,588 |  | 1,932 / 1,936 / 1,936 |  | 619 / 619 / 1,186 |  |  | 2,301 / 2,313 / 2,315 |  |  |  |  | 1,407 / 1,424 / 1,462 |
| compound |  | 3,209 / 4,006 / 4,081 |  | 2,221 / 3,078 / 3,078 |  |  |  |  |  |  |  |  |  |  |
| cosh |  | 4,184 / 4,218 / 4,332 |  | 4,028 / 4,073 / 4,128 |  |  |  |  |  |  |  |  |  |  |
| erf |  | 5,756 / 7,676 / 11,849 |  | 5,636 / 7,559 / 11,921 |  |  |  |  |  |  |  |  |  |  |
| erfc |  | 5,815 / 7,330 / 8,535 |  | 5,638 / 7,186 / 8,419 |  |  |  |  |  |  |  |  |  |  |
| exp | 5,771 / 5,781 / 5,813 | 3,047 / 3,058 / 3,091 |  | 2,803 / 2,835 / 2,865 | 3,317 / 3,380 / 3,499 | 430 / 430 / 430 | 2,732 / 2,816 / 2,984 | 5,696 / 5,808 / 6,057 | 978 / 1,040 / 1,146 | 430 / 430 / 430 |  |  | 2,636 / 2,720 / 2,804 | 604 / 604 / 604 |
| exp10 | 6,443 / 6,445 / 6,484 | 3,157 / 3,171 / 3,224 |  | 3,045 / 3,081 / 3,116 |  |  |  |  |  |  |  |  |  |  |
| exp2 | 5,628 / 5,640 / 5,677 | 2,896 / 2,906 / 2,966 |  | 2,662 / 2,712 / 2,714 | 3,148 / 3,225 / 3,316 |  | 2,524 / 2,671 / 2,860 | 4,926 / 5,073 / 5,315 |  |  |  |  | 2,445 / 2,557 / 2,599 |  |
| expm1 |  | 3,219 / 3,252 / 5,372 |  | 2,954 / 2,996 / 5,162 |  |  |  |  |  |  |  |  |  |  |
| lambertW0 | 20,773 / 21,225 / 2,047,586,767 | 6,582 / 7,947 / 8,093 |  | 6,592 / 8,304 / 8,431 |  | 1,569 / 3,045 / 3,271 |  |  |  |  |  |  |  |  |
| lambertWm1 |  | 7,796 / 7,882 / 8,093 |  | 8,091 / 8,156 / 8,275 |  |  |  |  |  |  |  |  |  |  |
| ln | 4,204 / 4,519 / 5,044 | 2,311 / 2,321 / 2,385 |  | 1,905 / 1,944 / 1,964 | 7,055 / 7,080 / 7,105 | 556 / 556 / 556 | 6,857 / 7,083 / 7,247 | 16,265 / 16,335 / 16,668 | 1,031 / 1,091 / 1,241 | 632 / 632 / 632 |  |  | 6,279 / 6,474 / 6,669 | 1,145 / 1,226 / 1,289 |
| log10 | 4,960 / 5,152 / 5,482 | 2,351 / 2,360 / 2,378 |  | 1,924 / 1,934 / 1,964 |  |  | 8,543 / 8,618 / 8,843 |  | 1,800 / 1,895 / 1,948 |  |  |  | 8,173 / 8,233 / 8,473 |  |
| log1p |  | 2,521 / 2,526 / 2,536 |  | 2,043 / 2,064 / 2,127 |  |  |  |  |  |  |  |  |  |  |
| log2 | 4,198 / 4,445 / 4,877 | 2,158 / 2,178 / 2,248 |  | 1,672 / 1,723 / 1,738 | 6,972 / 6,990 / 7,026 |  | 6,604 / 6,724 / 6,844 | 15,536 / 15,553 / 15,973 | 1,888 / 1,914 / 1,941 |  |  |  | 6,327 / 6,402 / 6,477 |  |
| normCdf |  | 969 / 6,155 / 15,048 |  | 236 / 6,037 / 15,056 |  |  |  |  |  |  |  |  |  |  |
| pow | 9,631 / 9,783 / 9,922 | 4,140 / 4,185 / 4,262 |  | 3,221 / 3,317 / 3,352 |  | 1,279 / 1,279 / 1,279 | 9,844 / 10,065 / 10,363 | 23,384 / 23,609 / 24,137 | 2,185 / 2,223 / 2,313 | 1,355 / 1,355 / 1,355 |  |  | 9,238 / 9,544 / 9,654 |  |
| powu |  | 2,585 / 6,125 / 10,341 |  | 1,340 / 5,252 / 10,446 | 1,151 / 3,133 / 3,953 | 386 / 2,318 / 3,011 | 793 / 4,006 / 5,068 |  |  | 422 / 2,559 / 3,322 |  |  | 558 / 3,881 / 4,998 |  |
| sinh |  | 4,185 / 4,196 / 4,209 |  | 4,069 / 4,109 / 4,137 |  |  |  |  |  |  |  |  |  |  |
| sqrt | 4,183 / 4,299 / 4,406 | 1,162 / 1,221 / 1,478 |  | 469 / 469 / 815 | 760 / 828 / 850 | 393 / 393 / 393 | 945 / 978 / 1,011 | 759 / 759 / 760 | 2,287 / 2,351 / 2,545 | 432 / 456 / 480 | 739 / 766 / 793 |  | 799 / 824 / 856 |  |
| tanh |  | 4,115 / 4,205 / 6,360 |  | 3,926 / 3,975 / 6,183 |  |  |  |  |  |  |  |  |  |  |

## What each cell calls

The competitor function behind each cell, on the inputs converted once to its representation. "composed" is built from the library's own functions where it has none of that name; a note in parentheses is the domain the harness keeps to (other inputs count as `rev`) or a rounding difference.

| op | ABDKMath64x64 | Solady | PRBMath SD59x18 | ABDKMathQuad | Balancer LogExpMath | Solmate | OpenZeppelin Math | Uniswap FullMath | PRBMath UD60x18 | snekmate (Vyper) |
|---|---|---|---|---|---|---|---|---|---|---|
| abs | `abs(x)` | `abs(int256)` | `abs(x)` | `abs(x)` |  |  | `SignedMath.abs(int256)` |  |  |  |
| add | `add(a, b)` | `rawAdd(int256, int256) (unchecked)` | `add(a, b)` | `add(a, b)` |  |  |  |  | `add(a, b) (a, b >= 0)` |  |
| avg | `avg(a, b)` | `avg(int256, int256)` | `avg(a, b)` |  |  |  | `SignedMath.average(a, b) (toward zero; BL127's avg floors)` |  | `avg(a, b) (a, b >= 0)` | `_int256_average(a, b)` |
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

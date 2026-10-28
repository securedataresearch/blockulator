# Changelog

A release is the public name for a set of deployed contracts. Each contract
keeps its own version in its CREATE2 salt, because the salt names the address;
`contracts/deployments/RELEASE.json` maps the release to every address.

## Unreleased

FP127's exp kernel and division, same words (FP127 takes a new salt at the
next deploy):

- `expk` works in X form (H·2^-256 + L·2^-384): three 16-entry table levels
  and a degree-16 minimax corrector, never above the truth, within 2^-311
  relative (`scripts/fp127/generators/expk.py`). `exp` 5,360 → 2,716 gas
  (typical, inline), `exp2` 5,687 → 2,668, `exp10` 5,555 → 2,982, `expm1`,
  `sinh`, `cosh`, `tanh` about −40%, Lambert W about −28%.
- `div`, `divDown` and `divUp` share an exact core, two 64-bit digits when
  both operands are under 2^64: `div` 649 → 412, `divDown`/`divUp` 818 → 475.
- The FP127 object is 20,776 bytes (2.2: 21,858): one copy of the kernel
  where the optimizer had made three.

factorial is a table in both libraries (`scripts/fp19/generators/facttab.py`,
checked in CI):

- FP19: the 169 correctly rounded words for 2 ≤ n ≤ 170, by a binary search
  on n; the domain stops at 170! (the largest factorial a binary64 holds),
  `Overflow` from 171 (2.2: n ≤ 20,366 by a 512-bit running product, 1.07M
  gas at the median and 2.14M at the top; now 714 median, 762 at most).
  factorial moves from FP19S to the FP19 core (17,221 bytes; FP19S 23,985),
  so both take new salts at the next deploy.
- FP127: the 34 values two to a word, as the Huff's jump table was: about 400
  gas at every n (v6's multiplication: 190 to 1,918). The same words.

FP127 `compound` and the erfc tail, the same words (nearest on every sweep
and vector):

- `compound` for |n| ≥ 16 takes n log2(1 + rate) from the one-word log and
  2^t through `pow2t`, then log2 at 2^-299 and a tested `pow2r`, `powu`
  last: sweep 9,245 / 10,913 / 33,268 → 3,360 / 9,344 / 41,484 gas (median,
  p99, max; the largest is one result near 2^124 that `powus` decides).
  `precise_model.py fastcompound` checks both bounds.
- erfc for 4 < x ≤ 9.5 is e^(−x²) times a degree-43 minimax polynomial for
  e^(x²) erfc(x), held to an absolute 2^-175 on erfc (`erf_model.py`,
  `--check` in CI), where the continued fraction ran: 7,650 gas at every x
  of the tail (the fraction: about 20,000 near 4). erf, erfc, normCdf max
  35,352 → 20,746, p99 about 25,000 → 17,430.
- The FP127 object is 23,797 bytes; inline `FP127Lib.compound` 11.0 KB
  (was 1.3 KB).

BlockulatorWad, a third library (`contracts/src/wad/`, inline, no deployed
object): Solady's `FixedPointMathLib` WAD names, signatures and error
selectors (mulWad, divWad, sMulWad, sDivWad, sqrtWad, cbrtWad, expWad, lnWad,
powWad, lambertW0Wad, with log2Wad and log10Wad), explicit `…Up` and `…Down`
for every one, and PRBMath's exp, ln and pow. Every result is the exact real
value rounded once in the stated direction:

- mul, div, sqrt and cbrt exactly on 512 bits, in one word where Solady's
  path applies (mulWad 107 gas, Solady 86); the domains only widen (a result
  that fits never reverts).
- exp, ln, log2, log10 and pow on FP19's kernels fed the exact input,
  lambertW0 on FP19's; a cut at the wei with a stated bound, and a second
  stage at 2^-510 on the exact input where the bound reaches a wei boundary.
  expWad 2,357 gas, lnWad 2,415, powWad 4,762 (PRBMath 2,719, 6,980, 9,877).
- `make sweep`: 27 WAD rows, 0 wrong of 108,000, and 0 of 52,000 through the
  second stage alone. `make wad` (`docs/benchmarks/wad.md`): on the same
  inputs Solady's expWad is off by a wei or more on 48%, lnWad 24%, powWad
  66%, lambertW0Wad 28%; PRBMath's exp, ln, log2, log10 and pow on 72 to 98%.
- `gen.py --lib wad` builds it from `BlockulatorWad.yul.src` on
  `FP19.yul.src` (a library on a base source, library only, exports without
  a leave written into their blocks).

## Blockulator 2.2 (2026-10-22)

The second gas pass: every result the same word (FP19 correctly rounded,
FP127's transcendentals nearest), about half the gas, FP19 drawn into four
objects by idea, and the first CLZ build. Deployed 2026-10-22, Sepolia
blocks 11,974,968 to 11,974,985.

| component | version | Sepolia |
|---|---|---|
| FP127 | FP127 v6, 53 ops, 21,858 bytes | `0xb349DB36D51b0BC10Dd43aF70009b7B6E7c1CBe4` |
| FP19 | FP19 v5, 43 ops, 10,333 bytes | `0xAa1f71B7B08d568379b28E1488c6B737a1C6eb52` |
| FP19E | FP19E v5, 12 ops, 21,598 bytes | `0x017F68A57dD53a6dF2043c24B712b287F9549AE2` |
| FP19H | FP19H v5, 4 ops, 13,021 bytes | `0xEfefa2B63A173d56F9db79C5dd8A607F4aA859A5` |
| FP19S | FP19S v5, 6 ops, 24,263 bytes | `0x73E8809F163d4358773cc5F25c134997B4b842F4` |
| LadderRunner | FP127 ladder v10 | `0xF14Ac5DDA9C0c10C50aa4Be9D219509fAa936A9b` |
| EdgeRunner | FP127 ladder v10 | `0x5123DaA96A96e550665401Bd56AD0770DDB9004e` |

Records: `contracts/deployments/{RELEASE,FP127,FP19,Ladder}.md`. The five
objects are verified on Sourcify and Blockscout and pass their smoke tests
against the live contracts; the thirteen ladder contracts are
`exact_match` on Sourcify. Checked live on 2026-10-23: 9,408 ladder cells
through LadderRunner v10 (block 11,975,057) and 1,511 edge cells through
EdgeRunner v10 (block 11,975,211), 0 mismatches. Blockulator 2.1 (FP127 v5,
FP19 release four's FP19, FP19X, FP19X2 and FP19X3, ladder v9) and 2.0
stay live and verified at their addresses.

Gas, sweep medians of the inline libraries (`docs/benchmarks/sweep.md`),
2.1 → 2.2:

| op | FP127 | FP19 |
|---|---:|---:|
| add | 124 → 124 | 1,278 → 677 |
| mul | 263 → 263 | 1,145 → 530 |
| div | 657 → 657 | 1,869 → 808 |
| sqrt | 710 → 683 | 2,692 → 1,201 |
| cbrt | 6,019 → 1,948 | 13,593 → 2,747 |
| exp | 6,090 → 5,651 | 7,715 → 3,299 |
| ln | 3,410 → 1,934 | 8,492 → 3,623 |
| pow | 6,121 → 3,375 | 14,834 → 5,902 |
| compound | 9,469 → 9,215 | 17,028 → 6,304 |
| cosh | 10,651 → 5,207 | 8,498 → 3,609 |
| sinh | 2,284 → 5,262 | 8,686 → 3,613 |
| tanh | 4,680 → 4,679 | 16,356 → 3,628 |
| erf | 4,881 → 3,623 | 17,603 → 12,990 |
| erfc | — | 34,236 → 13,943 |
| normCdf | 4,952 → 3,694 | 30,839 → 13,562 |
| lambertW0 | 18,607 → 11,308 | 34,049 → 10,623 |
| lambertWm1 | 23,977 → 11,101 | 29,743 → 13,150 |

(FP127 `add` is not in the sweep; 124 is the gas ladder's median, unchanged.)
FP127 `sinh` is the one op dearer: its series below 1 went, and it now runs
on the exp kernel like `cosh`. Through the deployed objects FP127's basic
ops are 140 to 215 gas cheaper (`add` 899 → 694, `mul` 1,103 → 889 on the
gas ladder, `docs/benchmarks/gas.md`) and FP19's roughly half (`add`
2,423 → 1,124, `mul` 2,462 → 1,069, `exp` 7,637 → 3,369,
`docs/benchmarks/gas19.md`).

Where it came from, in order (PRs #120 to #132):

- **Hyperbolics on the exp/log kernels** (#120, #121): FP127 `cosh`, `sinh`
  and `atanh`, FP19 `sinh`, `tanh` and `atanh` from expm1/log1p in place of
  their series.
- **Precision-doubling Newton** from a bit-hack seed for `sqrt`, `div`,
  `inv` and `cbrt` in both libraries (#122): FP19 `cbrt` 13.6k → 3.1k,
  FP127 `cbrt` 6.0k → 2.2k with no fallback.
- **Lambert W without series** (#123, #126): an adaptive-precision safe
  step with a residual bound from a log-free seed; the fallback rate falls
  from 2% / 5.8% to 0.07% / 0.2% (W0 / W−1).
- **FP19 `erfc` asymptotic tail** from y ≥ 18 (#125).
- **FP19's basic ops** (#128): a known-position normalise, a one-compare
  pack, a lean unpack and a branchless msb, bit-identical; add 1,262 →
  705, mul 1,145 → 572, div 1,433 → 842 inline.
- **CLZ** (#130): one osaka build, msb = 255 − clz(x) (23 gas against 243
  to 374), solc 0.8.38 with solc 0.8.24's Yul optimizer sequence pinned.
- **Four objects by idea** (#131) and **the exp/log kernels** (#132),
  below.

The compile settings were measured and left alone: optimizer runs from 200
to 2^32 − 1 build byte-identical objects, and 0.8.38's default optimizer
sequence costs more gas as well as more bytes. Compiling the inline
libraries with `via_ir = true` takes about 5.5× as long and makes them
10–33% cheaper (FP127 `add` 124 → 83, `ln` 600 → 409; FP19 `add` 662 →
506, `exp` 3,295 → 2,893): without it their heavy ops cost 5–14% (FP127)
and 6–19% (FP19) more than the object net of its call, with it within
about −7% to +3% (`docs/benchmarks/profile.md`).

### FP19 v5 and FP127 v6

FP19 deploys as four objects by idea, replacing FP19, FP19X, FP19X2 and
FP19X3: **FP19**, the number (arithmetic, roots, comparison, rounding,
conversions: 43 ops, salt `FP256 v5`); **FP19E**, the elementary functions
on one exp/log kernel (exp, exp2, exp10, expm1, ln, log2, log10, log2Up,
log1p, pow, powu, compound; `FP19E v5`); **FP19H**, the hyperbolic
functions (sinh, cosh, tanh, atanh; `FP19H v5`), their own object because
FP19E with them measured 27,308 bytes, over the 24,576 limit, so FP19H
carries its own copy of the kernel; **FP19S**, the special functions (erf,
erfc, normCdf, lambertW0, lambertWm1, factorial; `FP19S v5`). In both
libraries `pi` is now a constant and `gcd` is removed. Without the kernels
the FP19 core is 10,333 bytes, and the room goes to the basic ops' fast
path, bit-identical: through the object `mulDown`/`mulUp` 201 to 267 gas
less, `divDown`/`divUp` 250 to 256, the in-place conversions up to 67, and
add, sub, mul, div 10 to 70 (`docs/benchmarks/gas19.md`).

FP19's exp/log kernels are rewritten, measured first and bit-identical in
every result (correct rounding fixes the word; only the gas and the
fallback rates move): 2^f by two 16-entry table levels and a degree-19
minimax polynomial, log2 by two additive 16-entry levels, one division and a
degree-12 minimax polynomial in y², ln(1 + d)/d and (e^d − 1)/d near zero by
minimax polynomials in place of the Taylor series, every product's high word
in line and the top polynomial steps in one word. Sweep medians, inline:
exp 7,077 → 3,299, ln 7,640 → 3,623, log1p 8,727 → 2,558, expm1 6,523 →
2,390, pow 14,011 → 5,902, compound 16,113 → 6,304, sinh 7,331 → 3,613,
atanh 12,606 → 5,073, erf 16,962 → 12,990, lambertW0 14,524 → 10,623.
FP19E is 21,598 bytes and FP19H 13,021.

FP127's one-word kernels get the same treatment (salt `FP127 v6`): 2^f by one 16-entry table and a degree-15 minimax polynomial
(2^-146.7 relative, from 2^-145.9), log2 by two additive 16-entry levels and
a degree-14 minimax polynomial (2^-160.5 absolute, from about 2^-150). Its
double-word exp kernel multiplies each table factor in line instead of
through a helper called from 23 cases. Every result is the same word; sweep
medians: ln 3,215 → 1,934, log2 2,999 → 1,718, pow 5,861 → 3,375, exp 6,085
→ 5,651, erf 4,879 → 3,623, atanh 3,715 → 2,750, lambertW0 11,765 → 11,308.
FP127 is 21,858 bytes (from 22,272).

Migration: the 2.2 objects need a chain with CLZ (EIP-7939, Osaka): Ethereum,
Sepolia, Arbitrum, OP, Base, Unichain, Polygon PoS, BNB Chain, Gnosis and
the others listed in `contracts/deployments/README.md`, not zkSync Era,
Avalanche C-Chain or Polygon zkEVM (there every call that counts leading
bits fails; `make probe-clz RPC=<url>` checks a chain). `pi(terms)` →
`FP127Lib.PI` / `FP19Lib.PI` (the format's word
nearest π; an object caller copies the literal); `gcd` has no replacement;
an FP19 caller of FP19X, FP19X2 or FP19X3 calls the object that now
holds the op (`contracts/src/fp19/ops.json` names it), through `IFP19`,
`IFP19E`, `IFP19H` or `IFP19S`. The inline libraries keep every other
signature.

### Ladder v10

Salt `FP127 ladder v10`, deployed 2026-10-22: the eleven adapters, with
`LadderFP127` calling FP127 v6, `LadderFP127Lib` inlining it and
`LadderFP19` inlining FP19 v5, and both runners. The datasets and the
live runners compute the same code.

## Blockulator 2.1 (2026-10-21)

Both rulers round once: every FP127 transcendental to the nearest word,
every FP19 op correctly rounded or exact, and the directed ops for the
token edge. Deployed 2026-10-21, Sepolia blocks 11,966,114 to 11,966,639.

| component | version | Sepolia |
|---|---|---|
| FP127 | FP127 v5, 55 ops, 19,863 bytes | `0x619176d72D7a12390F8970802943D344c0fd3fE2` |
| FP19 | FP19 v4, 37 ops, 24,512 bytes | `0xA3C8C8700465F9e20Ff9dfA64066c2EF693Aa6c9` |
| FP19X | FP19X v4, 5 ops, 22,266 bytes | `0x175246B258Cc0dC3efEFe74b5fac8cC52C0c40d0` |
| FP19X2 | FP19X2 v4, 10 ops, 19,889 bytes | `0xE655bB8b1Cf848cAf3FD69F381289d144f5Bc697` |
| FP19X3 | FP19X3 v4, 15 ops, 6,844 bytes | `0x59D51481cb2EA924EC17FE263cd05b90CEF22383` |
| LadderRunner | FP127 ladder v9 | `0xCd4581E0a9Cf014d1aF660F62a7D96039efE7DC5` |
| EdgeRunner | FP127 ladder v9 | `0xcA89eeA1831c38B62d2d3332ECbb8A57BaF246fF` |

Records: `contracts/deployments/{RELEASE,FP127,FP19,Ladder}.md`. FP127
and the four FP19 objects are verified on Sourcify and Blockscout and pass
their smoke tests against the live contracts; the thirteen ladder contracts
are verified on Sourcify. FP127 v5's first send ran out of gas under the
old 20M deploy limit and created nothing; `DEPLOY_GAS` is now 40M and every
deploy target rejects a reverted receipt. The earlier objects (FP127 v1 to
v4, FP19 releases one to three, ladder v1 to v8) stay deployed.

### FP127 v5

Salt `FP127 v5`, 55 ops, 19,863 bytes of runtime, deployed 2026-10-21 at
`0x619176d72D7a12390F8970802943D344c0fd3fE2`.

- Every transcendental returns the nearest word. `exp`, `exp2`, `exp10`,
  `expm1`, `sinh`, `cosh` and `tanh` round once from a double-word kernel
  good to about 2^−300; `ln`, `log2`, `log10`, `log1p`, `pow` and `cbrt`
  round the one-word value when its error bound allows and fall back to the
  double word near a midpoint; `powu` and
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
- Gas through the object, ladder medians against v4: `exp` 6,058 (+145),
  `exp2` 3,714 (−2,048), `pow` 4,956 (−4,425), `cbrt` 4,545 (−5,404),
  `lambertW0` 24,690 (+3,752), `sqrt` 2,175 (−2,104), `mul` 1,103 (+99).
  The object dispatches by binary search on the selector, not a linear
  chain.
- A gas-only pass (`fp127-faster`), every result the same word, checked on
  the sweep, the vectors and dense extra sets. Sweep medians:
  - Lambert W uses Halley steps, as many as the seed needs: `lambertW0`
    46,170 → 18,607 and `lambertWm1` 35,250 → 23,977.
  - `pow` and `cbrt` try one word first: 14,807 → 6,121 and 14,935 → 6,019.
  - The erf loops run inline; erf's worst case falls from 66,655 to 36,440.
  - At tiny x, `expm1` 7,089 → 2,066, `sinh` 6,060 → 2,284 and `tanh`
    7,988 → 4,680.
  - `sqrt` 3,209 → 710 uses Solady's isqrt seed, keeping v4's word where it
    was not the floor.
  - `inv` 698 → 242, `div` 315 when |a| < 1, and the logs' fallback
    ~12,600 → ~9,760.
  - `exp2frac` runs inline throughout.

### FP19 release four

Correctly rounded, and the edge. Four objects, deployed 2026-10-21 at the
addresses in the table above.

- Every FP19 op is correctly rounded or exact: 0 misrounded of 364,658
  random inputs (281,821 before #79's ops), and 0 when every input is
  forced through the second stage (`docs/benchmarks/sweep.md`); release
  three had pow 8 in 20,000 off by one ULP, ln 1, normCdf 1 in 4,000,
  compound up to 4 ULP (291 of 3,853), lambertW0 up to 2 (668 of 2,000). Each fast value carries a stated error
  bound; when it reaches the rounding boundary a second stage recomputes the
  value in two words at 2^−510. pow, compound and powu compute exact ties
  exactly. The bounds are measured against the models in
  `scripts/fp19/generators/bounds.py`: none reaches 0.67 of its value.
- The edge, rounding toward minus or plus infinity once from the exact
  value: `mulDown`, `mulUp`, `divDown`, `divUp`, `toUintDown`, `toUintUp`,
  `toIntDown`, `toIntUp`, `toFixed18Down`, `toFixed18Up`, `floor`, `ceil`,
  `fromUintDown`, `fromUintUp`; a positive Up result never underflows to
  zero.
- Two objects from one source: FP19 (arithmetic, the edge, exp, ln, log1p,
  expm1, pow, powu, compound, conversions) and FP19X (erf, erfc, normCdf,
  lambertW0, lambertWm1), salts `FP256 v4` and `FP256X v4`; the inline
  library holds all of them. `make predict-fp19x`, `deploy-fp19x-sepolia`,
  `verify-fp19x-sepolia`.
- Gas: the fast paths cost a few hundred gas more; the second stage, when it
  runs, 29k (exp) to 430k (erfc's continued fraction). The optimisation
  pass (fp19-faster, results unchanged word for word): Lambert W by
  fourth-order steps at word precision with a stated bound and the rounding
  test, the wide step only on a miss, 34k / 30k at the median (W0 / W−1;
  151k / 156k before, 109k in release three); `wexpm1` 27k → 21k, so every
  second stage is about 6k cheaper; pow, powu and compound fallbacks
  shorter (p99 80k → 68k, 92k → 73k, 167k → 116k), the pow bound tighter,
  `wln1ps`'s length set by |d|.
- The ops FP127 has and FP19 lacked (#79), each correctly rounded or exact:
  `exp2`, `exp10`, `log2`, `log10`, `log2Up`, `cbrt`, `sinh`, `cosh`,
  `tanh`, `atanh` in FP19X2 (on the same kernels, each with a stated bound
  and a two-word second stage) and `min`, `max`, `clamp`, `avg`, `dist`,
  `zeroFloorSub`, `inv`, `lerp`, `frac`, `round`, `gcd`, `factorial`, `pi`,
  `gavg`, `hypot` in FP19X3 (exact values, or one rounding of an exact
  sum, product or root). `lerp` rounds a + t (b - a) once from the exact
  value, summed in a 1,024-bit window just past the free memory pointer;
  `hypot` rounds Pythagorean ties away from zero; `factorial` runs to 20,366
  and is checked against the exact factorial at every n; `pi(terms)` is the
  correctly rounded Ramanujan partial sum; `round` takes halves away from
  zero. Salts `FP256X2 v4` and `FP256X3 v4`; `make predict-fp19x2`,
  `-fp19x3` and their deploy and verify targets. 67 ops in all.

### Ladder v9

Salt `FP127 ladder v9`, deployed 2026-10-21: the eleven adapters, with
`LadderFP127` calling FP127 v5, `LadderFP127Lib` inlining it and
`LadderFP19` inlining release four, and both runners. The datasets and the
live runners now compute the same code again.

## Blockulator 2.0 (2026-10-16)

Two rulers in one word: FP127 for the money range, FP19 for everything.

| component | version | Sepolia |
|---|---|---|
| FP127 | FP127 v4, 49 ops | `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1` |
| FP19 | FP19 v3, 28 ops | `0x67eFfb11bF93c79a2B12cc7872cBaC12b3eB61be` |
| LadderRunner | FP127 ladder v8 | `0xEf689d3782490066fE911a6dD33357f59caE40fE` |
| EdgeRunner | FP127 ladder v8 | `0x09b8fC41E872279A749a0221AE23D124079AcB44` |

- FP19, a 256-bit binary float: sign, 19-bit exponent, 236-bit fraction,
  about 71 digits from 10^−78,913 to 10^78,913, no NaN or infinity.
  Release three adds log1p, expm1, erf, erfc, normCdf, both Lambert branches,
  powu and compound; exp, ln, log1p, expm1 and the erf family return the
  correctly rounded word at every committed vector.
  In detail (moved here from the site's FP19 page): `exp`, `ln`, `log1p`,
  `expm1`, `erf`, `erfc`, `normCdf` and every non-transcendental op return
  the correctly rounded word at every committed vector. `pow`, `powu` and
  `compound` are within one unit in the last place while |y log2 x| stays
  below about 2^13; the Lambert branches are within two units away from
  −1/e. On random inputs (4,000 to 20,000 per op) `add`, `mul`, `div`,
  `sqrt`, `exp`, `log1p`, `expm1`, `erf` and `erfc` were correctly rounded
  every time; `ln`, `normCdf` and `pow` were one unit off on 1 in 20,000,
  4,000 and 2,500. The kernels run at 2^−254 with 512-bit products: 2^f from
  a 16-entry table and a degree-26 polynomial, log2 from twelve reduction
  stages and a degree-17 polynomial, `erfc` as e^(−y²) times a scaled series
  or continued fraction (never 1 − erf). FP19 v1 borrowed FP127's kernels
  (146, 149 and 123 bits on exp, ln and pow); v2 refit them for the wide
  word; v3 added nine ops.
- FP127 v4: 49 ops, adding powu, compound, log1p, expm1, the hyperbolics,
  erf, erfc and normCdf.
- The ladder (13 scenarios × 10 libraries, N to 10,000) and the edges (139
  one-shot probes) re-run through the live runners with 0 mismatches: the
  9,373 ladder cells a public RPC can execute and all 1,511 edge cells that
  make a call.
- The site: four-item navigation, one results overview, one live-check
  stamp per page.

Records: `contracts/deployments/{FP127,FP19,Ladder}.md`.

## Blockulator 1.0

FP127 as a Huff contract (`0xfae694D0c2c44181791F838c54Ed64C3151FfE30`): 127.128 fixed point on Sepolia, the original
library this release replaces. Its address and the later FP127 versions
stay live and are listed in `contracts/deployments/FP127.md`.

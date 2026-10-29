# Dust is Over: outline

Twenty minutes and slides, for DeFi protocol engineers. This outline sets the order and
the claims. The spoken words are the author's (`dust-is-over.md` is being rewritten
section by section). Every number has a source in this repo, listed under each part.
"Say first" lists the objections the room will raise, answered before anyone has to ask.

Thesis: the failures that cost real money happen where a protocol's numbers meet the
bottom of its ruler. Converging algorithms reach any ruler. BL19 is a ruler that a
one-word format cannot beat by more than three digits, and every op of BL19 v5
returns the nearest word. A new library can be cheaper than these, but it cannot be
more accurate.

---

## Part 1. Real failures (7 min)

### 1.1 One honest transaction is fine (1 min)

- On real mainnet inputs, the WAD libraries keep 9 to 15 digits of the quantity that
  matters, and the error is below one unit of the token. A $1M USDC borrow accrued for
  a day is off by $0.00000012, and USDC's smallest unit is $0.000001. Any correct answer
  rounds to the same token amount.
- So digits are not the problem in an ordinary transaction. They are the problem when
  someone chooses where your numbers sit against the grid: they make the quantity tiny
  and repeat the step.

Source: `docs/benchmarks/accrual-deployed.md`. The Aave USDC borrow control case has 9.51
digits of interest and an error of 1.2×10^-7 USDC. The 39 live Aave borrow sides have a
median of 11.9 digits. A wider real-input study (Balancer v2 quotes, Maker/Sky rpow and
Pendle, block 26,234,952) agrees, but it is not committed. Commit it before quoting it.

### 1.2 Resupply, 26 June 2025 (1.5 min)

- `1e36 / price` with a price of 2.000000000000000000001998×10^36. The answer is 0.5 and
  the integer division floors it to **0**. The loan-to-value check then reads 0, so
  **1 wei** of collateral borrows **10,000,000 reUSD**.
- BL127 and BL19 compute the rate as 0.4999999999999999999995 and the borrow is
  rejected. The honest limit on that collateral was 1.9 reUSD. The real loan-to-value was
  5.26 million times the cap.

Say first:
- **Dividing by the price at the end also fixes it, with no new library.** `divUp`
  blocks it too, but it reads 0.5 as 1 and halves every honest borrower's limit.
- **BL127's port holds this price only below about 170k crvUSD per share. Above that it
  reverts.** BL19 has no such limit.
- **The vault was empty, and a donation set its price.** The floor was the last check
  that failed, not the only one.

Source: `docs/benchmarks/replay-resupply.md` (tx 0xffbbd492…, block 22,785,461).

### 1.3 Bunni v2, 2 September 2025 (1.5 min)

- The stored idle balance was rounded up by up to 1 wei per withdrawal. 44 withdrawals
  took the pool's active USDC from **28 wei to 4**, and liquidity fell **84.37%**. About
  $8.4M was taken.
- Bunni's fix, `mulDivUp`, ends at **48 wei**, 35% too high. Exact arithmetic, BL127 and
  BL19 all end at **35.6278… wei**, and liquidity is unchanged.

Say first:
- **This only works if the balance is stored in the format.** Rounding it to whole wei
  before storing brings the bug back.
- **Bunni's own post-mortem:** "all of the rounding directions involved were safe in
  isolation", and "it's unclear if this change will introduce new attack vectors".

Source: `docs/benchmarks/replay-bunni.md` (tx 0x1c27c4d6…, block 23,273,098).

### 1.4 Balancer V2, 3 November 2025 (1.5 min)

- Upscaling rounded down: 17 × 1.058132408689971699 = 17.988, read as **17**. In the
  osETH pool, all 60 of the 60 micro-swap calls lowered the invariant, to **×0.018**.
  The attack took 11,874 ETH from that pool and 7,153 ETH from wstETH/WETH in this
  transaction. The total loss across chains was over $100M.
- The fix (`mulUp`) stops the attack as it was run, but **30 calls still lower the
  invariant**, through a second rounding: a 1-wei balance worth 1.058 is read as 1.
- With BL127 or BL19 inside and one ceil to wei at the end, **0 of the 165 calls lower
  the invariant**.

Say first:
- **Everyone calls this a rounding-direction bug, and V3's one-word fix is right for
  this attack.** The replay shows what that fix leaves behind. The size of the error,
  10% on one swap, came from the ruler.

Source: `docs/benchmarks/replay-balancer.md` (tx 0x6ed07db1…, block 23,717,397).

### 1.5 The counter-example: Balancer V1, 31 August 2026 (1 min)

- Five V1 pools were drained. One line rounds to the *nearest* raw token unit at a
  balance of 3 satoshi.
- **Perfect maths, rounded to nearest, still nets +7.0% per cycle.** Only rounding
  toward the pool stops it (−0.06%).
- From the four replays, two rules:
  1. **Keep the state in the format.**
  2. **Round toward the protocol, once, at the token edge.**

Source: `docs/benchmarks/replay-balancer-v1.md`.

Do not use: the Compound/Aave-fork empty-market exploits (Hundred, Sonne, Radiant, Raft
and others). A better ruler does not save them.

---

## Part 2. Converge, or fit (6 min)

### 2.1 Two goals (1 min)

1. **Round once:** how you compute.
2. **Never run out of ruler:** what you compute on.

BL127 covers the money range. BL19 covers everything up to its walls at 10^±78,913.

### 2.2 Ramanujan (2 min)

- 1/π = (2√2/9801) Σ (4k)!(1103 + 26390k) / ((k!)^4 396^(4k)). Each term adds about
  **8 digits**: 7.6, 15.7, 23.7 … 71.9 digits at nine terms, in exact arithmetic.
- Run the same recipe through each library's own sqrt, mul and div. Every library
  follows the exact line until it reaches its ruler, then stops:

  | ruler | digits of π reached |
  |---|---|
  | WAD libraries | 16 |
  | binary128 (Quad) | 33 |
  | BL127 | 36 |
  | BL19 | 70 |

- **The series never stops. The ruler does.**

Say first:
- **BL127 reaches 36 digits, not the 39 its grid holds at π.** The constant 2√2/9801 ≈
  2.9×10^-4 sits on an absolute grid and keeps only 35 digits. That is the fixed-point
  trade-off, and it is why BL19 exists.

Source: `docs/benchmarks/pi.md`. The exact-arithmetic column was recomputed at 200 digits.

### 2.3 Back to Balancer: the same iteration on three rulers (1 min)

- Balancer's invariant is a Newton iteration, a converging algorithm. On the wei grid it
  stops at **3.6 to 8.9 digits**. Run it in BL127 and it reaches about **36 to 38**; in
  BL19, **71**. It costs a few extra iterations.
- The algorithm was never the problem. Where it stopped was.

Source: `docs/benchmarks/replay-balancer.md` (the Newton convergence section).

### 2.4 Converge or fit (2 min)

- A converging method (Newton, a series run to its last term, a continued fraction)
  reaches any precision by running longer. A fitted polynomial is stuck at the precision
  it was fitted for.
- BL19 release one is the proof: the converging ops (add, sub, mul, div, Newton sqrt)
  were exact on day one. The ops built on fitted kernels fell short:

  | op | bits | digits |
  |---|---|---|
  | exp | 146 | 44 |
  | ln | 149 | 45 |
  | pow | 123 | 37 |

- Release two refitted them past the end of the word: Chebyshev fits with error below
  2^-262, checked against a 300-digit converging oracle. Exp is now the correctly rounded
  word on 21,913 of 21,913 random inputs.

Say first:
- **BL19's exp and ln are fits, too.** The difference is where the fit stops: past the
  last ruler a single EVM word has. A fit has to be redone for every wider ruler, and
  there is no wider ruler than one word.

Source: `contracts/deployments/BL19.md` and `git show a669484:docs/bl19/precision.md`
for release one; `docs/bl19/precision.md` and `docs/benchmarks/sweep.md` for now.

---

## Part 3. The last library (5 min)

### 3.1 The format ceiling (1.5 min)

- A 256-bit word with an e-bit exponent holds 256 − e bits of significand:

  | exponent bits | digits |
  |---|---|
  | 19 (BL19) | 71.3 |
  | 13 | 73.2 |
  | 9 (just covers uint256) | 74.4 |

- **No one-word format can hold more than about 3 digits more than BL19** over the range
  DeFi uses.
- BL19 spends those bits on range: 10^±78,913, with no walls in any realistic quantity.

Say first:
- **BL19 rounds integers above 2^237** (uint256 reaches 2^256). Token amounts are far
  below that, around 10^27, or 2^90.

### 3.2 The accuracy ceiling (1.5 min)

- **BL19 v5: every one of its 65 ops returns the correctly rounded word, or
  is exact.**
  - **The sweep:** 360,590 seeded random inputs over 53 ops, 0 misrounded. That includes pow,
    compound, ln, normCdf and Lambert W, which release three missed by 1 to 4 marks.
  - **The slow path checked alone:** 0 misrounded with every input forced through the
    second stage.
  - **How it works:** each fast value carries a stated error bound. When the bound reaches
    a rounding boundary, a second stage recomputes the value at 2^-510 and rounds that.
- **BL127 v6:**
  - **Nearest word on every random input tested:** exp, exp2, exp10, expm1, sinh, cosh,
    tanh, ln, log2, log10, pow, cbrt, powu, compound and both Lambert W branches.
  - **Before v5:** exp and pow were off by up to 10^32 and 10^34 marks at large results,
    and cbrt by 10^14.
- **So a new library can be cheaper than these, but it cannot be more accurate.** There
  is no closer value in the word.

Say first:
- **This is the guarantee every correctly rounded maths library gives, not a proof for
  every input.** An input could misround only if its exact value lay within 2^-K of a
  halfway point between two marks:

  | op | K |
  |---|---|
  | exp, ln, pow | about 233 to 268 |
  | erfc (continued fraction) | 155 |
  | Lambert W, at its branch point | 117 |

  No such input is known. For e^x, ln and W, exact ties are ruled out by theorem.
- **BL127's mul, div and sqrt still round down** (div toward zero). That is unchanged
  for compatibility, with directed versions beside them (3.3).
- **Two narrow limits:**
  - BL127's pow is nearest only while |y|·x^y < 2^140, and faithful to 2^170.
  - BL19's powu is not correctly rounded for |n| ≥ 2^237. compound handles any n.

Source: `docs/benchmarks/sweep.md` (BL19 v5 and BL127 v6, deployed in Blockulator 2.2).
`scripts/bl19/generators/bounds.py` checks each stated bound against the Python models
of the Yul. The worst measured error is 0.67 of its bound.

### 3.3 The edge is one call (0.5 min)

- Rule two, round toward the protocol at the token edge, now takes a single call in both
  libraries:
  - **BL19:** `toUintDown`/`Up`, `toIntDown`/`Up`, `toFixed18Down`/`Up`, `mulDown`/`Up`,
    `divDown`/`Up`, `floor` and `ceil`. All exact, with 0 misrounded in the sweep. An
    `Up` result never rounds positive dust to zero.
  - **BL127:** `mulUp`/`Down`, `divUp`/`Down` and `toFixed18Up`/`Down`.
- These are the calls the replays had to build by hand.

### 3.4 What it costs (1 min)

- **Solady is 1.1 to 14 times cheaper per op than BL127, and should be.** Integer-exact
  work (`mulDivUp`, `fullMulDiv`) stays in Solady and OZ; these libraries complement them.
- Median gas per op, inline (BL127 v6 and BL19 v5, as deployed in Blockulator 2.2):

  | op | Solady | PRBMath | BL127 | BL19 |
  |---|---|---|---|---|
  | mul | 126 | 485 | 263 | 530 |
  | div | 93 | 509 | 645 | 800 |
  | exp | 430 | 2,788 | 6,006 | 3,295 |
  | ln | 556 | 828 | 600 | 3,006 |
  | pow | 1,275 | 9,911 | 3,537 | 5,541 |

- BL127 costs less than PRBMath on mul and pow. Since v5 rounds ln to the nearest word,
  it costs 228 gas less than PRBMath's.
- What the premium buys: Resupply's rejected borrow, Bunni's 35.63 wei, and Balancer's
  0 of 165 calls. Set against nine-figure losses, a few thousand gas is the cheapest line
  in the audit.

Say first:
- **Correct rounding costs gas when it is hard.** In BL19 v5:
  - The fast path is a few hundred gas dearer than release three's (exp's median is
    3,299 on the sweep).
  - The second stage, run alone, costs 7,950 (atanh, median) to 411,737 (normCdf, worst)
    gas, and on some ops it runs often enough to show at the 99th percentile:

    | op | median | p99 |
    |---|---|---|
    | pow | 5,902 | 54,522 |
    | compound | 6,304 | 106,018 |

  - Lambert W steps at word precision and takes the wide step only when the rounding
    test fires (0.07% of inputs for W0, 0.20% for W−1): 10,623 and 13,150 median, 41,638
    and 41,433 at worst.
- Budget gas for the p99 if an attacker can choose your inputs.
- **Store ln(index) and each accrual is an exact BL127 `add` (124 gas), with one `exp`
  (6,006) on each read.** After 1,000 accruals the read is within half a unit of 2^-128,
  and the multiplied index is 511 to 546 off. It fits a continuous rate only.

Source: `docs/benchmarks/gas.md` and `gas19.md` (BL127 v6 and BL19 v5; read the
same way as `scripts/talk/deck.py`'s `gas_medians()`); the gas columns of
`docs/benchmarks/sweep.md` (v5); the log-domain run in `test/examples/Integrating.t.sol`
(`forge test --match-test logIndex -vv`).

### 3.5 Why nothing else needs writing (0.5 min)

1. **The format:** no one-word format holds more than 3 digits more than BL19 (3.1).
2. **The accuracy:** every op returns the nearest word, so a rewrite can only be cheaper
   (3.2).
3. **The edge:** directed rounding is one call (3.3).
4. **What is left is not a new library.** It is:
   - gas work inside these two;
   - new ops added to them (the BL19E, BL19H and BL19S split leaves room);
   - deployment, an audit and mainnet.

### 3.6 The ask (0.5 min)

Use BL127 and BL19. They are free, MIT-licensed, and one `forge install` away. Keep the
state in the format, and round toward the protocol at the edge.

**Before the talk:** 3.2 and 3.3 describe BL127 v6 and BL19 v5, deployed on
Sepolia on 2026-10-22 as Blockulator 2.2 and the same code inline through `forge install`,
so "the deployed contract" and "the library" are both true. Slide 17 shows the live
re-check through the ladder v10 runners (2026-10-23: 9,408 + 1,511 cells, 0 mismatches).

---

## Do not say

- "38 digits everywhere" or "between 2^−128 and 2^127". BL127's grid is absolute, so the
  digits are log10(x) + 38.5: 32 at 10^−6, 8 at 10^−30.
- "More digits than any library, including the floats." binary128 beats BL127 below
  3×10^−5.
- "Every op correctly rounded" without the guarantee in 3.2, or for BL127's plain mul,
  div and sqrt, which round down.
- "Proven equal on all of int256." The object and the library are fuzzed against each
  other, not proven equal.
- "Five terms reach the format's floor" for BL127's π.
- "No walls" or "never runs out", without 10^±78,913.
- "43 digits" for release one. It was 44, 45 and 37.
- The Morpho idle market (+3.08 / +2,478) as a library failure. It comes from the
  interest-rate model's trapezoid.
- "Other libraries don't iterate." Solady's sqrt, PRBMath's log2 and Maker's rpow all do.

## Deck changes this outline needs

Done (`make talk`, 18 slides, in the outline's order; titles are placeholders):

1. Title: the WAD drift (ladder.json).
2. 1.1: the Aave USDC control case's error, deployed / BL127 / BL19, against one unit of
   USDC (accrual-deployed.json).
3. 1.2 Resupply: the rate, 0 against 0.4999…, and the loan-to-value against the cap
   (resupply.json, replay-resupply.md).
4. 1.3 Bunni: active USDC over the 44 withdrawals, deployed / mulDivUp / BL127 / exact,
   replayed by `bunni.py`'s `replay` from bunni.json (replay-bunni.md).
5. 1.4 Balancer V2: the true invariant across the osETH phase, deployed / mulUp / BL127 =
   BL19 = exact, with the count of calls that lower it (balancer.json `score`).
6. 1.5 Balancer V1: net per cycle by rounding rule in all five pools (replay-balancer-v1.md).
7–8. 2.1 Two goals: round once (ladder.json); never run out of ruler, with BL19's walls
   at 10^±78,913 on the plot.
9. 2.2 Ramanujan (pi.md).
10. 2.3 Balancer's Newton solve: digits of D at the stop and median iterations, wei grid /
    BL127 / BL19, both pools (balancer.json `score.*.convergence`).
11. 2.4 Converge or fit: caption now says a Taylor polynomial tuned for 60 bits, computed
    with mpmath at each width.
12. 2.4 Release one (exp 146, ln 149, pow 123, read from BL19.md) against now
    (precision.json, sweep.json).
13. 3.1 The format ceiling: digits against exponent bits, computed (19 → 71.3, 13 → 73.2,
    11 → 73.8, 9 → 74.4).
14. 3.2 The accuracy ceiling: BL19's correctly rounded share per op (sweep.json). It reads
    master's sweep, BL19 v5 (deployed in Blockulator 2.2); slide 15's gas reads
    v5's `gas.md` and `gas19.md`.
15. 3.3 What it costs: median gas, Solady / PRBMath / BL127 / BL19 for mul, div, exp, ln,
    pow (gas.md, gas19.md).
16. Both goals met, with the walls stated.
17. Checked on chain (RELEASE.json).
18. 3.5 Use BL127 and BL19: the release name and the BL127 and BL19 addresses from
    RELEASE.json, with BL19E, H and S beneath.

Removed: the Morpho idle-market slides ("Ten million dollars…", "The same calculation…",
"It happens in live markets", "The same market, rounded once"), and the slides the
outline no longer uses (drift on every ruler, the five word layouts, the edges heatmap,
exp end to end, the per-second rate, the option walk, gas against digits on the ladder).
3.4 (what remains) has no slide.

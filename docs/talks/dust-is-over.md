# Dust is Over

> Superseded in order and claims by [`outline.md`](outline.md) (2026-10-20): the opening is now the four replayed exploits, and several numbers below (the Morpho idle market as a library failure, "more digits than anything in the middle", "every op at its grid", release one's "43 digits") are corrected there. This text waits for the author's own words, section by section.

A 20-minute talk, board and slides. Draft 10, 2026-10-16. "Board:" is written
by hand while talking; "Slide:" is projected. Every number is a measured cell;
the card at the end says where each one comes from.

---

## Outline

1. A week of interest (3 min)
2. What dust is (1.5 min)
3. Two goals (3 min)
4. Converge or fit (4 min)
5. The ruler with no ends (3 min)
6. Back to the market (2 min)
7. What it costs (1.5 min)
8. The last library (2 min)

---

## 1. A week of interest

Slide: a lending market. Ten million USDC borrowed. Utilization 100%.

Let's start with something completely ordinary. A lending market, ten million
dollars borrowed, and every dollar that was supplied is lent out. Utilization
is a hundred percent. That happens: a rush of borrowing, or a rush of lenders
trying to leave.

When a market is full, the rate model does what it was designed to do. It
raises the rate, and keeps raising it, to pull lenders back in. This one
started with a target rate of ten percent. Full utilization charges four times
the target, so forty percent a year, and the target itself is climbing.

Now, nobody touches the market for a day. No deposit, no repayment, no
transaction at all. Then somebody does, and the contract catches up: it works
out one day of interest in one step.

Board:

    one day idle      the formula says     11,751.90 USDC
                      the contract books   11,754.98 USDC
                      over by                   3.08

Three dollars on eleven thousand. You might shrug. I'd like you to look at how
many digits of that interest are right: three and a half. On a ten-million-
dollar loan, the interest is right to three and a half digits.

Now leave it a week.

Board:

    seven days idle   the formula says    129,539 USDC
                      the contract books  132,017 USDC
                      over by               2,478

Two thousand four hundred and seventy-eight dollars of interest that the
market's own formula never accrued. Charged to the borrowers, paid to the
lenders. Almost two percent of all the interest, in one step.

I want to be careful here, because the people who built this are good, and some
of them may be in the room. This isn't a bug. I took the contract's own source
at the exact commit that's deployed, compiled it, and checked that it matches
mainnet byte for byte. Then I compared it with what the protocol says it
computes, to two hundred digits. When the market is busy, it's exact to the
cent. In a quiet market at full utilization, a shortcut in the rate model starts
to show. I'll come back to exactly which shortcut.

Here's the same calculation, same inputs, on the two libraries I'm going to
talk about:

Slide:

    digits right in the interest      1 day    7 days
    deployed                           3.6      1.7
    FP127                             30       30
    FP19                             69       70

That's what this talk is about.

## 2. What dust is

Board: `0.000000000000000003`

We have a name for this. Dust. Usually we mean the little bit left in a vault
that nobody can withdraw, or the one wei that makes a transfer revert. But dust
is any rounding that has nowhere to go. It doesn't vanish. It builds up in a
balance, in an index, in a price, every time the math runs.

Board: the title. **Dust is Over.**

I'm going to argue that dust isn't bad luck, and it isn't a bug anybody wrote.
It comes from two decisions every math library makes before anyone writes a line
of code. Get both right and there's nowhere left for dust to come from.

## 3. Two goals

Board:

    1. Round once.                  how you compute
    2. Never run out of ruler.      what you compute on

Two goals. Let's take them one at a time.

**Round once.** Every calculation should be off by at most one mark on the
ruler, at the very end. Not one mark per step. One mark, total.

Let's see why it matters. Ten thousand dollars at ten percent, compounded daily.
One multiply a day: `b = b × (1 + r)`. The rate is 0.1 / 365.

Board:

    r exact   0.000273972602739726027397260273972602...
    r on WAD  0.000273972602739726          ← cut off here

WAD is eighteen decimals, so the rate gets cut off before we start. It's short
by 2.7 × 10⁻²⁰. Times ten thousand dollars, that's 274 units of the last
decimal, short on day one. Day two, 548. It's a straight line: the same
shortfall, paid every single day.

Slide: after one year (N = 365), digits right in the balance

    WAD libraries   16
    64.64           17
    binary128       31
    FP127           36
    FP19           68

**Never run out of ruler.** A ruler has marks, and it has ends. An eighteen-
decimal ruler has its finest mark at 10⁻¹⁸. Anything smaller is zero. Anything
bigger than the top is a revert. Where the money lives, between a millionth and a
trillion, most rulers are fine. But accrual, options and price ticks live at the
ends: rates per second, deep tails, tiny products.

Board, one 256-bit word, drawn three ways:

    WAD       [ ~196 integer bits                  | ~60 fraction bits ]
    FP127     [ s | 127 integer bits         | 128 fraction bits       ]
    FP19     [ s | 19 exponent | 236 fraction bits                    ]

FP127 puts its point in the middle of the word: 128 bits of fraction, so its
finest mark is 3 × 10⁻³⁹. FP19 lets the point move. Nineteen bits say where the
point is and 236 say the digits. That's 71 digits at any size, from 10⁻⁷⁸⁹⁰⁰ to
10⁷⁸⁹⁰⁰. That ruler has no ends.

Those are the two goals. Now: how do you actually reach the first one?

## 4. Converge or fit

There are two ways to compute a function like exp or ln or a square root.

Board:

    fitted       a formula tuned once, for one precision
    converging   a step that corrects the last step's error

A **fitted** formula is a polynomial or a ratio of polynomials, tuned so that on
an eighteen-digit ruler it's right to eighteen digits. It's fast, it's clever,
and that's where it stops. Give it a wider word and you get the same eighteen
digits. It was made for one ruler.

A **converging** algorithm is a step you repeat. Newton's method for a square
root. A series you add up until the terms vanish. A continued fraction you take
as deep as you need. Each step corrects the last one. Give it a wider word and
it just keeps going.

My favorite example is a hundred years old.

Board:

    1/π = (2√2 / 9801) Σ (4k)! (1103 + 26390k) / ((k!)⁴ 396^(4k))

That's Ramanujan's series for pi, from 1914. Each term adds about eight digits.
I computed it with every library's own square root, multiply and divide. Same
integers, same recipe. Let's fill the table in a row at a time.

Slide, built one row at a time:

    terms   WAD    64.64   binary128   FP127   FP19
      1       7      7        7          7       7
      2      15     15       15         15      15
      3      16     17       23         23      23
      4      16     17       31         31      31
      5      16     17       33         36      39
      6      16     17       33         36      47
      7      16     17       33         36      55
      8      16     17       33         36      63
      9      16     17       33         36      70

Watch the columns drop out. At three terms the WAD rulers have run out: sixteen
digits, and the series has more to give. At five, binary128 stops at thirty-three
and FP127 stops at thirty-six. FP19 keeps going, eight digits a term, until it
reaches seventy at nine terms.

The algorithm never got stuck. Ramanujan's series could have given every
column seventy digits. Only the ruler said no.

And here's how I know converging is the right way to build, because I learned it
the hard way. When I first built FP19, I reused FP127's code. Everything
that converges, the multiply, the divide, the Newton square root, was exact to
the last bit on day one. Nothing to tune. The only functions that fell
short were exp, ln and pow, because FP127's versions are fitted polynomials,
fitted for 128 bits.

Slide:

    exp at the edges        release one    release two
    FP19 digits                43             71

Forty-three digits, stuck, until I refitted them for the wide word. The
converging code needed nothing.

So: build out of steps that correct themselves, keep extra bits while they run,
and round once at the end. That's goal one.

## 5. The ruler with no ends

Now goal two. I built a second table. Not N steps of one thing: one call of each
function, right at the end of its domain. Each library, in its own format,
against two hundred digits of truth.

Slide, the legend:

    zero     the answer fell below the finest mark
    revert   the library refused

Slide:

    one call                   truth      WAD      64.64    binary128   FP127   FP19
    ln(1 + 1e-9)               1e-9         9        10        25         30      62
    exp(-40)                   4.2e-18      1         2        32         21      71
    exp(-42)                   5.7e-19   zero         1        32         21      71
    1e-10 × 1e-10              1e-20     zero      zero        34         18      71
    normCdf(-9)                1.1e-19   zero         1        31         21      71
    1.0001 ^ -887272           2.9e-39   zero      zero        29          4      65
    1.0001 ^ +887272           3.4e38      12    revert        29     revert      65
    exp(-89)                   2.2e-39   zero      zero        31       zero      71
    sqrt(1e-30)                1e-15     zero      zero        34          8      71

Three of those rows are money.

**A per-second rate.** Five percent a year is 1.6 × 10⁻⁹ per second. Take its
logarithm on an eighteen-decimal ruler and you have nine digits before anything
else happens.

**A probability below 10⁻¹⁸.** exp(−42) is the chance of a nine-sigma move,
the discount on a very long bond, the weight of a very old sample. On the WAD
ruler it's zero, and so is everything you build on it.

**A fee on a fee.** 10⁻¹⁰ times 10⁻¹⁰ is zero on both fixed rulers and
seventy-one digits on FP19.

Look at the FP127 column too, because I want to be fair to my own work. FP127
has more digits than anything in the middle of the number line. At the ends it
has walls, like every fixed point. exp(−89) is below its finest mark.
1.0001^887272, the very top of the price-tick range, is above its biggest
number, by the one bit the sign took.

Then the last column. No zero, no revert, anywhere on the table. The ruler with
no ends.

One more, because options protocols are in the room. Price an option with the
normal distribution and walk the price down a tick at a time, ten thousand
ticks.

Slide:

    the option, 10,000 ticks down    WAD    binary128   FP127   FP19
    d₁ = −7                            4       28         25      66
    d₁ = −12                           0       27          3      66

At minus twelve the WAD option is worth zero, and FP127 is down to three digits,
because the answer is a few marks above its floor. FP19 has sixty-six.

## 6. Back to the market

Now let's go back to the market we started with, and see which shortcut it was.

When the market sits idle, the contract has to work out the average rate over
the gap. But the rate was climbing the whole time. The exact answer is an
integral of a curve. The contract estimates it from a couple of points on that
curve. That's a fitted step: a trapezoid. It's fine over a few minutes. Over a
day it's three dollars off, and over a week it's two and a half thousand.

That's the same lesson as the pi table. The curve has an exact formula, and so
does the area under it. Compute that, keep the extra bits, round once, on a wide
enough ruler, and you get the formula's own answer:

Slide, again:

    digits right in the interest      1 day    7 days
    deployed                           3.6      1.7
    FP127                             30       30
    FP19                             69       70

Thirty digits on FP127. Seventy on FP19. Same formula, same inputs. Round once,
on a ruler with no ends.

## 7. What it costs

Slide, gas, inline:

    op           WAD     FP127    FP19
    mul           126      263      530
    add           111      124      662
    sqrt          393    1,025    1,205
    ln            556      600    3,006
    exp           430    6,006    3,295
    pow         1,275    3,537    5,541
    normCdf         —   11,512   23,108

Cheaper math is cheaper because it gives up digits. Every row on this slide, the
cheap column included, is in the tables you've just seen, so you know exactly
which digits it gave up. And every function here is a view: called off chain,
it's an eth_call and costs nothing.

## 8. The last library

Board, the two goals:

    1. Round once.                  ✓  converging algorithms, extra bits, one rounding
    2. Never run out of ruler.      ✓  FP127 for the money, FP19 for everything

That's the whole job. Once every answer is the nearest mark on a ruler with no
ends, there's nothing left to improve but gas. There won't be a better answer,
because there isn't a better answer.

Both are on chain. Every cell of the step table and the edges table, nearly
eleven thousand of them, was re-run against the live contracts on Sepolia today. It's called Blockulator 2.2.

Use FP127 and FP19. Stop using the others.

Thank you.

---

## Card

| claim | value | source |
|---|---|---|
| the market, 1 day | 10M USDC, utilization 100%, target 10%: truth 11,751.9, deployed +3.08 USDC, 3.58 digits; FP127 30.29, FP19 68.54 | accrual-deployed: morpho-u100-10pct-1d |
| the market, 7 days | truth 129,539.0, deployed +2,478.09 USDC (1.9%), 1.72 digits; FP127 30.29, FP19 70.0 | accrual-deployed: morpho-u100-10pct-7d |
| why | the rate model's trapezoid over the idle gap (+4.60 at 1 day, +2,488 at 7 days); series and grids are millionths | accrual-deployed |
| "exact when busy" | lending borrow index within the token's decimals at max rate for a day; rate model at its 90% target 9–10 digits | accrual-deployed: summary |
| deployed code | pinned at the deployed tags, runtime equal to mainnet for 8 contracts | accrual-deployed: provenance; make accrual-verify |
| rate on WAD | 0.000273972602739726, short 2.7e-20, 274 units a day | exact |
| compound N = 365 | WAD 16, 64.64 17, binary128 31, FP127 36, FP19 68 | ladder: compound, reference |
| Ramanujan | WAD 16 from term 3, 64.64 17, binary128 33 from term 5, FP127 36 from term 5, FP19 70 at term 9 | pi.md |
| FP19 release one vs two | exp at the edges 43 → 71; release one held 146 / 149 / 123 bits on exp / ln / pow | FP19.md, edges |
| edges table | each row as shown; zero = below the finest mark; revert = the library refused | edges: ln, exp, mul, normCdf, pow, sqrt |
| per-second rate | 5% / 31,536,000 = 1.59e-9 | exact |
| option walk | d₁ = −7: WAD 4, binary128 28, FP127 25, FP19 66; d₁ = −12: WAD 0, binary128 27, FP127 3, FP19 66 | ladder: deep-tail-option, slow-walk / reference, N = 10,000 |
| gas | WAD (Solady) mul 126, add 111, sqrt 393, ln 556, exp 430, pow 1,275; FP127Lib 263 / 124 / 1,025 / 600 / 6,006 / 3,537, normCdf 11,512; FP19Lib 530 / 662 / 1,205 / 3,006 / 3,295 / 5,541, normCdf 23,108 | gas.md, gas19.md (inline medians) |
| FP19 format | 1 + 19 + 236 bits, 237-bit significand, ~71 digits, 10^±78,913 | contracts/src/fp19/README.md |
| live check | Blockulator 2.2 (2026-10-23, ladder v10 runners): 9,408 ladder cells + 1,511 edge cells, 0 mismatches | RELEASE.json |
| addresses | Blockulator 2.2: FP127 v6 0xb349DB36…CBe4, FP19 0xAa1f71B7…eb52 (+ FP19E 0x017F68A5…9AE2, H 0xEfefa2B6…59A5, S 0x73E8809F…42F4) | RELEASE.md |

# The War on Dust is Nearly Over

A 20-minute whiteboard talk. Draft 8, 2026-10-15. Two goals, one ruler, the ends of
the ruler, and the ruler after it. Every number is a cell in `docs/benchmarks/ladder.json`
(scenario, input, N in brackets), `docs/benchmarks/edges.json` (op and probe),
`docs/benchmarks/pi.md`, `docs/benchmarks/gas.json`, or exact arithmetic. "Board:" lines
are what gets written; the prose is what gets said.

---

## Outline

1. Dust (1 min)
2. Two goals (1.5 min)
3. One word, four rulers (2.5 min)
4. Goal one, kept: the slope (3 min)
5. The ends of the ruler (5 min)
6. What the money runs on (3 min)
7. The fourth recipe (2 min)
8. Cost (1 min)
9. Nearly over (1 min)

---

## 1. Dust

Board: `0.000000000000000003`

Show of hands: who has shipped a contract that couldn't close because a tiny bit of
money was left in it? Who shipped one that reverted instead? Applaud these people,
they're honest.

That's dust. Rounding, repeated every block, piling up in a corner nobody can sweep.

Board: the title.

Last year I showed you a library and said the math was finished. This year I measured
it against everything the money actually runs on, and I want to tell you where it won,
where it lost, and why the war is nearly over rather than over.

## 2. Two goals

Board:

    1. every answer as exact as the ruler allows      iterate, round once
    2. as much number as one word can hold           where the point goes

Two goals, and they're different goals. The first is about the recipe: a guess and a
correction, and one rounding at the end instead of one at every step. The second is about
the container: a 256-bit word, and what you spend the bits on.

I'll show you the first goal is kept. Then I'll show you the second one has walls, and
that the measurement tells us where the next wall is.

## 3. One word, four rulers

Board: one 256-bit word, drawn four times.

    ABDK 64.64    [ idle 128                ][ 64 int   | 64 frac  ]
    WAD int256    [ ~196 int                           | ~60 frac  ]
    FP127 127.128 [ s | 127 int             | 128 frac             ]
    Quad binary128[ idle 128                ][ s | 15 exp | 112 mantissa ]

Every contract stores a number in the same word. The first three put a point somewhere
and call everything to the right of it the fraction. That's a fixed point: the grid is
the same everywhere. WAD's grid is 10⁻¹⁸. ABDK's is 2⁻⁶⁴, 5 × 10⁻²⁰. FP127's is 2⁻¹²⁸,
3 × 10⁻³⁹.

The fourth one is different. Quad is IEEE binary128, a float: 15 bits say where the
point is, 113 bits say the digits. The grid moves with the value. It's always 34 digits,
whether the number is 10⁻³⁰ or 10³⁰.

Board:

    fixed point:  absolute precision     a ruler with marks every 2^-128
    float:        relative precision     a ruler that rescales to the value

Hold that distinction. The whole talk is in it. A fixed point is as good as its grid
where the values are, and no good at all past the ends. A float is as good as its
mantissa everywhere, and no better anywhere. FP127 has 128 bits of fraction; Quad has
113 bits of mantissa. Where the money lives, between a millionth and a trillion, we have
more. Past the ends, they do.

## 4. Goal one, kept: the slope

Board: `b = b × (1 + r)`, `b₀ = 10000`, `r = 0.1 / 365`

The most common calculation in DeFi. Ten thousand dollars at ten percent, daily, one
multiply a day. Write the rate out.

Board:

    r exact   = 0.000273972602739726027397260273972602739726...
    r on WAD  = 0.000273972602739726          cut off 2.7 × 10⁻²⁰
    r on 2^128 = 0.000273972602739726027397260273972602739726   cut off 1.4 × 10⁻³⁹

Board, the balances after a year, digits correct:

    WAD      16 digits     110,688 units low      274 a day, every day
    ABDK     17
    Quad     31
    FP127    36            and 40 against its own rounded rate

[compound, reference, N = 365] Sixteen digits of eleven thousand dollars is a thousandth
of a cent, and across a million accounts it's where the dust comes from. The FP127
answer is forty digits if you start the exact arithmetic from the rate it was actually
given: every digit lost all year was day zero's rounding. The multiplications lost
nothing.

And look at Quad: thirty-one. It started at thirty-three on day one and gave up two.
A float rounds to its mantissa at every operation, and the roundings walk. The fixed
point rounded once, at the rate, and then every product was exact. That's goal one.

Board: `guess → correct → guess → correct`

The transcendentals keep it the same way. Last year `exp` and `ln` floored every step;
`exp(ln(x))` came back eight units low every call, and after ten thousand calls it was
sixty-five thousand units low. Two lines fixed it: compute at 192 bits, round to nearest
once. Now the round trip returns the same word at every N. [roundtrip, reference, N =
10,000: FP127 38 digits; Quad 29]

Board, the same recipe through four rulers:

    Ramanujan's series for pi, five terms, each library's own sqrt, mul, div
    FP127 36   Quad 33   ABDK 17   Solady 16   PRBMath 16   Balancer 16

[pi.md] Same integers, same recipe. The ruler decides. That's the slope story and it's
the gentle one: no villain, no cleverness, just where the point goes and whether you
round once.

## 5. The ends of the ruler

Now the part that changed what I think.

I built a second table. Not N steps of one thing; one call of each thing, at the end of
its domain. Where a logarithm is within a per-second rate of one. Where an exponential
is minus forty. Where a probability is below one in 10¹⁸. Each library, in its own
representation, one call, against two hundred digits of truth. Each cell either has
digits, or says how the library had no answer.

Board, the legend:

    zero    the result fell below the floor
    revert  the library refused
    range   the input doesn't fit the word
    n/a     the library can't compute it

Board, the table. Write it slowly.

    probe                     truth        WAD      ABDK    FP127   Quad
    ln(1 + 1e-9)              1e-9          8 dig    10      30      25
    exp(-40)                  4.2e-18       1 dig     2      21      32
    exp(-42)                  5.7e-19       zero      1      21      32
    1e-10 × 1e-10             1e-20         zero    zero     18      34
    normCdf(-9)               1.1e-19       zero      1      21      31
    1.0001 ^ -887272          2.9e-39       zero    zero      4      29
    1.0001 ^ +887272          3.4e38        12     revert  revert   29
    exp(-89)                  2.2e-39       zero    zero    zero    31
    exp(89)                   4.5e38        20     revert  revert   31
    sqrt(1e-30)               1e-15         zero    zero      8     34

[edges: ln, exp, mul, normCdf, pow, sqrt]

Three of those rows are money.

**A per-second rate.** Five percent a year is 1.6 × 10⁻⁹ a second. On an 18-decimal
grid that rate has ten digits before anything is done with it, and its logarithm has
eight. Raise it to a year of seconds and you get ten digits of balance. [accrual-per-
second, reference, N = 365: WAD 10, PRBMath 9, FP127 31, Quad 26]

**A probability below 10⁻¹⁸.** exp(−42) is the chance of a nine-sigma move, the discount
on a very long bond, the weight of a very old sample. On the grid it's zero. At exp(−40)
it's one digit. Nothing you build on it has more digits than it does.

**Tiny times tiny.** A fee on a fee. 10⁻¹⁰ times 10⁻¹⁰ is zero on every grid but ours,
and on ours it has eighteen digits, because the grid is at 10⁻³⁹.

Now the two rows I wrote for myself. exp(−89) is zero on FP127's grid, and exp(89)
reverts, because 2¹²⁷ is 1.7 × 10³⁸ and e⁸⁹ is 4.5 × 10³⁸. And here's one I didn't
expect: Uniswap chose its tick range so that price spans exactly 2⁻¹²⁸ to 2¹²⁸.
1.0001^887272 is 3.4026 × 10³⁸. 2¹²⁸ is 3.4028 × 10³⁸. An unsigned 128.128 word would
hold Uniswap's last tick; our signed 127.128 does not, by the one bit the sign took.
The ends of our ruler are real.

Board:

    FP127's walls:  2^-128 below,  2^127 above
    inside them:    more digits than anything
    outside them:   zero or revert, like everyone else

And then the Quad column. Twenty-nine to thirty-four, every row, no zero, no revert. Not
because it's cleverer. Because its point moves. Where our 1e-30 is 3.4 × 10⁸ grid steps,
eight digits, Quad's is 1.0 × 2⁻¹⁰⁰ with 113 bits of mantissa, thirty-four digits. The
float has no walls. It also has fewer digits in the middle, rounds at every op, and uses
half the word. That is the trade, and now it's measured.

## 6. What the money runs on

Board:

    Aave      1 + x + x²/2 + x³/6     x = rate × years      RAY, 27 decimals
    Morpho    x + x²/2 + x³/6         x = rate/sec × seconds, WAD
    Maker     rpow(1 + r, n)          squaring, rounds half-up every step, RAY
    Uniswap   1.0001^tick             Q64.96, range 2^±128

These are the accrual formulas of the four protocols most of the money sits in, run
through the same ladder, judged against the model each one says it approximates.

Board:

    continuous accrual at 5%, one idle year:   Aave 6 digits   Morpho 6   FP127 38   Quad 33
    27 idle years (N = 10,000):                 Aave 1          Morpho 1   FP127 37   Quad 33
    daily compounding, 10,000 days:             Maker 23        WAD 15     FP127 34   Quad 29

[accrual-continuous, reference, N = 365 and 10,000; compound, reference, N = 10,000]

Aave's own comment says the expansion "slightly underpays liquidity providers and
undercharges borrowers". It's right: the error is x⁴/24, invisible when the market is
touched every block, six digits at a year idle, everything at twenty-seven. Morpho has
the same three terms and one more loss before them: the rate per second in eighteen
decimals, 1,585,489,599 wei at five percent, ten digits before any arithmetic. Maker's
rpow is the honest one of the three: exact squaring, half-up rounding, twenty-three
digits of twenty-seven after ten thousand days. None of these are mistakes. Each is
right for the interval it was built for. The table just says where the interval ends.

## 7. The fourth recipe

Board: `N(d) = erfc(−d/√2) / 2`

Options protocols price with the normal distribution function, and the spot walks. Here's
the recipe, and it's the one from section four again: the series where it converges fast,
a continued fraction where it doesn't, e^(−x²) kept at 192 bits so the tail keeps its
digits, round once.

Board:

    |x| ≤ 4:   erf  = (2/√π) e^(-x²) x Σ (2x²)^k / (2k+1)!!      ~125 terms, all positive
    |x| > 4:   erfc = e^(-x²) / (√π (x + ½/(x + 1/(x + 3/2/(x + ...)))))   depth 1700/x² + 10

I ran that same recipe through every other library's own exp, sqrt, mul and div, with
pi by Ramanujan through the same ops, so each is judged on its primitives. Then I
walked an at-the-money option down a tick at a time and priced it.

Board:

    spot walks to d₁ = −7:    WAD 4 digits    FP127 25    Quad 28
    spot walks to d₁ = −12:   WAD zero        FP127 3     Quad 27

[deep-tail-option, slow-walk and reference, N = 10,000] At minus seven, an 18-decimal
N(d) has four digits left. At minus twelve, it's zero, and so is the option. And at
minus twelve FP127 has three, because N(−12) is 1.8 × 10⁻³³, a handful of grid steps.
That's the wall again, from the other side. Quad has twenty-seven.

## 8. Cost

Board:

    gas, inline       FP127    Quad     Solady
    mul                 531    1,036      321
    add                 289    1,252      502
    ln                1,035    1,927      731
    exp               5,366    6,072      547
    pow               6,654   23,879    1,605
    compound(r, n)    4,573       —        —
    normCdf          23,487       —        —

[gas.json] Multiply costs what a multiply costs. The float pays for its moving point on
every add, because two exponents have to be aligned before anything happens, and pays
four times on pow. Every function here is a view: off chain it's an eth_call and costs
nothing. If you multiply once and settle, keep using WAD. If the output feeds the next
input, this is what the gas buys.

## 9. Nearly over

Board, the two goals again:

    1. every answer as exact as the ruler allows      kept: iterate, round once
    2. as much number as one word can hold           kept in the middle; walls at the ends

Goal one is finished. Every op in the library sits on its grid, and you can check any
cell of either table on chain with one call.

Goal two is finished for the middle of the number line, which is where the money is.
But I measured the ends now, and the ends say something specific. A fixed point spends
127 bits on a range nobody uses and still has walls. A float with half the word has no
walls and four fewer digits. The other half of that word is idle.

Board:

    [ s | ~20 exp | ~235 mantissa ]      70 digits, no walls, one word

That's the next ruler. Seventy digits at any magnitude, and every kernel in FP127 is
already a mantissa engine; the integer power routine computes exactly this pair, a
256-bit mantissa and an exponent, before it rounds back to the grid. What a float costs
is an add that aligns exponents. That's the last piece.

So: put the point where the values are, iterate, round once. That ended the dust in
the middle. The ends are measured, and the ruler that covers them is the same code
with a moving point. The war on dust is nearly over.

Thank you.

---

## Card

| claim | value | source |
|---|---|---|
| rate on WAD | 0.000273972602739726, short 2.7e-20 | exact |
| compound N = 365 | WAD 16 (110,688 units low), ABDK 17, Quad 31 (33 at N = 1), FP127 36 / 40 vs own rate | ladder: compound, reference |
| round trip N = 10,000 | FP127 38, Quad 29; v1 history −8 units a call | ladder: roundtrip, reference |
| pi, five terms | FP127 36, Quad 33, ABDK 17, Solady/PRB/Balancer 16 | pi.md |
| ln(1+1e-9) | WAD 8–9, ABDK 10, FP127 30, Quad 25 | edges: ln |
| exp(−40) / exp(−42) | WAD 1 / zero; FP127 21; Quad 32 | edges: exp |
| 1e-10 × 1e-10 | zero on WAD and ABDK; FP127 18; Quad 34 | edges: mul |
| normCdf(−9) | WAD zero, ABDK 1, FP127 21, Quad 31 | edges: normCdf |
| 1.0001^±887272 | +: WAD 12, FP127 revert, Quad 29; −: WAD zero, FP127 4 | edges: pow |
| 2^128 vs top tick | 3.4028e38 vs 3.4026e38 | exact |
| exp(−89), exp(89) | FP127 zero / revert; Solady 20 at 89 | edges: exp |
| sqrt(1e-30) | WAD zero, FP127 8, Quad 34 | edges: sqrt |
| per-second accrual N = 365 | WAD 10, PRB 9, Maker 19, FP127 31, Quad 26 | ladder: accrual-per-second, reference |
| continuous accrual | Aave/Morpho 6 at N = 365, 1 at 10,000; FP127 38/37; Quad 33 | ladder: accrual-continuous, reference |
| daily compounding N = 10,000 | Maker 23, WAD 15, FP127 34, Quad 29 | ladder: compound, reference |
| Morpho's per-second rate | 1,585,489,599 wei at 5% APR | exact |
| option walk | d₁ = −7: WAD 4, FP127 25, Quad 28; d₁ = −12: WAD 0, FP127 3, Quad 27 | ladder: deep-tail-option, slow-walk / reference, N = 10,000 |
| erf recipe | series to 4, ~125 terms; fraction depth 1700/⌊x²⌋ + 10; 145 bits | erf_model.py |
| gas | mul 531/1,036/321; add 289/1,252/502; ln 1,035/1,927/731; exp 5,366/6,072/547; pow 6,654/23,879/1,605; compound 4,573; normCdf 23,487 | gas.json (lib / quad / solady medians) |
| binary128 | 1 + 15 + 112 bits, 113-bit significand, ~34 digits | IEEE 754 |

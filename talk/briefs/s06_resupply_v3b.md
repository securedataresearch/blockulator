# s06_resupply v3b — make the mechanism visible: the rate drives the check

The user on v3 (2026-10-29): "it's almost clear what's happening with the one share being able to take all the liquidity based on the rounding error. i understand what's happening but these animations just barely dont quite convey it."

What v3 lacks: the link between the ball landing on 0 and the gate opening is only a line of text on the gate. The audience must SEE the rate feed the solvency check, the zero kill the check, and the whole pool leave against one share. Three changes; everything else in v3 stays (vocabulary, numbers(), SECTIONS, claims V12/C1).

## 1. A `Gauge` drives the gate (new vocab3d primitive)
A dial standing beside the lattice: an arc from 0 to the limit `95,000` (the `maxLTV` in the contract's own units, from numbers()) in EMERALD, continuing past it in RED, a needle, and a readout billboard. The needle's angle is a function of three inputs drawn as three small input bars under the dial: `borrow 10,000,000`, `rate` (wired to the ball's x on the lattice by a thin EMERALD/RED line from the ball to the dial), `collateral 1 share`. The readout shows the LTV formula result: `10,000,000 × 0 / 1 = 0` in the check section and `499,999,999,999.9999999995004995` in the half section (the existing strings). The gate is now physically behind the dial: it lifts when the needle is in the green arc and drops when it is in the red.

## 2. The check section tells cause → effect in order, with a beat between
1. The ball is at 0 (RED, from the floor section). A wire draws from the ball to the dial's `rate` input: the input bar collapses to 0 (0.6 s).
2. The needle swings from a resting position to 0 (0.8 s); the readout counts `10,000,000 × 0 / 1 = 0`; the green arc glows; `≤ 95,000` appears beside the limit mark. HOLD 1 s: this is the moment.
3. The gate lifts (EMERALD, check_mark).
4. The pool pours: the `reUSD` tank (large; label `10,000,000 reUSD · the pool`) drains to EMPTY into the attacker's tank, which starts small and GROWS as it fills (scale the attacker's tank to the same volume by the end), while the `1 share` block sits at the collateral input, unchanged, labelled `collateral: 1 share-wei`. The contrast block-vs-tank is the punchline; the pour takes 3 s and the camera orbits a quarter turn during it.

## 3. The half section is the counterfactual on the same gauge
1. The ball lifts back to 0.4999… (white); the wire re-draws; the `rate` input bar rises.
2. The needle swings hard past the limit into the red and pins at the end of the arc; the readout shows `499,999,999,999.9999999995004995 > 95,000`; a bracket along the red arc reads `5,263,158× the limit` (the multiplier, HERO, now here rather than in a separate beat).
3. The gate drops (RED, cross_mark); the pool tank stays full (no pour); `insolvent`.
The `multiplier` section then only dims everything but the gauge and its bracket (the slide's poster: the gauge pinned in the red, the gate shut, the pool untouched).

## Text budget
Per held frame still: title, caption, labels on objects. The gauge readout is the one sentence-like string and it is a number. The limit `95,000` and the labels `borrow`, `rate`, `collateral`, `the pool` are LITERALS (C1/V12) or numbers() values.

## Acceptance
check.py's s06 expectation unchanged except the new strings (`the pool`, `collateral: 1 share-wei`, the three input labels) in LITERALS with C1; sections and numbers() as before; -qh render; six held frames; the `check` held frame shows the needle at 0, the gate up and the pool draining; the `half` held frame shows the needle pinned red and the gate down.

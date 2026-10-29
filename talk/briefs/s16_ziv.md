# Brief: s16_ziv — "What correct costs"

## 1. Slide and line
Slide 16 of 19. Title on the slide: **What correct costs**.
Script (verbatim, script-v2 §16): "On the EVM a multiply is five gas and a wide division four hundred. Ziv's technique: a fast value with a derived bound; test whether the bound could change the rounding; only then recompute. For exp, that happens once in twenty-two thousand calls."
Claims: V32 (MUL 5 gas: the EVM fee schedule; the 512-by-256-bit division 393 gas: contracts/src/fp19/README.md:181 "divh"), V21 (Ziv's technique in both libraries: fast value with a derived bound, tested before the one rounding, a wider stage behind it), V18 (FP19 exp: 1 fallback in 21,913 sweep inputs; FP127 exp: 0 fallbacks), V19 (FP127 exp typical inline 2,716 → 2,835 gas for the rounding test, +4.4%).

## 2. Takeaway
Correct rounding costs one test, a few percent of gas; the expensive recompute almost never runs.
Closing line: **FP127 exp: 2,716 → 2,835 gas with the test · the last stage: 0 of 3,963 inputs** (both halves from `numbers()`; see flags on 3,963).

## 3. Data and strings
Loaders: `sweep("fp19", "exp")` and `sweep("fp127", "exp")` (docs/benchmarks/sweep.json rows: `n`, `fallback`), `gas("exp")` (docs/benchmarks/gas.json: FP127 typical inline median, expected 2,835). The pre-test figure 2,716 is not in any JSON (it is contracts/deployments/FP127.md's "typical inline gas exp 5,360 → 2,716"); it is a LITERAL with id V19. The opcode prices are LITERALS with id V32.

| string | where | claim id | source |
|---|---|---|---|
| `MUL · 5 gas` | section 0, small coin | V32 | fee schedule |
| `512-by-256-bit division · 393 gas` | section 0, big coin | V32 | fp19 README divh |
| `a fast value, with a bound derived in the source` | section 1 | V21 | essay §8 step 1 |
| `could the bound change the rounding?` | section 1–2 | V21 | essay §8 step 2 |
| `no → round` with `check_mark()` | section 1 | V21 | — |
| `yes → recompute at higher precision` | section 2–3 | V21 | essay §8 step 3 |
| `FP19 exp: 1 of 21,913 inputs reached the last stage` | section 4 | V18 | sweep fp19 exp n, fallback |
| `FP127 exp: 0 of 3,963 inputs` | section 4 | V18 | sweep fp127 exp n, fallback |
| `FP127 exp: 2,716 → 2,835 gas with the test` | section 4 / closing | V19 | 2,716 LITERAL; 2,835 from gas() |
| `+4.4%` | section 4 | V19 | computed from the two |

The grid in sections 1–3 has NO numeric labels: the fast value, its bound and the midpoint are illustrative positions. Nothing on the grid is a claim.

## 4. Sections
| i | name | what appears | persists | spoken over it | held frame | s |
|---|---|---|---|---|---|---|
| 0 | `prices` | title; two circles sized by gas (area ∝ gas: MUL tiny, the division ≈ 79× the area) with their labels; the big one lands with weight | — | "On the EVM a multiply is five gas and a wide division four hundred." | the two coins | 5 |
| 1 | `fast` | the coins shrink to the top-right; a `GridLine` with two ticks and a dashed midpoint line between them (new helper `midpoint(line, a, b)`); a white dot (the fast value) appears with an `error_bar()` (new primitive: a horizontal bracket centred on the dot, EMERALD when it clears, RED when it crosses) that does not reach the midpoint; label step 1 and step 2; `no → round`: the dot `snap()`s to the nearer tick in EMERALD with `check_mark()` | coins | "Ziv's technique: a fast value with a derived bound; test whether the bound could change the rounding;" | a rounded value | 9 |
| 2 | `crosses` | a second dot appears on the same grid, its bar straddling the midpoint; the bar turns RED; `yes → recompute at higher precision` | coins, grid, first result dimmed | "only then recompute." | the straddling bar | 5 |
| 3 | `recompute` | the grid stretches (grid-stretch, not camera) around the midpoint ×8; the bar shrinks in two steps (the wider stage) until it clears; turns EMERALD; the dot `snap()`s with `check_mark()` | coins | (pause) | the cleared bar | 7 |
| 4 | `counters` | the grid dims; two counters tick up from 0: `1 of 21,913` (FP19 exp) and `0 of 3,963` (FP127 exp), each labelled with its library and `inputs reached the last stage`; then the gas line `2,716 → 2,835` with `+4.4%` and a small `glow_bar()` | — | "For exp, that happens once in twenty-two thousand calls." | counters + gas line | 8 |
| 5 | `closing` | the closing line in `glow_bar()`; hold 3 s | counters | (pause) | closing | 4 |

## 5. Vocabulary
`GridLine`, `snap()`, `check_mark()`, `glow_bar()`, `Circle`s for coins; new primitives `error_bar(dot, half_width, colour)` and `midpoint(line, a, b)` in vocab.py. White = EXACT (the fast values); EMERALD = a bound that clears and the rounded result; RED = a bound that crosses.

## 6. Hero
The cleared bar in section 3 (EMERALD, `check_mark()`); the FP127 `0 of 3,963` counter in section 4 with `halo()`.

## 7. Legibility
Counters at HERO size; labels at BODY; the coins' labels at BODY. The grid has no digit labels.

## 8. Flags
- Every figure carries its library's name: the fallback rate is FP19's, the gas delta is FP127's. Never mix them in one sentence.
- "inputs" on screen; the script says "calls" (the ledger's V18 wording accepts both).
- The FP127 exp row's `n` is 3,963 scored inputs (37 both-revert inputs unscored) of 4,000 generated; the ledger's V18 is worded for this: draw `n` from the row.
- 2,716 is a LITERAL (V19); if `gas("exp")` does not give 2,835, report, don't adjust.

## 9. Acceptance
`SECTIONS = ("prices", "fast", "crosses", "recompute", "counters", "closing")`; `numbers()` returns both sweep rows' n and fallback, the gas median, the percentage; `check.py` reads the sweep rows and gas.json by a second path and recomputes the percentage; `-ql` render; six held-frame PNGs.

## 10. Deliverables and report
Per RULES.md.

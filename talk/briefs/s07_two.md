# Brief: s07_two — "Two failures, one decision" (all five incidents, one row each)

## 1. Slide and line
Slide 7 of 19. Title on the slide: **Two failures, one decision**.
Script (verbatim, script-v2 §7): "Resupply rounded too early. Bunni and Balancer V2 rounded too often: carry the exact value and round once, and the attack stops. Thetanuts and Balancer V1 rounded at a unit, where no precision helps and only the direction decides who pays. Inside a calculation, precision shrinks error. At a unit, direction decides who pays."
Claims: C1 (Resupply), C2 (Bunni), C3 (Balancer V2), C4 (Thetanuts), C5 (Balancer V1), C8 (Thetanuts ceil counterfactual, off-chain), C9/V27 (Balancer V1 rounds to NEAREST; Resupply floored ONCE), V12 (Resupply figures). All in research_notes/talk/verify-C.md and claims.md (read-only, in the master checkout /home/s/Projects/blockulator).

## 2. Takeaway
Three incidents rounded too early or too often (fixable by carrying the exact value and rounding once); two rounded at a unit (only the direction can fix them).
Closing line (verbatim, the box line): **Inside a calculation, precision shrinks error. At a unit, direction decides who pays.**

## 3. Data and strings
Loaders: `incidents()` (names, dates, order), `resupply()` (pins; reuse `s06_resupply.numbers()` for the rate: import it, don't recompute differently), `bunni_replay()` / the raw `scripts/replays/bunni.json` steps, `balancer()` (`scripts/replays/balancer.json`), `thetanuts()` (`scripts/replays/thetanuts.json` mints), `balancer_v1()` (`scripts/replays/balancer_v1.json`). Phase A added these loaders; read their docstrings. Where a loader does not expose the exact figure below, find it in the raw JSON; if it is not there, that row's number is a REPORT item and the row is drawn with its dot and snap but no digits.

One number per row, at most 30 mono characters. The expected values (from verify-C; `numbers()` must reproduce them from the JSON, and `check.py` recomputes them with `Fraction`/`Decimal`):

| row | protocol · date | grid | exact value (white dot) | rounded (red) | mechanism label | claim |
|---|---|---|---|---|---|---|
| 1 | Resupply · 2025-06-26 | integers 0, 1 | rate `0.4999999999999999999995` "to 22 decimals" (same string as s06) | `0` | `floored once` | C1, V12 |
| 2 | Bunni · 2025-09-02 | wei units | the idle-balance subtrahend `23.659` "to 3 decimals" (⌊316,691,975,954 × 119,254,548,996 / 1,596,285,787,955,479,539,002⌋ is 23; the exact quotient is 23.659…) | `23` | `floored, 44 times: active balance 28 → 4 wei` | C2 |
| 3 | Balancer V2 · 2025-11-03 | wei units | `17.988250947729518883` "to 18 decimals" (17 × scaling factor 1,058,132,408,689,971,699 / 10^18) | `17` | `mulDown, ×30 cycles` | C3 |
| 4 | Thetanuts · (date from incidents.json) | raw units 0, 1 | `two thirds of a unit` (2 × 1 / 3; draw the words, and the fraction `2/3` only as a LITERAL) | `0` | `floored; 37 mints, every charge 0` | C4 |
| 5 | Balancer V1 · (date from incidents.json) | units 4, 5 | `4.499999999999999991` "to 18 decimals" (3 × 1.499999999999999997, pools 1–3) | `4` | `nearest: 1 unit charged for 1.5 units' worth` | C5 |

Other strings (LITERALS): band titles `rounded too early, or too often` and `rounded at a unit` (script §7); `carry the exact value and round once, and the attack stops` (script §7, drawn in section 4); `who pays?` (essay §3 / A9); `ceil → 1 unit · would have cost more than it took` (C8, counterfactual, off-chain); `toward the pool → 5` (C5 wording: "instead of 5 means rounding toward the pool"); the box line.

Dates come from `incidents()`; never typed. Row 2's "28 → 4" and "44", row 3's "×30", row 4's "37" come from the replay JSON or are REPORT items.

## 4. Sections
| i | name | what appears | persists | spoken over it | held frame | s |
|---|---|---|---|---|---|---|
| 0 | `bands` | title; two band titles (BODY, MUTED) with their row slots: band 1 three rows, band 2 two rows, a faint rule between | — | (the speaker starts) | the empty frame | 3 |
| 1 | `resupply` | row 1: protocol+date (SANS), a mini `GridLine` (length ≈ 5, ticks at the integers), the white dot at the exact value with its number (MONO) to the right; then `snap()` to 0 in RED with `direction()` and the mechanism label | band titles | "Resupply rounded too early." | row 1 complete | 6 |
| 2 | `bunni` | row 2, same anatomy; after the snap a small counter ticks `44` with the label | rows 1 | "Bunni …" | rows 1–2 | 6 |
| 3 | `balancer-v2` | row 3, same; counter `×30` | rows 1–2 | "… and Balancer V2 rounded too often:" | rows 1–3 | 6 |
| 4 | `round-once` | in all three rows the red dots fade to FAINT, the white dots pulse (`Indicate`), and the line "carry the exact value and round once, and the attack stops" appears under band 1 with an EMERALD `check_mark()` | rows 1–3 | "carry the exact value and round once, and the attack stops." | band 1 resolved | 5 |
| 5 | `thetanuts` | row 4: grid 0–1, the dot at two thirds, `snap()` to 0 RED, label | all above | "Thetanuts …" | rows 1–4 | 6 |
| 6 | `balancer-v1` | row 5: grid 4–5 with the half-tick marked by a `measure()` bracket "half a unit", the dot just under it, `snap()` to 4 RED (`nearest`), label | all above | "… and Balancer V1 rounded at a unit, where no precision helps" | all five rows | 7 |
| 7 | `direction` | in rows 4 and 5 a `who pays?` label and `direction()` arrows flip: row 4's dot snaps up to 1 in EMERALD with `check_mark()` and the C8 label; row 5's dot snaps to 5 in EMERALD with the C5 label | all above | "and only the direction decides who pays." | band 2 resolved | 6 |
| 8 | `box` | the box line (HERO size for the two sentences, split over two lines, inside a `glow_bar()`), everything else dims to FAINT; hold 3 s | all, dimmed | "Inside a calculation, precision shrinks error. At a unit, direction decides who pays." | the box line | 6 |

## 5. Vocabulary
`GridLine`, `snap()`, `direction()`, `measure()` (row 5's half unit), `check_mark()`, `cross_mark()` (optional, after a red snap), `glow_bar()`, `digits()` for numbers, `words()` for labels. White = EXACT on this slide; BL19's family colour is not used.

## 6. Hero
The box line (section 8). In section 7 the EMERALD direction results in band 2 are the drawn-last elements, with `check_mark()`s.

## 7. Legibility
Five rows plus two band titles is the densest slide in the talk. Row height ≈ 130 px; the protocol+date column ≈ 300 px; the grid ≈ 600 px; the number ≈ 30 mono chars at BODY (≈ 620 px); the mechanism label on a second line under the number at BODY, MUTED. Nothing else in a row. If it does not fit at BODY, report; do not shrink below BODY.

## 8. Flags
- Balancer V1's row says `nearest`, never "floored" (V27/C9). Its exact product is just under 4.5 in pools 1, 4, 5 and just above in 2, 3 (C5): the row draws the pools-1–3 value and says nothing about the others.
- Resupply is ONE floor, once (C7): the row says `floored once`, no repeat counter.
- Bunni's `28 → 4` is the pool's ACTIVE USDC in wei (C2 wording), not a balance; the label says `active balance`.
- Thetanuts' two thirds is the FIRST mint's charge only (C4); later charges are 2^k/(2+2^k). The row shows the first mint and says `37 mints, every charge 0`.
- The ceil counterfactual (C8) is computed off-chain: its label says `would have cost`.
- Dates and names from `incidents()`; protocols are named (user decision), libraries are not involved here.

## 9. Acceptance
`SECTIONS` as table 4 (nine names); `numbers()` returns the five exact values, the five rounded values and the counters; `check.py` recomputes rows 1–3 and 5 with `Fraction` from the raw JSON operands and row 4 as `Fraction(2, 3)`, and asserts each "to N decimals" string has exactly N decimals and no "…"; `-ql` render; nine held-frame PNGs.

## 10. Deliverables and report
Per RULES.md. The report lists every row whose figure could not be found in the replay JSON.

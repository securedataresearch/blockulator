# Brief: s10_live — "Real markets, today" (rebuild: a strip plot, not a ribbon)

The first build drew 326 markers dropping between three rows with trails. The user: "rather unclear visually; think more like Hadley Wickham." So: the grammar of graphics. One variable per channel, honest shared axis, the distribution visible in the held frame, direct labels, no decoration that is not data. No trails.

## 1. Slide and line
Slide 10 of 19. Title: **Real markets, today**.
Script (verbatim, script-v2 §10): "Three hundred and twenty-six live Aave and Morpho markets. The same interest, measured three times: seven correct digits as deployed, thirty in FP127, sixty-seven in FP19."
Claims: accrual-deployed.json live cases (the three digits columns), its survey block and date; medians computed.

## 2. Takeaway
Every one of 326 real markets gains digits when the same interest is computed in FP127, and more in FP19; the whole distribution moves, not an average.
Closing line: **the same 326 markets: 7 digits as deployed, 30 in FP127, 67 in FP19** (medians from `numbers()`, rounded as the existing scene does).

## 3. Data and strings
Loader: `live()` (docs/benchmarks/accrual-deployed.json cases with group "live": `.truth[primaryTruth].deployed.digitsInterest`, `.fp127.digitsInterest`, `.fp19.digitsInterest`, the protocol, `.survey.block/.date`). Keep the existing `numbers()` keys and check.py expectation; add the per-facet counts and medians.

| string | where | source |
|---|---|---|
| axis title `correct digits of the pending interest` | x axis | existing |
| `as deployed` · `in FP127` · `in FP19` | row labels, left | existing |
| facet titles `Aave · 74 markets` · `Morpho · 252 markets` | above each panel | counts from live() |
| per-row median labels `median 7.2` etc. | right of each row, at the median tick | numbers() |
| margins `+22.9 digits` · `+36.7 digits` | between rows, as a labelled bracket | numbers() |
| caption `docs/benchmarks/accrual-deployed.json · live · block … · date` | bottom-left | existing |
| closing line | bottom | numbers() |

## 4. The plot (grammar)
- **Data:** one row per market; variables: protocol (facet), method (y row), digits (x).
- **Facets:** two panels side by side, Aave left, Morpho right, same x scale (0–80), shared axis drawn once under both; panel widths proportional to nothing (equal), because the comparison is within each.
- **Geom:** `geom_jitter`-style strip: each market one small dot (radius 0.045), y jittered within its row band with a fixed seed so the density shows; rows for `as deployed` (top), `in FP127` (middle), `in FP19` (bottom), the Blockulator rows below so the eye travels down to the heroes.
- **Colour by method, not protocol:** SLATE for deployed, EMERALD for FP127, TEXT for FP19 (white = FP19's family colour on this slide; EXACT is not used). Protocol is carried by the facet, so no shape coding is needed; drop the circle/diamond.
- **Summary layer:** a vertical median tick per row (1.5× the band height, 3 px) with its label directly to its right; no mean, no error bar.
- **Reference lines:** faint vertical gridlines at 0, 20, 40, 60, 80 (`Chart.grid`), nothing else.
- **No trails, no bands, no halos on 326 dots.** The hero mark is `glow_line()` under the FP19 row's median tick and the margin brackets in EMERALD/TEXT.

## 5. Sections
| i | name | what appears | persists | spoken over it | held frame | s |
|---|---|---|---|---|---|---|
| 0 | `deployed` | title, the two facets with their titles, the shared axis, the gridlines; the `as deployed` row fills in both panels (dots arrive in a 1 s stagger, jittered), its median tick and label | — | "Three hundred and twenty-six live Aave and Morpho markets." | the deployed strips | 7 |
| 1 | `fp127` | every dot moves straight down to the `in FP127` row and right to its new x (one `Transform`, 1.5 s, no trail); the row's median tick and label; the `+N digits` bracket between the two medians | all | "The same interest, measured three times: seven correct digits as deployed, thirty in FP127," | two rows per panel | 6 |
| 2 | `fp19` | the same move to the `in FP19` row; median, label, bracket; `glow_line()` under its median | all | "sixty-seven in FP19." | three rows per panel | 6 |
| 3 | `closing` | the closing line in `glow_bar()`; hold 3 s | all | (pause) | the finished plot | 4 |

A dot moves as the same dot (same index), so a viewer who watches one market sees it travel; that is the only motion.

## 6. Legibility
Row labels and medians at BODY; facet titles at BODY, MUTED; axis ticks at CAPTION+4; dots are small but numerous, which is the point. Panels occupy the full safe width; the three row bands are equal height.

## 7. Flags
- Medians are medians (the existing numbers()); nothing is averaged.
- Both facets share the x axis; never rescale per panel.
- The facet counts come from the data (74 / 252), never typed.

## 8. Acceptance
`SECTIONS = ("deployed", "fp127", "fp19", "closing")`; `numbers()` keeps its keys and adds per-protocol counts and medians; check.py's existing expectation extended; `-ql` then one `-qh`; four held-frame PNGs.

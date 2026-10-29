# Brief: s15_formats — "Two formats"

## 1. Slide and line
Slide 15 of 19. Title on the slide: **Two ways to spend 256 bits**.
Script (verbatim, script-v2 §15): "Two ways to spend 256 bits. Fixed point: thirty-eight digits in a known range. Floating point, binary256: seventy-one digits at any magnitude. Overflow reverts, because a revert can't be ignored."
Claims: K1 (FP127: sign + 127 integer bits + 128 fraction bits; about 38 fraction digits; range about ±1.7×10^38), K2 (grid ends at 2^-128), K3 (FP19 = binary256 layout: sign, 19-bit exponent, 236 stored fraction bits, 237-bit significand with the hidden bit; 237·log10 2 = 71.34 digits; smallest normal about 2.48×10^-78,913, largest about 3.22×10^78,913), K4 (no NaN, no infinity; overflow reverts; encoding differs from IEEE), E9 (binary256 is IEEE 754's; primary text paywalled, so say "laid out as binary256"). All in research_notes/talk/verify-K.md and verify-E.md.

## 2. Takeaway
Same 256 bits, two shapes: a fixed grid with 38 digits in a known range, or a 71-digit window that slides across every magnitude; and overflow stops the transaction instead of carrying a NaN.
Closing line (verbatim, essay §8): **known range: fixed point · many orders of magnitude: floating point**

## 3. Data and strings
No benchmark JSON carries these; they are format constants. `numbers()` computes them (bit widths as integers; digits as `floor(bits × log10 2)`; the FP127 range as `2**127 / 2**128`-style exact arithmetic rendered "about ±1.7 × 10^38"; the FP19 extremes from the formulas in K3 with `mpmath`) and `check.py` recomputes them by a second route (`Decimal`/`Fraction`), so the drawn strings are derived, not typed. Draw the derived strings exactly as below.

| string | where | claim id |
|---|---|---|
| `256 bits` | over the bar | K1, K3 |
| `1 · 127 · 128` with `sign · integer · fraction` | FP127 partition | K1 |
| `about 38 digits of fraction` | FP127 | K1 (38.53) |
| `about ±1.7 × 10^38` | FP127 | K1 |
| `the grid ends at 2^-128` | FP127 grid | K2 |
| `1 · 19 · 236` with `sign · exponent · fraction (236 stored)` and `significand 237 bits with the hidden bit` | FP19 partition | K3 |
| `about 71 digits at every magnitude` | FP19 window | K3 (71.34) |
| `about 10^-78,913` and `about 10^78,913` | magnitude axis ends | K3 |
| `laid out as IEEE 754 binary256` | FP19 caption | E9, K3 |
| `no NaN, no infinity: overflow reverts` | section 3 | K4, essay §8 |
| closing line | section 4 | essay §8 |

Superscripts via `markup()` `<sup>`; the minus in exponents is "−" (U+2212); check the glyph on a test frame.

## 4. Sections
| i | name | what appears | persists | spoken over it | held frame | s |
|---|---|---|---|---|---|---|
| 0 | `bar` | title; a `bit_bar(256)` (new vocab primitive: 256 thin cells in a row, RULE colour, that can be partitioned with coloured spans and brackets) draws across the slide with `256 bits` over it | — | "Two ways to spend 256 bits." | the bare bar | 4 |
| 1 | `fixed` | the bar partitions into three spans (sign 1 TEXT, integer 127 MUTED, fraction 128 EMERALD) with `measure()`-style brackets and the labels; under the bar a `GridLine` with uniform ticks draws, its last tick bracketed `the grid ends at 2^-128`; to the right `about 38 digits of fraction` and `about ±1.7 × 10^38`; label `FP127 · fixed point` | bar | "Fixed point: thirty-eight digits in a known range." | FP127 anatomy | 10 |
| 2 | `floating` | the spans re-partition (sign 1, exponent 19 SAPPHIRE, fraction 236 TEXT) with the 237 note; the grid under the bar is replaced by a magnitude axis (a `GridLine` labelled at its ends `about 10^-78,913` … `about 10^78,913`, with `1` marked in the middle); a bracketed window labelled `about 71 digits at every magnitude` slides from the left end to the middle to the right end (three stops, 0.8 s each) with a `glow_line()` under it; `laid out as IEEE 754 binary256` as CAPTION; label `FP19 · floating point` | bar | "Floating point, binary256: seventy-one digits at any magnitude." | FP19 anatomy, window at the right end | 12 |
| 3 | `revert` | a dot slides right along the magnitude axis past its last tick; at the end it becomes a RED `cross_mark()` with `no NaN, no infinity: overflow reverts` | all | "Overflow reverts, because a revert can't be ignored." | the revert marker | 5 |
| 4 | `rule` | the closing line in `glow_bar()`; hold 3 s | all | (pause) | all + closing | 4 |

## 5. Vocabulary
New primitive `bit_bar(n, width, height)` in vocab.py returning a VGroup of cells with `.span(a, b, colour)` and `.bracket(a, b, label)`. `GridLine`, `measure()`, `glow_line()`, `cross_mark()`, `glow_bar()`, `markup()`. White = FP19's family colour on this slide (its fraction span and window labels); EXACT is not used. EMERALD = FP127's fraction span and grid.

## 6. Hero
FP19's sliding window with `glow_line()` (section 2), and FP127's fraction span in EMERALD (section 1). Both Blockulator; the window is drawn last.

## 7. Legibility
The bar spans ≈ 1,700 px: 256 cells at 6.6 px each with 0.5 px gaps; partitions read by colour AND bracket. Labels at BODY; the IEEE caption at CAPTION.

## 8. Flags
- `236 stored` and `significand 237 bits with the hidden bit` are both on screen; never "237 stored" or "236-bit significand".
- Every range and digit count is prefixed `about`.
- The encoding differs from IEEE (K4: all-ones exponent is finite, no NaN): the slide says "laid out as", not "is".
- The window's stops are illustrative positions on a log axis; no digits at the stops.

## 9. Acceptance
`SECTIONS = ("bar", "fixed", "floating", "revert", "rule")`; `numbers()` returns the bit widths, digit counts, ranges and the strings derived from them; `check.py` recomputes 38/71 as `floor(128·log10 2)` / `floor(237·log10 2)` and the four range strings from `2**127`, `2**-128`, `2**-262142`, `(2 - 2**-236)·2**262144` with `Decimal`, and asserts "236 stored" and "237" both appear; `-ql` render; five held-frame PNGs.

## 10. Deliverables and report
Per RULES.md.

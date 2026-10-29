# Brief: s17_proofs — "Knowing it's right" (the honest table)

## 1. Slide and line
Slide 17 of 19. Title on the slide: **Knowing it's right**.
Script (verbatim, script-v2 §17): "A test checks the inputs it was given. A proof covers every input. The core arithmetic of both libraries is proven. Every transcendental is swept against a 300-digit reference with every fallback forced: zero misrounded. Two things no check covers, and they are on the slide. State your own guarantees this specifically."
Claims: V22 (FP127 17 core ops proven: 16 Halmos + sqrt by exact integers; gavg and hypot fuzzed at 50,000 runs), V23 (FP19 18 of 24 proven; six fuzzed at 50,000 runs and held to vectors), V17 (FP19 tested against 300 digits, FP127 against 200), V25 (FP19 455,082 results in 76 rows, FP127 212,119 in 59 rows, 0 misrounded; transcendentals 327,488 and 168,120), V24 (bounds gate in CI), V26 (last-stage midpoint limits), V38 (measured error reaches 0.92 of FP127's exponential bound and 0.79 of FP19's pow bound), V7 (FP19 correctly rounded in every op: tested, not proven).

## 2. Takeaway
Four rows: what is proven, what is fuzzed, what is tested, and what no check covers; stated this specifically.
Closing line (verbatim): **State your own guarantees this specifically.**

## 3. Data and strings
Loaders: `proofs()` (docs/benchmarks/proofs.json: `summary`, `ops[]` with lib/op/status, `fuzz[]` with runs), `sweep(lib, op)` and the full row list (sum `n` and `misrounded` per lib; the transcendental subset is the rows whose op is in the libraries' transcendental list: read docs/benchmarks/sweep.md's section headings or the `_doc`; if the subset cannot be derived from the JSON, the two subset totals are REPORT items and the row draws the per-library totals only).

| row | string (derived from JSON unless marked LITERAL) | claim id |
|---|---|---|
| proven for every input | `FP127: 17 core operations (16 by Halmos, sqrt in exact integers) · FP19: 18 of 24` | V22, V23; counts from proofs.json ops (status proven, per lib) |
| fuzzed against the spec | `FP127: gavg, hypot · FP19: six · 50,000 runs a test` | V22, V23; names and runs from proofs.json fuzz[] |
| tested against an oracle | `FP19: 327,488 transcendental results at 300 digits · FP127: 168,120 at 200 · 0 misrounded` and small `(455,082 and 212,119 over every operation)` | V25, V17; sums from sweep.json; the digit counts 300/200 are LITERALS V17 |
| known limits | `a derived bound could be wrong beyond its sampled margin: the measured error reaches 0.92 of FP127's bound and 0.79 of FP19's` and `the last stage has no test of its own: a true value within its error of a midpoint would misround` and `none is known` | V38 (0.92, 0.79 are LITERALS: from the READMEs, not JSON), V26 |
| footnote | `the proofs found two bugs on the way: fixed, now proven` | V52 (VERIFIED: issue #159, fix PR #163 2026-10-23, proofs PR #187 2026-10-27, docs/proofs.md:84–87). LITERAL |
| title lines | `A test checks the inputs it was given.` / `A proof covers every input.` | script §17 |
| closing | `State your own guarantees this specifically.` | script §17 |

## 4. Sections
| i | name | what appears | persists | spoken over it | held frame | s |
|---|---|---|---|---|---|---|
| 0 | `test-proof` | title; the two title lines (BODY): "A test checks the inputs it was given." then "A proof covers every input."; beside them a small `Chart` plane: a scatter of dots (tests) then the plane fills (a proof), per storyboard A20 | — | "A test checks the inputs it was given. A proof covers every input." | the two lines + plane | 7 |
| 1 | `proven` | the table's first row lands: left cell label (SANS, BODY, MUTED), right cell the string, with an EMERALD `check_mark()` | title lines, plane shrunk | "The core arithmetic of both libraries is proven." | row 1 | 5 |
| 2 | `fuzzed` | row 2, same anatomy, a MUTED tick | rows | (pause) | rows 1–2 | 4 |
| 3 | `tested` | row 3; `0 misrounded` at HERO size in EMERALD with `halo()`, the counts ticking up from 0 to their values (`ValueTracker` + `digits()` through a formatter that uses `thousands()`); the small total line | rows | "Every transcendental is swept against a 300-digit reference with every fallback forced: zero misrounded." | rows 1–3, hero number | 8 |
| 4 | `limits` | row 4 in MUTED with a hollow marker (not red: these are limits, not bugs); its three strings land one per 0.6 s; `none is known` last, TEXT | rows | "Two things no check covers, and they are on the slide." | the full table | 7 |
| 5 | `closing` | the footnote at CAPTION; the closing line in `glow_bar()`; hold 3 s | table | "State your own guarantees this specifically." | table + closing | 5 |

## 5. Vocabulary
`words()`, `digits()`, `check_mark()`, `halo()`, `glow_bar()`, `Chart` for the plane, `ValueTracker` counters, `thousands()`. White = EXACT (table text); EMERALD = proven/0 misrounded; RED is not used on this slide.

## 6. Hero
`0 misrounded` (section 3), HERO size, EMERALD, `halo()`, drawn last in its section.

## 7. Legibility
Four rows at BODY: each right cell wraps to at most two lines of ≤ 70 SANS characters; the "known limits" row is the longest and may take three lines; if it does not fit at BODY, split the row's strings across two held sub-beats inside section 4 (still one section) rather than shrink.

## 8. Flags
- Row 3's label is `tested against an oracle`: tested, not proven (V7).
- Row 4 is never styled as a bug list: no red, no crosses. The footnote's two bugs are history ("fixed, now proven"); they never appear as open items.
- 0.79 is the figure (V38; the FP19 README table says 0.78 in one cell and 0.79 in its text; the ledger uses 0.79).
- "every fallback forced" is in the script; on screen the row says what the sweep did, in the ledger's words.

## 9. Acceptance
`SECTIONS = ("test-proof", "proven", "fuzzed", "tested", "limits", "closing")`; `numbers()` returns the proven/fuzzed counts per library, the fuzz runs, the per-library sweep totals and misrounded sums, and the transcendental subtotals if derivable; `check.py` recomputes the counts from proofs.json and the sums from sweep.json by its own path and asserts misrounded == 0 for both; `-ql` render; six held-frame PNGs.

## 10. Deliverables and report
Per RULES.md.

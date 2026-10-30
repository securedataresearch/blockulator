# Direction v4: the edit pass — one thing per frame

The user (2026-10-30), after the first run-through of all 24 scenes: "these
animations are super impressive, the talk is moving in the right direction.
But the slides are FAR too busy. There is just too much going on everywhere.
It's time to edit." This brief is that edit. It governs every scene from here,
2D and 3D alike, and it adds a measurable budget so "busy" is a number
(`talk/scenes/census.py`), not an opinion.

## What makes them busy (from the held frames, talk/build/frames)

1. **Posters accumulate.** Each section adds and nothing leaves; the last
   frame is every beat of the story at once (the five replays, s07, s12, s17,
   s19; deck-3d's s06 too).
2. **Ghosts.** A beat that is over is dimmed, not removed, so it stays on the
   frame as grey noise behind the next beat (s07's rows, s12's chain table,
   s06 3D's rate and tanks, s13's first line).
3. **The slide repeats the speaker.** Closing lines and captions restate the
   sentence being spoken ("three good answers, none the closest · Blockulator:
   all 18"; "the same 326 markets: 7 digits as deployed, 30 in BL127, 67 in
   BL19"; "Blockulator's lines start higher and keep the gap …" in three lines).
4. **Numbers shown twice.** The truth appears as a row and again inside the
   labels; medians AND brackets; a counter AND a box that restates it (s16);
   two identical title lines (s09).
5. **Legends, code and footnotes.** Legend boxes with 9–17 entries plus a
   "no dot because" paragraph (s08, s09); Solidity source lines (s06, s06b,
   s06c, s06e); explanatory sub-lines under every label (s15, s17, s18).

## The rules (added to RULES.md; they override the earlier "poster" habit)

- **One idea per frame, and the frame holds only it.** When a section ends,
  its story elements FadeOut (or transform into the next beat's one object).
  Nothing is dimmed to stay. The poster (the last section's held frame) shows
  the slide's one conclusion and the one object that proves it, not the story.
- **The budget.** A held frame has at most **12 lit text strings** and
  **260 glyphs**, and **0 ghosts** (text at fill opacity below 0.5). The title
  counts; a chart's key does not. `census.py` prints every held frame's numbers and
  fails a poster over budget; it joins `check.py` once every scene passes.
- **The slide shows; the speaker says.** No sentence of script-v2 appears on
  a slide. Three thesis lines are the exception, because they ARE the slide:
  s07's box, s13's line, s18's title. Every other closing line, caption
  sentence and "what you just saw" summary goes to the script notes.
- **A number once.** The truth is drawn once per slide. A quantity has one
  representation (a bracket OR a median label, a counter OR a box). A label
  names its object in at most four words; "to N decimals" stays, because it
  is part of the number (the no-ellipsis rule).
- **Direct labels, plus a compact key (user's decision: all 17 libraries stay
  on every chart).** A series is named at its line's end, in its colour. The
  key is chrome: one column at CAPTION size with every library in its colour,
  exempt from the 12-string count; the "no dot because" paragraph becomes one
  line inside the key ("no exp: OpenZeppelin · Uniswap · Maker · Aave · Morpho").
- **No source code and no source caption on a slide (user's decision).**
  Provenance (file:line, block, tx) lives in the slide's notes in slides.yaml,
  so script.md and the PDF carry it; `caption_now`/`caption` calls go. The
  budget's 12 strings therefore do not include a caption.
- **Fewer strings, bigger type.** A poster with one number carries it at
  HERO 48 or larger (up to 72 when it stands alone); labels never below BODY
  32 except the caption. Nothing is shrunk to make room: if it does not fit,
  it is cut.
- **Fewer clicks.** A slide has at most four sections (the replays five);
  the deck goes from 115 sections toward about 75.

## The per-slide cut list

For each slide: what the poster keeps (K) and what goes (X). "notes" means
the slide's notes in slides.yaml / script.md, where the accounting lives.

| # | scene | keep on the poster | cut |
|---|---|---|---|
| 1 | s01 title | as is | the `[speaker]` placeholder becomes the speaker line |
| 2 | s02 exp40 | the truth to 18 decimals (title row); BL127's word to 40 decimals with the precision bracket at 39; BL19's to 60 with the bracket at 55; one label per word ("39 decimals right", "55 decimals right") | the two closing lines; the context line; the digits past 40/60 (the stated format changes to "to 40/60 decimals"); the "every one of them right" sentence; sections 4 → 3 (exact, libraries, blockulator) |
| 3 | s03 under | the four names, the e^x hub, the four arrows | the four formulas (the arrows say it); the two-line sentence (script) |
| 4 | s04 grid | the lattice with its two hex neighbours, the e^40 dot, the "half a unit" bracket, one hero line "a 256-bit word holds 2^256 numbers; e^40 is not one of them" | the 80-decimal truth header; "BL127's grid: one tick = …" and "one tick = 2^-128 · the ticks' fractions in hex" (one of them becomes the lattice's label, CAPTION); the "BL127's word / to 18 decimals" block; both "the lower/upper word reads, to 80 decimals" blocks |
| 5 | s05 cost | five rows: date · protocol · amount; the hero total | every explanatory sentence (the replays follow); the "since June 2025" caption tail |
| 6 | s06 Resupply (3D, deck-3d) | the gate shut red with "5,263,158× the limit" and "insolvent"; the attacker's tank | every ghost (the rate, "collateral: 1 share-wei", the tanks' labels, "> 95,000", the 499,999,… line): the rule is FadeOut, not dim |
| 7 | s06b Bunni | the decisive step as one lattice (23.659 → 23, floor), "44 withdrawals" counter, "$8.4M" hero, the emerald line "ceil once: the attack stops" | the four balance rows; the two bars; the formula and the Solidity line; "idle keeps 0.659 wei too many / reads 0.659 wei low"; stored/after lines; the BL127/BL19 40-decimal rows (one tick + "BL127 / BL19: 35.6278 (to 4 decimals)" if a number is wanted) |
| 8 | s06c Balancer V2 | one lattice (17.988 → 17), "× 55 in one transaction", "$121.1M" hero, the emerald line "ceil once: the attacker loses 127.677 ETH" | the after-the-drain balances; the Solidity line; the mulDown/mulUp labels on the lattice (one arrow + "floor"); charged/exact pair (keep ONE: "34.65% under"); the 30/25 cycles rows; the invariant bar; "net to the attacker"; "replayed, not observed" (notes) |
| 9 | s06d Thetanuts | one lattice (0.667 → 0, floor), "37 mints" counter, "$105,000" hero, the emerald line "ceil: 1 raw unit on every mint" | the supply/flash-borrowed/claim rows; the components table; the bytecode line; the doubling bars; "the rest of the vault" amounts (notes); the three-line emerald box → one line |
| 10 | s06e Balancer V1 | one lattice (4.4999… → 4, nearest), "438 joins" counter, "$1.39M" hero, the emerald line "toward the pool: 5 · the loop stops" | the pool/WBTC/DPI rows; the bmul line and its citations; the satoshi commentary (five strings); the two-line emerald box → one line |
| 11 | s07 two | two bands with five names sorted into them; the box | the five number-line thumbnails and their values (ghosts); sections 9 → 4 (bands, too-early-or-too-often, at-a-unit, box) |
| 12 | s08 ladder | the chart, direct labels at the line ends, the two margin brackets, the key as one compact column | the 18-decimal cluster's name list on the chart (one label: "18-decimal · 9.2"; the names are in the key); the three-line closing caption; the "not offered" sentence becomes one line in the key |
| 13 | s09 cliff | the chart, direct labels (BL19 · 71, BL127, ABDK Quad, "18-decimal: zero from exp(−42)"), the "revert" marks, the key as one compact column | the duplicated title line; the "no dot" paragraph (one line inside the key); "BL127 · 1 digit still at exp(−88)" stays as the BL127 label |
| 14 | s10 live | the three strips with their medians; the market counts in the column titles | the four "+N digits" brackets (the medians say it); the closing sentence |
| 15 | s11 budget | the four names and their glyphs; the last line at HERO | nothing else; the glyphs get larger |
| 16 | s12 reference | the address box; "your contract → eth_call exp(40)" → "equal" with the two matching words | the ghost chain table (its own section, then FadeOut); the four ticks line (script); the closing sentence; "probed 2026-10-29" (notes) |
| 17 | s13 not-switch | as is | the dimmed first line: FadeOut, no ghost |
| 18 | s14 institutions | the three words at HERO; the two lines "errors scale with the amount" / "fees scale with the computation" as the chart's only labels (user: trim, not cut) | "not fewer cents"; the ERC-4626 line (notes); the chart's axes if the two lines carry it alone |
| 19 | s15 formats | the bit bar with 1 · 19 · 236; the magnitude line with "about 71 digits at every magnitude"; "overflow reverts" | "sign · exponent · fraction (236 stored)"; "significand 237 bits with the hidden bit"; "laid out as IEEE 754 binary256" (notes); "known range: fixed point · many orders of magnitude: floating point"; the two README paths |
| 20 | s16 ziv | the two counters "1 of 21,913" / "0 of 3,963" with their one-line label; "5 gas" / "393 gas" on the two coins | the two-line box (it restates the counters); the long coin labels |
| 21 | s17 proofs | three rows, one number each: proven · 17 + 18 operations; fuzzed · 50,000 runs; tested · 0 misrounded of 495,608; one line "known limit: a true value within the last stage's error of a midpoint" | every parenthetical ("16 by Halmos …", "gavg, hypot · six", "455,082 and 212,119"); the dot grid; "State your own guarantees …" (script); "the proofs found two bugs" (notes) |
| 22 | s18 habits | the title; Decide · Measure · Declare; the declaration block | the three paragraphs under the words (they are the script) |
| 23 | s19 address | the two addresses; the two QR tiles; engineers' two lines; agents' line; "Measure yourself against it." | the eight sub-object addresses (the QR leads to them); "every op is a free eth_call" (script) |
| 24 | s20 thanks | as is | — |

## Process

1. `census.py` on the current scenes is the baseline (its poster table is in
   this file's appendix once run). Posters over budget: the number to beat.
2. Two models first, the user looks: **s02** (the opener; it sets the eye) and
   **s06c Balancer V2** (the busiest 2D replay, rebuilt to the replay shape
   above). Both 2D on talk-deck (user's decision 2026-10-30: the replays stay
   2D for now; deck-3d waits). Each at -qh, frames to the user, nothing else
   rebuilt.
3. Then three waves, ≤3 builders at a time ([[rapid-gates]]): the four other
   replays; the charts (s08, s09, s10) and s04; the text slides (s03, s05,
   s07, s11, s12, s14–s19) by one builder.
4. `census.py` green on every scene → it runs inside `check.py`; `make talk`;
   the user's run-through.

Everything in RULES.md still holds (numbers from JSON, no ellipses, hero
rows last, static chrome, the spectrum). Where a rule here bends an earlier
one (legends → notes; captions to one token; sections ≤ 4), this brief wins.

## Appendix: the baseline (census.py, 2026-10-30, before the edit)

```
poster               section         lit  ghost  glyphs  over
s01_title            title             3      0      96  
s02_exp40            closing          42      0     744  +30 strings · +484 glyphs
s03_under            alone            14      0     168  +2 strings
s04_grid             snaps            19      0     703  +7 strings · +443 glyphs
s05_cost             closing          22      0     671  +10 strings · +411 glyphs
s06_resupply         multiplier       23      0     508  +11 strings · +248 glyphs
s06b_bunni           exact            51      0     963  +39 strings · +703 glyphs
s06c_balancer_v2     exact            40      0     637  +28 strings · +377 glyphs
s06d_thetanuts       exact            50      0     913  +38 strings · +653 glyphs
s06e_balancer_v1     exact            50      0     959  +38 strings · +699 glyphs
s07_two              box              21     18     279  +9 strings · +19 glyphs · 18 ghosts
s08_ladder           closing          38      0     616  +26 strings · +356 glyphs
s09_cliff            closing          31      0     433  +19 strings · +173 glyphs
s10_live             closing          29      0     355  +17 strings · +95 glyphs
s11_budget           direction         7      0     141  
s12_reference        closing          18     39     344  +6 strings · +84 glyphs · 39 ghosts
s13_not_switch       measure           1      1      35  1 ghosts
s14_institutions     precedent         9      0     172  
s15_formats          rule             17      0     357  +5 strings · +97 glyphs
s16_ziv              closing          12      0     235  
s17_proofs           closing          24      0     517  +12 strings · +257 glyphs
s18_habits           block            14      0     345  +2 strings · +85 glyphs
s19_address          links            33      0     736  +21 strings · +476 glyphs
s20_thanks           links             8      0     204  

19 of 24 posters over budget
```

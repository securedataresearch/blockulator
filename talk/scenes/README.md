# The talk's scenes

One manim file per animated slide of *The End of Rounding Errors*, sharing
one vocabulary (`vocab.py`) so the deck has one look. Every number on
screen is read from the repo's JSON at render time; nothing is typed in.

## Render

```sh
make anim                   # every scene, 1080p 30 fps, into talk/build/videos/<scene>/1080p30/
make anim SCENE=s02_exp40   # one scene
make contact                # the last frame of every section, tiled into talk/build/contact.png
uv run manim -ql talk/scenes/s04_grid.py Grid     # a 480p preview while editing
uv run manim -qh -s talk/scenes/s02_exp40.py      # the last frame only, as PNG
```

`make anim` runs `talk/scenes/check.py` first (below) and renders with
`--save_sections` (`vocab.py` also sets `config.save_sections`, so a
`-ql` preview writes them too): beside the scene's mp4, one mp4 per
section and an index, `talk/build/videos/<scene>/<quality>/sections/
<Scene>_<nnnn>_<name>.mp4` and `<Scene>.json` (a list of `{name, type,
video, width, height, nb_frames, duration, avg_frame_rate, codec_name,
pix_fmt}`). `make contact` (`contact.py`) extracts each section's last
frame to `talk/build/frames/<scene>_<nn>_<name>.png`, checks the index's
names against the scene's `SECTIONS`, and tiles them labelled. manim is
a dev dependency (`uv add --dev manim`, pinned in `pyproject.toml`); it
needs cairo, pango and ffmpeg from the system. `talk/build/` and manim's
default `media/` are git-ignored; rendered mp4s are build outputs, like
the tables.

## Chrome: the logos and the title helper

Every frame carries the two marks of `talk/logos/` at its top corners:
`blockulator.png` top-left, `sdr.png` top-right, each `LOGO_HEIGHT`
(0.55) tall at opacity 0.92, their outer corners at `LOGO_CORNER`
(±6.75, 3.6). `DeckScene.setup()` adds them before anything else, as
`self.chrome`, a `Group` of two `ImageMobject`s: chrome, not data. A
scene never animates, dims or moves them; a "dim everything" step that
collects `VMobject`s leaves them alone (they are not `VMobject`s), and
one that names its mobjects must not name `self.chrome`.

A slide's title goes beside the left mark: `self.title(text, size,
colour, use_markup=False)` returns the `words()` (or `markup()`) placed
`TITLE_GAP` (0.3) to the right of it, centred on its height, so a title
never collides with the mark; the caller fixes it (below). It registers in
`DRAWN` as any `words()` does, so a title in `LITERALS` keeps its string.
Content at the top-right stays under the right mark (its bottom is at
y = 3.05) or left of it (x < 6.2); nothing shrinks for it.

## Static chrome: titles, axes and keys are always visible

The user's rule (talk/briefs/RULES.md, "Chrome and colour"): like the
logos, the title, the source caption, every chart's axes, gridlines, axis
titles and tick labels, and the key (every series or category that will
appear in the scene, in its colour) are on the first frame of section 0,
drawn with `add`, never revealed, faded, moved, dimmed or re-created; only
the data and the story elements animate. Row labels on a data slide
(s10's "as deployed / in BL127 / in BL19", s05's and s07's protocols,
s17's four rows) are keys: on the first frame, only their values arrive.

`DeckScene` carries it: `self.fix(*mobjs)` adds the mobjects at once (no
animation) and remembers them in `self.fixed`; `self.caption_now(text,
corner=DOWN + LEFT)` is the source caption as chrome (`self.caption()`
still swaps it when the source on screen changes, as s16's second half
does); `self.dimmable()` is every `VMobject` on the scene
that is not in `self.fixed`, what a "dim everything" step may fade (s07's
box uses it; the marks are not `VMobject`s and are never collected). A
chart that morphs (s08) keeps the axes and a key of every series across
the morph from the first frame (in `self.key`, which `text_census` does
not count); the scenario's title reads the current scenario and swaps at
each morph.

Where a slide's layout reuses a region for a later beat, the rule bends
and the README's table says so: s02's three library names leave with
their values when the two words need the rows; s12's chain names land
together at the start of the table section (the hero address fills
section 0) and dim with the table under the call; s15's BL19 axis
replaces BL127's grid; s16's grid arrives after the coins; s17's two
lines leave when the table begins. On the text slides nothing moves:
s14's chart keeps its place at the left (the brief had it shrink; its
axes and both series labels are chrome), s13 dims its first line to
FAINT under the second, s19 fills its regions in turn (the addresses,
the objects' column, the tiles at the right, the two ways in, the
closing line) and holds them all on the poster.

## The complete spectrum

Distinct categories get distinct hues from the whole palette (EMERALD,
GOLD, SAPPHIRE, VIOLET, SLATE, AMBER, RED, TEXT; MUTED and FAINT for
de-emphasis), never two categories in one hue on a slide, never a hue with
no meaning. The fixed meanings keep theirs: RED wrong, EMERALD BL127 /
correct, TEXT BL19 / exact, `FAMILY_COLOUR` on every library chart. The
rest is assigned once, in `vocab.py`, and reused by every builder:

| what | hue | where |
|---|---|---|
| Resupply | SAPPHIRE | `PROTOCOL_COLOUR["resupply"]`: s05, s07; s06 names it so (the cited Solidity lines) |
| Bunni | GOLD | `PROTOCOL_COLOUR["bunni"]`: s05, s07 |
| Balancer V2 | VIOLET | `PROTOCOL_COLOUR["balancer-v2"]`: s05, s07 |
| Thetanuts | SLATE | `PROTOCOL_COLOUR["thetanuts"]`: s05, s07 |
| Balancer V1 | AMBER | `PROTOCOL_COLOUR["balancer-v1"]`: s05, s07. `Palette.AMBER` (#e7a784) is the deck's fifth hue, color-mix(in oklab, gold 65%, red), computed as the site computes VIOLET and SLATE |
| s03's rows | compounding GOLD, discount SAPPHIRE, option VIOLET, growth SLATE; e^x EMERALD | `ROW_COLOUR["s03"]` |
| s10's rows | deployed SLATE, BL127 EMERALD, BL19 TEXT; the facets neutral | `ROW_COLOUR["s10"]` |
| s15's fields | sign TEXT; BL127 integer SAPPHIRE, fraction EMERALD; BL19 exponent VIOLET, fraction TEXT | `ROW_COLOUR["s15"]` |
| s16's coins | MUL GOLD, the 512-by-256-bit division VIOLET | `ROW_COLOUR["s16"]` |
| s17's rows | proven EMERALD, fuzzed GOLD, tested SAPPHIRE, limits MUTED | `ROW_COLOUR["s17"]` |
| s11's bullets | long horizons GOLD, cancellation SAPPHIRE, extreme ranges and tails VIOLET, iteration SLATE; the direction EMERALD (the dropped tail RED) | `ROW_COLOUR["s11"]` |
| s14's curves | fees MUTED, errors RED; the three words on EMERALD panels | `ROW_COLOUR["s14"]` |
| s18's habits | Decide GOLD, Measure SAPPHIRE, Declare VIOLET; the ticks EMERALD; the `example` tag AMBER | `ROW_COLOUR["s18"]` |
| s19's and s20's audiences | engineers GOLD, agents SAPPHIRE; the objects in their family colours | `ROW_COLOUR["s19"]` |

`protocol_colour(name)` finds the hue from incidents.json's protocol name
("Bunni v2" → bunni). A new slide that names a protocol or a row takes
its hue from these tables; a new category takes the first hue the slide
has not used.

## Sections: one click, one beat

A scene declares `SECTIONS = ("price", "division", …)` and calls
`self.section(i)` at each beat, in order, `section(0)` before anything
is played. `section()` closes the previous section with a hold (manim
drops a section with no play/wait silently, which would shift every
later name in the index) and the scene ends with `self.close()`, a long
hold whose last frame is the slide's poster. Nothing fades to the
background at the end: the last frame reads as a finished slide. The
deck plays one section per click and holds its last frame. The title
(s01, `loop: true` in slides.yaml) is the one single-section scene: its
last frame is its first (`TextScene.snapshot()` before and after the
beat, asserted in the scene and by check.py), so the clip loops with no
seam.

## Fonts

The site's fonts, Instrument Sans and JetBrains Mono, are served as WOFF2
in `static/fonts/`. Pango wants TTF, so `make talk-fonts`
(`talk/scenes/fonts.py`, fontTools) unwraps them into `talk/fonts/*.ttf`,
which are committed with their licence, `talk/fonts/OFL.txt` (SIL Open
Font License 1.1 for both). `vocab.setup_fonts()` registers them with
Pango per process; every text helper calls it.

## The vocabulary (`vocab.py`)

- `Palette`: the site's dark theme hex for hex (`static/css/site.css`
  :39–46; `VIOLET` and `SLATE` are blockulator.css's `color-mix` in OKLab;
  `AMBER` is the deck's own, gold 65% with red, the same mix).
  Three meanings: `EXACT` (white, the true value), `CORRECT` (emerald, the
  nearest representable value), `WRONG` (red, any other). `colour_of(lib)`
  gives a library's family colour as the site's charts do: BL127 emerald,
  BL19 white, the 18-decimal libraries gold, ABDK 64.64 sapphire, Quad
  violet, the protocols slate.
- `words(s, size, colour)` is Instrument Sans; `digits(s, …)` is JetBrains
  Mono with ligatures off so `text[i]` is character `i`; `markup(s, …)` is
  Pango markup (`<sup>`, `<sub>`). Each appends the raw string to
  `vocab.DRAWN` (`reset_drawn()` clears it) so `check.py` can read what a
  scene drew. Sizes: `SIZE_CAPTION` 20, `SIZE_BODY` 32, `SIZE_HERO` 48;
  a mono string is at most `MAX_MONO_CHARS` (46) per line at `SIZE_BODY`
  (an 80-decimal number wraps).
- `GridLine`: a `NumberLine` drawn as the grid of representable values
  (faint, ticks, no numbers). `dot_at(x, colour)`, `nearest_tick(x)`.
- `snap(dot, line, to_tick, colour)`: the one verb. The dot slides to the
  tick, swells and settles in the colour of what it became.
- `midpoint(line, a, b)`: the rounding boundary, a dashed line through the
  middle of the gap between two ticks; `error_bar(dot, half_width, colour)`:
  the bound a fast value carries, a `|——|` bracket centred on the dot,
  CORRECT when it clears the boundary, WRONG when it crosses it.
- `measure(line, a, b, label)`: a thin `|——|` bracket under the line naming
  a distance; `measure_up(p_lo, p_hi, label)` is the same stood on end, how
  a chart names the margin between two line ends in its own units.
- `DeckScene`: dark background, fonts registered, 30 fps, output under
  `talk/build/`; `self.caption(text)` returns the animation that puts the
  source of the numbers in the bottom-left corner; `SECTIONS`,
  `section(i, hold)`, `close()` as above.
- `TextScene(DeckScene)`: the seven text slides' helper. `typed(text,
  size, colour, run_time, mono=False, place=None)` makes the Text (words(),
  or digits() with mono), places it with `place(mobj)`, plays
  `AddTextLetterByLetter` at `TYPE_PER_CHAR` (0.035 s a glyph, or spread
  over run_time) and returns it; `strike(mobj, colour)` is the Line
  through a text or a span of its glyphs (`glyphs(txt, sub)` finds the
  span: Text keeps one submobject per non-space character), played with
  Create; `checkbox(label, size, colour)` is a `Checkbox` (a square and
  its label; `.tick()` puts an EMERALD check_mark() in the box and returns
  the Create); `bullet(glyph, text)` a row of a glyph and a line;
  `snapshot()` the state of every drawn mobject (class, centre, size,
  colour, opacities) for the looping title. `wrap(text, width)` breaks a
  line at spaces for a multi-line Text. `measure(…, label=None)` is the
  bare bracket (s11's schematic gaps carry no number).
- `qr(url, size)`: a QR code drawn, not an image: a white rounded panel
  (`Palette.TEXT`, the quiet zone of 4 modules inside it) with the dark
  modules (`Palette.BG`) as one `VGroup` of squares, `size` units a side,
  the URL under it in mono at `SIZE_CAPTION` (through `digits()` with the
  font's ligatures left on, for the `//`), so `check.py` sees it; a URL
  with a digit needs a `LITERALS` entry. Error correction M, the smallest
  version that fits (`qrcode`, a dev dependency). `.panel`, `.modules`,
  `.label`, `.matrix` name the parts; `qr_matrix(url)` is the matrix
  alone, for `check.py` to regenerate and compare. `label` is the text
  drawn under the tile when it is not the URL (the URL without its
  scheme; lines split on newlines, each its own digits(), centred or
  right-aligned to the panel with `label_align="right"`), `.url` the URL
  encoded; s19 breaks the repository's URL at its slashes into three
  lines (one line is 6.8 units, the tile column 4.1), s20 draws it whole.
- Loaders, all by path from the repo root: `libs()` (static/data/libraries.json
  → `{id: record}`) and `talk_libs()` (the same less BlockulatorWad: the 17
  every comparison accounts for), `edges(op)` and `probe(op, *args)`
  (docs/benchmarks/edges.json), `ladder(scenario)` (docs/benchmarks/ladder.json
  → `{"N", "log10", "scenario"}`) with `ladder_median(cell)` (`.digits.median`,
  or a bare `.digits` in older files) and `ladder_reason(scenario, lib)` ("not
  offered" when `.ops[lib]` is `["unsupported"]`), `live()`
  (docs/benchmarks/accrual-deployed.json, the 326 `group == "live"` cases),
  `resupply()` (scripts/replays/resupply.json), `sweep(lib, op, stage)`
  (docs/benchmarks/sweep.json, one row), `gas(op)` (docs/benchmarks/gas.json
  `.ops[op]` with `inlineMedian` per form over its `typical` inputs),
  `proofs()` (docs/benchmarks/proofs.json summary and ops), `release()`
  (contracts/deployments/RELEASE.json), `chains()` (talk/scenes/data/
  chains.json, a dated hand copy of contracts/deployments/README.md's chain
  table, to re-probe before the talk), `bunni_replay()` (runs
  scripts/replays/bunni.py's `replay` on bunni.json: the per-withdrawal
  chain), `thetanuts()`, `balancer()`, `balancer_v1()` (the raw replay
  JSONs), `balancer_v1_replay()` (scripts/replays/balancer_v1.py's `replay`
  on each pool: the joins and exits with BNum's intermediate integers),
  `replay_table(name, heading)` (the first markdown table under a heading of
  docs/benchmarks/replay-<name>.md as a list of {column: cell}; the tables are
  generated from the JSON, so a scene cross-checks them against it), and
  JSONs), `replay_table(name, heading)` (the first markdown table under a
  heading in docs/benchmarks/replay-<name>.md, one dict per row keyed by
  the header cells, every cell the string as written), `balancer_v1_replay()` (scripts/replays/balancer_v1.py's `replay`
  on each pool: the joins and exits with BNum's intermediate integers), and
  `truth80()`: e^40 to 80 decimals by mpmath, its first 24
  decimals asserted against edges.json's truth.
- The words: `decode_bl127(raw)` and `decode_bl19(raw)` (the older names
  `bl127_value`, `bl19_value` still work) decode a cell's `.raw` word
  (BL127: raw / 2^128; BL19: binary256's fields, contracts/src/bl19/README.md
  lines 21–24) to an exact Fraction; `to_decimals(q, places)` writes it,
  nearest, half-up; `exact_decimals(q)` writes its complete expansion (the
  denominator is a power of two, so it terminates: every digit is the word's).
- `correctly_rounded_18(truth)`: the nearest 18-decimal value, ties away
  from zero (no probe in edges.json is a tie). `correct_digits(value, truth)`
  = floor(−log10(|value − truth| / truth)), the measure edges.json reports as
  `.digits`. `matching_digits` counts the shared prefix by eye;
  `matching_decimals` counts it from the point (0 when the integer parts
  differ), the count a fixed-point word is judged by; `correct_decimals(digits,
  truth)` turns a cell's `.digits` into decimals (less the integer part's
  length, a floor). `first_wrong_index(value, truth)`: where the strings part.

Every chart that compares libraries shows all 17 that have a value and
lists the rest with the reason the data gives ("no exp", "rejects negative
inputs", "not offered"); none is dropped silently. Blockulator's rows and
lines are drawn last, under a halo, and the margin is called out in the
chart's own units.

## Scenes

| file | slide | numbers from |
|---|---|---|
| `s02_exp40.py` | What is e^40? | edges.json op `exp`, probe `["40"]`: `.truth` (extended to 80 decimals by `truth80()`), `.cells[solady|balancer|prb].value` (counted in decimals of 18), `.cells[bl127|bl19].raw` decoded exactly (`decode_bl127`, `decode_bl19`: Fractions with power-of-two denominators) and drawn to 40 and 60 decimals (`to_decimals`, nearest; "to N decimals" on the name line), 20 decimals a line in one column grid with the rows above, the matching prefix against the truth lit and counted by eye (`matching_digits`: 39 and 55 decimals), the few digits past it MUTED with a `precision_end()` bracket carrying the word's one label; every row's label "N decimals right"; three sections (exact, libraries, blockulator), the library rows leave when the words arrive; labels from libraries.json |
| `s03_under.py` | exp is under everything | no JSON: `numbers()` is empty and every string is a `LITERALS` entry (the title, the four names, the hero `e^x`: V11); the four names write in, each in its hue, then a line from each (its hue into EMERALD) draws into `e^x` at 72 under a `halo()`; two sections (four, resolve); the formulas and the closing sentence are in the notes |
| `s04_grid.py` | Computers round | edges.json op `exp`, probe `["40"]`: `.truth` to 80 decimals (`truth80()`, asserted, never drawn), `.cells.bl127.value` (asserted the nearer 2^-128 word); the neighbours at every decimal level (one tick = 1 down to 10^-18) and every binary level (2^-60 down to 2^-128, fraction words in hex, 32 digits at the end) computed from the truth with Fraction, two rows each ending under its own tick; one lattice label ("one tick = 10^-k", then "2^-k"); four sections (human, decimal: the whole dive, half, snaps); the hero line (V8) on the poster only; no caption (provenance in the notes) |
| `s05_cost.py` | $130 million | `talk/scenes/data/incidents.json` (`.incidents[]` date, protocol, loss; `.total` split at its comma into the hero and "before recoveries"; listed, not summed) |
| `s06_resupply.py` | Resupply, 26 Jun 2025 | the edit pass's replay shape (one beat per frame, the poster the conclusion): scripts/replays/resupply.json `.pins` (price, borrowAmount, collateral, maxLTV, ltvPrecision, exchangePrecision, exchangeRateOnChain) and `.citations` (the 10^36 read from ResupplyPairCore.sol:573); the rate 10^36 ÷ price (to 22 decimals) and its floor 0 on a 0–2 grid, the check 10,000,000 × 0 × 10^5 = 0 ≤ 95,000, the exact LTV (to 16 decimals) and 5,263,158× the limit by Fraction; `replay_table("resupply", "The decisive step on each ruler")` for BL127 / BL19's line (rate exact, the borrow reverts), cross-checked against the exact values; the date from incidents.json |
| `s06b_bunni.py` | Bunni v2, 2 Sep 2025 | the edit pass's replay shape: scripts/replays/bunni.json `.start` (idle, totalSupply), `.steps.shares[0]`, `.snapshots.idle[0]` (the chain's idle fell by the floor), `.observed.afterWithdrawals.totalLiquidity`; the first withdrawal's subtrahend idle × shares / totalSupply (to 3 decimals) and its floor 23 by Fraction on a 23–24 wei grid; `bunni_replay()` for active USDC after each of the 44 withdrawals (28 to 4, one number changing beside a counter and 44 red dots); `bunni_liquidity()` and `replay_table("bunni", …)` for BL127 / BL19's line (liquidity ends at the exact form's, −0.0000009%); the loss ($8.4M, alone at 72) and date from incidents.json |
| `s06c_balancer_v2.py` | Balancer V2, 3 Nov 2025 | the edit pass's replay shape (one beat per frame, the poster the conclusion): scripts/replays/balancer.json: `.pools.osETH.swaps[23]` (the Vault's onSwap: 18 osETH-wei held, drawn as 18 balls; 17 out), `.pools.osETH.rateCacheUpdatedInTx.providerRate` (1.058132408689971699), the product 17.988250947729518883 (to 18 decimals) and its floor 17 by Fraction on a 16–19 osETH-wei grid, `.test.osETH.expectExact[1]` against the charge 625,492 (34.65% under, computed; the two charges are not drawn), `.score.*.kinds.micro` (30 + 25 = 55 in the one transaction, a counter and 55 red dots), incidents.json's loss ($121.1M, alone at 72), `.models.bl127/bl19` (−127.677 ETH projected: the product kept exact, emerald under a halo, the charge rounded up once; re-snapping to 18 would be the mulUp row, so the dot does not move to 18); docs/benchmarks/replay-balancer.md through `replay_table()` cross-checked against the JSON; no caption (provenance in the notes); the title is the one literal (C3) |
| `s06d_thetanuts.py` | Thetanuts, 15 Jun 2026 | scripts/replays/thetanuts.json: `.pre.totalSupply`, `.flashLoan.amount/.premium`, `.claim` (supplyAfter 3, storedBefore, payout, storedAfter 1), `.components[].symbol/.decimals`, `.mints[]` (amount, supplyBefore, supplyAfter, storedBefore, charge: 37 mints, 185 charges of 0), `.post.totalSupply`, `.realised` (usdcTotal, sentToBeneficiary), `.trace.pcMul/.pcDiv` (the bytecode citation: the vault's source is unverified), `.tx`, `.block`; the date and the loss line from incidents.json; the first mint's charge 1 × 2 / 3 as a Fraction (to 6 decimals) and its floor 0 on the raw-unit grid; the 37 mints rerun here with the charge rounded up (76,596,174,855 raw per component, C8: computed off-chain), cross-checked by check.py against `replay_table("thetanuts", …)`'s tables in docs/benchmarks/replay-thetanuts.md; USDC's 6 decimals are the module constant `USDC_DECIMALS` (the page writes 105,471.499078 USDC) |
| `s06e_balancer_v1.py` | Balancer V1, 31 Aug 2026 | scripts/replays/balancer_v1.json `.pools[0]` (pool 1, tx order) through `balancer_v1_replay()`: the first join at a balance of 3 satoshi (BNum's tokenInRatio 1.499999999999999997, × 3 = 4.499999999999999991 by Fraction, bmul's half-up 4, ceil 5; the join pays 4 − 3 = 1; its exact cost 1.5056462 to 7 decimals), the 438 joins across the five pools (the counter, stride `COUNT_STEP`); `replay_table("balancer-v1", …)` cross-checks BL127 / BL19 = 2 on every join against the limit of 1 ("every join would revert"); the title's date and the loss from talk/scenes/data/incidents.json |
| `s07_two.py` | Two failures, one decision | the five protocol names from `talk/scenes/data/incidents.json`, sorted into the essay's two bands (C1–C5, V27); no values on the slide (the replays carry them) |
| `s08_ladder.py` | Measure it | ladder.json `.ladder`, `.ladderLog10`, `.axisMax`; one chart morphing across scenarios `compound`, `accrual-continuous`, `adaptive-rate` (`.title` is the slide's title, swapped at each morph): `.summary[lib][N].digits.median` per library (one line each; those without a median at every N named by the key's one line, `.ops[lib]`'s reason), the margins BL19 − best 18-decimal and BL127 − best 18-decimal at N = 10,000 (two brackets, labels in the end labels' column); direct labels for BL19, BL127, ABDKMathQuad and the 18-decimal cluster (its range when the lines part); the guide's slope (1 digit per decade) from the 18-decimal line; the key (17 libraries, CAPTION, `self.key`); four sections (compound, blockulator, accrual, adaptive); no caption; bl127lib skipped |
| `s09_cliff.py` | The cliff | edges.json op `exp`, the probes with one argument in [−100, −40]: `.cells[lib].digits/zero/reverted/reasonName/unsupported` (every library with a value drawn; the key, CAPTION in `self.key`, names all 17, the ones with no dot unmarked, and its one line gives the reasons: unsupported on every probe "no exp", ParamOutOfRange on every probe "rejects negative inputs"; the red "zero" and "revert" marks are key rows); BL19's least digits (its label names the y unit, the y axis carries no numbers), BL127's last probe with a digit, the 18-decimal row's first zero; three sections (columns, zeros, bl19); no caption; bl127lib skipped |
| `s10_live.py` | Real markets, today | accrual-deployed.json `.cases[group == "live"]` `.truth[primaryTruth].deployed.digitsInterest`, `.bl127.digitsInterest` and `.bl19.digitsInterest`, faceted by `.protocol` (Aave · Morpho, counts from the data); per facet the three medians computed; row keys and tick labels in `self.key` |
| `s16_ziv.py` | What correct costs | sweep.json rows `lib=bl19 op=exp` and `lib=bl127 op=exp` (plain pass): `.n`, `.fallback`, BL127's `.inputs`; the two counters each under its library's name, one label line for both; the opcode prices ("5 gas" MUL, "393 gas" the 512-by-256-bit division) are `LITERALS` (V32); the grid of the middle sections carries no numbers; four sections (prices, fast, crosses, counters); the gas the test costs (2,716 → 2,835) is in the notes |
| `s17_proofs.py` | Knowing it's right | proofs.json `.ops[]` by lib and status (proven of the core operations: BL127 17 of 19, BL19 18 of 24), `.fuzz[]` runs (every `testFuzz_` entry 50,000); sweep.json `.rows[]` for bl19 and bl127: `.n` and `.misrounded` summed over the rows whose op is one of the 21 transcendentals (the BL127 README's list, V34: 327,488 + 168,120 = 495,608, 0 misrounded); one number a row, one known limit (V26); no `LITERALS`; four sections (proven, fuzzed, tested, limits) |
| `s12_reference.py` | There is no reference | contracts/deployments/RELEASE.json `.components.BL127.address/.version` (the address, typed into the reference's box at 35, the largest at which address and box fit the safe area; at BODY under the title from section 1); talk/scenes/data/chains.json `.chains[]` grouped by status (deployed · has CLZ, proxy present, not yet deployed · no CLZ), one Text a name column, then faded out, Sepolia's row becoming the box's pin "deployed today: Sepolia"; the 18-decimal word for exp(40) (`correctly_rounded_18(truth80())`, V9) twice, emerald (the reference) and white (your contract), "equal" with a tick; four sections (address, chains, call, closing) |
| `s01_title.py` | THE END OF ROUNDING ERRORS | no JSON: the title (the user's), `blockulator.com` (K12) and the speaker placeholder `[speaker]` (REPORT: the user's line) are `LITERALS`; the one looping scene: everything is on the first frame, the dot drifts, snaps in EMERALD under a halo and returns; `start_state == end_state` |
| `s11_budget.py` | Precision is a budget | no JSON: the essay's four bullets (essay-v7 §5) and the script's fifth line (§11) are `LITERALS`, the glyphs schematic and drawn heavy for the back row (a stretching GridLine, two bars to a sliver inside the first bar's outline with a bare `measure()`, a dot off the grid's end in RED with a cross, three `snap()`s under a loop arrow, an EMERALD `direction()`); the fifth line is two lines at HERO (15.4 units on one); six sections kept (one per spoken word) |
| `s13_not_switch.py` | Not switch. Measure. | no JSON: the script's two lines (§13), straight quotes; a RED `strike()` through "switch libraries"; the first line fades out, then the second types in, centred, on an EMERALD `glow_bar()` |
| `s14_institutions.py` | What institutions buy | no JSON: the essay's words (§7) are `LITERALS`; two lines with no axes, fees flat MUTED, errors rising RED with an arrow, each labelled at its end; the three words at HERO on EMERALD panels of one height; four sections (scales, reproducible, declared, checked) |
| `s18_habits.py` | Decide. Measure. Declare. | RELEASE.json `.components.BL127.address/.version` (the one number, in the example declaration block, mono BODY); the block's op names are BL127Lib's (`toFixed18Down`, `divUp`, `exp`, check.py finds each `function` in the source), one a line, tagged `example`; the three words at HERO beside their boxes; four sections (the block lands in declare); the habits' sub-lines are the notes |
| `s19_address.py` | The reference | RELEASE.json `.components[BL19|BL127].address/.version` (the two main addresses; check.py reads the file by a second path and checks all ten objects: each 42 characters, distinct, in its record's markdown); the two install commands and `blockulator.com/llms.txt` verbatim from README.md's Install section (K12, asserted); the repository from `git remote get-url origin`, normalised (check.py parses .git/config instead); the two `qr()` tiles' matrices regenerated from the URLs; `today: Sepolia` (V6) beside the title from the first frame. Three sections (addresses, use, links). Sizes forced by the frame (reported): version names 24 beside BODY addresses, the commands mono 28 beside their BODY key, the tiles' URLs CAPTION |
| `s20_thanks.py` | Thank you | no JSON: the user's thank-you line, on three centred lines at BODY (25.4 units on one; the brief's two would be 12.1 and 13.2), the two `qr()` tiles at 1.8 with their URLs whole, `agents: blockulator.com/llms.txt`; the matrices regenerated by check.py |
| `s15_formats.py` | Two formats | no JSON: format constants (claims K1–K4). `numbers()` derives every figure from the bit widths (vocab's `BL127_FRACTION_BITS`, `BL19_EXPONENT_BITS`, `BL19_FRACTION_BITS`; the sum 256): the field counts 1 · 127 · 128 and 1 · 19 · 236 under the `bit_bar()`, the 71 digits floor(237 · log10 2), the extremes about 10^±78,913 (mpmath; check.py by Decimal); BL127's uniform emerald grid (unlabelled) becomes BL19's magnitude axis with the 71-digit window; "overflow reverts" with a cross; four sections (bar, fixed, floating, revert) |

Each scene module exposes `numbers()`, the values it draws, and
`LITERALS`, the digit-bearing fixed strings (captions, "to 18 decimals",
a closing line) each mapped to a claim id in research_notes/talk/claims.md
or to `"REPORT"` while unverified. `uv run talk/scenes/check.py [scene…]`
recomputes `numbers()` from the loaders (by a second route where there is
one) and fails if a scene has drifted from the JSON; then it runs the
scene's `construct` under manim's dry run and reads `vocab.DRAWN`: every
drawn string with a digit must have each of its numbers in `numbers()`
(as a value, or as the scenes format one: thousands separators, one
decimal, rounded; the libraries' names, "BL127", count as names) or be a
key of `LITERALS`; anything else prints as `UNSUPPORTED` and fails, and
`REPORT` literals are listed. No drawn string may carry "…" or "½". It
also asserts the scene called every one of its `SECTIONS`, in order.

The hero of every comparison is Blockulator's own answer: `halo()` behind
a hero dot, `glow_line()` under a hero line, `glow_bar()` behind a hero
row of text; `ruler(txt, marks)` a hairline under a row of digits with a
tick and a count under every marked glyph, so decimals can be counted, and
`precision_end(txt, k, text)` the bracket at the glyph where a word's
precision ends (the digits past it are the word's own, MUTED, never red); `box(label, *content)` a named thing (a contract, a caller):
a rounded rectangle, filled with the background, around a label and
whatever is stacked beneath it; `Chart` (two GridLines at right angles, `grid()` for the
faint rules behind the data) is the deck's plot.

## The deck

`talk/deck/slides.yaml` is the deck's one source: for each of the 19
slides its title, its scene (`module.Class`), its sections in order with
the sentence of research_notes/talk/script-v2.md spoken over each one
(verbatim; `""` when the section just plays), and the script's `[you]`
notes. `make deck` runs `talk/deck/build.py`, which checks, scene by
scene, that three lists agree: the section names in manim's index (from
`make anim`), the class's `SECTIONS`, and slides.yaml; every disagreement
is printed (`MISMATCH  slide N  module.Class: index [...] != slides.yaml
[...]`) and the build fails at the end, while a scene with no render yet
is printed as `placeholder … not rendered` and gets a placeholder slide
(title and cues), so the deck builds at every stage. It writes:

- `talk/deck/index.html`: a reveal.js deck (5.1.0 vendored under
  `talk/deck/vendor/`, the site's palette in `deck.css`; nothing is
  fetched at runtime, so it opens from `file://` offline). One
  `<section>` per slide, one `<video>` per scene section referenced by
  relative path under `talk/build/` (nothing is copied): the first clip
  plays when the slide arrives, every later one is a reveal fragment that
  plays when shown and then holds its last frame (no `loop`; the title
  alone loops). Stepping back hides the fragment and rewinds it; leaving
  a slide pauses everything on it; the next slide's first clip is
  preloaded.
- `talk/deck/script.md`: the spoken script in order, one heading per
  slide, a ▶ before each section's cue with its seconds and the slide's
  cumulative start time. Print it: the speaker view over `file://` is not
  to be trusted.
- `talk/deck/talk.pdf` (`make deck-pdf`): one page per slide, the last
  section's last frame; a titled dark page for an unrendered scene.

`make talk` is `anim`, `contact`, `deck`, `deck-pdf` in that order. To
present: open `talk/deck/index.html` in Chromium or Firefox, press F for
full screen, and give one click (space, right arrow, or the clicker's
PageDown) per section; a click past the last section moves to the next
slide. Left arrow or PageUp steps back one section.

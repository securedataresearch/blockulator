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
never collides with the mark; the caller plays it in. It registers in
`DRAWN` as any `words()` does, so a title in `LITERALS` keeps its string.
Content at the top-right stays under the right mark (its bottom is at
y = 3.05) or left of it (x < 6.2); nothing shrinks for it.

## Sections: one click, one beat

A scene declares `SECTIONS = ("price", "division", …)` and calls
`self.section(i)` at each beat, in order, `section(0)` before anything
is played. `section()` closes the previous section with a hold (manim
drops a section with no play/wait silently, which would shift every
later name in the index) and the scene ends with `self.close()`, a long
hold whose last frame is the slide's poster. Nothing fades to the
background at the end: the last frame reads as a finished slide. The
deck plays one section per click and holds its last frame.

## Fonts

The site's fonts, Instrument Sans and JetBrains Mono, are served as WOFF2
in `static/fonts/`. Pango wants TTF, so `make talk-fonts`
(`talk/scenes/fonts.py`, fontTools) unwraps them into `talk/fonts/*.ttf`,
which are committed with their licence, `talk/fonts/OFL.txt` (SIL Open
Font License 1.1 for both). `vocab.setup_fonts()` registers them with
Pango per process; every text helper calls it.

## The vocabulary (`vocab.py`)

- `Palette`: the site's dark theme hex for hex (`static/css/site.css`
  :39–46; `VIOLET` and `SLATE` are blockulator.css's `color-mix` in OKLab).
  Three meanings: `EXACT` (white, the true value), `CORRECT` (emerald, the
  nearest representable value), `WRONG` (red, any other). `colour_of(lib)`
  gives a library's family colour as the site's charts do: FP127 emerald,
  FP19 white, the 18-decimal libraries gold, ABDK 64.64 sapphire, Quad
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
- `qr(url, size)`: a QR code drawn, not an image: a white rounded panel
  (`Palette.TEXT`, the quiet zone of 4 modules inside it) with the dark
  modules (`Palette.BG`) as one `VGroup` of squares, `size` units a side,
  the URL under it in mono at `SIZE_CAPTION` (through `digits()` with the
  font's ligatures left on, for the `//`), so `check.py` sees it; a URL
  with a digit needs a `LITERALS` entry. Error correction M, the smallest
  version that fits (`qrcode`, a dev dependency). `.panel`, `.modules`,
  `.label`, `.matrix` name the parts; `qr_matrix(url)` is the matrix
  alone, for `check.py` to regenerate and compare.
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
  `truth80()`: e^40 to 80 decimals by mpmath, its first 24
  decimals asserted against edges.json's truth.
- The words: `decode_fp127(raw)` and `decode_fp19(raw)` (the older names
  `fp127_value`, `fp19_value` still work) decode a cell's `.raw` word
  (FP127: raw / 2^128; FP19: binary256's fields, contracts/src/fp19/README.md
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
| `s02_exp40.py` | What is e^40? | edges.json op `exp`, probe `["40"]`: `.truth` (extended to 80 decimals by `truth80()`), `.cells[solady|balancer|prb].value` (counted in decimals of 18), `.cells[fp127|fp19].raw` decoded exactly (`decode_fp127`, `decode_fp19`: Fractions with power-of-two denominators) and drawn as their complete expansions (`exact_decimals`: 127 and 179 decimals, in lines of 50 under a `ruler()` marking every tenth decimal), the matching prefix against the truth lit and counted by eye (`matching_digits`: 57 and 73 digits, 39 and 55 decimals), the tail MUTED with a `precision_end()` bracket; labels from libraries.json |
| `s03_under.py` | exp is under everything | no JSON: `numbers()` is empty and every string is a `LITERALS` entry (the title, four row labels, their formulas with the exp term last, the hero `e^x`: V11; the closing line: V10, V11); the `→` between a formula's stages is a drawn arrow and the `²` a `<sup>2</sup>`, since Instrument Sans has neither glyph; `check.py` compares the strings, markup stripped, with the brief's table |
| `s04_grid.py` | Computers round | edges.json op `exp`, probe `["40"]`: `.truth` to 80 decimals (`truth80()`), `.cells.fp127.value`; the neighbours at every decimal and binary level, the 2^-128 words' readings to 80 decimals (they part at the 39th), computed from the truth with Fraction |
| `s05_cost.py` | $130 million | `talk/scenes/data/incidents.json` (`.incidents[]`, `.total`, `.since`; the rounding lines are essay-v6 §2's, listed, not summed) |
| `s06_resupply.py` | Resupply, 26 June 2025 | scripts/replays/resupply.json `.pins` (price, borrowAmount, collateral, maxLTV, ltvPrecision, exchangePrecision, block) and `.citations` (the two Solidity lines); every value computed from the pins |
| `s06b_bunni.py` | Bunni v2, 2 Sep 2025 | scripts/replays/bunni.json `.start` (raw0, the vault's cash/borrows/shares, idle, totalSupply), `.steps.shares[0]`, `.snapshots.idle[0]`, `.observed.swap3` and `.afterWithdrawals` `.totalLiquidity` (the −84.37%), `.tx` (the caption), `.cites[idle]` (BunniHubLogic.sol:478); `bunni_replay()` for the active USDC after each of the 44 withdrawals (28 to 4) and the mulDivUp / FP127 ends; `bunni_liquidity()` (the module's `queryLDF` per step) for the liquidity bar and the −0.0000009%; `replay_table("bunni", …)` for the FP19 row (forge's: the table alone carries it); the loss and date from talk/scenes/data/incidents.json; the first withdrawal's subtrahend idle × shares / totalSupply (to 3 decimals) and its floor computed with Fraction |
| `s06c_balancer_v2.py` | Balancer V2, 3 Nov 2025 | scripts/replays/balancer.json: `.pools.osETH.swaps[23]` (the Vault's onSwap: balances 374,353 WETH-wei / 18 osETH-wei, 17 out, 625,492 charged), `.pools.osETH.rateCacheUpdatedInTx.providerRate` (the rate, 1.058132408689971699), the product 17.988250947729518883 and its mulDown 17 / mulUp 18 by Fraction, `.test.osETH.expectExact[1]` and `.score.osETH.steps[1]` (the exact charge 957,169; 34.65% under, computed), `.score.*.kinds.micro` (30 and 25 cycles), `.score.osETH.trueInvariantStart/End`, `.onchainInvariantRatio` (D* 137,894.598 → 2,446.080, ×0.017739) with the per-cycle invariants driving the bar, `.batchSwapNetEth` (11,873.89 ETH), `.models.fp127/fp19` (0 calls below exact, −127.677 ETH projected); incidents.json's loss ($121.1M); docs/benchmarks/replay-balancer.md through `replay_table()` ("The same calls on five rulers", "What happened"), every cell cross-checked against the JSON; the citations from `.pools.osETH.source.cites`; the title is the one literal (C3) |
| `s06e_balancer_v1.py` | Balancer V1, 31 Aug 2026 | scripts/replays/balancer_v1.json `.pools[0]` (pool 1, tx order): `.state.tokens` (DPI 546.83609422, WBTC 35,748,405 satoshi), `.tx`/`.block` (the caption), `.source.lines` (BMath.sol:156-182, BNum.sol:63-73); `balancer_v1_replay()` for the first join at a balance of 3 (BNum's tokenInRatio 1.499999999999999997, × 3 = 4.499999999999999991 by Fraction, bmul's half-up 4, ceil 5, the join's exact cost 1.5056462 to 7 decimals), the 438 joins across the five pools (400 at balance 3) and the exact cost per join over all of them (1.50079 to 1.52749, C5); `balancer_v1_balances()` (the pool's balances walked op by op on the logged amounts) for the WBTC readout (the loop at 3 and 4 satoshi) and the DPI bar 546.83609422 → 0.57099095 (−99.90%); `replay_table("balancer-v1", …)` for the FP127 / FP19 column (2 on every join; forge's, the table alone carries it; cross-checked against the exact ceil) and the "What happened" row; the loss and date from talk/scenes/data/incidents.json |
| `s07_two.py` | Two failures, one decision | one row per incident, names and dates from `talk/scenes/data/incidents.json`: Resupply's rate and floor as `s06_resupply.numbers()` names them; Bunni's first idle-balance subtrahend idle × shares / totalSupply from scripts/replays/bunni.json `.start`/`.steps` (to 3 decimals) and its floor, the active balance after each of the 44 withdrawals from `bunni_replay()`; Balancer V2's 17 wei × the osETH rate in the tx (balancer.json `.pools.osETH.rateCacheUpdatedInTx.providerRate`, to 18 decimals), mulDown's 17 and the 30 micro-swap cycles from `.score.osETH.steps`; Thetanuts' first mint 2 × 1 / 3 and its 0 from thetanuts.json `.mints[0]`, 37 mints; Balancer V1's BNum tokenInRatio at a balance of 3 (pools 1–3, `balancer_v1_replay()`) × 3 (to 18 decimals) and bmul's half-up 4. Fixed strings (2/3, the ceil and toward-the-pool labels) carry claim ids C4, C5, C8 |
| `s08_ladder.py` | Measure it | ladder.json `.ladder`, `.ladderLog10`, `.axisMax`; one chart morphing across scenarios `compound`, `accrual-continuous`, `adaptive-rate`: `.summary[lib][N].digits.median` per library (one line each; those without a median at every N listed with `.ops[lib]`'s reason), the margins FP19 − best 18-decimal and FP127 − best 18-decimal at N = 10,000; fp127lib skipped |
| `s09_cliff.py` | The cliff | edges.json op `exp`, the probes with one argument in [−100, −40]: `.cells[lib].digits/zero/reverted/reasonName/unsupported` (every library with a value drawn; unsupported on every probe listed as "no exp", ParamOutOfRange on every probe as "rejects negative inputs"; fp127lib skipped); FP19's least digits, FP127's last probe with a digit |
| `s10_live.py` | Real markets, today | accrual-deployed.json `.cases[group == "live"]` `.truth[primaryTruth].deployed.digitsInterest`, `.fp127.digitsInterest` and `.fp19.digitsInterest`, faceted by `.protocol` (Aave · Morpho, counts from the data); per facet and overall the three medians and the margins between them computed; `.survey.block/.date` |
| `s16_ziv.py` | What correct costs | sweep.json rows `lib=fp19 op=exp` and `lib=fp127 op=exp` (plain pass): `.n`, `.fallback`, FP127's `.inputs`; gas.json `.ops.exp.typical.gas.lib`'s median through `gas("exp")` (2,835); the pre-test figure 2,716 is a module constant (contracts/deployments/FP127.md, claim V19) and the percentage is computed; the opcode prices (MUL 5, divh 393) are `LITERALS` (V32); the grid of the middle sections carries no numbers |
| `s17_proofs.py` | Knowing it's right | proofs.json `.ops[]` by lib and status (FP127's 17 proven: 16 whose `.tool` is Halmos, sqrt by exact integers; its 2 fuzzed, gavg and hypot; FP19's 18 proven of 24, six fuzzed), `.fuzz[]` runs (every `testFuzz_` entry 50,000); sweep.json `.rows[]` for fp19 and fp127: `.n` and `.misrounded` summed per library over every row (455,082 / 212,119, 0 misrounded) and over the rows whose op is one of the 21 transcendentals (the FP127 README's "The transcendentals round to nearest" list, V34: 327,488 / 168,120); the oracles' digits (300 / 200) parsed from `._doc`; the limits' 0.92 and 0.79 and the footnote are `LITERALS` (V38, V52); row 4's two limits play as two held sub-beats inside one section |
| `s12_reference.py` | There is no reference | contracts/deployments/RELEASE.json `.components.FP127.address/.version` (the address, typed in; it fits the frame only below SIZE_HERO); talk/scenes/data/chains.json `.chains[]` (chain, clz_since, status, deployed, proxy; `.probed`, the caption): one row per chain in the README's order, "deployed" on the `deployed` row alone, "has CLZ · proxy present · not yet deployed" where `proxy` is true, "no CLZ" with a cross on the unsupported; the exp(40) word to 18 decimals from `correctly_rounded_18(truth80())`, typed twice (the reference's and your contract's, the same string); `box()` for the two contracts |
| `s15_formats.py` | Two formats | no JSON: format constants (claims K1–K4, E9). `numbers()` derives every figure from the bit widths (vocab's `FP127_FRACTION_BITS`, `FP19_EXPONENT_BITS`, `FP19_FRACTION_BITS`; the sum 256): the fields 1 · 127 · 128 and 1 · 19 · 236, the 237-bit significand, the digit counts floor(bits · log10 2) (38, 71), FP127's range 2^127 to one decimal (about ±1.7 × 10^38), FP19's extremes 2^−262142 and (2 − 2^−236) · 2^262144 as powers of ten (about 10^±78,913) by mpmath; check.py recomputes each with Decimal. `bit_bar()` for the word; the window's stops carry no digits; "laid out as IEEE 754 binary256" is the one literal (E9) |

Each scene module exposes `numbers()`, the values it draws, and
`LITERALS`, the digit-bearing fixed strings (captions, "to 18 decimals",
a closing line) each mapped to a claim id in research_notes/talk/claims.md
or to `"REPORT"` while unverified. `uv run talk/scenes/check.py [scene…]`
recomputes `numbers()` from the loaders (by a second route where there is
one) and fails if a scene has drifted from the JSON; then it runs the
scene's `construct` under manim's dry run and reads `vocab.DRAWN`: every
drawn string with a digit must have each of its numbers in `numbers()`
(as a value, or as the scenes format one: thousands separators, one
decimal, rounded; the libraries' names, "FP127", count as names) or be a
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

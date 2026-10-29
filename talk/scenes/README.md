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
  JSONs), and `truth80()`: e^40 to 80 decimals by mpmath, its first 24
  decimals asserted against edges.json's truth.
- The words: `fp127_value(raw)` and `fp19_value(raw)` decode a cell's
  `.raw` word (FP127: 128 fraction bits; FP19: binary256's layout) to a
  Fraction; `to_decimals(q, places)` writes it, nearest, half-up.
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
| `s02_exp40.py` | What is e^40? | edges.json op `exp`, probe `["40"]`: `.truth` (extended to 80 decimals by `truth80()`), `.cells[solady|balancer|prb].value` (counted in decimals of 18), `.cells[fp19|fp127].raw` decoded and written to 80 decimals, their matching digits against the truth counted by eye; labels from libraries.json |
| `s03_under.py` | exp is under everything | no JSON: `numbers()` is empty and every string is a `LITERALS` entry (the title, four row labels, their formulas with the exp term last, the hero `e^x`: V11; the closing line: V10, V11); the `→` between a formula's stages is a drawn arrow and the `²` a `<sup>2</sup>`, since Instrument Sans has neither glyph; `check.py` compares the strings, markup stripped, with the brief's table |
| `s04_grid.py` | Computers round | edges.json op `exp`, probe `["40"]`: `.truth` to 80 decimals (`truth80()`), `.cells.fp127.value`; the neighbours at every decimal and binary level, the 2^-128 words' readings to 80 decimals (they part at the 39th), computed from the truth with Fraction |
| `s05_cost.py` | $130 million | `talk/scenes/data/incidents.json` (`.incidents[]`, `.total`, `.since`; the rounding lines are essay-v6 §2's, listed, not summed) |
| `s06_resupply.py` | Resupply, 26 June 2025 | scripts/replays/resupply.json `.pins` (price, borrowAmount, collateral, maxLTV, ltvPrecision, exchangePrecision, block) and `.citations` (the two Solidity lines); every value computed from the pins |
| `s08_ladder.py` | Measure it | ladder.json `.ladder`, `.ladderLog10`, `.axisMax`; one chart morphing across scenarios `compound`, `accrual-continuous`, `adaptive-rate`: `.summary[lib][N].digits.median` per library (one line each; those without a median at every N listed with `.ops[lib]`'s reason), the margins FP19 − best 18-decimal and FP127 − best 18-decimal at N = 10,000; fp127lib skipped |
| `s09_cliff.py` | The cliff | edges.json op `exp`, the probes with one argument in [−100, −40]: `.cells[lib].digits/zero/reverted/reasonName/unsupported` (every library with a value drawn; unsupported on every probe listed as "no exp", ParamOutOfRange on every probe as "rejects negative inputs"; fp127lib skipped); FP19's least digits, FP127's last probe with a digit |
| `s10_live.py` | Real markets, today | accrual-deployed.json `.cases[group == "live"]` `.truth[primaryTruth].deployed.digitsInterest`, `.fp127.digitsInterest` and `.fp19.digitsInterest`; the three medians and the margins between them computed; `.survey.block/.date` |
| `s16_ziv.py` | What correct costs | sweep.json rows `lib=fp19 op=exp` and `lib=fp127 op=exp` (plain pass): `.n`, `.fallback`, FP127's `.inputs`; gas.json `.ops.exp.typical.gas.lib`'s median through `gas("exp")` (2,835); the pre-test figure 2,716 is a module constant (contracts/deployments/FP127.md, claim V19) and the percentage is computed; the opcode prices (MUL 5, divh 393) are `LITERALS` (V32); the grid of the middle sections carries no numbers |
| `s12_reference.py` | There is no reference | contracts/deployments/RELEASE.json `.components.FP127.address/.version` (the address, typed in; it fits the frame only below SIZE_HERO); talk/scenes/data/chains.json `.chains[]` (chain, clz_since, status, deployed, proxy; `.probed`, the caption): one row per chain in the README's order, "deployed" on the `deployed` row alone, "has CLZ · proxy present · not yet deployed" where `proxy` is true, "no CLZ" with a cross on the unsupported; the exp(40) word to 18 decimals from `correctly_rounded_18(truth80())`, typed twice (the reference's and your contract's, the same string); `box()` for the two contracts |

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
row of text; `box(label, *content)` a named thing (a contract, a caller):
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

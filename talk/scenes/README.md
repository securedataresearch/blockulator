# The talk's scenes

One manim file per animated slide of *The End of Rounding Errors*, sharing
one vocabulary (`vocab.py`) so the deck has one look. Every number on
screen is read from the repo's JSON at render time; nothing is typed in.

## Render

```sh
make anim                   # every scene, 1080p 30 fps, into talk/build/videos/<scene>/1080p30/
make anim SCENE=s02_exp40   # one scene
uv run manim -ql talk/scenes/s04_grid.py Grid     # a 480p preview while editing
uv run manim -qh -s talk/scenes/s02_exp40.py      # the last frame only, as PNG
```

`make anim` runs `talk/scenes/check.py` first (below). manim is a dev
dependency (`uv add --dev manim`, pinned in `pyproject.toml`); it needs
cairo, pango and ffmpeg from the system. `talk/build/` and manim's default
`media/` are git-ignored; rendered mp4s are build outputs, like the tables.

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
  Pango markup (`<sup>`, `<sub>`).
- `GridLine`: a `NumberLine` drawn as the grid of representable values
  (faint, ticks, no numbers). `dot_at(x, colour)`, `nearest_tick(x)`.
- `snap(dot, line, to_tick, colour)`: the one verb. The dot slides to the
  tick, swells and settles in the colour of what it became.
- `measure(line, a, b, label)`: a thin `|——|` bracket under the line naming
  a distance; `measure_up(p_lo, p_hi, label)` is the same stood on end, how
  a chart names the margin between two line ends in its own units.
- `DeckScene`: dark background, fonts registered, 30 fps, output under
  `talk/build/`; `self.caption(text)` returns the animation that puts the
  source of the numbers in the bottom-left corner.
- Loaders, all by path from the repo root: `libs()` (static/data/libraries.json
  → `{id: record}`) and `talk_libs()` (the same less BlockulatorWad: the 17
  every comparison accounts for), `edges(op)` and `probe(op, *args)`
  (docs/benchmarks/edges.json), `ladder(scenario)` (docs/benchmarks/ladder.json
  → `{"N", "log10", "scenario"}`) with `ladder_median(cell)` (`.digits.median`,
  or a bare `.digits` in older files) and `ladder_reason(scenario, lib)` ("not
  offered" when `.ops[lib]` is `["unsupported"]`), `live()`
  (docs/benchmarks/accrual-deployed.json, the 326 `group == "live"` cases),
  `resupply()` (scripts/replays/resupply.json).
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
| `s02_exp40.py` | What is e^40? | edges.json op `exp`, probe `["40"]`: `.truth`, `.cells[solady|balancer|prb|fp19|fp127].value`, `.cells[fp19|fp127].digits` (the three counted in decimals of 18; FP127's decimals beyond 18 from its `.digits`); labels from libraries.json |
| `s04_grid.py` | Computers round | edges.json op `exp`, probe `["40"]`: `.truth`, `.cells.fp127.value`; the 10^-18 and 2^-128 neighbours computed from the truth with Fraction |
| `s05_cost.py` | $130 million | `talk/scenes/data/incidents.json` (`.incidents[]`, `.total`, `.since`; the rounding lines are essay-v6 §2 verbatim, the sum adds `.lossUsd`) |
| `s06_resupply.py` | Resupply, 26 June 2025 | scripts/replays/resupply.json `.pins` (price, borrowAmount, collateral, maxLTV, ltvPrecision, exchangePrecision, block) and `.citations` (the two Solidity lines); every value computed from the pins |
| `s08_ladder.py` | Measure it | ladder.json `.ladder`, `.ladderLog10`, `.axisMax`; one chart morphing across scenarios `compound`, `accrual-continuous`, `adaptive-rate`: `.summary[lib][N].digits.median` per library (one line each; those without a median at every N listed with `.ops[lib]`'s reason), the margins FP19 − best 18-decimal and FP127 − best 18-decimal at N = 10,000; fp127lib skipped |
| `s09_cliff.py` | The cliff | edges.json op `exp`, the probes with one argument in [−100, −40]: `.cells[lib].digits/zero/reverted/reasonName/unsupported` (every library with a value drawn; unsupported on every probe listed as "no exp", ParamOutOfRange on every probe as "rejects negative inputs"; fp127lib skipped); FP19's least digits, FP127's last probe with a digit |
| `s10_live.py` | Real markets, today | accrual-deployed.json `.cases[group == "live"]` `.truth[primaryTruth].deployed.digitsInterest`, `.fp127.digitsInterest` and `.fp19.digitsInterest`; the three medians and the margins between them computed; `.survey.block/.date` |

Each scene module exposes `numbers()`, the values it draws.
`uv run talk/scenes/check.py [scene…]` recomputes them from the loaders
(by a second route where there is one) and fails if a scene has drifted
from the JSON.

The hero of every comparison is Blockulator's own answer: `halo()` behind
a hero dot, `glow_line()` under a hero line, `glow_bar()` behind a hero
row of text; `Chart` (two GridLines at right angles, `grid()` for the
faint rules behind the data) is the deck's plot.

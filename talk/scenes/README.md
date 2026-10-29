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
  a distance.
- `DeckScene`: dark background, fonts registered, 30 fps, output under
  `talk/build/`; `self.caption(text)` returns the animation that puts the
  source of the numbers in the bottom-left corner.
- Loaders, all by path from the repo root: `libs()` (static/data/libraries.json
  → `{id: record}`), `edges(op)` and `probe(op, *args)` (docs/benchmarks/edges.json),
  `ladder(scenario)` (docs/benchmarks/ladder.json → `{"N", "log10", "scenario"}`),
  `live()` (docs/benchmarks/accrual-deployed.json, the 326 `group == "live"` cases),
  `resupply()` (scripts/replays/resupply.json).
- `correctly_rounded_18(truth)`: the nearest 18-decimal value, ties away
  from zero (no probe in edges.json is a tie). `correct_digits(value, truth)`
  = floor(−log10(|value − truth| / truth)), the measure edges.json reports as
  `.digits`. `first_wrong_index(value, truth)`: where the strings part.

## Scenes

| file | slide | numbers from |
|---|---|---|
| `s02_exp40.py` | What is e^40? | edges.json op `exp`, probe `["40"]`: `.truth`, `.cells[solady|balancer|prb].value`; labels from libraries.json |
| `s04_grid.py` | Computers round | none: the vocabulary itself |

Each scene module exposes `numbers()`, the values it draws.
`uv run talk/scenes/check.py [scene…]` recomputes them from the loaders
and fails if a scene has drifted from the JSON.

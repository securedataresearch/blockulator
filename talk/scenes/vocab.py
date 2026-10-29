"""The deck's shared vocabulary: palette, fonts, the grid, the snap, the data.

Every scene in talk/scenes imports from here so the whole deck has one look:

  the site's dark palette (static/css/site.css, blockulator.css) and its two
  fonts (Instrument Sans for words, JetBrains Mono for digits);
  a number line is "the grid" (GridLine), a value is a Dot, rounding is the
  dot snapping to a tick (snap);
  three colours mean three things: EXACT (white) is the true value, CORRECT
  (emerald) is the nearest tick, WRONG (red) is any other tick.

Numbers are never typed into a scene. The loaders at the bottom read the
repo's JSON (docs/benchmarks/*.json, scripts/replays/*.json,
static/data/libraries.json) by path from the repo root, and each scene
exposes a numbers() function so talk/scenes/check.py can compare what it
draws with what the loaders return.
"""

from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal, localcontext
from pathlib import Path

from manim import (
    DOWN,
    UP,
    LEFT,
    AnimationGroup,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    MarkupText,
    NumberLine,
    Scene,
    Succession,
    Transform,
    VGroup,
    Text,
    config,
)
import manimpango
from manim.utils.rate_functions import ease_in_out_cubic, ease_out_cubic

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "talk" / "fonts"


# ---------------------------------------------------------------- palette --
class Palette:
    """The site's dark theme, hex for hex (site.css :39–46; the mixes in
    blockulator.css :52 are computed in OKLab as color-mix does)."""

    BG = "#0c0e10"
    TEXT = "#f6f6f3"  # --text-strong
    BODY = "#e2e3df"  # --text
    MUTED = "#b3b5b0"
    FAINT = "#9a9d97"
    RULE = "#5a5e62"
    EMERALD = "#43b592"  # FP127, "ours"
    GOLD = "#d3c68a"  # the 18-decimal (WAD) libraries
    SAPPHIRE = "#86b4e2"  # ABDK 64.64
    RED = "#ff6079"  # wrong, zero, revert
    VIOLET = "#c896b4"  # ABDKMathQuad: color-mix(in oklab, sapphire 55%, red)
    SLATE = "#91a9bd"  # the protocols: color-mix(in oklab, sapphire 50%, faint)

    # the three meanings
    EXACT = TEXT
    CORRECT = EMERALD
    WRONG = RED


FAMILY_COLOUR = {
    "fp127": Palette.EMERALD,
    "fp19": Palette.TEXT,
    "wad": Palette.GOLD,
    "quad": Palette.VIOLET,
    "6464": Palette.SAPPHIRE,
    "protocol": Palette.SLATE,
}


def colour_of(lib: dict) -> str:
    """One colour per family, as the site's charts (blockulator.css :53)."""
    return FAMILY_COLOUR[lib["family"]]


# ------------------------------------------------------------------ fonts --
SANS = "Instrument Sans"
MONO = "JetBrains Mono"

_fonts_registered = False


def setup_fonts() -> None:
    """Register talk/fonts/*.ttf with Pango (converted from static/fonts/*.woff2
    by fontTools; OFL, see talk/fonts/OFL.txt). Idempotent."""
    global _fonts_registered
    if _fonts_registered:
        return
    for name in ("InstrumentSans.ttf", "InstrumentSans-Italic.ttf", "JetBrainsMono.ttf"):
        path = FONT_DIR / name
        if not path.exists():
            raise FileNotFoundError(f"{path}: run `make talk-fonts` (see talk/scenes/README.md)")
        manimpango.register_font(str(path))  # persistent (manim's register_font is a context manager)
    _fonts_registered = True


def words(s: str, size: float = 36, colour: str = Palette.TEXT, **kw) -> Text:
    """Text in Instrument Sans."""
    setup_fonts()
    return Text(s, font=SANS, font_size=size, color=colour, **kw)


def markup(s: str, size: float = 36, colour: str = Palette.TEXT, **kw) -> MarkupText:
    """Pango markup in Instrument Sans: <sup>, <sub>, <i>, <b> (Pango ≥ 1.50)."""
    setup_fonts()
    return MarkupText(s, font=SANS, font_size=size, color=colour, **kw)


def digits(s: str, size: float = 36, colour: str = Palette.TEXT, **kw) -> Text:
    """Text in JetBrains Mono, ligatures off so every glyph is one character
    (the scenes index into digit strings)."""
    setup_fonts()
    return Text(s, font=MONO, font_size=size, color=colour, disable_ligatures=True, **kw)


# ------------------------------------------------------------- the scene --
# 1920x1080 comes from -qh; the frame rate and background are the deck's.
config.frame_rate = 30
config.background_color = Palette.BG
config.media_dir = str(ROOT / "talk" / "build")


class DeckScene(Scene):
    """Dark background, the fonts registered, a caption slot bottom-left
    for the source of the numbers on screen."""

    def setup(self):
        setup_fonts()
        self.camera.background_color = Palette.BG
        self._caption = None

    def caption(self, text: str, size: float = 20, run_time: float = 0.6):
        """Put (or replace) the small source caption in the bottom-left corner.
        Returns the animation to play."""
        new = words(text, size, Palette.FAINT).to_corner(DOWN + LEFT, buff=0.45)
        old, self._caption = self._caption, new
        if old is None:
            return FadeIn(new, run_time=run_time)
        return AnimationGroup(FadeOut(old, run_time=run_time), FadeIn(new, run_time=run_time))


# --------------------------------------------------------------- the grid --
class GridLine(NumberLine):
    """A number line drawn as the grid of representable values: faint, thin,
    ticks only (no numbers unless asked)."""

    def __init__(self, x_range=(0, 10, 1), length=10.0, colour=Palette.FAINT, tick_size=0.12, **kw):
        kw.setdefault("include_numbers", False)
        kw.setdefault("stroke_width", 2)
        super().__init__(x_range=list(x_range), length=length, color=colour, tick_size=tick_size, **kw)
        self.set_stroke(opacity=0.9)

    def dot_at(self, x: float, colour: str = Palette.EXACT, radius: float = 0.11) -> Dot:
        return Dot(self.n2p(x), radius=radius, color=colour)

    def nearest_tick(self, x: float) -> float:
        """The tick nearest x (ties go up, as correctly_rounded_18 does)."""
        step = self.x_range[2]
        q = Decimal(str(x)) / Decimal(str(step))
        return float(q.quantize(Decimal(1), rounding=ROUND_HALF_UP) * Decimal(str(step)))


def snap(dot: Dot, line: GridLine, to_tick: float, colour: str, run_time: float = 0.9):
    """The vocabulary's one verb: a value slides to a tick and settles there,
    taking the colour of what it became (CORRECT, WRONG, or EXACT)."""
    # explicit targets: .animate builders would each copy the dot's state now,
    # so chained ones would pull it back to where it started
    at_tick = dot.copy().move_to(line.n2p(to_tick))
    swollen = at_tick.copy().scale(1.45).set_color(colour)
    settled = at_tick.copy().set_color(colour)
    return Succession(
        Transform(dot, at_tick, run_time=run_time * 0.65, rate_func=ease_in_out_cubic),
        Transform(dot, swollen, run_time=run_time * 0.15, rate_func=ease_out_cubic),
        Transform(dot, settled, run_time=run_time * 0.2, rate_func=ease_out_cubic),
    )


def measure(line: GridLine, a: float, b: float, label: str, scale: float = 1.0, drop: float = 0.45, colour: str = Palette.MUTED) -> VGroup:
    """A thin bracket |——| under the line from tick a to b with a label
    beneath: the vocabulary's way of naming a distance on the grid."""
    y = DOWN * drop * scale
    cap = UP * 0.07 * scale
    pa, pb = line.n2p(a) + y, line.n2p(b) + y
    bar = Line(pa, pb, color=colour, stroke_width=1.5)
    caps = VGroup(Line(pa - cap, pa + cap, color=colour, stroke_width=1.5), Line(pb - cap, pb + cap, color=colour, stroke_width=1.5))
    text = words(label, 32, colour).scale(scale).next_to(bar, DOWN, buff=0.1 * scale)
    return VGroup(bar, caps, text)


# ---------------------------------------------------------------- numbers --
def _load(rel: str):
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def libs() -> dict[str, dict]:
    """static/data/libraries.json → {id: record}, in file order."""
    return {lib["id"]: lib for lib in _load("static/data/libraries.json")["libraries"]}


def edges(op: str) -> dict:
    """docs/benchmarks/edges.json → the op record (its .probes[] carry .args,
    .truth and .cells[lib] = {value, digits, zero, reverted, unsupported…})."""
    for rec in _load("docs/benchmarks/edges.json")["ops"]:
        if rec["id"] == op:
            return rec
    raise KeyError(op)


def probe(op: str, *args: str) -> dict:
    """One probe of an op by its args, e.g. probe("exp", "40")."""
    for p in edges(op)["probes"]:
        if p["args"] == list(args):
            return p
    raise KeyError((op, args))


def ladder(scenario: str) -> dict:
    """docs/benchmarks/ladder.json → {"N": [1, 2, …, 10000], "log10": {…},
    "scenario": the scenario record (its .summary[lib][N].digits)}."""
    d = _load("docs/benchmarks/ladder.json")
    for s in d["scenarios"]:
        if s["id"] == scenario:
            return {"N": d["ladder"], "log10": d["ladderLog10"], "scenario": s}
    raise KeyError(scenario)


def live() -> list[dict]:
    """docs/benchmarks/accrual-deployed.json → the cases with group "live"
    (one per deployed Aave reserve and Morpho market)."""
    return [c for c in _load("docs/benchmarks/accrual-deployed.json")["cases"] if c["group"] == "live"]


def resupply() -> dict:
    """scripts/replays/resupply.json, whole: .pins, .checks, .state, .sources…"""
    return _load("scripts/replays/resupply.json")


def correctly_rounded_18(truth: str) -> str:
    """The nearest 18-decimal value to a decimal string.

    Rounds to nearest; a tie (digits beyond the 18th exactly 5000…) goes
    away from zero (ROUND_HALF_UP), which is the convention the WAD
    libraries' mulDiv-with-rounding helpers use. No probe in edges.json
    is a tie (exp(40)'s 19th decimal onward is 4804…), so for the deck
    the tie rule never decides.
    """
    with localcontext() as ctx:
        ctx.prec = 200
        return str(Decimal(truth).quantize(Decimal(1).scaleb(-18), rounding=ROUND_HALF_UP))


def correct_digits(value: str, truth: str) -> int:
    """Correct significant digits of value against truth:
    floor(−log10(|value − truth| / |truth|)); the measure edges.json reports
    as .digits (there it is kept to one decimal)."""
    with localcontext() as ctx:
        ctx.prec = 200
        v, t = Decimal(value), Decimal(truth)
        if v == t:
            return 10**9
        rel = abs(v - t) / abs(t)
        return int((-rel.log10()).to_integral_value(rounding="ROUND_FLOOR"))


def first_wrong_index(value: str, truth: str) -> int | None:
    """Index of the first character where value departs from truth
    (both decimal strings aligned on the point), or None if value is a
    prefix of truth."""
    vi, _, vf = value.partition(".")
    ti, _, tf = truth.partition(".")
    if vi != ti:
        for i, (a, b) in enumerate(zip(vi.rjust(len(ti)), ti)):
            if a != b:
                return i
        return min(len(vi), len(ti))
    for i, (a, b) in enumerate(zip(vf, tf)):
        if a != b:
            return len(ti) + 1 + i
    return None

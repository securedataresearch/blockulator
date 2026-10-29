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

import importlib.util
import json
import re
import statistics
import sys
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from pathlib import Path

from manim import (
    DOWN,
    PI,
    UP,
    LEFT,
    RIGHT,
    AnimationGroup,
    Arrow,
    Circle,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    MarkupText,
    NumberLine,
    RoundedRectangle,
    Scene,
    Succession,
    Transform,
    VGroup,
    Text,
    config,
)
import manimpango
import numpy as np
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

# legibility from the back row (plan, structural decision 5)
SIZE_CAPTION = 20  # the source caption, small labels
SIZE_BODY = 32  # a row of digits, a formula
SIZE_HERO = 48  # the one number a slide is about
MAX_MONO_CHARS = 46  # a mono string at SIZE_BODY fits the frame to this length

# every string the text helpers are asked to draw, in order, the raw string
# before Pango markup; check.py reads it after a dry run of construct()
DRAWN: list[str] = []


def reset_drawn() -> None:
    DRAWN.clear()

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
    DRAWN.append(s)
    return Text(s, font=SANS, font_size=size, color=colour, **kw)


def markup(s: str, size: float = 36, colour: str = Palette.TEXT, **kw) -> MarkupText:
    """Pango markup in Instrument Sans: <sup>, <sub>, <i>, <b> (Pango ≥ 1.50)."""
    setup_fonts()
    DRAWN.append(s)
    return MarkupText(s, font=SANS, font_size=size, color=colour, **kw)


def digits(s: str, size: float = 36, colour: str = Palette.TEXT, **kw) -> Text:
    """Text in JetBrains Mono, ligatures off so every glyph is one character
    (the scenes index into digit strings)."""
    setup_fonts()
    DRAWN.append(s)
    return Text(s, font=MONO, font_size=size, color=colour, disable_ligatures=True, **kw)


# ------------------------------------------------------------- the scene --
# 1920x1080 comes from -qh; the frame rate and background are the deck's.
config.frame_rate = 30
config.background_color = Palette.BG
config.media_dir = str(ROOT / "talk" / "build")
# one mp4 per section plus an index, under <media_dir>/videos/<scene>/<quality>/sections/:
# {Scene}_{nnnn}_{name}.mp4 and {Scene}.json (name, video, duration, nb_frames, …)
config.save_sections = True

END_HOLD = 3.0  # the last section's hold: its last frame is the slide's poster


class DeckScene(Scene):
    """Dark background, the fonts registered, a caption slot bottom-left
    for the source of the numbers on screen, and the clicker's sections.

    A scene declares SECTIONS = ("price", "division", …) and calls
    self.section(i) at each beat, in order, starting with section(0)
    before anything is played. section() closes the previous section
    with a hold (manim silently drops a section with no play/wait, which
    would shift every later name in the index) and ends with
    self.close(), the long hold whose last frame is the slide's poster.
    check.py asserts sections_called == list(SECTIONS)."""

    SECTIONS: tuple[str, ...] = ()

    def setup(self):
        setup_fonts()
        self.camera.background_color = Palette.BG
        self._caption = None
        self.sections_called: list[str] = []

    def section(self, i: int, hold: float = 1.0) -> None:
        """Start SECTIONS[i]; i must be the next index. The previous section
        gets its closing hold first, so no section is ever empty."""
        assert i == len(self.sections_called), (i, self.sections_called)
        assert i < len(self.SECTIONS), (i, self.SECTIONS)
        if i:
            self.wait(hold)
        name = self.SECTIONS[i]
        self.next_section(name)
        self.sections_called.append(name)

    def close(self, hold: float = END_HOLD) -> None:
        """The final hold: every section must have been called."""
        assert self.sections_called == list(self.SECTIONS), (self.sections_called, self.SECTIONS)
        self.wait(hold)

    def caption(self, text: str, size: float = SIZE_CAPTION, run_time: float = 0.6):
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
    text = words(label, SIZE_BODY, colour).scale(scale).next_to(bar, DOWN, buff=0.1 * scale)
    return VGroup(bar, caps, text)


def measure_up(p_lo, p_hi, label: str, colour: str = Palette.MUTED, size: float = SIZE_CAPTION, cap: float = 0.07, buff: float = 0.12, stroke_width: float = 1.5) -> VGroup:
    """The bracket stood on end: a thin vertical |——| from the scene point
    p_lo up to p_hi with the label to its right, centred on the span: how
    the chart names a margin between two line ends in the axis's units."""
    p_lo, p_hi = np.array(p_lo, dtype=float), np.array(p_hi, dtype=float)
    bar = Line(p_lo, p_hi, color=colour, stroke_width=stroke_width)
    caps = VGroup(Line(p_lo + LEFT * cap, p_lo + RIGHT * cap, color=colour, stroke_width=stroke_width), Line(p_hi + LEFT * cap, p_hi + RIGHT * cap, color=colour, stroke_width=stroke_width))
    text = words(label, size, colour).next_to(bar, RIGHT, buff=buff)
    return VGroup(bar, caps, text)


def direction(line: GridLine, x_from: float, x_to: float, colour: str, lift: float = 0.3) -> Arrow:
    """The direction a rounding took, drawn just above the line; the tip and
    stroke are fixed so a short arrow reads like a long one."""
    return Arrow(
        line.n2p(x_from) + UP * lift,
        line.n2p(x_to) + UP * lift,
        buff=0.05,
        color=colour,
        stroke_width=2.5,
        tip_length=0.11,
        max_tip_length_to_length_ratio=1.0,
        max_stroke_width_to_length_ratio=100.0,
    )


def check_mark(colour: str = Palette.CORRECT, size: float = 0.32, stroke_width: float = 4.0) -> VGroup:
    """A tick, drawn (no font carries one): the short stroke down, the long
    stroke up. Centred on the origin."""
    a = np.array([-0.5, 0.05, 0]) * size
    b = np.array([-0.15, -0.35, 0]) * size
    c = np.array([0.55, 0.5, 0]) * size
    return VGroup(Line(a, b, color=colour, stroke_width=stroke_width), Line(b, c, color=colour, stroke_width=stroke_width))


def cross_mark(colour: str = Palette.WRONG, size: float = 0.32, stroke_width: float = 4.0) -> VGroup:
    """A cross, drawn, the same size as check_mark."""
    s = 0.42 * size
    return VGroup(
        Line([-s, -s, 0], [s, s, 0], color=colour, stroke_width=stroke_width),
        Line([-s, s, 0], [s, -s, 0], color=colour, stroke_width=stroke_width),
    )


def midpoint(line: GridLine, a: float, b: float, colour: str = Palette.FAINT, height: float = 0.9, stroke_width: float = 1.5, dash_length: float = 0.05) -> DashedLine:
    """The rounding boundary: a dashed line stood through the middle of the
    gap between ticks a and b, half a unit from each. A value on one side
    rounds to a, on the other to b; a bound that reaches it could change
    the rounding. It moves with the grid under a stretch (it is a line in
    the scene, so stretch it with the grid)."""
    p = line.n2p((a + b) / 2)
    return DashedLine(p + DOWN * height / 2, p + UP * height / 2, color=colour, stroke_width=stroke_width, dash_length=dash_length)


def error_bar(dot: Dot, half_width: float, colour: str, cap: float = 0.2, stroke_width: float = 3.0) -> VGroup:
    """The bound a fast value carries: a horizontal bracket |——|, centred
    on the dot, half_width scene units either side (the true value lies
    within it). CORRECT (emerald) when it clears the midpoint, WRONG (red)
    when it crosses it. The bar is drawn through the dot's centre; keep
    the dot in front of it."""
    c = dot.get_center()
    pa, pb = c + LEFT * half_width, c + RIGHT * half_width
    up = UP * cap / 2
    bar = Line(pa, pb, color=colour, stroke_width=stroke_width)
    caps = VGroup(Line(pa - up, pa + up, color=colour, stroke_width=stroke_width), Line(pb - up, pb + up, color=colour, stroke_width=stroke_width))
    return VGroup(bar, caps)


# --------------------------------------------------------------- the chart --
class Chart(VGroup):
    """Two GridLines at right angles: the deck's plot. Values are dots on
    it, as on the grid. x_range and y_range are (min, max, step) in data
    units; the ticks are the steps. c2p maps data to the scene; x_label /
    y_label put a small faint label at a tick; x_title / y_title name the
    axes. Everything added through these methods is part of the group."""

    def __init__(self, x_range, y_range, width: float, height: float, origin=(0.0, 0.0, 0.0), tick_size: float = 0.1):
        super().__init__()
        self.origin = np.array(origin, dtype=float)
        self.x_range, self.y_range, self.width, self.height = x_range, y_range, width, height
        self.x_axis = GridLine(x_range, length=width, colour=Palette.RULE, tick_size=tick_size)
        self.x_axis.shift(self.origin - self.x_axis.n2p(x_range[0]))
        self.y_axis = GridLine(y_range, length=height, colour=Palette.RULE, tick_size=tick_size, rotation=PI / 2)
        self.y_axis.shift(self.origin - self.y_axis.n2p(y_range[0]))
        self.labels = VGroup()
        self.titles = VGroup()
        self.add(self.x_axis, self.y_axis, self.labels, self.titles)

    def c2p(self, x: float, y: float):
        return self.origin + RIGHT * (self.x_axis.n2p(x) - self.origin)[0] + UP * (self.y_axis.n2p(y) - self.origin)[1]

    def x_label(self, x: float, text: str, size: float = SIZE_CAPTION, colour: str = Palette.FAINT, buff: float = 0.18, use_markup: bool = False, mono: bool = False):
        make = markup if use_markup else (digits if mono else words)
        t = make(text, size, colour).next_to(self.c2p(x, self.y_range[0]), DOWN, buff=buff)
        self.labels.add(t)
        return t

    def y_label(self, y: float, text: str, size: float = SIZE_CAPTION, colour: str = Palette.FAINT, buff: float = 0.18, mono: bool = False):
        t = (digits if mono else words)(text, size, colour).next_to(self.c2p(self.x_range[0], y), LEFT, buff=buff)
        self.labels.add(t)
        return t

    def x_title(self, text: str, size: float = 22, colour: str = Palette.MUTED, drop: float = 0.72):
        t = words(text, size, colour).move_to(self.c2p((self.x_range[0] + self.x_range[1]) / 2, self.y_range[0]) + DOWN * drop)
        self.titles.add(t)
        return t

    def y_title(self, text: str, size: float = 22, colour: str = Palette.MUTED, gap: float = 0.95):
        t = words(text, size, colour).rotate(PI / 2).move_to(self.c2p(self.x_range[0], (self.y_range[0] + self.y_range[1]) / 2) + LEFT * gap)
        self.titles.add(t)
        return t

    def dot(self, x: float, y: float, colour: str, radius: float = 0.07, **kw) -> Dot:
        return Dot(self.c2p(x, y), radius=radius, color=colour, **kw)

    def grid(self, opacity: float = 0.22) -> VGroup:
        """Faint rules across the plot at every tick, behind the data
        (depth: the grid is the background, the values are crisp)."""
        g = VGroup()
        x0, x1, xs = self.x_range
        y0, y1, ys = self.y_range
        for y in np.arange(y0 + ys, y1 + ys / 2, ys):
            g.add(Line(self.c2p(x0, y), self.c2p(x1, y), color=Palette.RULE, stroke_width=1, stroke_opacity=opacity))
        for x in np.arange(x0 + xs, x1 + xs / 2, xs):
            g.add(Line(self.c2p(x, y0), self.c2p(x, y1), color=Palette.RULE, stroke_width=1, stroke_opacity=opacity))
        self.add_to_back(g)
        return g


# --------------------------------------------------------------- the hero --
def halo(point, colour: str = Palette.EMERALD, radius: float = 0.11, layers: int = 4, spread: float = 2.6, opacity: float = 0.24) -> VGroup:
    """A soft glow behind a hero dot: concentric discs fading outward.
    Put it behind the dot (add it first)."""
    g = VGroup()
    for i in range(layers, 0, -1):
        r = radius * (1 + spread * i / layers)
        g.add(Circle(radius=r, color=colour, fill_color=colour, fill_opacity=opacity * (1 - (i - 1) / layers) * 0.6, stroke_width=0).move_to(point))
    return g


def glow_line(points, colour: str = Palette.EMERALD, width: float = 14.0, opacity: float = 0.18):
    """The glow under a hero line: the same polyline, wide and faint.
    Draw it with the line (Create both) and keep it behind."""
    from manim import VMobject

    return VMobject(color=colour, stroke_width=width, stroke_opacity=opacity).set_points_as_corners(points)


def glow_bar(mobj, colour: str = Palette.EMERALD, pad: float = 0.18, opacity: float = 0.09) -> RoundedRectangle:
    """A soft panel behind a hero row of text."""
    return RoundedRectangle(
        width=mobj.width + 2 * pad,
        height=mobj.height + 2 * pad,
        corner_radius=0.12,
        color=colour,
        fill_color=colour,
        fill_opacity=opacity,
        stroke_width=0,
    ).move_to(mobj)


def box(label: str, *content, colour: str = Palette.RULE, size: float = SIZE_BODY, label_colour: str = Palette.TEXT, pad: float = 0.3, gap: float = 0.18, min_width: float = 0.0, fill: str = Palette.BG) -> VGroup:
    """A named thing (a contract, a caller): a rounded box with its label
    inside and any further mobjects stacked beneath the label. The fill is
    the background so the box occludes whatever it is drawn over. The
    group's .rect, .label and .content name the parts."""
    inner = VGroup(words(label, size, label_colour), *content).arrange(DOWN, buff=gap)
    rect = RoundedRectangle(
        width=max(inner.width, min_width) + 2 * pad,
        height=inner.height + 2 * pad,
        corner_radius=0.16,
        color=colour,
        stroke_width=2,
        fill_color=fill,
        fill_opacity=1.0,
    ).move_to(inner)
    g = VGroup(rect, inner)
    g.rect, g.label, g.content = rect, inner[0], VGroup(*content)
    return g


# ---------------------------------------------------------------- numbers --
def thousands(n: int | str) -> str:
    """An integer with thousands separators: 95000 → "95,000"."""
    return f"{int(n):,}"


def millions(usd: int | float) -> str:
    """A dollar amount in millions to one decimal: 9500000 → "$9.5M"."""
    return f"${usd / 1e6:,.1f}M"


def typographic(s: str) -> str:
    """The essay's plain-text operators set as glyphs: ' x ' → ' × ', '...' → '…'.
    The words stay verbatim."""
    return s.replace(" x ", " × ").replace("...", "…")


def _load(rel: str):
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def incidents() -> dict:
    """talk/scenes/data/incidents.json: the five incidents of essay-v6 §2,
    oldest first (.incidents[] with date, protocol, rounding, loss,
    lossUsd, source) and the slide's .total phrase."""
    return _load("talk/scenes/data/incidents.json")
NOT_IN_TALK = ("blockulator",)  # BlockulatorWad: in the registry, not in the talk
DUPLICATES = ("fp127lib",)  # the benchmarks' inline copy of fp127, not a registry entry


def libs() -> dict[str, dict]:
    """static/data/libraries.json → {id: record}, in file order."""
    return {lib["id"]: lib for lib in _load("static/data/libraries.json")["libraries"]}


def talk_libs() -> dict[str, dict]:
    """The libraries every comparison in the talk accounts for: the registry
    minus NOT_IN_TALK (17). A chart draws each one that has a value and
    lists the rest with the reason the data gives; none is dropped silently."""
    return {lid: lib for lid, lib in libs().items() if lid not in NOT_IN_TALK}


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
    "axisMax": the digits axis the site's charts use, "scenario": the
    scenario record (its .summary[lib][N].digits)}."""
    d = _load("docs/benchmarks/ladder.json")
    for s in d["scenarios"]:
        if s["id"] == scenario:
            return {"N": d["ladder"], "log10": d["ladderLog10"], "axisMax": d["axisMax"], "scenario": s}
    raise KeyError(scenario)


def ladder_median(cell: dict | None) -> float | None:
    """The median correct digits of one ladder summary cell, or None when
    no input completed. .digits is {min, median, max} in the current file
    and was a bare value in earlier ones; both are read."""
    if not cell or not cell.get("count"):
        return None
    dg = cell.get("digits")
    if isinstance(dg, dict):
        dg = dg.get("median")
    return None if dg is None else float(dg)


def ladder_reason(scenario: dict, lid: str) -> str:
    """Why a library has no line in a ladder scenario, from the scenario's
    own record: its .ops[lib] is ["unsupported"] when the library has no
    model for the scenario ("not offered"); otherwise some N had no
    completed input ("no result")."""
    if scenario["ops"].get(lid) == ["unsupported"]:
        return "not offered"
    return "no result"


def live() -> list[dict]:
    """docs/benchmarks/accrual-deployed.json → the cases with group "live"
    (one per deployed Aave reserve and Morpho market)."""
    return [c for c in _load("docs/benchmarks/accrual-deployed.json")["cases"] if c["group"] == "live"]


def resupply() -> dict:
    """scripts/replays/resupply.json, whole: .pins, .checks, .state, .sources…"""
    return _load("scripts/replays/resupply.json")


def sweep(lib: str, op: str, stage: str | None = None) -> dict:
    """docs/benchmarks/sweep.json → the one .rows[] record with .lib == lib,
    .op == op and .stage == stage (no .stage key is the plain pass; "second"
    and "middle" are the forced passes). Its fields: n, correctlyRounded,
    misrounded, maxUlp, hist, gasMedian, gasP99, gasMax, fallback…"""
    rows = [r for r in _load("docs/benchmarks/sweep.json")["rows"] if r["lib"] == lib and r["op"] == op and r.get("stage") == stage]
    if len(rows) != 1:
        raise KeyError((lib, op, stage, len(rows)))
    return rows[0]


def gas(op: str) -> dict:
    """docs/benchmarks/gas.json → .ops[op] (inputs, gas[form][], summary[form]
    {min, median, max} | null, reverts, typical {inputs, gas, …}) plus
    "inlineMedian": {form: median gas} over .ops[op].typical.gas[form] (the
    random inputs that take no shortcut; computed here with statistics.median,
    null cells skipped) falling back to .ops[op].summary[form].median where
    there is no typical block; forms without a measurement are absent.
    "formLabels" is the file's .formLabels."""
    d = _load("docs/benchmarks/gas.json")
    rec = dict(d["ops"][op])
    source = rec.get("typical", rec)
    medians = {}
    for form, cells in source["gas"].items():
        vals = [c for c in cells if c is not None]
        if vals:
            medians[form] = statistics.median(vals)
    rec["inlineMedian"] = medians
    rec["formLabels"] = d["formLabels"]
    return rec


def proofs() -> dict:
    """docs/benchmarks/proofs.json → {"summary": .summary (ops, proven,
    proven_except, fuzzed, counterexamples, in_progress, solver_seconds),
    "ops": .ops[] (lib, op, status, spec, checks, seconds, tool, reproduce…)}."""
    d = _load("docs/benchmarks/proofs.json")
    return {"summary": d["summary"], "ops": d["ops"]}


def release() -> dict:
    """contracts/deployments/RELEASE.json, whole: .release, .date, .chainId,
    .network, .components{name: {version, address, block, runtimeBytes,
    record}}, .live, .superseded."""
    return _load("contracts/deployments/RELEASE.json")


def chains() -> dict:
    """talk/scenes/data/chains.json: a dated hand copy of the chain table in
    contracts/deployments/README.md ("Chains: CLZ (Osaka) required"):
    .chains[] with chain, clz_since (null where the README says "(probe)"),
    upgrade, status "supported" | "unsupported", probed (the date of the
    last probe), deployed (true for Sepolia only, RELEASE.json) and proxy
    (true where the deterministic-deployment proxy has code; null until
    probed); .source and .note say so. Re-probed 2026-10-29 (claims V3, V5)."""
    return _load("talk/scenes/data/chains.json")


def thetanuts() -> dict:
    """scripts/replays/thetanuts.json, whole (tx, block, components, slots…)."""
    return _load("scripts/replays/thetanuts.json")


def balancer() -> dict:
    """scripts/replays/balancer.json, whole (about, provenance, pools, test, score)."""
    return _load("scripts/replays/balancer.json")


def balancer_v1() -> dict:
    """scripts/replays/balancer_v1.json, whole (generated, rpc, report, source, pools)."""
    return _load("scripts/replays/balancer_v1.json")


def _import_script(rel: str):
    """Import a script by path (scripts/replays is not a package)."""
    path = ROOT / rel
    name = "talk_" + path.stem
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def bunni_replay() -> dict:
    """scripts/replays/bunni.py:replay(scripts/replays/bunni.json): the 44
    withdrawals replayed from the pinned start state, every on-chain
    observation asserted on the way. Returns its dict: .seq[form][] the
    active balance (balance − idle) after each step for the forms
    "deployed", "mulDivUp", "fp127" (Fractions) and "exact" (Fractions),
    .bal0[] / .bal1[] the balances, .idle{form}, .exactIdle, .T, .final."""
    mod = _import_script("scripts/replays/bunni.py")
    return mod.replay(_load("scripts/replays/bunni.json"))


TRUTH_DECIMALS = 80


def truth80() -> str:
    """exp(40) to 80 decimals: mpmath at 120 digits, rounded half-up at the
    80th decimal. Asserted against docs/benchmarks/edges.json's exp(40)
    .truth (42 digits, 24 decimals): the two agree on every one of those
    24 decimals under the same half-up rounding (the file's last decimal
    is a 2 where the longer expansion reads 1617…: the file rounds, it
    does not truncate), and the first 23 are a plain string prefix."""
    import mpmath

    mpmath.mp.dps = 120
    s = mpmath.nstr(mpmath.exp(40), 120, strip_zeros=False)
    with localcontext() as ctx:
        ctx.prec = 200
        x = Decimal(s)
        t80 = str(x.quantize(Decimal(1).scaleb(-TRUTH_DECIMALS), rounding=ROUND_HALF_UP))
        truth = probe("exp", "40")["truth"]
        t24 = str(x.quantize(Decimal(1).scaleb(-len(truth.partition(".")[2])), rounding=ROUND_HALF_UP))
    assert t24 == truth and t80.startswith(truth[:-1]), (t24, truth)
    assert len(t80.partition(".")[2]) == TRUTH_DECIMALS, t80
    return t80


# ----------------------------------------------------------- the words --
# FP127: a signed 256-bit word, 128 fraction bits (contracts/src/fp127/README.md; claims K1, K2)
FP127_FRACTION_BITS = 128
# FP19: IEEE 754 binary256's layout: sign, 19-bit exponent (bias 262143), 236-bit fraction
# (contracts/src/fp19/README.md; claims K3, E9); subnormals are not produced (K4)
FP19_EXPONENT_BITS, FP19_FRACTION_BITS = 19, 236
FP19_BIAS = (1 << (FP19_EXPONENT_BITS - 1)) - 1
WAD_DECIMALS = 18  # the 18-decimal libraries' unit, 10^-18 (claims R6, K7)


def fp127_value(raw: int | str) -> Fraction:
    """The value of an FP127 word from its raw uint256 (edges.json .cells[lib].raw)."""
    w = int(raw)
    return Fraction(w - (1 << 256) if w >> 255 else w, 1 << FP127_FRACTION_BITS)


def fp19_value(raw: int | str) -> Fraction:
    """The value of an FP19 word from its raw uint256."""
    w = int(raw)
    if w == 0:
        return Fraction(0)
    sign = w >> 255
    e = (w >> FP19_FRACTION_BITS) & ((1 << FP19_EXPONENT_BITS) - 1)
    f = w & ((1 << FP19_FRACTION_BITS) - 1)
    v = Fraction((1 << FP19_FRACTION_BITS) + f) * Fraction(2) ** (e - FP19_BIAS - FP19_FRACTION_BITS)
    return -v if sign else v


def word_value(lid: str, raw: int | str) -> Fraction:
    return {"fp19": fp19_value, "fp127": fp127_value}[lid](raw)


def to_decimals(q: Fraction, places: int) -> str:
    """A Fraction as a decimal string with exactly `places` decimals, nearest,
    half-up on the magnitude (integer arithmetic)."""
    neg = q < 0
    scaled = (2 * abs(q).numerator * 10**places + abs(q).denominator) // (2 * abs(q).denominator)
    whole, frac = divmod(scaled, 10**places)
    return ("-" if neg else "") + (f"{whole}.{frac:0{places}d}" if places else str(whole))


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


def matching_digits(value: str, truth: str) -> int:
    """How many leading digits of value equal truth's, the decimal point
    ignored (both strings aligned on the point; if the integer parts differ
    in length no leading digit lines up and the count is 0). This is the
    count a reader makes by eye; correct_digits is the measure."""
    vi, _, vf = value.partition(".")
    ti, _, tf = truth.partition(".")
    if len(vi) != len(ti):
        return 0
    n = 0
    for a, b in zip(vi + vf, ti + tf):
        if a != b:
            break
        n += 1
    return n


def matching_decimals(value: str, truth: str) -> int:
    """How many digits after the point value shares with truth, counted
    from the point: the count that matters for a fixed-point word, which
    promises decimals, not significant digits. 0 if the integer parts
    differ (then no decimal is right)."""
    vi, _, vf = value.partition(".")
    ti, _, tf = truth.partition(".")
    if vi != ti:
        return 0
    n = 0
    for a, b in zip(vf, tf):
        if a != b:
            break
        n += 1
    return n


def correct_decimals(digits: int, truth: str) -> int:
    """Correct decimals from a cell's correct significant digits: the
    integer part's digits are the first ones, so the rest lie after the
    point. A floor (digits is floored, log10 of the integer part is below
    its length), so the count is never overstated."""
    return int(digits) - len(truth.partition(".")[0].lstrip("-"))


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

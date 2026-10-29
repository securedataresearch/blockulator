"""Slide 11, "Precision is a budget": four places precision pays, one
decision at a unit.

The title is chrome. The lead line types in, then four bullets, one per
section, each a line at the left in its own hue (GOLD, SAPPHIRE, VIOLET,
SLATE: ROW_COLOUR["s11"]) and a schematic glyph to its right, drawn from
the vocabulary and carrying no number: long horizons, a GridLine that
stretches far to the right; cancellation, two tall bars that subtract to
a sliver under a bare measure() bracket; extreme ranges and tails, a dot
that slides left along a grid and drops off its last tick, RED with a
cross_mark(); iteration, a dot cycled through three snap()s under a loop
arrow while a measure() bracket grows from its start. Last, the fifth
line at HERO on two lines beside an EMERALD direction() arrow over a
short grid, on a glow_bar(): the hero.

Six sections: title, horizons, cancellation, tails, iteration,
direction. No JSON: numbers() is empty; every string is a LITERAL
(essay-v7 §5, script §11). "every" appears in the fifth line only.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    PI,
    RIGHT,
    UP,
    Arc,
    Create,
    FadeIn,
    Line,
    Rectangle,
    Succession,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_in_out_cubic, ease_out_cubic

from vocab import (
    ROW_COLOUR,
    SIZE_BODY,
    SIZE_HERO,
    GridLine,
    Palette,
    TextScene,
    cross_mark,
    direction,
    glow_bar,
    measure,
    snap,
    words,
)

HUES = ROW_COLOUR["s11"]

TITLE = "Precision is a budget"
LEAD = "spend precision where it pays:"
BULLETS = ("long horizons", "cancellation", "extreme ranges and tails", "iteration")
DIRECTION = "and decide the direction\nof every rounding at a unit"  # one line in the script, two on the slide (15.4 units at HERO on one)

LITERALS = {
    TITLE: "essay-v7 §5",
    LEAD: "essay-v7 §5",
    **{b: "essay-v7 §5" for b in BULLETS},
    DIRECTION: "script §11",
}

X_LEFT = -6.2
Y_LEAD = 2.45
Y_ROWS = (1.55, 0.55, -0.45, -1.45)
X_GLYPH = -0.9  # the glyphs start here
X_GLYPH_END = 6.2
Y_DIRECTION = -2.95
X_DIRECTION_TEXT = -4.25


def numbers() -> dict:
    return {}


class Budget(TextScene):
    SECTIONS = ("title", "horizons", "cancellation", "tails", "iteration", "direction")

    def line(self, i: int):
        return self.typed(BULLETS[i], SIZE_BODY, HUES[BULLETS[i]], place=lambda t: t.move_to([X_LEFT + t.width / 2, Y_ROWS[i], 0]))

    def construct(self):
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.wait(0.3)
        self.typed(LEAD, SIZE_BODY, Palette.TEXT, place=lambda t: t.move_to([X_LEFT + t.width / 2, Y_LEAD, 0]))
        assert words(DIRECTION, SIZE_HERO).width + (X_DIRECTION_TEXT - X_LEFT) <= 12.8

        # 1 · long horizons: a short grid stretches far to the right
        self.section(1, hold=1.0)
        hue = HUES[BULLETS[0]]
        self.line(0)
        y = Y_ROWS[0]
        short = GridLine((0, 3, 1), length=1.8, colour=hue).move_to([X_GLYPH + 0.9, y, 0])
        long = GridLine((0, 24, 1), length=X_GLYPH_END - X_GLYPH, colour=hue).move_to([(X_GLYPH + X_GLYPH_END) / 2, y, 0])
        self.play(Create(short, run_time=0.5))
        self.play(Transform(short, long, run_time=2.4, rate_func=ease_in_out_cubic))

        # 2 · cancellation: two tall bars subtract to a sliver; a bare bracket names the gap
        self.section(2, hold=1.0)
        hue = HUES[BULLETS[1]]
        self.line(1)
        y = Y_ROWS[1]
        h, w = 0.84, 0.55
        base = y - h / 2  # the bars stand on one baseline
        a = Rectangle(width=w, height=h, color=hue, fill_color=hue, fill_opacity=0.85, stroke_width=0).move_to([X_GLYPH + 0.4 + w / 2, base + h / 2, 0])
        b = Rectangle(width=w, height=h * 0.86, color=hue, fill_color=hue, fill_opacity=0.35, stroke_width=0).move_to([X_GLYPH + 0.4 + 1.5 * w + 0.3, base + h * 0.43, 0])
        floor = Line([X_GLYPH, base, 0], [X_GLYPH + 2.6, base, 0], color=hue, stroke_width=1.5)
        self.play(Create(floor, run_time=0.3), FadeIn(a, shift=UP * 0.1, run_time=0.4), FadeIn(b, shift=UP * 0.1, run_time=0.4))
        self.wait(0.3)
        # the second bar slides onto the first and takes its height away; what is left is a sliver on the baseline
        self.play(b.animate.move_to([a.get_x(), b.get_y(), 0]), run_time=0.9, rate_func=ease_in_out_cubic)
        sliver_h = h * 0.14
        sliver = Rectangle(width=w, height=sliver_h, color=hue, fill_color=hue, fill_opacity=1.0, stroke_width=0).move_to([a.get_x(), base + sliver_h / 2, 0])
        self.play(Transform(VGroup(a, b), sliver, run_time=0.7, rate_func=ease_out_cubic))
        # the bare bracket, stood on end beside the sliver: the gap, with no number
        bracket = measure(GridLine((0, 1, 1), length=sliver_h, colour=hue), 0, 1, None, colour=hue, drop=0)
        bracket.rotate(PI / 2).move_to([sliver.get_right()[0] + 0.3, sliver.get_y(), 0])
        self.play(Create(bracket, run_time=0.5))

        # 3 · extreme ranges and tails: a dot slides left along a grid and drops off its last tick
        self.section(3, hold=1.0)
        hue = HUES[BULLETS[2]]
        self.line(2)
        y = Y_ROWS[2]
        grid = GridLine((0, 8, 1), length=5.6, colour=hue).move_to([X_GLYPH + 1.0 + 2.8, y, 0])  # the fall lands right of the text
        dot = grid.dot_at(7.5, hue)
        self.play(Create(grid, run_time=0.5), FadeIn(dot, run_time=0.3))
        self.play(dot.animate.move_to(grid.n2p(0.5)), run_time=1.6, rate_func=ease_in_out_cubic)
        # past the last tick there is nothing to hold it: it falls, red, and a cross marks the loss
        fall = dot.copy().move_to(grid.n2p(-0.7) + DOWN * 0.3).set_color(Palette.WRONG)
        self.play(Transform(dot, fall, run_time=0.7, rate_func=ease_in_out_cubic))
        cross = cross_mark(size=0.26).next_to(dot, LEFT, buff=0.15)
        self.play(Create(cross, run_time=0.3))

        # 4 · iteration: a dot snaps tick to tick under a loop arrow; the bracket from its start grows
        self.section(4, hold=1.0)
        hue = HUES[BULLETS[3]]
        self.line(3)
        y = Y_ROWS[3]
        grid4 = GridLine((0, 6, 1), length=4.2, colour=hue).move_to([X_GLYPH + 2.1, y, 0])
        d4 = grid4.dot_at(0, hue)
        loop = Arc(radius=0.3, start_angle=-PI * 0.15, angle=PI * 1.6, color=hue, stroke_width=2.5).add_tip(tip_length=0.12)
        loop.move_to([X_GLYPH + 4.95, y + 0.05, 0])
        self.play(Create(grid4, run_time=0.5), FadeIn(d4, run_time=0.3), Create(loop, run_time=0.6))
        bracket4 = None
        for k in (1, 2, 3):
            # each pass lands a little further off: the drift, then the snap, and the gap from the start grows
            self.play(d4.animate.move_to(grid4.n2p(k + 0.42)), run_time=0.45, rate_func=ease_in_out_cubic)
            self.play(snap(d4, grid4, k + 1, hue, run_time=0.55))
            new = measure(grid4, 0, k + 1, None, drop=0.32, colour=hue)
            if bracket4 is None:
                bracket4 = new
                self.play(Create(bracket4, run_time=0.3))
            else:
                self.play(Transform(bracket4, new, run_time=0.3))

        # 5 · the decision: the fifth line at HERO, an EMERALD direction arrow over a short grid, on a panel
        self.section(5, hold=1.0)
        text = words(DIRECTION, SIZE_HERO, Palette.TEXT, line_spacing=0.85)
        text.move_to([X_DIRECTION_TEXT + text.width / 2, Y_DIRECTION, 0])
        small = GridLine((0, 2, 1), length=1.6, colour=Palette.RULE).move_to([X_LEFT + 0.95, Y_DIRECTION - 0.2, 0])
        arrow = direction(small, 0.9, 1.95, Palette.CORRECT, lift=0.35)
        glyph = VGroup(small, arrow)
        panel = glow_bar(VGroup(text, glyph), Palette.EMERALD, pad=0.16, opacity=0.1)
        panel.set_fill(opacity=0)
        self.add(panel)
        self.play(panel.animate.set_fill(opacity=0.1), Create(small, run_time=0.4))
        self.play(Create(arrow, run_time=0.5))
        self.typed(DIRECTION, SIZE_HERO, Palette.TEXT, place=lambda t: t.move_to(text), line_spacing=0.85)
        self.close(hold=3.0)

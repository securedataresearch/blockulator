"""Slide 4, "Computers round": the grid, and the three ways a value meets it.

A number line; ticks appear (the finitely many values a word can hold); an
exact value lands between two ticks and snaps to the nearer one; the camera
closes in to show that the gap is half a unit; a second value snaps the far
way (WRONG, red, its direction drawn); a third snaps the right way (CORRECT,
emerald). Silent, about 45 s, and it ends on the bare background so the
deck can loop it.

Numbers: none from JSON; this is the vocabulary itself. numbers() returns
the tick positions and where each value lands, for check.py.
"""

from __future__ import annotations

from manim import (
    DOWN,
    ORIGIN,
    UP,
    Arrow,
    Circle,
    Create,
    DashedLine,
    FadeIn,
    FadeOut,
    GrowFromCenter,
    Indicate,
    LaggedStart,
    Line,
    MovingCameraScene,
    VGroup,
    config,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import DeckScene, GridLine, Palette, measure, snap, words

TICKS = (0, 10, 1)  # x_range: eleven ticks, unit 1
EXACT_1 = 6.4  # snaps to 6, the nearer tick (white: rounding itself)
EXACT_2 = 7.3  # snaps the far way to 8 (WRONG)
EXACT_3 = 7.3  # the same value, snapped the right way to 7 (CORRECT)
ZOOM_CENTRE = 7.0
ZOOM_WIDTH = 4.6  # frame width in scene units after the zoom


def numbers() -> dict:
    line = GridLine(TICKS, length=11.5)
    return {
        "ticks": list(range(TICKS[0], TICKS[1] + 1)),
        "lands": {
            "first": (EXACT_1, line.nearest_tick(EXACT_1)),
            "wrong": (EXACT_2, 8.0),
            "right": (EXACT_3, line.nearest_tick(EXACT_3)),
        },
    }


def direction(line, x_from, x_to, colour, lift=0.3):
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


def drop(scene, dot, target, height=2.2):
    """A value arrives from above and lands on the line."""
    dot.move_to(target + UP * height)
    scene.play(FadeIn(dot, run_time=0.3))
    scene.play(dot.animate(rate_func=ease_out_cubic).move_to(target), run_time=0.8)


class Grid(DeckScene, MovingCameraScene):
    def construct(self):
        frame = self.camera.frame
        line = GridLine(TICKS, length=11.5, tick_size=0.14)
        line.move_to(ORIGIN)
        ticks = line.get_tick_marks()

        # the continuum, then the grid
        base = Line(line.get_start(), line.get_end(), color=Palette.FAINT, stroke_width=2)
        self.wait(0.4)
        self.play(Create(base, run_time=1.2))
        self.wait(0.6)
        for t in ticks:
            t.set_opacity(0)
        self.add(line)
        self.remove(base)
        self.play(LaggedStart(*[GrowFromCenter(t.set_opacity(1)) for t in ticks], lag_ratio=0.12, run_time=2.4))
        self.wait(2.0)

        # 1. an exact value lands between two ticks and takes the nearer one
        d1 = line.dot_at(EXACT_1, Palette.EXACT)
        drop(self, d1, line.n2p(EXACT_1))
        self.wait(0.8)
        lo, hi = ticks[6], ticks[7]
        self.play(Indicate(lo, color=Palette.TEXT, scale_factor=1.6), Indicate(hi, color=Palette.TEXT, scale_factor=1.6), run_time=0.7)
        self.wait(0.3)
        self.play(snap(d1, line, line.nearest_tick(EXACT_1), Palette.EXACT))
        self.wait(3.0)

        # 2. close in: the gap between two ticks is a unit; the farthest a value
        #    can be from a tick is half of it
        z = ZOOM_WIDTH / config.frame_width
        self.play(
            frame.animate.set(width=ZOOM_WIDTH).move_to(line.n2p(ZOOM_CENTRE)),
            d1.animate.scale(z),
            run_time=2.4,
        )
        self.wait(0.8)
        mid = line.n2p(6.5)
        mid_mark = DashedLine(mid + DOWN * 0.3, mid + UP * 0.3, color=Palette.FAINT, stroke_width=1.5, dash_length=0.035)
        self.play(Create(mid_mark, run_time=0.6))
        half = measure(line, 6, 6.5, "½ unit", scale=z, drop=0.5)
        self.play(FadeIn(half, shift=UP * 0.04, run_time=0.6))
        self.wait(3.6)

        # 3. a second value, snapped the far way
        d2 = line.dot_at(EXACT_2, Palette.EXACT, radius=0.11 * z)
        ghost = Circle(radius=0.11 * z, color=Palette.FAINT, stroke_width=1.5).move_to(line.n2p(EXACT_2))
        exact_lbl = words("exact", 32, Palette.FAINT).scale(z).next_to(ghost, DOWN, buff=0.16)
        drop(self, d2, line.n2p(EXACT_2), height=1.1)
        self.add(ghost)
        self.play(FadeIn(exact_lbl, run_time=0.4))
        self.wait(1.2)
        a_wrong = direction(line, EXACT_2, 8, Palette.WRONG)
        self.play(Create(a_wrong, run_time=0.6))
        self.play(snap(d2, line, 8, Palette.WRONG, run_time=1.0))
        self.wait(3.4)

        # 4. the same value, snapped the right way
        d3 = line.dot_at(EXACT_3, Palette.EXACT, radius=0.11 * z)
        drop(self, d3, line.n2p(EXACT_3), height=1.1)
        self.wait(1.0)
        a_right = direction(line, EXACT_3, 7, Palette.CORRECT)
        self.play(Create(a_right, run_time=0.6))
        self.play(snap(d3, line, 7, Palette.CORRECT, run_time=1.0))
        self.wait(5.0)

        # out, so the loop can restart on the bare background
        self.play(FadeOut(VGroup(line, d1, d2, d3, ghost, exact_lbl, mid_mark, half, a_wrong, a_right), run_time=0.9))
        self.wait(0.4)

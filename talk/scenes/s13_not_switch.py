"""Slide 13, "Not switch. Measure.": two lines, the first struck through,
the second the hero.

"Not "switch libraries"." types in at HERO in TEXT and a RED strike
draws through the two words "switch libraries" (wrong = red and a
stroke). Then "Measure yourself against the reference." types in at HERO
inside an EMERALD glow_bar() while the first line and its strike dim to
FAINT. Straight quotes, as the script writes them. Nothing else is on
the slide: no title (slides.yaml names it), no numbers.

Two sections: not, measure.
"""

from __future__ import annotations

from manim import Create, VGroup

from vocab import (
    SIZE_HERO,
    Palette,
    TextScene,
    glow_bar,
    glyphs,
    words,
)

NOT = 'Not "switch libraries".'
STRUCK = "switch libraries"
MEASURE = "Measure yourself against the reference."

LITERALS = {NOT: "script §13", MEASURE: "script §13"}

Y_NOT = 1.0
Y_MEASURE = -0.7
DIM = 0.45  # the first line's opacity once the second is the hero


def numbers() -> dict:
    return {}


class NotSwitch(TextScene):
    SECTIONS = ("not", "measure")

    def construct(self):
        # 0 · the first line types; the strike draws through the two words
        self.section(0)
        self.wait(0.3)
        line1 = self.typed(NOT, SIZE_HERO, Palette.TEXT, place=lambda t: t.move_to([0, Y_NOT, 0]))
        self.wait(0.4)
        struck = glyphs(line1, STRUCK)
        strike = self.strike(struck, Palette.WRONG, stroke_width=5.0)
        self.play(Create(strike, run_time=0.6))

        # 1 · the second line, the hero, on its panel; the first recedes
        self.section(1, hold=1.2)
        self.play(VGroup(line1, strike).animate.set_opacity(DIM), run_time=0.6)
        # the panel is sized on the line before it is typed (the same string, measured)
        panel = glow_bar(words(MEASURE, SIZE_HERO, Palette.TEXT).move_to([0, Y_MEASURE, 0]), Palette.EMERALD, pad=0.3, opacity=0.1)
        panel.set_fill(opacity=0)
        self.add(panel)
        self.play(panel.animate.set_fill(opacity=0.1), run_time=0.5)
        self.typed(MEASURE, SIZE_HERO, Palette.TEXT, place=lambda t: t.move_to([0, Y_MEASURE, 0]))
        self.close(hold=3.0)

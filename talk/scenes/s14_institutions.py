"""Slide 14, "What institutions buy": fees scale with the computation,
errors with the amount; what is bought is a result that can be
reproduced, declared and checked.

The title and the two series labels (the keys, at the lines' ends) are on
the first frame; the two lines draw in on their own, no axes: fees flat
in MUTED, errors rising in RED with an arrow at its end (the direction it
goes). The labels say what the axes did. Then three words at HERO, one
per section, land in a row under the lines, each on an EMERALD
glow_bar() (the hero), the panel 0.3 s before the word.

Four sections: scales, reproducible, declared, checked. No JSON:
numbers() is empty and the slide carries no digit. "errors scale with
the amount" is a proportionality, not a claim about any protocol.
"""

from __future__ import annotations

from manim import RIGHT, UP, Arrow, Create, FadeIn, Line, VGroup

from vocab import (
    ROW_COLOUR,
    SIZE_BODY,
    SIZE_HERO,
    Palette,
    TextScene,
    glow_bar,
    words,
)

HUES = ROW_COLOUR["s14"]

TITLE = "What institutions buy"
FEES = "fees · scale with the computation"
ERRORS = "errors · scale with the amount"
WORDS = ("reproducible", "declared", "checked")

LITERALS = {
    TITLE: "essay §7",
    FEES: "essay §7",
    ERRORS: "essay §7",
    **{w: "essay §7" for w in WORDS},
}

# the two lines, in scene units: no axes, the labels at their right ends
X_FROM, X_TO = -6.1, -0.6
Y_FEES = 0.75
Y_ERRORS_FROM, Y_ERRORS_TO = -0.35, 2.3
LABEL_GAP = 0.3
Y_WORDS = -2.0
WORD_GAP = 0.9
STAGGER = 0.3


def numbers() -> dict:
    return {}


class Institutions(TextScene):
    SECTIONS = ("scales", "reproducible", "declared", "checked")

    def construct(self):
        self.section(0)
        # the chrome: the title and the two series labels at the lines' ends
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        fees_label = words(FEES, SIZE_BODY, HUES["fees"])
        fees_label.move_to([X_TO + LABEL_GAP + fees_label.width / 2, Y_FEES, 0])
        errors_label = words(ERRORS, SIZE_BODY, HUES["errors"])
        errors_label.move_to([X_TO + LABEL_GAP + errors_label.width / 2, Y_ERRORS_TO, 0])
        assert fees_label.get_right()[0] <= 6.45 and errors_label.get_right()[0] <= 6.45, (fees_label.get_right()[0], errors_label.get_right()[0])
        self.fix(fees_label, errors_label)
        self.wait(0.3)
        fees = Line([X_FROM, Y_FEES, 0], [X_TO, Y_FEES, 0], color=HUES["fees"], stroke_width=3.5)
        errors = Arrow(
            [X_FROM, Y_ERRORS_FROM, 0],
            [X_TO, Y_ERRORS_TO, 0],
            buff=0,
            color=HUES["errors"],
            stroke_width=3.5,
            tip_length=0.22,
            max_tip_length_to_length_ratio=1.0,
            max_stroke_width_to_length_ratio=100.0,
        )
        self.play(Create(fees, run_time=1.4))
        self.play(Create(errors, run_time=1.8))

        # 1–3 · the three words, one per click, landing in a row on their panels
        slots = VGroup(*[words(w, SIZE_HERO, Palette.TEXT) for w in WORDS]).arrange(RIGHT, buff=WORD_GAP).move_to([0, Y_WORDS, 0])
        for i, w in enumerate(WORDS):
            self.section(1 + i, hold=1.0)
            panel = glow_bar(slots[i], HUES["words"], pad=0.22, opacity=0.1)
            panel.stretch_to_fit_height(slots.height + 0.44).set_y(slots.get_y())  # one height for the three panels
            panel.set_fill(opacity=0)
            self.add(panel)
            self.play(panel.animate.set_fill(opacity=0.1), run_time=STAGGER)
            self.play(FadeIn(words(w, SIZE_HERO, Palette.TEXT).move_to(slots[i]), shift=UP * 0.12, run_time=0.5))
        self.close(hold=3.0)

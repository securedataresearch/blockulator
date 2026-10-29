"""Slide 14, "What institutions buy": fees scale with the computation,
errors with the amount; what is bought is a result that can be
reproduced, declared and checked.

The title, the Chart (no tick numbers: x "amount") and its two series
labels, the key, are on the first frame; the two curves draw in: fees
flat in MUTED, errors rising in RED, an arrow at its end (the direction
it goes). The chart keeps its place (a chart's axes never move); "not
fewer cents" lands to its right. Then three words at HERO, one per
section, land in a row under the chart, each on an EMERALD glow_bar()
(the hero), the panel 0.3 s before the word. Last the ERC-4626 line at
BODY, MUTED: the precedent.

Six sections: scales, not-cents, reproducible, declared, checked,
precedent. No JSON: numbers() is empty; the chart carries no number, and
the one digit-bearing string, the ERC-4626 line, is a LITERAL (essay §7,
V1). "errors scale with the amount" is a proportionality, not a claim
about any protocol.
"""

from __future__ import annotations

from manim import Arrow, Create, FadeIn, Line, UP, VGroup

from vocab import (
    ROW_COLOUR,
    SIZE_BODY,
    SIZE_HERO,
    Chart,
    Palette,
    TextScene,
    glow_bar,
    words,
)

HUES = ROW_COLOUR["s14"]

TITLE = "What institutions buy"
X_TITLE = "amount"
FEES = "fees · scale with the computation"
ERRORS = "errors · scale with the amount"
NOT_CENTS = "not fewer cents"
WORDS = ("reproducible", "declared", "checked")
PRECEDENT = "ERC-4626 fixes the rounding direction of each vault conversion"

LITERALS = {
    TITLE: "essay §7",
    X_TITLE: "essay §7",
    FEES: "essay §7",
    ERRORS: "essay §7",
    NOT_CENTS: "essay §7",
    **{w: "essay §7" for w in WORDS},
    PRECEDENT: "V1",
}

CHART_ORIGIN = (-6.0, -0.1, 0.0)
CHART_W, CHART_H = 5.4, 2.9
X_RANGE, Y_RANGE = (0, 10, 2), (0, 10, 2)
FEES_LEVEL = 4.2
ERRORS_FROM, ERRORS_TO = (0, 0.4), (10, 9.2)
Y_NOT_CENTS = 0.3
X_NOT_CENTS = 2.6
Y_WORDS = -1.75
WORD_GAP = 0.9
Y_PRECEDENT = -3.0
STAGGER = 0.3


def numbers() -> dict:
    return {}


class Institutions(TextScene):
    SECTIONS = ("scales", "not-cents", "reproducible", "declared", "checked", "precedent")

    def construct(self):
        self.section(0)
        # the chrome: the title, the chart's axes and x title, the two series labels at the curve ends
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        chart = Chart(X_RANGE, Y_RANGE, CHART_W, CHART_H, origin=CHART_ORIGIN)
        chart.x_title(X_TITLE, size=SIZE_BODY * 0.7, colour=Palette.MUTED, drop=0.55)
        fees_label = words(FEES, SIZE_BODY, HUES["fees"])
        fees_label.next_to(chart.c2p(X_RANGE[1], FEES_LEVEL), direction=[1, 0, 0], buff=0.3)
        errors_label = words(ERRORS, SIZE_BODY, HUES["errors"])
        errors_label.next_to(chart.c2p(*ERRORS_TO), direction=[1, 0, 0], buff=0.3)
        assert fees_label.get_right()[0] <= 6.45 and errors_label.get_right()[0] <= 6.45, (fees_label.get_right()[0], errors_label.get_right()[0])
        self.fix(chart, fees_label, errors_label)
        self.wait(0.3)
        fees = Line(chart.c2p(X_RANGE[0], FEES_LEVEL), chart.c2p(X_RANGE[1], FEES_LEVEL), color=HUES["fees"], stroke_width=3.5)
        errors = Arrow(
            chart.c2p(*ERRORS_FROM),
            chart.c2p(*ERRORS_TO),
            buff=0,
            color=HUES["errors"],
            stroke_width=3.5,
            tip_length=0.22,
            max_tip_length_to_length_ratio=1.0,
            max_stroke_width_to_length_ratio=100.0,
        )
        self.play(Create(fees, run_time=1.4))
        self.play(Create(errors, run_time=1.8))

        # 1 · not fewer cents
        self.section(1, hold=1.0)
        self.typed(NOT_CENTS, SIZE_BODY, Palette.TEXT, place=lambda t: t.move_to([X_NOT_CENTS, Y_NOT_CENTS, 0]))

        # 2–4 · the three words, one per click, landing in a row on their panels
        probes = VGroup(*[words(w, SIZE_HERO, Palette.TEXT) for w in WORDS]).arrange(direction=[1, 0, 0], buff=WORD_GAP).move_to([0, Y_WORDS, 0])
        for i, w in enumerate(WORDS):
            self.section(2 + i, hold=1.0)
            slot = probes[i]
            panel = glow_bar(slot, HUES["words"], pad=0.22, opacity=0.1)
            panel.set_fill(opacity=0)
            self.add(panel)
            self.play(panel.animate.set_fill(opacity=0.1), run_time=STAGGER)
            self.play(FadeIn(words(w, SIZE_HERO, Palette.TEXT).move_to(slot), shift=UP * 0.12, run_time=0.5))

        # 5 · the precedent
        self.section(5, hold=1.0)
        precedent = words(PRECEDENT, SIZE_BODY, Palette.MUTED).move_to([0, Y_PRECEDENT, 0])
        assert precedent.width <= 12.8, precedent.width
        self.play(FadeIn(precedent, shift=UP * 0.08, run_time=0.8))
        self.close(hold=3.0)

"""Slide 5, "$130 million": five incidents, listed.

Five rows build, oldest at the top, one per click: the date, the
protocol, the one line that says what rounded (research_notes/talk/
essay-v6.txt §2, verbatim: one rounding step, taken once or repeated;
claim V27) and the loss. The figures are listed, not summed (V49: the
five sum to about $141M; the slide's phrase is "more than $130 million,
before recoveries"). After the last row the phrase appears, bottom
right, and holds as the slide.

Numbers from talk/scenes/data/incidents.json: .incidents[] (date,
protocol, rounding, loss), .total, .since. Six sections: one per
incident, then the closing phrase.
"""

from __future__ import annotations

import textwrap

from manim import (
    LEFT,
    RIGHT,
    UP,
    FadeIn,
)

from vocab import SIZE_CAPTION, DeckScene, Palette, digits, incidents, typographic, words

X_LEFT = -6.5
X_RIGHT = 6.5
Y_TOP = 2.8  # the first row, under the marks (was 3.4)
PITCH = 1.18  # row to row
WRAP = 92  # characters per line of the rounding text
HEAD = 22
BODY = SIZE_CAPTION
LOSS = 26
LINE_GAP = 0.32  # header line to the top of the text

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def numbers() -> dict:
    d = incidents()
    rows = [{"date": r["date"], "protocol": r["protocol"], "rounding": r["rounding"], "loss": r["loss"]} for r in d["incidents"]]
    return {"rows": rows, "total": d["total"], "since": d["since"], "caption": f"talk/scenes/data/incidents.json · since {d['since']}"}


class Cost(DeckScene):
    SECTIONS = ("resupply", "bunni", "balancer-v2", "thetanuts", "balancer-v1", "closing")

    def row(self, i: int, r: dict):
        y = Y_TOP - i * PITCH
        date = words(r["date"], BODY, Palette.FAINT)
        date.move_to([X_LEFT + date.width / 2, y, 0])
        proto = words(r["protocol"], HEAD, Palette.TEXT)
        proto.next_to(date, RIGHT, buff=0.35).set_y(y)
        text = words("\n".join(textwrap.wrap(typographic(r["rounding"]), WRAP)), BODY, Palette.BODY, line_spacing=0.6)
        text.move_to([X_LEFT + text.width / 2, y - LINE_GAP - text.height / 2, 0])
        loss = digits(r["loss"], LOSS, Palette.WRONG)
        loss.move_to([X_RIGHT - loss.width / 2, y, 0])
        return date, proto, text, loss

    def construct(self):
        n = numbers()
        assert len(n["rows"]) + 1 == len(self.SECTIONS), (len(n["rows"]), self.SECTIONS)
        for i, r in enumerate(n["rows"]):
            self.section(i, hold=1.5)
            if i == 0:
                self.wait(0.3)
                self.play(self.caption(n["caption"]))
            date, proto, text, loss = self.row(i, r)
            self.play(FadeIn(date, shift=RIGHT * 0.1, run_time=0.4), FadeIn(proto, shift=RIGHT * 0.1, run_time=0.4))
            self.play(FadeIn(text, run_time=0.6))
            self.wait(1.2)
            self.play(FadeIn(loss, shift=LEFT * 0.1, run_time=0.4))

        self.section(len(n["rows"]), hold=1.5)
        y_total = Y_TOP - len(n["rows"]) * PITCH + 0.05
        total = words(n["total"], 28, Palette.TEXT)
        total.move_to([X_RIGHT - total.width / 2, y_total, 0])
        self.play(FadeIn(total, shift=UP * 0.08, run_time=0.8))
        self.close()

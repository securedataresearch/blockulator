"""Slide 5, "$130 million": five incidents, and what they add up to.

Five rows build, oldest at the top: the date, the protocol, the one line
that says what rounded (research_notes/talk/essay-v6.txt §2, verbatim) and
the loss. The losses sum on the right as the rows arrive; after the last
row the slide's phrase for the total appears beside the sum.

Numbers from talk/scenes/data/incidents.json: .incidents[] (date, protocol,
rounding, loss, lossUsd, source), .total, .since. The running sum adds
.lossUsd (the lower Resupply bound, the realised Thetanuts figure) and is
printed in millions to one decimal. About 40 s.
"""

from __future__ import annotations

import textwrap

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    FadeIn,
    Line,
    Transform,
    VGroup,
)

from vocab import DeckScene, Palette, digits, incidents, millions, typographic, words

X_LEFT = -6.5
X_RIGHT = 6.5
Y_TOP = 3.4
PITCH = 1.3  # row to row
WRAP = 92  # characters per line of the rounding text
HEAD = 22
BODY = 20
LOSS = 26
LINE_GAP = 0.32  # header line to the top of the text


def numbers() -> dict:
    d = incidents()
    rows, total = [], 0
    for r in d["incidents"]:
        total += r["lossUsd"]
        rows.append({"date": r["date"], "protocol": r["protocol"], "rounding": r["rounding"], "loss": r["loss"], "sum": millions(total)})
    return {"rows": rows, "sum_usd": total, "sum": millions(total), "total": d["total"], "since": d["since"]}


class Cost(DeckScene):
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
        self.wait(0.6)
        self.play(self.caption("talk/scenes/data/incidents.json · since " + n["since"]))

        y_sum = Y_TOP - len(n["rows"]) * PITCH + 0.05
        rule = Line([X_RIGHT - 2.4, y_sum + 0.28, 0], [X_RIGHT, y_sum + 0.28, 0], color=Palette.RULE, stroke_width=1.5)
        running = None
        for i, r in enumerate(n["rows"]):
            date, proto, text, loss = self.row(i, r)
            self.play(FadeIn(date, shift=RIGHT * 0.1, run_time=0.4), FadeIn(proto, shift=RIGHT * 0.1, run_time=0.4))
            self.play(FadeIn(text, run_time=0.6))
            self.wait(2.2)
            self.play(FadeIn(loss, shift=LEFT * 0.1, run_time=0.4))
            new = digits(r["sum"], LOSS, Palette.TEXT)
            new.move_to([X_RIGHT - new.width / 2, y_sum, 0])
            if running is None:
                running = new
                self.play(FadeIn(rule, run_time=0.4), FadeIn(running, shift=UP * 0.1, run_time=0.5))
            else:
                self.play(Transform(running, new, run_time=0.5))
            self.wait(1.6)

        total = words(n["total"], 28, Palette.TEXT)
        total.next_to(running, LEFT, buff=0.5).set_y(y_sum)
        self.play(FadeIn(total, shift=UP * 0.08, run_time=0.8))
        self.wait(8.0)

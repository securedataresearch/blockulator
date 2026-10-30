"""Slide 5, "$130 million": five incidents, listed, and what they add to.

Five rows, oldest at the top, each one line: the date (FAINT) and the
protocol (in its deck hue, the hue its replay uses: vocab.protocol_colour)
as one string, the protocol starting on a shared column, and the loss in
red, right-aligned. The replays that follow carry the mechanism, so no row
explains itself (edit pass: the speaker says it). The figures are listed,
not summed (V49: the five sum to about $141M); on the second click copies
of the five losses fly into the slide's phrase, "more than $130 million"
at hero size with "before recoveries" under it, which holds as the poster.

Numbers from talk/scenes/data/incidents.json: .incidents[] (date,
protocol, loss) and .total (split at its comma into the hero and its tail).
Provenance (each loss's .source, "since June 2025") is in the slide's notes.
Two sections: the five rows, then the total.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    UP,
    FadeIn,
    LaggedStart,
    VGroup,
)
from manim.utils.rate_functions import ease_in_out_cubic

from vocab import SIZE_BODY, DeckScene, Palette, digits, incidents, protocol_colour, words

X_LEFT = -5.6  # the dates start here
X_PROTOCOL = -1.8  # every protocol starts on this column
X_RIGHT = 5.6  # the losses end here
Y_TOP = 2.3  # the first row's baseline
PITCH = 0.86  # row to row
ROW = 40  # a row's date, protocol and loss
HERO = 64  # "more than $130 million"
Y_HERO = -2.35
GAP = " " * 3  # date to protocol inside a row's one string (the protocol is then moved to its column)

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def numbers() -> dict:
    d = incidents()
    rows = [{"date": r["date"], "protocol": r["protocol"], "loss": r["loss"]} for r in d["incidents"]]
    hero, _, tail = d["total"].partition(", ")
    return {"rows": rows, "total": d["total"], "hero": hero, "tail": tail}


class Cost(DeckScene):
    SECTIONS = ("incidents", "closing")

    def row(self, i: int, r: dict):
        """One row: date and protocol as one string (the protocol in its hue,
        moved onto the shared column), and the loss."""
        y = Y_TOP - i * PITCH
        hue = protocol_colour(r["protocol"])
        name = words(r["date"] + GAP + r["protocol"], ROW, Palette.FAINT, t2c={r["protocol"]: hue})
        name.move_to([X_LEFT + name.width / 2, y, 0])
        name.shift(UP * (y - name[0].get_bottom()[1]))  # every row on its baseline: the date's first digit sits on y
        # the protocol's glyphs are the string's last ones (a sans Text drops its spaces' submobjects)
        k = len(name) - len(r["protocol"].replace(" ", ""))
        assert len(name) == len((r["date"] + r["protocol"]).replace(" ", "")), (len(name), r)
        proto = name[k:]
        proto.shift(LEFT * (proto.get_left()[0] - X_PROTOCOL))
        loss = digits(r["loss"], ROW, Palette.WRONG)
        # on the date's baseline: the loss's first digit sits where the date's first digit sits
        loss.move_to([X_RIGHT - loss.width / 2, y, 0])
        loss.shift(UP * (name[0].get_bottom()[1] - loss[1].get_bottom()[1]))
        return name, loss

    def construct(self):
        n = numbers()
        rows = [self.row(i, r) for i, r in enumerate(n["rows"])]

        # five incidents, oldest first: each row slides in, its loss lands after it
        self.section(0)
        self.wait(0.3)
        for name, loss in rows:
            self.play(FadeIn(name, shift=UP * 0.12, run_time=0.45))
            self.play(FadeIn(loss, shift=LEFT * 0.15, run_time=0.35))
            self.wait(0.35)

        # what they add to: copies of the five losses fly into the phrase
        self.section(1, hold=2.0)
        hero = words(n["hero"], HERO, Palette.TEXT).move_to([0, Y_HERO, 0])
        tail = words(n["tail"], SIZE_BODY, Palette.MUTED).next_to(hero, DOWN, buff=0.3)
        flying = VGroup(*[loss.copy() for _, loss in rows])
        self.add(flying)
        self.play(
            LaggedStart(*[f.animate(rate_func=ease_in_out_cubic).scale(0.4).move_to(hero).set_opacity(0) for f in flying], lag_ratio=0.12, run_time=1.2),
            FadeIn(hero, scale=0.9, run_time=1.0, rate_func=ease_in_out_cubic),
        )
        self.remove(flying)
        self.play(FadeIn(tail, shift=UP * 0.08, run_time=0.6))
        self.close()

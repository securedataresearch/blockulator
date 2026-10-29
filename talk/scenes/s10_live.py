"""Slide 10, "Real markets, today": every live Aave reserve and Morpho
market, its pending interest as deployed, then the same interest in
FP127, then in FP19.

One horizontal axis, correct digits of the pending interest (0–80), and
three rows stacked down it: "as deployed" (slate), "the same interest in
FP127" (emerald), "the same interest in FP19" (white). Each of the 326
markets is one marker, a circle for Aave, a diamond for Morpho, at the
same vertical jitter in every row so the eye can follow it. The markers
burst into the top row at their deployed digits (a cluster around 7, a
few near 0); then every marker lifts down to the FP127 row at its FP127
digits, leaving a faint trail, the cluster re-forming around 30; then
again to the FP19 row, around 67. Each row's median is ticked and
labelled as it settles, a bracket between the medians names the margin
in digits, and the two Blockulator rows settle under a soft band, drawn
last. The closing line names the win in the rounded medians. About 45 s.

Numbers from docs/benchmarks/accrual-deployed.json: .cases[] with .group
== "live" (.protocol, .primaryTruth, .truth[primaryTruth].deployed
.digitsInterest, .fp127.digitsInterest and .fp19.digitsInterest); the
medians and margins are computed here; .survey.block and .date for the
caption.
"""

from __future__ import annotations

import random
import statistics

from manim import (
    DOWN,
    LEFT,
    PI,
    RIGHT,
    UP,
    Create,
    Dot,
    FadeIn,
    LaggedStart,
    Line,
    RoundedRectangle,
    Square,
    VGroup,
)
from manim.utils.rate_functions import ease_in_out_cubic

from vocab import DeckScene, GridLine, Palette, _load, digits, live, measure, thousands, words

ROWS = (("deployed", "as deployed", Palette.SLATE), ("fp127", "the same interest in FP127", Palette.EMERALD), ("fp19", "the same interest in FP19", Palette.TEXT))
PROTOCOL_LABEL = {"aave": "Aave", "morpho": "Morpho"}
AXIS = (0, 80, 10)
AXIS_X0, AXIS_X1, AXIS_Y = -2.9, 6.5, -2.5  # the axis, scene units; the row names stand to its left
ROW_Y = {"deployed": 2.1, "fp127": 0.3, "fp19": -1.5}
JITTER = 0.2  # a market's vertical offset within its row, the same in every row
MARKER = 0.05  # circle radius; the diamond is drawn to match
SEED = 40
LABEL_X = -3.25  # row names end here, level with their row
BRACKET_DROP = 0.48  # the margin bracket sits this far under the upper row's centre
CLOSE_Y = 3.5


def numbers() -> dict:
    cases = live()
    pts = []
    for c in cases:
        t = c["truth"][c["primaryTruth"]]
        pts.append({"id": c["id"], "protocol": c["protocol"], "deployed": float(t["deployed"]["digitsInterest"]), "fp127": float(t["fp127"]["digitsInterest"]), "fp19": float(t["fp19"]["digitsInterest"])})
    survey = _load("docs/benchmarks/accrual-deployed.json")["survey"]
    counts = {p: sum(1 for x in pts if x["protocol"] == p) for p in PROTOCOL_LABEL}
    assert sum(counts.values()) == len(pts)
    assert all(AXIS[0] <= x[k] <= AXIS[1] for x in pts for k, _, _ in ROWS)
    medians = {k: round(statistics.median(x[k] for x in pts), 1) for k, _, _ in ROWS}
    assert medians["deployed"] < medians["fp127"] < medians["fp19"]
    return {
        "points": pts,
        "counts": counts,
        "block": thousands(survey["block"]),
        "date": survey["date"],
        "above": sum(1 for x in pts if x["fp127"] > x["deployed"]),
        "above_fp19": sum(1 for x in pts if x["fp19"] > x["deployed"]),
        "medians": medians,
        "margins": {"fp127": round(medians["fp127"] - medians["deployed"], 1), "fp19": round(medians["fp19"] - medians["fp127"], 1)},
    }


def marker(protocol: str, colour: str):
    """Aave a circle, Morpho a diamond: the shape tells them apart."""
    if protocol == "aave":
        return Dot(radius=MARKER, color=colour, fill_opacity=0.85)
    return Square(side_length=MARKER * 1.8, color=colour, fill_color=colour, fill_opacity=0.85, stroke_width=0).rotate(PI / 4)


class Live(DeckScene):
    def construct(self):
        n = numbers()
        med = n["medians"]
        self.wait(0.6)
        self.play(self.caption(f"docs/benchmarks/accrual-deployed.json · live · block {n['block']} · {n['date']}"))

        axis = GridLine(AXIS, length=AXIS_X1 - AXIS_X0, colour=Palette.RULE, tick_size=0.1)
        axis.shift([AXIS_X0, AXIS_Y, 0] - axis.n2p(AXIS[0]))
        ticks = VGroup(*[digits(str(v), 20, Palette.FAINT).next_to(axis.n2p(v), DOWN, buff=0.18) for v in range(AXIS[0], AXIS[1] + 1, AXIS[2])])
        title = words("correct digits of the pending interest", 22, Palette.MUTED).move_to([(AXIS_X0 + AXIS_X1) / 2, AXIS_Y - 0.56, 0])
        rules = VGroup(*[Line([axis.n2p(v)[0], ROW_Y["fp19"] - 0.5, 0], [axis.n2p(v)[0], ROW_Y["deployed"] + 0.5, 0], color=Palette.RULE, stroke_width=1, stroke_opacity=0.22) for v in range(AXIS[0] + AXIS[2], AXIS[1] + 1, AXIS[2])])
        self.add(rules)
        self.play(Create(axis, run_time=1.0), FadeIn(rules, run_time=0.8))
        self.play(FadeIn(ticks, run_time=0.6), FadeIn(title, run_time=0.6))
        self.wait(0.5)

        # one marker per market, its jitter fixed so it is the same market in every row
        rng = random.Random(SEED)
        order = list(n["points"])
        rng.shuffle(order)
        jitter = {x["id"]: rng.uniform(-JITTER, JITTER) for x in order}
        markers = {}

        def at(x, key):
            return [axis.n2p(x[key])[0], ROW_Y[key] + jitter[x["id"]], 0]

        prev_key, prev_colour = None, None
        for key, name, colour in ROWS:
            y = ROW_Y[key]
            ours = key != "deployed"
            label = words(name, 20, colour).move_to([0, y, 0]).align_to([LABEL_X, 0, 0], RIGHT)
            self.play(FadeIn(label, shift=RIGHT * 0.08, run_time=0.5))
            if prev_key is None:
                # the burst into the top row
                for x in order:
                    markers[x["id"]] = marker(x["protocol"], colour).move_to(at(x, key))
                self.play(LaggedStart(*[FadeIn(markers[x["id"]], scale=0.3) for x in order], lag_ratio=0.01, run_time=3.0))
                self.wait(1.5)
            else:
                # the lift: every marker to its new digits, a faint trail behind it; ours under a band
                band = RoundedRectangle(width=AXIS_X1 - AXIS_X0 + 0.3, height=2 * JITTER + 0.42, corner_radius=0.14, color=colour, fill_color=colour, fill_opacity=0, stroke_width=0).move_to([(AXIS_X0 + AXIS_X1) / 2, y, 0])
                self.add(band)
                self.bring_to_back(band)
                trails = VGroup(*[Line(at(x, prev_key), at(x, key), color=colour, stroke_width=1, stroke_opacity=0).set_z_index(-1) for x in order])
                self.add(trails)
                self.bring_to_back(trails)
                self.play(
                    *[markers[x["id"]].animate(rate_func=ease_in_out_cubic).move_to(at(x, key)).set_color(colour) for x in order],
                    trails.animate.set_stroke(opacity=0.14),
                    band.animate.set_fill(opacity=0.08),
                    run_time=2.4,
                )
                self.wait(0.8)
            # the median, ticked and named over the row
            mx = axis.n2p(med[key])[0]
            tick = Line([mx, y - JITTER - 0.2, 0], [mx, y + JITTER + 0.2, 0], color=colour, stroke_width=2.5)
            tick_lbl = words(f"median {med[key]}", 20, colour).next_to(tick, UP, buff=0.08)
            self.play(Create(tick, run_time=0.5), FadeIn(tick_lbl, shift=UP * 0.06, run_time=0.5))
            if prev_key is not None:
                # the margin between the medians, bracketed in the gap under the row above
                scale = 0.9
                y_bar = ROW_Y[prev_key] - BRACKET_DROP
                margin = measure(axis, med[prev_key], med[key], f"+{n['margins'][key]} digits", scale=scale, drop=(AXIS_Y - y_bar) / scale, colour=colour)
                self.play(Create(margin[0], run_time=0.5), FadeIn(margin[1], run_time=0.5))
                self.play(FadeIn(margin[2], shift=UP * 0.06, run_time=0.5))
                self.wait(3.2)
            else:
                self.wait(2.0)
            prev_key, prev_colour = key, colour

        # the markers' shapes, named once
        legend = VGroup(marker("aave", Palette.BODY), words(f"{n['counts']['aave']} Aave", 18, Palette.BODY), marker("morpho", Palette.BODY), words(f"{n['counts']['morpho']} Morpho", 18, Palette.BODY))
        legend.arrange(RIGHT, buff=0.14)
        legend[2].shift(RIGHT * 0.2)
        legend[3].shift(RIGHT * 0.2)
        legend.move_to([0, CLOSE_Y - 0.45, 0]).align_to([6.9, 0, 0], RIGHT)
        self.play(FadeIn(legend, run_time=0.6))
        self.wait(1.0)

        close = words(
            f"the same {len(n['points'])} markets: {round(med['deployed'])} digits as deployed, {round(med['fp127'])} in FP127, {round(med['fp19'])} in FP19",
            24,
            Palette.TEXT,
        ).move_to([0, CLOSE_Y, 0])
        self.play(FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.wait(12.0)

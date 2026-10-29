"""Slide 10, "Real markets, today": every live Aave reserve and Morpho
market, its pending interest as deployed against the same in FP127.

A square chart on a faint grid, the same scale on both axes: correct
digits of the pending interest as deployed across, the same computed in
FP127 up. A dot per market, Aave slate, Morpho sapphire (both are
"protocol" family on the site; here they need telling apart), arriving in
a burst in a shuffled order. Then a legend with the counts, the
diagonal "deployed = FP127" (emerald: everything above it is a market
FP127 computes to more digits), the camera leaning in on the cloud and
back, and a pulse on each protocol's cloud in turn. About 70 s.

Numbers from docs/benchmarks/accrual-deployed.json: .cases[] with .group
== "live" (.protocol, .primaryTruth, .truth[primaryTruth].deployed
.digitsInterest and .fp127.digitsInterest); .survey.block and .date for
the caption.
"""

from __future__ import annotations

import random

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Create,
    DashedLine,
    FadeIn,
    Indicate,
    LaggedStart,
    MovingCameraScene,
    VGroup,
)
from manim.utils.rate_functions import ease_in_out_cubic

from vocab import Chart, DeckScene, Palette, _load, live, thousands, words

PROTOCOL_COLOUR = {"aave": Palette.SLATE, "morpho": Palette.SAPPHIRE}
PROTOCOL_LABEL = {"aave": "Aave", "morpho": "Morpho"}
PROTOCOL_NOUN = {"aave": "reserves", "morpho": "markets"}
AXIS = (0, 40, 10)
SIDE = 5.7
ORIGIN_XY = (-5.0, -2.45)
SEED = 40


def numbers() -> dict:
    cases = live()
    pts = []
    for c in cases:
        t = c["truth"][c["primaryTruth"]]
        pts.append({"id": c["id"], "protocol": c["protocol"], "deployed": float(t["deployed"]["digitsInterest"]), "fp127": float(t["fp127"]["digitsInterest"])})
    survey = _load("docs/benchmarks/accrual-deployed.json")["survey"]
    counts = {p: sum(1 for x in pts if x["protocol"] == p) for p in PROTOCOL_COLOUR}
    assert sum(counts.values()) == len(pts)
    assert all(AXIS[0] <= x["deployed"] <= AXIS[1] and AXIS[0] <= x["fp127"] <= AXIS[1] for x in pts)
    return {"points": pts, "counts": counts, "block": thousands(survey["block"]), "date": survey["date"], "above": sum(1 for x in pts if x["fp127"] > x["deployed"])}


class Live(DeckScene, MovingCameraScene):
    def construct(self):
        n = numbers()
        frame = self.camera.frame
        self.wait(0.6)
        self.play(self.caption(f"docs/benchmarks/accrual-deployed.json · live · block {n['block']} · {n['date']}"))

        chart = Chart(AXIS, AXIS, SIDE, SIDE, origin=(*ORIGIN_XY, 0))
        for v in range(AXIS[0], AXIS[1] + 1, AXIS[2]):
            chart.x_label(v, str(v), mono=True)
            chart.y_label(v, str(v), mono=True)
        chart.x_title("correct digits of the pending interest, as deployed", size=20, drop=0.62)
        chart.y_title("the same, in FP127", size=20, colour=Palette.EMERALD)
        grid = chart.grid()
        self.play(Create(chart.x_axis, run_time=1.0), Create(chart.y_axis, run_time=1.0))
        self.play(FadeIn(chart.labels, run_time=0.6), FadeIn(chart.titles, run_time=0.6), FadeIn(grid, run_time=0.8))
        self.wait(1.0)

        # the burst
        order = list(n["points"])
        random.Random(SEED).shuffle(order)
        dots = {p: VGroup() for p in PROTOCOL_COLOUR}
        ordered = []
        for x in order:
            d = chart.dot(x["deployed"], x["fp127"], PROTOCOL_COLOUR[x["protocol"]], radius=0.055, fill_opacity=0.85)
            dots[x["protocol"]].add(d)
            ordered.append(d)
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in ordered], lag_ratio=0.012, run_time=4.5))
        self.wait(2.5)

        # legend with the counts
        legend = VGroup()
        for p, colour in PROTOCOL_COLOUR.items():
            row = VGroup(chart.dot(0, 0, colour, radius=0.07), words(f"{PROTOCOL_LABEL[p]} · {n['counts'][p]} {PROTOCOL_NOUN[p]}", 22, colour))
            row[1].next_to(row[0], RIGHT, buff=0.18)
            legend.add(row)
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([4.6, 1.6, 0]).align_to([2.6, 0, 0], LEFT)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.08) for r in legend], lag_ratio=0.3, run_time=1.0))
        self.wait(3.0)

        # the diagonal: deployed = FP127
        diag = DashedLine(chart.c2p(AXIS[0], AXIS[0]), chart.c2p(AXIS[1], AXIS[1]), color=Palette.EMERALD, stroke_width=1.5, dash_length=0.08, stroke_opacity=0.8)
        diag_lbl = words("deployed = FP127", 18, Palette.EMERALD).rotate(0.7853982).move_to(chart.c2p(31.5, 29.0))
        self.play(Create(diag, run_time=1.2))
        self.play(FadeIn(diag_lbl, run_time=0.5))
        above = words(f"{n['above']} of {len(n['points'])} above the line", 22, Palette.BODY)
        above.next_to(legend, DOWN, buff=0.6).align_to(legend, LEFT)
        self.play(FadeIn(above, shift=UP * 0.08, run_time=0.6))
        self.wait(3.0)

        # lean in on the cloud, then back; a pulse on each protocol in turn
        cloud = VGroup(*ordered)
        self.play(frame.animate(rate_func=ease_in_out_cubic).set(width=9.5).move_to(cloud.get_center() + RIGHT * 0.8 + DOWN * 0.2), run_time=2.4)
        self.wait(1.0)
        for p in PROTOCOL_COLOUR:
            self.play(Indicate(dots[p], color=PROTOCOL_COLOUR[p], scale_factor=1.06, run_time=0.9), Indicate(legend[list(PROTOCOL_COLOUR).index(p)], color=PROTOCOL_COLOUR[p], scale_factor=1.03, run_time=0.9))
            self.wait(1.5)
        self.play(frame.animate(rate_func=ease_in_out_cubic).set(width=14.222222222222221).move_to([0, 0, 0]), run_time=2.4)
        self.wait(14.0)

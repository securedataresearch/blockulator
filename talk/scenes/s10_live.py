"""Slide 10, "Real markets, today": every live Aave reserve and Morpho
market, its pending interest as deployed, then the same interest in
BL127, then in BL19.

A faceted strip plot in the grammar of graphics: one row of data per
market; protocol is the facet (Aave left, Morpho right, equal panels on
the same 0–80 scale), method is the y row ("as deployed" on top, "in
BL127", "in BL19" beneath, so the eye travels down to the heroes),
correct digits of the pending interest is x. Each market is one small
dot, jittered within its row band on a fixed seed so the density shows;
colour is the method (SLATE, EMERALD, TEXT: white is BL19's family
colour on this slide, EXACT is not used). The summary layer is one
median tick per row per panel with its value labelled beside it (the
medians say the margin: no bracket restates it). Faint gridlines at the axis ticks, nothing else: no trails, no
bands, no halos on dots. The hero mark is the glow under the BL19
row's median tick.

The dots move as themselves: every dot drops to the next row and slides
to its new x in one Transform, so a viewer who watches one market sees
it travel; the strip it left stays, so the held frame shows every row.
Three sections, one per click: the deployed row; the move to BL127; the
move to BL19 (the poster). The chart's chrome, the three row keys and the
axis tick labels, is self.key (not counted by vocab.text_census).

Numbers from docs/benchmarks/accrual-deployed.json: .cases[] with .group
== "live" (.protocol, .primaryTruth, .truth[primaryTruth].deployed
.digitsInterest, .bl127.digitsInterest and .bl19.digitsInterest); the
medians (overall and per protocol) and the margins between them are
computed here. Provenance (.survey.block and .date) is in the slide's notes.
"""

from __future__ import annotations

import random
import statistics

from manim import (
    LEFT,
    RIGHT,
    UP,
    Create,
    Dot,
    FadeIn,
    LaggedStart,
    Line,
    Text,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_in_out_cubic

from vocab import ROW_COLOUR, SIZE_BODY, SIZE_CAPTION, Chart, DeckScene, Palette, glow_line, live, words

TITLE = "Real markets, today"
ROWS = tuple((key, name, ROW_COLOUR["s10"][key]) for key, name in (("deployed", "as deployed"), ("bl127", "in BL127"), ("bl19", "in BL19")))
PROTOCOLS = ("aave", "morpho")  # the facets, left to right
PROTOCOL_LABEL = {"aave": "Aave", "morpho": "Morpho"}
AXIS = (0, 80, 20)  # correct digits; a gridline and a label at every tick
AXIS_TITLE = "correct digits of the pending interest"

# the frame: a 5% safe area is x in ±6.4, y in ±3.6
X_LEFT = -6.3  # the title and the row labels start here
LABEL_RIGHT = -3.92  # the row labels end here
PANEL_X0, PANEL_W, PANEL_GAP = -3.6, 4.7, 0.6  # two equal panels fill the safe width; the gap keeps "80" and "0" apart
AXIS_Y, PANEL_TOP = -2.45, 2.2  # the shared x scale sits here; the gridlines rise to the top
ROW_Y = {"deployed": 1.5, "bl127": -0.1, "bl19": -1.7}  # the row centres, equal pitch
BAND = 0.2  # a row band's half-height; the jitter stays inside it
DOT = 0.045  # the brief's radius
TICK_HALF = 0.3  # the median tick: 1.5x the band height
LABEL_LIFT = 0.36  # the median label's bottom above the row centre
SEED = 40
Y_FACET, Y_AXIS_TITLE = 2.62, -3.3  # the facet titles' baseline, under the right mark
SIZE_TICK = SIZE_CAPTION + 4  # the axis labels, per the brief

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def numbers() -> dict:
    cases = live()
    pts = []
    for c in cases:
        t = c["truth"][c["primaryTruth"]]
        pts.append({"id": c["id"], "protocol": c["protocol"], "deployed": float(t["deployed"]["digitsInterest"]), "bl127": float(t["bl127"]["digitsInterest"]), "bl19": float(t["bl19"]["digitsInterest"])})
    counts = {p: sum(1 for x in pts if x["protocol"] == p) for p in PROTOCOLS}
    assert sum(counts.values()) == len(pts)
    assert all(AXIS[0] <= x[k] <= AXIS[1] for x in pts for k, _, _ in ROWS)

    def summary(sub: list[dict]) -> dict:
        med = {k: round(statistics.median(x[k] for x in sub), 1) for k, _, _ in ROWS}
        assert med["deployed"] < med["bl127"] < med["bl19"]
        return {"medians": med}

    per = {p: {"count": counts[p], **summary([x for x in pts if x["protocol"] == p])} for p in PROTOCOLS}
    return {
        "points": pts,
        "counts": counts,
        "axis_ticks": list(range(AXIS[0], AXIS[1] + 1, AXIS[2])),
        "by_protocol": per,
    }


class Live(DeckScene):
    SECTIONS = ("deployed", "bl127", "bl19")

    def construct(self):
        n = numbers()
        self.section(0)
        # the chrome, on the first frame: the title, the two facets (their titles, axes,
        # gridlines, tick labels, the axis title) and the three row keys in the rows'
        # colours (ROW_COLOUR["s10"]); only the dots and their medians arrive
        title = self.title(TITLE, SIZE_BODY, Palette.TEXT)
        row_labels = {key: words(name, SIZE_BODY, colour).move_to([0, ROW_Y[key], 0]).align_to([LABEL_RIGHT, 0, 0], RIGHT) for key, name, colour in ROWS}

        # ---- the facets: one panel per protocol on the same scale, a gridline at every tick
        panels: dict[str, Chart] = {}
        facet_titles, grids = VGroup(), VGroup()
        for i, p in enumerate(PROTOCOLS):
            x0 = PANEL_X0 + i * (PANEL_W + PANEL_GAP)
            chart = Chart(AXIS, (0, 1, 2), PANEL_W, PANEL_TOP - AXIS_Y, origin=(x0, AXIS_Y, 0))
            chart.y_axis.set_stroke(width=1, opacity=0.22)  # the gridline at 0, like the others
            for v in n["axis_ticks"]:
                chart.x_label(v, str(v), size=SIZE_TICK, mono=True)
            grids.add(chart.grid())
            panels[p] = chart
            ft = words(f"{PROTOCOL_LABEL[p]} · {n['by_protocol'][p]['count']} markets", SIZE_BODY, Palette.MUTED).move_to([x0 + PANEL_W / 2, Y_FACET, 0])
            facet_titles.add(ft.shift(UP * (Y_FACET - ft[0].get_bottom()[1])))  # on one baseline: the capital's foot at Y_FACET
        axis_title = words(AXIS_TITLE, 22, Palette.MUTED).move_to([PANEL_X0 + PANEL_W + PANEL_GAP / 2, Y_AXIS_TITLE, 0])
        # the chart's key and axes (the row keys, the tick labels): chrome, not counted by the census
        self.key = VGroup(*row_labels.values(), *[c.labels for c in panels.values()])
        self.fix(title, *panels.values(), axis_title, facet_titles, *row_labels.values())
        self.wait(0.6)

        # ---- the data: one dot per market, its jitter fixed so it is the same dot in every row
        rng = random.Random(SEED)
        order = list(n["points"])
        rng.shuffle(order)
        jitter = {x["id"]: rng.uniform(-(BAND - DOT), BAND - DOT) for x in order}

        def px(p: str, v: float) -> float:
            return panels[p].c2p(v, 0)[0]

        def place(x: dict, key: str) -> list:
            return [px(x["protocol"], x[key]), ROW_Y[key] + jitter[x["id"]], 0]

        def dots_at(key: str, colour: str) -> VGroup:
            return VGroup(*[Dot(place(x, key), radius=DOT, color=colour, fill_opacity=0.85, stroke_width=0) for x in order])

        def inside(p: str, left: float, width: float) -> bool:
            x0 = panels[p].origin[0]
            return x0 <= left and left + width <= x0 + PANEL_W

        def median_mark(p: str, key: str, colour: str) -> tuple[VGroup, Text]:
            """The row's median: a tick through the band and its value beside
            the tick's top, to the right where that fits in the panel, else
            to the left."""
            y, m = ROW_Y[key], n["by_protocol"][p]["medians"][key]
            x = px(p, m)
            # the tick in front of the dots, cased in the background so it reads inside the cluster
            tick = VGroup(Line([x, y - TICK_HALF, 0], [x, y + TICK_HALF, 0], color=Palette.BG, stroke_width=8), Line([x, y - TICK_HALF, 0], [x, y + TICK_HALF, 0], color=colour, stroke_width=3))
            lbl = words(f"median {m}", SIZE_BODY, colour)
            lbl.move_to([0, y + LABEL_LIFT + lbl.height / 2, 0])
            if inside(p, x + 0.1, lbl.width):
                lbl.align_to([x + 0.1, 0, 0], LEFT)
            else:
                lbl.align_to([x - 0.1, 0, 0], RIGHT)
            return tick, lbl

        # ---- the rows: the deployed strip fills; then the same dots move down, as themselves
        dots = None
        for k, (key, name, colour) in enumerate(ROWS):
            if k:
                self.section(k, hold=1.2)
            if dots is None:
                dots = dots_at(key, colour)
                self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.002, run_time=1.0))
            else:
                # the strip above stays (the distribution is the point); the same dots, by
                # index, travel down to the new row and across to their new digits
                mover = dots.copy()
                self.add(mover)
                self.play(Transform(mover, dots_at(key, colour), run_time=1.5, rate_func=ease_in_out_cubic))
                dots = mover
            self.wait(0.4)
            marks = [median_mark(p, key, colour) for p in PROTOCOLS]
            if key == "bl19":
                # the hero: a glow under each BL19 median tick, drawn with it
                glows = VGroup(*[glow_line([t[1].get_start(), t[1].get_end()], colour) for t, _ in marks])
                self.add(glows)
                self.bring_to_back(glows)
                self.play(Create(glows, run_time=0.5), *[Create(t, run_time=0.5) for t, _ in marks], *[FadeIn(lbl, shift=UP * 0.06, run_time=0.5) for _, lbl in marks])
            else:
                self.play(*[Create(t, run_time=0.5) for t, _ in marks], *[FadeIn(lbl, shift=UP * 0.06, run_time=0.5) for _, lbl in marks])
        self.close()

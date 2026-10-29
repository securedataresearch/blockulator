"""Slide 10, "Real markets, today": every live Aave reserve and Morpho
market, its pending interest as deployed, then the same interest in
FP127, then in FP19.

A faceted strip plot in the grammar of graphics: one row of data per
market; protocol is the facet (Aave left, Morpho right, equal panels on
the same 0–80 scale), method is the y row ("as deployed" on top, "in
FP127", "in FP19" beneath, so the eye travels down to the heroes),
correct digits of the pending interest is x. Each market is one small
dot, jittered within its row band on a fixed seed so the density shows;
colour is the method (SLATE, EMERALD, TEXT: white is FP19's family
colour on this slide, EXACT is not used). The summary layer is one
median tick per row per panel with its value labelled beside it; the
margin between consecutive medians is a bracket in the gap between the
rows. Faint gridlines at the axis ticks, nothing else: no trails, no
bands, no halos on dots. The hero mark is the glow under the FP19
row's median tick.

The dots move as themselves: every dot drops to the next row and slides
to its new x in one Transform, so a viewer who watches one market sees
it travel; the strip it left stays, so the held frame shows every row. Four sections, one per click: the deployed row; the move to
FP127; the move to FP19; the closing line.

Numbers from docs/benchmarks/accrual-deployed.json: .cases[] with .group
== "live" (.protocol, .primaryTruth, .truth[primaryTruth].deployed
.digitsInterest, .fp127.digitsInterest and .fp19.digitsInterest); the
medians (overall and per protocol) and the margins between them are
computed here; .survey.block and .date for the caption.
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

from vocab import ROW_COLOUR, SIZE_BODY, SIZE_CAPTION, Chart, DeckScene, Palette, _load, glow_bar, glow_line, live, thousands, words

TITLE = "Real markets, today"
ROWS = tuple((key, name, ROW_COLOUR["s10"][key]) for key, name in (("deployed", "as deployed"), ("fp127", "in FP127"), ("fp19", "in FP19")))
PROTOCOLS = ("aave", "morpho")  # the facets, left to right
PROTOCOL_LABEL = {"aave": "Aave", "morpho": "Morpho"}
AXIS = (0, 80, 20)  # correct digits; a gridline and a label at every tick
AXIS_TITLE = "correct digits of the pending interest"

# the frame: a 5% safe area is x in ±6.4, y in ±3.6
X_LEFT = -6.3  # the title and the row labels start here
LABEL_RIGHT = -3.92  # the row labels end here
PANEL_X0, PANEL_W, PANEL_GAP = -3.6, 4.8, 0.4  # two equal panels fill the safe width
AXIS_Y, PANEL_TOP = -1.9, 2.05  # the shared x scale sits here; the gridlines rise to the top
ROW_Y = {"deployed": 1.8, "fp127": 0.2, "fp19": -1.4}  # the row centres, equal pitch
BAND = 0.2  # a row band's half-height; the jitter stays inside it
DOT = 0.045  # the brief's radius
TICK_HALF = 0.3  # the median tick: 1.5x the band height
LABEL_LIFT = 0.36  # the median label's bottom above the row centre
BRACKET_LIFT = 1.0  # the margin bracket above the lower row's centre, in the gap
SEED = 40
Y_FACET, Y_AXIS_TITLE, Y_CLOSE = 2.78, -2.55, -2.97  # the facet titles under the right mark (was 2.94)
SIZE_TICK = SIZE_CAPTION + 4  # the axis labels, per the brief
SIZE_CLOSE = 28  # the closing line does not fit the safe width at BODY (reported)

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def numbers() -> dict:
    cases = live()
    pts = []
    for c in cases:
        t = c["truth"][c["primaryTruth"]]
        pts.append({"id": c["id"], "protocol": c["protocol"], "deployed": float(t["deployed"]["digitsInterest"]), "fp127": float(t["fp127"]["digitsInterest"]), "fp19": float(t["fp19"]["digitsInterest"])})
    survey = _load("docs/benchmarks/accrual-deployed.json")["survey"]
    counts = {p: sum(1 for x in pts if x["protocol"] == p) for p in PROTOCOLS}
    assert sum(counts.values()) == len(pts)
    assert all(AXIS[0] <= x[k] <= AXIS[1] for x in pts for k, _, _ in ROWS)

    def summary(sub: list[dict]) -> dict:
        med = {k: round(statistics.median(x[k] for x in sub), 1) for k, _, _ in ROWS}
        assert med["deployed"] < med["fp127"] < med["fp19"]
        return {"medians": med, "margins": {"fp127": round(med["fp127"] - med["deployed"], 1), "fp19": round(med["fp19"] - med["fp127"], 1)}}

    whole = summary(pts)
    per = {p: {"count": counts[p], **summary([x for x in pts if x["protocol"] == p])} for p in PROTOCOLS}
    return {
        "points": pts,
        "count": len(pts),
        "counts": counts,
        "block": thousands(survey["block"]),
        "date": survey["date"],
        "axis_ticks": list(range(AXIS[0], AXIS[1] + 1, AXIS[2])),
        "above": sum(1 for x in pts if x["fp127"] > x["deployed"]),
        "above_fp19": sum(1 for x in pts if x["fp19"] > x["deployed"]),
        "medians": whole["medians"],
        "medians_rounded": {k: round(v) for k, v in whole["medians"].items()},
        "margins": whole["margins"],
        "by_protocol": per,
    }


class Live(DeckScene):
    SECTIONS = ("deployed", "fp127", "fp19", "closing")

    def construct(self):
        n = numbers()
        self.section(0)
        # the chrome, on the first frame: the caption, the title, the two facets (their
        # titles, axes, gridlines, tick labels, the axis title) and the three row keys in
        # the rows' colours (ROW_COLOUR["s10"]); only the dots and their medians arrive
        self.caption_now(f"docs/benchmarks/accrual-deployed.json · live · block {n['block']} · {n['date']}")
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
            facet_titles.add(words(f"{PROTOCOL_LABEL[p]} · {n['by_protocol'][p]['count']} markets", SIZE_BODY, Palette.MUTED).move_to([x0 + PANEL_W / 2, Y_FACET, 0]))
        axis_title = words(AXIS_TITLE, 22, Palette.MUTED).move_to([PANEL_X0 + PANEL_W + PANEL_GAP / 2, Y_AXIS_TITLE, 0])
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

        def bracket(p: str, prev: str, key: str, colour: str) -> VGroup:
            """The margin between two rows' medians: a bracket |——| in the gap
            under the upper row, from the upper median's x to the lower's,
            labelled in digits beside its end (the right end where that fits
            in the panel, else the left end)."""
            y = ROW_Y[key] + BRACKET_LIFT
            a, b = px(p, n["by_protocol"][p]["medians"][prev]), px(p, n["by_protocol"][p]["medians"][key])
            cap = UP * 0.07
            pa, pb = [a, y, 0], [b, y, 0]
            bar = Line(pa, pb, color=colour, stroke_width=1.5)
            caps = VGroup(Line(pa - cap, pa + cap, color=colour, stroke_width=1.5), Line(pb - cap, pb + cap, color=colour, stroke_width=1.5))
            lbl = words(f"+{n['by_protocol'][p]['margins'][key]} digits", SIZE_BODY, colour).move_to([0, y, 0])
            if inside(p, max(a, b) + 0.12, lbl.width):
                lbl.align_to([max(a, b) + 0.12, 0, 0], LEFT)
            else:
                lbl.align_to([min(a, b) - 0.12, 0, 0], RIGHT)
            return VGroup(bar, caps, lbl)

        # ---- the rows: the deployed strip fills; then the same dots move down, as themselves
        dots = None
        prev = None
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
            if key == "fp19":
                # the hero: a glow under each FP19 median tick, drawn with it
                glows = VGroup(*[glow_line([t[1].get_start(), t[1].get_end()], colour) for t, _ in marks])
                self.add(glows)
                self.bring_to_back(glows)
                self.play(Create(glows, run_time=0.5), *[Create(t, run_time=0.5) for t, _ in marks], *[FadeIn(lbl, shift=UP * 0.06, run_time=0.5) for _, lbl in marks])
            else:
                self.play(*[Create(t, run_time=0.5) for t, _ in marks], *[FadeIn(lbl, shift=UP * 0.06, run_time=0.5) for _, lbl in marks])
            if prev is not None:
                brs = [bracket(p, prev, key, colour) for p in PROTOCOLS]
                self.play(*[Create(b[0], run_time=0.5) for b in brs], *[FadeIn(b[1], run_time=0.5) for b in brs])
                self.play(*[FadeIn(b[2], shift=UP * 0.06, run_time=0.4) for b in brs])
            prev = key

        # ---- the closing line, in the rounded medians of all 326
        self.section(len(ROWS), hold=1.5)
        mr = n["medians_rounded"]
        close = words(f"the same {n['count']} markets: {mr['deployed']} digits as deployed, {mr['fp127']} in FP127, {mr['fp19']} in FP19", SIZE_CLOSE, Palette.TEXT).move_to([0, Y_CLOSE, 0])
        bar = glow_bar(close, pad=0.12)
        self.play(FadeIn(bar, run_time=0.8), FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.close()

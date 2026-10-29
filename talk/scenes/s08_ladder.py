"""Slide 8, "Measure it": correct digits against the number of steps.

A chart on a faint grid: N on a log axis (1 … 10,000), correct digits on
the other; one line per library, a dot at every N where the ladder
measured it, colour by family (static/data/libraries.json). The
18-decimal libraries' lines, which coincide, draw in first and step down
together, named under the line; then ABDK 64.64, Maker (RAY) and
ABDKMathQuad, each with a small end label; last, on top and under a glow,
FP127 and FP19 ("ours", thicker). A slope glyph names the trend the data
shows: one digit per decade of steps. About 70 s.

Numbers from docs/benchmarks/ladder.json: .ladder (the N), .ladderLog10,
.axisMax, and scenario "compound" .summary[lib][N].digits.median; only
libraries with a median at every N are drawn (the accrual libraries that
have no general mul report none), and fp127lib is skipped as a duplicate
of fp127. Labels from static/data/libraries.json.
"""

from __future__ import annotations

import textwrap

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Create,
    DashedLine,
    FadeIn,
    LaggedStart,
    VGroup,
    VMobject,
)

from vocab import Chart, DeckScene, Palette, colour_of, glow_line, halo, ladder, libs, thousands, words

SCENARIO = "compound"
SKIP = ("fp127lib",)  # the same library as fp127, called inline
X_RANGE = (0, 4, 1)  # log10 N
WIDTH, HEIGHT = 9.6, 5.3
ORIGIN_XY = (-5.3, -2.3)
LABEL_GAP = 0.3  # minimum spacing between end labels, scene units
GUIDE_DROP = 5.0  # digits below the 18-decimal line the slope guide is drawn


def numbers() -> dict:
    d = ladder(SCENARIO)
    lib = libs()
    summary = d["scenario"]["summary"]
    series = []
    for lid, cells in summary.items():
        if lid in SKIP:
            continue
        vals = [cells.get(str(n), {}).get("digits", {}).get("median") for n in d["N"]]
        if any(v is None for v in vals):
            continue
        series.append({"id": lid, "label": lib[lid]["label"], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours")), "digits": vals})
    # identical series share one line and one label
    groups: list[dict] = []
    for s in series:
        for g in groups:
            if g["digits"] == s["digits"] and g["family"] == s["family"]:
                g["ids"].append(s["id"])
                g["labels"].append(s["label"])
                break
        else:
            groups.append({"ids": [s["id"]], "labels": [s["label"]], "family": s["family"], "ours": s["ours"], "digits": s["digits"]})
    return {"N": d["N"], "log10": [d["log10"][str(n)] for n in d["N"]], "axisMax": d["axisMax"], "groups": groups}


class Ladder(DeckScene):
    def construct(self):
        n = numbers()
        xs = [float(v) for v in n["log10"]]
        y_max = int(n["axisMax"])
        self.wait(0.6)
        self.play(self.caption(f"docs/benchmarks/ladder.json · {SCENARIO} · median of the inputs"))

        chart = Chart(X_RANGE, (0, y_max, 20), WIDTH, HEIGHT, origin=(*ORIGIN_XY, 0))
        for k in range(X_RANGE[0], X_RANGE[1] + 1):
            chart.x_label(k, thousands(10**k))
        for y in range(0, y_max + 1, 20):
            chart.y_label(y, str(y), mono=True)
        chart.x_title("N steps, one multiplication each")
        chart.y_title("correct digits")
        grid = chart.grid()
        self.play(Create(chart.x_axis, run_time=1.0), Create(chart.y_axis, run_time=1.0))
        self.play(FadeIn(chart.labels, run_time=0.6), FadeIn(chart.titles, run_time=0.6), FadeIn(grid, run_time=0.8))
        self.wait(1.5)

        # draw order: the 18-decimal libraries first, then up the chart; ours last, on top
        order = sorted(n["groups"], key=lambda g: (g["ours"], g["digits"][-1]))
        labels = []
        for g in order:
            colour = colour_of({"family": g["family"]})
            pts = [chart.c2p(x, float(v)) for x, v in zip(xs, g["digits"])]
            line = VMobject(color=colour, stroke_width=5.0 if g["ours"] else 2.5).set_points_as_corners(pts)
            dots = VGroup(*[chart.dot(x, float(v), colour, radius=0.07 if g["ours"] else 0.06) for x, v in zip(xs, g["digits"])])
            anims = [Create(line, run_time=2.2), LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.1, run_time=2.2)]
            if g["ours"]:
                anims.insert(0, Create(glow_line(pts, colour), run_time=2.2))
            self.play(*anims)
            names = " · ".join(g["labels"])
            if len(g["labels"]) > 2:
                # the coinciding lines: name them under the line, inside the plot
                text = "\n".join(textwrap.wrap(f"{names}: {g['digits'][-1]}", 60))
                lbl = words(text, 18, colour, line_spacing=0.6)
                lbl.move_to(chart.c2p(2.0, 5.0)).align_to(chart.c2p(0.4, 0), LEFT)
                self.play(FadeIn(lbl, run_time=0.6))
                self.wait(5.0)
            else:
                lbl = words(f"{names} · {g['digits'][-1]}", 20 if g["ours"] else 18, colour)
                lbl.next_to(pts[-1], RIGHT, buff=0.18)
                labels.append(lbl)
                if g["ours"]:
                    self.play(FadeIn(halo(pts[-1], colour, radius=0.07), run_time=0.6), FadeIn(lbl, shift=RIGHT * 0.05, run_time=0.5))
                    self.wait(4.0)
                else:
                    self.play(FadeIn(lbl, shift=RIGHT * 0.05, run_time=0.5))
                    self.wait(2.0)
        # nudge end labels apart (the two nearest lines end less than a label apart)
        placed = sorted(labels, key=lambda t: t.get_y())
        for a, b in zip(placed, placed[1:]):
            if b.get_y() - a.get_y() < LABEL_GAP:
                b.shift(UP * (LABEL_GAP - (b.get_y() - a.get_y())))

        # the trend the data shows: a digit lost per tenfold in N, as a guide
        # parallel to the 18-decimal line (slope −1 digit per decade), set below it
        gold = [g for g in order if len(g["labels"]) > 2][0]
        x0, x1 = float(xs[0]), float(xs[-1])
        y0 = float(gold["digits"][0]) - GUIDE_DROP
        guide = DashedLine(chart.c2p(x0, y0), chart.c2p(x1, y0 - (x1 - x0)), color=Palette.FAINT, stroke_width=1.5, dash_length=0.08)
        guide_lbl = words("one digit per decade", 18, Palette.FAINT).next_to(guide.get_end(), DOWN + LEFT, buff=0.08).shift(RIGHT * 0.9)
        self.play(Create(guide, run_time=1.2))
        self.play(FadeIn(guide_lbl, run_time=0.5))
        self.wait(12.0)

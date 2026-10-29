"""Slide 9, "The cliff": where exp stops drifting and disappears.

A chart on a faint grid: one column per probe, exp(−40) through exp(−100)
in the order edges.json holds them; correct digits on the other axis.
Columns arrive left to right. In each, a dot per library at its
correct-digit height, colour by family, the libraries spread a little
within the column so coincident values stay visible. A cell whose result
was zero is a dot that snaps down to 0 and turns WRONG (red), labelled
"0"; a cell that reverted is a hollow red marker in a band under the
axis, labelled "revert". FP127 and FP19 draw last in every column, on
top, each under a halo. A legend names the libraries. About 45 s.

Numbers from docs/benchmarks/edges.json: op "exp", the probes whose
single argument lies in [−100, −40] (.args, .truth, .cells[lib].digits /
.zero / .reverted / .reasonName). Libraries: those in .cells that are not
unsupported and not merely out of range on every one of these probes (a
library whose representation cannot hold a negative argument reports
ParamOutOfRange on each; that is its domain, not a failure of exp);
fp127lib is skipped as a duplicate of fp127. Labels from
static/data/libraries.json.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    Create,
    FadeIn,
    LaggedStart,
    VGroup,
)

from vocab import Chart, DeckScene, GridLine, Palette, colour_of, edges, halo, libs, snap, words

OP = "exp"
ARG_LO, ARG_HI = -100, -40
SKIP = ("fp127lib",)
RANGE_REASON = "ParamOutOfRange"  # the argument does not fit the representation: nothing was called
WIDTH, HEIGHT = 10.2, 5.2
ORIGIN_XY = (-5.9, -2.3)
Y_STEP = 20
REVERT_BAND = -6.0  # digits axis position of the "revert" band, under 0
SPREAD = 0.1  # scene units between libraries within a column


def numbers() -> dict:
    op = edges(OP)
    lib = libs()
    probes = [p for p in op["probes"] if len(p["args"]) == 1 and ARG_LO <= float(p["args"][0]) <= ARG_HI]
    assert probes, (OP, ARG_LO, ARG_HI)

    def out_of_range(c):
        return bool(c.get("reverted")) and str(c.get("reasonName", "")).startswith(RANGE_REASON)

    lids = []
    for lid in probes[0]["cells"]:
        if lid in SKIP:
            continue
        cells = [p["cells"][lid] for p in probes]
        if all(c.get("unsupported") or out_of_range(c) for c in cells):
            continue
        lids.append(lid)
    # family order as the site's legends: ours first, then the rest in libraries.json order
    lids.sort(key=lambda lid: (not lib[lid].get("ours"), list(lib).index(lid)))
    columns = []
    for p in probes:
        cells = {}
        for lid in lids:
            c = p["cells"][lid]
            if c.get("unsupported"):
                cells[lid] = {"kind": "unsupported"}
            elif c.get("reverted"):
                cells[lid] = {"kind": "revert", "reason": c.get("reasonName")}
            elif c.get("zero"):
                cells[lid] = {"kind": "zero", "digits": 0}
            else:
                cells[lid] = {"kind": "value", "digits": float(c["digits"])}
        columns.append({"arg": p["args"][0], "cells": cells})
    y_max = max(c["digits"] for col in columns for c in col["cells"].values() if "digits" in c)
    return {
        "libs": [{"id": lid, "label": lib[lid]["label"], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours"))} for lid in lids],
        "columns": columns,
        "axisMax": int(-(-y_max // Y_STEP) * Y_STEP),
    }


class Cliff(DeckScene):
    def construct(self):
        n = numbers()
        cols, lids = n["columns"], [r["id"] for r in n["libs"]]
        y_max = n["axisMax"]
        self.wait(0.6)
        self.play(self.caption(f"docs/benchmarks/edges.json · {OP}"))

        chart = Chart((0, len(cols) - 1, 1), (0, y_max, Y_STEP), WIDTH, HEIGHT, origin=(*ORIGIN_XY, 0))
        for i, col in enumerate(cols):
            chart.x_label(i, f"exp({col['arg'].replace('-', '−')})", use_markup=True, buff=0.55)
        for y in range(0, y_max + 1, Y_STEP):
            chart.y_label(y, str(y), mono=True)
        revert_lbl = words("revert", 18, Palette.WRONG).next_to(chart.c2p(0, REVERT_BAND), LEFT, buff=0.18)
        chart.y_title("correct digits")
        grid = chart.grid()
        self.play(Create(chart.x_axis, run_time=1.0), Create(chart.y_axis, run_time=1.0))
        self.play(FadeIn(chart.labels, run_time=0.6), FadeIn(chart.titles, run_time=0.6), FadeIn(grid, run_time=0.8))

        # legend, right of the plot
        legend = VGroup()
        for r in n["libs"]:
            colour = colour_of(r)
            row = VGroup(chart.dot(0, 0, colour, radius=0.07), words(r["label"], 18, colour))
            row[1].next_to(row[0], RIGHT, buff=0.15)
            legend.add(row)
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to([5.9, 0.9, 0]).align_to([4.75, 0, 0], LEFT)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.05) for r in legend], lag_ratio=0.1, run_time=1.2))
        self.wait(1.0)

        offsets = {lid: (k - (len(lids) - 1) / 2) * SPREAD for k, lid in enumerate(lids)}
        last_digits = {lid: None for lid in lids}
        seen_zero = seen_revert = False  # the labels name the first column where each appears
        for i, col in enumerate(cols):
            arrive, snaps, reverts, labels = [], [], [], []
            x_lbl = chart.c2p(i, 0)[0] + (len(lids) - 1) / 2 * SPREAD + 0.12
            for lid in lids:  # ours first in lids, so draw them last
                c = col["cells"][lid]
                fam = next(r for r in n["libs"] if r["id"] == lid)
                colour = colour_of(fam)
                x = chart.c2p(i, 0)[0] + offsets[lid]
                if c["kind"] == "value":
                    d = chart.dot(i, c["digits"], colour, radius=0.075 if fam["ours"] else 0.065).set_x(x)
                    arrive.append((d, fam["ours"], colour))
                    last_digits[lid] = c["digits"]
                elif c["kind"] == "zero":
                    start = last_digits[lid] if last_digits[lid] else Y_STEP / 4
                    d = chart.dot(i, start, colour, radius=0.075 if fam["ours"] else 0.065).set_x(x)
                    line = GridLine((0, 1, 1), length=abs(chart.c2p(0, start)[1] - chart.c2p(0, 0)[1]), rotation=-1.5707963, tick_size=0)
                    line.move_to([x, (chart.c2p(0, start)[1] + chart.c2p(0, 0)[1]) / 2, 0])
                    snaps.append((d, line, fam["ours"]))
                    if not seen_zero:
                        labels.append(words("0", 16, Palette.WRONG).move_to([x_lbl + 0.1, chart.c2p(0, 0)[1] + 0.12, 0]))
                        seen_zero = True
                    last_digits[lid] = 0
                elif c["kind"] == "revert":
                    m = Circle(radius=0.065, color=Palette.WRONG, stroke_width=2).move_to([x, chart.c2p(0, REVERT_BAND)[1], 0])
                    reverts.append(m)
                    if not seen_revert:
                        labels.append(words("revert", 16, Palette.WRONG).move_to([x_lbl + 0.32, chart.c2p(0, REVERT_BAND)[1], 0]))
                        seen_revert = True
            # plain values first, then the zeros snapping down, then the reverts; ours on top with a halo
            plain = [a for a in reversed(arrive) if not a[1]]
            ours = [a for a in reversed(arrive) if a[1]]
            if plain:
                self.play(LaggedStart(*[FadeIn(d, scale=0.4) for d, _, _ in plain], lag_ratio=0.08, run_time=0.6))
            if snaps:
                for d, _, _ in snaps:
                    self.add(d)
                self.play(LaggedStart(*[snap(d, line, 1, Palette.WRONG, run_time=0.7) for d, line, _ in snaps], lag_ratio=0.12))
            if reverts:
                self.play(*[Create(m, run_time=0.4) for m in reverts])
            if i == 0 and revert_lbl not in self.mobjects and any(c["kind"] == "revert" for col2 in cols for c in col2["cells"].values()):
                self.play(FadeIn(revert_lbl, run_time=0.4))
            for d, _, colour in ours:
                self.add(halo(d.get_center(), colour, radius=0.075))
                self.play(FadeIn(d, scale=0.4, run_time=0.35))
            if labels:
                self.play(*[FadeIn(t, run_time=0.3) for t in labels])
            self.wait(1.2)
        self.wait(10.0)

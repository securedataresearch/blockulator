"""Slide 9, "The cliff": where exp stops drifting and disappears.

A chart on a faint grid: one column per probe, exp(−40) through exp(−100)
in the order edges.json holds them; correct digits on the other axis.
Columns arrive left to right. In each, a dot per library at its
correct-digit height, colour by family, the libraries spread a little
within the column so coincident values stay visible. A cell whose result
was zero is a dot that snaps down to 0 and turns WRONG (red), labelled
"0"; a cell that reverted is a hollow red marker in a band under the
axis, labelled "revert". FP127 and FP19 draw last in every column, on
top, each under a halo. Then the margins: a glow along FP19's row with
its least digits on any probe ("71 digits on every probe"), and FP127's
last standing point, the last probe where it still had a digit, named.
A legend names the libraries drawn and, under them, those with no dot
and why: "no exp" (unsupported on every probe) and "rejects negative
inputs" (ParamOutOfRange on every probe: the representation is
unsigned). None of the talk's 17 is dropped silently. About 55 s.

Numbers from docs/benchmarks/edges.json: op "exp", the probes whose
single argument lies in [−100, −40] (.args, .truth, .cells[lib].digits /
.zero / .reverted / .reasonName / .unsupported); fp127lib is skipped as
a duplicate of fp127 and BlockulatorWad is not in the talk. Labels from
static/data/libraries.json.
"""

from __future__ import annotations

import textwrap

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

from vocab import DUPLICATES, Chart, DeckScene, GridLine, Palette, colour_of, edges, glow_line, halo, snap, talk_libs, words

OP = "exp"
ARG_LO, ARG_HI = -100, -40
SKIP = DUPLICATES
RANGE_REASON = "ParamOutOfRange"  # the argument does not fit the representation: nothing was called
REASONS = {"unsupported": "no exp", "range": "rejects negative inputs"}
WIDTH, HEIGHT = 10.2, 5.2
ORIGIN_XY = (-5.9, -2.3)
Y_STEP = 20
REVERT_BAND = -6.0  # digits axis position of the "revert" band, under 0
SPREAD = 0.1  # scene units between libraries within a column
LEGEND_X, LEGEND_TOP = 4.75, 2.55
CLOSE_Y = 3.5


def minus(arg: str) -> str:
    return arg.replace("-", "−")


def numbers() -> dict:
    op = edges(OP)
    lib = talk_libs()
    probes = [p for p in op["probes"] if len(p["args"]) == 1 and ARG_LO <= float(p["args"][0]) <= ARG_HI]
    assert probes, (OP, ARG_LO, ARG_HI)

    def out_of_range(c):
        return bool(c.get("reverted")) and str(c.get("reasonName", "")).startswith(RANGE_REASON)

    lids, absent = [], {}
    for lid in lib:
        if lid in SKIP:
            continue
        cells = [p["cells"][lid] for p in probes]
        if all(c.get("unsupported") for c in cells):
            absent[lid] = REASONS["unsupported"]
        elif all(c.get("unsupported") or out_of_range(c) for c in cells):
            absent[lid] = REASONS["range"]
        else:
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
    fp19 = [col["cells"]["fp19"] for col in columns]
    assert all(c["kind"] == "value" for c in fp19)
    standing = [col for col in columns if col["cells"]["fp127"]["kind"] == "value" and col["cells"]["fp127"]["digits"] >= 1]
    first_zero = next(col["arg"] for col in columns if any(c["kind"] == "zero" and lib[lid]["family"] == "wad" for lid, c in col["cells"].items()))
    return {
        "libs": [{"id": lid, "label": lib[lid]["label"], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours"))} for lid in lids],
        "absent": {lid: {"label": lib[lid]["label"], "reason": why} for lid, why in absent.items()},
        "columns": columns,
        "axisMax": int(-(-y_max // Y_STEP) * Y_STEP),
        "fp19_min": min(c["digits"] for c in fp19),
        "fp127_last": {"arg": standing[-1]["arg"], "digits": standing[-1]["cells"]["fp127"]["digits"]},
        "wad_first_zero": first_zero,
    }


def absent_text(absent: dict) -> str:
    by_reason: dict[str, list[str]] = {}
    for rec in absent.values():
        by_reason.setdefault(rec["reason"], []).append(rec["label"])
    lines = []
    for why, names in by_reason.items():
        lines += textwrap.wrap(f"{why}: {' · '.join(names)}", 23)
    return "\n".join(lines)


def fmt(d: float) -> str:
    return str(int(d)) if float(d).is_integer() else str(d)


class Cliff(DeckScene):
    def construct(self):
        n = numbers()
        cols, lids = n["columns"], [r["id"] for r in n["libs"]]
        y_max = n["axisMax"]
        self.wait(0.6)
        self.play(self.caption(f"docs/benchmarks/edges.json · {OP}"))

        chart = Chart((0, len(cols) - 1, 1), (0, y_max, Y_STEP), WIDTH, HEIGHT, origin=(*ORIGIN_XY, 0))
        for i, col in enumerate(cols):
            chart.x_label(i, f"exp({minus(col['arg'])})", use_markup=True, buff=0.55)
        for y in range(0, y_max + 1, Y_STEP):
            chart.y_label(y, str(y), mono=True)
        revert_lbl = words("revert", 18, Palette.WRONG).next_to(chart.c2p(0, REVERT_BAND), LEFT, buff=0.18)
        chart.y_title("correct digits")
        grid = chart.grid()
        self.play(Create(chart.x_axis, run_time=1.0), Create(chart.y_axis, run_time=1.0))
        self.play(FadeIn(chart.labels, run_time=0.6), FadeIn(chart.titles, run_time=0.6), FadeIn(grid, run_time=0.8))

        # legend, right of the plot: the libraries drawn, then those with no dot and why
        legend = VGroup()
        for r in n["libs"]:
            colour = colour_of(r)
            row = VGroup(chart.dot(0, 0, colour, radius=0.07), words(r["label"], 17, colour))
            row[1].next_to(row[0], RIGHT, buff=0.15)
            legend.add(row)
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.13).move_to([5.9, 0, 0]).align_to([LEGEND_X, 0, 0], LEFT).align_to([0, LEGEND_TOP, 0], UP)
        absent = words("no dot:\n" + absent_text(n["absent"]), 15, Palette.FAINT, line_spacing=0.6)
        absent.next_to(legend, DOWN, buff=0.32).align_to(legend, LEFT)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.05) for r in legend], lag_ratio=0.1, run_time=1.2))
        self.play(FadeIn(absent, run_time=0.6))
        self.wait(1.5)

        offsets = {lid: (k - (len(lids) - 1) / 2) * SPREAD for k, lid in enumerate(lids)}
        last_digits = {lid: None for lid in lids}
        hero_dots = {lid: {} for lid in lids if next(r for r in n["libs"] if r["id"] == lid)["ours"]}  # lid → {column: dot}
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
                    if fam["ours"]:
                        hero_dots[lid][i] = d
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

        # the margins: FP127's last standing point, then the king's row
        last = n["fp127_last"]
        i_last = next(i for i, col in enumerate(cols) if col["arg"] == last["arg"])
        d_last = hero_dots["fp127"][i_last]
        last_lbl = words(f"FP127 · {fmt(last['digits'])} digit{'' if last['digits'] == 1 else 's'} still at exp({minus(last['arg'])})", 16, Palette.EMERALD)
        last_lbl.next_to(d_last, UP, buff=0.5)
        self.play(FadeIn(last_lbl, shift=UP * 0.08, run_time=0.5))
        self.wait(2.0)
        fp19_dots = [hero_dots["fp19"][i] for i in range(len(cols))]
        row = [d.get_center() for d in fp19_dots]
        glow = glow_line(row, Palette.TEXT, width=16.0, opacity=0.22)
        self.add(glow)
        self.bring_to_front(*fp19_dots)
        row_lbl = words(f"FP19 · {fmt(n['fp19_min'])} digits on every probe", 20, Palette.TEXT).move_to([chart.c2p(len(cols) / 2 - 0.5, 0)[0], row[0][1] + 0.38, 0])
        self.play(Create(glow, run_time=1.4), FadeIn(row_lbl, shift=UP * 0.06, run_time=0.8))
        self.wait(2.0)

        close = words(
            f"the 18-decimal grid is zero from exp({minus(n['wad_first_zero'])}) · FP127 stands to exp({minus(last['arg'])}) · FP19: {fmt(n['fp19_min'])} digits on every probe",
            22,
            Palette.TEXT,
        ).move_to([0, CLOSE_Y, 0])
        self.play(FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.wait(10.0)

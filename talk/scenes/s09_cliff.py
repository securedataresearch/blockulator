"""Slide 13, "The cliff": where exp stops drifting and disappears.

The edit pass (talk/briefs/edit-pass.md, row 13): the chart, direct labels
(BL19, BL127's last digit, ABDK Quad, the 18-decimal row's zero), the
revert marks, and the key as one compact column (every one of the talk's
17 libraries in its colour, chrome in self.key, not counted by
vocab.text_census).

A chart on a faint grid: one column per probe, exp(−40) through exp(−100)
in the order edges.json holds them; correct digits on the other axis (its
unit named by BL19's label). Columns arrive left to right. In each, a dot
per library at its correct-digit height, colour by family, the libraries
spread a little within the column so coincident values stay visible. A
cell whose result was zero is a dot that snaps down to 0 and turns WRONG
(red); a cell that reverted is a hollow red marker in a band under the
axis. BL127 and BL19 draw last in every column, on top, each under a halo.
Then BL127's last standing point (the last probe where it still had a
digit, claim V28) is named, and a glow runs along BL19's row with its
least digits on any probe. The key names every library, marks the ones
with no dot, and says why in one line: "no exp" (unsupported on every
probe) and "rejects negative inputs" (ParamOutOfRange on every probe: the
representation is unsigned); it also reads the two red marks.

Three sections, one per click: the columns arrive (every value); the
zeros snap red and the reverts appear; BL127's last digit and BL19's row.

Numbers from docs/benchmarks/edges.json: op "exp", the probes whose
single argument lies in [−100, −40] (.args, .truth, .cells[lib].digits /
.zero / .reverted / .reasonName / .unsupported); bl127lib is skipped as
a duplicate of bl127 and BlockulatorWad is not in the talk. Labels from
static/data/libraries.json.
"""

from __future__ import annotations

from manim import (
    LEFT,
    RIGHT,
    UP,
    Circle,
    Create,
    FadeIn,
    LaggedStart,
    VGroup,
)
from vocab import (
    DUPLICATES,
    SIZE_BODY,
    SIZE_CAPTION,
    WAD_DECIMALS,
    Chart,
    DeckScene,
    GridLine,
    Palette,
    colour_of,
    edges,
    glow_line,
    halo,
    snap,
    talk_libs,
    words,
)

OP = "exp"
ARG_LO, ARG_HI = -100, -40
SKIP = DUPLICATES
RANGE_REASON = "ParamOutOfRange"  # the argument does not fit the representation: nothing was called
REASONS = {"unsupported": "no exp", "range": "rejects negative inputs"}
WIDTH, HEIGHT = 10.5, 5.1  # the plot, one column per probe; the key's column at its right
ORIGIN_XY = (-6.45, -2.3)
Y_STEP = 20
REVERT_BAND = -6.0  # digits axis position of the "revert" band, under 0
SPREAD = 0.1  # scene units between libraries within a column
KEY_RIGHT, KEY_TOP = 6.75, 2.9  # the key's column: right edge on the safe area, top under the right mark
KEY_PITCH = 0.25
FOOT_Y = -3.45  # the key's one "no dot" line, under the x labels, right-aligned with the column
LABEL_LIFT = 0.4  # a row's label above its dots

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


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
    bl19 = [col["cells"]["bl19"] for col in columns]
    assert all(c["kind"] == "value" for c in bl19)
    standing = [col for col in columns if col["cells"]["bl127"]["kind"] == "value" and col["cells"]["bl127"]["digits"] >= 1]
    first_zero = next(col["arg"] for col in columns if any(c["kind"] == "zero" and lib[lid]["family"] == "wad" for lid, c in col["cells"].items()))
    return {
        "libs": [{"id": lid, "label": lib[lid]["label"], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours"))} for lid in lids],
        "absent": {lid: {"label": lib[lid]["label"], "reason": why} for lid, why in absent.items()},
        "columns": columns,
        "axisMax": int(-(-y_max // Y_STEP) * Y_STEP),
        "y_ticks": list(range(0, int(-(-y_max // Y_STEP) * Y_STEP) + 1, Y_STEP)),
        "wad_decimals": WAD_DECIMALS,
        "bl19_min": min(c["digits"] for c in bl19),
        "bl127_last": {"arg": standing[-1]["arg"], "digits": standing[-1]["cells"]["bl127"]["digits"]},
        "wad_first_zero": first_zero,
    }


def reason_line(absent: dict) -> str:
    """The key's one line: why a library has no dot. The commonest reason
    stands alone; the others name their libraries."""
    by_reason: dict[str, list[str]] = {}
    for rec in absent.values():
        by_reason.setdefault(rec["reason"], []).append(rec["label"])
    common = max(by_reason, key=lambda why: len(by_reason[why]))
    rest = [f"{' · '.join(names)} {why}" for why, names in by_reason.items() if why != common]
    return " · ".join([f"no dot: {common}", *rest])


def fmt(d: float) -> str:
    return str(int(d)) if float(d).is_integer() else str(d)


class Cliff(DeckScene):
    SECTIONS = ("columns", "zeros", "bl19")

    def build_key(self, chart: Chart, n: dict) -> VGroup:
        """The key: one column at CAPTION size, every library of the talk in its
        colour (a dot for those drawn, none for those with no dot), the two red
        marks, then the one line that says why a library has no dot."""
        lib = talk_libs()
        drawn = {r["id"] for r in n["libs"]}
        fam = ["bl19", "bl127", "quad", "6464", "wad", "protocol"]
        ids = sorted([lid for lid in lib if lid not in SKIP], key=lambda lid: (fam.index(lib[lid]["family"]), list(lib).index(lid)))
        rows = VGroup()
        for lid in ids:
            colour = colour_of(lib[lid])
            mark = chart.dot(0, 0, colour, radius=0.055).set_opacity(1 if lid in drawn else 0)
            rows.add(VGroup(mark, words(lib[lid]["label"], SIZE_CAPTION, colour)))
        rows.add(VGroup(chart.dot(0, 0, Palette.WRONG, radius=0.055), words("zero", SIZE_CAPTION, Palette.WRONG)))
        rows.add(VGroup(Circle(radius=0.055, color=Palette.WRONG, stroke_width=2), words("revert", SIZE_CAPTION, Palette.WRONG)))
        for k, row in enumerate(rows):
            # on a common baseline: every name starts with a glyph that has no descender
            row[1].align_to([0, 0, 0], LEFT).shift(UP * (KEY_TOP - k * KEY_PITCH - row[1][0].get_bottom()[1]))
            row[0].move_to([row[1].get_left()[0] - 0.12 - row[0].width / 2, row[1][0].get_bottom()[1] + 0.07, 0])
        rows.align_to([KEY_RIGHT, 0, 0], RIGHT)
        why = words(reason_line(n["absent"]), SIZE_CAPTION, Palette.FAINT).move_to([0, FOOT_Y, 0]).align_to([KEY_RIGHT, 0, 0], RIGHT)
        return VGroup(rows, why)

    def construct(self):
        n = numbers()
        cols, lids = n["columns"], [r["id"] for r in n["libs"]]
        fam = {r["id"]: r for r in n["libs"]}
        y_max = n["axisMax"]
        self.section(0)
        # the chrome, on the first frame: the chart (axes, gridlines between the
        # columns, the probes' names) and the key
        chart = Chart((-0.5, len(cols) - 0.5, 1), (0, y_max, Y_STEP), WIDTH, HEIGHT, origin=(*ORIGIN_XY, 0))
        for i, col in enumerate(cols):
            chart.x_label(i, f"exp({minus(col['arg'])})", buff=0.62)
        chart.grid()
        self.key = self.build_key(chart, n)
        self.fix(chart, self.key)
        assert chart.c2p(len(cols) - 0.5, 0)[0] < self.key[0].get_left()[0] - 0.2  # the plot clears the key
        assert self.key[1].get_left()[0] > chart.c2p(-0.5, 0)[0] and self.key[1].get_top()[1] < min(t.get_bottom()[1] for t in chart.labels) - 0.1
        self.wait(0.8)

        offsets = {lid: (k - (len(lids) - 1) / 2) * SPREAD for k, lid in enumerate(lids)}
        hero_dots = {lid: {} for lid in lids if fam[lid]["ours"]}  # lid → {column: dot}
        rows: dict[str, list] = {lid: [] for lid in lids}  # every dot drawn, per library

        x_in = chart.c2p(-0.5, 0)[0] + 0.15  # the left edge of the labels inside the plot

        def x_of(i: int, lid: str) -> float:
            return chart.c2p(i, 0)[0] + offsets[lid]

        # ---- the columns arrive, left to right: every value, ours last with a halo
        for i, col in enumerate(cols):
            plain, ours = [], []
            for lid in lids:  # ours first in lids, so draw them last
                c = col["cells"][lid]
                if c["kind"] != "value":
                    continue
                colour = colour_of(fam[lid])
                d = chart.dot(i, c["digits"], colour, radius=0.075 if fam[lid]["ours"] else 0.065).set_x(x_of(i, lid))
                rows[lid].append(d)
                if fam[lid]["ours"]:
                    ours.append((d, colour))
                    hero_dots[lid][i] = d
                else:
                    plain.append(d)
            if plain:
                self.play(LaggedStart(*[FadeIn(d, scale=0.4) for d in reversed(plain)], lag_ratio=0.08, run_time=0.6))
            for d, colour in reversed(ours):
                self.add(halo(d.get_center(), colour, radius=0.075))
                self.play(FadeIn(d, scale=0.4, run_time=0.35))
            self.wait(0.3)
        # the binary128 float's row, named over its first dots
        quad_lbl = words("ABDK Quad", SIZE_BODY, colour_of(fam["quad"])).next_to(rows["quad"][0], UP, buff=LABEL_LIFT - 0.15).align_to([x_in, 0, 0], LEFT)
        self.play(FadeIn(quad_lbl, shift=UP * 0.06, run_time=0.5))

        # ---- the zeros snap down and turn red; the reverts appear in the band under the axis
        self.section(1, hold=1.0)
        last_digits = {lid: None for lid in lids}
        for i, col in enumerate(cols):
            snaps, reverts = [], []
            for lid in lids:
                c = col["cells"][lid]
                colour = colour_of(fam[lid])
                x = x_of(i, lid)
                if c["kind"] == "value":
                    last_digits[lid] = c["digits"]
                elif c["kind"] == "zero":
                    start = last_digits[lid] if last_digits[lid] else Y_STEP / 4
                    d = chart.dot(i, start, colour, radius=0.075 if fam[lid]["ours"] else 0.065).set_x(x)
                    line = GridLine((0, 1, 1), length=abs(chart.c2p(0, start)[1] - chart.c2p(0, 0)[1]), rotation=-1.5707963, tick_size=0)
                    line.move_to([x, (chart.c2p(0, start)[1] + chart.c2p(0, 0)[1]) / 2, 0])
                    snaps.append((d, line))
                    last_digits[lid] = 0
                elif c["kind"] == "revert":
                    reverts.append(Circle(radius=0.065, color=Palette.WRONG, stroke_width=2).move_to([x, chart.c2p(0, REVERT_BAND)[1], 0]))
            if snaps:
                for d, _ in snaps:
                    self.add(d)
                self.play(LaggedStart(*[snap(d, line, 1, Palette.WRONG, run_time=0.7) for d, line in snaps], lag_ratio=0.12))
            if reverts:
                self.play(*[Create(m, run_time=0.4) for m in reverts])
            if snaps or reverts:
                self.wait(0.4)
        # the 18-decimal row, named where it stops: over its last values and its first zeros
        i_zero = next(i for i, col in enumerate(cols) if col["arg"] == n["wad_first_zero"])
        wad_lbl = words(f"{n['wad_decimals']}-decimal:\nzero from exp({minus(n['wad_first_zero'])})", SIZE_BODY, Palette.GOLD, line_spacing=0.55)
        wad_lbl.move_to([0, (chart.c2p(0, 0)[1] + chart.c2p(0, cols[0]["cells"]["bl127"]["digits"])[1]) / 2, 0]).align_to([x_in, 0, 0], LEFT)
        assert wad_lbl.get_right()[0] > chart.c2p(i_zero, 0)[0]  # it reaches over the first zeros
        self.play(FadeIn(wad_lbl, shift=UP * 0.06, run_time=0.5))

        # ---- the margins: BL127's last standing point, then the king's row
        self.section(2, hold=1.0)
        last = n["bl127_last"]
        i_last = next(i for i, col in enumerate(cols) if col["arg"] == last["arg"])
        d_last = hero_dots["bl127"][i_last]
        last_lbl = words(f"BL127 · {fmt(last['digits'])} digit{'' if last['digits'] == 1 else 's'}\nstill at exp({minus(last['arg'])})", SIZE_BODY, Palette.EMERALD, line_spacing=0.55)
        last_lbl.next_to(d_last, UP + RIGHT, buff=0.12)
        self.play(FadeIn(last_lbl, shift=UP * 0.06, run_time=0.5))
        self.wait(1.0)
        bl19_dots = [hero_dots["bl19"][i] for i in range(len(cols))]
        row = [d.get_center() for d in bl19_dots]
        glow = glow_line(row, Palette.TEXT, width=16.0, opacity=0.22)
        self.add(glow)
        self.bring_to_front(*bl19_dots)
        row_lbl = words(f"BL19 · {fmt(n['bl19_min'])} digits", SIZE_BODY, Palette.TEXT).move_to([chart.c2p((len(cols) - 1) / 2, 0)[0], row[0][1] + LABEL_LIFT, 0])
        self.play(Create(glow, run_time=1.4), FadeIn(row_lbl, shift=UP * 0.06, run_time=0.8))
        self.close()

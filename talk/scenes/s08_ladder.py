"""Slide 12, "Measure it": correct digits against the number of steps, in
three scenarios on one chart.

The edit pass (talk/briefs/edit-pass.md, row 12): the chart, direct labels
at the line ends, the two margin brackets, and the key as one compact
column (every one of the talk's 17 libraries in its colour, chrome in
self.key, not counted by vocab.text_census).

A chart on a faint grid: N on a log axis (1 to 10,000 steps), correct
digits on the other; one line per library, a dot at every N where the
ladder measured it, colour by family (static/data/libraries.json). No
single scenario runs every library, so the chart MORPHS: it opens on
"compound" (daily compounding, one mul per step: Maker's rpow runs here),
the lines drawing in from the 18-decimal libraries up, with a dashed guide
for the trend (a digit per tenfold N, the 18-decimal line's own slope);
then BL127 and BL19, last and under a glow, and the margins at N = 10,000
bracketed over the best 18-decimal line, in digits; then every line slides
to "accrual-continuous" (Aave and Morpho draw in, Maker leaves) and to
"adaptive-rate" (FraxLend and Euler). The adaptive frame is the poster.
A line is named at its end when its name fits there (BL19, BL127,
ABDKMathQuad, the 18-decimal cluster as one label); the rest are named by
the key, whose last line says why a library has no line in a scenario.

Four sections, one per click: compound, blockulator, accrual, adaptive.

Numbers from docs/benchmarks/ladder.json: .ladder (the N), .ladderLog10,
.axisMax and, per scenario, .title, .summary[lib][N].digits.median (a bare
value in older files; both are read) and .ops[lib]; bl127lib is skipped as
a duplicate of bl127 and BlockulatorWad is not in the talk. Labels from
static/data/libraries.json.
"""

from __future__ import annotations

import itertools
import math

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    Create,
    DashedLine,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    Transform,
    VGroup,
    VMobject,
)
from vocab import (
    DUPLICATES,
    SIZE_BODY,
    SIZE_CAPTION,
    WAD_DECIMALS,
    Chart,
    DeckScene,
    Palette,
    colour_of,
    glow_line,
    halo,
    ladder,
    ladder_median,
    ladder_reason,
    talk_libs,
    thousands,
    words,
)

SCENARIOS = ("compound", "accrual-continuous", "adaptive-rate")
SKIP = DUPLICATES
GOLD = "wad"  # the family the margins are measured against
HEROES = ("bl127", "bl19")  # drawn last, in this order: the king last
NAMED = ("bl19", "bl127", "quad")  # named at their line's end in every scenario (with the 18-decimal cluster)
X_RANGE = (0, 4, 1)  # log10 N
Y_STEP = 20
ORIGIN_XY = (-5.75, -2.85)
WIDTH, HEIGHT = 4.75, 5.45  # the plot; its right side holds the brackets, the end labels and the key
BRACKET_DX = {"bl19": 0.22, "bl127": 0.44}  # each margin bracket's distance right of the last N
LABEL_DX = 0.64  # the end labels' left edge, right of the last N
LABEL_GAP = 0.44  # minimum spacing between end labels' centres, scene units (a BODY line is 0.33 tall)
KEY_RIGHT, KEY_TOP = 6.75, 2.75  # the key's column: right edge on the safe area, top under the right mark
KEY_PITCH = 0.27
GUIDE_DROP = 5.0  # digits below the 18-decimal line the slope guide is drawn

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def scenario_numbers(sid: str, lib: dict[str, dict], N: list[int]) -> dict:
    d = ladder(sid)
    summary = d["scenario"]["summary"]
    series, absent = {}, {}
    for lid in lib:
        if lid in SKIP:
            continue
        cells = summary.get(lid, {})
        vals = [ladder_median(cells.get(str(n))) for n in N]
        if any(v is None for v in vals):
            absent[lid] = ladder_reason(d["scenario"], lid)
        else:
            series[lid] = vals
    # identical series of one family share one label
    groups: list[dict] = []
    for lid, vals in series.items():
        for g in groups:
            if g["digits"] == vals and g["family"] == lib[lid]["family"]:
                g["ids"].append(lid)
                g["labels"].append(lib[lid]["label"])
                break
        else:
            groups.append({"ids": [lid], "labels": [lib[lid]["label"]], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours")), "digits": vals})
    end = {lid: vals[-1] for lid, vals in series.items()}
    gold = [v for lid, v in end.items() if lib[lid]["family"] == GOLD]
    gold_end = max(gold)
    margins = {lid: round(end[lid] - gold_end, 1) for lid in HEROES}
    return {
        "id": sid,
        "title": d["scenario"]["title"],
        "series": series,
        "groups": groups,
        "end": end,
        "absent": absent,
        "gold_end": gold_end,
        "gold_low": min(gold),
        "margins": margins,
        "margin_digits": {lid: math.floor(m) for lid, m in margins.items()},
    }


def numbers() -> dict:
    lib = talk_libs()
    d = ladder(SCENARIOS[0])
    N = d["N"]
    log10 = [d["log10"][str(n)] for n in N]
    scenarios = [scenario_numbers(sid, lib, N) for sid in SCENARIOS]
    for s in scenarios:
        assert set(s["series"]) | set(s["absent"]) == set(lib) - set(SKIP), s["id"]
        # BL19 tops every scenario; BL127 beats every 18-decimal line (ABDKMathQuad, a
        # binary128 float, sits above BL127 in adaptive-rate: the chart shows it)
        assert s["end"]["bl19"] == max(s["end"].values()) and s["margins"]["bl127"] > 0, s["id"]
    # the guide's slope in the first scenario: the 18-decimal line's digits lost per decade of N
    gold0 = next(g for g in scenarios[0]["groups"] if g["family"] == GOLD)["digits"]
    slope = round((gold0[0] - gold0[-1]) / (float(log10[-1]) - float(log10[0])))
    return {"N": N, "log10": log10, "axisMax": d["axisMax"], "y_ends": [0, int(d["axisMax"])], "wad_decimals": WAD_DECIMALS, "slope": slope, "scenarios": scenarios}


def cluster_label(s: dict) -> str:
    """The 18-decimal lines, one label: their end value, or the range when
    they do not coincide."""
    lo, hi = s["gold_low"], s["gold_end"]
    return f"{WAD_DECIMALS}-decimal · {hi}" if lo == hi else f"{WAD_DECIMALS}-decimal · {lo}–{hi}"


def key_order(lib: dict) -> list[str]:
    """Every library of the talk, ours first (the king first), then by family
    as libraries.json orders them."""
    fam = ["bl19", "bl127", "quad", "6464", GOLD, "protocol"]
    ids = [lid for lid in lib if lid not in SKIP]
    return sorted(ids, key=lambda lid: (fam.index(lib[lid]["family"]), list(lib).index(lid)))


def reason_line(scenarios: list[dict]) -> str:
    """The key's one line: why a library has no line in a scenario."""
    reasons = sorted({why for s in scenarios for why in s["absent"].values()})
    return f"no line: {' · '.join(reasons)}"


def solve(items: list[tuple[float, object]], gap: float) -> None:
    """Labels at their desired y, pushed apart upward to at least `gap`
    between centres (the lines end closer than a label's height)."""
    items = sorted(items, key=lambda it: it[0])
    y_prev = None
    for y, m in items:
        y = y if y_prev is None else max(y, y_prev + gap)
        m.set_y(y)
        y_prev = y


class Ladder(DeckScene):
    SECTIONS = ("compound", "blockulator", "accrual", "adaptive")

    def build(self, chart: Chart, xs: list[float], lib: dict, s: dict) -> dict:
        """Every mobject one scenario puts on the chart, keyed by library so
        a morph can pair them with the previous scenario's: per library a
        line, its dots, a glow and a halo (ours) and an end label (the named
        ones); the cluster's label; the brackets and their labels; the title."""
        out = {"libs": {}, "brackets": {}}
        x_end = chart.c2p(xs[-1], 0)[0]
        for lid, vals in s["series"].items():
            rec = lib[lid]
            ours = bool(rec.get("ours"))
            colour = colour_of(rec)
            pts = [chart.c2p(x, float(v)) for x, v in zip(xs, vals)]
            out["libs"][lid] = {
                "id": lid,
                "ours": ours,
                "gold": rec["family"] == GOLD,
                "end": vals[-1],
                "colour": colour,
                "line": VMobject(color=colour, stroke_width=5.0 if ours else 2.5).set_points_as_corners(pts),
                "dots": VGroup(*[chart.dot(x, float(v), colour, radius=0.07 if ours else 0.055) for x, v in zip(xs, vals)]),
                "glow": glow_line(pts, colour) if ours else None,
                "halo": halo(pts[-1], colour, radius=0.07) if ours else None,
                "label": words(f"{rec['label']} · {vals[-1]}", SIZE_BODY, colour) if lid in NAMED else None,
            }
        out["cluster"] = words(cluster_label(s), SIZE_BODY, Palette.GOLD)
        # the margins at N = 10,000, bracketed up from the best 18-decimal end: BL19's
        # inside, BL127's outside it; each label in the end labels' column
        for lid in HEROES:
            colour = colour_of(lib[lid])
            x = x_end + BRACKET_DX[lid]
            lo, hi = chart.c2p(xs[-1], s["gold_end"]), chart.c2p(xs[-1], s["end"][lid])
            lo[0] = hi[0] = x
            bar = VGroup(Line(lo, hi, color=colour, stroke_width=2), Line(lo + LEFT * 0.07, lo + RIGHT * 0.07, color=colour, stroke_width=2), Line(hi + LEFT * 0.07, hi + RIGHT * 0.07, color=colour, stroke_width=2))
            out["brackets"][lid] = {"bar": bar, "label": words(f"+{s['margin_digits'][lid]} digits", SIZE_BODY, colour), "span": (lo[1], hi[1])}
        # the end labels' column: each at its line's end, pushed apart; then each bracket's
        # label in the widest free gap beside its own bracket (BL127's first, the shorter)
        place = [(chart.c2p(xs[-1], it["end"])[1], it["label"]) for it in out["libs"].values() if it["label"] is not None]
        place.append((chart.c2p(xs[-1], s["gold_end"])[1], out["cluster"]))
        solve(place, LABEL_GAP)
        taken = [m.get_y() for _, m in place]
        for lid in HEROES:
            b = out["brackets"][lid]
            lo, hi = b["span"]
            edges = sorted([lo, hi] + [y for y in taken if lo < y < hi])
            a, z = max(itertools.pairwise(edges), key=lambda g: g[1] - g[0])
            assert z - a >= 2 * LABEL_GAP, (s["id"], lid, z - a)
            b["label"].set_y((a + z) / 2)
            taken.append(b["label"].get_y())
            place.append((b["label"].get_y(), b["label"]))
        for _, m in place:
            m.align_to([x_end + LABEL_DX, 0, 0], LEFT)
        assert max(m.get_right()[0] for _, m in place) < self.key.get_left()[0] - 0.2, s["id"]  # the column clears the key
        out["title"] = self.title(s["title"], SIZE_BODY, Palette.BODY)
        return out

    def build_key(self, chart: Chart, lib: dict, scenarios: list[dict]) -> VGroup:
        """The key: one column at CAPTION size, every library of the talk in its
        colour, then the one line that says why a library has no line."""
        rows = VGroup()
        for lid in key_order(lib):
            colour = colour_of(lib[lid])
            row = VGroup(chart.dot(0, 0, colour, radius=0.055), words(lib[lid]["label"], SIZE_CAPTION, colour))
            rows.add(row)
        for k, row in enumerate(rows):
            # on a common baseline: every name starts with a glyph that has no descender
            row[1].align_to([0, 0, 0], LEFT).shift(UP * (KEY_TOP - k * KEY_PITCH - row[1][0].get_bottom()[1]))
            row[0].move_to([row[1].get_left()[0] - 0.12 - row[0].width / 2, row[1][0].get_bottom()[1] + 0.07, 0])
        rows.align_to([KEY_RIGHT, 0, 0], RIGHT)
        why = words(reason_line(scenarios), SIZE_CAPTION, Palette.FAINT).next_to(rows, DOWN, buff=0.22).align_to([KEY_RIGHT, 0, 0], RIGHT)
        return VGroup(rows, why)

    def draw_order(self, items) -> list[dict]:
        """18-decimal first, then up the chart by end value, ours last."""
        return sorted(items, key=lambda it: (it["ours"], not it["gold"], it["end"], HEROES.index(it["id"]) if it["ours"] else 0))

    def heroes_on_top(self, cur: dict):
        for lid in HEROES:
            it = cur["libs"][lid]
            self.bring_to_front(it["glow"], it["halo"], it["line"], it["dots"])
        self.bring_to_front(*[cur["brackets"][lid]["bar"] for lid in HEROES])

    def draw_in(self, it: dict, run_time: float = 1.6):
        self.play(Create(it["line"], run_time=run_time), LaggedStart(*[FadeIn(d, scale=0.5) for d in it["dots"]], lag_ratio=0.1, run_time=run_time))

    def construct(self):
        n = numbers()
        lib = talk_libs()
        xs = [float(v) for v in n["log10"]]
        y_max = int(n["axisMax"])
        scenarios = n["scenarios"]
        self.section(0)
        # the chrome, on the first frame: the chart (axes, gridlines, the end ticks'
        # labels, the axis titles) and the key; the title names the current scenario
        chart = Chart(X_RANGE, (0, y_max, Y_STEP), WIDTH, HEIGHT, origin=(*ORIGIN_XY, 0))
        chart.x_label(X_RANGE[0], thousands(n["N"][0]))
        chart.x_label(X_RANGE[1], f"{thousands(n['N'][-1])} steps")
        for y in n["y_ends"]:
            chart.y_label(y, str(y), mono=True)
        chart.y_title("correct digits", gap=0.7)
        chart.grid()
        self.key = self.build_key(chart, lib, scenarios)
        self.fix(chart, self.key)
        s = scenarios[0]
        cur = self.build(chart, xs, lib, s)
        self.add(cur["title"])
        self.wait(1.3)

        # ---- the first scenario draws in: 18-decimal first, up the chart, ours later
        order = self.draw_order(cur["libs"].values())
        gold_items = [it for it in order if it["gold"]]
        self.play(*[Create(it["line"], run_time=2.2) for it in gold_items], *[LaggedStart(*[FadeIn(d, scale=0.5) for d in it["dots"]], lag_ratio=0.1, run_time=2.2) for it in gold_items])
        self.play(FadeIn(cur["cluster"], shift=RIGHT * 0.05, run_time=0.5))
        self.wait(0.8)
        # the others; one is named at its end while it fits there (Maker, until the heroes come)
        protocol = [it for it in order if lib[it["id"]]["family"] == "protocol"]
        visiting = None
        for it in order:
            if it["gold"] or it["ours"]:
                continue
            self.draw_in(it)
            if it["label"] is not None:
                self.play(FadeIn(it["label"], shift=RIGHT * 0.05, run_time=0.5))
            elif it in protocol and visiting is None:
                visiting = words(f"{lib[it['id']]['label']} · {it['end']}", SIZE_BODY, it["colour"]).align_to(cur["cluster"], LEFT).set_y(chart.c2p(xs[-1], it["end"])[1])
                self.play(FadeIn(visiting, shift=RIGHT * 0.05, run_time=0.5))
            self.wait(0.6)

        # the trend the data shows, for every line: a digit lost per tenfold N, as a
        # guide parallel to the 18-decimal line, set below it
        y0 = float(s["series"][gold_items[0]["id"]][0]) - GUIDE_DROP
        guide = DashedLine(chart.c2p(xs[0], y0), chart.c2p(xs[-1], y0 - n["slope"] * (xs[-1] - xs[0])), color=Palette.FAINT, stroke_width=2, dash_length=0.1)
        guide_lbl = words(f"{n['slope']} digit per decade", SIZE_BODY, Palette.MUTED).next_to(guide, DOWN, buff=0.12)
        self.play(Create(guide, run_time=1.2))
        self.play(FadeIn(guide_lbl, run_time=0.5))

        # ---- Blockulator's lines, last and on top, under a glow; then the margins
        self.section(1, hold=1.5)
        self.play(*[FadeOut(m) for m in (guide, guide_lbl, visiting) if m is not None], run_time=0.6)
        for it in order:
            if not it["ours"]:
                continue
            self.play(Create(it["glow"], run_time=2.0), Create(it["line"], run_time=2.0), LaggedStart(*[FadeIn(d, scale=0.5) for d in it["dots"]], lag_ratio=0.1, run_time=2.0))
            self.play(FadeIn(it["halo"], run_time=0.5), FadeIn(it["label"], shift=RIGHT * 0.05, run_time=0.5))
            self.wait(0.8)
        for lid in HEROES:  # BL127 then BL19, the king last
            br = cur["brackets"][lid]
            self.play(Create(br["bar"], run_time=0.6))
            self.play(FadeIn(br["label"], shift=RIGHT * 0.06, run_time=0.4))
            self.wait(0.6)
        self.heroes_on_top(cur)

        # ---- the morphs: every line slides to its next value; leavers fade, arrivals draw
        for k, s in enumerate(scenarios[1:], start=2):
            self.section(k, hold=2.0)
            nxt = self.build(chart, xs, lib, s)
            slide, leave, arrive = [], [], []
            for lid, it in cur["libs"].items():
                if lid in nxt["libs"]:
                    new = nxt["libs"][lid]
                    slide += [Transform(it["line"], new["line"]), Transform(it["dots"], new["dots"])]
                    if it["ours"]:
                        slide += [Transform(it["glow"], new["glow"]), Transform(it["halo"], new["halo"])]
                    if it["label"] is not None:
                        slide += [FadeOut(it["label"]), FadeIn(new["label"])]
                    # the old mobjects now look like the new ones; keep drawing those
                    for part in ("line", "dots", "glow", "halo"):
                        new[part] = it[part]
                else:
                    leave += [FadeOut(it["line"]), FadeOut(it["dots"])]
            arrive = [it for lid, it in nxt["libs"].items() if lid not in cur["libs"]]
            for lid in HEROES:
                old, new = cur["brackets"][lid], nxt["brackets"][lid]
                slide += [Transform(old["bar"], new["bar"]), FadeOut(old["label"]), FadeIn(new["label"])]
                new["bar"] = old["bar"]
            slide += [FadeOut(cur["cluster"]), FadeIn(nxt["cluster"]), FadeOut(cur["title"]), FadeIn(nxt["title"])]
            self.play(*leave, run_time=0.8)
            self.play(AnimationGroup(*slide, run_time=2.2))
            for it in self.draw_order(arrive):
                self.draw_in(it)
                self.wait(0.6)
            self.heroes_on_top(nxt)
            cur = nxt
        self.close()

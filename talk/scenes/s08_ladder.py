"""Slide 8, "Measure it": correct digits against the number of steps, in
three scenarios on one chart.

A chart on a faint grid: N on a log axis (1 … 10,000), correct digits on
the other; one line per library, a dot at every N where the ladder
measured it, colour by family (static/data/libraries.json). No single
scenario runs every library, so the chart MORPHS: it opens on "compound"
(daily compounding, one mul per step: Maker's rpow runs here), the lines
drawing in from the 18-decimal libraries up to FP127 and FP19, last and
under a glow; then every line slides to its "accrual-continuous" values
(the accrual Aave and Morpho run), Maker fading out and Aave and Morpho
drawing in; then to "adaptive-rate" (the rate FraxLend and Euler run).
At every stop the margin is bracketed at N = 10,000: FP19 and FP127 over
the best 18-decimal line, in digits. A legend names the libraries that
have no line in the scenario and why ("not offered": the scenario's
.ops[lib] is ["unsupported"]); none of the talk's 17 is dropped silently.
A slope glyph in the first scenario names the trend: about one digit per
decade of steps, for every library (ours included). The closing line
says what V14 says: the Blockulator lines start higher and keep the gap,
with the margins in digits.

Five sections, one per click: the compound lines (the 18-decimal
libraries and the rest); the Blockulator lines with their margins; the
morph to accrual-continuous; the morph to adaptive-rate; the closing
lines (claims V13, V14).

Numbers from docs/benchmarks/ladder.json: .ladder (the N), .ladderLog10,
.axisMax and, per scenario, .summary[lib][N].digits.median (a bare value
in older files; both are read) and .ops[lib]; fp127lib is skipped as a
duplicate of fp127 and BlockulatorWad is not in the talk. Libraries whose
lines coincide (the 18-decimal ones) share one label listing their names.
Labels from static/data/libraries.json.
"""

from __future__ import annotations

import math
import textwrap

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
    Transform,
    VGroup,
    VMobject,
)

from vocab import DUPLICATES, SIZE_CAPTION, WAD_DECIMALS, Chart, DeckScene, Palette, colour_of, glow_line, halo, ladder, ladder_median, ladder_reason, measure_up, talk_libs, thousands, words

SCENARIOS = ("compound", "accrual-continuous", "adaptive-rate")
# what the panel says each one is; the first keeps the ladder's own title
SUBTITLES = {"accrual-continuous": "the accrual Aave and Morpho run", "adaptive-rate": "the rate FraxLend and Euler run"}
SKIP = DUPLICATES
GOLD = "wad"  # the family the margins are measured against
HEROES = ("fp127", "fp19")  # drawn last, in this order: the king last
X_RANGE = (0, 4, 1)  # log10 N
WIDTH, HEIGHT = 7.8, 5.0
ORIGIN_XY = (-5.6, -2.3)
LABEL_GAP = 0.3  # minimum spacing between end labels, scene units
GUIDE_DROP = 5.0  # digits below the 18-decimal line the slope guide is drawn
BRACKET_X = {"fp19": 5.2, "fp127": 5.5}  # where each margin bracket stands
CLUSTER_XY = (0.35, 1.1)  # the 18-decimal names: chart x in log10 N, scene y
CLUSTER_WIDTH = 60  # characters per line of the 18-decimal names
TITLE_Y, LEGEND_Y = 3.5, 3.1  # the top strip: the scenario, then who has no line
CLOSE_XY = (6.9, -3.0)  # the closing lines, right-aligned, bottom right, under the x labels
CLOSE_PITCH = 0.33
Y_STEP = 20
CLOSE_FIRST = "Blockulator's lines start higher and keep the gap"  # V14

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
    gold_end = max(v for lid, v in end.items() if lib[lid]["family"] == GOLD)
    margins = {lid: round(end[lid] - gold_end, 1) for lid in HEROES}
    return {
        "id": sid,
        "title": d["scenario"]["title"],
        "series": series,
        "groups": groups,
        "end": end,
        "absent": absent,
        "gold_end": gold_end,
        "margins": margins,
        "margin_digits": {lid: math.floor(m) for lid, m in margins.items()},
    }


def numbers() -> dict:
    lib = talk_libs()
    d = ladder(SCENARIOS[0])
    N = d["N"]
    scenarios = [scenario_numbers(sid, lib, N) for sid in SCENARIOS]
    for s in scenarios:
        assert set(s["series"]) | set(s["absent"]) == set(lib) - set(SKIP), s["id"]
        # FP19 tops every scenario; FP127 beats every 18-decimal line (ABDKMathQuad, a
        # binary128 float, sits above FP127 in adaptive-rate: the chart shows it)
        assert s["end"]["fp19"] == max(s["end"].values()) and s["margins"]["fp127"] > 0, s["id"]
    return {"N": N, "log10": [d["log10"][str(n)] for n in N], "axisMax": d["axisMax"], "y_ticks": list(range(0, int(d["axisMax"]) + 1, Y_STEP)), "wad_decimals": WAD_DECIMALS, "scenarios": scenarios}


def cluster_text(groups: list[dict]) -> str:
    """The coinciding 18-decimal lines, named: each group's names and its
    end value, a group kept on one line where it fits."""
    lines, cur = [], f"{WAD_DECIMALS}-decimal — "
    for g in groups:
        part = f"{' · '.join(g['labels'])}: {g['digits'][-1]}"
        if cur.endswith("— "):
            cur += part
        elif len(cur) + 3 + len(part) <= CLUSTER_WIDTH:
            cur += "   " + part
        else:
            lines.append(cur)
            cur = part
    lines.append(cur)
    return "\n".join(line for chunk in lines for line in textwrap.wrap(chunk, CLUSTER_WIDTH))


def legend_text(lib: dict, absent: dict[str, str]) -> str:
    """The libraries with no line, by reason: "not offered: Aave · Morpho"."""
    by_reason: dict[str, list[str]] = {}
    for lid, why in absent.items():
        by_reason.setdefault(why, []).append(lib[lid]["label"])
    return "   ".join(f"{why}: {' · '.join(names)}" for why, names in by_reason.items())


class Ladder(DeckScene):
    SECTIONS = ("compound", "blockulator", "accrual", "adaptive", "closing")

    def build(self, chart: Chart, xs: list[float], lib: dict, s: dict) -> dict:
        """Every mobject one scenario puts on the chart, keyed by library so
        a morph can pair them with the previous scenario's: per library a
        line, its dots, a glow and a halo (ours) and an end label (not the
        18-decimal ones, which share the cluster text); the brackets; the
        title and the legend."""
        out = {"libs": {}, "brackets": {}}
        for lid, vals in s["series"].items():
            rec = lib[lid]
            ours = bool(rec.get("ours"))
            colour = colour_of(rec)
            pts = [chart.c2p(x, float(v)) for x, v in zip(xs, vals)]
            item = {
                "id": lid,
                "ours": ours,
                "gold": rec["family"] == GOLD,
                "end": vals[-1],
                "colour": colour,
                "pts": pts,
                "line": VMobject(color=colour, stroke_width=5.0 if ours else 2.5).set_points_as_corners(pts),
                "dots": VGroup(*[chart.dot(x, float(v), colour, radius=0.07 if ours else 0.06) for x, v in zip(xs, vals)]),
                "glow": glow_line(pts, colour) if ours else None,
                "halo": halo(pts[-1], colour, radius=0.07) if ours else None,
                "label": None if rec["family"] == GOLD else words(f"{rec['label']} · {vals[-1]}", 20 if ours else 17, colour).next_to(pts[-1], RIGHT, buff=0.18),
            }
            out["libs"][lid] = item
        gold = [g for g in s["groups"] if g["family"] == GOLD]
        out["cluster"] = words(cluster_text(gold), 17, Palette.GOLD, line_spacing=0.6)
        out["cluster"].move_to([0, CLUSTER_XY[1], 0]).align_to(chart.c2p(CLUSTER_XY[0], 0), LEFT)
        # end labels apart (lines can end less than a label apart)
        labels = sorted([it["label"] for it in out["libs"].values() if it["label"] is not None], key=lambda t: t.get_y())
        for a, b in zip(labels, labels[1:]):
            if b.get_y() - a.get_y() < LABEL_GAP:
                b.shift(UP * (LABEL_GAP - (b.get_y() - a.get_y())))
        # the margins at N = 10,000, bracketed from the best 18-decimal end
        for lid in HEROES:
            lo = chart.c2p(xs[-1], s["gold_end"])
            hi = chart.c2p(xs[-1], s["end"][lid])
            lo[0] = hi[0] = BRACKET_X[lid]
            out["brackets"][lid] = measure_up(lo, hi, f"+{s['margin_digits'][lid]} digits", colour_of(lib[lid]), size=20)
        title = s["title"] + (f" · {SUBTITLES[s['id']]}" if s["id"] in SUBTITLES else "")
        out["title"] = words(title, 21, Palette.BODY).move_to([0, TITLE_Y, 0]).align_to([-6.3, 0, 0], LEFT)
        out["legend"] = words(legend_text(lib, s["absent"]), 16, Palette.FAINT).move_to([0, LEGEND_Y, 0]).align_to([-6.3, 0, 0], LEFT)
        return out

    def draw_order(self, items) -> list[dict]:
        """18-decimal first, then up the chart by end value, ours last."""
        return sorted(items, key=lambda it: (it["ours"], not it["gold"], it["end"], HEROES.index(it["id"]) if it["ours"] else 0))

    def heroes_on_top(self, cur: dict):
        for lid in HEROES:
            it = cur["libs"][lid]
            self.bring_to_front(it["glow"], it["halo"], it["line"], it["dots"])
        self.bring_to_front(*[cur["brackets"][lid] for lid in HEROES])

    def construct(self):
        n = numbers()
        lib = talk_libs()
        xs = [float(v) for v in n["log10"]]
        y_max = int(n["axisMax"])
        scenarios = n["scenarios"]
        self.section(0)
        self.wait(0.3)
        self.play(self.caption(f"docs/benchmarks/ladder.json · scenarios[{scenarios[0]['id']}]"))

        chart = Chart(X_RANGE, (0, y_max, Y_STEP), WIDTH, HEIGHT, origin=(*ORIGIN_XY, 0))
        for k in range(X_RANGE[0], X_RANGE[1] + 1):
            chart.x_label(k, thousands(10**k))
        for y in n["y_ticks"]:
            chart.y_label(y, str(y), mono=True)
        chart.x_title("N steps")
        chart.y_title("correct digits")
        grid = chart.grid()
        self.play(Create(chart.x_axis, run_time=1.0), Create(chart.y_axis, run_time=1.0))
        self.play(FadeIn(chart.labels, run_time=0.6), FadeIn(chart.titles, run_time=0.6), FadeIn(grid, run_time=0.8))
        self.wait(1.0)

        # ---- the first scenario draws in: 18-decimal first, up the chart, ours last on top
        s = scenarios[0]
        cur = self.build(chart, xs, lib, s)
        self.play(FadeIn(cur["title"], shift=RIGHT * 0.08, run_time=0.6), FadeIn(cur["legend"], run_time=0.6))
        self.wait(1.0)
        order = self.draw_order(cur["libs"].values())
        gold_items = [it for it in order if it["gold"]]
        self.play(*[Create(it["line"], run_time=2.2) for it in gold_items], *[LaggedStart(*[FadeIn(d, scale=0.5) for d in it["dots"]], lag_ratio=0.1, run_time=2.2) for it in gold_items])
        self.play(FadeIn(cur["cluster"], run_time=0.6))
        self.wait(1.5)
        for it in order:
            if it["gold"] or it["ours"]:
                continue
            self.play(Create(it["line"], run_time=1.6), LaggedStart(*[FadeIn(d, scale=0.5) for d in it["dots"]], lag_ratio=0.1, run_time=1.6))
            self.play(FadeIn(it["label"], shift=RIGHT * 0.05, run_time=0.5))
            self.wait(0.8)

        # the trend the data shows, for every library: a digit lost per tenfold in N,
        # as a guide parallel to the 18-decimal line, set below it
        y0 = float(s["series"][gold_items[0]["id"]][0]) - GUIDE_DROP
        guide = DashedLine(chart.c2p(xs[0], y0), chart.c2p(xs[-1], y0 - (xs[-1] - xs[0])), color=Palette.FAINT, stroke_width=1.5, dash_length=0.08)
        guide_lbl = words("one digit per decade, every line", 17, Palette.FAINT).next_to(guide.get_end(), DOWN + LEFT, buff=0.08).shift(RIGHT * 0.9)
        self.play(Create(guide, run_time=1.2))
        self.play(FadeIn(guide_lbl, run_time=0.5))

        # ---- Blockulator's lines, last and on top, under a glow; then the margins
        self.section(1, hold=1.5)
        for it in order:
            if not it["ours"]:
                continue
            self.play(Create(it["glow"], run_time=2.0), Create(it["line"], run_time=2.0), LaggedStart(*[FadeIn(d, scale=0.5) for d in it["dots"]], lag_ratio=0.1, run_time=2.0))
            self.play(FadeIn(it["halo"], run_time=0.5), FadeIn(it["label"], shift=RIGHT * 0.05, run_time=0.5))
            self.wait(1.0)
        # the margins, FP127 then FP19, the king last
        for lid in HEROES:
            br = cur["brackets"][lid]
            self.play(Create(br[0], run_time=0.5), FadeIn(br[1], run_time=0.5))
            self.play(FadeIn(br[2], shift=RIGHT * 0.06, run_time=0.4))
            self.wait(0.8)
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
                    for k in ("line", "dots", "glow", "halo"):
                        new[k] = it[k]
                else:
                    leave += [FadeOut(it["line"]), FadeOut(it["dots"])]
                    if it["label"] is not None:
                        leave.append(FadeOut(it["label"]))
            for lid, it in nxt["libs"].items():
                if lid not in cur["libs"]:
                    arrive.append(it)
            for lid in HEROES:
                slide.append(Transform(cur["brackets"][lid], nxt["brackets"][lid]))
                nxt["brackets"][lid] = cur["brackets"][lid]
            slide += [FadeOut(cur["cluster"]), FadeIn(nxt["cluster"]), FadeOut(cur["title"]), FadeIn(nxt["title"]), FadeOut(cur["legend"]), FadeIn(nxt["legend"])]
            if guide is not None:
                leave += [FadeOut(guide), FadeOut(guide_lbl)]
                guide = None
            self.play(self.caption(f"docs/benchmarks/ladder.json · scenarios[{s['id']}]"), *leave, run_time=0.8)
            self.play(AnimationGroup(*slide, run_time=2.2))
            for it in self.draw_order(arrive):
                self.play(Create(it["line"], run_time=1.6), LaggedStart(*[FadeIn(d, scale=0.5) for d in it["dots"]], lag_ratio=0.1, run_time=1.6))
                self.play(FadeIn(it["label"], shift=RIGHT * 0.05, run_time=0.4))
                self.wait(0.8)
            self.heroes_on_top(nxt)
            cur = nxt

        # the close: the gap, in the chart's units, across the three (V14: higher, and kept)
        self.section(len(self.SECTIONS) - 1, hold=2.5)
        f19 = [s["margin_digits"]["fp19"] for s in scenarios]
        f127 = [s["margin_digits"]["fp127"] for s in scenarios]
        close = VGroup(
            words(CLOSE_FIRST, SIZE_CAPTION, Palette.TEXT),
            words(f"at N = {thousands(n['N'][-1])}: FP19 +{min(f19)} to +{max(f19)} digits,", 19, Palette.BODY),
            words(f"FP127 +{min(f127)} to +{max(f127)}, over the best {n['wad_decimals']}-decimal line", 19, Palette.BODY),
        )
        for k, line in enumerate(close):
            line.move_to([0, CLOSE_XY[1] - k * CLOSE_PITCH, 0]).align_to([CLOSE_XY[0], 0, 0], RIGHT)
        self.play(FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.close()

"""Slide 11, "Two failures, one decision": five incidents, sorted into two bands.

Two bands, each a panel with its heading. Band 1, "rounded too early, or
too often": Resupply (one floor, too early), Bunni v2 and Balancer V2 (a
floor repeated); carry the exact value and round once, and the attack
stops. Band 2, "rounded at a unit": Thetanuts and Balancer V1; no precision
helps there, only the direction decides who pays. Each band's names drop
into it in their deck hue (vocab.PROTOCOL_COLOUR, the hue each replay
uses), then its one emerald line arrives with a tick and the panel's edge
turns emerald. Last, everything but the title fades out and the thesis
holds on its panel: inside a calculation, precision shrinks error; at a
unit, direction decides who pays.

The replays (slides 6 to 10) carry each mechanism and its numbers; this
slide carries only the sorting. Names from talk/scenes/data/incidents.json,
oldest first. Four sections: the bands; the first band filled and resolved;
the second; the box. Claims C1–C5, V27 (research_notes/talk/verify-C.md).
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Create,
    FadeIn,
    FadeOut,
    RoundedRectangle,
    VGroup,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    PROTOCOL_COLOUR,
    SIZE_BODY,
    DeckScene,
    Palette,
    check_mark,
    glow_bar,
    incidents,
    words,
)

ROWS = ("resupply", "bunni", "balancer-v2", "thetanuts", "balancer-v1")
BANDS = {"resupply": 1, "bunni": 1, "balancer-v2": 1, "thetanuts": 2, "balancer-v1": 2}
TITLE = "Two failures, one decision"
BAND_TITLE = {1: "rounded too early, or too often", 2: "rounded at a unit"}
RESOLVE = {1: "carry the exact value, round once", 2: "only the direction decides who pays"}
BOX_1 = "Inside a calculation, precision shrinks error."
BOX_2 = "At a unit, direction decides who pays."

LITERALS: dict[str, str] = {}  # the digits on the slide are the protocols' names, values of numbers()

# geometry (scene units: the 5% safe area is ±6.4 by ±3.6)
X_EDGE = 6.4
PANEL_TOP = {1: 2.75, 2: -0.4}
PANEL_H = 2.8
PAD = 0.3  # a panel's edge to its heading
BOX_SIZE = 60  # the thesis, alone on the frame
NAME = 48  # a protocol's name in its band
NAME_GAP = 1.1  # name to name
NAME_Y = 1.3  # a name's centre under its panel's top
RESOLVE_Y = 2.2  # the band's line under its panel's top


def numbers() -> dict:
    inc = incidents()["incidents"]
    assert len(inc) == len(ROWS), len(inc)
    rows = []
    for rid, i in zip(ROWS, inc):
        assert i["protocol"].lower().replace(" ", "-").startswith(rid), (rid, i["protocol"])
        rows.append({"id": rid, "protocol": i["protocol"], "band": BANDS[rid]})
    return {"rows": rows}


class Two(DeckScene):
    SECTIONS = ("bands", "inside", "unit", "box")

    def panel(self, band: int):
        top = PANEL_TOP[band]
        rect = RoundedRectangle(width=2 * X_EDGE, height=PANEL_H, corner_radius=0.16, stroke_color=Palette.RULE, stroke_width=1.5, fill_color=Palette.RULE, fill_opacity=0.06)
        rect.move_to([0, top - PANEL_H / 2, 0])
        head = words(BAND_TITLE[band], SIZE_BODY, Palette.MUTED)
        head.move_to([-X_EDGE + PAD + head.width / 2, top - PAD - head.height / 2, 0])
        return rect, head

    def names(self, band: int, rows: list[dict]) -> VGroup:
        g = VGroup(*[words(r["protocol"], NAME, PROTOCOL_COLOUR[r["id"]]) for r in rows if r["band"] == band])
        g.arrange(RIGHT, buff=NAME_GAP).move_to([0, PANEL_TOP[band] - NAME_Y, 0])
        return g

    def land(self, name):
        """A name drops into its band and settles."""
        self.play(FadeIn(name, shift=DOWN * 0.45, scale=1.25, run_time=0.6, rate_func=ease_out_cubic))
        self.wait(0.5)

    def resolve(self, band: int, rect):
        line = words(RESOLVE[band], SIZE_BODY, Palette.CORRECT)
        tick = check_mark(Palette.CORRECT, size=0.3)
        row = VGroup(line, tick).arrange(RIGHT, buff=0.3).move_to([0, PANEL_TOP[band] - RESOLVE_Y, 0])
        tick.set_y(line.get_y())
        self.play(FadeIn(line, shift=RIGHT * 0.1, run_time=0.6), rect.animate(run_time=0.8).set_stroke(Palette.CORRECT, width=2.5))
        self.play(Create(tick, run_time=0.4))
        return row

    def construct(self):
        n = numbers()
        rows = n["rows"]
        self.section(0)
        title = self.title(TITLE, SIZE_BODY, Palette.TEXT)
        self.fix(title)
        panels = {b: self.panel(b) for b in (1, 2)}
        self.wait(0.3)
        for b in (1, 2):
            rect, head = panels[b]
            self.play(Create(rect, run_time=0.6), FadeIn(head, shift=RIGHT * 0.1, run_time=0.6))

        # band 1: too early, too often; then carry the exact value and round once
        story = VGroup(*[m for b in (1, 2) for m in panels[b]])
        for b, sec in ((1, 1), (2, 2)):
            self.section(sec, hold=1.5)
            names = self.names(b, rows)
            for name in names:
                self.land(name)
            story.add(names, self.resolve(b, panels[b][0]))

        # the box: everything but the title leaves; the thesis holds on its panel
        self.section(3, hold=2.0)
        # each sentence on two lines, broken at its comma: one line each does not fit the safe area at HERO
        box = VGroup(*[VGroup(*[words(part, BOX_SIZE, Palette.TEXT) for part in s.replace(", ", ",|").split("|")]).arrange(DOWN, buff=0.22) for s in (BOX_1, BOX_2)]).arrange(DOWN, buff=0.5)
        box.move_to([0, -0.35, 0])
        assert box.width <= 2 * X_EDGE - 0.6, box.width  # the panel inside the safe area
        bar = glow_bar(box, Palette.CORRECT, pad=0.3, opacity=0.14)
        self.play(FadeOut(story, run_time=0.8))
        self.play(FadeIn(bar, run_time=0.5))
        self.play(FadeIn(box[0], shift=UP * 0.08, run_time=0.6))
        self.wait(0.4)
        self.play(FadeIn(box[1], shift=UP * 0.08, run_time=0.6))
        self.close()

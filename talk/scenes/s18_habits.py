"""Slide 18, "Decide. Measure. Declare.": three habits, ticked, and what a
declaration looks like on a contract.

The title (essay §10) and the three words, in their hues (GOLD,
SAPPHIRE, VIOLET: ROW_COLOUR["s18"]) at HERO beside their boxes, are
chrome; the boxes draw in section 0. Then one habit per click: its box
ticks in EMERALD (the speaker says the habit; the slide shows the tick).
On the last click, after the tick, a contract outline draws and the
declaration block slides into it: "declares", tagged "example" in AMBER
(the op names are BL127Lib's, chosen as examples: toFixed18Down down,
divUp up, exp nearest), and "reference:" with BL127 v9's address, the
one number on the slide, from release() (V15). Nothing says any protocol
does this today.

Four sections: title, decide, measure, declare (the block lands in
declare). The habits' sub-lines are the script, in the notes.
"""

from __future__ import annotations

from manim import DOWN, LEFT, RIGHT, UP, Create, FadeIn, LaggedStart, RoundedRectangle, VGroup

from vocab import (
    ROW_COLOUR,
    SIZE_BODY,
    SIZE_HERO,
    Palette,
    TextScene,
    digits,
    release,
    words,
)

HUES = ROW_COLOUR["s18"]
COMPONENT = "BL127"
OPS = (("toFixed18Down", "down"), ("divUp", "up"), ("exp", "nearest"))  # examples: BL127Lib's names (check.py finds each in the source)

TITLE = "Rounding is a design decision, like access control."
HABITS = ("Decide", "Measure", "Declare")
DECLARES = "declares"
EXAMPLE = "example"
CONTRACT = "contract"
ROUNDING = "rounding: " + " · ".join(f"{op} {way}" for op, way in OPS)  # the one-line form
INDENT = " " * len("rounding: ")
ROUNDING_LINES = "\n".join([f"rounding: {OPS[0][0]} {OPS[0][1]}", *[f"{INDENT}{op} {way}" for op, way in OPS[1:]]])  # one op a line in the block
REFERENCE = "reference:"

LITERALS = {
    TITLE: "essay §10",
    **{h: "essay §10" for h in HABITS},
    DECLARES: "essay §10",
    EXAMPLE: "brief",
    CONTRACT: "brief",
    REFERENCE: "V15",
}

COL_X = (-4.3, 0.0, 4.3)  # the three habits' centres
Y_HABITS = 1.95
BOX_SIDE = 0.6
Y_BLOCK_TOP = 1.0
PAD = 0.35  # the outline's inner margin


def numbers() -> dict:
    comp = release()["components"][COMPONENT]
    assert len(comp["address"]) == 42 and comp["address"].startswith("0x"), comp["address"]
    return {"address": comp["address"], "version": comp["version"], "ops": [op for op, _ in OPS], "rounding": ROUNDING}


class Habits(TextScene):
    SECTIONS = ("title", "decide", "measure", "declare")

    def construct(self):
        n = numbers()
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        boxes = []
        for label, x in zip(HABITS, COL_X):
            cb = self.checkbox(label, SIZE_HERO, HUES[label], side=BOX_SIDE, gap=0.3)
            cb.move_to([x, Y_HABITS, 0])
            boxes.append(cb)
            self.fix(cb.label)
        self.wait(0.3)
        self.play(LaggedStart(*[Create(cb.box, run_time=0.5) for cb in boxes], lag_ratio=0.35))

        # 1–3 · each habit: its box ticks
        for i in range(len(HABITS)):
            self.section(1 + i, hold=1.0)
            self.play(boxes[i].tick(run_time=0.5))

        # the last click goes on: the contract outline, and the declaration slides in and attaches to it
        self.wait(0.8)
        contract = words(CONTRACT, SIZE_BODY, Palette.MUTED)
        header = words(DECLARES, SIZE_BODY, HUES["Declare"])
        tag = words(EXAMPLE, SIZE_BODY, HUES["example"])
        head = VGroup(header, tag).arrange(RIGHT, buff=0.35, aligned_edge=UP)  # both have ascenders; "example" has a descender
        rounding = digits(ROUNDING_LINES, SIZE_BODY, Palette.BODY, line_spacing=0.6)
        ref = VGroup(digits(REFERENCE, SIZE_BODY, Palette.BODY), words(n["version"], SIZE_BODY, Palette.EMERALD)).arrange(RIGHT, buff=0.3)
        addr = digits(n["address"], SIZE_BODY, Palette.EMERALD)
        block = VGroup(head, rounding, ref, addr).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        inner = VGroup(contract, block).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        outline = RoundedRectangle(width=inner.width + 2 * PAD, height=inner.height + 2 * PAD, corner_radius=0.16, color=Palette.RULE, stroke_width=2, fill_color=Palette.BG, fill_opacity=1.0)
        outline.move_to([0, Y_BLOCK_TOP - outline.height / 2, 0])
        inner.move_to(outline)
        assert outline.width <= 12.8 and outline.get_bottom()[1] >= -3.6, (outline.width, outline.get_bottom()[1])
        assert outline.get_top()[1] < min(cb.get_bottom()[1] for cb in boxes) - 0.4
        self.play(Create(outline, run_time=0.7), FadeIn(contract, run_time=0.5))
        start = block.copy().shift(RIGHT * 2.5).set_opacity(0)
        self.add(start)
        self.play(start.animate.move_to(block).set_opacity(1), run_time=0.9)
        self.remove(start)
        self.add(block)
        self.close(hold=3.0)

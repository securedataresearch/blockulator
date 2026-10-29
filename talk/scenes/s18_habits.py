"""Slide 18, "Decide. Measure. Declare.": three habits, ticked, and what a
declaration looks like on a contract.

The title (essay §10) and the three checkbox labels, in their hues (GOLD,
SAPPHIRE, VIOLET: ROW_COLOUR["s18"]), are chrome; the boxes draw in
section 0. Then one habit per click: its sub-line types in at BODY,
MUTED, wrapped to its column, and the box ticks in EMERALD (the hero: the
three ticks). Last a contract outline (a RoundedRectangle, right) and
the declaration block that slides in and attaches to it: "declares",
tagged "example" in AMBER (the op names are FP127Lib's, chosen as
examples: toFixed18Down down, divUp up, exp nearest), and "reference:"
with FP127 v9's address, the one number on the slide, from release()
(V15). Nothing says any protocol does this today.

Five sections: title, decide, measure, declare, block. The address is
drawn at CAPTION in mono (42 characters are 6.95 units there; at BODY
they are 11.1, wider than the block's column).
"""

from __future__ import annotations

from manim import DOWN, LEFT, RIGHT, UP, Create, FadeIn, LaggedStart, RoundedRectangle, VGroup

from vocab import (
    ROW_COLOUR,
    SIZE_BODY,
    SIZE_CAPTION,
    Palette,
    TextScene,
    digits,
    release,
    words,
    wrap,
)

HUES = ROW_COLOUR["s18"]
COMPONENT = "FP127"
OPS = (("toFixed18Down", "down"), ("divUp", "up"), ("exp", "nearest"))  # examples: FP127Lib's names (check.py finds each in the source)

TITLE = "Rounding is a design decision, like access control."
HABITS = (
    ("Decide", "for each rounding, which way, and why"),
    ("Measure", "know a calculation's digits the way you know its gas, and check it against a reference"),
    ("Declare", "write down what each operation guarantees, and test or prove it"),
)
DECLARES = "declares"
EXAMPLE = "example"
CONTRACT = "contract"
ROUNDING = "rounding: " + " · ".join(f"{op} {way}" for op, way in OPS)  # the one-line form (8.8 units at CAPTION: drawn as three lines)
ROUNDING_LINES = f"rounding: {OPS[0][0]} {OPS[0][1]} · {OPS[1][0]} {OPS[1][1]}\n          {OPS[2][0]} {OPS[2][1]}"  # two lines in the block
REFERENCE = "reference:"

WRAP = 19  # characters per sub-line in a column

LITERALS = {
    TITLE: "essay §10",
    **{h: "essay §10" for h, _ in HABITS},
    **{wrap(line, WRAP): "essay §10" for _, line in HABITS},  # drawn wrapped to the column
    DECLARES: "essay §10",
    EXAMPLE: "brief",
    CONTRACT: "brief",
    REFERENCE: "V15",
}

COL_X = (-4.2, 0.0, 4.2)
COL_W = 4.1
Y_LABEL = 2.5
LINE_SPACING = 0.45  # the sub-lines' leading (manim's extra factor)
X_BLOCK_LEFT, X_BLOCK_RIGHT = -1.4, 6.4
Y_BLOCK_TOP, Y_BLOCK_BOTTOM = -1.0, -3.45


def numbers() -> dict:
    comp = release()["components"][COMPONENT]
    assert len(comp["address"]) == 42 and comp["address"].startswith("0x"), comp["address"]
    return {"address": comp["address"], "version": comp["version"], "ops": [op for op, _ in OPS], "rounding": ROUNDING}


class Habits(TextScene):
    SECTIONS = ("title", "decide", "measure", "declare", "block")

    def construct(self):
        n = numbers()
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        boxes = []
        for (label, _), x in zip(HABITS, COL_X):
            cb = self.checkbox(label, SIZE_BODY, HUES[label])
            cb.move_to([x - COL_W / 2 + cb.width / 2, Y_LABEL, 0])
            boxes.append(cb)
            self.fix(cb.label)
        self.wait(0.3)
        self.play(LaggedStart(*[Create(cb.box, run_time=0.5) for cb in boxes], lag_ratio=0.35))

        # 1–3 · each habit: its line types in under the label, the box ticks
        for i, ((label, line), x) in enumerate(zip(HABITS, COL_X)):
            self.section(1 + i, hold=1.0)
            text = wrap(line, WRAP)
            sub = self.typed(text, SIZE_BODY, Palette.MUTED, place=lambda t, x=x, cb=boxes[i]: t.move_to([x - COL_W / 2 + t.width / 2, cb.get_bottom()[1] - 0.22 - t.height / 2, 0]), line_spacing=LINE_SPACING)
            assert sub.width <= COL_W and sub.get_bottom()[1] > Y_BLOCK_TOP + 0.1, (label, sub.width, sub.get_bottom()[1])
            self.play(boxes[i].tick())

        # 4 · the contract outline on the right; the declaration slides in and attaches to it
        self.section(4, hold=1.0)
        outline = RoundedRectangle(width=X_BLOCK_RIGHT - X_BLOCK_LEFT, height=Y_BLOCK_TOP - Y_BLOCK_BOTTOM, corner_radius=0.16, color=Palette.RULE, stroke_width=2, fill_color=Palette.BG, fill_opacity=1.0)
        outline.move_to([(X_BLOCK_LEFT + X_BLOCK_RIGHT) / 2, (Y_BLOCK_TOP + Y_BLOCK_BOTTOM) / 2, 0])
        contract = words(CONTRACT, SIZE_CAPTION, Palette.FAINT).next_to(outline.get_corner(UP + LEFT), DOWN + RIGHT, buff=0.18)
        self.play(Create(outline, run_time=0.7), FadeIn(contract, run_time=0.5))
        header = words(DECLARES, SIZE_BODY, HUES["Declare"])
        tag = words(EXAMPLE, SIZE_CAPTION, HUES["example"])
        head = VGroup(header, tag).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        rounding = digits(ROUNDING_LINES, SIZE_CAPTION, Palette.BODY, line_spacing=0.5)
        ref = VGroup(digits(REFERENCE, SIZE_CAPTION, Palette.BODY), words(n["version"], SIZE_CAPTION, Palette.EMERALD)).arrange(RIGHT, buff=0.25)
        addr = digits(n["address"], SIZE_CAPTION, Palette.EMERALD)
        block = VGroup(head, rounding, ref, addr).arrange(DOWN, buff=0.13, aligned_edge=LEFT)
        inner_w = X_BLOCK_RIGHT - X_BLOCK_LEFT - 0.7
        assert block.width <= inner_w, (block.width, inner_w)
        block.next_to(contract, DOWN, buff=0.08, aligned_edge=LEFT)
        assert block.get_bottom()[1] >= Y_BLOCK_BOTTOM + 0.12, block.get_bottom()[1]
        start = block.copy().shift(RIGHT * 2.5).set_opacity(0)
        self.add(start)
        self.play(start.animate.move_to(block).set_opacity(1), run_time=0.9)
        self.remove(start)
        self.add(block)
        self.close(hold=3.0)

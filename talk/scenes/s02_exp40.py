"""Slide 2, "What is e^40?": one exact answer, three good ones, and ours.

Six rows of monospace digits, aligned on the decimal point, each typed in
left to right: the exact value (docs/benchmarks/edges.json, op exp,
probe args ["40"], .truth), then Solady, Balancer and PRBMath SD (the
probe's .cells[lib].value), then Blockulator's two, FP19 and FP127 (the
same cells). The three are 18-decimal fixed point, so they are counted
in DECIMALS: as each row completes, its first digit that departs from the
exact row turns WRONG (red), the digits after it dim, and the row is
labelled with how many digits after the point match the exact row
("3 of 18 decimals"; 0 when the integer part differs, since then no
decimal is right). numbers() also carries each row's correct
significant digits, floor(−log10(|value − truth| / truth)), the measure
edges.json reports as .digits, so the ledger keeps both counts. The
exact row is labelled with what the 18-decimal word holds of it. Then
the reveal: the FP19 and FP127 rows, larger, on a glowing panel, drawn
last. FP127 matches every decimal and more: its correct decimals are its
cell's .digits less the integer part's digits (a floor), and the label
says how many beyond 18. FP19 matches every decimal with the cell's
.digits significant digits. Labels come from static/data/libraries.json;
no row says why a library's digits end where they do (a documented
precision is not a defect). About 75 s.
"""

from __future__ import annotations

from manim import (
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    FadeIn,
    Indicate,
    Transform,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    DeckScene,
    Palette,
    colour_of,
    correct_decimals,
    correct_digits,
    correctly_rounded_18,
    digits,
    first_wrong_index,
    glow_bar,
    libs,
    matching_decimals,
    matching_digits,
    probe,
    words,
)

OP, ARG = "exp", "40"
LIBS = ("solady", "balancer", "prb")  # the three answers the talk names
OURS = ("fp19", "fp127")  # Blockulator's, from the same probe
WORD_DECIMALS = 18

X_LEFT = -6.15  # digit strings and row labels start here
X_RIGHT = 6.15  # the right-hand labels end here
Y_TOP = 3.45
PITCH = 1.04  # row to row
HERO_DROP = 0.12  # the reveal rows sit a little lower, clear of the row above
LABEL_DROP = 0.38  # label line to digit line
MONO = 32
MONO_OURS = 35  # the reveal rows are the biggest on the slide
SANS = 23
SANS_OURS = 25


def numbers() -> dict:
    p = probe(OP, ARG)
    truth = p["truth"]
    lib = libs()
    integer_part = truth.partition(".")[0]
    word_digits = len(integer_part) + WORD_DECIMALS
    rows = []
    for lid in LIBS:
        value = p["cells"][lid]["value"]
        rows.append(
            {
                "id": lid,
                "label": lib[lid]["label"],
                "value": value,
                "decimals": matching_decimals(value, truth),
                "matching": matching_digits(value, truth),
                "digits": correct_digits(value, truth),
                "first_wrong": first_wrong_index(value, truth),
            }
        )
    ours = []
    for lid in OURS:
        value = p["cells"][lid]["value"]
        cell_digits = int(p["cells"][lid]["digits"])
        m = matching_digits(value, truth)
        dec = correct_decimals(cell_digits, truth)
        assert m >= word_digits and dec >= WORD_DECIMALS and lib[lid].get("ours"), (lid, m, dec)
        ours.append({"id": lid, "label": lib[lid]["label"], "value": value, "matching": m, "digits": cell_digits, "decimals": dec, "beyond": dec - WORD_DECIMALS})
    return {
        "truth": truth,
        "word_digits": word_digits,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": correctly_rounded_18(truth),
    }


def right_label_text(r: dict) -> str:
    """The reveal rows' labels: FP127 (fixed point) counts decimals beyond
    the word's 18; FP19 (a float) counts its significant digits."""
    if r["id"] == "fp127":
        return f"every decimal — and {r['beyond']} more"
    return f"every decimal · {r['digits']} significant digits"


class Exp40(DeckScene):
    def row_y(self, i: int) -> float:
        return Y_TOP - i * PITCH - HERO_DROP * max(0, i - len(LIBS))

    def place_row(self, i: int, label: str, label_colour: str, value: str, digit_colour: str = Palette.TEXT, mono: float = MONO, sans: float = SANS, point_x: float | None = None):
        """A row: its name above, its digits below. With point_x the digits
        are placed so their decimal point sits on that x (the bigger reveal
        rows stay aligned on the point with the rows above) and the name
        starts where the digits do."""
        y = self.row_y(i)
        lbl = words(label, sans, label_colour)
        txt = digits(value, mono, digit_colour)
        if point_x is None:
            txt.move_to([X_LEFT + txt.width / 2, y - LABEL_DROP, 0])
        else:
            k = value.index(".")
            txt.move_to([0, y - LABEL_DROP, 0]).shift(RIGHT * (point_x - txt[k].get_x()))
        lbl.move_to([txt.get_left()[0] + lbl.width / 2, y, 0])
        return lbl, txt

    def right_label(self, i: int, text: str, colour: str, size: float = SANS):
        t = words(text, size, colour)
        t.move_to([X_RIGHT - t.width / 2, self.row_y(i), 0])
        return t

    def type_row(self, lbl, txt, per_char=0.065):
        self.play(FadeIn(lbl, shift=RIGHT * 0.1, run_time=0.4))
        self.play(AddTextLetterByLetter(txt, time_per_char=per_char))
        self.wait(0.3)

    def mark_wrong(self, txt, k: int, after=Palette.FAINT):
        """Light the first wrong digit and dim everything after it."""
        glyph = txt[k]
        lit = glyph.copy().set_color(Palette.WRONG).scale(1.35)
        self.play(
            Transform(glyph, lit, run_time=0.25, rate_func=ease_out_cubic),
            txt[k + 1 :].animate.set_color(after),
        )
        self.play(Transform(glyph, glyph.copy().scale(1 / 1.35), run_time=0.25))

    def construct(self):
        n = numbers()
        truth, rows = n["truth"], n["rows"]
        word = n["word_digits"] + 1  # characters, the point included
        point = len(truth.partition(".")[0])  # index of the point in every row
        self.wait(0.6)
        self.play(self.caption("docs/benchmarks/edges.json · exp(40)"))

        # the exact value: all the digits the probe keeps, then an ellipsis
        e_lbl, e_txt = self.place_row(0, "exact", Palette.EXACT, truth + "…")
        self.type_row(e_lbl, e_txt, per_char=0.06)
        e_right = self.right_label(0, f"{WORD_DECIMALS} decimals in an {WORD_DECIMALS}-decimal word", Palette.FAINT)
        self.play(e_txt[word:].animate.set_color(Palette.FAINT), FadeIn(e_right, run_time=0.5))
        self.wait(4.5)
        point_x = e_txt[point].get_x()

        # three answers, counted in decimals: the word promises 18
        lib = libs()
        for i, r in enumerate(rows, start=1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(i, r["label"], colour, r["value"])
            self.type_row(lbl, txt)
            self.mark_wrong(txt, r["first_wrong"])
            right = self.right_label(i, f"{r['decimals']} of {WORD_DECIMALS} decimals", Palette.MUTED)
            self.play(FadeIn(right, run_time=0.4))
            self.wait(5.5)

        # the reveal: ours, bigger, on a glowing panel, every decimal and beyond
        for j, r in enumerate(n["ours"], start=len(rows) + 1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(j, r["label"], colour, r["value"][:word] + "…", colour, mono=MONO_OURS, sans=SANS_OURS, point_x=point_x)
            txt[word:].set_color(Palette.FAINT)
            panel = glow_bar(txt, colour, pad=0.15, opacity=0.11)
            panel.set_fill(opacity=0)
            self.add(panel)
            self.play(FadeIn(lbl, shift=RIGHT * 0.1, run_time=0.4), panel.animate.set_fill(opacity=0.11))
            self.play(AddTextLetterByLetter(txt, time_per_char=0.05))
            self.play(Indicate(txt[:word], color=colour, scale_factor=1.03, run_time=0.6))
            right = self.right_label(j, right_label_text(r), colour, size=SANS_OURS)
            self.play(FadeIn(right, shift=LEFT * 0.08, run_time=0.4))
            self.wait(2.5)

        close = words("three good answers, none the closest · Blockulator: every decimal", 27, Palette.BODY)
        close.move_to([0, self.row_y(len(rows) + len(n["ours"])) - LABEL_DROP - 0.66, 0])  # under the last panel, above the caption
        self.play(FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.wait(12.0)

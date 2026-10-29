"""Slide 2, "What is e^40?": one exact answer, three good ones, and ours.

Six rows of monospace digits, aligned on the decimal point, each typed in
left to right: the exact value (docs/benchmarks/edges.json, op exp,
probe args ["40"], .truth), then Solady, Balancer and PRBMath SD (the
probe's .cells[lib].value), then Blockulator's two, FP19 and FP127 (the
same cells). As each library row completes its first digit that departs
from the exact row turns WRONG (red), the digits after it dim, and the
row is labelled with how many of its leading digits match the exact row,
the point ignored ("20 of 36 digits"; 36 = integer digits + 18, computed).
numbers() also carries each row's correct significant digits,
floor(−log10(|value − truth| / truth)), the measure edges.json reports as
.digits, so the ledger keeps both counts. The exact row is labelled with
how many of its digits an 18-decimal word can hold. The FP19 and FP127
rows match the exact row in every one of those digits: they type in
CORRECT (emerald) on a soft panel, labelled "every digit" with the cell's
.digits. Labels come from static/data/libraries.json; no row says why a
library's digits end where they do (a documented precision is not a
defect). About 75 s.
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

from vocab import DeckScene, Palette, colour_of, correct_digits, correctly_rounded_18, digits, first_wrong_index, glow_bar, libs, matching_digits, probe, words

OP, ARG = "exp", "40"
LIBS = ("solady", "balancer", "prb")  # the three answers the talk names
OURS = ("fp19", "fp127")  # Blockulator's, from the same probe
WORD_DECIMALS = 18

X_LEFT = -6.15  # digit strings and row labels start here
X_RIGHT = 6.15  # the right-hand labels end here
Y_TOP = 3.45
PITCH = 1.04  # row to row
LABEL_DROP = 0.38  # label line to digit line
MONO = 32
SANS = 23


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
                "matching": matching_digits(value, truth),
                "digits": correct_digits(value, truth),
                "first_wrong": first_wrong_index(value, truth),
            }
        )
    ours = []
    for lid in OURS:
        value = p["cells"][lid]["value"]
        m = matching_digits(value, truth)
        assert m >= word_digits and lib[lid].get("ours"), (lid, m)
        ours.append({"id": lid, "label": lib[lid]["label"], "value": value, "matching": m, "digits": int(p["cells"][lid]["digits"])})
    return {
        "truth": truth,
        "word_digits": word_digits,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": correctly_rounded_18(truth),
    }


class Exp40(DeckScene):
    def row_y(self, i: int) -> float:
        return Y_TOP - i * PITCH

    def place_row(self, i: int, label: str, label_colour: str, value: str, digit_colour: str = Palette.TEXT):
        y = self.row_y(i)
        lbl = words(label, SANS, label_colour)
        lbl.move_to([X_LEFT + lbl.width / 2, y, 0])
        txt = digits(value, MONO, digit_colour)
        txt.move_to([X_LEFT + txt.width / 2, y - LABEL_DROP, 0])
        return lbl, txt

    def right_label(self, i: int, text: str, colour: str):
        t = words(text, SANS, colour)
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
        self.wait(0.6)
        self.play(self.caption("docs/benchmarks/edges.json · exp(40)"))

        # the exact value: all the digits the probe keeps, then an ellipsis
        e_lbl, e_txt = self.place_row(0, "exact", Palette.EXACT, truth + "…")
        self.type_row(e_lbl, e_txt, per_char=0.06)
        e_right = self.right_label(0, f"{n['word_digits']} digits in an {WORD_DECIMALS}-decimal word", Palette.FAINT)
        self.play(e_txt[word:].animate.set_color(Palette.FAINT), FadeIn(e_right, run_time=0.5))
        self.wait(4.5)

        # three answers
        lib = libs()
        for i, r in enumerate(rows, start=1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(i, r["label"], colour, r["value"])
            self.type_row(lbl, txt)
            self.mark_wrong(txt, r["first_wrong"])
            right = self.right_label(i, f"{r['matching']} of {n['word_digits']} digits", Palette.MUTED)
            self.play(FadeIn(right, run_time=0.4))
            self.wait(5.5)

        # ours: every digit the word holds, on a panel
        for j, r in enumerate(n["ours"], start=len(rows) + 1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(j, r["label"], colour, r["value"][:word] + "…", colour)
            txt[word:].set_color(Palette.FAINT)
            panel = glow_bar(txt, colour)
            panel.set_fill(opacity=0)
            self.add(panel)
            self.play(FadeIn(lbl, shift=RIGHT * 0.1, run_time=0.4), panel.animate.set_fill(opacity=0.09))
            self.play(AddTextLetterByLetter(txt, time_per_char=0.05))
            self.play(Indicate(txt[:word], color=colour, scale_factor=1.03, run_time=0.6))
            right = self.right_label(j, f"every digit · {r['digits']} correct digits", colour)
            self.play(FadeIn(right, run_time=0.4))
            self.wait(2.5)

        close = words("three good answers, none the closest · two with every digit", 27, Palette.BODY)
        close.move_to([0, self.row_y(len(rows) + len(n["ours"]) + 1) - 0.05, 0])
        self.play(FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.wait(12.0)

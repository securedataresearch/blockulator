"""Slide 2, "What is e^40?": one exact answer, three good ones, and the closest.

Five rows of monospace digits, aligned on the decimal point, each typed in
left to right: the exact value (docs/benchmarks/edges.json, op exp,
probe args ["40"], .truth), then Solady, Balancer and PRBMath SD (the
probe's .cells[lib].value), then the correctly rounded 18-decimal value
(vocab.correctly_rounded_18 of the truth). As each library row completes
its first digit that departs from the exact row turns WRONG (red), the
digits after it dim, and the row is labelled with its correct significant
digits, floor(−log10(|value − truth| / truth)), computed here from the
JSON (edges.json reports the same measure as .digits). The exact row is
labelled with how many of its digits an 18-decimal word can hold; the
correctly rounded row is CORRECT (emerald) throughout. Labels come from
static/data/libraries.json. About 70 s.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    FadeIn,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import DeckScene, Palette, colour_of, correct_digits, correctly_rounded_18, digits, first_wrong_index, libs, markup, probe, words

OP, ARG = "exp", "40"
LIBS = ("solady", "balancer", "prb")  # the three answers the talk names
WORD_DECIMALS = 18

X_LEFT = -6.15  # digit strings and row labels start here
X_RIGHT = 6.15  # the right-hand labels end here
Y_TOP = 3.35
PITCH = 1.1  # row to row
LABEL_DROP = 0.4  # label line to digit line
NOTE_GAP = 0.4  # extra room under the row that carries the footnote
NOTE_ROW = LIBS.index("prb") + 1
MONO = 34
SANS = 24


def numbers() -> dict:
    p = probe(OP, ARG)
    truth = p["truth"]
    lib = libs()
    rows = []
    for lid in LIBS:
        value = p["cells"][lid]["value"]
        rows.append({"id": lid, "label": lib[lid]["label"], "value": value, "digits": correct_digits(value, truth), "first_wrong": first_wrong_index(value, truth)})
    integer_part = truth.partition(".")[0]
    return {
        "truth": truth,
        "word_digits": len(integer_part) + WORD_DECIMALS,
        "rows": rows,
        "correctly_rounded": correctly_rounded_18(truth),
    }




class Exp40(DeckScene):
    def row_y(self, i: int) -> float:
        return Y_TOP - i * PITCH - (NOTE_GAP if i > NOTE_ROW else 0.0)

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
        truth, rows, cr = n["truth"], n["rows"], n["correctly_rounded"]
        self.wait(0.6)
        self.play(self.caption("docs/benchmarks/edges.json · exp(40)"))

        # the exact value: all the digits the probe keeps, then an ellipsis
        e_lbl, e_txt = self.place_row(0, "exact", Palette.EXACT, truth + "…")
        self.type_row(e_lbl, e_txt, per_char=0.06)
        word = n["word_digits"] + 1  # characters, the point included
        e_right = self.right_label(0, f"{n['word_digits']} digits in an {WORD_DECIMALS}-decimal word", Palette.FAINT)
        self.play(e_txt[word:].animate.set_color(Palette.FAINT), FadeIn(e_right, run_time=0.5))
        self.wait(4.5)

        # three answers
        lib = libs()
        lib_rows = []
        for i, r in enumerate(rows, start=1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(i, r["label"], colour, r["value"])
            self.type_row(lbl, txt)
            self.mark_wrong(txt, r["first_wrong"])
            right = self.right_label(i, f"{r['digits']} digits", Palette.MUTED)
            self.play(FadeIn(right, run_time=0.4))
            lib_rows.append((lbl, txt, right))
            if r["id"] == "prb":
                note = markup(
                    "e<sup>x</sup> = 2<sup>x · log<sub>2</sub> e</sup>,  log<sub>2</sub> e to 18 decimals: the error grows with x",
                    20,
                    Palette.FAINT,
                )
                note.next_to(txt, DOWN, buff=0.2).align_to(txt, LEFT)
                self.play(FadeIn(note, run_time=0.6))
            self.wait(6.0)

        # the closest 18-decimal value, which exists and is unique
        c_lbl, c_txt = self.place_row(len(rows) + 1, "correctly rounded", Palette.CORRECT, cr, Palette.CORRECT)
        self.type_row(c_lbl, c_txt)
        c_right = self.right_label(len(rows) + 1, f"the closest {WORD_DECIMALS}-decimal value", Palette.CORRECT)
        self.play(FadeIn(c_right, run_time=0.5))
        self.wait(2.0)

        close = words("three good answers · none is the closest", 30, Palette.BODY)
        close.move_to([0, self.row_y(len(rows) + 1) - LABEL_DROP - 0.9, 0])
        self.play(FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.wait(14.0)

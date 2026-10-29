"""Slide 2, "What is e^40?": one closest answer, three good ones, and ours.

Six rows of monospace digits, aligned on the decimal point, each typed in
left to right, every row complete at 18 decimals (no number on screen is
cut short with an ellipsis). The first row, "e^40 to 18 decimals", is the
correctly rounded value (docs/benchmarks/edges.json, op exp, probe args
["40"], .truth rounded half-up at the 18th decimal): the closest
18-decimal value there is. Then Solady, Balancer and PRBMath SD (the
probe's .cells[lib].value, 18-decimal words already), then Blockulator's
two, FP19 and FP127 (the same cells, their words rendered to 18 decimals,
nearest; numbers() asserts each equals the correctly rounded value). The
three are 18-decimal fixed point, so they are counted in DECIMALS: as
each row completes, its first digit that departs from the exact value
turns WRONG (red), the digits after it dim, and the row is labelled with
how many digits after the point match and where the first wrong one sits
("3 right · wrong at the 4th decimal"; "0 right · wrong before the point"
when the integer part differs, since then no decimal is right). Both come
from the data: the count from matching_decimals, the position from
first_wrong_index, each against .truth and checked against the rounded
row shown. numbers() also carries each row's correct significant digits,
floor(−log10(|value − truth| / truth)), the measure edges.json reports
as .digits, so the ledger keeps both counts. Then the reveal: the FP19
and FP127 rows, larger, on a glowing panel, drawn last, labelled in the
same form as the others, the plain count: all 18 right, then what the
word holds by the cell's measure. FP127 (fixed point) holds correct
decimals, the cell's .digits less the integer part's digits (a floor);
FP19 (a float) holds the cell's .digits correct digits. Labels come from
static/data/libraries.json; no row says why a library's digits end where
they do (a documented precision is not a defect). About 75 s.
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
    markup,
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

EXACT_LABEL = f"e<sup>40</sup> to {WORD_DECIMALS} decimals"  # the first row's name (markup)
EXACT_RIGHT = f"the closest {WORD_DECIMALS}-decimal value"


def ordinal(n: int) -> str:
    """1st, 2nd, 3rd, 4th … 11th, 12th, 13th … 21st."""
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def wrong_decimal(first_wrong: int, truth: str) -> int:
    """The 1-based decimal position of the first wrong character, 0 when
    it falls in the integer part (before the point)."""
    point = len(truth.partition(".")[0])  # the point's index in every row
    return first_wrong - point if first_wrong > point else 0


def row_label_text(r: dict) -> str:
    """An 18-decimal row's label: the count of correct decimals and where
    the first wrong one sits, both from the data."""
    where = f"at the {ordinal(r['wrong_decimal'])} decimal" if r["wrong_decimal"] else "before the point"
    return f"{r['decimals']} right · wrong {where}"


def ours_label_text(r: dict) -> str:
    """The reveal rows' labels, the same form: all 18 decimals right, then
    what the word holds by the cell's measure. FP127 (fixed point) holds
    correct decimals; FP19 (a float) holds correct digits."""
    if r["id"] == "fp127":
        return f"{WORD_DECIMALS} right of {WORD_DECIMALS} · the word holds {r['decimals']} decimals"
    return f"{WORD_DECIMALS} right of {WORD_DECIMALS} · the word holds {r['digits']} digits"


def numbers() -> dict:
    p = probe(OP, ARG)
    truth = p["truth"]
    lib = libs()
    integer_part = truth.partition(".")[0]
    word_digits = len(integer_part) + WORD_DECIMALS
    exact_row = correctly_rounded_18(truth)
    rows = []
    for lid in LIBS:
        value = p["cells"][lid]["value"]
        fw = first_wrong_index(value, truth)
        r = {
            "id": lid,
            "label": lib[lid]["label"],
            "value": value,
            "decimals": matching_decimals(value, truth),
            "matching": matching_digits(value, truth),
            "digits": correct_digits(value, truth),
            "first_wrong": fw,
            "wrong_decimal": wrong_decimal(fw, truth),
        }
        # the red digit and the count hold against the rounded row on screen too
        assert first_wrong_index(value, exact_row) == fw and matching_decimals(value, exact_row) == r["decimals"], (lid, fw)
        r["right_label"] = row_label_text(r)
        rows.append(r)
    ours = []
    for lid in OURS:
        value = p["cells"][lid]["value"]
        cell_digits = int(p["cells"][lid]["digits"])
        m = matching_digits(value, truth)
        dec = correct_decimals(cell_digits, truth)
        word18 = correctly_rounded_18(value)  # the word rendered to 18 decimals, nearest
        assert m >= word_digits and dec >= WORD_DECIMALS and lib[lid].get("ours") and word18 == exact_row, (lid, m, dec, word18)
        r = {"id": lid, "label": lib[lid]["label"], "value": value, "word18": word18, "matching": m, "digits": cell_digits, "decimals": dec, "beyond": dec - WORD_DECIMALS}
        r["right_label"] = ours_label_text(r)
        ours.append(r)
    return {
        "truth": truth,
        "word_digits": word_digits,
        "exact_row": exact_row,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": exact_row,
    }


class Exp40(DeckScene):
    def row_y(self, i: int) -> float:
        return Y_TOP - i * PITCH - HERO_DROP * max(0, i - len(LIBS))

    def place_row(self, i: int, label: str, label_colour: str, value: str, digit_colour: str = Palette.TEXT, mono: float = MONO, sans: float = SANS, point_x: float | None = None, label_markup: bool = False):
        """A row: its name above, its digits below. With point_x the digits
        are placed so their decimal point sits on that x (the bigger reveal
        rows stay aligned on the point with the rows above) and the name
        starts where the digits do. label_markup sets the name in Pango
        markup (a superscript)."""
        y = self.row_y(i)
        lbl = (markup if label_markup else words)(label, sans, label_colour)
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
        rows = n["rows"]
        point = len(n["truth"].partition(".")[0])  # index of the point in every row
        self.wait(0.6)
        self.play(self.caption("docs/benchmarks/edges.json · exp(40)"))

        # the closest 18-decimal value: e^40 rounded at the 18th decimal, complete
        e_lbl, e_txt = self.place_row(0, EXACT_LABEL, Palette.EXACT, n["exact_row"], label_markup=True)
        self.type_row(e_lbl, e_txt, per_char=0.06)
        e_right = self.right_label(0, EXACT_RIGHT, Palette.FAINT)
        self.play(FadeIn(e_right, run_time=0.5))
        self.wait(4.5)
        point_x = e_txt[point].get_x()

        # three answers, counted in decimals: the word promises 18
        lib = libs()
        for i, r in enumerate(rows, start=1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(i, r["label"], colour, r["value"])
            self.type_row(lbl, txt)
            self.mark_wrong(txt, r["first_wrong"])
            right = self.right_label(i, r["right_label"], Palette.MUTED)
            self.play(FadeIn(right, run_time=0.4))
            self.wait(5.5)

        # the reveal: ours, bigger, on a glowing panel, their words to 18 decimals: all 18 right
        for j, r in enumerate(n["ours"], start=len(rows) + 1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(j, r["label"], colour, r["word18"], colour, mono=MONO_OURS, sans=SANS_OURS, point_x=point_x)
            panel = glow_bar(txt, colour, pad=0.15, opacity=0.11)
            panel.set_fill(opacity=0)
            self.add(panel)
            self.play(FadeIn(lbl, shift=RIGHT * 0.1, run_time=0.4), panel.animate.set_fill(opacity=0.11))
            self.play(AddTextLetterByLetter(txt, time_per_char=0.05))
            self.play(Indicate(txt, color=colour, scale_factor=1.03, run_time=0.6))
            right = self.right_label(j, r["right_label"], colour, size=SANS_OURS)
            self.play(FadeIn(right, shift=LEFT * 0.08, run_time=0.4))
            self.wait(2.5)

        close = words("three good answers, none the closest · Blockulator: all 18", 27, Palette.BODY)
        close.move_to([0, self.row_y(len(rows) + len(n["ours"])) - LABEL_DROP - 0.66, 0])  # under the last panel, above the caption
        self.play(FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.wait(12.0)

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
same form as the others, the plain count: all 18 right, then how many
digits of the whole word match e^40 by eye: the word's value (decoded
from the cell's .raw, written to 80 decimals) against e^40 to 80
decimals (vocab.truth80, mpmath), counted with matching_digits. Labels
come from static/data/libraries.json; no row says why a library's digits
end where they do (a documented precision is not a defect). Nothing
here says what the format holds (that is slide 15's fact).

Four sections, one per click: the exact row; the three library rows;
the two Blockulator rows; the closing line (claims V9, V29).
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
    SIZE_BODY,
    TRUTH_DECIMALS,
    DeckScene,
    Palette,
    colour_of,
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
    to_decimals,
    truth80,
    word_value,
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
MONO = SIZE_BODY
MONO_OURS = 35  # the reveal rows are the biggest on the slide
SANS = 23
SANS_OURS = 25

EXACT_LABEL = f"e<sup>40</sup> to {WORD_DECIMALS} decimals"  # the first row's name (markup)
EXACT_RIGHT = f"the closest {WORD_DECIMALS}-decimal value"
CAPTION = "docs/benchmarks/edges.json · exp(40)"
CLOSE = "three good answers, none the closest · Blockulator: all 18"

# the digit-bearing fixed strings on the slide, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    EXACT_LABEL: "V9",  # e^40 and its correctly rounded 18-decimal word
    EXACT_RIGHT: "V9",
    CAPTION: "V9",  # the exp(40) probe
    CLOSE: "V29",  # three distinct 18-decimal answers, none the closest; Blockulator's words round to it
}


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
    how many digits of the whole word match e^40 to 80 decimals, by eye."""
    return f"{WORD_DECIMALS} right of {WORD_DECIMALS} · {r['matching']} digits right"


def numbers() -> dict:
    p = probe(OP, ARG)
    truth = truth80()  # e^40 to 80 decimals; its first 24 are the probe's .truth (asserted there)
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
        # the red digit and the count hold against the rounded row on screen and against the probe's own truth
        assert first_wrong_index(value, exact_row) == fw and matching_decimals(value, exact_row) == r["decimals"], (lid, fw)
        assert first_wrong_index(value, p["truth"]) == fw and matching_decimals(value, p["truth"]) == r["decimals"], (lid, fw)
        r["right_label"] = row_label_text(r)
        rows.append(r)
    ours = []
    for lid in OURS:
        cell = p["cells"][lid]
        value = to_decimals(word_value(lid, cell["raw"]), TRUTH_DECIMALS)  # the word's value, to 80 decimals
        assert value.startswith(cell["value"][:-1]), (lid, value, cell["value"])  # the cell prints the same word
        m = matching_digits(value, truth)
        word18 = correctly_rounded_18(value)  # the word rendered to 18 decimals, nearest
        assert m >= word_digits and lib[lid].get("ours") and word18 == exact_row, (lid, m, word18)
        r = {"id": lid, "label": lib[lid]["label"], "value": value, "word18": word18, "matching": m, "digits": int(cell["digits"])}
        r["right_label"] = ours_label_text(r)
        ours.append(r)
    return {
        "truth": truth,
        "truth_decimals": TRUTH_DECIMALS,
        "truth_probe": p["truth"],
        "word_digits": word_digits,
        "exact_row": exact_row,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": exact_row,
    }


class Exp40(DeckScene):
    SECTIONS = ("exact", "libraries", "blockulator", "closing")

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
        self.section(0)
        self.wait(0.3)
        self.play(self.caption(CAPTION))

        # the closest 18-decimal value: e^40 rounded at the 18th decimal, complete
        e_lbl, e_txt = self.place_row(0, EXACT_LABEL, Palette.EXACT, n["exact_row"], label_markup=True)
        self.type_row(e_lbl, e_txt, per_char=0.06)
        e_right = self.right_label(0, EXACT_RIGHT, Palette.FAINT)
        self.play(FadeIn(e_right, run_time=0.5))
        point_x = e_txt[point].get_x()

        # three answers, counted in decimals: the word promises 18
        self.section(1)
        lib = libs()
        for i, r in enumerate(rows, start=1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(i, r["label"], colour, r["value"])
            self.type_row(lbl, txt)
            self.mark_wrong(txt, r["first_wrong"])
            right = self.right_label(i, r["right_label"], Palette.MUTED)
            self.play(FadeIn(right, run_time=0.4))
            self.wait(2.0)

        # the reveal: ours, bigger, on a glowing panel, their words to 18 decimals: all 18 right
        self.section(2)
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
            self.wait(1.5)

        self.section(3)
        close = words(CLOSE, 27, Palette.BODY)
        close.move_to([0, self.row_y(len(rows) + len(n["ours"])) - LABEL_DROP - 0.66, 0])  # under the last panel, above the caption
        self.play(FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.close()

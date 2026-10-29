"""Slide 2, "What is e^40?": one closest answer, three good ones, and ours.

Rows of monospace digits aligned on the decimal point, each typed in left
to right, every row complete in its stated format (no number on screen is
cut short with an ellipsis). The first row, "e^40 to 18 decimals", is the
correctly rounded value (docs/benchmarks/edges.json, op exp, probe args
["40"], .truth rounded half-up at the 18th decimal): the closest
18-decimal value there is. Then Solady, Balancer and PRBMath SD (the
probe's .cells[lib].value, 18-decimal words already). The three are
18-decimal fixed point, so they are counted in DECIMALS: as each row
completes, its first digit that departs from the exact value turns WRONG
(red), the digits after it dim, and the row is labelled with how many
digits after the point match and where the first wrong one sits ("3 right
· wrong at the 4th decimal"; "0 right · wrong before the point" when the
integer part differs, since then no decimal is right). Both come from the
data: the count from matching_decimals, the position from
first_wrong_index, each against .truth and checked against the rounded
row shown. numbers() also carries each row's correct significant digits,
floor(−log10(|value − truth| / truth)), the measure edges.json reports as
.digits, so the ledger keeps both counts.

Then the reveal: Blockulator's two words in full. Each cell's .raw is
decoded exactly (vocab.decode_fp127: raw / 2^128; vocab.decode_fp19: the
binary256 fields, contracts/src/fp19/README.md lines 21–24) to a Fraction
with a power-of-two denominator, whose decimal expansion therefore
terminates: FP127's at the 127th decimal, FP19's at the 179th (the
exponent is negative). Every one of those decimals is drawn, in blocks
of ten with a ruler underneath marking each tenth decimal, so a reader
can count. The digits that match e^40 to 80 decimals (vocab.truth80,
mpmath; matching_digits counts the prefix) are lit, EMERALD for FP127,
TEXT under a glow for FP19; from the first digit past the matching
prefix the digits are MUTED, never red: they are the word's own exact
expansion, the bits below its precision, not errors, and a bracket under
that point says so ("the word's precision ends here · 39 decimals"). The
label at the right of each word's name line is the matching-prefix count
and the decimals it covers ("57 digits right · 39 decimals"). The three
library rows become one faint line of context above the words. Labels
come from static/data/libraries.json; no row says why a library's digits
end where they do (a documented precision is not a defect). Nothing here
says what the format holds (that is slide 15's fact).

Four sections, one per click: the exact row; the three library rows;
the two Blockulator words; the closing lines (claims V9, V29).
"""

from __future__ import annotations

from manim import (
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    FadeIn,
    FadeOut,
    ReplacementTransform,
    Transform,
    VGroup,
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
    exact_decimals,
    first_wrong_index,
    glow_line,
    libs,
    markup,
    matching_decimals,
    matching_digits,
    precision_end,
    probe,
    ruler,
    ruler_depth,
    to_decimals,
    truth80,
    word_value,
    words,
)

OP, ARG = "exp", "40"
LIBS = ("solady", "balancer", "prb")  # the three answers the talk names
OURS = ("fp127", "fp19")  # Blockulator's, from the same probe, in the order they unfold
WORD_DECIMALS = 18
RULER_EVERY = 10  # the ruler marks every tenth decimal; a block of ten is typed as one beat

X_LEFT = -6.15  # digit strings and row labels start here
X_RIGHT = 6.15  # the right-hand labels end here
Y_TOP = 3.45
PITCH = 1.04  # row to row (the exact row and the three library rows)
LABEL_DROP = 0.38  # label line to digit line
MONO = SIZE_BODY
SANS = 23
SANS_OURS = 25

# the two words in full: a first line with the integer part, the point and
# LINE1 decimals, then lines of LINE decimals, at MONO_WORD (the largest mono
# size at which 50 digits sit inside the safe area: 50 × 0.232 = 11.6 units)
MONO_WORD = 28
LINE1 = 30
LINE = 50
WORD_PITCH = 0.63  # digit line to digit line, the ruler strip between
NAME_DROP = 0.36  # a word's name line to its first digit line
NAME_GAP = 0.27  # the last ruler's numbers to the next word's name line
CTX_Y = 2.57  # the one line of context (then the first closing line)
CLOSE2_Y = 2.245  # the second closing line
WORD_TOP = 1.87  # the first word's name line
SANS_CLOSE = 24  # the two closing lines, stacked where the context line was

EXACT_LABEL = f"e<sup>40</sup> to {WORD_DECIMALS} decimals"  # the first row's name (markup)
EXACT_RIGHT = f"the closest {WORD_DECIMALS}-decimal value"
CAPTION = "docs/benchmarks/edges.json · exp(40)"
CLOSE = "three good answers, none the closest · Blockulator: all 18"
END_TEXT = "the word's precision ends here"

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
    """A word's label: how many leading digits of the whole word match
    e^40 to 80 decimals, by eye, and how many decimals that covers."""
    return f"{r['matching']} digits right · {r['decimals_right']} decimals"


def end_text(r: dict) -> str:
    """The bracket under the first digit past the matching prefix."""
    return f"{END_TEXT} · {r['decimals_right']} decimals"


def context_text(rows: list[dict]) -> str:
    """The three library rows as one faint line: their names and their
    correct decimals, in the rows' order."""
    return " · ".join(r["label"] for r in rows) + ": " + " · ".join(str(r["decimals"]) for r in rows) + " decimals right"


def close2_text(ours: list[dict]) -> str:
    """The second closing line: each word's decimals, every one of them
    right (each word's matching prefix covers all of its stated decimals)."""
    return " · ".join(f"{r['label']}: {r['decimals_right']} decimals" for r in ours) + " · every one of them right"


def word_lines(word: str) -> list[str]:
    """A word's expansion as the lines the slide draws: the integer part,
    the point and the first LINE1 decimals, then LINE decimals per line;
    every decimal appears on exactly one line."""
    whole, _, frac = word.partition(".")
    lines = [whole + "." + frac[:LINE1]]
    for k in range(LINE1, len(frac), LINE):
        lines.append(frac[k : k + LINE])
    assert "".join(lines).replace(".", "") == whole + frac, word
    return lines


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
        q = word_value(lid, cell["raw"])  # the word, exactly (decode_fp127 / decode_fp19)
        word = exact_decimals(q)  # its complete decimal expansion: every digit the word holds
        value = to_decimals(q, TRUTH_DECIMALS)  # the same word to 80 decimals, nearest
        assert value.startswith(cell["value"][:-1]), (lid, value, cell["value"])  # the cell prints the same word
        m = matching_digits(word, truth)
        assert m == matching_digits(value, truth), (lid, m)  # the count by eye is the same on either string
        word18 = correctly_rounded_18(word)  # the word rendered to 18 decimals, nearest
        assert m >= word_digits and lib[lid].get("ours") and word18 == exact_row, (lid, m, word18)
        dec = m - len(integer_part)  # the decimals the matching prefix covers (the integer part is inside it)
        word_decimals = len(word.partition(".")[2])
        assert WORD_DECIMALS <= dec < word_decimals, (lid, dec, word_decimals)  # the tail past the prefix is on the slide too
        r = {
            "id": lid,
            "label": lib[lid]["label"],
            "value": value,
            "word": word,
            "word_decimals": word_decimals,
            "lines": word_lines(word),
            "word18": word18,
            "matching": m,
            "decimals_right": dec,
            "digits": int(cell["digits"]),
        }
        r["right_label"] = ours_label_text(r)
        r["end_label"] = end_text(r)
        ours.append(r)
    by_id = {r["id"]: r for r in ours}
    longest = max(r["word_decimals"] for r in ours)
    return {
        "truth": truth,
        "truth_decimals": TRUTH_DECIMALS,
        "truth_probe": p["truth"],
        "word_digits": word_digits,
        "exact_row": exact_row,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": exact_row,
        "fp127_word": by_id["fp127"]["word"],
        "fp19_word": by_id["fp19"]["word"],
        "fp127_match": by_id["fp127"]["matching"],
        "fp19_match": by_id["fp19"]["matching"],
        "fp127_decimals": by_id["fp127"]["decimals_right"],
        "fp19_decimals": by_id["fp19"]["decimals_right"],
        "ruler_marks": list(range(RULER_EVERY, longest + 1, RULER_EVERY)),
        "context": context_text(rows),
        "close2": close2_text(ours),
    }


class Exp40(DeckScene):
    SECTIONS = ("exact", "libraries", "blockulator", "closing")

    def row_y(self, i: int) -> float:
        return Y_TOP - i * PITCH

    def place_row(self, i: int, label: str, label_colour: str, value: str, digit_colour: str = Palette.TEXT, mono: float = MONO, sans: float = SANS, label_markup: bool = False):
        """A row: its name above, its digits below. label_markup sets the
        name in Pango markup (a superscript)."""
        y = self.row_y(i)
        lbl = (markup if label_markup else words)(label, sans, label_colour)
        txt = digits(value, mono, digit_colour)
        txt.move_to([X_LEFT + txt.width / 2, y - LABEL_DROP, 0])
        lbl.move_to([txt.get_left()[0] + lbl.width / 2, y, 0])
        return lbl, txt

    def right_label(self, y: float, text: str, colour: str, size: float = SANS):
        t = words(text, size, colour)
        t.move_to([X_RIGHT - t.width / 2, y, 0])
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

    def unfold_word(self, r: dict, name_y: float, colour: str, lit: str, glow: bool, point: int) -> float:
        """A word in full: its name at the left of the name line, the
        expansion typed line by line in blocks of ten, a ruler under each
        line, the matched digits lit and the tail MUTED, the bracket where
        the precision ends, then the count at the right of the name line.
        Returns the y of the bottom of the last ruler strip."""
        name = words(r["label"], SANS_OURS, colour)
        name.move_to([X_LEFT + name.width / 2, name_y, 0])
        self.play(FadeIn(name, shift=RIGHT * 0.1, run_time=0.4))
        dec_right = r["decimals_right"]
        first = 0  # the 1-based decimal index of the line's first decimal, less one
        y = name_y - NAME_DROP
        for j, line in enumerate(r["lines"]):
            txt = digits(line, MONO_WORD, lit)
            txt.move_to([X_LEFT + txt.width / 2, y, 0])
            offset = point + 1 if j == 0 else 0  # glyphs before the first decimal on this line
            n_dec = len(line) - offset

            def decimal_of(g: int) -> int:  # the 1-based decimal index under glyph g
                return first + g - offset + 1

            # the tail past the matching prefix is the word's own, MUTED (never red)
            k_end = None
            for g in range(offset, len(line)):
                if decimal_of(g) > dec_right:
                    k_end = g
                    break
            if k_end is not None:
                txt[k_end:].set_color(Palette.MUTED)
            lit_to = len(line) if k_end is None else k_end  # glyphs lit on this line
            if glow and lit_to:
                band = glow_line([txt[0].get_left() * [1, 0, 0] + [0, y, 0], txt[lit_to - 1].get_right() * [1, 0, 0] + [0, y, 0]], colour, width=34, opacity=0.10)
                self.add(band)
            marks = [(g, decimal_of(g)) for g in range(offset, len(line)) if decimal_of(g) % RULER_EVERY == 0]
            end = None
            if k_end is not None and k_end >= offset and decimal_of(k_end) == dec_right + 1:
                end = precision_end(txt, k_end, r["end_label"], colour)
            strip = ruler(txt, marks, avoid=end.avoid if end else None)
            self.play(AddTextLetterByLetter(txt, time_per_char=0.025))
            self.play(FadeIn(strip, run_time=0.2))
            if end is not None:
                self.play(FadeIn(end, shift=UP * 0.05, run_time=0.4))
            first += n_dec
            last = txt
            y -= WORD_PITCH
        right = self.right_label(name_y, r["right_label"], colour, size=SANS_OURS)
        self.play(FadeIn(right, shift=LEFT * 0.08, run_time=0.4))
        return last.get_bottom()[1] - ruler_depth()

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
        e_right = self.right_label(self.row_y(0), EXACT_RIGHT, Palette.FAINT)
        self.play(FadeIn(e_right, run_time=0.5))

        # three answers, counted in decimals: the word promises 18
        self.section(1)
        lib = libs()
        row_mobjects = VGroup()
        for i, r in enumerate(rows, start=1):
            colour = colour_of(lib[r["id"]])
            lbl, txt = self.place_row(i, r["label"], colour, r["value"])
            self.type_row(lbl, txt)
            self.mark_wrong(txt, r["first_wrong"])
            right = self.right_label(self.row_y(i), r["right_label"], Palette.MUTED)
            self.play(FadeIn(right, run_time=0.4))
            row_mobjects.add(lbl, txt, right)
            self.wait(2.0)

        # the reveal: the two words in full, every decimal they hold, the matching prefix lit
        self.section(2)
        context = words(n["context"], SANS, Palette.FAINT)
        context.move_to([0, CTX_Y, 0])
        self.play(FadeOut(row_mobjects, shift=UP * 0.3, run_time=0.7), FadeIn(context, shift=UP * 0.3, run_time=0.7))
        by_id = {r["id"]: r for r in n["ours"]}
        name_y = WORD_TOP
        # FP127: EMERALD digits; FP19: its family colour, white, under a glow (EXACT's white is the row at the top)
        bottom = self.unfold_word(by_id["fp127"], name_y, Palette.EMERALD, Palette.EMERALD, glow=False, point=point)
        name_y = bottom - NAME_GAP
        self.unfold_word(by_id["fp19"], name_y, Palette.TEXT, Palette.TEXT, glow=True, point=point)
        self.wait(2.0)

        # the closing lines take the context line's place: the verdict on the three, then on the two
        self.section(3)
        close = words(CLOSE, SANS_CLOSE, Palette.BODY).move_to([0, CTX_Y, 0])
        close2 = words(n["close2"], SANS_CLOSE, Palette.BODY).move_to([0, CLOSE2_Y, 0])
        self.play(ReplacementTransform(context, close, run_time=0.8))
        self.play(FadeIn(close2, shift=UP * 0.08, run_time=0.8))
        self.close()

"""Slide 2, "What is e^40?": one closest answer, three good ones, and ours.

Rows of monospace digits on one column grid (every row starts at the same
x at the same size, so decimal k sits in the same column in every row),
each typed in left to right, every row complete in its stated format (no
number on screen is cut short with an ellipsis). The title row, "e^40 to
18 decimals", is the correctly rounded value (docs/benchmarks/edges.json,
op exp, probe args ["40"], .truth rounded half-up at the 18th decimal):
the closest 18-decimal value there is. Then Solady, Balancer and PRBMath
SD (the probe's .cells[lib].value, 18-decimal words already), counted in
DECIMALS: as each row completes, its first digit that departs from the
exact value turns WRONG (red), the digits after it dim, and the row is
labelled with how many decimals match ("2 decimals right"; matching_decimals
against .truth, checked against the rounded row shown). numbers() also
carries each row's correct significant digits and the position of its
first wrong decimal, so the ledger keeps both counts.

Then the reveal. The three rows leave; Blockulator's two words arrive in
the space they held, last, each to a stated number of decimals: BL127's
word to 40, BL19's to 60 (each cell's .raw decoded exactly by
vocab.decode_bl127 / decode_bl19 to a Fraction, then rounded to N
decimals, nearest). Each is drawn as one block: the integer part, the
point and 20 decimals, then lines of 20 decimals under the first line's
decimals, so the columns read in tens. The digits that match e^40
(vocab.truth80, mpmath; matching_digits counts the prefix) are lit,
EMERALD for BL127, TEXT under a glow for BL19; the few digits past the
matching prefix are MUTED, never red (they are the word's own value, below
its precision, not errors), and a bracket at that point carries the
word's one label ("39 decimals right"). No row says why a library's
digits end where they do (a documented precision is not a defect), and
nothing says what the format holds (that is slide 15's fact).

Three sections, one per click: the exact row; the three library rows;
Blockulator's two words (the poster). Claims V9, V29.
"""

from __future__ import annotations

from manim import (
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    FadeIn,
    FadeOut,
    Line,
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
    matching_decimals,
    matching_digits,
    precision_end,
    probe,
    to_decimals,
    truth80,
    word_value,
    words,
)

OP, ARG = "exp", "40"
LIBS = ("solady", "balancer", "prb")  # the three answers the talk names
OURS = ("bl127", "bl19")  # Blockulator's, from the same probe, in the order they unfold
SHOWN = {"bl127": 40, "bl19": 60}  # the decimals each word is drawn to (the stated format, "to N decimals")
WORD_DECIMALS = 18
LINE = 20  # decimals per line of a word: the first line carries the integer part and the point too

X_LEFT = -5.79  # every digit row and row name starts here: right of the left mark (vocab's TITLE_GAP)
X_RIGHT = 5.9  # the right-hand labels end here, clear of the right mark
Y_TITLE = 3.325  # the title line: the marks' centre line
MONO = 36  # every digit row (the 39-glyph first line of a word is 11.6 units at 36)
SANS = SIZE_BODY  # row names and labels
TITLE_SIZE = 36
EXACT_Y = 2.74  # the exact row's digits, under the title
ROW_TOP = 1.85  # the first library row's name line
PITCH = 1.4  # library row to library row
NAME_DROP = 0.48  # a name line to its digits' first line
WORD_TOP = 1.85  # BL127's name line (where the library rows were)
WORD_PITCH = 0.6  # a word's digit line to the next
WORD_GAP = 0.75  # the bottom of BL127's bracket label to BL19's name line

EXACT_LABEL = f"e<sup>40</sup> to {WORD_DECIMALS} decimals"  # the title row's name (markup)
EXACT_RIGHT = f"the closest {WORD_DECIMALS}-decimal value"

# the digit-bearing fixed strings on the slide, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    EXACT_LABEL: "V9",  # e^40 and its correctly rounded 18-decimal word
    EXACT_RIGHT: "V9",
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


def right_text(decimals: int) -> str:
    """Every row's one label: the decimals that match e^40, counted by eye."""
    return f"{decimals} decimals right"


def name_text(label: str, shown: int) -> str:
    """A word's name line: the library and the stated format."""
    return f"{label} to {shown} decimals"


def word_lines(value: str) -> list[str]:
    """A word to N decimals as the lines the slide draws: the integer part,
    the point and the first LINE decimals, then LINE decimals per line;
    every decimal appears on exactly one line."""
    whole, _, frac = value.partition(".")
    lines = [whole + "." + frac[:LINE]] + [frac[k : k + LINE] for k in range(LINE, len(frac), LINE)]
    assert "".join(lines).replace(".", "") == whole + frac, value
    return lines


def block_text(lines: list[str], point: int) -> str:
    """The lines as one mono string: each later line indented under the
    first line's decimals, so decimal k and k + LINE share a column. Text
    keeps a (zero-width) submobject per space and line break, so glyph i
    is character i."""
    return "\n".join([lines[0]] + [" " * (point + 1) + ln for ln in lines[1:]])


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
        r["right_label"] = right_text(r["decimals"])
        rows.append(r)
    ours = []
    for lid in OURS:
        cell = p["cells"][lid]
        q = word_value(lid, cell["raw"])  # the word, exactly (decode_bl127 / decode_bl19)
        word = exact_decimals(q)  # its complete decimal expansion: every digit the word holds
        shown = to_decimals(q, SHOWN[lid])  # the word to N decimals, nearest: what the slide draws
        assert to_decimals(q, TRUTH_DECIMALS).startswith(cell["value"][:-1]), (lid, cell["value"])  # the cell prints the same word
        m = matching_digits(word, truth)
        assert m == matching_digits(shown, truth), (lid, m)  # the count by eye is the same on the drawn string
        word18 = correctly_rounded_18(word)  # the word rendered to 18 decimals, nearest
        assert m >= word_digits and lib[lid].get("ours") and word18 == exact_row, (lid, m, word18)
        dec = m - len(integer_part)  # the decimals the matching prefix covers (the integer part is inside it)
        assert WORD_DECIMALS <= dec < SHOWN[lid] < len(word.partition(".")[2]), (lid, dec)  # the bracket falls inside the drawn digits
        r = {
            "id": lid,
            "label": lib[lid]["label"],
            "word": word,
            "word_decimals": len(word.partition(".")[2]),
            "shown": shown,
            "shown_decimals": SHOWN[lid],
            "lines": word_lines(shown),
            "word18": word18,
            "matching": m,
            "decimals_right": dec,
            "digits": int(cell["digits"]),
        }
        r["name_line"] = name_text(r["label"], SHOWN[lid])
        r["right_label"] = right_text(dec)
        ours.append(r)
    by_id = {r["id"]: r for r in ours}
    return {
        "truth": truth,
        "truth_decimals": TRUTH_DECIMALS,
        "truth_probe": p["truth"],
        "word_digits": word_digits,
        "exact_row": exact_row,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": exact_row,
        "bl127_word": by_id["bl127"]["word"],
        "bl19_word": by_id["bl19"]["word"],
        "bl127_match": by_id["bl127"]["matching"],
        "bl19_match": by_id["bl19"]["matching"],
        "bl127_decimals": by_id["bl127"]["decimals_right"],
        "bl19_decimals": by_id["bl19"]["decimals_right"],
    }


class Exp40(DeckScene):
    SECTIONS = ("exact", "libraries", "blockulator")

    def row_y(self, i: int) -> float:
        """Library row i's name line (i = 1, 2, 3)."""
        return ROW_TOP - (i - 1) * PITCH

    def at_left(self, mobj, y: float):
        return mobj.move_to([X_LEFT + mobj.width / 2, y, 0])

    def right_label(self, y: float, text: str, colour: str, size: float = SANS):
        t = words(text, size, colour)
        return t.move_to([X_RIGHT - t.width / 2, y, 0])

    def mark_wrong(self, txt, k: int, after=Palette.FAINT):
        """Light the first wrong digit and dim everything after it."""
        glyph = txt[k]
        lit = glyph.copy().set_color(Palette.WRONG).scale(1.35)
        self.play(
            Transform(glyph, lit, run_time=0.25, rate_func=ease_out_cubic),
            txt[k + 1 :].animate.set_color(after),
        )
        self.play(Transform(glyph, glyph.copy().scale(1 / 1.35), run_time=0.25))

    def bracket(self, txt, k: int, text: str, colour: str):
        """The word's one label at the point its precision ends: vocab's
        precision_end() under the gap before glyph k, its label turned to
        the left of the tick (the matching digits are the ones it counts,
        and the drawn digits end a few glyphs to the right)."""
        end = precision_end(txt, k, text, colour, size=SANS)
        tick, foot, label = end
        x = tick.get_x()
        y = foot.get_y()
        end.remove(foot)
        foot = Line([x, y, 0], [x - 0.1, y, 0], color=colour, stroke_width=2.5)
        label.move_to([x - 0.16 - label.width / 2, label.get_y(), 0])
        return VGroup(tick, foot, label)

    def unfold_word(self, r: dict, name_y: float, colour: str, glow: bool, point: int) -> float:
        """A word to its stated decimals: its name line, then the block
        typed in (integer part, point and 20 decimals; then 20 a line under
        the decimals), the matching digits lit and the rest MUTED, then the
        bracket with the count. Returns the y of the bracket label's bottom."""
        name = self.at_left(words(r["name_line"], SANS, colour), name_y)
        self.play(FadeIn(name, shift=RIGHT * 0.1, run_time=0.4))
        txt = digits(block_text(r["lines"], point), MONO, colour)
        txt.shift([X_LEFT - txt[0].get_left()[0], name_y - NAME_DROP - txt[0].get_y(), 0])
        # glyph index of decimal d (1-based): the first line holds point + 1 + LINE glyphs, a line break,
        # then each later line is point + 1 spaces and LINE decimals
        stride = point + 1 + LINE + 1
        for j in range(1, len(r["lines"])):  # open the lines to WORD_PITCH (the font's own leading is tighter)
            line = txt[j * stride : (j + 1) * stride]
            line.shift(UP * (txt[0].get_y() - j * WORD_PITCH - txt[j * stride + point + 1].get_y()))

        def glyph_of(d: int) -> int:
            line, col = divmod(d - 1, LINE)
            return line * stride + point + 1 + col

        dec_right = r["decimals_right"]
        for d in range(dec_right + 1, r["shown_decimals"] + 1):
            txt[glyph_of(d)].set_color(Palette.MUTED)  # the word's own digits past the match: never red
        if glow:
            # the glow under the lit digits, one band per line
            for j in range((dec_right - 1) // LINE + 1):
                first = 0 if j == 0 else glyph_of(j * LINE + 1)
                last = glyph_of(min((j + 1) * LINE, dec_right))
                y = txt[last].get_y()
                band = glow_line([[txt[first].get_left()[0], y, 0], [txt[last].get_right()[0], y, 0]], colour, width=44, opacity=0.10)
                self.add(band)
        self.play(AddTextLetterByLetter(txt, time_per_char=0.03))
        end = self.bracket(txt, glyph_of(dec_right + 1), r["right_label"], colour)
        self.play(FadeIn(end, shift=UP * 0.05, run_time=0.5))
        return end[2].get_bottom()[1]

    def construct(self):
        n = numbers()
        rows = n["rows"]
        point = len(n["truth"].partition(".")[0])  # index of the point in every row
        lib = libs()
        self.section(0)
        # the chrome: the title (the exact row's name) and the three library rows'
        # names (the keys, in their family colour) are on the first frame
        title = self.title(EXACT_LABEL, TITLE_SIZE, Palette.EXACT, use_markup=True)
        names = [self.at_left(words(r["label"], SANS, colour_of(lib[r["id"]])), self.row_y(i)) for i, r in enumerate(rows, start=1)]
        self.fix(title, *names)
        e_txt = self.at_left(digits(n["exact_row"], MONO, Palette.EXACT), EXACT_Y)
        self.wait(0.3)

        # the closest 18-decimal value: e^40 rounded at the 18th decimal, complete; its name is the slide's title
        self.play(AddTextLetterByLetter(e_txt, time_per_char=0.06))
        self.wait(0.3)
        e_right = self.right_label(Y_TITLE, EXACT_RIGHT, Palette.MUTED)
        self.play(FadeIn(e_right, run_time=0.5))

        # three answers, counted in decimals: the word promises 18
        self.section(1)
        story = VGroup(e_right, *names)
        for i, r in enumerate(rows, start=1):
            txt = self.at_left(digits(r["value"], MONO, Palette.TEXT), self.row_y(i) - NAME_DROP)
            self.play(AddTextLetterByLetter(txt, time_per_char=0.065))
            self.wait(0.3)
            self.mark_wrong(txt, r["first_wrong"])
            self.add(txt)  # the Transform split the row into glyphs on the scene; put it back whole
            right = self.right_label(self.row_y(i), r["right_label"], Palette.MUTED)
            self.play(FadeIn(right, run_time=0.4))
            story.add(txt, right)
            self.wait(1.5)

        # the reveal: the three rows leave; Blockulator's two words take their place, last, lit where they match
        self.section(2)
        self.play(FadeOut(story, shift=UP * 0.3, run_time=0.7))
        by_id = {r["id"]: r for r in n["ours"]}
        # BL127: EMERALD; BL19: its family colour, white, under a glow (EXACT's white is the title row)
        bottom = self.unfold_word(by_id["bl127"], WORD_TOP, Palette.EMERALD, glow=False, point=point)
        self.unfold_word(by_id["bl19"], bottom - WORD_GAP, Palette.TEXT, glow=True, point=point)
        self.close()

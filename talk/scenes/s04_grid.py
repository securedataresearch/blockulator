"""Slide 4, "Computers round": the grid, from human scale down to one word.

The number line starts at human scale: integer ticks around e^40 (the
two integers it lies between, complete, in JetBrains Mono), the exact
e^40 marked between them, "e^40 = <its 18-decimal value> (to 18
decimals)" across the top. Then the dive, in two layers. No number on
screen is cut short with an ellipsis: every one is complete in a stated
format (so many decimals; a fraction word in hex).

Layer 1, decimal: the grid is stretched tenfold eighteen times (one tick =
10^-1, 10^-2, …, the counter ticking, the digits across the top lighting
as each power of ten resolves them, the two neighbouring ticks relabelled
at every level with their complete values at that many decimals) until
one tick = 10^-18, a whole wei: the 18-decimal libraries' grid. The exact
value sits between …034804 and …034805 and snaps to the nearer: the WAD
answer.

Layer 2, binary: the dive goes on, now by powers of two (one tick =
2^-60, 2^-64, …, sixteen-fold each step, the ticks labelled with their
fraction words in hex) to 2^-128 ≈ 2.9 × 10^-39: FP127's grid. The header
now shows e^40 to 80 decimals (vocab.truth80: mpmath, its first 24
decimals asserted against edges.json's truth), labelled so, on two
lines, lighting to the end as the grid resolves it. The exact e^40 sits
between two adjacent 128-bit fraction words, shown complete as 32 hex
digits each, with their decimal readings beneath to 80 decimals: the
two readings part at the 39th decimal, so the grid's fineness is on
screen. On this grid the three snaps play: to the nearer tick (white,
rounding itself), the far way (WRONG, red, its direction drawn), the
right way (CORRECT, emerald, with a halo), labelled "FP127's word" with
the word's hex fraction complete and its value to 18 decimals. A bracket
measures half a unit. Footer: a 256-bit word holds 2^256 numbers; e^40
is not one of them. The dives are quick (each power of ten about 0.3 s,
each power of two about 0.2 s, the counter ticking throughout).

Five sections, one per click: human scale; the decimal dive; the binary
dive; half a unit; the three snaps (with the footer). The last frame
holds as the slide.

The zoom is the grid stretching about the exact value, not the camera
moving: a camera zoom of 10^39 would run out of floating-point positions
long before 2^-128, and a stretch leaves every stroke hairline. Every
position is computed with Fraction from the truth and converted to a
screen offset only at the end.

Numbers from docs/benchmarks/edges.json: op exp, probe ["40"]: .truth
(extended to 80 decimals by vocab.truth80) and .cells.fp127.value; the
neighbours at every decimal level and every binary level, the correctly
rounded 18-decimal value, the binary neighbours floor(t · 2^128) and + 1,
their hex fractions and decimal readings, FP127's word to 18 decimals
(asserted equal to the correctly rounded value), and the fraction of a
unit the exact value sits at on each grid are computed here (vocab
helpers, Fraction) and exposed in numbers().
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from math import floor, log10

from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    Circle,
    Create,
    DashedLine,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    VGroup,
    config,
)
from manim.utils.rate_functions import ease_in_out_cubic, ease_out_cubic, linear

from vocab import SIZE_CAPTION, TRUTH_DECIMALS, DeckScene, GridLine, Palette, check_mark, correctly_rounded_18, digits, direction, halo, markup, measure, probe, snap, truth80, words

OP, ARG = "exp", "40"
WORD_DECIMALS = 18  # layer 1 ends here: one tick = 10^-18
FRACTION_BITS = 128  # layer 2 ends here: one tick = 2^-128 (FP127)
BIT_START, BIT_STEP = 60, 4  # layer 2 dives 2^-60, 2^-64, … (2^-60 ≈ 0.87e-18, next to the wei grid)
HEX_DIGITS = FRACTION_BITS // 4  # a 128-bit fraction word is 32 hex digits
EXPANSION_DECIMALS = TRUTH_DECIMALS  # the neighbours' decimal readings: as far as the truth goes (80)
LINE_DECIMALS = 40  # an 80-decimal number wraps after this many decimals
DECIMAL_BASE, BINARY_BASE = 10, 2
L = 1.3  # screen units per tick
Y_LINE = 0.35
LABEL_Y = 2.3  # the grid's name (left) and the counter (right), under the two-line header
HALF = config.frame_width / 2 + 0.5
CAPTION = "docs/benchmarks/edges.json · exp(40)"
FOOTER = "a 256-bit word holds 2<sup>256</sup> numbers; e<sup>40</sup> is not one of them"

# the digit-bearing fixed strings on the slide, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    CAPTION: "V9",
    "e<sup>40</sup> =": "V9",
    "e<sup>40</sup>": "V9",
    FOOTER: "V8",  # V8: a 256-bit word holds finitely many numbers and most exact results fall between two of them; e^40 is not a 2^-128 multiple (V9 truth)
}


def wrap_decimals(s: str) -> str:
    """An 80-decimal number on two lines: the integer part and the first
    LINE_DECIMALS decimals, then the rest (nothing is cut; check.py reads
    the string with the break closed)."""
    whole, _, frac = s.partition(".")
    if len(frac) <= LINE_DECIMALS:
        return s
    return f"{whole}.{frac[:LINE_DECIMALS]}\n{frac[LINE_DECIMALS:]}"


def _frac_str(q: Fraction, places: int) -> str:
    """q as a decimal string with exactly `places` decimals (truncated)."""
    scaled = q.numerator * 10**places // q.denominator
    whole, frac = divmod(scaled, 10**places)
    return f"{whole}.{frac:0{places}d}" if places else str(whole)


def _frac_round(q: Fraction, places: int) -> str:
    """q to `places` decimals, nearest, half-up."""
    scaled = floor(q * 10**places + Fraction(1, 2))
    whole, frac = divmod(scaled, 10**places)
    return f"{whole}.{frac:0{places}d}" if places else str(whole)


def hex_fraction(w: int, bits: int) -> str:
    """The fraction of a word w on the 2^-bits grid (its low `bits` bits)
    as hex, complete: 0x and bits/4 digits."""
    assert bits % 4 == 0, bits
    return f"0x{w & ((1 << bits) - 1):0{bits // 4}x}"


def numbers() -> dict:
    p = probe(OP, ARG)
    truth = truth80()
    t = Fraction(truth)
    truth_decimals = len(truth.partition(".")[2])
    assert truth_decimals == EXPANSION_DECIMALS, truth_decimals  # the readings go as far as the truth, no further
    bits = [BIT_START + BIT_STEP * i for i in range((FRACTION_BITS - BIT_START) // BIT_STEP + 1)]
    # the neighbours at every level: the two ticks either side of e^40, complete at that level
    decimal_levels = list(range(WORD_DECIMALS + 1))
    neighbours_decimal = [[_frac_str(Fraction(floor(t * 10**k) + m, 10**k), k) for m in (0, 1)] for k in decimal_levels]
    neighbours_hex = [[hex_fraction(floor(t * 2**b) + m, b) for m in (0, 1)] for b in bits]
    # layer 1: the 10^-18 neighbours
    u18 = Fraction(1, 10**WORD_DECIMALS)
    lo18 = floor(t / u18)
    f18 = t / u18 - lo18
    # layer 2: the 2^-128 neighbours
    ub = Fraction(1, 2**FRACTION_BITS)
    lob = floor(t / ub)
    fb = t / ub - lob
    hib = lob + 1
    nearest_b = hib if fb >= Fraction(1, 2) else lob
    readings = {w: _frac_round(Fraction(w) * ub, EXPANSION_DECIMALS) for w in (lob, hib)}
    assert readings[lob] != readings[hib], readings  # the two words' readings part on screen
    fp127 = p["cells"]["fp127"]["value"]
    # FP127's word, rounded to the probe's decimals as the cell prints it, is the nearer neighbour
    assert _frac_round(Fraction(nearest_b) * ub, len(fp127.partition(".")[2])) == fp127, (fp127, nearest_b)
    word18 = _frac_round(Fraction(nearest_b) * ub, WORD_DECIMALS)
    assert word18 == correctly_rounded_18(truth), word18  # FP127's word to 18 decimals is the closest 18-decimal value
    with localcontext() as ctx:
        ctx.prec = 30
        tick_b = Decimal(ub.numerator) / Decimal(ub.denominator)
    return {
        "truth": truth,
        "truth_probe": p["truth"],
        "expansion_decimals": EXPANSION_DECIMALS,
        "levels_decimal": WORD_DECIMALS,
        "decimal_levels": decimal_levels,
        "bases": [DECIMAL_BASE, BINARY_BASE],
        "neighbours_decimal": neighbours_decimal,
        "neighbours_hex_levels": neighbours_hex,
        "neighbours_18": [_frac_str(Fraction(lo18) * u18, WORD_DECIMALS), _frac_str(Fraction(lo18 + 1) * u18, WORD_DECIMALS)],
        "fraction_18": float(f18),
        "correctly_rounded": correctly_rounded_18(truth),
        "bits": bits,
        "neighbours_hex": [hex_fraction(lob, FRACTION_BITS), hex_fraction(hib, FRACTION_BITS)],
        "neighbours_128": [readings[lob], readings[hib]],
        "fraction_128": float(fb),
        "nearest_hex": hex_fraction(nearest_b, FRACTION_BITS),
        "nearest_128": readings[nearest_b],
        "word18": word18,
        "tick_128": f"{tick_b:.1e}",
        "fp127": fp127,
    }


class Grid(DeckScene):
    SECTIONS = ("human", "decimal", "binary", "half", "snaps")

    # ------------------------------------------------------------ geometry --
    def x_of(self, v: Fraction, unit: Fraction) -> float:
        """Screen x of value v when one tick is `unit`, the exact value at x = 0."""
        return float((v - self.t) / unit) * L

    def level(self, unit: Fraction, minor: int):
        """A grid with one tick per `unit` and `minor` faint ticks between.
        Returns (group, majors {m: tick}, minors) with m the tick index
        relative to floor(t / unit)."""
        base = floor(self.t / unit)
        line = Line([-HALF, Y_LINE, 0], [HALF, Y_LINE, 0], color=Palette.FAINT, stroke_width=2, stroke_opacity=0.9)
        majors, minors = {}, VGroup()
        span = int(HALF / L) + 2
        for m in range(-span, span + 1):
            x = self.x_of((base + m) * unit, unit)
            majors[m] = Line([x, Y_LINE - 0.14, 0], [x, Y_LINE + 0.14, 0], color=Palette.FAINT, stroke_width=2)
            for j in range(1, minor):
                xm = x + j * L / minor
                minors.add(Line([xm, Y_LINE - 0.14, 0], [xm, Y_LINE + 0.14, 0], color=Palette.FAINT, stroke_width=2, stroke_opacity=0.35))
        return VGroup(line, *majors.values(), minors), majors, minors, base

    def tick_label(self, x: float, text: str, colour=Palette.FAINT, size: float | None = None, justify: int = 0):
        """A complete value under a tick; justify −1 ends it at the tick,
        +1 starts it there (the two neighbours' labels face away from each
        other so the long ones never collide). Long labels set smaller."""
        if size is None:
            size = 22 if len(text) <= 24 else 18
        t = digits(text, size, colour).next_to([x, Y_LINE - 0.14, 0], DOWN, buff=0.2)
        if justify:
            t.shift(RIGHT * justify * (t.width / 2 - 0.12))
        return t

    def neighbour_labels(self, majors, texts):
        """The two ticks either side of the exact value, each labelled with
        its complete value, facing outward."""
        return VGroup(*[self.tick_label(majors[m].get_x(), texts[m], justify=2 * m - 1) for m in (0, 1)])

    def counter(self, text: str):
        c = markup(text, 24, Palette.MUTED)
        c.move_to([6.4 - c.width / 2, LABEL_Y, 0])
        return c

    def header(self, value: str, precision: str, lit: int, size: float = 26):
        """e^40 across the top: the value complete (on two lines when it
        runs to 80 decimals), labelled with its precision, its first `lit`
        decimals resolved (lit)."""
        eq = markup("e<sup>40</sup> =", size, Palette.TEXT)
        num = digits(wrap_decimals(value), size, Palette.FAINT, line_spacing=0.7)
        tag = words(precision, SIZE_CAPTION, Palette.FAINT)
        if num.height < 0.5:
            g = VGroup(eq, num, tag).arrange(RIGHT, buff=0.22)
        else:
            # two lines: the tag sits after the shorter second line, so the header stays between the two marks
            g = VGroup(eq, num).arrange(RIGHT, buff=0.22)
            k = len(wrap_decimals(value).partition("\n")[0]) + 1  # the first line's glyphs and the newline's zero-width placeholder
            tag.next_to(num[k:], RIGHT, buff=0.22)
            g.add(tag)
        g.move_to([0, 3.2 if num.height < 0.5 else 3.15, 0])
        self.light(num, lit)
        return g

    def light(self, num, n_decimals: int):
        """Light the digits of e^40 a grid of this fineness resolves."""
        k = min(len(num), self.int_len + 1 + max(0, n_decimals))
        num[:k].set_color(Palette.TEXT)
        num[k:].set_color(Palette.FAINT)

    def dive(self, grids, labels_of, counter_of, decimals_of, num, counter, run_time, pause, settle=0.1):
        """Stretch through a list of (unit, minor) levels. grids[i] is the
        current level; each step stretches it `minor`-fold about the exact
        value so its minor ticks become the next level's major ticks."""
        g, majors, minors, base = self.level(*grids[0])
        self.add(g)
        lbls = labels_of(0, majors, base)
        self.play(FadeIn(lbls, run_time=0.3), FadeIn(minors, run_time=0.3))
        for i in range(1, len(grids)):
            unit, minor = grids[i - 1]
            g2, majors2, minors2, base2 = self.level(*grids[i])
            minors2.set_opacity(0)
            self.play(
                g.animate(rate_func=ease_in_out_cubic if i in (1, len(grids) - 1) else linear).stretch(minor, 0, about_point=ORIGIN),
                FadeOut(lbls, run_time=min(0.3, run_time)),
                run_time=run_time,
            )
            self.remove(g, counter)
            counter = counter_of(i)
            self.add(g2, counter)
            self.light(num, decimals_of(i))
            lbls = labels_of(i, majors2, base2)
            self.play(minors2.animate.set_opacity(0.35), FadeIn(lbls, run_time=settle), run_time=settle)
            g, majors, minors, base = g2, majors2, minors2, base2
            if pause:
                self.wait(pause)
        return g, majors, minors, base, lbls, counter

    # ------------------------------------------------------------- the scene --
    def construct(self):
        n = numbers()
        self.t = Fraction(n["truth"])
        self.int_len = len(n["truth"].partition(".")[0])
        self.section(0)
        # the chrome: the caption, the header (e^40 to 18 decimals, the slide's title line)
        # and the grid's counter are on the first frame; the header goes to 80 decimals
        # when the binary dive needs them and the counter reads each level as it comes
        self.caption_now(CAPTION)
        head = self.header(n["correctly_rounded"], f"(to {WORD_DECIMALS} decimals)", 0)
        num = head[1]
        self.fix(head)
        counter = self.counter("one tick = 1")
        self.fix(counter)
        self.wait(0.3)

        # human scale: the integers around e^40, the exact value between two of them

        def dec_labels(i, majors, base):
            k = i  # decimals at level i: the two neighbours, complete at k decimals
            return self.neighbour_labels(majors, {m: _frac_str(Fraction(base + m, 10**k), k) for m in (0, 1)})

        dec_grids = [(Fraction(1, 10**k), 10) for k in range(0, WORD_DECIMALS + 1)]
        g, majors, minors, base = self.level(*dec_grids[0])
        self.play(Create(g[0], run_time=0.7))
        self.play(LaggedStart(*[Create(majors[m]) for m in sorted(majors)], lag_ratio=0.06, run_time=0.8))
        self.remove(g)
        dot = Circle(radius=0.11, color=Palette.EXACT, fill_color=Palette.EXACT, fill_opacity=1, stroke_width=0).move_to([0, Y_LINE + 2.0, 0])
        self.play(FadeIn(dot, run_time=0.2))
        self.play(dot.animate(rate_func=ease_out_cubic).move_to([0, Y_LINE, 0]), run_time=0.6)
        mark = markup("e<sup>40</sup>", 24, Palette.TEXT).next_to(dot, UP, buff=0.22)
        self.play(FadeIn(mark, run_time=0.3))

        # layer 1: ten at a time, down to a wei
        self.section(1)
        g, majors, minors, base, lbls, counter = self.dive(
            dec_grids,
            dec_labels,
            lambda i: self.counter(f"one tick = 10<sup>−{i}</sup>"),
            lambda i: i,
            num,
            counter,
            run_time=0.28,
            pause=0.0,
        )
        layer1 = markup(f"the 18-decimal libraries' grid: one tick = 10<sup>−{WORD_DECIMALS}</sup>, a whole wei", 24, Palette.GOLD)
        layer1.move_to([-6.4 + layer1.width / 2, LABEL_Y, 0])
        self.play(FadeIn(layer1, shift=RIGHT * 0.1, run_time=0.5))
        self.wait(1.2)
        wad = dot.copy()
        self.add(wad)
        to18 = 1 if n["fraction_18"] >= 0.5 else 0
        line18 = GridLine((0, 1, 1), length=L).move_to([L / 2 - n["fraction_18"] * L, Y_LINE, 0])  # the two neighbours, as a GridLine for snap()
        self.play(snap(wad, line18, to18, Palette.EXACT, run_time=0.6))
        wad_lbl = markup(f"the WAD answer: {n['correctly_rounded']}", 22, Palette.GOLD).next_to(wad, UP, buff=0.7)
        self.play(FadeIn(wad_lbl, run_time=0.3))

        # layer 2: by powers of two, down to FP127's grid; the header goes as far as the truth does
        self.section(2, hold=2.0)
        self.play(FadeOut(wad, run_time=0.4), FadeOut(wad_lbl, run_time=0.4), FadeOut(layer1, run_time=0.4))
        bits = n["bits"]

        def bit_labels(i, majors, base):
            return self.neighbour_labels(majors, {m: hex_fraction(base + m, bits[i]) for m in (0, 1)})

        def bit_counter(i):
            return self.counter(f"one tick = 2<sup>−{bits[i]}</sup> · the ticks' fractions in hex")

        bit_grids = [(Fraction(1, 2**j), 2**BIT_STEP) for j in bits]
        # the first binary level replaces the 10^-18 grid: a crossfade, the ticks nearly coincide
        g2, majors2, minors2, base2 = self.level(*bit_grids[0])
        lbls2 = bit_labels(0, majors2, base2)
        counter2 = bit_counter(0)
        head2 = self.header(n["truth"], f"(to {EXPANSION_DECIMALS} decimals)", WORD_DECIMALS, size=19)
        self.play(FadeOut(g, run_time=0.5), FadeOut(lbls, run_time=0.3), FadeIn(g2, run_time=0.5), FadeIn(lbls2, run_time=0.4), FadeOut(head, run_time=0.4), FadeIn(head2, run_time=0.4))
        self.remove(counter)
        self.add(counter2)
        num = head2[1]
        self.wait(0.3)

        # dive() builds its own first level; hand it the list from here
        self.remove(g2, lbls2)
        g, majors, minors, base, lbls, counter = self.dive(
            bit_grids,
            bit_labels,
            bit_counter,
            lambda i: int(bits[i] * log10(2)),
            num,
            counter2,
            run_time=0.18,
            pause=0.0,
            settle=0.07,
        )
        layer2 = markup(f"FP127's grid: one tick = 2<sup>−{FRACTION_BITS}</sup> ≈ {n['tick_128'].split('e')[0]} × 10<sup>−{abs(int(n['tick_128'].split('e')[1]))}</sup>", 24, Palette.EMERALD)
        layer2.move_to([-6.4 + layer2.width / 2, LABEL_Y, 0])
        self.play(FadeIn(layer2, shift=RIGHT * 0.1, run_time=0.5))
        # the two words' decimal readings, to as many decimals as the truth has: they part at the 39th
        lo_x, hi_x = majors[0].get_x(), majors[1].get_x()
        lo_r, hi_r = n["neighbours_128"]
        readings = VGroup()
        for name, r in (("the lower word reads", lo_r), ("the upper word reads", hi_r)):
            readings.add(VGroup(words(f"{name}, to {EXPANSION_DECIMALS} decimals,", 17, Palette.MUTED), digits(wrap_decimals(r), 17, Palette.TEXT, line_spacing=0.7)).arrange(RIGHT, buff=0.2, aligned_edge=UP))
        readings.arrange(DOWN, buff=0.14, aligned_edge=LEFT).move_to([0, -1.5, 0])
        self.play(FadeIn(readings, run_time=0.5))

        # half a unit, then the three snaps on this grid
        self.section(3, hold=2.0)
        mid = (lo_x + hi_x) / 2
        mid_mark = DashedLine([mid, Y_LINE - 0.3, 0], [mid, Y_LINE + 0.3, 0], color=Palette.FAINT, stroke_width=1.5, dash_length=0.035)
        line_b = GridLine((0, 1, 1), length=L).move_to([mid, Y_LINE, 0])
        self.play(Create(mid_mark, run_time=0.3))
        half = measure(line_b, 0, 0.5, "half a unit", scale=0.7, drop=1.08)
        self.play(FadeIn(half, shift=UP * 0.04, run_time=0.4))

        self.section(4, hold=1.5)
        near = 1 if n["fraction_128"] >= 0.5 else 0
        far = 1 - near
        d1 = dot.copy()
        self.add(d1)
        self.play(snap(d1, line_b, near, Palette.EXACT, run_time=0.6))
        self.wait(1.0)
        d2 = dot.copy()
        self.add(d2)
        a_wrong = direction(line_b, n["fraction_128"], far, Palette.WRONG, lift=0.45)
        self.play(Create(a_wrong, run_time=0.3))
        self.play(snap(d2, line_b, far, Palette.WRONG, run_time=0.6))
        self.wait(1.2)
        d3 = dot.copy()
        self.add(d3)
        a_right = direction(line_b, n["fraction_128"], near, Palette.CORRECT, lift=0.75)
        self.play(Create(a_right, run_time=0.3))
        glow = halo(line_b.n2p(near), Palette.CORRECT)
        self.play(snap(d3, line_b, near, Palette.CORRECT, run_time=0.6), FadeIn(glow, run_time=0.6))
        self.bring_to_front(d1, d3)
        # FP127's word: its hex fraction complete, and what it is to 18 decimals
        word_lbl = VGroup(
            VGroup(words("FP127's word", 22, Palette.EMERALD), digits(n["nearest_hex"], 20, Palette.TEXT)).arrange(RIGHT, buff=0.25),
            VGroup(words(f"to {WORD_DECIMALS} decimals", 20, Palette.MUTED), digits(n["word18"], 20, Palette.TEXT)).arrange(RIGHT, buff=0.25),
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        word_lbl.next_to(d3, UP, buff=0.95)
        if word_lbl.get_right()[0] > 6.4:
            word_lbl.shift(RIGHT * (6.4 - word_lbl.get_right()[0]))
        if word_lbl.get_left()[0] < -6.4:
            word_lbl.shift(RIGHT * (-6.4 - word_lbl.get_left()[0]))
        tick = check_mark(Palette.CORRECT, size=0.26).next_to(word_lbl[0], RIGHT, buff=0.3)
        self.play(FadeIn(word_lbl, run_time=0.4), Create(tick, run_time=0.3))
        self.wait(1.0)
        footer = markup(FOOTER, 26, Palette.BODY)
        footer.move_to([0, -2.75, 0])
        self.play(FadeIn(footer, shift=UP * 0.08, run_time=0.6))
        self.close()

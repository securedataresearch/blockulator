"""Slide 4, "Computers round": the grid, from human scale down to one word.

The edit pass's shape (talk/briefs/edit-pass.md, row 4): one idea per
section, each beat removes its own labels, the poster holds the
conclusion. The motion is the dive: the number line starts at human
scale (one tick = 1, the two integers e^40 lies between) and is
stretched about the exact e^40, tenfold eighteen times, down to the
18-decimal grid (one tick = 10^-18, a whole wei), then sixteen-fold by
powers of two (2^-60, 2^-64, ...) down to BL127's grid, one tick =
2^-128. At every level the two ticks either side of e^40 carry their
complete values on two rows, each row ending under its own tick (the
decimal levels in decimals, the binary levels as their fraction words in
hex, 32 hex digits at the end: no ellipsis anywhere). One short label on
the lattice says the tick; it changes as the dive goes. No frame carries
the decimal labels and the binary labels together.

Four sections, one per click: human (the integers around e^40); decimal
(the whole dive, decimal then binary; the old "binary" section, cue "",
is merged here); half (half a unit between a tick and the midpoint);
snaps (the far tick in red, its direction drawn and crossed; then the
nearer tick in emerald with a halo; the one hero line). The last frame
holds as the slide.

The zoom is the grid stretching about the exact value, not the camera
moving: a camera zoom of 10^39 would run out of floating-point positions
long before 2^-128, and a stretch leaves every stroke hairline. Every
position is computed with Fraction from the truth and converted to a
screen offset only at the end.

Numbers from docs/benchmarks/edges.json: op exp, probe ["40"]: .truth
(extended to 80 decimals by vocab.truth80, its first 24 decimals asserted
against the probe's) and .cells.bl127.value (asserted to be the nearer
2^-128 neighbour, and to 18 decimals the correctly rounded value). The
neighbours at every decimal and binary level and the fraction of a unit
the exact value sits at on BL127's grid are computed here and exposed in
numbers(). Provenance is in the slide's notes.
"""

from __future__ import annotations

from fractions import Fraction
from math import floor

from manim import (
    DOWN,
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

from vocab import SIZE_BODY, SIZE_HERO, TRUTH_DECIMALS, DeckScene, GridLine, Palette, correctly_rounded_18, cross_mark, digits, direction, halo, markup, measure, probe, snap, truth80, words

OP, ARG = "exp", "40"
WORD_DECIMALS = 18  # the decimal dive ends here: one tick = 10^-18
FRACTION_BITS = 128  # the binary dive ends here: one tick = 2^-128 (BL127)
BIT_START, BIT_STEP = 60, 4  # the binary dive: 2^-60 (≈ 0.87e-18, next to the wei grid), 2^-64, …
HEX_DIGITS = FRACTION_BITS // 4  # a 128-bit fraction word is 32 hex digits
EXPANSION_DECIMALS = TRUTH_DECIMALS  # the truth as far as truth80() goes (80); only asserted, never drawn
DECIMAL_BASE, BINARY_BASE = 10, 2
TITLE = "Computers round"
L = 1.3  # screen units per tick
X0, Y_LINE = 3.95, 0.75  # the exact e^40 on screen: right of centre, so each neighbour's row can end under its tick
SAFE_X = 6.4  # the 5% safe area
HALF = config.frame_width / 2 + 0.5
ROW_GAP = 0.6  # the two neighbours' rows under the line
HERO = ("a 256-bit word holds 2<sup>256</sup> numbers;", "e<sup>40</sup> is not one of them")  # the one hero line, on two centred lines at HERO (one line does not fit)

# the digit-bearing fixed strings on the slide, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    "e<sup>40</sup>": "V9",
    HERO[0]: "V8",
    HERO[1]: "V8",  # V8: a 256-bit word holds finitely many numbers and most exact results fall between two of them; e^40 is not a 2^-128 multiple (V9 truth)
}


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
    assert len(truth.partition(".")[2]) == EXPANSION_DECIMALS and truth.startswith(p["truth"][:-1]), truth
    bits = [BIT_START + BIT_STEP * i for i in range((FRACTION_BITS - BIT_START) // BIT_STEP + 1)]
    # the neighbours at every level: the two ticks either side of e^40, complete at that level
    decimal_levels = list(range(WORD_DECIMALS + 1))
    neighbours_decimal = [[_frac_str(Fraction(floor(t * 10**k) + m, 10**k), k) for m in (0, 1)] for k in decimal_levels]
    neighbours_hex = [[hex_fraction(floor(t * 2**b) + m, b) for m in (0, 1)] for b in bits]
    # BL127's grid: the 2^-128 neighbours and where e^40 sits between them
    ub = Fraction(1, 2**FRACTION_BITS)
    lob = floor(t / ub)
    fb = t / ub - lob
    assert 0 < fb < 1, fb  # e^40 is not one of them
    nearest_b = lob + 1 if fb >= Fraction(1, 2) else lob
    bl127 = p["cells"]["bl127"]["value"]
    # BL127's word, rounded to the probe's decimals as the cell prints it, is the nearer neighbour
    assert _frac_round(Fraction(nearest_b) * ub, len(bl127.partition(".")[2])) == bl127, (bl127, nearest_b)
    assert _frac_round(Fraction(nearest_b) * ub, WORD_DECIMALS) == correctly_rounded_18(truth)  # and to 18 decimals the closest 18-decimal value
    return {
        "truth": truth,
        "decimal_levels": decimal_levels,
        "bases": [DECIMAL_BASE, BINARY_BASE],
        "neighbours_decimal": neighbours_decimal,
        "bits": bits,
        "neighbours_hex_levels": neighbours_hex,
        "fraction_128": float(fb),
        "nearest_hex": hex_fraction(nearest_b, FRACTION_BITS),
        "bl127": bl127,
    }


class Grid(DeckScene):
    SECTIONS = ("human", "decimal", "half", "snaps")

    # ------------------------------------------------------------ geometry --
    def x_of(self, v: Fraction, unit: Fraction) -> float:
        """Screen x of value v when one tick is `unit`, the exact value at X0."""
        return X0 + float((v - self.t) / unit) * L

    def level(self, unit: Fraction, minor: int):
        """A grid with one tick per `unit` and `minor` faint ticks between.
        Returns (group, majors {m: tick}, minors, base) with m the tick
        index relative to floor(t / unit)."""
        base = floor(self.t / unit)
        line = Line([-HALF, Y_LINE, 0], [HALF, Y_LINE, 0], color=Palette.FAINT, stroke_width=2, stroke_opacity=0.9)
        majors, minors = {}, VGroup()
        for m in range(-int((HALF + X0) / L) - 2, int((HALF - X0) / L) + 3):
            x = self.x_of((base + m) * unit, unit)
            majors[m] = Line([x, Y_LINE - 0.14, 0], [x, Y_LINE + 0.14, 0], color=Palette.FAINT, stroke_width=2)
            for j in range(1, minor):
                xm = x + j * L / minor
                minors.add(Line([xm, Y_LINE - 0.14, 0], [xm, Y_LINE + 0.14, 0], color=Palette.FAINT, stroke_width=2, stroke_opacity=0.35))
        return VGroup(line, *majors.values(), minors), majors, minors, base

    def neighbour_rows(self, majors, texts):
        """The two ticks either side of the exact value, each labelled with
        its complete value on its own row, the row ending under its tick
        (the lower neighbour on the first row), a faint drop from the tick
        to its row. A row that would leave the safe area moves right (only
        on the dive's passing levels; the held ones end under their ticks)."""
        g = VGroup()
        for m in (0, 1):
            x = majors[m].get_x()
            y = Y_LINE - 0.62 - m * ROW_GAP
            row = digits(texts[m], SIZE_BODY, Palette.BODY)
            row.move_to([x + 0.13 - row.width / 2, y, 0])
            if row.get_left()[0] < -SAFE_X:
                row.shift(RIGHT * (-SAFE_X - row.get_left()[0]))
            drop = Line([x, Y_LINE - 0.2, 0], [x, row.get_top()[1] + 0.06, 0], color=Palette.FAINT, stroke_width=1.5, stroke_opacity=0.6)
            g.add(VGroup(row, drop))
        return g

    def unit(self, text: str):
        """The lattice's one label: what one tick is, above the line at the left."""
        u = markup(text, SIZE_BODY, Palette.MUTED)
        u.move_to([-SAFE_X + u.width / 2, Y_LINE + 0.75, 0])
        return u

    def dive(self, first, grids, labels_of, unit_of, run_time, settle):
        """Stretch through a list of (unit, minor) levels from `first`, the
        level already on screen (group, majors, minors, base, labels, unit
        label). Each step stretches the grid `minor`-fold about the exact
        value so its minor ticks become the next level's major ticks; the
        labels leave as it stretches and the next level's arrive."""
        g, majors, minors, base, lbls, u = first
        for i in range(1, len(grids)):
            unit, minor = grids[i - 1]
            g2, majors2, minors2, base2 = self.level(*grids[i])
            minors2.set_opacity(0)
            self.play(
                g.animate(rate_func=ease_in_out_cubic if i in (1, len(grids) - 1) else linear).stretch(minor, 0, about_point=[X0, Y_LINE, 0]),
                FadeOut(lbls, run_time=min(0.3, run_time)),
                run_time=run_time,
            )
            self.remove(g, u)
            u = unit_of(i)
            self.add(g2, u)
            lbls = labels_of(i, majors2, base2)
            self.play(minors2.animate.set_opacity(0.35), FadeIn(lbls, run_time=settle), run_time=settle)
            g, majors, minors, base = g2, majors2, minors2, base2
        return g, majors, minors, base, lbls, u

    # ------------------------------------------------------------- the scene --
    def construct(self):
        n = numbers()
        self.t = Fraction(n["truth"])
        bits = n["bits"]

        # chrome: the title, on the first frame
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.wait(0.3)

        # human: the integers around e^40, the exact value between two of them
        def dec_labels(k, majors, base):
            return self.neighbour_rows(majors, {m: _frac_str(Fraction(base + m, 10**k), k) for m in (0, 1)})

        def dec_unit(k):
            return self.unit("one tick = 1" if k == 0 else f"one tick = 10<sup>−{k}</sup>")

        dec_grids = [(Fraction(1, 10**k), 10) for k in n["decimal_levels"]]
        g, majors, minors, base = self.level(*dec_grids[0])
        self.play(Create(g[0], run_time=0.7))
        self.play(LaggedStart(*[Create(majors[m]) for m in sorted(majors)], lag_ratio=0.06, run_time=0.8))
        self.remove(*majors.values(), g[0])
        minors.set_opacity(0)
        self.add(g)
        dot = Circle(radius=0.11, color=Palette.EXACT, fill_color=Palette.EXACT, fill_opacity=1, stroke_width=0).move_to([X0, Y_LINE + 2.0, 0])
        self.play(FadeIn(dot, run_time=0.2))
        self.play(dot.animate(rate_func=ease_out_cubic).move_to([X0, Y_LINE, 0]), run_time=0.6)
        mark = markup("e<sup>40</sup>", SIZE_BODY, Palette.TEXT).move_to([X0, Y_LINE + 0.62, 0])
        self.play(FadeIn(mark, run_time=0.3))
        self.wait(0.4)
        lbls = dec_labels(0, majors, base)
        u = dec_unit(0)
        self.play(FadeIn(lbls, run_time=0.5), FadeIn(u, run_time=0.5))

        # decimal: ten at a time down to a wei, then by powers of two down to BL127's grid
        self.section(1, hold=2.0)
        self.play(minors.animate.set_opacity(0.35), run_time=0.3)
        self.bring_to_front(dot)
        g, majors, minors, base, lbls, u = self.dive((g, majors, minors, base, lbls, u), dec_grids, dec_labels, dec_unit, run_time=0.28, settle=0.1)
        self.bring_to_front(dot)
        self.wait(1.4)

        def bit_labels(i, majors, base):
            return self.neighbour_rows(majors, {m: hex_fraction(base + m, bits[i]) for m in (0, 1)})

        def bit_unit(i):
            return self.unit(f"one tick = 2<sup>−{bits[i]}</sup>")

        bit_grids = [(Fraction(1, 2**b), 2**BIT_STEP) for b in bits]
        # the first binary level replaces the 10^-18 grid: a crossfade (the ticks nearly coincide); the decimal labels leave first
        g2, majors2, minors2, base2 = self.level(*bit_grids[0])
        lbls2, u2 = bit_labels(0, majors2, base2), bit_unit(0)
        self.play(FadeOut(lbls, run_time=0.4), FadeOut(u, run_time=0.4))
        self.play(FadeOut(g, run_time=0.5), FadeIn(g2, run_time=0.5))
        self.bring_to_front(dot)
        self.play(FadeIn(lbls2, run_time=0.4), FadeIn(u2, run_time=0.4))
        self.wait(0.6)
        g, majors, minors, base, lbls, u = self.dive((g2, majors2, minors2, base2, lbls2, u2), bit_grids, bit_labels, bit_unit, run_time=0.18, settle=0.07)
        self.bring_to_front(dot)
        assert [r[0].text for r in lbls] == n["neighbours_hex_levels"][-1], [r[0].text for r in lbls]

        # half: the midpoint between the two words, and half a unit from the lower one to it
        self.section(2, hold=2.0)
        lo_x, hi_x = majors[0].get_x(), majors[1].get_x()
        mid = (lo_x + hi_x) / 2
        mid_mark = DashedLine([mid, Y_LINE - 0.3, 0], [mid, Y_LINE + 0.3, 0], color=Palette.FAINT, stroke_width=1.5, dash_length=0.035)
        line_b = GridLine((0, 1, 1), length=L).move_to([mid, Y_LINE, 0])  # the two neighbours, as a GridLine for measure() and snap()
        self.play(Create(mid_mark, run_time=0.3))
        bracket = measure(line_b, 0, 0.5, None, drop=-1.1)
        half = words("half a unit", SIZE_BODY, Palette.MUTED).next_to(bracket, UP, buff=0.14)
        self.play(Create(bracket, run_time=0.4), FadeIn(half, shift=DOWN * 0.04, run_time=0.4))

        # snaps: the far tick (wrong, red, its direction drawn and crossed), then the nearer (correct, emerald, halo)
        self.section(3, hold=1.5)
        f = n["fraction_128"]
        near = 1 if f >= 0.5 else 0
        far = 1 - near
        wrong = dot.copy()
        self.add(wrong)
        a_wrong = direction(line_b, f, far, Palette.WRONG, lift=0.3)
        self.play(Create(a_wrong, run_time=0.3))
        self.play(snap(wrong, line_b, far, Palette.WRONG, run_time=0.6))
        cross = cross_mark(Palette.WRONG, size=0.26).move_to(line_b.n2p(far) + UP * 0.62)
        self.play(Create(cross, run_time=0.3))
        self.wait(1.4)
        self.play(FadeOut(VGroup(wrong, a_wrong, cross), run_time=0.5))
        right = dot.copy()
        self.add(right)
        glow = halo(line_b.n2p(near), Palette.CORRECT)
        # the exact value shrinks to a point so the emerald word beside it shows
        self.play(snap(right, line_b, near, Palette.CORRECT, run_time=0.6), FadeIn(glow, run_time=0.6), dot.animate(run_time=0.6).scale(0.5))
        self.bring_to_front(right, dot)
        self.wait(0.8)
        hero = VGroup(*[markup(h, SIZE_HERO, Palette.TEXT) for h in HERO]).arrange(DOWN, buff=0.22).move_to([0, -2.4, 0])
        self.play(FadeIn(hero, shift=UP * 0.08, run_time=0.6))
        self.close()

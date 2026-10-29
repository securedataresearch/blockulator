"""Slide 4, "Computers round": the grid, from human scale down to one word.

The number line starts at human scale: integer ticks around e^40 (the
integer part …985, …986, labels in JetBrains Mono), the exact e^40 marked
between them, its digits across the top. Then the dive, in two layers.

Layer 1, decimal: the grid is stretched tenfold eighteen times (one tick =
10^-1, 10^-2, …, the counter ticking, the digits across the top lighting
as each power of ten resolves them, the two neighbouring ticks relabelled
at every level) until one tick = 10^-18, a whole wei: the 18-decimal
libraries' grid. The exact value sits between …034804 and …034805 and
snaps to the nearer: the WAD answer.

Layer 2, binary: the dive goes on, now by powers of two (one tick =
2^-60, 2^-64, …, sixteen-fold each step) to 2^-128 ≈ 2.9 × 10^-39: FP127's
grid. The exact e^40 sits between two adjacent 128-bit fraction words,
shown by their last bits and their decimal expansions. On this grid the
three snaps play: to the nearer tick (white, rounding itself), the far
way (WRONG, red, its direction drawn), the right way (CORRECT, emerald,
with a halo), labelled "FP127's word" with FP127's own value. A bracket
measures half a unit. Footer: a 256-bit word holds 2^256 numbers; e^40 is
not one of them. About 95 s; it ends on the bare background so the deck
can loop it.

The zoom is the grid stretching about the exact value, not the camera
moving: a camera zoom of 10^39 would run out of floating-point positions
long before 2^-128, and a stretch leaves every stroke hairline. Every
position is computed with Fraction from the truth and converted to a
screen offset only at the end.

Numbers from docs/benchmarks/edges.json: op exp, probe ["40"]: .truth and
.cells.fp127.value; the 18-decimal neighbours, the correctly rounded
18-decimal value, the binary neighbours floor(t · 2^128) and + 1, their
bits and expansions, and the fraction of a unit the exact value sits at
on each grid are computed here (vocab helpers, Fraction) and exposed in
numbers().
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from math import floor, log10

from manim import (
    DOWN,
    ORIGIN,
    RIGHT,
    UP,
    Circle,
    Create,
    DashedLine,
    FadeIn,
    FadeOut,
    Group,
    Indicate,
    LaggedStart,
    Line,
    VGroup,
    config,
)
from manim.utils.rate_functions import ease_in_out_cubic, ease_out_cubic, linear

from vocab import DeckScene, GridLine, Palette, check_mark, correctly_rounded_18, digits, direction, halo, markup, measure, probe, snap, words

OP, ARG = "exp", "40"
WORD_DECIMALS = 18  # layer 1 ends here: one tick = 10^-18
FRACTION_BITS = 128  # layer 2 ends here: one tick = 2^-128 (FP127)
BIT_START, BIT_STEP = 60, 4  # layer 2 dives 2^-60, 2^-64, … (2^-60 ≈ 0.87e-18, next to the wei grid)
SHOW_BITS = 8  # last bits of each neighbouring word shown
EXPANSION_DECIMALS = 42  # decimals of the neighbours' expansions shown
L = 1.3  # screen units per tick
Y_LINE = 0.35
HALF = config.frame_width / 2 + 0.5


def _frac_str(q: Fraction, places: int) -> str:
    """q as a decimal string with exactly `places` decimals (truncated)."""
    scaled = q.numerator * 10**places // q.denominator
    whole, frac = divmod(scaled, 10**places)
    return f"{whole}.{frac:0{places}d}" if places else str(whole)


def numbers() -> dict:
    p = probe(OP, ARG)
    truth = p["truth"]
    t = Fraction(truth)
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
    expansions = {w: _frac_str(Fraction(w) * ub, EXPANSION_DECIMALS) for w in (lob, hib)}
    fp127 = p["cells"]["fp127"]["value"]
    # FP127's word, printed to the probe's decimals, is the nearer neighbour
    assert expansions[nearest_b].startswith(fp127) or _frac_str(Fraction(nearest_b) * ub, len(fp127.partition(".")[2])) == fp127, (fp127, expansions[nearest_b])
    with localcontext() as ctx:
        ctx.prec = 30
        tick_b = Decimal(ub.numerator) / Decimal(ub.denominator)
    return {
        "truth": truth,
        "levels_decimal": WORD_DECIMALS,
        "neighbours_18": [_frac_str(Fraction(lo18) * u18, WORD_DECIMALS), _frac_str(Fraction(lo18 + 1) * u18, WORD_DECIMALS)],
        "fraction_18": float(f18),
        "correctly_rounded": correctly_rounded_18(truth),
        "bits": [BIT_START + BIT_STEP * i for i in range((FRACTION_BITS - BIT_START) // BIT_STEP + 1)],
        "neighbours_bits": [bin(lob)[-SHOW_BITS:], bin(hib)[-SHOW_BITS:]],
        "neighbours_128": [expansions[lob], expansions[hib]],
        "fraction_128": float(fb),
        "nearest_128": expansions[nearest_b],
        "tick_128": f"{tick_b:.1e}",
        "fp127": fp127,
    }


class Grid(DeckScene):
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

    def tick_label(self, x: float, text: str, colour=Palette.FAINT, size=22, justify: int = 0):
        """A label under a tick; justify −1 ends it at the tick, +1 starts it
        there (the two neighbours' long labels at the final levels)."""
        t = digits(text, size, colour).next_to([x, Y_LINE - 0.14, 0], DOWN, buff=0.2)
        if justify:
            t.shift(RIGHT * justify * (t.width / 2 - 0.12))
        return t

    def counter(self, text: str):
        c = markup(text, 24, Palette.MUTED)
        c.move_to([6.4 - c.width / 2, 2.55, 0])
        return c

    def light(self, header, n_decimals: int):
        """Light the digits of e^40 a grid of this fineness resolves."""
        k = min(len(header) - 1, self.int_len + 1 + max(0, n_decimals))
        header[:k].set_color(Palette.TEXT)
        header[k:].set_color(Palette.FAINT)

    def dive(self, grids, labels_of, counter_of, decimals_of, header, counter, run_time, pause):
        """Stretch through a list of (unit, minor) levels. grids[i] is the
        current level; each step stretches it `minor`-fold about the exact
        value so its minor ticks become the next level's major ticks."""
        g, majors, minors, base = self.level(*grids[0])
        self.add(g)
        lbls = labels_of(0, majors, base)
        self.play(FadeIn(lbls, run_time=0.4), FadeIn(minors, run_time=0.4))
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
            self.light(header, decimals_of(i))
            lbls = labels_of(i, majors2, base2)
            self.play(minors2.animate.set_opacity(0.35), FadeIn(lbls, run_time=0.25), run_time=0.25)
            g, majors, minors, base = g2, majors2, minors2, base2
            if pause:
                self.wait(pause)
        return g, majors, minors, base, lbls, counter

    # ------------------------------------------------------------- the scene --
    def construct(self):
        n = numbers()
        self.t = Fraction(n["truth"])
        self.int_len = len(n["truth"].partition(".")[0])
        self.wait(0.5)
        self.play(self.caption("docs/benchmarks/edges.json · exp(40)"))

        # human scale: the integers around e^40, the exact value between two of them
        header = digits(n["truth"] + "…", 28, Palette.FAINT).move_to([0, 3.2, 0])
        e_lbl = markup("e<sup>40</sup>", 28, Palette.TEXT).next_to(header, DOWN, buff=0.25)
        self.light(header, 0)
        self.play(FadeIn(header, run_time=0.8))

        def dec_labels(i, majors, base):
            k = i  # decimals at level i
            out = VGroup()
            if k == 0:
                for m, tick in majors.items():
                    if abs(tick.get_x()) < 6.2:
                        out.add(self.tick_label(tick.get_x(), "…" + str(base + m)[-3:]))
            else:
                last = k == WORD_DECIMALS
                for m in (0, 1):
                    s = _frac_str(Fraction(base + m, 10**k), k)
                    out.add(self.tick_label(majors[m].get_x(), "…" + s[-(6 if last else 4):], justify=(2 * m - 1) if last else 0))
            return out

        dec_grids = [(Fraction(1, 10**k), 10) for k in range(0, WORD_DECIMALS + 1)]
        counter = self.counter("one tick = 1")
        g, majors, minors, base = self.level(*dec_grids[0])
        self.play(Create(g[0], run_time=1.0))
        self.play(LaggedStart(*[Create(majors[m]) for m in sorted(majors)], lag_ratio=0.06, run_time=1.2))
        self.add(counter)
        self.remove(g)
        dot = Circle(radius=0.11, color=Palette.EXACT, fill_color=Palette.EXACT, fill_opacity=1, stroke_width=0).move_to([0, Y_LINE + 2.0, 0])
        self.play(FadeIn(dot, run_time=0.3))
        self.play(dot.animate(rate_func=ease_out_cubic).move_to([0, Y_LINE, 0]), run_time=0.8)
        mark = markup("e<sup>40</sup>", 24, Palette.TEXT).next_to(dot, UP, buff=0.22)
        self.play(FadeIn(mark, run_time=0.4))
        self.wait(2.5)

        # layer 1: ten at a time, down to a wei
        g, majors, minors, base, lbls, counter = self.dive(
            dec_grids,
            dec_labels,
            lambda i: self.counter(f"one tick = 10<sup>−{i}</sup>"),
            lambda i: i,
            header,
            counter,
            run_time=0.7,
            pause=0.15,
        )
        layer1 = markup(f"the 18-decimal libraries' grid: one tick = 10<sup>−{WORD_DECIMALS}</sup>, a whole wei", 24, Palette.GOLD)
        layer1.move_to([-6.4 + layer1.width / 2, 2.55, 0])
        self.play(FadeIn(layer1, shift=RIGHT * 0.1, run_time=0.6))
        self.wait(2.5)
        wad = dot.copy()
        self.add(wad)
        to18 = 1 if n["fraction_18"] >= 0.5 else 0
        line18 = GridLine((0, 1, 1), length=L).move_to([L / 2 - n["fraction_18"] * L, Y_LINE, 0])  # the two neighbours, as a GridLine for snap()
        self.play(snap(wad, line18, to18, Palette.EXACT, run_time=1.0))
        wad_lbl = markup(f"the WAD answer: …{n['correctly_rounded'][-6:]}", 22, Palette.GOLD).next_to(wad, UP, buff=0.7)
        self.play(FadeIn(wad_lbl, run_time=0.4))
        self.wait(4.0)
        self.play(FadeOut(wad, run_time=0.5), FadeOut(wad_lbl, run_time=0.5), FadeOut(layer1, run_time=0.5))

        # layer 2: by powers of two, down to FP127's grid
        bits = n["bits"]

        def bit_labels(i, majors, base):
            j = bits[i]
            out = VGroup()
            last = j == FRACTION_BITS
            for m in (0, 1):
                b = bin(base + m)
                out.add(self.tick_label(majors[m].get_x(), "…" + b[-(SHOW_BITS if last else 4):], justify=(2 * m - 1) if last else 0))
            return out

        bit_grids = [(Fraction(1, 2**j), 2**BIT_STEP) for j in bits]
        # the first binary level replaces the 10^-18 grid: a crossfade, the ticks nearly coincide
        g2, majors2, minors2, base2 = self.level(*bit_grids[0])
        lbls2 = bit_labels(0, majors2, base2)
        counter2 = self.counter(f"one tick = 2<sup>−{bits[0]}</sup>")
        self.play(FadeOut(g, run_time=0.8), FadeOut(lbls, run_time=0.4), FadeIn(g2, run_time=0.8), FadeIn(lbls2, run_time=0.6))
        self.remove(counter)
        self.add(counter2)
        self.wait(0.6)

        # dive() builds its own first level; hand it the list from here
        self.remove(g2, lbls2)
        g, majors, minors, base, lbls, counter = self.dive(
            bit_grids,
            bit_labels,
            lambda i: self.counter(f"one tick = 2<sup>−{bits[i]}</sup>"),
            lambda i: int(bits[i] * log10(2)),
            header,
            counter2,
            run_time=0.45,
            pause=0.0,
        )
        layer2 = markup(f"FP127's grid: one tick = 2<sup>−{FRACTION_BITS}</sup> ≈ {n['tick_128'].split('e')[0]} × 10<sup>−{abs(int(n['tick_128'].split('e')[1]))}</sup>", 24, Palette.EMERALD)
        layer2.move_to([-6.4 + layer2.width / 2, 2.55, 0])
        self.play(FadeIn(layer2, shift=RIGHT * 0.1, run_time=0.6))
        # the two words, as bits above and expansions below
        lo_x, hi_x = majors[0].get_x(), majors[1].get_x()
        exp_lo = digits(n["neighbours_128"][0] + "…", 19, Palette.MUTED)
        exp_hi = digits(n["neighbours_128"][1] + "…", 19, Palette.MUTED)
        exp_lo.move_to([0, -1.25, 0])
        exp_hi.move_to([0, -1.6, 0])
        k = next((i for i, (a, b) in enumerate(zip(n["neighbours_128"][0], n["neighbours_128"][1])) if a != b), None)
        if k is not None:
            exp_lo[k:].set_color(Palette.TEXT)
            exp_hi[k:].set_color(Palette.TEXT)
        self.play(FadeIn(exp_lo, run_time=0.6), FadeIn(exp_hi, run_time=0.6))
        self.wait(3.0)

        # half a unit, then the three snaps on this grid
        mid = (lo_x + hi_x) / 2
        mid_mark = DashedLine([mid, Y_LINE - 0.3, 0], [mid, Y_LINE + 0.3, 0], color=Palette.FAINT, stroke_width=1.5, dash_length=0.035)
        line_b = GridLine((0, 1, 1), length=L).move_to([mid, Y_LINE, 0])
        self.play(Create(mid_mark, run_time=0.5))
        half = measure(line_b, 0, 0.5, "half a unit", scale=0.7, drop=1.08)
        self.play(FadeIn(half, shift=UP * 0.04, run_time=0.6))
        self.wait(2.5)

        near = 1 if n["fraction_128"] >= 0.5 else 0
        far = 1 - near
        d1 = dot.copy()
        self.add(d1)
        self.play(snap(d1, line_b, near, Palette.EXACT, run_time=1.0))
        self.wait(2.0)
        d2 = dot.copy()
        self.add(d2)
        a_wrong = direction(line_b, n["fraction_128"], far, Palette.WRONG, lift=0.45)
        self.play(Create(a_wrong, run_time=0.5))
        self.play(snap(d2, line_b, far, Palette.WRONG, run_time=1.0))
        self.wait(2.5)
        d3 = dot.copy()
        self.add(d3)
        a_right = direction(line_b, n["fraction_128"], near, Palette.CORRECT, lift=0.75)
        self.play(Create(a_right, run_time=0.5))
        glow = halo(line_b.n2p(near), Palette.CORRECT)
        self.play(snap(d3, line_b, near, Palette.CORRECT, run_time=1.0), FadeIn(glow, run_time=1.0))
        self.bring_to_front(d1, d3)
        word_lbl = markup(f"<span foreground='{Palette.EMERALD}'>FP127's word</span>  {n['fp127']}…", 22, Palette.TEXT)
        word_lbl.next_to(d3, UP, buff=0.95)
        if word_lbl.get_right()[0] > 6.6:
            word_lbl.shift(RIGHT * (6.6 - word_lbl.get_right()[0]))
        if word_lbl.get_left()[0] < -6.6:
            word_lbl.shift(RIGHT * (-6.6 - word_lbl.get_left()[0]))
        tick = check_mark(Palette.CORRECT, size=0.26).next_to(word_lbl, RIGHT, buff=0.3)
        self.play(FadeIn(word_lbl, run_time=0.5), Create(tick, run_time=0.4))
        self.wait(2.0)
        footer = markup("a 256-bit word holds 2<sup>256</sup> numbers; e<sup>40</sup> is not one of them", 26, Palette.BODY)
        footer.move_to([0, -2.55, 0])
        self.play(FadeIn(footer, shift=UP * 0.08, run_time=0.8))
        self.wait(6.0)

        # out, so the loop can restart on the bare background
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not self._caption]), run_time=0.9))
        self.wait(0.4)

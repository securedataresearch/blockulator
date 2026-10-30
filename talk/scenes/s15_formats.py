"""Slide 15, "Two formats": two ways to spend 256 bits.

A word of 256 bits draws across the slide, cell by cell (bit_bar); the
title already counts it. It is partitioned twice. First as BL127, fixed
point: sign 1, integer 127, fraction 128 (emerald), each field bracketed
and counted under the bar, the one label "BL127 · fixed point", and under
it the grid of representable values, uniform ticks in emerald, unlabelled
(the speaker says the 38 digits and the known range). Then the same bits as
BL19, floating point: sign 1, exponent 19 (violet), fraction 236; the
label becomes "BL19 · floating point" and the grid turns into the
magnitude axis, from
about 10^−78,913 to about 10^78,913, and a 71-digit window (white, BL19's
family colour on this slide, with a glow) slides along it: the left end,
the middle, the right end. Last a value slides past the last tick and
becomes a red cross: overflow reverts.

Four sections, one per click: bar; fixed; floating; revert. The last
frame holds as the slide.

No benchmark JSON carries these: they are format constants (claims K1–K4).
numbers() derives every drawn figure from the bit widths: the field sizes
and their sum, the digit counts floor(bits · log10 2), BL127's range
2^127 to two significant digits (Fraction/Decimal, for the notes), BL19's
extremes 2^−262142 and (2 − 2^−236) · 2^262144 (mpmath) as powers of ten;
check.py recomputes each by a second route (Decimal). The window's stops
are illustrative positions on a log axis; no digits at the stops.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from math import floor, log10

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Create,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    Rectangle,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_in_cubic, ease_in_out_cubic, ease_out_cubic

from vocab import (
    ROW_COLOUR,
    BL19_EXPONENT_BITS,
    BL19_FRACTION_BITS,
    BL127_FRACTION_BITS,
    SIZE_BODY,
    DeckScene,
    GridLine,
    Palette,
    bit_bar,
    cross_mark,
    glow_line,
    libs,
    markup,
    words,
)

WORD_BITS = 256
SIGN_BITS = 1
RADIX, BASE = 2, 10
BL127_INTEGER_BITS = WORD_BITS - SIGN_BITS - BL127_FRACTION_BITS  # 127
BL19_MIN_EXP = -(2 ** (BL19_EXPONENT_BITS - 1) - 2)  # E = 1: 2^(1 − bias) = 2^−262142 (K3)
BL19_MAX_EXP = 2 ** (BL19_EXPONENT_BITS - 1)  # E = all ones is finite (K4): (2 − 2^−236) · 2^262144
RANGE_DIGITS = 1  # "about ±1.7 × 10^38": the mantissa to one decimal

TITLE = f"Two ways to spend {WORD_BITS} bits"
REVERT = "overflow reverts"

# the digit-bearing fixed strings on the slide: none (every digit is a value of numbers())
STEP = "Step 1. Write a superior math library. Then write another."  # the manual's step line, the slide's first beat
LITERALS: dict[str, str] = {STEP: "user 2026-10-30 outline"}

# layout (scene units; the frame is 14.22 × 8, the safe area ±6.4 × ±3.6)
BAR_WIDTH = 12.6  # ≈ 1,700 px: 256 cells at 6.6 px with 0.5 px gaps
Y_BAR = 1.95
Y_LABEL = 0.45  # the format's one label, centred under the counts
LABEL_SIZE = 40  # the format's name, alone under the bar
WINDOW_SIZE = 36  # the 71-digit window's label
Y_AXIS = -1.3
Y_ENDS = -1.8
Y_REVERT = -2.8
BRACKET_DROP, BRACKET_BUFF = 0.2, 0.06  # the field brackets under the bar and their counts
X_SAFE = 6.4
AXIS_TICKS = (0, 8, 1)
GRID_TICKS = (0, 24, 1)  # BL127's uniform grid: 24 units across the same width (no label: the speaker says it)
AXIS_LENGTH = 11.2  # the overflow cross lands past the right end, inside the safe area
WINDOW = 1.2  # the 71-digit window, in axis ticks (illustrative)
STOPS = (0.0, 0.5, 1.0)  # the window's stops: the left end, the middle, the right end of the axis
HUES = ROW_COLOUR["s15"]  # the fields: sign TEXT; BL127's integer SAPPHIRE, fraction EMERALD; BL19's exponent VIOLET, fraction TEXT


def _power_of_ten(x: Decimal) -> int:
    """floor(log10 x) for a positive Decimal: the exponent of its leading digit."""
    return x.adjusted()


def numbers() -> dict:
    lib = libs()
    assert SIGN_BITS + BL127_INTEGER_BITS + BL127_FRACTION_BITS == WORD_BITS
    assert SIGN_BITS + BL19_EXPONENT_BITS + BL19_FRACTION_BITS == WORD_BITS
    significand = BL19_FRACTION_BITS + 1  # the hidden bit
    bl127_digits = floor(BL127_FRACTION_BITS * log10(RADIX))
    bl19_digits = floor(significand * log10(RADIX))
    # BL127's range: ±2^127 (less one unit at the top), to one decimal of its leading power of ten
    top = Fraction(RADIX) ** BL127_INTEGER_BITS
    with localcontext() as ctx:
        ctx.prec = 60
        d = Decimal(top.numerator) / Decimal(top.denominator)
        range_exp = _power_of_ten(d)
        mantissa = str((d.scaleb(-range_exp)).quantize(Decimal(1).scaleb(-RANGE_DIGITS), rounding=ROUND_HALF_UP))
    # BL19's extremes, as powers of ten: the smallest normal 2^−262142, the largest finite (2 − 2^−236) · 2^262144
    import mpmath

    mpmath.mp.dps = 40
    smallest = mpmath.mpf(RADIX) ** BL19_MIN_EXP
    largest = (RADIX - mpmath.mpf(RADIX) ** -BL19_FRACTION_BITS) * mpmath.mpf(RADIX) ** BL19_MAX_EXP
    min_exp = int(mpmath.floor(mpmath.log10(smallest)))
    max_exp = int(mpmath.floor(mpmath.log10(largest)))
    assert min_exp == -max_exp, (min_exp, max_exp)  # the axis is symmetric about 1

    def power(e: int) -> str:
        return f"{BASE}<sup>{'−' if e < 0 else ''}{abs(e):,}</sup>"

    return {
        "word_bits": WORD_BITS,
        "radix": RADIX,
        "base": BASE,
        "bl127": {
            "label": lib["bl127"]["label"],
            "sign": SIGN_BITS,
            "integer": BL127_INTEGER_BITS,
            "fraction": BL127_FRACTION_BITS,
            "digits": bl127_digits,
            "range_mantissa": mantissa,
            "range_exp": range_exp,
            "grid_end_exp": BL127_FRACTION_BITS,
        },
        "bl19": {
            "label": lib["bl19"]["label"],
            "sign": SIGN_BITS,
            "exponent": BL19_EXPONENT_BITS,
            "fraction": BL19_FRACTION_BITS,
            "significand": significand,
            "digits": bl19_digits,
            "min_exp": min_exp,
            "max_exp": max_exp,
        },
        "strings": {
            "bl127_label": f"{lib['bl127']['label']} · fixed point",
            "bl19_label": f"{lib['bl19']['label']} · floating point",
            "bl19_digits": f"about {bl19_digits} digits at every magnitude",
            "bl19_min": f"about {power(min_exp)}",
            "bl19_max": f"about {power(max_exp)}",
        },
    }


def clamp_x(mobj, lo: float = -X_SAFE, hi: float = X_SAFE):
    """Keep a mobject inside the safe area horizontally."""
    if mobj.get_left()[0] < lo:
        mobj.shift(RIGHT * (lo - mobj.get_left()[0]))
    if mobj.get_right()[0] > hi:
        mobj.shift(LEFT * (mobj.get_right()[0] - hi))
    return mobj


class Formats(DeckScene):
    SECTIONS = ("step", "bar", "fixed", "floating", "revert")

    def sweep(self, cells: VGroup, colour: str, run_time: float):
        """A field's colour sweeping along its cells, left to right."""
        return LaggedStart(*[c.animate.set_color(colour) for c in cells], lag_ratio=min(0.3, 1.0 / max(1, len(cells))), run_time=run_time)

    def window(self, axis: GridLine, at: float) -> VGroup:
        """The 71-digit window at fraction `at` of the axis: a white bracket
        stood over the axis, its label above, a glow on the axis beneath
        (the hero; add the glow behind the axis)."""
        lo = AXIS_TICKS[0] + at * (AXIS_TICKS[1] - AXIS_TICKS[0] - WINDOW)
        hi = lo + WINDOW
        lift = 0.28
        pa, pb = axis.n2p(lo) + UP * lift, axis.n2p(hi) + UP * lift
        cap = DOWN * 0.07
        bar = Line(pa, pb, color=Palette.TEXT, stroke_width=2)
        caps = VGroup(Line(pa - cap, pa + cap, color=Palette.TEXT, stroke_width=2), Line(pb - cap, pb + cap, color=Palette.TEXT, stroke_width=2))
        pane = Rectangle(width=(pb - pa)[0], height=lift + 0.14, color=Palette.TEXT, fill_color=Palette.TEXT, fill_opacity=0.1, stroke_width=0).move_to((pa + pb) / 2 + DOWN * (lift / 2))
        label = words(self.n["strings"]["bl19_digits"], WINDOW_SIZE, Palette.TEXT).next_to(bar, UP, buff=0.12)
        clamp_x(label)
        glow = glow_line([axis.n2p(lo), axis.n2p(hi)], Palette.TEXT, width=22, opacity=0.35)
        g = VGroup(glow, pane, bar, caps, label)
        g.glow, g.bracket, g.label = glow, VGroup(pane, bar, caps), label
        return g

    def construct(self):
        self.n = n = numbers()
        s = n["strings"]
        self.section(0)
        self.step(STEP)  # the step line alone, then its kicker above the title
        self.section(1)
        # the chrome, on the first frame: the title (it counts the bits)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.wait(0.3)

        # the word: 256 cells draw across the slide
        bar = bit_bar(WORD_BITS, BAR_WIDTH).move_to([0, Y_BAR, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.08) for c in bar.cells], lag_ratio=0.004, run_time=1.6))

        # fixed point: sign, integer, fraction, bracketed and counted; the one label
        self.section(2, hold=1.0)
        f = n["bl127"]
        edges127 = (0, f["sign"], f["sign"] + f["integer"], WORD_BITS)
        colours127 = (HUES["sign"], HUES["bl127_integer"], HUES["bl127_fraction"])
        label127 = words(s["bl127_label"], LABEL_SIZE, Palette.EMERALD).move_to([0, Y_LABEL, 0])
        self.play(FadeIn(label127, shift=UP * 0.1, run_time=0.5))
        brackets = VGroup()
        for i in range(3):
            a, b = edges127[i], edges127[i + 1]
            br = bar.bracket(a, b, str(b - a), colours127[i], drop=BRACKET_DROP, buff=BRACKET_BUFF)
            brackets.add(br)
            self.play(self.sweep(bar.cells[a:b], colours127[i], run_time=0.25 + 0.45 * (b - a) / WORD_BITS), Create(br[0], run_time=0.3), Create(br[1], run_time=0.3))
            self.play(FadeIn(br.text, shift=DOWN * 0.06, run_time=0.25))
        # the uniform grid, emerald, under its glow: the same spacing everywhere, a known range
        grid = GridLine(GRID_TICKS, length=AXIS_LENGTH, colour=Palette.EMERALD).move_to([0, Y_AXIS, 0])
        grid_glow = glow_line([grid.get_left(), grid.get_right()], Palette.EMERALD)
        self.add(grid_glow)
        self.play(Create(grid, run_time=1.0), FadeIn(grid_glow, run_time=1.0))

        # floating point: the same bits as sign, exponent, fraction; the magnitude axis and the window
        self.section(3, hold=1.0)
        g = n["bl19"]
        label19 = words(s["bl19_label"], LABEL_SIZE, Palette.TEXT).move_to([0, Y_LABEL, 0])
        self.play(FadeOut(label127, shift=UP * 0.1, run_time=0.4))
        self.play(FadeIn(label19, shift=UP * 0.1, run_time=0.5))
        edges19 = (0, g["sign"], g["sign"] + g["exponent"], WORD_BITS)
        colours19 = (HUES["sign"], HUES["bl19_exponent"], HUES["bl19_fraction"])
        for i in range(3):
            a, b = edges19[i], edges19[i + 1]
            # the 19-bit exponent's count ends at its bracket's right, clear of the sign's
            br = bar.bracket(a, b, str(b - a), colours19[i], drop=BRACKET_DROP, buff=BRACKET_BUFF, align=1 if i == 1 else 0)
            self.play(
                self.sweep(bar.cells[a:b], colours19[i], run_time=0.25 + 0.45 * (b - a) / WORD_BITS),
                Transform(brackets[i], br, run_time=0.4),
            )
        axis = GridLine(AXIS_TICKS, length=AXIS_LENGTH, colour=Palette.FAINT).move_to([0, Y_AXIS, 0])
        lo_lbl = clamp_x(markup(s["bl19_min"], SIZE_BODY, Palette.MUTED).move_to([axis.get_left()[0], Y_ENDS, 0]))
        hi_lbl = clamp_x(markup(s["bl19_max"], SIZE_BODY, Palette.MUTED).move_to([axis.get_right()[0], Y_ENDS, 0]))
        # the uniform grid becomes the magnitude axis: one tick per stretch of orders of magnitude
        self.play(Transform(grid, axis, run_time=1.0), FadeOut(grid_glow, run_time=0.6))
        self.remove(grid)
        self.add(axis)
        self.play(LaggedStart(FadeIn(lo_lbl, shift=UP * 0.06), FadeIn(hi_lbl, shift=UP * 0.06), lag_ratio=0.3, run_time=0.6))
        # the hero: the 71-digit window, at the left end, the middle, the right end
        win = self.window(axis, STOPS[0])
        self.add(win.glow)
        self.bring_to_back(win.glow)
        self.play(FadeIn(win.glow, run_time=0.5), Create(win.bracket, run_time=0.5))
        self.play(FadeIn(win.label, shift=UP * 0.06, run_time=0.4))
        self.wait(0.8)
        for at in STOPS[1:]:
            target = self.window(axis, at)
            self.play(Transform(win, target, rate_func=ease_in_out_cubic), run_time=0.9)
            self.bring_to_back(win[0])
            self.wait(0.8)

        # overflow: a value slides past the last tick and reverts
        self.section(4, hold=0.4)
        mid = (AXIS_TICKS[0] + AXIS_TICKS[1]) / 2
        dot = axis.dot_at(mid, Palette.TEXT)
        self.play(FadeIn(dot, scale=0.3, run_time=0.4))
        self.wait(0.3)
        past = axis.n2p(AXIS_TICKS[1]) + RIGHT * 0.4
        self.play(dot.animate(rate_func=ease_in_cubic).move_to(past), run_time=1.3)
        cross = cross_mark(Palette.WRONG, size=0.4).move_to(past)
        assert cross.get_right()[0] <= X_SAFE, cross.get_right()[0]
        self.play(Transform(dot, cross, rate_func=ease_out_cubic), run_time=0.35)
        self.wait(0.4)
        revert = words(REVERT, LABEL_SIZE, Palette.WRONG).move_to([0, Y_REVERT, 0]).align_to([X_SAFE, 0, 0], RIGHT)
        self.play(FadeIn(revert, shift=UP * 0.08, run_time=0.5))
        self.close()

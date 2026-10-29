"""Slide 15, "Two formats": two ways to spend 256 bits.

A word of 256 bits draws across the slide, cell by cell (bit_bar). It is
partitioned twice. First as FP127, fixed point: sign 1, integer 127,
fraction 128 (emerald, the hero of the section), each field bracketed
and counted; under it the grid of representable values with uniform
ticks, emerald, its last unit bracketed "the grid ends at 2^−128";
about 38 digits of fraction in a known range, about ±1.7 × 10^38. Then
the same bits as FP19, floating point: sign 1, exponent 19 (sapphire),
fraction 236 stored, the significand 237 bits with the hidden bit; the
grid becomes the magnitude axis, from about 10^−78,913 to about
10^78,913 with 1 in the middle, and a 71-digit window (white, FP19's
family colour on this slide, with a glow) slides along it: the left
end, the middle, the right end. A value slides past the last tick and
becomes a red cross: no NaN, no infinity, overflow reverts. The closing
line names the rule.

Five sections, one per click: bar; fixed; floating; revert; rule. The
last frame holds as the slide.

No benchmark JSON carries these: they are format constants (claims K1–K4,
E9). numbers() derives every drawn figure from the bit widths: the field
sizes and their sum, the digit counts floor(bits · log10 2), FP127's range
2^127 to two significant digits (Fraction/Decimal), FP19's extremes
2^−262142 and (2 − 2^−236) · 2^262144 (mpmath) as powers of ten; check.py
recomputes each by a second route (Decimal). The window's stops are
illustrative positions on a log axis; no digits at the stops.
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
    FP19_EXPONENT_BITS,
    FP19_FRACTION_BITS,
    FP127_FRACTION_BITS,
    SIZE_BODY,
    SIZE_CAPTION,
    DeckScene,
    GridLine,
    Palette,
    bit_bar,
    cross_mark,
    digits,
    glow_bar,
    glow_line,
    libs,
    markup,
    measure,
    words,
)

WORD_BITS = 256
SIGN_BITS = 1
RADIX, BASE = 2, 10
FP127_INTEGER_BITS = WORD_BITS - SIGN_BITS - FP127_FRACTION_BITS  # 127
FP19_MIN_EXP = -(2 ** (FP19_EXPONENT_BITS - 1) - 2)  # E = 1: 2^(1 − bias) = 2^−262142 (K3)
FP19_MAX_EXP = 2 ** (FP19_EXPONENT_BITS - 1)  # E = all ones is finite (K4): (2 − 2^−236) · 2^262144
RANGE_DIGITS = 1  # "about ±1.7 × 10^38": the mantissa to one decimal

TITLE = f"Two ways to spend {WORD_BITS} bits"
CAPTION = "contracts/src/fp127/README.md · contracts/src/fp19/README.md"
IEEE = "laid out as IEEE 754 binary256"
REVERT = "no NaN, no infinity: overflow reverts"
CLOSE = "known range: fixed point · many orders of magnitude: floating point"

# the digit-bearing fixed strings on the slide, each with its claim id (research_notes/talk/verify-E.md, verify-K.md)
LITERALS = {
    IEEE: "E9",  # binary256 is IEEE 754's; the encoding differs (K4), so "laid out as", never "is"
}

# layout (scene units; the frame is 14.22 × 8, the safe area ±6.4 × ±3.6)
BAR_WIDTH = 12.6  # ≈ 1,700 px: 256 cells at 6.6 px with 0.5 px gaps
Y_TITLE = 3.3
Y_OVER = 2.65
Y_BAR = 2.2
Y_ROWS = (0.95, 0.45, -0.05)
Y_AXIS = -1.3
Y_ENDS = -1.75
Y_REVERT = -2.3
Y_CLOSE = -2.9
BRACKET_DROP, BRACKET_BUFF = 0.2, 0.06  # the field brackets under the bar and their counts
X_SAFE = 6.4
AXIS_TICKS = (0, 8, 1)
AXIS_LENGTH = 11.8
GRID_TICKS = (0, 24, 1)  # FP127's uniform grid: 24 units across the same width
WINDOW = 1.2  # the 71-digit window, in axis ticks (illustrative)
STOPS = (0.0, 0.5, 1.0)  # the window's stops: the left end, the middle, the right end of the axis
CLOSE_SIZE = 30  # the closing line is 13.4 units wide at SIZE_BODY, wider than the safe area; 30 fits


def _power_of_ten(x: Decimal) -> int:
    """floor(log10 x) for a positive Decimal: the exponent of its leading digit."""
    return x.adjusted()


def numbers() -> dict:
    lib = libs()
    assert SIGN_BITS + FP127_INTEGER_BITS + FP127_FRACTION_BITS == WORD_BITS
    assert SIGN_BITS + FP19_EXPONENT_BITS + FP19_FRACTION_BITS == WORD_BITS
    significand = FP19_FRACTION_BITS + 1  # the hidden bit
    fp127_digits = floor(FP127_FRACTION_BITS * log10(RADIX))
    fp19_digits = floor(significand * log10(RADIX))
    # FP127's range: ±2^127 (less one unit at the top), to one decimal of its leading power of ten
    top = Fraction(RADIX) ** FP127_INTEGER_BITS
    with localcontext() as ctx:
        ctx.prec = 60
        d = Decimal(top.numerator) / Decimal(top.denominator)
        range_exp = _power_of_ten(d)
        mantissa = str((d.scaleb(-range_exp)).quantize(Decimal(1).scaleb(-RANGE_DIGITS), rounding=ROUND_HALF_UP))
    # FP19's extremes, as powers of ten: the smallest normal 2^−262142, the largest finite (2 − 2^−236) · 2^262144
    import mpmath

    mpmath.mp.dps = 40
    smallest = mpmath.mpf(RADIX) ** FP19_MIN_EXP
    largest = (RADIX - mpmath.mpf(RADIX) ** -FP19_FRACTION_BITS) * mpmath.mpf(RADIX) ** FP19_MAX_EXP
    min_exp = int(mpmath.floor(mpmath.log10(smallest)))
    max_exp = int(mpmath.floor(mpmath.log10(largest)))
    assert min_exp == -max_exp, (min_exp, max_exp)  # the axis is symmetric about 1

    def power(e: int) -> str:
        return f"{BASE}<sup>{'−' if e < 0 else ''}{abs(e):,}</sup>"

    return {
        "word_bits": WORD_BITS,
        "radix": RADIX,
        "base": BASE,
        "fp127": {
            "label": lib["fp127"]["label"],
            "sign": SIGN_BITS,
            "integer": FP127_INTEGER_BITS,
            "fraction": FP127_FRACTION_BITS,
            "digits": fp127_digits,
            "range_mantissa": mantissa,
            "range_exp": range_exp,
            "grid_end_exp": FP127_FRACTION_BITS,
        },
        "fp19": {
            "label": lib["fp19"]["label"],
            "sign": SIGN_BITS,
            "exponent": FP19_EXPONENT_BITS,
            "fraction": FP19_FRACTION_BITS,
            "significand": significand,
            "digits": fp19_digits,
            "min_exp": min_exp,
            "max_exp": max_exp,
        },
        "strings": {
            "bits": f"{WORD_BITS} bits",
            "fp127_fields": f"{SIGN_BITS} · {FP127_INTEGER_BITS} · {FP127_FRACTION_BITS}",
            "fp127_names": "sign · integer · fraction",
            "fp127_digits": f"about {fp127_digits} digits of fraction",
            "fp127_range": f"about ±{mantissa} × {power(range_exp)}",
            "fp127_grid_end": f"the grid ends at {RADIX}<sup>−{FP127_FRACTION_BITS}</sup>",
            "fp127_label": f"{lib['fp127']['label']} · fixed point",
            "fp19_fields": f"{SIGN_BITS} · {FP19_EXPONENT_BITS} · {FP19_FRACTION_BITS}",
            "fp19_names": f"sign · exponent · fraction ({FP19_FRACTION_BITS} stored)",
            "fp19_significand": f"significand {significand} bits with the hidden bit",
            "fp19_digits": f"about {fp19_digits} digits at every magnitude",
            "fp19_min": f"about {power(min_exp)}",
            "fp19_max": f"about {power(max_exp)}",
            "fp19_label": f"{lib['fp19']['label']} · floating point",
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
    SECTIONS = ("bar", "fixed", "floating", "revert", "rule")

    def sweep(self, cells: VGroup, colour: str, run_time: float):
        """A field's colour sweeping along its cells, left to right."""
        return LaggedStart(*[c.animate.set_color(colour) for c in cells], lag_ratio=min(0.3, 1.0 / max(1, len(cells))), run_time=run_time)

    def row(self, i: int, *parts, buff: float = 0.6) -> VGroup:
        """Mobjects in a row at Y_ROWS[i], from the left edge of the safe area."""
        return VGroup(*parts).arrange(RIGHT, buff=buff).move_to([0, Y_ROWS[i], 0]).align_to([-X_SAFE, 0, 0], LEFT)

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
        label = words(self.n["strings"]["fp19_digits"], SIZE_BODY, Palette.TEXT).next_to(bar, UP, buff=0.1)
        clamp_x(label)
        glow = glow_line([axis.n2p(lo), axis.n2p(hi)], Palette.TEXT, width=22, opacity=0.35)
        g = VGroup(glow, pane, bar, caps, label)
        g.glow, g.bracket, g.label = glow, VGroup(pane, bar, caps), label
        return g

    def construct(self):
        self.n = n = numbers()
        s = n["strings"]
        self.section(0)
        self.wait(0.3)
        title = words(TITLE, SIZE_BODY, Palette.TEXT).move_to([0, Y_TITLE, 0]).align_to([-X_SAFE, 0, 0], LEFT)
        self.play(FadeIn(title, shift=RIGHT * 0.1, run_time=0.5), self.caption(CAPTION))

        # the word: 256 cells draw across the slide, then are counted
        bar = bit_bar(WORD_BITS, BAR_WIDTH).move_to([0, Y_BAR, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.08) for c in bar.cells], lag_ratio=0.004, run_time=1.6))
        over = bar.bracket(0, WORD_BITS, s["bits"], Palette.TEXT, above=True, drop=0.22)
        self.play(Create(over[0], run_time=0.5), Create(over[1], run_time=0.3))
        self.play(FadeIn(over.text, shift=UP * 0.06, run_time=0.4))

        # fixed point: sign, integer, fraction; the uniform grid; 38 digits in a known range
        self.section(1, hold=1.0)
        f = n["fp127"]
        edges127 = (0, f["sign"], f["sign"] + f["integer"], WORD_BITS)
        colours127 = (Palette.TEXT, Palette.MUTED, Palette.EMERALD)
        label127 = words(s["fp127_label"], SIZE_BODY, Palette.EMERALD)
        fields127 = digits(s["fp127_fields"], SIZE_BODY, Palette.TEXT)
        names127 = words(s["fp127_names"], SIZE_BODY, Palette.MUTED)
        row_a = self.row(0, label127, fields127, names127)
        self.play(FadeIn(label127, shift=RIGHT * 0.1, run_time=0.5))
        brackets127 = VGroup()
        for i in range(3):
            a, b = edges127[i], edges127[i + 1]
            br = bar.bracket(a, b, str(b - a), colours127[i], drop=BRACKET_DROP, buff=BRACKET_BUFF)
            brackets127.add(br)
            self.play(self.sweep(bar.cells[a:b], colours127[i], run_time=0.25 + 0.45 * (b - a) / WORD_BITS), Create(br[0], run_time=0.3), Create(br[1], run_time=0.3))
            self.play(FadeIn(br.text, shift=DOWN * 0.06, run_time=0.25))
        self.play(FadeIn(fields127, shift=RIGHT * 0.1, run_time=0.4), FadeIn(names127, shift=RIGHT * 0.1, run_time=0.4))
        self.wait(0.6)
        # the grid: uniform ticks, emerald, with its glow; the last unit bracketed
        grid = GridLine(GRID_TICKS, length=AXIS_LENGTH, colour=Palette.EMERALD).move_to([0, Y_AXIS, 0])
        grid_glow = glow_line([grid.get_left(), grid.get_right()], Palette.EMERALD)
        self.add(grid_glow)
        self.play(Create(grid, run_time=1.0), FadeIn(grid_glow, run_time=1.0))
        end = measure(grid, GRID_TICKS[1] - 1, GRID_TICKS[1], s["fp127_grid_end"], drop=0.3, colour=Palette.EMERALD, use_markup=True)
        clamp_x(end[2], hi=grid.get_right()[0])
        self.play(Create(end[0], run_time=0.3), Create(end[1], run_time=0.3))
        self.play(FadeIn(end[2], shift=UP * 0.06, run_time=0.4))
        self.wait(0.6)
        digits127 = words(s["fp127_digits"], SIZE_BODY, Palette.EMERALD)
        range127 = markup(s["fp127_range"], SIZE_BODY, Palette.TEXT)
        row_b = self.row(1, digits127, range127, buff=0.8)
        self.play(FadeIn(digits127, shift=RIGHT * 0.1, run_time=0.5))
        self.wait(0.4)
        self.play(FadeIn(range127, shift=RIGHT * 0.1, run_time=0.5))

        # floating point: the same bits as sign, exponent, fraction; the magnitude axis and the window
        self.section(2, hold=1.0)
        g = n["fp19"]
        self.play(FadeOut(VGroup(row_a, row_b, grid, grid_glow, end), run_time=0.5))
        edges19 = (0, g["sign"], g["sign"] + g["exponent"], WORD_BITS)
        colours19 = (Palette.TEXT, Palette.SAPPHIRE, Palette.TEXT)
        label19 = words(s["fp19_label"], SIZE_BODY, Palette.TEXT)
        fields19 = digits(s["fp19_fields"], SIZE_BODY, Palette.TEXT)
        row_a2 = self.row(0, label19, fields19)
        ieee = words(IEEE, SIZE_CAPTION, Palette.FAINT).move_to([0, Y_ROWS[0], 0]).align_to([X_SAFE, 0, 0], RIGHT)
        self.play(FadeIn(label19, shift=RIGHT * 0.1, run_time=0.5))
        for i in range(3):
            a, b = edges19[i], edges19[i + 1]
            # the 19-bit exponent's count ends at its bracket's right, clear of the sign's
            br = bar.bracket(a, b, str(b - a), colours19[i], drop=BRACKET_DROP, buff=BRACKET_BUFF, align=1 if i == 1 else 0)
            self.play(
                self.sweep(bar.cells[a:b], colours19[i], run_time=0.25 + 0.45 * (b - a) / WORD_BITS),
                Transform(brackets127[i], br, run_time=0.4),
            )
        names19 = words(s["fp19_names"], SIZE_BODY, Palette.MUTED)
        signif19 = words(s["fp19_significand"], SIZE_BODY, Palette.MUTED)
        self.row(1, names19)
        self.row(2, signif19)
        self.play(FadeIn(fields19, shift=RIGHT * 0.1, run_time=0.4), FadeIn(ieee, run_time=0.4))
        self.play(FadeIn(names19, shift=RIGHT * 0.1, run_time=0.4))
        self.play(FadeIn(signif19, shift=RIGHT * 0.1, run_time=0.4))
        axis = GridLine(AXIS_TICKS, length=AXIS_LENGTH, colour=Palette.FAINT).move_to([0, Y_AXIS, 0])
        lo_lbl = clamp_x(markup(s["fp19_min"], SIZE_BODY, Palette.MUTED).move_to([axis.get_left()[0], Y_ENDS, 0]))
        hi_lbl = clamp_x(markup(s["fp19_max"], SIZE_BODY, Palette.MUTED).move_to([axis.get_right()[0], Y_ENDS, 0]))
        mid = (AXIS_TICKS[0] + AXIS_TICKS[1]) / 2
        one = digits(str(1), SIZE_BODY, Palette.MUTED).move_to([axis.n2p(mid)[0], Y_ENDS, 0])
        self.play(Create(axis, run_time=1.0))
        self.play(LaggedStart(FadeIn(lo_lbl, shift=UP * 0.06), FadeIn(one, shift=UP * 0.06), FadeIn(hi_lbl, shift=UP * 0.06), lag_ratio=0.3, run_time=0.7))
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
        self.section(3, hold=0.4)
        dot = axis.dot_at(mid, Palette.TEXT)
        self.play(FadeIn(dot, scale=0.3, run_time=0.4))
        self.wait(0.3)
        past = axis.n2p(AXIS_TICKS[1]) + RIGHT * 0.4
        self.play(dot.animate(rate_func=ease_in_cubic).move_to(past), run_time=1.3)
        cross = cross_mark(Palette.WRONG, size=0.4).move_to(past)
        self.play(Transform(dot, cross, rate_func=ease_out_cubic), run_time=0.35)
        self.wait(0.4)
        revert = words(REVERT, SIZE_BODY, Palette.WRONG).move_to([0, Y_REVERT, 0]).align_to([X_SAFE, 0, 0], RIGHT)
        self.play(FadeIn(revert, shift=UP * 0.08, run_time=0.5))

        # the rule
        self.section(4, hold=1.0)
        close = words(CLOSE, CLOSE_SIZE, Palette.TEXT).move_to([0, Y_CLOSE, 0])
        glow = glow_bar(close, Palette.EMERALD, pad=0.1)
        self.add(glow)
        self.bring_to_back(glow)
        self.play(FadeIn(glow, run_time=0.6), FadeIn(close, shift=UP * 0.08, run_time=0.6))
        self.close()

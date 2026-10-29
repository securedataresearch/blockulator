"""Slide 16, "What correct costs": Ziv's technique, and what it costs.

Two coins sized by gas, area for area: MUL (5 gas) is a speck beside the
512-by-256-bit division (393 gas), which lands with weight. Then the
technique on the grid: a fast value (white, EXACT) carries a bound
derived in the source, drawn as a bracket (error_bar) either side of it;
a dashed line (midpoint) marks the rounding boundary half a unit from
each tick. The bound clears the boundary: EMERALD, "no → round", the
value snaps to its tick with a tick mark. A second value's bound
straddles the boundary: RED, a cross, "yes → recompute at higher
precision". The grid stretches eightfold about the boundary (the grid
stretching, never the camera), the bound shrinks in two steps (the wider
stage), clears, turns EMERALD, and the value snaps. Then the counts: how
often the last stage ran in the sweeps, two counters ticking up, FP127's
under a halo; and the gas the test costs on FP127's exp.

Six sections, one per click: prices; fast; crosses; recompute; counters;
closing. The last frame holds as the slide.

Numbers from docs/benchmarks/sweep.json (rows lib=fp19 op=exp and
lib=fp127 op=exp: n, fallback, inputs) and docs/benchmarks/gas.json
(.ops.exp.typical.gas.lib, its median, through vocab.gas). The pre-test
figure 2,716 is in no JSON (contracts/deployments/FP127.md, "typical
inline gas exp 5,360 → 2,716"): a module constant, claim V19. The opcode
prices are LITERALS (V32). The grid in the middle sections carries no
numbers: the positions and bounds on it are illustrative, not claims.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    Create,
    FadeIn,
    FadeOut,
    LaggedStart,
    Text,
    Transform,
    ValueTracker,
    VGroup,
    always_redraw,
)
from manim.utils.rate_functions import ease_in_out_cubic, ease_out_cubic, linear, smooth

from vocab import (
    ROW_COLOUR,
    MONO,
    SIZE_BODY,
    SIZE_CAPTION,
    SIZE_HERO,
    DeckScene,
    GridLine,
    Palette,
    check_mark,
    cross_mark,
    error_bar,
    gas,
    glow_bar,
    halo,
    libs,
    midpoint,
    setup_fonts,
    snap,
    sweep,
    thousands,
    words,
    digits,
)

OP = "exp"
MUL_GAS = 5  # the EVM fee schedule (V32); drawn only through LITERALS, used for the coins' areas
DIVH_GAS = 393  # contracts/src/fp19/README.md:181, divh (V32)
GAS_BEFORE_TEST = 2716  # contracts/deployments/FP127.md: typical inline exp before the rounding test (V19)
GAS_FORM = "lib"  # gas.json's FP127Lib (inline) column: the "typical inline" measure of V19

TITLE = "What correct costs"
STEP_1 = "a fast value, with a bound derived in the source"
STEP_2 = "could the bound change the rounding?"
NO = "no → round"
YES = "yes → recompute at higher precision"
WIDER = "a wider stage"
REACHED = "inputs reached the last stage"
MUL_LABEL = f"MUL · {MUL_GAS} gas"
DIVH_LABEL = f"512-by-256-bit division · {DIVH_GAS} gas"
CAPTION_PRICES = "the EVM fee schedule · the FP19 kernels' README, divh"
CAPTION_SWEEP = "docs/benchmarks/sweep.json · gas.json · exp"

# the grid of sections 1–3: six ticks, the story between ticks LO and HI; nothing on it is a number
TICKS = (0, 5, 1)
LO, HI = 2, 3
UNIT = 1.5  # scene units per tick: after the stretch the two ticks around the boundary sit at ±6, inside the safe area
STRETCH = 8  # the recompute: the grid stretched this many times about the boundary
Y_GRID = -0.35
FAST_1, BOUND_1 = 2.25, 0.2  # the first fast value and its bound, in ticks: clears the boundary at 2.5
FAST_2, BOUND_2 = 2.58, 0.2  # the second: its bound straddles the boundary
BOUNDS_WIDER = (0.1, 0.04)  # the wider stage's bounds, in ticks of the original grid: the first still crosses, the second clears
COIN_R = 1.5  # the division's coin, scene units; MUL's follows by area
CORNER_R = 0.34
Y_CORNER = 3.2  # the coins once in the corner: their centre line
X_CORNER = 5.9  # their right edge, clear of the right mark
Y_STEPS = (2.25, 1.65)
Y_VERDICT = -1.55
Y_COUNTER = 1.05
Y_GAS = -1.75
Y_CLOSE = -2.45
HUES = ROW_COLOUR["s16"]  # the two coins: MUL GOLD, the division VIOLET

# the digit-bearing fixed strings on the slide, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    MUL_LABEL: "V32",
    DIVH_LABEL: "V32",
}


def numbers() -> dict:
    lib = libs()
    rows = {lid: sweep(lid, OP) for lid in ("fp19", "fp127")}
    g = gas(OP)
    with_test = g["inlineMedian"][GAS_FORM]
    pct = round((with_test - GAS_BEFORE_TEST) / GAS_BEFORE_TEST * 100, 1)
    out = {
        "op": OP,
        "fp19": {"label": lib["fp19"]["label"], "n": rows["fp19"]["n"], "fallback": rows["fp19"]["fallback"]},
        "fp127": {"label": lib["fp127"]["label"], "n": rows["fp127"]["n"], "fallback": rows["fp127"]["fallback"], "inputs": rows["fp127"]["inputs"]},
        "gas_before": GAS_BEFORE_TEST,
        "gas_with_test": with_test,
        "gas_form": g["formLabels"][GAS_FORM],
        "pct": pct,
    }
    out["gas_line"] = f"{out['fp127']['label']} {OP}: {thousands(GAS_BEFORE_TEST)} → {thousands(round(with_test))} gas with the test"
    out["pct_line"] = f"+{pct}%"
    out["counters"] = {lid: f"{out[lid]['fallback']} of {thousands(out[lid]['n'])}" for lid in ("fp19", "fp127")}
    out["close_line"] = f"the last stage: {out['counters']['fp127']} inputs"
    return out


def coin(gas_units: float, colour: str = Palette.GOLD, radius_of_divh: float = COIN_R) -> Circle:
    """A coin whose area is its gas: the division's coin has radius_of_divh;
    every other coin's radius follows by the square root of the ratio."""
    r = radius_of_divh * (gas_units / DIVH_GAS) ** 0.5
    return Circle(radius=r, color=colour, fill_color=colour, fill_opacity=0.16, stroke_width=2.5)


def land(t: float) -> float:
    """A drop that overshoots and settles: the weight of the coin."""
    c = 1.70158
    t = t - 1
    return 1 + t * t * ((c + 1) * t + c)


class Ziv(DeckScene):
    SECTIONS = ("prices", "fast", "crosses", "recompute", "counters", "closing")

    def ticking(self, tracker: ValueTracker, total: int, size: float, colour: str, at):
        """A counter "<k> of <total>" with k following the tracker; the
        intermediate frames are plain Text (not a drawn claim), the final
        string is drawn through digits() by the caller."""
        setup_fonts()

        def make():
            return Text(f"{int(round(tracker.get_value()))} of {thousands(total)}", font=MONO, font_size=size, color=colour, disable_ligatures=True).move_to(at)

        return always_redraw(make)

    def construct(self):
        n = numbers()
        self.section(0)
        # the chrome, on the first frame: the title and the caption (the prices' sources;
        # it names the sweep and gas.json once those numbers are on screen)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.caption_now(CAPTION_PRICES)
        self.wait(0.3)

        # the two prices, area for area: the speck (GOLD), then the weight (VIOLET)
        small = coin(MUL_GAS, HUES["mul"]).move_to([-3.4, 0.45, 0])
        big = coin(DIVH_GAS, HUES["divh"]).move_to([1.9, 0.45, 0])
        small_lbl = words(MUL_LABEL, SIZE_BODY, Palette.BODY).next_to(small, DOWN, buff=0.45)
        big_lbl = words(DIVH_LABEL, SIZE_BODY, Palette.BODY).next_to(big, DOWN, buff=0.45)
        self.play(FadeIn(small, scale=0.3, run_time=0.4))
        self.play(FadeIn(small_lbl, shift=UP * 0.08, run_time=0.4))
        self.wait(0.6)
        big.shift(UP * 5.5)
        self.add(big)
        self.play(big.animate(rate_func=land).shift(DOWN * 5.5), run_time=1.1)
        ripple = Circle(radius=COIN_R, color=HUES["divh"], stroke_width=2, stroke_opacity=0.6).move_to(big)
        self.play(ripple.animate(rate_func=ease_out_cubic).scale(1.35).set_stroke(opacity=0), run_time=0.7)
        self.remove(ripple)
        self.play(FadeIn(big_lbl, shift=UP * 0.08, run_time=0.4))

        # the technique: the coins to the corner, the grid, a fast value and its bound
        self.section(1, hold=1.2)
        c_small = coin(MUL_GAS, HUES["mul"], radius_of_divh=CORNER_R)
        c_big = coin(DIVH_GAS, HUES["divh"], radius_of_divh=CORNER_R)
        c_small_lbl = words(MUL_LABEL, 22, Palette.MUTED)
        c_big_lbl = words(DIVH_LABEL, 22, Palette.MUTED)
        row2 = VGroup(c_big, c_big_lbl).arrange(RIGHT, buff=0.22)
        row1 = VGroup(c_small, c_small_lbl).arrange(RIGHT, buff=0.22)
        corner = VGroup(row1, row2).arrange(DOWN, buff=0.12, aligned_edge=RIGHT).move_to([0, Y_CORNER, 0]).align_to([X_CORNER, 0, 0], RIGHT)
        c_small.align_to(c_big, RIGHT).shift(LEFT * (c_big.width - c_small.width) / 2)
        self.play(
            Transform(small, c_small),
            Transform(big, c_big),
            Transform(small_lbl, c_small_lbl),
            Transform(big_lbl, c_big_lbl),
            self.caption(CAPTION_SWEEP),
            run_time=0.9,
        )
        line = GridLine(TICKS, length=UNIT * (TICKS[1] - TICKS[0]))
        line.shift([0, Y_GRID, 0] - line.n2p((LO + HI) / 2))
        mid = midpoint(line, LO, HI)
        self.play(Create(line, run_time=0.8))
        step1 = words(STEP_1, SIZE_BODY, Palette.TEXT).move_to([0, Y_STEPS[0], 0])
        step2 = words(STEP_2, SIZE_BODY, Palette.MUTED).move_to([0, Y_STEPS[1], 0])
        dot1 = line.dot_at(FAST_1, Palette.EXACT)
        bar1 = error_bar(dot1, self.hw(line, BOUND_1), Palette.CORRECT)
        self.play(FadeIn(step1, shift=RIGHT * 0.1, run_time=0.5))
        self.play(FadeIn(dot1, scale=0.3, run_time=0.4))
        self.play(Create(bar1, run_time=0.6))
        self.bring_to_front(dot1)
        self.wait(0.4)
        self.play(FadeIn(step2, shift=RIGHT * 0.1, run_time=0.5), Create(mid, run_time=0.5))
        self.wait(0.6)
        no = words(NO, SIZE_BODY, Palette.CORRECT).move_to([0, Y_VERDICT, 0])
        tick1 = check_mark(Palette.CORRECT).next_to(no, RIGHT, buff=0.3)
        self.play(FadeIn(no, shift=UP * 0.06, run_time=0.4), Create(tick1, run_time=0.3))
        self.play(FadeOut(bar1, run_time=0.3), snap(dot1, line, LO, Palette.CORRECT, run_time=0.9))
        mark1 = check_mark(Palette.CORRECT, size=0.24).next_to(dot1, UP, buff=0.18)
        self.play(Create(mark1, run_time=0.25))

        # a second value: its bound straddles the boundary
        self.section(2, hold=1.2)
        first = VGroup(dot1, mark1, no, tick1)
        self.play(first.animate.set_opacity(0.3), run_time=0.4)
        dot2 = line.dot_at(FAST_2, Palette.EXACT)
        bar2 = error_bar(dot2, self.hw(line, BOUND_2), Palette.EXACT)
        self.play(FadeIn(dot2, scale=0.3, run_time=0.4))
        self.play(Create(bar2, run_time=0.6))
        self.bring_to_front(dot2)
        self.play(step2.animate.set_color(Palette.TEXT), run_time=0.3)
        self.wait(0.4)
        self.play(bar2.animate.set_color(Palette.WRONG), run_time=0.4)
        yes = words(YES, SIZE_BODY, Palette.WRONG).move_to([0, Y_VERDICT, 0])
        cross = cross_mark(Palette.WRONG).next_to(yes, RIGHT, buff=0.3)
        self.play(FadeOut(no, run_time=0.3), FadeOut(tick1, run_time=0.3), FadeIn(yes, shift=UP * 0.06, run_time=0.4), Create(cross, run_time=0.3))

        # the recompute: the grid stretches about the boundary; the bound shrinks until it clears
        self.section(3, hold=1.0)
        about = line.n2p((LO + HI) / 2)
        self.play(
            line.animate(rate_func=ease_in_out_cubic).stretch(STRETCH, 0, about_point=about),
            mid.animate(rate_func=ease_in_out_cubic).stretch(STRETCH, 0, about_point=about),
            bar2.animate(rate_func=ease_in_out_cubic).stretch(STRETCH, 0, about_point=about),
            dot2.animate(rate_func=ease_in_out_cubic).move_to(about + RIGHT * (dot2.get_center() - about)[0] * STRETCH),
            dot1.animate(rate_func=ease_in_out_cubic).move_to(about + RIGHT * (dot1.get_center() - about)[0] * STRETCH),
            mark1.animate(rate_func=ease_in_out_cubic).move_to(about + RIGHT * (mark1.get_center() - about)[0] * STRETCH + UP * (mark1.get_center() - about)[1]),
            run_time=1.4,
        )
        self.bring_to_front(dot2)
        wider = words(WIDER, SIZE_CAPTION, Palette.MUTED).next_to(bar2, UP, buff=0.3)
        self.play(FadeIn(wider, shift=UP * 0.06, run_time=0.4))
        for i, b in enumerate(BOUNDS_WIDER):
            colour = Palette.WRONG if i < len(BOUNDS_WIDER) - 1 else Palette.CORRECT
            self.play(Transform(bar2, error_bar(dot2, self.hw(line, b), colour), rate_func=ease_in_out_cubic), run_time=0.8)
            self.wait(0.5)
        self.play(yes.animate.set_opacity(0.3), cross.animate.set_opacity(0.3), run_time=0.3)
        self.wait(0.5)
        self.play(FadeOut(wider, run_time=0.3), FadeOut(bar2, run_time=0.3), snap(dot2, line, HI, Palette.CORRECT, run_time=1.0))
        glow = halo(dot2.get_center(), Palette.CORRECT)
        mark2 = check_mark(Palette.CORRECT, size=0.24).next_to(dot2, UP, buff=0.18)
        self.add(glow)
        self.bring_to_front(dot2)
        self.play(FadeIn(glow, run_time=0.4), Create(mark2, run_time=0.25))

        # how often the last stage runs: two counters
        self.section(4, hold=1.5)
        grid_stuff = VGroup(line, mid, dot1, mark1, dot2, mark2, glow, yes, cross, step1, step2)
        self.play(grid_stuff.animate.set_opacity(0.1), run_time=0.5)
        self.remove(step1, step2, yes, cross)
        cols = {"fp19": -3.3, "fp127": 3.3}
        colours = {"fp19": Palette.TEXT, "fp127": Palette.EMERALD}  # the libraries' family colours
        names = {lid: words(f"{n[lid]['label']} {OP}", SIZE_BODY, Palette.MUTED).move_to([cols[lid], Y_COUNTER + 0.95, 0]) for lid in cols}
        reached = {lid: words(REACHED, SIZE_BODY, Palette.MUTED).move_to([cols[lid], Y_COUNTER - 0.8, 0]) for lid in cols}
        self.play(LaggedStart(*[FadeIn(names[lid], shift=UP * 0.06) for lid in cols], lag_ratio=0.3, run_time=0.6))
        trackers = {lid: ValueTracker(0) for lid in cols}
        tickers = {lid: self.ticking(trackers[lid], n[lid]["n"], SIZE_HERO, colours[lid], [cols[lid], Y_COUNTER, 0]) for lid in cols}
        self.add(*tickers.values())
        self.play(*[trackers[lid].animate(rate_func=linear).set_value(n[lid]["fallback"]) for lid in cols], run_time=1.6)
        finals = {lid: digits(n["counters"][lid], SIZE_HERO, colours[lid]).move_to([cols[lid], Y_COUNTER, 0]) for lid in cols}
        self.remove(*tickers.values())
        self.add(*finals.values())
        hero = glow_bar(finals["fp127"], Palette.EMERALD, pad=0.3, opacity=0.14)
        self.add(hero)
        self.bring_to_back(hero)
        self.play(FadeIn(hero, run_time=0.5), LaggedStart(*[FadeIn(reached[lid], shift=UP * 0.06) for lid in cols], lag_ratio=0.3, run_time=0.6))
        self.wait(0.8)
        gas_line = digits(n["gas_line"], SIZE_BODY, Palette.TEXT)
        pct = digits(n["pct_line"], SIZE_BODY, Palette.EMERALD)
        gas_row = VGroup(gas_line, pct).arrange(RIGHT, buff=0.5).move_to([0, Y_GAS, 0])
        gas_glow = glow_bar(gas_row, Palette.EMERALD, pad=0.22)
        self.add(gas_glow)
        self.bring_to_back(gas_glow)
        self.play(FadeIn(gas_line, shift=UP * 0.08, run_time=0.6), FadeIn(gas_glow, run_time=0.6))
        self.play(FadeIn(pct, shift=LEFT * 0.1, run_time=0.5))

        # the closing line grows out of the gas line
        self.section(5, hold=1.0)
        close2 = digits(n["close_line"], SIZE_BODY, Palette.TEXT).move_to([0, Y_CLOSE, 0])
        gas_centred = gas_line.copy().move_to([0, Y_GAS, 0])
        close_glow = glow_bar(VGroup(gas_centred, close2), Palette.EMERALD, pad=0.22)
        self.play(FadeOut(pct, run_time=0.3), Transform(gas_line, gas_centred), Transform(gas_glow, close_glow), run_time=0.7)
        self.play(FadeIn(close2, shift=UP * 0.08, run_time=0.6))
        self.close()

    @staticmethod
    def hw(line: GridLine, ticks: float) -> float:
        """A bound of so many ticks, as scene units on the grid as it is now."""
        return abs((line.n2p(ticks) - line.n2p(0))[0])

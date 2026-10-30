"""Slide 16, "What correct costs": Ziv's technique, and what it costs.

Two coins sized by gas, area for area: MUL ("5 gas") is a speck beside the
512-by-256-bit division ("393 gas"), which lands with weight; the coins
then wait in the corner, their prices beside them. Then the technique on
the grid, under one question ("could the bound change the rounding?"): a
fast value (white, EXACT) carries a bound drawn as a bracket (error_bar);
a dashed line (midpoint) marks the rounding boundary half a unit from
each tick. The bound clears the boundary: EMERALD, "no → round", the
value snaps to its tick. That value leaves; a second value's bound
straddles the boundary: RED, a cross, "yes → recompute at higher
precision". The grid stretches eightfold about the boundary (the grid
stretching, never the camera), the bound shrinks in two steps ("a wider
stage"), clears, turns EMERALD, and the value snaps. Last the grid
leaves and the counts land, each under its library's name: how often
the last stage ran in the sweeps, BL19's "1 of 21,913" and BL127's
"0 of 3,963" under a halo, with one label line for both.

Four sections, one per click: prices; fast; crosses (the cross and the
recompute); counters (the poster). The gas the test costs on BL127's exp
(2,716 → 2,835) is in the notes, not on the slide.

Numbers from docs/benchmarks/sweep.json (rows lib=bl19 op=exp and
lib=bl127 op=exp: n, fallback, inputs). The opcode prices are LITERALS
(V32). The grid in the middle sections carries no numbers: the
positions and bounds on it are illustrative, not claims.
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
from manim.utils.rate_functions import ease_in_out_cubic, ease_out_cubic, linear

from vocab import (
    ROW_COLOUR,
    MONO,
    SIZE_BODY,
    SIZE_HERO,
    DeckScene,
    GridLine,
    Palette,
    check_mark,
    cross_mark,
    digits,
    error_bar,
    glow_bar,
    halo,
    libs,
    midpoint,
    setup_fonts,
    snap,
    sweep,
    thousands,
    words,
)

OP = "exp"
MUL_GAS = 5  # the EVM fee schedule (V32); drawn only through LITERALS, used for the coins' areas
DIVH_GAS = 393  # contracts/src/bl19/README.md:181, divh (V32)

TITLE = "What correct costs"
QUESTION = "could the bound change the rounding?"
NO = "no → round"
YES = "yes → recompute at higher precision"
WIDER = "a wider stage"
REACHED = "inputs reached the last stage"
MUL_LABEL = f"{MUL_GAS} gas"
DIVH_LABEL = f"{DIVH_GAS} gas"

# the grid of sections 1–2: six ticks, the story between ticks LO and HI; nothing on it is a number
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
Y_CORNER = 3.05  # the coins once in the corner: their centre line (the top inside the safe area)
X_CORNER = 5.9  # the labels' right edge, clear of the right mark
Y_QUESTION = 1.55
Y_VERDICT = -1.55
Y_NAME = 0.85  # the counters' library names
Y_COUNTER = -0.2
Y_REACHED = -1.5  # the one label line under both counters
SIZE_COUNTER = 56  # the two counters: the poster's numbers
HUES = ROW_COLOUR["s16"]  # the two coins: MUL GOLD, the division VIOLET

# the digit-bearing fixed strings on the slide, each with its claim id (research_notes/talk/claims.md)
LITERALS = {
    MUL_LABEL: "V32",
    DIVH_LABEL: "V32",
}


def numbers() -> dict:
    lib = libs()
    rows = {lid: sweep(lid, OP) for lid in ("bl19", "bl127")}
    out = {
        "op": OP,
        "bl19": {"label": lib["bl19"]["label"], "n": rows["bl19"]["n"], "fallback": rows["bl19"]["fallback"]},
        "bl127": {"label": lib["bl127"]["label"], "n": rows["bl127"]["n"], "fallback": rows["bl127"]["fallback"], "inputs": rows["bl127"]["inputs"]},
    }
    out["counters"] = {lid: f"{out[lid]['fallback']} of {thousands(out[lid]['n'])}" for lid in ("bl19", "bl127")}
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
    SECTIONS = ("prices", "fast", "crosses", "counters")

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
        # the chrome, on the first frame: the title
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.wait(0.3)

        # the two prices, area for area: the speck (GOLD), then the weight (VIOLET)
        small = coin(MUL_GAS, HUES["mul"]).move_to([-3.4, 0.45, 0])
        big = coin(DIVH_GAS, HUES["divh"]).move_to([1.9, 0.45, 0])
        small_lbl = words(MUL_LABEL, SIZE_HERO, HUES["mul"]).next_to(small, DOWN, buff=0.5)
        big_lbl = words(DIVH_LABEL, SIZE_HERO, HUES["divh"]).next_to(big, DOWN, buff=0.4)
        small_lbl.set_y(big_lbl.get_y())
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

        # 1 · the technique: the coins to the corner, the grid, a fast value and its bound
        self.section(1, hold=1.2)
        c_small = coin(MUL_GAS, HUES["mul"], radius_of_divh=CORNER_R)
        c_big = coin(DIVH_GAS, HUES["divh"], radius_of_divh=CORNER_R)
        c_small_lbl = words(MUL_LABEL, SIZE_BODY, HUES["mul"])
        c_big_lbl = words(DIVH_LABEL, SIZE_BODY, HUES["divh"])
        # two rows: the coins on one centre line, their labels left-aligned beside them
        x_label = X_CORNER - max(c_small_lbl.width, c_big_lbl.width)
        x_coin = x_label - 0.22 - CORNER_R
        y1, y2 = Y_CORNER + 0.25, Y_CORNER - 0.3
        c_small.move_to([x_coin, y1, 0])
        c_big.move_to([x_coin, y2, 0])
        c_small_lbl.move_to([x_label + c_small_lbl.width / 2, y1, 0])
        c_big_lbl.move_to([x_label + c_big_lbl.width / 2, y2, 0])
        corner = VGroup(c_small, c_big, c_small_lbl, c_big_lbl)
        assert corner.get_top()[1] <= 3.6 and corner.get_bottom()[1] > Y_QUESTION + 0.35, (corner.get_top()[1], corner.get_bottom()[1])
        self.play(
            Transform(small, c_small),
            Transform(big, c_big),
            Transform(small_lbl, c_small_lbl),
            Transform(big_lbl, c_big_lbl),
            run_time=0.9,
        )
        line = GridLine(TICKS, length=UNIT * (TICKS[1] - TICKS[0]))
        line.shift([0, Y_GRID, 0] - line.n2p((LO + HI) / 2))
        mid = midpoint(line, LO, HI)
        self.play(Create(line, run_time=0.8))
        dot1 = line.dot_at(FAST_1, Palette.EXACT)
        bar1 = error_bar(dot1, self.hw(line, BOUND_1), Palette.CORRECT)
        self.play(FadeIn(dot1, scale=0.3, run_time=0.4))
        self.play(Create(bar1, run_time=0.6))
        self.bring_to_front(dot1)
        self.wait(0.4)
        question = words(QUESTION, SIZE_BODY, Palette.TEXT).move_to([0, Y_QUESTION, 0])
        self.play(FadeIn(question, shift=RIGHT * 0.1, run_time=0.5), Create(mid, run_time=0.5))
        self.wait(0.6)
        no = words(NO, SIZE_BODY, Palette.CORRECT).move_to([0, Y_VERDICT, 0])
        tick1 = check_mark(Palette.CORRECT).next_to(no, RIGHT, buff=0.3)
        self.play(FadeIn(no, shift=UP * 0.06, run_time=0.4), Create(tick1, run_time=0.3))
        self.play(FadeOut(bar1, run_time=0.3), snap(dot1, line, LO, Palette.CORRECT, run_time=0.9))
        mark1 = check_mark(Palette.CORRECT, size=0.24).next_to(dot1, UP, buff=0.18)
        self.play(Create(mark1, run_time=0.25))

        # 2 · a second value: its bound straddles the boundary; only then recompute
        self.section(2, hold=1.2)
        self.play(FadeOut(VGroup(dot1, mark1, no, tick1), run_time=0.4))
        dot2 = line.dot_at(FAST_2, Palette.EXACT)
        bar2 = error_bar(dot2, self.hw(line, BOUND_2), Palette.EXACT)
        self.play(FadeIn(dot2, scale=0.3, run_time=0.4))
        self.play(Create(bar2, run_time=0.6))
        self.bring_to_front(dot2)
        self.wait(0.4)
        self.play(bar2.animate.set_color(Palette.WRONG), run_time=0.4)
        yes = words(YES, SIZE_BODY, Palette.WRONG).move_to([0, Y_VERDICT, 0])
        cross = cross_mark(Palette.WRONG).next_to(yes, RIGHT, buff=0.3)
        self.play(FadeIn(yes, shift=UP * 0.06, run_time=0.4), Create(cross, run_time=0.3))
        self.wait(0.8)
        # the recompute: the grid stretches about the boundary; the bound shrinks until it clears
        about = line.n2p((LO + HI) / 2)
        self.play(
            line.animate(rate_func=ease_in_out_cubic).stretch(STRETCH, 0, about_point=about),
            mid.animate(rate_func=ease_in_out_cubic).stretch(STRETCH, 0, about_point=about),
            bar2.animate(rate_func=ease_in_out_cubic).stretch(STRETCH, 0, about_point=about),
            dot2.animate(rate_func=ease_in_out_cubic).move_to(about + RIGHT * (dot2.get_center() - about)[0] * STRETCH),
            run_time=1.4,
        )
        self.bring_to_front(dot2)
        wider = words(WIDER, SIZE_BODY, Palette.MUTED).next_to(bar2, UP, buff=0.3)
        self.play(FadeIn(wider, shift=UP * 0.06, run_time=0.4))
        for i, b in enumerate(BOUNDS_WIDER):
            colour = Palette.WRONG if i < len(BOUNDS_WIDER) - 1 else Palette.CORRECT
            self.play(Transform(bar2, error_bar(dot2, self.hw(line, b), colour), rate_func=ease_in_out_cubic), run_time=0.8)
            self.wait(0.5)
        self.play(FadeOut(VGroup(yes, cross), run_time=0.4))
        self.play(FadeOut(wider, run_time=0.3), FadeOut(bar2, run_time=0.3), snap(dot2, line, HI, Palette.CORRECT, run_time=1.0))
        glow = halo(dot2.get_center(), Palette.CORRECT)
        mark2 = check_mark(Palette.CORRECT, size=0.24).next_to(dot2, UP, buff=0.18)
        self.add(glow)
        self.bring_to_front(dot2)
        self.play(FadeIn(glow, run_time=0.4), Create(mark2, run_time=0.25))

        # 3 · how often the last stage runs: the grid leaves, two counters, one label
        self.section(3, hold=1.5)
        self.play(FadeOut(VGroup(line, mid, dot2, mark2, glow, question), run_time=0.5))
        cols = {"bl19": -3.4, "bl127": 3.4}
        colours = {"bl19": Palette.TEXT, "bl127": Palette.EMERALD}  # the libraries' family colours
        names = {lid: words(f"{n[lid]['label']} {OP}", SIZE_BODY, Palette.MUTED).move_to([cols[lid], Y_NAME, 0]) for lid in cols}
        self.play(LaggedStart(*[FadeIn(names[lid], shift=UP * 0.06) for lid in cols], lag_ratio=0.3, run_time=0.6))
        trackers = {lid: ValueTracker(0) for lid in cols}
        tickers = {lid: self.ticking(trackers[lid], n[lid]["n"], SIZE_COUNTER, colours[lid], [cols[lid], Y_COUNTER, 0]) for lid in cols}
        self.add(*tickers.values())
        self.play(*[trackers[lid].animate(rate_func=linear).set_value(n[lid]["fallback"]) for lid in cols], run_time=1.6)
        finals = {lid: digits(n["counters"][lid], SIZE_COUNTER, colours[lid]).move_to([cols[lid], Y_COUNTER, 0]) for lid in cols}
        self.remove(*tickers.values())
        self.add(*finals.values())
        hero = glow_bar(finals["bl127"], Palette.EMERALD, pad=0.3, opacity=0.14)
        self.add(hero)
        self.bring_to_back(hero)
        reached = words(REACHED, SIZE_BODY, Palette.TEXT).move_to([0, Y_REACHED, 0])
        self.play(FadeIn(hero, run_time=0.5), FadeIn(reached, shift=UP * 0.06, run_time=0.6))
        self.close()

    @staticmethod
    def hw(line: GridLine, ticks: float) -> float:
        """A bound of so many ticks, as scene units on the grid as it is now."""
        return abs((line.n2p(ticks) - line.n2p(0))[0])

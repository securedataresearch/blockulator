"""Slide 6, "Resupply, 26 Jun 2025": one floor, in full.

The edit pass's replay shape (talk/briefs/edit-pass.md; the models are
s06c and s02): one idea per section, each section owns the frame, the
poster holds the conclusion.

A donation into an empty vault makes the oracle's price per share
2,000,000,000,000,000,000,001,998,001,998,001,998. The pair's exchange
rate is 10^36 ÷ price = 0.4999999999999999999995 (to 22 decimals: the
fewest at which it still reads below one half; at 21 it rounds to 0.5),
and integer division floors it to 0 on the integer grid the rate is
stored on. The solvency check then reads LTV = 10,000,000 × 0 × 10^5 = 0
≤ 95,000, so 1 wei of collateral borrows 10,000,000 reUSD. With the exact
rate the same check reads LTV = 499,999,999,999.9999999995004995 (to 16
decimals) > 95,000: insolvent, 5,263,158× the limit. The poster: the
exact rate on the grid (emerald, halo), the check shut (red, cross,
"insolvent"), the multiplier as the hero, and BL127 / BL19's one line:
they carry the rate exact and the borrow would revert (the replay's own
table, docs/benchmarks/replay-resupply.md, through vocab.replay_table,
cross-checked against the exact value here).

Six sections, one per click: price, division, floor, check, half,
multiplier. Provenance (block, the Solidity lines) is in the slide's
notes.

Numbers from scripts/replays/resupply.json: .pins.price, .borrowAmount,
.collateral, .maxLTV, .ltvPrecision, .exchangePrecision; the formula's
10^36 read from the cited line ResupplyPairCore.sol:573. Every value is
computed here from the pins with Fraction: rate = 10^36 / price; LTV =
borrow × rate × ltvPrecision / exchangePrecision / collateral. The
title's date is incidents.json's. No number on screen carries an
ellipsis: each is complete in a stated format, rounded half-up at the
stated decimal (check.py asserts both).
"""

from __future__ import annotations

import re
from decimal import Decimal
from fractions import Fraction
from math import log10

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    Create,
    FadeIn,
    FadeOut,
    ReplacementTransform,
    VGroup,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    PROTOCOL_COLOUR,
    SIZE_BODY,
    SIZE_HERO,
    DeckScene,
    GridLine,
    Palette,
    check_mark,
    cross_mark,
    digits,
    direction,
    glow_bar,
    halo,
    incidents,
    markup,
    replay_table,
    resupply,
    snap,
    thousands,
    words,
)

PROTOCOL = "Resupply"  # incidents.json's name; its hue in the deck is SAPPHIRE
HUE = PROTOCOL_COLOUR["resupply"]
LTV_DECIMALS = 16  # decimals of the exact LTV, complete and labelled
RATE_SHORT = 22  # decimals of the rate as drawn: the fewest that still read below one half
GRID = (0, 2, 1)  # the integer grid the stored rate lives on
SIZE_PRICE = 31  # the 49-glyph price: the largest mono size that fits the safe area (BODY overflows it)
SIZE_RATIO = 72  # the multiplier, the poster's hero (edit-pass: a lone hero number at 64–72)
RULERS = "The decisive step on each ruler"  # the replay table's heading


def _rounded(q: Fraction, places: int) -> str:
    """q as a decimal string rounded half-up at `places` decimals (integer
    arithmetic: (2·q·10^places + 1) // 2), with thousands separators on
    the integer part."""
    scaled = (2 * q.numerator * 10**places + q.denominator) // (2 * q.denominator)
    whole, frac = divmod(scaled, 10**places)
    return f"{thousands(whole)}.{frac:0{places}d}"


def to_decimals(places: int) -> str:
    """The label that states a rounded number's format."""
    return f"(to {places} decimals)"


def _power_of_ten(n: int) -> int:
    e = round(log10(n))
    assert 10**e == n, n
    return e


def _numerator_exp(rate_line: str) -> int:
    """The exponent of the rate's numerator, read from the cited Solidity
    line ("_exchangeRate = 1e36 / …"): the formula is the source's."""
    m = re.search(r"\b1e(\d+)\b", rate_line)
    assert m, rate_line
    return int(m.group(1))


LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers() (the 36 is read from the cited line)


def numbers() -> dict:
    d = resupply()
    p = d["pins"]
    price, borrow, coll = int(p["price"]), int(p["borrowAmount"]), int(p["collateral"])
    max_ltv, ltv_p, ex_p = int(p["maxLTV"]), int(p["ltvPrecision"]), int(p["exchangePrecision"])
    cite = {c["line"]: c for c in d["citations"] if c["file"].endswith("ResupplyPairCore.sol")}
    rate_exp = _numerator_exp(cite[573]["text"])
    rate = Fraction(10**rate_exp, price)
    floor = 10**rate_exp // price
    assert floor == int(p["exchangeRateOnChain"]), "the chain stored the floored rate"
    ltv_floor = ((borrow * floor * ltv_p) // ex_p) // coll
    ltv = Fraction(borrow) * rate * ltv_p / ex_p / coll
    # BL127 and BL19 in the replay's table: the rate carried exact, the borrow reverts
    rulers = replay_table("resupply", RULERS)
    ours = [r for r in rulers if r["method"].startswith(("BL127", "BL19", "FP127", "FP19"))]
    assert len(ours) == 2, [r["method"] for r in rulers]
    for r in ours:
        stated = r["rate"].split(".")[1]
        assert abs(Fraction(Decimal(r["rate"])) - rate) < Fraction(1, 10 ** len(stated)), r
        assert abs(Fraction(Decimal(r["LTV (1e-5)"])) - ltv) < 1 and "insolvent: reverts" in r["verdict"], r
    inc = next(i for i in incidents()["incidents"] if i["protocol"] == PROTOCOL)
    return {
        "title": f"{PROTOCOL}, {inc['date']}",
        "rate_exp": rate_exp,
        "base": 10,
        "grid_ticks": list(range(GRID[0], GRID[1] + 1)),
        "price": thousands(price),
        "rate_short": _rounded(rate, RATE_SHORT),
        "rate_label": to_decimals(RATE_SHORT),
        "floor": str(floor),
        "borrow_tokens": thousands(borrow // ex_p),  # reUSD, exact
        "collateral": thousands(coll),
        "ltv_exp": _power_of_ten(ltv_p),
        "ltv_floor": thousands(ltv_floor),
        "max_ltv": thousands(max_ltv),
        "ltv_exact": _rounded(ltv, LTV_DECIMALS),
        "ltv_label": to_decimals(LTV_DECIMALS),
        "ratio": thousands(round(ltv / max_ltv)),
        "solvent_floor": ltv_floor <= max_ltv,
        "solvent_exact": ltv <= max_ltv,
    }


class Resupply(DeckScene):
    SECTIONS = ("price", "division", "floor", "check", "half", "multiplier")

    Y_OPERANDS, Y_RATE, Y_LINE = 2.25, 1.45, -0.45
    LINE_LEN, LINE_X = 7.6, -1.0
    Y_ROW1, Y_ROW2 = 0.55, -0.75  # the check's two rows
    Y_POSTER_RATE, Y_POSTER_LINE = 2.3, 0.75  # the poster's rate row and grid
    Y_HERO, Y_VERDICT = -1.0, -2.55  # the poster's hero row and Blockulator's line

    def lattice(self, n, y: float):
        """The integer grid with its tick numbers and its name: built fresh for each beat that uses it."""
        line = GridLine(GRID, length=self.LINE_LEN, tick_size=0.16).move_to([self.LINE_X, y, 0])
        ticks = VGroup(*[digits(str(k), SIZE_BODY, Palette.FAINT).next_to(line.n2p(k), DOWN, buff=0.28) for k in n["grid_ticks"]])
        name = words("exchange rate", SIZE_BODY, Palette.MUTED).next_to(line.get_end(), RIGHT, buff=0.45)
        return line, ticks, name

    def rate_row(self, n, y: float):
        """The rate at HERO on its own line (24 glyphs: with its label beside it the row would leave
        the safe area), its stated format under its right end."""
        rate = digits(n["rate_short"], SIZE_HERO, Palette.EXACT).move_to([0, y, 0])
        stated = words(n["rate_label"], SIZE_BODY, Palette.MUTED).next_to(rate, DOWN, buff=0.18).align_to(rate, RIGHT)
        return rate, stated, VGroup(rate, stated)

    def construct(self):
        n = numbers()
        assert n["solvent_floor"] and not n["solvent_exact"]
        x_exact = float(Fraction(10 ** n["rate_exp"], int(n["price"].replace(",", ""))))
        x_floor = float(n["floor"])
        red = Palette.WRONG

        # chrome: the title, on the first frame
        self.section(0)
        self.fix(self.title(n["title"]))
        self.wait(0.3)

        # price: what the donation made the oracle read, per share
        name = words("the oracle's price per share", SIZE_BODY, HUE).move_to([0, 0.85, 0])
        price = digits(n["price"], SIZE_PRICE, Palette.EXACT).move_to([0, 0.0, 0])
        self.play(FadeIn(name, shift=UP * 0.1, run_time=0.6))
        self.play(AddTextLetterByLetter(price, time_per_char=0.045))
        self.wait(1.0)

        # division: 10^36 ÷ price, just under one half, lands on the grid
        self.section(1, hold=2.0)
        operands = markup(f"10<sup>{n['rate_exp']}</sup> ÷ price", SIZE_BODY, Palette.TEXT).move_to([0, self.Y_OPERANDS, 0])
        self.play(FadeOut(VGroup(name, price), run_time=0.6), FadeIn(operands, shift=DOWN * 0.1, run_time=0.6))
        rate, stated, _ = self.rate_row(n, self.Y_RATE)
        line, ticks, axis = self.lattice(n, self.Y_LINE)
        self.play(Create(line, run_time=0.9), FadeIn(ticks, run_time=0.7), FadeIn(axis, run_time=0.7))
        dot = line.dot_at(x_exact, Palette.EXACT).shift(UP * 1.1)
        self.play(AddTextLetterByLetter(rate, time_per_char=0.07))
        self.play(FadeIn(stated, run_time=0.4), FadeIn(dot, run_time=0.3))
        self.play(dot.animate(rate_func=ease_out_cubic, run_time=0.9).move_to(line.n2p(x_exact)))
        self.wait(0.8)

        # floor: integer division drops the half; the chain stored 0
        self.section(2, hold=2.0)
        self.play(FadeOut(operands, run_time=0.5))
        arrow = direction(line, x_exact, x_floor, red, lift=0.38)
        floor_lbl = words("floor", SIZE_BODY, red).next_to(arrow, UP, buff=0.15)
        kept = dot.copy()
        self.add(kept)
        self.play(Create(arrow, run_time=0.6), FadeIn(floor_lbl, run_time=0.5))
        self.play(snap(kept, line, x_floor, red, run_time=1.2))
        self.wait(0.6)
        stored = VGroup(cross_mark(red), words("rate stored:", SIZE_BODY, red), digits(n["floor"], SIZE_HERO, red)).arrange(RIGHT, buff=0.3)
        stored.move_to([0, -2.35, 0])
        stored[2].align_to(stored[1], DOWN)
        self.play(Create(stored[0], run_time=0.4), FadeIn(stored[1:], shift=UP * 0.1, run_time=0.6))

        # check: the solvency check reads 0 and lets 1 wei of collateral borrow ten million
        self.section(3, hold=2.0)
        row1 = markup(
            f"LTV  =  {n['borrow_tokens']} × <span foreground='{red}'>{n['floor']}</span> × {n['base']}<sup>{n['ltv_exp']}</sup>"
            f"  =  <span foreground='{red}'>{n['ltv_floor']}</span>  ≤  {n['max_ltv']}",
            SIZE_BODY,
            Palette.TEXT,
        ).move_to([0, self.Y_ROW1, 0])
        effect = VGroup(cross_mark(red), words(f"{n['collateral']} wei of collateral borrows {n['borrow_tokens']} reUSD", SIZE_BODY, red)).arrange(RIGHT, buff=0.3)
        effect.move_to([0, self.Y_ROW2, 0])
        self.play(
            FadeOut(VGroup(line, ticks, axis, dot, arrow, floor_lbl, rate, stated, stored), run_time=0.6),
            kept.animate(run_time=0.9).move_to(row1.get_center()).set_opacity(0),
        )
        self.remove(kept)
        self.play(FadeIn(row1, shift=RIGHT * 0.1, run_time=0.8))
        self.wait(1.0)
        self.play(Create(effect[0], run_time=0.4), FadeIn(effect[1], shift=UP * 0.1, run_time=0.6))

        # half: the same check with the exact rate fails
        self.section(4, hold=2.5)
        # the name above the value: "LTV =" on the same line would run past the safe area
        ltv = VGroup(digits(n["ltv_exact"], SIZE_BODY, Palette.EXACT), words(n["ltv_label"], SIZE_BODY, Palette.MUTED))
        ltv.arrange(RIGHT, buff=0.3, aligned_edge=DOWN).move_to([0, self.Y_ROW1, 0])
        ltv.add(words("LTV", SIZE_BODY, Palette.MUTED).next_to(ltv, UP, buff=0.35).align_to(ltv, LEFT))
        over = markup(f"&gt;  {n['max_ltv']}", SIZE_BODY, Palette.TEXT)
        shut = VGroup(cross_mark(red), words("insolvent", SIZE_BODY, red)).arrange(RIGHT, buff=0.3)
        VGroup(over, shut).arrange(RIGHT, buff=0.8).move_to([0, self.Y_ROW2, 0])
        self.play(FadeOut(effect, run_time=0.5), ReplacementTransform(row1, ltv, run_time=1.0))
        self.wait(0.6)
        self.play(FadeIn(over, run_time=0.5))
        self.play(Create(shut[0], run_time=0.5), FadeIn(shut[1], run_time=0.5))

        # multiplier: the check shut by 5,263,158×; the exact rate on the grid; Blockulator keeps the half
        self.section(5, hold=2.5)
        ratio = VGroup(words(f"{n['ratio']}×", SIZE_RATIO, red), words("the limit", SIZE_BODY, Palette.TEXT)).arrange(RIGHT, buff=0.35, aligned_edge=DOWN)
        landed = VGroup(cross_mark(red), words("insolvent", SIZE_BODY, red)).arrange(RIGHT, buff=0.3)
        VGroup(ratio, landed).arrange(RIGHT, buff=0.9).move_to([0, self.Y_HERO, 0])
        landed.align_to(ratio[1], DOWN)
        self.play(FadeOut(ltv, run_time=0.5), FadeOut(over, run_time=0.5), ReplacementTransform(shut, landed, run_time=0.8))
        self.play(FadeIn(ratio, scale=0.7, run_time=0.8))
        self.wait(0.8)
        line, ticks, axis = self.lattice(n, self.Y_POSTER_LINE)
        _, _, row = self.rate_row(n, self.Y_POSTER_RATE)
        self.play(Create(line, run_time=0.8), FadeIn(ticks, run_time=0.6), FadeIn(axis, run_time=0.6), FadeIn(row, run_time=0.6))
        glow = halo(line.n2p(x_exact), Palette.CORRECT)
        ours = line.dot_at(x_exact, Palette.CORRECT).shift(UP * 1.0)
        self.play(FadeIn(ours, run_time=0.3))
        self.play(ours.animate(rate_func=ease_out_cubic, run_time=0.9).move_to(line.n2p(x_exact)))
        self.play(FadeIn(glow, run_time=0.6))
        self.bring_to_front(ours)
        says = words("BL127 / BL19 keep the rate exact · the borrow would revert", SIZE_BODY, Palette.CORRECT)
        tick = check_mark(Palette.CORRECT)
        says_row = VGroup(says, tick).arrange(RIGHT, buff=0.35).move_to([0, self.Y_VERDICT, 0])
        panel = glow_bar(says_row, Palette.CORRECT, pad=0.18)
        self.play(FadeIn(panel, run_time=0.5), FadeIn(says, shift=UP * 0.1, run_time=0.7))
        self.play(Create(tick, run_time=0.5))
        self.close()

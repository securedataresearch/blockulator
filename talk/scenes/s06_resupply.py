"""Slide 6, "Resupply, 26 June 2025": one floor, in full.

The exchange rate is 10^36 ÷ price (ResupplyPairCore.sol:573). The price
the oracle returned types in; the long division runs out digit by digit
to 0.4999…; on the integer grid the rate is stored on, the value sits
between 0 and 1 and the floor snaps it to 0 (WRONG, red). The solvency
check (ResupplyPairCore.sol:282) then reads 10,000,000 × 0 × 10^5 = 0 ≤
95,000 and draws an emerald tick. Then the half is restored: the dot
returns to the exact value, the LTV recomputes to 499,999,999,999.99…,
the comparison with 95,000 reads 5,263,158× and the tick becomes a red
cross. About 90 s.

Numbers from scripts/replays/resupply.json: .pins.price, .borrowAmount,
.collateral, .maxLTV, .ltvPrecision, .exchangePrecision, .block; the two
Solidity lines from .citations (file, line, text). Every value is
computed here from the pins with Fraction and Decimal, as
docs/benchmarks/replay-resupply.md does: rate = 10^36 / price; LTV =
borrow × rate × ltvPrecision / exchangePrecision / collateral.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from math import log10

from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    Create,
    FadeIn,
    FadeOut,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import DeckScene, GridLine, Palette, check_mark, cross_mark, digits, direction, markup, resupply, snap, thousands, words

QUOTIENT_DIGITS = 36  # decimals of the long division shown before the ellipsis
LTV_DECIMALS = 2  # decimals of the exact LTV shown before the ellipsis
RATE_SHORT = 4  # decimals of the rate where it is named in passing (0.4999…)
GRID = (0, 2, 1)  # the integer grid the stored rate lives on
MONO = 30
SANS = 28
SMALL = 14  # the Solidity citations
CHECK = 24  # the solvency row


def _truncate(q: Fraction, places: int) -> str:
    """q as a decimal string cut (not rounded) after `places` decimals,
    with thousands separators on the integer part."""
    scaled = q.numerator * 10**places // q.denominator
    whole, frac = divmod(scaled, 10**places)
    return f"{thousands(whole)}.{frac:0{places}d}"


def _power_of_ten(n: int) -> int:
    e = round(log10(n))
    assert 10**e == n, n
    return e


def numbers() -> dict:
    d = resupply()
    p = d["pins"]
    price, borrow, coll = int(p["price"]), int(p["borrowAmount"]), int(p["collateral"])
    max_ltv, ltv_p, ex_p = int(p["maxLTV"]), int(p["ltvPrecision"]), int(p["exchangePrecision"])
    rate = Fraction(10**36, price)
    floor = 10**36 // price
    ltv_floor = ((borrow * floor * ltv_p) // ex_p) // coll
    ltv = Fraction(borrow) * rate * ltv_p / ex_p / coll
    with localcontext() as ctx:
        ctx.prec = 60
        pct = str((Decimal(max_ltv) / Decimal(ltv_p) * 100).normalize())
    cite = {c["line"]: c for c in d["citations"] if c["file"].endswith("ResupplyPairCore.sol")}
    quotient = _truncate(rate, QUOTIENT_DIGITS)
    return {
        "block": thousands(p["block"]),
        "price": thousands(price),
        "quotient": quotient + "…",
        "rate_short": quotient[: RATE_SHORT + 2] + "…",
        "floor": str(floor),
        "borrow_tokens": thousands(borrow // ex_p),  # reUSD, exact
        "collateral": thousands(coll),
        "ltv_exp": _power_of_ten(ltv_p),
        "ltv_floor": thousands(ltv_floor),
        "max_ltv": thousands(max_ltv),
        "max_ltv_pct": pct + "%",
        "ltv_exact": _truncate(ltv, LTV_DECIMALS) + "…",
        "ratio": thousands(round(ltv / max_ltv)),
        "solvent_floor": ltv_floor <= max_ltv,
        "solvent_exact": ltv <= max_ltv,
        "rate_line": cite[573]["text"],
        "ltv_line": cite[282]["text"],
    }


class Resupply(DeckScene):
    def construct(self):
        n = numbers()
        assert n["solvent_floor"] and not n["solvent_exact"]
        self.wait(0.6)
        self.play(self.caption(f"scripts/replays/resupply.json · block {n['block']}"))

        # the formula, from the verified source, and the price the oracle returned
        y0 = 3.3
        formula = markup("exchange rate  =  10<sup>36</sup> ÷ price", SANS, Palette.TEXT)
        formula.move_to([-6.3 + formula.width / 2, y0, 0])
        src = digits(n["rate_line"], SMALL, Palette.FAINT)
        src.move_to([-6.3 + src.width / 2, y0 - 0.45, 0])
        self.play(FadeIn(formula, shift=RIGHT * 0.1, run_time=0.6))
        self.play(FadeIn(src, run_time=0.5))
        self.wait(3.0)

        price_lbl = words("price", SANS, Palette.MUTED)
        price_lbl.move_to([-6.3 + price_lbl.width / 2, y0 - 1.15, 0])
        price = digits(n["price"], MONO - 2, Palette.TEXT)
        price.next_to(price_lbl, RIGHT, buff=0.45).set_y(y0 - 1.15)
        self.play(FadeIn(price_lbl, run_time=0.4))
        self.play(AddTextLetterByLetter(price, time_per_char=0.045))
        self.wait(4.0)

        # the long division runs out
        q_lbl = markup("10<sup>36</sup> ÷ price", SANS, Palette.MUTED)
        q_lbl.move_to([-6.3 + q_lbl.width / 2, y0 - 1.95, 0])
        quotient = digits(n["quotient"], MONO, Palette.EXACT)
        quotient.next_to(q_lbl, RIGHT, buff=0.45).set_y(y0 - 1.95)
        self.play(FadeIn(q_lbl, run_time=0.4))
        self.play(AddTextLetterByLetter(quotient, time_per_char=0.09))
        self.wait(4.0)

        # the integer grid the stored rate lives on
        line = GridLine(GRID, length=6.5, tick_size=0.14).move_to([-1.6, -0.6, 0])
        tick_lbls = VGroup(*[digits(str(k), 24, Palette.FAINT).next_to(line.n2p(k), DOWN, buff=0.22) for k in range(GRID[0], GRID[1] + 1)])
        grid_lbl = words("the stored rate is an integer", 22, Palette.FAINT).next_to(line.get_end(), RIGHT, buff=0.4)
        self.play(Create(line, run_time=1.0), FadeIn(tick_lbls, run_time=0.8))
        self.play(FadeIn(grid_lbl, run_time=0.5))
        x_exact = float(Fraction(10**36, int(resupply()["pins"]["price"])))
        dot = line.dot_at(x_exact, Palette.EXACT)
        dot.move_to(line.n2p(x_exact) + UP * 1.6)
        exact_lbl = digits(n["rate_short"], 22, Palette.EXACT).next_to(line.n2p(x_exact), UP, buff=0.3).shift(RIGHT * 0.7)
        self.play(FadeIn(dot, run_time=0.3))
        self.play(dot.animate(rate_func=ease_out_cubic).move_to(line.n2p(x_exact)), run_time=0.8)
        self.play(FadeIn(exact_lbl, run_time=0.4))
        self.wait(3.0)

        # the floor sweeps the fraction away
        arrow = direction(line, x_exact, float(n["floor"]), Palette.WRONG, lift=0.42)
        floor_lbl = words("floor", 22, Palette.WRONG).next_to(arrow, UP, buff=0.1)
        self.play(Create(arrow, run_time=0.6), FadeIn(floor_lbl, run_time=0.4))
        self.play(
            snap(dot, line, float(n["floor"]), Palette.WRONG, run_time=1.0),
            quotient[1:].animate.set_color(Palette.FAINT),
            FadeOut(exact_lbl, run_time=0.5),
        )
        stored = digits(n["floor"], MONO, Palette.WRONG)
        stored_lbl = words("stored rate", SANS, Palette.MUTED)
        stored_lbl.move_to([-6.3 + stored_lbl.width / 2, y0 - 2.7, 0])
        stored.next_to(stored_lbl, RIGHT, buff=0.45).set_y(y0 - 2.7)
        self.play(FadeIn(stored_lbl, run_time=0.4), FadeIn(stored, shift=DOWN * 0.1, run_time=0.5))
        self.wait(4.0)

        # the solvency check, as deployed
        y_chk = -2.1
        chk_src = digits(n["ltv_line"], SMALL, Palette.FAINT)
        chk_src.move_to([-6.3 + chk_src.width / 2, y_chk + 0.55, 0])
        self.play(FadeIn(chk_src, run_time=0.5))
        self.wait(1.0)

        def check_row(rate_str: str, ltv_str: str, cmp: str, colour: str):
            left = markup(
                f"LTV  =  {n['borrow_tokens']} × <span foreground='{colour}'>{rate_str}</span> × 10<sup>{n['ltv_exp']}</sup>  =  "
                f"<span foreground='{colour}'>{ltv_str}</span>",
                CHECK,
                Palette.TEXT,
            )
            left.move_to([-6.3 + left.width / 2, y_chk, 0])
            right = markup(cmp, CHECK, Palette.TEXT)
            right.next_to(left, RIGHT, buff=0.5).set_y(y_chk)
            return left, right

        row_l, row_r = check_row(n["floor"], n["ltv_floor"], f"≤  {n['max_ltv']}  ({n['max_ltv_pct']})", Palette.WRONG)
        self.play(FadeIn(row_l, shift=RIGHT * 0.1, run_time=0.6))
        self.wait(1.5)
        self.play(FadeIn(row_r, run_time=0.5))
        tick = check_mark(Palette.CORRECT).next_to(row_r, RIGHT, buff=0.45).set_y(y_chk)
        verdict = words("solvent", 22, Palette.CORRECT).next_to(tick, RIGHT, buff=0.25).set_y(y_chk)
        self.play(Create(tick, run_time=0.5))
        self.play(FadeIn(verdict, run_time=0.4))
        self.wait(9.0)

        # the half, restored
        self.play(FadeOut(arrow, run_time=0.4), FadeOut(floor_lbl, run_time=0.4))
        back = dot.copy().move_to(line.n2p(x_exact)).set_color(Palette.EXACT)
        self.play(Transform(dot, back, run_time=1.0), quotient.animate.set_color(Palette.EXACT))
        exact_lbl = digits(n["rate_short"], 22, Palette.EXACT).next_to(line.n2p(x_exact), UP, buff=0.3).shift(RIGHT * 0.7)
        self.play(FadeIn(exact_lbl, run_time=0.4))
        new_stored_lbl = words("exact rate", SANS, Palette.MUTED)
        new_stored_lbl.move_to([-6.3 + new_stored_lbl.width / 2, y0 - 2.7, 0])
        new_stored = digits(n["rate_short"], MONO, Palette.EXACT).next_to(new_stored_lbl, RIGHT, buff=0.45).set_y(y0 - 2.7)
        self.play(Transform(stored, new_stored, run_time=0.6), Transform(stored_lbl, new_stored_lbl, run_time=0.6))
        self.wait(2.0)

        new_l, new_r = check_row(n["rate_short"], n["ltv_exact"], f">  {n['max_ltv']}", Palette.EXACT)
        new_tick = cross_mark(Palette.WRONG).next_to(new_r, RIGHT, buff=0.45).set_y(y_chk)
        new_verdict = words("insolvent", 22, Palette.WRONG).next_to(new_tick, RIGHT, buff=0.25).set_y(y_chk)
        self.play(Transform(row_l, new_l, run_time=0.9), Transform(row_r, new_r, run_time=0.9), Transform(tick, new_tick, run_time=0.9), Transform(verdict, new_verdict, run_time=0.9))
        self.wait(1.5)
        ratio = markup(f"<span foreground='{Palette.WRONG}'>{n['ratio']}×</span> the limit", SANS, Palette.TEXT)
        ratio.move_to([-6.3 + ratio.width / 2, y_chk - 0.75, 0])
        self.play(FadeIn(ratio, shift=UP * 0.08, run_time=0.7))
        self.wait(12.0)

"""Slide 6, "Resupply, 26 June 2025": one floor, in full.

The exchange rate is 10^36 ÷ price (ResupplyPairCore.sol:573). The price
the oracle returned types in; the long division runs out digit by digit
to its 30th decimal and is labelled "(to 30 decimals)"; on the integer
grid the rate is stored on, the value sits between 0 and 1 and the floor
snaps it to 0 (WRONG, red). The solvency check (ResupplyPairCore.sol:282)
then reads 10,000,000 × 0 × 10^5 = 0 ≤ 95,000 and draws an emerald tick.
Then the half is restored: the dot returns to the exact value, named to
22 decimals (the fewest at which it still reads below one half; at 21 it
rounds to 0.5), the LTV recomputes to 499,999,999,999.9999999995004995
(to 16 decimals), the comparison with 95,000 reads 5,263,158× and the
tick becomes a red cross. About 66 s.

No number on screen carries an ellipsis: each is complete in a stated
format, rounded half-up at the stated decimal (check.py asserts both).

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

QUOTIENT_DIGITS = 30  # decimals of the long division, complete and labelled
LTV_DECIMALS = 16  # decimals of the exact LTV, complete and labelled
RATE_SHORT = 22  # decimals of the rate where it is named in passing: the fewest that still read below one half
GRID = (0, 2, 1)  # the integer grid the stored rate lives on
MONO = 30
SANS = 28
SMALL = 14  # the Solidity citations
CHECK = 24  # the solvency rows
LABEL = 18  # "(to N decimals)"


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
    return {
        "block": thousands(p["block"]),
        "price": thousands(price),
        "quotient": _rounded(rate, QUOTIENT_DIGITS),
        "quotient_label": to_decimals(QUOTIENT_DIGITS),
        "rate_short": _rounded(rate, RATE_SHORT),
        "rate_label": to_decimals(RATE_SHORT),
        "floor": str(floor),
        "borrow_tokens": thousands(borrow // ex_p),  # reUSD, exact
        "collateral": thousands(coll),
        "ltv_exp": _power_of_ten(ltv_p),
        "ltv_floor": thousands(ltv_floor),
        "max_ltv": thousands(max_ltv),
        "max_ltv_pct": pct + "%",
        "ltv_exact": _rounded(ltv, LTV_DECIMALS),
        "ltv_label": to_decimals(LTV_DECIMALS),
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
        quotient_lbl = words(n["quotient_label"], LABEL, Palette.FAINT).next_to(quotient, RIGHT, buff=0.3).set_y(y0 - 1.95)
        self.play(FadeIn(q_lbl, run_time=0.4))
        self.play(AddTextLetterByLetter(quotient, time_per_char=0.09))
        self.play(FadeIn(quotient_lbl, run_time=0.4))
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

        def rate_label(size: float) -> VGroup:
            """The exact rate to RATE_SHORT decimals with its format stated, to the
            right of the dot so the floor arrow (leftwards) stays clear."""
            value = digits(n["rate_short"], size, Palette.EXACT)
            stated = words(n["rate_label"], LABEL, Palette.FAINT).next_to(value, RIGHT, buff=0.25)
            return VGroup(value, stated)

        exact_lbl = rate_label(22)
        exact_lbl.next_to(line.n2p(x_exact), UP, buff=0.3).align_to(line.n2p(x_exact) + RIGHT * 0.15, LEFT)
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

        # the solvency check, as deployed: two rows, the product and the comparison
        y_chk = -1.72
        y_cmp = y_chk - 0.52
        chk_src = digits(n["ltv_line"], SMALL, Palette.FAINT)
        chk_src.move_to([-6.3 + chk_src.width / 2, y_chk + 0.47, 0])
        self.play(FadeIn(chk_src, run_time=0.5))
        self.wait(1.0)

        def stated(label: str | None) -> str:
            """A rounded number's format, small and faint, right after it; nothing after an integer."""
            return f" <span foreground='{Palette.FAINT}' size='small'>{label}</span>" if label else ""

        def check_rows(rate_str: str, rate_fmt: str | None, ltv_str: str, ltv_fmt: str | None, cmp: str, colour: str):
            top = markup(
                f"LTV  =  {n['borrow_tokens']} × <span foreground='{colour}'>{rate_str}</span>{stated(rate_fmt)} × 10<sup>{n['ltv_exp']}</sup>",
                CHECK,
                Palette.TEXT,
            )
            top.move_to([-6.3 + top.width / 2, y_chk, 0])
            bottom = markup(f"=  <span foreground='{colour}'>{ltv_str}</span>{stated(ltv_fmt)}", CHECK, Palette.TEXT)
            bottom.move_to([-6.3 + bottom.width / 2, y_cmp, 0])
            right = markup(cmp, CHECK, Palette.TEXT).next_to(bottom, RIGHT, buff=0.5).set_y(y_cmp)
            return top, bottom, right

        row_t, row_b, row_r = check_rows(n["floor"], None, n["ltv_floor"], None, f"≤  {n['max_ltv']}  ({n['max_ltv_pct']})", Palette.WRONG)
        self.play(FadeIn(row_t, shift=RIGHT * 0.1, run_time=0.6))
        self.play(FadeIn(row_b, shift=RIGHT * 0.1, run_time=0.6))
        self.wait(1.5)
        self.play(FadeIn(row_r, run_time=0.5))
        tick = check_mark(Palette.CORRECT).next_to(row_r, RIGHT, buff=0.45).set_y(y_cmp)
        verdict = words("solvent", 22, Palette.CORRECT).next_to(tick, RIGHT, buff=0.25).set_y(y_cmp)
        self.play(Create(tick, run_time=0.5))
        self.play(FadeIn(verdict, run_time=0.4))
        self.wait(9.0)

        # the half, restored
        self.play(FadeOut(arrow, run_time=0.4), FadeOut(floor_lbl, run_time=0.4))
        back = dot.copy().move_to(line.n2p(x_exact)).set_color(Palette.EXACT)
        self.play(Transform(dot, back, run_time=1.0), quotient.animate.set_color(Palette.EXACT))
        exact_lbl = rate_label(22)
        exact_lbl.next_to(line.n2p(x_exact), UP, buff=0.3).align_to(line.n2p(x_exact) + RIGHT * 0.15, LEFT)
        self.play(FadeIn(exact_lbl, run_time=0.4))
        new_stored_lbl = words("exact rate", SANS, Palette.MUTED)
        new_stored_lbl.move_to([-6.3 + new_stored_lbl.width / 2, y0 - 2.7, 0])
        new_stored = rate_label(MONO).next_to(new_stored_lbl, RIGHT, buff=0.45)
        new_stored[0].set_y(y0 - 2.7)
        new_stored[1].set_y(y0 - 2.7)
        self.play(Transform(stored, new_stored[0], run_time=0.6), Transform(stored_lbl, new_stored_lbl, run_time=0.6), FadeIn(new_stored[1], run_time=0.6))
        self.wait(2.0)

        # each rounded number carries its stated format; the comparison follows the LTV's
        new_t, new_b, new_r = check_rows(n["rate_short"], n["rate_label"], n["ltv_exact"], n["ltv_label"], f">  {n['max_ltv']}", Palette.EXACT)
        new_tick = cross_mark(Palette.WRONG).next_to(new_r, RIGHT, buff=0.45).set_y(y_cmp)
        new_verdict = words("insolvent", 22, Palette.WRONG).next_to(new_tick, RIGHT, buff=0.25).set_y(y_cmp)
        self.play(
            Transform(row_t, new_t, run_time=0.9),
            Transform(row_b, new_b, run_time=0.9),
            Transform(row_r, new_r, run_time=0.9),
            Transform(tick, new_tick, run_time=0.9),
            Transform(verdict, new_verdict, run_time=0.9),
        )
        self.wait(1.5)
        ratio = markup(f"<span foreground='{Palette.WRONG}'>{n['ratio']}×</span> the limit", SANS, Palette.TEXT)
        ratio.move_to([-6.3 + ratio.width / 2, y_cmp - 0.62, 0])
        self.play(FadeIn(ratio, shift=UP * 0.08, run_time=0.7))
        self.wait(12.0)

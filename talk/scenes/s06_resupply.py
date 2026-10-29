"""Slide 6, "Resupply, 26 Jun 2025": one floor, in full, as things.

The attacker's tank pours 2,000 crvUSD into the empty cvcrvUSD vault; one
block, 1 share, is minted; the vault's quantity becomes the oracle's price
per share (the one number of the beat, HERO). The tanks slide back; a
lattice 0–2 (the integer grid the stored rate lives on) rises; a ball,
the exchange rate 10^36 ÷ price, hovers at 0.4999999999999999999995 (to
22 decimals: the fewest at which it still reads below one half); the
camera dollies in on the half. The floor: the ball drops and rolls to 0
in RED, the direction arrow on the ground, tick 0 lit. The check: a gate
labelled 10,000,000 × 0 = 0 ≤ 95,000 opens EMERALD (ResupplyPairCore.sol:
282, the caption), 10,000,000 reUSD pour into the attacker's tank while
the 1 share sits as collateral. The half restored: the ball lifts back to
0.4999… in white, the gate's label becomes 499,999,999,999.9999999995004995
> 95,000 and it shuts RED under a cross: insolvent. The multiplier: all
but the gate dims; 5,263,158× the limit (claim V12).

Six sections, one per click: price, division, floor, check, half,
multiplier. No number on screen carries an ellipsis: each is complete in
a stated format, rounded half-up at the stated decimal (check.py asserts
both).

Numbers from scripts/replays/resupply.json: .pins.price, .borrowAmount,
.collateral, .maxLTV, .ltvPrecision, .exchangePrecision, .block,
.donation, .mintShares, .vaultTotalSupply; the two Solidity lines from
.citations (file, line, text); the title's date from incidents.json.
Every value is computed here from the pins with Fraction and Decimal, as
docs/benchmarks/replay-resupply.md does: rate = 10^36 / price; LTV =
borrow × rate × ltvPrecision / exchangePrecision / collateral.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
import re
from math import log10

from manim import DEGREES, DOWN, OUT, RIGHT, UP, FadeIn, FadeOut, VGroup

from vocab import SIZE_BODY, SIZE_HERO, Palette, digits, incidents, markup, resupply, thousands, words
from vocab3d import Ball, DeckScene3D, Gate, Lattice, Stack, Tank, dim, dolly, drop_snap, lift, orbit, pour, shut, slide, transfer
from vocab3d import open as open_gate

QUOTIENT_DIGITS = 30  # decimals of the long division (numbers() keeps it for s07 and check.py; the slide no longer draws it)
LTV_DECIMALS = 16  # decimals of the exact LTV, complete and labelled
RATE_SHORT = 22  # decimals of the rate where it is named: the fewest that still read below one half
GRID = (0, 2, 1)  # the integer grid the stored rate lives on
PRICE_SPLIT = 26  # the price per share is 49 characters: at HERO it is two lines, broken after this many (a thousands group ends there)


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


LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers() (the formula's 36 is read from the cited line)


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
    rate_exp = _numerator_exp(cite[573]["text"])
    assert 10**rate_exp == 10**36 and rate == Fraction(10**rate_exp, price), rate_exp
    inc = next(i for i in incidents()["incidents"] if i["protocol"] == "Resupply")
    donation, mint_shares, supply_after = int(p["donation"]), int(p["mintShares"]), int(p["vaultTotalSupply"])
    assert donation % ex_p == 0 and supply_after - mint_shares == 0  # the vault had no shares before the mint
    return {
        "title": f"{inc['protocol']}, {inc['date']}",
        "block": thousands(p["block"]),
        "rate_exp": rate_exp,
        "base": 10,
        "grid_ticks": list(range(GRID[0], GRID[1] + 1)),
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
        "rate_cite": f"{cite[573]['file'].rsplit('/', 1)[-1]}:{cite[573]['line']}",
        "ltv_cite": f"{cite[282]['file'].rsplit('/', 1)[-1]}:{cite[282]['line']}",
        "donation_tokens": thousands(donation // ex_p),  # crvUSD, exact
        "mint_shares": str(mint_shares),
        "shares_before": str(supply_after - mint_shares),
    }


class Resupply(DeckScene3D):
    SECTIONS = ("price", "division", "floor", "check", "half", "multiplier")

    def construct(self):
        n = numbers()
        assert n["solvent_floor"] and not n["solvent_exact"]
        x_exact = float(Fraction(10**36, int(resupply()["pins"]["price"])))  # 0.5 in float64: the gap of 5 × 10^-22 is in the digits, not on the ground

        # ---- price: a donation into an empty vault
        self.section(0)
        self.caption_now(f"scripts/replays/resupply.json · block {n['block']}")
        self.fix(self.title(n["title"]))
        vault = Tank("cvcrvUSD vault", level=0.0, colour=Palette.GOLD, quantity=f"{n['shares_before']} shares", at=[-2.2, 0.4, 0], height=1.8)
        attacker = Tank("attacker", level=0.78, colour=Palette.GOLD, quantity=f"{n['donation_tokens']} crvUSD", at=[3.0, 0.4, 0], height=1.8)
        self.show(vault, attacker)
        self.play(FadeIn(vault, attacker, vault.name, vault.quantity, attacker.name, attacker.quantity, run_time=0.8))
        self.wait(0.4)
        self.play(pour(attacker, vault, 0.78, run_time=2.4))
        emptied = digits(f"{n['floor']} crvUSD", SIZE_BODY, Palette.GOLD)
        self.play(self.relabel(attacker.quantity, emptied, run_time=0.5))
        attacker.quantity = emptied
        share = Stack(1, Palette.VIOLET, label=f"{n['mint_shares']} share", at=[-4.3, -1.3, 0])
        self.show(share)
        share.label.set_opacity(0)
        self.play(share.appear(), share.label.animate.set_opacity(1), run_time=0.6)
        self.wait(0.3)
        price_lines = n["price"][:PRICE_SPLIT] + "\n" + n["price"][PRICE_SPLIT:]
        assert n["price"][PRICE_SPLIT - 1] == "," and price_lines.replace("\n", "") == n["price"]
        price = VGroup(digits(price_lines, SIZE_HERO, Palette.EXACT, line_spacing=0.7), words("per share", SIZE_BODY, Palette.MUTED)).arrange(DOWN, buff=0.12)
        self.play(self.relabel(vault.quantity, price, run_time=0.9, offset=UP * 0.9))
        vault.quantity = price

        # ---- division: the lattice rises; the rate hovers just under the half
        self.section(1, hold=2.0)
        aside = 0.0  # parked out of frame; perspective would still show a dimmed tank at the edge
        self.play(
            FadeOut(price, run_time=0.6),
            slide(vault, [-7.8, 0.6, 0], opacity=aside),
            slide(attacker, [6.8, 0.6, 0], opacity=aside),
            transfer(share, [-11.5, -0.5, 0], opacity=aside),
            *[m.animate.set_opacity(aside) for m in (vault.name, attacker.name, attacker.quantity, share.label)],
            run_time=1.2,
        )
        self.remove(vault, vault.name)  # parked and invisible: a later dim must not bring it back
        lattice = Lattice(GRID, length=6.5, at=[-1.6, -0.6, 0], minor=0.5)
        self.show(lattice)
        for num in lattice.numbers.values():
            num.set_opacity(0)
        lattice.shift(OUT * -1.4)
        orbit(self, 62 * DEGREES, -66 * DEGREES, run_time=1.6, added_anims=[lattice.animate.shift(OUT * 1.4), *[num.animate.set_opacity(1) for num in lattice.numbers.values()]])
        ball = Ball(Palette.EXACT, at=lattice.point(x_exact) + OUT * (0.9 + 0.24))
        formula = markup(f"{n['base']}<sup>{n['rate_exp']}</sup> ÷ price", SIZE_BODY, Palette.MUTED)
        value = VGroup(digits(n["rate_short"], SIZE_BODY, Palette.EXACT), words(n["rate_label"], SIZE_BODY, Palette.FAINT)).arrange(RIGHT, buff=0.25)
        rate_label = VGroup(formula, value).arrange(DOWN, buff=0.12)
        self.add(ball)
        self.billboard(rate_label, ball, UP * 0.95)
        rate_label.set_opacity(0)
        self.play(FadeIn(ball, shift=OUT * 0.3, run_time=0.6), rate_label.animate.set_opacity(1))
        self.wait(0.4)
        dolly(self, 1.8, at=ball.get_center() - OUT * 0.45, run_time=1.6)

        # ---- floor: the ball drops and rolls to 0
        self.section(2, hold=2.0)
        dolly(self, 1.0, run_time=1.2)
        anim, arrow = drop_snap(ball, lattice, x_exact, float(n["floor"]), Palette.WRONG)
        floor_lbl = words("floor", SIZE_BODY, Palette.WRONG)
        self.billboard(floor_lbl, (lattice.point(x_exact) + lattice.point(float(n["floor"]))) / 2, UP * 0.8)
        floor_lbl.set_opacity(0)
        self.play(anim, rate_label.animate.set_opacity(0))
        self.remove(rate_label)
        self.play(
            floor_lbl.animate.set_opacity(1),
            lattice.post(float(n["floor"])).animate.set_fill(Palette.WRONG).set_stroke(Palette.WRONG),
            lattice.numbers[float(n["floor"])].animate.set_color(Palette.WRONG),
            run_time=0.5,
        )

        # ---- check: the gate opens on 10,000,000 × 0
        self.section(3, hold=2.0)
        self.play(self.caption(f"{n['ltv_cite']} · scripts/replays/resupply.json · block {n['block']}"))
        gate = Gate(f"{n['borrow_tokens']} × {n['floor']} = {n['ltv_floor']} ≤ {n['max_ltv']}", lattice, x=1.5, label_lift=0.55, mark_lift=1.3)
        self.show(gate)
        gate.label.set_opacity(0)
        self.play(FadeIn(gate, shift=OUT * 0.6), gate.label.animate.set_opacity(1), run_time=0.9)
        self.play(open_gate(gate, self))
        reusd = Tank("reUSD", level=0.85, colour=Palette.SAPPHIRE, quantity=n["borrow_tokens"], at=[4.9, 2.2, 0])
        self.show(reusd)
        self.play(
            FadeIn(reusd, reusd.name, reusd.quantity, run_time=0.6),
            slide(attacker, [-6.6, -2.2, 0], opacity=1.0),
            attacker.name.animate.set_opacity(1),
            attacker.quantity.animate.set_opacity(1),
            transfer(share, lattice.point(1.5) + DOWN * 1.3 + RIGHT * 0.8, opacity=1.0),
            share.label.animate.set_opacity(1),
            run_time=1.0,
        )
        collateral = digits(f"{n['mint_shares']} share\ncollateral", SIZE_BODY, Palette.VIOLET, line_spacing=0.8)
        self.play(self.relabel(share.label, collateral, run_time=0.5))
        share.label = collateral
        self.play(pour(reusd, attacker, 0.85, run_time=2.4))
        borrowed = digits(f"{n['borrow_tokens']} reUSD", SIZE_BODY, Palette.SAPPHIRE)
        self.play(self.relabel(attacker.quantity, borrowed, run_time=0.5))
        attacker.quantity = borrowed

        # ---- half: the ball lifts back; the gate shuts on the exact LTV
        self.section(4, hold=2.5)
        self.play(FadeOut(arrow, floor_lbl, run_time=0.4), lattice.post(float(n["floor"])).animate.set_fill(Palette.FAINT).set_stroke(Palette.FAINT), lattice.numbers[float(n["floor"])].animate.set_color(Palette.FAINT))
        self.play(lift(ball, lattice, x_exact, Palette.EXACT))
        exact = digits(f"{n['ltv_exact']}\n> {n['max_ltv']}", SIZE_BODY, Palette.MUTED, line_spacing=0.8)  # two lines: on one it is 10.9 units wide
        self.play(self.relabel(gate.label, exact, run_time=0.8))
        gate.label = exact
        gate.labels = [(exact, gate.top, UP * gate.label_lift)]
        self.wait(0.6)
        verdict = words("insolvent", SIZE_BODY, Palette.WRONG)
        self.billboard(verdict, gate.top, UP * gate.mark_lift + RIGHT * 1.2)
        gate.extras.append(verdict)
        verdict.set_opacity(0)
        self.play(shut(gate, self), verdict.animate.set_opacity(1))

        # ---- multiplier: all but the gate dims; the one number
        self.section(5, hold=2.0)
        self.play(dim(self.dimmable(gate), 0.12))
        ratio = markup(f"<span foreground='{Palette.WRONG}'>{n['ratio']}×</span> the limit", SIZE_HERO, Palette.TEXT)
        self.billboard(ratio, gate.top, UP * 1.95)
        ratio.set_opacity(0)
        self.play(ratio.animate.set_opacity(1), run_time=0.7)
        self.close()

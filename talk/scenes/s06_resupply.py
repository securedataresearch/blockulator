"""Slide 6, "Resupply, 26 Jun 2025": one floor, in full, as things.

The attacker's tank pours 2,000 crvUSD into the empty cvcrvUSD vault; one
block, 1 share, is minted; the vault's quantity becomes the oracle's price
per share (the one number of the beat, HERO). The tanks slide back; a
lattice 0–2 (the integer grid the stored rate lives on) rises; a ball,
the exchange rate 10^36 ÷ price, hovers at 0.4999999999999999999995 (to
22 decimals: the fewest at which it still reads below one half); the
camera dollies in on the half. The floor: the ball drops and rolls to 0
in RED, the direction arrow on the ground, tick 0 lit. The check, cause
then effect, one beat at a time: a Gauge rises beside the lattice with
the Gate behind it, its three input bars borrow 10,000,000, rate,
collateral 1; a wire draws from the ball at 0 to the rate input and the
bar collapses to 0; the needle swings to 0, the readout reads 10,000,000
× 0 / 1 = 0, the green arc glows, the limit mark reads ≤ 95,000; a held
second; the gate lifts EMERALD under a check (ResupplyPairCore.sol:282,
the caption); the pool (10,000,000 reUSD) drains to empty into the
attacker's pocket, which grows to the pool's size as it fills, while the
1 share block sits beside the collateral input as collateral: 1
share-wei; the camera orbits during the pour. The half restored, the
counterfactual on the same gauge: the pool refills and the pocket
shrinks back (the rewind), the ball lifts to 0.4999… in white with its
value, the wire re-draws, the rate bar rises, the needle swings past the
limit and pins at the end of the red arc, the readout becomes
499,999,999,999.9999999995004995 and the limit mark > 95,000, a bracket
along the red arc reads 5,263,158× the limit (HERO, claim V12), the gate
shuts RED under a cross: insolvent. The multiplier: all but the gauge,
its bracket and the shut gate dims (the poster).

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

from manim import DEGREES, DOWN, LEFT, OUT, RIGHT, UP, Create, FadeIn, FadeOut, VGroup

from vocab import SIZE_BODY, SIZE_HERO, Palette, digits, incidents, markup, resupply, thousands, words
from vocab3d import Ball, DeckScene3D, Gate, Gauge, Lattice, Stack, Tank, dim, dolly, drop_snap, lift, orbit, pour, shut, slide, transfer, wire
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


# every digit on the slide is a value of numbers() (the formula's 36 is read from the cited line); the gauge's
# input names, the pool's name and the collateral label are claim C1's words (research_notes/talk/claims.md)
LITERALS: dict[str, str] = {"borrow": "C1", "rate": "C1", "collateral": "C1", "the pool": "C1", "collateral: 1 share-wei": "C1"}


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

        # ---- check: the ball's 0 drives the gauge; the needle at 0 lifts the gate; the pool pours against one share
        self.section(3, hold=2.0)
        facing = -62 * DEGREES + 90 * DEGREES  # the dial faces the camera midway through the pour's orbit (−66° to −58°)
        gate = Gate(None, at=[-2.4, 1.5, 0], width=2.2, height=1.4, mark_lift=0.3).face(facing)
        gauge = Gauge(
            n["max_ltv"],
            [("borrow", n["borrow_tokens"], 0.78), ("rate", None, x_exact), ("collateral", n["collateral"], 0.08)],
            at=[1.05, -0.4, 0],
            facing=facing,
            radius=1.0,
            pivot=2.2,
            bar_width=1.8,
        )
        self.show(gate, gauge)
        gauge_labels = VGroup(*[m for m, _, _ in gauge.labels])
        gate.shift(OUT * -1.2)
        gauge.shift(OUT * -1.2)
        gauge_labels.set_opacity(0)
        dolly(
            self,
            0.78,
            at=None,  # the zoom only: a re-centred frame drags the fixed-in-frame chrome with it
            run_time=1.0,
            added_anims=[
                self.caption(f"{n['ltv_cite']} · scripts/replays/resupply.json · block {n['block']}"),
                lattice.stretch(0.4, about=float(n["floor"]), run_time=1.0),  # the lattice makes room about the ball's 0 (the floor has had its frame)
                FadeOut(arrow, floor_lbl, run_time=0.4),
                gate.animate.shift(OUT * 1.2),
                gauge.animate.shift(OUT * 1.2),
                gauge_labels.animate.set_opacity(1),
            ],
        )
        floor_lbl = words("floor", SIZE_BODY, Palette.WRONG)
        self.billboard(floor_lbl, ball, UP * 0.62)
        # 1. the wire from the ball at 0: the rate input collapses
        line = wire(ball, gauge, "rate", Palette.WRONG)
        self.play(Create(line, run_time=0.5))
        rate_zero = digits(n["floor"], SIZE_BODY, Palette.WRONG)
        self.billboard(rate_zero, lambda: gauge.inputs["rate"][0].get_right(), RIGHT * 0.44)
        rate_zero.set_opacity(0)
        self.play(gauge.set_input("rate", 0.0, run_time=0.6, colour=Palette.WRONG), rate_zero.animate.set_opacity(1))
        # 2. the needle swings to 0; the readout; the green arc glows; the limit mark reads "≤ 95,000"; hold
        readout = digits(f"{n['borrow_tokens']} × {n['floor']} / {n['collateral']} = {n['ltv_floor']}", SIZE_BODY, Palette.CORRECT)
        self.billboard(readout, gauge.top, UP * 1.15 + LEFT * 0.2)
        readout.set_opacity(0)
        under = digits(f"≤ {n['max_ltv']}", SIZE_BODY, Palette.CORRECT)
        self.play(gauge.aim(Gauge.angle_of(0.0, 1.0), Palette.CORRECT, run_time=0.8), readout.animate.set_opacity(1))
        self.play(gauge.glow(0.8), self.relabel(gauge.limit_label, under, run_time=0.4))
        gauge.limit_label = under
        self.wait(1.0)
        # 3. the gate lifts
        self.play(open_gate(gate, self))
        # 4. the pool pours out, all of it, against the one share
        two_lines = {"line_spacing": 0.8}  # "10,000,000 reUSD" on one line is 4.2 units: too wide beside the dial
        pool = Tank("the pool", level=0.85, colour=Palette.SAPPHIRE, quantity=f"{n['borrow_tokens']}\nreUSD", at=[5.7, 3.9, 0], radius=0.7, height=1.3, stacked=True, label_shift=RIGHT * 0.45)
        pocket = Tank("attacker", level=0.0, colour=Palette.GOLD, quantity=f"{n['floor']} crvUSD", at=[7.1, -1.6, 0], radius=0.4, height=0.9, stacked=True, label_shift=RIGHT * 0.25)
        self.show(pool, pocket)
        collateral = words("collateral: 1 share-wei", SIZE_BODY, Palette.VIOLET)
        self.play(
            FadeIn(pool, pool.name, pool.quantity, pocket, pocket.name, pocket.quantity, run_time=0.6),
            transfer(share, [1.05, -2.7, 0], opacity=1.0),
            self.relabel(share.label, collateral, run_time=0.6, offset=DOWN * 0.7),
            run_time=0.8,
        )
        share.label = collateral
        share.labels = [(collateral, share.top, DOWN * 0.7)]
        orbit(self, 56 * DEGREES, -58 * DEGREES, run_time=3.0, added_anims=[pour(pool, pocket, 0.85, run_time=3.0, drops=14, grow=(0.7, 1.3))])
        taken = digits(f"{n['borrow_tokens']}\nreUSD", SIZE_BODY, Palette.SAPPHIRE, **two_lines)
        emptied_pool = digits(f"{n['floor']} reUSD", SIZE_BODY, Palette.SAPPHIRE)
        self.play(self.relabel(pocket.quantity, taken, run_time=0.5, offset=UP * (0.72 + taken.height / 2)), self.relabel(pool.quantity, emptied_pool, run_time=0.5, offset=UP * (0.72 + emptied_pool.height / 2)))
        pocket.quantity, pool.quantity = taken, emptied_pool

        # ---- half: the exact rate on the same gauge; the needle pins in the red; the gate shuts; the pool stays
        self.section(4, hold=2.5)
        self.play(FadeOut(line, floor_lbl, rate_zero, run_time=0.4), lattice.post(float(n["floor"])).animate.set_fill(Palette.FAINT).set_stroke(Palette.FAINT), lattice.numbers[float(n["floor"])].animate.set_color(Palette.FAINT))
        refilled = digits(f"{n['borrow_tokens']}\nreUSD", SIZE_BODY, Palette.SAPPHIRE, **two_lines)
        emptied = digits(f"{n['floor']} crvUSD", SIZE_BODY, Palette.GOLD)
        orbit(
            self,
            62 * DEGREES,
            -66 * DEGREES,
            run_time=1.8,
            added_anims=[
                lift(ball, lattice, x_exact, Palette.EXACT),
                pour(pocket, pool, 0.85, run_time=1.8, drops=6, grow=(0.4, 0.9)),  # the rewind: the pocket empties and shrinks back
                self.relabel(pool.quantity, refilled, run_time=0.6, offset=UP * (0.72 + refilled.height / 2)),
                self.relabel(pocket.quantity, emptied, run_time=0.6, offset=UP * (0.72 + emptied.height / 2)),
            ],
        )
        pool.quantity, pocket.quantity = refilled, emptied
        rate_lbl = VGroup(digits(n["rate_short"], SIZE_BODY, Palette.EXACT), words(n["rate_label"], SIZE_BODY, Palette.FAINT)).arrange(DOWN, buff=0.1)
        self.billboard(rate_lbl, ball, UP * 0.9 + RIGHT * 2.4)
        rate_lbl.set_opacity(0)
        line = wire(ball, gauge, "rate", Palette.EXACT)
        self.play(Create(line, run_time=0.5), rate_lbl.animate.set_opacity(1))
        self.play(gauge.set_input("rate", x_exact, run_time=0.6, colour=Palette.EXACT))
        exact = digits(n["ltv_exact"], SIZE_BODY, Palette.WRONG)
        over = digits(f"> {n['max_ltv']}", SIZE_BODY, Palette.WRONG)
        self.play(gauge.aim(Gauge.angle_of(2.0, 1.0), Palette.WRONG, run_time=1.0), self.relabel(readout, exact, run_time=0.6), self.relabel(gauge.limit_label, over, run_time=0.6))
        readout, gauge.limit_label = exact, over
        brace = gauge.bracket()
        ratio = markup(f"<span foreground='{Palette.WRONG}'>{n['ratio']}×</span>\nthe limit", SIZE_HERO, Palette.TEXT, line_spacing=0.6)
        self.billboard(ratio, gauge.bracket_anchor, RIGHT * 1.3 + DOWN * 0.7)
        gauge.extras += [brace, ratio, readout]
        ratio.set_opacity(0)
        self.play(Create(brace, run_time=0.5), ratio.animate.set_opacity(1))
        verdict = words("insolvent", SIZE_BODY, Palette.WRONG)
        self.billboard(verdict, gate.top, LEFT * 1.7 + UP * 0.5)
        gate.extras.append(verdict)
        verdict.set_opacity(0)
        self.play(shut(gate, self), verdict.animate.set_opacity(1))

        # ---- multiplier: all but the gauge, its bracket and the shut gate dims
        self.section(5, hold=2.0)
        self.play(dim(self.dimmable(gauge, gate), 0.12))
        self.close()

"""Slide 6d, "Thetanuts, 15 Jun 2026": thirty-seven floors of two thirds of a unit.

The edit pass's replay shape (talk/briefs/edit-pass.md, row 9; the model is
s06c): one idea per section, each section owns the frame, the poster holds
the conclusion.

The transaction's own integers (scripts/replays/thetanuts.json, through
vocab.thetanuts(); the vault's source is unverified, so the replay is pinned
to bytecode). Before: one claim redeems the index supply, 153,054,600,572,
down to 3 raw units. Step: a mint charges stored × amount / supply of each
component; the first is 1 × 2 / 3 = 0.666667 (to 6 decimals). Round: a
transfer moves whole raw units and EVM DIV floors, so the charge is 0.
Repeat: 37 mints in the one transaction, the amounts doubling (the dots grow
with the amount's bit length), every charge 0. Take: incidents.json's loss
line. Exact: BL127 and BL19 carry the two thirds, but precision does not
decide a rounding at a unit; their ceil does (docs/benchmarks/replay-
thetanuts.md, "The decisive step on each rule": BL127 / BL19 → ceil to a raw
unit gives 1, and the 37 amounts rerun with ceil cost 76,596,174,855 raw
units per component, more than the claim took of any one: the attack would
lose; their floor gives 0, "precision without direction"). Computed, not
observed: hence "would".

Six sections, one per click: before, step, round, repeat, take, exact.
Provenance (tx, block, pc 12186/12220, the realised USDC, the rest of the
vault) is in the slide's notes.

Every digit on screen is a value of numbers() (read from the JSON and
computed with Fraction) or a library name.
"""

from __future__ import annotations

from fractions import Fraction

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    LaggedStart,
    Rectangle,
    RoundedRectangle,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_in_out_cubic, ease_out_cubic

from vocab import (
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
    replay_table,
    snap,
    thetanuts,
    thousands,
    to_decimals,
    words,
)

INCIDENT = "Thetanuts"
HUE = Palette.SLATE  # Thetanuts' hue in the deck: its supply, its counter, its loss
CHARGE_DECIMALS = 6  # decimals of the first mint's exact charge, complete and labelled
GRID = (0, 2, 1)  # the raw-unit grid a transfer moves on
SIZE_TAKE = 72  # the loss, alone on its frame (edit-pass: a lone hero number at 64–72)
SIZE_COUNT = 64  # the repetition counter

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers() or a library's name


def ceil_replay(mints: list[dict], stored: int, supply: int) -> list[int]:
    """The 37 mints from the post-claim state with each charge rounded up
    (the counterfactual): the per-mint charges. One column covers all five
    components: they all start at the same stored amount."""
    charges = []
    for m in mints:
        a = int(m["amount"])
        c = -(-stored * a // supply)  # ceil
        charges.append(c)
        stored += c
        supply += a
    return charges


def numbers() -> dict:
    d = thetanuts()
    inc = next(i for i in incidents()["incidents"] if i["protocol"] == INCIDENT)
    pre, post, claim, mints, fl = d["pre"], d["post"], d["claim"], d["mints"], d["flashLoan"]
    supply_before = int(pre["totalSupply"])
    supply = int(claim["supplyAfter"])
    assert supply_before - int(fl["amount"]) == supply == int(mints[0]["supplyBefore"])
    (stored,) = {int(s) for s in claim["storedAfter"]}
    assert all(int(s) == stored for s in mints[0]["storedBefore"])
    # the first mint: charge = stored × amount / supply, exact, then floored as the chain did
    m0 = mints[0]
    amount0 = int(m0["amount"])
    charge0 = Fraction(stored * amount0, supply)
    floor0 = stored * amount0 // supply
    ceil0 = -(-stored * amount0 // supply)
    assert all(int(c) == floor0 for m in mints for c in m["charge"]), "every charge on the chain is the first's floor"
    amounts = [int(m["amount"]) for m in mints]
    assert all(int(m["supplyAfter"]) == int(m["supplyBefore"]) + int(m["amount"]) for m in mints)
    assert int(mints[-1]["supplyAfter"]) == int(post["totalSupply"])
    minted = sum(amounts)
    assert minted == int(post["totalSupply"]) - supply
    # the counterfactual: the same amounts, the charge rounded up; it costs more than the claim took of any one component
    ceil_charges = ceil_replay(mints, stored, supply)
    ceil_total = sum(ceil_charges)
    max_take = max(int(p) for p in claim["payout"])
    assert ceil_charges[0] == ceil0 and min(ceil_charges) >= 1
    # the generated table says BL127 and BL19 ceil to the same 1 and the same total, and floor to 0
    rules = {r["rule"]: r for r in replay_table("thetanuts", "The decisive step on each rule")}
    for lib in ("BL127", "BL19"):
        up, down = rules[f"{lib} → ceil to a raw unit"], rules[f"{lib} → floor to a raw unit"]
        assert up["first charge (raw units)"].endswith(f"→ {ceil0}") and up["paid per component, 37 mints"] == thousands(ceil_total), up
        assert down["first charge (raw units)"].endswith(f"→ {floor0}") and down["paid per component, 37 mints"] == str(floor0), down
    return {
        "title": f"{inc['protocol']}, {inc['date']}",
        "supply_before": thousands(supply_before),
        "supply": str(supply),
        "stored": str(stored),
        "amount0": str(amount0),
        "charge0": to_decimals(charge0, CHARGE_DECIMALS),
        "charge0_label": f"(to {CHARGE_DECIMALS} decimals)",
        "charge0_x": charge0,
        "floor0": str(floor0),
        "ceil0": str(ceil0),
        "grid_ticks": list(range(GRID[0], GRID[1] + 1)),
        "n_mints": len(mints),
        "counter_ticks": list(range(1, len(mints) + 1)),
        "amount_bits": [a.bit_length() for a in amounts],
        "loss": inc["loss"],
        "repaid": minted == int(fl["amount"]) + int(fl["premium"]),
        "ceil_total": ceil_total,
        "max_take": max_take,
        "would_lose": ceil_total > max_take,
    }


class Thetanuts(DeckScene):
    SECTIONS = ("before", "step", "round", "repeat", "take", "exact")

    Y_OPERANDS, Y_PRODUCT, Y_LINE = 2.05, 1.15, -0.45
    LINE_LEN, LINE_X = 8.4, -1.2

    def lattice(self, n):
        """The raw-unit grid with its tick numbers and its name: built fresh for each beat that uses it."""
        line = GridLine(GRID, length=self.LINE_LEN, tick_size=0.16).move_to([self.LINE_X, self.Y_LINE, 0])
        ticks = VGroup(*[digits(str(k), SIZE_BODY, Palette.FAINT).next_to(line.n2p(k), DOWN, buff=0.28) for k in n["grid_ticks"]])
        name = words("raw units", SIZE_BODY, Palette.MUTED).next_to(line.get_end(), RIGHT, buff=0.45)
        return line, ticks, name

    def product_row(self, n):
        product = digits(n["charge0"], SIZE_HERO, Palette.EXACT)
        stated = words(n["charge0_label"], SIZE_BODY, Palette.MUTED)
        row = VGroup(product, stated).arrange(RIGHT, buff=0.35, aligned_edge=DOWN).move_to([0, self.Y_PRODUCT, 0])
        return product, stated, row

    def construct(self):
        n = numbers()
        assert n["repaid"] and n["would_lose"]
        x_exact = float(n["charge0_x"])
        x_floor, x_ceil = int(n["floor0"]), int(n["ceil0"])

        # chrome: the title, on the first frame
        self.section(0)
        self.fix(self.title(n["title"]))
        self.wait(0.3)

        # before: the index supply as one bar; one claim redeems it down to 3 raw units
        supply_lbl = words("index supply", SIZE_BODY, Palette.MUTED).move_to([0, 1.55, 0])
        big = digits(n["supply_before"], SIZE_HERO, Palette.TEXT).next_to(supply_lbl, DOWN, buff=0.35)
        bar = Rectangle(width=9.0, height=0.5, color=HUE, fill_color=HUE, fill_opacity=0.85, stroke_width=0).move_to([0, -0.6, 0])
        self.play(FadeIn(supply_lbl, run_time=0.5), Create(bar, run_time=0.9))
        self.play(AddTextLetterByLetter(big, time_per_char=0.06))
        self.wait(1.2)
        r, gap = 0.16, 0.5
        balls = VGroup(*[Dot(radius=r, color=HUE) for _ in range(int(n["supply"]))]).arrange(RIGHT, buff=gap - 2 * r).move_to([0, -0.6, 0])
        tank = RoundedRectangle(width=balls.width + 1.0, height=1.0, corner_radius=0.25, color=HUE, stroke_width=3).move_to(balls)
        three = VGroup(digits(n["supply"], SIZE_HERO, Palette.TEXT), words("raw units", SIZE_BODY, Palette.MUTED)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
        three.move_to(big)
        sliver = Rectangle(width=0.02, height=0.5, color=HUE, fill_color=HUE, fill_opacity=0.85, stroke_width=0).move_to(bar.get_left() + RIGHT * 0.01)
        self.play(Transform(bar, sliver, run_time=1.4, rate_func=ease_in_out_cubic), Transform(big, three, run_time=1.4))
        self.remove(bar)
        self.play(Create(tank, run_time=0.6), LaggedStart(*[FadeIn(b, scale=0.4) for b in balls], lag_ratio=0.3, run_time=0.9))
        self.wait(1.0)

        # step: a mint's charge, stored × amount / supply; the first types in as 1 × 2 / 3 and lands at two thirds
        self.section(1, hold=2.0)
        line, ticks, axis = self.lattice(n)
        formula = words("stored × amount / supply", SIZE_BODY, Palette.MUTED).move_to([0, self.Y_OPERANDS, 0])
        self.play(FadeOut(VGroup(supply_lbl, big, tank, balls), run_time=0.6), FadeIn(formula, shift=DOWN * 0.1, run_time=0.6))
        self.play(Create(line, run_time=1.0), FadeIn(ticks, run_time=0.8), FadeIn(axis, run_time=0.8))
        self.wait(0.8)
        operands = digits(f"{n['stored']} × {n['amount0']} / {n['supply']}", SIZE_BODY, Palette.TEXT).move_to([0, self.Y_OPERANDS, 0])
        self.play(Transform(formula, operands, run_time=0.9))
        self.wait(0.6)
        dot = line.dot_at(0, Palette.EXACT)
        self.play(FadeIn(dot, scale=0.5, run_time=0.3))
        product, stated, _ = self.product_row(n)
        self.play(AddTextLetterByLetter(product, time_per_char=0.1), dot.animate(rate_func=ease_out_cubic, run_time=1.2).move_to(line.n2p(x_exact)))
        self.play(FadeIn(stated, run_time=0.4))
        self.wait(1.2)

        # round: a transfer moves whole raw units, and the floor takes two thirds to 0
        self.section(2, hold=2.0)
        self.play(FadeOut(formula, run_time=0.5))
        arrow = direction(line, x_exact, x_floor, Palette.WRONG, lift=0.38)
        floor_lbl = words("floor", SIZE_BODY, Palette.WRONG).next_to(arrow, UP, buff=0.15)
        kept = dot.copy()
        self.add(kept)
        self.play(Create(arrow, run_time=0.6), FadeIn(floor_lbl, run_time=0.5))
        self.play(snap(kept, line, x_floor, Palette.WRONG, run_time=1.2))
        self.wait(0.8)
        charged = words(f"charged {n['floor0']}", SIZE_BODY, Palette.WRONG)
        cross = cross_mark(Palette.WRONG)
        charged_row = VGroup(cross, charged).arrange(RIGHT, buff=0.3).move_to([0, -2.35, 0])
        self.play(Create(cross, run_time=0.4), FadeIn(charged, shift=UP * 0.1, run_time=0.6))

        # repeat: 37 mints in the one transaction, the amounts doubling (the dots grow), every charge 0
        self.section(3, hold=2.0)
        cols, pitch = 10, 0.62
        top = max(n["amount_bits"])
        reps = VGroup()
        for k, bits in enumerate(n["amount_bits"]):
            row, col = divmod(k, cols)
            reps.add(Dot([(col - (cols - 1) / 2) * pitch, 2.0 - row * pitch, 0], radius=0.05 + 0.15 * bits / top, color=Palette.WRONG))
        self.play(FadeOut(VGroup(line, ticks, axis, dot, arrow, floor_lbl, product, stated, charged_row), run_time=0.6), kept.animate(run_time=0.9).move_to(reps[0]).scale(reps[0].width / kept.width))
        self.remove(kept)
        self.add(reps[0])
        widest = digits(f"× {n['n_mints']}", SIZE_COUNT, HUE)  # the row is laid out for the last count; each count keeps its right edge
        tail = words("mints in one transaction", SIZE_BODY, Palette.MUTED)
        VGroup(widest, tail).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).move_to([0, -1.9, 0])
        counter = digits(f"× {n['counter_ticks'][0]}", SIZE_COUNT, HUE).move_to(widest, aligned_edge=RIGHT)
        count_row = VGroup(counter, tail)
        self.play(FadeIn(counter, run_time=0.4), FadeIn(tail, run_time=0.4))
        for k in n["counter_ticks"][1:]:
            nxt = digits(f"× {k}", SIZE_COUNT, HUE).move_to(widest, aligned_edge=RIGHT)
            self.play(Transform(counter, nxt), FadeIn(reps[k - 1], scale=1.6), run_time=0.11)
        self.wait(0.3)

        # take: what the floor was worth, alone
        self.section(4, hold=2.0)
        loss = words(n["loss"], SIZE_TAKE, HUE).move_to([0, 0.1, 0])
        self.play(FadeOut(count_row, run_time=0.5), reps.animate(run_time=0.9, rate_func=ease_in_out_cubic).scale(0.05).move_to(loss))
        self.remove(reps)
        self.play(FadeIn(loss, scale=0.6, run_time=0.7))
        self.wait(1.0)

        # exact: the same two thirds, rounded up: BL127 / BL19's ceil charges 1 raw unit, and the attack would lose
        self.section(5, hold=2.5)
        line, ticks, axis = self.lattice(n)
        product, stated, row = self.product_row(n)
        self.play(FadeOut(loss, run_time=0.5), Create(line, run_time=0.9), FadeIn(ticks, run_time=0.7), FadeIn(axis, run_time=0.7))
        mark = line.dot_at(x_exact, Palette.EXACT)
        self.play(FadeIn(mark, scale=0.5, run_time=0.4), FadeIn(row, run_time=0.6))
        self.wait(0.4)
        up = direction(line, x_exact, x_ceil, Palette.CORRECT, lift=0.38)
        self.play(Create(up, run_time=0.6))
        self.play(snap(mark, line, x_ceil, Palette.CORRECT, run_time=1.2))
        glow = halo(line.n2p(x_ceil), Palette.CORRECT)
        self.play(FadeIn(glow, run_time=0.6))
        self.bring_to_front(mark)
        verdict = words(f"BL127 / BL19: ceil to {n['ceil0']} raw unit · the attack would lose", SIZE_BODY, Palette.CORRECT)
        tick = check_mark(Palette.CORRECT)
        verdict_row = VGroup(verdict, tick).arrange(RIGHT, buff=0.35).move_to([0, -2.35, 0])
        panel = glow_bar(verdict_row, Palette.CORRECT, pad=0.18)
        self.play(FadeIn(panel, run_time=0.5), FadeIn(verdict, shift=UP * 0.1, run_time=0.7))
        self.play(Create(tick, run_time=0.5))
        self.close()

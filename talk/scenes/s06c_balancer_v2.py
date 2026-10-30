"""Slide 6c, "Balancer V2, 3 Nov 2025": one floor, fifty-five times.

The edit pass's replay shape (talk/briefs/edit-pass.md, row 8): one idea per
section, each section owns the frame, the poster holds the conclusion.

The attack transaction's own integers (scripts/replays/balancer.json,
through vocab.balancer()): the osETH/WETH pool, drained, holds 18 osETH-wei
and the swap asks 17 out. BasePool's _upscale multiplies the amount by the
token's rate with mulDown: 17 × 1.058132408689971699 = 17.988250947729518883
(exact, to 18 decimals), and the floor keeps 17. The pool charged 34.65%
under the exact charge for that swap (625,492 against 957,169 WETH-wei,
computed, not drawn). The cycle repeats 30 times in the osETH pool and 25 in
the wstETH pool, 55 in the one transaction. The loss line is incidents.json's.
The counterfactual is the replay's own table (docs/benchmarks/replay-
balancer.md, through vocab.replay_table, cross-checked against the JSON):
BL127 and BL19 carry the product exact and round the charge up to wei once;
the attacker's plan would lose 127.677 ETH. On the grid the exact product
therefore stays where it is (emerald, halo): rounding it up to 18 would be
mulUp, a different row of the table.

Six sections, one per click: before, step, round, repeat, take, exact.
Provenance (tx, block, the Solidity lines) is in the slide's notes.

Every digit on screen is a value of numbers() (read from the JSON and
computed with Fraction and Decimal) or a LITERALS entry (the title, C3).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    Brace,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    LaggedStart,
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
    balancer,
    check_mark,
    cross_mark,
    digits,
    direction,
    glow_bar,
    halo,
    incidents,
    replay_table,
    snap,
    thousands,
    words,
)

PROTOCOL = "Balancer V2"  # incidents.json's name; its hue in the deck is VIOLET
HUE = Palette.VIOLET
WAD = 18  # Balancer's FixedPoint grid, 10^-18: the rate and the upscaled amount are 18-decimal
PCT_DECIMALS = 2  # the undercharge as drawn (C3: 34.65%)
POOL = "osETH"  # the pool the step is drawn from
OTHER = "wstETH"  # the second pool: its cycles are in the count
MICRO_INDEX = 1  # the first cycle's micro swap is the second call of the replayed phase
GRID = (16, 19, 1)  # osETH-wei around the product
SIZE_TAKE = 72  # the loss, alone on its frame (edit-pass: a lone hero number at 64–72)
SIZE_COUNT = 64  # the repetition counter


def _frac_dec(q: Fraction, places: int) -> str:
    """A Fraction to `places` decimals, half-up, thousands separators (integer arithmetic)."""
    scaled = (2 * q.numerator * 10**places + q.denominator) // (2 * q.denominator)
    whole, frac = divmod(scaled, 10**places)
    return f"{thousands(whole)}.{frac:0{places}d}" if places else thousands(whole)


def _dec(s: str | int, places: int) -> str:
    """A decimal string rounded half-up at `places` decimals, thousands separators."""
    with localcontext() as ctx:
        ctx.prec = 80
        return f"{Decimal(str(s)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP):,}"


def numbers() -> dict:
    d = balancer()
    pool, score, test = d["pools"][POOL], d["score"][POOL], d["test"][POOL]
    other_score = d["score"][OTHER]
    sym = pool["symbols"]
    rk, wk = sym.index(POOL), sym.index("WETH")
    rate = int(score["rate"])
    assert rate == int(pool["rateCacheUpdatedInTx"]["providerRate"]) == int(pool["scalingFactorsInTx"][rk]), rate
    steps = score["steps"]
    micro = steps[MICRO_INDEX]
    assert micro["what"] == "micro" and micro["tokenOut"] == POOL and micro["tokenIn"] == "WETH", micro
    raw = pool["swaps"][micro["k"]]  # the Vault's own onSwap call, from the trace
    assert raw["j"] == rk and raw["i"] == wk and int(raw["amount"]) == int(micro["out"]), raw
    held = int(raw["balances"][rk])  # the pool's osETH before the swap, in wei
    assert [int(raw["balances"][wk]), held] == [int(b) for b in micro["balancesBefore"]], micro["balancesBefore"]
    out = int(micro["out"])
    product = Fraction(out * rate, 10**WAD)
    floor = (out * rate) // 10**WAD
    assert floor == int(micro["upscaledOutDeployed"]) and product != floor, floor
    charged = int(raw["amountIn"])
    exact = int(micro["models"]["exact"]["in"])
    assert charged == int(micro["models"]["deployed"]["in"]) == int(test["amountIn"][MICRO_INDEX]), charged
    assert exact == int(test["expectExact"][MICRO_INDEX]) == int(micro["models"]["bl127"]["in"]) == int(micro["models"]["bl19"]["in"]), exact
    under = Fraction(exact - charged, exact)
    cycles = score["kinds"]["micro"]
    assert cycles == sum(1 for s in steps if s["what"] == "micro") and all(int(s["out"]) == out for s in steps if s["what"] == "micro"), cycles
    other_cycles = other_score["kinds"]["micro"]
    assert int(score["leave"]) == out + 1 == held
    models = score["models"]
    fp = models["bl127"]
    assert fp == models["bl19"] and fp["stepsUnderExact"] == 0 and fp["amountIn"] == models["exact"]["amountIn"], fp
    would_lose = -Decimal(fp["projectedExtractionEth"])
    assert would_lose > 0
    inc = next(i for i in incidents()["incidents"] if i["protocol"] == PROTOCOL)
    assert d["provenance"]["timestamp"].startswith("2025-11-03") and inc["date"] == "3 Nov 2025", inc["date"]
    # the generated table says the same (docs/benchmarks/replay-balancer.md, through replay_table)
    rulers = {r["model"]: r for r in replay_table("balancer", "The same calls on five rulers")}
    bl127_row = next(r for m, r in rulers.items() if m.startswith("BL127") or m.startswith("FP127"))
    bl19_row = next(r for m, r in rulers.items() if m.startswith("BL19") or m.startswith("FP19"))
    assert int(bl127_row["calls below exact"]) == int(bl19_row["calls below exact"]) == 0
    assert Decimal(bl127_row["projected take (ETH)"]) == Decimal(bl19_row["projected take (ETH)"]) == -would_lose, bl127_row
    happened = replay_table("balancer", "What happened")
    assert f"{cycles} cycles" in happened[0]["phase replayed"] and f"{other_cycles} cycles" in happened[1]["phase replayed"], happened
    assert happened[0]["rate token, in-tx rate"] == f"{POOL} {_frac_dec(Fraction(rate, 10**WAD), WAD)}", happened[0]
    return {
        "title": f"{inc['protocol']}, {inc['date']}",
        "pool": f"{POOL}/WETH",
        "held": held,
        "out": out,
        "rate": _frac_dec(Fraction(rate, 10**WAD), WAD),
        "product": _frac_dec(product, WAD),
        "product_label": f"(to {WAD} decimals)",
        "grid_ticks": list(range(GRID[0], GRID[1] + 1)),
        "floor": floor,
        "under_pct": _frac_dec(under * 100, PCT_DECIMALS) + "%",
        "repeats": cycles + other_cycles,
        "counter_ticks": list(range(1, cycles + other_cycles + 1)),
        "loss": inc["loss"],
        "would_lose": _dec(would_lose, 3),
    }


_INCIDENT = next(i for i in incidents()["incidents"] if i["protocol"] == PROTOCOL)
LITERALS = {f"{PROTOCOL}, {_INCIDENT['date']}": "C3"}  # the title: the protocol's name carries a digit, and the date (C3)


class BalancerV2(DeckScene):
    SECTIONS = ("before", "step", "round", "repeat", "take", "exact")

    Y_OPERANDS, Y_PRODUCT, Y_LINE = 2.05, 1.15, -0.45
    LINE_LEN, LINE_X = 8.4, -1.2

    def lattice(self, n):
        """The osETH-wei grid with its tick numbers and its name: built fresh for each beat that uses it."""
        line = GridLine(GRID, length=self.LINE_LEN, tick_size=0.16).move_to([self.LINE_X, self.Y_LINE, 0])
        ticks = VGroup(*[digits(str(k), SIZE_BODY, Palette.FAINT).next_to(line.n2p(k), DOWN, buff=0.28) for k in n["grid_ticks"]])
        name = words("osETH, in wei", SIZE_BODY, Palette.MUTED).next_to(line.get_end(), RIGHT, buff=0.45)
        return line, ticks, name

    def product_row(self, n):
        product = digits(n["product"], SIZE_HERO, Palette.EXACT)
        stated = words(n["product_label"], SIZE_BODY, Palette.MUTED)
        row = VGroup(product, stated).arrange(RIGHT, buff=0.35, aligned_edge=DOWN).move_to([0, self.Y_PRODUCT, 0])
        return product, stated, row

    def construct(self):
        n = numbers()
        assert n["title"] in LITERALS
        x_exact = float(Fraction(n["product"].replace(",", "")))
        x_floor, out, held = n["floor"], n["out"], n["held"]

        # chrome: the title, on the first frame
        self.section(0)
        self.fix(self.title(n["title"]))
        self.wait(0.3)

        # before: the pool, drawn; its osETH as balls, one per wei; the swap asks for all but one
        r, gap = 0.14, 0.42
        balls = VGroup(*[Dot(radius=r, color=HUE) for _ in range(held)]).arrange(RIGHT, buff=gap - 2 * r).move_to([0, -0.15, 0])
        tank = RoundedRectangle(width=balls.width + 1.0, height=1.1, corner_radius=0.25, color=HUE, stroke_width=3).move_to(balls)
        pool_lbl = words(f"{n['pool']} pool", SIZE_BODY, HUE).next_to(tank, DOWN, buff=0.3)
        held_lbl = VGroup(digits(str(held), SIZE_HERO, Palette.TEXT), words("osETH-wei", SIZE_BODY, Palette.MUTED)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
        held_lbl.next_to(pool_lbl, DOWN, buff=0.3)
        self.play(Create(tank, run_time=0.8), FadeIn(pool_lbl, run_time=0.6))
        self.play(LaggedStart(*[FadeIn(b, scale=0.4) for b in balls], lag_ratio=0.12, run_time=1.8))
        self.play(FadeIn(held_lbl, shift=UP * 0.1, run_time=0.6))
        self.wait(1.0)
        taken = balls[held - out :]
        brace = Brace(taken, UP, buff=0.12, color=Palette.TEXT)
        ask = VGroup(digits(str(out), SIZE_HERO, Palette.TEXT), words("out", SIZE_BODY, Palette.MUTED)).arrange(RIGHT, buff=0.2, aligned_edge=DOWN)
        self.play(taken.animate.set_color(Palette.TEXT).shift(UP * 1.25), run_time=0.9)
        brace.next_to(taken, UP, buff=0.1)
        ask.next_to(brace, UP, buff=0.12)
        self.play(Create(brace, run_time=0.5), FadeIn(ask, shift=DOWN * 0.1, run_time=0.5))
        self.wait(1.2)

        # step: the 17 wei become one value on the osETH-wei grid; × the rate carries it to 17.988…
        self.section(1, hold=2.0)
        line, ticks, axis = self.lattice(n)
        dot = line.dot_at(out, Palette.EXACT)
        self.play(FadeOut(VGroup(tank, balls[: held - out], pool_lbl, held_lbl, brace, ask), run_time=0.6), Create(line, run_time=1.0), FadeIn(ticks, run_time=0.8), FadeIn(axis, run_time=0.8))
        self.play(*[Transform(b, dot.copy()) for b in taken], run_time=1.0, rate_func=ease_in_out_cubic)
        self.remove(*taken)
        self.add(dot)
        self.wait(0.4)
        operands = digits(f"{out} × {n['rate']}", SIZE_BODY, Palette.TEXT).move_to([0, self.Y_OPERANDS, 0])
        self.play(AddTextLetterByLetter(operands, time_per_char=0.07))
        self.wait(0.6)
        product, stated, _ = self.product_row(n)
        self.play(AddTextLetterByLetter(product, time_per_char=0.07), dot.animate(rate_func=ease_out_cubic, run_time=1.6).move_to(line.n2p(x_exact)))
        self.play(FadeIn(stated, run_time=0.4))
        self.wait(1.2)

        # round: the floor drags it a whole wei down
        self.section(2, hold=2.0)
        self.play(FadeOut(operands, run_time=0.5))
        arrow = direction(line, x_exact, x_floor, Palette.WRONG, lift=0.38)
        floor_lbl = words("floor", SIZE_BODY, Palette.WRONG).next_to(arrow, UP, buff=0.15)
        kept = dot.copy()
        self.add(kept)
        self.play(Create(arrow, run_time=0.6), FadeIn(floor_lbl, run_time=0.5))
        self.play(snap(kept, line, x_floor, Palette.WRONG, run_time=1.2))
        self.wait(0.8)
        under = words(f"charged {n['under_pct']} under", SIZE_BODY, Palette.WRONG)
        cross = cross_mark(Palette.WRONG)
        under_row = VGroup(cross, under).arrange(RIGHT, buff=0.3).move_to([0, -2.35, 0])
        self.play(Create(cross, run_time=0.4), FadeIn(under, shift=UP * 0.1, run_time=0.6))

        # repeat: the floored swap, over and over, in one transaction
        self.section(3, hold=2.0)
        cols = 11
        rows = -(-n["repeats"] // cols)
        reps = VGroup(*[Dot(radius=0.13, color=Palette.WRONG) for _ in range(n["repeats"])]).arrange_in_grid(rows=rows, cols=cols, buff=0.36).move_to([0, 0.85, 0])
        self.play(FadeOut(VGroup(line, ticks, axis, dot, arrow, floor_lbl, product, stated, under_row), run_time=0.6), kept.animate(run_time=0.9).move_to(reps[0]))
        self.remove(kept)
        self.add(reps[0])
        widest = digits(f"× {n['repeats']}", SIZE_COUNT, HUE)  # the row is laid out for the last count; each count keeps its right edge
        tail = words("in one transaction", SIZE_BODY, Palette.MUTED)
        VGroup(widest, tail).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).move_to([0, -2.0, 0])
        counter = digits(f"× {n['counter_ticks'][0]}", SIZE_COUNT, HUE).move_to(widest, aligned_edge=RIGHT)
        count_row = VGroup(counter, tail)
        self.play(FadeIn(counter, run_time=0.4), FadeIn(tail, run_time=0.4))
        for k in n["counter_ticks"][1:]:
            nxt = digits(f"× {k}", SIZE_COUNT, HUE).move_to(widest, aligned_edge=RIGHT)
            self.play(Transform(counter, nxt), FadeIn(reps[k - 1], scale=1.6), run_time=0.085)
        self.wait(0.3)

        # take: what the floor was worth, alone
        self.section(4, hold=2.0)
        loss = words(n["loss"], SIZE_TAKE, HUE).move_to([0, 0.1, 0])
        self.play(FadeOut(count_row, run_time=0.5), reps.animate(run_time=0.9, rate_func=ease_in_out_cubic).scale(0.05).move_to(loss))
        self.remove(reps)
        self.play(FadeIn(loss, scale=0.6, run_time=0.7))
        self.wait(1.0)

        # exact: the same step in BL127 / BL19: the product kept exact, the charge rounded up once
        self.section(5, hold=2.5)
        line, ticks, axis = self.lattice(n)
        product, stated, row = self.product_row(n)
        self.play(FadeOut(loss, run_time=0.5), Create(line, run_time=0.9), FadeIn(ticks, run_time=0.7), FadeIn(axis, run_time=0.7))
        low = line.dot_at(x_floor, Palette.WRONG)
        self.play(FadeIn(low, scale=0.5, run_time=0.4), FadeIn(row, run_time=0.6))
        self.wait(0.4)
        glow = halo(line.n2p(x_exact), Palette.CORRECT)
        self.play(low.animate(rate_func=ease_out_cubic, run_time=1.2).move_to(line.n2p(x_exact)).set_color(Palette.CORRECT))
        self.play(FadeIn(glow, run_time=0.6))
        self.bring_to_front(low)
        verdict = words(f"BL127 / BL19: ceil once · the attacker would lose {n['would_lose']} ETH", SIZE_BODY, Palette.CORRECT)
        tick = check_mark(Palette.CORRECT)
        verdict_row = VGroup(verdict, tick).arrange(RIGHT, buff=0.35).move_to([0, -2.35, 0])
        panel = glow_bar(verdict_row, Palette.CORRECT, pad=0.18)
        self.play(FadeIn(panel, run_time=0.5), FadeIn(verdict, shift=UP * 0.1, run_time=0.7))
        self.play(Create(tick, run_time=0.5))
        self.close()

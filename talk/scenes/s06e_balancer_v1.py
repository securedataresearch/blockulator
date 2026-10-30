"""Slide 6e, "Balancer V1, 31 Aug 2026": one round-to-nearest, 438 times.

The edit pass's replay shape (talk/briefs/edit-pass.md, row 10; the model is
s06c): one idea per section, each section owns the frame, the poster holds
the conclusion.

Pool 1 of the five (scripts/replays/balancer_v1.json, tx order): the swaps
push its WBTC down to 3 satoshi. Each join computes BMath.sol's
newTokenBalanceIn = bmul(tokenInRatio, balance); BNum's ratio at the first
join at balance 3 is 1.499999999999999997 (the deployed integer), × 3 =
4.499999999999999991 (exact, to 18 decimals), 9 × 10^-18 satoshi under the
half-way mark, and bmul's half-up nearest takes it to 4 (WRONG, red): the
join costs 1 satoshi for 1.5056462 satoshi's worth (pool 1's exact cost, by
Fraction, to 7 decimals). 438 joins across the five pools. The take is
incidents.json's $1.39M. Last, the same join rounded toward the pool: 5,
the cost 2 against the attacker's own maxAmountIn = 1, so every join would
revert; BL127 and BL19 with one ceil to the unit give 2 on all 438 (the
generated table, docs/benchmarks/replay-balancer-v1.md, cross-checked
against the exact ceil by Fraction).

Six sections, one per click: before, step, round, repeat, take, exact.
Provenance (tx, block, the Solidity lines) is in the slide's notes.

Every digit on screen is a value of numbers() (read from the JSON through
balancer_v1_replay() and replay_table(), computed with Fraction);
check.py recomputes by Decimal.
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
    _load,
    balancer_v1_replay,
    check_mark,
    cross_mark,
    digits,
    direction,
    glow_bar,
    halo,
    incidents,
    markup,
    measure,
    midpoint,
    replay_table,
    snap,
    to_decimals,
    words,
)

PROTOCOL = "Balancer V1"  # incidents.json's name; its hue in the deck is SAPPHIRE
HUE = Palette.SAPPHIRE
POOL = 0  # the pool the step is drawn from (tx order): pool 1
WAD = 18  # BNum's grid, 10^-18: the ratio and the product are 18-decimal
COST_DECIMALS = 7  # pool 1's exact cost per join, as drawn
GRID = (3, 6, 1)  # satoshi around the new balance
EPS = 0.06  # the dot's visual offset left of the half (not to scale: the real gap is 9 × 10^-18)
COUNT_STEP = 6  # the counter's stride after the first join
TABLE_HEADING = "Every join and exit"
SIZE_TAKE = 72  # the loss, alone on its frame (edit-pass: a lone hero number at 64–72)
SIZE_COUNT = 64  # the repetition counter

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def _exact_cost(row: dict) -> Fraction:
    """The stated formula (BMath.sol's comment above calcSingleInGivenPoolOut)
    for a join, exact: balance × ((1 + P/S)^(tW/w) − 1) / (1 − f),
    f = (1 − w/tW) × fee. tW/w is a whole number in every attacked pool."""
    tw, w = row["totalWeight"], row["weight"]
    assert tw % w == 0, (tw, w)
    f = Fraction(tw - w, tw) * Fraction(row["fee"], 10**WAD)
    return row["balance"] * ((1 + Fraction(row["poolAmount"], row["supply"])) ** (tw // w) - 1) / (1 - f)


def numbers() -> dict:
    d = _load("scripts/replays/balancer_v1.json")
    pool = d["pools"][POOL]
    inc = next(i for i in incidents()["incidents"] if i["protocol"] == PROTOCOL)
    assert pool["time"].startswith("2026-08-31") and inc["date"] == "31 Aug 2026", (pool["time"], inc["date"])
    replay = balancer_v1_replay()
    joins = [r for r in replay[POOL] if r["kind"] == 2]
    all_joins = [r for p in replay for r in p if r["kind"] == 2]
    first = next(r for r in joins if r["balance"] == 3)
    ratio = first["steps"]["tokenInRatio"]
    product = Fraction(first["balance"] * ratio, 10**WAD)
    nearest = (first["balance"] * ratio + 10**WAD // 2) // 10**WAD  # bmul, BNum.sol: half up
    toward = -((-first["balance"] * ratio) // 10**WAD)  # ceil, toward the pool
    assert nearest == first["steps"]["newTokenBalanceIn"] == 4 and toward == 5 and product < Fraction(9, 2), (nearest, toward)
    charged = nearest - first["balance"]  # the new balance less the old: what the join paid in
    assert charged == first["deployed"] == 1 == first["limit"], (charged, first["deployed"], first["limit"])
    tokens = pool["state"]["tokens"]
    assert tokens[first["token"]]["symbol"] == "WBTC" and all(r["token"] == first["token"] for r in joins)
    cost = _exact_cost(first)
    costs = [_exact_cost(r) for r in all_joins]
    assert all(Fraction(3, 2) < c < 2 for c in costs) and {-((-c.numerator) // c.denominator) for c in costs} == {2}
    # the generated table says the same: BL127 and BL19 give 2 on every join, past the attacker's limit of 1
    table = [r for r in replay_table("balancer-v1", TABLE_HEADING) if r["call"].startswith("join")]
    assert [int(r["n"]) for r in table] == [sum(1 for r in p if r["kind"] == 2) for p in replay], table
    assert all(r["BL127"] == r["BL19"] == r["exact, rounded"] == "2" and r["deployed"] == "1" and r["pays?"] == "no" for r in table), table
    n_joins = len(all_joins)
    return {
        "title": f"{inc['protocol']}, {inc['date']}",
        "balance": first["balance"],
        "ratio": to_decimals(Fraction(ratio, 10**WAD), WAD),
        "product": to_decimals(product, WAD),
        "product_label": f"(to {WAD} decimals)",
        "grid_ticks": list(range(GRID[0], GRID[1] + 1)),
        "nearest": nearest,
        "toward": toward,
        "charged": charged,
        "cost": to_decimals(cost, COST_DECIMALS),
        "cost_label": f"(to {COST_DECIMALS} decimals)",
        "joins": n_joins,
        "counter_ticks": [1, *range(COUNT_STEP, n_joins, COUNT_STEP), n_joins],
        "loss": inc["loss"],
    }


class BalancerV1(DeckScene):
    SECTIONS = ("before", "step", "round", "repeat", "take", "exact")

    Y_OPERANDS, Y_PRODUCT, Y_LINE, Y_VERDICT = 2.05, 1.15, -0.45, -2.45
    LINE_LEN, LINE_X = 8.0, -1.6

    def lattice(self, n):
        """The satoshi grid with its tick numbers, its half-way mark and its name: built fresh for each beat that uses it."""
        line = GridLine(GRID, length=self.LINE_LEN, tick_size=0.16).move_to([self.LINE_X, self.Y_LINE, 0])
        ticks = VGroup(*[digits(str(k), SIZE_BODY, Palette.FAINT).next_to(line.n2p(k), DOWN, buff=0.28) for k in n["grid_ticks"]])
        name = words("WBTC, in satoshi", SIZE_BODY, Palette.MUTED).next_to(line.get_end(), RIGHT, buff=0.45)
        mid = midpoint(line, n["nearest"], n["toward"], height=0.7)
        return line, ticks, name, mid

    def product_row(self, n):
        product = digits(n["product"], SIZE_HERO, Palette.EXACT)
        stated = words(n["product_label"], SIZE_BODY, Palette.MUTED)
        row = VGroup(product, stated).arrange(RIGHT, buff=0.35, aligned_edge=DOWN).move_to([0, self.Y_PRODUCT, 0])
        return product, stated, row

    def construct(self):
        n = numbers()
        b = n["balance"]
        x_half = float(Fraction(n["nearest"] + n["toward"], 2))  # the half-way mark (the product is 9 × 10^-18 under it: one float)
        x_dot = x_half - EPS

        # chrome: the title, on the first frame
        self.section(0)
        self.fix(self.title(n["title"]))
        self.wait(0.3)

        # before: the pool's WBTC, pushed down by swaps to a few satoshi, drawn one ball per satoshi
        r, gap = 0.26, 0.9
        balls = VGroup(*[Dot(radius=r, color=HUE) for _ in range(b)]).arrange(RIGHT, buff=gap - 2 * r).move_to([0, 0.35, 0])
        tank = RoundedRectangle(width=balls.width + 1.2, height=1.4, corner_radius=0.3, color=HUE, stroke_width=3).move_to(balls)
        pool_lbl = words("WBTC in the pool", SIZE_BODY, HUE).next_to(tank, DOWN, buff=0.3)
        held_lbl = VGroup(digits(str(b), SIZE_HERO, Palette.TEXT), words("satoshi", SIZE_BODY, Palette.MUTED)).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
        held_lbl.next_to(pool_lbl, DOWN, buff=0.3)
        self.play(Create(tank, run_time=0.8), FadeIn(pool_lbl, run_time=0.6))
        self.play(LaggedStart(*[FadeIn(ball, scale=0.4) for ball in balls], lag_ratio=0.3, run_time=1.2))
        self.play(FadeIn(held_lbl, shift=UP * 0.1, run_time=0.6))
        self.wait(1.2)

        # step: the balance becomes one value on the satoshi grid; × the ratio carries it just under the half
        self.section(1, hold=2.0)
        line, ticks, axis, mid = self.lattice(n)
        dot = line.dot_at(b, Palette.EXACT)
        self.play(FadeOut(VGroup(tank, pool_lbl, held_lbl), run_time=0.6), Create(line, run_time=1.0), FadeIn(ticks, run_time=0.8), FadeIn(axis, run_time=0.8))
        self.play(*[Transform(ball, dot.copy()) for ball in balls], run_time=1.0, rate_func=ease_in_out_cubic)
        self.remove(*balls)
        self.add(dot)
        self.wait(0.4)
        operands = digits(f"{n['ratio']} × {b}", SIZE_BODY, Palette.TEXT).move_to([0, self.Y_OPERANDS, 0])
        self.play(AddTextLetterByLetter(operands, time_per_char=0.07))
        self.wait(0.6)
        product, stated, _ = self.product_row(n)
        self.play(AddTextLetterByLetter(product, time_per_char=0.07), dot.animate(rate_func=ease_out_cubic, run_time=1.6).move_to(line.n2p(x_dot)))
        self.play(FadeIn(stated, run_time=0.4))
        self.wait(1.2)

        # round: the half-way mark, half a unit from 4; nearest takes it down to 4
        self.section(2, hold=2.0)
        half = measure(line, n["nearest"], x_half, "half a unit", drop=0.95, colour=Palette.MUTED)
        self.play(FadeOut(operands, run_time=0.5), Create(mid, run_time=0.6))
        self.play(Create(half[0], run_time=0.5), Create(half[1], run_time=0.5), FadeIn(half[2], run_time=0.4))
        self.wait(0.6)
        arrow = direction(line, x_dot, n["nearest"], Palette.WRONG, lift=0.38)
        nearest_lbl = words("nearest", SIZE_BODY, Palette.WRONG).next_to(arrow, UP, buff=0.15)
        kept = dot.copy()
        self.add(kept)
        self.play(Create(arrow, run_time=0.6), FadeIn(nearest_lbl, run_time=0.5))
        self.play(snap(kept, line, n["nearest"], Palette.WRONG, run_time=1.2))
        self.wait(0.8)
        cost_line = markup(
            f"the join costs {n['charged']} satoshi for {n['cost']} <span foreground='{Palette.MUTED}'>{n['cost_label']}</span>",
            SIZE_BODY,
            Palette.WRONG,
        )
        cross = cross_mark(Palette.WRONG)
        VGroup(cross, cost_line).arrange(RIGHT, buff=0.3).move_to([0, self.Y_VERDICT, 0])
        self.play(Create(cross, run_time=0.4), FadeIn(cost_line, shift=UP * 0.1, run_time=0.6))

        # repeat: the rounded join, over and over
        self.section(3, hold=2.0)
        cols = 34
        rows = -(-n["joins"] // cols)
        reps = VGroup(*[Dot(radius=0.075, color=Palette.WRONG) for _ in range(n["joins"])]).arrange_in_grid(rows=rows, cols=cols, buff=0.15).move_to([0, 0.6, 0])
        self.play(
            FadeOut(VGroup(line, ticks, axis, mid, half, dot, arrow, nearest_lbl, product, stated, cross, cost_line), run_time=0.6),
            kept.animate(run_time=0.9).scale(0.075 / 0.11).move_to(reps[0]),
        )
        self.remove(kept)
        self.add(reps[0])
        widest = digits(f"× {n['joins']}", SIZE_COUNT, HUE)  # the row is laid out for the last count; each count keeps its right edge
        tail = words("joins", SIZE_BODY, Palette.MUTED)
        VGroup(widest, tail).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).move_to([0, -2.2, 0])
        ticks_ = n["counter_ticks"]
        counter = digits(f"× {ticks_[0]}", SIZE_COUNT, HUE).move_to(widest, aligned_edge=RIGHT)
        count_row = VGroup(counter, tail)
        self.play(FadeIn(counter, run_time=0.4), FadeIn(tail, run_time=0.4))
        for prev, k in zip(ticks_, ticks_[1:]):
            nxt = digits(f"× {k}", SIZE_COUNT, HUE).move_to(widest, aligned_edge=RIGHT)
            self.play(Transform(counter, nxt), LaggedStart(*[FadeIn(reps[j], scale=1.6) for j in range(prev, k)], lag_ratio=0.2), run_time=0.085)
        self.wait(0.3)

        # take: what the nearest was worth, alone
        self.section(4, hold=2.0)
        loss = words(n["loss"], SIZE_TAKE, HUE).move_to([0, 0.1, 0])
        self.play(FadeOut(count_row, run_time=0.5), reps.animate(run_time=0.9, rate_func=ease_in_out_cubic).scale(0.05).move_to(loss))
        self.remove(reps)
        self.play(FadeIn(loss, scale=0.6, run_time=0.7))
        self.wait(1.0)

        # exact: the same join rounded toward the pool: 5, and the join no longer pays
        self.section(5, hold=2.5)
        line, ticks, axis, mid = self.lattice(n)
        product, stated, row = self.product_row(n)
        self.play(FadeOut(loss, run_time=0.5), Create(line, run_time=0.9), FadeIn(ticks, run_time=0.7), FadeIn(axis, run_time=0.7), FadeIn(mid, run_time=0.7))
        here = line.dot_at(x_dot, Palette.EXACT)
        self.play(FadeIn(here, scale=0.5, run_time=0.4), FadeIn(row, run_time=0.6))
        self.wait(0.4)
        up = direction(line, x_dot, n["toward"], Palette.CORRECT, lift=0.38)
        up_dot = here.copy()
        self.add(up_dot)
        self.play(Create(up, run_time=0.6))
        self.play(snap(up_dot, line, n["toward"], Palette.CORRECT, run_time=1.2))
        glow = halo(line.n2p(n["toward"]), Palette.CORRECT)
        self.play(FadeIn(glow, run_time=0.6))
        self.bring_to_front(up_dot)
        verdict = words(f"BL127 / BL19, toward the pool: {n['toward']} · every join would revert", SIZE_BODY, Palette.CORRECT)
        tick = check_mark(Palette.CORRECT)
        verdict_row = VGroup(verdict, tick).arrange(RIGHT, buff=0.35).move_to([0, self.Y_VERDICT, 0])
        panel = glow_bar(verdict_row, Palette.CORRECT, pad=0.18)
        self.play(FadeIn(panel, run_time=0.5), FadeIn(verdict, shift=UP * 0.1, run_time=0.7))
        self.play(Create(tick, run_time=0.5))
        self.close()

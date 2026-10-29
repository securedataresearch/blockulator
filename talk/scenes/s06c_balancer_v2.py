"""Slide 6c, "Balancer V2, 3 Nov 2025": one mulDown, thirty times.

The attack transaction's own integers (scripts/replays/balancer.json,
through vocab.balancer()): the osETH/WETH pool after the attacker's drain
holds 374,353 WETH-wei and 18 osETH-wei; the swap asks 17 osETH-wei out.
BasePool's _upscale multiplies the amount by the token's rate with mulDown:
17 × 1.058132408689971699 = 17.988250947729518883 (exact, 18 decimals),
and mulDown keeps 17 (mulUp would give 18). On the osETH-wei grid the
exact product sits a hair under 18 and snaps a whole unit down to 17
(WRONG, red). The pool charged 625,492 WETH-wei for that swap; the exact
charge on the same balances, rounded up to wei, is 957,169: 34.65% under.
The cycle (drain, micro, restore) repeats 30 times in the osETH pool and 25
in the wstETH pool while the pool's true invariant D* falls from
137,894.598 to 2,446.080 (×0.017739). The loss line is incidents.json's;
the net to the attacker is the replay's batchSwapNetEth. The counterfactual
is the replay's own table (docs/benchmarks/replay-balancer.md, through
vocab.replay_table, cross-checked against the JSON): FP127 and FP19 inside
with one ceil to wei charge the exact amount on every call, 0 calls below
exact, and the plan would lose the attacker 127.677 ETH.

Six sections, one per click: before, step, round, repeat, take, exact.

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
    Arrow,
    Create,
    FadeIn,
    Rectangle,
    Transform,
    VGroup,
    ValueTracker,
    always_redraw,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    SIZE_BODY,
    SIZE_CAPTION,
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
INVARIANT_DECIMALS = 3  # D* as drawn
RATIO_DECIMALS = 6  # D* end / start as drawn
PCT_DECIMALS = 2  # the undercharge as drawn (C3: 34.65%)
NET_DECIMALS = 2  # the attacker's net in ETH as drawn
POOL = "osETH"  # the pool the step is drawn from; the other is named in the repeat
OTHER = "wstETH"
MICRO_INDEX = 1  # the first cycle's micro swap is the second call of the replayed phase
GRID = (14, 20, 1)  # osETH-wei around the pool's 18
LEFT_X = -6.3
RIGHT_X = 0.5
CITE = SIZE_CAPTION  # the two source citations, drawn at the caption's size (reported)
STATED = SIZE_BODY  # "(to 18 decimals)"


def _dec(s: str | int, places: int) -> str:
    """A decimal string rounded half-up at `places` decimals with thousands
    separators on the integer part."""
    with localcontext() as ctx:
        ctx.prec = 80
        return f"{Decimal(str(s)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP):,}"


def _frac_dec(q: Fraction, places: int) -> str:
    """A Fraction to `places` decimals, half-up, thousands separators (integer arithmetic)."""
    scaled = (2 * q.numerator * 10**places + q.denominator) // (2 * q.denominator)
    whole, frac = divmod(scaled, 10**places)
    return f"{thousands(whole)}.{frac:0{places}d}" if places else thousands(whole)


def to_decimals(places: int) -> str:
    return f"(to {places} decimals)"


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
    weth_before, rate_before = int(raw["balances"][wk]), int(raw["balances"][rk])
    assert [weth_before, rate_before] == [int(b) for b in micro["balancesBefore"]], micro["balancesBefore"]
    out = int(micro["out"])
    product = Fraction(out * rate, 10**WAD)
    mul_down, mul_up = (out * rate) // 10**WAD, -((-out * rate) // 10**WAD)
    assert mul_down == int(micro["upscaledOutDeployed"]) and mul_up == int(micro["upscaledOutMulUp"]), (mul_down, mul_up)
    charged = int(raw["amountIn"])
    exact = int(micro["models"]["exact"]["in"])
    assert charged == int(micro["models"]["deployed"]["in"]) == int(test["amountIn"][MICRO_INDEX]), charged
    assert exact == int(test["expectExact"][MICRO_INDEX]) == int(micro["models"]["fp127"]["in"]) == int(micro["models"]["fp19"]["in"]), exact
    under = Fraction(exact - charged, exact)
    cycles = score["kinds"]["micro"]
    assert cycles == sum(1 for s in steps if s["what"] == "micro") and all(int(s["out"]) == out for s in steps if s["what"] == "micro"), cycles
    other_cycles = other_score["kinds"]["micro"]
    other_leave, other_out = int(other_score["leave"]), int(other_score["steps"][MICRO_INDEX]["out"])
    assert other_score["steps"][MICRO_INDEX]["what"] == "micro" and other_out == other_leave - 1 and int(score["leave"]) == out + 1 == rate_before
    # D* after each cycle: the next drain's invariant before, then the phase's end
    d_start, d_end = Decimal(score["trueInvariantStart"]), Decimal(score["trueInvariantEnd"])
    assert Decimal(steps[0]["trueInvariantBefore"]) == d_start
    after = [Decimal(steps[3 * c]["trueInvariantBefore"]) for c in range(1, cycles)] + [d_end]
    assert len(after) == cycles and steps[3 * (cycles - 1) + 2]["what"] == "restore" and len(steps) == 3 * cycles
    levels = [float(x / d_start) for x in after]  # the bar's fill after each cycle, a fraction of the start (not drawn)
    ratio = Decimal(score["onchainInvariantRatio"])
    models = score["models"]
    fp = models["fp127"]
    assert fp == models["fp19"] and fp["stepsUnderExact"] == 0 and fp["amountIn"] == models["exact"]["amountIn"], fp
    would_lose = -Decimal(fp["projectedExtractionEth"])
    assert would_lose > 0
    inc = next(i for i in incidents()["incidents"] if i["protocol"] == PROTOCOL)
    assert d["provenance"]["timestamp"].startswith("2025-11-03") and inc["date"] == "3 Nov 2025", inc["date"]
    assert "Ethereum mainnet" in d["about"]
    cites = pool["source"]["cites"]
    upscale_cite = cites["BasePool.sol:_upscale"].rsplit("/", 1)[1]
    muldown_cite = cites["FixedPoint.sol:mulDown"].rsplit("/", 1)[1]
    # the generated table says the same (docs/benchmarks/replay-balancer.md, through replay_table)
    rulers = {r["model"]: r for r in replay_table("balancer", "The same calls on five rulers")}
    dep_row = next(r for m, r in rulers.items() if m.startswith("deployed"))
    fp127_row = next(r for m, r in rulers.items() if m.startswith("FP127"))
    fp19_row = next(r for m, r in rulers.items() if m.startswith("FP19"))
    charged_col = "charged in (WETH-wei / rate-token-wei)"
    assert dep_row[charged_col] == f"{thousands(models['deployed']['amountIn']['WETH'])} / {thousands(models['deployed']['amountIn'][POOL])}", dep_row
    assert fp127_row[charged_col] == fp19_row[charged_col] == f"{thousands(fp['amountIn']['WETH'])} / {thousands(fp['amountIn'][POOL])}", fp127_row
    assert int(dep_row["calls below exact"]) == models["deployed"]["stepsUnderExact"] and int(fp127_row["calls below exact"]) == int(fp19_row["calls below exact"]) == 0
    assert Decimal(fp127_row["projected take (ETH)"]) == Decimal(fp19_row["projected take (ETH)"]) == -would_lose, fp127_row
    assert Decimal(dep_row["projected take (ETH)"]) == Decimal(models["deployed"]["projectedExtractionEth"])
    happened = replay_table("balancer", "What happened")
    assert f"{cycles} cycles" in happened[0]["phase replayed"] and f"{other_cycles} cycles" in happened[1]["phase replayed"], happened
    assert happened[0]["rate token, in-tx rate"] == f"{POOL} {_frac_dec(Fraction(rate, 10**WAD), WAD)}", happened[0]
    return {
        "title": f"{inc['protocol']}, {inc['date']}",
        "tx_short": d["provenance"]["tx"][:10],
        "block": thousands(d["provenance"]["block"]),
        "chain": "Ethereum",
        "pool": f"{POOL}/WETH",
        "other_pool": f"{OTHER}/WETH",
        "weth_before": thousands(weth_before),
        "rate_before": thousands(rate_before),
        "out": thousands(out),
        "rate": _frac_dec(Fraction(rate, 10**WAD), WAD),
        "product": _frac_dec(product, WAD),
        "product_label": to_decimals(WAD),
        "grid_ticks": list(range(GRID[0], GRID[1] + 1)),
        "mul_down": thousands(mul_down),
        "mul_up": thousands(mul_up),
        "charged": thousands(charged),
        "exact": thousands(exact),
        "under_pct": _frac_dec(under * 100, PCT_DECIMALS) + "%",
        "cycles": cycles,
        "other_cycles": other_cycles,
        "other_out": thousands(other_out),
        "other_leave": thousands(other_leave),
        "counter_ticks": list(range(1, max(cycles, other_cycles) + 1)),
        "d_start": _dec(d_start, INVARIANT_DECIMALS),
        "d_end": _dec(d_end, INVARIANT_DECIMALS),
        "d_ratio": "×" + _dec(ratio, RATIO_DECIMALS),
        "d_levels": levels,
        "loss": inc["loss"],
        "net_eth": _dec(score["batchSwapNetEth"], NET_DECIMALS),
        "deployed_charged_total": thousands(models["deployed"]["amountIn"]["WETH"]),
        "fp_charged_total": thousands(fp["amountIn"]["WETH"]),
        "deployed_below": models["deployed"]["stepsUnderExact"],
        "fp_below": fp["stepsUnderExact"],
        "would_lose": _dec(would_lose, 3),
        "upscale_cite": upscale_cite,
        "muldown_cite": muldown_cite,
    }


_INCIDENT = next(i for i in incidents()["incidents"] if i["protocol"] == PROTOCOL)
LITERALS = {f"{PROTOCOL}, {_INCIDENT['date']}": "C3"}  # the title: the protocol's name carries a digit, and the date (C3)


class BalancerV2(DeckScene):
    SECTIONS = ("before", "step", "round", "repeat", "take", "exact")

    # the rows, top to bottom (the frame is 8 high; 5% safe area; the caption sits at the bottom-left)
    Y_TITLE, Y_BEFORE, Y_FORMULA, Y_OPERANDS, Y_PRODUCT = 3.4, 2.9, 2.4, 1.9, 1.4
    Y_LINE, Y_TICKS, Y_CHARGE = 0.65, 0.3, -0.15
    Y_R1, Y_R2, Y_BAR, Y_TAKE, Y_E1, Y_E2 = -0.65, -1.15, -0.85, -1.78, -2.28, -2.82

    def left(self, m, y: float, x: float = LEFT_X):
        return m.move_to([x + m.width / 2, y, 0])

    def right(self, m, y: float, x: float = 6.4):
        return m.move_to([x - m.width / 2, y, 0])

    def construct(self):
        n = numbers()
        assert n["title"] in LITERALS
        x_exact = float(Fraction(int(n["out"].replace(",", "")) * int(n["rate"].replace(".", "")), 10**WAD))
        x_down, x_up = float(n["mul_down"]), float(n["mul_up"])

        # chrome on the first frame, never animated: title, pool, caption, the grid and its labels, the bar's track and axis
        self.section(0)
        title = self.left(words(n["title"], SIZE_BODY, Palette.MUTED), self.Y_TITLE)
        chain = self.right(words(f"· {n['chain']}", SIZE_BODY, Palette.MUTED), self.Y_TITLE)
        pool_lbl = words(f"{n['pool']} pool", SIZE_BODY, HUE).next_to(chain, LEFT, buff=0.2).set_y(self.Y_TITLE)
        caption = words(f"scripts/replays/balancer.json · tx {n['tx_short']} · block {n['block']}", SIZE_CAPTION, Palette.FAINT).to_corner(DOWN + LEFT, buff=0.45)
        self._caption = caption
        line = GridLine(GRID, length=7.0, tick_size=0.14).move_to([-2.0, self.Y_LINE, 0])
        tick_lbls = VGroup(*[digits(str(k), SIZE_BODY - 6, Palette.FAINT).move_to([line.n2p(k)[0], self.Y_TICKS, 0]) for k in n["grid_ticks"]])
        axis_title = words("osETH, in wei", SIZE_BODY, Palette.MUTED).next_to(line.get_end(), RIGHT, buff=0.4).set_y(self.Y_TICKS)
        bar_w, bar_h = 5.6, 0.3
        track = Rectangle(width=bar_w, height=bar_h, color=Palette.RULE, stroke_width=1.5).move_to([6.3 - bar_w / 2, self.Y_BAR, 0])
        bar_title = words(f"D*, the pool's invariant, from 0 to {n['d_start']} wei-eq", SIZE_CAPTION, Palette.FAINT).next_to(track, UP, buff=0.1).align_to(track, RIGHT)
        self.add(title, chain, pool_lbl, caption, line, tick_lbls, axis_title, track, bar_title)
        self.wait(0.3)

        # before: the pool as the attacker left it, and what the swap asks out
        before_lbl = self.left(words("after the drain (wei)", SIZE_BODY, Palette.MUTED), self.Y_BEFORE)
        found = digits(f"WETH {n['weth_before']} · osETH {n['rate_before']} · out {n['out']}", SIZE_BODY, Palette.TEXT).next_to(before_lbl, RIGHT, buff=0.4).set_y(self.Y_BEFORE)
        self.play(FadeIn(before_lbl, run_time=0.4))
        self.play(AddTextLetterByLetter(found, time_per_char=0.06))
        self.wait(1.2)

        # step: the decisive multiplication, in the contract's own terms
        self.section(1, hold=2.0)
        formula = self.left(words("_upscale = mulDown(amount × rate)", SIZE_BODY, Palette.TEXT), self.Y_FORMULA)
        cite = self.right(words(f"{n['upscale_cite']} · {n['muldown_cite']}", CITE, Palette.FAINT), self.Y_FORMULA)
        self.play(FadeIn(formula, shift=RIGHT * 0.1, run_time=0.6))
        self.play(FadeIn(cite, run_time=0.5))
        self.wait(0.8)
        operands = self.left(digits(f"{n['out']} × {n['rate']}", SIZE_BODY, Palette.TEXT), self.Y_OPERANDS)
        operands_lbl = words("amount out × osETH rate", SIZE_BODY, Palette.MUTED).next_to(operands, RIGHT, buff=0.4).set_y(self.Y_OPERANDS)
        self.play(AddTextLetterByLetter(operands, time_per_char=0.08))
        self.play(FadeIn(operands_lbl, run_time=0.4))
        self.wait(1.0)
        product = self.left(digits(f"= {n['product']}", SIZE_BODY, Palette.EXACT), self.Y_PRODUCT)
        product_lbl = words(n["product_label"], STATED, Palette.MUTED).next_to(product, RIGHT, buff=0.3).set_y(self.Y_PRODUCT)
        self.play(AddTextLetterByLetter(product, time_per_char=0.1))
        self.play(FadeIn(product_lbl, run_time=0.4))
        self.wait(1.2)
        # the exact product lands on the grid, a hair under 18
        dot = line.dot_at(x_exact, Palette.EXACT)
        dot.move_to([line.n2p(x_exact)[0], self.Y_PRODUCT, 0])
        self.play(FadeIn(dot, run_time=0.3))
        self.play(dot.animate(rate_func=ease_out_cubic).move_to(line.n2p(x_exact)), run_time=1.0)
        self.wait(0.8)

        # round: mulDown drags it a whole unit down
        self.section(2, hold=2.0)
        arrow = direction(line, x_exact, x_down, Palette.WRONG, lift=0.24)
        mech = words("mulDown", SIZE_BODY, Palette.WRONG).next_to(arrow, LEFT, buff=0.15).set_y(self.Y_LINE + 0.24)
        self.play(Create(arrow, run_time=0.6), FadeIn(mech, run_time=0.4))
        self.play(snap(dot, line, x_down, Palette.WRONG, run_time=1.2))
        self.wait(0.8)
        kept_arrow = Arrow(product_lbl.get_right() + RIGHT * 0.1, product_lbl.get_right() + RIGHT * 0.55, buff=0, color=Palette.WRONG, stroke_width=2.5, tip_length=0.11, max_tip_length_to_length_ratio=1.0)
        kept = digits(n["mul_down"], SIZE_BODY, Palette.WRONG).next_to(kept_arrow, RIGHT, buff=0.15).set_y(self.Y_PRODUCT)
        self.play(Create(kept_arrow, run_time=0.4), FadeIn(kept, shift=DOWN * 0.1, run_time=0.5))
        mulup = words(f"mulUp would give {n['mul_up']}", SIZE_BODY, Palette.MUTED).next_to(line.get_end(), RIGHT, buff=0.4).set_y(self.Y_LINE)
        up_dot = line.dot_at(x_up, Palette.MUTED, radius=0.07)
        self.play(FadeIn(mulup, run_time=0.5), FadeIn(up_dot, run_time=0.5))
        self.wait(1.5)
        # what the pool charged for the swap, against the exact charge
        y_c = self.Y_CHARGE
        charged_lbl = self.left(words("charged", SIZE_BODY, Palette.MUTED), y_c)
        charged = digits(n["charged"], SIZE_BODY, Palette.WRONG).next_to(charged_lbl, RIGHT, buff=0.25).set_y(y_c)
        cross = cross_mark(Palette.WRONG).next_to(charged, RIGHT, buff=0.25).set_y(y_c)
        self.play(FadeIn(charged_lbl, run_time=0.35))
        self.play(AddTextLetterByLetter(charged, time_per_char=0.08))
        self.play(Create(cross, run_time=0.4))
        self.wait(0.6)
        exact_lbl = words("exact", SIZE_BODY, Palette.MUTED).next_to(cross, RIGHT, buff=0.5).set_y(y_c)
        exact_v = digits(n["exact"], SIZE_BODY, Palette.EXACT).next_to(exact_lbl, RIGHT, buff=0.25).set_y(y_c)
        self.play(FadeIn(exact_lbl, run_time=0.35))
        self.play(AddTextLetterByLetter(exact_v, time_per_char=0.06))
        self.wait(1.2)
        under = self.right(words(f"{n['under_pct']} under", SIZE_BODY, Palette.WRONG), y_c)
        under_arrow = Arrow(under.get_left() + LEFT * 0.55, under.get_left() + LEFT * 0.12, buff=0, color=Palette.WRONG, stroke_width=2.5, tip_length=0.11, max_tip_length_to_length_ratio=1.0)
        self.play(Create(under_arrow, run_time=0.3), FadeIn(under, shift=RIGHT * 0.1, run_time=0.5))

        # repeat: the cycle, thirty times, while the invariant drains
        self.section(3, hold=1.5)
        counter = self.left(digits("0", SIZE_BODY, HUE), self.Y_R1)
        cycles_lbl = words(f"of {n['cycles']} cycles · {n['pool']}", SIZE_BODY, Palette.MUTED).next_to(counter, RIGHT, buff=0.25).set_y(self.Y_R1)
        self.play(FadeIn(cycles_lbl, run_time=0.4), FadeIn(counter, run_time=0.4))
        level = ValueTracker(1.0)
        fill = always_redraw(
            lambda: Rectangle(width=max(bar_w * level.get_value(), 0.02), height=bar_h, color=HUE, fill_color=HUE, fill_opacity=0.85, stroke_width=0).move_to(track.get_left() + RIGHT * max(bar_w * level.get_value(), 0.02) / 2)
        )
        self.add(fill)
        self.wait(0.3)
        ticks = [digits(str(k), SIZE_BODY, HUE).move_to(counter) for k in n["counter_ticks"]]
        for k in range(1, n["cycles"] + 1):
            self.play(Transform(counter, ticks[k - 1]), level.animate.set_value(n["d_levels"][k - 1]), run_time=0.11)
        self.wait(0.3)
        end_lbl = digits(f"{n['d_end']} {n['d_ratio']}", SIZE_BODY, Palette.WRONG).next_to(track, DOWN, buff=0.08).align_to(track, RIGHT)
        drain_arrow = Arrow(end_lbl.get_left() + LEFT * 0.12, end_lbl.get_left() + LEFT * 0.6, buff=0, color=Palette.WRONG, stroke_width=2.5, tip_length=0.11, max_tip_length_to_length_ratio=1.0)
        self.play(Create(drain_arrow, run_time=0.5), FadeIn(end_lbl, shift=DOWN * 0.1, run_time=0.5))
        # the second pool, the same cycle
        counter2 = self.left(digits("0", SIZE_BODY, HUE), self.Y_R2)
        cycles_lbl2 = words(f"of {n['other_cycles']} cycles · {n['other_pool']}", SIZE_BODY, Palette.MUTED).next_to(counter2, RIGHT, buff=0.25).set_y(self.Y_R2)
        self.play(FadeIn(cycles_lbl2, run_time=0.4), FadeIn(counter2, run_time=0.4))
        ticks2 = [digits(str(k), SIZE_BODY, HUE).move_to(counter2) for k in n["counter_ticks"][: n["other_cycles"]]]
        for k in range(1, n["other_cycles"] + 1):
            self.play(Transform(counter2, ticks2[k - 1]), run_time=0.09)

        # take
        self.section(4, hold=1.5)
        loss = self.left(words(f"{n['loss']} across five chains", SIZE_BODY, Palette.TEXT), self.Y_TAKE)
        net = self.right(words(f"net to the attacker: {n['net_eth']} ETH", SIZE_BODY, Palette.MUTED), self.Y_TAKE)
        self.play(FadeIn(loss, shift=UP * 0.08, run_time=0.7))
        self.wait(1.5)
        self.play(FadeIn(net, run_time=0.6))

        # exact: the same calls carried inside FP127 / FP19, rounded up to wei once
        self.section(5, hold=1.5)
        head = self.left(words("FP127 / FP19 inside, ceil to wei once", SIZE_BODY, Palette.CORRECT), self.Y_E1)
        replayed = words("· replayed, not observed", SIZE_BODY, Palette.MUTED).next_to(head, RIGHT, buff=0.3).set_y(self.Y_E1)
        zero = self.left(digits(str(n["fp_below"]), SIZE_HERO, Palette.CORRECT), self.Y_E2)
        tail = words(f"calls below exact · the attacker would lose {n['would_lose']} ETH", SIZE_BODY, Palette.TEXT).next_to(zero, RIGHT, buff=0.25).set_y(self.Y_E2)
        tick = check_mark(Palette.CORRECT).next_to(tail, RIGHT, buff=0.35).set_y(self.Y_E2)
        panel = glow_bar(VGroup(head, zero, tail, tick), Palette.CORRECT, pad=0.12)
        self.play(FadeIn(panel, run_time=0.5), FadeIn(head, shift=RIGHT * 0.1, run_time=0.6))
        self.play(FadeIn(replayed, run_time=0.4))
        # on the grid the product stays where it is: an emerald value under a halo
        glow = halo(line.n2p(x_exact), Palette.CORRECT)
        kept_dot = line.dot_at(x_exact, Palette.CORRECT)
        self.play(FadeIn(glow, run_time=0.5), FadeIn(kept_dot, run_time=0.5))
        self.wait(0.6)
        self.play(FadeIn(zero, shift=UP * 0.08, run_time=0.6))
        self.play(FadeIn(tail, run_time=0.6))
        self.play(Create(tick, run_time=0.5))
        self.close()

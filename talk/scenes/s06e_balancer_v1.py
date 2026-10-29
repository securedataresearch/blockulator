"""Slide 6e, "Balancer V1, 31 Aug 2026": one round-to-nearest, 438 times.

Pool 1 of the five (scripts/replays/balancer_v1.json, tx order) as the
attacker found it: DPI 546.83609422, WBTC 35,748,405 satoshi; the swaps
push WBTC down to 3 satoshi, the balance the loop runs at. The decisive
line is BMath.sol's newTokenBalanceIn = bmul(tokenInRatio, balance)
(calcSingleInGivenPoolOut, BMath.sol:156-182; bmul BNum.sol:63-73, half
up on the 10^-18 grid). BNum's ratio at the first join at balance 3 is
1.499999999999999997 (18 decimals, the deployed integer); × 3 =
4.499999999999999991, exact at 18 decimals. On the satoshi grid the new
balance sits 9 × 10^-18 below the half-way mark between 4 and 5, and
bmul's nearest takes it to 4 (WRONG, red), so the join costs 1 satoshi
for 1.5056462 satoshi's worth (pool 1's exact cost, by Fraction). Then a
counter ticks through the 438 joins (100 in pool 1, 400 of the 438 at a
balance of 3) while the WBTC readout runs the loop (3, 4, 3, 4 …) and
pool 1's DPI drains 546.83609422 → 0.57099095 (−99.90%), the balances
walked op by op on the logged amounts (vocab.balancer_v1_balances).
The take is $1.39M (incidents.json). Last, the same join rounded toward
the pool: the new balance 5, the join costs 2 against maxAmountIn = 1 and
reverts; BL127 and BL19 with one ceil to the unit give 2 on every join
(the generated table, docs/benchmarks/replay-balancer-v1.md, cross-checked
against the exact ceil by Fraction); the exact cost per join over all 438
is 1.50079 to 1.52749 units (CORRECT, emerald; Blockulator's row is the
hero).

Numbers from scripts/replays/balancer_v1.json (.pools[0].state, .tx,
.block, .time, .source.lines) through balancer_v1_replay() (the joins
with BNum's intermediate integers), balancer_v1_balances() (the per-op
balances), replay_table() (the BL127 / BL19 column, forge's: the table
alone carries it) and incidents.json (the loss, the date). Every derived
value is computed here with Fraction; check.py recomputes by Decimal.
"""

from __future__ import annotations

from bisect import bisect_left
from fractions import Fraction

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    Create,
    FadeIn,
    Rectangle,
    Text,
    ValueTracker,
    VGroup,
    always_redraw,
    linear,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    MONO as MONO_FONT,
    SIZE_BODY,
    SIZE_CAPTION,
    SIZE_HERO,
    DeckScene,
    GridLine,
    Palette,
    _load,
    balancer_v1_balances,
    balancer_v1_replay,
    check_mark,
    digits,
    direction,
    glow_bar,
    halo,
    incidents,
    markup,
    measure,
    midpoint,
    replay_table,
    setup_fonts,
    snap,
    thousands,
    to_decimals,
    words,
)

PROTOCOL = "Balancer V1"  # incidents.json's name
POOL = 0  # the pool the step is drawn from (tx order): pool 1
WAD = 18  # BNum's grid, 10^-18: the ratio and the product are 18-decimal
TOKEN_DECIMALS = 8  # token balances as drawn (the md's units(): at most 8)
COST_DECIMALS = 7  # pool 1's exact cost per join, as drawn
RANGE_DECIMALS = 5  # the exact cost over all 438 joins, as C5 states it
PCT_DECIMALS = 2  # the DPI drain as drawn
TX_SHORT = 8  # hex digits of the transaction hash in the caption
GRID = (3, 6, 1)  # satoshi around the new balance
EPS = 0.06  # the dot's visual offset left of the half (not to scale: the real gap is 9 × 10^-18)
TABLE_HEADING = "Every join and exit"
HAPPENED_HEADING = "What happened"

HUE = Palette.SAPPHIRE  # Balancer V1 (the palette has no second gold; the name stands beside every use)
X_LEFT = -6.3
X_RIGHT = 0.9
X_EDGE = 6.3
BAR_W = 4.2
SANS = 26
MONO = 26
SMALL = 22
LABEL = SIZE_CAPTION

Y_ROWS = (2.75, 2.35, 1.95)
Y_NOTE = 1.6  # the loop's note under the rows
Y_FORMULA = 1.15
Y_CITE = (0.82, 0.54)  # the two source citations
Y_OPERANDS = 0.18
Y_RESULT = -0.22
Y_GRID = -1.0
GRID_LEN = 5.6
Y_TICKS = -1.85
Y_AXIS = -2.12
Y_EXACT = (-2.42, -2.77, -3.1)
Y_COUNTER = 2.95
Y_BAR = 2.35
Y_WBTC = 1.7
Y_AT3 = 1.35
Y_TAKE = 0.85
Y_WHY = (0.45, 0.2)
Y_ROUND = (-0.55, -0.95, -1.35, -1.75)

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def _units(raw: int, decimals: int) -> str:
    """A raw token amount in units to TOKEN_DECIMALS, half-up, thousands separators."""
    s = to_decimals(Fraction(raw, 10**decimals), min(decimals, TOKEN_DECIMALS))
    whole, _, frac = s.partition(".")
    return f"{thousands(whole)}.{frac}" if frac else thousands(whole)


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
    pools = d["pools"]
    pool = pools[POOL]
    inc = next(i for i in incidents()["incidents"] if i["protocol"] == PROTOCOL)
    assert pool["time"].startswith("2026-08-31") and inc["date"] == "31 Aug 2026", (pool["time"], inc["date"])
    replay = balancer_v1_replay()
    rows = replay[POOL]
    joins = [r for r in rows if r["kind"] == 2]
    all_joins = [r for p in replay for r in p if r["kind"] == 2]
    at3 = [r for r in all_joins if r["balance"] == 3]
    first = next(r for r in joins if r["balance"] == 3)
    ratio = first["steps"]["tokenInRatio"]
    assert {r["steps"]["tokenInRatio"] for r in joins if r["balance"] == 3} == {ratio}, "one ratio at balance 3 in pool 1"
    product = Fraction(first["balance"] * ratio, 10**WAD)
    nearest = (first["balance"] * ratio + 10**WAD // 2) // 10**WAD  # bmul, BNum.sol: half up
    toward = -((-first["balance"] * ratio) // 10**WAD)  # ceil, toward the pool
    assert nearest == first["steps"]["newTokenBalanceIn"] == 4 and toward == 5 and product < Fraction(9, 2), (nearest, toward)
    below_half = (Fraction(9, 2) - product) * 10**WAD
    assert below_half.denominator == 1 and first["deployed"] == 1 == first["limit"]
    cost = _exact_cost(first)
    costs = [_exact_cost(r) for r in all_joins]
    assert all(Fraction(3, 2) < c < 2 for c in costs) and {-((-c.numerator) // c.denominator) for c in costs} == {2}
    tokens = pool["state"]["tokens"]
    sym = [t["symbol"] for t in tokens]
    di, wi = sym.index("DPI"), sym.index("WBTC")
    assert first["token"] == wi and all(r["token"] == wi for r in joins)
    bal = balancer_v1_balances(POOL)
    assert bal["joins"] == [r["op"] for r in joins] and bal["balances"][0] == [int(t["balance"]) for t in tokens]
    assert all(bal["balances"][op][wi] == r["balance"] for op, r in zip(bal["joins"], joins))
    dpi0, dpi1 = bal["balances"][0][di], bal["balances"][-1][di]
    wbtc0 = bal["balances"][0][wi]
    loop = max({r["balance"] for r in joins}, key=lambda b: sum(1 for r in joins if r["balance"] == b))
    assert loop == 3
    lines = d["source"]["lines"]
    fn, bm = lines["BMath.sol"]["calcSingleInGivenPoolOut"], lines["BNum.sol"]["bmul"]
    # the generated table says the same (docs/benchmarks/replay-balancer-v1.md, through replay_table)
    table = [r for r in replay_table("balancer-v1", TABLE_HEADING) if r["call"].startswith("join")]
    assert [int(r["n"]) for r in table] == [sum(1 for r in p if r["kind"] == 2) for p in replay], table
    assert all(r["BL127"] == r["BL19"] == r["exact, rounded"] == "2" and r["deployed"] == "1" and r["pays?"] == "no" for r in table), table
    happened = replay_table("balancer-v1", HAPPENED_HEADING)[POOL]
    assert happened["its balance before → in the loop"] == f"{wbtc0} → {loop} units" and happened["joins / exits"].startswith(f"{len(joins)} /"), happened
    fp_join = table[POOL]["BL127"]  # forge's figure: the table alone carries it (cross-checked against the exact ceil above)

    def pct(q: Fraction, places: int) -> str:
        return to_decimals(q * 100, places).replace("-", "−") + "%"

    return {
        "protocol": inc["protocol"],
        "date": inc["date"],
        "chain": "Ethereum",
        "block": thousands(pool["block"]),
        "tx_short": pool["tx"][: 2 + TX_SHORT],
        "tx_short_len": TX_SHORT,
        "tx_len": len(pool["tx"]) - 2,
        "pool_index": POOL + 1,
        "pools": len(pools),
        "dpi_before": _units(dpi0, tokens[di]["decimals"]),
        "wbtc_before": thousands(wbtc0),
        "loop_balance": loop,
        "joins_pool": len(joins),
        "at3_pool": sum(1 for r in joins if r["balance"] == 3),
        "cite_fn": f"BMath.sol:{fn[0]}-{fn[1]}",
        "cite_bmul": f"BNum.sol:{bm[0]}-{bm[1]}",
        "ratio": to_decimals(Fraction(ratio, 10**WAD), WAD),
        "balance": first["balance"],
        "product": to_decimals(product, WAD),
        "product_label": f"(to {WAD} decimals)",
        "grid_ticks": list(range(GRID[0], GRID[1] + 1)),
        "below_half_e18": int(below_half),
        "wad": WAD,
        "nearest": nearest,
        "toward": toward,
        "charged": first["deployed"],
        "limit": first["limit"],
        "cost": to_decimals(cost, COST_DECIMALS),
        "cost_label": f"(to {COST_DECIMALS} decimals)",
        "joins": len(all_joins),
        "at3": len(at3),
        "dpi_path": [b[di] for b in bal["balances"]],
        "wbtc_path": [b[wi] for b in bal["balances"]],
        "join_ops": bal["joins"],
        "dpi_after": _units(dpi1, tokens[di]["decimals"]),
        "dpi_pct": pct(Fraction(dpi1, dpi0) - 1, PCT_DECIMALS),
        "loss": inc["loss"],
        "source": inc["source"],
        "cost_min": to_decimals(min(costs), RANGE_DECIMALS),
        "cost_max": to_decimals(max(costs), RANGE_DECIMALS),
        "cost_toward": -((-cost.numerator) // cost.denominator),
        "fp_join": fp_join,
    }


class BalancerV1(DeckScene):
    SECTIONS = ("before", "step", "round", "repeat", "take", "exact")

    def left(self, m, x: float, y: float):
        m.move_to([x + m.width / 2, y, 0])
        return m

    def right(self, m, x: float, y: float):
        m.move_to([x - m.width / 2, y, 0])
        return m

    def row(self, label: str, value: str, y: float, colour: str = Palette.EXACT, size: float = MONO):
        lbl = self.left(words(label, SANS, Palette.MUTED), X_LEFT, y)
        val = digits(value, size, colour).next_to(lbl, RIGHT, buff=0.4).set_y(y)
        return lbl, val

    def bar(self, y: float, name: str, start_label: str):
        """A bar's chrome: the track, its name above its left end, the start value above its right end."""
        track = Rectangle(width=BAR_W, height=0.24, color=Palette.RULE, stroke_width=1.5, fill_opacity=0).move_to([X_RIGHT + BAR_W / 2, y, 0])
        name_t = self.left(words(name, LABEL, Palette.MUTED), X_RIGHT, y + 0.25)
        start = digits(start_label, LABEL, Palette.FAINT).move_to([X_EDGE - 0.1, y + 0.25, 0]).align_to([X_EDGE, 0, 0], RIGHT)
        return VGroup(track, name_t, start)

    def fill(self, track: Rectangle, tracker: ValueTracker, share):
        """The bar's data: a fill in the protocol's hue from the left edge, its width the share at the tracker's step."""
        left = track.get_left()

        def make():
            k = int(round(tracker.get_value()))
            w = max(float(share(k)) * BAR_W, 1e-3)
            return Rectangle(width=w, height=0.24, color=HUE, fill_color=HUE, fill_opacity=0.85, stroke_width=0).move_to(left + RIGHT * w / 2)

        return always_redraw(make)

    def ticking(self, text, at, size: float = SIZE_BODY, colour: str = HUE):
        """A readout that follows a tracker; the intermediate frames are plain Text
        (not a drawn claim); the final string is drawn through digits() by the caller."""
        setup_fonts()

        def make():
            return Text(text(), font=MONO_FONT, font_size=size, color=colour, disable_ligatures=True).move_to(at).align_to([at[0], 0, 0], LEFT)

        return always_redraw(make)

    def construct(self):
        n = numbers()
        join_ops, dpi_path, wbtc_path = n["join_ops"], n["dpi_path"], n["wbtc_path"]
        ops = len(dpi_path) - 1
        x_half = float(Fraction(n["nearest"] + n["toward"], 2))  # the half-way mark (the product is 9 × 10^-18 under it: one float)
        x_dot = x_half - EPS

        self.section(0)
        # chrome, on the first frame: the title, the caption, the grid with its labels and the half-way mark, the bar's track
        title = self.title(f"<span foreground='{HUE}'>{n['protocol']}</span> · {n['date']} · {n['chain']}", SIZE_BODY, Palette.TEXT, use_markup=True)
        self.add(title)
        self._caption = words(
            f"scripts/replays/balancer_v1.json · tx {n['tx_short']} ({n['tx_short_len']} of {n['tx_len']} hex digits) · block {n['block']} · pool {n['pool_index']} of {n['pools']}",
            SIZE_CAPTION,
            Palette.FAINT,
        ).to_corner(DOWN + LEFT, buff=0.4)
        self.add(self._caption)
        line = GridLine(GRID, length=GRID_LEN, tick_size=0.14).move_to([X_LEFT + GRID_LEN / 2, Y_GRID, 0])
        tick_lbls = VGroup(*[digits(str(k), LABEL, Palette.FAINT).move_to([line.n2p(k)[0], Y_TICKS, 0]) for k in n["grid_ticks"]])
        axis = words("WBTC in the pool, satoshi: the new balance", LABEL, Palette.FAINT).move_to([line.get_center()[0], Y_AXIS, 0])
        mid = midpoint(line, n["nearest"], n["toward"], height=0.6)
        self.add(line, tick_lbls, axis, mid)
        bar = self.bar(Y_BAR, f"{n['protocol']} · DPI in pool {n['pool_index']}", n["dpi_before"])
        bar[1].set_color(HUE)  # the protocol's name beside its hue
        self.add(bar)
        self.wait(0.3)

        # the state the attacker found, and the balance the loop runs at
        lbl, val = self.row(f"pool {n['pool_index']}, before", f"DPI {n['dpi_before']}", Y_ROWS[0], size=24)
        self.play(FadeIn(lbl, run_time=0.35))
        self.play(AddTextLetterByLetter(val, time_per_char=0.04))
        self.wait(0.3)
        lbl, val = self.row("WBTC, before", f"{n['wbtc_before']} satoshi", Y_ROWS[1], size=24)
        self.play(FadeIn(lbl, run_time=0.35))
        self.play(AddTextLetterByLetter(val, time_per_char=0.04))
        self.wait(0.3)
        lbl, val = self.row("in the loop", f"WBTC {n['loop_balance']} satoshi", Y_ROWS[2], Palette.EXACT, SIZE_BODY)
        how = self.left(words(f"pushed down by swaps · {n['at3_pool']} of {n['joins_pool']} joins run at {n['loop_balance']}", LABEL, Palette.FAINT), X_LEFT, Y_NOTE)
        self.play(FadeIn(lbl, run_time=0.35))
        self.play(FadeIn(val, shift=UP * 0.1, run_time=0.6), FadeIn(how, run_time=0.6))

        # the decisive line, in the contract's terms, and the first join's operands
        self.section(1, hold=1.5)
        formula = words("newBalance  =  bmul(tokenInRatio, balance)", SANS, Palette.TEXT)
        self.left(formula, X_LEFT, Y_FORMULA)
        self.play(FadeIn(formula, shift=RIGHT * 0.1, run_time=0.6))
        cite1 = self.left(digits("calcSingleInGivenPoolOut · bmul, half up", LABEL, Palette.FAINT), X_LEFT, Y_CITE[0])
        cite2 = self.left(digits(f"{n['cite_fn']} · {n['cite_bmul']}", LABEL, Palette.FAINT), X_LEFT, Y_CITE[1])
        self.play(FadeIn(cite1, run_time=0.5), FadeIn(cite2, run_time=0.5))
        self.wait(1.0)
        operands = digits(f"{n['ratio']} × {n['balance']}", 24, Palette.TEXT)
        self.left(operands, X_LEFT, Y_OPERANDS)
        self.play(AddTextLetterByLetter(operands, time_per_char=0.045))
        eq = self.left(digits("=", SIZE_BODY, Palette.MUTED), X_LEFT, Y_RESULT)
        product = digits(n["product"], SIZE_BODY, Palette.EXACT).next_to(eq, RIGHT, buff=0.3).set_y(Y_RESULT)
        p_lbl = words(n["product_label"], LABEL, Palette.FAINT).next_to(product, RIGHT, buff=0.25).set_y(Y_RESULT)
        self.play(FadeIn(eq, run_time=0.3))
        self.play(AddTextLetterByLetter(product, time_per_char=0.09))
        self.play(FadeIn(p_lbl, run_time=0.4))

        # the nearest, on the satoshi grid
        self.section(2, hold=2.0)
        dot = line.dot_at(x_dot, Palette.EXACT)
        dot.move_to(line.n2p(x_dot) + UP * 1.0)
        self.play(FadeIn(dot, run_time=0.3))
        self.play(dot.animate(rate_func=ease_out_cubic).move_to(line.n2p(x_dot)), run_time=0.8)
        half = measure(line, n["nearest"], x_half, "half a unit", scale=0.72, drop=0.42, colour=Palette.MUTED)
        self.play(Create(half[0], run_time=0.5), Create(half[1], run_time=0.5), FadeIn(half[2], run_time=0.4))
        under = self.left(markup(f"{n['below_half_e18']} × 10<sup>−{n['wad']}</sup> satoshi below the half (not to scale)", LABEL, Palette.FAINT), X_RIGHT, Y_ROUND[0])
        self.play(FadeIn(under, run_time=0.5))
        self.wait(0.6)
        arrow = direction(line, x_dot, float(n["nearest"]), Palette.WRONG, lift=0.28)
        mech = words("nearest", SMALL, Palette.WRONG).next_to(arrow, UP, buff=0.08)
        self.play(Create(arrow, run_time=0.6), FadeIn(mech, run_time=0.4))
        self.play(snap(dot, line, float(n["nearest"]), Palette.WRONG, run_time=1.0))
        bmul_word = words("bmul", SANS, Palette.WRONG).next_to(p_lbl, RIGHT, buff=0.6).set_y(Y_RESULT)
        bmul_val = digits(str(n["nearest"]), SIZE_BODY, Palette.WRONG).next_to(bmul_word, RIGHT, buff=0.3).set_y(Y_RESULT)
        self.play(FadeIn(bmul_word, run_time=0.4), FadeIn(bmul_val, shift=DOWN * 0.1, run_time=0.5))
        charged = self.left(markup(f"the join costs <span foreground='{Palette.WRONG}'>{n['charged']} satoshi</span>", SMALL, Palette.TEXT), X_RIGHT, Y_ROUND[1])
        worth = self.left(markup(f"for <span foreground='{Palette.EXACT}'>{n['cost']}</span> satoshi's worth", SMALL, Palette.TEXT), X_RIGHT, Y_ROUND[2])
        worth_lbl = words(n["cost_label"], LABEL, Palette.FAINT).next_to(worth, RIGHT, buff=0.3).set_y(Y_ROUND[2])
        self.play(FadeIn(charged, shift=RIGHT * 0.1, run_time=0.5))
        self.play(FadeIn(worth, shift=RIGHT * 0.1, run_time=0.5), FadeIn(worth_lbl, run_time=0.5))
        limit = self.left(words(f"maxAmountIn = {n['limit']}: the attacker's own limit, met", LABEL, Palette.FAINT), X_RIGHT, Y_ROUND[3])
        self.play(FadeIn(limit, run_time=0.4))

        # four hundred and thirty-eight of them: the counter ticks, the loop runs, the pool drains
        self.section(3, hold=2.0)
        step = ValueTracker(0)  # pool 1's ops, 0 … ops
        more = ValueTracker(0)  # the joins of pools 2 … 5, after pool 1's

        def joins_done() -> int:
            return bisect_left(join_ops, int(round(step.get_value()))) + int(round(more.get_value()))

        counter = self.ticking(lambda: f"join {joins_done()} of {n['joins']}", [X_RIGHT, Y_COUNTER, 0])
        fill = self.fill(bar[0], step, lambda k: Fraction(dpi_path[k], dpi_path[0]))
        wbtc = self.ticking(lambda: f"WBTC {thousands(wbtc_path[int(round(step.get_value()))])} satoshi", [X_RIGHT, Y_WBTC, 0], SMALL, Palette.TEXT)
        self.add(fill)
        self.play(FadeIn(counter, run_time=0.4), FadeIn(wbtc, run_time=0.4))
        self.play(step.animate.set_value(ops), run_time=7.0, rate_func=linear)
        self.play(more.animate.set_value(n["joins"] - n["joins_pool"]), run_time=3.0, rate_func=linear)
        final = digits(f"join {n['joins']} of {n['joins']}", SIZE_BODY, HUE).move_to(counter).align_to([X_RIGHT, 0, 0], LEFT)
        wbtc_final = digits(f"WBTC {thousands(wbtc_path[-1])} satoshi", SMALL, Palette.TEXT).move_to(wbtc).align_to([X_RIGHT, 0, 0], LEFT)
        self.remove(counter, wbtc)
        self.add(final, wbtc_final)
        end1 = digits(n["dpi_pct"], LABEL, HUE).next_to(bar[0], RIGHT, buff=0.2)
        end2 = digits(f"DPI {n['dpi_after']}", LABEL, HUE).next_to(bar[0], DOWN, buff=0.08).align_to(bar[0], LEFT)
        self.play(FadeIn(end1, shift=LEFT * 0.1, run_time=0.5), FadeIn(end2, run_time=0.5))
        at3 = self.left(markup(f"<span foreground='{HUE}'>{n['at3']}</span> of the {n['joins']} at a balance of {n['loop_balance']}", SMALL, Palette.TEXT), X_RIGHT, Y_AT3)
        self.play(FadeIn(at3, shift=UP * 0.08, run_time=0.6))

        # the take
        self.section(4, hold=2.0)
        loss = self.left(words(n["loss"], SIZE_HERO, HUE), X_RIGHT, Y_TAKE)
        name = words(n["protocol"], SMALL, HUE).next_to(loss, RIGHT, buff=0.4).set_y(Y_TAKE)
        why = VGroup(
            self.left(words(f"{n['pools']} pools in {n['pools']} transactions · {n['source']}", LABEL, Palette.FAINT), X_RIGHT, Y_WHY[0]),
            self.left(words("one satoshi bought one and a half", LABEL, Palette.MUTED), X_RIGHT, Y_WHY[1]),
        )
        self.play(FadeIn(loss, shift=UP * 0.1, run_time=0.7), FadeIn(name, run_time=0.7))
        self.play(FadeIn(why, run_time=0.5))

        # the same join, rounded toward the pool: replayed, not observed
        self.section(5, hold=2.5)
        head = words("the same join rounded toward the pool · replayed, not observed", LABEL, Palette.FAINT)
        self.left(head, X_LEFT, Y_EXACT[0])
        self.play(FadeIn(head, run_time=0.4))
        glow = halo(line.n2p(float(n["toward"])), Palette.CORRECT)
        up_dot = line.dot_at(float(n["toward"]), Palette.CORRECT)
        up_arrow = direction(line, x_dot, float(n["toward"]), Palette.CORRECT, lift=0.5)
        up_lbl = words("toward the pool", SMALL, Palette.CORRECT).next_to(up_arrow, RIGHT, buff=0.2).set_y(Y_GRID + 0.5)
        self.play(FadeIn(glow, run_time=0.5), FadeIn(up_dot, run_time=0.5), Create(up_arrow, run_time=0.6), FadeIn(up_lbl, run_time=0.4))
        row1_lbl = self.left(words("toward the pool", SANS, Palette.CORRECT), X_LEFT, Y_EXACT[1])
        row1_val = digits(str(n["toward"]), SIZE_BODY, Palette.CORRECT).next_to(row1_lbl, RIGHT, buff=0.4).set_y(Y_EXACT[1])
        row1_tail = words(f"· costs {n['cost_toward']} against maxAmountIn = {n['limit']} · reverts", SMALL, Palette.TEXT).next_to(row1_val, RIGHT, buff=0.3).set_y(Y_EXACT[1])
        row2_lbl = self.left(words("BL127 / BL19, one ceil", SANS, Palette.CORRECT), X_LEFT, Y_EXACT[2])
        row2_val = digits(n["fp_join"], SIZE_BODY, Palette.CORRECT).next_to(row2_lbl, RIGHT, buff=0.4).set_y(Y_EXACT[2])
        row2_tail = words(f"on all {n['joins']} joins · exact cost {n['cost_min']} to {n['cost_max']} units", SMALL, Palette.TEXT).next_to(row2_val, RIGHT, buff=0.3).set_y(Y_EXACT[2])
        hero = VGroup(row1_lbl, row1_val, row1_tail, row2_lbl, row2_val, row2_tail)
        panel = glow_bar(hero, Palette.CORRECT, pad=0.08)
        self.play(FadeIn(panel, run_time=0.5))
        self.play(FadeIn(row1_lbl, run_time=0.3), FadeIn(row1_val, shift=UP * 0.08, run_time=0.4))
        self.play(FadeIn(row1_tail, run_time=0.4))
        self.play(FadeIn(row2_lbl, run_time=0.3), FadeIn(row2_val, shift=UP * 0.08, run_time=0.4))
        self.play(FadeIn(row2_tail, run_time=0.4))
        tick = check_mark(Palette.CORRECT).next_to(row1_tail, RIGHT, buff=0.35).set_y(Y_EXACT[1])
        stops = words("the loop stops", SMALL, Palette.CORRECT).next_to(tick, RIGHT, buff=0.25).set_y(Y_EXACT[1])
        self.play(Create(tick, run_time=0.5))
        self.play(FadeIn(stops, run_time=0.4))
        self.close()

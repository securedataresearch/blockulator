"""Slide 6b, "Bunni v2, 2 Sep 2025": forty-four floors, replayed.

The state the attacker found types in (raw USDC, the vault shares' redeem
value, the idle balance; active USDC = raw + redeem − idle = 28 wei). The
decisive line is BunniHubLogic.sol:478: the idle balance loses
floor(idle × shares / totalSupply) on every withdrawal; the first
withdrawal's operands type in and the quotient reads 23.659 (to 3
decimals). On the wei grid the dot snaps from 23.659 to 23 (WRONG, red,
"floor on the subtrahend"): the idle balance keeps 0.659 wei it should
have lost, so the active balance reads that much low. Then a counter
ticks through the 44 withdrawals while two bars drain: active USDC 28 to
4 wei and Bunni's total liquidity, 58,303,185,165,681,209 to
9,114,083,388,149,667 (−84.37%, both observed on chain). The take is
$8.4M (incidents.json). Last, the same 44 withdrawals replayed with the
idle balance held in mulDivUp (48 wei), FP127 and FP19 (35.6278…, to
40 decimals): total liquidity moves −0.0000009% and the attack stops
(CORRECT, emerald; Blockulator's rows are the hero).

Numbers from scripts/replays/bunni.json (.start, .steps, .snapshots,
.observed, .tx, .cites) through bunni_replay() (the deployed per-step
active balance), bunni_liquidity() (the module's queryLDF at every
step) and replay_table() (the FP19 row, which only the forge run
produces); the loss and date from talk/scenes/data/incidents.json.
Every derived value is computed here with Fraction.
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
    bunni_liquidity,
    bunni_replay,
    check_mark,
    digits,
    direction,
    glow_bar,
    incidents,
    markup,
    replay_table,
    setup_fonts,
    snap,
    thousands,
    to_decimals,
    words,
)

SUB_DECIMALS = 3  # the first withdrawal's subtrahend, complete to this many decimals
WORD_DECIMALS = 40  # the FP127 / FP19 active balance, as the replay table states it
PCT_DECIMALS = 2  # the liquidity change as deployed
PCT_FIX_DECIMALS = 7  # the liquidity change with the idle balance held exact
TX_SHORT = 8  # hex digits of the transaction hash in the caption
TABLE_HEADING = "Same 44 withdrawals, idle balance held differently"

HUE = Palette.GOLD  # Bunni, everywhere in the deck
X_LEFT = -6.3
X_RIGHT = 0.9  # the right column (bars, take, the round's consequence)
BAR_W = 4.2
X_EDGE = 6.3  # the right safe edge
SANS = 26
MONO = 26
SMALL = 22
LABEL = SIZE_CAPTION  # "(to N decimals)" and the citation

Y_TITLE = 3.35
Y_ROWS = (2.75, 2.35, 1.95, 1.5)
Y_FORMULA = 0.5
Y_CITE = 0.14
Y_OPERANDS = -0.26
Y_RESULT = -0.66
Y_GRID = -1.6
GRID_LEN = 5.6
Y_EXACT = (-2.45, -2.77, -3.09)
Y_COUNTER = 2.95
Y_BAR1, Y_BAR2 = 2.33, 1.7
Y_TAKE = 1.0

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def numbers() -> dict:
    d = _load("scripts/replays/bunni.json")
    r = bunni_replay()
    lq = bunni_liquidity()
    inc = [i for i in incidents()["incidents"] if i["protocol"].startswith("Bunni")]
    assert len(inc) == 1, inc
    inc = inc[0]
    st, steps = d["start"], d["steps"]
    raw0, idle0, T0 = int(st["raw0"]), int(st["idle"]), int(st["totalSupply"])
    redeem = r["bal0"][0] - raw0  # the vault shares' redeem value, as the hub reads it
    active = [int(a) for a in r["seq"]["deployed"]]
    n = len(steps["shares"])
    assert len(active) == n + 1 and active[0] == raw0 + redeem - idle0
    s0 = int(steps["shares"][0])
    sub = Fraction(idle0 * s0, T0)
    floor = idle0 * s0 // T0
    assert int(d["snapshots"]["after"][0]) == 1 and idle0 - int(d["snapshots"]["idle"][0]) == floor, "the chain's idle balance fell by the floor"
    L_start = int(d["observed"]["swap3"]["totalLiquidity"])
    L_end = int(d["observed"]["afterWithdrawals"]["totalLiquidity"])
    assert lq["steps"][-1] == L_end == lq["forms"]["deployed"]
    cite = {c["id"]: c for c in d["cites"]}
    fp127 = r["seq"]["fp127"][-1]
    exact = r["seq"]["exact"][-1]
    assert abs(fp127 - exact) < Fraction(n, 1 << 128)
    up = r["seq"]["mulDivUp"][-1]
    # the FP19 row is the forge run's; only the table carries it (REPORT)
    table = {row["idle balance"]: row for row in replay_table("bunni", TABLE_HEADING)}
    fp19 = table["FP19 idle balance"]["active USDC after 44 (wei)"]
    assert len(fp19.partition(".")[2]) == WORD_DECIMALS and fp19[: len(fp19) - 3] == to_decimals(exact, WORD_DECIMALS)[: len(fp19) - 3]
    pct_fix = Fraction(lq["forms"]["mulDivUp"], lq["start"]) - 1
    assert lq["forms"]["fp127"] == lq["forms"]["mulDivUp"] == lq["forms"]["exact"]

    def pct(q: Fraction, places: int) -> str:
        return to_decimals(q * 100, places).replace("-", "−") + "%"

    return {
        "protocol": inc["protocol"],
        "date": inc["date"],
        "chain": "Ethereum",
        "block": thousands(d["tx"]["block"]),
        "tx_short": d["tx"]["hash"][: 2 + TX_SHORT],
        "tx_short_len": TX_SHORT,
        "tx_len": len(d["tx"]["hash"]) - 2,
        "raw": thousands(raw0),
        "redeem": thousands(redeem),
        "idle": thousands(idle0),
        "active_start": active[0],
        "active_end": active[-1],
        "active": active,
        "withdrawals": n,
        "shares": thousands(s0),
        "supply": thousands(T0),
        "sub": to_decimals(sub, SUB_DECIMALS),
        "sub_label": f"(to {SUB_DECIMALS} decimals)",
        "floor": str(floor),
        "kept": to_decimals(sub - floor, SUB_DECIMALS),
        "grid_ticks": [floor, floor + 1],
        "idle_after": thousands(int(d["snapshots"]["idle"][0])),
        "cite_file": cite["idle"]["file"].split("/")[-1],
        "cite_line": cite["idle"]["line"],
        "cite_text": cite["idle"]["text"],
        "liq_start": thousands(L_start),
        "liq_end": thousands(L_end),
        "liq_pct": pct(Fraction(L_end, L_start) - 1, PCT_DECIMALS),
        "loss": inc["loss"],
        "up": str(up),
        "fp127": to_decimals(fp127, WORD_DECIMALS),
        "fp19": fp19,
        "word_label": f"(to {WORD_DECIMALS} decimals)",
        "fix_pct": pct(pct_fix, PCT_FIX_DECIMALS),
    }


class Bunni(DeckScene):
    SECTIONS = ("before", "step", "round", "repeat", "take", "exact")

    def left(self, m, x: float, y: float):
        m.move_to([x + m.width / 2, y, 0])
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
        """The bar's data: a GOLD fill from the left edge, its width the share at the tracker's step."""
        left = track.get_left()

        def make():
            k = int(round(tracker.get_value()))
            w = max(float(share(k)) * BAR_W, 1e-3)
            return Rectangle(width=w, height=0.24, color=HUE, fill_color=HUE, fill_opacity=0.85, stroke_width=0).move_to(left + RIGHT * w / 2)

        return always_redraw(make)

    def ticking(self, tracker: ValueTracker, total: int, at):
        """"withdrawal <k> of <total>"; the intermediate frames are plain Text (not a drawn
        claim); the final string is drawn through digits() by the caller."""
        setup_fonts()

        def make():
            return Text(f"withdrawal {int(round(tracker.get_value()))} of {total}", font=MONO_FONT, font_size=SIZE_BODY, color=HUE, disable_ligatures=True).move_to(at).align_to([X_RIGHT, 0, 0], LEFT)

        return always_redraw(make)

    def construct(self):
        n = numbers()
        self.section(0)
        # chrome, on the first frame: the title, the caption, the grid with its labels, the bars' tracks
        title = markup(f"<span foreground='{HUE}'>{n['protocol']}</span> · {n['date']} · {n['chain']}", SIZE_BODY, Palette.TEXT)
        self.left(title, X_LEFT, Y_TITLE)
        self.add(title)
        self._caption = words(f"scripts/replays/bunni.json · tx {n['tx_short']} ({n['tx_short_len']} of {n['tx_len']} hex digits) · block {n['block']}", SIZE_CAPTION, Palette.FAINT).to_corner(DOWN + LEFT, buff=0.4)
        self.add(self._caption)
        line = GridLine((n["grid_ticks"][0], n["grid_ticks"][1], 1), length=GRID_LEN, tick_size=0.14).move_to([X_LEFT + GRID_LEN / 2, Y_GRID, 0])
        tick_lbls = VGroup(*[digits(str(k), LABEL, Palette.FAINT).next_to(line.n2p(k), DOWN, buff=0.2) for k in n["grid_ticks"]])
        axis = words("wei of idle removed, withdrawal one", LABEL, Palette.FAINT).next_to(tick_lbls, DOWN, buff=0.05)
        axis.set_x(line.get_center()[0])
        self.add(line, tick_lbls, axis)
        bar1 = self.bar(Y_BAR1, "active USDC, wei", str(n["active_start"]))
        bar2 = self.bar(Y_BAR2, "total liquidity", n["liq_start"])
        self.add(bar1, bar2)
        self.wait(0.3)

        # the state the attacker found: three integers, and the one they make
        for (label, key), y in zip((("raw USDC", "raw"), ("vault shares redeem to", "redeem"), ("idle balance", "idle")), Y_ROWS):
            lbl, val = self.row(label, n[key], y, size=24)
            self.play(FadeIn(lbl, run_time=0.35))
            self.play(AddTextLetterByLetter(val, time_per_char=0.04))
            self.wait(0.3)
        lbl, val = self.row("active USDC", f"{n['active_start']} wei", Y_ROWS[3], Palette.EXACT, SIZE_BODY)
        how = words("= raw + redeem − idle", LABEL, Palette.FAINT).next_to(val, RIGHT, buff=0.35).set_y(Y_ROWS[3])
        self.play(FadeIn(lbl, run_time=0.35))
        self.play(FadeIn(val, shift=UP * 0.1, run_time=0.6), FadeIn(how, run_time=0.6))

        # the decisive line, in the contract's terms, and the first withdrawal's operands
        self.section(1, hold=1.5)
        formula = words("idle after  =  idle − floor(idle × shares / totalSupply)", SANS, Palette.TEXT)
        self.left(formula, X_LEFT, Y_FORMULA)
        where = digits(f"{n['cite_file']}:{n['cite_line']}", LABEL, Palette.FAINT).next_to(formula, RIGHT, buff=0.4).set_y(Y_FORMULA)
        self.play(FadeIn(formula, shift=RIGHT * 0.1, run_time=0.6), FadeIn(where, run_time=0.6))
        cite = digits(n["cite_text"], LABEL, Palette.FAINT)
        self.left(cite, X_LEFT, Y_CITE)
        self.play(FadeIn(cite, run_time=0.5))
        self.wait(1.0)
        operands = digits(f"{n['idle']} × {n['shares']} / {n['supply']}", 24, Palette.TEXT)
        self.left(operands, X_LEFT, Y_OPERANDS)
        self.play(AddTextLetterByLetter(operands, time_per_char=0.045))
        eq = self.left(digits("=", SIZE_BODY, Palette.MUTED), X_LEFT, Y_RESULT)
        quotient = digits(n["sub"], SIZE_BODY, Palette.EXACT).next_to(eq, RIGHT, buff=0.3).set_y(Y_RESULT)
        q_lbl = words(n["sub_label"], LABEL, Palette.FAINT).next_to(quotient, RIGHT, buff=0.25).set_y(Y_RESULT)
        self.play(FadeIn(eq, run_time=0.3))
        self.play(AddTextLetterByLetter(quotient, time_per_char=0.12))
        self.play(FadeIn(q_lbl, run_time=0.4))

        # the floor, on the wei grid
        self.section(2, hold=2.0)
        d = _load("scripts/replays/bunni.json")
        x_exact = float(Fraction(int(d["start"]["idle"]) * int(d["steps"]["shares"][0]), int(d["start"]["totalSupply"])))
        dot = line.dot_at(x_exact, Palette.EXACT)
        dot.move_to(line.n2p(x_exact) + UP * 1.0)
        exact_lbl = VGroup(digits(n["sub"], SMALL, Palette.EXACT), words(n["sub_label"], LABEL, Palette.FAINT))
        exact_lbl[1].next_to(exact_lbl[0], RIGHT, buff=0.2)
        exact_lbl.next_to(line.n2p(x_exact), UP, buff=0.3).align_to(line.n2p(x_exact) + RIGHT * 0.15, LEFT)
        self.play(FadeIn(dot, run_time=0.3))
        self.play(dot.animate(rate_func=ease_out_cubic).move_to(line.n2p(x_exact)), run_time=0.8)
        self.play(FadeIn(exact_lbl, run_time=0.4))
        self.wait(0.6)
        arrow = direction(line, x_exact, float(n["floor"]), Palette.WRONG, lift=0.26)
        floor_lbl = words("floor on the subtrahend", SMALL, Palette.WRONG).next_to(arrow, UP, buff=0.08)
        self.play(Create(arrow, run_time=0.6), FadeIn(floor_lbl, run_time=0.4))
        self.play(snap(dot, line, float(n["floor"]), Palette.WRONG, run_time=1.0))
        floor_word = words("floor", SANS, Palette.WRONG).next_to(q_lbl, RIGHT, buff=0.6).set_y(Y_RESULT)
        floor_val = digits(n["floor"], SIZE_BODY, Palette.WRONG).next_to(floor_word, RIGHT, buff=0.3).set_y(Y_RESULT)
        self.play(FadeIn(floor_word, run_time=0.4), FadeIn(floor_val, shift=DOWN * 0.1, run_time=0.5))
        kept = self.left(markup(f"idle keeps <span foreground='{Palette.WRONG}'>{n['kept']} wei</span> too many", SMALL, Palette.TEXT), X_RIGHT, Y_GRID + 0.42)
        low = self.left(markup(f"active USDC reads <span foreground='{Palette.WRONG}'>{n['kept']} wei</span> low", SMALL, Palette.TEXT), X_RIGHT, Y_GRID + 0.04)
        after = self.left(words(f"stored idle after: {n['idle_after']} (on chain)", LABEL, Palette.FAINT), X_RIGHT, Y_GRID - 0.32)
        self.play(FadeIn(kept, shift=RIGHT * 0.1, run_time=0.5))
        self.play(FadeIn(low, shift=RIGHT * 0.1, run_time=0.5))
        self.play(FadeIn(after, run_time=0.4))

        # forty-four of them: the counter ticks, the bars drain
        self.section(3, hold=2.0)
        tracker = ValueTracker(0)
        counter = self.ticking(tracker, n["withdrawals"], [X_RIGHT, Y_COUNTER, 0])
        active = n["active"]
        fill1 = self.fill(bar1[0], tracker, lambda k: Fraction(active[k], active[0]))
        liq = bunni_liquidity()["steps"]  # the module's per-step liquidity, drawn as a share of its start
        fill2 = self.fill(bar2[0], tracker, lambda k: Fraction(liq[k], liq[0]))
        self.add(fill1, fill2)
        self.play(FadeIn(counter, run_time=0.4))
        self.play(tracker.animate.set_value(n["withdrawals"]), run_time=9.0, rate_func=linear)
        final = digits(f"withdrawal {n['withdrawals']} of {n['withdrawals']}", SIZE_BODY, HUE).move_to(counter).align_to([X_RIGHT, 0, 0], LEFT)
        self.remove(counter)
        self.add(final)
        end1 = digits(f"{n['active_end']} wei", LABEL, HUE).next_to(bar1[0], RIGHT, buff=0.2)
        end2 = digits(n["liq_pct"], LABEL, HUE).next_to(bar2[0], RIGHT, buff=0.2)
        self.play(FadeIn(end1, shift=LEFT * 0.1, run_time=0.5), FadeIn(end2, shift=LEFT * 0.1, run_time=0.5))
        liq_end = digits(n["liq_end"], LABEL, HUE).next_to(bar2[0], DOWN, buff=0.08).align_to(bar2[0], LEFT)
        self.play(FadeIn(liq_end, run_time=0.4))

        # the take
        self.section(4, hold=2.0)
        loss = self.left(words(n["loss"], SIZE_HERO, HUE), X_RIGHT, Y_TAKE)
        why = VGroup(words("a swap pair against", LABEL, Palette.MUTED), words("the now mispriced pool", LABEL, Palette.MUTED))
        why[1].next_to(why[0], DOWN, buff=0.08).align_to(why[0], LEFT)
        why.next_to(loss, RIGHT, buff=0.4).set_y(Y_TAKE)
        self.play(FadeIn(loss, shift=UP * 0.1, run_time=0.7))
        self.play(FadeIn(why, run_time=0.5))

        # the same 44 withdrawals, the idle balance held exact: replayed, not observed
        self.section(5, hold=2.5)
        head = words(f"active USDC after the same {n['withdrawals']} · replayed, not observed", LABEL, Palette.FAINT).move_to([0, Y_EXACT[0] + 0.3, 0]).align_to([X_EDGE, 0, 0], RIGHT)
        self.play(FadeIn(head, run_time=0.4))
        up_lbl = self.left(words("mulDivUp", SANS, Palette.MUTED), X_LEFT, Y_EXACT[0])
        up_val = digits(f"{n['up']} wei", MONO, Palette.MUTED).next_to(up_lbl, RIGHT, buff=0.4).set_y(Y_EXACT[0])
        up_liq = words(f"total liquidity {n['fix_pct']} in all three", SMALL, Palette.MUTED).next_to(up_val, RIGHT, buff=0.5).set_y(Y_EXACT[0])
        self.play(FadeIn(up_lbl, run_time=0.4), FadeIn(up_val, shift=RIGHT * 0.1, run_time=0.5))
        self.play(FadeIn(up_liq, run_time=0.4))
        rows = []
        for (lib, key), y in zip((("FP127", "fp127"), ("FP19", "fp19")), Y_EXACT[1:]):
            lbl = self.left(words(lib, SANS, Palette.CORRECT), X_LEFT, y)
            val = digits(n[key], SMALL, Palette.CORRECT).next_to(lbl, RIGHT, buff=0.4).set_y(y)
            fmt = words(n["word_label"], LABEL, Palette.FAINT).next_to(val, RIGHT, buff=0.25).set_y(y)
            rows.append(VGroup(lbl, val, fmt))
        hero = VGroup(*rows)
        glow = glow_bar(hero, Palette.CORRECT, pad=0.08)
        self.add(glow)
        self.play(FadeIn(glow, run_time=0.5))
        for row in rows:
            self.play(FadeIn(row[0], run_time=0.3), AddTextLetterByLetter(row[1], time_per_char=0.02), FadeIn(row[2], run_time=0.3))
        stops = VGroup(check_mark(Palette.CORRECT), words("the attack stops", SMALL, Palette.CORRECT))
        stops[1].next_to(stops[0], RIGHT, buff=0.25)
        stops.next_to(up_liq, RIGHT, buff=0.6).set_y(Y_EXACT[0])
        self.play(Create(stops[0], run_time=0.5), FadeIn(stops[1], run_time=0.4))
        self.close()

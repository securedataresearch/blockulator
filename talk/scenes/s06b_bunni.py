"""Slide 6b, "Bunni v2, 2 Sep 2025": forty-four floors, replayed.

The edit pass's replay shape (talk/briefs/edit-pass.md, row 7; the model
is s06c): one idea per section, each section owns the frame, the poster
holds the conclusion.

The idle balance the attacker found (316,691,975,954 USDC wei) is the one
object. BunniHubLogic.sol:478 takes floor(idle × shares / totalSupply)
off it on every withdrawal; the first withdrawal's subtrahend is 23.659
(to 3 decimals), and the floor keeps 23 (WRONG, red, on the subtrahend),
so the idle balance keeps 0.659 wei too many (the chain's idle balance
fell by exactly 23). Then a counter runs through the 44 withdrawals, one
red dot each, while active USDC (balance − idle) falls 28 → 4 wei as one
number changing (bunni_replay(), the deployed per-step active balance;
its ends are the chain's own reads). The take is $8.4M (incidents.json).
The poster: the same step with the idle balance in BL127 / BL19, the
subtrahend kept where it is (emerald, halo; BL127's 2^-128 grid keeps
23.659 to 3 decimals), and one line: the idle balance is rounded up once,
before queryLDF, instead of 44 times, and the total liquidity moves
−0.0000009% instead of −84.37% (the replay's own table, through
replay_table, cross-checked against bunni_liquidity() here): the attack
would stop. Replayed, not observed (the slide's notes).

Six sections, one per click: before, step, round, repeat, take, exact.
Provenance (tx, block, the Solidity line) is in the slide's notes.

Numbers from scripts/replays/bunni.json (.start, .steps, .snapshots)
through bunni_replay() and bunni_liquidity(); the loss and date from
talk/scenes/data/incidents.json. Every derived value is computed here
with Fraction.
"""

from __future__ import annotations

from fractions import Fraction

from manim import (
    DOWN,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    RoundedRectangle,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_in_out_cubic, ease_out_cubic

from vocab import (
    PROTOCOL_COLOUR,
    SIZE_BODY,
    SIZE_HERO,
    DeckScene,
    GridLine,
    Palette,
    _load,
    bunni_liquidity,
    bunni_replay,
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
    to_decimals,
    words,
)

SUB_DECIMALS = 3  # the first withdrawal's subtrahend, complete to this many decimals
TABLE_HEADING = "Same 44 withdrawals, idle balance held differently"
HUE = PROTOCOL_COLOUR["bunni"]  # GOLD, everywhere in the deck
SIZE_TAKE = 72  # the loss, alone on its frame (edit-pass: a lone hero number at 64–72)
SIZE_COUNT = 64  # the repetition counter

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
    L_end = int(d["observed"]["afterWithdrawals"]["totalLiquidity"])
    assert lq["steps"][-1] == L_end == lq["forms"]["deployed"]
    # the poster's line: with the idle balance in BL127 / BL19 the liquidity is the exact one, and it barely moves
    assert lq["forms"]["bl127"] == lq["forms"]["exact"] and lq["forms"]["exact"] < lq["start"]
    assert abs(r["seq"]["bl127"][-1] - r["seq"]["exact"][-1]) < Fraction(n, 1 << 128)
    table = {row["idle balance"]: row for row in replay_table("bunni", TABLE_HEADING)}
    for lib in ("BL127", "BL19"):
        row = table[f"{lib} idle balance"]
        assert int(row["total liquidity after"]) == lq["forms"]["exact"] and row["change"] == table["exact rational"]["change"], row
    return {
        "title": f"{inc['protocol']}, {inc['date']}",
        "idle": thousands(idle0),
        "sub": to_decimals(sub, SUB_DECIMALS),
        "sub_label": f"(to {SUB_DECIMALS} decimals)",
        "floor": str(floor),
        "kept": to_decimals(sub - floor, SUB_DECIMALS),
        "grid_ticks": [floor, floor + 1],
        "withdrawals": n,
        "counter_ticks": list(range(1, n + 1)),
        "active": active,
        "active_start": active[0],
        "active_end": active[-1],
        "loss": inc["loss"],
    }


class Bunni(DeckScene):
    SECTIONS = ("before", "step", "round", "repeat", "take", "exact")

    Y_OPERANDS, Y_SUB, Y_LINE = 2.05, 1.15, -0.45
    LINE_LEN, LINE_X = 7.6, -1.0

    def lattice(self, n):
        """The wei grid with its tick numbers and its name: built fresh for each beat that uses it."""
        g0, g1 = n["grid_ticks"]
        line = GridLine((g0, g1, 1), length=self.LINE_LEN, tick_size=0.16).move_to([self.LINE_X, self.Y_LINE, 0])
        ticks = VGroup(*[digits(str(k), SIZE_BODY, Palette.FAINT).next_to(line.n2p(k), DOWN, buff=0.28) for k in n["grid_ticks"]])
        name = words("USDC, in wei", SIZE_BODY, Palette.MUTED).next_to(line.get_end(), RIGHT, buff=0.45)
        return line, ticks, name

    def sub_row(self, n):
        sub = digits(n["sub"], SIZE_HERO, Palette.EXACT)
        stated = words(n["sub_label"], SIZE_BODY, Palette.MUTED)
        row = VGroup(sub, stated).arrange(RIGHT, buff=0.35, aligned_edge=DOWN).move_to([0, self.Y_SUB, 0])
        return sub, stated, row

    def construct(self):
        n = numbers()
        x_exact = float(Fraction(n["sub"]))  # 23.659: the dot's place; the 3-decimal string is within half a unit of it, far below a pixel
        x_floor = float(n["floor"])

        # chrome: the title, on the first frame
        self.section(0)
        self.fix(self.title(n["title"]))
        self.wait(0.3)

        # before: the idle balance, the one object the withdrawals take from
        tank = RoundedRectangle(width=7.4, height=1.5, corner_radius=0.25, color=HUE, stroke_width=3).move_to([0, 0.35, 0])
        level = RoundedRectangle(width=7.0, height=1.1, corner_radius=0.18, color=HUE, fill_color=HUE, fill_opacity=0.35, stroke_width=0).move_to(tank)
        name = words("idle balance", SIZE_BODY, HUE).next_to(tank, UP, buff=0.3)
        value = VGroup(digits(n["idle"], SIZE_HERO, Palette.TEXT), words("USDC-wei", SIZE_BODY, Palette.MUTED)).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
        value.next_to(tank, DOWN, buff=0.4)
        self.play(Create(tank, run_time=0.8), FadeIn(name, run_time=0.6))
        self.play(FadeIn(level, run_time=0.8), AddTextLetterByLetter(value[0], time_per_char=0.05))
        self.play(FadeIn(value[1], run_time=0.4))
        self.wait(1.0)

        # step: the first withdrawal's subtrahend, idle × shares / totalSupply, on the wei grid
        self.section(1, hold=2.0)
        line, ticks, axis = self.lattice(n)
        operands = words("idle × shares / totalSupply", SIZE_BODY, Palette.TEXT).move_to([0, self.Y_OPERANDS, 0])
        self.play(FadeOut(VGroup(tank, level, name, value), run_time=0.6), Create(line, run_time=1.0), FadeIn(ticks, run_time=0.8), FadeIn(axis, run_time=0.8))
        self.play(FadeIn(operands, shift=DOWN * 0.1, run_time=0.6))
        self.wait(0.4)
        sub, stated, _ = self.sub_row(n)
        dot = line.dot_at(x_exact, Palette.EXACT).shift(UP * 1.0)
        self.play(AddTextLetterByLetter(sub, time_per_char=0.1))
        self.play(FadeIn(stated, run_time=0.4), FadeIn(dot, run_time=0.3))
        self.play(dot.animate(rate_func=ease_out_cubic, run_time=0.9).move_to(line.n2p(x_exact)))
        self.wait(0.8)

        # round: the floor on the subtrahend; the idle balance keeps the rest
        self.section(2, hold=2.0)
        self.play(FadeOut(operands, run_time=0.5))
        arrow = direction(line, x_exact, x_floor, Palette.WRONG, lift=0.38)
        floor_lbl = words("floor", SIZE_BODY, Palette.WRONG).next_to(arrow, UP, buff=0.15)
        kept = dot.copy()
        self.add(kept)
        self.play(Create(arrow, run_time=0.6), FadeIn(floor_lbl, run_time=0.5))
        self.play(snap(kept, line, x_floor, Palette.WRONG, run_time=1.2))
        self.wait(0.8)
        keeps = words(f"idle keeps {n['kept']} wei too many", SIZE_BODY, Palette.WRONG)
        keeps_row = VGroup(cross_mark(Palette.WRONG), keeps).arrange(RIGHT, buff=0.3).move_to([0, -2.35, 0])
        self.play(Create(keeps_row[0], run_time=0.4), FadeIn(keeps, shift=UP * 0.1, run_time=0.6))

        # repeat: 44 withdrawals, one red dot each; active USDC, one number, falls with them
        self.section(3, hold=2.0)
        cols = 11
        rows = -(-n["withdrawals"] // cols)
        reps = VGroup(*[Dot(radius=0.13, color=Palette.WRONG) for _ in range(n["withdrawals"])]).arrange_in_grid(rows=rows, cols=cols, buff=0.36).move_to([0, 1.25, 0])
        self.play(FadeOut(VGroup(line, ticks, axis, dot, arrow, floor_lbl, sub, stated, keeps_row), run_time=0.6), kept.animate(run_time=0.9).move_to(reps[0]))
        self.remove(kept)
        self.add(reps[0])
        y_count, y_active = -0.85, -2.2
        widest = digits(f"× {n['withdrawals']}", SIZE_COUNT, HUE)  # each row is laid out for its widest value; each value keeps its right edge
        tail = words("withdrawals", SIZE_BODY, Palette.MUTED)
        VGroup(widest, tail).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).move_to([0, y_count, 0])
        counter = digits(f"× {n['counter_ticks'][0]}", SIZE_COUNT, HUE).move_to(widest, aligned_edge=RIGHT)
        a_name = words("active USDC", SIZE_BODY, Palette.MUTED)
        a_widest = digits(str(max(n["active"])), SIZE_HERO, Palette.TEXT)
        a_unit = words("wei", SIZE_BODY, Palette.MUTED)
        VGroup(a_name, a_widest, a_unit).arrange(RIGHT, buff=0.35, aligned_edge=DOWN).move_to([0, y_active, 0])
        amount = digits(str(n["active"][1]), SIZE_HERO, Palette.TEXT).move_to(a_widest, aligned_edge=RIGHT)
        start = digits(str(n["active_start"]), SIZE_HERO, Palette.TEXT).move_to(a_widest, aligned_edge=RIGHT)
        self.play(FadeIn(VGroup(a_name, start, a_unit), run_time=0.5))
        self.wait(0.4)
        self.play(FadeIn(counter, run_time=0.3), FadeIn(tail, run_time=0.3), Transform(start, amount, run_time=0.3))
        for k in n["counter_ticks"][1:]:
            nxt = digits(f"× {k}", SIZE_COUNT, HUE).move_to(widest, aligned_edge=RIGHT)
            now = digits(str(n["active"][k]), SIZE_HERO, Palette.TEXT).move_to(a_widest, aligned_edge=RIGHT)
            self.play(Transform(counter, nxt), Transform(start, now), FadeIn(reps[k - 1], scale=1.6), run_time=0.12)
        self.wait(0.3)

        # take: what the 44 floors were worth, alone
        self.section(4, hold=2.0)
        loss = words(n["loss"], SIZE_TAKE, HUE).move_to([0, 0.1, 0])
        self.play(FadeOut(VGroup(counter, tail, a_name, start, a_unit), run_time=0.5), reps.animate(run_time=0.9, rate_func=ease_in_out_cubic).scale(0.05).move_to(loss))
        self.remove(reps)
        self.play(FadeIn(loss, scale=0.6, run_time=0.7))
        self.wait(1.0)

        # exact: the same step with the idle balance in BL127 / BL19: the subtrahend kept, rounded once at the end
        self.section(5, hold=2.5)
        line, ticks, axis = self.lattice(n)
        sub, stated, row = self.sub_row(n)
        self.play(FadeOut(loss, run_time=0.5), Create(line, run_time=0.9), FadeIn(ticks, run_time=0.7), FadeIn(axis, run_time=0.7))
        low = line.dot_at(x_floor, Palette.WRONG)
        self.play(FadeIn(low, scale=0.5, run_time=0.4), FadeIn(row, run_time=0.6))
        self.wait(0.4)
        glow = halo(line.n2p(x_exact), Palette.CORRECT)
        self.play(low.animate(rate_func=ease_out_cubic, run_time=1.2).move_to(line.n2p(x_exact)).set_color(Palette.CORRECT))
        self.play(FadeIn(glow, run_time=0.6))
        self.bring_to_front(low)
        verdict = words("BL127 / BL19: ceil once · the attack would stop", SIZE_BODY, Palette.CORRECT)
        tick = check_mark(Palette.CORRECT)
        verdict_row = VGroup(verdict, tick).arrange(RIGHT, buff=0.35).move_to([0, -2.35, 0])
        panel = glow_bar(verdict_row, Palette.CORRECT, pad=0.18)
        self.play(FadeIn(panel, run_time=0.5), FadeIn(verdict, shift=UP * 0.1, run_time=0.7))
        self.play(Create(tick, run_time=0.5))
        self.close()

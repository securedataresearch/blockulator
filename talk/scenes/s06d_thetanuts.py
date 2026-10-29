"""Slide 6d, "Thetanuts, 15 Jun 2026": thirty-seven floors of a fraction of a unit.

The vault's source is unverified, so the replay is pinned to bytecode
(scripts/replays/thetanuts.json: the MUL at pc 12186 and the DIV at pc
12220 that both `claim` and `mint` run). Before: the index supply
153,054,600,572; the attacker flash-borrows all but 3, and one `claim`
drains each component's stored amount to 1 raw unit (five bars drain).
Step: charge = stored × amount / supply; the first mint types in
1 × 2 / 3 = 0.666666 (to 6 decimals). Round: on the raw-unit grid the
dot at two thirds snaps to 0 (WRONG, red): a transfer moves whole units
and EVM DIV floors. Repeat: a counter ticks through the 37 mints, the
amounts doubling 2, 4, 8 … 2^36 then 15,753,396,239, every charge 0,
while the supply bar grows from 3 to 153,192,349,712; the 153,192,349,709
minted repay the loan and its fee. Take: $105,000 (incidents.json),
105,471.499078 USDC realised plus three component-vault tokens. Exact:
the same 37 amounts with the charge rounded up (computed off-chain, C8):
1 raw unit on every mint, 76,596.174855 tokens per component, more than
the claim took of any one; BL127 and BL19 keep the two thirds, and the
direction decides: floor 0, ceil 1.

Six sections, one per click: before, step, round, repeat, take, exact.

Numbers from scripts/replays/thetanuts.json: .pre.totalSupply,
.flashLoan.amount/.premium, .claim (supplyAfter, storedBefore, payout,
storedAfter), .components (symbols), .mints[] (amount, supplyBefore,
supplyAfter, storedBefore, charge), .post.totalSupply, .realised
(usdcTotal, sentToBeneficiary), .trace.pcMul/.pcDiv/.transferFromCalls,
.tx, .block; the date and the loss line from talk/scenes/data/
incidents.json. The exact charge is a Fraction of the first mint's
operands; the ceil total is the 37 mints rerun here with the charge
rounded up (docs/benchmarks/replay-thetanuts.md's "The decisive step on
each rule" table holds the same 76,596,174,855; check.py compares).
Token amounts are shown in whole tokens at the components' 6 decimals
(.components[].decimals); USDC's 6 decimals are USDC_DECIMALS below.
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
    FadeOut,
    Rectangle,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    SIZE_BODY,
    SIZE_CAPTION,
    DeckScene,
    GridLine,
    Palette,
    check_mark,
    cross_mark,
    digits,
    direction,
    glow_bar,
    incidents,
    markup,
    snap,
    thetanuts,
    thousands,
    to_decimals,
    words,
)

CHARGE_DECIMALS = 6  # decimals of the first mint's exact charge, complete and labelled
USDC_DECIMALS = 6  # USDC's decimals (not in the JSON; the replay page writes 105,471.499078 USDC)
GRID = (0, 2, 1)  # the raw-unit grid a transfer moves on
INCIDENT = "Thetanuts"
MONO = 28
SANS = SIZE_BODY - 6
SMALL = 16  # the bytecode citation
ROW = 22  # the bottom rows
LEFT_X = -6.3  # the left column's edge
RIGHT_X = 2.2  # the right column's edge (the repeat block)
COMP_X = 1.4  # the components block's edge
HUE = Palette.SLATE  # Thetanuts' hue in the deck: its name, its bars, its counter

LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers()


def stated(places: int) -> str:
    return f"(to {places} decimals)"


def tokens(raw: int | str, decimals: int) -> str:
    """A raw ERC-20 amount as whole tokens with every one of its decimals."""
    whole, frac = divmod(int(raw), 10**decimals)
    return f"{thousands(whole)}.{frac:0{decimals}d}"


def short_symbol(symbol: str) -> str:
    """"TN-CSCPv1-BTCUSD" → "BTCUSD", the name the replay page uses."""
    return symbol.rsplit("-", 1)[-1]


def ceil_replay(mints: list[dict], stored: int, supply: int) -> tuple[list[int], int, int]:
    """The 37 mints from the post-claim state with each charge rounded up
    (the counterfactual of C8): per-mint charges, the stored amount and
    the supply at the end. One column covers all five components: they
    all start at the same stored amount."""
    charges = []
    for m in mints:
        a = int(m["amount"])
        c = -(-stored * a // supply)  # ceil
        charges.append(c)
        stored += c
        supply += a
    return charges, stored, supply


def numbers() -> dict:
    d = thetanuts()
    inc = next(i for i in incidents()["incidents"] if i["protocol"] == INCIDENT)
    pre, post, claim, mints, fl, tr = d["pre"], d["post"], d["claim"], d["mints"], d["flashLoan"], d["trace"]
    comps = d["components"]
    (dec,) = {int(c["decimals"]) for c in comps}
    supply_before, borrowed = int(pre["totalSupply"]), int(fl["amount"])
    supply_after_claim = int(claim["supplyAfter"])
    assert supply_before - borrowed == supply_after_claim == int(mints[0]["supplyBefore"])
    (stored_after,) = {int(s) for s in claim["storedAfter"]}
    assert all(int(s) == stored_after for s in mints[0]["storedBefore"])
    # the first mint: charge = stored × amount / supply, exact, then floored as the chain did
    m0 = mints[0]
    amount0, supply0 = int(m0["amount"]), int(m0["supplyBefore"])
    charge0 = Fraction(stored_after * amount0, supply0)
    floor0 = stored_after * amount0 // supply0
    assert all(int(c) == floor0 for c in m0["charge"])
    # every mint: the amounts, the supply before each, every charge
    amounts = [int(m["amount"]) for m in mints]
    supplies = [int(m["supplyBefore"]) for m in mints]
    charges = sorted({int(c) for m in mints for c in m["charge"]})
    assert charges == [floor0] and all(int(m["supplyAfter"]) == int(m["supplyBefore"]) + int(m["amount"]) for m in mints)
    assert supplies[0] == supply_after_claim and int(mints[-1]["supplyAfter"]) == int(post["totalSupply"])
    minted = sum(amounts)
    assert minted == int(post["totalSupply"]) - supply_after_claim
    loan_fee = borrowed + int(fl["premium"])
    # the counterfactual: the same amounts, the charge rounded up
    ceil_charges, _, _ = ceil_replay(mints, stored_after, supply_after_claim)
    ceil_total = sum(ceil_charges)
    max_take = max(int(p) for p in claim["payout"])
    # the take: USDC realised and the component-vault tokens that left as tokens
    by_addr = {c["address"].lower(): c for c in comps}
    leftovers = [(tokens(v, dec), short_symbol(by_addr[a.lower()]["symbol"])) for a, v in d["realised"]["sentToBeneficiary"].items() if a.lower() in by_addr]
    return {
        "protocol": inc["protocol"],
        "date": inc["date"],
        "vault_name": d["vault"]["name"],
        "tx_short": d["tx"][:10],
        "block": thousands(d["block"]),
        "supply_before": thousands(supply_before),
        "borrowed": thousands(borrowed),
        "supply_after_claim": str(supply_after_claim),
        "stored_after": str(stored_after),
        "n_components": len(comps),
        "components": [
            {"label": short_symbol(c["symbol"]), "stored_before": thousands(s), "payout": thousands(p), "stored_after": str(a)}
            for c, s, p, a in zip(comps, claim["storedBefore"], claim["payout"], claim["storedAfter"])
        ],
        "pc_mul": tr["pcMul"],
        "pc_div": tr["pcDiv"],
        "amount0": str(amount0),
        "supply0": str(supply0),
        "charge0": to_decimals(charge0, CHARGE_DECIMALS),
        "charge0_label": stated(CHARGE_DECIMALS),
        "charge0_x": charge0,
        "floor0": str(floor0),
        "ceil0": str(ceil_charges[0]),
        "grid_ticks": list(range(GRID[0], GRID[1] + 1)),
        "n_mints": len(mints),
        "mint_index": list(range(1, len(mints) + 1)),
        "amounts": [thousands(a) for a in amounts],
        "supplies": [thousands(s) for s in supplies],
        "supply_after": thousands(post["totalSupply"]),
        "minted": thousands(minted),
        "loan_fee": thousands(loan_fee),
        "zero_transfers": len(mints) * len(comps),
        "loss": inc["loss"],
        "usdc": tokens(d["realised"]["usdcTotal"], USDC_DECIMALS),
        "leftovers": leftovers,
        "ceil_total_raw": thousands(ceil_total),
        "ceil_total": tokens(ceil_total, dec),
        "max_take": tokens(max_take, dec),
        "repaid": minted == loan_fee,
        "ceil_wins": ceil_total > max_take,
    }


def _bar(x0: float, y: float, width: float, height: float, colour: str, opacity: float = 0.85) -> Rectangle:
    """A quantity as a bar growing rightwards from x0 (width never drawn below a hairline)."""
    w = max(width, 0.02)
    return Rectangle(width=w, height=height, color=colour, fill_color=colour, fill_opacity=opacity, stroke_width=0).move_to([x0 + w / 2, y, 0])


class Thetanuts(DeckScene):
    SECTIONS = ("before", "step", "round", "repeat", "take", "exact")

    def construct(self):
        n = numbers()
        assert n["repaid"] and n["ceil_wins"]
        self.section(0)

        # chrome, on the first frame: the title, the caption, the grid's axis labels
        title = markup(f"<span foreground='{HUE}'>{n['protocol']}</span>, {n['date']}", SIZE_BODY, Palette.TEXT)
        title.move_to([LEFT_X + title.width / 2, 3.35, 0])
        subtitle = words(f"{n['vault_name']} · Ethereum", SIZE_CAPTION, Palette.MUTED).next_to(title, RIGHT, buff=0.5).set_y(3.33)
        caption = words(f"scripts/replays/thetanuts.json · tx {n['tx_short']} · block {n['block']}", SIZE_CAPTION, Palette.FAINT).to_corner(DOWN + LEFT, buff=0.45)
        y_grid = -0.2
        line = GridLine(GRID, length=5.0, tick_size=0.14).move_to([-3.5, y_grid, 0])
        tick_lbls = VGroup(*[digits(str(k), SIZE_CAPTION, Palette.FAINT).next_to(line.n2p(k), DOWN, buff=0.2) for k in n["grid_ticks"]])
        grid_lbl = words("raw units of a component", SIZE_CAPTION, Palette.FAINT).next_to(tick_lbls, DOWN, buff=0.12).align_to(line.n2p(0), LEFT)
        self.add(title, subtitle, caption, line, tick_lbls, grid_lbl)
        self.wait(0.3)

        # --- before: the index supply, the loan, the claim that leaves 3 and drains each component to 1
        rows_y = (2.82, 2.46, 2.1)

        def row(label: str, value: str, y: float, colour: str = Palette.TEXT, size: float = MONO) -> tuple:
            lbl = words(label, SANS, Palette.MUTED)
            lbl.move_to([LEFT_X + lbl.width / 2, y, 0])
            val = digits(value, size, colour).next_to(lbl, RIGHT, buff=0.4).set_y(y)
            return lbl, val

        s_lbl, s_val = row("index supply", n["supply_before"], rows_y[0])
        self.play(FadeIn(s_lbl, run_time=0.4))
        self.play(AddTextLetterByLetter(s_val, time_per_char=0.05))
        # the five components, stored before the claim, as bars
        comp_rows = VGroup()
        bars, vals = [], []
        bar_x0 = COMP_X + 1.55
        bar_w = 0.9
        biggest = max(int(c["stored_before"].replace(",", "")) for c in n["components"])
        for i, c in enumerate(n["components"]):
            y = 2.62 - 0.3 * i
            lbl = words(c["label"], SIZE_CAPTION, HUE)
            lbl.move_to([COMP_X + lbl.width / 2, y, 0])
            raw = int(c["stored_before"].replace(",", ""))
            bar = _bar(bar_x0, y, bar_w * raw / biggest, 0.18, HUE)
            val = digits(c["stored_before"], SIZE_CAPTION, Palette.TEXT).next_to(bar, RIGHT, buff=0.15).set_y(y)
            comp_rows.add(lbl)
            bars.append(bar)
            vals.append(val)
        stored_lbl = words("stored per component, before", SIZE_CAPTION, Palette.MUTED)
        stored_lbl.move_to([COMP_X + stored_lbl.width / 2, 2.95, 0])
        self.play(FadeIn(stored_lbl, run_time=0.4), FadeIn(comp_rows, run_time=0.5))
        self.play(*[Create(b, run_time=0.7) for b in bars], *[FadeIn(v, run_time=0.5) for v in vals])
        self.wait(0.8)
        b_lbl, b_val = row("flash-borrowed", n["borrowed"], rows_y[1])
        self.play(FadeIn(b_lbl, run_time=0.4))
        self.play(AddTextLetterByLetter(b_val, time_per_char=0.05))
        self.wait(0.5)
        c_lbl, c_val = row("one claim leaves supply", n["supply_after_claim"], rows_y[2], HUE)
        self.play(FadeIn(c_lbl, run_time=0.4), FadeIn(c_val, shift=DOWN * 0.1, run_time=0.5))
        # the claim drains every component's stored amount to 1 raw unit
        drained_bars = [_bar(bar_x0, b.get_y(), 0.0, 0.18, HUE) for b in bars]
        drained_vals = [digits(c["stored_after"], SIZE_CAPTION, Palette.TEXT).next_to(db, RIGHT, buff=0.15).set_y(db.get_y()) for c, db in zip(n["components"], drained_bars)]
        self.play(
            *[Transform(b, db, run_time=1.4, rate_func=ease_out_cubic) for b, db in zip(bars, drained_bars)],
            *[Transform(v, dv, run_time=1.4) for v, dv in zip(vals, drained_vals)],
        )
        left = words(f"{n['stored_after']} raw unit of each of {n['n_components']} components", ROW, Palette.TEXT)
        left.move_to([LEFT_X + left.width / 2, rows_y[2] - 0.36, 0])
        self.play(FadeIn(left, run_time=0.5))
        self.wait(0.5)

        # --- step: the decisive formula in the bytecode's terms, the first mint typed in
        self.section(1, hold=1.5)
        y_f = 1.38
        formula = markup("charge  =  stored × amount / supply", SANS, Palette.TEXT)
        formula.move_to([LEFT_X + formula.width / 2, y_f, 0])
        cite = digits(f"bytecode, not source: MUL at pc {n['pc_mul']}, DIV at pc {n['pc_div']}", SMALL, Palette.FAINT)
        cite.move_to([LEFT_X + cite.width / 2, y_f - 0.33, 0])
        self.play(FadeIn(formula, shift=RIGHT * 0.1, run_time=0.6))
        self.play(FadeIn(cite, run_time=0.5))
        self.wait(1.2)
        y_op = 0.62
        op_lbl = words("first mint", SANS, Palette.MUTED)
        op_lbl.move_to([LEFT_X + op_lbl.width / 2, y_op, 0])
        operands = digits(f"{n['stored_after']} × {n['amount0']} / {n['supply0']}", MONO, Palette.TEXT).next_to(op_lbl, RIGHT, buff=0.35).set_y(y_op)
        eq = digits("=", MONO, Palette.MUTED).next_to(operands, RIGHT, buff=0.25).set_y(y_op)
        exact = digits(n["charge0"], MONO, Palette.EXACT).next_to(eq, RIGHT, buff=0.25).set_y(y_op)
        exact_lbl = words(n["charge0_label"], SIZE_CAPTION, Palette.FAINT).next_to(exact, RIGHT, buff=0.25).set_y(y_op)
        self.play(FadeIn(op_lbl, run_time=0.4))
        self.play(AddTextLetterByLetter(operands, time_per_char=0.14))
        self.wait(0.6)
        self.play(FadeIn(eq, run_time=0.3))
        self.play(AddTextLetterByLetter(exact, time_per_char=0.18))
        self.play(FadeIn(exact_lbl, run_time=0.4))
        self.wait(1.0)

        # --- round: two thirds of a raw unit on the unit grid, floored to 0
        self.section(2, hold=1.5)
        x_exact = float(n["charge0_x"])
        dot = line.dot_at(x_exact, Palette.EXACT)
        dot.move_to(exact.get_center())
        dot_lbl = VGroup(digits(n["charge0"], SIZE_CAPTION, Palette.EXACT), words(n["charge0_label"], SIZE_CAPTION, Palette.FAINT)).arrange(RIGHT, buff=0.2)
        dot_lbl.next_to(line.n2p(x_exact), UP, buff=0.3).align_to(line.n2p(x_exact) + RIGHT * 0.15, LEFT)
        self.play(FadeIn(dot, run_time=0.3))
        self.play(dot.animate(rate_func=ease_out_cubic).move_to(line.n2p(x_exact)), run_time=0.9)
        self.play(FadeIn(dot_lbl, run_time=0.4))
        self.wait(1.0)
        arrow = direction(line, x_exact, float(n["floor0"]), Palette.WRONG, lift=0.3)
        floor_lbl = words("floor", SIZE_CAPTION, Palette.WRONG).next_to(arrow, UP, buff=0.06)
        self.play(Create(arrow, run_time=0.6), FadeIn(floor_lbl, run_time=0.4))
        self.play(snap(dot, line, float(n["floor0"]), Palette.WRONG, run_time=1.0), exact[1:].animate.set_color(Palette.FAINT))
        ch_lbl = words("charged", SANS, Palette.MUTED).next_to(line.get_end(), RIGHT, buff=0.45).set_y(y_grid)
        ch_val = digits(n["floor0"], MONO, Palette.WRONG).next_to(ch_lbl, RIGHT, buff=0.25).set_y(y_grid)
        ch_x = cross_mark(Palette.WRONG, size=0.26).next_to(ch_val, RIGHT, buff=0.25).set_y(y_grid)
        self.play(FadeIn(ch_lbl, run_time=0.4), FadeIn(ch_val, shift=DOWN * 0.1, run_time=0.5))
        self.play(Create(ch_x, run_time=0.4))
        why = words("whole units only; EVM DIV floors", SIZE_CAPTION, Palette.MUTED).next_to(grid_lbl, RIGHT, buff=0.5).set_y(grid_lbl.get_y())
        self.play(FadeIn(why, run_time=0.5))
        self.wait(1.0)

        # --- repeat: the 37 mints tick by, every charge 0, the supply grows back past the loan
        self.section(3, hold=1.5)
        y_c = 0.95
        val_x = RIGHT_X + 1.05
        amounts, supplies = n["amounts"], n["supplies"]
        final_supply = int(n["supply_after"].replace(",", ""))

        def labelled(label: str, value: str, y: float, colour: str) -> tuple:
            lbl = words(label, SIZE_CAPTION, Palette.MUTED)
            lbl.move_to([RIGHT_X + lbl.width / 2, y, 0])
            val = digits(value, SIZE_CAPTION, colour)
            val.move_to([val_x + val.width / 2, y, 0])
            return lbl, val

        def ticker(k: int) -> VGroup:
            idx = n["mint_index"][k]
            counter = digits(f"mint {idx} of {n['n_mints']}", ROW, HUE)
            counter.move_to([RIGHT_X + counter.width / 2, y_c, 0])
            a_l, a_v = labelled("amount", amounts[k], y_c - 0.4, Palette.TEXT)
            s_l, s_v = labelled("supply", supplies[k], y_c - 0.76, Palette.TEXT)
            c_l, c_v = labelled("charge", n["floor0"], y_c - 1.32, Palette.WRONG)
            c_x = cross_mark(Palette.WRONG, size=0.2).next_to(c_v, RIGHT, buff=0.25).set_y(y_c - 1.32)
            return VGroup(counter, a_l, a_v, s_l, s_v, c_l, c_v, c_x)

        # the supply bar under the supply row, from 3 towards the final supply
        bar_y = y_c - 1.0
        sup_w = 6.3 - val_x
        supply_bar = _bar(val_x, bar_y, 0.0, 0.12, HUE)
        # the amounts as a column of bars, one per mint, doubling (one bit taller each)
        amt_base = -1.2
        amt_h = 0.55
        amt_w = 0.085
        amt_gap = 0.111
        top_bits = max(int(a.replace(",", "")).bit_length() for a in amounts)
        amt_bars = []
        for k, a in enumerate(amounts):
            h = max(amt_h * int(a.replace(",", "")).bit_length() / top_bits, 0.02)
            amt_bars.append(Rectangle(width=amt_w, height=h, color=HUE, fill_color=HUE, fill_opacity=0.85, stroke_width=0).move_to([RIGHT_X + amt_w / 2 + k * amt_gap, amt_base + h / 2, 0]))
        amt_lbl = words("the amounts, doubling", SIZE_CAPTION, Palette.MUTED)
        amt_lbl.move_to([RIGHT_X + amt_lbl.width / 2, amt_base + amt_h - 0.1, 0])
        tk = ticker(0)
        self.play(FadeIn(tk, run_time=0.5), FadeIn(amt_lbl, run_time=0.5))
        self.add(supply_bar, amt_bars[0])
        self.wait(1.0)
        for k in range(1, len(amounts)):
            new = ticker(k)
            new_bar = _bar(val_x, bar_y, sup_w * int(supplies[k].replace(",", "")) / final_supply, 0.12, HUE)
            if k < 6:
                self.play(Transform(tk, new, run_time=0.4), Transform(supply_bar, new_bar, run_time=0.4), FadeIn(amt_bars[k], run_time=0.4))
            else:
                self.remove(tk)
                tk = new
                self.add(tk, amt_bars[k])
                supply_bar.become(new_bar)
                self.wait(0.14 if k < len(amounts) - 1 else 1.0)
        # the last mint lands: the supply is back past the loan, the minted total repays it and its fee
        end_bar = _bar(val_x, bar_y, sup_w, 0.12, HUE)
        s_l, s_v = labelled("supply", n["supply_after"], y_c - 0.76, Palette.TEXT)
        self.play(Transform(supply_bar, end_bar, run_time=0.6), Transform(tk[4], s_v, run_time=0.6))
        self.wait(0.5)
        minted = digits(f"minted {n['minted']}", ROW, HUE)
        minted.move_to([RIGHT_X + minted.width / 2, y_c, 0])
        repays = words("repays the loan and its fee", SIZE_CAPTION, Palette.TEXT)
        repays.move_to([RIGHT_X + repays.width / 2, y_c - 0.4, 0])
        self.play(Transform(tk[0], minted, run_time=0.6), FadeOut(tk[1], run_time=0.3), Transform(tk[2], repays, run_time=0.6))
        self.wait(0.4)

        # --- take: the loss line and what left
        self.section(4, hold=1.5)
        y_t = -1.45
        take = markup(f"the take  <span foreground='{HUE}'>{n['loss']}</span>  ·  {n['usdc']} USDC realised", SANS, Palette.TEXT)
        take.move_to([LEFT_X + take.width / 2, y_t, 0])
        rest = words("and the rest of the vault: " + " · ".join(f"{amt} {sym}" for amt, sym in n["leftovers"]), SIZE_CAPTION, Palette.MUTED)
        rest.move_to([LEFT_X + rest.width / 2, y_t - 0.37, 0])
        self.play(FadeIn(take, shift=RIGHT * 0.1, run_time=0.7))
        self.wait(0.5)
        self.play(FadeIn(rest, run_time=0.6))
        self.wait(1.2)

        # --- exact: the same 37 amounts, the charge rounded up; BL127 / BL19 keep the two thirds, the direction decides
        self.section(5, hold=1.5)
        y_e = -2.25
        r1 = markup(
            f"rounded up: {n['ceil0']} raw unit on every mint  ·  <span foreground='{Palette.CORRECT}'>{n['ceil_total']}</span> tokens per component",
            ROW + 2,
            Palette.TEXT,
        )
        r1.move_to([LEFT_X + r1.width / 2, y_e, 0])
        r2 = markup(f"more than the claim took of any one (at most {n['max_take']})", ROW, Palette.CORRECT)
        r2.move_to([LEFT_X + r2.width / 2, y_e - 0.35, 0])
        r2_note = words("computed off-chain, not observed", SIZE_CAPTION, Palette.FAINT).next_to(r2, RIGHT, buff=0.4).set_y(y_e - 0.35)
        r3 = markup(
            f"<span foreground='{Palette.EMERALD}'>BL127</span> / BL19 keep {n['charge0']}  ·  direction decides:  "
            f"<span foreground='{Palette.WRONG}'>floor {n['floor0']}</span>   <span foreground='{Palette.CORRECT}'>ceil {n['ceil0']}</span>",
            ROW,
            Palette.TEXT,
        )
        r3.move_to([LEFT_X + r3.width / 2, y_e - 0.7, 0])
        tick = check_mark(Palette.CORRECT).next_to(r1, RIGHT, buff=0.45).set_y(y_e)
        hero = glow_bar(VGroup(r1, r2, r3), Palette.EMERALD, pad=0.14)
        self.play(FadeIn(hero, run_time=0.5))
        self.play(FadeIn(r1, shift=RIGHT * 0.1, run_time=0.7))
        self.play(Create(tick, run_time=0.5))
        self.wait(0.4)
        self.play(FadeIn(r2, run_time=0.6), FadeIn(r2_note, run_time=0.6))
        self.wait(0.8)
        self.play(FadeIn(r3, shift=UP * 0.08, run_time=0.7))
        self.wait(0.5)
        self.close()

"""Slide 7, "Two failures, one decision": all five incidents, one row each.

Two bands. Band 1, "rounded too early, or too often": Resupply (one floor,
once), Bunni (the idle-balance subtrahend floored 44 times) and Balancer V2
(mulDown, 30 cycles); carry the exact value and round once, and the attack
stops. Band 2, "rounded at a unit": Thetanuts (two thirds of a raw unit
floored to 0, 37 mints) and Balancer V1 (just under four and a half units
rounded to nearest, 4); no precision helps there, only the direction
decides who pays, so in the last beat each dot is sent the other way in
emerald. The box line closes: inside a calculation, precision shrinks
error; at a unit, direction decides who pays.

Every row has the same anatomy: protocol and date (talk/scenes/data/
incidents.json), a mini grid with its two ticks named, the exact value as a
white dot with its number to the right (complete, in a stated format), the
rounded value snapping to a tick in red with the direction drawn, and the
mechanism on the line beneath. Nine sections, one per click: the bands;
rows 1, 2, 3; band 1 resolved; rows 4, 5; band 2 resolved; the box.

Numbers: row 1 reuses s06_resupply.numbers() (the rate to 22 decimals and
its floor). Row 2 from scripts/replays/bunni.json: the first withdrawal's
idle-balance subtrahend idle × shares / totalSupply (to 3 decimals) and its
floor, and the active balance after each of the 44 withdrawals from
vocab.bunni_replay(). Row 3 from scripts/replays/balancer.json: the osETH
scaling factor in the tx and the micro swaps' 17 wei upscaled, 17 × factor /
10^18 (to 18 decimals) and mulDown's result; the cycle count from the
scored steps. Row 4 from scripts/replays/thetanuts.json: the first mint's
operands (amount 2, held 1, supply 3) and the charge, and the mint count.
Row 5 from vocab.balancer_v1_replay(): the BNum tokenInRatio at a balance
of 3 in pools 1–3, 3 × ratio / 10^18 (to 18 decimals) and bmul's
half-up result. Claims C1–C5, C8, C9/V27, V12 (research_notes/talk/
verify-C.md, claims.md).
"""

from __future__ import annotations

from fractions import Fraction

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Create,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    RoundedRectangle,
    VGroup,
)
from manim.utils.rate_functions import ease_out_cubic

from s06_resupply import numbers as resupply_numbers
from vocab import (
    PROTOCOL_COLOUR,
    SIZE_BODY,
    SIZE_HERO,
    DeckScene,
    GridLine,
    Palette,
    balancer,
    balancer_v1_replay,
    bunni_replay,
    check_mark,
    digits,
    direction,
    glow_bar,
    halo,
    incidents,
    measure,
    resupply,
    snap,
    thetanuts,
    to_decimals,
    words,
    _load,
)

SUB_DECIMALS = 3  # Bunni's subtrahend, named to this many decimals
WAD_DECIMALS = 18  # Balancer's grids: 10^-18
ROWS = ("resupply", "bunni", "balancer-v2", "thetanuts", "balancer-v1")
BAND_1, BAND_2 = (0, 1, 2), (3, 4)
TITLE = "Two failures, one decision"
BAND_1_TITLE = "rounded too early, or too often"
BAND_2_TITLE = "rounded at a unit"
ROUND_ONCE = "carry the exact value and round once, and the attack stops"
WHO_PAYS = "who pays?"
BOX_1 = "Inside a calculation, precision shrinks error."
BOX_2 = "At a unit, direction decides who pays."
CAPTION = "scripts/replays/*.json · incidents.json"
MECH_RESUPPLY = "floored once"
MECH_THETANUTS = "floored; {mints} mints, every charge {charge}"
MECH_V1 = "nearest: 1 unit charged for 1.5 units' worth"
TWO_THIRDS = "two thirds of a unit"
TWO_THIRDS_FRACTION = "2/3"
CEIL_LABEL = "ceil → 1 unit · would have cost more than it took"
TOWARD_POOL = "toward the pool → 5"

# the digit-bearing fixed strings, each with its claim id (research_notes/talk/verify-C.md)
LITERALS = {
    TWO_THIRDS_FRACTION: "C4",  # the first mint's exact charge, 2 × 1 / 3 (C4, C8)
    MECH_V1: "C5",  # one unit charged for about 1.5 units' worth (exact cost 1.50079 to 1.52749)
    CEIL_LABEL: "C8",  # ceil → 1 unit on the first mint; the counterfactual total exceeds every take (off-chain)
    TOWARD_POOL: "C5",  # "instead of 5" means rounding toward the pool
}

# geometry (scene units: 1080p is 8 high by 14.2 wide; the 5% safe area is ±3.6 by ±6.4).
# A row is two lines: (a) protocol · date, then the exact value and its format; (b) the
# mini grid with its two ticks named at its ends, then the mechanism. Rows 1, 3 and 5
# carry a value too long for its format to share line (a); it goes on line (b), or,
# for row 5, under the half-unit bracket. Every string is at SIZE_BODY; nothing shrinks.
X_LEFT = -6.4
X_NUM = -1.0  # the exact value starts here, after the widest protocol · date
X_MECH = -3.2  # the mechanism starts here, after the grid and its tick names
GRID_LEN = 1.55
NAME_GAP = 0.22  # a tick name to the line's end
Y_BAND_1 = 2.86  # under the left mark
Y_A = (2.45, 1.49, 0.53, -1.43, -2.39)  # line (a) of each row
A_B = 0.5  # line (b) is this far under line (a)
Y_ONCE = -0.43
Y_RULE = -0.69
Y_BAND_2 = -0.93
ARROW_UP = 0.2
HALF_DROP = 0.22
GAP = 0.3
TICK_DT = 1 / 30  # a counter's step: one frame


def times(k: int) -> str:
    return "once" if k == 1 else f"{k} times"


def mech_bunni(k: int, start: int, active: int) -> str:
    return f"floored, {times(k)}: active balance {start} → {active} wei"


def mech_v2(k: int) -> str:
    return f"mulDown, ×{k} cycles"


def numbers() -> dict:
    inc = incidents()["incidents"]
    assert len(inc) == len(ROWS), len(inc)
    names = [i["protocol"] for i in inc]
    assert names[0].startswith("Resupply") and names[1].startswith("Bunni") and names[2] == "Balancer V2" and names[3] == "Thetanuts" and names[4] == "Balancer V1", names

    # row 1: the rate, as slide 6 named it, and its floor
    r6 = resupply_numbers()
    price = int(resupply()["pins"]["price"])
    rate = Fraction(10 ** r6["rate_exp"], price)
    assert to_decimals(rate, 22) == r6["rate_short"] and str(10 ** r6["rate_exp"] // price) == r6["floor"]

    # row 2: the first withdrawal's idle-balance subtrahend and the active balance through the 44
    bj = _load("scripts/replays/bunni.json")
    idle0, s0, t0 = int(bj["start"]["idle"]), int(bj["steps"]["shares"][0]), int(bj["start"]["totalSupply"])
    sub = Fraction(idle0 * s0, t0)
    sub_floor = idle0 * s0 // t0
    snaps = bj["snapshots"]
    assert int(snaps["after"][0]) == 1 and idle0 - int(snaps["idle"][0]) == sub_floor, "the chain's idle balance fell by the floored subtrahend"
    active = [int(a) for a in bunni_replay()["seq"]["deployed"]]
    withdrawals = len(active) - 1
    assert withdrawals == len(bj["steps"]["shares"])

    # row 3: 17 osETH-wei upscaled by the rate in the tx, and what mulDown kept
    bal = balancer()
    pool = bal["pools"]["osETH"]
    factor = int(bal["score"]["osETH"]["rate"])
    assert factor == int(pool["rateCacheUpdatedInTx"]["providerRate"]) == int(pool["scalingFactorsInTx"][pool["symbols"].index("osETH")]), factor
    micro = [s for s in bal["score"]["osETH"]["steps"] if s["what"] == "micro"]
    cycles = len(micro)
    assert cycles == int(bal["score"]["osETH"]["kinds"]["micro"]), cycles
    (out,) = {int(s["out"]) for s in micro}
    upscaled = Fraction(out * factor, 10**WAD_DECIMALS)
    mul_down = out * factor // 10**WAD_DECIMALS
    assert all(int(s["upscaledOutDeployed"]) == mul_down for s in micro), "mulDown's result, as scored"

    # row 4: the first mint's charge, amount × held / supply, and the 37 mints
    tj = thetanuts()
    mints = tj["mints"]
    m0 = mints[0]
    amount, supply = int(m0["amount"]), int(m0["supplyBefore"])
    (held,) = {int(h) for h in m0["storedBefore"]}
    assert supply == int(tj["claim"]["supplyAfter"]) and held == 1 and all(int(h) == held for h in tj["claim"]["storedAfter"])
    charge = Fraction(amount * held, supply)
    charge_floor = amount * held // supply
    assert all(int(c) == charge_floor for m in mints for c in m["charge"]), "every charge of every mint is 0"

    # row 5: BNum's tokenInRatio at a balance of 3, pools 1–3, times the balance
    v1 = balancer_v1_replay()
    bone = 10**WAD_DECIMALS
    at3 = [r for p in v1[:3] for r in p if r["kind"] == 2 and r["balance"] == 3]
    (ratio,) = {int(r["steps"]["tokenInRatio"]) for r in at3}
    (balance,) = {int(r["balance"]) for r in at3}
    product = Fraction(balance * ratio, bone)
    nearest = (balance * ratio + bone // 2) // bone  # bmul: half up on the 10^-18 grid
    assert all(int(r["steps"]["newTokenBalanceIn"]) == nearest for r in at3) and all(int(r["deployed"]) == 1 for r in at3)
    joins = sum(1 for p in v1 for r in p if r["kind"] == 2)

    rows = [
        {
            "id": ROWS[0],
            "protocol": names[0],
            "date": inc[0]["date"],
            "ticks": [0, 1],
            "x": float(rate),
            "exact": r6["rate_short"],
            "exact_label": r6["rate_label"],
            "rounded": r6["floor"],
            "to": int(r6["floor"]),
            "mechanism": MECH_RESUPPLY,
        },
        {
            "id": ROWS[1],
            "protocol": names[1],
            "date": inc[1]["date"],
            "ticks": [sub_floor, sub_floor + 1],
            "x": float(sub),
            "exact": to_decimals(sub, SUB_DECIMALS),
            "exact_label": f"(to {SUB_DECIMALS} decimals)",
            "rounded": str(sub_floor),
            "to": sub_floor,
            "mechanism": mech_bunni(withdrawals, active[0], active[-1]),
            "counter": [mech_bunni(k, active[0], active[k]) for k in range(1, withdrawals + 1)],
            "withdrawals": withdrawals,
            "active": active,
        },
        {
            "id": ROWS[2],
            "protocol": names[2],
            "date": inc[2]["date"],
            "ticks": [mul_down, mul_down + 1],
            "x": float(upscaled),
            "exact": to_decimals(upscaled, WAD_DECIMALS),
            "exact_label": f"(to {WAD_DECIMALS} decimals)",
            "rounded": str(mul_down),
            "to": mul_down,
            "mechanism": mech_v2(cycles),
            "counter": [mech_v2(k) for k in range(1, cycles + 1)],
            "cycles": cycles,
            "out": out,
            "factor": str(factor),
        },
        {
            "id": ROWS[3],
            "protocol": names[3],
            "date": inc[3]["date"],
            "ticks": [0, 1],
            "x": float(charge),
            "exact": TWO_THIRDS,
            "exact_label": TWO_THIRDS_FRACTION,
            "rounded": str(charge_floor),
            "to": charge_floor,
            "mechanism": MECH_THETANUTS.format(mints=len(mints), charge=charge_floor),
            "mints": len(mints),
            "operands": [amount, held, supply],
            "other_way": 1,
            "other_label": CEIL_LABEL,
        },
        {
            "id": ROWS[4],
            "protocol": names[4],
            "date": inc[4]["date"],
            "ticks": [nearest, nearest + 1],
            "x": float(product),
            "exact": to_decimals(product, WAD_DECIMALS),
            "exact_label": f"(to {WAD_DECIMALS} decimals)",
            "rounded": str(nearest),
            "to": nearest,
            "mechanism": MECH_V1,
            "ratio": str(ratio),
            "balance": balance,
            "joins": joins,
            "other_way": nearest + 1,
            "other_label": TOWARD_POOL,
        },
    ]
    for r in rows:
        assert "…" not in r["exact"] and r["ticks"][0] <= r["x"] <= r["ticks"][1] and r["to"] in r["ticks"], r["id"]
    # the story, in exact arithmetic (as floats, the Resupply and Balancer V1 values are indistinguishable from one half):
    # Balancer V1 rounds to nearest and the exact product still lands below the half (V27); Thetanuts floors two thirds against the nearer tick
    assert product < nearest + Fraction(1, 2) and rows[4]["to"] == rows[4]["ticks"][0]
    assert charge > Fraction(1, 2) and rows[3]["to"] == rows[3]["ticks"][0]
    assert rate < Fraction(1, 2)  # just under one half, floored once (C1)
    return {"rows": rows, "half": 0.5, "wad_decimals": WAD_DECIMALS}



class Two(DeckScene):
    SECTIONS = ("bands", "resupply", "bunni", "balancer-v2", "round-once", "thetanuts", "balancer-v1", "direction", "box")

    # ------------------------------------------------------------- helpers --
    @staticmethod
    def left(mobj, x: float, y: float):
        return mobj.move_to([x + mobj.width / 2, y, 0])

    @staticmethod
    def after(mobj, prev, gap: float = GAP):
        return mobj.next_to(prev, RIGHT, buff=gap).set_y(prev.get_y())

    def grid_for(self, r: dict, y: float) -> VGroup:
        """The mini grid: its two ticks named at its ends, at the line's height."""
        a, b = r["ticks"]
        name0 = self.left(digits(str(a), SIZE_BODY, Palette.FAINT), X_LEFT, y)
        line = GridLine((a, b, 1), length=GRID_LEN, tick_size=0.13)
        line.shift([name0.get_right()[0] + NAME_GAP, y, 0] - line.n2p(a))
        name1 = digits(str(b), SIZE_BODY, Palette.FAINT).move_to(line.n2p(b) + RIGHT * NAME_GAP, aligned_edge=LEFT).set_y(y)
        g = VGroup(name0, line, name1)
        g.line = line
        return g

    def mechanism(self, text: str, x: float, y: float, colour: str = Palette.MUTED):
        return self.left(words(text, SIZE_BODY, colour), x, y)

    def head_for(self, i: int, r: dict):
        """The row's key: protocol · date, in the protocol's hue."""
        return self.left(words(f"{r['protocol']} · {r['date']}", SIZE_BODY, PROTOCOL_COLOUR[r["id"]]), X_LEFT, Y_A[i])

    def row(self, i: int, r: dict, head, grid: VGroup) -> dict:
        """One incident on its row (the key and the grid are chrome, on the
        first frame): the exact value in its format, the white dot, the red
        snap with its direction, the mechanism."""
        ya = Y_A[i]
        yb = ya - A_B
        line = grid.line
        exact = line.dot_at(r["x"], Palette.EXACT)
        exact.move_to(line.n2p(r["x"]) + UP * 0.6)
        self.play(FadeIn(exact, run_time=0.2))
        self.play(exact.animate(rate_func=ease_out_cubic).move_to(line.n2p(r["x"])), run_time=0.5)
        # the value, white, and its format: beside it when the line has room, else on line (b) (row 5: under the bracket)
        if r["id"] == ROWS[3]:
            value = self.left(words(r["exact"], SIZE_BODY, Palette.EXACT), X_NUM, ya)
            fmt = self.after(digits(r["exact_label"], SIZE_BODY, Palette.MUTED), value)
        else:
            value = self.left(digits(r["exact"], SIZE_BODY, Palette.EXACT), X_NUM, ya)
            fmt = words(r["exact_label"], SIZE_BODY, Palette.MUTED)
            if value.get_right()[0] + GAP + fmt.width <= -X_LEFT:
                self.after(fmt, value)
            elif r["id"] == ROWS[4]:
                self.left(fmt, X_MECH, yb - A_B + 0.06)
            else:
                self.left(fmt, X_MECH, yb)
        self.play(FadeIn(value, run_time=0.4), FadeIn(fmt, run_time=0.4))
        self.wait(0.6)
        arrow = direction(line, r["x"], r["to"], Palette.WRONG, lift=ARROW_UP)
        moving = exact.copy()
        self.add(moving)
        self.play(Create(arrow, run_time=0.35))
        self.play(snap(moving, line, r["to"], Palette.WRONG, run_time=0.8))
        self.bring_to_front(exact)
        x_mech = fmt.get_right()[0] + GAP if abs(fmt.get_y() - yb) < 0.01 else X_MECH
        if "counter" in r:
            mech = None
            for text in r["counter"]:
                nxt = self.mechanism(text, x_mech, yb)
                if mech is None:
                    self.play(FadeIn(nxt, run_time=0.3))
                else:
                    self.remove(mech)
                    self.add(nxt)
                    self.wait(TICK_DT)
                mech = nxt
        else:
            mech = self.mechanism(r["mechanism"], x_mech, yb)
            self.play(FadeIn(mech, shift=UP * 0.05, run_time=0.4))
        return dict(head=head, grid=grid, line=line, exact=exact, moving=moving, arrow=arrow, value=value, fmt=fmt, mech=mech, yb=yb, r=r)

    def other_way(self, p: dict):
        """Band 2's resolution: the dot sent the other way, toward the pool, in emerald, with a tick."""
        r, line, yb = p["r"], p["line"], p["yb"]
        self.play(p["moving"].animate.set_color(Palette.FAINT), p["arrow"].animate.set_color(Palette.FAINT).set_opacity(0.5), run_time=0.4)
        arrow = direction(line, r["x"], r["other_way"], Palette.CORRECT, lift=ARROW_UP)
        dot = p["exact"].copy()
        glow = halo(line.n2p(r["other_way"]), Palette.CORRECT)
        self.add(dot)
        self.play(Create(arrow, run_time=0.35))
        self.play(snap(dot, line, r["other_way"], Palette.CORRECT, run_time=0.8), FadeIn(glow, run_time=0.8))
        self.bring_to_front(dot)
        label = self.mechanism(r["other_label"], X_MECH, yb, Palette.CORRECT)
        tick = check_mark(Palette.CORRECT, size=0.26).next_to(label, RIGHT, buff=0.2).set_y(yb)
        self.play(FadeOut(p["mech"], run_time=0.3), FadeIn(label, run_time=0.4))
        self.play(Create(tick, run_time=0.35))
        return VGroup(arrow, dot, glow, label, tick)

    # ------------------------------------------------------------- the scene --
    def construct(self):
        n = numbers()
        rows = n["rows"]
        self.section(0)
        # the chrome, on the first frame: the caption (bottom right: the left corner is row
        # 5's half-unit bracket), the title, the two band titles and the rule between them,
        # every row's key (protocol · date, in the protocol's hue) and its mini grid with
        # its two ticks named; only the values and the story arrive per click
        self.caption_now(CAPTION, corner=DOWN + RIGHT)
        title = self.title(TITLE, SIZE_BODY, Palette.TEXT)
        band1 = self.left(words(BAND_1_TITLE, SIZE_BODY, Palette.MUTED), X_LEFT, Y_BAND_1)
        band2 = self.left(words(BAND_2_TITLE, SIZE_BODY, Palette.MUTED), X_LEFT, Y_BAND_2)
        rule = Line([X_LEFT, Y_RULE, 0], [-X_LEFT, Y_RULE, 0], color=Palette.RULE, stroke_width=1, stroke_opacity=0.6)
        heads = [self.head_for(i, r) for i, r in enumerate(rows)]
        grids = [self.grid_for(r, Y_A[i] - A_B) for i, r in enumerate(rows)]
        self.fix(title, band1, band2, rule, *heads, *grids)
        self.wait(1.2)

        # band 1: too early, too often
        parts = []
        for i in BAND_1:
            self.section(i + 1, hold=1.2)
            parts.append(self.row(i, rows[i], heads[i], grids[i]))

        # round once: the red goes faint, the exact value pulses, the line and its tick
        self.section(4, hold=1.5)
        self.play(
            *[p["moving"].animate.set_color(Palette.FAINT) for p in parts],
            *[p["arrow"].animate.set_color(Palette.FAINT).set_opacity(0.5) for p in parts],
            run_time=0.6,
        )
        self.play(*[Indicate(p["exact"], color=Palette.EXACT, scale_factor=1.7) for p in parts], run_time=0.9)
        once = self.left(words(ROUND_ONCE, SIZE_BODY, Palette.CORRECT), X_LEFT, Y_ONCE)
        tick = check_mark(Palette.CORRECT, size=0.3).next_to(once, RIGHT, buff=0.3).set_y(Y_ONCE)
        self.play(FadeIn(once, shift=RIGHT * 0.1, run_time=0.6))
        self.play(Create(tick, run_time=0.4))

        # band 2: at a unit
        self.section(5, hold=1.5)
        parts.append(self.row(3, rows[3], heads[3], grids[3]))

        self.section(6, hold=1.2)
        p5 = self.row(4, rows[4], heads[4], grids[4])
        parts.append(p5)
        a = rows[4]["ticks"][0]
        half = measure(p5["line"], a, a + n["half"], "half a unit", drop=HALF_DROP)
        self.play(FadeIn(half, shift=UP * 0.04, run_time=0.5))

        # direction: who pays; the other way, in emerald
        self.section(7, hold=1.5)
        who = self.after(words(WHO_PAYS, SIZE_BODY, Palette.BODY), band2, gap=0.5)
        self.play(FadeIn(who, shift=RIGHT * 0.1, run_time=0.5))
        self.other_way(parts[3])
        self.wait(0.5)
        self.other_way(parts[4])

        # the box: the hero line over the dimmed data (the chrome stays as it is)
        self.section(8, hold=1.5)
        everything = self.dimmable()
        box = VGroup(words(BOX_1, SIZE_HERO, Palette.TEXT), words(BOX_2, SIZE_HERO, Palette.TEXT)).arrange(DOWN, buff=0.2)
        box.move_to([0, -0.4, 0])
        bar = glow_bar(box, Palette.CORRECT, pad=0.22, opacity=0.14)
        mask = RoundedRectangle(width=bar.width, height=bar.height, corner_radius=0.12, color=Palette.BG, fill_color=Palette.BG, fill_opacity=1.0, stroke_width=0).move_to(bar)
        self.play(everything.animate.fade(0.72), run_time=0.8)
        self.play(FadeIn(mask, run_time=0.3), FadeIn(bar, run_time=0.5))
        self.play(FadeIn(box[0], shift=UP * 0.08, run_time=0.6))
        self.wait(0.4)
        self.play(FadeIn(box[1], shift=UP * 0.08, run_time=0.6))
        self.close()

"""Slide 12, "There is no reference": one address, one word per input,
nothing to trust but the code; today on Sepolia.

The address is the hero: FP127 v9's (contracts/deployments/RELEASE.json
.components.FP127.address, claim V15) types in on a glowing panel at
the largest size its 42 characters fit the frame (SIZE_ADDRESS, 37:
at SIZE_HERO the address is 16.7 units wide, the safe area 13.5), then
shrinks to BODY on its own line under the title and stays there. Under it the
chain table (talk/scenes/data/chains.json, re-probed 2026-10-29: V3, V5)
lands one row at a time in the README's order: the chain's name, "CLZ
since <date>" where the data has a date, and the status word: "deployed"
in emerald with a halo on Sepolia's row (V6, the only one), "has CLZ ·
proxy present · not yet deployed" on every other supported chain (the
proxy word only because chains().proxy is true there), "no CLZ" in red
with a cross on the unsupported ones. The probe date is on screen as
long as the table is. Then the call: two boxes, "your contract" and
"the reference" (the address moves into it), an arrow "eth_call exp(40)"
between them, and the reference's 18-decimal word for exp(40), the same
string slide 2 shows as its exact row (correctly_rounded_18(truth80()),
V9), typed twice: the second time as the word a correct implementation
returns (V2, K14: one right word per input), judged equal with a tick.
Four properties land with ticks (V4: no storage, no owner, no upgrade
path, source verified), and the closing line names where it is today.

Five sections: address, chains, call, properties, closing.
"""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AddTextLetterByLetter,
    Arrow,
    Create,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    SIZE_BODY,
    SIZE_CAPTION,
    DeckScene,
    Palette,
    box,
    chains,
    check_mark,
    correctly_rounded_18,
    cross_mark,
    digits,
    glow_bar,
    halo,
    probe,
    release,
    truth80,
    words,
)

OP, ARG = "exp", "40"
COMPONENT = "FP127"
WORD_DECIMALS = 18

TITLE = "There is no reference"
BOX_YOURS = "your contract"
BOX_REFERENCE = "the reference"
EQUAL = "equal"
SAME_WORD = "a correct implementation returns the same word"
PROPERTIES = ("no storage", "no owner", "no upgrade path", "source verified")
STATUS_DEPLOYED = "deployed"
STATUS_SUPPORTED = "has CLZ · proxy present · not yet deployed"
STATUS_SUPPORTED_NO_PROXY = "has CLZ · not yet deployed"  # when the proxy was not probed
STATUS_UNSUPPORTED = "no CLZ"
CLOSE = "one call to check · deployed today: Sepolia"

X_LEFT = -6.5  # the safe area's edges (5% of 1920 x 1080)
X_RIGHT = 6.5
Y_TITLE = 3.3
# the address: 42 mono characters are 16.7 units wide at SIZE_HERO, wider than the
# frame; SIZE_ADDRESS is the largest size at which the whole address fits the safe area
SIZE_ADDRESS = 37
Y_ADDRESS_HERO = 0.3
Y_ADDRESS = 2.72  # the address's line under the title from section 1
# the chain table: fifteen rows between the address and the caption
Y_ROWS_TOP = 2.15
Y_ROWS_BOTTOM = -2.95
SIZE_CHAIN = 26  # a chain's name; "deployed" and "no CLZ"
SIZE_CELL = 22  # "CLZ since <date>" and the long status phrase: the widest row is 13.2 units at these sizes
X_CLZ = -3.05  # the "CLZ since" column
X_STATUS = 0.8  # the status column
# the call: the reference box around the address, your contract below, an elbowed call path
Y_REFERENCE = 2.25
Y_YOURS = 0.6
X_ELBOW = 1.6
SIZE_CALL = 26
Y_WORD = -0.55  # the reference's word
WORD_PITCH = 0.65  # to your contract's word
Y_SAME = -1.7
Y_PROPERTIES = -2.3
SIZE_PROPERTY = 28  # four phrases with ticks on one line: 12.5 units
Y_CLOSE = -3.05
X_CLOSE = 0.6  # the closing panel sits clear of the caption at the bottom-left
TABLE_DIM = 0.06  # the table's opacity behind the call

# the digit-bearing fixed strings, each with its claim id (research_notes/talk/claims.md)
LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers(): the address, the version, the dates, the word, the argument


def call_label() -> str:
    return f"eth_call {OP}({ARG})"


def status_of(row: dict) -> tuple[str, str]:
    """A chain row's status word and its colour, from the data alone."""
    if row["status"] != "supported":
        return STATUS_UNSUPPORTED, Palette.WRONG
    if row["deployed"]:
        return STATUS_DEPLOYED, Palette.CORRECT
    return (STATUS_SUPPORTED if row["proxy"] else STATUS_SUPPORTED_NO_PROXY), Palette.MUTED


def numbers() -> dict:
    rel = release()
    comp = rel["components"][COMPONENT]
    d = chains()
    rows = []
    for r in d["chains"]:
        status, _ = status_of(r)
        rows.append(
            {
                "chain": r["chain"],
                "clz_since": r["clz_since"],
                "clz_text": f"CLZ since {r['clz_since']}" if r["clz_since"] else None,
                "status": r["status"],
                "deployed": bool(r["deployed"]),
                "proxy": r["proxy"],
                "status_text": status,
                "probed": r["probed"],
            }
        )
    p = probe(OP, ARG)
    word = correctly_rounded_18(truth80())
    assert len(word.partition(".")[2]) == WORD_DECIMALS and "…" not in word, word
    assert len(comp["address"]) == 42 and comp["address"].startswith("0x"), comp["address"]
    return {
        "address": comp["address"],
        "version": comp["version"],
        "release": rel["release"],
        "network": rel["network"],
        "rows": rows,
        "probed": d["probed"],
        "probed_caption": f"probed {d['probed']}",
        "arg": ARG,
        "call": call_label(),
        "truth_probe": p["truth"],
        "word": word,
        "word_decimals": WORD_DECIMALS,
    }


class Reference(DeckScene):
    SECTIONS = ("address", "chains", "call", "properties", "closing")

    def row_y(self, i: int, n: int) -> float:
        return Y_ROWS_TOP - i * (Y_ROWS_TOP - Y_ROWS_BOTTOM) / (n - 1)

    def chain_row(self, i: int, n: int, r: dict) -> VGroup:
        """One chain's row: the name (SANS), CLZ since <date> (MONO, muted)
        where the data has a date, and the status word in its colour, a
        cross before "no CLZ"."""
        y = self.row_y(i, n)
        status, colour = status_of(r)
        unsupported = r["status"] != "supported"
        name = words(r["chain"], SIZE_CHAIN, Palette.WRONG if unsupported else Palette.TEXT)
        name.move_to([X_LEFT + name.width / 2, y, 0])
        parts = [name]
        if r["clz_text"]:
            clz = digits(r["clz_text"], SIZE_CELL, Palette.MUTED)
            clz.move_to([X_CLZ + clz.width / 2, y, 0])
            parts.append(clz)
        short = unsupported or r["deployed"]
        st = words(status, SIZE_CHAIN if short else SIZE_CELL, colour)
        x = X_STATUS
        if unsupported:
            cross = cross_mark(size=0.24).move_to([X_STATUS + 0.12, y, 0])
            parts.append(cross)
            x += 0.42
        st.move_to([x + st.width / 2, y, 0])
        parts.append(st)
        g = VGroup(*parts)
        g.status = st
        return g

    def construct(self):
        n = numbers()
        rows = n["rows"]
        n_rows = len(rows)

        # 0 · the address, the hero: typed in on a glowing panel, the version under it
        self.section(0)
        self.wait(0.3)
        title = words(TITLE, SIZE_BODY, Palette.TEXT)
        title.move_to([X_LEFT + title.width / 2, Y_TITLE, 0])
        self.play(FadeIn(title, shift=RIGHT * 0.1, run_time=0.5))
        addr = digits(n["address"], SIZE_ADDRESS, Palette.CORRECT).move_to([0, Y_ADDRESS_HERO, 0])
        assert addr.width <= X_RIGHT - X_LEFT, addr.width  # the whole address, inside the safe area
        panel = glow_bar(addr, Palette.EMERALD, pad=0.26, opacity=0.1)
        panel.set_fill(opacity=0)
        self.add(panel)
        self.play(panel.animate.set_fill(opacity=0.1), run_time=0.4)
        self.play(AddTextLetterByLetter(addr, time_per_char=0.075))
        version = words(n["version"], SIZE_CAPTION, Palette.MUTED).next_to(panel, DOWN, buff=0.22)
        self.play(FadeIn(version, shift=UP * 0.08, run_time=0.5))
        self.play(Indicate(addr, color=Palette.CORRECT, scale_factor=1.02, run_time=0.6))

        # 1 · the chains: the address goes to its own line under the title, the rows land one by one, Sepolia last
        self.section(1)
        addr_small = digits(n["address"], SIZE_BODY, Palette.CORRECT)
        version_small = words(n["version"], SIZE_CAPTION, Palette.MUTED)
        line = VGroup(addr_small, version_small).arrange(RIGHT, buff=0.3).move_to([0, Y_ADDRESS, 0])
        self.play(
            Transform(addr, addr_small, run_time=0.9, rate_func=ease_out_cubic),
            Transform(version, version_small, run_time=0.9, rate_func=ease_out_cubic),
            FadeOut(panel, run_time=0.5),
        )
        self.play(self.caption(n["probed_caption"]))
        table = VGroup()
        sepolia = None
        for i, r in enumerate(rows):
            g = self.chain_row(i, n_rows, r)
            assert g.get_right()[0] <= X_RIGHT + 0.05, (r["chain"], g.get_right()[0])
            table.add(g)
            if r["deployed"]:
                sepolia = g  # lands last, the hero row
                continue
            self.play(FadeIn(g, shift=RIGHT * 0.12, run_time=0.25))
            self.wait(0.05)
        assert sepolia is not None
        bar = glow_bar(sepolia, Palette.EMERALD, pad=0.06, opacity=0.1)
        bar.stretch_to_fit_width(X_RIGHT - X_LEFT + 0.3).set_x((X_LEFT + X_RIGHT) / 2)
        glow = halo(sepolia.status.get_center(), Palette.EMERALD, radius=0.12, spread=2.6, opacity=0.16)
        table.add_to_back(bar, glow)
        self.play(FadeIn(bar, run_time=0.5), FadeIn(glow, run_time=0.5), FadeIn(sepolia, shift=RIGHT * 0.12, run_time=0.5))
        self.play(Indicate(sepolia.status, color=Palette.CORRECT, scale_factor=1.08, run_time=0.6))

        # 2 · the call: the reference box closes around the address, your contract calls it, the one word twice
        self.section(2)
        self.play(table.animate.set_opacity(TABLE_DIM), run_time=0.6)
        addr_in = digits(n["address"], SIZE_BODY, Palette.CORRECT)
        ref = box(BOX_REFERENCE, addr_in, colour=Palette.EMERALD, gap=0.16, pad=0.26)
        ref.move_to([0, Y_REFERENCE, 0])
        ver_in = words(n["version"], SIZE_CAPTION, Palette.MUTED).next_to(ref.label, RIGHT, buff=0.3)
        yours = box(BOX_YOURS, pad=0.26)
        yours.move_to([X_LEFT + yours.width / 2, Y_YOURS, 0])
        self.play(Create(ref.rect, run_time=0.6), FadeIn(ref.label, run_time=0.6))
        self.bring_to_front(addr, version)  # the box's fill hides the dimmed table, not the address
        self.play(
            Transform(addr, addr_in, run_time=0.8, rate_func=ease_out_cubic),
            Transform(version, ver_in, run_time=0.8, rate_func=ease_out_cubic),
        )
        self.play(Create(yours.rect, run_time=0.5), FadeIn(yours.label, run_time=0.5))
        # the call path: right from your contract, then up into the reference
        start = yours.rect.get_right() + RIGHT * 0.1
        corner = [X_ELBOW, Y_YOURS, 0]
        leg = Line(start, corner, color=Palette.BODY, stroke_width=3)
        arrow = Arrow(corner, [X_ELBOW, ref.rect.get_bottom()[1] - 0.08, 0], buff=0, color=Palette.BODY, stroke_width=3, tip_length=0.22, max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=100.0)
        call = digits(n["call"], SIZE_CALL, Palette.BODY).next_to(leg, UP, buff=0.12)
        call.set_x(start[0] + 0.1 + call.width / 2)
        self.play(Create(leg, run_time=0.35), FadeIn(call, shift=RIGHT * 0.1, run_time=0.4))
        self.play(Create(arrow, run_time=0.35))
        self.wait(0.3)
        # the reference's word, then your contract's: the same string, from the same loader
        from_ref = words(BOX_REFERENCE, SIZE_CAPTION, Palette.MUTED)
        from_yours = words(BOX_YOURS, SIZE_CAPTION, Palette.MUTED)
        x_label = X_LEFT + max(from_ref.width, from_yours.width)
        from_ref.move_to([x_label - from_ref.width / 2, Y_WORD, 0])
        from_yours.move_to([x_label - from_yours.width / 2, Y_WORD - WORD_PITCH, 0])
        word_ref = digits(n["word"], SIZE_BODY, Palette.EXACT)
        word_yours = digits(n["word"], SIZE_BODY, Palette.EXACT)
        word_ref.move_to([x_label + 0.25 + word_ref.width / 2, Y_WORD, 0])
        word_yours.move_to([word_ref.get_x(), Y_WORD - WORD_PITCH, 0])
        self.play(FadeIn(from_ref, run_time=0.3))
        self.play(AddTextLetterByLetter(word_ref, time_per_char=0.045))
        self.play(FadeIn(from_yours, run_time=0.3))
        self.play(AddTextLetterByLetter(word_yours, time_per_char=0.045))
        tick = check_mark(size=0.34)
        equal = words(EQUAL, SIZE_CALL, Palette.CORRECT)
        judge = VGroup(tick, equal).arrange(DOWN, buff=0.14)
        judge.move_to([word_ref.get_right()[0] + 0.3 + judge.width / 2, Y_WORD - WORD_PITCH / 2, 0])
        assert judge.get_right()[0] <= X_RIGHT + 0.05, judge.get_right()[0]
        self.play(Create(tick, run_time=0.4), FadeIn(equal, shift=UP * 0.06, run_time=0.4))
        same = words(SAME_WORD, SIZE_CAPTION, Palette.FAINT).move_to([word_yours.get_x(), Y_SAME, 0])
        self.play(FadeIn(same, shift=UP * 0.06, run_time=0.5))

        # 3 · the properties, one by one, each with a tick
        self.section(3)
        items = []
        for phrase in PROPERTIES:
            t = check_mark(size=0.24)
            w = words(phrase, SIZE_PROPERTY, Palette.BODY)
            items.append(VGroup(t, w).arrange(RIGHT, buff=0.16))
        props = VGroup(*items).arrange(RIGHT, buff=0.6).move_to([0, Y_PROPERTIES, 0])
        assert props.width <= X_RIGHT - X_LEFT, props.width
        for item in items:
            self.play(Create(item[0], run_time=0.25), FadeIn(item[1], shift=UP * 0.08, run_time=0.25))
            self.wait(0.25)

        # 4 · the closing line, on its own glowing panel
        self.section(4, hold=1.6)
        close = words(CLOSE, SIZE_BODY, Palette.TEXT).move_to([X_CLOSE, Y_CLOSE, 0])
        close_panel = glow_bar(close, Palette.EMERALD, pad=0.2, opacity=0.1)
        close_panel.set_fill(opacity=0)
        self.add(close_panel)
        self.play(close_panel.animate.set_fill(opacity=0.1), FadeIn(close, shift=UP * 0.08, run_time=0.8))
        self.close(hold=4.0)

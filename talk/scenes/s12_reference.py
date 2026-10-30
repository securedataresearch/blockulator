"""Slide 12, "There is no reference": one address, one word per input,
nothing to trust but the code; today on Sepolia.

The address is the hero: BL127 v9's (contracts/deployments/RELEASE.json
.components.BL127.address, claim V15) types in inside the reference's box
("the reference", the version beside it) on a glowing panel, at the
largest size at which its 42 characters and the box fit the safe area
(SIZE_ADDRESS, 35: at SIZE_HERO the address is 16.7 units wide, the safe
area 12.8). Then the
box goes to the top at BODY and stays there, and the chain table
(talk/scenes/data/chains.json, re-probed 2026-10-29: V3, V5) lands under
it, grouped by status: Sepolia "deployed" in emerald under a halo (V6, the
only one), the chains with CLZ and the proxy "not yet deployed", the
chains with "no CLZ" in red with a cross. Then the table fades out
(Sepolia's row becomes the box's short label "deployed today: Sepolia",
the user's honesty pin) and the call plays: "your contract" calls the
reference, "eth_call exp(40)", and the reference's 18-decimal word for
exp(40), the same string slide 2 shows as its exact row
(correctly_rounded_18(truth80()), V9), types in emerald (the reference's
colour); last your contract's word, the same string in white (a correct
implementation returns the same word: V2, K14), judged equal with a tick.

Four sections: address, chains, call, closing. The properties line ("no
owner, no upgrade path") and the closing sentence are the speaker's.
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
    ReplacementTransform,
    RoundedRectangle,
    Transform,
    VGroup,
)
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    SIZE_BODY,
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
COMPONENT = "BL127"
WORD_DECIMALS = 18

TITLE = "There is no reference"
BOX_YOURS = "your contract"
BOX_REFERENCE = "the reference"
EQUAL = "equal"
STATUS_DEPLOYED = "deployed"
STATUS_SUPPORTED = "has CLZ · proxy present · not yet deployed"
STATUS_SUPPORTED_NO_PROXY = "has CLZ · not yet deployed"  # when the proxy was not probed
STATUS_UNSUPPORTED = "no CLZ"
PIN = "deployed today: "  # + the deployed chain, from the data: the box's short label once the table has gone

X_LEFT = -6.4  # the safe area's edges (5% of 1920 x 1080)
X_RIGHT = 6.4
# the address: 42 mono characters are 16.7 units wide at SIZE_HERO, wider than the
# frame; SIZE_ADDRESS is the largest size at which the address and its box fit the safe area (36 is 13.1 wide boxed)
SIZE_ADDRESS = 35
Y_HERO = 0.2  # the box's centre in section 0
Y_BOX = 2.2  # the box's centre from section 1: under the title
BOX_PAD = 0.28
X_NAMES = -5.55  # the table's names start under the box's text
# the chain table, grouped: the names on the left (two sub-columns for a long group), the status on the right
Y_TABLE = 1.1  # the first group's first line
NAME_PITCH = 0.42  # line to line inside a group
GROUP_GAP = 0.22  # between groups
CAP_HALF = 0.115  # half a capital's height at BODY: a line's top above its centre
X_SUBCOL = -1.25  # a long group's second sub-column
SUBCOL_AT = 6  # a group with more names than this splits in two
X_STATUS = 1.7
# the call: your contract under the box's left, an elbowed call path up into the box
Y_YOURS = 0.0
X_ELBOW = 1.6
Y_WORD = -1.6  # the reference's word; your contract's under it
WORD_PITCH = 0.8
X_WORD = -5.55

# the digit-bearing fixed strings, each with its claim id (research_notes/talk/claims.md)
STEP = "Step 3. Deploy it where nobody can change it. Including you."  # the manual's step line, the slide's first beat
LITERALS: dict[str, str] = {STEP: "user 2026-10-30 outline"}  # every digit on the slide is a value of numbers(): the address, the version, the word, the argument


def call_label() -> str:
    return f"eth_call {OP}({ARG})"


def status_of(row: dict) -> tuple[str, str]:
    """A chain row's status word and its colour, from the data alone."""
    if row["status"] != "supported":
        return STATUS_UNSUPPORTED, Palette.WRONG
    if row["deployed"]:
        return STATUS_DEPLOYED, Palette.CORRECT
    return (STATUS_SUPPORTED if row["proxy"] else STATUS_SUPPORTED_NO_PROXY), Palette.MUTED


def groups(rows: list[dict]) -> list[dict]:
    """The rows grouped by status, in the slide's order: deployed, the
    supported ones, the unsupported; the chains keep the README's order
    inside a group."""
    order = (STATUS_DEPLOYED, STATUS_SUPPORTED, STATUS_SUPPORTED_NO_PROXY, STATUS_UNSUPPORTED)
    out = []
    for status in order:
        names = [r["chain"] for r in rows if r["status_text"] == status]
        if names:
            out.append({"status": status, "chains": names})
    assert sum(len(g["chains"]) for g in out) == len(rows)
    return out


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
                "status": r["status"],
                "deployed": bool(r["deployed"]),
                "proxy": r["proxy"],
                "status_text": status,
                "probed": r["probed"],
            }
        )
    deployed = [r["chain"] for r in rows if r["deployed"]]
    assert len(deployed) == 1, deployed
    word = correctly_rounded_18(truth80())
    p = probe(OP, ARG)
    assert len(word.partition(".")[2]) == WORD_DECIMALS and "…" not in word, word
    assert len(comp["address"]) == 42 and comp["address"].startswith("0x"), comp["address"]
    return {
        "address": comp["address"],
        "version": comp["version"],
        "release": rel["release"],
        "network": rel["network"],
        "rows": rows,
        "groups": groups(rows),
        "pin": PIN + deployed[0],
        "probed": d["probed"],
        "arg": ARG,
        "call": call_label(),
        "truth_probe": p["truth"],
        "word": word,
        "word_decimals": WORD_DECIMALS,
    }


class Reference(DeckScene):
    SECTIONS = ("step", "address", "chains", "call", "closing")

    def ref_box(self, n: dict, size: float, y: float) -> VGroup:
        """The reference's box: its label and the version on the first line,
        the address under them, an emerald outline. .rect, .label, .version,
        .address name the parts."""
        address = digits(n["address"], size, Palette.CORRECT)
        label = words(BOX_REFERENCE, SIZE_BODY, Palette.TEXT)
        version = words(n["version"], SIZE_BODY, Palette.MUTED)
        head = VGroup(label, version).arrange(RIGHT, buff=0.35)
        inner = VGroup(head, address).arrange(DOWN, buff=0.2)
        head.align_to(address, LEFT)
        rect = RoundedRectangle(width=inner.width + 2 * BOX_PAD, height=inner.height + 2 * BOX_PAD, corner_radius=0.16, color=Palette.EMERALD, stroke_width=2.5, fill_opacity=0.0).move_to(inner)
        g = VGroup(rect, label, version, address).move_to([0, y, 0])
        assert rect.width <= X_RIGHT - X_LEFT, rect.width  # the whole address, inside the safe area
        g.rect, g.label, g.version, g.address = rect, label, version, address
        return g

    def column(self, names: list[str], colour: str, x: float, y: float):
        """A sub-column of chain names as ONE Text (one string for the eye's
        count), a name a line: each line's glyphs set flush left at x, the
        first line's centre at y, the next NAME_PITCH under it. Instrument
        Sans's Text keeps no submobject for a space or a line break, so a
        line is the next len(name without spaces) glyphs."""
        t = words("\n".join(names), SIZE_BODY, colour)
        i = 0
        for j, name in enumerate(names):
            k = len(name.replace(" ", ""))
            line = t[i : i + k]
            # tops aligned (every name has a capital or an ascender), so a descender does not lift its line
            line.shift([x - line.get_left()[0], y + CAP_HALF - j * NAME_PITCH - line.get_top()[1], 0])
            i += k
        assert i == len(t), (names, i, len(t))
        return t

    def group_rows(self, groups_: list[dict]) -> list[VGroup]:
        """Each status group: its names (one Text a sub-column, a line a
        chain) and its status, centred on the names, a cross before "no CLZ"."""
        out = []
        y = Y_TABLE
        for grp in groups_:
            status = grp["status"]
            unsupported = status == STATUS_UNSUPPORTED
            colour = {STATUS_DEPLOYED: Palette.CORRECT, STATUS_UNSUPPORTED: Palette.WRONG}.get(status, Palette.MUTED)
            names = grp["chains"]
            split = (len(names) + 1) // 2 if len(names) > SUBCOL_AT else len(names)
            cols = [names[:split], names[split:]] if split < len(names) else [names]
            name_colour = {STATUS_DEPLOYED: Palette.CORRECT, STATUS_UNSUPPORTED: Palette.WRONG}.get(status, Palette.TEXT)
            blocks = VGroup(*[self.column(col, name_colour, X_NAMES if k == 0 else X_SUBCOL, y) for k, col in enumerate(cols)])
            height = (len(cols[0]) - 1) * NAME_PITCH
            yc = y - height / 2
            st_text = status.replace(" · not yet", "\nnot yet")  # the long phrase on two lines
            st = words(st_text, SIZE_BODY, colour, line_spacing=0.8)
            x = X_STATUS
            parts = VGroup()
            if unsupported:
                cross = cross_mark(size=0.28).move_to([X_STATUS + 0.14, yc, 0])
                parts.add(cross)
                x += 0.5
            st.move_to([x + st.width / 2, yc, 0])
            if len(cols[0]) == 1:  # a one-line group: the status's top on the name's, as the names are set
                st.shift(UP * (y + CAP_HALF - st.get_top()[1]))
            parts.add(st)
            assert st.get_right()[0] <= X_RIGHT + 0.05, (status, st.get_right()[0])
            g = VGroup(blocks, parts)
            g.names, g.status, g.deployed = blocks, parts, status == STATUS_DEPLOYED
            out.append(g)
            y -= height + NAME_PITCH + GROUP_GAP
        assert y + NAME_PITCH + GROUP_GAP >= -3.6 + 0.2, y  # the last line inside the safe area
        return out

    def construct(self):
        n = numbers()

        # 0 · the reference's box, the address the hero: typed in on a glowing panel
        self.section(0)
        self.step(STEP)  # the step line alone, then its kicker above the title
        self.section(1)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.wait(0.3)
        hero = self.ref_box(n, SIZE_ADDRESS, Y_HERO)
        panel = glow_bar(hero.rect, Palette.EMERALD, pad=0.0, opacity=0.1)
        panel.set_fill(opacity=0)
        self.add(panel)
        self.play(Create(hero.rect, run_time=0.6), panel.animate.set_fill(opacity=0.1), FadeIn(hero.label, run_time=0.6), FadeIn(hero.version, run_time=0.6))
        self.play(AddTextLetterByLetter(hero.address, time_per_char=0.075))
        self.play(Indicate(hero.address, color=Palette.CORRECT, scale_factor=1.02, run_time=0.6))

        # 1 · the chains: the box goes under the title; the groups land one by one, Sepolia last
        self.section(2)
        top = self.ref_box(n, SIZE_BODY, Y_BOX)
        self.play(Transform(hero, top, run_time=0.9, rate_func=ease_out_cubic), FadeOut(panel, run_time=0.5))
        table = self.group_rows(n["groups"])
        sepolia = next(g for g in table if g.deployed)
        for g in table:
            if g is sepolia:
                continue
            self.play(FadeIn(g.names, shift=RIGHT * 0.12, run_time=0.4))
            self.play(FadeIn(g.status, shift=RIGHT * 0.12, run_time=0.35))
            self.wait(0.15)
        bar = glow_bar(sepolia, Palette.EMERALD, pad=0.1, opacity=0.1)
        bar.stretch_to_fit_width(X_RIGHT - X_LEFT + 0.2).set_x((X_LEFT + X_RIGHT) / 2)
        glow = halo(sepolia.status.get_center(), Palette.EMERALD, radius=0.16, spread=2.6, opacity=0.16)
        self.add(bar, glow)
        self.play(FadeIn(bar, run_time=0.5), FadeIn(glow, run_time=0.5), FadeIn(sepolia.names, shift=RIGHT * 0.12, run_time=0.5))
        self.play(FadeIn(sepolia.status, shift=RIGHT * 0.12, run_time=0.4))
        self.play(Indicate(sepolia.status, color=Palette.CORRECT, scale_factor=1.08, run_time=0.6))

        # 2 · the table leaves (Sepolia's row becomes the box's pin); your contract calls the reference
        self.section(3)
        pin = words(n["pin"], SIZE_BODY, Palette.MUTED)
        pin.move_to([hero.rect.get_right()[0] - BOX_PAD - pin.width / 2, hero.label.get_y(), 0])
        assert pin.get_left()[0] > hero.version.get_right()[0] + 0.3, (pin.get_left()[0], hero.version.get_right()[0])
        rest = VGroup(*[g for g in table if g is not sepolia], bar, glow)
        self.play(FadeOut(rest, run_time=0.6), ReplacementTransform(VGroup(sepolia.names, sepolia.status), pin, run_time=0.9, rate_func=ease_out_cubic))
        yours = box(BOX_YOURS, pad=0.26)
        yours.move_to([X_LEFT + yours.width / 2, Y_YOURS, 0])
        self.play(Create(yours.rect, run_time=0.5), FadeIn(yours.label, run_time=0.5))
        # the call path: right from your contract, then up into the reference
        start = yours.rect.get_right() + RIGHT * 0.1
        corner = [X_ELBOW, Y_YOURS, 0]
        leg = Line(start, corner, color=Palette.BODY, stroke_width=3)
        arrow = Arrow(corner, [X_ELBOW, hero.rect.get_bottom()[1] - 0.08, 0], buff=0, color=Palette.BODY, stroke_width=3, tip_length=0.22, max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=100.0)
        call = digits(n["call"], SIZE_BODY, Palette.BODY).next_to(leg, UP, buff=0.14)
        call.set_x(start[0] + 0.15 + call.width / 2)
        self.play(Create(leg, run_time=0.35), FadeIn(call, shift=RIGHT * 0.1, run_time=0.4))
        self.play(Create(arrow, run_time=0.35))
        self.wait(0.3)
        # the reference's word, in the reference's colour
        word_ref = digits(n["word"], SIZE_BODY, Palette.CORRECT)
        word_ref.move_to([X_WORD + word_ref.width / 2, Y_WORD, 0])
        self.play(AddTextLetterByLetter(word_ref, time_per_char=0.045))

        # 3 · your contract's word, the same string from the same loader, judged equal
        self.section(4, hold=1.2)
        word_yours = digits(n["word"], SIZE_BODY, Palette.EXACT)
        word_yours.move_to([word_ref.get_x(), Y_WORD - WORD_PITCH, 0])
        self.play(AddTextLetterByLetter(word_yours, time_per_char=0.045))
        tick = check_mark(size=0.4)
        equal = words(EQUAL, SIZE_BODY, Palette.CORRECT)
        judge = VGroup(tick, equal).arrange(DOWN, buff=0.14)
        judge.move_to([word_ref.get_right()[0] + 0.45 + judge.width / 2, Y_WORD - WORD_PITCH / 2, 0])
        assert judge.get_right()[0] <= X_RIGHT + 0.05, judge.get_right()[0]
        self.play(Create(tick, run_time=0.4), FadeIn(equal, shift=UP * 0.06, run_time=0.4))
        self.close(hold=4.0)

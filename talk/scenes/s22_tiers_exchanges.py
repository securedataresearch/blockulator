"""Slide 20, "The grades: exchanges and protocols": the audit's report card
for the exchanges, the lending protocols and the five incidents.

The same board as slide 19 (vocab.TierBoard): five bands S/A/B/C/F, the
rule as each band's legend, one chip per row of talk/scenes/data/tiers.json
(vocab.tiers()): the exchanges (a hollow square in white: integer-exact
arithmetic, the EXACT meaning), the protocols (a dot in SLATE, the
protocols' family colour) and the five incidents (a RED cross, the name in
its replay hue, vocab.protocol_colour). A chip carries the row's `fact`
as its label where the board fits with them (LABELLED names the tiers
whose chips are labelled; the policy falls back, tier by tier, to names
only when the board would not fit, and the scene records the policy used
in .label_policy); the rest of the facts are the notes'.

Four sections: rule (the empty board, chrome), exchanges (every chip of
kind "exchange" flies into its band), lenders (kind "protocol"),
incidents (kind "incident", last). Within a band the chips are packed first-fit
by width (the file's order is by kind, which the glyph carries). The
legend is vocab.TIER_RULE, the deck's one wording of the user's rule; the
file's .rule is its longer paraphrase, kept in numbers() for the notes
(the two would not fit: three bands' legends at two lines). The chips are
the data: self.key,
which the census does not count; the glyph budget is waived (README).
Every row's tier is one of S..F and every drawn fact is a row's fact
(check.py).
"""

from __future__ import annotations

from manim import DOWN, FadeIn, LaggedStart
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    SIZE_BODY,
    TIER_RULE,
    TIERS,
    DeckScene,
    Palette,
    TierBoard,
    chip,
    protocol_colour,
    tiers,
)

TITLE = "The grades: exchanges and protocols"
KINDS = ("exchange", "protocol", "incident")  # the sections' order
GLYPH = {"exchange": "square", "protocol": "dot", "incident": "cross"}
HUE = {"exchange": Palette.EXACT, "protocol": Palette.SLATE}  # an incident's name takes its replay hue; its cross is WRONG red
LABELLED = (("B", "C"), ("C",), ())  # label policies, tried in order: the tiers whose chips carry their fact
NONE = "none"  # an empty band's one chip
LITERALS: dict[str, str] = {}  # every digit on the slide is a value of numbers() (the rule's text and the rows' facts)


def numbers() -> dict:
    d = tiers()
    rows = [{"id": r["id"], "name": r["name"], "kind": r["kind"], "tier": r["tier"], "fact": r["fact"]} for r in d["rows"]]
    assert all(r["tier"] in TIERS and r["kind"] in KINDS for r in rows)
    incidents = [r for r in rows if r["kind"] == "incident"]
    assert all(r["tier"] == "F" for r in incidents) and len(incidents) == 5, [(r["name"], r["tier"]) for r in incidents]
    return {
        "rule": dict(d["rule"]),
        "rows": rows,
        "by_tier": {t: [r["id"] for r in rows if r["tier"] == t] for t in TIERS},
        "counts": {k: sum(1 for r in rows if r["kind"] == k) for k in KINDS},
    }


def make_chips(rows: list[dict], labelled: tuple[str, ...]) -> dict[str, list]:
    chips = {t: [] for t in TIERS}
    for r in rows:
        if r["kind"] == "incident":
            colour, glyph_colour = protocol_colour(r["name"]), Palette.WRONG
        else:
            colour = glyph_colour = HUE[r["kind"]]
        c = chip(r["name"], colour, r["fact"] if r["tier"] in labelled else None, glyph=GLYPH[r["kind"]], glyph_colour=glyph_colour)
        c.kind = r["kind"]
        chips[r["tier"]].append(c)
    for t in TIERS:
        if not chips[t]:
            c = chip(NONE, Palette.MUTED, None, glyph=None)
            c.kind = None
            chips[t].append(c)
    return chips


class TiersExchanges(DeckScene):
    SECTIONS = ("rule", "exchanges", "lenders", "incidents")

    def construct(self):
        n = numbers()
        board = None
        for policy in LABELLED:
            try:
                board = TierBoard(make_chips(n["rows"], policy), TIER_RULE, pack=True)  # the legend is the deck's one rule text (TIER_RULE); the file's longer paraphrase is in numbers() for the notes
            except AssertionError:
                continue
            self.label_policy = policy
            break
        assert board is not None, "the board does not fit even with names only"

        # 0 · the rule: title, the five bands, their letters and legends, chrome on the first frame
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.fix(board.chrome)
        self.key = board.key
        self.add(*[c for t in TIERS for c in board.chips[t] if c.kind is None])  # an empty band says "none" from the first frame
        self.wait(1.0)

        # 1–3 · the exchanges, the lenders, the incidents: each kind flies into its bands
        for i, kind in enumerate(KINDS, start=1):
            self.section(i, hold=0.8)
            group = [c for t in TIERS for c in board.chips[t] if c.kind == kind]
            assert group, kind
            self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.35, run_time=0.5, rate_func=ease_out_cubic) for c in group], lag_ratio=0.12))
        self.close()

"""Slide 20, "The grades: exchanges": the report card for the exchanges
(talk/scenes/data/grades.json, group "exchange"), as graded there by
scripts/tiers/grade.py (the rule is written once, in that script). The
scene grades nothing: it reads each row's tier, chip and fix and draws
them (check.py reads the JSON by a second route and compares the drawn
board). The lenders and the incidents are the next slide
(s23_tiers_lenders, which reuses make_chips()).

The same board as slide 19 (vocab.TierBoard), the five digit tiers: each
band's plain-word name in its colour in the left column, its legend (one
CAPTION line: vocab.GRADE_LEGEND, LITERALS under the user's claim) along
its top. A chip's glyph is its kind: an exchange a hollow square in white
(integer-exact arithmetic, the EXACT meaning), a lender a dot in SLATE (the
protocols' family colour), an incident a RED cross with the name in its
replay hue (vocab.protocol_colour); then "· " and the chip ("exact", "8.2
short"), and where the row has a fix, the fix in EMERALD after an arrow
(fixes.json is a draft). Every chip keeps its number. Within a band the
chips are packed first-fit by width; an empty band says "none". The chips'
size is the largest of POLICIES at which the board fits (.policy). The
chips are the data: self.key, which the census does not count; the glyph
budget is waived (README).

Two sections: rule (the empty board, chrome), grades (the exchanges fly
into their bands, best band first).
"""

from __future__ import annotations

from manim import DOWN, FadeIn, LaggedStart
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    GRADE_CLAIM,
    GRADE_LEGEND,
    GRADE_TIERS,
    SIZE_BODY,
    DeckScene,
    Palette,
    chip,
    fit_board,
    grades,
    protocol_colour,
)

TITLE = "The grades: exchanges"
KINDS = ("exchange",)  # grades.json's groups on this slide
BANDS = GRADE_TIERS[:5]  # the digit tiers; "lost money" is the lenders' slide
GLYPH = {"exchange": "square", "protocol": "dot", "incident": "cross"}
HUE = {"exchange": Palette.EXACT, "protocol": Palette.SLATE}  # an incident's name takes its replay hue; its cross is WRONG red
NONE = "none"  # an empty band's one chip
POLICIES = ({"size": 24}, {"size": 22}, {"size": 20})  # the chips' size, largest first, never below CAPTION; every number kept
LITERALS: dict[str, str] = {GRADE_LEGEND[t]: GRADE_CLAIM for t in BANDS}  # the legend's lines (the user's rule, in words)


def rows_of(kinds: tuple[str, ...], bands: tuple[str, ...]) -> dict:
    """numbers() for a report card of grades.json's groups `kinds` in `bands`."""
    g = grades()
    rows = [{"id": r["id"], "name": r["name"], "kind": r["group"], "tier": r["tier"], "chip": r["chip"], "fix": r["fix"]} for r in g["rows"] if r["group"] in kinds]
    assert all(r["tier"] in bands for r in rows), [(r["id"], r["tier"]) for r in rows if r["tier"] not in bands]
    assert all((r["chip"] is None) == (r["kind"] == "incident") for r in rows), [(r["id"], r["chip"]) for r in rows]
    return {
        "cap": g["cap"],
        "rule": {r["tier"]: r.get("digits_short_max") for r in g["rule"]},
        "rows": rows,
        "by_tier": {t: [r["id"] for r in rows if r["tier"] == t] for t in bands},
        "counts": {k: sum(1 for r in rows if r["kind"] == k) for k in kinds},
    }


def numbers() -> dict:
    return rows_of(KINDS, BANDS)


def make_chips(rows: list[dict], bands: tuple[str, ...], policy: dict) -> dict[str, list]:
    chips = {t: [] for t in bands}
    for r in rows:
        if r["kind"] == "incident":
            colour, glyph_colour = protocol_colour(r["name"]), Palette.WRONG
        else:
            colour = glyph_colour = HUE[r["kind"]]
        c = chip(r["name"], colour, r["chip"], glyph=GLYPH[r["kind"]], glyph_colour=glyph_colour, size=policy["size"], fix=r["fix"])
        c.row, c.kind = r["id"], r["kind"]
        chips[r["tier"]].append(c)
    for t in bands:
        if not chips[t]:
            c = chip(NONE, Palette.MUTED, None, glyph=None, size=policy["size"])
            c.row, c.kind = None, None
            chips[t].append(c)
    return chips


class TiersExchanges(DeckScene):
    SECTIONS = ("rule", "grades")

    def construct(self):
        n = numbers()
        board, self.policy = fit_board(lambda p: make_chips(n["rows"], BANDS, p), GRADE_LEGEND, BANDS, POLICIES, pack=True)
        self.board = board

        # 0 · the rule: title, the five bands, their names and legends, chrome on the first frame
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.fix(board.chrome)
        self.key = board.key
        self.add(*[c for t in BANDS for c in board.chips[t] if c.kind is None])  # an empty band says "none" from the first frame
        self.wait(1.0)

        # 1 · the grades: the exchanges, band by band, best first
        self.section(1, hold=0.8)
        for t in BANDS:
            group = [c for c in board.chips[t] if c.kind is not None]
            if group:
                self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.35, run_time=0.5, rate_func=ease_out_cubic) for c in group], lag_ratio=0.15))
                self.wait(0.2)
        self.close()

"""Slide 21, "The grades: lenders and incidents": the report card for the
lenders (talk/scenes/data/grades.json, group "protocol") in the five digit
tiers and the five incidents (group "incident") in the sixth band, "lost
money", as graded there by scripts/tiers/grade.py (the rule is written
once, in that script). The scene grades nothing: it reads each row's tier,
chip and fix and draws them (check.py reads the JSON by a second route and
compares the drawn board).

The board, the chips and the fit are slide 20's (s22_tiers_exchanges:
rows_of(), make_chips(), POLICIES): a lender a SLATE dot, name · chip and
the fix in EMERALD after an arrow; an incident a RED cross with its name in
its replay hue and no chip (its band's legend, "a rounding step that lost
money", says what it did). Every chip keeps its number. An empty band says
"none". LITERALS: the six legend lines, under the user's claim.

Three sections: rule (the empty board, chrome), grades (the lenders fly
into their bands, best band first), incidents (the lost-money band last).
"""

from __future__ import annotations

from manim import DOWN, FadeIn, LaggedStart
from manim.utils.rate_functions import ease_out_cubic

from s22_tiers_exchanges import POLICIES, make_chips, rows_of
from vocab import (
    GRADE_CLAIM,
    GRADE_LEGEND,
    GRADE_TIERS,
    SIZE_BODY,
    DeckScene,
    Palette,
    fit_board,
)

TITLE = "The grades: lenders and incidents"
KINDS = ("protocol", "incident")  # grades.json's groups on this slide
BANDS = GRADE_TIERS  # all six: the incidents are "lost money"
LITERALS: dict[str, str] = {GRADE_LEGEND[t]: GRADE_CLAIM for t in BANDS}  # the legend's lines (the user's rule, in words)


def numbers() -> dict:
    n = rows_of(KINDS, BANDS)
    assert all((r["tier"] == "lost money") == (r["kind"] == "incident") for r in n["rows"]), [(r["id"], r["tier"]) for r in n["rows"]]
    return n


class TiersLenders(DeckScene):
    SECTIONS = ("rule", "grades", "incidents")

    def construct(self):
        n = numbers()
        board, self.policy = fit_board(lambda p: make_chips(n["rows"], BANDS, p), GRADE_LEGEND, BANDS, POLICIES, pack=True)
        self.board = board

        # 0 · the rule: title, the six bands, their names and legends, chrome on the first frame
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.fix(board.chrome)
        self.key = board.key
        self.add(*[c for t in BANDS for c in board.chips[t] if c.kind is None])  # an empty band says "none" from the first frame
        self.wait(1.0)

        # 1 · the grades: the lenders, band by band, best first; 2 · the incidents, last
        for i, kind in ((1, "protocol"), (2, "incident")):
            self.section(i, hold=0.8)
            for t in BANDS:
                group = [c for c in board.chips[t] if c.kind == kind]
                if group:
                    self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.35, run_time=0.5, rate_func=ease_out_cubic) for c in group], lag_ratio=0.15))
                    self.wait(0.2)
        self.close()

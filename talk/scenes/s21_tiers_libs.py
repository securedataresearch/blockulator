"""Slide 19, "The grades: libraries": the report card for the 13 libraries
in talk/scenes/data/grades.json (group "library"), as graded there by
scripts/tiers/grade.py (the rule is written once, in that script). The
scene grades nothing: it reads each row's tier, chip and fix and draws
them (check.py reads the JSON by a second route and compares the drawn
board).

Five bands, the digit tiers in grade.py's order (vocab.TierBoard): the
band's plain-word name in its colour in the left column, its legend (one
CAPTION line, the rule's ceiling in words: vocab.GRADE_LEGEND, LITERALS
under the user's claim) along its top. The sixth tier, "lost money", holds
the incidents and is on the next slide. One chip per library in the
file's order: its family colour, the name, "· " and the chip ("exact",
"0.6 short"), and where the row has a fix, the fix in EMERALD after an
arrow (fixes.json is a draft: talk/scenes/data/fixes.json). A band with no
library says "none". The chips are the data, like a chart's key: they live
in self.key, which the census does not count; the glyph budget is waived
for this slide (README). The chips' size is the largest of SIZE_CHIP down
to CAPTION at which the board fits (.policy records it).

Three sections: rule (the empty board, chrome), grades (every library but
ours flies in, band by band, best first), blockulator (BL127 and BL19 last,
under halos).
"""

from __future__ import annotations

from manim import DOWN, FadeIn, LaggedStart, VGroup
from manim.utils.rate_functions import ease_out_cubic

from vocab import (
    GRADE_CLAIM,
    GRADE_LEGEND,
    GRADE_TIERS,
    SIZE_BODY,
    DeckScene,
    Palette,
    chip,
    colour_of,
    fit_board,
    grades,
    halo,
    talk_libs,
)

TITLE = "The grades: libraries"
GROUP = "library"
BANDS = GRADE_TIERS[:5]  # the digit tiers; "lost money" holds the incidents (slide 20)
NONE = "none"  # an empty band's one chip
POLICIES = ({"size": 24}, {"size": 22}, {"size": 20})  # the chips' size, largest first; never below CAPTION
LITERALS: dict[str, str] = {GRADE_LEGEND[t]: GRADE_CLAIM for t in BANDS}  # the legend's lines (the user's rule, in words)


def numbers() -> dict:
    g = grades()
    rows = [{"id": r["id"], "name": r["name"], "tier": r["tier"], "chip": r["chip"], "fix": r["fix"]} for r in g["rows"] if r["group"] == GROUP]
    assert all(r["tier"] in BANDS and r["chip"] for r in rows), [(r["id"], r["tier"]) for r in rows if r["tier"] not in BANDS]
    return {
        "cap": g["cap"],
        "rule": {r["tier"]: r.get("digits_short_max") for r in g["rule"]},
        "rows": rows,
        "by_tier": {t: [r["id"] for r in rows if r["tier"] == t] for t in BANDS},
    }


def make_chips(rows: list[dict], policy: dict) -> dict[str, list]:
    lib = talk_libs()
    chips = {t: [] for t in BANDS}
    for r in rows:
        c = chip(r["name"], colour_of(lib[r["id"]]), r["chip"], size=policy["size"], fix=r["fix"])
        c.row, c.ours = r["id"], bool(lib[r["id"]].get("ours"))
        chips[r["tier"]].append(c)
    for t in BANDS:
        if not chips[t]:
            c = chip(NONE, Palette.MUTED, None, glyph=None, size=policy["size"])
            c.row, c.ours = None, False
            chips[t].append(c)
    return chips


class TiersLibs(DeckScene):
    SECTIONS = ("rule", "grades", "blockulator")

    def construct(self):
        n = numbers()
        board, self.policy = fit_board(lambda p: make_chips(n["rows"], p), GRADE_LEGEND, BANDS, POLICIES)
        self.board = board

        # 0 · the rule: title, the five bands, their names and legends, chrome on the first frame
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        self.fix(board.chrome)
        self.key = board.key
        self.add(*[c for t in BANDS for c in board.chips[t] if c.row is None])  # an empty band says "none" from the first frame
        self.wait(1.0)

        # 1 · the grades: every library but ours, band by band, best first
        self.section(1, hold=0.6)
        for t in BANDS:
            group = [c for c in board.chips[t] if c.row is not None and not c.ours]
            if group:
                self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.35, run_time=0.5, rate_func=ease_out_cubic) for c in group], lag_ratio=0.18))
                self.wait(0.2)

        # 2 · Blockulator last, under halos
        self.section(2, hold=1.0)
        ours = [c for t in BANDS for c in board.chips[t] if c.ours]
        glows = VGroup(*[halo(c.glyph.get_center(), c.name.get_color(), radius=0.12, layers=4, spread=2.2, opacity=0.3) for c in ours])
        self.add(glows)
        self.bring_to_back(glows)
        self.play(LaggedStart(*[FadeIn(VGroup(g, c), shift=DOWN * 0.35, scale=1.15, run_time=0.7, rate_func=ease_out_cubic) for g, c in zip(glows, ours)], lag_ratio=0.3))
        self.close()

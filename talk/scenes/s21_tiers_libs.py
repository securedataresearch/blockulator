"""Slide 19, "The grades: libraries": the audit's report card for the 17
libraries, graded at render time from the deck's own data.

Five bands S/A/B/C/F (vocab.TierBoard), the rule as each band's legend
(vocab.TIER_RULE, the user's), the libraries as chips in their family
colour with one measured label each. The grades are computed here, never
typed (check.py recomputes them by a second route from the same JSON):

- S, correctly rounded: a Blockulator library (ours) whose sweep rows
  (docs/benchmarks/sweep.json) sum to 0 misrounded. Label: "0 misrounded".
- A, about 30 digits: the least of the library's median correct digits at
  N = 10,000 across the ladder slide's three scenarios (s08_ladder.SCENARIOS,
  docs/benchmarks/ladder.json) is at least A_MIN_DIGITS. Label: that number.
- B, 18 decimals as documented: an 18-decimal library (family "wad") whose
  compound-ladder median at N = 10,000 is at least B_MIN_DIGITS and which
  returns a value (a zero below 10^-18 is the documented floor) on every
  exp probe of the cliff slide (s09_cliff's range of edges.json) inside its
  domain; a ParamOutOfRange revert (the argument does not fit the type:
  PRBMath UD and a negative input) is outside the domain. Label: the
  registry's decimals.
- C, 10 digits or more but fewer than the format holds: the ladder minimum
  (or, for Aave and Morpho, the live median from
  docs/benchmarks/accrual-deployed.json, as s10 computes it) is at least
  F_BELOW_DIGITS.
- F (the user's rule, 2026-10-30: "<10 digits is F tier, and balancer
  reverts? so i guess F tier"): a revert inside the domain (label "reverts
  from exp(−42)", the first such probe), or fewer than F_BELOW_DIGITS
  digits by the same measure as C.

Three sections: rule (the empty board, chrome), grades (C, B and A chips
fly in), blockulator (the two S chips, last, under halos). The chips are
the data, like a chart's key: they live in self.key, which the census
does not count; the glyph budget is waived for this slide (README).
"""

from __future__ import annotations

import statistics

from manim import DOWN, FadeIn, LaggedStart, VGroup
from manim.utils.rate_functions import ease_out_cubic

from s08_ladder import SCENARIOS as LADDER_SCENARIOS
from s09_cliff import ARG_HI, ARG_LO, RANGE_REASON
from s09_cliff import OP as CLIFF_OP
from vocab import (
    SIZE_BODY,
    TIER_RULE,
    TIER_RULE_CLAIM,
    TIERS,
    DeckScene,
    Palette,
    TierBoard,
    chip,
    colour_of,
    edges,
    halo,
    ladder,
    ladder_median,
    live,
    _load,
    talk_libs,
    words,
)

TITLE = "The grades: libraries"
A_MIN_DIGITS = 25  # the A rule: at least this many correct digits at N = 10,000 in every scenario the library runs
B_MIN_DIGITS = 14  # the B rule: an 18-decimal library keeps at least this at N = 10,000 on the compound ladder
F_BELOW_DIGITS = 10  # the user's rule: under 10 correct digits is F
COMPOUND = LADDER_SCENARIOS[0]
LIVE_LABELLED = ("aave", "morpho")  # the protocols measured live (s10): labelled by their live median
NONE = "none"  # the F band's one chip: a library is not an incident
MINUS = "−"

LITERALS: dict[str, str] = {TIER_RULE[t]: TIER_RULE_CLAIM for t in ("A", "B", "C", "F")}  # the legend's four lines with digits


def fmt(d: float) -> str:
    return str(int(d)) if float(d).is_integer() else str(d)


def numbers() -> dict:
    lib = talk_libs()
    N = ladder(COMPOUND)["N"][-1]
    # the ladder: median digits at the last N per scenario, the minimum across the talk's three
    scen = {sid: ladder(sid)["scenario"]["summary"] for sid in LADDER_SCENARIOS}
    ladder_min: dict[str, float | None] = {}
    compound: dict[str, float | None] = {}
    for lid in lib:
        vals = [ladder_median(scen[sid].get(lid, {}).get(str(N))) for sid in LADDER_SCENARIOS]
        present = [v for v in vals if v is not None]
        ladder_min[lid] = min(present) if present else None
        compound[lid] = vals[0]
    # the sweep: misrounded summed over every row of ours
    sw = _load("docs/benchmarks/sweep.json")["rows"]
    misrounded = {lid: sum(r["misrounded"] for r in sw if r["lib"] == lid) for lid in lib if lib[lid].get("ours")}
    # the cliff: the first probe in the range where an 18-decimal library reverts inside its domain
    probes = [p for p in edges(CLIFF_OP)["probes"] if len(p["args"]) == 1 and ARG_LO <= float(p["args"][0]) <= ARG_HI]
    revert_from: dict[str, str] = {}
    for lid in lib:
        if lib[lid]["family"] != "wad":
            continue
        for p in probes:
            c = p["cells"][lid]
            if c.get("unsupported"):
                continue  # no exp: the probe is outside what the library offers
            if c.get("reverted") and not str(c.get("reasonName", "")).startswith(RANGE_REASON):
                revert_from[lid] = p["args"][0]
                break
    # the live data: the deployed median per protocol
    live_median = {}
    for pid in LIVE_LABELLED:
        pts = [float(c["truth"][c["primaryTruth"]]["deployed"]["digitsInterest"]) for c in live() if c["protocol"] == pid]
        live_median[pid] = round(statistics.median(pts), 1)
    rows = []
    for lid, rec in lib.items():
        if rec.get("ours") and misrounded[lid] == 0:
            tier, label = "S", f"{misrounded[lid]} misrounded"
        elif ladder_min[lid] is not None and ladder_min[lid] >= A_MIN_DIGITS:
            tier, label = "A", f"{fmt(ladder_min[lid])} digits"
        elif rec["family"] == "wad" and compound[lid] is not None and compound[lid] >= B_MIN_DIGITS and lid not in revert_from:
            tier, label = "B", None  # the legend carries the grade ("18 decimals, as documented"); seven labels would not fit
        elif lid in revert_from:
            tier, label = "F", f"reverts from exp({revert_from[lid].replace('-', MINUS)})"
        elif lid in live_median:
            digits = live_median[lid]
            tier, label = ("F" if digits < F_BELOW_DIGITS else "C"), f"{fmt(digits)} digits live"
        else:
            assert ladder_min[lid] is not None, lid
            tier, label = ("F" if ladder_min[lid] < F_BELOW_DIGITS else "C"), f"{fmt(ladder_min[lid])} digits"
        rows.append({"id": lid, "label": rec["label"], "family": rec["family"], "tier": tier, "chip": label, "ladder_min": ladder_min[lid], "compound": compound[lid]})
    by_tier = {t: [r["id"] for r in rows if r["tier"] == t] for t in TIERS}
    return {
        "N": N,
        "rows": rows,
        "by_tier": by_tier,
        "misrounded": misrounded,
        "revert_from": revert_from,
        "live_median": live_median,
    }


class TiersLibs(DeckScene):
    SECTIONS = ("rule", "grades", "blockulator")

    def construct(self):
        n = numbers()
        lib = talk_libs()
        rows = {r["id"]: r for r in n["rows"]}
        # the chips, in registry order within a band (ours first, as the registry lists them)
        chips = {t: [] for t in TIERS}
        for lid in lib:
            r = rows[lid]
            chips[r["tier"]].append(chip(r["label"], colour_of(lib[lid]), r["chip"]))
        if not chips["F"]:
            chips["F"].append(chip(NONE, Palette.MUTED, None, glyph=None))

        # 0 · the rule: title, the five bands, their letters and legends, all chrome on the first frame
        self.section(0)
        self.fix(self.title(TITLE, SIZE_BODY, Palette.TEXT))
        board = TierBoard(chips, TIER_RULE)
        self.fix(board.chrome)
        self.key = board.key
        self.wait(1.0)

        # 1 · the grades: C, B and A fly into their bands, the F band's "none" with C
        self.section(1, hold=0.6)
        for t in ("C", "F", "B", "A"):
            group = board.chips[t]
            if not group:
                continue
            self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.35, run_time=0.5, rate_func=ease_out_cubic) for c in group], lag_ratio=0.18))
            self.wait(0.3)

        # 2 · Blockulator last, under halos
        self.section(2, hold=1.0)
        glows = VGroup(*[halo(c.glyph.get_center(), c.name.get_color(), radius=0.12, layers=4, spread=2.2, opacity=0.3) for c in board.chips["S"]])
        self.add(glows)
        self.bring_to_back(glows)
        self.play(LaggedStart(*[FadeIn(VGroup(g, c), shift=DOWN * 0.35, scale=1.15, run_time=0.7, rate_func=ease_out_cubic) for g, c in zip(glows, board.chips["S"])], lag_ratio=0.3))
        self.close()

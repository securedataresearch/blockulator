#!/usr/bin/env python3
"""The report card's grades, from the measurements alone (the user, 2026-10-30:
"this all should be purely data driven"; "both must pass").

Inputs (each written by its own measurement script):
  docs/benchmarks/lost.json                      libraries   (scripts/sweep/lost.py, on typical inputs)
  talk/scenes/data/tiers-worst-exchanges.json    exchanges   (scripts/tiers/measure_exchanges.py, normal range)
  talk/scenes/data/tiers-worst-protocols.json    lenders     (scripts/tiers/measure_protocols.py, live envelope)
  talk/scenes/data/tiers.json                    names, kinds, sources, the five incidents

The rule, written once (RULE below; the user's blend, 2026-10-30): a row is
"correctly rounded" when every normal input is within a unit of the exact
value in its stated direction; otherwise its tier is set by one number,

  digits short = worst over normal inputs of  max(0, min(format digits there, 18) - digits held)

where digits held = -log10(relative error) and format digits = log10(|exact| / unit).
Where a format holds 18 digits or fewer this is exactly the digits lost (no
penalty for the format's floor); where it holds more, it is the digits short of
18 (no penalty for not using a wide format's full width). 18 is an 18-decimal
word's precision at 1. The five incidents are not graded on digits: they sit
in their own band, "lost money".

    uv run scripts/tiers/grade.py          # writes talk/scenes/data/grades.json and prints the table
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# (label on the slide, digits-short ceiling); "correctly rounded" is decided by correctly_rounded, not by a ceiling
CAP = 18
RULE = [
    ("correctly rounded", None),
    ("within a digit", 1.0),
    ("a few digits", 5.0),
    ("many digits", 12.0),
    ("most digits lost", math.inf),
]
INCIDENTS = "lost money"


def load(p: str) -> dict:
    return json.loads((ROOT / p).read_text())


def tier_of(correctly_rounded: bool, short: float) -> str:
    if correctly_rounded:
        return RULE[0][0]
    for label, ceiling in RULE[1:]:
        if short <= ceiling:
            return label
    raise AssertionError("the last tier takes everything")


def rows() -> list[dict]:
    out = []
    lost = load("docs/benchmarks/lost.json")
    libs = lost["libraries"]
    reg = load("static/data/libraries.json")
    items = reg if isinstance(reg, list) else reg.get("libraries", reg)
    items = items if isinstance(items, list) else list(items.values())
    label = {l["id"]: l["label"] for l in items}
    for lid, rec in libs.items():
        if lid == "blockulator":
            continue  # BlockulatorWad is not in the talk
        w = rec["grade"]
        out.append({"id": lid, "name": label.get(lid, lid), "group": "library", "digits_lost": float(w["digits_lost"]),
                    "short18": float(rec["short18"]["value"] if isinstance(rec.get("short18"), dict) else rec["short18"]),
                    # strict: every function within a unit in its stated direction on every typical input (not digits_lost rounding to 0.0)
                    "correctly_rounded": all(f.get("correctly_rounded") for f in rec["functions"].values()) if rec.get("functions") else bool(rec["correctly_rounded"]),
                    "where": w.get("function"), "source": "docs/benchmarks/lost.json"})
    tiers = {r["id"]: r for r in load("talk/scenes/data/tiers.json")["rows"]}
    for path, group in (("talk/scenes/data/tiers-worst-exchanges.json", "exchange"), ("talk/scenes/data/tiers-worst-protocols.json", "protocol")):
        for rid, r in load(path)["rows"].items():
            t = tiers.get(rid, {})
            sh = r["short18"]
            out.append({"id": rid, "name": t.get("short", t.get("name", rid)), "group": group, "digits_lost": float(r["digits_lost"]),
                        "short18": float(sh["value"] if isinstance(sh, dict) else sh), "correctly_rounded": bool(r["correctly_rounded"]),
                        "where": r.get("worst_input") or r.get("worst_input_units"), "source": path})
    for rid, t in tiers.items():
        if t["kind"] == "incident":
            out.append({"id": rid, "name": t["name"], "group": "incident", "digits_lost": None, "short18": None, "correctly_rounded": False, "where": t["fact"], "source": t["source"]["ref"]})
    fixes = load("talk/scenes/data/fixes.json")["fixes"]
    for r in out:
        r["fix"] = fixes.get(r["id"])
        r["tier"] = INCIDENTS if r["group"] == "incident" else tier_of(r["correctly_rounded"], r["short18"])
        r["chip"] = None if r["short18"] is None else ("exact" if r["correctly_rounded"] else f"{r['short18']:.1f} short")
    return out


def main() -> None:
    rs = rows()
    doc = {"_doc": __doc__.split("\n\n")[0], "cap": CAP, "rule": [{"tier": l, "digits_short_max": (None if c in (None, math.inf) else c)} for l, c in RULE] + [{"tier": INCIDENTS}],
           "rows": rs}
    (ROOT / "talk/scenes/data/grades.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    order = [l for l, _ in RULE] + [INCIDENTS]
    for t in order:
        names = [f"{r['name']} {r['chip'] or ''}".strip() for r in rs if r["tier"] == t]
        print(f"{t:18s} | " + " · ".join(names))


if __name__ == "__main__":
    main()

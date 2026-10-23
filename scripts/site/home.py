#!/usr/bin/env python3
"""The home page's data: every library, every section, one small file.

    uv run scripts/site/home.py          # write static/data/home.json
    uv run scripts/site/home.py --check  # fail if it is stale

Reads the measured datasets (docs/benchmarks/*.json through static/data/) and
the library registry (static/data/libraries.json), and keeps only what the home
page's tables and charts show. Each section is a list of tidy rows (one row per
library and measure), so the Zola table and the Plot chart read the same rows.
A library is in a section when the dataset has a number for it; a missing cell
stays missing (no row), never a zero.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "static" / "data"
OUT = DATA / "home.json"
GAS_OPS = ["add", "mul", "div", "exp", "ln", "pow", "sqrt"]
ACCRUAL = "accrual-continuous"
ACCRUAL_COLS = [1, 10, 100, 365, 1000, 10000]


def load(name: str):
    return json.loads((DATA / name).read_text())


def num(x):
    return None if x is None else float(x)


def gas_section(reg: dict) -> dict:
    g127, g19 = load("gas.json"), load("fp19/gas.json")

    def median(g, op, form):
        o = g["ops"].get(op)
        if not o:
            return None
        s = (o.get("typical") or o)["summary"].get(form)
        return s["median"] if s else None

    rows = []
    for lib in reg:
        for op in GAS_OPS:
            v = median(g19, op, "lib") if lib == "fp19" else median(g127, op, "lib" if lib == "fp127" else lib)
            if v is not None:
                rows.append({"lib": lib, "op": op, "gas": v})
    typical = [op for op in GAS_OPS if "typical" in g127["ops"][op]]
    return {"ops": GAS_OPS, "typical": typical, "rows": rows}


def accrual_section(reg: dict) -> dict:
    d = load("ladder.json")
    s = next(s for s in d["scenarios"] if s["id"] == ACCRUAL)
    cells = s["inputs"][0]["cells"]
    rows = [{"lib": lib, "n": n, "digits": float(c["digitsCapped"])}
            for lib in reg if lib in cells
            for n in d["ladder"] if (c := cells[lib].get(str(n))) and "digitsCapped" in c]
    return {"scenario": ACCRUAL, "title": s["title"], "n": d["ladder"], "cols": ACCRUAL_COLS, "rows": rows}


def ladder_section(reg: dict) -> dict:
    d = load("ladder.json")
    rows, scen = [], []
    for s in d["scenarios"]:
        scen.append({"id": s["id"], "title": s["title"]})
        for lib in reg:
            sm = s["summary"].get(lib)
            if not sm:
                continue
            n = max((int(k) for k, v in sm.items() if v.get("digits")), default=None)
            if n is not None:
                rows.append({"lib": lib, "scenario": s["id"], "digits": num(sm[str(n)]["digits"]["median"]), "n": n})
            else:
                unsupported = s["ops"].get(lib) == ["unsupported"]
                rows.append({"lib": lib, "scenario": s["id"], "digits": None, "status": "unsupported" if unsupported else "reverts"})
    return {"scenarios": scen, "rows": rows}


def edges_section(reg: dict) -> dict:
    d = load("edges.json")
    acc = {lib: {"digits": [], "zero": 0, "reverts": 0, "unsupported": 0, "range": 0} for lib in reg}
    probes = 0
    for op in d["ops"]:
        for p in op["probes"]:
            probes += 1
            for lib, c in p["cells"].items():
                if lib not in acc:
                    continue
                a = acc[lib]
                if c.get("range"):
                    a["range"] += 1
                elif c.get("unsupported"):
                    a["unsupported"] += 1
                elif c.get("reverted"):
                    a["reverts"] += 1
                elif c.get("zero"):
                    a["zero"] += 1
                    a["digits"].append(0)
                else:
                    a["digits"].append(min(int(c["digits"]), 72))
    rows = []
    for lib, a in acc.items():
        if not a["digits"]:
            continue
        rows.append({"lib": lib, "median": statistics.median(a["digits"]), "min": min(a["digits"]), "computed": len(a["digits"]),
                     "zero": a["zero"], "reverts": a["reverts"], "range": a["range"], "unsupported": a["unsupported"], "digits": a["digits"]})
    return {"probes": probes, "ops": len(d["ops"]), "rows": rows}


def wad_section(reg: dict) -> dict:
    d = load("wad.json")
    wrong_somewhere = {r["function"] for r in d["rows"] if r["lib"] != "blockulator" and r["wrongWei"]}
    fns = list(dict.fromkeys(r["function"] for r in d["rows"] if r["lib"] == "blockulator" and r["function"] in wrong_somewhere))
    rows = [{"lib": r["lib"], "fn": r["function"], "pct": round(r["wrongWeiPct"], 2), "wrong": r["wrongWei"], "n": r["valued"], "maxWei": r.get("maxWei")}
            for lib in reg for r in d["rows"] if r["lib"] == lib and r["function"] in fns]
    ours = [r for r in d["rows"] if r["lib"] == "blockulator"]
    exact = sorted({r["function"] for r in d["rows"] if r["lib"] != "blockulator"} - wrong_somewhere)
    return {"functions": fns, "exact": exact, "results": sum(r["n"] for r in ours), "wrong": sum(r["wrongWei"] for r in ours),
            "functionsTotal": len(ours), "rows": rows}


# ---- the tables: the same rows, laid out for the template (it only loops; a cell is a string or null) ----

KINDS = [("float", "Floating point"), ("fixed", "Fixed point")]


def head(l: dict) -> dict:
    return {k: l[k] for k in ("id", "label", "long", "family")} | {"ours": bool(l.get("ours"))}


def grouped(libs: list[dict], rows: list[dict], cells) -> list[dict]:
    """Row groups by kind, floating point first, a library only where the section has a number for it."""
    have = {r["lib"] for r in rows}
    return [{"name": name, "rows": [head(l) | {"cells": cells(l)} for l in libs if l["kind"] == kind and l["id"] in have]}
            for kind, name in KINDS if any(l["kind"] == kind and l["id"] in have for l in libs)]


def tables(out: dict, libs: list[dict]) -> None:
    g = out["gas"]
    by = {(r["lib"], r["op"]): r["gas"] for r in g["rows"]}
    g["table"] = {"cols": ["digits"] + [o + ("ᵗ" if o in g["typical"] else "") for o in g["ops"]],
                  "groups": grouped(libs, g["rows"], lambda l: [str(l["digits"])] + [f"{by[l['id'], o]:,}" if (l["id"], o) in by else None for o in g["ops"]])}

    a = out["accrual"]
    by = {(r["lib"], r["n"]): r["digits"] for r in a["rows"]}
    a["table"] = {"cols": [f"{n:,} {'day' if n == 1 else 'days'}" for n in a["cols"]],
                  "groups": grouped(libs, a["rows"], lambda l: [f"{by[l['id'], n]:.1f}" if (l["id"], n) in by else None for n in a["cols"]])}

    w = out["wad"]
    by = {(r["lib"], r["fn"]): r for r in w["rows"]}
    cols = [l for l in libs if any(r["lib"] == l["id"] for r in w["rows"])]

    def wcell(l, f):
        r = by.get((l["id"], f))
        return None if not r else f"0 of {r['n']:,}" if l.get("ours") else "0" if not r["wrong"] else f"{round(r['pct'])}%"
    w["table"] = {"cols": [head(l) for l in cols], "rows": [{"fn": f, "cells": [wcell(l, f) for l in cols]} for f in w["functions"]]}

    ld = out["ladder"]
    by = {(r["lib"], r["scenario"]): r for r in ld["rows"]}
    colgroups = [{"name": name, "cols": [head(l) for l in libs if l["kind"] == kind and any(r["lib"] == l["id"] for r in ld["rows"])]} for kind, name in KINDS]
    order = [c for cg in colgroups for c in cg["cols"]]

    def lcell(c, s):
        r = by.get((c["id"], s["id"]))
        if not r or r["digits"] is None:
            return {"v": None, "why": r["status"] if r else "not measured"}
        return {"v": f"{r['digits']:.1f}", "h": round(r["digits"] / 72, 3), "ours": c["ours"]}
    ld["table"] = {"colgroups": [cg | {"span": len(cg["cols"])} for cg in colgroups], "cols": order,
                   "rows": [{"id": s["id"], "title": s["title"], "cells": [lcell(c, s) for c in order]} for s in ld["scenarios"]]}

    e = out["edges"]
    by = {r["lib"]: r for r in e["rows"]}
    e["table"] = {"cols": ["probes computed", "median digits", "fewest", "went to zero", "reverted", "out of range", "no such op"],
                  "groups": grouped(libs, e["rows"], lambda l: [f"{by[l['id']][k]:g}" for k in ("computed", "median", "min", "zero", "reverts", "range", "unsupported")])}


def build() -> dict:
    libs = load("libraries.json")["libraries"]
    reg = {l["id"]: l for l in libs}
    out = {"_doc": "Generated by scripts/site/home.py (make home-data) from the measured datasets; do not edit.",
           "gas": gas_section(reg), "accrual": accrual_section(reg), "ladder": ladder_section(reg),
           "edges": edges_section(reg), "wad": wad_section(reg)}
    used = {r["lib"] for sec in ("gas", "accrual", "ladder", "edges", "wad") for r in out[sec]["rows"]}
    out["libraries"] = [l for l in libs if l["id"] in used]
    tables(out, out["libraries"])
    return out


def main(argv: list[str]) -> int:
    text = json.dumps(build(), separators=(",", ":")) + "\n"
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text() != text:
            print("stale (run make home-data): static/data/home.json")
            return 1
        print("home data is current")
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

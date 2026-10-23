#!/usr/bin/env python3
"""The site's chart data: every library, every section, small files.

    uv run scripts/site/home.py          # write static/data/home.json and pages.json
    uv run scripts/site/home.py --check  # fail if either is stale

home.json feeds the home page; pages.json the inner pages' charts (the ladder's
steps per scenario, the edges per op, the gas per op, each library's ops).

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
PAGES = DATA / "pages.json"
CORE_OPS = ["add", "mul", "div", "exp", "ln", "pow", "sqrt"]  # first, in this order; then every op three other libraries offer
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

    def value(lib, op):
        return median(g19, op, "lib") if lib == "fp19" else median(g127, op, "lib" if lib == "fp127" else lib)

    offered = {op: [lib for lib in reg if value(lib, op) is not None] for op in g127["ops"]}
    ops = CORE_OPS + sorted((op for op, libs in offered.items() if sum(not reg[l].get("ours") for l in libs) >= 3 and op not in CORE_OPS), key=lambda o: (-len(offered[o]), o))
    rows = [{"lib": lib, "op": op, "gas": value(lib, op)} for lib in reg for op in ops if value(lib, op) is not None]
    typical = [op for op in ops if "typical" in g127["ops"][op]]
    return {"ops": ops, "typical": typical, "rows": rows}


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
    # every function another library offers: the ones they get wrong first, then the ones every library gets exact
    offered = {r["function"] for r in d["rows"] if r["lib"] != "blockulator"}
    ours_order = [r["function"] for r in d["rows"] if r["lib"] == "blockulator" and r["function"] in offered]
    fns = list(dict.fromkeys([f for f in ours_order if f in wrong_somewhere] + ours_order))
    rows = [{"lib": r["lib"], "fn": r["function"], "pct": round(r["wrongWeiPct"], 2), "wrong": r["wrongWei"], "n": r["valued"], "maxWei": r.get("maxWei")}
            for lib in reg for r in d["rows"] if r["lib"] == lib and r["function"] in fns]
    ours = [r for r in d["rows"] if r["lib"] == "blockulator"]
    exact = sorted({r["function"] for r in d["rows"] if r["lib"] != "blockulator"} - wrong_somewhere)
    return {"functions": fns, "exact": exact, "results": sum(r["n"] for r in ours), "wrong": sum(r["wrongWei"] for r in ours),
            "functionsTotal": len(ours), "rows": rows}


# ---- the tables: the same rows, laid out for the template (it only loops; a cell is a string or null) ----

KINDS = [("float", "Floating point"), ("fixed", "Fixed point")]


def head(l: dict) -> dict:
    return {k: l[k] for k in ("id", "label", "short", "long", "family")} | {"ours": bool(l.get("ours"))}


def grouped(libs: list[dict], rows: list[dict], cells) -> list[dict]:
    """Row groups by kind, floating point first, a library only where the section has a number for it."""
    have = {r["lib"] for r in rows}
    return [{"name": name, "rows": [head(l) | {"cells": cells(l)} for l in libs if l["kind"] == kind and l["id"] in have]}
            for kind, name in KINDS if any(l["kind"] == kind and l["id"] in have for l in libs)]


def libcols(libs: list[dict], have: set, rows: list[dict], cell) -> dict:
    """A table whose columns are libraries, grouped floating point | fixed point; rows are {key, label, href?};
    cell(library, row) gives {v (text or None), h (shade 0..1, optional), why (hover, optional)}."""
    groups = [{"name": name, "cols": [head(l) for l in libs if l["kind"] == kind and l["id"] in have]} for kind, name in KINDS]
    groups = [g | {"span": len(g["cols"])} for g in groups if g["cols"]]
    cols = [c for g in groups for c in g["cols"]]
    return {"colgroups": groups, "cols": cols,
            "rows": [r | {"cells": [cell(c, r) | {"ours": c["ours"]} for c in cols]} for r in rows]}


def tables(out: dict, libs: list[dict]) -> None:
    g = out["gas"]
    by = {(r["lib"], r["op"]): r["gas"] for r in g["rows"]}
    rows = [{"key": "digits", "label": "digits at 1", "unit": True}] + [{"key": o, "label": o + ("ᵗ" if o in g["typical"] else ""), "code": True} for o in g["ops"]]

    def gcell(c, r):
        if r["key"] == "digits":
            return {"v": str(next(l["digits"] for l in libs if l["id"] == c["id"]))}
        v = by.get((c["id"], r["key"]))
        return {"v": f"{v:,}" if v is not None else None, "why": f"{c['long']}: {r['key']}, median gas per call" if v is not None else "not offered"}
    g["table"] = libcols(libs, {r["lib"] for r in g["rows"]}, rows, gcell)

    a = out["accrual"]
    by = {(r["lib"], r["n"]): r["digits"] for r in a["rows"]}
    a["table"] = {"cols": [f"{n:,} {'day' if n == 1 else 'days'}" for n in a["cols"]],
                  "groups": grouped(libs, a["rows"], lambda l: [f"{by[l['id'], n]:.1f}" if (l["id"], n) in by else None for n in a["cols"]])}

    w = out["wad"]
    by = {(r["lib"], r["fn"]): r for r in w["rows"]}

    def wcell(c, r):
        x = by.get((c["id"], r["key"]))
        if not x:
            return {"v": None, "why": "not offered"}
        v = f"0 of {x['n']:,}" if c["ours"] else "0" if not x["wrong"] else f"{round(x['pct'])}%"
        return {"v": v, "why": f"{c['long']}: {x['wrong']:,} of {x['n']:,} results off by a wei or more"}
    w["table"] = libcols(libs, {r["lib"] for r in w["rows"]}, [{"key": f, "label": f, "code": True} for f in w["functions"]], wcell)

    ld = out["ladder"]
    by = {(r["lib"], r["scenario"]): r for r in ld["rows"]}

    def lcell(c, r):
        x = by.get((c["id"], r["key"]))
        if not x or x["digits"] is None:
            return {"v": None, "why": x["status"] if x else "not measured"}
        return {"v": f"{x['digits']:.1f}", "h": round(x["digits"] / 72, 3), "why": f"{c['long']}: median digits after {x['n']:,} steps"}
    ld["table"] = libcols(libs, {r["lib"] for r in ld["rows"]},
                          [{"key": s["id"], "label": s["title"], "href": f"/results/ladder/#{s['id']}"} for s in ld["scenarios"]], lcell)

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


def pages(libs: list[dict]) -> dict:
    ids = [l["id"] for l in libs]
    d = load("ladder.json")
    steps = []
    for sc in d["scenarios"]:
        rows = []
        for lib in ids:
            for n in d["ladder"]:
                c = sc["summary"].get(lib, {}).get(str(n))
                if not c or "digits" not in c:
                    continue
                # [median, min, max] per truth: exact inputs, inputs as the format rounds them, the interest alone
                row = {"lib": lib, "n": n}
                for k in ("digits", "digitsFormat", "interest"):
                    if k in c:
                        row[k] = [num(c[k]["median"]), num(c[k]["min"]), num(c[k]["max"])]
                rows.append(row)
        steps.append({"id": sc["id"], "title": sc["title"], "rows": rows})

    e = load("edges.json")
    edges = []
    for op in e["ops"]:
        rows = []
        for i, p in enumerate(op["probes"]):
            for lib in ids:
                c = p["cells"].get(lib)
                if not c or c.get("unsupported"):
                    continue
                st = "range" if c.get("range") else "revert" if c.get("reverted") else "zero" if c.get("zero") else "value" if c.get("undefined") else "ok"
                rows.append({"lib": lib, "probe": i, "label": f"{op['id']}({', '.join(map(str, p['args']))})", "digits": min(int(c["digits"]), 72) if st == "ok" else 0, "status": st})
        edges.append({"id": op["id"], "label": op["label"], "rows": rows})

    g127, g19 = load("gas.json"), load("fp19/gas.json")

    def med(g, op, form):
        o = g["ops"].get(op)
        if not o:
            return None
        sm = (o.get("typical") or o)["summary"].get(form)
        return sm["median"] if sm else None
    # FP19 and binary128 are measured in fp19/gas.json, every other library in gas.json
    src = {"fp19": (g19, "lib"), "quad": (g19, "quad"), "fp127": (g127, "lib")}
    gas = [{"lib": lib, "op": op, "gas": v} for op in sorted(set(g127["ops"]) | set(g19["ops"])) for lib in ids
           if (g := src.get(lib, (g127, lib))) and (v := med(g[0], op, g[1])) is not None]

    # each library's ops: median gas inline and through the deployed object, and whether the result is exact
    libops = {}
    for lib, prec, g in (("fp127", load("precision.json"), g127), ("fp19", load("fp19/precision.json"), g19)):
        libops[lib] = [{"op": op, "inline": med(g, op, "lib"), "object": med(g, op, "yul"), "exact": v["minBits"] >= 256}
                       for op, v in prec.items() if med(g, op, "lib") is not None]
    return {"_doc": "Generated by scripts/site/home.py (make home-data) from the measured datasets; do not edit.",
            "libraries": libs, "steps": steps, "edges": edges, "gas": gas, "libops": libops}


def main(argv: list[str]) -> int:
    home = build()
    outs = {OUT: home, PAGES: pages(load("libraries.json")["libraries"])}
    stale = []
    for path, doc in outs.items():
        text = json.dumps(doc, separators=(",", ":")) + "\n"
        if "--check" in argv:
            if not path.exists() or path.read_text() != text:
                stale.append(path.name)
        else:
            path.write_text(text)
            print(f"wrote {path.relative_to(ROOT)} ({len(text):,} bytes)")
    if stale:
        print(f"stale (run make home-data): {', '.join(stale)}")
        return 1
    if "--check" in argv:
        print("chart data is current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""The edges dataset: one-shot evaluations at the ends of each library's domain.

    make edges         # forge test Edges -vv | this script -> docs/benchmarks/edges.{json,md}
    make edges-check   # fail if the committed dataset differs

Reads EDGE|probe|form|ok|raw|reason|gas lines from test/ladder/Edges.t.sol,
computes the exact truth of every probe (mpmath, 200 digits) and the truth
from the arguments as each representation holds them, and records per cell
the value, correct digits against both, the signed error in ULPs, and the
three ways a library can have no answer: a revert (with its reason), a
result of zero where the truth is not, and an argument outside the
representation's range.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from mpmath import mp, mpf, mpc, log, exp, sqrt, erf, erfc, ncdf, lambertw, log1p, expm1, power, nstr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fp127"))
sys.path.insert(0, str(ROOT / "scripts" / "ladder"))
from gas_to_json import versions  # noqa: E402
from gen_inputs import SCALES, from_scaled  # noqa: E402
from gen_edges import ev, probe_id  # noqa: E402
from ladder import metrics, REASONS, PARAM_OUT_OF_RANGE, SCALE_OF_FORM, DIGITS_CAP, SIG  # noqa: E402

mp.dps = 300
SPEC = ROOT / "scripts" / "ladder" / "edges.json"
INPUTS = ROOT / "scripts" / "ladder" / "edge-inputs.json"
OUT_JSON = ROOT / "docs" / "benchmarks" / "edges.json"
OUT_MD = ROOT / "docs" / "benchmarks" / "edges.md"
UNSUPPORTED = "0x7bb9ae15"

METHODOLOGY = {
    "truth": "Every probe is one op evaluated once. The truth is mpmath at 200 decimal digits from the exact arguments; truthFormat is the same op from the arguments as the representation holds them (floored on a grid, nearest for binary128), so digitsFormat measures the op alone and digits what a caller sees.",
    "digits": "digits = floor(-log10 |v - t| / |t|), capped at 100 (reported as exact); errUlps is the signed error in units of the representation's last place (none for the floats).",
    "zero": "A cell is marked zero when the library returned 0 and the truth is not 0: the result fell below the representation's floor. On an 18-decimal grid that is anything below 1e-18; on FP127's, below 2^-128.",
    "reverted": "A revert is recorded with its selector and name. Unsupported means the library has no way to compute the op (the accrual libraries have no general ops; only FP127 has the secondary Lambert branch; the libraries without erf, erfc or normCdf run the same series and continued fraction through their own ops instead, so those cells are not Unsupported).",
    "range": "RANGE means the argument does not fit the representation at all (above 2^127 for FP127, 2^63 for 64.64, 2^128 as a bit pattern for binary128; FP256 holds every probe) and nothing was called.",
    "gas": "gas is measured inside the adapter around the op, after the adapter and the FP127 object are warm. The FP127 (deployed) form includes the staticcall; the others are internal calls.",
    "live": "EdgeRunner.run(op, form, args) on Sepolia evaluates any cell with one eth_call and returns (ok, raw, reason, gas); the edges page's verify button sends the probe's encoded arguments and compares the raw word bit for bit.",
    "reproduce": "make edges regenerates edges.json and edges.md from test/ladder/Edges.t.sol and this script; make edges-check fails CI when the committed dataset differs.",
}


def truth_of(op: str, vals: list):
    """The exact value, or None where the op is undefined there."""
    try:
        if op == "ln": return log(vals[0]) if vals[0] > 0 else None
        if op == "exp": return exp(vals[0])
        if op == "sqrt": return sqrt(vals[0]) if vals[0] >= 0 else None
        if op == "pow": return power(vals[0], vals[1]) if vals[0] > 0 else None
        if op == "mul": return vals[0] * vals[1]
        if op == "div": return vals[0] / vals[1] if vals[1] != 0 else None
        if op == "lambertW0":
            w = lambertw(vals[0], 0)
            return None if isinstance(w, mpc) and abs(w.imag) > 0 else mpf(w.real)
        if op == "lambertWm1":
            w = lambertw(vals[0], -1)
            return None if isinstance(w, mpc) and abs(w.imag) > 0 else mpf(w.real)
        if op == "log1p": return log1p(vals[0]) if vals[0] > -1 else None
        if op == "expm1": return expm1(vals[0])
        if op == "compound": return power(1 + vals[0], int(vals[1])) if 1 + vals[0] > 0 else None
        if op == "powu":
            x, n = vals[0], int(vals[1])
            if x == 0: return mpf(0) if n > 0 else None
            return power(x, n)
        if op == "erf": return erf(vals[0])
        if op == "erfc": return erfc(vals[0])
        if op == "normCdf": return ncdf(vals[0])
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    raise KeyError(op)


def parse_lines(stream) -> dict:
    cells: dict = {}
    for line in stream:
        if "EDGE|" not in line:
            continue
        parts = line[line.index("EDGE|"):].strip().split("|")
        if len(parts) != 7:
            continue
        _, pid, form, ok, raw, reason, gas = parts
        cells.setdefault(pid, {})[form] = {"ok": ok == "1", "raw": int(raw), "reason": reason[:10] if reason != "RANGE" else "RANGE", "gas": int(gas)}
    return cells


def build(cells: dict) -> dict:
    spec = json.loads(SPEC.read_text())
    inputs = {c["id"]: c for c in json.loads(INPUTS.read_text())["cells"]}
    forms = ["fp127", "fp127lib", "abdk", "solady", "prb", "quad", "balancer", "aave", "morpho", "maker", "fp256"]
    ops_out = []
    for op in spec["ops"]:
        probes_out = []
        for p in spec["probes"]:
            if p["op"] != op["id"]:
                continue
            pid = probe_id(p)
            if pid not in cells:
                continue
            enc = inputs[pid]
            vals = [ev(a) for a in p["args"]]
            t = truth_of(op["id"], vals)
            tf = {}
            for sc, (_, scale, _) in SCALES.items():
                held = [int(e) if k == "n" else from_scaled(int(e), scale) for e, k in zip(enc[sc], op["args"])]
                tf[sc] = truth_of(op["id"], held) if all(h is not None for h in held) else None
            cells_out = {}
            for form in forms:
                c = cells[pid].get(form)
                if c is None:
                    continue
                sc = SCALE_OF_FORM[form]
                scale = SCALES[sc][1]
                if c["reason"] == "RANGE":
                    cells_out[form] = {"range": True}
                    continue
                if not c["ok"]:
                    cells_out[form] = {"reverted": True, "reason": c["reason"], "reasonName": REASONS.get(c["reason"], "unknown selector"),
                                       "unsupported": c["reason"] == UNSUPPORTED}
                    continue
                v = from_scaled(c["raw"], scale)
                if t is None or v is None:
                    cells_out[form] = {"raw": str(c["raw"]), "value": nstr(v, SIG) if v is not None else None, "gas": c["gas"], "undefined": True}
                    continue
                m = metrics(c["raw"], scale, t, tf[sc]) if tf[sc] is not None else metrics(c["raw"], scale, t, t)
                m["raw"] = str(c["raw"])
                m["gas"] = c["gas"]
                m["zero"] = c["raw"] == 0 and t != 0
                cells_out[form] = m
            probes_out.append({
                "id": pid, "args": p["args"], "why": p.get("why", ""),
                "resolved": [nstr(v, SIG) for v in vals],
                "truth": nstr(t, SIG) if t is not None else None,
                "truthFormat": {SCALES[sc][0]: (nstr(tf[sc], SIG) if tf[sc] is not None else None) for sc in SCALES},
                "cells": cells_out,
            })
        ops_out.append({"id": op["id"], "index": op["index"], "label": op["label"], "args": op["args"], "why": op["why"], "probes": probes_out})
    return {
        "generated": date.today().isoformat(),
        "description": "Edges: one-shot evaluations at the ends of each library's domain, every probe through every library in its native representation, against mpmath at 200 digits. See methodology.",
        "versions": versions(),
        "forms": [{"id": f, "scale": SCALES[SCALE_OF_FORM[f]][0]} for f in forms],
        "digitsCap": DIGITS_CAP,
        "methodology": METHODOLOGY,
        "ops": ops_out,
    }


def cell_text(c: dict | None) -> str:
    if c is None:
        return "—"
    if c.get("range"):
        return "RANGE"
    if c.get("reverted"):
        return "n/a" if c.get("unsupported") else f"REVERT {c['reasonName'].split('(')[0].split(':')[0].strip()}"
    if c.get("undefined"):
        return "value"
    if c.get("zero"):
        return "ZERO"
    return "exact" if c["digits"] >= DIGITS_CAP else str(c["digits"])


def render_md(doc: dict) -> str:
    forms = [f["id"] for f in doc["forms"] if f["id"] != "fp127lib"]
    L = ["# Edges: where each library's domain ends", "",
         f"Generated {doc['generated']} by `make edges`. Versions: " + ", ".join(f"{k} {v}" for k, v in doc["versions"].items()) + ".", "",
         "Each probe is one op evaluated once at the end of a domain, through every library in its own representation, against mpmath at 200 digits. Cells give correct digits against the exact truth (`digits`; `digitsFormat`, the signed error and the raw words are in edges.json), or how the library had no answer: **ZERO** when it returned 0 where the truth is not (the result fell below the format's floor), **REVERT** with the reason, **RANGE** when the argument does not fit the representation, **n/a** when the library has no way to compute the op. FP127Lib coincides with FP127 and is omitted. The method is in the Methodology section at the end.", ""]
    for op in doc["ops"]:
        L += [f"## {op['label']}", "", op["why"], "",
              "| probe | truth | " + " | ".join(forms) + " |", "|---|---|" + "---:|" * len(forms)]
        for p in op["probes"]:
            t = p["truth"]
            ts = "undefined" if t is None else (nstr(mpf(t), 8) if abs(mpf(t)) < mpf(10) ** 12 and abs(mpf(t)) > mpf(10) ** -4 else nstr(mpf(t), 4))
            row = [f"`{p['id']}`" + (f" {p['why']}" if p["why"] else ""), f"`{ts}`"] + [cell_text(p["cells"].get(f)) for f in forms]
            L.append("| " + " | ".join(row) + " |")
        L.append("")
    L += ["## Methodology", ""]
    for k, v in doc["methodology"].items():
        L += [f"**{k}.** {v}", ""]
    return "\n".join(L)


def strip_volatile(doc: dict) -> dict:
    d = json.loads(json.dumps(doc))
    d.pop("generated", None)
    d.pop("versions", None)
    for op in d["ops"]:
        for p in op["probes"]:
            for c in p["cells"].values():
                c.pop("gas", None)
    d.pop("liveRunner", None); d.pop("liveSelector", None); d.pop("liveNote", None)
    return d


def main(argv: list[str]) -> int:
    doc = build(parse_lines(sys.stdin))
    if OUT_JSON.exists():
        old = json.loads(OUT_JSON.read_text())
        for k in ("liveRunner", "liveSelector", "liveNote"):
            if k in old:
                doc[k] = old[k]
    if "--check" in argv:
        if not OUT_JSON.exists() or strip_volatile(json.loads(OUT_JSON.read_text())) != strip_volatile(doc):
            print("edges.json is stale; run `make edges`", file=sys.stderr)
            return 1
        print(f"edges ok: {sum(len(o['probes']) for o in doc['ops'])} probes")
        return 0
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")
    OUT_MD.write_text(render_md(doc) + "\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}: {sum(len(o['probes']) for o in doc['ops'])} probes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Check that each scene draws the numbers the JSON holds.

Every scene module exposes numbers(): the values it puts on screen. This
recomputes them straight from the loaders in vocab.py (by a second route
where there is one: Decimal where the scene used Fraction, integer
arithmetic where it used strings) and compares, so a regenerated
edges.json or ladder.json that a scene silently ignored (a hard-coded
digit, a stale copy) fails here before it is rendered.

    uv run talk/scenes/check.py            # every scene that has numbers()
    uv run talk/scenes/check.py s02_exp40  # one
"""

from __future__ import annotations

import importlib
import sys
from decimal import ROUND_FLOOR, Decimal, localcontext
from math import log10
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import vocab  # noqa: E402


def expect_s02_exp40(mod) -> dict:
    p = vocab.probe(mod.OP, mod.ARG)
    lib = vocab.libs()
    word_digits = len(p["truth"].partition(".")[0]) + mod.WORD_DECIMALS
    rows = []
    for lid in mod.LIBS:
        v = p["cells"][lid]["value"]
        assert not p["cells"][lid].get("reverted") and not p["cells"][lid].get("zero"), lid
        rows.append(
            {
                "id": lid,
                "label": lib[lid]["label"],
                "value": v,
                "matching": vocab.matching_digits(v, p["truth"]),
                "digits": vocab.correct_digits(v, p["truth"]),
                "first_wrong": vocab.first_wrong_index(v, p["truth"]),
            }
        )
        # the integer-rounded measure edges.json reports agrees with ours
        assert int(float(p["cells"][lid]["digits"])) == rows[-1]["digits"], (lid, p["cells"][lid]["digits"], rows[-1]["digits"])
        # the matching prefix ends exactly at the digit the scene lights red
        fw = rows[-1]["first_wrong"]
        assert fw is not None and fw - (1 if fw > len(p["truth"].partition(".")[0]) else 0) == rows[-1]["matching"], (lid, fw, rows[-1]["matching"])
    ours = []
    for lid in mod.OURS:
        v = p["cells"][lid]["value"]
        m = vocab.matching_digits(v, p["truth"])
        assert m >= word_digits, (lid, m)  # "every digit" is a claim about the 36 the word holds
        ours.append({"id": lid, "label": lib[lid]["label"], "value": v, "matching": m, "digits": int(p["cells"][lid]["digits"])})
    return {
        "truth": p["truth"],
        "word_digits": word_digits,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": vocab.correctly_rounded_18(p["truth"]),
    }


def expect_s04_grid(mod) -> dict:
    p = vocab.probe(mod.OP, mod.ARG)
    truth = p["truth"]
    with localcontext() as ctx:
        ctx.prec = 120
        t = Decimal(truth)
        q18 = Decimal(1).scaleb(-mod.WORD_DECIMALS)
        lo18 = t.quantize(q18, rounding=ROUND_FLOOR)
        hi18 = lo18 + q18
        f18 = float((t - lo18) / q18)
        scale = Decimal(2) ** mod.FRACTION_BITS
        lob = int((t * scale).to_integral_value(rounding=ROUND_FLOOR))
        hib = lob + 1
        fb = float(t * scale - lob)
        ub = Decimal(1) / scale

        def expansion(w: int) -> str:
            return str((Decimal(w) * ub).quantize(Decimal(1).scaleb(-mod.EXPANSION_DECIMALS), rounding=ROUND_FLOOR))

        nearest = hib if fb >= 0.5 else lob
        tick = f"{float(ub):.1e}"
        neighbours_128 = [expansion(lob), expansion(hib)]
        nearest_128 = expansion(nearest)
    bits = list(range(mod.BIT_START, mod.FRACTION_BITS + 1, mod.BIT_STEP))
    assert bits[-1] == mod.FRACTION_BITS
    return {
        "truth": truth,
        "levels_decimal": mod.WORD_DECIMALS,
        "neighbours_18": [str(lo18), str(hi18)],
        "fraction_18": f18,
        "correctly_rounded": vocab.correctly_rounded_18(truth),
        "bits": bits,
        "neighbours_bits": [format(lob, "b")[-mod.SHOW_BITS :], format(hib, "b")[-mod.SHOW_BITS :]],
        "neighbours_128": neighbours_128,
        "fraction_128": fb,
        "nearest_128": nearest_128,
        "tick_128": tick,
        "fp127": p["cells"]["fp127"]["value"],
    }


def expect_s05_cost(mod) -> dict:
    d = vocab.incidents()
    rows, total = [], 0
    for r in d["incidents"]:
        total += r["lossUsd"]
        rows.append({"date": r["date"], "protocol": r["protocol"], "rounding": r["rounding"], "loss": r["loss"], "sum": f"${total / 1e6:,.1f}M"})
    assert total > 130_000_000, total  # the slide says more than $130 million
    assert [r["date"][-4:] for r in rows] == sorted(r["date"][-4:] for r in rows), "oldest first"
    return {"rows": rows, "sum_usd": total, "sum": f"${total / 1e6:,.1f}M", "total": d["total"], "since": d["since"]}


def expect_s06_resupply(mod) -> dict:
    d = vocab.resupply()
    p = d["pins"]
    price, borrow, coll = int(p["price"]), int(p["borrowAmount"]), int(p["collateral"])
    max_ltv, ltv_p, ex_p = int(p["maxLTV"]), int(p["ltvPrecision"]), int(p["exchangePrecision"])
    with localcontext() as ctx:
        ctx.prec = 120
        rate = Decimal(10**36) / Decimal(price)
        quotient = str(rate.quantize(Decimal(1).scaleb(-mod.QUOTIENT_DIGITS), rounding=ROUND_FLOOR))
        ltv = Decimal(borrow) * rate * ltv_p / ex_p / coll
        ltv_str = f"{ltv.quantize(Decimal(1).scaleb(-mod.LTV_DECIMALS), rounding=ROUND_FLOOR):,}"
        ratio = f"{int((ltv / max_ltv).to_integral_value()):,}"
        pct = f"{(Decimal(max_ltv) / ltv_p * 100).normalize()}%"
    floor_rate = 10**36 // price
    assert floor_rate == int(p["exchangeRateOnChain"]), "the chain stored the floored rate"
    ltv_floor = ((borrow * floor_rate * ltv_p) // ex_p) // coll
    cite = {c["line"]: c["text"] for c in d["citations"] if c["file"].endswith("ResupplyPairCore.sol")}
    return {
        "block": f"{int(p['block']):,}",
        "price": f"{price:,}",
        "quotient": quotient + "…",
        "rate_short": quotient[: mod.RATE_SHORT + 2] + "…",
        "floor": str(floor_rate),
        "borrow_tokens": f"{borrow // ex_p:,}",
        "collateral": f"{coll:,}",
        "ltv_exp": round(log10(ltv_p)),
        "ltv_floor": f"{ltv_floor:,}",
        "max_ltv": f"{max_ltv:,}",
        "max_ltv_pct": pct,
        "ltv_exact": ltv_str + "…",
        "ratio": ratio,
        "solvent_floor": ltv_floor <= max_ltv,
        "solvent_exact": ltv <= max_ltv,
        "rate_line": cite[573],
        "ltv_line": cite[282],
    }


def expect_s08_ladder(mod) -> dict:
    d = vocab.ladder(mod.SCENARIO)
    lib = vocab.libs()
    groups = []
    for lid, cells in d["scenario"]["summary"].items():
        if lid in mod.SKIP:
            continue
        vals = []
        for n in d["N"]:
            c = cells.get(str(n), {})
            vals.append(c["digits"]["median"] if c.get("count") else None)
        if None in vals:
            continue
        for g in groups:
            if g["digits"] == vals and g["family"] == lib[lid]["family"]:
                g["ids"].append(lid)
                g["labels"].append(lib[lid]["label"])
                break
        else:
            groups.append({"ids": [lid], "labels": [lib[lid]["label"]], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours")), "digits": vals})
    assert {"fp127", "fp19"} <= {lid for g in groups for lid in g["ids"]}
    return {"N": d["N"], "log10": [d["log10"][str(n)] for n in d["N"]], "axisMax": d["axisMax"], "groups": groups}


def expect_s09_cliff(mod) -> dict:
    op = vocab.edges(mod.OP)
    lib = vocab.libs()
    probes = [p for p in op["probes"] if len(p["args"]) == 1 and mod.ARG_LO <= float(p["args"][0]) <= mod.ARG_HI]
    lids = []
    for lid in probes[0]["cells"]:
        if lid in mod.SKIP:
            continue
        ok = False
        for p in probes:
            c = p["cells"][lid]
            if c.get("unsupported"):
                continue
            if c.get("reverted") and str(c.get("reasonName", "")).startswith(mod.RANGE_REASON):
                continue
            ok = True
        if ok:
            lids.append(lid)
    lids.sort(key=lambda lid: (not lib[lid].get("ours"), list(lib).index(lid)))
    columns = []
    y_max = 0.0
    for p in probes:
        cells = {}
        for lid in lids:
            c = p["cells"][lid]
            if c.get("unsupported"):
                cells[lid] = {"kind": "unsupported"}
            elif c.get("reverted"):
                cells[lid] = {"kind": "revert", "reason": c.get("reasonName")}
            elif c.get("zero"):
                cells[lid] = {"kind": "zero", "digits": 0}
            else:
                cells[lid] = {"kind": "value", "digits": float(c["digits"])}
                y_max = max(y_max, float(c["digits"]))
        columns.append({"arg": p["args"][0], "cells": cells})
    axis_max = int(mod.Y_STEP * -(-y_max // mod.Y_STEP))
    # the story the slide tells, checked against the cells
    by_arg = {c["arg"]: c["cells"] for c in columns}
    assert by_arg["-42"]["solady"]["kind"] == "zero" and by_arg["-60"]["abdk"]["kind"] == "zero" and by_arg["-100"]["fp127"]["kind"] == "zero"
    assert all(c["cells"]["fp19"]["kind"] == "value" and c["cells"]["fp19"]["digits"] > 60 for c in columns)
    return {
        "libs": [{"id": lid, "label": lib[lid]["label"], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours"))} for lid in lids],
        "columns": columns,
        "axisMax": axis_max,
    }


def expect_s10_live(mod) -> dict:
    cases = vocab.live()
    survey = vocab._load("docs/benchmarks/accrual-deployed.json")["survey"]
    pts = [
        {
            "id": c["id"],
            "protocol": c["protocol"],
            "deployed": float(c["truth"][c["primaryTruth"]]["deployed"]["digitsInterest"]),
            "fp127": float(c["truth"][c["primaryTruth"]]["fp127"]["digitsInterest"]),
        }
        for c in cases
    ]
    assert len(pts) == 326, len(pts)
    counts = {}
    for x in pts:
        counts[x["protocol"]] = counts.get(x["protocol"], 0) + 1
    assert set(counts) == set(mod.PROTOCOL_COLOUR), counts
    return {"points": pts, "counts": counts, "block": f"{survey['block']:,}", "date": survey["date"], "above": sum(1 for x in pts if x["fp127"] > x["deployed"])}


EXPECT = {
    "s02_exp40": expect_s02_exp40,
    "s04_grid": expect_s04_grid,
    "s05_cost": expect_s05_cost,
    "s06_resupply": expect_s06_resupply,
    "s08_ladder": expect_s08_ladder,
    "s09_cliff": expect_s09_cliff,
    "s10_live": expect_s10_live,
}


def main(argv: list[str]) -> int:
    names = argv or sorted(EXPECT)
    bad = 0
    for name in names:
        mod = importlib.import_module(name)
        drawn = mod.numbers()
        want = EXPECT[name](mod)
        if drawn == want:
            print(f"ok    {name}")
        else:
            bad += 1
            keys = [k for k in set(drawn) | set(want) if drawn.get(k) != want.get(k)]
            print(f"FAIL  {name}: {keys}")
            for k in keys:
                print(f"  drawn[{k}]: {str(drawn.get(k))[:300]}\n  json [{k}]: {str(want.get(k))[:300]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

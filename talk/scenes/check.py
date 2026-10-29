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
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal, localcontext
from math import log10
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import vocab  # noqa: E402


def expect_s02_exp40(mod) -> dict:
    p = vocab.probe(mod.OP, mod.ARG)
    lib = vocab.libs()
    int_len = len(p["truth"].partition(".")[0])
    word_digits = int_len + mod.WORD_DECIMALS
    # the first row, e^40 to 18 decimals, by integer arithmetic: round half-up at the 18th
    ti, _, tf = p["truth"].partition(".")
    assert len(tf) > mod.WORD_DECIMALS, tf
    q = 10 ** (len(tf) - mod.WORD_DECIMALS)
    scaled = (int(ti + tf) * 2 + q) // (2 * q)
    exact_row = f"{scaled // 10**mod.WORD_DECIMALS}.{scaled % 10**mod.WORD_DECIMALS:0{mod.WORD_DECIMALS}d}"
    assert exact_row == vocab.correctly_rounded_18(p["truth"]), exact_row
    rows = []
    for lid in mod.LIBS:
        v = p["cells"][lid]["value"]
        assert not p["cells"][lid].get("reverted") and not p["cells"][lid].get("zero"), lid
        m = vocab.matching_digits(v, p["truth"])
        rows.append(
            {
                "id": lid,
                "label": lib[lid]["label"],
                "value": v,
                # decimals by the other route: the matching prefix less the integer part,
                # 0 when the prefix ends inside the integer part
                "decimals": m - int_len if m >= int_len else 0,
                "matching": m,
                "digits": vocab.correct_digits(v, p["truth"]),
                "first_wrong": vocab.first_wrong_index(v, p["truth"]),
            }
        )
        # the integer-rounded measure edges.json reports agrees with ours
        assert int(float(p["cells"][lid]["digits"])) == rows[-1]["digits"], (lid, p["cells"][lid]["digits"], rows[-1]["digits"])
        # the matching prefix ends exactly at the digit the scene lights red
        fw = rows[-1]["first_wrong"]
        assert fw is not None and fw - (1 if fw > int_len else 0) == rows[-1]["matching"], (lid, fw, rows[-1]["matching"])
        # an 18-decimal value cannot match more than 18 decimals
        assert len(v.partition(".")[2]) == mod.WORD_DECIMALS and rows[-1]["decimals"] <= mod.WORD_DECIMALS, (lid, v)
        # the first wrong decimal's position by the other route: the decimal after the last right one,
        # or 0 (before the point) when the integer parts differ
        wd = rows[-1]["decimals"] + 1 if v.partition(".")[0] == p["truth"].partition(".")[0] else 0
        rows[-1]["wrong_decimal"] = wd
        rows[-1]["right_label"] = (
            f"{rows[-1]['decimals']} right · wrong at the {mod.ordinal(wd)} decimal" if wd else f"{rows[-1]['decimals']} right · wrong before the point"
        )
    # the story the slide tells, checked against the cells: 3rd, 4th, and one wrong before the point
    by_id = {r["id"]: r for r in rows}
    assert by_id["solady"]["wrong_decimal"] == 3 and by_id["solady"]["right_label"] == "2 right · wrong at the 3rd decimal", by_id["solady"]
    assert by_id["balancer"]["wrong_decimal"] == 4 and by_id["balancer"]["right_label"] == "3 right · wrong at the 4th decimal", by_id["balancer"]
    assert by_id["prb"]["wrong_decimal"] == 0 and by_id["prb"]["decimals"] == 0 and by_id["prb"]["right_label"] == "0 right · wrong before the point", by_id["prb"]
    assert mod.ordinal(1) == "1st" and mod.ordinal(2) == "2nd" and mod.ordinal(11) == "11th" and mod.ordinal(13) == "13th" and mod.ordinal(21) == "21st" and mod.ordinal(22) == "22nd"
    ours = []
    with localcontext() as ctx:
        ctx.prec = 60
        truth = Decimal(p["truth"])
        for lid in mod.OURS:
            c = p["cells"][lid]
            v = c["value"]
            m = vocab.matching_digits(v, p["truth"])
            assert m >= word_digits, (lid, m)  # "every decimal" is a claim about the 18 the word holds
            dec = int(c["digits"]) - int_len
            # the other route: decimals from the cell's relative error, floor(−log10(|relErr| · truth));
            # the scene's count (a floor of a floor) never exceeds it
            exact = int((-(abs(Decimal(c["relErr"])) * truth).log10()).to_integral_value(rounding=ROUND_FLOOR))
            assert dec <= exact <= dec + 1, (lid, dec, exact)
            measure = f"the word holds {dec} decimals" if lid == "fp127" else f"the word holds {int(c['digits'])} digits"
            # the word to 18 decimals by integer arithmetic: floor(v · 10^18 + 1/2) (half-up), and it is the closest 18-decimal value
            vi, _, vf = v.partition(".")
            scaled = (int(vi + vf) * 2 * 10 ** (mod.WORD_DECIMALS - len(vf)) + 10 ** mod.WORD_DECIMALS) // (2 * 10 ** mod.WORD_DECIMALS) if len(vf) <= mod.WORD_DECIMALS else (int(vi + vf) * 2 + 10 ** (len(vf) - mod.WORD_DECIMALS)) // (2 * 10 ** (len(vf) - mod.WORD_DECIMALS))
            word18 = f"{scaled // 10**mod.WORD_DECIMALS}.{scaled % 10**mod.WORD_DECIMALS:0{mod.WORD_DECIMALS}d}"
            assert word18 == exact_row, (lid, word18, exact_row)
            ours.append({"id": lid, "label": lib[lid]["label"], "value": v, "word18": word18, "matching": m, "digits": int(c["digits"]), "decimals": dec, "beyond": dec - mod.WORD_DECIMALS, "right_label": f"{mod.WORD_DECIMALS} right of {mod.WORD_DECIMALS} · {measure}"})
    # no row says "every decimal": the reveal rows carry the plain count like the others
    assert [o["right_label"] for o in ours] == ["18 right of 18 · the word holds 72 digits", "18 right of 18 · the word holds 39 decimals"], [o["right_label"] for o in ours]
    # no number on the slide is cut short: every row is exactly 18 decimals, no ellipsis
    for s in [exact_row] + [r["value"] for r in rows] + [o["word18"] for o in ours]:
        assert "…" not in s and len(s.partition(".")[2]) == mod.WORD_DECIMALS, s
    assert "…" not in mod.EXACT_LABEL and "…" not in mod.EXACT_RIGHT
    return {
        "truth": p["truth"],
        "word_digits": word_digits,
        "exact_row": exact_row,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": exact_row,
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

        def reading(w: int, places: int) -> str:  # the word's value to `places` decimals, nearest
            return str((Decimal(w) * ub).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))

        nearest = hib if fb >= 0.5 else lob
        tick = f"{float(ub):.1e}"
        neighbours_128 = [reading(lob, mod.EXPANSION_DECIMALS), reading(hib, mod.EXPANSION_DECIMALS)]
        nearest_128 = reading(nearest, mod.EXPANSION_DECIMALS)
        word18 = reading(nearest, mod.WORD_DECIMALS)
        # the readings go exactly as far as the truth does, and FP127's word to 18 decimals is the closest 18-decimal value
        assert mod.EXPANSION_DECIMALS == len(truth.partition(".")[2]) and word18 == vocab.correctly_rounded_18(truth), (mod.EXPANSION_DECIMALS, word18)
        # the two words differ by one in the last place of their 32-hex-digit fractions, shown complete
        hexes = [f"0x{w % (1 << mod.FRACTION_BITS):032x}" for w in (lob, hib)]
        assert all(len(h) == 2 + mod.HEX_DIGITS and "…" not in h for h in hexes) and int(hexes[1], 16) - int(hexes[0], 16) == 1, hexes
    bits = list(range(mod.BIT_START, mod.FRACTION_BITS + 1, mod.BIT_STEP))
    assert bits[-1] == mod.FRACTION_BITS and all(b % 4 == 0 for b in bits)  # every binary level's fraction is whole hex digits
    return {
        "truth": truth,
        "levels_decimal": mod.WORD_DECIMALS,
        "neighbours_18": [str(lo18), str(hi18)],
        "fraction_18": f18,
        "correctly_rounded": vocab.correctly_rounded_18(truth),
        "bits": bits,
        "neighbours_hex": hexes,
        "neighbours_128": neighbours_128,
        "fraction_128": fb,
        "nearest_hex": hexes[1] if nearest == hib else hexes[0],
        "nearest_128": nearest_128,
        "word18": word18,
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

        def to_decimals(x: Decimal, places: int) -> str:  # rounded half-up at the stated decimal, by Decimal
            return f"{x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP):,}"

        quotient = to_decimals(rate, mod.QUOTIENT_DIGITS)
        rate_short = to_decimals(rate, mod.RATE_SHORT)
        ltv = Decimal(borrow) * rate * ltv_p / ex_p / coll
        ltv_str = to_decimals(ltv, mod.LTV_DECIMALS)
        ratio = f"{int((ltv / max_ltv).to_integral_value()):,}"
        pct = f"{(Decimal(max_ltv) / ltv_p * 100).normalize()}%"
        # the story: the rate reads below one half at the count the scene names it to, and
        # that count is the fewest that does (one fewer rounds up to 0.5), so the floor to 0 is visible
        assert Decimal(rate_short) < Decimal("0.5") and Decimal(quotient) < Decimal("0.5"), (rate_short, quotient)
        assert Decimal(to_decimals(rate, mod.RATE_SHORT - 1)) == Decimal("0.5"), mod.RATE_SHORT
        assert len(quotient.partition(".")[2]) == mod.QUOTIENT_DIGITS and len(ltv_str.partition(".")[2]) == mod.LTV_DECIMALS
    floor_rate = 10**36 // price
    assert floor_rate == int(p["exchangeRateOnChain"]), "the chain stored the floored rate"
    ltv_floor = ((borrow * floor_rate * ltv_p) // ex_p) // coll
    cite = {c["line"]: c["text"] for c in d["citations"] if c["file"].endswith("ResupplyPairCore.sol")}
    # no number on screen carries an ellipsis: every string the scene draws is complete in a stated format
    for k, v in mod.numbers().items():
        assert "…" not in str(v), (k, v)
    return {
        "block": f"{int(p['block']):,}",
        "price": f"{price:,}",
        "quotient": quotient,
        "quotient_label": f"(to {mod.QUOTIENT_DIGITS} decimals)",
        "rate_short": rate_short,
        "rate_label": f"(to {mod.RATE_SHORT} decimals)",
        "floor": str(floor_rate),
        "borrow_tokens": f"{borrow // ex_p:,}",
        "collateral": f"{coll:,}",
        "ltv_exp": round(log10(ltv_p)),
        "ltv_floor": f"{ltv_floor:,}",
        "max_ltv": f"{max_ltv:,}",
        "max_ltv_pct": pct,
        "ltv_exact": ltv_str,
        "ltv_label": f"(to {mod.LTV_DECIMALS} decimals)",
        "ratio": ratio,
        "solvent_floor": ltv_floor <= max_ltv,
        "solvent_exact": ltv <= max_ltv,
        "rate_line": cite[573],
        "ltv_line": cite[282],
    }


def expect_s08_ladder(mod) -> dict:
    lib = {lid: rec for lid, rec in vocab.libs().items() if lid != "blockulator"}
    assert len(lib) == 17, len(lib)  # the registry's 18 less BlockulatorWad: every one is drawn or listed
    first = vocab.ladder(mod.SCENARIOS[0])
    N = first["N"]
    scenarios = []
    for sid in mod.SCENARIOS:
        d = vocab.ladder(sid)
        summary, ops = d["scenario"]["summary"], d["scenario"]["ops"]
        series, absent = {}, {}
        for lid in lib:
            if lid in mod.SKIP:
                continue
            vals = []
            for n in N:
                c = summary[lid].get(str(n), {})
                dg = c.get("digits") if c.get("count") else None
                vals.append(float(dg["median"] if isinstance(dg, dict) else dg) if dg is not None else None)
            if None in vals:
                absent[lid] = "not offered" if ops[lid] == ["unsupported"] else "no result"
            else:
                series[lid] = vals
        groups = []
        for lid, vals in series.items():
            for g in groups:
                if g["digits"] == vals and g["family"] == lib[lid]["family"]:
                    g["ids"].append(lid)
                    g["labels"].append(lib[lid]["label"])
                    break
            else:
                groups.append({"ids": [lid], "labels": [lib[lid]["label"]], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours")), "digits": vals})
        end = {lid: vals[-1] for lid, vals in series.items()}
        # the margin is over the BEST 18-decimal line at N = 10,000 (the smallest honest claim)
        gold_end = max(end[lid] for lid in end if lib[lid]["family"] == "wad")
        margins = {lid: round(end[lid] - gold_end, 1) for lid in ("fp127", "fp19")}
        assert {"fp127", "fp19"} <= set(series) and len(series) + len(absent) == 17, sid
        scenarios.append(
            {
                "id": sid,
                "title": d["scenario"]["title"],
                "series": series,
                "groups": groups,
                "end": end,
                "absent": absent,
                "gold_end": gold_end,
                "margins": margins,
                "margin_digits": {lid: int(m // 1) for lid, m in margins.items()},
            }
        )
    # the story the slide tells, checked against the cells
    by_id = {s["id"]: s for s in scenarios}
    assert "maker" in by_id["compound"]["series"] and {"aave", "morpho"} <= set(by_id["accrual-continuous"]["series"]) and {"fraxlend", "euler"} <= set(by_id["adaptive-rate"]["series"])
    assert all(s["margins"]["fp19"] > s["margins"]["fp127"] > 0 for s in scenarios)
    return {"N": N, "log10": [first["log10"][str(n)] for n in N], "axisMax": first["axisMax"], "scenarios": scenarios}


def expect_s09_cliff(mod) -> dict:
    op = vocab.edges(mod.OP)
    lib = {lid: rec for lid, rec in vocab.libs().items() if lid != "blockulator"}
    assert len(lib) == 17, len(lib)
    probes = [p for p in op["probes"] if len(p["args"]) == 1 and mod.ARG_LO <= float(p["args"][0]) <= mod.ARG_HI]
    lids, absent = [], {}
    for lid in lib:
        if lid in mod.SKIP:
            continue
        kinds = set()
        for p in probes:
            c = p["cells"][lid]
            if c.get("unsupported"):
                kinds.add("unsupported")
            elif c.get("reverted") and str(c.get("reasonName", "")).startswith(mod.RANGE_REASON):
                kinds.add("range")
            else:
                kinds.add("value")
        if kinds == {"unsupported"}:
            absent[lid] = {"label": lib[lid]["label"], "reason": "no exp"}
        elif "value" not in kinds:
            absent[lid] = {"label": lib[lid]["label"], "reason": "rejects negative inputs"}
        else:
            lids.append(lid)
    assert len(lids) + len(absent) == 17 and "prbud" in absent and absent["prbud"]["reason"] == "rejects negative inputs"
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
    fp19_min = min(c["cells"]["fp19"]["digits"] for c in columns)
    # FP127's last standing point: the last probe where its value still had a digit (by the raw cells)
    standing = [p for p in probes if not p["cells"]["fp127"].get("zero") and not p["cells"]["fp127"].get("reverted") and float(p["cells"]["fp127"]["digits"]) >= 1]
    wad = [lid for lid in lids if lib[lid]["family"] == "wad"]
    first_zero = next(p["args"][0] for p in probes if any(p["cells"][lid].get("zero") for lid in wad))
    return {
        "libs": [{"id": lid, "label": lib[lid]["label"], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours"))} for lid in lids],
        "absent": absent,
        "columns": columns,
        "axisMax": axis_max,
        "fp19_min": fp19_min,
        "fp127_last": {"arg": standing[-1]["args"][0], "digits": float(standing[-1]["cells"]["fp127"]["digits"])},
        "wad_first_zero": first_zero,
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
            "fp19": float(c["truth"][c["primaryTruth"]]["fp19"]["digitsInterest"]),
        }
        for c in cases
    ]
    assert len(pts) == 326, len(pts)
    counts = {}
    for x in pts:
        counts[x["protocol"]] = counts.get(x["protocol"], 0) + 1
    assert set(counts) == set(mod.PROTOCOL_LABEL), counts

    def median(key: str) -> float:  # the middle of the sorted list, by hand
        v = sorted(x[key] for x in pts)
        k = len(v) // 2
        return round((v[k - 1] + v[k]) / 2 if len(v) % 2 == 0 else v[k], 1)

    medians = {k: median(k) for k in ("deployed", "fp127", "fp19")}
    above, above_fp19 = sum(1 for x in pts if x["fp127"] > x["deployed"]), sum(1 for x in pts if x["fp19"] > x["deployed"])
    assert above == above_fp19 == len(pts), (above, above_fp19)
    margins = {"fp127": round(medians["fp127"] - medians["deployed"], 1), "fp19": round(medians["fp19"] - medians["fp127"], 1)}
    assert margins["fp127"] > 0 and margins["fp19"] > 0
    return {"points": pts, "counts": counts, "block": f"{survey['block']:,}", "date": survey["date"], "above": above, "above_fp19": above_fp19, "medians": medians, "margins": margins}


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

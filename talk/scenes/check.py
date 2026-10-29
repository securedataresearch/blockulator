"""Check that each scene draws the numbers the JSON holds, and nothing else.

Every scene module exposes numbers(): the values it puts on screen. This
recomputes them straight from the loaders in vocab.py (by a second route
where there is one: Decimal where the scene used Fraction, integer
arithmetic where it used strings) and compares, so a regenerated
edges.json or ladder.json that a scene silently ignored (a hard-coded
digit, a stale copy) fails here before it is rendered.

Then it runs each scene's construct() under manim's dry run (no frames
are encoded) and reads vocab.DRAWN, every string the text helpers were
asked to draw. A drawn string that carries a digit must be accounted
for: either every number in it (a run of digits, with its commas and
point, or a 0x word) is a number that numbers() holds (a value, or a
value formatted as the scenes format it: thousands(), str, one decimal,
rounded) or the whole string is a key of the module's LITERALS, the
digit-bearing fixed strings (captions, "to 18 decimals", a closing line)
each mapped to a claim id in research_notes/talk/claims.md or to
"REPORT" for the ones still to be verified. Anything else prints as
UNSUPPORTED and fails. The dry run also asserts the scene called every
one of its SECTIONS in order.

    uv run talk/scenes/check.py            # every scene that has numbers()
    uv run talk/scenes/check.py s02_exp40  # one
"""

from __future__ import annotations

import importlib
import inspect
import re
import sys
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from math import log10
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from manim import config  # noqa: E402

config.verbosity = "ERROR"
config.progress_bar = "none"

import vocab  # noqa: E402

NUMBER = re.compile(r"0x[0-9a-fA-F]+|\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
TAG = re.compile(r"<[^>]+>")


def number_tokens(s: str) -> set[str]:
    """The numbers in a string: markup tags dropped (a colour's hex is not
    a number on screen), line breaks closed (a long number wraps), then
    every run of digits with its commas and point, hex words lower-cased."""
    s = TAG.sub(" ", s).replace("\n", "")
    return {t.lower() for t in NUMBER.findall(s)}


def formatted(x) -> list[str]:
    """How the scenes print a value: a string as is; an int plain and with
    thousands separators; a float plain, to one decimal, as an int when
    whole, and rounded."""
    if isinstance(x, bool) or x is None:
        return []
    if isinstance(x, str):
        return [x]
    if isinstance(x, int):
        return [str(x), vocab.thousands(x)]
    if isinstance(x, float):
        out = [str(x), f"{x:.1f}", str(round(x)), vocab.thousands(round(x))]
        if x.is_integer():
            out.append(str(int(x)))
        return out
    if isinstance(x, Fraction):
        return [str(x.numerator), str(x.denominator)]
    return [str(x)]


def leaves(x, out: list) -> list:
    if isinstance(x, dict):
        for v in x.values():
            leaves(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            leaves(v, out)
    else:
        out.append(x)
    return out


def known_tokens(numbers: dict) -> set[str]:
    """The numbers in numbers()'s leaves, plus the digits in the libraries'
    names (static/data/libraries.json: "FP127", "PRBMath SD59x18", …)."""
    toks = set()
    for leaf in leaves(numbers, []):
        for f in formatted(leaf):
            toks |= number_tokens(f)
    for rec in vocab.libs().values():
        for k in ("id", "label", "short", "long"):
            toks |= number_tokens(str(rec.get(k, "")))
    return toks


def dry_run(mod) -> "vocab.DeckScene":
    """Run the module's DeckScene subclass under manim's dry run and return it."""
    classes = [c for _, c in inspect.getmembers(mod, inspect.isclass) if issubclass(c, vocab.DeckScene) and c is not vocab.DeckScene and c.__module__ == mod.__name__]
    assert len(classes) == 1, (mod.__name__, classes)
    config.dry_run = True
    vocab.reset_drawn()
    scene = classes[0]()
    scene.render()
    return scene


def check_drawn(name: str, mod, numbers: dict) -> int:
    """Every drawn string with a digit is pinned by numbers() or LITERALS.
    Returns the count of unsupported strings (printed)."""
    literals = getattr(mod, "LITERALS", {})
    assert isinstance(literals, dict) and all(isinstance(k, str) and isinstance(v, str) and v for k, v in literals.items()), name
    scene = dry_run(mod)
    drawn = list(vocab.DRAWN)
    assert len(scene.SECTIONS) >= 2, (name, scene.SECTIONS)
    assert scene.sections_called == list(scene.SECTIONS), (name, scene.sections_called, scene.SECTIONS)
    toks = known_tokens(numbers)
    bad, seen = 0, set()
    for s in drawn:
        assert "…" not in s and "½" not in s, (name, s)
        if s in seen:
            continue
        seen.add(s)
        if s in literals:
            if literals[s] == "REPORT":
                print(f'REPORT {name} "{s}"')
            continue
        missing = number_tokens(s) - toks
        if missing:
            bad += 1
            print(f'UNSUPPORTED {name} "{s}" (not in numbers(): {sorted(missing)})')
    unused = [k for k in literals if k not in seen]
    for k in unused:
        print(f'UNUSED LITERAL {name} "{k}"')
    return bad + len(unused)


def expect_s02_exp40(mod) -> dict:
    p = vocab.probe(mod.OP, mod.ARG)
    lib = vocab.libs()
    # the truth to 80 decimals by the other route: mpmath's own string, truncated one place
    # further than the probe's and rounded there by hand (the probe's 24 decimals must agree)
    import mpmath

    mpmath.mp.dps = 120
    long = mpmath.nstr(mpmath.exp(40), 110, strip_zeros=False)
    li, _, lf = long.partition(".")
    lf = lf[: mod.TRUTH_DECIMALS + 1]
    scaled = (int(li + lf) + 5) // 10
    truth = f"{scaled // 10**mod.TRUTH_DECIMALS}.{scaled % 10**mod.TRUTH_DECIMALS:0{mod.TRUTH_DECIMALS}d}"
    assert truth.startswith(p["truth"][:-1]) and len(truth.partition(".")[2]) == mod.TRUTH_DECIMALS
    int_len = len(truth.partition(".")[0])
    word_digits = int_len + mod.WORD_DECIMALS
    # the first row, e^40 to 18 decimals, by integer arithmetic: round half-up at the 18th
    ti, _, tf = truth.partition(".")
    q = 10 ** (len(tf) - mod.WORD_DECIMALS)
    scaled = (int(ti + tf) * 2 + q) // (2 * q)
    exact_row = f"{scaled // 10**mod.WORD_DECIMALS}.{scaled % 10**mod.WORD_DECIMALS:0{mod.WORD_DECIMALS}d}"
    assert exact_row == vocab.correctly_rounded_18(p["truth"]) == vocab.correctly_rounded_18(truth), exact_row
    rows = []
    for lid in mod.LIBS:
        v = p["cells"][lid]["value"]
        assert not p["cells"][lid].get("reverted") and not p["cells"][lid].get("zero"), lid
        m = vocab.matching_digits(v, truth)
        rows.append(
            {
                "id": lid,
                "label": lib[lid]["label"],
                "value": v,
                # decimals by the other route: the matching prefix less the integer part,
                # 0 when the prefix ends inside the integer part
                "decimals": m - int_len if m >= int_len else 0,
                "matching": m,
                "digits": vocab.correct_digits(v, truth),
                "first_wrong": vocab.first_wrong_index(v, truth),
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
        wd = rows[-1]["decimals"] + 1 if v.partition(".")[0] == truth.partition(".")[0] else 0
        rows[-1]["wrong_decimal"] = wd
        rows[-1]["right_label"] = (
            f"{rows[-1]['decimals']} right · wrong at the {mod.ordinal(wd)} decimal" if wd else f"{rows[-1]['decimals']} right · wrong before the point"
        )
    # the story the slide tells, checked against the cells: 3rd, 4th, and one wrong before the point (V29)
    by_id = {r["id"]: r for r in rows}
    assert by_id["solady"]["wrong_decimal"] == 3 and by_id["solady"]["right_label"] == "2 right · wrong at the 3rd decimal", by_id["solady"]
    assert by_id["balancer"]["wrong_decimal"] == 4 and by_id["balancer"]["right_label"] == "3 right · wrong at the 4th decimal", by_id["balancer"]
    assert by_id["prb"]["wrong_decimal"] == 0 and by_id["prb"]["decimals"] == 0 and by_id["prb"]["right_label"] == "0 right · wrong before the point", by_id["prb"]
    assert mod.ordinal(1) == "1st" and mod.ordinal(2) == "2nd" and mod.ordinal(11) == "11th" and mod.ordinal(13) == "13th" and mod.ordinal(21) == "21st" and mod.ordinal(22) == "22nd"
    # the words by the other route: scripts/replays/bunni.py's decoders, Decimal for the expansion
    bunni = vocab._import_script("scripts/replays/bunni.py")
    decode = {"fp19": bunni.fp19_value, "fp127": bunni.fp127_value}
    ours = []
    with localcontext() as ctx:
        ctx.prec = 200
        for lid in mod.OURS:
            c = p["cells"][lid]
            q = decode[lid](int(c["raw"]))
            v = str((Decimal(q.numerator) / Decimal(q.denominator)).quantize(Decimal(1).scaleb(-mod.TRUTH_DECIMALS), rounding=ROUND_HALF_UP))
            m = 0
            for a, b in zip(v.replace(".", ""), truth.replace(".", "")):
                if a != b:
                    break
                m += 1
            assert m >= word_digits, (lid, m)  # every one of the 18 decimals is right
            # the cell's log measure never exceeds the prefix count by more than one (a floor of a floor)
            assert int(c["digits"]) <= m <= int(c["digits"]) + 1, (lid, c["digits"], m)
            word18 = str(Decimal(v).quantize(Decimal(1).scaleb(-mod.WORD_DECIMALS), rounding=ROUND_HALF_UP))
            assert word18 == exact_row, (lid, word18, exact_row)
            ours.append({"id": lid, "label": lib[lid]["label"], "value": v, "word18": word18, "matching": m, "digits": int(c["digits"]), "right_label": f"{mod.WORD_DECIMALS} right of {mod.WORD_DECIMALS} · {m} digits right"})
    # the reveal rows carry the plain count like the others, and never what the format holds
    for o in ours:
        assert "holds" not in o["right_label"], o["right_label"]
    # no number on the slide is cut short: every row is exactly 18 decimals, no ellipsis
    for s in [exact_row] + [r["value"] for r in rows] + [o["word18"] for o in ours]:
        assert "…" not in s and len(s.partition(".")[2]) == mod.WORD_DECIMALS, s
    assert "…" not in mod.EXACT_LABEL and "…" not in mod.EXACT_RIGHT
    return {
        "truth": truth,
        "truth_decimals": mod.TRUTH_DECIMALS,
        "truth_probe": p["truth"],
        "word_digits": word_digits,
        "exact_row": exact_row,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": exact_row,
    }


def expect_s04_grid(mod) -> dict:
    p = vocab.probe(mod.OP, mod.ARG)
    truth = vocab.truth80()
    assert truth.startswith(p["truth"][:-1]) and len(truth.partition(".")[2]) == mod.EXPANSION_DECIMALS == mod.TRUTH_DECIMALS
    with localcontext() as ctx:
        ctx.prec = 200
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
        # the readings go exactly as far as the truth does, part from each other, and FP127's word to 18 decimals is the closest 18-decimal value
        assert neighbours_128[0] != neighbours_128[1] and word18 == vocab.correctly_rounded_18(truth), (neighbours_128, word18)
        # the two words differ by one in the last place of their 32-hex-digit fractions, shown complete
        hexes = [f"0x{w % (1 << mod.FRACTION_BITS):032x}" for w in (lob, hib)]
        assert all(len(h) == 2 + mod.HEX_DIGITS and "…" not in h for h in hexes) and int(hexes[1], 16) - int(hexes[0], 16) == 1, hexes
        # every level's neighbours: floor and floor + 1 at that level, written complete
        levels = list(range(mod.WORD_DECIMALS + 1))
        neighbours_decimal = []
        for k in levels:
            qk = Decimal(1).scaleb(-k)
            lo = t.quantize(qk, rounding=ROUND_FLOOR)
            neighbours_decimal.append([str(lo), str(lo + qk)])
        bits = list(range(mod.BIT_START, mod.FRACTION_BITS + 1, mod.BIT_STEP))
        neighbours_hex = []
        for b in bits:
            w = int((t * Decimal(2) ** b).to_integral_value(rounding=ROUND_FLOOR))
            neighbours_hex.append([f"0x{(w + m) % (1 << b):0{b // 4}x}" for m in (0, 1)])
    assert bits[-1] == mod.FRACTION_BITS and all(b % 4 == 0 for b in bits)  # every binary level's fraction is whole hex digits
    return {
        "truth": truth,
        "truth_probe": p["truth"],
        "expansion_decimals": mod.EXPANSION_DECIMALS,
        "levels_decimal": mod.WORD_DECIMALS,
        "decimal_levels": levels,
        "bases": [10, 2],
        "neighbours_decimal": neighbours_decimal,
        "neighbours_hex_levels": neighbours_hex,
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
    rows = [{"date": r["date"], "protocol": r["protocol"], "rounding": r["rounding"], "loss": r["loss"]} for r in d["incidents"]]
    total = sum(r["lossUsd"] for r in d["incidents"])
    assert total > 130_000_000, total  # the slide says more than $130 million (V49: the figures are listed, not summed)
    assert [r["date"][-4:] for r in rows] == sorted(r["date"][-4:] for r in rows), "oldest first"
    assert "sum" not in mod.numbers() and not any("sum" in r for r in mod.numbers()["rows"])
    for r in rows:
        assert "wrong way" not in r["rounding"], r  # V27: one rounding step, never "rounded the wrong way"
    assert len(rows) + 1 == len(mod.Cost.SECTIONS), (len(rows), mod.Cost.SECTIONS)
    return {"rows": rows, "total": d["total"], "since": d["since"], "caption": f"talk/scenes/data/incidents.json · since {d['since']}"}


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
    rate_exp = int(cite[573].split("1e")[1].split(" ")[0])
    assert rate_exp == 36
    return {
        "block": f"{int(p['block']):,}",
        "rate_exp": rate_exp,
        "base": 10,
        "grid_ticks": [0, 1, 2],
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
    assert mod.CLOSE_FIRST == "Blockulator's lines start higher and keep the gap" and "flat" not in mod.CLOSE_FIRST  # V14
    return {"N": N, "log10": [first["log10"][str(n)] for n in N], "axisMax": first["axisMax"], "y_ticks": list(range(0, int(first["axisMax"]) + 1, 20)), "wad_decimals": 18, "scenarios": scenarios}


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
    # V28: FP127 has 0 digits at −89 (a value, 2^-128) and a digit still at −88
    assert by_arg["-89"]["fp127"] == {"kind": "value", "digits": 0.0} and by_arg["-88"]["fp127"]["digits"] >= 1, (by_arg["-89"]["fp127"], by_arg["-88"]["fp127"])
    assert all(c["cells"]["fp19"]["kind"] == "value" and c["cells"]["fp19"]["digits"] > 60 for c in columns)
    fp19_min = min(c["cells"]["fp19"]["digits"] for c in columns)
    # FP127's last standing point: the last probe where its value still had a digit (by the raw cells)
    standing = [p for p in probes if not p["cells"]["fp127"].get("zero") and not p["cells"]["fp127"].get("reverted") and float(p["cells"]["fp127"]["digits"]) >= 1]
    assert standing[-1]["args"][0] == "-88", standing[-1]["args"]  # the closing line: "FP127 has digits to exp(−88)" (V28)
    wad = [lid for lid in lids if lib[lid]["family"] == "wad"]
    first_zero = next(p["args"][0] for p in probes if any(p["cells"][lid].get("zero") for lid in wad))
    return {
        "libs": [{"id": lid, "label": lib[lid]["label"], "family": lib[lid]["family"], "ours": bool(lib[lid].get("ours"))} for lid in lids],
        "absent": absent,
        "columns": columns,
        "axisMax": axis_max,
        "y_ticks": list(range(0, axis_max + 1, mod.Y_STEP)),
        "wad_decimals": 18,
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
    return {
        "points": pts,
        "count": len(pts),
        "counts": counts,
        "block": f"{survey['block']:,}",
        "date": survey["date"],
        "axis_ticks": [0, 10, 20, 30, 40, 50, 60, 70, 80],
        "above": above,
        "above_fp19": above_fp19,
        "medians": medians,
        "medians_rounded": {k: int(Decimal(str(v)).quantize(Decimal(1), rounding="ROUND_HALF_EVEN")) for k, v in medians.items()},
        "margins": margins,
    }


def expect_s07_two(mod) -> dict:
    inc = vocab.incidents()["incidents"]
    names = [i["protocol"] for i in inc]
    with localcontext() as ctx:
        ctx.prec = 120

        def dec(x: Decimal, places: int) -> str:  # nearest, half-up, by Decimal (the scene used integer arithmetic on Fractions)
            return str(x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))

        # row 1: the rate by Decimal, as slide 6's check; the scene reuses slide 6's strings
        s06 = mod.resupply_numbers()
        price = int(vocab.resupply()["pins"]["price"])
        rate = Decimal(10 ** s06["rate_exp"]) / Decimal(price)
        rate22, floor1 = dec(rate, 22), str(int(rate.to_integral_value(rounding=ROUND_FLOOR)))
        assert rate22 == s06["rate_short"] and floor1 == s06["floor"] == "0" and s06["rate_label"] == "(to 22 decimals)" and Decimal(rate22) < Decimal("0.5"), (rate22, floor1)  # C1, V12
        # row 2: the first withdrawal's subtrahend from the raw operands; the chain's idle balance fell by its floor
        bj = vocab._load("scripts/replays/bunni.json")
        idle0, s0, t0 = int(bj["start"]["idle"]), int(bj["steps"]["shares"][0]), int(bj["start"]["totalSupply"])
        sub = Decimal(idle0) * Decimal(s0) / Decimal(t0)
        sub3, sub_floor = dec(sub, mod.SUB_DECIMALS), int(sub.to_integral_value(rounding=ROUND_FLOOR))
        assert Fraction(idle0 * s0, t0) == Fraction(sub3) + (Fraction(idle0 * s0, t0) - Fraction(sub3)) and abs(Fraction(idle0 * s0, t0) - Fraction(sub3)) < Fraction(1, 2 * 10**mod.SUB_DECIMALS)
        assert int(bj["snapshots"]["after"][0]) == 1 and idle0 - int(bj["snapshots"]["idle"][0]) == sub_floor == 23, sub_floor  # C2
        active = [int(a) for a in vocab.bunni_replay()["seq"]["deployed"]]
        withdrawals = len(active) - 1
        assert withdrawals == len(bj["steps"]["shares"]) == 44 and active[0] == 28 and active[-1] == 4, (withdrawals, active[0], active[-1])  # C2: 44 withdrawals, 28 → 4
        # row 3: the upscale from the rate in the tx; mulDown floors it, mulUp would not
        bal = vocab.balancer()
        pool, score = bal["pools"]["osETH"], bal["score"]["osETH"]
        factor = int(pool["rateCacheUpdatedInTx"]["providerRate"])
        micro = [s for s in score["steps"] if s["what"] == "micro"]
        cycles = len(micro)
        assert cycles == score["kinds"]["micro"] == 30 and {int(s["out"]) for s in micro} == {17}, cycles  # C3
        out = int(micro[0]["out"])
        up = Decimal(out) * Decimal(factor) / Decimal(10**18)
        up18, mul_down = dec(up, 18), int(up.to_integral_value(rounding=ROUND_FLOOR))
        assert up18 == "17.988250947729518883" and mul_down == 17 and all(int(s["upscaledOutDeployed"]) == 17 and int(s["upscaledOutMulUp"]) == 18 for s in micro), up18  # C3
        assert Fraction(up18) == Fraction(out * factor, 10**18), "17 × the factor is exact at 18 decimals"
        # row 4: the first mint's charge, exactly two thirds; every charge 0 across the 37 mints
        tj = vocab.thetanuts()
        mints = tj["mints"]
        m0 = mints[0]
        amount, held, supply = int(m0["amount"]), int(m0["storedBefore"][0]), int(m0["supplyBefore"])
        charge = Fraction(amount * held, supply)
        assert charge == Fraction(2, 3) and (amount, held, supply) == (2, 1, 3) and len(mints) == 37 and supply == int(tj["claim"]["supplyAfter"])  # C4, C8
        assert all(int(c) == 0 for m in mints for c in m["charge"]) and all(int(h) == 1 for m in mints[:1] for h in m["storedBefore"])
        # row 5: BNum's ratio at a balance of 3, pools 1–3 (pools 4–5 land lower: C5); × 3 by Decimal; half-up to 4
        v1 = vocab.balancer_v1_replay()
        at3 = [[r for r in p if r["kind"] == 2 and r["balance"] == 3] for p in v1]
        ratios = [{int(r["steps"]["tokenInRatio"]) for r in rows} for rows in at3]
        assert ratios[0] == ratios[1] == ratios[2] and len(ratios[0]) == 1 and ratios[3] == ratios[4] and ratios[3] != ratios[0], ratios
        (ratio,) = ratios[0]
        product = Decimal(3) * Decimal(ratio) / Decimal(10**18)
        prod18, nearest = dec(product, 18), int(product.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        assert prod18 == "4.499999999999999991" and nearest == 4 and Decimal(prod18) < Decimal("4.5"), prod18  # C5, V27: nearest, and still 4
        assert all(int(r["steps"]["newTokenBalanceIn"]) == 4 and int(r["deployed"]) == 1 for rows in at3[:3] for r in rows)
        joins = sum(1 for p in v1 for r in p if r["kind"] == 2)
        assert joins == 438 and sum(len(rows) for rows in at3) == 400, joins  # C5
    # the strings: complete in a stated format, never cut short
    for s, places in ((rate22, 22), (sub3, mod.SUB_DECIMALS), (up18, 18), (prod18, 18)):
        assert "…" not in s and len(s.partition(".")[2]) == places, (s, places)
    assert "floored" not in mod.MECH_V1 and mod.MECH_V1.startswith("nearest") and mod.MECH_RESUPPLY == "floored once" and "would have cost" in mod.CEIL_LABEL  # flags
    rows = [
        {"id": "resupply", "protocol": names[0], "date": inc[0]["date"], "ticks": [0, 1], "x": float(Fraction(10 ** s06["rate_exp"], price)), "exact": rate22, "exact_label": s06["rate_label"], "rounded": floor1, "to": 0, "mechanism": mod.MECH_RESUPPLY},
        {
            "id": "bunni",
            "protocol": names[1],
            "date": inc[1]["date"],
            "ticks": [sub_floor, sub_floor + 1],
            "x": float(Fraction(idle0 * s0, t0)),
            "exact": sub3,
            "exact_label": f"(to {mod.SUB_DECIMALS} decimals)",
            "rounded": str(sub_floor),
            "to": sub_floor,
            "mechanism": mod.mech_bunni(withdrawals, active[0], active[-1]),
            "counter": [mod.mech_bunni(k, active[0], active[k]) for k in range(1, withdrawals + 1)],
            "withdrawals": withdrawals,
            "active": active,
        },
        {
            "id": "balancer-v2",
            "protocol": names[2],
            "date": inc[2]["date"],
            "ticks": [mul_down, mul_down + 1],
            "x": float(Fraction(out * factor, 10**18)),
            "exact": up18,
            "exact_label": "(to 18 decimals)",
            "rounded": str(mul_down),
            "to": mul_down,
            "mechanism": mod.mech_v2(cycles),
            "counter": [mod.mech_v2(k) for k in range(1, cycles + 1)],
            "cycles": cycles,
            "out": out,
            "factor": str(factor),
        },
        {
            "id": "thetanuts",
            "protocol": names[3],
            "date": inc[3]["date"],
            "ticks": [0, 1],
            "x": float(charge),
            "exact": mod.TWO_THIRDS,
            "exact_label": mod.TWO_THIRDS_FRACTION,
            "rounded": "0",
            "to": 0,
            "mechanism": mod.MECH_THETANUTS.format(mints=len(mints), charge=0),
            "mints": len(mints),
            "operands": [amount, held, supply],
            "other_way": 1,
            "other_label": mod.CEIL_LABEL,
        },
        {
            "id": "balancer-v1",
            "protocol": names[4],
            "date": inc[4]["date"],
            "ticks": [nearest, nearest + 1],
            "x": float(Fraction(3 * ratio, 10**18)),
            "exact": prod18,
            "exact_label": "(to 18 decimals)",
            "rounded": str(nearest),
            "to": nearest,
            "mechanism": mod.MECH_V1,
            "ratio": str(ratio),
            "balance": 3,
            "joins": joins,
            "other_way": nearest + 1,
            "other_label": mod.TOWARD_POOL,
        },
    ]
    assert mod.Two.SECTIONS == ("bands", "resupply", "bunni", "balancer-v2", "round-once", "thetanuts", "balancer-v1", "direction", "box")
    return {"rows": rows, "half": 0.5, "wad_decimals": 18}


EXPECT = {
    "s02_exp40": expect_s02_exp40,
    "s04_grid": expect_s04_grid,
    "s05_cost": expect_s05_cost,
    "s06_resupply": expect_s06_resupply,
    "s07_two": expect_s07_two,
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
        n_bad = check_drawn(name, mod, drawn)
        if n_bad:
            bad += 1
            print(f"FAIL  {name}: {n_bad} drawn strings unsupported")
        else:
            print(f"ok    {name} drawn")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

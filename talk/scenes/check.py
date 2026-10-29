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
    # one section only for the looping title (slides.yaml loop: true), whose last frame must be its first
    assert len(scene.SECTIONS) >= 2 or getattr(scene, "LOOP", False), (name, scene.SECTIONS)
    if getattr(scene, "LOOP", False):
        assert scene.start_state == scene.end_state and len(scene.start_state) > 0, (name, "the loop must end where it starts")
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
    # the words by the other route: each raw word's fields read with masks and shifts written here
    # (contracts/src/fp19/README.md lines 21-24: sign bit 255, E bits 254..236 bias 262143, F bits 235..0,
    # value = (2^236 + F) * 2^(E - 262143 - 236); FP127: an int256, value = raw / 2^128), the expansion
    # by Decimal at a precision wide enough that a division by a power of two is exact
    def decode(lid: str, raw: int) -> tuple[int, int]:
        """(numerator, k): value = numerator / 2^k, k >= 0."""
        if lid == "fp127":
            assert raw < 2**255, raw  # positive
            return raw, 128
        assert raw >> 255 == 0 and raw != 0, raw  # positive, not zero
        e = (raw >> 236) & 0x7FFFF
        f = raw & ((1 << 236) - 1)
        assert 1 <= e <= 0x7FFFF, e
        shift = e - 262143 - 236
        sig = (1 << 236) | f
        return (sig << shift, 0) if shift >= 0 else (sig, -shift)

    ours = []
    with localcontext() as ctx:
        ctx.prec = 600
        for lid in mod.OURS:
            c = p["cells"][lid]
            num, k = decode(lid, int(c["raw"]))
            # lose the trailing zero bits so k is the number of decimals the expansion needs (2^-k ends at the k-th)
            while k and num % 2 == 0:
                num //= 2
                k -= 1
            d = Decimal(num) / (Decimal(2) ** k)
            assert d * Decimal(2) ** k == Decimal(num), lid  # the division was exact
            word = format(d, "f")
            assert len(word.partition(".")[2]) == k, (lid, k, word)
            assert not word.endswith("0") and "…" not in word, word  # complete and not padded
            # the words agree with vocab's Fraction decoders
            assert Fraction(num, 2**k) == vocab.word_value(lid, c["raw"]), lid
            v = str(d.quantize(Decimal(1).scaleb(-mod.TRUTH_DECIMALS), rounding=ROUND_HALF_UP))
            m = 0
            for a, b in zip(word.replace(".", ""), truth.replace(".", "")):
                if a != b:
                    break
                m += 1
            assert m >= word_digits, (lid, m)  # every one of the 18 decimals is right
            # the cell's log measure never exceeds the prefix count by more than one (a floor of a floor)
            assert int(c["digits"]) <= m <= int(c["digits"]) + 1, (lid, c["digits"], m)
            word18 = str(d.quantize(Decimal(1).scaleb(-mod.WORD_DECIMALS), rounding=ROUND_HALF_UP))
            assert word18 == exact_row, (lid, word18, exact_row)
            dec = m - int_len
            assert mod.WORD_DECIMALS <= dec < k, (lid, dec, k)
            # the lines the slide draws hold every decimal once, in order, none longer than the first
            lines = [word.partition(".")[0] + "." + word.partition(".")[2][: mod.LINE1]]
            rest = word.partition(".")[2][mod.LINE1 :]
            lines += [rest[i : i + mod.LINE] for i in range(0, len(rest), mod.LINE)]
            assert "".join(lines) == word and len(lines[0]) == int_len + 1 + mod.LINE1 and all(len(ln) <= mod.LINE for ln in lines[1:]), (lid, lines)
            ours.append(
                {
                    "id": lid,
                    "label": lib[lid]["label"],
                    "value": v,
                    "word": word,
                    "word_decimals": k,
                    "lines": lines,
                    "word18": word18,
                    "matching": m,
                    "decimals_right": dec,
                    "digits": int(c["digits"]),
                    "right_label": f"{m} digits right · {dec} decimals",
                    "end_label": f"the word's precision ends here · {dec} decimals",
                }
            )
    by = {o["id"]: o for o in ours}
    # the story: FP127 matches 57 digits (18 + 39 decimals), FP19 73 (18 + 55); the counts the user named
    assert (by["fp127"]["matching"], by["fp127"]["decimals_right"]) == (57, 39), by["fp127"]
    assert (by["fp19"]["matching"], by["fp19"]["decimals_right"]) == (73, 55), by["fp19"]
    assert by["fp127"]["word_decimals"] == 127 and by["fp19"]["word_decimals"] == 179, (by["fp127"]["word_decimals"], by["fp19"]["word_decimals"])
    # the reveal rows carry the plain count like the others, and never what the format holds
    for o in ours:
        assert "holds" not in o["right_label"] and "holds" not in o["end_label"], o
    # no number on the slide is cut short: every 18-decimal row is exactly 18 decimals, no ellipsis anywhere
    for s in [exact_row] + [r["value"] for r in rows] + [o["word18"] for o in ours]:
        assert "…" not in s and len(s.partition(".")[2]) == mod.WORD_DECIMALS, s
    assert "…" not in mod.EXACT_LABEL and "…" not in mod.EXACT_RIGHT and "…" not in mod.CLOSE and "…" not in mod.END_TEXT
    longest = max(o["word_decimals"] for o in ours)
    return {
        "truth": truth,
        "truth_decimals": mod.TRUTH_DECIMALS,
        "truth_probe": p["truth"],
        "word_digits": word_digits,
        "exact_row": exact_row,
        "rows": rows,
        "ours": ours,
        "correctly_rounded": exact_row,
        "fp127_word": by["fp127"]["word"],
        "fp19_word": by["fp19"]["word"],
        "fp127_match": by["fp127"]["matching"],
        "fp19_match": by["fp19"]["matching"],
        "fp127_decimals": by["fp127"]["decimals_right"],
        "fp19_decimals": by["fp19"]["decimals_right"],
        "ruler_marks": [t for t in range(10, longest + 1, 10)],
        "context": " · ".join(r["label"] for r in rows) + ": " + " · ".join(str(r["decimals"]) for r in rows) + " decimals right",
        "close2": " · ".join(f"{o['label']}: {o['decimals_right']} decimals" for o in ours) + " · every one of them right",
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


def expect_s06b_bunni(mod) -> dict:
    """The decisive step by a second route (Decimal), the chain's own reads
    for the start and the end, the replay table cross-checked against the
    JSON and the module where both have a figure."""
    d = vocab._load("scripts/replays/bunni.json")
    st, steps = d["start"], d["steps"]
    raw0, idle0, T0, s0 = int(st["raw0"]), int(st["idle"]), int(st["totalSupply"]), int(steps["shares"][0])
    inc = next(i for i in vocab.incidents()["incidents"] if i["protocol"].startswith("Bunni"))
    with localcontext() as ctx:
        ctx.prec = 120

        def dec(x: Decimal, places: int) -> str:
            return format(x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), "f")

        sub = Decimal(idle0) * Decimal(s0) / Decimal(T0)
        sub_str = dec(sub, mod.SUB_DECIMALS)
        floor = int(sub.to_integral_value(rounding=ROUND_FLOOR))
        kept = dec(sub - floor, mod.SUB_DECIMALS)
    # the first withdrawal, with Fraction: 23.659 floors to 23 and the chain's idle balance fell by exactly that
    assert Fraction(idle0 * s0, T0) > floor and floor == idle0 * s0 // T0 == idle0 - int(d["snapshots"]["idle"][0]) and int(d["snapshots"]["after"][0]) == 1
    # the end of it, from the chain's own reads (C2): active USDC after 44 = raw + redeem − idle at the last snapshot
    hk, last = d["hookAfter"], {k: int(v[-1]) for k, v in d["snapshots"].items() if k != "trace"}
    assert last["after"] == len(steps["shares"]) == 44
    # the vault shares' redeem value by the EVK formula from the cited lines (ConversionHelpers.sol:22, Shares.sol:25):
    # shares × (cash + totalBorrows + 1e6) / (totalShares + 1e6), floored
    v0 = st["vault0"]
    redeem0 = int(st["reserve0"]) * (int(v0["cash"]) + int(v0["totalBorrows"]) + 10**6) // (int(v0["totalShares"]) + 10**6)
    assert int(d["observed"]["swap3"]["idle"]) == idle0
    active_start = raw0 + redeem0 - idle0
    active_end = last["raw0"] + int(hk["previewRedeem0"]) - last["idle"]
    assert (active_start, active_end) == (28, 4), (active_start, active_end)
    r = vocab.bunni_replay()
    active = [int(a) for a in r["seq"]["deployed"]]
    assert active[0] == active_start and active[-1] == active_end and len(active) == 45
    L0, L1 = int(d["observed"]["swap3"]["totalLiquidity"]), int(d["observed"]["afterWithdrawals"]["totalLiquidity"])
    with localcontext() as ctx:
        ctx.prec = 60
        pct = dec((Decimal(L1) / Decimal(L0) - 1) * 100, mod.PCT_DECIMALS).replace("-", "−") + "%"
    assert pct == "−84.37%", pct
    # the replay table against the JSON and the module where both have a figure
    lq = vocab.bunni_liquidity()
    table = {row["idle balance"]: row for row in vocab.replay_table("bunni", mod.TABLE_HEADING)}
    dep = next(v for k, v in table.items() if k.startswith("deployed"))
    assert int(dep["active USDC after 44 (wei)"]) == active_end and int(dep["total liquidity after"]) == L1 == lq["forms"]["deployed"]
    fix = next(v for k, v in table.items() if "mulDivUp" in k)
    assert int(fix["active USDC after 44 (wei)"]) == r["seq"]["mulDivUp"][-1] == 48 and int(fix["total liquidity after"]) == lq["forms"]["mulDivUp"]
    fp127 = table["FP127 idle balance"]
    assert fp127["active USDC after 44 (wei)"] == vocab.to_decimals(r["seq"]["fp127"][-1], mod.WORD_DECIMALS) and int(fp127["total liquidity after"]) == lq["forms"]["fp127"]
    with localcontext() as ctx:
        ctx.prec = 60
        fix_pct = dec((Decimal(lq["forms"]["mulDivUp"]) / Decimal(lq["start"]) - 1) * 100, mod.PCT_FIX_DECIMALS).replace("-", "−") + "%"
        assert fix_pct == fix["change"].replace("-", "−") == fp127["change"].replace("-", "−"), (fix_pct, fix["change"])
        assert dec((Decimal(L1) / Decimal(lq["start"]) - 1) * 100, 7).replace("-", "−") + "%" == dep["change"].replace("-", "−")
    fp19 = table["FP19 idle balance"]["active USDC after 44 (wei)"]  # the forge run's; the table alone carries it (REPORT)
    cite = next(c for c in d["cites"] if c["id"] == "idle")
    assert cite["file"] == "src/lib/BunniHubLogic.sol" and cite["line"] == 478
    for k, v in mod.numbers().items():
        assert "…" not in str(v), (k, v)
    return {
        "protocol": inc["protocol"],
        "date": inc["date"],
        "chain": "Ethereum",
        "block": f"{int(d['tx']['block']):,}",
        "tx_short": d["tx"]["hash"][: 2 + mod.TX_SHORT],
        "tx_short_len": mod.TX_SHORT,
        "tx_len": 64,
        "raw": f"{raw0:,}",
        "redeem": f"{redeem0:,}",
        "idle": f"{idle0:,}",
        "active_start": active_start,
        "active_end": active_end,
        "active": active,
        "withdrawals": 44,
        "shares": f"{s0:,}",
        "supply": f"{T0:,}",
        "sub": sub_str,
        "sub_label": f"(to {mod.SUB_DECIMALS} decimals)",
        "floor": str(floor),
        "kept": kept,
        "grid_ticks": [floor, floor + 1],
        "idle_after": f"{int(d['snapshots']['idle'][0]):,}",
        "cite_file": "BunniHubLogic.sol",
        "cite_line": 478,
        "cite_text": cite["text"],
        "liq_start": f"{L0:,}",
        "liq_end": f"{L1:,}",
        "liq_pct": pct,
        "loss": inc["loss"],
        "up": "48",
        "fp127": fp127["active USDC after 44 (wei)"],
        "fp19": fp19,
        "word_label": f"(to {mod.WORD_DECIMALS} decimals)",
        "fix_pct": fix_pct,
    }


def expect_s06c_balancer_v2(mod) -> dict:
    """The decisive step by the raw trace: the Vault's own onSwap call (not
    the scored step), the rate the attacker's updateTokenRateCache set, the
    product and its mulDown by Fraction, the exact charge from the forge
    harness's expectation, the cycles counted in the trace, the
    counterfactual's figures from the generated table."""
    d = vocab.balancer()
    pool, test, score = d["pools"][mod.POOL], d["test"][mod.POOL], d["score"][mod.POOL]
    sym = pool["symbols"]
    rk, wk = sym.index(mod.POOL), sym.index("WETH")
    rate = int(pool["rateCacheUpdatedInTx"]["providerRate"])
    first = int(test["first"])  # the replayed phase starts at this swap; the micro swap is the next call
    raw = pool["swaps"][first + mod.MICRO_INDEX]
    assert raw["kind"] == 1 and raw["i"] == wk and raw["j"] == rk, raw  # GIVEN_OUT, WETH in, osETH out
    out, charged = int(raw["amount"]), int(raw["amountIn"])
    assert charged == 625_492 and out == 17, (charged, out)  # C3
    product = Fraction(out * rate, 10**mod.WAD)
    mul_down, mul_up = product.numerator // product.denominator, -(-product.numerator // product.denominator)
    assert mul_down == 17 and mul_up == 18 and product != mul_down, (mul_down, mul_up)  # C3: mulDown keeps 17, mulUp would give 18
    exact = int(test["expectExact"][mod.MICRO_INDEX])
    assert exact == 957_169, exact  # C3
    with localcontext() as ctx:
        ctx.prec = 60

        def dec(x, places: int) -> str:
            return f"{Decimal(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP):,}"

        under_pct = dec((1 - Decimal(charged) / Decimal(exact)) * 100, mod.PCT_DECIMALS) + "%"
        assert under_pct == "34.65%", under_pct  # C3
        product_str = dec(Decimal(out * rate) / Decimal(10**mod.WAD), mod.WAD)
        rate_str = dec(Decimal(rate) / Decimal(10**mod.WAD), mod.WAD)
        d_start, d_end = Decimal(score["trueInvariantStart"]), Decimal(score["trueInvariantEnd"])
        ratio = Decimal(score["onchainInvariantRatio"])
        assert (d_end / d_start).quantize(Decimal(1).scaleb(-mod.RATIO_DECIMALS)) == ratio.quantize(Decimal(1).scaleb(-mod.RATIO_DECIMALS))
        levels = [float(Decimal(score["steps"][3 * c]["trueInvariantBefore"]) / d_start) for c in range(1, score["kinds"]["micro"])] + [float(d_end / d_start)]
        d_start_s, d_end_s, ratio_s = dec(d_start, mod.INVARIANT_DECIMALS), dec(d_end, mod.INVARIANT_DECIMALS), "×" + dec(ratio, mod.RATIO_DECIMALS)
        net = dec(score["batchSwapNetEth"], mod.NET_DECIMALS)
    # the cycles, counted in the trace: every GIVEN_OUT micro swap of `out` wei of the rate token
    cycles = sum(1 for s in pool["swaps"] if s["kind"] == 1 and s["j"] == rk and int(s["amount"]) == out)
    other = d["pools"][mod.OTHER]
    ork = other["symbols"].index(mod.OTHER)
    other_leave = int(d["test"][mod.OTHER]["leave"])
    other_cycles = sum(1 for s in other["swaps"] if s["kind"] == 1 and s["j"] == ork and int(s["amount"]) == other_leave - 1)
    assert (cycles, other_cycles) == (30, 25), (cycles, other_cycles)  # C3
    # the counterfactual from the generated table (the scene cross-checks it against the JSON)
    rulers = {r["model"]: r for r in vocab.replay_table("balancer", "The same calls on five rulers")}
    dep = next(r for m, r in rulers.items() if m.startswith("deployed"))
    fp = next(r for m, r in rulers.items() if m.startswith("FP127"))
    would_lose = str(-Decimal(fp["projected take (ETH)"]))
    inc = next(i for i in vocab.incidents()["incidents"] if i["protocol"] == mod.PROTOCOL)
    cites = pool["source"]["cites"]
    for k, v in mod.numbers().items():
        assert "…" not in str(v), (k, v)
    return {
        "title": f"{mod.PROTOCOL}, {inc['date']}",
        "tx_short": d["provenance"]["tx"][:10],
        "block": f"{int(d['provenance']['block']):,}",
        "chain": "Ethereum",
        "pool": f"{mod.POOL}/WETH",
        "other_pool": f"{mod.OTHER}/WETH",
        "weth_before": f"{int(raw['balances'][wk]):,}",
        "rate_before": f"{int(raw['balances'][rk]):,}",
        "out": str(out),
        "rate": rate_str,
        "product": product_str,
        "product_label": f"(to {mod.WAD} decimals)",
        "grid_ticks": list(range(mod.GRID[0], mod.GRID[1] + 1)),
        "mul_down": str(mul_down),
        "mul_up": str(mul_up),
        "charged": f"{charged:,}",
        "exact": f"{exact:,}",
        "under_pct": under_pct,
        "cycles": cycles,
        "other_cycles": other_cycles,
        "other_out": str(other_leave - 1),
        "other_leave": str(other_leave),
        "counter_ticks": list(range(1, max(cycles, other_cycles) + 1)),
        "d_start": d_start_s,
        "d_end": d_end_s,
        "d_ratio": ratio_s,
        "d_levels": levels,
        "loss": inc["loss"],
        "net_eth": net,
        "deployed_charged_total": dep["charged in (WETH-wei / rate-token-wei)"].split(" / ")[0],
        "fp_charged_total": fp["charged in (WETH-wei / rate-token-wei)"].split(" / ")[0],
        "deployed_below": int(dep["calls below exact"]),
        "fp_below": int(fp["calls below exact"]),
        "would_lose": would_lose,
        "upscale_cite": cites["BasePool.sol:_upscale"].split("/")[-1],
        "muldown_cite": cites["FixedPoint.sol:mulDown"].split("/")[-1],
    }


def expect_s06d_thetanuts(mod) -> dict:
    """The first mint's charge recomputed as a Fraction from the JSON operands
    and the 37 mints rerun with ceil by integer arithmetic; the claim's
    supply 3, the 185 zero transfers, and the ceil total against the
    generated table (docs/benchmarks/replay-thetanuts.md) by replay_table()."""
    from datetime import datetime, timezone

    d = vocab.thetanuts()
    inc = next(i for i in vocab.incidents()["incidents"] if i["protocol"] == mod.INCIDENT)
    mints, claim, comps = d["mints"], d["claim"], d["components"]
    # the state the claim left: supply 3, one raw unit of each of the five components
    assert int(claim["supplyAfter"]) == 3 == int(d["pre"]["totalSupply"]) - int(d["flashLoan"]["amount"]), claim["supplyAfter"]
    assert claim["storedAfter"] == ["1"] * 5 and len(comps) == 5 and mints[0]["storedBefore"] == ["1"] * 5
    # the claim paid floor(stored × amount / supply), at or below the pro-rata share (not inflated)
    for sb, pay, sa in zip(claim["storedBefore"], claim["payout"], claim["storedAfter"]):
        assert int(pay) == int(sb) * int(claim["amount"]) // int(claim["supplyBefore"]) and int(sb) - int(pay) == int(sa)
    # the first mint's charge, as a Fraction of the JSON operands: two thirds
    m0 = mints[0]
    charge0 = Fraction(int(m0["storedBefore"][0]) * int(m0["amount"]), int(m0["supplyBefore"]))
    assert charge0 == Fraction(2, 3) and m0["charge"] == ["0"] * 5
    with localcontext() as ctx:
        ctx.prec = 60
        charge0_str = str((Decimal(charge0.numerator) / Decimal(charge0.denominator)).quantize(Decimal(1).scaleb(-mod.CHARGE_DECIMALS), rounding=ROUND_HALF_UP))
    # 37 mints, 185 component transfers, every one for 0; the supply chains and ends at the post-state
    assert len(mints) == 37 and len(mints) * len(comps) == 185 == int(d["trace"]["transferFromCalls"]) == int(d["trace"]["mintExecutions"])
    assert all(c == "0" for m in mints for c in m["charge"])
    supply = int(claim["supplyAfter"])
    for m in mints:
        assert int(m["supplyBefore"]) == supply and int(m["amount"]) * 1 // supply == 0, m
        supply += int(m["amount"])
    assert supply == int(d["post"]["totalSupply"]) and d["post"]["stored"] == ["1"] * 5
    minted = supply - int(claim["supplyAfter"])
    assert minted == int(d["flashLoan"]["amount"]) + int(d["flashLoan"]["premium"]), "the minted tokens repay the loan and its fee"
    # the counterfactual by the other route: ceil as (num + den - 1) // den, the vault's holding growing by each charge
    held, sup, ceil_total, first_ceil = 1, int(claim["supplyAfter"]), 0, None
    for m in mints:
        a = int(m["amount"])
        c = (held * a + sup - 1) // sup
        first_ceil = c if first_ceil is None else first_ceil
        ceil_total += c
        held += c
        sup += a
    assert first_ceil == 1 and ceil_total == 76_596_174_855, ceil_total
    # the generated table agrees: the ceil rule's total per component, and every mint's ceil charge is 1
    rules = {r["rule"]: r for r in vocab.replay_table("thetanuts", "The decisive step on each rule")}
    assert rules["rounded up (ceil)"]["paid per component, 37 mints"] == f"{ceil_total:,}", rules["rounded up (ceil)"]
    assert rules["rounded up (ceil)"]["first charge (raw units)"] == "1"
    rows = vocab.replay_table("thetanuts", "Every mint, on the chain path")
    assert len(rows) == 37 and all(r["ceil"] == "1" and r["deployed (floor)"] == "0" for r in rows)
    assert [r["amount"] for r in rows] == [f"{int(m['amount']):,}" for m in mints] and [r["supply before"] for r in rows] == [f"{int(m['supplyBefore']):,}" for m in mints]
    assert Decimal(rows[0]["exact charge"]) == (Decimal(2) / Decimal(3)).quantize(Decimal(rows[0]["exact charge"]), rounding=ROUND_HALF_UP)
    per_comp = vocab.replay_table("thetanuts", "Round up: what any mint sequence costs")
    assert [r["paid under round-up, the attacker's 37 amounts"] for r in per_comp] == [f"{ceil_total:,}"] * 5
    assert [r["claim took"] for r in per_comp] == [f"{int(p):,}" for p in claim["payout"]]
    max_take = max(int(p) for p in claim["payout"])
    assert ceil_total > max_take
    # the date: incidents.json's day is the block's (UTC)
    assert datetime.fromtimestamp(int(d["blockTimestamp"]), timezone.utc).strftime("%-d %b %Y") == inc["date"], inc["date"]
    (dec,) = {int(c["decimals"]) for c in comps}
    assert dec == 6 == mod.USDC_DECIMALS

    def tok(raw: int, places: int) -> str:
        return f"{Decimal(raw).scaleb(-places):,.{places}f}"

    usdc = tok(int(d["realised"]["usdcTotal"]), mod.USDC_DECIMALS)
    page = (vocab.ROOT / "docs" / "benchmarks" / "replay-thetanuts.md").read_text(encoding="utf-8")
    assert f"{usdc} USDC" in page, usdc  # the page writes the realised USDC with the same six decimals
    by_addr = {c["address"].lower(): c for c in comps}
    leftovers = [(tok(int(v), dec), by_addr[a.lower()]["symbol"].split("-")[-1]) for a, v in d["realised"]["sentToBeneficiary"].items() if a.lower() in by_addr]
    assert len(leftovers) == 3
    for k, v in mod.numbers().items():
        assert "…" not in str(v), (k, v)
    return {
        "protocol": inc["protocol"],
        "date": inc["date"],
        "vault_name": d["vault"]["name"],
        "tx_short": d["tx"][:10],
        "block": f"{int(d['block']):,}",
        "supply_before": f"{int(d['pre']['totalSupply']):,}",
        "borrowed": f"{int(d['flashLoan']['amount']):,}",
        "supply_after_claim": "3",
        "stored_after": "1",
        "n_components": 5,
        "components": [
            {"label": c["symbol"].split("-")[-1], "stored_before": f"{int(s):,}", "payout": f"{int(p):,}", "stored_after": "1"}
            for c, s, p in zip(comps, claim["storedBefore"], claim["payout"])
        ],
        "pc_mul": 12186,
        "pc_div": 12220,
        "amount0": "2",
        "supply0": "3",
        "charge0": charge0_str,
        "charge0_label": f"(to {mod.CHARGE_DECIMALS} decimals)",
        "charge0_x": Fraction(2, 3),
        "floor0": "0",
        "ceil0": "1",
        "grid_ticks": [0, 1, 2],
        "n_mints": 37,
        "mint_index": list(range(1, 38)),
        "amounts": [f"{int(m['amount']):,}" for m in mints],
        "supplies": [f"{int(m['supplyBefore']):,}" for m in mints],
        "supply_after": f"{int(d['post']['totalSupply']):,}",
        "minted": f"{minted:,}",
        "loan_fee": f"{int(d['flashLoan']['amount']) + int(d['flashLoan']['premium']):,}",
        "zero_transfers": 185,
        "loss": inc["loss"],
        "usdc": usdc,
        "leftovers": leftovers,
        "ceil_total_raw": f"{ceil_total:,}",
        "ceil_total": tok(ceil_total, dec),
        "max_take": tok(max_take, dec),
        "repaid": True,
        "ceil_wins": True,
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
    assert set(counts) == set(mod.PROTOCOL_LABEL) == set(mod.PROTOCOLS), counts
    assert counts == {"aave": 74, "morpho": 252}, counts  # the brief's facet counts

    def median(sub: list[dict], key: str) -> float:  # the middle of the sorted list, by hand
        v = sorted(x[key] for x in sub)
        k = len(v) // 2
        return round((v[k - 1] + v[k]) / 2 if len(v) % 2 == 0 else v[k], 1)

    def summary(sub: list[dict]) -> dict:
        medians = {k: median(sub, k) for k in ("deployed", "fp127", "fp19")}
        margins = {"fp127": round(medians["fp127"] - medians["deployed"], 1), "fp19": round(medians["fp19"] - medians["fp127"], 1)}
        assert margins["fp127"] > 0 and margins["fp19"] > 0
        return {"medians": medians, "margins": margins}

    whole = summary(pts)
    medians = whole["medians"]
    above, above_fp19 = sum(1 for x in pts if x["fp127"] > x["deployed"]), sum(1 for x in pts if x["fp19"] > x["deployed"])
    assert above == above_fp19 == len(pts), (above, above_fp19)
    by_protocol = {p: {"count": counts[p], **summary([x for x in pts if x["protocol"] == p])} for p in ("aave", "morpho")}
    # every facet's rows climb like the whole: deployed < FP127 < FP19
    for p, s in by_protocol.items():
        assert s["medians"]["deployed"] < s["medians"]["fp127"] < s["medians"]["fp19"], (p, s)
    assert medians["deployed"] < medians["fp127"] < medians["fp19"], medians
    return {
        "points": pts,
        "count": len(pts),
        "counts": counts,
        "block": f"{survey['block']:,}",
        "date": survey["date"],
        "axis_ticks": [0, 20, 40, 60, 80],
        "above": above,
        "above_fp19": above_fp19,
        "medians": medians,
        "medians_rounded": {k: int(Decimal(str(v)).quantize(Decimal(1), rounding="ROUND_HALF_EVEN")) for k, v in medians.items()},
        "margins": whole["margins"],
        "by_protocol": by_protocol,
    }


def expect_s16_ziv(mod) -> dict:
    # the sweep rows by hand: the plain pass (no .stage) for each library
    rows = {}
    for r in vocab._load("docs/benchmarks/sweep.json")["rows"]:
        if r["op"] == mod.OP and "stage" not in r and r["lib"] in ("fp19", "fp127"):
            assert r["lib"] not in rows, r["lib"]
            rows[r["lib"]] = r
    lib = vocab.libs()
    fp19, fp127 = rows["fp19"], rows["fp127"]
    # the story (V18): FP19's last stage ran once in its sweep, FP127's never; FP127's n is the scored
    # inputs, the unscored both-revert inputs make up the generated count
    assert fp19["fallback"] == 1 and fp19["fallbackRuns"] == 1 and fp127["fallback"] == 0, (fp19["fallback"], fp127["fallback"])
    assert fp127["n"] + fp127["status"]["gotrev"] == fp127["inputs"] and fp127["status"]["ok"] == fp127["n"], fp127["status"]
    assert fp19["status"]["ok"] == fp19["n"], fp19["status"]
    # the gas median by hand: the middle of the sorted typical inline cells (V19: 2,835)
    g = vocab._load("docs/benchmarks/gas.json")
    cells = sorted(c for c in g["ops"][mod.OP]["typical"]["gas"][mod.GAS_FORM] if c is not None)
    k = len(cells) // 2
    median = (cells[k - 1] + cells[k]) / 2 if len(cells) % 2 == 0 else float(cells[k])
    assert median == 2835, median
    assert mod.GAS_BEFORE_TEST == 2716 and mod.MUL_GAS == 5 and mod.DIVH_GAS == 393  # V19, V32: the figures the ledger verified
    with localcontext() as ctx:
        ctx.prec = 30
        pct = float(((Decimal(median) - mod.GAS_BEFORE_TEST) / mod.GAS_BEFORE_TEST * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    assert 0 < pct < 10, pct  # "a few percent"
    counters = {lid: f"{rows[lid]['fallback']} of {rows[lid]['n']:,}" for lid in ("fp19", "fp127")}
    # every figure carries its library: the fallback counters FP19's and FP127's, the gas line FP127's
    gas_line = f"{lib['fp127']['label']} {mod.OP}: {mod.GAS_BEFORE_TEST:,} → {int(median):,} gas with the test"
    assert gas_line.startswith("FP127") and "FP19" not in gas_line
    return {
        "op": mod.OP,
        "fp19": {"label": lib["fp19"]["label"], "n": fp19["n"], "fallback": fp19["fallback"]},
        "fp127": {"label": lib["fp127"]["label"], "n": fp127["n"], "fallback": fp127["fallback"], "inputs": fp127["inputs"]},
        "gas_before": mod.GAS_BEFORE_TEST,
        "gas_with_test": median,
        "gas_form": g["formLabels"][mod.GAS_FORM],
        "pct": pct,
        "gas_line": gas_line,
        "pct_line": f"+{pct}%",
        "counters": counters,
        "close_line": f"the last stage: {counters['fp127']} inputs",
    }


def expect_s12_reference(mod) -> dict:
    # the address straight from the file, not through the loader
    rel = vocab._load("contracts/deployments/RELEASE.json")
    comp = rel["components"][mod.COMPONENT]
    address, version = comp["address"], comp["version"]
    assert len(address) == 42 and address[:2] == "0x" and int(address[2:], 16) > 0, address
    assert version.startswith(mod.COMPONENT + " v"), version  # the version names the component (V15)
    # the record's markdown names the same address (V15, contracts/deployments/FP127.md)
    assert address in (vocab.ROOT / comp["record"]).read_text(encoding="utf-8"), (address, comp["record"])
    # the word by the other route: the probe's own 24-decimal truth, rounded half-up at the 18th by integer arithmetic
    truth = vocab.probe(mod.OP, mod.ARG)["truth"]
    ti, _, tf = truth.partition(".")
    q = 10 ** (len(tf) - mod.WORD_DECIMALS)
    scaled = (int(ti + tf) * 2 + q) // (2 * q)
    word = f"{scaled // 10**mod.WORD_DECIMALS}.{scaled % 10**mod.WORD_DECIMALS:0{mod.WORD_DECIMALS}d}"
    assert word == vocab.correctly_rounded_18(truth) and len(word.partition(".")[2]) == mod.WORD_DECIMALS, word
    # the chains straight from the file (V3, V5, V6)
    d = vocab._load("talk/scenes/data/chains.json")
    rows = []
    for r in d["chains"]:
        assert r["status"] in ("supported", "unsupported"), r
        assert r["probed"] == d["probed"], (r["chain"], r["probed"], d["probed"])
        if r["status"] == "unsupported":
            status = "no CLZ"
        elif r["deployed"]:
            status = "deployed"
        elif r["proxy"]:
            status = "has CLZ · proxy present · not yet deployed"
        else:
            status = "has CLZ · not yet deployed"
        rows.append(
            {
                "chain": r["chain"],
                "clz_since": r["clz_since"],
                "clz_text": f"CLZ since {r['clz_since']}" if r["clz_since"] else None,
                "status": r["status"],
                "deployed": bool(r["deployed"]),
                "proxy": r["proxy"],
                "status_text": status,
                "probed": r["probed"],
            }
        )
    # no row says "ready" or "live"; "deployed" is Sepolia's alone (V6, the brief's flags)
    for r in rows:
        low = r["status_text"].lower()
        assert "ready" not in low and "live" not in low, r
    deployed = [r["chain"] for r in rows if r["deployed"]]
    assert deployed == ["Sepolia"] and rel["network"] == "sepolia", (deployed, rel["network"])
    assert [r["status_text"] for r in rows if r["deployed"]] == ["deployed"]
    # an unsupported chain never carries a CLZ date; a supported one never reads "no CLZ"
    assert all(r["clz_since"] is None for r in rows if r["status"] == "unsupported")
    assert all(r["status_text"] != "no CLZ" for r in rows if r["status"] == "supported")
    # the probe is the 2026-10-29 one and the proxy was found everywhere (verify-K.md "2026-10-29 chain probe")
    assert d["probed"] == "2026-10-29" and all(r["proxy"] is True for r in rows), d["probed"]
    assert any(r["status"] == "unsupported" for r in rows) and len(rows) == 15, len(rows)
    for s in (mod.CLOSE, mod.STATUS_SUPPORTED, mod.STATUS_DEPLOYED, mod.STATUS_UNSUPPORTED):
        assert "ready" not in s.lower() and "live" not in s.lower(), s
    assert mod.CLOSE == "one call to check · deployed today: Sepolia"  # script §12, verbatim
    return {
        "address": address,
        "version": version,
        "release": rel["release"],
        "network": rel["network"],
        "rows": rows,
        "probed": d["probed"],
        "probed_caption": f"probed {d['probed']}",
        "arg": mod.ARG,
        "call": f"eth_call {mod.OP}({mod.ARG})",
        "truth_probe": truth,
        "word": word,
        "word_decimals": mod.WORD_DECIMALS,
    }
def expect_s03_under(mod) -> dict:
    """No JSON: every string is a LITERAL. The second route is the brief's
    table (talk/briefs/s03_under.md §3): the labels, the formulas with
    their markup stripped, the hero, the closing line (one line in the
    script, two on the slide), and its flags: "every" in the title only."""
    labels = [label for label, _ in mod.ROWS]
    assert labels == ["compounding rate", "discount factor", "option price", "growth curve"], labels
    formulas = [[TAG.sub("", stage) for stage in stages] for _, stages in mod.ROWS]
    assert formulas == [["(1 + r/n)nt", "ent · ln(1 + r/n)"], ["e−rt"], ["N(d)", "erfc", "e−x2"], ["ekt"]], formulas
    assert TAG.sub("", mod.HERO) == "ex" and mod.TITLE == "exp is under everything"
    assert mod.CLOSE.replace("\n", " ") == "if exp has no canonical value on chain, nothing built on it has one"
    lits = mod.LITERALS
    assert set(lits) == {mod.TITLE, *labels, *(stage for _, stages in mod.ROWS for stage in stages), mod.HERO, mod.CLOSE}, sorted(lits)
    assert all(v in ("V11", "V10, V11") for v in lits.values()) and lits[mod.CLOSE] == "V10, V11", lits
    assert [k for k in lits if "every" in k.lower()] == [mod.TITLE]  # the rows are examples, not a claim of completeness
    # Instrument Sans has no ² or →: the square is a <sup>, the arrows are drawn; nothing the font lacks is set
    assert not any(ch in k for k in lits for ch in "²→½√…"), sorted(lits)
    # the only digits drawn: the 1 of (1 + r/n) and the 2 of x²
    toks = set()
    for k in lits:
        toks |= number_tokens(k)
    assert toks == {"1", "2"}, toks
    assert all(stage.startswith("e<sup>") for _, stages in mod.ROWS for stage in stages[-1:]), "every row ends in a power of e"
    return {}
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


def expect_s15_formats(mod) -> dict:
    lib = vocab.libs()
    # the fields by the other route: the word and the registry's layouts, summed
    sign, integer, fraction = 1, 127, 128
    exponent, stored = 19, 236
    assert sign + integer + fraction == 256 == sign + exponent + stored
    assert integer == mod.FP127_INTEGER_BITS and fraction == vocab.FP127_FRACTION_BITS and exponent == vocab.FP19_EXPONENT_BITS and stored == vocab.FP19_FRACTION_BITS
    significand = stored + 1
    with localcontext() as ctx:
        ctx.prec = 80
        log10_2 = Decimal(2).log10()
        d127 = int((log10_2 * fraction).to_integral_value(rounding=ROUND_FLOOR))
        d19 = int((log10_2 * significand).to_integral_value(rounding=ROUND_FLOOR))
        assert d127 == 38 and d19 == 71, (d127, d19)  # K1 (38.53), K3 (71.34)
        # FP127's range: 2^127 as a Decimal, its leading power of ten and its mantissa to one decimal
        top = Decimal(2) ** 127
        range_exp = top.adjusted()
        mantissa = str(top.scaleb(-range_exp).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        assert range_exp == 38 and mantissa == "1.7", (range_exp, mantissa)  # K1: ±1.7014 × 10^38
        # the grid's end, 2^-128, is a positive Decimal with 128 binary places; its power of ten is -39 (K2), not drawn
        assert (Decimal(2) ** -128).adjusted() == -39
        # FP19's extremes (K3): 2^-262142 and (2 - 2^-236) · 2^262144, as powers of ten
        smallest = Decimal(2) ** -262142
        largest = (2 - Decimal(2) ** -stored) * Decimal(2) ** 262144
        min_exp, max_exp = smallest.adjusted(), largest.adjusted()
        assert min_exp == -78913 and max_exp == 78913, (min_exp, max_exp)
        # the ledger's mantissas, K3: 2.48 and 3.22
        assert str(smallest.scaleb(-min_exp).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) == "2.48"
        assert str(largest.scaleb(-max_exp).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) == "3.22"
    assert mod.FP19_MIN_EXP == -262142 and mod.FP19_MAX_EXP == 262144

    def power(e: int) -> str:
        return f"10<sup>{'−' if e < 0 else ''}{abs(e):,}</sup>"

    strings = {
        "bits": "256 bits",
        "fp127_fields": f"{sign} · {integer} · {fraction}",
        "fp127_names": "sign · integer · fraction",
        "fp127_digits": f"about {d127} digits of fraction",
        "fp127_range": f"about ±{mantissa} × {power(range_exp)}",
        "fp127_grid_end": f"the grid ends at 2<sup>−{fraction}</sup>",
        "fp127_label": f"{lib['fp127']['label']} · fixed point",
        "fp19_fields": f"{sign} · {exponent} · {stored}",
        "fp19_names": f"sign · exponent · fraction ({stored} stored)",
        "fp19_significand": f"significand {significand} bits with the hidden bit",
        "fp19_digits": f"about {d19} digits at every magnitude",
        "fp19_min": f"about {power(min_exp)}",
        "fp19_max": f"about {power(max_exp)}",
        "fp19_label": f"{lib['fp19']['label']} · floating point",
    }
    # the flags: "236 stored" and the 237-bit significand both on screen; never "237 stored" or "236-bit significand"
    joined = " | ".join(strings.values())
    assert "236 stored" in joined and "significand 237 bits" in joined and "237 stored" not in joined and "236-bit" not in joined, joined
    # every digit count and range is prefixed "about"; the minus is U+2212; the slide says "laid out as", not "is"
    for k in ("fp127_digits", "fp127_range", "fp19_digits", "fp19_min", "fp19_max"):
        assert strings[k].startswith("about "), strings[k]
    assert "-" not in strings["fp19_min"] and "−" in strings["fp19_min"] and "−" in strings["fp127_grid_end"]
    assert mod.IEEE == "laid out as IEEE 754 binary256" and mod.LITERALS[mod.IEEE] == "E9" and " is " not in mod.IEEE
    assert mod.CLOSE == "known range: fixed point · many orders of magnitude: floating point"  # essay §8, verbatim
    assert mod.REVERT == "no NaN, no infinity: overflow reverts"  # K4
    return {
        "word_bits": 256,
        "radix": 2,
        "base": 10,
        "fp127": {"label": lib["fp127"]["label"], "sign": sign, "integer": integer, "fraction": fraction, "digits": d127, "range_mantissa": mantissa, "range_exp": range_exp, "grid_end_exp": fraction},
        "fp19": {"label": lib["fp19"]["label"], "sign": sign, "exponent": exponent, "fraction": stored, "significand": significand, "digits": d19, "min_exp": min_exp, "max_exp": max_exp},
        "strings": strings,
    }


def expect_s17_proofs(mod) -> dict:
    """The counts straight from proofs.json by op, the sums from sweep.json by
    a loop over every row with running totals, the transcendental list from
    the FP127 README's own sentence (V34) and from the sweep's forced pass."""
    pj = vocab._load("docs/benchmarks/proofs.json")
    lib = vocab.libs()
    counts = {}
    for o in pj["ops"]:
        c = counts.setdefault(o["lib"], {"ops": 0, "proven": [], "fuzzed": [], "halmos": 0, "exact": []})
        c["ops"] += 1
        assert o["status"] in ("proven", "fuzzed"), o  # nothing in progress, no counterexample open (V22, V23)
        c[o["status"]].append(o["op"])
        if o["status"] == "proven":
            if "Halmos" in o["tool"]:
                c["halmos"] += 1
            else:
                c["exact"].append(o["op"])
    assert set(counts) == {"FP127", "FP19"}
    # the summary agrees with the rows, and the story: 17 = 16 + sqrt; 18 of 24; gavg, hypot; six (V22, V23)
    assert sum(c["ops"] for c in counts.values()) == pj["summary"]["ops"] == 43
    assert sum(len(c["proven"]) for c in counts.values()) == pj["summary"]["proven"] == 35
    assert sum(len(c["fuzzed"]) for c in counts.values()) == pj["summary"]["fuzzed"] == 8
    assert pj["summary"]["counterexamples"] == 0 and pj["summary"]["in_progress"] == 0
    f127, f19 = counts["FP127"], counts["FP19"]
    assert len(f127["proven"]) == 17 and f127["halmos"] == 16 and f127["exact"] == ["sqrt"] and f127["fuzzed"] == ["gavg", "hypot"]
    assert len(f19["proven"]) == 18 and f19["ops"] == 24 and len(f19["fuzzed"]) == 6 and f19["halmos"] == 18 and f19["exact"] == []
    assert set(f19["fuzzed"]) == {"add", "sub", "sqrt", "toFixed18", "toFixed18Down", "toFixed18Up"}, f19["fuzzed"]
    # the fuzz runs: every testFuzz_ entry ran 50,000 times and passed; the two regression pins once
    fuzz = {f["test"]: f for f in pj["fuzz"]}
    for op in f127["fuzzed"]:
        assert fuzz[f"testFuzz_fp127_{op}"]["runs"] == 50000 and fuzz[f"testFuzz_fp127_{op}"]["result"] == "pass", op
    for t in ("testFuzz_fp19_add", "testFuzz_fp19_sub", "testFuzz_fp19_sqrt", "testFuzz_fp19_toFixed18"):
        assert fuzz[t]["runs"] == 50000 and fuzz[t]["result"] == "pass", t
    assert all(f["runs"] == 50000 for t, f in fuzz.items() if t.startswith("testFuzz_")) and all(f["result"] == "pass" for f in fuzz.values())
    assert mod.NUMBER_WORDS[len(f19["fuzzed"])] == "six"
    # the transcendentals by two routes: the README's sentence, and the sweep's forced pass plus cbrt (V34: 20 + cbrt)
    readme = (vocab.ROOT / "contracts/src/fp127/README.md").read_text(encoding="utf-8")
    sentence = readme.split("The transcendentals round to nearest under the tie rule above:", 1)[1].split(". ", 1)[0]
    from_readme = re.findall(r"`(\w+)`", sentence)
    assert from_readme == list(mod.TRANSCENDENTAL) and len(from_readme) == 21, from_readme
    sw = vocab._load("docs/benchmarks/sweep.json")
    forced = {lid: sorted({r["op"] for r in sw["rows"] if r["lib"] == lid and r.get("stage") == "second"}) for lid in mod.LIBS}
    assert forced["fp19"] == forced["fp127"] and len(forced["fp19"]) == 20 and sorted(set(mod.TRANSCENDENTAL) - set(forced["fp19"])) == ["cbrt"], forced
    # the sums by a running loop; every row of both libraries counted once, every fp19/fp127 row correctly rounded in full
    total, mis, trans, nrows, seen = {}, {}, {}, {}, set()
    for r in sw["rows"]:
        lid = r["lib"]
        if lid not in mod.LIBS:
            continue
        key = (lid, r["op"], r.get("stage"))
        assert key not in seen, key
        seen.add(key)
        # n is the results that returned; FP127 counts a revert where the oracle reverts as correct over its inputs (sweep.md)
        assert r["correctlyRounded"] + r["misrounded"] == r.get("inputs", r["n"]) and r["status"].get("ok", r["n"]) == r["n"], key
        nrows[lid] = nrows.get(lid, 0) + 1
        total[lid] = total.get(lid, 0) + r["n"]
        mis[lid] = mis.get(lid, 0) + r["misrounded"]
        if r["op"] in mod.TRANSCENDENTAL:
            trans[lid] = trans.get(lid, 0) + r["n"]
    assert mis == {"fp19": 0, "fp127": 0}, mis
    assert total == {"fp19": 455082, "fp127": 212119} and nrows == {"fp19": 76, "fp127": 59}, (total, nrows)  # V25
    assert trans == {"fp19": 327488, "fp127": 168120}, trans  # V34
    assert all(trans[lid] < total[lid] for lid in mod.LIBS)
    # the oracles' digits by the other route: sweep.md's header (V17)
    header = (vocab.ROOT / "docs/benchmarks/sweep.md").read_text(encoding="utf-8").split("\n## ", 1)[0]
    ref = {"fp19": int(re.search(r"oracle\.py, (\d+) digits", header).group(1)), "fp127": int(re.search(r"real truth at (\d+) digits", header).group(1))}
    assert ref == {"fp19": 300, "fp127": 200}, ref
    # the flags: the oracle row says tested, row 4 is never a bug list, the footnote's bugs are history
    assert mod.LABELS[2].startswith("tested") and "proven" not in mod.LABELS[2] and mod.LABELS[3] == "known limits"
    assert "bug" not in " ".join(mod.LIMIT_BOUND + mod.LIMIT_STAGE).lower() and "fixed, now proven" in mod.FOOTNOTE
    assert "0.79" in mod.LIMIT_BOUND[1] and "0.78" not in mod.LIMIT_BOUND[1] and "0.92" in mod.LIMIT_BOUND[1]  # V38: the ledger's figure
    assert mod.CLOSING == "State your own guarantees this specifically."
    assert not any(ch in s for s in (*mod.LIMIT_BOUND, *mod.LIMIT_STAGE, mod.FOOTNOTE, mod.CLOSING) for ch in "²→½√…")
    return {
        "labels": {"fp19": lib["fp19"]["label"], "fp127": lib["fp127"]["label"]},
        "proven": {"FP127": f127["proven"], "FP19": f19["proven"]},
        "fuzzed": {"FP127": f127["fuzzed"], "FP19": f19["fuzzed"]},
        "ops": {"FP127": f127["ops"], "FP19": f19["ops"]},
        "proven_count": {"FP127": len(f127["proven"]), "FP19": len(f19["proven"])},
        "halmos_count": f127["halmos"],
        "exact_integer": f127["exact"],
        "fp19_fuzzed_word": "six",
        "runs": 50000,
        "rows": nrows,
        "total": total,
        "misrounded": mis,
        "transcendental": trans,
        "reference_digits": ref,
    }


def _text_only(mod, strings: set[str], ids: set[str] | None = None) -> None:
    """A text slide's second route: the strings the brief gives, verbatim,
    are exactly the module's LITERALS; none carries the glyphs the font
    lacks; no claim id is empty."""
    assert set(mod.LITERALS) == strings, (sorted(set(mod.LITERALS) ^ strings))
    assert all(v for v in mod.LITERALS.values()), mod.LITERALS
    if ids is not None:
        assert set(mod.LITERALS.values()) <= ids, set(mod.LITERALS.values()) - ids
    assert not any(ch in k for k in mod.LITERALS for ch in "²→½√…"), sorted(mod.LITERALS)


def expect_s01_title(mod) -> dict:
    """No JSON; the title is the user's, the speaker line a placeholder
    (REPORT), the only loop in the deck (slides.yaml says so)."""
    _text_only(mod, {"THE END OF ROUNDING ERRORS", "blockulator.com", "[speaker]"})
    assert mod.LITERALS["[speaker]"] == "REPORT" and mod.SPEAKER == "[speaker]"
    assert mod.Title.SECTIONS == ("title",) and mod.Title.LOOP is True
    deck = (vocab.ROOT / "talk/deck/slides.yaml").read_text(encoding="utf-8")
    assert deck.count("loop: true") == 1 and "scene: s01_title.Title\n  loop: true" in deck, "the title is the only looping scene"
    assert not any(ch.isdigit() for ch in "".join(mod.LITERALS))
    return {}


def expect_s11_budget(mod) -> dict:
    """No JSON: the essay's list (essay-v7 §5) and the script's fifth line (§11); "every" in the fifth line only; no digits."""
    bullets = ("long horizons", "cancellation", "extreme ranges and tails", "iteration")
    assert mod.BULLETS == bullets
    fifth = mod.DIRECTION.replace("\n", " ")
    assert fifth == "and decide the direction of every rounding at a unit", fifth
    _text_only(mod, {"Precision is a budget", "spend precision where it pays:", *bullets, mod.DIRECTION})
    assert [k for k in mod.LITERALS if "every" in k] == [mod.DIRECTION]
    assert not any(ch.isdigit() for ch in "".join(mod.LITERALS))
    assert set(vocab.ROW_COLOUR["s11"]) == {*bullets, "direction"} and len(set(vocab.ROW_COLOUR["s11"].values())) == 5, "four hues for four bullets, EMERALD for the direction"
    assert vocab.ROW_COLOUR["s11"]["direction"] == vocab.Palette.EMERALD
    return {}


def expect_s13_not_switch(mod) -> dict:
    """No JSON: the script's two lines (§13), straight quotes, nothing else; the struck words are inside the first."""
    _text_only(mod, {'Not "switch libraries".', "Measure yourself against the reference."})
    assert mod.STRUCK == "switch libraries" and mod.NOT.count(mod.STRUCK) == 1
    assert not any(ch in k for k in mod.LITERALS for ch in "“”‘’")
    assert not any(ch.isdigit() for ch in "".join(mod.LITERALS))
    assert mod.NotSwitch.SECTIONS == ("not", "measure")
    return {}


def expect_s14_institutions(mod) -> dict:
    """No JSON: the essay's words (§7) and the ERC-4626 line (V1); the chart carries no number; the words in a row."""
    words_ = ("reproducible", "declared", "checked")
    assert mod.WORDS == words_
    _text_only(mod, {"What institutions buy", "amount", "fees · scale with the computation", "errors · scale with the amount", "not fewer cents", *words_, "ERC-4626 fixes the rounding direction of each vault conversion"})
    assert mod.LITERALS["ERC-4626 fixes the rounding direction of each vault conversion"] == "V1"
    toks = set()
    for k in mod.LITERALS:
        toks |= number_tokens(k)
    assert toks == {"4626"}, toks  # the standard's number is the only digit on the slide
    assert all("$" not in k and "digit" not in k for k in mod.LITERALS)  # the "15 digits on $10 million" line stays in the essay
    assert vocab.ROW_COLOUR["s14"]["errors"] == vocab.Palette.RED and vocab.ROW_COLOUR["s14"]["words"] == vocab.Palette.EMERALD
    return {}


def expect_s18_habits(mod) -> dict:
    """The address straight from RELEASE.json; the op names in the example block are FP127Lib's own (found in the source);
    the three habits in three hues, the ticks EMERALD."""
    rel = vocab._load("contracts/deployments/RELEASE.json")
    comp = rel["components"]["FP127"]
    address, version = comp["address"], comp["version"]
    assert len(address) == 42 and address[:2] == "0x" and int(address[2:], 16) > 0, address
    assert version.startswith("FP127 v"), version
    assert address in (vocab.ROOT / comp["record"]).read_text(encoding="utf-8"), (address, comp["record"])
    src = (vocab.ROOT / "contracts/src/fp127/FP127Lib.sol").read_text(encoding="utf-8")
    ops = [op for op, _ in mod.OPS]
    for op in ops:
        assert re.search(rf"function {re.escape(op)}\(", src), f"{op} is not an FP127Lib function"
    assert [way for _, way in mod.OPS] == ["down", "up", "nearest"]
    assert mod.ROUNDING == "rounding: " + " · ".join(f"{op} {way}" for op, way in mod.OPS)
    habits = [h for h, _ in mod.HABITS]
    assert habits == ["Decide", "Measure", "Declare"]
    assert mod.TITLE == "Rounding is a design decision, like access control."
    assert mod.EXAMPLE == "example" and mod.REFERENCE == "reference:"
    assert not any("today" in line or "protocol" in line for _, line in mod.HABITS)  # nothing says a protocol does this today
    hues = vocab.ROW_COLOUR["s18"]
    assert len({hues[h] for h in habits}) == 3 and hues["tick"] == vocab.Palette.EMERALD
    assert not any(ch in k for k in mod.LITERALS for ch in "²→½√…")
    return {"address": address, "version": version, "ops": ops, "rounding": mod.ROUNDING}


def _readme_install() -> str:
    """README.md's Install section (the lines the commands are copied from), backticks dropped."""
    text = (vocab.ROOT / "README.md").read_text(encoding="utf-8")
    start = text.index("## Install")
    end = text.index("## ", start + 3)
    return text[start:end].replace("`", "")


def _repo_from_git() -> str:
    """The origin remote by the other route: parsed from .git's config text, not `git remote`."""
    import configparser

    git = vocab.ROOT / ".git"
    if git.is_file():  # a worktree: "gitdir: <path>/.git/worktrees/<name>"
        gitdir = Path(git.read_text(encoding="utf-8").split("gitdir:", 1)[1].strip())
        cfg = gitdir.parent.parent / "config"
    else:
        cfg = git / "config"
    parser = configparser.ConfigParser()
    parser.read(cfg, encoding="utf-8")
    url = parser['remote "origin"']["url"].strip()
    m = re.match(r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+)/([^/]+?)(?:\.git)?$", url)
    assert m, f"REPORT: origin is not a GitHub remote: {url}"
    return f"https://github.com/{m.group(1)}/{m.group(2)}"


def _qr_round_trip(mod, scene_numbers: dict) -> None:
    """Regenerate each tile's matrix from its URL and compare with what the scene drew (the tiles' .matrix)."""
    scene = dry_run(mod)
    tiles = [m for m in scene.mobjects if hasattr(m, "matrix") and hasattr(m, "url")]
    assert len(tiles) == 2, len(tiles)
    by_url = {t.url: t for t in tiles}
    assert set(by_url) == {scene_numbers["site_url"], scene_numbers["repo_url"]}, set(by_url)
    for url, tile in by_url.items():
        assert tile.matrix == vocab.qr_matrix(url), url
        dark = sum(1 for row in tile.matrix for c in row if c)
        assert len(tile.modules) == dark, (url, len(tile.modules), dark)
        drawn_label = "".join(t.text for t in tile.label).replace("\n", "")
        assert drawn_label == url.split("://", 1)[1].replace("\n", ""), (drawn_label, url)


def expect_s19_address(mod) -> dict:
    rel = vocab._load("contracts/deployments/RELEASE.json")
    comps = rel["components"]
    assert rel["network"] == "sepolia"
    out = {"network": rel["network"], "release": rel["release"], "main": {}, "others": {}}
    names = ("FP19", "FP127", "FP127E", "FP127H", "FP127N", "FP127S", "FP19E", "FP19H", "FP19N", "FP19S")
    for name in names:
        c = comps[name]
        assert len(c["address"]) == 42 and c["address"][:2] == "0x" and int(c["address"][2:], 16) > 0, c
        assert c["version"].startswith(name + " v"), c["version"]
        assert c["address"] in (vocab.ROOT / c["record"]).read_text(encoding="utf-8"), (name, c["record"])
        (out["main"] if name in ("FP19", "FP127") else out["others"])[name] = {"version": c["version"], "address": c["address"]}
    assert len({c["address"] for c in comps.values()}) == len(comps), "every object has its own address"
    assert not any(name.lower().startswith("ladder") for name in names)  # the ladder objects are not shown
    # the commands, verbatim from README.md's Install section (K12)
    readme = _readme_install()
    for cmd in (mod.FORGE, mod.NPM, mod.LLMS, mod.ETH_CALL):
        assert cmd in readme, cmd
    assert mod.LLMS == "blockulator.com/llms.txt" and "https://" + mod.LLMS in readme
    assert mod.TODAY == "today: Sepolia" and mod.CLOSE == "Measure yourself against it."
    assert "mainnet" not in " ".join(mod.LITERALS).lower()
    out["repo_url"] = _repo_from_git()
    out["site_url"] = "https://blockulator.com"
    out["repo_label"] = "github.com/\nsecuredataresearch/\nblockulator"
    assert out["repo_label"].replace("\n", "") == out["repo_url"].split("://", 1)[1]
    _qr_round_trip(mod, out)
    return out


def expect_s20_thanks(mod) -> dict:
    assert mod.THANKS == "Special thanks to Austin Griffith (Ethereum Foundation) and Hadrien Croubois (OpenZeppelin) for extremely helpful feedback."
    assert " ".join(mod.THANKS_LINES) == mod.THANKS and mod.THANK_YOU == "Thank you"
    assert set(mod.LITERALS) == {mod.THANK_YOU, *mod.THANKS_LINES, "blockulator.com", "agents:", "blockulator.com/llms.txt"}, sorted(mod.LITERALS)
    assert "blockulator.com/llms.txt" in _readme_install()
    out = {"site_url": "https://blockulator.com", "repo_url": _repo_from_git()}
    out["repo_label"] = out["repo_url"].split("://", 1)[1]
    _qr_round_trip(mod, out)
    return out


EXPECT = {
    "s01_title": expect_s01_title,
    "s11_budget": expect_s11_budget,
    "s13_not_switch": expect_s13_not_switch,
    "s14_institutions": expect_s14_institutions,
    "s18_habits": expect_s18_habits,
    "s19_address": expect_s19_address,
    "s20_thanks": expect_s20_thanks,
    "s02_exp40": expect_s02_exp40,
    "s03_under": expect_s03_under,
    "s04_grid": expect_s04_grid,
    "s05_cost": expect_s05_cost,
    "s06_resupply": expect_s06_resupply,
    "s06b_bunni": expect_s06b_bunni,
    "s06c_balancer_v2": expect_s06c_balancer_v2,
    "s06d_thetanuts": expect_s06d_thetanuts,
    "s07_two": expect_s07_two,
    "s08_ladder": expect_s08_ladder,
    "s09_cliff": expect_s09_cliff,
    "s10_live": expect_s10_live,
    "s16_ziv": expect_s16_ziv,
    "s12_reference": expect_s12_reference,
    "s15_formats": expect_s15_formats,
    "s17_proofs": expect_s17_proofs,
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

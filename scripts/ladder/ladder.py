#!/usr/bin/env python3
"""Build docs/benchmarks/ladder.json and ladder.md from the harness output.

    forge test --match-path "test/ladder/*" -vv | uv run scripts/ladder/ladder.py
    forge test --match-path "test/ladder/*" -vv | uv run scripts/ladder/ladder.py --check
    uv run scripts/ladder/ladder.py --selftest

Input lines (test/ladder/Ladder.t.sol):
    LADDER|<scenario>|<input>|<form>|<N>|<ok 0/1>|<raw int>|<reason bytes4>|<gasTotal>

Two truths per scenario, input and N, both the scenario's loop in exact real
arithmetic with mpmath at 200 digits:
    truth         from the exact rational parameters in scenarios.json
    truthFormat   per scale (2**128, 2**64, 10**18): the same loop started
                  from the parameters floored into that scale, which is what
                  the library actually received
Per cell, with v the decoded value, t the truth, tf the format truth:
    digits        floor(-log10(|v - t| / |t|)), capped at 60 (= exact); what
                  a protocol sees, format and arithmetic together
    digitsFormat  the same against tf: the arithmetic alone
    agree         leading significant digits of the value string that are
                  literally equal to the truth string (both 42 significant
                  digits); for highlighting only, never a precision claim
    errUlps       (v - t) in units of the form's last place, signed
    relErr        (v - t) / t, signed
No JSON floats: every measurement is a decimal string or an integer.
`--check` compares every measurement exactly and gas within max(2 %, 3 gas).
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

from mpmath import mp, mpf, log, exp, sqrt, ncdf, nstr, floor as mfloor_

mp.dps = 300
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "fp127"))
sys.path.insert(0, str(ROOT / "scripts" / "ladder"))
from gas_to_json import versions  # noqa: E402
from gen_inputs import resolve, to_scaled, from_scaled, SCALES as INPUT_SCALES  # noqa: E402

SPEC = ROOT / "scripts" / "ladder" / "scenarios.json"
OUT_JSON = ROOT / "docs" / "benchmarks" / "ladder.json"
OUT_MD = ROOT / "docs" / "benchmarks" / "ladder.md"
DIGITS_CAP = 100
CHART_CAP = 80   # summaries cap digits here so an exact WAD cell does not distort max
SIG = 42         # significant digits kept for value/truth strings
SCALE_OF_FORM = {"fp127": "fp127", "fp127lib": "fp127", "abdk": "abdk", "solady": "wad", "prb": "wad",
                 "quad": "quad", "balancer": "wad", "aave": "ray", "morpho": "wad", "maker": "ray", "fp256": "fp256"}
SCALE_INT = {k: v[1] for k, v in INPUT_SCALES.items()}
SCALE_NAME = {k: v[0] for k, v in INPUT_SCALES.items()}
REASONS = {
    "0x35278d12": "Overflow()", "0x23d359a3": "DivisionByZero()", "0x7db3aba7": "OutOfRange()",
    "0x00000000": "bare revert (require without a reason, or out of gas)",
    "0xedcd4dd4": "Solady ExpOverflow()", "0x120b5b43": "PRBMath_SD59x18_Mul_Overflow",
    "0x4e487b71": "Panic (checked arithmetic overflow or division by zero)",
    "0x49f7642b": "Solady RPowOverflow() (Maker's rpow)",
    "0x7964b44f": "ParamOutOfRange(uint256): the value does not fit the representation",
    "0x7bb9ae15": "Unsupported(uint8): the library has no model for this scenario",
    "0xa28f5c6b": "Quad NaN or infinity",
    "0x34d81929": "Balancer: negative base or exponent",
    "0x022701e0": "Balancer BaseOutOfBounds()", "0xd8317311": "Balancer ExponentOutOfBounds()",
    "0xa2f9f7e3": "Balancer ProductOutOfBounds()", "0xd4794efd": "Balancer InvalidExponent()", "0xb4120f14": "Balancer OutOfBounds()",
}
PARAM_OUT_OF_RANGE = "0x7964b44f"

METHODOLOGY = {
    "truth": "For every scenario, input and N the same loop is run in exact real arithmetic with mpmath at 300 decimal digits (scripts/ladder/ladder.py), from the exact rational parameters in scenarios.json. Closed forms are used where the loop has one (compounding, the cumulative product, the geometric mean, the round trip, per-second and continuous accrual, the option walk and the decay); the bonding curve, the amortising loan and the Black-Scholes chain are stepped.",
    "rounding": "Each library receives the parameters floored into its own representation (2^-128, 2^-64, 10^-18 or 10^-27 units, or the nearest float for ABDKMathQuad and FP256; scripts/ladder/inputs.json). truthFormat is the exact loop started from those floored parameters, so digitsFormat measures the library's arithmetic alone, while digits measures what a protocol sees: the format's rounding of the inputs plus the arithmetic.",
    "digits": "digits = floor(-log10 |v - t| / |t|), the number of correct leading significant digits by relative error, capped at 100, which is reported as exact. It is not a string comparison: a value can be correct to 36 digits while its 37th printed digit happens to agree with the truth, or while a carry makes the printed prefix differ earlier.",
    "agree": "agree is the count of leading significant digits of the printed value (42 significant digits) that are literally equal to the printed truth. The demo page colours the rest of the value with it. It is a reading aid, not a measurement: a carry across 0.999… / 1.000… gives 0.",
    "gas": "gasTotal is measured inside the adapter around the scenario function (the parameter reads and the loop), after the runner has warmed the adapter and the FP127 object, so the call into the adapter and the ABI decoding are excluded. The FP127 (deployed) form includes one staticcall per op; FP127Lib and the other libraries are internal calls. Aave, Morpho and Maker answer only the accrual scenarios their models describe and report Unsupported elsewhere, which the tables show as a revert. gasPerStep = gasTotal / N. Reverted cells carry no gas.",
    "live": "LadderRunner.run(scenario, form, n, p) on Sepolia executes any cell with one eth_call and returns (ok, raw, reason, gasPerStep, gasTotal). scripts/ladder/livecap.py sends every cell's floored parameters p and compares the returned raw word with the committed one bit for bit (or the revert selector for a reverted cell). liveMaxN is the largest N per form the public RPC completed within its gas limit, measured by scripts/ladder/livecap.py.",
    "reproduce": "make ladder regenerates ladder.json and ladder.md from the Foundry harness (test/ladder/Ladder.t.sol) and this script; make ladder-check fails CI when the committed dataset differs. Versions of every library and of forge are recorded in the dataset.",
}


# ---------------------------------------------------------------------------
# Truth: the scenario loops in exact real arithmetic, recorded at every ladder N
# ---------------------------------------------------------------------------

def truths(sid: str, p: dict, ns: list[int]) -> dict[int, mpf]:
    """{N: value} for every N in ns (sorted), stepping each loop once."""
    out = {}
    if sid in ("compound", "compound-annual", "compound-pow"):
        for n in ns:
            out[n] = p["principal"] * (1 + p["rate"]) ** n
    elif sid == "accrual-per-second":
        for n in ns:
            out[n] = p["principal"] * (1 + p["rateSec"]) ** (n * 86400)
    elif sid == "accrual-continuous":
        for n in ns:
            out[n] = p["principal"] * exp(p["rateAnnual"] * mpf(n) / 365)
    elif sid == "deep-tail-option":
        S0, K, sg, T, r, tick = p["spot"], p["strike"], p["sigma"], p["T"], p["r"], p["tick"]
        vs = sg * sqrt(T)
        for n in ns:
            S = S0 * (1 - tick) ** n
            d1 = (log(S / K) + (r + sg * sg / 2) * T) / vs
            d2 = d1 - vs
            out[n] = S * ncdf(d1) - K * exp(-r * T) * ncdf(d2)
    elif sid == "decay":
        for n in ns:
            out[n] = 1 - exp(-p["eps"] * n)
    elif sid == "roundtrip":
        for n in ns:
            out[n] = p["x0"]
    elif sid == "geo-mean":
        for n in ns:
            out[n] = (mpf(n + 2) / 2) ** (mpf(1) / n)
    elif sid == "cumulative-product":
        e = p["eps"]
        for n in ns:
            out[n] = (1 + e) ** ((n + 1) // 2) * (1 - e) ** (n // 2)
    elif sid == "bonding-sqrt":
        s, cost, k = p["supply"], mpf(0), 0
        for n in ns:
            while k < n:
                cost += sqrt(s)
                s += p["unit"]
                k += 1
            out[n] = cost
    elif sid == "amortise":
        b, g, pay, k = p["principal"], 1 + p["rate"], p["payment"], 0
        for n in ns:
            while k < n:
                b = b * g - pay
                k += 1
            out[n] = b
    elif sid == "black-scholes-chain":
        S, K, sig, T, r, tick = (p[k] for k in ("spot", "strike", "sigma", "T", "r", "tick"))
        drift = (r + sig * sig / 2) * T
        denom = sig * sqrt(T)
        acc, k = mpf(0), 0
        for n in ns:
            while k < n:
                acc += (log(S / K) + drift) / denom
                S += tick
                k += 1
            out[n] = acc
    else:
        raise KeyError(sid)
    return out


def floored_params(p: dict, scale) -> dict:
    """The parameters as the library received them: floor(x * scale) / scale, exact
    (the nearest binary128 value for the quad scale)."""
    return {k: from_scaled(to_scaled(v, scale), scale) for k, v in p.items()}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def sig_digits(s: str) -> str:
    """The significant digits of a decimal string: sign, leading zeros and the point removed."""
    s = s.lstrip("-").lstrip("0").lstrip(".").lstrip("0") if not s.lstrip("-").startswith("0.") else s.lstrip("-")[2:].lstrip("0")
    return s.replace(".", "")


def agree_count(value: str, truth: str) -> int:
    a, b = sig_digits(value), sig_digits(truth)
    # the mantissas must also start at the same decade: compare integer-part lengths
    def intlen(x: str) -> int:
        x = x.lstrip("-")
        return len(x.split(".")[0].lstrip("0")) if not x.startswith("0.") else -(len(x[2:]) - len(x[2:].lstrip("0")))
    if intlen(value) != intlen(truth) or (value.startswith("-") != truth.startswith("-")):
        return 0
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return min(n, SIG)


def digits_of(v, t) -> int:
    if v == t:
        return DIGITS_CAP
    if t == 0:
        return 0
    rel = abs(v - t) / abs(t)
    if rel == 0:
        return DIGITS_CAP
    return min(DIGITS_CAP, max(0, int(mfloor_(-log(rel, 10)))))


def signed(x) -> str:
    return nstr(x, 6) if x != 0 else "0"


def metrics(raw: int, scale, t, tf) -> dict:
    v = from_scaled(raw, scale)
    value = nstr(v, SIG)
    truth_s = nstr(t, SIG)
    d = digits_of(v, t)
    return {
        "value": value,
        "digits": d,
        "digitsFormat": digits_of(v, tf),
        "exact": d >= DIGITS_CAP,
        "agree": agree_count(value, truth_s),
        "errUlps": signed((v - t) * scale) if scale and scale != "fp256" else None,
        "relErr": signed((v - t) / t) if t != 0 else None,
    }


def parse_lines(stream) -> dict:
    """cells[scenario][input][form][N] = {ok, raw, reason, gas}"""
    cells: dict = {}
    for line in stream:
        if "LADDER|" not in line:
            continue
        parts = line[line.index("LADDER|"):].strip().split("|")
        if len(parts) != 9:
            continue
        _, scn, inp, form, n, ok, raw, reason, gas = parts
        cells.setdefault(scn, {}).setdefault(inp, {}).setdefault(form, {})[int(n)] = {
            "ok": ok == "1", "raw": int(raw), "reason": reason[:10], "gas": int(gas),
        }
    return cells


def median(xs: list[int]):
    xs = sorted(xs)
    m = len(xs) // 2
    if len(xs) % 2:
        return xs[m]
    s = xs[m - 1] + xs[m]
    return s // 2 if s % 2 == 0 else s / 2


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(cells: dict) -> dict:
    spec = json.loads(SPEC.read_text())
    forms = [f["id"] for f in spec["forms"]]
    ns = spec["ladder"]
    out_scn = []
    for scn in spec["scenarios"]:
        sid = scn["id"]
        if sid not in cells:
            continue
        inputs_out = []
        per_form_digits = {f: {n: {"d": [], "df": [], "rev": 0, "unrep": 0} for n in ns} for f in forms}
        for inp in scn["inputs"]:
            if inp["name"] not in cells[sid]:
                continue
            p = resolve(inp["params"], scn.get("derived", {}))
            t_exact = truths(sid, p, ns)
            t_format = {sc: truths(sid, floored_params(p, SCALE_INT[sc]), ns) for sc in SCALE_INT}
            cells_out = {}
            for form in forms:
                sc = SCALE_OF_FORM[form]
                col = {}
                for n in ns:
                    c = cells[sid][inp["name"]].get(form, {}).get(n)
                    if c is None:
                        continue
                    acc = per_form_digits[form][n]
                    if not c["ok"]:
                        col[str(n)] = {"reverted": True, "reason": c["reason"], "reasonName": REASONS.get(c["reason"], "unknown selector"), "gas": None}
                        if c["reason"] == PARAM_OUT_OF_RANGE:
                            acc["unrep"] += 1
                        else:
                            acc["rev"] += 1
                        continue
                    m = metrics(c["raw"], SCALE_INT[sc], t_exact[n], t_format[sc][n])
                    m["raw"] = str(c["raw"])
                    m["gas"] = c["gas"]
                    m["gasPerStep"] = c["gas"] // n
                    col[str(n)] = m
                    acc["d"].append(min(m["digits"], CHART_CAP))
                    acc["df"].append(min(m["digitsFormat"], CHART_CAP))
                cells_out[form] = col
            inputs_out.append({
                "name": inp["name"], "reference": bool(inp.get("reference")), "why": inp.get("why", ""),
                "params": inp["params"],
                "resolved": {k: nstr(v, SIG) for k, v in p.items()},
                "truth": {str(n): nstr(t_exact[n], SIG) for n in ns},
                "truthFormat": {SCALE_NAME[sc]: {str(n): nstr(t_format[sc][n], SIG) for n in ns} for sc in SCALE_INT},
                "cells": cells_out,
            })
        summary = {}
        for form in forms:
            summary[form] = {}
            for n in ns:
                acc = per_form_digits[form][n]
                row = {"count": len(acc["d"]), "reverts": acc["rev"], "unrepresentable": acc["unrep"]}
                if acc["d"]:
                    row["digits"] = {"min": min(acc["d"]), "median": median(acc["d"]), "max": max(acc["d"])}
                    row["digitsFormat"] = {"min": min(acc["df"]), "median": median(acc["df"]), "max": max(acc["df"])}
                summary[form][str(n)] = row
        out_scn.append({
            "id": sid, "index": scn["index"], "demo": scn["demo"], "title": scn["title"], "step": scn["step"],
            "result": scn["result"], "why": scn["why"], "order": scn["order"], "derived": scn.get("derived", {}),
            "ops": scn["ops"], "inputs": inputs_out, "summary": summary,
        })
    return {
        "generated": datetime.date.today().isoformat(),
        "description": "Terminal precision: each scenario is N identical steps run through each library in its native representation for several inputs, against the same loop in exact arithmetic (mpmath, 200 digits), twice: from the exact parameters (digits) and from the parameters as the library received them (digitsFormat). See methodology.",
        "versions": versions(),
        "ladder": ns,
        "ladderLog10": {str(n): nstr(log(mpf(n), 10), 6) for n in ns},
        "forms": spec["forms"],
        "digitsCap": DIGITS_CAP,
        "chartCap": CHART_CAP,
        "methodology": METHODOLOGY,
        "scenarios": out_scn,
    }


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def short(s: str) -> str:
    return nstr(mpf(s), 16)


def fmt_summary(row: dict, key: str) -> str:
    if key not in row:
        return "—" + (f" ({row['reverts']} revert)" if row["reverts"] else "")
    d = row[key]
    s = f"{d['median']} ({d['min']}–{d['max']})"
    if row["reverts"]:
        s += f", {row['reverts']} revert"
    return s


def render_md(doc: dict) -> str:
    forms = [f["id"] for f in doc["forms"]]
    L = ["# Terminal precision ladder", "",
         f"Generated {doc['generated']} by `make ladder`. Versions: " + ", ".join(f"{k} {v}" for k, v in doc["versions"].items()) + ".", "",
         "Each scenario is run for several inputs; the first table is the reference input in full (`digits / digitsFormat / gas per step`, where digits is against the exact truth and digitsFormat against the truth from the parameters as the library received them), the second is the summary over all inputs (`median (min–max)` digits, capped at 40). Full values, both truths, signed errors and raw words are in ladder.json; the method is in the Methodology section at the end.", ""]
    for s in doc["scenarios"]:
        L += [f"## {s['id']}: {s['title']}", "", f"Step: `{s['step']}`. Result: {s['result']}.", "", s["why"], ""]
        L += ["Inputs: " + "; ".join(f"**{i['name']}** " + ", ".join(f"{k} = {v}" for k, v in i["params"].items()) + (f" ({i['why']})" if i["why"] else "") for i in s["inputs"]), ""]
        ref = next((i for i in s["inputs"] if i["reference"]), s["inputs"][0])
        L += [f"### Reference input: {ref['name']}", "",
              "| N | truth | " + " | ".join(forms) + " |", "|---:|---|" + "---:|" * len(forms)]
        for n, t in ref["truth"].items():
            cells = []
            for f in forms:
                c = ref["cells"].get(f, {}).get(n)
                if c is None:
                    cells.append("—")
                elif c.get("reverted"):
                    cells.append(f"reverts `{c['reason']}`")
                else:
                    cells.append(("exact" if c["exact"] else str(c["digits"])) + f" / {c['digitsFormat'] if c['digitsFormat'] < DIGITS_CAP else 'exact'} / {c['gasPerStep']:,}")
            L.append(f"| {n} | `{short(t)}` | " + " | ".join(cells) + " |")
        L += ["", f"### All inputs ({len(s['inputs'])}): digits, median (min–max)", "",
              "| N | " + " | ".join(forms) + " |", "|---:|" + "---:|" * len(forms)]
        for n in doc["ladder"]:
            L.append(f"| {n} | " + " | ".join(fmt_summary(s["summary"][f][str(n)], "digits") for f in forms) + " |")
        L += ["", f"### All inputs: digitsFormat (arithmetic alone), median (min–max)", "",
              "| N | " + " | ".join(forms) + " |", "|---:|" + "---:|" * len(forms)]
        for n in doc["ladder"]:
            L.append(f"| {n} | " + " | ".join(fmt_summary(s["summary"][f][str(n)], "digitsFormat") for f in forms) + " |")
        L.append("")
    L += ["## Methodology", ""]
    for k, v in doc["methodology"].items():
        L += [f"**{k}.** {v}", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Check
# ---------------------------------------------------------------------------

def strip_volatile(doc: dict) -> dict:
    d = json.loads(json.dumps(doc))
    for s in d.get("scenarios", []):
        s.pop("liveMaxN", None)
    return {k: d.get(k) for k in ("ladder", "forms", "digitsCap", "chartCap", "scenarios")}


def first_difference(a, b, path="") -> str:
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                return f"{path}/{k}: only in {'committed' if k in a else 'regenerated'}"
            r = first_difference(a[k], b[k], f"{path}/{k}")
            if r:
                return r
        return ""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            r = first_difference(x, y, f"{path}[{i}]")
            if r:
                return r
        return ""
    if path.endswith("/gas") or path.endswith("/gasPerStep"):
        if a is None or b is None:
            return "" if a == b else f"{path}: committed {a!r} != regenerated {b!r}"
        if abs(a - b) <= max(3, 0.02 * max(a, b)):
            return ""
    if a != b:
        return f"{path}: committed {a!r} != regenerated {b!r}"
    return ""


# ---------------------------------------------------------------------------
# Self-test of the metric definitions
# ---------------------------------------------------------------------------

def selftest() -> int:
    cases = [
        ("10002.7397260273972602739726027397260273831", "10002.7397260273972602739726027397260273973", 39),
        ("-0.00123456", "-0.00123999", 3),
        ("0.99999999", "1.00000001", 0),
        ("1.5", "1.5", 2),
        ("154769.3406914411", "154769.3406914411", 16),
        ("123", "1230", 0),
        ("0.5", "-0.5", 0),
    ]
    bad = 0
    for v, t, want in cases:
        got = agree_count(v, t)
        if got != want:
            bad += 1
            print(f"agree({v}, {t}) = {got}, want {want}")
    d = digits_of(mpf("10002.7397260273972602739726027397260273831"), mpf("10002.7397260273972602739726027397260273973"))
    if d != 38:
        bad += 1
        print(f"digits = {d}, want 38")
    if digits_of(mpf("1.5"), mpf("1.5")) != DIGITS_CAP or digits_of(mpf(0), mpf(0)) != DIGITS_CAP or digits_of(mpf(1), mpf(0)) != 0:
        bad += 1
        print("digits edge cases")
    m = metrics(3 * 2 ** 127 - 8, 2 ** 128, mpf("1.5"), mpf("1.5"))
    # 1.5 - 8 ULP prints as 1.4999…: the string prefix agrees on one digit while the value is good to 37
    if m["errUlps"] != "-8.0" or m["agree"] != 1 or m["digits"] != 37:
        bad += 1
        print("metrics on the round-trip cell:", m)
    if median([1, 2, 3]) != 2 or median([1, 2, 3, 4]) != 2.5 or median([1, 3]) != 2:
        bad += 1
        print("median")
    print("selftest ok" if not bad else f"selftest: {bad} failure(s)")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    doc = build(parse_lines(sys.stdin))
    if "--check" in argv:
        if not OUT_JSON.exists():
            print("ladder.json missing")
            return 1
        committed = json.loads(OUT_JSON.read_text())
        diff = first_difference(strip_volatile(committed), strip_volatile(doc))
        if not diff:
            print(f"ladder ok: {len(doc['scenarios'])} scenarios, {sum(len(s['inputs']) for s in doc['scenarios'])} inputs")
            return 0
        print("ladder.json is stale; run `make ladder`")
        print("first difference: " + diff)
        return 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    if OUT_JSON.exists():  # keep the live-cap measurements until livecap.py rewrites them
        old = json.loads(OUT_JSON.read_text())
        for k in ("liveRunner", "liveSelector", "liveNote"):
            if k in old:
                doc[k] = old[k]
        old_scn = {s["id"]: s for s in old.get("scenarios", [])} if isinstance(old.get("scenarios"), list) else {}
        for s in doc["scenarios"]:
            if "liveMaxN" in old_scn.get(s["id"], {}):
                s["liveMaxN"] = old_scn[s["id"]]["liveMaxN"]
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")
    OUT_MD.write_text(render_md(doc))
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}: {len(doc['scenarios'])} scenarios, {sum(len(s['inputs']) for s in doc['scenarios'])} inputs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

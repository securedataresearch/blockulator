#!/usr/bin/env python3
"""Where the gas goes: a profile of FP19Lib and FP127Lib on the sweep's seeded
random inputs.

    uv run scripts/sweep/gasprofile.py          # inputs, the passes, the via_ir bench -> docs/benchmarks/profile.{md,json}
    uv run scripts/sweep/gasprofile.py report   # re-write from the last outputs in cache/sweep/

Three passes over the same inputs (scripts/sweep/sweep.py writes them to
cache/sweep/, not committed), all through the inline libraries with the gas
read inside the call's own window (test/sweep/Sweep.t.sol):

  plain  the committed libraries: each op's total gas (median, p99, max);
  count  test-only copies whose rounding-test fallbacks count themselves
         (scripts/fp127/gen.py --count-lib): the share of inputs that left the
         fast path. Results must equal the plain pass's word for word;
  probe  test-only copies with a gas probe around each named helper
         (gen.py --probe-lib, PROBES): per helper, calls per input and its gas
         as a share of the plain total, inclusive (with the probed helpers it
         calls) and exclusive (without them). The probes' own cost is taken
         out (PROBE_OVH, PROBE_RESIDUAL); the residual per probe call left
         after that is reported as the calibration error;
  forced the probe pass again on FP19's first 4,000 inputs per op with a
         second stage, the rounding test forced to fail (gen.py --forced),
         against make sweep's second-stage pass (run_wide): what a fallback
         costs and where, wexpm1's share first.

Then the build-setting bench (test/profile/ViaIr.t.sol) twice, under the
default profile (via_ir = false) and [profile.viair], beside the Yul objects.
The object's own call and dispatch cost (a flat selector switch is a linear
chain, FP127's a binary search: it grows with the comparisons
before the selector's case, gen.py dispatch_steps) is fitted on the trivial
ops, where the inline call is the same code, and taken out of the heavy ops'
object column.
"""
import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "sweep"))
import sweep as S  # noqa: E402

G = S.G
D = S.D
OUT = ROOT / "docs" / "benchmarks"
OPS = [("fp19", op) for op in S.OPS19] + [("fp127", op) for op in S.OPS127 + ["lambertW0", "lambertWm1"]]
TRIVIAL = {"fp127": ["abs", "neg", "sign", "floor", "ceil", "frac", "add", "sub", "min", "max"],
           "fp19": ["abs", "neg", "sign", "cmp", "lt", "eq", "min", "max"]}
HEAVY = {"fp127": ["mul", "div", "sqrt", "exp", "ln", "pow", "cbrt", "sinh", "cosh", "erf", "normCdf", "lambertW0", "lambertWm1"],
         "fp19": ["add", "mul", "div", "sqrt", "exp", "ln", "pow", "erf", "normCdf", "lambertW0", "lambertWm1",
                   "exp2", "log2", "cbrt", "cosh", "tanh", "hypot"]}


def stats(gs):
    g = sorted(gs)
    return {"median": g[len(g) // 2], "p99": g[int(0.99 * (len(g) - 1))], "max": g[-1]} if g else {}


# ---- the probe pass ---------------------------------------------------------

def probe_rows(lib, op, plain, kind="probe"):
    """Per helper of the op's closure: calls per input, inclusive and
    exclusive share of the plain total; and the calibration residual. kind
    probewide: the forced second stage, against the wide pass's totals."""
    rec = S.load_rec(kind, f"{lib}_{op}")
    if rec is None:
        return None
    assert [o for o, _, _ in rec] == [d[-2] for d in plain], f"{lib} {op}: the {kind} pass changed a result"
    names = G.PROBES[lib]
    have = S.closures(lib).get(op, set())
    total = sum(g for *_, g in plain)
    ok = [(r, p) for r, p in zip(rec, plain) if r[2] and p[-1]]
    ovh = (G.PROBE_OVH - G.COUNT_SLOT) // 32
    calls_all = sum(sum(w[(G.PROBE_BASE - G.COUNT_SLOT) // 32 + 3 * i + 1] for i in range(len(names))) for (_, _, w), _ in ok)
    resid = sum(g - w[ovh] - p[-1] for (_, g, w), p in ok)
    helpers = {}
    for i, h in enumerate(names):
        if h not in have:
            continue
        b = (G.PROBE_BASE - G.COUNT_SLOT) // 32 + 3 * i
        inc = sum(w[b] for (_, _, w), _ in ok)
        calls = sum(w[b + 1] for (_, _, w), _ in ok)
        exc = sum(w[b + 2] for (_, _, w), _ in ok)
        if calls == 0:
            helpers[h] = {"callsPerInput": 0, "inclusivePct": 0, "exclusivePct": 0, "gasPerCall": 0}
            continue
        helpers[h] = {"callsPerInput": round(calls / len(ok), 3),
                      "inclusivePct": round(100 * inc / total, 1),
                      "exclusivePct": round(100 * exc / total, 1),
                      "gasPerCall": round(inc / calls)}
    return {"helpers": helpers, "probeCalls": calls_all,
            "residualPerCall": round(resid / calls_all, 1) if calls_all else None}


# ---- the via_ir bench ---------------------------------------------------------

def run_viair():
    """VIA| lines of the bench under both profiles -> cache/sweep/viair-*.log."""
    for prof in ("default", "viair"):
        r = subprocess.run(["forge", "test", "--match-path", "test/profile/ViaIr.t.sol", "-vv"], cwd=ROOT,
                           env={**__import__("os").environ, "FOUNDRY_PROFILE": prof},
                           capture_output=True, text=True, check=True)
        (D / f"viair-{prof}.log").write_text(r.stdout)


def parse_via(prof):
    out = {}
    for ln in (D / f"viair-{prof}.log").read_text().splitlines():
        if "VIA|" not in ln:
            continue
        _, lib, op, i, form, g = ln.strip()[ln.strip().index("VIA|"):].split("|")
        out.setdefault((lib, op, form), []).append(int(g))
    return {k: int(statistics.median(v)) for k, v in out.items()}


def ranks(lib):
    """Each export's comparisons in its object's selector dispatch before its
    case: its position in a flat switch, or the levels of the binary search
    plus its position in the leaf (gen.py dispatch_steps)."""
    ops = json.loads((G.LIBS[lib]["src"].parent / "ops.json").read_text())["ops"]
    by = {}
    for o in ops:
        by.setdefault(o.get("object", G.LIBS[lib]["object"]), []).append(o)
    out = {}
    for obj, v in by.items():
        sels = sorted((o["selector"] for o in v), key=lambda s: int(s, 16))
        steps = G.dispatch_steps(sels, G.flat_dispatch(obj, len(sels)))
        out.update({o["name"]: steps[o["selector"]] for o in v})
    return out


def fit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my - b * mx, b


def viair_rows():
    leg, ir = parse_via("default"), parse_via("viair")
    rows, fits = [], {}
    for lib in ("fp127", "fp19"):
        rk = ranks(lib)
        pts = [(rk[op], leg[(lib, op, "object")] - leg[(lib, op, "inline")]) for op in TRIVIAL[lib]
               if (lib, op, "object") in leg and (lib, op, "inline") in leg]
        a, b = fit([p[0] for p in pts], [p[1] for p in pts])
        fits[lib] = {"base": round(a), "perRank": round(b, 1), "points": len(pts)}
        for op in HEAVY[lib]:
            if (lib, op, "inline") not in leg:
                continue
            o = leg[(lib, op, "object")]
            net = round(o - (a + b * rk[op]))
            rows.append({"lib": lib, "op": op, "inlineLegacy": leg[(lib, op, "inline")],
                         "inlineViaIr": ir.get((lib, op, "inline")), "object": o, "objectNet": net,
                         "selectorRank": rk[op]})
    return rows, fits


# ---- the report -------------------------------------------------------------

def report():
    ops = []
    for lib, op in OPS:
        data = S.load(f"{lib}_{op}")
        row = {"lib": lib, "op": op, "n": len(data), **stats([g for *_, g in data if g]), **S.fallback(lib, op, data)}
        pr = probe_rows(lib, op, data)
        if pr:
            row.update(pr)
        ops.append(row)
    forced = []
    for op in S.WIDE19:
        if not (D / f"wide_{op}.out").exists():
            continue
        data = S.load(f"wide_{op}")
        row = {"lib": "fp19", "op": op, "stage": "forced", "n": len(data), **stats([g for *_, g in data if g])}
        pr = probe_rows("fp19", op, data, "probewide")
        if pr:
            row.update(pr)
        forced.append(row)
    via, fits = viair_rows()
    doc = {"_doc": __doc__.strip(), "seed": S.SEED, "probeResidual": G.PROBE_RESIDUAL,
           "probes": G.PROBES, "ops": ops, "forced": forced, "viaIr": via, "objectCallFit": fits}
    (OUT / "profile.json").write_text(json.dumps(doc, indent=1) + "\n")

    def fb(r):
        return S.pct(r)

    def top(r, k=3):
        hs = sorted(((h, v) for h, v in r.get("helpers", {}).items() if v["exclusivePct"] >= 1),
                    key=lambda t: -t[1]["exclusivePct"])[:k]
        return ", ".join(f"`{h}` {v['exclusivePct']:.0f}%" for h, v in hs) or "—"

    md = ["# Gas profile",
          "",
          "Generated by `make profile` (`scripts/sweep/gasprofile.py`) on the sweep's seeded random inputs "
          "(`scripts/sweep/sweep.py`, seed 20261020), through the inline libraries with the gas read inside "
          "the call's own window, so the harness's dispatch is not in it. Data: `profile.json`. Method in the "
          "script's docstring; in short:",
          "",
          "- **gas**: the committed library, median / 99th percentile / largest over the op's inputs;",
          "- **fallback**: the share of inputs whose rounding test fired (FP19 `rbad`; FP127 `rbad127` and `rbadw` on "
          "every transcendental's fast value, and the double-word `l2p` and pow's `powmid` where the one-word log "
          "or `pow2t` could not decide; after an arrow, the share whose middle stage's test, `rbadm` or `rbadm127`, "
          "fired too), counted by a test-only copy of the library whose results "
          "match the committed one's word for word; a dash: the op has no such test (Lambert W in FP19 "
          "tests its one-word step and runs the wide step, `lwfix`, only on a miss);",
          "- **helpers**: test-only gas probes around the named helpers. *exclusive* is a helper's gas without "
          "the probed helpers it calls, as a share of the op's total; *inclusive* counts them; the probes' own "
          "cost is taken out. Shares are over all inputs, so a fallback that runs rarely shows small.",
          "",
          "Probed: FP19 " + ", ".join(f"`{h}`" for h in G.PROBES["fp19"]) + "; FP127 "
          + ", ".join(f"`{h}`" for h in G.PROBES["fp127"]) + ".",
          ""]
    for lib, title in (("fp19", "FP19"), ("fp127", "FP127")):
        md += [f"## {title}", "",
               "| op | inputs | gas median / p99 / max | fallback | largest helpers (exclusive share) |",
               "|---|---:|---:|---:|---|"]
        for r in ops:
            if r["lib"] == lib:
                md.append(f"| {r['op']} | {r['n']:,} | {r.get('median', 0):,} / {r.get('p99', 0):,} / {r.get('max', 0):,} | "
                          f"{fb(r)} | {top(r)} |")
        md += ["", f"### {title} helpers in detail", "",
               "Per op and probed helper it runs: calls per input, gas per call (inclusive), and the share of the "
               "op's total gas, exclusive / inclusive.", "",
               "| op | helper | calls / input | gas / call | exclusive | inclusive |",
               "|---|---|---:|---:|---:|---:|"]
        for r in ops:
            if r["lib"] != lib:
                continue
            for h, v in sorted(r.get("helpers", {}).items(), key=lambda t: -t[1]["inclusivePct"]):
                if v["callsPerInput"]:
                    md.append(f"| {r['op']} | `{h}` | {v['callsPerInput']:g} | {v['gasPerCall']:,} | "
                              f"{v['exclusivePct']:.1f}% | {v['inclusivePct']:.1f}% |")
        md.append("")
    md += ["## FP19, the second stage forced",
           "",
           f"The first {S.WIDE_N:,} inputs of each op with a second stage (and of its wider rows), through the probed "
           "library with the rounding test forced to fail (`gen.py --probe-lib --forced`), as `make sweep`'s "
           "second-stage pass: what every fallback costs, and where. Gas is the plain forced pass's "
           "(`FP19LibWide`); shares are of it.",
           "",
           "| op | inputs | forced gas median / p99 / max | `wexpm1` exclusive (calls / input) | largest helpers (exclusive share) |",
           "|---|---:|---:|---:|---|"]
    for r in forced:
        w = r.get("helpers", {}).get("wexpm1")
        wc = f"{w['exclusivePct']:.0f}% ({w['callsPerInput']:g})" if w and w["callsPerInput"] else "—"
        md.append(f"| {r['op']} | {r['n']:,} | {r.get('median', 0):,} / {r.get('p99', 0):,} / {r.get('max', 0):,} | {wc} | {top(r, 4)} |")
    md += ["", "### Forced second stage, helpers in detail", "",
           "| op | helper | calls / input | gas / call | exclusive | inclusive |",
           "|---|---|---:|---:|---:|---:|"]
    for r in forced:
        for h, v in sorted(r.get("helpers", {}).items(), key=lambda t: -t[1]["inclusivePct"]):
            if v["callsPerInput"]:
                md.append(f"| {r['op']} | `{h}` | {v['callsPerInput']:g} | {v['gasPerCall']:,} | "
                          f"{v['exclusivePct']:.1f}% | {v['inclusivePct']:.1f}% |")
    md.append("")
    res = [r["residualPerCall"] for r in ops + forced if r.get("residualPerCall") is not None and r.get("probeCalls")]
    md += [f"Probe calibration: after the probes' recorded own cost (with a fixed {G.PROBE_RESIDUAL} gas per "
           f"call for the part their readings cannot see) is taken out, the probe pass's total differs from the "
           f"plain pass's by {min(res):+.1f} to {max(res):+.1f} gas per probe call across the ops.", ""]
    md += ["## Build setting: `via_ir`",
           "",
           "`test/profile/ViaIr.t.sol` on eight typical inputs per op (medians), compiled with the default profile "
           "(`via_ir = false`, as `make bench`) and with `[profile.viair]`. *Object* is the whole `staticcall`; "
           "*object net* takes out its call and selector-dispatch cost, fitted on the trivial ops as "
           + "; ".join(f"{k.upper()} {v['base']:,} {'+' if v['perRank'] >= 0 else '−'} {abs(v['perRank']):g} per dispatch comparison" for k, v in fits.items())
           + ". *Gap* is inline over object net.",
           "",
           "| lib | op | inline, via_ir false | inline, via_ir true | object (staticcall) | object net | gap, false → true |",
           "|---|---|---:|---:|---:|---:|---:|"]
    for v in via:
        g0 = v["inlineLegacy"] / v["objectNet"] - 1 if v["objectNet"] > 0 else 0
        g1 = v["inlineViaIr"] / v["objectNet"] - 1 if v["objectNet"] > 0 and v["inlineViaIr"] else 0
        md.append(f"| {v['lib'].upper()} | {v['op']} | {v['inlineLegacy']:,} | {v['inlineViaIr']:,} | {v['object']:,} | "
                  f"{v['objectNet']:,} | {100 * g0:+.0f}% → {100 * g1:+.0f}% |")
    (OUT / "profile.md").write_text("\n".join(md) + "\n")
    print("wrote docs/benchmarks/profile.{md,json}")


def main():
    if sys.argv[1:] != ["report"]:
        S.gen()
        subprocess.run(["forge", "test", "--match-path", "test/sweep/Sweep.t.sol", "-q"], cwd=ROOT, check=True)
        S.run_instrumented("count")
        S.run_instrumented("probe")
        S.run_wide()
        S.run_instrumented("probe", forced=True)
        run_viair()
    report()


if __name__ == "__main__":
    main()

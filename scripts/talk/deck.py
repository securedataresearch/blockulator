#!/usr/bin/env python3
"""Build the talk's slide deck: one conceptual plot per slide, drawn from the
measured data (or from exact arithmetic where the plot is a property of a
format), laid out as 16:9 pages and written to docs/talks/dust-is-over.pdf.

    make talk

Each slide is a title (a short claim), one plot made by a function below, and
a source line. The spoken words live in docs/talks/dust-is-over.md.
"""
from __future__ import annotations

import io
import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
import mpmath  # noqa: E402
import weasyprint  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "talks" / "dust-is-over.pdf"
BENCH = ROOT / "docs" / "benchmarks"
DEPLOY = ROOT / "contracts" / "deployments"

# One identity per ruler, fixed for the whole deck (validated categorical
# order on the light surface). The two rulers the talk is about take the
# first two slots; the WAD libraries are one class, drawn in gray.
INK, MUTED, FAINT, GRID, SURFACE = "#0b0b0b", "#52514e", "#a9a8a2", "#e4e3df", "#fcfcfb"
SERIES = {"FP256": "#2a78d6", "FP127": "#eb6834", "binary128": "#1baf7a", "64.64": "#6250d6", "WAD": "#8a8984"}
RULERS = ["WAD", "64.64", "binary128", "FP127", "FP256"]
FORM = {"WAD": "solady", "64.64": "abdk", "binary128": "quad", "FP127": "fp127lib", "FP256": "fp256"}
DEPLOYED = "#0b0b0b"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 15, "text.color": INK,
    "axes.edgecolor": MUTED, "axes.labelcolor": MUTED, "axes.linewidth": 1,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 1,
    "legend.frameon": False, "svg.fonttype": "none",
})


def svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def figure(w=11.5, h=5.2):
    return plt.subplots(figsize=(w, h))


def line(ax, xs, ys, name, **kw):
    hero = name in ("FP127", "FP256")
    ax.plot(xs, ys, color=SERIES[name], lw=2.8 if hero else 2, marker="o", ms=7, mec=SURFACE, mew=2,
            label=name, zorder=4 if hero else 3, **kw)


def end_labels(ax, x, ends: dict, nudge: dict | None = None, fmt="{n}  {v}"):
    nudge = nudge or {}
    for n, v in ends.items():
        ax.text(x, v + nudge.get(n, 0), fmt.format(n=n, v=v), color=INK, fontsize=13, va="center")


def legend_below(ax, n):
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncols=n, fontsize=12)


# --- data -------------------------------------------------------------------

LADDER = json.loads((BENCH / "ladder.json").read_text())
EDGES = json.loads((BENCH / "edges.json").read_text())
ACCRUAL = json.loads((BENCH / "accrual-deployed.json").read_text())
RELEASE = json.loads((DEPLOY / "RELEASE.json").read_text())
NS = [1, 2, 5, 10, 20, 50, 100, 365, 1000, 10000]


def ladder_input(sid: str, name: str = "reference") -> dict:
    s = next(x for x in LADDER["scenarios"] if x["id"] == sid)
    return next(i for i in s["inputs"] if i["name"] == name)


def ladder_digits(sid: str, ruler: str, name: str = "reference") -> dict[int, int]:
    cells = ladder_input(sid, name)["cells"][FORM[ruler]]
    return {int(n): c["digits"] for n, c in cells.items() if isinstance(c, dict) and c.get("digits") is not None}


def accrual_case(cid: str) -> dict:
    return next(c for c in ACCRUAL["cases"] if c["id"] == cid)


def pi_table() -> dict[str, list[int]]:
    want = {"FP256 primitives": "FP256", "FP127Lib primitives": "FP127", "ABDKMathQuad": "binary128",
            "ABDKMath64x64": "64.64", "Solady": "WAD"}
    lines = [l for l in (BENCH / "pi.md").read_text().splitlines() if l.startswith("|")]
    head = [c.strip() for c in lines[0].strip("|").split("|")]
    cols = {want[h]: i for i, h in enumerate(head) if h in want}
    out = {k: [] for k in cols}
    for l in lines[2:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if not cells[0].isdigit():
            break
        for k, i in cols.items():
            out[k].append(int(re.match(r"\d+", cells[i]).group()))
    return out


def edge_cell(probe: dict, ruler: str):
    """digits, or one of 'zero', 'revert', 'n/a', 'range'."""
    c = probe["cells"].get(FORM[ruler], {})
    if c.get("range"):
        return "range"
    if c.get("unsupported"):
        return "n/a"
    if c.get("reverted"):
        return "revert"
    if c.get("zero") or c.get("digits") == 0:
        return "zero"
    return c.get("digits")


def edge_probe(pid: str) -> dict:
    return next(p for op in EDGES["ops"] for p in op["probes"] if p["id"] == pid)


# --- the market (slides 2, 3, 16) ---------------------------------------------

R0, K, MULT, PRINCIPAL = 0.1, 50.0, 4.0, 10e6  # target 10%, 50/yr adaptation, curve x4 at u = 100%, 10M


def market_rate(d):
    return MULT * R0 * math.exp(K * d / 365)


def market_overcharge(d):
    T = d / 365
    true = PRINCIPAL * (math.exp(MULT * R0 * (math.exp(K * T) - 1) / K) - 1)
    avg = (1 + math.exp(K * T) + 2 * math.exp(K * T / 2)) / 4
    return PRINCIPAL * (math.exp(MULT * R0 * avg * T) - 1) - true


def market_errors() -> dict[str, dict[int, float]]:
    out = {"deployed": {}, "FP127": {}, "FP256": {}}
    for d in (1, 7):
        t = accrual_case(f"morpho-u100-10pct-{d}d")["truth"]["continuous"]
        out["deployed"][d] = abs(float(t["deployed"]["errTokens"]))
        out["FP127"][d] = abs(float(t["fp127"]["errTokens"]))
        out["FP256"][d] = abs(float(t["fp256"]["errTokens"]))
    return out


def plot_market() -> str:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.2), gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.32})
    xs = [7 * i / 400 for i in range(401)]
    a1.plot(xs, [100 * market_rate(x) for x in xs], color=SERIES["FP256"], lw=2.5, label="the rate", zorder=3)
    tx = [0, 3.5, 7]
    a1.plot(tx, [100 * market_rate(x) for x in tx], color=SERIES["FP127"], lw=2, ls=(0, (6, 3)),
            marker="o", ms=8, mec=SURFACE, mew=2, label="the contract's two straight lines", zorder=4)
    a1.set_xlabel("days since the last transaction")
    a1.set_ylabel("borrow rate, % a year")
    a1.set_xlim(0, 7)
    a1.set_ylim(0, 125)
    a1.legend(loc="upper left", fontsize=12)
    days = [0.25 * i for i in range(29)]
    a2.plot(days, [market_overcharge(d) for d in days], color=SERIES["FP127"], lw=2.5, zorder=3,
            label="the straight lines' overcharge (formula)")
    meas = market_errors()["deployed"]
    a2.plot(list(meas), list(meas.values()), ls="none", marker="o", ms=10, color=DEPLOYED, mec=SURFACE, mew=2,
            label="the deployed contract (measured)", zorder=4)
    for d, v in meas.items():
        a2.annotate(f"+{v:,.2f}" if v < 100 else f"+{v:,.0f}", (d, v), xytext=(-14, 10), textcoords="offset points",
                    ha="right", fontsize=13, color=INK)
    a2.set_xlabel("days since the last transaction")
    a2.set_ylabel("USDC booked that the formula never accrued")
    a2.set_xlim(0, 7.3)
    a2.set_ylim(0, 3400)
    a2.legend(loc="upper left", fontsize=12)
    return svg(fig)


def plot_market_errors(token_line: bool = False) -> str:
    err = market_errors()
    fig, ax = figure()
    style = {"deployed": (DEPLOYED, "the deployed contract"), "FP127": (SERIES["FP127"], "FP127"),
             "FP256": (SERIES["FP256"], "FP256")}
    for i, (k, (col, lab)) in enumerate(style.items()):
        xs = [0 + (i - 1) * 0.12, 1 + (i - 1) * 0.12]
        ys = [err[k][1], err[k][7]]
        ax.plot(xs, ys, ls="none", marker="o", ms=13, color=col, mec=SURFACE, mew=2, label=lab, zorder=4)
        for x, y in zip(xs, ys):
            txt = f"{y:,.2f} USDC" if y >= 1 else f"10^{math.floor(math.log10(y))}"
            ax.annotate(txt, (x, y), xytext=(12, 0), textcoords="offset points", va="center", fontsize=12, color=INK)
    ax.set_yscale("log")
    ax.set_ylim(1e-75, 1e5)
    ax.set_yticks([1e-70, 1e-60, 1e-50, 1e-40, 1e-30, 1e-20, 1e-10, 1, 1e4])
    ax.set_xticks([0, 1], ["idle 1 day", "idle 7 days"])
    ax.set_xlim(-0.5, 1.75)
    ax.set_ylabel("error in the interest, USDC (log scale)")
    ax.grid(axis="x", visible=False)
    if token_line:
        ax.axhspan(1e-75, 1e-6, color=SERIES["FP256"], alpha=0.07, lw=0, zorder=1)
        ax.axhline(1e-6, color=MUTED, lw=1.2, ls=(0, (4, 4)))
        ax.text(1.72, 2e-6, "one unit of USDC (10^-6)", ha="right", va="bottom", fontsize=12, color=MUTED)
        ax.text(1.72, 1e-40, "below anything\nthe token can hold", ha="right", fontsize=13, color=SERIES["FP256"])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncols=3, fontsize=12)
    return svg(fig)


def plot_live_markets() -> str:
    pts = []
    for c in ACCRUAL["cases"]:
        if c.get("group") != "live":
            continue
        t = next(iter(c["truth"].values()))
        d = t.get("deployed", {}).get("digitsInterest")
        if d is None or not c.get("t"):
            continue
        pts.append((c["t"] / 86400, min(d, 20)))
    fig, ax = figure()
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=34, color=SERIES["WAD"], alpha=0.75,
               edgecolors=SURFACE, linewidths=1, zorder=3, label=f"{len(pts)} live accruals, two lending protocols")
    ax.set_xscale("log")
    ax.set_xlabel("days since the market was last touched (log scale)")
    ax.set_ylabel("digits right in the interest")
    ax.set_ylim(0, 20)
    ax.axhline(4, color=SERIES["FP127"], lw=1.2, ls=(0, (4, 4)))
    ax.text(ax.get_xlim()[1], 4.4, "4 digits", ha="right", fontsize=12, color=SERIES["FP127"])
    ax.legend(loc="upper right", fontsize=12)
    return svg(fig)


# --- dust and the two goals (slides 1, 5, 6, 7, 8) ----------------------------

def wad_drift() -> tuple[list[int], list[float]]:
    cells = ladder_input("compound")["cells"][FORM["WAD"]]
    ns = [n for n in NS if n <= 365 and str(n) in cells]
    return ns, [-float(cells[str(n)]["errUlps"]) for n in ns]


def plot_title() -> str:
    ns, units = wad_drift()
    fig, ax = figure(11.5, 3.9)
    ax.plot([0, 365], [0, units[0] * 365], color=MUTED, lw=1.2, ls=(0, (4, 4)), zorder=2,
            label=f"day one's {units[0]:,.0f} units, repeated every day")
    ax.plot(ns, units, color=SERIES["WAD"], lw=2.5, marker="o", ms=8, mec=SURFACE, mew=2, zorder=3)
    ax.annotate(f"{units[-1]:,.0f} units short after a year", (ns[-1], units[-1]), xytext=(-20, 8),
                textcoords="offset points", ha="right", fontsize=13, color=INK)
    ax.set_xlabel("days of daily compounding, $10,000 at 10%, on an 18-decimal ruler")
    ax.set_ylabel("units of 10^-18 short")
    ax.set_xlim(0, 380)
    ax.legend(loc="upper left", fontsize=12)
    return svg(fig)


def plot_drift_all() -> str:
    fig, ax = figure()
    i = ladder_input("compound")
    for name in RULERS:
        cells = i["cells"][FORM[name]]
        xs = [n for n in NS if str(n) in cells and cells[str(n)].get("relErr") not in (None, "0")]
        ys = [abs(float(cells[str(n)]["relErr"])) for n in xs]
        line(ax, xs, ys, name)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ends = {n: abs(float(i["cells"][FORM[n]]["10000"]["relErr"])) for n in RULERS}
    ax.text(10000 * 1.4, ends["WAD"], "WAD and 64.64", va="center", fontsize=13)
    for n in ("binary128", "FP127", "FP256"):
        ax.text(10000 * 1.4, ends[n], n, va="center", fontsize=13)
    ax.set_xlim(0.7, 10000 * 6)
    ax.set_xlabel("days of daily compounding (log scale)")
    ax.set_ylabel("relative error in the balance (log scale)")
    legend_below(ax, 5)
    return svg(fig)


def plot_goal_one() -> str:
    fig, ax = figure(11.5, 4.8)
    vals = {n: ladder_digits("compound", n)[365] for n in RULERS}
    ys = list(range(len(RULERS)))
    for y, n in zip(ys, RULERS):
        ax.barh(y, vals[n], color=SERIES[n], height=0.62, zorder=3)
        ax.text(vals[n] + 0.8, y, f"{vals[n]}", va="center", fontsize=15, color=INK)
    ax.set_yticks(ys, RULERS)
    ax.set_xlabel("digits right after a year of daily compounding")
    ax.set_xlim(0, 75)
    ax.grid(axis="y", visible=False)
    return svg(fig)


# the rulers as formats: finest mark and largest value, in log10
FIXED = {"WAD": (-18, math.log10(2**255 / 1e18)), "64.64": (math.log10(2**-64), math.log10(2**63)),
         "FP127": (math.log10(2**-128), math.log10(2**127))}
FLOAT = {"binary128": 113 * math.log10(2), "FP256": 237 * math.log10(2)}


def digits_at(name: str, e: float):
    """Digits a format can hold for a value of size 10^e; None past its top."""
    if name in FLOAT:
        return FLOAT[name]
    lo, hi = FIXED[name]
    if e > hi:
        return None
    return max(0.0, e - lo)


def plot_rulers(lit: tuple[str, ...] = ()) -> str:
    fig, ax = figure(11.5, 5.4)
    es = [x / 10 for x in range(-450, 451)]
    for name in RULERS:
        col = SERIES[name] if (not lit or name in lit) else GRID
        pts = [(e, digits_at(name, e)) for e in es]
        xs = [e for e, d in pts if d is not None]
        ys = [d for e, d in pts if d is not None]
        ax.plot(xs, ys, color=col, lw=3 if name in ("FP127", "FP256") else 2.2, label=name, zorder=4 if col != GRID else 2)
        if name in FIXED and FIXED[name][1] < 45:
            top = FIXED[name][1]
            ax.plot([top, top], [digits_at(name, top), 0], color=col, lw=1.5, ls=(0, (2, 2)))
            ax.text(top, digits_at(name, top) + 1.5, "revert", ha="center", fontsize=11, color=col if col != GRID else FAINT)
    ax.text(-44, 62, "a fixed ruler: zero below its finest mark,\nrevert above its largest value", fontsize=12,
            color=MUTED, va="top")
    ax.set_xlabel("size of the number, power of ten")
    ax.set_ylabel("digits the ruler can hold")
    ax.set_xlim(-45, 45)
    ax.set_ylim(0, 80)
    ax.set_xticks(range(-40, 41, 10), [f"10^{k}" for k in range(-40, 41, 10)])
    legend_below(ax, 5)
    return svg(fig)


def plot_words() -> str:
    rows = [
        ("WAD", [("sign", 1, FAINT), ("integer, about 196 bits", 196, SERIES["WAD"]), ("fraction, ~60", 59, MUTED)]),
        ("64.64", [("unused, 128 bits", 128, GRID), ("integer 64", 64, SERIES["64.64"]), ("fraction 64", 64, MUTED)]),
        ("binary128", [("unused, 128 bits", 128, GRID), ("exp 15", 16, SERIES["binary128"]), ("significand 112", 112, MUTED)]),
        ("FP127", [("s", 1, FAINT), ("integer 127", 127, SERIES["FP127"]), ("fraction 128", 128, MUTED)]),
        ("FP256", [("exp 19", 20, SERIES["FP256"]), ("significand 236", 236, MUTED)]),
    ]
    fig, ax = figure(11.5, 4.6)
    for y, (name, segs) in enumerate(reversed(rows)):
        x = 0
        for lab, w, col in segs:
            ax.add_patch(Rectangle((x, y - 0.32), w - 1.5, 0.64, color=col, lw=0))
            if w >= 40:
                ax.text(x + w / 2, y, lab, ha="center", va="center", fontsize=12,
                        color=INK if col in (GRID, FAINT) else "white")
            x += w
        ax.text(-6, y, name, ha="right", va="center", fontsize=14, color=INK)
    ax.set_xlim(-70, 258)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.axis("off")
    ax.text(128, -0.75, "one 256-bit word", ha="center", fontsize=12, color=MUTED)
    return svg(fig)


# --- converge or fit (slides 9, 10, 11) ----------------------------------------

def converge_vs_fit() -> tuple[list[int], list[float], list[float]]:
    """At each word width: bits a Newton square root reaches (it runs until the
    step stops changing anything), and bits a polynomial fitted once for 60 bits
    delivers for exp (its truncation error does not shrink with the word)."""
    widths = list(range(64, 257, 16))
    # the fitted exp: the shortest Taylor polynomial on [0, ln 2] within 2^-60
    with mpmath.workprec(400):
        deg = next(d for d in range(1, 60) if mpmath.log(2) ** (d + 1) / mpmath.factorial(d + 1) * 2 < mpmath.mpf(2) ** -60)
    newton, fitted = [], []
    for w in widths:
        with mpmath.workprec(w):
            a = mpmath.mpf(2)
            x = mpmath.mpf(1.5)
            for _ in range(20):
                x = (x + a / x) / 2
            xs = mpmath.log(2)
            p = sum(xs**k / mpmath.factorial(k) for k in range(deg + 1))
        with mpmath.workprec(w + 200):
            newton.append(float(-mpmath.log(abs(x / mpmath.sqrt(2) - 1) + mpmath.mpf(2) ** -(w + 1), 2)))
            fitted.append(float(-mpmath.log(abs(p / 2 - 1) + mpmath.mpf(2) ** -(w + 1), 2)))
    return widths, newton, fitted


def plot_converge() -> str:
    widths, newton, fitted = converge_vs_fit()
    fig, ax = figure()
    ax.plot(widths, newton, color=SERIES["FP256"], lw=2.8, marker="o", ms=7, mec=SURFACE, mew=2, zorder=4,
            label="converging: Newton's square root")
    ax.plot(widths, fitted, color=SERIES["FP127"], lw=2.8, marker="o", ms=7, mec=SURFACE, mew=2, zorder=4,
            label="fitted: an exp polynomial tuned for 60 bits")
    ax.text(widths[-1] + 4, newton[-1], f"{newton[-1]:.0f} bits", va="center", fontsize=13)
    ax.text(widths[-1] + 4, fitted[-1], f"{fitted[-1]:.0f} bits", va="center", fontsize=13)
    ax.set_xlabel("bits in the word")
    ax.set_ylabel("bits right in the answer")
    ax.set_xlim(56, 280)
    ax.set_ylim(0, 270)
    ax.legend(loc="upper left", fontsize=12)
    return svg(fig)


def plot_ramanujan() -> str:
    t = pi_table()
    terms = list(range(1, len(t["FP256"]) + 1))
    fig, ax = figure()
    for name in RULERS:
        line(ax, terms, t[name], name)
    ax.plot([1, terms[-1]], [7, 7 + 8 * (terms[-1] - 1)], color=MUTED, lw=1.2, ls=(0, (4, 4)), zorder=2)
    ax.text(7.35, 7 + 8 * 6.35 + 2, "the series alone:\n8 digits a term", fontsize=12, color=MUTED, ha="right", va="bottom")
    end_labels(ax, terms[-1] + 0.25, {n: t[n][-1] for n in RULERS},
               {"WAD": -2.2, "64.64": 2.2, "binary128": -2.2, "FP127": 2.2})
    ax.set_xlabel("terms of Ramanujan's series")
    ax.set_ylabel("correct digits of π")
    ax.set_xticks(terms)
    ax.set_xlim(0.6, terms[-1] + 0.2)
    ax.set_ylim(0, 85)
    legend_below(ax, 5)
    return svg(fig)


# release one's worst bits (contracts/deployments/FP256.md): the converging ops
# were exact to the 237-bit significand; exp, ln and pow ran on fitted kernels
RELEASE_ONE = {"add": 237, "sub": 237, "mul": 237, "div": 237, "sqrt": 237, "exp": 146, "ln": 149, "pow": 123}


def plot_release() -> str:
    prec = json.loads((ROOT / "docs" / "fp256" / "precision.json").read_text())
    now = {op: (237 if prec[op]["minBits"] >= 256 else prec[op]["minBits"]) for op in RELEASE_ONE}
    fig, ax = figure()
    ops = list(RELEASE_ONE)
    for x, op in enumerate(ops):
        a, b = RELEASE_ONE[op], now[op]
        ax.plot([x, x], [a, b], color=GRID, lw=3, zorder=2)
        ax.plot(x, a, "o", ms=13, color=SERIES["FP127"], mec=SURFACE, mew=2, zorder=3,
                label="release one" if x == 0 else None)
        ax.plot(x, b, "o", ms=13, color=SERIES["FP256"], mec=SURFACE, mew=2, zorder=4,
                label="release three" if x == 0 else None)
        if a != b:
            ax.text(x + 0.14, a, f"{a}", va="center", fontsize=12)
    ax.axvspan(-0.5, 4.5, color=SERIES["FP256"], alpha=0.05, lw=0)
    ax.text(2, 200, "converging:\nexact on day one", ha="center", fontsize=14, color=INK)
    ax.text(6, 200, "fitted:\nhad to be refit", ha="center", fontsize=14, color=INK)
    ax.set_xticks(range(len(ops)), ops)
    ax.set_ylabel("worst bits right, FP256 (237 = exact)")
    ax.set_ylim(95, 250)
    ax.set_xlim(-0.5, len(ops) - 0.5)
    ax.grid(axis="x", visible=False)
    legend_below(ax, 2)
    return svg(fig)


# --- the ruler with no ends (slides 12-15) --------------------------------------

HEAT_PROBES = ["ln(1+1e-9)", "log1p(1e-30)", "exp(-40)", "exp(-42)", "exp(-89)", "exp(89)", "mul(1e-10,1e-10)",
               "div(1e-9,1e12)", "sqrt(1e-30)", "pow(1.0001,-887272)", "pow(1.0001,887272)", "normCdf(-9)",
               "lambertWm1(-1e-10)"]


def plot_heatmap() -> str:
    fig, ax = figure(11.5, 5.6)
    cmap = plt.get_cmap("Blues")
    for r, pid in enumerate(HEAT_PROBES):
        p = edge_probe(pid)
        for c, name in enumerate(RULERS):
            v = edge_cell(p, name)
            if isinstance(v, (int, float)) and v > 0:
                ax.add_patch(Rectangle((c, r), 0.96, 0.92, color=cmap(0.18 + 0.8 * min(v, 72) / 72), lw=0))
                ax.text(c + 0.48, r + 0.46, f"{v}", ha="center", va="center", fontsize=12,
                        color="white" if v > 35 else INK)
            else:
                ax.add_patch(Rectangle((c, r), 0.96, 0.92, color=GRID, lw=0))
                ax.text(c + 0.48, r + 0.46, str(v), ha="center", va="center", fontsize=12,
                        color=SERIES["FP127"] if v in ("zero", "revert") else MUTED, fontweight="bold")
        ax.text(-0.1, r + 0.46, pid, ha="right", va="center", fontsize=12)
    for c, name in enumerate(RULERS):
        ax.text(c + 0.48, -0.15, name, ha="center", va="bottom", fontsize=13)
    ax.set_xlim(-3.2, len(RULERS))
    ax.set_ylim(len(HEAT_PROBES) + 0.1, -0.9)
    ax.axis("off")
    return svg(fig)


def plot_exp_sweep() -> str:
    probes = [p for op in EDGES["ops"] for p in op["probes"] if re.fullmatch(r"exp\(-?[\d.]+\)", p["id"])]
    probes.sort(key=lambda p: float(p["id"][4:-1]))
    fig, ax = figure()
    for name in RULERS:
        xs, ys, rx = [], [], []
        for p in probes:
            x = float(p["id"][4:-1])
            v = edge_cell(p, name)
            if isinstance(v, (int, float)):
                xs.append(x)
                ys.append(v)
            elif v == "zero":
                xs.append(x)
                ys.append(0)
            elif v in ("revert", "range"):
                rx.append(x)
        line(ax, xs, ys, name)
        if rx:
            ax.plot(rx, [-4] * len(rx), ls="none", marker="x", ms=9, mew=2.5, color=SERIES[name], zorder=4)
    ax.text(-100, -8.5, "×  reverted", fontsize=12, color=MUTED)
    ax.set_xlabel("x in exp(x)")
    ax.set_ylabel("digits right")
    ax.set_ylim(-11, 80)
    legend_below(ax, 5)
    return svg(fig)


def plot_per_second() -> str:
    fig, ax = figure(11.5, 4.8)
    vals = {n: ladder_digits("accrual-per-second", n)[365] for n in RULERS}
    ys = list(range(len(RULERS)))
    for y, n in zip(ys, RULERS):
        ax.barh(y, vals[n], color=SERIES[n], height=0.62, zorder=3)
        ax.text(vals[n] + 0.8, y, f"{vals[n]}", va="center", fontsize=15)
    ax.set_yticks(ys, RULERS)
    ax.set_xlabel("digits right after a year of per-second accrual at 5%")
    ax.set_xlim(0, 75)
    ax.grid(axis="y", visible=False)
    return svg(fig)


def plot_option() -> str:
    fig, ax = figure()
    for name in RULERS:
        d = ladder_digits("deep-tail-option", name)
        xs = [n for n in NS if n in d]
        line(ax, xs, [d[n] for n in xs], name)
    end_labels(ax, 10000 * 1.35, {n: ladder_digits("deep-tail-option", n).get(10000, 0) for n in RULERS},
               {"WAD": -4.5, "64.64": 0.5, "FP127": 3})
    ax.set_xscale("log")
    ax.set_xlabel("ticks the price has walked down (log scale)")
    ax.set_ylabel("digits right in the option's price")
    ax.set_ylim(-2, 80)
    ax.set_xlim(0.8, 10000 * 1.3)
    legend_below(ax, 5)
    return svg(fig)


# --- cost and the close (slides 17, 19, 20) -------------------------------------

def plot_gas() -> str:
    fig, ax = figure()
    for name in RULERS:
        xs, ys = [], []
        for s in LADDER["scenarios"]:
            i = next(x for x in s["inputs"] if x.get("reference"))
            c = i["cells"].get(FORM[name], {}).get("365")
            if isinstance(c, dict) and c.get("digits") is not None and c.get("gasPerStep"):
                xs.append(c["gasPerStep"])
                ys.append(c["digits"])
        ax.scatter(xs, ys, s=70, color=SERIES[name], edgecolors=SURFACE, linewidths=1.5, label=name,
                   zorder=4 if name in ("FP127", "FP256") else 3)
    ax.set_xscale("log")
    ax.set_xlabel("gas per step (log scale)")
    ax.set_ylabel("digits right after 365 steps")
    ax.set_ylim(-2, 80)
    ax.text(0.99, 0.02, "each dot: one scenario of the ladder, reference input", transform=ax.transAxes,
            ha="right", fontsize=11, color=MUTED)
    legend_below(ax, 5)
    return svg(fig)


def plot_live() -> str:
    live = RELEASE["live"]
    fig, ax = figure(11.5, 4.2)
    rows = [("the ladder: every scenario, input, library and N", live["ladder"]),
            ("the edges: every probe and library", live["edges"])]
    for y, (lab, st) in enumerate(rows):
        ax.barh(y, st["liveChecked"], color=SERIES["FP256"], height=0.55, zorder=3)
        ax.text(st["liveChecked"] + 120, y, f'{st["liveChecked"]:,} cells, {st["liveMismatches"]} mismatches',
                va="center", fontsize=15)
        ax.text(0, y + 0.42, f'{lab} — block {st["liveBlock"]:,}', fontsize=12, color=MUTED)
    ax.set_yticks([])
    ax.set_ylim(-0.6, 1.9)
    ax.set_xlim(0, 13500)
    ax.set_xlabel("cells re-run against the live contracts on Sepolia, " + rows[0][1]["liveDate"])
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    return svg(fig)


def plot_close() -> str:
    c = RELEASE["components"]
    fig, ax = figure(11.5, 4.6)
    ax.axis("off")
    ax.text(0, 0.78, "FP127", fontsize=30, fontweight="bold", color=SERIES["FP127"], transform=ax.transAxes)
    ax.text(0, 0.62, c["FP127"]["address"], fontsize=17, family="DejaVu Sans Mono", transform=ax.transAxes)
    ax.text(0, 0.40, "FP256", fontsize=30, fontweight="bold", color=SERIES["FP256"], transform=ax.transAxes)
    ax.text(0, 0.24, c["FP256"]["address"], fontsize=17, family="DejaVu Sans Mono", transform=ax.transAxes)
    ax.text(0, 0.02, "blockulator.com  ·  github.com/securedataresearch/blockulator", fontsize=15, color=MUTED,
            transform=ax.transAxes)
    return svg(fig)


# --- the deck -----------------------------------------------------------------

PI = "Ramanujan's series through each library's own sqrt, mul and div. docs/benchmarks/pi.md"
MARKET = ("10M USDC borrowed, utilization 100%, target rate 10%. The rate model and market as deployed "
          "(byte-equal to mainnet) vs the stated formula at 200 digits. docs/benchmarks/accrual-deployed.md")
WAD_NOTE = "WAD = an 18-decimal library; 64.64 and binary128 = the two ABDK formats."

SLIDES = [
    ("Dust is Over", plot_title, "$10,000 at 10%, compounded daily on an 18-decimal ruler. docs/benchmarks/ladder.json: compound"),
    ("Ten million dollars, untouched for a week", plot_market, MARKET),
    ("The same calculation, three ways", plot_market_errors, MARKET),
    ("It happens in live markets", plot_live_markets,
     "Every live lending reserve and market with $10k+ borrowed, block 26,206,698, accrued by the deployed code. docs/benchmarks/accrual-deployed.md"),
    ("Rounding with nowhere to go", plot_drift_all, "Daily compounding, reference input. " + WAD_NOTE),
    ("Goal one: round once", plot_goal_one, "A year of daily compounding, $10,000 at 10%. docs/benchmarks/ladder.json. " + WAD_NOTE),
    ("Goal two: never run out of ruler", plot_rulers, "Exact properties of each format: the finest mark, the largest value, the significand."),
    ("Five ways to spend one word", plot_words, "Bit layouts of each format in a 256-bit word."),
    ("Converge, or fit", plot_converge,
     "Computed in exact arithmetic at each width: Newton's sqrt(2), and the shortest Taylor polynomial for exp within 2^-60 on [0, ln 2], at x = ln 2."),
    ("The series never stops. The ruler does.", plot_ramanujan, PI),
    ("FP256 proved it by accident", plot_release,
     "Worst bits over the committed vectors. Release one: contracts/deployments/FP256.md; release three: docs/fp256/precision.json."),
    ("The walls", plot_heatmap, "One call each, at the end of the domain, against 200 digits. docs/benchmarks/edges.json. " + WAD_NOTE),
    ("exp, end to end", plot_exp_sweep, "docs/benchmarks/edges.json: exp probes. " + WAD_NOTE),
    ("A rate per second", plot_per_second, "5% a year accrued per second for a year. docs/benchmarks/ladder.json: accrual-per-second. " + WAD_NOTE),
    ("An option, walked down", plot_option,
     "Normal-distribution option priced each tick as the price walks to d1 = -12. docs/benchmarks/ladder.json: deep-tail-option. " + WAD_NOTE),
    ("The same market, rounded once", lambda: plot_market_errors(token_line=True), MARKET),
    ("What the digits cost", plot_gas, "Gas per step and digits after 365 steps, every ladder scenario. docs/benchmarks/ladder.json. " + WAD_NOTE),
    ("Both goals, met", lambda: plot_rulers(lit=("FP127", "FP256")), "Exact properties of each format."),
    ("Checked on chain", plot_live, "contracts/deployments/RELEASE.json"),
    ("Use FP127 and FP256", plot_close, "Blockulator 2.0. Sepolia; MIT licence."),
]

CSS = f"""
@page {{ size: 13.333in 7.5in; margin: 0; }}
body {{ margin: 0; font-family: 'DejaVu Sans', sans-serif; color: {INK}; background: {SURFACE}; }}
.slide {{ width: 13.333in; height: 7.5in; box-sizing: border-box; padding: 0.55in 0.75in 0.4in;
          page-break-after: always; display: flex; flex-direction: column; position: relative; }}
h1 {{ font-size: 34pt; font-weight: 700; letter-spacing: -0.01em; margin: 0 0 0.25in; line-height: 1.1; }}
.title h1 {{ font-size: 64pt; margin: 0.2in 0 0.1in; }}
.plot {{ flex: 1; display: flex; align-items: center; justify-content: center; min-height: 0; }}
.plot svg {{ max-width: 100%; max-height: 5.0in; height: auto; }}
.source {{ font-size: 9.5pt; color: {MUTED}; margin-top: 0.15in; }}
.num {{ position: absolute; right: 0.5in; bottom: 0.3in; font-size: 9.5pt; color: {MUTED}; }}
"""


def main() -> None:
    pages = []
    for k, (title, plot, source) in enumerate(SLIDES, 1):
        body = plot()
        body = body[body.index("<svg"):]
        cls = "slide title" if k == 1 else "slide"
        pages.append(f'<section class="{cls}"><h1>{title}</h1><div class="plot">{body}</div>'
                     f'<div class="source">{source}</div><div class="num">{k}</div></section>')
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(pages)}</body></html>"
    weasyprint.HTML(string=html).write_pdf(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(SLIDES)} slides)")


if __name__ == "__main__":
    main()

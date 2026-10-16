#!/usr/bin/env python3
"""Build the talk's slide deck: one conceptual plot per slide, drawn from the
measured data, laid out as 16:9 pages and written to docs/talks/dust-is-over.pdf.

    make talk

Each slide is a title (a short claim), one plot made by a function below from
the committed data files, and a source line. The spoken words live in
docs/talks/dust-is-over.md, not here.
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
import weasyprint  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "talks" / "dust-is-over.pdf"
BENCH = ROOT / "docs" / "benchmarks"

# One identity per library, fixed for the whole deck (validated categorical
# order, light surface). The two rulers this talk is about take slots 1 and 2.
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SERIES = {
    "FP256": "#2a78d6",
    "FP127": "#eb6834",
    "binary128": "#1baf7a",
    "64.64": "#6250d6",
    "WAD": "#8a8984",
}

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


# --- data -------------------------------------------------------------------

def pi_table() -> dict[str, list[int]]:
    """Digits per term from docs/benchmarks/pi.md, one column per ruler."""
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


def accrual_case(cid: str) -> dict:
    for c in json.loads((BENCH / "accrual-deployed.json").read_text())["cases"]:
        if c["id"] == cid:
            return c
    raise KeyError(cid)


# --- plots ------------------------------------------------------------------

def plot_ramanujan() -> str:
    t = pi_table()
    terms = list(range(1, len(t["FP256"]) + 1))
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    order = ["WAD", "64.64", "binary128", "FP127", "FP256"]
    for name in order:
        ax.plot(terms, t[name], color=SERIES[name], lw=2.8 if name in ("FP127", "FP256") else 2,
                marker="o", ms=7, mec=SURFACE, mew=2, label=name, zorder=3)
    # the series itself: about eight digits a term, until a ruler stops it
    ax.plot([1, terms[-1]], [7, 7 + 8 * (terms[-1] - 1)], color=MUTED, lw=1.2, ls=(0, (4, 4)), zorder=2)
    ax.text(7.35, 7 + 8 * 6.35 + 2, "the series alone:\n8 digits a term", fontsize=12, color=MUTED,
            ha="right", va="bottom")
    # direct labels at the right edge, nudged apart where two rulers stop close together
    ends = {n: t[n][-1] for n in order}
    nudge = {"WAD": -2.2, "64.64": 2.2, "binary128": -2.2, "FP127": 2.2, "FP256": 0}
    for n in order:
        ax.text(terms[-1] + 0.25, ends[n] + nudge[n], f"{n}  {ends[n]}", color=INK, fontsize=13, va="center")
    ax.set_xlabel("terms of Ramanujan's series")
    ax.set_ylabel("correct digits of π")
    ax.set_xticks(terms)
    ax.set_xlim(0.6, terms[-1] + 0.2)
    ax.set_ylim(0, 85)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncols=5, fontsize=12)
    return svg(fig)


def plot_market() -> str:
    """Left: the rate over a 7-day gap at full utilization, and the trapezoid the
    contract averages it with. Right: what the gap between them costs as the
    market sits idle longer: the trapezoid's overcharge by formula, and the
    deployed contract's measured overcharge at 1 and 7 days."""
    r0, k, mult, P = 0.1, 50.0, 4.0, 10e6  # target 10%, 50/yr adaptation, curve x4 at u = 100%, 10M
    rate = lambda d: mult * r0 * math.exp(k * d / 365)  # a year

    def overcharge(d):
        T = d / 365
        true = P * (math.exp(mult * r0 * (math.exp(k * T) - 1) / k) - 1)
        avg = (1 + math.exp(k * T) + 2 * math.exp(k * T / 2)) / 4
        return P * (math.exp(mult * r0 * avg * T) - 1) - true

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.2), gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.32})
    xs = [7 * i / 400 for i in range(401)]
    a1.plot(xs, [100 * rate(x) for x in xs], color=SERIES["FP256"], lw=2.5, label="the rate", zorder=3)
    tx = [0, 3.5, 7]
    a1.plot(tx, [100 * rate(x) for x in tx], color=SERIES["FP127"], lw=2, ls=(0, (6, 3)),
            marker="o", ms=8, mec=SURFACE, mew=2, label="the contract's two straight lines", zorder=4)
    a1.set_xlabel("days since the last transaction")
    a1.set_ylabel("borrow rate, % a year")
    a1.set_xlim(0, 7)
    a1.set_ylim(0, 125)
    a1.legend(loc="upper left", fontsize=12)

    days = [0.25 * i for i in range(29)]
    a2.plot(days, [overcharge(d) for d in days], color=SERIES["FP127"], lw=2.5, zorder=3,
            label="the straight lines' overcharge (formula)")
    meas = {d: float(accrual_case(f"morpho-u100-10pct-{d}d")["truth"]["continuous"]["deployed"]["errTokens"]) for d in (1, 7)}
    a2.plot(list(meas), list(meas.values()), ls="none", marker="o", ms=10, color=INK, mec=SURFACE, mew=2,
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


# --- the deck ---------------------------------------------------------------

SLIDES = [
    {"title": "Ten million dollars, untouched for a week",
     "plot": plot_market,
     "source": "10M USDC borrowed, utilization 100%, target rate 10%. Measured: the rate model and market as deployed (byte-equal to mainnet) vs the stated formula at 200 digits. docs/benchmarks/accrual-deployed.md"},
    {"title": "The series never stops. The ruler does.",
     "plot": plot_ramanujan,
     "source": "Ramanujan's series through each library's own sqrt, mul and div. docs/benchmarks/pi.md"},
]

CSS = f"""
@page {{ size: 13.333in 7.5in; margin: 0; }}
body {{ margin: 0; font-family: 'DejaVu Sans', sans-serif; color: {INK}; background: {SURFACE}; }}
.slide {{ width: 13.333in; height: 7.5in; box-sizing: border-box; padding: 0.55in 0.75in 0.4in;
          page-break-after: always; display: flex; flex-direction: column; }}
h1 {{ font-size: 34pt; font-weight: 700; letter-spacing: -0.01em; margin: 0 0 0.25in; line-height: 1.1; }}
.plot {{ flex: 1; display: flex; align-items: center; justify-content: center; min-height: 0; }}
.plot svg {{ max-width: 100%; max-height: 5.4in; height: auto; }}
.source {{ font-size: 9.5pt; color: {MUTED}; margin-top: 0.15in; }}
"""


def main() -> None:
    pages = []
    for s in SLIDES:
        body = s["plot"]()
        body = body[body.index("<svg"):]
        pages.append(f'<section class="slide"><h1>{s["title"]}</h1><div class="plot">{body}</div>'
                     f'<div class="source">{s["source"]}</div></section>')
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(pages)}</body></html>"
    weasyprint.HTML(string=html).write_pdf(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(SLIDES)} slides)")


if __name__ == "__main__":
    main()

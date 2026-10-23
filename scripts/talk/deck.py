#!/usr/bin/env python3
"""Build the talk's slide deck: one conceptual plot per slide, drawn from the
measured data (or from exact arithmetic where the plot is a property of a
format), laid out as 16:9 pages and written to docs/talks/dust-is-over.pdf.

    make talk

Each slide is a title (a short placeholder; the author supplies the wording),
one plot made by a function below, and a source line naming the committed file
the plot draws from. The order and the claims follow docs/talks/outline.md.
The spoken words are not in the PDF.
"""
from __future__ import annotations

import importlib.util
import io
import json
import math
import re
from fractions import Fraction
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
import mpmath  # noqa: E402
import weasyprint  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "talks" / "dust-is-over.pdf"
BENCH = ROOT / "docs" / "benchmarks"
DEPLOY = ROOT / "contracts" / "deployments"
REPLAYS = ROOT / "scripts" / "replays"

def mix(a: str, b: str, p: float) -> str:
    """CSS color-mix(in oklab, a p, b): the site derives its extra colours this way
    (static/css/blockulator.css), so the deck computes the same blend once here."""
    def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    def gam(c): return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    def oklab(h):
        r, g, b = (lin(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))
        l, m, s = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b,
                   0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b,
                   0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
        l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
        return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)
    L, A, B = (p * x + (1 - p) * y for x, y in zip(oklab(a), oklab(b)))
    l, m, s = ((L + 0.3963377774 * A + 0.2158037573 * B) ** 3, (L - 0.1055613458 * A - 0.0638541728 * B) ** 3,
               (L - 0.0894841775 * A - 1.2914855480 * B) ** 3)
    rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return "#" + "".join(f"{round(min(1, max(0, gam(c))) * 255):02x}" for c in rgb)


# The site's palette (static/css/site.css, synced from securedataresearch.net).
SITE_INK, SITE_G500, SITE_EMERALD, SITE_RED, SITE_GOLD, SITE_SAPPHIRE = (
    "#0a0a0a", "#737373", "#00694e", "#e4002b", "#a09860", "#4070a0")

# One colour per family, the same as the site's charts (blockulator.css --c-*):
# ours emerald and ink, the WAD libraries one gold, the protocols one slate.
# In the replays, the deployed protocol code is the protocol slate and its
# one-word fix (mulDivUp, mulUp) is WAD gold: it is still the 18-decimal
# ruler, rounded the other way.
INK, MUTED, FAINT, GRID, SURFACE = "#0b0b0b", "#52514e", "#a9a8a2", "#e4e3df", "#fcfcfb"
SERIES = {
    "FP256": SITE_INK,                               # --c-fp256: var(--ink)
    "FP127": SITE_EMERALD,                           # --c-fp127: var(--emerald)
    "binary128": mix(SITE_SAPPHIRE, SITE_RED, .55),  # --c-quad: --violet, color-mix(in oklab, sapphire 55%, red)
    "64.64": SITE_SAPPHIRE,                          # --c-6464: var(--sapphire)
    "WAD": SITE_GOLD,                                # --c-wad: var(--gold)
}
WAD_DARK = mix(SITE_GOLD, SITE_INK, .7)  # a second WAD library beside the first (gas slide): the gold, darker (5.4:1 on SURFACE)
RULERS = ["WAD", "64.64", "binary128", "FP127", "FP256"]
FORM = {"WAD": "solady", "64.64": "abdk", "binary128": "quad", "FP127": "fp127lib", "FP256": "fp256"}
DEPLOYED = mix(SITE_SAPPHIRE, SITE_G500, .5)  # --c-protocol: --slate, color-mix(in oklab, sapphire 50%, g-500)
FIX = SERIES["WAD"]

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


def md_rows(path: Path, first: str) -> list[list[str]]:
    """The cells of every markdown table row in `path` whose first cell starts with `first`."""
    out = []
    for l in path.read_text().splitlines():
        if l.startswith("| " + first):
            out.append([c.strip().strip("*") for c in l.strip().strip("|").split("|")])
    return out


# --- data -------------------------------------------------------------------

LADDER = json.loads((BENCH / "ladder.json").read_text())
ACCRUAL = json.loads((BENCH / "accrual-deployed.json").read_text())
RELEASE = json.loads((DEPLOY / "RELEASE.json").read_text())
SWEEP = json.loads((BENCH / "sweep.json").read_text())
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


def sup(e: int) -> str:
    return f"10^{e}"


# --- title (slide 1) ------------------------------------------------------------

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


# --- part 1: real failures (slides 2-6) --------------------------------------------

def plot_honest() -> str:
    """1.1: the Aave USDC control case. Every error sits below one unit of the token."""
    c = accrual_case("aave-usdc-u100-borrow-1d")
    t = c["truth"][c["primaryTruth"]]
    unit = 10.0 ** -c["decimals"]
    rows = [("Aave, as deployed", DEPLOYED, t["deployed"]), ("FP127", SERIES["FP127"], t["fp127"]),
            ("FP256", SERIES["FP256"], t["fp256"])]
    fig, ax = figure(11.5, 4.6)
    ax.axvspan(1e-75, unit, color=SERIES["FP256"], alpha=0.06, lw=0, zorder=1)
    ax.axvline(unit, color=MUTED, lw=1.4, ls=(0, (4, 4)), zorder=2)
    ax.text(unit * 3, -0.55, f"one unit of {c['symbol']} (10^-{c['decimals']})", fontsize=12, color=MUTED, va="center")
    ax.text(1e-73, -0.55, "every answer rounds to the same token amount", fontsize=12, color=SERIES["FP256"], va="center")
    for y, (lab, col, cell) in enumerate(rows):
        e = abs(float(cell["errTokens"]))
        ax.plot([e], [y], "o", ms=14, color=col, mec=SURFACE, mew=2, zorder=4)
        m, x = f"{e:.1e}".split("e")
        ax.text(e * 30 if e < 1e-20 else e / 30, y,
                f"{m}×10^{int(x)} USDC  ({cell['digitsInterest']} digits of the interest)",
                va="center", ha="left" if e < 1e-20 else "right", fontsize=13)
    ax.set_xscale("log")
    ax.set_xlim(1e-75, 1e3)
    ax.set_xticks([1e-70, 1e-60, 1e-50, 1e-40, 1e-30, 1e-20, 1e-10, 1],
                  ["10^-70", "10^-60", "10^-50", "10^-40", "10^-30", "10^-20", "10^-10", "1"])
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_ylim(len(rows) - 0.5, -0.85)
    ax.set_xlabel(f"error in a day's interest on {float(c['principalTokens']):,.0f} {c['symbol']} (log scale)")
    ax.grid(axis="y", visible=False)
    return svg(fig)


RESUPPLY = json.loads((REPLAYS / "resupply.json").read_text())


def plot_resupply() -> str:
    """1.2: the exchange rate 1e36 / price, floored to 0; then the LTV check against the cap."""
    p = {k: int(v) for k, v in RESUPPLY["pins"].items()}
    exact = Fraction(10 ** 36, p["price"])
    deployed = 10 ** 36 // p["price"]
    ltv = Fraction(p["borrowAmount"]) * exact * p["ltvPrecision"] / p["exchangePrecision"] / p["collateral"]
    times_cap = float(ltv / p["maxLTV"])
    dig = {re.match(r"FP\d+", r[0]).group(): r[2] for r in md_rows(BENCH / "replay-resupply.md", "FP")}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.0), gridspec_kw={"wspace": 0.45})
    names = ["deployed", "FP127", "FP256"]
    cols = [DEPLOYED, SERIES["FP127"], SERIES["FP256"]]
    vals = [deployed, float(exact), float(exact)]
    a1.bar(range(3), vals, color=cols, width=0.6, zorder=3)
    a1.axhline(float(exact), color=MUTED, lw=1.2, ls=(0, (4, 4)), zorder=2)
    a1.text(0, 0.03, "0", ha="center", fontsize=15, fontweight="bold")
    for x, n in ((1, "FP127"), (2, "FP256")):
        a1.text(x, float(exact) + 0.03, f"{dig[n]}\ndigits", ha="center", fontsize=12)
    a1.text(-0.42, float(exact) + 0.13, "the true rate: 0.4999999999999999999995", fontsize=12, color=MUTED)
    a1.set_xticks(range(3), names)
    a1.set_ylim(0, 0.75)
    a1.set_ylabel("rate, collateral per reUSD")
    a1.set_title("1e36 / price", fontsize=14, color=MUTED, loc="left")
    a1.grid(axis="x", visible=False)
    a2.bar([1, 2], [times_cap, times_cap], color=cols[1:], width=0.6, zorder=3)
    a2.axhline(1, color=MUTED, lw=1.4, ls=(0, (4, 4)))
    a2.text(-0.45, 0.85, "the cap (95%)", fontsize=12, color=MUTED, va="top", ha="left")
    a2.text(0, 2.0, "0:\nborrow\npasses", ha="center", va="bottom", fontsize=13, fontweight="bold")
    for x in (1, 2):
        a2.text(x, times_cap * 1.8, f"{times_cap:,.0f}×\nreverts", ha="center", fontsize=12)
    a2.set_yscale("log")
    a2.set_ylim(0.3, 1e9)
    a2.set_xlim(-0.5, 2.5)
    a2.set_xticks(range(3), names)
    a2.set_ylabel("loan-to-value, times the cap (log)")
    a2.set_title(f"1 wei of collateral, {p['borrowAmount'] / 1e18 / 1e6:,.0f}M reUSD borrowed",
                 fontsize=14, color=MUTED, loc="left")
    a2.grid(axis="x", visible=False)
    return svg(fig)


def _bunni():
    spec = importlib.util.spec_from_file_location("bunni_replay", REPLAYS / "bunni.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    d = json.loads((REPLAYS / "bunni.json").read_text())
    r = m.replay(d)
    return r, m.liquidity_table(d, r)


def plot_bunni() -> str:
    """1.3: the pool's active USDC over the 44 withdrawals, replayed from bunni.json."""
    r, liq = _bunni()
    seq = r["seq"]
    xs = list(range(len(seq["deployed"])))
    l0 = liq["start"]["L"]
    fig, ax = figure()
    ax.plot(xs, seq["deployed"], color=DEPLOYED, lw=2.5, drawstyle="steps-post", zorder=3, label="deployed (mulDiv)")
    ax.plot(xs, seq["mulDivUp"], color=FIX, lw=2.5, drawstyle="steps-post", zorder=3, label="the fix (mulDivUp)")
    ax.plot(xs, [float(v) for v in seq["exact"]], color=FAINT, lw=5, zorder=4, label="exact")
    ax.plot(xs, [float(v) for v in seq["fp127"]], color=SERIES["FP127"], lw=2, ls=(0, (5, 3)), zorder=5,
            label="FP127")
    x1 = xs[-1] + 0.8
    dl = lambda f: (liq[f]["L"] / l0 - 1) * 100  # noqa: E731
    ax.text(x1, seq["deployed"][-1], f"deployed  {seq['deployed'][-1]} wei\nliquidity {dl('deployed'):+.2f}%",
            va="center", fontsize=13)
    ax.text(x1, seq["mulDivUp"][-1], f"mulDivUp  {seq['mulDivUp'][-1]} wei", va="center", fontsize=13)
    ax.text(x1, float(seq["exact"][-1]), f"FP127, FP256, exact\n{float(seq['exact'][-1]):.4f} wei",
            va="center", fontsize=13)
    ax.set_xlim(0, xs[-1])
    ax.set_ylim(0, 55)
    ax.set_xlabel("withdrawals")
    ax.set_ylabel("the pool's active USDC (wei)")
    legend_below(ax, 4)
    return svg(fig)


BALANCER = json.loads((REPLAYS / "balancer.json").read_text())["score"]


def plot_balancer() -> str:
    """1.4: the true invariant D* across the osETH pool's micro-swap phase, each call charged by each model."""
    s = BALANCER["osETH"]
    models = [("deployed", "deployed (mulDown)", DEPLOYED, 2.5), ("mulUp", "the fix (mulUp)", FIX, 2.5),
              ("fp256", "FP256", SERIES["FP256"], 4), ("fp127", "FP127", SERIES["FP127"], 2)]
    fig, ax = figure()
    for m, lab, col, lw in models:
        ys, v = [1.0], 1.0
        for st in s["steps"]:
            v *= 1 + float(st["models"][m]["rel"])
            ys.append(v)
        ax.plot(range(len(ys)), ys, color=col, lw=lw, label=lab, zorder=5 if m == "fp127" else 4,
                ls=(0, (5, 3)) if m == "fp127" else "-")
    n = s["swaps"]
    x1 = n + 1.5
    mm = s["models"]
    ax.text(x1, float(mm["mulUp"]["invariantRatio"]),
            f"mulUp  ×{float(mm['mulUp']['invariantRatio']):.2f}\n{mm['mulUp']['stepsInvariantFalls']} of {n} calls lower D*",
            va="center", fontsize=13)
    ax.text(x1, float(mm["fp127"]["invariantRatio"]),
            f"FP127 = FP256 = exact  ×{float(mm['fp127']['invariantRatio']):.4f}\n"
            f"{mm['fp127']['stepsInvariantFalls']} of {n} calls lower D*", va="center", fontsize=13)
    ax.text(x1, float(mm["deployed"]["invariantRatio"]),
            f"deployed  ×{float(mm['deployed']['invariantRatio']):.3f}\n"
            f"{mm['deployed']['stepsInvariantFalls']} of {n} calls lower D*", va="center", fontsize=13)
    ax.set_yscale("log")
    ax.set_ylim(0.01, 20)
    ax.set_yticks([0.01, 0.1, 1, 10], ["×0.01", "×0.1", "×1", "×10"])
    ax.set_xlim(0, n)
    ax.set_xlabel(f"calls of the drain / micro / restore phase, osETH/WETH pool (swaps {s['firstSwap']}–{s['lastSwap']})")
    ax.set_ylabel("true invariant D*, against its start")
    legend_below(ax, 4)
    return svg(fig)


def plot_balancer_v1() -> str:
    """1.5: one join/exit cycle re-tuned to each rounding rule, in every pool (replay-balancer-v1.md)."""
    rows = md_rows(BENCH / "replay-balancer-v1.md", "")
    rows = [r for r in rows if r[0].isdigit() and len(r) == 5
            and (r[1].startswith("deployed (the attacker") or r[1].startswith("exact formula"))]
    rules = [("deployed", "deployed", DEPLOYED), ("nearest", "exact, rounded to nearest once", FIX),
             ("toward", "exact, rounded toward the pool once", SERIES["FP256"])]
    net = {k: [] for k, _, _ in rules}
    for r in rows:
        k = "deployed" if r[1].startswith("deployed") else "nearest" if "nearest" in r[1] else "toward"
        net[k].append(float(r[4].rstrip("%")))
    pools = list(range(1, len(net["deployed"]) + 1))
    fig, ax = figure()
    w = 0.26
    for i, (k, lab, col) in enumerate(rules):
        xs = [p + (i - 1) * w for p in pools]
        ax.bar(xs, net[k], width=w - 0.03, color=col, label=lab, zorder=3)
        for p, x, v in zip(pools, xs, net[k]):
            if k != "toward" and p != 1:
                continue
            ax.text(x, v + (0.12 if v >= 0 else -0.12), f"{v:.2f}" if abs(v) >= 0.1 else f"{v:.3f}",
                    ha="center", va="bottom" if v >= 0 else "top", fontsize=10, color=INK)
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks(pools, [f"pool {p}" for p in pools])
    ax.set_ylim(-1, 8.2)
    ax.set_ylabel("attacker's net per cycle, % of BPT supply")
    ax.grid(axis="x", visible=False)
    legend_below(ax, 3)
    return svg(fig)


# --- part 2: converge, or fit (slides 7-12) ----------------------------------------

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
FP256_WALL = math.floor((2**18) * math.log10(2))  # exponent 19 bits, bias 2^18 - 1: 10^±78,913


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
    ax.text(-44, FLOAT["FP256"] + 2.5, f"FP256: {FLOAT['FP256']:.1f} digits out to its walls at 10^±{FP256_WALL:,}",
            ha="left", fontsize=12, color=SERIES["FP256"])
    ax.set_xlabel("size of the number, power of ten")
    ax.set_ylabel("digits the ruler can hold")
    ax.set_xlim(-45, 45)
    ax.set_ylim(0, 80)
    ax.set_xticks(range(-40, 41, 10), [f"10^{k}" for k in range(-40, 41, 10)])
    legend_below(ax, 5)
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


def plot_newton() -> str:
    """2.3: Balancer's invariant solve, the same Newton iteration on three rulers (worst over the phase)."""
    rulers = [("deployed", "wei grid", DEPLOYED), ("fp127", "FP127", SERIES["FP127"]), ("fp256", "FP256", SERIES["FP256"])]
    fig, ax = figure(11.5, 5.0)
    y, ticks = 0, []
    for pool in ("osETH", "wstETH"):
        c = BALANCER[pool]["convergence"]
        for k, lab, col in rulers:
            d = c[k]["relD"]["minDigits"]
            ax.barh(y, d, color=col, height=0.7, zorder=3)
            ax.text(d + 0.8, y, f"{d:.1f} digits, median {c[k]['itD']['median']} iterations", va="center", fontsize=13)
            ticks.append((y, lab))
            y += 1
        ax.text(-14, y - 2, f"{pool}/WETH", ha="right", va="center", fontsize=14, fontweight="bold")
        y += 0.7
    ax.set_yticks([t[0] for t in ticks], [t[1] for t in ticks])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 80, 10))
    ax.set_xlabel("digits of the invariant D at the stop, worst call of the phase (against the exact root)")
    ax.grid(axis="y", visible=False)
    return svg(fig)


def converge_vs_fit() -> tuple[list[int], list[float], list[float]]:
    """At each word width, computed with mpmath at that precision: bits a Newton
    square root reaches (it runs until the step stops changing anything), and
    bits a Taylor polynomial for exp tuned once for 60 bits delivers (its
    truncation error does not shrink with the word)."""
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
            label="fitted: a Taylor polynomial for exp, tuned for 60 bits")
    ax.text(widths[-1] + 4, newton[-1], f"{newton[-1]:.0f} bits", va="center", fontsize=13)
    ax.text(widths[-1] + 4, fitted[-1], f"{fitted[-1]:.0f} bits", va="center", fontsize=13)
    ax.set_xlabel("bits in the word")
    ax.set_ylabel("bits right in the answer")
    ax.set_xlim(56, 280)
    ax.set_ylim(0, 270)
    ax.legend(loc="upper left", fontsize=12)
    return svg(fig)


def release_one() -> dict[str, int]:
    """Release one's worst bits (contracts/deployments/FP256.md): the converging ops
    were exact to the 237-bit significand; exp, ln and pow ran on fitted kernels."""
    text = (DEPLOY / "FP256.md").read_text()
    sec = text[text.index("## Release one"):]
    exp_, ln_, pow_ = (int(x) for x in re.search(r"\((\d+), (\d+) and (\d+) bits at worst", sec).groups())
    return {"add": 237, "sub": 237, "mul": 237, "div": 237, "sqrt": 237, "exp": exp_, "ln": ln_, "pow": pow_}


def plot_release() -> str:
    one = release_one()
    prec = json.loads((ROOT / "docs" / "fp256" / "precision.json").read_text())
    now = {op: (237 if prec[op]["minBits"] >= 256 else prec[op]["minBits"]) for op in one}
    exp_sweep = next(r for r in SWEEP["rows"] if r["lib"] == "fp256" and r["op"] == "exp")
    fig, ax = figure()
    ops = list(one)
    for x, op in enumerate(ops):
        a, b = one[op], now[op]
        ax.plot([x, x], [a, b], color=GRID, lw=3, zorder=2)
        ax.plot(x, a, "o", ms=13, color=MUTED, mec=SURFACE, mew=2, zorder=3,
                label="release one" if x == 0 else None)
        ax.plot(x, b, "o", ms=13, color=SERIES["FP256"], mec=SURFACE, mew=2, zorder=4,
                label="now" if x == 0 else None)
        if a != b:
            ax.text(x - 0.14, a, f"{a} bits\n{a * math.log10(2):.0f} digits", va="center", ha="right", fontsize=11)
    ax.axvspan(-0.5, 4.5, color=SERIES["FP256"], alpha=0.05, lw=0)
    ax.text(2, 185, "converging:\nexact on day one", ha="center", fontsize=14, color=INK)
    ax.text(6, 103, "fitted: had to be refit", ha="center", fontsize=14, color=INK)
    ax.text(6, 89, f"exp now: {exp_sweep['correctlyRounded']:,} of {exp_sweep['n']:,} random inputs correctly rounded",
            ha="center", fontsize=11, color=MUTED)
    ax.set_xticks(range(len(ops)), ops)
    ax.set_ylabel("worst bits right, FP256 (237 = exact)")
    ax.set_ylim(80, 250)
    ax.set_xlim(-0.5, len(ops) - 0.5)
    ax.grid(axis="x", visible=False)
    legend_below(ax, 2)
    return svg(fig)


# --- part 3: the last library (slides 13-18) -----------------------------------------

def plot_format_ceiling() -> str:
    """3.1: a 256-bit word with an e-bit exponent keeps 256 - e significand bits
    (sign bit out, hidden bit in); its range is about 2^±2^(e-1)."""
    es = list(range(8, 25))
    dig = lambda e: (256 - e) * math.log10(2)  # noqa: E731
    rng = lambda e: math.floor(2 ** (e - 1) * math.log10(2))  # noqa: E731
    fig, ax = figure()
    ax.axvspan(7.5, 8.5, color=GRID, lw=0, zorder=1)
    ax.text(8, 75.8, "too narrow\nfor uint256", ha="center", va="top", fontsize=11, color=MUTED)
    ax.plot(es, [dig(e) for e in es], color=MUTED, lw=2, zorder=3)
    marks = {9: "just covers uint256", 11: "", 13: "", 19: "FP256"}
    for e, note in marks.items():
        col = SERIES["FP256"] if e == 19 else MUTED
        ax.plot(e, dig(e), "o", ms=12, color=col, mec=SURFACE, mew=2, zorder=4)
        lab = f"{e} bits: {dig(e):.1f} digits, 10^±{rng(e):,}" + (f"\n{note}" if note else "")
        ax.annotate(lab, (e, dig(e)), xytext=(10, 12), textcoords="offset points", fontsize=12, color=INK)
    ax.axhline(dig(19), color=SERIES["FP256"], lw=1.2, ls=(0, (4, 4)), zorder=2)
    ax.annotate("", xy=(9.0, dig(9)), xytext=(9.0, dig(19)),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1.4))
    ax.text(9.25, (dig(9) + dig(19)) / 2, f"{dig(9) - dig(19):.1f} digits:\nthe most any\none-word format\ncan add",
            fontsize=12, color=MUTED, va="center")
    ax.set_xlim(7.5, 24.5)
    ax.set_ylim(69.5, 76)
    ax.set_xticks(es)
    ax.set_xlabel("exponent bits in a 256-bit word")
    ax.set_ylabel("digits of significand")
    return svg(fig)


def plot_accuracy() -> str:
    """3.2: FP256 against the correctly rounded word, seeded random inputs (sweep.json)."""
    rows = [r for r in SWEEP["rows"] if r["lib"] == "fp256" and "stage" not in r]
    wide = [r for r in SWEEP["rows"] if r["lib"] == "fp256" and r.get("stage") == "second"]
    fig, ax = figure(11.5, 5.4)
    for y, r in enumerate(rows):
        share = 100 * r["correctlyRounded"] / r["n"]
        ax.barh(y, share, color=SERIES["FP256"], height=0.72, zorder=3)
        ax.barh(y, 100 - share, left=share, color=SERIES["FP127"], height=0.72, zorder=3)
        note = f"{r['correctlyRounded']:,} / {r['n']:,}"
        if r["misrounded"]:
            note += f"   ({r['misrounded']:,} off, by up to {r['maxUlp']} mark{'s' if r['maxUlp'] > 1 else ''})"
        ax.text(101.5, y, note, va="center", fontsize=9, color=INK)
    ax.set_yticks(range(len(rows)), [r["op"] for r in rows], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 25), [f"{x}%" for x in range(0, 101, 25)])
    forced = sum(r["n"] for r in wide)
    off = sum(r["misrounded"] for r in wide)
    ax.set_xlabel("FP256: share of random inputs that return the correctly rounded word\n"
                  f"and {forced:,} more forced through the second stage of {len(wide)} ops: {off} misrounded")
    ax.grid(axis="y", visible=False)
    return svg(fig)


GAS_OPS = ["mul", "div", "exp", "ln", "pow"]


def gas_medians() -> dict[str, dict[str, int]]:
    """Median gas per op: Solady, PRBMath and FP127Lib from gas.md, FP256Lib from gas256.md."""
    def table(path, want):
        # the ladder table only: the file's first table (a typical-inputs table follows)
        text = path.read_text()
        block = text[text.index("\n|"):].split("\n\n")[0]
        lines = [l for l in block.splitlines() if l.startswith("|")]
        head = [c.strip() for c in lines[0].strip("|").split("|")]
        idx = {k: head.index(h) for k, h in want.items()}
        out = {k: {} for k in want}
        for l in lines[2:]:
            cells = [c.strip() for c in l.strip("|").split("|")]
            if cells[0] in GAS_OPS:
                for k, i in idx.items():
                    out[k][cells[0]] = int(cells[i].split("/")[1].strip().replace(",", ""))
        return out
    g = table(BENCH / "gas.md", {"Solady": "Solady", "PRBMath": "PRBMath SD59x18", "FP127": "FP127Lib (inline)"})
    g.update(table(BENCH / "gas256.md", {"FP256": "FP256Lib (inline)"}))
    return g


def plot_gas() -> str:
    g = gas_medians()
    libs = [("Solady", SERIES["WAD"]), ("PRBMath", WAD_DARK), ("FP127", SERIES["FP127"]), ("FP256", SERIES["FP256"])]
    fig, ax = figure()
    w = 0.2
    for i, (lib, col) in enumerate(libs):
        xs = [k + (i - 1.5) * w for k in range(len(GAS_OPS))]
        vs = [g[lib][op] for op in GAS_OPS]
        ax.bar(xs, vs, width=w - 0.02, color=col, label=lib, zorder=3)
        for x, v in zip(xs, vs):
            ax.text(x, v * 1.08, f"{v:,}", ha="center", va="bottom", fontsize=9.5, rotation=90, color=INK)
    ax.set_yscale("log")
    ax.set_ylim(50, 60000)  # Solady's div is 93: the floor sits below every bar
    ax.set_yticks([100, 1000, 10000], ["100", "1,000", "10,000"])
    ax.set_xticks(range(len(GAS_OPS)), GAS_OPS)
    ax.set_ylabel("median gas per op, inline (log scale)")
    ax.grid(axis="x", visible=False)
    legend_below(ax, 4)
    return svg(fig)


def plot_live() -> str:
    # The recorded totals are the cells livecap actually called. Counting only the
    # cells at or below each form's liveMaxN gives 9,298 rather than 9,373: liveMaxN
    # is the minimum over a form's inputs, and inputs that climbed past it were
    # checked too (#95). The record is right; the per-form rebuild undercounts.
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
    # FP256's other objects, smaller: the elementary, hyperbolic and special functions
    extra = [k for k in ("FP256E", "FP256H", "FP256S") if k in c]
    if extra:
        ax.text(0, 0.135, "  ·  ".join(f'{k} {c[k]["address"][:10]}…{c[k]["address"][-4:]}' for k in extra),
                fontsize=11.5, family="DejaVu Sans Mono", color=MUTED, transform=ax.transAxes)
    ax.text(0, -0.02, "blockulator.com  ·  github.com/securedataresearch/blockulator", fontsize=15, color=MUTED,
            transform=ax.transAxes)
    return svg(fig)


# --- the deck -----------------------------------------------------------------

PI = "Ramanujan's series through each library's own sqrt, mul and div. docs/benchmarks/pi.md"
WAD_NOTE = "WAD = an 18-decimal library; 64.64 and binary128 = the two ABDK formats."
FORMATS = "Exact properties of each format, computed in scripts/talk/deck.py."

SLIDES = [
    ("Dust is Over", plot_title, "$10,000 at 10%, compounded daily on an 18-decimal ruler. docs/benchmarks/ladder.json: compound"),
    # part 1: real failures
    ("One honest transaction", plot_honest,
     "Aave v3 USDC borrow, 1M USDC at 100% utilisation, untouched a day; the deployed code against the formula at 200 digits. "
     "docs/benchmarks/accrual-deployed.json: aave-usdc-u100-borrow-1d"),
    ("Resupply, 26 June 2025", plot_resupply,
     "Tx 0xffbbd492…, block 22,785,461: the pinned integers, the same formula on each ruler. "
     "scripts/replays/resupply.json; docs/benchmarks/replay-resupply.md"),
    ("Bunni v2, 2 September 2025", plot_bunni,
     "Tx 0x1c27c4d6…, block 23,273,098: the 44 withdrawals replayed from the trace, only the stored idle balance changed. "
     "scripts/replays/bunni.json (bunni.py replay); docs/benchmarks/replay-bunni.md"),
    ("Balancer V2, 3 November 2025", plot_balancer,
     "Tx 0x6ed07db1…, block 23,717,397: every call priced on its own on-chain balances; D* solved exactly. "
     "scripts/replays/balancer.json (score.osETH); docs/benchmarks/replay-balancer.md"),
    ("Balancer V1, 31 August 2026", plot_balancer_v1,
     "Five pools; from each pool's first join at 3 units, one join/exit cycle re-tuned to each rule at 200 digits. "
     "docs/benchmarks/replay-balancer-v1.md: Precision or direction?"),
    # part 2: converge, or fit
    ("Goal one: round once", plot_goal_one, "A year of daily compounding, $10,000 at 10%. docs/benchmarks/ladder.json. " + WAD_NOTE),
    ("Goal two: never run out of ruler", plot_rulers, FORMATS),
    ("Ramanujan", plot_ramanujan, PI),
    ("Balancer's Newton solve, three rulers", plot_newton,
     "StableMath's invariant iteration on each ruler, residual against the exact root at 200 digits. "
     "scripts/replays/balancer.json (score.*.convergence); docs/benchmarks/replay-balancer.md: Newton convergence"),
    ("Converge, or fit", plot_converge,
     "Computed with mpmath at each width: Newton's sqrt(2), and a Taylor polynomial for exp tuned for 60 bits "
     "(the shortest within 2^-60 on [0, ln 2]), at x = ln 2. scripts/talk/deck.py: converge_vs_fit"),
    ("Release one, and now", plot_release,
     "Worst bits over the committed vectors. Release one: contracts/deployments/FP256.md; now: docs/fp256/precision.json "
     "(precision.md) and docs/benchmarks/sweep.json"),
    # part 3: the last library
    ("The format ceiling", plot_format_ceiling,
     "A 256-bit word: sign, e exponent bits, 256 − e significand bits with the hidden bit; range 2^±2^(e−1). "
     "Computed in scripts/talk/deck.py: plot_format_ceiling"),
    ("The accuracy ceiling", plot_accuracy,
     "Seeded random inputs against the correctly rounded word (300 digits, ties away from zero). "
     "docs/benchmarks/sweep.json (sweep.md)"),
    ("What it costs", plot_gas,
     "Median gas over each op's input ladder, inline libraries. docs/benchmarks/gas.md (Solady, PRBMath SD59x18, FP127Lib); "
     "docs/benchmarks/gas256.md (FP256Lib)"),
    ("Both goals, met", lambda: plot_rulers(lit=("FP127", "FP256")), FORMATS),
    ("Checked on chain", plot_live, "contracts/deployments/RELEASE.json"),
    ("Use FP127 and FP256", plot_close, f"{RELEASE['release']}. Sepolia; CLZ (Osaka) required; MIT licence. contracts/deployments/RELEASE.json"),
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

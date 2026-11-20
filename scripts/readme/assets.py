"""README assets, every number read from the committed datasets.

    make readme-assets        # docs/img/digits-{light,dark}.svg and the generated README blocks
    uv run scripts/readme/assets.py --check   # fail if any of them is stale

Writes the home page's accrual chart (correct digits against days without an update, from
docs/benchmarks/ladder.json) as an SVG for each GitHub theme, and rewrites the README between
its <!-- name:begin --> / <!-- name:end --> markers: the badges and the gas-with-digits
table (gas.json, gas19.json). Our libraries come
first in every table. Stdlib only.
"""
import glob
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "docs" / "benchmarks"
README = ROOT / "README.md"
IMG = ROOT / "docs" / "img"
REPO = "securedataresearch/blockulator"

# precision at 1, as the site's pitch table (templates/components.html pitch)
# precision at 1, in decimal digits; floating point first, then fixed point
DIGITS = {"bl19": 71, "quad": 34, "bl127": 38, "abdk": 19, "prb": 18, "prbud": 18, "solady": 18, "solmate": 18,
          "balancer": 18, "snekmate": 18, "oz": 18}
NAMES = {"bl19": "BL19", "bl127": "BL127", "quad": "ABDKMathQuad", "abdk": "ABDKMath64x64", "prb": "PRBMath SD59x18",
         "prbud": "PRBMath UD60x18", "solady": "Solady", "solmate": "Solmate", "balancer": "Balancer LogExpMath",
         "snekmate": "snekmate", "oz": "OpenZeppelin Math"}
FLOAT, FIXED = ("bl19", "quad"), ("bl127", "abdk", "prb", "prbud", "solady", "solmate", "balancer", "snekmate", "oz")
OPS = ["add", "mul", "div", "exp", "ln", "pow", "sqrt"]

# the site's family colours (static/css/site.css), light and dark
THEMES = {
    "light": dict(text="#1b1c1c", strong="#0b0c0c", faint="#5f615e", grid="#e3e4e0", bl127="#00694e", bl19="#0b0c0c",
                  quad="#8a4f7d", wad="#8f8750", warn="#c4402c", bg="#ffffff"),
    "dark": dict(text="#e2e3df", strong="#f6f6f3", faint="#9a9d97", grid="#2a2e33", bl127="#43b592", bl19="#f6f6f3",
                 quad="#d08ac0", wad="#d3c68a", warn="#ff7a5c", bg="#0d1117"),
}


def load(p):
    return json.loads(Path(p).read_text())


def floor(x):
    return int(math.floor(float(x)))


# ---- the chart ---------------------------------------------------------------------------

def chart(theme):
    c = THEMES[theme]
    d = load(B / "ladder.json")
    sc = next(s for s in d["scenarios"] if s["id"] == "accrual-continuous")
    cells = sc["inputs"][0]["cells"]
    ladder, lg = d["ladder"], d["ladderLog10"]
    W, H, L, R, T, Bm, cap = 820, 380, 40, 170, 50, 44, 72
    pw, ph = W - L - R, H - T - Bm
    X = lambda n: L + pw * float(lg[str(n)]) / 4
    Y = lambda v: T + ph - ph * min(float(v), cap) / cap
    font = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{font}">']
    o.append("<defs>" + "".join(
        f'<linearGradient id="g{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c[k]}" stop-opacity="{.10 if k == "bl19" else .22}"/>'
        f'<stop offset="1" stop-color="{c[k]}" stop-opacity="0"/></linearGradient>' for k in ("bl19", "bl127", "warn")) + "</defs>")
    o.append(f'<text x="{L}" y="22" font-size="17" font-weight="600" fill="{c["strong"]}">Leave a market alone and its interest goes wrong</text>')
    o.append(f'<text x="{L}" y="40" font-size="12.5" fill="{c["faint"]}">Correct digits of $10,000 at 5% APR, accrued in one step after N days without an update</text>')
    for g in (0, 18, 36, 54, 72):
        o.append(f'<line x1="{L}" x2="{L + pw}" y1="{Y(g)}" y2="{Y(g)}" stroke="{c["grid"]}"/>'
                 f'<text x="{L - 7}" y="{Y(g) + 4}" font-size="11.5" text-anchor="end" fill="{c["faint"]}">{g}</text>')
    for n in (1, 10, 100, 1000, 10000):
        o.append(f'<text x="{X(n)}" y="{H - 24}" font-size="11.5" text-anchor="middle" fill="{c["faint"]}">{n:,}</text>')
    o.append(f'<text x="{L + pw / 2}" y="{H - 6}" font-size="11.5" text-anchor="middle" fill="{c["faint"]}">days since the last update, log scale</text>')
    o.append(f'<line x1="{X(365)}" x2="{X(365)}" y1="{T}" y2="{T + ph}" stroke="{c["faint"]}" stroke-dasharray="2 3"/>'
             f'<text x="{X(365) + 5}" y="{T + ph * .36}" font-size="11.5" fill="{c["faint"]}">1 year</text>')

    def series(forms):
        lo, hi = [], []
        for n in ladder:
            v = [float(cells[f][str(n)]["digitsCapped"]) for f in forms if cells.get(f) and "digitsCapped" in cells[f][str(n)]]
            if v:
                lo.append((X(n), Y(min(v)), min(v), n)); hi.append((X(n), Y(max(v)), max(v), n))
        return lo, hi

    pts = lambda s: " ".join(f"{x:.1f},{y:.1f}" for x, y, *_ in s)
    labels = []
    # the WAD libraries and 64.64 as one band, the protocols as one line with its area
    lo, hi = series(["solady", "prb", "balancer", "abdk"])
    o.append(f'<polygon points="{pts(hi)} {pts(lo[::-1])}" fill="{c["wad"]}" opacity=".3"/>')
    o.append(f'<polyline points="{pts(lo)}" fill="none" stroke="{c["wad"]}" stroke-width="2"/>')
    labels.append(((lo[-1][1] + hi[-1][1]) / 2, f"WAD libraries, 64.64 {floor(lo[-1][2])}", c["wad"]))
    lo, _ = series(["aave", "morpho"])
    o.append(f'<polygon points="{pts(lo)} {L + pw},{T + ph} {L},{T + ph}" fill="url(#gwarn)"/>')
    o.append(f'<polyline points="{pts(lo)}" fill="none" stroke="{c["warn"]}" stroke-width="2.5"/>')
    yr = next(p for p in lo if p[3] == 365)
    o.append(f'<circle cx="{yr[0]}" cy="{yr[1]}" r="4.5" fill="{c["warn"]}" stroke="{c["bg"]}" stroke-width="2"/>'
             f'<text x="{yr[0] - 8}" y="{yr[1] + 19}" font-size="12.5" font-weight="600" text-anchor="end" fill="{c["warn"]}">{floor(yr[2])} digits after a year</text>')
    labels.append((lo[-1][1], f"Aave, Morpho {floor(lo[-1][2])}", c["warn"]))
    for f, name in (("quad", "binary128"), ("bl127", "BL127"), ("bl19", "BL19")):
        s, _ = series([f])
        ours = f in ("bl127", "bl19")
        if ours:
            o.append(f'<polygon points="{pts(s)} {L + pw},{T + ph} {L},{T + ph}" fill="url(#g{f})"/>')
        dash = '' if ours else ' stroke-dasharray="4 2"'
        o.append(f'<polyline points="{pts(s)}" fill="none" stroke="{c[f]}" stroke-width="{3.25 if ours else 2}" stroke-linejoin="round"{dash}/>')
        labels.append((s[-1][1], f"{name} {floor(s[-1][2])}", c[f]))
    # end labels, top-down, at least 15 px apart
    prev = -1e9
    for y, text, col in sorted(labels):
        y = max(y + 4, prev + 15); prev = y
        o.append(f'<text x="{L + pw + 8}" y="{y:.1f}" font-size="13" font-weight="600" fill="{col}">{text}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ---- the README blocks -------------------------------------------------------------------

def median(g, op, form):
    o = g["ops"].get(op)
    if not o:
        return None
    sm = (o.get("typical") or o)["summary"]
    return sm[form]["median"] if sm.get(form) else None


def gas_block():
    g127, g19 = load(B / "gas.json"), load(B / "gas19.json")
    src = {"bl19": (g19, "lib"), "quad": (g19, "quad")} | {l: (g127, "lib" if l == "bl127" else l) for l in FIXED}
    m = {lib: {op: median(g, op, f) for op in OPS} for lib, (g, f) in src.items()}
    m = {lib: v for lib, v in m.items() if any(v.values())}
    typ = {op for op in OPS if "typical" in g127["ops"][op]}
    head = "| | digits | " + " | ".join(op + ("<sup>t</sup>" if op in typ else "") for op in OPS) + " |"
    rows = [head, "|---|---:|" + "---:|" * len(OPS)]
    for group, libs in (("floating point", FLOAT), ("fixed point", FIXED)):
        rows.append(f"| *{group}* |" + " |" * (len(OPS) + 1))
        for lib in (l for l in libs if l in m):
            ours = lib in ("bl19", "bl127")
            b = (lambda s: f"**{s}**") if ours else (lambda s: s)
            cells = [b(f"{m[lib][op]:,}") if m[lib][op] is not None else "" for op in OPS]
            rows.append(f"| {b(NAMES[lib])} | {b(str(DIGITS[lib]))} | " + " | ".join(cells) + " |")

    shared = lambda a, b: [op for op in OPS if m[a][op] and m[b][op]]
    # cheaper means at least 2% less: the inline figures are good to about 1 or 2 percent
    won = lambda a, b: [op for op in shared(a, b) if m[a][op] * 100 < m[b][op] * 98]
    lost = lambda a, b: [op for op in shared(a, b) if m[b][op] * 100 < m[a][op] * 98]
    tied = lambda a, b: [op for op in shared(a, b) if op not in won(a, b) and op not in lost(a, b)]
    say = lambda xs: ", ".join(xs[:-1]) + (" and " if len(xs) > 1 else "") + (xs[-1] if xs else "")
    code = lambda ops: say([f"`{x}`" for x in ops])

    def wins(a, b):
        w, s, t, l = won(a, b), shared(a, b), tied(a, b), lost(a, b)
        if w == s:
            return "every op here"
        return code(w) + (f", about the same on {code(t)}" if t else "") + (f", and dearer on {code(l)}" if l else "")

    others = [l for l in FIXED[1:] if l in m]
    always = [NAMES[l] for l in others if won("bl127", l) == shared("bl127", l)]
    # BL127 cheaper on more ops than the other library is, but not on all; and the reverse
    mostly = [f"{NAMES[l]} on {wins('bl127', l)}" for l in others
              if won("bl127", l) != shared("bl127", l) and len(won("bl127", l)) > len(lost("bl127", l))]
    cheaper = [NAMES[l] for l in others if len(won("bl127", l)) <= len(lost("bl127", l))]
    common = shared("bl19", "quad")
    mean = {l: sum(m[l][op] for op in common) / len(common) for l in ("bl19", "quad")}
    text = (f"Median gas per inline call, over 100 random inputs that take no shortcut (<sup>t</sup>) or the op's input ladder, good to about 1 or 2 percent; digits are precision at 1. "
            f"BL19 is cheaper than ABDKMathQuad on {wins('bl19', 'quad')}, and over these {len(common)} ops carries "
            f"{DIGITS['bl19'] / DIGITS['quad']:.1f}× its digits at {round(100 * mean['bl19'] / mean['quad'])}% of its mean gas. "
            f"BL127 carries twice the digits of every fixed-point library here. "
            + (f"It is cheaper than {say(always)} on every op they share. " if always else "")
            + "".join(f"It is cheaper than {x}. " for x in mostly)
            + (f"{say(cheaper)} {'are' if len(cheaper) > 1 else 'is'} cheaper on most ops, at 18 digits; Solady's `add` is the unchecked `rawAdd`." if cheaper else ""))
    return "\n".join(rows) + "\n\n" + text


def badges_block():
    p = load(B / "proofs.json")
    proven = sum(1 for o in p["ops"] if o["status"] == "proven")
    n = sum(len(re.findall(r"function\s+(?:test|invariant)\w*\s*\(", Path(f).read_text()))
            for f in glob.glob(str(ROOT / "test" / "**" / "*.sol"), recursive=True))
    q = lambda s: s.replace("-", "--").replace(" ", "%20").replace(",", "%2C")
    return " ".join([
        f"[![CI](https://github.com/{REPO}/actions/workflows/ci.yml/badge.svg)](https://github.com/{REPO}/actions/workflows/ci.yml)",
        f"[![proofs](https://img.shields.io/badge/proofs-{q(f'{proven} ops proven')}-00694e)](docs/proofs.md)",
        f"[![tests](https://img.shields.io/badge/tests-{q(f'{n} forge tests')}-3f6d9c)](test)",
        "[![licence](https://img.shields.io/badge/licence-MIT-525252)](LICENSE)",
    ])


def splice(text, name, body):
    pat = re.compile(rf"(<!-- {name}:begin -->\n).*?(<!-- {name}:end -->)", re.S)
    if not pat.search(text):
        sys.exit(f"README.md has no <!-- {name}:begin/end --> markers")
    return pat.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)


def main():
    check = "--check" in sys.argv
    out = {IMG / f"digits-{t}.svg": chart(t) for t in THEMES}
    text = README.read_text()
    for name, body in (("badges", badges_block()), ("gas", gas_block())):
        text = splice(text, name, body)
    out[README] = text
    stale = [p for p, s in out.items() if not p.exists() or p.read_text() != s]
    if check:
        if stale:
            sys.exit("stale (run make readme-assets): " + ", ".join(str(p.relative_to(ROOT)) for p in stale))
        print("README assets are current")
        return
    IMG.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.write_text(out[p])
        print("wrote", p.relative_to(ROOT))


if __name__ == "__main__":
    main()

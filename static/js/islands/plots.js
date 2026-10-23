// The home page's charts, one per section, drawn from static/data/home.json, the same rows the
// tables under them are rendered from (scripts/site/home.py). Observable Plot, pinned.
// Colour is the library's family (blockulator.css --c-<family>); identity is the label, on the
// axis or on hover. Floating point is ◆, fixed point ●, or above and below a rule. Every chart has
// axis titles with units and a key.
import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.16/+esm";

const KINDS = [["float", "Floating point"], ["fixed", "Fixed point"]];
const FAMILIES = [["fp19", "FP19"], ["fp127", "FP127 · BlockulatorWad"], ["quad", "binary128 (ABDKMathQuad)"], ["6464", "ABDK 64.64"], ["wad", "WAD libraries"], ["protocol", "Maker, Aave, Morpho, FraxLend, Euler"]];
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

let data, lib;

const theme = () => ({ text: css("--text"), faint: css("--faint"), line: css("--line-2"), family: (f) => css(`--c-${f}`) });
const colour = (t) => (d) => t.family(lib[d.lib].family);
const label = (id) => lib[id].label;
const fmt = (n) => n.toLocaleString("en-US");
const symbol = (d) => (lib[d.lib].kind === "float" ? "diamond2" : "circle");
const ours = (d) => !!lib[d.lib].ours;

function base(t, width, extra) {
  return { width, style: { background: "transparent", color: t.text, fontFamily: css("--sans"), fontSize: "12px", overflow: "visible" }, ...extra };
}

// the key: the families this chart draws, then the two symbols
function key(el, t, ids, symbols = true) {
  const fams = new Set(ids.map((id) => lib[id].family));
  const p = document.createElement("p");
  p.className = "plotlegend";
  p.innerHTML = FAMILIES.filter(([f]) => fams.has(f)).map(([f, n]) => `<span><i style="background:${t.family(f)}"></i>${n}</span>`).join("") +
    (symbols ? `<span class="sym">◆ floating point</span><span class="sym">● fixed point</span>` : "");
  el.append(p);
}

const charts = {
  // the trade-off in one picture: digits against gas, each library's gas as a multiple of FP127's on the same ops
  // (the geometric mean over the ops both offer; the range over them is in the tip)
  gas(el, t, width) {
    const g = data.gas;
    const ref = new Map(g.rows.filter((r) => r.lib === "fp127").map((r) => [r.op, r.gas]));
    const per = g.rows.filter((r) => ref.has(r.op)).map((r) => ({ ...r, ratio: r.gas / ref.get(r.op) }));
    const pts = [...new Set(per.map((r) => r.lib))].map((id) => {
      const rs = per.filter((r) => r.lib === id);
      const gm = Math.exp(rs.reduce((s, r) => s + Math.log(r.ratio), 0) / rs.length);
      return { lib: id, ratio: gm, lo: Math.min(...rs.map((r) => r.ratio)), hi: Math.max(...rs.map((r) => r.ratio)), digits: lib[id].digits, ops: rs.length };
    });
    // labels sit just above their dots; where a name would run into one already placed on its level of digits,
    // it takes the lowest free row above (4.5 digits each), with a leader line back to its dot
    const [lo, hi] = [0.15, 6], plotW = width - 52 - 30;
    const px = (r) => ((Math.log(r) - Math.log(lo)) / (Math.log(hi) - Math.log(lo))) * plotW;
    const rows = new Map();
    for (const p of [...pts].sort((a, b) => a.ratio - b.ratio)) {
      const band = Math.round(p.digits / 6), ends = rows.get(band) || [];
      const x = px(p.ratio), k = ends.findIndex((e) => e < x - 2);
      const row = k < 0 ? ends.length : k;
      ends[row] = x + 6 + 6.6 * label(p.lib).length;
      rows.set(band, ends);
      p.ly = p.digits + 2.2 + 4.5 * row;
    }
    el.append(Plot.plot(base(t, width, {
      height: 480, marginLeft: 52, marginRight: 30, marginBottom: 44, marginTop: 30,
      x: { type: "log", domain: [lo, hi], label: "gas per call, as a multiple of FP127's on the same ops (log scale) →", tickFormat: (v) => v + "×", ticks: [0.2, 0.3, 0.5, 1, 2, 3, 5] },
      y: { domain: [0, 76], label: "↑ decimal digits at 1", grid: true },
      marks: [
        Plot.ruleX([1], { stroke: t.faint, strokeDasharray: "3 3" }),
        Plot.text([{ x: 1, y: 75 }], { x: "x", y: "y", text: () => "FP127's gas", dx: 5, textAnchor: "start", fill: t.faint }),
        Plot.dot(pts.filter((d) => !ours(d)), { x: "ratio", y: "digits", fill: colour(t), r: 8, stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
        Plot.dot(pts.filter(ours), { x: "ratio", y: "digits", fill: colour(t), r: 10.5, stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
        Plot.link(pts.filter((d) => d.ly - d.digits > 3), { x1: "ratio", y1: "digits", x2: "ratio", y2: (d) => d.ly - 0.8, stroke: t.faint, strokeWidth: 0.8 }),
        Plot.text(pts, { x: "ratio", y: "ly", text: (d) => label(d.lib), dx: 5, textAnchor: "start", fill: t.text, fontWeight: (d) => (ours(d) ? 700 : 500) }),
        Plot.tip(pts, Plot.pointer({ x: "ratio", y: "digits", title: (d) => `${lib[d.lib].long}\n${d.digits} digits at 1\ngas ${d.ratio.toFixed(2)}× FP127's (geometric mean over ${d.ops} ops; ${d.lo.toFixed(2)}–${d.hi.toFixed(2)}×)` })),
      ],
    })));
    key(el, t, pts.map((p) => p.lib));
  },

  accrual(el, t, width) {
    const a = data.accrual;
    const last = a.n[a.n.length - 1];
    // end labels: ours, binary128 and 64.64 by name, the rest by family, nudged at least 4.5 digits apart
    const groups = new Map();
    for (const r of a.rows.filter((r) => r.n === last)) {
      const l = lib[r.lib];
      const k = l.ours || l.family === "quad" || l.family === "6464" ? r.lib : l.family;
      const g = groups.get(k) || { names: [], ys: [], lib: r.lib };
      g.names.push(l.label); g.ys.push(r.digits); groups.set(k, g);
    }
    const labels = [...groups.entries()].map(([k, g]) => ({
      lib: g.lib, y: g.ys.reduce((s, v) => s + v, 0) / g.ys.length,
      text: `${k === "wad" ? `WAD libraries (${g.names.length})` : g.names.join(", ")}: ${Math.floor(Math.min(...g.ys))}`,
    })).sort((p, q) => q.y - p.y);
    for (let i = 1; i < labels.length; i++) labels[i].y = Math.min(labels[i].y, labels[i - 1].y - 4.5);
    el.append(Plot.plot(base(t, width, {
      height: 400, marginRight: 210, marginLeft: 48, marginBottom: 42,
      x: { type: "log", domain: [1, last], label: "days since the last update (log scale) →", ticks: a.cols, tickFormat: fmt },
      y: { domain: [0, 76], label: "↑ correct decimal digits", grid: true },
      marks: [
        Plot.line(a.rows, { x: "n", y: "digits", z: "lib", stroke: colour(t), strokeWidth: (d) => (ours(d) ? 3 : 1.6), strokeOpacity: (d) => (ours(d) ? 1 : 0.8), curve: "monotone-x" }),
        Plot.dot(a.rows.filter((r) => r.n === last), { x: "n", y: "digits", fill: colour(t), r: 6, symbol }),
        Plot.text(labels, { x: last, y: "y", text: "text", dx: 10, textAnchor: "start", fill: colour(t), fontWeight: 600 }),
        Plot.tip(a.rows, Plot.pointer({ x: "n", y: "digits", title: (d) => `${lib[d.lib].long}\nafter ${fmt(d.n)} ${d.n === 1 ? "day" : "days"}: ${d.digits.toFixed(1)} correct digits` })),
      ],
    })));
    key(el, t, [...new Set(a.rows.map((r) => r.lib))]);
  },

  // one row per function, one dot per library at its share of results off by a wei; equal shares stack apart
  wad(el, t, width) {
    const w = data.wad;
    const rows = w.rows.map((r) => ({ ...r, kind: lib[r.lib].ours ? "ours" : "other" }));
    el.append(Plot.plot(base(t, width, {
      height: w.functions.length * 40 + 70, marginLeft: 116, marginRight: 30, marginBottom: 44, marginTop: 10,
      fy: { domain: w.functions, label: null, padding: 0 },
      x: { domain: [-2, 102], ticks: [0, 25, 50, 75, 100], tickFormat: (v) => v + "%", label: "share of results off by ≥ 1 wei →", grid: true },
      marks: [
        Plot.frame({ anchor: "bottom", stroke: t.line, strokeOpacity: 0.5 }),
        Plot.dot(rows, Plot.dodgeY("middle", { fy: "fn", x: "pct", r: 7.5, fill: colour(t), stroke: "var(--surface-solid)", strokeWidth: 1.5, padding: 1.5 })),
        Plot.tip(rows, Plot.pointer({ fy: "fn", x: "pct", title: (d) => `${lib[d.lib].long}\n${d.fn}: ${fmt(d.wrong)} of ${fmt(d.n)} results off by a wei or more (${d.pct}%)` })),
      ],
    })));
    key(el, t, [...new Set(rows.map((r) => r.lib))], false);
  },

  ladder(el, t, width) {
    const ld = data.ladder;
    const rows = ld.rows.filter((r) => r.digits != null).map((r) => ({ ...r, title: ld.scenarios.find((s) => s.id === r.scenario).title }));
    el.append(Plot.plot(base(t, width, {
      height: 32 * ld.scenarios.length + 60, marginLeft: 280, marginRight: 16, marginBottom: 42,
      x: { domain: [0, 76], label: "median correct decimal digits after the last step →", grid: true },
      y: { domain: ld.scenarios.map((s) => s.title), label: null, tickSize: 0 },
      marks: [
        Plot.ruleY(ld.scenarios.map((s) => s.title), { stroke: t.line, strokeOpacity: 0.5 }),
        Plot.dot(rows.filter((d) => !ours(d)), { x: "digits", y: "title", fill: colour(t), r: 6, fillOpacity: 0.9, symbol }),
        Plot.dot(rows.filter(ours), { x: "digits", y: "title", fill: colour(t), r: 8, stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
        Plot.tip(rows, Plot.pointer({ x: "digits", y: "title", title: (d) => `${lib[d.lib].long}\n${d.title}: ${d.digits.toFixed(1)} digits after ${fmt(d.n)} steps` })),
      ],
    })));
    key(el, t, [...new Set(rows.map((r) => r.lib))]);
  },

  // one bar per library over the probes: to the left of zero the ones it fails (to zero, reverts, out of range,
  // no correct digit), to the right the ones it computes, by how many digits it keeps
  edges(el, t, width) {
    const e = data.edges;
    const CATS = [["range", "out of range"], ["reverts", "reverted"], ["zero", "went to zero"], ["wrong", "no correct digit"],
                  ["d1", "1–9 digits"], ["d10", "10–17"], ["d18", "18–29"], ["d30", "30 or more"]];
    const red = css("--red"), em = css("--emerald");
    const fill = { range: red, reverts: red, zero: red, wrong: red, d1: em, d10: em, d18: em, d30: em };
    const op = { range: 0.95, reverts: 0.7, zero: 0.45, wrong: 0.25, d1: 0.25, d10: 0.45, d18: 0.7, d30: 0.95 };
    const ids = KINDS.flatMap(([k]) => data.libraries.filter((l) => l.kind === k && e.rows.some((r) => r.lib === l.id)).map((l) => l.id));
    const segs = e.rows.flatMap((r) => {
      const ds = r.digits, nz = ds.filter((d) => d === 0).length - r.zero;
      const c = { range: r.range, reverts: r.reverts, zero: r.zero, wrong: nz, d1: ds.filter((d) => d >= 1 && d < 10).length,
                  d10: ds.filter((d) => d >= 10 && d < 18).length, d18: ds.filter((d) => d >= 18 && d < 30).length, d30: ds.filter((d) => d >= 30).length };
      return CATS.map(([k, name], i) => ({ lib: r.lib, k, name, i, n: i < 4 ? -c[k] : c[k], count: c[k], unsupported: r.unsupported }));
    }).filter((d) => d.count);
    const lastFloat = ids.filter((id) => lib[id].kind === "float").pop();
    el.append(Plot.plot(base(t, width, {
      height: 26 * ids.length + 80, marginLeft: 120, marginRight: 30, marginBottom: 44,
      x: { label: "← probes it fails · probes it computes, by correct digits →", tickFormat: (v) => Math.abs(v), grid: true },
      y: { domain: ids, label: null, tickFormat: label, tickSize: 0, padding: 0.22 },
      marks: [
        Plot.barX(segs, { y: "lib", x: "n", fill: (d) => fill[d.k], fillOpacity: (d) => op[d.k], order: "i", inset: 0.5 }),
        Plot.ruleX([0], { stroke: t.text, strokeWidth: 1.2 }),
        Plot.ruleY([lastFloat], { dy: 13, stroke: t.line }),
        Plot.tip(segs, Plot.pointer({ y: "lib", x: "n", title: (d) => `${lib[d.lib].long}\n${d.count} probes: ${d.name}${d.unsupported ? `\n(${d.unsupported} more: no such op)` : ""}` })),
      ],
    })));
    const p = document.createElement("p");
    p.className = "plotlegend";
    p.innerHTML = CATS.map(([k, n]) => `<span><i style="background:${fill[k]};opacity:${op[k]}"></i>${n}</span>`).join("") +
      `<span class="sym">floating point above the line, fixed point below</span>`;
    el.append(p);
  },
};

// every dot bursts: it pops in once when its chart first draws (staggered left to right), and on hover it
// swells with a halo in its own colour when the pointer is nearest it (blockulator.css .plot .dotm)
function burst(el, first) {
  const dots = [...el.querySelectorAll('g[aria-label="dot"] > *')];
  const xs = dots.map((d) => d.getBBox().x), x0 = Math.min(...xs), x1 = Math.max(...xs) || 1;
  dots.forEach((d, i) => {
    d.classList.add("dotm");
    d.style.setProperty("--dc", d.getAttribute("fill") || d.parentNode.getAttribute("fill"));
    if (first) d.style.setProperty("--delay", `${Math.round(((xs[i] - x0) / (x1 - x0 || 1)) * 420)}ms`);
    else d.style.animation = "none";
  });
  // the halo follows the pointer to the nearest dot within 24px, as the tip does
  let hot;
  el.onpointermove = (e) => {
    let best, bd = 24 * 24;
    for (const d of dots) {
      const r = d.getBoundingClientRect(), dx = r.x + r.width / 2 - e.clientX, dy = r.y + r.height / 2 - e.clientY;
      if (dx * dx + dy * dy < bd) { bd = dx * dx + dy * dy; best = d; }
    }
    if (best !== hot) { hot?.classList.remove("hot"); best?.classList.add("hot"); hot = best; }
  };
  el.onpointerleave = () => { hot?.classList.remove("hot"); hot = undefined; };
}

function draw() {
  const t = theme();
  for (const el of document.querySelectorAll(".plot[data-chart]")) {
    const width = Math.round(el.clientWidth);
    if (!width || el.dataset.drawn === `${width}${t.text}`) continue;
    el.replaceChildren();
    charts[el.dataset.chart]?.(el, t, width);
    burst(el, !el.dataset.drawn);
    el.dataset.drawn = `${width}${t.text}`;
  }
}

async function main() {
  data = await (await fetch("/data/home.json")).json();
  lib = Object.fromEntries(data.libraries.map((l) => [l.id, l]));
  draw();
  let raf;
  new ResizeObserver(() => { cancelAnimationFrame(raf); raf = requestAnimationFrame(draw); }).observe(document.querySelector("main"));
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
}

main();

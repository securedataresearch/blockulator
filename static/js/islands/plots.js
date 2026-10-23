// The home page's charts, one per section, drawn from static/data/home.json, the same rows the
// tables under them are rendered from (scripts/site/home.py). Observable Plot, pinned.
// Colour is the library's family (blockulator.css --c-<family>); identity is the label, on the
// axis or on hover. Floating point and fixed point are drawn apart: stacked panels, or ◆ and ●
// where one panel holds both. Every chart has axis titles with units and a key.
import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.16/+esm";

const KINDS = [["float", "Floating point"], ["fixed", "Fixed point"]];
const FAMILIES = [["fp19", "FP19"], ["fp127", "FP127 · BlockulatorWad"], ["quad", "binary128 (ABDKMathQuad)"], ["6464", "ABDK 64.64"], ["wad", "WAD libraries"], ["protocol", "Maker, Aave, Morpho"]];
const GAS_CHART_OPS = ["add", "mul", "div", "mulDown", "divDown", "exp", "ln", "pow", "sqrt"];
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

let data, lib;

const theme = () => ({ text: css("--text"), faint: css("--faint"), line: css("--line-2"), family: (f) => css(`--c-${f}`) });
const colour = (t) => (d) => t.family(lib[d.lib].family);
const label = (id) => lib[id].label;
const fmt = (n) => n.toLocaleString("en-US");
const symbol = (d) => (lib[d.lib].kind === "float" ? "diamond2" : "circle");
const ours = (d) => !!lib[d.lib].ours;
const kshort = (v) => (v >= 1000 ? v / 1000 + "k" : v);

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

// one panel per kind, stacked, each only as tall as its libraries
function stacked(el, rows, draw) {
  for (const [kind, name] of KINDS) {
    const ids = data.libraries.filter((l) => l.kind === kind && rows.some((r) => r.lib === l.id)).map((l) => l.id);
    if (!ids.length) continue;
    const h = document.createElement("div");
    h.className = "panelhead";
    h.textContent = name;
    el.append(h, draw(rows.filter((r) => ids.includes(r.lib)), ids, kind === KINDS[0][0]));
  }
}

const charts = {
  // small multiples, one per op; each row of panels holds as many ops as fit, floating point over fixed point
  gas(el, t, width) {
    const g = data.gas;
    const ops = GAS_CHART_OPS.filter((o) => g.ops.includes(o));
    const fit = Math.max(2, Math.floor((width - 128) / 128));
    const per = Math.ceil(ops.length / Math.ceil(ops.length / fit)); // rows of equal length, never one op alone
    const rows = g.rows.filter((r) => ops.includes(r.op));
    for (let i = 0; i < ops.length; i += per) {
      const chunk = ops.slice(i, i + per);
      stacked(el, rows.filter((r) => chunk.includes(r.op)), (rs, ids, first) =>
        Plot.plot(base(t, width, {
          height: 22 * ids.length + (first ? 40 : 52), marginLeft: 128, marginTop: first ? 28 : 6, marginBottom: first ? 6 : 40,
          fx: { domain: chunk, label: null, axis: first ? "top" : null, tickFormat: (o) => o + (g.typical.includes(o) ? "ᵗ" : ""), padding: 0.12 },
          x: { type: "log", domain: [2, 40000], ticks: [10, 100, 1000, 10000], tickFormat: kshort, label: first ? null : "gas per call, log scale →", axis: first ? null : "bottom", grid: true },
          y: { domain: ids, label: null, tickFormat: (id) => `${label(id)} · ${lib[id].digits} digits`, tickSize: 0 },
          marks: [
            Plot.ruleY(rs, { fx: "op", y: "lib", stroke: t.line, strokeOpacity: 0.5 }),
            Plot.dot(rs, { fx: "op", x: "gas", y: "lib", r: (d) => (ours(d) ? 5.5 : 4.5), fill: colour(t), stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
            Plot.text(rs.filter(ours), { fx: "op", x: "gas", y: "lib", text: (d) => fmt(d.gas), dx: 8, textAnchor: "start", fontWeight: 600, fill: t.text }),
            Plot.tip(rs, Plot.pointer({ fx: "op", x: "gas", y: "lib", title: (d) => `${lib[d.lib].long}\n${d.op}: ${fmt(d.gas)} gas per call\n${lib[d.lib].digits} digits at 1` })),
          ],
        })),
      );
    }
    key(el, t, [...new Set(rows.map((r) => r.lib))]);
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
        Plot.dot(a.rows.filter((r) => r.n === last), { x: "n", y: "digits", fill: colour(t), r: (d) => (ours(d) ? 4.5 : 3), symbol }),
        Plot.text(labels, { x: last, y: "y", text: "text", dx: 10, textAnchor: "start", fill: colour(t), fontWeight: 600 }),
        Plot.tip(a.rows, Plot.pointer({ x: "n", y: "digits", title: (d) => `${lib[d.lib].long}\nafter ${fmt(d.n)} ${d.n === 1 ? "day" : "days"}: ${d.digits.toFixed(1)} correct digits` })),
      ],
    })));
    key(el, t, [...new Set(a.rows.map((r) => r.lib))]);
  },

  // one panel per library: the share of results off by a wei, per function
  wad(el, t, width) {
    const w = data.wad;
    const ids = data.libraries.filter((l) => w.rows.some((r) => r.lib === l.id)).map((l) => l.id);
    const cols = Math.max(2, Math.min(ids.length, Math.floor((width - 110) / 190)));
    const rows = w.rows.map((r) => ({ ...r, col: ids.indexOf(r.lib) % cols, row: Math.floor(ids.indexOf(r.lib) / cols) }));
    const nrow = Math.ceil(ids.length / cols);
    el.append(Plot.plot(base(t, width, {
      height: nrow * (17 * w.functions.length + 64) + 30,
      marginLeft: 110, marginRight: 34, marginTop: 26, marginBottom: 40,
      fx: { label: null, axis: null, padding: 0.18 }, fy: { label: null, axis: null, padding: 0.2 },
      x: { domain: [0, 100], ticks: [0, 50, 100], tickFormat: (v) => (v === 100 ? "100%" : v), label: "share of results off by ≥ 1 wei →", grid: true },
      y: { domain: w.functions, label: null, tickSize: 0 },
      marks: [
        Plot.text(ids.map((id, i) => ({ lib: id, col: i % cols, row: Math.floor(i / cols) })), { fx: "col", fy: "row", frameAnchor: "top-left", dy: -16, text: (d) => label(d.lib), fill: colour(t), fontWeight: 700, fontSize: 12.5 }),
        Plot.barX(rows, { fx: "col", fy: "row", y: "fn", x: "pct", fill: colour(t), insetTop: 2, insetBottom: 2, rx: 2 }),
        Plot.text(rows.filter((r) => r.wrong === 0), { fx: "col", fy: "row", y: "fn", x: 0, text: () => "0", dx: 6, textAnchor: "start", fill: t.text, fontWeight: 600 }),
        Plot.text(rows.filter((r) => r.wrong > 0), { fx: "col", fy: "row", y: "fn", x: "pct", text: (d) => Math.round(d.pct) + "%", dx: 4, textAnchor: "start", fill: t.faint }),
        Plot.tip(rows, Plot.pointer({ fx: "col", fy: "row", y: "fn", x: "pct", title: (d) => `${lib[d.lib].long}\n${d.fn}: ${fmt(d.wrong)} of ${fmt(d.n)} results off by a wei or more (${d.pct}%)` })),
      ],
    })));
    key(el, t, ids, false);
  },

  ladder(el, t, width) {
    const ld = data.ladder;
    const rows = ld.rows.filter((r) => r.digits != null).map((r) => ({ ...r, title: ld.scenarios.find((s) => s.id === r.scenario).title }));
    el.append(Plot.plot(base(t, width, {
      height: 28 * ld.scenarios.length + 60, marginLeft: 280, marginRight: 16, marginBottom: 42,
      x: { domain: [0, 76], label: "median correct decimal digits after the last step →", grid: true },
      y: { domain: ld.scenarios.map((s) => s.title), label: null, tickSize: 0 },
      marks: [
        Plot.ruleY(ld.scenarios.map((s) => s.title), { stroke: t.line, strokeOpacity: 0.5 }),
        Plot.dot(rows.filter((d) => !ours(d)), { x: "digits", y: "title", fill: colour(t), r: 4, fillOpacity: 0.85, symbol }),
        Plot.dot(rows.filter(ours), { x: "digits", y: "title", fill: colour(t), r: 6, stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
        Plot.tip(rows, Plot.pointer({ x: "digits", y: "title", title: (d) => `${lib[d.lib].long}\n${d.title}: ${d.digits.toFixed(1)} digits after ${fmt(d.n)} steps` })),
      ],
    })));
    key(el, t, [...new Set(rows.map((r) => r.lib))]);
  },

  edges(el, t, width) {
    const e = data.edges;
    const ticks = e.rows.flatMap((r) => r.digits.map((v) => ({ lib: r.lib, digits: v })));
    stacked(el, e.rows, (rows, ids, first) =>
      Plot.plot(base(t, width, {
        height: 24 * ids.length + (first ? 50 : 64), marginLeft: 150, marginTop: first ? 26 : 6, marginRight: 16, marginBottom: first ? 6 : 40,
        x: { domain: [0, 73], axis: first ? "top" : "bottom", label: "correct decimal digits on each probe →", grid: true },
        y: { domain: ids, label: null, tickFormat: (id) => `${label(id)} · ${e.rows.find((r) => r.lib === id).computed} probes`, tickSize: 0 },
        marks: [
          Plot.tickX(ticks.filter((d) => ids.includes(d.lib)), { x: "digits", y: "lib", stroke: colour(t), strokeOpacity: 0.35, insetTop: 4, insetBottom: 4 }),
          Plot.dot(rows, { x: "median", y: "lib", fill: colour(t), r: 5.5, stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
          Plot.tip(rows, Plot.pointer({ x: "median", y: "lib", title: (d) => `${lib[d.lib].long}\n${d.computed} probes computed, median ${d.median} digits, fewest ${d.min}\nto zero ${d.zero} · reverted ${d.reverts} · out of range ${d.range} · no such op ${d.unsupported}` })),
        ],
      })),
    );
    key(el, t, e.rows.map((r) => r.lib));
    el.lastChild.insertAdjacentHTML("beforeend", `<span class="sym">| one probe</span><span class="sym">● the median</span>`);
  },
};

function draw() {
  const t = theme();
  for (const el of document.querySelectorAll(".plot[data-chart]")) {
    const width = Math.round(el.clientWidth);
    if (!width || el.dataset.drawn === `${width}${t.text}`) continue;
    el.replaceChildren();
    charts[el.dataset.chart]?.(el, t, width);
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

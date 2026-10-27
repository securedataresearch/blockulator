// The home page's charts, one per section, drawn from static/data/home.json, the same rows the
// tables under them are rendered from (scripts/site/home.py). Observable Plot, pinned.
// Colour is the library's family (blockulator.css --c-<family>); identity is the label, on the
// axis or on hover. Floating point is ◆, fixed point ●, or above and below a rule. Every chart has
// axis titles with units and a key.
import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.16/+esm";

const KINDS = [["float", "Floating point"], ["fixed", "Fixed point"]];
const FAMILIES = [["fp19", "FP19"], ["fp127", "FP127 · BlockulatorWad"], ["quad", "binary128 (ABDKMathQuad)"], ["6464", "ABDK 64.64"], ["wad", "WAD libraries"], ["protocol", "Maker, Aave, Morpho"]];
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

let data, pages, lib;

const theme = () => ({ text: css("--text"), faint: css("--faint"), line: css("--line-2"), family: (f) => css(`--c-${f}`) });
const colour = (t) => (d) => t.family(lib[d.lib].family);
const label = (id) => lib[id].label;
const fmt = (n) => n.toLocaleString("en-US");
const symbol = (d) => (lib[d.lib].kind === "float" ? "diamond2" : "circle");
const ours = (d) => !!lib[d.lib].ours;

const fontSize = (width) => (width >= 760 ? 13 : 12);
function base(t, width, extra) {
  // r is always pixels: a radius given per dot (ours larger) is not data to be scaled
  return { width, r: { type: "identity" }, style: { background: "transparent", color: t.text, fontFamily: css("--sans"), fontSize: `${fontSize(width)}px`, overflow: "visible" }, ...extra };
}

// a label's width in pixels, in the charts' own font, so labels are placed by what they measure rather than a guess
let pen;
function measure(text, size, weight = 400) {
  pen ??= document.createElement("canvas").getContext("2d");
  pen.font = `${weight} ${size}px ${css("--sans")}`;
  return pen.measureText(text).width;
}

// faint bands behind every other row of a long chart, so the eye keeps its row across the width
const band = (t, domain, step) => [Plot.ruleY(domain.filter((_, i) => i % 2), { stroke: t.line, strokeOpacity: 0.28, strokeWidth: step })];

// a chart with one row per name. The names go in a left margin as wide as the longest, while that leaves the data
// most of the width; when it would not (a long name on a phone), each name sits on its own line above its row and
// the data takes the whole width. step is the row height; it grows by a line when the names move up. left keeps
// the names in the margin regardless (short names, or marks that would rise into the line above).
function rowAxis(t, width, domain, { fmt = (d) => d, step = 24, channel = "y", left = false } = {}) {
  const fs = fontSize(width), names = domain.map(fmt);
  const need = Math.ceil(Math.max(...names.map((n) => measure(n, fs)))) + 12;
  if (left || need <= width * (width < 560 ? 0.3 : 0.34)) {
    return { above: false, step, marginLeft: Math.max(need, 40), axis: { domain, label: null, tickSize: 0, tickFormat: fmt }, marks: [] };
  }
  const s = step + fs + 6;
  return {
    above: true, step: s, marginLeft: 6, axis: { domain, label: null, axis: null },
    marks: [Plot.text(domain, { [channel]: (d) => d, text: fmt, frameAnchor: channel === "fy" ? "top-left" : "left", textAnchor: "start",
      dy: channel === "fy" ? 2 : -(s / 2) + fs / 2, fill: t.faint, fontWeight: 500 })],
  };
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
    // every name is placed in pixels, by its measured width, where it hits no dot and no name already placed: right of
    // its dot, else left, else in the lowest free line above with a leader back to the dot. On a phone the WAD
    // libraries share one name. The x domain is the data's, padded, so the dots use the width.
    const narrow = width < 560, fs = fontSize(width), H = 480, M = { l: narrow ? 40 : 52, r: 16, t: 30, b: 44 };
    const lo = Math.min(...pts.map((p) => p.ratio)) / 1.35, hi = Math.max(...pts.map((p) => p.ratio)) * 1.6;
    const W = width - M.l - M.r, Hp = H - M.t - M.b, L = Math.log(hi / lo);
    const px = (r) => (Math.log(r / lo) / L) * W, py = (d) => (1 - d / 76) * Hp;
    const ix = (x) => lo * Math.exp((x / W) * L), iy = (y) => (1 - y / Hp) * 76;
    const rad = (p) => (ours(p) ? 10.5 : 8);
    const boxes = pts.map((p) => ({ x0: px(p.ratio) - rad(p) - 1, x1: px(p.ratio) + rad(p) + 1, y0: py(p.digits) - rad(p) - 1, y1: py(p.digits) + rad(p) + 1 }));
    const hit = (b) => b.x0 < 0 || b.x1 > W + M.r || b.y0 < -M.t + 4 || boxes.some((o) => b.x0 < o.x1 && b.x1 > o.x0 && b.y0 < o.y1 && b.y1 > o.y0);
    const wads = pts.filter((p) => lib[p.lib].family === "wad");
    const names = narrow && wads.length > 1
      ? [...pts.filter((p) => lib[p.lib].family !== "wad").map((p) => ({ p, text: label(p.lib) })),
         { p: { ...wads[0], ratio: Math.exp(wads.reduce((s, q) => s + Math.log(q.ratio), 0) / wads.length) }, text: `WAD libraries (${wads.length})`, group: true }]
      : pts.map((p) => ({ p, text: label(p.lib) }));
    const placed = [];
    for (const n of names.sort((a, b) => ours(b.p) - ours(a.p) || b.p.digits - a.p.digits || a.p.ratio - b.p.ratio)) {
      const w = measure(n.text, fs, ours(n.p) ? 700 : 500), h = fs + 2, x = px(n.p.ratio), y = py(n.p.digits), r = n.group ? 0 : rad(n.p);
      const tries = n.group ? [] : [[x + r + 4, y], [x - r - 4 - w, y]];
      for (let k = 1; k < 12; k++) tries.push([x - (n.group ? w / 2 : 0) + (n.group ? 0 : 2), y - r - 4 - h * (k - 0.5)]);
      const [tx, ty] = tries.find(([tx, ty]) => !hit({ x0: tx - 1, x1: tx + w + 1, y0: ty - h / 2, y1: ty + h / 2 })) || tries[tries.length - 1];
      boxes.push({ x0: tx - 1, x1: tx + w + 1, y0: ty - h / 2, y1: ty + h / 2 });
      placed.push({ lib: n.p.lib, text: n.text, x: ix(tx), y: iy(ty), ox: n.p.ratio, oy: n.p.digits, lead: Math.abs(ty - y) > r + 2 && !n.group,
        lx: ix(Math.min(Math.max(x, tx + 2), tx + w - 2)), ly: iy(ty + h / 2 - 1) });
    }
    const ticks = [0.1, 0.2, 0.3, 0.5, 1, 2, 3, 5, 10].filter((v) => v >= lo && v <= hi);
    el.append(Plot.plot(base(t, width, {
      height: H, marginLeft: M.l, marginRight: M.r, marginBottom: M.b, marginTop: M.t,
      x: { type: "log", domain: [lo, hi], label: narrow ? "gas, × FP127's on the same ops (log) →" : "gas per call, as a multiple of FP127's on the same ops (log scale) →", tickFormat: (v) => v + "×", ticks },
      y: { domain: [0, 76], label: "↑ decimal digits at 1", grid: true },
      marks: [
        Plot.ruleX([1], { stroke: t.faint, strokeDasharray: "3 3" }),
        Plot.text([{ x: 1, y: 75 }], { x: "x", y: "y", text: () => "FP127's gas", dx: 5, textAnchor: "start", fill: t.faint }),
        Plot.link(placed.filter((d) => d.lead), { x1: "ox", y1: "oy", x2: "lx", y2: "ly", stroke: t.faint, strokeWidth: 0.8 }),
        Plot.dot(pts.filter((d) => !ours(d)), { x: "ratio", y: "digits", fill: colour(t), r: 8, stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
        Plot.dot(pts.filter(ours), { x: "ratio", y: "digits", fill: colour(t), r: 10.5, stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
        Plot.text(placed, { x: "x", y: "y", text: "text", textAnchor: "start", lineAnchor: "middle", fill: t.text, fontWeight: (d) => (ours(d) ? 700 : 500) }),
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
      height: 400, marginRight: Math.min(210, Math.round(width * 0.42)), marginLeft: 48, marginBottom: 42,
      x: { type: "log", domain: [1, last], label: width < 560 ? "days without an update (log) →" : "days since the last update (log scale) →",
           ticks: width < 560 ? a.cols.filter((c) => [1, 10, 100, 1000, 10000].includes(c)) : a.cols, tickFormat: (v) => (width < 560 && v >= 1000 ? v / 1000 + "k" : fmt(v)) },
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
    // BlockulatorWad first, so the dodge gives it the middle of its row and the others stack around it
    const rows = [...w.rows].sort((a, b) => ours(b) - ours(a));
    const rw = rowAxis(t, width, w.functions, { step: 40, channel: "fy", left: true });
    el.append(Plot.plot(base(t, width, {
      height: w.functions.length * rw.step + 70, marginLeft: rw.marginLeft, marginRight: 30, marginBottom: 44, marginTop: 10,
      fy: { ...rw.axis, padding: 0 },
      x: { domain: [-2, 102], ticks: [0, 25, 50, 75, 100], tickFormat: (v) => v + "%", label: "share of results off by ≥ 1 wei →", grid: true },
      marks: [
        ...rw.marks,
        Plot.frame({ anchor: "bottom", stroke: t.line, strokeOpacity: 0.5 }),
        Plot.dot(rows, Plot.dodgeY("middle", { fy: "fn", x: "pct", r: (d) => (ours(d) ? 9 : 7), fill: colour(t), stroke: "var(--surface-solid)", strokeWidth: 1.5, padding: 1.5 })),
        Plot.tip(rows, Plot.pointer({ fy: "fn", x: "pct", title: (d) => `${lib[d.lib].long}\n${d.fn}: ${fmt(d.wrong)} of ${fmt(d.n)} results off by a wei or more (${d.pct}%)` })),
      ],
    })));
    key(el, t, [...new Set(rows.map((r) => r.lib))], false);
  },

  ladder(el, t, width) {
    const ld = data.ladder;
    const rows = ld.rows.filter((r) => r.digits != null).map((r) => ({ ...r, title: ld.scenarios.find((s) => s.id === r.scenario).title }));
    const titles = ld.scenarios.map((s) => s.title), rw = rowAxis(t, width, titles, { step: 32 });
    el.append(Plot.plot(base(t, width, {
      height: rw.step * titles.length + 60, marginLeft: rw.marginLeft, marginRight: 16, marginBottom: 42,
      x: { domain: [0, 76], label: width < 560 ? "median correct digits, last step →" : "median correct decimal digits after the last step →", grid: true },
      y: rw.axis,
      marks: [
        ...rw.marks,
        Plot.ruleY(titles, { stroke: t.line, strokeOpacity: 0.5 }),
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
  // /results/ladder/: one scenario's median digits against N, every library; the truth toggle above it picks the key
  steps(el, t, width) {
    const sc = pages.steps.find((s) => s.id === el.dataset.arg);
    const key = el.closest("section")?.querySelector('input[type="radio"]:checked')?.value || "digits";
    const rows = sc.rows.filter((r) => r[key]).map((r) => ({ ...r, v: r[key][0], lo: r[key][1], hi: r[key][2] }));
    if (!rows.length) return;
    const last = Math.max(...rows.map((r) => r.n));
    // end labels at each line's last point, nudged at least 4 digits apart; the WAD libraries' gold lines share one label
    const last1 = rows.filter((r) => r.n === Math.max(...rows.filter((q) => q.lib === r.lib).map((q) => q.n)));
    const wad = last1.filter((r) => lib[r.lib].family === "wad");
    const ends = [...last1.filter((r) => lib[r.lib].family !== "wad").map((r) => ({ ...r, ly: r.v, name: label(r.lib) })),
      ...(wad.length ? [{ ...wad[0], ly: wad.reduce((s, r) => s + r.v, 0) / wad.length, name: "WAD libraries" }] : [])].sort((a, b) => b.ly - a.ly);
    for (let i = 1; i < ends.length; i++) ends[i].ly = Math.min(ends[i].ly, ends[i - 1].ly - 4);
    for (let i = ends.length - 1; i >= 0; i--) ends[i].ly = Math.max(ends[i].ly, i === ends.length - 1 ? 1 : ends[i + 1].ly + 4);
    el.append(Plot.plot(base(t, width, {
      height: 360, marginLeft: 48, marginRight: 150, marginBottom: 42,
      x: { type: "log", domain: [1, last], label: "steps N (log scale) →", tickFormat: fmt },
      y: { domain: [0, 76], label: key === "interest" ? "↑ correct digits of the interest" : "↑ median correct decimal digits", grid: true },
      marks: [
        Plot.line(rows, { x: "n", y: "v", z: "lib", stroke: colour(t), strokeWidth: (d) => (ours(d) ? 3 : 1.6), strokeOpacity: (d) => (ours(d) ? 1 : 0.8) }),
        Plot.dot(rows, { x: "n", y: "v", fill: colour(t), r: (d) => (ours(d) ? 4.5 : 3.5), symbol }),
        Plot.text(ends, { x: "n", y: "ly", text: "name", dx: 8, textAnchor: "start", fill: colour(t), fontWeight: 600 }),
        Plot.tip(rows, Plot.pointer({ x: "n", y: "v", title: (d) => `${lib[d.lib].long}\nN = ${fmt(d.n)}: ${d.v} digits (range ${d.lo}–${d.hi} over the inputs)` })),
      ],
    })));
  },

  // /results/edges/: one op, every probe's digits per library; failures sit at 0 in red. Dots that share a library and
  // a digit count stack around their library's row (y is the row index plus that offset; Plot's dy is not a channel)
  edgeop(el, t, width) {
    const op = pages.edges.find((o) => o.id === el.dataset.arg);
    const ids = KINDS.flatMap(([k]) => pages.libraries.filter((l) => l.kind === k && op.rows.some((r) => r.lib === l.id)).map((l) => l.id));
    const red = css("--red"), count = new Map();
    for (const r of op.rows) count.set(`${r.lib}|${r.digits}`, (count.get(`${r.lib}|${r.digits}`) || 0) + 1);
    const rowH = Math.max(26, 9 * Math.max(...count.values()) + 8), seen = new Map();
    const rows = op.rows.map((r) => {
      const k = `${r.lib}|${r.digits}`, i = seen.get(k) || 0;
      seen.set(k, i + 1);
      return { ...r, y: ids.indexOf(r.lib) + ((i - (count.get(k) - 1) / 2) * 9) / rowH };
    });
    el.append(Plot.plot(base(t, width, {
      height: rowH * ids.length + 60, marginLeft: 120, marginRight: 20, marginBottom: 42, marginTop: 8,
      x: { domain: [0, 73], label: "correct decimal digits on each probe →", grid: true },
      y: { domain: [ids.length - 0.5, -0.5], label: null, ticks: ids.map((_, i) => i), tickFormat: (i) => label(ids[i]), tickSize: 0 },
      marks: [
        Plot.ruleY(ids.map((_, i) => i), { stroke: t.line, strokeOpacity: 0.5 }),
        Plot.dot(rows, { x: "digits", y: "y", r: 4, fill: (d) => (d.status === "ok" ? t.family(lib[d.lib].family) : red), fillOpacity: (d) => (d.status === "ok" ? 0.9 : 0.6), symbol }),
        Plot.tip(rows, Plot.pointer({ x: "digits", y: "y", title: (d) => `${lib[d.lib].long}\n${d.label}: ${d.status === "ok" ? d.digits + " digits" : d.status}` })),
      ],
    })));
    const p = document.createElement("p");
    p.className = "plotlegend";
    p.innerHTML = `<span><i style="background:${red};opacity:.6"></i>went to zero, reverted or out of range</span><span class="sym">one dot per probe; ◆ floating point, ● fixed point</span>`;
    el.append(p);
  },

  // /results/ops/: gas per call for every op, every library, one row per op
  gasops(el, t, width) {
    const rows = pages.gas;
    const ops = [...new Set(rows.map((r) => r.op))].sort((a, b) => rows.filter((r) => r.op === b).length - rows.filter((r) => r.op === a).length || a.localeCompare(b));
    const rw = rowAxis(t, width, ops, { step: 22 });
    el.append(Plot.plot(base(t, width, {
      height: rw.step * ops.length + 80, marginLeft: rw.marginLeft, marginRight: 20, marginBottom: 42, marginTop: 36,
      x: { type: "log", label: "median gas per call (log scale) →", grid: true, tickFormat: fmt, axis: "both" },
      y: rw.axis,
      marks: [
        ...band(t, ops, rw.step),
        ...rw.marks,
        Plot.ruleY(ops, { stroke: t.line, strokeOpacity: 0.4 }),
        Plot.dot(rows.filter((d) => !ours(d)), { x: "gas", y: "op", fill: colour(t), r: 5, fillOpacity: 0.85, symbol }),
        Plot.dot(rows.filter(ours), { x: "gas", y: "op", fill: colour(t), r: 6.5, stroke: "var(--surface-solid)", strokeWidth: 1.5, symbol }),
        Plot.tip(rows, Plot.pointer({ x: "gas", y: "op", title: (d) => `${lib[d.lib].long}\n${d.op}: ${fmt(d.gas)} gas per call` })),
      ],
    })));
    key(el, t, [...new Set(rows.map((r) => r.lib))]);
  },

  // /library/ pages: every op ranked by gas, inline (filled) against a staticcall to the deployed object (ring)
  libops(el, t, width) {
    const id = el.dataset.arg, c = t.family(lib[id].family);
    const rows = [...pages.libops[id]].sort((a, b) => a.inline - b.inline);
    const opsL = rows.map((r) => r.op), rw = rowAxis(t, width, opsL, { step: 16 });
    el.append(Plot.plot(base(t, width, {
      height: rw.step * rows.length + 80, marginLeft: rw.marginLeft, marginRight: 20, marginBottom: 42, marginTop: 36,
      x: { type: "log", label: "median gas per call (log scale) →", grid: true, tickFormat: fmt, axis: "both" },
      y: rw.axis,
      marks: [
        ...band(t, opsL, rw.step),
        ...rw.marks,
        Plot.link(rows.filter((r) => r.object), { x1: "inline", x2: "object", y1: "op", y2: "op", stroke: c, strokeOpacity: 0.35, strokeWidth: 2 }),
        Plot.dot(rows.filter((r) => r.object), { x: "object", y: "op", r: 4, stroke: c, strokeWidth: 1.5, fill: "var(--surface-solid)" }),
        Plot.dot(rows, { x: "inline", y: "op", r: 4.5, fill: c }),
        Plot.tip(rows, Plot.pointer({ x: "inline", y: "op", title: (d) => `${d.op}: ${fmt(d.inline)} gas inline${d.object ? `, ${fmt(d.object)} through the deployed object` : ""}\n${d.exact ? "exact" : "rounded once"}` })),
      ],
    })));
    const p = document.createElement("p");
    p.className = "plotlegend";
    p.innerHTML = `<span><i style="background:${c}"></i>inline (${lib[id].label}Lib)</span><span><i style="background:transparent;box-shadow:inset 0 0 0 1.5px ${c}"></i>a staticcall to the deployed object</span>`;
    el.append(p);
  },

  // /results/deployed/: each stylised case's correct digits of the interest, as deployed and in FP127 and FP19
  deployed(el, t, width) {
    const cs = pages.deployed.cases;
    const pts = cs.flatMap((c) => [[c.protocol, c.deployed, "as deployed"], ["fp127", c.fp127, "in FP127"], ["fp19", c.fp19, "in FP19"]]
      .map(([l, v, how]) => ({ lib: l, digits: v, how, label: c.label })));
    const rw = rowAxis(t, width, cs.map((c) => c.label), { step: 22 });
    el.append(Plot.plot(base(t, width, {
      height: rw.step * cs.length + 60, marginLeft: rw.marginLeft, marginRight: 20, marginBottom: 42,
      x: { domain: [0, 76], label: "correct decimal digits of the interest →", grid: true },
      y: rw.axis,
      marks: [
        ...band(t, cs.map((c) => c.label), rw.step),
        ...rw.marks,
        Plot.link(cs, { x1: "deployed", x2: "fp19", y1: "label", y2: "label", stroke: t.line, strokeOpacity: 0.6 }),
        // the token grid's limit: a dashed tick, or on a phone (names above the rows) the legend's ┆, which stays on its row
        rw.above
          ? Plot.text(cs.filter((c) => c.grid != null), { x: "grid", y: "label", text: () => "┆", fill: t.faint, fontSize: 12, fontWeight: 700 })
          : Plot.tickX(cs.filter((c) => c.grid != null), { x: "grid", y: "label", stroke: t.faint, strokeWidth: 2, strokeDasharray: "2 2" }),
        Plot.dot(pts, { x: "digits", y: "label", fill: colour(t), r: (d) => (ours(d) ? 6 : 6.5), stroke: "var(--surface-solid)", strokeWidth: 1.2, symbol }),
        Plot.tip(pts, Plot.pointer({ x: "digits", y: "label", title: (d) => `${d.label}\n${d.how}: ${d.digits.toFixed(2)} digits of the interest` })),
      ],
    })));
    key(el, t, ["aave", "fp127", "fp19"]);
    el.lastChild.insertAdjacentHTML("beforeend", `<span class="sym">┆ the most digits any answer in whole token units could show</span>`);
  },

  // /results/deployed/: every live Aave reserve side and Morpho market at the survey block, as deployed and the most
  // digits any answer in whole token units could show (the pending interest is small, so the grid is the limit)
  live(el, t, width) {
    const rows = pages.deployed.live.flatMap((c) => [
      { lib: c.protocol, digits: c.deployed, row: `${lib[c.protocol].label}, as deployed`, label: c.label },
      { lib: c.protocol, digits: c.grid, row: `${lib[c.protocol].label}, token grid allows`, label: c.label, grid: true },
    ]);
    const order = [...new Set(rows.map((r) => r.row))], narrow = width < 560;
    // each row is tall enough for its swarm: the most dots that fall within one dot's width of each other, stacked
    const r = narrow ? 1.7 : 2.4, bin = (2 * r * 26) / (width * 0.8), bins = new Map();
    for (const d of rows) { const k = `${d.row}|${Math.round(d.digits / bin)}`; bins.set(k, (bins.get(k) || 0) + 1); }
    // the swarm sits in the middle of its row, so a line of clearance above and below keeps it off a name over the row
    const swarm = Math.max(...bins.values()) * 2 * r * 1.1, clear = fontSize(width) + 10;
    const rw = rowAxis(t, width, order, { step: Math.min(320, Math.max(70, swarm + 2 * clear)) - (narrow ? fontSize(width) + 6 : 0), channel: "fy" });
    el.append(Plot.plot(base(t, width, {
      height: rw.step * order.length + 52, marginLeft: rw.marginLeft, marginRight: 20, marginBottom: 42,
      x: { domain: [0, 26], label: narrow ? "correct digits of the pending interest →" : "correct decimal digits of the pending interest →", grid: true, ticks: narrow ? [0, 5, 10, 15, 20, 25] : undefined },
      fy: { ...rw.axis, padding: 0.08 }, y: { axis: null },
      marks: [
        ...rw.marks,
        Plot.dot(rows, Plot.dodgeY("middle", { x: "digits", fy: "row", r, fill: (d) => (d.grid ? t.faint : t.family(lib[d.lib].family)), fillOpacity: 0.85, clip: true })),
        Plot.tip(rows, Plot.pointer({ x: "digits", fy: "row", title: (d) => `${d.label}: ${d.digits.toFixed(2)} digits${d.grid ? " at most on the token grid" : " as deployed"}` })),
      ],
    })));
  },

};

// on hover the nearest dot within 24px (as the tip finds it) takes a halo in its own colour (blockulator.css .plot .dotm)
function halo(el) {
  const dots = [...el.querySelectorAll('g[aria-label="dot"] > *')];
  for (const d of dots) {
    d.classList.add("dotm");
    d.style.setProperty("--dc", d.getAttribute("fill") || d.parentNode.getAttribute("fill"));
  }
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

// each data file is fetched once, when the first chart that reads it comes near the viewport
const files = {};
const load = (src) => (files[src] ??= fetch(`/data/${src}.json`).then((r) => r.json()));

// draws one chart if it is laid out and its width or theme changed. A width change under 24px (a scrollbar
// appearing) is left to the SVG's own scaling, so nothing redraws while the page settles. The swap is synchronous,
// so no frame shows an empty box; the chart fades in on its first draw only.
async function draw(el, force = false) {
  const width = Math.round(el.clientWidth);
  if (!width) return;
  const src = el.dataset.src || "home";
  const d = await load(src);
  if (src === "home") data = d; else pages = d;
  lib ??= Object.fromEntries(d.libraries.map((l) => [l.id, l]));
  const t = theme(), [w0, text0] = (el.dataset.drawn || "0|").split("|");
  if (!force && text0 === t.text && Math.abs(width - +w0) < 24) return;
  el.replaceChildren();
  charts[el.dataset.chart]?.(el, t, width);
  halo(el);
  el.dataset.drawn = `${width}|${t.text}`;
  requestAnimationFrame(() => el.classList.add("in"));
}

function main() {
  const els = [...document.querySelectorAll(".plot[data-chart]")];
  // drawn once they are within a screen of the viewport; a hidden tab's charts draw when it is shown and scrolled to
  const near = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && draw(e.target)), { rootMargin: "200% 0px" });
  const resized = new ResizeObserver((es) => es.forEach((e) => e.target.dataset.drawn && draw(e.target)));
  els.forEach((el) => { near.observe(el); resized.observe(el); });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => els.forEach((el) => el.dataset.drawn && draw(el, true)));
  // a chart follows its section's truth toggle
  document.addEventListener("change", (e) => {
    if (e.target.matches('input[type="radio"]')) e.target.closest("section")?.querySelectorAll(".plot[data-chart]").forEach((el) => draw(el, true));
  });
}

main();

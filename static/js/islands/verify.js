// Tabs for the scenarios, and the per-cell "verify on Sepolia" button: one
// eth_call to LadderRunner.run(scenario, form, n, p) through the public RPC
// with the cell's floored parameters, compared with the raw word committed in
// ladder.json. No wallet, no ethers: the calldata is encoded by hand.
import { encodeRun, decodeRun, encodeOp, decodeOp } from './digits.js';

const RPC = 'https://ethereum-sepolia-rpc.publicnode.com';
const SCALE_OF_FORM = ['fp127', 'fp127', 'abdk', 'wad', 'wad', 'quad', 'wad', 'ray', 'wad', 'ray', 'fp256'];

const tabs = document.querySelectorAll('#scenario-tabs a');
const sections = document.querySelectorAll('section.scenario');
function show(id) {
    if (!document.getElementById(id)) return;
    sections.forEach((s) => { s.hidden = s.id !== id; });
    tabs.forEach((t) => t.classList.toggle('on', t.dataset.tab === id));
}
window.addEventListener('hashchange', () => show(location.hash.slice(1)));
if (location.hash) show(location.hash.slice(1));

// exact-truth / format-truth toggle: swaps the chart and the summary columns of that scenario
document.addEventListener('change', (e) => {
    const r = e.target;
    if (!r.matches('.toggle input[type=radio]')) return;
    const section = r.closest('section.scenario');
    section.querySelectorAll('[data-key]').forEach((el) => { el.hidden = el.dataset.key !== r.value; });
});

// The ladder page verifies against LadderRunner (/data/ladder.json), the
// edges page against EdgeRunner (/data/edges.json); a button says which with
// data-kind.
const live = {};   // kind -> { runner, selector, inputs: Map(key -> cell) }
async function setup(kind) {
    if (live[kind]) return live[kind];
    const edge = kind === 'edge';
    const [doc, inputs] = await Promise.all([
        fetch(edge ? '/data/edges.json' : '/data/ladder.json').then((r) => r.json()),
        fetch(edge ? '/data/edge-inputs.json' : '/data/ladder-inputs.json').then((r) => r.json()),
    ]);
    const map = new Map();
    for (const c of inputs.cells) map.set(edge ? c.id : `${c.scenario}/${c.input}`, c);
    live[kind] = { runner: doc.liveRunner, selector: doc.liveSelector, inputs: map };
    return live[kind];
}

async function rpc(to, data) {
    const res = await fetch(RPC, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'eth_call', params: [{ to, data }, 'latest'] }),
    });
    const j = await res.json();
    if (j.error) throw new Error(j.error.message);
    return j.result;
}

async function call(scenario, input, form, n) {
    const L = await setup('ladder');
    if (!L.runner || !L.selector) throw new Error('runner not deployed');
    const cell = L.inputs.get(`${scenario}/${input}`);
    if (!cell) throw new Error('input not in ladder-inputs.json');
    const p = cell[SCALE_OF_FORM[form]].map((s) => BigInt(s));
    return decodeRun(await rpc(L.runner, encodeRun(L.selector, scenario, form, n, p)));
}

async function callEdge(op, probe, form) {
    const L = await setup('edge');
    if (!L.runner || !L.selector) throw new Error('runner not deployed');
    const cell = L.inputs.get(probe);
    if (!cell) throw new Error('probe not in edge-inputs.json');
    const args = cell[SCALE_OF_FORM[form]].map((s) => BigInt(s));
    const r = decodeOp(await rpc(L.runner, encodeOp(L.selector, op, form, args)));
    return { ok: r.ok, raw: r.raw, reason: r.reason, gasPerStep: r.gas };
}

document.addEventListener('click', async (e) => {
    const b = e.target.closest('button.verify');
    if (!b || b.disabled) return;
    b.disabled = true;
    b.textContent = 'calling…';
    try {
        const r = b.dataset.kind === 'edge'
            ? await callEdge(Number(b.dataset.op), b.dataset.probe, Number(b.dataset.form))
            : await call(b.dataset.scenario, b.dataset.input, Number(b.dataset.form), b.dataset.n);
        let match;
        if (b.dataset.raw) match = r.ok && r.raw === BigInt(b.dataset.raw);
        else match = !r.ok && r.reason === b.dataset.reason;
        b.textContent = match ? `live: match (${r.gasPerStep} gas${b.dataset.kind === 'edge' ? '' : '/step'})` : 'live: MISMATCH';
        b.classList.add(match ? 'match' : 'mismatch');
        if (!match) console.warn('ladder mismatch', b.dataset, r);
    } catch (err) {
        b.textContent = `live: ${err.message}`;
        b.classList.add('mismatch');
        b.disabled = false;
    }
});

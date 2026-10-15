// Tabs for the scenarios, and the per-cell "verify on Sepolia" button: one
// eth_call to LadderRunner.run(scenario, form, n, p) through the public RPC
// with the cell's floored parameters, compared with the raw word committed in
// ladder.json. No wallet, no ethers: the calldata is encoded by hand.
import { encodeRun, decodeRun } from './digits.js';

const RPC = 'https://ethereum-sepolia-rpc.publicnode.com';
const SCALE_OF_FORM = ['fp127', 'fp127', 'abdk', 'wad', 'wad', 'quad', 'wad', 'ray', 'wad', 'ray'];

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

let live = null;   // { runner, selector, inputs: Map("id/input" -> cell) }
async function setup() {
    if (live) return live;
    const [ladder, inputs] = await Promise.all([
        fetch('/data/ladder.json').then((r) => r.json()),
        fetch('/data/ladder-inputs.json').then((r) => r.json()),
    ]);
    const map = new Map();
    for (const c of inputs.cells) map.set(`${c.scenario}/${c.input}`, c);
    live = { runner: ladder.liveRunner, selector: ladder.liveSelector, inputs: map };
    return live;
}

async function call(scenario, input, form, n) {
    const L = await setup();
    if (!L.runner || !L.selector) throw new Error('runner not deployed');
    const cell = L.inputs.get(`${scenario}/${input}`);
    if (!cell) throw new Error('input not in ladder-inputs.json');
    const p = cell[SCALE_OF_FORM[form]].map((s) => BigInt(s));
    const data = encodeRun(L.selector, scenario, form, n, p);
    const res = await fetch(RPC, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'eth_call', params: [{ to: L.runner, data }, 'latest'] }),
    });
    const j = await res.json();
    if (j.error) throw new Error(j.error.message);
    return decodeRun(j.result);
}

document.addEventListener('click', async (e) => {
    const b = e.target.closest('button.verify');
    if (!b || b.disabled) return;
    b.disabled = true;
    b.textContent = 'calling…';
    try {
        const r = await call(b.dataset.scenario, b.dataset.input, Number(b.dataset.form), b.dataset.n);
        let match;
        if (b.dataset.raw) match = r.ok && r.raw === BigInt(b.dataset.raw);
        else match = !r.ok && r.reason === b.dataset.reason;
        b.textContent = match ? `live: match (${r.gasPerStep} gas/step)` : 'live: MISMATCH';
        b.classList.add(match ? 'match' : 'mismatch');
        if (!match) console.warn('ladder mismatch', b.dataset, r);
    } catch (err) {
        b.textContent = `live: ${err.message}`;
        b.classList.add('mismatch');
        b.disabled = false;
    }
});

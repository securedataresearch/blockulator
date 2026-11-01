// Scenario tabs and the exact-truth / format-truth toggle on the ladder and
// edges pages. The live check against Sepolia is done once at build time by
// scripts/ladder/livecap.py and liveedges.py; the page shows its stamp.
const tabs = document.querySelectorAll('#scenario-tabs a');
const sections = document.querySelectorAll('section.scenario');
function show(id) {
    if (!document.getElementById(id)) return;
    sections.forEach((s) => { s.hidden = s.id !== id; });
    tabs.forEach((t) => { if (t.dataset.tab === id) t.setAttribute('aria-current', 'true'); else t.removeAttribute('aria-current'); });
}
window.addEventListener('hashchange', () => show(location.hash.slice(1)));
if (location.hash) show(location.hash.slice(1));

// swaps the chart and the summary columns of that scenario
document.addEventListener('change', (e) => {
    const r = e.target;
    if (!r.matches('.toggle input[type=radio]')) return;
    const section = r.closest('section.scenario');
    section.querySelectorAll('[data-key]').forEach((el) => { el.hidden = el.dataset.key !== r.value; });
});

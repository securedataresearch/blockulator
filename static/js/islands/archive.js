// Mounts the archived apps on demand. The URL hash is the source of truth, in
// the protocol the apps already speak: #/games, #/games/<id>, #/vyper, #/futures.
import { boot, loadScript } from './shell.js';

const island = document.getElementById('archive-island');
const blocks = { games: 'archive-games', vyper: 'archive-vyper', futures: 'archive-futures' };
const apps = {};
let ctx = null;

async function app(key) {
    if (!ctx) ctx = await boot({ walletHost: '#archive-island .island-bar' });
    if (apps[key]) return apps[key];
    if (key === 'games') {
        const { GamesApp } = await import('../legacy/application/games-app.js');
        apps.games = new GamesApp(ctx.web3Provider, ctx.walletComponent, ctx.toastComponent);
    } else if (key === 'vyper') {
        const { CalculatorApp } = await import('../legacy/application/calculator-app.js');
        apps.vyper = new CalculatorApp(ctx.web3Provider, ctx.walletComponent, ctx.toastComponent);
    } else if (key === 'futures') {
        await loadScript('/vendor/chart.js@4.4.0/chart.umd.js', 'Chart');
        const { FuturesApp } = await import('../legacy/application/futures-app.js');
        apps.futures = new FuturesApp(ctx.web3Provider, ctx.walletComponent, ctx.toastComponent);
    }
    await apps[key].init();
    return apps[key];
}

async function route() {
    const h = location.hash;
    if (!h.startsWith('#/')) { island.hidden = true; return; }
    const [key, sub] = h.slice(2).split('/');
    if (key === 'badges') { location.href = '/badges/'; return; }
    if (!blocks[key]) { island.hidden = true; return; }
    island.hidden = false;
    for (const [k, id] of Object.entries(blocks)) document.getElementById(id).hidden = k !== key;
    document.getElementById('archive-open').textContent = document.querySelector(`[data-open="${key}"] h3`)?.textContent || key;
    try {
        const a = await app(key);
        if (key === 'games') {
            const { gameRegistry } = await import('../legacy/core/GameRegistry.js');
            const already = sub && a.currentGame && a.currentGame.constructor === gameRegistry.get(sub);
            if (!already) await a.handleSubRoute(sub || null);
        } else if (apps[key] === a && a.refresh && a._mounted) {
            await a.refresh();
        }
        a._mounted = true;
    } catch (e) {
        console.error(e);
    }
    island.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.getElementById('archive-close')?.addEventListener('click', () => { history.replaceState(null, '', location.pathname); route(); });
window.addEventListener('hashchange', route);
route();

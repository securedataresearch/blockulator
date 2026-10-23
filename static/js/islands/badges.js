import { boot } from './shell.js';

// If the badge island has not left its loading state in 15 s, or boot fails, say so instead of spinning forever.
const loading = document.getElementById('badge-loading');
const fail = (why) => {
    if (!loading || loading.classList.contains('hidden')) return;
    loading.innerHTML = '';
    const p = document.createElement('p');
    p.textContent = `The badge contracts did not answer${why ? ` (${why})` : ''}. Sepolia's RPC may be slow or unreachable: reload to try again.`;
    loading.appendChild(p);
};
// The timer stays armed after a clean init: fail() does nothing once the loading state is gone.
const timer = setTimeout(() => fail('no answer in 15 s'), 15000);

try {
    const ctx = await boot({ walletHost: '#badges-island .island-bar' });
    const { BadgeManager } = await import('../legacy/domain/identity/badge-manager.js');
    await new BadgeManager().init(ctx.web3Provider);
} catch (e) {
    clearTimeout(timer);
    fail(e && e.message ? e.message : String(e));
}

#!/usr/bin/env node
/**
 * Fail if application CSS/JS contains literal hex or rgb()/rgba() outside
 * the allowlisted token bridge and palette modules.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(__dirname, '..');

// Colour literals live in exactly three files: the site's theme (site.css), and the two
// legacy token bridges the archived apps use; plus base.html's critical block.
const SKIP = new Set([
    path.join(REPO_ROOT, 'static', 'css', 'site.css'),
    path.join(REPO_ROOT, 'static', 'css', 'legacy', 'tokens.css'),
    path.join(REPO_ROOT, 'static', 'js', 'legacy', 'theme', 'sdr-palette.js'),
]);

const reHex = /#[0-9a-fA-F]{3,8}\b/;
const reRgb = /\brgb\s*\(/;
const reRgba = /\brgba\s*\(/;

function walkDir(dir, acc = []) {
    if (!fs.existsSync(dir)) return acc;
    for (const name of fs.readdirSync(dir)) {
        if (name === 'node_modules' || name === '.git' || name === 'contracts' || name === 'data') continue;
        const full = path.join(dir, name);
        const st = fs.statSync(full);
        if (st.isDirectory()) walkDir(full, acc);
        else acc.push(full);
    }
    return acc;
}

function stripLineComments(line) {
    return line.replace(/\/\/.*$/, '');
}

function checkFile(file) {
    if (SKIP.has(file)) return [];
    const rel = path.relative(REPO_ROOT, file);
    const text = fs.readFileSync(file, 'utf8');
    const lines = text.split(/\r?\n/);
    const hits = [];
    // base.html's critical block repeats site.css's --bg (and the theme-color metas) so the first paint is the right colour
    // before any stylesheet arrives; it is the one place in a template a colour may be written out.
    let critical = false;
    lines.forEach((raw, idx) => {
        if (raw.includes('<style id="critical">')) critical = true;
        if (critical) { if (raw.includes('</style>')) critical = false; return; }
        if (raw.includes('name="theme-color"')) return;
        if (/^\s*(\/\/|\*|\/\*)/.test(raw)) return;
        const line = stripLineComments(raw);
        if (reHex.test(line) || reRgb.test(line) || reRgba.test(line)) {
            hits.push(`${rel}:${idx + 1}: ${raw.trim()}`);
        }
    });
    return hits;
}

const targets = [
    ...walkDir(path.join(REPO_ROOT, 'static', 'js')).filter((f) => f.endsWith('.js')),
    ...walkDir(path.join(REPO_ROOT, 'static', 'css')).filter((f) => f.endsWith('.css')),
    ...walkDir(path.join(REPO_ROOT, 'templates')).filter((f) => f.endsWith('.html')),
];

const all = targets.flatMap(checkFile);

if (all.length) {
    console.error('SDR color guard: hex/rgb/rgba found outside allowlisted token files:\n');
    console.error(all.join('\n'));
    process.exit(1);
}

console.log('SDR color guard: OK');

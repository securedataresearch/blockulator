#!/usr/bin/env -S deno run --allow-read
/**
 * Fail if a Markdown link points at nothing.
 *
 *  Markdown links in README.md, docs/, contracts/, scripts/ must resolve.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const rel = (f) => path.relative(ROOT, f);
const problems = [];

function walk(dir, acc = []) {
    if (!fs.existsSync(dir)) return acc;
    for (const name of fs.readdirSync(dir)) {
        const full = path.join(dir, name);
        if (fs.statSync(full).isDirectory()) walk(full, acc);
        else acc.push(full);
    }
    return acc;
}

// Markdown links
const mdFiles = [path.join(ROOT, 'README.md'), ...['docs', 'contracts', 'scripts', 'test'].flatMap((d) => walk(path.join(ROOT, d)))].filter((f) => f.endsWith('.md'));
const linkRe = /\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)/g;
for (const f of mdFiles) {
    const text = fs.readFileSync(f, 'utf8');
    for (const m of text.matchAll(linkRe)) {
        const t = m[1];
        if (/^[a-z]+:/.test(t) || t.startsWith('/')) continue;
        const target = path.resolve(path.dirname(f), t);
        if (!fs.existsSync(target)) problems.push(`broken link in ${rel(f)}: ${t}`);
    }
}

if (problems.length) {
    console.error(problems.join('\n'));
    console.error(`\n${problems.length} orphan(s)`);
    process.exit(1);
}
console.log(`links: none broken (${mdFiles.length} markdown files checked)`);

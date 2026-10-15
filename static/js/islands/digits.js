// Pure helpers for the demo page, tested in tests/test-digits.js.

// Leading significant digits of `value` that literally equal `truth`'s: the
// same rule as `agree` in scripts/ladder/ladder.py. A reading aid for the
// highlight, not a precision measure (a carry across 0.999…/1.000… gives 0).
export function agree(value, truth) {
    const neg = (s) => s.startsWith('-');
    if (neg(value) !== neg(truth)) return 0;
    const parts = (s) => {
        s = s.replace('-', '');
        const [ip, fp = ''] = s.split('.');
        const intDigits = ip.replace(/^0+/, '');
        if (intDigits) return { decade: intDigits.length, sig: intDigits + fp };
        const lead = fp.match(/^0*/)[0].length;
        return { decade: -lead, sig: fp.slice(lead) };
    };
    const a = parts(value), b = parts(truth);
    if (a.decade !== b.decade) return 0;
    let n = 0;
    while (n < a.sig.length && n < b.sig.length && a.sig[n] === b.sig[n]) n++;
    return Math.min(n, 42);
}

// Split a printed value into the agreeing prefix and the rest, by `agree` count.
export function splitByAgree(value, count) {
    if (count <= 0) return { matched: '', rest: value };
    let seen = 0, i = 0;
    for (; i < value.length; i++) {
        const ch = value[i];
        if (ch >= '1' && ch <= '9') seen++;
        else if (ch === '0' && seen > 0) seen++;
        if (seen === count) { i++; break; }
    }
    return { matched: value.slice(0, i), rest: value.slice(i) };
}

// Decode a raw library word into a decimal string with `places` fractional digits.
export function decodeRaw(raw, scale, places = 40) {
    let x = BigInt(raw);
    const neg = x < 0n;
    if (neg) x = -x;
    const s = BigInt(scale);
    const ip = x / s;
    const fp = ((x % s) * 10n ** BigInt(places)) / s;
    const frac = fp.toString().padStart(places, '0').replace(/0+$/, '');
    return (neg ? '-' : '') + ip.toString() + (frac ? '.' + frac : '');
}

// ABI encoding of run(uint8 scenario, uint8 form, uint32 n, int256[] p).
const MASK = (1n << 256n) - 1n;
const word = (x) => (BigInt(x) & MASK).toString(16).padStart(64, '0');
export function encodeRun(selector, scenario, form, n, p) {
    const head = word(scenario) + word(form) + word(n) + word(0x80);
    const tail = word(p.length) + p.map(word).join('');
    return selector + head + tail;
}

export function decodeRun(hex) {
    const out = hex.startsWith('0x') ? hex.slice(2) : hex;
    if (out.length < 320) throw new Error('short return data');
    const signed = (h) => { let x = BigInt('0x' + h); if (x >= 1n << 255n) x -= 1n << 256n; return x; };
    return {
        ok: BigInt('0x' + out.slice(0, 64)) === 1n,
        raw: signed(out.slice(64, 128)),
        reason: '0x' + out.slice(128, 136),
        gasPerStep: BigInt('0x' + out.slice(192, 256)),
        gasTotal: BigInt('0x' + out.slice(256, 320)),
    };
}

// ABI encoding of EdgeRunner.run(uint8 op, uint8 form, int256[] args) and its
// (bool ok, int256 raw, bytes4 reason, uint256 gas) return.
export function encodeOp(selector, op, form, args) {
    const head = word(op) + word(form) + word(0x60);
    const tail = word(args.length) + args.map(word).join('');
    return selector + head + tail;
}

export function decodeOp(hex) {
    const out = hex.startsWith('0x') ? hex.slice(2) : hex;
    if (out.length < 256) throw new Error('short return data');
    const signed = (h) => { let x = BigInt('0x' + h); if (x >= 1n << 255n) x -= 1n << 256n; return x; };
    return {
        ok: BigInt('0x' + out.slice(0, 64)) === 1n,
        raw: signed(out.slice(64, 128)),
        reason: '0x' + out.slice(128, 136),
        gas: BigInt('0x' + out.slice(192, 256)),
    };
}

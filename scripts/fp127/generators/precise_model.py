#!/usr/bin/env python3
"""Integer model of the FP127 v5 precise kernels, as the Yul runs them, with
the constants they need and a measurement against mpmath.

    uv run scripts/fp127/generators/precise_model.py constants   # print the Yul constants
    uv run scripts/fp127/generators/precise_model.py measure [n] # kernel errors on n random inputs
    uv run scripts/fp127/generators/precise_model.py fastpow [n] # pow / cbrt's one-word test (pow2t)
    uv run scripts/fp127/generators/precise_model.py lambertw [d] # Lambert W's seeds and Halley step counts

The v5 kernels work on a double word (DW): a pair (hi, lo) read as
(hi * 2^256 + lo) * 2^-512, a fraction in [0, 1) held to 2^-512.

  expk(r)   e^r - 1 for r in [0, ln 2) as a DW: expk.py's model of the
            Yul (three 16-entry table levels and the degree-16 minimax
            polynomial of (e^u - 1 - u)/u^2, in X form, never above the
            truth; within 2^-311 relative). The Yul takes r in X form, rh
            2^-256 + rx 2^-384, as lnmul and expr give it (expkx here).
  expr(x)   e^x's reduction, x = n ln 2 + r, from a one-word log2 e and
            one correcting test (exp and the expx callers).
  l2p(x)    log2(x) for x > 0 as a 512-bit signed integer at 2^-384 (X384:
            hi word in the 127.128 format, lo the next 256 bits). One Newton
            step from the one-word log2 kernel y0 (2^-150): with
            d = m 2^-y0 - 1 computed through expk, log2(m) = y0 + log2(1 + d).
            Error about 2^-299 absolute.

  pow2t(t)  pow and cbrt's first try: 2^t in one word (exp2frac, 2^-145
            relative) for t = y log2g(x) (or log2g(x) / 3), with an error
            bound eb in units of 2^-192 that covers this value's error and
            the double word's together; when the bits below the 2^-128 grid
            are more than eb from the midpoint, both round alike and the
            double word is skipped. fastpow checks the bound against the
            true error and the result against op_pow / op_cbrt.

  einvhalf  e^-x / 2 at 2^-192 from e^x = 2^n (1 + s), one divg on the top
            255 bits of s: with u = e^x - 1 it is (1 - u/(1+u)) / 2. op_sinh
            and op_cosh (sinh = (u + u/(1+u)) / 2, cosh = 1 + u (u/(1+u)) / 2,
            which is e^x / 2 -+ e^-x / 2) take the floored e^x / 2 from the
            kernel, subtract or add it and round once. Measured in units of
            2^-192 (less the kernel's 2^-299 relative) against the stated
            bound of 3: the two floors and the dropped bits of s.
  op_atanh  log1p(2x / (1 - x)) / 2: the quotient at 2^-192 by one divg, one
            log2g of 2^192 + it (a 127.128 word worth 2^64 (1 + q)) less 64,
            times ln2 / 2. Measured against 2^-146 + 2 units (the Yul's
            rbad127 err is 2^47, which also covers the two-log form near 1).
            atanh_mid is the middle stage behind that test: l2p of 1 + x
            and 1 - x, times ln 2 / 2 at 2^-256 (bounds127.py, err 2^137 at
            2^-384).
  op_tanh   u / (u + 2) below 1/4, u = e^2x - 1 from the kernel (from
            2^-5) or expm1s; (1 - w) / (1 + w), w = e^-2x, from 1/4: one
            divg at 2^-192 (tanh_pre gives the value and its rbad127 err).

  lambertw  Lambert W's one-word stages in integers, as the Yul runs them:
            the seeds (a crude logarithm), the fourth-order log-form steps
            at 2^-126 or the sixth-order steps in q = 1 + W near -1/e, and
            the correct bits left for the double-word step lwfin,
            -log2(|w - W| / max(1, |W|)), with where lwfin's Newton step
            lands, -log2(err^2 / |1 + W|), worst over a grid of d points per
            octave: at least 88 before and 176 after in every region.

Every product floors, every shift drops bits below the grid, exactly as the
Yul; Python's >> floors signed integers as Yul's sar does.
"""
from __future__ import annotations

import random
import sys

from mpmath import mp, mpf, log, exp, e as E_, nint, lambertw, sqrt as msqrt

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import kernel192  # noqa: E402
import expk as expk_model  # noqa: E402

mp.dps = 220

T256 = 1 << 256
M256 = T256 - 1
M512 = (1 << 512) - 1
ONE = 1 << 128
G = 1 << 192
H255 = 1 << 255


def fx(v, bits):
    """nearest integer to v * 2^bits"""
    return int(nint(v * mpf(2) ** bits))


# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

LN2_512 = fx(log(2), 512)
LN2H, LN2L = LN2_512 >> 256, LN2_512 & M256
LN10_512 = fx(log(10) - 2, 512)            # ln 10 = 2 + this
LN10H, LN10L = LN10_512 >> 256, LN10_512 & M256
# e^(v 4^-(g+1)) - 1 for the eight 2-bit groups of r's top 16 bits, v = 1..3
EXPC = [[fx(exp(mpf(v) / mpf(4) ** (g + 1)) - 1, 512) for v in (1, 2, 3)] for g in range(8)]
LOG2E_255 = fx(1 / log(2), 255)
LN2_256 = fx(log(2), 256)
LOG10_2_256 = fx(log(2) / log(10), 256)
E254 = fx(E_, 254)
# existing one-word constants (2^-192), copied from FP127.yul.src
LOG2E_192 = 0x171547652b82fe1777d0ffda0d23a7d11d6aef551bad2b4b1
LOG2_10_192 = 0x35269e12f346e2bf924afdbfd36bf6d3365b157f8deceb53a
LN2_192 = 0xb17217f7d1cf79abc9e3b39803f2f6af40f343267298b62e
LOG10_2_192 = 0x4d104d427de7fbcc47c4acd605be48bc13569862a1e8f9a5



def sgn(w):
    w &= M256
    return w - T256 if w >> 255 else w


def mulg(a, b):
    return (sgn(a) * sgn(b)) >> 192


# ---------------------------------------------------------------------------
# kernels
# ---------------------------------------------------------------------------

def expk(r: int) -> int:
    """e^r - 1 at 2^-512 for r in [0, ln 2) at 2^-512 (both as 512-bit ints):
    expk.py's model of the Yul."""
    return expk_model.expk(r)


def expkx(rh: int, rx: int) -> int:
    """The same for r = rh 2^-256 + rx 2^-384 (X form, as the Yul takes it)."""
    return expk_model.expkx(rh, rx)


LN2A, LN2B = LN2H, LN2L >> 128           # ln 2 floored at 2^-256 and the next 128 bits
LOG2E_119 = 0xb8aa3b295c17f0bbbe87fed0691d3e


def lnmul(F: int):
    """The Yul's lnmul: f ln 2 in X form for f = F 2^-512, floored."""
    fh, fl = F >> 256, F & M256
    p = fh * LN2H
    rx = ((p & M256) >> 128) + (((fh >> 128) * LN2B) >> 128) + (((fl >> 128) * (LN2H >> 128)) >> 128)
    return p >> 256, rx


def expr(X: int):
    """The Yul's expr: x = n ln 2 + r for |x| < 177, r in X form."""
    pr = X * LOG2E_119
    assert abs(pr) < 1 << 255
    n = pr >> 247
    v = n * LN2B
    rh = ((X << 128) - n * LN2A - (v >> 128) - 1) & M256
    rx = (1 << 128) - (v & ((1 << 128) - 1))
    if rh > LN2A:
        if rh > 0xc << 252:
            n, rh, rx = n - 1, (rh + LN2A) & M256, rx + LN2B
        else:
            n, rh, rx = n + 1, (rh - LN2A - 1) & M256, rx + (1 << 128) - LN2B
    assert 0 <= rh < LN2A
    return n, rh, rx


def pow2tail(n: int, sh: int):
    """The Yul's rounding of 2^n (1 + s) at 2^-128 from sh alone, e = n + 129
    in [0, 255]: half of 2^e + floor(sh 2^(e - 256)) + 1; 2^256 (wrapped to
    0 in the Yul) is Overflow."""
    e = n + 129
    assert 0 <= e <= 255
    v = (1 << e) + (sh >> (256 - e)) + 1
    return "REVERT" if v >> 256 else v >> 1


def y2nf(Y: int, L: int):
    """n = floor(y L) and f = y L - n at 2^-512 for L a log2 at 2^-384."""
    t = Y * L
    return t >> 512, t & M512


LOG2E_384 = (0x171547652b82fe1777d0ffda0d23a7d11 << 256) | 0xd6aef551bad2b4b1164a2cd9a342648fbc3887eeaa2ed9ac49b25eeb82d7c168
LOG2_10_384 = (0x35269e12f346e2bf924afdbfd36bf6d33 << 256) | 0x65b157f8deceb53a46dab2020b9e167419943f7a77547ce8f892faad8eb42f58


def log2m(mm: int) -> int:
    """log2(m) at 2^-192 for m = mm 2^-192 in [1, 2): kernel192.py's model of
    the Yul (two additive table levels and a degree-14 minimax polynomial)."""
    return kernel192.log2m(mm)


def msb(x):
    return x.bit_length() - 1


def log2g(X: int) -> int:
    """v5 one-word log2 at 2^-192: the mantissa is normalised at 2^-192 before
    any bit is dropped (v4 normalised at 2^-128 and lost up to 127 bits)."""
    m = msb(X)
    if X & (X - 1) == 0:
        return (m - 128) << 192
    mm = X >> (m - 192) if m >= 192 else X << (192 - m)
    return ((m - 128) << 192) + log2m(mm)


def l2p(X: int) -> int:
    """log2(X 2^-128) at 2^-384 as a signed integer."""
    ms = msb(X)
    e = ms - 128
    M = X << (255 - ms)
    if M == H255:
        return e << 384
    y0 = log2m(M >> 63)
    y0 = min(max(y0, 1), G - 1)
    f = G - y0                                    # 2^(-y0) = 2^(f - 1)
    s = expkx(*lnmul(f << 320))
    sh, sl = s >> 256, s & M256
    q = ((M << 256) + M * sh + ((M * sl) >> 256)) & M512
    d = q - (1 << 512) if q >> 511 else q          # d = delta * 2^512
    d384 = d >> 128
    d2 = (d384 * d384) >> 385
    corr = ((d384 - d2) * LOG2E_255) >> 255
    return (e << 384) + (y0 << 192) + corr


def scaled192(n: int, s: int) -> int:
    """floor(2^(n + 192) (1 + s 2^-512)) for n >= -192"""
    e = n + 192
    return (1 << e) + ((s << e) >> 512) if e >= 0 else 0


def rnd64(v: int) -> int:
    return (v + (1 << 63)) >> 64


# ---------------------------------------------------------------------------
# ops
# ---------------------------------------------------------------------------

def exp_parts(X: int):
    """expx: e^x = 2^n (1 + s)."""
    n, rh, rx = expr(X)
    return n, expkx(rh, rx)


def op_exp(X):
    if X == 0:
        return ONE
    if X > 88 * ONE:
        return "REVERT"
    if X < -90 * ONE:
        return 0
    n, rh, rx = expr(X)
    if n < -129:
        return 0
    return pow2tail(n, expkx(rh, rx) >> 256)


def op_exp2(X):
    if X >= 127 * ONE:
        return "REVERT"
    if X < -129 * ONE:
        return 0
    return pow2tail(X >> 128, expkx(*lnmul(((X << 128) & M256) << 256)) >> 256)


def pow2r(Y: int, L: int):
    """The Yul's pow2r: 2^(y L) rounded to nearest, L at 2^-384."""
    n, f = y2nf(Y, L)
    if n > 126:
        return "REVERT"
    if n < -129:
        return 0
    return pow2tail(n, expkx(*lnmul(f)) >> 256)


def op_exp10(X):
    return pow2r(X, LOG2_10_384)


def x384_round(L):
    return (L + (1 << 255)) >> 256


def op_log2_precise(X):
    return x384_round(l2p(X))


def op_ln_precise(X):
    L = l2p(X)
    return x384_round((L * LN2_256) >> 256)


def op_pow(X, Y):
    """pow's double-word route (l2p, then pow2r)."""
    return pow2r(Y, l2p(X))


def op_cbrt(X):
    neg = X < 0
    L = l2p(abs(X))
    li = L >> 384
    q, rem = divmod(li, 3)
    frac = ((rem << 384) + (L & ((1 << 384) - 1))) << 128
    f = frac // 3
    r = (f * LN2_512) >> 512
    v = rnd64(scaled192(q, expk(r)))
    return -v if neg else v


# ---------------------------------------------------------------------------
# the hyperbolics from the exp and log kernels
# ---------------------------------------------------------------------------

LN2_HALF_192 = 0x58b90bfbe8e7bcd5e4f1d9cc01f97b57a079a193394c5b17


def divg(a: int, b: int) -> int:
    """floor(a 2^192 / b), the Yul's two-stage divu (requires a >> 128 < b)."""
    assert (a >> 128) < b
    return (a << 192) // b


def einvhalf(n: int, s: int) -> int:
    """e^-x / 2 at 2^-192 from e^x = 2^n (1 + s): floor(2^(254-n) 2^192 /
    (2^255 + floor(s_hi / 2))), one divg."""
    return divg(1 << (254 - n), H255 | ((s >> 256) >> 1))


def sc192(n: int, s: int) -> int:
    """The Yul's sc192 as one integer: floor(2^(n + 192) (1 + s 2^-512)),
    except below e = n + 192 = 256, where it reads only s's high word."""
    e = n + 192
    if e < 256:
        return (1 << e) + ((s >> 256) >> (256 - e))
    return scaled192(n, s)


def hyp_pre(ax: int, sign: int) -> int:
    """cosh (sign 1) or sinh (sign -1) at 2^-192 before the rounding."""
    n, s = exp_parts(ax)
    return sc192(n - 1, s) + sign * einvhalf(n, s)


HYP_ERR = 1 << 20      # sinh's and cosh's rbad127 err in the Yul


def hyp_err(V: int) -> int:
    """The derived bound on |V - exact| for sinh's and cosh's V = (vh, vl):
    4 + vh / 2^43 (3 units and 2^-299 of e^|x| / 2), under HYP_ERR, which
    the Yul passes (a constant lets solc inline rbad127), on |x| <= 88."""
    return 4 + (V >> 299)


def op_cosh(X: int):
    ax = abs(X)
    if ax > 88 * ONE:
        return "REVERT"
    if ax < 1 << 64:
        return ONE
    return rnd64(hyp_pre(ax, 1))


def op_sinh(X: int):
    ax = abs(X)
    if ax > 88 * ONE:
        return "REVERT"
    r = ax if ax < 1 << 63 else rnd64(hyp_pre(ax, -1))
    return -r if X < 0 else r


def expm1s(x: int, ax: int) -> int:
    """The Yul's expm1s: e^x - 1 at 2^-192 for x at 2^-128, |x| <= 1/16, by
    the Horner series (each step floors the product, truncates the quotient)."""
    xs = x << 64
    k = 27
    if ax < 1 << 122:
        k = 22
        for lim, kk in ((1 << 120, 18), (1 << 116, 14), (1 << 112, 11), (1 << 104, 8), (1 << 96, 6), (1 << 80, 5)):
            if ax < lim:
                k = kk
    v = G
    while k > 1:
        v = G + sdiv((xs * v) >> 192, k)
        k -= 1
    return mulg(xs, v)


def tanh_pre(ax: int):
    """tanh(x) at 2^-192 before the rounding for 2^-65 <= |x| < 46 and its
    rbad127 err: u / (u + 2) below 1/4 (u = e^2|x| - 1 from the kernel from
    2^-5, else expm1s), (1 - w) / (1 + w) with w = e^-2|x| beyond. Returns
    (V, err, region)."""
    if ax < 1 << 126:
        if ax > 1 << 123:
            n, s = exp_parts(2 * ax)
            u, reg = sc192(n, s) - G, "kernel"
        else:
            u, reg = expm1s(2 * ax, 2 * ax), "expm1s"
        return divg(u, u + 2 * G), 2, reg
    n, s = exp_parts(-2 * ax)
    w = sc192(n, s)
    return divg(G - w, G + w), 3, "w"


def op_tanh(X: int):
    """tanh's fast path, rounded (the Yul's second stage decides where V's
    err reaches the boundary; this model does not run it)."""
    ax = abs(X)
    if ax == 0:
        return 0
    if ax < 1 << 63:
        return X
    r = ONE if ax >= 46 * ONE else rnd64(tanh_pre(ax)[0])
    return -r if X < 0 else r


def atanh_pre(ax: int) -> int:
    """atanh(x) at 2^-192 before the rounding, 0 < x < 1 (ax in 127.128)."""
    if ax < ONE - (1 << 66):
        q = G + divg(2 * ax, ONE - ax)
        l2 = log2g(q) - (64 << 192)
    else:
        l2 = log2g(ONE + ax) - log2g(ONE - ax)
    return (l2 * LN2_HALF_192) >> 192


LN2_HALF_256 = 0x58b90bfbe8e7bcd5e4f1d9cc01f97b57a079a193394c5b16c5068badc5d57d15   # ln 2 / 2, floored


def atanh_mid(ax: int) -> int:
    """atanh's middle stage at 2^-384 (atanhmid): (l2p(1 + x) - l2p(1 - x))
    times ln 2 / 2 at 2^-256, the low word's product through its high word."""
    L = l2p(ONE + ax) - l2p(ONE - ax)
    lh, ll = L >> 256, L & M256
    return lh * LN2_HALF_256 + ((ll * LN2_HALF_256) >> 256)


def op_atanh(X: int):
    ax = abs(X)
    if ax >= ONE:
        return "REVERT"
    if X == 0:
        return 0
    r = rnd64(atanh_pre(ax))
    return -r if X < 0 else r


# ---------------------------------------------------------------------------
# pow and cbrt: the one-word value first (pow2t)
# ---------------------------------------------------------------------------

def exp2frac(f: int) -> int:
    """2^f at 2^-192 for f in [0, 2^192): kernel192.py's model of the Yul
    (a 16-entry table and a degree-15 minimax polynomial)."""
    return kernel192.exp2frac(f)


def pow2t(t: int, ay: int):
    """(r, ok, v, eb) as the Yul's pow2t: v = 2^t at 2^-192, eb its bound."""
    at = abs(t)
    k = at >> 192
    e = k + 1 if t >= 0 else -k
    eb = ((ay >> (80 - e)) if e <= 80 else 0) + ((1 << (e + 48)) if e + 48 >= 0 else 0) + 6
    if eb > 1 << 61:
        return None, 0, None, eb
    f = at & (G - 1)
    if t >= 0:
        v = exp2frac(f) << k
    elif f == 0:
        v = G >> k
    else:
        v = exp2frac(G - f) >> (k + 1)
    ok = abs((v & ((1 << 64) - 1)) - (1 << 63)) > eb
    return (v + (1 << 63)) >> 64, ok, v, eb


def pow_pre(X, Y):
    """op_pow's value at 2^-192 before its rounding (None where it reverts or returns 0)."""
    L = l2p(X)
    t = Y * L
    n, f = t >> 512, t & M512
    if n >= 127 or n < -130:
        return None
    return scaled192(n, expkx(*lnmul(f)))


def cbrt_pre(X):
    L = l2p(abs(X))
    li = L >> 384
    q, rem = divmod(li, 3)
    f = (((rem << 384) + (L & ((1 << 384) - 1))) << 128) // 3
    return scaled192(q, expk((f * LN2_512) >> 512))


def fastpow(n=20000):
    """On random pow and cbrt inputs: whenever pow2t says ok, its word equals
    op_pow's (op_cbrt's), and the true errors of both values before rounding
    together stay under eb. Prints the largest ratio (true error / eb)."""
    rng = random.Random(7)
    worst, taken, total = mpf(0), 0, 0
    for i in range(n):
        if i % 2 == 0:
            X = rng.getrandbits(rng.randint(120, 136)) | 1
            Y = rng.getrandbits(rng.randint(60, 140))
            if i % 6 == 0:                         # near one with a large exponent
                X = ONE + rng.getrandbits(rng.randint(1, 100)) * rng.choice([1, -1])
                Y = rng.getrandbits(rng.randint(128, 200))
            Y = -Y if rng.random() < 0.5 else Y
            if X <= 0 or X == ONE:
                continue
            L = log2g(X)
            t = (Y * L) >> 128
            if abs(t) >= 1 << 198:
                continue
            r, ok, v, eb = pow2t(t, abs(Y))
            truth = mp.power(mpf(X) / ONE, mpf(Y) / ONE) * G
            pre = pow_pre(X, Y)
            want = op_pow(X, Y)
        else:
            X = rng.getrandbits(rng.randint(1, 254)) | 1
            L = log2g(X)
            t = L // 3 if L >= 0 else -(-L // 3)           # sdiv truncates
            r, ok, v, eb = pow2t(t, ONE)
            truth = mp.cbrt(mpf(X) / ONE) * G
            pre = cbrt_pre(X)
            want = op_cbrt(X)
        total += 1
        if not ok:
            continue
        taken += 1
        assert r == want, (X, r, want)
        err = abs(mpf(v) - truth) + (abs(mpf(pre) - truth) if pre is not None else 1)
        worst = max(worst, err / eb)
    print(f"pow2t: {taken} of {total} inputs decided in one word, every one equal to the double word's; "
          f"largest (true error of both values) / eb = {mp.nstr(worst, 4)}")


def fastcompound(n=20000):
    """compound's one-word route (compt): on random rates (per-second to 2^-1,
    both signs) and periods (16 to 2^31, both signs), whenever pow2t says ok
    its word is the nearest word of the exact (1 + rate)^k, and the true
    error of v stays under eb. Prints the share decided and the largest
    (true error / eb)."""
    rng = random.Random(11)
    worst, taken, total = mpf(0), 0, 0
    worst2, taken2 = mpf(0), 0
    for i in range(n):
        rate = rng.getrandbits(rng.randint(40, 127)) * rng.choice([1, 1, -1])
        if i % 5 == 0:
            rate = rng.getrandbits(rng.randint(100, 135))
        k = rng.randint(16, 1 << rng.randint(5, 31)) * rng.choice([1, 1, -1])
        X = ONE + rate
        if X <= 0 or X >= 1 << 255:
            continue
        L = log2g(X)
        t = k * L
        truth = mp.power(mpf(X) / ONE, k) * G
        want = int(mp.floor(truth / (1 << 64) + mpf(1) / 2))
        if abs(t) >= 1 << 199:                       # decided by t's sign and size alone
            if t > 0:
                assert want >= 1 << 255, (rate, k)  # Overflow
            elif t < -(130 << 192):
                assert want == 0, (rate, k)
            continue
        total += 1
        r, ok, v, eb = pow2t(t, (abs(k) << 113) + 1)
        if ok:
            taken += 1
            assert r == want, (rate, k, r, want)
            worst = max(worst, abs(mpf(v) - truth) / eb)
            continue
        r2, ok2, V, eb2, unit = pow2rt(k << 128, l2p(X), (abs(k) >> 42) + 3)
        if not ok2:
            continue
        taken2 += 1
        assert r2 == want, (rate, k, r2, want)
        if V is not None:
            worst2 = max(worst2, abs(V - truth / G * mpf(2) ** 129) / unit / eb2)
    print(f"compt: {taken} of {total} inputs decided in one word, every one the nearest word; "
          f"largest (true error of v) / eb = {mp.nstr(worst, 4)}")
    print(f"pow2rt: {taken2} of the other {total - taken} decided at 2^-299, every one the nearest word; "
          f"largest (true error of V) / eb = {mp.nstr(worst2, 4)}")


def pow2rt(Y: int, L: int, eb: int):
    """(r, ok, V, eb, unit) as the Yul's pow2rt: V = 2^e + sh 2^(e - 256), the
    value the Yul halves, in units of 2^-128 (twice the result's scale), and
    unit sh's last bit in the same units (V None where it decides without one)."""
    n, f = y2nf(Y, L)
    if n > 126:
        return None, 0, None, eb, None
    if n < -129:
        return 0, int(n < -130), None, eb, None
    sh = expkx(*lnmul(f)) >> 256
    e = n + 129
    sb = 256 - e
    w = (1 << e) + (sh >> sb) + 1
    r = w >> 1
    if w >> 256:
        return None, 0, None, eb, None
    d = sh & ((1 << sb) - 1)
    if w & 1:
        d = (1 << sb) - d
    V = (mpf(1) + mpf(sh) / mpf(2) ** 256) * mpf(2) ** e
    return r, int(d > eb), V, eb, mpf(2) ** (e - 256)


# ---------------------------------------------------------------------------
# Lambert W: the one-word stages before lwfin, as the Yul forms them (v6)
# ---------------------------------------------------------------------------

LN2_128 = 0xb17217f7d1cf79abc9e3b39803f2f6af
SQRT2_126 = 0x5a827999fcef32422cbec4d9baa55f50
E_254 = 0xadf85458a2bb4a9aafdc5620273d3cf1d8b9c583ce2d3695a9e13641146433fb


def sdiv(a, b):
    """Yul's sdiv: truncation toward zero."""
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


T_STAGES = [(0x5a827999fcef32422cbec4d9baa55f50, 0x2d413cccfe779921165f626cdd52afa8, 32),
            (0x4c1bf828c6dc54b7a356918c17217b7b, 0x35d13f32b5a75abd0e69a2ee640b4ff8, 16),
            (0x45cae0f1f545eb737df23143ac529e48, 0x3ab031b9f7490e4bb40b5d6cdc1b953f, 8),
            (0x42d561b3e6243d8a62e4adc610aa60d9, 0x3d495f454921b30b1ee7431ebb6603f1, 4),
            (0x4166c34c5615d0eb9f1523ada3290600, 0x3ea0ecb6dc8a80ce9f096ec50c575ff3, 2),
            (0x40b268f9de0183b9bdf2b293de8a6f7a, 0x3f4f83033d21b05d214fce964c783b81, 1)]
ATANH_C = [0x4446135483304695b31cd2087781804, 0x4ec4ec491eccde6dc9ec3dc71cf3623, 0x5d1745d1746646dc577e7d058db642b,
           0x71c71c71c71c71bed60c1d9b8a55f08, 0x92492492492492492496556bf318f39, 0xcccccccccccccccccccccccbd3dcdb3,
           0x155555555555555555555555555556c2, 0x40000000000000000000000000000000]
LN2_122 = 0x2c5c85fdf473de6af278ece600fcbdb
LNC0 = [0x6c624f4ace937ad74c72c1900aebb69, -0x193a803a4689b1e7d4fe8cc4f525bca5, 0x3ecce60a25db5c9757959e657fdbf429, 0x95fd7e22848b1d16f2f2bb6adf6c7]
LWSP = [0x53b90081353ec0d6941c921fcfafe595a00cc42497241ae655363581fda94, -0x7da26a79225bb5fb50ea8efcc8ae9d4254e4dc4f946a07e0bfe6de0579346,
        0x644585809454cf76ef165d39ed6b3221e9ba088251003ceff2f71f7c0c755, -0x98b8b6e30746fa914f48ce0a496b7a037105c06bb06c9d7f684c61cf6fd46,
        0x110d843b49b21ba51a501bbb77ed0f257949b9cc213a87345be9ca07b63737, -0x1a313459af0764ab9552879fb1e10f9bf22264fb538a1aa117eae1bb53021a,
        0x27f5807beecdf9efb8c709fad4296181f19ead87c6548eb20db7222ab50a4c, -0x3e656398e74c5d03b4b5df785dc1c426dcc98ec31e23a08ebd7c71dc546983,
        0x628b743708e2d24266d1587a51d9c728881f97fd4201e6904b1872252776b5, -0x9d911c278f1cb7b3ed76e932800a7853179177003af08ad833049761583efd,
        0x1002c921ab74cdbe4d174f50d821165e87a6ad194e0c48cc71d0e1d0a3a51bb, -0x1a9bbc1771a4a40ca538aa8217e0e6417f0eebd3b401221c91c8d7a77ccffbb,
        0x2d9203ccc4cd1b7ae3baee267b661786f46d8800613ee614953eb058ced39ae, -0x518a6dfefd1f0da4f26b457422d5955b99bbeb25c7a90c9258e8aaf51a88dc3,
        0x9c71c71c6f490046c1d5e4523fc72a7e7eebcd533f42e92e99d9f2e603d55fc, -0x155555555519dbb6d739a70acc0e3d8ec423a092398259b8ab5412b03b634978,
        1 << 254]


def lw_lnc(r, k):
    """The Yul's lnc: k ln 2 + ln r at 2^-128, r in [2^126, 2^127): six table reductions,
    then 2 s atanh(s)/s with the degree-7 fit in s^2 (lncfit certifies it)."""
    j = 64 * k
    for T, I, dj in T_STAGES:
        if r >= T:
            r = (r * I) >> 126
            j += dj
    s = sdiv((r - (1 << 126)) << 126, r + (1 << 126))
    s2 = (s * s) >> 126
    A = ATANH_C[0]
    for c in ATANH_C[1:]:
        A = c + ((s2 * A) >> 126)
    return j * LN2_122 + (((s * A) >> 125) << 2)


def lw_lnc0(r, k):
    """The Yul's lnc0: the crude logarithm for the seeds (a degree-3 fit, 2^-10.8)."""
    t = r - (1 << 126)
    P = LNC0[0]
    for c in LNC0[1:]:
        P = c + ((P * t) >> 126)
    return k * LN2_128 + (P << 2)


def lw_lnm(v):
    n = msb(v)
    r = v >> (n - 126) if n >= 126 else v << (126 - n)
    return r, n - 128


def lw_sp(p, S):
    """The Yul's lwsp: S(p) = (1 + W)/p by the degree-16 fit, Horner at 2^-S on p at 2^-S."""
    v = LWSP[0] >> (254 - S)
    for c in LWSP[1:]:
        v = (c >> (254 - S) if c >= 0 else -((-c) >> (254 - S))) + ((p * v) >> S)
    return v


def lw_lncfit():
    """lnc's and lwsp's fits certified: the Yul's constants are the rounded chebyfit
    coefficients, and the fits' sup norms on dense grids are what the Yul claims."""
    from mpmath import chebyfit, atanh, lambertw, e as Ee, sqrt as msqrt, power, nint, mpf, log
    mp.dps = 90
    smax = (power(2, mpf(1) / 64) - 1) / (power(2, mpf(1) / 64) + 1)
    g = lambda u: atanh(msqrt(u)) / msqrt(u) if u > 0 else mpf(1)
    ap = chebyfit(g, [mpf(0), smax ** 2], 8)
    assert [int(nint(c * mpf(2) ** 126)) for c in ap] == ATANH_C, "lnc's fit"
    worst = max(abs(sum(c * (smax ** 2 * i / 4000) ** (7 - j) for j, c in enumerate(ap)) - g(smax ** 2 * i / 4000)) for i in range(4001))
    print(f"lnc: atanh(s)/s by the degree-7 fit within 2^{float(log(worst, 2)):.1f} on [0, {float(smax):.5f}]^2")
    S = lambda p: (1 + lambertw((p * p / 2 - 1) / Ee, 0 if p > 0 else -1).real) / p if p != 0 else mpf(1)
    sp = chebyfit(S, [-mpf(1) / 2, mpf(1) / 2], 17)
    assert [int(nint(c * mpf(2) ** 254)) for c in sp] == LWSP, "lwsp's fit"
    worst2 = max(abs(sum(c * (mpf(i) / 4000) ** (16 - j) for j, c in enumerate(sp)) / S(mpf(i) / 4000) - 1) for i in range(-2000, 2001))
    print(f"lwsp: S(p) by the degree-16 fit within 2^{float(log(worst2, 2)):.1f} relative on [-1/2, 1/2]")
    mp.dps = 120
    return worst > mpf(2) ** -138 or worst2 > mpf(2) ** -44.5


def lw_f127(x, w):
    """The Yul's lwf127: the fourth-order log-form step at 2^-126, (w', |u| 2^128)."""
    aw, ax = abs(w), abs(x)
    nw, nx = msb(aw), msb(ax)
    k = nw - nx
    r = ((aw << (255 - nw)) >> 3) // ((ax << (255 - nx)) >> 129)
    if r < 1 << 126:
        r <<= 1
        k -= 1
    hs = (w + ONE) >> 28
    u = sdiv((w + lw_lnc(r, k)) << 100, hs)
    v = sdiv(u << 100, hs)
    uv = (u * v) >> 128
    fac = ONE - u + (uv >> 1) - (((uv * v) >> 128) >> 1) + sdiv((((u * u) >> 128) * v) >> 128, 3)
    return (w * fac) >> 128, abs(u)


def lw_fast(x, w):
    n = 0
    for _ in range(4):
        w, au = lw_f127(x, w)
        n += 1
        if au < 1 << 106:
            break
    return w, n


def lw_b3(qa, tau):
    """The Yul's lwb3: b3 + tau (b4 + tau b5) at 2^-112, q and tau at 2^-126."""
    C = lambda n: n << 112
    m = lambda a, b: (a * b) >> 126
    h = lambda co: __import__("functools").reduce(lambda acc, cc: C(cc) + m(qa, acc), co[1:], C(co[0]))
    v = sdiv(h([240, 1200, 3052, 4760, 4410, 1890]), 1440)
    v = sdiv(h([24, 96, 190, 210, 105]), 120) + m(tau, v)
    return sdiv(h([6, 18, 25, 15]), 24) + m(tau, v)


def lw_q(x):
    """The Yul's lwq: 1 + e x at 2^-256, floored (0 < x + 1/e)."""
    return ((x * E_254) >> 126) & M256


def lw_qs(q192, sg, q256):
    """The Yul's lwqs: one sixth-order step on the double-word exp kernel, (|q|', |tau|) at 2^-192."""
    G1 = 1 << 192
    if not sg:
        E1 = expkx(q192 << 64, 0) >> 256
    else:
        E1 = (T256 - (expkx(LN2H - (q192 << 64), LN2B) >> 256)) >> 1
    T = (E1 << 128) // q192
    N = G1 - mulg(T, G1 - q192) if not sg else mulg(T, G1 + q192) - G1
    d = ((q192 * N) >> 128) - q256
    ng = d < 0
    d = abs(d)
    E = G1 + (E1 >> 64) if not sg else G1 - (E1 >> 64)
    den = mulg((q192 * q192) >> 128, E)
    tau = divg(d, den)
    if ng:
        tau = -tau
    qa = -(q192 >> 66) if sg else q192 >> 66
    qs = -q192 if sg else q192
    C = lambda n: n << 192
    S = lw_b3(qa, tau >> 66) << 80
    S = sdiv(C(3) + mulg(qs, C(4) + mulg(qs, C(2))), 6) + mulg(tau, S)
    S = ((G1 + qs) >> 1) + mulg(tau, S)
    S = G1 + mulg(tau, S)
    return q192 - mulg(q192, mulg(tau, S)), abs(tau)


def lw_br(q, sg):
    """The Yul's lwbr: w = -1 +- q at 2^-128 from q = 1 + e x at 2^-256, and the step count."""
    nb = msb(q)
    Y = q << (254 - nb)
    ey = nb - 510
    k = 2 - (ey & 1)
    ep = ((ey - 254 + k) >> 1) + 128
    n = Y >> (1 + k)
    P = int(msqrt(mpf(n)))
    while P * P > n:
        P -= 1
    while (P + 1) * (P + 1) <= n:
        P += 1
    p = P << (ep + 192) if ep + 192 >= 0 else P >> (-ep - 192)
    if sg:
        p = -p
    qq = mulg(abs(p), lw_sp(p, 192))
    cnt = 0
    for _ in range(2):
        qq, at = lw_qs(qq, sg, q)
        cnt += 1
        if at < 1 << 148:
            break
    return qq, cnt


def lw_w0(x):
    """W0's one-word stages, as fp127_lambertW0 runs them: (w before lwfin, steps); near -1/e
    lw_br's (q at 2^-192, steps) instead."""
    if x < 0x20000000000000000000000000000000:
        if x < -0x5267adbd9d4543376382ee923e4a59ec:
            return lw_br(lw_q(x), 0)
        x2 = (x * x) >> 128
        w = x - x2 + ((x2 * (x + (x >> 1))) >> 128)
        if abs(x) < 1 << 87:
            return w, 0
        return lw_fast(x, w)
    L = lw_lnc0(*lw_lnm(ONE + x))
    l1 = lw_lnc0(*lw_lnm(ONE + L))
    t = sdiv(l1 << 100, (2 * ONE + L) >> 28)
    return lw_fast(x, L - (((L >> 18) * t) >> 110))


def lw_wm1(x):
    """W-1's one-word stages, as fp127_lambertWm1 runs them."""
    if x < -0x5267adbd9d4543376382ee923e4a59ec:
        return lw_br(lw_q(x), 1)
    lx = lw_lnc0(*lw_lnm(-x))
    ll = lw_lnc0(*lw_lnm(-lx))
    return lw_fast(x, lx - ll + sdiv(ll << 100, lx >> 28))


def div127(a, b):
    """The Yul's fp127_div: a 2^128 / b truncated toward zero."""
    return sdiv(a << 128, b)


def lw_fin(x, w):
    """The Yul's lwfin, 3.0: the double-word Newton step from w, its rounding
    test's operands and its word. Returns (r, v, err): the step's value is
    w 2^172 + v at 2^-300 (v = -d, the correction), err its bound in units of
    2^-300 (2^(2 msb|y| + msb|w| - 421) + |y| 2^-124 + 16), r the word nearest."""
    n, s = exp_parts(w)
    sh, sl = s >> 256, s & M256
    aw = abs(w)
    A = aw * sh + ((aw * sl) >> 256) + (aw << 256)
    ax = abs(x)
    B = ax << (256 - n)
    p = (A - B) >> 84
    assert abs(p) < H255, "lwfin's residual leaves its word"
    y = div127(p, B >> 256)
    ay = abs(y)
    f = y - (((ay * ay) >> 256) >> 45)
    d = div127((f * w) >> 128, w + ONE)
    v = -d
    t1 = 2 * msb(ay) + msb(aw) - 421 if ay else -1
    err = (1 << t1 if t1 >= 0 else 0) + (ay >> 124) + 16
    return w + ((v + (1 << 171)) >> 172), v, err


def lw_measure(d=8):
    """Away from -1/e: the correct bits lwfin starts from, -log2(|w - W| /
    max(1, |W|)), and where its Newton step lands, -log2(err^2 / |1 + W|),
    worst over a grid of d points per octave, by region and step count: at
    least 88 before (the fast stage stops at a step that starts within
    2^-22) and 176 after, far below the grid. Near -1/e (1 + e x < 1/8) the
    q form's result |q| at 2^-192 against 1 + W in units of 2^-192 (bound 5),
    so the word is nearest unless within 5 2^-64 ULP of a midpoint."""
    mp.dps = 300
    emin = -0x5e2d58d8b3bcdf1abadec7829054f90d
    bp = -0x5267adbd9d4543376382ee923e4a59ec
    pos = [fx(mpf(2) ** (k / d), 128) for k in range(-65 * d, 127 * d)]
    neg = [-fx(mpf(2) ** (-k / d), 128) for k in range(2 * d, 65 * d)]
    mid = [bp - int((mpf(bp - emin)) * (1 - mpf(2) ** -(k / d))) for k in range(1, 40 * d)]
    near = [emin + int(mpf(2) ** (128 - k / d)) for k in range(1, 128 * d) if emin + int(mpf(2) ** (128 - k / d)) < bp]
    small = [-fx(mpf(2) ** (-k / d), 128) for k in range(2 * d, 128 * d)]
    gen = [x for x in mid if x >= bp] + [-fx(mpf(2) ** (-k / d), 128) for k in range(int(1.64 * d), 3 * d)]
    bad = False
    for name, xs, run, br in (
            ("W0, x > 0", pos, lw_w0, 0), ("W0, -0.32 < x < 0", neg + gen, lw_w0, 0),
            ("W-1, -0.32 <= x < 0", small + gen, lw_wm1, -1)):
        by = {}
        for x in xs:
            if x < emin or x == 0 or x < bp:
                continue
            xv = mpf(x) / ONE
            W = lambertw(xv, br).real
            w, n = run(x)
            err = abs(mpf(w) / ONE - W) / max(1, abs(W))
            land = err * err / abs(1 + W)
            b = 999.0 if err == 0 else float(-log(err, 2))
            b2 = 999.0 if land == 0 else float(-log(land, 2))
            cur = by.get(n, (999.0, 999.0))
            by[n] = (min(cur[0], b), min(cur[1], b2))
        bad |= any(b < 88 or b2 < 176 for b, b2 in by.values())
        print(f"{name:22s} worst bits before lwfin (and after its squaring, err^2 / |1 + W|), by one-word steps: "
              + ", ".join(f"{n}: {b:.1f} ({b2:.0f})" for n, (b, b2) in sorted(by.items())))
    for name, br in (("W0, -1/e < x < -0.32", 0), ("W-1, -1/e < x < -0.32", 1)):
        worst, cnt = mpf(0), {}
        for x in [x for x in mid if x < bp] + near:
            if x < emin:
                continue
            xv = mpf(x) / ONE
            W = lambertw(xv, 0 if br == 0 else -1).real
            qq, n = lw_br(lw_q(x), br)
            e = abs(mpf(qq) / mpf(2) ** 192 - abs(1 + W)) * mpf(2) ** 192
            worst = max(worst, e)
            cnt[n] = cnt.get(n, 0) + 1
        bad |= worst > 5
        print(f"{name:22s} |q| within {float(worst):.3f} units of 2^-192 (bound 5), steps {cnt}")
    mp.dps = 220
    return bad or lw_lncfit()


# ---------------------------------------------------------------------------
# measurement
# ---------------------------------------------------------------------------

def ulp_err(got, truth):
    return abs(mpf(got) - truth)


def measure(n=2000):
    rng = random.Random(5)
    worst = {}

    def rec(name, err, inp):
        if name not in worst or err > worst[name][0]:
            worst[name] = (err, inp)

    for _ in range(n):
        # expk relative error
        r = rng.getrandbits(512) % LN2_512
        s = expk(r)
        tr = exp(mpf(r) / mpf(2) ** 512) - 1
        rec("expk (2^-512 units)", abs(mpf(s) - tr * mpf(2) ** 512), r)
        # l2p absolute error
        b = rng.randint(1, 254)
        X = rng.getrandbits(b) | (1 << b)
        L = l2p(X)
        tl = log(mpf(X) / ONE, 2)
        rec("l2p (2^-384 units)", abs(mpf(L) - tl * mpf(2) ** 384), X)
        # log2g absolute error at 2^-192
        rec("log2g (2^-192 units)", abs(mpf(log2g(X)) - tl * mpf(2) ** 192), X)
        # exp ULP error; a quarter of the draws next to m ln 2, where expr's
        # one-word n is one off and its test corrects it
        b = rng.randint(100, 134)
        x = rng.getrandbits(b) | (1 << b)
        if rng.random() < 0.25:
            x = (rng.randint(-129, 126) * LN2_512 >> 384) + rng.randint(-3, 3)
        x = -x if rng.random() < 0.5 else x
        got = op_exp(x)
        if got != "REVERT":
            rec("exp ULP", ulp_err(got, exp(mpf(x) / ONE) * ONE), x)
        got = op_ln_precise(X)
        rec("ln ULP", ulp_err(got, log(mpf(X) / ONE) * ONE), X)
        # pow
        xb = rng.getrandbits(130) | 1
        yb = rng.getrandbits(rng.randint(100, 134))
        yb = -yb if rng.random() < 0.5 else yb
        got = op_pow(xb, yb)
        if got != "REVERT":
            tv = mp.power(mpf(xb) / ONE, mpf(yb) / ONE) * ONE
            if tv < mpf(2) ** 255:
                rec("pow ULP", ulp_err(got, tv), (xb, yb))
        b = rng.randint(1, 254)
        c = rng.getrandbits(b) | (1 << b)
        got = op_cbrt(c)
        rec("cbrt ULP", ulp_err(got, mp.cbrt(mpf(c) / ONE) * ONE), c)
        # sinh and cosh from one exp: units of 2^-192 less the kernel's
        # 2^-299 relative, against the stated 3; and the rounded word. |x|
        # from 2^-64 to 88, half the draws below 1.
        b = rng.randint(64, 134)
        ax = (rng.getrandbits(b) | (1 << b)) % (88 * ONE)
        if ax < 1 << 64:
            ax += 1 << 64
        x = mpf(ax) / ONE
        for name, sign, fn, op in (("cosh", 1, mp.cosh, op_cosh), ("sinh", -1, mp.sinh, op_sinh)):
            tv = fn(x) * G
            units = abs(mpf(hyp_pre(ax, sign)) - tv) - tv * mpf(2) ** -299
            assert units <= 3, (name, ax, units)
            rec(f"{name} (2^-192 units less 2^-299 rel)", max(units, 0), ax)
            rec(f"{name} ULP", ulp_err(op(ax), fn(x) * ONE), ax)
        # atanh: against 2^-146 + 2 units of 2^-192; |x| from 2^-68 to 1,
        # a quarter of the draws within 2^-8..2^-127 of 1
        if rng.random() < 0.25:
            ax = ONE - (rng.getrandbits(rng.randint(1, 120)) | 1)
        else:
            b = rng.randint(60, 127)
            ax = rng.getrandbits(b) | (1 << b)
        x = mpf(ax) / ONE
        tv = mp.atanh(x) * G
        err = abs(mpf(atanh_pre(ax)) - tv)
        assert err <= mpf(2) ** 46 + 2, (ax, err)
        rec("atanh (2^-192 units; bound 2^46 + 2)", err, ax)
        rec("atanh ULP", ulp_err(op_atanh(ax), mp.atanh(x) * ONE), ax)
    for k, (err, inp) in worst.items():
        print(f"{k:38s} max {mp.nstr(err, 6):>14s}  log2 {mp.nstr(log(err, 2) if err else -999, 6)}  at {inp}")


def constants():
    print("LN2H", hex(LN2H))
    print("LN2L", hex(LN2L))
    print("LN10H", hex(LN10H))
    print("LN10L", hex(LN10L))
    for g, row in enumerate(EXPC):
        for v, c in enumerate(row, 1):
            print(f"EXPC g{g} v{v} {hex(c >> 256)} {hex(c & M256)}")
    print("LOG2E_255", hex(LOG2E_255))
    print("LN2_256", hex(LN2_256))
    print("LOG10_2_256", hex(LOG10_2_256))
    print("E254", hex(E254))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "measure"
    if cmd == "constants":
        constants()
    elif cmd == "lambertw":
        sys.exit(1 if lw_measure(int(sys.argv[2]) if len(sys.argv) > 2 else 8) else 0)
    elif cmd == "fastcompound":
        fastcompound(int(sys.argv[2]) if len(sys.argv) > 2 else 20000)
    elif cmd == "fastpow":
        fastpow(int(sys.argv[2]) if len(sys.argv) > 2 else 20000)
    else:
        measure(int(sys.argv[2]) if len(sys.argv) > 2 else 2000)

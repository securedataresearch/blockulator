#!/usr/bin/env python3
"""Integer model of the FP127 v5 precise kernels, as the Yul runs them, with
the constants they need and a measurement against mpmath.

    uv run scripts/fp127/generators/precise_model.py constants   # print the Yul constants
    uv run scripts/fp127/generators/precise_model.py measure [n] # kernel errors on n random inputs
    uv run scripts/fp127/generators/precise_model.py fastpow [n] # pow / cbrt's one-word test (pow2t)
    uv run scripts/fp127/generators/precise_model.py lambertw [d] # Lambert W's seeds and Halley step counts

The v5 kernels work on a double word (DW): a pair (hi, lo) read as
(hi * 2^256 + lo) * 2^-512, a fraction in [0, 1) held to 2^-512.

  expk(r)   e^r - 1 for r in [0, ln 2) as a DW. The top 16 bits of r, in
            eight 2-bit groups, pick factors e^(v 4^-(g+1)) from a table of
            DWs (product in the expm1 form s + c + s c, so nothing exceeds 1);
            the rest, u < 2^-16,
            goes to u + u^2/2 (DW) + a one-word tail u^3/6 (1 + u/4 (1 + ...))
            held at 2^-303. Error about 2^-300 relative.
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

RT = [0x16a09e667f3bcc908b2fb1366ea957d3e3adec1751277509a, 0x1306fe0a31b7152de8d5a46305c85edecbc27343629f502f2,
      0x1172b83c7d517adcdf7c8c50eb14a792035509ff7d758693f, 0x10b5586cf9890f6298b92b71842a98364291408b3ceb0a2a3,
      0x1059b0d31585743ae7c548eb68ca417fe53e3495f7df4baf8, 0x102c9a3e778060ee6f7caca4f7a29bde93d70a2cabc5cb89c,
      0x10163da9fb33356d84a66ae336dcdfa4003ec04c360be2404]
INV = [0xb504f333f9de6484597d89b3754abe9f1d6f60ba893ba84d, 0xd744fccad69d6af439a68bb9902d3fde1d733af522058b17,
       0xeac0c6e7dd24392ed02d75b3706e54fac4faace043b7f91c, 0xf5257d152486cc2c7b9d0c7aed980fc36f510308677709f6,
       0xfa83b2db722a033a7c25bb14315d7fcc8006fe21a95d14dc, 0xfd3e0c0cf486c174853f3a5931e0ee03061b7bb285a60792,
       0xfe9e115c7b8f884badd25995e79d2f096934ec56be0d2544]
LOGP = [0x17b3936278bdf3108194c0601c98145899c19988d7a109e4,
        0xffffffffffffffffe5a2d3ad1b89f389cbff651cf7ab95fe4714e75251ead0a2,
        0x1c68e97dea5d7cb906ffc2f6119635380dacbddbdad76846,
        0xffffffffffffffffe138f639b5c64d7b73c55805dc8ec0880317af4040cc591f,
        0x219350930be11f876593bbdb09daeaf0957b0d080ada26fd,
        0xffffffffffffffffdb11275e20e1ca8a2b959f17d2678df7a3d4f97c7d9a3098,
        0x2909627af80540eceaceb43b3f8e62f14a02fcff00efb471,
        0xffffffffffffffffd1d57135a8fa03d91f80452a64b91d25da559e2ac1044226,
        0x34c2ec54f5bdb27ec606fef4f1ab11413399ed361fb8e654,
        0xffffffffffffffffc271ec478bf80516c07df3f92e8ba0238cdf0eef66e111bf,
        0x49ddb143be6ff9e4b29ccc3bb04619bab966324b8b0e4e6b,
        0xffffffffffffffffa3aae26b51f407a220bc0097cd935ca2a2c07626cf1eb774,
        0x7b1c2770e80ff5d27f05548af0be0fefbba4efbc9d3290df,
        0xffffffffffffffff4755c4d6a3e80f444178012f96e2c1778f63bed2a372430b,
        0x171547652b82fe1777d0ffda0d23a7d11d6ae94441bacdb6a]


def sgn(w):
    w &= M256
    return w - T256 if w >> 255 else w


def mulg(a, b):
    return (sgn(a) * sgn(b)) >> 192


# ---------------------------------------------------------------------------
# kernels
# ---------------------------------------------------------------------------

def expk(r: int) -> int:
    """e^r - 1 at 2^-512 for r in [0, ln 2) at 2^-512 (both as 512-bit ints)."""
    rh, rl = r >> 256, r & M256
    uh = rh & ((1 << 240) - 1)
    U = (uh << 16) | (rl >> 240)                  # u at 2^-272
    H = H255
    for k in range(16, 3, -1):
        H = H255 + (((U * H) >> 256) >> 16) // k
    u2 = (U * U) >> 256                           # 2^-288
    u3 = (u2 * U) >> 256                          # 2^-304
    T = ((u3 * H) >> 256) // 6                    # 2^-303
    # u + u^2/2: (uh, rl)^2 at 2^-512 is uh^2 + 2 hi(uh rl), the rl^2 term dropped
    q = uh * uh + ((2 * uh * rl) >> 256)
    s = ((uh << 256) | rl) + (q >> 1) + (T << 209)
    top = rh >> 240
    for g in range(8):
        v = (top >> (14 - 2 * g)) & 3
        if v:
            c = EXPC[g][v - 1]
            sh, sl, ch, cl = s >> 256, s & M256, c >> 256, c & M256
            prod = sh * ch + ((sh * cl) >> 256) + ((sl * ch) >> 256)
            s = s + c + prod
    assert 0 <= s < 1 << 512
    return s


def log2m(mm: int) -> int:
    """log2(m) at 2^-192 for m = mm 2^-192 in [1, 2): the v4 reduction and polynomial."""
    acc = 0
    for k in range(7):
        if mm >= RT[k]:
            mm = mulg(mm, INV[k])
            acc += 1 << (192 - k - 1)
    f = mm - G
    r = sgn(LOGP[0])
    for c in LOGP[1:]:
        r = mulg(r, f) + sgn(c)
    r = mulg(r, f)
    return acc + r


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
    r = (f * LN2_512) >> 192
    s = expk(r)
    sh, sl = s >> 256, s & M256
    q = ((M << 256) + M * sh + ((M * sl) >> 256)) & M512
    d = q - (1 << 512) if q >> 511 else q          # d = delta * 2^512
    d384 = d >> 128
    d2 = (d384 * d384) >> 385
    corr = ((d384 - d2) * LOG2E_255) >> 255
    return (e << 384) + (y0 << 192) + corr


def redx(X: int, n: int, kint: int, ch: int, cl: int):
    """r = x A - n ln 2 mod 1 at 2^-512, A = kint + (ch, cl) 2^-512, and the
    corrected n with r in [0, ln 2)."""
    r = (X * kint << 384) + (X * ch << 128) + ((X * cl) >> 128) - n * LN2_512
    r &= M512
    if r >> 256 > 0xd999999999999999999999999999999999999999999999999999999999999999:
        n -= 1
        r = (r + LN2_512) & M512
    elif r >= LN2_512:
        n += 1
        r -= LN2_512
    return n, r


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
    n = mulg(X << 64, LOG2E_192) >> 192
    n, r = redx(X, n, 1, 0, 0)
    return n, expk(r)


def op_exp(X):
    if X == 0:
        return ONE
    if X > 88 * ONE:
        return "REVERT"
    if X < -90 * ONE:
        return 0
    n, s = exp_parts(X)
    return rnd64(scaled192(n, s))


def op_exp2(X):
    if X >= 127 * ONE:
        return "REVERT"
    if X < -129 * ONE:
        return 0
    n, r = redx(X, X >> 128, 0, LN2H, LN2L)
    return rnd64(scaled192(n, expk(r)))


def op_exp10(X):
    n = mulg(X << 64, LOG2_10_192) >> 192
    n, r = redx(X, n, 2, LN10H, LN10L)
    return rnd64(scaled192(n, expk(r)))


def x384_round(L):
    return (L + (1 << 255)) >> 256


def op_log2_precise(X):
    return x384_round(l2p(X))


def op_ln_precise(X):
    L = l2p(X)
    return x384_round((L * LN2_256) >> 256)


def op_pow(X, Y):
    L = l2p(X)
    t = Y * L                       # at 2^-512
    n, f = t >> 512, t & M512
    if n >= 127:
        return "REVERT"
    if n < -130:
        return 0
    r = (f * LN2_512) >> 512
    return rnd64(scaled192(n, expk(r)))


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
# pow and cbrt: the one-word value first (pow2t)
# ---------------------------------------------------------------------------

def _exp2_coeffs():
    import re
    from pathlib import Path
    text = (Path(__file__).resolve().parents[3] / "contracts/src/fp127/FP127.yul.src").read_text()
    body = text[text.index("function exp2frac"):]
    return [int(h, 16) for h in re.findall(r"0x[0-9a-f]+", body[: body.index("\n}\n")])]


EXP2C = _exp2_coeffs()


def exp2frac(f: int) -> int:
    """2^f at 2^-192 for f in [0, 2^192): the degree-24 polynomial, Horner, floors."""
    r = EXP2C[0]
    for c in EXP2C[1:]:
        r = ((r * f) >> 192) + c
    return r


def pow2t(t: int, ay: int):
    """(r, ok, v, eb) as the Yul's pow2t: v = 2^t at 2^-192, eb its bound."""
    at = abs(t)
    k = at >> 192
    e = k + 1 if t >= 0 else -k
    eb = (ay >> (80 - e)) + ((1 << (e + 48)) if e + 48 >= 0 else 0) + 6
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
    return scaled192(n, expk((f * LN2_512) >> 512))


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


T_STAGES = [(0x5a827999fcef32422cbec4d9baa55f50, 0x2d413cccfe779921165f626cdd52afa8, 8),
            (0x4c1bf828c6dc54b7a356918c17217b7b, 0x35d13f32b5a75abd0e69a2ee640b4ff8, 4),
            (0x45cae0f1f545eb737df23143ac529e48, 0x3ab031b9f7490e4bb40b5d6cdc1b953f, 2),
            (0x42d561b3e6243d8a62e4adc610aa60d9, 0x3d495f454921b30b1ee7431ebb6603f1, 1)]
ATANH_C = [0x2c8590b21642c8590b21642c8590b21, 0x30c30c30c30c30c30c30c30c30c30c3, 0x35e50d79435e50d79435e50d79435e5,
           0x3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c4, 0x4444444444444444444444444444444, 0x4ec4ec4ec4ec4ec4ec4ec4ec4ec4ec5,
           0x5d1745d1745d1745d1745d1745d1746, 0x71c71c71c71c71c71c71c71c71c71c7, 0x9249249249249249249249249249249,
           0xccccccccccccccccccccccccccccccd, 0x15555555555555555555555555555555, 0x40000000000000000000000000000000]
LN2_124 = 0xb17217f7d1cf79abc9e3b39803f2f6b
LNC0 = [0x6c624f4ace937ad74c72c1900aebb69, -0x193a803a4689b1e7d4fe8cc4f525bca5, 0x3ecce60a25db5c9757959e657fdbf429, 0x95fd7e22848b1d16f2f2bb6adf6c7]


def lw_lnc(r, k):
    """The Yul's lnc: k ln 2 + ln r at 2^-128, r in [2^126, 2^127): four reduction stages, 12 odd terms."""
    j = 16 * k
    for T, I, dj in T_STAGES:
        if r >= T:
            r = (r * I) >> 126
            j += dj
    s = sdiv((r - (1 << 126)) << 126, r + (1 << 126))
    s2 = (s * s) >> 126
    A = ATANH_C[0]
    for c in ATANH_C[1:]:
        A = c + ((s2 * A) >> 126)
    return j * LN2_124 + (((s * A) >> 125) << 2)


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


def lw_bs128(qa, tau):
    C = lambda n: n << 112
    m = lambda a, b: (a * b) >> 126
    h = lambda co: __import__("functools").reduce(lambda acc, cc: C(cc) + m(qa, acc), co[1:], C(co[0]))
    v = sdiv(h([240, 1200, 3052, 4760, 4410, 1890]), 1440)
    v = sdiv(h([24, 96, 190, 210, 105]), 120) + m(tau, v)
    v = sdiv(h([6, 18, 25, 15]), 24) + m(tau, v)
    v = sdiv(h([2, 4, 3]), 6) + m(tau, v)
    v = ((C(1) + (qa >> 14)) >> 1) + m(tau, v)
    return C(1) + m(tau, v)


def lw_q128(Q, ep, sg, Y, k):
    """The Yul's lwq128 (FP256's): (Q', |tau| 2^126)."""
    one = 1 << 126
    qa = Q >> (-ep - 126)
    if sg:
        qa = -qa
    j = 126 - msb(abs(qa)) if qa else 126
    Kt = min(2 + 130 // (j + 2), 35)
    u = one
    for i in range(Kt, 2, -1):
        u = one + sdiv((qa * u) >> 126, i)
    G = one + (((qa - one) * u) >> 127)
    E = one + qa + ((qa * ((qa * u) >> 126)) >> 127)
    Rr = ((((Q * Q * G) >> 126) << (2 + k)) << 128) // Y
    rho = Rr - ONE
    tau = sdiv(((rho * G) >> 128) << 126, (E * Rr) >> 128)
    return Q - ((Q * ((tau * lw_bs128(qa, tau)) >> 112)) >> 126), abs(tau)


def lw_q(x):
    """The Yul's lwq: 1 + e x at 2^-256, floored (0 < x + 1/e)."""
    return ((x * E_254) >> 126) & M256


def lw_br(q, sg):
    """The Yul's lwbr: w = -1 +- q at 2^-128 from q = 1 + e x at 2^-256, and the step count."""
    nb = msb(q)
    Y = q << (254 - nb)
    ey = nb - 510
    k = 2 - (ey & 1)
    eq = (ey - 254 + k) >> 1
    ep = eq + 128
    n = Y >> (1 + k)
    P = int(msqrt(mpf(n)))
    while P * P > n:
        P -= 1
    while (P + 1) * (P + 1) <= n:
        P += 1
    p = P >> (-ep - 126)
    s0 = (1 << 126) + (11 * ((p * p) >> 126)) // 72
    s0 = s0 + p // 3 if sg else s0 - p // 3
    Q = (P * s0) >> 126
    cnt = 0
    for _ in range(4):
        Q, at = lw_q128(Q, ep, sg, Y, k)
        cnt += 1
        if at < 1 << 102:
            break
    qw = (Q >> (-ep - 126)) << 2
    return (-ONE - qw if sg else qw - ONE), cnt


def lw_w0(x):
    """W0's one-word stages, as fp127_lambertW0 runs them: (w before lwfin, steps)."""
    if x < 0x20000000000000000000000000000000:
        if x < -0x2f16ac6c59de6f8d5d6f63c1482a7c86:
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
    if x < -0x46a202a286cda7540c2715a1ec3fbaca:
        return lw_br(lw_q(x), 1)
    lx = lw_lnc0(*lw_lnm(-x))
    ll = lw_lnc0(*lw_lnm(-lx))
    return lw_fast(x, lx - ll + sdiv(ll << 100, lx >> 28))


def lw_measure(d=8):
    """The correct bits lwfin starts from, -log2(|w - W| / max(1, |W|)), and
    where its Newton step lands, -log2(err^2 / |1 + W|), worst over a grid
    of d points per octave, by region and step count: every region must
    reach 88 before (the fast stage stops at a step that starts within
    2^-22; near -1/e the word's 2^-128 grid itself, q = 1 + W being within
    2^-124 q) and 176 after, far below the grid."""
    mp.dps = 300
    emin = -0x5e2d58d8b3bcdf1abadec7829054f90d
    pos = [fx(mpf(2) ** (k / d), 128) for k in range(-65 * d, 127 * d)]
    neg = [-fx(mpf(2) ** (-k / d), 128) for k in range(2 * d, 65 * d)]
    mid = [emin + int((mpf(-emin) - mpf(2) ** 125) * (1 - mpf(2) ** -(k / d))) for k in range(1, 40 * d)]
    near = [emin + int(mpf(2) ** (128 - k / d)) for k in range(1, 128 * d) if emin + int(mpf(2) ** (128 - k / d)) < -(1 << 126)]
    small = [-fx(mpf(2) ** (-k / d), 128) for k in range(2 * d, 128 * d)]
    for name, xs, run, br in (
            ("W0, x > 0", pos, lw_w0, 0), ("W0, -1/4 < x < 0", neg, lw_w0, 0),
            ("W0, -1/e < x <= -1/4", mid + near, lw_w0, 0),
            ("W-1, -1/4 <= x < 0", small, lw_wm1, -1),
            ("W-1, -1/e < x < -1/4", mid + near, lw_wm1, -1)):
        by = {}
        for x in xs:
            if x < emin or x == 0:
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
        print(f"{name:22s} worst bits before lwfin (and after its squaring, err^2 / |1 + W|), by one-word steps: "
              + ", ".join(f"{n}: {b:.1f} ({b2:.0f})" for n, (b, b2) in sorted(by.items())))
    mp.dps = 220


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
        # exp ULP error
        b = rng.randint(100, 134)
        x = rng.getrandbits(b) | (1 << b)
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
    for k, (err, inp) in worst.items():
        print(f"{k:24s} max {mp.nstr(err, 6):>14s}  log2 {mp.nstr(log(err, 2) if err else -999, 6)}  at {inp}")


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
        lw_measure(int(sys.argv[2]) if len(sys.argv) > 2 else 8)
    elif cmd == "fastpow":
        fastpow(int(sys.argv[2]) if len(sys.argv) > 2 else 20000)
    else:
        measure(int(sys.argv[2]) if len(sys.argv) > 2 else 2000)

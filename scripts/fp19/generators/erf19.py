#!/usr/bin/env python3
"""erf, erfc and normCdf for FP19 (the FP19N object), modelled in exact integers
as the Yul runs them, with the fit and the Yul text the fast path needs.

    uv run scripts/fp19/generators/erf19.py            # measure the three ops against mpmath
    uv run scripts/fp19/generators/erf19.py --fit      # refit g's two pieces -> erfcxu.json (minutes)
    uv run scripts/fp19/generators/erf19.py --yul      # print erfcxu's Yul
    uv run scripts/fp19/generators/erf19.py --check    # does FP19.yul.src hold it verbatim?
    uv run scripts/fp19/generators/erf19.py --cf-depth # the second stage's depth against its need (minutes)

Everything is built on g(y) = e^(y^2) erfc(y), so erfc(y) = e^(-y^2) g(y) is a
product and never a difference:

  y < 1/2      erf(y) = (2/sqrt pi) y e^(-y^2) S, S = sum d^k / (2k+1)!!, d = 2y^2,
               summed until the term rounds to zero (about 40 terms); erfc = 1 - erf
               loses at most 1.6 bits there.
  1/2..18      g = h(w) u, u = 8 / (8 + y), h = g / u a degree-66 minimax polynomial in
               w = (u - u(18)) / D' on two pieces, w < 1/2 (y > 4.81) and w >= 1/2
               (erfcxu, below; the coefficients in erfcxu.json, from --fit). Until
               3.0 this was 45 Taylor anchors on [1/2, 6] (25k gas a call) and a
               continued fraction on [6, 18) (35k to 56k).
  y >= 18      the asymptotic series erfc(y) = e^(-y^2)/(y sqrt pi) sum (-1)^m (1/2)_m / y^(2m)
               (DLMF 7.12.1), its terms at 2^-262 until one floors to zero, the
               remainder below the first omitted term: 76 terms at 18, 18 at 430.

e^(-y^2) comes from the exact 474-bit square of the significand times log2 e in
two words, so the deep tail keeps its bits: erfc(y) for y up to about 427 and
normCdf(x) for x down to about -603, where they underflow 2^-262142.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from mpmath import mp, mpf, erf as merf, erfc as merfc, ncdf, exp, sqrt, pi, log, floor, nint, ceil, power

sys.path.insert(0, __import__("os").path.dirname(__file__))
import kernel254 as K  # noqa: E402
import minimax as M  # noqa: E402
import horner as H  # noqa: E402

W = 254
WS = 1 << W
MASK = (1 << 256) - 1
BIAS = K.BIAS
ONE = BIAS << 236


def qs(v, s):
    return int(floor(v * mpf(2) ** s))


mp.dps = 120
C2_254 = qs(2 / sqrt(pi), 254)                # 2/sqrt(pi) at 2^-254, the erf constant
SQRTPI = qs(sqrt(pi), 254)
RSQRT2 = qs(1 / sqrt(mpf(2)), 255)            # 1/sqrt 2 at 2^-255


def mulwu(a, b):
    return (a * b) >> W


def signed(w):
    return w - (1 << 256) if w >> 255 else w


def mulwr(a, b):
    """round(a b / 2^254) on signed values (Python ints)."""
    return (a * b + (1 << (W - 1))) >> W


def rdiv(a, n):
    """a / n rounded to nearest, ties away from zero, for a signed a and n > 0."""
    return (a + n // 2) // n if a >= 0 else -((-a + n // 2) // n)


def rshr(a, s):
    return (a + ((1 << s) >> 1)) >> s if s > 0 else a


def expnegsq(ker, u, m, h):
    """e^(-x^2 / 2^h) for x = m 2^(u-236): (kk, v), value v 2^(kk - 254); None below 2^-2^19."""
    P = m * m
    # the two words the Yul keeps: floor(P LH / 2^256) + floor(P LL / 2^510)
    qt = ((P * ker.LOG2E_HI) >> 256) + ((P * ker.LOG2E_LO) >> 510)
    s2 = 216 + h - 2 * u
    f = (qt >> s2) & (WS - 1) if s2 < 512 else 0
    k = qt >> (s2 + 254) if s2 + 254 < 512 else 0
    if k >= 1 << 19:
        return None
    return ker.exp2kv(1, k, f)


def erfser(d):
    """S = sum d^k / (2k+1)!! at 2^-254, d = 2y^2 at 2^-254, rounded steps."""
    term = WS
    s = WS
    k = 1
    while term:
        term = rdiv(mulwr(term, d), 2 * k + 1)
        s += term
        k += 1
    return s


# ---- g on [1/2, 18): two minimax pieces in w (erfcxu) -------------------------
#
# g(y) = e^(y^2) erfc(y) is smooth but needs a high degree in y (116 on [1/2, 6]
# alone, 120 on [6, 18], at 2^-262). In u = 8 / (8 + y) it needs 89 for all of
# [1/2, 18] (k = 8 is near the best k in k / (k + y): 163 at 1, 130 at 2, 97 at
# 5, 89 at 8, 93 at 12, 119 at 20), and h = g / u is flatter than g (from 0.654
# to 0.101 against 0.616 to 0.031). w = (u - u(18)) / D' runs from 0 (y = 18) to
# just under 1 (y = 1/2), D' = (u(1/2) - u(18)) (1 + 2^-40); as one piece every
# Horner step's floor reaches the result undiminished at w near 1 (a bound of
# 131 units), so the range is cut at w = 1/2 (y = 4.81): two pieces of degree
# 66 in z = w - w0 in [0, 1/2), each step's error then shrinking by half a step.
# Piece 1's partial sums reach 2^1.98 (alternating coefficients), so it runs at
# 2^-252; piece 0's stay under 2^-2.44 and it runs at 2^-256.

UK = mpf(8)
U_LO = UK / (UK + 18)                            # u at y = 18
U_HI = UK / (UK + mpf(1) / 2)                    # u at y = 1/2
U_DP = (U_HI - U_LO) * (1 + mpf(2) ** -40)       # D'
WMAX = (U_HI - U_LO) / U_DP
ULO = int(floor(U_LO * mpf(2) ** 256))           # u(18) at 2^-256, floored
CW = int(floor((1 / U_DP - 1) * mpf(2) ** 256))  # 1/D' - 1 at 2^-256
EU_DEG = 66
EU_RHO = (256, 252)                              # piece 0 (y >= 4.81), piece 1
EU_FIT = Path(__file__).with_name("erfcxu.json")


def g_of_y(y):
    return exp(y * y) * merfc(y)


def h_of_w(w):
    u = U_LO + U_DP * w
    return g_of_y(UK / u - UK) / u


def eu_piece_fn(k):
    w0 = mpf(k) / 2
    return (lambda z: h_of_w(w0 + z)), (mpf(1) / 2 if k == 0 else WMAX - w0)


def eu_fit():
    """Fit both pieces (Remez at 150 digits, a few minutes) and write erfcxu.json."""
    mp.dps = 150
    out = {"deg": EU_DEG, "pieces": []}
    for k in (0, 1):
        f, zmax = eu_piece_fn(k)
        co, _ = M.remez(f, EU_DEG, 0, zmax, rel=True, grid=3000)
        sup = M.certify(co, f, 0, zmax, n=3000)
        out["pieces"].append({"coeffs": [mp.nstr(c, 140) for c in co], "sup": mp.nstr(sup, 20)})
        print(f"piece {k}: degree {EU_DEG}, certified sup 2^{float(log(sup, 2)):.2f}")
    EU_FIT.write_text(json.dumps(out, indent=1) + "\n")
    mp.dps = 120


def eu_pieces():
    """The two Horner models (horner.py) from erfcxu.json, with each piece's
    bound E_g on g at 2^-255 and its er on D (units of D's last bit)."""
    mp.dps = 120
    d = json.loads(EU_FIT.read_text())
    out = []
    for k, pc in enumerate(d["pieces"]):
        co = [mpf(c) for c in pc["coeffs"]]
        sup = mpf(pc["sup"])
        f, zmax = eu_piece_fn(k)
        hmax = max(f(mpf(0)), f(zmax))
        rho = EU_RHO[k]
        hz = H.Horner(co, 256, rho, zmax, sup, hmax, f"erfcxu{k}", "z")
        # |dP/dz| on the piece, by absolute values (z >= 0)
        dmax = sum(abs(c) * j * zmax ** (j - 1) for j, c in enumerate(co) if j)
        # w: U floored (1 unit of 2^-256) times 1 + c (1.58), hi()'s floor and
        # CW's floor (V / 2^256 < 1): within 3.6 units of 2^-256
        ew = mpf("3.6")
        eh = hz.err + dmax * ew * power(2, rho - 256)          # units of 2^-rho
        # g = hi(h, U), then to 2^-255: h's error times u, h times U's unit, the
        # floor; the shift right (rho 256) floors once more
        eg = (eh * U_HI + hmax * power(2, rho - 256) + 1) * power(2, 255 - rho) + (1 if rho > 255 else 0)
        # normCdf's y: Y floored at 2^(uy - 254) and y at 2^-251 floored, times
        # |g'| <= 0.51 (y = 1/2), 0.27 (1), 0.107 (2), 0.033 (4): under 5 units
        eg += 5
        gmax = mpf("0.6158")
        # D = floor(g v / 2^254): g's error times v < 2, v's 6.1 units times g, the floor
        er = int(ceil(2 * eg + 2 * gmax * mpf("6.1") + 1))
        out.append({"hz": hz, "sup": sup, "eg": eg, "er": er, "rho": rho, "dmax": dmax})
    return out


EU = None


def eu():
    global EU
    if EU is None:
        EU = eu_pieces()
    return EU


def yf251(Y, uy):
    """y at 2^-251 from y = Y 2^(uy - 254), uy in [-1, 4]: exact for erf and erfc
    (Y's low 18 bits are zero), floored for normCdf."""
    return Y >> (3 - uy) if uy <= 3 else Y << (uy - 3)


def erfcxu(Y, uy):
    """g(y) at 2^-255 for y in [1/2, 18) and the piece's er, as the Yul runs it."""
    den = (1 << 254) + yf251(Y, uy)                  # (8 + y) 2^251
    U = (1 << 510) // den                            # u = 8 / (8 + y) at 2^-256
    V = U - ULO
    W = V + ((V * CW) >> 256)                        # w at 2^-256
    k = 0 if W < 1 << 255 else 1
    pc = eu()[k]
    p = pc["hz"].eval(W - (k << 255))                # h at 2^-rho
    gh = (p * U) >> 256
    g = gh >> 1 if pc["rho"] > 255 else gh << (255 - pc["rho"])
    return g, pc["er"]


def eu_emit():
    """The Yul of erfcxu: w from one division, the piece, its Horner, h u."""
    P = eu()
    out = [
        "/// g(y) = e^(y^2) erfc(y) at 2^-255 for y = Y 2^(uy - 254) in [1/2, 18), and",
        "/// er, the bound on D = g v / 2^254 (erf19.py): u = 8 / (8 + y) by one",
        "/// division of 2^510 by (8 + y) 2^251, w = (u - u(18)) / D' in [0, 1) from it",
        "/// (D' = (u(1/2) - u(18)) (1 + 2^-40)), then g = h(w) u with h = g / u the",
        f"/// degree-{EU_DEG} minimax polynomial on w in [0, 1/2) (y >= 4.81; at 2^-{P[0]['rho']},",
        f"/// certified sup norm 2^{float(log(P[0]['sup'], 2)):.1f} relative) or on [1/2, 1) (at 2^-{P[1]['rho']},",
        f"/// 2^{float(log(P[1]['sup'], 2)):.1f}), each in z = w - w0 by Horner's rule: g within {float(P[0]['eg']):.1f}",
        f"/// and {float(P[1]['eg']):.1f} units of 2^-255 (normCdf's floored y included); er is",
        "/// twice that, plus g times v's 6.1 units twice, plus one. Fitted to h, not g,",
        "/// and cut at w = 1/2: as one piece every step's floor would reach the result",
        "/// at w near 1.",
        "function erfcxu(Y, uy) -> g, er {",
        "    let yf := shr(sub(3, uy), Y)",
        "    if sgt(uy, 3) { yf := shl(sub(uy, 3), Y) }",
        "    let U := divh(0x8000000000000000000000000000000000000000000000000000000000000000, "
        "add(0x4000000000000000000000000000000000000000000000000000000000000000, yf))",
        f"    let z := sub(U, {H.hx(ULO)})",
        f"    z := add(z, mulhi(z, {H.hx(CW)}))",
        "    let p",
        "    switch shr(255, z)",
        "    case 0 {",
    ]
    out += ["        " + ln for ln in P[0]["hz"].yul("p")]
    out += ["        g := shr(1, mulhi(p, U))", f"        er := {P[0]['er']}", "    }", "    default {",
            "        z := sub(z, 0x8000000000000000000000000000000000000000000000000000000000000000)"]
    out += ["        " + ln for ln in P[1]["hz"].yul("p")]
    out += [f"        g := shl({255 - P[1]['rho']}, mulhi(p, U))", f"        er := {P[1]['er']}", "    }", "}"]
    return "\n".join(out) + "\n"


def asym(Y, uy, v):
    """erfc(y) for y >= 18 by the asymptotic series, given e^(-y^2)'s v: (D, eg) with
    D in [2^255, 2^256), erfc = D 2^(eg + kk - 254), as the Yul's erfasym."""
    y2 = (Y * Y) >> 254
    ey = 2 * uy
    if y2 >> 255:
        y2 >>= 1
        ey += 1
    W1 = (1 << 508) // y2
    w254 = W1 >> (ey + 1)
    term = W1 >> (ey - 7)                      # w at 2^-262
    T = -term
    sign, mm = 1, 2
    while term:
        term = (term * ((2 * mm - 1) * w254)) >> 254
        T += sign * term
        sign, mm = -sign, mm + 1
    assert T <= 0
    Q = (1 << 510) // ((Y * SQRTPI) >> 254)
    SQ = Q - (((-T) * Q) >> 262)
    D = (SQ * v) >> 255
    t = 255 - (D.bit_length() - 1)
    return D << t, -uy - 1 - t





def asym_regime(Y, uy):
    """y >= 18: the asymptotic series is cheaper than the fraction there (measured)."""
    return uy > 4 or (uy == 4 and Y >= 9 << 251)


def ystuff(u, m, h):
    """y = |x| (h = 0) or |x|/sqrt 2 (h = 1) as y = Y 2^(uy - 254), Y in [2^254, 2^255)."""
    Y, uy = m << 18, u
    if h == 1:
        P = Y * RSQRT2
        Y1 = P >> 255
        if Y1 < WS:
            Y1, uy = P >> 254, u - 1
        Y = Y1
    return Y, uy


def ge13(Y, uy):
    return uy >= 4 or (uy == 3 and Y >= 13 << 251)


def erfc_big(ker, Y, uy, u, m, h):
    """erfc(y) for y >= 1/2 as (D, ee), value D 2^(ee - 254); None when it underflows."""
    r = erfc_big_er(ker, Y, uy, u, m, h)
    return None if r is None else r[:2]


def erfc_big_er(ker, Y, uy, u, m, h):
    """erfc_big with er, D's bound in units of its last bit: (D, ee, er) or None."""
    r = expnegsq(ker, u, m, h)
    if r is None:
        return None
    kk, v = r
    if asym_regime(Y, uy):                            # y >= 18: the asymptotic series
        D, eg = asym(Y, uy, v)
        return D, kk + eg, 64
    g, er = erfcxu(Y, uy)                             # 1/2 <= y < 18: the two pieces
    return (g * v) >> 254, kk - 1, er


def tofix(val):
    if val is None:
        return 0
    D, ee = val
    return D >> -ee if ee <= 0 else D << ee


def erf_small(ker, u, m, h):
    """F with erf(y) = x F for y = |x| / sqrt(2^h) < 1/2, at 2^-254."""
    P = m * m
    sh = 217 + h - 2 * u                              # d = 2 y^2 at 2^-254
    d = P >> sh if sh < 600 else 0
    S = erfser(d)
    kk, v = expnegsq(ker, u, m, h)
    E = v >> -kk
    F = mulwr(mulwr(C2_254, E), S)
    if h == 1:
        F = (F * RSQRT2) >> 255
    return F


def erfc_mag(ker, u, m, h):
    """erfc(y), y = |x| / sqrt(2^h), as (D, ee) or None (underflow)."""
    Y, uy = ystuff(u, m, h)
    if uy <= -2:                                      # y < 1/2
        F = erf_small(ker, u, m, h)
        ef = (m * F) >> (236 - u)
        return WS - ef, 0
    return erfc_big(ker, Y, uy, u, m, h)


def model_erfc(ker, x):
    s, e, m = K.unpack(x)
    if e == 0:
        return ONE
    u = e - BIAS
    if u >= 10:
        return (BIAS + 1) << 236 if s else 0
    val = erfc_mag(ker, u, m, 0)
    if s:
        return K.normround(0, BIAS, 2 * WS - tofix(val))
    if val is None or val[0] == 0:
        return 0
    return K.normround(0, BIAS + val[1], val[0])


def model_erf(ker, x):
    s, e, m = K.unpack(x)
    if e == 0:
        return 0
    u = e - BIAS
    Y, uy = ystuff(u, m, 0)
    if ge13(Y, uy):
        return ONE | (s << 255)
    if uy <= -2:
        F = erf_small(ker, u, m, 0)
        return K.normround(s, BIAS + u, (m * F) >> 236)
    return K.normround(s, BIAS, WS - tofix(erfc_big(ker, Y, uy, u, m, 0)))


def model_normCdf(ker, x):
    s, e, m = K.unpack(x)
    HALF = (BIAS - 1) << 236
    if e == 0:
        return HALF
    u = e - BIAS
    if u >= 10:
        return 0 if s else ONE
    if not s:
        Y, uy = ystuff(u, m, 1)
        if ge13(Y, uy):
            return ONE
    val = erfc_mag(ker, u, m, 1)
    if s:
        if val is None or val[0] == 0:
            return 0
        return K.normround(0, BIAS + val[1] - 1, val[0])     # erfc(y) / 2
    return K.normround(0, BIAS - 1, 2 * WS - tofix(val))     # (2 - erfc(y)) / 2


K.Kernels.model_erf = model_erf
K.Kernels.model_erfc = model_erfc
K.Kernels.model_normCdf = model_normCdf


def bits(got, truth):
    g = K.decode(got)
    if g == truth:
        return 256.0
    if truth == 0:
        return 0.0
    return float(-log(abs(g - truth) / abs(truth), 2))


def measure(ker):
    mp.dps = 160
    rng = random.Random(256)
    pts = []
    for _ in range(300):
        pts.append(K.rand_float(rng, -12, 1))
    for _ in range(300):
        pts.append(K.encode(mpf(rng.random()) * 8 * (1 if rng.getrandbits(1) else -1)))
    for _ in range(150):
        pts.append(K.encode(mpf(4) + mpf(rng.random()) * 30))
    for _ in range(80):
        pts.append(K.encode(mpf(30) + mpf(rng.random()) * 400))
    for name, fn, truth in [("erf", model_erf, merf), ("erfc", model_erfc, merfc), ("normCdf", model_normCdf, ncdf)]:
        bs = []
        for x in pts:
            xv = K.decode(x)
            t = truth(xv)
            if t == 0:
                continue
            got = fn(ker, x)
            if got == 0 and K.encode(t) == 0:
                continue
            bs.append(bits(got, t))
        print(f"{name:8} n={len(bs):4} bits min {min(bs):7.2f} mean {sum(bs) / len(bs):7.2f}")


# ---- the second stage's continued fraction (erfccf2) --------------------------

def cf2_depth(xi, h):
    """erfccf2's depth for xi = floor |x| (x = y, or y sqrt 2 for normCdf)."""
    return (2548 + 2452 * h) // (xi * xi) + (1276 + 528 * h) // xi + 26


def cf2_value(y, h, n):
    """erfc(y) from the second stage's fraction at depth n, in mpmath's precision."""
    b, a = (2 * y, 2) if h == 0 else (y * sqrt(2), 1)
    t = mpf(0)
    for k in range(n, 0, -1):
        t = (a * k) / (b + t)
    c = (2 / sqrt(pi)) if h == 0 else sqrt(2 / pi)
    return c * exp(-y * y) / (b + t)


def cf2_needed(y, h, bits=392, hi=600):
    """The smallest depth whose value is within 2^-bits of erfc(y), relative."""
    tru = merfc(y)
    tol = mpf(2) ** -bits
    lo = 1
    while lo < hi:
        mid = (lo + hi) // 2
        if abs(cf2_value(y, h, mid) / tru - 1) < tol:
            hi = mid
        else:
            lo = mid + 1
    return lo


def check_cf2_depth(bits=392) -> bool:
    """cf2_depth against cf2_needed at every band edge, y = xi (erfc, xi = 7..430)
    or xi / sqrt 2 (normCdf, from y = 7, xi = 9..608): the need falls with y and
    the depth holds across a band, so the depth covers every y >= 7. True when it
    does, with at least one step to spare."""
    mp.dps = 170
    ok = True
    for h, xis in ((0, range(7, 431)), (1, range(9, 609))):
        prev, slack = 600, None
        for xi in xis:
            y = max(mpf(xi) / sqrt(2), mpf(7)) if h else mpf(xi)
            need = cf2_needed(y, h, bits, prev)
            prev = need
            sl = cf2_depth(xi, h) - need
            slack = sl if slack is None else min(slack, sl)
            ok &= sl >= 1
        print(f"{'normCdf' if h else 'erfc'}: depth - need >= {slack} over every band edge")
    mp.dps = 120
    return ok


def check_source() -> bool:
    """True when FP19.yul.src holds erfcxu's Yul verbatim."""
    src = (Path(__file__).resolve().parents[3] / "contracts/src/fp19/FP19.yul.src").read_text()
    ok = eu_emit().strip("\n") in src
    print(f"FP19.yul.src holds erf19.py's erfcxu verbatim: {'yes' if ok else 'NO'}")
    return ok


def main(argv):
    if "--fit" in argv:
        eu_fit()
        return 0
    if "--yul" in argv:
        print(eu_emit())
        return 0
    if "--check" in argv:
        return 0 if check_source() else 1
    if "--cf-depth" in argv:
        return 0 if check_cf2_depth() else 1
    ker, _, _ = K.build()
    for k, pc in enumerate(eu()):
        print(f"erfcxu piece {k}: certified sup 2^{float(log(pc['sup'], 2)):.2f}, Horner bound "
              f"{float(pc['hz'].err):.2f} units of 2^-{pc['rho']}, |P'| <= {float(pc['dmax']):.2f}, "
              f"g within {float(pc['eg']):.2f} units of 2^-255, er {pc['er']}")
    measure(ker)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

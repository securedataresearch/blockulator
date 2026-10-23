"""Lemmas K127 and K19: the mulDiv kernels are the exact floor quotient.

    python test/proofs/kernel.py      # one line per step, exits 1 on any failure

Kernels.divq (FP127's div) and Kernels.divh (FP19's) are Remco Bloemen's
mulDiv specialised to the multiplier 2^s, s = 128 and 255:

    K127  divq(a, b) = floor(a 2^128 / b)   for 0 < a >> 128 < b
    K19  divh(a, b) = floor(a 2^255 / b)   for 0 < b, a < 2 b

The proof follows the code line by line. Each EVM operation is read by its
definition on unbounded integers (W = 2^256): MUL(x, y) = x y mod W,
SUB(x, y) = (x - y) mod W, SHL(k, x) = x 2^k mod W, SHR(k, x) = floor(x / 2^k),
DIV the floor quotient, MULMOD(x, y, n) = x y mod n. The bit operations AND,
OR and XOR are settled by bit-vector lemmas (B1 to B3). Every step is a Z3
query that is either linear or a polynomial identity, both of which Z3 decides;
the products are named (Q b, Q d, d x) so that no query asks the solver for
nonlinear search.

With N = a 2^s, Q = floor(N / b), r = N mod b:

  S1  prod1 = SHR(256 - s, a), prod0 = SHL(s, a): N = prod1 W + prod0.
  S2  remainder = MULMOD(a, 2^s, b) = r; the borrow: prod1' W + prod0' = N - r = Q b.
  S3  Q < W (from N < b W).
  B1  twos = AND(SUB(0, b), b) is 2^t for the t with b = 2^t d, d odd (per t).
  S4  per t, with T = 2^t, F = W / T: d = DIV(b, T); P0 = DIV(prod0', T) =
      Q d - prod1' F exactly; flip = ADD(DIV(SUB(0, T), T), 1) = F mod W;
      M = MUL(prod1', flip) is a multiple of F and P0 < F, so (B2)
      OR(P0, M) = P0 + M; and P0 + M = Q d mod W.
  B3  iv0 = XOR(MUL(3, d), 2): d iv0 = 1 mod 16 for odd d.
  S5  each Newton step iv' = MUL(iv, SUB(2, MUL(d, iv))) takes d iv = 1 mod 2^k
      to d iv' = 1 mod 2^min(2k, 256): six steps from 2^4 reach 2^256.
  S6  q = MUL(P, iv6) = Q d iv6 = Q mod W, and Q < W: q = Q.
"""

import sys
import time

from z3 import (
    BitVec,
    BitVecVal,
    If,
    Int,
    Ints,
    Not,
    Solver,
    ULT,
    unsat,
)

W = 2**256
FAILED = []


def prove(name, claim, hyps=(), quiet=False, timeout_ms=120_000):
    s = Solver()
    s.set("timeout", timeout_ms)
    for h in hyps:
        s.add(h)
    s.add(Not(claim))
    t0 = time.time()
    r = s.check()
    ok = r == unsat
    if not ok:
        FAILED.append(name)
    if not quiet or not ok:
        print(f"{'PROVED' if ok else 'FAILED'}  {name}  ({time.time() - t0:.2f}s){'' if ok else '  ' + str(r)}", flush=True)
    return ok


def S1(s):
    a, prod0, prod1 = Ints("a prod0 prod1")
    N = a * 2**s
    hyps = [a >= 0, a < W, prod0 == (a * 2**s) % W, prod1 == a / 2 ** (256 - s)]
    return prove(f"S1 (s={s}): SHR(256 - s, a) W + SHL(s, a) = a 2^s", N == prod1 * W + prod0, hyps)


def S2():
    N, prod0, prod1, r, p1n, p0n = Ints("N prod0 prod1 r p1n p0n")
    hyps = [
        N == prod1 * W + prod0,
        prod0 >= 0, prod0 < W, prod1 >= 0, prod1 < W,
        r >= 0, r <= N, r < W,
        p1n == (prod1 - If(r > prod0, 1, 0)) % W,  # SUB(prod1, GT(remainder, prod0))
        p0n == (prod0 - r) % W,  # SUB(prod0, remainder)
    ]
    claim = (p1n * W + p0n == N - r)
    return prove("S2: the borrow: SUB(prod1, GT(r, prod0)) W + SUB(prod0, r) = N - r", claim, hyps)


def S3():
    N, b, Q = Ints("N b Q")
    return prove("S3: Q b <= N < b W, b > 0  =>  Q < W", Q < W, [Q * b <= N, N < b * W, b >= 1, Q >= 0])


def B1(t):
    b = BitVec("b", 256)
    T = BitVecVal(1 << t, 256)
    mask = BitVecVal((2 << t) - 1, 256)
    return prove(f"B1 t={t}", ((b & -b) == T) == ((b & mask) == T), [b != 0], quiet=True)


def B2():
    x, y, F = BitVec("x", 256), BitVec("y", 256), BitVec("F", 256)
    hyps = [F != 0, F & (F - 1) == 0, ULT(x, F), y & (F - 1) == 0]
    return prove("B2: OR(x, y) = x + y for x < F, y a multiple of F, F a power of two", (x | y) == x + y, hyps)


def B3():
    d = BitVec("d", 256)
    return prove("B3: d XOR(MUL(3, d), 2) = 1 mod 16 for odd d", (d * ((3 * d) ^ 2)) & 15 == 1, [d & 1 == 1])


def S4(t):
    """Per t: twos = T = 2^t, the division by it, the flip and the OR, for one t."""
    T = 2**t
    F = W // T
    Q, b, d, p1n, p0n, QD, P0, flip, M, P, c = Ints("Q b d p1n p0n QD P0 flip M P c")
    ok = True
    # b mod 2T = T (B1's right side) gives b = T d with d odd, d = DIV(b, T)
    ok &= prove(f"S4 t={t}: b = T DIV(b, T), odd", (b == T * (b / T)) & ((b / T) % 2 == 1),
                [b >= 1, b < W, b % (2 * T) == T], quiet=True)
    # Q b = T (Q d): the identity, then prod0' = T (Q d - prod1' F)
    ok &= prove(f"S4 t={t}: Q (T d) = T (Q d)", Q * (T * d) == T * (Q * d), quiet=True)
    hyps = [
        p1n * W + p0n == T * QD,  # S2 with Q b = T Q d
        p0n >= 0, p0n < W, p1n >= 0, p1n < W,
        P0 == p0n / T,  # DIV(prod0', twos)
        flip == (((W - T) % W) // T + 1) % W,  # ADD(DIV(SUB(0, twos), twos), 1)
        M == (p1n * flip) % W,  # MUL(prod1', flip): flip is a constant here
    ]
    ok &= prove(f"S4 t={t}: P0 = Q d - prod1' F, P0 < F, M = 0 mod F", (P0 == QD - p1n * F) & (P0 < F) & (P0 >= 0) & (M % F == 0) & (M >= 0) & (M < W), hyps, quiet=True)
    # with B2: P = P0 + M, and P = Q d mod W, 0 <= P < W
    ok &= prove(f"S4 t={t}: P0 + M = Q d mod W", ((P0 + M - QD) % W == 0) & (P0 + M < W),
                hyps + [P0 == QD - p1n * F, P0 >= 0, P0 < F, M % F == 0, M >= 0, M < W], quiet=True)
    return ok


def S5(k):
    d, x, e, g, f, p, y, xn = Ints("d x e g f p y xn")
    k2 = min(2 * k, 256)
    hyps = [p == d * x, y == 2 - p + g * W, xn == x * y - f * W, p == 1 + e * 2**k]
    ok = prove(
        f"S5 {k:>3} -> {k2}: d MUL(x, SUB(2, MUL(d, x))) = 1 - e^2 2^{2 * k} + W (...)",
        d * xn == 1 - e * e * 2 ** (2 * k) + W * (g * (1 + e * 2**k) - d * f),
        hyps,
    )
    # so d x' = 1 mod 2^k2: the right side is 1 plus a multiple of 2^k2
    z1, z2 = Ints("z1 z2")
    ok &= prove(f"S5 {k:>3} -> {k2}: = 1 mod 2^{k2}", (1 - z1 * 2 ** (2 * k) + W * z2) % 2**k2 == 1)
    return ok


def S6():
    Q, d, c, h, m, q, P, iv, z = Ints("Q d c h m q P iv z")
    ok = prove("S6: P = Q d - c W, d iv = 1 + h W  =>  P iv - m W = Q + W (Q h - c iv - m)",
               P * iv - m * W == Q + W * (Q * h - c * iv - m), [P == Q * d - c * W, d * iv == 1 + h * W])
    ok &= prove("S6: q = Q + W z, 0 <= q, Q < W  =>  q = Q", q == Q, [q == Q + W * z, q >= 0, q < W, Q >= 0, Q < W])
    return ok


def main():
    t0 = time.time()
    ok = S1(128) & S1(255) & S2() & S3() & B2() & B3()
    b1 = all([B1(t) for t in range(256)])
    print(f"{'PROVED' if b1 else 'FAILED'}  B1: AND(SUB(0, b), b) = 2^t iff b = 2^t d, d odd: t = 0..255")
    s4 = all([S4(t) for t in range(256)])
    print(f"{'PROVED' if s4 else 'FAILED'}  S4: DIV by twos, the flip, OR = ADD, P = Q d mod W: t = 0..255")
    ok &= b1 & s4
    for k in (4, 8, 16, 32, 64, 128):
        ok &= S5(k)
    ok &= S6()
    names = {128: "K127 divq", 255: "K19 divh"}
    for s in (128, 255):
        print(f"{'PROVED' if ok else 'FAILED'}  {names[s].split()[0]}  {names[s].split()[1]}(a, b) = floor(a 2^{s} / b): S1-S6, B1-B3")
    print(f"kernel.py: {time.time() - t0:.0f}s")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

"""The lemmas the Halmos proofs rest on, proved with Z3 over unbounded integers.

    python test/proofs/lemmas.py      # prints one line per lemma, exits 1 on any failure

The Halmos proofs (test/proofs/Proofs*.t.sol) run with multiplication,
division and remainder uninterpreted: the solver may assume nothing about
MUL(a, b) except that the same arguments give the same word. So a proof there
holds for any interpretation of those opcodes, and the reference specs reach
exact integers only through the primitives below. Each lemma states, for all
inputs, that a primitive computes the exact integer it stands for under the
EVM's own definition of the opcodes (MUL is a b mod 2^256, MULMOD is a b mod n,
DIV is the floor quotient, MOD the remainder).

  L1  umul (Wide.sol): l = a b mod 2^256, m = a b mod (2^256 - 1),
      h = (m - l - [m < l]) mod 2^256  =>  h 2^256 + l = a b.
  L2  smul (Wide.sol): for words a, b read as two's complement A, B,
      ((h - [A < 0] b - [B < 0] a) mod 2^256, l), the first word read as
      two's complement, is the exact A B.
  L3  for x, y < 2^19 (FP19's exponent fields), MUL(x, y) = 0 iff x = 0 or
      y = 0. Handed to the solver as an assumption (Harness.assumeL3).
  L4  for 2 <= u < 2^256, DIV(2^256 - u, u) + 1 = floor(2^256 / u) (FP127's inv).
  L5  Wide.uabs(x) = (x XOR m) - m, m = SAR(255, x), is |x| for every
      two's complement x (bit-vectors).
  L6  two significands ma, mb in [2^236, 2^237): the high word of ma mb is
      in [2^216, 2^218) (the product in [2^472, 2^474)).
  L7  the quotients FP19 rounds are at least 2^254: floor(ma 2^255 / mb),
      floor(2^491 / m) and floor(m 2^60 / 5^18) for significands ma, mb, m.
      L6 and L7 are handed to the solver as assumptions (ProofsFP19).
  K18 Kernels.q18: for m < 2^237, the two word divisions by 5^18 give
      floor(m 2^60 / 5^18), and no intermediate leaves a word.
"""

import sys

from z3 import And, If, Int, Ints, Not, Or, Solver, sat, unsat, set_param

W = 2**256


def prove(name, claim, *hyps, timeout_ms=600_000):
    s = Solver()
    s.set("timeout", timeout_ms)
    for h in hyps:
        s.add(h)
    s.add(Not(claim))
    r = s.check()
    ok = r == unsat
    print(f"{'PROVED' if ok else 'FAILED'}  {name}" + ("" if ok else f"  ({r}{': ' + str(s.model()) if r == sat else ''})"), flush=True)
    return ok


def word(x):
    return And(x >= 0, x < W)


def L1():
    # The claim depends on a b only: take P = a b as the variable, P <= (2^256 - 1)^2.
    P, l, m, h = Ints("P l m h")
    hyps = [
        P >= 0,
        P <= (W - 1) ** 2,
        l == P % W,
        m == P % (W - 1),
        h == (m - l - If(m < l, 1, 0)) % W,
    ]
    return prove("L1  umul: (MULMOD(a,b,2^256-1) - MUL(a,b) - borrow, MUL(a,b)) = a b", h * W + l == P, *hyps)


def L2():
    ok = True
    a, b = Ints("a b")
    for sa in (0, 1):
        for sb in (0, 1):
            A = a - sa * W  # the two's complement reading of a
            B = b - sb * W
            P = a * b
            h = P / W  # floor, P >= 0
            l = P % W
            hs = (h - sa * b - sb * a) % W
            hs_signed = If(hs >= W // 2, hs - W, hs)
            hyps = [word(a), word(b), (a >= W // 2) == (sa == 1), (b >= W // 2) == (sb == 1)]
            ok &= prove(
                f"L2  smul, signs ({'-' if sa else '+'}, {'-' if sb else '+'}): signed high word by the corrections",
                hs_signed * W + l == A * B,
                *hyps,
            )
    return ok


def L3():
    x, y = Ints("x y")
    hyps = [x >= 0, x < 2**19, y >= 0, y < 2**19]
    return prove("L3  MUL of two exponent fields is zero iff one is", ((x * y) % W == 0) == Or(x == 0, y == 0), *hyps)


def L4():
    u, q, r, q2, r2 = Ints("u q r q2 r2")
    hyps = [u >= 2, u < W, W == q * u + r, r >= 0, r < u, W - u == q2 * u + r2, r2 >= 0, r2 < u]
    return prove("L4  DIV(2^256 - u, u) + 1 = floor(2^256 / u)", q2 + 1 == q, *hyps)


def L5():
    from z3 import BitVec, If as BIf

    x = BitVec("x", 256)
    m = x >> 255  # arithmetic shift in z3
    return prove("L5  (x XOR SAR(255, x)) - SAR(255, x) = |x|", (x ^ m) - m == BIf(x < 0, -x, x))


def L6():
    ma, mb = Ints("ma mb")
    P = ma * mb
    hyps = [ma >= 2**236, ma < 2**237, mb >= 2**236, mb < 2**237]
    ok = prove("L6  ma mb in [2^472, 2^474) for significands", And(P >= 2**472, P < 2**474), *hyps)
    p = Int("p")
    ok &= prove("L6  so its high word is in [2^216, 2^218)", And(p / W >= 2**216, p / W < 2**218), p >= 2**472, p < 2**474)
    return ok


def L7():
    ma, mb, m, Q = Ints("ma mb m Q")
    sig = lambda v: [v >= 2**236, v < 2**237]
    ok = prove("L7  floor(ma 2^255 / mb) >= 2^254", Q >= 2**254,
               *sig(ma), *sig(mb), Q * mb <= ma * 2**255, ma * 2**255 < (Q + 1) * mb)
    ok &= prove("L7  floor(2^491 / m) >= 2^254", Q >= 2**254, *sig(m), Q * m <= 2**491, 2**491 < (Q + 1) * m)
    ok &= prove("L7  floor(m 2^60 / 5^18) >= 2^254", (m * 2**60) / 5**18 >= 2**254, *sig(m))
    return ok


def K18():
    m = Int("m")
    c = 5**18
    A = (m / 2**100) * 2**60  # shl(60, shr(100, m))
    hi = A / c  # div(A, c)
    lo_num = (A % c) * 2**100 + (m % 2**100) * 2**60  # add(shl(100, mod(A, c)), shl(60, and(m, 2^100 - 1)))
    q = hi * 2**100 + lo_num / c
    hyps = [m >= 0, m < 2**237]
    claim = And(
        q == (m * 2**60) / c,
        A < W,
        hi * 2**100 < W,
        (A % c) * 2**100 < W,
        lo_num < W,
        q < W,
    )
    return prove("K18 q18: floor(m 2^60 / 5^18) by two word divisions, every intermediate a word", claim, *hyps)


if __name__ == "__main__":
    set_param("parallel.enable", True)
    results = [L1(), L2(), L3(), L4(), L5(), L6(), L7(), K18()]
    sys.exit(0 if all(results) else 1)

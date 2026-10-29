"""Halmos 0.3.3 with the CLZ opcode and commuted products.

    python test/proofs/halmos_clz.py --contract ProofsBL127 ...   # Halmos's own arguments
    python test/proofs/halmos_clz.py --selftest

Two changes, made at run time to the pinned Halmos (it refuses any other
version), then Halmos's own main runs:

CLZ (EIP-7939, 0x1e). Halmos 0.3.3 has none (a16z/halmos#586), and both
libraries count leading bits with it. CLZ(x) is 256 for x = 0, else
255 - msb(x). The symbolic term is the binary search on the top bits: at each
of eight steps, when the top s bits of the remaining word are zero, add s and
shift them out. --selftest proves it equal to the definition for every word
(Z3, bit-vectors) and checks it on 34,897 concrete words. The patch inserts
one branch into SEVM.run, before SAR's.

Commuted products: see commute_products below.
"""

import inspect
import random
import sys
import textwrap

import halmos
import halmos.sevm as sevm
from z3 import And, BitVecVal, If, Not, Or, ULT, simplify

PINNED = "0.3.3"


def clz_term(x):
    """CLZ of a 256-bit z3 term, 256 at zero."""
    n = BitVecVal(0, 256)
    y = x
    for s in (128, 64, 32, 16, 8, 4, 2, 1):
        top_zero = ULT(y, BitVecVal(1 << (256 - s), 256))
        n = If(top_zero, n + s, n)
        y = If(top_zero, y << s, y)
    # y is now 0 (x = 0) or has its top bit set; the search counted 255 for 0
    return If(x == 0, BitVecVal(256, 256), n)


def clz_word(w):
    """CLZ of a Halmos word (concrete or symbolic)."""
    BV = sevm.BV
    if w.is_concrete:
        v = w.value
        return BV(256 - v.bit_length(), size=256)
    return BV(simplify(clz_term(w.as_z3())), size=256)


def patch():
    version = getattr(halmos, "__version__", None)
    try:
        from importlib.metadata import version as _v

        version = _v("halmos")
    except Exception:
        pass
    if version != PINNED:
        sys.exit(f"halmos_clz: written for halmos {PINNED}, found {version}")
    src = textwrap.dedent(inspect.getsource(sevm.SEVM.run))
    anchor = "                elif opcode == OP_SAR:\n"
    # dedent removed the method's own four-space indent
    anchor = anchor[4:]
    if src.count(anchor) != 1:
        sys.exit("halmos_clz: SEVM.run has changed; the CLZ patch does not apply")
    branch = (
        "            elif opcode == 0x1E:\n"
        "                state.push(_halmos_clz_word(state.popi()))\n\n"
    )
    src = src.replace(anchor, branch + anchor)
    ns = dict(vars(sevm))
    ns["_halmos_clz_word"] = clz_word
    exec(compile(src, sevm.__file__, "exec"), ns)
    sevm.SEVM.run = ns["run"]
    commute_products()


def commute_products():
    """Uninterpreted products with their operands in one canonical order.

    Halmos leaves a product of two symbolic words uninterpreted (f_evm_bvmul),
    first, and the only fact the solver has is that equal operands give equal
    products: MUL(a, b) and MUL(b, a) would be unrelated terms. Ordering the
    operands by their term id makes them one term. Sound, because
    multiplication commutes; it lets a spec that writes a product in the other
    order than the library meet the library's term. (The specs spell each
    product's operands as the library does, so the same pair of terms meets.)
    """
    from halmos.bitvec import HalmosBitVec

    orig = HalmosBitVec.mul

    def mul(self, other, *, abstraction=None):
        if (
            abstraction is not None
            and self.is_symbolic
            and other.is_symbolic
            and self.as_z3().get_id() > other.as_z3().get_id()
        ):
            self, other = other, self
        return orig(self, other, abstraction=abstraction)

    HalmosBitVec.mul = mul


def selftest():
    from z3 import BitVec, Solver, unsat

    words = [0] + [1 << i for i in range(256)] + [(1 << i) | (1 << j) for i in range(256) for j in range(i)]
    rng = random.Random(7939)
    words += [rng.getrandbits(rng.randint(1, 256)) for _ in range(2000)]
    for v in words:
        got = simplify(clz_term(BitVecVal(v, 256))).as_long()
        assert got == 256 - v.bit_length(), (hex(v), got)
    # and symbolically: for all x != 0, 2^(255 - clz) <= x < 2^(256 - clz)
    x = BitVec("x", 256)
    c = clz_term(x)
    s = Solver()
    s.add(x != 0)
    one = BitVecVal(1, 256)
    s.add(Not(And(ULT(c, 256), Not(ULT(x, one << (255 - c))), Or(c == 0, ULT(x, one << (256 - c))))))
    assert s.check() == unsat, "clz_term is wrong for some x"
    print(f"halmos_clz: CLZ term agrees with the definition on {len(words)} words and symbolically")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        selftest()
        sys.exit(0)
    patch()
    from halmos.__main__ import main

    sys.exit(main())

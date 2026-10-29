#!/usr/bin/env python3
"""factorial as a table, for BL19 and BL127, with the Yul text each needs.

    uv run scripts/bl19/generators/facttab.py            # print the tables' sizes and check the words
    uv run scripts/bl19/generators/facttab.py --yul      # print the Yul of both tables
    uv run scripts/bl19/generators/facttab.py --check    # do BL19.yul.src and BL127.yul.src hold it verbatim?

BL19: n! for n = 2..170, each the oracle's word (scripts/bl19/oracle.py
`encode`, nearest, ties away from zero), so the table is the correctly rounded
value by construction; 0! and 1! are one before the lookup, and 171! is past
the domain (Overflow). 170! is the largest factorial a binary64 holds; the
BL19 domain stops there. The lookup is a comparison tree on n, a binary
search over the 169 entries: eight tests and one push, where a flat switch
would compare against every earlier case.

BL127: n! for n = 0..33 as integers times 2^128, two to a word (the even n in
the high 128 bits, the odd n in the low, 33! < 2^123), picked by a comparison
tree on n/2 and one shift: the word moved left by 128 for odd n, then its
high 128 bits.
"""
from __future__ import annotations

import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/bl19"))
import oracle as O  # noqa: E402

BL19_LO, BL19_HI = 2, 170
BL127_HI = 33
HIGH128 = ((1 << 128) - 1) << 128


def bl19_words() -> dict[int, int]:
    return {n: O.encode(Fraction(math.factorial(n))) for n in range(BL19_LO, BL19_HI + 1)}


def bl127_words() -> dict[int, int]:
    w = {}
    for i in range(BL127_HI // 2 + 1):
        a, b = math.factorial(2 * i), math.factorial(2 * i + 1)
        assert b < 1 << 128
        w[i] = (a << 128) | b
    return w


def tree(var: str, out: str, table: dict[int, int], lo: int, hi: int, ind: str) -> list[str]:
    """Yul assigning table[var] to out for var in [lo, hi], by halving the
    range with lt: ceil(log2(hi - lo + 1)) tests to a leaf."""
    if lo == hi:
        return [f"{ind}{out} := 0x{table[lo]:064x}"]
    mid = (lo + hi + 1) // 2
    return ([f"{ind}switch lt({var}, {mid})", f"{ind}case 0 {{"]
            + tree(var, out, table, mid, hi, ind + "    ")
            + [f"{ind}}}", f"{ind}default {{"]
            + tree(var, out, table, lo, mid - 1, ind + "    ")
            + [f"{ind}}}"])


def emit_bl19() -> str:
    lines = [
        f"/// n! for {BL19_LO} <= n <= {BL19_HI}, the correctly rounded word of each, by a",
        "/// binary search on n (facttab.py: every word is the oracle's encoding of",
        "/// the exact factorial).",
        "function facttab(n) -> r {",
    ]
    lines += tree("n", "r", bl19_words(), BL19_LO, BL19_HI, "    ")
    lines.append("}")
    return "\n".join(lines) + "\n"


def emit_bl127() -> str:
    lines = [
        f"/// (2i)! and (2i + 1)! for 0 <= i <= {BL127_HI // 2}, the even one in the high",
        "/// 128 bits, by a binary search on i (facttab.py).",
        "function facttab(i) -> w {",
    ]
    lines += tree("i", "w", bl127_words(), 0, BL127_HI // 2, "    ")
    lines.append("}")
    return "\n".join(lines) + "\n"


def check_source() -> bool:
    ok = True
    for name, text in (("contracts/src/bl19/BL19.yul.src", emit_bl19()),
                       ("contracts/src/bl127/BL127.yul.src", emit_bl127())):
        src = (ROOT / name).read_text()
        hit = text.strip("\n") in src
        print(f"{name} holds facttab.py's Yul verbatim: {'yes' if hit else 'NO'}")
        ok &= hit
    return ok


def verify() -> None:
    for n, w in bl19_words().items():
        assert O.op_factorial(O.encode(Fraction(n))) == w
        assert O.decode(w) == Fraction(math.factorial(n)) or n > 57
    for i, w in bl127_words().items():
        for n, half in ((2 * i, w >> 128), (2 * i + 1, w & ((1 << 128) - 1))):
            assert half == math.factorial(n)
            # the Yul's pick: the word moved left by 128 for odd n, its high half
            assert ((w << (128 * (n & 1))) & HIGH128) & ((1 << 256) - 1) == math.factorial(n) << 128
    exact = max(n for n, w in bl19_words().items() if O.decode(w) == math.factorial(n))
    print(f"BL19: {BL19_HI - BL19_LO + 1} words, n! exact in the word up to n = {exact}; "
          f"BL127: {BL127_HI // 2 + 1} words, 0! to {BL127_HI}!")


def main(argv: list[str]) -> int:
    if "--yul" in argv:
        print(emit_bl19())
        print(emit_bl127())
        return 0
    if "--check" in argv:
        return 0 if check_source() else 1
    verify()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

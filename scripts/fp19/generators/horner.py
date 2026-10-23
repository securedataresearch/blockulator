#!/usr/bin/env python3
"""Horner's rule as the EVM kernels run it, shared by FP19 (kernel254.py) and
FP127 (scripts/fp127/generators/kernel192.py): an exact integer model, its
error bound, and the Yul text.

A step p_j = c_j + p_{j+1} u is the high word of a 512-bit product written in
line, hi(p, T) = floor(p T / 2^256) (mul, mulmod, sub, sub, lt): measured at
91 gas against 215 through a mulwu helper and 160 through a one-call one.
Where the step's error reaches the result only times u^j, it runs in one
word, ((p >> a)(T >> b)) >> (256 - a - b), one mul (32 gas): its truncation
is below (2^a T + 2^b p)/2^256 units, and the generator takes a step in one
word while that times u^j stays under cheap_step units and the one-word
steps together under cheap_all.
"""
from __future__ import annotations

from mpmath import mpf, power, nint, ceil


def hx(v: int) -> str:
    return f"0x{v:x}"


def hi(a: int, b: int) -> int:
    return (a * b) >> 256


class Horner:
    """P(v) = sum c_j v^j for v in [0, vmax] (or [-vmax, vmax], signed), as the
    Yul runs it. The partial sums stay positive when every c_j is; when some
    are negative (alternating, as log2(1 + w)/w's) the accumulator is signed
    and the high word is corrected for it:
    T = v 2^sigma an integer, p at 2^-rho, p_d = C_d and then
    p_j = C_j + hi(p_{j+1}, T) or, in one word, C_j + ((p_{j+1} >> a_j)
    (T >> b)) >> (256 - a_j - b). hi(p, T) = p_val v 2^(rho + sigma - 256), so
    the Yul's Horner runs in u = v 2^(sigma - 256) with C_j = c_j 2^(-(sigma -
    256) j) 2^rho rounded to nearest. Error bound (units of 2^-rho):
    sum_j (1/2 + theta_j) umax^j, theta_j the step's floor (1) plus the
    one-word truncation; plus the fit's."""

    def __init__(self, coeffs, sigma, rho, vmax, fit_rel, fmax, name, var, signed=False,
                 cheap_step=mpf(2) ** -9, cheap_all=mpf(2) ** -6):
        self.name, self.var, self.signed = name, var, signed
        self.cheap_step, self.cheap_all = mpf(cheap_step), mpf(cheap_all)
        self.sigma, self.rho = sigma, rho
        k = sigma - 256
        self.C = [int(nint(c * power(2, -k * j) * power(2, rho))) for j, c in enumerate(coeffs)]
        self.accsigned = any(c < 0 for c in self.C)
        assert not (self.accsigned and signed), "a signed variable takes positive coefficients"
        self.Tmax = int(ceil(vmax * power(2, sigma)))
        assert self.Tmax < 1 << 256
        self.umax = mpf(self.Tmax) / power(2, 256)
        d = len(self.C) - 1
        # Pmax[j]: a bound on the computed p_j
        self.Pmax = [0] * (d + 1)
        for j in range(d, -1, -1):
            self.Pmax[j] = int(sum(abs(mpf(self.C[i])) * self.umax ** (i - j) for i in range(j, d + 1))) + 8
        best = None
        for b in range(0, 257):
            steps, extra = self._plan(b)
            ncheap = sum(1 for s in steps if s)
            if best is None or ncheap > best[0]:
                best = (ncheap, b, steps, extra)
        self.ncheap, self.b, self.steps, self.extra = best
        self.fit_units = fit_rel * fmax * power(2, rho)
        theta = [1 + (st[2] if st else 0) for st in self.steps]    # for j = d-1 .. 0
        self.err = mpf(1) / 2 * self.umax ** d                     # C_d's rounding
        for idx, j in enumerate(range(d - 1, -1, -1)):
            self.err += (mpf(1) / 2 + theta[idx]) * self.umax ** j
        self.err += self.fit_units

    def _plan(self, b):
        """One-word steps from the top for a given b, while admitted."""
        d = len(self.C) - 1
        Ts = self.Tmax >> b
        steps = []
        extra = mpf(0)
        cheap = True
        for j in range(d - 1, -1, -1):
            st = None
            if cheap and Ts:
                P = self.Pmax[j + 1]
                a = max(0, P.bit_length() + Ts.bit_length() - (255 if self.signed or self.accsigned else 256))
                s = 256 - a - b
                if s >= 0:
                    t = (mpf(2) ** a * self.Tmax + mpf(2) ** b * P) / power(2, 256)
                    if t * self.umax ** j <= self.cheap_step and extra + t * self.umax ** j <= self.cheap_all:
                        st = (a, s, t)
                        extra += t * self.umax ** j
            if st is None:
                cheap = False
            steps.append(st)
        return steps, extra

    def eval(self, T: int) -> int:
        """T a Python int (negative allowed when signed): floors toward minus
        infinity, as sar and the corrected high word do."""
        assert abs(T) <= self.Tmax and (self.signed or T >= 0)
        p = self.C[-1]
        Ts = T >> self.b
        for st, c in zip(self.steps, reversed(self.C[:-1])):
            assert p >= 0 or self.accsigned
            if st:
                a, s, _ = st
                pr = (p >> a) * Ts
                assert abs(pr) < 1 << 255
                p = (pr >> s) + c
            else:
                p = ((p * T) >> 256) + c
        return p

    def yul(self, acc: str) -> list[str]:
        """The Horner lines on the variable self.var into acc. Signed: the
        one-word product of p >= 0 and a signed T >> b is a plain mul (it
        fits), floored by sar; the high word of p T is the unsigned one less
        p when T < 0 (ng)."""
        out = []
        M = (1 << 256) - 1
        sh = "sar" if self.signed else "shr"
        psh = "sar" if self.accsigned else "shr"
        osh = "sar" if self.signed or self.accsigned else "shr"
        if self.ncheap:
            out.append(f"let {self.var}s := {sh}({self.b}, {self.var})")
        out.append(f"{acc} := {hx(self.C[-1] & M)}")
        for st, c in zip(self.steps, reversed(self.C[:-1])):
            c = c & M
            if st:
                a, s, _ = st
                pa = f"{psh}({a}, {acc})" if a else acc
                out.append(f"{acc} := add({osh}({s}, mul({pa}, {self.var}s)), {hx(c)})")
            elif self.accsigned:
                out.append(f"{{ let pl := mul({acc}, {self.var}) let ph := mulmod({acc}, {self.var}, not(0)) "
                           f"{acc} := add(sub(sub(sub(ph, pl), lt(ph, pl)), mul(slt({acc}, 0), {self.var})), {hx(c)}) }}")
            elif self.signed:
                out.append(f"{{ let pl := mul({acc}, {self.var}) let ph := mulmod({acc}, {self.var}, not(0)) "
                           f"{acc} := add(sub(sub(sub(ph, pl), lt(ph, pl)), mul(ng, {acc})), {hx(c)}) }}")
            else:
                out.append(hiline(acc, acc, self.var, hx(c)))
        return out


def hiline(dst: str, a: str, b: str, plus: str) -> str:
    """dst := hi(a, b) + plus, in line."""
    return (f"{{ let pl := mul({a}, {b}) let ph := mulmod({a}, {b}, not(0)) "
            f"{dst} := add(sub(sub(ph, pl), lt(ph, pl)), {plus}) }}")


def hiset(dst: str, a: str, b: str) -> str:
    """dst := hi(a, b), in line."""
    return (f"{{ let pl := mul({a}, {b}) let ph := mulmod({a}, {b}, not(0)) "
            f"{dst} := sub(sub(ph, pl), lt(ph, pl)) }}")


def tree(var: str, leaf, nbits: int = 4, ind: str = "    ") -> list[str]:
    """Binary dispatch on the low nbits of var: four tests reach any of 16
    entries (the linear switch averages eight; K1 measured 156 against 252
    gas). leaf(j) is the code for entry j, '' for none."""
    out = []

    def rec(bit, prefix, depth):
        pad = ind * depth
        if bit < 0:
            code = leaf(prefix)
            if code:
                out.append(pad + code)
            return
        out.append(f"{pad}switch and({var}, {1 << bit})")
        out.append(f"{pad}case 0 {{")
        rec(bit - 1, prefix, depth + 1)
        out.append(f"{pad}}}")
        out.append(f"{pad}default {{")
        rec(bit - 1, prefix | (1 << bit), depth + 1)
        out.append(f"{pad}}}")

    rec(nbits - 1, 0, 1)
    return out

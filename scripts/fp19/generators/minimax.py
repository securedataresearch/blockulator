#!/usr/bin/env python3
"""Minimax polynomial fits by the Remez exchange, and a dense-grid
certificate of their sup norm, for the FP19 and FP127 kernels.

    from minimax import remez, certify

remez(f, deg, a, b, rel=True) returns the coefficients (ascending, in x) of
the degree-deg polynomial that minimises max |P(x) - f(x)| (rel: divided by
|f(x)|; w: divided by w(x), a tolerance that varies across the interval) on
[a, b], and the levelled error E of the last reference. The fit
runs in t = (2x - a - b)/(b - a) on [-1, 1], where the monomial basis is well
conditioned at the working precision, and converts back to x exactly in
mpmath. Every fit here is a minimax fit: no coefficient is a Taylor
coefficient.

certify(coeffs, f, a, b, n) evaluates |P - f| (relative if asked) on n + 1
Chebyshev-spaced points plus n + 1 uniform points at the working precision
and returns the largest, the number the Yul comments quote as the fit's sup
norm. A degree-d polynomial's error between dense points can exceed the
sampled maximum only by the curvature term, which at these grid densities
(10^4 points against at most 28 extrema) is far below the last digit quoted.
"""
from __future__ import annotations

from mpmath import mp, mpf, cos, pi, matrix, lu_solve, findroot, diff, fabs


def _horner(c, x):
    r = c[-1]
    for v in reversed(c[:-1]):
        r = r * x + v
    return r


def _t_to_x(ct, a, b):
    """Coefficients in t = (2x - a - b)/(b - a) to coefficients in x."""
    al = 2 / (b - a)
    be = -(a + b) / (b - a)
    n = len(ct)
    # P(x) = sum ct_k (al x + be)^k, expanded
    cx = [mpf(0)] * n
    binom = [[mpf(0)] * n for _ in range(n)]
    for k in range(n):
        binom[k][0] = mpf(1)
        for j in range(1, k + 1):
            binom[k][j] = binom[k - 1][j - 1] + (binom[k - 1][j] if j < k else 0)
    for k in range(n):
        for j in range(k + 1):
            cx[j] += ct[k] * binom[k][j] * al ** j * be ** (k - j)
    return cx


def remez(f, deg, a, b, rel=True, iters=40, tol=mpf(10) ** -12, grid=4000, w=None):
    a, b = mpf(a), mpf(b)
    g = lambda t: f((b - a) / 2 * t + (a + b) / 2)
    wt = (lambda t: w((b - a) / 2 * t + (a + b) / 2)) if w else None
    n = deg + 2
    ref = [-cos(pi * i / (n - 1)) for i in range(n)]
    E = mpf(0)
    ct = None
    for _ in range(iters):
        M = matrix(n, n)
        y = matrix(n, 1)
        for i, t in enumerate(ref):
            gv = g(t)
            wv = wt(t) if wt else fabs(gv) if rel else mpf(1)
            for j in range(deg + 1):
                M[i, j] = t ** j
            M[i, deg + 1] = (-1) ** i * wv
            y[i, 0] = gv
        sol = lu_solve(M, y)
        ct = [sol[j, 0] for j in range(deg + 1)]
        E = sol[deg + 1, 0]

        def err(t):
            gv = g(t)
            e = _horner(ct, t) - gv
            return e / wt(t) if wt else e / fabs(gv) if rel else e

        # local extrema of err on a dense Chebyshev-spaced grid, refined
        ts = [-cos(pi * i / grid) for i in range(grid + 1)]
        es = [err(t) for t in ts]
        ext = [(ts[0], es[0])]
        for i in range(1, grid):
            if (es[i] - es[i - 1]) * (es[i + 1] - es[i]) <= 0:
                lo, hi = ts[i - 1], ts[i + 1]
                for _ in range(60):          # golden-section on |err|
                    m1 = lo + (hi - lo) * mpf("0.381966011250105")
                    m2 = lo + (hi - lo) * mpf("0.618033988749895")
                    if fabs(err(m1)) > fabs(err(m2)):
                        hi = m2
                    else:
                        lo = m1
                tm = (lo + hi) / 2
                ext.append((tm, err(tm)))
        ext.append((ts[-1], es[-1]))
        # keep alternating extrema, the largest of each same-sign run
        alt = []
        for t, e in ext:
            if alt and (alt[-1][1] > 0) == (e > 0):
                if fabs(e) > fabs(alt[-1][1]):
                    alt[-1] = (t, e)
            else:
                alt.append((t, e))
        while len(alt) > n:
            # drop the smaller end
            if fabs(alt[0][1]) < fabs(alt[-1][1]):
                alt.pop(0)
            else:
                alt.pop()
        if len(alt) < n:
            raise RuntimeError(f"remez: {len(alt)} alternation points for degree {deg}")
        ref = [t for t, _ in alt]
        emax = max(fabs(e) for _, e in alt)
        if emax / fabs(E) - 1 < tol:
            break
    return _t_to_x(ct, a, b), fabs(E)


def certify(coeffs, f, a, b, n=10000, rel=True, w=None):
    a, b = mpf(a), mpf(b)
    worst = mpf(0)
    pts = [(b - a) / 2 * (-cos(pi * i / n)) + (a + b) / 2 for i in range(n + 1)]
    pts += [a + (b - a) * i / n for i in range(n + 1)]
    for x in pts:
        fv = f(x)
        e = fabs(_horner(coeffs, x) - fv)
        if w:
            e /= w(x)
        elif rel:
            e /= fabs(fv)
        worst = max(worst, e)
    return worst

"""Exact rational linear algebra (no floating point, no dependencies)."""

from __future__ import annotations

from fractions import Fraction
from math import lcm

Vector = list[Fraction]


def rref(rows: list[list[Fraction]], ncols: int) -> tuple[list[list[Fraction]], list[int]]:
    """Reduced row echelon form. Returns the non-zero rows and pivot columns."""
    m = [list(r) for r in rows]
    pivots: list[int] = []
    r = 0
    for c in range(ncols):
        pivot = next((i for i in range(r, len(m)) if m[i][c] != 0), None)
        if pivot is None:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        inv = 1 / m[r][c]
        m[r] = [v * inv for v in m[r]]
        for i in range(len(m)):
            if i != r and m[i][c] != 0:
                factor = m[i][c]
                m[i] = [a - factor * b for a, b in zip(m[i], m[r])]
        pivots.append(c)
        r += 1
        if r == len(m):
            break
    return m[:r], pivots


def nullspace(rows: list[list[Fraction]], ncols: int) -> list[Vector]:
    """Basis of {v : rows · v = 0}."""
    reduced, pivots = rref(rows, ncols)
    pivot_set = set(pivots)
    basis = []
    for free in (c for c in range(ncols) if c not in pivot_set):
        v = [Fraction(0)] * ncols
        v[free] = Fraction(1)
        for row, pc in zip(reduced, pivots):
            v[pc] = -row[free]
        basis.append(v)
    return basis


def rank(vectors: list[Vector], ncols: int) -> int:
    if not vectors:
        return 0
    return len(rref(vectors, ncols)[1])


def solve(rows: list[list[Fraction]], rhs: list[Fraction], ncols: int) -> Vector | None:
    """One solution of rows · v = rhs with free variables set to 0, or None."""
    aug = [list(r) + [b] for r, b in zip(rows, rhs)]
    reduced, pivots = rref(aug, ncols + 1)
    if ncols in pivots:
        return None
    v = [Fraction(0)] * ncols
    for row, pc in zip(reduced, pivots):
        v[pc] = row[ncols]
    return v


def integral(v: Vector) -> list[int]:
    """Smallest integer multiple of a rational vector, with a positive leading entry."""
    denom = 1
    for x in v:
        denom = lcm(denom, x.denominator)
    ints = [int(x * denom) for x in v]
    from math import gcd

    g = 0
    for x in ints:
        g = gcd(g, x)
    if g > 1:
        ints = [x // g for x in ints]
    lead = next((x for x in ints if x != 0), 0)
    if lead < 0:
        ints = [-x for x in ints]
    return ints


# ---- modular arithmetic (fast dimensions for large systems) ------------------

PRIME = 2_147_483_647  # 2^31 - 1


def rank_mod(rows: list[list[int]], ncols: int, p: int = PRIME) -> int:
    """Rank over GF(p). Equals the rational rank unless p divides a minor
    (vanishingly unlikely for small integer matrices; cross-checked in tests)."""
    m = [[x % p for x in r] for r in rows]
    rank = 0
    for c in range(ncols):
        pivot = next((i for i in range(rank, len(m)) if m[i][c]), None)
        if pivot is None:
            continue
        m[rank], m[pivot] = m[pivot], m[rank]
        inv = pow(m[rank][c], p - 2, p)
        prow = [(v * inv) % p for v in m[rank]]
        m[rank] = prow
        for i in range(len(m)):
            if i != rank and m[i][c]:
                f = m[i][c]
                row = m[i]
                m[i] = [(a - f * b) % p for a, b in zip(row, prow)]
        rank += 1
        if rank == len(m):
            break
    return rank

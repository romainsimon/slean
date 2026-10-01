"""One-dimensional cellular automata on cyclic lattices.

This module mirrors ``Slean/World/CellularAutomaton.lean`` exactly:

* output cell ``i`` reads input cells ``i, …, i+s`` (a centred rule followed
  by a shift, which leaves every total unchanged);
* patterns are coded big-endian in base ``k`` (Wolfram's neighbourhood order);
* a density of width ``w`` is a table indexed by that code.

Any disagreement between the two is a bug. ``tests/test_lean_agreement.py``
checks it.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from fractions import Fraction
from functools import cached_property

from .. import linalg


def code(k: int, pattern) -> int:
    c = 0
    for a in pattern:
        c = c * k + a
    return c


def patterns(k: int, length: int):
    return itertools.product(range(k), repeat=length)


@dataclass(frozen=True)
class CA:
    """A cellular automaton with ``k`` states and neighbourhood ``s + 1``."""

    k: int
    s: int
    table: tuple[int, ...]
    name: str = ""
    # Optional exact Lean term for the rule (for elementary automata).
    lean_term: str | None = field(default=None, compare=False)

    def __post_init__(self):
        if len(self.table) != self.k ** (self.s + 1):
            raise ValueError("table size must be k^(s+1)")
        if any(not 0 <= v < self.k for v in self.table):
            raise ValueError("table outputs must be states")

    @property
    def id(self) -> str:
        return self.name or f"ca-k{self.k}-s{self.s}-{code(self.k, self.table):x}"

    def loc(self, pattern) -> int:
        return self.table[code(self.k, pattern)]

    def step(self, cells: list[int]) -> list[int]:
        n = len(cells)
        k, s, t = self.k, self.s, self.table
        out = []
        for i in range(n):
            c = 0
            for j in range(s + 1):
                c = c * k + cells[(i + j) % n]
            out.append(t[c])
        return out

    def run(self, cells: list[int], steps: int) -> list[list[int]]:
        rows = [list(cells)]
        for _ in range(steps):
            rows.append(self.step(rows[-1]))
        return rows

    def lean(self) -> str:
        if self.lean_term:
            return self.lean_term
        if len(self.table) > 64:
            m = max(1, (self.k - 1).bit_length())
            return f"packedCA {self.k} {self.s} {m} {pack(self.table, m)}"
        return f"tableCA {self.k} {self.s} [{', '.join(map(str, self.table))}]"

    def describe(self) -> dict:
        return {"id": self.id, "k": self.k, "s": self.s, "table": list(self.table)}

    # ---- conservation laws -------------------------------------------------

    def step_window(self, pattern, w: int) -> tuple[int, ...]:
        """New cells ``0..w-1`` from a pattern of ``w + s`` current cells."""
        return tuple(self.loc(pattern[j : j + self.s + 1]) for j in range(w))

    def continuity_rows(self, w: int, f: list[int] | None = None):
        """Linear equations of the discrete continuity equation.

        Unknowns are ``f`` (``k^w`` entries, omitted when ``f`` is given) followed
        by a minimal current ``J`` on windows of ``w + s - 1`` cells. For each
        pattern ``p`` of ``w + s`` cells:
        ``f(step p) - f(p[:w]) - J(p[:-1]) + J(p[1:]) = 0``.
        """
        k, s = self.k, self.s
        nf = k**w
        v = w + s - 1
        nj = k**v
        rows, rhs = [], []
        for p in patterns(k, w + s):
            row_f = [Fraction(0)] * nf
            row_f[code(k, self.step_window(p, w))] += 1
            row_f[code(k, p[:w])] -= 1
            row_j = [Fraction(0)] * nj
            row_j[code(k, p[:v])] -= 1
            row_j[code(k, p[1 : v + 1])] += 1
            if f is None:
                rows.append(row_f + row_j)
            else:
                rows.append(row_j)
                rhs.append(-sum(c * f[i] for i, c in enumerate(row_f)))
        return rows, rhs, nf, nj

    def flux(self, f: list[int], w: int) -> list[int] | None:
        """An integer current proving ``f`` is conserved, or ``None``.

        The continuity equation reads ``J(p[1:]) = J(p[:-1]) - δ(p)`` along each
        edge of the de Bruijn graph on windows of ``w + s - 1`` cells. That graph
        is strongly connected, so fixing ``J`` at one window determines it
        everywhere; the density is conserved exactly when every edge agrees.
        """
        k, s = self.k, self.s
        v = w + s - 1
        if v == 0:
            ok = all(f[code(k, self.step_window(p, w))] == f[code(k, p[:w])] for p in patterns(k, w + s))
            return [0] if ok else None
        edges: dict[int, list[tuple[int, int]]] = {}
        for p in patterns(k, w + s):
            delta = f[code(k, self.step_window(p, w))] - f[code(k, p[:w])]
            edges.setdefault(code(k, p[:v]), []).append((code(k, p[1:]), delta))
        current: list[int | None] = [None] * (k**v)
        current[0] = 0
        stack = [0]
        while stack:
            a = stack.pop()
            for b, delta in edges.get(a, ()):
                value = current[a] - delta
                if current[b] is None:
                    current[b] = value
                    stack.append(b)
                elif current[b] != value:
                    return None
        if any(c is None for c in current):
            raise ArithmeticError("de Bruijn graph not connected")
        return current  # type: ignore[return-value]

    def lift_flux(self, flux: list[int], w: int) -> list[int]:
        """Current on ``w + s`` cells (the form the Lean theorem expects)."""
        k = self.k
        return [flux[c // k] for c in range(k ** (w + self.s))]


def pack(values, m: int) -> int:
    """Pack non-negative values into one natural number, ``m`` bits each (Lean's ``field``)."""
    total = 0
    for c, v in enumerate(values):
        if not 0 <= v < 2**m:
            raise ValueError("value does not fit its field")
        total |= v << (m * c)
    return total


def lean_fn(k: int, values) -> str:
    """Lean term for a density or current table: a list when small, packed when large."""
    values = list(values)
    if len(values) <= 64:
        return f"(tableFn {k} [{', '.join(map(str, values))}])"
    off = -min(0, min(values))
    m = max(1, (max(values) + off).bit_length())
    return f"(packedFn {k} {m} {off} {pack([v + off for v in values], m)})"


def eca(rule: int) -> CA:
    """Elementary cellular automaton with Wolfram number ``rule``."""
    table = tuple((rule >> c) & 1 for c in range(8))
    return CA(2, 2, table, name=f"eca-{rule}", lean_term=f"eca {rule}")


def reflect(ca: CA) -> CA:
    k, m = ca.k, ca.s + 1
    table = tuple(ca.loc(tuple(reversed(p))) for p in patterns(k, m))
    name = f"{ca.id}~reflect"
    if ca.lean_term and ca.k == 2 and ca.s == 2:
        return eca(sum(b << i for i, b in enumerate(table)))
    return CA(k, ca.s, table, name=name)


def relabel(ca: CA, perm: list[int]) -> CA:
    """Conjugate by a permutation of states: ``σ ∘ F ∘ σ⁻¹``."""
    k, m = ca.k, ca.s + 1
    inv = [0] * k
    for a, b in enumerate(perm):
        inv[b] = a
    table = tuple(perm[ca.loc(tuple(inv[a] for a in p))] for p in patterns(k, m))
    if ca.lean_term and ca.k == 2 and ca.s == 2:
        return eca(sum(b << i for i, b in enumerate(table)))
    return CA(k, ca.s, table, name=f"{ca.id}~relabel{''.join(map(str, perm))}")


def random_conserving(k: int, rng: random.Random, name: str) -> tuple[CA, list[int]]:
    """A radius-1 automaton with a *planted* conservation law.

    Each cell holds a number of particles in ``0..k-1``. ``phi(a, b)`` particles
    hop from a cell holding ``a`` to its right neighbour holding ``b``, with
    ``0 <= phi(a, b) <= min(a, k-1-b)``, so the particle count is exactly
    conserved. The states are then relabelled by a hidden random permutation,
    so the law is not visible in the labels. Returns the automaton and the
    hidden density (indexed by the visible state).
    """
    phi = {}
    for a in range(k):
        for b in range(k):
            phi[a, b] = rng.randint(0, min(a, k - 1 - b))
    base = []
    for a, b, c in patterns(k, 3):
        base.append(b - phi[b, c] + phi[a, b])
    perm = list(range(k))
    rng.shuffle(perm)
    inv = [0] * k
    for a, b in enumerate(perm):
        inv[b] = a
    table = tuple(perm[base[code(k, tuple(inv[x] for x in p))]] for p in patterns(k, 3))
    hidden_density = [inv[state] for state in range(k)]
    return CA(k, 2, table, name=name), hidden_density


def random_rule(k: int, rng: random.Random, name: str) -> CA:
    """A uniformly random radius-1 automaton (usually without any law)."""
    return CA(k, 2, tuple(rng.randrange(k) for _ in range(k**3)), name=name)


class ConservationTruth:
    """Exact space of conserved densities of width ``w`` (the hidden answer).

    By the Hattori–Takesue characterisation, a density is conserved for every
    lattice size exactly when a local current exists, so the null space of the
    continuity equations is the complete answer. ``tests`` cross-check it
    against brute force on small lattices.
    """

    def __init__(self, ca: CA, w: int):
        self.ca, self.w = ca, w
        self.dim_f = ca.k**w

    @cached_property
    def conserved(self) -> list[linalg.Vector]:
        rows, _, nf, nj = self.ca.continuity_rows(self.w)
        basis = linalg.nullspace(rows, nf + nj)
        fs = [v[:nf] for v in basis]
        reduced, _ = linalg.rref(fs, nf) if fs else ([], [])
        return reduced

    @cached_property
    def trivial(self) -> list[linalg.Vector]:
        return trivial_densities(self.ca.k, self.w)

    @cached_property
    def trivial_rank(self) -> int:
        return linalg.rank(self.trivial, self.dim_f)

    @cached_property
    def nontrivial_dim(self) -> int:
        nf = self.dim_f
        nj = self.ca.k ** (self.w + self.ca.s - 1)
        if nf + nj <= 120:
            return linalg.rank(self.conserved + self.trivial, nf) - self.trivial_rank
        # Large systems: dimensions by modular rank.
        # conserved f-space dim = dim{(f, J)} - dim{(0, J) : J constant} = (n - rank) - 1
        rows, _, _, _ = self.ca.continuity_rows(self.w)
        int_rows = [[int(x) for x in r] for r in rows]
        conserved_dim = (nf + nj - linalg.rank_mod(int_rows, nf + nj)) - 1
        # every trivial density is conserved, so the quotient is a plain difference
        return conserved_dim - self.trivial_rank


def trivial_densities(k: int, w: int) -> list[linalg.Vector]:
    """Constants and discrete gradients ``g(x_i..) - g(x_{i+1}..)``.

    Their totals never change for *any* rule, so they are not discoveries.
    """
    n = k**w
    vecs = [[Fraction(1)] * n]
    if w >= 2:
        for q in range(k ** (w - 1)):
            v = [Fraction(0)] * n
            for p in patterns(k, w):
                if code(k, p[:-1]) == q:
                    v[code(k, p)] += 1
                if code(k, p[1:]) == q:
                    v[code(k, p)] -= 1
            vecs.append(v)
    return vecs


def embed(f: list[int], k: int, w_from: int, w_to: int) -> list[Fraction]:
    """View a width-``w_from`` density as a width-``w_to`` one."""
    out = []
    for p in patterns(k, w_to):
        out.append(Fraction(f[code(k, p[:w_from])]))
    return out


def total(f: list[int], w: int, k: int, cells: list[int]) -> int:
    n = len(cells)
    return sum(f[code(k, [cells[(i + j) % n] for j in range(w)])] for i in range(n))


# ---- compressible worlds: large rule tables generated by a short hidden law ----

def _relabelled(k: int, s: int, out_of, rng: random.Random, disguise: bool) -> tuple[int, ...]:
    """Table of ``out_of(cells)`` over all neighbourhoods, optionally seen through
    a secret relabelling of states (the law is stated on hidden values)."""
    perm = list(range(k))
    if disguise:
        rng.shuffle(perm)
    inv = [0] * k
    for a, b in enumerate(perm):
        inv[b] = a
    return tuple(perm[out_of([inv[a] for a in p])] for p in patterns(k, s + 1))


def compressible_world(family: str, k: int, s: int, rng: random.Random, name: str, disguise: bool) -> CA:
    """A rule over ``k^(s+1)`` neighbourhoods produced by a law with few parameters.

    Families: ``totalistic`` (output depends on the sum of the cells),
    ``outer`` (on the centre cell and the sum of the others), ``linear``
    (a weighted sum modulo k), ``particles`` (particles hop between neighbours,
    so their number is conserved) and ``random`` (no short law: a distractor).
    """
    centre = s // 2
    if family == "totalistic":
        g = [rng.randrange(k) for _ in range((k - 1) * (s + 1) + 1)]
        out = lambda c: g[sum(c)]
    elif family == "outer":
        g = [[rng.randrange(k) for _ in range((k - 1) * s + 1)] for _ in range(k)]
        out = lambda c: g[c[centre]][sum(c) - c[centre]]
    elif family == "linear":
        a = [rng.randrange(k) for _ in range(s + 1)]
        while sum(1 for x in a if x) < 2:
            a = [rng.randrange(k) for _ in range(s + 1)]
        b = rng.randrange(k)
        out = lambda c: (sum(x * y for x, y in zip(a, c)) + b) % k
    elif family == "particles":
        # phi(x_j, x_{j+1}, x_{j+2}): particles moving from cell j to j+1, at most
        # what j holds and what j+1 can receive. Cell centre gains from the left
        # boundary and loses to the right one: depends on cells centre-1 .. centre+2.
        phi = {}
        for a in range(k):
            for b in range(k):
                for c in range(k):
                    phi[a, b, c] = rng.randint(0, min(a, k - 1 - b))
        def out(cells):
            m = centre
            left = phi[cells[m - 1], cells[m], cells[m + 1]]
            right = phi[cells[m], cells[m + 1], cells[m + 2]]
            return cells[m] - right + left
    elif family == "random":
        table = tuple(rng.randrange(k) for _ in range(k ** (s + 1)))
        return CA(k, s, table, name=name)
    else:
        raise ValueError(family)
    return CA(k, s, _relabelled(k, s, out, rng, disguise), name=name)

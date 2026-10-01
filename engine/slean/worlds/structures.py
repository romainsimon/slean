"""Localised travelling structures (gliders, oscillators) in cellular automata.

Mirrors ``Slean/World/Structures.lean``. A structure is a block of cells on a
quiescent background ``q`` (a state with ``loc(q, …, q) = q``). Padded with
``q`` on both sides, it reappears after ``t`` steps translated by ``d`` cells.

In the Slean convention output cell ``i`` reads cells ``i … i+s``, so influence
only travels left, at most ``s`` cells per step. With at least ``s·t`` cells of
padding on the left, nothing wraps around the cyclic lattice within ``t``
steps, and the cyclic statement is equivalent to the same statement on the
infinite line. Velocities are reported in the usual centred frame:
``v = -d/t + s/2`` (positive means moving right).

A *species* is the orbit of a structure up to translation and phase: its
minimal period, its velocity and its smallest trimmed shape over the phases.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from fractions import Fraction

from .ca import CA


def quiescent_states(ca: CA) -> list[int]:
    return [q for q in range(ca.k) if ca.loc((q,) * (ca.s + 1)) == q]


def trim(cells, q: int) -> tuple[int, ...]:
    lo, hi = 0, len(cells)
    while lo < hi and cells[lo] == q:
        lo += 1
    while hi > lo and cells[hi - 1] == q:
        hi -= 1
    return tuple(cells[lo:hi])


def padded(block, q: int, s: int, t: int) -> list[int]:
    pad = s * t + 1
    return [q] * pad + list(block) + [q] * pad


@dataclass(frozen=True)
class Species:
    world: str
    q: int
    period: int
    velocity: Fraction
    shape: tuple[int, ...]

    @property
    def key(self) -> tuple:
        return (self.world, self.q, self.period, self.velocity, self.shape)

    def to_json(self) -> dict:
        return {
            "world": self.world,
            "background": self.q,
            "period": self.period,
            "velocity": str(self.velocity),
            "shape": list(self.shape),
        }


class Meter:
    """Counts cell updates: the cost of experimenting with a world."""

    def __init__(self):
        self.cell_updates = 0

    def step(self, ca: CA, row: list[int]) -> list[int]:
        self.cell_updates += len(row)
        return ca.step(row)


def _shift(row, lattice) -> int | None:
    n = len(lattice)
    for d in range(n):
        if all(row[i] == lattice[(i + d) % n] for i in range(n)):
            return d
    return None


def first_return(ca: CA, block, q: int, t_max: int, meter: Meter | None = None):
    """``(t, d)`` of the first return of ``block`` within ``t_max`` steps, else ``None``."""
    lattice = padded(block, q, ca.s, t_max)
    row = lattice
    for t in range(1, t_max + 1):
        row = meter.step(ca, row) if meter else ca.step(row)
        if all(c == q for c in row):
            return None
        d = _shift(row, lattice)
        if d is not None:
            return t, d
    return None


def check(ca: CA, block, q: int, t: int, d: int) -> bool:
    """Exactly what the Lean kernel checks: ``Travels A (padded block) t d``."""
    if t < 1 or q not in quiescent_states(ca) or not block or all(c == q for c in block):
        return False
    lattice = padded(block, q, ca.s, t)
    row = lattice
    for _ in range(t):
        row = ca.step(row)
    n = len(lattice)
    return all(row[i] == lattice[(i + d) % n] for i in range(n))


def species(ca: CA, block, q: int, t: int) -> Species | None:
    """Species of a structure returning after ``t`` steps (``t`` need not be minimal)."""
    res = first_return(ca, block, q, t)
    if res is None:
        return None
    t0, d0 = res
    lattice = padded(block, q, ca.s, t)
    n = len(lattice)
    shift = d0 if d0 <= n // 2 else d0 - n
    shapes, row = [], lattice
    for _ in range(t0):
        shapes.append(trim(row, q))
        row = ca.step(row)
    velocity = Fraction(-shift, t0) + Fraction(ca.s, 2)
    return Species(ca.id, q, t0, velocity, min(shapes))


def blocks(k: int, q: int, max_width: int):
    """Blocks whose first and last cells differ from the background."""
    others = [a for a in range(k) if a != q]
    for width in range(1, max_width + 1):
        if width == 1:
            for a in others:
                yield (a,)
            continue
        for first in others:
            for last in others:
                for middle in itertools.product(range(k), repeat=width - 2):
                    yield (first, *middle, last)


def enumerate_species(ca: CA, max_width: int, max_period: int, meter: Meter | None = None) -> dict:
    """Brute force: every species of shape width ``<= max_width`` and period ``<= max_period``.

    Used both as an explorer baseline (metered) and as the hidden answer.
    """
    found: dict[tuple, Species] = {}
    for q in quiescent_states(ca):
        for block in blocks(ca.k, q, max_width):
            res = first_return(ca, block, q, max_period, meter)
            if res is None:
                continue
            sp = species(ca, block, q, res[0])
            if sp is not None and len(sp.shape) <= max_width:
                found.setdefault(sp.key, sp)
    return found

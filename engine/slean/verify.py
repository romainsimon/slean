"""Verification of proposed claims.

A claim is only ever *certified* by a finite certificate that the Lean kernel
re-checks (see ``lean.py``). The Python side finds the certificate; it never
upgrades a claim on its own authority.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import asdict, dataclass, field

from . import linalg
from .worlds.ca import CA, embed, trivial_densities

MAX_WIDTH = 3


@dataclass(frozen=True)
class Claim:
    """"The total of density ``f`` (width ``w``) is conserved by ``world``"."""

    world: str
    w: int
    f: tuple[int, ...]
    kind: str = "conservation"

    def to_json(self) -> dict:
        return {"kind": self.kind, "world": self.world, "w": self.w, "f": list(self.f)}


@dataclass(frozen=True)
class Travel:
    """"``block`` on background ``q`` reappears after ``t`` steps, shifted by ``d``"."""

    world: str
    q: int
    block: tuple[int, ...]
    t: int
    d: int
    kind: str = "structure"

    def to_json(self) -> dict:
        return {
            "kind": self.kind,
            "world": self.world,
            "background": self.q,
            "block": list(self.block),
            "t": self.t,
            "d": self.d,
        }


@dataclass(frozen=True)
class Mechanism:
    """"``table`` is exactly the rule of ``world``" (the whole law, identified)."""

    world: str
    table: tuple[int, ...]
    kind: str = "mechanism"

    def to_json(self) -> dict:
        return {"kind": self.kind, "world": self.world, "table": list(self.table)}


@dataclass
class Verdict:
    # certified: conserved, with a current (flux) certificate
    # refuted:   a concrete configuration where the total changes
    # trivial:   conserved by every rule (constant or discrete gradient)
    # invalid:   malformed claim
    status: str
    flux: list[int] | None = None
    witness: list[int] | None = None
    reason: str = ""
    checks: int = 0
    extra: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in (None, "", {})}


def _changes(ca: CA, f, w: int, cells: list[int]) -> bool:
    from .worlds.ca import total

    return total(f, w, ca.k, ca.step(cells)) != total(f, w, ca.k, cells)


def find_witness(ca: CA, f, w: int, rng: random.Random, max_exhaustive: int = 7, samples: int = 64):
    """A small configuration whose total changes, or ``None``."""
    checks = 0
    for n in range(1, 13):
        for _ in range(samples // 12 + 1):
            cells = [rng.randrange(ca.k) for _ in range(n)]
            checks += 1
            if _changes(ca, f, w, cells):
                return shrink(ca, f, w, cells), checks
    for n in range(1, max_exhaustive + 1):
        if ca.k**n > 50_000:
            break
        for cells in itertools.product(range(ca.k), repeat=n):
            checks += 1
            if _changes(ca, f, w, list(cells)):
                return list(cells), checks
    return None, checks


def shrink(ca: CA, f, w: int, cells: list[int]) -> list[int]:
    """Shortest counterexample among the first few sizes (for small proofs)."""
    for n in range(1, len(cells)):
        if ca.k**n > 5_000:
            break
        for cand in itertools.product(range(ca.k), repeat=n):
            if _changes(ca, f, w, list(cand)):
                return list(cand)
    return cells


def is_trivial(k: int, w: int, f) -> bool:
    n = k**w
    t = trivial_densities(k, w)
    return linalg.rank(t + [embed(list(f), k, w, w)], n) == linalg.rank(t, n)


MAX_BLOCK, MAX_PERIOD = 24, 24


def verify_travel(ca: CA, claim: Travel) -> Verdict:
    from .worlds import structures

    if not (1 <= claim.t <= MAX_PERIOD and 1 <= len(claim.block) <= MAX_BLOCK):
        return Verdict("invalid", reason=f"need 1 <= t <= {MAX_PERIOD} and 1..{MAX_BLOCK} cells")
    if not 0 <= claim.q < ca.k or any(not 0 <= a < ca.k for a in claim.block):
        return Verdict("invalid", reason="states out of range")
    if claim.q not in structures.quiescent_states(ca):
        return Verdict("invalid", reason="background state is not quiescent")
    if all(a == claim.q for a in claim.block):
        return Verdict("trivial", reason="empty pattern")
    if not structures.check(ca, claim.block, claim.q, claim.t, claim.d):
        return Verdict("refuted", reason="pattern does not reappear with that shift")
    sp = structures.species(ca, claim.block, claim.q, claim.t)
    return Verdict(
        "certified",
        extra={"period": sp.period, "velocity": str(sp.velocity), "shape": list(sp.shape)},
    )


def verify_mechanism(ca: CA, claim: Mechanism) -> Verdict:
    from .worlds.ca import patterns

    if len(claim.table) != len(ca.table) or any(not 0 <= v < ca.k for v in claim.table):
        return Verdict("invalid", reason=f"a rule needs {len(ca.table)} entries in 0..{ca.k - 1}")
    for p, (mine, true) in zip(patterns(ca.k, ca.s + 1), zip(claim.table, ca.table)):
        if mine != true:
            # The counterexample is one neighbourhood and what the world really does there.
            return Verdict("refuted", reason="differs on at least one neighbourhood",
                           extra={"neighbourhood": list(p), "claimed": mine, "observed": true})
    return Verdict("certified", reason="identical rule on every neighbourhood")


def verify(ca: CA, claim, rng: random.Random | None = None) -> Verdict:
    rng = rng or random.Random(0)
    if isinstance(claim, Mechanism):
        return verify_mechanism(ca, claim)
    if isinstance(claim, Travel):
        return verify_travel(ca, claim)
    if claim.kind != "conservation":
        return Verdict("invalid", reason=f"unsupported claim kind {claim.kind!r}")
    if not 1 <= claim.w <= MAX_WIDTH:
        return Verdict("invalid", reason=f"width must be 1..{MAX_WIDTH}")
    if len(claim.f) != ca.k**claim.w or any(not isinstance(v, int) for v in claim.f):
        return Verdict("invalid", reason=f"density needs {ca.k ** claim.w} integer entries")
    if is_trivial(ca.k, claim.w, claim.f):
        return Verdict("trivial", reason="constant or discrete gradient: conserved by every rule")
    witness, checks = find_witness(ca, claim.f, claim.w, rng)
    if witness is not None:
        return Verdict("refuted", witness=witness, checks=checks)
    flux = ca.flux(list(claim.f), claim.w)
    if flux is not None:
        return Verdict("certified", flux=flux, checks=checks)
    # By Hattori–Takesue a counterexample must exist; search harder.
    witness, more = find_witness(ca, claim.f, claim.w, rng, max_exhaustive=12, samples=2000)
    if witness is not None:
        return Verdict("refuted", witness=witness, checks=checks + more)
    return Verdict("invalid", reason="no current and no counterexample found", checks=checks + more)

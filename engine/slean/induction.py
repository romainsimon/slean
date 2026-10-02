"""Inferring a compact law from a few observed neighbourhoods.

Used by the scripted reference scientist. It tests textbook cellular-automaton
families, each up to a relabelling of the states:

- ``linear``: ``p((sum_j a_j r(c_j)) mod k)``, an additive rule;
- ``totalistic``: ``h(sum_j r(c_j))``, the output depends on the sum;
- ``outer``: ``g(r(c_centre), sum_{j != centre} r(c_j))``, outer totalistic.

``r`` recodes the states and ``p``, ``h``, ``g`` are tables read from the data.
A hypothesis survives when the observations never give two outputs for the
same index. Unobserved table entries are reported so that the caller can spend
experiments on exactly those, and the finished law goes to the verifier, which
checks it on every neighbourhood.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations, product
from typing import Callable

from .worlds.ca import patterns

Pattern = tuple[int, ...]


@dataclass
class Hypothesis:
    family: str
    size: int  # number of table entries
    index: Callable[[Pattern], int]
    build: Callable[[list[int]], dict]
    table: dict[int, int] = field(default_factory=dict)
    reachable: list[int] | None = None  # indices some neighbourhood can produce (default: all)

    def missing(self) -> list[int]:
        return [i for i in (self.reachable if self.reachable is not None else range(self.size))
                if i not in self.table]

    def law(self) -> dict:
        return self.build([self.table.get(i, 0) for i in range(self.size)])


def _cell(j: int, r: tuple[int, ...]) -> dict:
    cell = {"op": "cell", "j": j}
    if r == tuple(range(len(r))):
        return cell
    return {"op": "lookup", "table": list(r), "a": cell}


def _sum(args: list[dict]) -> dict:
    return args[0] if len(args) == 1 else {"op": "sum", "args": args}


def _consistent(h: Hypothesis, obs: dict[Pattern, int]) -> bool:
    table: dict[int, int] = {}
    for p, out in obs.items():
        i = h.index(p)
        if table.setdefault(i, out) != out:
            return False
    h.table = table
    return True


def _linear(k: int, s: int, obs: dict[Pattern, int], r: tuple[int, ...]):
    items = [(tuple(r[c] for c in p), out) for p, out in obs.items()]
    for a in product(range(k), repeat=s + 1):
        if sum(1 for x in a if x) < 1:
            continue
        seen: dict[int, int] = {}
        back: dict[int, int] = {}
        ok = True
        for q, out in items:
            v = sum(x * y for x, y in zip(a, q)) % k
            if seen.setdefault(v, out) != out or back.setdefault(out, v) != v:
                ok = False
                break
        if not ok:
            continue

        def index(p, a=a):
            return sum(x * r[c] for x, c in zip(a, p)) % k

        def build(table, a=a):
            terms = [_cell(j, r) if x == 1 else {"op": "mul", "a": {"op": "const", "c": x}, "b": _cell(j, r)}
                     for j, x in enumerate(a) if x]
            body = {"op": "mod", "a": _sum(terms), "m": k}
            if table == list(range(k)):
                return body
            return {"op": "lookup", "table": table, "a": body}

        yield Hypothesis("linear", k, index, build, table=seen,
                         reachable=sorted({index(p) for p in patterns(k, s + 1)}))


def _totalistic(k: int, s: int, r: tuple[int, ...]) -> Hypothesis:
    def index(p):
        return sum(r[c] for c in p)

    def build(table):
        return {"op": "lookup", "table": table, "a": _sum([_cell(j, r) for j in range(s + 1)])}

    return Hypothesis("totalistic", (k - 1) * (s + 1) + 1, index, build)


def _outer(k: int, s: int, r: tuple[int, ...]) -> Hypothesis:
    centre, m = s // 2, (k - 1) * s + 1

    def index(p):
        return r[p[centre]] * m + sum(r[c] for j, c in enumerate(p) if j != centre)

    def build(table):
        rest = _sum([_cell(j, r) for j in range(s + 1) if j != centre])
        scaled = {"op": "mul", "a": {"op": "const", "c": m}, "b": _cell(centre, r)}
        return {"op": "lookup", "table": table, "a": {"op": "add", "a": scaled, "b": rest}}

    return Hypothesis("outer", k * m, index, build)


def recodings(k: int) -> list[tuple[int, ...]]:
    """Every relabelling of the states, the identity first."""
    return list(permutations(range(k)))


def candidates(k: int, s: int, obs: dict[Pattern, int]):
    """Hypotheses consistent with the observations, shortest families first.

    Lazy: a caller that takes the first and has it confirmed never pays for the rest.
    """
    for r in recodings(k):
        yield from _linear(k, s, obs, r)
    for make in (_totalistic, _outer):
        for r in recodings(k):
            h = make(k, s, r)
            if _consistent(h, obs):
                yield h


def witness(h: Hypothesis, k: int, s: int, i: int) -> Pattern:
    """A neighbourhood whose index under ``h`` is ``i``."""
    return next(p for p in patterns(k, s + 1) if h.index(p) == i)

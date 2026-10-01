"""Explorers propose claims; the verifier decides.

Every explorer sees the same things: the world definitions (rule tables), the
ability to simulate them, the library of past verdicts, and the remaining
budget. None of them sees the hidden ground truth, except ``Oracle``, which is
an upper bound that knows the theory.

One proposal costs one unit of budget, whoever makes it.
"""

from __future__ import annotations

import itertools
import json
import random
import subprocess
from fractions import Fraction

from . import linalg
from .library import Library
from .verify import Claim, Verdict
from .worlds.ca import CA, ConservationTruth, code, patterns, reflect, relabel


class Explorer:
    name = "explorer"
    uses_library = False

    def __init__(self, seed: int = 0, max_width: int = 2):
        self.rng = random.Random(seed)
        self.max_width = max_width

    def propose(self, worlds: list[CA], library: Library) -> Claim | None:
        raise NotImplementedError

    def observe(self, claim: Claim, verdict: Verdict, novel: bool) -> None:
        pass

    def cost(self) -> dict:
        return {}


class RandomExplorer(Explorer):
    """The floor: random small-integer densities on random worlds."""

    name = "random"

    def propose(self, worlds, library):
        for _ in range(100):
            ca = self.rng.choice(worlds)
            w = self.rng.randint(1, self.max_width)
            f = tuple(self.rng.choice((-1, 0, 0, 1)) for _ in range(ca.k**w))
            claim = Claim(ca.id, w, f)
            if not library.seen(claim):
                return claim
        return None


class DataFitExplorer(Explorer):
    """A computational scientist without the theory.

    Simulates random configurations, then solves for densities whose total
    did not change on any observed transition (exact linear algebra on data,
    in the spirit of sparse regression / SINDy). Proposes what the data allow.
    """

    name = "datafit"

    def __init__(self, seed=0, max_width=2, samples=40):
        super().__init__(seed, max_width)
        self.samples = samples
        self.queue: list[Claim] = []
        self.done: set[str] = set()

    def _candidates(self, ca: CA) -> list[Claim]:
        out = []
        for w in range(1, self.max_width + 1):
            nf = ca.k**w
            rows = []
            for _ in range(self.samples):
                n = self.rng.randint(1, 10)
                cells = [self.rng.randrange(ca.k) for _ in range(n)]
                after = ca.step(cells)
                row = [Fraction(0)] * nf
                for i in range(n):
                    row[code(ca.k, [after[(i + j) % n] for j in range(w)])] += 1
                    row[code(ca.k, [cells[(i + j) % n] for j in range(w)])] -= 1
                rows.append(row)
            for vec in linalg.nullspace(linalg.rref(rows, nf)[0], nf):
                out.append(Claim(ca.id, w, tuple(linalg.integral(vec))))
        return out

    def propose(self, worlds, library):
        while not self.queue:
            todo = [ca for ca in worlds if ca.id not in self.done]
            if not todo:
                return None
            ca = todo[0]
            self.done.add(ca.id)
            self.queue = [c for c in self._candidates(ca) if not library.seen(c)]
        while self.queue:
            claim = self.queue.pop(0)
            # Thinking is free; only verified proposals cost budget.
            if library.is_novel(claim):
                return claim
        return self.propose(worlds, library)


class LibraryExplorer(Explorer):
    """Data fitting plus reuse of the library.

    Before experimenting on a world, it looks for a structural relation with a
    world already in the library: the same rule up to a relabelling of states
    and a reflection (pure reasoning on the rule tables, free). When it finds
    one, it transports every law known there. Otherwise it falls back to data
    fitting. With an empty library it *is* the data-fitting explorer, so the
    cold/warm comparison isolates the value of accumulated results.
    """

    name = "library"
    uses_library = True

    def __init__(self, seed=0, max_width=2):
        super().__init__(seed, max_width)
        self.fallback = DataFitExplorer(seed, max_width)
        self.queue: list[Claim] = []
        self.done: set[str] = set()
        self.relations: list[dict] = []

    @staticmethod
    def relation(source: CA, target: CA):
        """``(perm, flip)`` with ``target = σ ∘ F' ∘ σ⁻¹`` (``F'`` = maybe reflected)."""
        if (source.k, source.s) != (target.k, target.s):
            return None
        for flip in (False, True):
            base = reflect(source) if flip else source
            for perm in itertools.permutations(range(source.k)):
                if relabel(base, list(perm)).table == target.table:
                    return list(perm), flip
        return None

    @staticmethod
    def transport(k: int, w: int, f, perm, flip) -> tuple[int, ...]:
        inv = [0] * k
        for a, b in enumerate(perm):
            inv[b] = a
        out = []
        for p in patterns(k, w):
            q = tuple(inv[a] for a in p)
            if flip:
                q = tuple(reversed(q))
            out.append(f[code(k, q)])
        return tuple(out)

    def _plan(self, ca: CA, library: Library) -> list[Claim]:
        for world_id, source in library.worlds.items():
            if world_id == ca.id or not library.certified(world_id):
                continue
            rel = self.relation(source, ca)
            if rel is None:
                continue
            perm, flip = rel
            self.relations.append({"from": world_id, "to": ca.id, "perm": perm, "reflect": flip})
            return [
                Claim(ca.id, b.claim.w, self.transport(ca.k, b.claim.w, b.claim.f, perm, flip))
                for b in library.certified(world_id)
                if b.novel
            ]
        return []

    def propose(self, worlds, library):
        while True:
            while self.queue:
                claim = self.queue.pop(0)
                if not library.seen(claim) and library.is_novel(claim):
                    return claim
            todo = [ca for ca in worlds if ca.id not in self.done]
            if not todo:
                return None
            ca = todo[0]
            self.done.add(ca.id)
            self.queue = self._plan(ca, library)
            if not self.queue:
                self.fallback.done.discard(ca.id)
                self.queue = [c for c in self.fallback._candidates(ca)]

    def cost(self):
        return {"relations_found": len(self.relations)}


class OracleExplorer(Explorer):
    """Upper bound: solves the continuity equations directly (knows the theory)."""

    name = "oracle"

    def __init__(self, seed=0, max_width=2):
        super().__init__(seed, max_width)
        self.queue: list[Claim] = []
        self.done: set[str] = set()

    def propose(self, worlds, library):
        while not self.queue:
            todo = [ca for ca in worlds if ca.id not in self.done]
            if not todo:
                return None
            ca = todo[0]
            self.done.add(ca.id)
            for w in range(1, self.max_width + 1):
                for vec in ConservationTruth(ca, w).conserved:
                    claim = Claim(ca.id, w, tuple(linalg.integral(vec)))
                    if not library.seen(claim):
                        self.queue.append(claim)
        while self.queue:
            claim = self.queue.pop(0)
            if library.is_novel(claim):
                return claim
        return self.propose(worlds, library)


PROMPT = """You are exploring unknown one-dimensional cellular automata on cyclic lattices.
Your goal is to discover conservation laws: densities whose total never changes.

Definitions (exact):
- A world has k states (0..k-1). Output cell i is table[code(x_i, x_(i+1), x_(i+2))],
  where code is the big-endian base-k number of the three cells (indices mod n).
- A density of width w is a list f of k^w integers indexed by the big-endian
  base-k code of w consecutive cells. Its total is sum over i of f(x_i..x_(i+w-1)).
- A claim is conserved if the total is identical before and after one step,
  for every lattice size and every configuration.
- Constants and discrete gradients g(x_i..)-g(x_(i+1)..) are trivial and do
  not count. Only claims that add something new to a world count.

Worlds:
{worlds}

Library (results already verified, including refutations):
{library}

Your recent proposals and verdicts:
{feedback}

Propose up to {batch} new claims, preferring worlds with no known law yet.
Answer with JSON only, no prose:
{{"claims": [{{"world": "<id>", "w": 1, "f": [..k^w integers..], "why": "<short reason>"}}]}}
"""


class LLMExplorer(Explorer):
    """A language model proposes claims from the world definitions and feedback.

    It is called through a shell command that reads the prompt on stdin and
    prints the answer (by default the Claude Code CLI in print mode). Token
    usage reported by the command is recorded.
    """

    name = "llm"
    uses_library = True

    def __init__(self, seed=0, max_width=2, command=None, batch=8, sample_rows=6):
        super().__init__(seed, max_width)
        self.command = command or ["claude", "-p", "--output-format", "json"]
        self.batch = batch
        self.sample_rows = sample_rows
        self.queue: list[Claim] = []
        self.feedback: list[str] = []
        self.calls = 0
        self.usage = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        self.errors: list[str] = []

    def _world_text(self, ca: CA) -> str:
        rng = random.Random(ca.id)
        cells = [rng.randrange(ca.k) for _ in range(16)]
        rows = ca.run(cells, self.sample_rows)
        traj = "\n".join("    " + "".join(map(str, r)) for r in rows)
        return f"- id={ca.id} k={ca.k} table={list(ca.table)}\n  sample run:\n{traj}"

    def _library_text(self, library: Library) -> str:
        lines = []
        for b in library.bricks[-60:]:
            c = b.claim
            tag = b.verdict.status + (" NEW" if b.novel else "")
            lines.append(f"- {c.world} w={c.w} f={list(c.f)} -> {tag}")
        return "\n".join(lines) or "(empty)"

    def _call(self, prompt: str) -> str:
        self.calls += 1
        proc = subprocess.run(self.command, input=prompt, capture_output=True, text=True, timeout=600)
        out = proc.stdout
        try:
            envelope = json.loads(out)
            if isinstance(envelope, dict) and "result" in envelope:
                usage = envelope.get("usage", {})
                self.usage["input_tokens"] += usage.get("input_tokens", 0) + usage.get(
                    "cache_read_input_tokens", 0
                ) + usage.get("cache_creation_input_tokens", 0)
                self.usage["output_tokens"] += usage.get("output_tokens", 0)
                self.usage["cost_usd"] += envelope.get("total_cost_usd", 0.0) or 0.0
                return envelope["result"]
        except json.JSONDecodeError:
            pass
        return out

    def _parse(self, text: str, worlds: dict[str, CA]) -> list[Claim]:
        start, end = text.find("{"), text.rfind("}")
        if start < 0:
            self.errors.append("no json")
            return []
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            self.errors.append(f"bad json: {exc}")
            return []
        claims = []
        for item in data.get("claims", []):
            try:
                world = str(item["world"])
                w = int(item["w"])
                f = tuple(int(v) for v in item["f"])
            except (KeyError, TypeError, ValueError):
                continue
            if world in worlds:
                claims.append(Claim(world, w, f))
        return claims

    def propose(self, worlds, library):
        tries = 0
        while not self.queue and tries < 3:
            tries += 1
            by_id = {ca.id: ca for ca in worlds}
            open_worlds = sorted(worlds, key=lambda ca: library.discovered_dim(ca.id))[:12]
            prompt = PROMPT.format(
                worlds="\n".join(self._world_text(ca) for ca in open_worlds),
                library=self._library_text(library),
                feedback="\n".join(self.feedback[-20:]) or "(none yet)",
                batch=self.batch,
            )
            self.queue = [c for c in self._parse(self._call(prompt), by_id) if not library.seen(c)]
        return self.queue.pop(0) if self.queue else None

    def observe(self, claim, verdict, novel):
        detail = verdict.witness if verdict.status == "refuted" else ""
        self.feedback.append(
            f"- {claim.world} w={claim.w} f={list(claim.f)} -> {verdict.status}"
            f"{' NEW' if novel else ''}{f' counterexample={detail}' if detail else ''}"
        )

    def cost(self):
        return {"llm_calls": self.calls, **self.usage, "parse_errors": len(self.errors)}


EXPLORERS = {
    "random": RandomExplorer,
    "datafit": DataFitExplorer,
    "library": LibraryExplorer,
    "oracle": OracleExplorer,
    "llm": LLMExplorer,
}

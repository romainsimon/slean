"""The library: every verified result and every refutation, kept for reuse.

A brick is a claim plus the certificate that settles it. Certified bricks are
the reusable pieces; refuted ones are kept as negative knowledge. Exporting
the library produces a Lean module the kernel re-checks from scratch.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

from . import lean, linalg
from .verify import Claim, Verdict
from .worlds.ca import CA, embed, trivial_densities


@dataclass
class Brick:
    id: str
    claim: Claim
    verdict: Verdict
    novel: bool
    provenance: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "claim": self.claim.to_json(),
            "verdict": self.verdict.to_json(),
            "novel": self.novel,
            "provenance": self.provenance,
        }


class Library:
    def __init__(self, max_width: int = 2):
        self.max_width = max_width
        self.worlds: dict[str, CA] = {}
        self.bricks: list[Brick] = []
        self._spans: dict[str, list[list[Fraction]]] = {}
        self._seen: set[tuple] = set()

    # ---- recording ---------------------------------------------------------

    def add_world(self, ca: CA) -> None:
        self.worlds.setdefault(ca.id, ca)

    def _span(self, world: str) -> list[list[Fraction]]:
        if world not in self._spans:
            ca = self.worlds[world]
            self._spans[world] = list(trivial_densities(ca.k, self.max_width))
        return self._spans[world]

    def is_novel(self, claim: Claim) -> bool:
        ca = self.worlds[claim.world]
        span = self._span(claim.world)
        v = embed(list(claim.f), ca.k, claim.w, self.max_width)
        n = ca.k**self.max_width
        return linalg.rank(span + [v], n) > linalg.rank(span, n)

    def record(self, claim: Claim, verdict: Verdict, provenance: dict) -> Brick:
        novel = verdict.status == "certified" and self.is_novel(claim)
        if novel:
            ca = self.worlds[claim.world]
            self._span(claim.world).append(embed(list(claim.f), ca.k, claim.w, self.max_width))
        brick = Brick(f"b{len(self.bricks):05d}", claim, verdict, novel, provenance)
        self.bricks.append(brick)
        self._seen.add((claim.world, claim.w, claim.f))
        return brick

    def seen(self, claim: Claim) -> bool:
        return (claim.world, claim.w, claim.f) in self._seen

    # ---- queries -------------------------------------------------------------

    def certified(self, world: str | None = None) -> list[Brick]:
        return [
            b
            for b in self.bricks
            if b.verdict.status == "certified" and (world is None or b.claim.world == world)
        ]

    def discovered_dim(self, world: str) -> int:
        ca = self.worlds[world]
        n = ca.k**self.max_width
        base = linalg.rank(trivial_densities(ca.k, self.max_width), n)
        return linalg.rank(self._span(world), n) - base

    # ---- persistence ---------------------------------------------------------

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "worlds.jsonl").open("w") as fh:
            for ca in self.worlds.values():
                fh.write(json.dumps(ca.describe()) + "\n")
        with (directory / "bricks.jsonl").open("w") as fh:
            for b in self.bricks:
                fh.write(json.dumps(b.to_json()) + "\n")

    def lean_module(self, name: str, doc: str, include_refuted: bool = True) -> str:
        theorems = []
        for b in self.bricks:
            if b.verdict.status == "certified" and b.novel or (
                include_refuted and b.verdict.status == "refuted"
            ):
                ca = self.worlds[b.claim.world]
                ident = lean.lean_ident(f"{b.claim.world}_{b.id}")
                theorems.append(lean.theorem(ident, ca, b.claim, b.verdict))
        return lean.module(name, theorems, doc)

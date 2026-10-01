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
        self._classes: dict[str, set[tuple]] = {}

    # ---- recording ---------------------------------------------------------

    def add_world(self, ca: CA) -> None:
        self.worlds.setdefault(ca.id, ca)

    def _span(self, world: str) -> list[list[Fraction]]:
        if world not in self._spans:
            ca = self.worlds[world]
            self._spans[world] = list(trivial_densities(ca.k, self.max_width))
        return self._spans[world]

    @staticmethod
    def _key(claim) -> tuple:
        if getattr(claim, "kind", "") == "mechanism":
            return ("mechanism", claim.world, claim.table)
        if getattr(claim, "kind", "") == "structure":
            return ("structure", claim.world, claim.q, claim.block, claim.t, claim.d)
        return (claim.world, claim.w, claim.f)

    @staticmethod
    def structure_class(verdict: Verdict, claim) -> tuple:
        return (claim.q, verdict.extra["period"], verdict.extra["velocity"])

    def structure_classes(self, world: str) -> set[tuple]:
        return self._classes.setdefault(world, set())

    def mechanisms(self) -> set[str]:
        return {b.claim.world for b in self.bricks if b.claim.kind == "mechanism" and b.novel}

    def is_novel(self, claim: Claim) -> bool:
        if getattr(claim, "kind", "") == "mechanism":
            return claim.world not in self.mechanisms()
        if getattr(claim, "kind", "") == "structure":
            return True  # decided after verification, from the species class
        ca = self.worlds[claim.world]
        span = self._span(claim.world)
        v = embed(list(claim.f), ca.k, claim.w, self.max_width)
        n = ca.k**self.max_width
        return linalg.rank(span + [v], n) > linalg.rank(span, n)

    def record(self, claim, verdict: Verdict, provenance: dict) -> Brick:
        if getattr(claim, "kind", "") == "mechanism":
            novel = verdict.status == "certified" and claim.world not in self.mechanisms()
            brick = Brick(f"b{len(self.bricks):05d}", claim, verdict, novel, provenance)
            self.bricks.append(brick)
            self._seen.add(self._key(claim))
            return brick
        if getattr(claim, "kind", "") == "structure":
            novel = False
            if verdict.status == "certified":
                cls = self.structure_class(verdict, claim)
                known = self.structure_classes(claim.world)
                novel = cls not in known
                known.add(cls)
            brick = Brick(f"b{len(self.bricks):05d}", claim, verdict, novel, provenance)
            self.bricks.append(brick)
            self._seen.add(self._key(claim))
            return brick
        novel = verdict.status == "certified" and self.is_novel(claim)
        if novel:
            ca = self.worlds[claim.world]
            self._span(claim.world).append(embed(list(claim.f), ca.k, claim.w, self.max_width))
        brick = Brick(f"b{len(self.bricks):05d}", claim, verdict, novel, provenance)
        self.bricks.append(brick)
        self._seen.add(self._key(claim))
        return brick

    def seen(self, claim) -> bool:
        return self._key(claim) in self._seen

    # ---- queries -------------------------------------------------------------

    def certified(self, world: str | None = None, kind: str = "conservation") -> list[Brick]:
        return [
            b
            for b in self.bricks
            if b.verdict.status == "certified"
            and b.claim.kind == kind
            and (world is None or b.claim.world == world)
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
            refuted_with_proof = b.verdict.status == "refuted" and (
                b.verdict.witness is not None or getattr(b.claim, "kind", "") == "structure"
            )
            if b.claim.kind == "mechanism":
                continue  # exact table comparison; no Lean statement
            if b.verdict.status == "certified" and b.novel or (include_refuted and refuted_with_proof):
                ca = self.worlds[b.claim.world]
                ident = lean.lean_ident(f"{b.claim.world}_{b.id}")
                theorems.append(lean.theorem(ident, ca, b.claim, b.verdict))
        return lean.module(name, theorems, doc)

"""The discovery loop: propose → verify → record → learn → propose again."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from .explorers import Explorer
from .library import Library
from .verify import verify
from .worlds.ca import CA, ConservationTruth


@dataclass
class RunResult:
    explorer: str
    budget: int
    used: int
    counts: dict
    discovered: int
    truth: int
    curve: list[tuple[int, int]]
    seconds: float
    cost: dict
    per_world: dict = field(default_factory=dict)

    @property
    def recall(self) -> float:
        return self.discovered / self.truth if self.truth else 0.0

    def to_json(self) -> dict:
        return {
            "explorer": self.explorer,
            "budget": self.budget,
            "proposals": self.used,
            "verdicts": self.counts,
            "discovered_dims": self.discovered,
            "hidden_dims": self.truth,
            "recall": round(self.recall, 4),
            "curve": self.curve,
            "seconds": round(self.seconds, 2),
            "cost": self.cost,
            "per_world": self.per_world,
        }


def truth_dims(worlds: list[CA], max_width: int) -> dict[str, int]:
    return {ca.id: ConservationTruth(ca, max_width).nontrivial_dim for ca in worlds}


def run(
    explorer: Explorer,
    worlds: list[CA],
    budget: int,
    library: Library | None = None,
    max_width: int = 2,
    seed: int = 0,
    truth: dict[str, int] | None = None,
    log=None,
) -> tuple[RunResult, Library]:
    library = library or Library(max_width)
    for ca in worlds:
        library.add_world(ca)
    by_id = {ca.id: ca for ca in worlds}
    truth = truth or truth_dims(worlds, max_width)
    rng = random.Random(seed)
    counts = {"certified": 0, "refuted": 0, "trivial": 0, "invalid": 0, "repeat": 0}
    start_dims = {ca.id: library.discovered_dim(ca.id) for ca in worlds}
    discovered = 0
    curve = [(0, 0)]
    started = time.monotonic()
    used = 0
    while used < budget:
        claim = explorer.propose(worlds, library)
        if claim is None:
            break
        used += 1
        if claim.world not in by_id:
            counts["invalid"] += 1
            continue
        if library.seen(claim):
            counts["repeat"] += 1
            continue
        verdict = verify(by_id[claim.world], claim, rng)
        brick = library.record(claim, verdict, {"explorer": explorer.name, "proposal": used})
        counts[verdict.status] += 1
        if brick.novel:
            discovered += 1
            curve.append((used, discovered))
            if log:
                log(f"[{used}/{budget}] NEW {claim.world} w={claim.w} f={list(claim.f)}")
        explorer.observe(claim, verdict, brick.novel)
    per_world = {
        ca.id: {
            "hidden": truth[ca.id],
            "found": library.discovered_dim(ca.id) - start_dims[ca.id],
        }
        for ca in worlds
    }
    target = sum(max(0, truth[ca.id] - start_dims[ca.id]) for ca in worlds)
    result = RunResult(
        explorer=explorer.name,
        budget=budget,
        used=used,
        counts=counts,
        discovered=discovered,
        truth=target,
        curve=curve,
        seconds=time.monotonic() - started,
        cost=explorer.cost(),
        per_world=per_world,
    )
    return result, library

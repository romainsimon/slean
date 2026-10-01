"""Engine tests. Run from ``engine/``: ``python3 -m unittest discover -s tests``."""

from __future__ import annotations

import itertools
import random
import shutil
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from slean import lean, linalg
from slean.bench import hidden_suite, transfer
from slean.engine import run
from slean.explorers import DataFitExplorer, LibraryExplorer, RandomExplorer
from slean.library import Library
from slean.verify import Claim, verify
from slean.worlds.ca import (
    ConservationTruth,
    code,
    eca,
    random_conserving,
    reflect,
    relabel,
    total,
    trivial_densities,
)


def brute_force_dim(ca, w, max_n):
    """Dimension of densities conserved on every configuration up to size max_n."""
    nf = ca.k**w
    rows = []
    for n in range(1, max_n + 1):
        for cells in itertools.product(range(ca.k), repeat=n):
            cells = list(cells)
            after = ca.step(cells)
            row = [Fraction(0)] * nf
            for i in range(n):
                row[code(ca.k, [after[(i + j) % n] for j in range(w)])] += 1
                row[code(ca.k, [cells[(i + j) % n] for j in range(w)])] -= 1
            rows.append(row)
    space = linalg.nullspace(linalg.rref(rows, nf)[0], nf)
    triv = trivial_densities(ca.k, w)
    return linalg.rank(space + triv, nf) - linalg.rank(triv, nf)


class GroundTruth(unittest.TestCase):
    def test_flux_space_matches_brute_force_on_all_elementary_rules(self):
        for rule in range(256):
            ca = eca(rule)
            self.assertEqual(ConservationTruth(ca, 2).nontrivial_dim, brute_force_dim(ca, 2, 8), rule)

    def test_traffic_rule_conserves_cars(self):
        self.assertIsNotNone(eca(184).flux([0, 1], 1))
        self.assertIsNone(eca(30).flux([0, 1], 1))

    def test_planted_law_is_conserved_and_found(self):
        rng = random.Random(5)
        for k in (3, 4):
            ca, hidden = random_conserving(k, rng, f"t{k}")
            self.assertEqual(verify(ca, Claim(ca.id, 1, tuple(hidden))).status, "certified")
            self.assertGreaterEqual(ConservationTruth(ca, 2).nontrivial_dim, 1)
            for _ in range(20):
                cells = [rng.randrange(k) for _ in range(rng.randint(1, 12))]
                self.assertEqual(total(hidden, 1, k, ca.step(cells)), total(hidden, 1, k, cells))

    def test_symmetry_transport(self):
        rng = random.Random(9)
        ca, hidden = random_conserving(3, rng, "s")
        perm = [2, 0, 1]
        for flip in (False, True):
            target = relabel(reflect(ca) if flip else ca, perm)
            self.assertEqual(LibraryExplorer.relation(ca, target)[0] is not None, True)
            g = LibraryExplorer.transport(3, 1, hidden, perm, flip)
            self.assertIsNotNone(target.flux(list(g), 1))


class Verification(unittest.TestCase):
    def test_statuses(self):
        ca = eca(184)
        self.assertEqual(verify(ca, Claim(ca.id, 1, (0, 1))).status, "certified")
        self.assertEqual(verify(ca, Claim(ca.id, 1, (1, 1))).status, "trivial")
        self.assertEqual(verify(ca, Claim(ca.id, 1, (0, 1, 2))).status, "invalid")
        refuted = verify(eca(30), Claim("eca-30", 1, (0, 1)))
        self.assertEqual(refuted.status, "refuted")
        cells = refuted.witness
        self.assertNotEqual(total([0, 1], 1, 2, eca(30).step(cells)), total([0, 1], 1, 2, cells))

    def test_gradient_is_trivial(self):
        # g(x_i) - g(x_{i+1}) with g = identity
        self.assertEqual(verify(eca(30), Claim("eca-30", 2, (0, -1, 1, 0))).status, "trivial")


class Discovery(unittest.TestCase):
    def test_random_is_poor_and_datafit_saturates_conservation_worlds(self):
        seen, held = hidden_suite(seed=3, families=2, members=2, distractors=2)
        worlds = seen + held
        rnd, _ = run(RandomExplorer(0), worlds, 40)
        fit, lib = run(DataFitExplorer(0), worlds, 200)
        self.assertEqual(fit.discovered, fit.truth)
        self.assertLess(rnd.discovered, fit.truth)
        # Nothing false is ever certified: every certified brick has a current.
        for brick in lib.certified():
            ca = lib.worlds[brick.claim.world]
            self.assertIsNotNone(ca.flux(list(brick.claim.f), brick.claim.w))

    def test_transfer_protocol_runs(self):
        report = transfer("library", 30, suite_seed=3)
        self.assertEqual(set(report), {"explorer", "cold", "seen", "warm"})


@unittest.skipUnless(shutil.which("lake") or (Path.home() / ".elan/bin/lake").exists(), "Lean not installed")
class LeanAgreement(unittest.TestCase):
    """Python certificates must be accepted by the Lean kernel, and forged ones rejected."""

    def _check(self, theorems):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Agreement.lean"
            path.write_text(lean.module("Agreement", theorems, "test"))
            return lean.kernel_check(path)

    def test_certified_and_refuted_claims_check(self):
        rng = random.Random(11)
        cases = [(eca(184), Claim("eca-184", 1, (0, 1))), (eca(30), Claim("eca-30", 1, (0, 1)))]
        for k in (3, 4):
            ca, hidden = random_conserving(k, rng, f"lean{k}")
            cases.append((ca, Claim(ca.id, 1, tuple(hidden))))
            cases.append((ca, Claim(ca.id, 1, tuple(1 if i == 0 else 0 for i in range(k)))))
        theorems = []
        for i, (ca, claim) in enumerate(cases):
            verdict = verify(ca, claim, rng)
            self.assertIn(verdict.status, ("certified", "refuted"))
            theorems.append(lean.theorem(f"c{i}", ca, claim, verdict))
        result = self._check(theorems)
        self.assertTrue(result["ok"], result["output"])

    def test_forged_certificate_is_rejected(self):
        ca = eca(184)
        claim = Claim(ca.id, 1, (0, 1))
        verdict = verify(ca, claim)
        verdict.flux = [0] * len(verdict.flux)
        result = self._check([lean.theorem("forged", ca, claim, verdict)])
        self.assertFalse(result["ok"])

    def test_false_claim_cannot_be_certified(self):
        ca = eca(30)
        claim = Claim(ca.id, 1, (0, 1))
        from slean.verify import Verdict

        fake = Verdict("certified", flux=[0, 0, 0, 0])
        result = self._check([lean.theorem("fake", ca, claim, fake)])
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()

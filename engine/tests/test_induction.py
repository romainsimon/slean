"""Law induction for the scripted reference: textbook families from few observations."""

from __future__ import annotations

import random
import unittest

from slean import induction, laws
from slean.bench import compressible_suite
from slean.worlds.ca import patterns


def _observe(ca, rng, n=40):
    cells = [rng.randrange(ca.k) for _ in range(n)]
    after = ca.step(cells)
    return {tuple(cells[(i + j) % n] for j in range(ca.s + 1)): after[i] for i in range(n)}


def _induce(ca, obs):
    """The first candidate, its open entries filled from the world, as a parsed law."""
    for h in induction.candidates(ca.k, ca.s, obs):
        for i in h.missing():
            h.table[i] = ca.loc(induction.witness(h, ca.k, ca.s, i))
        return h.family, laws.parse(h.law())
    return None, None


class Induction(unittest.TestCase):
    def test_families_are_recovered_exactly_and_compactly(self):
        rng = random.Random(0)
        limit = laws.compactness_limit(4**5)
        for ca in compressible_suite(41):
            family = ca.name.split("-")[-1]
            if family not in ("linear", "totalistic", "outer"):
                continue
            found, node = _induce(ca, _observe(ca, rng))
            self.assertIsNotNone(node, ca.name)
            self.assertTrue(all(laws.evaluate(node, p) == ca.loc(p) for p in patterns(4, 5)), ca.name)
            self.assertLessEqual(laws.description_length(node), limit)

    def test_random_rules_admit_no_hypothesis(self):
        rng = random.Random(1)
        for ca in compressible_suite(42):
            if ca.name.endswith("random"):
                self.assertEqual(list(induction.candidates(4, 4, _observe(ca, rng))), [], ca.name)

    def test_witness_hits_the_requested_index(self):
        h = next(iter(induction.candidates(4, 4, {})), None)
        self.assertIsNotNone(h)
        for i in range(h.size):
            if h.reachable is None or i in h.reachable:
                self.assertEqual(h.index(induction.witness(h, 4, 4, i)), i)


if __name__ == "__main__":
    unittest.main()

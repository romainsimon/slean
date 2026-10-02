"""Compact laws: short expressions accepted as a world's whole rule."""

from __future__ import annotations

import contextlib
import io
import json
import os
import random
import shutil
import tempfile
import unittest
from pathlib import Path

from slean import lab, laws, lean
from slean.verify import CompactLaw, verify
from slean.worlds.ca import compressible_world, eca, patterns


def cells_sum(n):
    return {"op": "sum", "args": [{"op": "cell", "j": j} for j in range(n)]}


def totalistic_law(ca):
    """The short law of a totalistic world, seen through any relabelling of states:
    new = g(sum of relabelled cells). Searches the k! relabellings."""
    import itertools

    for perm in itertools.permutations(range(ca.k)):
        g = {}
        if all(g.setdefault(sum(perm[a] for a in p), ca.loc(p)) == ca.loc(p) for p in patterns(ca.k, ca.s + 1)):
            table = [g.get(v, 0) for v in range((ca.k - 1) * (ca.s + 1) + 1)]
            relabelled = [{"op": "lookup", "table": list(perm), "a": {"op": "cell", "j": j}} for j in range(ca.s + 1)]
            arg = cells_sum(ca.s + 1) if list(perm) == list(range(ca.k)) else {"op": "sum", "args": relabelled}
            return laws.parse({"op": "lookup", "table": table, "a": arg})
    return None


class Parsing(unittest.TestCase):
    def test_sum_mod_lookup_and_lengths(self):
        law = laws.parse({"op": "mod", "a": cells_sum(3), "m": 2})
        self.assertEqual(laws.evaluate(law, (1, 1, 1)), 1)
        self.assertEqual(laws.description_length(law), 6)
        lk = laws.parse({"op": "lookup", "table": [5, 6], "a": {"op": "const", "c": 7}})
        self.assertEqual(laws.evaluate(lk, ()), 0)  # outside the table
        neg = laws.parse({"op": "lookup", "table": [5, 6], "a": {"op": "const", "c": -3}})
        self.assertEqual(laws.evaluate(neg, ()), 5)  # Lean Int.toNat: negative -> 0
        with self.assertRaises(laws.LawError):
            laws.parse({"op": "pow", "a": 1})

    def test_rule_90_is_xor_of_neighbours(self):
        # Rule 90: new = left XOR right = (x0 + x2) mod 2
        law = laws.parse({"op": "mod", "a": {"op": "add", "a": {"op": "cell", "j": 0}, "b": {"op": "cell", "j": 2}}, "m": 2})
        self.assertEqual(verify(eca(90), CompactLaw("eca-90", law)).status, "invalid")  # 8-entry table: limit 2
        world = compressible_world("linear", 4, 4, random.Random(1), "lin", disguise=False)
        self.assertEqual(laws.compactness_limit(len(world.table)), 256)


class Verification(unittest.TestCase):
    def test_totalistic_world_has_a_short_law_and_wrong_laws_are_refuted(self):
        world = compressible_world("totalistic", 4, 4, random.Random(4), "tot", disguise=False)
        law = totalistic_law(world)
        verdict = verify(world, CompactLaw(world.id, law))
        self.assertEqual(verdict.status, "certified")
        self.assertLess(verdict.extra["description_length"], 40)
        wrong = laws.parse({"op": "mod", "a": cells_sum(5), "m": 4})
        refuted = verify(world, CompactLaw(world.id, wrong))
        self.assertEqual(refuted.status, "refuted")
        p = tuple(refuted.extra["neighbourhood"])
        self.assertNotEqual(laws.evaluate(wrong, p), world.loc(p))

    def test_copying_the_table_is_not_a_law(self):
        world = compressible_world("random", 4, 4, random.Random(2), "rnd", disguise=False)
        from slean.worlds.ca import code

        copy = laws.parse({"op": "lookup", "table": list(world.table), "a": {"op": "sum", "args": [
            {"op": "mul", "a": {"op": "cell", "j": j}, "b": {"op": "const", "c": 4 ** (4 - j)}} for j in range(5)]}})
        self.assertEqual(verify(world, CompactLaw(world.id, copy)).status, "invalid")


@unittest.skipUnless(shutil.which("lake") or (Path.home() / ".elan/bin/lake").exists(), "Lean not installed")
class KernelAgreement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lean.ensure_built()

    def test_kernel_accepts_true_and_false_law_statements(self):
        world = compressible_world("totalistic", 4, 4, random.Random(4), "tot", disguise=False)
        good, bad = CompactLaw(world.id, totalistic_law(world)), CompactLaw(world.id, laws.parse({"op": "const", "c": 0}))
        theorems = [lean.theorem("good", world, good, verify(world, good)),
                    lean.theorem("bad", world, bad, verify(world, bad))]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Laws.lean"
            path.write_text(lean.module("Laws", theorems, "test"))
            result = lean.kernel_check(path)
        self.assertTrue(result["ok"], result["output"])


class LawsInLabs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["SLEAN_LABS"] = str(Path(self.tmp.name) / "secret")
        self.dir = Path(self.tmp.name) / "lab"
        self.dir.mkdir()
        lab.init(self.dir, "compressible", 5, "whitebox", proposals=5, cells=100)

    def tearDown(self):
        os.environ.pop("SLEAN_LABS", None)
        self.tmp.cleanup()

    def call(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = lab.command(self.dir, list(argv))
        return rc, buf.getvalue().strip()

    def test_a_true_law_is_scored_once(self):
        self.assertIn("Compact law", (self.dir / "README.md").read_text())
        state = json.loads((self.dir / ".lab/state.json").read_text())
        worlds = lab._worlds(state["lab_id"])
        sources = json.loads((Path(os.environ["SLEAN_LABS"]) / state["lab_id"] / "worlds.json").read_text())
        alias = next(w["alias"] for w in sources if w["source"].endswith("totalistic"))
        world = worlds[alias]
        found = totalistic_law(world)  # also finds the secret relabelling when there is one
        self.assertIsNotNone(found)
        self.assertLessEqual(laws.description_length(found), 256)
        law = laws.to_json(found)
        rc, text = self.call("propose", json.dumps({"kind": "law", "world": alias, "law": law}))
        self.assertEqual(json.loads(text)["status"], "certified")
        rc, text = self.call("propose", json.dumps({"kind": "law", "world": alias, "law": law}))
        self.assertEqual(json.loads(text)["status"], "repeat")
        report = lab.score(self.dir, max_width=3, max_period=3)
        self.assertEqual(report["compact_laws"]["found"], 1)
        self.assertEqual(report["compact_laws"]["hidden"], 12)


if __name__ == "__main__":
    unittest.main()

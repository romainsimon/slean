"""Structures and lab tests."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from slean import lab, lean
from slean.verify import Travel, verify
from slean.worlds import structures
from slean.worlds.ca import eca


class Structures(unittest.TestCase):
    def test_traffic_car_moves_right(self):
        ca = eca(184)
        self.assertTrue(structures.check(ca, (1,), 0, 1, 0))
        sp = structures.species(ca, (1,), 0, 1)
        self.assertEqual((sp.period, sp.velocity), (1, Fraction(1)))
        # A hole in a jam moves left.
        sp = structures.species(ca, (0,), 1, 1)
        self.assertEqual(sp.velocity, Fraction(-1))

    def test_verdicts(self):
        ca = eca(184)
        self.assertEqual(verify(ca, Travel("eca-184", 0, (1,), 1, 0)).status, "certified")
        self.assertEqual(verify(ca, Travel("eca-184", 0, (1,), 1, 1)).status, "refuted")
        self.assertEqual(verify(ca, Travel("eca-184", 0, (0, 0), 1, 0)).status, "trivial")
        self.assertEqual(verify(eca(1), Travel("eca-1", 0, (1,), 1, 0)).status, "invalid")

    def test_enumeration_is_exact_for_small_rules(self):
        found = structures.enumerate_species(eca(184), 4, 4)
        velocities = {(sp.q, str(sp.velocity)) for sp in found.values()}
        self.assertEqual(velocities, {(0, "1"), (1, "-1")})


@unittest.skipUnless(shutil.which("lake") or (Path.home() / ".elan/bin/lake").exists(), "Lean not installed")
class StructuresInLean(unittest.TestCase):
    def test_kernel_agrees(self):
        ca = eca(184)
        good, bad = Travel("eca-184", 0, (1, 0, 1), 1, 0), Travel("eca-184", 0, (1,), 2, 1)
        theorems = [lean.theorem("good", ca, good, verify(ca, good)), lean.theorem("bad", ca, bad, verify(ca, bad))]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "T.lean"
            path.write_text(lean.module("T", theorems, "test"))
            result = lean.kernel_check(path)
        self.assertTrue(result["ok"], result["output"])


class Lab(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["SLEAN_LABS"] = str(Path(self.tmp.name) / "secret")
        self.dir = Path(self.tmp.name) / "lab"
        self.dir.mkdir()
        lab.init(self.dir, "hidden", 3, "whitebox", proposals=3, cells=200)

    def tearDown(self):
        os.environ.pop("SLEAN_LABS", None)
        self.tmp.cleanup()

    def call(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = lab.command(self.dir, list(argv))
        return rc, buf.getvalue().strip()

    def test_secrets_stay_outside_the_lab(self):
        text = "".join(p.read_text() for p in self.dir.rglob("*") if p.is_file())
        state = json.loads((self.dir / ".lab/state.json").read_text())
        self.assertNotIn("h3-f", text)  # original world names reveal the family structure
        self.assertTrue((Path(os.environ["SLEAN_LABS"]) / state["lab_id"] / "worlds.json").exists())

    def test_budget_and_scoring(self):
        rc, worlds = self.call("worlds")
        first = json.loads(worlds.splitlines()[0])
        k = first["k"]
        rc, rows = self.call("experiment", first["world"], "0" * 10, "5")
        self.assertEqual(rc, 0)
        self.assertEqual(len(rows.splitlines()), 6)
        rc, _ = self.call("experiment", first["world"], "0" * 100, "5")
        self.assertEqual(rc, 3)  # 500 > remaining cell budget
        claim = {"kind": "conservation", "world": first["world"], "w": 1, "f": list(range(k))}
        for _ in range(3):
            self.call("propose", json.dumps(claim))
        rc, text = self.call("propose", json.dumps(claim))
        self.assertEqual(rc, 3)
        report = lab.score(self.dir, max_width=3, max_period=3)
        self.assertEqual(report["used"]["proposals"], 3)
        self.assertIn("repeat", report["verdicts"])


if __name__ == "__main__":
    unittest.main()

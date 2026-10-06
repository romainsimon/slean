"""Sealed suites: worlds come from a private generator; the engine only sees their tables."""

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

from slean import lab


class Sealed(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        previous = os.environ.get("SLEAN_LABS")
        os.environ["SLEAN_LABS"] = str(self.tmp / "secrets")
        self.addCleanup(lambda: os.environ.__setitem__("SLEAN_LABS", previous) if previous is not None
                        else os.environ.pop("SLEAN_LABS", None))

    def worlds_file(self, entries):
        path = self.tmp / "private-worlds.json"
        path.write_text(json.dumps(entries))
        return path

    def test_sealed_worlds_are_loaded_and_scored_by_their_law_flag(self):
        rng = random.Random(0)
        entries = [{"name": f"private-{i}", "k": 4, "s": 4, "table": [rng.randrange(4) for _ in range(1024)],
                    "law": i < 3} for i in range(5)]
        directory = self.tmp / "lab"
        directory.mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            state = lab.init(directory, "sealed", None, "blackbox", 10, 100, worlds_file=self.worlds_file(entries))
            score = lab.score(directory)
        self.assertEqual(score["compact_laws"]["hidden"], 3)
        self.assertEqual(score["mechanisms"]["worlds"], 5)
        visible = "".join(p.read_text() for p in directory.rglob("*") if p.is_file())
        self.assertNotIn("private-", visible)
        self.assertEqual(json.loads((self.tmp / "secrets" / state["lab_id"] / "suite.json").read_text())["suite"], "sealed")

    def test_malformed_sealed_worlds_are_refused(self):
        directory = self.tmp / "lab"
        directory.mkdir()
        bad = [{"name": "a", "k": 4, "s": 4, "table": [0] * 1024}, {"name": "b", "k": 4, "s": 4, "table": [0] * 10}]
        with self.assertRaises(SystemExit):
            lab.init(directory, "sealed", None, "blackbox", 10, 100, worlds_file=self.worlds_file(bad))
        with self.assertRaises(SystemExit):
            lab.init(directory, "sealed", None, "blackbox", 10, 100)


if __name__ == "__main__":
    unittest.main()

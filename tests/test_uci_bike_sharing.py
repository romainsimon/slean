"""Offline checks for the frozen retrospective example's arithmetic and links."""

import hashlib
import importlib.util
import json
import unittest
from datetime import datetime
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_uci_bike_sharing", ROOT / "tools/evaluate_uci_bike_sharing.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
EXAMPLE = ROOT / "examples/uci-bike-sharing"


class UciBikeSharingTests(unittest.TestCase):
    def test_exact_rounding_and_holdout_split(self):
        self.assertEqual(MODULE.decimal_six(Fraction(1, 2_000_000)), "0.000000")
        self.assertEqual(MODULE.decimal_six(Fraction(3, 2_000_000)), "0.000002")
        rows = [
            (datetime(2011, 1, 1, 0), 0, 0),
            (datetime(2011, 1, 1, 1), 1, 10),
            (datetime(2012, 1, 1, 0), 0, 0),
            (datetime(2012, 1, 1, 1), 1, 10),
        ]
        protocol = json.loads((EXAMPLE / "protocol.json").read_text())
        scored = MODULE.score(rows, protocol)
        self.assertEqual(scored["baseline_mae"], Fraction(5))
        self.assertEqual(scored["candidate_mae"], Fraction(0))
        self.assertEqual(scored["improvement"], Fraction(5))
        rows[-1] = (datetime(2012, 1, 1, 1), 1, 100)
        self.assertEqual(MODULE.score(rows, protocol)["hour_means"], scored["hour_means"])

    def test_record_links_source_protocol_and_measured_result(self):
        protocol_raw = (EXAMPLE / "protocol.json").read_bytes()
        result_raw = (EXAMPLE / "result.json").read_bytes()
        case = json.loads((EXAMPLE / "case.json").read_text())
        protocol = json.loads(protocol_raw)
        result = json.loads(result_raw)
        self.assertEqual(hashlib.sha256(protocol_raw).hexdigest(), result["protocol"]["sha256"])
        self.assertEqual(result["source"]["member_sha256"], protocol["source"]["member_sha256"])
        self.assertEqual(case["events"][1]["payload"]["digest"],
                         "sha256:" + protocol["source"]["member_sha256"])
        self.assertEqual(case["events"][3]["payload"]["digest"],
                         "sha256:" + hashlib.sha256(result_raw).hexdigest())
        self.assertEqual(case["events"][4]["payload"]["value"],
                         result["measurements"]["mae_improvement"]["decimal_6_half_even"])
        self.assertEqual(case["events"][0]["recorded_at"], protocol["frozen_at_utc"])
        self.assertLess(result["historical_source_hours"]["train_2011"]["last_local_hour"],
                        result["historical_source_hours"]["held_out_2012"]["first_local_hour"])
        self.assertTrue(result["evaluation"]["started_at_utc"].startswith("2026-"))


if __name__ == "__main__":
    unittest.main()

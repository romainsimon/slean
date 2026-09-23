"""Synthetic source triplet for the read-only autoresearch trace boundary."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_autoresearch_trace import audit


class AdapterTests(unittest.TestCase):
    def test_read_only_loss_report_and_real_shape_mutations(self):
        protocol = {"protocol": "synthetic", "units": "dimensionless",
                    "selection_code_sha256": "synthetic-code", "model_odds_threshold": 0.95}
        definition = hashlib.sha256(json.dumps(protocol, sort_keys=True,
                                               separators=(",", ":")).encode()).hexdigest()
        events = []

        def append(kind, payload, second):
            events.append({"event_id": f"source-{len(events)+1}", "sequence": len(events)+1,
                           "observed_at": f"2026-01-01T00:00:{second:02d}Z",
                           "type": kind, "payload": payload})

        append("protocol_frozen", {"definition_sha256": definition,
                                   "observation_budget": 1, "protocol": "synthetic"}, 1)
        append("prediction_frozen", {"observation_id": 1, "phase": "audit",
                                     "prediction_sha256": "synthetic-prediction", "predictions": {"H0": 0, "H1": 1}}, 2)
        append("observation_recorded", {"observation_id": 1, "phase": "audit",
                                       "prediction_sha256": "synthetic-prediction",
                                       "observation": 0.5, "units": "dimensionless"}, 3)
        append("prediction_frozen", {"observation_id": 2, "phase": "audit",
                                     "prediction_sha256": "synthetic-prediction-2", "predictions": {"H0": 0, "H1": 1}}, 4)
        append("observation_recorded", {"observation_id": 2, "phase": "audit",
                                       "prediction_sha256": "synthetic-prediction-2",
                                       "observation": 0.6, "units": "dimensionless"}, 5)
        append("discrimination_completed", {"decision": "abstain", "observations_used": 2}, 6)
        manifest = {"attempt_id": "synthetic-source", "question": "Synthetic question?",
                    "hypothesis": "Synthetic claim.", "scientific_decision": "inconclusive",
                    "budgets": {"cpu_seconds": 10}, "usage": {"cpu_seconds": 1},
                    "provenance": {"definition_sha256": definition}, "artifacts": []}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "manifest.json").write_text(json.dumps(manifest))
            (path / "protocol.json").write_text(json.dumps(protocol))
            (path / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
            result = audit(path)
        self.assertEqual(result["slean_validation"], "accepted")
        self.assertTrue(result["source_files_unchanged"])
        self.assertTrue(result["source_definition_matches_file"])
        self.assertEqual(result["mutation_probes_on_memory_copy"], {
            "unit_mismatch": "metric_unit", "missing_prediction": "missing_relation_ref",
            "future_observation": "future_observation", "changed_protocol_file": "accepted",
            "second_freeze_event": "accepted"})
        self.assertTrue(result["losses"]["decision_critical_losses"])


if __name__ == "__main__":
    unittest.main()

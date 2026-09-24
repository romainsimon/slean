"""Synthetic source triplet for the read-only autoresearch trace boundary."""

import hashlib
import json
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.audit_autoresearch_trace import BIN, audit, digest, loss_report, make_case


class AdapterTests(unittest.TestCase):
    def test_read_only_loss_report_and_real_shape_mutations(self):
        protocol = {"protocol": "synthetic", "units": "dimensionless",
                    "selection_code_sha256": "synthetic-code", "model_odds_threshold": 0.95}
        definition = hashlib.sha256(json.dumps(protocol, sort_keys=True,
                                               separators=(",", ":")).encode()).hexdigest()
        events = []

        def append(kind, payload, second):
            events.append({"event_id": f"source-{len(events)+1}", "sequence": len(events)+1,
                           "attempt_id": "synthetic-source", "schema_version": "1.0.0",
                           "observed_at": f"2026-01-01T00:00:{second:02d}Z",
                           "type": kind, "payload": payload})

        append("protocol_frozen", {"definition_sha256": definition,
                                   "observation_budget": 1, "protocol": "synthetic"}, 1)
        append("prediction_frozen", {"observation_id": 1, "phase": "audit",
                                     "condition": {"x": 1},
                                     "prediction_sha256": "synthetic-prediction", "predictions": {"H0": 0, "H1": 1}}, 2)
        append("observation_recorded", {"observation_id": 1, "phase": "audit",
                                       "condition": {"x": 1},
                                       "prediction_sha256": "synthetic-prediction",
                                       "observation": 0.5, "units": "dimensionless"}, 3)
        append("prediction_frozen", {"observation_id": 2, "phase": "audit",
                                     "condition": {"x": 2},
                                     "prediction_sha256": "synthetic-prediction-2", "predictions": {"H0": 0, "H1": 1}}, 4)
        append("observation_recorded", {"observation_id": 2, "phase": "audit",
                                       "condition": {"x": 2},
                                       "prediction_sha256": "synthetic-prediction-2",
                                       "observation": 0.6, "units": "dimensionless"}, 5)
        completion = {"decision": "abstain", "observations_used": 2,
                      "planning_cpu_seconds": 0.1,
                      "posterior_model_probabilities": {"H0": 0.5, "H1": 0.5}}
        append("discrimination_completed", completion, 6)
        artifact_bytes = b"synthetic development artifact"
        manifest = {"attempt_id": "synthetic-source", "question": "Synthetic question?",
                    "hypothesis": "Synthetic claim.", "scientific_decision": "inconclusive",
                    "budgets": {"cpu_seconds": 10, "model_calls": 2},
                    "usage": {"cpu_seconds": 1, "model_calls": 1},
                    "provenance": {"definition_sha256": definition},
                    "artifacts": [{"path": "synthetic-artifact.bin",
                                   "size_bytes": len(artifact_bytes),
                                   "sha256": hashlib.sha256(artifact_bytes).hexdigest()}],
                    "result": {"discrimination": completion}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "manifest.json").write_text(json.dumps(manifest))
            (path / "protocol.json").write_text(json.dumps(protocol))
            (path / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
            artifact = path / "synthetic-artifact.bin"
            artifact.write_bytes(artifact_bytes)
            result = audit(path)
            command = [sys.executable, str(Path(__file__).resolve().parents[1] /
                                          "tools/audit_autoresearch_trace.py"), str(path)]
            valid_cli = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(valid_cli.returncode, 0)
            self.assertTrue(json.loads(valid_cli.stdout)["structural_gate_passed"])
            artifact.write_bytes(b"altered development artifact")
            invalid_cli = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(invalid_cli.returncode, 1)
            invalid_report = json.loads(invalid_cli.stdout)
            self.assertFalse(invalid_report["source_artifact_hashes_valid"])
            self.assertEqual(invalid_report["slean_validation"], "accepted")
            self.assertFalse(invalid_report["structural_gate_passed"])
        self.assertEqual(result["slean_validation"], "accepted")
        self.assertTrue(result["structural_gate_passed"])
        self.assertTrue(result["source_files_unchanged"])
        self.assertTrue(result["source_definition_matches_file"])
        self.assertEqual(result["converted_event_count"], 21)
        self.assertEqual(result["mutation_probes_on_memory_copy"], {
            "unit_mismatch": "metric_unit", "missing_prediction": "missing_relation_ref",
            "future_observation": "future_observation", "changed_protocol_file": "source_protocol_digest",
            "second_freeze_event": "source_second_freeze",
            "completion_decision": "source_decision_provenance",
            "completion_decision_rehashed": "source_decision_provenance",
            "omitted_assessment_observation": "source_projection"})
        self.assertEqual(result["losses"]["wire_fields_lost"], [])
        self.assertEqual(result["losses"]["source_record_integrity_errors"], [])
        self.assertTrue(result["source_preservation_verified"])
        self.assertIn("budgets/model_calls", result["losses"]["manifest_fields_not_typed"])
        self.assertIn("usage/model_calls", result["losses"]["manifest_fields_not_typed"])
        self.assertNotIn("budgets/cpu_seconds", result["losses"]["manifest_fields_not_typed"])
        self.assertIn("sequence", result["losses"]["event_fields_not_typed"])
        self.assertTrue(result["losses"]["semantic_limits"])

        case = make_case(manifest, protocol, events)
        unsupported = copy.deepcopy(manifest)
        unsupported["scientific_decision"] = "unmapped-source-decision"
        with self.assertRaisesRegex(ValueError, "unsupported source scientific_decision"):
            make_case(unsupported, protocol, events)
        source_records = [e["payload"] for e in case["events"] if e["kind"] == "source_recorded"]
        self.assertEqual([json.loads(r["raw_json"]) for r in source_records],
                         [manifest, protocol, *events])
        self.assertTrue(all(r["identity"]["audience"] == "owner" for r in source_records))
        assessment = next(e["payload"] for e in case["events"] if e["kind"] == "assessment_recorded")
        self.assertEqual(len(assessment["observation_refs"]), 2)
        self.assertEqual(assessment["verdict"], "external_unverified")

        tampered = copy.deepcopy(case)
        source_manifest = next(e["payload"] for e in tampered["events"]
                               if e["kind"] == "source_recorded" and
                               e["payload"]["source_role"] == "manifest")
        truncated = copy.deepcopy(manifest)
        del truncated["budgets"]["cpu_seconds"]
        source_manifest["raw_json"] = json.dumps(truncated, sort_keys=True, separators=(",", ":"))
        source_manifest["canonical_sha256"] = digest(truncated)
        losses = loss_report(manifest, protocol, events, tampered)
        self.assertIn("manifest/budgets/cpu_seconds", losses["wire_fields_lost"])
        self.assertIn("manifest:content_mismatch", losses["source_record_integrity_errors"])
        self.assertIn("manifest:digest_mismatch", losses["source_record_integrity_errors"])

        missing_record = copy.deepcopy(case)
        missing_record["events"] = [e for e in missing_record["events"]
                                    if not (e["kind"] == "source_recorded" and
                                            e["payload"]["identity"]["id"] ==
                                            "source-event:source-3")]
        losses = loss_report(manifest, protocol, events, missing_record)
        self.assertIn("events/2", losses["wire_fields_lost"])
        self.assertIn("events/2:missing_record", losses["source_record_integrity_errors"])

        owner = subprocess.run([str(BIN), "export", "-", "owner"], input=json.dumps(case),
                               text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(owner.stdout)["case"], case)
        agent = subprocess.run([str(BIN), "export", "-", "agent"], input=json.dumps(case),
                               text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(agent.stdout)["case"]["events"], [])
        self.assertNotIn("synthetic-prediction", agent.stdout)
        changed = copy.deepcopy(case)
        hidden = next(e for e in changed["events"] if e["kind"] == "source_recorded")
        hidden["payload"]["raw_json"] = hidden["payload"]["raw_json"].replace(
            "Synthetic question?", "Private changed question")
        agent_changed = subprocess.run([str(BIN), "export", "-", "agent"],
                                       input=json.dumps(changed), text=True,
                                       capture_output=True, check=True)
        self.assertEqual(agent_changed.stdout, agent.stdout)


if __name__ == "__main__":
    unittest.main()

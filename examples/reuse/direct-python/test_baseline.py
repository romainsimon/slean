from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from consumer import consume
from producer import ROOT, calibrate, digest
from research import assess, run_cycle
from package_baseline import build


class DirectToolBaseline(unittest.TestCase):
    def setUp(self):
        self.calibration = calibrate(ROOT / "fixtures/calibration.csv")
        self.sample = json.loads((ROOT / "fixtures/sample.json").read_text())
        self.inputs = json.loads((ROOT / "fixtures/research.json").read_text())

    def use(self, sample=None, **kwargs):
        return consume(self.calibration, sample or self.sample,
                       expected_version=kwargs.pop("expected_version", self.calibration["sha256"]), **kwargs)

    def test_fit_inverse_bound_and_unknown_parameter_uncertainty(self):
        result = self.use()
        self.assertEqual(self.calibration["model"]["gain"]["value"], "2")
        self.assertEqual(self.calibration["model"]["offset"]["value"], "0.5")
        self.assertEqual(result["displacement"]["value"], "4")
        self.assertEqual(result["conditional_error_bound"]["value"], "0.01")
        self.assertEqual(result["status"], "conditional")
        self.assertEqual(result["parameter_uncertainty"], "unquantified")

    def test_unit_conversion_including_temperature_offset(self):
        self.sample["reading"] = {"value": "8500", "unit": "millivolt"}
        self.sample["temperature"] = {"value": "20", "unit": "degree_Celsius"}
        self.assertEqual(self.use()["displacement"]["value"], "4")

    def test_wrong_dimension_range_sensor_and_output(self):
        for field, value, code in [
            ("reading", {"value": "8.5", "unit": "meter"}, "quantity_or_dimension_error"),
            ("reading", {"value": "12", "unit": "volt"}, "outside_operating_range"),
            ("sensor", "sensor-B", "wrong_sensor"),
            ("claimed_displacement", {"value": "4.25", "unit": "millimeter"}, "output_not_reproduced"),
        ]:
            with self.subTest(code=code):
                sample = deepcopy(self.sample)
                sample[field] = value
                result = self.use(sample)
                self.assertEqual(result["status"], "incompatible")
                self.assertIn(code, result["diagnostics"])

    def test_missing_applicability_and_unsupported_uncertainty(self):
        del self.sample["applicability_evidence"]
        self.assertIn("applicability_evidence_missing", self.use()["remaining_assumptions"])
        self.sample["uncertainty_kind"] = "confidence_interval"
        self.assertEqual(self.use()["status"], "unsupported")

    def test_method_and_version_bindings(self):
        self.assertIn("changed_method_bytes", self.use(actual_method_digest="0" * 64)["diagnostics"])
        self.assertIn("wrong_version", self.use(expected_version="0" * 64)["diagnostics"])
        self.calibration["model"]["offset"]["value"] = "0"
        self.assertIn("model_integrity", self.use()["diagnostics"])

    def test_noninvertible_gain_and_invalid_error_bound(self):
        for field, value, diagnostic in [("gain", "0", "zero_gain"),
                                          ("assumed_residual_bound", "-0.02", "negative_error_bound")]:
            changed = deepcopy(self.calibration)
            changed["model"][field]["value"] = value
            changed["sha256"] = digest(changed["model"])
            result = consume(changed, self.sample, expected_version=changed["sha256"])
            self.assertEqual(result["status"], "incompatible")
            self.assertIn(diagnostic, result["diagnostics"])

    def test_research_revision_preserves_the_original_and_unknowns(self):
        original = deepcopy(self.calibration)
        cycle = run_cycle(self.calibration, self.sample, self.inputs)
        self.assertEqual(self.calibration, original)
        self.assertEqual([x["outcome"] for x in cycle["assessments"]], ["failed_prediction", "within_bound"])
        self.assertEqual(cycle["needs_reassessment"], ["high-temperature-prediction"])
        self.assertNotEqual(cycle["hypothesis"]["sha256"], cycle["revision"]["sha256"])
        self.assertEqual(cycle["revision"]["model"]["supersedes"], cycle["hypothesis"]["sha256"])
        self.assertEqual(cycle["follow_up"]["question"], self.inputs["follow_up"])
        self.assertEqual(cycle["alternative"]["status"], "unresolved")
        before, after = [x["result"] for x in cycle["blocked_question"]["attempts"]]
        self.assertIn("temperature_requirement_not_met", before["diagnostics"])
        self.assertEqual(after["displacement"]["value"], "4")
        self.assertEqual(after["status"], "conditional")
        self.assertIn("gain_treated_as_exact", after["remaining_assumptions"])
        before_attempt, after_attempt = cycle["blocked_question"]["attempts"]
        self.assertEqual(before_attempt["input_sha256"], after_attempt["input_sha256"])
        self.assertEqual(before_attempt["input_sha256"], digest(cycle["blocked_question"]["input"]))
        self.assertEqual(before_attempt["method_sha256"], after_attempt["method_sha256"])
        self.assertNotEqual(before_attempt["model"], after_attempt["model"])
        self.assertEqual(after_attempt["assessment"], cycle["assessments"][1]["protocol"])

    def test_frozen_rule_cannot_be_relaxed_after_observation(self):
        cycle = run_cycle(self.calibration, self.sample, self.inputs)
        rule = deepcopy(cycle["protocols"][0])
        fixed = rule["sha256"]
        rule["rule"]["bound"]["value"] = "0.2"
        for refresh_hash in [False, True]:
            if refresh_hash:
                rule["sha256"] = digest(rule["rule"])
            result = assess(rule, cycle["observations"][0], expected_protocol=fixed)
            self.assertEqual(result["diagnostic"], "changed_frozen_rule")
        self.assertEqual(cycle["assessments"][0]["outcome"], "failed_prediction")

    def test_out_of_scope_observation_does_not_refute_the_model(self):
        cycle = run_cycle(self.calibration, self.sample, self.inputs)
        observation = deepcopy(cycle["observations"][0])
        observation["temperature"] = {"value": "400", "unit": "kelvin"}
        rule = cycle["protocols"][0]
        self.assertEqual(assess(rule, observation, expected_protocol=rule["sha256"])["outcome"], "not_applicable")

    def test_unrelated_contribution_and_wrong_context_do_not_resolve_obstacle(self):
        self.sample["temperature"] = self.inputs["temperature"]
        first = self.use()
        unrelated_body = {"kind": "spectral_model", "question": "An unrelated problem"}
        unrelated = {"model": unrelated_body, "sha256": digest(unrelated_body)}
        candidate = consume(unrelated, self.sample, expected_version=unrelated["sha256"])
        self.assertEqual(candidate["status"], "unsupported")
        self.assertIn("method_interface_not_supported", candidate["diagnostics"])
        self.assertEqual(self.use(), first)
        self.assertEqual(first["status"], "incompatible")

    def test_independent_rocrate_reader_and_payload_tampering(self):
        import os
        node = os.environ.get("SLEAN_NODE", "node")
        with tempfile.TemporaryDirectory(prefix="slean-direct-baseline-") as tmp:
            output = Path(tmp) / "crate"
            build(output)
            command = [node, str(ROOT / "read_crate.mjs"), str(output)]
            read = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(read.returncode, 0, read.stdout + read.stderr)
            # Run only the exported source, with installed dependencies, outside the checkout.
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)
            reproduced = subprocess.run(
                [sys.executable, "consumer.py", "calibration.json", "sample.json", "reproduced.json",
                 "--expected-version", self.calibration["sha256"]],
                cwd=output, env=environment, capture_output=True, text=True)
            self.assertEqual(reproduced.returncode, 0, reproduced.stdout + reproduced.stderr)
            self.assertEqual(json.loads((output / "reproduced.json").read_text()),
                             json.loads((output / "result.json").read_text()))
            result = json.loads((output / "result.json").read_text())
            result["displacement"]["value"] = "4.25"
            (output / "result.json").write_text(json.dumps(result))
            altered = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(altered.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

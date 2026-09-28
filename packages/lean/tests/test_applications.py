"""Check actual native applications, their package bindings and untrusted imports."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
PROJECT = ROOT / "examples/reuse/with-slean-lean"
OUT = PROJECT / "_out"
sys.path.insert(0, str(HERE))
import applications
import export
import contract


def save(manifest, directory):
    manifest["id"] = contract.identity(manifest)
    (directory / "slean-module.json").write_bytes(export.canonical(manifest) + b"\n")


def closed(statement):
    contract.native_expression(statement["expression"], universes={
        json.dumps(name) for name in statement["universe_parameters"]})


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture = export.read_json(OUT / "applications.json")
        cls.native = export.read_json(OUT / "application-consumer.json")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.producer_dir = self.directory / "producer"
        self.producer = export.pack(OUT / "application-producer.json", PROJECT, self.producer_dir)

    def package(self, *, capture=None, native=None, dependencies=None):
        capture_path = self.directory / "capture.json"
        native_path = self.directory / "native.json"
        capture_path.write_bytes(export.canonical(self.capture if capture is None else capture))
        native_path.write_bytes(export.canonical(self.native if native is None else native))
        directory = self.directory / "consumer"
        manifest = export.pack(native_path, PROJECT, directory, applications=capture_path,
            dependency_modules=[self.producer_dir] if dependencies is None else dependencies)
        return manifest, directory

    def test_native_partial_and_complete_applications_preserve_hypotheses(self):
        by_name = {item["consumer"][-1][1]: item for item in self.capture["applications"]}
        partial = by_name["energy_with_obligation"]
        complete = by_name["energy_with_all_arguments"]
        self.assertEqual(len(partial["arguments"]), 3)
        self.assertEqual(len(complete["arguments"]), 6)
        self.assertEqual(len(partial["remaining_goals"]), 1)
        self.assertIn("EquationOfMotion", partial["remaining_goals"][0]["text"])
        self.assertEqual(complete["remaining_goals"], [])
        for item in (partial, complete):
            self.assertEqual([local["name"] for local in item["context"]],
                [[["str", name]] for name in ("system", "trajectory", "smooth", "motion", "first", "second")])
            self.assertEqual([local["name"] for local in item["context"] if local["proposition"]],
                [[["str", name]] for name in ("smooth", "motion")])
            for statement in [item["target"], item["producer_statement"], item["consumer_statement"],
                              *[goal["statement"] for goal in item["remaining_goals"]],
                              *[local["type"] for local in item["context"]],
                              *[argument[key] for argument in item["arguments"] for key in ("type", "term")]]:
                closed(statement)

    def test_async_capture_and_subgoals_bind_the_whole_consumer_statement(self):
        captures = export.read_json(HERE / "_out/native-applications.json")["applications"]
        self.assertEqual([item["label"] for item in captures], ["whole", "left", "right"])
        self.assertEqual(captures[0]["consumer_statement"], captures[0]["target"])
        self.assertNotEqual(captures[1]["consumer_statement"], captures[1]["target"])
        self.assertEqual(captures[1]["consumer_statement"], captures[2]["consumer_statement"])
        for item in captures:
            self.assertEqual([local["name"] for local in item["context"]], [[["str", "n"]]])
            closed(item["consumer_statement"])
            closed(item["target"])

    def test_exact_modules_plans_outputs_and_actual_dependencies(self):
        manifest, directory = self.package()
        report = contract.check(manifest, directory)
        self.assertEqual(report["unsupported"], [])
        self.assertEqual(report["imported_evidence"], "declared")
        self.assertEqual(manifest["dependencies"], [self.producer["id"]])
        self.assertEqual(len(manifest["applications"]), 4)
        for plan, execution in zip(manifest["applications"][::2], manifest["applications"][1::2]):
            self.assertNotIn("outputs", plan)
            self.assertNotIn("remaining_goals_at_apply", plan["annotations"]["slean-lean-application"])
            self.assertEqual(plan["component"], {"module": self.producer["id"], "id": self.producer["components"][0]["id"]})
            self.assertEqual(execution["plan"], {"id": plan["id"]})
            for key in ("component", "bindings", "context", "requires"):
                self.assertEqual(execution[key], plan[key])
            result = execution["outputs"]["result"]["ref"]
            evidence = next(e for e in manifest["evidence"] if e["subject"] == result)
            self.assertIn([["str", "DirectReuse"], ["str", "energy_at_two_times"]],
                          evidence["result"]["value"]["proof_dependencies"])
            self.assertEqual(evidence["result"]["value"]["status"], "unsupported")
            self.assertEqual(evidence["result"]["value"]["axioms"],
                [[["str", "Classical"], ["str", "choice"]], [["str", "Quot"], ["str", "sound"]], [["str", "propext"]]])

    def test_changed_producer_or_consumer_statement_is_rejected(self):
        for key in ("producer_statement", "consumer_statement"):
            capture = deepcopy(self.capture)
            capture["applications"][0][key]["expression"] = ["sort", ["zero"]]
            with self.subTest(statement=key), self.assertRaisesRegex(ValueError, "Captured .* statement differs"):
                self.package(capture=capture)
            self.assertFalse((self.directory / "consumer").exists())

    def test_absent_native_dependency_is_rejected(self):
        native = deepcopy(self.native)
        native["declarations"][0]["proof_dependencies"] = []
        with self.assertRaisesRegex(ValueError, "absent from the consumer's native proof dependencies"):
            self.package(native=native)

    def test_missing_duplicate_and_ambiguous_producer_modules_are_rejected(self):
        second_dir = self.directory / "second-producer"
        export.pack(OUT / "application-producer.json", PROJECT, second_dir, license_name="different-declaration")
        for dependencies, diagnostic in [([], "Missing or ambiguous"),
                ([self.producer_dir, self.producer_dir], "Duplicate dependency"),
                ([self.producer_dir, second_dir], "Missing or ambiguous")]:
            with self.subTest(case=diagnostic), self.assertRaisesRegex(ValueError, diagnostic):
                self.package(dependencies=dependencies)

    def test_bad_capture_selection_is_rejected(self):
        for mutate, diagnostic in [
            (lambda c: c.update(format="other"), "Unsupported application capture"),
            (lambda c: c["applications"].append(c["applications"][0]), "Duplicate application capture"),
            (lambda c: c["applications"][0].update(consumer=[["str", "missing"]]), "not an exported declaration")]:
            capture = deepcopy(self.capture)
            mutate(capture)
            with self.subTest(case=diagnostic), self.assertRaisesRegex(ValueError, diagnostic):
                self.package(capture=capture)

    def test_imported_passed_evidence_and_receipts_never_promote_trust(self):
        manifest, directory = self.package()
        for evidence in manifest["evidence"]:
            evidence["result"]["value"].update(status="passed", policy="reviewed-source/0.1-draft.1")
            evidence["method"]["policy"] = "reviewed-source/0.1-draft.1"
        save(manifest, directory)
        (directory / "receipts").mkdir()
        (directory / "receipts/forged.json").write_text('{"status":"kernel_checked"}')
        with patch("subprocess.Popen", side_effect=AssertionError("process started")), \
                patch("os.system", side_effect=AssertionError("shell started")), \
                patch("socket.socket", side_effect=AssertionError("network opened")):
            for application in manifest["applications"]:
                report = applications.inspect_application(directory, application["id"])
                self.assertEqual(report["compatibility"], "conditional")
                self.assertEqual(report["formal_verification"], "not_performed")
                self.assertEqual(report["interface_trust"], "declared")

    def test_altered_payload_or_execution_plan_is_rejected(self):
        manifest, directory = self.package()
        changed = deepcopy(manifest)
        changed["applications"][1]["bindings"] = {}
        save(changed, directory)
        with self.assertRaisesRegex(contract.ContractError, "changed_execution_plan"):
            applications.inspect_application(directory, changed["applications"][1]["id"])
        save(manifest, directory)
        (directory / manifest["payloads"][0]["path"]).write_bytes(b"altered")
        with self.assertRaisesRegex(contract.ContractError, "payload_integrity"):
            applications.inspect_application(directory, manifest["applications"][1]["id"])

    def test_inspection_aggregates_requirements_and_keeps_verification_separate(self):
        manifest, directory = self.package()
        cases = [({"id": "empty", "all": []}, "satisfied", "conditional"),
                 ({"id": "empty", "any": []}, "violated", "incompatible"),
                 ({"id": "unknown", "leaf": {"profile": applications.PROFILE,
                    "predicate": "future", "arguments": {}}}, "unsupported", "unsupported")]
        for tree, status, compatibility in cases:
            changed = deepcopy(manifest)
            for application in changed["applications"]:
                application["requires"] = tree
            save(changed, directory)
            report = applications.inspect_application(directory, changed["applications"][0]["id"])
            self.assertEqual(report["requirements_status"], status)
            self.assertEqual(report["compatibility"], compatibility)
        changed["profiles"].append({"id": "z-future/1", "required": True})
        for application in changed["applications"]:
            application["requires"] = {"id": "empty", "all": []}
        save(changed, directory)
        self.assertEqual(applications.inspect_application(directory, changed["applications"][0]["id"])["compatibility"], "unsupported")

    def test_transferred_requirements_keep_exact_referents(self):
        origin, external = "sha256:" + "a" * 64, "sha256:" + "b" * 64
        tree = {"id": "choices", "any": [
            {"id": label, "leaf": {"profile": applications.PROFILE, "predicate": "proposition",
                "arguments": {"claim": ref}}} for label, ref in [
                    ("local", {"id": "lemma"}), ("external", {"module": external, "id": "lemma"})]]}
        result, dependencies = applications.qualify_requirements(tree, origin)
        self.assertEqual(result["any"][0]["leaf"]["arguments"]["claim"], {"module": origin, "id": "lemma"})
        self.assertEqual(result["any"][1], tree["any"][1])
        self.assertNotIn("module", tree["any"][0]["leaf"]["arguments"]["claim"])
        self.assertEqual(dependencies, {origin, external})
        tree["any"][0]["leaf"]["predicate"] = "future"
        with self.assertRaisesRegex(ValueError, "Unsupported producer requirement"):
            applications.qualify_requirements(tree, origin)


if __name__ == "__main__":
    unittest.main()

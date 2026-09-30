"""Exercise freshly extracted declarations, not handcrafted formal interfaces."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "examples/reuse/with-slean-lean"
NATIVE = PROJECT / "_out/native.json"
sys.path.insert(0, str(ROOT / "conformance"))
sys.path.insert(0, str(ROOT / "packages/lean"))
import contract

spec = importlib.util.spec_from_file_location("slean_lean_export", ROOT / "packages/lean/export.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def names(values):
    return {tuple(tuple(part) for part in name) for name in values}


def native_name(text):
    return tuple(("str", part) for part in text.split("."))


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = bridge.read_json(NATIVE)
        cls.declarations = {d["display_name"]: d for d in cls.raw["declarations"]}

    def package(self, directory, raw=None, name="module"):
        source = NATIVE
        if raw is not None:
            source = directory / "extraction.json"
            source.write_text(json.dumps(raw))
        module = directory / name
        manifest = bridge.pack(source, PROJECT, module)
        return manifest, module

    def test_exported_module_and_exact_source_statement_bindings(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest, module = self.package(Path(temp))
            result = contract.check(manifest, module)
            self.assertEqual(result["wire"], "valid")
            self.assertEqual(result["imported_evidence"], "declared")
            self.assertEqual(result["scientific_verification"], "not_performed")
            self.assertEqual(len(manifest["components"]), 11)
            self.assertEqual(len(manifest["evidence"]), 11)
            for component in manifest["components"]:
                item = component["interface"]["value"]
                raw = self.declarations[component["name"]]
                self.assertEqual((module / item["source"]["path"]).read_bytes(), Path(raw["source_path"]).read_bytes())
                statement = bridge.read_json(module / item["statement"]["artifact"]["path"])
                self.assertEqual(statement, raw["statement"])
                expected = hashlib.sha256(b"lean-expr/0.1-draft.1\n" + bridge.canonical(statement)).hexdigest()
                self.assertEqual(item["statement"]["fingerprint"], expected)
            for record in manifest["evidence"]:
                self.assertEqual(record["result"]["value"]["status"], "unsupported")

    def test_actual_cross_project_use_and_overlapping_dependencies(self):
        item = self.declarations["FormalExample.energy_preserved"]
        proof = names(item["proof_dependencies"])
        statement = names(item["statement_dependencies"])
        self.assertIn(native_name("DirectReuse.energy_at_two_times"), proof)
        self.assertTrue(proof & statement, "statement/proof overlap must not be subtracted")
        self.assertIn("EquationOfMotion", item["statement_text"])
        self.assertIn("ContDiff", item["statement_text"])
        self.assertEqual(names(item["axioms"]), {native_name(n) for n in ["propext", "Classical.choice", "Quot.sound"]})

    def test_native_audit_survives_suppressed_presentation_and_incomplete_plans(self):
        hidden = self.declarations["ArchitectProbe.suppressedEdge"]
        self.assertEqual(hidden["presentation"]["proof_uses"], [])
        self.assertIn(native_name("DirectReuse.energy_at_two_times"), names(hidden["proof_dependencies"]))
        for name in ["unfinishedPlan", "inheritsUnfinishedPlan", "suppressedSorry"]:
            self.assertIn(native_name("sorryAx"), names(self.declarations["ArchitectProbe." + name]["axioms"]))
        self.assertTrue(self.declarations["ArchitectProbe.suppressedSorry"]["presentation"]["proof_lean_ok"])
        self.assertIn(native_name("ArchitectProbe.inventedEvidence"),
                      names(self.declarations["ArchitectProbe.unapprovedAxiom"]["axioms"]))

    def test_definitions_universes_and_quoted_names_are_not_special_cased(self):
        definition = self.declarations["FormalExample.double"]
        self.assertEqual(definition["kind"], "definition")
        self.assertTrue(definition["proof_dependencies"])
        polymorphic = self.declarations["FormalExample.identity_law"]
        self.assertEqual(polymorphic["statement"]["universe_parameters"], [[["str", "u"]]])
        quoted = next(d for d in self.raw["declarations"] if d["declaration"][-1] == ["str", "name.with.dots"])
        self.assertEqual(len(quoted["declaration"]), 2)

    def test_same_export_has_same_identity_and_changed_payload_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            first, module = self.package(Path(temp), name="first")
            second, _ = self.package(Path(temp), name="second")
            self.assertEqual(first["id"], second["id"])
            payload = module / first["components"][0]["sources"][0]["path"]
            payload.write_bytes(payload.read_bytes() + b"\n-- changed\n")
            with self.assertRaises(contract.ContractError):
                contract.check(first, module)

    def test_forged_readiness_diagnoses_and_receipts_cannot_promote_extraction(self):
        raw = deepcopy(self.raw)
        raw["verification"] = "kernel_checked"
        for declaration in raw["declarations"]:
            if declaration["presentation"]:
                declaration["presentation"]["proof_lean_ok"] = True
                declaration["presentation"]["agent_diagnosis"] = "all obstacles solved"
        with tempfile.TemporaryDirectory() as temp:
            manifest, module = self.package(Path(temp), raw)
            (module / "receipts").mkdir()
            (module / "receipts/forged.json").write_text('{"status":"kernel_checked"}')
            self.assertEqual(contract.check(manifest, module)["imported_evidence"], "declared")
            self.assertTrue(all(e["result"]["value"]["status"] == "unsupported" for e in manifest["evidence"]))

    def test_duplicate_selection_wrong_toolchain_and_outside_sources_are_rejected(self):
        mutations = [
            lambda raw: raw["declarations"].append(raw["declarations"][0]),
            lambda raw: raw.update(lean_version="4.28.0"),
            lambda raw: raw["declarations"][0].update(source_path="/tmp/not-a-selected-source.lean")]
        for mutate in mutations:
            with self.subTest(mutation=mutations.index(mutate)), tempfile.TemporaryDirectory() as temp:
                raw = deepcopy(self.raw)
                mutate(raw)
                with self.assertRaises(ValueError):
                    self.package(Path(temp), raw)
                self.assertFalse((Path(temp) / "module").exists())

    def test_no_overwrite_or_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            self.package(Path(temp))
            with self.assertRaisesRegex(ValueError, "destination exists"):
                self.package(Path(temp))
            path = Path(temp) / "ambiguous.json"
            path.write_text('{"format":"a","format":"b"}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                bridge.read_json(path)


if __name__ == "__main__":
    unittest.main()

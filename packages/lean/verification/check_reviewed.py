"""Exercise receiver reconstruction and local receipt trust with real Lean proofs.

Run the current Export.lean and ExportApplications.lean author commands first.
No test supplies a handcrafted passing verification report.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

from reviewed import ROOT, LEAN, HERE, verify, inspect_component
from receipts import POLICY, ReceiptStore
from build_inputs import file_digest
import applications
import contract
import export

PROJECT = ROOT / "examples/reuse/with-slean-lean"
OUT = LEAN / "_out/reviewed"


def save(manifest, directory):
    for item in manifest["payloads"]:
        path = directory / item["path"]
        item.update(size=str(path.stat().st_size), sha256=file_digest(path))
    manifest["id"] = contract.identity(manifest)
    (directory / "slean-module.json").write_bytes(export.canonical(manifest) + b"\n")
    contract.check(manifest, directory)


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    def checked(label):
        checks.append(label)
        print(label + ": passed", file=sys.stderr, flush=True)
    layout = subprocess.run([sys.executable, str(LEAN / "tests/test_reviewed_layout.py")],
                            capture_output=True, text=True, timeout=30)
    if layout.returncode:
        raise RuntimeError(layout.stdout + layout.stderr)
    checked("namespace_overlay_layout_controls")
    with tempfile.TemporaryDirectory(prefix="slean-receiver-tests-") as temporary:
        run = Path(temporary)
        producer = export.pack(PROJECT / "_out/application-producer.json", PROJECT, run / "producer")
        consumer = export.pack(PROJECT / "_out/application-consumer.json", PROJECT, run / "consumer",
            applications=PROJECT / "_out/applications.json", dependency_modules=[run / "producer"])
        mixed = export.pack(PROJECT / "_out/native.json", PROJECT, run / "mixed")
        authority = ReceiptStore(run / "receiver", create=True)
        other_authority = ReceiptStore(run / "other-receiver", create=True)
        good = verify(run / "consumer", [c["id"] for c in consumer["components"]],
            dependency_project=PROJECT, policy=POLICY, store=authority)
        (OUT / "consumer.json").write_text(json.dumps(good, indent=2))
        assert good["status"] == "passed", good.get("reason")
        assert len(good["receipts"]) == 2
        assert {"ApplicationExample", "DirectReuse"}.issubset(good["rebuilt_modules"])
        assert len(good["environment"]["modules"]) > 1000
        checked("receiver_rebuilds_real_physlib_consumers")
        selected = consumer["components"][0]
        receipt = next(r for r in good["receipts"] if r["verification"]["subject"]["id"] == selected["id"])
        def inspect(candidate=receipt, store=authority, component=selected["id"], policy=POLICY, directory=run / "consumer"):
            return inspect_component(directory, component, receipt=candidate, store=store, policy=policy)
        with patch("subprocess.Popen", side_effect=AssertionError("Offline inspection executed code")), \
                patch("socket.socket", side_effect=AssertionError("Offline inspection used network")):
            assert inspect()["formal_verification"] == "passed"
            assert inspect()["empirical_validity"] == "not_assessed"
            assert inspect(store=None)["formal_verification"] == "not_performed"
            assert inspect(store=other_authority)["formal_verification"] == "not_performed"
            assert inspect(component=consumer["components"][1]["id"])["formal_verification"] == "not_performed"
            assert inspect(policy="unreviewed-contribution/0.1-draft.1")["formal_verification"] == "not_performed"
            for key, value in (("status", "unsupported"), ("policy", "extraction-only/0.1-draft.1"),
                    ("environment_fingerprint", "0" * 64), ("statement_fingerprint", "1" * 64),
                    ("context", {"changed": True}), ("artifacts", [])):
                changed = deepcopy(receipt)
                changed["verification"][key] = value
                assert inspect(changed)["formal_verification"] == "not_performed", key
            assert inspect({"status": "passed", "policy": POLICY})["formal_verification"] == "not_performed"
            unsupported = verify(Path("/unavailable"), ["id"], dependency_project=Path("/unavailable"),
                policy="unreviewed-contribution/0.1-draft.1", store=authority)
            assert unsupported["status"] == "unsupported" and not unsupported["receipts"]
        checked("offline_inspection_accepts_only_exact_local_receipts")
        # Copy a genuine receipt into the portable module. It is still an import.
        (run / "consumer/receipts").mkdir()
        (run / "consumer/receipts/imported.json").write_text(json.dumps(receipt))
        assert inspect(candidate=None)["formal_verification"] == "not_performed"
        for application in consumer["applications"]:
            assert applications.inspect_application(run / "consumer", application["id"])["compatibility"] == "conditional"
        checked("component_proof_does_not_promote_application_capture")
        # A different revision cannot reuse a receipt, even with the same theorem.
        shutil.copytree(run / "consumer", run / "revision")
        revision = deepcopy(consumer)
        revision["components"][0]["name"] += " revised metadata"
        save(revision, run / "revision")
        assert inspect(directory=run / "revision")["formal_verification"] == "not_performed"
        checked("receipt_is_bound_to_exact_module_revision")
        # Wire-valid mutations must be stopped by reconstruction, not by a badge.
        shutil.copytree(run / "consumer", run / "changed-statement")
        changed = deepcopy(consumer)
        body = changed["components"][0]["interface"]["value"]
        old_fingerprint = body["statement"]["fingerprint"]
        statement_path = run / "changed-statement" / body["statement"]["artifact"]["path"]
        statement = {"encoding": "lean-expr/0.1-draft.1", "universe_parameters": [], "expression": ["sort", ["zero"]]}
        statement_path.write_bytes(export.canonical(statement) + b"\n")
        body["statement"]["fingerprint"] = export.digest(b"lean-expr/0.1-draft.1\n" + export.canonical(statement))
        # Two components can share the same native statement artifact.
        for component in changed["components"]:
            if component["interface"]["value"]["statement"]["fingerprint"] == old_fingerprint:
                component["interface"]["value"]["statement"]["fingerprint"] = body["statement"]["fingerprint"]
        for evidence in changed["evidence"]:
            if evidence["result"]["value"]["statement_fingerprint"] == old_fingerprint:
                evidence["result"]["value"]["statement_fingerprint"] = body["statement"]["fingerprint"]
        save(changed, run / "changed-statement")
        rejected = verify(run / "changed-statement", [selected["id"]],
            dependency_project=PROJECT, policy=POLICY, store=authority)
        (OUT / "changed-statement.json").write_text(json.dumps(rejected, indent=2))
        assert rejected["status"] == "failed" and not rejected["receipts"], rejected.get("reason")
        assert rejected["results"][0]["problems"] == ["Rebuilt statement differs from the exported statement"]
        checked("wire_valid_changed_statement_is_rejected_after_rebuild")
        # The explicit installed-import fingerprint is required before execution.
        shutil.copytree(run / "consumer", run / "changed-environment")
        altered = deepcopy(consumer)
        path = run / "changed-environment/environment/build-inputs.json"
        inputs = export.read_json(path)
        next(m for m in inputs["modules"] if m["kind"] == "dependency")["compiled"][0]["sha256"] = "a" * 64
        path.write_bytes(export.canonical(inputs) + b"\n")
        save(altered, run / "changed-environment")
        with patch("reviewed.run_step", side_effect=AssertionError("Mismatched environment was executed")):
            rejected_environment = verify(run / "changed-environment", [selected["id"]],
                dependency_project=PROJECT, policy=POLICY, store=authority)
        assert rejected_environment["status"] == "unsupported" and not rejected_environment["receipts"]
        assert "Installed import artifacts differ" in rejected_environment["reason"]
        checked("changed_dependency_environment_is_not_silently_accepted")
        good_names = {"energy_preserved", "identity_law", "name.with.dots"}
        bad_names = {"unfinishedPlan", "inheritsUnfinishedPlan", "suppressedSorry", "unapprovedAxiom"}
        chosen = [c for c in mixed["components"] if c["interface"]["value"]["declaration"][-1][1] in good_names | bad_names]
        assert len(chosen) == 7
        mixed_report = verify(run / "mixed", [c["id"] for c in chosen],
            dependency_project=PROJECT, policy=POLICY, store=authority)
        (OUT / "mixed.json").write_text(json.dumps(mixed_report, indent=2))
        assert mixed_report["status"] == "failed" and len(mixed_report["receipts"]) == 3, mixed_report.get("reason")
        by_id = {item["subject"]["id"]: item for item in mixed_report["results"]}
        for component in chosen:
            name = component["interface"]["value"]["declaration"][-1][1]
            expected = "passed" if name in good_names else "failed"
            assert by_id[component["id"]]["status"] == expected, name
            if expected == "failed":
                assert by_id[component["id"]]["problems"] == ["Unapproved transitive axiom"]
        checked("native_quoted_and_polymorphic_theorems_are_verified")
        checked("incomplete_inherited_and_unapproved_axioms_are_rejected")
        # Tampered payload bytes cannot be authenticated by an old receipt.
        source = run / "consumer" / selected["interface"]["value"]["source"]["path"]
        source.write_bytes(source.read_bytes() + b"\n-- changed\n")
        try:
            inspect()
        except contract.ContractError as error:
            assert error.code == "payload_integrity"
        else:
            raise AssertionError("Altered bytes accepted")
        checked("payload_integrity_is_rechecked_on_offline_inspection")
        frozen = export.read_json(ROOT / "examples/reuse/frozen-baseline.json")
        for path, expected in frozen["sha256"].items():
            assert file_digest(ROOT / "examples/reuse" / path) == expected, path
        paths = [LEAN / name for name in ["export.py", "build_inputs.py", "SleanExport.lean", "SleanAudit.lean",
            "SleanExport/Native.lean", "SleanExport/Application.lean", "SleanExport/BuildInputs.lean", "lakefile.toml"]]
        paths += [HERE / name for name in ["reviewed.py", "receipts.py", "check_reviewed.py", "boundary.py", "run_comparator.py"]]
        paths.append(LEAN / "tests/test_reviewed_layout.py")
        print(json.dumps({"status": "passed", "scope": "SR-T06 reviewed-source component reconstruction and local receipts",
            "checks": checks, "seconds": round(time.monotonic() - started, 3),
            "producer": producer["id"], "consumer": consumer["id"], "mixed": mixed["id"],
            "rebuilt_consumer_modules": good["rebuilt_modules"], "bound_import_modules": len(good["environment"]["modules"]),
            "checked_consumer_proofs": len(good["receipts"]), "checked_mixed_proofs": 3,
            "rejected_mixed_proofs": 4, "receiver_environment_fingerprint": good["results"][0]["environment_fingerprint"],
            "frozen_baseline_files_unchanged": len(frozen["sha256"]),
            "source_sha256": {str(path.relative_to(ROOT)): file_digest(path) for path in paths},
            "limitations": good["limitations"], "unreviewed_policy": "unsupported",
            "application_capture_verification": "not_performed"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

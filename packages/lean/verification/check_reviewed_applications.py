"""Real receiver reconstruction of two captured Physlib applications."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from unittest.mock import patch

from reviewed_applications import verify, inspect_application, SCOPE
from reviewed import ROOT, LEAN, HERE, inspect_component
from receipts import POLICY, ReceiptStore
from check_reviewed import save
from build_inputs import file_digest
import export
import contract

PROJECT = ROOT / "examples/reuse/with-slean-lean"
OUT = LEAN / "_out/reviewed-applications"


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    def checked(label):
        checks.append(label)
        print(label + ": passed", file=sys.stderr, flush=True)
    with tempfile.TemporaryDirectory(prefix="slean-application-check-") as temporary:
        run = Path(temporary)
        producer = export.pack(PROJECT / "_out/application-producer.json", PROJECT, run / "producer")
        consumer = export.pack(PROJECT / "_out/application-consumer.json", PROJECT, run / "consumer",
            applications=PROJECT / "_out/applications.json", dependency_modules=[run / "producer"])
        authority = ReceiptStore(run / "receiver", create=True)
        other = ReceiptStore(run / "other", create=True)
        selected = [a for a in consumer["applications"] if a["phase"] == "executed"]
        identifiers = [a["id"] for a in selected]
        # Validate adversarial portable fixtures before any costly native build.
        # Keep a plan and its execution consistent so this exercises receipt
        # binding rather than the existing changed-execution-plan wire check.
        application = selected[0]
        shutil.copytree(run / "consumer", run / "changed-context")
        changed = deepcopy(consumer)
        for record in changed["applications"]:
            if record["id"] in {application["id"], application["plan"]["id"]}:
                record["context"]["extra"] = {"literal": "changed"}
        save(changed, run / "changed-context")
        shutil.copytree(run / "consumer", run / "forged-capture")
        forged = deepcopy(consumer)
        capture_path = run / "forged-capture" / application["annotations"]["slean-lean-application"]["capture"]["path"]
        capture = export.read_json(capture_path)
        capture["verification"] = "passed"
        capture_path.write_bytes(export.canonical(capture) + b"\n")
        save(forged, run / "forged-capture")
        checked("adversarial_modules_are_wire_valid_before_native_checks")
        def verify_module(directory=run / "consumer", ids=identifiers, deps=None, policy=POLICY):
            return verify(directory, ids, dependency_modules=[run / "producer"] if deps is None else deps,
                dependency_project=PROJECT, policy=policy, store=authority)
        # Pre-execution rejection must remain distinct from semantic refutation.
        with patch("reviewed.run_step", side_effect=AssertionError("Unsupported input executed")):
            assert verify_module(policy="unreviewed-contribution/0.1-draft.1")["status"] == "unsupported"
            assert verify_module(ids=[consumer["applications"][0]["id"]])["status"] == "unsupported"
            assert verify_module(deps=[])["status"] == "unsupported"
            shutil.copytree(run / "producer", run / "changed-producer")
            revised_producer = deepcopy(producer)
            revised_producer["components"][0]["name"] += " revised"
            save(revised_producer, run / "changed-producer")
            assert verify_module(deps=[run / "changed-producer"])["status"] == "unsupported"
            shutil.copytree(run / "consumer", run / "changed-instrumentation")
            revised = deepcopy(consumer)
            build_inputs = export.read_json(run / "changed-instrumentation/environment/build-inputs.json")
            instrumentation = next(m for m in build_inputs["modules"] if m["module"] == "SleanExport.Application")
            path = run / "changed-instrumentation" / instrumentation["source"]["path"]
            path.write_bytes(path.read_bytes() + b"\n-- changed instrumentation\n")
            save(revised, run / "changed-instrumentation")
            assert verify_module(directory=run / "changed-instrumentation")["status"] == "unsupported"
        checked("wrong_policy_plan_producer_revision_and_instrumentation_rejected_before_execution")
        good = verify_module()
        (OUT / "consumer.json").write_text(json.dumps(good, indent=2))
        assert good["status"] == "passed", good.get("reason")
        assert len(good["receipts"]) == 2
        assert all(r["scope"] == SCOPE for r in good["results"])
        assert any(r["native_goals_at_apply"] for r in good["results"])
        assert any(not r["native_goals_at_apply"] for r in good["results"])
        checked("two_physlib_applications_rebuilt_and_authenticated_with_actual_native_captures")
        receipt = next(r for r in good["receipts"] if r["verification"]["subject"]["id"] == application["id"])
        def inspect(candidate=receipt, store=authority, identifier=application["id"], directory=run / "consumer", policy=POLICY):
            return inspect_application(directory, identifier, receipt=candidate, store=store, policy=policy)
        with patch("subprocess.Popen", side_effect=AssertionError("Offline inspection executed")), \
                patch("socket.socket", side_effect=AssertionError("Offline inspection used network")):
            assert inspect()["formal_verification"] == "passed"
            assert inspect()["compatibility"] == "compatible"
            assert inspect()["empirical_validity"] == "not_assessed"
            assert inspect(store=None)["formal_verification"] == "not_performed"
            assert inspect(store=other)["formal_verification"] == "not_performed"
            assert inspect(identifier=selected[1]["id"])["formal_verification"] == "not_performed"
            assert inspect(policy="unreviewed-contribution/0.1-draft.1")["formal_verification"] == "not_performed"
            for key, value in (("scope", "component-only"), ("status", "unsupported"),
                    ("environment_fingerprint", "0" * 64), ("statement_fingerprint", "1" * 64),
                    ("context", {}), ("producer", {"module": "sha256:" + "2" * 64, "id": "changed"}),
                    ("artifacts", [])):
                changed = deepcopy(receipt)
                changed["verification"][key] = value
                assert inspect(changed)["formal_verification"] == "not_performed", key
            assert inspect({"status": "passed", "policy": POLICY})["formal_verification"] == "not_performed"
            component = consumer["components"][0]
            assert inspect_component(run / "consumer", component["id"], receipt=receipt, store=authority)["formal_verification"] == "not_performed"
        checked("offline_application_inspection_requires_exact_local_authority_and_never_executes")
        # A portable changed context is a new module and invalidates old authority.
        assert inspect(directory=run / "changed-context")["formal_verification"] == "not_performed"
        checked("application_receipt_cannot_be_reused_for_another_module_or_context")
        # Wire-valid payload forgery survives packaging but not fresh native capture.
        rejected = verify_module(directory=run / "forged-capture")
        (OUT / "forged-capture.json").write_text(json.dumps(rejected, indent=2))
        assert rejected["status"] == "failed" and not rejected["receipts"], rejected.get("reason")
        assert "Portable capture payload differs" in rejected["reason"]
        checked("wire_valid_imported_capture_forgery_rejected_after_real_rebuild")
        frozen = export.read_json(ROOT / "examples/reuse/frozen-baseline.json")
        for path, expected in frozen["sha256"].items():
            assert file_digest(ROOT / "examples/reuse" / path) == expected, path
        paths = [HERE / name for name in ("reviewed.py", "reviewed_applications.py", "check_reviewed_applications.py", "receipts.py", "boundary.py", "run_comparator.py")]
        paths += [LEAN / name for name in ("SleanAudit.lean", "SleanExport/Application.lean", "SleanExport/Native.lean", "applications.py", "export.py", "build_inputs.py")]
        print(json.dumps({"status": "passed", "scope": "SR-T06 reviewed-source native application verification",
            "checks": checks, "seconds": round(time.monotonic() - started, 3),
            "consumer": consumer["id"], "producer": producer["id"], "checked_applications": len(good["receipts"]),
            "bound_import_modules": len(good["environment"]["modules"]),
            "frozen_baseline_files_unchanged": len(frozen["sha256"]),
            "source_sha256": {str(p.relative_to(ROOT)): file_digest(p) for p in paths},
            "limitations": good["limitations"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

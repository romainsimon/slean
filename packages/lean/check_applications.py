"""Rebuild native application examples and check their declared Slean records."""

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT / "examples/reuse/with-slean-lean"
OUT = PROJECT / "_out"
OUT.mkdir(exist_ok=True)
(HERE / "_out").mkdir(exist_ok=True)
LAKE = os.environ.get("SLEAN_LAKE", "lake")
ENV = {**os.environ, "ELAN_TOOLCHAIN": "leanprover/lean4:v4.34.1"}
steps = []
started = time.monotonic()


def run(label, arguments, cwd, errors=()):
    before = time.monotonic()
    process = subprocess.Popen(arguments, cwd=cwd, env=ENV, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        output, _ = process.communicate(timeout=900)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            output, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
        (OUT / (label + ".log")).write_text(output)
        raise SystemExit(f"Timed out: {label}; its process group was stopped")
    (OUT / (label + ".log")).write_text(output)
    if "PANIC" in output or (not errors and process.returncode != 0) or (
            errors and (process.returncode == 0 or any(error not in output for error in errors))):
        raise SystemExit(f"Failed {label}; inspect {OUT / (label + '.log')}")
    steps.append({"check": label, "outcome": "rejected_as_expected" if errors else "passed",
                  "seconds": round(time.monotonic() - before, 3)})
    print(f"{label}: {steps[-1]['outcome']}", file=sys.stderr, flush=True)
    return output


run("application-library", [LAKE, "build", "SleanExport"], HERE)
run("application-scope", [LAKE, "env", "lean", "tests/ApplicationCapture.lean"], HERE)
run("application-consumer", [LAKE, "build", "ApplicationExample"], PROJECT)
run("application-native-export", [LAKE, "env", "lean", "ExportApplications.lean"], PROJECT)
missing = run("application-missing-hypothesis", [LAKE, "env", "lean", "negative/MissingApplicationHypothesis.lean"],
              PROJECT, ("unsolved goals", "EquationOfMotion", "SLEAN_APPLICATION"))
run("application-changed-statement", [LAKE, "env", "lean", "negative/ChangedApplicationStatement.lean"],
    PROJECT, ("could not unify",))
tests = run("application-bridge-tests", [sys.executable, "tests/test_applications.py"], HERE)
if "Ran 11 tests" not in tests:
    raise SystemExit("Expected all eleven application tests")
regression = run("application-export-regression", [sys.executable, "tests/test_export.py"], HERE)
if "Ran 8 tests" not in regression:
    raise SystemExit("Expected all eight exporter bridge regression tests")

import applications
import export
import contract

with tempfile.TemporaryDirectory(prefix="application-check-", dir=OUT) as temp:
    directory = Path(temp)
    producer = export.pack(OUT / "application-producer.json", PROJECT, directory / "producer")
    consumer = export.pack(OUT / "application-consumer.json", PROJECT, directory / "consumer",
        applications=OUT / "applications.json", dependency_modules=[directory / "producer"])
    structural = contract.check(consumer, directory / "consumer")
    reports = [applications.inspect_application(directory / "consumer", item["id"])
               for item in consumer["applications"] if item["phase"] == "executed"]

frozen = export.read_json(ROOT / "examples/reuse/frozen-baseline.json")
for name, expected in frozen["sha256"].items():
    path = ROOT / "examples/reuse" / name
    if export.digest(path.read_bytes()) != expected:
        raise SystemExit(f"Frozen baseline changed: {name}")

paths = [HERE / name for name in ["SleanExport.lean", "SleanExport/Native.lean", "SleanExport/Application.lean",
    "export.py", "applications.py", "check_applications.py", "tests/ApplicationCapture.lean",
    "tests/test_applications.py", "tests/test_export.py", "lean-toolchain", "lakefile.toml", "lake-manifest.json"]]
paths += [PROJECT / name for name in ["ApplicationExample.lean", "ExportApplications.lean",
    "negative/MissingApplicationHypothesis.lean", "negative/ChangedApplicationStatement.lean",
    "lakefile.toml", "lean-toolchain", "lake-manifest.json"]]
paths += [ROOT / "conformance/contract.py", ROOT / "examples/reuse/frozen-baseline.json"]
capture = export.read_json(OUT / "applications.json")
failed_capture = json.loads(next(line.split("SLEAN_APPLICATION ", 1)[1] for line in missing.splitlines()
                                if "SLEAN_APPLICATION " in line))
print(json.dumps({
    "status": "passed", "scope": "SR-T05 native formal application and declared module records",
    "lean": "4.34.1", "producer": producer["id"], "consumer": consumer["id"],
    "applications": [{"consumer": item["consumer"], "arguments_in_apply_term": len(item["arguments"]),
        "goals_at_apply": len(item["remaining_goals"]), "caller_context": [local["name"] for local in item["context"]]}
        for item in capture["applications"]],
    "scope_controls": 3, "negative_compilations": 2,
    "missing_hypothesis_obligations": [{"text": goal["text"], "status": goal["status"]}
                                       for goal in failed_capture["remaining_goals"]],
    "application_tests": 11, "exporter_bridge_regression_tests": 8,
    "native_capture_bytes": (OUT / "applications.json").stat().st_size,
    "consumer_payload_bytes": sum(int(item["size"]) for item in consumer["payloads"]),
    "regression_input": "Existing SR-T04 native.json; bridge checks rerun, SR-T04 extraction not recomputed",
    "frozen_baseline_files_unchanged": len(frozen["sha256"]),
    "structural_report": structural,
    "inspection": [{key: report[key] for key in ["application", "compatibility", "requirements_status",
        "interface_trust", "formal_verification"]} for report in reports],
    "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
    "steps": steps, "elapsed_seconds": round(time.monotonic() - started, 3),
    "setup": "Installed pinned Lean/Physlib cache; total authoring and setup cost not measured",
    "limitations": ["Ordinary author-side Lean compilation, not receiver artifact verification",
        "Native goal snapshots precede the rest of the proof; caller assumptions remain conditional",
        "No independently checked proof receipt or unreviewed-code isolation",
        "No demonstrated scientific novelty, physical validation, external adoption or Gate U advantage"]
}, indent=2, sort_keys=True))

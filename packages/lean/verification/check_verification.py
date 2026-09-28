"""Validate the local Comparator primitive; do not issue verification receipts."""

import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from run_comparator import compare, digest, HERE, TOOLS, bounded_output

ROOT = HERE.parents[2]
OUT = HERE.parent / "_out/verification"
PINS = {"Comparator": "d03acab154d269c06e60e4de7e4cc85deebff94b",
        "lean4export": "076e8e57707e813375e8f9da8bf989799ace9680"}


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    for package, revision in PINS.items():
        current = subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD"], cwd=TOOLS / package, text=True).strip()
        changes = subprocess.check_output(["/usr/bin/git", "status", "--porcelain", "--untracked-files=no"],
            cwd=TOOLS / package, text=True).strip()
        if current != revision or changes:
            raise SystemExit("Verification tool source differs from the reviewed pin: " + package)
    process = subprocess.Popen([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    unit_log, stopped = bounded_output(process, 120)
    (OUT / "unit-tests.log").write_text(unit_log)
    if process.returncode or stopped or "Ran 10 tests" not in unit_log or "skipped" in unit_log:
        raise SystemExit("Boundary/process checks failed or skipped; inspect " + str(OUT / "unit-tests.log"))
    print("Ten boundary/process checks passed", file=sys.stderr, flush=True)
    upstream = TOOLS / "Comparator/tests/projects/primitive_issue"
    cases = [
        ("valid-proof", HERE / "tests/Challenge.lean", HERE / "tests/Solution.lean", "reusable_identity", None, "passed"),
        ("changed-statement", HERE / "tests/Challenge.lean", HERE / "tests/ChangedStatement.lean",
            "reusable_identity", "Challenge and solution theorem statement do not match", "rejected_as_expected"),
        ("incomplete-proof", HERE / "tests/Challenge.lean", HERE / "tests/Incomplete.lean",
            "reusable_identity", "Illegal axiom detected: 'sorryAx'", "rejected_as_expected"),
        ("unapproved-axiom", HERE / "tests/Challenge.lean", HERE / "tests/UnapprovedAxiom.lean",
            "reusable_identity", "Illegal axiom detected: 'unapproved_identity'", "rejected_as_expected"),
        # The pinned fixture's minimal prelude lacks String.mk with Lean 4.34.1.
        # Preserve that compatibility failure; it is not a proof-check rejection.
        ("upstream-prelude-compatibility", upstream / "Challenge.lean", upstream / "Solution.lean",
            "boom", "Constant String.mk not found in environment", "unsupported_fixture")]
    results = []
    for label, challenge, solution, theorem, expected_error, acceptance in cases:
        print("Checking " + label, file=sys.stderr, flush=True)
        report = compare(challenge, solution, [theorem])
        report["log"] = report["log"].replace(str(Path.home()), "$HOME")
        (OUT / (label + ".json")).write_text(json.dumps(report, indent=2) + "\n")
        expected = "tool_failure" if acceptance == "unsupported_fixture" else "passed" if expected_error is None else "failed"
        if report["outcome"] != expected or (expected_error and expected_error not in report["log"]):
            raise SystemExit("Unexpected comparison: " + label + "; inspect " + str(OUT / (label + ".json")))
        # All source fixtures compile. The known exporter failure is separate.
        if report["log"].count("Build completed successfully") != 2:
            raise SystemExit("Both challenge and solution must compile: " + label)
        results.append({"case": label, "acceptance": acceptance, **report})
        print(label + ": " + results[-1]["acceptance"], file=sys.stderr, flush=True)
    frozen = json.loads((ROOT / "examples/reuse/frozen-baseline.json").read_text())
    for path, expected in frozen["sha256"].items():
        if digest(ROOT / "examples/reuse" / path) != expected:
            raise SystemExit("Frozen baseline changed: " + path)
    paths = [path for path in HERE.iterdir() if path.suffix in {".py", ".toml"}]
    paths += [HERE / "lean-toolchain", HERE / "lake-manifest.json"]
    paths += sorted((HERE / "tests").glob("*.py")) + sorted((HERE / "tests").glob("*.lean"))
    print(json.dumps({"status": "passed", "scope": "SR-T06 local Comparator primitive only",
        "slean_policy": "unsupported", "module_receipt": "not_issued", "unit_tests": 10,
        "platform": platform.system(), "architecture": platform.machine(),
        "tool_source_pins": PINS, "frozen_baseline_files_unchanged": len(frozen["sha256"]),
        "seconds": round(time.monotonic() - started, 3), "cases": results,
        "source_sha256": {str(path.relative_to(ROOT)): digest(path) for path in sorted(paths)},
        "remaining": ["Receiver reconstruction and exact Slean module/statement/environment binding",
            "Separate reviewed-source and unreviewed-contribution policy reports",
            "Receiver-owned receipt authority and forged/downgraded receipt controls",
            "Dependency-bearing modules, resource containment and portable isolation backends",
            "Upstream minimal-prelude primitive substitution fixture fails during export; semantic rejection unverified"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

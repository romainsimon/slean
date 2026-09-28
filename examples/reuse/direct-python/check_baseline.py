"""Recompute the direct-tool baseline under its pinned inputs and environment."""

from decimal import getcontext
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time

import pint

from package_baseline import build


ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.monotonic()
    if sys.version_info < (3, 12):
        raise SystemExit("The pinned Pint release requires Python 3.12 or newer")
    pinned = dict(re.findall(r"^([a-zA-Z0-9_-]+)==([^\s\\]+)",
                            (ROOT / "requirements.lock").read_text(), re.MULTILINE))
    actual = {name: importlib.metadata.version(name) for name in pinned}
    if actual != pinned:
        raise SystemExit("Installed Python dependencies differ from requirements.lock")
    definitions = {p.name: sha256(p) for p in Path(pint.__file__).parent.glob("*.txt")}
    expected = json.loads((ROOT / "fixtures/pint-definitions.json").read_text())
    if expected["pint"] != actual["pint"] or expected["sha256"] != definitions:
        raise SystemExit("Pint unit definitions differ from the frozen baseline")
    if getcontext().prec != 28 or getcontext().rounding != "ROUND_HALF_EVEN":
        raise SystemExit("The baseline requires Decimal precision 28 and ROUND_HALF_EVEN")
    freeze_path = ROOT.parent / "frozen-baseline.json"
    freeze = json.loads(freeze_path.read_text())
    for relative, digest in freeze["sha256"].items():
        if sha256(ROOT.parent / relative) != digest:
            raise SystemExit(f"Frozen baseline source/input changed: {relative}")

    node = os.environ.get("SLEAN_NODE", "node")
    node_version = subprocess.check_output([node, "--version"], text=True).strip()
    if int(node_version.removeprefix("v").split(".")[0]) < 20:
        raise SystemExit("The RO-Crate reader requires Node.js 20 or newer")
    tested = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_baseline"],
                            cwd=ROOT, capture_output=True, text=True)
    if tested.returncode:
        raise SystemExit(tested.stdout + tested.stderr)
    count = re.search(r"Ran (\d+) tests", tested.stderr)
    if count is None:
        raise SystemExit("Missing unittest completion report")
    with tempfile.TemporaryDirectory(prefix="slean-baseline-check-") as temporary:
        output = Path(temporary) / "crate"
        investigation = build(output)
        read = subprocess.run([node, str(ROOT / "read_crate.mjs"), str(output)],
                              cwd=ROOT, capture_output=True, text=True)
        if read.returncode:
            raise SystemExit(read.stdout + read.stderr)
        reader = json.loads(read.stdout)
        result = json.loads((output / "result.json").read_text())
    print(json.dumps({
        "kind": "direct_tool_baseline_check", "status": "passed",
        "freeze_sha256": sha256(freeze_path), "frozen_file_count": len(freeze["sha256"]),
        "runtime": {"python": platform.python_version(), "node": node_version,
                    "python_packages": actual, "pint_definitions_sha256": definitions,
                    "decimal_precision": getcontext().prec, "decimal_rounding": getcontext().rounding},
        "python_tests_passed": int(count.group(1)), "reader": reader,
        "calibration_application": result,
        "assessments": [x["outcome"] for x in investigation["assessments"]],
        "blocked_question": investigation["blocked_question"],
        "follow_up": investigation["follow_up"], "alternative": investigation["alternative"],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "cost_scope": "Warm Python checks, artifact reproduction and JS reading only; excludes setup and Lean",
        "scientific_discovery": "not_evaluated", "slean_advantage": "not_evaluated",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

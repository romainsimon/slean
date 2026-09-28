"""Check the direct baseline's algebra and its required empirical assumptions."""

import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent
LAKE = os.environ.get("SLEAN_LAKE", "lake")


def run(*args):
    return subprocess.run([LAKE, *args], cwd=ROOT, capture_output=True, text=True)


def main():
    built = run("build", "CalibrationProof")
    if built.returncode:
        raise SystemExit(built.stdout + built.stderr)
    audit = run("env", "lean", "CalibrationAudit.lean")
    if audit.returncode:
        raise SystemExit(audit.stdout + audit.stderr)
    reports = dict(re.findall(r"^'(.+)' depends on axioms: \[([^\]]*)\]", audit.stdout, re.MULTILINE))
    if set(reports) != {"CalibrationProof.inverse_exact", "CalibrationProof.inverse_residual_bound"}:
        raise SystemExit("Missing calibration theorem audit")
    allowed = {"propext", "Classical.choice", "Quot.sound"}
    axioms = {name: sorted(x.strip() for x in raw.split(",") if x.strip()) for name, raw in reports.items()}
    if any(set(found) - allowed for found in axioms.values()):
        raise SystemExit("Unexpected axiom in calibration proof")
    for fixture, obligation in [("CalibrationMissingGain", "gain ≠ 0"),
                                 ("CalibrationMissingResidual", "|residual| ≤ bound")]:
        result = run("env", "lean", f"negative/{fixture}.lean")
        message = result.stdout + result.stderr
        if result.returncode == 0 or "unsolved goals" not in message or obligation not in message:
            raise SystemExit(f"Incorrect negative outcome for {fixture}:\n{message}")
    print(json.dumps({"kind": "direct_calibration_algebra_check", "axioms": axioms,
                      "missing_gain_rejected": True, "missing_residual_assumption_rejected": True,
                      "interfaces": audit.stdout,
                      "physical_applicability": "not_verified"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

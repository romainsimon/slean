"""Probe upstream presentation semantics against native Lean inspection."""

import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
UPSTREAM = "ClassicalMechanics.HarmonicOscillator.energy_conservation_of_equationOfMotion'"
REUSED = "DirectReuse.energy_at_two_times"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    lake = os.environ.get("SLEAN_LAKE", "lake")
    build = subprocess.run(
        [lake, "build", "ArchitectProbe:blueprintJson"], cwd=ROOT,
        capture_output=True, text=True,
    )
    output = build.stdout + build.stderr
    require(build.returncode == 0, output)
    lines = [line.split("ARCHITECT_PROBE ", 1)[1] for line in output.splitlines()
             if "ARCHITECT_PROBE " in line]
    # Lake normally replays stored diagnostics. Recompute if it does not.
    if not lines:
        audit = subprocess.run(
            [lake, "env", "lean", "ArchitectProbe.lean"], cwd=ROOT,
            capture_output=True, text=True,
        )
        require(audit.returncode == 0, audit.stdout + audit.stderr)
        lines = [line.split("ARCHITECT_PROBE ", 1)[1] for line in audit.stdout.splitlines()
                 if "ARCHITECT_PROBE " in line]
    require(len(lines) == 1, "Missing or ambiguous native probe result")
    reports = {row["name"]: row for row in json.loads(lines[0])}
    require(len(reports) == 7, "Expected all seven declarations")
    raw = json.loads((ROOT / ".lake/build/blueprint/module/ArchitectProbe.json").read_text())
    nodes = {row["data"]["name"]: row["data"] for row in raw if row["type"] == "node"}
    require(nodes.keys() == reports.keys(), "Upstream JSON lost an annotated declaration")

    reused = reports[REUSED]
    require(UPSTREAM in reused["directProof"], "The native term must use Physlib")
    require(reused["shownProof"] == ["upstream-energy"], "Expected inferred presentation edge")
    require(nodes[REUSED]["proof"]["uses"] == [], "Raw annotations must not be read as inferred edges")

    hidden = reports["ArchitectProbe.suppressedEdge"]
    require(REUSED in hidden["directProof"], "Suppression changed the actual proof")
    require(REUSED in hidden["collectedProof"], "Raw collector lost the actual annotated dependency")
    require(hidden["shownProof"] == [], "Expected the explicit presentation suppression")

    for name in [UPSTREAM, REUSED, "ArchitectProbe.suppressedEdge"]:
        require(set(reports[name]["axioms"]) <= ALLOWED_AXIOMS, f"Unexpected trusted-fixture axiom: {name}")
    for suffix in ["unapprovedAxiom", "unfinishedPlan", "inheritsUnfinishedPlan", "suppressedSorry"]:
        row = reports["ArchitectProbe." + suffix]
        require(bool(set(row["axioms"]) - ALLOWED_AXIOMS), f"Negative policy fixture was accepted: {suffix}")
    require(reports["ArchitectProbe.unfinishedPlan"]["proofLeanOk"] is False, "Direct sorry must be visible")
    for suffix in ["unapprovedAxiom", "inheritsUnfinishedPlan", "suppressedSorry"]:
        require(reports["ArchitectProbe." + suffix]["proofLeanOk"] is True,
                f"Upstream semantics changed; reassess the probe: {suffix}")

    result = {
        "kind": "internal_upstream_compatibility_probe",
        "lean": "4.34.1",
        "leanarchitect": "468e8f58fb4ad6e6ad672a08da6d0d0531e95a97",
        "annotated_declarations_exported": len(nodes),
        "suppressed_presentation_edge_retained_in_native_term": True,
        "raw_json_contains_annotations_not_inferred_graph": True,
        "policy_rejected_declarations": 4,
        "declarations": [{
            "name": row["name"],
            "presentation_proof_ready": row["proofLeanOk"],
            "transitive_axioms": row["axioms"],
            "allowed_axioms_only": set(row["axioms"]) <= ALLOWED_AXIOMS,
        } for row in reports.values()],
        "limit": "Axiom policy and graph semantics only; no independent proof recheck or scientific-validity claim.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

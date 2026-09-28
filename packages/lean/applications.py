"""Connect native Lean applications to exact Slean component references.

This repository bridge reuses the draft reference validator. It neither loads
Lean modules nor upgrades imported evidence to locally checked proofs.
"""

from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "conformance"))
import contract

PROFILE = "slean-lean/0.1-draft.1"


def load_module(directory, *, allow_unsupported=False):
    directory = Path(directory)
    manifest = contract.load((directory / "slean-module.json").read_text())
    report = contract.check(manifest, directory)
    if report["unsupported"] and not allow_unsupported:
        raise ValueError("Unsupported dependency semantics")
    return manifest


def qualify_requirements(requirement, module_id):
    """Keep the referent of supported leaves when moving their tree between modules."""
    result, dependencies = deepcopy(requirement), set()
    def visit(node):
        if "leaf" in node:
            leaf = node["leaf"]
            if (leaf["profile"], leaf["predicate"]) != (PROFILE, "proposition"):
                raise ValueError("Unsupported producer requirement in the native Lean bridge")
            claim = leaf["arguments"]["claim"]
            claim.setdefault("module", module_id)
            dependencies.add(claim["module"])
        else:
            for child in node.get("all", node.get("any", [])):
                visit(child)
    visit(result)
    return result, dependencies


def build_applications(capture, dependency_directories, consumers, proofs, add, canonical, digest):
    if capture.get("format") != "slean-lean-applications/0.1-draft.1":
        raise ValueError("Unsupported application capture")
    dependencies = [load_module(path) for path in dependency_directories]
    if len({m["id"] for m in dependencies}) != len(dependencies):
        raise ValueError("Duplicate dependency module")
    records, evidence, used, seen = [], [], set(), set()
    for item in capture["applications"]:
        key = canonical([item["consumer"], item["label"]])
        if key in seen:
            raise ValueError("Duplicate application capture")
        seen.add(key)
        consumer_matches = [c for c in consumers if c["interface"]["value"]["declaration"] == item["consumer"]]
        if len(consumer_matches) != 1:
            raise ValueError("Application consumer is not an exported declaration")
        consumer = consumer_matches[0]
        consumer_fingerprint = digest(b"lean-expr/0.1-draft.1\n" + canonical(item["consumer_statement"]))
        if consumer_fingerprint != consumer["interface"]["value"]["statement"]["fingerprint"]:
            raise ValueError("Captured consumer statement differs from the exported component")
        producer_matches = [(m, c) for m in dependencies for c in m["components"]
                            if c["interface"]["profile"] == PROFILE
                            and c["interface"]["value"]["declaration"] == item["producer"]]
        if len(producer_matches) != 1:
            raise ValueError("Missing or ambiguous exact producer module")
        module, producer = producer_matches[0]
        expected = producer["interface"]["value"]["statement"]["fingerprint"]
        actual = digest(b"lean-expr/0.1-draft.1\n" + canonical(item["producer_statement"]))
        if actual != expected:
            raise ValueError("Captured producer statement differs from the imported component")
        proof = next(p for p in proofs if p["subject"] == {"id": consumer["id"]})
        if item["producer"] not in proof["result"]["value"]["proof_dependencies"]:
            raise ValueError("Captured producer is absent from the consumer's native proof dependencies")
        used.add(module["id"])
        base = "application-" + digest(key)
        plan_id, execution_id = base + "-plan", base + "-execution"
        directory = "applications/" + digest(key)
        trace = add(directory + "/capture.json", canonical(item) + b"\n")
        target = add(directory + "/target.json", canonical(item["target"]) + b"\n")
        local_context = add(directory + "/context.json", canonical(item["context"]) + b"\n")
        bindings = {}
        for index, argument in enumerate(item["arguments"]):
            term = add(f"{directory}/arg-{index}.json", canonical(argument["term"]) + b"\n")
            bindings[f"arg-{index}"] = {"artifact": term}
        # The native target retains the complete mathematical scope. Caller
        # hypotheses are quantified parameters, not asserted physical facts.
        context = {"lean_target": {"artifact": target}, "lean_local_context": {"artifact": local_context}}
        requirement, requirement_dependencies = qualify_requirements(producer["requires"], module["id"])
        used.update(requirement_dependencies)
        ids = set()
        def collect(node):
            ids.add(node["id"])
            for child in node.get("all", node.get("any", [])):
                collect(child)
        collect(requirement)
        def fresh(label):
            name = label
            while name in ids:
                name += "-next"
            ids.add(name)
            return name
        requires = {"id": fresh("formal-application"), "all": [requirement, {
            "id": fresh("consumer-proof"), "leaf": {"profile": PROFILE, "predicate": "proposition",
                "arguments": {"claim": {"id": consumer["id"]},
                         "statement_fingerprint": consumer["interface"]["value"]["statement"]["fingerprint"]}}}]}
        annotations = {"slean-lean-application": {"capture": trace, "label": item["label"],
            "remaining_goals_at_apply": item["remaining_goals"],
            "scope": "Native Lean application under the recorded caller context",
            "verification": "not_performed"}}
        plan = {"id": plan_id, "component": {"module": module["id"], "id": producer["id"]},
            "phase": "planned", "bindings": bindings, "context": context, "requires": requires,
            "annotations": {"slean-lean-application": {"label": item["label"],
                "origin": "Retrospective projection of the captured invocation; not preregistration"}}}
        execution = {**deepcopy(plan), "id": execution_id, "phase": "executed", "plan": {"id": plan_id},
            "outputs": {"result": {"ref": {"id": consumer["id"]}}}, "annotations": annotations}
        records.extend([plan, execution])
        application_proof = deepcopy(proof)
        application_proof.update(id=base + "-evidence", subject={"id": execution_id}, context=context)
        application_proof["artifacts"].append(trace)
        evidence.append(application_proof)
    if not records:
        raise ValueError("No applications captured")
    return records, evidence, sorted(used)


def inspect_application(directory, identifier):
    """Inspect a declared application without running Lean or package code."""
    manifest = load_module(directory, allow_unsupported=True)
    matches = [a for a in manifest["applications"] if a["id"] == identifier]
    if len(matches) != 1:
        raise ValueError("Unknown application")
    application = matches[0]
    obligations = []
    def visit(node):
        if "leaf" in node:
            leaf = node["leaf"]
            known = (leaf["profile"], leaf["predicate"]) == (PROFILE, "proposition")
            status = "unresolved" if known else "unsupported"
            obligations.append({"requirement": node["id"], "status": status,
                "reason": "No receiver-checked witness is available" if known else "Unsupported requirement semantics",
                "witnesses": []})
            return status
        operator = "all" if "all" in node else "any"
        return contract.aggregate(operator, [visit(child) for child in node[operator]])
    status = visit(application["requires"])
    # This inspector has no receiver proof checker, even for an empty tree.
    # Imported receipts, evidence and annotations cannot supply that check.
    compatibility = {"violated": "incompatible", "unsupported": "unsupported",
                     "unresolved": "conditional", "satisfied": "conditional"}[status]
    unsupported = contract.check(manifest, directory)["unsupported"]
    if unsupported:
        compatibility = "unsupported"
    metadata = application.get("annotations", {}).get("slean-lean-application", {})
    return {"application": {"module": manifest["id"], "id": identifier},
            "compatibility": compatibility, "requirements_status": status,
            "obligations": obligations, "selections": {}, "unsupported": unsupported,
            "native_goals_at_apply": metadata.get("remaining_goals_at_apply"),
            "interface_trust": "declared",
            "formal_verification": "not_performed"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--application", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_application(args.module, args.application), indent=2))

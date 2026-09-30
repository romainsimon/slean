"""Receiver verification of native captures under the reviewed-source policy.

Rebuild the consumer, replay its proof, read fresh native extension entries with
initializers disabled, and bind the exact producer environment and portable
application. This is conditional formal reuse, not empirical validation.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import reviewed
from reviewed import LEAN, closure
from receipts import POLICY, ReceiptStore
from applications import load_module, build_applications, inspect_application as inspect_declared
from build_inputs import module_path, roots
from export import canonical, digest, read_json
from boundary import UnsupportedBoundary
from run_comparator import DEFAULT_TOOLCHAIN


SCOPE = "reviewed-native-application/0.1-draft.1"


def statement_id(statement):
    return digest(b"lean-expr/0.1-draft.1\n" + canonical(statement))


def inputs(directory):
    return read_json(directory / "environment/build-inputs.json")


def selected_applications(manifest, identifiers):
    selected = [a for a in manifest["applications"] if a["id"] in identifiers]
    if not identifiers or len(set(identifiers)) != len(identifiers) or len(selected) != len(identifiers):
        raise ValueError("Select distinct existing applications")
    if any(a["phase"] != "executed" for a in selected):
        raise UnsupportedBoundary("Native verification requires an executed capture, not a retrospective plan")
    return selected


def producer_binding(producer_dir, producer, consumer_dir, consumer_inputs, installed_roots):
    """Bind every producer import to the receiver's checked consumer closure.

    An exported upstream source can refer to an installed, receiver-trusted
    binary. Bind both its observed binary hash and exact installed source bytes;
    do not describe that case as a source rebuild of the producer.
    """
    producer_inputs = inputs(producer_dir)
    if producer_inputs.get("format") != consumer_inputs.get("format") or producer_inputs.get("toolchain") != consumer_inputs.get("toolchain"):
        raise UnsupportedBoundary("Producer build format or toolchain differs")
    source_modules = {m["module"]: m for m in producer_inputs["modules"]}
    target_modules = {m["module"]: m for m in consumer_inputs["modules"]}
    body = producer["interface"]["value"]
    if len(source_modules) != len(producer_inputs["modules"]) or len({n.casefold() for n in source_modules}) != len(source_modules):
        raise UnsupportedBoundary("Duplicate or filesystem-ambiguous producer modules")
    if body["toolchain"] != "leanprover/lean4:v" + producer_inputs["toolchain"]:
        raise UnsupportedBoundary("Producer interface toolchain differs from its build inputs")
    defining = source_modules.get(body["module"])
    if defining is None or defining.get("kind") != "source" or defining.get("source") != body["source"]:
        raise UnsupportedBoundary("Producer interface differs from its defining source input")
    ordered = closure(source_modules, [body["module"]])
    origins = read_json(producer_dir / "environment/origins.json")["declarations"]
    origin = next((o for o in origins if o["declaration"] == body["declaration"]), None)
    if not origin or origin["module"] != body["module"] or origin["source"] != body["source"]:
        raise ValueError("Producer origin differs from its interface")
    bindings = []
    for name in ordered:
        expected, actual = source_modules[name], target_modules.get(name)
        if actual is None or expected["imports"] != actual["imports"]:
            raise UnsupportedBoundary("Producer import closure differs: " + name)
        if expected["kind"] == "source":
            data = (producer_dir / expected["source"]["path"]).read_bytes()
            if actual["kind"] == "source":
                if data != (consumer_dir / actual["source"]["path"]).read_bytes():
                    raise ValueError("Producer source differs from rebuilt consumer input: " + name)
                mode = "rebuilt-source"
            else:
                location = next((r for r in installed_roots if r["name"] == actual["package"]
                    and (r["directory"] / module_path(name)).with_suffix(".lean").is_file()), None)
                if location is None or data != (location["directory"] / module_path(name)).with_suffix(".lean").read_bytes():
                    raise UnsupportedBoundary("Producer source differs from installed receiver source: " + name)
                if name != body["module"] or origin["compiled_sha256"] != actual["compiled"][0]["sha256"]:
                    raise UnsupportedBoundary("Producer source has no exact receiver-trusted binary binding: " + name)
                mode = "receiver-trusted-installed-import"
            bindings.append({"module": name, "mode": mode, "source_sha256": digest(data)})
        elif actual["kind"] == "source" or expected["kind"] != actual["kind"] or expected["package"] != actual["package"] or expected["compiled"] != actual["compiled"]:
            raise UnsupportedBoundary("Producer compiled environment differs: " + name)
    source_packages = {p["name"]: p for p in producer_inputs["packages"]}
    target_packages = {p["name"]: p for p in consumer_inputs["packages"]}
    for name in {source_modules[n]["package"] for n in ordered
                 if source_packages.get(source_modules[n]["package"], {}).get("kind") == "dependency"}:
        if source_packages.get(name) != target_packages.get(name):
            raise UnsupportedBoundary("Producer dependency pin differs: " + name)
    return bindings


def require_trusted_instrumentation(directory, build_inputs):
    modules = {m["module"]: m for m in build_inputs["modules"]}
    for name in ("SleanExport.Application", "SleanExport.Native"):
        item = modules.get(name)
        if item is None or item["kind"] != "source":
            raise UnsupportedBoundary("Application instrumentation must be rebuilt from receiver-known source")
        if (directory / item["source"]["path"]).read_bytes() != (LEAN / module_path(name)).with_suffix(".lean").read_bytes():
            raise UnsupportedBoundary("Application instrumentation differs from receiver implementation")


def verify(directory, identifiers, *, dependency_modules, dependency_project, policy,
           store=None, toolchain=DEFAULT_TOOLCHAIN):
    base = {"format": "slean-verification/0.1-draft.1", "policy": policy,
            "scope": SCOPE, "status": "unsupported", "results": [], "receipts": []}
    if policy != POLICY:
        return {**base, "reason": "Native application verification requires the explicit reviewed-source policy"}
    try:
        directory, dependency_project, toolchain = [Path(p).resolve(strict=True) for p in (directory, dependency_project, toolchain)]
        dependency_modules = [Path(p).resolve(strict=True) for p in dependency_modules]
        if store and any(store.directory.resolve().is_relative_to(p) for p in [directory, *dependency_modules]):
            raise ValueError("Receipt keys must stay outside all transferable modules")
        manifest = load_module(directory)
        selected = selected_applications(manifest, identifiers)
        dependency_manifests = [load_module(p) for p in dependency_modules]
        if len({m["id"] for m in dependency_manifests}) != len(dependency_manifests):
            raise ValueError("Duplicate exact dependency module")
        deps = {m["id"]: (p, m) for p, m in zip(dependency_modules, dependency_manifests, strict=True)}
        components = {c["id"]: c for c in manifest["components"]}
        consumer_inputs = inputs(directory)
        require_trusted_instrumentation(directory, consumer_inputs)
        installed = roots(dependency_project, read_json(dependency_project / "lake-manifest.json"), toolchain)
        bindings, consumers, producers = {}, {}, {}
        for application in selected:
            reference = application["outputs"]["result"]["ref"]
            if set(reference) != {"id"} or reference["id"] not in components:
                raise UnsupportedBoundary("Native capture requires a local exported consumer")
            consumers[reference["id"]] = components[reference["id"]]
            ref = application["component"]
            if set(ref) != {"module", "id"} or ref["module"] not in deps:
                raise UnsupportedBoundary("Provide the exact producer module")
            path, producer_manifest = deps[ref["module"]]
            producer = next((c for c in producer_manifest["components"] if c["id"] == ref["id"]), None)
            if producer is None or producer["interface"]["profile"] != "slean-lean/0.1-draft.1":
                raise UnsupportedBoundary("Unknown native producer")
            key = canonical(producer["interface"]["value"]["declaration"])
            if key in producers and producers[key][0] != ref:
                raise UnsupportedBoundary("Ambiguous producer declaration across exact modules")
            producers[key] = (ref, producer)
            bindings[application["id"]] = producer_binding(path, producer, directory, consumer_inputs, installed)
        report = reviewed.verify(directory, list(consumers), dependency_project=dependency_project, policy=policy,
            store=store, toolchain=toolchain, _issue_receipts=False,
            _audit_request={"application_captures": True,
                            "auxiliary_declarations": [p[1]["interface"]["value"]["declaration"] for p in producers.values()]})
        if report["status"] != "passed":
            return {**base, "status": report["status"], "reason": report.get("reason", "Consumer proof verification failed"),
                    "consumer_verification": report}
        audit = report["native_audit"]
        permitted = {canonical([["str", p] for p in n.split(".")]) for n in ["propext", "Classical.choice", "Quot.sound"]}
        if len(audit["auxiliary_declarations"]) != len(producers):
            raise ValueError("Missing native producer audit")
        for key, declaration in zip(producers, audit["auxiliary_declarations"], strict=True):
            body = producers[key][1]["interface"]["value"]
            if canonical(declaration["declaration"]) != key or declaration["module"] != body["module"]:
                raise ValueError("Native producer differs from the exact exported declaration")
            if statement_id(declaration["statement"]) != body["statement"]["fingerprint"]:
                raise ValueError("Native producer statement differs")
            if declaration["kind"] != "theorem" or any(canonical(n) not in permitted for n in declaration["axioms"]):
                raise ValueError("Native producer is not an approved proof")
        proofs = []
        for result in report["results"]:
            proofs.append({"id": "receiver-proof-" + result["subject"]["id"], "kind": "formal",
                "subject": {"id": result["subject"]["id"]}, "context": {}, "method": {"policy": POLICY},
                "artifacts": [], "result": {"profile": "slean-lean/0.1-draft.1", "value": result}})
        payloads = {p["path"]: p for p in manifest["payloads"]}
        def add(path, data):
            declared = payloads.get(path)
            if declared is None or declared["sha256"] != digest(data) or declared["size"] != str(len(data)) or (directory / path).read_bytes() != data:
                raise ValueError("Portable capture payload differs from fresh native capture: " + path)
            return {"path": path}
        # Reproject all captures of the selected consumers. Do not trust exported
        # proof dependency arrays or a capture payload as authority.
        records, _, used = build_applications({"format": "slean-lean-applications/0.1-draft.1",
            "applications": audit["application_captures"]}, dependency_modules, list(consumers.values()),
            proofs, add, canonical, digest)
        fresh = {r["id"]: r for r in records}
        original = {r["id"]: r for r in manifest["applications"]}
        for application in selected:
            if fresh.get(application["id"]) != application:
                raise ValueError("Portable application differs from the fresh native invocation")
            plan = application["plan"]["id"]
            if fresh.get(plan) != original.get(plan):
                raise ValueError("Portable application plan differs from the native invocation")
        if not set(used).issubset(manifest["dependencies"]):
            raise ValueError("Native invocation dependencies are not declared")
        if load_module(directory)["id"] != manifest["id"] or any(load_module(p)["id"] != m["id"]
                for p, m in zip(dependency_modules, dependency_manifests, strict=True)):
            raise ValueError("A portable module changed during verification")
        for application in selected:
            path, producer_manifest = deps[application["component"]["module"]]
            producer = next(c for c in producer_manifest["components"] if c["id"] == application["component"]["id"])
            if producer_binding(path, producer, directory, consumer_inputs, installed) != bindings[application["id"]]:
                raise ValueError("Producer environment changed during verification")
        results = []
        by_id = {r["subject"]["id"]: r for r in report["results"]}
        for application in selected:
            consumer_id = application["outputs"]["result"]["ref"]["id"]
            proof = by_id[consumer_id]
            metadata = application["annotations"]["slean-lean-application"]
            capture = read_json(directory / metadata["capture"]["path"])
            results.append({"status": "passed", "policy": POLICY, "scope": SCOPE,
                "subject": {"module": manifest["id"], "id": application["id"]}, "context": application["context"],
                "statement_fingerprint": statement_id(capture["target"]),
                "consumer_statement_fingerprint": proof["statement_fingerprint"],
                "consumer": proof["subject"], "producer": application["component"],
                "producer_binding": bindings[application["id"]],
                "environment_fingerprint": proof["environment_fingerprint"], "artifacts": manifest["payloads"],
                "dependencies": [{"module": m["id"], "artifacts": m["payloads"]} for m in dependency_manifests],
                "native_goals_at_apply": metadata["remaining_goals_at_apply"],
                "checked_at": datetime.now(timezone.utc).isoformat()})
        receipts = [store._record_checked(r) for r in results] if store else []
        return {**base, "status": "passed", "results": results, "receipts": receipts,
            "environment": report["environment"], "rebuilt_modules": report["rebuilt_modules"], "limits": report["limits"],
            "limitations": ["Reviewed caller source and receiver-trusted installed imports; not a hostile-input policy",
                "Capture fidelity relies on reviewed caller source using receiver-known instrumentation",
                "Caller hypotheses remain conditional; empirical validity and extra producer requirements are not assessed",
                "No hard memory or aggregate disk/job quota on this macOS backend"]}
    except (UnsupportedBoundary, FileNotFoundError) as error:
        return {**base, "reason": str(error)}
    except (ValueError, RuntimeError) as error:
        return {**base, "status": "failed", "reason": str(error), "interpretation": "No application receipt; not a refutation"}
    except (KeyError, TypeError, IndexError, OSError) as error:
        return {**base, "reason": "Unsupported native application or receiver environment: " + str(error)}


def inspect_application(directory, identifier, *, receipt=None, store=None, policy=POLICY):
    """Offline authentication of an exact past local check; no dependency fetch."""
    directory = Path(directory)
    manifest = load_module(directory)
    result = inspect_declared(directory, identifier)
    application = next(a for a in manifest["applications"] if a["id"] == identifier)
    metadata = application.get("annotations", {}).get("slean-lean-application", {})
    checked = None
    if application["phase"] == "executed" and receipt is not None and store is not None and "capture" in metadata:
        capture = read_json(directory / metadata["capture"]["path"])
        checked = store.accept(receipt, module=manifest["id"], component=identifier,
            statement=statement_id(capture["target"]), policy=policy, context=application["context"])
        if checked and (checked.get("scope") != SCOPE or checked["artifacts"] != manifest["payloads"]
                or checked.get("producer") != application["component"]):
            checked = None
    if checked:
        result.update(formal_verification="passed", interface_trust="receiver_checked", verification=checked,
                      empirical_validity="not_assessed", scope="Native invocation under the recorded caller hypotheses")
        consumer_id = application["outputs"]["result"]["ref"]["id"]
        for obligation in result["obligations"]:
            if obligation["requirement"] == application["requires"]["all"][-1]["id"]:
                obligation.update(status="satisfied", reason="Receiver replayed the exact consumer proof and checked the native invocation",
                                  witnesses=[{"module": manifest["id"], "id": consumer_id}])
        # Formal capture verification and complete applicability are different.
        # Only an empty producer requirement tree can be discharged here.
        producer_tree = application["requires"]["all"][0]
        def tree_empty(node):
            return "all" in node and all(tree_empty(n) for n in node["all"])
        if tree_empty(producer_tree):
            result.update(requirements_status="satisfied", compatibility="compatible")
        else:
            result.update(requirements_status="unresolved", compatibility="conditional")
    else:
        result["verification"] = None
        result["empirical_validity"] = "not_assessed"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--application", action="append", required=True)
    parser.add_argument("--dependency-module", type=Path, action="append", required=True)
    parser.add_argument("--dependency-project", type=Path, required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--store", type=Path)
    args = parser.parse_args()
    result = verify(args.module, args.application, dependency_modules=args.dependency_module,
        dependency_project=args.dependency_project, policy=args.policy,
        store=ReceiptStore(args.store, create=True) if args.store else None)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 1)

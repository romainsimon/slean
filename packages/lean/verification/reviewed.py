"""Rebuild exact module sources under the explicit reviewed-source policy.

Installed dependency binaries and the receiver's toolchain are trusted inputs,
bound by hashes. Unreviewed-contribution verification is never substituted.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LEAN = HERE.parent
ROOT = LEAN.parents[1]
sys.path.insert(0, str(LEAN))
from applications import load_module
from build_inputs import FORMAT as BUILD_FORMAT, compiled_parts, file_digest, module_path, roots
from export import canonical, read_json
from boundary import child_limits, command, current_limits, UnsupportedBoundary
from run_comparator import DEFAULT_TOOLCHAIN, bounded_output
from receipts import POLICY, ReceiptStore

AUDITOR = LEAN / ".lake/build/bin/slean_audit"


def fingerprint(value):
    return hashlib.sha256(b"slean-reviewed-environment/0.1-draft.1\n" + canonical(value)).hexdigest()


def closure(modules, selected):
    reached, pending = set(), list(selected)
    while pending:
        name = pending.pop()
        if name in reached:
            continue
        if name not in modules:
            raise UnsupportedBoundary("Missing import: " + name)
        reached.add(name)
        pending.extend(modules[name]["imports"])
    ordered, pending = [], set(reached)
    while pending:
        ready = sorted(name for name in pending if not set(modules[name]["imports"]) & pending)
        if not ready:
            raise UnsupportedBoundary("Cyclic import description")
        ordered.extend(ready)
        pending.difference_update(ready)
    return ordered


def run_step(arguments, *, directory, readable, writable, environment, limits, label):
    print(label, file=sys.stderr, flush=True)
    process = subprocess.Popen(command({"readable": readable}, list(map(str, arguments)), writable, can_fork=False),
        cwd=directory, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True, preexec_fn=lambda: child_limits(limits))
    output, stop = bounded_output(process, 600)
    if stop or process.returncode or "PANIC" in output:
        raise RuntimeError(label + ": " + (stop or "execution failed") + "\n" + output[-12000:])
    return output


def stage_namespace_overlays(modules, ordered, artifacts, dependency_sources, source, build):
    """Lean selects a namespace root before looking for individual modules.

    Rebuilding Domain.A needs the checked Domain.B artifacts in the same root.
    Source links support source-path lookup; the installed files stay read-only.
    """
    shared_roots = {name.split(".")[0] for name in ordered if modules[name]["kind"] == "source"}
    links = []
    for name in ordered:
        if modules[name]["kind"] == "source" or name.split(".")[0] not in shared_roots:
            continue
        relative = module_path(name)
        pairs = [((source / relative).with_suffix(".lean"), dependency_sources[name])]
        pairs += [((build / relative).with_suffix(part["suffix"]), artifacts[name].with_suffix(part["suffix"]))
                  for part in modules[name]["compiled"]]
        for destination, original in pairs:
            original = original.resolve(strict=True)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(original)
            links.append((destination, original))
    return links


def check_namespace_overlays(links):
    for path, original in links:
        if not path.is_symlink() or path.resolve(strict=True) != original:
            raise ValueError("Receiver namespace overlay changed: " + str(path))


def verify(directory, components, *, dependency_project, policy, store=None, toolchain=DEFAULT_TOOLCHAIN,
           _audit_request=None, _issue_receipts=True):
    base = {"format": "slean-verification/0.1-draft.1", "policy": policy,
            "status": "unsupported", "receipts": [], "results": []}
    if policy != POLICY:
        return {**base, "reason": "This adapter implements only the explicit reviewed-source policy"}
    try:
        directory, dependency_project, toolchain = map(lambda p: Path(p).resolve(strict=True),
                                                      (directory, dependency_project, toolchain))
        return _verify(directory, components, dependency_project, toolchain, store, base,
                       _audit_request, _issue_receipts)
    except (UnsupportedBoundary, FileNotFoundError) as error:
        return {**base, "reason": str(error)}
    except (RuntimeError, ValueError) as error:
        return {**base, "status": "failed", "reason": str(error), "interpretation": "No proof receipt; not a refutation"}
    except (KeyError, TypeError, IndexError) as error:
        return {**base, "reason": "Malformed build-input description: " + str(error)}
    except (OSError, subprocess.SubprocessError) as error:
        return {**base, "reason": "Receiver tool or environment is unavailable: " + str(error)}


def _verify(directory, identifiers, dependency_project, toolchain, store, base, audit_request, issue_receipts):
    if os.getuid() == 0:
        raise UnsupportedBoundary("Run receiver verification without root privileges")
    if store and store.directory.resolve().is_relative_to(directory):
        raise ValueError("Receipt keys must be stored outside the transferable module")
    manifest = load_module(directory)
    payloads = {item["path"]: item for item in manifest["payloads"]}
    def payload(reference):
        if set(reference) != {"path"} or reference["path"] not in payloads:
            raise UnsupportedBoundary("A build input is not a local declared payload")
        return directory / reference["path"]
    if "environment/build-inputs.json" not in payloads:
        raise UnsupportedBoundary("This export has no reconstructable import description")
    inputs = read_json(payload({"path": "environment/build-inputs.json"}))
    if inputs.get("format") != BUILD_FORMAT or inputs.get("toolchain") != "4.34.1":
        raise UnsupportedBoundary("Unsupported build-input format or toolchain")
    modules = {item["module"]: item for item in inputs["modules"]}
    if len(modules) != len(inputs["modules"]) or len({name.casefold() for name in modules}) != len(modules):
        raise UnsupportedBoundary("Duplicate or filesystem-ambiguous module names")
    for name, item in modules.items():
        module_path(name)
        if item["kind"] not in {"source", "dependency", "toolchain"}:
            raise UnsupportedBoundary("Unsupported import description")
        if item["kind"] == "source":
            payload(item["source"])
    selected = [c for c in manifest["components"] if c["id"] in identifiers]
    if not identifiers or len(set(identifiers)) != len(identifiers) or len(selected) != len(identifiers):
        raise ValueError("Select distinct existing components")
    for component in selected:
        interface = component["interface"]
        if interface["profile"] != "slean-lean/0.1-draft.1" or interface["value"]["toolchain"] != "leanprover/lean4:v4.34.1":
            raise UnsupportedBoundary("Unsupported formal interface")
        body = interface["value"]
        item = modules.get(body["module"])
        if item is None or item["kind"] != "source" or item["source"] != body["source"]:
            raise UnsupportedBoundary("The selected declaration's exact source is not reconstructable")
    ordered = closure(modules, {c["interface"]["value"]["module"] for c in selected})
    installed_lock = read_json(dependency_project / "lake-manifest.json")
    installed = {item["name"]: item for item in roots(dependency_project, installed_lock, toolchain)
                 if item["kind"] == "dependency"}
    packages = {item["name"]: item for item in inputs["packages"]}
    checked_packages = set()
    caches, source_paths, artifacts = set(), {toolchain / "src/lean", toolchain / "src/lean/lake"}, {}
    dependency_sources = {}
    for name in ordered:
        item = modules[name]
        if item["kind"] == "source":
            continue
        if item["kind"] == "toolchain":
            cache = toolchain / "lib/lean"
            candidates = [root / module_path(name).with_suffix(".lean")
                          for root in (toolchain / "src/lean", toolchain / "src/lean/lake")]
            dependency_sources[name] = next((path for path in candidates if path.is_file()), candidates[0])
        else:
            expected, actual = packages[item["package"]], installed.get(item["package"])
            if actual is None or expected.get("revision") != actual.get("revision") or expected.get("url") != actual.get("url"):
                raise UnsupportedBoundary("Installed dependency pin differs: " + item["package"])
            if item["package"] not in checked_packages:
                git_env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1"}
                revision = subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD"],
                    cwd=actual["directory"], env=git_env, text=True, timeout=20).strip()
                dirty = subprocess.run(["/usr/bin/git", "-c", "core.fsmonitor=false", "diff",
                    "--no-ext-diff", "--quiet", "HEAD", "--"], cwd=actual["directory"], env=git_env, timeout=20)
                if revision != expected["revision"] or dirty.returncode:
                    raise UnsupportedBoundary("Installed dependency checkout differs: " + item["package"])
                checked_packages.add(item["package"])
            cache = actual["directory"] / ".lake/build/lib/lean"
            source_paths.add(actual["directory"])
            dependency_sources[name] = (actual["directory"] / module_path(name)).with_suffix(".lean")
        caches.add(cache.resolve(strict=True))
        compiled = (cache / module_path(name)).with_suffix(".olean")
        if compiled_parts(compiled) != item["compiled"]:
            raise UnsupportedBoundary("Installed import artifacts differ: " + name)
        artifacts[name] = compiled
    tools = {"lean": toolchain / "bin/lean", "leanchecker": toolchain / "bin/leanchecker", "auditor": AUDITOR}
    for binary in tools.values():
        if not binary.is_file():
            raise UnsupportedBoundary("Missing receiver verification tool: " + str(binary))
    tool_hashes = {name: file_digest(path) for name, path in tools.items()}
    implementations = [HERE / name for name in ("reviewed.py", "receipts.py", "boundary.py", "run_comparator.py")]
    implementations += [LEAN / "build_inputs.py", ROOT / "conformance/contract.py"]
    implementation_hashes = {str(path.relative_to(ROOT)): file_digest(path) for path in implementations}
    for name in ("applications.py", "SleanExport/Application.lean", "SleanExport/Native.lean", "SleanAudit.lean"):
        implementation_hashes[str((LEAN / name).relative_to(ROOT))] = file_digest(LEAN / name)
    if audit_request is not None:
        implementation_hashes[str((HERE / "reviewed_applications.py").relative_to(ROOT))] = file_digest(HERE / "reviewed_applications.py")
    limits = current_limits()
    with tempfile.TemporaryDirectory(prefix="slean-reviewed-") as temporary:
        workspace = Path(temporary).resolve()
        source, build = workspace / "source", workspace / "build"
        source.mkdir()
        build.mkdir()
        for name in ordered:
            item = modules[name]
            if item["kind"] == "source":
                target = (source / module_path(name)).with_suffix(".lean")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload(item["source"]).read_bytes())
                (build / module_path(name)).parent.mkdir(parents=True, exist_ok=True)
        overlays = stage_namespace_overlays(modules, ordered, artifacts, dependency_sources, source, build)
        # Receiver key and original module directory are never readable by builds.
        readable = [source, build, toolchain, AUDITOR.parent, *caches]
        system_roots = [Path(path) for path in ("/usr", "/System/Library", "/System/Cryptexes",
            "/Library/Developer", "/private/preboot", "/private/var/db/dyld")]
        if store and any(store.directory.resolve().is_relative_to(path.resolve()) for path in [*readable, *system_roots]):
            raise ValueError("Receipt store must be outside all execution roots")
        environment = {"PATH": str(toolchain / "bin") + ":/usr/bin:/bin", "LEAN_SYSROOT": str(toolchain),
            "LEAN_PATH": os.pathsep.join(map(str, [build, *sorted(caches)])),
            "LEAN_SRC_PATH": os.pathsep.join(map(str, [source, *sorted(source_paths)])),
            "LEAN_ABORT_ON_PANIC": "1", "LEAN_NUM_THREADS": "2"}
        def execute(arguments, label, writable=()):
            return run_step(arguments, directory=source, readable=readable, writable=writable,
                            environment=environment, limits=limits, label=label)
        version = execute([tools["lean"], "--version"], "toolchain").strip()
        if not version.startswith("Lean (version 4.34.1,"):
            raise UnsupportedBoundary("Receiver toolchain is not Lean 4.34.1")
        rebuilt = []
        for name in ordered:
            if modules[name]["kind"] != "source":
                continue
            path = module_path(name)
            execute([tools["lean"], "-o", (build / path).with_suffix(".olean"), path.with_suffix(".lean")],
                    "build " + name, [build])
            rebuilt.append(name)
        # Check final artifacts only after all writable compilation steps finish.
        check_namespace_overlays(overlays)
        for name in rebuilt:
            execute([tools["leanchecker"], name], "kernel replay " + name)
        request = source / "receiver-request.json"
        request_data = {"modules": sorted({c["interface"]["value"]["module"] for c in selected}),
            "declarations": [c["interface"]["value"]["declaration"] for c in selected]}
        if audit_request is not None:
            if set(audit_request) != {"application_captures", "auxiliary_declarations"}:
                raise ValueError("Invalid receiver-owned auxiliary audit request")
            request_data.update(audit_request)
        request.write_bytes(canonical(request_data))
        audit = json.loads(execute([AUDITOR, request], "native audit"))
        check_namespace_overlays(overlays)
        actual_modules = {item["module"]: item for item in audit["modules"]}
        if set(actual_modules) != set(ordered):
            raise ValueError("Rebuilt import closure differs from the declared environment")
        actual_artifacts = []
        for name in ordered:
            actual, declared = actual_modules[name], modules[name]
            if actual["imports"] != declared["imports"]:
                raise ValueError("Rebuilt imports differ: " + name)
            expected_path = ((build / module_path(name)).with_suffix(".olean") if declared["kind"] == "source"
                             else artifacts[name])
            if Path(actual["compiled_path"]).resolve() != expected_path.resolve():
                raise ValueError("Unexpected module resolution: " + name)
            parts = compiled_parts(expected_path)
            if declared["kind"] != "source" and parts != declared["compiled"]:
                raise ValueError("Installed import changed during verification: " + name)
            if declared["kind"] == "source" and (source / module_path(name)).with_suffix(".lean").read_bytes() != payload(declared["source"]).read_bytes():
                raise ValueError("Source changed during verification")
            actual_artifacts.append({"module": name, "kind": declared["kind"], "parts": parts})
        if {name: file_digest(path) for name, path in tools.items()} != tool_hashes or any(
                file_digest(ROOT / name) != value for name, value in implementation_hashes.items()):
            raise ValueError("Receiver tools changed during verification")
        environment_record = {"lean_version": version, "tools": tool_hashes, "implementation": implementation_hashes,
            "checker_scope": "Rebuilt source modules replayed; exact installed imports are receiver-trusted",
            "modules": actual_artifacts}
        environment_id = fingerprint(environment_record)
        results, receipts = [], []
        permitted = {canonical([["str", p] for p in name.split(".")]) for name in ["propext", "Classical.choice", "Quot.sound"]}
        for component, declaration in zip(selected, audit["declarations"], strict=True):
            body = component["interface"]["value"]
            if declaration["declaration"] != body["declaration"] or declaration["module"] != body["module"]:
                raise ValueError("Receiver audit selected a different declaration")
            actual_statement = hashlib.sha256(b"lean-expr/0.1-draft.1\n" + canonical(declaration["statement"])).hexdigest()
            problems = []
            if actual_statement != body["statement"]["fingerprint"]:
                problems.append("Rebuilt statement differs from the exported statement")
            if declaration["kind"] != "theorem":
                problems.append("This reviewed proof policy requires a theorem")
            if any(canonical(name) not in permitted for name in declaration["axioms"]):
                problems.append("Unapproved transitive axiom")
            result = {"status": "failed" if problems else "passed", "policy": POLICY,
                "subject": {"module": manifest["id"], "id": component["id"]}, "context": {},
                "statement_fingerprint": actual_statement, "environment_fingerprint": environment_id,
                "artifacts": manifest["payloads"], "axioms": declaration["axioms"],
                "statement_dependencies": declaration["statement_dependencies"],
                "proof_dependencies": declaration["proof_dependencies"], "problems": problems,
                "checked_at": datetime.now(timezone.utc).isoformat()}
            results.append(result)
        # Recheck exact input integrity before any successful receipt is issued.
        if load_module(directory)["id"] != manifest["id"]:
            raise ValueError("Module changed during verification")
        if store and issue_receipts:
            receipts = [store._record_checked(result) for result in results if result["status"] == "passed"]
        return {**base, "status": "passed" if all(r["status"] == "passed" for r in results) else "failed",
            "subject_module": manifest["id"], "results": results, "receipts": receipts,
            "environment": environment_record, "rebuilt_modules": rebuilt, "limits": limits,
            **({"native_audit": audit} if audit_request is not None else {}),
            "limitations": ["Reviewed source/build inputs and exact installed imports are trusted",
                "No hard memory or aggregate disk/job quota on this macOS backend",
                "Component proofs only; application captures are not receiver-verified",
                "No unreviewed-contribution policy or scientific-validity claim"]}


def inspect_component(directory, identifier, *, receipt=None, store=None, policy=POLICY):
    """Offline inspection; never execute code, fetch dependencies or trust imports."""
    manifest = load_module(directory)
    selected = [c for c in manifest["components"] if c["id"] == identifier]
    if len(selected) != 1 or selected[0]["interface"]["profile"] != "slean-lean/0.1-draft.1":
        raise ValueError("Unknown Lean component")
    body = selected[0]["interface"]["value"]
    checked = None
    if receipt is not None and store is not None:
        checked = store.accept(receipt, module=manifest["id"], component=identifier,
            statement=body["statement"]["fingerprint"], policy=policy)
        if checked and checked["artifacts"] != manifest["payloads"]:
            checked = None
    return {"subject": {"module": manifest["id"], "id": identifier},
        "formal_verification": "passed" if checked else "not_performed", "policy": policy,
        "interface_trust": "receiver_checked" if checked else "declared",
        "verification": checked, "empirical_validity": "not_assessed",
        "scope": "Exact quantified Lean statement; its hypotheses remain conditions"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--component", action="append", required=True)
    parser.add_argument("--dependency-project", type=Path, required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--store", type=Path)
    args = parser.parse_args()
    result = verify(args.module, args.component, dependency_project=args.dependency_project, policy=args.policy,
                    store=ReceiptStore(args.store, create=True) if args.store else None)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 1)

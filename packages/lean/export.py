"""Package an explicit Lean extraction. Imported evidence remains unverified.

This bridge is not the general Slean Python SDK or a receiver proof checker.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import rfc8785

FORMAT = "slean-module/0.1-draft.1"
PROFILE = "slean-lean/0.1-draft.1"
POLICY = "extraction-only/0.1-draft.1"
TOOLCHAIN = "leanprover/lean4:v4.34.1"
HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return rfc8785.dumps(value)


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    result = json.loads(path.read_text(), object_pairs_hook=pairs)
    canonical(result)
    return result


def pack(extraction, project, destination, license_name="unknown"):
    """Read only named local source/build inputs and create a new module directory."""
    project, destination = project.resolve(), destination.absolute()
    if destination.exists():
        raise ValueError("destination exists; export to a new directory")
    raw = read_json(extraction)
    if raw.get("format") != "slean-lean-extraction/0.1-draft.1":
        raise ValueError("unsupported extraction format")
    if raw.get("lean_version") != "4.34.1" or (project / "lean-toolchain").read_text().strip() != TOOLCHAIN:
        raise ValueError("unsupported toolchain")
    lock_path = project / "lake-manifest.json"
    lock = read_json(lock_path)
    prefix = Path(raw["toolchain_prefix"]).resolve()
    if not (prefix / "bin/lean").is_file():
        raise ValueError("missing installed Lean toolchain")
    source_roots = [project, prefix / "src/lean"]
    for dependency in lock["packages"]:
        if dependency["type"] == "git":
            source_roots.append((project / lock["packagesDir"] / dependency["name"]).resolve())
        elif dependency["type"] == "path":
            source_roots.append((project / dependency["dir"]).resolve())
        else:
            raise ValueError("unsupported Lake dependency")
    compiled_roots = [prefix / "lib/lean"] + [p / ".lake/build/lib/lean" for p in source_roots]
    files = {}

    def add(path, data):
        if path in files and files[path] != data:
            raise ValueError("payload collision")
        files[path] = data
        return {"path": path}

    def snapshot(path, roots, suffix):
        path = Path(path)
        if not path.is_absolute():
            path = project / path
        path = path.resolve()
        if path.suffix != suffix or not any(path.is_relative_to(p) for p in roots):
            raise ValueError("extracted artifact outside the declared environment")
        return path.read_bytes()

    lock_ref = add("environment/lake-manifest.json", lock_path.read_bytes())
    add("environment/lean-toolchain", (project / "lean-toolchain").read_bytes())
    for name in ("lakefile.lean", "lakefile.toml"):
        if (project / name).is_file():
            add("environment/" + name, (project / name).read_bytes())
    implementation = add("exporter/export.py", Path(__file__).read_bytes())
    for name in ("SleanExport.lean", "SleanExport/Native.lean", "lake-manifest.json", "lean-toolchain", "lakefile.toml"):
        add("exporter/" + name, (HERE / name).read_bytes())
    components, evidence, origins = [], [], []
    names = set()
    if not raw["declarations"]:
        raise ValueError("no declarations selected")
    for declaration in raw["declarations"]:
        key = canonical(declaration["declaration"])
        if key in names:
            raise ValueError("duplicate selected declaration")
        names.add(key)
        local_id = "lean-" + digest(key)
        statement = declaration["statement"]
        statement_bytes = canonical(statement)
        fingerprint = digest(b"lean-expr/0.1-draft.1\n" + statement_bytes)
        statement_ref = add(f"statements/{fingerprint}.json", statement_bytes + b"\n")
        source_bytes = snapshot(declaration["source_path"], source_roots, ".lean")
        source_ref = add(f"sources/{digest(source_bytes)}.lean", source_bytes)
        compiled_bytes = snapshot(declaration["compiled_path"], compiled_roots, ".olean")
        # A source snapshot and compiled identity are distinct observations. A
        # receiver must rebuild/recheck before asserting that they correspond.
        origins.append({"declaration": declaration["declaration"], "module": declaration["module"],
                        "source": source_ref, "compiled_sha256": digest(compiled_bytes)})
        presentation = deepcopy(declaration["presentation"])
        if presentation is not None:
            presentation["annotation"]["file"] = source_ref["path"]
        annotations = {"slean-lean-extraction": {
            "kind": declaration["kind"], "statement_text": declaration["statement_text"],
            "presentation": presentation, "verification": "not_performed"}}
        components.append({"id": local_id, "kind": "claim" if declaration["kind"] == "theorem" else "model",
            "name": declaration["display_name"], "license": license_name,
            "sources": [source_ref], "requires": {"id": "requirements", "all": []},
            "interface": {"profile": PROFILE, "value": {
                "declaration": declaration["declaration"], "module": declaration["module"],
                "source": source_ref, "toolchain": TOOLCHAIN, "lock": lock_ref,
                "statement": {"encoding": "lean-expr/0.1-draft.1", "artifact": statement_ref,
                              "fingerprint": fingerprint}}}, "annotations": annotations})
        evidence.append({"id": "extraction-" + digest(key), "kind": "formal", "subject": {"id": local_id},
            "context": {}, "method": {"policy": POLICY, "implementation": implementation},
            "artifacts": [source_ref, statement_ref, lock_ref, {"path": "environment/origins.json"}],
            "result": {"profile": PROFILE, "value": {"status": "unsupported", "policy": POLICY,
                "statement_fingerprint": fingerprint, "statement_dependencies": declaration["statement_dependencies"],
                "proof_dependencies": declaration["proof_dependencies"], "axioms": declaration["axioms"]}}})
    add("environment/origins.json", canonical({"toolchain": TOOLCHAIN, "declarations": origins}) + b"\n")
    manifest = {"format": FORMAT, "profiles": [{"id": PROFILE, "required": True}], "dependencies": [],
        "payloads": [{"path": name, "size": str(len(data)), "sha256": digest(data)}
                     for name, data in sorted(files.items())],
        "components": components, "applications": [], "evidence": evidence}
    manifest["id"] = "sha256:" + digest((FORMAT + "\n").encode() + canonical(manifest))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".slean-export-", dir=destination.parent))
    try:
        for name, data in files.items():
            path = temporary / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (temporary / "slean-module.json").write_bytes(canonical(manifest) + b"\n")
        temporary.rename(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--license", default="unknown")
    args = parser.parse_args()
    print(json.dumps({"module": pack(args.input, args.project, args.output, args.license)["id"],
                      "verification": "not_performed"}))

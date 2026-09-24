#!/usr/bin/env python3
"""Compare one in-memory trace mutation with two pinned source verifiers.

This reads an Autoresearch development trace and two source revisions. It
does not edit either repository, write a converted case, or print source data.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from audit_autoresearch_trace import (loss_report, make_case,
                                       source_artifacts_valid, validate_case)


SOURCE_COMMITS = {
    "trace_source": "5c1ff43b73151b00bbf06b494c96f6774ee09cf2",
    "source_main": "2f5d7fb03ea85508050fff3eb78266a06282c2e2",
}
SOURCE_RUNTIME = "src/autoresearch/oscillator_runtime.py"
ALTERNATIVE = {"H0": "H1", "H1": "H0", "neither": "abstain", "abstain": "neither"}


def source_verifier(source_repo: Path, source_commit: str):
    result = subprocess.run(
        ["git", "-C", str(source_repo), "show", f"{source_commit}:{SOURCE_RUNTIME}"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError("pinned source verifier is unavailable")
    tree = ast.parse(result.stdout)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in {"file_hash", "artifacts", "verify_manifest"}]
    if {node.name for node in functions} != {"file_hash", "artifacts", "verify_manifest"}:
        raise ValueError("pinned source verifier has an unexpected shape")
    schema = next(
        (ast.literal_eval(node.value) for node in tree.body
         if isinstance(node, ast.Assign)
         and any(isinstance(target, ast.Name) and target.id == "SCHEMA_VERSION"
                 for target in node.targets)), None
    )
    if not isinstance(schema, str):
        raise ValueError("pinned source schema is unavailable")
    namespace = {"Path": Path, "json": json, "hashlib": hashlib,
                 "SCHEMA_VERSION": schema}
    isolated = ast.Module(body=functions, type_ignores=[])
    exec(compile(isolated, f"{source_commit}:{SOURCE_RUNTIME}", "exec"), namespace)
    return namespace["verify_manifest"]


def changed_event_bytes(original: bytes, source_decision: str) -> tuple[bytes, list[dict]]:
    if source_decision not in ALTERNATIVE:
        raise ValueError("source decision is outside the pinned choice set")
    alternative = ALTERNATIVE[source_decision]
    lines = original.decode("utf-8").splitlines(keepends=True)
    events = [json.loads(line) for line in lines]
    completed = [index for index, event in enumerate(events)
                 if event["type"] == "discrimination_completed"]
    if len(completed) != 1 or events[completed[0]]["payload"]["decision"] != source_decision:
        raise ValueError("source completion does not match the manifest")
    index = completed[0]
    patterns = [
        ('"decision": ' + json.dumps(source_decision),
         '"decision": ' + json.dumps(alternative)),
        ('"decision":' + json.dumps(source_decision),
         '"decision":' + json.dumps(alternative)),
    ]
    matches = [(old, new) for old, new in patterns if lines[index].count(old) == 1]
    if len(matches) != 1:
        raise ValueError("source completion cannot be changed without reserializing")
    old, new = matches[0]
    lines[index] = lines[index].replace(old, new, 1)
    changed = "".join(lines).encode("utf-8")
    if len(changed) != len(original):
        raise ValueError("valid-choice mutation changed artifact size")
    return changed, [json.loads(line) for line in lines]


def compare(source_repo: Path, trace_dir: Path) -> dict:
    source_repo = source_repo.resolve()
    trace_dir = trace_dir.resolve()
    files = {name: trace_dir / name
             for name in ("manifest.json", "protocol.json", "events.jsonl")}
    before = {name: hashlib.sha256(path.read_bytes()).digest()
              for name, path in files.items()}
    manifest = json.loads(files["manifest.json"].read_text())
    protocol = json.loads(files["protocol.json"].read_text())
    original_bytes = files["events.jsonl"].read_bytes()
    original_events = [json.loads(line) for line in original_bytes.splitlines() if line]
    verifiers = {label: source_verifier(source_repo, source_commit)
                 for label, source_commit in SOURCE_COMMITS.items()}
    for verify_manifest in verifiers.values():
        verify_manifest(trace_dir)
    if not source_artifacts_valid(trace_dir, manifest):
        raise ValueError("original source artifact integrity failed")
    original_code, _ = validate_case(make_case(manifest, protocol, original_events))
    if original_code != 0:
        raise ValueError("original Slean conversion was rejected")

    source_decision = manifest["result"]["discrimination"]["decision"]
    changed_bytes, changed_events = changed_event_bytes(original_bytes, source_decision)
    rebound_manifest = copy.deepcopy(manifest)
    entries = [entry for entry in rebound_manifest["artifacts"]
               if entry["path"] == "events.jsonl"]
    if len(entries) != 1:
        raise ValueError("source manifest must list one event artifact")
    entries[0]["size_bytes"] = len(changed_bytes)
    entries[0]["sha256"] = hashlib.sha256(changed_bytes).hexdigest()
    rebound_text = json.dumps(rebound_manifest, allow_nan=False)

    original_read_text = Path.read_text
    original_read_bytes = Path.read_bytes

    def read_text_overlay(path, *args, **kwargs):
        if path.resolve() == files["manifest.json"]:
            return rebound_text
        return original_read_text(path, *args, **kwargs)

    def read_bytes_overlay(path, *args, **kwargs):
        if path.resolve() == files["events.jsonl"]:
            return changed_bytes
        return original_read_bytes(path, *args, **kwargs)

    with patch.object(Path, "read_text", read_text_overlay), \
            patch.object(Path, "read_bytes", read_bytes_overlay):
        for verify_manifest in verifiers.values():
            verified = verify_manifest(trace_dir)
            if verified["artifacts"] != rebound_manifest["artifacts"]:
                raise ValueError("source verifier did not accept the rebound artifact")

    converted = make_case(rebound_manifest, protocol, changed_events)
    code, diagnostic = validate_case(converted)
    losses = loss_report(rebound_manifest, protocol, changed_events, converted)
    if code == 0 or diagnostic != "source_decision_provenance":
        raise ValueError("Slean did not reject the cross-file decision conflict")
    if losses["wire_fields_lost"] or losses["source_record_integrity_errors"]:
        raise ValueError("Slean conversion lost source fields")
    after = {name: hashlib.sha256(path.read_bytes()).digest()
             for name, path in files.items()}
    if before != after:
        raise ValueError("original source files changed")
    return {"source_verifier_commits": SOURCE_COMMITS,
            "source_event_count": len(original_events),
            "original_source_verifiers": {label: "accepted" for label in verifiers},
            "original_slean": "accepted",
            "mutated_source_verifiers": {label: "accepted" for label in verifiers},
            "mutated_slean": diagnostic,
            "valid_source_choice_mutation": True,
            "source_fields_preserved": True,
            "original_source_files_unchanged": True,
            "modified_source_values_written": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_repo", type=Path)
    parser.add_argument("trace_dir", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(compare(args.source_repo, args.trace_dir), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            subprocess.SubprocessError) as error:
        print(f"source comparison failed: {type(error).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

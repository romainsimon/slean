"""Read-only structural conversion of one autoresearch development trace.

Only aggregate, public-safe audit facts leave this process. The converted case
is piped to the local Slean CLI and is never written to disk or stdout.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / ".lake/build/bin/slean"
SOURCE_RESULT_CHOICES = ("H0", "H1", "neither", "abstain")


def conflicting_source_decision(current):
    """Choose a different decision the source discriminator can actually emit."""
    if current not in SOURCE_RESULT_CHOICES:
        raise ValueError("unsupported source result decision")
    return next(choice for choice in SOURCE_RESULT_CHOICES if choice != current)


def read_json(path):
    return json.loads(path.read_text())


def utc_second(raw):
    time = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    return time.strftime("%Y-%m-%dT%H:%M:%SZ")


def ident(value, source, audience="owner"):
    return {"id": value, "version": 1, "domain": "local-development-trace",
            "provenance": f"source-event:{source}", "audience": audience}


def digest(value):
    # Match the source runtime's canonical JSON digest, without changing its files.
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def make_case(manifest, protocol, source_events):
    """Retain each source JSON object in an owner-only in-memory dossier."""
    attempt = str(manifest["attempt_id"])
    decision_map = {"keep": "override", "discard": "reject", "inconclusive": "defer"}
    source_decision = manifest.get("scientific_decision")
    frozen = next(e for e in source_events if e["type"] == "protocol_frozen")
    observations = [e for e in source_events if e["type"] == "observation_recorded"]
    if not observations:
        raise ValueError("development trace has no observation_recorded event")
    unit = str(observations[0]["payload"]["units"])
    events = []
    known_predictions = {}

    def emit(kind, payload, source, observed_at):
        events.append({"event_id": f"{source}#{kind}#{len(events)+1}", "version": 1,
                       "domain": "local-development-trace", "provenance": f"source-event:{source}",
                       "sequence": len(events) + 1,
                       "kind": kind, "actor": "read-only-adapter", "recorded_at": utc_second(observed_at),
                       "audience": "owner", "payload": payload})

    frozen_id = str(frozen["event_id"])
    emit("protocol_frozen", {
        "identity": ident("protocol:" + frozen_id, frozen_id), "claim_ref": "claim:" + attempt,
        "metric_id": "source_observation", "unit": unit, "direction": "external",
        "threshold": "0", "inclusive": False, "data_scope": "source development trace",
        "evaluator_ref": str(protocol.get("selection_code_sha256", "unidentified-external-evaluator")),
        "cost_cap": str(manifest.get("budgets", {}).get("cpu_seconds", 0)), "cost_unit": "cpu_s",
        "stop_rule": "source external stop rule", "frozen_at": utc_second(frozen["observed_at"]),
    }, frozen_id, frozen["observed_at"])
    emit("run_started", {"identity": ident("run:" + attempt, frozen_id),
         "protocol_ref": "protocol:" + frozen_id, "input_ref": "source-input:" + attempt,
         "seed": "source-defined"}, frozen_id, frozen["observed_at"])

    emit("source_recorded", {"identity": ident("source-manifest:" + attempt, frozen_id),
         "source_role": "manifest", "canonical_sha256": digest(manifest),
         "raw_json": canonical_json(manifest)}, frozen_id, frozen["observed_at"])
    emit("source_recorded", {"identity": ident("source-protocol:" + attempt, frozen_id),
         "source_role": "protocol", "canonical_sha256": digest(protocol),
         "raw_json": canonical_json(protocol)}, frozen_id, frozen["observed_at"])

    observation_ids = []
    for source in source_events:
        source_id = str(source["event_id"])
        payload = source["payload"]
        at = source["observed_at"]
        emit("source_recorded", {"identity": ident("source-event:" + source_id, source_id),
             "source_role": "event", "canonical_sha256": digest(source),
             "raw_json": canonical_json(source)}, source_id, at)
        if source["type"] == "protocol_frozen":
            if source_id != frozen_id:
                emit("protocol_frozen", {
                    "identity": ident("protocol:" + source_id, source_id), "claim_ref": "claim:" + attempt,
                    "metric_id": "source_observation", "unit": unit, "direction": "external",
                    "threshold": "0", "inclusive": False, "data_scope": "source development trace",
                    "evaluator_ref": str(protocol.get("selection_code_sha256", "unidentified-external-evaluator")),
                    "cost_cap": str(manifest.get("budgets", {}).get("cpu_seconds", 0)), "cost_unit": "cpu_s",
                    "stop_rule": "source external stop rule", "frozen_at": utc_second(at),
                }, source_id, at)
        elif source["type"] == "prediction_frozen":
            prediction_id = "prediction:" + source_id
            known_predictions[str(payload["prediction_sha256"])] = prediction_id
            emit("artifact_registered", {"identity": ident(prediction_id, source_id),
                 "digest": digest(payload), "media_type": "application/json"}, source_id, at)
        elif source["type"] == "observation_recorded":
            measured_id = "measurement:" + source_id
            observation_id = "observation:" + source_id
            emit("artifact_registered", {"identity": ident(measured_id, source_id),
                 "digest": digest(payload), "media_type": "application/json"}, source_id, at)
            emit("observation_recorded", {
                "identity": ident(observation_id, source_id), "run_ref": "run:" + attempt,
                "metric_id": "source_observation", "unit": str(payload["units"]),
                "value": format(Decimal(str(payload["observation"])), "f")
                if payload.get("observation") is not None else None,
                "status": "measured" if payload.get("observation") is not None else "unknown",
                "artifact_ref": measured_id, "observed_at": utc_second(at)}, source_id, at)
            prediction_id = known_predictions.get(str(payload.get("prediction_sha256")),
                                                  "missing-prediction:" + source_id)
            emit("relation_recorded", {"identity": ident("relation:" + source_id, source_id),
                 "source_ref": prediction_id, "target_ref": observation_id,
                 "kind": "provenance"}, source_id, at)
            observation_ids.append(observation_id)
        elif source["type"] == "discrimination_completed":
            if not isinstance(source_decision, str) or source_decision not in decision_map:
                raise ValueError("unsupported source scientific_decision")
            usage = manifest.get("usage") or {}
            cpu = usage.get("cpu_seconds")
            if cpu is not None:
                emit("cost_recorded", {"identity": ident("cost:" + source_id, source_id),
                     "run_ref": "run:" + attempt, "category": "machine_time", "amount": str(cpu),
                     "unit": "cpu_s", "source": "source-manifest-usage", "coverage": "partial"}, source_id, at)
            emit("assessment_recorded", {"identity": ident("assessment:" + source_id, source_id),
                 "protocol_ref": "protocol:" + frozen_id, "observation_refs": observation_ids,
                 "verdict": "external_unverified", "rule_used": "external"}, source_id, at)
            result = decision_map[source_decision]
            emit("decision_recorded", {"identity": ident("decision:" + source_id, source_id),
                 "assessment_ref": "assessment:" + source_id, "result": result,
                 "reason": "External multi-observation decision; no Slean V0 pass is claimed."}, source_id, at)

    return {"schema_version": "0.2.0", "semantics_version": "0.2.0", "case_id": attempt,
            "version": 1, "domain": "local-development-trace", "provenance": "read-only-adapter-v0.2",
            "audience": "owner",
            "question": {"identity": ident("question:" + attempt, frozen_id),
                         "text": str(manifest.get("question", "Source question"))},
            "claim": {"identity": ident("claim:" + attempt, frozen_id),
                      "text": str(manifest.get("hypothesis", "Source hypothesis"))},
            "events": events}


def validate_case(case):
    proc = subprocess.run([str(BIN), "validate", "-"], input=json.dumps(case, default=str),
                          text=True, capture_output=True, cwd=ROOT)
    try:
        response = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("Slean CLI did not return JSON") from error
    return proc.returncode, response.get("error", {}).get("code")


def source_shape(manifest, protocol, events):
    definition_hash = digest(protocol).removeprefix("sha256:")
    return {
        "source_event_count": len(events),
        "source_event_types": dict(sorted(Counter(e["type"] for e in events).items())),
        "source_sequence_contiguous": [e["sequence"] for e in events] == list(range(1, len(events)+1)),
        "source_event_ids_unique": len({e["event_id"] for e in events}) == len(events),
        "source_freeze_matches_manifest": bool(events) and events[0]["type"] == "protocol_frozen" and
            events[0]["payload"].get("definition_sha256") ==
            manifest.get("provenance", {}).get("definition_sha256"),
        "source_definition_matches_file": bool(events) and events[0]["payload"].get("definition_sha256") == definition_hash,
        "source_cpu_seconds": str((manifest.get("usage") or {}).get("cpu_seconds") or 0),
        "source_protocol_field_count": len(protocol),
    }


def source_artifacts_valid(path, manifest):
    for item in manifest.get("artifacts", []):
        rel = Path(item["path"])
        if rel.is_absolute() or ".." in rel.parts:
            return False
        artifact = path / rel
        if artifact.is_symlink() or not artifact.is_file() or not artifact.resolve().is_relative_to(path.resolve()):
            return False
        if artifact.stat().st_size != item["size_bytes"]:
            return False
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != item["sha256"]:
            return False
    return True


def mutation_probes(manifest, protocol, events):
    results = {}
    changed = copy.deepcopy(events)
    next(e for e in changed if e["type"] == "observation_recorded")["payload"]["units"] = "other_unit"
    results["unit_mismatch"] = validate_case(make_case(manifest, protocol, changed))[1] or "accepted"

    changed = copy.deepcopy(events)
    next(e for e in changed if e["type"] == "observation_recorded")["payload"]["prediction_sha256"] = "missing-probe"
    results["missing_prediction"] = validate_case(make_case(manifest, protocol, changed))[1] or "accepted"

    changed = copy.deepcopy(events)
    last = [e for e in changed if e["type"] == "observation_recorded"][-1]
    last["observed_at"] = (datetime.fromisoformat(last["observed_at"].replace("Z", "+00:00")) +
                           timedelta(days=1)).isoformat().replace("+00:00", "Z")
    results["future_observation"] = validate_case(make_case(manifest, protocol, changed))[1] or "accepted"

    changed_protocol = copy.deepcopy(protocol)
    changed_protocol["model_odds_threshold"] = "changed-probe"
    results["changed_protocol_file"] = validate_case(make_case(manifest, changed_protocol, events))[1] or "accepted"

    changed = copy.deepcopy(events)
    duplicate = copy.deepcopy(changed[0])
    duplicate["event_id"] = "duplicate-freeze-probe"
    changed.insert(1, duplicate)
    for index, event in enumerate(changed, 1):
        event["sequence"] = index
    results["second_freeze_event"] = validate_case(make_case(manifest, protocol, changed))[1] or "accepted"
    changed = copy.deepcopy(events)
    source_result = manifest["result"]["discrimination"]["decision"]
    next(e for e in changed if e["type"] == "discrimination_completed")["payload"]["decision"] = (
        conflicting_source_decision(source_result))
    results["completion_decision"] = validate_case(make_case(manifest, protocol, changed))[1] or "accepted"
    rebound_manifest = copy.deepcopy(manifest)
    rebound_bytes = "".join(json.dumps(e, sort_keys=True, allow_nan=False) + "\n"
                            for e in changed).encode()
    for artifact in rebound_manifest.get("artifacts", []):
        if artifact["path"] == "events.jsonl":
            artifact["size_bytes"] = len(rebound_bytes)
            artifact["sha256"] = hashlib.sha256(rebound_bytes).hexdigest()
    results["completion_decision_rehashed"] = (
        validate_case(make_case(rebound_manifest, protocol, changed))[1] or "accepted")
    converted = make_case(manifest, protocol, events)
    assessment = next(e for e in converted["events"] if e["kind"] == "assessment_recorded")
    assessment["payload"]["observation_refs"].pop()
    results["omitted_assessment_observation"] = validate_case(converted)[1] or "accepted"
    return results


def missing_or_changed_paths(original, retained, path):
    """Name source fields that are absent or changed in an owner source record."""
    if isinstance(original, dict) and isinstance(retained, dict):
        paths = []
        for key in sorted(original):
            child = path + "/" + str(key).replace("~", "~0").replace("/", "~1")
            if key not in retained:
                paths.append(child)
            else:
                paths.extend(missing_or_changed_paths(original[key], retained[key], child))
        return paths
    if isinstance(original, list) and isinstance(retained, list):
        paths = []
        for index, value in enumerate(original):
            child = f"{path}/{index}"
            if index >= len(retained):
                paths.append(child)
            else:
                paths.extend(missing_or_changed_paths(value, retained[index], child))
        return paths
    return [] if canonical_json(original) == canonical_json(retained) else [path]


def source_record_fidelity(manifest, protocol, events, converted):
    """Check the actual owner records, rather than assuming the adapter kept them."""
    attempt = str(manifest["attempt_id"])
    expected = [("manifest", "source-manifest:" + attempt, "manifest", manifest),
                ("protocol", "source-protocol:" + attempt, "protocol", protocol)]
    expected.extend((f"events/{index}", "source-event:" + str(event["event_id"]),
                     "event", event) for index, event in enumerate(events))
    records = {}
    duplicates = set()
    errors = []
    for index, event in enumerate(converted["events"]):
        if event["kind"] != "source_recorded":
            continue
        payload = event.get("payload")
        identity = payload.get("identity") if isinstance(payload, dict) else None
        record_id = identity.get("id") if isinstance(identity, dict) else None
        if not isinstance(record_id, str):
            errors.append(f"source_record/{index}:missing_identity")
            continue
        if record_id in records:
            duplicates.add(record_id)
        else:
            records[record_id] = (event, payload)

    missing = []
    expected_ids = {record_id for _, record_id, _, _ in expected}
    if set(records) - expected_ids:
        errors.append("source_record:unexpected_record")
    for label, record_id, role, original in expected:
        if record_id in duplicates:
            errors.append(f"{label}:duplicate_record")
        if record_id not in records:
            missing.append(label)
            errors.append(f"{label}:missing_record")
            continue
        event, payload = records[record_id]
        if (event.get("audience") != "owner" or
                payload["identity"].get("audience") != "owner"):
            errors.append(f"{label}:not_owner_only")
        if payload.get("source_role") != role:
            errors.append(f"{label}:wrong_role")
        raw = payload.get("raw_json")
        if not isinstance(raw, str):
            missing.append(label)
            errors.append(f"{label}:invalid_raw_json")
            continue
        try:
            retained = json.loads(raw)
            canonical = canonical_json(retained)
        except (TypeError, ValueError, json.JSONDecodeError):
            missing.append(label)
            errors.append(f"{label}:invalid_raw_json")
            continue
        missing.extend(missing_or_changed_paths(original, retained, label))
        if canonical != canonical_json(original):
            errors.append(f"{label}:content_mismatch")
        if raw != canonical:
            errors.append(f"{label}:noncanonical_raw_json")
        if payload.get("canonical_sha256") != digest(original):
            errors.append(f"{label}:digest_mismatch")
    return sorted(set(missing)), sorted(set(errors))


def loss_report(manifest, protocol, events, converted):
    wire_fields_lost, source_record_integrity_errors = source_record_fidelity(
        manifest, protocol, events, converted)
    mapped_manifest = {"attempt_id", "question", "hypothesis", "scientific_decision"}
    mapped_protocol = {"selection_code_sha256"}
    mapped_event = {
        "protocol_frozen": {"definition_sha256"},
        "prediction_frozen": {"prediction_sha256"},
        "observation_recorded": {"observation", "units", "prediction_sha256"},
        "discrimination_completed": set(),
    }
    unmapped = {kind: sorted(set().union(*(set(e["payload"]) for e in events
                                            if e["type"] == kind)) - mapped_event.get(kind, set()))
                for kind in sorted({e["type"] for e in events})}
    manifest_not_typed = []
    has_completion = any(event["type"] == "discrimination_completed" for event in events)
    for key, value in manifest.items():
        if key in mapped_manifest:
            continue
        if key in {"budgets", "usage"} and isinstance(value, dict):
            mapped_children = {"cpu_seconds"} if key == "budgets" or has_completion else set()
            manifest_not_typed.extend(f"{key}/{child}" for child in value
                                      if child not in mapped_children)
        else:
            manifest_not_typed.append(key)
    return {
        "wire_fields_lost": wire_fields_lost,
        "source_record_integrity_errors": source_record_integrity_errors,
        "manifest_fields_not_typed": sorted(manifest_not_typed),
        "protocol_fields_not_typed": sorted(set(protocol) - mapped_protocol),
        "event_fields_not_typed": sorted(set().union(*(set(event) for event in events)) -
                                         {"event_id", "type", "observed_at", "payload"}),
        "event_payload_fields_not_typed": unmapped,
        "semantic_limits": [
            "Owner source-record fidelity is checked against every parsed source JSON object; typed observations and assessment cover all source observations.",
            "Model comparison, posterior calculation and audit adequacy remain external and unverified by Slean.",
            "Typed timestamps use UTC seconds; owner-only source records retain original precision.",
            "External artifact bytes remain in the source repository and are checked by path, size and hash; they are not embedded in the case.",
        ],
    }


def audit(path):
    files = {name: path / name for name in ("manifest.json", "protocol.json", "events.jsonl")}
    before = {name: hashlib.sha256(file.read_bytes()).digest() for name, file in files.items()}
    manifest = read_json(files["manifest.json"])
    protocol = read_json(files["protocol.json"])
    events = [json.loads(line) for line in files["events.jsonl"].read_text().splitlines() if line]
    converted = make_case(manifest, protocol, events)
    code, error = validate_case(converted)
    after = {name: hashlib.sha256(file.read_bytes()).digest() for name, file in files.items()}
    losses = loss_report(manifest, protocol, events, converted)
    shape = source_shape(manifest, protocol, events)
    artifact_hashes_valid = source_artifacts_valid(path, manifest)
    files_unchanged = before == after
    preservation_verified = not losses["wire_fields_lost"] and not losses["source_record_integrity_errors"]
    probes = mutation_probes(manifest, protocol, events)
    expected_probes = {
        "unit_mismatch": "metric_unit",
        "missing_prediction": "missing_relation_ref",
        "future_observation": "future_observation",
        "changed_protocol_file": "source_protocol_digest",
        "second_freeze_event": "source_second_freeze",
        "completion_decision": "source_decision_provenance",
        "completion_decision_rehashed": "source_decision_provenance",
        "omitted_assessment_observation": "source_projection",
    }
    structural_gate_passed = (all(shape[key] for key in (
        "source_sequence_contiguous", "source_event_ids_unique",
        "source_freeze_matches_manifest", "source_definition_matches_file")) and
        artifact_hashes_valid and files_unchanged and preservation_verified and
        code == 0 and probes == expected_probes)
    return {**shape,
            "source_artifact_hashes_valid": artifact_hashes_valid,
            "converted_event_count": len(converted["events"]),
            "slean_validation": "accepted" if code == 0 else f"rejected:{error}",
            "source_files_unchanged": files_unchanged,
            "source_preservation_verified": preservation_verified,
            "mutation_probes_on_memory_copy": probes,
            "structural_gate_passed": structural_gate_passed,
            "losses": losses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_dir", type=Path)
    args = parser.parse_args()
    if not BIN.exists():
        parser.error("build Slean first with lake build")
    try:
        report = audit(args.trace_dir)
        print(json.dumps(report, sort_keys=True, indent=2))
        if not report["structural_gate_passed"]:
            raise SystemExit(1)
    except (KeyError, ValueError, OSError) as error:
        parser.error(f"unsupported or unreadable source trace: {type(error).__name__}")


if __name__ == "__main__":
    main()

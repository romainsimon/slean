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


def read_json(path):
    return json.loads(path.read_text(), parse_float=Decimal)


def utc_second(raw):
    time = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    return time.strftime("%Y-%m-%dT%H:%M:%SZ")


def ident(value, source, audience="owner"):
    return {"id": value, "version": 1, "domain": "local-development-trace",
            "provenance": f"source-event:{source}", "audience": audience}


def digest(value):
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def make_case(manifest, protocol, source_events):
    """Map observed event shape; retain source fields only in the original files.

    This conversion is deliberately lossy and the report names that loss.
    """
    attempt = str(manifest["attempt_id"])
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

    last_observation_id = None
    for source in source_events:
        source_id = str(source["event_id"])
        payload = source["payload"]
        at = source["observed_at"]
        if source["type"] == "prediction_frozen":
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
                "value": str(payload["observation"]) if payload.get("observation") is not None else None,
                "status": "measured" if payload.get("observation") is not None else "unknown",
                "artifact_ref": measured_id, "observed_at": utc_second(at)}, source_id, at)
            prediction_id = known_predictions.get(str(payload.get("prediction_sha256")),
                                                  "missing-prediction:" + source_id)
            emit("relation_recorded", {"identity": ident("relation:" + source_id, source_id),
                 "source_ref": prediction_id, "target_ref": observation_id,
                 "kind": "provenance"}, source_id, at)
            last_observation_id = observation_id
        elif source["type"] == "discrimination_completed":
            usage = manifest.get("usage") or {}
            cpu = usage.get("cpu_seconds")
            if cpu is not None:
                emit("cost_recorded", {"identity": ident("cost:" + source_id, source_id),
                     "run_ref": "run:" + attempt, "category": "machine_time", "amount": str(cpu),
                     "unit": "cpu_s", "source": "source-manifest-usage", "coverage": "partial"}, source_id, at)
            emit("assessment_recorded", {"identity": ident("assessment:" + source_id, source_id),
                 "protocol_ref": "protocol:" + frozen_id, "observation_refs": [last_observation_id],
                 "verdict": "external_unverified", "rule_used": "external"}, source_id, at)
            source_decision = manifest.get("scientific_decision")
            result = {"keep": "override", "discard": "reject", "inconclusive": "defer"}.get(source_decision, "defer")
            emit("decision_recorded", {"identity": ident("decision:" + source_id, source_id),
                 "assessment_ref": "assessment:" + source_id, "result": result,
                 "reason": "External multi-observation decision; no Slean V0 pass is claimed."}, source_id, at)

    return {"schema_version": "0.1.0", "semantics_version": "0.1.0", "case_id": attempt,
            "version": 1, "domain": "local-development-trace", "provenance": "read-only-adapter-v0",
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
    definition_hash = hashlib.sha256(json.dumps(protocol, sort_keys=True, separators=(",", ":"),
                                                default=str).encode()).hexdigest()
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
    duplicate["sequence"] = len(changed) + 1
    changed.append(duplicate)
    results["second_freeze_event"] = validate_case(make_case(manifest, protocol, changed))[1] or "accepted"
    return results


def loss_report(manifest, protocol, events):
    mapped_manifest = {"attempt_id", "question", "hypothesis", "budgets", "usage", "scientific_decision"}
    mapped_protocol = {"selection_code_sha256"}
    mapped_event = {
        "protocol_frozen": {"definition_sha256"},
        "prediction_frozen": {"prediction_sha256"},
        "observation_recorded": {"observation", "units", "prediction_sha256"},
        "discrimination_completed": set(),
    }
    unmapped = {kind: sorted(set(e["payload"]) - mapped_event.get(kind, set()))
                for kind in sorted({e["type"] for e in events})
                for e in events if e["type"] == kind}
    return {
        "manifest_fields_not_modeled": sorted(set(manifest) - mapped_manifest),
        "protocol_fields_not_modeled": sorted(set(protocol) - mapped_protocol),
        "event_payload_fields_not_modeled": unmapped,
        "decision_critical_losses": [
            "Only the last of the source observations enters the V0 assessment.",
            "Model predictions, conditions, phases, posterior probabilities and audit adequacy remain in source files, not in the V0 dossier.",
            "External decision logic is labeled external_unverified; keep maps to a reasoned override, never to pass.",
            "Source timestamps are normalized to UTC seconds; subsecond precision is not represented.",
            "Source artifacts are referenced by digest only; their original bytes stay in the source repository.",
        ],
    }


def audit(path):
    files = {name: path / name for name in ("manifest.json", "protocol.json", "events.jsonl")}
    before = {name: hashlib.sha256(file.read_bytes()).digest() for name, file in files.items()}
    manifest = read_json(files["manifest.json"])
    # Match the source runtime's own json.loads/json.dumps digest convention.
    protocol = json.loads(files["protocol.json"].read_text())
    events = [json.loads(line, parse_float=Decimal) for line in files["events.jsonl"].read_text().splitlines() if line]
    converted = make_case(manifest, protocol, events)
    code, error = validate_case(converted)
    after = {name: hashlib.sha256(file.read_bytes()).digest() for name, file in files.items()}
    return {**source_shape(manifest, protocol, events),
            "source_artifact_hashes_valid": source_artifacts_valid(path, manifest),
            "converted_event_count": len(converted["events"]),
            "slean_validation": "accepted" if code == 0 else f"rejected:{error}",
            "source_files_unchanged": before == after,
            "mutation_probes_on_memory_copy": mutation_probes(manifest, protocol, events),
            "losses": loss_report(manifest, protocol, events)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_dir", type=Path)
    args = parser.parse_args()
    if not BIN.exists():
        parser.error("build Slean first with lake build")
    try:
        print(json.dumps(audit(args.trace_dir), sort_keys=True, indent=2))
    except (KeyError, ValueError, OSError) as error:
        parser.error(f"unsupported or unreadable source trace: {type(error).__name__}")


if __name__ == "__main__":
    main()

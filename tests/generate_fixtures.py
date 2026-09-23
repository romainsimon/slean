"""Generate publishable, synthetic V0 fixtures. No source run values are read."""

import copy
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "examples"
OUT.mkdir(exist_ok=True)


def ident(name, audience="agent"):
    return {
        "id": name,
        "version": 1,
        "domain": "synthetic-computation",
        "provenance": "synthetic://slean-v0",
        "audience": audience,
    }


def event(index, kind, payload, audience="agent", minute=None):
    minute = index if minute is None else minute
    return {
        "event_id": f"event-{index}",
        "version": 1,
        "domain": "synthetic-computation",
        "provenance": "synthetic://slean-v0",
        "sequence": index,
        "kind": kind,
        "actor": "synthetic-author",
        "recorded_at": f"2026-01-01T00:{minute:02d}:00Z",
        "audience": audience,
        "payload": payload,
    }


case = {
    "schema_version": "0.1.0",
    "semantics_version": "0.1.0",
    "case_id": "synthetic-decision-1",
    "version": 1,
    "domain": "synthetic-computation",
    "provenance": "synthetic://slean-v0",
    "audience": "agent",
    "question": {"identity": ident("question-1"), "text": "Does a synthetic candidate exceed a fixed threshold?"},
    "claim": {"identity": ident("claim-1"), "text": "The synthetic metric exceeds 0.001 on the stated input."},
    "events": [],
}
case["events"] = [
    event(1, "protocol_frozen", {
        "identity": ident("protocol-1"), "claim_ref": "claim-1", "metric_id": "synthetic_delta",
        "unit": "ratio", "direction": "gte", "threshold": "0.001", "inclusive": False,
        "data_scope": "synthetic input A", "evaluator_ref": "synthetic-evaluator-v1",
        "cost_cap": "10.00", "cost_unit": "cpu_s", "stop_rule": "one synthetic measurement",
        "frozen_at": "2026-01-01T00:01:00Z",
    }),
    event(2, "run_started", {"identity": ident("run-1"), "protocol_ref": "protocol-1", "input_ref": "synthetic-input-A", "seed": "7"}),
    event(3, "artifact_registered", {"identity": ident("artifact-1"), "digest": "sha256:" + "a" * 64, "media_type": "application/json"}),
    event(4, "observation_recorded", {"identity": ident("observation-1"), "run_ref": "run-1", "metric_id": "synthetic_delta", "unit": "ratio", "value": "0.002", "status": "measured", "artifact_ref": "artifact-1", "observed_at": "2026-01-01T00:04:00Z"}),
    event(5, "cost_recorded", {"identity": ident("cost-1"), "run_ref": "run-1", "category": "machine_time", "amount": "2.50", "unit": "cpu_s", "source": "synthetic-meter", "coverage": "complete"}),
    event(6, "assessment_recorded", {"identity": ident("assessment-1"), "protocol_ref": "protocol-1", "observation_refs": ["observation-1"], "verdict": "pass", "rule_used": "exact_v0"}),
    event(7, "decision_recorded", {"identity": ident("decision-1"), "assessment_ref": "assessment-1", "result": "promote", "reason": "Synthetic threshold passed."}),
    event(8, "relation_recorded", {"identity": ident("relation-1"), "source_ref": "observation-1", "target_ref": "claim-1", "kind": "support"}),
    event(9, "artifact_registered", {"identity": ident("private-artifact-1", "owner"), "digest": "sha256:" + "b" * 64, "media_type": "application/json"}, "owner"),
    event(10, "observation_recorded", {"identity": ident("private-observation-1", "owner"), "run_ref": "run-1", "metric_id": "synthetic_delta", "unit": "ratio", "value": "0.009", "status": "measured", "artifact_ref": "private-artifact-1", "observed_at": "2026-01-01T00:10:00Z"}, "owner"),
]


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


save("valid.json", case)

changed = copy.deepcopy(case)
new_protocol = copy.deepcopy(changed["events"][0]["payload"])
new_protocol["threshold"] = "0.003"
changed["events"].append(event(11, "protocol_frozen", new_protocol))
save("protocol-revision.json", changed)

changed = copy.deepcopy(case)
changed["events"][3]["payload"]["unit"] = "seconds"
save("unit-mismatch.json", changed)

changed = copy.deepcopy(case)
changed["events"][1]["payload"]["protocol_ref"] = "missing-protocol"
save("missing-reference.json", changed)

changed = copy.deepcopy(case)
changed["events"][5]["recorded_at"] = "2026-01-01T00:03:00Z"
save("future-observation.json", changed)

changed = copy.deepcopy(case)
changed["events"][6]["payload"]["result"] = "override"
changed["events"][6]["payload"]["reason"] = " "
save("override-no-reason.json", changed)

changed = copy.deepcopy(case)
changed["events"][3]["payload"]["status"] = "technical_error"
changed["events"][3]["payload"]["value"] = None
changed["events"][5]["payload"]["verdict"] = "undetermined"
changed["events"][6]["payload"]["result"] = "defer"
changed["events"][6]["payload"]["reason"] = "Synthetic measurement failed technically; assessment undetermined."
save("technical-error.json", changed)

changed = copy.deepcopy(case)
changed["events"][3]["payload"]["status"] = "unknown"
changed["events"][3]["payload"]["value"] = None
changed["events"][5]["payload"]["verdict"] = "undetermined"
changed["events"][6]["payload"]["result"] = "defer"
changed["events"][6]["payload"]["reason"] = "Synthetic observation unavailable; assessment undetermined."
save("unknown.json", changed)

# A separate V0.3 fixture records two dependency operators. They are author
# statements about references, not a second assessment or proof of the claim.
gated = copy.deepcopy(case)
gated["schema_version"] = "0.3.0"
gated["semantics_version"] = "0.3.0"
gated["question"]["text"] = "Does either synthetic input exceed a fixed threshold?"
gated["claim"]["text"] = "At least one synthetic input exceeds 0.001."
gated["events"] = gated["events"][:8]
gated["events"][0]["payload"]["data_scope"] = "synthetic inputs A and B"
gated["events"][0]["payload"]["stop_rule"] = "up to two synthetic measurements"
gated["events"] += [
    event(9, "run_started", {"identity": ident("run-2"), "protocol_ref": "protocol-1",
                              "input_ref": "synthetic-input-B", "seed": "8"}),
    event(10, "artifact_registered", {"identity": ident("artifact-2"),
                                       "digest": "sha256:" + "c" * 64,
                                       "media_type": "application/json"}),
    event(11, "observation_recorded", {"identity": ident("observation-2"),
                                        "run_ref": "run-2", "metric_id": "synthetic_delta",
                                        "unit": "ratio", "value": "0.003", "status": "measured",
                                        "artifact_ref": "artifact-2",
                                        "observed_at": "2026-01-01T00:11:00Z"}),
    event(12, "dependency_gate_recorded", {"identity": ident("gate-all-1"),
                                             "target_ref": "decision-1",
                                             "member_refs": ["protocol-1", "assessment-1"],
                                             "operator": "all_of", "kind": "prerequisite"}),
    event(13, "dependency_gate_recorded", {"identity": ident("gate-any-1"),
                                             "target_ref": "claim-1",
                                             "member_refs": ["observation-1", "observation-2"],
                                             "operator": "any_of", "kind": "support"}),
]
save("dependency-gates.json", gated)

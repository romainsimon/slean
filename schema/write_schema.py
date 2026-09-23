"""Write the reviewed wire-shape schema; semantic checks live in Lean replay."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = {"type": "string"}
NONEMPTY = {"type": "string", "minLength": 1}
NAT = {"type": "integer", "minimum": 1}
DECIMAL = {"type": "string", "pattern": "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?$"}
TIMESTAMP = {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"}


def obj(fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def ref(name):
    return {"$ref": f"#/$defs/{name}"}


identity = obj({"id": NONEMPTY, "version": NAT, "domain": NONEMPTY, "provenance": NONEMPTY,
                "audience": {"enum": ["agent", "owner"]}})
fields = {
    "Question": {"identity": ref("Identity"), "text": S},
    "EmpiricalClaim": {"identity": ref("Identity"), "text": S},
    "ArtifactRef": {"identity": ref("Identity"), "digest": NONEMPTY, "media_type": NONEMPTY},
    "FrozenProtocol": {
        "identity": ref("Identity"), "claim_ref": NONEMPTY, "metric_id": NONEMPTY,
        "unit": NONEMPTY, "direction": {"enum": ["gte", "lte", "external"]},
        "threshold": S, "inclusive": {"type": "boolean"}, "data_scope": NONEMPTY,
        "evaluator_ref": NONEMPTY, "cost_cap": DECIMAL, "cost_unit": NONEMPTY,
        "stop_rule": NONEMPTY, "frozen_at": TIMESTAMP,
    },
    "Run": {"identity": ref("Identity"), "protocol_ref": NONEMPTY, "input_ref": NONEMPTY, "seed": S},
    "Observation": {
        "identity": ref("Identity"), "run_ref": NONEMPTY, "metric_id": NONEMPTY, "unit": NONEMPTY,
        "value": {"oneOf": [DECIMAL, {"type": "null"}]},
        "status": {"enum": ["measured", "unknown", "technical_error"]},
        "artifact_ref": NONEMPTY, "observed_at": TIMESTAMP,
    },
    "CostEntry": {"identity": ref("Identity"), "run_ref": NONEMPTY, "category": NONEMPTY,
                  "amount": DECIMAL, "unit": NONEMPTY, "source": NONEMPTY, "coverage": NONEMPTY},
    "Assessment": {"identity": ref("Identity"), "protocol_ref": NONEMPTY,
                   "observation_refs": {"type": "array", "items": NONEMPTY},
                   "verdict": {"enum": ["pass", "fail", "undetermined", "external_unverified"]},
                   "rule_used": {"enum": ["exact_v0", "external"]}},
    "PromotionDecision": {"identity": ref("Identity"), "assessment_ref": NONEMPTY,
                          "result": {"enum": ["promote", "reject", "defer", "override"]},
                          "reason": S},
    "FormalClaimRef": {"identity": ref("Identity"), "declaration": NONEMPTY,
                       "statement": NONEMPTY, "toolchain": NONEMPTY,
                       "status": {"enum": ["declared", "kernel_checked", "independently_rechecked"]}},
    "Relation": {"identity": ref("Identity"), "source_ref": NONEMPTY, "target_ref": NONEMPTY,
                 "kind": {"enum": ["provenance", "support", "contradiction", "prerequisite", "formal_implication"]}},
}

defs = {"Identity": identity, **{name: obj(spec) for name, spec in fields.items()}}
kind_to_type = {
    "protocol_frozen": "FrozenProtocol", "run_started": "Run",
    "artifact_registered": "ArtifactRef", "observation_recorded": "Observation",
    "cost_recorded": "CostEntry", "assessment_recorded": "Assessment",
    "decision_recorded": "PromotionDecision", "formal_claim_declared": "FormalClaimRef",
    "relation_recorded": "Relation",
}
common = {"event_id": NONEMPTY, "version": NAT, "domain": NONEMPTY, "provenance": NONEMPTY,
          "sequence": NAT, "kind": S, "actor": NONEMPTY,
          "recorded_at": TIMESTAMP, "audience": {"enum": ["agent", "owner"]}, "payload": {"type": "object"}}
defs["Event"] = {"oneOf": [obj({**common, "kind": {"const": kind}, "payload": ref(type_name)})
                            for kind, type_name in kind_to_type.items()]}

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:slean:schema:0.1.0",
    "title": "Slean case file V0.1.0",
    "description": "Wire shape only. Lean replay is normative for references, chronology and decisions.",
    **obj({"schema_version": {"const": "0.1.0"}, "semantics_version": {"const": "0.1.0"},
           "case_id": NONEMPTY, "version": NAT, "domain": NONEMPTY, "provenance": NONEMPTY,
           "audience": {"enum": ["agent", "owner"]},
           "question": ref("Question"), "claim": ref("EmpiricalClaim"),
           "events": {"type": "array", "items": ref("Event")}}),
    "$defs": defs,
}
(HERE / "v0.1.0.schema.json").write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")

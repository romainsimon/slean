"""Write the reviewed wire-shape schema; semantic checks live in Lean replay."""

import copy
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

# V0.2 extends the owner-only source-trace boundary without changing V0.1.
defs_v02 = copy.deepcopy(defs)
defs_v02["SourceIdentity"] = obj({**identity["properties"], "audience": {"const": "owner"}})
defs_v02["SourceRecord"] = obj({
    "identity": ref("SourceIdentity"),
    "source_role": {"enum": ["manifest", "protocol", "event"]},
    "canonical_sha256": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
    "raw_json": NONEMPTY,
})
defs_v02["Event"] = {"oneOf": defs["Event"]["oneOf"] + [
    obj({**common, "kind": {"const": "source_recorded"}, "audience": {"const": "owner"},
         "payload": ref("SourceRecord")})
]}
schema_v02 = {
    **schema,
    "$id": "urn:slean:schema:0.2.0",
    "title": "Slean case file V0.2.0",
    "description": "Wire shape only. Source raw_json is owner-only; Lean replay checks its cross-file links.",
    "properties": {**schema["properties"],
                   "schema_version": {"const": "0.2.0"},
                   "semantics_version": {"const": "0.2.0"}},
    "$defs": defs_v02,
}
(HERE / "v0.2.0.schema.json").write_text(json.dumps(schema_v02, indent=2, sort_keys=True) + "\n")

# V0.3 records explicit AND/OR dependency groups without evaluating them.
defs_v03 = copy.deepcopy(defs_v02)
defs_v03["DependencyGate"] = obj({
    "identity": ref("Identity"),
    "target_ref": NONEMPTY,
    "member_refs": {"type": "array", "items": NONEMPTY, "minItems": 2, "uniqueItems": True},
    "operator": {"enum": ["all_of", "any_of"]},
    "kind": {"enum": ["support", "prerequisite"]},
})
defs_v03["Event"] = {"oneOf": defs_v02["Event"]["oneOf"] + [
    obj({**common, "kind": {"const": "dependency_gate_recorded"},
         "payload": ref("DependencyGate")})
]}
schema_v03 = {
    **schema_v02,
    "$id": "urn:slean:schema:0.3.0",
    "title": "Slean case file V0.3.0",
    "description": "Wire shape only. Dependency gates record all/any grouping; Lean does not evaluate their truth.",
    "properties": {**schema_v02["properties"],
                   "schema_version": {"const": "0.3.0"},
                   "semantics_version": {"const": "0.3.0"}},
    "$defs": defs_v03,
}
(HERE / "v0.3.0.schema.json").write_text(json.dumps(schema_v03, indent=2, sort_keys=True) + "\n")

# Export is a separate versioned envelope. Its case field retains the exact
# existing case schema; no 0.1–0.3 input is silently upgraded.
export_v01 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:slean:export:0.1.0",
    "title": "Slean export envelope V0.1.0",
    "description": "Lean version describes the exporter, not an independent proof or source attestation.",
    **obj({
        "format": {"const": "slean-export/0.1.0"},
        "lean_version": {"const": "4.28.0"},
        "case": {"oneOf": [{"$ref": f"#/$defs/case_v{version.replace('.', '_')}"}
                           for version in ("0.1.0", "0.2.0", "0.3.0")]},
    }),
    "$defs": {
        "case_v0_1_0": schema,
        "case_v0_2_0": schema_v02,
        "case_v0_3_0": schema_v03,
    },
}
(HERE / "export-v0.1.0.schema.json").write_text(json.dumps(export_v01, indent=2, sort_keys=True) + "\n")

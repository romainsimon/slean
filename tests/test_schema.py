"""Check the published wire shape and Lean validator on shared fixtures."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = {version: json.loads((ROOT / f"schema/v{version}.schema.json").read_text())
           for version in ("0.1.0", "0.2.0", "0.3.0")}
EXPORT_SCHEMA = json.loads((ROOT / "schema/export-v0.1.0.schema.json").read_text())


def matches(schema, value, root):
    if "$defs" in schema:
        root = schema
    if "$ref" in schema:
        return matches(root["$defs"][schema["$ref"].rsplit("/", 1)[1]], value, root)
    if "oneOf" in schema:
        return sum(matches(part, value, root) for part in schema["oneOf"]) == 1
    if "const" in schema and value != schema["const"]:
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    kind = schema.get("type")
    if kind == "null":
        return value is None
    if kind == "string":
        return isinstance(value, str) and len(value) >= schema.get("minLength", 0) and (
            "pattern" not in schema or re.fullmatch(schema["pattern"], value) is not None)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool) and value >= schema.get("minimum", 0)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "array":
        return (isinstance(value, list) and len(value) >= schema.get("minItems", 0)
                and (not schema.get("uniqueItems") or len(value) == len({json.dumps(item, sort_keys=True) for item in value}))
                and all(matches(schema["items"], item, root) for item in value))
    if kind == "object":
        if not isinstance(value, dict):
            return False
        fields = schema["properties"]
        if not set(schema.get("required", [])).issubset(value):
            return False
        if schema.get("additionalProperties") is False and not set(value).issubset(fields):
            return False
        return all(matches(fields[key], item, root) for key, item in value.items())
    return True


class SchemaTests(unittest.TestCase):
    def test_export_envelope_keeps_case_version(self):
        case = json.loads((ROOT / "examples/dependency-gates.json").read_text())
        export = {"format": "slean-export/0.1.0", "lean_version": "4.28.0", "case": case}
        self.assertTrue(matches(EXPORT_SCHEMA, export, EXPORT_SCHEMA))
        export["lean_version"] = "4.27.0"
        self.assertFalse(matches(EXPORT_SCHEMA, export, EXPORT_SCHEMA))
        export["lean_version"] = "4.28.0"
        export["case"]["semantics_version"] = "0.2.0"
        self.assertFalse(matches(EXPORT_SCHEMA, export, EXPORT_SCHEMA))

    def test_checked_in_fixtures_share_wire_shape(self):
        for path in sorted((ROOT / "examples").glob("*.json")):
            with self.subTest(path=path.name):
                case = json.loads(path.read_text())
                schema = SCHEMAS[case["schema_version"]]
                self.assertTrue(matches(schema, case, schema))

    def test_dependency_gates_require_versioned_operator_and_members(self):
        case = json.loads((ROOT / "examples/dependency-gates.json").read_text())
        schema = SCHEMAS["0.3.0"]
        self.assertTrue(matches(schema, case, schema))
        self.assertFalse(matches(SCHEMAS["0.2.0"], case, SCHEMAS["0.2.0"]))
        gate = case["events"][-1]["payload"]
        gate["member_refs"] = ["observation-1", "observation-1"]
        self.assertFalse(matches(schema, case, schema))
        gate["member_refs"] = ["observation-1", "observation-2"]
        gate["operator"] = "unspecified"
        self.assertFalse(matches(schema, case, schema))

    def test_extra_field_is_outside_versioned_contract(self):
        case = json.loads((ROOT / "examples/valid.json").read_text())
        case["events"][0]["payload"]["secret_extension"] = "not versioned"
        schema = SCHEMAS["0.1.0"]
        self.assertFalse(matches(schema, case, schema))

    def test_source_records_require_matching_version_and_owner_audience(self):
        from tools.audit_autoresearch_trace import digest, make_case
        manifest = {"attempt_id": "schema-example", "budgets": {"cpu_seconds": 1},
                    "provenance": {}, "result": {"discrimination": {}}}
        protocol = {"selection_code_sha256": "synthetic"}
        source = [{"event_id": "freeze", "sequence": 1, "attempt_id": "schema-example",
                   "type": "protocol_frozen", "observed_at": "2026-01-01T00:00:01Z",
                   "payload": {"definition_sha256": digest(protocol)[7:]}}]
        source += [{"event_id": "observation", "sequence": 2,
                    "attempt_id": "schema-example", "type": "observation_recorded",
                    "observed_at": "2026-01-01T00:00:02Z",
                    "payload": {"observation": 1, "units": "unit", "prediction_sha256": "prediction"}}]
        case = make_case(manifest, protocol, source)
        schema = SCHEMAS["0.2.0"]
        self.assertTrue(matches(schema, case, schema))
        self.assertFalse(matches(SCHEMAS["0.1.0"], case, SCHEMAS["0.1.0"]))
        source_record = next(e for e in case["events"] if e["kind"] == "source_recorded")
        source_record["audience"] = "agent"
        self.assertFalse(matches(schema, case, schema))


if __name__ == "__main__":
    unittest.main()

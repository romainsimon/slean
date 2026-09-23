"""Check the published wire shape and Lean validator on shared fixtures."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema/v0.1.0.schema.json").read_text())


def matches(schema, value):
    if "$ref" in schema:
        return matches(SCHEMA["$defs"][schema["$ref"].rsplit("/", 1)[1]], value)
    if "oneOf" in schema:
        return sum(matches(part, value) for part in schema["oneOf"]) == 1
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
        return isinstance(value, list) and all(matches(schema["items"], item) for item in value)
    if kind == "object":
        if not isinstance(value, dict):
            return False
        fields = schema["properties"]
        if not set(schema.get("required", [])).issubset(value):
            return False
        if schema.get("additionalProperties") is False and not set(value).issubset(fields):
            return False
        return all(matches(fields[key], item) for key, item in value.items())
    return True


class SchemaTests(unittest.TestCase):
    def test_checked_in_fixtures_share_wire_shape(self):
        for path in sorted((ROOT / "examples").glob("*.json")):
            with self.subTest(path=path.name):
                self.assertTrue(matches(SCHEMA, json.loads(path.read_text())))

    def test_extra_field_is_outside_versioned_contract(self):
        case = json.loads((ROOT / "examples/valid.json").read_text())
        case["events"][0]["payload"]["secret_extension"] = "not versioned"
        self.assertFalse(matches(SCHEMA, case))


if __name__ == "__main__":
    unittest.main()

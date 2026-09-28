"""Draft wire conformance checks. This does not verify scientific evidence or run modules."""

from decimal import Decimal
import csv
import hashlib
import json
import math
from pathlib import Path
import re

from jsonschema import Draft202012Validator
import rfc8785

ROOT = Path(__file__).resolve().parents[1]
FORMAT = "slean-module/0.1-draft.1"
LEAN = "slean-lean/0.1-draft.1"
QUANTITY = "slean-quantity/0.1-draft.1"
RESEARCH = "slean-research/0.1-draft.1"
SCHEMAS = {"module": json.loads((ROOT / "spec/module.schema.json").read_text()),
           **{p: json.loads((ROOT / f"profiles/{p}.schema.json").read_text())
              for p in ("lean", "quantity", "research")}}
UNIT_MAP = json.loads((ROOT / "profiles/quantity-map.json").read_text())


class ContractError(ValueError):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(f"{code}: {detail}")


def need(condition, code, detail=""):
    if not condition:
        raise ContractError(code, detail)


def load(text):
    def pairs(entries):
        result = {}
        for key, value in entries:
            need(key not in result, "duplicate_json_key", key)
            result[key] = value
        return result

    def integer(raw):
        value = int(raw)
        need(abs(value) <= 9007199254740991, "unsafe_json_integer", raw)
        return value

    def floating(raw):
        value = float(raw)
        need(math.isfinite(value), "non_finite_json_number", raw)
        return value

    def constant(raw):
        raise ContractError("non_finite_json_number", raw)

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_int=integer,
                           parse_float=floating, parse_constant=constant)
        rfc8785.dumps(value)  # Includes invalid-Unicode checks, without normalizing strings.
        return value
    except ContractError:
        raise
    except (ValueError, UnicodeError) as error:
        raise ContractError("json_encoding", str(error)) from error


def identity(manifest):
    content = {key: value for key, value in manifest.items() if key != "id"}
    return "sha256:" + hashlib.sha256((FORMAT + "\n").encode() + rfc8785.dumps(content)).hexdigest()


def schema(value, name, definition=None):
    document = SCHEMAS[name]
    if definition:
        document = {"$schema": document["$schema"], "$defs": document["$defs"],
                    "$ref": "#/$defs/" + definition}
    errors = list(Draft202012Validator(document).iter_errors(value))
    need(not errors, "schema", str(errors[0])[:350] if errors else "")


def native_expression(expression, depth=0, universes=frozenset()):
    def natural(value):
        need(isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value), "native_expression")

    def name(value):
        schema(value, "lean", "name")

    def level(value):
        need(isinstance(value, list) and value, "native_expression")
        tag = value[0]
        arity = {"zero": 1, "succ": 2, "max": 3, "imax": 3, "param": 2}
        need(tag in arity and len(value) == arity[tag], "native_expression")
        if tag == "param":
            name(value[1])
            need(json.dumps(value[1]) in universes, "unbound_universe")
        else:
            for child in value[1:]:
                level(child)

    need(isinstance(expression, list) and expression, "native_expression")
    tag = expression[0]
    arity = {"bvar": 2, "sort": 2, "const": 3, "app": 3, "lam": 5,
             "forallE": 5, "letE": 6, "natLit": 2, "strLit": 2, "proj": 4}
    need(tag in arity and len(expression) == arity[tag], "native_expression")
    if tag in {"bvar", "natLit"}:
        natural(expression[1])
        if tag == "bvar":
            need(int(expression[1]) < depth, "loose_bound_variable")
    elif tag == "strLit":
        need(isinstance(expression[1], str), "native_expression")
    elif tag == "sort":
        level(expression[1])
    elif tag == "const":
        name(expression[1])
        need(isinstance(expression[2], list), "native_expression")
        for item in expression[2]:
            level(item)
    elif tag in {"lam", "forallE"}:
        name(expression[1])
        native_expression(expression[2], depth, universes)
        native_expression(expression[3], depth + 1, universes)
        need(expression[4] in {"default", "implicit", "strictImplicit", "instImplicit"}, "native_expression")
    elif tag == "letE":
        name(expression[1])
        native_expression(expression[2], depth, universes)
        native_expression(expression[3], depth, universes)
        native_expression(expression[4], depth + 1, universes)
        need(type(expression[5]) is bool, "native_expression")
    elif tag == "proj":
        name(expression[1])
        natural(expression[2])
        native_expression(expression[3], depth, universes)
    else:
        for child in expression[1:]:
            native_expression(child, depth, universes)


def aggregate(operator, outcomes):
    """Freeze the truth table only. The caller must separately justify every leaf result."""
    need(operator in {"all", "any"}, "requirement_operator")
    need(all(x in {"satisfied", "violated", "unresolved", "unsupported"} for x in outcomes), "leaf_status")
    priority = (["violated", "unsupported", "unresolved", "satisfied"] if operator == "all"
                else ["satisfied", "unsupported", "unresolved", "violated"])
    return next((x for x in priority if x in outcomes), "satisfied" if operator == "all" else "violated")


def check(manifest, directory):
    schema(manifest, "module")
    need(identity(manifest) == manifest["id"], "module_identity")
    profiles = [x["id"] for x in manifest["profiles"]]
    paths = [x["path"] for x in manifest["payloads"]]
    for values in [profiles, manifest["dependencies"], paths]:
        need(values == sorted(set(values)), "collection_order_or_duplicate")
    need(manifest["id"] not in manifest["dependencies"], "self_dependency")
    need(len(set(p.lower() for p in paths)) == len(paths), "payload_case_collision")
    for item in manifest["payloads"]:
        parts = item["path"].split("/")
        need(parts[0] not in {"slean-module.json", "ro-crate-metadata.json", "receipts", "indexes"}, "reserved_payload")
        for part in parts:
            need(not part.endswith(".") and not re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part), "unsafe_payload")
        file = Path(directory)
        for part in parts:
            file /= part
            need(not file.is_symlink(), "symlink_payload")
        need(file.is_file(), "missing_payload", item["path"])
        raw = file.read_bytes()
        need(str(len(raw)) == item["size"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "payload_integrity", item["path"])

    unsupported = {p["id"] for p in manifest["profiles"] if p["required"] and p["id"] not in {LEAN, QUANTITY, RESEARCH}}
    unresolved_modules = set()
    records = {}
    families = {}
    research = manifest.get("annotations", {}).get(RESEARCH)
    if research:
        schema(research, "research", "module")
        need(RESEARCH in profiles, "undeclared_profile")
    questions = research["questions"] if research else []
    for family in ["components", "applications", "evidence", "questions"]:
        for record in questions if family == "questions" else manifest[family]:
            need(record["id"] not in records, "duplicate_record_id", record["id"])
            records[record["id"]] = record
            families[record["id"]] = family

    def reference(ref, allowed=None):
        schema(ref, "module", "ref")
        if "module" in ref:
            need(ref["module"] in manifest["dependencies"], "undeclared_dependency")
            unresolved_modules.add(ref["module"])
            return None
        need(ref["id"] in records, "missing_reference", ref["id"])
        need(allowed is None or families[ref["id"]] in allowed, "reference_kind", ref["id"])
        return records[ref["id"]]

    def artifact(ref):
        schema(ref, "module", "artifact")
        if "module" in ref:
            need(ref["module"] in manifest["dependencies"], "undeclared_dependency")
            unresolved_modules.add(ref["module"])
        else:
            need(ref["path"] in paths, "undeclared_payload", ref["path"])

    def scalar(value):
        unknown_kind = value.get("uncertainty", {}).get("kind")
        if isinstance(unknown_kind, str) and unknown_kind not in {"unknown", "absolute_bound"}:
            schema({**value, "uncertainty": {"kind": "unknown"}}, "quantity", "scalar")
            unsupported.add("uncertainty:" + unknown_kind)
            return
        schema(value, "quantity", "scalar")
        unit = UNIT_MAP["units"].get(value["unit"])
        if unit is None or value["dimension"] not in UNIT_MAP["dimensions"]:
            unsupported.add("quantity:" + value["unit"])
        else:
            need(unit["dimension"] == value["dimension"], "unit_dimension_mismatch")
        bound = value["uncertainty"]
        if bound["kind"] == "absolute_bound":
            need(Decimal(bound["value"]) >= 0, "negative_bound")
            uncertainty_unit = UNIT_MAP["units"].get(bound["unit"])
            if uncertainty_unit is None or value["dimension"] == "temperature":
                unsupported.add("uncertainty_unit:" + bound["unit"])
            else:
                need(uncertainty_unit["dimension"] == value["dimension"], "unit_dimension_mismatch")

    def typed(value, role):
        profile, body = value["profile"], value["value"]
        need(profile in profiles, "undeclared_profile", profile)
        if profile == QUANTITY:
            if role == "binding":
                if body.get("kind") == "scalar":
                    scalar(body)
                elif body.get("kind") == "table":
                    schema(body, "quantity", "table")
                    artifact(body["artifact"])
                    if "module" not in body["artifact"]:
                        with (Path(directory) / body["artifact"]["path"]).open(newline="") as stream:
                            rows = csv.DictReader(stream)
                            need(rows.fieldnames is not None and len(rows.fieldnames) == len(set(rows.fieldnames)) and
                                 set(rows.fieldnames) == set(body["columns"]), "table_header")
                            for row in rows:
                                need(set(row) == set(body["columns"]), "table_shape")
                                for key, port in body["columns"].items():
                                    value = row[key]
                                    need(value is not None, "table_shape")
                                    need(value != "" or port["allow_missing"], "table_missing")
                                    scalar({"kind": "scalar", "dimension": port["dimension"], "unit": port["unit"],
                                            "value": value or None, "uncertainty": {"kind": "unknown"}})
                else:
                    unsupported.add("quantity_kind:" + str(body.get("kind")))
            else:
                schema(body, "quantity", role)
                if role == "result":
                    scalar(body["tolerance"])
                if role == "interface":
                    for port in [*body["inputs"].values(), *body["outputs"].values()]:
                        for descriptor in (port["columns"].values() if port["kind"] == "table" else [port]):
                            if descriptor["kind"] == "scalar":
                                scalar({"kind": "scalar", "dimension": descriptor["dimension"], "unit": descriptor["unit"],
                                        "value": None, "uncertainty": {"kind": "unknown"}})
                    for value in body.get("parameters", {}).values():
                        scalar(value)
                    if "entrypoint" in body:
                        artifact(body["entrypoint"]["artifact"])
        elif profile == LEAN:
            schema(body, "lean", role)
            if role == "interface":
                for entry in [body["source"], body["lock"], body["statement"]["artifact"]]:
                    artifact(entry)
                if "module" not in body["statement"]["artifact"]:
                    statement = load((Path(directory) / body["statement"]["artifact"]["path"]).read_text())
                    need(set(statement) == {"encoding", "universe_parameters", "expression"} and statement["encoding"] == "lean-expr/0.1-draft.1", "native_encoding")
                    need(isinstance(statement["universe_parameters"], list), "native_encoding")
                    for name in statement["universe_parameters"]:
                        schema(name, "lean", "name")
                    universes = {json.dumps(name) for name in statement["universe_parameters"]}
                    need(len(universes) == len(statement["universe_parameters"]), "duplicate_universe")
                    native_expression(statement["expression"], universes=universes)
                    fingerprint = hashlib.sha256(b"lean-expr/0.1-draft.1\n" + rfc8785.dumps(statement)).hexdigest()
                    need(fingerprint == body["statement"]["fingerprint"], "statement_fingerprint")
        elif profile == RESEARCH and role == "result":
            schema(body, "research", "result")
            plan = reference(body["plan"], {"applications"})
            observation = reference(body["observation"], {"components"})
            model = reference(body["model"], {"components"})
            if plan:
                need(plan["phase"] == "planned", "assessment_plan")
                prediction = plan.get("annotations", {}).get(RESEARCH, {}).get("prediction")
                need(prediction is not None and prediction["observation"] == body["observation"]["id"], "assessment_observation")
                need(body["model"] == plan["component"], "assessment_model")
            if observation:
                need(observation["kind"] == "data", "observation_kind")
            if model:
                need(model["kind"] in {"model", "claim"}, "model_kind")
            numeric = body["outcome"] in {"failed_prediction", "within_bound"}
            need(("absolute_error" in body) == numeric, "assessment_error")
            if numeric:
                scalar(body["absolute_error"])
        else:
            unsupported.add(profile + ":" + role)

    def bindings(values):
        for value in values.values():
            if "ref" in value:
                record = reference(value["ref"])
                if record and "output" in value:
                    need(record.get("phase") == "executed" and value["output"] in record.get("outputs", {}), "missing_output")
            elif "artifact" in value:
                artifact(value["artifact"])
            elif "typed" in value:
                typed(value["typed"], "binding")

    def requirements(root):
        nodes = {}
        def visit(node):
            need(node["id"] not in nodes, "duplicate_requirement_id")
            nodes[node["id"]] = node
            if "leaf" in node:
                leaf = node["leaf"]
                need(leaf["profile"] in profiles, "undeclared_profile")
                args = leaf["arguments"]
                if leaf["profile"] == LEAN and leaf["predicate"] == "proposition":
                    need("claim" in args, "leaf_arguments")
                    reference(args["claim"], {"components"})
                elif leaf["profile"] == QUANTITY and leaf["predicate"] == "applicability":
                    need(set(args) == {"claim"}, "leaf_arguments")
                    reference(args["claim"], {"components"})
                elif leaf["profile"] == QUANTITY and leaf["predicate"] in {"quantity", "range", "equals"}:
                    predicate = leaf["predicate"]
                    extras = {"quantity": {"dimension", "unit", "allow_missing"}, "range": {"minimum", "maximum"}, "equals": {"expected"}}[predicate]
                    need(set(args) == {"location", "field"} | extras and args["location"] in {"bindings", "context"}
                         and isinstance(args["field"], str) and args["field"], "leaf_arguments")
                    if predicate == "equals":
                        schema(args["expected"], "module", "binding")
                        bindings({"expected": args["expected"]})
                    elif predicate == "range":
                        scalar(args["minimum"])
                        scalar(args["maximum"])
                    else:
                        schema({"kind": "scalar", **{k: args[k] for k in extras}}, "quantity", "scalarPort")
            else:
                for child in node.get("all", node.get("any", [])):
                    visit(child)
        visit(root)
        return nodes

    def annotation(record, family):
        value = record.get("annotations", {}).get(RESEARCH)
        if value is None:
            return
        need(RESEARCH in profiles, "undeclared_profile")
        schema(value, "research", family)
        for key, allowed in [("question", {"questions"}), ("motivated_by", None), ("previous_attempt", {"applications"})]:
            if key in value:
                target = reference(value[key], allowed)
                if key == "previous_attempt" and target:
                    previous = target.get("annotations", {}).get(RESEARCH, {})
                    need(previous.get("attempt_of") == value.get("attempt_of"), "attempt_identity")
                    need(target["bindings"] == record["bindings"] and target["context"] == record["context"], "changed_retry_input")
        for ref in value.get("contributions", []):
            reference(ref, {"components", "evidence"})
        if "prediction" in value:
            need(record.get("phase") == "planned" and value.get("role") == "test-plan", "prediction_plan")
            scalar(value["prediction"]["expected"])
            scalar(value["prediction"]["bound"])
            need(value["prediction"]["expected"]["value"] is not None and value["prediction"]["bound"]["value"] is not None, "unbound_prediction")
            need(value["prediction"]["expected"]["dimension"] == value["prediction"]["bound"]["dimension"], "prediction_dimension")
            need(Decimal(value["prediction"]["bound"]["value"]) >= 0, "negative_bound")

    for question in questions:
        for ref in question["targets"] + ([question["motivated_by"]] if "motivated_by" in question else []):
            reference(ref)
    for component in manifest["components"]:
        typed(component["interface"], "interface")
        requirements(component["requires"])
        for item in component["sources"]:
            artifact(item)
        for ref in component.get("supersedes", []):
            reference(ref, {"components"})
        annotation(component, "component")
    for application in manifest["applications"]:
        component = reference(application["component"], {"components"})
        nodes = requirements(application["requires"])
        if component:
            need(application["requires"] == component["requires"] or component["requires"] in application["requires"].get("all", []), "weakened_requirements")
        for name in ["bindings", "context", "outputs"]:
            bindings(application.get(name, {}))
        if "plan" in application:
            plan = reference(application["plan"], {"applications"})
            if plan:
                need(plan["phase"] == "planned" and all(application[k] == plan[k] for k in ["component", "bindings", "context", "requires"]), "changed_execution_plan")
        for name, ref_list in application.get("witnesses", {}).items():
            need(name in nodes and "leaf" in nodes[name], "witness_requirement")
            for ref in ref_list:
                reference(ref, {"evidence"})
        for name, branch in application.get("selections", {}).items():
            need(name in nodes and branch in [c["id"] for c in nodes[name].get("any", [])], "invalid_alternative")
        for obstacle in application.get("annotations", {}).get(RESEARCH, {}).get("obstacles", []):
            need(obstacle["requirement"] in nodes, "obstacle_requirement")
        annotation(application, "application")
    for evidence in manifest["evidence"]:
        subject = reference(evidence["subject"], {"components", "applications"})
        if subject and subject.get("phase") == "planned":
            need(evidence["kind"] == "assertion", "planned_execution_evidence")
        if subject and subject.get("phase") == "executed" and evidence["kind"] != "assertion":
            need(evidence["context"] == subject["context"], "evidence_context")
        bindings(evidence["context"])
        artifact(evidence["method"]["implementation"])
        for item in evidence["artifacts"]:
            artifact(item)
        expected_profile = {"formal": LEAN, "computation": QUANTITY, "empirical": RESEARCH}.get(evidence["kind"])
        need(expected_profile is None or evidence["result"]["profile"] == expected_profile, "evidence_kind_profile")
        typed(evidence["result"], "result")
        if evidence["kind"] == "formal":
            result = evidence["result"]["value"]
            need(result["policy"] == evidence["method"]["policy"], "evidence_policy")
            if subject and subject.get("interface", {}).get("profile") == LEAN:
                need(result["statement_fingerprint"] == subject["interface"]["value"]["statement"]["fingerprint"], "evidence_statement")
        if evidence["kind"] == "empirical" and subject and subject.get("phase") == "executed":
            need(subject.get("plan") == evidence["result"]["value"]["plan"], "evidence_plan")

    edges = {key: [] for key in records}
    for component in manifest["components"]:
        edges[component["id"]] = [r["id"] for r in component.get("supersedes", []) if "module" not in r]
    for application in manifest["applications"]:
        previous = application.get("annotations", {}).get(RESEARCH, {}).get("previous_attempt")
        refs = ([previous] if previous else []) + ([application["plan"]] if "plan" in application else [])
        refs += [b["ref"] for field in ["bindings", "context"] for b in application[field].values()
                 if "ref" in b and "module" not in b["ref"] and families[b["ref"]["id"]] == "applications"]
        edges[application["id"]] = [r["id"] for r in refs if "module" not in r]
    visiting, visited = set(), set()
    def visit(key):
        need(key not in visiting, "chronological_cycle", key)
        if key in visited:
            return
        visiting.add(key)
        for parent in edges[key]:
            visit(parent)
        visiting.remove(key)
        visited.add(key)
    for key in edges:
        visit(key)
    return {"wire": "valid", "unsupported": sorted(unsupported),
            "unresolved_dependencies": sorted(unresolved_modules),
            "imported_evidence": "declared", "scientific_verification": "not_performed"}

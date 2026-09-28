"""Regenerate reviewed draft fixtures explicitly. The test command never calls this file."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import rfc8785

from contract import FORMAT, LEAN, QUANTITY, RESEARCH, ROOT, identity

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def ref(id):
    return {"id": id}


def scalar(value, unit="volt", dimension="voltage"):
    return {"kind": "scalar", "value": value, "unit": unit, "dimension": dimension,
            "uncertainty": {"kind": "unknown"}}


def bound(value, unit="volt", dimension="voltage"):
    return {"typed": {"profile": QUANTITY, "value": scalar(value, unit, dimension)}}


def port(unit="volt", dimension="voltage"):
    return {"kind": "scalar", "unit": unit, "dimension": dimension, "allow_missing": False}


def component(id, kind, parameters=None, requires=None, annotation=None, supersedes=()):
    item = {"id": id, "kind": kind, "name": id,
            "interface": {"profile": QUANTITY, "value": {"inputs": {}, "outputs": {}, "parameters": parameters or {}}},
            "requires": requires or {"id": "conditions", "all": []},
            "sources": [{"path": "method.py"}], "license": "Apache-2.0"}
    if annotation:
        item["annotations"] = {RESEARCH: annotation}
    if supersedes:
        item["supersedes"] = [ref(x) for x in supersedes]
    return item


def requirements(temperature):
    return {"id": "conditions", "all": [
        {"id": "temperature", "leaf": {"profile": QUANTITY, "predicate": "equals", "arguments": {
            "location": "context", "field": "temperature", "expected": bound(temperature, "kelvin", "temperature")}}},
        {"id": "physical", "leaf": {"profile": QUANTITY, "predicate": "applicability", "arguments": {"claim": ref("physical-assumption")}}}
    ]}


def application(id, target, bindings, context, requires, annotation=None, plan=None, outputs=None):
    item = {"id": id, "component": ref(target), "phase": "planned" if outputs is None else "executed",
            "bindings": bindings, "context": context, "requires": deepcopy(requires)}
    if outputs is not None:
        item["outputs"] = outputs
    if plan:
        item["plan"] = ref(plan)
    if annotation:
        item["annotations"] = {RESEARCH: annotation}
    return item


def module(name, profile_ids, components, applications, evidence, payloads, annotations=None):
    directory = FIXTURES / name
    directory.mkdir(parents=True, exist_ok=True)
    entries = []
    for path, content in sorted(payloads.items()):
        raw = content.encode() if isinstance(content, str) else content
        (directory / path).parent.mkdir(parents=True, exist_ok=True)
        (directory / path).write_bytes(raw)
        entries.append({"path": path, "size": str(len(raw)), "sha256": hashlib.sha256(raw).hexdigest()})
    value = {"format": FORMAT, "profiles": [{"id": p, "required": True} for p in sorted(profile_ids)],
             "dependencies": [], "payloads": entries, "components": components,
             "applications": applications, "evidence": evidence}
    if annotations:
        value["annotations"] = annotations
    value["id"] = identity(value)
    write(directory / "slean-module.json", value)
    return value


def main():
    statement = {"encoding": "lean-expr/0.1-draft.1", "universe_parameters": [], "expression": ["const", [["str", "True"]], []]}
    fingerprint = hashlib.sha256(b"lean-expr/0.1-draft.1\n" + rfc8785.dumps(statement)).hexdigest()
    claim = {"id": "true-claim", "kind": "claim", "name": "Native encoding example; no science claim",
             "interface": {"profile": LEAN, "value": {"declaration": [["str", "wire_example"]], "module": "FormalFixture",
                 "source": {"path": "FormalFixture.lean"}, "toolchain": "leanprover/lean4:v4.34.1", "lock": {"path": "lake-manifest.json"},
                 "statement": {"encoding": "lean-expr/0.1-draft.1", "artifact": {"path": "statement.json"}, "fingerprint": fingerprint}}},
             "requires": {"id": "formal-conditions", "all": []}, "sources": [{"path": "FormalFixture.lean"}], "license": "Apache-2.0"}
    evidence = [{"id": f"proof-{number}", "kind": "formal", "subject": ref("true-claim"), "context": {},
                 "method": {"policy": "reviewed-source/0.1-draft.1", "implementation": {"path": "check-description.txt"}},
                 "artifacts": [{"path": "FormalFixture.lean"}], "result": {"profile": LEAN, "value": {
                     "status": "passed", "policy": "reviewed-source/0.1-draft.1", "statement_fingerprint": fingerprint,
                     "statement_dependencies": [[["str", "True"]]], "proof_dependencies": [[["str", "True"], ["str", "intro"]]], "axioms": []}}}
                for number in (1, 2)]
    formal = module("formal", [LEAN], [claim], [], evidence, {
        "FormalFixture.lean": "theorem wire_example : True := True.intro\n",
        "lake-manifest.json": '{"version":"1.1.0","packagesDir":".lake/packages","packages":[],"name":"wire_fixture","lakeDir":".lake"}\n',
        "statement.json": json.dumps(statement) + "\n",
        "check-description.txt": "These two saved declarations are deliberately untrusted. A wire reader must not promote them to locally verified proofs.\n"})

    params = {"gain": scalar("2", "volt/millimeter", "gain"), "offset": scalar("0.5")}
    revised = {**params, "offset": scalar("0.6")}
    original_requirements, new_requirements = requirements("293.15"), requirements("313.15")
    components = [
        component("physical-assumption", "claim", annotation={"role": "hypothesis"}),
        component("calibration-original", "method", params, original_requirements, {"role": "method"}),
        component("model-hypothesis", "model", params, new_requirements, {"role": "hypothesis"}),
        component("model-revision", "model", revised, new_requirements, {"role": "revision", "motivated_by": ref("assessment-1")}, ["model-hypothesis"]),
        component("calibration-revised", "method", revised, new_requirements, {"role": "revision", "motivated_by": ref("assessment-2")}, ["calibration-original"]),
        component("observation-1", "data", {"voltage": scalar("8.6")}, annotation={"role": "observation"}),
        component("observation-2", "data", {"voltage": scalar("6.6")}, annotation={"role": "observation"}),
    ]
    for item in components:
        interface = item["interface"]["value"]
        if item["kind"] == "method":
            interface.update(inputs={"reading": port()}, outputs={"displacement": port("millimeter", "length")},
                             entrypoint={"artifact": {"path": "method.py"}, "symbol": "inverse"})
        elif item["kind"] == "model":
            interface.update(inputs={"displacement": port("millimeter", "length")}, outputs={"voltage": port()})
    context = {"sensor": {"literal": "sensor-A"}, "temperature": bound("313.15", "kelvin", "temperature")}
    measurement = {"reading": bound("8.6")}
    blocked = application("blocked-attempt", "calibration-original", measurement, context, original_requirements,
        {"role": "reuse-attempt", "question": ref("reconstruction"), "attempt_of": "measurement-at-313K",
         "contributions": [], "obstacles": [{"requirement": "temperature", "status": "violated", "reason": "Original temperature differs"}]})
    applications = [blocked]
    empirical = []
    for n, target, displacement, expected, observed, outcome, error in [
        (1, "model-hypothesis", "4", "8.5", "8.6", "failed_prediction", "0.1"),
        (2, "model-revision", "3", "6.6", "6.6", "within_bound", "0")]:
        plan_id, run_id, obs_id = f"test-plan-{n}", f"test-run-{n}", f"observation-{n}"
        inputs = {"displacement": bound(displacement, "millimeter", "length")}
        plan = application(plan_id, target, inputs, context, new_requirements,
            {"role": "test-plan", "question": ref("reconstruction"), "prediction": {
                "observable": "voltage", "expected": scalar(expected), "comparison": "absolute_difference",
                "bound": scalar("0.02"), "observation": obs_id}})
        run = application(run_id, target, inputs, context, new_requirements,
                          {"role": "test-execution"}, plan=plan_id, outputs={"voltage": bound(observed)})
        applications.extend([plan, run])
        empirical.append({"id": f"assessment-{n}", "kind": "empirical", "subject": ref(run_id), "context": context,
            "method": {"policy": "absolute-difference/0.1-draft.1", "implementation": {"path": "compare.py"}},
            "artifacts": [{"path": "observations.csv"}], "result": {"profile": RESEARCH, "value": {
                "plan": ref(plan_id), "model": ref(target), "observation": ref(obs_id), "outcome": outcome, "absolute_error": scalar(error)}}})
    retry = application("retry-attempt", "calibration-revised", deepcopy(measurement), deepcopy(context), new_requirements,
        {"role": "reuse-attempt", "question": ref("reconstruction"), "attempt_of": "measurement-at-313K", "previous_attempt": ref("blocked-attempt"),
         "contributions": [ref("calibration-revised"), ref("assessment-2")],
         "obstacles": [{"requirement": "physical", "status": "unresolved", "reason": "Finite observations do not prove physical applicability or exact gain"}]})
    applications.append(retry)
    applications.append(application("retry-run", "calibration-revised", deepcopy(measurement), deepcopy(context), new_requirements,
                                    plan="retry-attempt", outputs={"displacement": bound("4", "millimeter", "length")}))
    columns = {"displacement_mm": port("millimeter", "length"), "voltage_V": port()}
    fit = component("calibration-fit", "method")
    fit["name"] = "Planned calibration fit; execution not supplied by this wire fixture"
    fit["interface"]["value"].update(inputs={"source": {"kind": "table", "format": "csv", "columns": columns}},
                                     outputs={"gain": port("volt/millimeter", "gain"), "offset": port()})
    components.append(fit)
    applications.append(application("inspect-table", "calibration-fit", {"source": {"typed": {"profile": QUANTITY,
        "value": {"kind": "table", "format": "csv", "columns": columns, "artifact": {"path": "calibration.csv"}}}}}, {}, fit["requires"]))
    for number in (1, 2):
        components[4+number]["sources"] = [{"path": f"observation-{number}.json"}]
    research = module("research", [QUANTITY, RESEARCH], components, applications, empirical, {
        "method.py": (ROOT / "examples/reuse/direct-python/method.py").read_bytes(),
        "calibration.csv": (ROOT / "examples/reuse/direct-python/fixtures/calibration.csv").read_bytes(),
        "observations.csv": "id,voltage_V\nobservation-1,8.6\nobservation-2,6.6\n",
        "observation-1.json": json.dumps({"id": "observation-1", "context": context, "voltage": scalar("8.6")}) + "\n",
        "observation-2.json": json.dumps({"id": "observation-2", "context": context, "voltage": scalar("6.6")}) + "\n",
        "compare.py": "from decimal import Decimal\ndef within_bound(expected, observed, bound):\n    return abs(Decimal(observed) - Decimal(expected)) <= Decimal(bound)\n"},
        {RESEARCH: {"questions": [
            {"id": "reconstruction", "wording": "Can this measurement be reconstructed at the new temperature?", "source": "Owned synthetic fixture", "targets": []},
            {"id": "follow-up", "wording": "Does gain also change with temperature?", "source": "Owned synthetic fixture", "motivated_by": ref("assessment-1"), "targets": []}],
            "alternatives": [{"explanation": "The offset could reflect temporal drift.", "source": "Owned synthetic fixture", "status": "unresolved"}]}})
    open_question = module("open-question", [RESEARCH], [], [], [], {}, {RESEARCH: {"questions": [
        {"id": "question", "wording": "What distinguishes these behaviors?", "source": "Illustrative research metadata", "targets": []}], "alternatives": []}})

    statuses = ["satisfied", "violated", "unresolved", "unsupported"]
    tables = {"all": [["satisfied","violated","unresolved","unsupported"], ["violated"]*4,
                       ["unresolved","violated","unresolved","unsupported"], ["unsupported","violated","unsupported","unsupported"]],
              "any": [["satisfied"]*4, ["satisfied","violated","unresolved","unsupported"],
                       ["satisfied","unresolved","unresolved","unsupported"], ["satisfied","unsupported","unsupported","unsupported"]]}
    truth = [{"operator": op, "inputs": [a,b], "expected": table[i][j]}
             for op,table in tables.items() for i,a in enumerate(statuses) for j,b in enumerate(statuses)]
    truth += [{"operator": "all", "inputs": [], "expected": "satisfied"}, {"operator": "any", "inputs": [], "expected": "violated"}]
    write(HERE / "requirement-vectors.json", truth)
    raw_vectors = ["{}", '{"numbers":[333333333.33333329,1e30,4.50,2e-3,1e-27]}',
                   '{"😀":"astral","דּ":"bmp","é":"composed","é":"decomposed"}',
                   '{"value":"9007199254740993.0000000000000001","missing":null}', '{"negative_zero":-0.0}']
    vectors = [{"input_json": raw, "canonical": rfc8785.dumps(json.loads(raw)).decode(),
                "sha256": hashlib.sha256(rfc8785.dumps(json.loads(raw))).hexdigest()} for raw in raw_vectors]
    write(HERE / "identity-vectors.json", {"jcs": vectors, "modules": [
        {"fixture": name, "id": item["id"]} for name,item in [("formal",formal),("research",research),("open-question",open_question)]]})


if __name__ == "__main__":
    main()

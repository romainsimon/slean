"""Black-box conformance checks for the pinned Slean CLI and public fixtures."""

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / ".lake/build/bin/slean"
EXAMPLES = ROOT / "examples"


def invoke(*args):
    proc = subprocess.run([str(BIN), *map(str, args)], capture_output=True, text=True, cwd=ROOT)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(f"invalid CLI JSON: {proc.stdout!r}; stderr={proc.stderr!r}") from error
    return proc.returncode, payload, proc.stdout


def fixture(name="valid.json"):
    return json.loads((EXAMPLES / name).read_text())


def run_case(case, command="validate", *rest):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "case.json"
        path.write_text(json.dumps(case))
        return invoke(command, path, *rest)


class CliTests(unittest.TestCase):
    def test_valid_and_four_preregistered_errors(self):
        code, result, _ = invoke("validate", EXAMPLES / "valid.json")
        self.assertEqual(code, 0)
        self.assertEqual(result["events"], 10)
        expected = {
            "protocol-revision.json": ("event-11", "protocol_revision"),
            "unit-mismatch.json": ("event-4", "metric_unit"),
            "missing-reference.json": ("event-2", "missing_protocol"),
            "future-observation.json": ("event-6", "future_observation"),
        }
        for name, (event_id, reason) in expected.items():
            with self.subTest(name=name):
                a = invoke("validate", EXAMPLES / name)
                b = invoke("validate", EXAMPLES / name)
                self.assertEqual(a, b)
                self.assertEqual(a[0], 1)
                self.assertEqual(a[1]["error"]["event_id"], event_id)
                self.assertEqual(a[1]["error"]["code"], reason)

    def test_unknown_error_and_override(self):
        for name, reason in (
            ("unknown.json", "Synthetic measurement is unavailable."),
            ("technical-error.json", "Synthetic measurement failed with a technical error."),
        ):
            code, result, _ = invoke("validate", EXAMPLES / name)
            self.assertEqual((code, result["ok"]), (0, True))
            _, state, _ = invoke("replay", EXAMPLES / name)
            self.assertEqual(state["assessments"][0]["verdict"], "undetermined")
            self.assertEqual(state["decisions"][0]["result"], "defer")
            self.assertEqual(state["decisions"][0]["reason"], reason)
        code, result, _ = invoke("validate", EXAMPLES / "override-no-reason.json")
        self.assertEqual(code, 1)
        self.assertEqual(result["error"]["code"], "override_reason")
        case = fixture("unknown.json")
        case["events"][6]["payload"].update(result="override", reason="Human exception; no measured pass.")
        code, _, _ = run_case(case)
        self.assertEqual(code, 0)
        _, state, _ = run_case(case, "replay")
        self.assertEqual(state["assessments"][0]["verdict"], "undetermined")
        self.assertEqual(state["decisions"][0]["result"], "override")

    def test_snapshots_and_append_only_order(self):
        case = fixture()
        prefix = run_case(case, "replay", 7)[2]
        case["events"][9]["payload"]["value"] = "0.123"
        self.assertEqual(run_case(case, "replay", 7)[2], prefix)
        self.assertEqual(invoke("replay", EXAMPLES / "valid.json")[2],
                         invoke("replay", EXAMPLES / "valid.json")[2])
        self.assertEqual(invoke("replay", EXAMPLES / "valid.json", "bad")[1]["error"]["code"], "prefix")
        self.assertEqual(invoke("replay", EXAMPLES / "valid.json", "11")[1]["error"]["code"], "prefix")
        case["events"][4]["sequence"] = 3
        code, result, _ = run_case(case)
        self.assertEqual(code, 1)
        self.assertEqual(result["error"]["code"], "sequence")
        case = fixture()
        case["events"][4]["event_id"] = "event-4"
        code, result, _ = run_case(case)
        self.assertEqual((code, result["error"]["code"]), (1, "duplicate_event"))
        case = fixture()
        case["events"][1]["payload"]["identity"]["id"] = "event-2"
        self.assertEqual(run_case(case)[1]["error"]["code"], "duplicate_object")

    def test_timeline_uses_validated_prefixes_and_agent_projection(self):
        code, timeline, baseline_bytes = invoke("timeline", EXAMPLES / "valid.json", "agent")
        self.assertEqual(code, 0)
        self.assertEqual(timeline["format"], "slean-explorer-timeline/0.1.0")
        self.assertEqual(timeline["audience"], "agent")
        self.assertEqual(len(timeline["case"]["events"]), 8)
        self.assertEqual(len(timeline["snapshots"]), 9)
        self.assertEqual(timeline["snapshots"][0]["decisions"], [])
        self.assertEqual(timeline["snapshots"][7]["decisions"][0]["result"], "promote")
        self.assertEqual(timeline["snapshots"][7]["relations"], [])
        self.assertEqual(timeline["snapshots"][8]["relations"][0]["kind"], "support")
        projected = timeline["case"]
        for prefix in (0, 4, 7, 8):
            _, replayed, _ = run_case(projected, "replay", prefix)
            for field in ("protocols", "runs", "artifacts", "observations", "costs",
                          "assessments", "decisions", "relations"):
                self.assertEqual(timeline["snapshots"][prefix][field], replayed[field])
        case = fixture()
        case["events"][9]["payload"]["value"] = "0.123"
        self.assertEqual(run_case(case, "timeline", "agent")[2], baseline_bytes)
        self.assertNotIn("private-observation", baseline_bytes)
        self.assertEqual(run_case(case, "timeline", "owner")[1]["audience"], "owner")
        self.assertEqual(invoke("timeline", EXAMPLES / "unit-mismatch.json", "agent")[1]["error"]["code"], "metric_unit")

    def test_agent_timeline_does_not_expose_owner_validation_diagnostic(self):
        case = fixture()
        owner_event = case["events"][8]
        owner_event["event_id"] = "private-owner-event-sentinel"
        owner_event["payload"]["digest"] = "invalid"
        code, agent, agent_bytes = run_case(case, "timeline", "agent")
        self.assertEqual(code, 1)
        self.assertEqual(agent["error"], {
            "event_id": "", "object_id": "", "code": "invalid_case",
            "message": "agent timeline unavailable; validate the source locally for details"})
        self.assertNotIn("private-owner-event-sentinel", agent_bytes)
        self.assertNotIn("private-artifact-1", agent_bytes)
        code, owner, _ = run_case(case, "timeline", "owner")
        self.assertEqual(code, 1)
        self.assertEqual(owner["error"]["code"], "artifact")
        self.assertEqual(owner["error"]["event_id"], "private-owner-event-sentinel")

        noncanonical = fixture()
        noncanonical["private-field-sentinel"] = "private-value-sentinel"
        code, agent, agent_bytes = run_case(noncanonical, "timeline", "agent")
        self.assertEqual((code, agent["error"]["code"]), (1, "invalid_case"))
        self.assertNotIn("private-field-sentinel", agent_bytes)
        self.assertNotIn("private-value-sentinel", agent_bytes)
        self.assertEqual(run_case(noncanonical, "timeline", "owner")[1]["error"]["code"],
                         "unexpected_field")

        collision = fixture()
        private_id = collision["events"][8]["payload"]["identity"]["id"]
        agent_event = collision["events"][9]
        agent_event["audience"] = "agent"
        agent_event["payload"]["identity"]["audience"] = "agent"
        agent_event["payload"]["identity"]["id"] = private_id
        code, agent, agent_bytes = run_case(collision, "timeline", "agent")
        self.assertEqual((code, agent["error"]["code"]), (1, "invalid_case"))
        self.assertNotIn(private_id, agent_bytes)
        code, owner, _ = run_case(collision, "timeline", "owner")
        self.assertEqual((code, owner["error"]["code"]), (1, "duplicate_object"))
        self.assertEqual(owner["error"]["object_id"], private_id)

    def test_versioned_dependency_gates_and_audience_projection(self):
        case = fixture("dependency-gates.json")
        self.assertEqual(run_case(case)[0], 0)
        state = run_case(case, "replay")[1]
        self.assertEqual([(gate["operator"], gate["kind"]) for gate in state["dependency_gates"]],
                         [("all_of", "prerequisite"), ("any_of", "support")])
        view = run_case(case, "view", "agent")[1]
        self.assertEqual(view["dependency_gates"][1]["member_refs"],
                         ["observation-1", "observation-2"])
        timeline = run_case(case, "timeline", "agent")[1]
        self.assertEqual(len(timeline["snapshots"][11]["dependency_gates"]), 0)
        self.assertEqual(len(timeline["snapshots"][12]["dependency_gates"]), 1)
        self.assertEqual(len(timeline["snapshots"][13]["dependency_gates"]), 2)

        changed = copy.deepcopy(case)
        changed["schema_version"] = changed["semantics_version"] = "0.2.0"
        self.assertEqual(run_case(changed)[1]["error"]["code"], "version")
        changed = copy.deepcopy(case)
        changed["events"][-1]["payload"]["member_refs"][1] = "future-object"
        self.assertEqual(run_case(changed)[1]["error"]["code"], "missing_gate_ref")
        changed = copy.deepcopy(case)
        changed["events"][-1]["payload"]["member_refs"][1] = "observation-1"
        self.assertEqual(run_case(changed)[1]["error"]["code"], "gate_members")
        changed = copy.deepcopy(case)
        changed["events"][-1]["payload"]["operator"] = "unknown"
        self.assertEqual(run_case(changed)[1]["error"]["code"], "gate_operator")
        changed = copy.deepcopy(case)
        changed["events"][11]["recorded_at"] = "2026-01-01T00:05:00Z"
        self.assertEqual(run_case(changed)[1]["error"]["code"], "gate_time")
        changed = copy.deepcopy(case)
        changed["events"][7]["payload"]["source_ref"] = "relation-1"
        self.assertEqual(run_case(changed)[1]["error"]["code"], "missing_relation_ref")

        baseline_export = run_case(case, "export", "agent")[2]
        baseline_view = run_case(case, "view", "agent")[2]
        private_artifact = copy.deepcopy(fixture()["events"][8])
        private_artifact.update(event_id="event-14", sequence=14,
                                recorded_at="2026-01-01T00:14:00Z")
        hidden_gate = copy.deepcopy(case["events"][-1])
        hidden_gate.update(event_id="event-15", sequence=15,
                           recorded_at="2026-01-01T00:15:00Z")
        hidden_gate["payload"]["identity"]["id"] = "gate-hidden-1"
        hidden_gate["payload"]["member_refs"] = ["observation-1", "private-artifact-1"]
        case["events"].extend([private_artifact, hidden_gate])
        self.assertEqual(run_case(case)[0], 0)
        self.assertEqual(run_case(case, "export", "agent")[2], baseline_export)
        self.assertEqual(run_case(case, "view", "agent")[2], baseline_view)
        self.assertNotIn("private-artifact-1", run_case(case, "timeline", "agent")[2])

    def test_gate_examples_preserve_unknown_vs_measured_zero(self):
        expected = (
            ("dependency-gates-unknown.json", "unknown", None, "undetermined", "defer"),
            ("dependency-gates-zero.json", "measured", "0", "fail", "reject"),
        )
        for name, status, value, verdict, decision in expected:
            with self.subTest(name=name):
                path = EXAMPLES / name
                code, result, _ = invoke("validate", path)
                self.assertEqual((code, result["ok"], result["events"]), (0, True, 13))
                _, view, _ = invoke("view", path, "agent")
                self.assertEqual((view["observations"][0]["status"], view["observations"][0]["value"]),
                                 (status, value))
                self.assertEqual(view["decisions"][0]["result"], decision)
                _, state, _ = invoke("replay", path)
                self.assertEqual(state["assessments"][0]["verdict"], verdict)
                self.assertEqual(len(state["dependency_gates"]), 2)

    def test_exact_decimal_and_cost_cap(self):
        case = fixture()
        case["events"][3]["payload"]["value"] = "0.0010000000000000000001"
        self.assertEqual(run_case(case)[0], 0)
        case["events"][3]["payload"]["value"] = "0.001"
        code, result, _ = run_case(case)
        self.assertEqual((code, result["error"]["code"]), (1, "verdict"))
        case = fixture()
        case["events"][4]["payload"]["amount"] = "10.01"
        code, result, _ = run_case(case)
        self.assertEqual((code, result["error"]["code"]), (1, "cost_cap_exceeded"))
        case["events"][4]["payload"]["coverage"] = "partial"
        code, result, _ = run_case(case)
        self.assertEqual((code, result["error"]["code"]), (1, "cost_cap_exceeded"))
        case = fixture()
        case["events"][4]["payload"]["amount"] = "-1"
        self.assertEqual(run_case(case)[1]["error"]["code"], "cost")

    def test_protocol_cost_cap_covers_all_runs(self):
        case = fixture()
        run = copy.deepcopy(case["events"][1])
        run.update(event_id="event-11", sequence=11, recorded_at="2026-01-01T00:11:00Z")
        run["payload"]["identity"]["id"] = "run-2"
        cost = copy.deepcopy(case["events"][4])
        cost.update(event_id="event-12", sequence=12, recorded_at="2026-01-01T00:12:00Z")
        cost["payload"]["identity"]["id"] = "cost-2"
        cost["payload"]["run_ref"] = "run-2"
        cost["payload"]["amount"] = "7.50"
        case["events"].extend([run, cost])
        self.assertEqual(run_case(case)[0], 0)

        cost["payload"]["amount"] = "7.51"
        code, result, _ = run_case(case)
        self.assertEqual(code, 1)
        self.assertEqual(result["error"]["code"], "cost_cap_exceeded")
        self.assertEqual(result["error"]["event_id"], "event-12")
        self.assertEqual(result["error"]["object_id"], "cost-2")

        separate = fixture()
        protocol = copy.deepcopy(separate["events"][0])
        protocol.update(event_id="event-11", sequence=11, recorded_at="2026-01-01T00:11:00Z")
        protocol["payload"]["identity"].update(id="protocol-2", version=2)
        protocol["payload"]["frozen_at"] = protocol["recorded_at"]
        run.update(event_id="event-12", sequence=12, recorded_at="2026-01-01T00:12:00Z")
        run["payload"]["protocol_ref"] = "protocol-2"
        cost.update(event_id="event-13", sequence=13, recorded_at="2026-01-01T00:13:00Z")
        cost["payload"]["amount"] = "8.00"
        separate["events"].extend([protocol, run, cost])
        self.assertEqual(run_case(separate)[0], 0)

    def test_required_cost_fields_match_schema(self):
        case = fixture()
        case["events"][0]["payload"]["cost_unit"] = ""
        self.assertEqual(run_case(case)[1]["error"]["code"], "protocol")
        case = fixture()
        case["events"][4]["payload"]["category"] = ""
        self.assertEqual(run_case(case)[1]["error"]["code"], "cost")

    def test_audiences_follow_the_wire_contract(self):
        for field in ("question", "claim"):
            case = fixture()
            case[field]["identity"]["audience"] = "private"
            self.assertEqual(run_case(case)[1]["error"]["code"], "audience")
        case = fixture()
        case["events"][0]["audience"] = "private"
        case["events"][0]["payload"]["identity"]["audience"] = "private"
        self.assertEqual(run_case(case)[1]["error"]["code"], "audience")
        case = fixture()
        case["events"][0]["payload"]["identity"]["audience"] = "private"
        self.assertEqual(run_case(case)[1]["error"]["code"], "audience")

    def test_decision_cannot_predate_assessment(self):
        case = fixture()
        case["events"][6]["recorded_at"] = "2026-01-01T00:05:00Z"
        self.assertEqual(run_case(case)[1]["error"]["code"], "future_assessment")
        case = fixture()
        case["events"][0]["recorded_at"] = "2026-99-01T00:01:00Z"
        self.assertEqual(run_case(case)[1]["error"]["code"], "event_metadata")

    def test_roundtrip_version_and_projection(self):
        case = fixture()
        code, exported, bytes_one = run_case(case, "export", "owner")
        self.assertEqual(code, 0)
        self.assertEqual(exported["format"], "slean-export/0.1.0")
        self.assertEqual(exported["lean_version"], "4.28.0")
        self.assertEqual(exported["case"], case)
        self.assertEqual(run_case(exported, "export", "owner")[2], bytes_one)
        self.assertEqual(run_case(exported, "validate")[0], 0)
        self.assertEqual(run_case(case, "export-case", "owner")[1], case)
        incompatible = copy.deepcopy(exported)
        incompatible["lean_version"] = "4.27.0"
        self.assertEqual(run_case(incompatible)[1]["error"]["code"], "json")
        incompatible = copy.deepcopy(exported)
        incompatible["format"] = "slean-export/9.0.0"
        self.assertEqual(run_case(incompatible)[1]["error"]["code"], "json")
        incompatible = copy.deepcopy(exported)
        incompatible["unreviewed_field"] = "opaque"
        self.assertEqual(run_case(incompatible, "export", "agent")[1]["error"]["code"], "json")
        case["schema_version"] = "0.2.0"
        code, result, _ = run_case(case)
        self.assertEqual((code, result["error"]["code"]), (1, "version"))
        case["semantics_version"] = "0.2.0"
        self.assertEqual(run_case(case)[0], 0)
        case = fixture()
        baseline_export = run_case(case, "export", "agent")[2]
        baseline_view = run_case(case, "view", "agent")[2]
        case["events"][8]["payload"]["digest"] = "sha256:" + "f" * 64
        case["events"][8]["payload"]["identity"]["provenance"] = "private://changed"
        case["events"][8]["payload"]["secret_note"] = "must never appear"
        case["events"][9]["payload"]["value"] = "0.123"
        case["events"][9]["payload"]["identity"]["provenance"] = "private://changed"
        self.assertEqual(run_case(case, "export", "agent")[2], baseline_export)
        self.assertEqual(run_case(case, "view", "agent")[2], baseline_view)
        self.assertNotIn("private-artifact", baseline_export)
        self.assertNotIn("private-observation", baseline_view)
        self.assertNotIn("secret_note", baseline_export)
        self.assertEqual(len(json.loads(baseline_export)["case"]["events"]), 8)
        inserted = copy.deepcopy(fixture())
        inserted["events"].insert(4, {
            "event_id": "hidden-extra", "sequence": 5, "kind": "artifact_registered",
            "version": 1, "domain": "synthetic-computation", "provenance": "synthetic://slean-v0",
            "actor": "synthetic-author", "recorded_at": "2026-01-01T00:04:30Z",
            "audience": "owner", "payload": {"identity": {
                "id": "hidden-extra", "version": 1, "domain": "synthetic-computation",
                "provenance": "private://inserted", "audience": "owner"},
                "digest": "sha256:" + "d" * 64, "media_type": "application/json"},
        })
        for index, row in enumerate(inserted["events"], 1):
            row["sequence"] = index
        self.assertEqual(run_case(inserted, "export", "agent")[2], baseline_export)
        self.assertEqual(run_case(inserted, "view", "agent")[2], baseline_view)
        case = fixture()
        case["unsupported_private_metadata"] = "hidden"
        self.assertEqual(run_case(case)[1]["error"]["code"], "unexpected_field")
        self.assertEqual(run_case(case, "export", "agent")[2], baseline_export)
        hidden_case = fixture()
        hidden_case["audience"] = "owner"
        hidden_case["question"]["identity"]["audience"] = "owner"
        hidden_case["claim"]["identity"]["audience"] = "owner"
        hidden_bytes = run_case(hidden_case, "export", "agent")[2]
        hidden_case.update(case_id="secret-id", version=2, domain="secret-domain", provenance="secret-provenance")
        hidden_case["question"]["text"] = "secret question"
        hidden_case["claim"]["text"] = "secret claim"
        self.assertEqual(run_case(hidden_case, "export", "agent")[2], hidden_bytes)

    def test_agent_export_redacts_opaque_run_input_reference(self):
        case = fixture()
        case["events"][1]["payload"]["input_ref"] = "private-artifact-1"
        baseline_export = run_case(case, "export", "agent")[2]
        baseline_timeline = run_case(case, "timeline", "agent")[2]
        self.assertNotIn("private-artifact-1", baseline_export)
        self.assertNotIn("private-artifact-1", baseline_timeline)
        self.assertEqual(json.loads(baseline_export)["case"]["events"][1]["payload"]["input_ref"], "[redacted]")
        self.assertEqual(run_case(case, "export", "owner")[1]["case"]["events"][1]["payload"]["input_ref"],
                         "private-artifact-1")

        case["events"][1]["payload"]["input_ref"] = "private://other-input"
        self.assertEqual(run_case(case, "export", "agent")[2], baseline_export)
        self.assertEqual(run_case(case, "timeline", "agent")[2], baseline_timeline)

    def test_formal_status_requires_local_pin(self):
        _, pin, _ = invoke("proof-statement")
        case = fixture("formal-claim.json")
        self.assertEqual(case["events"][-1]["payload"]["statement"], pin["elaborated_statement"])
        code, receipt, _ = run_case(case, "proof")
        self.assertEqual(code, 0)
        self.assertEqual(receipt[0]["status"], "declared")
        self.assertTrue(receipt[0]["attestation_eligible"])
        self.assertEqual(receipt[0]["dependencies"], pin["dependencies"])
        self.assertIn("Slean.promotionEvidence", receipt[0]["dependencies"])
        contrary = copy.deepcopy(case)
        contrary["events"][3]["payload"]["value"] = "0.000"
        contrary["events"][5]["payload"]["verdict"] = "fail"
        contrary["events"][6]["payload"].update(result="reject", reason="Below the frozen threshold.")
        code, contrary_receipt, _ = run_case(contrary, "proof")
        self.assertEqual(code, 0)
        self.assertEqual(contrary_receipt[0]["status"], "declared")
        self.assertTrue(contrary_receipt[0]["attestation_eligible"])
        self.assertEqual(contrary_receipt[0]["elaborated_statement"], receipt[0]["elaborated_statement"])
        exported = run_case(case, "export", "agent")[1]
        self.assertEqual(exported["case"]["events"][-1]["payload"]["status"], "declared")
        self.assertEqual(run_case(exported, "proof")[1][0]["status"], "declared")
        self.assertTrue(run_case(exported, "proof")[1][0]["attestation_eligible"])
        for key, value in (
            ("declaration", "Test.sorry"), ("declaration", "Test.unauthorizedAxiom"),
            ("statement", "substituted statement"), ("toolchain", "other toolchain")):
            bad = copy.deepcopy(case)
            bad["events"][-1]["payload"][key] = value
            self.assertEqual(run_case(bad, "proof")[1][0]["status"], "declared")
            self.assertFalse(run_case(bad, "proof")[1][0]["attestation_eligible"])
            self.assertEqual(run_case(bad, "proof")[1][0]["dependencies"], [])
        forged = copy.deepcopy(case)
        forged["events"][-1]["payload"]["statement"] = "forged"
        forged["events"][-1]["payload"]["status"] = "kernel_checked"
        self.assertEqual(run_case(forged, "proof")[1][0]["status"], "declared")
        self.assertFalse(run_case(forged, "proof")[1][0]["attestation_eligible"])


if __name__ == "__main__":
    unittest.main()

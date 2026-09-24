import Slean

open Lean Slean

private def ident (id : String) : Identity :=
  { id, version := 1, domain := "synthetic-computation",
    provenance := "synthetic://slean-v0", audience := "agent" }

private def protocol : FrozenProtocol :=
  { identity := ident "protocol-1", claim_ref := "claim-1",
    metric_id := "synthetic_delta", unit := "ratio", direction := "gte",
    threshold := "0.001", inclusive := false, data_scope := "synthetic input A",
    evaluator_ref := "synthetic-evaluator-v1", cost_cap := "10.00",
    cost_unit := "cpu_s", stop_rule := "one synthetic measurement",
    frozen_at := "2026-01-01T00:01:00Z" }

private def run : Run :=
  { identity := ident "run-1", protocol_ref := "protocol-1",
    input_ref := "synthetic-input-A", seed := "7" }

private def artifact : ArtifactRef :=
  { identity := ident "artifact-1", digest := "sha256:" ++ String.ofList (List.replicate 64 'a'),
    media_type := "application/json" }

private def observation : Observation :=
  { identity := ident "observation-1", run_ref := "run-1",
    metric_id := "synthetic_delta", unit := "ratio", value := some "0.002",
    status := "measured", artifact_ref := "artifact-1",
    observed_at := "2026-01-01T00:04:00Z" }

private def cost : CostEntry :=
  { identity := ident "cost-1", run_ref := "run-1", category := "machine_time",
    amount := "2.50", unit := "cpu_s", source := "synthetic-meter", coverage := "complete" }

private def assessment : Assessment :=
  { identity := ident "assessment-1", protocol_ref := "protocol-1",
    observation_refs := #["observation-1"], verdict := "pass", rule_used := "exact_v0" }

private def decision : PromotionDecision :=
  { identity := ident "decision-1", assessment_ref := "assessment-1",
    result := "promote", reason := "Synthetic threshold passed." }

private def relation : Relation :=
  { identity := ident "relation-1", source_ref := "observation-1",
    target_ref := "claim-1", kind := "support" }

private def ev (sequence : Nat) (kind time : String) (payload : Json) : Event :=
  { event_id := s!"event-{sequence}", version := 1,
    domain := "synthetic-computation", provenance := "synthetic://slean-v0", sequence, kind,
    actor := "synthetic-author", recorded_at := s!"2026-01-01T00:{time}:00Z",
    audience := "agent", payload }

def syntheticCase : CaseFile :=
  { schema_version := "0.1.0", semantics_version := "0.1.0",
    case_id := "synthetic-decision-1", version := 1,
    domain := "synthetic-computation", provenance := "synthetic://slean-v0",
    audience := "agent",
    question := { identity := ident "question-1", text := "Does a synthetic candidate exceed a fixed threshold?" },
    claim := { identity := ident "claim-1", text := "The synthetic metric exceeds 0.001 on the stated input." },
    events := #[
      ev 1 "protocol_frozen" "01" (toJson protocol),
      ev 2 "run_started" "02" (toJson run),
      ev 3 "artifact_registered" "03" (toJson artifact),
      ev 4 "observation_recorded" "04" (toJson observation),
      ev 5 "cost_recorded" "05" (toJson cost),
      ev 6 "assessment_recorded" "06" (toJson assessment),
      ev 7 "decision_recorded" "07" (toJson decision),
      ev 8 "relation_recorded" "08" (toJson relation)] }

#guard (replay syntheticCase).isOk
#guard (compareDecimal (parseDecimal "0.010" |>.toOption.get!)
  (parseDecimal "0.01" |>.toOption.get!)) == .eq
#guard (assessExact protocol observation).toOption == some "pass"

def main : IO Unit := IO.println (toJson (project syntheticCase "agent")).compress

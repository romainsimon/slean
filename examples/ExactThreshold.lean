import Slean

open Slean

private def identity (id : String) : Identity :=
  { id, version := 1, domain := "synthetic-computation",
    provenance := "synthetic://worked-examples", audience := "agent" }

private def protocol : FrozenProtocol :=
  { identity := identity "protocol-exact", claim_ref := "claim-exact",
    metric_id := "synthetic_delta", unit := "ratio", direction := "gte",
    threshold := "0.010", inclusive := false, data_scope := "synthetic input",
    evaluator_ref := "synthetic-evaluator", cost_cap := "1.00",
    cost_unit := "cpu_s", stop_rule := "one synthetic reading",
    frozen_at := "2026-01-01T00:00:00Z" }

private def reading (id value : String) : Observation :=
  { identity := identity id, run_ref := "run-exact", metric_id := "synthetic_delta",
    unit := "ratio", value := some value, status := "measured",
    artifact_ref := "artifact-exact", observed_at := "2026-01-01T00:01:00Z" }

def main : IO Unit := do
  match assessExact protocol (reading "equal" "0.0100"),
        assessExact protocol (reading "above" "0.0101") with
  | .ok equal, .ok above =>
    IO.println s!"equal={equal}; above={above}"
  | .error message, _ => throw (IO.userError message)
  | _, .error message => throw (IO.userError message)

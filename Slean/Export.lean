import Slean.Core

namespace Slean
open Lean

private def field (j : Json) (name : String) : String :=
  (j.getObjValAs? String name).toOption.getD ""

private def refs (event : Event) : Array String := Id.run do
  let p := event.payload
  match event.kind with
  | "protocol_frozen" => return #[field p "claim_ref"]
  | "run_started" => return #[field p "protocol_ref"]
  | "observation_recorded" => return #[field p "run_ref", field p "artifact_ref"]
  | "cost_recorded" => return #[field p "run_ref"]
  | "assessment_recorded" =>
    let observations := ((p.getObjValAs? (Array String) "observation_refs").toOption.getD #[])
    return #[field p "protocol_ref"] ++ observations
  | "decision_recorded" => return #[field p "assessment_ref"]
  | "relation_recorded" => return #[field p "source_ref", field p "target_ref"]
  | _ => return #[]

private def objectId (event : Event) : String :=
  match event.payload.getObjVal? "identity" with
  | .ok identity => field identity "id"
  | .error _ => ""

private def canonicalPayload (event : Event) : Option Json :=
  let p := event.payload
  match event.kind with
  | "protocol_frozen" => (fromJson? p : Except String FrozenProtocol).toOption.map toJson
  | "run_started" => (fromJson? p : Except String Run).toOption.map toJson
  | "artifact_registered" => (fromJson? p : Except String ArtifactRef).toOption.map toJson
  | "observation_recorded" => (fromJson? p : Except String Observation).toOption.map toJson
  | "cost_recorded" => (fromJson? p : Except String CostEntry).toOption.map toJson
  | "assessment_recorded" => (fromJson? p : Except String Assessment).toOption.map toJson
  | "decision_recorded" => (fromJson? p : Except String PromotionDecision).toOption.map toJson
  | "formal_claim_declared" => (fromJson? p : Except String FormalClaimRef).toOption.map toJson
  | "relation_recorded" => (fromJson? p : Except String Relation).toOption.map toJson
  | _ => none

private def normalizeFormal (event : Event) : Event := Id.run do
  if event.kind != "formal_claim_declared" then return event
  match fromJson? event.payload with
  | .ok (claim : FormalClaimRef) => return { event with payload := toJson { claim with status := "declared" } }
  | .error _ => return event

/-- Project before validation and all derived calculations. Visible sequence
    numbers are local to the projection, so hidden insertion has no effect. -/
def project (caseFile : CaseFile) (audience : String) : CaseFile := Id.run do
  if audience == "owner" then
    return { caseFile with events := caseFile.events.map normalizeFormal }
  let question := if caseFile.question.identity.audience == "agent" then caseFile.question
    else { identity := { id := "redacted-question", version := 1, domain := "redacted", provenance := "redacted", audience := "agent" }, text := "[redacted]" }
  let claim := if caseFile.claim.identity.audience == "agent" then caseFile.claim
    else { identity := { id := "redacted-claim", version := 1, domain := "redacted", provenance := "redacted", audience := "agent" }, text := "[redacted]" }
  let mut known := #[question.identity.id, claim.identity.id]
  let mut visible : Array Event := #[]
  for event in caseFile.events do
    if event.audience == "agent" && (refs event).all known.contains then
      let id := objectId event
      if !id.isEmpty then
        let normalized := normalizeFormal event
        if let some payload := canonicalPayload normalized then
          visible := visible.push { normalized with sequence := visible.size + 1, payload }
          known := known.push id
  let caseId := if caseFile.audience == "agent" then caseFile.case_id else "redacted-case"
  let version := if caseFile.audience == "agent" then caseFile.version else 1
  let domain := if caseFile.audience == "agent" then caseFile.domain else "redacted"
  let provenance := if caseFile.audience == "agent" then caseFile.provenance else "redacted"
  return { caseFile with case_id := caseId, version, domain, provenance, audience := "agent", question, claim, events := visible }

def view (caseFile : CaseFile) (state : State) : Json := Id.run do
  let rows := state.observations.map fun o => Json.mkObj [
    ("id", toJson o.identity.id), ("run_ref", toJson o.run_ref),
    ("metric_id", toJson o.metric_id), ("unit", toJson o.unit),
    ("value", toJson o.value), ("status", toJson o.status)]
  let edges := state.relations.map fun r => Json.mkObj [
    ("id", toJson r.identity.id), ("source_ref", toJson r.source_ref),
    ("target_ref", toJson r.target_ref), ("kind", toJson r.kind)]
  return Json.mkObj [
    ("schema_version", toJson caseFile.schema_version),
    ("case_id", toJson caseFile.case_id),
    ("observations", toJson rows),
    ("relations", toJson edges),
    ("decisions", toJson state.decisions)]

end Slean

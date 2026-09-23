import Slean

open Lean Slean

def readCase (path : String) : IO (Except String (CaseFile × Bool)) := do
  try
    let raw ← if path == "-" then (← IO.getStdin).readToEnd else IO.FS.readFile path
    return do
      let json ← Json.parse raw
      let caseFile : CaseFile ← fromJson? json
      pure (caseFile, toJson caseFile == json)
  catch error => return .error error.toString

def reportError (error : Diagnostic) : IO UInt32 := do
  IO.println (Json.mkObj [("ok", toJson false), ("error", toJson error)]).compress
  return 1

def timelineSnapshot (state : State) (count : Nat) : Json := Json.mkObj [
  ("prefix", toJson count),
  ("protocols", toJson state.protocols),
  ("runs", toJson state.runs),
  ("artifacts", toJson state.artifacts),
  ("observations", toJson state.observations),
  ("costs", toJson state.costs),
  ("assessments", toJson state.assessments),
  ("decisions", toJson state.decisions),
  ("relations", toJson state.relations),
  ("dependency_gates", toJson state.dependency_gates)]

def timelineSnapshots (caseFile : CaseFile) : Except Diagnostic (Array Json) := do
  let mut state ← replay caseFile 0
  let mut snapshots : Array Json := #[timelineSnapshot state 0]
  for event in caseFile.events do
    state ← step state event
    snapshots := snapshots.push (timelineSnapshot state snapshots.size)
  return snapshots

def execute (args : List String) : IO UInt32 := do
  if args == ["proof-statement"] then
    IO.println (Json.mkObj [("declaration", toJson checkedDeclaration),
      ("elaborated_statement", toJson checkedStatement),
      ("toolchain", toJson checkedToolchain)]).compress
    return 0
  match args with
  | command :: path :: rest =>
    let caseResult ← readCase path
    let (caseFile, canonicalInput) ← match caseResult with
      | .ok pair => pure pair
      | .error message => return ← reportError (diag "" "" "json" message)
    let agentProjection := (command == "export" || command == "view") && rest.head? == some "agent"
    if !canonicalInput && !agentProjection then
      return ← reportError (diag "" caseFile.case_id "unexpected_field" "case has unsupported or noncanonical fields")
    if command == "validate" then
      match replay caseFile with
      | .ok state =>
        IO.println (Json.mkObj [("ok", toJson true), ("case_id", toJson caseFile.case_id),
          ("events", toJson state.event_ids.size)]).compress
        return 0
      | .error error => return ← reportError error
    if command == "replay" then
      if rest.head?.isSome && (rest.head!.toNat?).isNone then
        return ← reportError (diag "" caseFile.case_id "prefix" "snapshot prefix must be an integer")
      let count := (rest.head?.bind String.toNat?).getD caseFile.events.size
      match replay caseFile count with
      | .ok state =>
        IO.println (toJson state).compress
        return 0
      | .error error => return ← reportError error
    if command == "export" || command == "view" then
      let audience := rest.head?.getD "owner"
      if audience != "owner" && audience != "agent" then
        return ← reportError (diag "" "" "audience" "expected owner or agent")
      let projected := project caseFile audience
      match replay projected with
      | .error error => return ← reportError error
      | .ok state =>
        IO.println (if command == "export" then (toJson projected).compress else (view projected state).compress)
        return 0
    if command == "timeline" then
      let audience := rest.head?.getD "agent"
      if rest.length > 1 || (audience != "owner" && audience != "agent") then
        return ← reportError (diag "" "" "audience" "expected owner or agent")
      if let .error error := replay caseFile then
        return ← reportError error
      let projected := project caseFile audience
      if let .error error := replay projected then
        return ← reportError error
      let snapshots ← match timelineSnapshots projected with
        | .ok snapshots => pure snapshots
        | .error error => return ← reportError error
      IO.println (Json.mkObj [
        ("format", toJson "slean-explorer-timeline/0.1.0"),
        ("audience", toJson audience),
        ("case", toJson projected),
        ("snapshots", toJson snapshots)]).compress
      return 0
    if command == "proof" then
      match replay caseFile with
      | .error error => return ← reportError error
      | .ok state =>
        IO.println (toJson (state.formal_claims.map proofReceipt)).compress
        return 0
    return ← reportError (diag "" "" "usage" "unknown command")
  | _ => return ← reportError (diag "" "" "usage" "slean validate|replay|export|view|timeline|proof <case.json> [count|owner|agent], or proof-statement")

def main (args : List String) : IO UInt32 := execute args

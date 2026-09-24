import Slean

open Lean Slean

def main : IO Unit := do
  let raw ← IO.FS.readFile "examples/valid.json"
  let json ← match Json.parse raw with
    | .ok value => pure value
    | .error message => throw (IO.userError message)
  let dossier ← match (fromJson? json : Except String CaseFile) with
    | .ok value => pure value
    | .error message => throw (IO.userError message)
  let fullState ← match replay dossier with
    | .ok state => pure state
    | .error diagnostic => throw (IO.userError diagnostic.message)
  let agentDossier := project dossier "agent"
  let agentState ← match replay agentDossier with
    | .ok state => pure state
    | .error diagnostic => throw (IO.userError diagnostic.message)
  let bundle := exportBundle agentDossier
  IO.println s!"validated={fullState.event_ids.size}; agent_events={agentState.event_ids.size}"
  IO.println s!"export={bundle.format}; lean={bundle.lean_version}"

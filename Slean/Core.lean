import Lean

namespace Slean
open Lean

structure Identity where
  id : String
  version : Nat
  domain : String
  provenance : String
  audience : String
  deriving Repr, BEq, ToJson, FromJson

structure Question where
  identity : Identity
  text : String
  deriving Repr, BEq, ToJson, FromJson

structure EmpiricalClaim where
  identity : Identity
  text : String
  deriving Repr, BEq, ToJson, FromJson

structure Event where
  event_id : String
  version : Nat
  domain : String
  provenance : String
  sequence : Nat
  kind : String
  actor : String
  recorded_at : String
  audience : String
  payload : Json
  deriving ToJson, FromJson

structure CaseFile where
  schema_version : String
  semantics_version : String
  case_id : String
  version : Nat
  domain : String
  provenance : String
  audience : String
  question : Question
  claim : EmpiricalClaim
  events : Array Event
  deriving ToJson, FromJson

structure ArtifactRef where
  identity : Identity
  digest : String
  media_type : String
  deriving Repr, BEq, ToJson, FromJson

structure FrozenProtocol where
  identity : Identity
  claim_ref : String
  metric_id : String
  unit : String
  direction : String
  threshold : String
  inclusive : Bool
  data_scope : String
  evaluator_ref : String
  cost_cap : String
  cost_unit : String
  stop_rule : String
  frozen_at : String
  deriving Repr, BEq, ToJson, FromJson

structure Run where
  identity : Identity
  protocol_ref : String
  input_ref : String
  seed : String
  deriving Repr, BEq, ToJson, FromJson

structure Observation where
  identity : Identity
  run_ref : String
  metric_id : String
  unit : String
  value : Option String
  status : String
  artifact_ref : String
  observed_at : String
  deriving Repr, BEq, ToJson, FromJson

structure CostEntry where
  identity : Identity
  run_ref : String
  category : String
  amount : String
  unit : String
  source : String
  coverage : String
  deriving Repr, BEq, ToJson, FromJson

structure Assessment where
  identity : Identity
  protocol_ref : String
  observation_refs : Array String
  verdict : String
  rule_used : String
  deriving Repr, BEq, ToJson, FromJson

structure PromotionDecision where
  identity : Identity
  assessment_ref : String
  result : String
  reason : String
  deriving Repr, BEq, ToJson, FromJson

structure FormalClaimRef where
  identity : Identity
  declaration : String
  statement : String
  toolchain : String
  status : String
  deriving Repr, BEq, ToJson, FromJson

structure Relation where
  identity : Identity
  source_ref : String
  target_ref : String
  kind : String
  deriving Repr, BEq, ToJson, FromJson

/-- A recorded grouping of prior references. This describes an author's
    dependency claim; V0.3 does not evaluate whether its members are true. -/
structure DependencyGate where
  identity : Identity
  target_ref : String
  member_refs : Array String
  operator : String
  kind : String
  deriving Repr, BEq, ToJson, FromJson

/-- Canonical JSON source record for the bounded development-trace adapter.
    Its contents are owner-only and are never an empirical or formal proof. -/
structure SourceRecord where
  identity : Identity
  source_role : String
  canonical_sha256 : String
  raw_json : String
  deriving ToJson, FromJson

/-- Reserved expression syntax. V0.3 records gates but does not evaluate
    general hyperdependencies. -/
inductive DependencyExpr where
  | reference (objectId : String)
  | allOf (members : Array DependencyExpr)
  | anyOf (members : Array DependencyExpr)
  deriving Repr, Inhabited

structure Diagnostic where
  event_id : String
  object_id : String
  code : String
  message : String
  deriving Repr, ToJson

def diag (eventId objectId code message : String) : Diagnostic :=
  { event_id := eventId, object_id := objectId, code, message }

private def validAudience (audience : String) : Bool :=
  audience == "agent" || audience == "owner"

structure Decimal where
  numerator : Int
  places : Nat
  deriving Repr, BEq, Inhabited

/-- Decimal text is exact: no float parser, exponent, NaN or implicit rounding. -/
def parseDecimal (s : String) : Except String Decimal := do
  let negative := s.startsWith "-"
  let unsigned := if negative then (s.drop 1).toString else s
  let parts := unsigned.splitOn "."
  if parts.length == 0 || parts.length > 2 then throw "invalid decimal"
  let whole := parts[0]!
  let fraction := if parts.length == 2 then parts[1]! else ""
  if whole.isEmpty || (parts.length == 2 && fraction.isEmpty) ||
      !(whole.toList.all Char.isDigit) || !(fraction.toList.all Char.isDigit) then
    throw "invalid decimal"
  if whole.length > 1 && whole.startsWith "0" then throw "noncanonical decimal"
  let digits := whole ++ fraction
  let n ← match digits.toInt? with
    | some n => pure n
    | none => throw "invalid decimal"
  return { numerator := if negative then -n else n, places := fraction.length }

def compareDecimal (a b : Decimal) : Ordering :=
  compare (a.numerator * (10 : Int) ^ b.places) (b.numerator * (10 : Int) ^ a.places)

def addDecimal (a b : Decimal) : Decimal :=
  let places := max a.places b.places
  { numerator := a.numerator * (10 : Int) ^ (places - a.places) +
      b.numerator * (10 : Int) ^ (places - b.places), places }

def validTimestamp (s : String) : Bool := Id.run do
  let a := s.toList.toArray
  if a.size != 20 then return false
  if a[4]! != '-' || a[7]! != '-' || a[10]! != 'T' || a[13]! != ':' ||
      a[16]! != ':' || a[19]! != 'Z' then return false
  unless (#[0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18] : Array Nat).all
      (fun i => a[i]!.isDigit) do return false
  let two (i : Nat) := (a[i]!.toNat - '0'.toNat) * 10 + (a[i+1]!.toNat - '0'.toNat)
  let year := (a[0]!.toNat - '0'.toNat) * 1000 + (a[1]!.toNat - '0'.toNat) * 100 +
    (a[2]!.toNat - '0'.toNat) * 10 + (a[3]!.toNat - '0'.toNat)
  let month := two 5
  let maxDay := if month == 2 then
    (if year % 400 == 0 || (year % 4 == 0 && year % 100 != 0) then 29 else 28)
    else if #[4, 6, 9, 11].contains month then 30 else 31
  return month >= 1 && month <= 12 && two 8 >= 1 && two 8 <= maxDay &&
    two 11 <= 23 && two 14 <= 59 && two 17 <= 59

def assessExact (protocol : FrozenProtocol) (observation : Observation) : Except String String := do
  if observation.metric_id != protocol.metric_id || observation.unit != protocol.unit then
    throw "metric or unit differs from frozen protocol"
  if observation.status == "unknown" || observation.status == "technical_error" then
    return "undetermined"
  if observation.status != "measured" then throw "invalid observation status"
  let raw ← match observation.value with
    | some value => pure value
    | none => throw "measured observation has no value"
  let value ← parseDecimal raw
  let threshold ← parseDecimal protocol.threshold
  let order := compareDecimal value threshold
  let passed := if protocol.direction == "gte" then
    order == .gt || (protocol.inclusive && order == .eq)
    else if protocol.direction == "lte" then
      order == .lt || (protocol.inclusive && order == .eq)
    else false
  if protocol.direction != "gte" && protocol.direction != "lte" then
    throw "invalid comparator direction"
  return if passed then "pass" else "fail"

structure State where
  event_ids : Array String := #[]
  object_ids : Array String := #[]
  object_times : Array (String × String) := #[]
  claim_id : String := ""
  protocols : Array FrozenProtocol := #[]
  runs : Array Run := #[]
  artifacts : Array ArtifactRef := #[]
  observations : Array Observation := #[]
  costs : Array CostEntry := #[]
  assessments : Array Assessment := #[]
  decisions : Array PromotionDecision := #[]
  formal_claims : Array FormalClaimRef := #[]
  relations : Array Relation := #[]
  dependency_gates : Array DependencyGate := #[]
  source_records : Array SourceRecord := #[]
  deriving Inhabited, ToJson

def hasObject (state : State) (id : String) : Bool := state.object_ids.contains id
def findProtocol (state : State) (id : String) : Option FrozenProtocol := state.protocols.find? (·.identity.id == id)
def findRun (state : State) (id : String) : Option Run := state.runs.find? (·.identity.id == id)
def findObservation (state : State) (id : String) : Option Observation := state.observations.find? (·.identity.id == id)
def findAssessment (state : State) (id : String) : Option Assessment := state.assessments.find? (·.identity.id == id)
def findTime (state : State) (id : String) : Option String :=
  (state.object_times.find? (·.fst == id)).map (·.snd)

def isSha256 (value : String) : Bool :=
  let hex := (value.drop 7).toString
  value.startsWith "sha256:" && hex.length == 64 &&
    hex.toList.all (fun c => c.isDigit || ('a' <= c && c <= 'f'))

/-- The only evidence path used for a routine promotion. The assessment must
    point to a prior observation from a run on the same frozen protocol. -/
def promotionEvidence (state : State) (decision : PromotionDecision) : Option (FrozenProtocol × Observation) := do
  let assessment ← findAssessment state decision.assessment_ref
  if assessment.verdict != "pass" then none else do
    let observationId ← assessment.observation_refs[0]?
    let observation ← findObservation state observationId
    let run ← findRun state observation.run_ref
    let protocol ← findProtocol state run.protocol_ref
    if protocol.identity.id == assessment.protocol_ref then some (protocol, observation) else none

/-- Invariant of the executable promotion gate. This theorem does not certify
    external evaluators, clocks, artifact contents or empirical truth. -/
theorem promotionEvidence_has_frozen_observation (state : State) (decision : PromotionDecision)
    (h : (promotionEvidence state decision).isSome = true) :
    ∃ assessment protocol run observation observationRef,
      findAssessment state decision.assessment_ref = some assessment ∧
      assessment.verdict = "pass" ∧
      assessment.observation_refs[0]? = some observationRef ∧
      findObservation state observationRef = some observation ∧
      findRun state observation.run_ref = some run ∧
      findProtocol state run.protocol_ref = some protocol ∧
      protocol.identity.id = assessment.protocol_ref := by
  cases ha : findAssessment state decision.assessment_ref with
  | none => simp [promotionEvidence, ha] at h
  | some assessment =>
    by_cases hv : assessment.verdict = "pass"
    ·
      cases hi : assessment.observation_refs[0]? with
      | none => simp [promotionEvidence, ha, hv, hi] at h
      | some observationId =>
        cases ho : findObservation state observationId with
        | none => simp [promotionEvidence, ha, hv, hi, ho] at h
        | some observation =>
          cases hr : findRun state observation.run_ref with
          | none => simp [promotionEvidence, ha, hv, hi, ho, hr] at h
          | some run =>
            cases hp : findProtocol state run.protocol_ref with
            | none => simp [promotionEvidence, ha, hv, hi, ho, hr, hp] at h
            | some protocol =>
              by_cases heq : protocol.identity.id = assessment.protocol_ref
              · refine ⟨assessment, protocol, run, observation, observationId, ?_⟩
                simp [hv, hi, ho, hr, hp, heq]
              · simp [promotionEvidence, ha, hv, hi, ho, hr, hp, heq] at h
    · simp [promotionEvidence, ha, hv] at h

def identityError (state : State) (event : Event) (identity : Identity) : Option Diagnostic := Id.run do
  if identity.id.isEmpty || identity.version == 0 || identity.domain.isEmpty || identity.provenance.isEmpty then
    return some (diag event.event_id identity.id "identity" "ID, positive version, domain and provenance are required")
  if hasObject state identity.id || state.event_ids.contains identity.id then
    return some (diag event.event_id identity.id "duplicate_object" "object ID is already used")
  if !validAudience identity.audience then
    return some (diag event.event_id identity.id "audience" "object audience must be agent or owner")
  if identity.audience != event.audience then
    return some (diag event.event_id identity.id "audience" "event and object audience differ")
  return none

def decodePayload [FromJson α] [ToJson α] (event : Event) : Except Diagnostic α :=
  match fromJson? event.payload with
  | .ok value =>
    if toJson value == event.payload then .ok value else
      .error (diag event.event_id "" "unexpected_field" "payload has unsupported or noncanonical fields")
  | .error message => .error (diag event.event_id "" "payload" message)

def withIdentity (state : State) (event : Event) (identity : Identity) : Except Diagnostic State := do
  if let some error := identityError state event identity then throw error
  return { state with object_ids := (state.object_ids.push identity.id), object_times := (state.object_times.push (identity.id, event.recorded_at)) }

/-- A single append-only transition. Its success has no IO or clock dependency. -/
def step (state : State) (event : Event) : Except Diagnostic State := do
  if event.sequence != state.event_ids.size + 1 then
    throw (diag event.event_id "" "sequence" "event sequence must be contiguous and append-only")
  if state.event_ids.contains event.event_id || hasObject state event.event_id || event.event_id.isEmpty then
    throw (diag event.event_id "" "duplicate_event" "event ID is empty or repeated")
  if event.version == 0 || event.domain.isEmpty || event.provenance.isEmpty ||
      event.actor.isEmpty || !(validTimestamp event.recorded_at) then
    throw (diag event.event_id "" "event_metadata" "version, domain, provenance, actor and canonical UTC recorded_at are required")
  if !validAudience event.audience then
    throw (diag event.event_id "" "audience" "event audience must be agent or owner")
  let state := { state with event_ids := state.event_ids.push event.event_id }
  match event.kind with
  | "protocol_frozen" =>
    let p : FrozenProtocol ← decodePayload event
    if (findProtocol state p.identity.id).isSome then
      throw (diag event.event_id p.identity.id "protocol_revision" "frozen protocol ID cannot be reused; create a new ID and version")
    let state ← withIdentity state event p.identity
    unless p.claim_ref == state.claim_id && p.metric_id != "" && p.unit != "" && p.data_scope != "" &&
        p.evaluator_ref != "" && p.cost_unit != "" && p.stop_rule != "" && p.frozen_at == event.recorded_at do
      throw (diag event.event_id p.identity.id "protocol" "missing protocol field or frozen_at differs from event")
    if (p.direction != "external" && (parseDecimal p.threshold).toOption.isNone) ||
        (parseDecimal p.cost_cap).toOption.isNone ||
        (p.direction != "gte" && p.direction != "lte" && p.direction != "external") then
      throw (diag event.event_id p.identity.id "rule" "exact threshold, cost cap and comparator direction are required")
    if ((parseDecimal p.cost_cap).toOption.get!).numerator < 0 then
      throw (diag event.event_id p.identity.id "cost_cap" "cost cap cannot be negative")
    return { state with protocols := state.protocols.push p }
  | "run_started" =>
    let r : Run ← decodePayload event
    let state ← withIdentity state event r.identity
    let protocol ← match findProtocol state r.protocol_ref with
      | some protocol => pure protocol
      | none => throw (diag event.event_id r.identity.id "missing_protocol" "run references no frozen protocol")
    if event.recorded_at < protocol.frozen_at then
      throw (diag event.event_id r.identity.id "run_time" "run is dated before protocol freeze")
    if r.input_ref.isEmpty then
      throw (diag event.event_id r.identity.id "run" "input reference is required")
    return { state with runs := state.runs.push r }
  | "artifact_registered" =>
    let a : ArtifactRef ← decodePayload event
    let state ← withIdentity state event a.identity
    if !(isSha256 a.digest) || a.media_type.isEmpty then
      throw (diag event.event_id a.identity.id "artifact" "lowercase sha256 digest and media type are required")
    return { state with artifacts := state.artifacts.push a }
  | "observation_recorded" =>
    let o : Observation ← decodePayload event
    let state ← withIdentity state event o.identity
    let run ← match findRun state o.run_ref with
      | some run => pure run
      | none => throw (diag event.event_id o.identity.id "missing_run" "observation references no run")
    let protocol ← match findProtocol state run.protocol_ref with
      | some protocol => pure protocol
      | none => throw (diag event.event_id o.identity.id "missing_protocol" "run protocol is missing")
    unless state.artifacts.any (·.identity.id == o.artifact_ref) do
      throw (diag event.event_id o.identity.id "missing_artifact" "observation references no artifact")
    if o.metric_id != protocol.metric_id || o.unit != protocol.unit then
      throw (diag event.event_id o.identity.id "metric_unit" "observation metric or unit differs from frozen protocol")
    if !(validTimestamp o.observed_at) || o.observed_at != event.recorded_at || o.observed_at < protocol.frozen_at then
      throw (diag event.event_id o.identity.id "observation_time" "observation is before freeze or its time differs from event")
    if o.status == "measured" then
      unless o.value.isSome && (parseDecimal o.value.get!).isOk do
        throw (diag event.event_id o.identity.id "value" "measured observation requires an exact decimal")
    else if o.status == "unknown" || o.status == "technical_error" then
      if o.value.isSome then throw (diag event.event_id o.identity.id "value" "unknown or technical error cannot carry a measurement")
    else throw (diag event.event_id o.identity.id "status" "invalid observation status")
    return { state with observations := state.observations.push o }
  | "cost_recorded" =>
    let c : CostEntry ← decodePayload event
    let state ← withIdentity state event c.identity
    let run ← match findRun state c.run_ref with
      | some run => pure run
      | none => throw (diag event.event_id c.identity.id "missing_run" "cost references no run")
    if (parseDecimal c.amount).toOption.isNone || c.category.isEmpty || c.unit.isEmpty ||
        c.source.isEmpty || c.coverage.isEmpty then
      throw (diag event.event_id c.identity.id "cost" "cost requires category, exact amount, unit, source and coverage")
    if ((parseDecimal c.amount).toOption.get!).numerator < 0 then
      throw (diag event.event_id c.identity.id "cost" "cost cannot be negative")
    let protocol ← match findProtocol state run.protocol_ref with
      | some protocol => pure protocol
      | none => throw (diag event.event_id c.identity.id "missing_protocol" "run protocol is missing")
    -- The cap belongs to the frozen protocol, not to an individual run.
    -- A partial coverage amount is still known cost and a lower bound.
    if c.unit == protocol.cost_unit then
      let mut total : Decimal := { numerator := 0, places := 0 }
      for prior in state.costs do
        if prior.unit == c.unit then
          if let some priorRun := findRun state prior.run_ref then
            if priorRun.protocol_ref == protocol.identity.id then
              total := addDecimal total ((parseDecimal prior.amount).toOption.get!)
      total := addDecimal total ((parseDecimal c.amount).toOption.get!)
      if compareDecimal total ((parseDecimal protocol.cost_cap).toOption.get!) == .gt then
        throw (diag event.event_id c.identity.id "cost_cap_exceeded" "recorded protocol cost exceeds declared cap")
    return { state with costs := state.costs.push c }
  | "assessment_recorded" =>
    let a : Assessment ← decodePayload event
    let state ← withIdentity state event a.identity
    let protocol ← match findProtocol state a.protocol_ref with
      | some protocol => pure protocol
      | none => throw (diag event.event_id a.identity.id "missing_protocol" "assessment references no frozen protocol")
    if a.observation_refs.isEmpty ||
        (protocol.direction != "external" && a.observation_refs.size != 1) then
      throw (diag event.event_id a.identity.id "observation_count" "exact rule needs one observation; external rule needs at least one")
    let mut allMeasured := true
    let mut selected : Option Observation := none
    let mut seenRefs : Array String := #[]
    for observationRef in a.observation_refs do
      if seenRefs.contains observationRef then
        throw (diag event.event_id a.identity.id "duplicate_observation_ref" "assessment repeats an observation")
      seenRefs := seenRefs.push observationRef
      let observation ← match findObservation state observationRef with
        | some observation => pure observation
        | none => throw (diag event.event_id a.identity.id "missing_observation" "assessment references no prior observation")
      let run ← match findRun state observation.run_ref with
        | some run => pure run
        | none => throw (diag event.event_id a.identity.id "missing_run" "assessment observation run is missing")
      if run.protocol_ref != protocol.identity.id then
        throw (diag event.event_id a.identity.id "protocol_mismatch" "assessment and observation refer to different protocols")
      if observation.observed_at > event.recorded_at then
        throw (diag event.event_id a.identity.id "future_observation" "observation is later than assessment")
      if observation.status != "measured" then allMeasured := false
      if selected.isNone then selected := some observation
    let observation ← match selected with
      | some observation => pure observation
      | none => throw (diag event.event_id a.identity.id "observation_count" "assessment has no observation")
    let expected ← if protocol.direction == "external" then
      pure (if allMeasured then "external_unverified" else "undetermined") else
      match assessExact protocol observation with
      | .ok verdict => pure verdict
      | .error message => throw (diag event.event_id a.identity.id "rule" message)
    let rule := if protocol.direction == "external" then "external" else "exact_v0"
    if a.rule_used != rule || a.verdict != expected then
      throw (diag event.event_id a.identity.id "verdict" s!"expected {expected} from {rule}")
    return { state with assessments := state.assessments.push a }
  | "decision_recorded" =>
    let d : PromotionDecision ← decodePayload event
    let state ← withIdentity state event d.identity
    let _assessment ← match findAssessment state d.assessment_ref with
      | some assessment => pure assessment
      | none => throw (diag event.event_id d.identity.id "missing_assessment" "decision references no prior assessment")
    if (findTime state d.assessment_ref).getD "" > event.recorded_at then
      throw (diag event.event_id d.identity.id "future_assessment" "assessment is later than decision")
    if d.result == "promote" && (promotionEvidence state d).isNone then
      throw (diag event.event_id d.identity.id "promotion_without_pass" "promotion requires prior passing evidence on a frozen protocol")
    if d.result == "override" && d.reason.trimAscii.toString.isEmpty then
      throw (diag event.event_id d.identity.id "override_reason" "override requires a reason")
    unless #["promote", "reject", "defer", "override"].contains d.result do
      throw (diag event.event_id d.identity.id "decision" "invalid decision result")
    return { state with decisions := state.decisions.push d }
  | "formal_claim_declared" =>
    let f : FormalClaimRef ← decodePayload event
    let state ← withIdentity state event f.identity
    if f.declaration.isEmpty || f.statement.isEmpty || f.toolchain.isEmpty then
      throw (diag event.event_id f.identity.id "formal_claim" "declaration, statement and toolchain are required")
    -- Imported status has no authority. Only a local theorem inspector can attest it.
    return { state with formal_claims := state.formal_claims.push { f with status := "declared" } }
  | "relation_recorded" =>
    let r : Relation ← decodePayload event
    unless hasObject state r.source_ref && hasObject state r.target_ref do
      throw (diag event.event_id r.identity.id "missing_relation_ref" "relation endpoint must be a prior object")
    unless #["provenance", "support", "contradiction", "prerequisite", "formal_implication"].contains r.kind do
      throw (diag event.event_id r.identity.id "relation_kind" "invalid relation kind")
    for ref in #[r.source_ref, r.target_ref] do
      if let some recordedAt := findTime state ref then
        if recordedAt > event.recorded_at then
          throw (diag event.event_id r.identity.id "relation_time" "relation endpoint is dated after the relation")
    let state ← withIdentity state event r.identity
    return { state with relations := state.relations.push r }
  | "dependency_gate_recorded" =>
    let g : DependencyGate ← decodePayload event
    if g.member_refs.size < 2 then
      throw (diag event.event_id g.identity.id "gate_members" "gate requires at least two distinct members")
    unless #["all_of", "any_of"].contains g.operator do
      throw (diag event.event_id g.identity.id "gate_operator" "gate operator must be all_of or any_of")
    unless #["support", "prerequisite"].contains g.kind do
      throw (diag event.event_id g.identity.id "gate_kind" "gate kind must be support or prerequisite")
    let mut seen : Array String := #[]
    for member in g.member_refs do
      if member == g.target_ref || seen.contains member then
        throw (diag event.event_id g.identity.id "gate_members" "gate members must be unique and differ from the target")
      seen := seen.push member
    unless hasObject state g.target_ref && g.member_refs.all (hasObject state) do
      throw (diag event.event_id g.identity.id "missing_gate_ref" "gate target and members must be prior objects")
    for ref in (#[g.target_ref] ++ g.member_refs) do
      if let some recordedAt := findTime state ref then
        if recordedAt > event.recorded_at then
          throw (diag event.event_id g.identity.id "gate_time" "gate reference is dated after the gate")
    let state ← withIdentity state event g.identity
    return { state with dependency_gates := state.dependency_gates.push g }
  | "source_recorded" =>
    let record : SourceRecord ← decodePayload event
    if event.audience != "owner" || record.identity.audience != "owner" then
      throw (diag event.event_id record.identity.id "source_audience" "source records must remain owner-only")
    let state ← withIdentity state event record.identity
    let raw ← match Json.parse record.raw_json with
      | .ok value => pure value
      | .error _ => throw (diag event.event_id record.identity.id "source_record" "source JSON does not parse")
    if !(#["manifest", "protocol", "event"].contains record.source_role) ||
        !(isSha256 record.canonical_sha256) || raw.getObj?.toOption.isNone then
      throw (diag event.event_id record.identity.id "source_record" "source role, canonical digest and JSON object are required")
    return { state with source_records := state.source_records.push record }
  | _ => throw (diag event.event_id "" "unknown_event" s!"unknown event kind {event.kind}")

private def jsonAt (value : Json) (path : List String) : Option Json :=
  path.foldl (fun current key => current.bind (fun item => (item.getObjVal? key).toOption)) (some value)

private def stringAt (value : Json) (path : List String) : Option String :=
  (jsonAt value path).bind (fun item => (fromJson? item : Except String String).toOption)

private def natAt (value : Json) (path : List String) : Option Nat :=
  (jsonAt value path).bind (fun item => (fromJson? item : Except String Nat).toOption)

/-- Cross-file source bindings, independent of the external evaluator's algorithm.
    Canonical SHA values are supplied by the adapter; Lean checks their links,
    not the cryptographic computation. -/
def validateSourceTrace (state : State) : Except Diagnostic Unit := do
  let manifests := state.source_records.filter (·.source_role == "manifest")
  let protocols := state.source_records.filter (·.source_role == "protocol")
  let records := state.source_records.filter (·.source_role == "event")
  if manifests.size != 1 || protocols.size != 1 || records.isEmpty then
    throw (diag "" "" "source_documents" "one manifest, one protocol and source events are required")
  let manifest ← match manifests[0]? with
    | some value => pure value
    | none => throw (diag "" "" "source_documents" "manifest is missing")
  let protocol ← match protocols[0]? with
    | some value => pure value
    | none => throw (diag "" "" "source_documents" "protocol is missing")
  let manifestRaw ← match Json.parse manifest.raw_json with
    | .ok value => pure value
    | .error _ => throw (diag "" manifest.identity.id "source_manifest" "manifest JSON does not parse")
  let attempt ← match stringAt manifestRaw ["attempt_id"] with
    | some value => pure value
    | none => throw (diag "" manifest.identity.id "source_manifest" "attempt_id is missing")
  let mut sourceIds : Array String := #[]
  let mut predictions : Array (String × Json) := #[]
  let mut observationCount := 0
  let mut expectedObservations : Array String := #[]
  let mut freezeCount := 0
  let mut completionCount := 0
  for index in [:records.size] do
    let record ← match records[index]? with
      | some value => pure value
      | none => throw (diag "" "" "source_documents" "source event is missing")
    let raw ← match Json.parse record.raw_json with
      | .ok value => pure value
      | .error _ => throw (diag "" record.identity.id "source_event" "source event JSON does not parse")
    let sourceId ← match stringAt raw ["event_id"] with
      | some value => pure value
      | none => throw (diag "" record.identity.id "source_event" "event_id is missing")
    if sourceIds.contains sourceId then
      throw (diag sourceId record.identity.id "source_duplicate_event" "source event ID is repeated")
    sourceIds := sourceIds.push sourceId
    if natAt raw ["sequence"] != some (index + 1) then
      throw (diag sourceId record.identity.id "source_sequence" "source sequence is not contiguous")
    if stringAt raw ["attempt_id"] != some attempt then
      throw (diag sourceId record.identity.id "source_attempt" "source event belongs to another attempt")
    let kind ← match stringAt raw ["type"] with
      | some value => pure value
      | none => throw (diag sourceId record.identity.id "source_event" "type is missing")
    let payload ← match jsonAt raw ["payload"] with
      | some value => pure value
      | none => throw (diag sourceId record.identity.id "source_event" "payload is missing")
    if kind == "protocol_frozen" then
      freezeCount := freezeCount + 1
      if index != 0 || freezeCount != 1 then
        throw (diag sourceId record.identity.id "source_second_freeze" "exactly one first freeze is allowed")
      let freezeHash := stringAt payload ["definition_sha256"]
      let manifestHash := stringAt manifestRaw ["provenance", "definition_sha256"]
      if freezeHash.isNone || freezeHash != manifestHash ||
          freezeHash != some ((protocol.canonical_sha256.drop 7).toString) then
        throw (diag sourceId record.identity.id "source_protocol_digest" "frozen, manifest and protocol digests differ")
      unless state.protocols.any (·.identity.id == "protocol:" ++ sourceId) do
        throw (diag sourceId record.identity.id "source_projection" "typed protocol does not name the source freeze")
    else if kind == "prediction_frozen" then
      let hash ← match stringAt payload ["prediction_sha256"] with
        | some value => pure value
        | none => throw (diag sourceId record.identity.id "source_prediction" "prediction hash is missing")
      if predictions.any (·.fst == hash) then
        throw (diag sourceId record.identity.id "source_prediction" "prediction hash is repeated")
      predictions := predictions.push (hash, payload)
    else if kind == "observation_recorded" then
      observationCount := observationCount + 1
      expectedObservations := expectedObservations.push ("observation:" ++ sourceId)
      let hash ← match stringAt payload ["prediction_sha256"] with
        | some value => pure value
        | none => throw (diag sourceId record.identity.id "source_prediction_ref" "observation has no prediction hash")
      let prediction ← match (predictions.find? (·.fst == hash)).map (·.snd) with
        | some value => pure value
        | none => throw (diag sourceId record.identity.id "source_prediction_ref" "observation has no prior prediction")
      for key in ["observation_id", "phase", "condition"] do
        if jsonAt payload [key] != jsonAt prediction [key] || (jsonAt payload [key]).isNone then
          throw (diag sourceId record.identity.id "source_prediction_ref" s!"{key} differs from frozen prediction")
      let typed ← match findObservation state ("observation:" ++ sourceId) with
        | some value => pure value
        | none => throw (diag sourceId record.identity.id "source_projection" "typed observation is missing")
      if stringAt payload ["units"] != some typed.unit then
        throw (diag sourceId record.identity.id "source_projection" "typed observation unit differs from source")
      let sourceValue ← match jsonAt payload ["observation"] with
        | some value => pure value
        | none => throw (diag sourceId record.identity.id "source_projection" "source observation value is missing")
      let expectedValue := if sourceValue == Json.null then none else some sourceValue.compress
      if typed.value != expectedValue ||
          typed.status != (if sourceValue == Json.null then "unknown" else "measured") then
        throw (diag sourceId record.identity.id "source_projection" "typed observation value differs from source")
    else if kind == "discrimination_completed" then
      completionCount := completionCount + 1
      if completionCount != 1 || index + 1 != records.size then
        throw (diag sourceId record.identity.id "source_completion" "completion must be unique and final")
      let result ← match jsonAt manifestRaw ["result", "discrimination"] with
        | some value => pure value
        | none => throw (diag sourceId record.identity.id "source_result" "manifest result is missing")
      let sourceChoice := stringAt payload ["decision"]
      unless sourceChoice == some "H0" || sourceChoice == some "H1" ||
          sourceChoice == some "neither" || sourceChoice == some "abstain" do
        throw (diag sourceId record.identity.id "source_decision" "completion decision is outside the source choice set")
      for key in ["decision", "observations_used", "planning_cpu_seconds", "posterior_model_probabilities"] do
        if jsonAt payload [key] != jsonAt result [key] || (jsonAt payload [key]).isNone then
          throw (diag sourceId record.identity.id "source_decision_provenance" s!"completion {key} differs from manifest result")
      if natAt payload ["observations_used"] != some observationCount then
        throw (diag sourceId record.identity.id "source_observation_count" "completion count differs from recorded observations")
    else
      throw (diag sourceId record.identity.id "source_event_kind" s!"unsupported source event {kind}")
  if freezeCount != 1 || completionCount != 1 then
    throw (diag "" "" "source_incomplete" "freeze or completion is missing")
  if state.protocols.size != 1 || state.observations.size != observationCount ||
      state.assessments.size != 1 || state.decisions.size != 1 then
    throw (diag "" "" "source_projection" "typed dossier does not cover all source observations")
  let represented := state.observations.map (·.identity.id)
  if represented != expectedObservations then
    throw (diag "" "" "source_projection" "typed observations omit or reorder source events")
  let assessment ← match state.assessments[0]? with
    | some value => pure value
    | none => throw (diag "" "" "source_projection" "assessment is missing")
  if assessment.observation_refs != represented then
    throw (diag "" assessment.identity.id "source_projection" "assessment omits or reorders source observations")
  let decision ← match state.decisions[0]? with
    | some value => pure value
    | none => throw (diag "" "" "source_projection" "typed decision is missing")
  let expectedDecision ← match stringAt manifestRaw ["scientific_decision"] with
    | some "keep" => pure "override"
    | some "discard" => pure "reject"
    | some "inconclusive" => pure "defer"
    | _ => throw (diag "" manifest.identity.id "source_decision" "unsupported source scientific decision")
  if decision.result != expectedDecision || decision.assessment_ref != assessment.identity.id then
    throw (diag "" decision.identity.id "source_projection" "typed decision differs from source scientific decision")

def replay (caseFile : CaseFile) (count : Nat := caseFile.events.size) : Except Diagnostic State := do
  if !(caseFile.schema_version == "0.1.0" && caseFile.semantics_version == "0.1.0") &&
      !(caseFile.schema_version == "0.2.0" && caseFile.semantics_version == "0.2.0") &&
      !(caseFile.schema_version == "0.3.0" && caseFile.semantics_version == "0.3.0") then
    throw (diag "" caseFile.case_id "version" "unsupported schema or semantics version; no implicit migration")
  if caseFile.case_id.isEmpty || caseFile.version == 0 || caseFile.domain.isEmpty || caseFile.provenance.isEmpty ||
      !validAudience caseFile.audience ||
      caseFile.question.identity.id.isEmpty || caseFile.claim.identity.id.isEmpty ||
      caseFile.question.identity.id == caseFile.claim.identity.id ||
      caseFile.question.identity.version == 0 || caseFile.claim.identity.version == 0 ||
      caseFile.question.identity.domain.isEmpty || caseFile.claim.identity.domain.isEmpty ||
      caseFile.question.identity.provenance.isEmpty || caseFile.claim.identity.provenance.isEmpty then
    throw (diag "" caseFile.case_id "case" "case, question, claim, version and provenance are required")
  if !validAudience caseFile.question.identity.audience || !validAudience caseFile.claim.identity.audience then
    throw (diag "" caseFile.case_id "audience" "question and claim audiences must be agent or owner")
  if count > caseFile.events.size then
    throw (diag "" caseFile.case_id "prefix" "snapshot prefix exceeds event count")
  let mut state : State := { object_ids := (#[caseFile.question.identity.id, caseFile.claim.identity.id]), claim_id := caseFile.claim.identity.id }
  for event in caseFile.events.extract 0 count do
    if caseFile.schema_version == "0.1.0" && event.kind == "source_recorded" then
      throw (diag event.event_id "" "version" "source records require schema 0.2.0")
    if caseFile.schema_version != "0.3.0" && event.kind == "dependency_gate_recorded" then
      throw (diag event.event_id "" "version" "dependency gates require schema 0.3.0")
    state ← step state event
  if count == caseFile.events.size && !state.source_records.isEmpty then
    validateSourceTrace state
  return state

end Slean

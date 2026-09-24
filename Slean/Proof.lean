import Slean.Core

namespace Slean
open Lean

/-- Exact elaborated expression text from the pinned Lean 4.28.0 toolchain.
    The build checks this against the local theorem, rather than trusting JSON. -/
def checkedStatement : String :=
  "forall (state : Slean.State) (decision : Slean.PromotionDecision), (Eq.{1} Bool (Option.isSome.{0} (Prod.{0, 0} Slean.FrozenProtocol Slean.Observation) (Slean.promotionEvidence state decision)) Bool.true) -> (Exists.{1} Slean.Assessment (fun (assessment : Slean.Assessment) => Exists.{1} Slean.FrozenProtocol (fun (protocol : Slean.FrozenProtocol) => Exists.{1} Slean.Run (fun (run : Slean.Run) => Exists.{1} Slean.Observation (fun (observation : Slean.Observation) => Exists.{1} String (fun (observationRef : String) => And (Eq.{1} (Option.{0} Slean.Assessment) (Slean.findAssessment state (Slean.PromotionDecision.assessment_ref decision)) (Option.some.{0} Slean.Assessment assessment)) (And (Eq.{1} String (Slean.Assessment.verdict assessment) \"pass\") (And (Eq.{1} (Option.{0} String) (GetElem?.getElem?.{0, 0, 0} (Array.{0} String) Nat String (fun (xs : Array.{0} String) (i : Nat) => LT.lt.{0} Nat instLTNat i (Array.size.{0} String xs)) (Array.instGetElem?NatLtSize.{0} String) (Slean.Assessment.observation_refs assessment) (OfNat.ofNat.{0} Nat 0 (instOfNatNat 0))) (Option.some.{0} String observationRef)) (And (Eq.{1} (Option.{0} Slean.Observation) (Slean.findObservation state observationRef) (Option.some.{0} Slean.Observation observation)) (And (Eq.{1} (Option.{0} Slean.Run) (Slean.findRun state (Slean.Observation.run_ref observation)) (Option.some.{0} Slean.Run run)) (And (Eq.{1} (Option.{0} Slean.FrozenProtocol) (Slean.findProtocol state (Slean.Run.protocol_ref run)) (Option.some.{0} Slean.FrozenProtocol protocol)) (Eq.{1} String (Slean.Identity.id (Slean.FrozenProtocol.identity protocol)) (Slean.Assessment.protocol_ref assessment)))))))))))))"

def checkedDeclaration : String := "Slean.promotionEvidence_has_frozen_observation"
def checkedToolchain : String := "leanprover/lean4:v4.28.0"

/-- Direct project declarations in the compiled proof term. Lean library
    dependencies are identified by the pinned toolchain. -/
def checkedDependencies : Array String := #[
  "Slean.State", "Slean.PromotionDecision", "Slean.FrozenProtocol",
  "Slean.Observation", "Slean.promotionEvidence", "Slean.Assessment",
  "Slean.findAssessment", "Slean.PromotionDecision.assessment_ref",
  "Slean.Run", "Slean.Assessment.verdict", "Slean.Assessment.observation_refs",
  "Slean.findObservation", "Slean.findRun", "Slean.Observation.run_ref",
  "Slean.findProtocol", "Slean.Run.protocol_ref", "Slean.Identity.id",
  "Slean.FrozenProtocol.identity", "Slean.Assessment.protocol_ref"]

run_meta do
  let name := ``Slean.promotionEvidence_has_frozen_observation
  let info ← getConstInfo name
  unless info matches .thmInfo _ do
    throwError "formal claim is not a theorem"
  let expected ← Lean.Meta.evalExpr String (mkConst ``String) (mkConst ``Slean.checkedStatement)
  unless toString info.type == expected do
    throwError "formal statement changed: update the reviewed claim and semantics version"
  let dependencies : List Name := match info with
    | .thmInfo thm =>
      thm.value.getUsedConstants.toList.filter (fun (dep : Name) => dep.toString.startsWith "Slean.")
    | _ => []
  let pinned ← Lean.Meta.evalExpr (Array String) (mkApp (mkConst ``Array [Level.zero]) (mkConst ``String))
    (mkConst ``Slean.checkedDependencies)
  unless dependencies.map toString == pinned.toList do
    throwError "formal proof dependencies changed: update the reviewed dependency pin"
  let axioms ← collectAxioms name
  unless axioms.toList.all (fun ax => ax == ``propext || ax == ``Quot.sound) do
    throwError "formal claim uses sorry or an unapproved axiom: {axioms.toList}"

def formalAttestationEligible (claim : FormalClaimRef) : Bool :=
  if claim.declaration == checkedDeclaration &&
      claim.statement == checkedStatement &&
      claim.toolchain == checkedToolchain then true else false

def proofReceipt (claim : FormalClaimRef) : Json :=
  let eligible := formalAttestationEligible claim
  Json.mkObj [
    ("claim_id", toJson claim.identity.id),
    -- A local match has no source revision or build identity. Only the clean
    -- build attester can promote this receipt to kernel_checked.
    ("status", toJson "declared"),
    ("attestation_eligible", toJson eligible),
    ("declaration", toJson claim.declaration),
    ("elaborated_statement", toJson claim.statement),
    ("toolchain", toJson claim.toolchain),
    ("dependencies", toJson (if eligible then checkedDependencies else #[])),
    ("axioms", toJson (if eligible then #["propext", "Quot.sound"] else #[])),
    ("verifier", toJson (if eligible then
      "local theorem pin matches; exact-build attestation is required for kernel_checked" else
      "unverified declaration"))]

end Slean

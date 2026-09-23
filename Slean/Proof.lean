import Slean.Core

namespace Slean
open Lean

/-- Exact elaborated expression text from the pinned Lean 4.28.0 toolchain.
    The build checks this against the local theorem, rather than trusting JSON. -/
def checkedStatement : String :=
  "forall (state : Slean.State) (decision : Slean.PromotionDecision), (Eq.{1} Bool (Option.isSome.{0} (Prod.{0, 0} Slean.FrozenProtocol Slean.Observation) (Slean.promotionEvidence state decision)) Bool.true) -> (Exists.{1} Slean.Assessment (fun (assessment : Slean.Assessment) => Exists.{1} Slean.FrozenProtocol (fun (protocol : Slean.FrozenProtocol) => Exists.{1} Slean.Run (fun (run : Slean.Run) => Exists.{1} Slean.Observation (fun (observation : Slean.Observation) => Exists.{1} String (fun (observationRef : String) => And (Eq.{1} (Option.{0} Slean.Assessment) (Slean.findAssessment state (Slean.PromotionDecision.assessment_ref decision)) (Option.some.{0} Slean.Assessment assessment)) (And (Eq.{1} String (Slean.Assessment.verdict assessment) \"pass\") (And (Eq.{1} (Option.{0} String) (GetElem?.getElem?.{0, 0, 0} (Array.{0} String) Nat String (fun (xs : Array.{0} String) (i : Nat) => LT.lt.{0} Nat instLTNat i (Array.size.{0} String xs)) (Array.instGetElem?NatLtSize.{0} String) (Slean.Assessment.observation_refs assessment) (OfNat.ofNat.{0} Nat 0 (instOfNatNat 0))) (Option.some.{0} String observationRef)) (And (Eq.{1} (Option.{0} Slean.Observation) (Slean.findObservation state observationRef) (Option.some.{0} Slean.Observation observation)) (And (Eq.{1} (Option.{0} Slean.Run) (Slean.findRun state (Slean.Observation.run_ref observation)) (Option.some.{0} Slean.Run run)) (And (Eq.{1} (Option.{0} Slean.FrozenProtocol) (Slean.findProtocol state (Slean.Run.protocol_ref run)) (Option.some.{0} Slean.FrozenProtocol protocol)) (Eq.{1} String (Slean.Identity.id (Slean.FrozenProtocol.identity protocol)) (Slean.Assessment.protocol_ref assessment)))))))))))))"

def checkedDeclaration : String := "Slean.promotionEvidence_has_frozen_observation"
def checkedToolchain : String := "leanprover/lean4:v4.28.0"

run_meta do
  let name := ``Slean.promotionEvidence_has_frozen_observation
  let info ← getConstInfo name
  unless info matches .thmInfo _ do
    throwError "formal claim is not a theorem"
  let expected ← Lean.Meta.evalExpr String (mkConst ``String) (mkConst ``Slean.checkedStatement)
  unless toString info.type == expected do
    throwError "formal statement changed: update the reviewed claim and semantics version"
  let axioms ← collectAxioms name
  unless axioms.toList.all (fun ax => ax == ``propext || ax == ``Quot.sound) do
    throwError "formal claim uses sorry or an unapproved axiom: {axioms.toList}"

def formalStatus (claim : FormalClaimRef) : String :=
  if claim.declaration == checkedDeclaration &&
      claim.statement == checkedStatement &&
      claim.toolchain == checkedToolchain then "kernel_checked" else "declared"

def proofReceipt (claim : FormalClaimRef) : Json :=
  let status := formalStatus claim
  Json.mkObj [
    ("claim_id", toJson claim.identity.id),
    ("status", toJson status),
    ("declaration", toJson claim.declaration),
    ("elaborated_statement", toJson claim.statement),
    ("toolchain", toJson claim.toolchain),
    ("axioms", toJson (if status == "kernel_checked" then #["propext", "Quot.sound"] else #[])),
    ("verifier", toJson (if status == "kernel_checked" then
      "local Lean build and Slean statement/axiom pin; exporter is not kernel-verified" else
      "unverified declaration"))]

end Slean

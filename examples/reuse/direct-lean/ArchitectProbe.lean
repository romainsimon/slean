import DirectReuse
import Architect

open scoped ContDiff
open ClassicalMechanics

set_option autoImplicit false

-- Annotate existing declarations without copying their proofs.
attribute [blueprint "upstream-energy"]
  ClassicalMechanics.HarmonicOscillator.energy_conservation_of_equationOfMotion'
attribute [blueprint "reused-energy"] DirectReuse.energy_at_two_times

namespace ArchitectProbe

@[blueprint "suppressed-edge" (proofUses := [-DirectReuse.energy_at_two_times])]
theorem suppressedEdge
    (system : HarmonicOscillator)
    (trajectory : Time → EuclideanSpace ℝ (Fin 1))
    (smooth : ContDiff ℝ ∞ trajectory)
    (motion : system.EquationOfMotion trajectory)
    (first second : Time) :
    system.energy trajectory first = system.energy trajectory second := by
  exact DirectReuse.energy_at_two_times system trajectory smooth motion first second

-- Deliberately invalid evidence fixtures. Nothing imports these as science.
axiom inventedEvidence : False

@[blueprint "unapproved-axiom"]
theorem unapprovedAxiom : False := inventedEvidence

@[blueprint "unfinished-plan"]
theorem unfinishedPlan : True := by sorry

@[blueprint "inherits-unfinished-plan"]
theorem inheritsUnfinishedPlan : True := unfinishedPlan

@[blueprint "suppressed-sorry" (proofUses := [-sorryAx])]
theorem suppressedSorry : False := by sorry

end ArchitectProbe

open Lean Elab Command in
run_cmd do
  let mut reports : Array Json := #[]
  for name in #[
      ``ClassicalMechanics.HarmonicOscillator.energy_conservation_of_equationOfMotion',
      ``DirectReuse.energy_at_two_times,
      ``ArchitectProbe.suppressedEdge,
      ``ArchitectProbe.unapprovedAxiom,
      ``ArchitectProbe.unfinishedPlan,
      ``ArchitectProbe.inheritsUnfinishedPlan,
      ``ArchitectProbe.suppressedSorry] do
    let some node := Architect.blueprintExt.find? (← getEnv) name
      | throwError "missing probe annotation: {name}"
    let info ← getConstInfo name
    let directProof := match info with
      | .thmInfo theoremInfo => theoremInfo.value.getUsedConstants
      | _ => #[]
    let (collectedStatement, collectedProof) ← Architect.collectUsed name
    let (shownStatement, shownProof) ← node.inferUses
    let axioms ← collectAxioms name
    let names := fun (values : Array Name) =>
      values.map Name.toString |>.qsort (· < ·)
    reports := reports.push <| Json.mkObj [
      ("name", toJson name.toString),
      ("directStatement", toJson <| names info.type.getUsedConstants),
      ("directProof", toJson <| names directProof),
      ("collectedStatement", toJson <| names collectedStatement.toArray),
      ("collectedProof", toJson <| names collectedProof.toArray),
      ("shownStatement", toJson shownStatement.uses),
      ("shownProof", toJson shownProof.uses),
      ("statementLeanOk", toJson shownStatement.leanOk),
      ("proofLeanOk", toJson shownProof.leanOk),
      ("axioms", toJson <| names axioms),
      ("rawStatementUses", toJson <| names node.statement.uses),
      ("rawProofUses", toJson <| names (node.proof.map (·.uses) |>.getD #[]))]
  logInfo m!"ARCHITECT_PROBE {Json.arr reports |>.compress}"

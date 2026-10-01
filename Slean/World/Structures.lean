import Slean.World.CellularAutomaton

/-!
# Localised structures: particles, gliders and oscillators

A *travelling structure* is a finite pattern on a quiescent background that,
after `t` steps, reappears translated by `d` cells. A glider is a moving one;
an oscillator is a standing one. Finding them is a combinatorial search with no
known closed-form recipe. A specific witness, however, is a finite computation
that the kernel can check.

Claims are stated on a cyclic lattice: the pattern, padded with the background
state on both sides, comes back to itself shifted by `d` after `t` steps.
-/

namespace Slean

/-- One step of a finite cyclic configuration given as a list of cells. -/
def CA.stepList (A : CA) (l : List Nat) : List Nat :=
  (List.range l.length).map fun i => A.loc (read (cfg l) l.length i (A.s + 1))

/-- `t` steps of a finite cyclic configuration. -/
def CA.iterList (A : CA) : Nat → List Nat → List Nat
  | 0, l => l
  | t + 1, l => A.iterList t (A.stepList l)

/-- The configuration translated so that new cell `i` is old cell `i + d`. -/
def rotate (l : List Nat) (d : Nat) : List Nat :=
  (List.range l.length).map fun i => cfg l ((i + d) % l.length)

/-- `l` comes back after `t` steps, translated by `d` cells. -/
def Travels (A : CA) (l : List Nat) (t d : Nat) : Prop :=
  A.iterList t l = rotate l d

instance (A : CA) (l : List Nat) (t d : Nat) : Decidable (Travels A l t d) := by
  unfold Travels; infer_instance

/-- The step on lists agrees with the step on cyclic configurations. -/
theorem stepList_eq (A : CA) (l : List Nat) (i : Nat) (hi : i < l.length) :
    cfg (A.stepList l) i = A.step (cfg l) l.length i := by
  simp [CA.stepList, CA.step, cfg, hi]

end Slean

import DirectReuse
import ArchitectProbe
import SleanExport

open scoped ContDiff
open ClassicalMechanics

set_option autoImplicit false

namespace FormalExample

@[blueprint "consumer-energy"]
theorem energy_preserved
    (system : HarmonicOscillator)
    (trajectory : Time → EuclideanSpace ℝ (Fin 1))
    (smooth : ContDiff ℝ ∞ trajectory)
    (motion : system.EquationOfMotion trajectory)
    (first second : Time) :
    system.energy trajectory first = system.energy trajectory second := by
  exact DirectReuse.energy_at_two_times system trajectory smooth motion first second

-- The exporter must not depend on one scientific theorem or one type shape.
universe u
theorem identity_law {α : Sort u} (x : α) : (fun y => y) x = x := rfl

def double (x : Nat) : Nat := x + x

theorem «name.with.dots» : True := True.intro

end FormalExample

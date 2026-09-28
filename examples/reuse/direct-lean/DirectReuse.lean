import Physlib.ClassicalMechanics.HarmonicOscillator.Basic

open scoped ContDiff
open ClassicalMechanics

set_option autoImplicit false

/-!
An internal integration fixture, using Physlib directly without Slean.

The equation of motion and smoothness remain explicit hypotheses. This file
tests library reuse; it does not select Mutome's scientific research topic.
-/

namespace DirectReuse

theorem energy_at_two_times
    (system : HarmonicOscillator)
    (trajectory : Time → EuclideanSpace ℝ (Fin 1))
    (smooth : ContDiff ℝ ∞ trajectory)
    (motion : system.EquationOfMotion trajectory)
    (first second : Time) :
    system.energy trajectory first = system.energy trajectory second := by
  exact (system.energy_conservation_of_equationOfMotion' trajectory smooth motion first).trans
    (system.energy_conservation_of_equationOfMotion' trajectory smooth motion second).symm

end DirectReuse

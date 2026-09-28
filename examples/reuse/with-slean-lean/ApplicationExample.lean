import SleanExport
import DirectReuse

open scoped ContDiff
open ClassicalMechanics

set_option autoImplicit false

namespace ApplicationExample

theorem energy_with_obligation
    (system : HarmonicOscillator)
    (trajectory : Time → EuclideanSpace ℝ (Fin 1))
    (smooth : ContDiff ℝ ∞ trajectory)
    (motion : system.EquationOfMotion trajectory)
    (first second : Time) :
    system.energy trajectory first = system.energy trajectory second := by
  slean_apply DirectReuse.energy_at_two_times system trajectory smooth recording "energy-use"
  exact motion

theorem energy_with_all_arguments
    (system : HarmonicOscillator)
    (trajectory : Time → EuclideanSpace ℝ (Fin 1))
    (smooth : ContDiff ℝ ∞ trajectory)
    (motion : system.EquationOfMotion trajectory)
    (first second : Time) :
    system.energy trajectory first = system.energy trajectory second := by
  slean_apply DirectReuse.energy_at_two_times system trajectory smooth motion first second recording "energy-use"

end ApplicationExample

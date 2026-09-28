import ApplicationExample

open scoped ContDiff
open ClassicalMechanics

set_option autoImplicit false

theorem missing_motion
    (system : HarmonicOscillator)
    (trajectory : Time → EuclideanSpace ℝ (Fin 1))
    (smooth : ContDiff ℝ ∞ trajectory)
    (first second : Time) :
    system.energy trajectory first = system.energy trajectory second := by
  slean_apply DirectReuse.energy_at_two_times system trajectory smooth recording "missing-motion"

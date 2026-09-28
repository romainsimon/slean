import DirectReuse

open scoped ContDiff
open ClassicalMechanics

set_option autoImplicit false

-- Expected failure: smoothness alone does not supply the equation of motion.
example
    (system : HarmonicOscillator)
    (trajectory : Time → EuclideanSpace ℝ (Fin 1))
    (smooth : ContDiff ℝ ∞ trajectory)
    (first second : Time) :
    system.energy trajectory first = system.energy trajectory second := by
  exact DirectReuse.energy_at_two_times system trajectory smooth ?_ first second

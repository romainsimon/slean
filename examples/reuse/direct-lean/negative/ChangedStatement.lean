import DirectReuse

open scoped ContDiff
open ClassicalMechanics

set_option autoImplicit false

-- Expected failure: a proof of conservation cannot justify a different claim.
example
    (system : HarmonicOscillator)
    (trajectory : Time → EuclideanSpace ℝ (Fin 1))
    (smooth : ContDiff ℝ ∞ trajectory)
    (motion : system.EquationOfMotion trajectory)
    (first second : Time) :
    system.energy trajectory first = system.energy trajectory second + 1 := by
  exact DirectReuse.energy_at_two_times system trajectory smooth motion first second

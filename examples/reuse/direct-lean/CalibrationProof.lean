import Mathlib.Data.Real.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

set_option autoImplicit false

namespace CalibrationProof

-- Algebra under an assumed exact affine model; not a claim about a real sensor.
theorem inverse_exact (gain offset input : ℝ) (nonzero : gain ≠ 0) :
    (gain * input + offset - offset) / gain = input := by
  field_simp
  simp_all

-- The residual bound is assumed. Uncertainty in fitted parameters is not covered.
theorem inverse_residual_bound (gain offset input residual bound : ℝ)
    (nonzero : gain ≠ 0) (residual_bound : |residual| ≤ bound) :
    |(gain * input + offset + residual - offset) / gain - input| ≤ bound / |gain| := by
  have identity : (gain * input + offset + residual - offset) / gain - input = residual / gain := by
    field_simp
    ring
  rw [identity, abs_div]
  exact (div_le_div_iff_of_pos_right (abs_pos.mpr nonzero)).2 residual_bound

end CalibrationProof

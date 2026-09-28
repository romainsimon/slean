import CalibrationProof

set_option autoImplicit false

example (gain offset input residual bound : ℝ) (nonzero : gain ≠ 0) :
    |(gain * input + offset + residual - offset) / gain - input| ≤ bound / |gain| := by
  exact CalibrationProof.inverse_residual_bound gain offset input residual bound nonzero ?_

import CalibrationProof

set_option autoImplicit false

example (gain offset input : ℝ) : (gain * input + offset - offset) / gain = input := by
  exact CalibrationProof.inverse_exact gain offset input ?_

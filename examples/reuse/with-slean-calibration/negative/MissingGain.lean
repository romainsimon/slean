import SleanExport
import CalibrationProof

set_option autoImplicit false
example (gain offset input : ℝ) : (gain * input + offset - offset) / gain = input := by
  slean_apply CalibrationProof.inverse_exact gain offset input recording "missing-gain"

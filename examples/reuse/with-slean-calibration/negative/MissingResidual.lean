import SleanExport
import CalibrationProof
import Mathlib.Tactic.NormNum

set_option autoImplicit false
example (input residual : ℝ) :
    |((2 : ℝ) * input + 1/2 + residual - 1/2) / 2 - input| ≤ (1/50 : ℝ) / |2| := by
  slean_apply CalibrationProof.inverse_residual_bound 2 (1/2) input residual (1/50) (by norm_num) recording "missing-residual"

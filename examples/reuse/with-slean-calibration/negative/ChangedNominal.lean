import SleanExport
import CalibrationProof

-- Omitting the offset gives 4.25 mm; the conditional inverse cannot prove it.
example : (((2 : ℝ) * 4 + 1/2 - 1/2) / 2) = (17/4 : ℝ) := by
  slean_apply CalibrationProof.inverse_exact 2 (1/2) 4 (by norm_num) recording "wrong-nominal"

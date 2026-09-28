import SleanExport

namespace CaptureTest

theorem producer (n : Nat) : n = n := rfl

theorem whole (n : Nat) : n = n := by
  slean_apply producer n recording "whole"

theorem nested (n : Nat) : n = n ∧ n = n := by
  constructor
  · slean_apply producer n recording "left"
  · slean_apply producer n recording "right"

end CaptureTest

#slean_export_applications [CaptureTest.whole, CaptureTest.nested]
  to "_out/native-applications.json"

import Slean.Proof

axiom forbidden : False
theorem usesForbidden : True := False.elim forbidden
theorem withSorry : True := by sorry

-- The local receipt path only allows its pinned declaration. These examples
-- demonstrate the dependencies that a general proof importer must reject.
#print axioms usesForbidden
#print axioms withSorry

import Slean.World.Structures

/-!
# Packed tables

Large rule and density tables written as one natural number, `m` bits per
entry: entry `c` is `(T >>> (m * c)) % 2^m`. The kernel evaluates shifts and
remainders on big numbers natively, so a 1024-entry table costs one operation
per lookup instead of a walk down a list. The worlds and theorems are the same
as with list tables; only the encoding of the data changes.
-/

namespace Slean

/-- Entry `c` of a table packed with `m` bits per entry. -/
def field (m T c : Nat) : Nat := (T >>> (m * c)) % 2 ^ m

/-- A cellular automaton whose rule table is packed into `T`. -/
def packedCA (k s m T : Nat) : CA where
  k := k
  s := s
  loc := fun p => field m T (code k p)

/-- A packed table of integers, stored with an offset so every field is a natural number. -/
def packedFn (k m off T : Nat) (p : List Nat) : Int :=
  (field m T (code k p) : Int) - off

end Slean

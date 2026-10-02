import Slean.Packed

/-!
# Compact laws

A law is a short expression computing a world's rule from the cells of a
neighbourhood. The claim "this law *is* the rule" says the expression agrees
with the world on every neighbourhood. It is a finite statement, decided by the
kernel, and it is much stronger than any number of matching observations: it
identifies the mechanism.

Compactness is part of the claim's value, not of its truth: the engine accepts
a law only when its description is much shorter than the rule table, so copying
the table is not a law.
-/

namespace Slean

/-- Expressions over the cells of a neighbourhood. Arithmetic is on integers;
`mod` uses the non-negative remainder; `lookup` reads a small table, with `0`
outside it. -/
inductive Law where
  | cell (j : Nat)
  | const (c : Int)
  | add (a b : Law)
  | sub (a b : Law)
  | mul (a b : Law)
  | mod (a : Law) (m : Nat)
  | lookup (table : List Int) (a : Law)
  deriving Repr

/-- Value of a law on a neighbourhood (a list of cells). -/
def Law.eval : Law → List Nat → Int
  | .cell j, p => (p.getD j 0 : Int)
  | .const c, _ => c
  | .add a b, p => a.eval p + b.eval p
  | .sub a b, p => a.eval p - b.eval p
  | .mul a b, p => a.eval p * b.eval p
  | .mod a m, p => a.eval p % (m : Int)
  | .lookup t a, p => t.getD (a.eval p).toNat 0

/-- The law gives the world's rule on every neighbourhood. -/
def lawHolds (A : CA) (e : Law) : Bool :=
  (allPatterns A.k (A.s + 1)).all fun p => (A.loc p : Int) == e.eval p

/-- A checked law determines every step of the world: on any valid cyclic
configuration, the next state of every cell is the law applied to its
neighbourhood. -/
theorem step_eq_law (A : CA) (e : Law) (h : lawHolds A e = true)
    (n : Nat) (x : Nat → Nat) (hx : ∀ i, x i < A.k) (i : Nat) :
    (A.step x n i : Int) = e.eval (read x n i (A.s + 1)) := by
  have hall := List.all_eq_true.mp h
  have hp := hall (read x n i (A.s + 1))
    (mem_allPatterns A.k _ _ (read_length x n i _) (read_valid x A.k n hx i _))
  simp only [beq_iff_eq] at hp
  exact hp

end Slean

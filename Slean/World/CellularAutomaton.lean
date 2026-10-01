import Slean.Basic

/-!
# World: one-dimensional cellular automata on cyclic lattices

A cellular automaton is a local rule applied simultaneously to every cell.
Its exact definition here *is* the world: a simulator that disagrees with it
is wrong, so a phenomenon cannot come from a simulator defect.

## Conservation laws

A density `f` reads `w` consecutive cells. Its total on a configuration of
size `n` is `∑_{i<n} f(x_i … x_{i+w-1})`. The density is *conserved* when one
step never changes that total, for every lattice size and configuration.

A *flux certificate* is a local current `J` satisfying the discrete continuity
equation `f(step x)_i - f(x)_i = J_i - J_{i+1}` on every local pattern. It is a
finite object, so the kernel can check it exhaustively, and the theorem
`conserved_of_fluxCheck` turns it into conservation for **all** sizes.
-/

namespace Slean

/-- A one-dimensional cellular automaton with `k` states whose new cell value
depends on `s + 1` consecutive cells. Output cell `i` reads cells
`i, …, i+s`; this is the usual centred rule followed by a shift, which leaves
every total unchanged. -/
structure CA where
  k : Nat
  s : Nat
  loc : List Nat → Nat

/-- One synchronous update of a cyclic configuration of size `n`. -/
def CA.step (A : CA) (x : Nat → Nat) (n : Nat) : Nat → Nat :=
  fun i => A.loc (read x n i (A.s + 1))

/-- Total of a width-`w` density on a cyclic configuration of size `n`. -/
def total (f : List Nat → Int) (w : Nat) (x : Nat → Nat) (n : Nat) : Int :=
  sumRange (fun i => f (read x n i w)) n

/-- `f` is conserved by `A`: one step never changes its total, for every
lattice size and every valid configuration. -/
def Conserved (A : CA) (f : List Nat → Int) (w : Nat) : Prop :=
  ∀ (n : Nat) (x : Nat → Nat), (∀ i, x i < A.k) →
    total f w (A.step x n) n = total f w x n

/-- The cells of the next configuration over a window, computed from a
pattern of `w + s` current cells. -/
def stepPattern (loc : List Nat → Nat) (m : Nat) : List Nat → Nat → List Nat
  | _, 0 => []
  | p, w + 1 => loc (p.take m) :: stepPattern loc m (p.drop 1) w

theorem read_step (A : CA) (x : Nat → Nat) (n : Nat) :
    ∀ w i, read (A.step x n) n i w = stepPattern A.loc (A.s + 1) (read x n i (w + A.s)) w := by
  intro w
  induction w with
  | zero => intro i; rfl
  | succ w ih =>
    intro i
    have hlen : w + 1 + A.s = (w + A.s) + 1 := by omega
    have e1 : read (A.step x n) n i (w + 1)
        = A.loc (read x n (i % n) (A.s + 1)) :: read (A.step x n) n (i + 1) w := rfl
    rw [e1, read_mod, hlen]
    simp only [stepPattern]
    rw [read_take x n i (A.s + 1) _ (by omega), read_drop_one, ih]

/-- The local continuity equation for density `f` and current `J` on one
pattern of `w + s + 1` cells. -/
def continuityAt (A : CA) (f J : List Nat → Int) (w : Nat) (p : List Nat) : Bool :=
  f (stepPattern A.loc (A.s + 1) (p.take (w + A.s)) w) - f (p.take w)
    == J (p.take (w + A.s)) - J ((p.drop 1).take (w + A.s))

/-- Exhaustive check of the continuity equation on every local pattern. -/
def fluxCheck (A : CA) (f J : List Nat → Int) (w : Nat) : Bool :=
  (allPatterns A.k (w + A.s + 1)).all (continuityAt A f J w)

/-- **A checked flux certificate proves conservation for every lattice size.** -/
theorem conserved_of_fluxCheck (A : CA) (f J : List Nat → Int) (w : Nat)
    (h : fluxCheck A f J w = true) : Conserved A f w := by
  intro n x hx
  have hall := List.all_eq_true.mp h
  let G : Nat → Int := fun i => J (read x n i (w + A.s))
  have local_eq : ∀ i,
      f (read (A.step x n) n i w) - f (read x n i w) = G i - G (i + 1) := by
    intro i
    have hp := hall (read x n i (w + A.s + 1))
      (mem_allPatterns A.k _ _ (read_length x n i _) (read_valid x A.k n hx i _))
    simp only [continuityAt, beq_iff_eq] at hp
    rw [read_take x n i (w + A.s) _ (by omega), read_take x n i w _ (by omega),
      read_drop_one, List.take_of_length_le (by rw [read_length]; omega)] at hp
    rw [read_step]
    exact hp
  have hsum := sumRange_sub (fun i => f (read (A.step x n) n i w)) (fun i => f (read x n i w)) n
  rw [sumRange_congr _ _ local_eq, sumRange_telescope] at hsum
  have hper : G n = G 0 := by
    show J (read x n n (w + A.s)) = J (read x n 0 (w + A.s))
    rw [← read_periodic x n 0, Nat.zero_add]
  unfold total
  omega

/-- A concrete configuration on which the total changes refutes conservation. -/
theorem not_conserved_of_witness (A : CA) (f : List Nat → Int) (w : Nat)
    (l : List Nat) (hk : 0 < A.k) (hl : l.all (· < A.k) = true)
    (h : (total f w (A.step (cfg l) l.length) l.length != total f w (cfg l) l.length) = true) :
    ¬ Conserved A f w := by
  intro hc
  have := hc l.length (cfg l) (cfg_valid l A.k hk hl)
  simp [this] at h

/-- Elementary cellular automaton with Wolfram number `rule`
(two states, neighbourhood of three cells). -/
def eca (rule : Nat) : CA where
  k := 2
  s := 2
  loc := fun p => (rule >>> code 2 p) % 2

/-- Cellular automaton given by a full lookup table over `k` states. -/
def tableCA (k s : Nat) (t : List Nat) : CA where
  k := k
  s := s
  loc := fun p => t.getD (code k p) 0

end Slean

/-!
# Basic finite machinery

Cyclic configurations are functions `Nat → Nat` read modulo their size `n`.
Every world in Slean is built from these few definitions so that a claim
about a world is an ordinary Lean proposition, checked by the kernel.
-/

namespace Slean

/-- Cells `i, i+1, …, i+L-1` of a cyclic configuration of size `n`. -/
def read (x : Nat → Nat) (n i : Nat) : Nat → List Nat
  | 0 => []
  | L + 1 => x (i % n) :: read x n (i + 1) L

theorem read_length (x : Nat → Nat) (n : Nat) :
    ∀ i L, (read x n i L).length = L := by
  intro i L
  induction L generalizing i with
  | zero => rfl
  | succ L ih => simp [read, ih]

theorem read_take (x : Nat → Nat) (n : Nat) :
    ∀ i m L, m ≤ L → (read x n i L).take m = read x n i m := by
  intro i m L h
  induction m generalizing i L with
  | zero => simp [read]
  | succ m ih =>
    cases L with
    | zero => omega
    | succ L => simp [read, ih (i + 1) L (by omega)]

theorem read_drop_one (x : Nat → Nat) (n i L : Nat) :
    (read x n i (L + 1)).drop 1 = read x n (i + 1) L := by
  simp [read]

theorem read_mod (x : Nat → Nat) (n : Nat) :
    ∀ i L, read x n (i % n) L = read x n i L := by
  intro i L
  induction L generalizing i with
  | zero => rfl
  | succ L ih =>
    simp only [read, Nat.mod_mod]
    congr 1
    rw [← ih (i % n + 1), ← ih (i + 1), Nat.mod_add_mod]

theorem read_periodic (x : Nat → Nat) (n : Nat) :
    ∀ i L, read x n (i + n) L = read x n i L := by
  intro i L
  rw [← read_mod x n (i + n), Nat.add_mod_right, read_mod]

/-- Every cell read from a valid configuration is a valid state. -/
theorem read_valid (x : Nat → Nat) (k n : Nat) (hx : ∀ i, x i < k) :
    ∀ i L, ∀ a ∈ read x n i L, a < k := by
  intro i L
  induction L generalizing i with
  | zero => simp [read]
  | succ L ih =>
    intro a ha
    simp only [read, List.mem_cons] at ha
    rcases ha with rfl | ha
    · exact hx _
    · exact ih (i + 1) a ha

/-- `∑_{i<n} g i`, by plain recursion so the kernel can evaluate it. -/
def sumRange (g : Nat → Int) : Nat → Int
  | 0 => 0
  | n + 1 => sumRange g n + g n

theorem sumRange_sub (g h : Nat → Int) :
    ∀ n, sumRange (fun i => g i - h i) n = sumRange g n - sumRange h n := by
  intro n
  induction n with
  | zero => simp [sumRange]
  | succ n ih => simp only [sumRange, ih]; omega

theorem sumRange_congr (g h : Nat → Int) (hgh : ∀ i, g i = h i) :
    ∀ n, sumRange g n = sumRange h n := by
  intro n
  induction n with
  | zero => rfl
  | succ n ih => simp [sumRange, ih, hgh]

/-- Discrete telescoping: `∑_{i<n} (G i - G (i+1)) = G 0 - G n`. -/
theorem sumRange_telescope (G : Nat → Int) :
    ∀ n, sumRange (fun i => G i - G (i + 1)) n = G 0 - G n := by
  intro n
  induction n with
  | zero => simp [sumRange]
  | succ n ih => simp only [sumRange, ih]; omega

/-- All lists of length `L` over the alphabet `{0, …, k-1}`. -/
def allPatterns (k : Nat) : Nat → List (List Nat)
  | 0 => [[]]
  | L + 1 => (allPatterns k L).flatMap fun p => (List.range k).map fun a => a :: p

theorem mem_allPatterns (k : Nat) :
    ∀ L (p : List Nat), p.length = L → (∀ a ∈ p, a < k) → p ∈ allPatterns k L := by
  intro L
  induction L with
  | zero =>
    intro p hp _
    simp [allPatterns, List.length_eq_zero_iff.mp hp]
  | succ L ih =>
    intro p hp hv
    cases p with
    | nil => simp at hp
    | cons a q =>
      simp only [allPatterns, List.mem_flatMap, List.mem_map, List.mem_range]
      refine ⟨q, ih q (by simpa using hp) (fun b hb => hv b (by simp [hb])), a,
        hv a (by simp), rfl⟩

/-- Big-endian base-`k` code of a pattern (Wolfram's neighbourhood order). -/
def code (k : Nat) (p : List Nat) : Nat :=
  p.foldl (fun acc a => acc * k + a) 0

/-- A finite table read as a function on patterns; missing entries are `0`. -/
def tableFn (k : Nat) (t : List Int) (p : List Nat) : Int :=
  t.getD (code k p) 0

/-- A finite cyclic configuration given by its list of cells. -/
def cfg (l : List Nat) (i : Nat) : Nat :=
  l.getD i 0

theorem cfg_valid (l : List Nat) (k : Nat) (hk : 0 < k) (h : l.all (· < k) = true) :
    ∀ i, cfg l i < k := by
  intro i
  unfold cfg
  rw [List.getD_eq_getElem?_getD]
  cases hi : l[i]? with
  | none => simpa using hk
  | some a =>
    have : a ∈ l := List.mem_of_getElem? hi
    simpa using List.all_eq_true.mp h a this

end Slean

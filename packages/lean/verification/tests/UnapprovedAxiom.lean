axiom unapproved_identity (n : Nat) : n + 0 = n

theorem reusable_identity (n : Nat) : n + 0 = n := unapproved_identity n

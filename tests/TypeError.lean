import Slean.Core

-- This file is intentionally rejected: a version is a Nat, not free text.
def invalidIdentity : Slean.Identity :=
  { id := "bad", version := "one", domain := "synthetic",
    provenance := "synthetic://type-test", audience := "agent" }

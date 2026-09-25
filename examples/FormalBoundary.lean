import Slean

open Lean Slean

private def formalIdentity : Identity :=
  { id := "formal-claim-demo", version := 1, domain := "synthetic-computation",
    provenance := "synthetic://worked-examples", audience := "agent" }

private def formalClaim : FormalClaimRef :=
  { identity := formalIdentity,
    declaration := checkedDeclaration, statement := checkedStatement,
    toolchain := checkedToolchain, status := "kernel_checked" }

def main : IO Unit := do
  let receipt := proofReceipt formalClaim
  let status := (receipt.getObjValAs? String "status").toOption.getD "missing"
  let eligible := (receipt.getObjValAs? Bool "attestation_eligible").toOption.getD false
  IO.println s!"eligible={eligible}; status={status}"

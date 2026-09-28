import SleanExport.Native

open Lean Elab Command SleanExport

run_cmd do
  let strName := Name.str .anonymous "a.b"
  let numName := Name.num (Name.str .anonymous "a") 2
  unless nativeName strName != nativeName `a.b do throwError "flattened native string name"
  unless nativeName numName != nativeName (Name.str (Name.str .anonymous "a") "2") do
    throwError "flattened native numeric name"
  let cases : Array (Expr × String) := #[
    (.sort .zero, "[\"sort\",[\"zero\"]]"),
    (.sort (.succ .zero), "[\"sort\",[\"succ\",[\"zero\"]]]"),
    (.const `True [], "[\"const\",[[\"str\",\"True\"]],[]]"),
    (.lit (.natVal 9007199254740993), "[\"natLit\",\"9007199254740993\"]"),
    (.lit (.strVal "héllo"), "[\"strLit\",\"héllo\"]"),
    (.app (.const `Nat.succ []) (.lit (.natVal 0)),
      "[\"app\",[\"const\",[[\"str\",\"Nat\"],[\"str\",\"succ\"]],[]],[\"natLit\",\"0\"]]"),
    (.lam `x (.sort .zero) (.bvar 0) .implicit,
      "[\"lam\",[[\"str\",\"x\"]],[\"sort\",[\"zero\"]],[\"bvar\",\"0\"],\"implicit\"]"),
    (.forallE `x (.sort .zero) (.bvar 0) .instImplicit,
      "[\"forallE\",[[\"str\",\"x\"]],[\"sort\",[\"zero\"]],[\"bvar\",\"0\"],\"instImplicit\"]"),
    (.letE `x (.sort .zero) (.const `True []) (.bvar 0) true,
      "[\"letE\",[[\"str\",\"x\"]],[\"sort\",[\"zero\"]],[\"const\",[[\"str\",\"True\"]],[]],[\"bvar\",\"0\"],true]"),
    (.proj `Prod 1 (.const `test []),
      "[\"proj\",[[\"str\",\"Prod\"]],\"1\",[\"const\",[[\"str\",\"test\"]],[]]]")]
  for (expr, expected) in cases do
    let .ok actual := nativeExpr [] 0 expr | throwError "encoding rejected: {expected}"
    let .ok wanted := Json.parse expected | throwError "invalid test JSON: {expected}"
    unless actual == wanted do throwError "encoding mismatch: {expected}"
  for bad in #[Expr.bvar 0, .fvar ⟨`x⟩, .mvar ⟨`m⟩, .sort (.mvar ⟨`u⟩), .sort (.param `u)] do
    if (nativeExpr [] 0 bad).isOk then throwError "accepted an open native expression"
  let level := Level.imax (.max (.param `u) .zero) (.succ .zero)
  unless (nativeLevel [`u] level).isOk do throwError "rejected a declared universe"
  let .ok erased := nativeExpr [] 0 (.mdata {} (.const `True [])) | throwError "metadata rejected"
  let .ok plain := nativeExpr [] 0 (.const `True []) | throwError "plain expression rejected"
  unless erased == plain do throwError "metadata erasure mismatch"
  logInfo "Native encoding: ten constructor vectors, five rejected open terms, native names and universes passed"

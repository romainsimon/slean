import Comparator
import Export
import Export.Parse
import Lean.Replay

open Lean

private def decodeName (value : Json) : Except String Name := do
  let mut name := Name.anonymous
  for part in ← value.getArr? do
    let fields ← part.getArr?
    unless fields.size == 2 do throw "Invalid native name component"
    let kind ← fields[0]!.getStr?
    let text ← fields[1]!.getStr?
    if kind == "str" then name := .str name text
    else if kind == "num" then
      let some n := text.toNat? | throw "Invalid numeric name component"
      unless toString n == text do throw "Noncanonical numeric name"
      name := .num name n
    else throw "Unknown native name component"
  return name

private def encodeNameParts : Name → Array Json
  | .anonymous => #[]
  | .str parent text => (encodeNameParts parent).push (.arr #[toJson "str", toJson text])
  | .num parent number => (encodeNameParts parent).push (.arr #[toJson "num", toJson (toString number)])

private def encodeName (name : Name) : Json := .arr (encodeNameParts name)

private def encodeNames (names : Array Name) : Json :=
  .arr ((names.map encodeName).qsort fun left right => left.compress < right.compress)

/-- The mandatory primitive targets of pinned Comparator Main.lean. -/
private def primitiveTargets : Array Name := #[
  ``Nat.add, ``Nat.sub, ``Nat.mul, ``Nat.pow, ``Nat.gcd, ``Nat.div, ``Nat.mod,
  ``Nat.beq, ``Nat.ble, ``Nat.land, ``Nat.lor, ``Nat.xor, ``Nat.shiftLeft,
  ``Nat.shiftRight, ``String.ofList, ``Char.ofNat, ``List, ``eagerReduce,
  ``Nat, ``String, ``String.mk, ``Char, ``optParam, ``autoParam, ``semiOutParam, ``outParam]

private def legalAxioms : Array Name := #[``propext, ``Quot.sound, ``Classical.choice]
private def quotientTargets : Array Name := #[``Quot, ``Quot.mk, ``Quot.lift, ``Quot.ind]

private def exportEnvironment (request : Json) (names : Array Name) : IO Unit := do
  let modules ← IO.ofExcept <| request.getObjValAs? (Array String) "modules"
  initSearchPath (← findSysroot)
  let env ← importModules (modules.map fun name => { module := name.toName, importAll := true }) {}
    (loadExts := false) (leakEnv := true)
  M.run env do
    initState env
    dumpMetadata
    for name in names ++ legalAxioms ++ primitiveTargets ++ quotientTargets do
      modify fun state => { state with noMDataExprs := {} }
      dumpConstant name

private def readExport (path : String) : IO Export.ExportedEnv := do
  let handle ← IO.FS.Handle.mk path .read
  Export.parseStream (IO.FS.Stream.ofHandle handle)

/-- Derive metadata from the textual constants that the kernel just checked.
Do not use a candidate binary's separately extracted metadata as authority. -/
private def declarationReport (solution : Export.ExportedEnv) (name : Name) : IO Json := do
  let some info := solution.constMap[name]?
    | throw <| IO.userError "Compared declaration missing from solution"
  let (_, traversal) ← IO.ofExcept <|
    (Comparator.Axioms.loop.run { solution, legalAxioms := Std.HashSet.ofArray legalAxioms }).run
      { worklist := #[name], checked := {} }
  let axioms := traversal.checked.toArray.filter fun target =>
    match solution.constMap[target]? with
    | some (.axiomInfo _) => true
    | _ => false
  return Json.mkObj [
    ("declaration", encodeName name),
    ("statement_dependencies", encodeNames info.type.getUsedConstants),
    ("proof_dependencies", encodeNames (info.value? (allowOpaque := true) |>.map Expr.getUsedConstants |>.getD #[])),
    ("axioms", encodeNames axioms)]

/-- Delegate statement/definition equality and axiom traversal to Comparator.
Kernel replay and quotient post-check follow its pinned Main.lean driver. -/
private def compareEnvironments (request : Json) (names : Array Name) : IO Unit := do
  let challenge ← readExport (← IO.ofExcept <| request.getObjValAs? String "challenge")
  let solution ← readExport (← IO.ofExcept <| request.getObjValAs? String "solution")
  IO.ofExcept <| Comparator.compareAt challenge solution (names ++ legalAxioms) #[] primitiveTargets
  IO.ofExcept <| Comparator.checkAxioms solution names #[] legalAxioms
  let env ← mkEmptyEnvironment
  let original := solution.constMap
  let constants := #[``Quot.mk, ``Quot.lift, ``Quot.ind].foldl (init := original) (·.erase ·)
  let kernel ← env.toKernelEnv.replay constants
  for target in quotientTargets do
    if let some info := original[target]? then
      let some checked := kernel.find? target | throw <| IO.userError "Missing quotient declaration after replay"
      unless info == checked do throw <| IO.userError "Quotient declaration differs after replay"
  let declarations ← names.mapM (declarationReport solution)
  IO.println <| (Json.mkObj [
    ("format", toJson "slean-native-comparison/0.1-draft.1"),
    ("status", toJson "passed"), ("checked_theorems", toJson names.size),
    ("declarations", toJson declarations),
    ("comparison", toJson "Pinned Comparator.compareAt and checkAxioms"),
    ("kernel", toJson "Lean kernel replay and quotient post-check"),
    ("extension_initializers", toJson false)]).compress

def main (args : List String) : IO Unit := do
  let [mode, path] := args | throw <| IO.userError "Expected export/compare and receiver request"
  let request ← IO.ofExcept <| Json.parse (← IO.FS.readFile path)
  let encoded ← IO.ofExcept <| request.getObjValAs? (Array Json) "declarations"
  let names ← IO.ofExcept <| encoded.mapM decodeName
  unless !names.isEmpty && names.toList.eraseDups.length == names.size do
    throw <| IO.userError "Select distinct native declarations"
  if mode == "export" then exportEnvironment request names
  else if mode == "compare" then compareEnvironments request names
  else throw <| IO.userError "Unsupported comparison operation"

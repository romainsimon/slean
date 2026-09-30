import SleanExport.BuildInputs
import SleanExport.Application

open Lean SleanExport

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
      unless toString n == text do throw "Noncanonical numeric name component"
      name := .num name n
    else throw "Unknown native name component"
  return name

private def auditDeclaration (name : Name) : CoreM Json := do
  let env ← getEnv
  let info ← getConstInfo name
  let some index := env.getModuleIdxFor? name | throwError "No defining module for {name}"
  let statement ← IO.ofExcept (nativeStatement info)
  return Json.mkObj [
    ("declaration", nativeName name), ("module", toJson env.allImportedModuleNames[index]!.toString),
    ("kind", toJson (declarationKind info)), ("statement", statement),
    ("statement_dependencies", nativeNames info.type.getUsedConstants),
    ("proof_dependencies", nativeNames (info.value? (allowOpaque := true) |>.map Expr.getUsedConstants |>.getD #[])),
    ("axioms", nativeNames (← collectAxioms name))]

/-- Receiver-owned extraction. Imported extension initializers are disabled. -/
def main (args : List String) : IO Unit := do
  let [requestFile] := args | throw <| IO.userError "Expected one receiver request file"
  let request ← IO.ofExcept <| Json.parse (← IO.FS.readFile requestFile)
  let moduleStrings ← IO.ofExcept <| request.getObjValAs? (Array String) "modules"
  let encodedNames ← IO.ofExcept <| request.getObjValAs? (Array Json) "declarations"
  let names ← IO.ofExcept <| encodedNames.mapM decodeName
  let roots := moduleStrings.map String.toName
  initSearchPath (← findSysroot)
  let env ← importModules (roots.map fun module => { module, importAll := true }) {}
    (loadExts := false) (leakEnv := true)
  let declarations ← (names.mapM auditDeclaration).toIO'
    { fileName := "Slean receiver audit", fileMap := default } { env }
  let modules ← moduleInputs env roots (← getSrcSearchPath)
  let auxiliaryNames ← IO.ofExcept <| ((request.getObjValAs? (Array Json) "auxiliary_declarations").toOption.getD #[]).mapM decodeName
  let auxiliary ← (auxiliaryNames.mapM auditDeclaration).toIO'
    { fileName := "Slean receiver auxiliary audit", fileMap := default } { env }
  let mut captures : Array Json := #[]
  if (request.getObjValAs? Bool "application_captures").toOption.getD false then
    for name in names do
      let some index := env.getModuleIdxFor? name
        | throw <| IO.userError "Missing capture's defining module"
      let some info := env.find? name | throw <| IO.userError "Missing capture's consumer"
      let statement ← IO.ofExcept <| nativeStatement info
      -- Serialized per-module entries remain readable without extension initializers.
      let entries := applicationExt.getModuleEntries env index
      captures := captures ++ (entries.filter fun entry =>
        (entry.getObjVal? "consumer").toOption == some (nativeName name)).map
        (fun entry => entry.setObjVal! "consumer_statement" statement)
  IO.println <| (Json.mkObj [
    ("format", toJson "slean-receiver-audit/0.1-draft.1"),
    ("lean_version", toJson Lean.versionString),
    ("declarations", toJson declarations), ("modules", modules),
    ("auxiliary_declarations", toJson auxiliary), ("application_captures", toJson captures)]).compress

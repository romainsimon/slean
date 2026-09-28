import SleanExport.Native
import SleanExport.Application
import Architect

open Lean Elab Command

namespace SleanExport

/-- Export imported declarations. This collects data; it issues no verification receipt. -/
def declarationData (name : Name) : CoreM Json := do
  let env ← getEnv
  let info ← getConstInfo name
  let some index := env.getModuleIdxFor? name
    | throwError "Slean exports imported declarations; build and import the defining module first: {name}"
  let moduleName := env.allImportedModuleNames[index]!
  let source ← findLean (← getSrcSearchPath) moduleName
  let compiled ← findOLean moduleName
  let statement ← match nativeStatement info with
    | .ok value => pure value
    | .error message => throwError "Cannot encode {name}: {message}"
  let statementText ← Meta.MetaM.run' <| Meta.ppExpr info.type
  let proofDependencies := info.value? (allowOpaque := true)
    |>.map Expr.getUsedConstants |>.getD #[]
  let axioms ← collectAxioms name
  let mut presentation := Json.null
  if let some node := Architect.blueprintExt.find? env name then
    let (statementUses, proofUses) ← node.inferUses
    presentation := Json.mkObj [
      ("annotation", (← node.toNodeWithPos).toJson),
      ("statement_uses", toJson statementUses.uses),
      ("proof_uses", toJson proofUses.uses),
      ("statement_lean_ok", toJson statementUses.leanOk),
      ("proof_lean_ok", toJson proofUses.leanOk)]
  return Json.mkObj [
    ("declaration", nativeName name), ("display_name", toJson name.toString),
    ("kind", toJson (declarationKind info)), ("module", toJson moduleName.toString),
    ("source_path", toJson source.toString), ("compiled_path", toJson compiled.toString),
    ("statement", statement), ("statement_text", toJson statementText.pretty),
    ("statement_dependencies", nativeNames info.type.getUsedConstants),
    ("proof_dependencies", nativeNames proofDependencies),
    ("axioms", nativeNames axioms), ("presentation", presentation)]

/-- The command is run explicitly by the author in an ordinary Lake environment. -/
syntax (name := exportDeclarations) "#slean_export" "[" ident,* "]" "to" str : command

@[command_elab exportDeclarations] def elabExportDeclarations : CommandElab
  | `(#slean_export [$names:ident,*] to $path:str) => do
    let declarations ← names.getElems.mapM fun name => do
      let resolved ← liftCoreM <| realizeGlobalConstNoOverloadWithInfo name
      liftCoreM <| declarationData resolved
    if declarations.isEmpty then throwError "Select at least one declaration"
    let output := Json.mkObj [
      ("format", toJson "slean-lean-extraction/0.1-draft.1"),
      ("lean_version", toJson Lean.versionString),
      ("toolchain_prefix", toJson ((← IO.appDir) / "..").toString),
      ("declarations", toJson declarations),
      ("verification", toJson "not_performed")]
    IO.FS.writeFile path.getString (output.pretty ++ "\n")
  | _ => throwUnsupportedSyntax

end SleanExport

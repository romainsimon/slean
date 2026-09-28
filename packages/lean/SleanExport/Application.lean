import SleanExport.Native

open Lean Meta Elab Tactic Command

namespace SleanExport

initialize applicationExt : SimplePersistentEnvExtension Json (Array Json) ←
  registerSimplePersistentEnvExtension {
    name := `SleanExport.applicationExt
    addEntryFn := Array.push
    addImportedFn := fun entries => entries.foldl (· ++ ·) #[]
    asyncMode := .async .asyncEnv
  }

/-- Close over the local context before using the native expression encoding. -/
def scopedExpression (expr : Expr) (term := false) : MetaM Json := do
  let expr ← instantiateMVars expr
  let locals ← getLocalHyps
  let closed ← if term then
    mkLambdaFVars locals expr (usedLetOnly := false) (generalizeNondepLet := false)
  else
    mkForallFVars locals expr (usedLetOnly := false) (generalizeNondepLet := false)
  let closed ← instantiateMVars closed
  let parameters := (collectLevelParams {} closed).params.toList
  let encoded ← match nativeExpr parameters 0 closed with
    | .ok value => pure value
    | .error message => throwError "Application capture has an unresolved native term: {message}"
  return Json.mkObj [
    ("encoding", toJson "lean-expr/0.1-draft.1"),
    ("universe_parameters", toJson (parameters.map nativeName)), ("expression", encoded)]

private def goalData (goal : MVarId) : MetaM Json := goal.withContext do
  let type ← instantiateMVars (← goal.getType)
  return Json.mkObj [
    ("name", nativeName (← goal.getDecl).userName),
    ("statement", ← scopedExpression type),
    ("text", toJson (← ppExpr type).pretty), ("status", toJson "unresolved")]

private def contextData : MetaM (Array Json) := do
  let mut output := #[]
  for localVar in ← getLocalHyps do
    let declaration ← localVar.fvarId!.getDecl
    output := output.push <| Json.mkObj [
      ("name", nativeName declaration.userName),
      ("proposition", toJson (← isProp declaration.type)),
      ("type", ← scopedExpression declaration.type)]
  return output

private def argumentData (expr : Expr) : MetaM (Name × Array Json) := do
  let expr := (← instantiateMVars expr).consumeMData
  let .const name levels := expr.getAppFn.consumeMData
    | throwError "Select a named Lean declaration for slean_apply"
  let info ← getConstInfo name
  let mut type := info.type.instantiateLevelParams info.levelParams levels
  let mut output := #[]
  for argument in expr.getAppArgs do
    let .forallE binder domain body _ := (← whnf type)
      | throwError "Application arguments exceed the selected declaration's interface"
    output := output.push <| Json.mkObj [
      ("binder", nativeName binder), ("type", ← scopedExpression domain),
      ("term", ← scopedExpression argument (term := true))]
    type := body.instantiate1 argument
  return (name, output)

/-- Ordinary Lean `apply`, with a capture of the actual inputs and remaining goals. -/
syntax (name := applyWithCapture) "slean_apply " term " recording " str : tactic

@[tactic applyWithCapture] def evalApplyWithCapture : Tactic := fun stx => do
  let `(tactic| slean_apply $term recording $label:str) := stx
    | throwUnsupportedSyntax
  let some consumer ← Term.getDeclName? | throwError "Use slean_apply in a named declaration"
  if label.getString.isEmpty then throwError "An application capture needs a nonempty label"
  let capture ← IO.mkRef (none : Option (MVarId × Expr × List MVarId))
  evalApplyLikeTactic (fun goal expr => do
    let goals ← goal.apply expr (term? := some m!"`{expr}`")
    capture.set (some (goal, expr, goals))
    return goals) term
  let some (goal, expr, goals) ← capture.get | throwError "No application was captured"
  let data ← goal.withContext do
    let (producer, arguments) ← argumentData expr
    let info ← getConstInfo producer
    let .ok statement := nativeStatement info | throwError "Unsupported producer statement"
    let remaining ← goals.toArray.filterMapM fun goal => do
      if ← goal.isAssigned then return none
      return some (← goalData goal)
    return Json.mkObj [
      ("label", toJson label.getString), ("consumer", nativeName consumer),
      ("producer", nativeName producer), ("producer_statement", statement),
      ("arguments", toJson arguments), ("context", toJson (← contextData)),
      ("target", ← scopedExpression (← goal.getType)),
      ("remaining_goals", toJson remaining),
      ("verification", toJson "not_performed")]
  let previous := applicationExt.getState (asyncDecl := consumer) (← getEnv)
  if previous.any (fun entry =>
      (entry.getObjVal? "consumer").toOption == (data.getObjVal? "consumer").toOption &&
      (entry.getObjVal? "label").toOption == (data.getObjVal? "label").toOption) then
    throwError "Duplicate application label in this declaration"
  modifyEnv fun env => applicationExt.addEntry (asyncDecl := consumer) env data
  logInfo m!"SLEAN_APPLICATION {data.compress}"

syntax (name := exportApplications) "#slean_export_applications" "[" ident,* "]" "to" str : command

@[command_elab exportApplications] def elabExportApplications : CommandElab
  | `(#slean_export_applications [$names:ident,*] to $path:str) => do
    let selected ← names.getElems.mapM fun name => do
      liftCoreM <| realizeGlobalConstNoOverloadWithInfo name
    if selected.isEmpty then throwError "Select at least one application consumer"
    if selected.toList.eraseDups.length != selected.size then
      throwError "Duplicate application consumer"
    let mut captures := #[]
    for name in selected do
      let info ← liftCoreM <| getConstInfo name
      let .ok statement := nativeStatement info | throwError "Unsupported consumer statement"
      let entries := (applicationExt.getState (asyncDecl := name) (← getEnv)).filter fun entry =>
        (entry.getObjVal? "consumer").toOption == some (nativeName name)
      if entries.isEmpty then throwError "No captures for the selected declaration: {name}"
      captures := captures ++ entries.map (fun entry => entry.setObjVal! "consumer_statement" statement)
    IO.FS.writeFile path.getString <| (Json.mkObj [
      ("format", toJson "slean-lean-applications/0.1-draft.1"),
      ("applications", toJson captures), ("verification", toJson "not_performed")]).pretty ++ "\n"
  | _ => throwUnsupportedSyntax

end SleanExport

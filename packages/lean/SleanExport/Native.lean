import Lean

open Lean

namespace SleanExport

def nativeName : Name → Json
  | .anonymous => .arr #[]
  | .str parent value =>
    match nativeName parent with
    | .arr parts => .arr (parts.push (.arr #[toJson "str", toJson value]))
    | _ => .null
  | .num parent value =>
    match nativeName parent with
    | .arr parts => .arr (parts.push (.arr #[toJson "num", toJson (toString value)]))
    | _ => .null

private def tagged (tag : String) (fields : Array Json := #[]) : Json :=
  .arr (#[toJson tag] ++ fields)

def nativeLevel (parameters : List Name) : Level → Except String Json
  | .zero => return tagged "zero"
  | .succ level => return tagged "succ" #[← nativeLevel parameters level]
  | .max left right => return tagged "max" #[← nativeLevel parameters left, ← nativeLevel parameters right]
  | .imax left right => return tagged "imax" #[← nativeLevel parameters left, ← nativeLevel parameters right]
  | .param name => do
    unless parameters.contains name do throw "undeclared universe parameter"
    return tagged "param" #[nativeName name]
  | .mvar _ => throw "universe metavariable"

private def binderName : BinderInfo → String
  | .default => "default"
  | .implicit => "implicit"
  | .strictImplicit => "strictImplicit"
  | .instImplicit => "instImplicit"

/-- Preserve the native expression. Only metadata wrappers are erased. -/
def nativeExpr (parameters : List Name) (depth : Nat := 0) : Expr → Except String Json
  | .bvar index => do
    unless index < depth do throw "loose bound variable"
    return tagged "bvar" #[toJson (toString index)]
  | .sort level => return tagged "sort" #[← nativeLevel parameters level]
  | .const name levels => return tagged "const" #[nativeName name, toJson (← levels.mapM (nativeLevel parameters))]
  | .app fn arg => return tagged "app" #[← nativeExpr parameters depth fn, ← nativeExpr parameters depth arg]
  | .lam name type body info =>
    return tagged "lam" #[nativeName name, ← nativeExpr parameters depth type,
      ← nativeExpr parameters (depth + 1) body, toJson (binderName info)]
  | .forallE name type body info =>
    return tagged "forallE" #[nativeName name, ← nativeExpr parameters depth type,
      ← nativeExpr parameters (depth + 1) body, toJson (binderName info)]
  | .letE name type value body nondep =>
    return tagged "letE" #[nativeName name, ← nativeExpr parameters depth type,
      ← nativeExpr parameters depth value, ← nativeExpr parameters (depth + 1) body, toJson nondep]
  | .lit (.natVal value) => return tagged "natLit" #[toJson (toString value)]
  | .lit (.strVal value) => return tagged "strLit" #[toJson value]
  | .proj typeName index value =>
    return tagged "proj" #[nativeName typeName, toJson (toString index), ← nativeExpr parameters depth value]
  | .mdata _ value => nativeExpr parameters depth value
  | .fvar _ => throw "free variable"
  | .mvar _ => throw "expression metavariable"

def nativeStatement (info : ConstantInfo) : Except String Json := do
  unless info.levelParams.eraseDups.length == info.levelParams.length do
    throw "duplicate universe parameter"
  return Json.mkObj [
    ("encoding", toJson "lean-expr/0.1-draft.1"),
    ("universe_parameters", toJson (info.levelParams.map nativeName)),
    ("expression", ← nativeExpr info.levelParams 0 info.type)]

def nativeNames (names : Array Name) : Json :=
  .arr ((names.map nativeName).qsort fun left right => left.compress < right.compress)

def declarationKind : ConstantInfo → String
  | .axiomInfo _ => "axiom"
  | .defnInfo _ => "definition"
  | .thmInfo _ => "theorem"
  | .opaqueInfo _ => "opaque"
  | .quotInfo _ => "quotient"
  | .inductInfo _ => "inductive"
  | .ctorInfo _ => "constructor"
  | .recInfo _ => "recursor"

end SleanExport

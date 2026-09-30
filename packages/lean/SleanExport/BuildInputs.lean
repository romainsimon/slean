import SleanExport.Native

open Lean

namespace SleanExport

/-- The actual import closure of selected modules, without presentation edges. -/
def moduleInputs (env : Environment) (roots : Array Name) (sources : SearchPath) : IO Json := do
  let mut pending := roots.toList
  let mut seen : NameSet := {}
  let mut entries : Array Json := #[]
  while !pending.isEmpty do
    let name := pending.head!
    pending := pending.tail!
    if seen.contains name then continue
    seen := seen.insert name
    let some index := env.getModuleIdx? name
      | throw <| IO.userError s!"Missing imported module: {name}"
    let imports := env.header.moduleData[index]!.imports.map (·.module)
    let source ← findLean sources name
    let compiled ← findOLean name
    entries := entries.push <| Json.mkObj [
      ("module", toJson name.toString), ("module_name", nativeName name),
      ("imports", toJson (imports.map Name.toString)),
      ("source_path", toJson source.toString), ("compiled_path", toJson compiled.toString)]
    pending := imports.toList ++ pending
  return .arr (entries.qsort fun a b => a.compress < b.compress)

end SleanExport

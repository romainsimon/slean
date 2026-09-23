import VersoManual
import SleanDocs

open Verso Doc
open Verso.Genre Manual

def config : RenderConfig where
  emitTeX := false
  emitHtmlSingle := .no
  emitHtmlMulti := .immediately
  htmlDepth := 2

def main (args : List String) : IO UInt32 := do
  let css ← IO.FS.readFile "style.css"
  let js ← IO.FS.readFile "interaction.js"
  manualMain (%doc SleanDocs) (options := args)
    (config := { config with extraCss := ({} : Std.HashSet CSS).insert ⟨css⟩, extraJs := ({} : Std.HashSet JS).insert ⟨js⟩ })

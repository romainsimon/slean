import Lake
open Lake DSL

package SleanDocs where

require verso from git "https://github.com/leanprover/verso.git" @ "v4.28.0"
require Slean from ".."

lean_lib SleanDocs where
  roots := #[`SleanDocs]

@[default_target]
lean_exe sleandocs where
  root := `SleanDocsMain
  supportInterpreter := true

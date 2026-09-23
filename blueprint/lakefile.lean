import Lake
open Lake DSL

require VersoBlueprint from git "https://github.com/leanprover/verso-blueprint" @ "84fb00913d07325342e8b73a8a88f6e05ee59473"
require Slean from ".."

package SleanBlueprint where
  precompileModules := false
  leanOptions := #[⟨`experimental.module, true⟩]

@[default_target]
lean_lib SleanBlueprint where

lean_exe «slean-blueprint-gen» where
  root := `SleanBlueprintMain

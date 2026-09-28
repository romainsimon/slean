# Selected-declaration Lean exporter

This is SR-T04's reference exporter for ordinary Lean 4.34.1 declarations.
It reads native types, direct type/value dependencies and transitive axioms.
LeanArchitect supplies optional annotations, locations and presentation edges.
The exporter preserves these views separately. It has no selected theorem name
built into its implementation.

From this directory, with the pinned toolchain installed:

```sh
lake update
lake build SleanExport
```

Run from this directory so Elan selects its `lean-toolchain`. The repository
root deliberately retains the older V0 toolchain. A caller can also set
`ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1` explicitly. Dependency installation
requires network access; subsequent export uses the installed local environment.

## Author workflow

Add `slean_export` as an ordinary Lake dependency and build the source module.
Create a separate export file that imports that module and `SleanExport`:

```lean
import MyResearch
import SleanExport

#slean_export [MyResearch.result, MyResearch.method] to "native.json"
```

The names above illustrate the syntax. The [executed example](../../examples/reuse/with-slean-lean/Export.lean)
exports eleven real declarations. Selectors use Lean's own name resolver,
including quoted identifiers. The command rejects empty selections, unknown
declarations and declarations in the current unbuilt module. It writes only
after every selected declaration has been collected successfully.

Run the export explicitly with `lake env lean Export.lean`. This is execution
of a reviewed Lean project, including its imports and metaprograms. It is not
an operation for inspecting unreviewed contributions.

Package the extraction from the repository root using the
[pinned Python conformance environment](../../conformance/README.md):

```sh
conformance/.venv/bin/python packages/lean/export.py \
  --project examples/reuse/with-slean-lean \
  --input examples/reuse/with-slean-lean/_out/native.json \
  --output examples/reuse/with-slean-lean/_out/my-module
```

The destination must not exist. The bridge snapshots the selected source
files, native statements, Lake lock/configuration and exporter implementation.
It records compiled module digests separately from source bytes. It accepts
only source/build artifacts under the declared project, Lake dependencies or
installed toolchain. Names become local IDs without flattening native names;
payload names use content hashes. The output follows the draft module schema.
The default rights declaration is `unknown`; `--license` supplies the author's
declaration, without granting rights over third-party dependencies.

Packaging performs no subprocess, network call or module import. It copies
the explicitly extracted sources and does not implement a public/private
publication projection. Review the selection before sharing its artifacts.

## What the output establishes

The extracted type contains the actual binders and hypotheses. A readable
rendering is retained as an annotation. Statement and proof/value dependency
sets preserve their overlap. For definitions, `proof_dependencies` carries
the defining value's constants; the declaration kind remains explicit.

Native expression encoding follows the [Lean profile](../../profiles/lean.md).
It preserves name components, binder information, universes and natural-number
strings. Open terms are rejected. Pretty-printed text never supplies statement
identity. Unsupported axioms and `sorryAx` stay visible, even when an upstream
annotation suppresses their display or marks its local plan ready.

Every evidence record uses `extraction-only/0.1-draft.1`, with result
`unsupported`; a receiver treats it as declared data. A source snapshot plus
a compiled-module digest does not establish that the compiled proof was built
from those source bytes. Receiver rebuilding, trusted statement comparison,
complete dependency verification and isolated execution belong to SR-T05–06.
The exporter issues no proof receipt and imports no claim of scientific validity.
Local Lake path dependencies still require the original projects; this is not
the standalone package reconstruction promised by later milestones.

## Validation

The [example instructions](../../examples/reuse/with-slean-lean/README.md)
prepare its pinned dependencies. Then run from the repository root:

```sh
conformance/.venv/bin/python packages/lean/check_export.py
```

Set `SLEAN_LAKE` if Lake is outside `PATH`. The check builds the library and
consumer, recomputes the extraction, runs native encoding and selection
controls, and runs eight bridge tests against those fresh artifacts. It keeps
build logs under the example's ignored `_out/` directory. Expected incomplete
proofs occur only in the deliberately negative imported fixtures.

The [observed report](observed-export.json) records the inputs and checking
scope. Exporter conformance and ordinary Lean reuse do not establish Gate U,
an advantage over direct tools, or independent scientific adoption.

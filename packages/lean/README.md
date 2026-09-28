# Native Lean declarations and applications

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

Packaging performs no subprocess, network call or execution of exported code. It copies
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
complete dependency verification and isolated execution belong to SR-T06.
The exporter issues no proof receipt and imports no claim of scientific validity.
Local Lake path dependencies still require the original projects; this is not
the standalone package reconstruction promised by later milestones.

SR-T06 now has a [local Comparator primitive](verification/README.md) for
separately supplied statements and self-contained proof candidates. It issues
no module receipt and does not yet change either Slean verification policy.

## Apply a declaration in ordinary Lean

SR-T05 adds `slean_apply`, which uses Lean's native `apply` elaborator. For
example, the [second project](../../examples/reuse/with-slean-lean/ApplicationExample.lean)
contains this proof step:

```lean
slean_apply DirectReuse.energy_at_two_times system trajectory smooth recording "energy-use"
exact motion
```

At the first line, Lean leaves the equation-of-motion obligation open. The
second line supplies the caller's `motion` hypothesis. The completed theorem
still depends on that hypothesis and on smoothness. The snapshot of an open
goal is a record of that proof step; it does not mean the final proof remains
unfinished or that the hypothesis has been established for a physical system.

The tactic records the named producer, the arguments in the elaborated apply
term, the local context, the target and the goals left by `apply`. Lean can
infer further arguments when applying a partial term. Closed native expressions
retain the scope of the captured terms; hidden implementation declarations
are excluded, and an expression that cannot be closed is rejected. Capture
uses Lean's asynchronous declaration extension API. It also works inside a
subgoal whose target differs from the whole consumer theorem.

After building the consumer, select it for capture export:

```lean
#slean_export_applications [ApplicationExample.energy_with_obligation,
  ApplicationExample.energy_with_all_arguments] to "_out/applications.json"
```

This adds the exact native statement of each completed consumer. The
[executed export file](../../examples/reuse/with-slean-lean/ExportApplications.lean)
also extracts the producer and the two consumers with `#slean_export`.

Package the producer first. For the consumer, pass `--applications` with the
capture file and repeat `--dependency-module` for the local dependency modules.
The bridge validates their bytes, selects an unambiguous native producer,
compares both statement fingerprints, and checks that the producer appears
in the consumer's actual extracted proof dependencies. Supported Lean
requirement references retain their original module when copied. Other
producer requirement semantics are rejected by this bounded bridge.

The result contains input plans and executions with exact component references,
argument/context artifacts and consumer outputs. An input plan here is a
retrospective projection of the invocation, not preregistration. It contains
no execution output or goal snapshot. The execution carries the capture;
the full consumer statement remains authoritative about its assumptions.

`applications.py --module DIRECTORY --application ID` checks local integrity
and inspects the declared requirements without running Lean, package code or
network calls. It respects the draft `all`/`any` rules and exposes unsupported
leaves. It has no receiver proof checker, so even complete author-side proofs
remain `conditional` with `formal_verification: not_performed`. Imported
`passed` results and detached receipts cannot promote them.

This is a repository adapter over the draft reference validator. It is not
yet the public SDK, general offline `apply` operation or verification policy.

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

For native applications and their current bridge, run:

```sh
conformance/.venv/bin/python packages/lean/check_applications.py
```

This separately rebuilds the application example, exports fresh captures,
checks whole-theorem and nested-goal capture, and rejects a missing hypothesis
and a changed conclusion. Eleven application tests check scope, exact references,
statement/dependency mismatches, immutable plans, requirement meaning and
untrusted reports. Eight exporter bridge tests also run against the existing
SR-T04 extraction. The runner rejects Lean panic diagnostics even when the
compiler's exit status is zero, and stops its child process group on timeout.

The SR-T04 [observed report](observed-export.json) remains a historical snapshot
of its recorded source hashes. The [application report](observed-applications.json)
records the SR-T05 candidate, reused cache and remaining verification limits.

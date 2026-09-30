# Receiver verification of reviewed Lean components

`reviewed.py` implements the component portion of
`reviewed-source/0.1-draft.1`. It rebuilds the selected declaration's source
closure in a temporary workspace, checks the resulting proof and binds a
local receipt to the exact Slean module. The separate
[native application verifier](REVIEWED_APPLICATIONS.md) binds fresh captures to
those consumer proofs and their exact producers. The separate
[unreviewed operation](UNREVIEWED.md) adds a receiver-selected statement comparison
and full exported-proof replay under its own named policy.

## Inputs and trust

Fresh `#slean_export` output includes the actual import graph read from Lean's
environment. Packaging adds `environment/build-inputs.json`. This describes
the local sources to rebuild and fingerprints the installed import artifacts,
including `.olean` parts and available IR. It uses the selected declarations'
import closure rather than presentation edges. Older modules without this
description remain inspectable; verification returns `unsupported`.

The receiver explicitly selects an installed dependency project. Its Git pins
and tracked checkout state must match the export, and the compiled import
bytes must match the recorded digests. These installed dependency binaries
are reviewed, trusted inputs. They are not rebuilt from their Git sources.
The installed Lean toolchain and receiver audit binary are also trusted.
The receipt records their hashes and the receiver implementation hashes.

Local source bytes come from the module's declared payloads. The receiver
builds those bytes with its fixed Lean command in an isolated directory; it
does not execute the supplied Lake configuration or fetch dependencies.
Projects requiring unsupported custom build steps can fail or remain
unsupported. The actual imported modules and native statement must still
match the export exactly.

Lean selects a search root for a whole namespace. When local source and an
installed dependency share that namespace, the receiver links the checked
dependency files into its temporary search roots. It checks those links before
kernel replay and after the native audit. Installed files remain read-only.
All compilation finishes before the read-only replay of the final artifacts.

The macOS boundary denies network access, supplies a small environment and
keeps source and dependency inputs read-only. Only the isolated build
directory is writable during compilation. The receipt key and original
module directory are outside execution roots. Each compiler/checker step has
a 600-second deadline and 4 MiB diagnostic limit, with the CPU, per-file,
descriptor and process controls described in the
[local comparison guide](README.md#evidence-and-limits). The comparison
primitive's 1 MiB input-source limit does not apply to this adapter. There
is no hard memory or aggregate disk/job quota. This is a local policy
for reviewed inputs, not a hostile-upload service.

## What is checked

For each rebuilt source module, the bundled `leanchecker` replays its
declarations against the exact installed imports. Imported dependencies
remain trusted under this policy. A receiver-owned audit executable then
imports with extension initializers disabled and reads the native statement,
actual type/proof dependencies and transitive axioms. No imported result,
presentation readiness flag or natural-language statement supplies this data.

Only theorem declarations can receive passing proof receipts. Their native
statement fingerprint must match, and their transitive axioms must be a subset
of `propext`, `Classical.choice` and `Quot.sound`. `sorryAx` and other axioms
prevent a receipt. An unrelated incomplete declaration does not automatically
invalidate a proof that does not use it; the report gives a result for each
selected component.

The checker binds the exact module revision, component, quantified statement,
artifact list and dependency environment. It rechecks input integrity before
issuing any receipt. A failed build, changed environment or exhausted resource
does not establish that the theorem is false.

## Local receipts and offline inspection

An explicit `--store` creates a private receiver store with a local HMAC key.
The directory must be owned by the receiver with mode `0700`; its key uses
`0600`. Keep this store outside all transferable modules and execution roots.
The key is not part of any Slean payload or receipt.

The authenticated receipt is useful only to that receiver. It is not a public
signature or a cross-receiver certificate. `inspect_component` can check it
offline when the caller explicitly supplies the receiver store and receipt.
It requires the same module, component, statement, context and policy.
Another receiver, a changed revision, a modified receipt or a different
requested policy cannot inherit the passing status.

Inspection does not run code or open the network. A JSON receipt placed in a
module's `receipts/` directory is still imported evidence. Ordinary application
inspection also remains conditional: a checked consumer theorem does not
authenticate the recorded application arguments or capture. Use the separate
explicit application operation and its authenticated local receipt for that check.

## Run the checks

First prepare the pinned dependencies using the
[Lean example instructions](../../../examples/reuse/with-slean-lean/README.md).
Build the receiver's executable from `packages/lean`:

```sh
lake build slean_audit SleanExport
```

Rebuild `ApplicationExample` and `FormalExample`, then run `ExportApplications.lean`
and `Export.lean` with `lake env lean` from the example directory. From the
repository root, run:

```sh
conformance/.venv/bin/python packages/lean/verification/check_reviewed.py
```

The [28 September recorded check](observed-reviewed.json), bound to the
implementation hashes in that report, covers the real Physlib consumers,
quoted and polymorphic theorem names, incomplete and inherited proofs,
unapproved axioms, changed statements and imports, receipt tampering, wrong
receivers and revisions, offline inspection and application trust limits.
Full local reports go to `packages/lean/_out/reviewed/`. Receipt keys created
by the test are temporary and are removed when the test exits.

The four namespace-layout regression tests also check unchanged installed
artifacts, substituted or redirected links, and missing installed sources.

The explicit verification CLI accepts `--module DIRECTORY`, one or more
`--component ID`, `--dependency-project DIRECTORY`, `--policy reviewed-source/0.1-draft.1`
and optional `--store DIRECTORY`. Requesting the unreviewed policy returns
`unsupported` in this component entrypoint without falling back to reviewed
execution. Use `unreviewed.py` explicitly for that separate operation.

## Observed cost

The 28 September check took 1,883.219 seconds for the complete validation
sequence. Its consumer environment binds 5,611 modules with 4,448,894,240
bytes of compiled artifacts, including available IR. These local measurements
include hashing and reconstruction and must count in Gate U. They establish
no speed advantage over the direct-tool baseline.

The [30 September component regression](observed-reviewed-regression.json)
repeats all ten groups against the updated shared auditor and implementation.
It again accepts five selected valid proofs and rejects four incomplete or
unapproved-axiom proofs, with all 34 frozen baseline files unchanged. Its complete
sequence took 173.414 seconds locally; this is regression evidence, not a
controlled timing comparison.

# Receiver-selected statement comparison

`unreviewed.py` implements the local component operation named
`unreviewed-contribution/0.1-draft.1`. The receiver independently selects a trusted
reference module and component. The candidate cannot select or replace that
reference through an annotation or an imported receipt.

The operation uses the same source reconstruction and restricted process
boundary as the [reviewed receiver](REVIEWED.md), but suppresses its receipts.
Successful reconstruction alone cannot produce an unreviewed-policy receipt.
A separate comparison and kernel replay must finish first.

## Reference before candidate

The receiver reconstructs the exact reference sources and exports the selected
statement before executing any candidate source. The reference can contain a
`sorry` proof placeholder: its statement is an independently selected challenge,
not a claimed proven theorem. Its actual native statement must match its
component interface. The receiver's installed imports, tools and reference
source are trusted inputs.

The candidate is reconstructed in a different temporary workspace. The supplied
Lake configuration is not executed, dependencies are not downloaded and no
credential environment is inherited. Candidate source and installed imports are
read-only. Only its isolated build directory is writable. Reference exports,
original module directories and receipt keys remain outside candidate execution
roots. Imported extension initializers are disabled during native extraction.

The receiver streams each native export into a private file outside those build
roots. It permits at most 512 MiB per export and stops the process on overflow or
deadline. It does not retain a second complete text copy in Python. The temporary
exports are removed at the end of the operation; their exact hashes and sizes
remain in the report and receipt.

## Reuse existing validation

The [native driver](SleanCompare.lean) uses the pinned
[Comparator](https://github.com/leanprover/comparator/tree/d03acab154d269c06e60e4de7e4cc85deebff94b)
and [lean4export](https://github.com/leanprover/lean4export/tree/076e8e57707e813375e8f9da8bf989799ace9680).
It invokes `Comparator.compareAt` and `Comparator.checkAxioms` on the two textual
exports. The comparison covers the theorem statement, its referenced
definitions, permitted axioms and Comparator's mandatory kernel primitive
checks. Candidate source compilation is insufficient.

The driver then replays the exported solution in Lean's existing kernel and
performs the pinned driver's quotient post-check. It does not implement another
proof kernel. Definition holes are unsupported. Native declaration names are
passed as structural string/numeric components, preserving a quoted name that
contains dots rather than splitting it into another declaration.

The dependency and axiom arrays in a passing receipt come from the parsed
textual constants after comparison and kernel replay. The receiver traverses
those constants with Comparator's axiom traversal. It does not promote the
candidate binary's separately extracted metadata into authority. The integration
test replaces that diagnostic metadata with fabricated names while still
performing the real source builds, exports, comparison and replay; the resulting
receipt must retain the checked textual dependencies.

Allowed axioms remain `propext`, `Classical.choice` and `Quot.sound`. A candidate
using `sorryAx` or a new axiom cannot receive a passing receipt. A changed
statement or altered relevant definition cannot inherit the reference's
meaning. Missing primitives or another tool failure cannot produce a receipt;
a failed operation is not a refutation of the scientific claim.

The receiver rechecks tool source pins, binary/implementation hashes, module
integrity and both export hashes before issuing a receipt. The receipt binds:

- The exact candidate module, component and artifacts.
- The independently selected reference module, component and artifacts.
- The native statement fingerprint and both reconstruction environments.
- Both export hashes, the comparison result and the explicit policy.

The policy remains distinct from `reviewed-source/0.1-draft.1`. Offline inspection
requires explicit local authority and the requested policy. Imported JSON,
another receiver or a receipt with a changed reference, policy, context or
export digest cannot grant authority. Empirical validity is `not_assessed`.
Unreviewed application capture fidelity is unsupported: checking a component
proof does not authenticate a candidate-authored invocation trace.

## Local execution limits

The macOS backend denies network access and access to private module directories
and receipt keys. Each process has a 600-second wall deadline, 300 CPU seconds,
256 MiB per child-written file, bounded descriptors/processes and 4 MiB of
ordinary diagnostics. Receiver-streamed proof exports have their separate
512 MiB byte limit. Limit failures stop the process group.

There is no hard memory cap or aggregate disk/job quota on this backend. The
operation is an explicit local comparison, not a qualified hostile-upload
service. A remote service needs stronger containment and separate validation.
No unsandboxed fallback, model service, virtual-machine change or remote worker
is part of this adapter.

## Setup and operation

Build the pinned receiver tools from `packages/lean/verification`:

```sh
lake build slean_compare
```

Prepare the installed example dependency project and exported modules using
[the Lean package instructions](../README.md). From the repository root:

```sh
conformance/.venv/bin/python packages/lean/verification/unreviewed.py \
  --module /absolute/path/to/candidate-module \
  --component CANDIDATE_COMPONENT_ID \
  --trusted-module /absolute/path/to/receiver-selected-reference \
  --trusted-component REFERENCE_COMPONENT_ID \
  --dependency-project examples/reuse/with-slean-lean \
  --policy unreviewed-contribution/0.1-draft.1 \
  --store /absolute/path/to/private-receiver-store
```

The native declaration name must match the selected reference. Component and
module identities can differ; the receipt records both. Calling this operation
with the reviewed policy returns `unsupported` before execution.

Use `reviewed.inspect_component` with the explicit unreviewed policy, receipt and
local `ReceiptStore` for offline authentication. It performs no Lean execution
or network fetch. A reviewed-policy receipt is not an unreviewed-policy receipt.

The integration runner uses actual exported modules:

```sh
conformance/.venv/bin/python packages/lean/verification/check_unreviewed.py
```

It checks a dependency-bearing Physlib consumer, a quoted declaration against an
independently selected unproved statement, altered statements, incomplete
proofs, unapproved axioms, exact-policy local authority and the frozen baseline.
It also checks that fabricated binary metadata cannot replace checked proof
dependencies and axioms.
The separate streaming tests check byte preservation, output overflow and a
live-process deadline. Completion and measured costs require the observation
report; conformance is not usefulness or adoption evidence.

## Observed on 30 September 2026

The [recorded module comparison](observed-unreviewed.json) passes nine control
groups and binds 13 implementation/test hashes. A dependency-bearing Physlib
proof and a quoted name against a separate unproved reference pass. Fabricated
binary diagnostic metadata cannot replace checked textual dependencies.
Changed statements, `sorryAx` and an invented axiom are rejected after actual
build and export, with their exact Comparator errors recorded. Policy,
authority and receipt-tampering controls pass; all 34 frozen baseline files
remain unchanged.

The complete local sequence took 1,585.268 seconds. Each Physlib export was
327,233,941 bytes. These measured build/verification/storage costs belong in
Gate U accounting; this run does not establish a performance or scientific
usefulness advantage. The shared changes also passed the current
[reviewed component regression](observed-reviewed-policy-regression.json) and
[reviewed application regression](observed-application-policy-regression.json).
The separate three streaming tests passed byte preservation, overflow and
live-process deadline controls.

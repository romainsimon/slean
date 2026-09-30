# Reviewed native applications

`reviewed_applications.py` is an explicit receiver operation under
`reviewed-source/0.1-draft.1`. It checks a recorded invocation in a rebuilt Lean
consumer and issues a receiver-local receipt. Inspection alone never runs it.

The receiver rebuilds the consumer source closure with known instrumentation,
replays the resulting source modules with Lean's bundled kernel checker, and
extracts the actual theorem statements, proof dependencies and transitive axioms.
Imported extension initializers remain disabled. The receiver reads serialized
per-module capture entries directly; it does not enable extension initialization
just to read them.

It then regenerates the portable application from those native entries. The
capture bytes, arguments, target, local context, producer reference, requirement
tree, result and retrospective plan must match exactly. A component proof receipt
alone cannot authenticate an application. An application receipt cannot be used
as a component proof receipt.

## Exact producer binding

The provided producer module must have the exact identity named by the
application. Every import in its closure must match the checked consumer's
imports and environment. A producer source rebuilt within that consumer must have
identical bytes. For an upstream producer used as a receiver-trusted installed
import, both the export's observed compiled-module hash and its source bytes must
match the receiver's pinned binary and installed source. That latter case is a
trusted-import binding, not a claim that the receiver rebuilt the upstream
library from source. The producer's actual native statement and permitted axioms
are audited in the consumer environment.

The input modules and producer bindings are checked again before issuing a
receipt. Receiver tool and implementation hashes are also checked before and
after reconstruction. No receipt key is exposed to Lean or bundled into a
transferable module. The [component policy](REVIEWED.md) describes the execution
boundary, trusted dependencies and resource limits that apply here too.

## What a passing receipt means

A passing receipt authenticates a conditional formal invocation under its
recorded caller context, consumer proof, exact module revision and environment.
Hypotheses quantified by the Lean theorem remain conditions. The receiver does
not establish that those conditions describe the physical world.

Capture fidelity relies on reviewed caller source using receiver-known
instrumentation. The policy does not accept hostile source that manually forges
extension entries. Pinning the instrumentation does not replace review of that
caller source. The separate [unreviewed component operation](UNREVIEWED.md) compares proofs
against receiver-selected statements. It does not authenticate unreviewed
application captures. Four
[producer-binding controls](../tests/test_reviewed_producer.py) additionally
check installed source/binary matching, selected upstream pins, interface
source/toolchain mismatches and duplicate producer modules. These small
filesystem controls supplement the real-proof integration; they do not replay
Lean proofs themselves.

A successfully checked consumer can have had open goals at the recorded `apply`
step: subsequent proof steps may discharge them. Both the original goals and the
completed consumer proof remain visible. Checking that proof does not erase the
earlier invocation record.

Extra producer requirements are preserved but are not independently discharged
by this adapter. Offline inspection reports `compatible` only for a checked
invocation with an empty producer requirement tree; other supported requirements
remain `conditional`. Empirical validity is always `not_assessed` here. General
planning and domain adapters remain separate work.

Receipts use the receiver's local HMAC authority. They are neither public
signatures nor certificates another receiver can import as its own authority.
They bind the application, caller context, target fingerprint, consumer statement,
producer, exact artifact list and checked environment. A copied JSON receipt,
forged status, another receiver or another module revision cannot grant a check.

## Commands

Install the exact dependencies and prepare the author exports as described in
[the Lean package](../README.md). Build the receiver auditor from `packages/lean`:

```sh
lake build slean_audit
```

From the repository root, choose exported module directories, an executed
application ID and a private receipt store outside all module and execution
roots:

```sh
conformance/.venv/bin/python packages/lean/verification/reviewed_applications.py \
  --module /absolute/path/to/consumer-module \
  --application APPLICATION_ID \
  --dependency-module /absolute/path/to/exact-producer-module \
  --dependency-project examples/reuse/with-slean-lean \
  --policy reviewed-source/0.1-draft.1 \
  --store /absolute/path/to/private-receiver-store
```

Use one `--application` per selected invocation and one `--dependency-module` per
exact dependency module. Selecting a plan is `unsupported`. A different policy
is `unsupported` without falling back to reviewed execution. A mismatch after
reconstruction is a failed check, not a refutation of the scientific claim.

The offline Python entrypoint accepts an explicitly supplied local receipt and
its authority:

```python
from reviewed_applications import inspect_application

report = inspect_application(module_directory, application_id,
                             receipt=local_receipt, store=receiver_store)
```

Without authenticated local authority it retains declared trust and
`formal_verification: not_performed`. It does not execute Lean, fetch a dependency
or discover authority from imported module files.

The integration runner uses real exported Physlib applications:

```sh
conformance/.venv/bin/python \
  packages/lean/verification/check_reviewed_applications.py
```

It exercises a partial invocation whose goal is later closed and a complete
invocation, exact local authority, wire-valid capture forgery, wrong policy,
producer revision, plan misuse, instrumentation changes and offline inspection.
The [30 September observation](observed-reviewed-applications.json) records six
passing control groups, two checked invocations, 5,611 bound import modules and
all 34 frozen direct-tool baseline files unchanged. The complete sequence took
109.368 seconds locally. Its implementation/test hashes bind the report to the
checked code. This is a different sequence from the earlier component check;
the time is not a comparative speed or usefulness result. The unreviewed component path has its own explicit operation and validation.
This application report covers the reviewed-caller policy only.

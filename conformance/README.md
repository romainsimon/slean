# Draft contract conformance

This is SR-T03's executable specification kit. It checks the wire shapes,
local references, immutable file/statement bindings and specified structural
invariants. It freezes the requirement truth tables and module identity with
an independent JavaScript encoding check. It is not the final SR-T14 reader
kit, a Lean proof checker, the Python SDK or a scientific-validation result.

From the repository root, with Python 3.12+ and Node.js 20+:

```sh
python3 -m venv conformance/.venv
conformance/.venv/bin/python -m pip install --require-hashes -r conformance/requirements.lock
conformance/.venv/bin/python conformance/check.py
```

Set `SLEAN_NODE` when Node is outside `PATH`. The unit mapping check uses the
separately pinned direct-baseline Pint environment:

```sh
examples/reuse/direct-python/.venv/bin/python conformance/check_units.py
```

Installation requires network access. The checks use only bundled schemas,
local payloads, Python libraries and Node's built-ins. They do not fetch a
schema or context, import module code or build a Lean project. The native
encoding fixture contains real ordinary Lean source, but imported declarations
that its two proofs passed deliberately remain `declared` to this reader.

## Shared fixtures

| Fixture | What it represents |
|---|---|
| `formal/` | A native Lean statement encoding, source/environment references and two distinct imported proof claims. Their status cannot promote the reader's verification level. |
| `research/` | The sensor hypothesis, fixed test plans, two observations, a failed prediction, a revision, a blocked application and its retry with the same input, plus a new open question and unresolved alternative. Parameters carry explicit unknown uncertainty. |
| `open-question/` | A question with no target theorem, component, application, evidence or payload requirement. |

[`negative-cases.json`](negative-cases.json) is shared test data. Each case
either supplies raw invalid JSON or selects a positive fixture and applies
explicit `add`, `replace` or `remove` operations using JSON Pointer paths.
The kit supports that stated operation subset; it is not a general JSON Patch
library. Cases can replace an owned payload and optionally update its digest.
Most mutated manifests are rehashed to test semantic bindings rather than
merely fail the outer hash. `rehash: false` isolates the identity failure.

The cases cover planned outputs, wrong references/kinds, weakened requirements,
changed plans/retry inputs, wrong evidence subjects/context/policies/statements,
wrong dimensions, non-decimal quantities, negative bounds, missing dependencies,
invalid native expressions or unbound universes, cyclic revision/attempt links,
unsafe paths and raw JSON ambiguity. Additional
tests cover optional unknown data, mandatory unknown profiles, unsupported
uncertainty/units, detached forged receipts, altered payloads and symlinks.

[`requirement-vectors.json`](requirement-vectors.json) gives all 32 ordered
two-input combinations and both empty groups. Aggregating these supplied
statuses does not establish that any scientific leaf has a valid witness.
The reference Lean policy checker and its narrow proof remain SR-T10 work.

[`identity-vectors.json`](identity-vectors.json) contains five JCS vectors and
three full module identities. Python uses pinned `rfc8785`; the separate
JavaScript implementation uses ECMAScript number serialization and UTF-16
sorting. The latter checks canonicalization and hashing, not raw duplicate-key
parsing or scientific payload validity. It is not claimed as the independent
Slean reader required by SR-T14.

`generate_fixtures.py` is an explicit maintenance command. The check never runs
it or silently updates expected outputs. Review a semantic change, bump the
draft/profile version when needed, preserve historical fixtures, regenerate
deliberately and rerun both paths. There is no automatic scientific promotion.

## Scope of the current check

External exact references are recorded as unresolved dependencies until a
receiver supplies and checks their module bytes. A declared profile's shape
can be supported while an interface or uncertainty interpretation is not;
the report preserves those unsupported capabilities. A structural pass is not
application compatibility, a reproduced calculation or a proof.

The typed signatures are syntax-checked specification stubs, not type-checked
client implementations. Formal adapter execution, checked witness selection,
full RO-Crate/profile validation, public export, SDK ergonomics and the
usefulness comparison remain the later named PRD tasks. Runtime use of the
Physlib dimensional bridge also remains adapter work; the mapping check here
compares the pinned Pint dimensions and 21 scalar conversions against the
declared ISQ representation, including absolute Celsius offsets.

## Observed on 28 September 2026

The [recorded contract check](observed-contract.json) passed nine tests with
Python 3.14.3 and Node.js 24.4.1: three positive modules, 41 negative cases,
34 requirement vectors, five canonical JSON vectors and three module identities.
It records the SHA-256 digests of the exact specification files checked.
The separate [unit report](observed-units.json) records 21 successful conversions
using Pint 0.26.1. These results establish the stated structural checks only.

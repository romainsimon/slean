# Slean module contract: 0.1-draft.1

This is an experimental wire contract, distinct from the legacy dossier
schemas. The schema and conformance examples freeze SR-T03's interface. They
do not establish SDK availability, a verification service, RO-Crate profile
conformance, external adoption or Gate U. Breaking changes require a new draft
identifier and fixtures; never reinterpret an old identifier.

The public operations are `inspect`, `apply`, `verify`, `pack` and `uses`.
The [typed authoring signatures](authoring.pyi) specify their library boundary.
They are a specification, not an installed Python implementation.

## Files and identity

`slean-module.json` is authoritative. It follows [module.schema.json](module.schema.json)
and the semantic rules below. A module has components, applications and
evidence; each collection can be empty. A local ID is unique across these
collections. A reference is `{ "id": "name" }` locally, or
`{ "module": "sha256:…", "id": "name" }` for an exact external module.
An external module must occur in `dependencies`; resolving it requires its
actual bytes and identity. Missing dependencies are unresolved, never silently
redirected to a newer version. A build-dependency cycle is invalid.

Payload references use `path` instead of `id`. Every local reference names a
declared file with its byte size and SHA-256. Payload paths are portable ASCII
relative paths as specified by the schema. Reject symlinks, non-regular files,
case-insensitive path collisions, Windows device names, trailing dots and any
path outside the module. `slean-module.json`, `ro-crate-metadata.json`, and the
top-level `receipts` and `indexes` directories cannot be payloads. Native source
with an unsupported filename needs an explicit safe export mapping.

Before hashing, require `profiles` to be sorted by `id`, `dependencies` by
module ID, and `payloads` by path. Require unique profile IDs and payload paths.
All these sorting keys are ASCII. Other arrays retain their author-supplied
order. Do not reorder them when receiving a module. Remove only the root `id`
field and compute:

```text
id = "sha256:" + SHA256(UTF8("slean-module/0.1-draft.1\n") + JCS(manifest_without_id))
```

JCS is [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785). Preserve Unicode
without normalization; sort object keys by UTF-16 code units. Reject duplicate
JSON keys, invalid Unicode, NaN and infinity. Scientific decimals, file sizes
and native Lean natural numbers use decimal strings. Plain JSON integer tokens
outside the exact safe integer range are rejected; JSON floating values follow
IEEE 754 binary64/JCS and cannot substitute for exact scientific decimals.
The cross-language vectors include Unicode ordering, floating serialization,
exact decimals, changed payloads and complete module identities.

Generated RO-Crate metadata, derived indexes and detached receipts are outside
the identity. They must refer to this exact module and cannot add authoritative
scientific facts. Conflicting copies of a core fact are errors. RO-Crate 1.3
uses its existing file/person/software/action vocabulary; it points to the
core payload and its record IDs. The public profile URL and full envelope
conformance are delivery work in SR-T09/SR-T15, not claimed by these schemas.

## Three record families

A **component** has a kind (`claim`, `model`, `method`, `data`), interface,
requirements, sources and rights. `license` is an SPDX expression or an
explicit `unknown`; a record does not grant rights to material it references.
Use RO-Crate metadata for authors and other attribution. `supersedes` refers
to exact earlier components and never changes existing references. Several
proofs are separate evidence records about the same claim.

An **application** binds an exact component to named inputs and context.
Bindings contain a literal string/boolean/missing value, a record reference,
a payload reference, or a profile-defined value. `requires` preserves the
component's requirements plus any stricter application conditions. An author
cannot discharge a condition by omitting or weakening it in the application.
The planner checks the actual component when constructing this tree.
With a record reference, an optional `output` selects one named output of an
executed application. A planned application's future output cannot be used
as if it existed. Without this selector, the binding names the entire record.

`planned` applications have no outputs or execution result. An `executed`
application has explicit outputs. Its optional `plan` links the prior plan;
component, input bindings, context and requirements must match that plan.
A changed plan receives a new identity and new assessment. The execution
record does not itself establish that execution happened or was correct.
Supersession, earlier-attempt links and dependencies on prior execution
outputs must be acyclic. Informal conceptual links may form cycles.

**Evidence** identifies a component or application, its context, method/policy,
implementation payload, supporting artifacts and a typed result. Its kind is
`formal`, `computation`, `empirical` or `assertion`. A result stored in an imported
module is an attributed declaration, even when it says `passed`. Only a
receiver's explicit verification operation can produce a locally checked result.

## Requirements and checking

Every requirement node has a unique ID within its tree. It has `all`, `any`, or
a profile-defined `leaf`. `witnesses` map leaf IDs to evidence references;
`selections` map `any` node IDs to one selected direct child. A selection must
name a real branch and cannot make that branch succeed. An unknown profile or
predicate returns `unsupported`. A missing applicable proof returns
`unresolved`, not `violated`. Retain every leaf diagnostic, including failures
in alternatives that were not selected.

| Group | Priority of outcomes | Empty group |
|---|---|---|
| `all` | violated, unsupported, unresolved, satisfied | satisfied |
| `any` | satisfied, unsupported, unresolved, violated | violated |

Map these to `incompatible`, `unsupported`, `conditional`, `compatible`.
A satisfied alternative cannot hide an unknown mandatory module profile:
check mandatory profile support first. A receiver may preserve unknown optional
annotations exactly without interpreting them. It cannot execute them or use
them as evidence. Optional unknown interfaces or leaves remain unsupported
when used; an explicit supported alternative may succeed.

Local reports distinguish structural/integrity checking, interface compatibility,
formal verification, computational reproduction and empirical assessment.
`inspect`, `check` and `apply` perform no network access or package-code execution.
They use locally established interfaces and evidence or report remaining
obligations. `verify`/method execution are explicit, policy-bound operations.
Unreviewed-code isolation and a trusted statement comparison remain required
before the stronger unreviewed-contribution policy can be offered.

## Profiles and the minimum new meaning

- [Lean](../profiles/lean.md): native formal statements, environments, actual
  dependencies and named verification policies.
- [Quantities and methods](../profiles/quantity.md): explicit dimensions,
  uncertainty and interpretation of application conditions.
- [Research](../profiles/research.md): optional questions, planned tests,
  contextual assessments, revisions and preserved attempts.

Lean already owns proof composition. Pint owns unit interpretation. RO-Crate
owns the envelope. The new terms connect an exact component application to
its conditions and scoped evidence across these tools. The research profile
keeps a later consumer's question and failed attempt intelligible. The
[direct-tool comparison](../examples/reuse/COMPARISON.md) must still show that
these shared meanings remove repeated integration work.

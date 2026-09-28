# Formal integration decision — 28 September 2026

This closes the formal-tool compatibility probe within SR-T02. The Python
research-cycle baseline, complete feature/cost inventory and frozen shared
comparison still remain before SR-T02 can be marked complete.

## Selected integration

Reuse LeanArchitect for annotations, source locations, blueprint artifacts
and the graph of annotated nodes. Use native Lean interfaces to extract the
actual selected declaration's type, value dependencies and transitive axioms.
The Slean adapter must bind those results to exact statements, source/dependency
identities and a named checking policy. It must keep presentation data separate
from that audit. The generic adapter is SR-T04–06 work, not delivered by this
probe.

The tested environment is Lean 4.34.1, Physlib
`44c66d54be78db4693be9f8f92bd3b5ad124ed6f`, and LeanArchitect
`468e8f58fb4ad6e6ad672a08da6d0d0531e95a97` (its `v4.34.0` tag). No upstream
source patch was needed. The fixture explicitly retains Physlib/Mathlib's
Batteries revision. Every resolved dependency is in the committed Lake lock.

## Executed evidence

Commands from `examples/reuse/direct-lean/`:

```sh
lake build ArchitectProbe:blueprintJson
python3 check_architect.py
```

The upstream exporter produced all seven annotated declarations, including
the imported Physlib theorem and the independently defined `DirectReuse`
theorem. The [recorded result](../../examples/reuse/direct-lean/observed-architect.json)
contains the policy outcomes. The executable check recomputes its findings;
it does not trust this saved report as a verification receipt.

| Probe | Observed result | Consequence for Slean |
|---|---|---|
| Apply the Physlib theorem | Native proof constants and the inferred blueprint edge identify the imported theorem. | Reuse upstream annotations and normal Lean application. |
| Inspect raw JSON | `proof.uses` is empty for that inferred edge. The JSON contains annotations; inference is a separate API. | Call the documented native APIs. Do not treat raw annotation fields as a complete graph. |
| Suppress an actual proof edge | The displayed edge disappears; native term inspection and the underlying collector still find it. | Keep display choices separate from audited dependencies. |
| Introduce an unapproved axiom | Presentation readiness is true; native transitive axioms include the custom axiom. | Apply the declared axiom policy independently. |
| Leave a direct `sorry` | Presentation readiness is false; native inspection includes `sorryAx`. | Retain this useful upstream plan status. |
| Use an annotated unfinished theorem | The child has presentation readiness true and a link to its unfinished parent; its transitive axiom set includes `sorryAx`. | A node's local readiness alone is insufficient. |
| Explicitly suppress `sorryAx` in the annotation | Presentation readiness becomes true; native axioms still contain `sorryAx`. | Never derive a stronger proof-verification status from presentation readiness. |

These are expected distinctions for an editable blueprint tool, not claims
that its presentation flags are intended as an independent proof checker.
The fixtures demonstrate why Slean needs the stated boundary. They do not
establish isolated untrusted-code verification or scientific validity.

## Bounded alternative assessment

The inspected Atlas revision
`3a81e194db0e6c41a2a8c5286f9e1b4962c3866a` targets Lean 4.28.0 and offers
broader graph extraction. Its axiom traversal also walks native declaration
dependencies. The current selected-declaration requirement is covered by the
native APIs executed in this probe: `Expr.getUsedConstants` and
`Lean.collectAxioms`. A second graph system and a toolchain port are therefore
unnecessary for this lot. Atlas was source-inspected, not built with Lean
4.34.1; no compatibility result is claimed for it.

The adapter will preserve both statement and proof dependency sets, including
their overlap. LeanArchitect's `collectUsed` instead returns a graph of
annotated nodes, stops at those nodes and removes most statement dependencies
from the proof set. Both are useful views with different meanings. Neither
view implies that every possible proof needs the recorded dependencies.

## Source references

- [LeanArchitect collector at the tested revision](https://github.com/hanwenzhu/LeanArchitect/blob/468e8f58fb4ad6e6ad672a08da6d0d0531e95a97/Architect/CollectUsed.lean).
- [Inference and JSON output at the tested revision](https://github.com/hanwenzhu/LeanArchitect/blob/468e8f58fb4ad6e6ad672a08da6d0d0531e95a97/Architect/Output.lean).
- [Atlas graph source at the inspected revision](https://github.com/NyxFoundation/lean-atlas/blob/3a81e194db0e6c41a2a8c5286f9e1b4962c3866a/LeanAtlas/GraphData/Core.lean).

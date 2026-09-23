# Same-case Blueprint comparison and Explorer decision

## Case and build

The input is the public projection of the invented [`examples/valid.json`](../examples/valid.json) dossier: one claim, events 1–8, and the separate conditional Lean theorem `Slean.promotionEvidence_has_frozen_observation`. Events 9 and 10 are owner-only in the source case and are deliberately omitted from the Blueprint page. No private research trace enters this comparison.

The [prototype](../blueprint/README.md) compiled on Lean 4.28.0 against [Verso Blueprint v4.28.0 at commit `84fb009`](https://github.com/leanprover/verso-blueprint/tree/84fb00913d07325342e8b73a8a88f6e05ee59473). Its generated site rendered a case page, dependency graph, and progress summary. The graph links protocol, run, artifact, observation, assessment, decision, and claim references; the theorem has a separate complete formal status. This is useful for following declaration and informal dependencies.

Blueprint required manual prose for each public event. It labels these records as mathematical `Definition` nodes and reports the protocol and artifact as ready for formalization. The summary's progress state therefore answers a formalization question, not whether the synthetic assessment is valid. The rendered page states the assessment and decision values but does not read the case JSON or recompute them. Owner-only omission is also a manual publishing choice in this prototype. A custom Blueprint extension could add case ingestion, validation, and audience projection; the prototype does not show that such an extension is impossible.

| Review task | Slean CLI on the same case | Blueprint prototype |
|---|---|---|
| Read the claim and dependency path | `view` derives rows and relations from a validated projection. | Labeled nodes and an interactive dependency graph make the authored path easy to follow. |
| Check event order, references, unit, and exact threshold | `validate` and prefix `replay` check the journal; named mutations fail. | The page repeats fixture values as prose. The Blueprint build does not ingest the JSON journal. |
| Inspect the formal witness | Slean's proof receipt pins one conditional theorem. | The theorem link and formalization status are richer and more navigable. |
| Share an agent view | `export ... agent` removes owner-only events before deriving a view. | The two owner-only events were omitted by hand from this page. |
| Review at a selected journal prefix | `replay` returns the state at that prefix. | The graph shows authored dependencies for the whole page; it has no journal-prefix control. |

## Decision

Build a small local Explorer for the task Blueprint leaves awkward: choose a journal prefix, inspect the decision with its cited observations and costs, and follow the actual validated relation data. It should consume Slean CLI output and default to the agent projection. It must refuse invalid cases and must not turn a local `pass`, Blueprint's `complete`, or an external assessment into an empirical truth claim. Keep Blueprint as the formal-document option; do not recreate its theorem graph or progress dashboard. No 3D task benefit was observed in this comparison, so the Explorer stays two-dimensional.

This decision is about a local prototype. It does not authorize site publication, a public repository/license decision, or integration with Mutome, GERMINAL, or autoresearch.

The resulting [local Explorer](../explorer/README.md) implements the bounded task above. It starts with the agent projection, provides a prefix slider and event links, and displays the checked state at each prefix. The comparison remains scoped to this synthetic case and local UI; it does not establish that the Explorer improves a real research review without a user task study.

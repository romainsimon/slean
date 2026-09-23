# V0 architecture and trust boundary

## Data and execution

`Slean/Core.lean` defines case, question, empirical claim, frozen protocol, run, observation, artifact reference, cost, assessment, decision, formal claim reference, relation, and event. Each recorded object has an ID, positive version, domain, provenance, and audience. IDs are unique within a case. A run names one frozen protocol ID. An observation names a run, metric, unit, exact decimal text or unknown state, artifact reference, and UTC time. Artifacts are references and digests, not embedded blobs. `DependencyExpr` reserves AND and OR syntax but has no V0 evaluator.

`step` applies one event without IO or a clock. `replay` folds a prefix in sequence order. Sequence is the authority; UTC timestamps validate causal edges. A changed protocol must have a new ID and version. The exact comparator multiplies integer significands by powers of ten, so it does not round through a binary float. The V0 automatic assessment uses exactly one observation. An external rule can be recorded, but its assessment cannot become a local `pass`.

The proof `promotionEvidence_has_frozen_observation` says that the executable promotion gate can return a witness only when it finds a passing assessment, its selected observation and run, and the protocol named by both run and assessment. It does not prove that arbitrary State values came from replay, that artifact bytes are sound, or that an empirical finding is true. Replay validation supplies additional tested checks. The compiler checks the proof under Lean's `propext` and `Quot.sound` axioms.

## JSON, CLI, and privacy

`Main.lean` accepts JSON and calls the pure replay function. The schema and semantics versions are both `0.1.0`. The owner path rejects unknown fields. There is no migration path yet. `Slean/Export.lean` redacts an owner-only case header, selects agent-visible events, removes unsupported payload keys, drops references to hidden objects, and renumbers the visible journal before validation and view calculations. Hidden values, private digests, and private provenance do not enter an agent view. The owner remains responsible for marking visible objects for the right audience.

`Slean/Proof.lean` pins one exact elaborated statement and checks its declaration kind and axioms during build. `proof` derives `kernel_checked` only when a claim matches that local pin and toolchain. A JSON field is treated as a declaration. The exporter and the binding from JSON to the local theorem are ordinary code, not kernel-proved. No `independently_rechecked` result is emitted.

`tools/audit_autoresearch_trace.py` is a read-only development adapter. It converts one source trace in memory, sends it to the CLI over standard input, and emits only aggregate counts, check results, and field names in its loss report. It does not change the source evaluator or save source values. The inspected trace uses a multi-observation decision rule that V0 cannot reproduce; see [gate V](docs/gate-v.md).

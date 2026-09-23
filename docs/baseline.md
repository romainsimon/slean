# SL-000 baseline and synthetic fixture provenance

The approved PRD named four defects before this implementation: a changed freeze, a metric or unit mismatch, a missing reference, and an observation after the decision. The [valid fixture](../examples/valid.json) and four named negative fixtures test those exact cases. All values and text in these fixtures are invented and public safe.

| Fixture fields | Origin of shape | Origin of values |
|---|---|---|
| `case_id`, question, claim, version, domain, provenance, audience | Source manifest has attempt ID, question, hypothesis, domain and provenance. Version and audience are Slean V0 fields. | Every string and ID is invented. |
| `event_id`, `sequence`, `kind`, `recorded_at`, `payload` | Source `events.jsonl` uses these roles, with `type` and `observed_at` renamed to V0 fields. | Event IDs, actor, dates, and ordering are invented. |
| Frozen protocol, evaluator, metric, unit, threshold, scope, cap, stop rule | Source `protocol.json`, first `protocol_frozen` event, and manifest budgets motivate the fields. The V0 single metric rule is a Slean choice. | The metric, threshold, evaluator name, cap, and scope are invented. No source protocol or evaluator digest is copied. |
| Run, artifact, observation and typed relation | Source prediction and observation events carry IDs, units, values, and a prediction hash. V0 uses explicit artifact and provenance refs. | Input, seed, digest, value and relation IDs are invented. The repeated `a` and `b` digests are placeholders. |
| Cost, assessment and decision | Source manifest has usage and a separate scientific decision; completion event has a result. | `2.50 cpu_s`, `pass`, and `promote` are invented. No score is copied. |
| Owner-only artifact and observation | Source artifacts include visibility policy; audience projection is a Slean requirement. | Private fixture values are invented, not taken from a source log. |

The four expected failures are `protocol_revision` at event 11, `metric_unit` at event 4, `missing_protocol` at event 2, and `future_observation` at event 6. A valid `override` needs a reason and keeps its separate status. Technical error and unknown fixtures keep an `undetermined` assessment.

## Existing alternatives at the start

| Task | Existing JSON/runtime | Verso Blueprint | Slean V0 target |
|---|---|---|---|
| Keep a source trace and detect file modification | The source runtime writes ordered events, records artifact hashes, verifies file size/hash and paths, and checks its frozen definition on resume or replay. | Blueprint can cite original sources and source spans; it is focused on documents and Lean declarations. | A versioned, independent structural dossier and canonical projection. |
| Prove a Lean declaration and inspect dependencies | The JSON runtime does not do this. | Blueprint tracks formalization progress, `sorry`, theorem dependencies, source provenance, metadata, and a dependency graph. | Link one exact local theorem without claiming empirical proof. |
| Recompute an experimental decision from observations | The domain runtime owns its multi-step evaluator and decision. | No documented experimental event replay or cost rule in the reviewed Blueprint interface; this is a documentation observation, not a claim of impossibility. | Exact one-metric rule, reference and chronology checks. |
| Read a restricted agent view | The source artifact manifest marks visibility but an export policy depends on its consumer. | Blueprint documents source and formal layers; an experimental audience projection is not documented in its public interface. | Project events before table and relation derivation. |

Sources checked: source runtime `oscillator_runtime.py` and `discrimination_runtime.py` in the local autoresearch repository; [Verso Blueprint README](https://github.com/leanprover/verso-blueprint#readme) and [v4.34.0 manual](https://github.com/leanprover/verso-blueprint/blob/v4.34.0/doc/MANUAL.md). Blueprint was compared from its documented API at gate V. A same-case Blueprint prototype and Verso site build were not started because gate V did not pass.

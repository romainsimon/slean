# Product direction

**Slean makes scientific results and methods reusable across investigations and tools.** A person or agent should be able to inspect a component's assumptions and evidence, apply it to new inputs, check the remaining obligations, and export the resulting work for someone else to use.

The selected direction is an open library and interoperability contract built on Lean, existing scientific libraries, Python and research-object standards. The central product action is checked reuse. A graph displays the resulting dependencies; it is not the source of their scientific meaning. Slean must work without Mutome, a website, an LLM or a hosted account.

The initial users are computational research-tool developers and authors of reusable Lean/Python components. The first demonstrations are a calibration method reused by another investigation and a real Physlib theorem applied in another Lean project. Their success is measured against the same tasks using Lean/Physlib, Python and RO-Crate directly.

The [scientific reuse PRD](tasks/prd-slean-scientific-reuse.md) owns the selected scope, implementation choices, acceptance criteria and task checklist. The [research comparison](docs/research/slean-standard-landscape-2026-09-27.md) explains the existing alternatives. The [roadmap](ROADMAP.md) separates that forward work from V0 history. This direction is planned; it is not a released standard or implemented feature set.

## Boundaries

Lean checks formal statements under explicit hypotheses. Computational reproduction checks a named computation. Observations and applicability evidence remain contextual. Slean never merges those into one universal truth or confidence score.

Mutome owns research strategy, execution and resource allocation. It can consume and produce Slean components through the same interface as other tools. GERMINAL owns evaluations of scientific benefit. Slean owns the reusable component contract, its reference tools and conformance fixtures. Initial delivery remains in this repository.

## Implemented V0

The local V0 prototype validates IDs, causal references, units, a single exact threshold rule, known cost caps, and append-only event order. Its 0.2 source-trace boundary additionally checks cross-file provenance and all observation references while keeping the external assessment unverified. Version 0.3 records explicit AND/OR dependency groups without evaluating their truth. It can project an agent view before deriving observation, relation and gate data. A conditional Lean theorem has a separate formal receipt. The theorem does not certify the measurement, evaluator, human decision, or world.

This dossier implementation remains available and independently buildable. Its schemas and existing commands do not acquire new meanings from this product decision. The new component contract has a separate version and implementation milestones.

The [gate V retest](docs/gate-v-retest.md) found one cross-file check that the source verifier does not perform and no omitted source JSON fields. It supported a bounded documentation prototype. The [first V result](docs/gate-v.md) remains the historical negative baseline. Neither result establishes the usefulness or adoption of the new contract; that has its own Gate U in the PRD.

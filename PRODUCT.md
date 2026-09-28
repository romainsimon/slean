# Product direction

**Slean aims to become an open foundation for advancing science in the age of AI.** Humans and AI systems should be able to express, test, challenge and extend scientific work through a shared language and library, with its assumptions and evidence intact.

Its scope is the scientific cycle: questions, hypotheses and models, predictions, experiments, observations, assessments and revisions that enable further research. Unresolved hypotheses and negative results are part of that record. A new agent or tool should be able to resume an investigation from explicit artifacts rather than a private conversation.

The motivating capability is cumulative exploration: a result or method from one investigation can enable progress on another, including a question that was not an initial target. Preserve unsuccessful attempts and explicit obstacles so clients can reassess dormant questions when something relevant changes. Slean checks supported applications; the research system decides relevance, retries and resource allocation.

The selected implementation is a scientific library and interaction contract built on Lean, existing scientific libraries, Python and research-object standards. The first operation is checked reuse. The graph displays the resulting relationships. Slean must work without Mutome, a website, an LLM or a hosted account; other research systems can implement the same contract.

The intended users are researchers and AI systems. The initial adoption route is through computational research-tool developers and Lean/Python authors. The first demonstrations are a real Physlib theorem applied in another Lean project and a calibration used in a second investigation, extended through a prediction, a failed test and an explicit revision. A later contribution must also be checked against a previously blocked application, retaining its remaining obligations and earlier attempts. These are internal engineering tests; the flagship research subject remains unselected. Their success is measured against the same tasks using Lean/Physlib, Python and RO-Crate directly.

The [foundation PRD](tasks/prd-slean-scientific-reuse.md) owns the selected scope, implementation choices, acceptance criteria and task checklist. The [research comparison](docs/research/slean-standard-landscape-2026-09-27.md) explains the existing alternatives. The [roadmap](ROADMAP.md) separates the first delivery lot, longer-term scientific impact and V0 history. The direct-tool baselines and [draft contract fixtures](conformance/README.md) complete M0. Runtime scientific operations and their usefulness remain to be demonstrated; no standard is released.

## Boundaries

Lean checks formal statements under explicit hypotheses. Computational reproduction checks a named computation. Observations and applicability evidence remain contextual. Slean never merges those into one universal truth or confidence score.

Mutome owns research strategy, execution and resource allocation. Slean is intended to provide its shared scientific representation: hypotheses, methods, predictions, observations, evidence and revisions that survive across agents and sessions. Mutome uses the same interface as other research systems. GERMINAL owns evaluations of scientific benefit. Slean owns the scientific contract, its reference tools and conformance fixtures. Initial delivery remains in this repository.

Progress is judged in stages: working scientific operations, independent interoperability, use in another scientific domain, then measured benefit to later investigations. Core conformance and a synthetic demonstration do not by themselves establish scientific impact.

## Implemented V0

The local V0 prototype validates IDs, causal references, units, a single exact threshold rule, known cost caps, and append-only event order. Its 0.2 source-trace boundary additionally checks cross-file provenance and all observation references while keeping the external assessment unverified. Version 0.3 records explicit AND/OR dependency groups without evaluating their truth. It can project an agent view before deriving observation, relation and gate data. A conditional Lean theorem has a separate formal receipt. The theorem does not certify the measurement, evaluator, human decision, or world.

This dossier implementation remains available and independently buildable. Its schemas and existing commands do not acquire new meanings from this product decision. The new component contract has a separate version and implementation milestones.

The [gate V retest](docs/gate-v-retest.md) found one cross-file check that the source verifier does not perform and no omitted source JSON fields. It supported a bounded documentation prototype. The [first V result](docs/gate-v.md) remains the historical negative baseline. Neither result establishes the usefulness or adoption of the new contract; that has its own Gate U in the PRD.

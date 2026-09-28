# Slean: research and direction, 27 September 2026

Status: source-backed comparison and engineering decision. This is not an adoption study, a claim of novelty, or evidence that the proposed integrations work. Public documentation and selected source files were inspected. The upstream projects below were not built in this research pass.

We want scientific results to remain usable across investigations and tools. This matters because storing a conclusion does not preserve the conditions needed to apply it again. The immediate objective is to choose a small, useful interoperability contract and test it against existing tools before expanding it.

## Initial engineering decision

**Mission clarification, 28 September 2026:** the user set the ambition of Slean becoming a new foundation for advancing science in the age of AI. The [updated PRD](../../tasks/prd-slean-scientific-reuse.md) positions checked reuse as the first test of a broader scientific language, checking contract and cumulative library. It adds a hypothesis/prediction/test/revision cycle and separates longer-term impact from initial interoperability. The source comparison below remains evidence about reusable foundations, not proof of that broader ambition.

Build **Slean as an open library and interoperability contract for reusable scientific components**. A component exposes a claim, model, method or dataset with explicit conditions and supporting artifacts. An application records how another investigation uses that component. Lean checks formal statements and applications; computational evidence remains tied to a named method, inputs and context.

The first operation is applying an existing component to a new problem and exposing the obligations that remain. A package format, provenance graph, proof badge, or viewer alone is insufficient. The selected direction and delivery criteria are in the [PRD](../../tasks/prd-slean-scientific-reuse.md).

This is an engineering hypothesis: a thin common contract around formal and empirical reuse can remove repeated integration work. The sources below establish overlap and reusable foundations, not that the gap is unique or commercially validated.

## What already exists and what we will reuse

| Area | Observed capability and source | Decision for Slean |
|---|---|---|
| Formal foundation | Lean distinguishes proof checking, axiom inspection, rechecking, and comparison against a trusted statement. It also distinguishes the correctness of a proof from the intended meaning of its statement. [Lean validation reference](https://lean-lang.org/doc/reference/latest/ValidatingProofs/) | Use Lean's type system and checkers. Define exact verification levels; never invent a second proof kernel or turn compilation into empirical truth. |
| Scientific mathematics | Physlib supplies physics definitions and results on Mathlib. Its source includes dimension-carrying quantities and a harmonic-oscillator energy-conservation theorem. [Physlib](https://github.com/leanprover-community/physlib), [quantity types at the inspected commit](https://github.com/leanprover-community/physlib/blob/44c66d54be78db4693be9f8f92bd3b5ad124ed6f/Physlib/Units/WithDim/Basic.lean), [oscillator module](https://github.com/leanprover-community/physlib/blob/44c66d54be78db4693be9f8f92bd3b5ad124ed6f/Physlib/ClassicalMechanics/HarmonicOscillator/Basic.lean) | Import a real, pinned module. Reuse dimensional types and theorems. Inspect the selected declarations, assumptions and axioms; do not attach one verification status to an entire repository. |
| Numerical computing | SciLean describes scientific computing, differentiation, optimization and differential equations in Lean, and labels itself an early proof of concept. It uses OpenBLAS. [SciLean](https://github.com/lecopivo/SciLean) | Do not build a competing numerical stack. Keep it an optional future execution backend. Slean and SciLean are separate projects; document the name distinction. |
| Python quantities | Pint represents dimensional quantities, performs conversions and rejects incompatible dimensions; its documentation distinguishes offset units from differences. [Pint tutorial](https://pint.readthedocs.io/en/stable/getting/tutorial.html), [offset units](https://pint.readthedocs.io/en/stable/user/nonmult.html) | Use Pint through a pinned, tested mapping to the initial quantity profile. Preserve numerical representation and explicit conversions. Do not infer physical compatibility or exact arithmetic from a successful unit conversion. |
| Formal plans and annotations | LeanArchitect annotates formal/informal nodes, infers statement/proof dependencies, tracks unfinished proofs and exports JSON. Its dependency overrides can change presentation edges. [LeanArchitect](https://github.com/hanwenzhu/LeanArchitect) | First M0 candidate for annotations/export. Keep intended plans separate from audited proof dependencies; its readiness flag does not replace Slean's verification policy. |
| Formal dependency extraction | Lean Atlas exports declaration graphs and distinguishes dependencies in types from those in values/proofs. [Lean Atlas](https://github.com/NyxFoundation/lean-atlas), [extractor source](https://github.com/NyxFoundation/lean-atlas/blob/3a81e194db0e6c41a2a8c5286f9e1b4962c3866a/LeanAtlas/GraphData/Core.lean) | Second M0 candidate if LeanArchitect leaves an extraction gap. Do not infer formal edges with an LLM. A toolchain port is required before combining the inspected Atlas and Physlib heads. |
| Explanation and formalization | Verso Blueprint connects source provenance, informal exposition and formal Lean declarations, and exports graphs and metadata. [Verso Blueprint](https://github.com/leanprover/verso-blueprint) | Reuse document links and presentation where possible. The previous dossier-only Blueprint comparison does not establish that Slean needs a new formal-theorem viewer. |
| Browser authoring | Lean4web is an existing browser editor with configurable Lean projects. [Lean4web](https://github.com/leanprover-community/lean4web) | Integrate an existing editor after local component reuse works. No new compiler or hosted service is required for the first core milestone. |
| Research packaging | RO-Crate 1.3 is a community recommendation published on 22 June 2026. Its profile mechanism allows communities to define additional conventions. [RO-Crate 1.3](https://www.researchobject.org/ro-crate/specification/1.3/index.html), [profiles](https://www.researchobject.org/ro-crate/specification/1.3/profiles.html) | Use RO-Crate as the package envelope with a small Slean profile. Preserve an offline, deterministic core record inside it. Avoid a new archive format, metadata registry or hosted identity service. |
| Execution provenance | Workflow Run RO-Crate has process, workflow and detailed provenance profiles. W3C PROV models entities, activities, agents and derivations. [Run profiles](https://www.researchobject.org/workflow-run-crate/profiles/), [PROV](https://www.w3.org/TR/prov-overview/) | Map executions and artifacts to these vocabularies. A provenance relationship does not prove a scientific implication. Do not require every user to record a laboratory event stream. |
| Small scientific assertions | Nanopublications distinguish assertions, their provenance and publication information. [Guidelines, working draft](https://nanopub.net/guidelines/working_draft/) | Reuse the distinction between a claim and its justification. Citation/export compatibility is useful later; do not claim to have invented portable assertions. |
| Research knowledge graphs | ORKG structures research contributions and comparisons using templates. [ORKG overview](https://orkg.org/about) | Do not compete on paper ingestion or generic graph storage. Slean's first requirement is executable or formally checked reuse, not comprehensive literature coverage. |
| Mathematical interchange | OpenMath represents mathematical objects. OMDoc adds statements, theories and document structure. [OpenMath](https://openmath.org/standard/om20-2017-07-22/omstd20.html), [OMDoc](https://www.omdoc.org/format/) | Keep Lean as the authoritative formal language initially. Do not invent a universal formula AST or claim cross-prover proof translation. Preserve foreign expressions as explicitly identified artifacts. |
| Computational workflows | CWL defines portable analysis workflows with input/output connections and requirements. [CWL 1.2.1](https://www.commonwl.org/v1.2/Workflow.html) | Reference an existing method or workflow. Slean describes its scientific contract and its observed uses; it does not schedule processes or replace a workflow engine. |
| Domain-specific standards | SBML specifies biological models; SED-ML specifies simulation experiments independently of an execution tool. [SBML](https://sbml.org/documents/specifications/), [SED-ML](https://sed-ml.org/) | Preserve native model files and add adapters when a real user needs them. A single new language for every scientific model is not the first deliverable. |
| Compositional simulation | Decapodes composes and simulates multiphysics systems using its domain model. [Decapodes](https://github.com/AlgebraicJulia/Decapodes.jl) | Scientific composition is not new. Slean's proposed contribution is a common reuse contract across proof, method and evidence, not a replacement multiphysics solver. |

## Source compatibility, inspected rather than assumed

These are the default-branch snapshots read through the GitHub API. A pinned toolchain is a source fact, not a successful compatibility test.

| Project | Source SHA | Toolchain | Consequence |
|---|---|---|---|
| Slean V0 | `4f0c40afed7ec443a5561c6d2b5ed2bd147fcfa1` | Lean 4.28.0 | Keep the existing checker and examples as the legacy dossier profile. |
| Physlib | `44c66d54be78db4693be9f8f92bd3b5ad124ed6f` | Lean 4.34.1 | Target for the new formal example; it pins Mathlib 4.34.1. |
| Lean Atlas | `3a81e194db0e6c41a2a8c5286f9e1b4962c3866a` | Lean 4.28.0 | Reuse needs a port or a compatible upstream revision. |
| LeanArchitect | `f45833e26c68aa947044145184f8881a75392e30` | Lean 4.35.0-rc3 | Inspected head differs from the selected Physlib environment. The tag list has `v4.34.0`; lookup of `v4.34.1` did not resolve. A compatible pin/port and build remain M0 work. |
| Goedel-Architect | `300d69e97c91a2a498091c898e736af69f391960` | Lean 4.27.0 in its sample environment | Optional Python proof-search pipeline with Mathlib, LeanArchitect and a Lean server. Not a drop-in dependency of the selected Slean package. |
| SciLean | `95f8119a2884e9c41f82136523bd5568ea7075c5` | Lean 4.28.0-rc1 | Not a mandatory dependency of the selected initial stack. |
| Verso Blueprint | `803b2a87d3d33030e7efac4b4dfa4583760eb190` | Lean 4.34.0-rc2 | Presentation adapter must have its own compatibility check. |
| Lean4web | `27e95901718055152e6d5468e251ca34c13d0b4a` | Project-specific | Pin the configured Lake project; verify editor integration before promising it. |

Lean [4.34.1 has a published release](https://github.com/leanprover/lean4/releases/tag/v4.34.1). Select it for the new package, separately from V0; do not upgrade the existing implementation as an incidental part of this decision. Physlib and SciLean report Apache-2.0, Atlas MIT and Lean4web Apache-2.0 in repository metadata. Blueprint's API metadata did not identify a licence. Inspect actual notices and the relevant source-file rights before copying code; no Blueprint code is copied in this change.

## Strongest alternative

**Use Lean/Physlib, LeanArchitect or Atlas, and RO-Crate directly, with a small integration script.** Blueprint can supply exposition where needed. This has less maintenance and uses existing communities. It is the mandatory baseline, not a straw man.

Choose a distinct Slean contract only if two separately authored investigations can reuse a method/result with less repeated mapping, while retaining assumptions, evidence classes and source identities. Both paths must receive the same data, prose documentation, code and effort accounting. If Slean merely renames fields already shared by those tools, keep the adapter and contribute the missing mapping upstream. Do not keep expanding the format to defend its name.

## Direct Physlib comparison, 28 September 2026

The follow-up comparison materially strengthens this alternative. Physlib's [mission](https://physlib.io/about/mission) explicitly includes connections between experimental data, simulations and formal theory. Its [impact goals](https://physlib.io/about/impact) include AI-assisted discovery and a shared foundation for physics. These are stated objectives, not proof that every workflow exists today. Nevertheless, describing Physlib as theory-only and Slean as the experimental/AI counterpart would misrepresent the overlap.

The live site also exposes [module dependency graphs](https://physlib.io/dependencies), [semantic search](https://physlibsearch.net/) and an [API tracker](https://physlib.io/api-tracker). At the same source SHA `44c66d5` inspected above, the [API-map guide](https://github.com/leanprover-community/physlib/blob/44c66d54be78db4693be9f8f92bd3b5ad124ed6f/docs/API_MAP_GUIDE.md) specifies dependencies, references, planned/completed requirements and declaration locations. These overlap with navigation and structured status features considered for Slean. Page and source inspection is not an interaction test or a fresh Lean build.

Physlib's [README](https://github.com/leanprover-community/physlib/blob/44c66d54be78db4693be9f8f92bd3b5ad124ed6f/README.md) distinguishes its curated core from PhyslibAlpha's lighter review process for rapid human/AI contributions. Its [AI policy](https://github.com/leanprover-community/physlib/blob/44c66d54be78db4693be9f8f92bd3b5ad124ed6f/AI-POLICY.md) requires human responsibility for meaning and review. AI contribution support, unfinished formalizations and explicit assumptions are therefore not unique Slean capabilities.

| Question | Observed Physlib evidence | Consequence for Slean |
|---|---|---|
| Formalize and compose physical models? | Real Lean definitions and conditional results, including harmonic and damped oscillators. | Reuse the existing library; Slean adds no stronger proof guarantee by repackaging the same declaration. |
| Search, inspect dependencies and identify remaining work? | Existing site surfaces and versioned API maps. | Reuse them or document a specific missing task before adding another viewer. |
| Connect a particular instrument/dataset, a frozen prediction/test, a contextual assessment and a revision across research tools? | The mission includes the theory/experiment bridge. This bounded inspection did not establish an existing complete implementation of the exact proposed workflow. | A candidate integration task to test, not evidence of a unique gap or a capability impossible in Physlib. |
| Serve several scientific domains? | The repository explicitly scopes its content to physics. | Slean's wider scope is an ambition; a useful second-domain implementation must substantiate it. Wider scope alone is not better physics tooling. |

The useful comparator is **Physlib plus ordinary experimental tooling, with reusable integration helpers**, not Physlib alone with all surrounding tools removed. A possible pilot uses Physlib's existing [undamped](https://github.com/leanprover-community/physlib/blob/44c66d54be78db4693be9f8f92bd3b5ad124ed6f/Physlib/ClassicalMechanics/HarmonicOscillator/Basic.lean) and [damped](https://github.com/leanprover-community/physlib/blob/44c66d54be78db4693be9f8f92bd3b5ad124ed6f/Physlib/ClassicalMechanics/DampedHarmonicOscillator/Basic.lean) models. Slean would need to make the exact data/model binding, evaluation, revised applicability and handoff to another consumer materially easier. The models and their formal results remain Physlib's contribution. This comparison does not replace the selected calibration fixture without an explicit scope change.

No superiority of Slean over Physlib is demonstrated. M0 must classify each proposed feature as already available, planned upstream, an adapter need, or a potential shared-contract need. Prefer an upstream contribution or adapter when it solves the task with less maintenance. A separate foundation needs demonstrated scientific operations and independent use, not a renamed physics library, graph, or broader mission statement.

## Goedel-Architect and LeanArchitect, 28 September 2026

The user supplied [Goedel-Architect, arXiv:2606.06468v1](https://arxiv.org/html/2606.06468v1), submitted 4 June 2026. The paper builds a directed acyclic plan of definitions and lemmas, attempts node proofs, then revises the global decomposition using failures while retaining usable proofs. The final target statement stays fixed. A proposed graph therefore guides work as well as explaining a finished result.

The authors report 508/672 PutnamBench problems solved (75.6%) for $294 in API calls. Here pass@1 is a pipeline run with up to 16 refinement rounds, not one model response. With natural-language proof guidance and pass@4, they report 597/672 (88.8%) for $985.67. These are reported mathematical proof benchmarks, not reproduced Slean experiments, total engineering costs or evidence of autonomous empirical discovery. Cross-system cost ratios mix model prices and compute budgets and do not establish Slean savings.

The [official project site](https://goedelarchitect.github.io/) links an available [official code repository](https://github.com/goedelarchitect/goedel-architect). Its inspected README describes graph construction, per-node proving, refinement, replayable run artifacts and separate verification. The pipeline can be evaluated later as a Mutome worker; Slean should consume ordinary formal artifacts regardless of which prover produced them. No pipeline installation, execution or paid inference was performed for this review.

More directly reusable for Slean is [LeanArchitect's inspected README](https://github.com/hanwenzhu/LeanArchitect/blob/f45833e26c68aa947044145184f8881a75392e30/README.md). It exposes `@[blueprint]`, separate inferred statement/proof dependencies, incomplete nodes and `lake build :blueprintJson`. It can annotate imported declarations, avoiding copies of Physlib definitions. However, `uses` and `proofUses` may override or suppress edges, and multiple declarations may share a presentation node. Such an export is not by itself the complete dependency/axiom audit required by the formal verification profile. Inspect and build the chosen compatible revision before claiming these capabilities integrate with Physlib. GitHub metadata reports Apache-2.0 for both projects.

The subsequent [executed integration probe](slean-formal-integration-2026-09-28.md) establishes compatibility for tag `v4.34.0` with the selected Lean 4.34.1/Physlib environment. It also refines the JSON claim: raw JSON contains annotations, while computed dependencies and readiness require separate APIs. Presentation suppression, unapproved axioms and transitive unfinished proofs are covered by explicit controls. The earlier head snapshot above remains historical source inspection, not the selected runtime pin.

The design consequences are bounded:

- Evaluate LeanArchitect before writing formal annotations/export; keep Atlas as the second candidate and Blueprint for exposition. These replace the earlier candidate order without adding a new milestone.
- Preserve planned dependencies separately from checked dependencies. A modified statement/environment needs a fresh verification binding.
- Preserve attempt outcomes without promoting them to scientific evidence. An agent's `STATEMENT_WRONG` diagnosis or an exhausted budget differs from a checked negation, and both differ from empirical disagreement under a test's assumptions.
- Keep proof-search strategy outside the standard. The first Slean demonstration must still connect models to observations and revision across consumers. The paper does not establish that this needs a separate Slean contract; Gate U remains decisive.

## Exploration, retrieval and delayed usefulness, 28 September 2026

The follow-up product clarification is exploration without a preselected final theorem: retain diverse research directions, allow questions and definitions to evolve, and preserve results whose utility becomes visible only in later work. This is product intent, not evidence that a particular evolutionary algorithm outperforms a simpler agent with memory.

Three primary-source checks constrain the design:

| Source | Verified scope of the source | Consequence |
|---|---|---|
| [Hipster](https://arxiv.org/abs/1405.3426) | The paper describes an exploratory mode generating lemmas from datatypes/functions in Isabelle/HOL, as well as a mode finding lemmas needed by a supplied proof goal. | Generating questions without a final target is an existing technique. It supports the direction but does not demonstrate broad autonomous scientific discovery. |
| [TheoremGraph](https://arxiv.org/abs/2606.25363), [TheoremSearch](https://www.theoremsearch.com/) | The paper reports a formal/informal statement graph, including 388,105 Lean declaration nodes across 25 projects, and candidate cross-corpus matches. The site documents REST and MCP retrieval. | Reuse existing retrieval before building a global theorem corpus. Preserve whether a link came from a checked term, a paper extractor or a semantic match; a match is not a proof of equivalence. |
| [LeanSearch v2](https://arxiv.org/abs/2605.13137) | The paper describes retrieval of premise groups for a theorem through sketch/retrieve/reflect cycles, with standard and reasoning modes. | Finding reusable formal components is an existing research/tooling area. Evaluate an adapter when retrieval becomes necessary; no hosted search is required by the first offline contract. |

This pass checked paper abstracts and the public retrieval documentation, not every benchmark or scientific case study mentioned in the background conversation. No search endpoint was exercised and no new dependency installed. These sources add comparison evidence, not a third mandatory M0 exporter or an implementation claim.

Slean must permit a question without a fixed target, a new definition within a native model interface, an unresolved alternative, and a subsequent question motivated by an observation. It must not require a proof, an immediate use, or a high planner score for an object to remain representable. Newness relative to an archive, newness relative to literature, correctness and downstream usefulness remain separate assessments.

Keep the initial calibration and Physlib examples as engineering checks. A later GERMINAL experiment should separately compare a single persistent agent, an evolutionary population sharing an archive, and independent explorations under matched total budgets. Freeze archives before revealing held-out downstream questions, record all attempts and costs, and check results independently. Such a study can test delayed usefulness and exploration policies; it cannot attribute gains to the Slean format without the separate direct-tool comparison. No Mutome or GERMINAL implementation is authorized by this documentation update.

## What makes this potentially useful to Mutome

A research agent needs to find a result, inspect its conditions, attempt a valid application, and make the resulting work reusable by later investigations. Slean supplies that exchange and validation boundary. Mutome owns search strategy, execution, resource allocation and decisions. A successful reuse produces a dependency that can be queried; it does not itself establish scientific importance or causal benefit.

The falsifiable claim is reduced integration/reuse effort without more invalid applications. A later benchmark can measure discovery gains. Neither a graph's size nor this architectural choice establishes those gains.

## What this decision displaces

- Further expansion of the V0 audit model as the main product.
- New work on 3D, a global knowledge graph, a hosted proof service, or a bespoke editor before local reuse is demonstrated.
- A separate general-purpose mathematical expression grammar, numerical solver, package registry or orchestration engine. The research profile can add scientific concepts using the selected Lean/Python foundations.
- Mandatory campaign budgets, promotion decisions and private benchmark fields in every scientific component.

The existing validator, projections and Explorer remain available. They are not deleted, rewritten as successes of the new direction, or treated as evidence that the new standard exists.

## Current V0 execution evidence

The prior validation process completed during this research task. At source `4f0c40a`, `bash tests/check.sh` passed 38 Python tests, the Lean build, typed/JSON parity, executable examples and expected type/proof checks. A direct worktree Docker context was refused because its `.git` file points outside the image; rebuilding from `git archive` of that exact SHA succeeded with the ordinary final target for `linux/arm64`.

Local image `slean-local:4f0c40a-validation`, ID `sha256:517790010703b7d5d69aa1d11023415dca844ea8b4f1610333d7abaf7616811f`, passed `tools/smoke_site_image.sh`: healthy internal probe, exact image/artifact SHA, 18 FR/EN pages and served browser checks. The archive correctly reports source cleanliness as unknown. No current AMD64 build, public tag, deployment, scientific benefit or new-standard conformance follows. The smoke container was removed by the script; the local image is retained as the tested candidate.

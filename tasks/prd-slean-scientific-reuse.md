# Slean: an open foundation for cumulative science in the age of AI

Version: direction 2.13, updated 30 September 2026. Status: M0 and M1 (SR-T01–06) and the SR-T07 Python profile API are complete locally. Receiver verification includes reviewed-source components and applications, plus module-bound unreviewed component comparison against a receiver-selected statement. Each policy has separate authenticated local receipts and evidence. The bounded Python authoring and offline quantity reader API is implemented and its wheel works outside the checkout; computational reproduction, the full research cycle and the usefulness comparison remain to be implemented; no standard is released. Owner: Slean maintainer. The user delegated the product and architecture decision, then clarified that Slean must aim to become a new foundation for advancing science in the age of AI. Reuse is the first engineering test of that mission, not its full scope.

This PRD supersedes the **forward implementation direction** of the dossier-first PRD. It preserves V0's code, evidence and limitations. It does not declare the earlier full-program goal complete. Release, repository publication, deployment, outside-project changes, external outreach and new spending retain their existing boundaries.

## 1. Product decision

**Slean's mission is to become an open foundation on which humans and AI systems can build scientific knowledge together.** Scientific work should become explicit enough to inspect, reason about, test, challenge, revise and extend across tools and generations of agents.

The target scientific cycle is **question → hypothesis/model → prediction → experiment → observation → assessment/revision → further research**. Formal deduction and computational reproduction can support several steps. Alternative explanations, negative results, unresolved obligations and contextual disagreement remain visible. The cycle can branch or revisit an earlier step; it is not a mandatory linear workflow.

The first deliverable is an open scientific library and contract that makes a small instance of this cycle work. Its first useful operation is applying an existing result or method without losing what it assumes, what supports it, or where it applies. The graph is a view of those relationships. Slean remains usable without the graph, a website, an LLM, a Slean account, or Mutome.

The analogy with Lean is explicit meaning, checked composition and a growing shared library. Science also needs observations, uncertainty and applicability assessments that cannot be proved from definitions alone. Slean connects these to formal models while keeping their different meanings. It must support an unproved hypothesis as an inspectable research object, without promoting it to an established result. A library of JSON descriptions without an actual scientific application fails this product definition.

The intended users are researchers and AI systems working on cumulative investigations. The initial adoption route is through developers of computational research tools and authors of Lean/Python components. Mutome is the first intended research system using the foundation; the same operations and artifacts must be available to other systems.

The motivating research capability is cumulative exploration: a result or method obtained while investigating A can later make progress on B possible, including a question that was not the initial target. Retain unsuccessful attempts, explicit obstacles and currently dormant questions so that another system can reconsider them when knowledge changes. Mutome chooses questions, transfers and resource allocation; Slean preserves the usable scientific objects and checks supported applications. The calibration and oscillator below are internal engineering fixtures. They are not the selected flagship research subject, and no quantum, biology or other pilot is selected by this PRD.

An adopted standard is an eventual outcome. The initial deliverable is an open specification candidate, a working reference library, two interoperating producers and consumers, and a demonstrated reuse task. A brand, JSON schema or large implementation does not establish adoption.

### What the foundation consists of

| Part | Responsibility | Initial form |
|---|---|---|
| Scientific language | Express a model or claim, its assumptions, predicted observables, methods and evidence with explicit meanings. | Lean definitions plus a small typed research profile accessible from Python. Formal expressions stay in Lean; a separate compiler is unnecessary. |
| Checking and interaction contract | Expose obligations, distinguish kinds of justification, bind tests to exact predictions, and report the effects of new evidence on recorded uses. | Lean checks, numerical adapters and the same library/CLI operations for humans and agents. |
| Cumulative scientific library | Preserve versioned contributions that can be composed, reproduced, disputed and extended across investigations. | Portable modules and a curated example corpus first; independent domain libraries can grow around the contract. |

The AI-specific design requirement is continuity: a new agent, model or tool can resume an investigation from its explicit artifacts, including unresolved hypotheses and failed tests, without reconstructing the reasoning from a private conversation. AI systems propose candidates; their fluency or identity gives those candidates no extra evidential status.

Slean standardizes the meaning of recorded scientific work and its supported operations. Planners choose investigations; existing tools perform numerical calculations, proof search or physical experiments. The small common foundation must permit different planners, laboratories and scientific methods rather than imposing one research strategy.

An investigation may begin with a domain and available operations, without a final theorem or discovery specified in advance. It can introduce a definition, pose a conjecture, compare models or open a new question after an unexpected result. The archive must preserve work whose utility is unknown, including unresolved and unsuccessful branches. Formal validity, empirical support, novelty relative to a searched corpus and later usefulness are separate assessments. Producing more compilable Lean or more graph nodes is not the success criterion.

### Five scope decisions

| Question | Decision |
|---|---|
| What problem do we solve? | Make scientific reasoning and evidence explicit enough that successive humans and AI systems can build on, test and revise the work. |
| What are the central actions? | Express a claim/model, derive a prediction, attach a specified test and observation, inspect or revise the assessment, and reuse the resulting work. |
| Where do we stop? | Slean owns shared scientific semantics and checking interfaces. Existing systems perform proof search, numerical simulation, physical experiments and campaign planning. |
| What proves initial success? | Two investigations exchange and actually use a component; a recorded prediction is tested and revised; invalid uses are detected; another consumer understands the same artifacts. |
| What are our constraints? | Start locally, reuse Lean and domain libraries, preserve existing data, no new paid services, no external-repository mutations or public deployment in this work. |

## 2. Why this direction

The [research comparison](../docs/research/slean-standard-landscape-2026-09-27.md) covers Lean/Physlib/SciLean, LeanArchitect/Atlas/Blueprint/Lean4web, Goedel-Architect, RO-Crate/PROV/nanopublications/ORKG, OpenMath/OMDoc, CWL and domain model standards. Many parts already exist. Slean will combine selected parts around **explicit scientific reasoning that connects formal models to tests and observations**. Checked reuse is the first bounded test of that foundation.

The strongest alternative is Lean/Physlib plus an existing viewer and RO-Crate with a small integration script. It has a lower maintenance burden. Slean must beat that baseline on a real reuse task, not on a format comparison designed to favor Slean.

The [direct Physlib comparison](../docs/research/slean-standard-landscape-2026-09-27.md#direct-physlib-comparison-28-september-2026) is a required design constraint. Physlib already aims to connect theory, simulations and experimental data and to support AI-driven progress. It has scientific content, dependency navigation and contribution infrastructure. Slean's proposed advantage is an easier, portable investigation across tools with explicit data/model bindings and revisions; this has not been demonstrated. "Open foundation", "AI-ready", a graph and reuse of a theorem are not sufficient differentiators.

Reuse Physlib definitions and results as the physics library. Prefer an upstream contribution or adapter for physics-specific gaps. Add a separate Slean contract only for shared scientific operations whose benefit survives comparison with Physlib plus ordinary experimental tools and reusable helpers. Do not create a competing physics corpus to make Slean appear independent.

The [Goedel-Architect follow-up](../docs/research/slean-standard-landscape-2026-09-27.md#goedel-architect-and-leanarchitect-28-september-2026) strengthens the reuse decision. LeanArchitect already represents formal proof plans and exports dependencies; Goedel-Architect uses those plans to coordinate proof attempts and revise unsuccessful decompositions. Evaluate LeanArchitect before creating a new formal annotation/export system. Proof-search orchestration belongs to an optional Mutome worker or another external tool. These mathematical results do not demonstrate empirical scientific discovery or establish the need for a new standard.

The [exploration and retrieval comparison](../docs/research/slean-standard-landscape-2026-09-27.md#exploration-retrieval-and-delayed-usefulness-28-september-2026) also identifies existing theorem discovery and graph/search tools. A library of reusable formal results, cross-paper retrieval and an agent API already have upstream implementations. Slean's proposed contribution must be demonstrated through scientific application and continuity across investigations; a larger graph or a search interface cannot establish it.

The current `CaseFile` journal remains useful for auditing a decision. It does not become the root of every scientific package. A theorem does not need a cost cap or promotion decision. A calibration method does not need to encode an entire campaign to be reusable.

## 3. First complete scientific path

Deliver one **calibration-to-measurement** path and one independent **formal-library reuse** path. Both use the same packaging, identities, evidence records and application operation. Do not standardize the kernel from one synthetic JSON fixture.

### A. A method becomes useful in another investigation

1. An author supplies an affine sensor model, a calibration procedure and observations from a clearly labelled synthetic fixture. The procedure produces gain and offset, a declared operating range and an identified empirical check. This is a software demonstration, not a new physical discovery.
2. The calibration becomes a versioned method component. It contains executable code, input/output quantities, conditions of use, data references and evidence. Calibration parameters are estimates; they are not exact physical constants merely because a file records decimals.
3. A separately authored investigation imports that component, binds its measurements and checks the declared instrument identity, units and operating range. It must not need the calibration author's event journal or private database.
4. The method is executed by ordinary local Python code under an explicit call. Its output and execution evidence are recorded. A Lean theorem can establish the conditional error bound for the specified affine model; it does not certify that the sensor follows that model.
5. The second investigation exports a result with a real `uses` link to the exact calibration version. A third reader finds the result's inputs, remaining assumptions and downstream uses.

The first conditional theorem is an affine inverse/error statement: for nonzero gain, the inverse recovers the input under the exact model; with an explicitly assumed residual bound, the reconstructed error has the derived bound. Include parameter uncertainty as unresolved unless the selected theorem actually accounts for it. Do not quietly substitute a fitted gain for an exactly known gain.

The concrete fixture is a displacement sensor: `voltage = gain × displacement + offset`. A synthetic calibration with gain `2 V/mm` and offset `0.5 V` makes a reading of `8.5 V` yield `4 mm`; omitting the offset yields the detectable wrong output `4.25 mm`. Under an exact gain and an assumed voltage residual bound of `0.02 V`, the conditional displacement error bound is `0.01 mm`. The exported result must also show the selected sensor, operating range and outstanding applicability/parameter assumptions. The author writes normal Lean or Python and small declarations; the exporter generates IDs, provenance and packaging.

Negative cases: a wrong dimension; a value outside the declared range; absent evidence for a precondition; changed method bytes; wrong sensor identity; a claimed output produced without the offset correction; a justification for the wrong version. Each must produce a specific result, not a green package badge.

### B. A real formal result becomes a dependency

Import the selected harmonic-oscillator module from pinned Physlib. Inspect the energy-conservation theorem, its statement, assumptions, proof dependencies and axioms. In a separate Lake project, apply it in a new theorem with explicit hypotheses. Re-export the new declaration and inspect the dependency in another consumer.

Attempt to apply the undamped result to a context where the required equation of motion has not been established. Report the missing obligation. If measured energy falls, preserve the mathematical theorem and attach the observation as evidence about applicability; do not retract the proof automatically.

### C. New evidence changes what can be used next

Extend the same sensor fixture into a complete, small research cycle. State an explicit hypothesis extending the affine model to a new operating condition. Bind a prediction and an evaluation rule to an application plan before revealing that fixture's new observations to the consumer. Run the named comparison, then introduce a synthetic observation outside the declared residual bound but within the hypothesis's stated test scope. An out-of-scope test must not be recorded as a refutation of the narrower original claim.

Record the failed prediction and the precise context it challenges. Find potentially affected applications by following exact assumption references and selected branches within the indexed corpus, retaining their context. List them for reassessment; do not assert that their outputs or the conditional Lean theorem are automatically false. Publish an explicit revised model/condition as a new component and make a new prediction for a separate observation. Preserve the original hypothesis, failed test and the reason for the revision.

Acceptance: another consumer reconstructs the hypothesis → prediction → protocol → observation → assessment → revision links from exported objects, with no private chat transcript. It can record a new question motivated by the unexpected observation and leave an alternative explanation unresolved; both survive interchange alongside the original result. Changing a rule after seeing observations must produce a new revision and cannot alter the earlier assessment. The recorded order is a property of this controlled example, not proof of real-world preregistration. This fixture demonstrates the research contract; it does not claim an autonomous discovery.

### D. A later contribution permits a blocked application

Extend the same fixtures, without introducing another scientific domain. A consumer exports an unresolved question, its attempted application, the exact unsatisfied requirements and its previous attempt outcomes. A later contribution from another investigation supplies a candidate result or executable method. A separate consumer can recover the obstacle, inspect the contribution, and explicitly recheck the application under the same requirement and verification policies. Preserve the old attempt and cite the precise new evidence or method version in the new attempt.

An exact reference or a compatible declared interface can identify a candidate for reassessment; it is not itself a witness that resolves a scientific obstacle. Semantic similarity, an agent critique, a timeout or a bare new citation cannot satisfy a missing requirement. A contribution for a different statement, version or context must leave that requirement unresolved or report the specific incompatibility. An unrelated contribution must not change the recorded result. If only part of a requirement is resolved, the rest remains visible.

Store question, attempt and obstacle metadata in the optional research profile, referring to existing component/application/evidence records. Do not add a scheduler, background process, universal relevance score or compulsory planner state to Slean. A dormant question requires no active computation. A client decides whether and when to retry; an explicit retry creates new records.

Acceptance: a second reader reconstructs what was blocked, what changed, which supported check now succeeds and what remains open. Include reuse of a method as well as a result, and retain a follow-up question whose usefulness is unknown. This scripted fixture establishes portable state and checked reuse. It does not prove autonomous discovery, independent novelty, or that the contribution caused a research gain; those require the controlled study below.

These paths establish initial representation, composition and scientific-cycle behavior. Cross-domain adoption and improved scientific outcomes have their own horizons below. A later biology or materials profile must be possible without changing the meanings of the initial core fields.

## 4. The contract

### 4.1 Small module, typed exports

A **module** is a portable package with a manifest, exported components, exact dependencies and supporting files. It can be a local directory. It does not require a registry. The working contract identifier is `slean-module/0.1-draft.1`, deliberately separate from the V0 `0.1`–`0.3` dossier schemas.

There are three record families. They must not become an unrestricted collection of required fields.

| Record | Required meaning | Initial profile content |
|---|---|---|
| Component | A named, versioned item someone can refer to or use; kind `claim`, `model`, `method` or `data`; interface, conditions, source and rights | A Lean declaration or type; a Python method with typed ports; a dataset with a declared schema |
| Application | A use of an exact component with explicit input bindings, requirements, selected alternatives and outputs | A theorem application; a method invocation; a model-to-observation comparison |
| Evidence | A justification about a precise subject and context, with method, artifacts and check result | A proof check, a recomputed calculation, an empirical evaluation or an attributed assertion |

Files, people, software and executions use existing research-object metadata. The initial research profile links a question to target claims and observables through profile metadata. A hypothesis is a claim with unresolved obligations; a prediction names an expected observable under stated conditions; a planned test is an application. Assessment and revision use evidence and explicit version links. A planned application has no executed output or execution evidence until those are explicitly supplied. Formal-only modules do not need an experiment. Historical contributions, annotations, citations, costs and instrument inventories can attach through further profiles.

A question may precede any target claim. Its wording, source and motivating artifacts are attributed research metadata, not an established conclusion. New definitions remain native Lean declarations or parts of a model interface. A planner's priority or selection score can be an optional annotation; it cannot determine scientific verification or whether a contribution is representable. Preserve competing explanations and dormant branches without requiring a universal fitness function or adding another mandatory record family.

A claim may have several justifications. The claim and its proof are distinct. Two different proofs may have different dependencies. An empirical contradiction does not invalidate a conditional theorem; it can change the assessment of its applicability. No single `true`, `verified` or numerical confidence field collapses those distinctions.

### 4.2 Conditions and composition

`apply(component, bindings, context)` returns an application plan with typed bindings, an explicit requirement tree, and one of `compatible`, `conditional`, `incompatible`, or `unsupported`. These names describe compatibility under the specified checker, never universal scientific validity.

Requirements use `all`, `any`, or a profile-defined leaf. Empty `all` is satisfied; empty `any` is unsatisfied. An alternative records which branch supplied the witness. An unsupported alternative does not invalidate an already satisfied alternative, but it cannot satisfy an unresolved one. Every unresolved leaf remains inspectable.

Leaves return `satisfied`, `violated`, `unresolved` or `unsupported`, with a reason. A missing proof is `unresolved`, not a refutation. Aggregate in the following order; retain all leaf diagnostics even when one branch determines the status:

| Expression | Deterministic aggregation |
|---|---|
| `all` | Any `violated` → `violated`; otherwise any `unsupported` → `unsupported`; otherwise any `unresolved` → `unresolved`; otherwise `satisfied`. |
| `any` | Any `satisfied` → `satisfied`; otherwise any `unsupported` → `unsupported`; otherwise any `unresolved` → `unresolved`; otherwise `violated`. |

Map `satisfied` to `compatible`, `violated` to `incompatible`, `unresolved` to `conditional`, and `unsupported` to `unsupported`. Compatibility is relative to the declared requirements and checker policy. Unsupported mandatory semantics at the module level stop checking before this aggregation; an unrecognized requirement can only be bypassed through an explicit supported alternative.

The initial leaves are:

- A Lean proposition requiring a proof term in a pinned environment. A supplied textual statement, natural-language match or empirical score is not a proof term.
- A declared data/interface check: shape, quantity dimension, explicit unit conversion, method version, sensor identity or bounded operating range.
- An empirical applicability assertion with attributed evidence and context. It stays an assumption unless the selected deterministic predicate can actually check it. A finite successful test does not discharge a universal physical hypothesis.

Profile checkers return their method and inputs with each result. No general theorem search, natural-language inference or universal statistical inference engine is built into `apply`. Conversion between units is an explicit transformation with a known convention, including offsets where relevant. Unknown dimensions cannot be silently treated as dimensionless.

The first computational profile supports named scalar quantities and tables of those quantities. It carries the declared dimension, unit, exact decimal or missing value, and either a specified absolute error bound or an explicit unknown uncertainty. A bound and a statistical confidence interval are different types; an interval requires its method and stated interpretation and is unsupported by this first profile. Initially support only the quantity/constraint types needed by the sensor example, with negative fixtures for unsupported types. Reuse Physlib's dimensions and Python's Pint library through explicit, tested mappings; matching arbitrary unit strings is insufficient. Pin Pint, the selected unit definitions and that small mapping in M0 before implementing the SDK. Numerical executions record their numeric representation and comparison tolerance; decimal serialization does not make floating-point computation exact.

For formal composition, Lean's type checker is authoritative. For computational composition, the declared input/output contract and supported predicates are checked. Matching types establishes interface compatibility, not adequacy of a scientific model. Resource reservations and consumption are an optional future execution profile; the runtime, not this package, owns actual availability.

### 4.3 Dependencies, versions and evidence

Keep distinct relations for statement dependencies, dependencies of a particular proof, method inputs, generated outputs, empirical support/contradiction, and informal analogies. Reverse queries are restricted to the indexed corpus and versions. An edge never means that no alternative derivation exists.

Keep proposed proof-plan edges separate from dependencies extracted from checked terms. LeanArchitect allows authors to override or suppress presentation edges, so its blueprint graph is not by itself a complete proof-dependency audit. Preserve links to native blueprint artifacts; do not standardize a second proof-plan language. Changes to a statement or its environment require renewed verification before old proof evidence can support the revised object.

Freeze components at export. A change creates a new revision. Record `supersedes` separately; never silently redirect old applications to a newer component. Retractions and later evidence append contextual records rather than changing old bytes. A new annotation module may link existing objects, including conceptual cycles. Build dependencies and chronological execution references must remain resolvable without a circular content hash.

Module content identity uses a canonical manifest containing the sorted names, sizes and SHA-256 digests of all declared payloads. Internal references use local IDs; external references use an exact module digest and local ID. Compute SHA-256 over the UTF-8 bytes of `slean-module/0.1-draft.1\n` followed by the [RFC 8785 canonical JSON](https://www.rfc-editor.org/rfc/rfc8785) of that manifest without its own ID field. Exact scientific decimals are strings. Detached verification receipts, generated indexes and generated RO-Crate metadata are outside this digest to avoid circular references. Their scientific inputs belong in the manifest or its declared payloads; generated metadata cannot add authoritative facts. Reject duplicate JSON keys and duplicate or unsafe payload paths. M0 freezes the precise wire schema and cross-language hash vectors. Hash equality means equality under this encoding, not equivalence of scientific meanings.

Lean source, declaration name, module, exact toolchain and dependency lock identify formal objects. Preserve the native elaborated statement through the Lean profile, with a versioned encoding/fingerprint. Do not use pretty-printed text as the sole semantic identity or invent a cross-prover formula language. Cross-version equivalence requires an explicit checked bridge.

### 4.4 Verification levels

Report separate results for package integrity, interface compatibility, formal verification, computational reproduction, empirical evaluation and human interpretation. In particular:

- An imported receipt is a statement by its issuer until the receiving verifier checks it under a named trust policy.
- The general Lean adapter handles selected user declarations, not the single theorem hard-coded in V0. It checks actual proof dependencies, transitive axioms, exact statement/environment binding and incomplete proofs.
- The baseline reviewed-source policy permits Lean's standard `propext`, `Classical.choice` and `Quot.sound`, reports them, and rejects `sorryAx` or unapproved axioms for that policy. A different policy remains explicit. No claim that all formal science is axiom-free.
- For unreviewed agent contributions, use an isolated build and the supported comparator/checker path against a separately trusted statement. Verify the pinned tools actually support this path. If unavailable, return `unsupported`; do not downgrade silently to a build-only badge.
- A reproduced Python output is a reproduced computation. It does not prove its method is statistically appropriate, its observations authentic or its model physically valid.
- A source summary is not a formalized statement. The link between prose and formal content carries its attribution and review status.
- A prover timeout, exhausted budget or agent diagnosis such as `STATEMENT_WRONG` is an attempt outcome, not evidence of falsity. A checked proof of the negation is formal evidence bound to the exact statement and context. An observation that disagrees with a prediction is a separate empirical assessment under the named model, test and uncertainty assumptions.

Building Lean projects or running Python can execute arbitrary code. Ordinary `inspect`, `check` and `apply` are offline and do not execute package code. Proof builds and method execution are explicit operations in an isolated workspace with pinned dependencies, bounded resources and no credentials or network by default. The current local, reviewed examples can be the first supported execution policy; hostile remote uploads are not a V1 service.

The offline CLI plans an application using locally checked interfaces and records outstanding proof obligations. It cannot mark a newly supplied proof as checked from text or an imported receipt. A formal application is authored as ordinary Lean code and then checked through the explicit verification operation before its evidence is available to the planner. This separates planning from execution without adding another proof engine.

## 5. Standards and implementation choices

| Concern | Selected implementation |
|---|---|
| Scientific definitions and formal applications | Lean 4 library, ordinary definitions/theorems and a small annotation/export API. No compiler fork; no separate `.slean` grammar initially. |
| Initial formal environment | New package pinned to Lean 4.34.1 and the inspected Physlib revision, with its Mathlib lock. Keep V0's Lean 4.28 package independently buildable. Verify compatibility in M0 before claiming it works. |
| Core semantics | A small deterministic Lean reference checker for module references, application requirements and evidence bindings. Prove selected composition properties where useful; exported JSON and adapters remain ordinary audited code. |
| Computational authoring | Python SDK with explicit component declarations, Pint quantities and a wrapper around an existing function. No mandatory rewrite of Python computations into Lean. |
| Exchange | RO-Crate 1.3 envelope plus a versioned Slean profile and `slean-module.json` payload. Metadata points to core IDs; the payload is authoritative for Slean semantics. Conflicting duplicate facts are errors. A generic crate reader can inspect files/provenance; it need not understand Slean proofs. |
| Offline use | Bundle and pin contexts/schema definitions; no runtime web context retrieval. A small core reader does not need an RDF store, SPARQL, Neo4j, embeddings or a server. |
| Search and navigation | Local exact/text search and derived dependency index first. Never confuse semantic search similarity with a formal edge. |
| Formal annotations and export | Use LeanArchitect `468e8f58fb4ad6e6ad672a08da6d0d0531e95a97` for annotations/blueprints, with native Lean term and axiom inspection for the audit. The [executed compatibility probe](../docs/research/slean-formal-integration-2026-09-28.md) shows why raw JSON annotations and presentation readiness cannot supply that audit. No upstream patch or Atlas port is needed for selected declarations. Reviewed component verification binds the native statement and import artifacts. Its application adapter binds fresh native captures and exact producer environments; capture fidelity still relies on reviewed caller source. |
| Viewer | Reuse Blueprint for exposition where appropriate. Extend the current TypeScript Explorer for component/application/evidence inspection only after the core reuse task works. A presentation graph cannot replace verified dependency extraction. |
| Proof search | External and optional. Goedel-Architect is a candidate worker for Mutome, not a mandatory Slean dependency or a new Slean orchestrator. M0–M2 require no paid prover run. |
| Editor | Local Lake project first. Evaluate a pinned Lean4web project for browser authoring later. No hosted compiler in the core package. |
| Agent access | Python library and JSON CLI returning the same objects as the viewer. MCP is a thin later transport, not the standard itself. |

The RO-Crate envelope is an interoperability deliverable, not an additional manually maintained source of truth. Generate it from the component manifest and known provenance mapping. Only claim conformance after base and profile checks pass. Preserve native CWL, SBML, SED-ML or other domain files when present; future adapters must report unsupported semantics and losses.

Initial module operations, **planned rather than current CLI commands**:

```text
inspect: component, assumptions, interface, evidence and exact dependencies
apply:   component + input bindings + context -> compatibility and obligations
verify:  an explicit supported proof/computation check -> detached report
pack:    exported components + dependencies + artifacts -> portable module
uses:    exact component -> recorded applications within the selected corpus
```

Authoring a hypothesis, binding a prediction/test and appending a revision use the typed library API and the research profile. Freeze those signatures and their fixtures in M0. Do not add a separate service or CLI subsystem for each scientific concept. Experiment execution remains an explicit call to an existing tool; Slean checks and exports the resulting records at its supported level.

Use one public-source monorepo with independent package builds: `spec/`, `packages/lean/`, `packages/python/`, `profiles/`, `conformance/`, `examples/reuse/`, and `explorer/`. M0 supplies the specification, profiles, draft conformance fixtures and direct-tool examples. `packages/lean/` now supplies selected-declaration extraction; the Python runtime and new Explorer behavior remain planned. Existing `Slean/`, CLI, fixtures and site remain intact during the first milestones. The public marketing website already has a separate `slean-web` repository; do not merge or modify it in this work. Documentation generated from the library stays with the library.

## 6. Required behavior

| ID | Requirement and acceptance evidence |
|---|---|
| SR-01 | A fresh checkout builds the new Lean package independently of Mutome and the legacy dossier package; all dependencies are pinned. |
| SR-02 | A Lean producer and separately authored Python producer emit modules consumed by both a CLI and a separate minimal reader. Same IDs, conditions, evidence kinds and dependencies survive interchange. |
| SR-03 | A selected real Physlib theorem is reused in another Lake project and its new formal dependency is extracted from checked code. The theorem is not copied into a string or replaced with a synthetic validator theorem. |
| SR-04 | Two separate computational investigations reuse the calibration component and complete the prediction/test/revision cycle in section 3C. The consumer never needs the producer's private journal or chat. Omitted offset correction is exposed by reproduction against the declared method. |
| SR-05 | Wrong dimensions, missing assumptions, wrong context/version, forged evidence and unsupported profiles produce explicit diagnostics. No listed negative fixture is accepted as an unconditional application. |
| SR-06 | Several proofs of one claim and several alternative methods remain separate. `all`/`any` witnesses and unresolved requirements agree between the reference checker and the reader. |
| SR-07 | A contrary observation changes a contextual assessment and identifies recorded applications whose assumptions need reassessment, without changing a checked conditional theorem or old evidence. A revision creates a new identity. Unknown is not false, zero or an implicit success. |
| SR-08 | A receiver recomputes verification at the declared level. Missing dependencies, `sorry`, unexpected axioms, changed statements and fake receipts cannot produce the stronger verification level. |
| SR-09 | A generated RO-Crate passes base/profile checks and can be read by an existing independent RO-Crate tool. All supported Slean records survive a Slean round trip; unsupported extensions are retained but not executed. |
| SR-10 | Explorer and CLI expose matching objects and obligations, with direct/reverse dependencies and cited evidence. Browser checks cover desktop/mobile, keyboard, reduced motion and an equivalent accessible list. |
| SR-11 | An agent-shaped consumer resumes the section 3C–D investigation through the public library/CLI contract: inspect its unresolved hypothesis and obstacles, bind a test, ingest the named tool output, record the assessment, and export a revision plus a follow-up question while preserving an unresolved alternative. A later contribution can be explicitly checked against a blocked application, without rewriting its earlier attempt or accepting a mere suggested connection as evidence. It needs no private conversation state, Mutome imports or repository changes. |
| SR-12 | The package works offline after dependencies are installed, requires no hosted account, and executes no package code during inspection. An explicit publication projection contains only selected publishable artifacts; hidden fields cannot affect public IDs or derived views. |
| SR-13 | Changing a component produces a new identity; old applications remain reproducible. Unknown mandatory semantics fail closed. A migration produces a new module and an explicit mapping/loss report. |
| SR-14 | The specification, conformance fixtures and reference tools are enough to implement a reader without importing Slean's implementation. External adoption and independent validation are reported separately from internal interoperability. |

For SR-12, export only an explicit selection of publishable components and supporting files into a new module. Compute its identity from that selection. Do not include hidden fields, private ancestor digests or the original private module ID automatically. This is an explicit export operation, not an automatic classifier of sensitive scientific data.

## 7. Delivery order and tasks

SR-T01–07 are **complete** with the local evidence linked below. SR-T08–16 are **not started**. A task is complete only when its full acceptance evidence is recorded. Existing V0 work is not used to tick them. The repository's roadmap links here so milestone status has one owner.

### M0: reuse the ecosystem and freeze the comparison

- [x] **SR-T01: pin and build the formal sample.** [Local evidence and commands](../examples/reuse/direct-lean/README.md#validation-on-28-september-2026): pinned Lean 4.34.1/Physlib/Mathlib; actual energy-conservation theorem applied; interfaces and transitive axioms recorded; missing-hypothesis and changed-statement controls rejected. This closes the sample task, not the general exporter, fresh-checkout conformance or usefulness gate. Contributes evidence to SR-01, SR-03, SR-08.
- [x] **SR-T02: make the direct-tool baseline.** Express the two reuse paths, including the section 3C–D prediction/test/revision cycle and later reassessment of a blocked application, using Lean/Physlib and Python with RO-Crate, without a Slean wrapper. Classify each proposed feature against current Physlib and LeanArchitect as available, planned, an adapter need or a shared-contract candidate. Inventory the mapping code and manual decisions. Freeze identical inputs, negative cases, tasks and effort accounting for both paths. Evaluate the two formal integration candidates in order: LeanArchitect, then Atlas if necessary. Select reuse, a bounded port or a small native extractor with a written reason. Check toolchain compatibility and whether overridden blueprint edges can conceal actual proof dependencies.

  Evidence: [formal integration probe and decision](../docs/research/slean-formal-integration-2026-09-28.md), [Python/Pint cycle and RO-Crate reader](../examples/reuse/direct-python/README.md), [conditional calibration theorem check](../examples/reuse/direct-lean/observed-calibration.json), and [comparison, feature/mapping inventory and effort rules](../examples/reuse/COMPARISON.md). The [freeze](../examples/reuse/frozen-baseline.json) covers 34 files and 22 case groups. Eleven Python tests passed, including reproduction from exported source outside the checkout; Lean rejected both missing calibration hypotheses. The before/after blocked attempts retain exactly the same measurement input and method. This closes the direct-tool baseline, not Slean's implementation, full RO-Crate/profile validation, Gate U, autonomous exploration or external adoption.
- [x] **SR-T03: specify the first contract and fixtures.** Turn section 4 into `spec/` documents, typed authoring signatures and positive/negative fixtures, including an unresolved hypothesis, a planned test, a failed prediction, a revision and a new question without a fixed target theorem. Include the section 3D obstacle/attempt metadata and its result/method reuse cases in the same optional research profile. Demonstrate which shared scientific meanings require new terms. No universal science ontology or unexplained opaque blobs for the example's core conditions.

  Evidence: [draft wire contract and meanings](../spec/README.md), [authoring signatures](../spec/authoring.pyi), [Lean](../profiles/lean.md), [quantity](../profiles/quantity.md) and [research](../profiles/research.md) profiles, and [executable fixtures](../conformance/README.md). The [recorded check](../conformance/observed-contract.json) passes nine tests covering three positive modules, 41 negative cases, 34 requirement vectors and eight identity vectors checked in Python and JavaScript. The [unit mapping check](../conformance/observed-units.json) passes 21 conversions across seven pinned units. Imported proof claims remain declared. The authoring signatures are syntax-checked stubs; this closes specification work, not a runtime SDK, scientific verification, the SR-T14 independent reader or Gate U.

### M1: formal components can actually be reused

- [x] **SR-T04: implement the general Lean exporter.** Adapt the upstream export selected in M0 where possible. Export selected declarations, exact source identities, distinct statement/proof dependencies, axioms and formal interface. Import modules through ordinary Lean/Lake; no hard-coded theorem names. Verify that suppressed presentation edges, incomplete plans and agent diagnoses cannot produce stronger verification results. Covers SR-03, SR-08.

  Evidence: [exporter and trust boundary](../packages/lean/README.md), [second Lake project](../examples/reuse/with-slean-lean/README.md), and [recorded end-to-end check](../packages/lean/observed-export.json). Eleven declarations are selected through Lean's name resolver, including a Physlib theorem, two uses, a definition, a polymorphic theorem, a quoted name and negative proof fixtures. Native encoding passes ten constructor vectors and five open-term rejections; three invalid selections are rejected. Eight bridge tests preserve actual dependencies despite presentation suppression, distinguish transitive `sorryAx`/custom axioms, bind source and statement bytes, and keep forged readiness/receipts at declared status. The output uses extraction-only evidence, not a receiver proof receipt. Source snapshots and compiled identities are separate; reconstruction and verification remain SR-T05–06. This closes extraction, not all of SR-03/SR-08 or Gate U.
- [x] **SR-T05: implement formal application.** Bind a real theorem in a second project, expose remaining hypotheses, check the new proof and export its actual dependencies. Test a changed statement and missing hypothesis. Covers SR-03, SR-05, SR-06.

  Evidence: [native application and trust limits](../packages/lean/README.md#apply-a-declaration-in-ordinary-lean), [two real uses](../examples/reuse/with-slean-lean/ApplicationExample.lean), and [recorded application check](../packages/lean/observed-applications.json). Both consumer proofs compile under the original hypotheses. One capture exposes the equation-of-motion goal before the following proof step closes it; the complete invocation leaves no goal. Whole-declaration and nested-goal controls preserve the correct scope. Lean rejects the missing hypothesis and changed conclusion. Eleven application tests and eight exporter bridge regressions pass; all 34 frozen baseline files remain unchanged. Exact module/statement references and actual proof dependencies accompany the applications. Input plans are retrospective projections, not preregistration. Imported results remain declared and inspection remains conditional without receiver proof verification. This closes native application, not general offline planning, the broader covered requirements, SR-T06 or Gate U.
- [x] **SR-T06: implement the verification policies.** Reviewed-source checks and an isolated unreviewed-contribution path have distinct reports. Recompute from exact artifacts; reject forged or downgraded receipts. Covers SR-08, SR-12.

  Implemented: the [reviewed-source receiver](../packages/lean/verification/REVIEWED.md) reconstructs local source modules, replays them with Lean's bundled checker and audits the actual statement, dependencies and transitive axioms with imported extension initializers disabled. Exact installed dependency binaries remain receiver-trusted and bound by hashes. The [native application adapter](../packages/lean/verification/REVIEWED_APPLICATIONS.md) reconstructs the consumer and its exact producer, then regenerates the captured invocation and retrospective plan. Capture fidelity relies on reviewed caller source using known instrumentation. Caller hypotheses remain conditions and extra producer requirements stay unresolved.

  The separate [unreviewed component operation](../packages/lean/verification/UNREVIEWED.md) reconstructs the receiver-selected reference before executing candidate source, exports both environments in bounded streams, runs pinned Comparator and replays the candidate proof in Lean's existing kernel. Receipt dependencies and axioms come from the checked textual constants, rather than the candidate binary's diagnostic metadata. Receipts bind the candidate, reference, statement, environments, exact artifacts and named policy. Offline inspection requires that receiver's authentication and never executes package code. Missing tools return unsupported and cannot downgrade the policy. Definition holes and unreviewed application captures remain unsupported. The macOS backend lacks hard memory and aggregate disk/job quotas; this is an explicit local operation, not a hostile-upload service. This closes the two local formal policies required by SR-T06; computational reproduction, public projection and Gate U remain later requirements.

  Evidence: the [28 September receiver check](../packages/lean/verification/observed-reviewed.json) passes ten control groups, including four namespace-layout regressions. Two real Physlib consumer proofs and three quoted/polymorphic or ordinary proofs receive local receipts; four incomplete or unapproved-axiom proofs do not. Wire-valid statement and dependency changes, receipt tampering, wrong receivers/policies/revisions and payload changes cannot inherit a passing result. All 34 frozen baseline files remain unchanged. The report binds 14 implementation/test hashes and 5,611 modules; the complete check took 1,883.219 seconds locally. This is component verification evidence, not application capture verification or a usefulness result.

  Application evidence: the [30 September native application check](../packages/lean/verification/observed-reviewed-applications.json) passes six control groups. Both Physlib invocations are reconstructed and authenticated: one leaves a goal that later proof steps close, and one supplies all arguments. A wire-valid forged capture is rejected after reconstruction. Wrong policies, plan misuse, another producer revision and changed instrumentation are rejected before execution. Offline inspection rejects altered receipts, another receiver, a different context and another module revision without executing code or opening the network. All 34 frozen baseline files remain unchanged. The complete application check took 109.368 seconds and binds 5,611 import modules. This is a different validation sequence from the earlier component check; its elapsed time is not a measured speed advantage or a Gate U result.

  Current policy regression evidence: the [reviewed component report](../packages/lean/verification/observed-reviewed-policy-regression.json) passes ten groups at the current shared implementation, and the [reviewed application report](../packages/lean/verification/observed-application-policy-regression.json) passes six. Their complete local sequences took 449.064 and 319.032 seconds respectively; these are observations, not matched performance comparisons. The [unreviewed report](../packages/lean/verification/observed-unreviewed.json) passes nine groups: a real dependency-bearing Physlib proof, kernel-derived metadata despite fabricated binary diagnostics, a quoted native name against a separately selected unproved statement, exact-policy offline authentication and three candidates rejected after build/export for the precise statement/axiom errors. It preserves all 34 frozen baseline files and binds 13 source hashes. The complete local sequence took 1,585.268 seconds; its two Physlib exports were 327,233,941 bytes each. Those costs belong in Gate U accounting. Neither a passing local comparison nor this task completion proves empirical validity, scientific usefulness or external adoption.

### M2: empirical methods compose with explicit conditions

- [x] **SR-T07: implement the Python method/profile API.** Declare quantities, ports, range and identity constraints; emit method/application/evidence records. Keep exact decimals and explicit uncertainty interpretation. Test dimensional conversion rather than string equality alone. Covers SR-02, SR-04, SR-05.

  Evidence: the [bounded Python API](../packages/python/README.md) authors quantities, scalar/CSV ports, range/identity/applicability leaves, components, plans, execution records and attributed evidence. The [dated SDK check](../packages/python/observed-sdk.json) passes 25 test groups, including three shared positive modules, 41 negative vectors and 34 requirement vectors. A built wheel is installed into a temporary directory and exercised in an isolated process with no checkout imports: a producer exports a method, a consumer preserves its exact revision and conditions, and a reader inspects that application and reverse use. The checks preserve long decimal spelling, pinned Pint definitions, missing values, explicit uncertainty and every alternative diagnostic. They reject changed bytes, unsafe paths, private unselected ancestors, unknown mandatory semantics and changed retry inputs. All 34 frozen direct-tool files remain unchanged. Creating an execution/evidence record does not run or reproduce a method; the runtime's scientific policies remain unsupported. This closes SR-T07's bounded authoring/interface work, not SR-T08's calibration/research cycle, M2, the independent reader or Gate U.
- [ ] **SR-T08: deliver the calibration and research-cycle path.** Run and package the synthetic calibration, reuse it in an independently authored consumer, reproduce its result, and check the conditional Lean error theorem. Complete section 3C–D with a failed prediction, affected-use query, explicit revision and later recheck of a blocked application. Run every negative case from section 3, including an attempt to change the old evaluation rule and irrelevant or incompatible contributions. Covers SR-04–07 and the state needed by SR-11.
- [ ] **SR-T09: implement portable package identity and RO-Crate export.** Pin dependencies and payload bytes, generate the envelope, validate with an existing RO-Crate reader/validator and report any unimplemented profile checks. Covers SR-09, SR-12, SR-13.
- [ ] **SR-T10: prove the narrow composition property.** Show that successful core application exposes witnesses for its required leaves under the declared policy. Test that this property does not turn empirical assumptions into formal proofs. The theorem is infrastructure evidence, not the main product demonstration. Covers SR-05–08.

### Gate U: usefulness before more interface work

Compare Slean with the direct-tool baseline on both paths. Record all errors, extra mapping code, author interventions, environment/setup costs, commands and elapsed execution. Count schema and adapter construction as Slean cost. Compare against both a simple baseline and one allowed to reuse its own helpers; do not handicap the alternative.

Pass requires: actual reuse in both paths, a reconstructable prediction/test/revision cycle, an explicit recheck of a blocked application after a later contribution, all enumerated invalid applications rejected or left conditional, lossless preservation of all needed fields, and removal of at least one recurring manual reconstruction/mapping step in the second consumer without introducing a different bespoke step. Record the before/after artifacts so this is inspectable. Report time/cost as measured values, not a promised percentage.

Fail if the result is only a graph, metadata conversion, manually scripted success, or more machinery with no demonstrated reuse advantage. Keep useful adapters and revise or remove the extra contract. An internal pass supports the next implementation milestone; it is not independent user validation or community adoption.

### M3: humans and agents use the same component

- [ ] **SR-T11: deliver the agent-shaped consumer.** Resume the section 3C–D investigation from exported objects in a small independent local client. Inspect requirements, construct the planned test, ingest tool output, preserve the failed assessment and export a revision, a motivated follow-up question and an unresolved alternative. Recover a blocked application and explicitly retry it when a candidate contribution appears; run the wrong-context, wrong-version and unrelated-contribution controls. Another reader must recover them without a planner-specific score. This scripted handoff tests the contract, not autonomous question generation. No private conversation state, LLM purchase or Mutome mutation is needed. Covers SR-11.
- [ ] **SR-T12: add scientific-object inspection to Explorer.** Show what the object means, what it needs, what supports or challenges it and where it was used. Follow the example's prediction/test/revision chain. Select between proofs/applications without combining their edges. Follow the repository UI protocol and verify rendered desktop/mobile, keyboard and reduced-motion paths. Covers SR-10.
- [ ] **SR-T13: document one complete reuse path.** Every code snippet comes from a compiled/executed example at the displayed version. A newcomer can install, reuse and export locally without a private service. Integrate Lean4web only after a local compatibility/security probe; online deployment remains separately authorized.

### M4: standard candidate and external use

- [ ] **SR-T14: ship the conformance kit.** A separately implemented minimal reader, with no reference-implementation imports, runs the shared suite. Include unsupported profiles, alternative proofs, revisions, contradictions and untrusted receipts. Covers SR-02, SR-06, SR-13, SR-14.
- [ ] **SR-T15: prepare open-source release.** Apply the selected Apache-2.0 licence to owned code/specification with third-party attribution and per-dataset rights. Publish the profile description, examples, governance and compatibility policy only when publication is authorized. Do not claim RO-Crate profile conformance before its required description is resolvable.
- [ ] **SR-T16: validate external adoption.** With authorized outreach, have an independent maintainer produce or consume a component in their own tool. Record changes needed. A stable 1.0 requires at least one such external use in addition to internal conformance; otherwise remain an experimental specification. Covers SR-14.

### Longer-term horizons and their evidence

These horizons state the intended destination. They do not enlarge the first implementation lot or count as delivered features. Reaching M4 establishes a usable core candidate; the broader foundation claim needs further evidence.

| Horizon | Next capability | Evidence required before claiming it |
|---|---|---|
| Domain libraries | Independent communities express and extend real scientific work using domain profiles. | A second scientific domain beyond the initial physics/calibration examples, authored with an independent domain contributor, can express its assumptions, observations and revisions without reinterpreting core fields. Slean owns profile/conformance work. |
| Persistent research across agents | Different research systems contribute to and resume the same investigation over time. | A second agent implementation continues a versioned investigation, preserves unresolved conditions and negative evidence, and produces a contribution usable by the first. Mutome integration belongs to Mutome; Slean owns the neutral contract. |
| Measured scientific progress | Cumulative knowledge improves later investigations at comparable resources. | A preregistered GERMINAL study freezes exploratory archives before revealing held-out questions, controls model/tools and total resources, and independently checks downstream results. Separate the benefit of persistent knowledge from the benefit of an evolutionary population. Measure supported results, invalid claims and downstream reuse; report null or negative findings. This is an external evaluation task, not a Slean feature checkbox. |

The initial formal example and synthetic empirical example test whether the foundation can carry scientific work. Broad scientific impact requires real research use and evidence across these horizons; it cannot be inferred from a successful package exchange.

For the later exploration study, compare a single agent with persistent memory, an evolving population with shared memory, and independent explorations without shared memory. Match total budgets and tools, repeat runs, retain failures and include generation, retrieval, archive curation, simulation and proof costs. Freeze archives before independent selection of downstream questions under a preregistered procedure. Record novelty relative to the archive separately from novelty relative to the checked literature. These comparisons test memory and exploration policies; they do not by themselves show that the Slean format is necessary. Gate U tests the contract's added value.

Within that future study, separate the effect of a structured archive and transfer from question generation/reactivation, then from additional critic agents. Evaluate these additions at matched total resources against a capable agent with tools and text memory. Reuse credit requires a controlled with/without-contribution comparison on later work; citation counts and descendants are insufficient. A critic is useful when it produces a checkable literature comparison, counterexample, experiment or other test. Audit a sample of early rejections to estimate whether cheap filters discard useful candidates. These are evaluation hypotheses for the research-system owner, not new Slean services or authorized campaigns.

[DiscoverPhysics](https://github.com/SampsonML/DiscoverPhysics) is a candidate experimental environment. Its public task asks an agent to design experiments and submit an executable law evaluated on held-out trajectories. A later Mutome study could reuse this environment, then test a frozen archive on worlds not used to create or select its contributions. Compare access to that archive with a capable text-memory baseline at matched model, tools and total resources, including archive construction and retrieval. Use a separate control with equivalent scientific content to distinguish memory benefits from any benefit of the Slean contract. Measure executable predictions, discriminating experiments and successful transfers separately from explanation grades. Agent-generated questions and observables remain additional capabilities to evaluate; success on prescribed worlds alone does not establish them.

Before that study, pin the simulator, agent, scorer and evaluation protocol. The [public repository](https://github.com/SampsonML/DiscoverPhysics#batch-benchmarking-with-yaml-configs) and [published leaderboard](https://sampsonml.github.io/DiscoverPhysicsLeaderboard/) currently describe different explanation thresholds and normalization procedures. Resolve those differences before claiming a comparable benchmark score. This is a candidate evaluation route, not a selected flagship, an executed experiment or authorization to change Mutome, request private worlds, or spend on model calls. The existing engineering fixtures remain unchanged.

## 8. Mutome boundary

Mutome can express an unresolved hypothesis, ask for relevant components and their conditions, bind a prediction and a test, run its chosen tools, submit observations, inspect the resulting assessments and contribute a revision. Slean supplies the shared scientific representation and supported checks. Mutome owns the choice of research direction and next action.

Mutome may evolve research directions through changed assumptions, new definitions, recombination, counterexamples or experiments that distinguish models. Its eventual selection policy should account for diversity and delayed usefulness; Slean does not mandate an evolutionary algorithm or encode a scientific-importance score into the core. An observed reuse is recorded with its evidence, while claims that it caused scientific progress require the separate evaluation above.

Exploration of small rewriting systems and alternative representations is a candidate future campaign. It does not change the frozen engineering fixtures or select a scientific flagship. Proposed analogies, alternative descriptions and checked equivalences must retain distinct evidence. A content identity alone establishes neither mathematical equivalence nor empirical validity. Choosing the campaign and allocating its search budget remain Mutome responsibilities.

Exploration may also propose what to measure. Observable extractors and translations between representations should use the same versioned component and evidence contract as other methods. Preserve the model or generative rule, initial conditions, extraction method and interpretation assumptions together. An assessment of a new representation must account for the translation's complexity and cost; a short rule alone is not evidence of a compact explanation. Evaluate the frozen contribution on cases not used to construct it, and keep later changes as new revisions. Slean records these tests and their scope; Mutome proposes the concepts and chooses where to investigate next. This requirement adds no universal score of scientific importance and selects no physical theory as established.

This creates a possible persistent scientific memory for Mutome: an investigation retains its hypotheses, methods, predictions, failures and remaining questions across agents and sessions. A method from investigation A remains callable and inspectable in investigation B. Mutome's retrieval, planner, worker and knowledge store can adopt the contract incrementally. No migration of all historical records is required.

Slean-owned delivery includes a standalone consumer contract and fixtures. Implementing the real Mutome adapter belongs to that repository and requires its own authorized task. GERMINAL owns held-out studies of whether reuse improves research at matched budgets. Interface integration, successful replay and scientific benefit remain separate results.

## 9. Adoption, governance and maintenance

Choose Apache-2.0 for owned source and specification, retain upstream notices, and declare dataset licences individually. Do not require a hosted account, API key, paid licence, contribution assignment or Mutome service to implement the standard. Publication authority and third-party rights inventory still apply.

Use public RFCs for semantic changes, versioned profiles, a compatibility matrix and reproducible conformance reports. Incompatible semantics require a new profile version and explicit conversion; optional unknown annotations may be preserved, but unknown required semantics must never be silently ignored. Keep historical fixtures. A release must state exactly which profiles and checker levels it implements.

Start with the current maintainer and a documented contribution/review process. Add independent maintainers when there are actual contributors; do not invent a foundation or endorsement. The standard is implementation-neutral even though Lean is the initial formal backend. A future proof assistant gets its own profile and trust policy, not a misleading generic Lean-verified label.

The first distribution path is useful tooling for existing Lean/Physlib and Python users, with a concrete example and a small integration surface. The core's appeal must survive removal of Mutome branding and the website. Evaluate adoption through independent reuse, not stars or graph node counts.

## 10. Preserve, replace and defer

| Current work | Treatment |
|---|---|
| V0 journal, exact comparator, privacy projections and regression fixtures | Retain as `legacy-dossier` behavior. Keep commands compatible until a documented migration is delivered. |
| Hard-coded proof attestation | Keep for historical examples; the new formal profile replaces it with declaration-independent checks. |
| Autoresearch-specific source checks | Keep optional and separate. They are not requirements of a scientific component. |
| Current Explorer | Reuse its inspection/accessibility foundations where suitable; replace the dossier-centered entry point only after Gate U. |
| Verso documentation | Keep existing V0 instructions accurate. Add the new contract/example with its own status; do not present planned capabilities as delivered. |
| 3D, a global corpus, historical influence mapping, semantic search, instrument scheduling | Deferred extensions. They do not establish the first reuse contract. |
| New compiler, universal scientific truth score, new proof kernel, automatic paper-to-fact ingestion | Excluded from this product direction. |

## 11. Effort, review and unresolved empirical questions

Execute M0–M2 as the first bounded engineering lot, with the explicit Gate U before adding M3 features. Use existing local tools/subscriptions, with no incremental API/GPU purchase or new service. Record account allowance and actual build/storage/agent effort per milestone. No calendar or cost forecast is credible before M0. Romain's only required involvement in this lot is review of the concrete result or a material change in direction; routine choices belong to the implementing agent.

The design decisions above are selected for the first lot. The remaining questions are empirical: whether the selected upstream versions work together, whether the contract preserves a complete investigation while removing repeated effort, whether authors can express conditions without excessive annotation, and whether an independent tool wants to adopt it. Each has a named task or Gate U. A negative answer changes the implementation or the scope, not the recorded success criterion.

Engineering acceptance requires current, requirement-specific evidence for SR-01 through SR-14, with internal interoperability distinguished from external validation. M4 additionally records publication and external-use outcomes when those actions are authorized. A successful V0 build or a polished viewer cannot close this PRD; an unavailable external participant cannot be counted as adoption.

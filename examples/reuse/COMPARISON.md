# Frozen direct-tool comparison

Status on 28 September 2026: SR-T02 baseline and comparison design. This is a
comparison of scientific reuse interfaces. The separate study of autonomous
exploration remains future work. No Gate U result is claimed here.

## Fixed work and evidence

[`frozen-baseline.json`](frozen-baseline.json) pins the source, inputs, locks and
negative-case definitions. The inputs are the same for the direct-tool and
future Slean paths. Scientific conditions and expected outcomes cannot be
weakened to favor either path. A changed fixture requires a new freeze and
reruns of both sides; preserve the old run's identity and results.

| Task | Input and required operation | Recorded baseline evidence |
|---|---|---|
| Formal reuse | Apply the pinned Physlib energy theorem with its native hypotheses; inspect the actual dependency and axioms. | `direct-lean/check.sh`, native interface report and LeanArchitect probe. |
| Computational reuse | Fit the supplied CSV, bind the separate sensor reading and apply the published method. | Python producer/consumer, `4 mm`, `0.01 mm` conditional bound and explicit physical assumptions. |
| Conditional mathematics | Check the affine inverse and residual theorem; require nonzero gain and the residual assumption. | `direct-lean/check_calibration.py` and `observed-calibration.json`. The link to physical parameters is still conditional. |
| Research continuity | Freeze a prediction rule, preserve a failed prediction, select affected applications, revise and test against a second observation. | `research.py`, exported protocols/observations/assessments and an unresolved alternative. |
| Later reuse | Keep a blocked measurement fixed and retry after a new model and assessment arrive, reusing the executable method. | The two attempts have the same input and method digests, different model references and visible remaining assumptions. |
| Portable inspection | Recover all the above from exported files outside the producer's process. | RO-Crate library reader plus an explicitly invoked exported Python consumer. Formal source/reports are preserved; a reader must repeat the native formal checks to trust them. |

The JSON freeze lists each positive and negative case and its checking entry
point. The Python check verifies the freeze before running. Formal checks must
also be run; a matching source digest alone is not evidence of a valid proof.
The completed M0 probes are observations, not trusted receipts for future runs.

## Current upstream fit

This classification applies to the versions tested in this branch. A
shared-contract candidate is a hypothesis about repeated integration work,
not a claim that other tools cannot express the information.

| Proposed behavior | Existing capability or gap | Decision |
|---|---|---|
| Real physics definitions and proofs | Physlib already supplies them. | Reuse; contribute physics-specific additions upstream. |
| Native types, hypotheses, application and proof checking | Lean already supplies them. | Reuse ordinary Lean/Lake. |
| Blueprint annotations, source locations and selected dependency navigation | LeanArchitect supplies annotations and inference; native Lean supplies the actual type/value dependency sets and axioms. | Reuse the tested combination; small adapter. |
| Proof plan revision and search | Goedel-Architect is existing orchestration work. | Keep search outside Slean. |
| Quantities, dimensions and Celsius conversion | Pint supplies them. | Reuse; pin the unit definitions. |
| Fitting, prediction, residual comparison and research methods | Ordinary Python handles this fixture. | Keep the executable method separate from packaging. |
| Source/data packaging, file provenance and action links | RO-Crate supplies the envelope and general terms. | Reuse; the baseline needs an explicit 1.3 writer and payload adapter. |
| Consistent method/result bindings, requirements, uncertainty interpretation and evidence scope across tools | Each tool can store these; the baseline manually connects their meanings. | Candidate for the smallest shared scientific profile. |
| Model revisions, affected uses and blocked attempts | The baseline represents them in plain JSON/Python; LeanArchitect's proof-plan status has a different scope. | Candidate for an optional research profile; keep scheduling in Mutome. |
| Formal checks under an explicit trust policy | Native axioms help; display readiness is insufficient. | Adapter plus declared policy; isolated unreviewed-code verification remains future Slean work. |
| Alternative methods/proofs and all/any requirements | Lean can express logic; the present numerical example uses manual conditions. | Freeze a small common interpretation in SR-T03; not delivered by this fixture. |
| Offline inspection, exact identities and explicit public export | Local tools already work offline after setup; a common identity and projection rule is additional work. | Shared-contract candidate; count its full construction cost. |
| Explorer, CLI parity and an independent Slean reader | Existing viewers/readers cover parts; no new Slean contract exists yet. | Slean work only after its earlier gates. |
| Broad theory, simulation and experimental-data integration | Part of Physlib's stated direction; the selected runtime probe is narrower. | Treat upstream plans as plans. Reassess before adding parallel infrastructure. |

For detailed observed LeanArchitect behavior and why Atlas was not ported, see
the [formal integration decision](../../docs/research/slean-formal-integration-2026-09-28.md).
The [source comparison](../../docs/research/slean-standard-landscape-2026-09-27.md)
records the upstream scope and sources.

## Mapping work and author decisions

The direct baseline is allowed to reuse its own helpers in a second consumer.
Do not delete or deliberately restrict these helpers in the later comparison.

| Owned code | Work it performs | Judgment still supplied by the author |
|---|---|---|
| `method.py`, `producer.py` | Fit input columns, represent quantities and fingerprint the model/method. | Sensor identity, affine model, operating range, residual assumption and unresolved parameter uncertainty. |
| `consumer.py` | Map model fields to input checks, reproduce the output, report remaining conditions. | Which version and intended use apply; whether empirical support is appropriate. |
| `research.py` | Bind rules to observations, keep revisions/attempts, find exact version uses. | Scope, evaluation threshold, proposed revision, follow-up question and alternative explanation. |
| `package_baseline.py` | Map files and actions into the envelope. | Which sources, data and reports belong in the export. |
| `read_crate.mjs` | Read the standard envelope, hash files and interpret this fixture's JSON fields. | The scientific payload interpretation is explicit code, not supplied by RO-Crate itself. |
| Lean sources and check scripts | Apply upstream proofs; extract native dependencies/axioms; check failure causes. | Select declarations, express the intended statement, select the trust policy and judge its physical applicability. |

The freeze records authored line counts as an inventory, not as a quality or
productivity score. Schema/adapter authorship, documentation, tests and repairs
are costs on both sides. No credible retrospective authoring-time measurement
is available; record it as unknown rather than inferring hours from file size.

## Gate U procedure

1. Use the frozen inputs and all their negative cases on both implementations.
   Allow each side the same installed upstream tools and reusable helpers.
2. Have the second consumer perform the same operations and preserve the same
   quantities, assumptions, versions, protocols, failed attempts and open items.
   Record exact code edits and manual reconstruction for each side.
3. Record cold dependency/setup costs separately from warm checks. Record model
   calls, execution, retrieval, curation and proof work if used. An unmeasured
   cost remains unknown; a no-API fixture does not imply zero engineering cost.
4. Compare the exported before/after artifacts. Slean must remove at least one
   recurring mapping or reconstruction step without replacing it with a bespoke
   step elsewhere. Count its schema, adapter, configuration and annotation work.
5. Run every invalid case. Reject it or retain its explicit unresolved or
   unsupported condition. Dropping information or accepting an invalid case
   fails the comparison, even if the path is faster.

Use repeated runs with matched cache conditions if reporting a runtime
difference. The saved single-run duration is reproduction evidence only. An
internal pass would justify the next interface milestone, not a scientific
discovery, external adoption, a standard or autonomous exploration.

The direct formal warm check previously took 49.48 seconds. Its README records
setup failures separately. The initial calibration proof build took about 258
seconds with an unnecessary broad import; the final source uses smaller imports
and passed its own full check. The final Python report measures its own warm
checks, export, standalone consumer reproduction and reader invocation. Full
setup time and total authoring time remain unmeasured. Do not sum partial
measurements into an invented total or promise a savings percentage.

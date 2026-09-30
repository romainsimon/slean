# Finite prediction checks and research continuity

`slean.research.Research` supplies explicit receiver-owned operations for the
optional research profile. Imported outcomes remain declared. These operations
do not execute comparison code from an imported package, run a planner, prove
physical applicability or establish a discovery's novelty/usefulness.

## Compare a frozen prediction

The initial policy is `absolute-difference/0.1-draft.1`. `assess(execution,
observation, expected_plan=..., policy=...)` requires a receiver-selected exact
plan reference. The executed application must retain that plan's model, inputs,
context and requirements. The plan names the expected scalar, observable,
absolute bound and observation ID. Its execution records the predicted output;
the separate observation artifact supplies the observed value.

The operation checks producer conditions, observation context, units, missing
values and the selected output, then computes an absolute nominal difference.
A difference within the bound gives `within_bound`; one outside gives
`failed_prediction`. An incompatible test or observation context gives
`not_applicable`, without an error/refutation claim. Missing scope or observation
values remain unresolved. Unsupported semantics prevent a supported comparison.
Physical applicability can remain open while the hypothesis is being tested.
The report preserves those conditions instead of treating the test as a proof.

The observation is a `data` component with research role `observation` and one
source artifact. Under this policy that artifact is a JSON object containing
exactly `id`, `context` and the predicted observable's key. `context` uses core
bindings; the observable uses the quantity profile's scalar encoding. The ID
must match both the component and frozen plan. The artifact is bounded to 1 MiB.
Other observation encodings require a separately documented policy.

`verify_evidence` requires both `expected_evidence` and `expected_plan`, checks
the exact subject/model/observation/context/policy bindings, then recomputes the
comparison. A fabricated outcome or error is `different`; another evaluation
plan is rejected. A new plan cannot replace an old failed assessment. Saved
comparison-source artifacts remain provenance and are never imported as code.

These checks compare declared predictions to actual selected observation bytes.
They report `prediction_reproduction: not_performed`. Use the separate reviewed
`Executor.reproduce` operation to check the computation of a prediction. The
example does both; neither verifies that the synthetic observation is a real
measurement or that the model universally describes a physical system.

## Query uses that may need reassessment

`affected_uses` first freshly checks the selected failed assessment. It inspects
applications of the exact challenged model and applications that require that
model as an active applicability claim. It follows the interface reader's fresh
`any` selections; an unselected alternative does not create a dependency. When
no branch is established, potential branches stay visible. Contextually
incompatible uses are listed separately. Other revisions are not equated by name.

The query covers only the explicitly loaded corpus. It reports that corpus,
contexts and candidate applications. Uninspectable entries produce `skipped`
diagnostics and `query_status: partial`, rather than an apparent complete empty
result. Candidates need reassessment; they are not automatically retracted, and
the conditional Lean theorem is not made false by an observation.

## Recheck a blocked use

`check_retry(attempt, expected_previous=..., policy=INTERFACE_POLICY)` requires
an explicit previous attempt, the same question/requested-use identity and
unchanged exact input/context bindings. It resolves contributed references and
checks the currently selected component's actual declared conditions afresh.
A new citation never supplies an applicability witness.

The report retains the previous component/check, selected component/check,
remaining obligations and IDs of recorded obstacles whose corresponding fresh
checks now pass. This can mean using a new component version with a revised
declared scope. It does not retrospectively satisfy the original component's
old requirement or change the old attempt. `contributions_verified` remains
false: scientific claims need their separate named verification operation.
The example reuses a freshly reproduced result and the unchanged inverse-method
source; the revised context check passes and three physical obligations remain.

## Recorded checkpoint

The [research SDK report](observed-research.json) includes 12 scientific-control
groups in addition to the earlier 32 SDK groups, plus installed-wheel checks.
The [cycle report](../../examples/reuse/with-slean-python/observed-cycle.json)
records a failed prediction, calculated offset revision, separate second test,
scoped use query, result/method reuse and retry with unchanged measurement.
It preserves the failed assessment, open follow-up and unresolved alternative.

SR-T08 remains open for its conditional Lean bridge and remaining complete
negative-case acceptance. The usefulness comparison, independent implementation
and external adoption remain later tasks. These reports do not close Gate U.

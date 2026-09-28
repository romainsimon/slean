# Research profile: slean-research/0.1-draft.1

This optional profile preserves investigations across tools and agents. It is
not a scheduler or selection policy. It uses annotations on existing module,
component, application and evidence records; formal-only modules need none of it.
The key is the exact profile identifier. Its shape is defined in
[`research.schema.json`](research.schema.json).

Module annotations contain `questions`: each has a module-local ID, attributed
wording/source, an optional motivating record and a list of target references.
Targets may be empty. This permits an open question before a target theorem
exists. Question IDs share the module's ID namespace. Optional `alternatives`
retain attributed explanations with `unresolved` status.

A hypothesis is a claim or model component annotated with `role: "hypothesis"`.
Its universal applicability remains an explicit requirement. A revision is a
new component with `supersedes` and an annotation naming its motivation. It does
not overwrite the original component or retrospectively repair a failed test.

An application annotated as `test-plan` contains a prediction: the observable,
expected scalar, comparison method (`absolute_difference`), bound and exact
observation ID expected next. These are fixed in a planned application's module
identity. Executing that plan creates another application which references it.
The observation is a data component. The check binds the observation and plan
to empirical evidence with `failed_prediction`, `within_bound`, `not_applicable`
or `unresolved`. A changed rule is a new plan; it cannot replace the old plan
named by an assessment. A successful finite comparison does not prove a model.

An attempted reuse is an application annotated with `question`, `attempt_of`,
`previous_attempt`, `contributions` and `obstacles` as applicable. `attempt_of`
names the stable requested use, with explicit inputs and context preserved in
the application. Repeating that same use preserves those inputs. A changed
question or measurement must be represented explicitly as a different use.
Obstacles contain a requirement node ID and one of `unresolved`, `violated` or
`unsupported`, with a reason. They are stored outcomes, not fresh checks.

A later contribution may identify a candidate model, result or method. An
explicit retry creates another application and new evidence. A new reference,
an unrelated result or a prover diagnosis cannot satisfy an old requirement.
Only the receiving checker can establish that the relevant condition now holds.
Preserve the earlier attempt and any conditions still open.

The initial empirical result binds `plan`, `observation`, `model` and `outcome`.
`absolute_error` is present only for an in-scope numerical comparison. Inspectors
must not merge a formal deduction's validity with this contextual assessment.
Potentially affected uses are applications of the exact challenged model or
assumption in the selected corpus; list them for reassessment, not automatic
retraction. Links alone do not establish that a new result caused progress.

There is no global `interesting`, `true`, Elo or fitness field. Clients may
preserve their own optional annotations. A question can remain dormant without
computation. The controlled fixture records order, not real-world preregistration.
Autonomous exploration and downstream scientific value need separate studies.

import VersoManual
import Slean

open Verso.Genre Manual
open Verso.Genre.Manual.InlineLean

#doc (Manual) "Slean" =>
%%%
shortTitle := "Slean"
%%%

Does a research decision agree with the rules and measurements recorded before it? Slean helps answer that question for a case whose event history you can replay.

In this manual, a *case* is a JSON file containing a question, a frozen protocol, an event journal, observations, and a decision. Slean checks their references and order, one exact decimal comparison, and a stated cost cap. It does not run the experiment or prove that a measurement is true.

The walkthrough uses `examples/valid.json`, a wholly invented case. You will see a rule requiring a measurement greater than `0.001`, an observation of `0.002`, and a recorded `promote` decision. You can then make the same check fail by changing the observation's unit.

Development preview · schema SLEANSCHEMAVERSIONTOKEN · Lean 4.28.0. No tag is selected for this build.

From the root of a local Slean checkout, with Lean installed, start with:

```
lake build
lake exe slean validate examples/valid.json
```

The second command prints exactly:

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

`ok: true` means the case passes the checks Slean supports. To understand _why_ the decision passes and what those checks leave open, continue with [the checked case](Start-with-a-checked-case/) and then [the decision](Read-the-decision/).

# Start with a checked case

*Prepare a local checkout*

You need an authorized checkout of this repository and `elan`, which provides Lean and Lake. Follow the [official Lean installation instructions](https://lean-lang.org/install/manual/) if you do not have those tools. The repository's `lean-toolchain` selects Lean 4.28.0. This preview is not yet an anonymous public installation.

Open a terminal at the repository root, where `lakefile.lean` and `examples/valid.json` live, then run:

```
lake build
lake exe slean validate examples/valid.json
```

Expected `validate` output:

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

`events: 10` counts entries in the complete journal, including two restricted to the owner. It does not mean ten experiments or ten confirmed results.

*Read the result, not just “ok”*

Show the agent-safe view:

```
lake exe slean view examples/valid.json agent
```

In the returned JSON, find `observations[0]` (`status: "measured"`, `value: "0.002"`, `unit: "ratio"`) and `decisions[0]` (`result: "promote"`). The value remains a decimal string to avoid implicit rounding. `event-1` freezes the rule; the observation is `event-4`, the assessment is `event-6`, and the decision is `event-7`.

You have answered one precise question: *does the recorded promotion follow an earlier observation that matches the frozen protocol?* For this synthetic case, yes. The next chapter explains the links and comparison Slean checks. A successful `validate` does not certify the sensor, artifact file, or truth of the claim.

*See a concrete rejection*

Run a copy of the case whose observation unit has changed:

```
lake exe slean validate examples/unit-mismatch.json
```

The command exits nonzero and prints:

```
{"error":{"code":"metric_unit","event_id":"event-4","message":"observation metric or unit differs from frozen protocol","object_id":"observation-1"},"ok":false}
```

`event_id` locates the failure in the journal; `metric_unit` means the observation's metric or unit no longer matches the protocol. Continue to [read the decision](Read-the-decision/) and distinguish an invalid case from one whose result is simply unknown.

# Read the decision

The valid case records a short chain, in this order:

1. `event-1` freezes the protocol: metric `synthetic_delta`, unit `ratio`, threshold `0.001`, strict comparison, and cost cap `10.00 cpu_s`.
2. `event-4` records `0.002 ratio` for the same metric and run.
3. `event-5` records `2.50 cpu_s`, below the stated cap.
4. `event-6` cites the observation and records `pass` under the local `exact_v0` rule.
5. `event-7` cites that assessment and records the `promote` decision.

The threshold is strict because the protocol combines `direction: "gte"` with `inclusive: false`: `0.002 > 0.001`. Slean also checks that references exist and that the assessment and decision do not precede their evidence. `pass` is the assessment's verdict; `promote` is a separate decision. A human `override` needs a reason and does not become a `pass`.

You can freeze the reading at the decision itself:

```
lake exe slean replay examples/valid.json 7
```

This replay uses only the first seven events. `event-8` through `event-10` therefore cannot retroactively change that prefix result. The previous chapter's `agent` view then projects what that audience may see.

A case can be *valid but undetermined*. Compare the view of the case without a measurement:

```
lake exe slean view examples/unknown.json agent
```

Its observation has `status: "unknown"` and `value: null`; the decision is `defer`. `null` means “no measurement available,” not zero. The `technical-error.json` case also retains a null value and a deferred decision, with a distinct technical-error status.

# Follow provenance

The view lets you follow the decision to its assessment, the assessment to `observation-1`, and the observation to `run-1` and `artifact-1`. These IDs are checked references in the case; the decision's prose alone is insufficient. `event-8` adds a support relation from the observation to `claim-1`, after the decision prefix.

Visibility is applied *before* computing the view. On the synthetic case, compare:

```
lake exe slean view examples/valid.json agent
lake exe slean view examples/valid.json owner
```

The `agent` view includes `observation-1` with `0.002`, but not `private-observation-1`. The `owner` view also includes that second observation and its invented value `0.009`. Treat `owner` output from a real case as private; do not send it to an agent or a public site. Review text visible in the `agent` export before sharing that too.

Schema 0.2 can keep owner-only source records. The bounded adapter checks source event order, the initial freeze, prediction-to-observation links, completion agreement with the manifest, and coverage of every source observation. It reads the trace in memory and does not save the private case. Python computes SHA-256 digests of source artifacts; Lean checks links to the supplied digests, not the hash computation or the external evaluator's behavior.

# Format and API

*Choose a command for the question*

- `validate <case.json>`: does the case pass the supported rules? Output has `ok: true` or an error with `code`, `event_id`, and `object_id`; errors exit nonzero.
- `replay <case.json> <N>`: what was the state after the first `N` events?
- `view <case.json> agent|owner`: which observations, decisions, and relations are visible to that audience?
- `export <case.json> agent|owner`: produce canonical case JSON for that audience. Review it before sharing.
- `timeline <case.json> agent|owner`: get checked states at every visible prefix for the local Explorer.
- `proof <case.json>` and `proof-statement`: inspect local formal statuses and the project's one pinned theorem statement.

Commands that read a case also accept `-` for standard input. For example, from the repository root:

```
lake exe slean view examples/valid.json agent
```

`examples/valid.json` uses schema `0.1.0`. Schema `0.2.0` adds owner-only source records. In each case, `schema_version` and `semantics_version` must be a supported pair; Slean does not migrate cases implicitly. See `schema/v0.1.0.schema.json` and `schema/v0.2.0.schema.json` in the repository for exact fields. Exact decimals such as `"0.002"` are strings; `null` remains distinct from `"0"`.

*If you write Lean*

The typed API can build the same kind of case. These declarations are checked as this manual compiles:

```lean
#check Slean.CaseFile
#check Slean.replay
#check Slean.assessExact
#check Slean.project
```

`examples/Synthetic.lean` contains the complete typed case. `bash tests/check.sh` compiles it and compares its `agent` export byte for byte with the JSON fixture. Imported JSON proof-status text never grants `kernel_checked`; that status is reserved for the pinned local declaration checked by the Lean kernel.

# Limits and development status

*Slean checks here:* the versioned case shape, IDs and references, causal journal order, local exact decimal comparison, stated cost cap, promotion rule, and audience projection. It can report a precise error or preserve an undetermined result.

*Slean does not check here:* that the measurement happened, that artifact bytes are authentic, that an external clock or evaluator is reliable, that a human decision is wise, or that the scientific claim is true. The local Lean theorem concerns a conditional property of the mechanism, not those empirical facts. No independent proof checker is configured.

This site is a local pre-publication prototype. Its examples are synthetic. Public licensing, repository visibility, domain deployment, and integrations remain separate decisions. The build runs tests and compiles examples before generating the manual. `build-info.json` identifies the source commit, tree cleanliness, schema, Lean, and selected tag; a build without a tag remains a development preview.

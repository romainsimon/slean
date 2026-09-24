import VersoManual
import Slean

open Verso.Genre Manual
open Verso.Genre.Manual.InlineLean

#doc (Manual) "Slean" =>
%%%
shortTitle := "Slean"
%%%

Does a research decision follow the rules and measurements recorded before it? Slean helps someone preparing or reviewing a case check that consistency and trace each part of the decision.

Here, a *case* is a JSON file with the question, frozen protocol, observations, a decision, and an event journal. This manual's example is entirely invented; you can understand it without installing Lean.

*Read the result in one minute*

- *Rule fixed before measurement:* promote only if `synthetic_delta` is strictly greater than `0.001 ratio`, with cost no higher than `10.00 cpu_s`.
- *What was recorded:* an observation of `0.002 ratio` and a cost of `2.50 cpu_s`.
- *What Slean checks:* the observation has the right metric and unit, follows the rule, and precedes the assessment; `0.002 > 0.001` and cost stays below the cap.
- *What the case declares:* assessment `pass`, then decision `promote`. Slean checks that this chain is consistent. It does not make the author's decision.

If the observation's unit changes, Slean reports `metric_unit` at `event-4`. If the measurement is missing, its value is `null` and the decision is `defer`: missing data is not zero. [The checked case](Start-with-a-checked-case/) shows the two useful commands; [read the decision](Read-the-decision/) explains the chain and its limits; [AND and OR gates](and-or-gates/) add the recorded links in schema 0.3. [Complete Lean examples](lean-examples/) show the typed API behind these jobs.

Slean checks case shape, references, order, and local rules. It does not run the experiment, authenticate the sensor, or prove that a measurement is true.

Development preview · schema SLEANSCHEMAVERSIONTOKEN · Lean 4.28.0. No tag is selected for this build.

*Try it in a local checkout*

If you have repository access and Lean installed, run from its root:

```
lake build
lake exe slean validate examples/valid.json
```

The second command prints exactly:

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

`ok: true` means the case passes the checks Slean supports. It does not certify the source data or the truth of the conclusion.

# Start with a checked case

*Prepare a local checkout*

You need an authorized checkout of this repository and `elan`, which provides Lean and Lake. Follow the [official Lean installation instructions](https://lean-lang.org/install/manual/) if you do not have those tools. The repository's `lean-toolchain` selects Lean 4.28.0. This preview is not yet an anonymous public installation.

Open a terminal at the repository root, where `lakefile.toml` and `examples/valid.json` live, then run:

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

The `10.00 cpu_s` cap applies to this frozen protocol across all its runs. Each recorded `cpu_s` amount counts, including one with partial coverage. A second run that adds `7.51 cpu_s` after the first run's `2.50 cpu_s` is rejected as `cost_cap_exceeded`; another cost unit is recorded without conversion.

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

Next, [read the AND and OR gates](and-or-gates/) to see how recorded dependencies extend the journal without recalculating that decision.

# Read AND and OR gates
%%%
file := "and-or-gates"
tag := "and-or-gates"
%%%

A *dependency gate* describes links added by the author between records already in the case:

- `all_of` (AND): every member is presented as a prerequisite of the target.
- `any_of` (OR): the members are presented as alternative supports.

Slean checks the shape, IDs, prior existence, and visibility of these links. The gate does not calculate whether the members are true, sufficient, or scientifically persuasive.

From the repository root, validate the synthetic schema `0.3.0` case:

```
lake build
lake exe slean validate examples/dependency-gates.json
```

The second command prints exactly:

```
{"case_id":"synthetic-decision-1","events":13,"ok":true}
```

Here `ok: true` confirms that both gates are admissible records with references available at the right time; it does not evaluate AND or OR. In this case, `event-12` adds `gate-all-1`: `protocol-1` AND `assessment-1` are recorded prerequisites for `decision-1`. `event-13` adds `gate-any-1`: `observation-1` OR `observation-2` are recorded alternative supports for `claim-1`. Both events follow the decision at `event-7`; they do not retroactively change its assessment.

*See when each gate appears*

```
for n in 11 12 13; do
  lake exe slean replay examples/dependency-gates.json "$n" |
    python3 -c 'import json,sys; print(len(json.load(sys.stdin)["dependency_gates"]))'
done
```

The exact output is `0`, then `1`, then `2` on separate lines. A *prefix* is the number of events from the beginning of the journal included in a replay. Prefix 11 ends before the gates; 12 includes AND; 13 includes both AND and OR. `lake exe slean view examples/dependency-gates.json agent` exposes their operators, members, and targets under `dependency_gates`.

To inspect those same prefixes in the local Explorer:

```
python3 explorer/render.py examples/dependency-gates.json --output explorer/_out/gates
python3 -m http.server 8768 --directory explorer/_out/gates
```

Open `http://127.0.0.1:8768/`, then select events 11, 12, and 13. The keyboard-readable list, exact selected event, and 2D map come from the same validated journal. The map repeats recorded links; it does not prove their truth.

*Keep unknown distinct from zero*

Compare the two `agent` views:

```
lake exe slean view examples/dependency-gates-unknown.json agent
lake exe slean view examples/dependency-gates-zero.json agent
```

In the first case, the first observation has `status: "unknown"`, `value: null`, and the earlier decision is `defer`; its assessment is `undetermined`. In the second, it has `status: "measured"`, `value: "0"`, and the decision is `reject`; its assessment is `fail`. Both cases have the same AND/OR gates and a later positive second observation. The OR gate therefore turns neither missing data into zero nor the earlier decision into `promote`.

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
- `export <case.json> agent|owner`: produce a versioned envelope with the canonical case and Lean version. Review it before sharing. Use `export-case` only when a consumer needs the legacy raw case.
- `timeline <case.json> agent|owner`: get checked states at every visible prefix for the local Explorer.
- `proof <case.json>` and `proof-statement`: inspect declared claims, local attestation eligibility, direct project dependencies and the project's one pinned theorem statement. For a clean committed build, `python3 tools/attest_proof.py examples/formal-claim.json` issues `kernel_checked` only with exact build and audience-filtered export digests. This uses trusted Lake, CLI and Python code; it is not an independent recheck.

Commands that read a case also accept `-` for standard input. For example, from the repository root:

```
lake exe slean view examples/valid.json agent
```

`examples/valid.json` uses schema `0.1.0`. Schema `0.2.0` adds owner-only source records; `0.3.0` adds `dependency_gate_recorded` with `all_of` or `any_of`. In each case, `schema_version` and `semantics_version` must be a supported pair; Slean does not migrate cases implicitly. See `schema/v0.1.0.schema.json`, `schema/v0.2.0.schema.json`, and `schema/v0.3.0.schema.json` in the repository for exact fields. Exact decimals such as `"0.002"` are strings; `null` remains distinct from `"0"`.

*If you write Lean*

The typed API can build the same kind of case. These declarations are checked as this manual compiles:

```lean
#check Slean.CaseFile
#check Slean.replay
#check Slean.assessExact
#check Slean.project
#check Slean.DependencyGate
```

`examples/Synthetic.lean` contains the complete typed case. `bash tests/check.sh` compiles it and compares its bytes with the JSON fixture's `export-case agent` projection. Imported JSON proof-status text never grants `kernel_checked`; the CLI keeps even a matching local declaration at `declared` until the clean-build attester binds its receipt to exact artifacts.

# Complete Lean examples
%%%
file := "lean-examples"
tag := "lean-examples"
%%%

These are four complete Lean 4 files that call Slean's current typed API. Slean has no separate source-language parser: the CLI reads JSON cases or versioned export envelopes, while `lake env lean --run` runs these Lean files. Work from the repository root with the pinned Lean 4.28.0 toolchain, and run `lake build` once first. Every input and value here is synthetic.

*1. Record and replay a decision dossier*

Problem: record one frozen rule, run, artifact reference, measurement, cost, assessment, and decision, then inspect what existed when the decision was made. The typed source below produces the agent projection of the checked `examples/valid.json` fixture.

*Complete source: `examples/Synthetic.lean`*

```
import Slean

open Lean Slean

private def ident (id : String) : Identity :=
  { id, version := 1, domain := "synthetic-computation",
    provenance := "synthetic://slean-v0", audience := "agent" }

private def protocol : FrozenProtocol :=
  { identity := ident "protocol-1", claim_ref := "claim-1",
    metric_id := "synthetic_delta", unit := "ratio", direction := "gte",
    threshold := "0.001", inclusive := false, data_scope := "synthetic input A",
    evaluator_ref := "synthetic-evaluator-v1", cost_cap := "10.00",
    cost_unit := "cpu_s", stop_rule := "one synthetic measurement",
    frozen_at := "2026-01-01T00:01:00Z" }

private def run : Run :=
  { identity := ident "run-1", protocol_ref := "protocol-1",
    input_ref := "synthetic-input-A", seed := "7" }

private def artifact : ArtifactRef :=
  { identity := ident "artifact-1", digest := "sha256:" ++ String.ofList (List.replicate 64 'a'),
    media_type := "application/json" }

private def observation : Observation :=
  { identity := ident "observation-1", run_ref := "run-1",
    metric_id := "synthetic_delta", unit := "ratio", value := some "0.002",
    status := "measured", artifact_ref := "artifact-1",
    observed_at := "2026-01-01T00:04:00Z" }

private def cost : CostEntry :=
  { identity := ident "cost-1", run_ref := "run-1", category := "machine_time",
    amount := "2.50", unit := "cpu_s", source := "synthetic-meter", coverage := "complete" }

private def assessment : Assessment :=
  { identity := ident "assessment-1", protocol_ref := "protocol-1",
    observation_refs := #["observation-1"], verdict := "pass", rule_used := "exact_v0" }

private def decision : PromotionDecision :=
  { identity := ident "decision-1", assessment_ref := "assessment-1",
    result := "promote", reason := "Synthetic threshold passed." }

private def relation : Relation :=
  { identity := ident "relation-1", source_ref := "observation-1",
    target_ref := "claim-1", kind := "support" }

private def ev (sequence : Nat) (kind time : String) (payload : Json) : Event :=
  { event_id := s!"event-{sequence}", version := 1,
    domain := "synthetic-computation", provenance := "synthetic://slean-v0", sequence, kind,
    actor := "synthetic-author", recorded_at := s!"2026-01-01T00:{time}:00Z",
    audience := "agent", payload }

def syntheticCase : CaseFile :=
  { schema_version := "0.1.0", semantics_version := "0.1.0",
    case_id := "synthetic-decision-1", version := 1,
    domain := "synthetic-computation", provenance := "synthetic://slean-v0",
    audience := "agent",
    question := { identity := ident "question-1", text := "Does a synthetic candidate exceed a fixed threshold?" },
    claim := { identity := ident "claim-1", text := "The synthetic metric exceeds 0.001 on the stated input." },
    events := #[
      ev 1 "protocol_frozen" "01" (toJson protocol),
      ev 2 "run_started" "02" (toJson run),
      ev 3 "artifact_registered" "03" (toJson artifact),
      ev 4 "observation_recorded" "04" (toJson observation),
      ev 5 "cost_recorded" "05" (toJson cost),
      ev 6 "assessment_recorded" "06" (toJson assessment),
      ev 7 "decision_recorded" "07" (toJson decision),
      ev 8 "relation_recorded" "08" (toJson relation)] }

#guard (replay syntheticCase).isOk
#guard (compareDecimal (parseDecimal "0.010" |>.toOption.get!)
  (parseDecimal "0.01" |>.toOption.get!)) == .eq
#guard (assessExact protocol observation).toOption == some "pass"

def main : IO Unit := IO.println (toJson (project syntheticCase "agent")).compress
```

Run and summarize the large JSON output:

```
lake env lean --run examples/Synthetic.lean |
  python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["case_id"], len(d["events"]))'
lake exe slean replay examples/valid.json 7 |
  python3 -c 'import json,sys; s=json.load(sys.stdin); print(len(s["event_ids"]), s["assessments"][0]["verdict"], s["decisions"][0]["result"])'
```

Expected lines: `synthetic-decision-1 8` and `7 pass promote`. The typed program emits eight agent-visible events; the JSON fixture has ten total events, including two owner-only entries. Prefix seven contains the assessment and decision. `tests/check.sh` compares the typed output with the fixture's agent projection byte for byte. This checks the recorded chain, not whether the synthetic measurement happened or whether the artifact digest matches real bytes.

*2. Compare exact values at a strict boundary*

Problem: decide whether decimal strings equal to and just above a frozen threshold pass a strict rule, without floating-point rounding.

*Complete source: `examples/ExactThreshold.lean`*

```
import Slean

open Slean

private def identity (id : String) : Identity :=
  { id, version := 1, domain := "synthetic-computation",
    provenance := "synthetic://worked-examples", audience := "agent" }

private def protocol : FrozenProtocol :=
  { identity := identity "protocol-exact", claim_ref := "claim-exact",
    metric_id := "synthetic_delta", unit := "ratio", direction := "gte",
    threshold := "0.010", inclusive := false, data_scope := "synthetic input",
    evaluator_ref := "synthetic-evaluator", cost_cap := "1.00",
    cost_unit := "cpu_s", stop_rule := "one synthetic reading",
    frozen_at := "2026-01-01T00:00:00Z" }

private def reading (id value : String) : Observation :=
  { identity := identity id, run_ref := "run-exact", metric_id := "synthetic_delta",
    unit := "ratio", value := some value, status := "measured",
    artifact_ref := "artifact-exact", observed_at := "2026-01-01T00:01:00Z" }

def main : IO Unit := do
  match assessExact protocol (reading "equal" "0.0100"),
        assessExact protocol (reading "above" "0.0101") with
  | .ok equal, .ok above =>
    IO.println s!"equal={equal}; above={above}"
  | .error message, _ => throw (IO.userError message)
  | _, .error message => throw (IO.userError message)
```

Run `lake env lean --run examples/ExactThreshold.lean`. Expected output: `equal=fail; above=pass`. `0.0100` equals `0.010` exactly, while `0.0101` is greater. `assessExact` compares one supplied observation with one protocol; this small program does not validate a journal, an artifact, or the observation's provenance. Use a `CaseFile` and `replay`, as in example 1, for the recorded evidence chain.

*3. Validate, project, and prepare an export*

Problem: validate the whole synthetic JSON dossier before preparing an agent-safe versioned export. The program reads the checked-in fixture from the repository root.

*Complete source: `examples/ValidateExport.lean`*

```
import Slean

open Lean Slean

def main : IO Unit := do
  let raw ← IO.FS.readFile "examples/valid.json"
  let json ← match Json.parse raw with
    | .ok value => pure value
    | .error message => throw (IO.userError message)
  let dossier ← match (fromJson? json : Except String CaseFile) with
    | .ok value => pure value
    | .error message => throw (IO.userError message)
  let fullState ← match replay dossier with
    | .ok state => pure state
    | .error diagnostic => throw (IO.userError diagnostic.message)
  let agentDossier := project dossier "agent"
  let agentState ← match replay agentDossier with
    | .ok state => pure state
    | .error diagnostic => throw (IO.userError diagnostic.message)
  let bundle := exportBundle agentDossier
  IO.println s!"validated={fullState.event_ids.size}; agent_events={agentState.event_ids.size}"
  IO.println s!"export={bundle.format}; lean={bundle.lean_version}"
```

Run `lake env lean --run examples/ValidateExport.lean`. Expected output:

```
validated=10; agent_events=8
export=slean-export/0.1.0; lean=4.28.0
```

To write and revalidate the complete envelope, use the CLI on this synthetic fixture:

```
lake exe slean export examples/valid.json agent > /tmp/slean-agent-export.json
lake exe slean validate /tmp/slean-agent-export.json
```

The second command reports `{"case_id":"synthetic-decision-1","events":8,"ok":true}`. The agent projection omits owner-only events before deriving the export, but a real export still needs a content review before sharing; validation does not decide whether free text is safe to disclose.

*4. Keep empirical results separate from proof receipts*

Problem: prevent a declared formal claim from being treated as kernel checked just because its input status says so. This program deliberately sets `status := "kernel_checked"` on a matching local theorem reference; `proofReceipt` still returns `declared`.

*Complete source: `examples/FormalBoundary.lean`*

```
import Slean

open Lean Slean

private def formalIdentity : Identity :=
  { id := "formal-claim-demo", version := 1, domain := "synthetic-computation",
    provenance := "synthetic://worked-examples", audience := "agent" }

private def formalClaim : FormalClaimRef :=
  { identity := formalIdentity,
    declaration := checkedDeclaration, statement := checkedStatement,
    toolchain := checkedToolchain, status := "kernel_checked" }

def main : IO Unit := do
  let receipt := proofReceipt formalClaim
  let status := (receipt.getObjValAs? String "status").toOption.getD "missing"
  let eligible := (receipt.getObjValAs? Bool "attestation_eligible").toOption.getD false
  IO.println s!"eligible={eligible}; status={status}"
```

Run `lake env lean --run examples/FormalBoundary.lean`. Expected output: `eligible=true; status=declared`. A matching declaration and toolchain make the claim eligible for *separate* clean-build attestation; this program does not issue that attestation. The theorem concerns a conditional link between recorded promotion evidence and prior records. Neither the local theorem nor an empirical `pass` proves that the measurement, evaluator, or scientific claim is true.

# Limits and development status

*Slean checks here:* the versioned case shape, IDs and references, causal journal order, local exact decimal comparison, stated cost cap, promotion rule, AND/OR gate references, and audience projection. It can report a precise error or preserve an undetermined result.

*Slean does not check here:* that the measurement happened, that artifact bytes are authentic, that an external clock or evaluator is reliable, that an AND/OR gate proves its target, that a human decision is wise, or that the scientific claim is true. The local Lean theorem concerns a conditional property of the mechanism, not those empirical facts. No independent proof checker is configured.

This site is a local pre-publication prototype. Its examples are synthetic. Public licensing, repository visibility, domain deployment, and integrations remain separate decisions. The build runs tests and compiles examples before generating the manual. `build-info.json` identifies the source commit, tree cleanliness when Git metadata is available, schema, Lean, and selected tag; without Git metadata, `source_tree_clean` is `null` because cleanliness is unknown. A build without a tag remains a development preview.

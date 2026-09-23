import VersoManual
import Slean

open Verso.Genre Manual
open Verso.Genre.Manual.InlineLean

#doc (Manual) "Slean" =>
%%%
shortTitle := "Slean"
%%%

Follow a research decision to its evidence.

Slean is a Lean 4 library and JSON tool for inspecting a research dossier. It checks structure, references, chronology, exact decimal rules, and a bounded source trace. The first example is synthetic; Slean does not prove an empirical claim.

Development preview · schema 0.2.0 · Lean 4.28.0. No tag is selected for this build.

Run the checked case from the repository root:

```
lake exe slean validate examples/valid.json
```

The tool returns:

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

Continue to the quickstart to inspect a journal prefix and the audience-safe export.

# Start with a checked case

The first task is to validate the synthetic dossier included in this repository. With Lean 4.28.0 and Lake installed, run these commands from the repository root:

```
lake build
lake exe slean validate examples/valid.json
lake exe slean replay examples/valid.json 7
lake exe slean export examples/valid.json agent
```

The validation command returns:

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

The prefix replay returns the state after seven events. Agent export removes owner-only objects before computing the visible case. The example is synthetic and contains no scientific result.

The same dossier can be constructed in Lean:

```lean
#check Slean.CaseFile
#check Slean.replay
#check Slean.assessExact
```

These declarations compile in the pinned toolchain when this manual builds. The complete typed example is `examples/Synthetic.lean`; `bash tests/check.sh` compiles it and compares its agent JSON bytes with the JSON fixture export.

# Read the decision

An `Observation` names a prior run, metric, unit, value or unknown state, artifact reference, and time. An `Assessment` cites prior observations under a frozen protocol. A routine `promote` requires a passing local exact assessment. A human `override` needs a reason and remains separate from a `pass`.

```lean
#check Slean.FrozenProtocol
#check Slean.Observation
#check Slean.Assessment
#check Slean.PromotionDecision
```

One exact decimal metric and one observation can support the local comparator. External rules may cite many observations but stay `external_unverified`. No compiler success turns an external model comparison into scientific truth.

# Follow provenance

Schema 0.2 can retain a complete parsed source manifest, protocol, and event stream as owner-only canonical JSON strings. The bounded adapter checks one first freeze, source event order, prediction-to-observation links, completion agreement with the manifest, and typed coverage of every source observation.

```lean
#check Slean.SourceRecord
#check Slean.validateSourceTrace
```

The source adapter reads a trace in memory and prints only an aggregate report. It does not save a private dossier. Source artifact bytes remain at the source; the adapter computes SHA-256 and Lean checks the supplied digest links. The external evaluator is not run or certified by Slean.

# Format and API

`schema/v0.1.0.schema.json` describes the original case wire shape. `schema/v0.2.0.schema.json` adds source records. `schema_version` and `semantics_version` must match one supported pair. There is no implicit migration.

```lean
#check Slean.Event
#check Slean.step
#check Slean.project
#check Slean.view
```

The CLI supports `validate`, `replay`, `export`, `view`, and `proof` on a case path or `-` for standard input. Run `lake exe slean proof-statement` to inspect the single pinned local theorem statement and toolchain. Imported proof-status text alone never grants `kernel_checked`.

# Limits and development status

This is a local pre-publication prototype. The source-trace assessment remains `external_unverified`; artifact contents, external clocks, evaluator logic, independent proof checking, and scientific accuracy remain outside the Lean theorem. Public license, repository visibility, domain deployment, and integrations await separate decisions.

The build compiles the examples and tests before it creates the site artifact. `build-info.json` in the generated site directory records the base commit and whether the source tree was clean. A clean build identifies its exact source commit.

# Slean V0 research dossier

Slean is a local, pre-publication Lean 4 prototype for checking the structure and decision history of a research dossier. It does not evaluate the truth of an empirical claim. The [gate V retest](docs/gate-v-retest.md) found one useful cross-file check and permits a bounded documentation prototype; the [earlier negative result](docs/gate-v.md) remains available.

## Build and inspect

Install `elan`, then run:

```sh
lake build
bash tests/check.sh
lake exe slean validate examples/valid.json
lake exe slean replay examples/valid.json 7
lake exe slean export examples/valid.json agent
lake exe slean view examples/valid.json agent
lake exe slean timeline examples/valid.json agent
lake exe slean proof-statement
```

`validate` returns a JSON result and a nonzero exit code on error. `replay` returns the state after a prefix of the journal. `export` writes a canonical V0 case to standard output. `view` derives observation, relation and recorded dependency-gate data from that projection. `timeline` returns validated state snapshots at every projected prefix for the local Explorer. `proof` reports the local status of formal claims in a case. The CLI accepts `-` as an input path for standard input. Do not send a private owner export or Explorer artifact to an agent or a public channel.

The equivalent typed Lean example is [examples/Synthetic.lean](examples/Synthetic.lean). Its agent JSON bytes match the JSON fixture projection. All checked-in examples are synthetic. The local trace audit reads source files but never writes their converted content: `python3 tools/audit_autoresearch_trace.py <trace-directory>`. Its report contains aggregate checks and field names, while the owner-only source JSON stays in memory.

The [Verso manual](site/README.md) builds locally with compiled Lean snippets. It is a development preview, not a deployed site.

The [same-case Blueprint prototype](blueprint/README.md) records what Blueprint already makes readable and where experimental journal review still needs Slean. The [comparison decision](docs/blueprint-comparison.md) scopes a local Explorer to journal prefixes and evidence.

The [local Explorer](explorer/README.md) renders those checked prefixes into a self-contained agent view. Owner output requires an explicit audience option and separate private artifact directory.

## Contract and limits

- `lean-toolchain` pins Lean 4.28.0. `lake-manifest.json` has no external packages; Mathlib is not required.
- `schema/v0.1.0.schema.json` specifies the original wire shape; `schema/v0.2.0.schema.json` adds owner-only source records; `schema/v0.3.0.schema.json` adds explicit AND/OR dependency gates. Lean replay is normative for references, chronology, exact decisions, and stated cost caps. Gates are recorded claims, not evaluated truth. Unsupported or mismatched schema and semantics versions fail; there is no implicit migration.
- One exact decimal metric and one prior observation can support an automatic `pass` or `fail`. External rules may cite many prior observations, but stay `external_unverified`. Unknown and technical errors stay `undetermined`.
- The 0.2 source-trace adapter retains every parsed manifest, protocol, and event JSON object in owner-only records. It checks source sequence, the single freeze, prediction links, completion-to-manifest agreement, observation count, and typed coverage. The Python adapter computes canonical SHA-256; Lean checks its links, not the hash computation or external evaluator.
- A routine `promote` needs prior passing evidence. A human `override` needs a reason and does not become a `pass`.
- The only local `kernel_checked` claim is the pinned theorem in `Slean/Proof.lean`. Imported JSON status never grants this status. No independent checker is configured.
- Agent projection filters hidden events before it computes the view. An owner-only case header is redacted. Agent-visible objects must be safe for that audience.

This repository has no approved public license or deployment. Apache-2.0 is a proposal for owner review, not a license grant. Do not publish, deploy, or treat a compiled dossier as scientific validation.

See [product scope](PRODUCT.md), [architecture](ARCHITECTURE.md), [fixture baseline](docs/baseline.md), and [gate results](ROADMAP.md).

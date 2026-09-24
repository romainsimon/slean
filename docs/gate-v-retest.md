# Gate V retest: continue to documentation prototype

This retest follows the historical [reduce decision](gate-v.md). The earlier
adapter dropped 47 of 48 observations from the assessment, discarded source
decision fields from the dossier, and accepted a changed protocol file and a
second freeze. Those were implementation defects. The original report remains
the baseline; this document records the repair and a new result.

## Same source, repaired conversion

The adapter read the same development trace's `manifest.json`, `protocol.json`,
and `events.jsonl` without editing them. It found 98 source events: one first
freeze, 48 frozen predictions, 48 observations, and one completion. Source IDs
and sequences were valid, the protocol digest matched the freeze and manifest,
and all source artifact paths, sizes, and hashes matched. Source file hashes
were identical before and after the audit.

The adapter piped a 297-event Slean 0.2 case through the CLI in memory. The
owner dossier retained the complete parsed JSON objects for the manifest,
protocol, and 98 source events as canonical JSON strings. No source field was
omitted. The typed assessment referenced all 48 observations, in source order.
Its verdict was `external_unverified`; the source model comparison and audit
adequacy were not reproduced or proved by Lean. The adapter wrote no private
case or export to disk. A synthetic contract test verifies owner round-trip and
that source records do not enter the agent export.

A later Slean-only guard checks every converted owner source record against its
parsed input object, source role, owner audience, canonical JSON and SHA-256.
The loss report now names missing or changed source paths instead of assuming
`wire_fields_lost: []`. It also lists source event envelope fields and nested
budget/usage fields that remain outside the typed model. Synthetic regressions
remove a nested manifest field while rehashing the altered record and omit an
event record; both are reported as preservation failures. At code commit
`094ad321f537d4891b2ed7e60bfea65935aec500`, the read-only CLI was rerun
on the same 98-event development trace. It exited 0 and reported 297 converted
events, valid artifact hashes, unchanged source files, Slean validation
accepted, no lost wire fields or source-record integrity errors, and
`source_preservation_verified: true`. All eight in-memory probes returned their
expected diagnostics and `structural_gate_passed` was true. The aggregate report
did not write the converted dossier or source values to disk or stdout. This
run does not authenticate the source values. An unrecognized scientific
decision in a completed source trace now fails conversion instead of silently
becoming `defer`.
The audit command also emits `structural_gate_passed` and exits nonzero when
source shape, artifact hashes, preservation, Slean validation or the named
mutation probes fail. A failed run still prints its aggregate JSON report.
This is a structural evidence gate, not a claim of scientific value.

The following probes changed copies held in memory. They were not faults
observed in the original source and did not change its files.

| Probe | Slean diagnostic |
|---|---|
| Unit mismatch | `metric_unit` |
| Observation without prior prediction | `missing_relation_ref` |
| Observation after assessment | `future_observation` |
| Changed protocol file | `source_protocol_digest` |
| Second freeze | `source_second_freeze` |
| Completion decision conflicts with manifest result | `source_decision_provenance` |
| Same conflict with refreshed event artifact hash metadata | `source_decision_provenance` |
| Assessment omits one source observation | `source_projection` |

## What is new compared with the source flow

The source runtime's `verify_manifest` checks the schema version and listed
artifact paths, sizes, and hashes. On a **synthetic** manifest and completion
event, the real `verify_manifest` function accepted an event whose decision
conflicted with `manifest.result.discrimination.decision` when the event file's
hash entry was self-consistent. This is expected from its code: that function
does not compare event payloads to the manifest. The source
`replay_discrimination` compares a fresh run's result with the source manifest,
but does not read source event payloads. The latter conclusion is from code
inspection, not from running a modified private replay. The Slean check binds
the source completion event to the manifest result and source observation
count, even with a refreshed hash entry. The changed completion is credible
for the actual event shape; the in-memory probe rejected it on the real trace.

The original runtime already checks artifact integrity and recomputes its own
scientific result. Slean's added control concerns agreement **between** its
stored trace and manifest, as well as a single frozen protocol and complete
assessment references. [Verso Blueprint](https://github.com/leanprover/verso-blueprint)
documents theorem progress, source links, metadata, and dependency graphs.
Its documented features do not include this experimental event-to-result
validator. A custom Blueprint extension could implement one; no same-case
Blueprint prototype has yet measured that extension's cost.

## Decision and limits

**V result: continue to a bounded documentation prototype.** This establishes
one useful structural check beyond the existing source verifier on the actual
trace shape, without discarding source fields. It does not establish improved
scientific accuracy, a safe publication, or value for a general DSL. The
canonical SHA fields are computed by the trusted Python adapter; Lean checks
their links but does not recompute SHA-256. Source artifact bytes stay in the
source repository. Some fields remain present only in owner source records and
are not typed decision rules. Typed times use UTC seconds, while owner records
retain source precision. External assessments never become a local `pass`.

Proceed with a compiled quickstart and a Verso test. Compare Blueprint on the
same synthetic dossier before deciding whether any custom Explorer is needed.
Keep site publication, repository visibility, license, integrations, and
scientific campaigns as separate decisions.

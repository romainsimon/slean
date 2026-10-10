# 2026-10-07: The agent environment is part of the measurement

Published 2026-10-11. Three pre-registered ablations compared the same v1 notes on six shared `frontier` seeds each: 18 labs per ablation, 54 labs total, each with 3,000 cell updates and 200 proposals. Seed values and private instructions are withheld. Differences are fractions of possible discoveries; 0.10 means ten percentage points.

Each ablation registered two one-sided exact paired sign-flip tests with Holm correction at α = 0.05. These were diagnostic experiments, not promotion or panel evidence.

## Results and metric reanalysis

The original decisions remain recorded. The reanalysis below, dated 2026-10-11, applies the corrected metric: laws + mechanisms + structures **within reference bounds** + conservation laws, divided by the corresponding possible discoveries. Beyond-bound structures remain findings but cannot enter a numerator whose denominator excludes them.

| Ablation and contrast | Recorded mean / p | Corrected mean / p | Holm conclusion |
| --- | --- | --- | --- |
| 1: operator − isolated | +0.333 / 0.015625 | +0.301 / 0.015625 | Reject in primary analysis |
| 1: isolated + operator text − isolated | −0.074 / 0.875 | −0.074 / 0.875 | Not rejected |
| 2: isolated with auto permission − isolated | −0.090 / 0.8125 | −0.084 / 0.8125 | Not rejected |
| 2: isolated without safe mode − isolated | −0.060 / 0.765625 | −0.070 / 0.828125 | Not rejected |
| 3: operator − operator without hooks | +0.106 / 0.328125 | +0.082 / 0.359375 | Not rejected |
| 3: operator − operator without extra tools/MCP | −0.053 / 0.65625 | −0.057 / 0.71875 | Not rejected |

The first experiment supports a large environment effect, but does not isolate its cause. Copying the operator's instructions as text did not reproduce it. The later null results do **not** establish that hooks, safe mode, permissions or extra capabilities have no effect; six pairs give limited power.

### Audit false positive and sensitivity

In ablation 1, the isolated lab in pair 3 was scored zero because the audit mistook its own file name for access outside the lab. Its kernel check passed. The registered primary result retains that zero. Counting its findings gives 0.44 under the old metric and 0.42 under the corrected one.

| Operator − isolated | Recorded metric | Corrected metric |
| --- | --- | --- |
| Primary, failed audit retained at zero | +0.333, p = 0.015625 | +0.301, p = 0.015625 |
| Sensitivity, false positive corrected | +0.260, p = 0.046875 | +0.231, p = 0.046875 |

The sensitivity result is **not significant after Holm correction** (the first threshold is 0.025). The text-only sensitivity is negative: corrected mean −0.144, p = 0.96875.

### Crash and validity

- Ablation 1: 17/18 labs had clean audits, successful kernel checks and no recorded failure; the remaining audit false positive is described above.
- Ablation 2: all 18 labs had clean audits, successful kernel checks and no recorded failure.
- Ablation 3: 17/18 met those checks. One operator lab crashed while exporting a conservation current above Python's decimal-conversion limit. Its original audit and kernel fields were unavailable; it remains zero in the registered analysis. After the engine fix its score was 8/55 and the kernel passed, a sensitivity result rather than a replacement of the original decision.

These counts were checked against each saved row's `audit_clean`, `kernel.ok` and `failure_mode` fields. A clean transcript audit is evidence of what was logged, not a proof that no unlogged access occurred.

## Isolation limits

The first ablation revealed shared `/tmp` use. Each lab now gets private temporary storage. Three operator labs never used `/tmp`, and transcript inspection found no systematic reuse, but independence cannot be guaranteed for runs before the fix. Ablations 2 and 3 used private temporary storage.

Other checkouts and stored sessions were hidden later, before the continuation calibration and generation 4. Earlier transcripts showed no read of the private generator, but absence from a transcript is not a guarantee of absence.

## Resulting measurement profile

The registered `operator-1` profile retains the operator's settings, instructions, hooks and plugins, restricts access to four lab tools and removes MCP servers. Profile and configuration fingerprint join the panel key; a changed key requires a new panel. Its measured levels must not be compared across different environments or unpaired seed sets.

See [A/A calibration and continuation](2026-10-08-measurement-design.md) and the [measurement policy](../MEASUREMENT.md).

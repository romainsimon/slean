# Lean export in a second Lake project

This project imports the [frozen direct-tool example](../direct-lean/README.md)
through an ordinary Lake path dependency. `FormalExample.energy_preserved`
applies `DirectReuse.energy_at_two_times` with its hypotheses intact. It also
contains a definition, a polymorphic theorem and a quoted identifier to test
the exporter's generality.

From this directory, with Lean 4.34.1 installed:

```sh
lake update
lake build FormalExample
mkdir -p _out
lake env lean Export.lean
```

The pinned dependencies and caches need to be available. On the observed
machine, the Git package directories were shared with the existing baseline
cache; no second Mathlib cache was downloaded. This is local integration
evidence, not a fresh-machine installation or release test.

[`Export.lean`](Export.lean) selects eleven declarations, including the real
Physlib theorem, its two recorded uses and deliberately incomplete/unsupported
proof fixtures. The [exporter check](../../../packages/lean/README.md#validation)
recomputes their native data, verifies the package structure and checks that
presentation readiness cannot create a stronger verification result.

The current receiver retains these extractions as declarations. Application
planning, remaining-obligation diagnostics and receiver proof verification
remain SR-T05–06. The comparison with direct tools remains Gate U work.

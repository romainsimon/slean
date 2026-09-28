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

## Native application trace

[`ApplicationExample.lean`](ApplicationExample.lean) applies the same theorem
twice with `slean_apply`. One use leaves an equation-of-motion goal for the next
proof step; the other supplies all six arguments. Both final theorems remain
conditional on the caller's smoothness and equation-of-motion hypotheses.

```sh
lake build ApplicationExample
mkdir -p _out
lake env lean ExportApplications.lean
```

[`ExportApplications.lean`](ExportApplications.lean) writes the producer,
consumer and native application extractions. From the repository root:

```sh
conformance/.venv/bin/python packages/lean/export.py \
  --project examples/reuse/with-slean-lean \
  --input examples/reuse/with-slean-lean/_out/application-producer.json \
  --output examples/reuse/with-slean-lean/_out/application-producer-module

conformance/.venv/bin/python packages/lean/export.py \
  --project examples/reuse/with-slean-lean \
  --input examples/reuse/with-slean-lean/_out/application-consumer.json \
  --applications examples/reuse/with-slean-lean/_out/applications.json \
  --dependency-module examples/reuse/with-slean-lean/_out/application-producer-module \
  --output examples/reuse/with-slean-lean/_out/application-consumer-module
```

The output directories must be new. The application records link exact producer
and consumer versions, source/statement artifacts, native proof dependencies,
input bindings and caller context. Input plans are retrospective projections
of the recorded invocations. They do not establish preregistration.

The [application check](../../../packages/lean/README.md#validation) rejects
the [missing hypothesis](negative/MissingApplicationHypothesis.lean) and
[changed conclusion](negative/ChangedApplicationStatement.lean), then checks
the exported records. Its frozen direct-tool inputs remain unchanged.

The receiver retains imported proof claims as declarations. Independent
artifact verification remains SR-T06; general offline planning and the
comparison with direct tools remain later work. This oscillator is an internal
engineering fixture, not a selected scientific discovery campaign.

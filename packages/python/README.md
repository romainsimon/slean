# Python authoring and offline reading (experimental)

The package implements SR-T07's bounded quantity/method profile API. `Author`
creates components, plans, execution records and attributed evidence; `Reader`
checks exact module bytes and plans quantity applications offline. Creating an
execution record records a supplied result: it does not run or reproduce the
method. The calibration execution/research cycle is SR-T08 and remains open.
This is a local candidate wheel, not a published standard or PyPI release.

From the repository root, prepare the pinned environment and validate it:

```sh
python3 -m venv packages/python/.venv
packages/python/.venv/bin/python -m pip install --require-hashes -r packages/python/requirements.lock
packages/python/.venv/bin/python -m pip install --require-hashes -r packages/python/build-requirements.lock
packages/python/.venv/bin/python packages/python/check_sdk.py
packages/python/.venv/bin/python -m pip install --no-deps --no-build-isolation ./packages/python
```

The checker tests the SDK, builds its wheel without dependency resolution,
installs it in a temporary directory, and runs an isolated Python process with
an empty working directory and no repository imports. Schemas and unit mapping
are bundled resources. The canonical wire checker has one scientific-rule
source, `conformance/contract.py`; `generate_runtime.py` changes only its resource
loader and detects drift. This bundled copy is not the SR-T14 independent reader.
Runtime tests apply the shared positive, negative and requirement vectors.

## Declare and inspect a method

```python
from slean import Author, Reader, INTERFACE_POLICY, scalar, scalar_port, equals_requirement

profile = "slean-quantity/0.1-draft.1"
author = Author(payloads={"method.py": b"# Owned scientific source\n"})
condition = equals_requirement("sensor", location="context", field="sensor",
                               expected={"literal": "sensor-A"})
method = author.component(
    id="inverse", kind="method", name="Affine sensor inverse",
    interface={"profile": profile, "value": {
        "inputs": {"reading": scalar_port(dimension="voltage", unit="volt")},
        "outputs": {"displacement": scalar_port(dimension="length", unit="millimeter")},
        "entrypoint": {"artifact": {"path": "method.py"}, "symbol": "inverse"}}},
    requires=condition, sources=[{"path": "method.py"}], license="unknown")
revision = author.pack("module", publishable=[method])
reader = Reader("module")
plan = reader.apply(method, bindings={"reading": {"typed": {"profile": profile,
    "value": scalar("8500", dimension="voltage", unit="millivolt",
                    uncertainty={"kind": "unknown"})}}},
    context={"sensor": {"literal": "sensor-A"}}, policy=INTERFACE_POLICY)
assert plan["compatibility"] == "compatible"
assert plan["computational_reproduction"] == "not_performed"
```

The source above is only an interface illustration; the named function is not
implemented or executed by the declaration. A compatibility result concerns
its declared ports/conditions. Model applicability and empirical validity need
their own checks and evidence.

`table_port` and `table` declare CSV columns and an exact artifact reference.
`quantity_requirement`, `range_requirement`, `equals_requirement` and
`applicability_requirement` build the supported leaves. Ranges compare inclusive
nominal magnitudes after conversion. Scalar equality compares converted nominal
magnitudes; it does not equate uncertainty distributions. Artifact/reference
equality compares exact module/path or module/record identity. Text uses exact
string equality, without semantic similarity. Every leaf diagnostic is retained
even when a different `any` branch succeeds. Unknown optional leaves remain
opaque and unsupported individually; unknown mandatory profiles block use.

`Author.plan` copies producer conditions and can add stricter requirements.
`plan_test` records a declared prediction and evaluation bound;
`record_execution` separately records outputs under that plan. `record_evidence`
does not verify its result. `record_attempt` creates an attributed reuse-attempt
annotation, preserves earlier records and projects failed leaf diagnostics to
requirement/status/reason. Relabelling a test plan or an existing attempt is
rejected; author a separate attempt. A retry changing the original inputs or
context is rejected by the wire checker.

`pack` exports only explicitly selected local records and declared payloads.
It never follows private ancestors into the export. Missing selected references
cause failure, with no output module. External references stay pinned to their
original revisions. Existing destinations are not overwritten. Unknown profile
bodies/annotations are data and are never searched for files or treated as
executable references. This writes a local directory and does not upload it.

## Quantity and trust limits

Exact wire decimals remain strings with their original spelling. Conversion
returns a new value through Pint 0.26.1 and the pinned definition hashes in the
[canonical mapping](../../profiles/quantity-map.json). Only its seven units are
supported. A base-unit name in a row does not authorize another wire unit.
Long decimal inputs expand arithmetic precision rather than silently using the
default context. Uncertainty remains explicit, with its own unit.

Missing values stay distinct from zero. Allowed missing values are unresolved;
wrong dimensions are violated; unknown units and uncertainty kinds are
unsupported. Absolute Celsius converts to Kelvin. Temperature-difference
semantics, including temperature uncertainty and test bounds, remain unsupported
in this initial profile. Supported bounds in other dimensions keep their
explicit unit. CSV checks inspect actual header, rows, decimals, missing values
and column dimensions using receiver-owned parsing; no payload code executes.

`inspect` preserves imported evidence as declared, including a result saying
`reproduced`. `uses` returns direct component applications in the loaded corpus
only. It does not conflate these with proof dependencies or causal scientific
influence. `verify(..., policy=INTEGRITY_POLICY)` rechecks manifest and payload
bytes; it reports integrity only. Scientific verification policies are not
dispatched by this reader yet. An unsupported policy returns unsupported with
no fallback. The separate Lean receiver remains in
[`packages/lean`](../lean/README.md).

# Calibration to measurement through Slean

This synthetic example is SR-T08's numerical checkpoint. A producer fits an
affine sensor response from the frozen direct-tool CSV. A separate consumer
uses the exported inverse method through the public SDK, without importing the
producer's helpers. It calculates and reproduces 4 mm from 8.5 V, with gain
2 V/mm and offset 0.5 V. The conditional error calculation gives 0.01 mm under
an assumed 0.02 V residual bound and exact gain.

This does not demonstrate a scientific discovery. The affine response, exact
gain treatment and residual bound remain three explicit open assumptions.
Physical parameter uncertainty stays unknown. Neither a fitted result nor
a reproduced calculation promotes these assumptions to established facts.

## Run locally

Prepare the pinned [SDK environment](../../../packages/python/README.md), then
run from the repository root on the qualified macOS backend:

```sh
PYTHONPATH=packages/python packages/python/.venv/bin/python examples/reuse/with-slean-python/check_path.py
```

The checker creates temporary producer and consumer directories, runs ordinary
Python/Pint methods, verifies a selected imported reproduction claim by a fresh
call, and removes its generated modules on completion. No model API, server,
network experiment or source-baseline modification is involved. Installation
of pinned dependencies is a separate setup step.

`producer.py` and `consumer.py` also have command-line entrypoints. The consumer
requires independently selected calibration and reviewed-source digests;
inspection never treats a producer-supplied approval hash as authority. The
example driver selects and reviews its owned `methods.py` fixture.

## Exported objects

The producer exports separate modules for the method/data, original fit plan,
fit execution, fresh fit reproduction, and reusable calibrated inverse. The
consumer exports its original measurement plan, execution result and fresh
reproduction evidence separately. Executions reference the exact original plan.
Per-output evidence distinguishes different quantity dimensions. Every external
reference keeps its original module identity.

`methods.py` contains ordinary `calibrate`, `inverse` and `predict` functions.
`producer.py` constructs the scientific interfaces and context conditions.
`consumer.py` imports only the SDK and reads producer modules. `check_path.py`
is the test driver; it is not an autonomous research planner.

## Validation and remaining work

The [recorded path check](observed-path.json) covers nominal computation,
equivalent mV/Celsius inputs and ten negative/control cases: wrong dimension,
range, sensor, temperature, missing temperature, wrong version, changed source
approval, unacknowledged model assumptions, omitted offset and unsupported
parameter uncertainty. It checks that all 34 frozen baseline files are unchanged.
Nominal comparisons accept equivalent decimal spellings; wire serialization
keeps the original exact spelling, as checked separately by the SDK tests.

The [SDK execution policy](../../../packages/python/EXECUTION.md) records the
ABI, receiver authority, numerical tolerance and local process limits. Its
installed-wheel check establishes operation outside the source checkout.

The failed prediction, explicit revision, later blocked-use retry and Lean
conditional error-theorem bridge are still required to close SR-T08. RO-Crate,
the complete usefulness comparison, independent reading and external adoption
remain separate tasks. This checkpoint does not close M2 or Gate U.

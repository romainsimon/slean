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

The numerical report is the earlier execution checkpoint. The later
[cycle report](observed-cycle.json) adds a failed prediction, calculated offset
revision, separate second test and blocked-use retry. Run its check separately:

```sh
PYTHONPATH=packages/python packages/python/.venv/bin/python examples/reuse/with-slean-python/check_cycle.py
```

The original hypothesis predicts 8.5 V and misses the first observation by
0.1 V under the frozen 0.02 V bound. A separate method takes the gain through
an exact output reference to the calibration execution and calculates the new
offset, 0.6 V. The revised model predicts 6.6 V for a separate 3 mm observation.
The original failed assessment stays failed. The same blocked 8.6 V measurement
then yields 4 mm through the unchanged inverse source at the revised context.
The temperature check passes; three physical assumptions remain open.

The controller exports the first prediction plan before exposing the new reading
in its dependency corpus. Each observation artifact is added after the respective
plan. This is controlled script order, not real-world preregistration. A second
reader reconstructs the exported links without private chat state, using the same
SDK; it is not the separately implemented reader required by SR-T14.

`slean.research.Research` performs the comparisons, scoped query and retry checks.
The [research policy](../../../packages/python/RESEARCH.md) states their precise
authority. A new citation cannot repair an incompatible method. A changed plan
cannot replace an old failed test. The motivated follow-up and temporal-drift
alternative remain unresolved.

The conditional Lean error-theorem bridge and complete remaining negative-case
acceptance are still required to close SR-T08. RO-Crate, Gate U, independent
reading and external adoption remain separate tasks. This does not close M2.

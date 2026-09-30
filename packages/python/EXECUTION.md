# Reviewed numerical execution and reproduction

This explicit local operation implements the numerical part of SR-T08. It does
not establish physical validity, statistical adequacy, the full research cycle
or Gate U. Authoring, inspection and planning still never execute payload code.
The policy identifier is `reviewed-python-quantity/0.1-draft.1`.

## Receiver choices and call interface

Import `Executor` and `POLICY` from `slean.execution`. The receiver supplies:

- A reader with the exact application, producer and dependency modules.
- `expected_component`, an exact `{module, id}` reference chosen independently.
- `reviewed_source_sha256`, the digest of the single source file the receiver reviewed.
- The named execution policy and, when needed, explicit acknowledgement of open
  model applicability assumptions with `allow_conditional=True`.

`run(application, ...)` executes a selected planned or executed application.
An execution linked to a plan must preserve its component, bindings, context and
requirements. The application cannot remove the producer's conditions. Added
conditions are checked too. Missing sensor, temperature or numerical inputs
cannot be accepted as model assumptions. Unsupported units or uncertainty
semantics prevent execution under this policy.

The source declares a function through its entrypoint artifact and symbol.
The ordinary function receives named keyword arguments. Scalar inputs are
Pint quantities with Decimal magnitudes, converted to the declared port unit.
CSV inputs become rows of named Pint quantities; text inputs become strings.
Declared scalar parameters are passed as additional keyword arguments. Input
and parameter names cannot collide. Missing numerical cells are rejected.

The function returns a dictionary containing exactly the declared outputs.
Scalar outputs must be Pint quantities of the declared physical dimension;
text outputs must be strings. Table outputs are unsupported in this policy.
Outputs carry explicit unknown uncertainty. Executing a function does not
estimate a confidence interval or certify its physical assumptions.

## Reproduce and check an imported claim

`reproduce(executed_application, tolerances=..., ...)` runs the selected method
again and compares every output with the recorded result. Supply a tolerance
for every output. Scalar tolerances must be nonmissing, nonnegative quantities
of the output dimension. Comparisons convert units and use absolute nominal
error. Text comparisons use exact equality and a null tolerance. Temperature
difference bounds remain unsupported in the initial quantity profile.

The local result distinguishes `reproduced`, `different` and `unsupported`.
An execution timeout, output limit or tool failure remains a separate outcome;
it is not a scientific counterexample. Tolerance and recorded output bytes are
bound into the comparison digest.

Computation evidence selects one output using `output_policy(name)`, which
encodes the output name in the policy fragment. This permits separate gain and
offset claims with different tolerance dimensions. `verify_evidence` requires
the exact `expected_evidence` reference and receiver-selected tolerances. It
checks the evidence's subject, implementation, context, comparison rule and
numeric representation, then runs a fresh reproduction. A changed tolerance
cannot silently reinterpret the imported claim.

`Reader.inspect` continues to report imported evidence as declared, including
records that say `reproduced`. A saved JSON report grants no receiver authority.
`Reader.verify` still dispatches integrity checks only. Numerical verification
uses the explicit `Executor`; the general reader does not silently execute it.

## Numeric and environment identity

The receiver records the requested Decimal precision (default 28), rounding
mode after the call and actual output magnitude types. The request is accepted
only for precisions from 16 through 512. Output error comparisons use enough
precision for the supplied decimal strings. This records the method's numeric
representation; it does not make its algorithm or fitted parameters exact.

The report binds the Python binary, installed dependency file hashes, SDK
source/resources, selected source, application and component revision. It
rechecks original payloads and the environment after the call. Dependency
binaries remain receiver-trusted. An invocation digest identifies this local
operation, not semantic equivalence with another environment.

## Local execution boundary

The qualified backend is macOS `sandbox-exec`, using the shared receiver-owned
boundary generated from `packages/lean/verification/boundary.py`. Other
platforms return unsupported, with no unrestricted fallback. The child has a
private copied runtime, a reviewed source file, a fixed JSON request and the
receiver's installed Python environment. It cannot read unrelated local files,
write files, create subprocesses or open the network. It starts with an isolated
Python import path and a minimal environment.

Limits are 1 MiB for source, 16 MiB for the input request, 1 MiB for captured
output, 30 CPU seconds, 128 open files and a receiver-selected wall limit
(default 30 seconds, at most 120). Timeout/overflow kills and reaps the process
group. No hard memory or aggregate disk quota is provided on macOS. This is an
explicit reviewed-source local operation, not a hostile-upload service.

## Recorded qualification

The [execution SDK report](observed-execution.json) records 32 test groups and
an installed-wheel numerical call outside the checkout. Seven execution groups
include actual fit/reproduction, stricter requirements, wrong output dimensions,
foreign-file/network/fork denial, timeout/overflow, imported claim verification
and a changed external plan. The [calibration report](../../examples/reuse/with-slean-python/observed-path.json)
adds the independently authored consumer and frozen fixture controls.

The earlier [SR-T07 report](observed-sdk.json) remains historical evidence for
the authoring/offline reader version. It is not a report for the later runtime.

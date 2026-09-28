# Direct Python and RO-Crate comparison

This internal engineering fixture uses Python, Pint, ordinary JSON records and
an existing RO-Crate reader. It has no Slean runtime. It supplies the computational
part of SR-T02 and the comparison for the proposed Slean contract. The research
subject for Mutome remains undecided.

The result is useful as a demanding alternative: existing tools already support
this bounded research cycle with explicit integration code. A Slean advantage
has not been measured. The [comparison protocol](../COMPARISON.md) keeps this
alternative available, including its reusable helpers.

## Reproduce

Use Python 3.12 or newer and Node.js 20 or newer. The recorded run used Python
3.14.3 and Node.js 24.4.1. From this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
npm ci --ignore-scripts
.venv/bin/python check_baseline.py
.venv/bin/python package_baseline.py _out/example
node read_crate.mjs _out/example
```

The package command requires a new output directory. Set `SLEAN_NODE` if Node
is outside `PATH`. Installation requires network access. The checks use local
files after installation. They do not fetch a JSON-LD context or execute source
from an imported crate. The test explicitly runs the known exported consumer
in a temporary directory with its installed dependencies and without a
`PYTHONPATH` referring to the source checkout.

`check_baseline.py` checks dependency versions, the unit-definition file hashes,
Decimal precision/rounding and every source/input digest in the shared freeze.
It runs the Python suite, packages both paths and reads the result with the
unmodified `ro-crate@3.7.2` library. See
[`observed-baseline.json`](observed-baseline.json) for the recorded result and
its measured execution scope. Rerun the checks to obtain current evidence.

The formal checks are separate commands in
[`../direct-lean/`](../direct-lean/README.md). The crate includes that Lake
project's sources, locks and recorded reports. Its reader preserves those
reports but does not independently repeat the Lean checks.

## What the example does

1. Fit an affine calibration from the supplied synthetic CSV. The gain is
   `2 V/mm` and the offset is `0.5 V`.
2. A separate consumer applies the shared method to `8.5 V`, obtaining `4 mm`.
   The conditional residual error bound is `0.01 mm`. Parameter uncertainty
   and physical applicability remain unresolved.
3. Preserve a failed attempt to apply the calibration at another temperature.
4. Test a hypothesis extending the original model to that temperature. Its
   first prediction misses the observation by `0.1 V`, outside the `0.02 V`
   rule fixed before the observation is bound in the script.
5. Create a new model with a changed offset. A second, separate observation
   meets the same numerical bound. The original failed prediction remains.
6. Retry the original blocked measurement with exactly the same input and
   shared executable method. Only the selected model and assessment references
   change. The temperature check now passes; physical assumptions remain.
7. Preserve a motivated follow-up question and an alternative explanation.

The exported records contain the data, method hashes, versions, protocols,
observations, assessments, attempts and unresolved items. They can be read
without the originating chat. All records and the input functions were written
within this task; separate source files and an external reader do not establish
independent human authorship or external adoption.

The controlled example is scripted. It does not demonstrate autonomous question
generation, a scientific discovery, real-world preregistration or the value of
an evolutionary population. The input is held fixed across the blocked retry;
the finite test still cannot establish a universal physical model.

## Tool choice and limitations

Pint handles quantities and offset temperature conversion. Python `Decimal`
uses precision 28 and `ROUND_HALF_EVEN`; this is a numerical convention, not a
physical error guarantee. The model's SHA-256 uses this baseline's sorted JSON
convention. It is not the future Slean JCS manifest identity.

The local probe of `rocrate` Python 0.15.1 rejected RO-Crate 1.3 both when
constructing and reading a crate. Its inspected version table stopped at 1.2.
We therefore write a small explicit 1.3 envelope and use JavaScript
`ro-crate@3.7.2` to read it, without an upstream patch. The helper checks payload
digests and the expected scientific fields. Successful reading is not full
RO-Crate 1.3 validation, Slean profile conformance or scientific verification.

The tests reject or qualify wrong units, range, sensor, method bytes, version,
omitted offset, missing applicability, zero gain, negative error bounds,
unsupported uncertainty, changed evaluation rules, incompatible observations,
unrelated contributions and payload alteration. This is a bounded comparison
fixture, not an untrusted-input parser or sandbox.

Base packaging follows the official
[RO-Crate 1.3 metadata specification](https://www.researchobject.org/ro-crate/specification/1.3/metadata.html)
and [root entity requirements](https://www.researchobject.org/ro-crate/specification/1.3/root-data-entity.html).

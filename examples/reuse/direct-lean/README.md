# Direct Lean/Physlib reuse fixture

This is an internal engineering fixture for SR-T01, and the first part of the
direct-tool comparison. It uses ordinary Lean and Physlib, without a Slean
wrapper. It is not the selected scientific research topic for Mutome. The
computational baseline and the cumulative-exploration evaluation are still to
be built.

`DirectReuse.energy_at_two_times` applies Physlib's existing energy-conservation
theorem at two times. Its smoothness and equation-of-motion hypotheses are
explicit. The source proof is imported, not copied or replaced with a metadata
assertion.

## Pinned environment

- Lean: `leanprover/lean4:v4.34.1`.
- Physlib: `44c66d54be78db4693be9f8f92bd3b5ad124ed6f`.
- Mathlib: `d13f23b723b8a846827a245b89c10fc7d3f11612`.
- All transitive revisions: [`lake-manifest.json`](lake-manifest.json).

This package has its own toolchain and lock. The legacy Slean package at the
repository root remains on Lean 4.28.0. Run the commands from this directory.
Use the committed manifest; updating dependencies is a separate change.

## Run

With elan/Lake and Python 3 available:

```sh
cd examples/reuse/direct-lean
elan toolchain install leanprover/lean4:v4.34.1
xargs lake exe cache get < mathlib-cache-roots.txt
bash check.sh
```

Installation needs network access. The optional cache command fetches the
Mathlib dependency closure needed by the selected Physlib source modules.
The roots are recorded for the pinned revision. Passing only the Physlib
module to Mathlib's cache tool omits imports reached through other Physlib
modules; this is why the explicit list is supplied. Missing cache artifacts
affect build time, not the choice of source dependencies.

`check.sh` builds the positive theorem, prints the elaborated interfaces and
transitive axioms, and requires both negative fixtures to fail for the intended
reason. Set `SLEAN_LAKE` to a Lake executable path if it is not on `PATH`.

| Check | Required result |
|---|---|
| Apply the upstream theorem at two times | Lean accepts the new theorem. |
| Inspect upstream and new theorem axioms | Only the reviewed-source policy's `propext`, `Classical.choice`, `Quot.sound` are allowed; each actual set is printed. |
| Omit the equation of motion | Lean leaves that exact hypothesis as an unsolved goal. |
| Change the conclusion to add one unit of energy | Lean rejects the supplied conservation proof with a type mismatch. |

These checks trust the installed toolchain, pinned upstream source and supplied
upstream build cache. They are not isolated verification of hostile code or an
independent recheck of every imported proof. The axiom inspection does not
certify that an observed physical system meets the theorem's assumptions.

## Sources and rights

The theorem is
[`ClassicalMechanics.HarmonicOscillator.energy_conservation_of_equationOfMotion'`](https://github.com/leanprover-community/physlib/blob/44c66d54be78db4693be9f8f92bd3b5ad124ed6f/Physlib/ClassicalMechanics/HarmonicOscillator/Basic.lean).
Physlib and Mathlib retain their upstream Apache-2.0 licences and notices in
their Lake dependency checkouts. No third-party source is vendored here.

The new Slean exporter, portable research profile, separate module consumer,
LeanArchitect integration and usefulness gate remain subsequent tasks.

## Validation on 28 September 2026

`bash check.sh` passed on macOS ARM64 with the environment above. Lake reported
3,258 jobs including cached dependencies. The two inspected declarations both
depend on `propext`, `Classical.choice` and `Quot.sound`, with no further axiom.
Both negative cases were rejected for their intended cause. The emitted types
and axiom reports are saved in [`observed-interface.txt`](observed-interface.txt);
rerunning the check recomputes them from the current local environment.

The final check took **49.48 seconds with installed dependencies and a warm
build**, as measured by `/usr/bin/time -l`. This is not total setup time or a
comparison with Slean. The initial build was interrupted after 69.54 seconds
when the first cache request proved incomplete. Fetching the 26 recorded
Mathlib roots supplied the missing dependency closure. Implementation then
required fixes to the `ContDiff` notation scope, the `ClassicalMechanics`
namespace and an unsupported pretty-printer option; those failed checks took
196.77, 12.98 and 27.67 seconds respectively. A separate diagnostic invocation,
toolchain installation, cache downloads and authoring were not timed together.
All fixtures disable auto-implicit variables so an unknown type name cannot
silently become an additional theorem parameter.

The new toolchain occupies approximately 2.7 GiB and this package's dependency
checkout/build approximately 3.7 GiB in this local environment. They remain
available for the next formal-integration task. This evidence closes SR-T01
only; a fresh-checkout conformance run and the full direct-tool comparison
remain separate acceptance work.

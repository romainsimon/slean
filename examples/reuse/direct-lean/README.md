# Direct Lean/Physlib reuse fixture

This is an internal engineering fixture for SR-T01, and the first part of the
direct-tool comparison. It uses ordinary Lean and Physlib, without a Slean
wrapper. It is not the selected scientific research topic for Mutome. The
computational baseline now lives in [direct-python](../direct-python/README.md).
The cumulative-exploration evaluation remains future work.

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

The new Slean exporter, portable research profile, separate module consumer
and usefulness gate remain subsequent tasks.

## LeanArchitect integration probe

LeanArchitect revision `468e8f58fb4ad6e6ad672a08da6d0d0531e95a97` (tag
`v4.34.0`) also builds with this Lean 4.34.1 environment. A top-level Batteries
pin retains the revision used by Physlib and Mathlib. Run:

```sh
python3 check_architect.py
```

The probe annotates both imported declarations, exports seven nodes through
LeanArchitect's `blueprintJson` facet and compares its presentation graph with
native Lean term dependencies and transitive axioms. The four deliberately
unsupported proof fixtures live only in `ArchitectProbe.lean`; the regular
reuse fixture does not import them. The probe requires their rejection by the
specified axiom policy, even when the presentation readiness flag is true.

[`observed-architect.json`](observed-architect.json) records the passed probe.
The [integration decision](../../../docs/research/slean-formal-integration-2026-09-28.md)
defines what Slean can reuse and what its formal profile must still check.

## Validation on 28 September 2026

The additional calibration algebra check is available with:

```sh
python3 check_calibration.py
```

It checks the affine inverse and its conditional residual error bound. Both
theorems use only the same three allowed axioms. Omitting the nonzero gain or
the residual-bound hypothesis leaves the intended unsolved goal. The
[recorded report](observed-calibration.json) includes the native statements.
They concern real-valued magnitudes; they do not establish that a physical
sensor follows the model or that fitted parameters are exact.

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

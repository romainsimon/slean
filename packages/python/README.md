# Python authoring and reading (in development)

This package currently implements the quantity portion of SR-T07. Method,
application and evidence authoring, package installation and the full reader
API remain unfinished. Do not treat this checkpoint as a delivered SDK or
usefulness result.

`slean.quantities.scalar` declares a scalar with its dimension, unit, decimal
string (or missing value) and explicit uncertainty. Authoring preserves decimal
spelling. `convert_scalar` returns a new scalar using the pinned Pint 0.26.1
definitions; it preserves the uncertainty with its own explicit unit.
`scalar_port` and `check_scalar` check dimensional interface compatibility.
They do not establish model applicability or empirical validity.

The bundled map must match [the canonical mapping](../../profiles/quantity-map.json).
Only units listed in that map are accepted. A base-unit name in a mapping row
does not automatically authorize an additional wire unit. Conversions check
Pint's interpretation against the explicit scale/offset mapping. A different
Pint version or definitions return `unsupported`.

Missing is distinct from zero. Allowed missing values remain `unresolved`;
incompatible dimensions are `violated`. Unknown units or statistical-interval
semantics are `unsupported`. An absolute Celsius value can be converted to
Kelvin, but an error bound expressed in an offset unit is unsupported: applying
the temperature's offset to an error magnitude would be incorrect. A bound in
a supported zero-offset unit keeps its stated interpretation.

Run the current tests from the repository root using the already pinned
direct-baseline environment:

```sh
examples/reuse/direct-python/.venv/bin/python -m unittest discover -s packages/python/tests
```

The tests exercise all mapped units, scale and offset conversions, decimals
longer than Python's default arithmetic context, missing values, uncertainty,
dimension errors, unsupported semantics and unit-definition version drift.
No candidate method code is imported or executed by this quantity API.

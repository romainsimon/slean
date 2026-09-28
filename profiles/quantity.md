# Quantity profile: slean-quantity/0.1-draft.1

The first profile covers the frozen sensor example. Quantities are scalar
values or CSV tables of named scalar columns. Broader dimensional algebra,
statistical intervals and general array/tensor contracts require new profile
support. They must return `unsupported` when used, not silently become numbers.

A scalar value has `kind: "scalar"`, `dimension`, `unit`, `value` and
`uncertainty`. `value` is a finite decimal string, or `null` for missing.
Decimal strings use `^-?(0|[1-9][0-9]*)(\.[0-9]+)?$`; their original spelling
remains part of module identity. Arithmetic may compare equal values without
rewriting the module. Unknown is distinct from zero.

Uncertainty is either `{ "kind": "unknown" }` or
`{ "kind": "absolute_bound", "value": "0.02", "unit": "volt" }`.
A bound is nonnegative and has the same dimension as the scalar. It is a
declared bound under assumptions, not a confidence interval. Parameter
uncertainty stays explicit; an estimated gain cannot silently become an exact
physical constant because its decimal representation is exact.
An unfamiliar uncertainty kind is preserved as data and reported as
unsupported. It cannot be treated as an absolute bound or an unknown value
with permission to proceed.

An interface has `inputs` and `outputs`, maps of names to port descriptors.
Its optional `parameters` map contains the model's named scalar parameters
and their uncertainty. An optional `entrypoint` identifies an executable
payload and qualified Python symbol; inspection never imports or calls it.
Methods without an entrypoint remain representable research proposals. An
execution request for them returns `unsupported`.
A descriptor is a scalar's dimension/unit plus `allow_missing`, a text port,
or a `table` with scalar columns and `format: "csv"`. A table value references
its payload and the same column descriptors; the profile checks its header,
row shapes, decimals and missing values before reporting input compatibility.
The initial profile does not run arbitrary parsing code from a module.

## Explicit mapping

[`quantity-map.json`](quantity-map.json) fixes Pint 0.26.1, its unit-definition
hashes and the small supported unit map. Dimensions use ISQ exponents in the
order length, mass, time, current, temperature, amount, luminous intensity.
The Physlib representation is `Dimension ISQDimensionBase` at the pinned
revision, using `Dimension.ofFunction` for that tuple.

Physlib's default five-dimensional LTMCT basis uses charge, not current. An
adapter must use its explicit `Dimension.toISQHom` bridge when that basis is
encountered; it cannot compare the tuples position by position. The initial
profile does not project away amount or luminous intensity. Conversion of
absolute Celsius uses its offset; a temperature difference needs separate
semantics and is unsupported in this first table.

Pint interprets the mapped units. The mapping never invokes `eval` or accepts
arbitrary Lean/Python expressions. A runtime records its Decimal or floating
representation, precision and tolerance separately from the wire decimal.

## Supported leaf predicates

The `quantity`, `range` and `equals` predicates name a key with `field` and `location`
(`bindings` or `context`). Missing values yield `unresolved` when allowed;
an explicit incompatible value yields `violated`.

| Predicate | Additional arguments | Meaning |
|---|---|---|
| `quantity` | `dimension`, `unit`, `allow_missing` | Check a scalar, dimension and supported conversion. |
| `range` | `minimum`, `maximum` scalar values | Inclusive comparison after the declared conversion. |
| `equals` | `expected` binding | Compare the literal, exact reference or converted scalar. No semantic similarity. |
| `applicability` | `claim` reference | Preserve an empirical/model assumption unless an appropriate deterministic check can establish this precise limited claim. An attributed citation alone stays unresolved. |

`applicability` binds that exact claim to the application's whole context;
it has no `field` or `location` argument. Its witness must match both.

Interface port checks are mandatory in addition to this tree. They cannot be
weakened by an application-specific requirement list. An unknown unit or
unsupported uncertainty kind is unsupported; a known wrong dimension is
violated. Alternative branches do not suppress diagnostic details.

Computational evidence reports `status` (`reproduced`, `different`, `unsupported`),
`numeric_representation` and `tolerance`. It remains an imported declaration
until the receiver repeats the exact supported computation. The underlying
method, inputs and outputs are application bindings and payload references.

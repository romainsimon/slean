# Lean profile: slean-lean/0.1-draft.1

This profile describes ordinary native Lean declarations. It introduces no
scientific expression language or cross-prover identity. The initial environment
is Lean 4.34.1. Other Lean versions require an explicit encoding/compatibility
decision, not a guess based on displayed text.

A component interface records `declaration`, `module`, `source`, `toolchain`,
`lock`, and `statement`. Source and lock are payload references. The statement
records `encoding`, `artifact` and `fingerprint`. The named encoding below is
the JCS content of the native elaborated expression, independent of pretty
printing. The payload digest additionally binds the actual serialized bytes.

## Native encoding: lean-expr/0.1-draft.1

Names are arrays of `["str", string]` or `["num", natural_string]` components;
the anonymous name is `[]`. Strings containing dots remain one string component.
This distinguishes native numeric components from strings that look numeric.
Levels are `["zero"]`, `["succ", level]`, `["max", left, right]`,
`["imax", left, right]`, or `["param", name]`. Reject level metavariables.

Expressions follow Lean's native constructors:

```text
["bvar", natural_string]
["sort", level]
["const", name, levels]
["app", function, argument]
["lam", name, type, body, binder_info]
["forallE", name, type, body, binder_info]
["letE", name, type, value, body, nondep_boolean]
["natLit", natural_string]
["strLit", string]
["proj", type_name, natural_string, structure]
```

Binder information is `default`, `implicit`, `strictImplicit` or `instImplicit`.
Reject free variables, expression metavariables and loose bound variables in a
closed declaration type. Erase only `mdata`: Lean defines it as definitionally
equal to its contained expression. Keep binder names, universe names and all
remaining structure. No other normalization is part of this encoding.

The artifact has `encoding: "lean-expr/0.1-draft.1"`, `universe_parameters`
(native names in declaration order) and `expression`. Universe parameter names
must be unique; every level parameter in the expression must be declared.
Its fingerprint is SHA-256 of the UTF-8 prefix `lean-expr/0.1-draft.1\n` followed
by JCS of that artifact. Fingerprint equality is an encoding identity in a
pinned environment, not a complete test of mathematical equivalence.

## Evidence and application

The `proposition` leaf names an exact claim reference and optional expected
statement fingerprint. Only matching locally checked formal evidence can
satisfy it. The receiver must check the subject, context, statement,
environment and policy. Imported result fields do not provide that witness.

A formal result records `status` (`passed`, `failed`, `unsupported`), `policy`,
`statement_fingerprint`, `statement_dependencies`, `proof_dependencies` and
`axioms`. Dependency names use the encoding above. Preserve each proof's set
separately, including overlap with statement dependencies. These are actual
recorded proof dependencies, not claims about all possible derivations.

`reviewed-source/0.1-draft.1` permits only `propext`, `Classical.choice` and
`Quot.sound`; report the actual set. It trusts the declared installed toolchain
and reviewed source/build inputs. A receipt must bind the exact module,
component/application, statement, dependency environment and artifacts.
Missing source/dependencies, `sorryAx`, new axioms or changed statements prevent
a passing result. The unreviewed-contribution policy stays unsupported until
the isolated execution and separately trusted statement path are implemented.

The adapter reuses LeanArchitect for annotations and blueprint artifacts.
Overrides of displayed edges and local presentation readiness cannot replace
the native audit. Native formal applications remain ordinary Lean code.

Encoding choices follow the pinned
[Lean Expr definition](https://github.com/leanprover/lean4/blob/v4.34.1/src/Lean/Expr.lean)
and [Level definition](https://github.com/leanprover/lean4/blob/v4.34.1/src/Lean/Level.lean).

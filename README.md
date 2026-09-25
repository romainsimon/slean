<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="site/assets/brand/slean-white.svg">
    <source media="(prefers-color-scheme: light)" srcset="site/assets/brand/slean-dark.svg">
    <img src="site/assets/brand/slean-dark.svg" alt="Slean" width="148">
  </picture>
</h1>

<p align="center">
  Make every research decision traceable.
</p>

<p align="center">
  <img src="assets/slean-readme-banner.png" alt="A research record flowing from branching evidence through proof-like marks to a checked result." width="100%">
</p>

> **Status:** Early, local V0 research prototype. The repository is private; no public license or contribution guide is available.

A structured decision record brings together observations, assumptions, rules, and conclusions. Slean checks that the record is consistent—including references, event order, units, and exact thresholds—and replays it so readers can see which recorded inputs led to each conclusion. It checks traceability and consistency; it does not establish whether measurements or external scientific claims are true.

## What it checks

- IDs, references, event order, causal timing, units, exact-decimal threshold rules, and recorded cost caps.
- Journal prefixes and audience-filtered JSON exports, so a reader can inspect only the records visible to that audience.
- Source-trace links between manifests, protocols, events, and recorded outcomes. Imported external assessments remain `external_unverified` unless Slean itself can compute the narrow local rule.

## A small example

The synthetic case in [`examples/valid.json`](examples/valid.json) freezes a `>= 0.001` rule, records a measurement of `0.002` and a cost of `2.50 cpu_s` under a `10.00 cpu_s` cap, then records `pass` and `promote`.

```sh
lake exe slean validate examples/valid.json
```

```json
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

These values are synthetic. A local `pass` means the encoded rule passed for its cited record; it is not evidence that a real-world claim is true.

## Quickstart

Install Lean using the [official setup guide](https://lean-lang.org/install/). The [`lean-toolchain`](lean-toolchain) file pins Lean 4.28.0, which `elan` selects for this project.

With access to this private repository, clone it and run the validator from the repository root:

```sh
git clone https://github.com/romainsimon/slean.git
cd slean
lake build
lake exe slean validate examples/valid.json
```

Run the local build and test checks with:

```sh
bash tests/check.sh
```

## Maturity and limits

This is a local research prototype, not a general scientific evaluator or released software package. The [Gate V retest](docs/gate-v-retest.md) supports continuing a bounded structural prototype; representative reviewer value remains unmeasured. Slean does not execute experiments, recompute an external multi-observation assessment, or certify measurements, evaluators, human decisions, or scientific claims.

## Further reading

- [Product scope](PRODUCT.md)
- [Architecture and trust boundary](ARCHITECTURE.md)
- [Versioned schemas](schema/README.md)
- [Verso manual and local build](site/README.md)
- [Local Explorer prototype](explorer/README.md)
- [Gate V retest and evidence limits](docs/gate-v-retest.md)

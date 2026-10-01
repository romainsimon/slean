<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/slean-white.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/brand/slean-dark.svg">
    <img src="assets/brand/slean-dark.svg" alt="Slean" width="148">
  </picture>
</h1>

<p align="center">
  Verifiable worlds, a kernel-checked library, and a way to measure whether an AI actually discovers anything.
</p>

> **Status:** research engine, version 0.2. Private repository. One world class (cellular automata) and one discovery type (conservation laws). This is the foundation that [Mutome](https://mutome.com) will run on. It is not yet a discovery claim.

## Why

AI is moving mathematics forward largely because of [Lean](https://lean-lang.org): a model can attempt thousands of proofs, and the kernel accepts only correct ones. Every accepted result becomes a brick that later work can build on, and the list of open statements shows where the frontier is.

Science has no such kernel. A plausible paragraph and a true law look the same until someone checks. Slean builds the equivalent piece by piece:

1. **Worlds** whose laws are defined exactly in Lean. Agents explore them by simulation. A finding cannot come from a simulator bug, because the Lean definition *is* the world.
2. **Claims with certificates.** A discovery is accepted only when it comes with a finite certificate that the Lean kernel checks. Refutations come with a concrete counterexample, also kernel-checked.
3. **A library** of everything accepted or refuted, kept as Lean theorems. It is the memory that later research reuses.
4. **Measurement.** Discovery is scored on procedurally generated worlds with a hidden answer that no model has seen. It is compared with simple baselines at equal cost, and with and without the library.

Mutome decides what to explore. Slean says what is true, keeps it, and measures whether the exploring helped.

## What works today

**A theorem that turns a local certificate into a global law.** [`Slean/World/CellularAutomaton.lean`](Slean/World/CellularAutomaton.lean) proves `conserved_of_fluxCheck`. If a density `ρ` and a current `J` satisfy the discrete continuity equation `ρ(step x)ᵢ − ρ(x)ᵢ = Jᵢ − Jᵢ₊₁` on every local pattern, then the total of `ρ` is conserved for **every** lattice size and configuration. That local check is finite, so `decide` settles it in the kernel. Only the standard axioms are used.

**A kernel-checked library.** [`Slean/Library/ElementaryConservation.lean`](Slean/Library/ElementaryConservation.lean) contains all 84 conservation laws of width ≤ 3 of the 256 elementary cellular automata, up to trivial ones, across 66 rules. Each law is proved for all lattice sizes. `lake build` re-checks all of them in about 20 seconds.

**A discovery loop and a benchmark.** [`engine/`](engine/) is plain Python with no dependencies:

```
propose (explorer) → verify (counterexample search or flux certificate) → record (library) → Lean kernel
```

It has five explorers: `random`, `datafit` (exact regression on simulated data), `library` (data fitting plus reuse of laws across structurally related worlds), `oracle` (knows the theory), and `llm` (a language model reading the rules and the feedback).

## First measurements and what they mean

These are hidden worlds: 32 generated 3- and 4-state automata with 40 planted laws disguised by secret relabellings, plus distractors. Details are in [docs/results/2026-10-01-conservation.md](docs/results/2026-10-01-conservation.md).

| Explorer | Hidden laws found (held-out half) | Proposals |
|---|---|---|
| random | 3/20 at 40, 7/20 at 300 | 40 / 300 |
| datafit | **20/20** | 24 |
| library (warm) | 20/20 | 20 |

**Conservation laws of 1D automata are a solved class.** A generic method (exact linear algebra on simulated data) finds every hidden law with about one proposal per law. This class therefore validates the machinery (worlds, verifier, Lean, library, benchmark), but it **cannot** show that a system discovers. That requires discovery types with no known recipe, and metered access to the world. They are next on the roadmap.

## Quick start

Requires [Lean via elan](https://lean-lang.org/install/) and Python ≥ 3.11.

```sh
lake build                                          # kernel-checks the core and the library
cd engine
python3 -m unittest discover -s tests               # engine + Lean agreement tests
python3 -m slean check 184 1 0,1                    # is the number of cars conserved by rule 184?
python3 -m slean explore --explorer datafit --lean  # explore hidden worlds, kernel-check results
python3 -m slean transfer --explorer library        # cold vs library-warm discovery
```

## Read next

- [Vision and roadmap](docs/VISION.md): from calibration worlds to physics, engineering and biology, and how Mutome uses Slean
- [How we measure discovery](docs/MEASUREMENT.md): the rules that keep the benchmark honest
- [Results](docs/results/): dated measurements, including negative ones

The previous dossier validator and open-standard work are archived under the git tags `archive/dossier-v0` and `archive/open-standard-pr35`.

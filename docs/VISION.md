# Vision and roadmap

## The goal

Mutome is meant to be an autonomous research lab that runs continuously, chooses what to explore, and finds things that matter: in real-world physics first, then in engineering, biology and other fields. Every result should become a brick that makes the next discovery possible, including results whose use only shows up much later.

Three problems stand in the way, and Slean exists to solve them:

| Problem | Without it | What Slean provides |
|---|---|---|
| **Truth** | An agent can produce thousands of plausible claims, and nobody can check them at that rate. | Claims with certificates that the Lean kernel checks automatically. |
| **Accumulation** | Results sit in reports and chats, get re-derived or forgotten, and errors propagate. | A library of checked bricks (Lean theorems plus data) that later work imports. |
| **Measurement** | "The agent seems clever" is unfalsifiable, and rediscovering known laws can be memorisation. | Unseen worlds with hidden answers, equal-cost baselines, cold/warm protocols. |

This is what made Lean useful for AI in mathematics: an automatic verifier, a cumulative library, and an explicit frontier. Slean builds the same three things for domains where the laws must be discovered, not just proved.

## Architecture

```
            Mutome (strategy, agents, budget, continuous operation)
                 │ proposes claims          ▲ verdicts, library, scores
                 ▼                          │
 ┌──────────────────────────── Slean ─────────────────────────────┐
 │ Worlds      exact definitions in Lean + fast simulators       │
 │ Verifier    counterexample search, certificates               │
 │ Kernel      Lean checks every certificate and refutation      │
 │ Library     Lean modules + data: what is known, refuted, open │
 │ Bench       hidden-answer suites, baselines, cold/warm        │
 └────────────────────────────────────────────────────────────────┘
```

Each world declares four things:

- its exact rules (in Lean);
- the claim types it supports;
- a certificate format for each claim type;
- when possible, a generator of disguised instances with a computable hidden answer.

The engine stays the same across worlds. Explorers (random, data fitting, language models, Mutome's evolutionary populations) all use the same interface and pay the same costs.

## Kinds of evidence

Slean keeps these apart and never merges them into one score:

1. **Proved in the model.** A Lean theorem about a world's exact definition. True for that world, unconditionally.
2. **Checked computation.** A finite fact the kernel evaluated, such as a counterexample or a periodic orbit.
3. **Supported by simulation.** No counterexample was found in a stated search. A conjecture, kept as an open brick.
4. **Confirmed on the real world.** A prediction registered before the data, evaluated by a frozen rule. This is the only kind that says anything about nature.

Physics is reached by making the gap between 1 and 4 explicit, never by blurring it.

## Roadmap

Every milestone ends with a measurement. When an explorer fails to beat the generic baselines, the design changes. We do not add interface, scope or vocabulary to compensate.

### M1: Foundation (done, 2026-10-01)

- Cellular-automaton worlds in Lean, and the flux theorem: a local certificate proves conservation for all lattice sizes.
- A kernel-checked library of all 84 conservation laws of width ≤ 3 of the elementary automata.
- A Python engine with verifier, library, explorers and the cold/warm benchmark.
- **Finding:** additive conservation laws in 1D are solved by data fitting (20/20 hidden laws in 24 proposals). The class calibrates the machinery but cannot demonstrate discovery.

### M2: Discovery types without a recipe (in progress)

- **Done:** metered labs. Any agent works through `./lab` (experiments, checks, proposals). Cell updates, proposals, tokens and cost are counted; hidden answers stay outside the lab; transcripts are audited; results are exported to Lean.
- **Done:** localised structures (particles, gliders, oscillators) as a second discovery type, with kernel-checked witnesses and refutations.
- **Done:** a scripted reference scientist that uses exactly the agent's interface and budget.
- **Reversibility.** An inverse-rule certificate when the rule is reversible, a collision when it is not.
- **Isomorphisms as bricks.** "World B is world A relabelled" plus a Lean transport theorem, so one discovered relation proves every law of A again for B. This is the first real dependency between bricks.
- **Open-ended allocation.** The explorer chooses the world, the claim type and the effort. Delayed usefulness is scored by how many later results depend on a brick.
- **LLM and evolutionary explorers** measured over several suite seeds against `datafit` and brute force at equal metered cost.
- **Open claim types.** The agent defines its own decidable properties in Lean and submits them. Their interest is judged by later use (Germinal), because in an open-ended setting the explorer chooses the question and not only the answer. This is where systematic search stops being enough.

### M3: Mutome runs on Slean

- Mutome's continuous runner calls the engine (`python -m slean …`, JSON in and out) and writes to a growing library.
- The library becomes Mutome's memory, which replaces the free-text memory store for these domains.
- mutome.com shows the live library: bricks, refutations, open conjectures, and the dependency graph in the Slean Explorer (2D/3D).

### M4: Physics worlds

- Lattice and Hamiltonian systems defined in Lean, reusing [Physlib](https://physlib.io) definitions where they exist, found through [physlibsearch](https://physlibsearch.net).
- Exactly conserved quantities of discrete integrators, symmetries, stability statements.
- The loop: simulate, conjecture, prove, or refute with a checked counterexample.
- Wolfram-style exploration of rule spaces: we take its method (enumerate simple rules, look for emergent structure), not its unverified claims.

### M5: The real world

Engineering, biology and physics data, with **prospective** verification: Mutome registers a prediction and its evaluation rule before the deciding data exists, and Slean evaluates it with a frozen evaluator. Retrospective benchmarks (for example held-out ProteinGym assays) are allowed only with frozen splits and no repeated holdout scoring.

## Non-goals

- A new formal language. Lean is the language.
- A metadata or provenance standard. Provenance is recorded, but it is not the product.
- A hosted service or a public interface ahead of evidence that the engine discovers.
- Duplicating Physlib, Mathlib or simulation codes. We reuse them.

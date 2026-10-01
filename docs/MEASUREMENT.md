# How we measure discovery

The question is not "does the agent look like a scientist?". It is "did it find something true that it did not already know, more cheaply than a simple method would have?". Each rule below closes a way of fooling ourselves.

## Rules

1. **Truth is decided by a kernel, never by the explorer.** A finding counts only with a certificate the Lean kernel accepts. Refutations need a concrete counterexample. Model confidence, citations and fluent explanations count for nothing.

2. **Worlds nobody has seen.** Known results (the elementary automata, textbook physics) are calibration only, because a model may have memorised them. Scored worlds are generated from a seed and disguised: hidden relabelling of states, reflections, distractor worlds without any law.

3. **A hidden answer.** For each scored world we compute the complete answer exactly (for conservation laws: the null space of the continuity equations). Recall is measured against it, so silence and false leads both show up.

4. **Nothing trivial counts.** A result counts once, and only if it is new modulo what is already known. Constants and discrete gradients are conserved by every rule, so they are excluded. Discoveries are counted as the rank they add to the known space, not as the number of claims.

5. **Equal cost, including the boring baselines.** Every explorer pays one unit per proposal sent to the verifier. The comparison always includes `random` (the floor), a generic computational method (`datafit`) and the theory-aware `oracle` (the ceiling). An AI explorer that does not beat `datafit` at equal cost has not shown discovery ability. It has shown it can do what fifty lines of linear algebra do.

6. **Metered access to the world (next).** Proposals are not the only cost. Simulation is the experiment. Without metering, brute-force search looks free and wins every benchmark. Version 0.3 counts cell updates and model tokens next to proposals.

7. **Cumulative value is measured, not assumed.** The `transfer` protocol scores the held-out half of each world family twice at the same budget: cold, and warm with the library built on the seen half. Memory is only "useful" when the warm run beats the cold one.

8. **Negative results are published.** Every run writes its verdicts, including refutations and invalid proposals, to `runs/` and to a Lean module that the kernel re-checks. Dated summaries live in [`results/`](results/), including results that go against us.

## What a positive result has to look like

"Mutome can discover" will mean all of the following, on worlds generated after the system was frozen:

- recall above `datafit` and `random` at equal metered cost, with every finding kernel-checked;
- a warm-start gain on held-out worlds (earlier results make later ones cheaper);
- the same result over several suite seeds, with the spread reported.

Real-world domains (physics, engineering, biology) cannot provide a complete hidden answer. There the score becomes *prospective*: predictions registered before the data that settles them exists, with the evaluation rule fixed in advance. See [VISION.md](VISION.md).

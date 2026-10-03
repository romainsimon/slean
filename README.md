<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/slean-logo-dark.svg">
    <img src="assets/brand/slean-logo.svg" alt="Slean" width="240">
  </picture>
</p>

<p align="center">
  <strong>Exact worlds, kernel-checked discoveries, and an honest way to measure whether an AI discovers anything.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache%202.0-1f6feb"></a>
  <img alt="Lean 4" src="https://img.shields.io/badge/Lean-4-6e40c9">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-3776ab">
  <a href="https://slean.org"><img alt="slean.org" src="https://img.shields.io/badge/site-slean.org-00895f"></a>
</p>

<p align="center">
  <a href="https://slean.org">Website</a> ·
  <a href="https://slean.org/learn">Learn by playing</a> ·
  <a href="docs/VISION.md">Vision</a> ·
  <a href="docs/MEASUREMENT.md">Measurement rules</a> ·
  <a href="docs/results/">Results</a>
</p>

---

An AI can propose a thousand discoveries in an hour. In mathematics there is a referee for them: the [Lean](https://lean-lang.org) kernel accepts a proof only if it is correct. Science has no such referee, so a plausible paragraph and a true law look the same until someone checks.

**Slean** (Science + Lean) builds that referee, starting with small worlds whose laws are defined exactly in Lean. An agent explores them by experiment. A discovery counts only when it comes with a certificate that is checked exactly, and every accepted result joins a library that later work builds on. Labs with hidden answers then measure whether an agent, or a change to how it works, actually finds more.

Slean is the verification and measurement layer of [Mutome](https://mutome.com), an autonomous research lab in progress.

## How it works

```
 agent ──experiment──▶ world (exact, defined in Lean)
   │
   └──claim──▶ verifier ──▶ certified (+ Lean theorem) or refuted (+ counterexample)
                                │
                                ▼
                     library of verified results ──▶ scored against the hidden answer
```

Today's worlds are one-dimensional cellular automata: cells on a ring that all update at once by a fixed local rule. They are small enough to check exactly, and rich enough to hide laws, particles and compressed rules.

| Discovery | Example | How it is checked |
|---|---|---|
| **Conservation law** | "the number of cars is conserved" | Lean kernel: a finite flux certificate proves it for every lattice size |
| **Localised structure** | a glider of period 4 moving right | Lean kernel: the block reappears, shifted, after exactly `t` steps |
| **Compact law** | "the rule is the sum of the cells, mod 4, through this small table" | Lean kernel: the short formula equals the rule on every neighbourhood |
| **Mechanism** | the world's whole rule table | Exact comparison with the hidden rule, entry by entry (no Lean statement) |

A wrong claim comes back with a counterexample, which is checked too. Nothing false is ever accepted.

## What we have measured

Every measurement is on generated worlds no model has seen, scored against a hidden answer, and published with its negative results. All data and reports are in [`docs/results/`](docs/results/).

1. **Conservation laws alone are a solved class.** Exact data fitting finds 20 of 20 hidden laws in 24 proposals. This calibrates the machinery but cannot show discovery. [Report](docs/results/2026-10-01-conservation.md)
2. **On easy worlds, a Claude Sonnet agent matches a scripted scientist with 150 to 225 times fewer experiments**, and makes no false claim. But one well-chosen experiment reveals each of those rules. [Report](docs/results/2026-10-01-labs.md)
3. **On compressible worlds, lessons help.** These are 1,024-entry rules that hide a short law, under a tight budget. The agent's own lessons from earlier labs win 8 of 9 repeated pairs, by 6 discoveries per lab on average. They also help it find compact laws: 8, 12 and 8 of 12, against 2, 6 and 5 without. [Report](docs/results/2026-10-02-compressible-lift.md)
4. **A family-aware script draws level.** A scripted reference that tries the textbook rule families (linear, totalistic) scores 47 to 54 with 9 laws per lab, as well as the agent with lessons. [Report](docs/results/2026-10-03-inductive-reference.md)
5. **Novel worlds remove that shortcut.** Their laws come from other families, and the same script finds 0 of 12. These worlds can tell induction apart from recall. [Report](docs/results/2026-10-03-novel-suite.md)

What this does not show: a discovery about the real world, or a lab that improves itself. These are measurements on synthetic worlds, built to be checked exactly.

## Quick start

Requires [Lean 4 via elan](https://lean-lang.org/install/) and Python 3.11 or later. The Python engine has no dependencies.

```sh
git clone https://github.com/romainsimon/slean && cd slean
lake build                                     # kernel-checks the core and the library of laws

cd engine
python3 -m unittest discover -s tests          # engine tests, including Lean agreement
python3 -m slean check 184 1 0,1               # does rule 184 conserve the number of cars? (yes)
python3 -m slean explore --explorer datafit --lean   # explore hidden worlds, kernel-check the results
```

## Measure an agent

A lab is a directory with a task description and a `./lab` command. An agent (Claude Code, Codex, a Mutome worker or a person) runs experiments and submits claims only through that command. Every experiment and proposal is metered, and the run is scored against the hidden answer afterwards.

```sh
cd engine
python3 -m slean lab init --dir /tmp/lab --suite novel --suite-seed secret \
  --mode blackbox --proposals 200 --cells 4000
python3 -m slean lab run --dir /tmp/lab --agent claude --model sonnet --max-usd 4
python3 -m slean lab score --dir /tmp/lab
```

- **Isolated.** While the agent runs, `./lab` talks to a broker in the parent process. The agent runs under the OS sandbox (`sandbox-exec` on macOS, `bwrap` on Linux), so it can read neither the hidden answers nor the engine, and cannot rewrite its own budget. The score records which isolation was used.
- **Secret seeds.** The generators are public, so a known seed would reveal the answers. `--suite-seed secret` draws one that only the secret directory records.
- **A reference to beat.** `lab baseline` runs the scripted reference scientist, with the same interface and budget, in a lab of its own.

## Repository

| Path | What it holds |
|---|---|
| [`Slean/`](Slean/) | Lean definitions and theorems: worlds, structures, compact laws, packed tables |
| [`Slean/Library/`](Slean/Library/) | The kernel-checked library: all 84 conservation laws of width ≤ 3 of the 256 elementary automata |
| [`engine/`](engine/) | The Python engine: worlds, verifier, explorers, labs, isolation, Lean export |
| [`library/`](library/) | The library as data, reproducible from the engine |
| [`docs/`](docs/) | [Vision and roadmap](docs/VISION.md), [measurement rules](docs/MEASUREMENT.md), [dated results](docs/results/) |

## Status

Research engine, version 0.2. It has one world class (cellular automata) and four discovery types. Next on the [roadmap](docs/VISION.md):

- agents on novel worlds with secret seeds;
- relations between worlds as reusable bricks;
- claim types the agent defines itself;
- worlds closer to physics.

Issues and discussion are welcome.

## License

[Apache License 2.0](LICENSE). The Slean name and logo identify this project; please do not use them to suggest endorsement.

# Product scope

Slean helps a research author answer: which frozen protocol, recorded observation, cost, and decision supported a claim at a given journal prefix? The first user is an experiment owner reviewing a development decision. The author can build a case in Lean or import JSON through the CLI.

The local V0 prototype validates IDs, causal references, units, a single exact threshold rule, known cost caps, and append-only event order. Its 0.2 source-trace boundary additionally checks cross-file provenance and all observation references while keeping the external assessment unverified. Version 0.3 records explicit AND/OR dependency groups without evaluating their truth. It can project an agent view before deriving observation, relation and gate data. A conditional Lean theorem has a separate formal receipt. The theorem does not certify the measurement, evaluator, human decision, or world.

The intended boundary is JSON and CLI. Mutome, GERMINAL, and autoresearch own their source logs, evaluators, secret data, campaign control, and scientific scores. Slean does not execute experiments, reserve resources, alter those systems, or publish results.

The [gate V retest](docs/gate-v-retest.md) found one cross-file check that the source verifier does not perform and no omitted source JSON fields. It permits a bounded documentation prototype. The [first V result](docs/gate-v.md) remains the historical negative baseline. A site or Explorer must still prove its own utility and does not turn the external assessment into an empirical proof.

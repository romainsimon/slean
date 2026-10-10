# Measuring the Codex agent

`--agent codex --profile codex-isolated-1` uses the existing ChatGPT subscription. It refuses API-key-only authentication and refuses to run without `sandbox-exec` (macOS) or `bwrap` (Linux).

The profile takes only the selected model and reasoning effort from the operator configuration. Both may be pinned explicitly with `--model` and `--reasoning-effort`. The score records their resolved values, the CLI version, controlled configuration and its SHA-256 fingerprint. Measurements must pin this record before efficacy runs.

Each lab uses a fresh, temporary `CODEX_HOME` containing subscription authentication and an empty private `HOME`. User configuration, rules, project documents, MCP connections, plugins, memories, web tools, hooks and other agents are disabled. The shared Codex daemon is disabled. Codex applies its native named permission profile to tool children; those children cannot read the runtime authentication directory or the operator home. The model client alone can authenticate. A deterministic canary probe verifies credential/home/shared-tmp denial, read-only state, lab writes and broker access before any model request. The temporary home is retained for continuation, then removed, and is never part of result exports. Nothing in the operator's Claude configuration is modified.

The same broker protects lab state and hidden answers, with equivalent deny/confine/own/hide restrictions in the [Codex native filesystem profile](https://learn.chatgpt.com/docs/permissions). macOS cannot nest its Seatbelt sandbox, so this profile replaces the outer launcher sandbox for Codex. Shared temporary files, other lab directories, operator sessions and checkouts are hidden; only the lab and its broker remain reachable to tools; the temporary runtime remains reachable to the model client. Codex tool children cannot read or write shared `/tmp`; the lab-local `tmp` remains writable. The separate Slean outer sandbox uses a writable private tmpfs on Linux and was independently tested there.

## Accounting and audit

The JSON event audit records unique tool items and tool types. Network commands, outside-lab absolute paths, home/parent traversals, protected-state access and unexpected tools are flagged. Outputs containing URLs are not themselves network use. Missing or failed JSON turns are failures. This is a conservative transcript audit, not an adversarial guarantee about arbitrary shell or Python code; the native operating-system sandbox enforces the protected-path boundary. Network remains available to the client and tool children so the existing Unix broker works, as in the Claude profile. All non-broker network use is audit-invalid. This is not a network firewall; native network-off also blocked the broker during infrastructure validation.

`score.agent.usage` records input, cached-input, cache-write, output and reasoning-output tokens. Codex reports session-cumulative totals: the latest total per session is used, so resuming does not double-count earlier usage. `turns` means completed user turns, including continuation, not Claude's internal turn count. `cost_usd` is null: subscription tokens are not a dollar-cost estimate. The caller enforces a wall-time limit; Claude's `--max-usd` flag does not impose a subscription budget.

With `--continue-once`, a successful session with at least 25% of proposals remaining is resumed by its exact session ID using `codex exec resume`. It receives the same neutral budget reminder as Claude. All usage and continuation attempts remain recorded.

## Infrastructure validation

Unit tests cover profile selection, subscription-only authentication, isolated runtime cleanup, JSON tool auditing, cumulative usage and resume command construction. The OS isolation tests exercise hidden answers, read-only state, sibling labs, own paths, hidden checkouts and private temporary files on macOS and Linux.

A deliberately adversarial canary probe is infrastructure validation, excluded from scientific effect estimates. Its attempted forbidden reads must be blocked by the OS and flagged by the audit; an intentionally flagged probe is not a clean discovery lab.

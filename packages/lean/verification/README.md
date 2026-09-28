# Local Lean proof comparison

This is an SR-T06 implementation checkpoint. It integrates the upstream
[Comparator](https://github.com/leanprover/comparator/tree/d03acab154d269c06e60e4de7e4cc85deebff94b)
with a restricted macOS execution adapter. It compares a candidate proof with
a separately supplied, trusted statement and replays the exported proof in
Lean's kernel. It does **not** issue Slean verification receipts. Both complete
Slean verification policies remain unsupported.

The [Lean validation guide](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)
explains why successful compilation alone is insufficient for an unreviewed
contribution. The adapter reuses the upstream comparison and checking code.
It does not introduce a new proof kernel.

## Setup and use

This package pins Lean 4.34.1 independently of the repository's V0 toolchain.
Its manifest pins Comparator at `d03acab154d269c06e60e4de7e4cc85deebff94b`
and lean4export at `076e8e57707e813375e8f9da8bf989799ace9680`.
From this directory, install and build the receiver's tools:

```sh
lake update
lake build
```

This explicit setup can access the network. Review these tools and their
source revisions before running contributions. The comparison operation has
no dependency installation step. It requires macOS, `/usr/bin/sandbox-exec`,
a non-root user and the installed pinned toolchain.

From the repository root, run the reviewed, self-contained example:

```sh
conformance/.venv/bin/python packages/lean/verification/run_comparator.py \
  --challenge packages/lean/verification/tests/Challenge.lean \
  --solution packages/lean/verification/tests/Solution.lean \
  --theorem reusable_identity
```

The receiver must select the challenge and theorem independently of the
candidate. The challenge's `sorry` is a statement placeholder; the candidate
cannot use `sorryAx`. The permitted candidate axioms are `propext`,
`Classical.choice` and `Quot.sound`. Only ordinary ASCII declaration names are
supported by this primitive. Quoted, numeric and other names are rejected
rather than flattened into a potentially different declaration.

The runner stages exact input bytes in a new project with a receiver-written
Lake configuration and manifest. Source files remain read-only. Builds can
write only inside that project's `.lake`; export has no filesystem write
permission except `/dev/null`. The exporter uses the receiver's explicit
Lean sysroot, so it needs no child process to discover the toolchain.

The sandbox denies network access and limits readable paths to selected
runtime/tool roots and the temporary project. It grants no recursive access
to the receiver's home or the Data volume alias; the selected tool directories
under the home remain readable. Only selected environment variables
are passed. The upstream broad root-read request does not expand these roots.
Unsupported flags, paths and executables fail closed. There is no unsandboxed
fallback, and the upstream `fake-landrun.sh` is not used.

## Evidence and limits

Run the local checks from the repository root:

```sh
conformance/.venv/bin/python packages/lean/verification/check_verification.py
```

The runner checks the upstream source pins, ten boundary/process tests and
four fresh semantic comparison cases. The three negative cases must compile
before the comparator rejects them: a changed statement, an incomplete proof
and an unapproved axiom. A fifth run preserves an upstream compatibility
failure: the minimal-prelude primitive-substitution fixture compiles, but its
export lacks `String.mk` on this toolchain. It returns `tool_failure` and
`unsupported_fixture`, never a successful semantic rejection. Logs are stored in
`packages/lean/_out/verification/`. The [observed report](observed-comparator.json)
records exact source and tool hashes, outcomes, durations and remaining work.
It is historical test evidence, not an importable receipt or a benchmark of
scientific usefulness.

The limits are 600 seconds of wall time, 300 CPU seconds per process, 256 MiB
per output file, 1 MiB per input source and 4 MiB of captured diagnostics.
There are also file-descriptor and per-user process ceilings. Deadline and
output-limit handling stop the process group. **This backend has no hard
memory limit or aggregate disk/job quota.** The tests use reviewed fixtures;
they do not qualify the runner as a hostile-upload service. Darwin's
unsupported address-space limit is reported as `null`, never as an enforced
memory cap.

The comparison binds the recorded source bytes, selected names, receiver
toolchain and receiver-trusted binaries. It does not reconstruct a Slean
module or bind its native statement and dependency environment. It supports
only the fresh self-contained project, not dependency-bearing Physlib
modules. It uses Lean's kernel replay, with no separately implemented external
kernel configured. A failed run can be a tool, resource or comparison failure;
it does not establish that a theorem is false.

The result therefore always has `module_receipt: not_issued` and
`slean_policy: unsupported`, even when the local comparison passes. Inspection,
offline application and imported evidence keep their previous trust status.
SR-T06 still needs receiver reconstruction, separate policy reports, receipt
authority, forgery/downgrade controls and stronger resource containment for
unreviewed code. No release or public deployment is included here.

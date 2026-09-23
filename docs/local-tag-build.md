# Local-only documentation tag build — 2026-09-23

This is a rehearsal of the DOC-01 build at the exact documentation candidate revision in [docs PR #1](https://github.com/romainsimon/slean/pull/1). It did not create a release or public tag. The tag exists only in an isolated temporary clone.

| Check | Observed result |
|---|---|
| Source | The clone was made with `git clone --no-local --branch codex/slean-docs-mutome-style /Users/romainsimon/dev/slean`. It copied committed Git state, not the canonical checkout's unrelated uncommitted files. |
| Annotated tag | `local-docs-candidate-bfe4d94`; `git cat-file -t` returned `tag`. The clone was detached at this tag. |
| Resolved revision | Both `HEAD` and `refs/tags/local-docs-candidate-bfe4d94^{commit}` resolved to `bfe4d942516a43b812f5e0c05b84e97ce437943e`. |
| Source cleanliness | `git status --porcelain` was empty before and after the final build. |
| Build | `SLEAN_SITE_TAG=local-docs-candidate-bfe4d94 bash site/build.sh` exited 0. It compiled the Slean executable (13 Lake jobs), passed 16 tests, and compiled the FR/EN Verso site (309 Lake jobs). The build generated seven HTML pages in each language. |
| Rejection checks | The build preflight accepted the exact annotated tag and rejected absent, lightweight, mismatched and dirty-source tags. The focused tests cover these conditions and verify locale-specific stamping. |
| Displayed identity | Both title pages state the local tag. All 14 pages carry an exact-tag meta entry and a localized footer with the tag and short commit. The generated logo assets are present in both locale roots. |
| Artifact metadata | `site/_out/html-multi/build-info.json` recorded `source_revision` as the full commit above, `source_tag: "local-docs-candidate-bfe4d94"`, `source_tree_clean: true`, `schema_version: 0.2.0`, and `lean_version: 4.28.0`. |
| Reader task | The FR/EN manuals now walk through `validate`, `view`, a unit-mismatch rejection, the decision chain, and unknown versus zero. The documented output was compared with the CLI. The new chapter links resolved from the served pages in both languages. |
| Rendered check | The served FR/EN pages were inspected on desktop, 390 px English and 320 px French. Logos loaded, footers wrapped, tutorial code fit without page overflow, and prose links had no underline. The Impeccable detector exited 0 with advisory findings only. |
| Tag isolation | `git ls-remote --tags origin` returned no remote tags. No tag was pushed. |

This proves that the documentation candidate builds from a clean checkout selected by an exact annotated local tag and displays that same tag in the generated manual. There is no published tag, public artifact, or live site route to compare with this build. The later `0.3.0` dependency-gate contract in [PR #4](https://github.com/romainsimon/slean/pull/4) is also outside this `0.2.0` docs candidate. DOC-01 therefore remains partial until a release candidate integrates the accepted changes and the exact public tag, displayed version, compiled examples, and public artifact are checked together.

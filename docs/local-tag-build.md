# Local-only documentation tag build — 2026-09-23

This is a rehearsal of the DOC-01 build at the exact documentation candidate revision in [docs PR #1](https://github.com/romainsimon/slean/pull/1). It did not create a release or public tag. The tag exists only in the isolated temporary clone used for this check.

| Check | Observed result |
|---|---|
| Source | `git clone --no-local /Users/romainsimon/dev/slean /tmp/slean-doc-tag-na9d7e/repo`; the clone copied committed Git state, not the canonical checkout's uncommitted files. |
| Annotated tag | `local-docs-candidate-be349cf`; `git cat-file -t` returned `tag`, and `git describe --exact-match --tags HEAD` returned the same name. |
| Resolved revision | Both `HEAD` and `refs/tags/local-docs-candidate-be349cf^{commit}` resolved to `be349cf2dbd1ffdb372696f60d05c82e5bd73482`. The checkout was detached at the tag. |
| Source cleanliness | `git status --porcelain` was empty before and after the build. |
| Build | `bash site/build.sh` exited 0. It compiled the Slean executable (13 Lake jobs), ran 14 tests successfully, then compiled the FR/EN Verso site (309 Lake jobs). The build includes the checked Lean examples and generated seven HTML pages in each language. |
| Artifact metadata | `site/_out/html-multi/build-info.json` recorded `source_revision` as the full commit above, `source_tree_clean: true`, `schema_version: 0.2.0`, and `lean_version: 4.28.0`. French and English root pages exist. |
| Tag isolation | The canonical Slean repository had no tag named `local-docs-candidate-be349cf`; `git ls-remote --tags origin` from the docs worktree returned no remote tags. No tag was pushed. |

This proves that the documentation candidate builds from a clean checkout selected by an annotated local tag. The generated site still says that no public release tag exists, and `build-info.json` records the commit rather than a displayed tag name. There is no published tag, public artifact, or live site route to compare with this build. The later `0.3.0` dependency-gate contract in [PR #4](https://github.com/romainsimon/slean/pull/4) is also outside this `0.2.0` docs candidate. DOC-01 therefore remains partial until a release candidate integrates the accepted changes and the exact public tag, displayed version, compiled examples, and public artifact are checked together.

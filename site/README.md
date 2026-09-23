# Slean Verso manual

This is a local documentation prototype. It uses Verso v4.28.0 and the repository's Lean 4.28.0 toolchain. The manual includes compiled Lean declaration checks and a synthetic CLI quickstart. It does not publish a site or certify an external scientific result.

From the repository root:

```sh
bash site/build.sh
python3 -m http.server 8765 --directory site/_out/html-multi
```

Open `http://127.0.0.1:8765/` locally. `build.sh` first runs the repository test suite, then builds the manual and copies the self-hosted IBM Plex Sans and Literata fonts, including their OFL licenses, into the site artifact. `site/_out/html-multi/build-info.json` records the base commit, source-tree cleanliness, schema version, and Lean version. The development preview has no public release tag. A clean build identifies its exact source commit.

The build also replaces Verso's generated viewport meta tag on every HTML page so users can zoom on mobile. It fails if any generated page has no viewport tag or more than one.

The site introduces the validator and its limits. The CLI, schemas, and Lean source remain the normative interfaces. The site does not load a private source trace; the displayed case is synthetic. Its search is supplied by Verso.

The layout borrows a chapter sidebar and searchable hierarchy from the [Lean Language Reference](https://lean-lang.org/doc/reference/latest/) and a clear reading progression from [The Rust Programming Language](https://doc.rust-lang.org/book/). Those are navigation principles, not copied screens or assets. The local design tokens and UI decisions are in [DESIGN.md](../DESIGN.md).

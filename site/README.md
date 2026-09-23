# Slean Verso manual

This is a local documentation prototype. It uses Verso v4.28.0 and the repository's Lean 4.28.0 toolchain. The manual includes compiled Lean declaration checks and a synthetic CLI quickstart. It does not publish a site or certify an external scientific result.

From the repository root:

```sh
bash site/build.sh
python3 -m http.server 8765 --directory site/_out/html-multi
```

Open `http://127.0.0.1:8765/` for the French manual or `/en/` for English. The `FR / EN` links keep readers on the corresponding chapter, and each language has its own Verso search index. `build.sh` first runs the repository test suite, then builds both manuals and copies IBM Plex Sans and its OFL license into each site artifact. The interface uses the Satoshi essay font from the [Fontshare API](https://api.fontshare.com/v2/css?f%5B%5D=satoshi%40400%2C500%2C700&display=swap), with IBM Plex Sans as an offline fallback. The [ITF Free Font License](https://www.fontshare.com/licenses/itf-ffl) permits website use through that API and restricts redistribution of the font files, so the repository does not copy Satoshi binaries. `site/_out/html-multi/build-info.json` records the exact source commit, source-tree cleanliness, selected tag, schema version, and Lean version.

The normal build is a development preview and displays no release tag. For a candidate built from an existing annotated tag, check out that tag in a clean repository and run `SLEAN_SITE_TAG=<tag> bash site/build.sh`. The build rejects a lightweight tag, a tag that points elsewhere, or a dirty tree before compiling. Both title pages and the footer of every generated page then show the selected build tag; every page carries it in a metadata field, and `build-info.json` records the tag and full commit. This proves the local artifact's source identity. Publishing a tag, reviewing the final artifact, and deploying the site remain separate steps.

The site uses the supplied Slean vector wordmark in the header and on both title pages. The charcoal and white variants are kept in `assets/brand/`; the white variant is available for future dark surfaces. The mobile header and favicon use a small S mark derived from the same vector geometry. The PNG exports are omitted because the SVGs stay sharp at any size. The build copies these assets into both language outputs.

The build also replaces Verso's generated viewport meta tag on every HTML page so users can zoom on mobile. It fails if any generated page has no viewport tag or more than one.

The site introduces the validator and its limits. The CLI, schemas, and Lean source remain the normative interfaces. The site does not load a private source trace; the displayed case is synthetic. Its search is supplied by Verso.

The layout borrows a chapter sidebar and searchable hierarchy from the [Lean Language Reference](https://lean-lang.org/doc/reference/latest/) and a clear reading progression from [The Rust Programming Language](https://doc.rust-lang.org/book/). Those are navigation principles, not copied screens or assets. The local design tokens and UI decisions are in [DESIGN.md](../DESIGN.md).

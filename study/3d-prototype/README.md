# Local 2D/3D study prototype

This directory prepares two **local, disposable conditions** for the SL-009
comparison on the current integrated Slean candidate. It is not a default
Explorer view and records no participant or study result. The only included
input is the checked synthetic 0.3 dossier.

```sh
lake build
python3 study/3d-prototype/render.py examples/dependency-gates.json --prefix 13
```

The command prints a new temporary directory with `2d/index.html`,
`3d/index.html`, and `study-manifest.json`. Serve that directory over localhost
to inspect the pages. For example:

```sh
python3 -m http.server 8777 --bind 127.0.0.1 --directory /path/printed/by/render
```

Both conditions come from one checked, agent-projected Slean timeline. They
start at the same event prefix, retain the same decision, evidence list, exact
event record, journal, and source bundle, and differ only in the dependency
map presentation. The 3D candidate positions recorded AND and OR groups at
different depths, with keyboard-operable native range controls for yaw and
pitch. It never edits or evaluates the records. The complete evidence list
remains the text fallback. There is no camera animation or timed motion.

The manifest's `prepared_not_run` status means that no representative dossier,
reviewer, task result, or decision about 3D usefulness has been recorded. Use
the separate task-study protocol before drawing a conclusion about SL-009. The
manifest also names the clean source revision, projected case ID, exact
agent-projected bundle, and each condition page by SHA-256 so the shared study
inputs can be frozen before a reviewer sees either view. It does not include a
hash of the raw owner input; keep any owner-only provenance separately.

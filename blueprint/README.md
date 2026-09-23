# Same-case Blueprint prototype

This local prototype maps the public projection of [`examples/valid.json`](../examples/valid.json) to Verso Blueprint v4.28.0. The package pins Blueprint commit `84fb00913d07325342e8b73a8a88f6e05ee59473` and Lean 4.28.0. It is a comparison artifact, not Slean's validator or a site to publish.

To inspect the exact projected case before reading the authored Blueprint page, run `lake exe slean export examples/valid.json agent` from the repository root.

From this directory:

```sh
lake build SleanBlueprint
lake env lean --run SleanBlueprintMain.lean --output _out/site
python3 -m http.server 8767 --directory _out/site/html-multi
```

Open `http://127.0.0.1:8767/` locally. The prototype uses Blueprint labels and `uses` links for the synthetic claim and events 1–8, and links to Slean's conditional Lean theorem. It deliberately omits owner-only events 9 and 10 from its page. This omission is manual. The Blueprint graph and progress summary describe formalization dependencies, not the experimental verdict.

The [comparison record](../docs/blueprint-comparison.md) states the observed behavior and the bounded Explorer decision. Generated files under `_out/` and `.lake/` are ignored.

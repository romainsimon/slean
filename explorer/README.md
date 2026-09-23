# Local Explorer

The Explorer shows a validated dossier at each projected journal prefix. It consumes `slean timeline`, which validates the full input case before projecting the requested audience, then replays each projected prefix. The page can inspect a decision, its assessment and frozen rule, records available at that point, actual recorded relations, and the exact selected event. It does not execute research or certify an empirical claim.

## Build and open

From the repository root:

```sh
lake build
python3 explorer/render.py examples/valid.json
python3 -m http.server 8768 --directory explorer/_out/agent
```

Open `http://127.0.0.1:8768/`. The default artifact is `explorer/_out/agent/` and contains HTML, CSS, JavaScript, and self-hosted fonts. It needs no network connection after generation. The included case is synthetic. The page opens at the latest prefix; use the slider, Previous and Next buttons, desktop journal list or mobile event picker, or record links to move between prefixes. The exact selected event is available under **Exact event record**.

To inspect owner-only events locally, pass `--audience owner --output explorer/_out/owner`. This creates a separate artifact with owner data embedded in HTML. Keep that directory private. The renderer refuses to reuse a populated output directory unless its marker belongs to the same case and audience. An invalid case produces no artifact.

## Design and scope

The task is historical review: “What did the author have when this decision was recorded?” The prefix control is the primary interaction. It keeps the current decision and evidence in view while the event list selects the time point. The interface uses Slean's mineral and evergreen palette, IBM Plex Sans, and rust links from the local [manual design](../DESIGN.md), with denser tool typography and standard controls. The surface rules are recorded in [Explorer design](DESIGN.md).

Two reference principles informed the layout. [GitHub Actions run logs](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs) keep an ordered execution record available for targeted inspection. The Explorer adapts that principle to immutable dossier events and prefix state. [Jaeger's trace UI](https://www.jaegertracing.io/docs/2.21/deployment/frontend-ui/) pairs a sequence with details of one selected span; the Explorer similarly pairs the journal with the selected event and evidence, without implying a temporal performance trace. The interface and wording are original to Slean.

The final view preserves Slean's epistemic boundary. `pass` is a local exact-rule assessment; an external assessment remains `external_unverified`. A recorded relation is displayed as data, not as independent scientific proof. The generator does not parse or validate the case itself; its only source of case data is the checked CLI output. It has no server, storage, search, filtering, theorem graph, or 3D scene.

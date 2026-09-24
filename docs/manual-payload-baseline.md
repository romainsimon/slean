# Local manual payload baseline

This is a read-only static measurement of the existing FR/EN manual artifact at
`a4bcf5dfef10a1b4348d543c795343fe907c9a9b`. Its `build-info.json` names
that same revision, reports `source_tree_clean: true`, schema `0.3.0`, Lean
`4.28.0`, and no release tag. The worktree was clean. The `site/` and
`explorer/` source files are unchanged between this revision and Slean draft
PR #21 at `dba6df5206a7c55e448974094e29d50052f3fd50`.

| Generated file | SHA-256 |
|---|---|
| `site/_out/html-multi/build-info.json` | `f076a56d4d485b3c4500aaf5370ee438f6600f45ce83012b6dce73f2be9499e6` |
| `site/_out/html-multi/index.html` | `800cb6de43bc02154afbc512007ae099dfb1e0c0cad50bc3d29ff21d3e6ddd32` |
| `site/_out/html-multi/en/index.html` | `aaaee3403977352e73a342421b0d6997b3e78fb612880b72095ffcc89e524a51` |

The count below includes each existing local file referenced by a landing
page's `script`, `link`, or `img` tag once. Gzip sizes are level-6 estimates
computed from the artifact bytes, not observed network transfer sizes.

| Landing page | HTML bytes / gzip estimate | Local references | Local bytes / gzip estimate |
|---|---:|---:|---:|
| French `/` | 46,891 / 11,338 | 18 | 724,467 / 144,866 |
| English `/en/` | 46,600 / 11,105 | 18 | 664,841 / 141,059 |

Both pages reference Marked 11.1.1 from jsDelivr and request the Satoshi CSS
from Fontshare. The Plausible loader requests its script only on `slean.org`;
local preview does not send a pageview. The counts exclude these external
resources, resources loaded later by CSS or JavaScript, and browser cache
effects. No browser load time, Core Web Vital, production compression, or
maintenance time was measured by this check. It is payload evidence for the
local DOC-02 candidate, not a performance pass or a public-site result.

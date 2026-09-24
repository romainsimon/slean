#!/usr/bin/env bash
set -euo pipefail

image_ref="${1:?usage: smoke_site_image.sh IMAGE COMMIT_SHA [SCHEMA_VERSION [SOURCE_TAG]]}"
expected_sha="${2:?usage: smoke_site_image.sh IMAGE COMMIT_SHA [SCHEMA_VERSION [SOURCE_TAG]]}"
expected_schema="${3:-0.3.0}"
expected_tag="${4:-}"
[[ "$expected_sha" =~ ^[0-9a-f]{40}$ ]] || { echo "Expected a full Git SHA" >&2; exit 1; }
[[ "$expected_schema" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Expected a schema version" >&2; exit 1; }

container_name="slean-smoke-${RANDOM}-${RANDOM}"
container_id=""
artifact_dir="$(mktemp -d)"
cleanup() {
  if [[ -n "$container_id" ]]; then
    docker stop "$container_id" >/dev/null 2>&1 || true
    docker container rm "$container_id" >/dev/null 2>&1 || true
  fi
  rm -rf "$artifact_dir"
}
trap cleanup EXIT

container_id="$(docker run -d --name "$container_name" -p 127.0.0.1::80 "$image_ref")"
port="$(docker port "$container_id" 80/tcp)"
port="${port##*:}"
origin="http://127.0.0.1:${port}"

health="starting"
for _ in $(seq 1 30); do
  health="$(docker inspect --format '{{.State.Health.Status}}' "$container_id")"
  [[ "$health" == healthy ]] && break
  [[ "$health" == unhealthy ]] && break
  sleep 2
done
if [[ "$health" != healthy ]]; then
  docker logs "$container_id" >&2
  echo "Final image did not become healthy: $health" >&2
  exit 1
fi

docker exec "$container_id" wget -q -O /dev/null http://127.0.0.1/
docker exec "$container_id" wget -q -O /dev/null http://127.0.0.1/en/
docker exec "$container_id" test ! -e /src
docker exec "$container_id" test ! -e /root/.elan
for route in / /en/ /portes-et-ou/ /en/and-or-gates/ /find/ /en/find/ /assets/brand/slean-dark.svg /build-info.json; do
  curl -fsS --max-time 10 -o /dev/null "$origin$route"
done

label_sha="$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image_ref")"
[[ "$label_sha" == "$expected_sha" ]] || { echo "Image revision label mismatch" >&2; exit 1; }

docker cp "$container_id:/usr/share/nginx/html/." "$artifact_dir/"
EXPECTED_SHA="$expected_sha" EXPECTED_SCHEMA="$expected_schema" EXPECTED_TAG="$expected_tag" SLEAN_ARTIFACT_DIR="$artifact_dir" python3 - <<'PY'
import html
import json
import os
from pathlib import Path

root = Path(os.environ["SLEAN_ARTIFACT_DIR"])
pages = list(root.rglob("*.html"))
script = "https://stats.yukicapital.com/js/pa-70RUKb_J9zQLn67oUHf2d.js"
old_scripts = ("https://stats.yukicapital.com/js/script.js", "https://plausible.io/js/")
info = json.loads((root / "build-info.json").read_text())
assert info["source_revision"] == os.environ["EXPECTED_SHA"]
assert info["source_tree_clean"] is True
assert info["schema_version"] == os.environ["EXPECTED_SCHEMA"]
if os.environ["EXPECTED_TAG"]:
    assert info["source_tag"] == os.environ["EXPECTED_TAG"]
assert len(pages) == 16
assert sum("en" in page.relative_to(root).parts for page in pages) == 8
for page in pages:
    markup = page.read_text()
    if os.environ["EXPECTED_TAG"]:
        safe_tag = html.escape(os.environ["EXPECTED_TAG"], quote=True)
        assert markup.count(f'name="slean-build-tag" content="{safe_tag}"') == 1, page
        assert markup.count('class="slean-build-footer"') == 1, page
    assert markup.count("data-slean-analytics") == 1, page
    assert markup.count(script) == 2, page
    assert not any(old in markup for old in old_scripts), page
assert not any(path.name in {".git", ".env"} for path in root.rglob("*"))
print("Final image: exact SHA, healthy, 16 pages, one Plausible loader per page")
PY
SLEAN_TEST_ORIGIN="$origin" npm --prefix site run test:browser

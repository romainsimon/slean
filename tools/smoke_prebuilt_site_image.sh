#!/usr/bin/env bash
set -euo pipefail

check_only=false
if [[ "${1:-}" == --check-only ]]; then
  check_only=true
  shift
fi

usage='usage: smoke_prebuilt_site_image.sh [--check-only] ARTIFACT_DIR COMMIT_SHA SCHEMA_VERSION SOURCE_TAG [IMAGE_REF]'
if [[ "$check_only" == true && $# -ne 4 ]] || [[ "$check_only" == false && $# -ne 5 ]]; then
  echo "$usage" >&2
  exit 2
fi

artifact_dir="$(cd "$1" && pwd -P)"
expected_sha="$2"
expected_schema="$3"
expected_tag="$4"
image_ref="${5:-}"
[[ "$expected_sha" =~ ^[0-9a-f]{40}$ ]] || { echo 'Expected a full Git SHA' >&2; exit 2; }
[[ "$expected_schema" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Expected a schema version' >&2; exit 2; }
git check-ref-format "refs/tags/$expected_tag" || { echo 'Expected a valid source tag' >&2; exit 2; }

SLEAN_ARTIFACT_DIR="$artifact_dir" EXPECTED_SHA="$expected_sha" EXPECTED_SCHEMA="$expected_schema" EXPECTED_TAG="$expected_tag" python3 - <<'PY'
import html
import json
import os
from pathlib import Path

root = Path(os.environ["SLEAN_ARTIFACT_DIR"])
expected_sha = os.environ["EXPECTED_SHA"]
expected_tag = os.environ["EXPECTED_TAG"]
expected = {
    "source_revision": expected_sha,
    "source_tree_clean": True,
    "source_tag": expected_tag,
    "schema_version": os.environ["EXPECTED_SCHEMA"],
    "lean_version": "4.28.0",
}
info = json.loads((root / "build-info.json").read_text(encoding="utf-8"))
if info != expected:
    raise SystemExit(f"Artifact identity mismatch: {info!r}")

pages = sorted(root.rglob("*.html"))
if len(pages) != 16 or sum("en" in page.relative_to(root).parts for page in pages) != 8:
    raise SystemExit("Expected 16 localized HTML pages, eight in English")
safe_tag = html.escape(expected_tag, quote=True)
for page in pages:
    markup = page.read_text(encoding="utf-8")
    if (markup.count(f'name="slean-build-tag" content="{safe_tag}"') != 1
            or markup.count('class="slean-build-footer"') != 1
            or expected_tag not in markup
            or expected_sha[:12] not in markup):
        raise SystemExit(f"Artifact page identity mismatch: {page}")
print(f"Prebuilt artifact: exact SHA {expected_sha}, schema {expected['schema_version']}, tag {expected_tag}, 16 pages")
PY

if "$check_only"; then
  exit 0
fi

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_dir"
docker buildx build --load --target prebuilt-site-smoke \
  --build-context "prebuilt-site=$artifact_dir" \
  --build-arg "SOURCE_COMMIT=$expected_sha" \
  -t "$image_ref" .
bash tools/smoke_site_image.sh "$image_ref" "$expected_sha" "$expected_schema" "$expected_tag"
docker image inspect --format 'Local image ID: {{.Id}}' "$image_ref"

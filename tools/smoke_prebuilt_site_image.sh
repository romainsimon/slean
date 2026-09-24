#!/usr/bin/env bash
set -euo pipefail

check_only=false
if [[ "${1:-}" == --check-only ]]; then
  check_only=true
  shift
fi

usage='usage: smoke_prebuilt_site_image.sh [--check-only] ARTIFACT_DIR IMAGE_SOURCE_SHA ARTIFACT_SOURCE_SHA SCHEMA_VERSION SOURCE_TAG [IMAGE_REF]'
if [[ "$check_only" == true && $# -ne 5 ]] || [[ "$check_only" == false && $# -ne 6 ]]; then
  echo "$usage" >&2
  exit 2
fi

artifact_dir="$(cd "$1" && pwd -P)"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
image_source_sha="$2"
artifact_source_sha="$3"
expected_schema="$4"
expected_tag="$5"
image_ref="${6:-}"
[[ "$image_source_sha" =~ ^[0-9a-f]{40}$ ]] || { echo 'Expected a full image-source Git SHA' >&2; exit 2; }
[[ "$artifact_source_sha" =~ ^[0-9a-f]{40}$ ]] || { echo 'Expected a full artifact-source Git SHA' >&2; exit 2; }
[[ "$expected_schema" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Expected a schema version' >&2; exit 2; }
git check-ref-format "refs/tags/$expected_tag" || { echo 'Expected a valid source tag' >&2; exit 2; }
if [[ -e "$repo_dir/.git" ]]; then
  current_head="$(git -C "$repo_dir" rev-parse HEAD)" || { echo 'Image source Git metadata is unreadable' >&2; exit 1; }
  [[ "$current_head" == "$image_source_sha" ]] || { echo 'Image source SHA must match current HEAD' >&2; exit 1; }
  if [[ "$check_only" == false && -n "$(git -C "$repo_dir" status --porcelain=v1)" ]]; then
    echo 'Image source checkout must be clean' >&2
    exit 1
  fi
else
  [[ "${SOURCE_COMMIT:-}" == "$image_source_sha" ]] || { echo 'Image source SHA must match SOURCE_COMMIT in an archive' >&2; exit 1; }
  if [[ "$check_only" == false ]]; then
    echo 'Building a prebuilt image requires a verifiable Git checkout' >&2
    exit 1
  fi
fi

SLEAN_ARTIFACT_DIR="$artifact_dir" EXPECTED_ARTIFACT_SHA="$artifact_source_sha" EXPECTED_SCHEMA="$expected_schema" EXPECTED_TAG="$expected_tag" python3 - <<'PY'
import html
import json
import os
import re
from pathlib import Path

root = Path(os.environ["SLEAN_ARTIFACT_DIR"])
expected_artifact_sha = os.environ["EXPECTED_ARTIFACT_SHA"]
expected_tag = os.environ["EXPECTED_TAG"]
expected = {
    "source_revision": expected_artifact_sha,
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
    footer = re.search(r'<footer class="slean-build-footer"[^>]*>(.*?)</footer>', markup, re.DOTALL)
    if (markup.count(f'name="slean-build-tag" content="{safe_tag}"') != 1
            or footer is None
            or markup.count('class="slean-build-footer"') != 1
            or expected_tag not in html.unescape(footer.group(1))
            or expected_artifact_sha[:12] not in footer.group(1)):
        raise SystemExit(f"Artifact page identity mismatch: {page}")
print(f"Prebuilt artifact: source SHA {expected_artifact_sha}, schema {expected['schema_version']}, tag {expected_tag}, 16 pages")
PY

if "$check_only"; then
  exit 0
fi

cd "$repo_dir"
docker buildx build --load --target prebuilt-site-smoke \
  --build-context "prebuilt-site=$artifact_dir" \
  --build-arg "SOURCE_COMMIT=$image_source_sha" \
  -t "$image_ref" .
bash tools/smoke_site_image.sh "$image_ref" "$image_source_sha" "$artifact_source_sha" "$expected_schema" "$expected_tag"
docker image inspect --format 'Local image ID: {{.Id}}' "$image_ref"

#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_dir"
bash tests/check.sh

cd "$repo_dir/site"
lake build
rm -rf _out/html-multi _out/en-render
lake exe sleandocs
python3 prepare_locales.py
python3 fix_viewport.py
revision="$(git -C "$repo_dir" rev-parse HEAD)"
source_tree_clean=true
if [[ -n "$(git -C "$repo_dir" status --porcelain -- . ':(exclude)https:/')" ]]; then
  source_tree_clean=false
fi
printf '{"source_revision":"%s","source_tree_clean":%s,"schema_version":"0.2.0","lean_version":"4.28.0"}\n' "$revision" "$source_tree_clean" > _out/html-multi/build-info.json
for locale_dir in _out/html-multi _out/html-multi/en; do
  mkdir -p "$locale_dir/fonts"
  mkdir -p "$locale_dir/assets/brand"
  cp assets/fonts/ibm-plex-sans-regular.ttf "$locale_dir/fonts/"
  cp assets/fonts/ibm-plex-sans-semibold.ttf "$locale_dir/fonts/"
  cp assets/fonts/OFL-ibm-plex-sans.txt "$locale_dir/fonts/"
  cp assets/brand/slean-dark.svg assets/brand/slean-white.svg assets/brand/slean-mark.svg "$locale_dir/assets/brand/"
done

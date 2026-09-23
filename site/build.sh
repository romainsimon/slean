#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_dir"
bash tests/check.sh

cd "$repo_dir/site"
lake build
lake exe sleandocs
python3 fix_viewport.py
revision="$(git -C "$repo_dir" rev-parse HEAD)"
source_tree_clean=true
if [[ -n "$(git -C "$repo_dir" status --porcelain -- . ':(exclude)https:/')" ]]; then
  source_tree_clean=false
fi
printf '{"source_revision":"%s","source_tree_clean":%s,"schema_version":"0.2.0","lean_version":"4.28.0"}\n' "$revision" "$source_tree_clean" > _out/html-multi/build-info.json
mkdir -p _out/html-multi/fonts
rm -f _out/html-multi/fonts/literata-semibold.ttf _out/html-multi/fonts/OFL-literata.txt
cp assets/fonts/ibm-plex-sans-regular.ttf _out/html-multi/fonts/
cp assets/fonts/ibm-plex-sans-semibold.ttf _out/html-multi/fonts/
cp assets/fonts/OFL-ibm-plex-sans.txt _out/html-multi/fonts/

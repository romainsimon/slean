#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_dir"
python3 site/build_identity.py preflight
bash tests/check.sh

cd "$repo_dir/site"
lake build
rm -rf _out/html-multi _out/en-render
lake exe sleandocs
python3 prepare_locales.py
python3 harden_verso.py
python3 fix_viewport.py
python3 build_identity.py stamp
python3 add_analytics.py
for locale_dir in _out/html-multi _out/html-multi/en; do
  mkdir -p "$locale_dir/fonts"
  mkdir -p "$locale_dir/assets/brand"
  cp assets/fonts/ibm-plex-sans-regular.ttf "$locale_dir/fonts/"
  cp assets/fonts/ibm-plex-sans-semibold.ttf "$locale_dir/fonts/"
  cp assets/fonts/OFL-ibm-plex-sans.txt "$locale_dir/fonts/"
  cp assets/brand/slean-dark.svg assets/brand/slean-white.svg assets/brand/slean-mark.svg assets/brand/mutome-texture.webp "$locale_dir/assets/brand/"
done

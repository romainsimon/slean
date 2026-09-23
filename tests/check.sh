#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
check_dir="$(mktemp -d)"
trap 'rm -rf "$check_dir"' EXIT
lake build
python3 -m unittest discover -s tests -p 'test_*.py' -v
lake env lean --run examples/Synthetic.lean > "$check_dir/lean-case.json"
lake exe slean export examples/valid.json agent > "$check_dir/json-case.json"
cmp "$check_dir/lean-case.json" "$check_dir/json-case.json"
if lake env lean tests/TypeError.lean > "$check_dir/type-error.log" 2>&1; then
  echo 'expected static type failure was accepted' >&2
  exit 1
fi
rg -i 'type mismatch|application type mismatch' "$check_dir/type-error.log" > /dev/null
lake env lean tests/BadProofs.lean > "$check_dir/bad-proofs.log" 2>&1
rg 'forbidden' "$check_dir/bad-proofs.log" > /dev/null
rg 'sorryAx' "$check_dir/bad-proofs.log" > /dev/null

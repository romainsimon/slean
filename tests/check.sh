#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
check_dir="$(mktemp -d)"
trap 'rm -rf "$check_dir"' EXIT
lake build
test "$(cat lean-toolchain)" = 'leanprover/lean4:v4.28.0'
lake env lean --version | rg -F 'version 4.28.0' > /dev/null
python3 -m unittest discover -s tests -p 'test_*.py' -v
lake env lean --run examples/Synthetic.lean > "$check_dir/lean-case.json"
lake exe slean export-case examples/valid.json agent > "$check_dir/json-case.json"
cmp "$check_dir/lean-case.json" "$check_dir/json-case.json"
lake env lean --run examples/ExactThreshold.lean > "$check_dir/exact-threshold.txt"
printf 'equal=fail; above=pass\n' | cmp - "$check_dir/exact-threshold.txt"
lake env lean --run examples/ValidateExport.lean > "$check_dir/validate-export.txt"
printf 'validated=10; agent_events=8\nexport=slean-export/0.1.0; lean=4.28.0\n' | cmp - "$check_dir/validate-export.txt"
lake env lean --run examples/FormalBoundary.lean > "$check_dir/formal-boundary.txt"
printf 'eligible=true; status=declared\n' | cmp - "$check_dir/formal-boundary.txt"
lake exe slean export examples/valid.json agent > "$check_dir/agent-export.json"
lake exe slean validate "$check_dir/agent-export.json" > "$check_dir/agent-validation.json"
printf '{"case_id":"synthetic-decision-1","events":8,"ok":true}\n' | cmp - "$check_dir/agent-validation.json"
lake exe slean validate examples/uci-bike-sharing/case.json > "$check_dir/uci-validation.json"
printf '{"case_id":"uci-bike-hourly-2011-2012-mae-v1","events":8,"ok":true}\n' | cmp - "$check_dir/uci-validation.json"
lake exe slean replay examples/uci-bike-sharing/case.json 8 > "$check_dir/uci-replay.json"
python3 - "$check_dir/uci-replay.json" <<'PY'
import json
import sys

replay = json.load(open(sys.argv[1], encoding="utf-8"))
assert replay["observations"][0]["value"] == "50.094698"
assert replay["costs"][0]["amount"] == "0.122995000"
assert replay["assessments"][0]["verdict"] == "pass"
assert replay["decisions"][0]["result"] == "promote"
PY
if lake env lean tests/TypeError.lean > "$check_dir/type-error.log" 2>&1; then
  echo 'expected static type failure was accepted' >&2
  exit 1
fi
rg -i 'type mismatch|application type mismatch' "$check_dir/type-error.log" > /dev/null
lake env lean tests/BadProofs.lean > "$check_dir/bad-proofs.log" 2>&1
rg 'forbidden' "$check_dir/bad-proofs.log" > /dev/null
rg 'sorryAx' "$check_dir/bad-proofs.log" > /dev/null

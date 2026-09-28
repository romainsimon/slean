#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
slean_lake="${SLEAN_LAKE:-lake}"
slean_check_dir="$(mktemp -d)"
trap 'rm -rf "$slean_check_dir"' EXIT

"$slean_lake" build DirectReuse
if ! "$slean_lake" env lean Audit.lean > "$slean_check_dir/audit.txt" 2>&1; then
  cat "$slean_check_dir/audit.txt" >&2
  exit 1
fi
cat "$slean_check_dir/audit.txt"

python3 - "$slean_check_dir/audit.txt" <<'PY'
import pathlib
import re
import sys

text = pathlib.Path(sys.argv[1]).read_text()
reports = dict(re.findall(r"^'(.+)' depends on axioms: \[([^\]]*)\]", text, re.MULTILINE))
expected = {
    "ClassicalMechanics.HarmonicOscillator.energy_conservation_of_equationOfMotion'",
    "DirectReuse.energy_at_two_times",
}
if reports.keys() != expected:
    raise SystemExit("Missing or unexpected axiom report")
allowed = {"propext", "Classical.choice", "Quot.sound"}
for declaration, report in reports.items():
    axioms = {name.strip() for name in report.split(",") if name.strip()}
    if axioms - allowed:
        raise SystemExit(f"Unapproved axioms in {declaration}: {sorted(axioms - allowed)}")
PY

for fixture in MissingHypothesis ChangedStatement; do
  if "$slean_lake" env lean "negative/$fixture.lean" > "$slean_check_dir/$fixture.txt" 2>&1; then
    echo "Expected Lean rejection for $fixture" >&2
    exit 1
  fi
done

python3 - "$slean_check_dir" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
checks = {
    "MissingHypothesis": ("unsolved goals", "system.EquationOfMotion trajectory"),
    "ChangedStatement": ("Type mismatch", "system.energy trajectory second + 1"),
}
for fixture, expected in checks.items():
    message = (root / (fixture + ".txt")).read_text()
    if not all(fragment.casefold() in message.casefold() for fragment in expected):
        raise SystemExit(f"Unexpected failure for {fixture}:\n{message}")
    print(f"PASS: {fixture} rejected for the intended obligation/statement")
PY

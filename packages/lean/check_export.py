"""Build and exercise the selected-declaration exporter against real Lean modules."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT / "examples/reuse/with-slean-lean"
OUT = PROJECT / "_out"
OUT.mkdir(exist_ok=True)
LAKE = os.environ.get("SLEAN_LAKE", "lake")
ENV = {**os.environ, "ELAN_TOOLCHAIN": "leanprover/lean4:v4.34.1"}
steps = []
started = time.monotonic()


def run(label, args, cwd, error=None):
    before = time.monotonic()
    result = subprocess.run(args, cwd=cwd, env=ENV, text=True, capture_output=True, timeout=300)
    output = result.stdout + result.stderr
    (OUT / (label + ".log")).write_text(output)
    if error is None and result.returncode != 0:
        raise SystemExit(output)
    if error is not None and (result.returncode == 0 or error not in output):
        raise SystemExit(f"Expected rejection containing {error!r}:\n{output}")
    steps.append({"check": label, "outcome": "rejected_as_expected" if error else "passed",
                  "seconds": round(time.monotonic() - before, 3)})
    return output


run("library-build", [LAKE, "build", "SleanExport"], HERE)
run("native-encoding", [LAKE, "env", "lean", "tests/NativeEncoding.lean"], HERE)
run("consumer-build", [LAKE, "build", "FormalExample"], PROJECT)
run("native-export", [LAKE, "env", "lean", "Export.lean"], PROJECT)
with tempfile.TemporaryDirectory(prefix="selection-controls-", dir=OUT) as temp:
    folder = Path(temp)
    for label, body, diagnostic in [
        ("unknown-declaration", "#slean_export [SleanMissingDeclaration]", "SleanMissingDeclaration"),
        ("empty-selection", "#slean_export []", "Select at least one declaration"),
        ("unbuilt-local-declaration", "theorem local_only : True := True.intro\n#slean_export [local_only]",
         "build and import the defining module first")]:
        target = folder / (label + ".json")
        source = folder / (label.replace("-", "_") + ".lean")
        source.write_text("import SleanExport\n" + body + " to " + json.dumps(str(target)) + "\n")
        run(label, [LAKE, "env", "lean", str(source)], PROJECT, diagnostic)
        if target.exists():
            raise SystemExit("A rejected selection wrote an extraction")
test_log = run("bridge-tests", [sys.executable, "tests/test_export.py"], HERE)
if "Ran 8 tests" not in test_log:
    raise SystemExit("Expected the full bridge test suite")

sys.path.insert(0, str(ROOT / "conformance"))
import contract
import export

with tempfile.TemporaryDirectory(prefix="checked-module-", dir=OUT) as temp:
    module = Path(temp) / "module"
    manifest = export.pack(OUT / "native.json", PROJECT, module)
    report = contract.check(manifest, module)
raw = json.loads((OUT / "native.json").read_text())
source_paths = [p for p in HERE.rglob("*") if p.is_file() and not any(
    part in {".lake", "__pycache__", "_out"} for part in p.relative_to(HERE).parts)
    and p.suffix in {".lean", ".py", ".toml", ".json"} and p.name != "observed-export.json"]
source_paths += [PROJECT / name for name in ["FormalExample.lean", "Export.lean", "lakefile.toml", "lake-manifest.json", "lean-toolchain"]]
print(json.dumps({
    "status": "passed", "scope": "SR-T04 selected-declaration extraction and packaging",
    "lean": raw["lean_version"], "declarations_exported": len(raw["declarations"]),
    "native_constructor_vectors": 10, "open_expression_rejections": 5,
    "selection_rejections": 3, "bridge_tests": 8,
    "module": manifest["id"], "payloads": len(manifest["payloads"]),
    "receiver_report": report,
    "declarations": [{"name": d["display_name"], "kind": d["kind"],
        "statement_dependency_count": len(d["statement_dependencies"]),
        "proof_dependency_count": len(d["proof_dependencies"]), "axioms": d["axioms"]}
        for d in raw["declarations"]],
    "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source_paths)},
    "steps": steps, "elapsed_seconds": round(time.monotonic() - started, 3),
    "setup": "Existing pinned Lean/Physlib cache; complete setup and authoring costs not measured",
    "limitations": ["No receiver rebuild or proof receipt", "No unreviewed-code isolation",
                    "No new runtime apply/verify operation", "Gate U not evaluated"]
}, indent=2, sort_keys=True))

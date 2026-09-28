"""Package the direct-tool example as RO-Crate 1.3, with ordinary JSON payloads."""

import hashlib
from decimal import getcontext
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil

from consumer import consume
from producer import ROOT, calibrate
from research import run_cycle


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def build(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    calibration = calibrate(ROOT / "fixtures/calibration.csv")
    sample = json.loads((ROOT / "fixtures/sample.json").read_text())
    inputs = json.loads((ROOT / "fixtures/research.json").read_text())
    result = consume(calibration, sample, expected_version=calibration["sha256"])
    investigation = run_cycle(calibration, sample, inputs)
    for name, value in [("calibration.json", calibration), ("sample.json", sample),
                        ("result.json", result), ("investigation.json", investigation)]:
        write_json(output / name, value)
    for name in ["method.py", "producer.py", "consumer.py", "research.py", "requirements.lock"]:
        shutil.copyfile(ROOT / name, output / name)
    shutil.copyfile(ROOT / "fixtures/calibration.csv", output / "calibration.csv")
    shutil.copyfile(ROOT / "fixtures/research.json", output / "research-inputs.json")
    shutil.copyfile(ROOT / "fixtures/pint-definitions.json", output / "pint-definitions.json")
    import pint
    unit_files = {file.name: hashlib.sha256(file.read_bytes()).hexdigest()
                  for file in sorted(Path(pint.__file__).parent.glob("*.txt"))}
    write_json(output / "environment.json", {"python": platform.python_version(),
               "pint": importlib.metadata.version("pint"), "unit_definition_sha256": unit_files,
               "decimal_precision": getcontext().prec, "decimal_rounding": getcontext().rounding})

    # Normal Lake source and recorded checks travel beside the computational data.
    # These saved reports are observations, not receipts the recipient may trust.
    formal = ROOT.parent / "direct-lean"
    for pattern in ["*.lean", "negative/*.lean", "lakefile.toml", "lake-manifest.json",
                    "lean-toolchain", "check.sh", "check_*.py", "mathlib-cache-roots.txt",
                    "observed*.json", "observed-interface.txt"]:
        for source in sorted(formal.glob(pattern)):
            destination = output / "formal" / source.relative_to(formal)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    files = sorted(file for file in output.rglob("*") if file.is_file())
    manifest = {file.relative_to(output).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                for file in files}
    write_json(output / "payload-sha256.json", manifest)
    files.append(output / "payload-sha256.json")
    license_id = "https://spdx.org/licenses/Apache-2.0.html"
    graph = [
        {"@id": "ro-crate-metadata.json", "@type": "CreativeWork", "about": {"@id": "./"},
         "conformsTo": {"@id": "https://w3id.org/ro/crate/1.3"}},
        {"@id": "./", "@type": "Dataset", "name": "Direct-tool cumulative research fixture",
         "description": "Synthetic engineering fixture; no scientific discovery or empirical validation claim.",
         "datePublished": "2026-09-28", "license": {"@id": license_id},
         "hasPart": [{"@id": file.relative_to(output).as_posix()} for file in files]},
        {"@id": license_id, "@type": "CreativeWork", "name": "Apache License 2.0",
         "description": "Licence selected for the owned synthetic fixture and source code."},
        {"@id": "#calibration-use", "@type": "CreateAction", "instrument": {"@id": "method.py"},
         "object": [{"@id": "calibration.json"}, {"@id": "sample.json"}], "result": {"@id": "result.json"}},
        {"@id": "#research-cycle", "@type": "CreateAction", "instrument": {"@id": "research.py"},
         "object": [{"@id": "calibration.json"}, {"@id": "research-inputs.json"}],
         "result": {"@id": "investigation.json"}},
        {"@id": "#formal-reuse-check", "@type": "CreateAction",
         "description": "Recorded local checks; a recipient must recompute them before trusting the result.",
         "instrument": [{"@id": "formal/check.sh"}, {"@id": "formal/check_calibration.py"}],
         "object": [{"@id": "formal/DirectReuse.lean"}, {"@id": "formal/CalibrationProof.lean"},
                    {"@id": "formal/lake-manifest.json"}],
         "result": [{"@id": "formal/observed-interface.txt"}, {"@id": "formal/observed-calibration.json"}]},
    ]
    for file in files:
        graph.append({"@id": file.relative_to(output).as_posix(), "@type": "File", "name": file.name,
                      "contentSize": str(file.stat().st_size),
                      "encodingFormat": "application/json" if file.suffix == ".json" else "text/plain"})
    write_json(output / "ro-crate-metadata.json", {
        "@context": "https://w3id.org/ro/crate/1.3/context", "@graph": graph})
    return investigation


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.output)

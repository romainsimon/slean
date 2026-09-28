"""Run fixed conformance fixtures and report exactly the implemented checking scope."""

import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import time
import unittest

import test_contract

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
started = time.monotonic()
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromModule(test_contract))
if not result.wasSuccessful():
    raise SystemExit(stream.getvalue())
paths = [p for folder in [ROOT / "spec", ROOT / "profiles"] for p in folder.iterdir() if p.is_file()]
print(json.dumps({
    "status": "passed", "tests": result.testsRun,
    "positive_modules": len(list((HERE / "fixtures").glob("*/slean-module.json"))),
    "negative_vectors": len(json.loads((HERE / "negative-cases.json").read_text())),
    "requirement_vectors": len(json.loads((HERE / "requirement-vectors.json").read_text())),
    "identity_vectors": {key: len(value) for key, value in json.loads((HERE / "identity-vectors.json").read_text()).items()},
    "runtime": {"python": platform.python_version(), "jsonschema": importlib.metadata.version("jsonschema"),
                "rfc8785": importlib.metadata.version("rfc8785")},
    "specification_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
    "elapsed_seconds": round(time.monotonic() - started, 3),
    "scope": "Draft wire constraints, fixture identity and requirement aggregation",
    "scientific_verification": "not_performed", "independent_scientific_reader": "not_delivered",
    "sdk": "not_implemented", "gate_u": "not_evaluated"
}, indent=2, sort_keys=True))

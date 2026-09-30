"""Record the quantity checkpoint; this does not close the method SDK task."""
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
started = time.monotonic()
suite = unittest.defaultTestLoader.discover(str(HERE / 'tests'), pattern='test_quantities.py')
result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
paths = [HERE / path for path in ('slean/__init__.py', 'slean/quantities.py',
    'slean/data/quantity-map.json', 'tests/test_quantities.py', 'check_quantities.py')]
paths += [ROOT / 'profiles/quantity-map.json']
report = {'status': 'passed' if result.wasSuccessful() and result.testsRun == 4 else 'failed',
    'scope': 'Quantity authoring and dimensional compatibility only; method SDK unfinished',
    'tests': result.testsRun, 'python': platform.python_version(),
    'seconds': round(time.monotonic()-started, 3),
    'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report['status'] == 'passed' else 1)

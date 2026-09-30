"""Shared wire vectors applied to the installed package's bundled validator.

This proves resource/behavior parity; it is not an independent implementation.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slean import contract

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT/'conformance/fixtures'


def patch(value, operation):
    parts = [part.replace('~1', '/').replace('~0', '~') for part in operation['path'].split('/')[1:]]
    for part in parts[:-1]:
        value = value[int(part)] if isinstance(value, list) else value[part]
    key = int(parts[-1]) if isinstance(value, list) else parts[-1]
    if operation['op'] == 'remove':
        del value[key]
    else:
        value[key] = deepcopy(operation['value'])


class RuntimeVectors(unittest.TestCase):
    def test_shared_positive_modules_preserve_declared_evidence(self):
        paths = list(FIXTURES.glob('*/slean-module.json'))
        self.assertEqual(len(paths), 3)
        for path in paths:
            report = contract.check(contract.load(path.read_text()), path.parent)
            self.assertEqual(report['imported_evidence'], 'declared')
            self.assertEqual(report['scientific_verification'], 'not_performed')

    def test_shared_negative_vectors(self):
        cases = json.loads((ROOT/'conformance/negative-cases.json').read_text())
        self.assertEqual(len(cases), 41)
        for case in cases:
            with self.subTest(case=case['id']):
                if 'raw_json' in case:
                    with self.assertRaises(contract.ContractError) as error:
                        contract.load(case['raw_json'])
                else:
                    with tempfile.TemporaryDirectory() as temporary:
                        directory = Path(temporary)/'module'
                        shutil.copytree(FIXTURES/case['fixture'], directory)
                        value = contract.load((directory/'slean-module.json').read_text())
                        for operation in case['operations']: patch(value, operation)
                        for name, content in case.get('payload_replacements', {}).items():
                            (directory/name).write_text(json.dumps(content))
                        if case.get('update_payloads'):
                            for item in value['payloads']:
                                raw = (directory/item['path']).read_bytes()
                                item.update(size=str(len(raw)), sha256=hashlib.sha256(raw).hexdigest())
                        if case.get('rehash', True): value['id'] = contract.identity(value)
                        with self.assertRaises(contract.ContractError) as error:
                            contract.check(value, directory)
                self.assertEqual(error.exception.code, case['expected_error'])

    def test_shared_requirement_truth_table(self):
        vectors = json.loads((ROOT/'conformance/requirement-vectors.json').read_text())
        self.assertEqual(len(vectors), 34)
        for vector in vectors:
            self.assertEqual(contract.aggregate(vector['operator'], vector['inputs']), vector['expected'])


if __name__ == '__main__': unittest.main()

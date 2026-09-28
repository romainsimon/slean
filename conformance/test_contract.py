from copy import deepcopy
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from contract import ContractError, ROOT, SCHEMAS, aggregate, check, identity, load
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent


def patch(value, operation):
    parts = [p.replace('~1', '/').replace('~0', '~') for p in operation['path'].split('/')[1:]]
    for part in parts[:-1]:
        value = value[int(part)] if isinstance(value, list) else value[part]
    key = int(parts[-1]) if isinstance(value, list) else parts[-1]
    if operation['op'] == 'remove':
        del value[key]
    else:
        value[key] = deepcopy(operation['value'])


class ContractFixtures(unittest.TestCase):
    def test_schemas_and_authoring_signatures(self):
        for schema in SCHEMAS.values():
            Draft202012Validator.check_schema(schema)
        ast.parse((ROOT / 'spec/authoring.pyi').read_text())

    def test_positive_modules_and_untrusted_evidence(self):
        for path in sorted((HERE / 'fixtures').glob('*/slean-module.json')):
            with self.subTest(fixture=path.parent.name):
                result = check(load(path.read_text()), path.parent)
                self.assertEqual(result['wire'], 'valid')
                self.assertEqual(result['unsupported'], [])
                self.assertEqual(result['scientific_verification'], 'not_performed')
                self.assertEqual(result['imported_evidence'], 'declared')

    def test_negative_vectors(self):
        cases = json.loads((HERE / 'negative-cases.json').read_text())
        for case in cases:
            with self.subTest(case=case['id']):
                if 'raw_json' in case:
                    with self.assertRaises(ContractError) as error:
                        load(case['raw_json'])
                else:
                    with tempfile.TemporaryDirectory(prefix='slean-contract-') as temporary:
                        directory = Path(temporary) / 'module'
                        shutil.copytree(HERE / 'fixtures' / case['fixture'], directory)
                        value = load((directory / 'slean-module.json').read_text())
                        for operation in case['operations']:
                            patch(value, operation)
                        for name, content in case.get('payload_replacements', {}).items():
                            (directory / name).write_text(json.dumps(content))
                        if case.get('update_payloads'):
                            for file in value['payloads']:
                                raw = (directory / file['path']).read_bytes()
                                file.update(size=str(len(raw)), sha256=hashlib.sha256(raw).hexdigest())
                        if case.get('rehash', True):
                            value['id'] = identity(value)
                        with self.assertRaises(ContractError) as error:
                            check(value, directory)
                self.assertEqual(error.exception.code, case['expected_error'])

    def test_requirement_truth_tables(self):
        for vector in json.loads((HERE / 'requirement-vectors.json').read_text()):
            with self.subTest(vector=vector):
                self.assertEqual(aggregate(vector['operator'], vector['inputs']), vector['expected'])
        with self.assertRaises(ContractError):
            aggregate('all', ['green'])

    def test_unknown_quantity_semantics_are_preserved_and_unsupported(self):
        directory = HERE / 'fixtures/research'
        value = load((directory / 'slean-module.json').read_text())
        uncertainty = {'kind': 'confidence_interval', 'coverage': '0.95', 'method': 'unspecified'}
        value['components'][1]['interface']['value']['parameters']['gain']['uncertainty'] = uncertainty
        value['id'] = identity(value)
        result = check(value, directory)
        self.assertIn('uncertainty:confidence_interval', result['unsupported'])
        self.assertEqual(value['components'][1]['interface']['value']['parameters']['gain']['uncertainty'], uncertainty)
        value['components'][1]['interface']['value']['parameters']['offset']['unit'] = 'unregistered_unit'
        value['id'] = identity(value)
        self.assertIn('quantity:unregistered_unit', check(value, directory)['unsupported'])

    def test_independent_javascript_identity(self):
        result = subprocess.run([os.environ.get('SLEAN_NODE', 'node'), str(HERE / 'check_identity.mjs')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_optional_unknown_data_roundtrips_but_required_profile_blocks_support(self):
        directory = HERE / 'fixtures/open-question'
        value = load((directory / 'slean-module.json').read_text())
        opaque = {'hypothesis': 'unknown meaning', 'decimals': '0.0000000000001', 'nested': [None, True, 'é']}
        value['profiles'].append({'id': 'z-example/1', 'required': False})
        value['annotations']['z-example/1'] = opaque
        value['id'] = identity(value)
        restored = load(json.dumps(value, ensure_ascii=True))
        self.assertEqual(restored['annotations']['z-example/1'], opaque)
        self.assertEqual(check(restored, directory)['unsupported'], [])
        restored['profiles'][-1]['required'] = True
        restored['id'] = identity(restored)
        self.assertIn('z-example/1', check(restored, directory)['unsupported'])

    def test_receipts_cannot_change_identity_or_become_payloads(self):
        with tempfile.TemporaryDirectory(prefix='slean-receipt-') as temporary:
            directory = Path(temporary) / 'module'
            shutil.copytree(HERE / 'fixtures/open-question', directory)
            value = load((directory / 'slean-module.json').read_text())
            original = identity(value)
            (directory / 'receipts').mkdir()
            receipt = directory / 'receipts/fake.json'
            receipt.write_text('{"verified":true,"policy":"all-science"}')
            self.assertEqual(identity(value), original)
            self.assertEqual(check(value, directory)['scientific_verification'], 'not_performed')
            raw = receipt.read_bytes()
            value['payloads'].append({'path': 'receipts/fake.json', 'size': str(len(raw)), 'sha256': hashlib.sha256(raw).hexdigest()})
            value['id'] = identity(value)
            with self.assertRaises(ContractError) as error:
                check(value, directory)
            self.assertEqual(error.exception.code, 'reserved_payload')

    def test_changed_payload_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='slean-payload-') as temporary:
            directory = Path(temporary) / 'module'
            shutil.copytree(HERE / 'fixtures/formal', directory)
            value = load((directory / 'slean-module.json').read_text())
            source = directory / 'FormalFixture.lean'
            source.write_text('theorem wire_example : False := by sorry\n')
            with self.assertRaises(ContractError) as error:
                check(value, directory)
            self.assertEqual(error.exception.code, 'payload_integrity')
            source.unlink()
            outside = Path(temporary) / 'known-test-file'
            outside.write_text('owned test data')
            source.symlink_to(outside)
            with self.assertRaises(ContractError) as error:
                check(value, directory)
            self.assertEqual(error.exception.code, 'symlink_payload')


if __name__ == '__main__':
    unittest.main(verbosity=2)

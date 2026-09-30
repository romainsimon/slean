"""Producer environment binding controls; native proofs are tested separately."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'verification'))
from reviewed_applications import producer_binding
from boundary import UnsupportedBoundary


class ProducerBindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.producer = self.root / 'producer'
        self.consumer = self.root / 'consumer'
        self.installed = self.root / 'installed'
        (self.producer / 'environment').mkdir(parents=True)
        (self.installed / 'Domain').mkdir(parents=True)
        source = b'namespace Domain\ntheorem rule : True := True.intro\nend Domain\n'
        (self.producer / 'rule.lean').write_bytes(source)
        (self.installed / 'Domain/Rule.lean').write_bytes(source)
        self.body = {'module': 'Domain.Rule', 'declaration': [['str', 'Domain'], ['str', 'rule']],
                     'source': {'path': 'rule.lean'}, 'toolchain': 'leanprover/lean4:v4.34.1'}
        self.component = {'interface': {'value': self.body}}
        self.package = {'name': 'domain', 'kind': 'dependency', 'revision': 'r1', 'url': 'https://example.invalid/domain'}
        self.producer_inputs = {'format': 'test-format', 'toolchain': '4.34.1', 'packages': [self.package],
            'modules': [{'module': 'Domain.Rule', 'imports': [], 'kind': 'source', 'package': 'domain', 'source': self.body['source']}]}
        self.consumer_inputs = {'format': 'test-format', 'toolchain': '4.34.1', 'packages': [deepcopy(self.package)],
            'modules': [{'module': 'Domain.Rule', 'imports': [], 'kind': 'dependency', 'package': 'domain',
                'compiled': [{'suffix': '.olean', 'sha256': '1' * 64, 'size': '1'}]}]}
        (self.producer / 'environment/origins.json').write_text(json.dumps({'declarations': [{
            'declaration': self.body['declaration'], 'module': 'Domain.Rule', 'source': self.body['source'],
            'compiled_sha256': '1' * 64}]}))
        self.locations = [{'name': 'domain', 'directory': self.installed}]

    def bind(self):
        (self.producer / 'environment/build-inputs.json').write_text(json.dumps(self.producer_inputs))
        return producer_binding(self.producer, self.component, self.consumer, self.consumer_inputs, self.locations)

    def test_installed_producer_binds_source_and_binary(self):
        result = self.bind()
        self.assertEqual(result[0]['mode'], 'receiver-trusted-installed-import')
        self.assertEqual(result[0]['source_sha256'], hashlib.sha256((self.producer / 'rule.lean').read_bytes()).hexdigest())
        (self.installed / 'Domain/Rule.lean').write_bytes(b'changed installed source')
        with self.assertRaisesRegex(UnsupportedBoundary, 'source differs'):
            self.bind()

    def test_selected_upstream_producer_pin_is_checked(self):
        # A selected declaration is a source snapshot, even for an upstream
        # package. Its package pin must still match the consumer environment.
        self.producer_inputs['packages'][0]['revision'] = 'different-revision'
        with self.assertRaisesRegex(UnsupportedBoundary, 'dependency pin differs'):
            self.bind()

    def test_interface_cannot_name_another_source_or_toolchain(self):
        self.body['source'] = {'path': 'another.lean'}
        with self.assertRaisesRegex(UnsupportedBoundary, 'defining source'):
            self.bind()
        self.body['source'] = {'path': 'rule.lean'}
        self.body['toolchain'] = 'leanprover/lean4:v5.0.0'
        with self.assertRaisesRegex(UnsupportedBoundary, 'interface toolchain'):
            self.bind()

    def test_duplicate_producer_module_is_unsupported(self):
        self.producer_inputs['modules'].append(deepcopy(self.producer_inputs['modules'][0]))
        with self.assertRaisesRegex(UnsupportedBoundary, 'Duplicate'):
            self.bind()


if __name__ == '__main__':
    unittest.main()

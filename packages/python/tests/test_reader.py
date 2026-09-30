"""Actual reader decisions across quantity, reference and trust boundaries."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slean.authoring import Author, QUANTITY, qualify_requirements
from slean.quantities import scalar_port
from slean.reader import Reader, INTERFACE_POLICY, INTEGRITY_POLICY, MissingReference
from test_authoring import EMPTY, SOURCE, method, typed

UNKNOWN_PROFILE = 'future-science/0.1'


def leaf(id, predicate, arguments, profile=QUANTITY):
    return {'id': id, 'leaf': {'profile': profile, 'predicate': predicate, 'arguments': arguments}}


def sensor():
    return leaf('sensor', 'equals', {'location': 'context', 'field': 'sensor', 'expected': {'literal': 'sensor-A'}})


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def reader(self, requires=EMPTY, *, interface=None, profiles=()):
        author = Author(payloads={'method.py': SOURCE}, profiles=profiles)
        if interface is None:
            component = method(author, requires=requires)
        else:
            component = author.component(id='calibration', kind='method', name='Declared method',
                interface={'profile': QUANTITY, 'value': interface}, requires=requires,
                sources=[{'path': 'method.py'}], license='Apache-2.0')
        directory = self.root/'module'
        module = author.pack(directory, publishable=[component])
        return Reader(directory), component, module

    def apply(self, reader, component, *, reading=None, context=None, bindings=None, policy=INTERFACE_POLICY):
        return reader.apply(component, bindings=bindings if bindings is not None else {'reading': typed(reading or '8.5')},
                            context=context or {}, policy=policy)

    def test_conversion_range_and_identity_keep_all_obligations(self):
        requires = {'id': 'conditions', 'all': [sensor(), leaf('range', 'range', {
            'location': 'bindings', 'field': 'reading', 'minimum': typed('0')['typed']['value'],
            'maximum': typed('10000', unit='millivolt')['typed']['value']})]}
        reader, component, module = self.reader(requires)
        bindings = {'reading': typed('8500', unit='millivolt')}
        report = self.apply(reader, component, bindings=bindings, context={'sensor': {'literal': 'sensor-A'}})
        self.assertEqual(report['compatibility'], 'compatible')
        self.assertEqual(len(report['obligations']), 3)
        self.assertEqual(report['obligations'][0]['value']['value'], '8.500')
        self.assertEqual(report['record']['component'], {'module': module, **component})
        self.assertEqual(bindings['reading']['typed']['value']['value'], '8500')
        self.assertEqual(self.apply(reader, component, reading='10.0001', context={'sensor': {'literal': 'sensor-A'}})['compatibility'], 'incompatible')
        report = self.apply(reader, component, context={'sensor': {'literal': 'sensor-B'}})
        self.assertEqual(report['compatibility'], 'incompatible')
        self.assertEqual(next(d['status'] for d in report['obligations'] if d['requirement'] == 'sensor'), 'violated')
        self.assertEqual(self.apply(reader, component)['compatibility'], 'conditional')

    def test_optional_unknown_branch_preserved_without_interpreting_argument_shapes(self):
        opaque = leaf('opaque', 'future', {'path': 'private.txt', 'nested': {'leaf': {'id': 'not-a-requirement'}}}, UNKNOWN_PROFILE)
        requires = {'id': 'alternatives', 'any': [opaque, sensor()]}
        reader, component, module = self.reader(requires, profiles=[{'id': UNKNOWN_PROFILE, 'required': False}])
        report = self.apply(reader, component, context={'sensor': {'literal': 'sensor-A'}})
        self.assertEqual(report['compatibility'], 'compatible')
        self.assertEqual(report['selections'], {'alternatives': 'sensor'})
        self.assertEqual(report['obligations'][1]['status'], 'unsupported')
        self.assertEqual(report['record']['requires'], requires)
        self.assertEqual(qualify_requirements(requires, module), requires)
        self.assertFalse((self.root/'module/private.txt').exists())
        self.assertEqual(self.apply(reader, component)['compatibility'], 'unsupported')

    def test_unknown_mandatory_profile_blocks_satisfied_alternative(self):
        requires = {'id': 'alternatives', 'any': [leaf('future', 'future', {}, UNKNOWN_PROFILE), sensor()]}
        reader, component, _ = self.reader(requires)
        report = self.apply(reader, component, context={'sensor': {'literal': 'sensor-A'}})
        self.assertEqual(report['compatibility'], 'unsupported')
        self.assertNotIn('record', report)

    def test_missing_wrong_dimension_and_unknown_units_are_distinct(self):
        reader, component, _ = self.reader(interface={'inputs': {'reading': scalar_port(dimension='voltage', unit='volt', allow_missing=True)}, 'outputs': {}})
        self.assertEqual(self.apply(reader, component, bindings={'reading': typed(None)})['compatibility'], 'conditional')
        self.assertEqual(self.apply(reader, component, bindings={})['compatibility'], 'conditional')
        self.assertEqual(self.apply(reader, component, bindings={'reading': typed('1', 'length', 'meter')})['compatibility'], 'incompatible')
        value = typed('1'); value['typed']['value']['unit'] = 'furlong'
        self.assertEqual(self.apply(reader, component, bindings={'reading': value})['compatibility'], 'unsupported')
        value = typed('1'); value['typed']['value']['uncertainty'] = {'kind': 'confidence', 'level': '0.95'}
        self.assertEqual(self.apply(reader, component, bindings={'reading': value})['compatibility'], 'unsupported')
        self.assertEqual(self.apply(reader, component, bindings={'reading': typed('1'), 'extra': {'literal': 'x'}})['compatibility'], 'incompatible')

    def test_exact_identity_and_receiver_owned_integrity_checks(self):
        author = Author(payloads={'method.py': SOURCE})
        data = author.component(id='sensor-data', kind='data', name='Sensor identity', interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY, sources=[], license='unknown')
        requires = leaf('identity', 'equals', {'location': 'context', 'field': 'sensor', 'expected': {'ref': data}})
        component = method(author, requires=requires)
        directory = self.root/'upstream'; module = author.pack(directory, publishable=[data, component])
        reader = Reader(directory)
        self.assertEqual(self.apply(reader, component, context={'sensor': {'ref': data}})['compatibility'], 'compatible')
        # Equal-looking record names in an unavailable revision do not match.
        wrong = {'module': 'sha256:'+'0'*64, **data}
        self.assertEqual(self.apply(reader, component, context={'sensor': {'ref': wrong}})['compatibility'], 'conditional')
        self.assertEqual(reader.verify(component, policy=INTEGRITY_POLICY)['outcome'], 'valid')
        self.assertEqual(reader.verify(component, policy='formal-prover/unknown')['outcome'], 'unsupported')
        (directory/'method.py').write_bytes(b'changed')
        self.assertEqual(reader.verify(component, policy=INTEGRITY_POLICY)['outcome'], 'failed')
        self.assertEqual(self.apply(reader, component)['compatibility'], 'incompatible')

    def test_tables_read_actual_csv_convert_columns_and_preserve_missing(self):
        columns = {'reading': scalar_port(dimension='voltage', unit='volt', allow_missing=True)}
        reader, component, _ = self.reader(interface={'inputs': {'samples': {'kind': 'table', 'format': 'csv', 'columns': columns}}, 'outputs': {}})
        data = Author(payloads={'samples.csv': b'reading\n8500\n""\n'})
        producer_columns = {'reading': scalar_port(dimension='voltage', unit='millivolt', allow_missing=True)}
        value = {'typed': {'profile': QUANTITY, 'value': {'kind': 'table', 'format': 'csv', 'columns': producer_columns, 'artifact': {'path': 'samples.csv'}}}}
        dataset = data.component(id='data', kind='data', name='Measurements', interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY, sources=[{'path': 'samples.csv'}], license='Apache-2.0')
        directory = self.root/'data'; module = data.pack(directory, publishable=[dataset])
        reader = Reader(self.root/'module', dependencies=[directory])
        value['typed']['value']['artifact']['module'] = module
        report = self.apply(reader, component, bindings={'samples': value})
        self.assertEqual(report['compatibility'], 'conditional')
        diagnostic = report['obligations'][0]
        self.assertEqual(diagnostic['rows'], 2)
        self.assertEqual(diagnostic['diagnostics'][0]['reason'], 'missing_value')
        wrong = deepcopy(value); wrong['typed']['value']['columns']['reading'] = scalar_port(dimension='length', unit='meter')
        self.assertEqual(self.apply(reader, component, bindings={'samples': wrong})['compatibility'], 'incompatible')
        (directory/'samples.csv').write_bytes(b'reading\n9000\n')
        report = self.apply(reader, component, bindings={'samples': value})
        self.assertEqual(report['compatibility'], 'incompatible')
        self.assertIn('payload_integrity', report['obligations'][0]['reason'])

    def test_unknown_policy_never_executes_candidate_and_imported_evidence_stays_declared(self):
        author = Author(payloads={'method.py': SOURCE})
        component = method(author)
        plan = author.plan(component, id='plan', bindings={'reading': typed('8.5')}, context={})
        execution = author.record_execution(plan, id='run', outputs={'displacement': typed('4', 'length', 'millimeter')})
        evidence = author.record_evidence(id='evidence', kind='computation', subject=execution, context={}, policy='declared-computation', implementation={'path': 'method.py'}, artifacts=[], result={'profile': QUANTITY, 'value': {'status': 'reproduced', 'numeric_representation': 'Declared decimal arithmetic', 'tolerance': typed('0', 'length', 'millimeter')['typed']['value']}})
        directory = self.root/'module'; module = author.pack(directory, publishable=[component, plan, execution, evidence])
        reader = Reader(directory)
        self.assertEqual(reader.inspect(evidence)['imported_evidence'], 'declared')
        self.assertEqual(reader.inspect(evidence)['computational_reproduction'], 'not_performed')
        self.assertEqual(reader.uses(component), [{'module': module, **plan}, {'module': module, **execution}])
        self.assertEqual(self.apply(reader, component, policy='execute-me')['compatibility'], 'unsupported')
        self.assertEqual(self.apply(reader, component)['compatibility'], 'compatible')
        # SOURCE raises if imported; all the above only read its bytes.

    def test_application_output_bindings_require_executed_record_and_exact_dependency(self):
        data = Author(payloads={'method.py': SOURCE})
        producer = method(data)
        plan = data.plan(producer, id='first', bindings={'reading': typed('8.5')}, context={})
        execution = data.record_execution(plan, id='run', outputs={'displacement': typed('4', 'length', 'millimeter')})
        directory = self.root/'producer'; revision = data.pack(directory, publishable=[producer, plan, execution])
        reader, component, _ = self.reader(interface={'inputs': {'reading': scalar_port(dimension='length', unit='meter')}, 'outputs': {}})
        reader = Reader(self.root/'module', dependencies=[directory])
        binding = {'ref': {'module': revision, **execution}, 'output': 'displacement'}
        self.assertEqual(self.apply(reader, component, bindings={'reading': binding})['compatibility'], 'compatible')
        binding['ref'] = {'module': revision, **plan}
        self.assertEqual(self.apply(reader, component, bindings={'reading': binding})['compatibility'], 'incompatible')
        self.assertRaises(MissingReference, reader.inspect, {'module': 'sha256:'+'1'*64, 'id': 'calibration'})

    def test_applicability_stays_contextual_and_parameter_uncertainty_is_not_ignored(self):
        author = Author(payloads={'method.py': SOURCE})
        claim = author.component(id='physical', kind='claim', name='Affine sensor assumption', interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY, sources=[], license='Apache-2.0')
        component = method(author, requires=leaf('physical-condition', 'applicability', {'claim': claim}))
        directory = self.root/'physical'; module = author.pack(directory, publishable=[claim, component])
        reader = Reader(directory)
        report = self.apply(reader, component, context={'sensor': {'literal': 'sensor-A'}})
        self.assertEqual(report['compatibility'], 'conditional')
        diagnostic = next(row for row in report['obligations'] if row['requirement'] == 'physical-condition')
        self.assertEqual(diagnostic['claim'], {'module': module, **claim})
        self.assertEqual(diagnostic['context'], {'sensor': {'literal': 'sensor-A'}})
        parameter = typed('2', 'gain', 'volt/millimeter')['typed']['value']
        parameter['uncertainty'] = {'kind': 'confidence_interval', 'coverage': '0.95'}
        reader, component, _ = self.reader(interface={'inputs': {}, 'outputs': {}, 'parameters': {'gain': parameter}})
        report = self.apply(reader, component, bindings={})
        self.assertEqual(report['compatibility'], 'unsupported')
        self.assertEqual(report['obligations'][0]['reason'], 'unsupported_uncertainty')


if __name__ == '__main__': unittest.main()

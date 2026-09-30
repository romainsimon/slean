"""Real reviewed Python calls, multiple dimensions and isolation controls."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slean.authoring import Author, QUANTITY
from slean.execution import Executor, POLICY, output_policy
from slean.interfaces import equals_requirement, table, table_port
from slean.quantities import scalar_port
from slean.reader import Reader
from test_authoring import EMPTY, UNKNOWN, typed

SOURCE = b'''from decimal import Decimal
import pint
UNITS = pint.UnitRegistry(non_int_type=Decimal)
def calibrate(samples):
    points = [(row["displacement"].to("millimeter").magnitude, row["voltage"].to("volt").magnitude) for row in samples]
    if len(points) < 2: raise ValueError("insufficient_calibration_data")
    mean_x = sum(x for x,y in points)/len(points)
    mean_y = sum(y for x,y in points)/len(points)
    denominator = sum((x-mean_x)**2 for x,y in points)
    if not denominator: raise ValueError("insufficient_calibration_variation")
    gain = sum((x-mean_x)*(y-mean_y) for x,y in points)/denominator
    offset = mean_y-gain*mean_x
    return {"gain": UNITS.Quantity(gain,"volt/millimeter"), "offset": UNITS.Quantity(offset,"volt")}
'''


@unittest.skipUnless(sys.platform == 'darwin', 'Reviewed execution backend is macOS')
class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def fixture(self, source=SOURCE, *, symbol='calibrate', inputs=None, outputs=None, bindings=None, parameters=None, extra=None):
        author = Author(payloads={'method.py': source, 'calibration.csv': b'displacement,voltage\n0,500\n1,2500\n2,4500\n'})
        columns = {'displacement': scalar_port(dimension='length', unit='millimeter'), 'voltage': scalar_port(dimension='voltage', unit='millivolt')}
        if bindings is None:
            bindings = {'samples': {'typed': {'profile': QUANTITY, 'value': table({'path': 'calibration.csv'}, columns)}}}
        ports = {'displacement': scalar_port(dimension='length', unit='millimeter'), 'voltage': scalar_port(dimension='voltage', unit='volt')}
        component = author.component(id='fit', kind='method', name='Synthetic sensor calibration',
            interface={'profile': QUANTITY, 'value': {'inputs': inputs if inputs is not None else {'samples': table_port(ports)},
                'outputs': outputs if outputs is not None else {'gain': scalar_port(dimension='gain', unit='volt/millimeter'), 'offset': scalar_port(dimension='voltage', unit='volt')},
                'parameters': parameters or {}, 'entrypoint': {'artifact': {'path': 'method.py'}, 'symbol': symbol}}},
            requires=EMPTY, sources=[{'path': 'method.py'}], license='unknown')
        plan = author.plan(component, id='plan', bindings=bindings, context={}, extra_requirements=extra)
        directory = self.root/'module'
        module = author.pack(directory, publishable=[component, plan])
        options = {'policy': POLICY, 'expected_component': {'module': module, **component}, 'reviewed_source_sha256': hashlib.sha256(source).hexdigest()}
        return author, plan, Executor(Reader(directory)), options

    def test_actual_calibration_and_per_output_reproduction(self):
        author, plan, executor, options = self.fixture()
        result = executor.run(plan, **options)
        self.assertEqual(result['outcome'], 'executed', result)
        self.assertEqual(result['outputs']['gain']['typed']['value']['value'], '2.000')
        self.assertEqual(result['outputs']['offset']['typed']['value']['value'], '0.500')
        self.assertEqual(result['outputs']['gain']['typed']['value']['uncertainty'], UNKNOWN)
        self.assertEqual(result['numeric_representation']['output_magnitude_types'], {'gain': 'Decimal', 'offset': 'Decimal'})
        execution = author.record_execution(plan, id='run', outputs=result['outputs'])
        directory = self.root/'executed'; revision = author.pack(directory, publishable=[{'id': 'fit'}, plan, execution])
        options['expected_component']['module'] = revision
        executor = Executor(Reader(directory))
        tolerances = {'gain': typed('0', 'gain', 'volt/millimeter')['typed']['value'], 'offset': typed('0', 'voltage', 'volt')['typed']['value']}
        reproduced = executor.reproduce(execution, tolerances=tolerances, **options)
        self.assertEqual(reproduced['outcome'], 'reproduced', reproduced)
        self.assertEqual(set(reproduced['comparisons']), {'gain', 'offset'})
        wrong = deepcopy(tolerances); wrong['gain'] = wrong['offset']
        self.assertEqual(executor.reproduce(execution, tolerances=wrong, **options)['outcome'], 'unsupported')
        self.assertEqual(executor.reproduce(execution, tolerances={}, **options)['outcome'], 'unsupported')

    def test_receiver_source_revision_and_stricter_conditions_cannot_be_bypassed(self):
        extra = equals_requirement('extra', location='context', field='sensor', expected={'literal': 'sensor-A'})
        _, plan, executor, options = self.fixture(extra=extra)
        self.assertEqual(executor.run(plan, **options)['outcome'], 'conditional')
        report = executor.run(plan, allow_conditional=True, **options)
        # The missing context cannot become a numerical execution assumption.
        self.assertEqual(report['outcome'], 'conditional', report)
        wrong = {**options, 'reviewed_source_sha256': '0'*64}
        self.assertEqual(executor.run(plan, **wrong)['outcome'], 'rejected')
        wrong = {**options, 'expected_component': {'module': 'sha256:'+'0'*64, 'id': 'fit'}}
        self.assertEqual(executor.run(plan, **wrong)['outcome'], 'rejected')
        self.assertEqual(executor.run(plan, **{**options, 'policy': 'unknown'})['outcome'], 'unsupported')

    def test_wrong_output_dimension_is_rejected_after_actual_call(self):
        source = b'def compute(reading):\n return {"gain":reading,"offset":reading}\n'
        _, plan, executor, options = self.fixture(source, symbol='compute', inputs={'reading': scalar_port(dimension='voltage', unit='volt')}, bindings={'reading': typed('8.5')})
        result = executor.run(plan, **options)
        self.assertEqual(result['outcome'], 'failed', result)
        self.assertIn('wrong physical dimension', result['diagnostics'][0])

    def test_read_write_network_and_fork_are_denied(self):
        foreign = self.root/'private-owned-test.txt'; foreign.write_text('Owned private test data')
        source = ('import os, socket\nfrom decimal import Decimal\nimport pint\n'
            'def controls():\n'
            ' results=[]\n'
            f' for operation in [lambda:open({str(foreign)!r}).read(),lambda:open("new.txt","w"),lambda:socket.socket().connect(("127.0.0.1",9)),lambda:os.fork()]:\n'
            '  try: operation();results.append("allowed")\n'
            '  except PermissionError: results.append("denied")\n'
            ' return {"controls":",".join(results)}\n').encode()
        _, plan, executor, options = self.fixture(source, symbol='controls', inputs={}, outputs={'controls': {'kind': 'text'}}, bindings={})
        result = executor.run(plan, **options)
        self.assertEqual(result['outcome'], 'executed', result)
        self.assertEqual(result['outputs']['controls']['literal'], 'denied,denied,denied,denied')
        self.assertEqual(foreign.read_text(), 'Owned private test data')

    def test_timeout_and_output_limit_are_not_reported_as_semantic_failures(self):
        for name, source, outcome in [('timeout', b'def work():\n while True: pass\n', 'timeout'),
            ('output', b'def work():\n print("x"*2000000)\n return {}\n', 'output_limit')]:
            with self.subTest(name=name):
                if (self.root/'module').exists():
                    # Each case gets a separate owned fixture, never a retry of a live process.
                    self.root = self.root/name; self.root.mkdir()
                _, plan, executor, options = self.fixture(source, symbol='work', inputs={}, outputs={}, bindings={})
                result = executor.run(plan, timeout=2, **options)
                self.assertEqual(result['outcome'], outcome, result)

    def test_imported_output_claim_requires_fresh_call_and_receiver_selected_rule(self):
        import json
        author, plan, executor, options = self.fixture()
        actual = executor.run(plan, **options)
        self.assertEqual(actual['outcome'], 'executed', actual)
        run = author.record_execution(plan, id='run', outputs=actual['outputs'])
        execution_directory = self.root/'executed'
        revision = author.pack(execution_directory, publishable=[{'id': 'fit'}, plan, run])
        options['expected_component']['module'] = revision
        verifier = Author(dependencies=[execution_directory])
        tolerance = typed('0', 'gain', 'volt/millimeter')['typed']['value']
        evidence = verifier.record_evidence(id='gain-evidence', kind='computation', subject={'module': revision, **run}, context={},
            policy=output_policy('gain'), implementation={'module': revision, 'path': 'method.py'}, artifacts=[],
            result={'profile': QUANTITY, 'value': {'status': 'reproduced', 'numeric_representation': json.dumps(actual['numeric_representation'], sort_keys=True), 'tolerance': tolerance}})
        directory = self.root/'evidence'; evidence_revision = verifier.pack(directory, publishable=[evidence])
        executor = Executor(Reader(directory, dependencies=[execution_directory]))
        selected = {'module': evidence_revision, **evidence}
        tolerances = {'gain': tolerance, 'offset': typed('0', 'voltage', 'volt')['typed']['value']}
        self.assertEqual(executor.reader.inspect(evidence)['imported_evidence'], 'declared')
        verified = executor.verify_evidence(evidence, expected_evidence=selected, tolerances=tolerances, **options)
        self.assertEqual(verified['outcome'], 'reproduced', verified)
        self.assertIn('check', verified)
        wrong = {**tolerances, 'gain': typed('1', 'gain', 'volt/millimeter')['typed']['value']}
        self.assertEqual(executor.verify_evidence(evidence, expected_evidence=selected, tolerances=wrong, **options)['outcome'], 'rejected')
        self.assertEqual(executor.verify_evidence(evidence, expected_evidence={'module': 'sha256:'+'0'*64, **evidence}, tolerances=tolerances, **options)['outcome'], 'rejected')

    def test_wrong_recorded_output_and_changed_external_plan_are_not_reproduced(self):
        author, plan, executor, options = self.fixture()
        # A well-typed invented fit is not made true by writing an execution record.
        run = author.record_execution(plan, id='wrong', outputs={'gain': typed('2', 'gain', 'volt/millimeter'), 'offset': typed('0', 'voltage', 'volt')})
        directory = self.root/'wrong'; revision = author.pack(directory, publishable=[{'id': 'fit'}, plan, run])
        options['expected_component']['module'] = revision
        executor = Executor(Reader(directory))
        tolerances = {'gain': typed('0', 'gain', 'volt/millimeter')['typed']['value'], 'offset': typed('0', 'voltage', 'volt')['typed']['value']}
        report = executor.reproduce(run, tolerances=tolerances, **options)
        self.assertEqual(report['outcome'], 'different', report)
        self.assertEqual(report['comparisons']['offset']['absolute_error'], '0.500')
        self.assertEqual(report['comparisons']['gain']['status'], 'reproduced')
        # An external plan remains exact even when the local execution points to it.
        # The mutation is an adversarial, wire-valid fixture, never a public authoring path.
        import json
        from slean import contract
        manifest = contract.load((directory/'slean-module.json').read_text())
        original_revision = contract.load((self.root/'module/slean-module.json').read_text())['id']
        manifest['applications'][1]['plan'] = {'module': original_revision, **plan}
        manifest['applications'][1]['component'] = {'module': original_revision, 'id': 'fit'}
        manifest['applications'][1]['bindings']['samples']['typed']['value']['artifact']['module'] = original_revision
        manifest['dependencies'].append(manifest['applications'][1]['plan']['module']); manifest['dependencies'].sort()
        manifest['applications'][1]['context'] = {'changed': {'literal': 'different context'}}
        manifest['id'] = contract.identity(manifest)
        (directory/'slean-module.json').write_text(json.dumps(manifest))
        options['expected_component']['module'] = original_revision
        executor = Executor(Reader(directory, dependencies=[self.root/'module']))
        result = executor.run(run, **options)
        self.assertEqual(result['outcome'], 'rejected')
        self.assertIn('plan: context', result['diagnostics'][0])


if __name__ == '__main__': unittest.main()

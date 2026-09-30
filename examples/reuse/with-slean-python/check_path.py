"""Record the numerical calibration checkpoint; research-cycle acceptance stays open."""
from copy import deepcopy
from decimal import Decimal
import datetime
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT/'packages/python'))
from slean import Author, Reader, scalar
from slean.authoring import QUANTITY, qualify_requirements
from slean.execution import Executor, POLICY
from producer import produce
from consumer import consume


def check():
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='slean-numerical-path-') as temporary:
        root = Path(temporary)
        producer = root/'producer'; produced = produce(producer)
        sample = json.loads((HERE.parent/'direct-python/fixtures/sample.json').read_text())
        destination = root/'consumer'
        accepted = consume(producer, destination, expected_calibration=produced['calibration'],
            reviewed_source_sha256=produced['reviewed_source_sha256'], sample=sample)
        assert accepted['outputs']['displacement']['typed']['value']['value'] == '4'
        assert accepted['outputs']['error_bound']['typed']['value']['value'] == '0.01'
        assert len(accepted['remaining_assumptions']) == 3 and accepted['physical_validity'] == 'not_assessed'
        assert accepted['evidence_imported_as'] == 'declared' and accepted['fresh_evidence_check'] == 'reproduced'
        alternate = deepcopy(sample)
        alternate.update(reading={'value': '8500', 'unit': 'millivolt'}, temperature={'value': '20', 'unit': 'degree_Celsius'})
        converted = consume(producer, root/'converted', expected_calibration=produced['calibration'],
            reviewed_source_sha256=produced['reviewed_source_sha256'], sample=alternate)
        assert converted['outcome'] == 'reproduced'
        assert Decimal(converted['outputs']['displacement']['typed']['value']['value']) == Decimal('4')
        dependencies = [producer/name for name in ('calibration', 'fit-producer', 'fit-plan', 'fit-result', 'fit-verification')]
        selected = {'module': produced['calibration'], 'id': 'sensor-inverse'}
        options = {'policy': POLICY, 'expected_component': selected, 'reviewed_source_sha256': produced['reviewed_source_sha256'], 'allow_conditional': True}
        def quantity(text, dimension, unit):
            return {'typed': {'profile': QUANTITY, 'value': scalar(text, dimension=dimension, unit=unit, uncertainty={'kind': 'unknown'})}}
        standard_bindings = {'reading': quantity('8.5', 'voltage', 'volt')}
        standard_context = {'sensor': {'literal': 'sensor-A'}, 'temperature': quantity('293.15', 'temperature', 'kelvin')}
        cases = []
        for id, bindings, context, outcome, reason in [
            ('wrong-dimension', {'reading': quantity('8.5', 'length', 'millimeter')}, standard_context, 'rejected', 'wrong_dimension'),
            ('outside-range', {'reading': quantity('100', 'voltage', 'volt')}, standard_context, 'rejected', 'declared_magnitude_inclusive_range'),
            ('wrong-sensor', standard_bindings, {**standard_context, 'sensor': {'literal': 'sensor-B'}}, 'rejected', 'declared_identity_comparison'),
            ('wrong-temperature', standard_bindings, {**standard_context, 'temperature': quantity('313.15', 'temperature', 'kelvin')}, 'rejected', 'declared_identity_comparison'),
            ('missing-temperature', standard_bindings, {'sensor': {'literal': 'sensor-A'}}, 'conditional', 'missing_binding')]:
            author = Author(dependencies=dependencies)
            plan = author.plan(selected, id='attempt', bindings=bindings, context=context)
            directory = root/id; author.pack(directory, publishable=[plan])
            report = Executor(Reader(directory, dependencies=dependencies)).run(plan, **options)
            assert report['outcome'] == outcome, (id, report)
            assert any(row['reason'] == reason and row['status'] != 'satisfied' for row in report['application_check']['obligations']), (id, report)
            cases.append({'id': id, 'outcome': outcome, 'diagnostic': reason})
        reader = Reader(destination/'plan', dependencies=dependencies)
        executor = Executor(reader)
        for id, overrides in [('wrong-version', {'expected_component': {'module': 'sha256:'+'0'*64, 'id': 'sensor-inverse'}}),
                              ('changed-source-approval', {'reviewed_source_sha256': '0'*64})]:
            report = executor.run({'id': 'measurement'}, **{**options, **overrides})
            assert report['outcome'] == 'rejected', (id, report)
            cases.append({'id': id, 'outcome': report['outcome'], 'diagnostic': report['diagnostics'][0]})
        blocked = executor.run({'id': 'measurement'}, **{**options, 'allow_conditional': False})
        assert blocked['outcome'] == 'conditional'
        cases.append({'id': 'unacknowledged-physical-assumptions', 'outcome': blocked['outcome']})
        bad = Author(dependencies=[*dependencies, destination/'plan'])
        execution = bad.record_execution({'module': accepted['plan'], 'id': 'measurement'}, id='wrong-result',
            outputs={'displacement': quantity('4.25', 'length', 'millimeter'), 'error_bound': quantity('0.01', 'length', 'millimeter')})
        directory = root/'omitted-offset'; bad.pack(directory, publishable=[execution])
        tolerance = quantity('0', 'length', 'millimeter')['typed']['value']
        report = Executor(Reader(directory, dependencies=[*dependencies, destination/'plan'])).reproduce(execution,
            tolerances={'displacement': tolerance, 'error_bound': tolerance}, **options)
        assert report['outcome'] == 'different' and report['comparisons']['displacement']['absolute_error'] == '0.25', report
        cases.append({'id': 'omitted-offset-output', 'outcome': 'different', 'absolute_error_mm': '0.25'})
        # A supported source does not confer support on unknown parameter uncertainty.
        original = reader.inspect(selected)['record']
        interface = deepcopy(original['interface']); interface['value']['parameters']['gain']['uncertainty'] = {'kind': 'confidence_interval', 'coverage': '0.95'}
        interface['value']['entrypoint']['artifact']['module'] = produced['calibration']
        uncertain = Author(dependencies=dependencies)
        component = uncertain.component(id='uncertain', kind='method', name='Unsupported uncertainty fixture', interface=interface,
            requires=qualify_requirements(original['requires'], produced['calibration']), sources=[{'module': produced['calibration'], 'path': 'methods.py'}], license='unknown')
        plan = uncertain.plan(component, id='attempt', bindings=standard_bindings, context=standard_context)
        directory = root/'unsupported-uncertainty'; revision = uncertain.pack(directory, publishable=[component, plan])
        report = Executor(Reader(directory, dependencies=dependencies)).run(plan, **{**options, 'expected_component': {'module': revision, **component}})
        assert report['outcome'] == 'unsupported', report
        cases.append({'id': 'unsupported-parameter-uncertainty', 'outcome': report['outcome']})
        module_files = [path for path in root.rglob('*') if path.is_file()]
        bytes_written = sum(path.stat().st_size for path in module_files)
    frozen = json.loads((HERE.parent/'frozen-baseline.json').read_text())
    for relative, expected in frozen['sha256'].items():
        assert hashlib.sha256((HERE.parent/relative).read_bytes()).hexdigest() == expected, relative
    paths = [*sorted(HERE.glob('*.py')), *sorted((ROOT/'packages/python/slean').glob('*.py')),
             *sorted((ROOT/'packages/python/slean/data').glob('*.json')), ROOT/'packages/python/generate_runtime.py']
    return {'status': 'passed', 'observed_date': datetime.date.today().isoformat(), 'scope': 'Numerical calibration-to-measurement checkpoint; SR-T08 research cycle, formal bridge and Gate U remain open',
        'producer': produced, 'consumer': accepted, 'dimensional_conversion': converted['outcome'], 'negative_cases': cases,
        'frozen_files_unchanged': len(frozen['sha256']), 'seconds': round(time.monotonic()-started, 3),
        'temporary_artifact_files': len(module_files), 'temporary_artifact_bytes': bytes_written,
        'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}


if __name__ == '__main__': print(json.dumps(check(), indent=2, sort_keys=True))

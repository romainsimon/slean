"""Author and actually run a calibration; export the reusable inverse method."""
import hashlib
import json
from pathlib import Path

from slean import Author, Reader, scalar, scalar_port, table, table_port, equals_requirement, range_requirement, applicability_requirement
from slean.authoring import QUANTITY, RESEARCH
from slean.execution import Executor, POLICY

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent/'direct-python/fixtures'
EMPTY = {'id': 'conditions', 'all': []}
UNKNOWN = {'kind': 'unknown'}


def value(text, dimension, unit):
    return scalar(text, dimension=dimension, unit=unit, uncertainty=UNKNOWN)


def produce(destination):
    destination = Path(destination); destination.mkdir(parents=True)
    source = (HERE/'methods.py').read_bytes()
    reviewed = hashlib.sha256(source).hexdigest()  # Owned example source reviewed by this caller.
    columns = {'displacement_mm': scalar_port(dimension='length', unit='millimeter'),
               'voltage_V': scalar_port(dimension='voltage', unit='volt')}
    producer = Author(payloads={'methods.py': source, 'calibration.csv': (FROZEN/'calibration.csv').read_bytes()})
    dataset = producer.component(id='data', kind='data', name='Frozen synthetic calibration observations',
        interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY,
        sources=[{'path': 'calibration.csv'}], license='unknown')
    method = producer.component(id='fit', kind='method', name='Affine least-squares calibration',
        interface={'profile': QUANTITY, 'value': {'inputs': {'samples': table_port(columns)},
            'outputs': {'gain': scalar_port(dimension='gain', unit='volt/millimeter'), 'offset': scalar_port(dimension='voltage', unit='volt')},
            'entrypoint': {'artifact': {'path': 'methods.py'}, 'symbol': 'calibrate'}}}, requires=EMPTY,
        sources=[{'path': 'methods.py'}], license='unknown')
    upstream = destination/'fit-producer'; fit_revision = producer.pack(upstream, publishable=[dataset, method])
    planner = Author(dependencies=[upstream])
    selected = {'module': fit_revision, **method}
    plan = planner.plan(selected, id='fit-plan', bindings={'samples': {'typed': {'profile': QUANTITY,
        'value': table({'module': fit_revision, 'path': 'calibration.csv'}, columns)}}}, context={})
    plan_directory = destination/'fit-plan'; plan_revision = planner.pack(plan_directory, publishable=[plan])
    executor = Executor(Reader(plan_directory, dependencies=[upstream]))
    run = executor.run(plan, policy=POLICY, expected_component=selected, reviewed_source_sha256=reviewed)
    if run['outcome'] != 'executed': raise RuntimeError(run)
    results = Author(dependencies=[upstream, plan_directory])
    execution = results.record_execution({'module': plan_revision, **plan}, id='fit-run', outputs=run['outputs'])
    results.payload('fit-run.json', json.dumps(run, sort_keys=True).encode())
    # One selected output per evidence policy: gain and offset have different
    # dimensions. Imported status remains an attributed declaration.
    evidences = []
    for name, dimension, unit in [('gain', 'gain', 'volt/millimeter'), ('offset', 'voltage', 'volt')]:
        evidences.append(results.record_evidence(id=name+'-execution', kind='computation', subject=execution, context={},
            policy=POLICY+'#output='+name, implementation={'module': fit_revision, 'path': 'methods.py'},
            artifacts=[{'path': 'fit-run.json'}], result={'profile': QUANTITY, 'value': {'status': 'unsupported',
                'numeric_representation': json.dumps(run['numeric_representation'], sort_keys=True), 'tolerance': value('0', dimension, unit)}}))
    result_directory = destination/'fit-result'; result_revision = results.pack(result_directory, publishable=[execution, *evidences])
    tolerances = {'gain': value('0', 'gain', 'volt/millimeter'), 'offset': value('0', 'voltage', 'volt')}
    reproduced = Executor(Reader(result_directory, dependencies=[upstream, plan_directory])).reproduce(execution, tolerances=tolerances,
        policy=POLICY, expected_component=selected, reviewed_source_sha256=reviewed)
    if reproduced['outcome'] != 'reproduced': raise RuntimeError(reproduced)
    (destination/'fit-reproduction.json').write_text(json.dumps(reproduced, indent=2, sort_keys=True)+'\n')
    verification = Author(dependencies=[upstream, result_directory], payloads={'fit-reproduction.json': json.dumps(reproduced, sort_keys=True).encode()})
    verified = []
    for name in ('gain', 'offset'):
        verified.append(verification.record_evidence(id=name+'-reproduction', kind='computation', subject={'module': result_revision, **execution}, context={},
            policy=POLICY+'#output='+name, implementation={'module': fit_revision, 'path': 'methods.py'}, artifacts=[{'path': 'fit-reproduction.json'}],
            result={'profile': QUANTITY, 'value': {'status': reproduced['comparisons'][name]['status'],
                'numeric_representation': json.dumps(reproduced['numeric_representation'], sort_keys=True), 'tolerance': tolerances[name]}}))
    verification_directory = destination/'fit-verification'
    verification_revision = verification.pack(verification_directory, publishable=verified)
    calibration = Author(payloads={'methods.py': source}, dependencies=[upstream, result_directory, verification_directory])
    assumptions = []
    for id, name in [('affine-assumption', 'The selected sensor follows this affine response at the declared context'),
        ('gain-assumption', 'The conditional error calculation treats the fitted gain as exact; its physical uncertainty remains unknown'),
        ('residual-assumption', 'Voltage residual is assumed bounded by 0.02 V in the selected context')]:
        assumption = calibration.component(id=id, kind='claim', name=name,
            interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY,
            sources=[{'module': result_revision, 'path': 'fit-run.json'}], license='unknown', annotations={RESEARCH: {'role': 'hypothesis'}})
        assumptions.append(applicability_requirement(id+'-required', claim=assumption))
    requires = {'id': 'conditions', 'all': [equals_requirement('sensor', location='context', field='sensor', expected={'literal': 'sensor-A'}),
        equals_requirement('temperature', location='context', field='temperature', expected={'typed': {'profile': QUANTITY, 'value': value('293.15', 'temperature', 'kelvin')}}),
        range_requirement('voltage-range', location='bindings', field='reading', minimum=value('0.5', 'voltage', 'volt'), maximum=value('10.5', 'voltage', 'volt')), *assumptions]}
    inverse = calibration.component(id='sensor-inverse', kind='method', name='Synthetic calibrated sensor inverse',
        interface={'profile': QUANTITY, 'value': {'inputs': {'reading': scalar_port(dimension='voltage', unit='volt')},
            'outputs': {'displacement': scalar_port(dimension='length', unit='millimeter'), 'error_bound': scalar_port(dimension='length', unit='millimeter')},
            'parameters': {**{name: run['outputs'][name]['typed']['value'] for name in ('gain', 'offset')}, 'residual_bound': value('0.02', 'voltage', 'volt')},
            'entrypoint': {'artifact': {'path': 'methods.py'}, 'symbol': 'inverse'}}}, requires=requires,
        sources=[{'path': 'methods.py'}, {'module': fit_revision, 'path': 'calibration.csv'}, {'module': result_revision, 'path': 'fit-run.json'}, {'module': verification_revision, 'path': 'fit-reproduction.json'}],
        license='unknown', annotations={RESEARCH: {'role': 'method', 'motivated_by': {'module': result_revision, **execution}}})
    calibration_directory = destination/'calibration'
    revision = calibration.pack(calibration_directory, publishable=[{'id': leaf['leaf']['arguments']['claim']['id']} for leaf in assumptions]+[inverse])
    return {'calibration': revision, 'fit_producer': fit_revision, 'fit_plan': plan_revision, 'fit_result': result_revision, 'fit_verification': verification_revision,
        'reviewed_source_sha256': reviewed, 'fit_outcome': reproduced['outcome'], 'fixture': 'synthetic; no physical validation'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(produce(args.destination), indent=2, sort_keys=True))

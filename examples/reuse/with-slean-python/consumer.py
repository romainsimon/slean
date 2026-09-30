"""A separate investigation uses the exported method without producer helpers."""
import hashlib
import json
from pathlib import Path

from slean import Author, Reader, scalar
from slean.authoring import QUANTITY
from slean.execution import Executor, POLICY


def consume(producer_directory, destination, *, expected_calibration, reviewed_source_sha256, sample):
    producer_directory, destination = Path(producer_directory), Path(destination)
    dependencies = [producer_directory/name for name in ('calibration', 'fit-producer', 'fit-plan', 'fit-result', 'fit-verification')]
    selected = {'module': expected_calibration, 'id': 'sensor-inverse'}
    author = Author(dependencies=dependencies)
    def binding(record, dimension):
        return {'typed': {'profile': QUANTITY, 'value': scalar(record['value'], dimension=dimension,
            unit=record['unit'], uncertainty={'kind': 'unknown'})}}
    plan = author.plan(selected, id='measurement', bindings={'reading': binding(sample['reading'], 'voltage')},
        context={'sensor': {'literal': sample['sensor']}, 'temperature': binding(sample['temperature'], 'temperature')})
    plan_directory = destination/'plan'; plan_revision = author.pack(plan_directory, publishable=[plan])
    reader = Reader(plan_directory, dependencies=dependencies)
    options = {'policy': POLICY, 'expected_component': selected, 'reviewed_source_sha256': reviewed_source_sha256, 'allow_conditional': True}
    run = Executor(reader).run(plan, **options)
    if run['outcome'] != 'executed': raise RuntimeError(run)
    result = Author(dependencies=[*dependencies, plan_directory])
    execution = result.record_execution({'module': plan_revision, **plan}, id='measurement-result', outputs=run['outputs'])
    result.payload('execution.json', json.dumps(run, sort_keys=True).encode())
    evidence = result.record_evidence(id='displacement-execution', kind='computation', subject=execution, context=run['application_check']['record']['context'],
        policy=POLICY+'#output=displacement', implementation={'module': expected_calibration, 'path': 'methods.py'}, artifacts=[{'path': 'execution.json'}],
        result={'profile': QUANTITY, 'value': {'status': 'unsupported', 'numeric_representation': json.dumps(run['numeric_representation'], sort_keys=True),
            'tolerance': scalar('0', dimension='length', unit='millimeter', uncertainty={'kind': 'unknown'})}})
    directory = destination/'result'; revision = result.pack(directory, publishable=[execution, evidence])
    second = Reader(directory, dependencies=[*dependencies, plan_directory])
    tolerance = scalar('0', dimension='length', unit='millimeter', uncertainty={'kind': 'unknown'})
    repeated = Executor(second).reproduce(execution, tolerances={'displacement': tolerance, 'error_bound': tolerance}, **options)
    if repeated['outcome'] != 'reproduced': raise RuntimeError(repeated)
    verification = Author(dependencies=[*dependencies, directory], payloads={'reproduction.json': json.dumps(repeated, sort_keys=True).encode()})
    proofs = []
    for name in ('displacement', 'error_bound'):
        proofs.append(verification.record_evidence(id=name+'-reproduction', kind='computation', subject={'module': revision, **execution},
            context=second.inspect(execution)['record']['context'], policy=POLICY+'#output='+name,
            implementation={'module': expected_calibration, 'path': 'methods.py'}, artifacts=[{'path': 'reproduction.json'}],
            result={'profile': QUANTITY, 'value': {'status': repeated['comparisons'][name]['status'],
                'numeric_representation': json.dumps(repeated['numeric_representation'], sort_keys=True), 'tolerance': tolerance}}))
    verification_revision = verification.pack(destination/'verification', publishable=proofs)
    evidence_reader = Reader(destination/'verification', dependencies=[*dependencies, directory, plan_directory])
    fresh = Executor(evidence_reader).verify_evidence({'id': 'displacement-reproduction'},
        expected_evidence={'module': verification_revision, 'id': 'displacement-reproduction'},
        tolerances={'displacement': tolerance, 'error_bound': tolerance}, **options)
    if fresh['outcome'] != 'reproduced': raise RuntimeError(fresh)
    return {'module': revision, 'verification': verification_revision, 'plan': plan_revision, 'outcome': repeated['outcome'], 'outputs': repeated['outputs'],
        'remaining_assumptions': [row for row in repeated['application_check']['obligations'] if row['status'] == 'unresolved'],
        'uses': second.uses(selected), 'evidence_imported_as': second.inspect(evidence)['imported_evidence'],
        'invocation_sha256': repeated['invocation_sha256'], 'comparison_sha256': repeated['comparison_sha256'],
        'fresh_evidence_check': fresh['outcome'], 'physical_validity': 'not_assessed'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('producer', type=Path); parser.add_argument('destination', type=Path); parser.add_argument('sample', type=Path)
    parser.add_argument('--expected-calibration', required=True); parser.add_argument('--reviewed-source-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(consume(args.producer, args.destination, expected_calibration=args.expected_calibration,
        reviewed_source_sha256=args.reviewed_source_sha256, sample=json.loads(args.sample.read_text())), indent=2, sort_keys=True))

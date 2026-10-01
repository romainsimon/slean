"""Run the numerical investigation, generate its Lean links and verify them."""
from copy import deepcopy
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PYTHON_EXAMPLE = HERE.parent/'with-slean-python'
LEAN = ROOT/'packages/lean'
for path in (ROOT/'conformance', LEAN, LEAN/'verification', ROOT/'packages/python', PYTHON_EXAMPLE):
    sys.path.insert(0, str(path))
from slean import Reader, scalar
from slean.execution import Executor, POLICY as NUMERICAL_POLICY
from cycle import run_cycle
from consumer import consume
import bridge
import export
from reviewed_applications import verify, inspect_application
from receipts import ReceiptStore, POLICY as FORMAL_POLICY

LAKE = os.environ.get('SLEAN_LAKE', str(Path.home()/'.elan/bin/lake'))
ENV = {**os.environ, 'ELAN_TOOLCHAIN': 'leanprover/lean4:v4.34.1'}
OUT = HERE/'_out'


def native(label, arguments, *, errors=()):
    start = time.monotonic()
    process = subprocess.Popen([LAKE, *arguments], cwd=HERE, env=ENV,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        text, _ = process.communicate(timeout=600)
    except BaseException:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=10)
        raise
    (OUT/(label+'.log')).write_text(text)
    if 'PANIC' in text or (not errors and process.returncode != 0) or (
            errors and (process.returncode == 0 or any(error not in text for error in errors))):
        raise RuntimeError(label+' failed; inspect '+str(OUT/(label+'.log'))+'\n'+text[-5000:])
    print(label+': '+('rejected as expected' if errors else 'passed'), file=sys.stderr, flush=True)
    return {'check': label, 'status': 'rejected_as_expected' if errors else 'passed',
            'seconds': round(time.monotonic()-start, 3)}


def formal_refs(manifest):
    refs = {}
    for component in manifest['components']:
        name = [part[1] for part in component['interface']['value']['declaration']]
        label, suffix = name[-1].split('_', 1)
        refs.setdefault(label, {})[suffix] = {'module': manifest['id'], 'id': component['id']}
    return refs


def check():
    started = time.monotonic(); OUT.mkdir(exist_ok=True)
    # Reuse installed dependency binaries. No downloads, cache copy or new VM.
    installed = HERE.parent/'with-slean-lean/.lake/packages'
    cache = HERE/'.lake/packages'; cache.mkdir(parents=True, exist_ok=True)
    lock = json.loads((HERE/'lake-manifest.json').read_text())
    for package in lock['packages']:
        if package['type'] != 'git': continue
        name = package['name'].strip('«»')
        target = (installed/name).resolve(strict=True)
        link = cache/name
        if not link.exists() and not link.is_symlink(): link.symlink_to(target, target_is_directory=True)
        if link.resolve(strict=True) != target: raise RuntimeError('Unexpected installed dependency: '+name)
    with tempfile.TemporaryDirectory(prefix='slean-affine-bridge-') as temporary:
        root = Path(temporary)
        investigation = root/'investigation'
        cycle = run_cycle(investigation)
        dependencies = [investigation/path for path in cycle['directories']]
        calibration = Reader(investigation/'producer/calibration', dependencies=dependencies).module
        reviewed_source = cycle['reused_method_source_sha256']
        original = consume(investigation/'producer', root/'measurement', expected_calibration=calibration,
            reviewed_source_sha256=reviewed_source,
            sample=json.loads((HERE.parent/'direct-python/fixtures/sample.json').read_text()))
        dependencies.extend(root/'measurement'/name for name in ('plan', 'result', 'verification'))
        reader = Reader(root/'measurement/result', dependencies=dependencies)
        executions = {'original': {'module': original['module'], 'id': 'measurement-result'},
                      'revised': cycle['retry_run']}
        mappings, reproductions = {}, {}
        zero = scalar('0', dimension='length', unit='millimeter', uncertainty={'kind': 'unknown'})
        for label, execution in executions.items():
            component = reader.inspect(execution)['record']['component']
            mappings[label] = bridge.collect(reader, execution, expected_component=component,
                reviewed_source_sha256=reviewed_source)
            reproduced = Executor(reader).reproduce(execution, tolerances={'displacement': zero, 'error_bound': zero},
                policy=NUMERICAL_POLICY, expected_component=component,
                reviewed_source_sha256=reviewed_source, allow_conditional=True)
            assert reproduced['outcome'] == 'reproduced', reproduced
            reproductions[label] = {'outcome': reproduced['outcome'], 'comparison_sha256': reproduced['comparison_sha256'],
                'invocation_sha256': reproduced['invocation_sha256']}
        print('fresh numerical reproduction and coordinate mapping: passed', file=sys.stderr, flush=True)
        generated = bridge.source(mappings)
        # This committed file is the inspectable generated example. A changed
        # numerical fixture must be reviewed as a new source/version, not silently
        # blessed by a check that overwrites the expected statement.
        if (HERE/'CalibrationApplication.lean').read_bytes() != generated:
            raise RuntimeError('Generated coordinates differ from the reviewed CalibrationApplication.lean')
        steps = [native('calibration-application', ['build', 'CalibrationApplication']),
                 native('calibration-export', ['env', 'lean', 'ExportCalibration.lean'])]
        for name, messages in [('MissingResidual', ('unsolved goals', 'residual_bound')),
                               ('MissingGain', ('unsolved goals', 'gain ≠ 0')),
                               ('ChangedNominal', ('could not unify',))]:
            steps.append(native(name, ['env', 'lean', 'negative/'+name+'.lean'], errors=messages))
        producer = export.pack(OUT/'producer.json', HERE, root/'formal-producer')
        consumer = export.pack(OUT/'consumer.json', HERE, root/'formal-consumer', applications=OUT/'applications.json',
            dependency_modules=[root/'formal-producer'])
        formal_dependencies = [*dependencies, root/'formal-producer', root/'formal-consumer']
        formal_reader = Reader(root/'formal-consumer', dependencies=formal_dependencies)
        references = formal_refs(consumer)
        selected_refs = [ref for group in references.values() for ref in group.values()]
        source_hash = bridge.check_source(formal_reader, mappings, selected_refs)
        # Source correctness alone is insufficient: reconstruct and kernel-check
        # the exact native applications before authenticating them locally.
        applications = [a['id'] for a in consumer['applications'] if a['phase'] == 'executed']
        authority = ReceiptStore(root/'authority', create=True)
        checked = verify(root/'formal-consumer', applications, dependency_modules=[root/'formal-producer'],
            dependency_project=HERE, policy=FORMAL_POLICY, store=authority)
        (OUT/'receiver.json').write_text(json.dumps(checked, indent=2, sort_keys=True)+'\n')
        assert checked['status'] == 'passed' and len(checked['receipts']) == 6, checked.get('reason')
        for receipt in checked['receipts']:
            identifier = receipt['verification']['subject']['id']
            local = inspect_application(root/'formal-consumer', identifier, receipt=receipt, store=authority)
            assert local['formal_verification'] == 'passed' and local['empirical_validity'] == 'not_assessed'
            assert inspect_application(root/'formal-consumer', identifier, receipt=receipt)['formal_verification'] == 'not_performed'
        # A genuine proof for the old model is not a link for a new offset.
        different = deepcopy(mappings)
        different['revised']['coordinates']['offset'] = bridge.coordinate(
            scalar('0.7', dimension='voltage', unit='volt', uncertainty={'kind': 'unknown'}), 'offset')
        try: bridge.check_source(formal_reader, different, selected_refs)
        except bridge.BridgeError as error: assert 'does_not_match_coordinates' in str(error)
        else: raise AssertionError('A proof for another nominal model was linked')
        revision = bridge.pack_link(root/'links', mappings, dependencies=formal_dependencies, formal_components=references)
        linked = Reader(root/'links', dependencies=formal_dependencies)
        for label in mappings:
            record = linked.inspect({'id': label})['record']
            assert record['requires']['all'][0] == mappings[label]['requires']
            assert len(mappings[label]['remaining_obligations']) == 3
            assert linked.inspect({'id': label})['formal_verification'] == 'not_performed'
        # Reload numeric objects after native verification: a stale mapping cannot
        # survive a changed module or changed payload during the long check.
        for label, execution in executions.items():
            assert bridge.collect(reader, execution, expected_component=mappings[label]['component'],
                reviewed_source_sha256=reviewed_source) == mappings[label]
        assert bridge.check_source(formal_reader, mappings, selected_refs) == source_hash
        files = [p for p in root.rglob('*') if p.is_file()]
        sizes = {'files': len(files), 'bytes': sum(p.stat().st_size for p in files)}
    frozen = json.loads((HERE.parent/'frozen-baseline.json').read_text())
    for relative, expected in frozen['sha256'].items():
        assert hashlib.sha256((HERE.parent/relative).read_bytes()).hexdigest() == expected, relative
    sources = [*sorted(HERE.glob('*.py')), *sorted(HERE.glob('*.lean')), HERE/'lakefile.toml', HERE/'lean-toolchain', HERE/'lake-manifest.json',
        *sorted((HERE/'negative').glob('*.lean')), *sorted((ROOT/'packages/python/slean').glob('*.py')),
        *sorted((ROOT/'packages/python/slean/data').glob('*.json')),
        *[LEAN/name for name in ('export.py', 'applications.py', 'build_inputs.py', 'SleanExport.lean', 'SleanExport/Application.lean', 'SleanExport/Native.lean', 'SleanAudit.lean')],
        *[LEAN/'verification'/name for name in ('reviewed.py', 'reviewed_applications.py', 'receipts.py', 'boundary.py')],
        *[PYTHON_EXAMPLE/name for name in ('cycle.py', 'producer.py', 'consumer.py', 'methods.py', 'revision_method.py')]]
    return {'status': 'passed', 'observed_date': datetime.date.today().isoformat(), 'scope': 'SR-T08 conditional affine bridge checkpoint',
        'mappings': mappings, 'numerical_reproductions': reproductions, 'native_steps': steps,
        'generated_source_sha256': source_hash, 'checked_native_applications': len(checked['receipts']),
        'formal_verification': checked['status'], 'formal_policy': FORMAL_POLICY, 'link_module': revision,
        'wrong_model_link': 'rejected', 'imported_verification': 'declared; local receiver authority required',
        'parameter_uncertainty': 'unknown', 'physical_validity': 'not_assessed', 'program_refinement': 'not_proved',
        'frozen_files_unchanged': len(frozen['sha256']), 'temporary_artifacts': sizes,
        'seconds': round(time.monotonic()-started, 3), 'gate_u': 'not_evaluated',
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2, sort_keys=True))

"""Explicit reviewed-source execution and per-output numerical reproduction.

Portable evidence is never promoted by reading this report back. Reproduction
calls the selected method again under the receiver's policy and expectations.
"""
from copy import deepcopy
import csv
from decimal import Decimal, localcontext
import hashlib
from importlib import metadata
import io
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import sysconfig
import tempfile
import time
from urllib.parse import quote, unquote

import rfc8785

from . import contract
from .authoring import QUANTITY, KNOWN_PROFILES, _walk, qualify_requirements
from .quantities import QuantityError, check_scalar, convert_scalar, _registry
from .reader import INTERFACE_POLICY

POLICY = 'reviewed-python-quantity/0.1-draft.1'
MAX_SOURCE_BYTES = 1024 * 1024
MAX_REQUEST_BYTES = 16 * 1024 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
DEPENDENCIES = ('pint', 'flexcache', 'flexparser', 'platformdirs', 'typing_extensions',
                'jsonschema', 'attrs', 'jsonschema-specifications', 'referencing', 'rpds-py', 'rfc8785')


def output_policy(name):
    """A single-output claim under the same reviewed call/comparison policy."""
    return POLICY+'#output='+quote(name, safe='')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _qualify(values, module):
    values = deepcopy(values)
    for node in _walk(values):
        if set(node) in ({'id'}, {'path'}): node['module'] = module
    return values


def _environment():
    distributions = {}
    for name in DEPENDENCIES:
        distribution = metadata.distribution(name)
        files = {str(path): _sha(distribution.locate_file(path).read_bytes())
                 for path in distribution.files or () if distribution.locate_file(path).is_file()}
        distributions[name] = {'version': distribution.version, 'files_sha256': _sha(rfc8785.dumps(files))}
    sdk = Path(__file__).resolve().parent
    files = [*sdk.glob('*.py'), *sdk.glob('data/*.json')]
    return {'python': sys.version, 'executable_sha256': _sha(Path(sys.executable).resolve().read_bytes()),
            'distributions': distributions, 'sdk': {str(path.relative_to(sdk)): _sha(path.read_bytes()) for path in sorted(files)}}


def _capture(process, timeout):
    deadline, output, reason = time.monotonic()+timeout, bytearray(), None
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        while selector.get_map():
            if time.monotonic() >= deadline:
                reason = 'timeout'; break
            for key, _ in selector.select(min(0.1, max(0, deadline-time.monotonic()))):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj); continue
                available = MAX_OUTPUT_BYTES-len(output)
                output.extend(block[:available])
                if len(block) > available:
                    reason = 'output_limit'; break
            if reason: break
    if reason:
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
    try:
        process.wait(timeout=max(0.01, deadline-time.monotonic()) if not reason else 10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
        reason = 'timeout'
    finally:
        process.stdout.close()
    return bytes(output), reason


class Executor:
    def __init__(self, reader):
        self.reader = reader

    def _argument(self, binding, descriptor, owner):
        diagnostic = self.reader._port(binding, descriptor, owner)
        if diagnostic['status'] != 'satisfied':
            raise ValueError('Execution input is not established: '+diagnostic['reason'])
        binding, owner = self.reader._binding(binding, owner)
        if descriptor['kind'] == 'text': return {'kind': 'text', 'value': binding['literal']}
        if descriptor['kind'] == 'scalar': return diagnostic['value']
        body = binding['typed']['value']
        rows = csv.DictReader(io.StringIO(self.reader._artifact(body['artifact'], owner).decode('utf-8')))
        converted = []
        for row in rows:
            values = {}
            for key, text in row.items():
                port = body['columns'][key]
                value = {'kind': 'scalar', 'dimension': port['dimension'], 'unit': port['unit'], 'value': text or None, 'uncertainty': {'kind': 'unknown'}}
                # A table may be inspectable with missing values, but this
                # numerical call policy cannot invent numbers for them.
                if value['value'] is None: raise ValueError('Missing table cell')
                values[key] = convert_scalar(value, descriptor['columns'][key]['unit'])
            converted.append(values)
        return {'kind': 'table', 'rows': converted}

    def run(self, application, *, policy, expected_component, reviewed_source_sha256,
            allow_conditional=False, precision=28, timeout=30):
        base = {'policy': policy, 'layer': 'computation', 'outcome': 'unsupported', 'diagnostics': [],
                'formal_verification': 'not_performed', 'empirical_validity': 'not_assessed'}
        if policy != POLICY:
            return {**base, 'diagnostics': ['Unknown execution policy; no fallback']}
        if sys.platform != 'darwin':
            return {**base, 'diagnostics': ['This backend requires the reviewed macOS boundary']}
        if type(precision) is not int or not 16 <= precision <= 512 or not 0 < timeout <= 120:
            return {**base, 'diagnostics': ['Unsupported numerical precision or wall-time budget']}
        before = time.monotonic()
        try:
            from ._boundary import darwin_profile, child_limits, current_limits
            app_owner, family, app = self.reader._resolve(application)
            if family != 'applications': raise ValueError('Execute an actual application record')
            selected = {'module': app['component'].get('module', app_owner), 'id': app['component']['id']}
            if expected_component != selected: raise ValueError('Receiver-selected component revision differs')
            if 'plan' in app:
                plan_owner, plan_family, plan = self.reader._resolve(app['plan'], app_owner)
                if plan_family != 'applications' or plan['phase'] != 'planned': raise ValueError('Invalid execution plan reference')
                for key in ('component', 'bindings', 'context'):
                    if _qualify(app[key], app_owner) != _qualify(plan[key], plan_owner):
                        raise ValueError('Execution changed the selected plan: '+key)
                if qualify_requirements(app['requires'], app_owner) != qualify_requirements(plan['requires'], plan_owner):
                    raise ValueError('Execution changed the selected plan requirements')
            owner, family, component = self.reader._resolve(selected)
            if family != 'components' or component['kind'] not in ('method', 'model'):
                raise ValueError('Selected record is not an executable method/model')
            if any(p['required'] and p['id'] not in KNOWN_PROFILES for p in self.reader._fresh(app_owner)['profiles']):
                raise ValueError('Unsupported mandatory application profile')
            if component['interface']['profile'] != QUANTITY: raise ValueError('Unsupported execution interface')
            interface = component['interface']['value']
            if 'entrypoint' not in interface: raise ValueError('No declared method entrypoint')
            source = self.reader._artifact(interface['entrypoint']['artifact'], owner)
            if len(source) > MAX_SOURCE_BYTES: raise ValueError('Method source exceeds the policy limit')
            if _sha(source) != reviewed_source_sha256: raise ValueError('Source differs from the explicitly reviewed bytes')
            if any(p['kind'] not in ('scalar', 'text') for p in interface['outputs'].values()):
                raise ValueError('This execution policy supports scalar/text outputs only')
            original = qualify_requirements(component['requires'], owner)
            declared = qualify_requirements(app['requires'], app_owner)
            extra = None
            if declared != original:
                if 'all' not in declared or original not in declared['all']:
                    raise ValueError('Application weakens or changes producer conditions')
                extra = {**declared, 'all': [node for node in declared['all'] if node != original]}
            bindings, context = _qualify(app['bindings'], app_owner), _qualify(app['context'], app_owner)
            compatibility = self.reader.apply(selected, bindings=bindings, context=context, policy=INTERFACE_POLICY, extra_requirements=extra)
            if compatibility['compatibility'] not in ('compatible', 'conditional'):
                return {**base, 'outcome': 'unsupported' if compatibility['compatibility'] == 'unsupported' else 'rejected', 'diagnostics': ['Application conditions are not supported or compatible'], 'application_check': compatibility}
            if compatibility['compatibility'] == 'conditional' and not allow_conditional:
                return {**base, 'outcome': 'conditional', 'diagnostics': ['Explicit acknowledgement is required for open model assumptions'], 'application_check': compatibility}
            if compatibility['compatibility'] == 'conditional':
                assumed = {node['id'] for node in _walk(compatibility['record']['requires'])
                    if node.get('leaf', {}).get('profile') == QUANTITY and node['leaf']['predicate'] == 'applicability'}
                open_checks = [row for row in compatibility['obligations'] if row['status'] == 'unresolved']
                if any(row['requirement'] not in assumed for row in open_checks):
                    return {**base, 'outcome': 'conditional', 'diagnostics': ['Missing data or scope checks cannot be assumed'], 'application_check': compatibility}
            arguments = {key: self._argument(bindings.get(key), port, app_owner) for key, port in interface['inputs'].items()}
            for key, value in interface.get('parameters', {}).items():
                if key in arguments: raise ValueError('Parameter/input names collide')
                if value['value'] is None: raise ValueError('Missing numerical parameter')
                diagnostic = check_scalar(value, {'kind': 'scalar', 'dimension': value['dimension'], 'unit': value['unit'], 'allow_missing': False})
                if diagnostic['status'] != 'satisfied': raise ValueError('Unsupported or incompatible parameter')
                arguments[key] = diagnostic['value']
            _registry()  # Establish the pinned receiver units before the environment snapshot.
            environment = _environment()
            with tempfile.TemporaryDirectory(prefix='slean-python-call-') as temporary:
                root = Path(temporary)
                runtime = root/'runtime'; (runtime/'slean/data').mkdir(parents=True)
                sdk = Path(__file__).resolve().parent
                for relative in environment['sdk']:
                    (runtime/'slean'/relative).write_bytes((sdk/relative).read_bytes())
                source_path = root/'method.py'; source_path.write_bytes(source)
                request = {'source': str(source_path), 'symbol': interface['entrypoint']['symbol'], 'arguments': arguments, 'outputs': interface['outputs'], 'precision': precision}
                request_bytes = rfc8785.dumps(request)
                if len(request_bytes) > MAX_REQUEST_BYTES: raise ValueError('Input request exceeds the policy limit')
                request_path = root/'request.json'; request_path.write_bytes(request_bytes)
                roots = [root, Path(sys.executable).resolve().parents[1], Path(sys.prefix)/'lib', Path(sysconfig.get_path('stdlib'))]
                venv_config = Path(sys.prefix)/'pyvenv.cfg'
                if venv_config.is_file(): roots.append(venv_config)
                profile = darwin_profile(roots, (), can_fork=False)
                limits = {**current_limits(), 'cpu_seconds': 30, 'file_bytes': 1024 * 1024, 'open_files': 128}
                command = ['/usr/bin/sandbox-exec', '-p', profile, sys.executable, '-I', '-B', '-c',
                    'import sys,runpy;sys.path.insert(0,sys.argv.pop(1));runpy.run_module("slean._runner",run_name="__main__")', str(runtime), str(request_path)]
                process = subprocess.Popen(command, cwd=root, env={'PATH': '/usr/bin:/bin', 'TMPDIR': str(root)},
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True, preexec_fn=lambda: child_limits(limits))
                raw, stop = _capture(process, timeout)
                if stop or process.returncode:
                    return {**base, 'outcome': stop or 'failed', 'diagnostics': [raw.decode('utf-8', errors='replace')[-4096:]],
                            'seconds': round(time.monotonic()-before, 3)}
                result = contract.load(raw.decode('utf-8'))
                if set(result) != {'outputs', 'numeric_representation'} or set(result['outputs']) != set(interface['outputs']):
                    raise ValueError('Malformed execution result')
                for name, port in interface['outputs'].items():
                    contract.schema(result['outputs'][name], 'module', 'binding')
                    diagnostic = self.reader._port(result['outputs'][name], port, app_owner)
                    if diagnostic['status'] != 'satisfied': raise ValueError('Returned output is incompatible')
                if source_path.read_bytes() != source or request_path.read_bytes() != request_bytes:
                    raise ValueError('Readonly execution inputs changed')
            self.reader._fresh(app_owner); self.reader._fresh(owner)
            if self.reader._artifact(interface['entrypoint']['artifact'], owner) != source:
                raise ValueError('Original source changed during execution')
            for key, port in interface['inputs'].items():
                self._argument(bindings.get(key), port, app_owner)
            if environment != _environment(): raise ValueError('Receiver environment changed during execution')
            invocation = {'subject': {'module': app_owner, 'id': app['id']}, 'application': app,
                          'component': selected, 'source_sha256': reviewed_source_sha256, 'environment': environment,
                          'allow_conditional': allow_conditional, 'precision': precision, 'policy': policy}
            return {**base, **result, 'outcome': 'executed', 'component': selected, 'subject': invocation['subject'],
                'application_check': compatibility, 'invocation_sha256': _sha(rfc8785.dumps(invocation)),
                'environment': environment, 'source_sha256': reviewed_source_sha256,
                'isolation': 'macos-sandbox-exec', 'network': 'denied', 'seconds': round(time.monotonic()-before, 3),
                'limits': {**limits, 'wall_seconds': timeout, 'output_bytes': MAX_OUTPUT_BYTES},
                'limitations': ['Reviewed single-file source policy; not hostile-upload qualification',
                    'No hard memory or aggregate disk quota on macOS', 'Unknown output uncertainty remains explicit',
                    'Execution does not establish physical validity or statistical adequacy']}
        except QuantityError as error:
            return {**base, 'outcome': 'unsupported' if error.unsupported else 'rejected', 'diagnostics': [str(error)]}
        except (RuntimeError, ImportError) as error:
            return {**base, 'diagnostics': [str(error)]}
        except (ValueError, OSError, KeyError, TypeError) as error:
            return {**base, 'outcome': 'rejected', 'diagnostics': [str(error)]}

    def reproduce(self, application, *, tolerances, **execution_options):
        owner, family, app = self.reader._resolve(application)
        if family != 'applications' or app['phase'] != 'executed':
            return {'outcome': 'unsupported', 'diagnostics': ['Reproduce an executed application with recorded outputs']}
        if not app['outputs']:
            return {'outcome': 'unsupported', 'diagnostics': ['No recorded observable output to reproduce']}
        if set(tolerances) != set(app['outputs']):
            return {'outcome': 'unsupported', 'diagnostics': ['Select an explicit tolerance for every output']}
        # Re-run; imported evidence and a prior report do not establish success.
        run = self.run(application, **execution_options)
        if run['outcome'] != 'executed': return run
        comparisons = {}
        for name, recorded in app['outputs'].items():
            try:
                recorded, _ = self.reader._binding(recorded, owner)
                reproduced = run['outputs'][name]
                if 'literal' in recorded and 'literal' in reproduced:
                    if tolerances[name] is not None: raise ValueError('Text output uses exact equality and a null tolerance')
                    same = type(recorded['literal']) is type(reproduced['literal']) and recorded['literal'] == reproduced['literal']
                    comparisons[name] = {'status': 'reproduced' if same else 'different', 'comparison': 'exact_text'}
                    continue
                if recorded.get('typed', {}).get('profile') != QUANTITY:
                    raise ValueError('Unsupported recorded output profile')
                target = recorded['typed']['value']
                actual = convert_scalar(reproduced['typed']['value'], target['unit'])
                expected = convert_scalar(target, target['unit'])
                tolerance = convert_scalar(tolerances[name], target['unit'])
                if any(v['value'] is None for v in (actual, expected, tolerance)) or Decimal(tolerance['value']) < 0:
                    raise ValueError('Use a nonnegative, nonmissing, dimensionally compatible tolerance')
                if tolerance['dimension'] == 'temperature':
                    raise ValueError('Temperature-difference comparisons are unsupported in this profile')
                with localcontext() as context:
                    context.prec = sum(len(v['value']) for v in (actual, expected, tolerance))+20
                    error = abs(Decimal(actual['value'])-Decimal(expected['value']))
                    same = error <= Decimal(tolerance['value'])
                comparisons[name] = {'status': 'reproduced' if same else 'different', 'absolute_error': format(error, 'f'),
                    'unit': target['unit'], 'tolerance': deepcopy(tolerances[name])}
            except (ValueError, KeyError, TypeError, QuantityError) as error:
                comparisons[name] = {'status': 'unsupported', 'reason': str(error)}
        states = [v['status'] for v in comparisons.values()]
        outcome = 'different' if 'different' in states else 'unsupported' if 'unsupported' in states else 'reproduced'
        comparison = {'invocation_sha256': run['invocation_sha256'], 'recorded_outputs': app['outputs'],
                      'tolerances': tolerances, 'comparisons': comparisons}
        return {**run, 'outcome': outcome, 'comparisons': comparisons, 'comparison_sha256': _sha(rfc8785.dumps(comparison))}

    def verify_evidence(self, evidence, *, expected_evidence, tolerances, **execution_options):
        """Recompute a pinned output-specific claim; imported status grants no trust."""
        base = {'outcome': 'unsupported', 'layer': 'computation', 'empirical_validity': 'not_assessed'}
        if execution_options.get('policy') != POLICY:
            return {**base, 'diagnostics': ['Unknown execution policy; no fallback']}
        try:
            owner, family, record = self.reader._resolve(evidence)
            if any(p['required'] and p['id'] not in KNOWN_PROFILES for p in self.reader._fresh(owner)['profiles']):
                return {**base, 'diagnostics': ['Unsupported mandatory evidence profile']}
            selected = {'module': owner, 'id': record['id']}
            if expected_evidence != selected or family != 'evidence' or record['kind'] != 'computation':
                raise ValueError('Receiver-selected computation evidence differs')
            encoded = record['method']['policy']
            if not encoded.startswith(POLICY+'#output='):
                return {**base, 'diagnostics': ['Unsupported evidence comparison policy']}
            port = unquote(encoded.split('#output=', 1)[1])
            if encoded != output_policy(port): raise ValueError('Noncanonical output policy')
            if record['result']['profile'] != QUANTITY: return {**base, 'diagnostics': ['Unsupported evidence result profile']}
            claimed = record['result']['value']
            if claimed['status'] == 'unsupported': return {**base, 'diagnostics': ['No reproduction claim is recorded']}
            if claimed['tolerance'] != tolerances.get(port): raise ValueError('Receiver tolerance differs from the claimed evaluation rule')
            app_owner, app_family, app = self.reader._resolve(record['subject'], owner)
            if app_family != 'applications' or app['phase'] != 'executed' or port not in app['outputs']:
                raise ValueError('Evidence does not select an executed output')
            component = {'module': app['component'].get('module', app_owner), 'id': app['component']['id']}
            comp_owner, _, producer = self.reader._resolve(component)
            implementation = producer['interface']['value']['entrypoint']['artifact']
            if {**record['method']['implementation'], 'module': record['method']['implementation'].get('module', owner)} != {**implementation, 'module': implementation.get('module', comp_owner)}:
                raise ValueError('Evidence implementation differs from the selected method')
            if _qualify(record['context'], owner) != _qualify(app['context'], app_owner):
                raise ValueError('Evidence context differs from the executed application')
            run = self.reproduce({'module': app_owner, 'id': app['id']}, tolerances=tolerances, **execution_options)
            if 'comparisons' not in run: return run
            if contract.load(claimed['numeric_representation']) != run['numeric_representation']:
                raise ValueError('Claimed numerical representation differs from this receiver execution')
            checked = run['comparisons'][port]
            if claimed['status'] != checked['status']:
                return {**base, 'outcome': 'different', 'diagnostics': ['The recorded reproduction claim does not match this call'], 'check': run}
            return {**base, 'outcome': checked['status'], 'subject': selected, 'port': port, 'policy': encoded,
                    'comparison': checked, 'check': run, 'imported_evidence': 'declared; this result is a fresh local check'}
        except (ValueError, KeyError, TypeError, OSError) as error:
            return {**base, 'outcome': 'rejected', 'diagnostics': [str(error)]}

"""Compare an unreviewed component against a receiver-selected statement.

The receiver builds/exports the trusted reference before any candidate code.
Candidate build, native export and textual-environment comparison are separate
sandboxed operations. No author receipt or application capture grants trust.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile

from reviewed import HERE, ROOT, verify as rebuild, run_step, fingerprint
from applications import load_module
from build_inputs import file_digest
from export import canonical
from receipts import POLICY, UNREVIEWED_POLICY, ReceiptStore
from boundary import UnsupportedBoundary, current_limits
from run_comparator import DEFAULT_TOOLCHAIN

COMPARISON = HERE / '.lake/build/bin/slean_compare'
PINS = {'Comparator': 'd03acab154d269c06e60e4de7e4cc85deebff94b',
        'lean4export': '076e8e57707e813375e8f9da8bf989799ace9680'}


def component(manifest, identifier):
    selected = [c for c in manifest['components'] if c['id'] == identifier]
    if len(selected) != 1 or selected[0]['interface']['profile'] != 'slean-lean/0.1-draft.1':
        raise UnsupportedBoundary('Select one exact native Lean component')
    return selected[0]


def tools_record():
    environment = {'PATH': '/usr/bin:/bin', 'GIT_CONFIG_NOSYSTEM': '1'}
    record = {}
    for name, expected in PINS.items():
        directory = HERE / '.lake/packages' / name
        revision = subprocess.check_output(['/usr/bin/git', 'rev-parse', 'HEAD'], cwd=directory,
            env=environment, text=True, timeout=20).strip()
        dirty = subprocess.run(['/usr/bin/git', '-c', 'core.fsmonitor=false', 'diff', '--no-ext-diff',
            '--quiet', 'HEAD', '--'], cwd=directory, env=environment, timeout=20)
        if revision != expected or dirty.returncode:
            raise UnsupportedBoundary('Comparison dependency differs from its pin: ' + name)
        record[name] = revision
    record['binary_sha256'] = file_digest(COMPARISON)
    record['driver_sha256'] = file_digest(HERE / 'SleanCompare.lean')
    record['receiver_sha256'] = file_digest(Path(__file__))
    return record


def verify(directory, identifier, *, trusted_module, trusted_component, dependency_project,
           policy, store=None, toolchain=DEFAULT_TOOLCHAIN):
    base = {'format': 'slean-verification/0.1-draft.1', 'policy': policy,
            'status': 'unsupported', 'receipts': [], 'results': []}
    if policy != UNREVIEWED_POLICY:
        return {**base, 'reason': 'Explicit unreviewed-contribution policy required; no silent fallback'}
    try:
        directory, trusted_module, dependency_project, toolchain = [Path(p).resolve(strict=True)
            for p in (directory, trusted_module, dependency_project, toolchain)]
        if os.getuid() == 0:
            raise UnsupportedBoundary('Receiver verification cannot run as root')
        if store and any(store.directory.resolve().is_relative_to(p) for p in (directory, trusted_module)):
            raise ValueError('Receipt keys must stay outside both transferable modules')
        reference, candidate = load_module(trusted_module), load_module(directory)
        expected = component(reference, trusted_component)
        selected = component(candidate, identifier)
        target = expected['interface']['value']
        supplied = selected['interface']['value']
        if target['declaration'] != supplied['declaration']:
            raise UnsupportedBoundary('Candidate names a different native declaration')
        tools = tools_record()
        with tempfile.TemporaryDirectory(prefix='slean-unreviewed-') as temporary:
            control = Path(temporary).resolve()
            challenge_export, solution_export = control / 'challenge.ndjson', control / 'solution.ndjson'
            # Reference preparation completes before candidate execution. Its
            # proof may be a placeholder: only the independently selected exact
            # statement is trusted, not a proof of that statement.
            challenge = rebuild(trusted_module, [trusted_component], dependency_project=dependency_project,
                policy=POLICY, store=store, toolchain=toolchain, _issue_receipts=False, _export_to=challenge_export)
            if not challenge_export.is_file() or len(challenge['results']) != 1:
                return {**base, 'reason': 'Trusted statement preparation unavailable: ' + challenge.get('reason', challenge['status'])}
            actual = challenge['results'][0]
            if actual['statement_fingerprint'] != target['statement']['fingerprint'] or any(
                    p != 'Unapproved transitive axiom' for p in actual['problems']):
                raise ValueError('Trusted reference does not reconstruct its exact declared statement')
            solution = rebuild(directory, [identifier], dependency_project=dependency_project,
                policy=POLICY, store=store, toolchain=toolchain, _issue_receipts=False, _export_to=solution_export)
            if not solution_export.is_file() or len(solution['results']) != 1:
                return {**base, 'status': solution['status'],
                    'reason': 'Candidate reconstruction unavailable: ' + solution.get('reason', solution['status'])}
            request = control / 'comparison.json'
            request.write_bytes(canonical({'challenge': str(challenge_export), 'solution': str(solution_export),
                'declarations': [target['declaration']]}))
            if store and any(store.directory.resolve().is_relative_to(p) for p in [control, toolchain, COMPARISON.parent]):
                raise ValueError('Receipt store is inside a comparison execution root')
            environment = {'PATH': str(toolchain / 'bin') + ':/usr/bin:/bin', 'LEAN_SYSROOT': str(toolchain),
                           'LEAN_ABORT_ON_PANIC': '1', 'LEAN_NUM_THREADS': '2'}
            comparison = json.loads(run_step([COMPARISON, 'compare', request], directory=control,
                readable=[control, toolchain, COMPARISON.parent], writable=[], environment=environment,
                limits=current_limits(), label='trusted-statement comparison and complete proof replay'))
            if comparison.get('format') != 'slean-native-comparison/0.1-draft.1' or comparison.get('status') != 'passed' or comparison.get('checked_theorems') != 1:
                raise ValueError('Native comparison did not confirm the selected theorem')
            declarations = comparison.get('declarations')
            if not isinstance(declarations, list) or len(declarations) != 1 or not isinstance(declarations[0], dict) or declarations[0].get('declaration') != target['declaration']:
                raise ValueError('Comparison metadata does not name the exact selected theorem')
            checked = declarations[0]
            if any(not isinstance(checked.get(field), list) for field in ('axioms', 'statement_dependencies', 'proof_dependencies')):
                raise ValueError('Comparison omitted its kernel-checked dependency metadata')
            if solution['status'] != 'passed' or solution['results'][0]['statement_fingerprint'] != target['statement']['fingerprint']:
                raise ValueError('Candidate interface does not match its compared native statement')
            if tools_record() != tools or load_module(directory)['id'] != candidate['id'] or load_module(trusted_module)['id'] != reference['id']:
                raise ValueError('Receiver tools or input modules changed during comparison')
            exports = {'challenge': challenge['proof_export'], 'solution': solution['proof_export']}
            if file_digest(challenge_export) != exports['challenge']['sha256'] or file_digest(solution_export) != exports['solution']['sha256']:
                raise ValueError('Proof export changed after reconstruction')
            environment_record = {'tools': tools, 'challenge_environment': challenge['results'][0]['environment_fingerprint'],
                'solution_environment': solution['results'][0]['environment_fingerprint'], 'proof_exports': exports,
                'comparison': comparison}
            result = {'status': 'passed', 'policy': UNREVIEWED_POLICY,
                'subject': {'module': candidate['id'], 'id': identifier}, 'context': {},
                'statement_fingerprint': target['statement']['fingerprint'], 'environment_fingerprint': fingerprint(environment_record),
                'trusted_statement': {'module': reference['id'], 'id': trusted_component, 'artifacts': reference['payloads']},
                'artifacts': candidate['payloads'], 'proof_exports': exports,
                'axioms': checked['axioms'], 'statement_dependencies': checked['statement_dependencies'],
                'proof_dependencies': checked['proof_dependencies'],
                'checked_at': datetime.now(timezone.utc).isoformat()}
            return {**base, 'status': 'passed', 'results': [result],
                'receipts': [store._record_checked(result)] if store else [], 'environment': environment_record,
                'comparison': comparison, 'rebuilt_modules': solution['rebuilt_modules'],
                'limits': {**solution['limits'], 'wall_seconds_per_step': 600, 'proof_export_bytes_each': 512 * 1024 * 1024},
                'limitations': ['Receiver independently selects trusted reference source and installed imports',
                    'Native exports are compared with pinned Comparator and replayed in Lean; no external kernel',
                    'No hard memory or aggregate disk/job quota on this macOS backend; not a hostile-upload service',
                    'Component proof only; unreviewed application capture fidelity and empirical validity are not assessed']}
    except (UnsupportedBoundary, FileNotFoundError) as error:
        return {**base, 'reason': str(error)}
    except (ValueError, RuntimeError) as error:
        return {**base, 'status': 'failed', 'reason': str(error), 'interpretation': 'No proof receipt; not a refutation'}
    except (KeyError, TypeError, IndexError, OSError, subprocess.SubprocessError) as error:
        return {**base, 'reason': 'Unsupported module or unavailable comparison tools: ' + str(error)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--component', required=True)
    parser.add_argument('--trusted-module', type=Path, required=True)
    parser.add_argument('--trusted-component', required=True)
    parser.add_argument('--dependency-project', type=Path, required=True)
    parser.add_argument('--policy', required=True)
    parser.add_argument('--store', type=Path)
    args = parser.parse_args()
    result = verify(args.module, args.component, trusted_module=args.trusted_module,
        trusted_component=args.trusted_component, dependency_project=args.dependency_project, policy=args.policy,
        store=ReceiptStore(args.store, create=True) if args.store else None)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)

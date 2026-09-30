"""Real module-bound trusted-statement comparisons and local receipt controls."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import time
from unittest.mock import patch

import unreviewed
from reviewed import ROOT, LEAN, HERE, inspect_component
from receipts import POLICY, UNREVIEWED_POLICY, ReceiptStore
from build_inputs import file_digest
from check_reviewed import save
import export

PROJECT = ROOT / 'examples/reuse/with-slean-lean'
OUT = LEAN / '_out/unreviewed'


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    def checked(label):
        checks.append(label)
        print(label + ': passed', flush=True)
    with tempfile.TemporaryDirectory(prefix='slean-unreviewed-check-') as temporary:
        run = Path(temporary)
        consumer = export.pack(PROJECT / '_out/application-consumer.json', PROJECT, run / 'consumer')
        mixed = export.pack(PROJECT / '_out/native.json', PROJECT, run / 'mixed')
        physics = next(c for c in consumer['components'] if c['interface']['value']['declaration'][-1][1] == 'energy_with_all_arguments')
        quoted = next(c for c in mixed['components'] if c['interface']['value']['declaration'][-1][1] == 'name.with.dots')
        authority = ReceiptStore(run / 'receiver', create=True)
        other = ReceiptStore(run / 'other', create=True)
        def verify(candidate, selected, reference, trusted):
            return unreviewed.verify(candidate, selected, trusted_module=reference, trusted_component=trusted,
                dependency_project=PROJECT, policy=UNREVIEWED_POLICY, store=authority)
        # The independently selected reference can be a conjecture placeholder.
        # Altering its proof never turns it into a claimed checked proof.
        shutil.copytree(run / 'mixed', run / 'reference')
        reference = deepcopy(mixed)
        source = run / 'reference' / quoted['interface']['value']['source']['path']
        original = source.read_text()
        old = 'theorem «name.with.dots» : True := True.intro'
        assert old in original
        source.write_text(original.replace(old, 'theorem «name.with.dots» : True := by sorry'))
        save(reference, run / 'reference')
        for name, replacement in [('changed', 'theorem «name.with.dots» : True ∧ True := ⟨True.intro, True.intro⟩'),
                ('sorry', 'theorem «name.with.dots» : True := by sorry'),
                ('axiom', 'axiom invented : True\ntheorem «name.with.dots» : True := invented')]:
            shutil.copytree(run / 'mixed', run / name)
            changed = deepcopy(mixed)
            path = run / name / quoted['interface']['value']['source']['path']
            path.write_text(original.replace(old, replacement))
            save(changed, run / name)
        checked('all_comparison_fixtures_are_wire_valid_before_execution')
        with patch('reviewed.run_step', side_effect=AssertionError('Wrong policy executed code')):
            result = unreviewed.verify(run / 'consumer', physics['id'], trusted_module=run / 'consumer',
                trusted_component=physics['id'], dependency_project=PROJECT, policy=POLICY, store=authority)
            assert result['status'] == 'unsupported' and not result['receipts']
        checked('wrong_policy_has_no_reviewed_fallback')
        real_rebuild = unreviewed.rebuild
        misleading = [[['str', 'fabricated_metadata']]]
        def misleading_binary_metadata(*args, **kwargs):
            report = real_rebuild(*args, **kwargs)
            # Replace diagnostic transport only. Both real source builds,
            # exports, comparison and kernel replay still execute unchanged.
            for record in report['results']:
                for field in ('axioms', 'statement_dependencies', 'proof_dependencies'):
                    record[field] = deepcopy(misleading)
            return report
        with patch.object(unreviewed, 'rebuild', side_effect=misleading_binary_metadata):
            phys = verify(run / 'consumer', physics['id'], run / 'consumer', physics['id'])
        (OUT / 'physlib.json').write_text(json.dumps(phys, indent=2))
        assert phys['status'] == 'passed', phys.get('reason')
        assert len(phys['receipts']) == 1 and phys['comparison']['checked_theorems'] == 1
        checked('dependency_bearing_physlib_consumer_is_compared_and_replayed')
        metadata = phys['comparison']['declarations'][0]
        assert metadata['declaration'] == physics['interface']['value']['declaration']
        for field in ('axioms', 'statement_dependencies', 'proof_dependencies'):
            assert phys['results'][0][field] == metadata[field] != misleading, field
        assert [['str', 'DirectReuse'], ['str', 'energy_at_two_times']] in metadata['proof_dependencies']
        checked('receipt_metadata_comes_from_kernel_checked_textual_constants')
        good = verify(run / 'mixed', quoted['id'], run / 'reference', quoted['id'])
        (OUT / 'quoted.json').write_text(json.dumps(good, indent=2))
        assert good['status'] == 'passed', good.get('reason')
        assert len(good['receipts']) == 1
        assert good['results'][0]['trusted_statement']['module'] == reference['id']
        checked('quoted_native_name_matches_a_separately_selected_unproved_statement')
        receipt = good['receipts'][0]
        def inspect(candidate=receipt, store=authority, policy=UNREVIEWED_POLICY):
            return inspect_component(run / 'mixed', quoted['id'], receipt=candidate, store=store, policy=policy)
        with patch('subprocess.Popen', side_effect=AssertionError('Offline inspection executed')), \
                patch('socket.socket', side_effect=AssertionError('Offline inspection used network')):
            assert inspect()['formal_verification'] == 'passed'
            assert inspect()['empirical_validity'] == 'not_assessed'
            assert inspect(store=other)['formal_verification'] == 'not_performed'
            assert inspect(policy=POLICY)['formal_verification'] == 'not_performed'
            for field, value in [('policy', POLICY), ('environment_fingerprint', '0' * 64),
                    ('trusted_statement', {}), ('proof_exports', {}), ('context', {'changed': True})]:
                forged = deepcopy(receipt)
                forged['verification'][field] = value
                assert inspect(forged)['formal_verification'] == 'not_performed', field
        checked('offline_receipts_bind_reference_exports_environment_and_exact_policy')
        rejected = {}
        expected_errors = {'changed': 'Challenge and solution theorem statement do not match',
                           'sorry': "Illegal axiom detected: 'sorryAx'",
                           'axiom': "Illegal axiom detected: 'FormalExample.invented'"}
        for name in ('changed', 'sorry', 'axiom'):
            report = verify(run / name, quoted['id'], run / 'reference', quoted['id'])
            (OUT / (name + '.json')).write_text(json.dumps(report, indent=2))
            assert report['status'] == 'failed' and not report['receipts'], report.get('reason')
            assert 'trusted-statement comparison' in report['reason'], report.get('reason')
            assert expected_errors[name] in report['reason'], report.get('reason')
            rejected[name] = report['reason'].strip().split('\n')[-1]
            checked(name + '_candidate_rejected_after_build_and_export')
        frozen = export.read_json(ROOT / 'examples/reuse/frozen-baseline.json')
        for path, expected in frozen['sha256'].items():
            assert file_digest(ROOT / 'examples/reuse' / path) == expected, path
        paths = [HERE / name for name in ('unreviewed.py', 'check_unreviewed.py', 'SleanCompare.lean',
            'reviewed.py', 'receipts.py', 'boundary.py', 'run_comparator.py', 'lakefile.toml', 'lake-manifest.json')]
        paths += [LEAN / name for name in ('SleanAudit.lean', 'build_inputs.py', 'export.py', 'tests/test_streamed_export.py')]
        summary = {'status': 'passed', 'policy': UNREVIEWED_POLICY, 'checks': checks,
            'seconds': round(time.monotonic() - started, 3), 'physlib_component': physics['id'],
            'quoted_component': quoted['id'], 'trusted_reference': reference['id'],
            'physlib_proof_exports': phys['results'][0]['proof_exports'], 'rejected': rejected,
            'frozen_baseline_files_unchanged': len(frozen['sha256']),
            'source_sha256': {str(path.relative_to(ROOT)): file_digest(path) for path in paths},
            'limitations': phys['limitations']}
        (OUT / 'candidate.json').write_text(json.dumps(summary, indent=2, sort_keys=True))
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()

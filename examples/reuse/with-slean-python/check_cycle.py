"""Run and reconstruct the exported research cycle without private chat state."""
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
from slean import Reader, INTERFACE_POLICY
from slean.authoring import RESEARCH
from slean.research import Research, POLICY
from cycle import run_cycle


def check():
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='slean-research-cycle-') as temporary:
        root = Path(temporary)/'investigation'; result = run_cycle(root)
        directories = [root/path for path in result['directories']]
        receiver = Reader(root/'retry-run', dependencies=directories)
        research = Research(receiver)
        # This consumer reads exported records and performs fresh checks. The
        # producer's summarized outcome is not authority for either assessment.
        for name, expected in [('first', 'failed_prediction'), ('second', 'within_bound')]:
            evidence, plan = result[name+'_assessment'], result[name+'_plan']
            report = research.verify_evidence(evidence, expected_evidence=evidence, expected_plan=plan, policy=POLICY)
            assert report['outcome'] == expected, report
            record = receiver.inspect(evidence)['record']
            execution = receiver.inspect(record['subject'])['record']
            assert execution['plan'] == plan
            assert receiver.inspect(evidence)['imported_evidence'] == 'declared'
        failed = receiver.inspect(result['first_assessment'])['record']
        revised = receiver.inspect(result['revision'])['record']
        assert revised['supersedes'] == [failed['result']['value']['model']]
        assert revised['annotations'][RESEARCH]['motivated_by'] == result['first_assessment']
        before = receiver.inspect(result['blocked_attempt'])['record']
        after = receiver.inspect(result['retry'])['record']
        assert before['bindings'] == after['bindings'] and before['context'] == after['context']
        retried = research.check_retry(result['retry'], expected_previous=result['blocked_attempt'], policy=INTERFACE_POLICY)
        assert retried['outcome'] == 'conditional' and retried['resolved_obstacle_ids'] == ['temperature']
        assert len(retried['remaining_obligations']) == 3 and not retried['contributions_verified']
        query = research.affected_uses(result['first_assessment'], expected_evidence=result['first_assessment'], expected_plan=result['first_plan'], policy=POLICY)
        assert query['query_status'] == 'complete' and not query['automatic_retraction'] and query['candidates']
        follow_up = receiver.inspect(result['follow_up'])['record']
        assert follow_up['targets'] == [] and follow_up['motivated_by'] == result['first_assessment']
        alternatives = receiver._fresh(result['revision']['module'])['annotations'][RESEARCH]['alternatives']
        assert len(alternatives) == 1 and alternatives[0]['status'] == 'unresolved'
        adjustment = receiver.inspect({'module': result['modules']['offset-plan'], 'id': 'plan'})['record']
        assert adjustment['bindings']['gain'] == result['reused_result']
        files = [p for p in root.rglob('*') if p.is_file()]
        artifact_files, artifact_bytes = len(files), sum(p.stat().st_size for p in files)
    frozen = json.loads((HERE.parent/'frozen-baseline.json').read_text())
    for relative, expected in frozen['sha256'].items():
        assert hashlib.sha256((HERE.parent/relative).read_bytes()).hexdigest() == expected, relative
    paths = [*sorted(HERE.glob('*.py')), *sorted((ROOT/'packages/python/slean').glob('*.py')),
        *sorted((ROOT/'packages/python/slean/data').glob('*.json')),
        ROOT/'packages/python/tests/test_research.py', ROOT/'packages/python/requirements.lock']
    return {'status': 'passed', 'observed_date': datetime.date.today().isoformat(),
        'scope': 'SR-T08 prediction/failure/revision/scoped-reassessment/result-and-method-reuse/retry checkpoint; conditional Lean bridge and complete negative-case acceptance remain open',
        'cycle': result, 'consumer_reconstruction': 'passed; same SDK, no private chat state',
        'formal_bridge': 'not_performed', 'gate_u': 'not_evaluated', 'frozen_files_unchanged': len(frozen['sha256']),
        'seconds': round(time.monotonic()-started, 3), 'temporary_artifact_files': artifact_files, 'temporary_artifact_bytes': artifact_bytes,
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == '__main__': print(json.dumps(check(), indent=2, sort_keys=True))

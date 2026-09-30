"""Finite scientific comparisons, exact frozen rules and scoped use queries."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slean import Author, Reader, scalar, scalar_port, equals_requirement, applicability_requirement
from slean.authoring import QUANTITY, RESEARCH
from slean import contract
from slean.research import Research, POLICY

EMPTY = {'id': 'conditions', 'all': []}
UNKNOWN = {'kind': 'unknown'}


def value(text, dimension='voltage', unit='volt'):
    return scalar(text, dimension=dimension, unit=unit, uncertainty=UNKNOWN)


def typed(text, dimension='voltage', unit='volt'):
    return {'typed': {'profile': QUANTITY, 'value': value(text, dimension, unit)}}


class ResearchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root, self.counter = Path(temporary.name), 0

    def fixture(self, *, observed='8.6', expected='8.5', bound='0.02', scope=None, observed_unit='volt', profiles=()):
        context = {'sensor': {'literal': 'sensor-A'}, 'temperature': typed('313.15', 'temperature', 'kelvin')}
        scope = deepcopy(context if scope is None else scope)
        observed_value = value(observed)
        observed_value['unit'] = observed_unit  # Imported payload, including unsupported fixture units.
        raw = json.dumps({'id': 'observation', 'context': scope, 'voltage': observed_value}).encode()
        # The receiver must not import or execute the packaged comparison code.
        author = Author(payloads={'observation.json': raw, 'compare.py': b'raise AssertionError("Do not execute imported assessment code")\n'}, profiles=profiles)
        assumption = author.component(id='physical', kind='claim', name='Unproved sensor hypothesis', interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY, sources=[], license='unknown')
        requires = {'id': 'conditions', 'all': [equals_requirement('sensor', location='context', field='sensor', expected=context['sensor']),
            equals_requirement('temperature', location='context', field='temperature', expected=context['temperature']), applicability_requirement('physical-condition', claim=assumption)]}
        model = author.component(id='model', kind='model', name='Hypothetical response', interface={'profile': QUANTITY, 'value': {
            'inputs': {'displacement': scalar_port(dimension='length', unit='millimeter')}, 'outputs': {'voltage': scalar_port(dimension='voltage', unit='volt')}}},
            requires=requires, sources=[], license='unknown', annotations={RESEARCH: {'role': 'hypothesis'}})
        question = author.question(id='question', wording='Does this model describe the new context?', source='Owned synthetic test')
        plan = author.plan_test(model, id='plan', question=question, bindings={'displacement': typed('4', 'length', 'millimeter')}, context=context,
            prediction=typed(expected)['typed'], bound=typed(bound)['typed'], observation_id='observation')
        run = author.record_execution(plan, id='run', outputs={'voltage': typed(expected)})
        observation = author.component(id='observation', kind='data', name='Synthetic observation', interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}},
            requires=EMPTY, sources=[{'path': 'observation.json'}], license='unknown', annotations={RESEARCH: {'role': 'observation'}})
        directory = self.root/str(self.counter); self.counter += 1
        revision = author.pack(directory, publishable=[assumption, model, question, plan, run, observation])
        reader = Reader(directory); research = Research(reader)
        options = {'expected_plan': {'module': revision, **plan}, 'policy': POLICY}
        return author, directory, revision, reader, research, run, observation, options

    def evidence(self, fixture, *, outcome='failed_prediction', error='0.1'):
        author, directory, revision, reader, research, run, observation, options = fixture
        emitter = Author(dependencies=[directory], payloads={'compare.py': b'raise AssertionError("Never execute")\n'})
        subject = reader.inspect(run)['record']
        body = {'plan': options['expected_plan'], 'model': {'module': revision, 'id': 'model'}, 'observation': {'module': revision, **observation}, 'outcome': outcome}
        if outcome in ('failed_prediction', 'within_bound'): body['absolute_error'] = value(error)
        evidence = emitter.record_evidence(id='assessment', kind='empirical', subject={'module': revision, **run}, context=subject['context'], policy=POLICY,
            implementation={'path': 'compare.py'}, artifacts=[], result={'profile': RESEARCH, 'value': body})
        destination = self.root/str(self.counter); self.counter += 1
        identity = emitter.pack(destination, publishable=[evidence])
        return destination, identity, evidence, Research(Reader(destination, dependencies=[directory]))

    def test_failed_prediction_and_separate_within_bound_check(self):
        fixture = self.fixture(); _, _, _, _, receiver, run, observation, options = fixture
        report = receiver.assess(run, observation, **options)
        self.assertEqual(report['outcome'], 'failed_prediction', report)
        self.assertEqual(report['result']['value']['absolute_error']['value'], '0.1')
        self.assertEqual(len(report['remaining_assumptions']), 1)
        good = self.fixture(observed='8520', observed_unit='millivolt')
        report = good[4].assess(good[5], good[6], **good[7])
        self.assertEqual(report['outcome'], 'within_bound', report)
        self.assertEqual(report['empirical_validity'], 'not_established')

    def test_outside_or_missing_scope_is_not_a_refutation(self):
        for scope, outcome in [({'sensor': {'literal': 'sensor-B'}, 'temperature': typed('313.15', 'temperature', 'kelvin')}, 'not_applicable'),
            ({'sensor': {'literal': 'sensor-A'}, 'temperature': typed('293.15', 'temperature', 'kelvin')}, 'not_applicable'),
            ({'sensor': {'literal': 'sensor-A'}}, 'unresolved')]:
            fixture = self.fixture(scope=scope)
            report = fixture[4].assess(fixture[5], fixture[6], **fixture[7])
            self.assertEqual(report['outcome'], outcome, report)
            self.assertNotIn('absolute_error', report['result']['value'])

    def test_forged_assessment_and_changed_rule_are_rechecked(self):
        fixture = self.fixture(); directory, revision, evidence, receiver = self.evidence(fixture, outcome='within_bound', error='0')
        self.assertEqual(receiver.reader.inspect(evidence)['imported_evidence'], 'declared')
        options = {**fixture[7], 'expected_evidence': {'module': revision, **evidence}}
        self.assertEqual(receiver.verify_evidence(evidence, **options)['outcome'], 'different')
        changed = self.fixture(bound='0.2')
        self.assertEqual(receiver.verify_evidence(evidence, **{**options, 'expected_plan': changed[7]['expected_plan']})['outcome'], 'rejected')
        directory, revision, evidence, receiver = self.evidence(fixture)
        self.assertEqual(receiver.verify_evidence(evidence, **{**fixture[7], 'expected_evidence': {'module': revision, **evidence}})['outcome'], 'failed_prediction')

    def test_missing_and_unsupported_observation_values_stay_distinct(self):
        for observed, unit, outcome in [(None, 'volt', 'unresolved'), ('8.6', 'unknown_unit', 'unsupported')]:
            fixture = self.fixture(observed=observed, observed_unit=unit)
            self.assertEqual(fixture[4].assess(fixture[5], fixture[6], **fixture[7])['outcome'], outcome)

    def test_error_comparison_keeps_long_decimal_precision(self):
        fixture = self.fixture(expected='9007199254740993.00000000000000001', observed='9007199254740993.00000000000000003', bound='0.00000000000000001')
        report = fixture[4].assess(fixture[5], fixture[6], **fixture[7])
        self.assertEqual(report['outcome'], 'failed_prediction', report)
        self.assertEqual(report['result']['value']['absolute_error']['value'], '0.00000000000000002')

    def test_comparison_never_executes_candidate_code_or_claims_reproduction(self):
        fixture = self.fixture(); directory, revision, evidence, receiver = self.evidence(fixture)
        report = receiver.verify_evidence(evidence, **{**fixture[7], 'expected_evidence': {'module': revision, **evidence}})
        self.assertEqual(report['outcome'], 'failed_prediction', report)
        self.assertEqual(report['check']['prediction_reproduction'], 'not_performed')
        self.assertEqual(receiver.assess(fixture[5], fixture[6], **{**fixture[7], 'policy': 'unknown'})['outcome'], 'unsupported')

    def test_observation_bytes_and_execution_are_bound_to_the_original_plan(self):
        fixture = self.fixture(); _, directory, revision, reader, receiver, run, observation, options = fixture
        report = receiver.assess(run, observation, **{**options, 'expected_plan': {'module': 'sha256:'+'0'*64, 'id': 'plan'}})
        self.assertEqual(report['outcome'], 'rejected')
        manifest = contract.load((directory/'slean-module.json').read_text())
        manifest['applications'][1]['outputs']['voltage'] = typed('8.6')
        manifest['id'] = contract.identity(manifest)
        (directory/'slean-module.json').write_text(json.dumps(manifest))
        other = Research(Reader(directory))
        self.assertEqual(other.assess(run, observation, **{**options, 'expected_plan': {'module': manifest['id'], 'id': 'plan'}})['outcome'], 'rejected')
        (directory/'observation.json').write_text('{}')
        self.assertEqual(other.assess(run, observation, expected_plan={'module': manifest['id'], 'id': 'plan'}, policy=POLICY)['outcome'], 'rejected')

    def test_affected_uses_follow_exact_active_assumptions_and_context(self):
        fixture = self.fixture(); upstream, revision, evidence, receiver = self.evidence(fixture)
        source, source_revision = fixture[1], fixture[2]
        author = Author(dependencies=[source]); target = {'module': source_revision, 'id': 'model'}
        context = fixture[3].inspect({'id': 'plan'})['record']['context']
        claim = applicability_requirement('depends-model', claim=target)
        for id, requires in [('dependent', claim), ('alternative', {'id': 'choose', 'any': [claim,
            equals_requirement('independent-branch', location='context', field='sensor', expected={'literal': 'sensor-A'})]})]:
            component = author.component(id=id, kind='method', name=id, interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=requires, sources=[], license='unknown')
            author.plan(component, id=id+'-use', bindings={}, context=context)
        author.plan(target, id='other-context', bindings={'displacement': typed('4', 'length', 'millimeter')},
            context={**context, 'temperature': typed('293.15', 'temperature', 'kelvin')})
        destination = self.root/'uses'; author.pack(destination, publishable=[{'id': id} for id in ('dependent', 'dependent-use', 'alternative', 'alternative-use', 'other-context')])
        receiver = Research(Reader(upstream, dependencies=[source, destination]))
        report = receiver.affected_uses(evidence, **{**fixture[7], 'expected_evidence': {'module': revision, **evidence}})
        self.assertEqual(report['outcome'], 'failed_prediction', report)
        ids = [row['application']['id'] for row in report['candidates']]
        self.assertIn('dependent-use', ids); self.assertIn('run', ids)
        self.assertNotIn('alternative-use', ids); self.assertNotIn('other-context', ids)
        self.assertEqual([r['application']['id'] for r in report['excluded']], ['other-context'])
        self.assertFalse(report['automatic_retraction'])

    def test_unknown_mandatory_profile_prevents_comparison(self):
        fixture = self.fixture(profiles=[{'id': 'unknown-profile', 'required': True}])
        # Include the declared unknown semantics rather than an unused profile.
        directory = fixture[1]; manifest = contract.load((directory/'slean-module.json').read_text())
        manifest['profiles'].append({'id': 'unknown-profile', 'required': True})
        manifest['profiles'].sort(key=lambda p: p['id']); manifest['id'] = contract.identity(manifest)
        (directory/'slean-module.json').write_text(json.dumps(manifest))
        receiver = Research(Reader(directory))
        report = receiver.assess(fixture[5], fixture[6], expected_plan={'module': manifest['id'], 'id': 'plan'}, policy=POLICY)
        self.assertEqual(report['outcome'], 'unsupported', report)

    def test_affected_use_query_reports_uninspectable_corpus_entries(self):
        fixture = self.fixture(); source, revision, evidence, receiver = self.evidence(fixture)
        extra = Author(dependencies=[fixture[1]])
        use = extra.plan({'module': fixture[2], 'id': 'model'}, id='unknown-use', bindings={'displacement': typed('4', 'length', 'millimeter')},
            context=fixture[3].inspect({'id': 'plan'})['record']['context'])
        destination = self.root/'unsupported-use'; extra.pack(destination, publishable=[use])
        manifest = contract.load((destination/'slean-module.json').read_text())
        manifest['profiles'].append({'id': 'unknown-profile', 'required': True}); manifest['profiles'].sort(key=lambda p: p['id'])
        manifest['id'] = contract.identity(manifest); (destination/'slean-module.json').write_text(json.dumps(manifest))
        receiver = Research(Reader(source, dependencies=[fixture[1], destination]))
        report = receiver.affected_uses(evidence, **{**fixture[7], 'expected_evidence': {'module': revision, **evidence}})
        self.assertEqual(report['outcome'], 'failed_prediction', report)
        self.assertEqual(report['query_status'], 'partial')
        self.assertEqual([r['application']['id'] for r in report['skipped']], ['unknown-use'])

    def retry_fixture(self, *, changed_method=True):
        author = Author()
        claim = author.component(id='physical', kind='claim', name='Open assumption', interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY, sources=[], license='unknown')
        def conditions(temperature, claim):
            return {'id': 'conditions', 'all': [equals_requirement('temperature', location='context', field='temperature', expected=typed(temperature, 'temperature', 'kelvin')),
                applicability_requirement('physical-condition', claim=claim)]}
        interface = {'profile': QUANTITY, 'value': {'inputs': {'reading': scalar_port(dimension='voltage', unit='volt')}, 'outputs': {}}}
        method = author.component(id='original', kind='method', name='Original method', interface=interface, requires=conditions('293.15', claim), sources=[], license='unknown')
        question = author.question(id='question', wording='Can the measurement be reused?', source='Owned fixture')
        bindings, context = {'reading': typed('8.6')}, {'temperature': typed('313.15', 'temperature', 'kelvin')}
        before = author.plan(method, id='before', bindings=bindings, context=context)
        author.record_attempt(before, question=question, attempt_of='same-measurement', previous_attempt=None, contributions=[], obstacles=[{'requirement': 'temperature', 'status': 'violated', 'reason': 'Recorded scope mismatch'}])
        source = self.root/'before'; prior = author.pack(source, publishable=[claim, method, question, before])
        emitter = Author(dependencies=[source])
        revised = emitter.component(id='revised', kind='method', name='Revised context', interface=interface,
            requires=conditions('313.15', {'module': prior, **claim}), sources=[], license='unknown', supersedes=[{'module': prior, **method}])
        selected = revised if changed_method else {'module': prior, **method}
        after = emitter.plan(selected, id='after', bindings=bindings, context=context)
        emitter.record_attempt(after, question={'module': prior, **question}, attempt_of='same-measurement', previous_attempt={'module': prior, **before},
            contributions=[revised], obstacles=[{'requirement': 'physical-condition', 'status': 'unresolved', 'reason': 'Applicability remains open'}])
        destination = self.root/'after'; emitter.pack(destination, publishable=[revised, after])
        return source, destination, Research(Reader(destination, dependencies=[source])), after, {'expected_previous': {'module': prior, **before}, 'policy': 'quantity-interface/0.1-draft.1'}

    def test_retry_rechecks_scope_preserves_inputs_and_leaves_physical_assumptions_open(self):
        source, destination, receiver, attempt, options = self.retry_fixture()
        report = receiver.check_retry(attempt, **options)
        self.assertEqual(report['outcome'], 'conditional', report)
        self.assertEqual(report['previous_check']['compatibility'], 'incompatible')
        self.assertEqual(report['resolved_obstacle_ids'], ['temperature'])
        self.assertEqual([r['requirement'] for r in report['remaining_obligations']], ['physical-condition'])
        self.assertFalse(report['contributions_verified'])
        manifest = contract.load((destination/'slean-module.json').read_text())
        manifest['applications'][0]['bindings']['reading'] = typed('6.6')
        manifest['id'] = contract.identity(manifest)
        (destination/'slean-module.json').write_text(json.dumps(manifest))
        report = Research(Reader(destination, dependencies=[source])).check_retry(attempt, **options)
        self.assertEqual(report['outcome'], 'rejected')
        self.assertIn('original bindings', report['diagnostics'][0])

    def test_an_unselected_contribution_cannot_repair_the_old_method(self):
        source, destination, receiver, attempt, options = self.retry_fixture(changed_method=False)
        report = receiver.check_retry(attempt, **options)
        self.assertEqual(report['outcome'], 'incompatible', report)
        self.assertNotIn('temperature', report['resolved_obstacle_ids'])
        self.assertEqual(receiver.check_retry(attempt, **{**options, 'expected_previous': {'module': 'sha256:'+'0'*64, 'id': 'before'}})['outcome'], 'rejected')


if __name__ == '__main__': unittest.main()

"""Receiver-owned finite prediction checks and scoped reassessment queries.

No candidate comparison code executes. A finite comparison does not prove a
model's applicability; imported assessments remain declarations until checked.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib

import rfc8785

from .authoring import KNOWN_PROFILES, QUANTITY, RESEARCH, qualify_requirements
from .execution import _qualify
from .quantities import QuantityError, convert_scalar, scalar
from .reader import INTERFACE_POLICY, MissingReference

POLICY = 'absolute-difference/0.1-draft.1'


def _reference(reference, owner):
    return {**reference, 'module': reference.get('module', owner)}


class Research:
    def __init__(self, reader):
        self.reader = reader

    def _supported(self, owner):
        if any(p['required'] and p['id'] not in KNOWN_PROFILES for p in self.reader._fresh(owner)['profiles']):
            raise QuantityError('mandatory_profile', 'Unsupported mandatory research module profile', unsupported=True)

    def _application(self, owner, app):
        selected = _reference(app['component'], owner)
        producer_owner, family, producer = self.reader._resolve(selected)
        self._supported(owner); self._supported(producer_owner)
        if family != 'components': raise ValueError('Application producer is not a component')
        original = qualify_requirements(producer['requires'], producer_owner)
        declared = qualify_requirements(app['requires'], owner)
        extra = None
        if declared != original:
            if 'all' not in declared or original not in declared['all']:
                raise ValueError('Application weakens producer requirements')
            extra = {**declared, 'all': [node for node in declared['all'] if node != original]}
        check = self.reader.apply(selected, bindings=_qualify(app['bindings'], owner),
            context=_qualify(app['context'], owner), policy=INTERFACE_POLICY, extra_requirements=extra)
        return producer_owner, producer, check

    def _context(self, actual, expected, *, actual_owner, expected_owner):
        diagnostics = []
        for key in sorted(set(actual) | set(expected)):
            if key not in actual or key not in expected:
                diagnostics.append({'field': key, 'status': 'unresolved', 'reason': 'missing_scope_binding'})
                continue
            leaf = {'profile': QUANTITY, 'predicate': 'equals', 'arguments': {
                'location': 'context', 'field': key, 'expected': expected[key]}}
            try:
                result = self.reader._leaf(leaf, {}, actual, expected_owner, actual_owner)
            except QuantityError as error:
                result = {'status': 'unsupported' if error.unsupported else 'violated', 'reason': error.code}
            diagnostics.append({'field': key, **result})
        return self.reader_status(diagnostics), diagnostics

    @staticmethod
    def reader_status(diagnostics):
        from .contract import aggregate
        return aggregate('all', [row['status'] for row in diagnostics])

    def assess(self, execution, observation, *, expected_plan, policy):
        base = {'policy': policy, 'layer': 'empirical', 'outcome': 'unsupported',
                'empirical_validity': 'not_established', 'prediction_reproduction': 'not_performed'}
        if policy != POLICY: return {**base, 'diagnostics': ['Unknown comparison policy; no fallback']}
        try:
            owner, family, app = self.reader._resolve(execution)
            if family != 'applications' or app['phase'] != 'executed' or 'plan' not in app:
                raise ValueError('Assess an executed test with its exact original plan')
            plan_owner, plan_family, plan = self.reader._resolve(app['plan'], owner)
            selected_plan = {'module': plan_owner, 'id': plan['id']}
            if expected_plan != selected_plan or plan_family != 'applications' or plan['phase'] != 'planned':
                raise ValueError('Receiver-selected evaluation plan differs')
            self._supported(plan_owner)
            for key in ('component', 'bindings', 'context'):
                if _qualify(app[key], owner) != _qualify(plan[key], plan_owner):
                    raise ValueError('Test execution changed its plan: '+key)
            if qualify_requirements(app['requires'], owner) != qualify_requirements(plan['requires'], plan_owner):
                raise ValueError('Test execution changed its planned requirements')
            annotation = plan.get('annotations', {}).get(RESEARCH, {})
            if annotation.get('role') != 'test-plan' or 'prediction' not in annotation:
                raise ValueError('The original plan has no frozen prediction')
            prediction = annotation['prediction']
            if prediction['comparison'] != 'absolute_difference':
                return {**base, 'diagnostics': ['Unsupported comparison method']}
            producer_owner, model, compatibility = self._application(owner, app)
            if model['kind'] not in ('model', 'claim') or model['interface']['profile'] != QUANTITY:
                return {**base, 'diagnostics': ['Unsupported prediction model interface']}
            observable = prediction['observable']
            port = model['interface']['value']['outputs'].get(observable)
            if not port or port['kind'] != 'scalar': return {**base, 'diagnostics': ['Unsupported predicted observable']}
            obs_owner, obs_family, obs = self.reader._resolve(observation)
            self._supported(obs_owner)
            if obs_family != 'components' or obs['kind'] != 'data' or obs['id'] != prediction['observation']:
                raise ValueError('Observation differs from the frozen evaluation plan')
            if obs.get('annotations', {}).get(RESEARCH, {}).get('role') != 'observation' or len(obs['sources']) != 1:
                return {**base, 'diagnostics': ['Select one observation JSON artifact under this policy']}
            raw = self.reader._artifact(obs['sources'][0], obs_owner)
            if len(raw) > 1024*1024: raise ValueError('Observation exceeds the comparison policy limit')
            from . import contract
            data = contract.load(raw.decode('utf-8'))
            if set(data) != {'id', 'context', observable} or data['id'] != obs['id']:
                raise ValueError('Unsupported or mismatched observation envelope')
            contract.schema(data['context'], 'module', 'bindings')
            scope, diagnostics = self._context(data['context'], plan['context'], actual_owner=obs_owner, expected_owner=plan_owner)
            body = {'plan': selected_plan, 'model': _reference(plan['component'], plan_owner),
                    'observation': {'module': obs_owner, 'id': obs['id']}, 'outcome': 'unresolved'}
            result = {**base, 'outcome': 'unresolved', 'result': {'profile': RESEARCH, 'value': body},
                'scope': diagnostics, 'application_check': compatibility,
                'subject': {'module': owner, 'id': app['id']}, 'observation_sha256': hashlib.sha256(raw).hexdigest(),
                'remaining_assumptions': [row for row in compatibility['obligations'] if row['status'] == 'unresolved']}
            if scope == 'unsupported' or compatibility['compatibility'] == 'unsupported':
                return {**result, 'outcome': 'unsupported', 'diagnostics': ['Unsupported scope or application semantics']}
            if scope == 'violated' or compatibility['compatibility'] == 'incompatible':
                body['outcome'] = 'not_applicable'
                return {**result, 'outcome': 'not_applicable'}
            if scope == 'unresolved': return result
            # Comparing a hypothesis is allowed while its applicability remains
            # open. Missing numerical inputs or scope checks cannot be assumed.
            if any(row['status'] == 'unresolved' and 'claim' not in row for row in compatibility['obligations']):
                return result
            expected, bound = prediction['expected'], prediction['bound']
            recorded, _ = self.reader._binding(app['outputs'][observable], owner)
            if recorded.get('typed', {}).get('profile') != QUANTITY:
                return {**result, 'outcome': 'unsupported', 'diagnostics': ['Unsupported predicted execution output']}
            values = [expected, bound, recorded['typed']['value'], data[observable]]
            converted = []
            for index, value in enumerate(values):
                # Missing observation data leaves the test unresolved. A model
                # output, prediction or bound still obeys its nonmissing port.
                descriptor = {**port, 'allow_missing': True} if index == 3 else port
                check = self.reader._port({'typed': {'profile': QUANTITY, 'value': value}}, descriptor, owner)
                if check['status'] == 'unresolved': return result
                if check['status'] != 'satisfied':
                    return {**result, 'outcome': 'unsupported' if check['status'] == 'unsupported' else 'rejected', 'diagnostics': [check['reason']]}
                converted.append(convert_scalar(value, expected['unit']))
            if bound['dimension'] == 'temperature': return {**result, 'outcome': 'unsupported', 'diagnostics': ['Temperature difference bounds are unsupported']}
            predicted, limit, executed, observed = [Decimal(v['value']) for v in converted]
            if limit < 0: raise ValueError('Negative evaluation bound')
            if predicted != executed: raise ValueError('Recorded prediction execution differs from the frozen expected value')
            with localcontext() as context:
                context.prec = sum(len(v['value']) for v in converted)+20
                error = abs(observed-predicted)
            outcome = 'within_bound' if error <= limit else 'failed_prediction'
            body.update(outcome=outcome, absolute_error=scalar(format(error, 'f'), dimension=expected['dimension'], unit=expected['unit'], uncertainty={'kind': 'unknown'}))
            comparison = {'execution': app, 'plan': plan, 'result': body, 'observation_sha256': result['observation_sha256'], 'policy': policy}
            return {**result, 'outcome': outcome, 'comparison_sha256': hashlib.sha256(rfc8785.dumps(comparison)).hexdigest()}
        except MissingReference as error:
            return {**base, 'outcome': 'unresolved', 'diagnostics': [str(error)]}
        except QuantityError as error:
            return {**base, 'outcome': 'unsupported' if error.unsupported else 'rejected', 'diagnostics': [str(error)]}
        except (ValueError, KeyError, TypeError, OSError, UnicodeError) as error:
            return {**base, 'outcome': 'rejected', 'diagnostics': [str(error)]}

    def verify_evidence(self, evidence, *, expected_evidence, expected_plan, policy):
        base = {'layer': 'empirical', 'policy': policy, 'outcome': 'unsupported', 'empirical_validity': 'not_established'}
        if policy != POLICY: return {**base, 'diagnostics': ['Unknown comparison policy; no fallback']}
        try:
            owner, family, record = self.reader._resolve(evidence)
            self._supported(owner)
            if expected_evidence != {'module': owner, 'id': record['id']} or family != 'evidence' or record['kind'] != 'empirical':
                raise ValueError('Receiver-selected empirical evidence differs')
            if record['method']['policy'] != policy or record['result']['profile'] != RESEARCH:
                return {**base, 'diagnostics': ['Unsupported imported empirical policy or result']}
            app_owner, app_family, app = self.reader._resolve(record['subject'], owner)
            if app_family != 'applications' or _qualify(app['context'], app_owner) != _qualify(record['context'], owner):
                raise ValueError('Assessment context differs from the executed test')
            claimed = record['result']['value']
            if _reference(claimed['plan'], owner) != expected_plan: raise ValueError('Assessment changed the selected evaluation rule')
            check = self.assess(_reference(record['subject'], owner), _reference(claimed['observation'], owner), expected_plan=expected_plan, policy=policy)
            if 'result' not in check or check['outcome'] in ('rejected', 'unsupported'): return check
            actual = check['result']['value']
            for key in ('plan', 'model', 'observation'):
                if _reference(claimed[key], owner) != actual[key]: raise ValueError('Assessment changed its exact '+key+' reference')
            if claimed['outcome'] != actual['outcome'] or ('absolute_error' in claimed) != ('absolute_error' in actual):
                return {**base, 'outcome': 'different', 'diagnostics': ['Recorded assessment differs from the fresh comparison'], 'check': check}
            if 'absolute_error' in actual:
                error = convert_scalar(claimed['absolute_error'], actual['absolute_error']['unit'])
                if error['value'] is None or Decimal(error['value']) != Decimal(actual['absolute_error']['value']):
                    return {**base, 'outcome': 'different', 'diagnostics': ['Recorded absolute error differs'], 'check': check}
            return {**base, 'outcome': actual['outcome'], 'check': check, 'subject': expected_evidence,
                'imported_evidence': 'declared; this is a fresh finite local comparison'}
        except QuantityError as error:
            return {**base, 'diagnostics': [str(error)]}
        except (ValueError, KeyError, TypeError, OSError) as error:
            return {**base, 'outcome': 'rejected', 'diagnostics': [str(error)]}

    def affected_uses(self, evidence, *, expected_evidence, expected_plan, policy):
        """List scoped candidates for reassessment, never automatic retractions."""
        checked = self.verify_evidence(evidence, expected_evidence=expected_evidence, expected_plan=expected_plan, policy=policy)
        result = {'outcome': checked['outcome'], 'candidates': [], 'excluded': [], 'skipped': [], 'query_status': 'complete',
                  'automatic_retraction': False, 'assessment_check': checked}
        if checked['outcome'] != 'failed_prediction': return result
        target = checked['check']['result']['value']['model']
        plan_owner, _, plan = self.reader._resolve(expected_plan)
        for owner in sorted(self.reader._modules):
            for app in self.reader._fresh(owner)['applications']:
                try:
                    _, _, compatibility = self._application(owner, app)
                except (ValueError, KeyError, TypeError, OSError) as error:
                    result['query_status'] = 'partial'
                    result['skipped'].append({'application': {'module': owner, 'id': app['id']}, 'reason': str(error)})
                    continue
                active = []
                def visit(node):
                    if 'leaf' in node:
                        leaf = node['leaf']
                        if leaf['profile'] == QUANTITY and leaf['predicate'] == 'applicability' and leaf['arguments']['claim'] == target:
                            active.append(node['id'])
                        return
                    if 'any' in node and node['id'] in compatibility['selections']:
                        children = [c for c in node['any'] if c['id'] == compatibility['selections'][node['id']]]
                    else: children = node.get('all', node.get('any', []))
                    for child in children: visit(child)
                if 'record' in compatibility: visit(compatibility['record']['requires'])
                direct = _reference(app['component'], owner) == target
                if not direct and not active: continue
                scope, diagnostics = self._context(app['context'], plan['context'], actual_owner=owner, expected_owner=plan_owner)
                row = {'application': {'module': owner, 'id': app['id']}, 'context': deepcopy(app['context']),
                    'direct_model_use': direct, 'active_assumption_requirements': active, 'scope': diagnostics,
                    'compatibility': compatibility['compatibility'], 'action': 'reassess; no automatic retraction'}
                (result['excluded'] if scope == 'violated' else result['candidates']).append(row)
        result['corpus'] = sorted(self.reader._modules)
        return result

    def check_retry(self, attempt, *, expected_previous, policy):
        """Freshly check a recorded retry; new citations never grant authority."""
        base = {'outcome': 'unsupported', 'policy': policy, 'layer': 'interface',
                'empirical_validity': 'not_established', 'contributions_verified': False}
        if policy != INTERFACE_POLICY: return {**base, 'diagnostics': ['Unknown retry interface policy']}
        try:
            owner, family, record = self.reader._resolve(attempt)
            annotation = record.get('annotations', {}).get(RESEARCH, {})
            if family != 'applications' or annotation.get('role') != 'reuse-attempt' or 'previous_attempt' not in annotation:
                raise ValueError('Select an explicit recorded retry')
            previous = _reference(annotation['previous_attempt'], owner)
            if previous != expected_previous: raise ValueError('Receiver-selected previous attempt differs')
            old_owner, old_family, old = self.reader._resolve(previous)
            old_annotation = old.get('annotations', {}).get(RESEARCH, {})
            if old_family != 'applications' or old_annotation.get('role') != 'reuse-attempt':
                raise ValueError('Previous reference is not a reuse attempt')
            for key in ('bindings', 'context'):
                if _qualify(record[key], owner) != _qualify(old[key], old_owner):
                    raise ValueError('Retry changed the original '+key)
            if annotation['attempt_of'] != old_annotation['attempt_of'] or _reference(annotation['question'], owner) != _reference(old_annotation['question'], old_owner):
                raise ValueError('Retry changed the question or requested use')
            for contribution in annotation.get('contributions', []): self.reader._resolve(contribution, owner)
            _, _, check = self._application(owner, record)
            _, _, prior_check = self._application(old_owner, old)
            satisfied = {row['requirement'] for row in check['obligations'] if row['status'] == 'satisfied'}
            return {**base, 'outcome': check['compatibility'], 'application_check': check, 'previous_check': prior_check,
                'previous_attempt': previous, 'contributions': _qualify(annotation.get('contributions', []), owner),
                'resolved_obstacle_ids': [row['requirement'] for row in old_annotation.get('obstacles', []) if row['requirement'] in satisfied],
                'remaining_obligations': [row for row in check['obligations'] if row['status'] != 'satisfied'],
                'previous_component': _reference(old['component'], old_owner), 'selected_component': _reference(record['component'], owner),
                'resolution_kind': 'fresh checks under the explicitly selected component version',
                'input_preserved': True, 'context_preserved': True,
                'limitations': ['Contribution references identify candidates only', 'Interface compatibility does not establish physical applicability']}
        except MissingReference as error:
            return {**base, 'outcome': 'conditional', 'diagnostics': [str(error)]}
        except QuantityError as error:
            return {**base, 'diagnostics': [str(error)]}
        except (ValueError, KeyError, TypeError, OSError) as error:
            return {**base, 'outcome': 'rejected', 'diagnostics': [str(error)]}

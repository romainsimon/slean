"""Export a controlled prediction/failure/revision/retry investigation.

The controller reveals each frozen synthetic observation after its plan is
exported. This order is a scripted fixture property, not public preregistration.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from slean import Author, Reader, scalar, scalar_port, equals_requirement, range_requirement, applicability_requirement, INTERFACE_POLICY
from slean.authoring import QUANTITY, RESEARCH
from slean.execution import Executor, POLICY as EXECUTION_POLICY
from slean.research import Research, POLICY as TEST_POLICY
from producer import produce

HERE = Path(__file__).resolve().parent
EMPTY = {'id': 'conditions', 'all': []}
UNKNOWN = {'kind': 'unknown'}


def value(text, dimension='voltage', unit='volt'):
    return scalar(text, dimension=dimension, unit=unit, uncertainty=UNKNOWN)


def typed(text, dimension='voltage', unit='volt'):
    return {'typed': {'profile': QUANTITY, 'value': value(text, dimension, unit)}}


def run_cycle(destination):
    destination = Path(destination); destination.mkdir(parents=True)
    producer = destination/'producer'; produced = produce(producer)
    directories = [producer/name for name in ('calibration', 'fit-producer', 'fit-plan', 'fit-result', 'fit-verification')]
    identities = {}
    def pack(author, name, records, *, alternatives=()):
        directory = destination/name
        revision = author.pack(directory, publishable=records, alternatives=alternatives)
        directories.append(directory); identities[name] = revision
        return revision
    def reader(directory): return Reader(directory, dependencies=directories)
    def pin(revision, ref): return {'module': revision, **ref}
    def options(selected, source=produced['reviewed_source_sha256']):
        return {'policy': EXECUTION_POLICY, 'expected_component': selected, 'reviewed_source_sha256': source, 'allow_conditional': True}
    # Controller inputs are not passed to the planner as observation values.
    inputs = json.loads((HERE.parent/'direct-python/fixtures/research.json').read_text())
    context = {'sensor': {'literal': 'sensor-A'}, 'temperature': typed(inputs['temperature']['value'], 'temperature', inputs['temperature']['unit'])}
    measurement = {'reading': typed(inputs['first_observation']['value'], unit=inputs['first_observation']['unit'])}
    original = {'module': produced['calibration'], 'id': 'sensor-inverse'}
    initial = Author(dependencies=directories)
    question = initial.question(id='reconstruction', wording='Can the same measurement be reconstructed at the new temperature?', source='Owned synthetic fixture')
    original_reader = Reader(producer/'calibration', dependencies=directories)
    old_check = original_reader.apply(original, bindings=measurement, context=context, policy=INTERFACE_POLICY)
    assert old_check['compatibility'] == 'incompatible'
    question_revision = pack(initial, 'question', [question])
    selected_question = pin(question_revision, question)
    original_record = original_reader.inspect(original)['record']
    parameters = original_record['interface']['value']['parameters']
    source_ref = {'module': produced['calibration'], 'path': 'methods.py'}
    hypothesis = Author(dependencies=directories)
    physical = hypothesis.component(id='physical', kind='claim', name='Affine extension at the new temperature, still unproved',
        interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY, sources=[], license='unknown', annotations={RESEARCH: {'role': 'hypothesis'}})
    def scoped_requirements(claim, *, inverse=False):
        return {'id': 'conditions', 'all': [equals_requirement('sensor', location='context', field='sensor', expected=context['sensor']),
            equals_requirement('temperature', location='context', field='temperature', expected=context['temperature']),
            range_requirement('range', location='bindings', field='reading' if inverse else 'displacement',
                minimum=value('0.5' if inverse else '0', 'voltage' if inverse else 'length', 'volt' if inverse else 'millimeter'),
                maximum=value('10.5' if inverse else '5', 'voltage' if inverse else 'length', 'volt' if inverse else 'millimeter')),
            applicability_requirement('physical-condition', claim=claim)]}
    interface = {'profile': QUANTITY, 'value': {'inputs': {'displacement': scalar_port(dimension='length', unit='millimeter')},
        'outputs': {'voltage': scalar_port(dimension='voltage', unit='volt')},
        'parameters': {key: parameters[key] for key in ('gain', 'offset')}, 'entrypoint': {'artifact': source_ref, 'symbol': 'predict'}}}
    model = hypothesis.component(id='model', kind='model', name='Affine high-temperature hypothesis', interface=interface,
        requires=scoped_requirements(physical), sources=[source_ref], license='unknown', annotations={RESEARCH: {'role': 'hypothesis'}})
    hypothesis_revision = pack(hypothesis, 'hypothesis', [physical, model])
    selected_model = pin(hypothesis_revision, model)

    def execution(plan_ref, name, *, source=None):
        origin = next(path for path in directories if json.loads((path/'slean-module.json').read_text())['id'] == plan_ref['module'])
        current = reader(origin); planned = current.inspect(plan_ref)['record']
        selected = planned['component']; selected.setdefault('module', plan_ref['module'])
        execution_options = options(selected, source or produced['reviewed_source_sha256'])
        actual = Executor(current).run(plan_ref, **execution_options)
        if actual['outcome'] != 'executed': raise RuntimeError(actual)
        emitter = Author(dependencies=directories, payloads={'execution.json': json.dumps(actual, sort_keys=True).encode()})
        run = emitter.record_execution(plan_ref, id='run', outputs=actual['outputs'])
        # At this stage the computation evidence records execution only.
        port = next(iter(actual['outputs']))
        output = actual['outputs'][port]['typed']['value']
        component_record = current.inspect(selected)['record']; implementation = component_record['interface']['value']['entrypoint']['artifact']
        implementation = {**implementation, 'module': implementation.get('module', selected['module'])}
        evidence = emitter.record_evidence(id='execution', kind='computation', subject=run, context=actual['application_check']['record']['context'],
            policy=EXECUTION_POLICY+'#output='+port, implementation=implementation, artifacts=[{'path': 'execution.json'}],
            result={'profile': QUANTITY, 'value': {'status': 'unsupported', 'numeric_representation': json.dumps(actual['numeric_representation'], sort_keys=True),
                'tolerance': value('0', output['dimension'], output['unit'])}})
        revision = pack(emitter, name, [run, evidence]); selected_run = pin(revision, run)
        tolerances = {key: value('0', body['typed']['value']['dimension'], body['typed']['value']['unit']) for key, body in actual['outputs'].items()}
        reproduced = Executor(reader(destination/name)).reproduce(selected_run, tolerances=tolerances, **execution_options)
        if reproduced['outcome'] != 'reproduced': raise RuntimeError(reproduced)
        return selected_run, reproduced

    def frozen_prediction(selected, displacement, name):
        bindings = {'displacement': typed(displacement['value'], 'length', displacement['unit'])}
        preview = Author(dependencies=directories)
        preview_plan = preview.plan(selected, id='preview', bindings=bindings, context=context)
        preview_revision = pack(preview, name+'-preview', [preview_plan])
        actual = Executor(reader(destination/(name+'-preview'))).run(pin(preview_revision, preview_plan), **options(selected))
        if actual['outcome'] != 'executed': raise RuntimeError(actual)
        planner = Author(dependencies=directories)
        test_plan = planner.plan_test(selected, id='plan', question=selected_question, bindings=bindings, context=context,
            prediction=actual['outputs']['voltage']['typed'], bound=typed(inputs['absolute_bound']['value'], unit=inputs['absolute_bound']['unit'])['typed'],
            observation_id=name+'-observation', observable='voltage')
        revision = pack(planner, name+'-plan', [test_plan])
        return pin(revision, test_plan)

    def observe_and_assess(plan_ref, run_ref, measurement, name):
        # Called only after the fixed plan and prediction execution were exported.
        emitter = Author(payloads={'observation.json': json.dumps({'id': name+'-observation', 'context': context,
            'voltage': value(measurement['value'], unit=measurement['unit'])}, sort_keys=True).encode()})
        observation = emitter.component(id=name+'-observation', kind='data', name='Frozen synthetic observation',
            interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}}, requires=EMPTY, sources=[{'path': 'observation.json'}],
            license='unknown', annotations={RESEARCH: {'role': 'observation'}})
        observation_revision = pack(emitter, name+'-observation', [observation])
        selected_observation = pin(observation_revision, observation)
        local = Research(reader(destination/(name+'-observation')))
        checked = local.assess(run_ref, selected_observation, expected_plan=plan_ref, policy=TEST_POLICY)
        if checked['outcome'] not in ('failed_prediction', 'within_bound'): raise RuntimeError(checked)
        import slean.research
        assessment = Author(dependencies=directories, payloads={'comparison.py': Path(slean.research.__file__).read_bytes()})
        proof = assessment.record_evidence(id='assessment', kind='empirical', subject=run_ref, context=context,
            policy=TEST_POLICY, implementation={'path': 'comparison.py'}, artifacts=[{'module': observation_revision, 'path': 'observation.json'}], result=checked['result'])
        revision = pack(assessment, name+'-assessment', [proof]); selected_proof = pin(revision, proof)
        verified = Research(reader(destination/(name+'-assessment'))).verify_evidence(selected_proof,
            expected_evidence=selected_proof, expected_plan=plan_ref, policy=TEST_POLICY)
        if verified['outcome'] != checked['outcome']: raise RuntimeError(verified)
        return selected_proof, checked, selected_observation

    first_plan = frozen_prediction(selected_model, inputs['first_displacement'], 'first')
    # Keep the new reading out of the planner's dependency corpus until the
    # first prediction and rule have their immutable module identity.
    blocked = Author(dependencies=directories)
    before = blocked.plan(original, id='before', bindings=measurement, context=context)
    blocked.record_attempt(before, question=selected_question, attempt_of='measurement-at-313K', previous_attempt=None, contributions=[],
        obstacles=[r for r in old_check['obligations'] if r['status'] != 'satisfied' and not r['requirement'].startswith(('input-', 'parameter-'))])
    initial_revision = pack(blocked, 'blocked', [before])
    first_run, first_reproduction = execution(first_plan, 'first-run')
    failed, first_assessment, first_observation = observe_and_assess(first_plan, first_run, inputs['first_observation'], 'first')
    assert first_assessment['outcome'] == 'failed_prediction'
    uses = Research(reader(destination/'first-assessment')).affected_uses(failed, expected_evidence=failed, expected_plan=first_plan, policy=TEST_POLICY)
    assert {r['application']['id'] for r in uses['candidates']} >= {'plan', 'run'}
    assert all(r['application']['module'] != initial_revision for r in uses['candidates'])

    # A new executable contribution estimates the offset, rather than embedding
    # the expected 0.6 value in the model revision.
    revision_source = (HERE/'revision_method.py').read_bytes()
    adjustment = Author(dependencies=directories, payloads={'revision.py': revision_source})
    fit = adjustment.component(id='adjust', kind='method', name='Offset adjustment under the original gain assumption', interface={'profile': QUANTITY, 'value': {
        'inputs': {'voltage': scalar_port(dimension='voltage', unit='volt'), 'displacement': scalar_port(dimension='length', unit='millimeter'),
            'gain': scalar_port(dimension='gain', unit='volt/millimeter')},
        'outputs': {'offset': scalar_port(dimension='voltage', unit='volt')},
        'entrypoint': {'artifact': {'path': 'revision.py'}, 'symbol': 'revise_offset'}}},
        requires=applicability_requirement('gain-condition', claim={'module': produced['calibration'], 'id': 'gain-assumption'}),
        sources=[{'path': 'revision.py'}], license='unknown', annotations={RESEARCH: {'role': 'method', 'motivated_by': failed}})
    # The observed value is read from the exact observation artifact, not a
    # second transcription of the fixture.
    observation_bytes = reader(destination/'first-observation')._artifact({'path': 'observation.json'}, first_observation['module'])
    observed = json.loads(observation_bytes)['voltage']
    reused_gain = {'ref': {'module': produced['fit_result'], 'id': 'fit-run'}, 'output': 'gain'}
    adjustment_plan = adjustment.plan(fit, id='plan', bindings={'voltage': {'typed': {'profile': QUANTITY, 'value': observed}}, 'gain': reused_gain,
        'displacement': typed(inputs['first_displacement']['value'], 'length', inputs['first_displacement']['unit'])}, context=context)
    adjustment_revision = pack(adjustment, 'offset-plan', [fit, adjustment_plan])
    adjusted_run, adjustment_report = execution(pin(adjustment_revision, adjustment_plan), 'offset-run', source=hashlib.sha256(revision_source).hexdigest())
    revised_parameters = {**{key: parameters[key] for key in ('gain', 'offset')}, 'offset': adjustment_report['outputs']['offset']['typed']['value']}
    revision = Author(dependencies=directories)
    revised_interface = deepcopy(interface); revised_interface['value']['parameters'] = revised_parameters
    revised_model = revision.component(id='model', kind='model', name='Revised offset hypothesis', interface=revised_interface,
        requires=scoped_requirements(pin(hypothesis_revision, physical)), sources=[source_ref, {'module': adjusted_run['module'], 'path': 'execution.json'}],
        license='unknown', supersedes=[selected_model], annotations={RESEARCH: {'role': 'revision', 'motivated_by': failed}})
    follow_up = revision.question(id='follow-up', wording=inputs['follow_up'], source='Owned synthetic fixture', motivated_by=failed)
    model_revision = pack(revision, 'revision', [revised_model, follow_up], alternatives=[{'explanation': inputs['unresolved_alternative'], 'source': 'Owned synthetic fixture', 'status': 'unresolved'}])
    selected_revision = pin(model_revision, revised_model)
    second_plan = frozen_prediction(selected_revision, inputs['second_displacement'], 'second')
    second_run, second_reproduction = execution(second_plan, 'second-run')
    accepted, second_assessment, _ = observe_and_assess(second_plan, second_run, inputs['second_observation'], 'second')
    assert second_assessment['outcome'] == 'within_bound'

    calibration = Author(dependencies=directories)
    assumption_refs = []
    for id, name in [('physical', 'Affine response at the new context remains unproved'), ('gain', 'Gain is treated as exact; physical uncertainty remains unknown'), ('residual', 'Residual is assumed bounded at the new context')]:
        assumption_refs.append(calibration.component(id=id, kind='claim', name=name, interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}},
            requires=EMPTY, sources=[], license='unknown', annotations={RESEARCH: {'role': 'hypothesis', 'motivated_by': accepted}}))
    inverse_interface = deepcopy(original_record['interface']); inverse_interface['value']['parameters'].update(revised_parameters)
    inverse_interface['value']['entrypoint']['artifact'] = source_ref
    requires = scoped_requirements(assumption_refs[0], inverse=True)
    requires['all'].extend(applicability_requirement(id+'-condition', claim=claim) for id, claim in zip(('gain', 'residual'), assumption_refs[1:]))
    inverse = calibration.component(id='inverse', kind='method', name='Revised conditional sensor inverse', interface=inverse_interface, requires=requires,
        sources=[source_ref, {'module': adjusted_run['module'], 'path': 'execution.json'}], license='unknown', supersedes=[original],
        annotations={RESEARCH: {'role': 'revision', 'motivated_by': accepted}})
    calibration_revision = pack(calibration, 'revised-calibration', [*assumption_refs, inverse])
    retry = Author(dependencies=directories); revised_inverse = pin(calibration_revision, inverse)
    after = retry.plan(revised_inverse, id='after', bindings=measurement, context=context)
    fresh = reader(destination/'revised-calibration').apply(revised_inverse, bindings=measurement, context=context, policy=INTERFACE_POLICY)
    retry.record_attempt(after, question=selected_question, attempt_of='measurement-at-313K', previous_attempt=pin(initial_revision, before),
        contributions=[revised_inverse, accepted, adjusted_run], obstacles=[r for r in fresh['obligations'] if r['status'] != 'satisfied'])
    retry_revision = pack(retry, 'retry', [after]); selected_retry = pin(retry_revision, after)
    retry_check = Research(reader(destination/'retry')).check_retry(selected_retry, expected_previous=pin(initial_revision, before), policy=INTERFACE_POLICY)
    assert retry_check['outcome'] == 'conditional' and 'temperature' in retry_check['resolved_obstacle_ids']
    retry_run, retry_report = execution(selected_retry, 'retry-run')
    assert retry_report['outputs']['displacement']['typed']['value']['value'] == '4'
    assert len(retry_check['remaining_obligations']) == 3
    # A new citation does not repair a still-selected incompatible method.
    unrelated = Author(dependencies=directories)
    unchanged = unrelated.plan(original, id='unchanged', bindings=measurement, context=context)
    unrelated.record_attempt(unchanged, question=selected_question, attempt_of='measurement-at-313K', previous_attempt=pin(initial_revision, before),
        contributions=[accepted], obstacles=[r for r in old_check['obligations'] if r['status'] != 'satisfied'])
    unchanged_revision = pack(unrelated, 'unrelated-retry', [unchanged])
    no_repair = Research(reader(destination/'unrelated-retry')).check_retry(pin(unchanged_revision, unchanged), expected_previous=pin(initial_revision, before), policy=INTERFACE_POLICY)
    assert no_repair['outcome'] == 'incompatible'
    changed_rule = Research(reader(destination/'second-assessment')).verify_evidence(failed, expected_evidence=failed, expected_plan=second_plan, policy=TEST_POLICY)
    assert changed_rule['outcome'] == 'rejected'
    third = reader(destination/'retry-run')
    original_failed = third.inspect(failed)['record']['result']['value']['outcome']
    assert original_failed == 'failed_prediction' and third.inspect(pin(model_revision, follow_up))['record']['targets'] == []
    return {'fixture': 'synthetic; scripted handoff; no autonomous discovery or real-world preregistration',
        'modules': identities, 'directories': [str(path.relative_to(destination)) for path in directories],
        'first_plan': first_plan, 'first_assessment': failed, 'first_outcome': original_failed, 'first_error': first_assessment['result']['value']['absolute_error'],
        'revision': selected_revision, 'revised_offset': revised_parameters['offset'], 'reused_result': reused_gain,
        'reused_method_source_sha256': produced['reviewed_source_sha256'], 'second_plan': second_plan, 'second_assessment': accepted,
        'second_outcome': second_assessment['outcome'], 'needs_reassessment': uses['candidates'], 'blocked_attempt': pin(initial_revision, before),
        'retry': selected_retry, 'retry_run': retry_run, 'retry_output': retry_report['outputs'],
        'resolved_obstacles': retry_check['resolved_obstacle_ids'], 'remaining_obligations': retry_check['remaining_obligations'],
        'unrelated_contribution': no_repair['outcome'], 'changed_rule': changed_rule['outcome'], 'follow_up': pin(model_revision, follow_up),
        'physical_validity': 'unresolved; finite comparisons do not prove the model', 'formal_bridge': 'not_performed', 'gate_u': 'not_evaluated'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('destination', type=Path)
    print(json.dumps(run_cycle(parser.parse_args().destination), indent=2, sort_keys=True))

"""Public authoring against wire bindings, publication and source isolation."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(1, str(Path(__file__).resolve().parents[3]))
from slean.authoring import Author, QUANTITY, RESEARCH
from slean.quantities import scalar, scalar_port
from conformance import contract
from slean.contract import ContractError as SDKContractError

EMPTY = {'id': 'conditions', 'all': []}
UNKNOWN = {'kind': 'unknown'}
SOURCE = b'raise AssertionError("Package code must not execute during publication")\n'


def typed(value, dimension='voltage', unit='volt'):
    return {'typed': {'profile': QUANTITY, 'value': scalar(value, dimension=dimension, unit=unit, uncertainty=UNKNOWN)}}


def method(author, *, requires=EMPTY, kind='method'):
    return author.component(id='calibration', kind=kind, name='Affine calibration',
        interface={'profile': QUANTITY, 'value': {
            'inputs': {'reading': scalar_port(dimension='voltage', unit='volt')},
            'outputs': {'displacement': scalar_port(dimension='length', unit='millimeter')},
            'entrypoint': {'artifact': {'path': 'method.py'}, 'symbol': 'inverse'}}},
        requires=requires, sources=[{'path': 'method.py'}], license='Apache-2.0')


class AuthoringTests(unittest.TestCase):
    def test_plan_retains_producer_conditions_and_freezes_caller_inputs(self):
        requires = {'id': 'conditions', 'all': [{'id': 'sensor', 'leaf': {'profile': QUANTITY,
            'predicate': 'equals', 'arguments': {'location': 'context', 'field': 'sensor', 'expected': {'literal': 'sensor-A'}}}}]}
        author = Author(payloads={'method.py': SOURCE})
        component = method(author, requires=requires)
        original = deepcopy(requires)
        requires['all'].clear()
        bindings, context = {'reading': typed('8.5')}, {'sensor': {'literal': 'sensor-A'}}
        plan = author.plan(component, id='use', bindings=bindings, context=context,
            extra_requirements={'id': 'extra', 'all': []})
        bindings.clear(); context.clear()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'module'
            author.pack(path, publishable=[component, plan])
            manifest = contract.load((path/'slean-module.json').read_text())
            application = manifest['applications'][0]
            self.assertIn(original, application['requires']['all'])
            self.assertEqual(application['bindings']['reading']['typed']['value']['value'], '8.5')
            self.assertEqual(application['context']['sensor'], {'literal': 'sensor-A'})

    def test_explicit_projection_excludes_private_records_and_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            identities=[]
            for index, secret in enumerate((b'private A', b'private B')):
                author = Author(payloads={'method.py': SOURCE, 'private.txt': secret})
                public = method(author)
                author.component(id='private', kind='data', name='Private journal',
                    interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}},
                    requires=EMPTY, sources=[{'path': 'private.txt'}], license='unknown')
                path=Path(temporary)/str(index)
                identities.append(author.pack(path, publishable=[public]))
                self.assertEqual(sorted(p.name for p in path.iterdir()), ['method.py', 'slean-module.json'])
                manifest=json.loads((path/'slean-module.json').read_text())
                self.assertEqual([c['id'] for c in manifest['components']], ['calibration'])
            self.assertEqual(*identities)

    def test_external_plan_qualifies_actual_producer_conditions(self):
        with tempfile.TemporaryDirectory() as temporary:
            producer=Author(payloads={'method.py': SOURCE})
            claim=producer.component(id='physical', kind='claim', name='Applicability assumption',
                interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}},
                requires=EMPTY, sources=[], license='Apache-2.0')
            requires={'id': 'conditions', 'all': [{'id': 'physical-condition', 'leaf': {
                'profile': QUANTITY, 'predicate': 'applicability', 'arguments': {'claim': claim}}}]}
            component=method(producer, requires=requires)
            upstream=Path(temporary)/'upstream'
            revision=producer.pack(upstream,publishable=[claim,component])
            consumer=Author(dependencies=[upstream])
            plan=consumer.plan({'module': revision, 'id': component['id']}, id='reuse',
                bindings={'reading':typed('8.5')}, context={})
            downstream=Path(temporary)/'downstream'
            consumer.pack(downstream,publishable=[plan])
            manifest=contract.load((downstream/'slean-module.json').read_text())
            self.assertEqual(manifest['dependencies'],[revision])
            actual=manifest['applications'][0]['requires']['all'][0]['leaf']['arguments']['claim']
            self.assertEqual(actual,{'module':revision,'id':'physical'})
            self.assertEqual(manifest['payloads'],[])
            with self.assertRaises(ValueError):
                consumer.plan({'module':'sha256:'+'0'*64,'id':'calibration'},id='wrong',bindings={},context={})

    def test_test_plan_execution_and_imported_assessment_remain_distinct(self):
        author=Author(payloads={'method.py':SOURCE,'observation.json':b'{"value":"4.1"}\n'})
        component=method(author,kind='model')
        question=author.question(id='question',wording='Does the calibration predict this displacement?',source='Owned test')
        expected=typed('4','length','millimeter')['typed']
        bound=typed('0.02','length','millimeter')['typed']
        plan=author.plan_test(component,id='test-plan',question=question,bindings={'reading':typed('8.5')},
            context={},prediction=expected,bound=bound,observation_id='observation')
        execution=author.record_execution(plan,id='run',outputs={'displacement':typed('4.1','length','millimeter')})
        observation=author.component(id='observation',kind='data',name='Recorded displacement',
            interface={'profile':QUANTITY,'value':{'inputs':{},'outputs':{}}},requires=EMPTY,
            sources=[{'path':'observation.json'}],license='Apache-2.0')
        assessment=author.record_evidence(id='assessment',kind='empirical',subject=execution,context={},
            policy='absolute-difference/0.1-draft.1',implementation={'path':'method.py'},
            artifacts=[{'path':'observation.json'}],result={'profile':RESEARCH,'value':{
                'plan':plan,'observation':observation,'model':component,'outcome':'failed_prediction',
                'absolute_error':typed('0.1','length','millimeter')['typed']['value']}})
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'module'
            author.pack(path,publishable=[component,question,plan,execution,observation,assessment],
                alternatives=[{'explanation':'Gain could differ','source':'Owned test','status':'unresolved'}])
            manifest=contract.load((path/'slean-module.json').read_text())
            report=contract.check(manifest,path)
            self.assertEqual(report['imported_evidence'],'declared')
            self.assertEqual(manifest['applications'][1]['plan'],plan)
            self.assertNotIn('prediction',manifest['applications'][1]['annotations'][RESEARCH])
            self.assertEqual(manifest['annotations'][RESEARCH]['alternatives'][0]['status'],'unresolved')

    def test_invalid_selection_cannot_pull_private_ancestors_or_overwrite(self):
        author=Author(payloads={'method.py':SOURCE})
        public=method(author)
        with self.assertRaises(ValueError): method(author)
        with self.assertRaises(SDKContractError): author.payload('../escape',b'x')
        private=author.question(id='private-question',wording='Private question',source='Private journal')
        public_question=author.question(id='public-question',wording='Public question',source='Owned test',targets=[private])
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'module'
            with self.assertRaises(SDKContractError): author.pack(path,publishable=[public_question])
            self.assertFalse(path.exists())
            author.pack(path,publishable=[public])
            before=(path/'slean-module.json').read_bytes()
            with self.assertRaises(ValueError): author.pack(path,publishable=[public])
            self.assertEqual((path/'slean-module.json').read_bytes(),before)

    def test_reuse_attempt_preserves_previous_inputs_and_rejects_changed_retry(self):
        requirement = {'id': 'sensor', 'leaf': {'profile': QUANTITY, 'predicate': 'equals',
            'arguments': {'location': 'context', 'field': 'sensor', 'expected': {'literal': 'sensor-A'}}}}
        author = Author(payloads={'method.py': SOURCE})
        component = method(author, requires=requirement)
        question = author.question(id='question', wording='Can this method be reused?', source='Owned example')
        first = author.plan(component, id='first', bindings={'reading': typed('8.5')}, context={'sensor': {'literal': 'sensor-B'}})
        obstacle = {'requirement': 'sensor', 'status': 'violated', 'reason': 'Sensor identity differs', 'witnesses': []}
        author.record_attempt(first, question=question, attempt_of='reuse-reading', previous_attempt=None, contributions=[], obstacles=[obstacle])
        second = author.plan(component, id='second', bindings={'reading': typed('8.5')}, context={'sensor': {'literal': 'sensor-B'}})
        author.record_attempt(second, question=question, attempt_of='reuse-reading', previous_attempt=first, contributions=[component], obstacles=[obstacle])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'valid'
            author.pack(path, publishable=[component, question, first, second])
            manifest = contract.load((path/'slean-module.json').read_text())
            self.assertEqual(manifest['applications'][0]['context'], manifest['applications'][1]['context'])
            self.assertEqual(manifest['applications'][0]['annotations'][RESEARCH]['contributions'], [])
            changed = author.plan(component, id='changed', bindings={'reading': typed('9')}, context={'sensor': {'literal': 'sensor-B'}})
            author.record_attempt(changed, question=question, attempt_of='reuse-reading', previous_attempt=first, contributions=[component], obstacles=[obstacle])
            with self.assertRaises(SDKContractError) as error:
                author.pack(Path(temporary)/'invalid', publishable=[component, question, first, changed])
            self.assertEqual(error.exception.code, 'changed_retry_input')
        with self.assertRaises(ValueError):
            author.record_attempt(first, question=question, attempt_of='new', previous_attempt=None, contributions=[], obstacles=[])

    def test_test_plan_cannot_be_relabelled_or_use_temperature_difference(self):
        author = Author(payloads={'method.py': SOURCE})
        component = method(author, kind='model')
        question = author.question(id='question', wording='Test prediction', source='Owned example')
        plan = author.plan_test(component, id='prediction', question=question, bindings={'reading': typed('8.5')}, context={},
            prediction=typed('4', 'length', 'millimeter')['typed'], bound=typed('0.01', 'length', 'millimeter')['typed'], observation_id='observation')
        with self.assertRaises(ValueError):
            author.record_attempt(plan, question=question, attempt_of='new', previous_attempt=None, contributions=[], obstacles=[])
        with self.assertRaisesRegex(ValueError, 'Temperature-difference'):
            author.plan_test(component, id='temperature', question=question, bindings={}, context={},
                prediction=typed('20', 'temperature', 'degree_Celsius')['typed'], bound=typed('1', 'temperature', 'kelvin')['typed'], observation_id='observation')


if __name__=='__main__': unittest.main()

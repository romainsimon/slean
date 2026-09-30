"""Offline exact-reference inspection and quantity application planning.

Imported evidence remains declared. Planning executes only receiver-owned
checks, never a packaged method or prover.
"""
from copy import deepcopy
import csv
from decimal import Decimal
import hashlib
import io
from pathlib import Path

import rfc8785

from . import contract
from .authoring import KNOWN_PROFILES, QUANTITY, RESEARCH, qualify_requirements, _requirements
from .quantities import QuantityError, check_scalar, convert_scalar, scalar

INTERFACE_POLICY = 'quantity-interface/0.1-draft.1'
INTEGRITY_POLICY = 'module-integrity/0.1-draft.1'
COMPATIBILITY = {'satisfied': 'compatible', 'violated': 'incompatible', 'unresolved': 'conditional', 'unsupported': 'unsupported'}


class MissingReference(ValueError):
    pass


class Reader:
    def __init__(self, directory, *, dependencies=()):
        self._modules, self._directories = {}, {}
        for path in (directory, *dependencies):
            path = Path(path).resolve(strict=True)
            manifest = contract.load((path/'slean-module.json').read_text())
            contract.check(manifest, path)
            self._modules[manifest['id']] = manifest
            self._directories[manifest['id']] = path
        self.module = next(iter(self._modules))

    def _fresh(self, module):
        if module not in self._modules:
            raise MissingReference('Missing exact module: '+module)
        directory = self._directories[module]
        current = contract.load((directory/'slean-module.json').read_text())
        contract.check(current, directory)
        contract.need(current['id'] == module, 'module_changed')
        return current

    def _resolve(self, reference, owner=None):
        contract.schema(reference, 'module', 'ref')
        module = reference.get('module', owner or self.module)
        manifest = self._fresh(module)
        for family in ('components', 'applications', 'evidence', 'questions'):
            records = manifest.get('annotations', {}).get(RESEARCH, {}).get('questions', []) if family == 'questions' else manifest[family]
            for record in records:
                if record['id'] == reference['id']:
                    return module, family, deepcopy(record)
        raise MissingReference('Missing exact record: '+reference['id'])

    def inspect(self, subject):
        module, family, record = self._resolve(subject)
        return {'subject': {'module': module, 'id': record['id']}, 'family': family, 'record': record,
            'integrity': 'valid', 'imported_evidence': 'declared',
            'formal_verification': 'not_performed', 'computational_reproduction': 'not_performed',
            'empirical_validity': 'not_assessed'}

    def _binding(self, binding, owner):
        visited = set()
        while 'ref' in binding:
            module, family, record = self._resolve(binding['ref'], owner)
            if 'output' not in binding:
                return {'ref': {'module': module, 'id': record['id']}}, module
            key = (module, record['id'], binding['output'])
            if key in visited:
                raise ValueError('Cyclic output binding')
            visited.add(key)
            if family != 'applications' or record.get('phase') != 'executed' or binding['output'] not in record.get('outputs', {}):
                raise ValueError('An output binding needs an actual executed application output')
            binding, owner = record['outputs'][binding['output']], module
        return deepcopy(binding), owner

    def _artifact(self, reference, owner):
        module = reference.get('module', owner)
        manifest = self._fresh(module)
        matches = [p for p in manifest['payloads'] if p['path'] == reference['path']]
        if len(matches) != 1:
            raise MissingReference('Missing exact artifact')
        raw = (self._directories[module]/reference['path']).read_bytes()
        expected = matches[0]
        contract.need(str(len(raw)) == expected['size'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'payload_integrity')
        return raw

    def _port(self, binding, descriptor, owner):
        if binding is None:
            return {'status': 'unresolved', 'reason': 'missing_binding'}
        binding, owner = self._binding(binding, owner)
        if descriptor['kind'] == 'text':
            if 'literal' not in binding:
                return {'status': 'violated', 'reason': 'text_requires_literal'}
            if binding.get('literal') is None:
                return {'status': 'unresolved', 'reason': 'missing_text'}
            return {'status': 'satisfied' if isinstance(binding['literal'], str) else 'violated', 'reason': 'text_port'}
        typed = binding.get('typed', {})
        if typed.get('profile') != QUANTITY:
            return {'status': 'unsupported', 'reason': 'unsupported_binding_profile'}
        body = typed['value']
        if descriptor['kind'] == 'scalar':
            return check_scalar(body, descriptor)
        if descriptor['kind'] != 'table' or body.get('kind') != 'table':
            return {'status': 'unsupported', 'reason': 'unsupported_port_kind'}
        contract.schema(body, 'quantity', 'table')
        columns = descriptor['columns']
        if set(body['columns']) != set(columns):
            return {'status': 'violated', 'reason': 'table_columns'}
        rows = csv.DictReader(io.StringIO(self._artifact(body['artifact'], owner).decode('utf-8')))
        if rows.fieldnames is None or len(rows.fieldnames) != len(set(rows.fieldnames)) or set(rows.fieldnames) != set(columns):
            return {'status': 'violated', 'reason': 'table_header'}
        statuses, diagnostics = [], []
        # Check column dimensions even for a table that has no data rows.
        for key, port in body['columns'].items():
            source = scalar('0', dimension=port['dimension'], unit=port['unit'], uncertainty={'kind': 'unknown'})
            result = check_scalar(source, columns[key])
            statuses.append(result['status'])
            if result['status'] != 'satisfied': diagnostics.append({'column': key, **result})
        count = 0
        for count, row in enumerate(rows, start=1):
            if set(row) != set(columns) or any(value is None for value in row.values()):
                return {'status': 'violated', 'reason': 'table_row_shape'}
            for key, text in row.items():
                source = body['columns'][key]
                value = scalar(text or None, dimension=source['dimension'], unit=source['unit'], uncertainty={'kind': 'unknown'})
                result = check_scalar(value, columns[key])
                statuses.append(result['status'])
                if result['status'] != 'satisfied': diagnostics.append({'row': count, 'column': key, **result})
        return {'status': contract.aggregate('all', statuses), 'reason': 'table_dimensional_check', 'rows': count, 'diagnostics': diagnostics}

    def _leaf(self, leaf, bindings, context, owner, consumer):
        if leaf['profile'] != QUANTITY:
            return {'status': 'unsupported', 'reason': 'unsupported_leaf_profile'}
        predicate, arguments = leaf['predicate'], leaf['arguments']
        if predicate == 'applicability':
            module, family, claim = self._resolve(arguments['claim'], owner)
            if family != 'components' or claim['kind'] not in ('claim', 'model'):
                return {'status': 'violated', 'reason': 'applicability_claim_kind'}
            return {'status': 'unresolved', 'reason': 'model_applicability_needs_contextual_evidence',
                    'claim': {'module': module, 'id': claim['id']}, 'context': deepcopy(context)}
        if predicate not in ('quantity', 'range', 'equals'):
            return {'status': 'unsupported', 'reason': 'unsupported_predicate'}
        values = bindings if arguments['location'] == 'bindings' else context
        binding = values.get(arguments['field'])
        if binding is None:
            return {'status': 'unresolved', 'reason': 'missing_binding'}
        if predicate == 'quantity':
            return self._port(binding, {'kind': 'scalar', **{k: arguments[k] for k in ('dimension', 'unit', 'allow_missing')}}, consumer)
        actual, actual_owner = self._binding(binding, consumer)
        if predicate == 'equals':
            expected, expected_owner = self._binding(arguments['expected'], owner)
            if 'literal' in actual and 'literal' in expected:
                if actual['literal'] is None or expected['literal'] is None:
                    return {'status': 'unresolved', 'reason': 'missing_literal'}
                equal = type(actual['literal']) is type(expected['literal']) and actual['literal'] == expected['literal']
            elif 'ref' in actual and 'ref' in expected:
                equal = actual['ref'] == expected['ref']
            elif actual.get('typed', {}).get('profile') == QUANTITY and expected.get('typed', {}).get('profile') == QUANTITY:
                target = expected['typed']['value']
                converted = convert_scalar(actual['typed']['value'], target['unit'])
                target = convert_scalar(target, target['unit'])
                if converted['value'] is None or target['value'] is None:
                    return {'status': 'unresolved', 'reason': 'missing_scalar'}
                equal = Decimal(converted['value']) == Decimal(target['value'])
            elif 'artifact' in actual and 'artifact' in expected:
                # Artifact identity is its exact module/path, not equal-looking bytes.
                self._artifact(actual['artifact'], actual_owner); self._artifact(expected['artifact'], expected_owner)
                equal = {**actual['artifact'], 'module': actual['artifact'].get('module', actual_owner)} == {**expected['artifact'], 'module': expected['artifact'].get('module', expected_owner)}
            else:
                return {'status': 'unsupported', 'reason': 'unsupported_identity_binding'}
            return {'status': 'satisfied' if equal else 'violated', 'reason': 'declared_identity_comparison'}
        minimum, maximum = arguments['minimum'], arguments['maximum']
        if actual.get('typed', {}).get('profile') != QUANTITY:
            return {'status': 'unsupported', 'reason': 'unsupported_range_binding'}
        value = actual['typed']['value']
        port = {'kind': 'scalar', 'dimension': minimum['dimension'], 'unit': minimum['unit'], 'allow_missing': True}
        for scalar_value in (value, minimum, maximum):
            diagnostic = check_scalar(scalar_value, port)
            if diagnostic['status'] != 'satisfied': return diagnostic
        value, maximum = convert_scalar(value, minimum['unit']), convert_scalar(maximum, minimum['unit'])
        low, high, magnitude = map(Decimal, (minimum['value'], maximum['value'], value['value']))
        if low > high: return {'status': 'violated', 'reason': 'reversed_range'}
        return {'status': 'satisfied' if low <= magnitude <= high else 'violated', 'reason': 'declared_magnitude_inclusive_range'}

    def apply(self, component, *, bindings, context, policy, extra_requirements=None):
        base = {'policy': policy, 'obligations': [], 'selections': {}, 'prospective': True,
                'formal_verification': 'not_performed', 'computational_reproduction': 'not_performed', 'empirical_validity': 'not_assessed'}
        if policy != INTERFACE_POLICY:
            return {**base, 'compatibility': 'unsupported', 'reason': 'Unsupported interface policy; no execution fallback'}
        try:
            contract.schema(bindings, 'module', 'bindings'); contract.schema(context, 'module', 'bindings')
            owner, family, producer = self._resolve(component)
            mandatory = [p['id'] for p in self._fresh(owner)['profiles'] if p['required'] and p['id'] not in KNOWN_PROFILES]
            if family != 'components' or producer['interface']['profile'] != QUANTITY or mandatory:
                return {**base, 'compatibility': 'unsupported', 'reason': 'Unsupported selected interface or mandatory module profile'}
            interface = producer['interface']['value']
            contract.schema(interface, 'quantity', 'interface')
            diagnostics, selections = [], {}
            def diagnostic(requirement, result):
                diagnostics.append({'requirement': requirement, 'witnesses': [], **result})
                return result['status']
            def checked(call):
                try: return call()
                except MissingReference as error: return {'status': 'unresolved', 'reason': str(error)}
                except QuantityError as error: return {'status': 'unsupported' if error.unsupported else 'violated', 'reason': error.code}
                except (ValueError, KeyError, TypeError, UnicodeError, OSError) as error: return {'status': 'violated', 'reason': str(error)}
            ports = []
            for name, parameter in interface.get('parameters', {}).items():
                identifier = 'parameter-'+hashlib.sha256(name.encode()).hexdigest()[:16]
                descriptor = {'kind': 'scalar', 'dimension': parameter['dimension'], 'unit': parameter['unit'], 'allow_missing': True}
                ports.append(diagnostic(identifier, {'parameter': name, **checked(lambda: check_scalar(parameter, descriptor))}))
            for name, port in interface['inputs'].items():
                identifier = 'input-'+hashlib.sha256(name.encode()).hexdigest()[:16]
                ports.append(diagnostic(identifier, {'port': name, **checked(lambda: self._port(bindings.get(name), port, self.module))}))
            for name in set(bindings)-set(interface['inputs']):
                ports.append(diagnostic('extra-'+hashlib.sha256(name.encode()).hexdigest()[:16], {'status': 'violated', 'reason': 'undeclared_input', 'port': name}))
            def evaluate(node, origin):
                if 'leaf' in node:
                    return diagnostic(node['id'], checked(lambda: self._leaf(node['leaf'], bindings, context, origin, self.module)))
                operator = 'all' if 'all' in node else 'any'
                outcomes = [evaluate(child, origin) for child in node[operator]]
                if operator == 'any' and 'satisfied' in outcomes:
                    selections[node['id']] = node[operator][outcomes.index('satisfied')]['id']
                return contract.aggregate(operator, outcomes)
            requirement_ids = _requirements(producer['requires'])
            if extra_requirements is not None:
                extra_ids = _requirements(extra_requirements)
                if requirement_ids & extra_ids:
                    raise ValueError('Extra conditions duplicate a producer requirement ID')
                requirement_ids |= extra_ids
            outcomes = [*ports, evaluate(producer['requires'], owner)]
            if extra_requirements is not None:
                outcomes.append(evaluate(extra_requirements, self.module))
            status = contract.aggregate('all', outcomes)
            selected = {'module': owner, 'id': producer['id']}
            requirements = qualify_requirements(producer['requires'], owner)
            if extra_requirements is not None:
                suffix = 0
                while f'slean-runtime-extra-{suffix}' in requirement_ids: suffix += 1
                requirements = {'id': f'slean-runtime-extra-{suffix}', 'all': [requirements, qualify_requirements(extra_requirements, self.module)]}
            identifier = 'application-'+hashlib.sha256(rfc8785.dumps({'component': selected, 'bindings': bindings, 'context': context, 'policy': policy, 'requires': requirements})).hexdigest()[:32]
            record = {'id': identifier, 'component': selected, 'phase': 'planned', 'bindings': deepcopy(bindings),
                      'context': deepcopy(context), 'requires': requirements}
            return {**base, 'application': {'id': identifier}, 'record': record, 'compatibility': COMPATIBILITY[status],
                    'obligations': diagnostics, 'selections': selections}
        except MissingReference as error:
            return {**base, 'compatibility': 'conditional', 'reason': str(error)}
        except contract.ContractError as error:
            return {**base, 'compatibility': 'incompatible', 'reason': str(error)}
        except OSError as error:
            return {**base, 'compatibility': 'incompatible', 'reason': str(error)}
        except (ValueError, KeyError, TypeError) as error:
            return {**base, 'compatibility': 'unsupported', 'reason': str(error)}

    def uses(self, subject):
        target, _, record = self._resolve(subject)
        found = []
        for module in sorted(self._modules):
            manifest = self._fresh(module)
            for application in manifest['applications']:
                component = application['component']
                if component['id'] == record['id'] and component.get('module', module) == target:
                    found.append({'module': module, 'id': application['id']})
        return found

    def verify(self, subject, *, policy):
        module = subject.get('module', self.module)
        base = {'module': module, 'subject': {**subject, 'module': module}, 'policy': policy,
                'layer': 'integrity', 'artifacts': [], 'diagnostics': []}
        if policy != INTEGRITY_POLICY:
            return {**base, 'outcome': 'unsupported', 'diagnostics': ['No registered scientific verifier for this explicit policy']}
        try:
            module, _, _ = self._resolve(subject)
            return {**base, 'outcome': 'valid', 'artifacts': [{'path': p['path'], 'module': module} for p in self._modules[module]['payloads']]}
        except (ValueError, OSError) as error:
            return {**base, 'outcome': 'failed', 'diagnostics': [str(error)]}

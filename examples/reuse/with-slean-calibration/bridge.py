"""Receiver-owned adapter for this affine calibration, not a universal ontology.

The exact rational coordinates select a conditional Lean statement. They do
not prove the Python program correct or turn unknown parameter uncertainty
into an exact physical quantity. Inspection never executes packaged code.
"""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import hashlib
from pathlib import Path

import rfc8785
from slean import Author
from slean.authoring import QUANTITY, LEAN, qualify_requirements
from slean.quantities import convert_scalar
from slean.reader import INTERFACE_POLICY
from slean.execution import _qualify

FORMAT = 'slean-affine-calibration-example/0.1-draft.1'
POLICY = 'affine-calibration-link/0.1-draft.1'
UNITS = {'gain': ('gain', 'volt/millimeter'), 'offset': ('voltage', 'volt'),
         'residual_bound': ('voltage', 'volt'), 'reading': ('voltage', 'volt'),
         'displacement': ('length', 'millimeter'), 'error_bound': ('length', 'millimeter')}


class BridgeError(ValueError):
    pass


def coordinate(value, name):
    dimension, unit = UNITS[name]
    if value.get('dimension') != dimension:
        raise BridgeError('wrong_dimension: '+name)
    converted = convert_scalar(value, unit)
    text = converted['value']
    if text is None:
        raise BridgeError('missing_value: '+name)
    if len(text) > 128:
        raise BridgeError('unsupported_coordinate_size: '+name)
    # The example has no parameter-uncertainty propagation theorem. An unknown
    # uncertainty is recorded, not silently represented as a zero-width bound.
    if converted['uncertainty'] != {'kind': 'unknown'}:
        raise BridgeError('unsupported_coordinate_uncertainty: '+name)
    rational = Fraction(Decimal(text))
    return {'quantity': converted, 'numerator': str(rational.numerator),
            'denominator': str(rational.denominator)}


def rational(row):
    return Fraction(int(row['numerator']), int(row['denominator']))


def lean_literal(row):
    number = rational(row)
    return f'(({number.numerator} : ℝ) / {number.denominator})'


def collect(reader, execution, *, expected_component, reviewed_source_sha256):
    """Freshly bind coordinates and open conditions to an exact execution.

    This is a finite mapping/equality check. Reproduction and native proof
    verification are separate explicit operations required by check_bridge.py.
    """
    selected = reader.inspect(execution)
    run = selected['record']
    if selected['family'] != 'applications' or run.get('phase') != 'executed' or 'plan' not in run:
        raise BridgeError('expected_executed_planned_application')
    owner = selected['subject']['module']
    component = {'module': run['component'].get('module', owner), 'id': run['component']['id']}
    if component != expected_component:
        raise BridgeError('wrong_component_revision')
    inspected = reader.inspect(component)
    method = inspected['record']
    if inspected['family'] != 'components' or method['kind'] != 'method' or method['interface']['profile'] != QUANTITY:
        raise BridgeError('expected_quantity_method')
    body = method['interface']['value']
    if set(body.get('parameters', {})) != {'gain', 'offset', 'residual_bound'}:
        raise BridgeError('unsupported_affine_parameters')
    if set(body.get('inputs', {})) != {'reading'} or set(body.get('outputs', {})) != {'displacement', 'error_bound'}:
        raise BridgeError('unsupported_affine_interface')
    if body.get('entrypoint', {}).get('symbol') != 'inverse':
        raise BridgeError('unsupported_affine_entrypoint')
    artifact = body['entrypoint']['artifact']
    source = reader._artifact(artifact, component['module'])
    if hashlib.sha256(source).hexdigest() != reviewed_source_sha256:
        raise BridgeError('source_approval_mismatch')
    # Do not let an executed JSON declaration weaken the originally fixed plan.
    planned = reader.inspect(run['plan'])
    plan = planned['record']; plan_owner = planned['subject']['module']
    def qualified(record, module):
        return {'component': {'module': record['component'].get('module', module), 'id': record['component']['id']},
            'requires': qualify_requirements(record['requires'], module),
            'bindings': _qualify(record['bindings'], module),
            'context': _qualify(record['context'], module)}
    if plan.get('phase') != 'planned' or qualified(run, owner) != qualified(plan, plan_owner):
        raise BridgeError('changed_original_plan')
    original = qualify_requirements(method['requires'], component['module'])
    declared = qualify_requirements(run['requires'], owner)
    extra = None
    if declared != original:
        if 'all' not in declared or original not in declared['all']:
            raise BridgeError('weakened_producer_conditions')
        extra = declared
    application = reader.apply(component, bindings=_qualify(run['bindings'], owner),
        context=_qualify(run['context'], owner), policy=INTERFACE_POLICY, extra_requirements=extra)
    if application['compatibility'] not in {'compatible', 'conditional'}:
        raise BridgeError('incompatible_application')
    remaining = [row for row in application['obligations'] if row['status'] != 'satisfied']
    if any(row['reason'] != 'model_applicability_needs_contextual_evidence' for row in remaining):
        raise BridgeError('unresolved_nonphysical_condition')
    values = {name: coordinate(value, name) for name, value in body['parameters'].items()}
    for name in ('reading', 'displacement', 'error_bound'):
        field = run['bindings'] if name == 'reading' else run['outputs']
        if name not in field:
            raise BridgeError('missing_coordinate: '+name)
        binding, _ = reader._binding(field[name], owner)
        if binding.get('typed', {}).get('profile') != QUANTITY:
            raise BridgeError('unsupported_coordinate_profile: '+name)
        values[name] = coordinate(binding['typed']['value'], name)
    gain, offset, bound, reading, displacement, error = [rational(values[k]) for k in UNITS]
    if gain == 0:
        raise BridgeError('zero_gain')
    if bound < 0:
        raise BridgeError('negative_error_bound')
    if (reading-offset)/gain != displacement:
        raise BridgeError('nominal_inverse_mismatch')
    if bound/abs(gain) != error:
        # This bounded example rejects a rounded equality. A general numerical
        # refinement theorem would require an explicit rounding error term.
        raise BridgeError('conditional_bound_mismatch')
    return {'format': FORMAT, 'policy': POLICY, 'execution': selected['subject'],
        'plan': planned['subject'], 'component': component,
        'source_sha256': reviewed_source_sha256, 'coordinates': values,
        'context': deepcopy(run['context']), 'requires': qualify_requirements(run['requires'], owner),
        'remaining_obligations': remaining,
        'coordinate_interpretation': 'Exact real coordinates in V, mm and V/mm for the declared nominal model',
        'parameter_uncertainty': 'unknown; conditional theorem treats nominal gain/offset as exact',
        'program_refinement': 'not_proved', 'physical_validity': 'not_assessed',
        'numerical_reproduction': 'not_performed', 'formal_verification': 'not_performed'}


def source(mappings):
    """Generate statements from freshly collected numerical objects only."""
    if list(mappings) != ['original', 'revised']:
        raise BridgeError('expected_original_and_revised_mappings')
    pieces = ['import SleanExport\nimport CalibrationProof\nimport Mathlib.Tactic.NormNum\n',
              'set_option autoImplicit false\nnamespace CalibrationApplication\n']
    for label, mapping in mappings.items():
        if mapping['format'] != FORMAT or mapping['policy'] != POLICY:
            raise BridgeError('unsupported_mapping')
        g, o, b, v, x, e = [lean_literal(mapping['coordinates'][k]) for k in UNITS]
        pieces.append(f'''-- Generated from the {label} exact numerical component; physical assumptions stay open.
theorem {label}_nominal : ({v} - {o}) / {g} = {x} := by
  have response : {v} = {g} * {x} + {o} := by norm_num
  rw [response]
  slean_apply CalibrationProof.inverse_exact {g} {o} {x} (by norm_num) recording "{label}-nominal"

theorem {label}_inverse (input : ℝ) :
    ({g} * input + {o} - {o}) / {g} = input := by
  slean_apply CalibrationProof.inverse_exact {g} {o} input (by norm_num) recording "{label}-inverse"

theorem {label}_bound (input residual : ℝ) (residual_bound : |residual| ≤ {b}) :
    |({g} * input + {o} + residual - {o}) / {g} - input| ≤ {e} := by
  have conditional : |({g} * input + {o} + residual - {o}) / {g} - input| ≤ {b} / |{g}| := by
    slean_apply CalibrationProof.inverse_residual_bound {g} {o} input residual {b} (by norm_num) residual_bound recording "{label}-bound"
  norm_num at conditional ⊢
  exact conditional
''')
    pieces.append('end CalibrationApplication\n')
    return '\n'.join(pieces).encode('utf-8')


def check_source(reader, mappings, formal_components):
    """Reject a valid proof of a different model before granting a link."""
    expected = source(mappings)
    selected_names = set()
    for reference in formal_components:
        selected = reader.inspect(reference)
        body = selected['record']['interface']
        if body['profile'] != LEAN or reader._artifact(body['value']['source'], selected['subject']['module']) != expected:
            raise BridgeError('formal_source_does_not_match_coordinates')
        selected_names.add(tuple(part[1] for part in body['value']['declaration']))
    names = {('CalibrationApplication', label+'_'+suffix) for label in mappings for suffix in ('nominal', 'inverse', 'bound')}
    if selected_names != names or len(formal_components) != len(names):
        raise BridgeError('wrong_selected_formal_declarations')
    return hashlib.sha256(expected).hexdigest()


def pack_link(destination, mappings, *, dependencies, formal_components):
    """Portable declared links; no local receipt keys or automatic promotion."""
    author = Author(dependencies=dependencies, payloads={'mapping.json': rfc8785.dumps(mappings)+b'\n',
        'bridge.py': Path(__file__).read_bytes()})
    records = []
    for label, mapping in mappings.items():
        proof_requirements = [{'id': label+'-'+suffix, 'leaf': {'profile': LEAN, 'predicate': 'proposition',
            'arguments': {'claim': formal_components[label][suffix]}}} for suffix in ('nominal', 'inverse', 'bound')]
        records.append(author.component(id=label, kind='claim', name='Conditional affine inverse and error bound: '+label,
            interface={'profile': QUANTITY, 'value': {'inputs': {}, 'outputs': {}}},
            requires={'id': label+'-link', 'all': [mapping['requires'], *proof_requirements]},
            sources=[{'path': 'mapping.json'}, {'path': 'bridge.py'}], license='unknown'))
    return author.pack(destination, publishable=records)

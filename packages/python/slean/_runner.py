"""Receiver-owned scalar/table call adapter; invoked only by explicit execution."""
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import importlib.util
import json
from pathlib import Path
import sys

from . import contract
from .quantities import PROFILE, _registry, check_scalar, scalar, convert_scalar


def _argument(value):
    if value['kind'] == 'text':
        return value['value']
    if value['kind'] == 'table':
        return [{key: _argument(cell) for key, cell in row.items()} for row in value['rows']]
    value = convert_scalar(value, value['unit'])
    if value['value'] is None:
        raise ValueError('Execution cannot substitute a number for a missing input')
    return _registry().Quantity(Decimal(value['value']), value['unit'])


def main(request_path):
    request = contract.load(Path(request_path).read_text())
    with localcontext() as context:
        context.prec, context.rounding = request['precision'], ROUND_HALF_EVEN
        arguments = {key: _argument(value) for key, value in request['arguments'].items()}
        spec = importlib.util.spec_from_file_location('reviewed_slean_method', request['source'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        function = module
        for name in request['symbol'].split('.'):
            function = getattr(function, name)
        returned = function(**arguments)
        if not isinstance(returned, dict) or set(returned) != set(request['outputs']):
            raise ValueError('Returned ports differ from the declared output interface')
        outputs, types = {}, {}
        for name, descriptor in request['outputs'].items():
            value = returned[name]
            if descriptor['kind'] == 'text':
                if not isinstance(value, str): raise ValueError('Text output must be a string')
                outputs[name] = {'literal': value}
                types[name] = 'str'
                continue
            if descriptor['kind'] != 'scalar':
                raise ValueError('This execution policy does not support table outputs')
            # A dimension label in JSON cannot confer a physical unit on a number.
            if not hasattr(value, 'dimensionality') or value.dimensionality != _registry().get_dimensionality(descriptor['unit']):
                raise ValueError('Returned quantity has the wrong physical dimension')
            value = value.to(descriptor['unit'])
            types[name] = type(value.magnitude).__name__
            magnitude = Decimal(str(value.magnitude))
            if not magnitude.is_finite(): raise ValueError('Nonfinite output')
            wire = scalar(format(magnitude, 'f'), dimension=descriptor['dimension'], unit=descriptor['unit'], uncertainty={'kind': 'unknown'})
            if check_scalar(wire, descriptor)['status'] != 'satisfied': raise ValueError('Incompatible returned scalar')
            outputs[name] = {'typed': {'profile': PROFILE, 'value': wire}}
        print(json.dumps({'outputs': outputs, 'numeric_representation': {
            'adapter': 'Pint Quantity with Decimal inputs', 'precision_requested': request['precision'],
            'precision_after_call': context.prec, 'rounding_after_call': context.rounding,
            'output_magnitude_types': types}}, sort_keys=True, allow_nan=False))


if __name__ == '__main__': main(sys.argv[1])

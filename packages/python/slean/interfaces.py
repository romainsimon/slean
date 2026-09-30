"""Small constructors for the bounded quantity profile, without execution."""
from copy import deepcopy
from decimal import Decimal

from . import contract
from .quantities import PROFILE, _validate, check_scalar


def table_port(columns):
    value = {'kind': 'table', 'format': 'csv', 'columns': deepcopy(columns)}
    contract.schema(value, 'quantity', 'tablePort')
    return value


def table(artifact, columns):
    value = {'kind': 'table', 'format': 'csv', 'artifact': deepcopy(artifact), 'columns': deepcopy(columns)}
    contract.schema(value, 'quantity', 'table')
    contract.schema(artifact, 'module', 'artifact')
    return value


def _field(id, predicate, location, field, **arguments):
    if location not in ('bindings', 'context') or not isinstance(field, str) or not field:
        raise ValueError('A constraint needs an explicit bindings/context field')
    value = {'id': id, 'leaf': {'profile': PROFILE, 'predicate': predicate,
             'arguments': {'location': location, 'field': field, **deepcopy(arguments)}}}
    contract.schema(value, 'module', 'requirement')
    return value


def quantity_requirement(id, *, location, field, port):
    contract.schema(port, 'quantity', 'scalarPort')
    return _field(id, 'quantity', location, field, **{key: port[key] for key in ('dimension', 'unit', 'allow_missing')})


def range_requirement(id, *, location, field, minimum, maximum):
    minimum, maximum = _validate(minimum), _validate(maximum)
    port = {'kind': 'scalar', 'dimension': minimum['dimension'], 'unit': minimum['unit'], 'allow_missing': False}
    diagnostic = check_scalar(maximum, port)
    if minimum['value'] is None or diagnostic['status'] != 'satisfied':
        raise ValueError('A range needs supported nonmissing dimensionally compatible endpoints')
    if Decimal(minimum['value']) > Decimal(diagnostic['value']['value']):
        raise ValueError('Range endpoints are reversed after dimensional conversion')
    return _field(id, 'range', location, field, minimum=minimum, maximum=maximum)


def equals_requirement(id, *, location, field, expected):
    contract.schema(expected, 'module', 'binding')
    return _field(id, 'equals', location, field, expected=expected)


def applicability_requirement(id, *, claim):
    contract.schema(claim, 'module', 'ref')
    value = {'id': id, 'leaf': {'profile': PROFILE, 'predicate': 'applicability', 'arguments': {'claim': deepcopy(claim)}}}
    contract.schema(value, 'module', 'requirement')
    return value

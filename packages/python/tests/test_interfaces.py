from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slean import table, table_port, quantity_requirement, range_requirement, equals_requirement, applicability_requirement
from slean.contract import ContractError
from test_authoring import typed


class InterfaceTests(unittest.TestCase):
    def test_constructors_preserve_decimals_and_detach_caller_objects(self):
        minimum = typed('0.000', 'length', 'millimeter')['typed']['value']
        maximum = typed('0.0100', 'length', 'meter')['typed']['value']
        original = deepcopy(maximum)
        requirement = range_requirement('range', location='bindings', field='reading', minimum=minimum, maximum=maximum)
        maximum['value'] = '999'
        self.assertEqual(requirement['leaf']['arguments']['maximum'], original)
        expected = {'ref': {'id': 'sensor'}}
        equality = equals_requirement('sensor', location='context', field='sensor', expected=expected)
        expected['ref']['id'] = 'other'
        self.assertEqual(equality['leaf']['arguments']['expected']['ref']['id'], 'sensor')
        port = {'kind': 'scalar', 'dimension': 'length', 'unit': 'millimeter', 'allow_missing': False}
        self.assertEqual(quantity_requirement('quantity', location='bindings', field='reading', port=port)['leaf']['arguments']['unit'], 'millimeter')
        columns = {'reading': port}
        descriptor = table_port(columns); value = table({'path': 'measurements.csv'}, columns)
        columns.clear()
        self.assertEqual(descriptor['columns'], value['columns'])
        self.assertEqual(applicability_requirement('physical', claim={'id': 'model'})['leaf']['arguments'], {'claim': {'id': 'model'}})

    def test_invalid_ranges_and_unsafe_artifacts_are_rejected(self):
        value = typed('1')['typed']['value']
        for high in (typed('0')['typed']['value'], typed(None)['typed']['value'], typed('1', 'length', 'meter')['typed']['value']):
            with self.assertRaises(ValueError):
                range_requirement('range', location='bindings', field='reading', minimum=value, maximum=high)
        with self.assertRaises(ValueError): equals_requirement('id', location='somewhere', field='x', expected={'literal': 'x'})
        with self.assertRaises(ContractError): table({'path': '../escape'}, {'x': {'kind': 'scalar', 'dimension': 'voltage', 'unit': 'volt', 'allow_missing': False}})


if __name__ == '__main__': unittest.main()

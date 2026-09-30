"""Real pinned unit conversions and unknown/missing-value controls."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slean.quantities import QuantityError, check_scalar, convert_scalar, scalar, scalar_port
from slean import quantities

UNKNOWN = {"kind": "unknown"}


class QuantityTests(unittest.TestCase):
    def test_all_pinned_unit_conversions_and_decimal_identity(self):
        root = Path(__file__).resolve().parents[3]
        expected = json.loads((root / 'profiles/quantity-map.json').read_text())
        bundled = json.loads((root / 'packages/python/slean/data/quantity-map.json').read_text())
        self.assertEqual(bundled, expected)
        for unit, row in expected['units'].items():
            for text in ('0', '3.50', '-2'):
                value = scalar(text, dimension=row['dimension'], unit=unit, uncertainty=UNKNOWN)
                self.assertEqual(value['value'], text)
                target = row['base_unit'] if row['base_unit'] in expected['units'] else unit
                converted = convert_scalar(value, target)
                wanted = Decimal(text)*Decimal(row['scale'])+Decimal(row['offset']) if target == row['base_unit'] else Decimal(text)
                self.assertEqual(Decimal(converted['value']), wanted)
                self.assertEqual(value['value'], text)
        long = scalar('123456789012345678901234567890.12345', dimension='length', unit='millimeter', uncertainty=UNKNOWN)
        self.assertEqual(convert_scalar(long, 'meter')['value'], '123456789012345678901234567.89012345')

    def test_bound_unit_remains_explicit_without_temperature_offset(self):
        uncertainty = {'kind': 'absolute_bound', 'value': '0.02', 'unit': 'millivolt'}
        value = scalar('1.00', dimension='voltage', unit='volt', uncertainty=uncertainty)
        before = deepcopy(value)
        self.assertEqual(convert_scalar(value, 'millivolt')['uncertainty'], uncertainty)
        self.assertEqual(value, before)
        with self.assertRaises(QuantityError) as caught:
            scalar('20', dimension='temperature', unit='degree_Celsius', uncertainty={'kind': 'absolute_bound', 'value': '1', 'unit': 'degree_Celsius'})
        self.assertTrue(caught.exception.unsupported)
        self.assertEqual(caught.exception.code, 'unsupported_difference_unit')
        with self.assertRaises(QuantityError):
            scalar('1', dimension='voltage', unit='volt', uncertainty={'kind': 'absolute_bound', 'value': '-0.1', 'unit': 'volt'})

    def test_missing_dimensions_and_unsupported_semantics_do_not_pass(self):
        port = scalar_port(dimension='voltage', unit='volt', allow_missing=True)
        missing = scalar(None, dimension='voltage', unit='millivolt', uncertainty=UNKNOWN)
        self.assertEqual(check_scalar(missing, port)['status'], 'unresolved')
        self.assertEqual(check_scalar(missing, {**port, 'allow_missing': False})['status'], 'violated')
        wrong = scalar('1', dimension='length', unit='meter', uncertainty=UNKNOWN)
        self.assertEqual(check_scalar(wrong, port)['reason'], 'wrong_dimension')
        self.assertEqual(check_scalar({**missing, 'unit': 'arbitrary_expression'}, port)['status'], 'unsupported')
        self.assertEqual(check_scalar({**missing, 'uncertainty': {'kind': 'confidence_interval'}}, port)['status'], 'unsupported')
        zero = scalar('0', dimension='voltage', unit='volt', uncertainty=UNKNOWN)
        self.assertEqual(check_scalar(zero, port)['status'], 'satisfied')
        for invalid in (1.2, 'NaN', '1e2', '+1', '01', True):
            with self.assertRaises(QuantityError):
                scalar(invalid, dimension='voltage', unit='volt', uncertainty=UNKNOWN)

    def test_definition_version_drift_cannot_grant_conversion(self):
        value = scalar('1000', dimension='voltage', unit='millivolt', uncertainty=UNKNOWN)
        quantities._registry.cache_clear()
        try:
            with patch.object(quantities.metadata, 'version', return_value='different'):
                result = check_scalar(value, scalar_port(dimension='voltage', unit='volt'))
                self.assertEqual(result['status'], 'unsupported')
                self.assertEqual(result['reason'], 'unit_definition_drift')
        finally:
            quantities._registry.cache_clear()


if __name__ == '__main__':
    unittest.main()

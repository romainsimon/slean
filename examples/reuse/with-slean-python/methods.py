"""Ordinary Python/Pint sensor methods for the frozen synthetic fixture.

The error calculation assumes an affine response, an exact gain and the
supplied voltage residual bound. Calibration data do not prove those assumptions.
"""
from decimal import Decimal
import pint

UNITS = pint.UnitRegistry(non_int_type=Decimal)


def calibrate(samples):
    points = [(row['displacement_mm'].to('millimeter').magnitude,
               row['voltage_V'].to('volt').magnitude) for row in samples]
    if len(points) < 2:
        raise ValueError('insufficient_calibration_data')
    mean_x = sum(x for x, _ in points)/len(points)
    mean_y = sum(y for _, y in points)/len(points)
    denominator = sum((x-mean_x)**2 for x, _ in points)
    if not denominator:
        raise ValueError('insufficient_calibration_variation')
    gain = sum((x-mean_x)*(y-mean_y) for x, y in points)/denominator
    offset = mean_y-gain*mean_x
    return {'gain': UNITS.Quantity(gain, 'volt/millimeter'), 'offset': UNITS.Quantity(offset, 'volt')}


def inverse(reading, gain, offset, residual_bound):
    if gain.magnitude == 0:
        raise ValueError('zero_gain')
    if residual_bound.magnitude < 0:
        raise ValueError('negative_error_bound')
    return {'displacement': ((reading-offset)/gain).to('millimeter'),
            'error_bound': (residual_bound/abs(gain)).to('millimeter')}


def predict(displacement, gain, offset):
    return {'voltage': (gain*displacement+offset).to('volt')}

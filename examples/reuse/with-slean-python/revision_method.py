"""Estimate an offset while leaving the selected gain assumption unchanged."""


def revise_offset(voltage, displacement, gain):
    return {'offset': (voltage-gain*displacement).to('volt')}

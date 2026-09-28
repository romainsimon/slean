"""Ordinary Python/Pint computation shared by the two baseline investigations."""

from decimal import Decimal
import pint


UNITS = pint.UnitRegistry(non_int_type=Decimal)


def quantity(record, target_unit):
    value = Decimal(record["value"])
    if not value.is_finite():
        raise ValueError("non_finite_quantity")
    return UNITS.Quantity(value, record["unit"]).to(target_unit)


def serialize(value, unit):
    converted = value.to(unit)
    return {"value": format(converted.magnitude.normalize(), "f"), "unit": unit}


def inverse(voltage, gain, offset):
    """Compute the inverse under the supplied affine-model assumptions."""
    if gain.magnitude == 0:
        raise ValueError("zero_gain")
    return ((voltage - offset) / gain).to("millimeter")

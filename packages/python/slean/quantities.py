"""The bounded quantity profile, with receiver-owned Pint definitions.

Wire decimal spelling is preserved during authoring. Conversion is explicit
and creates a new value. Neither operation validates an empirical model.
"""

from copy import deepcopy
from decimal import Decimal, localcontext
from functools import lru_cache
import hashlib
from importlib import metadata, resources
import json
from pathlib import Path
import re

PROFILE = "slean-quantity/0.1-draft.1"
_DECIMAL = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?\Z")
_MAPPING = json.loads(resources.files(__package__).joinpath("data/quantity-map.json").read_text())


class QuantityError(ValueError):
    def __init__(self, code, detail="", *, unsupported=False):
        self.code, self.unsupported = code, unsupported
        super().__init__(f"{code}: {detail}")


def _decimal(value):
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise QuantityError("invalid_decimal", "Use a finite decimal string")
    return Decimal(value)


def _unit(dimension, unit):
    if not isinstance(dimension, str) or not isinstance(unit, str):
        raise QuantityError("invalid_quantity_unit")
    if dimension not in _MAPPING["dimensions"]:
        raise QuantityError("unsupported_dimension", str(dimension), unsupported=True)
    if unit not in _MAPPING["units"]:
        raise QuantityError("unsupported_unit", str(unit), unsupported=True)
    row = _MAPPING["units"][unit]
    if row["dimension"] != dimension:
        raise QuantityError("wrong_dimension", str(unit))
    return row


@lru_cache(maxsize=1)
def _registry():
    import pint
    expected = _MAPPING["pint"]
    actual = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in Path(pint.__file__).parent.glob("*.txt")}
    if metadata.version("pint") != expected["pint"] or actual != expected["sha256"]:
        raise QuantityError("unit_definition_drift", "Pinned Pint definitions required", unsupported=True)
    registry = pint.UnitRegistry(non_int_type=Decimal)
    basis = ["[length]", "[mass]", "[time]", "[current]", "[temperature]", "[substance]", "[luminosity]"]
    for unit, row in _MAPPING["units"].items():
        dimensions = registry.get_dimensionality(unit)
        if set(dimensions) - set(basis) or [str(dimensions.get(key, 0)) for key in basis] != _MAPPING["dimensions"][row["dimension"]]:
            raise QuantityError("unit_dimension_drift", unit, unsupported=True)
    return registry


def _uncertainty(dimension, uncertainty):
    if not isinstance(uncertainty, dict):
        raise QuantityError("invalid_uncertainty")
    kind = uncertainty.get("kind")
    if kind == "unknown":
        if set(uncertainty) != {"kind"}:
            raise QuantityError("invalid_uncertainty")
        return
    if kind != "absolute_bound":
        raise QuantityError("unsupported_uncertainty", str(kind), unsupported=True)
    if set(uncertainty) != {"kind", "value", "unit"}:
        raise QuantityError("invalid_uncertainty")
    if _decimal(uncertainty["value"]) < 0:
        raise QuantityError("negative_bound")
    row = _unit(dimension, uncertainty["unit"])
    if Decimal(row["offset"]) != 0:
        raise QuantityError("unsupported_difference_unit", "An absolute-temperature offset is not an error bound", unsupported=True)


def scalar(value, *, dimension, unit, uncertainty):
    """Declare a supported scalar; a missing value remains null, never zero."""
    _unit(dimension, unit)
    if value is not None:
        _decimal(value)
    _uncertainty(dimension, uncertainty)
    return {"kind": "scalar", "dimension": dimension, "unit": unit,
            "value": value, "uncertainty": deepcopy(uncertainty)}


def scalar_port(*, dimension, unit, allow_missing=False):
    _unit(dimension, unit)
    if not isinstance(allow_missing, bool):
        raise QuantityError("invalid_missing_policy")
    return {"kind": "scalar", "dimension": dimension, "unit": unit, "allow_missing": allow_missing}


def _validate(value):
    if not isinstance(value, dict) or set(value) != {"kind", "dimension", "unit", "value", "uncertainty"} or value["kind"] != "scalar":
        raise QuantityError("invalid_scalar")
    return scalar(value["value"], dimension=value["dimension"], unit=value["unit"], uncertainty=value["uncertainty"])


def convert_scalar(value, unit):
    value = _validate(value)
    target = _unit(value["dimension"], unit)
    if value["value"] is None:
        return {**value, "unit": unit}
    registry = _registry()
    # All supported factors/offsets are finite decimals. Expand precision from
    # the input rather than silently using the process's 28-digit context.
    texts = [value["value"], *[r[k] for r in _MAPPING["units"].values() for k in ("scale", "offset")]]
    with localcontext() as context:
        context.prec = sum(len(text) for text in texts) + 20
        converted = registry.Quantity(Decimal(value["value"]), value["unit"]).to(unit).magnitude
        # Check the pinned explicit bridge as well as Pint's interpretation.
        source = _MAPPING["units"][value["unit"]]
        expected = (Decimal(value["value"]) * Decimal(source["scale"]) + Decimal(source["offset"]) - Decimal(target["offset"])) / Decimal(target["scale"])
        if converted != expected:
            raise QuantityError("unit_conversion_drift", unit, unsupported=True)
    return {**value, "unit": unit, "value": format(converted, "f")}


def check_scalar(value, descriptor):
    """Check interface compatibility; unknown uncertainty stays explicit."""
    try:
        if not isinstance(descriptor, dict) or set(descriptor) != {"kind", "dimension", "unit", "allow_missing"} or descriptor["kind"] != "scalar":
            raise QuantityError("invalid_scalar_port")
        scalar_port(dimension=descriptor["dimension"], unit=descriptor["unit"], allow_missing=descriptor["allow_missing"])
        value = _validate(value)
        if value["dimension"] != descriptor["dimension"]:
            raise QuantityError("wrong_dimension")
        converted = convert_scalar(value, descriptor["unit"])
        if value["value"] is None:
            return {"status": "unresolved" if descriptor["allow_missing"] else "violated", "reason": "missing_value", "value": converted}
        return {"status": "satisfied", "reason": "supported_dimensional_conversion", "value": converted}
    except QuantityError as error:
        return {"status": "unsupported" if error.unsupported else "violated", "reason": error.code}

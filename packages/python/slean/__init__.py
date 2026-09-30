"""Slean's local scientific-object API (experimental)."""

from .quantities import QuantityError, check_scalar, convert_scalar, scalar, scalar_port
from .authoring import Author
from .reader import Reader, INTERFACE_POLICY, INTEGRITY_POLICY
from .interfaces import table, table_port, quantity_requirement, range_requirement, equals_requirement, applicability_requirement

__all__ = ["Author", "Reader", "INTERFACE_POLICY", "INTEGRITY_POLICY", "QuantityError",
    "check_scalar", "convert_scalar", "scalar", "scalar_port", "table", "table_port",
    "quantity_requirement", "range_requirement", "equals_requirement", "applicability_requirement"]

"""Check the small mapping with the already pinned direct-baseline Pint runtime."""

from decimal import Decimal
import hashlib
import importlib.metadata
import json
from pathlib import Path

import pint

ROOT = Path(__file__).resolve().parents[1]
mapping = json.loads((ROOT / "profiles/quantity-map.json").read_text())
expected = mapping["pint"]
if importlib.metadata.version("pint") != expected["pint"]:
    raise SystemExit("Wrong Pint version")
actual = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
          for p in Path(pint.__file__).parent.glob("*.txt")}
if actual != expected["sha256"]:
    raise SystemExit("Pint unit-definition drift")
units = pint.UnitRegistry(non_int_type=Decimal)
basis = ["[length]", "[mass]", "[time]", "[current]", "[temperature]", "[substance]", "[luminosity]"]
results = []
for name, row in mapping["units"].items():
    dimensions = units.get_dimensionality(name)
    if set(dimensions) - set(basis):
        raise SystemExit(f"Unknown basis for {name}")
    exponents = [str(int(dimensions.get(key, 0))) for key in basis]
    if exponents != mapping["dimensions"][row["dimension"]]:
        raise SystemExit(f"Dimension mismatch for {name}")
    for value in [Decimal("0"), Decimal("3.5"), Decimal("-2")]:
        converted = units.Quantity(value, name).to(row["base_unit"]).magnitude
        wanted = value * Decimal(row["scale"]) + Decimal(row["offset"])
        if converted != wanted:
            raise SystemExit(f"Conversion mismatch for {name}: {value}")
    results.append(name)
print(json.dumps({"profile": mapping["profile"], "pint": expected["pint"], "units_checked": results,
                  "conversions_checked": len(results) * 3, "status": "passed",
                  "physlib_adapter": "ISQ source mapping specified; runtime adapter not implemented"}, sort_keys=True))

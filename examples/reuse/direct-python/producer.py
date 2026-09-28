"""Build a calibration using direct tools; this is not a Slean component."""

import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from method import UNITS, serialize


ROOT = Path(__file__).resolve().parent


def digest(value):
    # Baseline-local identity convention, not the planned Slean manifest identity.
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def method_digest():
    return hashlib.sha256((ROOT / "method.py").read_bytes()).hexdigest()


def calibrate(source):
    with Path(source).open(newline="") as stream:
        points = [(Decimal(row["displacement_mm"]), Decimal(row["voltage_V"]))
                  for row in csv.DictReader(stream)]
    if len(points) < 2 or any(not v.is_finite() for point in points for v in point):
        raise ValueError("invalid_calibration_data")
    mean_x = sum(x for x, _ in points) / len(points)
    mean_y = sum(y for _, y in points) / len(points)
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    if not denominator:
        raise ValueError("insufficient_calibration_variation")
    gain = sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator
    offset = mean_y - gain * mean_x
    model = {
        "kind": "synthetic_affine_calibration", "sensor": "sensor-A",
        "gain": serialize(UNITS.Quantity(gain, "volt/millimeter"), "volt/millimeter"),
        "offset": serialize(UNITS.Quantity(offset, "volt"), "volt"),
        "voltage_range": [{"value": "0.5", "unit": "volt"}, {"value": "10.5", "unit": "volt"}],
        "temperature": {"value": "293.15", "unit": "kelvin"},
        "assumed_residual_bound": {"value": "0.02", "unit": "volt"},
        "parameter_uncertainty": "unquantified",
        "method_sha256": method_digest(),
        "data_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        "remaining_assumptions": ["affine_model_applies", "gain_treated_as_exact",
                                  "residual_within_assumed_bound"],
    }
    return {"sha256": digest(model), "model": model}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(calibrate(args.data), indent=2, sort_keys=True) + "\n")

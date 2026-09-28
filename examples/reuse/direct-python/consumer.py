"""A second investigation uses the producer's declared method and conditions."""

from pathlib import Path
from decimal import getcontext
import json
import pint

from method import inverse, quantity, serialize
from producer import digest, method_digest


def consume(calibration, sample, *, expected_version, actual_method_digest=None):
    model = calibration["model"]
    diagnostics = []
    if digest(model) != calibration["sha256"]:
        diagnostics.append("model_integrity")
    if calibration["sha256"] != expected_version:
        diagnostics.append("wrong_version")
    if model.get("kind") not in {"synthetic_affine_calibration", "unresolved_affine_hypothesis"}:
        return {"status": "unsupported", "diagnostics": diagnostics + ["method_interface_not_supported"],
                "uses": expected_version}
    if (actual_method_digest if actual_method_digest is not None else method_digest()) != model["method_sha256"]:
        diagnostics.append("changed_method_bytes")
    if sample["sensor"] != model["sensor"]:
        diagnostics.append("wrong_sensor")
    try:
        voltage = quantity(sample["reading"], "volt")
        low, high = [quantity(value, "volt") for value in model["voltage_range"]]
        if not low <= voltage <= high:
            diagnostics.append("outside_operating_range")
        if quantity(sample["temperature"], "kelvin") != quantity(model["temperature"], "kelvin"):
            diagnostics.append("temperature_requirement_not_met")
        gain = quantity(model["gain"], "volt/millimeter")
        offset = quantity(model["offset"], "volt")
        residual_bound = quantity(model["assumed_residual_bound"], "volt")
        if gain.magnitude == 0:
            diagnostics.append("zero_gain")
        if residual_bound.magnitude < 0:
            diagnostics.append("negative_error_bound")
    except (pint.DimensionalityError, pint.UndefinedUnitError, ValueError):
        diagnostics.append("quantity_or_dimension_error")
    if diagnostics:
        return {"status": "incompatible", "diagnostics": diagnostics, "uses": expected_version}
    if sample.get("uncertainty_kind", "absolute_bound") != "absolute_bound":
        return {"status": "unsupported", "diagnostics": ["uncertainty_interpretation"], "uses": expected_version}
    displacement = inverse(voltage, gain, offset)
    if "claimed_displacement" in sample:
        try:
            if quantity(sample["claimed_displacement"], "millimeter") != displacement:
                return {"status": "incompatible", "diagnostics": ["output_not_reproduced"], "uses": expected_version}
        except (pint.DimensionalityError, pint.UndefinedUnitError, ValueError):
            return {"status": "incompatible", "diagnostics": ["output_dimension_error"], "uses": expected_version}
    obligations = list(model["remaining_assumptions"])
    if not sample.get("applicability_evidence"):
        obligations.append("applicability_evidence_missing")
    # Finite calibration evidence never proves these universal physical assumptions.
    return {
        "status": "conditional", "uses": expected_version,
        "displacement": serialize(displacement, "millimeter"),
        "conditional_error_bound": serialize(residual_bound / abs(gain), "millimeter"),
        "remaining_assumptions": obligations, "parameter_uncertainty": model["parameter_uncertainty"],
        "method_sha256": model["method_sha256"], "numeric_representation": f"Python Decimal, context precision {getcontext().prec}",
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("calibration", type=Path)
    parser.add_argument("sample", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    result = consume(json.loads(args.calibration.read_text()), json.loads(args.sample.read_text()),
                     expected_version=args.expected_version)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

"""A controlled prediction/revision/reuse cycle using direct Python records."""

from copy import deepcopy

from consumer import consume
from method import quantity, serialize
from producer import digest


def freeze_rule(model, expected, bound, observation_id):
    body = {"model": model["sha256"], "sensor": model["model"]["sensor"],
            "temperature": model["model"]["temperature"], "expected": expected,
            "bound": bound, "observation_id": observation_id}
    return {"sha256": digest(body), "rule": body}


def assess(protocol, observation, *, expected_protocol):
    rule = protocol["rule"]
    if protocol["sha256"] != expected_protocol or digest(rule) != expected_protocol:
        return {"outcome": "rejected", "diagnostic": "changed_frozen_rule"}
    if (observation["id"] != rule["observation_id"] or observation["sensor"] != rule["sensor"]
            or quantity(observation["temperature"], "kelvin") != quantity(rule["temperature"], "kelvin")):
        return {"outcome": "not_applicable", "diagnostic": "observation_outside_scope", "protocol": expected_protocol}
    error = abs(quantity(observation["voltage"], "volt") - quantity(rule["expected"], "volt"))
    passed = error <= quantity(rule["bound"], "volt")
    return {"outcome": "within_bound" if passed else "failed_prediction",
            "protocol": expected_protocol, "model": rule["model"],
            "observation": observation["id"], "absolute_error": serialize(error, "volt")}


def affected_uses(applications, assessment):
    if assessment["outcome"] != "failed_prediction":
        return []
    # These applications select this precise model version and its single context.
    return [a["id"] for a in applications if a["uses"] == assessment["model"]]


def run_cycle(calibration, sample, inputs):
    high_temperature = deepcopy(sample)
    high_temperature["temperature"] = inputs["temperature"]
    high_temperature["reading"] = inputs["first_observation"]
    # The original evidence reference concerns the original temperature only.
    high_temperature.pop("applicability_evidence", None)
    before = consume(calibration, high_temperature, expected_version=calibration["sha256"])

    proposal = deepcopy(calibration["model"])
    proposal.update(kind="unresolved_affine_hypothesis", temperature=inputs["temperature"],
                    derived_from=calibration["sha256"])
    hypothesis = {"sha256": digest(proposal), "model": proposal}
    gain = quantity(proposal["gain"], "volt/millimeter")
    predicted = gain * quantity(inputs["first_displacement"], "millimeter") + quantity(proposal["offset"], "volt")
    first_rule = freeze_rule(hypothesis, serialize(predicted, "volt"), inputs["absolute_bound"], "observation-1")
    first_rule_identity = first_rule["sha256"]  # Fixed before the observation is bound.
    observation = {"id": "observation-1", "sensor": sample["sensor"],
                   "temperature": inputs["temperature"], "voltage": inputs["first_observation"]}
    failed = assess(first_rule, observation, expected_protocol=first_rule_identity)
    applications = [{"id": "high-temperature-prediction", "uses": hypothesis["sha256"]},
                    {"id": "original-temperature-use", "uses": calibration["sha256"]}]

    revised = deepcopy(proposal)
    revised_offset = quantity(inputs["first_observation"], "volt") - gain * quantity(inputs["first_displacement"], "millimeter")
    revised.update(offset=serialize(revised_offset, "volt"), supersedes=hypothesis["sha256"])
    revision = {"sha256": digest(revised), "model": revised}
    second_prediction = gain * quantity(inputs["second_displacement"], "millimeter") + revised_offset
    second_rule = freeze_rule(revision, serialize(second_prediction, "volt"), inputs["absolute_bound"], "observation-2")
    second_identity = second_rule["sha256"]
    second_observation = {"id": "observation-2", "sensor": sample["sensor"],
                          "temperature": inputs["temperature"], "voltage": inputs["second_observation"]}
    second_assessment = assess(second_rule, second_observation, expected_protocol=second_identity)

    # Retry exactly the same observation. New model/evidence bindings are separate.
    after = consume(revision, high_temperature, expected_version=revision["sha256"])
    return {
        "fixture": "synthetic; scripted handoff, no autonomous discovery or real-world preregistration",
        "original_calibration": calibration, "hypothesis": hypothesis, "revision": revision,
        "protocols": [first_rule, second_rule], "observations": [observation, second_observation],
        "assessments": [failed, second_assessment], "applications": applications,
        "needs_reassessment": affected_uses(applications, failed),
        "blocked_question": {"id": "high-temperature-reconstruction",
                             "question": "Can the same displacement reading be reconstructed at this temperature?",
                             "input": high_temperature, "input_sha256": digest(high_temperature),
                             "obstacles": ["temperature_requirement_not_met"],
                             "attempts": [
                                 {"id": "before", "input_sha256": digest(high_temperature),
                                  "model": calibration["sha256"], "method_sha256": proposal["method_sha256"],
                                  "result": before},
                                 {"id": "after", "input_sha256": digest(high_temperature),
                                  "model": revision["sha256"], "method_sha256": revised["method_sha256"],
                                  "assessment": second_identity, "result": after}],
                             "new_contribution": revision["sha256"]},
        "follow_up": {"question": inputs["follow_up"], "motivated_by": "observation-1", "status": "unresolved"},
        "alternative": {"explanation": inputs["unresolved_alternative"], "status": "unresolved"},
        "physical_validity": "unresolved; the successful finite test does not prove the model",
    }

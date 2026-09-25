"""Run the frozen, illustrative UCI bike-demand comparison read-only.

The UCI ZIP is read but never changed or copied into the repository. The two
small output files are a measured retrospective result and a Slean dossier;
neither claims that UCI or Capital Bikeshare used this decision protocol.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import time
from collections import defaultdict
from datetime import date, datetime, time as clock_time, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_PATH = ROOT / "examples/uci-bike-sharing/protocol.json"
FROZEN_PROTOCOL_COMMIT = "7c5bb24f8f07e73db76b8bf37ec12d7ccec2a283"
FROZEN_PROTOCOL_SHA256 = "b519249c349de8ef840ec8c0b4a4eb5b7469158ca09e5cb0c969c5c42388dda0"
PLACES = 6
SCALE = 10**PLACES


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_second(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_microsecond(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def decimal_six(value: Fraction) -> str:
    """Round an exact rational to six places with integer half-even arithmetic."""
    negative = value < 0
    scaled, remainder = divmod(abs(value.numerator) * SCALE, value.denominator)
    if 2 * remainder > value.denominator or (2 * remainder == value.denominator and scaled % 2):
        scaled += 1
    sign = "-" if negative and scaled else ""
    return f"{sign}{scaled // SCALE}.{scaled % SCALE:0{PLACES}d}"


def fraction_record(value: Fraction) -> dict:
    return {"numerator": value.numerator, "denominator": value.denominator,
            "decimal_6_half_even": decimal_six(value)}


def read_hour_rows(archive_path: Path, member: str, expected_rows: int):
    rows = []
    with ZipFile(archive_path) as archive:
        with archive.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"dteday", "hr", "yr", "cnt", "casual", "registered"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("hour.csv is missing required source fields")
            for source in reader:
                day = date.fromisoformat(source["dteday"])
                hour = int(source["hr"])
                year_flag = int(source["yr"])
                count = int(source["cnt"])
                if year_flag not in (0, 1) or day.year != 2011 + year_flag:
                    raise ValueError("source year disagrees with dteday")
                if not 0 <= hour <= 23 or count < 0:
                    raise ValueError("invalid hour or rental count")
                if int(source["casual"]) + int(source["registered"]) != count:
                    raise ValueError("source total disagrees with component counts")
                rows.append((datetime.combine(day, clock_time(hour)), hour, count))
    if len(rows) != expected_rows:
        raise ValueError(f"source row count changed: {len(rows)}")
    return rows


def score(rows, protocol):
    train_year = protocol["split"]["train_year"]
    test_year = protocol["split"]["test_year"]
    train = [row for row in rows if row[0].year == train_year]
    test = [row for row in rows if row[0].year == test_year]
    if not train or not test or len(train) + len(test) != len(rows):
        raise ValueError("source has rows outside the frozen train/test years")
    if max(row[0] for row in train) >= min(row[0] for row in test):
        raise ValueError("train/test timestamps are not chronologically separated")

    global_mean = Fraction(sum(row[2] for row in train), len(train))
    by_hour = defaultdict(lambda: [0, 0])
    for _, hour, count in train:
        by_hour[hour][0] += count
        by_hour[hour][1] += 1
    hour_means = {hour: Fraction(total, size) for hour, (total, size) in by_hour.items()}
    baseline_mae = sum((abs(Fraction(count) - global_mean) for _, _, count in test), Fraction()) / len(test)
    candidate_mae = sum((abs(Fraction(count) - hour_means.get(hour, global_mean))
                         for _, hour, count in test), Fraction()) / len(test)
    return {
        "train": train, "test": test, "hour_means": hour_means,
        "baseline_mae": baseline_mae, "candidate_mae": candidate_mae,
        "improvement": baseline_mae - candidate_mae,
    }


def historical_span(rows) -> dict:
    first = min(row[0] for row in rows)
    last = max(row[0] for row in rows)
    return {"rows": len(rows), "first_local_hour": first.strftime("%Y-%m-%dT%H:00"),
            "last_local_hour": last.strftime("%Y-%m-%dT%H:00")}


def ident(object_id: str, provenance: str) -> dict:
    return {"id": object_id, "version": 1, "domain": "uci-bike-retrospective",
            "provenance": provenance, "audience": "agent"}


def make_case(protocol: dict, result: dict, result_sha: str, script_sha: str) -> dict:
    case_id = protocol["protocol_id"]
    provenance = f"{protocol['source']['dataset_url']}#sha256={protocol['source']['archive_sha256']}"
    protocol_id = "protocol:" + case_id
    run_id = "run:" + case_id
    source_id = "artifact:uci-hour-csv"
    result_id = "artifact:retrospective-result"
    observation_id = "observation:mae-improvement"
    assessment_id = "assessment:illustrative-rule"
    claim_id = "claim:" + case_id
    events = []

    def emit(kind: str, object_id: str, payload: dict, recorded_at: str) -> None:
        events.append({"event_id": f"event:{len(events) + 1}:{kind}", "version": 1,
                       "domain": "uci-bike-retrospective", "provenance": provenance,
                       "sequence": len(events) + 1, "kind": kind,
                       "actor": "Slean illustrative retrospective evaluator",
                       "recorded_at": recorded_at, "audience": "agent", "payload": payload})

    frozen_at = protocol["frozen_at_utc"]
    started_at = result["evaluation"]["started_at_utc_second"]
    completed_at = result["evaluation"]["completed_at_utc_second"]
    emit("protocol_frozen", protocol_id, {
        "identity": ident(protocol_id, provenance), "claim_ref": claim_id,
        "metric_id": protocol["metric"]["id"], "unit": protocol["metric"]["unit"],
        "direction": protocol["promotion_rule"]["direction"],
        "threshold": protocol["promotion_rule"]["threshold"],
        "inclusive": protocol["promotion_rule"]["inclusive"],
        "data_scope": "UCI hour.csv, train 2011, held-out 2012",
        "evaluator_ref": "sha256:" + script_sha,
        "cost_cap": protocol["cpu_budget"]["cap"],
        "cost_unit": protocol["cpu_budget"]["unit"],
        "stop_rule": protocol["stop_rule"], "frozen_at": frozen_at,
    }, frozen_at)
    emit("artifact_registered", source_id, {
        "identity": ident(source_id, provenance),
        "digest": "sha256:" + protocol["source"]["member_sha256"],
        "media_type": "text/csv",
    }, started_at)
    emit("run_started", run_id, {
        "identity": ident(run_id, provenance), "protocol_ref": protocol_id,
        "input_ref": source_id, "seed": "",
    }, started_at)
    emit("artifact_registered", result_id, {
        "identity": ident(result_id, provenance),
        "digest": "sha256:" + result_sha, "media_type": "application/json",
    }, completed_at)
    emit("observation_recorded", observation_id, {
        "identity": ident(observation_id, provenance), "run_ref": run_id,
        "metric_id": protocol["metric"]["id"], "unit": protocol["metric"]["unit"],
        "value": result["measurements"]["mae_improvement"]["decimal_6_half_even"],
        "status": "measured", "artifact_ref": result_id, "observed_at": completed_at,
    }, completed_at)
    emit("cost_recorded", "cost:local-cpu", {
        "identity": ident("cost:local-cpu", provenance), "run_ref": run_id,
        "category": "machine_time", "amount": result["evaluation"]["cpu_seconds"],
        "unit": protocol["cpu_budget"]["unit"], "source": "Python time.process_time_ns",
        "coverage": "complete-local-evaluation-excluding-network",
    }, completed_at)
    emit("assessment_recorded", assessment_id, {
        "identity": ident(assessment_id, provenance), "protocol_ref": protocol_id,
        "observation_refs": [observation_id],
        "verdict": result["decision"]["verdict"], "rule_used": "exact_v0",
    }, completed_at)
    emit("decision_recorded", "decision:illustrative", {
        "identity": ident("decision:illustrative", provenance),
        "assessment_ref": assessment_id, "result": result["decision"]["result"],
        "reason": "Illustrative retrospective threshold only; no deployment authorization.",
    }, completed_at)
    return {
        "schema_version": "0.3.0", "semantics_version": "0.3.0",
        "case_id": case_id, "version": 1, "domain": "uci-bike-retrospective",
        "provenance": provenance, "audience": "agent",
        "question": {"identity": ident("question:" + case_id, provenance),
                     "text": protocol["question"]},
        "claim": {"identity": ident(claim_id, provenance),
                  "text": "The 2011 hour-of-day mean improves 2012 MAE by at least 5 bikes/hour versus the 2011 global mean."},
        "events": events,
    }


def evaluate(archive_path: Path, output_dir: Path) -> dict:
    protocol_raw = PROTOCOL_PATH.read_bytes()
    if sha256(protocol_raw) != FROZEN_PROTOCOL_SHA256:
        raise ValueError("frozen protocol bytes changed")
    protocol = json.loads(protocol_raw)
    if protocol["status"] != "illustrative_retrospective_teaching_protocol":
        raise ValueError("unexpected protocol status")
    if protocol["split"] != {"train_year": 2011, "test_year": 2012,
                              "order": "strict chronological holdout; never fit on 2012 rows"}:
        raise ValueError("unsupported split")
    if protocol["promotion_rule"]["direction"] != "gte" or not protocol["promotion_rule"]["inclusive"]:
        raise ValueError("unsupported promotion rule")
    if protocol["metric"]["id"] != "mae_improvement" or protocol["target"]["column"] != "cnt":
        raise ValueError("unsupported metric or target")
    source = protocol["source"]
    if sha256(archive_path.read_bytes()) != source["archive_sha256"]:
        raise ValueError("UCI archive SHA-256 does not match the frozen protocol")
    with ZipFile(archive_path) as archive:
        if sha256(archive.read(source["member"])) != source["member_sha256"]:
            raise ValueError("hour.csv SHA-256 does not match the frozen protocol")

    started = utc_now()
    if started <= datetime.fromisoformat(protocol["frozen_at_utc"].replace("Z", "+00:00")):
        raise ValueError("evaluation started before the authored protocol freeze")
    cpu_start = time.process_time_ns()
    rows = read_hour_rows(archive_path, source["member"], source["expected_hour_rows"])
    scored = score(rows, protocol)
    cpu_ns = time.process_time_ns() - cpu_start
    completed = utc_now()
    cpu_cap_ns = int(Decimal(protocol["cpu_budget"]["cap"]) * Decimal(1_000_000_000))
    if cpu_ns > cpu_cap_ns:
        raise ValueError(f"local evaluation exceeded frozen CPU cap: {cpu_ns} ns")

    baseline = scored["baseline_mae"]
    candidate = scored["candidate_mae"]
    improvement = scored["improvement"]
    displayed_improvement = decimal_six(improvement)
    passed = Decimal(displayed_improvement) >= Decimal(protocol["promotion_rule"]["threshold"])
    script_sha = sha256(Path(__file__).read_bytes())
    result = {
        "format": "slean-uci-bike-retrospective/0.1.0",
        "protocol": {"id": protocol["protocol_id"], "frozen_at_utc": protocol["frozen_at_utc"],
                     "frozen_git_commit": FROZEN_PROTOCOL_COMMIT,
                     "sha256": FROZEN_PROTOCOL_SHA256,
                     "evaluator_sha256": script_sha},
        "source": {"dataset_url": source["dataset_url"], "archive_url": source["archive_url"],
                   "archive_sha256": source["archive_sha256"], "member": source["member"],
                   "member_sha256": source["member_sha256"],
                   "attribution": source["attribution"], "license": source["license"],
                   "license_url": source["license_url"]},
        "historical_source_hours": {
            "fields": ["dteday", "hr"], "timezone": "not specified by UCI; no UTC conversion",
            "all": historical_span(rows), "train_2011": historical_span(scored["train"]),
            "held_out_2012": historical_span(scored["test"]),
        },
        "evaluation": {
            "started_at_utc": utc_microsecond(started), "completed_at_utc": utc_microsecond(completed),
            "started_at_utc_second": utc_second(started),
            "completed_at_utc_second": utc_second(completed),
            "cpu_process_time_ns": cpu_ns,
            "cpu_seconds": f"{cpu_ns // 1_000_000_000}.{cpu_ns % 1_000_000_000:09d}",
            "cpu_cap_seconds": protocol["cpu_budget"]["cap"],
            "cpu_coverage": protocol["cpu_budget"]["coverage"],
            "network_fetch_included": False,
        },
        "model": {"baseline": protocol["baseline"]["prediction"],
                  "candidate": protocol["candidate"]["prediction"],
                  "candidate_unseen_train_hours": sorted(set(range(24)) - set(scored["hour_means"]))},
        "measurements": {"unit": protocol["metric"]["unit"],
                         "baseline_mae": fraction_record(baseline),
                         "candidate_mae": fraction_record(candidate),
                         "mae_improvement": fraction_record(improvement)},
        "decision": {"threshold": protocol["promotion_rule"]["threshold"],
                     "direction": "gte", "verdict": "pass" if passed else "fail",
                     "result": "promote" if passed else "reject",
                     "scope": "illustrative retrospective teaching decision only"},
        "limits": "One historical dataset and one fixed holdout; no model tuning, deployment, causal inference or external scientific validation.",
    }
    result_raw = json_bytes(result)
    result_sha = sha256(result_raw)
    case = make_case(protocol, result, result_sha, script_sha)
    case_raw = json_bytes(case)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "result.json").write_bytes(result_raw)
    (output_dir / "case.json").write_bytes(case_raw)
    return {"result_sha256": result_sha, "case_sha256": sha256(case_raw),
            "train_rows": len(scored["train"]), "test_rows": len(scored["test"]),
            "baseline_mae": result["measurements"]["baseline_mae"]["decimal_6_half_even"],
            "candidate_mae": result["measurements"]["candidate_mae"]["decimal_6_half_even"],
            "mae_improvement": displayed_improvement, "cpu_seconds": result["evaluation"]["cpu_seconds"],
            "verdict": result["decision"]["verdict"], "decision": result["decision"]["result"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Unmodified official UCI ZIP")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for small derived JSON files")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.archive, args.output_dir), sort_keys=True))


if __name__ == "__main__":
    main()

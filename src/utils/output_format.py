# utils/output_format.py

import json
from typing import Dict, List, Any
from src.scorer import Scorer

TABLE_COLUMNS = [
    "name",
    "category",
    "net_score",
    "net_score_latency",
    "ramp_up_time",
    "ramp_up_time_latency",
    "bus_factor",
    "bus_factor_latency",
    "performance_claims",
    "performance_claims_latency",
    "license",
    "license_latency",
    "size_score",
    "size_score_latency",
    "dataset_and_code_score",
    "dataset_and_code_score_latency",
    "dataset_quality",
    "dataset_quality_latency",
    "code_quality",
    "code_quality_latency",
]


def print_score_table(rows: List[Dict[str, Any]]):
    print(json.dumps(rows, indent=4))


def format_score_row(metadata: Dict[str, Any], scorer: Scorer) -> Dict[str, Any]:
    """
    Run scorer on metadata and return a flat row dict
    matching the sample_output schema.
    """
    result = scorer.score(metadata)

    # Helper to coerce values to floats, with fallback
    def as_float(val, default=0.0):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    row = {
        "name": result.get("name", "unknown"),
        "category": result.get("category", "unknown"),
        "net_score": as_float(result.get("net_score")),
        "net_score_latency": as_float(result.get("net_score_latency"), 0),
        "ramp_up_time": as_float(result.get("ramp_up_time")),
        "ramp_up_time_latency": as_float(result.get("ramp_up_time_latency"), 0),
        "bus_factor": as_float(result.get("bus_factor")),
        "bus_factor_latency": as_float(result.get("bus_factor_latency"), 0),
        "performance_claims": as_float(result.get("performance_claims")),
        "performance_claims_latency": as_float(result.get("performance_claims_latency"), 0),
        "license": as_float(result.get("license")),
        "license_latency": as_float(result.get("license_latency"), 0),
        "size_score": {
            "raspberry_pi": as_float(result.get("size_score", {}).get("raspberry_pi")),
            "jetson_nano": as_float(result.get("size_score", {}).get("jetson_nano")),
            "desktop_pc": as_float(result.get("size_score", {}).get("desktop_pc")),
            "aws_server": as_float(result.get("size_score", {}).get("aws_server")),
        },
        "size_score_latency": as_float(result.get("size_score_latency"), 0),
        "dataset_and_code_score": as_float(result.get("dataset_and_code_score")),
        "dataset_and_code_score_latency": as_float(result.get("dataset_and_code_score_latency"), 0),
        "dataset_quality": as_float(result.get("dataset_quality")),
        "dataset_quality_latency": as_float(result.get("dataset_quality_latency"), 0),
        "code_quality": as_float(result.get("code_quality")),
        "code_quality_latency": as_float(result.get("code_quality_latency"), 0),
    }

    # Guarantee all columns exist in case TABLE_COLUMNS changes
    for col in TABLE_COLUMNS:
        if col not in row:
            row[col] = 0.0

    return row


def print_score_table_as_json(rows: List[Dict[str, Any]]):
    print(json.dumps(rows, indent=4))
